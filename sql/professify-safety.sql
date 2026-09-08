-- ================================================================================================
-- REPORT, BLOCK, MODERATE — 2026-09-06
-- ================================================================================================
-- The launch audit found these absent entirely: `reportUser`, `blockUser`, `is_blocked` and
-- `moderator` return zero hits across the whole codebase. Professify has direct messaging, public
-- reviews of named real people, and no way to report any of it. That is a launch blocker on its
-- own and an automatic App Store rejection.
--
-- THE RULE THIS FILE IS BUILT ON: a block that lives in the browser is not a block. If the only
-- thing stopping a harasser is client-side filtering, they open the console and carry on — and the
-- person who blocked them believes they are safe. So blocking is enforced in the INSERT policies
-- for friend_requests and messages, where the attacker's own request is refused by Postgres before
-- the app is involved. The client hiding blocked people is a courtesy on top, never the control.
--
-- Run AFTER professify-lockdown.sql. Safe to re-run.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 1. Who moderates
-- ------------------------------------------------------------------------------------------------
-- A table, not a column on profiles, and deliberately unreachable from the browser: no policy is
-- created for it and every privilege is revoked, so the ONLY way to become a moderator is a human
-- with database access typing an insert. A `profiles.is_moderator` boolean would sit on a row the
-- owner can already update, which is a self-promotion button waiting to be found.
create table if not exists public.moderators (
  user_id  uuid primary key references auth.users(id) on delete cascade,
  added_at timestamptz not null default now(),
  note     text
);
alter table public.moderators enable row level security;
revoke all on public.moderators from anon, public, authenticated;
-- No policies at all. RLS with zero policies denies everything to everyone except the table owner
-- and SECURITY DEFINER functions, which is exactly the reachability this table should have.

create or replace function public.is_moderator()
returns boolean language sql security definer stable set search_path = public as $$
  select auth.uid() is not null
     and exists (select 1 from public.moderators m where m.user_id = auth.uid());
$$;
revoke all on function public.is_moderator() from public;
revoke execute on function public.is_moderator() from anon;
grant execute on function public.is_moderator() to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 2. Blocks
-- ------------------------------------------------------------------------------------------------
create table if not exists public.blocks (
  blocker    uuid not null references auth.users(id) on delete cascade,
  blocked    uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (blocker, blocked)
);
do $$ begin
  if not exists (select 1 from pg_constraint where conname='blocks_not_self') then
    alter table public.blocks add constraint blocks_not_self check (blocker <> blocked);
  end if;
end $$;
alter table public.blocks enable row level security;

-- You can see and manage the blocks YOU made. You cannot discover that somebody blocked you —
-- that is the whole point of a block, and a readable list of who blocked whom is a harassment
-- tool in its own right.
drop policy if exists "blocks_own" on public.blocks;
create policy "blocks_own" on public.blocks for all to authenticated
  using ( blocker = auth.uid() ) with check ( blocker = auth.uid() );

revoke all on public.blocks from anon, public, authenticated;
grant select, insert, delete on public.blocks to authenticated;
create index if not exists blocks_blocked_idx on public.blocks(blocked);

-- The question every enforcement policy asks. SECURITY DEFINER because it must see blocks in BOTH
-- directions, and the RLS above deliberately hides the ones pointing at you.
create or replace function public.blocked_between(a uuid, b uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from public.blocks
    where (blocker = a and blocked = b) or (blocker = b and blocked = a)
  );
$$;
revoke all on function public.blocked_between(uuid,uuid) from public;
revoke execute on function public.blocked_between(uuid,uuid) from anon;
grant execute on function public.blocked_between(uuid,uuid) to authenticated;

-- Blocking someone you are friends with has to END the friendship, or the block stops messages
-- while leaving them your whole schedule. One call, one transaction, so the two can never drift.
create or replace function public.block_user(p_target uuid)
returns void language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'not signed in'; end if;
  if p_target is null or p_target = me then raise exception 'cannot block yourself'; end if;

  insert into public.blocks (blocker, blocked) values (me, p_target)
    on conflict (blocker, blocked) do nothing;

  -- Every edge between you, in either direction and at any stage.
  delete from public.friend_requests
   where (from_user = me and to_user = p_target)
      or (to_user = me and from_user = p_target);

  -- And stop suggesting them back to you tomorrow.
  begin
    insert into public.friend_suggestion_dismissals (user_id, dismissed_id)
    values (me, p_target) on conflict do nothing;
  exception when others then null;  -- table shape varies; a block must not fail over a nicety
  end;
end $$;
revoke all on function public.block_user(uuid) from public;
revoke execute on function public.block_user(uuid) from anon;
grant execute on function public.block_user(uuid) to authenticated;

