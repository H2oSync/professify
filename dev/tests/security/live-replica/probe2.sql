\set ON_ERROR_STOP 0
\set A '''{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated","email":"a@calpoly.edu"}'''
\set B '''{"sub":"bbbbbbbb-0000-0000-0000-000000000002","role":"authenticated","email":"b@calpoly.edu"}'''
\set C '''{"sub":"cccccccc-0000-0000-0000-000000000003","role":"authenticated","email":"c@calpoly.edu"}'''
\set D '''{"sub":"dddddddd-0000-0000-0000-000000000004","role":"authenticated","email":"d@calpoly.edu"}'''
\set E '''{"sub":"eeeeeeee-0000-0000-0000-000000000005","role":"authenticated","email":"reviewer@appreview.calpoly.edu"}'''
\pset footer off
begin; \echo '[T1] C sends 50 friend requests in ONE insert (after: refused past 40)'
set local role authenticated; set local request.jwt.claims = :C;
insert into friend_requests(from_user,to_user,status) select 'cccccccc-0000-0000-0000-000000000003', id, 'pending' from profiles where display_name like 'X%';
reset role; select count(*) as c_requests from friend_requests where from_user='cccccccc-0000-0000-0000-000000000003'; rollback;
begin; \echo '[T1b] A sends one normal friend request to C (expect ok both)'
set local role authenticated; set local request.jwt.claims = :A;
insert into friend_requests(from_user,to_user,status) values ('aaaaaaaa-0000-0000-0000-000000000001','cccccccc-0000-0000-0000-000000000003','pending');
reset role; select count(*) as a_to_c from friend_requests where from_user='aaaaaaaa-0000-0000-0000-000000000001' and to_user='cccccccc-0000-0000-0000-000000000003'; rollback;
begin; \echo '[T3] A upserts a suggestion with created_at=2000 on the update path (after: date kept)'
set local role authenticated; set local request.jwt.claims = :A;
insert into professor_suggestions(user_id,professor_key,professor_name) values ('aaaaaaaa-0000-0000-0000-000000000001','k','K');
update professor_suggestions set created_at='2000-01-01' where user_id='aaaaaaaa-0000-0000-0000-000000000001';
reset role; select created_at::date = current_date as kept_today from professor_suggestions; rollback;
begin; \echo '[T4] A pins a conversation (last_at=2099) (after: denied); renames (ok)'
set local role authenticated; set local request.jwt.claims = :A;
update conversations set last_at='2099-01-01' where id='c0000000-0000-0000-0000-0000000000ab';
rollback; begin; set local role authenticated; set local request.jwt.claims = :A;
with u as (update conversations set title='Study' where id='c0000000-0000-0000-0000-0000000000ab' returning 1) select count(*) as renamed from u; rollback;
begin; \echo '[T5] sign-up with gmail (after: refused); with calpoly (ok)'
insert into auth.users(id,email) values (gen_random_uuid(),'someone@gmail.com');
rollback; begin; insert into auth.users(id,email) values (gen_random_uuid(),'new@calpoly.edu'); select 'calpoly signup ok' as r; rollback;
begin; \echo '[T6] demo account reads profiles (after: only itself) and friend-requests Ann (after: refused)'
set local role authenticated; set local request.jwt.claims = :E;
select count(*) as demo_sees_profiles from profiles;
insert into friend_requests(from_user,to_user,status) values ('eeeeeeee-0000-0000-0000-000000000005','aaaaaaaa-0000-0000-0000-000000000001','pending');
rollback;
begin; \echo '[T6b] Ann reads profiles (expect all real ones, not demo after)'
set local role authenticated; set local request.jwt.claims = :A; select count(*) as ann_sees_profiles from profiles; rollback;
begin; \echo '[T7] D (blocked by Ann) searches "Ann" (after: 0) ; C searches "__" (after: 0)'
set local role authenticated; set local request.jwt.claims = :D; select count(*) as d_finds_ann from search_people('Ann');
set local request.jwt.claims = :C; select count(*) as wildcard_hits from search_people('__'); rollback;
begin; \echo '[T8] Ann blocks D again via block_user: D leaves their direct chat (after: 0)'
set local role authenticated; set local request.jwt.claims = :A; select block_user('dddddddd-0000-0000-0000-000000000004');
reset role; select count(*) as d_still_in_chat from conversation_members where user_id='dddddddd-0000-0000-0000-000000000004'; rollback;
begin; \echo '[T9] Ann unfriends Bee, then Bee DMs Ann (after: refused); friends still can (T9b)'
delete from friend_requests where from_user='aaaaaaaa-0000-0000-0000-000000000001';
set local role authenticated; set local request.jwt.claims = :B;
insert into messages(conversation_id,sender,kind,body) values ('c0000000-0000-0000-0000-0000000000ab','bbbbbbbb-0000-0000-0000-000000000002','text','still here');
rollback;
begin; \echo '[T9b] friends Ann -> Bee DM (expect ok)'
set local role authenticated; set local request.jwt.claims = :A;
insert into messages(conversation_id,sender,kind,body) values ('c0000000-0000-0000-0000-0000000000ab','aaaaaaaa-0000-0000-0000-000000000001','text','hi'); select 'dm ok' as r; rollback;
begin; \echo '[T10] C plants a fake class (after: refused); a real class (ok)'
set local role authenticated; set local request.jwt.claims = :C;
insert into my_sections(user_id,code,class_nbr,term) values ('cccccccc-0000-0000-0000-000000000003','FAKE 999','1','2268');
rollback; begin; set local role authenticated; set local request.jwt.claims = :C;
insert into my_sections(user_id,code,class_nbr,term) values ('cccccccc-0000-0000-0000-000000000003','BUS 212','2','2268'); select 'real class ok' as r; rollback;
begin; \echo '[T10b] C adds 61 sections (after: refused at 61)'
set local role authenticated; set local request.jwt.claims = :C;
insert into my_sections(user_id,code,class_nbr,term) select 'cccccccc-0000-0000-0000-000000000003','BUS 212',g::text,'2268' from generate_series(1,61) g;
reset role; select count(*) as c_sections from my_sections where user_id='cccccccc-0000-0000-0000-000000000003'; rollback;
begin; \echo '[T11] anon lists avatars (after: 0); C writes C/other.png (after: refused); C/avatar.jpg ok'
set local role anon; set local request.jwt.claims = '{"role":"anon"}'; select count(*) as anon_lists from storage.objects where bucket_id='avatars';
set local role authenticated; set local request.jwt.claims = :C;
insert into storage.objects(bucket_id,name,owner) values ('avatars','cccccccc-0000-0000-0000-000000000003/other.png','cccccccc-0000-0000-0000-000000000003');
rollback; begin; set local role authenticated; set local request.jwt.claims = :C;
insert into storage.objects(bucket_id,name,owner) values ('avatars','cccccccc-0000-0000-0000-000000000003/avatar.jpg','cccccccc-0000-0000-0000-000000000003'); select 'avatar ok' as r; rollback;
begin; \echo '[T12] avatar_url tracking pixel (after: refused); our URL ok; empty ok'
set local role authenticated; set local request.jwt.claims = :C;
update profiles set avatar_url='https://evil.example/t.gif' where id='cccccccc-0000-0000-0000-000000000003';
rollback; begin; set local role authenticated; set local request.jwt.claims = :C;
update profiles set avatar_url='https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/cccccccc-0000-0000-0000-000000000003/avatar.jpg?v=1729000000000' where id='cccccccc-0000-0000-0000-000000000003';
update profiles set avatar_url='' where id='cccccccc-0000-0000-0000-000000000003'; select 'avatar_url ok' as r; rollback;
\echo '[T13] realtime publication'
select string_agg(tablename, ',' order by tablename) as published from pg_publication_tables where pubname='supabase_realtime';
begin; \echo '[T14] Ann votes on her own review (after: refused)'
set local role authenticated; set local request.jwt.claims = :A;
insert into review_helpful(review_id,voter_id) values ('e0000000-0000-0000-0000-00000000000a','aaaaaaaa-0000-0000-0000-000000000001'); rollback;
begin; \echo '[T14b] C votes on Bee review: counter (after: 1), C reads all votes (after: own only)'
set local role authenticated; set local request.jwt.claims = :C;
insert into review_helpful(review_id,voter_id) values ('e0000000-0000-0000-0000-00000000000b','cccccccc-0000-0000-0000-000000000003');
reset role; insert into review_helpful(review_id,voter_id) values ('e0000000-0000-0000-0000-00000000000b','dddddddd-0000-0000-0000-000000000004');
select helpful as bee_helpful from reviews where id='e0000000-0000-0000-0000-00000000000b';
set local role authenticated; set local request.jwt.claims = :C; select count(*) as c_sees_votes from review_helpful;
set local request.jwt.claims = :B; select count(*) as bee_author_sees_votes from review_helpful; rollback;
begin; \echo '[T15] review difficulty 9 (after: refused)'
set local role authenticated; set local request.jwt.claims = :C;
insert into reviews(user_id,professor_key,professor_name,score,difficulty) values ('cccccccc-0000-0000-0000-000000000003','k|x','X',3,9); rollback;
begin; \echo '[T16] C reports Bee review naming Ann as author (after: author = Bee); C reports a message in a chat they are not in (after: refused)'
set local role authenticated; set local request.jwt.claims = :C;
insert into reports(reporter,kind,target_id,target_user,reason,status) values ('cccccccc-0000-0000-0000-000000000003','review','e0000000-0000-0000-0000-00000000000b','aaaaaaaa-0000-0000-0000-000000000001','spam','open');
reset role; select (target_user='bbbbbbbb-0000-0000-0000-000000000002') as author_is_bee from reports; rollback;
begin; set local role authenticated; set local request.jwt.claims = :C;
insert into reports(reporter,kind,target_id,target_user,reason,status,note) values ('cccccccc-0000-0000-0000-000000000003','message','e1000000-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','spam','open','fake words'); rollback;
begin; \echo '[T18] C asks is_suspended(Bee) (after: f); Bee asks own (t)'
set local role authenticated; set local request.jwt.claims = :C; select is_suspended('bbbbbbbb-0000-0000-0000-000000000002') as c_learns;
set local request.jwt.claims = :B; select is_suspended('bbbbbbbb-0000-0000-0000-000000000002') as own; rollback;
begin; \echo '[T19] anon re-adds an email already on the waitlist (after: no error)'
set local role anon; set local request.jwt.claims = '{"role":"anon"}';
insert into school_waitlist(email,school) values ('z@sdsu.edu','sdsu'); select 'waitlist quiet' as r; rollback;
\echo '[T20] privileges'
select has_function_privilege('anon','public.search_people(text)','EXECUTE') as anon_search,
       has_function_privilege('anon','public.is_pending_deletion(uuid)','EXECUTE') as anon_pending,
       has_function_privilege('anon','public.log_events(jsonb)','EXECUTE') as anon_log,
       has_function_privilege('authenticated','public.friends_of(uuid)','EXECUTE') as auth_friends_of,
       has_function_privilege('authenticated','public.wf_hit(text)','EXECUTE') as auth_wf_hit,
       has_table_privilege('authenticated','public.messages','TRUNCATE') as auth_truncate;
begin; \echo '[T21] regression: Ann saves a class, renames chat, searches Bee, suggests friends'
set local role authenticated; set local request.jwt.claims = :A;
insert into saved_classes(user_id,code,term) values ('aaaaaaaa-0000-0000-0000-000000000001','CSC 101','2268');
select count(*) as ann_finds_bee from search_people('Bee');
select count(*) >= 0 as suggest_ok from suggest_friends();
select count(*) >= 0 as classmates_ok from suggest_classmates_v2(); rollback;
