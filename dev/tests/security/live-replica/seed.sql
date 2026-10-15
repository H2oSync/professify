insert into auth.users(id,email) values
 ('aaaaaaaa-0000-0000-0000-000000000001','a@calpoly.edu'),('bbbbbbbb-0000-0000-0000-000000000002','b@calpoly.edu'),
 ('cccccccc-0000-0000-0000-000000000003','c@sdsu.edu'),('dddddddd-0000-0000-0000-000000000004','d@calpoly.edu');
insert into profiles(id,edu_email,display_name,username,school) values
 ('aaaaaaaa-0000-0000-0000-000000000001','a@calpoly.edu','Ann','ann','calpoly'),
 ('bbbbbbbb-0000-0000-0000-000000000002','b@calpoly.edu','Bee','bee','calpoly'),
 ('cccccccc-0000-0000-0000-000000000003','c@sdsu.edu','Cy','cy','sdsu'),
 ('dddddddd-0000-0000-0000-000000000004','d@calpoly.edu','Dee','dee','calpoly');
insert into my_sections(user_id,code,term) select id,'BUS 212','2272' from profiles;
insert into blocks(blocker,blocked) values ('aaaaaaaa-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000004');
insert into conversations(id,kind,created_by) values ('c0000000-0000-0000-0000-000000000001','direct','aaaaaaaa-0000-0000-0000-000000000001'),('c0000000-0000-0000-0000-000000000002','direct','bbbbbbbb-0000-0000-0000-000000000002');
insert into conversation_members(conversation_id,user_id) values ('c0000000-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001'),('c0000000-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000002'),('c0000000-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000002'),('c0000000-0000-0000-0000-000000000002','cccccccc-0000-0000-0000-000000000003');
set request.jwt.claims = '{"sub":"bbbbbbbb-0000-0000-0000-000000000002","role":"authenticated","email":"b@calpoly.edu"}';
insert into reviews(id,user_id,professor_key,professor_name,score,note) values ('e0000000-0000-0000-0000-000000000001','bbbbbbbb-0000-0000-0000-000000000002','smith|j','J Smith',4,'good');
insert into sprint_progress(task_id,done_by) values ('t1','tate');

reset request.jwt.claims;
