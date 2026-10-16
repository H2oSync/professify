-- =================================================================================================
-- TermChamp security, pass 2 — 2026-10-15 (from the post-fix catalog taken 01:21 UTC)
--
-- Run AFTER professify-security-hotfix-2026-10-14.sql. One transaction: if any check fails, nothing
-- changes. Safe to run twice. It touches no student data except: realtime publication membership,
-- and (only for reviews) the derived `helpful` counter, rebuilt from real votes (there are 0 today).
--
-- What it closes (details: claude/security-review-2026-10-14.md, "Pass 2"):
--   1. Rate limits that one request could bypass. The old limits counted rows with count(*) inside
--      the policy: a single bulk insert (rows don't see each other), or delete-and-re-insert, beat
--      them. A server-side counter (rate_log) now meters friend requests, messages, new chats,
--      chat adds, reports, professor suggestions, reviews, helpful votes, suggestion dismissals and
--      class rows. Old policies stay as a second wall.
--   2. created_at can't be changed after insert by a student (upsert-update path), and conversations
--      can only have their title changed (no pinning a thread to the top, no flipping kind).
--   3. Sign-ups: only school emails (calpoly / sdsu / ucsb .edu, incl. subdomains like the App
--      Review demo) can create or switch to an account, enforced in the database for every sign-in
--      method (email code AND the Google button).
--   4. The App Review demo accounts are walled off from real students in RLS (profiles, friend
--      requests) and in every people function, not only in two of them.
--   5. Block = gone everywhere: search, handle lookup, invite lookup, suggestions all skip anyone on
--      either side of a block; blocking also removes the blocked person from your 1-on-1 chats; and
--      1-on-1 messages need an active friendship (an ex-friend can't keep messaging you).
--   6. Classmate suggestions can't be farmed by planting fake classes: my_sections / saved_classes
--      only accept real catalog codes (Cal Poly) and are capped per student (60 / 120; today's max
--      is 30 / 39); search escapes % and _.
--   7. Storage: nobody can list the avatars bucket any more (it exposed every student's user id);
--      avatar files must be exactly <your id>/avatar.jpg; schedule cards need a school account and
--      are capped at 40 a day.
--   8. avatar_url can only point at TermChamp's own avatars bucket (no tracking pixels).
--   9. Realtime no longer broadcasts class_history / groups / group_members / sprint_progress
--      (Realtime DELETE events skip RLS and would carry who dropped which class).
--  10. review_helpful: votes are private (you see your own votes, and the votes on your own reviews
--      as a count source); you can't vote on your own or a removed review; the public helpful
--      count is now maintained by the server from real votes.
--  11. Reviews: difficulty / teach_ability must be 1-5, tags at most 12; friends no longer see a
--      review a moderator removed.
--  12. Reports: the reported person on a review report is set by the server (the review's author),
--      and a message report must point at a message in a chat you're in (no framing).
--  13. Message slur filter now covers every message kind, not only plain text.
--  14. Oracles: is_suspended answers only about yourself (moderators and server jobs see all);
--      the waitlist no longer reveals whether an email is already on it.
--  15. Grants: anon keeps only the handful of functions the signed-out site uses; nobody gets
--      TRUNCATE/TRIGGER/REFERENCES; new functions/tables are no longer auto-granted to anon.
--  16. Account emails: at most 3 account emails (deletion requested/cancelled) per student per day;
--      a report flood can't bury real report alerts (5 alerts per reporter per hour).
-- =================================================================================================

begin;

-- ---------- 0. Drift guard ----------------------------------------------------------------------
do $$
begin
  if to_regprocedure('public.sec_stamp_insert()') is null then
    raise exception 'VERIFY AGAINST LIVE: run professify-security-hotfix-2026-10-14.sql first';
  end if;
  if position('sec-hotfix-2026-10-14' in (select prosrc from pg_proc where oid='public.blocked_between(uuid,uuid)'::regprocedure)) = 0 then
    raise exception 'VERIFY AGAINST LIVE: blocked_between is not the hotfix version';
  end if;
  if to_regprocedure('public.wf_slur_guard_message()') is null
     or position('<> ''text''' in (select prosrc from pg_proc where oid='public.wf_slur_guard_message()'::regprocedure)) = 0
     and position('sec-pass2' in (select prosrc from pg_proc where oid='public.wf_slur_guard_message()'::regprocedure)) = 0 then
    raise exception 'VERIFY AGAINST LIVE: wf_slur_guard_message changed since the review';
  end if;
end $$;

-- ---------- 1. Server-side rate meter -----------------------------------------------------------
create table if not exists public.rate_log (
  user_id uuid        not null,
  bucket  text        not null,
  at      timestamptz not null default now()
);
create index if not exists rate_log_user_bucket_at on public.rate_log (user_id, bucket, at);
alter table public.rate_log enable row level security;          -- no policies: server only
revoke all on public.rate_log from public, anon, authenticated;

-- TG_ARGV: bucket, max, window, mode ('raise' | 'skip'), who ('auth' = auth.uid() | column name)
create or replace function public.sec_rate_limit()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  b    text     := TG_ARGV[0];
  lim  int      := TG_ARGV[1]::int;
  win  interval := TG_ARGV[2]::interval;
  mode text     := coalesce(TG_ARGV[3], 'raise');
  who  uuid     := auth.uid();
  n    int;
begin
  -- Server jobs and the SQL editor have no student behind them.
  if who is null then return new; end if;
  perform pg_advisory_xact_lock(hashtext('rate:' || b || ':' || who::text));
  select count(*) into n from public.rate_log
   where user_id = who and bucket = b and at > now() - win;
  if n >= lim then
    if mode = 'skip' then return null; end if;
    raise exception 'You''re doing that too fast. Try again a bit later.' using errcode = 'P0001';
  end if;
  insert into public.rate_log (user_id, bucket) values (who, b);
  if random() < 0.01 then
    delete from public.rate_log where at < now() - interval '2 days';
  end if;
  return new;
end $function$;
revoke execute on function public.sec_rate_limit() from public, anon, authenticated;

do $$
declare r record;
begin
  for r in select * from (values
      ('friend_requests',              'friend_request', 40,  '1 day',  'raise'),
      ('messages',                     'message_h',      200, '1 hour', 'raise'),
      ('conversations',                'conversation',   20,  '1 day',  'raise'),
      ('conversation_members',         'chat_add',       100, '1 day',  'raise'),
      ('reports',                      'report',         10,  '1 hour', 'raise'),
      ('professor_suggestions',        'suggestion',     20,  '1 day',  'raise'),
      ('reviews',                      'review',         30,  '1 day',  'raise'),
      ('review_helpful',               'helpful',        200, '1 day',  'raise'),
      ('friend_suggestion_dismissals', 'dismiss',        100, '1 day',  'raise'),
      ('my_sections',                  'my_section',     200, '1 day',  'raise'),
      ('saved_classes',                'saved_class',    400, '1 day',  'raise'),
      ('class_history',                'history',        600, '1 day',  'raise'),
      ('account_emails',               'account_email',  3,   '1 day',  'skip'),
      ('report_alerts',                'report_alert',   5,   '1 hour', 'skip')
    ) v(t, b, lim, win, mode)
  loop
    if to_regclass('public.' || r.t) is not null then
      execute format('drop trigger if exists sec_rate_limit on public.%I', r.t);
      execute format('create trigger sec_rate_limit before insert on public.%I for each row execute function public.sec_rate_limit(%L, %L, %L, %L)',
                     r.t, r.b, r.lim::text, r.win, r.mode);
    end if;
  end loop;
end $$;

-- ---------- 2. Timestamps and conversation columns ----------------------------------------------
create or replace function public.sec_stamp_insert()
 returns trigger
 language plpgsql
 set search_path to 'public'
as $function$
begin
  -- sec-pass2: fail closed — anything that is not a server role is treated as a student.
  if current_user not in ('postgres', 'service_role', 'supabase_admin') then
    if tg_op = 'INSERT' then
      new.created_at := now();
      if tg_table_name = 'reviews' then
        new.helpful    := 0;
        new.removed_at := null;
        new.removed_by := null;
        new.edited_at  := null;
      elsif tg_table_name = 'reports' then
        new.action_taken := null;
        new.resolved_at  := null;
      end if;
    else
      new.created_at := old.created_at;
    end if;
  end if;
  return new;
end $function$;
revoke execute on function public.sec_stamp_insert() from public, anon, authenticated;

do $$
declare t text;
begin
  foreach t in array array['messages','friend_requests','reports','professor_suggestions','reviews'] loop
    if to_regclass('public.' || t) is not null then
      execute format('drop trigger if exists sec_stamp_insert on public.%I', t);
      execute format('create trigger sec_stamp_insert before insert or update on public.%I for each row execute function public.sec_stamp_insert()', t);
    end if;
  end loop;
end $$;

create or replace function public.sec_reviews_keep_helpful()
 returns trigger
 language plpgsql
 set search_path to 'public'
as $function$
begin
  if current_user not in ('postgres', 'service_role', 'supabase_admin') then
    new.helpful := old.helpful;
  end if;
  return new;
end $function$;

revoke update on public.conversations from public, anon, authenticated;
grant update (title) on public.conversations to authenticated;

-- ---------- 3. Sign-ups only with a school email ------------------------------------------------
create or replace function public.sec_auth_school_email()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
begin
  -- sec-pass2: every way in (email code, Google) creates or updates auth.users; only school
  -- addresses TermChamp serves may do so. Existing accounts are untouched until their email changes.
  if new.email is null or public.school_from_email(new.email) is null then
    raise exception 'TermChamp is for students — sign in with your school email.' using errcode = 'P0001';
  end if;
  return new;
end $function$;
revoke execute on function public.sec_auth_school_email() from public, anon, authenticated;
do $$ begin
  execute 'drop trigger if exists sec_auth_school_email on auth.users';
  execute 'create trigger sec_auth_school_email before insert or update of email on auth.users for each row execute function public.sec_auth_school_email()';
exception when insufficient_privilege then
  raise warning 'sign-up gate: this project does not allow triggers on auth.users — set the same rule as a "Before user created" Auth hook instead (see the review doc).';
end $$;

-- ---------- 4. Demo wall in RLS ------------------------------------------------------------------
drop policy if exists "sec demo wall" on public.profiles;
create policy "sec demo wall" on public.profiles as restrictive for select to authenticated
  using (id = auth.uid() or public.is_moderator() or public.is_demo(id) = public.is_demo(auth.uid()));
drop policy if exists "sec demo wall" on public.friend_requests;
create policy "sec demo wall" on public.friend_requests as restrictive for insert to authenticated
  with check (public.is_demo(to_user) = public.is_demo(auth.uid()));

-- ---------- 5. People functions: school, demo and block walls everywhere -------------------------
create or replace function public.search_people__incl_pending(q text)
 returns table(id uuid, display_name text, instagram_handle text)
 language sql
 security definer
 set search_path to 'public'
as $function$
  -- sec-pass2: % and _ are matched literally.
  with s as (select replace(replace(replace(btrim(coalesce(q,'')), '\', '\\'), '%', '\%'), '_', '\_') as pat,
                    lower(btrim(coalesce(q,''))) as em)
  select p.id, p.display_name, p.instagram_handle
  from public.profiles p, s
  where btrim(coalesce(q,'')) <> ''
    and length(btrim(q)) >= 2
    and p.id <> auth.uid()
    and p.school = public.my_school()                 -- the wall
    and (
      p.display_name ilike '%' || s.pat || '%'
      or lower(p.edu_email) = s.em
    )
  order by (lower(p.edu_email) = s.em) desc, p.display_name asc
  limit 15;
$function$;

create or replace function public.search_people(q text)
 returns table(id uuid, display_name text, instagram_handle text)
 language sql security definer set search_path to 'public'
as $function$select x.* from public.search_people__incl_pending(q) x
  where not public.is_pending_deletion(x.id)
    and not public.blocked_between(auth.uid(), x.id)
    and public.is_demo(x.id) = public.is_demo(auth.uid())$function$;

create or replace function public.find_profile_by_handle(handle text)
 returns table(id uuid, display_name text, instagram_handle text)
 language sql security definer set search_path to 'public'
as $function$select x.* from public.find_profile_by_handle__incl_pending(handle) x
  where not public.is_pending_deletion(x.id)
    and not public.blocked_between(auth.uid(), x.id)
    and public.is_demo(x.id) = public.is_demo(auth.uid())$function$;

create or replace function public.get_inviter(ref uuid)
 returns table(display_name text)
 language sql stable security definer set search_path to 'public'
as $function$select x.* from public.get_inviter__incl_pending(ref) x
  where not public.is_pending_deletion(ref)
    and not public.blocked_between(auth.uid(), ref)
    and public.is_demo(ref) = public.is_demo(auth.uid())$function$;

create or replace function public.suggest_classmates()
 returns table(id uuid, display_name text, overlap bigint)
 language sql stable security definer set search_path to 'public'
as $function$select x.* from public.suggest_classmates__incl_pending() x
  where not public.is_pending_deletion(x.id)
    and not public.blocked_between(auth.uid(), x.id)
    and public.is_demo(x.id) = public.is_demo(auth.uid())$function$;

create or replace function public.suggest_classmates_v2()
 returns table(id uuid, display_name text, username text, avatar_url text, overlap integer, codes text[])
 language sql stable security definer set search_path to 'public'
as $function$select x.* from public.suggest_classmates_v2__incl_pending() x
  where not public.is_pending_deletion(x.id)
    and public.is_demo(x.id) = public.is_demo(auth.uid())$function$;

do $$
declare src text;
begin
  -- suggest_friends: add the block filter to the existing wrapper body, whatever its exact text.
  select prosrc into src from pg_proc where oid = 'public.suggest_friends__incl_pending(integer)'::regprocedure;
  if position('blocked_between' in src) = 0 then
    if position('and public.is_demo(s.id) = public.is_demo(auth.uid())' in src) = 0 then
      raise exception 'VERIFY AGAINST LIVE: suggest_friends__incl_pending body changed';
    end if;
    execute $f$
      create or replace function public.suggest_friends__incl_pending(p_limit integer default 6)
       returns table(id uuid, display_name text, username text, avatar_url text, reason text, mutuals integer, score integer, shared_codes text[])
       language sql stable security definer set search_path to 'public'
      as $b$
        select s.* from public.suggest_friends_unscoped(greatest(p_limit, 1) * 4) s
        where public.school_of(s.id) = public.my_school()
          and public.is_demo(s.id) = public.is_demo(auth.uid())
          and not public.blocked_between(auth.uid(), s.id)     -- sec-pass2
        limit greatest(p_limit, 1);
      $b$ $f$;
  end if;
end $$;

create or replace function public.friends_reviewed__incl_pending(p_professor_key text)
 returns table(id uuid, display_name text, username text, avatar_url text, score numeric, course text, created_at timestamp with time zone)
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  select p.id, p.display_name, p.username, p.avatar_url,
         r.score, r.course, r.created_at
  from public.reviews r
  join public.profiles p on p.id = r.user_id
  where r.professor_key = p_professor_key
    and r.share_with_friends
    and r.removed_at is null             -- sec-pass2: a removed review is gone for friends too
    and r.user_id <> auth.uid()
    and auth.uid() is not null
    and exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and (
          (fr.from_user = auth.uid() and fr.to_user = r.user_id) or
          (fr.to_user   = auth.uid() and fr.from_user = r.user_id)
        )
    )
  order by r.created_at desc
$function$;

drop policy if exists "friends read reviews shared with them" on public.reviews;
create policy "friends read reviews shared with them" on public.reviews for select to authenticated
  using (share_with_friends and removed_at is null and exists (
    select 1 from public.friend_requests fr
    where fr.status = 'accepted'
      and ((fr.from_user = auth.uid() and fr.to_user = reviews.user_id)
        or (fr.to_user = auth.uid() and fr.from_user = reviews.user_id))));

-- Blocking also ends your 1-on-1 chats with that person (you keep your copy; they lose access).
create or replace function public.block_user(p_target uuid)
 returns void
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'not signed in'; end if;
  if p_target is null or p_target = me then raise exception 'cannot block yourself'; end if;

  insert into public.blocks (blocker, blocked) values (me, p_target)
    on conflict (blocker, blocked) do nothing;

  -- Every edge between you, in either direction and at any stage.
  delete from public.friend_requests
   where (from_user = me and to_user = p_target)
      or (to_user = me and from_user = p_target);

  -- sec-pass2: the blocked person leaves every direct conversation they share with you.
  delete from public.conversation_members cm
   using public.conversations c
   where c.id = cm.conversation_id and c.kind = 'direct'
     and cm.user_id = p_target
     and exists (select 1 from public.conversation_members mine
                  where mine.conversation_id = c.id and mine.user_id = me);

  -- And stop suggesting them back to you tomorrow.
  begin
    insert into public.friend_suggestion_dismissals (user_id, dismissed_id)
    values (me, p_target) on conflict do nothing;
  exception when others then null;  -- table shape varies; a block must not fail over a nicety
  end;
end $function$;

-- 1-on-1 messages need an active friendship with the other person.
create or replace function public.sec_can_send_to(p_conv uuid)
 returns boolean
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  select auth.uid() is not null and (
    not exists (select 1 from public.conversations c where c.id = p_conv and c.kind = 'direct')
    or exists (
      select 1 from public.conversation_members cm
      join public.friend_requests fr on fr.status = 'accepted'
        and ((fr.from_user = auth.uid() and fr.to_user = cm.user_id)
          or (fr.to_user = auth.uid() and fr.from_user = cm.user_id))
      where cm.conversation_id = p_conv and cm.user_id <> auth.uid()));
$function$;
revoke execute on function public.sec_can_send_to(uuid) from public, anon;
grant execute on function public.sec_can_send_to(uuid) to authenticated;
drop policy if exists "sec direct needs friendship" on public.messages;
create policy "sec direct needs friendship" on public.messages as restrictive for insert to authenticated
  with check (public.sec_can_send_to(conversation_id));

-- ---------- 6. Real classes only, and a sane number of them -------------------------------------
create or replace function public.sec_class_rows_guard()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare me uuid := auth.uid(); n int; cap int := TG_ARGV[0]::int;
begin
  if me is null then return new; end if;
  if tg_op = 'INSERT' or new.code is distinct from old.code then
    if public.my_school() = 'calpoly'
       and not exists (select 1 from public.course_catalog c where c.course_code = new.code)
       and not exists (select 1 from public.course_seats  c where c.course_code = new.code) then
      raise exception 'That isn''t a class in the catalog.' using errcode = 'P0001';
    end if;
  end if;
  if tg_op = 'INSERT' then
    perform pg_advisory_xact_lock(hashtext('rows:' || tg_table_name || ':' || me::text));
    execute format('select count(*) from public.%I where user_id = $1', tg_table_name) into n using me;
    if n >= cap then
      raise exception 'That''s more classes than TermChamp keeps for one student.' using errcode = 'P0001';
    end if;
  end if;
  return new;
end $function$;
revoke execute on function public.sec_class_rows_guard() from public, anon, authenticated;
drop trigger if exists sec_class_rows_guard on public.my_sections;
create trigger sec_class_rows_guard before insert or update of code on public.my_sections
  for each row execute function public.sec_class_rows_guard('60');
drop trigger if exists sec_class_rows_guard on public.saved_classes;
create trigger sec_class_rows_guard before insert or update of code on public.saved_classes
  for each row execute function public.sec_class_rows_guard('120');

-- ---------- 7. Storage (each step tolerant: if the project forbids it, a warning says so) ------
create or replace function public.sec_cards_today()
 returns integer
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  select count(*)::int from storage.objects
   where bucket_id = 'schedule-cards' and owner = auth.uid() and created_at > now() - interval '1 day';
$function$;
revoke execute on function public.sec_cards_today() from public, anon;
grant execute on function public.sec_cards_today() to authenticated;

-- The public bucket still serves every photo by its exact URL; this policy only allowed LISTING.
do $st$ begin
  execute $q$drop policy if exists "avatars are publicly readable" on storage.objects$q$;
  execute $q$drop policy if exists "own avatar read" on storage.objects$q$;
exception when insufficient_privilege then
  raise warning 'storage: could not drop the avatar listing policy';
end $st$;
do $st$ begin
  execute $q$create policy "own avatar read" on storage.objects for select to authenticated
  using (bucket_id = 'avatars' and name = (auth.uid())::text || '/avatar.jpg')$q$;
exception when insufficient_privilege then
  raise warning 'storage: could not run: create policy "own avatar read" on storage.objects for select to authenticated';
end $st$;
do $st$ begin
  execute $q$alter policy "own avatar insert" on storage.objects
  with check (bucket_id = 'avatars' and name = (auth.uid())::text || '/avatar.jpg')$q$;
exception when insufficient_privilege then
  raise warning 'storage: could not run: alter policy "own avatar insert" on storage.objects';
end $st$;
do $st$ begin
  execute $q$alter policy "own avatar update" on storage.objects
  using (bucket_id = 'avatars' and name = (auth.uid())::text || '/avatar.jpg')
  with check (bucket_id = 'avatars' and name = (auth.uid())::text || '/avatar.jpg')$q$;
exception when insufficient_privilege then
  raise warning 'storage: could not run: alter policy "own avatar update" on storage.objects';
end $st$;
do $st$ begin
  execute $q$alter policy "own avatar delete" on storage.objects
  using (bucket_id = 'avatars' and name = (auth.uid())::text || '/avatar.jpg')$q$;
exception when insufficient_privilege then
  raise warning 'storage: could not run: alter policy "own avatar delete" on storage.objects';
end $st$;
do $st$ begin
  execute $q$alter policy "schedule card insert" on storage.objects
  with check (bucket_id = 'schedule-cards'
              and name ~ '^[0-9a-f]{32}\.(png|json)$'
              and public.my_school() is not null
              and public.sec_cards_today() < 40)$q$;
exception when insufficient_privilege then
  raise warning 'storage: could not run: alter policy "schedule card insert" on storage.objects';
end $st$;

-- ---------- 8. avatar_url only from our bucket --------------------------------------------------
alter table public.profiles drop constraint if exists profiles_avatar_url_ours;
alter table public.profiles add constraint profiles_avatar_url_ours check (
  avatar_url is null or avatar_url = '' or avatar_url ~ '^https://rqkndeqbcahozidniesn\.supabase\.co/storage/v1/object/public/avatars/[0-9a-f-]{36}/avatar\.jpg(\?[A-Za-z0-9=&._-]{0,64})?$'
) not valid;
do $$ begin
  if not exists (select 1 from public.profiles where not (avatar_url is null or avatar_url = '' or avatar_url ~ '^https://rqkndeqbcahozidniesn\.supabase\.co/storage/v1/object/public/avatars/[0-9a-f-]{36}/avatar\.jpg(\?[A-Za-z0-9=&._-]{0,64})?$')) then
    alter table public.profiles validate constraint profiles_avatar_url_ours;
  else
    raise warning 'profiles_avatar_url_ours: some existing avatar_url values are off-bucket; guard is on for new writes only';
  end if;
end $$;

-- ---------- 9. Realtime: stop broadcasting tables whose DELETE events leak ----------------------
do $$
declare t text;
begin
  foreach t in array array['class_history','groups','group_members','sprint_progress'] loop
    if exists (select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename=t) then
      execute format('alter publication supabase_realtime drop table public.%I', t);
    end if;
  end loop;
end $$;
drop policy if exists sprint_read on public.sprint_progress;
drop policy if exists sprint_ins  on public.sprint_progress;
drop policy if exists sprint_upd  on public.sprint_progress;
drop policy if exists sprint_del  on public.sprint_progress;

-- ---------- 10. Helpful votes -------------------------------------------------------------------
drop policy if exists rh_select_all on public.review_helpful;
drop policy if exists "sec helpful read" on public.review_helpful;
create or replace function public.sec_is_my_review(p_review uuid)
 returns boolean
 language sql stable security definer set search_path to 'public'
as $function$
  select auth.uid() is not null and exists (select 1 from public.reviews r where r.id = p_review and r.user_id = auth.uid());
$function$;
revoke execute on function public.sec_is_my_review(uuid) from public, anon;
grant execute on function public.sec_is_my_review(uuid) to authenticated;
create policy "sec helpful read" on public.review_helpful for select to authenticated
  using (voter_id = auth.uid() or public.sec_is_my_review(review_id));
create or replace function public.sec_helpful_ok(p_review uuid)
 returns boolean
 language sql stable security definer set search_path to 'public'
as $function$
  select auth.uid() is not null and public.my_school() is not null
     and exists (select 1 from public.reviews r
                  where r.id = p_review and r.removed_at is null and r.user_id is distinct from auth.uid());
$function$;
revoke execute on function public.sec_helpful_ok(uuid) from public, anon;
grant execute on function public.sec_helpful_ok(uuid) to authenticated;
drop policy if exists "sec helpful vote" on public.review_helpful;
create policy "sec helpful vote" on public.review_helpful as restrictive for insert to authenticated
  with check (public.sec_helpful_ok(review_id));

create or replace function public.sec_helpful_count()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare rid uuid := coalesce(new.review_id, old.review_id);
begin
  update public.reviews r
     set helpful = (select count(*) from public.review_helpful h where h.review_id = rid)
   where r.id = rid;
  return null;
end $function$;
revoke execute on function public.sec_helpful_count() from public, anon, authenticated;
drop trigger if exists sec_helpful_count on public.review_helpful;
create trigger sec_helpful_count after insert or delete on public.review_helpful
  for each row execute function public.sec_helpful_count();
update public.reviews r set helpful = (select count(*) from public.review_helpful h where h.review_id = r.id)
 where coalesce(r.helpful, 0) <> (select count(*) from public.review_helpful h where h.review_id = r.id);

-- ---------- 11. Review value checks -------------------------------------------------------------
alter table public.reviews drop constraint if exists reviews_ratings_range;
alter table public.reviews add constraint reviews_ratings_range check (
  (difficulty is null or (difficulty >= 1 and difficulty <= 5))
  and (teach_ability is null or (teach_ability >= 1 and teach_ability <= 5))
  and (tags is null or cardinality(tags) <= 12)
) not valid;
do $$ begin
  if not exists (select 1 from public.reviews where not (
       (difficulty is null or (difficulty >= 1 and difficulty <= 5))
       and (teach_ability is null or (teach_ability >= 1 and teach_ability <= 5))
       and (tags is null or cardinality(tags) <= 12))) then
    alter table public.reviews validate constraint reviews_ratings_range;
  end if;
end $$;

-- ---------- 12. Reports carry the truth ---------------------------------------------------------
create or replace function public.sec_report_facts()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare m record;
begin
  if auth.uid() is null then return new; end if;
  if new.kind = 'review' then
    select r.user_id into new.target_user from public.reviews r where r.id::text = new.target_id;
  elsif new.kind = 'message' then
    select msg.sender, msg.body into m from public.messages msg
     where msg.id::text = new.target_id
       and exists (select 1 from public.conversation_members cm
                    where cm.conversation_id = msg.conversation_id and cm.user_id = auth.uid());
    if not found then
      raise exception 'That message isn''t in one of your chats.' using errcode = 'P0001';
    end if;
    new.target_user := m.sender;
    if m.body is not null and m.body <> '' then
      new.note := left(m.body, 2000);
    end if;
  end if;
  return new;
end $function$;
revoke execute on function public.sec_report_facts() from public, anon, authenticated;
drop trigger if exists sec_report_facts on public.reports;
create trigger sec_report_facts before insert on public.reports
  for each row execute function public.sec_report_facts();

-- ---------- 13. Slur filter on every message kind -----------------------------------------------
create or replace function public.wf_slur_guard_message()
 returns trigger
 language plpgsql
as $function$
begin
  -- sec-pass2: every kind (class / professor cards carry a body too and it reaches lock screens).
  if NEW.body is null or NEW.body = '' then return NEW; end if;
  if TG_OP = 'UPDATE' and NEW.body is not distinct from OLD.body then return NEW; end if;
  if public.wf_slur_hit(NEW.body) is not null then
    raise exception 'Messages can''t contain slurs. Change it and try again.' using errcode = 'P0001';
  end if;
  return NEW;
end $function$;

-- ---------- 14. Oracles --------------------------------------------------------------------------
create or replace function public.is_suspended(u uuid default null::uuid)
 returns boolean
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  -- sec-pass2: a student may only ask about themselves; moderators and server jobs about anyone.
  select case
    when auth.uid() is not null and coalesce(u, auth.uid()) <> auth.uid() and not public.is_moderator() then false
    else exists (
      select 1 from public.suspensions s
      where s.user_id = coalesce(u, auth.uid())
        and (s.until is null or s.until > now()))
  end;
$function$;

create or replace function public.sec_waitlist_quiet()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
begin
  if exists (select 1 from public.school_waitlist w where w.email = new.email) then
    return null;            -- already on it: succeed quietly, reveal nothing
  end if;
  return new;
end $function$;
revoke execute on function public.sec_waitlist_quiet() from public, anon, authenticated;
drop trigger if exists sec_waitlist_quiet on public.school_waitlist;
create trigger sec_waitlist_quiet before insert on public.school_waitlist
  for each row execute function public.sec_waitlist_quiet();

-- ---------- 15. Grants --------------------------------------------------------------------------
do $$
declare f record; keep_auth oid[] := '{}'; keep_svc oid[] := '{}';
begin
  -- Remember who may call what today, so revoking PUBLIC takes nothing away from signed-in students.
  select coalesce(array_agg(p.oid), '{}') into keep_auth from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and has_function_privilege('authenticated', p.oid, 'EXECUTE');
  select coalesce(array_agg(p.oid), '{}') into keep_svc from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and has_function_privilege('service_role', p.oid, 'EXECUTE');

  execute 'revoke execute on all functions in schema public from public, anon';

  for f in select p.oid from pg_proc p where p.oid = any(keep_auth) loop
    execute format('grant execute on function %s to authenticated', f.oid::regprocedure);
  end loop;
  for f in select p.oid from pg_proc p where p.oid = any(keep_svc) loop
    execute format('grant execute on function %s to service_role', f.oid::regprocedure);
  end loop;
end $$;

-- What the signed-out website and the anon waitlist really use.
grant execute on function public.log_events(jsonb)               to anon;
grant execute on function public.trending_profs(integer,integer) to anon;
grant execute on function public.school_from_email(text)         to anon;
grant execute on function public.get_inviter(uuid)               to anon;
grant execute on function public.my_school()                     to anon;
grant execute on function public.assistant_gate()                to anon;
grant execute on function public.why_cant_i_ask()                to anon;
grant execute on function public.why_cant_i_review()             to anon;
-- (Helpers they call run as the function owner, so anon needs nothing else — which also closes the
--  anon is_pending_deletion oracle.)

-- Sec functions stay server/authenticated only as set above.
revoke execute on function public.sec_rate_limit(), public.sec_stamp_insert(), public.sec_reviews_keep_helpful(),
  public.sec_auth_school_email(), public.sec_class_rows_guard(), public.sec_helpful_count(),
  public.sec_report_facts(), public.sec_waitlist_quiet() from authenticated;

revoke truncate, references, trigger on all tables in schema public from anon, authenticated;
do $$ begin
  execute 'revoke maintain on all tables in schema public from anon, authenticated';
exception when others then null;   -- MAINTAIN exists only on Postgres 17+
end $$;

alter default privileges for role postgres in schema public revoke execute on functions from anon;
alter default privileges for role postgres revoke execute on functions from public;
alter default privileges for role postgres in schema public revoke all on tables from anon;
alter default privileges for role postgres in schema public revoke all on sequences from anon;
alter default privileges for role postgres in schema public revoke truncate, references, trigger on tables from authenticated;

-- ---------- Self-checks -------------------------------------------------------------------------
do $$
declare n int;
begin
  if has_function_privilege('anon', 'public.search_people(text)', 'EXECUTE') then
    raise exception 'self-check: anon can still run search_people';
  end if;
  if not has_function_privilege('authenticated', 'public.search_people(text)', 'EXECUTE')
     or not has_function_privilege('authenticated', 'public.suggest_classmates_v2()', 'EXECUTE')
     or not has_function_privilege('authenticated', 'public.block_user(uuid)', 'EXECUTE')
     or not has_function_privilege('authenticated', 'public.friends_of(uuid)', 'EXECUTE') then
    raise exception 'self-check: students lost a function they use';
  end if;
  if not has_function_privilege('anon', 'public.log_events(jsonb)', 'EXECUTE')
     or not has_function_privilege('anon', 'public.trending_profs(integer,integer)', 'EXECUTE') then
    raise exception 'self-check: the signed-out site lost log_events / trending_profs';
  end if;
  if has_table_privilege('authenticated', 'public.messages', 'TRUNCATE') then
    raise exception 'self-check: TRUNCATE still granted';
  end if;
  if has_column_privilege('authenticated', 'public.conversations', 'last_at', 'UPDATE') then
    raise exception 'self-check: conversations.last_at still writable';
  end if;
  select count(*) into n from pg_policies where schemaname='storage' and tablename='objects' and policyname='avatars are publicly readable';
  if n > 0 then raise warning 'CHECK: avatar listing policy still there (storage step was not allowed)'; end if;
  if exists (select 1 from pg_publication_tables where pubname='supabase_realtime' and tablename in ('class_history','group_members')) then
    raise exception 'self-check: realtime still publishes class_history/group_members';
  end if;
  if not exists (select 1 from pg_trigger where tgname='sec_auth_school_email' and tgrelid='auth.users'::regclass) then
    raise warning 'CHECK: sign-up gate trigger not installed — use the Auth hook instead';
  end if;
  raise notice 'security pass 2: all self-checks passed';
end $$;

commit;

-- ROLLBACK NOTES: each section can be undone by dropping the sec_* trigger/policy it adds, or by
-- re-running the old function body from the 2026-10-15 01:21 catalog snapshot. The grants section
-- can be undone with: grant execute on all functions in schema public to anon;  (not advised)
