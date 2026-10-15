-- =================================================================================================
-- TermChamp security hotfix — 2026-10-14 (from the live-catalog review taken 22:42 UTC)
--
-- RUN THIS FIRST, before the three other professify-security-*.sql files. One transaction: if any
-- self-check at the bottom fails, nothing is changed. Safe to run twice.
--
-- What it closes (details in claude/security-review-2026-10-14.md):
--   1. CRITICAL  reviews_public is a definer view that anon and authenticated can INSERT/UPDATE/
--                DELETE through. With only the public key, anyone could delete or rewrite every
--                professor review (the view runs as its owner, so reviews RLS never applies).
--                -> revoke every write privilege on the view; SELECT stays, the apps only read it.
--   2. HIGH      find_profile_by_username(text) is executable by anon and has no school wall,
--                block check or sign-in check: a script can walk usernames and collect uuid, name,
--                avatar and Instagram handle for every student. Neither app calls it.
--                -> revoke execute from everyone but postgres/service_role.
--   3. HIGH      suggest_classmates_v2 has no school wall and no block check: it returns strangers
--                at ANY school with the exact course codes they're enrolled in.
--                -> same body plus the school wall and a both-ways block filter.
--   4. MEDIUM    sprint_progress (the old team sprint board; /sprint.html already redirects to /)
--                is readable and writable by anyone with the public key.
--                -> revoke all from anon and authenticated. The table and its rows stay.
--   5. MEDIUM    A member can re-point their own conversation_members / group_members row at any
--                other conversation or group (UPDATE was allowed on conversation_id / group_id).
--                -> students may update only last_read_at / seen_at, which is all either app does.
--   6. MEDIUM    Rate limits count rows by created_at, and the client could set created_at itself
--                (backdate = unlimited friend requests, messages, reports, reviews, suggestions;
--                future-date = a message pinned to the top of the inbox).
--                -> a BEFORE INSERT trigger sets created_at := now() for student sessions.
--                Reviews also get helpful=0 and no moderation fields on insert, and a student can
--                no longer change their own review's helpful count. Reports can't be pre-filled
--                with action_taken / resolved_at.
--   7. MEDIUM    profiles.edu_email was whatever the client sent. It decides search-by-email, the
--                App Review demo wall (is_demo) and friend_emails().
--                -> stamped from the signed-in email for student sessions (same rule the school
--                column already follows; both apps already send exactly this value).
--   8. MEDIUM    blocked_between(a,b) answered for any pair, so a student could learn who blocked
--                them and rebuild someone's block list.
--                -> a student session gets an answer only when it is one of the two people.
--                Every policy that calls it passes auth.uid() as one side; server jobs (no JWT)
--                are unaffected.
--   9. LOW       anon had full privileges on conversation_mutes (RLS still applied). Revoked.
--
-- Not in this file (need a product decision or a redeploy): see "Needs Tate's decision" in the
-- review doc. The assistant spend cap (incl. the NaN switch-off) is professify-security-assistant-
-- spend.sql — run it right after this one.
--
-- Rollback notes are at the very bottom.
-- =================================================================================================

begin;

-- ---------- 0. Drift guard: stop if production no longer looks like the 22:42 snapshot ----------
do $$
declare src text;
begin
  if to_regclass('public.reviews_public') is null then raise exception 'VERIFY AGAINST LIVE: reviews_public missing'; end if;
  if to_regprocedure('public.find_profile_by_username(text)') is null then raise notice 'find_profile_by_username(text) already gone — step 2 skipped'; end if;
  if to_regprocedure('public.suggest_classmates_v2__incl_pending()') is null then raise exception 'VERIFY AGAINST LIVE: suggest_classmates_v2__incl_pending() missing'; end if;
  select prosrc into src from pg_proc where oid = 'public.suggest_classmates_v2__incl_pending()'::regprocedure;
  if position('THE INTERSECTION' in src) = 0 and position('sec-hotfix-2026-10-14' in src) = 0 then
    raise exception 'VERIFY AGAINST LIVE: suggest_classmates_v2__incl_pending body changed since the review';
  end if;
  if to_regprocedure('public.blocked_between(uuid,uuid)') is null then raise exception 'VERIFY AGAINST LIVE: blocked_between(uuid,uuid) missing'; end if;
  if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='conversation_members' and column_name='last_read_at')
     then raise exception 'VERIFY AGAINST LIVE: conversation_members.last_read_at missing'; end if;
  if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='group_members' and column_name='seen_at')
     then raise exception 'VERIFY AGAINST LIVE: group_members.seen_at missing'; end if;
end $$;

