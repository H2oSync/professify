-- ================================================================================================
-- WHY A REVIEW WAS REFUSED — 2026-09-11
-- ================================================================================================
-- Tate, with a finished review on screen: "i didnt rate 5 in the last hour so somethings wrong."
-- He was right, and the bug is not in the limit. It is in who gets to explain a refusal.
--
-- public.reviews has ONE insert policy carrying FOUR conditions:
--
--     auth.uid() = user_id
--     and lower(coalesce(auth.jwt() ->> 'email','')) like '%.edu'      -- if it was kept
--     and not public.is_suspended(auth.uid())
--     and ( count of my reviews in the last hour ) < 5
--
-- PostgreSQL answers all four with the same sentence: "new row violates row-level security
-- policy for table reviews". The client then guesses, and it has always guessed the same one:
--
--     /row-level security|policy/i.test(msg) ? "You've hit the limit of 5 reviews an hour."
--
-- So a student refused for ANY of the other three reasons is told a number they never reached,
-- and told to "try again shortly" — advice that will never work, for a reason nobody can see.
-- Reviews have been flat at 12 for over a month. This is at least one of the ways a student
-- who tried to leave one was quietly turned away.
--
-- Two changes here:
--   1. The limit goes 5 -> 30. Someone rating every professor they have ever had is the best
--      thing that can happen to this database, and five stops them a quarter of the way in.
--   2. A BEFORE INSERT trigger names the actual reason. RLS stays exactly where it is and keeps
--      doing the enforcing — the trigger only gets there first, so the sentence the student
--      reads is true. For INSERT, PostgreSQL runs BEFORE ROW triggers and only then evaluates
--      the policy's WITH CHECK, so the trigger's message is the one that surfaces.
--
-- The trigger MIRRORS the policy; it does not replace it. If you ever change one, change both,
-- in this file, and re-run it. Two rules that disagree are worse than one rule that is rude.
--
-- BE HONEST ABOUT WHAT THE SELF-CHECK BELOW CAN SEE. Review, 2026-09-11, proved the drift case
-- on a replica: add a condition to the POLICY that the trigger does not know about — `and score
-- <= 3` was the test — and an insert that trips only that condition raises nothing from the
-- trigger and fails with the same opaque RLS sentence this whole file exists to end. No error,
-- no warning. Section 3 can compare the cap and the .edu clause because it knows to look for
-- them; it cannot know about a condition nobody has written yet. So this is a rule about how
-- the file is edited, not a thing the database enforces: A NEW CONDITION GOES IN BOTH PLACES,
-- HERE, AND GETS A LINE IN SECTION 3.
--
-- Run AFTER professify-lockdown.sql, professify-safety.sql and professify-rate-limits.sql.
-- Safe to re-run.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 0. ANSWER THE QUESTION FIRST: why can't *I* post a review right now?
-- ------------------------------------------------------------------------------------------------
-- Read-only, security INVOKER, so it answers for whoever calls it. Run it signed in as yourself
-- from the app (the SQL editor runs as the table owner and will tell you nothing useful about a
-- student's session) — or from the browser console on professify.app:
--
--     await sb.rpc('why_cant_i_review')
--
-- Every row should say ok = true. The first false one is your answer.
create or replace function public.why_cant_i_review()
returns table(check_name text, ok boolean, detail text)
language plpgsql
security invoker
set search_path = public
as $$
declare n int; em text;
begin
  em := lower(coalesce(auth.jwt() ->> 'email', ''));

  check_name := 'signed in';
  ok         := auth.uid() is not null;
  detail     := coalesce(auth.uid()::text, 'auth.uid() is null — no session on this request');
  return next;

  check_name := 'email claim ends in .edu';
  ok         := em like '%.edu';
  detail     := case when em = '' then 'the JWT carries no email claim at all' else em end;
  return next;

  check_name := 'account not suspended';
  if to_regprocedure('public.is_suspended(uuid)') is null then
    ok := true; detail := 'is_suspended() not installed on this project';
  else
    execute 'select not public.is_suspended(auth.uid())' into ok;
    detail := case when ok then 'not suspended' else 'this account is suspended' end;
  end if;
  return next;

  select count(*) into n
    from public.reviews r
   where r.user_id = auth.uid()
     and r.created_at > now() - interval '1 hour';
  check_name := 'under the hourly limit';
  ok         := n < 30;
  detail     := n || ' review(s) posted in the last hour, limit 30';
  return next;
end $$;

revoke all on function public.why_cant_i_review() from public;
grant execute on function public.why_cant_i_review() to authenticated;


-- ------------------------------------------------------------------------------------------------
-- 1. The limit: 5 -> 30
-- ------------------------------------------------------------------------------------------------
-- PostgreSQL has no "alter policy ... change condition", so the whole policy is recreated and
-- every clause it had has to be carried. The .edu clause is detected rather than assumed, exactly
-- as professify-rate-limits.sql does, so running this on a project that never had it does not
-- quietly add a rule that locks people out.
--
-- Why 30 and not 5: the app's single best source of reviews is a student who has just imported
-- their transcript and can see every professor they have ever had. A senior has twenty-plus. The
-- cap exists to stop a script, and a script does not stop at 30 either — what 30 does is stop
-- the cap from being the thing that ends an honest sitting.
do $$
declare has_edu boolean;
begin
  select exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'reviews'
      and policyname = 'authors write their own reviews'
      and coalesce(with_check,'') like '%.edu%'
  ) into has_edu;

  execute 'drop policy if exists "authors write their own reviews" on public.reviews';
  execute 'drop policy if exists "reviews_insert_own_edu" on public.reviews';

  execute format($f$
    create policy "authors write their own reviews"
      on public.reviews for insert to authenticated
      with check (
        auth.uid() = user_id
        %s
        and not public.is_suspended(auth.uid())
        and ( select count(*) from public.reviews r
              where r.user_id = auth.uid()
                and r.created_at > now() - interval '1 hour' ) < 30
      )$f$,
    case when has_edu
      then $e$and lower(coalesce(auth.jwt() ->> 'email', '')) like '%.edu'$e$
      else '' end);

  raise notice 'reviews: hourly cap is now 30 (.edu clause %)',
    case when has_edu then 'kept' else 'was not present, not added' end;
