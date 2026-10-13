-- =============================================================================================
-- TermChamp — RUN 16: friends_of() leaves out anyone blocked on either side
-- Written 2026-10-11. Run this in the Supabase SQL editor. Safe to run twice. Drops no data.
--
-- WHY
-- The phone app now shows who your friends are friends with (Tate, 2026-10-11: "lets bring back
-- the feature for the app that shows who your friends are friends with"), from friends_of() — the
-- function the website's Friends tab has used since 2026-09-02. That function never looked at
-- blocks. So if X blocked you but is still friends with Avery, X showed up in Avery's list with an
-- Add button that the database then refused — which tells you X blocked you. Everything else in
-- the app keeps that secret (find_people, suggestions, chats: "you cannot discover that somebody
-- blocked you").
--
-- WHAT CHANGES
-- Only the last WHERE: a person is left out when either of you has blocked the other. Same name,
-- same argument, same columns, same gate (you see a list only when you are that person's ACCEPTED
-- friend), same grants. The app needs no change to use it.
--
-- WITH THE 30-DAY DELETE (RUN 7, professify-delete-account-30-days.sql) — fixed 2026-10-11, build 10:30
-- RUN 7 renames friends_of to friends_of__incl_pending and puts a filter called friends_of in front of
-- it, so accounts waiting to be deleted are hidden. The first version of this file re-created
-- friends_of directly, which on a database with RUN 7 would have replaced that filter. This version
-- puts the new body where it belongs: into friends_of__incl_pending when RUN 7 is in, and puts the
-- filter back in front of it (so running it repairs the first version too); into friends_of when not.
-- Safe to run again, either way.
-- =============================================================================================
begin;

do $do$
declare
  body text := $body$
with me as (select auth.uid() as uid),
-- THE GATE: nothing at all unless the caller is an accepted friend of p_user.
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
where t.other <> (select uid from me)
  -- RUN 16: nobody you blocked and nobody who blocked you
  and not exists (select 1 from public.blocks b, me m
                  where (b.blocker = m.uid and b.blocked = t.other)
                     or (b.blocker = t.other and b.blocked = m.uid))
order by (t.other in (select other from mine)) desc, coalesce(p.display_name,'') asc;
$body$;
  wrapped boolean := to_regproc('public.friends_of__incl_pending') is not null;
  target text := case when to_regproc('public.friends_of__incl_pending') is not null then 'friends_of__incl_pending' else 'friends_of' end;
begin
  execute format($f$create or replace function public.%I(p_user uuid)
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
as %L$f$, target, body);
  if wrapped then
    -- RUN 7's filter in front: hides accounts waiting to be deleted (and the list of one)
    create or replace function public.friends_of(p_user uuid)
    returns table (id uuid, display_name text, username text, avatar_url text, mutual boolean)
    language sql stable security definer set search_path = public
    as $w$ select x.* from public.friends_of__incl_pending(p_user) x where not public.is_pending_deletion(x.id) and not public.is_pending_deletion(p_user) $w$;
    revoke all on function public.friends_of__incl_pending(uuid) from public, anon, authenticated;
  end if;
end $do$;

revoke all on function public.friends_of(uuid) from public;
revoke execute on function public.friends_of(uuid) from anon;
grant execute on function public.friends_of(uuid) to authenticated;

do $$
begin
  if position('public.blocks' in (select p.prosrc from pg_proc p join pg_namespace n on n.oid = p.pronamespace
       where n.nspname = 'public' and p.proname = case when to_regproc('public.friends_of__incl_pending') is not null then 'friends_of__incl_pending' else 'friends_of' end)) = 0 then
    raise exception 'friends_of: the blocks filter did not take';
  end if;
  if to_regproc('public.friends_of__incl_pending') is not null then
    if (select p.prosrc from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = 'friends_of') not like '%is_pending_deletion%' then
      raise exception 'friends_of: the 30-day-delete filter is missing';
    end if;
    if has_function_privilege('authenticated', 'public.friends_of__incl_pending(uuid)', 'execute') then
      raise exception 'students can call friends_of__incl_pending directly';
    end if;
  end if;
  if has_function_privilege('anon', 'public.friends_of(uuid)', 'execute') then
    raise exception 'friends_of: anon can call it';
  end if;
end $$;

commit;

-- Check (read-only): expect blocks_filtered = true on the function that holds the body.
select p.proname, p.prosecdef, position('public.blocks' in p.prosrc) > 0 as blocks_filtered, position('is_pending_deletion' in p.prosrc) > 0 as hides_deleting
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.proname in ('friends_of', 'friends_of__incl_pending');
