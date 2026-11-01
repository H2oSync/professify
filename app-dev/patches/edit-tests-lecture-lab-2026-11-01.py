#!/usr/bin/env python3
"""2026-11-01: lecture + lab. check-app's Saturday-class fixture (BUS 3384A) is a lecture + activity class, so the
"Add to your week" note now goes on to say it also needs an activity. Usage: <script> <repo root>"""
import sys, os
root = sys.argv[1]
p = os.path.join(root, 'app-dev/tests/check-app.mjs'); s = open(p).read()
a = r"/^Fits Plan C — it meets only on the weekend, so it goes under Anytime\.$/.test(r.note)"
b = r"/^Fits Plan C — it meets only on the weekend, so it goes under Anytime\.( BUS 3384A also needs an activity — add one next\.)?$/.test(r.note)"
if s.count(b) == 0:
    assert s.count(a) == 1, a; s = s.replace(a, b)
open(p, 'w').write(s)
print('edit-tests-lecture-lab: done')
