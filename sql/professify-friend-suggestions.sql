-- =============================================================================================
-- Professify — "People you might know"
-- Written 2026-08-27 for Tate. Run this in the Supabase SQL editor.
--
-- WHY THIS IS A DATABASE FUNCTION AND NOT APP CODE
-- Mutual friends cannot be computed in the browser. RLS on friend_requests lets a student read
-- only their OWN edges, which is correct and must stay that way — counting mutuals means
-- reading edges between OTHER people. So the counting happens inside a SECURITY DEFINER
-- function that returns only the conclusion (a number) and never the edges themselves. Same for
-- shared sections: my_sections is friends-only, and a suggestion is by definition someone who
-- is NOT yet your friend.
--
-- What a caller can learn from this function is exactly: "here are up to N people, and here is
-- one sentence about why". It cannot enumerate anyone's classes, anyone's friends, or anyone
-- who fails the floor below. It answers only about auth.uid() — you cannot ask it about
-- someone else.
--
-- HONEST DATA: every number this returns is counted from real rows. There is no filler, no
-- padding to reach the limit, and no suggestion invented to make the section look populated.
-- When there is nobody to suggest it returns zero rows and the app hides the section entirely.
--
-- Every statement is guarded (IF NOT EXISTS / CREATE OR REPLACE). Nothing here drops anything.
-- Safe to run twice.
-- =============================================================================================

-- ---------------------------------------------------------------------------------------------
-- 1. Dismissals — "don't suggest this person again"
--
-- Permanent by design. The row said "not this person"; re-offering them next week is how a
-- suggestion list becomes noise you learn to scroll past.
-- ---------------------------------------------------------------------------------------------
create table if not exists public.friend_suggestion_dismissals (
  user_id      uuid not null references auth.users(id) on delete cascade,
  dismissed_id uuid not null references auth.users(id) on delete cascade,
  created_at   timestamptz not null default now(),
  primary key (user_id, dismissed_id)
);

alter table public.friend_suggestion_dismissals enable row level security;

do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public'
                 and tablename='friend_suggestion_dismissals' and policyname='fsd_own_select') then
    create policy fsd_own_select on public.friend_suggestion_dismissals
      for select to authenticated using (user_id = auth.uid());
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public'
                 and tablename='friend_suggestion_dismissals' and policyname='fsd_own_insert') then
    create policy fsd_own_insert on public.friend_suggestion_dismissals
      for insert to authenticated with check (user_id = auth.uid());
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public'
                 and tablename='friend_suggestion_dismissals' and policyname='fsd_own_delete') then
    create policy fsd_own_delete on public.friend_suggestion_dismissals
      for delete to authenticated using (user_id = auth.uid());
  end if;
end $$;

-- ---------------------------------------------------------------------------------------------
-- 2. suggest_friends()
--
-- RANKING — strongest predictor of a real Cal Poly friendship first:
--
--   same SECTION                   40 each   You are in the same room twice a week. Nothing
--                                            else on this list can offer that.
--   mutual friend                  18 each   Capped at 5, so one hyper-connected account
--                                            cannot dominate everyone's list.
--   same course, other section     10 each   Counted NET of shared sections, so a shared
--                                            section is never also paid as a shared course.
--   same major AND standing         6        The cohort effect.
--   same major                      3
--
-- FLOOR: a candidate needs a real class overlap OR 2+ mutual friends. A single mutual is noise
-- on a small graph and near-identifying on a tiny one — with twelve accounts, "1 mutual friend"
-- names the person. Major alone never qualifies anyone: 800 people share a major, and a list
-- built from that is a phone book, not a suggestion.
--
-- REASON: one line, the strongest true one. "In 1 of your sections" converts better than
-- "5 mutual friends", which converts better than "Suggested for you" — specificity is the whole
-- reason someone taps Add. The reason returned always matches the term that actually scored
-- highest, so it can never overstate the connection.
-- ---------------------------------------------------------------------------------------------
-- Postgres will not let CREATE OR REPLACE change a function's OUT columns, and an earlier
-- suggest_friends(int) on this database returns a different set of them:
--     ERROR: 42P13 cannot change return type of existing function
-- So this one signature is dropped immediately before being recreated below. Read that line
-- carefully and then relax: it drops a FUNCTION, not a table. Functions hold no data — this one
-- computes its answer from friend_requests, my_sections and profiles every time it is called,
-- and all three are untouched. Nothing you can lose is being dropped, and the next statement
-- puts a suggest_friends back.
--
-- If it errors saying the function does not exist, that is fine — "if exists" means it is a
-- no-op on a database that never had one.
--
-- Should there be OTHER overloads (a suggest_friends with different arguments), this leaves
-- them alone. List them with:
--     select oid::regprocedure from pg_proc where proname='suggest_friends';
drop function if exists public.suggest_friends(int);

