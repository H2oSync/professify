-- =================================================================================================
-- 02-backlog-purge.sql — drafted 2026-10-30, NOT run on production. Run ONCE, after 01 and BEFORE 03
-- (the cron job), so the first send can never be a seven-week-old "seat open".
--
-- Nothing is deleted: every unsent row is either kept (fresh, for a student with a browser
-- subscription) or closed with sent_at = now() and a last_error saying why. Matches the convention
-- used for the push_queue backlog on 2026-10-28 ('skipped: stale').
-- As counted read-only on 2026-10-30: 779 unsent, 701 older than 2 days, 113 belong to the one
-- student with a browser subscription.
-- =================================================================================================
begin;

-- Anything older than 2 days, whatever the kind.
update public.push_outbox
   set sent_at = now(), last_error = 'skipped: stale (backlog purge 2026-10-30)'
 where sent_at is null and created_at < now() - interval '2 days';

-- Then the ordinary rules: per-kind max age (seat/waitlist 12h), no subscription, out of tries.
select public.push_web_expire() as also_expired;

-- What is left to send (should be a handful, all fresh, all for subscribed students).
select kind, count(*) as still_pending
  from public.push_outbox where sent_at is null group by kind order by kind;

commit;
