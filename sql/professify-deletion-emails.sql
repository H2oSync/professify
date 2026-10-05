-- TermChamp: emails about deleting your account (2026-10-04)
--
-- Apple 5.1.1(v): an account deletion that takes time must tell people how long it will take, and
-- confirm when it is done. Two emails, from noreply@termchamp.com through Resend:
--   · "scheduled" — right after Delete account: it's hidden now, deleted on <date>, sign in before
--     then to recover it (and: didn't ask for this? sign in and recover it).
--   · "deleted"   — when the nightly job has really deleted it, with what happened to the reviews.
--
-- How: a small queue (account_emails) that nobody but these functions can read, and a job every
-- 5 minutes that sends what's waiting through pg_net (an HTTP call from the database) and checks
-- the answer on its next run. Nothing here can stop or delay a deletion: a failed email is retried
-- with growing gaps (15 minutes, then 30, 1h, 2h … about 2½ days over 8 tries, so a key or domain
-- fixed the next day still delivers it), the reason is kept, and the deletion never waits for it.
-- Each email carries an Idempotency-Key, so a retry after a lost answer can't send it twice.
--   · The address is kept only until the email is sent, and at most 14 days.
--   · A "scheduled" email that hasn't gone out when the account is recovered is dropped.
--
-- BEFORE RUNNING (Tate):
--   1. pg_net on: Supabase → Database → Extensions → pg_net → Enable (this file also tries).
--   2. A Resend key for these emails: Resend → API Keys → Create → name "TermChamp account emails",
--      permission "Sending access", domain termchamp.com → copy it. Then, in the SQL editor, alone:
--          select vault.create_secret('re_…paste the key…', 'resend_api_key');
--      Never paste the key into a chat. Without it the emails wait in the queue (nothing breaks)
--      and go out within 5 minutes of the key being added.
--
-- Needs professify-delete-account-30-days.sql (RUN-THESE-SQL-FIRST/7; this file re-creates purge_due_account_deletions() with one
-- addition: the address is read before the account goes, and the "deleted" email is queued only
-- if the deletion succeeded). Admin check:
--   select id, kind, created_at, sent_at, attempts, next_try_at, last_error from account_emails order by id desc limit 20;
-- One transaction; self-checks raise. Safe to run twice.

begin;

do $$ begin
  begin
    create extension if not exists pg_net with schema extensions;
  exception when others then
    raise exception 'pg_net is not on. Supabase → Database → Extensions → pg_net → Enable, then run this file again. (%)', sqlerrm;
  end;
end $$;

-- 1. The queue ------------------------------------------------------------------------------------
create table if not exists public.account_emails (
  id           bigserial primary key,
  kind         text not null check (kind in ('scheduled', 'deleted')),
  user_id      uuid not null,                 -- no foreign key: the account is gone for "deleted"
  email        text,                          -- cleared once sent (or after 14 days)
  detail       jsonb not null default '{}',   -- {purge_after} or {delete_reviews, requested_at}
  created_at   timestamptz not null default now(),
  request_id   bigint,                        -- pg_net's id while a send is in flight
  requested_at timestamptz,
  sent_at      timestamptz,
  attempts     int not null default 0,
  next_try_at  timestamptz not null default now(),
  last_error   text
);
alter table public.account_emails add column if not exists next_try_at timestamptz not null default now();
alter table public.account_emails enable row level security;   -- no policies: functions only
revoke all on public.account_emails from public, anon, authenticated;
revoke all on sequence public.account_emails_id_seq from public, anon, authenticated;
create index if not exists account_emails_todo_idx on public.account_emails (id) where sent_at is null;
-- one waiting "scheduled" email per account: asking, recovering and asking again sends one, not two
create unique index if not exists account_emails_one_scheduled on public.account_emails (user_id) where kind = 'scheduled' and sent_at is null;

-- 2. "Scheduled": queued when a deletion is first asked for (not when the reviews choice changes) --
create or replace function public.account_emails_on_request()
returns trigger language plpgsql security definer set search_path = public as $$
declare addr text;
begin
  select u.email into addr from auth.users u where u.id = new.user_id;
  if addr is not null and addr <> '' then
    -- asked again before the last one went: the waiting email takes the new date
    update public.account_emails set email = addr, detail = jsonb_build_object('purge_after', new.purge_after)
     where user_id = new.user_id and kind = 'scheduled' and sent_at is null and request_id is null;
    if not found then
      insert into public.account_emails (kind, user_id, email, detail)
      values ('scheduled', new.user_id, addr, jsonb_build_object('purge_after', new.purge_after));
    end if;
  end if;
  return new;
exception when others then
  return new;   -- an email must never stop a deletion being asked for
end $$;
revoke all on function public.account_emails_on_request() from public, anon, authenticated;
drop trigger if exists account_emails_on_request on public.account_deletions;
create trigger account_emails_on_request after insert on public.account_deletions
  for each row execute function public.account_emails_on_request();

-- 3. "Deleted": the purge, as in 7-delete-account-30-days.sql, plus the address read first ---------
create or replace function public.purge_due_account_deletions()
returns int language plpgsql security definer set search_path = public as $$
declare r record; n int := 0; addr text;
begin
  for r in select * from public.account_deletions where purge_after <= now() order by purge_after for update skip locked loop
    -- a recovery that landed after the list was read wins
    if not exists (select 1 from public.account_deletions d where d.user_id = r.user_id and d.purge_after <= now()) then continue; end if;
    begin
      select u.email into addr from auth.users u where u.id = r.user_id;   -- read before the account goes
      -- delete_my_account() works on auth.uid(); act as that one account, inside this block only
      perform set_config('request.jwt.claim.sub', r.user_id::text, true);
      perform set_config('request.jwt.claims', json_build_object('sub', r.user_id, 'role', 'authenticated')::text, true);
      -- The app removes the photo through the Storage API when the deletion is asked for. Anything
      -- left is cleared here as a backstop: Supabase refuses SQL deletes on storage unless
      -- storage.allow_delete_query is set, and this step may never block the deletion itself.
      begin
        perform set_config('storage.allow_delete_query', 'true', true);
        delete from storage.objects where bucket_id = 'avatars' and name like r.user_id::text || '/%';
        perform set_config('storage.allow_delete_query', 'false', true);
      exception when others then
        perform set_config('storage.allow_delete_query', 'false', true);
      end;
      perform public.delete_my_account_v2(r.delete_reviews);   -- the account_deletions row goes with auth.users
      -- queued only now, inside the same block: a deletion that failed sends no "deleted" email
      if addr is not null and addr <> '' then
        begin
          insert into public.account_emails (kind, user_id, email, detail)
          values ('deleted', r.user_id, addr, jsonb_build_object('delete_reviews', r.delete_reviews, 'requested_at', r.requested_at));
        exception when others then null;   -- the email is never a reason to undo a deletion
        end;
      end if;
      n := n + 1;
    exception when others then
      -- one account that fails never blocks the rest; it is retried tomorrow and the reason kept
      update public.account_deletions set attempts = attempts + 1, last_error = left(sqlerrm, 500)
       where user_id = r.user_id;
    end;
  end loop;
  perform set_config('request.jwt.claim.sub', '', true);
  perform set_config('request.jwt.claims', '', true);
  return n;
end $$;
revoke all on function public.purge_due_account_deletions() from public, anon, authenticated;

-- 4. What the emails say ----------------------------------------------------------------------------
-- Look A of "TermChamp Email Look" (the sign-in emails): navy band, white card, plain text.
create or replace function public.account_email_body(p_kind text, p_detail jsonb)
returns jsonb language plpgsql stable set search_path = public as $$
declare d text; subj text; para text; card text;
begin
  if p_kind = 'scheduled' then
    d := to_char((p_detail->>'purge_after')::timestamptz at time zone 'America/Los_Angeles', 'FMMon FMDD, YYYY');
    subj := 'Your TermChamp account will be deleted on ' || d;
    para := '<p style="margin:0 0 14px">We got your request to delete your TermChamp account. Other students can’t see it any more, and it will be <b>permanently deleted on ' || d || '</b>.</p>'
         || '<p style="margin:0 0 14px"><b>Changed your mind?</b> Sign in to TermChamp before then and tap <b>Recover my account</b> — everything comes back except your profile photo.</p>'
         || '<p style="margin:0">Didn’t ask for this? Sign in now and recover it, then change your password, and write to <a href="mailto:support@termchamp.com" style="color:#183178">support@termchamp.com</a>.</p>';
  else
    d := to_char(coalesce((p_detail->>'requested_at')::timestamptz, now()) at time zone 'America/Los_Angeles', 'FMMon FMDD, YYYY');
    subj := 'Your TermChamp account has been deleted';
    para := '<p style="margin:0 0 14px">Your TermChamp account and what was on it — your profile, classes, plans, friends and the messages you sent — have been permanently deleted, as you asked on ' || d || '.</p>'
         || case when coalesce((p_detail->>'delete_reviews')::boolean, false)
              then '<p style="margin:0 0 14px">Your reviews were deleted too.</p>'
              else '<p style="margin:0 0 14px">You chose to keep your reviews up for other students. They have no name on them, and nothing links them to you any more.</p>' end
         || '<p style="margin:0">Thanks for using TermChamp. Questions: <a href="mailto:support@termchamp.com" style="color:#183178">support@termchamp.com</a>.</p>';
  end if;
  card := '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1F7;padding:24px 0"><tr><td align="center">'
       || '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#fff;border-radius:14px;overflow:hidden;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
       || '<tr><td style="background:#183178;padding:18px 24px"><img src="https://termchamp.com/icon-192.png" width="32" height="32" alt="" style="vertical-align:middle;border-radius:8px"> '
       || '<span style="vertical-align:middle;color:#FBF7EE;font-family:Georgia,serif;font-size:22px;font-weight:bold">TermChamp</span></td></tr>'
       || '<tr><td style="padding:24px;color:#1E293B;font-size:15px;line-height:1.5">' || para || '</td></tr>'
       || '<tr><td style="padding:0 24px 22px;color:#64748B;font-size:12px">TermChamp · Made by students at Cal Poly · termchamp.com</td></tr>'
       || '</table></td></tr></table>';
  return jsonb_build_object('subject', subj, 'html', card);
end $$;
revoke all on function public.account_email_body(text, jsonb) from public, anon, authenticated;

-- 5. The sender (every 5 minutes) -------------------------------------------------------------------
create or replace function public.send_account_emails()
returns int language plpgsql security definer set search_path = public, extensions as $$
declare k text; r record; resp record; b jsonb; n int := 0;
begin
  -- 1. settle what was sent last time
  for r in select * from public.account_emails where request_id is not null and sent_at is null for update skip locked loop
    select status_code, content::text as content, error_msg into resp from net._http_response where id = r.request_id;
    if not found then
      if r.requested_at < now() - interval '1 hour' then   -- no answer kept: try again (same Idempotency-Key)
        update public.account_emails set request_id = null, attempts = attempts + 1, last_error = 'no response',
               next_try_at = now() + interval '15 minutes' * power(2, least(attempts, 8)) where id = r.id;
      end if;
      continue;
    end if;
    if resp.status_code between 200 and 299 then
      update public.account_emails set sent_at = now(), email = null, request_id = null, last_error = null where id = r.id;
    else
      update public.account_emails set request_id = null, attempts = attempts + 1,
             last_error = left(coalesce(resp.status_code::text, '') || ' ' || coalesce(resp.error_msg, resp.content, ''), 500),
             next_try_at = now() + interval '15 minutes' * power(2, least(attempts, 8))
       where id = r.id;
    end if;
  end loop;

  -- 2. never keep an address longer than 14 days, sent or not; the rows themselves go after 90
  update public.account_emails set email = null where email is not null and created_at < now() - interval '14 days';
  delete from public.account_emails where created_at < now() - interval '90 days' and email is null;

  -- 3. send what's waiting (without a key nothing is sent, and nothing is lost)
  begin
    select decrypted_secret into k from vault.decrypted_secrets where name = 'resend_api_key' order by created_at desc limit 1;
  exception when others then k := null;
  end;
  if k is null or k = '' then return 0; end if;
  for r in select * from public.account_emails
            where sent_at is null and request_id is null and attempts < 8 and email is not null and next_try_at <= now()
            order by id limit 5 for update skip locked loop
    -- recovered before the "scheduled" email went: it isn't sent
    if r.kind = 'scheduled' and not exists (select 1 from public.account_deletions d where d.user_id = r.user_id) then
      delete from public.account_emails where id = r.id; continue;
    end if;
    begin   -- one bad row never stops the others
      b := public.account_email_body(r.kind, r.detail);
      update public.account_emails set requested_at = now(), request_id = net.http_post(
          url := 'https://api.resend.com/emails',
          body := jsonb_build_object('from', 'TermChamp <noreply@termchamp.com>', 'to', jsonb_build_array(r.email),
                                     'reply_to', 'support@termchamp.com', 'subject', b->>'subject', 'html', b->>'html'),
          headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Content-Type', 'application/json',
                                        'Idempotency-Key', 'termchamp-account-email-' || r.id),
          timeout_milliseconds := 10000)
       where id = r.id;
      n := n + 1;
    exception when others then
      update public.account_emails set attempts = attempts + 1, last_error = left(sqlerrm, 500),
             next_try_at = now() + interval '15 minutes' * power(2, least(attempts, 8)) where id = r.id;
    end;
  end loop;
  return n;
