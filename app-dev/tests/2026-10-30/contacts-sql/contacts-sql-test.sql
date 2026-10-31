-- Runs after standin.sql and termchamp-contacts-2026-10-30.sql (twice). Every check is an assert:
-- the first one that fails stops the run (ON_ERROR_STOP) and names itself.
\set ON_ERROR_STOP 1
create or replace function public.t_sha(x text) returns text language sql immutable as $$ select encode(extensions.digest(x, 'sha256'), 'hex') $$;
grant execute on function public.t_sha(text) to anon, authenticated;
create or replace function public.t_as(uid text, email text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object('sub', uid, 'email', email, 'role', 'authenticated')::text, false) $$;
grant execute on function public.t_as(text, text) to anon, authenticated;

-- ---------- grants
do $$ begin
  assert not has_function_privilege('anon', 'public.match_contacts(text[])', 'execute'), 'anon cannot match';
  assert not has_function_privilege('anon', 'public.set_my_phone(text)', 'execute'), 'anon cannot set a phone';
  assert not has_function_privilege('anon', 'public.my_phone_saved()', 'execute'), 'anon cannot ask';
  assert has_function_privilege('authenticated', 'public.match_contacts(text[])', 'execute'), 'authenticated can match';
  assert has_function_privilege('authenticated', 'public.set_my_phone(text)', 'execute'), 'authenticated can set';
  assert not has_function_privilege('authenticated', 'public.contacts_key(text)', 'execute'), 'nobody calls contacts_key';
  assert not has_function_privilege('authenticated', 'public.contacts_rate(uuid,integer,integer)', 'execute'), 'nobody calls contacts_rate';
  assert not has_column_privilege('authenticated', 'public.profiles', 'phone_hash', 'select'), 'phone_hash not selectable';
  assert not has_column_privilege('anon', 'public.profiles', 'phone_hash', 'select'), 'phone_hash not selectable (anon)';
  assert (select count(*) from vault.secrets where name = 'contact_pepper') = 1, 'one pepper, even after two runs';
  raise notice 'ok grants';
end $$;

-- ---------- Avery saves her number (as Avery)
set role authenticated;
select public.t_as('00000000-0000-4000-8000-000000000002', 'avery@calpoly.edu');
do $$ begin
  assert public.my_phone_saved() = false, 'no number yet';
  assert public.set_my_phone(public.t_sha('+18055550134')) = true, 'set returns true';
  assert public.my_phone_saved() = true, 'saved';
  raise notice 'ok set';
end $$;
-- direct write through PostgREST's UPDATE grant is refused
do $$ begin
  begin
    update public.profiles set phone_hash = public.t_sha('+18055550199') where id = auth.uid();
    raise exception 'direct write should have failed';
  exception when insufficient_privilege then raise notice 'ok direct write refused'; end;
end $$;
-- a bad shape is refused
do $$ begin
  begin perform public.set_my_phone('8055550134'); raise exception 'bad shape accepted';
  exception when invalid_parameter_value then raise notice 'ok bad shape refused'; end;
end $$;
-- other columns still update normally
update public.profiles set major = 'Fixture Major' where id = auth.uid();
-- phone_hash can't be read back even for her own row
do $$ begin
  begin perform (select phone_hash from public.profiles where id = auth.uid()); raise exception 'phone_hash was readable';
  exception when insufficient_privilege then raise notice 'ok phone_hash unreadable'; end;
end $$;
reset role;
do $$ begin
  assert (select phone_hash from public.profiles where id = '00000000-0000-4000-8000-000000000002') <> public.t_sha('+18055550134'), 'stored value is peppered, not the bare sha256';
  assert (select phone_hash from public.profiles where id = '00000000-0000-4000-8000-000000000002') ~ '^[0-9a-f]{64}$', 'stored shape';
  raise notice 'ok peppered';
end $$;
-- the blocked, leaving, sdsu, demo and suspended people also save numbers (server job: no JWT)
select set_config('request.jwt.claims', '', false);
select set_config('tc.phone_write', '1', false);
update public.profiles set phone_hash = public.contacts_key(public.t_sha('+1805555010' || right(id::text, 1))) where id::text ~ '000[34567]$';
select set_config('tc.phone_write', '', false);

