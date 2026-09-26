-- Behaviour tests for professify-assistant.sql. Every block sets its own identity rather than
-- inheriting the one above it, because a SQL test can inherit the state that makes it pass.
\set ON_ERROR_STOP on
\set QUIET on
\pset tuples_only on
\pset format unaligned

create or replace function pg_temp.ok(cond boolean, label text) returns void
language plpgsql as $$
begin
  if cond then raise notice '  ok   %', label;
  else raise exception 'FAIL %', label; end if;
end $$;

create or replace function pg_temp.be(u text) returns void
language plpgsql as $$
begin
  perform set_config('request.jwt.claim.sub', u, false);
end $$;

-- Two real students and one suspended one.
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@calpoly.edu'),
  ('22222222-2222-2222-2222-222222222222', 'b@calpoly.edu'),
  ('33333333-3333-3333-3333-333333333333', 'c@calpoly.edu')
on conflict do nothing;
insert into public.suspensions (user_id, until)
  values ('33333333-3333-3333-3333-333333333333', now() + interval '7 days')
on conflict do nothing;

-- Start from a clean slate so a re-run does not inherit yesterday's counters.
truncate public.assistant_rate, public.assistant_runs, public.assistant_spend;
update public.assistant_config set value = 'false'   where key = 'enabled';
update public.assistant_config set value = 'UNSET'   where key = 'model';
update public.assistant_config set value = '2.00'    where key = 'daily_cap_usd';

do $$ begin raise notice '--- the switch ---'; end $$;

do $$
begin
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  perform pg_temp.ok((public.assistant_gate()->>'reason') = 'disabled',
    'ships disabled: the gate refuses before anything else is configured');
  perform pg_temp.ok(public.why_cant_i_ask() = 'disabled',
    'the oracle agrees with the gate while disabled');
end $$;

do $$
begin
  update public.assistant_config set value = 'true' where key = 'enabled';
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  perform pg_temp.ok((public.assistant_gate()->>'reason') = 'disabled',
    'enabled with model UNSET still refuses — a placeholder must never reach a vendor');
end $$;

do $$
declare g jsonb;
begin
  update public.assistant_config set value = 'test-model-1' where key = 'model';
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  g := public.assistant_gate();
  perform pg_temp.ok((g->>'allowed')::boolean, 'enabled and configured: the gate allows');
  perform pg_temp.ok(g->>'model' = 'test-model-1', 'the gate hands back the configured model');
end $$;

do $$ begin raise notice '--- identity ---'; end $$;

do $$
begin
  perform set_config('request.jwt.claim.sub', '', false);   -- signed out
  perform pg_temp.ok((public.assistant_gate()->>'reason') = 'sign_in_required',
    'a signed-out caller cannot spend the budget');
end $$;

do $$
begin
  perform pg_temp.be('33333333-3333-3333-3333-333333333333');
  perform pg_temp.ok((public.assistant_gate()->>'reason') = 'suspended',
    'a suspended student is refused');
  perform pg_temp.ok(public.why_cant_i_ask() = 'suspended',
    'and the oracle says so without spending a slot');
end $$;

do $$ begin raise notice '--- the three ceilings ---'; end $$;

do $$
declare i integer; allowed integer := 0; g jsonb;
begin
  truncate public.assistant_rate;
  perform pg_temp.be('22222222-2222-2222-2222-222222222222');
  for i in 1..25 loop
    g := public.assistant_gate();
    if (g->>'allowed')::boolean then allowed := allowed + 1; end if;
  end loop;
  perform pg_temp.ok(allowed = 20, format('the hourly ceiling is exactly 20, got %s', allowed));
  perform pg_temp.ok((public.assistant_gate()->>'reason') = 'hourly_cap',
    'the 21st call in an hour is refused as an hourly cap');
end $$;

do $$
declare other jsonb;
begin
  -- The ceiling is per student, not global. If B exhausting their hour also stops A, the cap is
  -- broken in the direction nobody notices until launch day.
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  other := public.assistant_gate();
  perform pg_temp.ok((other->>'allowed')::boolean,
    'one student hitting their ceiling does not block another');
end $$;

do $$
declare g jsonb;
begin
  -- Roll B's hour window backwards: the hour resets, the DAY does not.
  update public.assistant_rate
     set hour_start = date_trunc('hour', now()) - interval '2 hours'
   where user_id = '22222222-2222-2222-2222-222222222222';
  perform pg_temp.be('22222222-2222-2222-2222-222222222222');
  g := public.assistant_gate();
  perform pg_temp.ok((g->>'allowed')::boolean, 'a new hour restores the hourly allowance');
  perform pg_temp.ok(
    (select day_count from public.assistant_rate where user_id = '22222222-2222-2222-2222-222222222222') = 21,
    'the daily counter survives the hourly reset');
end $$;

do $$
declare i integer; g jsonb;
begin
  perform pg_temp.be('22222222-2222-2222-2222-222222222222');
  -- Walk to the daily ceiling, rolling the hour forward each time so the hourly cap is not what
  -- stops us. This is testing the 60, not the 20.
  for i in 1..60 loop
    update public.assistant_rate
       set hour_start = date_trunc('hour', now()) - interval '2 hours'
     where user_id = '22222222-2222-2222-2222-222222222222';
    g := public.assistant_gate();
    exit when not (g->>'allowed')::boolean;
  end loop;
  perform pg_temp.ok(g->>'reason' = 'daily_user_cap',
    'the daily ceiling stops a student the hourly one would let through');
  perform pg_temp.ok(
    (select day_count from public.assistant_rate where user_id = '22222222-2222-2222-2222-222222222222') = 60,
    'and it stops at exactly 60, not 61');
