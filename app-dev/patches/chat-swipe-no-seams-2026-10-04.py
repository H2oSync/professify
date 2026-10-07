#!/usr/bin/env python3
"""No red / blue lines between chats (Tate, 2026-10-04, on the Chats list after 18:30: "revert so it dosnt have
these red lines between friedns").

The swipe's Pin (blue) and Delete (red) buttons sat behind every row all the time, so their colour bled through
at the row edges and the card's rounded corners as thin blue and red lines. Now they exist on screen only while
a row is actually slid: a row gets .sw-on when it moves, and loses it once it has slid back closed.

Applies after chat-swipe-2026-10-04.py.
Usage: python3 chat-swipe-no-seams-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.sw-on' in s: sys.exit('already patched')
R = [
 (".swacts{position:absolute;top:0;right:0;bottom:0;display:flex}\n",
  ".swacts{position:absolute;top:0;right:0;bottom:0;display:flex}\n"
  "/* the buttons exist only while a row is slid, so no blue / red shows at the row edges (Tate, 2026-10-04) */\n"
  ".swrow:not(.sw-on) > .swacts{visibility:hidden}\n"),
 ("function swSet(row, x, anim) { const th = row && row.querySelector(':scope > .thread'); if (!th) return; row.classList.toggle('drag', !anim); th.style.transform = x ? `translateX(${x}px)` : ''; }",
  "function swSet(row, x, anim) { const th = row && row.querySelector(':scope > .thread'); if (!th) return; row.classList.toggle('drag', !anim); th.style.transform = x ? `translateX(${x}px)` : '';\n"
  "  clearTimeout(row._swOff);\n"
  "  if (x) row.classList.add('sw-on');\n"
  "  else if (!anim) row.classList.remove('sw-on');\n"
  "  else row._swOff = setTimeout(() => { if (!th.style.transform) row.classList.remove('sw-on'); }, 260); }"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
