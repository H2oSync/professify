#!/usr/bin/env python3
"""Fixes from the Sonnet review of build 2026-10-05 01:15.

1. Signing out (or losing the session) while on Home left the deep #E7ECF5 page, band and phone strip behind
   the sign-in view: that branch of render() returns before the Home check. It now clears them, and sets the
   strip the way applyTheme does (dark on a dark boot / offline screen, light behind sign-in and onboarding;
   it was always light there, which flashed a light strip over dark mode's first screen).
   Deep reads the data-theme attribute, not isDark(), which is false while a share picture is being drawn.
   In dark mode the rate sheet's top gets a faint light edge (its fill is the page's).
2. A full-page sheet over Home (Add to…) has the light page; the band and strip now go light with it.
3. A second finger during a pull drops the pull (touches[0] could become the other finger, and its x/y were
   measured against the first one's start).
4. The firmer Home shadow under the suggestion cards was cut off flat by the sideways-scrolling row; the row
   now has room below the cards for it (and gives the room back with a negative margin, so spacing is the same).

Applies after fab-clear-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 review-fixes-0115-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if "return; } if (e.touches.length === 1) ptrStart(" in s: sys.exit('already patched')
R = [
 ("sc.innerHTML = signinView(); sc.style.paddingTop = ''; sc.style.background = ''; document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = '#F4F6FB'; });",
  "sc.innerHTML = signinView(); sc.style.paddingTop = ''; sc.style.background = ''; document.documentElement.classList.remove('deep'); document.querySelectorAll('meta[name=theme-color]').forEach(m => { m.content = isDark() && !sc.querySelector('.onb') ? '#0A0F1C' : '#F4F6FB'; });"),
 ("const deep = !v.dark && !isDark() && TC.phase === 'ok' && S.tab === 'home' && !!e && e.s === 'home';",
  "const deep = !v.dark && document.documentElement.getAttribute('data-theme') !== 'dark' && TC.phase === 'ok' && S.tab === 'home' && !!e && e.s === 'home' && !(UI.sheet && SHEETS[UI.sheet.type] && SHEETS[UI.sheet.type].full);"),
 ("sc.addEventListener('touchstart', e => { if (e.touches.length === 1) ptrStart(",
  "sc.addEventListener('touchstart', e => { if (e.touches.length > 1) { if (PTR.y0 != null) { PTR.y0 = null; PTR.dy = 0; ptrClose(); } return; } if (e.touches.length === 1) ptrStart("),
 ("sc.addEventListener('touchmove', e => { if (e.touches.length === 1) ptrMove(",
  "sc.addEventListener('touchmove', e => { if (e.touches.length > 1) { if (PTR.y0 != null) { PTR.y0 = null; PTR.dy = 0; ptrClose(); } return; } if (e.touches.length === 1) ptrMove("),
 (".rm-bd .rchip{margin-top:auto}\n",
  ".rm-bd .rchip{margin-top:auto}\n.homepg .recs-row{padding-bottom:20px;margin-bottom:-18px}\n:root[data-theme=\"dark\"] .rf-sheet{box-shadow:0 -1px 0 rgba(255,255,255,.07)}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
