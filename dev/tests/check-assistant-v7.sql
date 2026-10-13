\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('44444444-4444-4444-4444-444444444444','d@calpoly.edu') on conflict do nothing;
select set_config('request.jwt.claim.sub','44444444-4444-4444-4444-444444444444',false);
do $$
declare t text;
begin
  foreach t in array array['friends_free_now','free_with_friends','best_professor','fits_plan','game_plan','my_free'] loop
    if not public.assistant_log_run('0123456789abcdef','q '||t, t, '{}'::jsonb) then raise exception 'FAIL v7 run %', t; end if;
    if public.assistant_log_miss('0123456789abcdef','q '||t, t) is null then raise exception 'FAIL v7 miss %', t; end if;
    if public.assistant_log_miss('0123456789abcdef','q pick '||t, 'my_free', null, 'model', t) is null then raise exception 'FAIL v7 picked %', t; end if;
  end loop;
  if public.assistant_log_run('0123456789abcdef','q','friends_free') then raise exception 'FAIL v7 unknown run accepted'; end if;
  if public.assistant_log_miss('0123456789abcdef','q','best_professors') is not null then raise exception 'FAIL v7 unknown miss accepted'; end if;
  if (select count(*) from public.assistant_runs where tool in ('friends_free_now','free_with_friends','best_professor','fits_plan')) <> 4 then raise exception 'FAIL v7 rows'; end if;
  raise notice 'ok   v7: the four new tools log as runs, misses and picks; old ones still do; unknown names still refused';
end $$;
