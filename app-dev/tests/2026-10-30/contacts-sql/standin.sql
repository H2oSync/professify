-- Minimal stand-in for the production pieces termchamp-contacts-2026-10-30.sql touches.
-- Columns, grants, policies and function bodies mirror production as read on 2026-10-30.
create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls;
create schema auth; create schema extensions; create schema vault;
create extension pgcrypto schema extensions;
grant usage on schema public, auth, extensions to anon, authenticated;

create table auth.users (id uuid primary key, email varchar(255), phone text, banned_until timestamptz, deleted_at timestamptz);
create function auth.uid() returns uuid language sql stable as $$
  select nullif(coalesce(current_setting('request.jwt.claim.sub', true), (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')), '')::uuid $$;

-- Vault (supabase_vault's surface: secrets, decrypted_secrets, create_secret)
create table vault.secrets (id uuid primary key default gen_random_uuid(), name text unique, secret text, description text);
create view vault.decrypted_secrets as select id, name, secret as decrypted_secret, description from vault.secrets;
create function vault.create_secret(new_secret text, new_name text, new_description text default '') returns uuid language sql as $$
  insert into vault.secrets (name, secret, description) values (new_name, new_secret, new_description) returning id $$;

create table public.profiles (id uuid primary key references auth.users(id) on delete cascade, edu_email text, display_name text, instagram_handle text,
  created_at timestamptz default now(), major text, concentration text, class_standing text, avatar_url text, username text, pinned_friends uuid[], school text not null default 'calpoly');
create table public.blocks (blocker uuid not null, blocked uuid not null, created_at timestamptz not null default now(), primary key (blocker, blocked));
create table public.rate_log (user_id uuid not null, bucket text not null, at timestamptz not null default now());
create index rate_log_user_bucket_at on public.rate_log (user_id, bucket, at);
alter table public.rate_log enable row level security;
create table public.account_deletions (user_id uuid primary key, requested_at timestamptz default now(), purge_after timestamptz, delete_reviews boolean, attempts int, last_error text);
create table public.suspensions (user_id uuid, until timestamptz, reason text, set_by uuid, created_at timestamptz default now());

-- production's grants on profiles: table-level INSERT/UPDATE, column-level SELECT
grant insert, update on public.profiles to authenticated;
grant select (id, display_name, username, avatar_url, major, class_standing, concentration, instagram_handle, school) on public.profiles to authenticated;
alter table public.profiles enable row level security;
create policy profiles_read on public.profiles for select using (true);
create policy profiles_update on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

create function public.school_from_email(email text) returns text language sql immutable as $$
  select case when email is null then null
    when lower(email) ~ '^[^@\s]+@([a-z0-9-]+\.)*calpoly\.edu$' then 'calpoly'
    when lower(email) ~ '^[^@\s]+@([a-z0-9-]+\.)*sdsu\.edu$' then 'sdsu' else null end $$;
create function public.my_school() returns text language sql stable security definer set search_path = public as $$
  select coalesce(public.school_from_email(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email'),
                  (select p.school from public.profiles p where p.id = auth.uid())) $$;
create function public.is_demo(u uuid) returns boolean language sql stable security definer set search_path = public as $$
  select coalesce((select p.edu_email like '%@appreview.calpoly.edu' from public.profiles p where p.id = u), false) $$;
create function public.is_pending_deletion(p_user uuid) returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.account_deletions d where d.user_id = p_user) $$;
create function public.blocked_between(a uuid, b uuid) returns boolean language sql stable security definer set search_path = public as $$
  select case when auth.uid() is not null and auth.uid() is distinct from a and auth.uid() is distinct from b then false
    else exists (select 1 from public.blocks where (blocker = a and blocked = b) or (blocker = b and blocked = a)) end $$;

-- people (all synthetic)
insert into auth.users (id, email) values
 ('00000000-0000-4000-8000-000000000001', 'me@calpoly.edu'),
 ('00000000-0000-4000-8000-000000000002', 'avery@calpoly.edu'),
 ('00000000-0000-4000-8000-000000000003', 'blocked@calpoly.edu'),
 ('00000000-0000-4000-8000-000000000004', 'leaving@calpoly.edu'),
 ('00000000-0000-4000-8000-000000000005', 'Sdsu.Person@sdsu.edu'),
 ('00000000-0000-4000-8000-000000000006', 'demo@appreview.calpoly.edu'),
 ('00000000-0000-4000-8000-000000000007', 'suspended@calpoly.edu'),
 ('00000000-0000-4000-8000-000000000008', 'Mixed.Case@CalPoly.edu');
update auth.users set deleted_at = now() where false;
insert into public.profiles (id, edu_email, display_name, username, school) values
 ('00000000-0000-4000-8000-000000000001', 'me@calpoly.edu', 'Me Fixture', 'me', 'calpoly'),
 ('00000000-0000-4000-8000-000000000002', 'avery@calpoly.edu', 'Avery Fixture', 'avery', 'calpoly'),
 ('00000000-0000-4000-8000-000000000003', 'blocked@calpoly.edu', 'Blocked Fixture', 'blocked', 'calpoly'),
 ('00000000-0000-4000-8000-000000000004', 'leaving@calpoly.edu', 'Leaving Fixture', 'leaving', 'calpoly'),
 ('00000000-0000-4000-8000-000000000005', 'Sdsu.Person@sdsu.edu', 'Sdsu Fixture', 'sdsu', 'sdsu'),
 ('00000000-0000-4000-8000-000000000006', 'demo@appreview.calpoly.edu', 'Demo Fixture', 'demo', 'calpoly'),
 ('00000000-0000-4000-8000-000000000007', 'suspended@calpoly.edu', 'Suspended Fixture', 'susp', 'calpoly'),
 ('00000000-0000-4000-8000-000000000008', 'mixed.case@calpoly.edu', 'Mixed Fixture', 'mixed', 'calpoly');
insert into public.blocks (blocker, blocked) values ('00000000-0000-4000-8000-000000000003', '00000000-0000-4000-8000-000000000001');
insert into public.account_deletions (user_id) values ('00000000-0000-4000-8000-000000000004');
insert into public.suspensions (user_id, until) values ('00000000-0000-4000-8000-000000000007', null);
