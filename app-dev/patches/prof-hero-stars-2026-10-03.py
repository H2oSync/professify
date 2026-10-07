#!/usr/bin/env python3
"""A professor's purple header: coloured stars (Tate, 2026-10-03: "make the star on 5 green and if it was 1 it would
be red make sure that these are color coordinated too. also the yellow star make it green").

1. AVERAGE: the star takes the rating's colour from rateTone(), the same cut-offs the big rating number below and
   every other rating in the app use (PolyRatings 3.3+/4 green, 2.5+ amber, below red). On the purple header a
   green or red star alone is too faint, so it sits in a small white circle.
2. The "Rate <name>" button's star is green (was amber), drawn with the app's star icon.

Applies after teach-arrow-no-hint-2026-10-03.py.
Usage: python3 prof-hero-stars-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="avgstar' in s: sys.exit('already patched')
R = [
 ("""<div class="stat"><small>AVERAGE</small><b>${r != null ? '★ ' + r.toFixed(1) : '—'}</b></div>""",
  """<div class="stat"><small>AVERAGE</small><b>${r != null ? `<span class="avgstar rt-${rateTone(r).k}">${starI(12, rateTone(r).star)}</span>${r.toFixed(1)}` : '—'}</b></div>"""),
 ("""<span style="color:#D97706">★</span>&nbsp; ${mine ?""",
  """<span class="rstar">${starI(17, '#16A34A')}</span>${mine ?"""),
 (".stat b{font-size:16px;font-weight:900}",
  """.stat b{font-size:16px;font-weight:900}
.avgstar{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#fff;vertical-align:middle;margin-right:6px}
.rstar{display:inline-flex;margin-right:8px;vertical-align:-3px}"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
