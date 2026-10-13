-- Postgres 16 check for sql/professify-commitments.sql (RUN 18), on a minimal stand-in of the Supabase pieces
-- it touches. Run from the repo root with run-check-commitments.sh.
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
-- three databases (run-check-commitments.sh): pend=0 no 30-day delete; pend=1 RUN 7 in before RUN 18;
-- late=1 RUN 18 first, then RUN 7 wrap (its section 5, as it runs), then RUN 18 again
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
-- me (a); friends: Avery (f) busy, Rowan (b) only-me item, Casey (c) at another school, X (x) who blocked me,
-- Y (y) whom I blocked, Wren (w) busy; Zed (z) pending; Sam (s) a friend of Avery's, not mine
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
insert into public.commitments (id, user_id, kind, name, days, start_min, end_min, busy) values
 ('10000000-0000-4000-8000-00000000000a','00000000-0000-0000-0000-00000000000a','work','Barista shift','TR',960,1200,true),
 ('10000000-0000-4000-8000-00000000000f','00000000-0000-0000-0000-00000000000f','practice','Soccer','MW',1080,1170,true),
 ('10000000-0000-4000-8000-0000000000b1','00000000-0000-0000-0000-00000000000b','work','Secret job','F',600,720,false),
 ('10000000-0000-4000-8000-00000000000c','00000000-0000-0000-0000-00000000000c','club','Chess','T',600,660,true),
 ('10000000-0000-4000-8000-0000000000a1','00000000-0000-0000-0000-0000000000a1','work',null,'M',600,660,true),
 ('10000000-0000-4000-8000-0000000000a2','00000000-0000-0000-0000-0000000000a2','work',null,'M',600,660,true),
 ('10000000-0000-4000-8000-0000000000a3','00000000-0000-0000-0000-0000000000a3','work',null,'M',600,660,true),
 ('10000000-0000-4000-8000-0000000000a4','00000000-0000-0000-0000-0000000000a4','other','Band','SU',540,600,true),
 ('10000000-0000-4000-8000-0000000000a5','00000000-0000-0000-0000-0000000000a5','work',null,'F',480,540,true);

create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$ begin if not coalesce(c, false) then raise exception 'FAIL: %', what; end if; raise notice 'ok   %', what; end $$;
create function pg_temp.err(q text) returns text language plpgsql as $$ begin execute q; return null; exception when others then return sqlerrm; end $$;
create table pg_temp.nm as select id, display_name from public.profiles;
grant select on pg_temp.nm to authenticated, anon;
create function pg_temp.seen() returns text language sql as $$
  select coalesce(string_agg(n.display_name || '@' || r.days || ' ' || r.start_min || '-' || r.end_min, ',' order by n.display_name), '')
  from public.friend_busy_blocks() r join pg_temp.nm n on n.id = r.user_id $$;

select pg_temp.ok((select count(*) from pg_policies where tablename = 'commitments') = 4, 'four policies, all owner-only');
select pg_temp.ok((select count(*) from information_schema.columns where table_name = 'commitments' and column_name in ('kind', 'name')) = 2
  and position('kind' in pg_get_function_result('public.friend_busy_blocks()'::regprocedure)) = 0 and position('name' in pg_get_function_result('public.friend_busy_blocks()'::regprocedure)) = 0, 'friends get days and times only — never the kind or the name');
\if :pend
\set wrapped 1
\elif :late
\set wrapped 1
\else
\set wrapped 0
\endif
\if :wrapped
select pg_temp.ok((select prosrc from pg_proc where proname = 'friend_busy_blocks') like '%is_pending_deletion(x.user_id)%'
  and position('public.blocks' in (select prosrc from pg_proc where proname = 'friend_busy_blocks__incl_pending')) > 0, 'with the 30-day delete: the body behind, the filter in front');
