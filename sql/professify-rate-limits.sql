-- ================================================================================================
-- SERVER-SIDE RATE LIMITS — 2026-09-06
-- ================================================================================================
-- The audit found reviews already capped in the INSERT policy (5/hour, from review-integrity.sql)
-- and nothing else limited anywhere. The client's own comment is honest about what its localStorage
-- cap is worth: it "is here to give an honest answer before someone writes 200 words, not to be the
-- thing standing between a spammer and the table."
--
-- These are the four writes an abusive account actually uses: friend requests to spray the whole
-- campus, DMs to harass, posts to spam the Quad, and professor suggestions to junk the catalog.
--
-- THIS FILE IS NOW THE DEFINITION OF THOSE POLICIES. PostgreSQL has no "alter policy … add
-- condition", so a rate limit can only be added by recreating the whole policy — which means each
-- recreation must carry every clause the last one had. professify-safety.sql added the block
-- checks; they are reproduced here in full. If a third thing ever needs adding, add it HERE and
-- run this file, rather than writing a fourth file that recreates a policy from a copy that has
-- since gone stale. That is exactly how the `using (true)` policy on reviews came back.
--
-- Run AFTER professify-lockdown.sql and professify-safety.sql. Safe to re-run.
-- ================================================================================================

-- The limits, in one place, with the reasoning. These are per-account and deliberately generous:
-- the point is to stop a script, not to interrupt a chatty freshman in week one.
--
--   friend requests   40 / day     Cal Poly's biggest lecture is ~400. Forty a day is more than
--                                  anyone adds honestly and far below "spray the campus".
--   direct messages  200 / hour    Three a minute, sustained, for an hour. A real conversation
--                                  never comes close; a bot does immediately.
--   posts             10 / day     You share a schedule when it changes. Ten is a whole term.
--   suggestions       20 / day     Adding professors the catalog is missing is a real thing to do
--                                  in one sitting; twenty of them is not.

-- ------------------------------------------------------------------------------------------------
-- 1. friend_requests — 40 a day
-- ------------------------------------------------------------------------------------------------
-- Full policy: self-only + pending-only (lockdown §1), not blocked (safety §3), now rate-limited.
do $$ begin
  if not exists (select 1 from information_schema.columns
                 where table_schema='public' and table_name='friend_requests' and column_name='created_at')
  then
    alter table public.friend_requests add column created_at timestamptz not null default now();
    raise notice 'friend_requests: added created_at — a rate limit needs something to count against';
  end if;
end $$;

drop policy if exists "fr_send_as_self" on public.friend_requests;
create policy "fr_send_as_self"
  on public.friend_requests for insert to authenticated
  with check (
    from_user = auth.uid()
    and to_user <> auth.uid()
    and status = 'pending'
    and not public.blocked_between(auth.uid(), to_user)
    and not public.is_suspended(auth.uid())
    and ( select count(*) from public.friend_requests fr
          where fr.from_user = auth.uid()
            and fr.created_at > now() - interval '1 day' ) < 40
  );

-- ------------------------------------------------------------------------------------------------
-- 2. messages — 200 an hour
-- ------------------------------------------------------------------------------------------------
-- Full policy: sender is you + you are in the thread (messaging.sql), nobody in it has blocked you
-- (safety §3), now rate-limited and suspension-aware.
drop policy if exists "members write to the thread" on public.messages;
create policy "members write to the thread"
  on public.messages for insert to authenticated
  with check (
    auth.uid() = sender
    and public.is_conv_member(conversation_id, auth.uid())
    and not public.is_suspended(auth.uid())
    and not exists (
      select 1 from public.conversation_members cm
      where cm.conversation_id = messages.conversation_id
        and cm.user_id <> auth.uid()
        and public.blocked_between(auth.uid(), cm.user_id)
    )
    and ( select count(*) from public.messages m
          where m.sender = auth.uid()
            and m.created_at > now() - interval '1 hour' ) < 200
  );