create or replace function public.suggest_friends(p_limit int default 6)
returns table (
  id           uuid,
  display_name text,
  username     text,
  avatar_url   text,
  reason       text,
  mutuals      int,
  score        int
)
language sql
security definer
stable
set search_path = public
as $$
with me as (
  select auth.uid() as uid
),
-- Everyone I am already connected to, in either direction and at any stage. A pending request
-- counts: re-suggesting someone whose request is sitting in their inbox is the single most
-- confusing thing this feature could do.
connected as (
  select case when r.from_user = m.uid then r.to_user else r.from_user end as other
  from public.friend_requests r, me m
  where (r.from_user = m.uid or r.to_user = m.uid)
    and r.status in ('accepted','pending')
),
my_friends as (
  select case when r.from_user = m.uid then r.to_user else r.from_user end as fid
  from public.friend_requests r, me m
  where (r.from_user = m.uid or r.to_user = m.uid)
    and r.status = 'accepted'
),
-- Mutuals: an accepted edge between one of MY friends and a stranger. This is the join that
-- cannot happen in the browser, and the only thing that escapes it is the count.
mutual as (
  select case when r.from_user = f.fid then r.to_user else r.from_user end as other,
         -- distinct FRIENDS, not distinct rows: two accepted rows for one pair (which the
         -- friends list itself had a duplicate bug from, 2026-08-26) must not read as two
         -- mutual friends. The number on the card has to be a number of people.
         count(distinct f.fid)::int as n
  from public.friend_requests r
  join my_friends f on (r.from_user = f.fid or r.to_user = f.fid)
  where r.status = 'accepted'
  group by 1
),
my_secs as (
  select distinct s.class_nbr, s.code
  from public.my_sections s, me m
  where s.user_id = m.uid and s.class_nbr is not null
),
my_codes as (
  select distinct s.code from public.my_sections s, me m
  where s.user_id = m.uid and s.code is not null
),
-- Same section, by class number. Distinct so a lecture logged twice cannot inflate anything.
sec_hits as (
  select s.user_id as other, count(distinct s.class_nbr)::int as n
  from public.my_sections s
  join my_secs k on k.class_nbr = s.class_nbr
  group by 1
),
course_hits as (
  select s.user_id as other, count(distinct s.code)::int as n
  from public.my_sections s
  join my_codes k on k.code = s.code
  group by 1
),
me_prof as (
  select p.major, p.class_standing from public.profiles p, me m where p.id = m.uid
),
cand as (
  select p.id,
         coalesce(sh.n,0) as sec_n,
         -- net of sections: a course you share a SECTION of is not also counted as a shared course
         greatest(coalesce(ch.n,0) - coalesce(sh.n,0), 0) as course_n,
         least(coalesce(mu.n,0), 5) as mut_n,
         coalesce(mu.n,0) as mut_raw,
         (p.major is not null and p.major = (select major from me_prof)) as same_major,
         (p.major is not null and p.major = (select major from me_prof)
          and p.class_standing is not null
          and p.class_standing = (select class_standing from me_prof)) as same_cohort
  from public.profiles p
  left join sec_hits    sh on sh.other = p.id
  left join course_hits ch on ch.other = p.id
  left join mutual      mu on mu.other = p.id
  where p.id <> (select uid from me)
    and p.id not in (select other from connected)
    and p.id not in (select dismissed_id from public.friend_suggestion_dismissals
                     where user_id = (select uid from me))
),
scored as (
  select c.*,
         (c.sec_n * 40) + (c.mut_n * 18) + (c.course_n * 10)
           + (case when c.same_cohort then 6 when c.same_major then 3 else 0 end) as sc
  from cand c
  -- THE FLOOR. Major similarity contributes to rank but can never put someone on the list.
  where c.sec_n > 0 or c.course_n > 0 or c.mut_raw >= 2
)
select s.id,
       coalesce(p.display_name,'Classmate') as display_name,
       p.username,
       p.avatar_url,
       -- The reason is whichever term actually scored HIGHEST, not a fixed preference order.
       -- Ordering it by hand meant someone with one shared section and five mutual friends was
       -- told "In 1 of your sections" while the score was almost entirely the mutuals — the
       -- card would have been explaining itself with the wrong fact.
       case
         when s.sec_n*40 >= greatest(s.mut_n*18, s.course_n*10) and s.sec_n > 0
           then (case when s.sec_n = 1 then 'In one of your sections'
                      else 'In '||s.sec_n||' of your sections' end)
         when s.mut_n*18 >= s.course_n*10 and s.mut_raw >= 2
           then s.mut_raw||' mutual friends'
         when s.course_n > 0
           then (case when s.course_n = 1 then 'Taking one of your classes'
                      else 'Taking '||s.course_n||' of your classes' end)
         when s.mut_raw >= 2 then s.mut_raw||' mutual friends'
         when s.same_cohort  then 'Same major and year as you'
         else 'Same major as you'
       end as reason,
       s.mut_raw as mutuals,
       s.sc::int as score