create or replace function public.unblock_user(p_target uuid)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  delete from public.blocks where blocker = auth.uid() and blocked = p_target;
end $$;
revoke all on function public.unblock_user(uuid) from public;
revoke execute on function public.unblock_user(uuid) from anon;
grant execute on function public.unblock_user(uuid) to authenticated;

-- The list you can act on, with names, so Settings can show more than a column of UUIDs.
create or replace function public.my_blocks()
returns table (id uuid, display_name text, username text, avatar_url text, created_at timestamptz)
language sql security definer stable set search_path = public as $$
  select p.id, coalesce(p.display_name,'Someone'), p.username, p.avatar_url, b.created_at
  from public.blocks b join public.profiles p on p.id = b.blocked
  where b.blocker = auth.uid() and auth.uid() is not null
  order by b.created_at desc;
$$;
revoke all on function public.my_blocks() from public;
revoke execute on function public.my_blocks() from anon;
grant execute on function public.my_blocks() to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 3. ENFORCEMENT — the part that makes a block real
-- ------------------------------------------------------------------------------------------------
-- friend_requests: recreated from professify-lockdown.sql §1 with one clause added. Recreating is
-- the only option — PostgreSQL has no "alter policy ... add condition", and leaving the old policy
-- beside a new one would OR them and enforce nothing.
drop policy if exists "fr_send_as_self" on public.friend_requests;
create policy "fr_send_as_self"
  on public.friend_requests for insert to authenticated
  with check (
    from_user = auth.uid()
    and to_user <> auth.uid()
    and status = 'pending'
    and not public.blocked_between(auth.uid(), to_user)
  );

-- messages: same treatment. A blocked person cannot write into a thread you share, even one that
-- existed before the block.
drop policy if exists "members write to the thread" on public.messages;
create policy "members write to the thread"
  on public.messages for insert to authenticated
  with check (
    auth.uid() = sender
    and public.is_conv_member(conversation_id, auth.uid())
    and not exists (
      select 1
      from public.conversation_members cm
      where cm.conversation_id = messages.conversation_id
        and cm.user_id <> auth.uid()
        and public.blocked_between(auth.uid(), cm.user_id)
    )
  );

-- And they cannot pull you into a NEW thread either.
drop policy if exists "the creator adds friends" on public.conversation_members;
create policy "the creator adds friends"
  on public.conversation_members for insert to authenticated
  with check (
    exists (select 1 from public.conversations c
             where c.id = conversation_id and c.created_by = auth.uid())
    and ( user_id = auth.uid() or public.is_friend_of(auth.uid(), user_id) )
    and not public.blocked_between(auth.uid(), user_id)
  );


-- ------------------------------------------------------------------------------------------------
-- 4. Reports
-- ------------------------------------------------------------------------------------------------
create table if not exists public.reports (
  id           uuid primary key default gen_random_uuid(),
  reporter     uuid not null references auth.users(id) on delete set null,
  kind         text not null,          -- review | post | message | user | suggestion
  target_id    text,                   -- the row being reported, as text: ids differ per table
  target_user  uuid references auth.users(id) on delete set null,
  reason       text not null,
  note         text,
  status       text not null default 'open',   -- open | actioned | dismissed
  action_taken text,
  resolved_by  uuid references auth.users(id) on delete set null,
  resolved_at  timestamptz,
  created_at   timestamptz not null default now()
);
do $$ begin
  if not exists (select 1 from pg_constraint where conname='reports_kind_ck') then
    alter table public.reports add constraint reports_kind_ck
      check (kind in ('review','post','message','user','suggestion'));
  end if;
  if not exists (select 1 from pg_constraint where conname='reports_status_ck') then
    alter table public.reports add constraint reports_status_ck
      check (status in ('open','actioned','dismissed'));
  end if;
  if not exists (select 1 from pg_constraint where conname='reports_reason_ck') then
    alter table public.reports add constraint reports_reason_ck
      check (reason in ('harassment','hate','threat','private_info','impersonation',
                        'spam','sexual','not_about_teaching','other'));
  end if;
end $$;
alter table public.reports enable row level security;

-- A reporter sees their own reports and nobody else's; a moderator sees all. Nobody edits a
-- report after filing it — the record of what was said at the time is the point.
drop policy if exists "reports_read" on public.reports;
create policy "reports_read" on public.reports for select to authenticated
  using ( reporter = auth.uid() or public.is_moderator() );

drop policy if exists "reports_file_own" on public.reports;
create policy "reports_file_own" on public.reports for insert to authenticated
  with check ( reporter = auth.uid() and status = 'open' and resolved_by is null );

