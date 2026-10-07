#!/usr/bin/env python3
"""No password "Sign In / Fill User Name" sheet over the Friends search (Tate, 2026-10-04, on iOS: "when i try to
type in the seach this is what comes up. its not necessary").

iOS Safari's password autofill guesses which fields are user names from their words. The Friends search said
"Find friends by name or @username" (placeholder and label), and the add-friend search "Name, email or
@username" — so iOS offered to fill tesims@calpoly.edu into them. The word is now "@handle" (same meaning:
the search still matches usernames), and both fields also carry the opt-outs password managers read
(data-1p-ignore, data-lpignore, data-form-type="other"), plus no autocorrect/capitalising on the second one.

Applies after top-seamless-2026-10-06.py (build 2026-10-06 06:10; first built after grid-edge-gap-2026-10-05.py, then re-based onto story-day-big and top-seamless).
Usage: python3 search-no-autofill-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'or @handle' in s: sys.exit('already patched')
OPT = 'data-1p-ignore data-lpignore="true" data-form-type="other"'
R = [
 ('placeholder="Find friends by name or @username" aria-label="Find friends by name or @username" autocomplete="off"',
  'placeholder="Find friends by name or @handle" aria-label="Find friends by name or @handle" autocomplete="off" ' + OPT),
 ('<input id="pq" value="${esc(UI.peopleQ || \'\')}" placeholder="Name, email or @username" autocomplete="off"',
  '<input id="pq" type="search" value="${esc(UI.peopleQ || \'\')}" placeholder="Name, email or @handle" aria-label="Name, email or @handle" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" ' + OPT),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
