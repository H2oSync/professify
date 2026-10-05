-- TermChamp: delete your account, with 30 days to recover it (2026-10-04)
--
-- Tate (2026-10-04): "only the one way — delete account and you have 30 days to recover".
-- Apple 5.1.1(v) allows deletion that takes time, as long as people are told how long.
--
-- What happens:
--   1. Delete account → request_account_deletion(p_delete_reviews). The account is hidden from
--      everyone else AT ONCE (profile, friend lists, search, suggestions, classes, plans, the
--      planner record) and the app signs you out. Nothing is deleted yet.
--   2. Sign in within 30 days → the app asks "Recover your account?" → cancel_account_deletion()
--      and everything is back exactly as it was.
--   3. After 30 days a daily job (pg_cron) runs purge_due_account_deletions(): the real deletion,
--      through delete_my_account_v2 → delete_my_account(), plus your profile photo.
--   "Keep my reviews up anonymously" (on by default) is decided at step 1 and applied at step 3.
--
-- BEFORE RUNNING: turn on pg_cron — Supabase dashboard → Integrations → Cron → Enable. This file
-- also tries "create extension pg_cron", and stops with nothing applied if the job can't be made:
-- an account promised deletion after 30 days must actually be deleted.
--
-- Also in this file (supersedes professify-delete-account-v2.sql, which was never run):
--   · reports.reporter NOT NULL is relaxed. Live bug found 2026-10-04: delete_my_account() sets it
--     to null, so anyone who ever filed a report could not delete their account (desktop too).
--   · delete_my_account_v2(p_delete_reviews), now for the purge job only (not callable by students).
--
-- People functions are SECURITY DEFINER (they bypass row security), so the thirteen that hand out
-- people are wrapped: the original is renamed <name>__incl_pending, students lose direct access
-- to it, and <name> becomes a filter over it. If you ever re-create one of these functions from an
-- older file, edit <name>__incl_pending instead — re-running THIS file then re-checks the wrap and
-- stops if the two have drifted.
--
-- Not hidden while pending: messages already sent (they show without a name, as "Someone") and
-- reviews (anonymous anyway; deleted at day 30 if the switch was off).
-- WATCH LIST (2026-10-04): get the newest list of people-returning definer functions before adding
-- one; a new one that isn't wrapped shows pending accounts.
-- Since website build 2026-10-04 19:15 the website asks for a deletion too, and shows Recover on
-- sign-in; professify-lock-immediate-delete.sql then takes delete_my_account() away from students.
-- professify-deletion-emails.sql re-creates the purge below to queue the "deleted" email.
-- Admin check for stuck purges:
--   select user_id, purge_after, attempts, last_error from account_deletions where attempts > 0 or purge_after < now() - interval '2 days';
-- ADDITIVE except the reporter column (a relaxation). One transaction; self-checks raise. Safe to
-- run twice.

begin;

-- 0. The reporter fix -------------------------------------------------------------------------
do $$ begin
  if to_regclass('public.reports') is not null and exists (
       select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'reports' and column_name = 'reporter' and is_nullable = 'NO') then
    alter table public.reports alter column reporter drop not null;
  end if;
end $$;

-- 1. Pending deletions ---------------------------------------------------------------------------
create table if not exists public.account_deletions (
  user_id        uuid primary key references auth.users(id) on delete cascade,
  requested_at   timestamptz not null default now(),
  purge_after    timestamptz not null,
  delete_reviews boolean not null default false,
  attempts       int not null default 0,
  last_error     text
);
alter table public.account_deletions enable row level security;   -- no policies: functions only
revoke all on public.account_deletions from public, anon, authenticated;
create index if not exists account_deletions_due_idx on public.account_deletions (purge_after);

create or replace function public.is_pending_deletion(p_user uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.account_deletions d where d.user_id = p_user)
$$;
revoke all on function public.is_pending_deletion(uuid) from public;
grant execute on function public.is_pending_deletion(uuid) to anon, authenticated;   -- row-security checks run as the reader

-- 2. Ask, recover, look ------------------------------------------------------------------------------
create or replace function public.request_account_deletion(p_delete_reviews boolean default false)
returns timestamptz language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid(); t timestamptz;
begin
  if me is null then raise exception 'not signed in'; end if;
  insert into public.account_deletions (user_id, purge_after, delete_reviews)
  values (me, now() + interval '30 days', coalesce(p_delete_reviews, false))
  on conflict (user_id) do update set delete_reviews = excluded.delete_reviews   -- the date never moves
  returning purge_after into t;
  return t;
end $$;

create or replace function public.cancel_account_deletion()
returns boolean language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid(); n int;
begin
  if me is null then raise exception 'not signed in'; end if;
  delete from public.account_deletions where user_id = me;
  get diagnostics n = row_count;
  return n > 0;
end $$;

create or replace function public.my_account_deletion()
returns table (purge_after timestamptz, delete_reviews boolean)
language sql stable security definer set search_path = public as $$
  select d.purge_after, d.delete_reviews from public.account_deletions d where d.user_id = auth.uid()
