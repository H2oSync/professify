#!/usr/bin/env python3
"""Tate (2026-10-13), on the Rate tab's list: "you see the small gaps we have in between classes do the same for ratings
professors." Each professor is now its own card with a 12px gap, like Explore's class cards, instead of rows divided by
hairlines inside one card. Replayable.
  python3 rate-cards-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'rate-cards: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
rep("""  <div class="card list" style="margin:0 12px">${t.items.map(([pid, code]) => {""",
    """  <div class="list rate-cards">${t.items.map(([pid, code]) => {""")
rep(""".list .li+.li{border-top:1px solid var(--line)}""",
    """.list .li+.li{border-top:1px solid var(--line)}
/* (2026-10-13) Rate: each professor its own card, 12px apart, like Explore's classes */
.rate-cards{display:flex;flex-direction:column;gap:12px;margin:0 12px}
.list.rate-cards .li{background:var(--card);border-radius:22px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 10px 30px rgba(22,51,107,.06);text-align:left}
.list.rate-cards .li+.li{border-top:0}""")
p.write_text(s); print('rate-cards: applied')
