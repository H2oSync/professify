-- =================================================================================================
-- 03-schedule.sql — drafted 2026-10-30, NOT run on production. Run LAST: after send-web-push is
-- deployed, its VAPID secrets are set, and ONE manual call returned sent >= 0 with no error.
--
-- Same shape as the working phone job: cron job 8 'termchamp-push-due' runs
-- `select public.push_kick_due()` every minute; that function reads push_config 'function_url'
-- and 'secret' and POSTs with pg_net, sending the secret as the x-push-secret header.
-- This adds the website twin: 'termchamp-web-push-due' -> public.push_web_kick_due(), which reads
-- 'web_function_url' and the SAME 'secret'. No secret is written here.
-- =================================================================================================
begin;

-- The URL is not a secret. Optional: without this row push_web_kick_due derives it from
-- 'function_url' by swapping /send-push for /send-web-push.
insert into public.push_config(key, value)
values ('web_function_url', 'https://rqkndeqbcahozidniesn.supabase.co/functions/v1/send-web-push')
on conflict (key) do update set value = excluded.value;

-- Every minute, like termchamp-push-due. It only makes an HTTP call when something is due for a
-- student who has a browser subscription, so an idle minute costs one indexed EXISTS.
select cron.unschedule(jobid) from cron.job where jobname = 'termchamp-web-push-due';
select cron.schedule('termchamp-web-push-due', '* * * * *', 'select public.push_web_kick_due()');

commit;

-- Check after 2-3 minutes (read-only):
--   select status, count(*) from cron.job_run_details d join cron.job j using (jobid)
--    where j.jobname = 'termchamp-web-push-due' and d.start_time > now() - interval '10 minutes' group by 1;
--   select status_code, count(*) from net._http_response where created > now() - interval '10 minutes' group by 1;
--   select kind, count(*) filter (where sent_at is not null and last_error is null) sent,
--          count(*) filter (where sent_at is null) pending, max(last_error) last_error
--     from public.push_outbox where created_at > now() - interval '1 day' group by kind;
