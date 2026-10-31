#!/usr/bin/env python3
"""Glue, 2026-10-30: the contacts pop-up (contacts-2026-10-30) and the notifications pop-ups (pushask-popup-2026-10-30)
were built side by side. On a later app open "Connect contacts" now goes through TC.popQueue too, first in line, so a
student never gets both on the same open (notifications comes the next open). Run after both."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
assert 'TC.popQueue = async function' in s and 'function ctLater()' in s
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""  if ((+st.n || 0) < 2 || st.on || Date.now() < (+st.snooze || 0) || !ctAvail()) return;
  setTimeout(() => { const e = cur(); if (S.tab === 'home' && e && e.s === 'home' && !S.stack.home.some(x => x.s === 'onb') && !UI.sheetNext) ctAsk('later'); }, 2500);
}""", """}
/* on a later open it takes its turn in the pop-up queue, ahead of notifications (one pop-up per open) */
POPS.unshift({ kind: 'contacts',
  due: at => { if (at !== 'open' || !TC.user || TC.phase !== 'ok' || UI.sheetNext) return null; const st = ctState(), e = cur();
    return (+st.n || 0) >= 2 && !st.on && Date.now() >= (+st.snooze || 0) && ctAvail() && S.tab === 'home' && e && e.s === 'home' ? 'later' : null; },
  show: why => ctAsk(why) });""")
p.write_text(s); print(p, 'contacts-into-popqueue: ok')
