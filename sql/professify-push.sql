-- ================================================================================================
-- PUSH — 8 September 2026
-- ================================================================================================
-- Three notifications, one pipe.
--
--   seat_open    a watched section goes from full to having a seat
--   waitlist     a watched section's waitlist drops to 3 or fewer — "see if you got off yet"
--   moved        a watched or enrolled section changes its meeting time, instructor or location
--   dropped      a watched or enrolled section stops appearing in the scrape at all
--   free         a starred friend's LAST class of the day ends
--
-- WHY AN OUTBOX AND NOT A DIRECT SEND. A trigger cannot make an HTTP request without pg_net, and
-- a trigger that CAN make one is a trigger that can hang the scraper's 500-row upsert behind a
-- push service. So the triggers only ever write a row. A scheduled function drains the outbox and
-- does the sending, where a failure is a retry rather than a lost seat scrape.
--
-- WHAT THIS FILE DOES NOT DO: send anything. That is the edge function (professify-push-send.ts),
-- which needs a VAPID key pair Tate generates — the private half must never pass through here.
--
-- Safe to re-run.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 1. Who to send to
-- ------------------------------------------------------------------------------------------------
create table if not exists public.push_subscriptions (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  endpoint    text not null unique,          -- the push service's URL for this browser
  p256dh      text not null,                 -- public key half of the browser's keypair
  auth        text not null,                 -- the shared secret half
  ua          text,
  created_at  timestamptz not null default now(),
  last_ok_at  timestamptz,
  fail_count  int not null default 0
);
create index if not exists push_subs_user_idx on public.push_subscriptions(user_id);

alter table public.push_subscriptions enable row level security;

do $$
begin
  -- drop by SHAPE, not by name. Five separate times on this project a permissive policy under a
  -- name no migration mentioned survived every migration and quietly decided the outcome.
  perform 1;
  execute (
    select coalesce(string_agg(format('drop policy %I on public.push_subscriptions;', polname), ' '), '')
      from pg_policy where polrelid = 'public.push_subscriptions'::regclass);
end $$;

create policy push_subs_own_select on public.push_subscriptions
  for select to authenticated using (user_id = auth.uid());
create policy push_subs_own_insert on public.push_subscriptions
  for insert to authenticated with check (user_id = auth.uid());
create policy push_subs_own_delete on public.push_subscriptions
  for delete to authenticated using (user_id = auth.uid());
-- deliberately no UPDATE policy: a browser re-subscribing inserts a new endpoint and deletes the
-- old one. Nothing legitimate needs to rewrite somebody's keys in place.

revoke all on public.push_subscriptions from anon;


-- ------------------------------------------------------------------------------------------------
-- 2. What they want, and when they do not want it
-- ------------------------------------------------------------------------------------------------
create table if not exists public.push_prefs (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  seats      boolean  not null default true,   -- you asked for the alert by watching the section
  friends    boolean  not null default false,  -- OPT IN: nobody asked to hear about other people
  quiet_from smallint not null default 22,     -- local hour, inclusive
  quiet_to   smallint not null default 8,      -- local hour, exclusive
  constraint push_prefs_quiet_from_hour check (quiet_from between 0 and 23),
  constraint push_prefs_quiet_to_hour   check (quiet_to   between 0 and 23)
);
alter table public.push_prefs enable row level security;
do $$
begin
  execute (
    select coalesce(string_agg(format('drop policy %I on public.push_prefs;', polname), ' '), '')
      from pg_policy where polrelid = 'public.push_prefs'::regclass);
end $$;
create policy push_prefs_own on public.push_prefs
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
revoke all on public.push_prefs from anon;


-- ------------------------------------------------------------------------------------------------
-- 3. The outbox
-- ------------------------------------------------------------------------------------------------
create table if not exists public.push_outbox (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  kind        text not null,
  title       text not null,
  body        text not null,
  url         text not null default '/',
  tag         text,
  dedupe_key  text not null,
  created_at  timestamptz not null default now(),
  send_after  timestamptz not null default now(),
  sent_at     timestamptz,
  attempts    int not null default 0,
  last_error  text
);
-- One row per (person, thing that happened). A seat that flickers open and shut four times in an
-- afternoon is one notification, not four.
create unique index if not exists push_outbox_dedupe_idx
  on public.push_outbox(user_id, dedupe_key);
