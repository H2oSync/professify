-- ================================================================================================
-- SCHOOLS — one database, several campuses, and a wall between them.        9 September 2026
-- ------------------------------------------------------------------------------------------------
-- Tate: "i dont want the app to be strictly cal poly ... for now UCSB and SDSU ... make sure cal
--        poly vs sdsu and ucsb students never are recommended for each other and don't cross over."
--
-- Until today the database had no idea what school anyone attends. It did not need to: sign-in was
-- locked to @calpoly.edu, so every row was Cal Poly by construction. Opening a second domain breaks
-- that construction, and "the client filters by school" is not a wall — a wall is something a
-- crafted request cannot climb. So the school lives on the profile, is DERIVED FROM THE VERIFIED
-- EMAIL on the server (the client cannot set it), and every surface where one student can find
-- another is fenced by it in SQL:
--
--   profiles       SELECT  — you read your own school (and anyone you are already connected to)
--   friend_requests INSERT — you can only send to your own school
--   search_people / find_profile_by_handle / get_inviter / suggest_classmates / friends_of
--                          — every discovery RPC returns your own school only
--
-- Chats, reviews-by-friends and professor suggestions inherit the wall: every one of them is gated
-- on an ACCEPTED FRIENDSHIP in its own policy or function (read off production 2026-09-09:
-- conversation_members INSERT requires is_friend_of(); friends_reviewed and professor_suggested_by
-- both require an accepted friend_requests row), and a request can no longer cross the wall — so
-- no cross-campus edge can be created, and nothing downstream of an edge can cross either.
-- Discovery is fenced first for exactly that reason.
--
-- What is NOT inherited and is fenced here explicitly: profiles SELECT, friend_requests INSERT,
-- the five discovery RPCs, and — if it ever exists — community_posts (the Quad). That table is not
-- on production today (checked 2026-09-09; the client's "Post your schedule" writes to nothing),
-- so its block below is guarded and a no-op until someone creates it.
--
-- HOW TO RUN: paste into the Supabase SQL editor as usual. The whole file is ONE TRANSACTION —
-- if any statement fails, nothing is applied, and the two shape-checks that can refuse to proceed
-- run before any change. Safe to run twice. Existing rows are stamped from their stored email
-- (all @calpoly.edu). Nothing is deleted.
--
-- Reviewed by a second model before it was called done. Its findings and what changed:
--   · the stamping trigger let a JWT WITHOUT an email claim (anonymous / phone sign-in, both off
--     today) write any school it liked → it now refuses any `authenticated` JWT that has no email;
--   · school_of(uuid) was callable by every student — a "does this id exist, and where" oracle for
--     any guessed uuid → EXECUTE revoked; the friend-request policy reads through the profiles
--     policy instead, which shows a student only their own campus anyway;
--   · no transaction, and the shape-check sat after the profiles policy had already changed →
--     BEGIN/COMMIT, checks first;
--   · school_from_email's pattern was anchored at the end only → anchored at both ends.
--
-- PROVEN LOCALLY before it touches production (check-schools.mjs → _schools-rls.sql): a UCSB user
-- searching for a Cal Poly student by name, by handle, by invite link, by shared section, and by
-- direct SELECT gets nothing; a friend request across the wall is refused by the policy; the same
-- queries within one school still work. Read that file if you want to see the wall being kicked.
-- ================================================================================================

begin;

-- ------------------------------------------------------------------------------------------------
-- 0. REFUSE TO PROCEED if the database is not the shape this file was written against. Both checks
--    run before anything changes, so a refusal leaves production exactly as it was.
-- ------------------------------------------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from pg_policies
   where schemaname='public' and tablename='friend_requests' and cmd='INSERT'
     and policyname <> 'fr_send_as_self';
  if n > 0 then
    raise exception 'friend_requests has % INSERT policy(ies) besides fr_send_as_self — look before running this', n;
  end if;
  if not exists (select 1 from pg_proc p join pg_namespace s on s.oid=p.pronamespace
                 where s.nspname='public' and p.proname in ('blocked_between','is_suspended','is_moderator')
                 group by s.nspname having count(distinct p.proname)=3) then
    raise exception 'blocked_between / is_suspended / is_moderator missing — this file recreates a policy that calls them';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 1. WHICH SCHOOL AN EMAIL BELONGS TO. Immutable, pure, and the only place the domain list lives.
--    A subdomain counts (my.calpoly.edu is Cal Poly). Anything else is NULL — "not a school we
--    serve" — which every caller below treats as "no access", never as a default.
-- ------------------------------------------------------------------------------------------------
create or replace function public.school_from_email(email text)
returns text
language sql
immutable
set search_path = public
as $$
  select case
    when email is null then null
    when lower(email) ~ '^[^@\s]+@([a-z0-9-]+\.)*calpoly\.edu$' then 'calpoly'
    when lower(email) ~ '^[^@\s]+@([a-z0-9-]+\.)*sdsu\.edu$'    then 'sdsu'
    when lower(email) ~ '^[^@\s]+@([a-z0-9-]+\.)*ucsb\.edu$'    then 'ucsb'
    else null
  end;
$$;
revoke all on function public.school_from_email(text) from public;
grant execute on function public.school_from_email(text) to authenticated, anon;

-- ------------------------------------------------------------------------------------------------
-- 2. THE COLUMN. NOT NULL with a CHECK, so a row can never be "no school" or a school we do not
--    serve. Stamped 'calpoly' on every existing row — true by construction, see the header.
-- ------------------------------------------------------------------------------------------------
do $$
begin
  if not exists (select 1 from information_schema.columns
                 where table_schema='public' and table_name='profiles' and column_name='school') then
    alter table public.profiles add column school text;
    raise notice 'profiles.school added';
  end if;
end $$;

-- Stamped from the verified email where one is stored, 'calpoly' otherwise. On production these
-- are the same statement — every stored address is @calpoly.edu — but deriving it is the honest
-- form, and it is what makes the local replica (which holds UCSB and SDSU test rows) meaningful.
update public.profiles set school = coalesce(public.school_from_email(edu_email), 'calpoly') where school is null;
alter table public.profiles alter column school set default 'calpoly';
alter table public.profiles alter column school set not null;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'profiles_school_known') then
    alter table public.profiles
      add constraint profiles_school_known check (school in ('calpoly','sdsu','ucsb'));
  end if;
