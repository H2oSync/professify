-- ============================================================================================
-- WHICH CLASS DO I HAVE WITH THIS PERSON — 2026-09-05
-- ============================================================================================
-- Tate: "lets make sure the 1 class in common actually works because what class do i have with
-- this person who im getting recommended to."
--
-- The suggestion cards say "1 class in common" and cannot say which one, because neither
-- suggestion function returns the codes it counted — only the number. The count is real, but
-- nothing on the page stands behind it, so a student cannot check it and neither can we. This
-- migration returns the evidence.
--
-- ADDITIVE ON PURPOSE. suggest_classmates() is left exactly as it is: a v2 is created beside it,
-- and the app calls v2 first and falls back to v1 when v2 is not installed. Nothing that works
-- today stops working, at any point during the rollout, in either order.
--
-- suggest_friends(int) IS replaced, because its full definition is in
-- professify-friend-suggestions.sql and this is that file's body with one column added. If you
-- have edited it in the dashboard since, diff before running.
--
-- Safe to re-run.
--
-- WHAT THIS DISCLOSES, stated plainly so it is a decision and not a side effect:
--   a suggestion card will now name a course that BOTH of you are in. It can only ever name a
--   class you are already enrolled in yourself — the codes are the intersection with your own
--   my_sections rows, computed inside a security-definer function, and no other part of that
--   person's schedule crosses. The card already disclosed the COUNT of that same intersection.
--   If naming it is further than you want to go before launch, do not run part 1; the client
--   handles the no-codes case and keeps today's behaviour.
-- ============================================================================================


-- --------------------------------------------------------------------------------------------
-- 1. suggest_classmates_v2() — the same people, plus the codes
-- --------------------------------------------------------------------------------------------
-- Shape matches what the app reads off these rows: id, display_name, username, avatar_url,
-- overlap, and codes. Deliberately NOT edu_email or instagram_handle — see the note below.
-- CREATE OR REPLACE cannot change a function's OUT columns (42P13), and an earlier draft of this
-- file shipped a version WITH edu_email. Drop first so the corrected shape actually lands instead
-- of the script aborting on a database that already has the old one.
drop function if exists public.suggest_classmates_v2();

