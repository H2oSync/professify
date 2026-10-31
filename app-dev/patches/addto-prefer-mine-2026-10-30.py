#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): a section that is in My Classes AND in a plan opened Add to your week on the
plan, so the student couldn't reach its My Classes status (Enrolled/Waitlisted) or remove it from My Classes without
first switching. My Classes wins when the section is in it."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""  const dest = inPlan || (inMine ? 'mine' : last || (AT_PLANS.includes(S.plan) ? S.plan : 'A'));""",
    """  const dest = inMine ? 'mine' : inPlan || last || (AT_PLANS.includes(S.plan) ? S.plan : 'A');""")
p.write_text(s); print('addto-prefer-mine applied')
