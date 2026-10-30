#!/usr/bin/env python3
"""Scale (2026-10-30): the seat-alert upsert on watch_sections named no conflict target. Like saved_classes and
my_sections before 2026-10-30 (upsert-onconflict-2026-10-30.py), watch_sections' term-scoped key is a UNIQUE
(user_id, class_nbr, term) — so without onConflict a supabase-js .upsert() is a plain INSERT, and turning on an
alert that is already on (a second device, a double tap, a retry) fails with 23505 "Couldn't update your seat
alert". It now names its key and updates. Works on app/index.html and index.html (the website); idempotent.
CHECK BEFORE SHIPPING: production must have a unique index on exactly (user_id, class_nbr, term) — otherwise
PostgREST refuses every watch with 42P10. Query:
  select indexrelid::regclass, pg_get_indexdef(indexrelid) from pg_index where indrelid = 'public.watch_sections'::regclass and indisunique;
Usage: python3 scale-watch-onconflict-2026-10-30.py app/index.html index.html"""
import sys, re, pathlib
for f in sys.argv[1:] or ['app/index.html']:
    p = pathlib.Path(f); s = p.read_text(); out = []; i = 0; n = 0
    for m in re.finditer(r"from\((['\"])watch_sections\1\)\.upsert\(", s):
        start = m.end(); depth = 1; j = start; q = None
        while depth:
            ch = s[j]
            if q:
                if ch == '\\': j += 1
                elif ch == q: q = None
            elif ch in '\'"`': q = ch
            elif ch == '(': depth += 1
            elif ch == ')': depth -= 1
            j += 1
        close = j - 1; args = s[start:close]
        if 'onConflict' in args: continue
        sp = ', ' if args.count(', ') else ','
        out.append(s[i:close]); out.append(sp + "{ onConflict: 'user_id,class_nbr,term' }" if sp == ', ' else ",{onConflict:'user_id,class_nbr,term'}"); i = close; n += 1
    out.append(s[i:]); p.write_text(''.join(out)); print(f, 'watch_sections upserts given onConflict:', n)
