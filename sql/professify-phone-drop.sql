-- ================================================================================================
-- THE PHONE ORACLE — THE DESTRUCTIVE HALF — 2026-09-07
-- ================================================================================================
-- Run this in the Supabase SQL editor. It is separate from professify-phone-oracle.sql because it
-- is the only part that cannot be undone, and because Claude is not permitted to put a DROP
-- against production into the editor — that click is yours by design.
--
-- WHAT ALREADY HAPPENED (professify-phone-oracle.sql, run earlier today):
--   · EXECUTE on find_profiles_by_phone_hashes(text[]) revoked from public, anon, authenticated
--   · the three stored phone hashes set to NULL
-- So the hole is already shut and the personal data is already gone. This removes the OBJECTS, so
-- nobody can grant the function back by accident and no future column-level slip can re-expose
-- the hash.
--
-- WHY IT IS SAFE FOR THE APP: my_private_profile() tests for the column with
--     (to_jsonb(p) ? 'phone_hash')
-- which is FALSE, not an error, once the column no longer exists. Nothing else names it — the
-- client's hashPhone() was deleted and there is no phone field in the friend-add UI.
--
-- ------------------------------------------------------------------------------------------------
-- THE GUARD IS INSIDE THE DO BLOCK, AND THAT IS THE WHOLE POINT.
--
-- The first version of this file had the check in one statement and the DROPs as four statements
-- after it. That is not a guard. psql runs each statement in its own implicit transaction, so the
-- RAISE aborted the check and then cheerfully ran the drops anyway — proven on a local replica:
-- the guard printed "refusing to drop the column" and the column was gone one line later. The
-- Supabase editor happens to wrap a multi-statement script in one transaction, which would have
-- hidden it, and it would have stayed hidden until somebody ran the file through psql.
--
-- So the drops are EXECUTEd from inside the same block that does the counting. There is no
-- ordering to get wrong and no transaction semantics to depend on: the only path to a DROP runs
-- through the check.
-- ------------------------------------------------------------------------------------------------
-- Safe to re-run.
-- ================================================================================================

do $$
declare n bigint := 0;
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='profiles' and column_name='phone_hash')
  then
    -- column already gone; still clear up the function and indexes if a previous run stopped early
    execute 'drop function if exists public.find_profiles_by_phone_hashes(text[])';
    execute 'drop index if exists public.profiles_phone_idx';
    execute 'drop index if exists public.profiles_phone_hash_idx';
    raise notice 'phone_hash column was already gone — function and indexes cleared';
    return;
  end if;

  select count(*) into n from public.profiles where phone_hash is not null;
  if n > 0 then
    raise exception
      '% phone hash(es) are still stored — nothing has been dropped. Run professify-phone-oracle.sql first, then re-run this.', n;
  end if;

  raise notice 'checked: 0 hashes stored';

  -- Dependency order: the function that reads the column, then the indexes on it, then the column.
  execute 'drop function if exists public.find_profiles_by_phone_hashes(text[])';
  execute 'drop index if exists public.profiles_phone_idx';
  execute 'drop index if exists public.profiles_phone_hash_idx';
  execute 'alter table public.profiles drop column if exists phone_hash';
  raise notice 'dropped: function, 2 indexes, phone_hash column';
end $$;

-- ------------------------------------------------------------------------------------------------
-- Verification. Every number below should be 0 except the last, which is your profile count.
-- ------------------------------------------------------------------------------------------------
select 'phone functions remaining' as thing, count(*)::text as n
  from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
 where ns.nspname='public' and p.proname like '%phone%'
union all
select 'phone_hash column remaining', count(*)::text
  from information_schema.columns
 where table_schema='public' and table_name='profiles' and column_name='phone_hash'
union all
select 'phone indexes remaining', count(*)::text
  from pg_index i
 where i.indrelid = to_regclass('public.profiles')
   and pg_get_indexdef(i.indexrelid) ilike '%phone%'
union all
select 'profiles still readable (sanity)', count(*)::text from public.profiles
 order by 1;
