-- =================================================================================================
-- professify-plans.sql — 2026-09-25
-- Spring Plans A–C: the foundation for the registration game plan and backup sections.
-- Run once in Supabase → SQL Editor. One transaction, idempotent, safe to re-run. Nothing is dropped
-- except this file's own policies, by name, before they are recreated.
--
-- Needs, already live: friend_requests, profiles.school + my_school() + school_of() (schools.sql),
-- is_suspended() (safety.sql), watch_sections with its term column (term-scope.sql).
-- =================================================================================================
--
-- WHAT A PLAN IS. Up to three possible schedules per term — A, B, C — each a list of sections
-- (course code + class number). Every section in a plan is watched: the client keeps
-- watch_sections in step, so the seat-alert path does not change.
--
-- WHO SEES A PLAN (locked by Tate 2026-09-25):
--   · the owner: everything;
--   · an accepted friend at the same school: the plan, while its "Friends can see" toggle is on
--     (shared defaults to TRUE);
--   · anyone else: nothing — no policy grants it, and there is no public directory.
-- A plan is where someone intends to be at a given hour, which is location data (the Saturn
-- lesson), so it follows the same rule as a schedule. Blocking deletes the friendship
-- (block_user), and with it the read.
--
-- "N IN PLANS". plan_interest() counts distinct OTHER students at the caller's school with a section
-- in any plan or on their watchlist for that term. It returns counts only — never who — and only at
-- 3 or more. The caller is never counted: if they were, adding and removing their own watch would
-- tell them whether exactly two others had it (review, 2026-09-25). It runs as the owner because a student cannot
-- (and must not) read strangers' plans; the count is the whole of what crosses.
begin;

-- ------------------------------------------------------------------------------------------------
-- 1. The table
-- ------------------------------------------------------------------------------------------------
create table if not exists public.plans (
  id          bigint generated always as identity primary key,
  user_id     uuid        not null default auth.uid() references auth.users(id) on delete cascade,
  term        text        not null,
  slot        text        not null,
  sections    jsonb       not null default '[]'::jsonb,
  shared      boolean     not null default true,
  updated_at  timestamptz not null default now(),
  constraint plans_term_shape   check (term ~ '^[0-9]{4}$'),
  constraint plans_slot_abc     check (slot in ('A','B','C')),
  constraint plans_sections_arr check (jsonb_typeof(sections) = 'array' and jsonb_array_length(sections) <= 12),
  constraint plans_one_per_slot unique (user_id, term, slot)
);
create index if not exists plans_term_idx on public.plans (term);

-- ------------------------------------------------------------------------------------------------
-- 2. Every write is normalised and checked here, not in the client
-- ------------------------------------------------------------------------------------------------
-- · sections is rebuilt from {code, class_nbr} only, so nothing else a client sends is stored;
--   a malformed element or a repeated class number refuses the write rather than being dropped
--   (a plan that silently loses a class is worse than an error the app can show).
-- · a student writes only their own rows (the policy also says so) and cannot write while
--   suspended — friends read plans, so a plan is "something others see".
-- · at most 12 plans per account (four terms of A–C): the unique key caps a term, this caps terms.
-- · updated_at is the server's clock.
-- Author rules are scoped to current_user = 'authenticated' so the definer paths (account
-- deletion cascades, Tate in the SQL editor) are never frozen by them.
-- SECURITY INVOKER on purpose: inside a definer function current_user is the owner, so the
-- 'authenticated' test below would never be true and every author rule would silently vanish.
create or replace function public.plans_guard()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  el   jsonb;
  out_ jsonb := '[]'::jsonb;
  seen text[] := '{}';
  c    text;
  n    text;
begin
  if current_user = 'authenticated' then
    if auth.uid() is null or new.user_id is distinct from auth.uid() then
      raise exception 'plans: you can only save your own plans' using errcode = '42501';
    end if;
    if public.is_suspended(auth.uid()) then
      raise exception 'plans: this account cannot save plans right now' using errcode = '42501';
    end if;
    /* Counted WITHOUT the slot being written: an upsert into an existing slot fires this BEFORE
       INSERT trigger before ON CONFLICT turns it into an update, so counting that row too locked a
       full account out of editing its own plans (review, 2026-09-25). */
    if tg_op = 'INSERT' and (select count(*) from public.plans p
                              where p.user_id = new.user_id
                                and not (p.term = new.term and p.slot = new.slot)) >= 12 then
      raise exception 'plans: 12 plans is the most one account can keep' using errcode = '54000';
    end if;
  end if;

  if jsonb_typeof(new.sections) is distinct from 'array' then
    raise exception 'plans: sections must be a list' using errcode = '22023';
  end if;
  for el in select * from jsonb_array_elements(new.sections) loop
    if jsonb_typeof(el) <> 'object' then
      raise exception 'plans: each section must be {code, class_nbr}' using errcode = '22023';
    end if;
    c := upper(btrim(coalesce(el ->> 'code', '')));
    n := btrim(coalesce(el ->> 'class_nbr', ''));
    if c !~ '^[A-Z&]{2,6} [0-9]{3,4}[A-Z]{0,2}$' then
      raise exception 'plans: % is not a course code', left(c, 20) using errcode = '22023';
    end if;
    if n !~ '^[0-9]{3,6}$' then
      raise exception 'plans: % is not a class number', left(n, 20) using errcode = '22023';
    end if;
    if n = any(seen) then
      raise exception 'plans: class % is in this plan twice', n using errcode = '22023';
    end if;
    seen := seen || n;
    out_ := out_ || jsonb_build_array(jsonb_build_object('code', c, 'class_nbr', n));
  end loop;

  new.sections   := out_;
  new.updated_at := now();
  return new;
