#!/usr/bin/env python3
"""Schedule's My Classes and Plans at Home's widths (Tate, 2026-10-04, on My Classes' week next to a Home card:
"i thought we talked about updating the horizontal size on schedule we already changed it on homepage we need to
update the same on plans and my classes").

- The week card sits 12px from the screen edge (was 16); the week sits 8px inside it with a 26px hour column and
  5px day gaps (was 14 / 30 / 6) — the same 59.8px day as Home and a friend's page at 390px.
- Everything else on those two tabs shares the 12px edge: the class cards under My Classes, the plan switch, the
  No set time card and the day-by-day cards under a plan. The Share bar's words and the muted notes sit 2px inside
  it, the footer line 4px.
- Reverses 07:15's "Schedule keeps 16 / 14 / 30 / 6". The Planner tab, the page title and the tab row are unchanged.

Applies after share-row-2026-10-04.py (build 2026-10-04 09:45).
Usage: python3 schedule-width-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '.schpg .grid' in s: sys.exit('already patched')
R = [
 (".fweek .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}\n",
  ".fweek .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}\n"
  "/* Schedule's My Classes and Plans at Home's widths (Tate, 2026-10-04) */\n"
  ".schpg .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}\n"
  ".schpg .pad{padding:0 12px}\n"
  ".schpg .agenda,.schpg .anytime{margin-left:12px;margin-right:12px}\n"
  ".schpg .regbar{margin-left:14px;margin-right:14px}\n", 1),
 ("<div class=\"card\" style=\"margin:10px 16px 0;padding:14px 0 12px\">${!TC.seatsLoaded ? loadingCard('Loading sections…')",
  "<div class=\"card\" style=\"margin:10px 12px 0;padding:14px 0 12px\">${!TC.seatsLoaded ? loadingCard('Loading sections…')", 1),
 ("<div class=\"card\" style=\"margin:10px 16px 0;padding:14px 0 12px\">${grid(secs, {",
  "<div class=\"card\" style=\"margin:10px 12px 0;padding:14px 0 12px\">${grid(secs, {", 1),
 ("style=\"margin:12px 16px 0;width:calc(100% - 32px)\" data-a=\"openClass\" data-x=\"${code}\">",
  "style=\"margin:12px 12px 0;width:calc(100% - 24px)\" data-a=\"openClass\" data-x=\"${code}\">", 2),
 # the muted lines under the plan bar and the footer line follow the new edge (2px and 4px inside the cards)
 ("padding:6px 18px\">${TC.err.plans", "padding:6px 14px\">${TC.err.plans", 1),
 ("padding:6px 18px\">${miss} section", "padding:6px 14px\">${miss} section", 1),
 ("padding:12px 20px 0;line-height:1.45\">Plans use", "padding:12px 16px 0;line-height:1.45\">Plans use", 1),
 (" ${inner}<div class=\"spacer\"></div>`, tabbar: true, fab: true",
  " ${t === 'planner' ? inner : `<div class=\"schpg\">${inner}</div>`}<div class=\"spacer\"></div>`, tabbar: true, fab: true", 1),
]
for a, b, n in R:
    if s.count(a) != n: sys.exit(f'anchor matched {s.count(a)}x (want {n}): {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