create index if not exists push_outbox_pending_idx
  on public.push_outbox(send_after) where sent_at is null;

alter table public.push_outbox enable row level security;
-- No policies at all, deliberately: RLS with zero policies denies everything to everyone except
-- the owner and SECURITY DEFINER functions. Nothing reads this table from the app. A student
-- cannot read their own queue, which matters because a "moved" row names a section somebody else
-- is watching only if they are watching it too — and there is no reason to hand out the shape of
-- the queue to find out.
revoke all on public.push_outbox from anon, authenticated;


-- ------------------------------------------------------------------------------------------------
-- 4. Enqueue: the one door in
-- ------------------------------------------------------------------------------------------------
-- Quiet hours DELAY, they do not drop. A seat that opens at 2am is still a seat at 8am, and the
-- student who set the watch would rather hear late than not at all. The one thing they must not
-- get is a phone lighting up at 2am.
-- The quiet-hours arithmetic, on its own and with a name, because it is the part of this file
-- that was wrong. Returns the instant to fire at if `p_local` falls inside the window, or NULL if
-- it does not — so the caller reads as `coalesce(push_fire_at(...), now())` and the "not quiet"
-- case is something a test can assert on rather than a clock reading.
--
-- p_local is LA WALL TIME with no zone. Handing it a timestamptz is the bug this had.
create or replace function public.push_fire_at(p_local timestamp, p_from smallint, p_to smallint)
returns timestamptz
language sql
immutable
as $fn$
  select case
    when p_from = p_to then null                       -- empty window: never quiet
    when (p_from > p_to and (extract(hour from p_local)::int >= p_from
                          or extract(hour from p_local)::int <  p_to))
      or (p_from < p_to and  extract(hour from p_local)::int >= p_from
                         and extract(hour from p_local)::int <  p_to)
    then (date_trunc('day', p_local)
          + make_interval(days  => case when extract(hour from p_local)::int >= p_to then 1 else 0 end)
          + make_interval(hours => p_to)) at time zone 'America/Los_Angeles'
    else null
  end
$fn$;

create or replace function public.push_enqueue(
  p_user uuid, p_kind text, p_title text, p_body text,
  p_url text, p_tag text, p_dedupe text)
returns boolean
language plpgsql
security definer
set search_path = public
as $fn$
declare
  pref     public.push_prefs%rowtype;
  want     boolean;
  /* timestamp, NOT timestamptz, and this cost an hour. `now() at time zone 'America/Los_Angeles'`
     yields a timestamp WITHOUT a zone — LA wall time. Assigning that to a timestamptz makes
     Postgres re-read the wall clock as if it were the SESSION zone (UTC on Supabase), so every
     later date_trunc and extract silently worked in the wrong zone and quiet hours produced a
     send_after in the PAST — which does not delay anything, it sends immediately. A quiet-hours
     feature that is a no-op is worse than none, because you believe it is on. */
  local_ts timestamp;
  fire_at  timestamptz;
begin
  if p_user is null or p_kind is null or p_dedupe is null then return false; end if;

  select * into pref from public.push_prefs where user_id = p_user;
  if not found then
    -- no row yet: seats on (you asked by watching), friends off (nobody asked)
    pref.seats := true; pref.friends := false; pref.quiet_from := 22; pref.quiet_to := 8;
  end if;

  want := case
            when p_kind in ('seat_open','waitlist','moved','dropped') then pref.seats
            when p_kind = 'free'                                      then pref.friends
            else false                                                        -- unknown kind: no
          end;
  if not want then return false; end if;

  -- Cal Poly is in one timezone and so is every student at it. Hard-coding it is honest here;
  -- a per-user timezone would be a column nobody fills in.
  local_ts := now() at time zone 'America/Los_Angeles';

  fire_at := coalesce(public.push_fire_at(local_ts, pref.quiet_from, pref.quiet_to), now());

  insert into public.push_outbox(user_id, kind, title, body, url, tag, dedupe_key, send_after)
  values (p_user, p_kind, left(p_title,120), left(p_body,200),
          coalesce(nullif(left(p_url,200),''),'/'), left(p_tag,80), left(p_dedupe,200), fire_at)
  on conflict (user_id, dedupe_key) do nothing;

  return found;