-- ------------------------------------------------------------------------------------------------
-- 3. community_posts — 10 a day
-- ------------------------------------------------------------------------------------------------
do $$ begin
  if exists (select 1 from information_schema.tables
             where table_schema='public' and table_name='community_posts') then

    if not exists (select 1 from information_schema.columns
                   where table_schema='public' and table_name='community_posts' and column_name='created_at')
    then execute 'alter table public.community_posts add column created_at timestamptz not null default now()';
    end if;

    execute 'drop policy if exists "posts_write_own" on public.community_posts';
    execute 'create policy "posts_write_own" on public.community_posts
               for insert to authenticated
               with check (
                 user_id = auth.uid()
                 and not public.is_suspended(auth.uid())
                 and ( select count(*) from public.community_posts cp
                       where cp.user_id = auth.uid()
                         and cp.created_at > now() - interval ''1 day'' ) < 10
               )';
    raise notice 'community_posts: 10/day';
  else
    raise notice 'community_posts does not exist — skipped';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 4. professor_suggestions — 20 a day
-- ------------------------------------------------------------------------------------------------
-- messaging.sql gives this table one FOR ALL policy. Splitting INSERT out is what lets the limit
-- apply to writes without also rate-limiting a student reading their own suggestions back.
do $$ begin
  if exists (select 1 from information_schema.tables
             where table_schema='public' and table_name='professor_suggestions') then

    if not exists (select 1 from information_schema.columns
                   where table_schema='public' and table_name='professor_suggestions' and column_name='created_at')
    then execute 'alter table public.professor_suggestions add column created_at timestamptz not null default now()';
    end if;

    execute 'drop policy if exists "ps_insert_rate" on public.professor_suggestions';
    execute 'create policy "ps_insert_rate" on public.professor_suggestions
               for insert to authenticated
               with check (
                 user_id = auth.uid()
                 and not public.is_suspended(auth.uid())
                 and ( select count(*) from public.professor_suggestions s
                       where s.user_id = auth.uid()
                         and s.created_at > now() - interval ''1 day'' ) < 20
               )';

    -- The existing FOR ALL policy covers INSERT too, and permissive policies OR together — so
    -- leaving it would let a spammer take the unlimited branch and the new one would enforce
    -- nothing. Replace it with three commands that exclude INSERT.
    execute 'drop policy if exists "you manage your own suggestions" on public.professor_suggestions';
    execute 'create policy "ps_read_own" on public.professor_suggestions
               for select to authenticated using ( user_id = auth.uid() )';
    execute 'drop policy if exists "ps_update_own" on public.professor_suggestions';
    execute 'create policy "ps_update_own" on public.professor_suggestions
               for update to authenticated using ( user_id = auth.uid() ) with check ( user_id = auth.uid() )';
    execute 'drop policy if exists "ps_delete_own" on public.professor_suggestions';
    execute 'create policy "ps_delete_own" on public.professor_suggestions
               for delete to authenticated using ( user_id = auth.uid() )';
    raise notice 'professor_suggestions: 20/day, and the FOR ALL policy no longer bypasses it';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 4b. reviews — TWO insert policies were racing, and the weaker one was winning
