#!/usr/bin/env python3
"""Home feed cards: no "Done for the day" / "In class till …" line under a friend's name (Tate, 2026-10-13:
"we dont need done for day or in class till"). The stories and the Friends list keep it.
Usage: python3 feed-no-status-2026-10-13.py <repo-dir>   (replayable on build 2026-10-12 22:32)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if b in S and a not in S: return
    if S.count(a) != 1: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""    ${st && st.free !== null && !st.quiet ? `<div style="font-size:12.5px;font-weight:800;color:${st.c || 'var(--muted)'};margin-top:3px">● ${esc(st.t)}</div>` : ''}</div>""",
    "    </div>", 'feed status line')
rep("  const st = isMe ? null : status(id);\n", "", 'feed st')
open(PA, 'w', encoding='utf-8').write(S); print('feed-no-status: done')
