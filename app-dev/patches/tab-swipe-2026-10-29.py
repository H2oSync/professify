#!/usr/bin/env python3
"""Tate, 2026-10-29: "make it so you can also swipe between tool bars by just sliding across the
screen like instagram has it". On a tab's own screen, a sideways swipe moves to the next tab (left)
or the previous one (right), in the tab bar's order: Home · Explore · Rate · Schedule · Friends. On a
screen you opened from a tab (a class, a professor, a friend, a chat…), a swipe right goes back, as in
Instagram. The page follows the finger a little and the next tab slides in. It never starts inside
something that already scrolls or swipes sideways (stories, suggestions, chips, chat rows), in a text
field, or with a sheet or Champ open, and a mostly-vertical move stays a scroll. A mouse drag does the
same in the Desktop preview.
2026-10-29, second pass (Tate: "more seamless and not so slow with blurring … as similar to instagram
as possible"): no fade at all. The page moves 1:1 with the finger with the neighbouring screen drawn
right beside it, and lands in 140–280ms depending on the flick."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""document.addEventListener('click', ev => { if (UI.swdSwallow) { ev.stopPropagation(); ev.preventDefault(); UI.swdSwallow = false; } }, true);""",
"""document.addEventListener('click', ev => { if (UI.swdSwallow) { ev.stopPropagation(); ev.preventDefault(); UI.swdSwallow = false; } }, true);
/* Swipe between tabs (Tate, 2026-10-29: "like instagram"; then "more seamless and not so slow with
   blurring"). Instagram's feel: the page moves 1:1 with the finger and the next screen is right there
   beside it — a pager, no fade. The neighbour is drawn into a ghost layer next to #scroll; when the
   swipe lands, the real screen renders in its place on the same frame, so nothing jumps. */
const TSW = { on: false, dead: false, el: null, x0: 0, y0: 0, dx: 0, pts: null, to: null, dir: 0, ghost: null, w: 0 };
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
  if (TSW.ghost) return; TSW.el = null; if (tswBlocked(t)) return;
  Object.assign(TSW, { el: document.getElementById('scroll'), x0: x, y0: y, dx: 0, on: false, dead: false, pts: [[Date.now(), x]], to: null, dir: 0 });
}
function tswTarget(dir) {   /* dir 1 = swipe left (next tab), -1 = swipe right */
  const st = S.stack[S.tab] || [];
  if (st.length > 1) return dir < 0 ? 'back' : null;
  const order = TABS.map(t => t[0]), i = order.indexOf(S.tab), j = i + dir;
  return i < 0 || j < 0 || j >= order.length ? null : order[j];
}
function tswGhost(to, sc) {
  const entry = to === 'back' ? S.stack[S.tab][S.stack[S.tab].length - 2] : S.stack[to][S.stack[to].length - 1];
  let v = { body: '' }; try { v = SCREENS[entry.s](entry.p || {}) || v; } catch (e) { v = { body: '' }; }
  const g = document.createElement('div'); g.className = 'tswghost'; g.setAttribute('aria-hidden', 'true');
  const deep = to === 'home' && !v.dark && document.documentElement.getAttribute('data-theme') !== 'dark';
  g.style.cssText = `position:absolute;inset:0;overflow:hidden;pointer-events:none;will-change:transform;padding-top:${v.padTop ? `calc(var(--sb) + ${v.padTop}px)` : 'var(--sb)'};background:${v.dark ? '#0F172A' : deep ? '#E7ECF5' : 'var(--bg)'}`;
  g.innerHTML = v.body; sc.after(g);
  try { hxRestore(g, entry.hx); g.scrollTop = entry.y || 0; } catch (e) {}
  return g;
}
function tswPlace(dx) {
  const sc = TSW.el, g = TSW.ghost, w = TSW.w;
  const x = TSW.dir > 0 ? Math.min(0, Math.max(-w, dx)) : Math.max(0, Math.min(w, dx));   /* only toward the neighbour */
  sc.style.transform = `translate3d(${x}px,0,0)`;
  if (g) g.style.transform = `translate3d(${(TSW.dir > 0 ? w : -w) + x}px,0,0)`;
  return x;
}
function tswMove(x, y, ev) {
  const sc = TSW.el; if (!sc || TSW.dead) return;
  const dx = x - TSW.x0, dy = y - TSW.y0;
  if (!TSW.on) {
    if (Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)) { TSW.dead = true; return; }
    if (Math.abs(dx) < 12 || Math.abs(dx) < Math.abs(dy) * 1.6) return;
    const dir = dx < 0 ? 1 : -1, to = tswTarget(dir); if (!to) { TSW.dead = true; return; }
    TSW.on = true; TSW.dir = dir; TSW.to = to; TSW.w = sc.clientWidth || window.innerWidth;
    sc.style.transition = 'none'; sc.style.willChange = 'transform';
    if (!tswStill()) TSW.ghost = tswGhost(to, sc);
  }
  TSW.dx = x - TSW.x0; const now = Date.now(); TSW.pts.push([now, x]); while (TSW.pts.length > 2 && now - TSW.pts[0][0] > 100) TSW.pts.shift();
  if (!tswStill()) tswPlace(TSW.dx);
  if (ev && ev.cancelable) ev.preventDefault();
}
function tswClean(sc) { if (TSW.ghost) { TSW.ghost.remove(); TSW.ghost = null; } if (sc) { sc.style.transition = ''; sc.style.transform = ''; sc.style.willChange = ''; } }
function tswEnd() {
  const sc = TSW.el; TSW.el = null; if (!sc || !TSW.on) return; TSW.on = false;
  const p0 = TSW.pts[0], p1 = TSW.pts[TSW.pts.length - 1], v = (p1[1] - p0[1]) / Math.max(1, p1[0] - p0[0]), w = TSW.w, dir = TSW.dir, to = TSW.to;
  const toward = -dir * TSW.dx > 0, flick = Math.abs(v) > 0.35 && Math.sign(v) === -dir;
  const go = toward && (Math.abs(TSW.dx) > w * 0.33 || (flick && Math.abs(TSW.dx) > 24));
  UI.tswLast = { dx: TSW.dx, to: go ? to : null };
  const land = () => { if (to === 'back') A.back(); else A.tab(to); tswClean(document.getElementById('scroll')); };
  if (tswStill()) { tswClean(sc); if (go) land(); return; }
  const g = TSW.ghost, left = go ? w - Math.abs(TSW.dx) : Math.abs(TSW.dx);
  const ms = Math.round(Math.max(140, Math.min(280, left / Math.max(1.4, Math.abs(v)))));   /* faster flicks land faster */
  const ease = `transform ${ms}ms cubic-bezier(.22,.75,.25,1)`;
  sc.style.transition = ease; if (g) g.style.transition = ease;
  if (go) { sc.style.transform = `translate3d(${-dir * w}px,0,0)`; if (g) g.style.transform = 'translate3d(0,0,0)'; }
  else { sc.style.transform = 'translate3d(0,0,0)'; if (g) g.style.transform = `translate3d(${dir > 0 ? w : -w}px,0,0)`; }
  TSW.busy = true;
  setTimeout(() => { TSW.busy = false; if (go) land(); else tswClean(sc); }, ms + 10);
}
document.addEventListener('touchstart', ev => { if (TSW.busy) return; if (ev.touches.length !== 1) { TSW.el = null; return; } tswStart(ev.target, ev.touches[0].clientX, ev.touches[0].clientY); }, { passive: true });
document.addEventListener('touchmove', ev => { if (TSW.el && ev.touches.length === 1) tswMove(ev.touches[0].clientX, ev.touches[0].clientY, ev); }, { passive: false });
document.addEventListener('touchend', tswEnd, { passive: true });
document.addEventListener('touchcancel', () => { const sc = TSW.el; TSW.el = null; TSW.on = false; tswClean(sc); }, { passive: true });
document.addEventListener('mousedown', ev => { if (!TSW.busy && ev.button === 0 && !(window.matchMedia && matchMedia('(pointer:coarse)').matches)) tswStart(ev.target, ev.clientX, ev.clientY); });
document.addEventListener('mousemove', ev => { if (TSW.el) tswMove(ev.clientX, ev.clientY, null); });
document.addEventListener('mouseup', () => { const moved = TSW.on; tswEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });""")
p.write_text(s); print('tab-swipe applied')
