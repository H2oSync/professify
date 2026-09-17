-- ================================================================================================
-- WHICH TERM IS THIS CLASS IN? — 2026-09-12
-- ================================================================================================
-- On 5 October the Spring 2027 schedule appears in Cal Poly's Class Search, and the scraper can be
-- pointed at it by changing one GitHub Actions variable. The app cannot follow, and this is why:
--
--   course_seats      term, class_nbr, ...          <- term is half the key. Fine.
--   my_sections       user_id, code, class_nbr, section, instructor, days, status, wl_pos
--   saved_classes     user_id, code
--   watch_sections    user_id, code, class_nbr, section, instructor, days
--
-- NOTHING THE STUDENT OWNS KNOWS WHAT TERM IT IS IN. Point the client at Spring and every saved
-- schedule is a set of Fall class numbers being looked up in a Spring seat table: the week goes
-- blank. Worse, the next class they add lands in the same undifferentiated list as their Fall
-- ones, and `saved_classes` is keyed on the course code, so planning a Spring section of a course
-- they are taking this term OVERWRITES the Fall row.
--
-- This file does the part that is safe to do today and gets more expensive every day it waits:
-- give those three tables a term, stamp everything that exists as Fall 2026, and widen each
-- table's unique key so two terms can coexist. Nothing on screen changes. With one term in the
-- data a key of (user_id, code, term) is exactly equivalent to (user_id, code) — which is the
-- whole reason to do it NOW rather than on the day a second term arrives.
--
-- WHAT THIS FILE DOES NOT DECIDE: what a student who is enrolled in Fall and planning Spring
-- actually sees. That is a product question — Free Now, "who's in my classes" and friends'
-- schedules are all about the term you are sitting in, and have to keep pointing at Fall until
-- January. This migration only makes that decision possible; it does not make it.
--
-- THE KEYS ARE DISCOVERED, NOT ASSUMED. These three tables were created outside this repo, so
-- their constraints are not written down anywhere I can read. Guessing would be how a Spring row
-- silently overwrites a Fall one. Every unique index is read out of the catalog, printed, and
-- widened; anything unrecognised stops the file rather than being worked around.
--
-- Run in the Supabase SQL editor. Safe to re-run.
-- ================================================================================================

-- ------------------------------------------------------------------------------------------------
-- 0. What is here right now — printed before anything changes
-- ------------------------------------------------------------------------------------------------
do $$
declare r record;
begin
  raise notice '--- before ---';
  for r in
    select c.relname as tbl, i.relname as idx, ix.indisprimary as is_pk, ix.indisunique as is_uq,
           pg_get_indexdef(i.oid) as def
      from pg_class c
      join pg_namespace n on n.oid=c.relnamespace and n.nspname='public'
      join pg_index ix on ix.indrelid=c.oid
      join pg_class i on i.oid=ix.indexrelid
     where c.relname in ('my_sections','saved_classes','watch_sections')
       and ix.indisunique
     order by c.relname, i.relname
  loop
    raise notice '% % % -> %', r.tbl, case when r.is_pk then '[pk]' else '[uq]' end, r.idx, r.def;
  end loop;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 1. The column
-- ------------------------------------------------------------------------------------------------
-- text, not int: Cal Poly's term codes are opaque four-character identifiers that happen to look
-- numeric. course_seats already stores them as text, and two representations of the same key is
-- how a join quietly returns nothing.
--
-- THE DEFAULT IS A TRANSITION CRUTCH AND MUST BE CHANGED ON 5 OCTOBER. This app is a PWA with a
-- service worker: after a deploy some students keep running a cached build for days. A default
-- means a stale client that does not send `term` writes a Fall row rather than a NULL one, which
-- is right today and WRONG the moment Spring is the term being planned. The Oct 5 change is
-- therefore two lines, not one: the client constant, and
--     alter table public.<t> alter column term set default '<new term>';
-- on all three tables. Section 4 checks that the default and the client agree.
do $$
declare t text;
begin
  foreach t in array array['my_sections','saved_classes','watch_sections'] loop
    if to_regclass('public.'||t) is null then
      raise exception 'public.% does not exist — nothing to term-scope', t;
    end if;
    execute format('alter table public.%I add column if not exists term text', t);
    execute format('update public.%I set term = ''2268'' where term is null', t);
    execute format('alter table public.%I alter column term set default ''2268''', t);
    execute format('alter table public.%I alter column term set not null', t);
    raise notice '%: term added, backfilled to 2268, not null, default 2268', t;
  end loop;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 2. Widen every unique key to include term
