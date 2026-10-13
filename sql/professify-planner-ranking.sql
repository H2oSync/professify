-- RUN 19 · What matters most, ranked 1-2-3 (2026-10-12)
-- The Builder lets you rank "Finishing my degree", "Great professors" and "Classes with friends". The first is
-- already saved in planner_prefs.priority; this adds the whole order so it follows you to another phone.
-- Until this runs, the app keeps the order on the phone and still saves the first. Safe to run again.

alter table public.planner_prefs add column if not exists ranking text;

do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'planner_prefs_ranking_check') then
    alter table public.planner_prefs add constraint planner_prefs_ranking_check check (
      ranking is null or (
        ranking ~ '^(degree|professors|friends),(degree|professors|friends),(degree|professors|friends)$'
        and ranking like '%degree%' and ranking like '%professors%' and ranking like '%friends%'
        and split_part(ranking, ',', 1) = priority));
  end if;
end $$;

-- Check: one row, ranking_column = 1, ranking_check = 1
select (select count(*) from information_schema.columns where table_schema = 'public' and table_name = 'planner_prefs' and column_name = 'ranking') as ranking_column,
       (select count(*) from pg_constraint where conname = 'planner_prefs_ranking_check') as ranking_check;
