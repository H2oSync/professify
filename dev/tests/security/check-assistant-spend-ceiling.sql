\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('a1111111-1111-1111-1111-111111111111','a@calpoly.edu'),('b2222222-2222-2222-2222-222222222222','b@calpoly.edu'),('c3333333-3333-3333-3333-333333333333','c@calpoly.edu') on conflict do nothing;
delete from public.assistant_spend; delete from public.assistant_runs; delete from public.assistant_log_rate;
create or replace function pg_temp.spend() returns numeric language sql as $$ select coalesce(sum(usd),0) from public.assistant_spend $$;
grant execute on function pg_temp.spend() to authenticated;
-- A: 50 x p_usd=999
select set_config('request.jwt.claims','{"sub":"a1111111-1111-1111-1111-111111111111"}',false) as _ \gset
set role authenticated;
do $$ declare i int; ok int := 0; begin for i in 1..50 loop if public.assistant_log_run('0123456789abcdef','a huge '||i,'help',null,null,null,null,null,null,null,false,false,999) then ok := ok+1; end if; end loop; raise notice 'student A: 50 calls with p_usd=999, % rows logged', ok; end $$;
reset role;
do $$ declare s numeric := (select sum(usd) from public.assistant_spend); begin
  raise notice 'global spend after A = %', s;
  if s <> 0.20 then raise exception 'FAIL A should add exactly 0.20, got %', s; end if; end $$;
-- B: still adds normally
select set_config('request.jwt.claims','{"sub":"b2222222-2222-2222-2222-222222222222"}',false) as _ \gset
set role authenticated;
select public.assistant_log_run('0123456789abcdef','b normal','help',null,null,null,null,null,null,null,false,false,0.004) as b_ok;
reset role;
do $$ declare s numeric := (select sum(usd) from public.assistant_spend); begin
  raise notice 'global spend after B (one 0.004 call) = %', s;
  if s <> 0.204 then raise exception 'FAIL B should add 0.004 in full, got %', s - 0.20; end if; end $$;
-- B again with p_usd=999: adds exactly 0.02 (clamp), still under B's ceiling
select set_config('request.jwt.claims','{"sub":"b2222222-2222-2222-2222-222222222222"}',false) as _ \gset
set role authenticated;
select public.assistant_log_run('0123456789abcdef','b big','help',null,null,null,null,null,null,null,false,false,999) as b_big_ok;
reset role;
do $$ declare s numeric := (select sum(usd) from public.assistant_spend); begin
  if s <> 0.224 then raise exception 'FAIL B clamp, total %', s; end if; raise notice 'global spend after B big call = % (+0.02)', s; end $$;
-- C: normal ~0.004 calls are counted in full until the 0.20 ceiling: 50 x 0.004 = 0.200 exactly, the 51st adds 0
select set_config('request.jwt.claims','{"sub":"c3333333-3333-3333-3333-333333333333"}',false) as _ \gset
set role authenticated;
do $$ declare i int; begin for i in 1..50 loop perform public.assistant_log_run('0123456789abcdef','c n '||i,'help',null,null,null,null,null,null,null,false,false,0.004); end loop; end $$;
reset role;
do $$ declare s numeric := (select sum(usd) from public.assistant_spend); begin
  if s <> 0.424 then raise exception 'FAIL C 50 normal calls should add 0.200 in full, total %', s; end if; raise notice 'global spend after C 50 x 0.004 = % (+0.200 in full)', s; end $$;
select set_config('request.jwt.claims','{"sub":"c3333333-3333-3333-3333-333333333333"}',false) as _ \gset
set role authenticated;
select public.assistant_log_run('0123456789abcdef','c 51','help',null,null,null,null,null,null,null,false,false,0.004) as c51_row_still_logged;
reset role;
do $$ declare s numeric := (select sum(usd) from public.assistant_spend); begin
  if s <> 0.424 then raise exception 'FAIL C 51st call should add 0, total %', s; end if; raise notice 'global spend after C 51st call = % (+0)', s;
  if (select count(*) from public.assistant_runs where who='0123456789abcdef' and q='c 51') <> 1 then raise exception 'FAIL row not logged'; end if;
  raise notice 'OK ceiling: one account adds at most 0.20; rows still logged'; end $$;
