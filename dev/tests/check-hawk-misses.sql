\set ON_ERROR_STOP on
\set QUIET on
create or replace function pg_temp.ok(cond boolean, label text) returns void language plpgsql as $$
begin if cond then raise notice '  ok   %', label; else raise exception 'FAIL %', label; end if; end $$;
create or replace function pg_temp.be(u text) returns void language plpgsql as $$
begin perform set_config('request.jwt.claim.sub', u, false); end $$;
insert into auth.users (id, email) values ('11111111-1111-1111-1111-111111111111','a@calpoly.edu'),
  ('22222222-2222-2222-2222-222222222222','b@calpoly.edu') on conflict do nothing;
truncate public.assistant_misses, public.assistant_miss_rate;

select pg_temp.be('');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','q','go_to') is null, 'signed out: refused');
select pg_temp.be('11111111-1111-1111-1111-111111111111');
select public.assistant_log_miss('0123456789abcdef','which professor of mine is best','go_to','{"where":"my classes"}','model') as id \gset
select pg_temp.ok(:id is not null, 'a miss is logged and its id returned');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','which professor of mine is best','go_to','{"where":"my classes"}','model','my_professors','{}', :id) = :id, 'the pick completes the SAME row');
select pg_temp.ok((select count(*) from public.assistant_misses) = 1 and (select picked_tool from public.assistant_misses) = 'my_professors', 'one miss, one row, with its pick');
select public.assistant_log_miss('aaaaaaaaaaaaaaaa','x','go_to',null,'router','help','{}', :id) as id2 \gset
select pg_temp.ok(:id2 <> :id and (select count(*) from public.assistant_misses) = 2, 'another pseudonym cannot complete another row (it inserts instead)');
select pg_temp.ok(public.assistant_log_miss('not-a-pseudonym','q','go_to') is null, 'bad pseudonym refused');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','q','drop_table') is null, 'unknown tool refused');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','q','go_to',null,'router','nope') is null, 'unknown picked tool refused');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','q','go_to',null,'somewhere') is null, 'bad via refused');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','   ','go_to') is null, 'empty question refused');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','q','go_to', ('{"x":"'||repeat('a',700)||'"}')::jsonb) is null, 'oversized args refused');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef', repeat('z',900),'go_to') is not null, 'long question accepted...');
select pg_temp.ok((select max(length(q)) from public.assistant_misses) = 300, '...and cut to 300');
truncate public.assistant_misses, public.assistant_miss_rate;
do $$ declare i int; begin for i in 1..70 loop perform public.assistant_log_miss(lpad(to_hex(i),16,'0'),'q'||i,'help'); end loop; end $$;
select pg_temp.ok((select count(*) from public.assistant_misses) = 60, 'daily cap is per ACCOUNT: 70 fake pseudonyms still stop at 60');
select pg_temp.be('22222222-2222-2222-2222-222222222222');
select pg_temp.ok(public.assistant_log_miss('0123456789abcdef','q','help') is not null, 'another account is not blocked by the first');
select pg_temp.ok((select count(*) from public.assistant_miss_rate where user_id = '22222222-2222-2222-2222-222222222222') = 1
  and not exists (select 1 from information_schema.columns where table_name = 'assistant_miss_rate' and column_name = 'q'), 'the counter holds no question');
insert into public.assistant_misses (at, who, q, shown_tool, via) values (now() - interval '31 days', '0123456789abcdef', 'old', 'help', 'router');
select public.assistant_log_miss('0123456789abcdef','new','help') as id3 \gset
select pg_temp.ok(:id3 is not null and not exists (select 1 from public.assistant_misses where q = 'old'), 'a write always clears rows past 30 days');
set role authenticated;
do $$ begin
  begin perform count(*) from public.assistant_misses; raise exception 'FAIL authenticated could read misses';
  exception when insufficient_privilege then raise notice '  ok   authenticated cannot read the table'; end;
end $$;
reset role;
set role anon;
do $$ begin
  begin perform public.assistant_log_miss('0123456789abcdef','q','help'); raise exception 'FAIL anon could call';
  exception when insufficient_privilege then raise notice '  ok   anon cannot call the logger'; end;
end $$;
reset role;
select pg_temp.be('11111111-1111-1111-1111-111111111111');
insert into public.assistant_runs (at, who, q, tool) values (now() - interval '31 days', '0123456789abcdef', 'old run', 'help');
select public.assistant_log_run('0123456789abcdef', 'new run', 'help') as r \gset
select pg_temp.ok(not exists (select 1 from public.assistant_runs where q = 'old run'), 'v5: every logged run clears runs past 30 days');
select 'misses suite done';
