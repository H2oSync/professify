-- Run (from dev/tests): psql -v ON_ERROR_STOP=1 -f fixture-chat.sql -f ../../sql/professify-chat-likes-hides.sql -f ../../sql/professify-chat-likes-hides.sql -f check-chat-likes-hides.sql
-- (the migration runs twice on purpose: it must be safe to re-run). Every check raises on failure.
-- RLS is exercised as the real 'authenticated' role; each block sets its own identity.
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

truncate public.message_likes, public.message_hides, public.conversation_clears, public.messages, public.conversation_members, public.conversations, public.blocks, public.suspensions cascade;
delete from auth.users;
insert into auth.users (id, email) values
  ('bbbbbbbb-0000-0000-0000-000000000001','a@calpoly.edu'),   -- A: me
  ('bbbbbbbb-0000-0000-0000-000000000002','b@calpoly.edu'),   -- B: in my chat
  ('bbbbbbbb-0000-0000-0000-000000000003','c@calpoly.edu'),   -- C: not in it
  ('bbbbbbbb-0000-0000-0000-000000000004','d@calpoly.edu'),   -- D: in a chat with me, then blocked
  ('bbbbbbbb-0000-0000-0000-000000000005','z@calpoly.edu');   -- Z: in my chat, suspended
insert into public.conversations (id, kind, created_by) values
  ('cccccccc-0000-0000-0000-000000000001','direct','bbbbbbbb-0000-0000-0000-000000000001'),
  ('cccccccc-0000-0000-0000-000000000002','direct','bbbbbbbb-0000-0000-0000-000000000001'),
  ('cccccccc-0000-0000-0000-000000000003','group','bbbbbbbb-0000-0000-0000-000000000001');
insert into public.conversation_members (conversation_id, user_id) values
  ('cccccccc-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000001'),
  ('cccccccc-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000002'),
  ('cccccccc-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000001'),
  ('cccccccc-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000004'),
  ('cccccccc-0000-0000-0000-000000000003','bbbbbbbb-0000-0000-0000-000000000001'),
  ('cccccccc-0000-0000-0000-000000000003','bbbbbbbb-0000-0000-0000-000000000005'),
  ('cccccccc-0000-0000-0000-000000000003','bbbbbbbb-0000-0000-0000-000000000004');   -- D is in the group too
insert into public.messages (id, conversation_id, sender, body) values
  ('dddddddd-0000-0000-0000-000000000001','cccccccc-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000002','hi from B'),
  ('dddddddd-0000-0000-0000-000000000002','cccccccc-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000001','hi from A'),
  ('dddddddd-0000-0000-0000-000000000003','cccccccc-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000004','hi from D'),
  ('dddddddd-0000-0000-0000-000000000004','cccccccc-0000-0000-0000-000000000003','bbbbbbbb-0000-0000-0000-000000000001','group hello'),
  ('dddddddd-0000-0000-0000-000000000005','cccccccc-0000-0000-0000-000000000003','bbbbbbbb-0000-0000-0000-000000000005','group note from Z');
insert into public.blocks values ('bbbbbbbb-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000004');
insert into public.suspensions (user_id) values ('bbbbbbbb-0000-0000-0000-000000000005');

set role authenticated;

-- ---- likes --------------------------------------------------------------------------------------
select t.be('bbbbbbbb-0000-0000-0000-000000000001');
insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000001');
select t.ok((select user_id = auth.uid() from public.message_likes where message_id = 'dddddddd-0000-0000-0000-000000000001'), 'A likes B''s message; user_id defaults to the caller');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000001')$$, 'one like per person per message');
select t.fails($$insert into public.message_likes (message_id, user_id) values ('dddddddd-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000002')$$, 'cannot like as someone else');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000003')$$, 'cannot like a message from someone you blocked');
select t.be('bbbbbbbb-0000-0000-0000-000000000004');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000003')$$, 'blocked D cannot like even his own message in a chat with the blocker');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000005')$$, 'blocked D cannot like a third person''s message in a group with the blocker');
select t.be('bbbbbbbb-0000-0000-0000-000000000001');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000005')$$, 'the blocker cannot like in a group shared with the person they blocked either');
select t.be('bbbbbbbb-0000-0000-0000-000000000002');
select t.ok((select count(*) = 1 from public.message_likes), 'B, in the chat, sees A''s like');
insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000002');
select t.be('bbbbbbbb-0000-0000-0000-000000000003');
select t.ok((select count(*) = 0 from public.message_likes), 'C, not in the chat, sees no likes');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000001')$$, 'C cannot like a message in a chat they are not in');
select t.be('bbbbbbbb-0000-0000-0000-000000000005');
select t.fails($$insert into public.message_likes (message_id) values ('dddddddd-0000-0000-0000-000000000004')$$, 'a suspended account cannot like (others would see it)');
select t.be('bbbbbbbb-0000-0000-0000-000000000002');
delete from public.message_likes where message_id = 'dddddddd-0000-0000-0000-000000000001';
select t.ok((select count(*) = 2 from public.message_likes), 'B cannot remove A''s like (the delete touches nothing)');
delete from public.message_likes where message_id = 'dddddddd-0000-0000-0000-000000000002';
select t.ok((select count(*) = 1 from public.message_likes), 'B unlikes their own');

