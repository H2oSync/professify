-- Checks sql/professify-deletion-emails.sql and sql/professify-group-names-filter.sql on Postgres 16.
-- Builds on check-delete-30-days.sql (its stand-in and the 30-day migration, run first by the runner),
-- then adds stand-ins for what Supabase provides: auth.users.email, pg_net (net.http_post records
-- each call; net._http_response is filled by the test, as pg_net would), and vault.decrypted_secrets.
-- Run: ./run-check-deletion-emails.sh
\set ON_ERROR_STOP 1

alter table auth.users add column if not exists email text;
drop schema if exists net cascade; drop schema if exists vault cascade; drop schema if exists extensions cascade;
create schema net; create schema vault; create schema extensions;
create sequence net.seq;
create table net.calls (id bigint, url text, body jsonb, headers jsonb);
create table net._http_response (id bigint primary key, status_code int, content text, error_msg text, created timestamptz default now());
create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds int default 5000)
returns bigint language plpgsql as $$ declare i bigint := nextval('net.seq'); begin insert into net.calls values (i, url, body, headers); return i; end $$;
create table vault.decrypted_secrets (name text, decrypted_secret text, created_at timestamptz default now());

-- the migration, twice
\i :mig2
\i :mig2

-- the purge as the 30-day file left it, back to a delete_my_account that works for everyone
create or replace function public.delete_my_account() returns void language plpgsql security definer set search_path = public as $$
begin if auth.uid() = '99999999-0000-0000-0000-000000000009' then raise exception 'boom'; end if; delete from auth.users where id = auth.uid(); end $$;
create or replace function storage.protect_delete() returns trigger language plpgsql as $$ begin return null; end $$;
delete from public.account_deletions;

-- 1. nobody but the functions can read the queue or run the sender
do $$ begin
  if has_table_privilege('authenticated', 'public.account_emails', 'select') or has_table_privilege('anon', 'public.account_emails', 'select') then raise exception 'FAIL students can read the queue'; end if;
  if has_function_privilege('authenticated', 'public.send_account_emails()', 'execute') then raise exception 'FAIL students can run the sender'; end if;
  if has_function_privilege('authenticated', 'public.account_email_body(text,jsonb)', 'execute') then raise exception 'FAIL students can run the body'; end if;
  if not exists (select 1 from cron.job where jobname = 'termchamp-account-emails' and schedule = '*/5 * * * *' and command like '%send_account_emails%') then raise exception 'FAIL no email job'; end if;
end $$;

-- 2. Fay asks to delete: one "scheduled" email queued; changing the reviews choice doesn't queue another
insert into auth.users (id, email) values ('ffffffff-0000-0000-0000-000000000006', 'fay@calpoly.edu'), ('11111111-0000-0000-0000-000000000011', 'gus@calpoly.edu');
do $$ declare t timestamptz; begin
  perform set_config('request.jwt.claims', '{"sub":"ffffffff-0000-0000-0000-000000000006","role":"authenticated"}', true);
  set local role authenticated;
  t := public.request_account_deletion(false);
  perform public.request_account_deletion(true);
  reset role;
  if (select count(*) from public.account_emails where user_id = 'ffffffff-0000-0000-0000-000000000006') <> 1 then raise exception 'FAIL expected one scheduled email'; end if;
  if not exists (select 1 from public.account_emails where kind = 'scheduled' and email = 'fay@calpoly.edu' and (detail->>'purge_after')::timestamptz = t) then raise exception 'FAIL the scheduled email lacks the address or the date'; end if;
end $$;

-- 3. No key: nothing is sent, nothing is lost
do $$ declare n int; begin
  n := public.send_account_emails();
  if n <> 0 or exists (select 1 from net.calls) then raise exception 'FAIL sent without a key'; end if;
  if not exists (select 1 from public.account_emails where email = 'fay@calpoly.edu' and sent_at is null and attempts = 0) then raise exception 'FAIL the email was dropped without a key'; end if;
end $$;

