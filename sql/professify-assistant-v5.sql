-- =================================================================================================
-- professify-assistant-v5.sql — 2026-09-24
-- Run AFTER professify-assistant-v4.sql. One transaction, idempotent, safe to re-run.
--
-- Two changes:
--   1. assistant_log_run clears questions older than 30 days on every write (was 1 in 100 writes).
--   2. THE MISS LOG, below: what makes "train Hawk every week" possible.
-- =================================================================================================
--
-- THE MISS LOG — what makes "train Hawk every week" possible.
--
-- "Not it?" already went to the events table as hawk_miss, and log_events has no name whitelist,
-- so nothing was being dropped. But an event there carries no question — events deliberately never
-- store what anyone typed — so a week of hawk_miss rows says HOW OFTEN Hawk was wrong and never
-- WHAT it was wrong about. A miss you cannot read is a miss you cannot fix.
--
-- So a miss is logged here, with the question, only when the student taps "Not it?" — an explicit
-- "this was wrong". Same rules as assistant_runs: the device pseudonym and never the account, the
-- first 300 characters, 30 days, no policies (so no client can read it; Tate reads it in the SQL
-- editor), a per-account daily cap. When the student then picks one of the "Did you mean" readings,
-- that pick is logged too, and it is the right answer, labelled by the person who asked. Those
-- rows go straight into golden/router-golden.json.
--
-- The Privacy Policy says so (build 2026-09-24).
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
      'add_friend','friend_profile','professor_stats','compare_professors')
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




create table if not exists public.assistant_misses (
  id           bigint generated always as identity primary key,
  at           timestamptz not null default now(),
  who          text not null,        -- device pseudonym, as in assistant_runs. NOT a user id.
  q            text not null,
  shown_tool   text not null,        -- what Hawk answered with
  shown_args   jsonb,
  via          text not null,        -- 'router' (answered on the device) or 'model'
  picked_tool  text,                 -- the "Did you mean" reading the student then chose, if any
  picked_args  jsonb
);
create index if not exists assistant_misses_at_idx on public.assistant_misses (at desc);

alter table public.assistant_misses enable row level security;
-- No policies, deliberately — the same as assistant_runs. Nobody reads this through the app.
revoke all on public.assistant_misses from anon, public, authenticated;

/* Per-ACCOUNT cap, in a counter that never holds a question (review, 2026-09-24: the first draft
   capped per pseudonym, which the client chooses — 500 fake pseudonyms put 500 rows in). The same
   shape as assistant_rate: the account is known here, briefly, to count; the question row itself
   carries only the pseudonym. */
create table if not exists public.assistant_miss_rate (
  user_id uuid not null,
  day     date not null,
  n       integer not null default 0,
  primary key (user_id, day)
);
alter table public.assistant_miss_rate enable row level security;
revoke all on public.assistant_miss_rate from anon, public, authenticated;

drop function if exists public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb);
drop function if exists public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint);

create function public.assistant_log_miss(
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
    'add_friend','friend_profile','professor_stats','compare_professors'];
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
declare src text;
begin
  if not exists (select 1 from pg_class where relname = 'assistant_misses' and relrowsecurity) then
    raise exception 'misses: RLS is not on';
  end if;
  if exists (select 1 from pg_policies where tablename = 'assistant_misses') then
    raise exception 'misses: a policy exists — nothing should be able to read this through the app';
  end if;
  if has_table_privilege('authenticated', 'public.assistant_misses', 'select')
     or has_table_privilege('authenticated', 'public.assistant_miss_rate', 'select') then
    raise exception 'misses: authenticated can read a table';
  end if;
  select prosrc into src from pg_proc where proname = 'assistant_log_run';
  if position('delete from public.assistant_runs where at < now() - interval ''30 days'';
  if random()' in src) = 0 then
    raise exception 'v5: the 30-day delete is not on every write';
  end if;
  if has_function_privilege('anon', 'public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint)', 'execute') then
    raise exception 'misses: anon can call the logger';
  end if;
end $$;

commit;

-- -------------------------------------------------------------------------------------------------
-- THE WEEKLY REVIEW. Paste this in the SQL editor once a week.
-- -------------------------------------------------------------------------------------------------
-- select at::date, q, via, shown_tool, shown_args, picked_tool, picked_args
--   from public.assistant_misses
--  where at > now() - interval '7 days'
--  order by at desc;
--
-- And the model's own give-ups, from the run log:
-- select at::date, q, reason from public.assistant_runs
--  where tool = 'cant_answer' and at > now() - interval '7 days' order by at desc;
