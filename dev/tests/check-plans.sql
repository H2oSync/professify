-- Run: psql -v ON_ERROR_STOP=1 -f fixture-plans.sql -f ../sql/professify-plans.sql -f check-plans.sql
-- Every check raises on failure. RLS is exercised as the real 'authenticated' role, never as the
-- superuser (which bypasses it). Each block sets its own identity rather than inheriting one.
\set ON_ERROR_STOP on
\set QUIET on
reset role;
create schema if not exists t;
grant usage on schema t to authenticated, anon;
create or replace function t.ok(cond boolean, label text) returns void language plpgsql as $$
begin if coalesce(cond, false) then raise notice '  ok   %', label; else raise exception 'FAIL %', label; end if; end $$;
create or replace function t.be(u text) returns void language plpgsql as $$
begin perform set_config('request.jwt.claim.sub', u, false); end $$;
create or replace function t.fails(sql text, label text) returns void language plpgsql as $$
begin
  begin execute sql; exception when others then raise notice '  ok   % (%)', label, sqlerrm; return; end;
  raise exception 'FAIL % — it was allowed', label;
end $$;
grant execute on all functions in schema t to authenticated, anon;

truncate public.plans, public.watch_sections, public.friend_requests, public.suspensions;
delete from public.profiles; delete from auth.users;
insert into auth.users (id, email) values
  ('aaaaaaaa-0000-0000-0000-000000000001','a@calpoly.edu'),   -- A: me
  ('aaaaaaaa-0000-0000-0000-000000000002','f@calpoly.edu'),   -- F: A's accepted friend
  ('aaaaaaaa-0000-0000-0000-000000000003','s@calpoly.edu'),   -- S: stranger, same school
  ('aaaaaaaa-0000-0000-0000-000000000004','u@ucsb.edu'),      -- U: other school
  ('aaaaaaaa-0000-0000-0000-000000000005','p@calpoly.edu'),   -- P: pending request from A
  ('aaaaaaaa-0000-0000-0000-000000000006','z@calpoly.edu');   -- Z: suspended
insert into public.profiles (id, school) values
  ('aaaaaaaa-0000-0000-0000-000000000001','calpoly'), ('aaaaaaaa-0000-0000-0000-000000000002','calpoly'),
  ('aaaaaaaa-0000-0000-0000-000000000003','calpoly'), ('aaaaaaaa-0000-0000-0000-000000000004','ucsb'),
  ('aaaaaaaa-0000-0000-0000-000000000005','calpoly'), ('aaaaaaaa-0000-0000-0000-000000000006','calpoly');
insert into public.friend_requests values
  ('aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000002','accepted'),
  ('aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000005','pending'),
  ('aaaaaaaa-0000-0000-0000-000000000004','aaaaaaaa-0000-0000-0000-000000000001','accepted'); -- pre-wall cross-school friendship
insert into public.suspensions values ('aaaaaaaa-0000-0000-0000-000000000006', null);

set role authenticated;

-- ---- writing your own plan ---------------------------------------------------------------------
select t.be('aaaaaaaa-0000-0000-0000-000000000001');
insert into public.plans (term, slot, sections) values
  ('2274','A','[{"code":"bus 4442","class_nbr":" 11111","junk":"x"},{"code":"ECON 2001","class_nbr":"22222"},{"code":"HIST 2230","class_nbr":"33333"}]');
select t.ok((select sections from public.plans where slot='A') =
  '[{"code":"BUS 4442","class_nbr":"11111"},{"code":"ECON 2001","class_nbr":"22222"},{"code":"HIST 2230","class_nbr":"33333"}]'::jsonb,
  'sections are normalised to {code, class_nbr}: upper-cased, trimmed, extra keys dropped');