-- 4. With a key: one call to Resend, from noreply, to Fay, with the date; then in flight, then sent
insert into vault.decrypted_secrets (name, decrypted_secret) values ('resend_api_key', 're_test_key');
do $$ declare n int; c record; begin
  n := public.send_account_emails();
  if n <> 1 then raise exception 'FAIL expected 1 sent, got %', n; end if;
  select * into c from net.calls order by id desc limit 1;
  if c.url <> 'https://api.resend.com/emails' or c.headers->>'Authorization' <> 'Bearer re_test_key' then raise exception 'FAIL wrong call %', c; end if;
  if c.headers->>'Idempotency-Key' !~ '^termchamp-account-email-\d+$' then raise exception 'FAIL no idempotency key %', c.headers; end if;
  if c.body->>'from' <> 'TermChamp <noreply@termchamp.com>' or c.body->'to'->>0 <> 'fay@calpoly.edu' or c.body->>'reply_to' <> 'support@termchamp.com' then raise exception 'FAIL wrong addresses %', c.body; end if;
  if c.body->>'subject' !~ '^Your TermChamp account will be deleted on [A-Z][a-z]{2} \d{1,2}, 20\d\d$' then raise exception 'FAIL subject %', c.body->>'subject'; end if;
  if c.body->>'html' !~ 'Recover my account' or c.body->>'html' !~ 'permanently deleted on' then raise exception 'FAIL body says nothing about recovering'; end if;
  -- next run, no answer yet: not sent again
  n := public.send_account_emails();
  if n <> 0 or (select count(*) from net.calls) <> 1 then raise exception 'FAIL re-sent while in flight'; end if;
  -- Resend answers 200: marked sent, and the address is gone
  insert into net._http_response (id, status_code, content) values (c.id, 200, '{"id":"x"}');
  perform public.send_account_emails();
  if not exists (select 1 from public.account_emails where user_id = 'ffffffff-0000-0000-0000-000000000006' and sent_at is not null and email is null and request_id is null) then raise exception 'FAIL not marked sent, or the address kept'; end if;
end $$;

-- 5. A refusal is kept with its reason and retried; after 5 tries it stops
do $$ declare c record; n int; begin
  insert into public.account_emails (kind, user_id, email, detail) values ('deleted', '22222222-0000-0000-0000-000000000022', 'hal@calpoly.edu', '{"delete_reviews":false}');
  perform public.send_account_emails();
  select * into c from net.calls order by id desc limit 1;
  insert into net._http_response (id, status_code, content) values (c.id, 422, '{"message":"bad"}');
  perform public.send_account_emails();   -- settles the 422; the retry waits
  if not exists (select 1 from public.account_emails where email = 'hal@calpoly.edu' and attempts = 1 and last_error like '422%' and request_id is null and next_try_at > now() + interval '10 minutes') then raise exception 'FAIL a refusal was not kept, or retried at once'; end if;
  update public.account_emails set next_try_at = now() where email = 'hal@calpoly.edu';
  perform public.send_account_emails();
  if not exists (select 1 from public.account_emails where email = 'hal@calpoly.edu' and request_id is not null) then raise exception 'FAIL not retried when due'; end if;
  update public.account_emails set attempts = 8, request_id = null, next_try_at = now() where email = 'hal@calpoly.edu';
  n := (select count(*) from net.calls);
  perform public.send_account_emails();
  if (select count(*) from net.calls) <> n then raise exception 'FAIL sent after 8 tries'; end if;
  -- no answer for an hour: tried again
  update public.account_emails set attempts = 0, request_id = 999999, requested_at = now() - interval '2 hours' where email = 'hal@calpoly.edu';
  perform public.send_account_emails();
  if not exists (select 1 from public.account_emails where email = 'hal@calpoly.edu' and attempts = 1 and last_error = 'no response') then raise exception 'FAIL a lost answer was not retried'; end if;
end $$;

