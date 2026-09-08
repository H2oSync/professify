-- ================================================================================================
-- PROFESSIFY — WHAT IS ACTUALLY LIVE
-- Paste into the Supabase SQL editor. Read-only: nothing here changes anything.
-- ================================================================================================
-- The pre-launch audit could read your twelve migration files but not your database. Nine tables
-- the browser talks to appear in NO migration, so their RLS state is unknown — and the project has
-- already been bitten once by exactly this gap (professify-rls-hardening.sql records my_sections
-- being world-readable through "two rounds of correct SQL", because a policy nobody wrote down was
-- assumed to exist).
--
-- These eight queries replace assumption with fact. Run them in order and paste the output back.
-- ================================================================================================

-- 1. WHICH TABLES HAVE RLS OFF. Anything listed here is fully readable and writable by anyone
--    holding the publishable key. This is the only query that can be a launch blocker on its own.
select c.relname as table_name,
       c.relrowsecurity  as rls_enabled,
       c.relforcerowsecurity as rls_forced,
       (select count(*) from pg_policies p where p.schemaname='public' and p.tablename=c.relname) as policies
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind='r'
order by c.relrowsecurity asc, policies asc, c.relname;

-- 2. EVERY POLICY, IN FULL. Read the `qual` (USING) and `with_check` columns literally.
--    Look for: `true` on its own; any UPDATE row with a null with_check; any policy whose roles
--    column contains {public} or {anon} on a table holding personal data.
select tablename, policyname, permissive, roles, cmd, qual, with_check
from pg_policies where schemaname='public'
order by tablename, cmd, policyname;

-- 3. TABLE PRIVILEGES HELD BY anon AND authenticated. A policy that fails closed still leaves the
--    grant standing, and a grant that should not exist is a finding by itself.
select table_name, grantee, string_agg(privilege_type, ', ' order by privilege_type) as privs
from information_schema.role_table_grants
where table_schema='public' and grantee in ('anon','authenticated','PUBLIC')
group by table_name, grantee order by table_name, grantee;

-- 4. COLUMN-LEVEL PRIVILEGES. After professify-lockdown.sql, `edu_email` and `phone_hash` must NOT
--    appear here for `authenticated`. Before it, they almost certainly do — via the table grant.
select table_name, column_name, grantee, privilege_type
from information_schema.column_privileges
where table_schema='public' and table_name='profiles' and grantee in ('anon','authenticated')
order by column_name, grantee;

-- 5. WHAT IS ACTUALLY IN profiles. The audit could not establish the column list from migrations;
--    phone_hash appears in none of them but is written by the browser.
select column_name, data_type, is_nullable
from information_schema.columns
where table_schema='public' and table_name='profiles' order by ordinal_position;

-- 6. EVERY FUNCTION anon OR authenticated CAN EXECUTE, with its security mode and search_path.
--    `security definer` + `config` null (no search_path) is a privilege-escalation shape.
--    Four functions the app calls are defined in no migration — search_people,
--    find_profile_by_handle, get_inviter, suggest_classmates. Their definitions are here.
select p.proname,
       pg_get_function_identity_arguments(p.oid) as args,
       case when p.prosecdef then 'DEFINER' else 'invoker' end as security,
       p.proconfig as settings,
       has_function_privilege('anon',          p.oid, 'EXECUTE') as anon_can_run,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') as auth_can_run
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' order by anon_can_run desc, p.prosecdef desc, p.proname;

-- 6b. THE FOUR UNKNOWN FUNCTIONS, IN FULL. search_people is the one that matters most — the client
--     calls it the "name/email search", which implies it reads profiles.edu_email. If it RETURNS
--     that column it is a directory of every student's address, and no column revoke stops it,
--     because a SECURITY DEFINER function runs as its owner.
select p.proname, pg_get_functiondef(p.oid) as definition
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public'
  and p.proname in ('search_people','find_profile_by_handle','get_inviter','suggest_classmates');

-- 7. VIEWS. reviews_public must exist, must NOT contain user_id, and its security_invoker setting
--    decides whether it reads past RLS (it is supposed to: security_invoker = false).
select c.relname as view_name,
       (select string_agg(a.attname, ', ' order by a.attnum) from pg_attribute a
         where a.attrelid=c.oid and a.attnum>0 and not a.attisdropped) as columns,
       c.reloptions
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind='v';

-- 8. STORAGE. The avatars bucket appears in no migration at all.
--    public=true is fine for reading avatars; what must be true is that WRITE policies scope the
--    path to the uploader's own uid, or one student can overwrite another's photo.
select id, name, public, file_size_limit, allowed_mime_types from storage.buckets;
select policyname, cmd, roles, qual, with_check
from pg_policies where schemaname='storage' and tablename='objects' order by cmd, policyname;

-- 9. ORPHANS. Anything here is a table the browser can reach that nobody has thought about.
select c.relname
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind='r'
  and (has_table_privilege('anon',c.oid,'SELECT') or has_table_privilege('anon',c.oid,'INSERT'))
order by 1;