select t.ok((select shared and user_id = auth.uid() from public.plans where slot='A'), 'shared defaults to true; user_id defaults to the caller');
select t.fails($$insert into public.plans (user_id, term, slot) values ('aaaaaaaa-0000-0000-0000-000000000002','2274','B')$$, 'cannot save a plan as someone else');
select t.fails($$insert into public.plans (term, slot) values ('2274','A')$$, 'one plan per slot');
select t.fails($$insert into public.plans (term, slot) values ('2274','D')$$, 'only slots A–C (Tate: 3 plans)');
select t.fails($$insert into public.plans (term, slot) values ('Spring','B')$$, 'term must be a 4-digit code');
select t.fails($$insert into public.plans (term, slot, sections) values ('2274','B','[{"code":"DROP TABLE","class_nbr":"1"}]')$$, 'malformed course code refused');
select t.fails($$insert into public.plans (term, slot, sections) values ('2274','B','[{"code":"BUS 4442","class_nbr":"12a"}]')$$, 'malformed class number refused');
select t.fails($$insert into public.plans (term, slot, sections) values ('2274','B','[{"code":"BUS 4442","class_nbr":"11111"},{"code":"BUS 4442","class_nbr":"11111"}]')$$, 'the same class twice refused');
select t.fails($$insert into public.plans (term, slot, sections) values ('2274','B','"BUS 4442"')$$, 'sections must be a list');
select t.fails($$insert into public.plans (term, slot, sections) values ('2274','B',
  (select jsonb_agg(jsonb_build_object('code','BUS 4442','class_nbr',(10000+g)::text)) from generate_series(1,13) g))$$, 'more than 12 sections refused');
select t.fails($$update public.plans set user_id = 'aaaaaaaa-0000-0000-0000-000000000002' where slot = 'A'$$, 'cannot hand a plan to someone else');
update public.plans set updated_at = '2000-01-01' where slot = 'A';
select t.ok((select updated_at > now() - interval '1 minute' from public.plans where slot='A'), 'updated_at is the server clock, not the client''s');
insert into public.plans (term, slot, sections) values ('2274','B','[{"code":"ECON 2001","class_nbr":"22223"}]');

-- ---- who can read it ---------------------------------------------------------------------------
select t.be('aaaaaaaa-0000-0000-0000-000000000002');
select t.ok((select count(*) from public.plans) = 2, 'an accepted friend reads both shared plans');
select t.be('aaaaaaaa-0000-0000-0000-000000000003');
select t.ok((select count(*) from public.plans) = 0, 'a stranger at the same school reads nothing');
select t.be('aaaaaaaa-0000-0000-0000-000000000005');
select t.ok((select count(*) from public.plans) = 0, 'a pending request reads nothing');
select t.be('aaaaaaaa-0000-0000-0000-000000000004');
select t.ok((select count(*) from public.plans) = 0, 'an accepted friend at ANOTHER school reads nothing (the wall holds)');
select t.be('');
select t.ok((select count(*) from public.plans) = 0, 'signed out reads nothing');

select t.be('aaaaaaaa-0000-0000-0000-000000000002');
update public.plans set shared = false, sections = '[]';
delete from public.plans;
reset role;
select t.ok((select count(*) from public.plans) = 2 and (select bool_and(shared) from public.plans), 'a friend cannot edit, hide or delete your plans');
set role authenticated;

select t.be('aaaaaaaa-0000-0000-0000-000000000001');
update public.plans set shared = false where slot = 'B';
select t.be('aaaaaaaa-0000-0000-0000-000000000002');
select t.ok((select count(*) from public.plans) = 1 and (select slot from public.plans) = 'A', 'turning "Friends can see" off hides that plan only');

reset role;
delete from public.friend_requests where to_user = 'aaaaaaaa-0000-0000-0000-000000000002';   -- what block_user does
set role authenticated;
select t.be('aaaaaaaa-0000-0000-0000-000000000002');
select t.ok((select count(*) from public.plans) = 0, 'unfriending or blocking ends the read');
reset role;
insert into public.friend_requests values ('aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000002','accepted');
set role authenticated;

-- ---- suspended and caps ------------------------------------------------------------------------
select t.be('aaaaaaaa-0000-0000-0000-000000000006');
select t.fails($$insert into public.plans (term, slot) values ('2274','A')$$, 'a suspended account cannot save a plan');
select t.be('aaaaaaaa-0000-0000-0000-000000000003');
do $$ declare y int; s text; begin
  for y in 2270..2273 loop foreach s in array array['A','B','C'] loop
    insert into public.plans (term, slot) values (y::text, s);
  end loop; end loop; end $$;
select t.fails($$insert into public.plans (term, slot) values ('2274','A')$$, 'the 13th plan is refused (12 per account)');
select t.ok((select count(*) from public.plans) = 12, 'the account holds 12 plans');
insert into public.plans (term, slot, sections) values ('2273','C','[{"code":"BUS 4442","class_nbr":"77777"}]')
  on conflict (user_id, term, slot) do update set sections = excluded.sections;
