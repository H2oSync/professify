#!/usr/bin/env python3
"""Tate, 2026-10-30: "you can't add or edit" a class the Degree Progress Report saved — "That's already
there." On production saved_classes and my_sections have NO primary key, only UNIQUE indexes
(saved_classes_pkey_term (user_id, code, term); my_sections_pkey_term (user_id, class_nbr, term)), so a
supabase-js .upsert() without onConflict is a plain INSERT and re-saving any saved class is a 23505.
Every upsert on those two tables now names its unique key, so it updates instead. Works on app/index.html
and index.html (the website). Idempotent: an upsert that already names onConflict is left alone."""
import sys, re, pathlib
KEYS = {'saved_classes': 'user_id,code,term', 'my_sections': 'user_id,class_nbr,term'}
for f in sys.argv[1:] or ['app/index.html']:
    p = pathlib.Path(f); s = p.read_text(); out = []; i = 0; n = 0
    for m in re.finditer(r"from\((['\"])(saved_classes|my_sections)\1\)\.upsert\(", s):
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
        out.append(s[i:close]); out.append(", { onConflict: '%s' }" % KEYS[m.group(2)]); i = close; n += 1
    out.append(s[i:]); p.write_text(''.join(out)); print(f, 'upserts given onConflict:', n)
