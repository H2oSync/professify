#!/usr/bin/env python3
"""No line under the strip at the top of the phone (Tate, 2026-10-06: "lets eleminate the line from the
iphones top thing make it seemless and blend").

Since 2026-09-30 20:00 a 1px hairline appeared under the status strip once you scrolled (light: rgba
(15,23,42,.1); dark since 00:30: rgba(255,255,255,.08)). It is gone in both themes: the strip is the page's
own colour, solid, so content slides under it with no seam. statusHair() no longer marks the strip, and
both .status.scrolled rules are removed.

Usage: python3 top-seamless-2026-10-06.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if '/* no hairline under the top strip' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

one(".status.scrolled{box-shadow:0 1px 0 rgba(15,23,42,.1)}\n", "")
one(':root[data-theme="dark"] .status.scrolled:not(.dark){box-shadow:0 1px 0 rgba(255,255,255,.08)}\n', "")
one("/* The hairline under the top strip: only once the page has scrolled, and not over a screen's own header. */\n", "")
one("function statusHair() { const sc = document.getElementById('scroll'), st = document.getElementById('status'), ft = document.getElementById('fixtop'); if (sc && st) st.classList.toggle('scrolled', sc.scrollTop > 2 && !(ft && ft.innerHTML.trim())); }",
    "/* no hairline under the top strip (Tate, 2026-10-06: \"make it seemless and blend\"): the strip is the\n   page's own colour and stays unmarked however far you scroll */\nfunction statusHair() { const st = document.getElementById('status'); if (st) st.classList.remove('scrolled'); }")
f.write_text(s)
print('patched', f)
