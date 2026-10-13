-- Postgres 16 check for sql/professify-friends-of-blocks.sql (RUN 16), on a minimal stand-in of the Supabase pieces
-- it touches. Run from the repo root with run-check-friends-of.sh.
\set QUIET on
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('test.uid', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
grant usage on schema public to anon, authenticated;
alter default privileges in schema public grant all on tables to anon, authenticated;
create table public.profiles (id uuid primary key, display_name text, username text, avatar_url text);
create table public.friend_requests (id bigserial primary key, from_user uuid, to_user uuid, status text);
create table public.blocks (blocker uuid, blocked uuid, primary key (blocker, blocked));
-- RLS on, no policies for anyone: only a SECURITY DEFINER function can read these
alter table public.friend_requests enable row level security; alter table public.blocks enable row level security; alter table public.profiles enable row level security;
-- the version before RUN 16, so the file runs over it as it will on production
\i sql/professify-friends-of.sql
\i :sqlfile
\i :sqlfile
-- me (a), Avery (v), Rowan (r, my friend too), Casey (c), X who blocked me (x), Y whom I blocked (y), Zed a stranger (z)
insert into public.profiles values
 ('00000000-0000-0000-0000-00000000000a','Me','me',null), ('00000000-0000-0000-0000-00000000000f','Avery','avery',null),
 ('00000000-0000-0000-0000-00000000000b','Rowan','rowan',null), ('00000000-0000-0000-0000-00000000000c','Casey','casey',null),
 ('00000000-0000-0000-0000-0000000000a1','X','x',null), ('00000000-0000-0000-0000-0000000000a2','Y','y',null), ('00000000-0000-0000-0000-0000000000a3','Zed','zed',null);
insert into public.friend_requests (from_user, to_user, status) values
 ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-00000000000f','accepted'),
 ('00000000-0000-0000-0000-00000000000b','00000000-0000-0000-0000-00000000000a','accepted'),
 ('00000000-0000-0000-0000-00000000000f','00000000-0000-0000-0000-00000000000b','accepted'),
 ('00000000-0000-0000-0000-00000000000c','00000000-0000-0000-0000-00000000000f','accepted'),
 ('00000000-0000-0000-0000-00000000000f','00000000-0000-0000-0000-0000000000a1','accepted'),
 ('00000000-0000-0000-0000-0000000000a2','00000000-0000-0000-0000-00000000000f','accepted'),
 ('00000000-0000-0000-0000-00000000000f','00000000-0000-0000-0000-0000000000a3','pending');
insert into public.blocks values ('00000000-0000-0000-0000-0000000000a1','00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-0000000000a2');

create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$ begin if not coalesce(c, false) then raise exception 'FAIL: %', what; end if; raise notice 'ok   %', what; end $$;
create function pg_temp.err(q text) returns text language plpgsql as $$ begin execute q; return null; exception when others then return sqlerrm; end $$;
create function pg_temp.names(u uuid) returns text language sql as $$ select coalesce(string_agg(display_name || case when mutual then '*' else '' end, ',' order by mutual desc, display_name), '') from public.friends_of(u) $$;

select pg_temp.ok((select prosecdef from pg_proc where proname = 'friends_of'), 'friends_of is SECURITY DEFINER');
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = 'Rowan*,Casey', 'my friend Avery: Rowan (also mine) first, then Casey; not me, not X (blocked me), not Y (I blocked), not Zed (pending)');
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000c') = '', 'Casey isn''t my friend: nothing at all');
select pg_temp.ok(pg_temp.err($q$select * from public.friend_requests$q$) is null and (select count(*) from public.friend_requests) = 0, 'the edges themselves stay unreadable');
select set_config('test.uid', '00000000-0000-0000-0000-00000000000b', false);
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = 'Me*,Casey,X,Y', 'Rowan (no blocks of his own) sees Avery''s whole list');
select set_config('test.uid', '00000000-0000-0000-0000-0000000000a1', false);
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = 'Casey,Rowan,Y', 'X (who blocked me) doesn''t see me in Avery''s list either');
select set_config('test.uid', '', false);
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = '', 'signed out: nothing');
reset role;
set role anon;
select pg_temp.ok(pg_temp.err($q$select * from public.friends_of('00000000-0000-0000-0000-00000000000f')$q$) like 'permission denied%', 'anon can''t call it');
reset role;
\echo 'check-friends-of: all passed'
