-- =================================================================================================
-- TermChamp: one account, same data on the phone and the website — 2026-10-15
--
-- Run after professify-security-pass2-2026-10-15.sql. One transaction; safe to run twice.
-- Adds only: two small functions, one table, one column, and two pref checks in the push queue.
-- Nothing is deleted; no student row is changed except that the pin limit goes from 2 to 3.
--
--   1. Pinned friends (stories). Pins live in profiles.pinned_friends. Other students must not read
--      your pins, so the column stays unreadable; you read your own through my_pinned_friends() and
--      write them through set_pinned_friends(uuid[]) (only friends, at most 3, no repeats).
--   2. Saved items (the website's watched classes/professors and the phone's Explore bookmarks):
--      one table, saved_items(kind 'class'|'prof', key), own rows only.
--   3. Chat pins (the phone pins chats): conversation_members.pinned_at, own row only.
--   4. Push settings mean the same thing everywhere: turning a kind off on either device stops it
--      on both (web push now honours the per-kind prefs; phone push honours the website's
--      "seat alerts" switch).
-- =================================================================================================

begin;

-- ---------- 1. Pinned friends -------------------------------------------------------------------
alter table public.profiles drop constraint if exists profiles_pinned_friends_max2;
alter table public.profiles drop constraint if exists profiles_pins_max_ck;
alter table public.profiles drop constraint if exists profiles_pins_max3;
alter table public.profiles add constraint profiles_pins_max3
  check (pinned_friends is null or cardinality(pinned_friends) <= 3);

create or replace function public.my_pinned_friends()
 returns uuid[]
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  select coalesce((select p.pinned_friends::text[]::uuid[] from public.profiles p where p.id = auth.uid()), '{}'::uuid[]);
$function$;
revoke execute on function public.my_pinned_friends() from public, anon;
grant execute on function public.my_pinned_friends() to authenticated;

create or replace function public.set_pinned_friends(p_ids uuid[])
 returns uuid[]
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare me uuid := auth.uid(); keep uuid[]; coltype text;
begin
  if me is null then raise exception 'not signed in' using errcode = '42501'; end if;
  -- only current friends, first 3, no repeats, order kept
  select coalesce(array_agg(x.id order by x.ord), '{}') into keep
  from (
    select id, min(ord) as ord
    from unnest(coalesce(p_ids, '{}'::uuid[])) with ordinality as u(id, ord)
    where id is not null and id <> me
      and exists (select 1 from public.friend_requests fr
                   where fr.status = 'accepted'
                     and ((fr.from_user = me and fr.to_user = u.id) or (fr.to_user = me and fr.from_user = u.id)))
    group by id
    order by min(ord)
    limit 3
  ) x;
  -- the column is uuid[] or text[] depending on how it was first made; write in its own type
  select format_type(a.atttypid, a.atttypmod) into coltype from pg_attribute a
   where a.attrelid = 'public.profiles'::regclass and a.attname = 'pinned_friends';
  execute format('update public.profiles set pinned_friends = $1::text[]::%s where id = $2', coltype) using keep, me;
  return keep;
end $function$;
revoke execute on function public.set_pinned_friends(uuid[]) from public, anon;
grant execute on function public.set_pinned_friends(uuid[]) to authenticated;

-- ---------- 2. Saved items ----------------------------------------------------------------------
create table if not exists public.saved_items (
  user_id    uuid        not null default auth.uid() references auth.users(id) on delete cascade,
  kind       text        not null check (kind in ('class', 'prof')),
  key        text        not null check (length(key) between 1 and 200),
  created_at timestamptz not null default now(),
  primary key (user_id, kind, key)
);
alter table public.saved_items enable row level security;
revoke all on public.saved_items from public, anon, authenticated;
grant select, insert, delete on public.saved_items to authenticated;
drop policy if exists "saved items are yours" on public.saved_items;
create policy "saved items are yours" on public.saved_items for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
do $$ begin
  if to_regprocedure('public.sec_rate_limit()') is not null then
    drop trigger if exists sec_rate_limit on public.saved_items;
    create trigger sec_rate_limit before insert on public.saved_items
      for each row execute function public.sec_rate_limit('saved_item', '300', '1 day', 'raise');
  end if;
