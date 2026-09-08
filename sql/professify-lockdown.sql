-- ================================================================================================
-- PROFESSIFY — RLS LOCKDOWN FOR THE TABLES NO MIGRATION EVER COVERED
-- 2026-09-05, written during the pre-launch security audit.
-- ================================================================================================
-- The audit read all twelve existing migrations and found that NINE of the nineteen tables the
-- browser talks to have no `enable row level security`, no policy, and no grant in ANY of them:
--
--     friend_requests   profiles   class_history   saved_classes   watch_sections
--     review_helpful    community_posts   course_prereqs   course_equiv
--
-- Their live state is therefore unknown. This file makes it known. It is written to be safe to run
-- whatever that state turns out to be: every policy is dropped by name and recreated, RLS is
-- enabled unconditionally, and privileges are revoked from PUBLIC before being granted narrowly.
--
-- WHY friend_requests IS FIRST AND WHY IT IS THE WHOLE BALL GAME
-- Five other migrations gate access on `friend_requests.status = 'accepted'` — my_sections,
-- reviews (share_with_friends), free_now, conversation_members, group_members. Two of them assert
-- in a comment that "RLS on friend_requests lets a student read only their OWN edges, which is
-- correct and must stay that way." No file in the set ever created that RLS. If it is not live,
-- then one INSERT with the public key —
--     {"from_user":"<victim>","to_user":"<me>","status":"accepted"}
-- — makes an attacker everyone's friend and unlocks all five of those tables at once. That is not
-- a theoretical chain; it is the documented design of every other policy in the project resting on
-- an assumption nobody wrote down in SQL.
--
-- RUN ORDER: run this AFTER professify-rls-hardening.sql and professify-messaging.sql, never
-- before, and never re-run rls-hardening.sql after messaging.sql (see section 8).
--
-- REVISED 2026-09-06. The first version named `pinned_friends` in a GRANT — a column that
-- professify-free-now.sql adds — so on a database where free-now had not been run it aborted with
-- 42703 and everything after that line, including the two revokes this file exists for, never ran.
-- Nothing here names a column now without first checking it is there. Two consequences worth
-- knowing: this file no longer depends on free-now having been run, and a failure anywhere in it
-- can no longer silently skip the security fix — it either applies or it says which table stopped
-- it. Safe to re-run; a partially-applied earlier attempt is fully overwritten.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 0. PREFLIGHT — say what is here before changing any of it
-- ------------------------------------------------------------------------------------------------
-- Read the NOTICE output of this block before reading anything else. Every table it reports as
-- missing is a section of this file that will skip itself, and every one it reports as present but
-- RLS-off is a table anyone with the publishable key can currently read and write.
do $$
declare t text; rls boolean; n int;
begin
  /* RAISE's % is a plain placeholder, not printf — a width like %-30s prints literally. rpad()
     is how you line a column up here. */
  raise notice '--- Professify lockdown preflight ---';
  foreach t in array array['friend_requests','profiles','class_history','saved_classes',
                           'watch_sections','review_helpful','community_posts',
                           'course_equiv','course_prereqs'] loop
    select c.relrowsecurity into rls
    from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
    where ns.nspname='public' and c.relname=t and c.relkind='r';
    if rls is null then
      raise notice '  %  MISSING — that section will skip itself', rpad(t,30);
    else
      select count(*) into n from pg_policies where schemaname='public' and tablename=t;
      raise notice '  %  rls=%  policies=%', rpad(t,30), rls, n;
    end if;
    rls := null;
  end loop;
  raise notice '--- end preflight ---';
end $$;


-- ------------------------------------------------------------------------------------------------
-- 1. friend_requests — the root of trust
-- ------------------------------------------------------------------------------------------------
alter table public.friend_requests enable row level security;

-- READ: only your own edges, in either direction. This is the property the other five migrations
-- already believe is true.
drop policy if exists "fr_read_own_edges" on public.friend_requests;
create policy "fr_read_own_edges"
  on public.friend_requests for select to authenticated
  using ( from_user = auth.uid() or to_user = auth.uid() );

-- CREATE: you may only ever send a PENDING request, as yourself, to someone else.
-- `status = 'pending'` in the WITH CHECK is the load-bearing clause: without it the insert path
-- is itself the forge-a-friendship attack described above.
drop policy if exists "fr_send_as_self" on public.friend_requests;
create policy "fr_send_as_self"
  on public.friend_requests for insert to authenticated
  with check ( from_user = auth.uid() and to_user <> auth.uid() and status = 'pending' );

