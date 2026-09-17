-- ================================================================================================
-- A FRIEND'S SCHOOL EMAIL — 2026-09-11
-- ================================================================================================
-- Tate: "I want the ability once im friends with someone to see their school email so for projects
-- or various reasons id want to be able to contact them."
--
-- This existed once and was taken away on purpose. From the 2026-09-05 security audit, quoted in
-- the client where the code used to be:
--
--     "The comment above states the intent ('only on the rows of people you have BOTH accepted')
--      but the query did not implement it: otherIds is friends PLUS both directions of pending
--      requests, so sending someone a request was enough to fetch their Cal Poly address. It was
--      then dropped on the floor for non-friends, which is not a control — the row had already
--      crossed the wire."
--
-- So professify-lockdown.sql revoked SELECT on profiles.edu_email from authenticated and anon, at
-- the COLUMN level, which no policy and no crafted select list can get around. That revoke stays.
-- Nothing in this file re-grants it.
--
-- What changes is who decides. The client used to ask for a column and then decide what to keep.
-- Now it asks a question — "which of these people are my friends, and what are their addresses" —
-- and the DATABASE decides, so an address only ever leaves the server for someone this student has
-- an accepted friendship with. Send a request and it is not enough. Receive one and it is not
-- enough. Both sides, accepted.
--
-- Run AFTER professify-lockdown.sql. Safe to re-run.
-- ================================================================================================

-- ------------------------------------------------------------------------------------------------
-- friend_emails(ids) — SECURITY DEFINER, which is the whole point and also the whole risk
-- ------------------------------------------------------------------------------------------------
-- A definer function runs as its owner, so it can read the column the caller cannot. That is how
-- it works, and it is exactly the hole professify-schools.sql warns about ("a SECURITY DEFINER
-- function runs as its OWNER, so the edu_email column revoke does not constrain it"). Everything
-- below exists to make sure the only rows that come back are ones the caller is already entitled
-- to know about:
--
--   · the accepted-friendship test is the same predicate professify-friend-sections.sql uses to
--     gate my_sections — one shape for "is this person my friend", not a second opinion;
--   · the school test is belt and braces. You cannot become friends across campuses — the wall
--     refuses the request at INSERT — so an accepted friendship already implies the same school.
--     It is here anyway because this function is a hole in that wall by construction, and a hole
--     with two locks is the only kind worth cutting;
--   · a null auth.uid() matches nothing, so an anonymous call returns zero rows rather than
--     erroring in a way that tells the caller something;
--   · STABLE, not VOLATILE: it writes nothing.
do $$
declare school_clause text := '';
begin
  if exists (select 1 from information_schema.columns
             where table_schema='public' and table_name='profiles' and column_name='school') then
    /* `=`, NOT `is not distinct from`. Found in review, 2026-09-11: the first version matched
       two NULL schools as equal, so a row whose school had never been stamped — a partially
       migrated project, or a row written by the service role rather than through the app —
       matched anybody else's unstamped row and the address came back. Reproduced on a replica.
       Every other use of this wall in the codebase is plain equality against my_school(), which
       is false on NULL, and fail-closed is the only correct direction for a check whose whole
       job is to keep two campuses apart. */
    school_clause := $s$
      and p.school = (select me.school from public.profiles me where me.id = auth.uid())$s$;
  end if;

  execute format($fn$
    create or replace function public.friend_emails(p_ids uuid[] default null)
    returns table (id uuid, edu_email text)
    language sql
    security definer
    stable
    set search_path = public
    as $body$
      select p.id, p.edu_email
      from public.profiles p
      where auth.uid() is not null
        and p.id <> auth.uid()
        and p.edu_email is not null
        and (p_ids is null or p.id = any(p_ids))
        %s
        and exists (
          select 1 from public.friend_requests fr
          where fr.status = 'accepted'
            and ( (fr.from_user = auth.uid() and fr.to_user   = p.id)
               or (fr.to_user   = auth.uid() and fr.from_user = p.id) )
        )
    $body$;
  $fn$, school_clause);

  raise notice 'friend_emails(): installed (school check %)',
    case when school_clause = '' then 'not available on this project' else 'in' end;
end $$;

-- anon has no friendships, but saying so out loud is cheaper than assuming it.
revoke all on function public.friend_emails(uuid[]) from public, anon;
grant execute on function public.friend_emails(uuid[]) to authenticated;


-- ------------------------------------------------------------------------------------------------
-- The revoke this depends on is still in force
-- ------------------------------------------------------------------------------------------------
-- If someone ever re-grants the column, this function stops being the only way out and the audit
-- finding comes back. Fail loudly rather than quietly becoming decoration.
do $$
declare leaked text := '';
begin
  select string_agg(grantee, ', ') into leaked
  from information_schema.column_privileges
  where table_schema='public' and table_name='profiles' and column_name='edu_email'
    and privilege_type='SELECT' and grantee in ('authenticated','anon');

  if leaked is not null and leaked <> '' then
    raise warning 'profiles.edu_email is SELECTable by % — friend_emails() is not the only way out. Re-run professify-lockdown.sql.', leaked;
  else
    raise notice 'profiles.edu_email: still revoked — friend_emails() is the only path';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- VERIFY, as a real student
-- ------------------------------------------------------------------------------------------------
-- From the browser console on professify.app, signed in:
--
--     await sb.rpc('friend_emails')                 -- every friend's address
--     await sb.rpc('friend_emails',{p_ids:[id]})    -- just one
--     await sb.from('profiles').select('edu_email') -- must still fail: column privilege denied
--
-- Expected: the first two return only people you have BOTH accepted; the third is refused.
