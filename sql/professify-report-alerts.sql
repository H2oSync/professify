-- TermChamp: an email to support@ for every report (2026-10-05)
--
-- Apple 1.2 and our own terms: we act on reports of objectionable content within 24 hours. Until
-- now nothing told anyone a report had come in — it sat in the moderator queue until someone
-- happened to look. Now:
--   · "new"      — within about 5 minutes of a report, an email to support@termchamp.com with what
--                  was reported, why, about whom, how many reports that person already has, and the
--                  time it must be handled by (24 hours after it was filed).
--   · "reminder" — if the same report is still open 20 hours after it was filed, one more email,
--                  "Still open", so the 24 hours isn't missed.
--   A report that has already been handled (actioned or dismissed) before its email goes out is
--   not emailed.
--
-- Same machinery as the account emails (RUN 9, professify-deletion-emails.sql): a queue nobody but
-- these functions can read, a job every 5 minutes, Resend through pg_net with the same Vault key
-- (resend_api_key), retries with growing gaps, and an Idempotency-Key so a retry can't send twice.
-- A report is never stopped or slowed by its email: the trigger swallows its own errors.
--
-- Where to act: termchamp.com on a computer, signed in as a moderator → Settings → Open the report
-- queue. Moderators are the rows in public.moderators (add one: insert into public.moderators
-- (user_id) select id from auth.users where email = '…';).
--
-- Needs: professify-safety.sql (reports, moderators), and RUN 9 done (pg_net on, the Vault key).
-- Admin check:
--   select id, report_id, kind, created_at, sent_at, attempts, last_error from report_alerts order by id desc limit 20;
-- One transaction; self-checks raise. Safe to run twice.

begin;

do $$ begin
  begin
    create extension if not exists pg_net with schema extensions;
  exception when others then
    raise exception 'pg_net is not on. Supabase → Database → Extensions → pg_net → Enable, then run this file again. (%)', sqlerrm;
  end;
  if to_regclass('public.reports') is null then raise exception 'run professify-safety.sql first: there is no reports table'; end if;
end $$;

-- 1. The queue ------------------------------------------------------------------------------------
create table if not exists public.report_alerts (
  id           bigserial primary key,
  report_id    uuid not null references public.reports(id) on delete cascade,
  kind         text not null check (kind in ('new', 'reminder')),
  created_at   timestamptz not null default now(),
  request_id   bigint,                        -- pg_net's id while a send is in flight
  requested_at timestamptz,
  sent_at      timestamptz,
  attempts     int not null default 0,
  next_try_at  timestamptz not null default now(),
  last_error   text,
  subject      text,                          -- built once, on the first try: a retry under the same
  html         text,                          -- Idempotency-Key must send exactly the same email
  unique (report_id, kind)                    -- one of each per report, ever
);
alter table public.report_alerts add column if not exists subject text;
alter table public.report_alerts add column if not exists html text;
alter table public.report_alerts enable row level security;   -- no policies: functions only
revoke all on public.report_alerts from public, anon, authenticated;
revoke all on sequence public.report_alerts_id_seq from public, anon, authenticated;
create index if not exists report_alerts_todo_idx on public.report_alerts (id) where sent_at is null;

-- 2. "New": queued as the report is filed ------------------------------------------------------------
create or replace function public.report_alerts_on_report()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.report_alerts (report_id, kind) values (new.id, 'new') on conflict do nothing;
  return new;
exception when others then
  return new;   -- an email must never stop a report being filed
end $$;
revoke all on function public.report_alerts_on_report() from public, anon, authenticated;
drop trigger if exists report_alerts_on_report on public.reports;
create trigger report_alerts_on_report after insert on public.reports
  for each row execute function public.report_alerts_on_report();