end $$;

-- That count runs on every insert. It has an index by professor_key but never had one by author.
create index if not exists reviews_user_created_idx
  on public.reviews (user_id, created_at desc);


-- ------------------------------------------------------------------------------------------------
-- 2. The trigger that says which one it was
-- ------------------------------------------------------------------------------------------------
-- errcode P0001 is deliberate and matches professify-word-filter.sql: the client's
-- dbFriendlyErr() passes a bare P0001 message straight through to the student, so these
-- sentences are written for a student and not for a log.
--
-- Note it also fills user_id from auth.uid() when the client sends none. The column already
-- defaults to auth.uid(), so this changes nothing on a healthy insert — but it means a client
-- that ever sends the wrong id gets a sentence instead of a policy refusal nobody can read.
do $$
declare has_edu boolean; edu_branch text; susp_branch text;
begin
  select exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'reviews'
      and policyname = 'authors write their own reviews'
      and coalesce(with_check,'') like '%.edu%'
  ) into has_edu;

  edu_branch := case when has_edu then $e$
    if lower(coalesce(auth.jwt() ->> 'email', '')) not like '%.edu' then
      raise exception 'Reviews can only be posted from a verified school email. Sign in with your .edu address and post again — nothing you wrote has been lost.'
        using errcode = 'P0001';
    end if;$e$ else '' end;

  susp_branch := case when to_regprocedure('public.is_suspended(uuid)') is not null then $s$
    if public.is_suspended(auth.uid()) then
      raise exception 'This account is suspended, so it cannot post reviews right now.'
        using errcode = 'P0001';
    end if;$s$ else '' end;

  execute format($fn$
    create or replace function public.reviews_explain_refusal()
    returns trigger
    language plpgsql
    security invoker
    set search_path = public
    as $body$
    declare n int;
    begin
      if new.user_id is null then new.user_id := auth.uid(); end if;

      if auth.uid() is null then
        raise exception 'You are signed out, so this review has nowhere to go. Sign in and post again — nothing you wrote has been lost.'
          using errcode = 'P0001';
      end if;

      if new.user_id <> auth.uid() then
        raise exception 'This review is addressed to a different account. Sign out, sign back in, and post again.'
          using errcode = 'P0001';
      end if;
      %s
      %s
      select count(*) into n
        from public.reviews r
       where r.user_id = auth.uid()
         and r.created_at > now() - interval '1 hour';
      if n >= 30 then
        raise exception 'That is 30 reviews in an hour, which is the limit. Nothing you wrote has been lost — try again in a little while.'
          using errcode = 'P0001';
      end if;

      return new;
    end
    $body$;
  $fn$, edu_branch, susp_branch);

  raise notice 'reviews_explain_refusal(): installed (.edu branch %, suspension branch %)',
    case when has_edu then 'in' else 'out' end,
    case when susp_branch <> '' then 'in' else 'out' end;
