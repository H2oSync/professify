-- =================================================================================================
-- professify-assistant-v3.sql — 2026-09-23
-- Run AFTER professify-assistant-v2.sql. One transaction, idempotent.
--
-- One change: the tool whitelist in assistant_log_run gains 'my_professors' ("which of my professors
-- has the highest rating") and 'friends_took' ("a class my friends have taken"). Without it the answer still reaches the student, but the run is not
-- logged, so the golden set would never see these questions.
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
     ('search_sections','open_class','open_professor','cant_answer','my_requirements','my_conflicts',
      'my_free','my_day','my_units','prereqs','fit_pair','swap_section','friends_in',
      'when_registration','go_to','build_term','explain','my_professors','friends_took')
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

do $$
declare src text;
begin
  select prosrc into src from pg_proc where proname = 'assistant_log_run';
  if position('my_professors' in src) = 0 or position('friends_took' in src) = 0 then raise exception 'v3: new tools not whitelisted'; end if;
  if position('SPEND FIRST' in src) = 0 then raise exception 'v3: lost spend-first'; end if;
end $$;

commit;
