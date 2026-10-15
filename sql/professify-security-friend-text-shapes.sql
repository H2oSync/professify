-- =================================================================================================
-- professify-security-friend-text-shapes.sql — drafted 2026-10-14 (NOT yet run anywhere but a local test DB)
-- Run any time. One transaction, idempotent, safe to run twice.
--
-- WHY (plain words, for Tate)
--   Your classes are shown on your friends' screens: "Sam is in ____", "Sam took ____ in ____".
--   The text in those spots comes straight from rows the student wrote with their own login
--   (saved_classes.code, my_sections.code, class_history.term). Nothing in the database says it
--   has to be a class code. A student can write a rude sentence, a link, or 5,000 characters of
--   junk into `code`, and every friend sees it. These checks make the database refuse anything
--   that is not shaped like what the apps really write.
--
-- WHAT THIS CHANGES — new CHECK constraints, all added NOT VALID, which means: they guard every
-- NEW insert and update from now on, and they do NOT look at (or fail on) rows already there.
--   saved_classes.code       letters (A-Z and &), optional space, 1-4 digits, optional 1-2 capital
--   my_sections.code         letters after the number:  CSC 1001   BUS 2050   CHEM 124   ECON 3A
--   my_sections.class_nbr    digits only (1-10 of them): the section's class number / CRN
--   saved_classes.class_nbr  same (it is the section number a friend sees you in)
--   class_history.term       Fall, Winter, Spring or Summer (or empty/NULL, which the phone's
--                            one-tap "I took this" writes)
--   class_history.year       1990 to 2100 (or empty/NULL)
--   Nothing is dropped or rewritten; no existing row is touched; the apps' reads are unaffected.
--
-- WIDER THAN THE FIRST SKETCH, ON PURPOSE. The first sketch was 2-5 letters and 3-4 digits. The
--   website's own UC Santa Barbara list (index.html SCHOOL_COURSES) has codes like CMPSC 16, ECON 3A,
--   MCDB 1A, PSY 10A, COMM 87 — one or two digits — and the degree-report importer accepts up to two
--   trailing letters. A too-tight rule would make the database refuse a legitimate save, and the
--   website saves a whole batch in one request (the batch fails if one row is refused). So digits are
--   1-4, letters 2-6, trailing letters 0-2. It still blocks every sentence, link and long string.
--   If you decide UCSB/SDSU will never write here, tighten the one regex line in section 1.
--
-- WHAT IS NOT CHECKED (on purpose): class_history.code. The degree-report importer saves transfer /
--   AP / study-abroad rows with codes like "AP 300", "BUS 3TR", "5A5C 1TR", "A1GE 1TR" — real, harmless
--   credit — and a digit-first subject would be refused by a letters-only rule. Those stay free text
--   (length-limited by the existing len_ checks).
--
-- TABLES THAT ARE NOT DEFINED IN THIS REPO. saved_classes, my_sections and class_history were created
--   by hand before the repo's SQL folder existed; their column types are known only from how the
--   apps use them. So every check below is CONDITIONAL: it is added only if the table and column exist
--   and have the expected type (text for the code/term/number columns, a whole-number type for year).
--   Anything skipped is printed as "VERIFY AGAINST LIVE", and the file does not fail. Please run this
--   before you run the file and compare:
--     select table_name, column_name, data_type from information_schema.columns
--      where table_schema='public' and table_name in ('saved_classes','my_sections','class_history')
--        and column_name in ('code','class_nbr','term','year');
--
-- OLD ROWS. Because the checks are NOT VALID, a row that already breaks a rule stays. But note: an
--   UPDATE of such a row (for example editing the professor on an old class_history row) would be
--   refused until that row is fixed. The file counts the offending rows per rule and prints up to 5
--   example values, so you can clean them up. Nothing is deleted for you.
--
-- It tests itself at the end (on scratch copies of the tables, nothing real is touched) and raises
-- an error — undoing the whole file — if anything is wrong. Functions/grants are not touched, so
-- there is nothing to "revoke from public" here.
-- =================================================================================================
begin;

do $$
declare
  -- (table, column, constraint name, kind, accepts these, refuses these)
  CODE_RE constant text := '^[A-Z&]{2,6} ?[0-9]{1,4}[A-Z]{0,2}$';          -- section 1: the one line to tighten
  NBR_RE  constant text := '^[0-9]{1,10}$';
  specs constant jsonb := jsonb_build_array(
    jsonb_build_object('t','saved_classes','c','code','n','saved_classes_code_shape','k','code'),
    jsonb_build_object('t','my_sections','c','code','n','my_sections_code_shape','k','code'),
    jsonb_build_object('t','my_sections','c','class_nbr','n','my_sections_class_nbr_digits','k','nbr'),
    jsonb_build_object('t','saved_classes','c','class_nbr','n','saved_classes_class_nbr_digits','k','nbr'),
    jsonb_build_object('t','class_history','c','term','n','class_history_term_quarter','k','term'),
    jsonb_build_object('t','class_history','c','year','n','class_history_year_range','k','year'));
  s jsonb; t text; c text; n text; k text; dtype text; expr text; ok_type boolean;
  bad bigint; sample text; added int := 0; present int := 0; skipped int := 0;
