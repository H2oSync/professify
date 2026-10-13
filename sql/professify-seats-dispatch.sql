-- TermChamp: Supabase starts the seat scraper every 10 minutes (2026-10-13) — RUN 20
--
-- WHY. update-seats.yml asks GitHub to run every 10 minutes. GitHub ran it 34 times from Oct 5 to
-- Oct 13 — about once every 5-6 hours — so Spring 2027's seats sat at Oct 5, and from Round 1
-- (Oct 19, a pull every 10-20 minutes) students would see numbers hours old. pg_cron here runs on
-- time, so it asks GitHub to start the workflow (a "workflow_dispatch" with auto=true) every 10
-- minutes. The workflow's own gate still decides what, if anything, to pull; most of these runs
-- finish in ~15 seconds with "nothing due". GitHub's cron stays on as a backup.
--
-- BEFORE RUNNING
--   1. The PR with seats-catch-up-2026-10-13 must be MERGED first (it adds the `auto` input; until
--      it is on main, GitHub refuses the dispatch with 422 and nothing happens).
--   2. A GitHub token that can start the workflow, stored in Vault. On github.com:
--        Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate
--        · Repository access: Only select repositories → H2oSync/professify
--        · Permissions → Repository → Actions: Read and write   (nothing else)
--        · Expiration: the longest it offers (renew it before it runs out — see the check below)
--      Then, in this SQL editor, by itself (paste YOUR token; never share it):
--        select vault.create_secret('github_pat_…paste…', 'github_seats_token');
--      Replacing it later: select vault.update_secret(id, 'github_pat_…new…') from vault.secrets where name = 'github_seats_token';
--   pg_cron and pg_net are already on (RUN 7 and RUN 9).
--
-- Without the token this does nothing at all (and the check at the bottom says so).
-- One transaction. Safe to run twice. To stop it: select cron.unschedule('termchamp-seats-dispatch');
--
-- Check it worked, ~15 minutes later (read-only):
--   select id, status_code, left(content::text, 120) as body, created
--     from net._http_response order by id desc limit 5;        -- 204 = GitHub accepted the dispatch
--   and on github.com → Actions → Update Cal Poly seats: runs marked "workflow_dispatch" every 10 min.
--   401 = the token expired or was revoked (make a new one, vault.update_secret as above);
--   422 = the PR isn't merged yet, or the default branch isn't `main`.
--
-- Are seats fresh? (read-only; during Round 1 Spring should be under ~1 hour old)
--   select term, max(updated_at) as newest, now() - max(updated_at) as age, count(*) as sections
--     from public.course_seats where term in ('2268','2274') group by term;

begin;

do $$ begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then
    raise exception 'pg_cron is not on — Dashboard → Integrations → Cron → Enable, then run this again';
  end if;
  if not exists (select 1 from pg_extension where extname = 'pg_net') then
    raise exception 'pg_net is not on — Dashboard → Database → Extensions → pg_net, then run this again';
  end if;
end $$;

create or replace function public.seats_dispatch()
returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  k text;
begin
  begin
    select decrypted_secret into k from vault.decrypted_secrets where name = 'github_seats_token' order by created_at desc limit 1;
  exception when others then k := null;
  end;
  if k is null or k = '' then return null; end if;   -- no token yet: do nothing
  return net.http_post(
    url := 'https://api.github.com/repos/H2oSync/professify/actions/workflows/update-seats.yml/dispatches',
    body := jsonb_build_object('ref', 'main', 'inputs', jsonb_build_object('auto', 'true')),
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || k,
      'Accept', 'application/vnd.github+json',
      'X-GitHub-Api-Version', '2022-11-28',
      'User-Agent', 'termchamp-seats-dispatch',
      'Content-Type', 'application/json'),
    timeout_milliseconds := 10000);
end $$;
revoke all on function public.seats_dispatch() from public, anon, authenticated;

-- every 10 minutes, offset 2 minutes past (02, 12, 22 …) so it never lands on GitHub's own :00 rush
do $$ begin
  perform cron.unschedule('termchamp-seats-dispatch') where exists (select 1 from cron.job where jobname = 'termchamp-seats-dispatch');
end $$;
select cron.schedule('termchamp-seats-dispatch', '2-59/10 * * * *', 'select public.seats_dispatch()');

do $$ begin
  if not exists (select 1 from cron.job where jobname = 'termchamp-seats-dispatch') then
    raise exception 'the dispatch job did not schedule';
  end if;
  if not exists (select 1 from vault.decrypted_secrets where name = 'github_seats_token') then
    raise notice 'Scheduled, but there is NO github_seats_token in Vault yet — nothing will be sent until you add it (see BEFORE RUNNING, step 2).';
  else
    raise notice 'Scheduled. Supabase will start the seat scraper at :02, :12, :22 … every hour.';
  end if;
end $$;

commit;

-- Check (read-only): the job and its last runs
select jobname, schedule, active from cron.job where jobname = 'termchamp-seats-dispatch';