-- ---------- 1. reviews_public: read-only for everyone -------------------------------------------
revoke insert, update, delete, truncate, references, trigger on public.reviews_public from public, anon, authenticated;
grant select on public.reviews_public to anon, authenticated;

-- ---------- 2. find_profile_by_username: server-only ---------------------------------------------
do $$ begin
  if to_regprocedure('public.find_profile_by_username(text)') is not null then
    revoke execute on function public.find_profile_by_username(text) from public, anon, authenticated;
    grant execute on function public.find_profile_by_username(text) to service_role;
  end if;
end $$;

-- ---------- 3. suggest_classmates_v2: same school, never across a block ---------------------------
create or replace function public.suggest_classmates_v2__incl_pending()
 returns table(id uuid, display_name text, username text, avatar_url text, overlap integer, codes text[])
 language sql
 stable security definer
 set search_path to 'public'
as $function$
-- sec-hotfix-2026-10-14: added the school wall (as every sibling has) and a both-ways block filter.
with me as (select auth.uid() as uid, public.my_school() as school),
-- Anyone already connected in either direction and at any stage. A pending request counts:
-- re-suggesting someone whose request is sitting in their inbox is the most confusing thing
-- this feature could do.
connected as (
  select case when r.from_user = m.uid then r.to_user else r.from_user end as other
  from public.friend_requests r, me m
  where (r.from_user = m.uid or r.to_user = m.uid)
    and r.status in ('accepted','pending')
),
my_codes as (
  select distinct s.code
  from public.my_sections s, me m
  where s.user_id = m.uid and s.code is not null
),
-- THE INTERSECTION, kept as codes rather than collapsed to a count. distinct so a lecture and
-- its lab logged under one code cannot make one shared class look like two.
hits as (
  select s.user_id as other, array_agg(distinct s.code order by s.code) as codes
  from public.my_sections s
  join my_codes k on k.code = s.code
  where s.user_id <> (select uid from me)
  group by 1
)
select p.id,
       coalesce(p.display_name,'Classmate') as display_name,
       p.username,
       p.avatar_url,
       cardinality(h.codes)::int as overlap,
       h.codes
from hits h
join public.profiles p on p.id = h.other
where (select school from me) is not null
  and p.school = (select school from me)                                   -- the wall
  and not exists (select 1 from public.blocks b                            -- never across a block
                  where (b.blocker = (select uid from me) and b.blocked = p.id)
                     or (b.blocker = p.id and b.blocked = (select uid from me)))
  and p.id not in (select other from connected)
  and p.id not in (select dismissed_id from public.friend_suggestion_dismissals
                   where user_id = (select uid from me))
order by cardinality(h.codes) desc, coalesce(p.display_name,'') asc
limit 12;
$function$;
revoke execute on function public.suggest_classmates_v2__incl_pending() from public, anon, authenticated;
grant execute on function public.suggest_classmates_v2__incl_pending() to service_role;

-- ---------- 4. sprint_progress: no client access -------------------------------------------------
do $$ begin
  if to_regclass('public.sprint_progress') is not null then
    revoke all on public.sprint_progress from public, anon, authenticated;
  end if;
end $$;

-- ---------- 5. memberships: students may only mark things read -----------------------------------
revoke update on public.conversation_members from public, anon, authenticated;
grant update (last_read_at) on public.conversation_members to authenticated;
revoke update on public.group_members from public, anon, authenticated;
grant update (seen_at) on public.group_members to authenticated;

-- ---------- 6. server clock for created_at (and review/report bookkeeping) -----------------------
create or replace function public.sec_stamp_insert()
 returns trigger
 language plpgsql
 set search_path to 'public'
as $function$
begin
  -- Only a student's own API session (PostgREST runs it as authenticated/anon). Definer routines,
  -- the service role and the SQL editor keep whatever they write.
  if current_user in ('authenticated', 'anon') then
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
      execute format('create trigger sec_stamp_insert before insert on public.%I for each row execute function public.sec_stamp_insert()', t);
    end if;
  end loop;
end $$;

create or replace function public.sec_reviews_keep_helpful()
 returns trigger
 language plpgsql
 set search_path to 'public'
as $function$
begin
  if current_user in ('authenticated', 'anon') then
    new.helpful := old.helpful;
  end if;
  return new;
end $function$;
revoke execute on function public.sec_reviews_keep_helpful() from public, anon, authenticated;
drop trigger if exists sec_reviews_keep_helpful on public.reviews;
create trigger sec_reviews_keep_helpful before update of helpful on public.reviews
  for each row execute function public.sec_reviews_keep_helpful();

