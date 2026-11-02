#!/usr/bin/env python3
"""2026-11-01: the header logo is the new wordmark (design/app-icon/2026-11-01, 709x144). Usage: <script> <repo root>"""
import sys, os
root = sys.argv[1]; p = os.path.join(root, 'app-dev/tests/check-app.mjs'); s = open(p).read()
def one(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a)); s = s.replace(a, b)
one("const dir = pth.resolve(pth.dirname(new URL(import.meta.url).pathname), '../patches/logo');\n  const want = { light: md5(fs.readFileSync(pth.join(dir, 'termchamp-logo-light.png'))), dark: md5(fs.readFileSync(pth.join(dir, 'termchamp-logo-dark.png'))) };",
    "const dir = pth.resolve(pth.dirname(new URL(import.meta.url).pathname), '../../design/app-icon/2026-11-01');   /* 2026-11-01: new brand */\n  const want = { light: md5(fs.readFileSync(pth.join(dir, 'termchamp-wm-light.png'))), dark: md5(fs.readFileSync(pth.join(dir, 'termchamp-wm-dark.png'))) };")
one("L.nat[0] === 672 && L.nat[1] === 144", "L.nat[0] === 709 && L.nat[1] === 144")
one("ok(L.h === 36 && Math.abs(L.w - 168) <= 1, 'logo: 36px tall, its own proportions (168px wide)', L);", "ok(L.h === 36 && Math.abs(L.w - 177) <= 1, 'logo: 36px tall, its own proportions (177px wide)', L);")
one("n.imgW === 168 &&", "Math.abs(n.imgW - 177) <= 1 &&")
one("'logo: dark mode shows the dark cut (Term in the dark theme’s navy so it reads on #0A0F1C)'", "'logo: dark mode shows the dark cut (the brighter blue that reads on #0A0F1C)'")
open(p, 'w').write(s); print('edit-tests-brand-i1: check-app wordmark updated')
