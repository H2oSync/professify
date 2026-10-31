-- =================================================================================================
-- 99-rollback.sql — undoes 01 and 03. (02 only closed stale rows; there is nothing to undo.)
-- Restores push_enqueue and push_cleanup to their production text as read on 2026-10-30.
-- =================================================================================================
begin;

delete from public.push_config where key = 'web_function_url';

drop function if exists public.push_web_kick_due();
drop function if exists public.push_web_claim_subs(integer);
drop function if exists public.push_web_expire();

create or replace function public.push_cleanup()
returns void language sql security definer set search_path to 'public'
as $function$
delete from public.push_queue where created_at < now() - interval '7 days' and kind in ('dm', 'group', 'like');
delete from public.push_queue where created_at < now() - interval '400 days';
$function$;

drop function if exists public.push_web_max_age(text);

create or replace function public.push_enqueue(p_user uuid, p_kind text, p_title text, p_body text,
                                               p_url text, p_tag text, p_dedupe text)
returns boolean language plpgsql security definer set search_path to 'public'
as $function$
declare
  pref     public.push_prefs%rowtype;
  want     boolean;
  local_ts timestamp;
  fire_at  timestamptz;
begin
  if p_user is null or p_kind is null or p_dedupe is null then return false; end if;
  select * into pref from public.push_prefs where user_id = p_user;
  if not found then
    pref.seats := true; pref.friends := false; pref.quiet_from := 22; pref.quiet_to := 8;
  end if;
  want := case
            when p_kind in ('seat_open','waitlist','moved','dropped') then pref.seats
            when p_kind = 'free'                                      then pref.friends
            else false
          end;
  if not want then return false; end if;
  if coalesce(pref.prefs ->> p_kind, '') = 'false' then return false; end if;
  local_ts := now() at time zone 'America/Los_Angeles';
  fire_at := coalesce(public.push_fire_at(local_ts, pref.quiet_from, pref.quiet_to), now());
  insert into public.push_outbox(user_id, kind, title, body, url, tag, dedupe_key, send_after)
  values (p_user, p_kind, left(p_title,120), left(p_body,200),
          coalesce(nullif(left(p_url,200),''),'/'), left(p_tag,80), left(p_dedupe,200), fire_at)
  on conflict (user_id, dedupe_key) do nothing;
  return found;
end;
$function$;

commit;
