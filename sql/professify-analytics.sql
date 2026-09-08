-- ================================================================================================
-- ANALYTICS, WITHOUT BUILDING A FILE ON EVERY STUDENT — 2026-09-07
-- ================================================================================================
-- Professify has had no analytics of any kind. This adds the smallest thing that answers the two
-- questions actually being asked: what do students do here, and which professors are people
-- looking at right now.
--
-- THE DECISION THAT SHAPES EVERYTHING ELSE: these events carry NO user id.
--
-- The obvious schema is (user_id, event, professor, timestamp). That schema is a browsing history
-- of named students against named professors at one small school — "who looked up Professor Kearns
-- eleven times" — and it would sit in the same database as reviews the app promises are anonymous.
-- It is the kind of table that is fine until the day it isn't: a leak, a subpoena, a curious admin.
-- Professify does not need it. Ranking by "how many different people looked" needs a way to tell
-- two people apart, not a way to name them.
--
-- So each event carries `who`: a rotating pseudonym the browser computes as
--     sha256(<random salt kept on this device>  +  <today's UTC date>)
-- It is stable for one day, so twelve refreshes count once. It is different tomorrow, so nothing
-- can be joined across days into a profile. Nobody — including the database owner — can turn one
-- back into a student.
--
-- WHAT IS COUNTED, and it is worth being able to say this in one line, because the Privacy Policy
-- has to: which professor pages were opened, which were shown on screen, and which surface they
-- were opened from. Not what you typed, not what you read, not who you are.
--
-- Impressions are logged as well as opens on purpose. Ranking by raw clicks measures POSITION, not
-- interest — whatever sits at the top is clicked because it is at the top, and within a few weeks
-- the ranking is measuring itself. Clicks ÷ times-shown does not have that problem. The trending
-- strip this ships with is a plain viewer count, because that is exactly what its label claims, but
-- the denominator is there from day one so a rate-based ranking is possible later without a
-- migration and without a gap in the data.
--
-- Safe to re-run.
-- ================================================================================================

-- ------------------------------------------------------------------------------------------------
-- 1. The table
-- ------------------------------------------------------------------------------------------------
create table if not exists public.events (
  id      bigint generated always as identity primary key,
  at      timestamptz not null default now(),
  name    text not null,
  subject text,          -- professor key or course code, whatever the event is about
  surface text,          -- where it happened: explore | home | search | friend | prof
  who     text not null  -- the rotating daily pseudonym. NOT a user id. See the header.
);

create index if not exists events_at_idx      on public.events (at desc);
create index if not exists events_subject_idx on public.events (subject, at desc) where subject is not null;

alter table public.events enable row level security;

-- No policies at all, and that is deliberate: RLS with zero policies denies everything to everyone
-- except the table owner and SECURITY DEFINER functions. Nothing reads or writes this table
-- directly — writes go through log_events(), reads go through the aggregate views below. A student
-- cannot read the event log, and neither can a signed-out visitor.
revoke all on public.events from anon, public, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 2. Writing: one batched call, validated server-side
-- ------------------------------------------------------------------------------------------------
-- Rendering a list of 24 professors produces 24 impressions. Twenty-four inserts per render is
-- absurd, so the browser batches and this takes an array.
--
-- WHAT THE LIMITS HERE DO AND DO NOT DO. The event name whitelist and the length caps stop this
-- from becoming a free-text store that quietly accumulates whatever a future call passes. The
-- per-`who` daily cap stops one browser flooding the table. The hourly ceiling is a circuit
-- breaker so a bad loop or a script cannot fill the disk overnight.
--
-- What they do NOT stop: `who` comes from the browser, so somebody determined can send a fresh
-- pseudonym per request and inflate a professor's viewer count. That is the price of not
-- identifying anybody, and it is the right trade here — the payoff for the attack is "a professor
-- appears in a strip on a student website". If it ever matters, the fix is a signed token from an
-- edge function, not a user id in this table.
create or replace function public.log_events(p_batch jsonb)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  e         jsonb;
  n         integer := 0;
  who_id    text;
  ev_name   text;
  recent    bigint;
begin
  if p_batch is null or jsonb_typeof(p_batch) <> 'array' then
    return 0;                                  -- malformed input is dropped, never raised: a
  end if;                                      -- analytics call must not break the page it is on
  if jsonb_array_length(p_batch) = 0 then return 0; end if;
  if jsonb_array_length(p_batch) > 60 then return 0; end if;

  who_id := left(coalesce(p_batch->0->>'who', ''), 32);
  if who_id !~ '^[0-9a-f]{16,32}$' then
    return 0;                                  -- not a pseudonym this app produced
  end if;

  -- Circuit breaker. 5k events an hour is roughly a hundred times anything this app can currently
  -- produce, and it is what bounds the disk. The arithmetic matters on a 500MB free tier: at the
  -- old 20k/hour ceiling, thirty days of sustained abuse is ~14M rows and well over a gigabyte —
  -- a ceiling that lets you run out of disk is not a ceiling. Paired with the row cap in the
  -- retention step below, the worst case is now bounded at roughly 100MB.
  select count(*) into recent from public.events where at > now() - interval '1 hour';
  if recent > 5000 then return 0; end if;

  -- Per-browser daily cap.
  select count(*) into recent from public.events
   where who = who_id and at > now() - interval '1 day';
  if recent > 2000 then return 0; end if;

  for e in select * from jsonb_array_elements(p_batch)
  loop
    ev_name := left(coalesce(e->>'name',''), 40);
    if ev_name in ('prof_view','prof_impression','class_view','class_impression',
                   'search','rate_open','rate_submit','signup','app_open',
                   -- 'error' added 2026-09-07. There was no error reporting at all: ~900 empty
                   -- catch blocks and no way to know the app was broken except somebody opening
                   -- it. This reuses the events pipe rather than adding a third party, so the
                   -- same "no identity, 30-day retention" rules apply to crashes as to clicks.
                   -- The browser sends a truncated message and nothing else.
                   'error')
    then
      insert into public.events (name, subject, surface, who)
      values (ev_name,
              nullif(left(coalesce(e->>'subject',''), 160), ''),
              nullif(left(coalesce(e->>'surface',''), 40), ''),
              who_id);
      n := n + 1;
    end if;
  end loop;

  -- Retention, done opportunistically so this needs no scheduler. Roughly one call in a hundred
  -- clears anything older than 30 days. Thirty days is longer than the trending window needs and
  -- short enough that the table cannot become a year of browsing behaviour.
  if random() < 0.01 then
    delete from public.events where at < now() - interval '30 days';
    -- And a hard ceiling on rows, independent of age. Retention by time alone assumes the traffic
    -- is what you expect; this holds even when it is not. A million rows is ~100MB and about six
    -- years of this app's realistic volume.
    delete from public.events
     where id < (select max(id) - 1000000 from public.events);
  end if;

  return n;
end;
$$;

-- Signed-out visitors browse professors too — guest discovery is a real surface — so anon writes.
-- `revoke ... from anon` alone would be a no-op: PostgreSQL grants EXECUTE to PUBLIC on a new
-- function automatically, so the revoke has to name public.
revoke all     on function public.log_events(jsonb) from public;
grant  execute on function public.log_events(jsonb) to anon, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 3. Reading: aggregates only, never rows
-- ------------------------------------------------------------------------------------------------
-- The only way anything outside this file sees the event log. Counts of distinct pseudonyms, no
-- `who` column, no timestamps, nothing per-person leaves.
create or replace view public.prof_activity_7d as
  select subject                                                     as prof_key,
         count(distinct who) filter (where name = 'prof_view')       as viewers,
         count(distinct who) filter (where name = 'prof_impression') as shown
    from public.events
   where at > now() - interval '7 days'
     and subject is not null
     and name in ('prof_view','prof_impression')
   group by subject;

revoke all on public.prof_activity_7d from anon, public, authenticated;
grant select on public.prof_activity_7d to anon, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 4. The trending strip
-- ------------------------------------------------------------------------------------------------
-- Distinct viewers, not clicks: twelve refreshes by one person is one viewer. That is also exactly
-- what the section's label claims, which is the whole reason to use this metric rather than a rate
-- here — a strip that says "looked at most this week" should be ordered by how many people looked.
--
-- p_min is the honesty threshold. Below it there is not enough data for the claim, and the right
-- answer is to return nothing so the app can hide the section — not to show a professor two people
-- glanced at and call them trending. On a campus app with a dozen users this will legitimately
-- return zero rows for a while, and that is the correct behaviour, not a bug.
create or replace function public.trending_profs(p_limit int default 12, p_min int default 5)
returns table (prof_key text, viewers bigint)
language sql
security definer
stable
set search_path = public
as $$
  select a.prof_key, a.viewers
    from public.prof_activity_7d a
   where a.viewers >= greatest(coalesce(p_min, 5), 3)   -- never below 3, whatever the caller asks
   order by a.viewers desc, a.prof_key
   limit least(coalesce(p_limit, 12), 40)
$$;

revoke all     on function public.trending_profs(int, int) from public;
grant  execute on function public.trending_profs(int, int) to anon, authenticated;


-- ------------------------------------------------------------------------------------------------
-- 5. A way to actually SEE it — moderators only
-- ------------------------------------------------------------------------------------------------
-- Analytics you cannot look at is a table that grows. This is the read side: one call, aggregates
-- only, gated on is_moderator() so it is the same handful of accounts that can already reach the
-- report queue. It returns counts and never rows — no `who` column crosses this boundary even for
-- a moderator, because there is nothing a moderator needs it for and the pseudonym is the one
-- thing in this design that must never become browsable.
--
-- Guarded on is_moderator() existing, so this file still installs on a deploy that has not run
-- professify-safety.sql — there it simply refuses everyone, which is the safe direction.
do $$
begin
  if to_regprocedure('public.is_moderator()') is null then
    raise notice 'is_moderator() not on this deploy — analytics_summary will refuse everyone until professify-safety.sql runs';
  end if;
end $$;

create or replace function public.analytics_summary(p_days int default 14)
returns jsonb
language plpgsql
security definer
stable
set search_path = public
as $$
declare
  d   int := least(greatest(coalesce(p_days, 14), 1), 90);
  res jsonb;
begin
  if to_regprocedure('public.is_moderator()') is null then
    raise exception 'not a moderator';
  end if;
  if not public.is_moderator() then
    raise exception 'not a moderator';
  end if;

  select jsonb_build_object(
    'days', d,
    'totals', (
      select jsonb_build_object(
        'events',  count(*),
        'people',  count(distinct who),          -- distinct daily pseudonyms, so this OVERSTATES
        'opens',   count(*) filter (where name='app_open'),
        'views',   count(*) filter (where name='prof_view')
      )                                          -- unique people across a multi-day window: one
      from public.events                         -- person over 14 days is up to 14 pseudonyms.
       where at > now() - make_interval(days => d)   -- Stated here so nobody reads it as a user count.
    ),
    'by_day', (
      select coalesce(jsonb_agg(x order by x->>'day'), '[]'::jsonb) from (
        select jsonb_build_object(
                 'day',    to_char(date_trunc('day', at), 'YYYY-MM-DD'),
                 'people', count(distinct who),
                 'views',  count(*) filter (where name='prof_view')
               ) as x
          from public.events
         where at > now() - make_interval(days => d)
         group by date_trunc('day', at)
      ) t
    ),
    'top_profs', (
      select coalesce(jsonb_agg(x order by (x->>'viewers')::int desc), '[]'::jsonb) from (
        select jsonb_build_object(
                 'prof_key', subject,
                 'viewers',  count(distinct who) filter (where name='prof_view'),
                 'shown',    count(distinct who) filter (where name='prof_impression')
               ) as x
          from public.events
         where at > now() - make_interval(days => d)
           and subject is not null and name in ('prof_view','prof_impression')
         group by subject
        having count(distinct who) filter (where name='prof_view') > 0
         order by count(distinct who) filter (where name='prof_view') desc
         limit 25
      ) t
    ),
    'errors', (
      select coalesce(jsonb_agg(x order by (x->>'hits')::int desc), '[]'::jsonb) from (
        select jsonb_build_object('message', subject, 'hits', count(*),
                                  'browsers', count(distinct who),
                                  'last', to_char(max(at), 'YYYY-MM-DD HH24:MI')) as x
          from public.events
         where at > now() - make_interval(days => d) and name = 'error' and subject is not null
         group by subject
         order by count(*) desc
         limit 20
      ) t
    ),
    'sources', (
      select coalesce(jsonb_agg(x order by (x->>'people')::int desc), '[]'::jsonb) from (
        select jsonb_build_object('source', coalesce(surface,'unknown'), 'people', count(distinct who)) as x
          from public.events
         where at > now() - make_interval(days => d) and name='app_open'
         group by surface
         order by count(distinct who) desc
         limit 15
      ) t
    )
  ) into res;

  return res;
end;
$$;

revoke all     on function public.analytics_summary(int) from public;
revoke execute on function public.analytics_summary(int) from anon;
grant  execute on function public.analytics_summary(int) to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 6. SELF-CHECK
-- ------------------------------------------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='events'
     and column_name in ('user_id','uid','email','ip','ip_address','user_agent');
  if n > 0 then
    raise exception 'events has an identifying column — the whole point of this table is that it does not';
  end if;

  if has_table_privilege('authenticated','public.events','SELECT') then
    raise exception 'authenticated can read public.events directly — it should only see the aggregate view';
  end if;
  if has_table_privilege('anon','public.events','SELECT') then
    raise exception 'anon can read public.events directly';
  end if;

  raise notice 'OK — events carries no identity, and nobody can read it row by row';
end $$;
