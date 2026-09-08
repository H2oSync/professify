-- ================================================================================================
-- THE SOCIAL GRAPH IS NOT A PUBLIC LOOKUP SERVICE — 2026-09-07
-- ================================================================================================
-- Four SECURITY DEFINER helpers answer questions about OTHER PEOPLE'S relationships, take both
-- parties as arguments, do no authorization of their own, and are granted to `authenticated`.
-- Supabase exposes every such function over REST at /rest/v1/rpc/<name> with the publishable key.
-- So today, any signed-in student can ask:
--
--     POST /rest/v1/rpc/are_friends   {"a":"<anyone>","b":"<anyone else>"}
--     POST /rest/v1/rpc/is_group_member {"g":"<any group>","u":"<anyone>"}
--
-- ...for pairs they have nothing to do with, one request at a time, and reconstruct the entire
-- friendship graph of the school. RLS does not help: these run as the owner precisely so the
-- policies that call them do not recurse, which also means they bypass every policy on
-- friend_requests, group_members and conversation_members.
--
-- THE FIX IS NOT TO REVOKE THEM. The policies genuinely need them. The fix is that a function
-- which answers "is X related to Y" must refuse unless the caller IS X or Y.
--
-- Verified before writing this: every one of the 14 call sites across five migrations passes
-- auth.uid() as one of the two arguments, and the browser never calls any of them by RPC. So the
-- guard changes no legitimate behaviour — it only closes the REST door.
--
--   is_friend_of(auth.uid(), user_id)          messaging §4a, safety §5
--   are_friends(auth.uid(), user_id)           groups §178-179
--   is_conv_member(conversation_id, auth.uid()) messaging ×4, rate-limits, safety
--   is_group_member(group_id, auth.uid())      groups ×6
--
-- RETURNS FALSE, DOES NOT RAISE. Two reasons. An exception inside an RLS policy aborts the whole
-- query, so a raise here would turn a future mistake into an outage. And false is the honest
-- answer to give a prober: it is indistinguishable from "no, they are not friends", so the caller
-- learns nothing about anyone but themselves either way.
--
-- Signatures are unchanged, so no policy has to be touched. Safe to re-run.
-- ================================================================================================

