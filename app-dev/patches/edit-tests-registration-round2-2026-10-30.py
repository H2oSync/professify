#!/usr/bin/env python3
"""Test edit for registration-round2-2026-10-30.py: on Nov 4 with no day the term card no longer drops to "just your
units" — Round 2 is open ("Round 2 is open · till Nov 17 · Add your day"). "Just your units" moves to Nov 18, when
both rounds are over (Open Enrollment). Usage: python3 edit-tests-registration-round2-2026-10-30.py app-dev/tests/check-app.mjs"""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests/check-app.mjs'); s = p.read_text()
if 'registration-round2 (2026-10-30)' in s:
    sys.exit('already patched')
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""  o = await regOpenPlanner({ time: '2026-11-04T09:00:00-08:00' });
  v = await regLine(o.page);
  ok(/^\\d+ units · What matters most: /.test(v.line) && !v.units && v.fr === null, 'regday states: Round 1 over, no day — just your units', v);
  await o.close();""", """  o = await regOpenPlanner({ time: '2026-11-04T09:00:00-08:00' });
  v = await regLine(o.page);
  ok(v.line === 'Round 2 is open · till Nov 17 Add your day' && v.units > 0 && v.fr === null, 'regday states: Round 1 over, no day — Round 2 is open, Add your day (registration-round2 (2026-10-30))', v);
  await o.close();
  o = await regOpenPlanner({ time: '2026-11-18T09:00:00-08:00' });
  v = await regLine(o.page);
  ok(/^\\d+ units · What matters most: /.test(v.line) && !v.units && v.fr === null, 'regday states: both rounds over (Open Enrollment), no day — just your units', v);
  await o.close();""")
p.write_text(s); print(p, 'edit-tests-registration-round2: ok')
