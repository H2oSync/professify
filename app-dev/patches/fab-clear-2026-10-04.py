#!/usr/bin/env python3
"""Champ never sits on the last thing on a page (found while testing 01:15's wider class page).

Champ floats over the bottom right of every tab, up to var(--tb) + 94px from the bottom of the screen, but
the space left at the end of a page (.spacer) was 120px, so with the page scrolled to its end the last row's
right side could still be under Champ — on ECON 2303's class page the second section's + was. The end space
is now var(--tb) + 104px (190px on a phone), so scrolled to the end everything sits above Champ.

Applies after home-deep-recs-blue-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 fab-clear-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
a, b = '.spacer{height:120px}', '.spacer{height:calc(var(--tb) + 104px)}'
if b in s: sys.exit('already patched')
if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x')
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
