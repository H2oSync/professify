#!/usr/bin/env python3
"""Tate (2026-10-13), on the Builder top card's big "2 left to graduate": "also take away this large 2 left its
repetitive". The heading goes; the bar opens the card, and the legend's amber entry carries the words:
"33 filled · 4 in progress · 2 left to graduate" (or "… 27 left on your flowchart"). Replayable on 06:30 + catalog chip.
  python3 builder-no-big-left-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-no-big-left: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep("""['l', nL, 'left']""", """['l', nL, R.audit ? 'left to graduate' : 'left on your flowchart']""")
rep("""  const top = `<div class="card pll"><div class="pll-hd"><div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div></div>${bar}""",
    """  const top = `<div class="card pll">${bar}""")
rep(""".pll-hd{display:flex;align-items:baseline;gap:10px;padding:0 2px}
.pll-hd .pll-h{flex:1;margin:0;padding:0;flex-wrap:wrap}
.pll-hd .pll-h span{font-size:17px}
""", """.pll > .pll-bar:first-child{margin-top:4px}
""")
# Tate, next: "have this Business Administration · Financial Management Quarter catalog above the progress line" and
# "take this out 55 requirements". Who you are (and the catalog chip) opens the card; then the bar and its legend.
rep("""${N ? `<span class="pll-n">${N} requirements</span>` : ''}</div>`;""", """</div>`;""")
rep("""  const top = `<div class="card pll">${bar}${meta}${clear}${pick}</div>`;""",
    """  const top = `<div class="card pll">${/<span/.test(meta) ? meta : ''}${bar}${clear}${pick}</div>`;""")
rep(""".pll > .pll-bar:first-child{margin-top:4px}
""", """.pll > .pll-bar:first-child{margin-top:4px}
.pll > .pll-info:first-child{margin-top:0}
""")
rep(""".pll-n{margin-left:auto}
""", "")
p.write_text(s); print('builder-no-big-left: applied')
