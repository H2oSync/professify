-- 2026-10-30 · changed_at: when a seat or catalog row's DATA last changed (needs the owner's approval to run).
--
-- Why: the scraper stamps updated_at with the time it READ a row and upserts every row it read, so the daily sweep
-- re-stamps ~6,800 Spring rows whether or not anything changed, and a row can be written up to ~40 min after its
-- stamp. The app (1.0.2) asks only for rows newer than its copy; on updated_at alone the first open after a sweep is
-- a whole download (~3 MB) and every check must look back 90 minutes. With changed_at:
--   · a sweep that changed 30 rows costs the app 30 rows, not the term;
--   · the stamp is the database's own clock at write time, so the look-back is 5 minutes;
--   · the catalog (re-stamped for ~2,200 of 2,971 rows every day) can be checked on every open, not weekly.
-- updated_at is left exactly as it is: seats/plan.mjs reads the newest updated_at to tell when a term was last pulled.
-- The app works without this file (it tries changed_at and falls back to updated_at); once it runs, the app picks
-- changed_at up at its next daily whole download, without an app update.
--
-- Safe to run more than once. No UPDATE of existing rows: the column is added with a constant default, so the
-- AFTER UPDATE seat-alert triggers (push_on_seats, push_seat_change) do not fire.

begin;

alter table public.course_seats   add column if not exists changed_at timestamptz not null default now();
alter table public.course_catalog add column if not exists changed_at timestamptz not null default now();

-- every column except the two stamps decides whether a row changed (new columns count automatically)
create or replace function public.keep_changed_at() returns trigger
language plpgsql set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    new.changed_at := now();
  elsif (to_jsonb(new) - 'updated_at' - 'changed_at') is distinct from (to_jsonb(old) - 'updated_at' - 'changed_at') then
    new.changed_at := now();
  else
    new.changed_at := old.changed_at;
  end if;
  return new;
end $$;

drop trigger if exists course_seats_changed_at on public.course_seats;
create trigger course_seats_changed_at before insert or update on public.course_seats
  for each row execute function public.keep_changed_at();
drop trigger if exists course_catalog_changed_at on public.course_catalog;
create trigger course_catalog_changed_at before insert or update on public.course_catalog
  for each row execute function public.keep_changed_at();

-- the app reads these tables with the public key, column by column (as the other 19 / 6 columns are granted)
grant select (changed_at) on public.course_seats   to anon, authenticated;
grant select (changed_at) on public.course_catalog to anon, authenticated;

create index if not exists course_seats_term_changed_idx on public.course_seats (term, changed_at, class_nbr);

commit;

-- check:
--   select term, count(*), max(changed_at), max(updated_at) from public.course_seats group by term;
-- undo:
--   drop trigger if exists course_seats_changed_at on public.course_seats;
--   drop trigger if exists course_catalog_changed_at on public.course_catalog;
--   drop function if exists public.keep_changed_at();
--   drop index if exists public.course_seats_term_changed_idx;
--   alter table public.course_seats drop column if exists changed_at;
--   alter table public.course_catalog drop column if exists changed_at;
--   (the 1.0.2 app then falls back to updated_at at its next whole download, or at once when a check is refused)