end;
$$;
revoke all on function public.plans_guard() from public, anon, authenticated;

drop trigger if exists plans_guard on public.plans;
create trigger plans_guard
  before insert or update on public.plans
  for each row execute function public.plans_guard();

-- ------------------------------------------------------------------------------------------------
-- 3. Row-level security
-- ------------------------------------------------------------------------------------------------
alter table public.plans enable row level security;
revoke all on public.plans from public, anon;
grant select, insert, update, delete on public.plans to authenticated;
-- identity column: no sequence grant is needed for GENERATED ALWAYS.

drop policy if exists "plans_own" on public.plans;
create policy "plans_own"
  on public.plans for all to authenticated
  using      ( user_id = auth.uid() )
  with check ( user_id = auth.uid() );

-- Friends read shared plans. The school test is a subquery on profiles evaluated as the reader
-- (profiles_read shows a student only their own campus), so it adds the wall without handing
-- the reader school_of(). Friend requests are already same-school only; this holds even for a
-- friendship that predates the wall.
drop policy if exists "plans_friends_read" on public.plans;
create policy "plans_friends_read"
  on public.plans for select to authenticated
  using (
    shared
    and user_id <> auth.uid()
    and exists (
      select 1 from public.friend_requests fr
       where fr.status = 'accepted'
         and ( (fr.from_user = auth.uid() and fr.to_user   = plans.user_id)
            or (fr.to_user   = auth.uid() and fr.from_user = plans.user_id) )
    )
    and exists (
      select 1 from public.profiles p
       where p.id = plans.user_id and p.school = public.my_school()
    )
  );

-- ------------------------------------------------------------------------------------------------
-- 4. "N in plans" — counts only, never who, only at 3 or more
-- ------------------------------------------------------------------------------------------------
-- Input: a term and up to 300 class numbers (a whole class page, or every section in a plan).
-- Output: one row per class number that at least 3 OTHER students at the caller's school have in a plan
-- or on their watchlist for that term. Anything below 3 is simply absent, so "absent" and "2"
-- are indistinguishable by design. Signed out → nothing.
create or replace function public.plan_interest(p_term text, p_class_nbrs text[])
returns table (class_nbr text, n integer)
language sql
stable
security definer
set search_path = public
as $$
  with me as (
    select public.school_of(auth.uid()) as school
     where auth.uid() is not null
       and p_term ~ '^[0-9]{4}$'
       and coalesce(cardinality(p_class_nbrs), 0) between 1 and 300
  ),
  wanted as (
    select distinct btrim(x) as class_nbr
      from unnest(p_class_nbrs) as x
     where btrim(x) ~ '^[0-9]{3,6}$'
  ),
  interest as (
    select p.user_id, e ->> 'class_nbr' as class_nbr
      from public.plans p
      cross join lateral jsonb_array_elements(p.sections) as e
     where p.term = p_term
    union
    select w.user_id, w.class_nbr::text
      from public.watch_sections w
     where w.term = p_term
  )
  select i.class_nbr, count(distinct i.user_id)::integer as n
    from interest i
    join wanted  on wanted.class_nbr = i.class_nbr
    join public.profiles pr on pr.id = i.user_id
    join me      on pr.school = me.school
   where i.user_id <> auth.uid()
   group by i.class_nbr
  having count(distinct i.user_id) >= 3
$$;
revoke all on function public.plan_interest(text, text[]) from public, anon;
grant execute on function public.plan_interest(text, text[]) to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 5. Self-checks — raise, so a half-applied file rolls back
-- ------------------------------------------------------------------------------------------------
do $$
declare
  pols text[];
begin
  if not (select relrowsecurity from pg_class where oid = 'public.plans'::regclass) then
    raise exception 'plans: row-level security is off';
  end if;
  select array_agg(policyname::text order by policyname) into pols
    from pg_policies where schemaname = 'public' and tablename = 'plans';
  if pols is distinct from array['plans_friends_read','plans_own'] then
    raise exception 'plans: expected exactly plans_friends_read and plans_own, found %', pols;
  end if;
  if has_table_privilege('anon', 'public.plans', 'select') then
    raise exception 'plans: anon can read plans';
  end if;
  if has_function_privilege('anon', 'public.plan_interest(text, text[])', 'execute') then
    raise exception 'plans: anon can call plan_interest';
  end if;
  if not exists (select 1 from pg_trigger where tgrelid = 'public.plans'::regclass and tgname = 'plans_guard') then
    raise exception 'plans: the guard trigger is missing';
  end if;
  if (select column_default from information_schema.columns
       where table_schema = 'public' and table_name = 'plans' and column_name = 'shared') is distinct from 'true' then
    raise exception 'plans: shared must default to true (Tate, 2026-09-25)';
  end if;
  raise notice 'plans: table, guard, 2 policies and plan_interest are in place';
end $$;

commit;

-- After running: select policyname, cmd, roles from pg_policies where tablename = 'plans';
-- Expect plans_friends_read (SELECT) and plans_own (ALL), both {authenticated}.
