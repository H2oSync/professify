-- =============================================================================================
-- TermChamp — RUN 17: your registration day (2026-10-11)
-- Run this in the Supabase SQL editor. One transaction, safe to run twice, drops nothing.
--
-- WHY
-- Tate, 2026-10-11: "people have different registration days so have them be able to upload their
-- registration day and maybe even display it to friends … something like 10 days until registration
-- plan out your perfect schedule", then "the time is fine to share too". The phone app's Planner now
-- counts down to the day you add, and shows which friends register before you, the same day, or after.
--
-- WHAT IT ADDS
-- 1. public.registration_days — one row per student per term: the day, the time (optional), and whether
--    friends can see it (on by default, like Plans). Only you can read or change your row.
-- 2. public.friend_registration_days(p_term) — SECURITY DEFINER. Returns day and time for:
--      · your ACCEPTED friends only,
--      · at your own school (a friendship from before the school wall still stops at the wall),
--      · who left "Friends can see your day" on,
--      · never anyone you blocked or who blocked you.
--      · never an account waiting to be deleted (when the 30-day delete, RUN 7, is in).
--    Nothing else: no names (the app already has them), no other terms, never your own row.
--
-- Until this runs, the app keeps the day on the phone and sends it up once it can; friends' days
-- don't show.
--
-- Check after (both read-only):
--   select count(*) from pg_policies where tablename = 'registration_days';            -- 4
--   select prosecdef from pg_proc where proname = 'friend_registration_days';           -- true
-- =============================================================================================
begin;

create table if not exists public.registration_days (
  user_id    uuid        not null references auth.users(id) on delete cascade,
  term       text        not null,
  day        date        not null,
  at_time    time,
  shared     boolean     not null default true,
  updated_at timestamptz not null default now(),
  primary key (user_id, term),
  constraint registration_days_term_ok check (term ~ '^[0-9]{4}$'),
  constraint registration_days_day_ok  check (day between date '2026-01-01' and date '2100-12-31'),
  constraint registration_days_time_ok check (at_time is null or extract(second from at_time) = 0)
);
alter table public.registration_days enable row level security;

-- updated_at is the server's clock, never the phone's (the app compares it with a change it kept offline)
create or replace function public.registration_days_stamp() returns trigger language plpgsql set search_path = public as $$
begin new.updated_at := now(); return new; end $$;
revoke all on function public.registration_days_stamp() from public, anon, authenticated;
drop trigger if exists registration_days_stamp on public.registration_days;
create trigger registration_days_stamp before insert or update on public.registration_days for each row execute function public.registration_days_stamp();

drop policy if exists registration_days_own_select on public.registration_days;
drop policy if exists registration_days_own_insert on public.registration_days;
drop policy if exists registration_days_own_update on public.registration_days;
drop policy if exists registration_days_own_delete on public.registration_days;
create policy registration_days_own_select on public.registration_days for select to authenticated using (user_id = auth.uid());
-- one row per term; 20 terms is more than anyone's whole time here
create policy registration_days_own_insert on public.registration_days for insert to authenticated
  with check (user_id = auth.uid() and (select count(*) from public.registration_days r where r.user_id = auth.uid()) < 20);
create policy registration_days_own_update on public.registration_days for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy registration_days_own_delete on public.registration_days for delete to authenticated using (user_id = auth.uid());

-- Supabase's default privileges give anon and authenticated everything on a new table: take it all back,
-- then grant only what the phone uses
revoke all on public.registration_days from public, anon, authenticated;
grant select, insert, update, delete on public.registration_days to authenticated;

-- The function. With RUN 7 (the 30-day delete) in, it goes in the way RUN 7 wraps every function that
-- returns people: the body as friend_registration_days__incl_pending, closed to students, and a filter
-- called friend_registration_days in front that hides accounts waiting to be deleted. Without RUN 7 it
-- is friend_registration_days itself, and RUN 7 wraps it when it runs (it is on RUN 7's list).
do $do$
declare
  body text := $body$
with me as (select auth.uid() as uid)
select r.user_id, r.day, r.at_time
from public.registration_days r, me m
where m.uid is not null
  and r.term = p_term
  and r.shared
  and r.user_id <> m.uid
  -- your accepted friends only
  and exists (select 1 from public.friend_requests f
              where f.status = 'accepted'
                and ((f.from_user = m.uid and f.to_user = r.user_id)
                  or (f.to_user = m.uid and f.from_user = r.user_id)))
  -- at your own school
  and exists (select 1 from public.profiles p, public.profiles q
              where p.id = r.user_id and q.id = m.uid and p.school = q.school)
  -- nobody you blocked and nobody who blocked you
  and not exists (select 1 from public.blocks b
                  where (b.blocker = m.uid and b.blocked = r.user_id)
                     or (b.blocker = r.user_id and b.blocked = m.uid))
order by r.day, r.at_time nulls last
limit 500;
$body$;
  pend boolean := to_regprocedure('public.is_pending_deletion(uuid)') is not null;
  wrapped boolean := to_regprocedure('public.friend_registration_days__incl_pending(text)') is not null;
begin
  if pend and not wrapped and to_regprocedure('public.friend_registration_days(text)') is not null then
    alter function public.friend_registration_days(text) rename to friend_registration_days__incl_pending;
    wrapped := true;
  end if;
  execute format($f$create or replace function public.%I(p_term text)
returns table (user_id uuid, day date, at_time time)
language sql security definer stable set search_path = public
as %L$f$, case when pend or wrapped then 'friend_registration_days__incl_pending' else 'friend_registration_days' end, body);
  if pend or wrapped then
    create or replace function public.friend_registration_days(p_term text)
    returns table (user_id uuid, day date, at_time time)
    language sql stable security definer set search_path = public
    as $w$ select x.* from public.friend_registration_days__incl_pending(p_term) x where not public.is_pending_deletion(x.user_id) $w$;
    revoke all on function public.friend_registration_days__incl_pending(text) from public, anon, authenticated;
  end if;
end $do$;

revoke all on function public.friend_registration_days(text) from public;
revoke execute on function public.friend_registration_days(text) from anon;
grant execute on function public.friend_registration_days(text) to authenticated;

do $$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'registration_days') <> 4 then
    raise exception 'registration_days: expected 4 policies';
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.registration_days'::regclass) then
    raise exception 'registration_days: row level security is off';
  end if;
  if has_table_privilege('anon', 'public.registration_days', 'select') or has_table_privilege('anon', 'public.registration_days', 'insert') then
    raise exception 'registration_days: anon can reach it';
  end if;
  if (select column_default from information_schema.columns
       where table_schema = 'public' and table_name = 'registration_days' and column_name = 'shared') is distinct from 'true' then
    raise exception 'registration_days: shared must default to true (like Plans)';
  end if;
  if not (select bool_and(prosecdef) from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname like 'friend\_registration\_days%') then
    raise exception 'friend_registration_days: must be SECURITY DEFINER';
  end if;
  if has_function_privilege('anon', 'public.friend_registration_days(text)', 'execute') then
    raise exception 'friend_registration_days: anon can call it';
  end if;
  if to_regprocedure('public.is_pending_deletion(uuid)') is not null then
    if (select p.prosrc from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = 'friend_registration_days') not like '%is_pending_deletion%' then
      raise exception 'friend_registration_days: accounts waiting to be deleted are not hidden';
    end if;
    if has_function_privilege('authenticated', 'public.friend_registration_days__incl_pending(text)', 'execute') then
      raise exception 'students can call friend_registration_days__incl_pending directly';
    end if;
  end if;
end $$;

commit;
