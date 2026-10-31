-- Local Postgres 16 harness for 01/02 (and 99). Stubs only what production has and PG16 lacks:
-- Supabase roles, pg_net's net.http_post (records calls), and the push tables/functions 01 builds on,
-- copied from production's catalog 2026-10-30. Fails loudly (ON_ERROR_STOP + raise) on any wrong result.
\set ON_ERROR_STOP on
create role anon; create role authenticated; create role service_role;
create schema net;
create table net.calls(url text, headers jsonb, at timestamptz default now());
create function net.http_post(url text, body jsonb default '{}', headers jsonb default '{}') returns bigint
language sql as $$ insert into net.calls(url, headers) values (url, headers) returning 1::bigint $$;

create table public.push_config(key text primary key, value text);
create table public.push_prefs(user_id uuid primary key, seats boolean, friends boolean, quiet_from smallint, quiet_to smallint, prefs jsonb, updated_at timestamptz);
create table public.push_subscriptions(id bigint generated always as identity primary key, user_id uuid not null, endpoint text not null unique,
  p256dh text not null, auth text not null, ua text, created_at timestamptz not null default now(), last_ok_at timestamptz, fail_count int not null default 0);
create table public.push_outbox(id bigint generated always as identity primary key, user_id uuid not null, kind text not null, title text not null,
  body text not null, url text not null default '/', tag text, dedupe_key text not null, created_at timestamptz not null default now(),
  send_after timestamptz not null default now(), sent_at timestamptz, attempts int not null default 0, last_error text, claimed_at timestamptz);
create unique index push_outbox_dedupe_idx on public.push_outbox(user_id, dedupe_key);
create table public.push_queue(id bigserial primary key, user_id uuid not null, kind text not null, created_at timestamptz not null default now());
create function public.push_cfg(k text) returns text language sql stable security definer set search_path to 'public'
as $$ select value from public.push_config where key = k $$;
create function public.push_fire_at(p_local timestamp, p_from smallint, p_to smallint) returns timestamptz language sql immutable as $$
  select case when p_from = p_to then null
    when (p_from > p_to and (extract(hour from p_local)::int >= p_from or extract(hour from p_local)::int < p_to))
      or (p_from < p_to and extract(hour from p_local)::int >= p_from and extract(hour from p_local)::int < p_to)
    then (date_trunc('day', p_local) + make_interval(days => case when extract(hour from p_local)::int >= p_to then 1 else 0 end)
          + make_interval(hours => p_to)) at time zone 'America/Los_Angeles'
    else null end $$;
-- the production push_cleanup and push_enqueue as they are today, so 01 replaces real definitions
create function public.push_cleanup() returns void language sql security definer set search_path to 'public' as $$
delete from public.push_queue where created_at < now() - interval '7 days' and kind in ('dm', 'group', 'like');
delete from public.push_queue where created_at < now() - interval '400 days'; $$;

\i 99-rollback-noncron.sql
\i 01-webpush-sender.sql
\i 01-webpush-sender.sql

-- users: W has a web subscription (no quiet hours), P has none, Q has a subscription + default prefs
\set W '''00000000-0000-0000-0000-00000000000a'''
\set P '''00000000-0000-0000-0000-00000000000b'''
\set Q '''00000000-0000-0000-0000-00000000000c'''
insert into push_prefs(user_id, seats, friends, quiet_from, quiet_to) values (:W, true, false, 0, 0);
insert into push_subscriptions(user_id, endpoint, p256dh, auth) values
  (:W, 'https://fcm.googleapis.com/fcm/send/w1', 'k', 'a'), (:W, 'https://web.push.apple.com/w2', 'k', 'a'),
  (:Q, 'https://fcm.googleapis.com/fcm/send/q1', 'k', 'a');

do $$
declare W uuid := '00000000-0000-0000-0000-00000000000a'; P uuid := '00000000-0000-0000-0000-00000000000b';
        n int; r record; c int;
