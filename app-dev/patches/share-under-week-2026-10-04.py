#!/usr/bin/env python3
"""Schedule: the Share bar goes under the week (Tate, 2026-10-04).

"lets put the share schedule and friends see this under the schedules this goes for plans and my
classes i think it will look less cluttered". On My Classes (Share; 15:50 moved "Fall 2026" into the term chips) and on a plan
("Friends can see" / "Only you" · Share) the bar moves from above the week card to right under it.
The plan's own notes (couldn't load, sections no longer listed) stay above the week.

Applies after friends-major-pins-shuffle-2026-10-04.py (on 15:50's my-classes-terms).
Usage: python3 share-under-week-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'regbar under' in s: sys.exit('already patched')
PLAN_BAR = """<div class="regbar"><span class="regbadge" style="background:var(--bg);color:var(--muted)">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span><button class="shbtn" data-a="shareOpen" data-x="${S.plan}" aria-label="Share Plan ${S.plan}" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>"""
MINE_BAR = """<div class="regbar" style="justify-content:flex-end"><button class="shbtn" data-a="shareOpen" data-x="mine" aria-label="Share your week" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>"""
under = lambda b: b.replace('<div class="regbar" style="justify-content:flex-end">', '<div class="regbar under" style="justify-content:flex-end">').replace('<div class="regbar">', '<div class="regbar under">')
R = [
 ("\n  " + PLAN_BAR + "\n  ${TC.err.plans ?", "\n  ${TC.err.plans ?"),
 ("""'<div class="empty"><b>No timed classes</b>Add classes from Explore.</div>'}</div>\n""",
  """'<div class="empty"><b>No timed classes</b>Add classes from Explore.</div>'}</div>\n  """ + under(PLAN_BAR) + "\n"),
 ("    else inner = chips + `" + MINE_BAR + "\n  ${TC.err.mine ?", "    else inner = chips + `\n  ${TC.err.mine ?"),
 ("""grid(secs, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330, faces: true })}</div>` : ''}\n""",
  """grid(secs, { sel: S.schedDay, act: 'schedDay', blockAct: 'secSheet', H: 330, faces: true })}</div>` : ''}\n  """ + under(MINE_BAR) + "\n"),
 (".regbar .rgt{display:flex;align-items:center;gap:8px}",
  ".regbar .rgt{display:flex;align-items:center;gap:8px}\n.regbar.under{margin-top:10px}"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