-- 5b. One bad row never stops the others; asking twice queues one email
do $$ declare n int; begin
  insert into public.account_emails (kind, user_id, email, detail) values ('deleted', '55555555-0000-0000-0000-000000000055', 'bad@calpoly.edu', '{"requested_at":"not a date"}');
  insert into public.account_emails (kind, user_id, email, detail) values ('deleted', '66666666-0000-0000-0000-000000000066', 'ok@calpoly.edu', '{"delete_reviews":true}');
  insert into public.account_deletions (user_id, purge_after) select '55555555-0000-0000-0000-000000000055', now() + interval '30 days' where false;
  perform public.send_account_emails();
  if not exists (select 1 from net.calls where body->'to'->>0 = 'ok@calpoly.edu') then raise exception 'FAIL a bad row stopped the good one'; end if;
end $$;
insert into auth.users (id, email) values ('77777777-0000-0000-0000-000000000077', 'jo@calpoly.edu');
do $$ begin
  perform set_config('request.jwt.claims', '{"sub":"77777777-0000-0000-0000-000000000077","role":"authenticated"}', true);
  set local role authenticated; perform public.request_account_deletion(false); perform public.cancel_account_deletion(); perform public.request_account_deletion(false); reset role;
  perform set_config('request.jwt.claims', '', true);
  if (select count(*) from public.account_emails where user_id = '77777777-0000-0000-0000-000000000077') <> 1 then raise exception 'FAIL ask, recover, ask queued two emails'; end if;
end $$;

-- 6. Gus asks, then recovers before the email goes: it isn't sent
do $$ declare n int; begin
  perform set_config('request.jwt.claims', '{"sub":"11111111-0000-0000-0000-000000000011","role":"authenticated"}', true);
  set local role authenticated; perform public.request_account_deletion(false); perform public.cancel_account_deletion(); reset role;
  perform set_config('request.jwt.claims', '', true);
  n := (select count(*) from net.calls where body->'to'->>0 = 'gus@calpoly.edu');
  perform public.send_account_emails();
  if (select count(*) from net.calls where body->'to'->>0 = 'gus@calpoly.edu') <> n then raise exception 'FAIL emailed a recovered account'; end if;
  if exists (select 1 from public.account_emails where email = 'gus@calpoly.edu') then raise exception 'FAIL the recovered account''s address was kept'; end if;
end $$;

-- 7. The purge: Fay (delete reviews) is deleted and gets "deleted"; Ivy fails and gets nothing
insert into auth.users (id, email) values ('99999999-0000-0000-0000-000000000009', 'ivy@calpoly.edu');
insert into public.account_deletions (user_id, purge_after, delete_reviews) values ('99999999-0000-0000-0000-000000000009', now() - interval '1 minute', false);
update public.account_deletions set purge_after = now() - interval '1 minute' where user_id = 'ffffffff-0000-0000-0000-000000000006';
do $$ declare n int; c record; begin
  n := public.purge_due_account_deletions();
  if n <> 1 then raise exception 'FAIL expected 1 purged, got %', n; end if;
  if exists (select 1 from auth.users where id = 'ffffffff-0000-0000-0000-000000000006') then raise exception 'FAIL Fay was not deleted'; end if;
  if not exists (select 1 from public.account_emails where kind = 'deleted' and email = 'fay@calpoly.edu' and (detail->>'delete_reviews')::boolean) then raise exception 'FAIL no "deleted" email for Fay'; end if;
  if exists (select 1 from public.account_emails where kind = 'deleted' and email = 'ivy@calpoly.edu') then raise exception 'FAIL a failed deletion queued a "deleted" email'; end if;
  if not exists (select 1 from public.account_deletions where user_id = '99999999-0000-0000-0000-000000000009' and attempts = 1 and last_error = 'boom') then raise exception 'FAIL Ivy''s failure was not recorded'; end if;
  perform public.send_account_emails();
  select * into c from net.calls where body->'to'->>0 = 'fay@calpoly.edu' order by id desc limit 1;
  if c.body->>'subject' <> 'Your TermChamp account has been deleted' or c.body->>'html' !~ 'Your reviews were deleted too' then raise exception 'FAIL the "deleted" email %', c.body->>'subject'; end if;
end $$;

