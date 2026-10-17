-- =================================================================================================
-- TermChamp security picks — 2026-10-16 (Tate's decisions on the items the 2026-10-14/15 reviews left open)
--
-- One transaction: if the self-check at the bottom fails, nothing is changed. Safe to run twice.
-- It refuses to run ("VERIFY AGAINST LIVE") if a function it replaces has changed since it was written, and
-- it takes its only table locks (events, messages) at the very end, with a 5-second lock timeout.
-- Run it after professify-security-hotfix-2026-10-14.sql and professify-security-pass2-2026-10-15.sql.
--
-- NOTHING HERE CHANGES WHAT THE IPHONE APP IN APPLE REVIEW SEES. The reviewed app (bcb4597) never
-- touches groups, push_subscriptions, the word-filter lists, suggest_classmates, log_events or
-- trending_profs. Every function below keeps its exact name, arguments and result columns, and no
-- view's columns change. (The one change that WOULD show up in the app, rounding review times to the
-- day, is deliberately NOT in this file: it is sql/professify-review-day-timestamps-AFTER-APPLE.sql.)
--
-- What it does, in plain words
--   1. CLASSMATE SUGGESTIONS  People who are not your friends yet now see only HOW MANY classes you
--      share ("3 classes in common"), not WHICH ones. suggest_classmates_v2 returns an empty list of
--      codes (the count is kept); suggest_friends returns no codes at all. The website's card shows
--      the count with no class chips. Friends still see each other's classes the normal way.
--   2. REPORT EMAILS  The email to support@ about a REVIEW report no longer names the review's
--      author: the "About" line says "The review's author (open the report queue to see who)". Reports
--      about a person or a message still name the person (they are not anonymous). The "Other reports"
--      count stays. Old copies of review-report emails stored in report_alerts have their saved body
--      erased; already-sent rows are never sent again (the sender only looks at rows with sent_at null),
--      and a not-yet-sent row simply rebuilds its body with the new anonymous wording.
--   3. TRENDING PROFESSORS  Only signed-in students count, and a professor needs at least 3 DIFFERENT
--      students. events gets one new column, acct: when a signed-in student's browser logs an event,
--      the server stores a salted one-way hash of their account id (pseudonymous, not anonymous: the
--      same account always gets the same hash; the salt lives in a table clients cannot read, and a
--      missing salt means no hash at all). Hashes older than 8 days are blanked by log_events' own cleanup.
--      Signed-out visitors still log analytics exactly as before, but their
--      events have acct = null and never count toward "trending". events stays unreadable to
--      clients. Existing events have no acct, so the trending strip starts empty and fills as students
--      browse (the window is 7 days). The 3-student floor in trending_profs was already there; the
--      website now asks for 3 instead of 5.
--   4. GROUPS (dormant feature, nobody calls the tables)  Only the person who made a group can delete
--      it or remove other members; a member can still leave on their own; any member can still rename
--      the group; nobody can rewrite who the creator is.
--   5. MESSAGE EXTRAS  messages.payload (the little card attached to a shared class or professor) is
--      capped at 2000 characters. Real ones are under 400. Added as NOT VALID first, then validated
--      only if no existing row breaks it.
--   6. WORD-FILTER LISTS  The block-lists inside wf_words(), wf_words_tight(), wf_slurs() and
--      wf_reserved_usernames() could be read by any signed-in student. The four checking functions
--      (wf_hit, wf_hit_tight, wf_reserved, wf_slur_hit) now run with the owner's rights, and the four
--      list functions are no longer callable by students. The name/review/group/message checks behave
--      exactly as before.
--   7. PUSH SIGN-UP  Re-subscribing to website notifications failed (the table had no UPDATE policy).
--      Adds the missing "update my own row" policy (and limits what columns a student can update), and
--      a function claim_push_subscription(...) that makes the endpoint belong to whoever is signed in
--      now (it removes another account's row for the same browser, then saves this one's). The website
--      uses the function and falls back to the old save if the function is missing.
--   8. ACCOUNT DELETION  The nightly deletion job now also removes the student's schedule-card images
--      (bucket schedule-cards, owner = the student) next to the profile photo, with the same
--      "allow delete" switch and the same never-block-the-deletion error handling.
--
-- Not in this file: review times to the day (held until Apple approves), the /s page headers, and the
-- GitHub workflow items from the audit.
--
-- Also noted by the audit: the replica has no trigger report_alerts_on_report on public.reports.
-- This file does not create it (professify-report-alerts.sql does). The self-check below only
-- NOTICES if it is missing on the database it runs on.
--
-- Rollback notes are at the very bottom.
-- =================================================================================================

begin;
set local lock_timeout = '5s';   -- never queue behind a long-running statement; the brief table locks are taken at the very end

