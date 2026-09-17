-- ================================================================================================
-- PINNED FRIENDS — the half of professify-free-now.sql that survived
-- ================================================================================================
-- professify-free-now.sql did two unrelated things: it created the `free_now` table for the
-- "I'm free now" declaration, and it added `profiles.pinned_friends`.
--
-- THE FREE-NOW HALF IS DEAD. Tate removed that control on 2026-09-05 and the note left in the
-- client says why: a timetable can show that nothing is scheduled, only a person can say they
-- are free. With the control gone there is nobody to say it, so every surface that read a
-- declaration went with it rather than sitting dormant waiting for data that can no longer
-- exist. Push kept the half a timetable CAN prove — "done for the day", from the real schedule —
-- which needs none of this. Creating `free_now` now would be building a table for a control
-- that does not exist and is not coming back.
--
-- THE PINS HALF IS LIVE. The Home feed still ranks pinned friends first (`a.pinned` in
-- hmRenderFeed's sort), and epPins() reads `myProfile.pinned_friends` on every render. Without
-- this column pins silently do not save — and the client is already defensive about exactly
-- that: it asks for `pinned_friends` in a SEPARATE select from the rest of the profile, because
-- one missing column 42703s the whole query and takes the profile down with it.
--
-- So this file is section 2 of professify-free-now.sql, lifted verbatim, and nothing else.
-- Run in the Supabase SQL editor. Safe to re-run.
--
-- IS IT ALREADY THERE? Two records in this repo disagree — sql/README.md says free-now was never
-- run, and a comment in the client says the free_now table "is already deployed". One of them is
-- wrong and neither is worth trusting. This settles it in one query:
--
--     select column_name from information_schema.columns
--      where table_schema='public' and table_name='profiles' and column_name='pinned_friends';
--
-- No row back means pins have never saved for anybody. Re-running this when it is already there
-- does nothing either way.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- profiles.pinned_friends — two, and the database says two
-- ------------------------------------------------------------------------------------------------
-- The cap is the feature. A pin list that grows is the friends list again in a different order,
-- and the top of the feed stops meaning anything. The app enforces it and explains it — a third
-- pin is refused with the two current names in the message, never silently evicting one — and the
-- constraint is here so a stale tab or a direct API call cannot quietly make it five.
alter table public.profiles add column if not exists pinned_friends uuid[];

do $$ begin
  if not exists (select 1 from pg_constraint where conname='profiles_pins_max_ck') then
    alter table public.profiles
      add constraint profiles_pins_max_ck
      check (pinned_friends is null or cardinality(pinned_friends) <= 2);
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- Say what the database now believes
-- ------------------------------------------------------------------------------------------------
do $$
declare has_col boolean; has_ck boolean;
begin
  select exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='profiles'
                    and column_name='pinned_friends') into has_col;
  select exists (select 1 from pg_constraint where conname='profiles_pins_max_ck') into has_ck;
  if has_col and has_ck then
    raise notice 'pinned_friends: column present, capped at 2 — pins will save';
  else
    raise exception 'pinned_friends did not install (column %, constraint %)', has_col, has_ck;
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- VERIFY, as a signed-in student — from the browser console on professify.app
-- ------------------------------------------------------------------------------------------------
--   await sb.from('profiles').update({pinned_friends:[<one uuid>,<another uuid>]}).eq('id', sbUser.id)
--     -- expect: ok
--   await sb.from('profiles').update({pinned_friends:[<three uuids>]}).eq('id', sbUser.id)
--     -- expect: violates check constraint "profiles_pins_max_ck"
