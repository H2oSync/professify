#!/usr/bin/env python3
"""Champ's bubble no longer types; he peeks out further (Tate, 2026-09-30).

"take out the effect that the bubble types every time, also have it more peaking instead of just
half Champs face"

- When the bars come back, "Ask Me!" simply fades and pops back in (the existing opacity/scale
  transition). The typing animation, its caret and the bub-type class are removed.
- While tucked away, Champ sits 30px in from the edge instead of 42px, so about 40px of the bird
  shows (his whole face and both eyes) instead of about half his face; the tilt eases to -12deg.

Run from the repo root, after scroll-hide-bars-2026-09-30.py. Idempotent; each anchor must match once.
"""
import sys, pathlib
P = pathlib.Path('app/index.html'); s = P.read_text()
if 'bub-type' not in s and 'translate(30px' in s: print('already applied'); sys.exit(0)
def sub(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: sys.exit(f'anchor matched {c} times (wanted {n}): {a[:80]!r}')
    s = s.replace(a, b)

sub("""/* "Ask Me!" types itself out when Champ comes back. */
#chrome.bub-type .fab .bub .t{display:inline-block;position:relative;animation:bubtype .7s steps(7,end) both}
#chrome.bub-type .fab .bub .t::after{content:"";position:absolute;right:-3px;top:2px;width:1.5px;height:10px;background:currentColor;animation:bubcaret .35s steps(1) 3 forwards}
@keyframes bubtype{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes bubcaret{50%,100%{opacity:0}}
""", "")
sub("#chrome.bub-type .fab .bub .t,#chrome.bub-type .fab .bub .t::after{animation:none}", "")
sub("translate(42px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px))) rotate(-16deg)",
    "translate(30px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px))) rotate(-12deg)")
sub("translate(42px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px)))}",
    "translate(30px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px)))}")
sub("""  clearTimeout(BARS.t);
  if (!hide) { ch.classList.remove('bub-type'); void ch.offsetWidth; ch.classList.add('bub-type'); BARS.t = setTimeout(() => ch.classList.remove('bub-type'), 1100); }
""", "")
P.write_text(s); print('applied')
