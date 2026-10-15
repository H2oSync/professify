-- Run as a Supabase-style student (role authenticated) and as anon. MODE: psql -v mode=before|after
\set ON_ERROR_STOP on
\if :{?mode} \else \set mode after \endif
reset role;
insert into auth.users (id,email) values ('55555555-5555-5555-5555-555555555555','s5@calpoly.edu') on conflict do nothing;
insert into auth.users (id,email) values ('66666666-6666-6666-6666-666666666666','s6@calpoly.edu') on conflict do nothing;
delete from public.assistant_spend; delete from public.assistant_runs;
select set_config('request.jwt.claims','{"sub":"55555555-5555-5555-5555-555555555555","role":"authenticated"}',false) \gset
set role authenticated;
\echo --- mode :mode
-- 1. huge p_usd
select public.assistant_log_run('0123456789abcdef','q huge','help',null,null,null,null,null,null,null,false,false,999) as accepted;
reset role; select usd as spend_after_p_usd_999 from public.assistant_spend; set role authenticated;
-- 2. huge args
select public.assistant_log_run('0123456789abcdef','q bigargs','help',jsonb_build_object('x',repeat('y',100000))) as accepted_bigargs;
reset role; select length(args::text) as stored_args_len from public.assistant_runs where q='q bigargs'; set role authenticated;
-- 3. normal call still logs, with its real cost
select public.assistant_log_run('0123456789abcdef','q normal','search_sections','{"days":["Mo"]}'::jsonb,null,'claude-haiku',120,0,30,800,false,false,0.0042) as accepted_normal;
reset role; select tool, args, tokens_in, model from public.assistant_runs where q='q normal'; select usd as spend_total_now from public.assistant_spend; set role authenticated;
-- 4. volume: 250 more calls
do $$ declare i int; ok int := 0; no int := 0; r boolean; begin
  for i in 1..250 loop
    r := public.assistant_log_run('0123456789abcdef','q vol '||i,'help');
    if r then ok := ok+1; else no := no+1; end if;
  end loop;
  raise notice 'volume: % accepted, % refused (3 calls already made)', ok, no;
end $$;
reset role; select count(*) as rows_for_student from public.assistant_runs where q not like 'q other%'; set role authenticated;
-- 5. another student is unaffected
reset role;
select set_config('request.jwt.claims','{"sub":"66666666-6666-6666-6666-666666666666","role":"authenticated"}',false) as _ \gset
set role authenticated;
select public.assistant_log_run('0123456789abcdef','q other student','help') as other_student_ok;
-- 6. anon
reset role;
select set_config('request.jwt.claims','',false) as _ \gset
set role anon;
do $$ begin
  begin
    perform public.assistant_log_run('0123456789abcdef','q anon','help');
    raise notice 'anon: CALL WAS ALLOWED';
  exception when insufficient_privilege then raise notice 'anon: permission denied (good)'; end;
end $$;
-- 7. student cannot read the counter table
reset role;
select set_config('request.jwt.claims','{"sub":"55555555-5555-5555-5555-555555555555","role":"authenticated"}',false) as _ \gset
set role authenticated;
do $$ begin
  begin
    perform 1 from public.assistant_log_rate;
    raise notice 'student could read assistant_log_rate';
  exception when insufficient_privilege or undefined_table then raise notice 'student cannot read assistant_log_rate (good)'; end;
end $$;
reset role;
