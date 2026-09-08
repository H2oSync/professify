-- ================================================================================================
-- ACCOUNT DELETION — COVER THE TABLES THAT WERE ADDED AFTER IT WAS WRITTEN — 2026-09-06
-- ================================================================================================
-- delete_my_account() is good work: it de-authors reviews FIRST so a failure rolls back with the
-- account intact, it guards every table with to_regclass so a missing one cannot abort the
-- deletion, and it deletes auth.users last. Nothing about that changes here.
--
-- What changed is the schema. Tables have been added since it was written, and it names none of
-- them: community_posts, class_waivers, free_now, professor_suggestions, moderators, suspensions,
-- blocks, reports, and the three messaging tables. Some cascade from auth.users and would be
-- removed anyway; relying on that is the problem, not the outcome — a cascade is invisible from
-- inside this function, so the next person reading it cannot tell which tables are handled and
-- which were forgotten. Every table is now named, whether it cascades or not.
--
-- WHAT THE APP PROMISES, which is what this has to deliver:
--   "Delete your account any time from Settings and your data goes with it — except your reviews,
--    which stay up permanently unlinked from you, because other students are relying on them."
-- Everything except reviews goes. That includes messages, which the original did not mention.
--
-- Run AFTER professify-safety.sql. Safe to re-run.
-- ================================================================================================

create or replace function public.delete_my_account()
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  me   uuid := auth.uid();
  t    record;
  col  text;
begin
  if me is null then
    raise exception 'not signed in';
  end if;

  -- Reviews are kept, de-authored. FIRST, so that if it fails the whole transaction rolls back
  -- and the account is still intact, rather than the account being gone and the reviews
  -- cascading away behind it.
  if to_regclass('public.reviews') is not null then
    update public.reviews set user_id = null where user_id = me;
  end if;

  -- Tables keyed to the caller by one owner column.
  --
  -- Two guards, not one. to_regclass covers a table this deploy does not have. The
  -- information_schema lookup covers the case that actually broke a migration on this project
  -- before: the table exists but the column is named something else. Without it, one wrong guess
  -- raises 42703 and the ENTIRE deletion aborts — the user is told deletion failed and their data
  -- stays. A table skipped for a renamed column leaves one table's rows behind; a table that
  -- raises leaves everything behind. The first failure mode is the survivable one, so it is the
  -- one this takes. Candidates are tried in order and the first that exists wins.
  for t in
    select * from (values
      ('my_sections',                  'user_id'),
      ('saved_classes',                'user_id'),
      ('watch_sections',               'user_id'),
      ('class_history',                'user_id'),
      ('review_helpful',               'voter_id,user_id'),
      ('friend_suggestion_dismissals', 'user_id'),
      -- added 2026-09-06 --------------------------------------------------------------------
      ('community_posts',              'user_id,author,author_id'),
      ('class_waivers',                'user_id'),
      ('free_now',                     'user_id'),
      ('professor_suggestions',        'user_id,suggested_by'),
      ('moderators',                   'user_id'),   -- a moderator who leaves stops being one
      ('suspensions',                  'user_id')
    ) as v(tbl, cols)
  loop
    if to_regclass('public.' || t.tbl) is not null then
      select c into col
        from unnest(string_to_array(t.cols, ',')) with ordinality as cand(c, ord)
       where exists (select 1 from information_schema.columns ic
                      where ic.table_schema='public' and ic.table_name=t.tbl
                        and ic.column_name=cand.c)
       order by cand.ord limit 1;
      if col is not null then
        execute format('delete from public.%I where %I = $1', t.tbl, col) using me;
      else
        raise notice 'delete_my_account: % has none of (%) — rows left behind', t.tbl, t.cols;
      end if;
    end if;
  end loop;

  -- Blocks are directional and both directions must go: the ones you made, and the ones pointing
  -- at you. Leaving the latter would keep a deleted account permanently blocked by strangers, for
  -- a person who no longer exists.
  if to_regclass('public.blocks') is not null then
    delete from public.blocks where blocker = me or blocked = me;
  end if;

  -- MESSAGES. The promise says your data goes with you, and a DM is your data — so the messages
  -- you sent are deleted rather than left attributed to a ghost account. This does leave gaps in
  -- the other person's thread, which is the honest trade: their copy of your words is not a reason
  -- to keep publishing them after you have asked to be erased.
  if to_regclass('public.messages') is not null then
    delete from public.messages where sender = me;
  end if;
  -- Leaving every conversation.
  if to_regclass('public.conversation_members') is not null then
    delete from public.conversation_members where user_id = me;
  end if;
  -- Threads you created split two ways, and getting this wrong destroys other people's messages.
  --
  -- conversations.created_by is NOT NULL REFERENCES auth.users ON DELETE CASCADE. So if a thread
  -- you started is still pointing at you when the auth.users row goes at the bottom of this
  -- function, the cascade takes the WHOLE THREAD with it — every message the other person wrote
  -- in it, in a thread they are still a member of. Their words are not yours to delete, and this
  -- was doing exactly that until a test with two users caught it (2026-09-06: bystander lost one
  -- of two messages, and the shared conversation vanished).
  --
  -- So: threads nobody is left in are removed, and threads someone IS left in are handed over.
  -- Both run AFTER the conversation_members delete above, so you are never a handover candidate.
  if to_regclass('public.conversations') is not null then
    -- (a) empty ones: you started it, you left, nobody else was ever in it.
    delete from public.conversations c
     where c.created_by = me
       and not exists (select 1 from public.conversation_members m where m.conversation_id = c.id);
    -- (b) the rest: hand the row to a remaining member so the cascade cannot reach it. Which
    --     member does not matter — groups are flat by instruction ("Any member can rename, add,
    --     remove"), and on a direct thread there is only one other person. Ordering by user_id
    --     keeps it deterministic without depending on a column beyond the primary key.
    update public.conversations c
       set created_by = (select m.user_id from public.conversation_members m
                          where m.conversation_id = c.id
                          order by m.user_id limit 1)
     where c.created_by = me
       and exists (select 1 from public.conversation_members m where m.conversation_id = c.id);
  end if;

  -- REPORTS ARE THE ONE THING KEPT BESIDES REVIEWS, and deliberately.
  --   Reports you FILED stay, de-authored: the person you reported may still be active, and a
  --   moderator dropping a live case because the reporter left is how harassment outlasts the
  --   person who reported it.
  --   Reports ABOUT you stay too, de-linked: they are the record of a decision a moderator made,
  --   and deleting an account is not a way to erase it.
  -- Both columns are ON DELETE SET NULL, so this would happen without naming them — done
  -- explicitly so the next reader knows it is a choice and not an oversight.
  if to_regclass('public.reports') is not null then
    update public.reports set reporter = null where reporter = me;
    -- target_user is left to its ON DELETE SET NULL: the reason, note and outcome survive.
  end if;

  -- Friendships are two-sided: remove the edge whichever end you are.
  if to_regclass('public.friend_requests') is not null then
    delete from public.friend_requests where from_user = me or to_user = me;
  end if;

  -- Anyone who dismissed this person as a suggestion no longer needs the row.
  if to_regclass('public.friend_suggestion_dismissals') is not null
     and exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='friend_suggestion_dismissals'
                    and column_name='dismissed_id') then
    delete from public.friend_suggestion_dismissals where dismissed_id = me;
  end if;

  -- Pinned-friend lists that pointed at this person.
  if exists (select 1 from information_schema.columns
             where table_schema='public' and table_name='profiles' and column_name='pinned_friends') then
    update public.profiles
       set pinned_friends = array_remove(pinned_friends, me)
     where pinned_friends @> array[me];
  end if;

  delete from public.profiles where id = me;

  -- Last, and only if everything above succeeded. By now no review points at this id, so no
  -- ON DELETE CASCADE can reach one.
  delete from auth.users where id = me;
