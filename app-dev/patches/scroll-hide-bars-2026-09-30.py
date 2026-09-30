#!/usr/bin/env python3
"""Tab bar and Champ get out of the way while you scroll (Tate, 2026-09-30).

"make it so when you scroll on the app that the tool bar and the bird go away. like instagram and
linkedIn. have the bird visually go and hide on the right and have the bubble disappear, have it
peeking out behind the edge of phone then have it come back when you scroll a small bit up ...
make sure when champ comes back that his bubble comes back visually have it type ask me out"

- Scrolling down (past the first 60px) slides the tab bar off the bottom, fades the "Ask Me!"
  bubble and tucks Champ behind the right edge of the screen, tilted, with a sliver still showing
  (and still tappable).
- A small scroll up (12px), reaching the top, or going to another screen brings both back; the
  bubble types "Ask Me!" out again, letter by letter.
- The state lives on #chrome (a class), which survives render() rebuilding the bar and the bird.
- Reduced motion: no slide or typing; the bar and bird just appear and disappear.

Run from the repo root (idempotent; each anchor must match once).
"""
import sys, pathlib
P = pathlib.Path('app/index.html'); s = P.read_text()
MARK = '/* ---------- tab bar + Champ hide on scroll'
if MARK in s: print('already applied'); sys.exit(0)
def sub(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n} times: {a[:80]!r}')
    s = s.replace(a, b)

sub("@keyframes soar{0%,100%{transform:translateY(0) rotate(0)}30%{transform:translateY(-6px) rotate(-2.5deg)}65%{transform:translateY(-2px) rotate(2deg)}}\n",
"""@keyframes soar{0%,100%{transform:translateY(0) rotate(0)}30%{transform:translateY(-6px) rotate(-2.5deg)}65%{transform:translateY(-2px) rotate(2deg)}}
/* ---------- tab bar + Champ hide on scroll (2026-09-30) ---------- */
#chrome .tabbar{transition:transform .28s cubic-bezier(.2,.8,.2,1),visibility 0s linear 0s}
#chrome .fab{transition:transform .34s cubic-bezier(.2,.8,.2,1)}
#chrome .fab .bub{transition:opacity .16s ease,transform .2s ease;transform-origin:50% 100%}
#chrome.bars-hid .tabbar{transform:translateY(100%);visibility:hidden;transition:transform .24s ease-in,visibility 0s linear .24s}
/* Tucked behind the right edge: a sliver of the bird's face shows, tilted as if peeking. */
#chrome.bars-hid .fab{transform:translate(42px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px))) rotate(-16deg)}
#chrome.bars-hid .fab .bub{opacity:0;transform:scale(.4)}
#chrome.bars-hid .fab img{animation-play-state:paused}
/* "Ask Me!" types itself out when Champ comes back. */
#chrome.bub-type .fab .bub .t{display:inline-block;position:relative;animation:bubtype .7s steps(7,end) both}
#chrome.bub-type .fab .bub .t::after{content:"";position:absolute;right:-3px;top:2px;width:1.5px;height:10px;background:currentColor;animation:bubcaret .35s steps(1) 3 forwards}
@keyframes bubtype{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes bubcaret{50%,100%{opacity:0}}
@media (prefers-reduced-motion:reduce){#chrome .tabbar,#chrome .fab,#chrome .fab .bub{transition:none}#chrome.bub-type .fab .bub .t,#chrome.bub-type .fab .bub .t::after{animation:none}#chrome.bars-hid .fab{transform:translate(42px,calc(var(--tb) - 14px - env(safe-area-inset-bottom,0px)))}}
""")

sub("""<span class="bub">Ask Me!</span>""", """<span class="bub"><span class="t">Ask Me!</span></span>""")

sub("""function render(keep) {
  const sc = document.getElementById('scroll'); if (!sc) return;""",
"""/* Scrolling down tucks the tab bar and Champ away; a small scroll up (or the top, or a new screen)
   brings them back. One listener on #scroll, which is never rebuilt. */
const BARS = { y: 0, up: 0, hid: false, t: null };
function setBars(hide) {
  const ch = document.getElementById('chrome'); if (!ch || BARS.hid === hide) return;
  BARS.hid = hide; ch.classList.toggle('bars-hid', hide);
  clearTimeout(BARS.t);
  if (!hide) { ch.classList.remove('bub-type'); void ch.offsetWidth; ch.classList.add('bub-type'); BARS.t = setTimeout(() => ch.classList.remove('bub-type'), 1100); }
}
function onScrollBars() {
  const sc = document.getElementById('scroll'); if (!sc) return;
  const y = sc.scrollTop, dy = y - BARS.y; BARS.y = y;
  if (UI.sheet || UI.champ) return;
  /* iOS bounces past the end of a list; the bounce back is not the student scrolling up. */
  if (y >= sc.scrollHeight - sc.clientHeight - 2) { BARS.up = 0; return; }
  if (y <= 8) { BARS.up = 0; return setBars(false); }
  if (dy > 0) { BARS.up = 0; if (y > 60 && dy >= 2) setBars(true); }
  else if (dy < 0) { BARS.up -= dy; if (BARS.up >= 12) setBars(false); }
}
function render(keep) {
  const sc = document.getElementById('scroll'); if (!sc) return;
  if (!sc._barsOn) { sc._barsOn = true; sc.addEventListener('scroll', onScrollBars, { passive: true }); }""")

# A new screen (not a keep-render) brings the bars back and resets the scroll tracking.
sub("""  if (keep) sc.scrollTop = y; else sc.scrollTop = e.y || 0;""",
"""  if (keep) sc.scrollTop = y; else { sc.scrollTop = e.y || 0; BARS.y = sc.scrollTop; BARS.up = 0; setBars(false); }""")
# Closing a sheet or Champ brings the bars back.
sub("  closeSheet: () => { UI.sheet = null; UI.champ = false; render(true); },",
    "  closeSheet: () => { UI.sheet = null; UI.champ = false; render(true); setBars(false); },")
P.write_text(s); print('applied')