$$;

revoke all on function public.request_account_deletion(boolean) from public, anon;
revoke all on function public.cancel_account_deletion() from public, anon;
revoke all on function public.my_account_deletion() from public, anon;
grant execute on function public.request_account_deletion(boolean) to authenticated;
grant execute on function public.cancel_account_deletion() to authenticated;
grant execute on function public.my_account_deletion() to authenticated;

-- 3. The real deletion (purge job only) ------------------------------------------------------------
create or replace function public.delete_my_account_v2(p_delete_reviews boolean default false)
returns void language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'not signed in'; end if;
  if p_delete_reviews and to_regclass('public.reviews') is not null then
    delete from public.reviews where user_id = me;
    if exists (select 1 from public.reviews where user_id = me) then
      raise exception 'your reviews could not be deleted';
    end if;
  end if;
  perform public.delete_my_account();   -- unchanged: de-authors reviews left, deletes the rest and the sign-in
end $$;
revoke all on function public.delete_my_account_v2(boolean) from public, anon, authenticated;

create or replace function public.purge_due_account_deletions()
returns int language plpgsql security definer set search_path = public as $$
declare r record; n int := 0;
begin
  for r in select * from public.account_deletions where purge_after <= now() order by purge_after for update skip locked loop
    -- a recovery that landed after the list was read wins
    if not exists (select 1 from public.account_deletions d where d.user_id = r.user_id and d.purge_after <= now()) then continue; end if;
    begin
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

-- 4. Hidden while pending: row security (restrictive, so it narrows every existing policy) -------
-- profiles is read school-wide; saved_classes and class_history are read through are_friends(),
-- which is a definer and so doesn't see the friend_requests rule below. my_sections, plans and
-- free_now are read through a friend_requests subquery, so hiding the friendship hides them — and
-- professify-plans.sql asserts exactly two policies on plans, so plans gets none here.
do $$
declare t record;
begin
  for t in select * from (values
      ('profiles', 'id'), ('saved_classes', 'user_id'), ('class_history', 'user_id'),
      ('watch_sections', 'user_id'), ('class_waivers', 'user_id')) as v(tbl, col)
  loop
    if to_regclass('public.' || t.tbl) is not null then
      execute format('drop policy if exists "hide accounts being deleted" on public.%I', t.tbl);
      execute format('create policy "hide accounts being deleted" on public.%I as restrictive for select to anon, authenticated using (%I = auth.uid() or not public.is_pending_deletion(%I))', t.tbl, t.col, t.col);
    end if;
  end loop;
end $$;

-- A friendship with someone being deleted disappears from the other person's list until they recover.
drop policy if exists "hide accounts being deleted" on public.friend_requests;
create policy "hide accounts being deleted" on public.friend_requests as restrictive for select to anon, authenticated
  using ((from_user = auth.uid() or not public.is_pending_deletion(from_user))
     and (to_user = auth.uid() or not public.is_pending_deletion(to_user)));
-- …and no new friend requests to or from them, and no adding them to a chat.
drop policy if exists "no requests to accounts being deleted" on public.friend_requests;
create policy "no requests to accounts being deleted" on public.friend_requests as restrictive for insert to anon, authenticated
  with check (not public.is_pending_deletion(from_user) and not public.is_pending_deletion(to_user));
do $$ begin
  if to_regclass('public.group_members') is not null then
    drop policy if exists "no adding accounts being deleted" on public.group_members;
    create policy "no adding accounts being deleted" on public.group_members as restrictive for insert to anon, authenticated
      with check (not public.is_pending_deletion(user_id));
  end if;
end $$;
drop policy if exists "no adding accounts being deleted" on public.conversation_members;
create policy "no adding accounts being deleted" on public.conversation_members as restrictive for insert to anon, authenticated
  with check (not public.is_pending_deletion(user_id));

-- 5. Hidden while pending: the people functions (they bypass row security) ----------------------
do $$
declare
  base text; cur oid; b oid; args text; idargs text; res text; argn text; vol text; filt text;
  ga boolean; gu boolean; nm text;
  names text[] := array['search_people','find_people','find_profile_by_handle','suggest_friends','suggest_friends_unscoped',
                        'suggest_classmates','suggest_classmates_unscoped','suggest_classmates_v2','friends_of','get_inviter','friend_emails',
                        'friends_reviewed','professor_suggested_by'];