end $$;

create index if not exists profiles_school_idx on public.profiles (school);

-- The lockdown file grants SELECT column-by-column (table-level SELECT is revoked on purpose, so a
-- new column is unreadable until it is named). `school` is public information about a person in
-- the same way `major` is.
grant select (school) on public.profiles to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 3. THE CLIENT DOES NOT CHOOSE ITS SCHOOL. `authenticated` holds INSERT and UPDATE on profiles,
--    so nothing stops a request from writing school='ucsb'. This trigger overwrites whatever was
--    sent with the school of the VERIFIED email in the JWT, on every insert and every update.
--    When there is no JWT (the SQL editor, a service-role job) it leaves the value alone, so an
--    admin fix is still possible — and if the JWT email is not a school we serve it raises, which
--    is the right answer to "an account exists whose domain the app never admitted".
-- ------------------------------------------------------------------------------------------------
create or replace function public.profiles_stamp_school()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare claims jsonb; s text;
begin
  begin
    claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  exception when others then
    claims := null;
  end;
  /* A student request. The email in the JWT is verified by Supabase Auth; nothing the client sent
     in the row is consulted. A student token WITHOUT an email — anonymous or phone sign-in, both
     switched off on this project — is refused outright rather than trusted: the first version of
     this trigger fell through to the client's value in that case (found in review). */
  if claims is not null and claims ->> 'role' = 'authenticated' then
    s := public.school_from_email(claims ->> 'email');
    if s is null then
      raise exception 'Professify is not open at this email domain yet' using errcode = '42501';
    end if;
    new.school := s;
  /* No student token (the SQL editor, a service-role job): keep what was given, derive if blank. */
  elsif new.school is null then
    new.school := coalesce(public.school_from_email(new.edu_email), 'calpoly');
  end if;
  return new;