-- ---------- 0. Drift guard: stop if production no longer looks like what this was written against ----------
do $$
begin
  if to_regprocedure('public.suggest_classmates_v2__incl_pending()') is null then raise exception 'VERIFY AGAINST LIVE: suggest_classmates_v2__incl_pending() missing'; end if;
  if to_regprocedure('public.suggest_friends_unscoped__incl_pending(integer)') is null then raise exception 'VERIFY AGAINST LIVE: suggest_friends_unscoped__incl_pending(integer) missing'; end if;
  if to_regprocedure('public.report_alert_body(uuid,text)') is null then raise exception 'VERIFY AGAINST LIVE: report_alert_body(uuid,text) missing'; end if;
  if to_regclass('public.report_alerts') is null then raise exception 'VERIFY AGAINST LIVE: report_alerts missing'; end if;
  if to_regprocedure('public.log_events(jsonb)') is null then raise exception 'VERIFY AGAINST LIVE: log_events(jsonb) missing'; end if;
  if to_regclass('public.events') is null or to_regclass('public.prof_activity_7d') is null then raise exception 'VERIFY AGAINST LIVE: events / prof_activity_7d missing'; end if;
  if to_regprocedure('public.trending_profs(integer,integer)') is null then raise exception 'VERIFY AGAINST LIVE: trending_profs missing'; end if;
  if to_regclass('public.groups') is null or to_regclass('public.group_members') is null then raise exception 'VERIFY AGAINST LIVE: groups tables missing'; end if;
  if to_regclass('public.messages') is null then raise exception 'VERIFY AGAINST LIVE: messages missing'; end if;
  if to_regprocedure('public.wf_hit(text)') is null or to_regprocedure('public.wf_words()') is null then raise exception 'VERIFY AGAINST LIVE: wf_* functions missing'; end if;
  if to_regclass('public.push_subscriptions') is null then raise exception 'VERIFY AGAINST LIVE: push_subscriptions missing'; end if;
  if to_regprocedure('public.purge_due_account_deletions()') is null then raise exception 'VERIFY AGAINST LIVE: purge_due_account_deletions() missing'; end if;
end $$;

