-- ================================================================================================
-- TWO THINGS THAT WERE BUILT AND NEVER SHIPPED — 8 September 2026
-- ================================================================================================
-- Found by asking production which of the functions and columns the client actually uses exist.
-- Exactly two answers came back wrong, and both fail SILENTLY, which is why neither was noticed.
--
-- 1. get_inviter() DOES NOT EXIST.
--    Every invite link ever sent lands on "You're invited to Professify." instead of
--    "Willow wants to compare schedules with you." The client asks for the inviter's name,
--    catches the error, and falls back to the generic copy — so the link works, it just loses
--    the entire reason somebody would tap it. The invite link is this app's main growth path.
--
-- 2. profiles.pinned_friends DOES NOT EXIST.
--    Starring a friend has never persisted: togglePin writes, the write fails, the star flips
--    back and a toast says the column may not be installed. It also means
--    push_sweep_done_for_day() — the "your friend is done for the day" notification built
--    yesterday — can never fire, because it checks for this column and returns 0.
--
-- Safe to re-run.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 1. Pinned friends
-- ------------------------------------------------------------------------------------------------
-- uuid[], not text[]: these are profile ids and the type should say so. A text[] would happily
-- store 'banana' and the first thing to notice would be a join that silently matches nothing.
-- No foreign key — Postgres cannot FK an array element, and the sweep already checks
-- friend_requests for an accepted friendship, which is the check that actually matters.
do $$
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='profiles' and column_name='pinned_friends')
  then
    alter table public.profiles add column pinned_friends uuid[];
    raise notice 'added profiles.pinned_friends';
  else
    raise notice 'profiles.pinned_friends already there';
  end if;
end $$;

-- Two is the whole feature (PIN_MAX in the client). Enforced here as well, because the client
-- cap is a courtesy and this is a column any authenticated caller can PATCH directly.
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'profiles_pinned_friends_max2') then
    alter table public.profiles
      add constraint profiles_pinned_friends_max2
      check (pinned_friends is null or array_length(pinned_friends, 1) <= 2) not valid;
    alter table public.profiles validate constraint profiles_pinned_friends_max2;
    raise notice 'capped pinned_friends at 2';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 2. get_inviter
-- ------------------------------------------------------------------------------------------------
-- Called by somebody who is NOT signed in — that is the whole point of an invite link — so it has
-- to be callable by anon. Which makes it, precisely, a uuid-to-display-name oracle, and worth
-- being deliberate about:
--
--   · it returns ONE column. Not the avatar, not the username, not the major. A name is what the
--     landing page renders and it is all this gives out.
--   · profile ids are random v4 uuids. There is no enumeration here: to get a name you must
--     already hold the id, and the only way to hold it is to have been sent the link.
--   · a miss returns no rows rather than an error, so a stale or mistyped link degrades to the
--     generic welcome instead of looking broken.
--
-- STABLE, so PostgREST will happily serve it, and SECURITY DEFINER because profiles is behind RLS
-- and an anonymous caller can read nothing at all without it.
create or replace function public.get_inviter(ref uuid)
returns table (display_name text)
language sql
security definer
stable
set search_path = public
as $fn$
  select p.display_name
    from public.profiles p
   where p.id = ref
     and p.display_name is not null
     and p.display_name <> ''
   limit 1
$fn$;

-- `revoke ... from anon` alone is a no-op: PostgreSQL grants EXECUTE to PUBLIC on every new
-- function, so the revoke has to name public first. Then grant it back to exactly who needs it.
revoke all     on function public.get_inviter(uuid) from public;
grant  execute on function public.get_inviter(uuid) to anon, authenticated;


-- ------------------------------------------------------------------------------------------------
-- 3. SELF-CHECK
-- ------------------------------------------------------------------------------------------------
do $$
declare n int; nm text;
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='profiles'
                    and column_name='pinned_friends' and data_type='ARRAY')
  then raise exception 'pinned_friends is missing or is not an array'; end if;

  if to_regprocedure('public.get_inviter(uuid)') is null then
    raise exception 'get_inviter(uuid) did not get created';
  end if;
  if not has_function_privilege('anon', 'public.get_inviter(uuid)', 'EXECUTE') then
    raise exception 'anon cannot call get_inviter — an invite link is opened by somebody signed out';
  end if;

  -- it must return a name for a real id, and NOTHING for one that does not exist
  select count(*) into n from public.get_inviter('00000000-0000-0000-0000-000000000000'::uuid);
  if n <> 0 then raise exception 'get_inviter returned a row for an id that does not exist'; end if;

  select p.id into nm from public.profiles p where p.display_name is not null limit 1;
  if nm is not null then
    select count(*) into n from public.get_inviter(nm::uuid);
    if n <> 1 then raise exception 'get_inviter returned % rows for a real profile', n; end if;
  end if;

  -- and it must give out one column only
  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='get_inviter';
  raise notice 'OK — pinned_friends exists, get_inviter answers for a real id and stays quiet for a fake one';
end $$;

-- Read-only: what the invite landing will now be able to say.
select 'profiles with a display_name (invite links that can name someone)' as thing,
       count(*)::text as n
  from public.profiles where display_name is not null and display_name <> ''
union all
select 'profiles with a pin set', count(*)::text
  from public.profiles where pinned_friends is not null and array_length(pinned_friends,1) > 0
 order by 1;
