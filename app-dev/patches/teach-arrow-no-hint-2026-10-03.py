#!/usr/bin/env python3
"""Teaching rows and the class page's hint line (Tate, 2026-10-03).

1. A professor's "Teaching Fall 2026" rows: the section count ("1 sec", "2 sec") is gone, and the arrow is the
   app's blue at a bolder 2.8 stroke and 20px ("do Bolder blue arrow", option 3 of the Teaching Row Taps mock).
   With the count gone, the full class title (not the 22-character short name) gets up to two lines.
2. A class page: the muted line under "Sections" ("Tap + to add a section to a plan · seats as of 21m ago") is
   removed ("we dont need this text here"). Seat counts still refresh as before; only the line is gone.

Applies after friend-week-switch-2026-10-03.py (build 06:45).
Usage: python3 teach-arrow-no-hint-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'teach-nm' in s: sys.exit('already patched')
R = [
 # 1. teaching rows: no count, two-line name, bold blue arrow
 ("""${profCourses(id).map(c => { const n = SECTIONS.filter(s => s.prof === id && s.code === c).length; return `<button class="teach" data-a="openClass" data-x="${c}"><span class="code">${c}</span><span class="grow b" style="font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(c).short)}</span><span class="muted b" style="font-size:13px">${n} sec</span><span class="chev">${ic('chevR', 18)}</span></button>`; }).join('')}""",
  """${profCourses(id).map(c => `<button class="teach" data-a="openClass" data-x="${c}"><span class="code">${c}</span><span class="grow b teach-nm">${esc(course(c).title)}</span><span class="teach-go">${ic('chevR', 20, 2.8)}</span></button>`).join('')}"""),
 # 2. class page: no hint line under "Sections"
 ("""\n <div class="muted b" style="font-size:13px;padding:0 18px 10px">Tap + to add a section to a plan${TC.seatsAt ? ` · seats as of ${agoText(new Date(TC.seatsAt).toISOString()) === 'now' ? 'just now' : agoText(new Date(TC.seatsAt).toISOString()) + ' ago'}` : ''}</div>""",
  ""),
 # CSS
 (".teach{display:flex;align-items:center;gap:10px;background:var(--bg);border-radius:16px;padding:10px 12px;width:100%;margin-top:8px}",
  """.teach{display:flex;align-items:center;gap:10px;background:var(--bg);border-radius:16px;padding:10px 12px;width:100%;margin-top:8px;min-height:52px;text-align:left}
.teach-nm{font-size:15px;min-width:0;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.teach-go{color:var(--blue);flex:none;display:inline-flex}"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
