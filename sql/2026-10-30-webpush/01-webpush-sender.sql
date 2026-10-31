-- =================================================================================================
-- 01-webpush-sender.sql — drafted 2026-10-30, NOT run on production. Tested on local Postgres 16
-- (sql/test-local.sh). One transaction, idempotent, safe to run twice.
--
-- WHAT THIS DOES (plain words)
--   The website's notifications (seat open, waitlist down to 3, section moved) have been written to
--   public.push_outbox since Sep 11 but nothing ever sent them. This file adds the database half of
--   the sender; the edge function send-web-push is the other half.
--
--   1. push_web_max_age(kind)      how long an alert is worth sending: seat/waitlist 12 hours (covers
--                                  the 10-hour quiet-hours delay), everything else 2 days.
--   2. push_web_claim_subs(limit)  hands the edge function a batch of due rows WITH that student's
--                                  browser subscriptions (like push_claim does for phone tokens).
--                                  Only rows for students who HAVE a subscription, only rows younger
--                                  than their max age. Marks each claimed (claimed_at, attempts+1);
--                                  a claim older than 10 minutes is handed out again, 5 tries at most.
--   3. push_web_expire()           marks stale or undeliverable unsent rows as done
--                                  (sent_at = now(), last_error = 'skipped: ...'), never sends them.
--   4. push_enqueue                same as today, plus ONE new line: no browser subscription, no row.
--                                  (push_queue_add already does the same for phones.) This is why the
--                                  outbox holds 776 rows for 36 students when 1 student can receive.
--   5. push_cleanup                same two push_queue deletes as today, plus outbox retention:
--                                  expire stale rows, delete rows finished more than 30 days ago.
--   6. push_web_kick_due()         what cron calls every minute: if anything is due for someone with
--                                  a subscription, POST the edge function with x-push-secret, exactly
--                                  like push_kick_due/push_kick. URL comes from push_config
--                                  'web_function_url' (or, if that row is missing, 'function_url' with
--                                  /send-push swapped for /send-web-push). Secret from push_config
--                                  'secret' — the same one send-push already uses.
--
--   The old push_web_claim is left in place (nothing calls it); drop it later if you like.
-- =================================================================================================
begin;

-- 1 -----------------------------------------------------------------------------------------------
create or replace function public.push_web_max_age(p_kind text)
returns interval language sql immutable
as $$ select case when p_kind in ('seat_open', 'waitlist') then interval '12 hours'
                  else interval '2 days' end $$;

-- 2 -----------------------------------------------------------------------------------------------
create or replace function public.push_web_claim_subs(p_limit integer default 100)
returns table(id bigint, user_id uuid, kind text, title text, body text, url text, tag text,
              attempts integer, subs jsonb)
language sql security definer set search_path to 'public'
as $$
  with picked as (
    select o.id from public.push_outbox o
    where o.sent_at is null and o.send_after <= now() and o.attempts < 5
      and (o.claimed_at is null or o.claimed_at < now() - interval '10 minutes')
      and o.created_at > now() - public.push_web_max_age(o.kind)
      and exists (select 1 from public.push_subscriptions s where s.user_id = o.user_id)
    order by o.id
    limit least(greatest(coalesce(p_limit, 100), 1), 500)
    for update of o skip locked),
  upd as (
    update public.push_outbox o set claimed_at = now(), attempts = o.attempts + 1
    from picked where o.id = picked.id
    returning o.id, o.user_id, o.kind, o.title, o.body, o.url, o.tag, o.attempts)
  select u.id, u.user_id, u.kind, u.title, u.body, u.url, u.tag, u.attempts,
         coalesce((select jsonb_agg(jsonb_build_object('id', s.id, 'endpoint', s.endpoint,
                                                       'p256dh', s.p256dh, 'auth', s.auth,
                                                       'fail_count', s.fail_count) order by s.id)
                   from public.push_subscriptions s where s.user_id = u.user_id), '[]'::jsonb)
  from upd u order by u.id
$$;

-- 3 -----------------------------------------------------------------------------------------------
create or replace function public.push_web_expire()
returns integer language plpgsql security definer set search_path to 'public'
as $$
declare a int; b int;
begin
  update public.push_outbox o set sent_at = now(), last_error = 'skipped: stale'
   where o.sent_at is null and o.created_at <= now() - public.push_web_max_age(o.kind);
  get diagnostics a = row_count;
  -- Due for over an hour and the student has no browser subscription: it can never be delivered.
  update public.push_outbox o set sent_at = now(), last_error = 'skipped: no subscription'
   where o.sent_at is null and o.send_after <= now() - interval '1 hour'
     and not exists (select 1 from public.push_subscriptions s where s.user_id = o.user_id);
  get diagnostics b = row_count;
  -- Out of tries: close it so it stops looking pending.
  update public.push_outbox o set sent_at = now(),
         last_error = left('gave up: ' || coalesce(o.last_error, ''), 300)
   where o.sent_at is null and o.attempts >= 5
     and (o.claimed_at is null or o.claimed_at < now() - interval '10 minutes');
  return a + b;
end $$;

-- 4 -----------------------------------------------------------------------------------------------
-- Identical to production's push_enqueue (read 2026-10-30) except the block marked NEW.
create or replace function public.push_enqueue(p_user uuid, p_kind text, p_title text, p_body text,
                                               p_url text, p_tag text, p_dedupe text)