end;
$fn$;

revoke all on function public.push_enqueue(uuid,text,text,text,text,text,text) from public, anon, authenticated;
revoke all on function public.push_fire_at(timestamp,smallint,smallint) from public;


-- ------------------------------------------------------------------------------------------------
-- 5. The seat triggers
-- ------------------------------------------------------------------------------------------------
-- The scraper writes with POST ...?on_conflict=term,class_nbr and Prefer: resolution=merge-
-- duplicates, i.e. INSERT ... ON CONFLICT DO UPDATE. So UPDATE triggers fire on every existing
-- row, ~6,900 of them per run. Everything below is written to cost nothing on the ~99% of rows
-- where nothing interesting changed: the WHEN clause is evaluated before the function body, and
-- the body only runs a query when a threshold was actually crossed.
--
-- `room` is NOT checked. It exists as a column and is empty in all 6,969 rows, so a rule about it
-- would be a rule that can never fire — worse than no rule, because it reads like coverage.
create or replace function public.push_on_seat_change()
returns trigger
language plpgsql
security definer
set search_path = public
as $fn$
declare
  label text;
  n     int := 0;
  w     record;
begin
  label := coalesce(NEW.course_code,'') || case when NEW.section is null or NEW.section='' then ''
                                                else ' §'||NEW.section end;

  -- (a) a seat opened. `available <= 0` and not `= 0` because a scrape can report negative.
  if coalesce(OLD.available,0) <= 0 and coalesce(NEW.available,0) > 0 then
    for w in select user_id from public.watch_sections where class_nbr = NEW.class_nbr loop
      perform public.push_enqueue(
        w.user_id, 'seat_open',
        label || ' has a seat',
        case when NEW.available = 1 then 'One seat just opened. They go fast.'
             else NEW.available || ' seats just opened.' end,
        '/?tab=sched', 'seat-'||NEW.class_nbr,
        'seat_open:'||NEW.class_nbr||':'||to_char(now() at time zone 'America/Los_Angeles','YYYY-MM-DD'));
      n := n + 1;
    end loop;
  end if;

  -- (b) the waitlist got short. Fires on the CROSSING, so a section that sits at 2 all week is
  --     one notification, not one per scrape.
  --     The wording is deliberately about the LIST, not the student's place in it: Cal Poly does
  --     not publish anybody's position and this app does not know it. "You are 3rd" would be a
  --     number we made up. "The waitlist is down to 3" is a number we have.
  if coalesce(OLD.waitlist_total, 999) > 3 and coalesce(NEW.waitlist_total, 999) <= 3 then
    for w in select user_id from public.watch_sections where class_nbr = NEW.class_nbr loop
      perform public.push_enqueue(
        w.user_id, 'waitlist',
        label || ' waitlist is down to ' || coalesce(NEW.waitlist_total,0),
        'Worth checking whether you got in.',
        '/?tab=sched', 'wl-'||NEW.class_nbr,
        'waitlist:'||NEW.class_nbr||':'||to_char(now() at time zone 'America/Los_Angeles','YYYY-MM-DD'));
      n := n + 1;
    end loop;
  end if;

  -- (c) it moved. Matters most to somebody already enrolled — it breaks a schedule they built —
  --     so this one fans out to my_sections as well as watch_sections.
  if (OLD.days       is distinct from NEW.days)
  or (OLD.instructor is distinct from NEW.instructor)
  or (OLD.location   is distinct from NEW.location) then
    for w in
      select user_id from public.watch_sections where class_nbr = NEW.class_nbr
      union
      select user_id from public.my_sections    where class_nbr = NEW.class_nbr
    loop
      perform public.push_enqueue(
        w.user_id, 'moved',
        label || ' changed',
        case when OLD.days is distinct from NEW.days
               then 'Now ' || coalesce(NEW.days,'unscheduled') || '. Check your week.'
             when OLD.instructor is distinct from NEW.instructor
               then 'Now taught by ' || coalesce(NEW.instructor,'someone else') || '.'
             else 'The location changed.' end,
        '/?tab=sched', 'moved-'||NEW.class_nbr,
        'moved:'||NEW.class_nbr||':'||md5(coalesce(NEW.days,'')||'|'||coalesce(NEW.instructor,'')||'|'||coalesce(NEW.location,'')));
      n := n + 1;
    end loop;
  end if;

  return NEW;
