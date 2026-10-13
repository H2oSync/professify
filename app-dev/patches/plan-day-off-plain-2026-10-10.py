#!/usr/bin/env python3
"""Planner card A: a weekday with no class is a plain column (Tate, 2026-10-10: "take out the free friday make it
normal"). The green "FREE" column and the green day name are gone; the day off stays in the Day off tile.
  python3 plan-day-off-plain-2026-10-10.py <repo-dir>"""
import sys, os
PI = os.path.join(sys.argv[1], 'app', 'index.html')
A = open(PI, encoding='utf-8').read()

def rep(s, a, b, what):
    c = s.count(a)
    if c != 1: sys.exit(f'plan-day-off-plain: anchor "{what}" found {c}x (want 1)')
    return s.replace(a, b)

A = rep(A, "      if (!day.length) return `<div class=\"pla-col pla-free\"><span>Free</span></div>`;\n",
        "      if (!day.length) return `<div class=\"pla-col\"></div>`;\n", 'free column')
A = rep(A, "${PL_DAYS.map(([d, nm]) => `<span class=\"${used(d) ? '' : 'free'}\">${nm}</span>`).join('')}",
        "${PL_DAYS.map(([d, nm]) => `<span>${nm}</span>`).join('')}", 'day names')
A = rep(A, "    const used = d => timed.some(x => x.days.includes(d));\n", "", 'used()')
A = rep(A, ".pla-dh .free{color:var(--green-ink3)}\n", "", 'css day name')
A = rep(A, ".pla-free{display:flex;align-items:center;justify-content:center;background:var(--green-wash)}\n.pla-free span{font-size:11px;font-weight:900;color:var(--green-ink2);writing-mode:vertical-rl;letter-spacing:.08em;text-transform:uppercase}\n", "", 'css column')
if 'pla-free' in A or 'used(d)' in A: sys.exit('plan-day-off-plain: something still draws the free day')
open(PI, 'w', encoding='utf-8').write(A)
print('plan-day-off-plain-2026-10-10: applied')
