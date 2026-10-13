-- Checks sql/professify-report-alerts.sql on Postgres 16 against a stand-in: reports exactly as
-- professify-safety.sql makes them (columns, checks, the insert policy and grants), profiles,
-- reviews, conversations, and stub cron / net / vault schemas (net.http_post records each call;
-- net._http_response is filled by the test, as pg_net would).
-- Run: ./run-check-report-alerts.sh
\set ON_ERROR_STOP 1

drop schema if exists auth cascade; drop schema if exists cron cascade; drop schema if exists net cascade;
drop schema if exists vault cascade; drop schema if exists extensions cascade;
drop schema if exists public cascade; create schema public;
create schema auth; create schema cron; create schema net; create schema vault; create schema extensions;
do $$ begin
  if not exists (select 1 from pg_roles where rolname='anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname='authenticated') then create role authenticated nologin; end if;
end $$;
grant usage on schema public, auth to anon, authenticated;
create table auth.users (id uuid primary key, email text);
create function auth.uid() returns uuid language sql stable as $$
  select (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')::uuid $$;
create table cron.job (jobname text primary key, schedule text, command text, active boolean default true);
create function cron.schedule(n text, s text, c text) returns bigint language sql as $$
  insert into cron.job values (n, s, c, true) on conflict (jobname) do update set schedule = excluded.schedule, command = excluded.command returning 1::bigint $$;
create sequence net.seq;
create table net.calls (id bigint, url text, body jsonb, headers jsonb);
create table net._http_response (id bigint primary key, status_code int, content text, error_msg text, created timestamptz default now());
create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds int default 5000)
returns bigint language plpgsql as $$ declare i bigint := nextval('net.seq'); begin insert into net.calls values (i, url, body, headers); return i; end $$;
create table vault.decrypted_secrets (name text, decrypted_secret text, created_at timestamptz default now());

create table public.profiles (id uuid primary key references auth.users(id), display_name text, username text);
create table public.reviews (id bigserial primary key, user_id uuid, professor_name text, course text, score numeric, note text);
create table public.conversations (id uuid primary key default gen_random_uuid(), kind text, title text, created_by uuid);
-- reports, as professify-safety.sql
create table public.reports (
  id uuid primary key default gen_random_uuid(),
  reporter uuid references auth.users(id) on delete set null,
  kind text not null check (kind in ('review','post','message','user','suggestion')),
  target_id text, target_user uuid references auth.users(id) on delete set null,
  reason text not null check (reason in ('harassment','hate','threat','private_info','impersonation','spam','sexual','not_about_teaching','other')),
  note text, status text not null default 'open' check (status in ('open','actioned','dismissed')),
  action_taken text, resolved_by uuid, resolved_at timestamptz, created_at timestamptz not null default now());
alter table public.reports enable row level security;
create policy reports_read on public.reports for select to authenticated using (reporter = auth.uid());
create policy reports_file_own on public.reports for insert to authenticated with check (reporter = auth.uid() and status = 'open' and resolved_by is null);
revoke all on public.reports from anon, public, authenticated;
grant select, insert on public.reports to authenticated;

insert into auth.users (id) values ('aaaaaaaa-0000-0000-0000-00000000000a'), ('bbbbbbbb-0000-0000-0000-00000000000b'), ('cccccccc-0000-0000-0000-00000000000c');
insert into public.profiles values ('aaaaaaaa-0000-0000-0000-00000000000a', 'Ada Reporter', 'ada'),
  ('bbbbbbbb-0000-0000-0000-00000000000b', 'Bo <b>Bad</b>', 'bo'), ('cccccccc-0000-0000-0000-00000000000c', 'Cy', 'cy');
insert into public.reviews (id, user_id, professor_name, course, score, note) values (42, 'bbbbbbbb-0000-0000-0000-00000000000b', 'Dr. Smith', 'FIN 342', 1, 'He is an <script>alert(1)</script> idiot'),
  (43, 'bbbbbbbb-0000-0000-0000-00000000000b', 'Dr. Jones', null, null, 'meh');
insert into public.conversations (id, kind, title, created_by) values ('dddddddd-0000-0000-0000-00000000000d', 'group', 'Rude & crude', 'bbbbbbbb-0000-0000-0000-00000000000b');

-- a report filed before the migration: never mailed about
insert into public.reports (reporter, kind, target_user, reason, created_at) values ('cccccccc-0000-0000-0000-00000000000c', 'user', 'bbbbbbbb-0000-0000-0000-00000000000b', 'spam', now() - interval '3 days');

-- the migration, twice
\i :mig
\i :mig

-- 1. nobody but the functions can read the queue, the bodies, or run the sender; the job runs every 5 minutes
do $$ begin
  if has_table_privilege('authenticated', 'public.report_alerts', 'select') or has_table_privilege('anon', 'public.report_alerts', 'select') then raise exception 'FAIL students can read the queue'; end if;
  if has_function_privilege('authenticated', 'public.send_report_alerts()', 'execute') or has_function_privilege('anon', 'public.send_report_alerts()', 'execute') then raise exception 'FAIL students can run the sender'; end if;
  if has_function_privilege('authenticated', 'public.report_alert_body(uuid,text)', 'execute') then raise exception 'FAIL students can read report emails'; end if;
  if not exists (select 1 from cron.job where jobname = 'termchamp-report-alerts' and schedule = '*/5 * * * *' and command like '%send_report_alerts%') then raise exception 'FAIL no job'; end if;
  if (select count(*) from cron.job where jobname = 'termchamp-report-alerts') <> 1 then raise exception 'FAIL job twice'; end if;
  if exists (select 1 from public.report_alerts) then raise exception 'FAIL an old report was queued'; end if;
end $$;

-- 2. A student files three reports through the real policy: each queues one "new"
do $$ declare rid uuid; begin
  perform set_config('request.jwt.claims', '{"sub":"aaaaaaaa-0000-0000-0000-00000000000a","role":"authenticated"}', true);
  set local role authenticated;
  insert into public.reports (reporter, kind, target_id, target_user, reason, note) values ('aaaaaaaa-0000-0000-0000-00000000000a', 'review', '42', null, 'harassment', 'He is an <script>alert(1)</script> idiot');
  insert into public.reports (reporter, kind, target_id, target_user, reason, note) values ('aaaaaaaa-0000-0000-0000-00000000000a', 'message', '7', 'bbbbbbbb-0000-0000-0000-00000000000b', 'threat', 'meet me <img src=x onerror=alert(1)> after class');
  insert into public.reports (reporter, kind, target_id, target_user, reason) values ('aaaaaaaa-0000-0000-0000-00000000000a', 'user', 'group:dddddddd-0000-0000-0000-00000000000d', 'bbbbbbbb-0000-0000-0000-00000000000b', 'hate');
  reset role;
  if (select count(*) from public.report_alerts where kind = 'new') <> 3 then raise exception 'FAIL expected 3 new alerts, got %', (select count(*) from public.report_alerts); end if;
end $$;

-- 3. The trigger can't stop a report: with the queue broken, a report still goes in
do $$ begin
  alter table public.report_alerts rename to report_alerts_x;
  insert into public.reports (reporter, kind, target_user, reason) values ('cccccccc-0000-0000-0000-00000000000c', 'user', 'bbbbbbbb-0000-0000-0000-00000000000b', 'other');
  alter table public.report_alerts_x rename to report_alerts;
  if not exists (select 1 from public.reports where reporter = 'cccccccc-0000-0000-0000-00000000000c' and reason = 'other') then raise exception 'FAIL report blocked by its email'; end if;
end $$;

-- 4. No key: nothing sent, nothing lost
do $$ begin
  if public.send_report_alerts() <> 0 or exists (select 1 from net.calls) then raise exception 'FAIL sent without a key'; end if;
  if (select count(*) from public.report_alerts where sent_at is null and attempts = 0) <> 3 then raise exception 'FAIL dropped without a key'; end if;
end $$;

-- 5. With the key: three emails to support@, from noreply, escaped, with the content and the deadline
insert into vault.decrypted_secrets (name, decrypted_secret) values ('resend_api_key', 're_test_key');
do $$ declare n int; c record; h text; begin
  n := public.send_report_alerts();
  if n <> 3 then raise exception 'FAIL expected 3 sent, got %', n; end if;
  for c in select * from net.calls loop
    if c.url <> 'https://api.resend.com/emails' or c.headers->>'Authorization' <> 'Bearer re_test_key' then raise exception 'FAIL wrong call'; end if;
    if c.headers->>'Idempotency-Key' !~ '^termchamp-report-alert-\d+$' then raise exception 'FAIL no idempotency key'; end if;
    if c.body->>'from' <> 'TermChamp <noreply@termchamp.com>' or c.body->'to'->>0 <> 'support@termchamp.com' or jsonb_array_length(c.body->'to') <> 1 then raise exception 'FAIL addresses %', c.body; end if;
    h := c.body->>'html';
    if h ~ '<script|<img src=x|<b>Bad' then raise exception 'FAIL unescaped student text: %', h; end if;
    if h !~ 'Handle by' or h !~ ' PT' or h !~ 'Open the report queue' then raise exception 'FAIL missing deadline or how to act'; end if;
    if h !~ 'Bo &lt;b&gt;Bad&lt;/b&gt; \(@bo\)' or h !~ 'Ada Reporter' then raise exception 'FAIL who'; end if;
  end loop;
  select body->>'html' into h from net.calls where body->>'subject' = 'New report: a review — harassment or bullying';
  if h is null or h !~ 'Dr\. Smith' or h !~ 'FIN 342' or h !~ '&lt;script&gt;alert\(1\)&lt;/script&gt; idiot' then raise exception 'FAIL review email %', h; end if;
  if h !~ 'Other reports</td><td>3 about this person before this one' then raise exception 'FAIL prior count %', h; end if;
  if (length(h) - length(replace(h, 'alert(1)', ''))) / length('alert(1)') <> 1 then raise exception 'FAIL the review is shown twice'; end if;
  if h ~ 'Note with the report' then raise exception 'FAIL the copied review shown as a note'; end if;
  select body->>'html' into h from net.calls where body->>'subject' = 'New report: a message — threats or violence';
  if h is null or h !~ 'The message' or h !~ 'meet me &lt;img src=x onerror=alert\(1\)&gt; after class' then raise exception 'FAIL message email %', h; end if;
  select body->>'html' into h from net.calls where body->>'subject' = 'New report: a group name — hate or discrimination';
  if h is null or h !~ 'Rude &amp; crude' then raise exception 'FAIL group email %', h; end if;
  -- in flight: not sent again
  if public.send_report_alerts() <> 0 or (select count(*) from net.calls) <> 3 then raise exception 'FAIL re-sent while in flight'; end if;
end $$;

-- 6. Answers: 200 → sent; 500 → kept with its reason and retried later, under the same key
do $$ declare c record; k1 text; begin
  for c in select * from net.calls order by id loop
    insert into net._http_response (id, status_code, content) values (c.id, case when c.id = 3 then 500 else 200 end, '{"message":"x"}');
  end loop;
  perform public.send_report_alerts();
  if (select count(*) from public.report_alerts where sent_at is not null) <> 2 then raise exception 'FAIL 200s not marked sent'; end if;
  if not exists (select 1 from public.report_alerts where sent_at is null and attempts = 1 and last_error like '500%' and next_try_at > now()) then raise exception 'FAIL 500 not kept for retry'; end if;
  if (select count(*) from net.calls) <> 3 then raise exception 'FAIL retried at once'; end if;
  select headers->>'Idempotency-Key' into k1 from net.calls where id = 3;
  insert into public.reports (reporter, kind, target_user, reason, status) values ('cccccccc-0000-0000-0000-00000000000c', 'post', 'bbbbbbbb-0000-0000-0000-00000000000b', 'spam', 'dismissed');
  update public.profiles set display_name = 'Bo Renamed' where id = 'bbbbbbbb-0000-0000-0000-00000000000b';
  update public.report_alerts set next_try_at = now() where sent_at is null;
  perform public.send_report_alerts();
  if (select count(*) from net.calls) <> 4 or (select headers->>'Idempotency-Key' from net.calls where id = 4) <> k1 then raise exception 'FAIL retry not sent with the same key'; end if;
  if (select body from net.calls where id = 4) <> (select body from net.calls where id = 3) then raise exception 'FAIL a retry sent a different email under the same key'; end if;
  update public.profiles set display_name = 'Bo <b>Bad</b>' where id = 'bbbbbbbb-0000-0000-0000-00000000000b';
end $$;

-- 7. Handled before its email: not sent
do $$ declare rid uuid; before int; begin
  insert into public.reports (reporter, kind, target_user, reason) values ('cccccccc-0000-0000-0000-00000000000c', 'user', 'aaaaaaaa-0000-0000-0000-00000000000a', 'spam') returning id into rid;
  update public.reports set status = 'dismissed' where id = rid;
  select count(*) into before from net.calls;
  perform public.send_report_alerts();
  if (select count(*) from net.calls) <> before then raise exception 'FAIL emailed a handled report'; end if;
  if not exists (select 1 from public.report_alerts where report_id = rid and sent_at is not null and last_error = 'handled before sending') then raise exception 'FAIL handled row not closed'; end if;
end $$;

-- 8. Still open 20 hours on: one "Still open"; handled ones and old ones get none
do $$ declare before int; s text; begin
  update public.reports set created_at = now() - interval '21 hours' where reason = 'harassment';
  update public.reports set created_at = now() - interval '21 hours', status = 'actioned' where reason = 'threat';
  select count(*) into before from net.calls;
  perform public.send_report_alerts();
  if (select count(*) from public.report_alerts where kind = 'reminder') <> 1 then raise exception 'FAIL expected one reminder, got %', (select count(*) from public.report_alerts where kind = 'reminder'); end if;
  select body->>'subject' into s from net.calls where id > before and body->>'subject' like 'Still open:%';
  if s is null or s !~ '^Still open: a review reported for harassment or bullying — handle by ' then raise exception 'FAIL reminder subject %', s; end if;
  if (select body->>'html' from net.calls where body->>'subject' = s) !~ 'still open, 21 hours after' or (select body->>'html' from net.calls where body->>'subject' = s) ~ 'past that' then raise exception 'FAIL reminder body'; end if;
  perform public.send_report_alerts(); perform public.send_report_alerts();
  if (select count(*) from public.report_alerts where kind = 'reminder') <> 1 then raise exception 'FAIL reminder queued twice'; end if;
end $$;

-- 9. A report about a deleted review / deleted person still emails (nothing to quote, no crash)
do $$ declare rid uuid; b jsonb; begin
  insert into public.reports (reporter, kind, target_id, target_user, reason) values ('aaaaaaaa-0000-0000-0000-00000000000a', 'review', '999', null, 'spam') returning id into rid;
  b := public.report_alert_body(rid, 'new');
  if b->>'subject' is null or b->>'html' is null or b->>'html' !~ 'About</td><td>—' then raise exception 'FAIL body for a gone review %', b; end if;
end $$;

-- 10. A review with no course or score: no empty brackets; overdue reminder says so
do $$ declare rid uuid; b jsonb; begin
  insert into public.reports (reporter, kind, target_id, target_user, reason, created_at) values ('cccccccc-0000-0000-0000-00000000000c', 'review', '43', null, 'other', now() - interval '30 hours') returning id into rid;
  b := public.report_alert_body(rid, 'reminder');
  if b->>'html' ~ '\(\)|, +stars' or b->>'html' !~ 'The review of Dr\. Jones</p>' then raise exception 'FAIL empty fields shown %', b->>'html'; end if;
  if b->>'html' !~ 'still open, 30 hours after' or b->>'html' !~ 'past that' then raise exception 'FAIL overdue wording'; end if;
  if b->>'html' !~ 'About</td><td>Bo &lt;b&gt;' then raise exception 'FAIL review author not shown'; end if;
end $$;

\echo 'check-report-alerts: all passed'
