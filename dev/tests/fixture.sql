-- Enough of Supabase to run the migration honestly: the roles, the auth schema, auth.uid() driven
-- by a session setting the way Supabase drives it, and the one app table the migration references.
-- Nothing here is part of the deliverable; it exists so the real file runs against real Postgres.
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then create role service_role nologin; end if;
end $$;

create schema if not exists auth;

create table if not exists auth.users (
  id    uuid primary key,
  email text
);

create or replace function auth.uid() returns uuid
language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

create table if not exists public.suspensions (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  until      timestamptz,
  reason     text,
  created_at timestamptz not null default now()
);