-- Every function this file replaces WHOLE must still be exactly what it was written against (or already
-- carry this file's marker, i.e. this is a re-run). If production moved on, stop instead of undoing it.
do $$
declare r record; src text;
begin
  for r in select * from (values
      ('public.log_events(jsonb)',                                 'be079839325aebf1e1b123628b0771a8'),
      ('public.purge_due_account_deletions()',                     'a3ff32e5a608bcedef3af4fffc58b2ae'),
      ('public.report_alert_body(uuid,text)',                      'b6196fa8bed22c8d0e0d2bd283972ebe'),
      ('public.suggest_classmates_v2__incl_pending()',             '6810f4bb04407527ae2ff3cc826b767d'),
      ('public.suggest_friends_unscoped__incl_pending(integer)',   'ff962d95b378a3534335c14380cfa930')) v(fn, h)
  loop
    select prosrc into src from pg_proc where oid = r.fn::regprocedure;
    if position('sec-picks-2026-10-16' in src) = 0 and md5(src) <> r.h then
      raise exception 'VERIFY AGAINST LIVE: % changed', r.fn;
    end if;
  end loop;
end $$;

-- Section 6 makes the four word LISTS unreadable to students. Anything else that calls a list as the
-- signed-in student would break, so stop if something other than the four checkers does.
do $$
declare bad text;
begin
  select string_agg(p.oid::regprocedure::text, ', ') into bad
    from pg_proc p
   where p.pronamespace not in ('pg_catalog'::regnamespace, 'information_schema'::regnamespace)
     and not (p.pronamespace = 'public'::regnamespace and p.proname in
              ('wf_hit','wf_hit_tight','wf_reserved','wf_slur_hit','wf_words','wf_words_tight','wf_slurs','wf_reserved_usernames'))
     and p.prosrc ~ 'wf_words|wf_slurs|wf_reserved_usernames';
  if bad is not null then raise exception 'VERIFY AGAINST LIVE: other functions read the word lists: %', bad; end if;
  if exists (select 1 from pg_depend d
              where d.refobjid in (select oid from pg_proc where pronamespace = 'public'::regnamespace
                                   and proname in ('wf_words','wf_words_tight','wf_slurs','wf_reserved_usernames'))
                and d.classid <> 'pg_proc'::regclass and d.deptype = 'n') then
    raise exception 'VERIFY AGAINST LIVE: a view, policy, constraint or trigger depends on a word-list function';
  end if;
end $$;

-- ---------- 1. Classmate suggestions: a count for strangers, never the class codes ----------
-- Same signatures and RETURNS TABLE columns as before (the iPhone app only reads suggest_friends'
-- id / display_name / username / avatar_url / reason, none of which change).
CREATE OR REPLACE FUNCTION public.suggest_classmates_v2__incl_pending()
 RETURNS TABLE(id uuid, display_name text, username text, avatar_url text, overlap integer, codes text[])
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
       -- sec-picks-2026-10-16: a stranger sees HOW MANY classes you share, never which ones.
       '{}'::text[] as codes
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

CREATE OR REPLACE FUNCTION public.suggest_friends_unscoped__incl_pending(p_limit integer DEFAULT 6)
 RETURNS TABLE(id uuid, display_name text, username text, avatar_url text, reason text, mutuals integer, score integer, shared_codes text[])
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
with me as (select auth.uid() as uid),
connected as (
  select case when r.from_user = m.uid then r.to_user else r.from_user end as other
  from public.friend_requests r, me m
  where (r.from_user = m.uid or r.to_user = m.uid)
    and r.status in ('accepted','pending')
),
my_friends as (
  select case when r.from_user = m.uid then r.to_user else r.from_user end as fid
  from public.friend_requests r, me m
  where (r.from_user = m.uid or r.to_user = m.uid)
    and r.status = 'accepted'
),
mutual as (
  select case when r.from_user = f.fid then r.to_user else r.from_user end as other,
         count(distinct f.fid)::int as n
  from public.friend_requests r
  join my_friends f on (r.from_user = f.fid or r.to_user = f.fid)
  where r.status = 'accepted'
  group by 1
),
my_secs as (
  select distinct s.class_nbr, s.code
  from public.my_sections s, me m
  where s.user_id = m.uid and s.class_nbr is not null
),
my_codes as (
  select distinct s.code from public.my_sections s, me m
  where s.user_id = m.uid and s.code is not null
),
sec_hits as (
  select s.user_id as other, count(distinct s.class_nbr)::int as n
  from public.my_sections s
  join my_secs k on k.class_nbr = s.class_nbr
  group by 1
),
course_hits as (
  select s.user_id as other, count(distinct s.code)::int as n
  from public.my_sections s
  join my_codes k on k.code = s.code
  group by 1
),
-- NEW: the codes behind those two counts, so the card can name them.
code_list as (
  select s.user_id as other, array_agg(distinct s.code order by s.code) as codes
  from public.my_sections s
  join my_codes k on k.code = s.code
  group by 1
),
me_prof as (
  select p.major, p.class_standing from public.profiles p, me m where p.id = m.uid
),
cand as (
  select p.id,
         coalesce(sh.n,0) as sec_n,
         greatest(coalesce(ch.n,0) - coalesce(sh.n,0), 0) as course_n,
         least(coalesce(mu.n,0), 5) as mut_n,
         coalesce(mu.n,0) as mut_raw,
         cl.codes as codes,
         (p.major is not null and p.major = (select major from me_prof)) as same_major,
         (p.major is not null and p.major = (select major from me_prof)
          and p.class_standing is not null
          and p.class_standing = (select class_standing from me_prof)) as same_cohort
  from public.profiles p
  left join sec_hits    sh on sh.other = p.id
  left join course_hits ch on ch.other = p.id
  left join code_list   cl on cl.other = p.id
  left join mutual      mu on mu.other = p.id
  where p.id <> (select uid from me)
    and p.id not in (select other from connected)
    and p.id not in (select dismissed_id from public.friend_suggestion_dismissals
                     where user_id = (select uid from me))
),
scored as (
  select c.*,
         (c.sec_n * 40) + (c.mut_n * 18) + (c.course_n * 10)
           + (case when c.same_cohort then 6 when c.same_major then 3 else 0 end) as sc
  from cand c
  where c.sec_n > 0 or c.course_n > 0 or c.mut_raw >= 2
)
select s.id,
       coalesce(p.display_name,'Classmate') as display_name,
       p.username,
       p.avatar_url,
       case
         when s.sec_n*40 >= greatest(s.mut_n*18, s.course_n*10) and s.sec_n > 0
           then (case when s.sec_n = 1 then 'In one of your sections'
                      else 'In '||s.sec_n||' of your sections' end)
         when s.mut_n*18 >= s.course_n*10 and s.mut_raw >= 2
           then s.mut_raw||' mutual friends'
         when s.course_n > 0
           then (case when s.course_n = 1 then 'Taking one of your classes'
                      else 'Taking '||s.course_n||' of your classes' end)
         when s.mut_raw >= 2 then s.mut_raw||' mutual friends'
         when s.same_cohort  then 'Same major and year as you'
         else 'Same major as you'
       end as reason,
       s.mut_raw as mutuals,
       s.sc::int as score,
       -- A pure-mutual-friends suggestion shares no class, and must not be handed an array
       -- that would make the card claim one.
       -- sec-picks-2026-10-16: the codes behind the counts are not handed to non-friends.
       null::text[] as shared_codes
from scored s
join public.profiles p on p.id = s.id
order by s.sc desc, p.display_name asc
limit greatest(least(coalesce(p_limit,6), 25), 1);
$function$;

-- ---------- 2. Report emails never name a review's author ----------
CREATE OR REPLACE FUNCTION public.report_alert_body(p_report uuid, p_kind text)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  r record; about uuid; who text; uname text; by_name text; prior int; reason text; what text; hrs int;
  due text; filed text; rows text := ''; extra text := ''; subj text; para text; card text;
  rv jsonb; gtitle text;
begin
  select * into r from public.reports where id = p_report;
  if not found then return null; end if;

  if r.kind = 'review' then
    begin
      select to_jsonb(v) into rv from public.reviews v where v.id::text = r.target_id;
    exception when others then rv := null;
    end;
  end if;
  about := coalesce(r.target_user, case when rv ? 'user_id' and (rv->>'user_id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then (rv->>'user_id')::uuid end);
  select p.display_name, p.username into who, uname from public.profiles p where p.id = about;
  -- sec-picks-2026-10-16: a review's author stays anonymous in the email (and in the stored copy).
  if r.kind = 'review' then who := null; uname := null; end if;
  select p.display_name into by_name from public.profiles p where p.id = r.reporter;
  select count(*)::int into prior from public.reports x
   where x.id <> r.id and x.created_at <= r.created_at
     and (x.target_user = about or (x.kind = 'review' and x.target_user is null and exists (
          select 1 from public.reviews v2 where v2.id::text = x.target_id and to_jsonb(v2)->>'user_id' = about::text)));

  reason := case r.reason
    when 'harassment' then 'Harassment or bullying' when 'hate' then 'Hate or discrimination'
    when 'threat' then 'Threats or violence' when 'private_info' then 'Shares private information'
    when 'impersonation' then 'Pretending to be someone else' when 'sexual' then 'Sexual content'
    when 'spam' then 'Spam or advertising' when 'not_about_teaching' then 'Not about the class or teaching'
    else 'Something else' end;
  what := case
    when r.kind = 'user' and r.target_id like 'group:%' then 'A group name'
    when r.kind = 'user' then 'A person' when r.kind = 'review' then 'A review'
    when r.kind = 'message' then 'A message' when r.kind = 'post' then 'A post'
    else 'A suggestion' end;
  filed := to_char(r.created_at at time zone 'America/Los_Angeles', 'FMDy FMMon FMDD, FMHH12:MI AM') || ' PT';
  due   := to_char((r.created_at + interval '24 hours') at time zone 'America/Los_Angeles', 'FMDy FMMon FMDD, FMHH12:MI AM') || ' PT';

  if r.kind = 'review' then
    if rv is not null then
      extra := '<p style="margin:0 0 6px;color:#64748B;font-size:13px">The review'
            || coalesce(' of ' || report_alert_esc(nullif(rv->>'professor_name', '')), '')
            || coalesce(' (' || report_alert_esc(nullif(rv->>'course', '')) || ')', '')
            || coalesce(', ' || report_alert_esc(nullif(rv->>'score', '')) || ' stars', '') || '</p>'
            || '<blockquote style="margin:0 0 14px;padding:10px 12px;background:#F8FAFC;border-left:3px solid #CBD5E1;white-space:pre-wrap">'
            || report_alert_esc(left(coalesce(rv->>'note', '(no written review)'), 2000)) || '</blockquote>';
    end if;
  elsif r.kind = 'user' and r.target_id like 'group:%' then
    begin
      select c.title into gtitle from public.conversations c where c.id::text = substr(r.target_id, 7);
    exception when others then gtitle := null;
    end;
    extra := '<p style="margin:0 0 6px;color:#64748B;font-size:13px">The group name (they made the group)</p>'
          || '<blockquote style="margin:0 0 14px;padding:10px 12px;background:#F8FAFC;border-left:3px solid #CBD5E1">'
          || report_alert_esc(coalesce(gtitle, '(the group is gone)')) || '</blockquote>';
  end if;
  if r.note is not null and r.note <> '' and not (r.kind = 'review' and rv is not null and btrim(r.note) = btrim(coalesce(rv->>'note', ''))) then
    extra := extra || '<p style="margin:0 0 6px;color:#64748B;font-size:13px">'
          || case when r.kind = 'message' then 'The message' else 'Note with the report' end || '</p>'
          || '<blockquote style="margin:0 0 14px;padding:10px 12px;background:#F8FAFC;border-left:3px solid #CBD5E1;white-space:pre-wrap">'
          || report_alert_esc(left(r.note, 2000)) || '</blockquote>';
  end if;

  rows := '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">What</td><td>' || what || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Why</td><td><b>' || reason || '</b></td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">About</td><td>'
       || case when r.kind = 'review' then 'The review''s author (open the report queue to see who)'
               when about is null then '—' else report_alert_esc(coalesce(who, 'Someone')) || coalesce(' (@' || report_alert_esc(uname) || ')', '') end || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Other reports</td><td>'
       || case when about is null then '—' when prior = 0 then 'None before this one' else prior::text || ' about this person before this one' end || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Reported by</td><td>' || report_alert_esc(coalesce(by_name, 'Someone')) || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Filed</td><td>' || filed || '</td></tr>'
       || '<tr><td style="padding:3px 12px 3px 0;color:#64748B;white-space:nowrap">Handle by</td><td><b>' || due || '</b></td></tr>';

  if p_kind = 'reminder' then
    subj := 'Still open: ' || lower(what) || ' reported for ' || lower(reason) || ' — handle by ' || due;
    hrs := floor(extract(epoch from now() - r.created_at) / 3600)::int;
    para := '<p style="margin:0 0 14px"><b>This report is still open, ' || hrs || ' hours after it was filed.</b> We promise to act on reports within 24 hours'
         || case when hrs >= 24 then ' — this one is past that, so please handle it now' else '' end || '.</p>';
  else
    subj := 'New report: ' || lower(what) || ' — ' || lower(reason);
    para := '<p style="margin:0 0 14px">Someone reported something on TermChamp. It needs to be handled within 24 hours.</p>';
  end if;
  para := para
       || '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 16px;font-size:14px">' || rows || '</table>'
       || extra
       || '<p style="margin:0 0 6px"><b>To act on it:</b> sign in at <a href="https://termchamp.com" style="color:#183178">termchamp.com</a> on a computer → Settings → <b>Open the report queue</b>. Remove it, suspend the person, or dismiss it.</p>'
       || '<p style="margin:0;color:#94A3B8;font-size:12px">Report ' || r.id || '</p>';
  card := '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1F7;padding:24px 0"><tr><td align="center">'
       || '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fff;border-radius:14px;overflow:hidden;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
       || '<tr><td style="background:#183178;padding:18px 24px"><span style="color:#FBF7EE;font-family:Georgia,serif;font-size:20px;font-weight:bold">TermChamp · Reports</span></td></tr>'
       || '<tr><td style="padding:24px;color:#1E293B;font-size:15px;line-height:1.5">' || para || '</td></tr>'
       || '</table></td></tr></table>';
  return jsonb_build_object('subject', subj, 'html', card);
end $function$;

-- Erase stored copies of review-report emails that already name an author. send_report_alerts() only
-- sends rows with sent_at null, and rebuilds a missing body from report_alert_body (now anonymous), so
-- blanking html on a SENT row can never cause a re-send. Subjects never contain a name.
update public.report_alerts a
   set html = null
  from public.reports r
 where r.id = a.report_id and r.kind = 'review' and a.html is not null;
-- Sent rows whose report has since been deleted can no longer be classified; erase those too (sent only).
update public.report_alerts a
   set html = null
 where a.html is not null and a.sent_at is not null
   and not exists (select 1 from public.reports r where r.id = a.report_id);

-- ---------- 3. Trending professors: signed-in students only, 3+ different students ----------
-- The salt: one row, created here with random text, readable only by the server-side functions.
create table if not exists public.event_salt (
  id   boolean primary key default true check (id),
  salt text not null default (replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''))
);
insert into public.event_salt (id) values (true) on conflict do nothing;
alter table public.event_salt enable row level security;
revoke all on public.event_salt from public, anon, authenticated;

CREATE OR REPLACE FUNCTION public.log_events(p_batch jsonb)
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  e         jsonb;
  n         integer := 0;
  who_id    text;
  ev_name   text;
  ev_sess   text;
  ev_props  jsonb;
  recent    bigint;
  uid       uuid;
  salt_v    text;
  acct_id   text;
begin
  if p_batch is null or jsonb_typeof(p_batch) <> 'array' then
    return 0;                                  -- malformed input is dropped, never raised: a
  end if;                                      -- analytics call must not break the page it is on
  if jsonb_array_length(p_batch) = 0 then return 0; end if;
  if jsonb_array_length(p_batch) > 60 then return 0; end if;

  who_id := left(coalesce(p_batch->0->>'who', ''), 32);
  if who_id !~ '^[0-9a-f]{16,32}$' then
    return 0;                                  -- not a pseudonym this app produced
  end if;

  -- See the header for why these moved. They are a guard rail, not a throttle: the client samples.
  select count(*) into recent from public.events where at > now() - interval '1 hour';
  if recent > 40000 then return 0; end if;

  select count(*) into recent from public.events
   where who = who_id and at > now() - interval '1 day';
  if recent > 6000 then return 0; end if;

  -- sec-picks-2026-10-16: a signed-in student is counted by a salted hash of their account id.
  -- Signed-out visitors still log (acct stays null) but never count toward "trending".
  uid := auth.uid();
  if uid is not null then
    select s.salt into salt_v from public.event_salt s where s.id;
    -- no salt row = no hash: acct stays null (never an unsalted fallback)
    if salt_v is not null and salt_v <> '' then
      acct_id := left(encode(sha256(convert_to(salt_v || ':' || uid::text, 'UTF8')), 'hex'), 32);
    end if;
  end if;

  for e in select * from jsonb_array_elements(p_batch)
  loop
    ev_name := left(coalesce(e->>'name',''), 40);
    if ev_name = '' then continue; end if;

    -- A session id this app produced, or nothing. Anything else is discarded rather than stored,
    -- because an unvalidated free-text column is how a analytics table becomes a place to put
    -- things that should not be in it.
    ev_sess := left(coalesce(e->>'session',''), 32);
    if ev_sess !~ '^[0-9a-z]{8,32}$' then ev_sess := null; end if;

    -- props is capped hard. It is a bag for small facts — a label, a count, a depth — and not a
    -- place for page text, a search query someone typed, or anything else that would turn an
    -- anonymous event stream into a record of what a named-ish browser read.
    ev_props := case when jsonb_typeof(e->'props') = 'object'
                       and length(e->>'props') <= 600
                     then e->'props' else null end;

    insert into public.events(name, subject, surface, who, props, session, acct)
    values (ev_name,
            left(nullif(e->>'subject',''), 160),
            left(nullif(e->>'surface',''), 40),
            who_id,
            ev_props,
            ev_sess,
            acct_id);
    n := n + 1;
  end loop;

  if random() < 0.02 then
    delete from public.events where at < now() - interval '30 days';
    -- sec-picks-2026-10-16: the account hash is only needed for the 7-day trending window
    update public.events set acct = null where acct is not null and at < now() - interval '8 days';
    delete from public.events
     where id < (select max(id) - 1000000 from public.events);
  end if;

  return n;
end;
$function$;

-- ---------- 4. Groups: only the creator deletes a group or removes others ----------
revoke update on public.groups from public, anon, authenticated;
grant  update (name) on public.groups to authenticated;     -- updated_at is set by the BEFORE UPDATE trigger
drop policy if exists groups_delete_members on public.groups;
drop policy if exists groups_delete_creator on public.groups;
create policy groups_delete_creator on public.groups for delete to authenticated
  using (created_by = auth.uid());
drop policy if exists gm_delete_members on public.group_members;
drop policy if exists gm_delete_self_or_creator on public.group_members;
create policy gm_delete_self_or_creator on public.group_members for delete to authenticated
  using (user_id = auth.uid()
         or exists (select 1 from public.groups g where g.id = group_id and g.created_by = auth.uid()));

-- ---------- 6. Word-filter lists: students can use the checkers, not read the lists ----------
alter function public.wf_hit(text)       security definer set search_path = public;
alter function public.wf_hit_tight(text) security definer set search_path = public;
alter function public.wf_reserved(text)  security definer set search_path = public;
alter function public.wf_slur_hit(text)  security definer set search_path = public;
revoke execute on function public.wf_words(), public.wf_words_tight(), public.wf_slurs(), public.wf_reserved_usernames()
  from public, anon, authenticated;

-- ---------- 7. Push sign-up: re-subscribe works; the endpoint follows whoever is signed in ----------
drop policy if exists push_subs_own_update on public.push_subscriptions;
create policy push_subs_own_update on public.push_subscriptions for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
-- A student may change only the fields the website sends; delivery bookkeeping (last_ok_at, fail_count)
-- stays server-side.
revoke update on public.push_subscriptions from public, anon, authenticated;
grant  update (user_id, endpoint, p256dh, auth, ua) on public.push_subscriptions to authenticated;

create or replace function public.claim_push_subscription(p_endpoint text, p_p256dh text, p_auth text, p_ua text)
returns void
language plpgsql
security definer
set search_path = public
as $fn$
declare uid uuid := auth.uid();
begin
  if uid is null then
    raise exception 'sign in first' using errcode = '28000';
  end if;
  if p_endpoint is null or p_endpoint = '' or p_p256dh is null or p_auth is null
     or length(p_p256dh) > 200 or length(p_auth) > 100 or length(coalesce(p_ua, '')) > 300 then
    raise exception 'incomplete or oversized push subscription' using errcode = '22023';
  end if;
  -- the same rule as the push_subs_endpoint_is_push_service CHECK, enforced here too so the function is safe even where that CHECK is missing
  if length(p_endpoint) > 2048
     or p_endpoint !~* '^https://(fcm\.googleapis\.com|updates\.push\.services\.mozilla\.com|web\.push\.apple\.com|([a-z0-9-]+\.)+push\.apple\.com|([a-z0-9-]+\.)+notify\.windows\.com)/[^\s\\]*$' then
    raise exception 'not a push-service address' using errcode = '22023';
  end if;
  if (select count(*) from public.push_subscriptions where user_id = uid and endpoint <> p_endpoint) >= 10 then
    raise exception 'too many notification subscriptions on this account' using errcode = '54000';
  end if;
  -- the same browser, previously used by another account: it belongs to whoever is signed in now
  delete from public.push_subscriptions where endpoint = p_endpoint and user_id is distinct from uid;
  -- the push_subs_endpoint_is_push_service CHECK still applies to this insert
  insert into public.push_subscriptions (user_id, endpoint, p256dh, auth, ua)
  values (uid, p_endpoint, p_p256dh, p_auth, p_ua)
  on conflict (endpoint) do update
     set user_id = excluded.user_id, p256dh = excluded.p256dh, auth = excluded.auth, ua = excluded.ua,
         fail_count = 0;
end $fn$;
revoke all on function public.claim_push_subscription(text, text, text, text) from public, anon;
grant execute on function public.claim_push_subscription(text, text, text, text) to authenticated;

-- ---------- 8. Account deletion also removes schedule-card images ----------
CREATE OR REPLACE FUNCTION public.purge_due_account_deletions()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare r record; n int := 0; addr text;
begin
  for r in select * from public.account_deletions where purge_after <= now() order by purge_after for update skip locked loop
    -- a recovery that landed after the list was read wins
    if not exists (select 1 from public.account_deletions d where d.user_id = r.user_id and d.purge_after <= now()) then continue; end if;
    begin
      select u.email into addr from auth.users u where u.id = r.user_id;   -- read before the account goes
      -- delete_my_account() works on auth.uid(); act as that one account, inside this block only
      perform set_config('request.jwt.claim.sub', r.user_id::text, true);
      perform set_config('request.jwt.claims', json_build_object('sub', r.user_id, 'role', 'authenticated')::text, true);
      -- The app removes the photo through the Storage API when the deletion is asked for. Anything
      -- left is cleared here as a backstop: Supabase refuses SQL deletes on storage unless
      -- storage.allow_delete_query is set, and this step may never block the deletion itself.
      begin
        perform set_config('storage.allow_delete_query', 'true', true);
        delete from storage.objects where bucket_id = 'avatars' and name like r.user_id::text || '/%';
        perform set_config('storage.allow_delete_query', 'false', true);
      exception when others then
        perform set_config('storage.allow_delete_query', 'false', true);
        raise warning 'avatars cleanup for % failed: %', r.user_id, sqlerrm;   -- sec-picks-2026-10-16: said out loud, still never blocks the deletion
      end;
      -- sec-picks-2026-10-16: the schedule cards (PNG + JSON share images) a student uploaded went on
      -- living in a public bucket after the account was gone. Same pattern as the avatars, its own
      -- block so one failure cannot skip the other, and BEFORE the account (and the email step) so
      -- it runs for every account, with or without an email address.
      begin
        perform set_config('storage.allow_delete_query', 'true', true);
        delete from storage.objects where bucket_id = 'schedule-cards' and owner = r.user_id;
        perform set_config('storage.allow_delete_query', 'false', true);
      exception when others then
        perform set_config('storage.allow_delete_query', 'false', true);
        raise warning 'schedule-cards cleanup for % failed: %', r.user_id, sqlerrm;
      end;
      perform public.delete_my_account_v2(r.delete_reviews);   -- the account_deletions row goes with auth.users
      -- queued only now, inside the same block: a deletion that failed sends no "deleted" email
      if addr is not null and addr <> '' then
        begin
          insert into public.account_emails (kind, user_id, email, detail)
          values ('deleted', r.user_id, addr, jsonb_build_object('delete_reviews', r.delete_reviews, 'requested_at', r.requested_at));
        exception when others then null;   -- the email is never a reason to undo a deletion
        end;
      end if;
      n := n + 1;
    exception when others then
      -- one account that fails never blocks the rest; it is retried tomorrow and the reason kept
      update public.account_deletions set attempts = attempts + 1, last_error = left(sqlerrm, 500)
       where user_id = r.user_id;
    end;
  end loop;
  perform set_config('request.jwt.claim.sub', '', true);
  perform set_config('request.jwt.claims', '', true);
  return n;
end $function$;

-- ---------- 3 (continued) and 5. The two statements that take a lock on a busy table, kept for last so the lock is held only briefly ----------
-- (log_events above is plpgsql, so it only needs the acct column when it runs, not when it is created)
alter table public.events add column if not exists acct text;
do $$
begin
  if not exists (select 1 from pg_constraint where conrelid = 'public.events'::regclass and conname = 'len_events_acct') then
    alter table public.events add constraint len_events_acct check (length(acct) <= 64) not valid;   -- guards new rows; no full scan of events
  end if;
end $$;

-- Same columns and types as before; only "viewers" now counts distinct signed-in accounts.
create or replace view public.prof_activity_7d as
 select subject as prof_key,
        count(distinct acct) filter (where name = 'prof_view' and acct is not null) as viewers,
        count(distinct who)  filter (where name = 'prof_impression') as shown
   from public.events
  where at > now() - interval '7 days'
    and subject is not null
    and name in ('prof_view', 'prof_impression')
  group by subject;
comment on view public.prof_activity_7d is
  'sec-picks-2026-10-16: viewers = distinct SIGNED-IN accounts (events.acct, salted hash) that viewed the professor in the last 7 days; shown = distinct browsers that saw the professor in a list. Read only through trending_profs(), which keeps a floor of 3.';

do $$
begin
  if not exists (select 1 from pg_constraint where conrelid = 'public.messages'::regclass and conname = 'len_messages_payload') then
    alter table public.messages add constraint len_messages_payload
      check (length(payload::text) <= 2000) not valid;     -- guards every new row at once; no scan
  end if;
  if exists (select 1 from pg_constraint where conrelid = 'public.messages'::regclass and conname = 'len_messages_payload' and not convalidated) then
    begin
      alter table public.messages validate constraint len_messages_payload;
    exception when others then
      raise notice 'messages.payload: could not validate the 2000-character cap (%); it guards new rows but stays NOT VALID until old rows are cleaned up', sqlerrm;
    end;
  end if;
end $$;

notify pgrst, 'reload schema';

-- ---------- Self-check: raises (and so rolls everything back) if anything above did not take ----------
do $$
declare src text; r text;
begin
  -- 1
  src := (select prosrc from pg_proc where oid = 'public.suggest_classmates_v2__incl_pending()'::regprocedure);
  if position('''{}''::text[] as codes' in src) = 0 or position('h.codes' in replace(src, 'cardinality(h.codes)', '')) > 0 then
    raise exception 'self-check 1: classmates v2 still returns codes'; end if;
  if position('p.school = (select school from me)' in src) = 0 then raise exception 'self-check 1: classmates wall lost'; end if;
  if position('null::text[] as shared_codes' in (select prosrc from pg_proc where oid = 'public.suggest_friends_unscoped__incl_pending(integer)'::regprocedure)) = 0 then
    raise exception 'self-check 1: suggest_friends_unscoped__incl_pending still returns shared_codes'; end if;
  -- 2
  src := (select prosrc from pg_proc where oid = 'public.report_alert_body(uuid,text)'::regprocedure);
  if position('The review''''s author (open the report queue to see who)' in src) = 0 or position('who := null; uname := null' in src) = 0 then
    raise exception 'self-check 2: report_alert_body still names a review author'; end if;
  -- tolerant of the sender cron rebuilding a body at the same moment: a rebuilt body carries the anonymous wording
  if exists (select 1 from public.report_alerts a join public.reports x on x.id = a.report_id
              where x.kind = 'review' and a.html is not null
                and a.html like '%>About</td>%' and a.html not like '%The review''s author (open the report queue to see who)%') then
    raise exception 'self-check 2: an old review-report email body (naming the author) is still stored'; end if;
  -- 3
  if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='events' and column_name='acct') then
    raise exception 'self-check 3: events.acct missing'; end if;
  if position('acct IS NOT NULL' in pg_get_viewdef('public.prof_activity_7d'::regclass, true)) = 0 then
    raise exception 'self-check 3: prof_activity_7d does not count accounts'; end if;
  if (select string_agg(a.attname || ':' || format_type(a.atttypid, null), ',' order by a.attnum)
        from pg_attribute a where a.attrelid = 'public.prof_activity_7d'::regclass and a.attnum > 0 and not a.attisdropped)
     <> 'prof_key:text,viewers:bigint,shown:bigint' then raise exception 'self-check 3: prof_activity_7d columns changed'; end if;
  if position('acct' in (select prosrc from pg_proc where oid = 'public.log_events(jsonb)'::regprocedure)) = 0 then
    raise exception 'self-check 3: log_events does not fill acct'; end if;
  if position('greatest(coalesce(p_min, 5), 3)' in (select prosrc from pg_proc where oid = 'public.trending_profs(integer,integer)'::regprocedure)) = 0 then
    raise exception 'self-check 3: trending_profs lost its floor of 3'; end if;
  foreach r in array array['anon', 'authenticated'] loop
    if has_table_privilege(r, 'public.events', 'SELECT') or has_table_privilege(r, 'public.prof_activity_7d', 'SELECT')
       or has_table_privilege(r, 'public.event_salt', 'SELECT') then
      raise exception 'self-check 3: % can read events / prof_activity_7d / event_salt', r; end if;
  end loop;
  if not has_function_privilege('anon', 'public.log_events(jsonb)', 'EXECUTE') then
    raise exception 'self-check 3: signed-out visitors can no longer log events'; end if;
  -- 4
  if exists (select 1 from pg_policies where tablename in ('groups','group_members') and policyname in ('groups_delete_members','gm_delete_members')) then
    raise exception 'self-check 4: member-wide delete policy still present'; end if;
  if exists (select 1 from pg_policies where schemaname='public' and tablename in ('groups','group_members') and cmd in ('DELETE','ALL')
             and policyname not in ('groups_delete_creator','gm_delete_self_or_creator')) then
    raise exception 'self-check 4: another DELETE policy on groups / group_members still lets members delete'; end if;
  if not exists (select 1 from pg_policies where tablename='groups' and policyname='groups_delete_creator')
     or not exists (select 1 from pg_policies where tablename='group_members' and policyname='gm_delete_self_or_creator') then
    raise exception 'self-check 4: creator-only delete policies missing'; end if;
  if has_column_privilege('authenticated', 'public.groups', 'created_by', 'UPDATE')
     or has_column_privilege('authenticated', 'public.groups', 'id', 'UPDATE') then
    raise exception 'self-check 4: members can still rewrite created_by'; end if;
  if not has_column_privilege('authenticated', 'public.groups', 'name', 'UPDATE') then
    raise exception 'self-check 4: members can no longer rename'; end if;
  -- 5
  if not exists (select 1 from pg_constraint where conrelid='public.messages'::regclass and conname='len_messages_payload') then
    raise exception 'self-check 5: payload cap missing'; end if;
  -- 6
  if exists (select 1 from pg_proc where oid in ('public.wf_hit(text)'::regprocedure, 'public.wf_hit_tight(text)'::regprocedure,
        'public.wf_reserved(text)'::regprocedure, 'public.wf_slur_hit(text)'::regprocedure) and not prosecdef) then
    raise exception 'self-check 6: a wf_ checker is not security definer'; end if;
  foreach r in array array['wf_words()', 'wf_words_tight()', 'wf_slurs()', 'wf_reserved_usernames()'] loop
    if has_function_privilege('authenticated', ('public.' || r)::regprocedure, 'EXECUTE')
       or has_function_privilege('anon', ('public.' || r)::regprocedure, 'EXECUTE') then
      raise exception 'self-check 6: students can still read %', r; end if;
  end loop;
  if not has_function_privilege('authenticated', 'public.wf_hit(text)', 'EXECUTE') then
    raise exception 'self-check 6: the filter triggers would fail for students'; end if;
  -- 7
  if not exists (select 1 from pg_policies where tablename='push_subscriptions' and policyname='push_subs_own_update') then
    raise exception 'self-check 7: push update policy missing'; end if;
  if not has_function_privilege('authenticated', 'public.claim_push_subscription(text,text,text,text)', 'EXECUTE')
     or has_function_privilege('anon', 'public.claim_push_subscription(text,text,text,text)', 'EXECUTE') then
    raise exception 'self-check 7: claim_push_subscription grants wrong'; end if;
  if not exists (select 1 from pg_constraint where conrelid='public.push_subscriptions'::regclass and conname='push_subs_endpoint_is_push_service') then
    raise notice 'self-check 7: push_subs_endpoint_is_push_service is not on this database (run professify-security-push-endpoint.sql)'; end if;
  -- 8
  src := (select prosrc from pg_proc where oid = 'public.purge_due_account_deletions()'::regprocedure);
  if position('schedule-cards' in src) = 0 or position('avatars' in src) = 0
     or position('schedule-cards' in src) > position('delete_my_account_v2' in src)
     or position('avatars' in src) > position('delete_my_account_v2' in src) then
    raise exception 'self-check 8: account purge does not clear both buckets before the account is deleted'; end if;
  if not exists (select 1 from pg_trigger where tgrelid = 'public.reports'::regclass and tgname = 'report_alerts_on_report') then
    raise notice 'NOTE: trigger report_alerts_on_report is not on public.reports in this database, so new-report emails are not queued here (professify-report-alerts.sql creates it)';
  end if;
  raise notice 'security picks 2026-10-16: all self-checks passed';
end $$;

commit;

-- =================================================================================================
-- ROLLBACK NOTES (only if something real breaks; each line undoes one step)
--   1. re-create suggest_classmates_v2__incl_pending / suggest_friends_unscoped__incl_pending with
--      `h.codes` / `s.codes as shared_codes` (bodies are in professify-security-hotfix-2026-10-14.sql
--      and the 2026-10-15 catalog snapshot)
--   2. re-create report_alert_body without the two sec-picks lines (stored bodies are gone for good)
--   3. re-create prof_activity_7d with count(distinct who) filter (where name = 'prof_view') AS viewers;
--      log_events can keep filling acct (harmless); alter table public.events drop column acct;
--   4. create policy groups_delete_members on public.groups for delete to authenticated using (is_group_member(id, auth.uid()));
--      create policy gm_delete_members on public.group_members for delete to authenticated using (user_id = auth.uid() or is_group_member(group_id, auth.uid()));
--      grant update on public.groups to authenticated;
--   5. alter table public.messages drop constraint len_messages_payload;
--   6. alter function public.wf_hit(text) security invoker; (same for wf_hit_tight, wf_reserved, wf_slur_hit)
--      grant execute on function public.wf_words(), public.wf_words_tight(), public.wf_slurs(), public.wf_reserved_usernames() to authenticated;
--   7. drop function public.claim_push_subscription(text,text,text,text); drop policy push_subs_own_update on public.push_subscriptions;
--      grant update on public.push_subscriptions to authenticated;   (restores the old table-wide UPDATE grant)
--   8. re-create purge_due_account_deletions() without the schedule-cards block
-- =================================================================================================
