-- Enough of Supabase and the live messaging/safety schema to run professify-chat-likes-hides.sql
-- honestly: roles, auth.uid() from the session setting, the three messaging tables with their real
-- read/write policies, and the helper functions the new policies call (copied from
-- professify-messaging.sql and professify-safety.sql). Not part of the deliverable.
\set ON_ERROR_STOP on
\set QUIET on
\i fixture.sql
create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  kind text not null default 'direct' check (kind in ('direct','group')),
  title text, created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(), last_at timestamptz not null default now());
create table if not exists public.conversation_members (
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  joined_at timestamptz not null default now(), last_read_at timestamptz not null default 'epoch',
  primary key (conversation_id, user_id));
create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  sender uuid not null references auth.users(id) on delete cascade,
  kind text not null default 'text' check (kind in ('text','class','professor','ask')),
  body text, payload jsonb, created_at timestamptz not null default now());
create table if not exists public.blocks (
  blocker uuid not null references auth.users(id) on delete cascade,
  blocked uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(), primary key (blocker, blocked));
create or replace function public.is_conv_member(p_conv uuid, p_user uuid) returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.conversation_members m where m.conversation_id = p_conv and m.user_id = p_user) $$;
create or replace function public.blocked_between(a uuid, b uuid) returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.blocks where (blocker = a and blocked = b) or (blocker = b and blocked = a)) $$;
create or replace function public.is_suspended(u uuid default null) returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.suspensions s where s.user_id = coalesce(u, auth.uid()) and (s.until is null or s.until > now())) $$;
alter table public.conversations enable row level security;
alter table public.conversation_members enable row level security;
alter table public.messages enable row level security;
drop policy if exists "members read the thread" on public.messages;
create policy "members read the thread" on public.messages for select using ( public.is_conv_member(conversation_id, auth.uid()) );
drop policy if exists "members read the member list" on public.conversation_members;
create policy "members read the member list" on public.conversation_members for select using ( public.is_conv_member(conversation_id, auth.uid()) );
grant usage on schema public to authenticated, anon;
grant usage on schema auth to authenticated, anon;
grant execute on function auth.uid() to authenticated, anon;
grant select on public.messages, public.conversation_members, public.conversations to authenticated;
grant execute on function public.is_conv_member(uuid,uuid), public.blocked_between(uuid,uuid), public.is_suspended(uuid) to authenticated;
