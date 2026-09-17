-- ================================================================================================
-- EVENTS v2 — every click, and enough context to know why it mattered — 2026-09-14
-- ================================================================================================
-- Tate: "every click should be documented at first so we can find out everything from the start",
-- and "I want to eventually connect a 3rd party analytics tool".
--
-- Two columns, and the reasons are different.
--
-- `props`  — a small jsonb bag. A click is not one fact, it is several: what was clicked, whether
--            anything was actually there, how long the page had been visible, how far down it was.
--            Adding a column per fact means a migration every time a question changes; a bag means
--            the question can change without the schema moving.
--
-- `session` — a random id generated per page load. THIS IS NOT A PERSON. It cannot be joined to
--            anything, it dies when the tab does, and it exists because the interesting questions
--            are session-shaped: what did they look at before they left, did this visit end in a
--            save or an exit, did they open the same class three times while deciding. The
--            person-level identifier still rotates daily and still cannot be joined across days.
--            That was a deliberate choice and nothing here undoes it.
--
-- THE ENVELOPE IS TOOL-AGNOSTIC ON PURPOSE. {name, props, surface, session, at} is exactly how
-- PostHog, Amplitude and Mixpanel model an event, so connecting one later is a view over this
-- table rather than a second instrumentation pass. Two pipelines always drift, and then there are
-- two numbers and no truth.
--
-- VOLUME, redone for click logging rather than page views.
-- The old ceiling was 5,000 events an hour, sized for a few professor opens per visit. Logging
-- every click is a different order: a student in a ten-minute session generates 100-300 clicks.
-- Twenty-four students doing that in one hour is ~5,000 events — the old cap, reached on the
-- quietest possible day, and once it trips the app silently stops recording ANYTHING, which is
-- worse than not having the data because it looks like nobody was there.
--
-- So the hourly ceiling moves to 40,000 and the per-browser daily cap to 6,000. The arithmetic
-- that bounds it: a click row with props is ~220 bytes, so 40,000/hour sustained is ~200MB a day
-- — which the 30-day retention alone would NOT save you from. The million-row ceiling already in
-- log_events is what actually holds the line at roughly 220MB, and it is the reason these numbers
-- can move at all. Client-side sampling is the real throttle; these are the guard rail behind it.
--
-- Safe to re-run.
-- ================================================================================================

alter table public.events add column if not exists props   jsonb;
alter table public.events add column if not exists session text;

-- The console asks "how many of event X in the last N days", constantly. Without this it is a
-- sequential scan over every row the app has ever written.
create index if not exists events_name_at_idx on public.events (name, at desc);
-- And session-shaped questions ("what happened in the visit that ended in a save") walk one
-- session in order.
create index if not exists events_session_idx on public.events (session, at) where session is not null;

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
  ev_sess   text;
  ev_props  jsonb;
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

  -- See the header for why these moved. They are a guard rail, not a throttle: the client samples.
  select count(*) into recent from public.events where at > now() - interval '1 hour';
  if recent > 40000 then return 0; end if;

  select count(*) into recent from public.events
   where who = who_id and at > now() - interval '1 day';
  if recent > 6000 then return 0; end if;

  for e in select * from jsonb_array_elements(p_batch)
  loop
    ev_name := left(coalesce(e->>'name',''), 40);
    if ev_name = '' then continue; end if;

    -- A session id this app produced, or nothing. Anything else is discarded rather than stored,
    -- because an unvalidated free-text column is how a analytics table becomes a place to put
    -- things that should not be in it.
    ev_sess := left(coalesce(e->>'session',''), 32);
    if ev_sess !~ '^[0-9a-z]{8,32}$' then ev_sess := null; end if;

    -- props is capped hard. It is a bag for small facts — a label, a count, a depth — and not a
    -- place for page text, a search query someone typed, or anything else that would turn an
    -- anonymous event stream into a record of what a named-ish browser read.
    ev_props := case when jsonb_typeof(e->'props') = 'object'
                       and length(e->>'props') <= 600
                     then e->'props' else null end;

    insert into public.events(name, subject, surface, who, props, session)
    values (ev_name,
            left(nullif(e->>'subject',''), 160),
            left(nullif(e->>'surface',''), 40),
            who_id,
            ev_props,
            ev_sess);
    n := n + 1;
  end loop;

  if random() < 0.02 then
    delete from public.events where at < now() - interval '30 days';
    delete from public.events
     where id < (select max(id) - 1000000 from public.events);
  end if;

  return n;
