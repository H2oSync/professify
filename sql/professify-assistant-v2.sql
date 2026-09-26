-- =================================================================================================
-- professify-assistant-v2.sql — 2026-09-24
-- Run AFTER professify-assistant.sql. One transaction, idempotent (CREATE OR REPLACE keeps grants).
--
-- Three changes, all found by reading v1 against what the function now sends:
--   1. assistant_log_run recorded spend AFTER validating the row, so any call whose row was
--      rejected cost money that the daily cap never saw. Spend is now recorded first.
--   2. The tool whitelist had 6 names; the function now emits 17. Every run using the other 11 was
--      silently dropped (the function returns false, it does not raise).
--   3. Per-student caps 20/hour -> 40/hour and 60/day -> 150/day, because a verified explanation
--      is a second model call on the same question. The global daily dollar cap is unchanged and
--      still bounds the worst case.
-- =================================================================================================
begin;

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

  if r.hour_count >= 40 then
    update public.assistant_rate
       set hour_start = r.hour_start, hour_count = r.hour_count, day = r.day, day_count = r.day_count
     where user_id = uid;
    return jsonb_build_object('allowed', false, 'reason', 'hourly_cap');
  end if;
  if r.day_count >= 150 then
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

  /* SPEND FIRST. In v1 the spend was recorded after the row checks below, so a call that failed
     them — an unlisted tool, a malformed pseudonym — had already cost money at the vendor and
     never counted toward the daily cap. The cap is the one bound on the worst case; it has to see
     every dollar, whatever happens to the row. */
  if coalesce(p_usd, 0) > 0 then
    insert into public.assistant_spend (day, usd, calls) values (today, p_usd, 1)
    on conflict (day) do update set usd = public.assistant_spend.usd + excluded.usd,
                                    calls = public.assistant_spend.calls + 1;
  end if;

  if who_id !~ '^[0-9a-f]{16,32}$' then return false; end if;
  if p_tool is null or p_tool not in
     ('search_sections','open_class','open_professor','cant_answer','my_requirements','my_conflicts',
      'my_free','my_day','my_units','prereqs','fit_pair','swap_section','friends_in',
      'when_registration','go_to','build_term','explain')
  then
    return false;                      -- an unknown tool name is a bug or an attack, never a row
  end if;

  insert into public.assistant_runs
    (who, q, tool, args, reason, model, tokens_in, tokens_cached, tokens_out, ms, prerouted, fallback)
  values
    (who_id, left(coalesce(p_q, ''), 300), p_tool, p_args, nullif(left(coalesce(p_reason,''), 40), ''),
     nullif(p_model, ''), p_in, p_cached, p_out, p_ms, coalesce(p_prerouted, false),
     coalesce(p_fallback, false));

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
    if r.hour_start >= date_trunc('hour', now()) and r.hour_count >= 40 then return 'hourly_cap'; end if;
    if r.day        >= today                     and r.day_count  >= 150 then return 'daily_user_cap'; end if;
  end if;
  return 'ok';
end;
$$;

-- Self-checks. Each raises, so a partial apply is impossible.
do $$
declare src text;
begin
  select prosrc into src from pg_proc where proname = 'assistant_log_run';
  if position('build_term' in src) = 0 then raise exception 'v2: tool list not updated'; end if;
  if position('SPEND FIRST' in src) = 0 then raise exception 'v2: spend-first not applied'; end if;
  if position('SPEND FIRST' in src) > position('who_id !~' in src) then raise exception 'v2: spend is still after validation'; end if;
  select prosrc into src from pg_proc where proname = 'assistant_gate';
  if position('>= 40' in src) = 0 then raise exception 'v2: hourly cap not raised'; end if;
  if position('>= 150' in src) = 0 then raise exception 'v2: daily cap not raised'; end if;
  select prosrc into src from pg_proc where proname = 'why_cant_i_ask';
  if position('>= 150' in src) = 0 or position('>= 40' in src) = 0 then raise exception 'v2: why_cant_i_ask caps not raised'; end if;
end $$;

commit;

-- Check:  select proname from pg_proc where proname like 'assistant_%';