-- ---- delete a message for yourself ---------------------------------------------------------------
select t.be('bbbbbbbb-0000-0000-0000-000000000001');
insert into public.message_hides (message_id) values ('dddddddd-0000-0000-0000-000000000001');
select t.ok((select count(*) = 1 from public.message_hides), 'A hides B''s message for themselves');
select t.ok((select count(*) = 2 from public.messages where conversation_id = 'cccccccc-0000-0000-0000-000000000001'), 'the message itself is untouched');
select t.be('bbbbbbbb-0000-0000-0000-000000000002');
select t.ok((select count(*) = 0 from public.message_hides), 'B cannot see that A hid it');
select t.fails($$insert into public.message_hides (message_id, user_id) values ('dddddddd-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000001')$$, 'cannot hide for someone else');
select t.be('bbbbbbbb-0000-0000-0000-000000000003');
select t.fails($$insert into public.message_hides (message_id) values ('dddddddd-0000-0000-0000-000000000001')$$, 'C cannot hide a message from a chat they are not in');
select t.be('bbbbbbbb-0000-0000-0000-000000000001');
delete from public.message_hides where message_id = 'dddddddd-0000-0000-0000-000000000001';
select t.ok((select count(*) = 0 from public.message_hides), 'A can undo a hide');

-- ---- delete a chat for yourself -------------------------------------------------------------------
select t.be('bbbbbbbb-0000-0000-0000-000000000001');
insert into public.conversation_clears (conversation_id) values ('cccccccc-0000-0000-0000-000000000001');
select t.ok((select user_id = auth.uid() and cleared_at <= now() from public.conversation_clears), 'A clears the chat; user_id and cleared_at default');
update public.conversation_clears set cleared_at = now() where conversation_id = 'cccccccc-0000-0000-0000-000000000001';
select t.ok((select count(*) = 1 from public.conversation_clears), 'clearing it again moves the time (an update, one row)');
select t.fails($$update public.conversation_clears set conversation_id = 'cccccccc-0000-0000-0000-000000000003'$$, 'cannot move a clear to another chat (only cleared_at is updatable)');
select t.ok((select count(*) from public.messages) = 5, 'clearing a chat deletes nobody''s messages (A sees all 5 in their three chats)');
select t.be('bbbbbbbb-0000-0000-0000-000000000002');
select t.ok((select count(*) = 0 from public.conversation_clears), 'B cannot tell A deleted the chat');
select t.ok((select count(*) = 2 from public.messages where conversation_id = 'cccccccc-0000-0000-0000-000000000001'), 'B still has the whole conversation');
select t.fails($$insert into public.conversation_clears (conversation_id) values ('cccccccc-0000-0000-0000-000000000003')$$, 'B cannot clear a chat B is not in');
select t.fails($$insert into public.conversation_clears (conversation_id, user_id) values ('cccccccc-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000001')$$, 'cannot clear for someone else');
update public.conversation_clears set cleared_at = '2000-01-01' where conversation_id = 'cccccccc-0000-0000-0000-000000000001';
select t.be('bbbbbbbb-0000-0000-0000-000000000001');
select t.ok((select cleared_at > '2001-01-01' from public.conversation_clears where conversation_id = 'cccccccc-0000-0000-0000-000000000001'), 'B cannot move A''s clear (the update touches nothing)');

-- ---- anon gets nothing ------------------------------------------------------------------------------
reset role; set role anon;
select t.fails($$select * from public.message_likes$$, 'anon cannot read likes');
select t.fails($$select * from public.message_hides$$, 'anon cannot read hides');
select t.fails($$select * from public.conversation_clears$$, 'anon cannot read clears');
reset role;
\echo 'check-chat-likes-hides: all passed'