end;
$$;

-- ------------------------------------------------------------------------------------------------
-- The behaviour summary the console reads. Moderator-only, aggregate-only.
-- ------------------------------------------------------------------------------------------------
-- Every number here is a count over SESSIONS or over events, never over people. Nothing in it can
-- be narrowed to one browser, and there is no function anywhere that returns one session's trail.
create or replace function public.admin_behaviour(p_days int default 14)
returns jsonb language plpgsql security definer stable set search_path = public as $$
declare v jsonb; d interval;
begin
  perform public.admin_guard();
  d := make_interval(days => greatest(1, p_days));
  select jsonb_build_object(
    'sessions', (select count(distinct session) from public.events where session is not null and at > now() - d),

    -- WHAT GOT CLICKED. Ranked by how many distinct sessions clicked it, not raw clicks: one
    -- person mashing a button is not the same signal as forty people finding it.
    'clicks', coalesce((
      select jsonb_agg(jsonb_build_object('target', target, 'sessions', s, 'clicks', c) order by s desc)
      from (select coalesce(props->>'target','(unnamed)') target,
                   count(distinct session) s, count(*) c
            from public.events where name='click' and at > now() - d
            group by 1 order by 2 desc limit 30) x), '[]'::jsonb),

    -- DEAD CLICKS: a tap that resolved to nothing interactive. The closest thing to a direct
    -- answer to "why did they leave" that any of this can produce.
    'dead_clicks', coalesce((
      select jsonb_agg(jsonb_build_object('surface', surface, 'n', c, 'sessions', s) order by c desc)
      from (select surface, count(*) c, count(distinct session) s
            from public.events where name='dead_click' and at > now() - d
            group by 1 order by 2 desc limit 15) y), '[]'::jsonb),

    -- WHERE SESSIONS ENDED, and what the person did last before they went.
    'exits', coalesce((
      select jsonb_agg(jsonb_build_object('surface', surface, 'last', last_action,
                                          'n', c, 'median_dwell_s', med) order by c desc)
      from (select surface, coalesce(props->>'last','(nothing)') last_action, count(*) c,
                   round(percentile_cont(0.5) within group
                     (order by coalesce((props->>'dwell')::numeric,0))/1000.0)::int med
            from public.events where name='page_exit' and at > now() - d
            group by 1,2 order by 3 desc limit 20) z), '[]'::jsonb),

    -- EMPTY STATES: every one is a question the product failed to answer, ranked by demand.
    'empty', coalesce((
      select jsonb_agg(jsonb_build_object('what', coalesce(props->>'what','?'), 'n', c) order by c desc)
      from (select props, count(*) c from public.events
            where name='empty_state' and at > now() - d group by 1 order by 2 desc limit 15) w), '[]'::jsonb),

    -- SEARCHES THAT FOUND NOTHING. Not a UX problem — a DATA problem, and it names the record to add.
    'no_results', coalesce((
      select jsonb_agg(jsonb_build_object('surface', surface, 'n', c) order by c desc)
      from (select surface, count(*) c from public.events
            where name='search_empty' and at > now() - d group by 1 order by 2 desc limit 10) q), '[]'::jsonb),

    -- RAGE: three or more taps in the same place inside two seconds.
    'rage', (select count(*) from public.events where name='rage_click' and at > now() - d),

    -- Installed-as-an-app versus a browser tab. They behave like different products.
    'installed', coalesce((
      select jsonb_agg(jsonb_build_object('mode', coalesce(props->>'mode','browser'), 'sessions', s) order by s desc)
      from (select props, count(distinct session) s from public.events
            where name='app_open' and at > now() - d group by 1) m), '[]'::jsonb)
  ) into v;
  return v;
end $$;
revoke all on function public.admin_behaviour(int) from public;
revoke execute on function public.admin_behaviour(int) from anon;
grant execute on function public.admin_behaviour(int) to authenticated;
