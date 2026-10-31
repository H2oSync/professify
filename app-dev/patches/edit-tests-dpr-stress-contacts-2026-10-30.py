#!/usr/bin/env python3
"""tests.dprStressQuarter reloads the page, which is a 2nd app open: the contacts pop-up (now in the
pop-up queue, 1.2s after an open on Home) then covers the Builder. This test is about the report, so it
marks contacts connected for its student before the app loads."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests/check-app.mjs'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""tests.dprStressQuarter = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });""",
"""tests.dprStressQuarter = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });
  await page.addInitScript(() => { try { const s0 = JSON.parse(localStorage.getItem('sb-rqkndeqbcahozidniesn-auth-token') || 'null'); if (s0 && s0.user) localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true })); } catch (e) {} });""")
p.write_text(s); print(p, 'tests: dprStressQuarter marks contacts connected')
