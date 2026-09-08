-- =============================================================================
--  professify-class-waivers.sql — 2026-09-03
--
--  "I never took this and didn't have to take it."  (Tate, on the Quick check
--  card offering ECON 2001.)  AP credit, transfer credit, an advisor's waiver,
--  a catalog year that never required it — all "satisfied", none "took".
--
--  Kept as its OWN table, deliberately apart from class_history:
--    class_history  = classes you took  (read by friends' views, professor
--                     pages, the rating prompts)
--    class_waivers  = requirements you satisfied without taking the class
--                     (read by prerequisite checks, planner ticks, degree
--                     progress — and by NOBODY ELSE, ever)
--
--  Owner-only. No friend, no professor page, no suggestion function reads it.
--  Safe to re-run. Nothing here is destructive.
-- =============================================================================

create table if not exists public.class_waivers (
  user_id    uuid        not null references auth.users(id) on delete cascade,
  code       text        not null,
  reason     text        not null default 'waived',   -- ap | transfer | waived | catalog
  created_at timestamptz not null default now(),
  primary key (user_id, code)
);

alter table public.class_waivers enable row level security;

drop policy if exists "own waivers only" on public.class_waivers;
create policy "own waivers only"
  on public.class_waivers for all
  using      ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

-- PUBLIC gets nothing; signed-in students get their own rows through the policy above.
revoke all on public.class_waivers from public, anon;
grant select, insert, update, delete on public.class_waivers to authenticated;

-- VERIFY (run as any signed-in user; expect only your own rows, or none):
--   select code, reason, created_at from public.class_waivers;
