-- Postgres 16 check for sql/professify-planner.sql (RUN 14) on a stand-in of the Supabase pieces it touches.
-- Run from the repo root (pg_cron / pg_net / vault are stubbed; their "create extension" lines are no-ops):
--   sh app-dev/tests/sql/run-check-planner.sh
\set QUIET on
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;
create schema auth; create schema cron; create schema net; create schema vault; create schema extensions;
create table auth.users (id uuid primary key, email text);
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('test.uid', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
grant usage on schema public to anon, authenticated;
create table cron.job (jobid serial, jobname text, schedule text, command text, active boolean default true);
create function cron.schedule(n text, s text, c text) returns int language plpgsql as $$ begin insert into cron.job (jobname, schedule, command) values (n, s, c); return 1; end $$;
create function cron.unschedule(n text) returns boolean language plpgsql as $$ begin delete from cron.job where jobname = n; return true; end $$;
create table net._http_response (id bigint, status_code int, content text, error_msg text);
create sequence net.req_seq;
create table net.sent (id bigint, url text, body jsonb, headers jsonb);
create function net.http_post(url text, body jsonb, headers jsonb, timeout_milliseconds int) returns bigint language plpgsql as $$
declare i bigint; begin i := nextval('net.req_seq'); insert into net.sent values (i, url, body, headers); return i; end $$;
create table vault.decrypted_secrets (name text, decrypted_secret text, created_at timestamptz default now());
\i :mig
\i :mig

insert into auth.users values ('00000000-0000-0000-0000-00000000000a', 'tate@calpoly.edu'), ('00000000-0000-0000-0000-00000000000b', 'bea@calpoly.edu'), ('00000000-0000-0000-0000-00000000000c', null);
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$ begin if not coalesce(c, false) then raise exception 'FAIL: %', what; end if; raise notice 'ok   %', what; end $$;
create function pg_temp.err(q text) returns text language plpgsql as $$ begin execute q; return null; exception when others then return sqlerrm; end $$;

set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
-- degree_audit: own row only, replaced on upload, never a grade
insert into public.degree_audit (user_id, catalog, major, requirements) values (auth.uid(), 'Fall Semester 2024', 'Business Administration', '[{"label":"GE Area 4B","status":"not","options":["ARCH 1121"]}]');
select pg_temp.ok((select count(*) from public.degree_audit) = 1, 'A reads A''s audit');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values ('00000000-0000-0000-0000-00000000000b', '[]')$q$) like '%row-level security%', 'A can''t write B''s audit');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"x","grade":"A-"}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_no_grades%', 'a grade key is refused by the table itself');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '{"a":1}') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_requirements_array%', 'requirements must be an array');
-- the check walks every level and every value (review 2026-10-08): nested keys, IDs and grades in text, notes
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"x","units":{"grade":"A-"}}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_no_grades%', 'a grade key one level down is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"EMPLID 1234567 Jordan Fixture","status":"not"}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_no_grades%', 'an ID in a label is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"BUS 214 Financial Accounting A- 4.00","status":"satisfied"}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_no_grades%', 'a grade beside units in a label is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"x","options":["9876543"]}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_no_grades%', 'a 7-digit number anywhere is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"x","note":"anything"}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) like '%degree_audit_no_grades%', 'no free-text note');
select pg_temp.ok(pg_temp.err($q$insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"BUS 4401/4411","status":"not","kind":"major","code":"R35-90","units":null,"courses":{"req":2,"used":1,"need":1},"options":["BUS 4401","BUS 4411"],"oneOf":false}]') on conflict (user_id) do update set requirements = excluded.requirements$q$) is null, 'a real line, as the phone sends it, is taken');
-- lines the student marked done: kept, and checked like the lines
update public.degree_audit set overrides = '[{"code":"R179-10","label":"Approved Elective","at":"2026-10-09T01:00:00Z"}]';
select pg_temp.ok((select overrides->0->>'code' from public.degree_audit) = 'R179-10', 'a line marked done is kept with the audit');
select pg_temp.ok(pg_temp.err($q$update public.degree_audit set overrides = '[{"code":null,"label":"EMPLID 1234567"}]'$q$) like '%degree_audit_overrides_ok%', 'a marked line can''t carry an ID');
select pg_temp.ok(pg_temp.err($q$update public.degree_audit set overrides = '{"code":"R1-1"}'$q$) like '%degree_audit_overrides_ok%', 'marked lines are a list');
insert into public.degree_audit (user_id, requirements) values (auth.uid(), '[{"label":"GE Area 4B","status":"satisfied"}]') on conflict (user_id) do update set requirements = excluded.requirements, read_at = now();
select pg_temp.ok((select requirements->0->>'status' from public.degree_audit) = 'satisfied', 'a re-upload replaces the row');
-- planner_prefs
insert into public.planner_prefs (user_id, priority, units) values (auth.uid(), 'professors', 14);
select pg_temp.ok(pg_temp.err($q$update public.planner_prefs set units = 21$q$) like '%planner_prefs_units_check%', 'units stay 12–20');
select pg_temp.ok(pg_temp.err($q$update public.planner_prefs set priority = 'ads'$q$) like '%planner_prefs_priority_check%', 'priority is one of three');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000b', false);
select pg_temp.ok((select count(*) from public.planner_prefs) = 0 and (select count(*) from public.degree_audit) = 0, 'B sees none of A''s rows');
-- dpr_flags: insert only, hashed, limited, never an id
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
insert into public.dpr_flags (who_hash, label, status, units) values ('whatever', 'GE Area 4B Lower-Division Social Sciences', 'not', '{"req":3,"used":0,"need":3}');
select pg_temp.ok(pg_temp.err($q$select * from public.dpr_flags$q$) like 'permission denied%', 'students can''t read flags');
select pg_temp.ok(pg_temp.err($q$insert into public.dpr_flags (who_hash, label) values ('x', 'EMPLID: 1234567 something')$q$) like '%can’t carry an ID%', 'a flag with an ID is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.dpr_flags (who_hash, label) values ('x', 'ENGL 1134 Writing and Rhetoric B+ 3.00')$q$) like '%can’t carry an ID%', 'a flag with a grade is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.dpr_flags (who_hash, label, major) values ('x', 'line', 'Name: Jordan')$q$) like '%can’t carry an ID%', 'the major field is checked too');
select pg_temp.ok(pg_temp.err($q$insert into public.dpr_flags (who_hash, label, note) values ('x', 'line', 'free text')$q$) like '%column "note"%', 'a flag has no free-text note');
select pg_temp.ok(pg_temp.err($q$insert into public.dpr_flags (who_hash, label, status) values ('x', 'line', 'whatever')$q$) like '%dpr_flags_status%', 'a flag''s status is a verdict');
do $$ begin for i in 1..28 loop insert into public.dpr_flags (who_hash, label) values ('x', 'line ' || i); end loop; end $$;
insert into public.dpr_flags (who_hash, label, status) values ('x', 'BUS 4488 · Spr 2026', 'row');
select pg_temp.ok(pg_temp.err($q$insert into public.dpr_flags (who_hash, label) values ('x', 'one more')$q$) like '%enough flags for today%', '30 a day, then a kind refusal');
reset role;
select pg_temp.ok((select count(*) from public.dpr_flags where who_hash = md5('00000000-0000-0000-0000-00000000000a' || ':' || current_date::text)) = 30, 'the hash is set by the trigger, whatever the client sent');
select pg_temp.ok((select count(*) from public.dpr_flags where who_hash = md5('00000000-0000-0000-0000-00000000000a')) = 0, 'the hash changes every day (it isn''t the account id''s own hash)');
select pg_temp.ok((select prosrc from pg_proc where proname = 'dpr_flags_limit') like '%pg_advisory_xact_lock%' and (select prosrc from pg_proc where proname = 'request_planner_link') like '%pg_advisory_xact_lock%', 'the daily limits are counted under a lock');
alter table public.dpr_flags disable trigger dpr_flags_limit;
insert into public.dpr_flags (created_at, who_hash, label) values (now() - interval '200 days', 'old', 'an old flag');
alter table public.dpr_flags enable trigger dpr_flags_limit;
set role authenticated;
-- the laptop link
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(public.request_planner_link() = 'ta***@calpoly.edu', 'the link is queued for my own address, masked back');
select public.request_planner_link(); select public.request_planner_link();
select pg_temp.ok(pg_temp.err($q$select public.request_planner_link()$q$) like '%3 times today%', 'a fourth in a day is refused');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000c', false);
select pg_temp.ok(pg_temp.err($q$select public.request_planner_link()$q$) like '%no email address%', 'no address, no email');
select pg_temp.ok(pg_temp.err($q$select * from public.planner_link_emails$q$) like 'permission denied%', 'the queue can''t be read');
select pg_temp.ok(pg_temp.err($q$select public.send_planner_links()$q$) like 'permission denied%', 'students can''t run the sender');
reset role;
-- (the sender runs in its own statement each time: an assertion that raises would roll its sends back)
create temp table runs (n int);
insert into runs select public.send_planner_links();
select pg_temp.ok((select max(n) from runs) = 0 and (select count(*) from net.sent) = 0, 'no key in the Vault: nothing is sent, nothing is lost');
insert into vault.decrypted_secrets (name, decrypted_secret) values ('resend_api_key', 're_test');
delete from runs; insert into runs select public.send_planner_links();
select pg_temp.ok((select max(n) from runs) = 3 and (select count(*) from net.sent) = 3, 'with a key, the three waiting emails go out');
select pg_temp.ok((select body->'to'->>0 from net.sent order by id limit 1) = 'tate@calpoly.edu' and (select body->>'subject' from net.sent limit 1) like '%Degree Progress Report%' and (select body->>'html' from net.sent limit 1) like '%Student Center%Academic Progress%' and (select body->>'html' from net.sent limit 1) like '%termchamp.com%', 'the email goes to the student, with the portal steps and the site link');
select pg_temp.ok((select count(distinct headers->>'Idempotency-Key') from net.sent) = 3 and (select headers->>'Idempotency-Key' from net.sent order by id limit 1) like 'termchamp-planner-link-%', 'each email has its own idempotency key');
insert into net._http_response select e.request_id, 200, '{"id":"x"}', null from public.planner_link_emails e where e.id <= 2;
insert into net._http_response select e.request_id, 422, 'bad address', null from public.planner_link_emails e where e.id = 3;
delete from runs; insert into runs select public.send_planner_links();
select pg_temp.ok((select count(*) from public.planner_link_emails where sent_at is not null and email is null) = 2, 'answered 2xx: sent, and the address is cleared');
select pg_temp.ok((select attempts from public.planner_link_emails where id = 3) = 1 and (select last_error from public.planner_link_emails where id = 3) like '422%', 'a refused send is retried later with the reason kept');
select pg_temp.ok((select count(*) from cron.job where jobname = 'termchamp-planner-links' and active) = 1, 'the sender is scheduled');
select pg_temp.ok((select count(*) from public.dpr_flags where label = 'an old flag') = 0 and (select count(*) from public.dpr_flags) = 30, 'flags older than 180 days are deleted by the sender');
-- a deleted account takes its queued emails with it
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000b', false);
select public.request_planner_link();
reset role;
delete from auth.users where id = '00000000-0000-0000-0000-00000000000b';
select pg_temp.ok((select count(*) from public.planner_link_emails where user_id = '00000000-0000-0000-0000-00000000000b') = 0, 'a deleted account''s queued emails go with it');
select 'ALL OK' as result;
