#!/usr/bin/env python3
"""The rating colours, toned down: a darker green, not neon (Tate, 2026-10-04, on Explore's bright-green
circles: "why is the green so neon" → "just dont make it so bright it can be more darker green").

- Same scale, same order, one step per half star (rating-gradient-2026-10-03): green at 5.0 → lime → yellow →
  orange → red at 0.5. The fills are now ~72% saturation instead of 95%, and the greens deeper: 5.0's circle is
  #1AA248 (was a near-pure #2EFA2E), close to the old #16A34A star.
- RATE_BRIGHT is now one fixed table of fills, measured: it stands out from white (2.3–3.4:1, was 1.2–1.4) and
  from the empty grey star, so star rows read better too.
- A circle's initials take RATE_INK, a near-black of the same hue picked for 4.6:1+ on that fill (the darker
  fills are too dark for RATE_DARK's numbers-on-white shade).
- AVERAGE's star on the purple header takes RATE_LIGHT (the darker fills disappear on purple); lighter at
  0.5–1.5 so every step is 3:1+ on the purple.
- RATE_HUE follows the fills (5.0 at 140, the big 5.0's family), so a number, its chip and its circle share a hue.
  RATE_DARK (numbers, 5.0 = #166534) and RATE_PALE (chips) are otherwise unchanged.

Applies after groups-2026-10-03.py (build 2026-10-04 09:20).
Usage: python3 rating-darker-2026-10-04.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const RATE_FILL' in s: sys.exit('already patched')
R = [
 ("const RATE_HUE = [null, 4, 12, 24, 34, 44, 56, 68, 82, 100, 120];\n",
  "const RATE_HUE = [null, 4, 12, 22, 32, 42, 54, 68, 86, 112, 140];\n"
  "/* Toned down (Tate, 2026-10-04: \"dont make it so bright it can be more darker green\"): fills at ~72% saturation,\n"
  "   greens deeper. RATE_INK is a same-hue near-black at 4.6:1+ on its fill, for a circle's initials. */\n"
  "const RATE_FILL = [null, '#E46258', '#E26D50', '#E0793E', '#DD8A2C', '#CE9A22', '#BDAD1F', '#A0B41D', '#70AF1D', '#2EA71B', '#1AA248'];\n"
  "const RATE_INKS = [null, '#450C08', '#491508', '#492008', '#492B08', '#453208', '#453F08', '#394007', '#223706', '#0B2E05', '#052911'];\n"),
 ("const RATE_BRIGHT = s => { const h = RATE_HUE[s]; return `hsl(${h} 95% ${h < 40 ? 64 : h <= 90 ? 55 : 58}%)`; };\n",
  "const RATE_BRIGHT = s => RATE_FILL[s];\n"
  "const RATE_INK = s => RATE_INKS[s];\n"
  "const RATE_LIGHT = s => `hsl(${RATE_HUE[s]} 80% ${[0, 81, 78, 74][s] || 70}%)`;\n"),
 # the old comment said initials take DARK
 ("   0.5 red. BRIGHT fills shapes (circles, star rows, bars), DARK writes (numbers, the star beside a number,\n"
  "   initials on a bright circle, 4.5:1+), PALE sits behind a dark number (the ★ chip). 5.0's dark is the big\n",
  "   0.5 red. BRIGHT fills shapes (circles, star rows, bars), DARK writes (numbers, the star beside a number,\n"
  "   4.5:1+ on white), INK writes initials on a circle, LIGHT is the star on purple, PALE sits behind a dark\n"
  "   number (the ★ chip). 5.0's dark is the big\n"),
 (", fill: RATE_BRIGHT(st) }; };", ", fill: RATE_BRIGHT(st), light: RATE_LIGHT(st) }; };"),
 ("  return { bg: RATE_BRIGHT(step), ink: RATE_DARK(step), step: step / 2 };",
  "  return { bg: RATE_BRIGHT(step), ink: RATE_INK(step), step: step / 2 };"),
 ("${starI(15, rateTone(r).fill)}", "${starI(15, rateTone(r).light)}"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
