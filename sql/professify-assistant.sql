-- ================================================================================================
-- HAWK, PHASE 0 — THE PLUMBING THAT MAKES THE ASSISTANT SAFE TO TURN ON — 2026-09-20
-- ================================================================================================
-- This runs before any model is called and before a single line of the Ask box exists. It builds
-- four tables and three functions, and its whole job is to make sure that when the model path is
-- switched on, two things are true: a runaway cannot cost more than a number Tate chose, and the
-- questions students type cannot be turned back into the students who typed them.
--
-- THE DECISION THAT SHAPES EVERYTHING ELSE, and it is the same one `events` made on 09-07:
-- a run row carries NO user id.
--
-- The obvious schema is (user_id, question, tool, timestamp). That is a log of named students
-- asking things like "is Professor Kearns hard" — in the same database as reviews this app
-- promises are anonymous. So `assistant_runs` carries `who`, the same rotating daily pseudonym the
-- browser already computes for `events`: sha256(device salt + today's UTC date). Stable for a day,
-- so a student's morning and afternoon questions group; different tomorrow, so nothing accumulates
-- into a profile.
--
-- But a per-user rate limit needs to know who the user is. That is the tension this file resolves,
-- and it resolves it by SEPARATION rather than by trust: identity lives in `assistant_rate`, which
-- holds COUNTERS AND NOTHING ELSE — no question, no tool, no per-call row, and no timestamp finer
-- than the hour. There is no column in it that could be joined to a run. Somebody with full
-- database access can learn that a student asked nine questions today. They cannot learn what any
-- of them was. That is the strongest guarantee available without giving up rate limiting entirely,
-- and rate limiting is what stops one account spending the whole daily budget.
--
-- WHAT BOUNDS THE BILL. Three ceilings, each one covering a failure the others do not:
--   * per user, per hour (20)  — a student mashing the button
--   * per user, per day  (60)  — a student who really likes the button
--   * global, per day ($ cap)  — a bug, a loop, or somebody with many accounts
-- The global cap is the only one that holds when the attacker controls the number of accounts, so
-- it is the one that actually bounds the worst case. It is a config row, not a constant, because
-- changing it must not be a deploy.
--
-- WHAT THIS FILE DOES NOT DO. It does not call a model, hold an API key, or know which vendor is
-- in use. The Edge Function does that, and it reaches these tables only through the three
-- SECURITY DEFINER functions below, using the student's own JWT. It has no service-role key. If
-- the function were compromised tomorrow, the blast radius is: read the assistant's model name,
-- spend up to the remaining daily cap, and write run rows. It cannot read `reviews`, `profiles`,
-- `messages` or anything else, because nothing grants it that.
--
-- Safe to re-run.
-- ================================================================================================

begin;

-- ------------------------------------------------------------------------------------------------
-- 1. Config — the two values that must be changeable without a deploy
-- ------------------------------------------------------------------------------------------------
-- Model name and daily cap live here rather than in the Edge Function for the same reason the GA
-- measurement id lives in a config object: the thing most likely to need changing at 11pm should
-- not require a git push and a build. `enabled` is the kill switch — flip it to false and every
-- gate call returns disabled, the client falls back to structured search, and no student sees an
-- error.
create table if not exists public.assistant_config (
  key   text primary key,
  value text not null
);

insert into public.assistant_config (key, value) values
  ('model',         'UNSET'),   -- set this to the chosen model id before switching enabled on
  ('daily_cap_usd', '2.00'),
  ('enabled',       'false')    -- ships OFF. Turning it on is a deliberate act, not a side effect.
on conflict (key) do nothing;   -- re-running must never reset a cap Tate has already tuned

alter table public.assistant_config enable row level security;
revoke all on public.assistant_config from anon, public, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 2. Spend — one row per day, the thing that bounds the worst case
-- ------------------------------------------------------------------------------------------------
-- Day is in America/Los_Angeles, not UTC, because the cap is a human decision about a human day
-- and a cap that resets at 5pm local is a cap nobody can reason about.
create table if not exists public.assistant_spend (
  day   date primary key,
  usd   numeric(10,4) not null default 0,
  calls integer       not null default 0
);

alter table public.assistant_spend enable row level security;
revoke all on public.assistant_spend from anon, public, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 3. Rate — identity, and deliberately nothing else
-- ------------------------------------------------------------------------------------------------
-- Read the column list and notice what is absent: no question, no tool, no args, no per-call row,
-- and no timestamp finer than the hour this counter started. This table can say "how many", never
-- "which". That is the entire point of it being a separate table from assistant_runs, and any
-- future column that would let the two be joined is the change that breaks the promise above.
create table if not exists public.assistant_rate (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  hour_start timestamptz not null default date_trunc('hour', now()),
  hour_count integer     not null default 0,
  day        date        not null default (now() at time zone 'America/Los_Angeles')::date,
  day_count  integer     not null default 0
);

alter table public.assistant_rate enable row level security;
revoke all on public.assistant_rate from anon, public, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 4. Runs — what was asked and how it was routed, under a pseudonym
-- ------------------------------------------------------------------------------------------------
-- `q` is the student's question, and storing it is a real choice that the Privacy Policy has to
-- carry. It is stored because the plan's kill criteria cannot be evaluated without it: "is
-- cant_answer over 40% of model-routed queries" is a question about what people asked, and
-- guessing at it is how products get built for imaginary users. 30 days, same as events, and never
-- joined to anything.
create table if not exists public.assistant_runs (
  id            bigint generated always as identity primary key,
  at            timestamptz not null default now(),
  who           text not null,          -- rotating daily pseudonym. NOT a user id. See the header.
  q             text not null,
  tool          text not null,
  args          jsonb,
  reason        text,                   -- cant_answer reason, when tool = 'cant_answer'
  model         text,                   -- null when the pre-router answered it for free
  tokens_in     integer,
  tokens_cached integer,
  tokens_out    integer,
  ms            integer,
  prerouted     boolean not null default false,
  fallback      boolean not null default false
);

create index if not exists assistant_runs_at_idx   on public.assistant_runs (at desc);
create index if not exists assistant_runs_tool_idx on public.assistant_runs (tool, at desc);

alter table public.assistant_runs enable row level security;
-- No policies, deliberately: RLS with zero policies denies everything to everyone except the owner
-- and the SECURITY DEFINER functions below. A student cannot read the question log. Neither can a
-- moderator through the client, which matters — the operator console shows emails and must never
-- show what somebody asked.
revoke all on public.assistant_runs from anon, public, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 5. The gate — called before every model call, and it RESERVES
-- ------------------------------------------------------------------------------------------------
-- This increments the counters before the model is called, not after. That ordering is the whole
-- value: if the vendor call times out, the function crashes, or the process is killed, the student
-- has still spent their slot. Counting afterwards means every crash is a free retry, and a crash
-- loop is exactly the shape of the runaway the cap exists to stop.
--
-- It returns a reason on refusal rather than a bare false, because the client has to say something
-- true to the student, and "you have asked a lot in the last hour" and "Ask is turned off right
-- now" are different sentences.
create or replace function public.assistant_gate()
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  uid        uuid := auth.uid();
  v_enabled  text;
  v_model    text;
  v_cap      numeric;
  v_spent    numeric;
  today      date := (now() at time zone 'America/Los_Angeles')::date;
  this_hour  timestamptz := date_trunc('hour', now());
  r          public.assistant_rate%rowtype;
begin
  if uid is null then
    return jsonb_build_object('allowed', false, 'reason', 'sign_in_required');
  end if;

  -- A suspended student can read but cannot write anything others see. Spending the shared daily
  -- budget is not writing, but it is consuming a common resource, and the suspension rule in this
  -- app has always been about removing the ability to affect other people.
  if exists (select 1 from public.suspensions s
              where s.user_id = uid and (s.until is null or s.until > now())) then
    return jsonb_build_object('allowed', false, 'reason', 'suspended');
  end if;

  select value into v_enabled from public.assistant_config where key = 'enabled';
  if coalesce(v_enabled, 'false') <> 'true' then
    return jsonb_build_object('allowed', false, 'reason', 'disabled');
  end if;

  select value into v_model from public.assistant_config where key = 'model';
  if v_model is null or v_model = 'UNSET' then
    -- Refusing when no model is configured is not defensive noise: 'UNSET' shipping through to a
    -- vendor call is how a config row becomes a 400 that looks like an outage.
    return jsonb_build_object('allowed', false, 'reason', 'disabled');
  end if;

  select coalesce(value::numeric, 0) into v_cap from public.assistant_config where key = 'daily_cap_usd';
  select coalesce(usd, 0) into v_spent from public.assistant_spend where day = today;
  if coalesce(v_spent, 0) >= coalesce(v_cap, 0) then
    return jsonb_build_object('allowed', false, 'reason', 'daily_cap');
  end if;

  insert into public.assistant_rate (user_id, hour_start, hour_count, day, day_count)
  values (uid, this_hour, 0, today, 0)
  on conflict (user_id) do nothing;

  select * into r from public.assistant_rate where user_id = uid for update;

  -- Roll the windows forward before testing them. Doing this in the same statement as the test
  -- would compare a fresh count against a stale window.
  if r.hour_start < this_hour then r.hour_count := 0; r.hour_start := this_hour; end if;
  if r.day        < today     then r.day_count  := 0; r.day        := today;     end if;

  if r.hour_count >= 20 then
    update public.assistant_rate
       set hour_start = r.hour_start, hour_count = r.hour_count, day = r.day, day_count = r.day_count
     where user_id = uid;
    return jsonb_build_object('allowed', false, 'reason', 'hourly_cap');
  end if;
  if r.day_count >= 60 then
    update public.assistant_rate
       set hour_start = r.hour_start, hour_count = r.hour_count, day = r.day, day_count = r.day_count
     where user_id = uid;
    return jsonb_build_object('allowed', false, 'reason', 'daily_user_cap');
  end if;

  update public.assistant_rate
     set hour_start = r.hour_start,
         hour_count = r.hour_count + 1,
         day        = r.day,
         day_count  = r.day_count + 1
   where user_id = uid;

  return jsonb_build_object('allowed', true, 'reason', 'ok', 'model', v_model);
end;
$$;

revoke all on function public.assistant_gate() from public;
grant execute on function public.assistant_gate() to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 6. Logging a run, and paying for it
-- ------------------------------------------------------------------------------------------------
-- Cost is passed in rather than computed here, because the price table belongs to the vendor and a
-- price hard-coded in a migration is a price that goes stale silently. The function's job is to
-- add whatever it is told to today's total; the Edge Function computes it from the usage numbers
-- the vendor returned on that very call.
--
-- `p_who` is validated to the pseudonym shape. A caller that sends something else — an email, a
-- uuid, a name — gets its row dropped rather than stored, because the one thing this table must
-- never accumulate is identity, and "the client promised not to" is not a control.
create or replace function public.assistant_log_run(
  p_who       text,
  p_q         text,
  p_tool      text,
  p_args      jsonb   default null,
  p_reason    text    default null,
  p_model     text    default null,
  p_in        integer default null,
  p_cached    integer default null,
  p_out       integer default null,
  p_ms        integer default null,
  p_prerouted boolean default false,
  p_fallback  boolean default false,
  p_usd       numeric default 0
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  today date := (now() at time zone 'America/Los_Angeles')::date;
  who_id text := left(coalesce(p_who, ''), 32);
begin
  if auth.uid() is null then return false; end if;
  if who_id !~ '^[0-9a-f]{16,32}$' then return false; end if;
  if p_tool is null or p_tool not in
     ('search_sections','open_class','open_professor','cant_answer','my_requirements','my_conflicts')
  then
    return false;                      -- an unknown tool name is a bug or an attack, never a row
  end if;

  insert into public.assistant_runs
    (who, q, tool, args, reason, model, tokens_in, tokens_cached, tokens_out, ms, prerouted, fallback)
  values
    (who_id, left(coalesce(p_q, ''), 300), p_tool, p_args, nullif(left(coalesce(p_reason,''), 40), ''),
     nullif(p_model, ''), p_in, p_cached, p_out, p_ms, coalesce(p_prerouted, false),
     coalesce(p_fallback, false));

  if coalesce(p_usd, 0) > 0 then
    insert into public.assistant_spend (day, usd, calls) values (today, p_usd, 1)
    on conflict (day) do update set usd = public.assistant_spend.usd + excluded.usd,
                                    calls = public.assistant_spend.calls + 1;
  end if;

  -- Retention, opportunistic so this needs no scheduler — the same pattern log_events uses. Two
  -- ceilings, because retention by age alone assumes the traffic is what you expect.
  if random() < 0.01 then
    delete from public.assistant_runs where at < now() - interval '30 days';
    delete from public.assistant_runs where id < (
      select max(id) - 500000 from public.assistant_runs
    );
    delete from public.assistant_spend where day < today - 400;
  end if;

  return true;
end;
$$;

revoke all on function public.assistant_log_run(
  text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric
) from public;
grant execute on function public.assistant_log_run(
  text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric
) to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 7. Why can't I ask? — the honest-refusal oracle, same shape as why_cant_i_review()
-- ------------------------------------------------------------------------------------------------
-- The client needs to tell a student the truth without guessing at it, and without the gate having
-- to spend one of their slots to find out.
create or replace function public.why_cant_i_ask()
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  uid       uuid := auth.uid();
  v_enabled text;
  v_cap     numeric;
  v_spent   numeric;
  today     date := (now() at time zone 'America/Los_Angeles')::date;
  r         public.assistant_rate%rowtype;
begin
  if uid is null then return 'sign_in_required'; end if;
  if exists (select 1 from public.suspensions s
              where s.user_id = uid and (s.until is null or s.until > now())) then
    return 'suspended';
  end if;
  select value into v_enabled from public.assistant_config where key = 'enabled';
  if coalesce(v_enabled, 'false') <> 'true' then return 'disabled'; end if;
  select coalesce(value::numeric, 0) into v_cap   from public.assistant_config where key = 'daily_cap_usd';
  select coalesce(usd, 0)           into v_spent  from public.assistant_spend  where day = today;
  if coalesce(v_spent, 0) >= coalesce(v_cap, 0) then return 'daily_cap'; end if;
  select * into r from public.assistant_rate where user_id = uid;
  if found then
    if r.hour_start >= date_trunc('hour', now()) and r.hour_count >= 20 then return 'hourly_cap'; end if;
    if r.day        >= today                     and r.day_count  >= 60 then return 'daily_user_cap'; end if;
  end if;
  return 'ok';
end;
$$;

revoke all on function public.why_cant_i_ask() from public;
grant execute on function public.why_cant_i_ask() to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 8. Self-checks — this migration reports its own failure rather than appearing to work
-- ------------------------------------------------------------------------------------------------
do $$
declare
  n integer;
begin
  select count(*) into n from information_schema.tables
   where table_schema = 'public'
     and table_name in ('assistant_config','assistant_spend','assistant_rate','assistant_runs');
  if n <> 4 then raise exception 'assistant: expected 4 tables, found %', n; end if;

  select count(*) into n from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
   where ns.nspname = 'public'
     and c.relname in ('assistant_config','assistant_spend','assistant_rate','assistant_runs')
     and c.relrowsecurity;
  if n <> 4 then raise exception 'assistant: expected RLS on 4 tables, found %', n; end if;

  -- Zero policies is the intended state. If a future migration adds one, this raises so that the
  -- decision is made on purpose rather than inherited.
  select count(*) into n from pg_policies
   where schemaname = 'public'
     and tablename in ('assistant_config','assistant_spend','assistant_rate','assistant_runs');
  if n <> 0 then raise exception 'assistant: expected 0 policies, found % — reads must go through definer functions', n; end if;

  select count(*) into n from information_schema.routines
   where routine_schema = 'public'
     and routine_name in ('assistant_gate','assistant_log_run','why_cant_i_ask');
  if n <> 3 then raise exception 'assistant: expected 3 functions, found %', n; end if;

  -- The promise in the header, asserted rather than described: no column on assistant_runs may
  -- name a user. This is what a future well-meaning "just add user_id for debugging" hits.
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'assistant_runs'
     and column_name in ('user_id','email','uid','author','author_id');
  if n <> 0 then raise exception 'assistant: assistant_runs must carry no identifying column, found %', n; end if;

  -- And the other half of it: the rate table must carry no content.
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'assistant_rate'
     and column_name in ('q','question','tool','args','who');
  if n <> 0 then raise exception 'assistant: assistant_rate must carry counters only, found %', n; end if;

  -- Ships off. If this raises, somebody enabled it inside the migration instead of deliberately.
  select count(*) into n from public.assistant_config where key = 'enabled' and value = 'true';
  if n <> 0 then raise exception 'assistant: enabled must ship false'; end if;

  raise notice 'assistant phase 0: 4 tables, 0 policies, 3 functions, disabled, cap = % USD/day',
    (select value from public.assistant_config where key = 'daily_cap_usd');
end $$;

commit;
