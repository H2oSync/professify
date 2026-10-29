#!/usr/bin/env python3
"""Tate, 2026-10-29 (bug in 1.0.1 build 3): "when you click something it wont let you click anything
else after". Cause: after a sheet was swiped down, SWD.on was never reset. On iPhone every tap also
fires a synthesized mouseup, and the mouseup handler saw SWD.on still true, so it swallowed the click
— every click, forever. Fix: swdEnd clears SWD.on (and TSW clears lock), and the mouse-drag helpers
only run on a real mouse (not on touch screens)."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""  const s = SWD.el; SWD.el = null; if (!s || !SWD.on) return;""",
    """  const s = SWD.el, was = SWD.on; SWD.el = null; SWD.on = false; if (!s || !was) return;""")
one("""document.addEventListener('mouseup', () => { const moved = SWD.on; swdEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });""",
    """const tcFine = () => !(window.matchMedia && matchMedia('(pointer:coarse)').matches);   /* a real mouse, not a finger */
document.addEventListener('mouseup', () => { if (!tcFine()) return; const moved = !!(SWD.el && SWD.on); swdEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });""")
one("""document.addEventListener('mouseup', () => { const moved = TSW.lock; tswEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });""",
    """document.addEventListener('mouseup', () => { if (!tcFine()) return; const moved = TSW.lock; tswEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });""")
one("""document.addEventListener('click', ev => { if (UI.swdSwallow) { ev.stopPropagation(); ev.preventDefault(); UI.swdSwallow = false; } }, true);""",
    """document.addEventListener('click', ev => { if (UI.swdSwallow && tcFine()) { ev.stopPropagation(); ev.preventDefault(); } UI.swdSwallow = false; }, true);""")
p.write_text(s); print('tap-after-swipe fix applied')