end $$;
revoke all on function public.send_account_emails() from public, anon, authenticated;

select cron.schedule('termchamp-account-emails', '*/5 * * * *', 'select public.send_account_emails()');

-- 6. Self-checks -----------------------------------------------------------------------------------
do $$
begin
  if has_table_privilege('authenticated', 'public.account_emails', 'select') or has_table_privilege('anon', 'public.account_emails', 'select') then
    raise exception 'students can read account_emails';
  end if;
  if has_function_privilege('authenticated', 'public.send_account_emails()', 'execute') then raise exception 'students can run the sender'; end if;
  if has_function_privilege('authenticated', 'public.purge_due_account_deletions()', 'execute') then raise exception 'students can run the purge'; end if;
  if (select prosrc from pg_proc where oid = 'public.purge_due_account_deletions()'::regprocedure) not like '%account_emails%' then
    raise exception 'the purge does not queue the "deleted" email';
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'account_emails_on_request' and tgrelid = 'public.account_deletions'::regclass) then
    raise exception 'the "scheduled" email is not queued on a request';
  end if;
  if not exists (select 1 from cron.job where jobname = 'termchamp-account-emails' and active) then
    raise exception 'the email job is not scheduled';
  end if;
  if not exists (select 1 from cron.job where jobname = 'termchamp-purge-deleted-accounts' and active) then
    raise exception 'run 7-delete-account-30-days.sql first: the nightly deletion job is missing';
  end if;
end $$;

commit;
