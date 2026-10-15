-- =================================================================================================
-- professify-security-assistant-spend.sql — drafted 2026-10-14 (NOT yet run anywhere but a local test DB)
-- Run AFTER professify-assistant-v8.sql. One transaction, idempotent, safe to run twice.
--
-- WHY (plain words, for Tate)
--   Champ's "ask" function tells the database what a question cost by calling assistant_log_run(...,
--   p_usd). The database simply believes the number it is handed and adds it to today's total. The
--   daily cap ($2.00 in assistant_config) is checked against that total. But any signed-in student
--   can call assistant_log_run themselves from their browser — they don't need the ask function —
--   and pass p_usd = 999. That one call "spends" the whole day's budget and Champ switches itself
--   off for every student until midnight Pacific. The same open door also lets one student write
--   unlimited rows into the question log, each carrying a huge args blob, to fill the database.
--
-- WHAT THIS CHANGES (and only this; the rest of the v8 body is copied unchanged)
--   1. Each call can add at most $0.02 to the day's spend (negative, empty or NaN counts as 0).
--      A real Champ question costs well under a cent, so nothing legitimate is touched.
--   1b. Each student can add at most $0.20 to the day's spend in total (Pacific day). Once a
--      student's own running total reaches $0.20, their later p_usd adds nothing to the shared
--      total (the log row itself is still kept, inside the 200-row limit). So one account, honest
--      or not, can use at most a tenth of the $2.00 daily cap. The running total lives in the new
--      `usd` column of assistant_log_rate.
--   2. If args is longer than 600 characters, the row is still logged but args is replaced by a tiny
--      marker {"truncated":true,"len":N}. The question and its cost are never lost; the junk is.
--   3. Each student may make at most 200 log calls per Pacific day (the ask gate already allows only
--      150 questions a day, so a real student never gets near it). Counted in a new table,
--      assistant_log_rate (user id + day + count), locked down like assistant_miss_rate: RLS on, no
--      policies, no grants to anyone. Calls past 200 return false and record nothing, not even spend.
--   4. (Small addition beyond the three above, flagged for you.) The model name column was
--      unbounded text; it is now cut to 80 characters, otherwise item 2 could be sidestepped by
--      putting the junk in p_model instead.
--
--   NOT changed: the function's name, argument list, defaults, return type (boolean), SECURITY
--   DEFINER, search_path, the tool whitelist, the pseudonym check, retention. The deployed `ask`
--   edge function keeps working with no redeploy. Grants: PUBLIC and anon are revoked, authenticated
--   is granted (as before). Nothing is dropped.
--
--   Remaining limit, stated plainly: it now takes at least ten different accounts, each spending its
--   full $0.20, to trip a $2.00 cap. Ordinary use is far below $0.20 per student per day. If you
--   ever raise the daily cap or see honest students hitting $0.20, change the two numbers marked [SEC]
--   in the function (0.02 per call, 0.20 per student).
--
-- BEFORE YOU RUN IT
--   This file replaces the live assistant_log_run with the v8 text plus the changes above. It first
--   checks that the function currently in your database is exactly the v8 one (ignoring spacing); if
--   it is not (someone edited it by hand since), it STOPS with a message instead of overwriting.
--   To see what is live:  select pg_get_functiondef('public.assistant_log_run(text,text,text,jsonb,text,text,integer,integer,integer,integer,boolean,boolean,numeric)'::regprocedure);
--
-- It tests itself at the end (inside a mini-transaction that is rolled back, so no fake rows remain)
-- and raises an error — undoing the whole file — if anything is wrong.
-- =================================================================================================
begin;

-- ---- 0. Refuse to run against the wrong starting point -------------------------------------------
do $$
declare
  v_src text;
  v_known constant text[] := array[
    '9859195a776cfee5f84ec75949ffb108'   -- md5 of the v8 body with whitespace collapsed
    ,'9d5352427af2d4b000a3f069653cae24'   -- live on 2026-10-14 22:42 UTC: the same v8 logic with its comments stripped
  ];
