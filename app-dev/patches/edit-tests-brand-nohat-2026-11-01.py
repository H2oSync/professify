#!/usr/bin/env python3
"""2026-11-01: header wordmark = icon T/C + Rubik lowercase, no cap: 809x144 shown 32px tall (180px wide), welcome 42px,
website 28-32px. Applies after edit-tests-brand-i1. Usage: <script> <repo root>"""
import sys, os
root = sys.argv[1]
def edit(rel, pairs):
    p = os.path.join(root, rel); s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70], s.count(a)); s = s.replace(a, b)
    open(p, 'w').write(s)
edit('app-dev/tests/check-app.mjs', [
  ("L.nat[0] === 709 && L.nat[1] === 144", "L.nat[0] === 809 && L.nat[1] === 144"),
  ("ok(L.h === 36 && Math.abs(L.w - 177) <= 1, 'logo: 36px tall, its own proportions (177px wide)', L);", "ok(L.h === 32 && Math.abs(L.w - 180) <= 1, 'logo: 32px tall (no cap), its own proportions (180px wide)', L);"),
  ("Math.abs(n.imgW - 177) <= 1 &&", "Math.abs(n.imgW - 180) <= 1 &&"),
  ("srcHash(D.src) === want.dark && D.h === 36", "srcHash(D.src) === want.dark && D.h === 32"),
  ("w.h === 48", "w.h === 42"),
  ("'logo: the welcome screen shows the same logo, 48px tall'", "'logo: the welcome screen shows the same logo, 42px tall'")])
edit('app-dev/tests/check-desktop-identity.mjs', [
  ("ok(r.lb.h >= 32 && r.lb.h <= 36.5 && r.lb.w > 80, 'the logo is 32-36px tall, with its own width (not squeezed)', r.lb);",
   "ok(r.lb.h >= 28 && r.lb.h <= 32.5 && r.lb.w > 80, 'the logo is 28-32px tall (no cap), with its own width (not squeezed)', r.lb);"),
  ("y.b.h >= 30, `390 ${th}: one logo image fits left of the account pill`", "y.b.h >= 27, `390 ${th}: one logo image fits left of the account pill`")])
print('edit-tests-brand-nohat: done')
