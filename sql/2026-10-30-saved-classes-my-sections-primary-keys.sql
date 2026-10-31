-- 2026-10-30 — "That's already there." when giving a class from the Degree Progress Report a time.
-- saved_classes and my_sections have NO primary key on production, only UNIQUE constraints
-- (saved_classes_pkey_term, my_sections_pkey_term). supabase-js .upsert() without onConflict resolves
-- against the primary key, so with none it is a plain INSERT and re-saving a saved class fails with
-- 23505. That is every phone app already installed (1.0) and the 1.0.1 build in App Review, and the
-- website. Making the same columns the primary key turns every one of those upserts into an update,
-- with no app change. Same columns, same uniqueness: no row can be rejected that wasn't already.
-- Checked 2026-10-30: no NULLs in these columns (all NOT NULL), no foreign key references either
-- constraint. Reversible: see the bottom.
begin;
alter table public.saved_classes
  drop constraint saved_classes_pkey_term,
  add constraint saved_classes_pkey primary key (user_id, code, term);
alter table public.my_sections
  drop constraint my_sections_pkey_term,
  add constraint my_sections_pkey primary key (user_id, class_nbr, term);
commit;

-- check (should list both as 'p'):
-- select conrelid::regclass, conname, contype, pg_get_constraintdef(oid) from pg_constraint
--  where conname in ('saved_classes_pkey','my_sections_pkey');

-- undo:
-- alter table public.saved_classes drop constraint saved_classes_pkey, add constraint saved_classes_pkey_term unique (user_id, code, term);
-- alter table public.my_sections  drop constraint my_sections_pkey,  add constraint my_sections_pkey_term  unique (user_id, class_nbr, term);
