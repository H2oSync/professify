#!/usr/bin/env python3
"""Rate form: Favorite teacher sits right above the Review box (Tate, 2026-10-04: "put the favorite teacher next to
review when you type put it right above it").

The Favorite teacher row moves from under "Take again?" into "+ Add detail", between Format and Review, so it is
the row right above where you type. An edit whose review is already a favorite opens "Add detail" so the picked
heart is in view (also once favorites finish loading, unless the student already opened or hid detail). With
detail hidden and a favorite picked, the "+ Add detail" row shows "♥ Favorite" where "Optional" was, so the heart
is never picked out of sight.

Applies after prof-page-one-green-2026-10-04.py.
Usage: python3 fav-above-review-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if '${favRow(d)}\n   <div class="frow2"><div class="row sb"><span class="flabel">Review</span>' in s: sys.exit('already patched')
R = [
 ("""   ${favRow(d)}
   <div class="frow2 row sb"><button class="b" style="color:var(--blue);font-size:17px;font-weight:900" data-a="draftMore">""",
  """   <div class="frow2 row sb"><button class="b" style="color:var(--blue);font-size:17px;font-weight:900" data-a="draftMore">"""),
 ("""   <div class="frow2"><div class="row sb"><span class="flabel">Review</span>""",
  """   ${favRow(d)}
   <div class="frow2"><div class="row sb"><span class="flabel">Review</span>"""),
 ("""const d = S.draft; if (d && d.editing && !d.favTouched) d.fav = d.fav0 = TC.myFavs.has(d.favKey); }""",
  """const d = S.draft; if (d && d.editing && !d.favTouched) { d.fav = d.fav0 = TC.myFavs.has(d.favKey); if (d.fav && !d.moreTouched) d.more = true; } }"""),
 # Hide detail with a favorite picked: the row says so where "Optional" was, so a picked heart is never invisible
 ("""data-a="draftMore">${d.more ? '− Hide detail' : '+ Add detail'}</button><span class="hint" style="font-size:14px">Optional</span></div>""",
  """data-a="draftMore">${d.more ? '− Hide detail' : '+ Add detail'}</button>${!d.more && d.fav && TC.favOn ? `<span class="favhid">${heartI(15)}Favorite</span>` : '<span class="hint" style="font-size:14px">Optional</span>'}</div>"""),
 ("""  draftMore: () => { S.draft.more = !S.draft.more; render(true); },""",
  """  draftMore: () => { S.draft.more = !S.draft.more; S.draft.moreTouched = true; render(true); },"""),
 (".favbtn{", ".favhid{display:inline-flex;align-items:center;gap:5px;font-size:14px;font-weight:900;color:#E11D48}\n.favbtn{"),
 ("""      more: !!(v.format || v.note), grade: v.grade || null,""",
  """      more: !!(v.format || v.note || (TC.myFavs && TC.myFavs.has(v.professor_key))), grade: v.grade || null,"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
