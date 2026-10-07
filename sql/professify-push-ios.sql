-- ================================================================================================
-- PUSH FOR THE IPHONE APP — 6 October 2026
-- ================================================================================================
-- professify-push.sql (live) queues a row in push_outbox when a watched section opens up, and
-- push-send delivers it as Web Push to push_subscriptions. The App Store app cannot use Web Push:
-- iOS gives a native app an APNs DEVICE TOKEN instead of an endpoint + keys. This adds the table
-- that holds those tokens and the two functions the app calls. push-send (updated the same day)
-- reads both tables and sends each row to every device the student has, of either kind.
--
-- Nothing about WHEN a notification is queued changes. Quiet hours, the per-kind prefs and the
-- dedupe key all live upstream in push_enqueue and are untouched.
--
-- WHY FUNCTIONS AND NOT A PLAIN INSERT POLICY. An APNs token belongs to a phone, not a person.
-- When a student signs out and a friend signs in on the same phone, the same token must move to
-- the new account — otherwise the first student keeps getting alerts on a phone they handed over.
-- Moving it means touching a row the caller does not own, which RLS rightly refuses; a SECURITY
-- DEFINER function that can only ever assign the token to auth.uid() is the narrow way to do it.
--
-- Safe to re-run. Adds one table and two functions; changes nothing that exists.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 1. The devices
-- ------------------------------------------------------------------------------------------------
create table if not exists public.push_devices (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,   -- account deletion clears it
  token       text not null unique,          -- APNs device token, hex
  platform    text not null default 'ios',
  apns_env    text,                          -- 'production' | 'sandbox', learned by push-send on first send
  created_at  timestamptz not null default now(),
  last_ok_at  timestamptz,
  fail_count  int not null default 0,
  constraint push_devices_platform check (platform in ('ios')),
  constraint push_devices_env check (apns_env is null or apns_env in ('production','sandbox')),
  constraint push_devices_token_shape check (token ~ '^[0-9a-f]{32,200}$')
);
create index if not exists push_devices_user_idx on public.push_devices(user_id);

alter table public.push_devices enable row level security;
do $$
begin
  -- drop by SHAPE, not by name (see professify-push.sql for why)
  execute (
    select coalesce(string_agg(format('drop policy %I on public.push_devices;', polname), ' '), '')
      from pg_policy where polrelid = 'public.push_devices'::regclass);
end $$;
-- A student may see and remove their own devices. Nothing writes here except the two functions
-- below (as the student) and push-send (as the service role).
create policy push_devices_own_select on public.push_devices
  for select to authenticated using (user_id = auth.uid());
create policy push_devices_own_delete on public.push_devices
  for delete to authenticated using (user_id = auth.uid());
revoke all on public.push_devices from anon;
revoke insert, update on public.push_devices from authenticated;


-- ------------------------------------------------------------------------------------------------
-- 2. register_push_device(token) — this phone now belongs to the caller
-- ------------------------------------------------------------------------------------------------
create or replace function public.register_push_device(p_token text, p_platform text default 'ios')
returns boolean
language plpgsql
security definer
set search_path = public
as $fn$
declare
  me  uuid := auth.uid();
  tok text := lower(regexp_replace(coalesce(p_token,''), '[^0-9A-Fa-f]', '', 'g'));
begin
  if me is null then return false; end if;
  if tok !~ '^[0-9a-f]{32,200}$' then return false; end if;
  if coalesce(p_platform,'ios') <> 'ios' then return false; end if;

  insert into public.push_devices(user_id, token, platform)
  values (me, tok, 'ios')
  on conflict (token) do update
     set user_id    = excluded.user_id,
         -- a token changing hands starts clean; one that stays put keeps its learned env
         apns_env   = case when push_devices.user_id = excluded.user_id then push_devices.apns_env end,
         fail_count = 0;

  -- a phone can't hold more than a handful of live tokens for one person; keep the newest 10
  delete from public.push_devices d
   where d.user_id = me
     and d.id not in (select id from public.push_devices where user_id = me order by created_at desc, id desc limit 10);
  return true;
end;
$fn$;


-- ------------------------------------------------------------------------------------------------
-- 3. unregister_push_device(token) — called on sign-out
-- ------------------------------------------------------------------------------------------------
create or replace function public.unregister_push_device(p_token text)
returns boolean
language plpgsql
security definer
set search_path = public
as $fn$
declare
  tok text := lower(regexp_replace(coalesce(p_token,''), '[^0-9A-Fa-f]', '', 'g'));
begin
  if auth.uid() is null or tok = '' then return false; end if;
  delete from public.push_devices where token = tok and user_id = auth.uid();
  return found;
end;
$fn$;

revoke all on function public.register_push_device(text,text) from public, anon;
revoke all on function public.unregister_push_device(text) from public, anon;
grant execute on function public.register_push_device(text,text) to authenticated;
grant execute on function public.unregister_push_device(text) to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 4. Self-check (read-only). Every row should say ok.
-- ------------------------------------------------------------------------------------------------
select 'push_devices RLS on' as check,
       case when relrowsecurity then 'ok' else 'FAIL' end as result
  from pg_class where oid = 'public.push_devices'::regclass
union all
select 'policies (expect 2)', count(*)::text
  from pg_policy where polrelid = 'public.push_devices'::regclass
union all
select 'anon cannot run register_push_device',
       case when has_function_privilege('anon','public.register_push_device(text,text)','execute') then 'FAIL' else 'ok' end
union all
select 'authenticated can run register_push_device',
       case when has_function_privilege('authenticated','public.register_push_device(text,text)','execute') then 'ok' else 'FAIL' end
union all
select 'authenticated cannot insert directly',
       case when has_table_privilege('authenticated','public.push_devices','insert') then 'FAIL' else 'ok' end;
