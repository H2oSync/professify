-- ================================================================================================
-- THE SAME FORGED FRIENDSHIP, ONE STEP TO THE RIGHT — 2026-09-07
-- ================================================================================================
-- professify-policy-sweep.sql closed the INSERT route: friend_requests now has exactly one INSERT
-- policy and it pins status to 'pending'. Verified live.
--
-- The UPDATE side was not swept, and it has the identical problem. Three permissive UPDATE
-- policies on friend_requests:
--
--   fr_accept_as_recipient   using ( to_user = auth.uid() AND status = 'pending' )   <-- correct
--   fr_update                using ( auth.uid() = from_user OR auth.uid() = to_user )
--   fr_update_involved       using ( from_user = auth.uid() OR to_user = auth.uid() )
--
-- The last two let the SENDER update their own row, with no constraint on what they set it to. So
-- the forgery just takes two steps instead of one, and both are allowed:
--
--     insert  {from_user: me, to_user: victim, status: 'pending'}    -- legitimate, allowed
--     update  set status = 'accepted' where from_user = me           -- allowed by fr_update
--
-- Reproduced on PostgreSQL 16 with the INSERT hole already closed: INSERT 0 1, UPDATE 1,
-- "status is now: accepted". The victim never touched anything.
--
-- Only the RECIPIENT may accept. That is what fr_accept_as_recipient already says, and it is the
-- only UPDATE the app ever makes — the whole client contains exactly one:
--     from('friend_requests').update({status:'accepted'}).eq('id', id)
-- Declining and unfriending are DELETEs and are untouched by this file.
--
-- Same by-shape rule as the INSERT sweep, and the same safety property: nothing is dropped unless
-- a policy that constrains `status` exists to defer to.
--
-- Safe to re-run. Run AFTER professify-policy-sweep.sql.
-- ================================================================================================

do $$
declare
  p       record;
  strong  int;
  dropped int := 0;
begin
  select count(*) into strong
    from pg_policies
   where schemaname='public' and tablename='friend_requests'
     and cmd in ('UPDATE','ALL') and permissive='PERMISSIVE'
     and coalesce(qual,'') like '%status%';

  if strong = 0 then
    raise notice 'friend_requests: no status-constrained UPDATE policy to defer to — leaving every policy alone';
  else
    for p in
      select policyname, coalesce(qual,'') as body
        from pg_policies
       where schemaname='public' and tablename='friend_requests'
         and cmd in ('UPDATE','ALL') and permissive='PERMISSIVE'
         and coalesce(qual,'') not like '%status%'
    loop
      raise notice 'DROPPING friend_requests.% — lets the sender accept their own request: %',
                   p.policyname, left(p.body,110);
      execute format('drop policy %I on public.friend_requests', p.policyname);
      dropped := dropped + 1;
    end loop;
    raise notice '--- dropped % unconstrained UPDATE polic(ies); % correct one(s) remain ---', dropped, strong;
  end if;
end $$;

-- ------------------------------------------------------------------------------------------------
-- ASSERT
-- ------------------------------------------------------------------------------------------------
do $$
declare bad text; n int;
begin
  select string_agg(policyname, ', ') into bad
    from pg_policies
   where schemaname='public' and tablename='friend_requests'
     and cmd in ('UPDATE','ALL') and permissive='PERMISSIVE'
     and coalesce(qual,'') not like '%to_user%';
  if bad is not null then
    raise exception 'an UPDATE policy on friend_requests does not require to_user = auth.uid(): % — the sender can still accept their own request', bad;
  end if;

  select count(*) into n from pg_policies
   where schemaname='public' and tablename='friend_requests'
     and cmd in ('UPDATE','ALL') and permissive='PERMISSIVE';
  if n = 0 then
    raise exception 'no UPDATE policy left on friend_requests — nobody could accept a request';
  end if;
  raise notice 'OK — % UPDATE polic(ies), all of them recipient-only', n;
end $$;

-- ------------------------------------------------------------------------------------------------
-- While we are here: the same by-shape question asked of every OTHER table, read-only.
-- Anything named below is a permissive policy that grants more than its siblings on the same table
-- and command. It is not automatically wrong — it is the shape that has now caused this bug five
-- times, so it is worth a look.
-- ------------------------------------------------------------------------------------------------
do $$
declare r record; n int := 0;
begin
  for r in
    select tablename, cmd, count(*) as policies,
           string_agg(policyname, ', ' order by policyname) as names
      from pg_policies
     where schemaname='public' and permissive='PERMISSIVE'
       and cmd in ('INSERT','UPDATE','DELETE','ALL')
     group by tablename, cmd
    having count(*) > 1
     order by 1,2
  loop
    n := n + 1;
    raise notice 'MULTIPLE % POLICIES on %: %', r.cmd, r.tablename, r.names;
  end loop;
  if n = 0 then
    raise notice 'OK — no table has two permissive policies for the same command';
  else
    raise notice '% table/command pair(s) above have more than one permissive policy. They OR together: the weakest one decides.', n;
  end if;
end $$;
