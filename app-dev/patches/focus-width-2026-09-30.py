#!/usr/bin/env python3
"""A tapped day spreads to 2/3 of the width it used to take, so the other days squeeze less.
(Tate, 2026-09-30: "for the size of spread when you click on a day lets make it a bit less intense
maybe 2/3 what it is right now so the other days dont compress as much")

Before: the tapped day was minmax(0,1fr) and every other day 32px, so the tapped day took everything
left over. Now each other day is (avail / 3n + 64/3 px) wide, where avail is the body width minus the
hour-label column (--glab, 30px; 26px on Home) and the gaps (--ggap); the tapped day keeps the remainder, which works out to exactly 2/3 of
what it had: avail - n*w = 2/3 * (avail - 32n). On a 4-day card at 390px: 180px -> 120px tapped,
32px -> 52px for the others. Floors: the tapped day never goes under 110px (so a 5-day card at
360px keeps the old layout) and no other day under 32px.

Applies after home-width-2026-09-30.py (07:15).
Usage: python3 focus-width-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const otherW' in s: sys.exit('already patched')
a = "  const tmpl = focus ? `grid-template-columns:var(--glab,30px) ${days.map(d => d === focus ? 'minmax(0,1fr)' : '32px').join(' ')}` : '';"
b = ("  /* The tapped day takes 2/3 of what it used to (Tate, 2026-09-30): each other day is avail/(3n) + 64/3 px,\n"
     "     but the tapped day never drops under 110px (room for code, time and faces) and the others never under 32px. */\n"
     "  const nOther = days.length - 1, A = `(100% - var(--glab,30px) - var(--ggap,6px) * ${days.length})`;\n"
     "  const otherW = nOther ? `max(32px, min(${A} / ${3 * nOther} + 21.333px, (${A} - 110px) / ${nOther}))` : '32px';\n"
     "  const tmpl = focus ? `grid-template-columns:var(--glab,30px) ${days.map(d => d === focus ? 'minmax(0,1fr)' : otherW).join(' ')}` : '';")
if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x')
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
