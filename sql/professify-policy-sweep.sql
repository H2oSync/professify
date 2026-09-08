-- ================================================================================================
-- THE FOURTH TIME A POLICY UNDER ANOTHER NAME DEFEATED A MIGRATION — 2026-09-07
-- ================================================================================================
-- Found on the live database today. friend_requests has THREE permissive INSERT policies:
--
--   fr_send_as_self   (from_user = auth.uid()) AND (to_user <> auth.uid()) AND status = 'pending'
--                     AND NOT blocked_between(...) AND NOT is_suspended(...) AND count(*) < 40
--   fr_insert         (auth.uid() = from_user)
--   fr_insert_self    (from_user = auth.uid())
--
-- Permissive policies OR together. So the first one — the one professify-rate-limits.sql installed,
-- with the cap, the block check and the suspension check — decides nothing. Anything the other two
-- allow is allowed.
--
-- WHAT THAT MEANS RIGHT NOW, and it is not only the rate limit:
--   · the 40/day cap does nothing
--   · a BLOCKED person can still send you friend requests
--   · a SUSPENDED account can still send them
--   · and `status` is unconstrained, so a signed-in student can POST
--         {"from_user":"<me>","to_user":"<victim>","status":"accepted"}
--     and be the victim's friend without the victim ever seeing a request. That opens my_sections,
--     opted-in reviews, and conversation membership. It is SEC-01 from the 2026-09-05 audit,
--     still open, because the migration that fixed it added a policy instead of removing these.
--
-- This is the same failure as `my_sections` (August), `reviews_public_read` (09-05) and
-- `reviews_insert_own_edu` (09-06): every migration in this project drops policies BY EXACT NAME,
-- so a policy created under any other name survives all of them.
--
-- So this file drops BY SHAPE, and refuses to drop anything unless the strong policy it is
-- deferring to actually exists. If the strong one is missing it raises and changes nothing —
-- removing the weak policies without a good one in place would lock students out of the feature.
--
-- Safe to re-run. Run AFTER professify-rate-limits.sql.
-- ================================================================================================

do $$
declare
  t         record;
  p         record;
  strong    int;
  dropped   int := 0;
  kept      int := 0;
begin
  for t in
    select * from (values
      ('friend_requests'),
      ('messages'),
      ('community_posts'),
      ('professor_suggestions'),
      ('reviews')
    ) as v(tbl)
  loop
    if to_regclass('public.' || t.tbl) is null then
      raise notice '% : table not on this deploy', t.tbl;
      continue;
    end if;

    -- A "strong" INSERT policy is one that counts. Every rate-limited policy this project writes
    -- contains a `select count(*)` subquery; nothing else on these tables does.
    select count(*) into strong
      from pg_policies
     where schemaname = 'public' and tablename = t.tbl
       and cmd in ('INSERT','ALL') and permissive = 'PERMISSIVE'
       and coalesce(with_check, qual, '') like '%count(%';

    if strong = 0 then
      raise notice '% : no capped INSERT policy to defer to — leaving every policy alone', t.tbl;
      continue;
    end if;

    for p in
      select policyname, coalesce(with_check, qual, '') as body
        from pg_policies
       where schemaname = 'public' and tablename = t.tbl
         and cmd in ('INSERT','ALL') and permissive = 'PERMISSIVE'
         and coalesce(with_check, qual, '') not like '%count(%'
    loop
      raise notice 'DROPPING %.% — permissive INSERT with no cap: %', t.tbl, p.policyname, left(p.body,120);
      execute format('drop policy %I on public.%I', p.policyname, t.tbl);
      dropped := dropped + 1;
    end loop;
    kept := kept + strong;
  end loop;

  raise notice '--- dropped % uncapped polic(ies); % capped polic(ies) remain ---', dropped, kept;
end $$;

-- ------------------------------------------------------------------------------------------------
-- ASSERT. Anything still uncapped after the sweep means the sweep did not understand this schema,
-- and that must stop the migration rather than be reported in a notice nobody reads.
-- ------------------------------------------------------------------------------------------------
do $$
declare bad text;
begin
  select string_agg(tablename || '.' || policyname, ', ')
    into bad
    from pg_policies
   where schemaname = 'public'
     and tablename in ('friend_requests','messages','community_posts','professor_suggestions','reviews')
     and cmd in ('INSERT','ALL') and permissive = 'PERMISSIVE'
     and coalesce(with_check, qual, '') not like '%count(%'
     and exists (select 1 from pg_policies p2
                  where p2.schemaname='public' and p2.tablename=pg_policies.tablename
                    and p2.cmd in ('INSERT','ALL') and p2.permissive='PERMISSIVE'
                    and coalesce(p2.with_check,p2.qual,'') like '%count(%');
  if bad is not null then
    raise exception 'STILL UNCAPPED alongside a capped policy: % — the OR defeats the cap', bad;
  end if;
  raise notice 'OK — no uncapped INSERT policy sits beside a capped one';
end $$;

-- ------------------------------------------------------------------------------------------------
-- And the friend_requests status gate, which the dropped policies were also bypassing.
-- ------------------------------------------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from pg_policies
   where schemaname='public' and tablename='friend_requests' and cmd in ('INSERT','ALL')
     and permissive='PERMISSIVE' and coalesce(with_check,qual,'') not like '%pending%';
  if n > 0 then
    raise exception 'a friend_requests INSERT policy still allows any status — a forged "accepted" row is a forged friendship';
  end if;
  raise notice 'OK — every friend_requests INSERT policy pins status to pending';
end $$;
