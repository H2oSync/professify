#!/usr/bin/env python3
"""Home cards: the "No classes 2p–6p" bands come back out (Tate, 2026-09-30, on a screenshot of the
dashed band: "also take out these little things"). This reverses the fold half of grid-folds (07:30).

Hours run straight through again, and every hour label sits on its step (an 8a–8p card reads
8a 10a 12p 2p 4p 6p 8p). Kept from 07:30: back-to-back classes get room where the card has space, cards
stay ≤300px, a block's minimum height never runs into the next class, and a tapped day spreads 2/3 as
much. Trade-off: an 8a–8p card is back to 25px an hour (the 300px cap); raise the cap for such cards if
it feels cramped — don't bring the band back.

This is the merge of the two 08:00 forks: a parallel session made the same change on 07:30 (commit
07a77a9, never in this repo); this script re-does it on the other 08:00 (0b1f3bb), after
home-no-set-time. With the builder gone, `folds` is always empty, so Y(), the labels and the block
clamp reduce to the pre-fold grid.

Usage: python3 no-grid-folds-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os, re
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="g-fold"' not in s: sys.exit('already patched')
R = [
 ("  if (o.fit) { const iv = secs.filter(timed).map(s => [s.s, s.e]).sort((x, y) => x[0] - y[0]); let end = iv.length ? iv[0][1] : S0;\n"
  "    for (let i = 1; i < iv.length; i++) { const a = Math.ceil(end / 60) * 60, b = Math.floor(iv[i][0] / 60) * 60; if (b - a >= 120) folds.push([a, b]); end = Math.max(end, iv[i][1]); } }\n",
  "  /* (no folds: Tate took the \"No classes 2p–6p\" bands back out, 2026-09-30) */\n"),
 ("${cols}${folds.map(([a, b]) => `<div class=\"g-fold\" style=\"top:${Y(a)}px;height:${FOLD}px\"><span>No classes ${hs(a)}–${hs(b)}</span></div>`).join('')}</div></div>`;",
  "${cols}</div></div>`;"),
 # the comments that described folds (the fold plumbing below stays, always empty, so the mutants that
 # anchor on it keep their meaning; the Tjudd probe is what proves no band comes back)
 ("  /* Fitted cards (Home) fold every stretch of 2+ whole hours with no class on any day into a thin\n"
  "     \"No classes\" band, and give back-to-back classes room:",
  "  /* Fitted cards (Home) give back-to-back classes room (the \"No classes\" fold bands were taken back\n"
  "     out, Tate 2026-09-30, so `folds` below is always empty):"),
 ("  /* minute -> px down the body; each fold is FOLD px tall (nothing is ever drawn inside one) */",
  "  /* minute -> px down the body (with no folds, a straight scale) */"),
 ("  /* with folds: label each stretch on the same step, and always label both edges of a fold */",
  "  /* (fold labelling; never runs now that folds is always empty) */"),
 ("      /* a block stops at the bottom of the card, or at the top of the next fold band below it */",
  "      /* a block stops at the bottom of the card */"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:70]}')
    s = s.replace(a, b)
s, n = re.subn(r"\n/\* a folded stretch with no classes on any day \(Home cards, 2026-09-30\) \*/\n\.g-fold\{[^\n]*\}\n\.g-fold span\{[^\n]*\}\n", "\n", s)
if n != 1: sys.exit(f'.g-fold CSS matched {n}x')
assert 'g-fold' not in s and 'folds.push' not in s
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
