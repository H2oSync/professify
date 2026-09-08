-- ================================================================================================
-- maxlength IS NOT A CONTROL — 2026-09-07
-- ================================================================================================
-- Every form in Professify caps what you can type. Not one of those caps exists in the database.
--
--     <input maxlength="600">          the browser stops you at 600
--     POST /rest/v1/reviews            nothing stops you at all
--
-- `maxlength` is a hint to a text box. PostgREST is a public HTTP API and the RLS policies check
-- WHO you are, never HOW MUCH you sent. One request inserts a ten-megabyte review, which is two
-- problems at once: every screen that renders it has to lay out ten megabytes of text, and the
-- free tier is 500 MB.
--
-- HOW THE CAPS WERE PICKED: comfortably above the matching form limit, so nothing a student has
-- already written can fail, and low enough to be a real ceiling. A 600-character note gets 4000.
--
-- THIS FILE CANNOT BREAK A DEPLOY, by construction. `alter table ... add check` fails outright if
-- one existing row violates it, and on a live database that is an aborted migration at best. So
-- every constraint is added only after counting the rows that would fail. If any would, the
-- constraint is SKIPPED and the count is printed — you decide what to do about those rows rather
-- than the migration deciding for you. Missing tables and missing columns are skipped the same way.
--
-- Safe to re-run.
-- ================================================================================================

do $$
declare
  t        record;
  over     bigint;
  c_name   text;   -- NOT `conname`: that is also a pg_constraint column, and the reference
                   -- inside the exists() below resolves to the variable, silently matching every row
  added    int := 0;
  skipped  int := 0;
  absent   int := 0;
begin
  for t in
    select * from (values
      -- profile ------------------------------------------------------------------
      ('profiles',              'display_name',       80),
      ('profiles',              'username',           40),
      ('profiles',              'instagram_handle',   60),
      ('profiles',              'major',             120),
      ('profiles',              'concentration',     120),
      ('profiles',              'class_standing',     40),
      ('profiles',              'avatar_url',        512),
      ('profiles',              'edu_email',         254),   -- the RFC maximum
      -- reviews ------------------------------------------------------------------
      ('reviews',               'note',             4000),
      ('reviews',               'course',             40),
      ('reviews',               'professor_key',     200),
      ('reviews',               'professor_name',    160),
      ('reviews',               'department',        120),
      ('reviews',               'grade',               8),
      -- messaging ----------------------------------------------------------------
      ('messages',              'body',             4000),
      ('conversations',         'title',             120),
      ('groups',                'name',               80),
      -- everything else a student can write --------------------------------------
      ('community_posts',       'body',             4000),
      ('community_posts',       'kind',               40),
      ('community_posts',       'term',               40),
      ('professor_suggestions', 'professor_key',     200),
      ('professor_suggestions', 'note',             1000),
      ('class_history',         'code',               40),
      ('class_history',         'term',               40),
      ('class_history',         'professor',         160),
      ('saved_classes',         'code',               40),
      ('watch_sections',        'code',               40),
      ('my_sections',           'code',               40),
      ('my_sections',           'section',            20),
      ('my_sections',           'prof',              160),
      ('my_sections',           'days',              120),
      ('free_now',              'note',              200),
      ('class_waivers',         'code',               40),
      ('class_waivers',         'reason',             40),
      -- moderation ---------------------------------------------------------------
      ('reports',               'note',             2000),
      ('reports',               'target_id',         200),
      ('reports',               'action_taken',      500),
      ('suspensions',           'reason',            500)
    ) as v(tbl, col, cap)
  loop
    -- table, then column, then type. A jsonb or uuid column named the same thing is not ours.
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
      continue;                                   -- already done on an earlier run
    end if;

    execute format('select count(*) from public.%I where length(%I) > %s', t.tbl, t.col, t.cap)
       into over;

    if over > 0 then
      raise notice 'SKIPPED %.% — % existing row(s) are longer than %. Shorten them, then re-run.',
                   t.tbl, t.col, over, t.cap;
      skipped := skipped + 1;
    else
      execute format('alter table public.%I add constraint %I check (length(%I) <= %s) not valid',
                     t.tbl, c_name, t.col, t.cap);
      -- NOT VALID skips the full-table scan on add; validating separately takes a weaker lock, and
      -- we already know every current row passes because of the count above.
      execute format('alter table public.%I validate constraint %I', t.tbl, c_name);
      added := added + 1;
    end if;
  end loop;

  raise notice '--- % constraint(s) added, % skipped for long rows, % column(s) not on this deploy ---',
               added, skipped, absent;
end $$;

-- ------------------------------------------------------------------------------------------------
-- SELF-CHECK — names any text column a student can write to that still has no ceiling.
-- Read-only. Anything listed is a column somebody can put a megabyte into.
-- ------------------------------------------------------------------------------------------------
do $$
declare r record; n int := 0;
begin
  for r in
    select c.table_name, c.column_name
      from information_schema.columns c
     where c.table_schema = 'public'
       and c.data_type in ('text','character varying')
       and c.table_name in ('profiles','reviews','messages','conversations','groups',
                            'community_posts','professor_suggestions','class_history',
                            'saved_classes','watch_sections','my_sections','free_now',
                            'class_waivers','reports','suspensions')
       and c.character_maximum_length is null
       and not exists (
         select 1 from pg_constraint pc
          where pc.conrelid = to_regclass('public.' || c.table_name)
            and pc.contype = 'c'
            and pg_get_constraintdef(pc.oid) like '%length(' || quote_ident(c.column_name) || ')%')
     order by 1,2
  loop
    n := n + 1;
    raise notice 'STILL UNCAPPED: public.%.%', r.table_name, r.column_name;
  end loop;
  if n = 0 then
    raise notice 'OK — every writable text column on these tables has a ceiling';
  else
    raise notice '% column(s) above have no length ceiling. Add them to the list and re-run.', n;
  end if;
end $$;
