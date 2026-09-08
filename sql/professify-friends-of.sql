-- =============================================================================================
-- Professify — "Friends" tab on a friend's profile
-- Written 2026-08-27 for Tate. Run this in the Supabase SQL editor.
--
-- WHAT THIS DOES
-- Lets you open a FRIEND's profile and see who they are friends with, and add those people
-- from there. (Tate, 2026-08-27: "next to their classes and already took have friends and
-- everyone a person is friends with you can see and then friend them from there.")
--
-- WHY IT IS A DATABASE FUNCTION
-- Same reason as suggest_friends: RLS on friend_requests lets a student read only their OWN
-- edges, which is correct and stays that way. Reading Sage's friend list means reading edges
-- that are not yours. That has to happen inside SECURITY DEFINER or not at all.
--
-- THE GATE — the important part of this file
-- You may only see the friend list of someone who has ACCEPTED YOU. If you are not their
-- accepted friend, this returns zero rows. Not an error, not a partial list — nothing. That
-- boundary is the same one the rest of the app already draws: a stranger's row in search is
-- not even clickable, because their week is not ours to show until they accept.
--
-- So the disclosure is: "a person you accepted as a friend can see who else you are friends
-- with." That is the ordinary social-graph bargain, and it is worth being deliberate that this
-- is what is being turned on — it is not reversible for edges that already exist, and there is
-- no per-user opt-out in this version. If you want one later, say so and I will add a
-- profiles.hide_friend_list column and honour it here.
--
-- Every statement is guarded. Nothing here drops a table.
-- =============================================================================================

-- Postgres will not let CREATE OR REPLACE change a function's OUT columns, so the exact
-- signature is dropped first. It drops a FUNCTION, not data — this one computes its answer
-- from friend_requests and profiles on every call and both are untouched. "if exists" makes it
-- a no-op on a database that never had one.
drop function if exists public.friends_of(uuid);

create or replace function public.friends_of(p_user uuid)
returns table (
  id           uuid,
  display_name text,
  username     text,
  avatar_url   text,
  mutual       boolean      -- already YOUR friend too
)
language sql
security definer
stable
set search_path = public
as $$
with me as (select auth.uid() as uid),
-- THE GATE. Everything below is inside this: if the caller is not an accepted friend of
-- p_user, `allowed` is empty, every join fails, and the function returns nothing at all.
allowed as (
  select 1
  from public.friend_requests r, me m
  where r.status='accepted'
    and m.uid is not null
    and p_user is not null
    and ((r.from_user=m.uid and r.to_user=p_user)
      or (r.from_user=p_user and r.to_user=m.uid))
),
theirs as (
  select distinct case when r.from_user=p_user then r.to_user else r.from_user end as other
  from public.friend_requests r
  where exists (select 1 from allowed)
    and r.status='accepted'
    and (r.from_user=p_user or r.to_user=p_user)
),
mine as (
  select case when r.from_user=m.uid then r.to_user else r.from_user end as other
  from public.friend_requests r, me m
  where r.status='accepted' and (r.from_user=m.uid or r.to_user=m.uid)
)
select p.id,
       coalesce(p.display_name,'Classmate') as display_name,
       p.username,
       p.avatar_url,
       (t.other in (select other from mine)) as mutual
from theirs t
join public.profiles p on p.id = t.other
-- The caller is excluded. This tab exists to find people you could add, and you are never one
-- of them; a row for yourself in that list is noise, not information.
where t.other <> (select uid from me)
order by (t.other in (select other from mine)) desc, coalesce(p.display_name,'') asc;
$$;

revoke all on function public.friends_of(uuid) from public;
grant execute on function public.friends_of(uuid) to authenticated;

-- =============================================================================================
-- AFTER RUNNING THIS
--
-- Test it from the APP, not from here — the SQL editor runs as the service role where
-- auth.uid() is null, so the gate correctly refuses and you'd see an empty result either way.
-- Open a friend's profile; the Friends tab appears only if the function answered.
--
-- To satisfy yourself the gate holds, check that the function is SECURITY DEFINER and that
-- nothing else got EXECUTE on it:
--
--   select p.prosecdef, p.proacl
--   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
--   where n.nspname='public' and p.proname='friends_of';
--
-- Expect prosecdef = true, and proacl granting EXECUTE to authenticated only.
-- =============================================================================================
