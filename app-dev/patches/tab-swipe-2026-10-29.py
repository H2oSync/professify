#!/usr/bin/env python3
"""Tate, 2026-10-29: "make it so you can also swipe between tool bars by just sliding across the
screen like instagram has it". On a tab's own screen, a sideways swipe moves to the next tab (left)
or the previous one (right), in the tab bar's order: Home · Explore · Rate · Schedule · Friends. On a
screen you opened from a tab (a class, a professor, a friend, a chat…), a swipe right goes back, as in
Instagram. The page follows the finger a little and the next tab slides in. It never starts inside
something that already scrolls or swipes sideways (stories, suggestions, chips, chat rows), in a text
field, or with a sheet or Champ open, and a mostly-vertical move stays a scroll. A mouse drag does the
same in the Desktop preview."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""document.addEventListener('click', ev => { if (UI.swdSwallow) { ev.stopPropagation(); ev.preventDefault(); UI.swdSwallow = false; } }, true);""",
"""document.addEventListener('click', ev => { if (UI.swdSwallow) { ev.stopPropagation(); ev.preventDefault(); UI.swdSwallow = false; } }, true);
/* Swipe between tabs (Tate, 2026-10-29: "like instagram"). */
const TSW = { on: false, dead: false, el: null, x0: 0, y0: 0, dx: 0, pts: null };
const tswStill = () => !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
function tswBlocked(t) {
  if (!t || !t.closest || UI.sheet || UI.champ || TC.phase !== 'ok' || !t.closest('#scroll')) return true;
  if (t.closest('input,textarea,select,[contenteditable],.swrow,.ptrspin,#hptr')) return true;
  for (let n = t; n && n.id !== 'scroll'; n = n.parentElement) {   /* anything that scrolls sideways keeps its own swipe */
    if (n.scrollWidth > n.clientWidth + 2) { const o = getComputedStyle(n).overflowX; if (o === 'auto' || o === 'scroll') return true; }
  }
  return false;
}
function tswStart(t, x, y) {
  TSW.el = null; if (tswBlocked(t)) return;
  Object.assign(TSW, { el: document.getElementById('scroll'), x0: x, y0: y, dx: 0, on: false, dead: false, pts: [[Date.now(), x]] });
}
function tswTarget(dir) {   /* dir 1 = swipe left (next tab), -1 = swipe right */
  const st = S.stack[S.tab] || [];
  if (st.length > 1) return dir < 0 ? 'back' : null;
  const order = TABS.map(t => t[0]), i = order.indexOf(S.tab), j = i + dir;
  return i < 0 || j < 0 || j >= order.length ? null : order[j];
}
function tswMove(x, y, ev) {
  const sc = TSW.el; if (!sc || TSW.dead) return;
  const dx = x - TSW.x0, dy = y - TSW.y0;
  if (!TSW.on) {
    if (Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)) { TSW.dead = true; return; }
    if (Math.abs(dx) < 14 || Math.abs(dx) < Math.abs(dy) * 1.6) return;
    if (!tswTarget(dx < 0 ? 1 : -1)) { TSW.dead = true; return; }
    TSW.on = true; sc.style.transition = 'none';
  }
  TSW.dx = dx; const now = Date.now(); TSW.pts.push([now, x]); while (TSW.pts.length > 2 && now - TSW.pts[0][0] > 120) TSW.pts.shift();
  if (!tswStill()) { const d = Math.max(-70, Math.min(70, dx * 0.3)); sc.style.transform = `translateX(${d}px)`; sc.style.opacity = String(1 - Math.min(0.35, Math.abs(dx) / 900)); }
  if (ev && ev.cancelable) ev.preventDefault();
}
function tswEnd() {
  const sc = TSW.el; TSW.el = null; if (!sc || !TSW.on) return; TSW.on = false;
  const p0 = TSW.pts[0], p1 = TSW.pts[TSW.pts.length - 1], v = (p1[1] - p0[1]) / Math.max(1, p1[0] - p0[0]);
  const dir = TSW.dx < 0 ? 1 : -1, go = Math.abs(TSW.dx) > 80 || (Math.abs(TSW.dx) > 36 && Math.abs(v) > 0.45 && Math.sign(v) === Math.sign(TSW.dx));
  const to = go ? tswTarget(dir) : null;
  UI.tswLast = { dx: TSW.dx, to };
  const reset = () => { sc.style.transition = ''; sc.style.transform = ''; sc.style.opacity = ''; };
  if (!to) { if (tswStill()) return reset(); sc.style.transition = 'transform .2s cubic-bezier(.2,.8,.2,1), opacity .2s'; sc.style.transform = ''; sc.style.opacity = ''; setTimeout(() => { sc.style.transition = ''; }, 220); return; }
  if (to === 'back') A.back(); else A.tab(to);
  if (tswStill()) return reset();
  const s2 = document.getElementById('scroll'); s2.style.transition = 'none'; s2.style.transform = `translateX(${dir * 44}px)`; s2.style.opacity = '0.4';
  requestAnimationFrame(() => requestAnimationFrame(() => { s2.style.transition = 'transform .22s cubic-bezier(.2,.8,.2,1), opacity .22s'; s2.style.transform = ''; s2.style.opacity = ''; setTimeout(() => { s2.style.transition = ''; }, 240); }));
}
document.addEventListener('touchstart', ev => { if (ev.touches.length !== 1) { TSW.el = null; return; } tswStart(ev.target, ev.touches[0].clientX, ev.touches[0].clientY); }, { passive: true });
document.addEventListener('touchmove', ev => { if (TSW.el && ev.touches.length === 1) tswMove(ev.touches[0].clientX, ev.touches[0].clientY, ev); }, { passive: false });
document.addEventListener('touchend', tswEnd, { passive: true });
document.addEventListener('touchcancel', () => { const sc = TSW.el; TSW.el = null; TSW.on = false; if (sc) { sc.style.transform = ''; sc.style.opacity = ''; sc.style.transition = ''; } }, { passive: true });
document.addEventListener('mousedown', ev => { if (ev.button === 0 && !(window.matchMedia && matchMedia('(pointer:coarse)').matches)) tswStart(ev.target, ev.clientX, ev.clientY); });
document.addEventListener('mousemove', ev => { if (TSW.el) tswMove(ev.clientX, ev.clientY, null); });
document.addEventListener('mouseup', () => { const moved = TSW.on; tswEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });""")
p.write_text(s); print('tab-swipe applied')
