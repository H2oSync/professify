#!/usr/bin/env python3
"""tests.legalText: the Privacy Policy is dated 30 October 2026 (Connect contacts) and says so."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests/check-app.mjs'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""/Last updated 6 October 2026/.test(priv) && /support@termchamp\\.com/.test(all) && !/tdogtate/.test(all), 'legal: terms dated 4 October, privacy 6 October 2026 (notifications), contact support@termchamp.com');""",
    """/Last updated 30 October 2026/.test(priv) && /Find friends from your contacts/.test(priv) && !/No phone number, in any form/.test(priv) && /support@termchamp\\.com/.test(all) && !/tdogtate/.test(all), 'legal: terms dated 4 October, privacy 30 October 2026 (contacts), contact support@termchamp.com');""")
p.write_text(s); print(p, 'tests: privacy dated 30 October')
