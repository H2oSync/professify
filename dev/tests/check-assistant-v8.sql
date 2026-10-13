\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('44444444-4444-4444-4444-444444444444','d@calpoly.edu') on conflict do nothing;
select set_config('request.jwt.claim.sub','44444444-4444-4444-4444-444444444444',false);
do $$
declare t text;
begin
  foreach t in array array['app_help','friends_free_now','fits_plan','game_plan','my_free','help'] loop
    if not public.assistant_log_run('0123456789abcdef','q8 '||t, t, '{}'::jsonb) then raise exception 'FAIL v8 run %', t; end if;
    if public.assistant_log_miss('0123456789abcdef','q8 '||t, t) is null then raise exception 'FAIL v8 miss %', t; end if;
    if public.assistant_log_miss('0123456789abcdef','q8 pick '||t, 'my_free', null, 'model', t) is null then raise exception 'FAIL v8 picked %', t; end if;
  end loop;
  if public.assistant_log_run('0123456789abcdef','q','app_helps') then raise exception 'FAIL v8 unknown run accepted'; end if;
  if public.assistant_log_miss('0123456789abcdef','q','apphelp') is not null then raise exception 'FAIL v8 unknown miss accepted'; end if;
  if (select count(*) from public.assistant_runs where tool = 'app_help') <> 1 then raise exception 'FAIL v8 rows'; end if;
  raise notice 'ok   v8: app_help logs as a run, a miss and a pick; old tools still do; unknown names still refused';
end $$;