-- ------------------------------------------------------------------------------------------------
-- Whatever identifies a row today, the identity becomes "that, plus which term". Read from the
-- catalog so this is correct against the real shape rather than the shape I would have guessed.
--
-- Refuses rather than improvises on three things:
--   · a partial or expression index — the column list is not the whole story and a rebuilt copy
--     would silently drop the predicate;
--   · a unique constraint another table's foreign key depends on — dropping it would cascade;
--   · a table with no unique key at all — then the client's upserts are already not doing what
--     they look like they do, and that is a bug to report, not to paper over here.
do $$
declare
  r record;
  cols text[];
  newcols text;
  n_done int := 0;
begin
  for r in
    select c.oid as tbloid, c.relname as tbl, i.relname as idx, i.oid as idxoid,
           ix.indisprimary as is_pk,
           ix.indpred is not null as is_partial,
           ix.indexprs is not null as is_expr,
           con.conname as conname
      from pg_class c
      join pg_namespace n on n.oid=c.relnamespace and n.nspname='public'
      join pg_index ix on ix.indrelid=c.oid
      join pg_class i on i.oid=ix.indexrelid
      left join pg_constraint con on con.conindid=i.oid and con.contype in ('p','u')
     where c.relname in ('my_sections','saved_classes','watch_sections')
       and ix.indisunique
     order by c.relname, i.relname
  loop
    select array_agg(a.attname order by k.ord)
      into cols
      from pg_index ix
      join lateral unnest(ix.indkey) with ordinality as k(attnum, ord) on true
      join pg_attribute a on a.attrelid = ix.indrelid and a.attnum = k.attnum
     where ix.indexrelid = r.idxoid;

    if 'term' = any(cols) then
      raise notice '% %: already includes term (%) — left alone', r.tbl, r.idx, array_to_string(cols,', ');
      continue;
    end if;

    /* A SURROGATE KEY IS NOT AN IDENTITY TO WIDEN. Caught on a replica, 2026-09-12: the first
       version of this block widened a bigserial `id` primary key into (id, term), which is
       strictly weaker than (id) and means nothing — `id` is already unique by itself, so the
       term adds no separation and the change is pure noise in the schema.
       What needs the term is the NATURAL key — the one the client's upsert actually conflicts
       on, (user_id, code) or (user_id, class_nbr). A single column defaulting to nextval() or
       declared as an identity is the machine's own row number; leave it exactly as it is. */
    if array_length(cols,1) = 1 and exists (
      select 1 from pg_attribute a
        left join pg_attrdef d on d.adrelid=a.attrelid and d.adnum=a.attnum
       where a.attrelid = r.tbloid and a.attname = cols[1]
         and (a.attidentity in ('a','d')
              or pg_get_expr(d.adbin, d.adrelid) like 'nextval(%') )
    then
      raise notice '% %: surrogate key on % — left alone, it is already unique by itself',
                   r.tbl, r.idx, cols[1];
      continue;
    end if;

    if r.is_partial or r.is_expr then
      raise exception '% %: partial or expression index — widen it by hand, a rebuilt copy would lose the predicate', r.tbl, r.idx;
    end if;

    if r.conname is not null and exists (
      select 1 from pg_constraint f
       where f.contype='f' and f.confrelid=r.tbloid and f.conindid=r.idxoid)
    then
      raise exception '% %: another table''s foreign key depends on this key — dropping it would cascade. Do this one by hand.', r.tbl, r.idx;
    end if;

    newcols := array_to_string(cols || array['term'], ', ');

    if r.conname is not null then
      /* A constraint, not a bare index: it has to go through ALTER TABLE, and the replacement is
         added in the same statement block so the table is never without a key for longer than this
         transaction. */
      execute format('alter table public.%I drop constraint %I', r.tbl, r.conname);
      execute format('alter table public.%I add constraint %I unique (%s)',
                     r.tbl, left(r.conname || '_term', 63), newcols);
      raise notice '% : constraint % (%) -> % (%)', r.tbl, r.conname, array_to_string(cols,', '),
                   left(r.conname||'_term',63), newcols;
    else
      execute format('drop index public.%I', r.idx);
      execute format('create unique index %I on public.%I (%s)',
                     left(r.idx || '_term', 63), r.tbl, newcols);
      raise notice '% : index % (%) -> % (%)', r.tbl, r.idx, array_to_string(cols,', '),
                   left(r.idx||'_term',63), newcols;
    end if;
    n_done := n_done + 1;
  end loop;

  if n_done = 0 then
    raise notice 'no unique keys needed widening';
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 3. A row count per term, so the backfill is visible rather than assumed
-- ------------------------------------------------------------------------------------------------
do $$
declare t text; n bigint; terms text;
begin
  raise notice '--- after ---';
  foreach t in array array['my_sections','saved_classes','watch_sections'] loop
    execute format('select count(*), coalesce(string_agg(distinct term, '', ''),''(none)'') from public.%I', t)
      into n, terms;
    raise notice '%: % row(s), term(s): %', t, n, terms;
  end loop;