begin
  foreach nm in array names loop
    cur := null; b := null;
    if (select count(*) from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = nm) > 1 then
      raise exception '% has more than one version — wrap each by hand', nm;
    end if;
    select p.oid into cur from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = nm;
    if cur is null then continue; end if;                                     -- not on this database
    base := nm || '__incl_pending';
    select p.oid into b from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = base;
    -- who may call it: read off the function students call today (the original, or the wrapper on a re-run)
    ga := has_function_privilege('anon', cur, 'execute');
    gu := has_function_privilege('authenticated', cur, 'execute');
    if b is null then
      execute format('alter function public.%I(%s) rename to %I', nm, pg_get_function_identity_arguments(cur), base);
      b := cur;
    elsif (select prosrc from pg_proc where oid = cur) not like '%' || base || '%' then
      raise exception '% was re-created by another file after it was wrapped. Put its new body into %, then run this file again.', nm, base;
    end if;
    args   := pg_get_function_arguments(b);
    idargs := pg_get_function_identity_arguments(b);
    res    := pg_get_function_result(b);
    vol    := case (select provolatile from pg_proc where oid = b) when 'i' then 'immutable' when 's' then 'stable' else 'volatile' end;
    select string_agg(quote_ident(a), ', ' order by o) into argn
      from unnest((select proargnames from pg_proc where oid = b)) with ordinality as x(a, o)
     where o <= (select pronargs from pg_proc where oid = b);
    filt := case nm
      when 'get_inviter' then 'where not public.is_pending_deletion(ref)'
      when 'friends_of'  then 'where not public.is_pending_deletion(x.id) and not public.is_pending_deletion(p_user)'
      else 'where not public.is_pending_deletion(x.id)' end;
    execute format('create or replace function public.%I(%s) returns %s language sql %s security definer set search_path = public as %L',
                   nm, args, res, vol,
                   format('select x.* from public.%I(%s) x %s', base, coalesce(argn, ''), filt));
    -- nobody calls the unfiltered one directly; the filter keeps exactly the original's callers
    execute format('revoke all on function public.%I(%s) from public, anon, authenticated', base, idargs);
    execute format('revoke all on function public.%I(%s) from public, anon, authenticated', nm, idargs);
    if ga then execute format('grant execute on function public.%I(%s) to anon', nm, idargs); end if;
    if gu then execute format('grant execute on function public.%I(%s) to authenticated', nm, idargs); end if;
  end loop;
end $$;

-- 6. The daily job ----------------------------------------------------------------------------------
do $$ begin
  begin
    create extension if not exists pg_cron;
  exception when others then
    raise exception 'pg_cron is not on. Supabase dashboard → Integrations → Cron → Enable, then run this file again. (%)', sqlerrm;
  end;
end $$;
select cron.schedule('termchamp-purge-deleted-accounts', '7 11 * * *', 'select public.purge_due_account_deletions()');   -- 4:07am PT daily
select cron.schedule('termchamp-trim-cron-history', '17 11 * * *', $j$delete from cron.job_run_details where end_time < now() - interval '14 days'$j$);

-- 7. Self-checks: stop here, with nothing applied, if any of this didn't take ----------------------
do $$
declare nm text;
begin
  if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'reports'
              and column_name = 'reporter' and is_nullable = 'NO') then
    raise exception 'reports.reporter is still NOT NULL — anyone who filed a report could not be deleted';
  end if;
  if has_table_privilege('authenticated', 'public.account_deletions', 'select') then raise exception 'students can read account_deletions'; end if;
  if has_function_privilege('authenticated', 'public.purge_due_account_deletions()', 'execute') then raise exception 'students can run the purge'; end if;
  if has_function_privilege('authenticated', 'public.delete_my_account_v2(boolean)', 'execute') then raise exception 'students can skip the 30 days'; end if;
  if not has_function_privilege('authenticated', 'public.request_account_deletion(boolean)', 'execute') then raise exception 'students cannot ask to delete'; end if;
  if has_function_privilege('anon', 'public.request_account_deletion(boolean)', 'execute') then raise exception 'anon can ask to delete'; end if;
  if (select count(*) from pg_policies where schemaname = 'public' and policyname = 'hide accounts being deleted' and permissive = 'RESTRICTIVE') < 6 then
    raise exception 'not every table hides accounts being deleted';
  end if;
  foreach nm in array array['search_people','find_people','find_profile_by_handle','suggest_friends','suggest_friends_unscoped',
                            'suggest_classmates','suggest_classmates_unscoped','suggest_classmates_v2','friends_of','get_inviter','friend_emails',
                        'friends_reviewed','professor_suggested_by'] loop
    if to_regproc('public.' || nm || '__incl_pending') is not null then
      if (select prosrc from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = nm) not like '%is_pending_deletion%' then
        raise exception '% is not filtered', nm;
      end if;
      if has_function_privilege('authenticated', (select p.oid from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = nm || '__incl_pending'), 'execute') then
        raise exception 'students can still call %__incl_pending directly', nm;
      end if;
    end if;
  end loop;
  if not exists (select 1 from cron.job where jobname = 'termchamp-purge-deleted-accounts' and active) then
    raise exception 'the daily deletion job is not scheduled';
  end if;
  if exists (select 1 from pg_policies where tablename = 'plans' and policyname = 'hide accounts being deleted') then
    raise exception 'plans must keep exactly its two policies (professify-plans.sql checks that)';
  end if;
end $$;

commit;

notify pgrst, 'reload schema';