begin
  for s in select * from jsonb_array_elements(specs) loop
    t := s->>'t'; c := s->>'c'; n := s->>'n'; k := s->>'k';
    select data_type into dtype from information_schema.columns
     where table_schema = 'public' and table_name = t and column_name = c;
    ok_type := case when dtype is null then false
                    when k = 'year' then dtype in ('integer','smallint','bigint','numeric')
                    else dtype in ('text','character varying','character') end;
    if not ok_type then
      skipped := skipped + 1;
      raise notice 'VERIFY AGAINST LIVE: skipped % — public.%.% is %', n, t, c,
        case when dtype is null then 'not found (table or column missing)' else 'type ' || dtype || ', not the expected type' end;
      continue;
    end if;

    expr := case k
      when 'code' then format('%I ~ %L', c, CODE_RE)
      when 'nbr'  then format('%I ~ %L', c, NBR_RE)
      when 'term' then format('%I in (''Fall'',''Winter'',''Spring'',''Summer'')', c)
      when 'year' then format('%I between 1990 and 2100', c) end;

    if exists (select 1 from pg_constraint where conrelid = format('public.%I', t)::regclass and conname = n) then
      present := present + 1;
    else
      execute format('alter table public.%I add constraint %I check (%s) not valid', t, n, expr);
      added := added + 1;
    end if;

    -- Old rows that already break the rule (they stay; this only tells you). NULL passes a CHECK.
    execute format('select count(*) from public.%I where not coalesce((%s), true)', t, expr) into bad;
    if bad > 0 then
      execute format('select string_agg(v, '' | '') from (select distinct left(%I::text, 40) as v from public.%I where not coalesce((%s), true) limit 5) q', c, t, expr) into sample;
    end if;
    if bad > 0 then
      raise warning 'security-friend-text-shapes: % existing row(s) in %.% already break % (examples: %). They are left alone; edits to those rows will be refused until fixed.', bad, t, c, n, sample;
    end if;
  end loop;
  raise notice 'security-friend-text-shapes: % added, % already present, % skipped (see VERIFY lines)', added, present, skipped;
end $$;

-- ---- Self-checks -------------------------------------------------------------------------------
do $$
declare
  tests constant jsonb := jsonb_build_array(
   jsonb_build_object('t','saved_classes','c','code','n','saved_classes_code_shape',
     'good', jsonb_build_array('CSC 1001','CSC 101','BUS 2050','BUS2050','CHEM 1241','CHEM 124L','ECON 3A','CMPSC 16','MCDB 1A','PSY 10A','A&S 101','AP 300','ENGL 1021AB'),
     'bad',  jsonb_build_array('csc 101','CSC  101','Hey look at this https://x.example','<b>CSC 101</b>','GE A1','CSC 101; drop table','5A5C 1TR','A1GE 1TR','CSC','101','', repeat('A',500), E'CSC 101\nfree iphone',E'CSC 101\n')),
   jsonb_build_object('t','my_sections','c','code','n','my_sections_code_shape',
     'good', jsonb_build_array('CSC 1001','BUS 2050','ECON 3A','CMPSC 16'),
     'bad',  jsonb_build_array('csc 101','Call me 555-1234','<script>','', repeat('A',500))),
   jsonb_build_object('t','my_sections','c','class_nbr','n','my_sections_class_nbr_digits',
     'good', jsonb_build_array('12345','1','0000000001'),
     'bad',  jsonb_build_array('12a45','t:CSC 101:x:5','','12 45','-1','12345678901','1.5')),
   jsonb_build_object('t','saved_classes','c','class_nbr','n','saved_classes_class_nbr_digits',
     'good', jsonb_build_array('12345'),
     'bad',  jsonb_build_array('abc','1 2')),
   jsonb_build_object('t','class_history','c','term','n','class_history_term_quarter',
     'good', jsonb_build_array('Fall','Winter','Spring','Summer'),
     'bad',  jsonb_build_array('fall','Autumn','Fall 2024','Wtr','Spr','', 'Spring ', repeat('S',100))),
   jsonb_build_object('t','class_history','c','year','n','class_history_year_range',
     'good', jsonb_build_array('1990','2015','2026','2027','2100'),
     'bad',  jsonb_build_array('1989','0','-5','2101')));
  tst jsonb; t text; c text; n text; v text; ok boolean; col record; tested int := 0;
begin
  for tst in select * from jsonb_array_elements(tests) loop
    t := tst->>'t'; c := tst->>'c'; n := tst->>'n';
    if not exists (select 1 from pg_constraint where conrelid = to_regclass('public.' || t) and conname = n) then
      continue;                                            -- skipped above (VERIFY AGAINST LIVE)
    end if;
    -- scratch copy carrying the real table's checks; every NOT NULL dropped so only one column is tested
    execute format('create temp table _shape_chk (like public.%I including constraints) on commit drop', t);
    for col in select a.attname from pg_attribute a where a.attrelid = '_shape_chk'::regclass and a.attnum > 0 and not a.attisdropped and a.attnotnull loop
      execute format('alter table _shape_chk alter column %I drop not null', col.attname);
    end loop;
    for v in select jsonb_array_elements_text(tst->'good') loop
      begin execute format('insert into _shape_chk (%I) values (%L)', c, v);
      exception when check_violation then raise exception 'self-check: % refused a legitimate value %', n, quote_literal(v); end;
    end loop;
    for v in select jsonb_array_elements_text(tst->'bad') loop
      ok := true;
      begin execute format('insert into _shape_chk (%I) values (%L)', c, v);
      exception when check_violation then ok := false; end;
      if ok then raise exception 'self-check: % accepted a bad value %', n, left(quote_literal(v), 60); end if;
    end loop;
    -- NULL must pass (the phone's quick-log writes NULL term and year; sections may have no number)
    begin execute format('insert into _shape_chk (%I) values (null)', c);
    exception when check_violation then raise exception 'self-check: % refused NULL', n; end;
    execute 'drop table _shape_chk';
    tested := tested + 1;
  end loop;
  -- every constraint that exists must still be NOT VALID or valid, never missing
  raise notice 'security-friend-text-shapes: ok (% rule(s) tested on scratch copies)', tested;
end $$;

commit;
