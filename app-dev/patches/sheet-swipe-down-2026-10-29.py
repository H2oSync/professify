#!/usr/bin/env python3
"""Tate, 2026-10-29: "when you click on someones story and it shows their day make it so you can just
swipe down instead of having to click the x upper right". Every bottom sheet (the story day, the
section preview, Add a friend…) now follows the finger down and closes past ~110px or on a quick
flick; anything less springs back. It only starts when the sheet's content is at its top (so a long
day still scrolls), never on a sideways or upward move, and never on full-screen pages. It closes
through A.closeSheet, so a sheet that refuses to close springs back. In the Desktop preview a mouse
drag does the same."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one("""document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });""",
"""document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });
/* Swipe a sheet down to close it (Tate, 2026-10-29: "swipe down instead of having to click the x"). */
const SWD = { el: null, y0: 0, x0: 0, dy: 0, t0: 0, on: false, dead: false };
function swdSheet(t) { const s = t && t.closest ? t.closest('#sheet .sheet') : null; return s && !s.classList.contains('champ') ? s : null; }
function swdStart(t, x, y) {
  SWD.el = null; const s = swdSheet(t); if (!s) return;
  for (let n = t; n && n !== s; n = n.parentElement) { if (n.scrollTop > 0) return; }   /* a scrolled list scrolls; it doesn't close */
  Object.assign(SWD, { el: s, y0: y, x0: x, dy: 0, t0: Date.now(), on: false, dead: false, pts: [[Date.now(), y]] });
}
function swdMove(x, y, ev) {
  const s = SWD.el; if (!s || SWD.dead) return;
  const dy = y - SWD.y0, dx = x - SWD.x0;
  if (!SWD.on) {
    if (Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) { SWD.dead = true; return; }
    if (dy < -6) { SWD.dead = true; return; }
    if (dy < 8) return;
    SWD.on = true; s.style.animation = 'none'; s.style.transition = 'none';
  }
  SWD.dy = Math.max(0, dy - 8); s.style.transform = `translateY(${SWD.dy}px)`;
  const now = Date.now(); SWD.pts.push([now, y]); while (SWD.pts.length > 2 && now - SWD.pts[0][0] > 120) SWD.pts.shift();
  const sc = document.querySelector('#sheet .scrim'); if (sc) { sc.style.transition = 'none'; sc.style.opacity = String(Math.max(0.15, 1 - SWD.dy / 420)); }
  if (ev && ev.cancelable) ev.preventDefault();
}
function swdEnd() {
  const s = SWD.el; SWD.el = null; if (!s || !SWD.on) return;
  /* speed over the last ~120ms, so a quick flick counts even after a slow start */
  const p0 = SWD.pts[0], p1 = SWD.pts[SWD.pts.length - 1], v = (p1[1] - p0[1]) / Math.max(1, p1[0] - p0[0]);
  const go = SWD.dy > 110 || (SWD.dy > 36 && v > 0.5), sc = document.querySelector('#sheet .scrim');
  UI.swdLast = { dy: SWD.dy, closed: go };
  if (!go) { s.style.transition = 'transform .22s cubic-bezier(.2,.8,.2,1)'; s.style.transform = ''; if (sc) { sc.style.transition = 'opacity .22s'; sc.style.opacity = ''; } return; }
  s.style.transition = 'transform .18s ease-in'; s.style.transform = `translateY(${Math.round(s.getBoundingClientRect().height) + 40}px)`;
  if (sc) { sc.style.transition = 'opacity .18s'; sc.style.opacity = '0'; }
  setTimeout(() => {
    A.closeSheet();
    const still = document.querySelector('#sheet .sheet'), sc2 = document.querySelector('#sheet .scrim');   /* refused (e.g. prefs not saved): spring back */
    if (still) { still.style.transition = 'transform .22s cubic-bezier(.2,.8,.2,1)'; still.style.transform = ''; } if (sc2) sc2.style.opacity = '';
  }, 170);
}
document.addEventListener('touchstart', ev => { if (ev.touches.length !== 1) { SWD.el = null; return; } swdStart(ev.target, ev.touches[0].clientX, ev.touches[0].clientY); }, { passive: true });
document.addEventListener('touchmove', ev => { if (SWD.el && ev.touches.length === 1) swdMove(ev.touches[0].clientX, ev.touches[0].clientY, ev); }, { passive: false });
document.addEventListener('touchend', swdEnd, { passive: true });
document.addEventListener('touchcancel', swdEnd, { passive: true });
/* the Desktop preview has no touch: a mouse drag does the same, and a drag that closed swallows its click */
document.addEventListener('mousedown', ev => { if (ev.button === 0 && !(window.matchMedia && matchMedia('(pointer:coarse)').matches)) swdStart(ev.target, ev.clientX, ev.clientY); });
document.addEventListener('mousemove', ev => { if (SWD.el) swdMove(ev.clientX, ev.clientY, null); });
document.addEventListener('mouseup', () => { const moved = SWD.on; swdEnd(); if (moved) { UI.swdSwallow = true; setTimeout(() => { UI.swdSwallow = false; }, 60); } });
document.addEventListener('click', ev => { if (UI.swdSwallow) { ev.stopPropagation(); ev.preventDefault(); UI.swdSwallow = false; } }, true);""")
p.write_text(s); print('sheet-swipe-down applied')