-- ACCEPT: only the RECIPIENT, and only into 'accepted'.
--
-- A policy cannot compare NEW to OLD, so WITH CHECK alone cannot stop someone rewriting from_user
-- while keeping to_user = themselves — which is the same forgery by another route. The column
-- grant in section 7 is what actually prevents it: UPDATE is granted on the `status` column only,
-- so from_user and to_user are not writable at all. Both halves are required; neither is
-- sufficient alone.
drop policy if exists "fr_accept_as_recipient" on public.friend_requests;
create policy "fr_accept_as_recipient"
  on public.friend_requests for update to authenticated
  using  ( to_user = auth.uid() and status = 'pending' )
  with check ( to_user = auth.uid() and status in ('accepted','declined') );

-- REMOVE: either side may cancel, decline, or unfriend. Deleting the row is how all three are
-- implemented in the client (cancelRequest, declineRequest, removeFriend).
drop policy if exists "fr_delete_either_side" on public.friend_requests;
create policy "fr_delete_either_side"
  on public.friend_requests for delete to authenticated
  using ( from_user = auth.uid() or to_user = auth.uid() );


-- ------------------------------------------------------------------------------------------------
-- 2. profiles — rows are not the unit of privacy here, COLUMNS are
-- ------------------------------------------------------------------------------------------------
-- The app genuinely needs cross-user reads of profiles: a friend's name and photo, a conversation
-- participant's name, a username-availability check. RLS is row-level, so any policy that permits
-- those reads also hands over every column of that row — including edu_email and phone_hash.
--
-- So the row policy stays permissive and the COLUMN GRANT does the protecting. Postgres checks
-- column privileges independently of RLS: with SELECT revoked on edu_email, no policy, no view and
-- no `select=*` can produce it.
alter table public.profiles enable row level security;

drop policy if exists "profiles_read" on public.profiles;
create policy "profiles_read"
  on public.profiles for select to authenticated
  using ( true );

drop policy if exists "profiles_write_own" on public.profiles;
create policy "profiles_write_own"
  on public.profiles for update to authenticated
  using ( id = auth.uid() ) with check ( id = auth.uid() );

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
  on public.profiles for insert to authenticated
  with check ( id = auth.uid() );

-- No DELETE policy: accounts are removed through delete_my_account(), which is SECURITY DEFINER
-- and deletes the auth.users row. A student deleting their profile row directly would leave an
-- auth account with no profile, which every screen in the app then has to cope with.

-- Anonymous visitors read professor ratings and seat counts. They have no reason to read people.
revoke all on public.profiles from anon, public;

-- ------------------------------------------------------------------------------------------------
-- A TABLE-LEVEL GRANT BEATS A COLUMN-LEVEL REVOKE. This revoke is not tidiness, it is the whole
-- mechanism. Supabase grants SELECT on public tables to `authenticated` by default, and in
-- PostgreSQL a table-wide SELECT covers every column — so `revoke select (edu_email)` against a
-- role that still holds table-level SELECT changes nothing at all. The table grant has to go
-- FIRST; only then does the column list below become the complete set of what can be read.
-- ------------------------------------------------------------------------------------------------
revoke all on public.profiles from authenticated;

-- The public column list is built from what the table ACTUALLY HAS, not from a list written
-- somewhere else. The first version of this file named `pinned_friends` outright — a column added
-- by professify-free-now.sql — so running the two files in the other order aborted the script at
-- this line with 42703, and every statement below it (including the two revokes this file exists
-- for) never ran. A hardcoded column list turns a run-order preference into a silent security
-- failure. Anything in this list that does not exist is simply skipped and reported.
do $$
declare cols text; missing text;
begin
  select string_agg(quote_ident(c), ', ')
    into cols
  from unnest(array['id','display_name','username','avatar_url','major','class_standing',
                    'pinned_friends','instagram_handle']) as c
  where exists (select 1 from information_schema.columns
                where table_schema='public' and table_name='profiles' and column_name=c);

  select string_agg(c, ', ')
    into missing
  from unnest(array['id','display_name','username','avatar_url','major','class_standing',
                    'pinned_friends','instagram_handle']) as c
  where not exists (select 1 from information_schema.columns
                    where table_schema='public' and table_name='profiles' and column_name=c);

  if cols is null then
    raise exception 'public.profiles has none of the expected public columns — stop and check the schema';
  end if;
  execute format('grant select (%s) on public.profiles to authenticated', cols);
  raise notice 'profiles: SELECT granted on % ', cols;
  if missing is not null then
    raise notice 'profiles: not present, skipped: %  (run professify-free-now.sql if you want pinned_friends)', missing;
  end if;
