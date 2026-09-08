-- ================================================================================================
-- THE PHONE ORACLE — 2026-09-07
-- ================================================================================================
-- Found while capping column lengths, not while looking for it: profiles still has a phone_hash
-- column, two indexes on it, three rows with a value in it, and a SECURITY DEFINER function
--
--     find_profiles_by_phone_hashes(hashes text[])
--       ... where p.phone_hash = any(hashes) and p.id <> auth.uid()
--
-- that ANY signed-out visitor on the internet can call. It answers "which Professify accounts have
-- these phone numbers" for a batch of hashes at a time.
--
-- Why that is worse than it sounds: a SHA-256 of a phone number is not anonymised data. There are
-- only ~10^10 phone numbers, and far fewer once you fix an area code — the entire space can be
-- hashed and tried. So the function turns a phone number into a student's name, username and
-- avatar, and the column stores something recoverable back to a phone number. The app's own
-- Privacy Policy now says it keeps "no phone number, in any form."
--
-- The feature that fed this is gone: there is no phone field in the friend-add UI, nothing writes
-- professify_pending_phone, and hashPhone() has been deleted from the client. So nothing calls it.
--
-- WHAT THIS FILE DOES (all of it reversible, none of it a DROP):
--   1. revokes EXECUTE on the oracle from public, anon and authenticated  -> hole shut immediately
--   2. nulls the three stored hashes                                      -> policy becomes true
-- The DROPs — the function and the column — are at the bottom, commented out, for Tate to run.
-- Safe to re-run.
-- ================================================================================================

-- ------------------------------------------------------------------------------------------------
-- 1. Shut the oracle. Not a drop: a revoke, so it is one grant away from being undone if the
--    phone-matching feature ever comes back with a rate limit and a session requirement.
--    `from anon` alone is a no-op — PostgreSQL grants EXECUTE to PUBLIC on every new function, so
--    the revoke has to name public. This is the same mistake that left the other five oracles open.
-- ------------------------------------------------------------------------------------------------
do $$
declare f record; n int := 0;
begin
  for f in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public'
       and p.proname in ('find_profiles_by_phone_hashes','find_profiles_by_phone','match_phone_hashes')
  loop
    execute format('revoke all on function %s from public, anon, authenticated', f.sig);
    raise notice 'revoked %', f.sig;
    n := n + 1;
  end loop;
  if n = 0 then raise notice 'no phone-matching function on this deploy'; end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 2. Erase the stored hashes. This is the part that actually removes the personal data; the revoke
--    only stops the lookup. Nothing reads this column — my_private_profile() tests for it with
--    to_jsonb(p) ? 'phone_hash', which is false-not-error once the column is gone.
-- ------------------------------------------------------------------------------------------------
do $$
declare n bigint := 0;
begin
  if exists (select 1 from information_schema.columns
              where table_schema='public' and table_name='profiles' and column_name='phone_hash')
  then
    update public.profiles set phone_hash = null where phone_hash is not null;
    get diagnostics n = row_count;
    raise notice 'cleared phone_hash on % profile(s)', n;
  else
    raise notice 'profiles.phone_hash already gone';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 3. SELF-CHECK — read-only. Fails loudly if either half did not take.
-- ------------------------------------------------------------------------------------------------
do $$
declare bad int;
begin
  select count(*) into bad
    from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname='public' and p.proname like '%phone%'
     and (has_function_privilege('anon', p.oid, 'EXECUTE')
       or has_function_privilege('authenticated', p.oid, 'EXECUTE'));
  if bad > 0 then
    raise exception 'a phone-matching function is still callable by anon or authenticated';
  end if;

  if exists (select 1 from information_schema.columns
              where table_schema='public' and table_name='profiles' and column_name='phone_hash')
  then
    select count(*) into bad from public.profiles where phone_hash is not null;
    if bad > 0 then raise exception '% phone hash(es) still stored', bad; end if;
  end if;

  raise notice 'OK — no phone lookup is callable, and no phone hash is stored';
end $$;

-- ------------------------------------------------------------------------------------------------
-- 4. FOR TATE — the destructive half. Nothing above needs it; this is the cleanup that makes the
--    column and the function stop existing rather than merely stop working. Run it when you are
--    ready; my_private_profile() and the app both survive it, because neither names the column
--    statically. Drop the function first, then the indexes, then the column.
-- ------------------------------------------------------------------------------------------------
-- drop function if exists public.find_profiles_by_phone_hashes(text[]);
-- drop index  if exists public.profiles_phone_idx;
-- drop index  if exists public.profiles_phone_hash_idx;
-- alter table public.profiles drop column if exists phone_hash;
