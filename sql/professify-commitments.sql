-- =============================================================================================
-- TermChamp — RUN 18: work & activities (2026-10-11)
-- Run this in the Supabase SQL editor. One transaction, safe to run twice, drops nothing.
--
-- WHY
-- Tate, 2026-10-11: "put in place a simple way to log Work and Extra curriculars like sports practice … so it can
-- also be shown on schedules … before you make a schedule so you could base your classes around this". The phone
-- app's Builder now asks about work, practice, a club or anything else every week before it drafts Plans A, B and
-- C; each one shows on My Classes, every plan and Home, and the Builder never puts a class over one.
--
-- WHAT IT ADDS
-- 1. public.commitments — one row per thing a student does every week: the kind (work, practice, club, other), a
--    name only they see, the days (letters of MTWRFSU), start and end (minutes after midnight) and whether friends
--    see it as Busy (on by default). Only you can read or change your rows.
-- 2. public.friend_busy_blocks() — SECURITY DEFINER. Returns only days, start and end (never the kind or name) for:
--      · your ACCEPTED friends only, at your own school,
--      · items they left "Friends see you're busy" on,
--      · never anyone you blocked or who blocked you,
--      · never an account waiting to be deleted (when the 30-day delete, RUN 7, is in).
--
-- Until this runs, the app keeps them on the phone and sends them up the first time the table answers; friends'
-- Busy times don't show.
--
-- Check after (both read-only):
--   select count(*) from pg_policies where tablename = 'commitments';                 -- 4
--   select prosecdef from pg_proc where proname = 'friend_busy_blocks';                -- true
-- =============================================================================================
begin;

create table if not exists public.commitments (
  id         uuid        primary key,
  user_id    uuid        not null references auth.users(id) on delete cascade,
  kind       text        not null default 'other',
  name       text,
  days       text        not null,
  start_min  smallint    not null,
  end_min    smallint    not null,
  busy       boolean     not null default true,
  updated_at timestamptz not null default now(),
  constraint commitments_kind_ok  check (kind in ('work', 'practice', 'club', 'other')),
  constraint commitments_name_ok  check (name is null or char_length(name) <= 40),
  constraint commitments_days_ok  check (days ~ '^[MTWRFSU]{1,7}$'),
  constraint commitments_time_ok  check (start_min >= 0 and end_min <= 1440 and start_min < end_min)
);
create index if not exists commitments_user on public.commitments (user_id);
alter table public.commitments enable row level security;

create or replace function public.commitments_stamp() returns trigger language plpgsql set search_path = public as $$
begin new.updated_at := now(); return new; end $$;
revoke all on function public.commitments_stamp() from public, anon, authenticated;
drop trigger if exists commitments_stamp on public.commitments;
create trigger commitments_stamp before insert or update on public.commitments for each row execute function public.commitments_stamp();

drop policy if exists commitments_own_select on public.commitments;
drop policy if exists commitments_own_insert on public.commitments;
drop policy if exists commitments_own_update on public.commitments;
drop policy if exists commitments_own_delete on public.commitments;
create policy commitments_own_select on public.commitments for select to authenticated using (user_id = auth.uid());
-- 30 is more than anyone's week
create policy commitments_own_insert on public.commitments for insert to authenticated
  with check (user_id = auth.uid() and (select count(*) from public.commitments c where c.user_id = auth.uid()) < 30);
create policy commitments_own_update on public.commitments for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy commitments_own_delete on public.commitments for delete to authenticated using (user_id = auth.uid());

revoke all on public.commitments from public, anon, authenticated;
grant select, insert, update, delete on public.commitments to authenticated;

-- The function, wrapped the way RUN 7 wraps every function that returns people (see RUN 17).
do $do$
declare
  body text := $body$
with me as (select auth.uid() as uid)
select c.user_id, c.days, c.start_min, c.end_min
from public.commitments c, me m
where m.uid is not null
  and c.busy
  and c.user_id <> m.uid
  and exists (select 1 from public.friend_requests f
              where f.status = 'accepted'
                and ((f.from_user = m.uid and f.to_user = c.user_id)
                  or (f.to_user = m.uid and f.from_user = c.user_id)))
  and exists (select 1 from public.profiles p, public.profiles q
              where p.id = c.user_id and q.id = m.uid and p.school = q.school)
  and not exists (select 1 from public.blocks b
                  where (b.blocker = m.uid and b.blocked = c.user_id)
                     or (b.blocker = c.user_id and b.blocked = m.uid))
order by c.user_id, c.start_min
limit 2000;
$body$;
  pend boolean := to_regprocedure('public.is_pending_deletion(uuid)') is not null;
  wrapped boolean := to_regprocedure('public.friend_busy_blocks__incl_pending()') is not null;
begin
  if pend and not wrapped and to_regprocedure('public.friend_busy_blocks()') is not null then
    alter function public.friend_busy_blocks() rename to friend_busy_blocks__incl_pending;
    wrapped := true;
  end if;
  execute format($f$create or replace function public.%I()
returns table (user_id uuid, days text, start_min smallint, end_min smallint)
language sql security definer stable set search_path = public
as %L$f$, case when pend or wrapped then 'friend_busy_blocks__incl_pending' else 'friend_busy_blocks' end, body);
  if pend or wrapped then
    create or replace function public.friend_busy_blocks()
    returns table (user_id uuid, days text, start_min smallint, end_min smallint)
    language sql stable security definer set search_path = public
    as $w$ select x.* from public.friend_busy_blocks__incl_pending() x where not public.is_pending_deletion(x.user_id) $w$;
    revoke all on function public.friend_busy_blocks__incl_pending() from public, anon, authenticated;
  end if;
end $do$;

revoke all on function public.friend_busy_blocks() from public;
revoke execute on function public.friend_busy_blocks() from anon;
grant execute on function public.friend_busy_blocks() to authenticated;

do $$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'commitments') <> 4 then
    raise exception 'commitments: expected 4 policies';
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.commitments'::regclass) then
    raise exception 'commitments: row level security is off';
  end if;
  if has_table_privilege('anon', 'public.commitments', 'select') or has_table_privilege('anon', 'public.commitments', 'insert') then
    raise exception 'commitments: anon can reach it';
  end if;
  if (select column_default from information_schema.columns
       where table_schema = 'public' and table_name = 'commitments' and column_name = 'busy') is distinct from 'true' then
    raise exception 'commitments: busy must default to true';
  end if;
  if not (select bool_and(prosecdef) from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname like 'friend\_busy\_blocks%') then
    raise exception 'friend_busy_blocks: must be SECURITY DEFINER';
  end if;
  if has_function_privilege('anon', 'public.friend_busy_blocks()', 'execute') then
    raise exception 'friend_busy_blocks: anon can call it';
  end if;
  if to_regprocedure('public.is_pending_deletion(uuid)') is not null then
    if (select p.prosrc from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = 'friend_busy_blocks') not like '%is_pending_deletion%' then
      raise exception 'friend_busy_blocks: accounts waiting to be deleted are not hidden';
    end if;
    if has_function_privilege('authenticated', 'public.friend_busy_blocks__incl_pending()', 'execute') then
      raise exception 'students can call friend_busy_blocks__incl_pending directly';
    end if;
  end if;
end $$;

commit;
