\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('88888888-8888-8888-8888-888888888888','s8@calpoly.edu') on conflict do nothing;
select set_config('request.jwt.claims','{"sub":"88888888-8888-8888-8888-888888888888","role":"authenticated"}',false) as _ \gset
set role authenticated;
delete from public.saved_classes; delete from public.my_sections; delete from public.class_history;
create or replace function pg_temp.w(label text, sql text) returns text language plpgsql as $$
begin execute sql; return 'accepted  ' || label;
exception when check_violation then return 'REFUSED   ' || label; end $$;
\echo -- what the two apps really write (must all be accepted)
select pg_temp.w('web  saved_classes upsert {term,code}', $q$insert into saved_classes(user_id,term,code) values (auth.uid(),'2268','CSC 1001') on conflict do nothing$q$);
select pg_temp.w('web  saved_classes class_nbr stamp (syncSavedSection)', $q$insert into saved_classes(user_id,term,code,class_nbr) values (auth.uid(),'2268','BUS 2050','20431')$q$);
select pg_temp.w('web  saved_classes waitlist_pos', $q$insert into saved_classes(user_id,term,code) values (auth.uid(),'2268','ECON 2210')$q$);
select pg_temp.w('web  my_sections {class_nbr:String(crn)}', $q$insert into my_sections(user_id,term,code,class_nbr,section,instructor,days,status,wl_pos) values (auth.uid(),'2268','CSC 1001','20431','01','Smith, J.','MWF','enrolled',null)$q$);
select pg_temp.w('app  my_sections waitlisted', $q$insert into my_sections(user_id,term,code,class_nbr,status,wl_pos) values (auth.uid(),'2268','BUS 2050','20999','waitlisted',3)$q$);
select pg_temp.w('web  class_history Spring 2024 (addPastClass)', $q$insert into class_history(user_id,code,term,year,professor) values (auth.uid(),'MATH 1411','Spring',2024,'Doe, A.')$q$);
select pg_temp.w('app  class_history quickLog term NULL year NULL', $q$insert into class_history(user_id,code,term,year,professor) values (auth.uid(),'CSC 1002',null,null,null)$q$);
select pg_temp.w('app  class_history DPR transfer AP 300 (code unchecked)', $q$insert into class_history(user_id,code,term,year,professor) values (auth.uid(),'AP 300','Fall',2022,null)$q$);
select pg_temp.w('app  class_history DPR transfer A1GE 1TR (code unchecked)', $q$insert into class_history(user_id,code,term,year,professor) values (auth.uid(),'A1GE 1TR','Fall',2022,null)$q$);
select pg_temp.w('app  class_history DPR Winter 2019 quarter era', $q$insert into class_history(user_id,code,term,year,professor) values (auth.uid(),'CPE 357','Winter',2019,null)$q$);
select pg_temp.w('web  UCSB-style code (SCHOOL_COURSES)', $q$insert into saved_classes(user_id,term,code) values (auth.uid(),'2268','CMPSC 16')$q$);
\echo -- what a student could write by hand (must be refused after the file)
select pg_temp.w('code = sentence', $q$insert into saved_classes(user_id,term,code) values (auth.uid(),'2268','you are all losers lol')$q$);
select pg_temp.w('code = link', $q$insert into saved_classes(user_id,term,code) values (auth.uid(),'2268','https://evil.example/login')$q$);
select pg_temp.w('code = 39 junk chars', $q$insert into saved_classes(user_id,term,code) values (auth.uid(),'2268',repeat('A',39))$q$);
select pg_temp.w('my_sections.code = sentence', $q$insert into my_sections(user_id,term,code,class_nbr) values (auth.uid(),'2268','call me maybe','1')$q$);
select pg_temp.w('my_sections.class_nbr = text', $q$insert into my_sections(user_id,term,code,class_nbr) values (auth.uid(),'2268','CSC 1001','see me after class')$q$);
select pg_temp.w('class_history.term = text', $q$insert into class_history(user_id,code,term,year) values (auth.uid(),'CSC 1003','whenever you like',2024)$q$);
select pg_temp.w('class_history.year = 1885', $q$insert into class_history(user_id,code,term,year) values (auth.uid(),'CSC 1004','Fall',1885)$q$);
select pg_temp.w('class_history.year = 9999', $q$insert into class_history(user_id,code,term,year) values (auth.uid(),'CSC 1005','Fall',9999)$q$);
reset role;