end;
$$;

drop trigger if exists profiles_stamp_school on public.profiles;
create trigger profiles_stamp_school
  before insert or update on public.profiles
  for each row execute function public.profiles_stamp_school();

-- ------------------------------------------------------------------------------------------------
-- 4. WHO AM I, WHERE ARE THEY. Both SECURITY DEFINER and STABLE so a policy can call them without
--    the policy itself needing to read profiles (which would recurse into the same policy).
--    my_school() reads the JWT first — the profile row may not exist yet during sign-up — and the
--    profile second. NULL when signed out or at a domain we do not serve.
-- ------------------------------------------------------------------------------------------------
create or replace function public.my_school()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(
    public.school_from_email(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email'),
    (select p.school from public.profiles p where p.id = auth.uid())
  );
$$;
revoke all on function public.my_school() from public;
grant execute on function public.my_school() to authenticated;

-- school_of() is for the SECURITY DEFINER wrappers below, which run as the owner and need no
-- grant. It is NOT callable by a student: granted to `authenticated` it would be an oracle —
-- "does this uuid exist, and at which campus" — for any id a student could guess or be leaked.
create or replace function public.school_of(uid uuid)
returns text
language sql
stable
security definer
set search_path = public
as $$
  select p.school from public.profiles p where p.id = uid;
$$;
revoke all on function public.school_of(uuid) from public, anon, authenticated;

-- ------------------------------------------------------------------------------------------------
-- 5. READING PEOPLE. The blanket `using (true)` read policy goes. What remains:
--      · your own row
--      · anyone you are already connected to, either direction, any status
--        (profiles_read_self_or_connected, already on production — kept as is)
--      · anyone at your own school
--      · everyone, if you are a moderator — the mod queue has to show every campus
--    Postgres ORs permissive policies together, so the connected-to policy and this one combine.
-- ------------------------------------------------------------------------------------------------
drop policy if exists "profiles_read" on public.profiles;
create policy "profiles_read"
  on public.profiles for select to authenticated
  using ( school = public.my_school() or public.is_moderator() );

-- ------------------------------------------------------------------------------------------------
-- 6. SENDING A FRIEND REQUEST. Recreated with the school test appended; everything else in the
--    policy is exactly what production has today (blocked_between, is_suspended, the 40/day cap).
--    Dropped by NAME because that name is what production has; the check in §0 already refused to
--    run if a differently-named INSERT policy existed, so this cannot leave two.
--
--    The school test is a subquery on profiles, evaluated AS THE SENDER: the profiles policy (§5)
--    shows a student only their own campus, so a recipient at another school is simply not there
--    to be found, and the request is refused. It does not call school_of() — a policy runs with
--    the caller's privileges, and school_of() is deliberately not theirs to call.
-- ------------------------------------------------------------------------------------------------
drop policy if exists "fr_send_as_self" on public.friend_requests;
create policy "fr_send_as_self"
  on public.friend_requests for insert to authenticated
  with check (
    from_user = auth.uid()
    and to_user <> auth.uid()
    and status = 'pending'
    and not public.blocked_between(auth.uid(), to_user)
    and not public.is_suspended(auth.uid())
    and (select count(*) from public.friend_requests fr
          where fr.from_user = auth.uid() and fr.created_at > now() - interval '1 day') < 40
    -- THE WALL. A request may only go to someone at the sender's own school.
    and exists (select 1 from public.profiles p
                 where p.id = to_user and p.school = public.my_school())
  );

-- ------------------------------------------------------------------------------------------------
-- 7. DISCOVERY RPCs. Three are recreated from their production bodies with one line added each.
--    Two (suggest_classmates, friends_of) are WRAPPED rather than rewritten: the copies in this
--    folder are not guaranteed to match what production runs, and re-issuing a body I cannot verify
--    is how a silent regression ships. The wrapper keeps the original untouched under a new name
--    and filters its rows by school. Same signature, so the client does not change.
-- ------------------------------------------------------------------------------------------------
create or replace function public.search_people(q text)
returns table(id uuid, display_name text, instagram_handle text)
language sql
security definer
set search_path = public
as $$
  select p.id, p.display_name, p.instagram_handle
  from public.profiles p
  where btrim(coalesce(q,'')) <> ''
    and length(btrim(q)) >= 2
    and p.id <> auth.uid()
    and p.school = public.my_school()                 -- the wall
    and (
      p.display_name ilike '%' || btrim(q) || '%'
      or lower(p.edu_email) = lower(btrim(q))
    )
  order by (lower(p.edu_email) = lower(btrim(q))) desc, p.display_name asc
  limit 15;
$$;

create or replace function public.find_profile_by_handle(handle text)
returns table(id uuid, display_name text, instagram_handle text)
language sql
security definer
set search_path = public
as $$
  select p.id, p.display_name, p.instagram_handle from public.profiles p
  where p.instagram_handle is not null
    and lower(p.instagram_handle) = lower(regexp_replace(coalesce(handle,''), '^@', ''))
    and p.id <> auth.uid()
    and p.school = public.my_school()                 -- the wall
  limit 5;
$$;

-- An invite link from another campus resolves to nobody: no name to show, and the request it
-- would lead to is refused by policy 6 anyway. Better that the link says nothing than that it
-- names a person the reader can never reach.
create or replace function public.get_inviter(ref uuid)
returns table(display_name text)
language sql
stable
security definer
set search_path = public
as $$
  select p.display_name
    from public.profiles p
   where p.id = ref
     and p.display_name is not null
     and p.display_name <> ''
     and p.school = public.my_school()                -- the wall
   limit 1
$$;

-- suggest_classmates: production signature is () -> (id uuid, display_name text, overlap bigint).
do $$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
             where n.nspname='public' and p.proname='suggest_classmates')
     and not exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
             where n.nspname='public' and p.proname='suggest_classmates_unscoped') then
    alter function public.suggest_classmates() rename to suggest_classmates_unscoped;
    revoke all on function public.suggest_classmates_unscoped() from public, anon, authenticated;
    raise notice 'suggest_classmates -> suggest_classmates_unscoped (kept, no longer callable)';
  end if;
