#!/usr/bin/env python3
"""Tate (2026-10-13): on a folded requirement's "best ★ 3.6 Birdsall": "dont need this"; and "put quarter catalog upper
right in the while area on the same line as spring 2027". The folded card is just its name (or "nothing offered this
term"); the Quarter / Semester catalog chip moves out of the top card to the right of the term heading. Replayable after
builder-option-tiles.
  python3 builder-catalog-top-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-catalog-top: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep("""    const sub = [n ? '' : 'nothing offered this term', !open && best ? (br != null ? `best ★ ${br.toFixed(1)}${prof(best) ? ' ' + esc(prof(best)) : ''}` : prof(best) ? 'best with ' + esc(prof(best)) : '') : ''].filter(Boolean).join(' · ');""",
    """    const sub = n ? '' : 'nothing offered this term';""")
rep("""    const best = q.cands[0], br = best ? ratingOf((secOf(best) || {}).prof) : null;
""", "")
rep("""${X && TC.audit.catalog ? (/quarter/i.test(TC.audit.catalog) ? '<span class="pc-catc q">Quarter catalog</span>' : '<span class="pc-catc s">Semester catalog</span>') : ''}${tot ?""",
    """${tot ?""")
rep("""  return `<div class="pl-top"><div>${term}</div></div>${plTermCard(w)}""",
    """  const catChip = R.audit && TC.audit && TC.audit.catalog ? (/quarter/i.test(TC.audit.catalog) ? '<span class="pc-catc q pl-cat">Quarter catalog</span>' : '<span class="pc-catc s pl-cat">Semester catalog</span>') : '';
  return `<div class="pl-top"><div>${term}</div>${catChip}</div>${plTermCard(w)}""")
rep(""".pl-top>div{flex:1;min-width:0}""", """.pl-top>div{flex:1;min-width:0}
.pl-top .pl-cat{align-self:center}""")
p.write_text(s); print('builder-catalog-top: applied')
