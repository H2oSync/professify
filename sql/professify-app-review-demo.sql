-- ================================================================================================
-- APP STORE REVIEW DEMO ACCOUNT — 6 October 2026
-- ================================================================================================
-- Apple's reviewer is not a Cal Poly student, and the app is only useful once you have friends and
-- classes. This gives the reviewer an account that shows every screen working — WITHOUT showing a
-- single real student. Every person in it is made up; every class is a real Fall 2026 section read
-- from course_seats (real data only, per CONTRIBUTING.md).
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
  v_term constant text := '2268';                     -- CFG.TERM, Fall 2026
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
  delete from public.friend_requests where from_user = any(ids) or to_user = any(ids);
  delete from public.my_sections   where user_id = any(ids);
  delete from public.saved_classes where user_id = any(ids);

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
  insert into public.messages (conversation_id, sender, kind, body)
  values (cid, ids[2], 'text', 'Are you taking BUS 3431 this term? Want to study for the first midterm together?');
  perform set_config('request.jwt.claims', json_build_object('sub', me, 'role', 'authenticated',
    'email', people->0->>'email')::text, true);
  perform set_config('request.jwt.claim.sub', me::text, true);
  insert into public.messages (conversation_id, sender, kind, body)
  values (cid, me, 'text', 'Yes! Library after class on Thursday?');

  raise notice 'Demo ready: reviewer@appreview.calpoly.edu has 4 friends, % sections, and 1 chat.',
    (select count(*) from public.my_sections where user_id = me);
end $$;

-- Check (read-only): five profiles, the reviewer's friends and classes.
select p.display_name, p.edu_email, p.school,
       (select count(*) from public.my_sections ms where ms.user_id = p.id and ms.term = '2268') as sections,
       (select count(*) from public.friend_requests f where (f.from_user = p.id or f.to_user = p.id) and f.status = 'accepted') as friends
  from public.profiles p
 where p.edu_email like '%@appreview.calpoly.edu'
 order by p.edu_email;