end $$;

create or replace function public.suggest_classmates()
returns table(id uuid, display_name text, overlap bigint)
language sql
security definer
stable
set search_path = public
as $$
  select s.id, s.display_name, s.overlap
  from public.suggest_classmates_unscoped() s
  where public.school_of(s.id) = public.my_school();  -- the wall
$$;
revoke all on function public.suggest_classmates() from public, anon;
grant execute on function public.suggest_classmates() to authenticated;

-- friends_of: production signature is (p_user uuid) -> (id, display_name, username, avatar_url, mutual).
do $$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
             where n.nspname='public' and p.proname='friends_of')
     and not exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
             where n.nspname='public' and p.proname='friends_of_unscoped') then
    alter function public.friends_of(uuid) rename to friends_of_unscoped;
    revoke all on function public.friends_of_unscoped(uuid) from public, anon, authenticated;
    raise notice 'friends_of -> friends_of_unscoped (kept, no longer callable)';
  end if;
end $$;

create or replace function public.friends_of(p_user uuid)
returns table(id uuid, display_name text, username text, avatar_url text, mutual boolean)
language sql
security definer
stable
set search_path = public
as $$
  select f.id, f.display_name, f.username, f.avatar_url, f.mutual
  from public.friends_of_unscoped(p_user) f
  where public.school_of(p_user) = public.my_school()  -- a friend's list is only readable in-school
    and public.school_of(f.id) = public.my_school();    -- and only its in-school rows
$$;
revoke all on function public.friends_of(uuid) from public, anon;
grant execute on function public.friends_of(uuid) to authenticated;

