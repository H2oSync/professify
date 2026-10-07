#!/usr/bin/env python3
"""Explore professor cards: the ratings count sits under the star chip (Tate, 2026-10-04).

From the "Professor Card Ratings" mockup, option D ("try one where you just put the ratings under the stars" → "D"):
today's card with one change. "14 ratings" moves from its own line to right under the ★ chip, centred on it
(13px, muted, one line). The middle line keeps only "N% would take again" when there is one; with nothing left
it is the old 10px spacer, so the card is one line shorter. A professor with no rating chip keeps "N ratings" /
"No ratings yet" on the middle line as before.

Applies after rating-gradient-2026-10-03.py (build 13:40).
Usage: python3 prof-card-count-under-star-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="prt"' in s: sys.exit('already patched')
R = [
 ("""  const line = [p.count ? nRatings(p.count) : (r == null && !st ? 'No ratings yet' : ''), st && st.again != null ? `${st.again}% would take again` : ''].filter(Boolean).join(' · ');
  return `<button class="card pcard" data-a="openProf" data-x="${esc(pk)}">
  <div class="row">${profAv(pk, 44, 15)}""",
  """  const line = [r != null ? '' : p.count ? nRatings(p.count) : (!st ? 'No ratings yet' : ''), st && st.again != null ? `${st.again}% would take again` : ''].filter(Boolean).join(' · ');
  return `<button class="card pcard" data-a="openProf" data-x="${esc(pk)}">
  <div class="row"${r != null ? ' style="align-items:flex-start"' : ''}>${profAv(pk, 44, 15)}"""),
 ("""${r != null ? `<span class="rchip rt-${rateTone(r).k}" style="background:${rateTone(r).bg};color:${rateTone(r).ink}">${starI(13, rateTone(r).star)} ${r.toFixed(1)}</span>` : ''}</div>
  ${line ? `<div class="muted b" style="font-size:13.5px;margin:10px 0">${line}</div>` : '<div style="height:10px"></div>'}""",
  """${r != null ? `<span class="prt"><span class="rchip rt-${rateTone(r).k}" style="background:${rateTone(r).bg};color:${rateTone(r).ink}">${starI(13, rateTone(r).star)} ${r.toFixed(1)}</span>${p.count ? `<span class="prt-n">${nRatings(p.count)}</span>` : ''}</span>` : ''}</div>
  ${line ? `<div class="muted b" style="font-size:13.5px;margin:10px 0">${line}</div>` : '<div style="height:10px"></div>'}"""),
 (".rchip{display:inline-flex;",
  """.prt{display:flex;flex-direction:column;align-items:center;gap:4px;flex:none}
.prt-n{font-size:13px;font-weight:800;color:var(--muted);white-space:nowrap}
.rchip{display:inline-flex;"""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