-- ---------- 7. edu_email follows the signed-in email ---------------------------------------------
create or replace function public.profiles_stamp_edu_email()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare claims jsonb; em text;
begin
  begin
    claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  exception when others then
    claims := null;
  end;
  -- Same rule as profiles_stamp_school: a student token decides; the SQL editor / service role
  -- keep what they write. A student token with no email is left alone here (stamp_school already
  -- refuses it).
  if claims is not null and claims ->> 'role' = 'authenticated' then
    em := nullif(trim(claims ->> 'email'), '');
    if em is not null then
      new.edu_email := em;
    elsif tg_op = 'UPDATE' then
      new.edu_email := old.edu_email;
    else
      new.edu_email := null;
    end if;
  end if;
  return new;
end $function$;
revoke execute on function public.profiles_stamp_edu_email() from public, anon, authenticated;
drop trigger if exists profiles_stamp_edu_email on public.profiles;
create trigger profiles_stamp_edu_email before insert or update on public.profiles
  for each row execute function public.profiles_stamp_edu_email();

-- ---------- 8. blocked_between answers only about yourself --------------------------------------
create or replace function public.blocked_between(a uuid, b uuid)
 returns boolean
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  -- sec-hotfix-2026-10-14: a student session may only ask about pairs it is part of. Every policy
  -- passes auth.uid() as one side; server jobs have no JWT (auth.uid() is null) and see everything.
  select case
    when auth.uid() is not null and auth.uid() is distinct from a and auth.uid() is distinct from b then false
    else exists (
      select 1 from public.blocks
      where (blocker = a and blocked = b) or (blocker = b and blocked = a))
  end;
$function$;

-- ---------- 9. conversation_mutes: nothing for anon ---------------------------------------------
do $$ begin
  if to_regclass('public.conversation_mutes') is not null then
    revoke all on public.conversation_mutes from anon;
  end if;
end $$;

-- ---------- Self-checks (any failure rolls the whole file back) ---------------------------------
do $$
declare r text;
begin
  foreach r in array array['anon','authenticated'] loop
    if has_table_privilege(r, 'public.reviews_public', 'INSERT')
       or has_table_privilege(r, 'public.reviews_public', 'UPDATE')
       or has_table_privilege(r, 'public.reviews_public', 'DELETE') then
      raise exception 'self-check: % can still write reviews_public', r;
    end if;
    if not has_table_privilege(r, 'public.reviews_public', 'SELECT') then
      raise exception 'self-check: % lost SELECT on reviews_public (the apps read it)', r;
    end if;
    if to_regprocedure('public.find_profile_by_username(text)') is not null
       and has_function_privilege(r, 'public.find_profile_by_username(text)', 'EXECUTE') then
      raise exception 'self-check: % can still execute find_profile_by_username', r;
    end if;
    if to_regclass('public.sprint_progress') is not null
       and has_table_privilege(r, 'public.sprint_progress', 'SELECT') then
      raise exception 'self-check: % can still read sprint_progress', r;
    end if;
  end loop;
  if has_column_privilege('authenticated', 'public.conversation_members', 'conversation_id', 'UPDATE')
     or has_column_privilege('authenticated', 'public.group_members', 'group_id', 'UPDATE') then
    raise exception 'self-check: membership rows can still be re-pointed';
  end if;
  if not has_column_privilege('authenticated', 'public.conversation_members', 'last_read_at', 'UPDATE') then
    raise exception 'self-check: students can no longer mark a chat read';
  end if;
  if position('p.school = (select school from me)' in
       (select prosrc from pg_proc where oid = 'public.suggest_classmates_v2__incl_pending()'::regprocedure)) = 0 then
    raise exception 'self-check: classmates wall missing';
  end if;
  raise notice 'security hotfix 2026-10-14: all self-checks passed';
end $$;

commit;

-- =================================================================================================
-- ROLLBACK NOTES (only if something real breaks; each line undoes one step)
--   1. grant insert, update, delete on public.reviews_public to anon, authenticated;   -- NOT advised
--   2. grant execute on function public.find_profile_by_username(text) to anon, authenticated;
--   3. re-run the old body (kept in the review doc's appendix / the 22:42 catalog snapshot)
--   4. grant all on public.sprint_progress to anon, authenticated;
--   5. grant update on public.conversation_members, public.group_members to authenticated;
--   6. drop trigger sec_stamp_insert on public.<table>; drop trigger sec_reviews_keep_helpful on public.reviews;
--   7. drop trigger profiles_stamp_edu_email on public.profiles;
--   8. create or replace blocked_between with the plain exists(...) body
--   9. (nothing to restore)
-- =================================================================================================
