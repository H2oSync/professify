#!/usr/bin/env python3
"""Pull to refresh with a trackpad or mouse wheel (Tate, 2026-10-04: "i dont think it really worked").

17:00's pull only listened to touch and a mouse click-and-drag. In the Desktop phone preview on a Mac
the natural "swipe down" is a two-finger trackpad scroll — wheel events — so nothing happened. Now a
two-finger swipe down (or wheel up) at the top of Home pulls the same gap open; letting go past the
line refreshes, short of it closes. A wheel gesture only pulls if it STARTS with the page already at
the top, so the momentum of scrolling back up the feed never sets off a refresh.

Applies after anytime-blue-2026-10-04.py.
Usage: python3 pull-wheel-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const PW = ' in s: sys.exit('already patched')
a = "  sc.addEventListener('mousedown', e => { if (e.button === 0) ptrStart(e.clientY); });"
if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x')
s = s.replace(a, a + """
  /* a trackpad / wheel: a gesture is a run of wheel events less than 200ms apart. It decides on its
     first real vertical move: it pulls only if that move is down the top edge with the page already at
     the top, so the momentum of scrolling back up the feed never pulls. Pinch-zoom (ctrl), sideways
     swipes and shift-scroll are not pulls. A wheel counts 0.6 of its distance, so one notch of a mouse
     wheel (~100px) doesn't refresh on its own. A touch or a mouse drag takes over from it. */
  const PW = { last: 0, pending: false, on: false, own: false, dy: 0, t: null };
  const pwDrop = () => { if (!PW.own) return; PW.own = false; PW.on = false; clearTimeout(PW.t); };
  sc.addEventListener('touchstart', pwDrop, { passive: true, capture: true });
  sc.addEventListener('mousedown', pwDrop, { capture: true });
  sc.addEventListener('wheel', e => {
    const now = Date.now(), fresh = now - PW.last > 200; PW.last = now;
    if (fresh) { PW.pending = true; PW.on = false; PW.dy = 0; }
    if (e.ctrlKey || e.shiftKey) return;
    const d = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaMode === 2 ? e.deltaY * 400 : e.deltaY;
    const sideways = Math.abs(e.deltaX) >= Math.abs(e.deltaY);
    if (PW.pending) {
      if (!d || sideways) return;
      PW.pending = false;
      PW.on = !PTR.busy && ptrOn() && sc.scrollTop <= 0 && d < 0 && (PTR.y0 == null || PW.own);
      if (PW.on) { PTR.swallow = false; PTR.y0 = 0; PW.own = true; }
    }
    if (!PW.on || !PW.own || sideways) return;
    PW.dy = Math.max(0, PW.dy - d);
    ptrMove(PW.dy * 0.6);
    clearTimeout(PW.t); PW.t = setTimeout(() => { PW.on = false; if (PW.own) { PW.own = false; ptrEnd(false); } }, 200);
  }, { passive: true });""")
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
