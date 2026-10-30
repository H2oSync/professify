#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): since a64c48f (keep sideways scroll) render() reads e.hx after drawing the
screen, so an empty stack for the open tab (a test's S.stack[S.tab] = [], or any path that pops the last entry)
threw "Cannot read properties of undefined (reading 'hx')" and left the app half-drawn. A tab with nothing on its
stack now starts again at its own root, and the hx reads are guarded."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""  ['A', 'B', 'C'].forEach(k => document.body.classList.toggle('plan-' + k, S.plan === k));
  gaView(S.tab && cur() ? cur().s : 'app');""",
    """  if (!Array.isArray(S.stack[S.tab]) || !S.stack[S.tab].length) S.stack[S.tab] = [{ s: S.tab }];   /* an emptied stack starts again at the tab's root (2026-10-30) */
  ['A', 'B', 'C'].forEach(k => document.body.classList.toggle('plan-' + k, S.plan === k));
  gaView(S.tab && cur() ? cur().s : 'app');""")
one("""  hxRestore(sc, e.hx); UI._rendE = e;""", """  hxRestore(sc, e && e.hx); UI._rendE = e;""")
p.write_text(s); print('render-empty-stack applied')
