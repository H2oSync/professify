-- ================================================================================================
-- FAVORITE TEACHER — three per student.  3 Oct 2026
-- ------------------------------------------------------------------------------------------------
-- Tate: "lets add in a favorite teacher badge so it will give the professor a favorite teacher
--        students only get 3 of these"
--
-- A student marks a professor "Favorite teacher" from the rate form. A professor's page shows how
-- many students at your school picked them. Rules, all enforced here, not in the app:
--   · 3 at most per student. A 4th is refused with a sentence the app shows as written;
--   · only a professor you have reviewed (the badge goes with your review). A favorite whose
--     review was deleted stops counting at once and is cleared on your next change — and it does
--     not come back if you review that professor again (pick it again);
--   · anonymous: nobody can read who picked whom. A student reads only their own list
--     (my_favorite_teachers); everyone else reads counts (favorite_teacher_counts);
--   · counts are your own school's students only (the school wall), and only at 3 or more;
--   · a suspended account can't add one (it can still take one back);
--   · deleting an account deletes its favorites (FK to auth.users, on delete cascade).
--
-- The table has NO grants and NO policies: the three functions below are the only way in.
-- New and additive — nothing existing changes. Safe to run twice. Nothing is dropped.
-- Until this runs, the phone simply doesn't show the Favorite teacher row or badge.
-- ================================================================================================
begin;

create table if not exists public.favorite_teachers (
  user_id       uuid        not null references auth.users(id) on delete cascade,
  professor_key text        not null check (length(professor_key) between 3 and 200),
  created_at    timestamptz not null default now(),
  primary key (user_id, professor_key)
);
alter table public.favorite_teachers enable row level security;
revoke all on table public.favorite_teachers from public, anon, authenticated;

-- Your own favorites that still have a review behind them.
create or replace function public.my_favorite_teachers()
returns setof text
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select f.professor_key
    from public.favorite_teachers f
   where f.user_id = auth.uid()
     and exists (select 1 from public.reviews r where r.user_id = f.user_id and r.professor_key = f.professor_key and r.created_at <= f.created_at)
   order by f.created_at;
$$;

-- Turn one on or off. Returns how many you have after the change (0–3).
create or replace function public.set_favorite_teacher(p_key text, p_on boolean)
returns int
language plpgsql
volatile
security definer
set search_path = public, pg_temp
as $$
declare
  me uuid := auth.uid();
  k  text := btrim(coalesce(p_key, ''));
  n  int;
  s  boolean := false;
begin
  if me is null then
    raise exception 'Sign in to pick a favorite teacher.' using errcode = 'P0001';
  end if;
  -- One student's changes run one at a time, so two quick taps can't both become the 3rd.
  perform pg_advisory_xact_lock(hashtext('favorite_teachers:' || me::text));
  -- Favorites whose review is gone don't count and are cleared.
  delete from public.favorite_teachers f
   where f.user_id = me
     and not exists (select 1 from public.reviews r where r.user_id = me and r.professor_key = f.professor_key and r.created_at <= f.created_at);

  if not coalesce(p_on, false) then
    delete from public.favorite_teachers where user_id = me and professor_key = k;
  elsif not exists (select 1 from public.favorite_teachers where user_id = me and professor_key = k) then
    if to_regprocedure('public.is_suspended(uuid)') is not null then
      execute 'select public.is_suspended($1)' into s using me;
    end if;
    if coalesce(s, false) then
      raise exception 'This account can''t pick favorite teachers right now.' using errcode = 'P0001';
    end if;
    if not exists (select 1 from public.reviews r where r.user_id = me and r.professor_key = k) then
      raise exception 'Rate this professor first — your favorite teacher goes with your review.' using errcode = 'P0001';
    end if;
    select count(*) into n from public.favorite_teachers where user_id = me;
    if n >= 3 then
      raise exception 'You''ve used all 3 favorite teachers. Take one back first.' using errcode = 'P0001';
    end if;
    insert into public.favorite_teachers (user_id, professor_key) values (me, k);
  end if;

  select count(*) into n from public.favorite_teachers where user_id = me;
  return n;
end;
$$;

-- How many students at your school picked each professor. Counts only — never who — and only at
-- 3 or more (the app's floor for any number built on reviews), so a badge never points at one
-- reviewer.
create or replace function public.favorite_teacher_counts()
returns table (professor_key text, n int)
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select f.professor_key, count(*)::int
    from public.favorite_teachers f
   where auth.uid() is not null
     and public.school_of(f.user_id) = public.my_school()
     and exists (select 1 from public.reviews r where r.user_id = f.user_id and r.professor_key = f.professor_key and r.created_at <= f.created_at)
   group by f.professor_key
  having count(*) >= 3;
$$;

revoke all on function public.my_favorite_teachers()             from public, anon;
revoke all on function public.set_favorite_teacher(text, boolean) from public, anon;
revoke all on function public.favorite_teacher_counts()          from public, anon;
grant execute on function public.my_favorite_teachers()             to authenticated;
grant execute on function public.set_favorite_teacher(text, boolean) to authenticated;
grant execute on function public.favorite_teacher_counts()          to authenticated;

-- Self-checks: raise (and roll back) if anything isn't what this file says.
do $$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where n.nspname = 'public' and p.proname in ('my_favorite_teachers', 'set_favorite_teacher', 'favorite_teacher_counts')
                and not p.prosecdef) then
    raise exception 'favorite teacher functions must be SECURITY DEFINER';
  end if;
  if has_table_privilege('authenticated', 'public.favorite_teachers', 'select')
     or has_table_privilege('authenticated', 'public.favorite_teachers', 'insert')
     or has_table_privilege('anon', 'public.favorite_teachers', 'select') then
    raise exception 'favorite_teachers must not be readable or writable directly';
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.favorite_teachers'::regclass) then
    raise exception 'favorite_teachers must have row level security on';
  end if;
  if has_function_privilege('anon', 'public.set_favorite_teacher(text, boolean)', 'execute')
     or has_function_privilege('anon', 'public.favorite_teacher_counts()', 'execute') then
    raise exception 'anon can call a favorite teacher function';
  end if;
  if not has_function_privilege('authenticated', 'public.set_favorite_teacher(text, boolean)', 'execute') then
    raise exception 'authenticated cannot call set_favorite_teacher';
  end if;
  if to_regprocedure('public.is_suspended(uuid)') is null then
    raise notice 'is_suspended(uuid) is not installed: suspended accounts are not stopped from picking favorites';
  end if;
end $$;

commit;

-- Check it (read-only), signed in as yourself:
--   select * from public.my_favorite_teachers();
--   select * from public.favorite_teacher_counts();
