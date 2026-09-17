-- ================================================================================================
-- THE ADMIN DASHBOARD — one place to see who signed up and whether the data is any good
-- 2026-09-14
-- ================================================================================================
-- Tate: "i want to set up a analytics site somewhere where i get all the information on the
-- website and app in one place where i can analyise it and make smart desicions", and then
-- "I also want to see each persons email that signs up and name and everything."
--
-- WHY THIS IS NOT BUILT ON THE EVENTS TABLE. `events` carries a pseudonym that rotates every day,
-- on purpose (see professify-analytics.sql). That makes cohort questions — "of the students who
-- signed up the week Spring registration opened, how many came back on their rotation morning" —
-- not hard but ARITHMETICALLY IMPOSSIBLE. Nothing joins across days.
--
-- The answer is that the events table was never the only behavioural record. `auth.users` knows
-- when someone signed up and when they last signed in. `reviews` knows who wrote what and when.
-- `course_seats` knows when every section was last observed. Those are rows the product keeps for
-- product reasons, tied to accounts, with timestamps — which is real cohort data that required no
-- new tracking and no change to what students were promised.
--
-- THE LINE THIS FILE DOES NOT CROSS, and it is deliberate. The app tells students two different
-- things, and they are not the same promise:
--
--   "Your email is never shown PUBLICLY."   -> publicly. An operator holding a list of their own
--                                              users is consistent with that, and it is how you
--                                              email your first 500 people.
--   "Reviews you post are ANONYMOUS."       -> unconditional. No qualifier.
--
-- So admin_roster returns how MANY reviews a student has written and never what they said. There
-- is no function here that puts a display name beside review text. On a campus this small, a
-- screenshot of a moderator screen doing that is the fastest way to lose every student's trust,
-- and the count answers the only question the dashboard actually has (who contributes, who lurks).
-- Tracing one specific review to its author is a deliberate one-off query with a reason behind it,
-- not a column sitting on a dashboard.
--
-- Every function is moderator-gated INSIDE the function body, not by RLS on a view, because these
-- are security definer and run as the owner — the gate is the only thing between a signed-in
-- student and every email in the database. check-admin.mjs proves that by calling each one as a
-- non-moderator and as anon.
--
-- Safe to re-run.
-- ================================================================================================

-- ------------------------------------------------------------------------------------------------
-- 0. One gate, used by every function below.
-- ------------------------------------------------------------------------------------------------
-- Raises rather than returning empty: an empty dashboard and a refused dashboard look identical on
-- screen, and "there are no users yet" is a very different thing from "you are not allowed to see
-- the users". The message matches the string the client already translates for humans.
create or replace function public.admin_guard()
returns void language plpgsql security definer stable set search_path = public as $$
begin
  if not public.is_moderator() then
    raise exception 'not a moderator' using errcode = 'P0001';
  end if;
end $$;
revoke all on function public.admin_guard() from public;
revoke execute on function public.admin_guard() from anon;
grant execute on function public.admin_guard() to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 1. The roster — every person who has signed up
-- ------------------------------------------------------------------------------------------------
-- Ordered newest first, because the question is almost always "who just joined". `p_q` filters on
-- name, username or email. Counts are counts; nothing here reveals what anyone wrote.
create or replace function public.admin_roster(p_q text default null,
                                               p_limit int default 100,
                                               p_offset int default 0)
returns jsonb language plpgsql security definer stable set search_path = public, auth as $$
declare v jsonb; n int; q text;
begin
  perform public.admin_guard();
  q := nullif(btrim(coalesce(p_q,'')), '');

  select count(*) into n
  from auth.users u
  left join public.profiles p on p.id = u.id
  where q is null
     or u.email ilike '%'||q||'%'
     or coalesce(p.display_name,'') ilike '%'||q||'%'
     or coalesce(p.username,'')     ilike '%'||q||'%';

  select coalesce(jsonb_agg(r order by r->>'signed_up' desc), '[]'::jsonb) into v from (
    select jsonb_build_object(
             'user_id',      u.id,
             'email',        u.email,
             'signed_up',    u.created_at,
             'last_seen',    u.last_sign_in_at,
             /* Days between signing up and the most recent visit. One number that separates
                "signed up and never came back" from "still here", which is the only retention
                question that matters at this size. */
             'days_active',  case when u.last_sign_in_at is null then null
                             else greatest(0, extract(day from (u.last_sign_in_at - u.created_at))::int) end,
             'name',         p.display_name,
             'username',     p.username,
             'school',       p.school,
             'edu_email',    p.edu_email,
             'has_profile',  (p.id is not null),
             /* HOW MANY, NEVER WHAT. See the header. */
             'reviews',      (select count(*) from public.reviews rv where rv.user_id = u.id)
           ) as r
    from auth.users u
    left join public.profiles p on p.id = u.id
    where q is null
       or u.email ilike '%'||q||'%'
       or coalesce(p.display_name,'') ilike '%'||q||'%'
       or coalesce(p.username,'')     ilike '%'||q||'%'
    order by u.created_at desc
    limit greatest(1, least(coalesce(p_limit,100), 500))
    offset greatest(0, coalesce(p_offset,0))
  ) s;

  return jsonb_build_object('total', n, 'rows', v);
