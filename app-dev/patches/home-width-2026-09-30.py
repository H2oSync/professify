#!/usr/bin/env python3
"""Home runs wider: 12px from the screen edge, and each friend's week grid 8px inside its card.
(Tate, 2026-09-30, from the Home Card Width mockup: "lets do recommended first. for home card width".)

The recommended option, in px: screen edge -> card 12 (was 16), card edge -> grid 8 (was 14),
hour-label column 26 (was 30), gap between days 5 (was 6). At 390px each day column goes from 55.2px
to 60.8px. The header, the stories, the feed and the cards below it all move to the same 12px edge, so
Home keeps one left edge. Only Home changes: Schedule, Plans and friend pages keep 16 / 14 / 30 / 6.

Usage: python3 home-width-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html in place)
Applies after scroll-hide-bars-2026-09-30.py. Every anchor must match exactly once, or nothing is written.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="homepg"' in s: sys.exit('already patched')
R = [
 # 1. the week grid's label column and day gap become variables (defaults unchanged: 30px, 6px)
 (".g-head,.g-body{display:grid;grid-template-columns:30px repeat(5,1fr);gap:6px}",
  ".g-head,.g-body{display:grid;grid-template-columns:var(--glab,30px) repeat(5,1fr);gap:var(--ggap,6px)}"),
 ("  const tmpl = focus ? `grid-template-columns:30px ${days.map(",
  "  const tmpl = focus ? `grid-template-columns:var(--glab,30px) ${days.map("),
 # 2. Home's own spacing, in one place
 (".mightknow{margin:16px 16px 0;",
  """/* Home width (Tate, 2026-09-30): everything on Home sits 12px from the screen edge (was 16), and a
   friend's week sits 8px inside its card (was 14) with a 26px hour column and 5px day gaps. */
.homepg{--hg:12px}
.homepg .homehdr,.homepg .stories{padding-left:var(--hg);padding-right:var(--hg)}
.homepg .hfeed .fcard{margin:0 var(--hg)}
.homepg .mightknow{margin-left:var(--hg);margin-right:var(--hg)}
.homepg .sec-h{padding-left:calc(var(--hg) + 4px);padding-right:calc(var(--hg) + 4px)}
.homepg .fcard .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}
.mightknow{margin:16px 16px 0;"""),
 # 3. wrap Home so the rules above reach only Home
 ("""    body: `
 <div class="homehdr">""",
  """    body: `<div class="homepg">
 <div class="homehdr">"""),
 # the two inline-margined cards on Home follow the same edge
 ("""<div class="card where" style="margin:0 16px">""",
  """<div class="card where" style="margin:0 var(--hg,16px)">"""),
 ("""<div class="card row" style="margin:14px 16px 0;padding:14px 16px"><span class="sq" style="width:44px;height:44px;background:var(--pink-soft);color:var(--pink)">${ic('users', 22)}</span><div class="grow"><div style="font-weight:900;font-size:15.5px">See your friends’ weeks</div>""",
  """<div class="card row" style="margin:14px var(--hg,16px) 0;padding:14px 16px"><span class="sq" style="width:44px;height:44px;background:var(--pink-soft);color:var(--pink)">${ic('users', 22)}</span><div class="grow"><div style="font-weight:900;font-size:15.5px">See your friends’ weeks</div>"""),
]
for a, b in R:   # applied in order; each anchor must match exactly once at its turn
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
# close the wrapper right after Home's own "See your friends' weeks" card, before its spacer
i = s.index('<div class="homepg">')
j = s.index(' <div class="spacer"></div>`, tabbar: true, fab: true', i)
s = s[:j] + ' </div>\n' + s[j:]
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