-- 3. What the email says -------------------------------------------------------------------------------
-- Everything a student typed is escaped: a report is written by one student about another, and
-- either could try to put markup in it. Null stays null, so an empty field can be left out.
create or replace function public.report_alert_esc(t text)
returns text language sql immutable as $$
  select replace(replace(replace(replace(replace(t, '&', '&amp;'), '<', '&lt;'), '>', '&gt;'), '"', '&quot;'), '''', '&#39;')
$$;
revoke all on function public.report_alert_esc(text) from public, anon, authenticated;

create or replace function public.report_alert_body(p_report uuid, p_kind text)
returns jsonb language plpgsql stable security definer set search_path = public as $$
declare
  r record; about uuid; who text; uname text; by_name text; prior int; reason text; what text; hrs int;
  due text; filed text; rows text := ''; extra text := ''; subj text; para text; card text;
  rv jsonb; gtitle text;
begin
  select * into r from public.reports where id = p_report;
  if not found then return null; end if;

  if r.kind = 'review' then
    begin
      select to_jsonb(v) into rv from public.reviews v where v.id::text = r.target_id;
    exception when others then rv := null;
    end;
  end if;
  -- a review report names no one (reviews are anonymous to students); the moderator sees the author
  about := coalesce(r.target_user, case when rv ? 'user_id' and (rv->>'user_id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then (rv->>'user_id')::uuid end);
  select p.display_name, p.username into who, uname from public.profiles p where p.id = about;
  select p.display_name into by_name from public.profiles p where p.id = r.reporter;
  -- other reports about this person, filed up to this one (fixed, so the email reads the same on a retry)
  select count(*)::int into prior from public.reports x
   where x.id <> r.id and x.created_at <= r.created_at
     and (x.target_user = about or (x.kind = 'review' and x.target_user is null and exists (
          select 1 from public.reviews v2 where v2.id::text = x.target_id and to_jsonb(v2)->>'user_id' = about::text)));

  reason := case r.reason
    when 'harassment' then 'Harassment or bullying' when 'hate' then 'Hate or discrimination'
    when 'threat' then 'Threats or violence' when 'private_info' then 'Shares private information'
    when 'impersonation' then 'Pretending to be someone else' when 'sexual' then 'Sexual content'
    when 'spam' then 'Spam or advertising' when 'not_about_teaching' then 'Not about the class or teaching'
    else 'Something else' end;
  what := case
    when r.kind = 'user' and r.target_id like 'group:%' then 'A group name'
    when r.kind = 'user' then 'A person' when r.kind = 'review' then 'A review'
    when r.kind = 'message' then 'A message' when r.kind = 'post' then 'A post'
    else 'A suggestion' end;
  filed := to_char(r.created_at at time zone 'America/Los_Angeles', 'FMDy FMMon FMDD, FMHH12:MI AM') || ' PT';
  due   := to_char((r.created_at + interval '24 hours') at time zone 'America/Los_Angeles', 'FMDy FMMon FMDD, FMHH12:MI AM') || ' PT';

  -- what was reported, in its own words
  if r.kind = 'review' then
    if rv is not null then
      extra := '<p style="margin:0 0 6px;color:#64748B;font-size:13px">The review'
            || coalesce(' of ' || report_alert_esc(nullif(rv->>'professor_name', '')), '')
            || coalesce(' (' || report_alert_esc(nullif(rv->>'course', '')) || ')', '')
            || coalesce(', ' || report_alert_esc(nullif(rv->>'score', '')) || ' stars', '') || '</p>'
            || '<blockquote style="margin:0 0 14px;padding:10px 12px;background:#F8FAFC;border-left:3px solid #CBD5E1;white-space:pre-wrap">'
            || report_alert_esc(left(coalesce(rv->>'note', '(no written review)'), 2000)) || '</blockquote>';
    end if;
  elsif r.kind = 'user' and r.target_id like 'group:%' then
    begin
      select c.title into gtitle from public.conversations c where c.id::text = substr(r.target_id, 7);
    exception when others then gtitle := null;
    end;
    extra := '<p style="margin:0 0 6px;color:#64748B;font-size:13px">The group name (they made the group)</p>'
          || '<blockquote style="margin:0 0 14px;padding:10px 12px;background:#F8FAFC;border-left:3px solid #CBD5E1">'
          || report_alert_esc(coalesce(gtitle, '(the group is gone)')) || '</blockquote>';
  end if;
  -- the phone app copies the review into the note; once is enough
  if r.note is not null and r.note <> '' and not (r.kind = 'review' and rv is not null and btrim(r.note) = btrim(coalesce(rv->>'note', ''))) then
    extra := extra || '<p style="margin:0 0 6px;color:#64748B;font-size:13px">'
          || case when r.kind = 'message' then 'The message' else 'Note with the report' end || '</p>'
          || '<blockquote style="margin:0 0 14px;padding:10px 12px;background:#F8FAFC;border-left:3px solid #CBD5E1;white-space:pre-wrap">'
          || report_alert_esc(left(r.note, 2000)) || '</blockquote>';
  end if;

  rows := '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">What</td><td>' || what || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Why</td><td><b>' || reason || '</b></td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">About</td><td>'
       || case when about is null then '—' else report_alert_esc(coalesce(who, 'Someone')) || coalesce(' (@' || report_alert_esc(uname) || ')', '') end || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Other reports</td><td>'
       || case when about is null then '—' when prior = 0 then 'None before this one' else prior::text || ' about this person before this one' end || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Reported by</td><td>' || report_alert_esc(coalesce(by_name, 'Someone')) || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Filed</td><td>' || filed || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Handle by</td><td><b>' || due || '</b></td></tr>';

  if p_kind = 'reminder' then
    subj := 'Still open: ' || lower(what) || ' reported for ' || lower(reason) || ' — handle by ' || due;
    hrs := floor(extract(epoch from now() - r.created_at) / 3600)::int;
    para := '<p style="margin:0 0 14px"><b>This report is still open, ' || hrs || ' hours after it was filed.</b> We promise to act on reports within 24 hours'
         || case when hrs >= 24 then ' — this one is past that, so please handle it now' else '' end || '.</p>';
  else
    subj := 'New report: ' || lower(what) || ' — ' || lower(reason);
    para := '<p style="margin:0 0 14px">Someone reported something on TermChamp. It needs to be handled within 24 hours.</p>';
  end if;
  para := para
       || '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 16px;font-size:14px">' || rows || '</table>'
       || extra
       || '<p style="margin:0 0 6px"><b>To act on it:</b> sign in at <a href="https://termchamp.com" style="color:#183178">termchamp.com</a> on a computer → Settings → <b>Open the report queue</b>. Remove it, suspend the person, or dismiss it.</p>'
       || '<p style="margin:0;color:#94A3B8;font-size:12px">Report ' || r.id || '</p>';
  card := '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1F7;padding:24px 0"><tr><td align="center">'
       || '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fff;border-radius:14px;overflow:hidden;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
       || '<tr><td style="background:#183178;padding:18px 24px"><span style="color:#FBF7EE;font-family:Georgia,serif;font-size:20px;font-weight:bold">TermChamp · Reports</span></td></tr>'
       || '<tr><td style="padding:24px;color:#1E293B;font-size:15px;line-height:1.5">' || para || '</td></tr>'
       || '</table></td></tr></table>';
  return jsonb_build_object('subject', subj, 'html', card);
end $$;
revoke all on function public.report_alert_body(uuid, text) from public, anon, authenticated;

-- 4. The sender (every 5 minutes) -------------------------------------------------------------------
create or replace function public.send_report_alerts()
returns int language plpgsql security definer set search_path = public, extensions as $$
declare k text; r record; resp record; b jsonb; n int := 0;
begin
  -- 1. settle what was sent last time
  for r in select * from public.report_alerts where request_id is not null and sent_at is null for update skip locked loop
    select status_code, content::text as content, error_msg into resp from net._http_response where id = r.request_id;
    if not found then
      if r.requested_at < now() - interval '1 hour' then   -- no answer kept: try again (same Idempotency-Key)
        update public.report_alerts set request_id = null, attempts = attempts + 1, last_error = 'no response',
               next_try_at = now() + interval '5 minutes' * power(2, least(attempts, 6)) where id = r.id;
      end if;
      continue;
    end if;
    if resp.status_code between 200 and 299 then
      update public.report_alerts set sent_at = now(), request_id = null, last_error = null where id = r.id;
    else
      update public.report_alerts set request_id = null, attempts = attempts + 1,
             last_error = left(coalesce(resp.status_code::text, '') || ' ' || coalesce(resp.error_msg, resp.content, ''), 500),
             next_try_at = now() + interval '5 minutes' * power(2, least(attempts, 6))
       where id = r.id;
    end if;
  end loop;

  -- 2. a report still open 20 hours on gets one "Still open" (only reports from the last 2 days,
  --    so turning this on never mails about old ones)
  insert into public.report_alerts (report_id, kind)
  select x.id, 'reminder' from public.reports x
   where x.status = 'open' and x.created_at <= now() - interval '20 hours' and x.created_at > now() - interval '2 days'
  on conflict do nothing;

  -- 3. tidy: the stored copy of a sent email is cleared after 30 days, the row after 90 (the report itself stays)
  update public.report_alerts set html = null where html is not null and sent_at is not null and sent_at < now() - interval '30 days';
  delete from public.report_alerts where created_at < now() - interval '90 days';

  -- 4. send what's waiting (without a key nothing is sent, and nothing is lost)
  begin
    select decrypted_secret into k from vault.decrypted_secrets where name = 'resend_api_key' order by created_at desc limit 1;
  exception when others then k := null;
  end;
  if k is null or k = '' then return 0; end if;
  for r in select a.* from public.report_alerts a
            where a.sent_at is null and a.request_id is null and a.attempts < 8 and a.next_try_at <= now()
            order by a.id limit 10 for update skip locked loop
    -- already handled before its email went: nothing to tell
    if not exists (select 1 from public.reports x where x.id = r.report_id and x.status = 'open') then
      update public.report_alerts set sent_at = now(), last_error = 'handled before sending' where id = r.id; continue;
    end if;
    begin   -- one bad row never stops the others
      if r.subject is null or r.html is null then
        b := public.report_alert_body(r.report_id, r.kind);
        if b is null or b->>'subject' is null then raise exception 'no email for report %', r.report_id; end if;
        update public.report_alerts set subject = b->>'subject', html = b->>'html' where id = r.id;
      else
        b := jsonb_build_object('subject', r.subject, 'html', r.html);
      end if;
      update public.report_alerts set requested_at = now(), request_id = net.http_post(
          url := 'https://api.resend.com/emails',
          body := jsonb_build_object('from', 'TermChamp <noreply@termchamp.com>', 'to', jsonb_build_array('support@termchamp.com'),
                                     'subject', b->>'subject', 'html', b->>'html'),
          headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Content-Type', 'application/json',
                                        'Idempotency-Key', 'termchamp-report-alert-' || r.id),
          timeout_milliseconds := 10000)
       where id = r.id;
      n := n + 1;
    exception when others then
      update public.report_alerts set attempts = attempts + 1, last_error = left(sqlerrm, 500),
             next_try_at = now() + interval '5 minutes' * power(2, least(attempts, 6)) where id = r.id;
    end;
  end loop;
  return n;
end $$;
revoke all on function public.send_report_alerts() from public, anon, authenticated;

select cron.schedule('termchamp-report-alerts', '*/5 * * * *', 'select public.send_report_alerts()');

-- 5. Self-checks -----------------------------------------------------------------------------------
do $$
begin
  if has_table_privilege('authenticated', 'public.report_alerts', 'select') or has_table_privilege('anon', 'public.report_alerts', 'select') then
    raise exception 'students can read report_alerts';
  end if;
  if has_function_privilege('authenticated', 'public.send_report_alerts()', 'execute') then raise exception 'students can run the sender'; end if;
  if has_function_privilege('authenticated', 'public.report_alert_body(uuid,text)', 'execute') or has_function_privilege('anon', 'public.report_alert_body(uuid,text)', 'execute') then raise exception 'students can read report emails'; end if;
  if has_function_privilege('authenticated', 'public.report_alert_esc(text)', 'execute') or has_function_privilege('authenticated', 'public.report_alerts_on_report()', 'execute') then raise exception 'students can run the report email helpers'; end if;
  if not exists (select 1 from pg_trigger where tgname = 'report_alerts_on_report' and tgrelid = 'public.reports'::regclass) then
    raise exception 'a new report is not queued for an email';
  end if;
  if not exists (select 1 from cron.job where jobname = 'termchamp-report-alerts' and active) then
    raise exception 'the report email job is not scheduled';
  end if;
  if not exists (select 1 from vault.decrypted_secrets where name = 'resend_api_key') then
    raise notice 'No resend_api_key in the Vault yet: report emails will wait until it is added (RUN 9 explains how).';
  end if;
end $$;

commit;