begin
  if to_regclass('public.assistant_runs') is null or to_regclass('public.assistant_spend') is null then
    raise exception 'security-assistant-spend: assistant_runs / assistant_spend not found — run professify-assistant.sql ... -v8.sql first';
  end if;
  select prosrc into v_src from pg_proc
   where oid = 'public.assistant_log_run(text,text,text,jsonb,text,text,integer,integer,integer,integer,boolean,boolean,numeric)'::regprocedure;
  if v_src is null then
    raise exception 'security-assistant-spend: assistant_log_run with the 13-argument signature does not exist';
  end if;
  -- Already ours (second run)? then fine. Otherwise it must be exactly v8.
  if v_src not like '%assistant_log_rate%'
     and md5(regexp_replace(v_src, '\s+', ' ', 'g')) <> all (v_known) then
    raise exception 'security-assistant-spend: the live assistant_log_run is not the v8 text this file was copied from. Nothing was changed. Send Claude the output of pg_get_functiondef(...) (see header) so the fix can be rebased on what is really live.';
  end if;
end $$;

-- ---- 1. Per-student, per-day counter of log calls and dollars ---------------------------------------
-- Same shape and lock-down as assistant_miss_rate: counts and a running dollar total, never content.
create table if not exists public.assistant_log_rate (
  user_id uuid    not null,
  day     date    not null,
  n       integer not null default 0,
  primary key (user_id, day)
);
alter table public.assistant_log_rate add column if not exists usd numeric not null default 0;
alter table public.assistant_log_rate enable row level security;
-- No policies on purpose: only the SECURITY DEFINER function below can touch it.
revoke all on public.assistant_log_rate from public, anon, authenticated;

-- ---- 2. The function: v8 verbatim, plus the guards marked [SEC] -----------------------------------
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
  uid uuid := auth.uid();                                   -- [SEC]
  mine integer;                                             -- [SEC]
  usd_in numeric;                                           -- [SEC]
  used_today numeric;                                       -- [SEC]
  args_in jsonb := p_args;                                  -- [SEC]
