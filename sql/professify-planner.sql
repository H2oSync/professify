-- TermChamp: the report → Planner → Plans flow (2026-10-08). RUN 14.
--
-- What this adds, all owner-only, nothing a friend or another student can read:
--   1. degree_audit    — what the student's Degree Progress Report SAYS, requirement by requirement
--                        (Satisfied / Not Satisfied / In Progress, units needed, the classes that clear
--                        it). One row per account, replaced on every upload. NO grades, NO EMPLID, NO name:
--                        the phone strips those before anything leaves readDpr(), and this table has no
--                        column for them. The Planner ranks from this instead of recomputing from our
--                        flowcharts (dpr-planner-plans-design-2026-10-08.md).
--   2. planner_prefs   — "what matters most" (one of degree | professors | friends) and units next term
--                        (12–20, default 16). Asked once on the Planner's first open; Edit any time.
--   3. dpr_flags       — a line of the report the student flagged as read wrong, DE-IDENTIFIED: the
--                        requirement's words, the verdict and the numbers. No user id, no name, no free
--                        text. This is how real reports keep teaching the reader. Students can insert;
--                        only the dashboard (service role) can read. 30 a day per account, counted by a
--                        hash that changes every day (so a day's flags can't be joined to another day's).
--                        Kept 180 days.
--   4. "Send the link to my laptop": request_planner_link() queues ONE email to the student's own
--                        verified address (3 a day) with the three portal steps and the termchamp.com
--                        drag-and-drop link; send_planner_links() mails the queue every 5 minutes through
--                        Resend with the same Vault key the report and deletion emails use
--                        (resend_api_key). Without the key the email waits; nothing breaks.
-- Idempotent: safe to run again. One transaction. Self-checks at the end raise on anything wrong.
-- Check after:
--   select has_table_privilege('authenticated', 'public.degree_audit', 'select');            -- t
--   select count(*) from pg_policies where tablename in ('degree_audit','planner_prefs','dpr_flags'); -- 9
--   select jobname, active from cron.job where jobname = 'termchamp-planner-links';           -- active
begin;

do $$ begin
  begin create extension if not exists pg_cron; exception when others then null; end;
  begin create extension if not exists pg_net with schema extensions; exception when others then null; end;
end $$;

-- 1. degree_audit ---------------------------------------------------------------------------------
create table if not exists public.degree_audit (
  user_id       uuid primary key references auth.users(id) on delete cascade,
  printed_on    date,
  catalog       text,
  major         text,
  concentration text,
  units_used    numeric,
  units_needed  numeric,
  requirements  jsonb not null default '[]'::jsonb,
  read_at       timestamptz not null default now(),
  constraint degree_audit_requirements_array check (jsonb_typeof(requirements) = 'array'),
  constraint degree_audit_requirements_size  check (pg_column_size(requirements) < 400000),
  constraint degree_audit_text_len check (length(coalesce(catalog,'')) <= 80 and length(coalesce(major,'')) <= 120 and length(coalesce(concentration,'')) <= 120)
);
-- lines the student marked done themselves ("I know it counts"): [{code, label, at}], kept across uploads
alter table public.degree_audit add column if not exists overrides jsonb not null default '[]'::jsonb;
alter table public.degree_audit drop constraint if exists degree_audit_overrides_ok;
alter table public.degree_audit drop constraint if exists degree_audit_requirements_count;
alter table public.degree_audit add constraint degree_audit_requirements_count check (jsonb_typeof(requirements) <> 'array' or jsonb_array_length(requirements) <= 400);
alter table public.degree_audit enable row level security;
drop policy if exists degree_audit_own_select on public.degree_audit;
drop policy if exists degree_audit_own_insert on public.degree_audit;
drop policy if exists degree_audit_own_update on public.degree_audit;
drop policy if exists degree_audit_own_delete on public.degree_audit;
create policy degree_audit_own_select on public.degree_audit for select to authenticated using (user_id = auth.uid());
create policy degree_audit_own_insert on public.degree_audit for insert to authenticated with check (user_id = auth.uid());
create policy degree_audit_own_update on public.degree_audit for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy degree_audit_own_delete on public.degree_audit for delete to authenticated using (user_id = auth.uid());
revoke all on public.degree_audit from public, anon;
grant select, insert, update, delete on public.degree_audit to authenticated;

-- No grades and no IDs, ever: a requirement entry may carry a label, a verdict, counts and course codes —
-- never a grade cell. The check walks EVERY level of the entries and refuses (a) a key named like a grade,
-- an ID, a name or a note, at any depth, and (b) any text with a 7-digit number, "EMPLID", "Name:", a
-- grade beside units ("B+ 3.00") or longer than 300 characters. The phone checks the same before sending.
create or replace function public.dpr_text_ok(t text) returns boolean language sql immutable as $$
  select t is null or (length(t) <= 300 and t !~ '[0-9]{7}' and t !~* 'emplid' and t !~* '\mname\s*:'
                       and t !~* '(^|\s)([a-df][+-]?|cr|nc|w|wu|ic|i|rp|au|p|np|ip|rd|ng)\s+[0-9]+\.[0-9]{2}\M')
$$;
create or replace function public.degree_audit_no_grades(req jsonb) returns boolean language sql immutable as $$
  select jsonb_typeof(req) <> 'array' or (
    not exists (
      select 1 from jsonb_path_query(req, 'strict $.**') v, jsonb_object_keys(case when jsonb_typeof(v) = 'object' then v else '{}'::jsonb end) k
      where lower(k) in ('grade', 'grades', 'gpa', 'letter', 'emplid', 'name', 'student_name', 'note', 'notes'))
    and not exists (
      select 1 from jsonb_path_query(req, 'strict $.**') v
      where jsonb_typeof(v) = 'string' and not public.dpr_text_ok(v #>> '{}')))
$$;
alter table public.degree_audit drop constraint if exists degree_audit_no_grades;
alter table public.degree_audit add constraint degree_audit_no_grades check (public.degree_audit_no_grades(requirements));
alter table public.degree_audit add constraint degree_audit_overrides_ok check (jsonb_typeof(overrides) = 'array' and jsonb_array_length(overrides) <= 100
  and pg_column_size(overrides) < 40000 and public.degree_audit_no_grades(overrides));

-- 2. planner_prefs --------------------------------------------------------------------------------
create table if not exists public.planner_prefs (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  priority   text not null default 'degree' check (priority in ('degree', 'professors', 'friends')),
  units      int  not null default 16 check (units between 12 and 20),
  updated_at timestamptz not null default now()
);
alter table public.planner_prefs enable row level security;
drop policy if exists planner_prefs_own_select on public.planner_prefs;
drop policy if exists planner_prefs_own_insert on public.planner_prefs;
drop policy if exists planner_prefs_own_update on public.planner_prefs;
drop policy if exists planner_prefs_own_delete on public.planner_prefs;
create policy planner_prefs_own_select on public.planner_prefs for select to authenticated using (user_id = auth.uid());
create policy planner_prefs_own_insert on public.planner_prefs for insert to authenticated with check (user_id = auth.uid());
create policy planner_prefs_own_update on public.planner_prefs for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy planner_prefs_own_delete on public.planner_prefs for delete to authenticated using (user_id = auth.uid());
revoke all on public.planner_prefs from public, anon;
grant select, insert, update, delete on public.planner_prefs to authenticated;

-- 3. dpr_flags (de-identified, insert-only for students) --------------------------------------------
create table if not exists public.dpr_flags (
  id         bigserial primary key,
  created_at timestamptz not null default now(),
  who_hash   text not null,          -- md5 of the account id: counts a day's flags, names nobody
  major      text,
  catalog    text,
  label      text not null,
  status     text,
  units      jsonb,
  constraint dpr_flags_len check (length(label) <= 160 and length(coalesce(major,'')) <= 120 and length(coalesce(catalog,'')) <= 80 and length(coalesce(status,'')) <= 20)
);
-- no free text: an earlier draft of this file had a `note` column
alter table public.dpr_flags drop column if exists note;
alter table public.dpr_flags drop constraint if exists dpr_flags_len;
alter table public.dpr_flags add constraint dpr_flags_len check (length(label) <= 160 and length(coalesce(major,'')) <= 120 and length(coalesce(catalog,'')) <= 80);
alter table public.dpr_flags drop constraint if exists dpr_flags_status;
alter table public.dpr_flags add constraint dpr_flags_status check (status is null or status in ('satisfied', 'not', 'in_progress', 'unknown', 'row'));
alter table public.dpr_flags drop constraint if exists dpr_flags_units;
alter table public.dpr_flags add constraint dpr_flags_units check (units is null or (jsonb_typeof(units) = 'object' and pg_column_size(units) < 200));
alter table public.dpr_flags enable row level security;
drop policy if exists dpr_flags_insert on public.dpr_flags;
create policy dpr_flags_insert on public.dpr_flags for insert to authenticated with check (who_hash = md5(auth.uid()::text || ':' || current_date::text));
revoke all on public.dpr_flags from public, anon, authenticated;
grant insert on public.dpr_flags to authenticated;
grant usage on sequence public.dpr_flags_id_seq to authenticated;
create or replace function public.dpr_flags_limit() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'Sign in first.'; end if;
  -- one account's flags are counted one at a time (two at once can't both slip under the limit)
  perform pg_advisory_xact_lock(hashtext('dpr_flags:' || auth.uid()::text));
  new.who_hash := md5(auth.uid()::text || ':' || current_date::text);
  if (select count(*) from public.dpr_flags f where f.who_hash = new.who_hash) >= 30 then
    raise exception 'That’s enough flags for today — thank you.';
  end if;
  -- a flag never carries a grade or an id, whatever the client sent
  if not (public.dpr_text_ok(new.label) and public.dpr_text_ok(new.major) and public.dpr_text_ok(new.catalog) and public.dpr_text_ok(new.units::text))
     or new.label ~* 'grade\s*:' then
    raise exception 'A flag can’t carry an ID or a grade.';
  end if;
  return new;
end $$;
revoke all on function public.dpr_flags_limit() from public, anon, authenticated;
drop trigger if exists dpr_flags_limit on public.dpr_flags;
create trigger dpr_flags_limit before insert on public.dpr_flags for each row execute function public.dpr_flags_limit();

-- 4. "Send the link to my laptop" ------------------------------------------------------------------
create table if not exists public.planner_link_emails (
  id           bigserial primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  email        text,                 -- cleared once sent (or after 14 days)
  created_at   timestamptz not null default now(),
  requested_at timestamptz,
  request_id   bigint,
  sent_at      timestamptz,
  attempts     int not null default 0,
  next_try_at  timestamptz not null default now(),
  last_error   text
);
do $$ begin   -- a table made by an earlier run of this file gets the cascade too
  if not exists (select 1 from pg_constraint where conrelid = 'public.planner_link_emails'::regclass and contype = 'f') then
    alter table public.planner_link_emails add constraint planner_link_emails_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;
  end if;
end $$;
alter table public.planner_link_emails enable row level security;   -- no policies: functions only
revoke all on public.planner_link_emails from public, anon, authenticated;
revoke all on sequence public.planner_link_emails_id_seq from public, anon, authenticated;
create index if not exists planner_link_emails_todo_idx on public.planner_link_emails (id) where sent_at is null;

create or replace function public.request_planner_link()
returns text language plpgsql security definer set search_path = public as $$
declare addr text; n int;
begin
  if auth.uid() is null then raise exception 'Sign in first.'; end if;
  select u.email into addr from auth.users u where u.id = auth.uid();
  if addr is null or addr = '' then raise exception 'Your account has no email address.'; end if;
  perform pg_advisory_xact_lock(hashtext('planner_link:' || auth.uid()::text));   -- two taps at once count as two
  select count(*) into n from public.planner_link_emails e where e.user_id = auth.uid() and e.created_at > now() - interval '1 day';
  if n >= 3 then raise exception 'That link was already sent 3 times today — check your inbox and spam.'; end if;
  insert into public.planner_link_emails (user_id, email) values (auth.uid(), addr);
  -- the masked address, for the toast: "Sent to ta***@calpoly.edu"
  return left(split_part(addr, '@', 1), 2) || '***@' || split_part(addr, '@', 2);
end $$;
revoke all on function public.request_planner_link() from public, anon;
grant execute on function public.request_planner_link() to authenticated;

create or replace function public.planner_link_esc(t text) returns text language sql immutable as $$
  select replace(replace(replace(coalesce(t, ''), '&', '&amp;'), '<', '&lt;'), '>', '&gt;')
$$;
revoke all on function public.planner_link_esc(text) from public, anon, authenticated;
revoke all on function public.dpr_text_ok(text) from public, anon;
grant execute on function public.dpr_text_ok(text) to authenticated;

create or replace function public.planner_link_body() returns jsonb language sql immutable as $$
  select jsonb_build_object(
    'subject', 'Your Degree Progress Report → TermChamp',
    'html',
    '<div style="background:#F4F6FB;padding:24px 12px;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
    || '<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:18px;overflow:hidden">'
    || '<div style="background:#183178;color:#fff;padding:18px 24px;font-size:18px;font-weight:800">TermChamp</div>'
    || '<div style="padding:24px;color:#0F172A;font-size:16px;line-height:1.5">'
    || '<p style="margin:0 0 14px;font-size:20px;font-weight:800">Upload your Degree Progress Report</p>'
    || '<p style="margin:0 0 14px">You asked for this link on your phone. On your laptop:</p>'
    || '<ol style="margin:0 0 18px;padding-left:22px">'
    || '<li style="margin:0 0 8px"><b>Cal Poly Portal</b> → Student Center → Academic Progress</li>'
    || '<li style="margin:0 0 8px"><b>Degree Progress Report</b> → View PDF → Download</li>'
    || '<li style="margin:0 0 8px">Open <a href="https://termchamp.com/?tab=schedule" style="color:#2563EB;font-weight:800">termchamp.com</a> → Schedule → Planner and drag the PDF onto the page</li>'
    || '</ol>'
    || '<p style="margin:0;color:#5B6B80;font-size:14px">It’s read in your browser. Your student ID and grades are never saved.</p>'
    || '</div></div>'
    || '<p style="text-align:center;color:#8A96A8;font-size:12px;margin:16px 0 0">You asked for this email in the TermChamp app. If you didn’t, you can ignore it.</p>'
    || '</div>')
$$;
revoke all on function public.planner_link_body() from public, anon, authenticated;

create or replace function public.send_planner_links()
returns int language plpgsql security definer set search_path = public, extensions as $$
declare r record; k text; n int := 0; resp record; b jsonb;
begin
  -- 1. answers to earlier requests
  for r in select e.* from public.planner_link_emails e where e.request_id is not null and e.sent_at is null loop
    begin
      select status_code, content, error_msg into resp from net._http_response where id = r.request_id;
    exception when others then continue;
    end;
    if resp is null or resp.status_code is null then
      if r.requested_at < now() - interval '15 minutes' then update public.planner_link_emails set request_id = null, attempts = attempts + 1, last_error = 'no answer', next_try_at = now() + interval '5 minutes' where id = r.id; end if;
      continue;
    end if;
    if resp.status_code between 200 and 299 then
      update public.planner_link_emails set sent_at = now(), request_id = null, last_error = null, email = null where id = r.id;
    else
      update public.planner_link_emails set request_id = null, attempts = attempts + 1,
             last_error = left(coalesce(resp.status_code::text, '') || ' ' || coalesce(resp.error_msg, resp.content, ''), 500),
             next_try_at = now() + interval '5 minutes' * power(2, least(attempts, 6))
       where id = r.id;
    end if;
  end loop;
  -- 2. tidy: an address never waits more than 14 days; rows go after 90
  update public.planner_link_emails set email = null, last_error = coalesce(last_error, 'expired') where email is not null and sent_at is null and created_at < now() - interval '14 days';
  delete from public.planner_link_emails where created_at < now() - interval '90 days';
  delete from public.dpr_flags where created_at < now() - interval '180 days';
  -- 3. send what's waiting (no key: nothing is sent, nothing is lost)
  begin
    select decrypted_secret into k from vault.decrypted_secrets where name = 'resend_api_key' order by created_at desc limit 1;
  exception when others then k := null;
  end;
  if k is null or k = '' then return 0; end if;
  b := public.planner_link_body();
  for r in select e.* from public.planner_link_emails e
            where e.sent_at is null and e.request_id is null and e.email is not null and e.attempts < 8 and e.next_try_at <= now()
            order by e.id limit 20 for update skip locked loop
    begin
      update public.planner_link_emails set requested_at = now(), request_id = net.http_post(
          url := 'https://api.resend.com/emails',
          body := jsonb_build_object('from', 'TermChamp <noreply@termchamp.com>', 'to', jsonb_build_array(r.email),
                                     'subject', b->>'subject', 'html', b->>'html'),
          headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Content-Type', 'application/json',
                                        'Idempotency-Key', 'termchamp-planner-link-' || r.id),
          timeout_milliseconds := 10000)
       where id = r.id;
      n := n + 1;
    exception when others then
      update public.planner_link_emails set attempts = attempts + 1, last_error = left(sqlerrm, 500),
             next_try_at = now() + interval '5 minutes' * power(2, least(attempts, 6)) where id = r.id;
    end;
  end loop;
  return n;
end $$;
revoke all on function public.send_planner_links() from public, anon, authenticated;

do $$ begin
  begin
    perform cron.unschedule('termchamp-planner-links');
  exception when others then null;
  end;
  begin
    perform cron.schedule('termchamp-planner-links', '*/5 * * * *', 'select public.send_planner_links()');
  exception when others then raise notice 'pg_cron is not available here: schedule send_planner_links() by hand (%).', sqlerrm;
  end;
end $$;

-- 5. Self-checks -----------------------------------------------------------------------------------
do $$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'degree_audit') <> 4 then raise exception 'degree_audit: expected 4 owner policies'; end if;
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'planner_prefs') <> 4 then raise exception 'planner_prefs: expected 4 owner policies'; end if;
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'dpr_flags') <> 1 then raise exception 'dpr_flags: expected 1 insert policy'; end if;
  if has_table_privilege('anon', 'public.degree_audit', 'select') or has_table_privilege('anon', 'public.planner_prefs', 'select') then raise exception 'anon can read the planner tables'; end if;
  if has_table_privilege('authenticated', 'public.dpr_flags', 'select') then raise exception 'students can read flags'; end if;
  if has_table_privilege('authenticated', 'public.planner_link_emails', 'select') or has_table_privilege('authenticated', 'public.planner_link_emails', 'insert') then raise exception 'students can touch the email queue'; end if;
  if not has_function_privilege('authenticated', 'public.request_planner_link()', 'execute') then raise exception 'students can’t ask for the link'; end if;
  if has_function_privilege('authenticated', 'public.send_planner_links()', 'execute') or has_function_privilege('anon', 'public.request_planner_link()', 'execute') then raise exception 'the sender is exposed'; end if;
  if not exists (select 1 from pg_constraint where conname = 'degree_audit_no_grades') then raise exception 'the no-grades check is missing'; end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'dpr_flags' and column_name = 'note') then raise exception 'dpr_flags still has a note column'; end if;
  if public.dpr_text_ok('EMPLID 1234567') or public.dpr_text_ok('BUS 214 Financial Accounting A- 4.00') or not public.dpr_text_ok('BUS 4401/4411') then raise exception 'the ID/grade text check is wrong'; end if;
  if not exists (select 1 from vault.decrypted_secrets where name = 'resend_api_key') then
    raise notice 'No resend_api_key in the Vault yet: the laptop-link emails will wait until it is added (RUN 9 explains how).';
  end if;
exception when undefined_table then
  raise notice 'vault is not available here (local test).';
end $$;

commit;
