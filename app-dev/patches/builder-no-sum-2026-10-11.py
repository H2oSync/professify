#!/usr/bin/env python3
"""Builder: no "6+ units · ★ 4.5 professors" line under "Recommended for Plan A" (Tate, 2026-10-11: "take this out").
Usage: python3 builder-no-sum-2026-10-11.py <repo-dir>   (replayable on build 19:05)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""  const sum = [planUnitsChip(st), st.avg != null ? `★ ${st.avg.toFixed(1)} professors` : '', st.friends ? `${st.friends} friend${st.friends === 1 ? '' : 's'} in your sections` : ''].filter(Boolean).join(' · ');
""", "", 'sum')
rep("""<div class="pl-rech">Recommended for Plan ${k}</div><div class="pl-recs">${esc(sum)}</div>""", """<div class="pl-rech">Recommended for Plan ${k}</div>""", 'line')
open(PA, 'w', encoding='utf-8').write(S); print('builder-no-sum: done')