end $$;
revoke all on function public.admin_roster(text,int,int) from public;
revoke execute on function public.admin_roster(text,int,int) from anon;
grant execute on function public.admin_roster(text,int,int) to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 2. Sign-up cohorts — from auth.users alone
-- ------------------------------------------------------------------------------------------------
-- No tracking involved: a sign-up is a row with a timestamp, and coming back is last_sign_in_at.
-- This is the honest floor of retention measurement. It cannot say WHAT someone did on their
-- return — that needs per-table timestamps which some tables may not carry yet.
create or replace function public.admin_signups(p_days int default 60)
returns jsonb language plpgsql security definer stable set search_path = public, auth as $$
declare v jsonb;
begin
  perform public.admin_guard();
  select jsonb_build_object(
    'total',        (select count(*) from auth.users),
    'with_profile', (select count(*) from auth.users u join public.profiles p on p.id=u.id),
    'returned',     (select count(*) from auth.users
                     where last_sign_in_at is not null
                       and last_sign_in_at > created_at + interval '1 day'),
    'by_day', coalesce((
      select jsonb_agg(jsonb_build_object('day', d, 'signups', c) order by d)
      from (select date_trunc('day', created_at)::date as d, count(*) c
            from auth.users
            where created_at > now() - make_interval(days => greatest(1, p_days))
            group by 1) x), '[]'::jsonb),
    'by_school', coalesce((
      select jsonb_agg(jsonb_build_object('school', coalesce(school,'(not set)'), 'n', c) order by c desc)
      from (select p.school, count(*) c from public.profiles p group by 1) y), '[]'::jsonb)
  ) into v;
  return v;
end $$;
revoke all on function public.admin_signups(int) from public;
revoke execute on function public.admin_signups(int) from anon;
grant execute on function public.admin_signups(int) to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 3. Seat-feed health — the number that says whether anything on screen is trustworthy
-- ------------------------------------------------------------------------------------------------
-- The BUS 310 review's sharpest structural point was that the report claimed "the data pipeline
-- works" with no coverage or freshness figure behind it. This is that figure. Per term:
-- how many sections, how many carry real counts, when the newest and oldest were observed.
--
-- `counted` vs `sections` is the one to watch. A row with a null capacity is a section the seat
-- feed knows exists but has never opened the detail page for — the app must say "we don't know"
-- for those, never a zero.
create or replace function public.admin_pipeline()
returns jsonb language plpgsql security definer stable set search_path = public as $$
declare v jsonb;
begin
  perform public.admin_guard();
  select coalesce(jsonb_agg(r order by r->>'term' desc), '[]'::jsonb) into v from (
    select jsonb_build_object(
      'term',        term,
      'sections',    count(*),
      'subjects',    count(distinct subject),
      'courses',     count(distinct course_code),
      'counted',     count(*) filter (where capacity is not null),
      'uncounted',   count(*) filter (where capacity is null),
      'open',        count(*) filter (where status = 'Open'),
      'waitlist',    count(*) filter (where status = 'Waitlist'),
      'closed',      count(*) filter (where status = 'Closed'),
      'newest',      max(updated_at),
      'oldest',      min(updated_at),
      /* Age of the STALEST record, in hours. The single number that answers "how old is the
         worst thing a student could be looking at right now". */
      'stalest_hours', round(extract(epoch from (now() - min(updated_at))) / 3600.0)::int,
      'stale_over_24h', count(*) filter (where updated_at < now() - interval '24 hours')
    ) as r
    from public.course_seats
    group by term
  ) s;
  return v;
end $$;
revoke all on function public.admin_pipeline() from public;
revoke execute on function public.admin_pipeline() from anon;
grant execute on function public.admin_pipeline() to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 4. Content and trust
-- ------------------------------------------------------------------------------------------------
-- Reviews by day and how many distinct students have written one — the contribution shape.
-- Reports by status. Neither returns review text or a reporter's identity.
create or replace function public.admin_trust(p_days int default 30)
returns jsonb language plpgsql security definer stable set search_path = public as $$
declare v jsonb; d interval;
begin
  perform public.admin_guard();
  d := make_interval(days => greatest(1, p_days));
  select jsonb_build_object(
    'reviews_total',    (select count(*) from public.reviews),
    'reviews_window',   (select count(*) from public.reviews where created_at > now() - d),
    /* Contributors, not reviews: ten reviews from one student is a very different product
       signal from ten students writing one each. */
    'reviewers',        (select count(distinct user_id) from public.reviews),
    'professors_rated', (select count(distinct professor_key) from public.reviews),
    'reviews_by_day', coalesce((
      select jsonb_agg(jsonb_build_object('day', day, 'n', c) order by day)
      from (select date_trunc('day', created_at)::date as day, count(*) c
            from public.reviews where created_at > now() - d group by 1) x), '[]'::jsonb),
    'reports', coalesce((
      select jsonb_agg(jsonb_build_object('status', status, 'n', c) order by c desc)
      from (select status, count(*) c from public.reports group by 1) y), '[]'::jsonb),
    'reports_open',     (select count(*) from public.reports where status = 'open')
  ) into v;
  return v;
end $$;
revoke all on function public.admin_trust(int) from public;
revoke execute on function public.admin_trust(int) from anon;
grant execute on function public.admin_trust(int) to authenticated;
