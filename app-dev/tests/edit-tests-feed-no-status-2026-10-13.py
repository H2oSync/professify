#!/usr/bin/env python3
"""Tests for feed-no-status-2026-10-13.py (run after edit-tests-builder-options-2026-10-13.py). Replayable."""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def sub(a, b, label):
    global S
    if b in S and a not in S: return
    if S.count(a) != 1: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
# home: no status line on a friend's card (the stories keep it)
sub("'home: each card is a friend, with no “N classes with you” pill (Tate, 2026-09-30)', heads);\n",
    "'home: each card is a friend, with no “N classes with you” pill (Tate, 2026-09-30)', heads);\n"
    "  ok(heads.every(h => !/●|Done for the day|In class|Free (till|now|all day)|Busy/.test(h)), 'home: no “Done for the day” / “In class till …” under a friend’s name (Tate, 2026-10-13)', heads);\n", 'home no status')
# darkSetting read the card's status line: read the card itself
sub("const st = [...document.querySelectorAll('.fcard .b, .fcard div')].find(e => /^● In /.test(e.textContent.trim()) && e.children.length === 0);\n    return { st: st && getComputedStyle(st).color,",
    "const st = document.querySelector('.fcard');\n    return { st: st && getComputedStyle(st).backgroundColor,", 'dark read')
sub("ok(flip.st === 'rgb(110, 162, 255)' && flip.meta === '#0A0F1C,#0A0F1C', 'appearance: the screen is redrawn with dark-mode colours (status line light blue) and the browser bar follows', flip);",
    "ok(flip.st && flip.st !== 'rgb(255, 255, 255)' && flip.meta === '#0A0F1C,#0A0F1C', 'appearance: the screen is redrawn with dark-mode colours (the feed cards go dark) and the browser bar follows', flip);", 'dark check')
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
MUT = [("feed: the status line back", "feedTag(id, v)}\n    </div>", "feedTag(id, v)}<div>● ${esc((status(id) || {}).t || '')}</div>\n    </div>", "home")]
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
if T.count(k) != 1: sys.exit('mutate anchor')
if MUT[0][0] not in T:
    T = T.replace(k, "\n  /* the feed card without a status line (2026-10-13; edit-tests-feed-no-status-2026-10-13.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');", 1)
# the line it mutated is gone (the feed card has no status line at all now)
T = '\n'.join(l for l in T.split('\n') if not l.lstrip().startswith("['No classes today back on Home only',"))
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-feed-no-status: done')