-- ---------- I match (as Me)
set role authenticated;
select public.t_as('00000000-0000-4000-8000-000000000001', 'me@calpoly.edu');
create temp table got as select * from public.match_contacts(array[
  public.t_sha('+18055550134'),                 -- Avery's phone
  public.t_sha('avery@calpoly.edu'),            -- Avery's email too: one row, two hashes
  public.t_sha('mixed.case@calpoly.edu'),       -- auth.users has Mixed.Case@CalPoly.edu
  public.t_sha('me@calpoly.edu'),               -- me: never
  public.t_sha('+18055550103'), public.t_sha('blocked@calpoly.edu'),     -- blocked me
  public.t_sha('+18055550104'), public.t_sha('leaving@calpoly.edu'),     -- being deleted
  public.t_sha('+18055550105'), public.t_sha('sdsu.person@sdsu.edu'),    -- other school
  public.t_sha('+18055550106'), public.t_sha('demo@appreview.calpoly.edu'), -- demo wall
  public.t_sha('+18055550107'), public.t_sha('suspended@calpoly.edu'),   -- suspended
  'not-a-hash', upper(public.t_sha('nobody@calpoly.edu'))]);
do $$ declare n int; m text[]; begin
  select count(*) into n from got;
  assert n = 2, 'exactly Avery and Mixed match, got ' || n || ': ' || (select string_agg(display_name, ', ') from got);
  select matched into m from got where username = 'avery';
  assert cardinality(m) = 2, 'Avery matched by phone and email';
  assert exists (select 1 from got where username = 'mixed'), 'email compare is case-insensitive';
  raise notice 'ok match';
end $$;
-- empty and oversized calls
do $$ begin
  assert (select count(*) from public.match_contacts(array[]::text[])) = 0, 'empty is empty';
  begin perform public.match_contacts(array_fill('a'::text, array[2001])); raise exception 'oversized accepted';
  exception when program_limit_exceeded then raise notice 'ok 2000 cap'; end;
end $$;
-- the demo account sees only demo accounts
select public.t_as('00000000-0000-4000-8000-000000000006', 'demo@appreview.calpoly.edu');
do $$ begin
  assert (select count(*) from public.match_contacts(array[public.t_sha('+18055550134')])) = 0, 'demo wall: demo cannot see Avery';
  raise notice 'ok demo wall';
end $$;
-- the blocked person can't find me either way
select public.t_as('00000000-0000-4000-8000-000000000003', 'blocked@calpoly.edu');
do $$ begin
  assert (select count(*) from public.match_contacts(array[public.t_sha('me@calpoly.edu')])) = 0, 'blocks work both ways';
  raise notice 'ok blocks';
end $$;
-- one account per number
select public.t_as('00000000-0000-4000-8000-000000000008', 'mixed.case@calpoly.edu');
do $$ begin
  begin perform public.set_my_phone(public.t_sha('+18055550134')); raise exception 'second claim accepted';
  exception when unique_violation then raise notice 'ok one account per number'; end;
end $$;
-- rate limit: Me has used 1 of 20 this hour (the empty and oversized calls return before counting)
select public.t_as('00000000-0000-4000-8000-000000000001', 'me@calpoly.edu');
do $$ declare i int; begin
  for i in 1..19 loop perform public.match_contacts(array[public.t_sha('x' || i)]); end loop;
  begin perform public.match_contacts(array[public.t_sha('x21')]); raise exception '21st call accepted';
  exception when raise_exception then if sqlerrm !~ 'too fast' then raise; end if; raise notice 'ok rate limit at 20/hour'; end;
end $$;
-- clear
select public.t_as('00000000-0000-4000-8000-000000000002', 'avery@calpoly.edu');
do $$ begin
  assert public.set_my_phone('') = false, 'clear returns false';
  assert public.my_phone_saved() = false, 'cleared';
  raise notice 'ok clear';
end $$;
reset role;
-- signed out
set role anon;
do $$ begin
  begin perform public.match_contacts(array['a']); raise exception 'anon ran match';
  exception when insufficient_privilege then raise notice 'ok anon refused'; end;
end $$;
reset role;
select 'ALL CONTACT SQL CHECKS PASSED' as result;
