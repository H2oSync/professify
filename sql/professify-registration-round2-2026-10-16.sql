-- =============================================================================================
-- TermChamp — your Round 2 registration day (2026-10-16)
-- Run this in the Supabase SQL editor, AFTER RUN 17 (professify-registration-days.sql).
-- One transaction, safe to run twice, drops nothing, changes nothing that exists.
--
-- WHY
-- The website's registration timeline (Home) has "Your Round 1" and "Your Round 2". Round 1 is the
-- registration_days row the phone already reads and writes; that table keeps ONE row per student per
-- term (primary key user_id, term) and "day" is NOT NULL, so Round 2 cannot be a second row there, and a
-- new column on it could not exist without a Round 1 day. Round 2 therefore gets its own small table.
-- registration_days, friend_registration_days() and everything the iPhone app calls are not touched:
-- the app keeps reading and writing exactly what it reads and writes today.
--
-- WHAT IT ADDS
-- 1. public.registration_round2 — one row per student per term: the day, the time (optional, yours only), and "shared"
--    (the Round 2 editor's "Friends can see your day" switch, which also moves Round 1's switch with it).
--    Only you can read or change your row (same four policies as registration_days).
-- 2. public.friend_registration_round2(p_term) — SECURITY DEFINER. Returns user_id and DAY ONLY (never the
--    time) for:
--      · your ACCEPTED friends only,
--      · at your own school,
--      · who left "Friends can see your day" on: registration_round2.shared AND Round 1's registration_days.shared
--        (someone with no Round 1 row has not turned that one off, so it counts as on). Someone with ONLY a Round 2
--        day can therefore opt out from the Round 2 editor; the website keeps the two switches together,
--      · never anyone you blocked or who blocked you,
--      · never an account waiting to be deleted (when RUN 7 is in; if RUN 7 is run LATER, run this file again).
--
-- Until this runs the website keeps Round 2 on the device and sends it up once the table is there;
-- friends' Round 2 days simply don't show.
--
-- Check after (both read-only):
--   select count(*) from pg_policies where tablename = 'registration_round2';          -- 4
--   select prosecdef from pg_proc where proname = 'friend_registration_round2';         -- true
-- =============================================================================================
begin;
set local lock_timeout = '5s';   -- fail fast instead of queueing behind a long-running query

do $$
begin
  if to_regclass('public.registration_days') is null then
    raise exception 'Run RUN 17 (professify-registration-days.sql) first: registration_days is not there';
  end if;
end $$;

create table if not exists public.registration_round2 (
  user_id    uuid        not null references auth.users(id) on delete cascade,
  term       text        not null,
  day        date        not null,
  at_time    time,
  shared     boolean     not null default true,
  updated_at timestamptz not null default now(),
  primary key (user_id, term),
  constraint registration_round2_term_ok check (term ~ '^[0-9]{4}$'),
  constraint registration_round2_day_ok  check (day between date '2026-01-01' and date '2100-12-31'),
  constraint registration_round2_time_ok check (at_time is null or extract(second from at_time) = 0)
);
alter table public.registration_round2 add column if not exists shared boolean not null default true;   -- (a run of an earlier copy of this file)
alter table public.registration_round2 enable row level security;

-- updated_at is the server's clock, never the browser's (the website compares it with a change it kept offline)
create or replace function public.registration_round2_stamp() returns trigger language plpgsql set search_path = public as $$
begin new.updated_at := now(); return new; end $$;
revoke all on function public.registration_round2_stamp() from public, anon, authenticated;
drop trigger if exists registration_round2_stamp on public.registration_round2;
create trigger registration_round2_stamp before insert or update on public.registration_round2 for each row execute function public.registration_round2_stamp();

drop policy if exists registration_round2_own_select on public.registration_round2;
drop policy if exists registration_round2_own_insert on public.registration_round2;
drop policy if exists registration_round2_own_update on public.registration_round2;
drop policy if exists registration_round2_own_delete on public.registration_round2;
create policy registration_round2_own_select on public.registration_round2 for select to authenticated using (user_id = auth.uid());
-- one row per term; 20 terms is more than anyone's whole time here
create policy registration_round2_own_insert on public.registration_round2 for insert to authenticated
  with check (user_id = auth.uid() and (select count(*) from public.registration_round2 r where r.user_id = auth.uid()) < 20);
create policy registration_round2_own_update on public.registration_round2 for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy registration_round2_own_delete on public.registration_round2 for delete to authenticated using (user_id = auth.uid());

-- Supabase's default privileges give anon and authenticated everything on a new table: take it all back,
-- then grant only what the website uses
revoke all on public.registration_round2 from public, anon, authenticated;
grant select, insert, update, delete on public.registration_round2 to authenticated;

-- The function. When RUN 7 (the 30-day delete) is in, accounts waiting to be deleted are filtered out here, in the body.
do $do$
declare
  pend boolean := to_regprocedure('public.is_pending_deletion(uuid)') is not null;
  body text := $body$
with me as (select auth.uid() as uid)
select r.user_id, r.day
from public.registration_round2 r, me m
where m.uid is not null
  and r.term = p_term
  and r.user_id <> m.uid
  -- "Friends can see your day": this row's switch, and Round 1's too; no Round 1 row means that one was never switched off
  and r.shared
  and coalesce((select d.shared from public.registration_days d where d.user_id = r.user_id and d.term = r.term), true)
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
  __PENDING__
order by r.day
limit 500;
$body$;
begin
  body := replace(body, '__PENDING__', case when pend then 'and not public.is_pending_deletion(r.user_id)' else '' end);
  execute format($f$create or replace function public.friend_registration_round2(p_term text)
returns table (user_id uuid, day date)
language sql security definer stable set search_path = public
as %L$f$, body);
end $do$;

revoke all on function public.friend_registration_round2(text) from public;
revoke execute on function public.friend_registration_round2(text) from anon;
grant execute on function public.friend_registration_round2(text) to authenticated;

do $$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'registration_round2') <> 4 then
    raise exception 'registration_round2: expected 4 policies';
  end if;
  if not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'registration_round2' and column_name = 'shared') then
    raise exception 'registration_round2: the shared column is missing';
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.registration_round2'::regclass) then
    raise exception 'registration_round2: row level security is off';
  end if;
  if has_table_privilege('anon', 'public.registration_round2', 'select') or has_table_privilege('anon', 'public.registration_round2', 'insert') then
    raise exception 'registration_round2: anon can reach it';
  end if;
  if not (select prosecdef from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = 'friend_registration_round2') then
    raise exception 'friend_registration_round2: must be SECURITY DEFINER';
  end if;
  if has_function_privilege('anon', 'public.friend_registration_round2(text)', 'execute') then
    raise exception 'friend_registration_round2: anon can call it';
  end if;
  if to_regprocedure('public.is_pending_deletion(uuid)') is not null
     and (select p.prosrc from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = 'friend_registration_round2') not like '%is_pending_deletion%' then
    raise exception 'friend_registration_round2: accounts waiting to be deleted are not hidden';
  end if;
end $$;

commit;
