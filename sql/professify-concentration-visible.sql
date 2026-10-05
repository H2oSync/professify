-- ================================================================================================
-- FRIENDS CAN SEE YOUR CONCENTRATION — 2026-10-04 (Tate: "i should also be able to see friends
-- majors and concentrations")
-- ================================================================================================
-- professify-lockdown.sql grants `authenticated` SELECT on a fixed list of profiles columns
-- (id, display_name, username, avatar_url, major, class_standing, pinned_friends,
-- instagram_handle). `concentration` was left off, so the phone can show a friend's major and year
-- but not their concentration. This adds that one column to the same grant — the same audience
-- that already reads `major` (the profiles RLS policy decides whose rows), nothing wider.
--
-- Additive, one statement, safe to re-run. If the column doesn't exist it says so and does nothing.
-- professify-lockdown.sql now lists `concentration` too, so re-running it keeps this grant.
--
-- Check after:  select has_column_privilege('authenticated', 'public.profiles', 'concentration', 'select');
--               → true
-- ================================================================================================
do $$
begin
  if exists (select 1 from information_schema.columns
             where table_schema = 'public' and table_name = 'profiles' and column_name = 'concentration') then
    grant select (concentration) on public.profiles to authenticated;
    raise notice 'profiles.concentration: SELECT granted to authenticated';
  else
    raise notice 'profiles.concentration does not exist — nothing to grant (the app shows major and year only)';
  end if;
end $$;
