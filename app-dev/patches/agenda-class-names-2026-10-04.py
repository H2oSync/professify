#!/usr/bin/env python3
"""The day lists under a plan's week show each class's name, not just its number (Tate, 2026-10-04: "lets display
names of the acutal classes here because its repetitive to just use the numbers").

Each row is now: the code (as before), the class's catalog name on its own line (one line, cut with … if long),
then the professor · seats line. The name comes from courseName() — the real Cal Poly catalog / class-search
title. If we have no name for a class, the line is left out (never made up).

Applies after ptr-sideways-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 agenda-class-names-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.arow .cn{' in s: sys.exit('already patched')
R = [
 ('<span class="grow"><span style="font-weight:900;font-size:16px">${s.code}</span><span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))} · ${secSeatText(s)}</span></span>${avStack(fr, 26)}</button>',
  '<span class="grow"><span style="font-weight:900;font-size:16px">${s.code}</span>${courseName(s.code) ? `<span class="cn">${esc(courseName(s.code))}</span>` : \'\'}<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))} · ${secSeatText(s)}</span></span>${avStack(fr, 26)}</button>'),
 ('.arow .vb{width:4px;',
  '.arow .grow{min-width:0}\n.arow .cn{display:block;font-size:14.5px;font-weight:800;color:var(--ink,#0F172A);line-height:1.3;margin:1px 0 2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.arow .vb{width:4px;'),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
