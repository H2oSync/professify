-- ============================================================
-- Professify — Supabase schema for persistent, .edu-verified reviews
-- Run this once in your Supabase project: SQL Editor → New query → paste → Run.
-- ============================================================

create extension if not exists "pgcrypto";

-- ---- Reviews table ----
create table if not exists public.reviews (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null default auth.uid() references auth.users(id) on delete cascade,
  professor_key  text not null,                       -- normalized "name|department"
  professor_name text not null,
  department     text,
  course         text,
  score          int  not null check (score between 1 and 5),
  would_again    boolean,
  tags           text[] default '{}',
  note           text,
  helpful        int  not null default 0,
  created_at     timestamptz not null default now()
);

-- One review per student, per professor, per course.
create unique index if not exists reviews_unique_per_class
  on public.reviews (user_id, professor_key, coalesce(course, ''));

create index if not exists reviews_prof_idx on public.reviews (professor_key);

-- ---- Row Level Security ----
alter table public.reviews enable row level security;

-- Anyone can read reviews (public site).
drop policy if exists "reviews_public_read" on public.reviews;
create policy "reviews_public_read" on public.reviews
  for select using (true);

-- A signed-in student may insert ONLY their own review, and ONLY from a verified .edu email.
-- (To lock to Cal Poly only, change '%.edu' to '%@calpoly.edu'.)
drop policy if exists "reviews_insert_own_edu" on public.reviews;
create policy "reviews_insert_own_edu" on public.reviews
  for insert with check (
    auth.uid() = user_id
    and lower(coalesce(auth.jwt() ->> 'email', '')) like '%.edu'
  );

-- A student may edit/delete their own reviews.
drop policy if exists "reviews_update_own" on public.reviews;
create policy "reviews_update_own" on public.reviews
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "reviews_delete_own" on public.reviews;
create policy "reviews_delete_own" on public.reviews
  for delete using (auth.uid() = user_id);

-- ---- Optional: public aggregate stats per professor (handy for future features) ----
create or replace view public.professor_review_stats as
  select professor_key,
         max(professor_name)                                        as professor_name,
         count(*)                                                   as review_count,
         round(avg(score)::numeric, 2)                              as avg_score,
         round(avg(case when would_again then 1 else 0 end)::numeric * 100) as would_again_pct
  from public.reviews
  group by professor_key;

grant select on public.professor_review_stats to anon, authenticated;
