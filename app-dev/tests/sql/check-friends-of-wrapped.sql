-- Postgres 16 check for sql/professify-friends-of-blocks.sql (RUN 16) on a database that has RUN 7's 30-day delete,
-- after the first RUN 16 had replaced RUN 7's filter, on a minimal stand-in of the Supabase pieces
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
-- the version before RUN 16, then RUN 7's wrap as RUN 7 does it (renamed, a filter in front, the base closed to students)
\i sql/professify-friends-of.sql
create table public.account_deletions (user_id uuid primary key);
create function public.is_pending_deletion(p_user uuid) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.account_deletions d where d.user_id = p_user) $$;
grant execute on function public.is_pending_deletion(uuid) to anon, authenticated;
alter function public.friends_of(uuid) rename to friends_of__incl_pending;
create function public.friends_of(p_user uuid) returns table (id uuid, display_name text, username text, avatar_url text, mutual boolean)
  language sql stable security definer set search_path = public as
  $$ select x.* from public.friends_of__incl_pending(p_user) x where not public.is_pending_deletion(x.id) and not public.is_pending_deletion(p_user) $$;
revoke all on function public.friends_of__incl_pending(uuid) from public, anon, authenticated;
revoke all on function public.friends_of(uuid) from public, anon; grant execute on function public.friends_of(uuid) to authenticated;
-- the first RUN 16 re-created friends_of directly, over the filter: the same clobber
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

select pg_temp.ok((select prosrc from pg_proc where proname = 'friends_of') like '%is_pending_deletion%', 'RUN 7''s filter is back in front');
select pg_temp.ok(position('public.blocks' in (select prosrc from pg_proc where proname = 'friends_of__incl_pending')) > 0, 'the blocks filter went into friends_of__incl_pending');
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = 'Rowan*,Casey', 'my friend Avery: Rowan, Casey; not X (blocked me), not Y (I blocked)');
select pg_temp.ok(pg_temp.err($q$select * from public.friends_of__incl_pending('00000000-0000-0000-0000-00000000000f')$q$) like 'permission denied%', 'students can''t call the unfiltered one');
reset role;
insert into public.account_deletions values ('00000000-0000-0000-0000-00000000000c');
set role authenticated;
select set_config('test.uid', '00000000-0000-0000-0000-00000000000a', false);
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = 'Rowan*', 'Casey asked to delete her account: gone from Avery''s list at once');
reset role;
insert into public.account_deletions values ('00000000-0000-0000-0000-00000000000f');
set role authenticated;
select pg_temp.ok(pg_temp.names('00000000-0000-0000-0000-00000000000f') = '', 'Avery herself deleting: her list is empty');
reset role;
set role anon;
select pg_temp.ok(pg_temp.err($q$select * from public.friends_of('00000000-0000-0000-0000-00000000000f')$q$) like 'permission denied%', 'anon can''t call it');
reset role;
\echo 'check-friends-of (with RUN 7): all passed'
