-- TermChamp: seat-table cleanup after the 2026-10-30 scraper audit — FOR TATE TO REVIEW AND RUN
--
-- WHAT IS WRONG IN course_seats TODAY (read-only queries, 2026-10-31 00:55 UTC)
--   Spring 2027 (term 2274) holds 678 rows that are FALL 2026 sections. Every one is dated 2026
--   (669 of them "08/24/2026 - 12/11/2026") and every one has an exact twin in term 2268 with the
--   same class_nbr, course_code and section. The scraper sometimes searched the page's default
--   term (Fall) while stamping the rows 2274. The app has been showing these as Spring classes.
--   The scraper fix (seats/sweep.mjs) stops new ones and would prune most of these within a day,
--   but a few subjects hold so many that the 50% safety cap refuses them (NAU, EPO) — so clear
--   them here, once.
--
-- PARTS
--   1  preview (read-only)                                  — run first, check the numbers
--   2  delete the 678 Fall impostors from term 2274         — one transaction, guarded
--   3  OPTIONAL: course_seats_removed, a record of deleted rows, for an app that syncs by
--      updated_at deltas (a deleted row has no updated_at to notice)
--   4  OPTIONAL, commented out: Fall 2026's own dropped sections
--
-- Safe to run twice (part 2 deletes nothing the second time; part 3 is idempotent).

-- ----------------------------------------------------------------------------- 1. preview
select count(*)                                                   as fall_dated_in_2274,     -- expect ~678
       count(*) filter (where f.class_nbr is not null
                          and f.course_code = s.course_code
                          and f.section = s.section)              as with_exact_fall_twin,   -- expect the same number
       min(s.updated_at) as first_written, max(s.updated_at) as last_written
  from public.course_seats s
  left join public.course_seats f on f.term = '2268' and f.class_nbr = s.class_nbr
 where s.term = '2274' and s.dates ~ '/2026';

-- ------------------------------------------------------------- 2. delete the Fall impostors
begin;
do $$
declare n int; m int;
begin
  select count(*) into n from public.course_seats s
   where s.term = '2274' and s.dates ~ '/2026'
     and exists (select 1 from public.course_seats f
                  where f.term = '2268' and f.class_nbr = s.class_nbr
                    and f.course_code = s.course_code and f.section = s.section);
  select count(*) into m from public.course_seats s where s.term = '2274' and s.dates ~ '/2026';
  if n <> m then
    raise exception 'refusing: % Fall-dated rows in 2274 but only % have an exact twin in 2268 — look before deleting', m, n;
  end if;
  if n > 800 then
    raise exception 'refusing: % rows is more than the audit found (678) — look before deleting', n;
  end if;
  delete from public.course_seats s
   where s.term = '2274' and s.dates ~ '/2026'
     and exists (select 1 from public.course_seats f
                  where f.term = '2268' and f.class_nbr = s.class_nbr
                    and f.course_code = s.course_code and f.section = s.section);
  raise notice 'deleted % Fall 2026 sections that were filed under Spring 2027', n;
end $$;
commit;

-- --------------------------------------------- 3. OPTIONAL: a record of removed sections
-- The scraper now deletes a section once complete sweeps have not seen it for 24h (sweep.mjs).
-- An app that downloads only rows with updated_at > its last sync never learns about a delete.
-- This keeps one row per removed (term, class_nbr) with when it went, readable like
-- course_seats itself, so a delta sync can ask "what was removed since T?":
--   /rest/v1/course_seats_removed?term=eq.2274&removed_at=gt.<T>&select=class_nbr,removed_at
-- If a section comes back (re-inserted by a later sweep), its tombstone is removed.
create table if not exists public.course_seats_removed (
  term        text        not null,
  class_nbr   text        not null,
  course_code text,
  section     text,
  last_seen   timestamptz,
  removed_at  timestamptz not null default now(),
  primary key (term, class_nbr)
);
create index if not exists course_seats_removed_term_at on public.course_seats_removed (term, removed_at);
alter table public.course_seats_removed enable row level security;
drop policy if exists course_seats_removed_read on public.course_seats_removed;
create policy course_seats_removed_read on public.course_seats_removed for select using (true);
grant select on public.course_seats_removed to anon, authenticated;

create or replace function public.course_seats_tombstone()
returns trigger language plpgsql security definer set search_path = public, pg_temp as $$
begin
  if tg_op = 'DELETE' then
    insert into public.course_seats_removed (term, class_nbr, course_code, section, last_seen, removed_at)
    values (old.term, old.class_nbr, old.course_code, old.section, old.updated_at, now())
    on conflict (term, class_nbr) do update
      set course_code = excluded.course_code, section = excluded.section,
          last_seen = excluded.last_seen, removed_at = excluded.removed_at;
    return old;
  else
    delete from public.course_seats_removed where term = new.term and class_nbr = new.class_nbr;
    return new;
  end if;
end $$;
revoke all on function public.course_seats_tombstone() from public, anon, authenticated;
drop trigger if exists course_seats_tombstone_del on public.course_seats;
create trigger course_seats_tombstone_del after delete on public.course_seats
  for each row execute function public.course_seats_tombstone();
drop trigger if exists course_seats_tombstone_ins on public.course_seats;
create trigger course_seats_tombstone_ins after insert on public.course_seats
  for each row execute function public.course_seats_tombstone();
-- NOTE: if part 3 is run BEFORE part 2, part 2's 678 deletes are recorded as removals too —
-- which is what a delta-syncing app needs to drop them from its cache. Running 3 then 2 is fine.

-- ------------------------------------- 4. OPTIONAL: Fall 2026's own dropped sections (off)
-- Fall is dark (enrolment closed Oct 28) so no sweep will ever prune it. 284 Fall rows were last
-- seen before Oct 24 while Fall was still being swept every 3 hours until Oct 29 05:30 UTC — about
-- fifty sweeps did not see them. They are almost certainly cancelled sections. Harmless to leave
-- (a student's own Fall classes are read by class number), but Explore's "now" list shows them.
-- Preview:   select count(*) from public.course_seats where term = '2268' and updated_at < '2026-10-24';
-- Delete:    delete from public.course_seats where term = '2268' and updated_at < '2026-10-24';
