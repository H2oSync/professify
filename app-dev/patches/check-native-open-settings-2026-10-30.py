#!/usr/bin/env python3
"""Goes with pushask-popup-2026-10-30.py: Settings › Notifications, when iOS has been told no, is now an
"Open Settings" button (straight to TermChamp's page in iPhone Settings), not "Settings › TermChamp › Notifications"
in words. check-native.mjs's denied check follows. Target path argv[1] (default app-dev/tests/check-native.mjs)."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app-dev/tests/check-native.mjs'); s = p.read_text()

def one(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:120]); s = s.replace(a, b)

one("""  ok(/Settings › TermChamp › Notifications/.test(body) && await page.locator('#scroll [data-a="pushAllow"]').count() === 0, 'native: denied → points to iPhone Settings, no dead button');""",
"""  ok(/Notifications are off for TermChamp/.test(body) && await page.locator('#scroll [data-a="pushOpenIOS"]').count() === 1 && await page.locator('#scroll [data-a="pushAllow"]').count() === 0, 'native: denied → an Open Settings button to iPhone Settings, no dead button');""")

p.write_text(s); print(p, 'check-native: denied check follows Open Settings')