end $$;

drop trigger if exists reviews_explain_refusal_trg on public.reviews;
create trigger reviews_explain_refusal_trg
  before insert on public.reviews
  for each row execute function public.reviews_explain_refusal();


-- ------------------------------------------------------------------------------------------------
-- 3. Self-check
-- ------------------------------------------------------------------------------------------------
-- The trigger and the policy must carry the same number. If these ever drift, the student gets a
-- sentence from one and a refusal from the other, which is the bug this file exists to end.
do $$
declare pol text; fn text; bad int := 0;
begin
  select coalesce(with_check,'') into pol
    from pg_policies
   where schemaname='public' and tablename='reviews'
     and policyname='authors write their own reviews';

  select coalesce(prosrc,'') into fn
    from pg_proc where proname='reviews_explain_refusal';

  if pol is null or pol = '' then
    raise warning 'no insert policy named "authors write their own reviews" on reviews'; bad := bad + 1;
  elsif pol not like '%< 30%' then
    raise warning 'the policy is not capped at 30: %', pol; bad := bad + 1;
  end if;

  if fn = '' then
    raise warning 'reviews_explain_refusal() is not installed'; bad := bad + 1;
  elsif fn not like '%n >= 30%' then
    raise warning 'the trigger is not capped at 30'; bad := bad + 1;
  end if;

  if (pol like '%.edu%') <> (fn like '%.edu%') then
    raise warning 'the policy and the trigger disagree about the .edu rule'; bad := bad + 1;
  end if;

  if not exists (select 1 from pg_trigger where tgname='reviews_explain_refusal_trg') then
    raise warning 'the trigger exists as a function but is not attached to reviews'; bad := bad + 1;
  end if;

  -- Permissive policies OR together. One uncapped INSERT policy beside this one defeats it,
  -- which is exactly how the 5/hour cap was silently off before 2026-09-06.
  if exists (
    select 1 from pg_policies
     where schemaname='public' and tablename='reviews'
       and cmd in ('INSERT','ALL') and permissive='PERMISSIVE'
       and policyname <> 'authors write their own reviews'
       and coalesce(with_check,'') not like '%interval%'
  ) then
    raise warning 'another uncapped INSERT policy sits beside this one and ORs with it'; bad := bad + 1;
  end if;

  if bad = 0 then
    raise notice 'reviews: policy and trigger agree — cap 30, one insert path, refusals are named';
  else
    /* An exception, not a warning. A warning scrolls past in the Supabase editor and the file
       reports success; the failure it is warning about is a student being told the wrong reason
       their review was refused, which is the thing that went unnoticed for a month. */
    raise exception '% problem(s) above — the policy and the trigger do not agree, so fix them and re-run before relying on either', bad;
  end if;
end $$;
