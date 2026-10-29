#!/usr/bin/env python3
"""Tate, 2026-10-28, on Home's "Classes your friends are planning" row: "kind of blends with the
background so lets make sure the contrast works and that it doesnt get lost".
The cards' pale-blue tops (#E3ECFF) sat on a #E7ECF5 page, and their white bodies had only a soft
shadow. Now: a solid class-blue top (#2563EB) with white code and friend count (5.2:1), a thin blue
edge round each card, and a firmer shadow, in light and dark."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:60], n); s = s.replace(a, b)
one('.homepg .recs-row{padding-bottom:20px;margin-bottom:-18px}\n',
    '.homepg .recs-row{padding-bottom:20px;margin-bottom:-18px}\n'
    '/* 2026-10-28 (Tate): the suggested row was getting lost on the page — solid class-blue tops,\n'
    '   white text on them, and a defined edge on every card (light and dark). */\n'
    '.rm-top{background:var(--blue)}\n'
    '.rmini .rm-k,.rm-top .rm-p{color:#fff}\n'
    '.recs .card.rmini{box-shadow:0 0 0 1.5px rgba(37,99,235,.28),0 2px 4px rgba(15,23,42,.06),0 12px 26px rgba(22,51,107,.16)}\n'
    ':root[data-theme="dark"] .recs .card.rmini{box-shadow:0 0 0 1.5px rgba(110,162,255,.35),0 12px 26px rgba(0,0,0,.35)}\n')
p.write_text(s); print('recs-contrast applied')