begin
  -- gate: P (no subscription) gets no row; W does; dedupe still holds
  assert public.push_enqueue(P, 'seat_open', 't', 'b', '/?tab=sched', 'seat-1', 'seat_open:1:d') = false, 'gate P';
  assert public.push_enqueue(W, 'seat_open', 't', 'b', '/?tab=sched', 'seat-1', 'seat_open:1:d') = true, 'W enqueue';
  assert public.push_enqueue(W, 'seat_open', 't', 'b', '/?tab=sched', 'seat-1', 'seat_open:1:d') = false, 'dedupe';
  assert public.push_enqueue(W, 'free', 't', 'b', '/', 'f', 'free:1') = false, 'friends off';
  select count(*) into n from push_outbox; assert n = 1, 'one row';

  -- backlog like production: stale rows, rows for P (pre-gate), a 13h-old seat alert, a 1-day-old move
  insert into push_outbox(user_id, kind, title, body, tag, dedupe_key, created_at, send_after) values
    (P, 'moved', 't', 'b', 'm', 'old1', now() - interval '40 days', now() - interval '40 days'),
    (W, 'moved', 't', 'b', 'm', 'old2', now() - interval '3 days',  now() - interval '3 days'),
    (W, 'seat_open', 't', 'b', 's', 'old3', now() - interval '13 hours', now() - interval '13 hours'),
    (W, 'moved', 't', 'b', 'm', 'fresh-move', now() - interval '1 day', now() - interval '1 day'),
    (P, 'seat_open', 't', 'b', 's', 'p-fresh', now() - interval '2 hours', now() - interval '2 hours'),
    (W, 'waitlist', 't', 'b', 'w', 'quiet', now(), now() + interval '5 hours');  -- in quiet hours

  -- kick: nothing configured -> no call; configured -> exactly one call with the header
  perform public.push_web_kick_due();
  select count(*) into n from net.calls; assert n = 0, 'no config, no call';
  insert into push_config values ('function_url', 'https://x.supabase.co/functions/v1/send-push'), ('secret', 'S');
  perform public.push_web_kick_due();
  select count(*) into n from net.calls where url = 'https://x.supabase.co/functions/v1/send-web-push'
     and headers ->> 'x-push-secret' = 'S'; assert n = 1, 'derived url kick';

  -- claim BEFORE purge: max-age + subscription filters already keep stale/undeliverable rows out
  c := 0;
  for r in select * from public.push_web_claim_subs(100) loop
    c := c + 1;
    assert r.user_id = W, 'only subscribed users';
    assert jsonb_array_length(r.subs) = 2 and r.subs -> 0 ? 'endpoint' and r.subs -> 0 ? 'p256dh', 'subs attached';
    assert r.attempts = 1, 'attempts incremented';
  end loop;
  assert c = 2, 'claims fresh seat_open + 1-day move, got ' || c;  -- not old2 (3d), old3 (13h seat), quiet (future), P rows
  select count(*) into n from public.push_web_claim_subs(100); assert n = 0, 'claimed rows not re-handed within 10 min';
  update push_outbox set claimed_at = now() - interval '11 minutes' where dedupe_key = 'fresh-move';
  select count(*) into n from public.push_web_claim_subs(100); assert n = 1, 're-handed after 10 min';
  delete from net.calls; perform public.push_web_kick_due();
  select count(*) into n from net.calls; assert n = 0, 'nothing claimable -> no kick';
  update push_outbox set attempts = 5, claimed_at = now() - interval '11 minutes' where dedupe_key = 'fresh-move';
  select count(*) into n from public.push_web_claim_subs(100); assert n = 0, '5 tries max';
end $$;

\i 02-backlog-purge.sql

do $$
declare n int;
begin
  select count(*) into n from push_outbox where last_error like 'skipped: stale (backlog%'; assert n = 2, 'purged >2d: ' || n;
  select count(*) into n from push_outbox where last_error = 'skipped: stale'; assert n = 1, '13h seat expired: ' || n;
  select count(*) into n from push_outbox where last_error = 'skipped: no subscription'; assert n = 1, 'P fresh expired: ' || n;
  select count(*) into n from push_outbox where last_error like 'gave up:%'; assert n = 1, 'out of tries closed: ' || n;
  select count(*) into n from push_outbox where sent_at is null; assert n = 2, 'left: claimed seat + quiet waitlist: ' || n;
  -- retention: finished > 30 days ago deleted, unsent > 60 days deleted
  insert into push_outbox(user_id, kind, title, body, dedupe_key, created_at, sent_at) values
    ('00000000-0000-0000-0000-00000000000a', 'moved', 't', 'b', 'r1', now() - interval '45 days', now() - interval '31 days');
  perform public.push_cleanup();
  select count(*) into n from push_outbox where dedupe_key in ('r1', 'old1'); assert n = 1, 'retention r1 gone, old1 (sent today) kept';
end $$;

-- grants
do $$ begin
  assert not has_function_privilege('anon', 'public.push_web_claim_subs(integer)', 'EXECUTE');
  assert not has_function_privilege('authenticated', 'public.push_web_expire()', 'EXECUTE');
  assert has_function_privilege('service_role', 'public.push_web_claim_subs(integer)', 'EXECUTE');
end $$;

-- rollback restores the old behaviour (gate gone)
\i 99-rollback-noncron.sql
do $$ begin
  assert public.push_enqueue('00000000-0000-0000-0000-00000000000b', 'moved', 't', 'b', '/', 'm', 'after-rollback') = true, 'rollback restores ungated enqueue';
  assert to_regprocedure('public.push_web_claim_subs(integer)') is null;
end $$;
select 'ALL LOCAL SQL CHECKS PASSED' as result;