returns boolean language plpgsql security definer set search_path to 'public'
as $function$
declare
  pref     public.push_prefs%rowtype;
  want     boolean;
  /* timestamp, NOT timestamptz, and this cost an hour. `now() at time zone 'America/Los_Angeles'`
     yields a timestamp WITHOUT a zone — LA wall time. Assigning that to a timestamptz makes
     Postgres re-read the wall clock as if it were the SESSION zone (UTC on Supabase), so every
     later date_trunc and extract silently worked in the wrong zone and quiet hours produced a
     send_after in the PAST — which does not delay anything, it sends immediately. A quiet-hours
     feature that is a no-op is worse than none, because you believe it is on. */
  local_ts timestamp;
  fire_at  timestamptz;
begin
  if p_user is null or p_kind is null or p_dedupe is null then return false; end if;

  -- NEW 2026-10-30: nobody to deliver to, so no row (push_queue_add does the same for phones).
  if not exists (select 1 from public.push_subscriptions s where s.user_id = p_user) then
    return false;
  end if;

  select * into pref from public.push_prefs where user_id = p_user;
  if not found then
    -- no row yet: seats on (you asked by watching), friends off (nobody asked)
    pref.seats := true; pref.friends := false; pref.quiet_from := 22; pref.quiet_to := 8;
  end if;

  want := case
            when p_kind in ('seat_open','waitlist','moved','dropped') then pref.seats
            when p_kind = 'free'                                      then pref.friends
            else false                                                        -- unknown kind: no
          end;
  if not want then return false; end if;
  -- sync-2026-10-15: a kind switched off on the phone is off here too
  if coalesce(pref.prefs ->> p_kind, '') = 'false' then return false; end if;

  -- Cal Poly is in one timezone and so is every student at it. Hard-coding it is honest here;
  -- a per-user timezone would be a column nobody fills in.
  local_ts := now() at time zone 'America/Los_Angeles';

  fire_at := coalesce(public.push_fire_at(local_ts, pref.quiet_from, pref.quiet_to), now());

  insert into public.push_outbox(user_id, kind, title, body, url, tag, dedupe_key, send_after)
  values (p_user, p_kind, left(p_title,120), left(p_body,200),
          coalesce(nullif(left(p_url,200),''),'/'), left(p_tag,80), left(p_dedupe,200), fire_at)
  on conflict (user_id, dedupe_key) do nothing;

  return found;
end;
$function$;

-- 5 -----------------------------------------------------------------------------------------------
create or replace function public.push_cleanup()
returns void language plpgsql security definer set search_path to 'public'
as $$
begin
  -- unchanged (production 2026-10-30)
  delete from public.push_queue where created_at < now() - interval '7 days' and kind in ('dm', 'group', 'like');
  delete from public.push_queue where created_at < now() - interval '400 days';
  -- NEW: website outbox retention
  perform public.push_web_expire();
  delete from public.push_outbox where sent_at is not null and sent_at < now() - interval '30 days';
  delete from public.push_outbox where created_at < now() - interval '60 days';   -- belt and braces
end $$;

-- 6 -----------------------------------------------------------------------------------------------
create or replace function public.push_web_kick_due()
returns void language plpgsql security definer set search_path to 'public'
as $$
declare
  u text := coalesce(nullif(push_cfg('web_function_url'), ''),
                     replace(push_cfg('function_url'), '/functions/v1/send-push', '/functions/v1/send-web-push'));
  s text := push_cfg('secret');
begin
  if u is null or s is null or u !~ '/send-web-push' then return; end if;
  if exists (select 1 from public.push_outbox o
              where o.sent_at is null and o.send_after <= now() and o.attempts < 5
                and (o.claimed_at is null or o.claimed_at < now() - interval '10 minutes')
                and o.created_at > now() - public.push_web_max_age(o.kind)
                and exists (select 1 from public.push_subscriptions x where x.user_id = o.user_id)) then
    perform net.http_post(url := u, body := '{}'::jsonb,
      headers := jsonb_build_object('content-type', 'application/json', 'x-push-secret', s));
  end if;
end $$;

-- Grants: only the edge function (service_role) may claim; nothing else is callable from the API.
revoke all on function public.push_web_max_age(text)       from public, anon, authenticated;
revoke all on function public.push_web_claim_subs(integer) from public, anon, authenticated;
revoke all on function public.push_web_expire()            from public, anon, authenticated;
revoke all on function public.push_web_kick_due()          from public, anon, authenticated;
revoke all on function public.push_cleanup()               from public, anon, authenticated;
revoke all on function public.push_enqueue(uuid, text, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.push_web_claim_subs(integer) to service_role;
grant execute on function public.push_web_max_age(text)       to service_role;
grant execute on function public.push_cleanup()               to service_role;   -- as before

-- Self-check (rolls the whole file back if wrong)
do $$ begin
  if has_function_privilege('anon', 'public.push_web_claim_subs(integer)', 'EXECUTE')
     or has_function_privilege('authenticated', 'public.push_web_claim_subs(integer)', 'EXECUTE')
     or not has_function_privilege('service_role', 'public.push_web_claim_subs(integer)', 'EXECUTE') then
    raise exception '01-webpush-sender: push_web_claim_subs grants wrong';
  end if;
  if has_function_privilege('authenticated', 'public.push_web_kick_due()', 'EXECUTE') then
    raise exception '01-webpush-sender: push_web_kick_due grants wrong';
  end if;
end $$;

commit;
