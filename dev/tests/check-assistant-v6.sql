\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('33333333-3333-3333-3333-333333333333','c@calpoly.edu') on conflict do nothing;
select set_config('request.jwt.claim.sub','33333333-3333-3333-3333-333333333333',false);
do $$ begin
  if public.assistant_log_miss('0123456789abcdef','what do i register for first','game_plan') is null then raise exception 'FAIL v6 miss game_plan'; end if;
  if not public.assistant_log_run('0123456789abcdef','what do i register for first','game_plan','{"plan":"A"}'::jsonb) then raise exception 'FAIL v6 run game_plan'; end if;
  if public.assistant_log_miss('0123456789abcdef','q','game_plans') is not null then raise exception 'FAIL v6 unknown still refused'; end if;
  raise notice 'ok   v6: game_plan logs as a run and as a miss; unknown names still refused';
end $$;