end $$;

-- ---------- 3. Chat pins ------------------------------------------------------------------------
alter table public.conversation_members add column if not exists pinned_at timestamptz;
grant update (pinned_at) on public.conversation_members to authenticated;

-- ---------- 4. Push settings mean the same thing on both ----------------------------------------
do $$
declare src text;
begin
  -- web push (push_enqueue): also honour the per-kind switches the phone writes into prefs
  select prosrc into src from pg_proc where oid = 'public.push_enqueue(uuid,text,text,text,text,text,text)'::regprocedure;
  if position('sync-2026-10-15' in src) = 0 then
    if position('if not want then return false; end if;' in src) = 0 then
      raise exception 'VERIFY AGAINST LIVE: push_enqueue changed since the review';
    end if;
    src := replace(src, 'if not want then return false; end if;',
      'if not want then return false; end if;
  -- sync-2026-10-15: a kind switched off on the phone is off here too
  if coalesce(pref.prefs ->> p_kind, '''') = ''false'' then return false; end if;');
    execute format($f$create or replace function public.push_enqueue(p_user uuid, p_kind text, p_title text, p_body text, p_url text, p_tag text, p_dedupe text)
      returns boolean language plpgsql security definer set search_path to 'public' as %L$f$, src);
  end if;

  -- phone push (push_queue_add): the website's "seat alerts" switch also stops seat pushes
  select prosrc into src from pg_proc where oid = 'public.push_queue_add(uuid,text,text,text,jsonb,text,text,interval,interval,integer)'::regprocedure;
  if position('sync-2026-10-15' in src) = 0 then
    if position('and prefs ->> p_kind = ''false'') then return null; end if;' in src) = 0 then
      raise exception 'VERIFY AGAINST LIVE: push_queue_add changed since the review';
    end if;
    src := replace(src, 'and prefs ->> p_kind = ''false'') then return null; end if;',
      'and prefs ->> p_kind = ''false'') then return null; end if;
-- sync-2026-10-15: the website''s seat-alerts switch counts on the phone too
if p_kind in (''seat_open'',''waitlist'',''moved'',''dropped'',''seat'',''seats'')
   and exists (select 1 from push_prefs where user_id = p_user and seats = false) then return null; end if;');
    execute format($f$create or replace function public.push_queue_add(p_user uuid, p_kind text, p_title text, p_body text, p_data jsonb, p_thread text, p_dedupe text default null::text, p_window interval default null::interval, p_delay interval default '00:00:00'::interval, p_daily_cap integer default null::integer)
      returns bigint language plpgsql security definer set search_path to 'public' as %L$f$, src);
  end if;
end $$;
revoke execute on function public.push_enqueue(uuid,text,text,text,text,text,text) from public, anon, authenticated;
revoke execute on function public.push_queue_add(uuid,text,text,text,jsonb,text,text,interval,interval,integer) from public, anon, authenticated;

-- ---------- Self-checks -------------------------------------------------------------------------
do $$
begin
  if has_column_privilege('authenticated', 'public.profiles', 'pinned_friends', 'SELECT') then
    raise exception 'self-check: other students could read pins';
  end if;
  if not has_function_privilege('authenticated', 'public.set_pinned_friends(uuid[])', 'EXECUTE')
     or has_function_privilege('anon', 'public.my_pinned_friends()', 'EXECUTE') then
    raise exception 'self-check: pin function grants wrong';
  end if;
  if has_table_privilege('anon', 'public.saved_items', 'SELECT') or not has_table_privilege('authenticated', 'public.saved_items', 'INSERT') then
    raise exception 'self-check: saved_items grants wrong';
  end if;
  if position('sync-2026-10-15' in (select prosrc from pg_proc where oid='public.push_enqueue(uuid,text,text,text,text,text,text)'::regprocedure)) = 0 then
    raise exception 'self-check: push_enqueue not updated';
  end if;
  raise notice 'sync 2026-10-15: all self-checks passed';
end $$;

commit;
