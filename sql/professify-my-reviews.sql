-- ================================================================================================
-- "YOUR REVIEWS" IS BROKEN ON PRODUCTION — 2026-09-07
-- ================================================================================================
-- professify-reviews-anon-fix.sql (run 2026-09-06) revoked SELECT on reviews.user_id from
-- `authenticated` as belt-and-braces behind the row policies, so that a permissive policy added
-- later under yet another name — which has now happened twice on this database — cannot re-expose
-- who wrote what.
--
-- That revoke was right and stays. What it also did, unnoticed, is break the app's own screen.
--
-- In PostgreSQL a column referenced in a WHERE clause needs SELECT privilege on that column, the
-- same as one in the select list. Every query the app makes for your own reviews filters on
-- user_id:
--
--     .select('*').eq('user_id', me)                     loadMyReviews()
--     .select('id,professor_key,share_with_friends').eq('user_id', me)   myShares()
--     .update({share_with_friends}).eq('id',id).eq('user_id', me)        setShare()
--
-- All three now fail with 42501. Reproduced on PostgreSQL 16 before writing this:
--
--     select * from public.reviews where user_id = auth.uid();      -> permission denied
--     select id, prof from public.reviews where user_id = auth.uid(); -> permission denied
--     select id, prof from public.reviews;                          -> 1 row, the caller's own
--
-- The third line is the point: the row policy "authors read their own reviews" ALREADY filters to
-- the caller. Policy expressions run as the table owner, so they may read a column the caller
-- cannot. The client's own filter was redundant — and is now fatal.
--
-- This matters more than one settings screen. The delete-account dialog tells students "Delete
-- them first instead →" and sends them to exactly this list, and the Terms, the Privacy Policy and
-- the Settings copy all promise that deleting a review before closing your account is how you keep
-- it from becoming permanent. A list that will not load makes all four of those promises unkeepable.
--
-- WHY A FUNCTION RATHER THAN GRANTING THE COLUMN BACK. Granting select(user_id) would also work —
-- the rows RLS lets you see are your own plus reviews a friend explicitly chose to put their name
-- to, so nothing leaks THROUGH THE POLICIES AS THEY STAND TODAY. But that is exactly the assumption
-- that failed twice before. A SECURITY DEFINER function filtered on auth.uid() gives the screen
-- what it needs without the column ever being readable, so the next stray using(true) policy still
-- cannot de-anonymise anyone.
--
-- Safe to re-run. Run AFTER professify-reviews-anon-fix.sql.
-- ================================================================================================

drop function if exists public.my_reviews();

create or replace function public.my_reviews()
returns setof public.reviews
language sql
security definer
stable
set search_path = public
as $$
  -- auth.uid() inside the body, never a caller-supplied id: this cannot be pointed at anyone else.
  select r.* from public.reviews r
   where r.user_id = auth.uid()
   order by r.created_at desc
$$;

-- returns setof reviews, so it hands back every column including ones added later without this
-- function needing to be rewritten. The caller only ever gets rows where user_id = their own id,
-- so returning user_id here reveals nothing they did not already know.

revoke all     on function public.my_reviews() from public;   -- `from anon` alone is a no-op:
revoke execute on function public.my_reviews() from anon;     -- PUBLIC holds EXECUTE by default
grant  execute on function public.my_reviews() to authenticated;

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK
-- ------------------------------------------------------------------------------------------------
do $$
declare has_col boolean; n int;
begin
  select has_column_privilege('authenticated','public.reviews','user_id','SELECT') into has_col;
  if has_col then
    raise notice 'NOTE: authenticated can still read reviews.user_id — reviews-anon-fix has not run, or was undone.';
  else
    raise notice 'OK — reviews.user_id is unreadable, and my_reviews() is how the app reads your own.';
  end if;
  select count(*) into n from pg_policies
   where schemaname='public' and tablename='reviews'
     and cmd in ('SELECT','ALL') and permissive='PERMISSIVE' and coalesce(qual,'true')='true';
  if n > 0 then
    raise warning '% wide-open SELECT polic(ies) on reviews — re-run professify-reviews-anon-fix.sql', n;
  end if;
end $$;
