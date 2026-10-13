-- Postgres 16 check for sql/professify-registration-days.sql (RUN 17), on a minimal stand-in of the Supabase pieces
-- it touches. Run from the repo root with run-check-registration-days.sh.
\set QUIET on
\pset tuples_only on
\o /dev/null
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;
create schema auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('test.uid', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
grant usage on schema public to anon, authenticated;
-- Supabase's default privileges: everything on every new table, to both
alter default privileges in schema public grant all on tables to anon, authenticated;
create table public.profiles (id uuid primary key, display_name text, school text not null default 'calpoly');
create table public.friend_requests (id bigserial primary key, from_user uuid, to_user uuid, status text);
create table public.blocks (blocker uuid, blocked uuid, primary key (blocker, blocked));
alter table public.friend_requests enable row level security; alter table public.blocks enable row level security; alter table public.profiles enable row level security;
-- three databases (run-check-registration-days.sh): pend=0 no 30-day delete; pend=1 RUN 7 in before RUN 17;
-- late=1 RUN 17 first, then RUN 7's wrap (its section 5, as it runs), then RUN 17 again
\if :pend
create table public.account_deletions (user_id uuid primary key);
create function public.is_pending_deletion(p_user uuid) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.account_deletions d where d.user_id = p_user) $$;
grant execute on function public.is_pending_deletion(uuid) to anon, authenticated;
\endif
\i :sqlfile
\if :late
create table public.account_deletions (user_id uuid primary key);
create function public.is_pending_deletion(p_user uuid) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.account_deletions d where d.user_id = p_user) $$;
grant execute on function public.is_pending_deletion(uuid) to anon, authenticated;
\i :run7wrap
\endif
\i :sqlfile

-- me (a); friends: Avery (f) shared, Rowan (b) not shared, Casey (c) at another school, X (x) who blocked me,
-- Y (y) whom I blocked, Wren (w) shared with no time; Zed (z) pending; Sam (s) a friend of Avery's, not mine
insert into auth.users values ('00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000f'), ('00000000-0000-0000-0000-00000000000b'),
 ('00000000-0000-0000-0000-00000000000c'), ('00000000-0000-0000-0000-0000000000a1'), ('00000000-0000-0000-0000-0000000000a2'), ('00000000-0000-0000-0000-0000000000a3'),
 ('00000000-0000-0000-0000-0000000000a4'), ('00000000-0000-0000-0000-0000000000a5');
insert into public.profiles (id, display_name, school) values
 ('00000000-0000-0000-0000-00000000000a','Me','calpoly'), ('00000000-0000-0000-0000-00000000000f','Avery','calpoly'), ('00000000-0000-0000-0000-00000000000b','Rowan','calpoly'),
 ('00000000-0000-0000-0000-00000000000c','Casey','ucsb'), ('00000000-0000-0000-0000-0000000000a1','X','calpoly'), ('00000000-0000-0000-0000-0000000000a2','Y','calpoly'),
 ('00000000-0000-0000-0000-0000000000a3','Zed','calpoly'), ('00000000-0000-0000-0000-0000000000a4','Wren','calpoly'), ('00000000-0000-0000-0000-0000000000a5','Sam','calpoly');
insert into public.friend_requests (from_user, to_user, status) values
 ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-00000000000f','accepted'),
 ('00000000-0000-0000-0000-00000000000b','00000000-0000-0000-0000-00000000000a','accepted'),
 ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-00000000000c','accepted'),
 ('00000000-0000-0000-0000-0000000000a1','00000000-0000-0000-0000-00000000000a','accepted'),
 ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-0000000000a2','accepted'),
 ('00000000-0000-0000-0000-0000000000a4','00000000-0000-0000-0000-00000000000a','accepted'),
 ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-0000000000a3','pending'),
 ('00000000-0000-0000-0000-00000000000f','00000000-0000-0000-0000-0000000000a5','accepted');
insert into public.blocks values ('00000000-0000-0000-0000-0000000000a1','00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-0000000000a2');
-- everyone's rows, as the table owner
insert into public.registration_days (user_id, term, day, at_time, shared) values
 ('00000000-0000-0000-0000-00000000000a','2274','2026-10-23','08:30',true),
 ('00000000-0000-0000-0000-00000000000f','2274','2026-10-21','08:00',true),
 ('00000000-0000-0000-0000-00000000000f','2268','2026-05-11','09:00',true),
 ('00000000-0000-0000-0000-00000000000b','2274','2026-10-20','09:00',false),
 ('00000000-0000-0000-0000-00000000000c','2274','2026-10-22','10:00',true),
 ('00000000-0000-0000-0000-0000000000a1','2274','2026-10-22','10:00',true),
 ('00000000-0000-0000-0000-0000000000a2','2274','2026-10-22','10:00',true),
 ('00000000-0000-0000-0000-0000000000a3','2274','2026-10-22','10:00',true),
 ('00000000-0000-0000-0000-0000000000a4','2274','2026-10-28',null,true),
 ('00000000-0000-0000-0000-0000000000a5','2274','2026-10-19','07:00',true);

create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$ begin if not coalesce(c, false) then raise exception 'FAIL: %', what; end if; raise notice 'ok   %', what; end $$;
create function pg_temp.err(q text) returns text language plpgsql as $$ begin execute q; return null; exception when others then return sqlerrm; end $$;
-- names for the checks, outside RLS (the caller can't read profiles here, and doesn't need to)
create table pg_temp.nm as select id, display_name from public.profiles;
grant select on pg_temp.nm to authenticated, anon;
create function pg_temp.seen(t text) returns text language sql as $$
  select coalesce(string_agg(n.display_name || '@' || r.day || coalesce(' ' || to_char(r.at_time, 'HH24:MI'), ''), ',' order by r.day, r.at_time nulls last), '')
  from public.friend_registration_days(t) r join pg_temp.nm n on n.id = r.user_id $$;

