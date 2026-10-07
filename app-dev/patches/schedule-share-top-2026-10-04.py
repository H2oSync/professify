#!/usr/bin/env python3
"""Share at the top right of Schedule, like a professor's or a class's page (Tate, 2026-10-04, on the
"Friends can see · Share" row under a plan's week: "move the share button to the top right similar to
professor and teacher").

- Schedule's title row gets the same round share button a professor's / class's page has (top right).
  It shares what you're looking at: My Classes (this term's chip) or the plan that's open.
  Planner, and My Classes on another term's chip, have nothing to share and show no button.
- The bar under the week keeps only a plan's "Friends can see" / "Only you". My Classes has no bar.

Applies after support-email-2026-10-04.py (19:15).
Usage: python3 schedule-share-top-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'schshare' in s: sys.exit('already patched')
R = [
 # a plan's bar: who can see it, alone
 ("<button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"${S.plan}\" aria-label=\"Share Plan ${S.plan}\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>",
  "</div>"),
 # My Classes: no bar
 ("  <div class=\"regbar under\" style=\"justify-content:flex-end\"><button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"mine\" aria-label=\"Share your week\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>\n",
  ""),
 # the title row
 ("    body: `<div class=\"title\">Schedule</div>\n <div class=\"stabs\">",
  "    body: `<div class=\"fhdr schhdr\"><div class=\"title\">Schedule</div>${schShareBtn()}</div>\n <div class=\"stabs\">"),
 ("SCREENS.schedule = () => {\n",
  "/* What Schedule's top-right Share sends: the open plan, or My Classes on this term's chip. */\n"
  "function schShareWhat() {\n"
  "  if (S.schedTab === 'plans') return /^[ABC]$/.test(S.plan) ? S.plan : null;\n"
  "  if (S.schedTab === 'mine') return mineTerm().code === CFG.TERM ? 'mine' : null;\n"
  "  return null;\n"
  "}\n"
  "function schShareBtn() {\n"
  "  const w = schShareWhat(); if (!w) return '';\n"
  "  return `<button class=\"iconbtn schshare\" data-a=\"shareOpen\" data-x=\"${w}\" aria-label=\"${w === 'mine' ? 'Share your week' : 'Share Plan ' + w}\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 20, 2.2)}</button>`;\n"
  "}\n"
  "SCREENS.schedule = () => {\n"),
 (".shbtn[disabled]{opacity:.5}\n",
  ".shbtn[disabled]{opacity:.5}\n.schshare[disabled]{opacity:.5}\n.schhdr{min-height:70px}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
