-- ================================================================================================
-- FIND PEOPLE — the phone's one Friends search: a name, an @username or a school email.  30 Sep 2026
-- ------------------------------------------------------------------------------------------------
-- Tate: "should we make it like instagram where the same search is for anyone — people who are your
--        current friends and people you haven't added yet — so it's all in one."
--
-- The phone's search box says "Find friends by name or @username". The desktop's two discovery RPCs
-- can't do the second half: search_people matches display_name or an exact school email, and
-- find_profile_by_handle matches the INSTAGRAM handle, not the TermChamp username everyone picks
-- at sign-up. So a student typing a classmate's @username found no one.
--
-- find_people is NEW and additive — search_people and find_profile_by_handle are untouched, so the
-- desktop keeps working exactly as it does. Until this file runs, the phone falls back to those two.
--
-- Same fences as every discovery RPC (professify-schools.sql):
--   · your own school only (the wall), never yourself, nothing when signed out;
--   · nobody you blocked and nobody who blocked you;
--   · 2+ characters, 20 rows at most;
--   · it returns id, display_name and username — nothing else. No photo, no major, no email, no
--     classes: a stranger's week is only ever visible after a mutual accept.
-- A leading "@" is a hint, not a requirement. The username match is a prefix ("tat" finds @tate);
-- the name match is a substring, as search_people's is. % and _ are escaped, so they match
-- themselves and not "anything".
--
-- Safe to run twice. Nothing is dropped.
-- ================================================================================================
begin;

create or replace function public.find_people(q text)
returns table(id uuid, display_name text, username text)
language sql
stable
security definer
set search_path = public
as $$
  with t as (
    select lower(btrim(coalesce(q, ''))) as s,
           replace(replace(replace(lower(regexp_replace(btrim(coalesce(q, '')), '^@', '')), '\', '\\'), '%', '\%'), '_', '\_') as h,
           replace(replace(replace(lower(btrim(coalesce(q, ''))), '\', '\\'), '%', '\%'), '_', '\_') as sl
  )
  select p.id, p.display_name, p.username
  from public.profiles p, t
  where length(t.s) >= 2
    and auth.uid() is not null
    and p.id <> auth.uid()
    and p.school = public.my_school()                                    -- the wall
    and not exists (select 1 from public.blocks b
                     where (b.blocker = auth.uid() and b.blocked = p.id)
                        or (b.blocker = p.id and b.blocked = auth.uid()))
    and (   lower(p.display_name) like '%' || t.sl || '%'
         or (length(t.h) >= 2 and lower(p.username) like t.h || '%')
         or lower(p.edu_email) = t.s)
  order by (lower(p.username) = lower(regexp_replace(t.s, '^@', ''))) desc,   -- an exact @username first
           (lower(p.edu_email) = t.s) desc,
           p.display_name asc
  limit 20;
$$;

revoke all on function public.find_people(text) from public, anon;
grant execute on function public.find_people(text) to authenticated;

-- Self-checks: raise (and roll back) if the function isn't what this file says it is.
do $$
declare f record;
begin
  select p.prosecdef, p.provolatile into f
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'find_people';
  if not found then raise exception 'find_people was not created'; end if;
  if not f.prosecdef then raise exception 'find_people must be SECURITY DEFINER'; end if;
  if has_function_privilege('anon', 'public.find_people(text)', 'execute') then raise exception 'anon can call find_people'; end if;
  if not has_function_privilege('authenticated', 'public.find_people(text)', 'execute') then raise exception 'authenticated cannot call find_people'; end if;
end $$;

commit;

-- Check it (read-only), signed in as yourself in the app, or here:
--   select * from public.find_people('ta');
