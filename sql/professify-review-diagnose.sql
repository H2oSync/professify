-- ================================================================================================
-- WHY ARE REVIEWS BEING REFUSED? — read-only diagnosis, 2026-09-28
-- ================================================================================================
-- Changes NOTHING. Paste into the Supabase SQL editor and Run; it prints one table. Send a
-- screenshot of it.
--
-- What prompted it: two reviews from the phone app were refused (one with a row-level-security
-- refusal, one with an unnamed error). Found on a Postgres 16 replica while looking: when
-- reviews.user_id is unreadable to `authenticated` (professify-reviews-anon-fix.sql, 09-06), the
-- insert policy's "reviews in the last hour" count — which reads r.user_id — fails with
-- "permission denied for table reviews" for EVERY insert, on the desktop too. Whether that is
-- what's live depends on which files ran in which order, which only this query can see.
-- ================================================================================================
select * from (
  select 1 as n, 'insert policies on reviews' as what,
         coalesce(string_agg(policyname || ' [' || array_to_string(roles, ',') || ']: ' || coalesce(with_check, '(none)'), '  ||  '), 'NONE') as answer
    from pg_policies where schemaname = 'public' and tablename = 'reviews' and cmd in ('INSERT', 'ALL')
  union all
  select 2, 'triggers on reviews',
         coalesce(string_agg(t.tgname || ' -> ' || p.proname || case when p.prosecdef then ' (definer)' else ' (invoker)' end, ', '), 'NONE')
    from pg_trigger t join pg_proc p on p.oid = t.tgfoid
   where t.tgrelid = 'public.reviews'::regclass and not t.tgisinternal
  union all
  select 3, 'can a signed-in student read reviews.user_id?',
         case when has_column_privilege('authenticated', 'public.reviews', 'user_id', 'SELECT') then 'yes' else 'NO (the column is hidden)' end
  union all
  select 4, 'can a signed-in student insert into reviews?',
         case when has_table_privilege('authenticated', 'public.reviews', 'INSERT') then 'yes' else 'NO' end
  union all
  select 5, 'why_cant_i_review() installed?',
         case when to_regprocedure('public.why_cant_i_review()') is null then 'no' else 'yes' end
  union all
  select 6, 'reviews in the table (total · newest)',
         count(*)::text || ' · ' || coalesce(to_char(max(created_at) at time zone 'America/Los_Angeles', 'YYYY-MM-DD HH24:MI'), 'none')
    from public.reviews
  union all
  select 7, 'reviews posted since 2026-09-06 (the day user_id was hidden)',
         count(*)::text from public.reviews where created_at >= '2026-09-06'
  union all
  select 8, 'the 5 most recent sign-ins: does the email end in .edu?',
         coalesce(string_agg(case when lower(email) like '%.edu' then '.edu' else 'NOT .edu' end
                             || ' (' || to_char(last_sign_in_at at time zone 'America/Los_Angeles', 'MM-DD HH24:MI') || ')', ', '), 'none')
    from (select email, last_sign_in_at from auth.users order by last_sign_in_at desc nulls last limit 5) u
) d order by n;
