-- =================================================================================================
-- TermChamp push notifications (2026-10-06)
-- -------------------------------------------------------------------------------------------------
-- Run once in the Supabase SQL editor, then fill in push_config (bottom of this file).
-- Safe to run again: everything is "if not exists" / "create or replace" / drop-then-create.
--
-- LIVING NEXT TO professify-push.sql (6 Oct, adapted for production). That file is already live and
-- owns public.push_outbox, public.push_prefs and public.push_enqueue(7 args) for the website's Web
-- Push. Written fresh, this file reused those three names with different columns, so on the real
-- database it stopped at the first index ("column dedupe does not exist") and nothing worked. Now:
--   · this file's queue is public.push_queue and its one way in is public.push_queue_add();
--   · push_prefs is shared: this adds the `prefs` jsonb column the app's Settings › Notifications
--     reads and writes, and leaves the old columns alone;
--   · the iPhone sender is supabase/functions/send-push. push-send stays the website's Web Push.
-- Proven on a local replica with professify-push.sql applied first: runs twice clean, every trigger
-- queues what it should and nothing else.
--
-- What sends a push (each one can be turned off in the app's Settings › Notifications):
--   seat_open        a seat opens in a section you watch or have in a plan        (course_seats update)
--   plan_full        a section in one of your plans fills up                      (course_seats update)
--   registration     the evening before and the morning registration opens        (hourly cron)
--   friend_request   someone sends you a friend request                           (friend_requests insert)
--   friend_in_class  a friend adds a class / section you're in                    (saved_classes, my_sections)
--   dm / group       a new message, unless you muted that chat                    (messages insert)
--   group_added      a friend adds you to a group chat                            (conversation_members insert)
--   like             someone likes a message you sent, unless you muted that chat (message_likes insert)
--
-- How it flows: the triggers below never send anything themselves. They put a row in push_queue
-- (after checking your choices, mutes, blocks and duplicate windows), then poke the send-push edge
-- function once per transaction through pg_net. The function claims the rows and talks to Apple.
-- A trigger that fails only logs a warning: a push bug can never stop a message, a friend request
-- or a seat update from saving.
-- =================================================================================================

create extension if not exists pg_net;
create extension if not exists pg_cron;

-- ---------------------------------------------------------------------------- settings (private)
create table if not exists public.push_config (key text primary key, value text);
alter table public.push_config enable row level security;          -- no policies: definer functions only
revoke all on public.push_config from anon, authenticated;

create or replace function public.push_cfg(k text) returns text
language sql stable security definer set search_path = public as
$$ select value from public.push_config where key = k $$;
revoke execute on function public.push_cfg(text) from public, anon, authenticated;

-- ---------------------------------------------------------------------------- device tokens
create table if not exists public.push_tokens (
  token      text primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  platform   text not null default 'ios' check (platform in ('ios')),
  env        text check (env in ('production', 'sandbox')),   -- learned by send-push on first delivery
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists push_tokens_user on public.push_tokens (user_id);
alter table public.push_tokens enable row level security;          -- no policies: only the functions below
revoke all on public.push_tokens from anon, authenticated;

-- A phone signed into a new account takes its token with it; at most 10 phones per account.
create or replace function public.register_push_token(p_token text, p_platform text default 'ios')
returns void language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'not signed in'; end if;
  if p_token is null or p_token !~ '^[0-9A-Fa-f]{32,200}$' then raise exception 'bad token'; end if;
  insert into push_tokens (token, user_id, platform, updated_at) values (lower(p_token), me, coalesce(p_platform, 'ios'), now())
  on conflict (token) do update set user_id = excluded.user_id, updated_at = now(),
    env = case when push_tokens.user_id = excluded.user_id then push_tokens.env else null end;
  delete from push_tokens where user_id = me and token in (
    select token from push_tokens where user_id = me order by updated_at desc offset 10);
end $$;

create or replace function public.unregister_push_token(p_token text)
returns void language sql security definer set search_path = public as
$$ delete from public.push_tokens where token = lower(p_token) and user_id = auth.uid() $$;

create or replace function public.forget_my_push_tokens()
returns void language sql security definer set search_path = public as
$$ delete from public.push_tokens where user_id = auth.uid() $$;

revoke execute on function public.register_push_token(text, text), public.unregister_push_token(text), public.forget_my_push_tokens() from public, anon;
grant  execute on function public.register_push_token(text, text), public.unregister_push_token(text), public.forget_my_push_tokens() to authenticated;

-- ---------------------------------------------------------------------------- choices
-- {"dm": false, ...}: a kind is on unless it says false.
create table if not exists public.push_prefs (
  user_id    uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  prefs      jsonb not null default '{}'::jsonb check (jsonb_typeof(prefs) = 'object' and pg_column_size(prefs) < 2000),
  updated_at timestamptz not null default now()
);
-- On production push_prefs already exists (professify-push.sql: seats, friends, quiet hours), so the
-- create above is skipped. Add what this needs to it; the old columns stay for the website's pushes.
alter table public.push_prefs add column if not exists prefs jsonb not null default '{}'::jsonb;
alter table public.push_prefs add column if not exists updated_at timestamptz not null default now();
alter table public.push_prefs alter column user_id set default auth.uid();
alter table public.push_prefs enable row level security;
drop policy if exists "push_prefs read own" on public.push_prefs;
drop policy if exists "push_prefs insert own" on public.push_prefs;
drop policy if exists "push_prefs update own" on public.push_prefs;
create policy "push_prefs read own"   on public.push_prefs for select to authenticated using (user_id = auth.uid());
create policy "push_prefs insert own" on public.push_prefs for insert to authenticated with check (user_id = auth.uid());
create policy "push_prefs update own" on public.push_prefs for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
grant select, insert, update on public.push_prefs to authenticated;

-- ---------------------------------------------------------------------------- muted chats
-- conversation_id takes whatever type conversations.id already is.
do $$
declare ty text;
begin
  select format_type(a.atttypid, a.atttypmod) into ty
  from pg_attribute a where a.attrelid = 'public.conversations'::regclass and a.attname = 'id';
  execute format($f$
    create table if not exists public.conversation_mutes (
      user_id         uuid not null default auth.uid() references auth.users(id) on delete cascade,
      conversation_id %s not null references public.conversations(id) on delete cascade,
      created_at      timestamptz not null default now(),
      primary key (user_id, conversation_id))$f$, ty);
end $$;
alter table public.conversation_mutes enable row level security;
drop policy if exists "mutes read own" on public.conversation_mutes;
drop policy if exists "mutes insert own" on public.conversation_mutes;
drop policy if exists "mutes delete own" on public.conversation_mutes;
create policy "mutes read own"   on public.conversation_mutes for select to authenticated using (user_id = auth.uid());
create policy "mutes insert own" on public.conversation_mutes for insert to authenticated with check (
  user_id = auth.uid() and exists (select 1 from public.conversation_members m
    where m.conversation_id = conversation_mutes.conversation_id and m.user_id = auth.uid()));
create policy "mutes delete own" on public.conversation_mutes for delete to authenticated using (user_id = auth.uid());
grant select, insert, delete on public.conversation_mutes to authenticated;

-- ---------------------------------------------------------------------------- the outbox
create table if not exists public.push_queue (
  id          bigserial primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  kind        text not null,
  title       text not null,
  body        text not null,
  data        jsonb not null default '{}'::jsonb,   -- where a tap goes: {"t":"chat","id":...}
  thread      text,                                 -- iOS groups notifications by this
  dedupe      text,
  send_after  timestamptz not null default now(),
  claimed_at  timestamptz,
  sent_at     timestamptz,
  tries       int not null default 0,
  error       text,
  created_at  timestamptz not null default now()
);
create index if not exists push_queue_due    on public.push_queue (send_after) where sent_at is null;
create index if not exists push_queue_dedupe on public.push_queue (user_id, dedupe, created_at) where dedupe is not null;
create index if not exists push_queue_kind   on public.push_queue (user_id, kind, created_at);
alter table public.push_queue enable row level security;          -- service role only
revoke all on public.push_queue from anon, authenticated;

-- ---------------------------------------------------------------------------- helpers
create or replace function public.push_name(uid uuid) returns text
language sql stable security definer set search_path = public as
$$ select coalesce(nullif(trim(display_name), ''), nullif(username, ''), 'Someone') from public.profiles where id = uid $$;

create or replace function public.push_are_friends(a uuid, b uuid) returns boolean
language sql stable security definer set search_path = public as
$$ select exists (select 1 from public.friend_requests where status = 'accepted'
     and ((from_user = a and to_user = b) or (from_user = b and to_user = a))) $$;

-- Blocks: find the app's block table (two uuid columns, name contains "block") and check it both ways,
-- so blocker/blocked column order doesn't matter.
do $$
declare t text; c1 text; c2 text;
begin
  select tbl, cols[1], cols[2] into t, c1, c2 from (
    select c.table_name::text tbl, array_agg(c.column_name::text order by c.ordinal_position) cols
    from information_schema.columns c
    join information_schema.tables tt on tt.table_schema = c.table_schema and tt.table_name = c.table_name and tt.table_type = 'BASE TABLE'
    where c.table_schema = 'public' and c.table_name ilike '%block%' and c.data_type = 'uuid' and c.column_name <> 'id'
    group by c.table_name having count(*) = 2) x
  order by (tbl = 'blocks') desc, (tbl = 'user_blocks') desc, tbl limit 1;
  if t is null then
    raise warning 'push: no block table found, push_is_blocked() returns false. Point it at your blocks table.';
    execute $f$create or replace function public.push_is_blocked(a uuid, b uuid) returns boolean language sql stable as 'select false'$f$;
  else
    execute format($f$create or replace function public.push_is_blocked(a uuid, b uuid) returns boolean
      language sql stable security definer set search_path = public as
      'select exists (select 1 from public.%I where (%I = a and %I = b) or (%I = b and %I = a))'$f$, t, c1, c2, c1, c2);
    raise notice 'push: blocks are read from public.% (%, %)', t, c1, c2;
  end if;
end $$;

-- Cal Poly's raw seat status → open / wait / full / unknown (the app's seatStatusOf, in SQL).
create or replace function public.push_seat_state(status text, avail int) returns text
language plpgsql immutable as $$
declare t text := lower(regexp_replace(coalesce(status, ''), '[\s_-]+', '', 'g'));
begin
  if t in ('waitlist', 'waitlisted', 'wl') then return 'wait'; end if;
  if t in ('closed', 'full', 'cancelled', 'canceled') then return 'full'; end if;
  if t in ('open', 'available') then return 'open'; end if;
  return case when coalesce(avail, 0) > 0 then 'open' else 'unknown' end;
end $$;

-- "S04-SEM Regular" → "S04", "01" → "Sec 01" (the app's secLabel).
create or replace function public.push_sec_label(sec text) returns text
language sql immutable as $$
  select case when tok = '' then '' when tok ~ '^\d' then 'Sec ' || tok else tok end
  from (select split_part(regexp_replace(trim(coalesce(sec, '')), '[-\s].*$', ''), ' ', 1) as tok) x
$$;

-- The one way into the outbox. Returns the new row id, or null when it shouldn't send.
create or replace function public.push_queue_add(
  p_user uuid, p_kind text, p_title text, p_body text, p_data jsonb, p_thread text,
  p_dedupe text default null, p_window interval default null, p_delay interval default '0',
  p_daily_cap int default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare nid bigint;
begin
  if p_user is null then return null; end if;
  if not exists (select 1 from push_tokens where user_id = p_user) then return null; end if;
  if exists (select 1 from push_prefs where user_id = p_user and prefs ->> p_kind = 'false') then return null; end if;
  if p_dedupe is not null and exists (select 1 from push_queue where user_id = p_user and dedupe = p_dedupe
       and created_at > now() - coalesce(p_window, interval '1 day')) then return null; end if;
  if p_daily_cap is not null and (select count(*) from push_queue where user_id = p_user and kind = p_kind
       and created_at > now() - interval '1 day') >= p_daily_cap then return null; end if;
  insert into push_queue (user_id, kind, title, body, data, thread, dedupe, send_after)
  values (p_user, p_kind, left(p_title, 120), left(p_body, 240), coalesce(p_data, '{}'), p_thread, p_dedupe, now() + coalesce(p_delay, '0'))
  returning id into nid;
  if coalesce(p_delay, '0') <= interval '0' then perform push_kick(); end if;
  return nid;
end $$;

-- Poke send-push once per transaction. pg_net sends after commit, so it sees every row this
-- transaction queued (a 3,000-row seat update pokes once, not 3,000 times).
create or replace function public.push_kick() returns void
language plpgsql security definer set search_path = public as $$
declare u text := push_cfg('function_url'); s text := push_cfg('secret');
begin
  if u is null or s is null or current_setting('tc.push_kicked', true) = '1' then return; end if;
  perform set_config('tc.push_kicked', '1', true);
  perform net.http_post(url := u, body := '{}'::jsonb,
    headers := jsonb_build_object('content-type', 'application/json', 'x-push-secret', s));
end $$;

-- Every minute: send what was delayed, and retry what didn't go out.
create or replace function public.push_kick_due() returns void
language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from push_queue where sent_at is null and send_after <= now() and tries < 5
             and (claimed_at is null or claimed_at < now() - interval '2 minutes')) then
    perform push_kick();
  end if;
end $$;

-- send-push claims a batch. Each row comes with that account's tokens.
create or replace function public.push_claim(p_limit int default 100)
returns table (id bigint, user_id uuid, kind text, title text, body text, data jsonb, thread text, tries int, tokens jsonb)
language sql security definer set search_path = public as $$
  with picked as (
    select o.id from push_queue o
    where o.sent_at is null and o.send_after <= now() and o.tries < 5
      and (o.claimed_at is null or o.claimed_at < now() - interval '2 minutes')
    order by o.id limit least(greatest(p_limit, 1), 500)
    for update skip locked),
  upd as (
    update push_queue o set claimed_at = now(), tries = o.tries + 1
    from picked where o.id = picked.id
    returning o.id, o.user_id, o.kind, o.title, o.body, o.data, o.thread, o.tries)
  select u.id, u.user_id, u.kind, u.title, u.body, u.data, u.thread, u.tries,
    coalesce((select jsonb_agg(jsonb_build_object('token', t.token, 'env', t.env)) from push_tokens t where t.user_id = u.user_id), '[]'::jsonb)
  from upd u
$$;

revoke execute on function public.push_queue_add(uuid, text, text, text, jsonb, text, text, interval, interval, int),
  public.push_kick(), public.push_kick_due(), public.push_claim(int),
  public.push_name(uuid), public.push_are_friends(uuid, uuid), public.push_is_blocked(uuid, uuid)
  from public, anon, authenticated;
grant execute on function public.push_claim(int) to service_role;

-- ================================================================================= the triggers
-- --------------------------------------------------------------------- messages → dm / group
create or replace function public.push_on_message() returns trigger
language plpgsql security definer set search_path = public as $$
declare c record; r record; who text; txt text; is_dm boolean;
begin
  begin
    select id, kind, title into c from conversations where id = new.conversation_id;
    if not found then return null; end if;
    is_dm := c.kind = 'direct';
    who := push_name(new.sender);
    txt := case
      when new.kind = 'class'     then coalesce(nullif(trim(new.body), ''), 'Shared ' || coalesce(new.payload ->> 'code', 'a class'))
      when new.kind = 'professor' then coalesce(nullif(trim(new.body), ''), 'Shared ' || coalesce(new.payload ->> 'name', 'a professor'))
      when coalesce(new.body, '') ~ 'termchamp\.com/s\?' then
        coalesce(nullif(trim(regexp_replace(new.body, '\s*https?://\S*termchamp\.com/s\?\S*', '', 'g')), ''), 'Shared a schedule')
      else coalesce(nullif(trim(new.body), ''), 'Sent a message') end;
    for r in select m.user_id from conversation_members m
             where m.conversation_id = new.conversation_id and m.user_id <> new.sender loop
      continue when exists (select 1 from conversation_mutes x where x.user_id = r.user_id and x.conversation_id = new.conversation_id);
      continue when push_is_blocked(r.user_id, new.sender);
      perform push_queue_add(r.user_id, case when is_dm then 'dm' else 'group' end,
        case when is_dm then who else coalesce(nullif(trim(c.title), ''), 'Group chat') end,
        case when is_dm then txt else split_part(who, ' ', 1) || ': ' || txt end,
        jsonb_build_object('t', 'chat', 'id', new.conversation_id), 'chat:' || new.conversation_id);
    end loop;
  exception when others then raise warning 'push_on_message: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_message on public.messages;
create trigger push_on_message after insert on public.messages for each row execute function public.push_on_message();

-- --------------------------------------------------------------------- message_likes → like
create or replace function public.push_on_like() returns trigger
language plpgsql security definer set search_path = public as $$
declare m record; txt text;
begin
  begin
    select id, sender, conversation_id, body, kind, payload into m from messages where id = new.message_id;
    if not found or m.sender = new.user_id then return null; end if;
    if exists (select 1 from conversation_mutes x where x.user_id = m.sender and x.conversation_id = m.conversation_id) then return null; end if;
    if push_is_blocked(m.sender, new.user_id) then return null; end if;
    txt := case when coalesce(trim(m.body), '') = '' then 'your message'
                when m.body ~ 'termchamp\.com/s\?' then 'your schedule'
                else '“' || left(trim(m.body), 80) || case when length(trim(m.body)) > 80 then '…' else '' end || '”' end;
    perform push_queue_add(m.sender, 'like', push_name(new.user_id), 'Liked ' || txt,
      jsonb_build_object('t', 'chat', 'id', m.conversation_id), 'chat:' || m.conversation_id,
      'like:' || new.message_id || ':' || new.user_id, interval '30 days');
  exception when others then raise warning 'push_on_like: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_like on public.message_likes;
create trigger push_on_like after insert on public.message_likes for each row execute function public.push_on_like();

-- --------------------------------------------------------------------- conversation_members → group_added
create or replace function public.push_on_member() returns trigger
language plpgsql security definer set search_path = public as $$
declare c record;
begin
  begin
    select id, kind, title, created_by into c from conversations where id = new.conversation_id;
    if not found or c.kind <> 'group' or new.user_id = c.created_by then return null; end if;
    if push_is_blocked(new.user_id, c.created_by) then return null; end if;
    perform push_queue_add(new.user_id, 'group_added', coalesce(nullif(trim(c.title), ''), 'New group chat'),
      push_name(c.created_by) || ' added you to a group',
      jsonb_build_object('t', 'chat', 'id', new.conversation_id), 'chat:' || new.conversation_id,
      'grp:' || new.conversation_id, interval '365 days');
  exception when others then raise warning 'push_on_member: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_member on public.conversation_members;
create trigger push_on_member after insert on public.conversation_members for each row execute function public.push_on_member();

-- --------------------------------------------------------------------- friend_requests → friend_request
create or replace function public.push_on_friend_request() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  begin
    if new.status is distinct from 'pending' or new.from_user = new.to_user then return null; end if;
    if push_is_blocked(new.to_user, new.from_user) then return null; end if;
    perform push_queue_add(new.to_user, 'friend_request', 'Friend request',
      push_name(new.from_user) || ' wants to be friends on TermChamp',
      jsonb_build_object('t', 'requests'), 'friends',
      'fr:' || new.from_user, interval '7 days');
  exception when others then raise warning 'push_on_friend_request: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_friend_request on public.friend_requests;
create trigger push_on_friend_request after insert on public.friend_requests for each row execute function public.push_on_friend_request();

-- --------------------------------------------------------------------- saved_classes → friend_in_class
-- Waits 2 minutes, so the section (my_sections, a moment later) can sharpen it to "your section".
-- One per friend per class, and at most 4 a day per person, so a 6-class import isn't 6 pushes.
create or replace function public.push_on_saved_class() returns trigger
language plpgsql security definer set search_path = public as $$
declare f record;
begin
  begin
    for f in select case when fr.from_user = new.user_id then fr.to_user else fr.from_user end as uid
             from friend_requests fr where fr.status = 'accepted' and (fr.from_user = new.user_id or fr.to_user = new.user_id) loop
      continue when not exists (select 1 from saved_classes s where s.user_id = f.uid and s.term::text = new.term::text and s.code = new.code);
      perform push_queue_add(f.uid, 'friend_in_class', push_name(new.user_id), 'Is taking ' || new.code || ' too',
        jsonb_build_object('t', 'friend', 'id', new.user_id), 'friends',
        'fic:' || new.user_id || ':' || new.code || ':' || new.term, interval '120 days', interval '2 minutes', 4);
    end loop;
  exception when others then raise warning 'push_on_saved_class: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_saved_class on public.saved_classes;
create trigger push_on_saved_class after insert on public.saved_classes for each row execute function public.push_on_saved_class();

create or replace function public.push_on_my_section() returns trigger
language plpgsql security definer set search_path = public as $$
declare f record; k text;
begin
  begin
    if new.class_nbr is null then return null; end if;
    k := 'fic:' || new.user_id || ':' || new.code || ':' || new.term;
    for f in select case when fr.from_user = new.user_id then fr.to_user else fr.from_user end as uid
             from friend_requests fr where fr.status = 'accepted' and (fr.from_user = new.user_id or fr.to_user = new.user_id) loop
      continue when not exists (select 1 from my_sections s where s.user_id = f.uid and s.term::text = new.term::text
                                and s.class_nbr::text = new.class_nbr::text);
      update push_queue set body = 'Is in your ' || new.code || ' section'
       where user_id = f.uid and dedupe = k and sent_at is null and claimed_at is null;
    end loop;
  exception when others then raise warning 'push_on_my_section: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_my_section on public.my_sections;
create trigger push_on_my_section after insert on public.my_sections for each row execute function public.push_on_my_section();

-- --------------------------------------------------------------------- course_seats → seat_open / plan_full
-- Fires on UPDATE. The seat scraper must update rows in place (upsert is fine). If it deletes and
-- re-inserts the term instead, nothing changes from one row to the next and no seat push is sent.
create or replace function public.push_on_seats() returns trigger
language plpgsql security definer set search_path = public as $$
declare a text; b text; r record; nm text; nbr text; trm text; opened boolean; filled boolean;
begin
  begin
    a := push_seat_state(old.status, old.available);
    b := push_seat_state(new.status, new.available);
    opened := (a <> 'open' and b = 'open' and coalesce(new.available, 1) > 0)
           or (a = 'open' and b = 'open' and coalesce(old.available, 0) = 0 and coalesce(new.available, 0) > 0);
    filled := a = 'open' and b in ('full', 'wait');
    if not opened and not filled then return null; end if;
    nbr := new.class_nbr::text; trm := new.term::text;
    nm  := trim(new.course_code || ' ' || push_sec_label(new.section));

    if opened then
      for r in
        select distinct x.user_id from (
          select w.user_id from watch_sections w where w.term::text = trm and w.class_nbr::text = nbr
          union
          select p.user_id from plans p where p.term::text = trm and p.sections::jsonb @> jsonb_build_array(jsonb_build_object('class_nbr', nbr))
        ) x
        where not exists (select 1 from my_sections s where s.user_id = x.user_id and s.term::text = trm
                          and s.class_nbr::text = nbr and coalesce(s.status, 'enrolled') <> 'waitlisted')
      loop
        perform push_queue_add(r.user_id, 'seat_open', 'Seat open: ' || nm,
          case when coalesce(new.available, 0) > 1 then new.available || ' seats open right now. Grab one before they’re gone.'
               else 'A seat just opened. Grab it before it’s gone.' end,
          jsonb_build_object('t', 'class', 'code', new.course_code), 'seats',
          'seat:' || trm || ':' || nbr, interval '6 hours');
      end loop;
    end if;

    if filled then
      for r in
        select p.user_id, string_agg('Plan ' || p.slot, ' and ' order by p.slot) as slots
        from plans p
        where p.term::text = trm and p.sections::jsonb @> jsonb_build_array(jsonb_build_object('class_nbr', nbr))
          and not exists (select 1 from my_sections s where s.user_id = p.user_id and s.term::text = trm
                          and s.class_nbr::text = nbr and coalesce(s.status, 'enrolled') <> 'waitlisted')
        group by p.user_id
      loop
        perform push_queue_add(r.user_id, 'plan_full', nm || ' just filled up',
          'It’s in your ' || r.slots || '. Tap to pick a backup section.',
          jsonb_build_object('t', 'class', 'code', new.course_code), 'seats',
          'full:' || trm || ':' || nbr, interval '12 hours');
      end loop;
    end if;
  exception when others then raise warning 'push_on_seats: %', sqlerrm;
  end;
  return null;
end $$;
drop trigger if exists push_on_seats on public.course_seats;
create trigger push_on_seats after update on public.course_seats for each row
  when (old.status is distinct from new.status or old.available is distinct from new.available)
  execute function public.push_on_seats();

-- --------------------------------------------------------------------- registration reminders (hourly)
-- 6pm the day before and 7am the day of, in San Luis Obispo time. Reads push_config:
-- registration_opens (YYYY-MM-DD) and registration_term — keep them equal to the app's
-- REGISTRATION_OPENS / REGISTRATION_TERM.
create or replace function public.push_registration_tick() returns void
language plpgsql security definer set search_path = public as $$
declare d date; trm text; loc timestamp := now() at time zone 'America/Los_Angeles'; stage text; u record;
begin
  begin d := push_cfg('registration_opens')::date; exception when others then return; end;
  trm := coalesce(push_cfg('registration_term'), 'next term');
  if d is null then return; end if;
  if loc::date = d - 1 and extract(hour from loc) = 18 then stage := 'eve';
  elsif loc::date = d and extract(hour from loc) = 7 then stage := 'day';
  else return; end if;
  for u in select distinct user_id from push_tokens loop
    perform push_queue_add(u.user_id, 'registration',
      case when stage = 'eve' then trm || ' registration opens tomorrow' else trm || ' registration opens today' end,
      'Check your appointment time in the Cal Poly Portal and get your plans ready.',
      jsonb_build_object('t', 'plans'), 'registration',
      'reg:' || trm || ':' || stage, interval '3 days');
  end loop;
end $$;
revoke execute on function public.push_registration_tick() from public, anon, authenticated;

-- --------------------------------------------------------------------- housekeeping
create or replace function public.push_cleanup() returns void
language sql security definer set search_path = public as $$
  delete from public.push_queue where created_at < now() - interval '7 days' and kind in ('dm', 'group', 'like');
  delete from public.push_queue where created_at < now() - interval '400 days';
$$;
revoke execute on function public.push_cleanup() from public, anon, authenticated;

-- --------------------------------------------------------------------- schedules
do $$
begin
  perform cron.unschedule(jobid) from cron.job where jobname in ('termchamp-push-due', 'termchamp-push-registration', 'termchamp-push-cleanup');
  perform cron.schedule('termchamp-push-due',          '* * * * *',  'select public.push_kick_due()');
  perform cron.schedule('termchamp-push-registration', '5 * * * *',  'select public.push_registration_tick()');
  perform cron.schedule('termchamp-push-cleanup',      '17 4 * * *', 'select public.push_cleanup()');
end $$;

-- =================================================================================================
-- FILL THESE IN (then nothing else to do here):
--   function_url : https://<project-ref>.supabase.co/functions/v1/send-push
--   secret       : a long random string; the same value goes in the function's PUSH_SECRET
-- =================================================================================================
-- insert into public.push_config (key, value) values
--   ('function_url',       'https://rqkndeqbcahozidniesn.supabase.co/functions/v1/send-push'),
--   ('secret',             '<paste a long random string>'),
--   ('registration_opens', '2026-10-19'),
--   ('registration_term',  'Spring 2027')
-- on conflict (key) do update set value = excluded.value;

-- ================================================================================= self-check
-- Read-only. Every row should say ok (push_config rows say "fill in" until you insert them).
select 'push_tokens RLS on' as check, case when relrowsecurity then 'ok' else 'FAIL' end as result
  from pg_class where oid = 'public.push_tokens'::regclass
union all select 'push_queue RLS on', case when relrowsecurity then 'ok' else 'FAIL' end
  from pg_class where oid = 'public.push_queue'::regclass
union all select 'push_prefs has prefs column',
  case when exists (select 1 from information_schema.columns where table_schema='public' and table_name='push_prefs' and column_name='prefs') then 'ok' else 'FAIL' end
union all select 'website push untouched (push_outbox.dedupe_key)',
  case when exists (select 1 from information_schema.columns where table_schema='public' and table_name='push_outbox' and column_name='dedupe_key')
       or not exists (select 1 from information_schema.tables where table_schema='public' and table_name='push_outbox') then 'ok' else 'FAIL' end
union all select 'anon cannot register a token',
  case when has_function_privilege('anon','public.register_push_token(text,text)','execute') then 'FAIL' else 'ok' end
union all select 'triggers installed (expect 7)', (select count(*)::text from pg_trigger where tgname in
  ('push_on_message','push_on_like','push_on_member','push_on_friend_request','push_on_saved_class','push_on_my_section','push_on_seats'))
union all select 'cron jobs (expect 3)', (select count(*)::text from cron.job where jobname like 'termchamp-push-%')
union all select 'push_config: function_url', coalesce((select 'ok' from public.push_config where key='function_url'), 'fill in')
union all select 'push_config: secret', coalesce((select 'ok' from public.push_config where key='secret'), 'fill in');
