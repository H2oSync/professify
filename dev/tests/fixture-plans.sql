-- Enough of Supabase + TermChamp to run professify-plans.sql honestly. Shapes copied from
-- schools.sql, safety.sql, friend-sections.sql and term-scope.sql. Not part of the deliverable.
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;
create schema if not exists auth;
grant usage on schema auth, public to anon, authenticated;
create table if not exists auth.users (id uuid primary key, email text);
create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to anon, authenticated;

create table if not exists public.profiles (id uuid primary key references auth.users(id) on delete cascade, school text not null default 'calpoly');
create or replace function public.my_school() returns text language sql stable security definer set search_path = public as $$
  select p.school from public.profiles p where p.id = auth.uid() $$;
revoke all on function public.my_school() from public; grant execute on function public.my_school() to authenticated;
create or replace function public.school_of(uid uuid) returns text language sql stable security definer set search_path = public as $$
  select p.school from public.profiles p where p.id = uid $$;
revoke all on function public.school_of(uuid) from public, anon, authenticated;
alter table public.profiles enable row level security;
drop policy if exists profiles_read on public.profiles;
create policy profiles_read on public.profiles for select to authenticated using (school = public.my_school());
grant select on public.profiles to authenticated;

create table if not exists public.suspensions (user_id uuid primary key references auth.users(id) on delete cascade, until timestamptz);
create or replace function public.is_suspended(u uuid default null) returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.suspensions s where s.user_id = coalesce(u, auth.uid()) and (s.until is null or s.until > now())) $$;
revoke all on function public.is_suspended(uuid) from public; grant execute on function public.is_suspended(uuid) to authenticated;

create table if not exists public.friend_requests (from_user uuid references auth.users(id) on delete cascade, to_user uuid references auth.users(id) on delete cascade, status text, primary key (from_user, to_user));
alter table public.friend_requests enable row level security;
drop policy if exists fr_read on public.friend_requests;
create policy fr_read on public.friend_requests for select to authenticated using (auth.uid() in (from_user, to_user));
grant select on public.friend_requests to authenticated;

create table if not exists public.watch_sections (user_id uuid default auth.uid() references auth.users(id) on delete cascade, term text not null default '2268', code text, class_nbr text, section text, instructor text, days text, primary key (user_id, class_nbr, term));
alter table public.watch_sections enable row level security;
drop policy if exists ws_own on public.watch_sections;
create policy ws_own on public.watch_sections for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
grant all on public.watch_sections to authenticated;
