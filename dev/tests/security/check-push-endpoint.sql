-- as a signed-in student (role authenticated), through RLS, the way the website upserts it
\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('77777777-7777-7777-7777-777777777777','s7@calpoly.edu') on conflict do nothing;
select set_config('request.jwt.claims','{"sub":"77777777-7777-7777-7777-777777777777","role":"authenticated"}',false) as _ \gset
set role authenticated;
create or replace function pg_temp.try(ep text) returns text language plpgsql as $$
declare n int;
begin
  insert into public.push_subscriptions (user_id, endpoint, p256dh, auth)
  values (auth.uid(), ep, 'k', 'a') on conflict (endpoint) do nothing;
  get diagnostics n = row_count;
  return case when n = 1 then 'ACCEPTED ' else 'exists   ' end || left(ep, 60);
exception when check_violation then return 'REFUSED  ' || left(ep, 60);
end $$;
select pg_temp.try('https://fcm.googleapis.com/fcm/send/abc:APA91b_real');
select pg_temp.try('https://updates.push.services.mozilla.com/wpush/v2/gAAAA');
select pg_temp.try('https://web.push.apple.com/QGhk3Zr');
select pg_temp.try('https://wns2-par02p.notify.windows.com/w/?token=BQ');
select pg_temp.try('https://attacker.example/steal');
select pg_temp.try('http://fcm.googleapis.com/fcm/send/abc');
select pg_temp.try('https://fcm.googleapis.com@attacker.example/x');
select pg_temp.try('https://169.254.169.254/latest/meta-data/');
reset role;
select count(*) as rows_now, count(*) filter (where endpoint like '%attacker%' or endpoint like '%169.254%' or endpoint like 'http:%') as bad_rows_now from public.push_subscriptions;
