-- ============================================================================
-- Review integrity — server-side limits
-- ============================================================================
-- The app now refuses a duplicate or a 6th-review-in-an-hour before you finish
-- typing, but that check runs in the browser and anyone can skip it by calling
-- the REST API directly with the publishable key. These two rules are the ones
-- that actually hold, because Postgres enforces them.
--
-- Run AFTER professify-rls-hardening.sql (it replaces the insert policy created
-- there). Safe to re-run.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. One review per person, per professor, per course.
-- ---------------------------------------------------------------------------
-- Without this, one account can post the same professor a hundred 1-star
-- reviews and move their average single-handedly. The app already expects this
-- constraint — it catches the unique violation and says "you've already
-- reviewed this" — it just was never created.
--
-- If this errors, you already have duplicates. Find them first:
--   select user_id, professor_key, coalesce(course_key,'') k, count(*)
--     from public.reviews group by 1,2,3 having count(*) > 1;

create unique index if not exists reviews_one_per_course_idx
  on public.reviews (user_id, professor_key, coalesce(course_key, ''));


-- ---------------------------------------------------------------------------
-- 2. At most 5 reviews an hour, enforced at insert.
-- ---------------------------------------------------------------------------
-- Stops bulk-posting across many professors, which the unique index above does
-- not cover. The subquery runs per insert; reviews is small and user_id is
-- indexed by the unique index above, so the cost is negligible.

drop policy if exists "authors write their own reviews" on public.reviews;
create policy "authors write their own reviews"
  on public.reviews for insert
  with check (
    auth.uid() = user_id
    and (
      select count(*) from public.reviews r
      where r.user_id = auth.uid()
        and r.created_at > now() - interval '1 hour'
    ) < 5
  );


-- ---------------------------------------------------------------------------
-- 3. Lock down the classmate-suggestion function (Section B of the review).
-- ---------------------------------------------------------------------------
-- It was callable by anonymous clients. It returned nothing, which suggests it
-- keys off auth.uid() and fails closed — but a function reachable from the open
-- internet should be reachable on purpose.

revoke execute on function public.suggest_classmates() from anon;


-- ---------------------------------------------------------------------------
-- VERIFY
-- ---------------------------------------------------------------------------
--   Post a review, then try posting the same professor + course again.
--   Expect: "You've already reviewed <name> for this course."
--
--   The hourly cap only shows itself at 6 reviews in an hour; the app blocks at
--   5 first, so to see the server rule fire you have to call the API directly.
