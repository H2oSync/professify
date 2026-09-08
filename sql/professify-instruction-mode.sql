-- ============================================================================
-- Instruction mode: make Async / Virtual / Hybrid real
-- ============================================================================
-- Cal Poly's PeopleSoft class detail page prints an "Instruction Mode" for every
-- section ("In Person", "Synchronous Virtual", "Asynchronous Virtual", "Hybrid")
-- and usually a "Location" ("Main Campus", "Online"). The scraper already loads
-- that page for seat counts, so capturing these costs no extra requests.
--
-- Nothing in the app can infer this. A section with no meeting time might be
-- asynchronous, or might simply not be scheduled yet — identical in the data,
-- opposite in meaning. Until these columns are populated, Professify shows no
-- mode pills at all rather than guessing.
--
-- Safe to run more than once. Run it BEFORE (or after) deploying the updated
-- scraper — the scraper detects a missing column and upserts without it either
-- way, so the nightly seat feed can never break on ordering.
--
-- Run once in Supabase -> SQL Editor.
-- ============================================================================

alter table public.course_seats
  add column if not exists instruction_mode text,
  add column if not exists location         text,
  add column if not exists room             text;

-- The app filters and groups on mode; an index keeps that cheap as the table grows.
create index if not exists course_seats_mode_idx
  on public.course_seats (term, instruction_mode);

-- ---------------------------------------------------------------------------
-- After the next scrape, check it landed:
--
--   select instruction_mode, count(*)
--     from public.course_seats
--    where term = '2268'
--    group by 1
--    order by 2 desc;
--
-- Expect rows like: In Person | 5200, Synchronous Virtual | 300,
-- Asynchronous Virtual | 120, Hybrid | 60, and possibly NULL for sections
-- whose detail page was not fetched (CP_FETCH_DETAILS=0).
-- ---------------------------------------------------------------------------