-- ------------------------------------------------------------------------------------------------
-- 1. is_friend_of(p_a, p_b) — either position is a legitimate caller
-- ------------------------------------------------------------------------------------------------
create or replace function public.is_friend_of(p_a uuid, p_b uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select auth.uid() is not null
     and auth.uid() in (p_a, p_b)          -- you may only ask about edges you are on
     and exists (
    select 1 from public.friend_requests fr
    where fr.status = 'accepted'
      and ((fr.from_user = p_a and fr.to_user = p_b) or (fr.to_user = p_a and fr.from_user = p_b))
  )
$$;

-- ------------------------------------------------------------------------------------------------
-- 2. are_friends(a, b) — the groups-era duplicate of the above, same rule
-- ------------------------------------------------------------------------------------------------
create or replace function public.are_friends(a uuid, b uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select auth.uid() is not null
     and auth.uid() in (a, b)
     and exists (
    select 1 from public.friend_requests r
    where r.status = 'accepted'
      and ((r.from_user = a and r.to_user = b)
        or (r.from_user = b and r.to_user = a))
  );
$$;

-- ------------------------------------------------------------------------------------------------
-- 3. is_conv_member(p_conv, p_user) — here the "who" argument is unambiguous
-- ------------------------------------------------------------------------------------------------
-- Exact equality rather than IN (…): p_conv is a conversation, not a person, so there is only one
-- position a caller can occupy. Asking whether SOMEONE ELSE is in a thread is a question this
-- function should never answer, even to a member of that thread — the member list is readable
-- through conversation_members' own policy, which is where that check belongs and is enforced.
create or replace function public.is_conv_member(p_conv uuid, p_user uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select auth.uid() is not null
     and p_user = auth.uid()
     and exists (
    select 1 from public.conversation_members m
    where m.conversation_id = p_conv and m.user_id = p_user
  )
$$;

-- ------------------------------------------------------------------------------------------------
-- 4. is_group_member(g, u) — same shape
-- ------------------------------------------------------------------------------------------------
create or replace function public.is_group_member(g uuid, u uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select auth.uid() is not null
     and u = auth.uid()
     and exists (
    select 1 from public.group_members m
    where m.group_id = g and m.user_id = u
  );
$$;

-- ------------------------------------------------------------------------------------------------
-- Grants. `revoke ... from anon` alone is a NO-OP: PostgreSQL grants EXECUTE on a new function to
-- PUBLIC automatically and anon is a member of PUBLIC, so the revoke has to name public.
-- (Verified live on this project 2026-08-28; review-integrity.sql still has the broken form.)
-- ------------------------------------------------------------------------------------------------
revoke all on function public.is_friend_of(uuid, uuid)    from public, anon;
revoke all on function public.are_friends(uuid, uuid)     from public, anon;
revoke all on function public.is_conv_member(uuid, uuid)  from public, anon;
revoke all on function public.is_group_member(uuid, uuid) from public, anon;
grant execute on function public.is_friend_of(uuid, uuid)    to authenticated;
grant execute on function public.are_friends(uuid, uuid)     to authenticated;
grant execute on function public.is_conv_member(uuid, uuid)  to authenticated;
grant execute on function public.is_group_member(uuid, uuid) to authenticated;


-- ------------------------------------------------------------------------------------------------
-- A FIFTH FUNCTION, WHICH NO MIGRATION IN THIS PROJECT MENTIONS — found live 2026-09-07
-- ------------------------------------------------------------------------------------------------
--   public.are_friends(target uuid)   SECURITY DEFINER, EXECUTE held by PUBLIC
--
-- It is an overload of are_friends, and unlike the two-argument one it was already written the
-- right way: it compares `target` against auth.uid() inside its own body, so it can only ever
-- answer about the caller, and a signed-out caller (auth.uid() = null) gets false. That is why it
-- is left alone rather than rewritten.
--
-- What it should not have is EXECUTE for PUBLIC. anon has no account and therefore no question to
-- ask here, and a function nobody signed-in-only can reach is one less thing to reason about the
-- next time somebody adds a policy. Guarded on the overload existing, because it is not in any
-- file and may not be on every deploy.
do $$
begin
  if exists (
    select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'are_friends'
       and pg_get_function_identity_arguments(p.oid) = 'target uuid')
  then
    execute 'revoke all on function public.are_friends(uuid) from public, anon';
    execute 'grant execute on function public.are_friends(uuid) to authenticated';
    raise notice 'are_friends(target uuid): EXECUTE narrowed to authenticated';
  else
    raise notice 'are_friends(target uuid): not on this deploy';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK — names any other SECURITY DEFINER function that takes a uuid argument, is callable
-- by `authenticated`, and never mentions auth.uid() in its body. Each one is a potential oracle of
-- the same shape: it answers a question about somebody using an id the caller supplies, with no
-- check that the caller is that somebody. Read-only; it changes nothing.
-- ------------------------------------------------------------------------------------------------
do $$
declare r record; n int := 0;
begin
  for r in
    select p.proname, pg_get_function_identity_arguments(p.oid) as args
      from pg_proc p
      join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public'
       and p.prosecdef                                     -- SECURITY DEFINER
       and pg_get_function_identity_arguments(p.oid) like '%uuid%'
       and p.prosrc not like '%auth.uid()%'
       and has_function_privilege('authenticated', p.oid, 'EXECUTE')
     order by 1
  loop
    n := n + 1;
    raise notice 'POSSIBLE ORACLE: public.%(%) — takes a uuid, never reads auth.uid()', r.proname, r.args;
  end loop;
  if n = 0 then
    raise notice 'OK — no SECURITY DEFINER function takes a caller-supplied uuid without checking auth.uid()';
  else
    raise notice '% function(s) above answer questions about an id the caller supplies. Check each one.', n;
  end if;
end $$;
