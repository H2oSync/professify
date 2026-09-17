-- ================================================================================================
-- THE ADVISOR'S THREE "SECURITY DEFINER VIEW" WARNINGS — 2026-09-12
-- ================================================================================================
-- Tate sent a screenshot of the Supabase dashboard: "Advisor found 3 issues", all CRITICAL, all
-- the same lint (splinter 0010, security_definer_view), on:
--
--     public.prof_activity_7d
--     public.professor_review_stats
--     public.reviews_public
--
-- WHAT THE LINT ACTUALLY SAYS. A PostgreSQL view runs as its OWNER unless it is created with
-- `with (security_invoker = true)`. Owner-runs is the DEFAULT and always has been, so this lint
-- fires on every view in an API-exposed schema that nobody explicitly opted out of. It is not
-- reporting that something went wrong; it is reporting that a view can read past RLS on its base
-- table, and it has no way to know whether that is the point of the view or an accident.
--
-- For two of these three it is the point. For the third, the view should not exist at all.
--
-- THE FINDING THAT CAME OUT OF CHECKING. Reading reviews_public to answer the question turned up
-- a real defect that the Advisor did not and could not flag: a review removed by a moderator was
-- still being served to the public. See section 2. That is the actual bug on this screen.
--
-- Run AFTER professify-messaging.sql, professify-safety.sql and professify-analytics.sql.
-- Safe to re-run.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 1. public.professor_review_stats — DELETE IT. Nothing has ever read it.
-- ------------------------------------------------------------------------------------------------
-- Written in the very first setup file (supabase-setup.sql, section commented "Optional: public
-- aggregate stats per professor (handy for future features)") and never wired to anything. The
-- client does not mention it. No function reads it. It has been a public, RLS-bypassing view over
-- the reviews table for the entire life of the project, kept alive by nobody deciding to remove it.
--
-- It exposes only aggregates — count, average score, would-again percentage per professor — so
-- this is not a leak being closed; every one of those numbers can be computed from reviews_public,
-- which is public on purpose. It is dead surface, and dead surface is the cheapest kind to delete.
--
-- No CASCADE. If something turns out to depend on this after all, the drop should fail loudly and
-- tell us, not quietly take the dependent with it.
do $$
begin
  if exists (select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
              where n.nspname = 'public' and c.relname = 'professor_review_stats'
                and c.relkind = 'v') then
    execute 'drop view public.professor_review_stats';
    raise notice 'professor_review_stats: dropped (unused since supabase-setup.sql)';
  else
    raise notice 'professor_review_stats: already gone';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 2. public.reviews_public — STAYS A DEFINER VIEW. It is the whole privacy design.
-- ------------------------------------------------------------------------------------------------
-- public.reviews is RLS'd so that a row is readable only by the student who wrote it. Every review
-- on every professor page is served from this view instead, which runs as its owner, reads past
-- that policy, and hands back the same rows with no author column in them at all. The privacy
-- policy in the app states this as a fact:
--
--     "Reviews are served to everyone — signed in or not — from a database view that does not
--      contain an author column at all, and the underlying table is readable only by the person
--      who wrote the row."
--
-- Setting security_invoker = true here — the lint's stated remediation — would make the view run
-- as the caller, the caller would hit the RLS policy, and every professor page would show each
-- student only their own reviews. It would not error. It would just empty the site. Section 5
-- exists to catch exactly that change if anyone ever makes it to silence the warning.
--
-- WHAT IS BEING FIXED HERE, WHICH IS NOT THE LINT:
--
-- professify-safety.sql gave moderators mod_remove_review(), which soft-removes a review by
-- stamping removed_at and removed_by. Nothing ever taught this view about those columns. The view
-- was built from the column list as it stood before they existed, and it has no WHERE clause, so
-- a removed review kept coming back to every professor page exactly as before.
--
-- The client looks like it covers this — the professor modal renders
--
--     revs.filter(function(r){ return !r.removed_at; })
--
-- but REVIEW_COLS never requests removed_at and the row mapper never copies it, so r.removed_at is
-- undefined on every row and the filter passes everything. A filter that cannot fail is not a
-- control. Moderation has been writing a timestamp nobody reads.
--
-- So the filter moves to where it cannot be bypassed by a client that forgot a column, and the two
-- moderation columns are excluded from the view as well: removed_by is a MODERATOR's auth.users id,
-- and there is no version of "reviews are anonymous" that includes publishing who took one down.
do $$
declare cols text; has_removed boolean;
begin
  select exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='reviews'
                    and column_name='removed_at') into has_removed;

  select string_agg(quote_ident(column_name), ', ' order by ordinal_position)
    into cols
    from information_schema.columns
   where table_schema = 'public'
     and table_name   = 'reviews'
     -- user_id is the one that must never come through: the same id appears on schedule rows, so
     -- a named professor could work out which student wrote a bad review.
     -- share_with_friends is somebody's privacy SETTING rather than review content, and a public
     -- list of who has opted in is not what this view is for.
     -- removed_at / removed_by are moderation bookkeeping. The view acts on removed_at below
     -- rather than publishing it.
     and column_name not in ('user_id', 'share_with_friends', 'removed_at', 'removed_by');

  if cols is null then
    raise exception 'public.reviews not found — run professify-rls-hardening.sql first';
  end if;

  execute 'drop view if exists public.reviews_public';
  execute 'create view public.reviews_public with (security_invoker = false) as select '
          || cols || ' from public.reviews'
          || case when has_removed then ' where removed_at is null' else '' end;

  raise notice 'reviews_public: rebuilt, definer on purpose, removed reviews %',
    case when has_removed then 'now excluded' else 'column not present on this project' end;
