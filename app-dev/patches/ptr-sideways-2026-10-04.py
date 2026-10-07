#!/usr/bin/env python3
"""Swiping the stories row sideways never pulls to refresh (Tate, 2026-10-04: "when your swiping left on the
profile picture it natuarly tries and refresh because of the finger carrying downwards ... the only way to
scroll profiles without refeshing the homepage everytime is to go exactly horizontally").

The pull counted only the vertical part of a touch, so a sideways swipe that drifted down 70px refreshed.
Now a touch (or mouse drag) decides its direction once it has moved 10px:
  * it pulls only if it is going down, and more down than sideways;
  * starting inside a row that scrolls sideways (the stories, the class suggestions), it must be at least
    twice as much down as sideways, so a slanted swipe through the faces stays a swipe;
  * if that row scrolls at all during the touch, the pull is dropped.
Anything else drops the pull for the rest of that touch. A straight pull down still refreshes exactly as
before; the trackpad/wheel pull (which already ignored sideways swipes) is unchanged.

Applies after class-prof-width-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 ptr-sideways-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function ptrHs(' in s: sys.exit('already patched')
R = [
 ("const PTR = { y0: null, dy: 0, busy: false, swallow: false };",
  "const PTR = { y0: null, x0: null, dy: 0, lock: null, hs: null, hsx: 0, busy: false, swallow: false };"),
 ("function ptrStart(y) { const sc = document.getElementById('scroll'); PTR.swallow = false; PTR.y0 = (!PTR.busy && ptrOn() && sc && sc.scrollTop <= 0) ? y : null; PTR.dy = 0; }\n"
  "function ptrMove(y) {\n"
  "  if (PTR.y0 == null) return; PTR.dy = Math.max(0, y - PTR.y0);\n",
  "/* 2026-10-04: the row that scrolls sideways under a touch (stories, class suggestions), if any */\n"
  "function ptrHs(t) {\n"
  "  const sc = document.getElementById('scroll');\n"
  "  for (let el = t && t.nodeType === 1 ? t : t && t.parentElement; el && el !== sc && el !== document.body; el = el.parentElement) {\n"
  "    const ox = getComputedStyle(el).overflowX; if ((ox === 'auto' || ox === 'scroll') && el.scrollWidth > el.clientWidth + 1) return el;\n"
  "  }\n"
  "  return null;\n"
  "}\n"
  "function ptrStart(y, x, t) {\n"
  "  const sc = document.getElementById('scroll'); PTR.swallow = false; PTR.y0 = (!PTR.busy && ptrOn() && sc && sc.scrollTop <= 0) ? y : null; PTR.dy = 0;\n"
  "  PTR.x0 = x == null ? null : x; PTR.lock = null; PTR.hs = PTR.y0 == null || x == null ? null : ptrHs(t); PTR.hsx = PTR.hs ? PTR.hs.scrollLeft : 0;\n"
  "}\n"
  "/* a touch or mouse drag pulls only once it has gone 10px and that was clearly down (see the patch notes) */\n"
  "function ptrMove(y, x) {\n"
  "  if (PTR.y0 == null) return;\n"
  "  if (x != null && PTR.x0 != null) {\n"
  "    if (PTR.hs && PTR.hs.scrollLeft !== PTR.hsx) { PTR.y0 = null; PTR.dy = 0; ptrClose(); return; }\n"
  "    if (PTR.lock !== 'v') {\n"
  "      const dx = Math.abs(x - PTR.x0), dv = y - PTR.y0; if (dx < 10 && Math.abs(dv) < 10) return;\n"
  "      if (dv > 0 && dv >= dx * (PTR.hs ? 2 : 1)) PTR.lock = 'v'; else { PTR.y0 = null; PTR.dy = 0; ptrClose(); return; }\n"
  "    }\n"
  "  }\n"
  "  PTR.dy = Math.max(0, y - PTR.y0);\n"),
 ("sc.addEventListener('touchstart', e => { if (e.touches.length === 1) ptrStart(e.touches[0].clientY); }, { passive: true });\n"
  "  sc.addEventListener('touchmove', e => { if (e.touches.length === 1) ptrMove(e.touches[0].clientY); }, { passive: true });",
  "sc.addEventListener('touchstart', e => { if (e.touches.length === 1) ptrStart(e.touches[0].clientY, e.touches[0].clientX, e.target); }, { passive: true });\n"
  "  sc.addEventListener('touchmove', e => { if (e.touches.length === 1) ptrMove(e.touches[0].clientY, e.touches[0].clientX); }, { passive: true });"),
 ("sc.addEventListener('mousedown', e => { if (e.button === 0) ptrStart(e.clientY); });",
  "sc.addEventListener('mousedown', e => { if (e.button === 0) ptrStart(e.clientY, e.clientX, e.target); });"),
 ("document.addEventListener('mousemove', e => { if (PTR.y0 != null && (e.buttons & 1)) ptrMove(e.clientY); });",
  "document.addEventListener('mousemove', e => { if (PTR.y0 != null && (e.buttons & 1)) ptrMove(e.clientY, e.clientX); });"),
 ("if (PW.on) { PTR.swallow = false; PTR.y0 = 0; PW.own = true; }",
  "if (PW.on) { PTR.swallow = false; PTR.y0 = 0; PTR.x0 = null; PTR.hs = null; PW.own = true; }"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
