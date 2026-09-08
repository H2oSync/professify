-- ============================================================================
-- RLS hardening — two CONFIRMED exposures, verified against production
-- ============================================================================
-- Method: a Supabase client was built in the browser from SUPABASE_ANON_KEY —
-- the publishable key already present in professify.app's page source, which any
-- visitor can read from devtools — with NO user session attached. It then read
-- from each table. Anything it got back is readable by the entire internet.
--
-- Result (2026-08-23, professify.app):
--   profiles        anonymous read -> 0 rows   (RLS working)
--   saved_classes   anonymous read -> 0 rows   (RLS working)
--   watch_sections  anonymous read -> 0 rows   (RLS working)
--   class_history   anonymous read -> 0 rows   (RLS working)
--   friend_requests anonymous read -> 0 rows   (RLS working)
--   review_helpful  anonymous read -> 0 rows   (RLS working)
--   my_sections     anonymous read -> 4 ROWS   <-- FINDING 1
--   reviews         anonymous read -> 7 ROWS, including user_id  <-- FINDING 2
--
-- This file fixes those two. It does not make the application "secure"; it
-- closes two specific holes that were demonstrated, and nothing more.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- FINDING 1 (critical) — my_sections is world-readable
-- ---------------------------------------------------------------------------
-- Anonymous clients read: user_id, code, class_nbr, section, instructor, days,
-- status, wl_pos. That is a named student's exact weekly whereabouts — which
-- building-hour they are in, which professor, and whether they are waitlisted.
-- It is readable without an account, so it is enumerable for every student who
-- ever imports a schedule. This is the table the whole Quad feature depends on,
-- so it will only get more populated.
--
-- NOTE: this supersedes professify-friend-sections.sql. That file was never
-- applied. Friends could read each other's sections not because a policy
-- allowed it but because NO policy was being enforced — an earlier session
-- read "friends can see sections" as evidence the policy was live. It was not.

alter table public.my_sections enable row level security;

-- Your own rows: full access.
drop policy if exists "own sections" on public.my_sections;
create policy "own sections"
  on public.my_sections for all
  using ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

-- Accepted friends may READ your sections — the same relationship that already
-- governs seeing each other's class lists. Read only, and never anonymous:
-- auth.uid() is null for a signed-out client, so this matches nothing for them.
drop policy if exists "friends can read sections" on public.my_sections;
create policy "friends can read sections"
  on public.my_sections for select
  using (
    exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and ( (fr.from_user = auth.uid() and fr.to_user   = my_sections.user_id)
           or (fr.to_user   = auth.uid() and fr.from_user = my_sections.user_id) )
    )
  );


-- ---------------------------------------------------------------------------
-- FINDING 2 (high) — reviews expose their author's user_id to the public
-- ---------------------------------------------------------------------------
-- Review CONTENT is meant to be public. The AUTHOR is not. Today an anonymous
-- client reads user_id alongside every review, and that same user_id appears on
-- my_sections and saved_classes rows — so a review can be tied to a person's
-- schedule, and a professor reading a negative review can work out who wrote it.
-- Students are being told reviews are safe to write honestly.
--
-- Column-level revoke: PostgREST honours column grants, so the column simply
-- stops existing for signed-out callers. The app's public review query was
-- changed in the same build to list columns explicitly instead of select('*'),
-- which is what keeps it working after this runs.
--
-- `authenticated` keeps the column because the app filters on it for
-- "my reviews" (.eq('user_id', sbUser.id)) — PostgREST needs SELECT on a column
-- to filter by it. See RESIDUAL RISK below; this is a partial fix.

revoke select (user_id) on public.reviews from anon;

-- Writes must still be owner-only. Enable RLS if it is not already on, and make
-- the ownership rules explicit rather than assumed.
alter table public.reviews enable row level security;

drop policy if exists "reviews are publicly readable" on public.reviews;
create policy "reviews are publicly readable"
  on public.reviews for select
  using ( true );

drop policy if exists "authors write their own reviews" on public.reviews;
create policy "authors write their own reviews"
  on public.reviews for insert
  with check ( auth.uid() = user_id );

drop policy if exists "authors edit their own reviews" on public.reviews;
create policy "authors edit their own reviews"
  on public.reviews for update
  using ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

drop policy if exists "authors delete their own reviews" on public.reviews;
create policy "authors delete their own reviews"
  on public.reviews for delete
  using ( auth.uid() = user_id );


-- ---------------------------------------------------------------------------
-- VERIFY (run after applying; both must come back empty / error)
-- ---------------------------------------------------------------------------
--   In a browser devtools console on professify.app, signed OUT:
--     const c=window.PROFESSIFY_CONFIG;
--     const a=window.supabase.createClient(c.SUPABASE_URL,c.SUPABASE_ANON_KEY,
--             {auth:{persistSession:false,storageKey:'v'}});
--     await a.from('my_sections').select('*',{count:'exact',head:true});   // expect count 0
--     await a.from('reviews').select('user_id').limit(1);                  // expect an error
--
-- And confirm the app still works signed out: a professor page must still list
-- its reviews. If reviews vanish, the app is on a build older than 18:45 and is
-- still asking for select('*').


-- ---------------------------------------------------------------------------
-- RESIDUAL RISK — not fixed by this file
-- ---------------------------------------------------------------------------
-- 1. Any SIGNED-IN student can still read reviews.user_id and de-anonymise
--    other students. Closing that properly means serving public reviews from a
--    view that omits user_id and restricting the base table to its owner. That
--    is an app change, not a policy change, and it needs your decision about
--    what review anonymity is supposed to promise.
-- 2. Whether a signed-in NON-friend can read another student's saved_classes,
--    class_history or profile row was NOT tested — it needs a second test
--    account. profiles returned 5 rows to a signed-in user; if that is every
--    profile in the system rather than just this user's friends, edu_email and
--    instagram_handle are exposed account-wide.
-- 3. Anonymous UPDATE on profiles returned "0 rows affected" rather than an
--    error. That is what a correct policy AND a missing policy both look like,
--    so it proves nothing either way and still needs checking.
-- 4. No penetration test, no review of the Supabase service-role key's handling
--    in CI, no dependency/supply-chain audit.
