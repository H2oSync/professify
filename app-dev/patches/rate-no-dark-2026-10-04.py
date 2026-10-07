#!/usr/bin/env python3
"""No black behind the rating form (Tate, 2026-10-04: "for rating lets change the black background and just have
whatever would naturally be behind it").

The rating form and the "Thanks" screen after it were "dark" screens: a navy band behind the top of the sheet,
a navy status bar and phone strip, and navy showing when you pulled the page down. Both are now ordinary
screens: the app's own light background sits behind the sheet (status bar, strip and overscroll all light),
and the sheet keeps its rounded top and grabber with a soft shadow so it still reads as a sheet.

Applies after agenda-class-names-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 rate-no-dark-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.rf{min-height:100%;background:none}' in s: sys.exit('already patched')
R = [
 ("    dark: true, body: `<div class=\"rf\"><div class=\"rf-sheet\"><div class=\"grab\"",
  "    body: `<div class=\"rf\"><div class=\"rf-sheet\"><div class=\"grab\"", 1),
 ("    dark: true, body: `<div class=\"rf\"><div class=\"rf-sheet\" style=\"padding-bottom:40px\">",
  "    body: `<div class=\"rf\"><div class=\"rf-sheet\" style=\"padding-bottom:40px\">", 1),
 (".rf{min-height:100%;background:linear-gradient(#0F172A,#1E293B) top/100% 140px no-repeat}",
  ".rf{min-height:100%;background:none}", 1),
 (".rf-sheet{background:var(--bg);border-radius:28px 28px 0 0;margin-top:52px;min-height:calc(100% - 52px);",
  ".rf-sheet{background:var(--bg);border-radius:28px 28px 0 0;margin-top:14px;min-height:calc(100% - 14px);box-shadow:0 -1px 0 rgba(15,23,42,.05),0 -10px 30px rgba(22,51,107,.08);", 1),
]
for a, b, n in R:
    if s.count(a) != n: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
