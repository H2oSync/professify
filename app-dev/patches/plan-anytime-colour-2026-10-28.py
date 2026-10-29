#!/usr/bin/env python3
"""Tate, 2026-10-28, on Tjudd's Home card (Plan A · Spring 2027, one async class): "why is the plan
and the class in asynch different colors we should keep them consistent". A friend's plan drew its
week in the plan's colour (A teal, B orange, C rose) but the Anytime tray sat outside the plan's
colour wrapper, so its chips stayed My Classes blue — and with only async classes there was no
wrapper at all. Now the tray is inside it, so its chips take the plan's colour too."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""  else if (!secs.some(onGrid)) week = anyRow;
  else week = (/^[ABC]$/.test(v.k) ? `<div class="plancol plan-${v.k}">` : '') + grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300, extra: /^[ABC]$/.test(v.k) ? [] : cmBlocks(isMe ? 'me' : id) }) + (/^[ABC]$/.test(v.k) ? '</div>' : '') + anyRow;""",
"""  else if (!secs.some(onGrid)) week = /^[ABC]$/.test(v.k) ? `<div class="plancol plan-${v.k}">${anyRow}</div>` : anyRow;
  else week = (/^[ABC]$/.test(v.k) ? `<div class="plancol plan-${v.k}">` : '') + grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300, extra: /^[ABC]$/.test(v.k) ? [] : cmBlocks(isMe ? 'me' : id) }) + anyRow + (/^[ABC]$/.test(v.k) ? '</div>' : '');""")
p.write_text(s); print('plan-anytime-colour applied')
