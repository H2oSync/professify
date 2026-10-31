-- ================================================================================================
-- TermChamp · Connect contacts (2026-10-30)
-- ------------------------------------------------------------------------------------------------
-- The phone app reads the student's contacts ON THE PHONE, turns every number into E.164
-- (+1 for a 10-digit US number) and every email into lower-case, SHA-256s each one, and sends only
-- those hashes here, 1000 at a time. Nothing about the address book is stored: match_contacts()
-- compares and forgets.
--
--   profiles.phone_hash  the student's OWN number, optional (sign-up step / Settings). Stored as
--                        HMAC-SHA256(contact_pepper, sha256(e164)) — the pepper is a Vault secret,
--                        so a copy of the table alone can't be turned back into phone numbers
--                        (a bare sha256 of a phone number can: claude/contact-sync-design.md).
--                        Never selectable by anon/authenticated (column grants), and only
--                        set_my_phone() can change it (trigger guard; the table-level UPDATE grant
--                        on profiles would otherwise let PostgREST write it directly).
--   emails               nothing stored: compared against sha256(lower(auth.users.email)).
--
--   match_contacts(hashes text[])  → (id, display_name, username, avatar_url, matched text[])
--        same school, same demo wall, not the caller, not blocked either way, not being deleted,
--        not suspended, not a deleted/banned sign-in. ≤ 2000 hashes a call, 20 calls an hour and
--        60 a day per student (rate_log bucket 'contacts'). `matched` = which of the caller's own
--        hashes hit, so the phone can leave those people out of its Invite list.
--   set_my_phone(p_hash text)      → boolean (true saved, false cleared). '' or null clears.
--   my_phone_saved()               → boolean.
--
-- Idempotent: run it again and nothing changes. EXECUTE: authenticated only.
-- Run in the Supabase SQL editor (as postgres). Undo: bottom of the file, commented out.
-- ================================================================================================
begin;

