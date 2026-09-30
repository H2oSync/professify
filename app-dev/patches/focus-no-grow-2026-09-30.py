#!/usr/bin/env python3
"""The focused day no longer grows the grid, and hour labels land on even steps.
(Tate, 2026-09-30, looking at 03:10: "when you click on a day it doesn't need to grow so much
have it not grow at all. also whats wrong with Sofias schedule why does it go from 12p-2p-3p")

- The body keeps the height it had before the tap. A wide block that is too short for three rows
  stacks code over time at the two small sizes with the faces to the right ("wide tight"); a tall
  one keeps the three-row column. Faces that don't fit are left off whole (never cut), and the block's
  title carries the friend count so a narrow column never hides how many are in the class.
- Hour labels use the largest step (1h, 2h, 3h, 4h) that divides the axis evenly with at most 8
  labels, so a 3-hour card reads 12p 1p 2p 3p, never 12p 2p 3p. The last label is no longer forced.

Usage: python3 focus-no-grow-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html in place)
Applies after home-grid-fit-2026-09-30.py. Every anchor must match exactly once, or nothing is written.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'wide tight' in s or 'in this class' in s: sys.exit('already patched')
R = [
 # 1. the body never grows for a focused day
 ("""  /* A focused day gets a taller body when its shortest class would otherwise be under 40px, so
     back-to-back classes on a long day never overlap. */
  const dur = focus ? secs.filter(s => timed(s) && s.days.includes(focus)).map(s => s.e - s.s) : [];
  const need = o.faces ? 52 : 40;   /* a wide block needs this much for code + time (+ faces) */
""", ""),
 ("""  const H = dur.length ? Math.min(900, Math.max(base, Math.ceil(need * (S1 - S0) / Math.min(...dur)))) : base;""",
  """  const H = base;   /* focusing a day never changes the height (Tate, 2026-09-30) */"""),
 # 2. hour labels on an even step, never a stray last label
 ("""  const step = S1 - S0 > 480 ? 180 : 120;
  /* Hour labels every 2h (3h past an 8-hour span), always ending on the last hour of the axis. */
  const ms = []; for (let m = S0; m < S1; m += step) ms.push(m);
  if (S1 - ms[ms.length - 1] < step / 2) ms.pop(); ms.push(S1);
""", """  /* Hour labels on the smallest even step (1h, 2h, 3h, 4h) that divides the axis into at most 7
     steps — a 3-hour card reads 12p 1p 2p 3p, a 12-hour day 8a 10a … 8p. When no step divides it,
     labels run from the top on the smallest step that fits and the axis end goes unlabelled, rather
     than landing a label an hour under the one before it. */
  const span = S1 - S0, STEPS = [60, 120, 180, 240];
  const step = STEPS.find(st => span % st === 0 && span / st <= 7) || STEPS.find(st => span / st <= 7) || 240;
  const ms = []; for (let m = S0; m <= S1; m += step) ms.push(m);
"""),
 # 3. wide blocks: the same minimum as the narrow ones; a tight two-line layout when there is no room for three rows
 ("""      /* Minimum heights: two lines of code always fit (24), a wide block fits code + time (34), and
         code + time + a row of faces (52). */
      const h = Math.max((s.e - s.s) * k, wide ? (faces ? 52 : 34) : o.fit ? 26 : (o.one ? 30 : 24));""",
  """      /* Minimum height: two lines of code always fit (24; 26 in a fitted card). A wide block with
         room for three rows stacks code / time / faces; a shorter one puts them on one line. */
      const h = Math.max((s.e - s.s) * k, o.fit ? 26 : (o.one ? 30 : 24));
      const tight = wide && h < (faces ? 56 : 36);   /* no room for three rows */
      const nf = wide && o.faces ? friendsIn(s.code).length : 0;"""),
 ("""title="${esc(s.code + ' · ' + course(s.code).title)}">${inner}</button>`;""",
  """title="${esc(s.code + ' · ' + course(s.code).title + (nf ? ` · ${nf} friend${nf === 1 ? '' : 's'} in this class` : ''))}">${inner}</button>`;"""),
 # (anchored on the start of the line only, so it applies with or without 05:00's ghost class)
 ("""      const cls = ['g-b', wide ? 'wide' : '', live ? 'live' : '',""",
  """      const cls = ['g-b', wide ? (tight ? 'wide tight' : 'wide') : '', live ? 'live' : '',"""),
 # 4. CSS for the tight wide block
 (""".g-b.wide .g-faces{margin-top:1px}
""", """.g-b.wide .g-faces{margin-top:1px}
/* tight wide block (under 36px, or under 56px with faces): code over time at the two small sizes,
   the faces to the right taking only what is left. Whole faces only: the ones that don't fit wrap onto
   a second line 20px down, hidden by the clip. "+N" is the last item, so it can only show when every
   face before it shows too — a visible count is always the true remainder. The 2px padding keeps the
   faces' rings out of the clip. */
.g-b.wide.tight{display:grid;grid-template-columns:auto minmax(0,1fr);grid-template-rows:auto auto;align-items:center;justify-items:start;column-gap:5px;row-gap:1px;padding:2px 6px;line-height:1}
.g-b.wide.tight .g-code{font-size:10px;grid-column:1;grid-row:1}
.g-b.wide.tight .g-time{font-size:9px;grid-column:1;grid-row:2}
.g-b.wide.tight .g-faces{grid-column:2;grid-row:1/3;margin:0 -2px;padding:2px;justify-self:end;min-width:0;max-width:calc(100% + 4px);display:flex;flex-wrap:wrap;gap:20px 2px;justify-content:flex-end;align-content:flex-start;max-height:23px;overflow:hidden}
"""),
 ("""@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide .g-time{font-size:9px}.g-b.wide .g-code{font-size:10.5px}}""",
  """@media (max-width:340px){.g-b.wide{padding:5px 4px}.g-b.wide.tight{padding:2px 4px;column-gap:3px}.g-b.wide .g-time{font-size:9px}.g-b.wide .g-code{font-size:10.5px}}"""),
]
for a, b in R:   # applied in order; each anchor must match exactly once at its turn
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
assert 'need * (S1 - S0)' not in s, 'the grow rule is still there'
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