end;
$fn$;

drop trigger if exists push_seat_change on public.course_seats;
create trigger push_seat_change
  after update on public.course_seats
  for each row
  when (OLD.available     is distinct from NEW.available
     or OLD.waitlist_total is distinct from NEW.waitlist_total
     or OLD.days           is distinct from NEW.days
     or OLD.instructor     is distinct from NEW.instructor
     or OLD.location       is distinct from NEW.location)
  execute function public.push_on_seat_change();


-- ------------------------------------------------------------------------------------------------
-- 6. Sections that stopped existing
-- ------------------------------------------------------------------------------------------------
-- A cancelled section does not change — it stops being written. The scraper only ever upserts, so
-- a section Cal Poly removed keeps its last row and its updated_at falls behind. On production
-- right now 439 of 6,969 rows are more than 36 hours behind the latest scrape; those are the ones
-- that stopped appearing.
--
-- Nothing fires for this, so it needs a sweep. Call it from the same schedule that drains the
-- outbox — it is cheap and idempotent (the dedupe key is per section per day).
create or replace function public.push_sweep_dropped()
returns integer   -- how many were actually QUEUED, not how many matched
language plpgsql
security definer
set search_path = public
as $fn$
declare
  latest timestamptz;
  r      record;
  n      int := 0;
begin
  select max(updated_at) into latest from public.course_seats;
  if latest is null then return 0; end if;
  -- If the scraper itself has been down, EVERY row is stale and this would tell every student
  -- their whole schedule was cancelled. Refuse to run rather than send that.
  if latest < now() - interval '36 hours' then
    raise notice 'scrape is % old — refusing to report dropped sections', now() - latest;
    return 0;
  end if;

  for r in
    select c.class_nbr, c.course_code, c.section, u.user_id
      from public.course_seats c
      join (select class_nbr, user_id from public.watch_sections
            union
            select class_nbr, user_id from public.my_sections) u
        on u.class_nbr = c.class_nbr
     where c.updated_at < latest - interval '36 hours'
  loop
    if public.push_enqueue(
      r.user_id, 'dropped',
      coalesce(r.course_code,'A section') ||
        case when r.section is null or r.section='' then '' else ' §'||r.section end ||
        ' is gone from the schedule',
      'It stopped appearing in Cal Poly''s listing. You may need another section.',
      '/?tab=sched', 'dropped-'||r.class_nbr,
      'dropped:'||r.class_nbr)
    then n := n + 1; end if;
  end loop;
  return n;
end;
$fn$;


-- ------------------------------------------------------------------------------------------------
-- 7. "Done for the day"
-- ------------------------------------------------------------------------------------------------
-- The version of this that says "Willow is free" was deliberately removed on 5 September, and the
-- note left in the client says why: a timetable can show that nothing is scheduled, but only a
-- person can say they are free. This is the half a timetable CAN prove — their last class of the
-- day has ended — and it is stated as exactly that, in those words. Nobody has to declare
-- anything, so there is no control to bring back.
--
-- Parsing the meeting string in SQL: it looks like 'Fr 1:00PM - 1:50PM', sometimes with a trailing
-- TBA. The day codes are the run before the first space; the end time is the second clock time.
-- Anything that does not match (a genuinely TBA section, an async one) yields NULL and is skipped
-- rather than guessed at.
create or replace function public.push_day_code(p_when timestamptz default now())
returns text
language sql
immutable
as $fn$
  select (array['Su','Mo','Tu','We','Th','Fr','Sa'])[
           extract(dow from (p_when at time zone 'America/Los_Angeles'))::int + 1]
$fn$;

create or replace function public.push_meets_on(p_days text, p_code text)
returns boolean
language sql
immutable
as $fn$
  -- only the day-code run, so a time like '10:00AM' can never be read as a day
  select coalesce(position(p_code in split_part(coalesce(p_days,''), ' ', 1)) > 0, false)
$fn$;

create or replace function public.push_end_time(p_days text)
returns time
language plpgsql
immutable
as $fn$
declare t text;
begin
  t := substring(coalesce(p_days,'') from '-[[:space:]]*([0-9]{1,2}:[0-9]{2}[[:space:]]*[AaPp][Mm])');
  if t is null then return null; end if;
  return to_timestamp(upper(replace(t,' ','')), 'HH12:MIAM')::time;
