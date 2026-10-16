#!/usr/bin/env python3
"""(2026-10-15) app-harness.mjs: the two pinned-friends functions the sync SQL adds (sql/professify-sync-2026-10-15.sql) answer like the real ones —
set_pinned_friends(p_ids) keeps the first 3 and returns them, my_pinned_friends() returns what was kept — unless a test supplies its own `rpc` entry.
Before this every unknown RPC answered [], which would read as "the server kept nothing".
Usage: python3 edit-harness-sync-2026-10-15.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/app-harness.mjs'; s = p.read_text()
if 'pinsSrv' in s: sys.exit('already edited')
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80]); s = s.replace(a, b)
rep("  let authed = signedIn;", "  let pinsSrv = [];                      // the stand-in for profiles.pinned_friends (my_pinned_friends / set_pinned_friends)\n  let authed = signedIn;")
rep("        const v = fn in rpc ? rpc[fn] : [];",
    "        let v = fn in rpc ? rpc[fn] : [];\n        if (!(fn in rpc) && fn === 'my_pinned_friends') v = pinsSrv.slice();\n        if (!(fn in rpc) && fn === 'set_pinned_friends') { pinsSrv = ((body && body.p_ids) || []).slice(0, 3); v = pinsSrv.slice(); }")
p.write_text(s); print('edited', p)
