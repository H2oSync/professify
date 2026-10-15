insert into auth.users(id,email) values
 ('aaaaaaaa-0000-0000-0000-000000000001','a@calpoly.edu'),('bbbbbbbb-0000-0000-0000-000000000002','b@calpoly.edu'),
 ('cccccccc-0000-0000-0000-000000000003','c@calpoly.edu'),('dddddddd-0000-0000-0000-000000000004','d@calpoly.edu'),
 ('eeeeeeee-0000-0000-0000-000000000005','reviewer@appreview.calpoly.edu');
insert into auth.users(id,email) select ('99999999-0000-0000-0000-'||lpad(g::text,12,'0'))::uuid, 'x'||g||'@calpoly.edu' from generate_series(1,50) g;
set session_replication_role = replica;  -- seed without triggers
insert into profiles(id,edu_email,display_name,username,school) values
 ('aaaaaaaa-0000-0000-0000-000000000001','a@calpoly.edu','Ann','ann','calpoly'),
 ('bbbbbbbb-0000-0000-0000-000000000002','b@calpoly.edu','Bee','bee','calpoly'),
 ('cccccccc-0000-0000-0000-000000000003','c@calpoly.edu','Cy','cyy','calpoly'),
 ('dddddddd-0000-0000-0000-000000000004','d@calpoly.edu','Dee','dee','calpoly'),
 ('eeeeeeee-0000-0000-0000-000000000005','reviewer@appreview.calpoly.edu','Riley Demo','riley_demo','calpoly');
insert into profiles(id,edu_email,display_name,school) select id, email, 'X'||substr(email,2,3), 'calpoly' from auth.users where email like 'x%';
insert into course_catalog(course_code) values ('BUS 212'),('CSC 101');
insert into friend_requests(from_user,to_user,status) values ('aaaaaaaa-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000002','accepted');
insert into blocks(blocker,blocked) values ('aaaaaaaa-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000004');
insert into conversations(id,kind,created_by) values
 ('c0000000-0000-0000-0000-0000000000ab','direct','aaaaaaaa-0000-0000-0000-000000000001'),
 ('c0000000-0000-0000-0000-0000000000ad','direct','aaaaaaaa-0000-0000-0000-000000000001');
insert into conversation_members(conversation_id,user_id) values
 ('c0000000-0000-0000-0000-0000000000ab','aaaaaaaa-0000-0000-0000-000000000001'),('c0000000-0000-0000-0000-0000000000ab','bbbbbbbb-0000-0000-0000-000000000002'),
 ('c0000000-0000-0000-0000-0000000000ad','aaaaaaaa-0000-0000-0000-000000000001'),('c0000000-0000-0000-0000-0000000000ad','dddddddd-0000-0000-0000-000000000004');
insert into messages(id,conversation_id,sender,kind,body) values ('e1000000-0000-0000-0000-000000000001','c0000000-0000-0000-0000-0000000000ab','bbbbbbbb-0000-0000-0000-000000000002','text','hey');
insert into reviews(id,user_id,professor_key,professor_name,score,note) values
 ('e0000000-0000-0000-0000-00000000000b','bbbbbbbb-0000-0000-0000-000000000002','smith|j','J Smith',4,'good'),
 ('e0000000-0000-0000-0000-00000000000a','aaaaaaaa-0000-0000-0000-000000000001','smith|j','J Smith',5,'great');
insert into suspensions(user_id) values ('bbbbbbbb-0000-0000-0000-000000000002');
insert into storage.objects(bucket_id,name,owner) values ('avatars','aaaaaaaa-0000-0000-0000-000000000001/avatar.jpg','aaaaaaaa-0000-0000-0000-000000000001');
insert into school_waitlist(email,school) values ('z@sdsu.edu','sdsu');
set session_replication_role = origin;
