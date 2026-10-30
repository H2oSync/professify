-- 2026-10-30: watch_sections had no primary key (same bug class as saved_classes/my_sections) — promote its unique index.
alter table public.watch_sections add constraint watch_sections_pkey primary key using index watch_sections_pkey_term;
-- undo: alter table public.watch_sections drop constraint watch_sections_pkey; create unique index watch_sections_pkey_term on public.watch_sections (user_id, class_nbr, term);
