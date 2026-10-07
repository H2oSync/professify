#!/usr/bin/env python3
"""Anytime chips in the class blocks' light blue (Tate, 2026-10-04).

"bring back the consistent color to the anytime classes so they have the light blue around them like
these classes": the chips in a Home card's ANYTIME tray (and the friend page's) take the week's block
colour (--blue-soft2 fill, --blue-ink text) instead of white. On a plan's grid they follow the plan
colour, as its blocks do. The yellow "same class" ring stays.

Applies after share-under-week-2026-10-04.py.
Usage: python3 anytime-blue-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.plancol .any-c{' in s: sys.exit('already patched')
a = "border-radius:10px;background:#fff;color:var(--blue-ink);font-size:13px;line-height:1.15;font-weight:900;"
if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x')
s = s.replace(a, "border-radius:10px;background:var(--blue-soft2);color:var(--blue-ink);font-size:13px;line-height:1.15;font-weight:900;")
b = ".any-c.shared{box-shadow:inset 0 0 0 2.5px var(--yellow)}"
if s.count(b) != 1: sys.exit(f'anchor matched {s.count(b)}x')
s = s.replace(b, b + "\n.plancol .any-c{background:var(--pc-soft2);color:var(--pc-ink)}")
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
