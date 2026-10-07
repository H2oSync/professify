#!/usr/bin/env python3
"""A class's and a professor's page at Home's width, like Schedule (Tate, 2026-10-04, on a class page's Sections:
"make sure to utualise the horizontal space like we changed on schedules for these as well professor and sections").

- The hero and every card on a class page and a professor page sit 12px from the screen edge (was 16), as Home
  and Schedule do since 07:15 / 10:15.
- Sections cards: 8px inside the card (was 12); a section row is 12px / 8px inside (was 14 / 10) with an 8px gap.
- A section's time never splits ("12:00–" / "1:50"): the time range stays on one line, and moves under the
  days as a whole if it has to.
- The "Sections" heading lines up with the card (16px).

Applies after search-no-autofill-2026-10-04.py.
Usage: python3 class-prof-width-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.secrow .nw{' in s: sys.exit('already patched')
a = s.index('SCREENS.classDetail = ({ code }) => {')
b = s.index('SCREENS.profDetail = ({ id }) => {')
c = s.index('\n};\n', b) + 4
seg = s[a:c]
n1, n2 = seg.count('margin:14px 16px 0'), seg.count('margin:0 16px 12px;padding:12px')
if (n1, n2) != (5, 1): sys.exit(f'card margins changed: {n1}, {n2}')
seg = seg.replace('margin:14px 16px 0', 'margin:14px 12px 0').replace('margin:0 16px 12px;padding:12px', 'margin:0 12px 12px;padding:8px')
R = [
 ('<div class="sec-h" style="padding-left:18px"><span>Sections</span></div>', '<div class="sec-h" style="padding-left:16px"><span>Sections</span></div>'),
 (" ${s.async ? 'self-paced' : s.noTime ? 'Time not posted' : range(s)}</span>${secSeatText(s)}",
  " <span class=\"nw\">${s.async ? 'self-paced' : s.noTime ? 'Time not posted' : range(s)}</span></span>${secSeatText(s)}"),
]
for x, y in R:
    if seg.count(x) != 1: sys.exit(f'anchor matched {seg.count(x)}x: {x[:80]}')
    seg = seg.replace(x, y)
s = s[:a] + seg + s[c:]
C = [
 ('.hero{margin:0 16px;', '.hero{margin:0 12px;'),
 ('.secrow{display:flex;align-items:center;gap:10px;background:var(--bg);border-radius:18px;padding:10px 10px 10px 14px;margin-top:8px}',
  '.secrow{display:flex;align-items:center;gap:8px;background:var(--bg);border-radius:18px;padding:10px 8px 10px 12px;margin-top:8px}\n.secrow .nw{white-space:nowrap}'),
]
for x, y in C:
    if s.count(x) != 1: sys.exit(f'anchor matched {s.count(x)}x: {x[:80]}')
    s = s.replace(x, y)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
