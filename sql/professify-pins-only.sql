-- ================================================================================================
-- PINNED FRIENDS ONLY — the half of professify-free-now.sql that is still a live feature
-- 2026-09-16
-- ================================================================================================
-- WHY THIS FILE EXISTS. professify-free-now.sql does two unrelated things under one name:
--
--   Section 1 + 3 — the `free_now` table, its RLS, trigger, index and realtime publication.
--                   DEAD. Free Now was removed from the app on 2026-09-05. Nothing reads or
--                   writes that table from the client. Do not run it.
--
--   Section 2     — `profiles.pinned_friends`. NOT Free Now. It is the "pin two friends to the
--                   top of Home" feature, which is still in the app today: the profile select on
--                   sign-in asks for the column by name, and pinFriend() writes to it.
--
-- So "I didn't want Free Now" and "pins should work" are both true, and the original file cannot
-- express that. This is section 2 alone.
--
-- WHAT IS BROKEN UNTIL THIS RUNS. Verified against production 2026-09-16: profiles.pinned_friends
-- does not exist. So pinning a friend fails on every attempt — the app updates its local copy,
-- re-renders, sends the write, gets 42703 undefined_column, rolls the pin back and toasts
-- "Could not save that pin — the column may not be installed yet." The feature is in the UI and
-- has never once worked in production.
--
-- Idempotent and safe to re-run. Adds one nullable column and one CHECK; touches no existing row.
-- ================================================================================================

-- The cap is the feature. A pin list that grows is the friends list again in a different order,
-- and the top of the feed stops meaning anything. The app enforces two and explains the refusal
-- by name; the constraint is here so a stale tab or a direct API call cannot quietly make it five.
alter table public.profiles add column if not exists pinned_friends uuid[];

do $$ begin
  if not exists (select 1 from pg_constraint where conname='profiles_pins_max_ck') then
    alter table public.profiles
      add constraint profiles_pins_max_ck
      check (pinned_friends is null or cardinality(pinned_friends) <= 2);
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK — raises rather than reporting success it did not achieve
-- ------------------------------------------------------------------------------------------------
do $$
begin
  if not exists (select 1 from information_schema.columns
                 where table_schema='public' and table_name='profiles'
                   and column_name='pinned_friends') then
    raise exception 'pinned_friends was not added';
  end if;
  if not exists (select 1 from pg_constraint where conname='profiles_pins_max_ck') then
    raise exception 'profiles_pins_max_ck was not added';
  end if;
  raise notice 'pinned_friends + two-pin cap are in place';
end $$;

-- ------------------------------------------------------------------------------------------------
-- VERIFY as a signed-in student, not the service role:
--   update public.profiles set pinned_friends = array[...three uuids...] where id = auth.uid();
--     -- expect: violates check constraint "profiles_pins_max_ck"
-- ------------------------------------------------------------------------------------------------
