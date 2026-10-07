#!/usr/bin/env python3
"""A professor's page: the rating circle has no white ring (Tate, 2026-10-04, on the "Professor Circle Ring" mock:
"do we need a white circle around the color try it without" → "implement no ring").

The 70px circle in the purple header sits straight on the purple; its 3px white ring is gone. Nothing else moves.

Applies after delete-account-2026-10-04.py (build 15:35).
Usage: python3 prof-circle-no-ring-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
a = """style="width:70px;height:70px;background:${t.bg};color:${t.ink};font-size:22px;box-shadow:0 0 0 3px #fff">${esc(p.ini)}</span>"""
b = """style="width:70px;height:70px;background:${t.bg};color:${t.ink};font-size:22px">${esc(p.ini)}</span>"""
if s.count(a) == 0 and s.count(b) == 1: sys.exit('already patched')
n = s.count(a)
if n != 1: sys.exit(f'anchor matched {n}x')
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
