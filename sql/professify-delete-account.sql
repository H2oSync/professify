-- ============================================================================
-- Delete my account — the function behind the button
-- ============================================================================
-- A student cannot delete their own auth.users row from the browser; that needs
-- privileges no client should ever hold. So deletion runs inside one
-- SECURITY DEFINER function that clears every row belonging to the caller and
-- then the account itself, as a single transaction. Either all of it goes or
-- none of it does — a half-deleted account is worse than a live one, because
-- the person believes they're gone and they aren't.
--
-- The function only ever acts on auth.uid(). It takes no user id argument, so
-- there is no version of calling it that touches somebody else.
--
-- REVIEWS ARE THE ONE EXCEPTION, and it is deliberate.
-- ----------------------------------------------------------------------------
-- Everything else on the account is *about* the person: their schedule, their
-- friends, their watchlist. A review is different — it is the thing another
-- student came here to read, and it is already baked into a professor's
-- average. Deleting it silently rewrites a number that other people made
-- decisions on, and it means a professor's page gets quietly better or worse
-- every time an unrelated senior graduates and closes their account.
--
-- So the review stays and the AUTHOR LINK is severed: user_id becomes null.
-- After this runs there is no row anywhere tying that review to a person — not
-- for us, not under subpoena, not by joining tables. The review is genuinely
-- anonymous, not merely displayed anonymously.
--
-- The trade this makes: an anonymised review can never be edited or removed
-- again, by anyone, because nothing identifies its author. That is why the
-- app now (a) says so plainly on the delete screen, and (b) gives every
-- student a Delete button on their own reviews, so anyone who wants theirs
-- gone can remove them BEFORE closing the account. Consent has to be informed
-- and it has to have an exit; this file provides the exit at the bottom.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- 1. reviews.user_id must be nullable, or the anonymise step can't run.
--    Guarded, so re-running this file is safe.
-- ---------------------------------------------------------------------------
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='reviews'
      and column_name='user_id' and is_nullable='NO'
  ) then
    alter table public.reviews alter column user_id drop not null;
  end if;
end $$;

-- Nulls can't be smuggled in by a client: the INSERT policy is auth.uid() = user_id,
-- and `auth.uid() = null` evaluates to null, which RLS treats as a refusal. Only this
-- SECURITY DEFINER function can produce a null-authored review.


-- ---------------------------------------------------------------------------
-- 2. Let a student delete their own review from the app.
--    Without this the "reviews stay forever" promise has no escape hatch.
--    Created only if absent — nothing is dropped or replaced.
-- ---------------------------------------------------------------------------
do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname='public' and tablename='reviews' and policyname='own reviews deletable'
  ) then
    create policy "own reviews deletable" on public.reviews
      for delete to authenticated
      using (user_id = auth.uid());
  end if;
end $$;

-- An anonymised review has user_id = null, so `null = auth.uid()` is null and this
-- policy can never match it. Nobody can delete somebody else's orphaned review by
-- signing out or by guessing — the row is beyond every account, including ours.


-- ---------------------------------------------------------------------------
-- 3. The deletion itself.
-- ---------------------------------------------------------------------------
create or replace function public.delete_my_account()
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  me uuid := auth.uid();
  t  record;
begin
  if me is null then
    raise exception 'not signed in';
  end if;

  -- Reviews are kept, de-authored. This runs FIRST: if it fails the whole
  -- transaction rolls back and the account is still intact, rather than the
  -- account being gone and the reviews cascading away behind it.
  if to_regclass('public.reviews') is not null then
    update public.reviews set user_id = null where user_id = me;
  end if;

  -- Tables keyed to the caller by a single owner column. Looped with a
  -- to_regclass guard so a table this deploy doesn't have yet (or one added
  -- later and forgotten here) can't abort the whole deletion.
  for t in
    select * from (values
      ('my_sections',                    'user_id'),
      ('saved_classes',                  'user_id'),
      ('watch_sections',                 'user_id'),
      ('class_history',                  'user_id'),
      ('review_helpful',                 'voter_id'),
      ('friend_suggestion_dismissals',   'user_id')
    ) as v(tbl, col)
  loop
    if to_regclass('public.' || t.tbl) is not null then
      execute format('delete from public.%I where %I = $1', t.tbl, t.col) using me;
    end if;
  end loop;
  -- review_helpful is the votes THIS person cast — their action, so it goes.
  -- Votes other students cast on their reviews are keyed by review_id and the
  -- review survives, so those counts stay correct.

  -- Friendships are two-sided: remove the edge whichever end you are.
  if to_regclass('public.friend_requests') is not null then
    delete from public.friend_requests where from_user = me or to_user = me;
  end if;

  -- Anyone who dismissed this person as a suggestion no longer needs the row.
  if to_regclass('public.friend_suggestion_dismissals') is not null then
    delete from public.friend_suggestion_dismissals where dismissed_id = me;
  end if;

  delete from public.profiles where id = me;

  -- Last, and only if everything above succeeded. By now no reviews point at
  -- this id, so no ON DELETE CASCADE can reach them.
  delete from auth.users where id = me;
end;
$$;

-- PUBLIC gets EXECUTE on a new function automatically, and PUBLIC includes anon.
-- Revoke the wide grant BEFORE granting narrowly — a revoke aimed only at `anon`
-- leaves the PUBLIC grant standing and silently does nothing.
revoke execute on function public.delete_my_account() from public;
revoke execute on function public.delete_my_account() from anon;
grant   execute on function public.delete_my_account() to authenticated;


-- ---------------------------------------------------------------------------
-- VERIFY — do NOT test this on your own account.
--   1. Make a throwaway account, add a class, write a review. Note the
--      professor and the review id:
--        select id, professor_name, score from public.reviews
--         where user_id = '<their id>';
--   2. Settings -> Delete account -> type DELETE.
--   3. Signed in as yourself, confirm:
--        select count(*) from public.profiles      where id      = '<their id>';  -- 0
--        select count(*) from public.saved_classes where user_id = '<their id>';  -- 0
--        select count(*) from public.class_history where user_id = '<their id>';  -- 0
--        select count(*) from public.reviews       where user_id = '<their id>';  -- 0
--      ...but the review itself is still there, now unowned:
--        select id, professor_name, score, user_id from public.reviews
--         where id = '<the review id>';        -- one row, user_id null
--   4. Open that professor in the app: the review is still listed and the
--      average is unchanged.
--   5. Try signing in as the deleted address — it should create a NEW empty
--      account, and Your reviews should be empty. The orphaned review must NOT
--      reattach.
--
-- Also worth checking once: sign in, open Your reviews, delete one. It should
-- disappear and the professor's average should move. That's step 2 working.
--
-- NOT covered by this function: the profile photo in Storage. The app deletes
-- that before calling, because Storage isn't reachable from SQL.
-- ---------------------------------------------------------------------------
