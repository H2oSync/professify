-- 2026-11-01: friend suggestions include people in your major (Tate: "recommended people in the same Major ... to be
-- able to get the same classes"). Before this, same major only broke ties: someone in your major who shares no class
-- and has fewer than 2 mutual friends was never suggested, so 'Same major as you' could not be reached.
-- The ONE change: `or c.same_major` in the candidate filter. Ranking is unchanged — a shared section (40), mutual
-- friends (18 each), a shared class (10) all still come first; same major + year (6), then same major (3).
-- Still scoped by the wrapper suggest_friends__incl_pending (same school, demo vs real, blocks) and
-- suggest_friends (accounts pending deletion), and dismissals are still honoured. Nothing new is shown on the card:
-- the reason line is the server's own text, as before.
CREATE OR REPLACE FUNCTION public.suggest_friends_unscoped__incl_pending(p_limit integer DEFAULT 6)
 RETURNS TABLE(id uuid, display_name text, username text, avatar_url text, reason text, mutuals integer, score integer, shared_codes text[])
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
     or c.same_major                                    -- 2026-11-01: people in your major qualify on their own
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
       -- sec-picks-2026-10-16: the codes behind the counts are not handed to non-friends.
       null::text[] as shared_codes
from scored s
join public.profiles p on p.id = s.id
order by s.sc desc, p.display_name asc
limit greatest(least(coalesce(p_limit,6), 25), 1);
$function$;
