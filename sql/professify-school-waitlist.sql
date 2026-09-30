-- ================================================================================================
-- professify-school-waitlist.sql — 2026-09-29
-- ------------------------------------------------------------------------------------------------
-- Tate: an SDSU or UCSB student who tries the phone app should see "we're bringing TermChamp to
-- your school — join the list and we'll tell you when we do", instead of a dead end.
--
-- WHAT IT KEEPS: an email address and which school it is. Nothing else — no name, no account, no
-- device, no IP. Only SDSU and UCSB addresses are accepted (the database checks the domain with the
-- same school_from_email() the school wall uses), so this can't become a list of anybody's email.
--
-- WHO CAN READ IT: nobody through the app. There is INSERT for anon/authenticated and no SELECT,
-- UPDATE or DELETE policy at all. Tate reads it in the Supabase SQL editor:
--     select school, count(*) from public.school_waitlist group by 1;
--     select email from public.school_waitlist where school = 'sdsu' order by created_at;
-- Joining twice is harmless: the email is the primary key, and the app says "you're already on it".
--
-- Needs professify-schools.sql (school_from_email) to have run — it has. One transaction; safe to
-- re-run; self-checks raise if anything is off.
-- ================================================================================================
begin;

do $$ begin
  if to_regprocedure('public.school_from_email(text)') is null then
    raise exception 'school_from_email(text) is missing — run professify-schools.sql first';
  end if;
end $$;

create table if not exists public.school_waitlist (
  email      text primary key,
  school     text not null,
  created_at timestamptz not null default now(),
  constraint school_waitlist_lower   check (email = lower(email)),
  constraint school_waitlist_len     check (char_length(email) <= 254),
  constraint school_waitlist_school  check (school in ('sdsu', 'ucsb')),
  constraint school_waitlist_matches check (public.school_from_email(email) = school)
);

alter table public.school_waitlist enable row level security;
revoke all on public.school_waitlist from public, anon, authenticated;
grant insert (email, school) on public.school_waitlist to anon, authenticated;

drop policy if exists "anyone can join a school waitlist" on public.school_waitlist;
create policy "anyone can join a school waitlist" on public.school_waitlist
  for insert to anon, authenticated
  with check (school in ('sdsu', 'ucsb') and public.school_from_email(email) = school);

-- Self-checks
do $$
declare n int;
begin
  select count(*) into n from pg_policies where schemaname = 'public' and tablename = 'school_waitlist';
  if n <> 1 then raise exception 'school_waitlist: expected exactly 1 policy, found %', n; end if;
  select count(*) into n from pg_policies where schemaname = 'public' and tablename = 'school_waitlist' and cmd <> 'INSERT';
  if n <> 0 then raise exception 'school_waitlist: a non-INSERT policy exists — nobody should read this through the API'; end if;
  if has_table_privilege('anon', 'public.school_waitlist', 'SELECT') or has_table_privilege('authenticated', 'public.school_waitlist', 'SELECT') then
    raise exception 'school_waitlist: SELECT is granted — revoke it';
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.school_waitlist'::regclass) then
    raise exception 'school_waitlist: row level security is off';
  end if;
end $$;

commit;