end $$;


-- ------------------------------------------------------------------------------------------------
-- 4. Self-check
-- ------------------------------------------------------------------------------------------------
-- The failure this guards against is the quiet one: the column exists, so everything looks done,
-- but a key was missed and the first Spring row to collide with a Fall one overwrites it.
do $$
declare t text; bad int := 0; missing int;
begin
  foreach t in array array['my_sections','saved_classes','watch_sections'] loop
    if not exists (select 1 from information_schema.columns
                    where table_schema='public' and table_name=t and column_name='term'
                      and is_nullable='NO') then
      raise warning '%: term is missing or nullable', t; bad := bad + 1;
    end if;
    if not exists (select 1 from information_schema.columns
                    where table_schema='public' and table_name=t and column_name='term'
                      and column_default like '%2268%') then
      raise warning '%: term has no 2268 default — a stale cached client would write NULL', t; bad := bad + 1;
    end if;

    /* The same surrogate exemption section 2 applies, and it has to be the same or the file
       refuses a database it just migrated correctly. Found on a replica: with a bigserial `id`
       primary key, section 2 rightly leaves (id) alone and this count rightly found a unique key
       without term in it — so the migration widened everything it should and then failed itself.
       A check that disagrees with the change it is checking is worse than no check. */
    select count(*) into missing
      from pg_class c
      join pg_namespace n on n.oid=c.relnamespace and n.nspname='public'
      join pg_index ix on ix.indrelid=c.oid
      join pg_class i on i.oid=ix.indexrelid
     where c.relname = t and ix.indisunique
       and not exists (
         select 1 from unnest(ix.indkey) as k(attnum)
          join pg_attribute a on a.attrelid=ix.indrelid and a.attnum=k.attnum
         where a.attname='term')
       and not (
         array_length(ix.indkey::int[],1) = 1
         and exists (
           select 1 from pg_attribute a2
             left join pg_attrdef d2 on d2.adrelid=a2.attrelid and d2.adnum=a2.attnum
            where a2.attrelid = c.oid and a2.attnum = ix.indkey[0]
              and (a2.attidentity in ('a','d')
                   or pg_get_expr(d2.adbin, d2.adrelid) like 'nextval(%') ) );
    if missing > 0 then
      raise warning '%: % unique key(s) still do not include term — a second term will overwrite the first', t, missing;
      bad := bad + 1;
    end if;
  end loop;

  if bad = 0 then
    raise notice 'term-scope: all three tables carry a term, stamped 2268, and every unique key includes it';
  else
    raise exception '% problem(s) above — fix before pointing anything at a second term', bad;
  end if;
end $$;


-- ------------------------------------------------------------------------------------------------
-- ON 5 OCTOBER
-- ------------------------------------------------------------------------------------------------
--   1. Find the Spring 2027 term code in Cal Poly's Class Search term dropdown. Do not guess it.
--   2. Set the CP_TERM repository variable to it. The scraper needs nothing else.
--   3. Change PROFESSIFY_TERM in index.html to the same value.
--   4. alter table public.my_sections   alter column term set default '<new>';
--      alter table public.saved_classes alter column term set default '<new>';
--      alter table public.watch_sections alter column term set default '<new>';
--   5. Decide, before any of the above, what a student enrolled in Fall and planning Spring sees.
