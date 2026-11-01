#!/usr/bin/env python3
"""2026-11-01: the redrawn header wordmark is 700x144 (175px wide at 36px). Usage: <script> <repo root>"""
import sys, os
p = os.path.join(sys.argv[1], 'app-dev/tests/check-app.mjs'); s = open(p).read()
for a, b in [("L.nat[0] === 709 && L.nat[1] === 144", "L.nat[0] === 700 && L.nat[1] === 144"),
             ("ok(L.h === 36 && Math.abs(L.w - 177) <= 1, 'logo: 36px tall, its own proportions (177px wide)', L);", "ok(L.h === 36 && Math.abs(L.w - 175) <= 1, 'logo: 36px tall, its own proportions (175px wide)', L);"),
             ("Math.abs(n.imgW - 177) <= 1 &&", "Math.abs(n.imgW - 175) <= 1 &&")]:
    if s.count(b) == 1: continue
    assert s.count(a) == 1, (a[:60], s.count(a)); s = s.replace(a, b)
open(p, 'w').write(s); print('edit-tests-brand-nohat: done')
