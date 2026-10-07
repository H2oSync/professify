#!/usr/bin/env python3
"""GEs move under "Still need" (Tate, 2026-10-03: "this should be evident under still need it looks like i just
need bus classes").

Before: the Planner showed "Still need · 3" with only the coded classes (BUS 3411, BUS 3441, BUS 4468), and a
separate "GE areas and electives · 3" card below it, so the three GEs read as something else.
Now: one "Still need" card counts everything left (6), in two labelled groups: "Classes" (the coded rows, as
before) then "General education" (GE areas; "Electives" or "GE and electives" when the flowchart has those).
GE rows still open the area's class list. With only one group, the group label is left out.

Also (Tate, same day, on the half-filled circle: "what is this half moon mean"): the flowchart card gets a key
for its four marks — ✓ Done, ◐ In progress, an empty circle for To do, ? Can't check — drawn from the same CELL
table the rows use, so the key can't drift from the marks.

And (Tate, same day, on a friend's profile: "make sure to make schedule view on a persons profile is the same
size that we remade the feed schedules to. as in the width"): a friend's page now uses Home's widths — the
week card, the class list and the plans card sit 12px from the screen edge (were 16), and both the week and
the plan grid sit 8px inside the card with a 26px hour column and 5px day gaps (were 14 / 30 / 6). The plan
grid bleeds past the plans card's 16px text padding so it lines up with the week above it. Schedule keeps
its own 16 / 14 / 30 / 6.

Applies after share-edge-plan-2026-09-30.py (build 20:00).
Usage: python3 still-need-ge-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'tc-needh' in s: sys.exit('already patched')
R = [
 # 1. the group label inside the card
 ("const sectionCard = (title, body, right) =>",
  """/* "Still need" groups (2026-10-03): a small label over each kind of thing still left. */
const needHead = (label, n) => `<div class="tc-needh"><span>${label}</span><span>${n}</span></div>`;
const sectionCard = (title, body, right) =>"""),
 # 2. one card, two groups
 ("""  ${needRows ? sectionCard('Still need', needRows + (UI.pl.prereqs === false ? '<div class="muted b" style="font-size:12.5px;padding:8px 0">Prerequisites didn’t load, so readiness isn’t shown.</div>' : ''), `<span class="muted b" style="font-size:13px">${L.need.length}</span>`) : ''}
  ${geRows ? sectionCard('GE areas and electives', geRows, `<span class="muted b" style="font-size:13px">${L.needU.length}</span>`) : ''}""",
  """  ${needRows || geRows ? sectionCard('Still need', (needRows && geRows ? needHead('Classes', L.need.length) : '') + needRows + (needRows && UI.pl.prereqs === false ? '<div class="muted b" style="font-size:12.5px;padding:8px 0">Prerequisites didn’t load, so readiness isn’t shown.</div>' : '')
    + (needRows && geRows ? needHead(L.needU.every(n => n.type === 'ge') ? 'General education' : L.needU.some(n => n.type === 'ge') ? 'GE and electives' : 'Electives', L.needU.length) : '') + geRows,
    `<span class="muted b" style="font-size:13px">${L.need.length + L.needU.length}</span>`) : ''}"""),
 # 4. a key for the flowchart's marks, under its hint line
 ("tap a GE area to see this term’s classes for it.</div>${body}`);",
  "tap a GE area to see this term’s classes for it.</div><div class=\"tc-key\">${['done', 'taking', 'need', 'cant'].map(k => `<span><span class=\"tc-dot ${k}\" style=\"color:${CELL[k][1]};background:${CELL[k][2]}\" aria-hidden=\"true\">${CELL[k][0]}</span>${CELL[k][3]}</span>`).join('')}</div>${body}`);"),
 # 5. a friend's page at Home's widths
 ('<div class="card" style="margin:18px 16px 0;padding:14px 0 12px">',
  '<div class="card fweek" style="margin:18px 12px 0;padding:14px 0 12px">'),
 ('<div class="card list" style="margin:12px 16px 0">${codes.map',
  '<div class="card list" style="margin:12px 12px 0">${codes.map'),
 ('return `<div class="muted b" style="font-size:13px;padding:12px 20px 0">No shared plans.</div>`;',
  'return `<div class="muted b" style="font-size:13px;padding:12px 16px 0">No shared plans.</div>`;'),
 ("  return `<div class=\"card tc-sec\"><div class=\"tc-sech\"><span>${esc(PEOPLE[id].short)}’s plans",
  "  return `<div class=\"card tc-sec fplans\"><div class=\"tc-sech\"><span>${esc(PEOPLE[id].short)}’s plans"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
# 3. CSS, next to the other planner card styles
a = '.tc-sech{'
n = s.count(a)
if n != 1: sys.exit(f'css anchor matched {n}x')
s = s.replace(a, """.tc-needh{display:flex;justify-content:space-between;font-size:11px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:14px 0 2px}
.tc-sech + .tc-needh{padding-top:2px}
.tc-key{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 8px;font-size:11.5px;font-weight:800;color:var(--muted);margin:2px 0 8px}
.tc-key > span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.tc-key .tc-dot{width:18px;height:18px;font-size:10.5px}
.tc-key .tc-dot.need{box-shadow:inset 0 0 0 2px var(--line)}
/* a friend's page at Home's widths (2026-10-03) */
.fweek .grid,.fplans .plancol .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}
.tc-sec.fplans{margin-left:12px;margin-right:12px}
.fplans .plancol{margin-left:-16px;margin-right:-16px}
.tc-sech{""", 1)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
