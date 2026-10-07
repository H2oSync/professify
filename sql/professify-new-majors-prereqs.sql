-- New majors on the phone and the website (2026-10-06): Industrial Technology & Packaging, Physics (BA),
-- and Experience & Event Management (the catalog's current name for "Recreation, Parks & Tourism
-- Administration / Experience Industry Management").
--
-- What this does, in one transaction:
--   1. Renames stored profiles from the old major name to the new one. (Both apps already read the old
--      name as the new one, so this only tidies the data.)
--   2. Adds prerequisite records to course_prereqs for courses on these three majors' flowcharts — ONLY
--      where the course has no record yet. Nothing that is already there is changed.
--      Every record is copied from the Cal Poly 2026–28 catalog's own requisite line (quoted beside it).
--      Only requisites that are classes are recorded. A course whose requisite also needs standing,
--      a major, consent, a placement or a GE area is left out on purpose: the app then says it can't
--      check it, instead of calling it fulfilled when it may not be.
--   3. Lists every class on the three flowcharts that still has no prerequisite record, so you can see
--      exactly what the app will show as "can't check".
--
-- Safe to run twice. Read-only except for steps 1 and 2. Run it when the PR goes live: until then, a student
-- renamed by the app and a friend still stored under the old name don't count as the same major for
-- friend suggestions.

begin;

-- 1. profiles
update public.profiles
   set major = 'Experience & Event Management'
 where major = 'Recreation, Parks & Tourism Administration / Experience Industry Management';

-- 2. course_prereqs, added only where missing
create temp table np (code text primary key, j text not null, src text not null) on commit drop;
insert into np values
-- Industrial Technology & Packaging
('ITP 2233', '{"req":[]}', 'none'),
('ITP 2234', '{"req":[]}', 'none'),
('ITP 2241', '{"req":[["CHEM 124","CHEM 127","CHEM 1120"]]}', 'One of the following: CHEM 124, CHEM 127, or CHEM 1120'),
('ITP 2260', '{"req":[["CHEM 124","CHEM 127","CHEM 1120"]]}', 'One of the following: CHEM 124, CHEM 127, or CHEM 1120'),
('ITP 3303', '{"req":[["STAT 218","STAT 251","STAT 301","STAT 312","STAT 1110","STAT 1210","STAT 1510","STAT 3210"]]}', 'One of the following: STAT 218, STAT 251, STAT 301, STAT 312, STAT 1110, STAT 1210, STAT 1510, or STAT 3210'),
('ITP 3326', '{"req":[["ITP 233","BUS 310","ITP 2233","BUS 3310"]]}', 'One of the following: ITP 233, BUS 310, ITP 2233, or BUS 3310'),
('ITP 3334', '{"req":[["ITP 234","ITP 2234"]]}', 'ITP 234 or ITP 2234'),
('ITP 3390', '{"req":[["ITP 260","ITP 2260"]]}', 'ITP 260 or ITP 2260'),
('ITP 4403', '{"req":[["ITP 303","ITP 3303"]]}', 'ITP 303 or ITP 3303'),
('ITP 4409', '{"req":[["ITP 330","ITP 3330"]]}', 'ITP 330 or ITP 3330'),
('ITP 4410', '{"req":[["BUS 391","BUS 3391"],["ITP 303","ITP 371","ITP 3303","ITP 3371"]]}', 'BUS 391 or BUS 3391; AND (ITP 303, ITP 371, ITP 3303, or ITP 3371)'),
('ITP 4411', '{"req":[["ITP 330","ITP 3330"]]}', 'ITP 330 or ITP 3330'),
('ITP 4415', '{"req":[["ITP 371","ITP 3371"]]}', 'ITP 371 or ITP 3371'),
('ITP 4428', '{"req":[["BUS 310","BUS 3310","BUS 346","BUS 3346","ITP 326","ITP 3326"]]}', 'One of the following: BUS 310, BUS 3310, BUS 346, BUS 3346, ITP 326, or ITP 3326'),
('ITP 4430', '{"req":[["ITP 330","ITP 3330"]]}', 'ITP 330 or ITP 3330'),
('ITP 4475', '{"req":[["ITP 330","ITP 3330"]]}', 'ITP 330 or ITP 3330'),
('ITP 4496', '{"req":[["ITP 233","ITP 2233"],["ITP 260","ITP 2260"],["ITP 326","ITP 3326"],["BUS 346","BUS 3346"]]}', 'ITP 233 or ITP 2233; ITP 260 or ITP 2260; ITP 326 or ITP 3326; AND BUS 346 or BUS 3346'),
('ITP 4497', '{"req":[["ITP 467","ITP 4496"]]}', 'ITP 467 or ITP 4496'),
('ITP 4498', '{"req":[["ITP 341","ITP 3341"],["ITP 408","ITP 4408"],["ITP 475","ITP 4475"]]}', 'ITP 341 or ITP 3341; ITP 408 or ITP 4408; AND ITP 475 or ITP 4475'),
-- Physics (BA) (most are shared with the BS)
('PHYS 1100', '{"req":[]}', 'none'),
('PHYS 1141', '{"req":[["MATH 141","MATH 1261"]],"concurrent":["MATH 141","MATH 1261"]}', 'Corequisite: MATH 141 or MATH 1261'),
('PHYS 1143', '{"req":[["PHYS 142C","PHYS 1141"],["MATH 143","MATH 1262"]],"concurrent":["MATH 143","MATH 1262"]}', 'Prerequisite: PHYS 142C or PHYS 1141. Corequisite: MATH 143 or MATH 1262'),
('PHYS 2211', '{"req":[["PHYS 143","PHYS 143C","PHYS 1143"],["MATH 241","MATH 2263"]]}', 'Prerequisite: PHYS 143, PHYS 143C, or PHYS 1143; and MATH 241 or MATH 2263'),
('PHYS 3301', '{"req":[["PHYS 211","PHYS 2211"],["MATH 143","MATH 1262"]]}', 'Prerequisite: PHYS 211 or PHYS 2211; and MATH 143 or MATH 1262'),
('PHYS 3316', '{"req":[["CSC 101","CSC 1001"],["PHYS 143","PHYS 143C","PHYS 1143"]]}', 'Prerequisite: CSC 101 or CSC 1001; and PHYS 143, PHYS 143C, or PHYS 1143'),
('PHYS 3340', '{"req":[["PHYS 206","PHYS 3316"],["PHYS 211","PHYS 2211"],["PHYS 3339"]],"concurrent":["PHYS 3339"]}', 'Prerequisite: PHYS 206 or PHYS 3316; and PHYS 211 or PHYS 2211. Concurrent: PHYS 3339'),
-- PHYS 3341 ("PHYS 340; or PHYS 3339 and PHYS 3340") is left out: the quarter PHYS 340 is the same class as
-- PHYS 3340 in the crosswalk, so any record would let PHYS 3340 alone count as enough.
('PHYS 4405', '{"req":[["PHYS 305","PHYS 3305"],["PHYS 320","PHYS 3320"]]}', 'Prerequisite: PHYS 305 or PHYS 3305; and PHYS 320 or PHYS 3320'),
('PHYS 4408', '{"req":[["PHYS 320","PHYS 3320"]]}', 'Prerequisite: PHYS 320 or PHYS 3320'),
-- Experience & Event Management (its other EIM courses also need standing or the major — left out)
('EIM 1112', '{"req":[]}', 'none'),
('EIM 1114', '{"req":[]}', 'none'),
('EIM 1160', '{"req":[]}', 'none'),
('EIM 2275', '{"req":[]}', 'none'),
('EIM 4416', '{"req":[["RPTA 360","EIM 3360"]]}', 'RPTA 360 or EIM 3360');

do $$
declare t text; extra text; n int;
begin
  select udt_name into t from information_schema.columns
   where table_schema = 'public' and table_name = 'course_prereqs' and column_name = 'prereq_json';
  if t is null then raise exception 'public.course_prereqs.prereq_json not found — nothing changed'; end if;
  if t not in ('jsonb', 'json', 'text', 'varchar') then raise exception 'prereq_json is %, expected jsonb/json/text — nothing changed', t; end if;
  select string_agg(column_name, ', ') into extra from information_schema.columns
   where table_schema = 'public' and table_name = 'course_prereqs' and is_nullable = 'NO' and column_default is null
     and is_identity = 'NO' and is_generated = 'NEVER'
     and column_name not in ('course_code', 'prereq_json');
  if extra is not null then raise exception 'course_prereqs also needs % — nothing changed; send this message to Claude', extra; end if;
  execute format(
    'insert into public.course_prereqs (course_code, prereq_json)
       select np.code, np.j::%s from np
        where not exists (select 1 from public.course_prereqs p where upper(btrim(p.course_code)) = np.code)',
    case when t = 'varchar' then 'text' else t end);
  get diagnostics n = row_count;
  raise notice 'course_prereqs: % added (% were already there and left as they are)', n, (select count(*) from np) - n;
end $$;

commit;

-- 3. what still has no record (read-only): every class code on the three flowcharts
select f.major, f.code,
       case when exists (select 1 from public.course_prereqs p where upper(btrim(p.course_code)) = f.code)
            then 'has a record' else 'NO RECORD — the app says it can''t check' end as prereqs
  from (values
    ('ITP','ITP 1100'),('ITP','ITP 1125'),('ITP','MATH 1261'),('ITP','MATH 1267'),('ITP','PHYS 1121'),
    ('ITP','ITP 1150'),('ITP','ITP 2233'),('ITP','CHEM 1120'),('ITP','STAT 1110'),('ITP','STAT 1210'),
    ('ITP','ITP 3330'),('ITP','ITP 3371'),('ITP','ECON 2001'),('ITP','ITP 3303'),('ITP','ITP 3326'),
    ('ITP','BUS 3391'),('ITP','ITP 4409'),('ITP','BUS 3346'),('ITP','ITP 3341'),('ITP','ITP 4411'),
    ('ITP','ITP 4464'),
    ('ITP · Industrial Technology','ITP 2260'),('ITP · Industrial Technology','ITP 3390'),('ITP · Industrial Technology','ITP 4403'),
    ('ITP · Industrial Technology','ITP 4410'),('ITP · Industrial Technology','ITP 4415'),('ITP · Industrial Technology','ITP 4428'),
    ('ITP · Industrial Technology','ITP 4496'),('ITP · Industrial Technology','ITP 4497'),
    ('ITP · Packaging','ITP 2234'),('ITP · Packaging','ITP 2241'),('ITP · Packaging','ITP 3334'),('ITP · Packaging','ITP 4408'),
    ('ITP · Packaging','ITP 4430'),('ITP · Packaging','ITP 4475'),('ITP · Packaging','ITP 4498'),
    ('Physics (BA)','PHYS 1100'),('Physics (BA)','CHEM 1120'),('Physics (BA)','MATH 1261'),('Physics (BA)','PHYS 1141'),
    ('Physics (BA)','CSC 1001'),('Physics (BA)','MATH 1262'),('Physics (BA)','PHYS 1143'),('Physics (BA)','MATH 2263'),
    ('Physics (BA)','PHYS 2211'),('Physics (BA)','MATH 2341'),('Physics (BA)','PHYS 3305'),('Physics (BA)','PHYS 3316'),
    ('Physics (BA)','PHYS 3320'),('Physics (BA)','PHYS 3301'),('Physics (BA)','PHYS 3339'),('Physics (BA)','PHYS 3340'),
    ('Physics (BA)','PHYS 4408'),('Physics (BA)','PHYS 3341'),('Physics (BA)','PHYS 4405'),('Physics (BA)','PHYS 4461'),
    ('EEM','EIM 1101'),('EEM','BUS 2212'),('EEM','AGB 2214'),('EEM','STAT 1110'),('EEM','STAT 1210'),('EEM','EIM 2210'),
    ('EEM','BUS 2215'),('EEM','AGB 3323'),('EEM','EIM 2255'),('EEM','EIM 3313'),('EEM','EIM 3360'),('EEM','BUS 3346'),
    ('EEM','ENGL 3310'),('EEM','EIM 3370'),('EEM','EIM 4405'),('EEM','EIM 4416'),('EEM','EIM 4424'),('EEM','EIM 4460'),
    ('EEM','EIM 4461'),('EEM','EIM 4463'),('EEM','EIM 4465')
  ) as f(major, code)
 order by (case when exists (select 1 from public.course_prereqs p where upper(btrim(p.course_code)) = f.code) then 1 else 0 end), f.major, f.code;
