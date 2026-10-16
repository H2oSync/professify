#!/usr/bin/env python3
"""(2026-10-15) Keeps check-app.mjs true after sync-app-2026-10-15.py:
  - the profile read now asks for `concentration` (it is granted; the website reads it too). A database that refuses the column (the harness's default grants,
    42501) is answered with the old read, so a refused column still never breaks sign-in: the test asserts both reads.
  - 'recover' counted at most one profiles read before the account decision; the refused-column retry makes it two (still nothing else is read).
Usage: python3 edit-tests-app-sync-2026-10-15.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
if 'sync-app (2026-10-15)' in s: sys.exit('already edited')
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
rep("ok(own.length >= 1 && own.every(r => !/concentration|select=\\*/.test(decodeURIComponent(r))), 'profile: own read names only granted columns', own);",
    "ok(own.length === 2 && /concentration/.test(decodeURIComponent(own[0])) && !/concentration|select=\\*/.test(decodeURIComponent(own[1])) && own.every(r => !/select=\\*/.test(decodeURIComponent(r))), 'profile: own read asks for concentration (sync-app (2026-10-15)) and, refused with 42501, is read again with granted columns only', own);")
rep("log.reads.filter(r => /^profiles\\b/.test(r)).length <= 1, 'recover:", "log.reads.filter(r => /^profiles\\b/.test(r)).length <= 2, 'recover:")
p.write_text(s); print('edited', p)