end $$;

do $$
declare g jsonb;
begin
  -- The global cap is the only one that holds when somebody controls many accounts.
  insert into public.assistant_spend (day, usd, calls)
  values ((now() at time zone 'America/Los_Angeles')::date, 2.00, 1)
  on conflict (day) do update set usd = 2.00;
  truncate public.assistant_rate;
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  g := public.assistant_gate();
  perform pg_temp.ok(g->>'reason' = 'daily_cap',
    'a fresh student with no history is still refused once the global cap is spent');
  perform pg_temp.ok(
    (select count(*) from public.assistant_rate where user_id = '11111111-1111-1111-1111-111111111111') = 0
     or (select day_count from public.assistant_rate where user_id = '11111111-1111-1111-1111-111111111111') = 0,
    'a refused call does not consume one of the student''s own slots');
  delete from public.assistant_spend;
end $$;

do $$ begin raise notice '--- the reservation ---'; end $$;

do $$
declare before_n integer; after_n integer;
begin
  truncate public.assistant_rate;
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  select coalesce(sum(day_count), 0) into before_n from public.assistant_rate;
  perform public.assistant_gate();
  select coalesce(sum(day_count), 0) into after_n from public.assistant_rate;
  perform pg_temp.ok(after_n = before_n + 1,
    'the gate reserves at call time, so a crash before the model replies is not a free retry');
end $$;

do $$ begin raise notice '--- logging ---'; end $$;

do $$
begin
  truncate public.assistant_runs, public.assistant_spend;
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  perform pg_temp.ok(
    public.assistant_log_run('a1b2c3d4e5f60718', 'open csc labs after 6', 'search_sections',
      '{"subject":"CSC","component":"LAB","start_after":"18:00"}'::jsonb, null,
      'test-model-1', 1200, 1100, 60, 430, false, false, 0.00011),
    'a well-formed run is logged');
  perform pg_temp.ok((select count(*) from public.assistant_runs) = 1, 'and exactly one row exists');
  perform pg_temp.ok(
    (select usd from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date) = 0.0001,
    'its cost lands on today''s spend');
end $$;

do $$
begin
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  perform pg_temp.ok(
    not public.assistant_log_run('b@calpoly.edu', 'q', 'search_sections'),
    'an email in the pseudonym slot is refused, not stored');
  perform pg_temp.ok(
    not public.assistant_log_run('11111111-1111-1111-1111-111111111111', 'q', 'search_sections'),
    'a user id in the pseudonym slot is refused, not stored');
  perform pg_temp.ok(
    not public.assistant_log_run('a1b2c3d4e5f60718', 'q', 'execute_sql'),
    'an unknown tool name is refused, not stored');
  perform pg_temp.ok((select count(*) from public.assistant_runs) = 1,
    'none of those three wrote a row');
end $$;

do $$
begin
  perform set_config('request.jwt.claim.sub', '', false);
  perform pg_temp.ok(
    not public.assistant_log_run('a1b2c3d4e5f60718', 'q', 'search_sections'),
    'a signed-out caller cannot write to the question log');
end $$;

do $$
declare long_q text := repeat('x', 900);
begin
  perform pg_temp.be('11111111-1111-1111-1111-111111111111');
  perform public.assistant_log_run('a1b2c3d4e5f60718', long_q, 'cant_answer', null, 'ambiguous');
  perform pg_temp.ok((select length(q) from public.assistant_runs order by id desc limit 1) = 300,
    'an over-long question is truncated at 300, not stored whole');
end $$;

do $$ begin raise notice '--- what the tables cannot do ---'; end $$;

do $$
declare leaked boolean := false;
begin
  -- The privacy promise, tested rather than described: nothing on a run row can be joined to the
  -- rate table, because they share no column but the absence of one.
  select exists (
    select 1 from information_schema.columns a
      join information_schema.columns b
        on a.column_name = b.column_name
     where a.table_name = 'assistant_runs' and b.table_name = 'assistant_rate'
       and a.table_schema = 'public' and b.table_schema = 'public'
  ) into leaked;
  perform pg_temp.ok(not leaked,
    'assistant_runs and assistant_rate share no column, so no join between them exists');
end $$;

do $$
declare denied boolean := false;
begin
  -- RLS with zero policies must deny a signed-in student reading the question log directly.
  begin
    set local role authenticated;
    perform 1 from public.assistant_runs limit 1;
    reset role;
  exception when insufficient_privilege then
    denied := true;
    reset role;
  end;
  perform pg_temp.ok(denied, 'a signed-in student cannot read the question log directly');
end $$;

do $$
declare denied boolean := false;
begin
  begin
    set local role authenticated;
    perform 1 from public.assistant_config limit 1;
    reset role;
  exception when insufficient_privilege then
    denied := true;
    reset role;
  end;
  perform pg_temp.ok(denied, 'a signed-in student cannot read the model name or the cap directly');
end $$;

do $$
declare denied boolean := false;
begin
  begin
    set local role authenticated;
    update public.assistant_config set value = '9999' where key = 'daily_cap_usd';
    reset role;
  exception when insufficient_privilege then
    denied := true;
    reset role;
  end;
  perform pg_temp.ok(denied, 'a signed-in student cannot raise the daily cap');
end $$;

do $$ begin raise notice 'all assistant SQL checks passed'; end $$;
