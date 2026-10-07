#!/usr/bin/env python3
"""The strip above the app on an iPhone is the app's own colour (Tate, 2026-10-04: "this color is still having a
problem its not blending in ... theres also now two diferent colors").

On a phone, Safari paints the strip behind the clock and battery from the page's own background — newer iOS
reads the body's colour rather than the theme-color tag. The body was the Desktop preview's dotted desk
(#E9EEF8), so the strip came out a shade darker than the app (#F4F6FB) under it, and the app's top band
then showed as a second colour once you scrolled. On a phone (520px and narrower, where the app is full
bleed) html and body are now plain #F4F6FB (--bg), the same as the app's top band, so the strip, the band and
the page are one colour. In dark mode that is the dark page; sign-up and onboarding, which stay light in dark
mode, keep a light strip too. The Desktop preview keeps its dotted desk.

Applies after rate-no-dark-2026-10-04.py (build 2026-10-05 01:15).
Usage: python3 phone-top-blend-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'html,body{background:var(--bg)}' in s: sys.exit('already patched')
a = "  .phone{width:100vw;height:100dvh;border-radius:0;transform:none;box-shadow:none}\n"
if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x')
s = s.replace(a, a + "  html,body{background:var(--bg)}\n  html:has(.onb),html:has(.onb) body{background:#F4F6FB}\n")
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