drop policy if exists "reports_moderate" on public.reports;
create policy "reports_moderate" on public.reports for update to authenticated
  using ( public.is_moderator() ) with check ( public.is_moderator() );

revoke all on public.reports from anon, public, authenticated;
grant select, insert on public.reports to authenticated;
grant update (status, action_taken, resolved_by, resolved_at) on public.reports to authenticated;

create index if not exists reports_status_idx on public.reports(status, created_at desc);
create index if not exists reports_target_idx on public.reports(target_user);

-- One report per person per thing. Without it, "12 reports" can be one angry student pressing a
-- button twelve times, and a moderation queue that cannot tell those apart is worse than none.
create unique index if not exists reports_one_per_target_idx
  on public.reports (reporter, kind, coalesce(target_id, ''));

-- Rate limit, in the policy, because the browser's copy of it is advisory at best.
drop policy if exists "reports_file_own" on public.reports;
create policy "reports_file_own" on public.reports for insert to authenticated
  with check (
    reporter = auth.uid() and status = 'open' and resolved_by is null
    and ( select count(*) from public.reports r
          where r.reporter = auth.uid()
            and r.created_at > now() - interval '1 hour' ) < 10
  );


-- ------------------------------------------------------------------------------------------------
-- 5. The moderator queue, as one call
-- ------------------------------------------------------------------------------------------------
-- Returns the report plus who filed it, who it is about, and how many prior reports that person
-- has — the four things a moderator needs before deciding, without four round trips or exposing
-- profiles to a non-moderator.
create or replace function public.mod_queue(p_status text default 'open', p_limit int default 50)
returns table (
  id uuid, kind text, target_id text, reason text, note text, status text,
  created_at timestamptz,
  reporter_name text,
  target_user uuid, target_name text, target_username text,
  prior_reports int
)
language sql security definer stable set search_path = public as $$
  select r.id, r.kind, r.target_id, r.reason, r.note, r.status, r.created_at,
         coalesce(rp.display_name,'Someone') as reporter_name,
         r.target_user,
         coalesce(tp.display_name,'—') as target_name,
         tp.username as target_username,
         (select count(*)::int from public.reports r2
           where r2.target_user = r.target_user and r2.id <> r.id) as prior_reports
  from public.reports r
  left join public.profiles rp on rp.id = r.reporter
  left join public.profiles tp on tp.id = r.target_user
  where public.is_moderator()
    and (p_status = 'all' or r.status = p_status)
  order by r.created_at desc
  limit greatest(least(coalesce(p_limit,50), 200), 1);
$$;
revoke all on function public.mod_queue(text,int) from public;
revoke execute on function public.mod_queue(text,int) from anon;
grant execute on function public.mod_queue(text,int) to authenticated;

