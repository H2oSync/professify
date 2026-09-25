-- professify-catalog-read.sql — 2026-09-24
--
-- Lets the app READ the course descriptions the seat scraper already saves.
--
-- seats/scrape-seats.mjs has upserted one row per course into public.course_catalog
-- (course_code, subject, title, prereqs, description, updated_at) off the same Cal Poly class-search
-- detail pages it reads seats from. Nothing in the app ever read it. Build 2026-09-23 23:06 reads
-- course_code + description with the public (anon) key to put a one-line description on Explore's
-- class cards. If this table is missing, or RLS refuses that read, the cards simply keep their
-- units/sections line — nothing breaks, nothing is invented.
--
-- What this does, all idempotent, in one transaction:
--   1. creates the table ONLY if it does not exist (same columns the scraper writes);
--   2. turns RLS on;
--   3. lets anyone read it — it is Cal Poly's public catalog text, not student data;
--   4. makes sure nobody but the scraper's service key can write it;
--   5. checks all of that and raises if any part is not true.
-- Nothing is dropped. Safe to run twice.

begin;

create table if not exists public.course_catalog (
  course_code  text primary key,
  subject      text,
  title        text,
  prereqs      text,
  description  text,
  updated_at   timestamptz default now()
);

alter table public.course_catalog enable row level security;

grant select on public.course_catalog to anon, authenticated;
revoke insert, update, delete, truncate on public.course_catalog from public, anon, authenticated;

do $$
begin
  if not exists (
    select 1 from pg_policies
     where schemaname = 'public' and tablename = 'course_catalog' and cmd in ('SELECT', 'ALL')
  ) then
    create policy "course catalog is public" on public.course_catalog
      for select to anon, authenticated using (true);
  end if;
end $$;

-- Self-checks. Each one raises, so a half-applied state rolls the whole thing back.
do $$
declare n int;
begin
  -- anon can read, and RLS does not hide rows from it: a probe row written here must be visible to
  -- anon (a missing policy returns zero rows, not an error, so a bare count would prove nothing).
  insert into public.course_catalog(course_code, description) values ('ZZZ 0001', 'self-check probe')
    on conflict (course_code) do nothing;
  set local role anon;
  select count(*) into n from public.course_catalog where course_code = 'ZZZ 0001';
  reset role;
  delete from public.course_catalog where course_code = 'ZZZ 0001';
  if n <> 1 then raise exception 'self-check FAILED: anon cannot see course_catalog rows (RLS policy missing?)'; end if;
  select count(*) into n from public.course_catalog;

  -- anon cannot write
  begin
    set local role anon;
    insert into public.course_catalog(course_code, description) values ('ZZZ 0000', 'self-check');
    reset role;
    raise exception 'self-check FAILED: anon could insert into course_catalog';
  exception when insufficient_privilege then
    reset role;
  end;

  raise notice 'course_catalog OK — % rows readable by anon, not writable by it', n;
end $$;

commit;

-- What is actually in it (read-only). Tate: paste these three numbers back.
select count(*)                                   as courses,
       count(description)                         as with_description,
       count(*) filter (where course_code ~ '^[A-Z]{2,5} [0-9]{4}[A-Z]?$') as semester_codes
  from public.course_catalog;
