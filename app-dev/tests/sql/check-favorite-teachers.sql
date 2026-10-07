-- Postgres 16 check for sql/professify-favorite-teachers.sql, on a minimal stand-in of the
-- Supabase pieces it touches. Run from the repo root:
--   createdb favtest && psql -v ON_ERROR_STOP=1 -v sqlfile=sql/professify-favorite-teachers.sql -d favtest -f app-dev/tests/sql/check-favorite-teachers.sql; dropdb favtest
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
create table public.profiles (id uuid primary key, school text);
create table public.reviews (id serial primary key, user_id uuid, professor_key text, created_at timestamptz not null default clock_timestamp());
create function public.my_school() returns text language sql stable security definer set search_path = public as $$ select school from profiles where id = auth.uid() $$;
create function public.school_of(uid uuid) returns text language sql stable security definer set search_path = public as $$ select school from profiles where id = uid $$;
create table public.suspensions (user_id uuid);
create function public.is_suspended(u uuid default null) returns boolean language sql stable security definer set search_path = public as $$ select exists (select 1 from suspensions where user_id = u) $$;
\i :sqlfile
\i :sqlfile
insert into auth.users values ('00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000b'), ('00000000-0000-0000-0000-00000000000c'), ('00000000-0000-0000-0000-00000000000d'), ('00000000-0000-0000-0000-00000000000e'), ('00000000-0000-0000-0000-00000000000f');
insert into profiles values ('00000000-0000-0000-0000-00000000000a', 'calpoly'), ('00000000-0000-0000-0000-00000000000b', 'calpoly'), ('00000000-0000-0000-0000-00000000000c', 'sdsu'), ('00000000-0000-0000-0000-00000000000d', 'calpoly'), ('00000000-0000-0000-0000-00000000000e', 'calpoly'), ('00000000-0000-0000-0000-00000000000f', 'calpoly');
insert into reviews (user_id, professor_key) select '00000000-0000-0000-0000-00000000000a', k from unnest(array['p1|bus','p2|bus','p3|bus','p4|bus']) k;
insert into reviews (user_id, professor_key) values ('00000000-0000-0000-0000-00000000000b', 'p1|bus'), ('00000000-0000-0000-0000-00000000000c', 'p1|bus'), ('00000000-0000-0000-0000-00000000000d', 'p1|bus'), ('00000000-0000-0000-0000-00000000000e', 'p1|bus'), ('00000000-0000-0000-0000-00000000000f', 'p1|bus');
insert into suspensions values ('00000000-0000-0000-0000-00000000000d');

create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$ begin if not coalesce(c, false) then raise exception 'FAIL: %', what; end if; raise notice 'ok   %', what; end $$;
create function pg_temp.err(q text) returns text language plpgsql as $$ begin execute q; return null; exception when others then return sqlerrm; end $$;