-- ------------------------------------------------------------------------------------------------
-- Found live on 2026-09-06. public.reviews had two PERMISSIVE INSERT policies:
--
--   authors write their own reviews   auth.uid() = user_id
--                                     AND NOT is_suspended(auth.uid())
--                                     AND (5 in the last hour)
--   reviews_insert_own_edu            auth.uid() = user_id
--                                     AND lower(auth.jwt() ->> 'email') LIKE '%.edu'
--
-- Permissive policies OR together, so every insert that satisfied the second one skipped the
-- first entirely: the five-an-hour cap was not in force, and a SUSPENDED student could still post
-- reviews. Both protections existed and neither applied. This is the same failure as
-- reviews_public_read yesterday, and it will keep happening for as long as policies are added
-- beside each other instead of replacing each other.
--
-- The .edu clause is worth keeping — it is the only place the "verified student" claim is enforced
-- anywhere but the browser, and the audit listed that as an open item. So the two are MERGED into
-- one policy carrying all four conditions, and the loose one is dropped.
--
-- NOTE ON '%.edu': that matches any .edu, not calpoly.edu. Professify is one campus today, so
-- tightening it to '%@calpoly.edu' would be more honest — but it would also lock out anyone who
-- signed up with a different .edu, so it is left as-is deliberately. Change it when you decide,
-- not by accident.
do $$
declare has_edu boolean;
begin
  select exists (select 1 from pg_policies
                 where schemaname='public' and tablename='reviews'
                   and policyname='reviews_insert_own_edu') into has_edu;

  execute 'drop policy if exists "authors write their own reviews" on public.reviews';
  execute 'drop policy if exists "reviews_insert_own_edu" on public.reviews';

  execute format($f$
    create policy "authors write their own reviews"
      on public.reviews for insert to authenticated
      with check (
        auth.uid() = user_id
        %s
        and not public.is_suspended(auth.uid())
        and ( select count(*) from public.reviews r
              where r.user_id = auth.uid()
                and r.created_at > now() - interval '1 hour' ) < 5
      )$f$,
    case when has_edu
      then $e$and lower(coalesce(auth.jwt() ->> 'email', '')) like '%.edu'$e$
      else '' end);

  if has_edu then
    raise notice 'reviews: merged the .edu check INTO the capped policy and dropped the loose one';
  else
    raise notice 'reviews: single capped INSERT policy (no .edu clause was present to keep)';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 5. The indexes these counts need
-- ------------------------------------------------------------------------------------------------
-- Every one of these subselects runs on every insert. Without an index on (author, created_at) they
-- are sequential scans that get slower as the app succeeds — a rate limit that becomes a
-- performance problem is a rate limit somebody will remove.
create index if not exists fr_from_created_idx  on public.friend_requests(from_user, created_at desc);
create index if not exists msg_sender_created_idx on public.messages(sender, created_at desc);
do $$ begin
  if exists (select 1 from information_schema.tables where table_schema='public' and table_name='community_posts')
  then execute 'create index if not exists cp_user_created_idx on public.community_posts(user_id, created_at desc)'; end if;
  if exists (select 1 from information_schema.tables where table_schema='public' and table_name='professor_suggestions')
  then execute 'create index if not exists ps_user_created_idx on public.professor_suggestions(user_id, created_at desc)'; end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 6. Nothing here is enforced if a wider policy sits beside it
-- ------------------------------------------------------------------------------------------------
-- Permissive policies OR together, so one leftover INSERT policy without a limit defeats all four.
do $$
declare r record; bad text := '';
begin
  for r in
    select tablename, policyname, coalesce(with_check,'') wc
    from pg_policies
    where schemaname='public'
      and tablename in ('friend_requests','messages','community_posts','professor_suggestions')
      and cmd in ('INSERT','ALL') and permissive='PERMISSIVE'
  loop
    if r.wc not like '%interval%' then bad := bad || r.tablename || '.' || r.policyname || '  '; end if;
  end loop;
  if bad <> '' then
    raise warning 'These INSERT policies have NO rate limit and OR with the ones above, defeating them: %', bad;
  else
    raise notice 'rate limits: every INSERT path on these four tables is capped';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- VERIFY, as a signed-in student
-- ------------------------------------------------------------------------------------------------
--   do $$ begin
--     for i in 1..45 loop
--       insert into public.friend_requests(from_user,to_user,status)
--       values (auth.uid(), gen_random_uuid(), 'pending');
--     end loop;
--   end $$;
--   -- expect: it fails on the 41st with "new row violates row-level security policy"
