#!/usr/bin/env python3
"""A professor's header stars (Tate, 2026-10-03).

1. AVERAGE: the plain star shape in the rating's colour, no white circle ("keep the same star shape but make it
   green not the circle with star inside"). The app's star icon at about the old ★'s size (15px), filled with
   rateTone(r).star — green at the top, amber in the middle, red at the bottom, as everywhere else. No rating, no
   star.
2. The Rate button: an empty (outline) star, the tab bar's Rate icon, in the button's own purple ("instead of a
   green star here have it an empty star like this").

Applies after the 12:00 merge (chat-actions-2026-10-03.py and the rest), after prof-hero-stars-2026-10-03.py.
Usage: python3 avg-star-plain-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.avgstar{display:inline-flex' in s: sys.exit('already patched')
R = [
 ("""<span class="avgstar rt-${rateTone(r).k}">${starI(12, rateTone(r).star)}</span>""",
  """<span class="avgstar rt-${rateTone(r).k}">${starI(15, rateTone(r).star)}</span>"""),
 (".avgstar{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#fff;vertical-align:middle;margin-right:6px}",
  ".avgstar{display:inline-flex;vertical-align:-2px;margin-right:5px}"),
 ("""<span class="rstar">${starI(17, '#16A34A')}</span>""",
  """<span class="rstar">${ic('star', 19, 2.2)}</span>"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
