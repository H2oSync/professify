-- =================================================================================================
-- professify-assistant-v6.sql — 2026-09-25
-- Run AFTER professify-assistant-v5.sql. One transaction, idempotent, safe to re-run.
--
-- One change: Hawk has a new tool, game_plan ("what do I register for first?"), which reads the
-- student's Plans A–C on the device. Both whitelists — the run log and the miss log — refuse any
-- tool name they do not know, so without this a game-plan answer is shown but never logged, and a
-- "Not it?" on one is dropped. Both functions are recreated exactly as v5 left them, same
-- signatures (so existing grants stand), with 'game_plan' added to each list. Nothing else changes.
-- =================================================================================================
begin;

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
     ('search_sections','open_class','open_professor','cant_answer','my_requirements',
      'my_conflicts','my_free','my_day','my_units','prereqs','fit_pair','swap_section','friends_in',
      'when_registration','go_to','build_term','explain','my_professors','friends_took','help',
      'set_theme','watch','open_section','add_section','rate_professor','draft_message','share',
      'add_friend','friend_profile','professor_stats','compare_professors','game_plan')
  then
    return false;                      -- an unknown tool name is a bug or an attack, never a row
  end if;

  insert into public.assistant_runs
    (who, q, tool, args, reason, model, tokens_in, tokens_cached, tokens_out, ms, prerouted, fallback)
  values
    (who_id, left(coalesce(p_q, ''), 300), p_tool, p_args, nullif(left(coalesce(p_reason,''), 40), ''),
     nullif(p_model, ''), p_in, p_cached, p_out, p_ms, coalesce(p_prerouted, false),
     coalesce(p_fallback, false));

  /* Retention. The 30-day delete now runs on EVERY write (v5, 2026-09-24): at 1% it could leave a
     question for weeks on a quiet week, and the Privacy Policy promises about 30 days. It is an
     index range scan on assistant_runs_at_idx, so it costs nothing. The row-count ceiling and the
     spend history stay opportunistic. */
  delete from public.assistant_runs where at < now() - interval '30 days';
  if random() < 0.01 then
    delete from public.assistant_runs where id < (
      select max(id) - 500000 from public.assistant_runs
    );
    delete from public.assistant_spend where day < today - 400;
  end if;

  return true;
end;
$$;

create or replace function public.assistant_log_miss(
  p_who         text,
  p_q           text,
  p_shown_tool  text,
  p_shown_args  jsonb  default null,
  p_via         text   default 'router',
  p_picked_tool text   default null,
  p_picked_args jsonb  default null,
  p_update_id   bigint default null
)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
  uid    uuid := auth.uid();
  who_id text := left(coalesce(p_who, ''), 32);
  today  date := (now() at time zone 'America/Los_Angeles')::date;
  tools  text[] := array['search_sections','open_class','open_professor','cant_answer','my_requirements',
    'my_conflicts','my_free','my_day','my_units','prereqs','fit_pair','swap_section','friends_in',
    'when_registration','go_to','build_term','explain','my_professors','friends_took','help',
    'set_theme','watch','open_section','add_section','rate_professor','draft_message','share',
    'add_friend','friend_profile','professor_stats','compare_professors','game_plan'];
  mine   integer;
  total  bigint;
  new_id bigint;
begin
  if uid is null then return null; end if;
  if who_id !~ '^[0-9a-f]{16,32}$' then return null; end if;
  if coalesce(btrim(p_q), '') = '' then return null; end if;
  if p_shown_tool is null or not (p_shown_tool = any(tools)) then return null; end if;
  if p_picked_tool is not null and not (p_picked_tool = any(tools)) then return null; end if;
  if coalesce(p_via, '') not in ('router', 'model') then return null; end if;
  if p_shown_args is not null and (jsonb_typeof(p_shown_args) <> 'object' or length(p_shown_args::text) > 600) then return null; end if;
  if p_picked_args is not null and (jsonb_typeof(p_picked_args) <> 'object' or length(p_picked_args::text) > 600) then return null; end if;

  /* The pick that follows a "Not it?" tap completes THAT row rather than adding a second one — so
     the weekly review counts one miss once. Only the same pseudonym's own row, only within the
     hour, only if it has no pick yet. */
  if p_update_id is not null and p_picked_tool is not null then
    update public.assistant_misses
       set picked_tool = p_picked_tool, picked_args = p_picked_args
     where id = p_update_id and who = who_id and picked_tool is null and at > now() - interval '1 hour'
    returning id into new_id;
    if new_id is not null then return new_id; end if;
  end if;

  -- Deterministic retention: every write clears anything past 30 days (an index range scan).
  delete from public.assistant_misses where at < now() - interval '30 days';
  delete from public.assistant_miss_rate where day < today - 2;

  -- A global ceiling, so no number of accounts can fill the table in a day.
  select count(*) into total from public.assistant_misses where at > now() - interval '1 day';
  if total >= 5000 then return null; end if;

  insert into public.assistant_miss_rate (user_id, day, n) values (uid, today, 1)
  on conflict (user_id, day) do update set n = public.assistant_miss_rate.n + 1
  returning n into mine;
  if mine > 60 then return null; end if;

  insert into public.assistant_misses (who, q, shown_tool, shown_args, via, picked_tool, picked_args)
  values (who_id, left(btrim(p_q), 300), p_shown_tool, p_shown_args, p_via, p_picked_tool, p_picked_args)
  returning id into new_id;
  return new_id;
end;
$$;

revoke all on function public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint) from public;
revoke execute on function public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint) from anon;
grant execute on function public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint) to authenticated;

do $$
begin
  if not exists (select 1 from pg_proc where proname = 'assistant_log_run' and prosrc like '%''game_plan''%') then
    raise exception 'v6: assistant_log_run does not know game_plan';
  end if;
  if not exists (select 1 from pg_proc where proname = 'assistant_log_miss' and prosrc like '%''game_plan''%') then
    raise exception 'v6: assistant_log_miss does not know game_plan';
  end if;
  if has_function_privilege('anon', 'public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint)', 'execute') then
    raise exception 'v6: anon can call assistant_log_miss';
  end if;
  raise notice 'v6: game_plan is on both whitelists';
end $$;

commit;
