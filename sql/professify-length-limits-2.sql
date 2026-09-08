-- ================================================================================================
-- LENGTH LIMITS, SECOND PASS — 2026-09-07
-- ================================================================================================
-- The first pass capped the 33 columns I had listed by hand. Its own self-check then named 22 more
-- that a student can write to and that still had no ceiling — columns I had not thought of
-- (watch_sections.*, reviews.format, reports.status) plus the four on the new events table.
-- That is the self-check doing its job; this file is the answer to it.
--
-- Same rules as the first pass: count the rows that would fail BEFORE adding the constraint, skip
-- and report a column that has long rows rather than aborting the file, NOT VALID then VALIDATE so
-- the add does not take a long exclusive lock. Safe to re-run.
--
-- On the events caps specifically: log_events() already truncates with left(name,40),
-- left(subject,160), left(surface,40), left(who,32). The caps here are set to exactly those
-- numbers, so the function can never violate them — they are a backstop against a direct insert,
-- not a second, tighter limit that could start rejecting normal traffic.
-- ================================================================================================

do $$
declare
  t        record;
  over     bigint;
  c_name   text;    -- not `conname`: that is a pg_constraint column and the reference would bind
  added    int := 0;
  skipped  int := 0;
  absent   int := 0;
begin
  for t in
    select * from (values
      ('conversations',         'kind',                40),
      ('events',                'name',                40),
      ('events',                'subject',            160),
      ('events',                'surface',             40),
      ('events',                'who',                 32),
      ('messages',              'kind',                40),
      ('my_sections',           'class_nbr',           20),
      ('my_sections',           'instructor',         160),
      ('my_sections',           'status',              40),
      ('professor_suggestions', 'professor_name',     160),
      ('profiles',              'phone_hash',         128),
      ('reports',               'kind',                40),
      ('reports',               'reason',             200),
      ('reports',               'status',              40),
      ('reviews',               'course_key',          80),
      ('reviews',               'format',              40),
      ('reviews',               'hours',               20),
      ('saved_classes',         'class_nbr',           20),
      ('watch_sections',        'class_nbr',           20),
      ('watch_sections',        'days',               120),
      ('watch_sections',        'instructor',         160),
      ('watch_sections',        'section',             20)
    ) as v(tbl, col, cap)
  loop
    if to_regclass('public.' || t.tbl) is null then
      absent := absent + 1; continue;
    end if;
    if not exists (
      select 1 from information_schema.columns
       where table_schema='public' and table_name=t.tbl and column_name=t.col
         and data_type in ('text','character varying','character'))
    then
      absent := absent + 1; continue;
    end if;

    c_name := 'len_' || t.tbl || '_' || t.col;
    if exists (select 1 from pg_constraint pc where pc.conname = c_name) then
      continue;
    end if;

    execute format('select count(*) from public.%I where length(%I) > %s', t.tbl, t.col, t.cap)
       into over;

    if over > 0 then
      raise notice 'SKIPPED %.% — % existing row(s) longer than %. Shorten them, then re-run.',
                   t.tbl, t.col, over, t.cap;
      skipped := skipped + 1;
    else
      execute format('alter table public.%I add constraint %I check (length(%I) <= %s) not valid',
                     t.tbl, c_name, t.col, t.cap);
      execute format('alter table public.%I validate constraint %I', t.tbl, c_name);
      added := added + 1;
    end if;
  end loop;

  raise notice '--- % added, % skipped, % not on this deploy ---', added, skipped, absent;
end $$;

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK — read-only. Returns rows, so the SQL editor shows it. Empty result = everything
-- a student can write to now has a ceiling.
-- ------------------------------------------------------------------------------------------------
select c.table_name || '.' || c.column_name as still_uncapped
  from information_schema.columns c
 where c.table_schema='public'
   and c.data_type in ('text','character varying')
   and c.table_name in ('profiles','reviews','messages','conversations','groups',
                        'community_posts','professor_suggestions','class_history',
                        'saved_classes','watch_sections','my_sections','free_now',
                        'class_waivers','reports','suspensions','events')
   and c.character_maximum_length is null
   and not exists (select 1 from pg_constraint pc
                    where pc.conrelid = to_regclass('public.'||c.table_name)
                      and pc.contype='c'
                      and pg_get_constraintdef(pc.oid) like '%length(' || quote_ident(c.column_name) || ')%')
 order by 1;
