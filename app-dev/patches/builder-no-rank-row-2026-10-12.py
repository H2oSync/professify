#!/usr/bin/env python3
"""The Builder no longer shows the 1 · 2 · 3 ranking chips under the term (Tate, 2026-10-12, on a screenshot of
"1 Professors  2 Degree  3 Friends": "take this out keep it in the edit where you pick units"). The order lives only in
the What-matters-most sheet that "N units · Edit" opens. Replayable on 18:05.
  python3 builder-no-rank-row-2026-10-12.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
R = [
(""".pl-rank{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:8px 16px 0;padding:0;text-align:left;min-height:32px}
.pl-rank span{display:inline-flex;align-items:center;gap:5px;height:28px;padding:0 10px 0 4px;border-radius:999px;background:var(--tint1);font-size:12.5px;font-weight:900;color:var(--ink)}
.pl-rank b{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;background:var(--blue);color:#fff;font-size:11.5px;font-weight:900}
""", ""),
("""  /* what matters most, in your order */
  const rankRow = `<button class="pl-rank" data-a="plPrefsOpen" aria-label="What matters most: ${esc(prefOrder().map((x, i) => (i + 1) + ' ' + PREF_LABEL[x]).join(', '))} · Edit">${prefOrder().map((x, i) => `<span><b>${i + 1}</b>${esc(PREF_SHORT[x])}</span>`).join('')}</button>`;
""", """  /* what matters most: its 1 · 2 · 3 lives only in the sheet "N units · Edit" opens (Tate, 2026-10-12: "take this out keep
     it in the edit where you pick units") */
"""),
("""${plUnitsTarget()} units · Edit</button></div>${rankRow}${plRegBanner()}""", """${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}"""),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'builder-no-rank-row: expected 1 of {a[:70]!r}, found {s.count(a)}')
    s = s.replace(a, b)
p.write_text(s)
print('builder-no-rank-row: applied')