create or replace function public.suggest_classmates_v2()
-- WHAT THIS DOES NOT RETURN, and why — corrected 2026-09-05 during the launch audit.
-- The first draft of this function returned edu_email and instagram_handle, because that is the
-- shape the client reads off a suggestion row. It was wrong: by construction every row here is a
-- person you are NOT connected to (see the `connected` filter below), so it handed any signed-in
-- student the Cal Poly address and Instagram handle of twelve strangers per call — a bulk
-- directory of real identities keyed on shared coursework, exactly the thing the app's own
-- comment says never happens ("shown only on the rows of people you have BOTH accepted, never in
-- search results"). A suggestion card needs a name, a photo and the classes you share. It does
-- not need a way to contact someone who has not accepted you.
returns table (
  id               uuid,
  display_name     text,
  username         text,
  avatar_url       text,
  overlap          int,
  codes            text[]
)
language sql
security definer
stable
set search_path = public
as $$
with me as (select auth.uid() as uid),
-- Anyone already connected in either direction and at any stage. A pending request counts:
-- re-suggesting someone whose request is sitting in their inbox is the most confusing thing
-- this feature could do.
connected as (
  select case when r.from_user = m.uid then r.to_user else r.from_user end as other
  from public.friend_requests r, me m
  where (r.from_user = m.uid or r.to_user = m.uid)
    and r.status in ('accepted','pending')
),
my_codes as (
  select distinct s.code
  from public.my_sections s, me m
  where s.user_id = m.uid and s.code is not null
),
-- THE INTERSECTION, kept as codes rather than collapsed to a count. distinct so a lecture and
-- its lab logged under one code cannot make one shared class look like two.
hits as (
  select s.user_id as other, array_agg(distinct s.code order by s.code) as codes
  from public.my_sections s
  join my_codes k on k.code = s.code
  where s.user_id <> (select uid from me)
  group by 1
)
select p.id,
       coalesce(p.display_name,'Classmate') as display_name,
       p.username,
       p.avatar_url,
       cardinality(h.codes)::int as overlap,
       h.codes
from hits h
join public.profiles p on p.id = h.other
where p.id not in (select other from connected)
  and p.id not in (select dismissed_id from public.friend_suggestion_dismissals
                   where user_id = (select uid from me))
order by cardinality(h.codes) desc, coalesce(p.display_name,'') asc
limit 12;
$$;

revoke all on function public.suggest_classmates_v2() from public;
revoke execute on function public.suggest_classmates_v2() from anon;
grant execute on function public.suggest_classmates_v2() to authenticated;


-- --------------------------------------------------------------------------------------------
-- 2. suggest_friends(int) — same function, one more column
-- --------------------------------------------------------------------------------------------
-- Only change from professify-friend-suggestions.sql: shared_codes is returned alongside the
-- reason. The reason sentence is untouched — the server is still the only thing that knows WHY
-- someone scored (mutual friends, shared section, shared course), and the app does not rewrite
-- it. The codes are evidence beside it.
-- Same 42P13 hazard: this adds shared_codes to an existing 7-column function, and without the
-- drop the whole script aborts here, leaving the revoke/grant at the bottom unexecuted.
drop function if exists public.suggest_friends(int);

create or replace function public.suggest_friends(p_limit int default 6)
returns table (
  id           uuid,
  display_name text,
  username     text,
  avatar_url   text,
  reason       text,
  mutuals      int,
  score        int,
  shared_codes text[]
)
language sql
security definer
stable
set search_path = public
as $$
with me as (select auth.uid() as uid),
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
mutual as (
  select case when r.from_user = f.fid then r.to_user else r.from_user end as other,
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
-- NEW: the codes behind those two counts, so the card can name them.
code_list as (
  select s.user_id as other, array_agg(distinct s.code order by s.code) as codes
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
         greatest(coalesce(ch.n,0) - coalesce(sh.n,0), 0) as course_n,
         least(coalesce(mu.n,0), 5) as mut_n,
         coalesce(mu.n,0) as mut_raw,
         cl.codes as codes,
         (p.major is not null and p.major = (select major from me_prof)) as same_major,
         (p.major is not null and p.major = (select major from me_prof)
          and p.class_standing is not null
          and p.class_standing = (select class_standing from me_prof)) as same_cohort
  from public.profiles p
  left join sec_hits    sh on sh.other = p.id
  left join course_hits ch on ch.other = p.id
  left join code_list   cl on cl.other = p.id
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
  where c.sec_n > 0 or c.course_n > 0 or c.mut_raw >= 2
)
select s.id,
       coalesce(p.display_name,'Classmate') as display_name,
       p.username,
       p.avatar_url,
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
       s.sc::int as score,
       -- A pure-mutual-friends suggestion shares no class, and must not be handed an array
       -- that would make the card claim one.
       s.codes as shared_codes
from scored s
join public.profiles p on p.id = s.id
order by s.sc desc, p.display_name asc
limit greatest(least(coalesce(p_limit,6), 25), 1);
$$;

revoke all on function public.suggest_friends(int) from public;
revoke execute on function public.suggest_friends(int) from anon;
grant execute on function public.suggest_friends(int) to authenticated;


-- --------------------------------------------------------------------------------------------
-- VERIFY — run these as a signed-in student, not as the service role
-- --------------------------------------------------------------------------------------------
--   select * from public.suggest_classmates_v2();
--     Expect SIX columns. If edu_email or instagram_handle appears, an older version of this
--     function is still installed and is leaking strangers' contact details — re-run this file.
--     Expect: codes has exactly `overlap` entries on every row, and every code in it is one of
--     yours:
--   select code from public.my_sections where user_id = auth.uid() order by code;
--
--   select display_name, reason, shared_codes from public.suggest_friends(6);
--     Expect: a row whose reason mentions sections or classes carries codes; a row whose reason
--     is "N mutual friends" may carry none, and the card then shows no chips.
