#!/usr/bin/env python3
"""Tate (2026-10-13), on a requirement card's line "pick one of 6 · 4 offered this spring" / "4 units · 3 offered this
spring": "take these out". The line now only appears for what the card can't show by itself: "best ★ 3.6 Birdsall" while
it's folded, and "nothing offered this term" when nothing is. Replayable on 06:30 + catalog chip + no big left.
  python3 builder-req-sub-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-req-sub: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep("""    const sub = [need(q), n ? `${n} offered this ${esc(String(CFG.TERM_LABEL).split(' ')[0].toLowerCase())}` : 'nothing offered this term', !open && best""",
    """    const sub = [n ? '' : 'nothing offered this term', !open && best""")
rep("""<span class="plq-t"><b>${esc(q.label)}${tag}</b><span>${sub}</span></span>""",
    """<span class="plq-t"><b>${esc(q.label)}${tag}</b>${sub ? `<span>${sub}</span>` : ''}</span>""")
# need() only fed that line
import re
i = s.index("  const need = q => q.b ? ["); j = s.index("\n", i) + 1
s = s[:i] + s[j:]
p.write_text(s); print('builder-req-sub: applied')