from scored s
join public.profiles p on p.id = s.id
order by s.sc desc, p.display_name asc
limit greatest(least(coalesce(p_limit,6), 25), 1);
$$;

revoke all on function public.suggest_friends(int) from public;
grant execute on function public.suggest_friends(int) to authenticated;

-- ---------------------------------------------------------------------------------------------
-- 3. Indexes the joins above actually use
-- ---------------------------------------------------------------------------------------------
create index if not exists my_sections_class_nbr_idx on public.my_sections(class_nbr);
create index if not exists my_sections_code_idx      on public.my_sections(code);
create index if not exists my_sections_user_idx      on public.my_sections(user_id);
create index if not exists friend_requests_from_idx  on public.friend_requests(from_user);
create index if not exists friend_requests_to_idx    on public.friend_requests(to_user);

-- =============================================================================================
-- AFTER RUNNING THIS
--
-- 1. Smoke test it as yourself (the SQL editor runs as the service role, where auth.uid() is
--    null and the function correctly returns nothing — so test from the app, not from here):
--
--      open professify.app signed in, go to Friends. The section appears only if it has rows.
--
-- 2. Check the dismissals policies landed and that nothing PERMISSIVE and wide-open outranks
--    them. This is not paranoia: that is exactly how my_sections stayed world-readable through
--    two rounds of "correct" SQL on 2026-08-23.
--
--      select tablename, policyname, cmd, qual
--      from pg_policies
--      where schemaname='public' and tablename='friend_suggestion_dismissals';
--
--    Expect 3 rows, every qual mentioning auth.uid(). A row with qual = true is a problem —
--    tell me and I'll write the replacement.
--
-- 3. WITH ~12 ACCOUNTS THIS WILL RETURN ALMOST NOTHING, and that is the correct behaviour, not
--    a bug. The mutual-friend term needs graph density that does not exist yet. The SECTION
--    term works from user #2 — so the fastest way to see this work is two accounts importing
--    schedules that share one class. Judge it at 200 users, not at 12.
-- =============================================================================================