-- 8. The body: keeping reviews is said; the date is in Pacific time with the year
do $$ declare b jsonb; begin
  b := public.account_email_body('deleted', '{"delete_reviews":false,"requested_at":"2026-10-04T23:30:00Z"}');
  if b->>'html' !~ 'You chose to keep your reviews up' or b->>'html' !~ 'Oct 4, 2026' then raise exception 'FAIL keep-reviews body %', b->>'html'; end if;
  b := public.account_email_body('scheduled', '{"purge_after":"2026-11-04T05:00:00Z"}');
  if b->>'subject' <> 'Your TermChamp account will be deleted on Nov 3, 2026' then raise exception 'FAIL Pacific date %', b->>'subject'; end if;
end $$;

-- 9. Addresses are never kept past 14 days, sent or not
do $$ begin
  insert into public.account_emails (kind, user_id, email, created_at, attempts) values ('deleted', '33333333-0000-0000-0000-000000000033', 'old@calpoly.edu', now() - interval '15 days', 5);
  perform public.send_account_emails();
  if exists (select 1 from public.account_emails where email = 'old@calpoly.edu') then raise exception 'FAIL an old address was kept'; end if;
end $$;

-- 10. An email can't stop a deletion being asked for
do $$ begin
  insert into auth.users (id, email) values ('44444444-0000-0000-0000-000000000044', 'kim@calpoly.edu');
  alter table public.account_emails add constraint test_breaks check (kind <> 'scheduled') not valid;
  perform set_config('request.jwt.claims', '{"sub":"44444444-0000-0000-0000-000000000044","role":"authenticated"}', true);
  set local role authenticated; perform public.request_account_deletion(false); reset role;
  perform set_config('request.jwt.claims', '', true);
  if not exists (select 1 from public.account_deletions where user_id = '44444444-0000-0000-0000-000000000044') then raise exception 'FAIL a broken queue stopped the request'; end if;
  alter table public.account_emails drop constraint test_breaks;
end $$;

-- ---------- group names ----------
create table if not exists public.conversations (id bigserial primary key, kind text default 'group', title text, created_by uuid, last_at timestamptz default now());
alter table public.profiles add column if not exists username text;
\i sql/professify-word-filter.sql
\i :mig3
\i :mig3
do $$ begin
  begin
    insert into public.conversations (title) values ('fuck this class');
    raise exception 'FAIL a filtered group name was accepted';
  exception when sqlstate 'P0001' then
    if sqlerrm !~ '^A group name can''t contain' then raise exception 'FAIL wrong message %', sqlerrm; end if;
  end;
  insert into public.conversations (title) values ('Study crew'), (null);
  insert into public.conversations (kind, title) values ('direct', null);
  -- a grandfathered name doesn't block other updates
  alter table public.conversations disable trigger wf_guard_conversations;
  insert into public.conversations (title) values ('shit crew');
  alter table public.conversations enable trigger wf_guard_conversations;
  update public.conversations set last_at = now() where title = 'shit crew';
  begin
    update public.conversations set title = 'more shit' where title = 'Study crew';
    raise exception 'FAIL a filtered rename was accepted';
  exception when sqlstate 'P0001' then null;
  end;
end $$;

-- ---------- no more delete-at-once ----------
\i sql/professify-lock-immediate-delete.sql
\i sql/professify-lock-immediate-delete.sql
insert into auth.users (id, email) values ('88888888-0000-0000-0000-000000000088', 'lee@calpoly.edu');
insert into public.account_deletions (user_id, purge_after) values ('88888888-0000-0000-0000-000000000088', now() - interval '1 minute');
do $$ begin
  perform set_config('request.jwt.claims', '{"sub":"88888888-0000-0000-0000-000000000088","role":"authenticated"}', true);
  set local role authenticated;
  begin perform public.delete_my_account(); raise exception 'FAIL a student can still delete at once';
  exception when insufficient_privilege then null; end;
  reset role; perform set_config('request.jwt.claims', '', true);
  -- the purge runs as its owner, as pg_cron does on Supabase (not a superuser)
  perform public.purge_due_account_deletions();
  if exists (select 1 from auth.users where id = '88888888-0000-0000-0000-000000000088') then raise exception 'FAIL the purge stopped working after the lock'; end if;
end $$;

select 'check-deletion-emails: all 10 blocks, group names and the lock passed' as result;
