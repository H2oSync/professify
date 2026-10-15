\set ON_ERROR_STOP 0
\set A '''{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated","email":"a@calpoly.edu"}'''
\set B '''{"sub":"bbbbbbbb-0000-0000-0000-000000000002","role":"authenticated","email":"b@calpoly.edu"}'''
\set C '''{"sub":"cccccccc-0000-0000-0000-000000000003","role":"authenticated","email":"c@sdsu.edu"}'''
\set D '''{"sub":"dddddddd-0000-0000-0000-000000000004","role":"authenticated","email":"d@calpoly.edu"}'''
begin;
\echo '[1] anon UPDATE reviews_public (expect: denied after)'
set local role anon; set local request.jwt.claims = '{"role":"anon"}';
with u as (update reviews_public set note='HACKED' where id='e0000000-0000-0000-0000-000000000001' returning 1) select count(*) as rewritten from u;
delete from reviews_public where professor_key='smith|j';
reset role;
rollback; begin;
\echo '[1b] anon SELECT reviews_public still works'
set local role anon; select count(*) as reviews_visible from reviews_public; reset role;
\echo '[2] anon find_profile_by_username (expect: denied after)'
set local role anon; select id is not null as got_profile from find_profile_by_username('bee'); 
rollback; begin;
\echo '[3] sdsu student C suggest_classmates_v2 (expect: 0 rows after)'
set local role authenticated; set local request.jwt.claims = :C; select username, codes from suggest_classmates_v2();
rollback; begin;
\echo '[3b] A suggest_classmates_v2 (expect: bee only after; dee blocked, cy other school)'
set local role authenticated; set local request.jwt.claims = :A; select username from suggest_classmates_v2() order by 1;
rollback; begin;
\echo '[4] anon sprint_progress (expect: denied after)'
set local role anon; select count(*) from sprint_progress;
rollback; begin;
\echo '[5] A re-points membership into conv2 (expect: denied after)'
set local role authenticated; set local request.jwt.claims = :A;
update conversation_members set conversation_id='c0000000-0000-0000-0000-000000000002';
select is_conv_member('c0000000-0000-0000-0000-000000000002','aaaaaaaa-0000-0000-0000-000000000001') as a_in_conv2;
rollback; begin;
\echo '[5b] A marks conv1 read (expect: 1 row both times)'
set local role authenticated; set local request.jwt.claims = :A;
with u as (update conversation_members set last_read_at=now() where conversation_id='c0000000-0000-0000-0000-000000000001' and user_id='aaaaaaaa-0000-0000-0000-000000000001' returning 1) select count(*) as marked from u;
rollback; begin;
\echo '[6] A backdated message + friend request + report + suggestion (expect: created_at = today after)'
set local role authenticated; set local request.jwt.claims = :A;
insert into messages(conversation_id,sender,kind,body,created_at) values ('c0000000-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','text','hi','2000-01-01');
insert into friend_requests(from_user,to_user,status,created_at) values ('aaaaaaaa-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000002','pending','2000-01-01');
insert into reports(reporter,kind,target_id,reason,status,action_taken,resolved_at,created_at) values ('aaaaaaaa-0000-0000-0000-000000000001','review','x','spam','open','dismissed',now(),'2000-01-01');
insert into professor_suggestions(user_id,professor_key,professor_name,created_at) values ('aaaaaaaa-0000-0000-0000-000000000001','k','K','2000-01-01');
reset role;
select 'messages' t, created_at::date = current_date as now_stamped from messages
union all select 'friend_requests', created_at::date = current_date from friend_requests
union all select 'reports', created_at::date = current_date and action_taken is null and resolved_at is null from reports
union all select 'professor_suggestions', created_at::date = current_date from professor_suggestions;
select last_at::date = current_date as conv_last_at_today from conversations where id='c0000000-0000-0000-0000-000000000001';
rollback; begin;
\echo '[7] A writes a review with helpful=999/removed_at, then bumps helpful on own review B? and on own'
set local role authenticated; set local request.jwt.claims = :A;
insert into reviews(id,user_id,professor_key,professor_name,score,note,helpful,removed_at,created_at) values ('e0000000-0000-0000-0000-0000000000a1','aaaaaaaa-0000-0000-0000-000000000001','smith|j','J Smith',5,'great',999,null,'2099-01-01');
update reviews set helpful=500, note='great!!' where id='e0000000-0000-0000-0000-0000000000a1';
reset role;
select helpful, note, created_at::date = current_date as now_stamped from reviews where id='e0000000-0000-0000-0000-0000000000a1';
rollback; begin;
\echo '[8] A sets edu_email to a victim address (expect: stays a@calpoly.edu after)'
set local role authenticated; set local request.jwt.claims = :A;
update profiles set edu_email='victim@calpoly.edu', major='Econ' where id='aaaaaaaa-0000-0000-0000-000000000001';
reset role; select edu_email, major from profiles where id='aaaaaaaa-0000-0000-0000-000000000001';
rollback; begin;
\echo '[8b] service/editor update keeps what it writes'
update profiles set edu_email='ops@calpoly.edu' where id='bbbbbbbb-0000-0000-0000-000000000002'; select edu_email from profiles where id='bbbbbbbb-0000-0000-0000-000000000002';
rollback; begin;
\echo '[9] B asks blocked_between(A,D) (expect: f after); A asks (A,D) (t)'
set local role authenticated; set local request.jwt.claims = :B; select blocked_between('aaaaaaaa-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000004') as b_sees;
set local request.jwt.claims = :A; select blocked_between('aaaaaaaa-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000004') as a_sees;
rollback; begin;
\echo '[9b] D friend-requests A (expect: refused both times)'
set local role authenticated; set local request.jwt.claims = :D;
insert into friend_requests(from_user,to_user,status) values ('dddddddd-0000-0000-0000-000000000004','aaaaaaaa-0000-0000-0000-000000000001','pending');
rollback; begin;
\echo '[10] A sends a normal message and B reads it (expect: works)'
set local role authenticated; set local request.jwt.claims = :A;
insert into messages(conversation_id,sender,kind,body) values ('c0000000-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','text','hello');
set local request.jwt.claims = :B; select count(*) as b_reads from messages;
rollback;