set role authenticated;
-- A: three favorites, the fourth refused
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(public.set_favorite_teacher('p1|bus', true) = 1, 'first favorite → 1 used');
select pg_temp.ok(public.set_favorite_teacher('p1|bus', true) = 1, 'the same one twice is still 1');
select pg_temp.ok(public.set_favorite_teacher('p2|bus', true) = 2 and public.set_favorite_teacher('p3|bus', true) = 3, 'second and third');
select pg_temp.ok(pg_temp.err($q$select public.set_favorite_teacher('p4|bus', true)$q$) like 'You''ve used all 3%', 'a fourth is refused with the sentence');
select pg_temp.ok((select count(*) from public.my_favorite_teachers()) = 3, 'my list has 3');
select pg_temp.ok(public.set_favorite_teacher('p2|bus', false) = 2 and public.set_favorite_teacher('p4|bus', true) = 3, 'take one back, then the fourth fits');
select pg_temp.ok(pg_temp.err($q$select public.set_favorite_teacher('nobody|bus', true)$q$) like 'Rate this professor first%', 'only a professor you reviewed');
select pg_temp.ok(pg_temp.err($q$select public.set_favorite_teacher('P5|BUS', true)$q$) like 'Rate this professor first%' and pg_temp.err($q$select public.set_favorite_teacher(' p9|bus', true)$q$) like 'Rate this professor first%', 'a key that differs in case can''t slip past the cap');
select pg_temp.ok(pg_temp.err($q$select * from public.favorite_teachers$q$) like 'permission denied%', 'the table can''t be read directly');
select pg_temp.ok(pg_temp.err($q$insert into public.favorite_teachers values (auth.uid(), 'p9|bus')$q$) like 'permission denied%', 'the table can''t be written directly');
-- B (same school) and C (other school) pick p1
select set_config('test.uid', '00000000-0000-0000-0000-00000000000b', false);
select public.set_favorite_teacher('p1|bus', true);
select set_config('test.uid', '00000000-0000-0000-0000-00000000000c', false);
select public.set_favorite_teacher('p1|bus', true);
select pg_temp.ok((select count(*) from public.my_favorite_teachers()) = 1, 'C sees only C''s own list');
-- D is suspended
select set_config('test.uid', '00000000-0000-0000-0000-00000000000d', false);
select pg_temp.ok(pg_temp.err($q$select public.set_favorite_teacher('p1|bus', true)$q$) like 'This account can''t%', 'a suspended account can''t add one');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(not exists (select 1 from public.favorite_teacher_counts() where professor_key = 'p1|bus'), 'two picks: no count yet (the floor is 3)');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000e', false);
select public.set_favorite_teacher('p1|bus', true);
select pg_temp.ok((select n from public.favorite_teacher_counts() where professor_key = 'p1|bus') = 3, 'three picks at Cal Poly (A, B, E): the count shows 3');
select pg_temp.ok(not exists (select 1 from public.favorite_teacher_counts() where professor_key <> 'p1|bus'), 'professors under 3 picks never show');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000c', false);
select pg_temp.ok(not exists (select 1 from public.favorite_teacher_counts()), 'SDSU sees none of Cal Poly''s 3 picks (the school wall)');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
-- A deletes the p1 review: the favorite stops counting and frees a slot
reset role;
delete from reviews where user_id = '00000000-0000-0000-0000-00000000000a' and professor_key = 'p1|bus';
insert into reviews (user_id, professor_key) values ('00000000-0000-0000-0000-00000000000a', 'p5|bus');
set role authenticated;
select pg_temp.ok(not exists (select 1 from public.favorite_teacher_counts() where professor_key = 'p1|bus'), 'a deleted review''s favorite stops counting at once (3 → 2, under the floor)');
select pg_temp.ok((select count(*) from public.my_favorite_teachers()) = 2, 'and leaves my list');
reset role;
insert into reviews (user_id, professor_key) values ('00000000-0000-0000-0000-00000000000a', 'p1|bus');
set role authenticated;
select pg_temp.ok(not exists (select 1 from public.my_favorite_teachers() where my_favorite_teachers = 'p1|bus') and not exists (select 1 from public.favorite_teacher_counts() where professor_key = 'p1|bus'), 'reviewing again doesn''t bring the old favorite back');
select pg_temp.ok(public.set_favorite_teacher('p5|bus', true) = 3, 'its slot is free again');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000d', false);
select pg_temp.ok(public.set_favorite_teacher('p1|bus', false) = 0, 'a suspended account can still take one back');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
-- signed out
select set_config('test.uid', '', false);
select pg_temp.ok(pg_temp.err($q$select public.set_favorite_teacher('p1|bus', true)$q$) like 'Sign in%', 'signed out is refused');
select pg_temp.ok((select count(*) from public.favorite_teacher_counts()) = 0, 'signed out reads no counts');
reset role;
set role anon;
select pg_temp.ok(pg_temp.err($q$select * from public.favorite_teacher_counts()$q$) like 'permission denied%', 'anon can''t call counts');
reset role;
-- account deletion cascades
delete from auth.users where id = '00000000-0000-0000-0000-00000000000b';
select pg_temp.ok((select count(*) from favorite_teachers where user_id = '00000000-0000-0000-0000-00000000000b') = 0, 'deleting an account deletes its favorites');
