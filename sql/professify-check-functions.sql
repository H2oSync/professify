-- ================================================================================================
-- WHAT DO THE FOUR UNDEFINED FUNCTIONS ACTUALLY RETURN? — paste into the SQL editor
-- ================================================================================================
-- search_people, find_profile_by_handle, get_inviter and suggest_classmates are called by the app
-- and defined in NONE of the migration files. search_people is the one that matters: the client
-- calls it "the name/email search" and reads p.edu_email off its results, which implies it both
-- queries and returns that column.
--
-- A SECURITY DEFINER function runs as its OWNER, so the edu_email column revoke does not constrain
-- it. If it returns that column, it is a directory of every student's Cal Poly address and the
-- lockdown has not closed the hole — it has closed the front door while this one stands open.
-- ================================================================================================

select p.proname,
       case when p.prosecdef then 'DEFINER (ignores column revokes)' else 'invoker' end as security,
       coalesce(array_to_string(p.proconfig,','),'!! NO search_path') as settings,
       has_function_privilege('anon', p.oid, 'EXECUTE')          as anon_can_run,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') as auth_can_run,
       coalesce(array_to_string(p.proargnames, ', '), '(scalar)') as args_and_returns
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in ('search_people','find_profile_by_handle','get_inviter','suggest_classmates')
order by p.proname;

-- If args_and_returns above contains edu_email or phone_hash, get the full body and send it to me:
-- select pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
--  where n.nspname='public' and p.proname='search_people';
