#!/usr/bin/env python3
"""Your profile page: the two count tiles are gone (Tate, 2026-10-04, "take this out").

The "6 classes · Fall 2026" and "15 friends · 15 free right now" cards under Edit profile / Settings
are removed, with the counts and CSS only they used. The settings list now sits right under the buttons.

Applies after prof-circle-no-ring-2026-10-04.py (build 15:45).
Usage: python3 me-no-stat-tiles-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'tc-mestats' not in s: sys.exit('already patched')
R = [
 ("  const P = TC.profile || {}, n = myCodes().size;\n", "  const P = TC.profile || {};\n"),
 ("""  /* "Free right now" counts only friends whose class times we have — a friend with none added is
     unknown, not free. status() is on San Luis Obispo time. */
  const timed = TC.friends.filter(f => status(f).free !== null), freeN = timed.filter(f => status(f).free === true).length;
  const freeLine = !TC.friends.length ? 'Add friends' : !timed.length ? 'No class times added yet' : `${freeN} free right now`;
""", ""),
 ("""
 <div class="tc-mestats"><button class="card tc-stat" data-a="tab" data-x="schedule"><span><b>${n}</b> ${n === 1 ? 'class' : 'classes'}</span><small>${esc(CFG.TERM_LABEL)}</small></button>
  <button class="card tc-stat" data-a="fFilterGo" data-x="people"><span><b>${TC.friends.length}</b> ${TC.friends.length === 1 ? 'friend' : 'friends'}</span><small>${esc(freeLine)}</small></button></div>""", ""),
 (""".tc-mestats{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 16px 0}
.tc-stat{display:flex;flex-direction:column;align-items:flex-start;gap:2px;padding:14px 16px;text-align:left;margin:0}
.tc-stat span{font-size:15px;font-weight:700;color:var(--ink2)}
.tc-stat b{font-size:22px;font-weight:900;color:var(--ink);font-variant-numeric:tabular-nums}
.tc-stat small{font-size:12.5px;font-weight:700;color:var(--muted)}
""", ""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
