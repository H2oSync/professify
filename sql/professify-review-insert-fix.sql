-- ================================================================================================
-- REVIEWS COULD NOT BE POSTED AT ALL — the fix, 2026-09-28
-- ================================================================================================
-- Run ONLY after professify-review-diagnose.sql shows row 3 = "NO (the column is hidden)" and
-- row 1's policy containing "select count(*) from public.reviews" (it prints "FROM reviews r").
--
-- WHAT IS WRONG. Two files, each right on its own, break every review together:
--   · professify-reviews-anon-fix.sql (09-06) hides reviews.user_id from `authenticated`, so no
--     student can ever read who wrote a review. Correct, and it stays.
--   · the insert policy (professify-review-refusals.sql, 09-11) caps reviews at 30 an hour by
--     counting `from public.reviews r where r.user_id = auth.uid()`. That count is a SELECT run
--     as the student — and the student cannot read user_id. PostgreSQL answers
--     "permission denied for table reviews" to EVERY insert, before any rule is even checked.
--     The trigger that explains refusals (reviews_explain_refusal) and why_cant_i_review() run the
--     same count as the student, so they fail the same way and cannot say why.
--     Depending on which policies are present the refusal surfaces as 42501 "permission denied for
--     table reviews", or as 42P17 "infinite recursion detected in policy for relation reviews" (the
--     count's SELECT meets the friends-can-see-your-name SELECT policy from the anon fix). The second
--     one contains the word "policy", which is why the phone app first called it "the limit".
--     Removing the subquery cures both.
--
-- RE-RUNNING OLDER FILES PUTS IT BACK. professify-review-refusals.sql, professify-safety.sql,
-- professify-rate-limits.sql and professify-review-integrity.sql each recreate the old policy. If you
-- ever re-run one of them, run this file straight after it.
-- Proven on a Postgres 16 replica: with the column hidden, no insert gets through; with the count
-- moved into a SECURITY DEFINER function, inserts land and user_id is still unreadable.
--
-- WHAT THIS DOES (one transaction, safe to re-run, changes no data):
--   1. public.my_reviews_last_hour() — SECURITY DEFINER, counts only the CALLER's own reviews in
--      the last hour, returns a number and nothing else. No argument, so it cannot be pointed at
--      anyone else.
--   2. Recreates "authors write their own reviews" with that function in place of the subquery.
--      Every other clause is carried: auth.uid() = user_id, not suspended, and the .edu clause
--      only if the current policy has it (detected, as the earlier files do — never added).
--   3. reviews_explain_refusal() and why_cant_i_review() become SECURITY DEFINER. Both only ever
--      look at the caller's own rows through auth.uid(), and both keep their pinned search_path.
--   4. Self-checks that raise if anything above didn't take.
-- ================================================================================================
begin;

create or replace function public.my_reviews_last_hour()
returns integer
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select count(*)::int
    from public.reviews r
   where r.user_id = auth.uid()
     and r.created_at > now() - interval '1 hour'
$$;
revoke all on function public.my_reviews_last_hour() from public;
revoke execute on function public.my_reviews_last_hour() from anon;
grant execute on function public.my_reviews_last_hour() to authenticated;

do $$
declare has_edu boolean; has_susp boolean;
begin
  select coalesce(bool_or(coalesce(with_check, '') like '%.edu%'), false)
    into has_edu
    from pg_policies
   where schemaname = 'public' and tablename = 'reviews' and cmd in ('INSERT', 'ALL');
  has_susp := to_regprocedure('public.is_suspended(uuid)') is not null;

  execute 'drop policy if exists "authors write their own reviews" on public.reviews';
  execute format($f$
    create policy "authors write their own reviews"
      on public.reviews for insert to authenticated
      with check (
        auth.uid() = user_id
        %s
        %s
        and public.my_reviews_last_hour() < 30
      )$f$,
    case when has_edu then $e$and lower(coalesce(auth.jwt() ->> 'email', '')) like '%.edu'$e$ else '' end,
    case when has_susp then 'and not public.is_suspended(auth.uid())' else '' end);
  raise notice 'reviews: insert policy recreated (.edu clause %, suspension clause %)',
    case when has_edu then 'kept' else 'not present' end, case when has_susp then 'kept' else 'not installed' end;
end $$;

do $$ begin
  if to_regprocedure('public.reviews_explain_refusal()') is not null then
    execute 'alter function public.reviews_explain_refusal() security definer';
    execute 'alter function public.reviews_explain_refusal() set search_path = public, pg_temp';
    raise notice 'reviews_explain_refusal(): now security definer';
  end if;
  if to_regprocedure('public.why_cant_i_review()') is not null then
    execute 'alter function public.why_cant_i_review() security definer';
    execute 'alter function public.why_cant_i_review() set search_path = public, pg_temp';
    execute 'revoke all on function public.why_cant_i_review() from public';
    execute 'grant execute on function public.why_cant_i_review() to authenticated';
    raise notice 'why_cant_i_review(): now security definer';
  end if;
end $$;

-- ---- self-checks ----------------------------------------------------------------------------------
do $$
declare wc text; bad int := 0; n int;
begin
  select string_agg(coalesce(with_check, ''), ' ') into wc
    from pg_policies where schemaname = 'public' and tablename = 'reviews' and cmd in ('INSERT', 'ALL');
  if wc is null then raise warning 'no insert policy on reviews at all'; bad := bad + 1; end if;
  if wc ilike '%from reviews%' or wc ilike '%from public.reviews%' then
    raise warning 'an insert policy still counts reviews as the student: %', wc; bad := bad + 1; end if;
  if wc not like '%my_reviews_last_hour() < 30%' then
    raise warning 'the insert policy is not capped at 30 through my_reviews_last_hour(): %', wc; bad := bad + 1; end if;
  select count(*) into n from pg_policies
   where schemaname = 'public' and tablename = 'reviews' and cmd in ('INSERT', 'ALL');
  if n > 1 then raise warning '% insert policies on reviews — they OR together, and an uncapped one opens the door', n; bad := bad + 1; end if;
  if has_column_privilege('authenticated', 'public.reviews', 'user_id', 'SELECT') then
    raise warning 'reviews.user_id is READABLE by students — this file must not change that, so something else did'; bad := bad + 1; end if;
  if not (select prosecdef from pg_proc where oid = 'public.my_reviews_last_hour()'::regprocedure) then
    raise warning 'my_reviews_last_hour() is not security definer'; bad := bad + 1; end if;
  if to_regprocedure('public.reviews_explain_refusal()') is not null
     and not (select prosecdef from pg_proc where oid = 'public.reviews_explain_refusal()'::regprocedure) then
    raise warning 'reviews_explain_refusal() is still security invoker'; bad := bad + 1; end if;
  if bad > 0 then
    raise exception '% problem(s) above — nothing was committed', bad;
  end if;
  raise notice 'reviews: students can post again; the hourly cap is counted without exposing user_id';
end $$;

commit;
