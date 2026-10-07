#!/usr/bin/env python3
"""A professor's page: one colour per rating, matching (Tate, 2026-10-04: "make sure all these greens are
consistent and match", on Chris Ainsworth's page at 5.0 — the circle, AVERAGE's star and the big ★ 5.0 were three
different greens).

The circle's fill, RATE_BRIGHT(step), is now the one colour on this page: AVERAGE's star on the purple header
(was RATE_LIGHT, a paler shade so it read on purple) and the big number with its star (was RATE_DARK). All three
follow the half-star scale together — green at 5.0 down to red at 0.5. Other screens keep their shades.

Applies after share-row-2026-10-04.py (build 09:45).
Usage: python3 prof-page-one-green-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="avgstar rt-${rateTone(r).k}">${starI(15, rateTone(r).fill)}' in s: sys.exit('already patched')
R = [
 ("""<span class="avgstar rt-${rateTone(r).k}">${starI(15, rateTone(r).light)}</span>""",
  """<span class="avgstar rt-${rateTone(r).k}">${starI(15, rateTone(r).fill)}</span>"""),
 ("""<div class="rt-${rateTone(r).k}" style="font-size:44px;font-weight:1000;line-height:1;color:${rateTone(r).ink};display:flex;align-items:center;justify-content:center;gap:4px">${starI(24, rateTone(r).star)}${r.toFixed(1)}</div>""",
  """<div class="rt-${rateTone(r).k}" style="font-size:44px;font-weight:1000;line-height:1;color:${rateTone(r).fill};display:flex;align-items:center;justify-content:center;gap:4px">${starI(24, rateTone(r).fill)}${r.toFixed(1)}</div>"""),

 # RATE_LIGHT (the paler star-on-purple shade) has no caller left: drop it and say so in the scale's comment
 ("""const RATE_LIGHT = s => `hsl(${RATE_HUE[s]} 80% ${[0, 81, 78, 74][s] || 70}%)`;
""", ""),
 (", fill: RATE_BRIGHT(st), light: RATE_LIGHT(st) }; };", ", fill: RATE_BRIGHT(st) }; };"),
 ("INK writes initials on a circle, LIGHT is the star on purple, PALE sits behind a dark",
  "INK writes initials on a circle, PALE sits behind a dark"),
 ("   number (the ★ chip). 5.0's dark is the big\n   5.0's #166534.",
  "   number (the ★ chip). 5.0's dark is #166534. On a professor's page the circle, AVERAGE's star and the big\n   number all use BRIGHT, one colour (2026-10-04)."),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