end;
$$;

revoke execute on function public.delete_my_account() from public;
revoke execute on function public.delete_my_account() from anon;
grant   execute on function public.delete_my_account() to authenticated;

-- ------------------------------------------------------------------------------------------------
-- A suspension does not survive deleting your account, and cannot
-- ------------------------------------------------------------------------------------------------
-- Deleting the row above means a suspended student can delete their account, sign up again and be
-- unsuspended. That is worth stating rather than pretending otherwise: nothing here can stop
-- someone making a new account with a different .edu address, so the suspension was never the
-- durable control — the moderation record in `reports` is. Keeping a suspension keyed to a deleted
-- user id would achieve nothing except an orphan row.

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK — names every public table with a column pointing at auth.users that this function
-- does not handle. Anything listed here is a table added after today that deletion has not been
-- taught about. Read-only; it changes nothing.
-- ------------------------------------------------------------------------------------------------
do $$
declare r record; n int := 0;
begin
  for r in
    select c.relname as tbl, a.attname as col
      from pg_constraint k
      join pg_class     c on c.oid = k.conrelid
      join pg_namespace ns on ns.oid = c.relnamespace
      join pg_class     f on f.oid = k.confrelid
      join pg_namespace fs on fs.oid = f.relnamespace
      join unnest(k.conkey) as ck(attnum) on true
      join pg_attribute a on a.attrelid = c.oid and a.attnum = ck.attnum
     where k.contype = 'f' and ns.nspname = 'public'
       and fs.nspname = 'auth' and f.relname = 'users'
       and c.relname not in ('my_sections','saved_classes','watch_sections','class_history',
                             'review_helpful','friend_suggestion_dismissals','community_posts',
                             'class_waivers','free_now','professor_suggestions','moderators',
                             'suspensions','blocks','messages','conversation_members',
                             'conversations','reports','friend_requests','profiles','reviews')
     order by 1,2
  loop
    n := n + 1;
    raise notice 'DELETION DOES NOT HANDLE: public.%.%', r.tbl, r.col;
  end loop;
  if n = 0 then
    raise notice 'OK — every table referencing auth.users is handled by delete_my_account()';
  else
    raise notice '% column(s) above are not deleted. Decide for each: delete, de-author, or keep.', n;
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- VERIFY, with a throwaway account
-- ------------------------------------------------------------------------------------------------
--   Sign in as the throwaway, post a review, save a class, send a message, block someone,
--   file a report. Then:
--     select public.delete_my_account();
--   Then as yourself:
--     select count(*) from public.saved_classes  where user_id = '<their id>';   -- 0
--     select count(*) from public.messages       where sender  = '<their id>';   -- 0
--     select count(*) from public.blocks         where blocker = '<their id>'
--                                                   or blocked = '<their id>';   -- 0
--     select count(*) from public.reviews        where user_id = '<their id>';   -- 0
--     select count(*) from public.reviews        where user_id is null;          -- their review, kept
--     select reason, reporter from public.reports;                               -- kept, reporter null
