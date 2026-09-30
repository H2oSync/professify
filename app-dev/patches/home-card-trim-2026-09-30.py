#!/usr/bin/env python3
"""Home friend cards lose two lines (Tate, 2026-09-30):
  - the "yellow = shared" line under the week ("we can take this away");
  - the "N classes with you" pill under the name ("lets also remove the 1 class with you or 0 or whatever it is").
The yellow ring on shared classes stays. "Your week" (shown when you have no friends yet) keeps its
"Fall 2026 · 5 classes" pill. A friend whose classes didn't load already says so in the card body
("Couldn't load <name>'s classes"), so the pill's "Classes didn't load" goes with it.

Applies after focus-width-2026-09-30.py (07:30).
Usage: python3 home-card-trim-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'yellow = shared' not in s: sys.exit('already patched')
R = [
 ("  ${week}\n"
  "  ${nClasses && shared.size ? '<div class=\"foot\"><span style=\"color:#A16207\">yellow = shared</span></div>' : ''}\n"
  " </div>`;",
  "  ${week}\n </div>`;"),
 ("    <span class=\"pillchip\">${isMe ? `${esc(CFG.TERM_LABEL)} · ${nClasses} class${nClasses === 1 ? '' : 'es'}` : TC.err.friendSecs ? 'Classes didn’t load' : `${shared.size} class${shared.size === 1 ? '' : 'es'} with you`}</span>\n"
  "    ${st && st.free !== null ? `<div style=\"font-size:12.5px;font-weight:800;color:${st.c || 'var(--muted)'};margin-top:5px\">",
  "    ${isMe ? `<span class=\"pillchip\">${esc(CFG.TERM_LABEL)} · ${nClasses} class${nClasses === 1 ? '' : 'es'}</span>` : ''}\n"
  "    ${st && st.free !== null ? `<div style=\"font-size:12.5px;font-weight:800;color:${st.c || 'var(--muted)'};margin-top:3px\">"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:70]}')
    s = s.replace(a, b)
assert 'yellow = shared' not in s and 'with you`}' not in s
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
