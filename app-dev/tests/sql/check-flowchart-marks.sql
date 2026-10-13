-- Postgres 16 check for sql/professify-flowchart-marks.sql, on a minimal stand-in of the Supabase pieces
-- it touches. Run from the repo root:
--   createdb marktest && psql -v ON_ERROR_STOP=1 -v sqlfile=sql/professify-flowchart-marks.sql -d marktest -f app-dev/tests/sql/check-flowchart-marks.sql; dropdb marktest
\set QUIET on
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;
create schema auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('test.uid', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
grant usage on schema public to anon, authenticated;
-- as on Supabase: every new table in public starts with everything granted to anon and authenticated
alter default privileges in schema public grant all on tables to anon, authenticated;
\i :sqlfile
\i :sqlfile
insert into auth.users values ('00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000b');

create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$ begin if not coalesce(c, false) then raise exception 'FAIL: %', what; end if; raise notice 'ok   %', what; end $$;
create function pg_temp.err(q text) returns text language plpgsql as $$ begin execute q; return null; exception when others then return sqlerrm; end $$;

select pg_temp.ok((select count(*) from pg_policies where tablename = 'flowchart_marks') = 3, 'run twice: still 3 policies');

set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
insert into public.flowchart_marks (user_id, major, slot_id, label) values (auth.uid(), 'Business Administration', 't3s4', 'GE · Area 3A');
select pg_temp.ok((select count(*) from public.flowchart_marks) = 1, 'A marks a row and reads it back');
insert into public.flowchart_marks (user_id, major, slot_id, label) values (auth.uid(), 'Business Administration', 't3s4', 'GE · Area 3A') on conflict (user_id, major, slot_id) do nothing;
select pg_temp.ok((select count(*) from public.flowchart_marks) = 1, 'the same mark twice is one row (on conflict do nothing)');
select pg_temp.ok(pg_temp.err($q$insert into public.flowchart_marks (user_id, major, slot_id) values ('00000000-0000-0000-0000-00000000000b', 'Business Administration', 't0s0')$q$) like '%row-level security%', 'A can''t mark a row for B');
select pg_temp.ok(pg_temp.err($q$insert into public.flowchart_marks (user_id, major, slot_id) values (auth.uid(), 'Business Administration', 't0s0; drop')$q$) like '%flowchart_marks_slot_ok%', 'a slot id that isn''t one is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.flowchart_marks (user_id, major, slot_id) values (auth.uid(), '', 't0s1')$q$) like '%flowchart_marks_major_len%', 'an empty major is refused');
select pg_temp.ok(pg_temp.err($q$insert into public.flowchart_marks (user_id, major, slot_id, label) values (auth.uid(), 'X', 't0s2', repeat('a', 161))$q$) like '%flowchart_marks_label_len%', 'a label over 160 characters is refused');
select pg_temp.ok(pg_temp.err($q$update public.flowchart_marks set label = 'x'$q$) like 'permission denied%', 'marks are never edited, only added or removed');
insert into public.flowchart_marks (user_id, major, slot_id) select auth.uid(), 'Physics', 't' || g || 's0' from generate_series(1, 299) g;
select pg_temp.ok((select count(*) from public.flowchart_marks) = 300, '300 marks fit');
select pg_temp.ok(pg_temp.err($q$insert into public.flowchart_marks (user_id, major, slot_id) values (auth.uid(), 'Physics', 't999s0')$q$) like '%row-level security%', 'the 301st is refused');

select set_config('test.uid', '00000000-0000-0000-0000-00000000000b', false);
select pg_temp.ok((select count(*) from public.flowchart_marks) = 0, 'B sees none of A''s marks');
delete from public.flowchart_marks where major = 'Business Administration';
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok((select count(*) from public.flowchart_marks where major = 'Business Administration') = 1, 'B''s delete removes nothing of A''s');
delete from public.flowchart_marks where major = 'Business Administration' and slot_id = 't3s4';
select pg_temp.ok((select count(*) from public.flowchart_marks where major = 'Business Administration') = 0, 'A unmarks the row');

reset role;
set role anon;
select pg_temp.ok(pg_temp.err($q$select * from public.flowchart_marks$q$) like 'permission denied%', 'signed out: nothing');
reset role;
delete from auth.users where id = '00000000-0000-0000-0000-00000000000a';
select pg_temp.ok((select count(*) from public.flowchart_marks) = 0, 'deleting the account deletes its marks');
\echo 'check-flowchart-marks: all passed'
