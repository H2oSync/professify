-- ================================================================================================
-- APP STORE REVIEW DEMO ACCOUNT — 6 October 2026 (plans moved to Spring 2027 on 13 October 2026)
-- ================================================================================================
-- Apple's reviewer is not a Cal Poly student, and the app is only useful once you have friends and
-- classes. This gives the reviewer an account that shows every screen working — WITHOUT showing a
-- single real student. Every person in it is made up; every class is a real section read from
-- course_seats (real data only, per CONTRIBUTING.md): their weeks are Fall 2026 (the term they're in,
-- CFG.NOW_TERM) and their plans are Spring 2027 (the term the app plans for, CFG.TERM = 2274). Before
-- 2026-10-13 the plans were Fall sections, which the Spring app never reads — Plans looked empty.
--
-- WHAT IT DOES NOT DO: write any review. A made-up review of a real professor would be a fabricated
-- rating on the public site. The reviewer sees the real public reviews like anyone else.
--
-- BEFORE RUNNING: create these five users in Supabase → Authentication → Users → Add user →
-- "Create new user", each with a password and "Auto Confirm User" ticked (so no email is sent):
--
--   reviewer@appreview.calpoly.edu   ← the login you give Apple
--   alex@appreview.calpoly.edu
--   priya@appreview.calpoly.edu
--   jordan@appreview.calpoly.edu
--   maya@appreview.calpoly.edu
--
-- WHY THAT DOMAIN. Sign-in is only open to Cal Poly addresses, enforced in the database
-- (school_from_email) and the app (schoolForEmail), and both accept a subdomain of calpoly.edu.
-- `appreview.calpoly.edu` is a subdomain no real student has, so these can never collide with a
-- real account, and no mail is ever sent to them (password sign-in, auto-confirmed).
--
-- All-or-nothing: it is one DO block, so if anything fails nothing is written, and the error says
-- what. Safe to re-run: it clears the demo accounts' own rows first. It never touches any account
-- outside the five above.
--
-- TO REMOVE AFTER APPROVAL (optional): delete the five users in Authentication → Users. Every row
-- here cascades away with them.
-- ================================================================================================
do $$
declare
  v_term constant text := '2268';                     -- CFG.NOW_TERM, Fall 2026: the week people are sitting in
  v_plan_term constant text := '2274';                -- CFG.TERM, Spring 2027: what Plans read since 2026-10-08
  people jsonb := '[
    {"email":"reviewer@appreview.calpoly.edu","name":"Riley Demo","username":"riley_demo","major":"Business Administration","standing":"Junior",
     "classes":["BUS 3431","BUS 3438","ENGL 3310","BUS 4401"]},
    {"email":"alex@appreview.calpoly.edu","name":"Alex Rivera","username":"alex_rivera_demo","major":"Business Administration","standing":"Junior",
     "classes":["BUS 3431","BUS 4442","BUS 4445","ENGL 3310"]},
    {"email":"priya@appreview.calpoly.edu","name":"Priya Shah","username":"priya_shah_demo","major":"Psychology","standing":"Sophomore",
     "classes":["PSY 3333","PSY 3323","BIO 3312","ENGL 3310"]},
    {"email":"jordan@appreview.calpoly.edu","name":"Jordan Lee","username":"jordan_lee_demo","major":"Mechanical Engineering","standing":"Senior",
     "classes":["ME 2240","PHYS 4405","AERO 4433","KINE 1141"]},
    {"email":"maya@appreview.calpoly.edu","name":"Maya Thompson","username":"maya_t_demo","major":"Business Administration","standing":"Senior",
     "classes":["BUS 4401","BUS 3443","PHIL 3331","BUS 3438"]}
  ]'::jsonb;
  p      jsonb;
  ids    uuid[] := '{}';
  uid    uuid;
  me     uuid;
  v_code text;
  s      record;
  n      int;
  cid    uuid;
  missing text := '';
