#!/usr/bin/env python3
"""Tate (2026-10-13), on the Builder's options under an open requirement: "same for this because its hard to
differentiate things" (after giving Rate's professors gaps like Explore's classes). Each option is its own tile on the
page colour, 8px apart, instead of rows split by hairlines; the See more / Mark done foot loses its hairline too.
Replayable after builder-term-card.
  python3 builder-option-tiles-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-option-tiles: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep(""".plo{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;padding:11px 0;border-top:1px solid var(--line);text-align:left}
.plo:first-of-type{border-top:0}""",
    """.plo{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;padding:11px 14px;border:0;border-radius:16px;background:var(--bg);text-align:left}
.plo + .plo{margin-top:8px}""")
rep(""".plq-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:2px 0 0;border-top:1px solid var(--line);margin-top:4px}""",
    """.plq-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:2px 0 0;margin-top:6px}""")
rep(""".plq-lab{font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:2px 0 4px}""",
    """.plq-lab{font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:2px 0 8px}""")
p.write_text(s); print('builder-option-tiles: applied')
