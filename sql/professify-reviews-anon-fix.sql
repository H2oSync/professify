-- ================================================================================================
-- REVIEWS ARE STILL NOT ANONYMOUS — 2026-09-06
-- ================================================================================================
-- Found by querying the live database after the lockdown ran. Everything else came back clean:
-- RLS is on everywhere, edu_email and phone_hash are gone from what `authenticated` can read, and
-- friend_requests accepts an UPDATE on the `status` column only. But this came back:
--
--     D reviews_true_policy   ->   reviews_public_read
--
-- There is a policy on public.reviews with `using (true)` under a name no migration mentions.
-- professify-lockdown.sql §8 drops the one it knows about, by its exact name — and that is exactly
-- the structural weakness the audit flagged: every migration in this project drops policies by
-- name, so a permissive policy created under any OTHER name survives all of them and ORs with
-- everything. This is the second time this has happened on this database (see rls-hardening's note
-- about my_sections staying world-readable through two rounds of correct SQL).
--
-- WHAT IT MEANS RIGHT NOW: permissive policies OR together, so `using (true)` grants SELECT on
-- every column of every review to every role that holds table SELECT. `authenticated` holds it.
-- Reviews are presented to students as anonymous; any signed-in student can currently read
-- reviews.user_id and put a name to every one of them.
--
-- This file drops permissive read policies on `reviews` BY SHAPE rather than by name, so it does
-- not matter what the next one gets called.
-- ================================================================================================

do $$
declare p record; n int := 0;
begin
  for p in
    select policyname, qual
    from pg_policies
    where schemaname='public' and tablename='reviews'
      and cmd in ('SELECT','ALL') and permissive='PERMISSIVE'
      and coalesce(qual,'true') = 'true'
  loop
    raise notice 'dropping wide-open policy on reviews: %  (using: %)', p.policyname, p.qual;
    execute format('drop policy %I on public.reviews', p.policyname);
    n := n + 1;
  end loop;
  if n = 0 then
    raise notice 'reviews: no using(true) policy found — nothing to drop';
  else
    raise notice 'reviews: dropped % wide-open polic(ies)', n;
  end if;
end $$;

-- The two reads that are supposed to exist, recreated so dropping the wide one cannot leave the
-- table unreadable to the people who are entitled to it. Both come from professify-messaging.sql;
-- they are repeated here so this file is safe to run on its own.
drop policy if exists "authors read their own reviews" on public.reviews;
create policy "authors read their own reviews"
  on public.reviews for select to authenticated
  using ( auth.uid() = user_id );

drop policy if exists "friends read reviews shared with them" on public.reviews;
create policy "friends read reviews shared with them"
  on public.reviews for select to authenticated
  using (
    share_with_friends
    and exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and ( (fr.from_user = auth.uid() and fr.to_user = public.reviews.user_id)
           or (fr.to_user   = auth.uid() and fr.from_user = public.reviews.user_id) )
    )
  );

-- Belt as well as braces. The row policies above are the barrier; this makes the column itself
-- unreadable, so a permissive policy added later under yet another name cannot re-expose it.
-- A missing column is a stronger guarantee than a policy, because a policy can be worked around
-- by asking a different question and a revoked column cannot.
revoke all on public.reviews from anon, public, authenticated;
grant select, insert, update, delete on public.reviews to authenticated;
do $$
declare cols text;
begin
  select string_agg(quote_ident(column_name), ', ' order by ordinal_position)
    into cols
  from information_schema.columns
  where table_schema='public' and table_name='reviews' and column_name <> 'user_id';
  execute format('revoke select on public.reviews from authenticated');
  execute format('grant select (%s) on public.reviews to authenticated', cols);
  raise notice 'reviews: SELECT now excludes user_id';
end $$;

-- The public site reads reviews through the view, which has no user_id column at all.
do $$ begin
  if exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
             where n.nspname='public' and c.relname='reviews_public' and c.relkind='v') then
    execute 'grant select on public.reviews_public to anon, authenticated';
    raise notice 'reviews_public: readable, as intended';
  else
    raise warning 'reviews_public does NOT exist — run professify-messaging.sql, or the site has no way to show reviews';
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- VERIFY as a signed-in student
-- ------------------------------------------------------------------------------------------------
--   select user_id from public.reviews limit 1;      -> ERROR 42501 permission denied
--   select id, score, note from public.reviews;      -> only your own rows
--   select * from public.reviews_public limit 1;     -> rows, and no user_id column exists