begin
  if uid is null then return false; end if;

  /* [SEC] At most 200 log calls per student per Pacific day. Counted before anything is recorded,
     so past the limit a call adds no spend and no row. The real gate allows 150 questions a day. */
  insert into public.assistant_log_rate (user_id, day, n) values (uid, today, 1)
  on conflict (user_id, day) do update set n = public.assistant_log_rate.n + 1
  returning n, usd into mine, used_today;
  if mine > 200 then return false; end if;

  /* [SEC] The caller says what the call cost; the database does not have to believe a number that
     large. One question is clamped to [0, 0.02] dollars. NaN is treated as 0. */
  usd_in := case when p_usd is null or p_usd = 'NaN'::numeric then 0
                 else least(greatest(p_usd, 0), 0.02) end;
  /* [SEC] And one student can add at most $0.20 a day to the shared total. */
  usd_in := least(usd_in, greatest(0.20 - used_today, 0));
  if usd_in > 0 then
    update public.assistant_log_rate set usd = usd + usd_in where user_id = uid and day = today;
  end if;

  /* [SEC] Oversized args are replaced by a marker rather than stored. */
  if args_in is not null and length(args_in::text) > 600 then
    args_in := jsonb_build_object('truncated', true, 'len', length(args_in::text));
  end if;

  /* SPEND FIRST. In v1 the spend was recorded after the row checks below, so a call that failed
     them — an unlisted tool, a malformed pseudonym — had already cost money at the vendor and
     never counted toward the daily cap. The cap is the one bound on the worst case; it has to see
     every dollar, whatever happens to the row. */
  if usd_in > 0 then
    insert into public.assistant_spend (day, usd, calls) values (today, usd_in, 1)
    on conflict (day) do update set usd = public.assistant_spend.usd + excluded.usd,
                                    calls = public.assistant_spend.calls + 1;
  end if;

  if who_id !~ '^[0-9a-f]{16,32}$' then return false; end if;
  if p_tool is null or p_tool not in
     ('search_sections','open_class','open_professor','cant_answer','my_requirements',
      'my_conflicts','my_free','my_day','my_units','prereqs','fit_pair','swap_section','friends_in',
      'when_registration','go_to','build_term','explain','my_professors','friends_took','help',
      'set_theme','watch','open_section','add_section','rate_professor','draft_message','share',
      'add_friend','friend_profile','professor_stats','compare_professors','game_plan',
      'friends_free_now','free_with_friends','best_professor','fits_plan','app_help')
  then
    return false;                      -- an unknown tool name is a bug or an attack, never a row
  end if;

  insert into public.assistant_runs
    (who, q, tool, args, reason, model, tokens_in, tokens_cached, tokens_out, ms, prerouted, fallback)
  values
    (who_id, left(coalesce(p_q, ''), 300), p_tool, args_in, nullif(left(coalesce(p_reason,''), 40), ''),
     nullif(left(p_model, 80), ''), p_in, p_cached, p_out, p_ms, coalesce(p_prerouted, false),
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
    delete from public.assistant_log_rate where day < today - 2;   -- [SEC]
  end if;

  return true;
end;
$$;

-- ---- 3. Who may call it: signed-in students only ---------------------------------------------------
revoke all     on function public.assistant_log_run(text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric) from public;
revoke execute on function public.assistant_log_run(text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric) from anon;
grant  execute on function public.assistant_log_run(text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric) to authenticated;

-- ---- 4. Self-checks: any failure raises and rolls the whole file back ------------------------------
do $$
declare
  fn  constant regprocedure := 'public.assistant_log_run(text,text,text,jsonb,text,text,integer,integer,integer,integer,boolean,boolean,numeric)'::regprocedure;
  p   pg_proc%rowtype;
  uid constant text := 'ee5ec000-0000-4000-8000-00000000a001';
  s0 numeric; s1 numeric; n_ok int; ok boolean; i int; a text;
  prev_sub text := current_setting('request.jwt.claim.sub', true);
begin
  -- shape: untouched signature, return type, definer, search_path; exactly one overload
  select * into p from pg_proc where oid = fn;
  if p.prorettype <> 'boolean'::regtype or not p.prosecdef or p.pronargs <> 13
     or not (coalesce(p.proconfig, '{}') @> array['search_path=public']) then
    raise exception 'self-check: assistant_log_run shape changed';
  end if;
  if (select count(*) from pg_proc where proname = 'assistant_log_run' and pronamespace = 'public'::regnamespace) <> 1 then
    raise exception 'self-check: unexpected overload of assistant_log_run';
  end if;

  -- grants
  if has_function_privilege('anon', fn, 'execute') then raise exception 'self-check: anon can call assistant_log_run'; end if;
  if not has_function_privilege('authenticated', fn, 'execute') then raise exception 'self-check: authenticated lost assistant_log_run'; end if;
  if exists (select 1 from pg_proc x, aclexplode(coalesce(x.proacl, acldefault('f', x.proowner))) e
              where x.oid = fn and e.grantee = 0) then
    raise exception 'self-check: PUBLIC can still call assistant_log_run';
  end if;
  -- counter table locked down
  if not (select relrowsecurity from pg_class where oid = 'public.assistant_log_rate'::regclass)
     or has_table_privilege('anon', 'public.assistant_log_rate', 'select, insert, update, delete')
     or has_table_privilege('authenticated', 'public.assistant_log_rate', 'select, insert, update, delete')
     or exists (select 1 from pg_policy where polrelid = 'public.assistant_log_rate'::regclass) then
    raise exception 'self-check: assistant_log_rate is not locked down';
  end if;

  -- behaviour, inside a sub-transaction that is always rolled back (no fake rows, no fake dollars)
  begin
    perform set_config('request.jwt.claim.sub', uid, true);
    select coalesce(sum(usd), 0) into s0 from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date;

    ok := public.assistant_log_run('0123456789abcdef', 'selfcheck', 'help', '{}'::jsonb, null, null, null, null, null, null, false, false, 999);
    select coalesce(sum(usd), 0) into s1 from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date;
    if not ok then raise exception 'self-check: a normal call was refused'; end if;
    if s1 - s0 > 0.02 then raise exception 'self-check: p_usd=999 added % (>0.02)', s1 - s0; end if;
    if s1 - s0 <> 0.02 then raise exception 'self-check: p_usd=999 should clamp to exactly 0.02, added %', s1 - s0; end if;

    perform public.assistant_log_run('0123456789abcdef', 'selfcheck', 'help', '{}'::jsonb, null, null, null, null, null, null, false, false, -5);
    perform public.assistant_log_run('0123456789abcdef', 'selfcheck', 'help', '{}'::jsonb, null, null, null, null, null, null, false, false, 'NaN');
    select coalesce(sum(usd), 0) into s0 from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date;
    if s0 - s1 <> 0 then raise exception 'self-check: negative/NaN p_usd changed spend by %', s0 - s1; end if;

    ok := public.assistant_log_run('0123456789abcdef', 'selfcheck big', 'help', jsonb_build_object('x', repeat('y', 5000)), null, repeat('m', 500));
    if not ok then raise exception 'self-check: big-args call was refused (should log with a marker)'; end if;
    select args::text into a from public.assistant_runs where q = 'selfcheck big';
    if a is null or length(a) > 100 or a not like '%truncated%' then raise exception 'self-check: big args not replaced (%)', left(a, 60); end if;
    if (select length(model) from public.assistant_runs where q = 'selfcheck big') > 80 then raise exception 'self-check: model not cut'; end if;

    -- per-student dollar ceiling: 30 more calls with p_usd=999 -> this student's total is exactly 0.20
    s1 := (select coalesce(sum(usd), 0) from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date);
    for i in 1 .. 30 loop
      ok := public.assistant_log_run('0123456789abcdef', 'selfcheck ceiling', 'help', null, null, null, null, null, null, null, false, false, 999);
      if not ok then raise exception 'self-check: ceiling call % was refused (should still log)', i; end if;
    end loop;
    s0 := (select coalesce(sum(usd), 0) from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date);
    if s0 - s1 <> 0.18 then raise exception 'self-check: student total should reach exactly 0.20 (0.02 earlier + 0.18 here), added % here', s0 - s1; end if;
    -- a different student still adds normally
    perform set_config('request.jwt.claim.sub', 'ee5ec000-0000-4000-8000-00000000a002', true);
    ok := public.assistant_log_run('0123456789abcdef', 'selfcheck other', 'help', null, null, null, null, null, null, null, false, false, 999);
    if (select coalesce(sum(usd), 0) from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date) - s0 <> 0.02 then
      raise exception 'self-check: a second student was not able to add normally';
    end if;
    perform set_config('request.jwt.claim.sub', uid, true);
    -- 34 calls made so far -> 166 more allowed, the 167th is the 201st
    for i in 1 .. 166 loop
      ok := public.assistant_log_run('0123456789abcdef', 'selfcheck loop', 'help');
      if not ok then raise exception 'self-check: call % refused too early', i + 34; end if;
    end loop;
    s1 := (select coalesce(sum(usd), 0) from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date);
    ok := public.assistant_log_run('0123456789abcdef', 'selfcheck 201', 'help', null, null, null, null, null, null, null, false, false, 0.02);
    if ok then raise exception 'self-check: the 201st call of the day was accepted'; end if;
    if exists (select 1 from public.assistant_runs where q = 'selfcheck 201') then raise exception 'self-check: 201st call left a row'; end if;
    if (select coalesce(sum(usd), 0) from public.assistant_spend where day = (now() at time zone 'America/Los_Angeles')::date) <> s1 then
      raise exception 'self-check: 201st call still added spend';
    end if;
    raise exception using errcode = 'P0001', message = 'SELFCHECK_ROLLBACK';   -- always undo the test rows
  exception when others then
    if sqlerrm <> 'SELFCHECK_ROLLBACK' then raise; end if;
  end;
  perform set_config('request.jwt.claim.sub', coalesce(prev_sub, ''), true);
  if exists (select 1 from public.assistant_runs where q like 'selfcheck%') then
    raise exception 'self-check: test rows were not rolled back';
  end if;
  raise notice 'security-assistant-spend: ok (clamp 0..0.02, 0.20/student/day, args marker, 200/day cap, anon refused)';
end $$;

commit;