end $$;

grant select on public.reviews_public to anon, authenticated;

comment on view public.reviews_public is
  'Deliberately SECURITY DEFINER (security_invoker = false). public.reviews is RLS''d to the row''s '
  'author; this view is how reviews are served publicly without an author column. Flipping it to '
  'security_invoker = true to silence the Supabase Advisor would show each student only their own '
  'reviews and empty every professor page. See sql/professify-view-security.sql.';


-- ------------------------------------------------------------------------------------------------
-- 3. public.prof_activity_7d — STAYS A DEFINER VIEW, and loses a door it never needed.
-- ------------------------------------------------------------------------------------------------
-- Same shape as reviews_public, over the analytics events table. public.events is revoked from
-- anon, public and authenticated — nobody reads it row by row, which is the promise
-- professify-analytics.sql makes and self-checks. This view aggregates it into per-professor
-- counts of distinct pseudonyms with no `who` column and no timestamps, and runs as its owner
-- because that is the only way an aggregate over an unreadable table can be read at all.
--
-- What is being tightened: the view is granted SELECT to anon and authenticated, but the app has
-- never read it directly. The only caller is trending_profs(), which is itself SECURITY DEFINER
-- and therefore does not need the grant. So the grant is a second public door onto the same data
-- with none of the floors trending_profs() enforces — it clamps the honesty threshold to at least
-- three viewers, so a professor two people glanced at is never called trending. Reading the view
-- straight past that is exactly the claim the threshold exists to prevent.
--
-- One door, and it is the one with the rules on it.
revoke select on public.prof_activity_7d from anon, authenticated;

comment on view public.prof_activity_7d is
  'Deliberately SECURITY DEFINER (security_invoker = false). public.events is unreadable by every '
  'client role; this view is the only aggregate path out of it and carries no per-person column. '
  'Not granted to anon or authenticated: read it through trending_profs(), which enforces the '
  'minimum-viewers threshold. See sql/professify-view-security.sql.';


-- ------------------------------------------------------------------------------------------------
-- 4. Self-check
-- ------------------------------------------------------------------------------------------------
-- The failure this guards against is specific and quiet: someone opens the Advisor, sees three
-- CRITICAL warnings, applies the documented remediation to all three, and the site stops showing
-- reviews without a single error in any log. Both survivors must still be definer views, and
-- reviews_public must still refuse removed rows.
do $$
declare bad int := 0; opts text[]; def text;
begin
  if exists (select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
              where n.nspname='public' and c.relname='professor_review_stats') then
    raise warning 'professor_review_stats still exists'; bad := bad + 1;
  end if;

  select c.reloptions into opts from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='reviews_public';
  if opts is not null and array_to_string(opts, ',') ilike '%security_invoker=true%' then
    raise warning 'reviews_public is security_invoker=true — every professor page now shows a student only their OWN reviews. This view must stay SECURITY DEFINER.';
    bad := bad + 1;
  end if;

  select pg_get_viewdef('public.reviews_public'::regclass, true) into def;
  if def ilike '%user_id%' then
    raise warning 'reviews_public exposes user_id'; bad := bad + 1;
  end if;
  if exists (select 1 from information_schema.columns
              where table_schema='public' and table_name='reviews' and column_name='removed_at')
     and def not ilike '%removed_at is null%' then
    raise warning 'reviews_public does not exclude removed reviews — moderation is decorative'; bad := bad + 1;
  end if;

  select c.reloptions into opts from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='prof_activity_7d';
  if opts is not null and array_to_string(opts, ',') ilike '%security_invoker=true%' then
    raise warning 'prof_activity_7d is security_invoker=true — events is unreadable by clients, so this view now returns nothing and the trending strip is permanently empty.';
    bad := bad + 1;
  end if;

  if has_table_privilege('anon','public.prof_activity_7d','SELECT')
     or has_table_privilege('authenticated','public.prof_activity_7d','SELECT') then
    raise warning 'prof_activity_7d is still directly readable — trending_profs() should be the only path'; bad := bad + 1;
  end if;

  if bad = 0 then
    raise notice 'views: one dropped, two definer on purpose and documented, removed reviews are out of reviews_public';
  else
    raise exception '% problem(s) above', bad;
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 5. AFTERWARDS: the Advisor will still show two warnings, and that is the correct outcome
-- ------------------------------------------------------------------------------------------------
-- Three becomes two. The two that remain are reviews_public and prof_activity_7d, and they remain
-- because the lint is describing a property they are supposed to have. Supabase's Advisor lets a
-- finding be dismissed from the dashboard if you want the list clean; the comments attached to
-- both views above are the durable version of that decision, because they travel with the database
-- rather than living in a UI setting.
--
-- VERIFY, signed out, from the browser console on professify.app:
--
--     await sb.from('reviews_public').select('*').limit(1)      -- rows, and no user_id column
--     await sb.from('reviews').select('*').limit(1)             -- refused / empty
--     await sb.from('prof_activity_7d').select('*').limit(1)    -- permission denied
--     await sb.rpc('trending_profs',{p_limit:10,p_min:5})       -- works
--     await sb.from('professor_review_stats').select('*')       -- does not exist
