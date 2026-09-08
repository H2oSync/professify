-- =============================================================================================
-- Professify — shared groups
-- Written 2026-08-26 for Tate. Run this in the Supabase SQL editor.
--
-- WHY THIS EXISTS
-- Groups today live entirely in localStorage on the device that made them. The other people in
-- a group have no row, no record, nothing — their app has never heard of it. That is why
-- "notify the person" and "let them make the same changes on their side" cannot be built on the
-- client: there is no their-side to build on. These two tables are that.
--
-- THE TRUST MODEL, from Tate 2026-08-26, verbatim:
--   "when i make a group it notifies the person and says youve been added to the group"
--        -> members are added directly. No invite, no accept step.
--   "Make them be able to do all the changes that i could on their side of the group"
--        -> FLAT permissions. There is no owner privilege. Any member can rename, add, remove.
--   "when i mute it shouldnt mute for the other person so that feature can stay personal"
--        -> mute has NO COLUMN HERE, on purpose. See the note above group_members.
--
-- Friends-only is kept from the existing design: you may only add someone you are already
-- accepted friends with, so no non-friend ever learns anything about anyone's week.
--
-- Every statement is guarded (IF NOT EXISTS / CREATE OR REPLACE). Nothing here drops anything.
-- Safe to run twice.
-- =============================================================================================

-- ---------------------------------------------------------------------------------------------
-- 1. The group itself
-- ---------------------------------------------------------------------------------------------
create table if not exists public.groups (
  id          uuid primary key default gen_random_uuid(),
  name        text not null default 'Group',
  created_by  uuid not null references auth.users(id) on delete cascade,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- ---------------------------------------------------------------------------------------------
-- 2. Who is in it
--
-- seen_at is what makes "You've been added to Test group" possible WITHOUT inventing a
-- notifications table: a member whose seen_at is null has never opened this group, so the app
-- can say so truthfully. The moment they open it, the app stamps seen_at and the badge is gone.
-- It is a real fact about a real row, not a flag we made up.
--
-- THERE IS DELIBERATELY NO `muted` COLUMN. Muting a member is the VIEWER asking "what opens up
-- if I don't wait for Sam" — a lens on the answer, not a fact about the group. It stays in that
-- one person's localStorage under professify_group_mutes. If a mute column is ever added here,
-- one person muting silently changes what everyone else sees, which is the exact thing Tate
-- asked to prevent.
-- ---------------------------------------------------------------------------------------------
create table if not exists public.group_members (
  group_id  uuid not null references public.groups(id) on delete cascade,
  user_id   uuid not null references auth.users(id)   on delete cascade,
  added_by  uuid          references auth.users(id)   on delete set null,
  added_at  timestamptz not null default now(),
  seen_at   timestamptz,
  primary key (group_id, user_id)
);

create index if not exists group_members_user_idx  on public.group_members(user_id);
create index if not exists group_members_group_idx on public.group_members(group_id);

-- ---------------------------------------------------------------------------------------------
-- 3. Two helpers, SECURITY DEFINER
--
-- is_group_member exists because a policy ON group_members that SELECTs group_members recurses
-- and Postgres will refuse it. A definer function reads the table without re-entering RLS,
-- which is the standard way out. It is STABLE and takes both ids explicitly so it can never be
-- coaxed into answering about a row the caller didn't name.
-- ---------------------------------------------------------------------------------------------
create or replace function public.is_group_member(g uuid, u uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (
    select 1 from public.group_members m
    where m.group_id = g and m.user_id = u
  );
$$;

-- Friendship, read the same way the app reads it: an accepted friend_requests row either way.
create or replace function public.are_friends(a uuid, b uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (
    select 1 from public.friend_requests r
    where r.status = 'accepted'
      and ((r.from_user = a and r.to_user = b)
        or (r.from_user = b and r.to_user = a))
  );
$$;

revoke all on function public.is_group_member(uuid, uuid) from public;
revoke all on function public.are_friends(uuid, uuid)     from public;
grant execute on function public.is_group_member(uuid, uuid) to authenticated;
grant execute on function public.are_friends(uuid, uuid)     to authenticated;

-- ---------------------------------------------------------------------------------------------
-- 4. RLS
-- ---------------------------------------------------------------------------------------------
alter table public.groups        enable row level security;
alter table public.group_members enable row level security;

-- groups ---------------------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='groups'
                 and policyname='groups_select_members') then
    create policy groups_select_members on public.groups
      for select to authenticated
      using (public.is_group_member(id, auth.uid()));
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='groups'
                 and policyname='groups_insert_own') then
    create policy groups_insert_own on public.groups
      for insert to authenticated
      with check (created_by = auth.uid());
  end if;
end $$;

-- Flat permissions: anyone in the group can rename it. No owner check, by instruction.
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='groups'
                 and policyname='groups_update_members') then
    create policy groups_update_members on public.groups
      for update to authenticated
      using      (public.is_group_member(id, auth.uid()))
      with check (public.is_group_member(id, auth.uid()));
  end if;