-- Acting on a report. The moderator's own id is taken from auth.uid(), never from the client, so
-- an action can never be attributed to someone who did not take it.
create or replace function public.mod_resolve(p_report uuid, p_status text, p_action text default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_moderator() then raise exception 'not a moderator'; end if;
  if p_status not in ('actioned','dismissed','open') then raise exception 'bad status'; end if;
  update public.reports
     set status = p_status,
         action_taken = p_action,
         resolved_by = auth.uid(),
         resolved_at = case when p_status = 'open' then null else now() end
   where id = p_report;
end $$;
revoke all on function public.mod_resolve(uuid,text,text) from public;
revoke execute on function public.mod_resolve(uuid,text,text) from anon;
grant execute on function public.mod_resolve(uuid,text,text) to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 6. Removing content, and suspending people
-- ------------------------------------------------------------------------------------------------
-- A moderator needs to take a review down without being handed DELETE on the whole table. One
-- function, one row, and it records who did it.
alter table public.reviews add column if not exists removed_at timestamptz;
alter table public.reviews add column if not exists removed_by uuid references auth.users(id) on delete set null;

create or replace function public.mod_remove_review(p_review uuid, p_reason text default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_moderator() then raise exception 'not a moderator'; end if;
  update public.reviews set removed_at = now(), removed_by = auth.uid() where id = p_review;
  update public.reports set status='actioned', action_taken=coalesce(p_reason,'review removed'),
         resolved_by=auth.uid(), resolved_at=now()
   where kind='review' and target_id = p_review::text and status='open';
end $$;
revoke all on function public.mod_remove_review(uuid,text) from public;
revoke execute on function public.mod_remove_review(uuid,text) from anon;
grant execute on function public.mod_remove_review(uuid,text) to authenticated;

-- Suspension. A suspended account can still sign in and read — it simply cannot write anything
-- anyone else will see, which is the enforceable half and the half that matters.
create table if not exists public.suspensions (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  until      timestamptz,
  reason     text,
  set_by     uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);
alter table public.suspensions enable row level security;
revoke all on public.suspensions from anon, public, authenticated;
drop policy if exists "see your own suspension" on public.suspensions;
create policy "see your own suspension" on public.suspensions for select to authenticated
  using ( user_id = auth.uid() or public.is_moderator() );
grant select on public.suspensions to authenticated;

create or replace function public.is_suspended(u uuid default null)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from public.suspensions s
    where s.user_id = coalesce(u, auth.uid())
      and (s.until is null or s.until > now())
  );
$$;
revoke all on function public.is_suspended(uuid) from public;
revoke execute on function public.is_suspended(uuid) from anon;
grant execute on function public.is_suspended(uuid) to authenticated;

create or replace function public.mod_suspend(p_user uuid, p_days int default 7, p_reason text default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_moderator() then raise exception 'not a moderator'; end if;
  insert into public.suspensions (user_id, until, reason, set_by)
  values (p_user, case when p_days is null then null else now() + (p_days || ' days')::interval end,
          p_reason, auth.uid())
  on conflict (user_id) do update
    set until = excluded.until, reason = excluded.reason, set_by = excluded.set_by, created_at = now();
end $$;
revoke all on function public.mod_suspend(uuid,int,text) from public;
revoke execute on function public.mod_suspend(uuid,int,text) from anon;
grant execute on function public.mod_suspend(uuid,int,text) to authenticated;

create or replace function public.mod_unsuspend(p_user uuid)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_moderator() then raise exception 'not a moderator'; end if;
  delete from public.suspensions where user_id = p_user;
end $$;
revoke all on function public.mod_unsuspend(uuid) from public;
revoke execute on function public.mod_unsuspend(uuid) from anon;
grant execute on function public.mod_unsuspend(uuid) to authenticated;

-- A suspension that only greys out a button is not a suspension. These policies are where it
-- actually holds — and a policy on a table whose RLS is OFF is not enforcement either, it is a row
-- in pg_policies that never runs. That exact shape has bitten this database twice (my_sections in
-- August, reviews_public_read yesterday), so RLS is asserted here rather than assumed from another
-- migration having been run first.
alter table public.reviews enable row level security;
do $$ begin
  if exists (select 1 from information_schema.tables
             where table_schema='public' and table_name='community_posts') then
    execute 'alter table public.community_posts enable row level security';
  end if;
end $$;
drop policy if exists "authors write their own reviews" on public.reviews;
create policy "authors write their own reviews"
  on public.reviews for insert to authenticated
  with check (
    auth.uid() = user_id
    and not public.is_suspended(auth.uid())
    and ( select count(*) from public.reviews r
          where r.user_id = auth.uid()
            and r.created_at > now() - interval '1 hour' ) < 5
  );

do $$ begin
  if exists (select 1 from information_schema.tables
             where table_schema='public' and table_name='community_posts') then
    execute 'drop policy if exists "posts_write_own" on public.community_posts';
    execute 'create policy "posts_write_own" on public.community_posts
               for insert to authenticated
               with check ( user_id = auth.uid() and not public.is_suspended(auth.uid()) )';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 7. Refuse to finish quietly if any of this is unenforced
-- ------------------------------------------------------------------------------------------------
-- Everything above is policies, and a policy on a table with RLS off is decoration. This block
-- raises rather than letting the file report success over a suspension nobody is subject to and a
-- block nothing checks.
do $$
declare t text; bad text := '';
begin
  foreach t in array array['reviews','messages','friend_requests','conversation_members',
                           'blocks','reports','moderators','suspensions'] loop
    if exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
               where n.nspname='public' and c.relname=t and c.relkind='r' and not c.relrowsecurity)
    then bad := bad || t || ' ';
    end if;
  end loop;
  if bad <> '' then
    raise exception 'RLS is OFF on: % — the policies in this file are not being enforced. Run professify-lockdown.sql, then this file again.', bad;
  end if;
  raise notice 'safety: RLS confirmed on every table this file writes a policy for';
end $$;


-- ------------------------------------------------------------------------------------------------
-- MAKE YOURSELF A MODERATOR — run this once, as yourself, or the queue has nobody to read it
-- ------------------------------------------------------------------------------------------------
--   insert into public.moderators (user_id, note)
--   select id, 'founder' from auth.users where email = 'YOUR@calpoly.edu'
--   on conflict do nothing;
--
-- VERIFY
--   select public.is_moderator();                 -- true for you, false for a test account
--   select * from public.mod_queue('open');       -- rows for you, ZERO rows for a test account
--   -- as a test account, after blocking someone:
--   insert into public.friend_requests(from_user,to_user,status)
--     values (auth.uid(), '<person who blocked you>', 'pending');
--     -- expect: new row violates row-level security policy
