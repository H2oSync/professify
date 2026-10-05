-- TermChamp: no more delete-at-once (2026-10-04). RUN ONLY AFTER the website build with "30 days to
-- recover" (19:15 or later) is merged and live on termchamp.com.
--
-- delete_my_account() deletes an account immediately. Since 16:45 the phone, and since 19:15 the
-- website, ask for a deletion instead (request_account_deletion: hidden now, deleted after 30 days,
-- recoverable, with the two emails). But delete_my_account() was still callable by any signed-in
-- student, so an old tab of the website — or anyone calling it directly — skipped the 30 days, the
-- Recover screen and the emails. Run before the website is updated and its Delete button breaks.
--
-- The nightly purge still works: it calls delete_my_account_v2 → delete_my_account() as their owner
-- (both SECURITY DEFINER), which doesn't need the student's permission.
-- One transaction; self-checks raise. Safe to run twice.

begin;

revoke all on function public.delete_my_account() from public, anon, authenticated;

do $$ begin
  if has_function_privilege('authenticated', 'public.delete_my_account()', 'execute') then
    raise exception 'students can still delete at once';
  end if;
  if has_function_privilege('authenticated', 'public.delete_my_account_v2(boolean)', 'execute') then
    raise exception 'students can skip the 30 days through delete_my_account_v2';
  end if;
  if not has_function_privilege('authenticated', 'public.request_account_deletion(boolean)', 'execute') then
    raise exception 'students can''t ask for a deletion — run professify-delete-account-30-days.sql first';
  end if;
  if (select prosecdef from pg_proc where oid = 'public.delete_my_account_v2(boolean)'::regprocedure) is not true then
    raise exception 'delete_my_account_v2 is not SECURITY DEFINER, so the purge would lose access';
  end if;
end $$;

commit;
