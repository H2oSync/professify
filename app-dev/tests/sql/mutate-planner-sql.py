#!/usr/bin/env python3
"""Mutants for SQL 14 (sql/professify-planner.sql): each one undoes one rule, and check-planner.sql must FAIL.
The migration is restored at the end whatever happens.
Usage (repo root): PSQL=... CREATEDB=... DROPDB=... python3 app-dev/tests/sql/mutate-planner-sql.py"""
import subprocess, sys, os
MIG = 'sql/professify-planner.sql'
ORIG = open(MIG, encoding='utf-8').read()
MUTANTS = [
  ('values in the entries aren\'t checked', "where jsonb_typeof(v) = 'string' and not public.dpr_text_ok(v #>> '{}')))", "where false))"),
  ('flags are kept forever', "  delete from public.dpr_flags where created_at < now() - interval '180 days';\n", ''),
  ('the flag hash never changes', "  new.who_hash := md5(auth.uid()::text || ':' || current_date::text);", "  new.who_hash := md5(auth.uid()::text);"),
  ('queued emails outlive the account', "    alter table public.planner_link_emails add constraint planner_link_emails_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;\n", "", "  user_id      uuid not null references auth.users(id) on delete cascade,", "  user_id      uuid not null,"),
  ('a note key is allowed', "'student_name', 'note', 'notes'))", "'student_name'))"),
  ('a flag\'s major isn\'t checked', "public.dpr_text_ok(new.label) and public.dpr_text_ok(new.major)", "public.dpr_text_ok(new.label)"),
  ('marked lines aren\'t checked', "  and pg_column_size(overrides) < 40000 and public.degree_audit_no_grades(overrides));", "  and pg_column_size(overrides) < 40000);"),
  ('no lock on the flag count', "  perform pg_advisory_xact_lock(hashtext('dpr_flags:' || auth.uid()::text));\n", ''),
]
bad = 0
try:
  for name, *ab in MUTANTS:
    src, ok = ORIG, True
    for a, b in zip(ab[0::2], ab[1::2]):
      if src.count(a) != 1: print(f'ANCHOR {name}: matched {src.count(a)}x'); ok = False; break
      src = src.replace(a, b)
    if not ok: bad += 1; continue
    open(MIG, 'w', encoding='utf-8').write(src)
    r = subprocess.run(['sh', 'app-dev/tests/sql/run-check-planner.sh'], capture_output=True, text=True)
    out = r.stdout + r.stderr
    fail = next((l for l in out.splitlines() if 'FAIL:' in l), '')
    if r.returncode == 0: print(f'SURVIVED  {name}'); bad += 1
    else: print(f'killed    {name}  ({fail.strip()[:110] or "error"})')
finally:
  open(MIG, 'w', encoding='utf-8').write(ORIG)
sys.exit(1 if bad else 0)