-- 1. The Vault key (made once; never rotate it without clearing every phone_hash — they'd stop matching).
do $$
begin
  if not exists (select 1 from vault.secrets where name = 'contact_pepper') then
    perform vault.create_secret(encode(extensions.gen_random_bytes(32), 'hex'), 'contact_pepper',
      'TermChamp contact matching: HMAC key for profiles.phone_hash. Rotating it unlinks every saved number.');
  end if;
end $$;

-- 2. The column: one number per account, one account per number, a 64-hex shape or nothing.
alter table public.profiles add column if not exists phone_hash text;
alter table public.profiles drop constraint if exists profiles_phone_hash_shape;
alter table public.profiles add constraint profiles_phone_hash_shape check (phone_hash is null or phone_hash ~ '^[0-9a-f]{64}$');
create unique index if not exists profiles_phone_hash_uniq on public.profiles (phone_hash) where phone_hash is not null;
-- profiles has column-level SELECT grants (no table-level SELECT), so a new column is unreadable
-- by default; say it anyway so a later "grant select on profiles" can't be the thing that leaks it.
revoke select (phone_hash) on public.profiles from public, anon, authenticated;

-- 3. Only set_my_phone() writes it (it sets tc.phone_write for its own transaction). Server jobs
--    (no JWT) are not stopped.
create or replace function public.profiles_phone_hash_guard() returns trigger
language plpgsql set search_path = '' as $$
begin
  if auth.uid() is null or coalesce(current_setting('tc.phone_write', true), '') = '1' then return new; end if;
  if (tg_op = 'INSERT' and new.phone_hash is not null)
     or (tg_op = 'UPDATE' and new.phone_hash is distinct from old.phone_hash) then
    raise exception 'Use Settings to change your phone number.' using errcode = '42501';
  end if;
  return new;
end $$;
drop trigger if exists profiles_phone_hash_guard on public.profiles;
create trigger profiles_phone_hash_guard before insert or update on public.profiles
  for each row execute function public.profiles_phone_hash_guard();

-- 4. HMAC of a client hash with the Vault key (internal: nobody may call it).
create or replace function public.contacts_key(h text) returns text
language sql stable security definer set search_path = '' as $$
  select encode(extensions.hmac(lower(h), s.decrypted_secret, 'sha256'), 'hex')
    from vault.decrypted_secrets s where s.name = 'contact_pepper' limit 1
$$;
revoke all on function public.contacts_key(text) from public, anon, authenticated;

-- 5. One rate check for both RPCs (internal).
create or replace function public.contacts_rate(me uuid, per_hour int, per_day int) returns void
language plpgsql security definer set search_path = '' as $$
declare nh int; nd int;
begin
  perform pg_advisory_xact_lock(hashtext('rate:contacts:' || me::text));
  select count(*) filter (where at > now() - interval '1 hour'), count(*) into nh, nd
    from public.rate_log where user_id = me and bucket = 'contacts' and at > now() - interval '1 day';
  if nh >= per_hour or nd >= per_day then
    raise exception 'You''re doing that too fast. Try again a bit later.' using errcode = 'P0001';
  end if;
  insert into public.rate_log (user_id, bucket) values (me, 'contacts');
end $$;
revoke all on function public.contacts_rate(uuid, int, int) from public, anon, authenticated;

-- 6. Match.
create or replace function public.match_contacts(hashes text[])
returns table (id uuid, display_name text, username text, avatar_url text, matched text[])
language plpgsql volatile security definer set search_path = '' as $$
declare me uuid := auth.uid(); pep text;
begin
  if me is null then raise exception 'Sign in first.' using errcode = '42501'; end if;
  if hashes is null or cardinality(hashes) = 0 then return; end if;
  if cardinality(hashes) > 2000 then raise exception 'Send at most 2000 at a time.' using errcode = '54000'; end if;
  perform public.contacts_rate(me, 20, 60);
  select s.decrypted_secret into pep from vault.decrypted_secrets s where s.name = 'contact_pepper' limit 1;
  return query
  with h as (select distinct lower(x) as hx from unnest(hashes) as x where x ~* '^[0-9a-f]{64}$'),
  hits as (
    select p.id as pid, h.hx from h
      join public.profiles p on pep is not null and p.phone_hash = encode(extensions.hmac(h.hx, pep, 'sha256'), 'hex')
    union
    select u.id, h.hx from h
      join auth.users u on encode(extensions.digest(lower(btrim(u.email::text)), 'sha256'), 'hex') = h.hx
  )
  select p.id, p.display_name, p.username, p.avatar_url, array_agg(distinct hits.hx order by hits.hx)
    from hits
    join public.profiles p on p.id = hits.pid
    join auth.users u on u.id = p.id
   where p.id <> me
     and u.deleted_at is null and (u.banned_until is null or u.banned_until < now())
     and p.school = public.my_school()
     and public.is_demo(p.id) = public.is_demo(me)
     and not public.is_pending_deletion(p.id)
     and not public.blocked_between(me, p.id)
     and not exists (select 1 from public.suspensions s where s.user_id = p.id and (s.until is null or s.until > now()))
   group by p.id, p.display_name, p.username, p.avatar_url
   order by p.display_name nulls last
   limit 500;
end $$;

-- 7. My own number: set (a 64-hex sha256 of my E.164 number) or clear ('' / null).
create or replace function public.set_my_phone(p_hash text) returns boolean
language plpgsql volatile security definer set search_path = '' as $$
declare me uuid := auth.uid(); h text := lower(btrim(coalesce(p_hash, ''))); k text;
begin
  if me is null then raise exception 'Sign in first.' using errcode = '42501'; end if;
  perform set_config('tc.phone_write', '1', true);
  if h = '' then
    update public.profiles set phone_hash = null where profiles.id = me;
    return false;
  end if;
  if h !~ '^[0-9a-f]{64}$' then raise exception 'That doesn''t look like a phone number.' using errcode = '22023'; end if;
  perform public.contacts_rate(me, 10, 30);
  k := public.contacts_key(h);
  if k is null then raise exception 'Contact matching isn''t set up yet.' using errcode = 'P0001'; end if;
  if exists (select 1 from public.profiles p where p.phone_hash = k and p.id <> me) then
    raise exception 'That number is already on another TermChamp account.' using errcode = '23505';
  end if;
  update public.profiles set phone_hash = k where profiles.id = me;
  if not found then raise exception 'Finish setting up your profile first.' using errcode = 'P0002'; end if;
  return true;
end $$;

create or replace function public.my_phone_saved() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce((select p.phone_hash is not null from public.profiles p where p.id = auth.uid()), false)
$$;

revoke all on function public.match_contacts(text[]) from public, anon;
revoke all on function public.set_my_phone(text) from public, anon;
revoke all on function public.my_phone_saved() from public, anon;
grant execute on function public.match_contacts(text[]) to authenticated;
grant execute on function public.set_my_phone(text) to authenticated;
grant execute on function public.my_phone_saved() to authenticated;
-- Supabase's default privileges also hand new functions to anon/authenticated directly:
revoke execute on function public.profiles_phone_hash_guard() from public, anon, authenticated;

commit;

-- Self-check (read-only): expect anon=false for all three, authenticated=true, phone_hash not selectable.
-- select f, has_function_privilege('anon', f, 'execute') anon, has_function_privilege('authenticated', f, 'execute') authd
--   from unnest(array['public.match_contacts(text[])','public.set_my_phone(text)','public.my_phone_saved()',
--                     'public.contacts_key(text)','public.contacts_rate(uuid,integer,integer)']) f;
-- select has_column_privilege('authenticated', 'public.profiles', 'phone_hash', 'select') must_be_false;

-- Undo (destructive, run by hand):
-- drop function if exists public.match_contacts(text[]); drop function if exists public.set_my_phone(text);
-- drop function if exists public.my_phone_saved(); drop function if exists public.contacts_key(text);
-- drop function if exists public.contacts_rate(uuid, int, int);
-- drop trigger if exists profiles_phone_hash_guard on public.profiles; drop function if exists public.profiles_phone_hash_guard();
-- drop index if exists public.profiles_phone_hash_uniq; alter table public.profiles drop constraint if exists profiles_phone_hash_shape;
-- alter table public.profiles drop column if exists phone_hash;