\else
select pg_temp.ok(to_regprocedure('public.friend_busy_blocks__incl_pending()') is null, 'without it: one function');
\endif
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(pg_temp.seen() = 'Avery@MW 1080-1170,Wren@SU 540-600', 'my friends'' Busy times: Avery and Wren; not Rowan (only him), Casey (another school), X (blocked me), Y (I blocked), Zed (pending), Sam (not my friend), never me');
\if :wrapped
select pg_temp.ok(pg_temp.err($q$select * from public.friend_busy_blocks__incl_pending()$q$) like 'permission denied%', 'students can''t call the unfiltered one');
reset role;
insert into public.account_deletions values ('00000000-0000-0000-0000-00000000000f');
set role authenticated;
select pg_temp.ok(pg_temp.seen() = 'Wren@SU 540-600', 'Avery asked to delete her account: her times are gone at once');
reset role;
delete from public.account_deletions;
set role authenticated;
\endif
select pg_temp.ok((select count(*) from public.commitments) = 1 and (select name from public.commitments) = 'Barista shift', 'the table itself: only my own rows (with my names)');
select pg_temp.ok(pg_temp.err($q$insert into public.commitments (id, user_id, kind, days, start_min, end_min) values ('20000000-0000-4000-8000-000000000001', '00000000-0000-0000-0000-00000000000f', 'work', 'M', 60, 120)$q$) is not null, 'I can''t write a row as someone else');
update public.commitments set name = 'mine now' where user_id = '00000000-0000-0000-0000-00000000000f';
delete from public.commitments where user_id = '00000000-0000-0000-0000-00000000000f';
reset role;
select pg_temp.ok((select name from public.commitments where user_id = '00000000-0000-0000-0000-00000000000f') = 'Soccer', 'my update and delete never reach Avery''s rows');
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
-- the app's upsert: insert … on conflict (id) do update
insert into public.commitments (id, user_id, kind, name, days, start_min, end_min, busy) values ('10000000-0000-4000-8000-00000000000a', '00000000-0000-0000-0000-00000000000a', 'work', 'Barista', 'TRU', 960, 1230, false)
  on conflict (id) do update set kind = excluded.kind, name = excluded.name, days = excluded.days, start_min = excluded.start_min, end_min = excluded.end_min, busy = excluded.busy;
select pg_temp.ok((select days = 'TRU' and end_min = 1230 and not busy from public.commitments), 'my upsert changes my own item');
select pg_temp.ok(pg_temp.err($q$update public.commitments set end_min = 900$q$) is not null, 'it has to end after it starts');
select pg_temp.ok(pg_temp.err($q$update public.commitments set days = 'MX'$q$) is not null, 'days are letters of MTWRFSU');
select pg_temp.ok(pg_temp.err($q$update public.commitments set kind = 'party'$q$) is not null, 'a kind is work, practice, club or other');
select pg_temp.ok(pg_temp.err($q$update public.commitments set user_id = '00000000-0000-0000-0000-0000000000a5'$q$) is not null, 'I can''t hand my row to someone else');
-- Avery sees mine only while it's Busy
select set_config('test.uid', '00000000-0000-0000-0000-00000000000f', false);
select pg_temp.ok(position('Me@' in pg_temp.seen()) = 0, 'with Busy off, my friend doesn''t see it');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
update public.commitments set busy = true;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000f', false);
select pg_temp.ok(pg_temp.seen() = 'Me@TRU 960-1230,Sam@F 480-540', 'on again: Avery sees my Busy times (and her own friend Sam)');
select set_config('test.uid', '00000000-0000-0000-0000-0000000000a1', false);
select pg_temp.ok(position('Me@' in pg_temp.seen()) = 0, 'X, who blocked me, doesn''t see mine either');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000c', false);
select pg_temp.ok(pg_temp.seen() = '', 'Casey, my friend at another school: nothing across the wall');
reset role;
set role anon;
select pg_temp.ok(pg_temp.err($q$select * from public.friend_busy_blocks()$q$) like 'permission denied%', 'anon can''t call it');
select pg_temp.ok(pg_temp.err($q$select * from public.commitments$q$) like 'permission denied%', 'anon can''t read the table');
reset role;
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
delete from public.commitments;
select pg_temp.ok((select count(*) from public.commitments) = 0, 'Remove deletes my row');
select set_config('test.uid', '', false);