end $$;

-- Deleting the group deletes it FOR EVERYONE — that is what "all the changes that I could"
-- means, so the policy allows it. The client must ask before calling this; a mis-tap here is
-- not recoverable. Leaving a group is a group_members delete, which is the far commoner intent.
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='groups'
                 and policyname='groups_delete_members') then
    create policy groups_delete_members on public.groups
      for delete to authenticated
      using (public.is_group_member(id, auth.uid()));
  end if;
end $$;

-- group_members --------------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='group_members'
                 and policyname='gm_select_members') then
    create policy gm_select_members on public.group_members
      for select to authenticated
      using (public.is_group_member(group_id, auth.uid()));
  end if;
end $$;

-- Adding someone. Two ways in, and only two:
--   * you are already in this group AND the person you are adding is your accepted friend
--   * you just created this group and are adding YOURSELF (the bootstrap row — without this,
--     a brand-new group has no members, so is_group_member is false and nobody can ever join)
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='group_members'
                 and policyname='gm_insert_friends_only') then
    create policy gm_insert_friends_only on public.group_members
      for insert to authenticated
      with check (
        added_by = auth.uid()
        and (
          (user_id = auth.uid() and exists (
             select 1 from public.groups g where g.id = group_id and g.created_by = auth.uid()))
          or
          (public.is_group_member(group_id, auth.uid())
           and public.are_friends(auth.uid(), user_id))
        )
      );
  end if;
end $$;

-- Removing someone: any member may remove any member (flat permissions), and you may always
-- remove yourself, which is how leaving works.
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='group_members'
                 and policyname='gm_delete_members') then
    create policy gm_delete_members on public.group_members
      for delete to authenticated
      using (user_id = auth.uid() or public.is_group_member(group_id, auth.uid()));
  end if;
end $$;

-- The ONLY thing a member updates is their own seen_at — the "you've been added" acknowledgement.
-- Scoped to your own row so nobody can mark someone else's notice as read.
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='group_members'
                 and policyname='gm_update_own_seen') then
    create policy gm_update_own_seen on public.group_members
      for update to authenticated
      using      (user_id = auth.uid())
      with check (user_id = auth.uid());
  end if;
end $$;

-- ---------------------------------------------------------------------------------------------
-- 5. Keep groups.updated_at honest, so "renamed since you last looked" is answerable
-- ---------------------------------------------------------------------------------------------
create or replace function public.touch_group_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

do $$ begin
  if not exists (select 1 from pg_trigger where tgname = 'groups_touch_updated_at') then
    create trigger groups_touch_updated_at
      before update on public.groups
      for each row execute function public.touch_group_updated_at();
  end if;
end $$;

-- ---------------------------------------------------------------------------------------------
-- 6. Realtime, so a group appears on the other person's screen without a refresh.
--    The app already subscribes to postgres_changes on friend_requests; these join that pattern.
-- ---------------------------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_publication_tables
                 where pubname='supabase_realtime' and schemaname='public' and tablename='groups') then
    alter publication supabase_realtime add table public.groups;
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_publication_tables
                 where pubname='supabase_realtime' and schemaname='public' and tablename='group_members') then
    alter publication supabase_realtime add table public.group_members;
  end if;
end $$;

-- =============================================================================================
-- AFTER RUNNING THIS, check it landed:
--
--   select tablename, policyname, cmd from pg_policies
--   where schemaname='public' and tablename in ('groups','group_members')
--   order by tablename, policyname;
--
-- Expect 8 rows: 4 on groups, 4 on group_members.
-- =============================================================================================