begin
  -- ---- 0. the five accounts must exist ------------------------------------------------------------
  for p in select * from jsonb_array_elements(people) loop
    select id into uid from auth.users where lower(email) = p->>'email';
    if uid is null then missing := missing || ' ' || (p->>'email'); end if;
    ids := ids || uid;
  end loop;
  if missing <> '' then
    raise exception 'Create these users first (Authentication → Users → Add user, Auto Confirm):%', missing;
  end if;
  me := ids[1];

  -- ---- 1. start clean: only these five accounts' rows ---------------------------------------------
  delete from public.conversations c
   where exists (select 1 from public.conversation_members m where m.conversation_id = c.id and m.user_id = any(ids))
     and not exists (select 1 from public.conversation_members m where m.conversation_id = c.id and not (m.user_id = any(ids)));
  -- Blocking someone (as the review video does) ends the friendship, and unblocking doesn't bring it
  -- back. Clear blocks and hidden suggestions between these five so a re-run restores everything.
  if to_regclass('public.blocks') is not null then
    execute 'delete from public.blocks where blocker = any($1) and blocked = any($1)' using ids;
  end if;
  if to_regclass('public.friend_suggestion_dismissals') is not null then
    execute 'delete from public.friend_suggestion_dismissals where user_id = any($1) and dismissed_id = any($1)' using ids;
  end if;
  delete from public.friend_requests where from_user = any(ids) or to_user = any(ids);
  delete from public.my_sections   where user_id = any(ids);
  delete from public.saved_classes where user_id = any(ids);
  delete from public.plans         where user_id = any(ids);

  -- ---- 2. profiles, classes -----------------------------------------------------------------------
  for i in 1..jsonb_array_length(people) loop
    p := people->(i-1); uid := ids[i];
    perform set_config('request.jwt.claims',
      json_build_object('sub', uid, 'email', p->>'email', 'role', 'authenticated')::text, true);
    perform set_config('request.jwt.claim.sub', uid::text, true);

    insert into public.profiles (id, edu_email, display_name, username, major, class_standing)
    values (uid, p->>'email', p->>'name', p->>'username', p->>'major', p->>'standing')
    on conflict (id) do update set display_name = excluded.display_name, username = excluded.username,
      major = excluded.major, class_standing = excluded.class_standing, avatar_url = null;

    n := 0;
    for v_code in select jsonb_array_elements_text(p->'classes') loop
      select cs.class_nbr, cs.section, cs.instructor, cs.days into s
        from public.course_seats cs
       where cs.term = v_term and upper(cs.course_code) = upper(v_code) and coalesce(cs.days,'') <> ''
       order by cs.section nulls last, cs.class_nbr
       limit 1;
      if not found then continue; end if;
      insert into public.saved_classes (user_id, term, code) values (uid, v_term, v_code) on conflict do nothing;
      insert into public.my_sections (user_id, term, code, class_nbr, section, instructor, days, status, wl_pos)
      values (uid, v_term, v_code, s.class_nbr::text, s.section, s.instructor, s.days, 'enrolled', null)
      on conflict do nothing;
      n := n + 1;
    end loop;
    if n < 2 then
      raise exception 'Only % of %''s classes are in course_seats for term %. Edit the "classes" list at the top to codes that are offered this term.', n, p->>'name', v_term;
    end if;
  end loop;

  -- ---- 3. friendships: the reviewer is friends with all four (sent pending, then accepted — the
  --         same two steps the app takes, so the "pending only" insert rule is respected) -----------
  for i in 2..array_length(ids,1) loop
    perform set_config('request.jwt.claims', json_build_object('sub', ids[i], 'role', 'authenticated',
      'email', people->(i-1)->>'email')::text, true);
    perform set_config('request.jwt.claim.sub', ids[i]::text, true);
    insert into public.friend_requests (from_user, to_user, status) values (ids[i], me, 'pending');
    perform set_config('request.jwt.claims', json_build_object('sub', me, 'role', 'authenticated',
      'email', people->0->>'email')::text, true);
    perform set_config('request.jwt.claim.sub', me::text, true);
    update public.friend_requests set status = 'accepted' where from_user = ids[i] and to_user = me;
  end loop;
  -- Alex and Maya know each other too, so "classes your friends are taking" has overlap
  perform set_config('request.jwt.claims', json_build_object('sub', ids[2], 'role', 'authenticated',
    'email', people->1->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', ids[2]::text, true);
  insert into public.friend_requests (from_user, to_user, status) values (ids[2], ids[5], 'pending');
  perform set_config('request.jwt.claims', json_build_object('sub', ids[5], 'role', 'authenticated',
    'email', people->4->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', ids[5]::text, true);
  update public.friend_requests set status = 'accepted' where from_user = ids[2] and to_user = ids[5];

  -- ---- 4. one chat, so the Friends tab shows messaging (and its ⋯ Report / Block) ----------------
  perform set_config('request.jwt.claims', json_build_object('sub', ids[2], 'role', 'authenticated',
    'email', people->1->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', ids[2]::text, true);
  insert into public.conversations (kind, created_by) values ('direct', ids[2]) returning id into cid;
  insert into public.conversation_members (conversation_id, user_id) values (cid, ids[2]), (cid, me);
  insert into public.messages (conversation_id, sender, kind, body, created_at)
  values (cid, ids[2], 'text', 'Are you taking BUS 3431 this term? Want to study for the first midterm together?', now() - interval '3 hours');
  perform set_config('request.jwt.claims', json_build_object('sub', me, 'role', 'authenticated',
    'email', people->0->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', me::text, true);
  insert into public.messages (conversation_id, sender, kind, body, created_at)
  values (cid, me, 'text', 'Yes! Library after class on Thursday?', now() - interval '2 hours 50 minutes');

  -- ---- 5. a group chat Alex made (so a group's people, Leave group and "Report the name" show) ------
  --         (added 2026-10-07 for App Review: the reviewer's Friends tab had one chat and no group)
  perform set_config('request.jwt.claims', json_build_object('sub', ids[2], 'role', 'authenticated',
    'email', people->1->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', ids[2]::text, true);
  insert into public.conversations (kind, title, created_by) values ('group', 'BUS 3431 study group', ids[2]) returning id into cid;
  insert into public.conversation_members (conversation_id, user_id) values (cid, ids[2]), (cid, me), (cid, ids[5]);
  insert into public.messages (conversation_id, sender, kind, body, created_at)
  values (cid, ids[2], 'text', 'Made a group for the midterm. Thursday 4pm at the library?', now() - interval '40 minutes');
  perform set_config('request.jwt.claims', json_build_object('sub', ids[5], 'role', 'authenticated',
    'email', people->4->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', ids[5]::text, true);
  insert into public.messages (conversation_id, sender, kind, body, created_at)
  values (cid, ids[5], 'text', 'Works for me. I''ll bring the practice exam.', now() - interval '25 minutes');

  -- ---- 6. plans, so Schedule › Plans isn't empty: the reviewer's Plan A and B, and Jordan's shared
  --         Plan A (a friend's plan shows on his page). SPRING 2027 sections (CFG.TERM): the phone reads
  --         plans only for that term. Each entry names a real section checked on 2026-10-13 so a plan
  --         has no clashes (A: MoWe 9:00 · 2:00 · 4:30, TuTh 10:00; B: TuTh 9:00 · 12:00, Th 10:30,
  --         MoWe 12:00); if that class number is gone, the class's first timed section stands in. ---
  for i in 1..3 loop
    declare
      who   uuid := case i when 3 then ids[4] else me end;
      slot_ text := case i when 2 then 'B' else 'A' end;
      picks text[] := case i when 1 then array['BUS 3431:4023','BUS 3438:4010','BUS 4401:4165','PHIL 3331:6785']
                             when 2 then array['BUS 4442:9285','ENGL 3310:6414','BUS 3431:8534','BUS 3438:4009']
                             else array['ME 2240:7110','PHYS 4405:1589'] end;
      pick  text;
      v_nbr text;
      secs  jsonb := '[]'::jsonb;
    begin
      foreach pick in array picks loop
        v_code := split_part(pick, ':', 1); v_nbr := split_part(pick, ':', 2);
        select cs.class_nbr into s from public.course_seats cs
         where cs.term = v_plan_term and upper(cs.course_code) = upper(v_code) and cs.class_nbr::text = v_nbr;
        if not found then
          select cs.class_nbr into s from public.course_seats cs
           where cs.term = v_plan_term and upper(cs.course_code) = upper(v_code) and coalesce(cs.days,'') <> ''
             and cs.days !~* 'TBA'
           order by cs.section nulls last, cs.class_nbr limit 1;
        end if;
        if found then secs := secs || jsonb_build_array(jsonb_build_object('code', v_code, 'class_nbr', s.class_nbr::text)); end if;
      end loop;
      if jsonb_array_length(secs) < 2 then
        raise exception 'Only % Spring 2027 sections found for Plan % — is term % in course_seats?', jsonb_array_length(secs), slot_, v_plan_term;
      end if;
      insert into public.plans (user_id, term, slot, sections, shared) values (who, v_plan_term, slot_, secs, true)
      on conflict (user_id, term, slot) do update set sections = excluded.sections, shared = true;
    end;
  end loop;

  raise notice 'Demo ready: reviewer@appreview.calpoly.edu has 4 friends, % Fall 2026 sections, % Spring 2027 plans, a 1:1 chat and a group chat.',
    (select count(*) from public.my_sections where user_id = me and term = v_term),
    (select count(*) from public.plans where user_id = me and term = v_plan_term);
end $$;

-- Check (read-only): five profiles, the reviewer's friends and classes.
select p.display_name, p.edu_email, p.school,
       (select count(*) from public.my_sections ms where ms.user_id = p.id and ms.term = '2268') as sections,
       (select count(*) from public.friend_requests f where (f.from_user = p.id or f.to_user = p.id) and f.status = 'accepted') as friends
  from public.profiles p
 where p.edu_email like '%@appreview.calpoly.edu'
 order by p.edu_email;