exception when others then
  return null;   -- an unparseable string is not a class that just ended
end;
$fn$;

-- Fires for a starred friend whose last class of the day ended inside the window. The window is
-- the sweep interval: call this every 15 minutes and pass 20 so a run that starts late still
-- catches it, with the per-day dedupe key stopping the overlap from sending twice.
create or replace function public.push_sweep_done_for_day(p_window_min int default 20)
returns integer   -- how many were actually QUEUED, not how many matched
language plpgsql
security definer
set search_path = public
as $fn$
declare
  /* v_ prefixed, and that is not style. `code` collided with my_sections.code and plpgsql
     resolved the reference to the VARIABLE inside the query, so the day filter silently compared
     every row against the same value. Same trap as `conname` against pg_constraint earlier in
     this project: a local whose name is also a column of a table the query touches. */
  v_code  text := public.push_day_code();
  v_now   timestamp := (now() at time zone 'America/Los_Angeles');
  v_today date := v_now::date;
  r       record;
  n       int := 0;
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='profiles' and column_name='pinned_friends')
  then
    raise notice 'no pinned_friends column on this deploy — nothing to sweep';
    return 0;
  end if;

  for r in
    with starred as (
      -- who has starred whom. The pinned array is the intent; friend_requests is the fact —
      -- a stale id left in somebody's pins after unfriending must not keep pushing.
      select p.id as watcher, f.fid as friend
        from public.profiles p
        cross join lateral unnest(coalesce(p.pinned_friends, '{}')::text[]) as f(fid)
       where exists (
         select 1 from public.friend_requests fr
          where fr.status = 'accepted'
            and ((fr.from_user = p.id and fr.to_user::text = f.fid)
              or (fr.to_user   = p.id and fr.from_user::text = f.fid)))
    ),
    last_class as (
      select s.user_id, max(public.push_end_time(s.days)) as ends
        from public.my_sections s
       where public.push_meets_on(s.days, v_code)
         and public.push_end_time(s.days) is not null
       group by s.user_id
    )
    select st.watcher, st.friend, lc.ends,
           coalesce(pf.display_name, 'A friend') as who
      from starred st
      join last_class lc on lc.user_id::text = st.friend
      left join public.profiles pf on pf.id::text = st.friend
     where lc.ends <= v_now::time
       and lc.ends >  (v_now - make_interval(mins => greatest(p_window_min,1)))::time
  loop
    if public.push_enqueue(
      r.watcher, 'free',
      r.who || ' is done for the day',
      'Their last class ended at ' || to_char(r.ends, 'FMHH12:MIam') || '.',
      '/?tab=friends', 'free-'||r.friend,
      'free:'||r.friend||':'||v_today::text)
    then n := n + 1; end if;
  end loop;
  return n;
end;
$fn$;

revoke all on function public.push_sweep_dropped()          from public, anon, authenticated;
revoke all on function public.push_sweep_done_for_day(int)  from public, anon, authenticated;
revoke all on function public.push_day_code(timestamptz)    from public;
revoke all on function public.push_meets_on(text,text)      from public;
revoke all on function public.push_end_time(text)           from public;


