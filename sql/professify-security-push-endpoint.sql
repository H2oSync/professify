-- =================================================================================================
-- professify-security-push-endpoint.sql — drafted 2026-10-14 (NOT yet run anywhere but a local test DB)
-- Run any time after professify-push.sql. One transaction, idempotent, safe to run twice.
--
-- WHY (plain words, for Tate)
--   When a student turns on website notifications, their browser hands the site an "endpoint": a web
--   address that belongs to Google, Mozilla, Apple or Microsoft's push service. The site saves it in
--   push_subscriptions.endpoint. Later the push-send function POSTs the notification to that address
--   and signs the request with TermChamp's private VAPID key. The table accepts ANY text there. So a
--   signed-in student can save https://attacker.example/x as their endpoint, and the next time that
--   student (or anyone sharing their row) is sent a notification, TermChamp's server makes a
--   signed request to a machine the attacker controls (or to an internal address) — a "make the
--   server fetch my URL" hole.
--
-- WHAT THIS CHANGES
--   Adds one CHECK constraint, push_subs_endpoint_is_push_service, on push_subscriptions.endpoint:
--     * must start with https://
--     * host must be exactly one of  fcm.googleapis.com (Chrome, Edge, Android),
--       updates.push.services.mozilla.com (Firefox), web.push.apple.com (Safari),
--       or any host ending .push.apple.com or .notify.windows.com (Edge/Windows)
--     * no user@ part, no port, no spaces or backslashes, and a path must follow the host
--     * 2048 characters at most (real ones are 100-400)
--   Nothing else changes: no column, no policy, no function, nothing dropped. The website's
--   subscribe code (index.html pushEnable) saves whatever endpoint the browser gives it, and every
--   real browser endpoint matches, so legitimate sign-ups are unaffected. The phone app does not use
--   this table (it uses push_tokens), so it is untouched.
--
--   Existing rows: the constraint is first added NOT VALID (it guards every new insert/update at
--   once without looking at old rows). Then, only if no existing row breaks the rule, it is VALIDATED.
--   If some old row does break it, the file does NOT delete anything: it adds the guard anyway,
--   prints how many rows are bad, and tells you the one-line query to look at them. Remove or fix
--   them, then run this file again and it will finish the validation.
--
--   Also: PUBLIC is revoked on the table (the original only revoked anon). authenticated keeps its
--   access and the three own-row policies.
--
-- It tests itself at the end (on a scratch copy of the table, nothing real is touched) and raises an
-- error — undoing the whole file — if anything is wrong.
-- =================================================================================================
begin;

do $$
declare
  -- One definition, used both to add the rule and to look for old rows that break it.
  rule constant text :=
    $re$endpoint ~* '^https://(fcm\.googleapis\.com|updates\.push\.services\.mozilla\.com|web\.push\.apple\.com|([a-z0-9-]+\.)+push\.apple\.com|([a-z0-9-]+\.)+notify\.windows\.com)/[^\s\\]*$' and length(endpoint) <= 2048$re$;
  bad bigint;
begin
  if to_regclass('public.push_subscriptions') is null then
    raise exception 'security-push-endpoint: public.push_subscriptions not found — run professify-push.sql first';
  end if;

  if not exists (select 1 from pg_constraint
                  where conrelid = 'public.push_subscriptions'::regclass and conname = 'push_subs_endpoint_is_push_service') then
    execute format('alter table public.push_subscriptions add constraint push_subs_endpoint_is_push_service check (%s) not valid', rule);
  end if;

  -- Validate only if every existing row already passes.
  execute format('select count(*) from public.push_subscriptions where not coalesce((%s), false)', rule) into bad;
  if bad = 0 then
    alter table public.push_subscriptions validate constraint push_subs_endpoint_is_push_service;
  else
    raise warning 'security-push-endpoint: % existing push_subscriptions row(s) have an endpoint outside the browser push services. The guard is ON for new writes, but old rows are not validated. Look at them with: select id, user_id, left(endpoint,80) from public.push_subscriptions where not (%) ; then delete or fix, and re-run this file.', bad, rule;
  end if;
end $$;

revoke all on public.push_subscriptions from public, anon;

-- ---- Self-checks ------------------------------------------------------------------------------
do $$
declare
  c pg_constraint%rowtype;
  good text[] := array[
    'https://fcm.googleapis.com/fcm/send/dX1abc:APA91bF-xyz_123',
    'https://FCM.googleapis.com/wp/ABC123',
    'https://updates.push.services.mozilla.com/wpush/v2/gAAAAABk',
    'https://web.push.apple.com/QGhk3Zr-ab_12',
    'https://api.sandbox.push.apple.com/3/device/abc',
    'https://wns2-par02p.notify.windows.com/w/?token=BQYAAAB%2f'];
  bad text[] := array[
    'http://fcm.googleapis.com/fcm/send/x',
    'https://attacker.example/x',
    'https://fcm.googleapis.com.attacker.example/x',
    'https://fcm.googleapis.com@attacker.example/x',
    'https://attacker.example\@fcm.googleapis.com/x',
    'https://attacker.example/fcm.googleapis.com/x',
    'https://evilpush.apple.com/x',
    'https://push.apple.com/x',
    'https://x.notify.windows.com.evil.io/x',
    'https://fcm.googleapis.com:8443/x',
    'https://fcm.googleapis.com',
    'https://169.254.169.254/latest/meta-data',
    'https://localhost/x',
    'ftp://fcm.googleapis.com/x',
    'https://fcm.googleapis.com/ x',
    '', 'fcm.googleapis.com/x'];
  e text; ok boolean;
begin
  select * into c from pg_constraint
   where conrelid = 'public.push_subscriptions'::regclass and conname = 'push_subs_endpoint_is_push_service';
  if c.oid is null or c.contype <> 'c' then raise exception 'self-check: constraint missing'; end if;

  -- scratch copy of the real table's check constraints; dropped at the end
  create temp table _push_selfcheck (like public.push_subscriptions including constraints) on commit drop;
  foreach e in array good loop
    begin insert into _push_selfcheck (id, user_id, endpoint, p256dh, auth, created_at, fail_count) values (0, gen_random_uuid(), e, 'k', 'a', now(), 0);
    exception when check_violation then raise exception 'self-check: legit endpoint refused: %', e; end;
  end loop;
  foreach e in array bad loop
    ok := true;
    begin insert into _push_selfcheck (id, user_id, endpoint, p256dh, auth, created_at, fail_count) values (0, gen_random_uuid(), e, 'k', 'a', now(), 0);
    exception when check_violation then ok := false; end;
    if ok then raise exception 'self-check: bad endpoint accepted: %', e; end if;
  end loop;
  begin
    insert into _push_selfcheck (id, user_id, endpoint, p256dh, auth, created_at, fail_count) values (0, gen_random_uuid(), 'https://fcm.googleapis.com/' || repeat('a', 2100), 'k', 'a', now(), 0);
    raise exception 'self-check: 2100-char endpoint accepted';
  exception when check_violation then null; end;
  drop table _push_selfcheck;

  if has_table_privilege('anon', 'public.push_subscriptions', 'select') then raise exception 'self-check: anon can read push_subscriptions'; end if;
  if not has_table_privilege('authenticated', 'public.push_subscriptions', 'insert') then raise exception 'self-check: authenticated lost insert'; end if;
  raise notice 'security-push-endpoint: ok (constraint present, validated = %)', c.convalidated;
end $$;

commit;