end $$;

grant insert, update on public.profiles to authenticated;

-- THE POINT OF THIS FILE, IN ONE PLACE: after this block, no query by any signed-in student
-- returns another student's Cal Poly email address or the hash of their phone number. Not through
-- select=*, not through a crafted column list, not through a policy someone re-adds later.
-- Both are guarded on existence for the same reason as above: phone_hash appears in NONE of the
-- twelve migrations, so whether it is there at all is a live question, and a script that dies
-- asking is a script that protects nothing.
do $$
declare c text;
begin
  foreach c in array array['edu_email','phone_hash'] loop
    if exists (select 1 from information_schema.columns
               where table_schema='public' and table_name='profiles' and column_name=c) then
      execute format('revoke select (%I) on public.profiles from authenticated, anon', c);
      raise notice 'profiles: SELECT on %  REVOKED', c;
    else
      raise notice 'profiles: column %  does not exist — nothing to revoke', c;
    end if;
  end loop;
end $$;

-- Your own private fields still have to reach you — you need to see the address you verified with
-- and whether a phone is linked. One row, yours, by definition.
create or replace function public.my_private_profile()
returns table (edu_email text, has_phone boolean)
language sql security definer stable set search_path = public as $$
  select p.edu_email,
         (to_jsonb(p) ? 'phone_hash') and (to_jsonb(p)->>'phone_hash') is not null
  from public.profiles p
  where p.id = auth.uid() and auth.uid() is not null;
$$;
revoke all on function public.my_private_profile() from public;
revoke execute on function public.my_private_profile() from anon;
grant execute on function public.my_private_profile() to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 3. Owner-only personal data
-- ------------------------------------------------------------------------------------------------
-- class_history, saved_classes and watch_sections are a student's own record of what they have
-- taken, saved and are watching. saved_classes is additionally readable by accepted friends,
-- because the Quad is built on it — that is the ONE deliberate widening here, and it matches the
-- friends-can-read-sections policy that already exists on my_sections.
do $$
declare t text;
begin
  foreach t in array array['class_history','saved_classes','watch_sections','review_helpful'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists %I on public.%I', t||'_own', t);
    execute format('revoke all on public.%I from anon, public, authenticated', t);
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);
  end loop;
end $$;

do $$
declare t text;
begin
  foreach t in array array['class_history','saved_classes','watch_sections'] loop
    if not exists (select 1 from information_schema.columns
                   where table_schema='public' and table_name=t and column_name='user_id') then
      raise exception '%.user_id does not exist — this table does not have the shape this file assumes. Stop and inspect it.', t;
    end if;
  end loop;
end $$;

create policy "class_history_own" on public.class_history for all to authenticated
  using ( user_id = auth.uid() ) with check ( user_id = auth.uid() );

create policy "saved_classes_own" on public.saved_classes for all to authenticated
  using ( user_id = auth.uid() ) with check ( user_id = auth.uid() );

-- The Quad. Same friendship test as my_sections, same shape, deliberately duplicated rather than
-- factored into is_friend_of() so this file has no dependency on messaging.sql having been run.
drop policy if exists "saved_classes_friends_read" on public.saved_classes;
create policy "saved_classes_friends_read"
  on public.saved_classes for select to authenticated
  using ( exists (
    select 1 from public.friend_requests fr
    where fr.status = 'accepted'
      and ( (fr.from_user = auth.uid() and fr.to_user   = saved_classes.user_id)
         or (fr.to_user   = auth.uid() and fr.from_user = saved_classes.user_id) ) ) );

create policy "watch_sections_own" on public.watch_sections for all to authenticated
  using ( user_id = auth.uid() ) with check ( user_id = auth.uid() );

