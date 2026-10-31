-- TermChamp: Supabase advisor cleanup (2026-10-30). Idempotent; one transaction.
-- What it does, and what it deliberately leaves alone:
--   1. Pins search_path on the 22 functions the advisor flags (behaviour unchanged: the same schemas, fixed).
--   2. Trigger functions can't be called usefully over the API; revoke EXECUTE from anon/authenticated.
--   3. reviews: drops "reviews_update_own" — it OR'ed a weaker rule (no .edu / not-suspended check) onto
--      "authors edit their own reviews", so a suspended student could still edit reviews.
--   4. Drops exact-duplicate policies (same table, command, role and condition) and duplicate indexes.
--      Each table keeps one policy per rule. Nothing anyone can or can't read changes.
--   LEFT ALONE, on purpose:
--   · reviews_public is SECURITY DEFINER by design: it is how reviews are public while the author column
--     and the reviews table stay private (see the Privacy page). Switching it to invoker would hide every review.
--   · The 83 definer functions callable by signed-in users: checked 2026-10-30 — admin_*/mod_*/analytics_*
--     all call is_moderator()/admin_guard(); friend_emails/friends_of gate on auth.uid() + accepted friendship.
--   · "RLS enabled, no policy" tables are server-only on purpose (nobody can read them over the API).
--   · Leaked-password protection is a dashboard setting (Authentication → Policies), not SQL.
begin;

-- 1. search_path
do $$
declare r record;
begin
  for r in select p.oid::regprocedure as f from pg_proc p join pg_namespace n on n.oid = p.pronamespace
            where n.nspname = 'public' and p.proname in (
              'wf_guard_username','push_fire_at','reviews_set_course_key','touch_group_updated_at','push_seat_state',
              'wf_norm','wf_split','wf_guard','push_day_code','push_meets_on','push_end_time','push_sec_label',
              'report_alert_esc','dpr_text_ok','degree_audit_no_grades','planner_link_esc','planner_link_body',
              'wf_slur_guard_message','wf_slurs','wf_words','wf_words_tight','wf_reserved_usernames')
              and not exists (select 1 from unnest(coalesce(p.proconfig, '{}')) c where c like 'search_path=%')
  loop
    execute format('alter function %s set search_path = public, extensions, pg_temp', r.f);
  end loop;
end $$;

-- 2. trigger functions: not API calls
do $$
declare r record;
begin
  for r in select p.oid::regprocedure as f from pg_proc p join pg_namespace n on n.oid = p.pronamespace
            where n.nspname = 'public' and p.prorettype = 'trigger'::regtype
  loop
    execute format('revoke execute on function %s from public, anon, authenticated', r.f);
  end loop;
end $$;

-- 3. the weaker review-edit rule
drop policy if exists "reviews_update_own" on public.reviews;

-- 4. exact duplicates (kept: the first name in each comment)
drop policy if exists "ch_write" on public.class_history;            -- keep class_history_own (= ch_write_self)
drop policy if exists "ch_write_self" on public.class_history;
drop policy if exists "ch_read" on public.class_history;             -- keep ch_read_self_or_friend (same rule, no function call)
drop policy if exists "course_equiv read" on public.course_equiv;    -- keep course_equiv_public_read
drop policy if exists "course_equiv_read" on public.course_equiv;
drop policy if exists "course_prereqs_read" on public.course_prereqs; -- keep course_prereqs_public_read
drop policy if exists "public read seats" on public.course_seats;    -- keep course_seats_public_read
drop policy if exists "fr_delete" on public.friend_requests;         -- keep fr_delete_involved
drop policy if exists "fr_delete_either_side" on public.friend_requests;
drop policy if exists "fr_read" on public.friend_requests;           -- keep fr_read_involved
drop policy if exists "fr_read_own_edges" on public.friend_requests;
drop policy if exists "own sections" on public.my_sections;          -- keep "my_sections owner"
drop policy if exists "profiles_insert" on public.profiles;          -- keep profiles_insert_own
drop policy if exists "profiles_insert_self" on public.profiles;
drop policy if exists "profiles_update" on public.profiles;          -- keep profiles_update_self
drop policy if exists "profiles_write_own" on public.profiles;
drop policy if exists "authors delete their own reviews" on public.reviews; -- keep reviews_delete_own
drop policy if exists "own reviews deletable" on public.reviews;
drop policy if exists "sc_write" on public.saved_classes;            -- keep saved_classes_own
drop policy if exists "sc_write_self" on public.saved_classes;
drop policy if exists "sc_read" on public.saved_classes;             -- keep sc_read_self_or_friend
drop policy if exists "saved_classes_friends_read" on public.saved_classes; -- covered by sc_read_self_or_friend

drop index if exists public.fr_from_idx;                  -- = friend_requests_from_idx
drop index if exists public.fr_to_idx;                    -- = friend_requests_to_idx
drop index if exists public.review_helpful_one_per_review; -- = review_helpful_pkey

-- sanity: every table still has its rules
do $$
begin
  if (select count(*) from pg_policies where schemaname='public' and tablename='reviews' and cmd='UPDATE') < 1
  or (select count(*) from pg_policies where schemaname='public' and tablename='profiles' and cmd='UPDATE') < 1
  or (select count(*) from pg_policies where schemaname='public' and tablename='saved_classes' and cmd='SELECT') < 1
  or (select count(*) from pg_policies where schemaname='public' and tablename='class_history' and cmd='SELECT') < 1
  or (select count(*) from pg_policies where schemaname='public' and tablename='friend_requests' and cmd='SELECT') < 1
  or (select count(*) from pg_policies where schemaname='public' and tablename='course_seats' and cmd='SELECT') < 1
  then raise exception 'a table lost its last policy — rolled back'; end if;
end $$;
commit;
