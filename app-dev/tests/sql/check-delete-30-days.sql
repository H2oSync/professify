-- Checks sql/professify-delete-account-30-days.sql on Postgres 16 against a stand-in of the live
-- shape (2026-10-04): auth.uid() exactly as Supabase defines it, the people functions with their live
-- signatures and anon/authenticated grants, permissive read policies like the live ones, and a
-- delete_my_account() that de-authors reviews, nulls reports.reporter, then deletes the profile and
-- the sign-in. pg_cron isn't installed here: the runner swaps "create extension" for a stub cron
-- schema (cron is checked on the live run by the file's own self-check).
-- Run: ./run-check-delete-30-days.sh   Every block sets its own identity.
\set ON_ERROR_STOP 1

-- ---------- stand-in ----------
drop schema if exists auth cascade; drop schema if exists storage cascade; drop schema if exists cron cascade;
drop schema if exists public cascade; create schema public; create schema auth; create schema storage; create schema cron;
do $$ begin
  if not exists (select 1 from pg_roles where rolname='anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname='authenticated') then create role authenticated nologin; end if;
end $$;
grant usage on schema public, auth to anon, authenticated;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$
  select coalesce(nullif(current_setting('request.jwt.claim.sub', true), ''),
                  (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'))::uuid $$;
create table storage.objects (id bigserial primary key, bucket_id text, name text);
-- as live: SQL deletes are refused unless storage.allow_delete_query is 'true' (statement-level)
create function storage.protect_delete() returns trigger language plpgsql as $$ begin
  if coalesce(current_setting('storage.allow_delete_query', true), 'false') <> 'true' then
    raise exception 'Direct deletion from storage tables is not allowed. Use the Storage API instead.' using errcode = '42501'; end if;
  return null; end $$;
create trigger protect_objects_delete before delete on storage.objects for each statement execute function storage.protect_delete();
create table cron.job (jobname text primary key, schedule text, command text, active boolean default true);
create table cron.job_run_details (end_time timestamptz);
create function cron.schedule(n text, s text, c text) returns bigint language sql as $$
  insert into cron.job values (n, s, c, true) on conflict (jobname) do update set schedule = excluded.schedule, command = excluded.command returning 1::bigint $$;

create table public.profiles (id uuid primary key references auth.users(id), display_name text, school text default 'calpoly');
create table public.friend_requests (id bigserial primary key, from_user uuid references auth.users(id) on delete cascade, to_user uuid references auth.users(id) on delete cascade, status text);
create table public.my_sections (user_id uuid references auth.users(id) on delete cascade, code text, status text);
create table public.saved_classes (user_id uuid references auth.users(id) on delete cascade, code text);
create table public.class_history (user_id uuid references auth.users(id) on delete cascade, code text);
create table public.plans (id bigserial primary key, user_id uuid references auth.users(id) on delete cascade, slot text, shared boolean default true);
create table public.watch_sections (user_id uuid references auth.users(id) on delete cascade, crn text);
create table public.class_waivers (user_id uuid references auth.users(id) on delete cascade, code text);
create table public.conversation_members (conversation_id int, user_id uuid references auth.users(id) on delete cascade);
create table public.group_members (group_id int, user_id uuid references auth.users(id) on delete cascade);
create table public.reviews (id bigserial primary key, user_id uuid references auth.users(id) on delete cascade, note text);
create table public.review_helpful (review_id bigint references public.reviews(id) on delete cascade, voter_id uuid);
create table public.reports (id bigserial primary key, reporter uuid not null references auth.users(id) on delete set null, reason text);
do $$ declare t text; begin
  foreach t in array array['profiles','friend_requests','my_sections','saved_classes','class_history','plans','watch_sections','class_waivers','conversation_members','group_members','reviews'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('grant select, insert, update, delete on public.%I to anon, authenticated', t);
    execute format('create policy "live-like write" on public.%I for insert to authenticated with check (true)', t);
    if t in ('my_sections', 'plans') then
      -- as live: a friend's sections and plans are read through a friend_requests subquery
      execute format('create policy "live-like read" on public.%I for select to anon, authenticated using (user_id = auth.uid() or exists (select 1 from public.friend_requests rq where rq.status = ''accepted'' and ((rq.from_user = auth.uid() and rq.to_user = %I.user_id) or (rq.to_user = auth.uid() and rq.from_user = %I.user_id))))', t, t, t);
    else
      execute format('create policy "live-like read" on public.%I for select to anon, authenticated using (auth.uid() is not null)', t);
    end if;
  end loop;
  -- as live: plans has exactly two policies (professify-plans.sql checks that)
  create policy "plans_own" on public.plans for all to authenticated using (user_id = auth.uid());
end $$;
grant usage, select on all sequences in schema public to authenticated;

create function public.delete_my_account() returns void language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'not signed in'; end if;
  update public.reviews set user_id = null where user_id = me;
  update public.reports set reporter = null where reporter = me;
  delete from public.profiles where id = me;
  delete from auth.users where id = me;
end $$;
revoke all on function public.delete_my_account() from public, anon; grant execute on function public.delete_my_account() to authenticated;

-- the people functions, with their live names, arguments, results, volatility and callers
create function public.search_people(q text) returns table(id uuid, display_name text, instagram_handle text) language sql volatile security definer set search_path = public as $$ select id, display_name, null::text from public.profiles where display_name ilike '%'||q||'%' $$;
create function public.find_people(q text) returns table(id uuid, display_name text, username text) language sql stable security definer set search_path = public as $$ select id, display_name, null::text from public.profiles where display_name ilike '%'||q||'%' $$;
create function public.find_profile_by_handle(handle text) returns table(id uuid, display_name text, instagram_handle text) language sql volatile security definer set search_path = public as $$ select id, display_name, handle from public.profiles where display_name = handle $$;
create function public.suggest_friends(p_limit integer default 6) returns table(id uuid, display_name text) language sql stable security definer set search_path = public as $$ select id, display_name from public.profiles order by display_name limit p_limit $$;
create function public.suggest_friends_unscoped(p_limit integer default 6) returns table(id uuid, display_name text) language sql volatile security definer set search_path = public as $$ select id, display_name from public.profiles limit p_limit $$;
create function public.suggest_classmates() returns table(id uuid, display_name text, overlap bigint) language sql stable security definer set search_path = public as $$ select id, display_name, 1::bigint from public.profiles $$;
create function public.suggest_classmates_unscoped() returns table(id uuid, display_name text, overlap bigint) language sql volatile security definer set search_path = public as $$ select id, display_name, 1::bigint from public.profiles $$;
create function public.suggest_classmates_v2() returns table(id uuid, display_name text, username text, avatar_url text, overlap integer, codes text[]) language sql stable security definer set search_path = public as $$ select id, display_name, null, null, 1, array['BUS 1']::text[] from public.profiles $$;
create function public.friends_of(p_user uuid) returns table(id uuid, display_name text, username text, avatar_url text, mutual boolean) language sql stable security definer set search_path = public as $$
  select p.id, p.display_name, null, null, false from public.profiles p where p.id <> p_user $$;
create function public.get_inviter(ref uuid) returns table(display_name text) language sql stable security definer set search_path = public as $$ select display_name from public.profiles where id = ref $$;
create function public.friends_reviewed(p_professor_key text) returns table(id uuid, display_name text, username text, avatar_url text, score numeric, course text, created_at timestamptz) language sql stable security definer set search_path = public as $$ select id, display_name, null, null, 4.0, 'BUS 1', now() from public.profiles $$;
create function public.professor_suggested_by(p_professor_key text) returns table(id uuid, display_name text, username text, avatar_url text, note text, created_at timestamptz) language sql stable security definer set search_path = public as $$ select id, display_name, null, null, 'x', now() from public.profiles $$;
create function public.friend_emails(p_ids uuid[] default null::uuid[]) returns table(id uuid, edu_email text) language sql stable security definer set search_path = public as $$ select id, display_name||'@calpoly.edu' from public.profiles where id = any(p_ids) $$;
do $$ declare f text; begin
  foreach f in array array['search_people(text)','find_people(text)','find_profile_by_handle(text)','suggest_friends(integer)','suggest_friends_unscoped(integer)','suggest_classmates()','suggest_classmates_unscoped()','suggest_classmates_v2()','friends_of(uuid)','get_inviter(uuid)','friend_emails(uuid[])','friends_reviewed(text)','professor_suggested_by(text)'] loop
    execute 'revoke all on function public.' || f || ' from public, anon';
    execute 'grant execute on function public.' || f || ' to authenticated';
  end loop;
  -- live 2026-10-04: anon could call exactly these three
  grant execute on function public.search_people(text), public.find_profile_by_handle(text), public.get_inviter(uuid) to anon;
end $$;

-- Ann (A) will delete; Ben (B) is her friend; Cam (C) has filed a report and will be purged
insert into auth.users values ('aaaaaaaa-0000-0000-0000-000000000001'), ('bbbbbbbb-0000-0000-0000-000000000002'), ('cccccccc-0000-0000-0000-000000000003');
insert into public.profiles (id, display_name) values ('aaaaaaaa-0000-0000-0000-000000000001', 'Ann'), ('bbbbbbbb-0000-0000-0000-000000000002', 'Ben'), ('cccccccc-0000-0000-0000-000000000003', 'Cam');
insert into public.friend_requests (from_user, to_user, status) values ('aaaaaaaa-0000-0000-0000-000000000001', 'bbbbbbbb-0000-0000-0000-000000000002', 'accepted');
insert into public.my_sections values ('aaaaaaaa-0000-0000-0000-000000000001', 'BUS 4442', 'enrolled');
insert into public.saved_classes values ('aaaaaaaa-0000-0000-0000-000000000001', 'BUS 4442');
insert into public.class_history values ('aaaaaaaa-0000-0000-0000-000000000001', 'BUS 2001');
insert into public.plans (user_id, slot) values ('aaaaaaaa-0000-0000-0000-000000000001', 'A');
insert into public.watch_sections values ('aaaaaaaa-0000-0000-0000-000000000001', '1234');
insert into public.class_waivers values ('aaaaaaaa-0000-0000-0000-000000000001', 'MATH 1');
insert into public.reviews (user_id, note) values ('aaaaaaaa-0000-0000-0000-000000000001', 'ann review'), ('cccccccc-0000-0000-0000-000000000003', 'cam review');
insert into public.review_helpful select id, 'bbbbbbbb-0000-0000-0000-000000000002' from public.reviews where note = 'ann review';
insert into public.reports (reporter, reason) values ('cccccccc-0000-0000-0000-000000000003', 'spam');
insert into storage.objects (bucket_id, name) values ('avatars', 'aaaaaaaa-0000-0000-0000-000000000001/avatar.jpg'), ('avatars', 'cccccccc-0000-0000-0000-000000000003/avatar.jpg'), ('avatars', 'bbbbbbbb-0000-0000-0000-000000000002/avatar.jpg');

-- ---------- the migration, twice ----------
\i :mig
\i :mig

-- ---------- checks ----------
-- 1. students can't skip the wait, run the purge, or read the table; anon can't ask
do $$ begin
  if has_function_privilege('authenticated', 'public.delete_my_account_v2(boolean)', 'execute') then raise exception 'FAIL v2 callable'; end if;
  if has_function_privilege('authenticated', 'public.purge_due_account_deletions()', 'execute') then raise exception 'FAIL purge callable'; end if;
  if has_table_privilege('authenticated', 'public.account_deletions', 'select') then raise exception 'FAIL table readable'; end if;
  if has_function_privilege('anon', 'public.request_account_deletion(boolean)', 'execute') then raise exception 'FAIL anon can ask'; end if;
  -- the wrappers kept exactly the original callers; the unfiltered bases have none
  if not has_function_privilege('anon', 'public.get_inviter(uuid)', 'execute') then raise exception 'FAIL invite page lost get_inviter'; end if;
  if has_function_privilege('anon', 'public.find_people(text)', 'execute') then raise exception 'FAIL anon gained find_people'; end if;
  if not has_function_privilege('authenticated', 'public.suggest_classmates_v2()', 'execute') then raise exception 'FAIL students lost suggest_classmates_v2'; end if;
  if has_function_privilege('authenticated', 'public.search_people__incl_pending(text)', 'execute') then raise exception 'FAIL unfiltered search callable'; end if;
end $$;

-- 2. Ann asks: a date 30 days out; she still sees her own things; Ben sees nothing of her
do $$ declare t timestamptz; n int; begin
  perform set_config('request.jwt.claims', '{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated"}', true);
  set local role authenticated;
  t := public.request_account_deletion(true);
  if t < now() + interval '29 days 23 hours' or t > now() + interval '30 days 1 hour' then raise exception 'FAIL purge date %', t; end if;
  if (select count(*) from public.my_account_deletion()) <> 1 then raise exception 'FAIL she cannot see her own pending deletion'; end if;
  if (select count(*) from public.my_sections) <> 1 or (select count(*) from public.profiles where display_name = 'Ann') <> 1 then raise exception 'FAIL she lost sight of her own data'; end if;
  reset role;
end $$;
do $$ declare n int; begin
  perform set_config('request.jwt.claims', '{"sub":"bbbbbbbb-0000-0000-0000-000000000002","role":"authenticated"}', true);
  set local role authenticated;
  if exists (select 1 from public.profiles where display_name = 'Ann') then raise exception 'FAIL Ben still sees her profile'; end if;
  if exists (select 1 from public.friend_requests) then raise exception 'FAIL Ben still sees the friendship'; end if;
  foreach n in array array[(select count(*) from public.my_sections), (select count(*) from public.saved_classes), (select count(*) from public.class_history),
                           (select count(*) from public.plans), (select count(*) from public.watch_sections), (select count(*) from public.class_waivers)]::int[] loop
    if n <> 0 then raise exception 'FAIL Ben still sees some of her classes or plans'; end if;
  end loop;
  if exists (select 1 from public.search_people('Ann')) or exists (select 1 from public.find_people('Ann')) or exists (select 1 from public.suggest_friends(10) where display_name = 'Ann')
     or exists (select 1 from public.suggest_classmates_v2() where display_name = 'Ann') or exists (select 1 from public.friends_of('cccccccc-0000-0000-0000-000000000003') where display_name = 'Ann')
     or exists (select 1 from public.friends_of('aaaaaaaa-0000-0000-0000-000000000001')) or exists (select 1 from public.friend_emails(array['aaaaaaaa-0000-0000-0000-000000000001'::uuid]))
     or exists (select 1 from public.suggest_classmates() where display_name = 'Ann') or exists (select 1 from public.suggest_classmates_unscoped() where display_name = 'Ann')
     or exists (select 1 from public.suggest_friends_unscoped(10) where display_name = 'Ann') or exists (select 1 from public.find_profile_by_handle('Ann'))
     or exists (select 1 from public.friends_reviewed('p') where display_name = 'Ann') or exists (select 1 from public.professor_suggested_by('p') where display_name = 'Ann') then
    raise exception 'FAIL a people function still hands her out';
  end if;
  if not exists (select 1 from public.search_people('Cam')) then raise exception 'FAIL search lost everyone else'; end if;
  begin insert into public.friend_requests (from_user, to_user, status) values ('bbbbbbbb-0000-0000-0000-000000000002', 'aaaaaaaa-0000-0000-0000-000000000001', 'pending');
        raise exception 'FAIL a request to her went in';
  exception when insufficient_privilege then null; end;
  begin insert into public.conversation_members values (1, 'aaaaaaaa-0000-0000-0000-000000000001'); raise exception 'FAIL she was added to a chat';
  exception when insufficient_privilege then null; end;
  begin insert into public.group_members values (1, 'aaaaaaaa-0000-0000-0000-000000000001'); raise exception 'FAIL she was added to a group';
  exception when insufficient_privilege then null; end;
  reset role;
end $$;
do $$ begin
  set local role anon;
  if exists (select 1 from public.get_inviter('aaaaaaaa-0000-0000-0000-000000000001')) then raise exception 'FAIL invite page still names her'; end if;
  reset role;
end $$;

-- 3. The purge leaves her alone before 30 days
select public.purge_due_account_deletions();
do $$ begin if not exists (select 1 from auth.users where id = 'aaaaaaaa-0000-0000-0000-000000000001') then raise exception 'FAIL purged early'; end if; end $$;

-- 4. She recovers: everything is back for Ben
do $$ begin
  perform set_config('request.jwt.claims', '{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated"}', true);
  set local role authenticated;
  if not public.cancel_account_deletion() then raise exception 'FAIL cancel said nothing to cancel'; end if;
  reset role;
  perform set_config('request.jwt.claims', '{"sub":"bbbbbbbb-0000-0000-0000-000000000002","role":"authenticated"}', true);
  set local role authenticated;
  if not exists (select 1 from public.profiles where display_name = 'Ann') or not exists (select 1 from public.friend_requests)
     or not exists (select 1 from public.my_sections) or not exists (select 1 from public.search_people('Ann')) then raise exception 'FAIL recovery did not bring her back'; end if;
  reset role;
end $$;

-- 5. She asks again (reviews: delete) and Cam asks (keep); both come due; the purge deletes both
do $$ begin
  perform set_config('request.jwt.claims', '{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated"}', true);
  set local role authenticated; perform public.request_account_deletion(true); reset role;
  perform set_config('request.jwt.claims', '{"sub":"cccccccc-0000-0000-0000-000000000003","role":"authenticated"}', true);
  set local role authenticated; perform public.request_account_deletion(false); reset role;
  perform set_config('request.jwt.claims', '', true);
end $$;
update public.account_deletions set purge_after = now() - interval '1 minute';
do $$ declare n int; begin
  n := public.purge_due_account_deletions();
  if n <> 2 then raise exception 'FAIL purged % accounts, expected 2', n; end if;
  if exists (select 1 from auth.users where id in ('aaaaaaaa-0000-0000-0000-000000000001', 'cccccccc-0000-0000-0000-000000000003')) then raise exception 'FAIL a sign-in survived'; end if;
  if exists (select 1 from public.reviews where note = 'ann review') then raise exception 'FAIL her reviews (delete) survived'; end if;
  if not exists (select 1 from public.reviews where note = 'cam review' and user_id is null) then raise exception 'FAIL Cam''s review (keep) is not kept de-authored'; end if;
  if not exists (select 1 from public.reports where reason = 'spam' and reporter is null) then raise exception 'FAIL Cam''s report did not stay, de-authored'; end if;
  if exists (select 1 from storage.objects where name like 'aaaaaaaa%' or name like 'cccccccc%') then raise exception 'FAIL a photo survived'; end if;
  if not exists (select 1 from storage.objects where name like 'bbbbbbbb%') then raise exception 'FAIL Ben''s photo was touched'; end if;
  if exists (select 1 from public.account_deletions) then raise exception 'FAIL pending rows left behind'; end if;
  if coalesce(current_setting('request.jwt.claims', true), '') <> '' or coalesce(current_setting('request.jwt.claim.sub', true), '') <> '' then raise exception 'FAIL the purge left an identity set'; end if;
  if coalesce(current_setting('storage.allow_delete_query', true), 'false') = 'true' then raise exception 'FAIL the purge left storage deletes switched on'; end if;
end $$;

-- 6. One account that fails is kept with its reason, and doesn't stop the next
insert into auth.users values ('dddddddd-0000-0000-0000-000000000004'), ('eeeeeeee-0000-0000-0000-000000000005');
insert into public.account_deletions (user_id, purge_after) values ('dddddddd-0000-0000-0000-000000000004', now() - interval '2 minutes'), ('eeeeeeee-0000-0000-0000-000000000005', now() - interval '1 minute');
insert into storage.objects (bucket_id, name) values ('avatars', 'eeeeeeee-0000-0000-0000-000000000005/avatar.jpg');
create or replace function public.delete_my_account() returns void language plpgsql security definer set search_path = public as $$
begin if auth.uid() = 'dddddddd-0000-0000-0000-000000000004' then raise exception 'boom'; end if; delete from auth.users where id = auth.uid(); end $$;
-- and Storage refuses every SQL delete (as if Supabase changed the rule): the account still goes
create or replace function storage.protect_delete() returns trigger language plpgsql as $$ begin raise exception 'no deletes'; end $$;
do $$ declare n int; begin
  n := public.purge_due_account_deletions();
  if n <> 1 then raise exception 'FAIL expected 1 purged past a failure, got %', n; end if;
  if not exists (select 1 from public.account_deletions where user_id = 'dddddddd-0000-0000-0000-000000000004' and attempts = 1 and last_error = 'boom') then raise exception 'FAIL the failure was not recorded'; end if;
  if exists (select 1 from auth.users where id = 'eeeeeeee-0000-0000-0000-000000000005') then raise exception 'FAIL the next account was blocked by the failure'; end if;
  if not exists (select 1 from auth.users where id = 'dddddddd-0000-0000-0000-000000000004') then raise exception 'FAIL the failed account was half-deleted'; end if;
end $$;

-- 7. the daily job is there
do $$ begin if not exists (select 1 from cron.job where jobname = 'termchamp-purge-deleted-accounts' and command like '%purge_due_account_deletions%') then raise exception 'FAIL no daily job'; end if; end $$;

select 'check-delete-30-days: all 7 blocks passed' as result;