-- review_helpful: your vote is yours. The public helpful COUNT lives on reviews.helpful and needs
-- no voter identity to be correct, so nobody reads anyone else's votes.
-- review_helpful's owner column is `voter_id` in delete_my_account() and nowhere else in the
-- twelve migrations, so it is worth confirming rather than assuming — a policy written against a
-- column that does not exist fails the whole script, and a table left with no policy is the exact
-- problem this file is here to fix.
do $$
declare owner_col text;
begin
  select column_name into owner_col
  from information_schema.columns
  where table_schema='public' and table_name='review_helpful' and column_name in ('voter_id','user_id')
  order by case column_name when 'voter_id' then 1 else 2 end
  limit 1;

  if owner_col is null then
    raise notice 'review_helpful: no voter_id or user_id column — SKIPPED, check this table by hand';
  else
    execute format(
      'create policy "review_helpful_own" on public.review_helpful for all to authenticated
         using ( %I = auth.uid() ) with check ( %I = auth.uid() )', owner_col, owner_col);
    raise notice 'review_helpful: owner column is % ', owner_col;

    -- One vote per person per review. Without it, "helpful" is a number anyone can run up.
    if exists (select 1 from information_schema.columns
               where table_schema='public' and table_name='review_helpful' and column_name='review_id')
       and not exists (select 1 from pg_constraint where conname='review_helpful_one_per_review')
    then
      execute format('alter table public.review_helpful
                      add constraint review_helpful_one_per_review unique (review_id, %I)', owner_col);
      raise notice 'review_helpful: one-vote-per-review constraint added';
    end if;
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 4. community_posts — the Quad's shared schedules
-- ------------------------------------------------------------------------------------------------
-- The client reads this with NO filter and writes display_name into the row from the browser, so
-- without a policy anyone can post as anyone. Author is bound to auth.uid(); display_name is left
-- writable because it is a snapshot of a name the reader is entitled to see anyway.
do $$ begin
  if exists (select 1 from information_schema.tables
             where table_schema='public' and table_name='community_posts') then

    execute 'alter table public.community_posts enable row level security';

    execute 'drop policy if exists "posts_read_signed_in" on public.community_posts';
    execute 'create policy "posts_read_signed_in" on public.community_posts
               for select to authenticated using ( true )';

    execute 'drop policy if exists "posts_write_own" on public.community_posts';
    execute 'create policy "posts_write_own" on public.community_posts
               for insert to authenticated with check ( user_id = auth.uid() )';

    execute 'drop policy if exists "posts_update_own" on public.community_posts';
    execute 'create policy "posts_update_own" on public.community_posts
               for update to authenticated using ( user_id = auth.uid() ) with check ( user_id = auth.uid() )';

    execute 'drop policy if exists "posts_delete_own" on public.community_posts';
    execute 'create policy "posts_delete_own" on public.community_posts
               for delete to authenticated using ( user_id = auth.uid() )';

    execute 'revoke all on public.community_posts from anon, public, authenticated';
    execute 'grant select, insert, update, delete on public.community_posts to authenticated';

    -- delete_my_account() does not name this table. If it has no cascade, a deleted account leaves
    -- its posts behind with a dangling user_id — which is a deletion promise the app does not keep.
    if not exists (
      select 1 from pg_constraint c
      join pg_class t on t.oid = c.conrelid
      where t.relname = 'community_posts' and c.contype = 'f'
        and pg_get_constraintdef(c.oid) like '%auth.users%')
    then
      raise notice 'community_posts has no FK to auth.users — account deletion will NOT remove posts. Add: alter table public.community_posts add constraint community_posts_user_fk foreign key (user_id) references auth.users(id) on delete cascade;';
    end if;
  else
    raise notice 'community_posts does not exist on this database — skipped.';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 5. Catalog reference data — public read, nobody writes
-- ------------------------------------------------------------------------------------------------
-- course_equiv and course_prereqs are Cal Poly catalog facts. Anonymous read is correct and wanted
-- (they load before sign-in). What must not be true is that a student can edit the prerequisite
-- graph the whole app plans against.
do $$
declare t text;
begin
  foreach t in array array['course_equiv','course_prereqs','course_seats'] loop
    if exists (select 1 from information_schema.tables where table_schema='public' and table_name=t) then
      execute format('alter table public.%I enable row level security', t);
      execute format('drop policy if exists %I on public.%I', t||'_public_read', t);
      execute format('create policy %I on public.%I for select using ( true )', t||'_public_read', t);
      execute format('revoke all on public.%I from anon, authenticated, public', t);
      execute format('grant select on public.%I to anon, authenticated', t);
    end if;
  end loop;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 6. Grants the other migrations never stated
-- ------------------------------------------------------------------------------------------------
-- my_sections, free_now, friend_suggestion_dismissals, groups and group_members have correct
-- policies and NO grant or revoke anywhere, so whether `anon` holds table privileges on them is
-- decided by whatever the project's default privileges happen to be. Policies fail closed for anon
-- (auth.uid() is null), but a table privilege that should not exist is a finding on its own.
do $$
declare t text;
begin
  foreach t in array array['my_sections','free_now','friend_suggestion_dismissals','groups','group_members'] loop
    if exists (select 1 from information_schema.tables where table_schema='public' and table_name=t) then
      execute format('revoke all on public.%I from anon, public, authenticated', t);
      execute format('grant select, insert, update, delete on public.%I to authenticated', t);
    end if;
  end loop;
end $$;

-- reviews: no file ever issued a positive grant, so INSERT/UPDATE/DELETE rest on defaults.
revoke all on public.reviews from anon, public, authenticated;
grant select, insert, update, delete on public.reviews to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 7. Column-level UPDATE on friend_requests — the other half of section 1
-- ------------------------------------------------------------------------------------------------
-- Run AFTER the policies above. Granting UPDATE on `status` alone is what makes it impossible to
-- rewrite from_user/to_user, which a WITH CHECK clause cannot prevent on its own.
-- `authenticated` MUST be in this revoke. Supabase grants table-level UPDATE on public tables by
-- default, a table-level UPDATE covers every column, and a column grant cannot narrow one that is
-- already wider. Revoke from anon, PUBLIC *and* authenticated first, and only then hand back the
-- single column. Verified against Postgres 16: without the authenticated revoke,
--     update public.friend_requests set from_user = auth.uid();
-- is permitted at the privilege layer and only RLS stands in its way — and RLS alone cannot see
-- that from_user changed, because a policy compares against the NEW row, never the old one.
revoke all on public.friend_requests from anon, public, authenticated;
grant select, insert, delete on public.friend_requests to authenticated;
grant update (status) on public.friend_requests to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 7b. Sequences follow their tables
-- ------------------------------------------------------------------------------------------------
-- Revoking privileges on a table says nothing about the SEQUENCE behind its bigserial id, and
-- Supabase grants USAGE on public sequences to anon by default. Nothing can be inserted through
-- one — RLS still refuses the row — but leaving anon holding nextval on every id sequence is a
-- privilege nobody decided to give.
do $$
declare sq text;
begin
  for sq in
    select quote_ident(sequence_schema)||'.'||quote_ident(sequence_name)
    from information_schema.sequences where sequence_schema='public'
  loop
    execute format('revoke all on sequence %s from anon', sq);
    execute format('grant usage, select on sequence %s to authenticated', sq);
  end loop;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 8. The re-run hazard, defused
-- ------------------------------------------------------------------------------------------------
-- professify-rls-hardening.sql contains `create policy "reviews are publicly readable" ... using
-- (true)` — the exact policy professify-messaging.sql exists to remove. Both files call themselves
-- safe to re-run, and running them out of order silently re-opens every column of `reviews`,
-- user_id included, to every signed-in student. It also replaces the rate-limited INSERT policy
-- with the unlimited one, removing the five-reviews-an-hour cap.
--
-- This drop is idempotent and belongs at the end of every future run.
drop policy if exists "reviews are publicly readable" on public.reviews;

do $$ begin
  if exists (select 1 from pg_policies
             where schemaname='public' and tablename='reviews' and policyname='reviews are publicly readable')
  then raise exception 'reviews still has a public-read policy — user_id is exposed. Stop and investigate.';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- VERIFY — as a signed-in student, then as a SECOND student
-- ------------------------------------------------------------------------------------------------
--  A. select edu_email from public.profiles limit 1;
--       expect: ERROR permission denied for column edu_email
--  B. select * from public.profiles limit 1;
--       expect: the same error — `*` expands to columns you cannot read
--  C. select id, display_name, avatar_url from public.profiles limit 5;
--       expect: rows. This is the read the app needs and the only one it gets.
--  D. select * from public.my_private_profile();
--       expect: exactly one row, your own address.
--  E. insert into public.friend_requests (from_user, to_user, status)
--       values ('<any other user id>', auth.uid(), 'accepted');
--       expect: new row violates row-level security policy
--  F. update public.friend_requests set from_user = auth.uid() where id = '<a request to you>';
--       expect: ERROR permission denied for column from_user
--  G. select * from public.class_history where user_id = '<the other student>';
--       expect: 0 rows
--  H. select count(*) from public.reviews;
--       expect: only your own. Then: select * from public.reviews_public limit 1; expect rows
--       WITHOUT a user_id column.
