#!/usr/bin/env python3
"""Tate, 2026-10-30, the app half: a slot we can't check reads "Not taken yet · I took this" under its
name (the circle does the same); once marked it reads "Marked done by you · Undo"."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""data-a="plMark" data-x="${esc(s.id)}" aria-pressed="${!!s.mine}" aria-label="Mark ${esc(code || name || s.title)} done\"""",
    """data-a="plMark" data-x="${esc(s.id)}" aria-pressed="${!!s.mine}" aria-label="I took ${esc(code || name || s.title)}\"""")
one("""  const line = s.mine ? '<span class="pc-pf tc-mine">Marked done by you</span>'""",
    """  const took = !s.mine && s.selfMark && s.state === 'need' ? `<span class="pc-pf">Not taken yet · <button class="pc-took" data-a="plMark" data-x="${esc(s.id)}">I took this</button></span>` : '';
  const line = took || s.mine ? took || `<span class="pc-pf tc-mine">Marked done by you · <button class="pc-took" data-a="plMark" data-x="${esc(s.id)}">Undo</button></span>`""")
one(""".pc-pf{font-size:13px;font-weight:800;color:var(--muted);margin:-4px 0 6px}""",
    """.pc-pf{font-size:13px;font-weight:800;color:var(--muted);margin:-4px 0 6px}
.pc-took{font:inherit;font-weight:900;color:var(--blue-t,var(--blue));background:none;border:0;padding:10px 4px;margin:-10px 0}""")
p.write_text(s); print('unknown-slots-took-link applied (index.html)')
