#!/usr/bin/env python3
"""Schedule's Share takes the colour of what it shares (Tate, 2026-10-04: "for the share on schedule have it
change color to the different colors of the my classes and plans").

The round button at the top right of Schedule is filled with the place's own colour, white arrow: My Classes
blue, Plan A teal, Plan B orange, Plan C rose — the same colours as the selected chip under it (.dest-mine /
.plan-A|B|C, from add-to-week and the plans). White on each is 5:1 or better.

Applies after share-prof-class-2026-10-04.py.
Usage: python3 schedule-share-colour-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'schshare ${' in s: sys.exit('already patched')
R = [
 ("  return `<button class=\"iconbtn schshare\" data-a=\"shareOpen\"",
  "  return `<button class=\"iconbtn schshare ${w === 'mine' ? 'dest-mine' : 'plan-' + w}\" data-a=\"shareOpen\""),
 (".schshare[disabled]{opacity:.5}\n",
  ".schshare[disabled]{opacity:.5}\n"
  "/* filled with the colour of what it shares: My Classes blue, Plan A teal, B orange, C rose (Tate, 2026-10-04) */\n"
  ".iconbtn.schshare{background:var(--pc);color:#fff;box-shadow:0 1px 2px rgba(15,23,42,.06),0 6px 16px var(--pc-glow);transition:background .2s,box-shadow .2s}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
