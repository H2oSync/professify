#!/usr/bin/env python3
"""Tate, 2026-10-29 (1.0.1 build 3): "its not easy to swipe when your on the last page". On Friends almost
the whole screen is chat rows, and chat rows were left out of tab swipes (they swipe left for
Pin/Delete), so there was almost nowhere to swipe right from. Now a swipe RIGHT on a closed chat row
goes back to Schedule like anywhere else; a swipe LEFT on a row still opens Pin/Delete, and a right
swipe on an open row still just closes it."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""  if (t.closest('input,textarea,select,[contenteditable],.swrow,.ptrspin,#hptr')) return true;""",
    """  if (t.closest('input,textarea,select,[contenteditable],.swacts,.ptrspin,#hptr')) return true;""")
one("""  Object.assign(TSW, { el: document.getElementById('scroll'), x0: x, y0: y, dead: false, lock: false });""",
    """  /* a chat row: only a right swipe on a closed row is a tab swipe (left = Pin/Delete; right on an open row closes it) */
  const row = t.closest('.swrow'), th = row && row.querySelector(':scope > .thread');
  const rowOpen = !!(row && ((th && /translateX\\(-[1-9]/.test(th.style.transform || '')) || (typeof SW !== 'undefined' && SW.open)));
  Object.assign(TSW, { el: document.getElementById('scroll'), x0: x, y0: y, dead: false, lock: false, row: !!row, rowOpen });""")
one("""  const dir = dx < 0 ? 1 : -1, to = tswTarget(dir); if (!to) { TSW.dead = true; return; }""",
    """  const dir = dx < 0 ? 1 : -1; if (TSW.row && (dir > 0 || TSW.rowOpen)) { TSW.dead = true; return; }
  const to = tswTarget(dir); if (!to) { TSW.dead = true; return; }""")
p.write_text(s); print('tab-swipe-on-chats applied')