-- suggest_friends is NOT on production (checked 2026-09-09; professify-friend-suggestions.sql was
-- never run). When it is, run THIS block again — it wraps it the same way, and is a no-op until then.
do $$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
             where n.nspname='public' and p.proname='suggest_friends')
     and not exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
             where n.nspname='public' and p.proname='suggest_friends_unscoped') then
    alter function public.suggest_friends(int) rename to suggest_friends_unscoped;
    revoke all on function public.suggest_friends_unscoped(int) from public, anon, authenticated;
    execute $w$
      create or replace function public.suggest_friends(p_limit int default 6)
      returns table(id uuid, display_name text, username text, avatar_url text,
                    reason text, mutuals int, score int, shared_codes text[])
      language sql security definer stable set search_path = public
      as $b$
        select s.* from public.suggest_friends_unscoped(p_limit) s
        where public.school_of(s.id) = public.my_school();
      $b$ $w$;
    execute 'revoke all on function public.suggest_friends(int) from public, anon';
    execute 'grant execute on function public.suggest_friends(int) to authenticated';
    raise notice 'suggest_friends wrapped';
  else
    raise notice 'suggest_friends: not present (or already wrapped) — nothing to do';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 7b. THE QUAD (community_posts) — if it exists. Not on production today. A feed of "who posted
--     their schedule" is discovery, and the review found the client reads it with no filter at all.
--     The day the table is created, this fences its reads by the poster's campus; until then it
--     prints a notice and does nothing.
-- ------------------------------------------------------------------------------------------------
do $$
begin
  if exists (select 1 from information_schema.tables where table_schema='public' and table_name='community_posts') then
    execute 'alter table public.community_posts enable row level security';
    execute 'drop policy if exists "quad_read_same_school" on public.community_posts';
    execute $p$create policy "quad_read_same_school" on public.community_posts for select to authenticated
      using ( exists (select 1 from public.profiles p where p.id = community_posts.user_id and p.school = public.my_school())
              or public.is_moderator() )$p$;
    raise notice 'community_posts: read policy fenced by school';
  else
    raise notice 'community_posts: table does not exist — the Quad writes to nothing today; nothing to fence';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- 8. USERNAMES STAY UNIQUE ACROSS ALL SCHOOLS. The client checked "is this handle taken" with a
--    direct SELECT on profiles, which policy 5 now scopes to one school — so a Cal Poly student
--    would be told a handle is free that a UCSB student holds, and hit the unique index on save.
--    A boolean RPC answers the question without exposing the row.
-- ------------------------------------------------------------------------------------------------
create or replace function public.username_taken(u text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (select 1 from public.profiles p
                 where lower(p.username) = lower(btrim(coalesce(u,'')))
                   and p.id is distinct from auth.uid());
$$;
revoke all on function public.username_taken(text) from public, anon;
grant execute on function public.username_taken(text) to authenticated;

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK. Prints what the wall is made of. Every row should read as expected.
-- ------------------------------------------------------------------------------------------------
select 'profiles.school' as what, count(*)::text || ' rows, ' || count(distinct school)::text || ' school(s): ' || string_agg(distinct school, ',') as result from public.profiles
union all
select 'profiles_read policy', qual from pg_policies where tablename='profiles' and policyname='profiles_read'
union all
select 'fr_send_as_self has wall', case when with_check like '%my_school()%' and with_check like '%to_user%' then 'yes' else 'NO' end from pg_policies where tablename='friend_requests' and policyname='fr_send_as_self'
union all
select 'rpc '||p.proname, case when pg_get_functiondef(p.oid) like '%my_school()%' then 'scoped' else 'NOT SCOPED' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('search_people','find_profile_by_handle','get_inviter','suggest_classmates','friends_of','suggest_friends')
union all
select 'unscoped originals callable by authenticated', coalesce(string_agg(p.proname, ','), 'none')
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname like '%_unscoped'
   and has_function_privilege('authenticated', p.oid, 'execute')
union all
select 'school_of callable by a student', case when has_function_privilege('authenticated', 'public.school_of(uuid)', 'execute') then 'YES — wrong' else 'no' end;

-- PostgREST caches function signatures; two of them changed shape. Ask it to look again now
-- rather than on its own schedule.
notify pgrst, 'reload schema';

commit;