select pg_temp.ok((select count(*) from pg_policies where tablename = 'registration_days') = 4, 'four policies, all owner-only');
\if :pend
\set wrapped 1
\elif :late
\set wrapped 1
\else
\set wrapped 0
\endif
\if :wrapped
select pg_temp.ok((select prosrc from pg_proc where proname = 'friend_registration_days') like '%is_pending_deletion(x.user_id)%'
  and position('public.blocks' in (select prosrc from pg_proc where proname = 'friend_registration_days__incl_pending')) > 0, 'with the 30-day delete: the body behind, the filter in front');
\else
select pg_temp.ok(to_regprocedure('public.friend_registration_days__incl_pending(text)') is null, 'without it: one function');
\endif
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(pg_temp.seen('2274') = 'Avery@2026-10-21 08:00,Wren@2026-10-28', 'my friends'' days: Avery with her time, Wren with none; not Rowan (not shared), Casey (another school), X (blocked me), Y (I blocked), Zed (pending), Sam (not my friend), never me');
\if :wrapped
select pg_temp.ok(pg_temp.err($q$select * from public.friend_registration_days__incl_pending('2274')$q$) like 'permission denied%', 'students can''t call the unfiltered one');
reset role;
insert into public.account_deletions values ('00000000-0000-0000-0000-00000000000f');
set role authenticated;
select pg_temp.ok(pg_temp.seen('2274') = 'Wren@2026-10-28', 'Avery asked to delete her account: her day is gone at once');
reset role;
delete from public.account_deletions;
set role authenticated;
\endif
select pg_temp.ok(pg_temp.seen('2268') = 'Avery@2026-05-11 09:00', 'another term is its own list');
select pg_temp.ok((select count(*) from public.registration_days) = 1 and (select day from public.registration_days) = '2026-10-23', 'the table itself: only my own row');
select pg_temp.ok(pg_temp.err($q$insert into public.registration_days (user_id, term, day) values ('00000000-0000-0000-0000-00000000000f', '2276', '2027-03-01')$q$) is not null, 'I can''t write a row as someone else');
update public.registration_days set day = '2026-10-01' where user_id = '00000000-0000-0000-0000-00000000000f';
delete from public.registration_days where user_id = '00000000-0000-0000-0000-00000000000f';
reset role;
select pg_temp.ok((select day from public.registration_days where user_id = '00000000-0000-0000-0000-00000000000f' and term = '2274') = '2026-10-21'
  and (select count(*) from public.registration_days where user_id = '00000000-0000-0000-0000-00000000000f') = 2, 'my update and delete never reach Avery''s rows');
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
-- the app's upsert: insert … on conflict (user_id, term) do update
insert into public.registration_days (user_id, term, day, at_time, shared) values ('00000000-0000-0000-0000-00000000000a', '2274', '2026-10-26', '13:15', false)
  on conflict (user_id, term) do update set day = excluded.day, at_time = excluded.at_time, shared = excluded.shared, updated_at = now();
select pg_temp.ok((select day = '2026-10-26' and at_time = '13:15' and not shared from public.registration_days where term = '2274'), 'my upsert changes my own day, time and sharing');
update public.registration_days set updated_at = '2000-01-01' where term = '2274';
select pg_temp.ok((select updated_at > now() - interval '1 minute' from public.registration_days where term = '2274'), 'updated_at is the server''s clock, whatever the phone sends');
select pg_temp.ok(pg_temp.err($q$update public.registration_days set user_id = '00000000-0000-0000-0000-0000000000a5', term = '2280' where term = '2274'$q$) is not null, 'I can''t hand my row to someone else');
select pg_temp.ok(pg_temp.err($q$update public.registration_days set at_time = '08:30:15' where term = '2274'$q$) is not null, 'a time is to the minute');
select pg_temp.ok(pg_temp.err($q$update public.registration_days set term = '27' where term = '2274'$q$) is not null, 'a term is a 4-digit code');
-- Avery sees me only while I share
select set_config('test.uid', '00000000-0000-0000-0000-00000000000f', false);
select pg_temp.ok(position('Me@' in pg_temp.seen('2274')) = 0, 'with sharing off, my friend doesn''t see my day');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
update public.registration_days set shared = true where term = '2274';
select set_config('test.uid', '00000000-0000-0000-0000-00000000000f', false);
select pg_temp.ok(pg_temp.seen('2274') = 'Sam@2026-10-19 07:00,Me@2026-10-26 13:15', 'on again: Avery sees my day and time (and her own friend Sam)');
select set_config('test.uid', '00000000-0000-0000-0000-0000000000a1', false);
select pg_temp.ok(position('Me@' in pg_temp.seen('2274')) = 0, 'X, who blocked me, doesn''t see mine either');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000c', false);
select pg_temp.ok(pg_temp.seen('2274') = '', 'Casey, my friend at another school: nothing across the wall');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
delete from public.registration_days where term = '2274';
select pg_temp.ok((select count(*) from public.registration_days) = 0, 'Remove my day deletes my row');
select set_config('test.uid', '', false);
select pg_temp.ok(pg_temp.seen('2274') = '' and (select count(*) from public.registration_days) = 0, 'signed out: nothing');
reset role;
set role anon;
select pg_temp.ok(pg_temp.err($q$select * from public.friend_registration_days('2274')$q$) like 'permission denied%', 'anon can''t call it');
select pg_temp.ok(pg_temp.err($q$select * from public.registration_days$q$) like 'permission denied%', 'anon can''t read the table');
reset role;
\echo 'check-registration-days: all passed'