-- ------------------------------------------------------------------------------------------------
-- 8. SELF-CHECK
-- ------------------------------------------------------------------------------------------------
do $$
declare bad int := 0; t time;
begin
  -- the meeting-string parser, on the shapes that are actually in course_seats
  t := public.push_end_time('Fr 1:00PM - 1:50PM');
  if t is distinct from time '13:50' then raise notice 'parse FAIL simple: %', t; bad := bad+1; end if;
  t := public.push_end_time('MoWeFr 9:10AM - 10:00AM TBA');
  if t is distinct from time '10:00' then raise notice 'parse FAIL trailing TBA: %', t; bad := bad+1; end if;
  t := public.push_end_time('TuTh 12:10PM - 1:30PM');
  if t is distinct from time '13:30' then raise notice 'parse FAIL pm: %', t; bad := bad+1; end if;
  if public.push_end_time('TBA') is not null then raise notice 'parse FAIL: TBA should be null'; bad := bad+1; end if;
  if public.push_end_time(null)  is not null then raise notice 'parse FAIL: null should be null'; bad := bad+1; end if;

  -- day matching must read the day codes, never the clock
  if not public.push_meets_on('TuTh 12:10PM - 1:30PM','Tu') then raise notice 'day FAIL Tu'; bad := bad+1; end if;
  if not public.push_meets_on('TuTh 12:10PM - 1:30PM','Th') then raise notice 'day FAIL Th'; bad := bad+1; end if;
  if     public.push_meets_on('TuTh 12:10PM - 1:30PM','Mo') then raise notice 'day FAIL Mo'; bad := bad+1; end if;
  -- 'Mo' does not appear in the codes here, but 'M' does appear in '12:10PM' — the split is what
  -- stops the clock being read as a day, and this is the case that proves it
  if     public.push_meets_on('Fr 1:00PM - 1:50PM','Mo')    then raise notice 'day FAIL PM-as-Monday'; bad := bad+1; end if;
  if     public.push_meets_on('Fr 1:00AM - 1:50AM','Sa')    then raise notice 'day FAIL AM-as-Saturday'; bad := bad+1; end if;

  -- QUIET HOURS MUST DELAY INTO THE FUTURE, and into the RIGHT day. The first version declared
  -- the wall-clock variable as timestamptz, so LA time was re-read as UTC and send_after landed
  -- in the past — which does not delay anything, it sends immediately while looking configured.
  if public.push_fire_at(timestamp '2026-01-15 23:30', 22::smallint, 8::smallint)
     is distinct from (timestamp '2026-01-16 08:00' at time zone 'America/Los_Angeles') then
    raise notice 'quiet FAIL late night should wake at 8am NEXT day: %',
      public.push_fire_at(timestamp '2026-01-15 23:30', 22::smallint, 8::smallint); bad := bad+1;
  end if;
  if public.push_fire_at(timestamp '2026-01-15 03:00', 22::smallint, 8::smallint)
     is distinct from (timestamp '2026-01-15 08:00' at time zone 'America/Los_Angeles') then
    raise notice 'quiet FAIL small hours should wake at 8am SAME day'; bad := bad+1;
  end if;
  if public.push_fire_at(timestamp '2026-01-15 14:00', 22::smallint, 8::smallint) is not null then
    raise notice 'quiet FAIL 2pm is not quiet'; bad := bad+1;
  end if;
  -- a window that does NOT cross midnight must not silence the rest of the day
  if public.push_fire_at(timestamp '2026-01-15 14:00', 13::smallint, 15::smallint)
     is distinct from (timestamp '2026-01-15 15:00' at time zone 'America/Los_Angeles') then
    raise notice 'quiet FAIL same-day window'; bad := bad+1;
  end if;
  if public.push_fire_at(timestamp '2026-01-15 16:00', 13::smallint, 15::smallint) is not null then
    raise notice 'quiet FAIL after a same-day window it is not quiet'; bad := bad+1;
  end if;
  if public.push_fire_at(timestamp '2026-01-15 03:00', 0::smallint, 0::smallint) is not null then
    raise notice 'quiet FAIL an empty window means never quiet'; bad := bad+1;
  end if;

  -- an unknown kind must never be sent, whatever the prefs say
  if public.push_enqueue('00000000-0000-0000-0000-000000000000'::uuid,
       'not_a_kind','x','y','/','t','selfcheck-unknown-kind') then
    raise notice 'enqueue FAIL: accepted an unknown kind'; bad := bad+1;
  end if;

  if bad > 0 then raise exception '% self-check failure(s) above', bad; end if;
  raise notice 'OK — meeting strings parse, day codes do not read the clock, quiet hours delay forward, unknown kinds are dropped';
end $$;

-- What is queued right now, and what the triggers are attached to. Read-only.
select 'outbox pending' as k, count(*)::text as v from public.push_outbox where sent_at is null
union all
select 'subscriptions', count(*)::text from public.push_subscriptions
union all
select 'watch_sections rows (seat alerts reach these)', count(*)::text from public.watch_sections
union all
select 'my_sections rows (moved/dropped reach these)', count(*)::text from public.my_sections
union all
select 'trigger on course_seats', count(*)::text from pg_trigger
 where tgname = 'push_seat_change' and not tgisinternal
 order by 1;
