#!/usr/bin/env python3
"""Explore professor cards: "No ratings yet" sits on the right, where "15 ratings" sits under a rated
professor's chip (Tate, 2026-10-04, on Alexander Hirsig's card under Alexandre Champagne's: "keep consistent no
ratings should be on the right where 15 ratings or 2 ratings would be").

- A professor with no rating: "No ratings yet" (or "N ratings" when PolyRatings has a count but no score) is in the
  same right column (.prt / .prt-n) as a rated card's count, beside the name, not on its own line.
- The middle line keeps only "N% would take again"; with nothing left it is the 10px spacer, as on rated cards.
- With TermChamp reviews but no rating the right side stays empty, as before ("No ratings yet" would be false).
- A card's name may break inside a word that can't fit beside the right column (at 320px a long surname
  would otherwise run under "No ratings yet").

Applies after rating-darker-2026-10-04.py.
Usage: python3 prof-card-no-rating-right-2026-10-04.py <repo-dir>
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const side = r != null' in s: sys.exit('already patched')
R = [
 ("  const line = [r != null ? '' : p.count ? nRatings(p.count) : (!st ? 'No ratings yet' : ''), st && st.again != null ? `${st.again}% would take again` : ''].filter(Boolean).join(' · ');\n",
  "  const side = r != null ? '' : p.count ? nRatings(p.count) : (!st ? 'No ratings yet' : '');\n"
  "  const line = st && st.again != null ? `${st.again}% would take again` : '';\n"),
 (".prt-n{font-size:13px;font-weight:800;color:var(--muted);white-space:nowrap}",
  ".prt-n{font-size:13px;font-weight:800;color:var(--muted);white-space:nowrap}\n.pcard .grow{min-width:0;overflow-wrap:anywhere}"),
 ("${p.count ? `<span class=\"prt-n\">${nRatings(p.count)}</span>` : ''}</span>` : ''}</div>",
  "${p.count ? `<span class=\"prt-n\">${nRatings(p.count)}</span>` : ''}</span>` : side ? `<span class=\"prt\"><span class=\"prt-n\">${side}</span></span>` : ''}</div>"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