select t.ok((select sections->0->>'class_nbr' from public.plans where term = '2273' and slot = 'C') = '77777', 'at the cap, editing an existing plan by upsert still works');
reset role; delete from public.plans where user_id = 'aaaaaaaa-0000-0000-0000-000000000003'; set role authenticated;

-- ---- "N in plans" ------------------------------------------------------------------------------
-- 11111: A plan + F plan + S watch                     → 3  (shown)
-- 22222: A plan + F watch                              → 2  (hidden)
-- 33333: A plan + A watch + F plan + U plan (ucsb)     → 2 at Cal Poly (A once, F) → hidden
-- 44444: A private plan B + F plan + S plan            → 3  (a private plan still counts — anonymously)
select t.be('aaaaaaaa-0000-0000-0000-000000000001');
update public.plans set sections = '[{"code":"ECON 2001","class_nbr":"44444"}]' where slot = 'B';
insert into public.watch_sections (term, code, class_nbr) values ('2274','HIST 2230','33333');
select t.be('aaaaaaaa-0000-0000-0000-000000000002');
insert into public.plans (term, slot, sections) values ('2274','A','[{"code":"BUS 4442","class_nbr":"11111"},{"code":"HIST 2230","class_nbr":"33333"},{"code":"ECON 2001","class_nbr":"44444"}]');
insert into public.watch_sections (term, code, class_nbr) values ('2274','ECON 2001','22222');
select t.be('aaaaaaaa-0000-0000-0000-000000000003');
insert into public.watch_sections (term, code, class_nbr) values ('2274','BUS 4442','11111');
insert into public.plans (term, slot, sections) values ('2274','A','[{"code":"ECON 2001","class_nbr":"44444"}]');
select t.be('aaaaaaaa-0000-0000-0000-000000000004');
insert into public.plans (term, slot, sections) values ('2274','A','[{"code":"HIST 2230","class_nbr":"33333"}]');

select t.be('aaaaaaaa-0000-0000-0000-000000000005');   -- P has nothing planned: a pure reader
select t.ok((select jsonb_object_agg(class_nbr, n) from public.plan_interest('2274', array['11111','22222','33333','44444','99999']))
  = '{"11111":3,"44444":3}'::jsonb, 'counts: 3 shown, 2 hidden, other schools excluded, a student counted once, private plans counted');
select t.ok((select count(*) from public.plan_interest('2268', array['11111'])) = 0, 'another term counts separately');
select t.be('aaaaaaaa-0000-0000-0000-000000000001');   -- A is one of the three on 11111
select t.ok((select count(*) from public.plan_interest('2274', array['11111'])) = 0, 'the caller is never counted: A sees 2 others on 11111, so nothing');
select t.be('aaaaaaaa-0000-0000-0000-000000000005');
select t.ok((select count(*) from public.plan_interest('22; select 1', array['11111'])) = 0, 'a malformed term returns nothing');
select t.ok((select count(*) from public.plan_interest('2274', (select array_agg((10000+g)::text) from generate_series(1,301) g) || '11111'::text)) = 0, 'more than 300 class numbers returns nothing');
select t.ok((select count(*) from public.plan_interest('2274', '{}')) = 0, 'an empty list returns nothing');
select t.be('aaaaaaaa-0000-0000-0000-000000000004');
select t.ok((select count(*) from public.plan_interest('2274', array['11111','33333','44444'])) = 0, 'a UCSB caller sees no Cal Poly counts');
select t.be('');
select t.ok((select count(*) from public.plan_interest('2274', array['11111'])) = 0, 'signed out: nothing');
reset role;
select t.ok((select array_agg(parameter_name::text order by ordinal_position) from information_schema.parameters
   where specific_name like 'plan_interest%' and parameter_mode = 'OUT') = array['class_nbr','n'], 'plan_interest returns only a class number and a count — no who');

-- ---- anon, and account deletion ---------------------------------------------------------------
set role anon;
select t.fails($$select count(*) from public.plans$$, 'anon cannot read plans');
select t.fails($$select * from public.plan_interest('2274', array['11111'])$$, 'anon cannot call plan_interest');
reset role;
delete from auth.users where id = 'aaaaaaaa-0000-0000-0000-000000000001';
select t.ok(not exists (select 1 from public.plans where user_id = 'aaaaaaaa-0000-0000-0000-000000000001'), 'deleting an account deletes its plans');

\echo check-plans: all ok
