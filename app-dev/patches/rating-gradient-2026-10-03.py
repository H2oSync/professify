#!/usr/bin/env python3
"""One rating scale for the whole phone app, along Tate's gradient (Tate, 2026-10-03, on the "Rating Greens"
mockup's swatch strip: "i love this but make everything consistent so a 5 on everything should be the farthest
left green and the worst teachers furthest right"; before that: "lets keep all of these greens consistent i
like the dark green that the big 5 is").

- Ten steps, one per half star: green at 5.0 → lime → yellow → orange → red at 0.5.
- Each step has three shades:
  - RATE_BRIGHT fills shapes: a professor's circle, star rows (rate form, reviews, thanks screen, Me), the
    review bars and AVERAGE's star on the purple header.
  - RATE_DARK writes: a rating number and the small star beside it, and a circle's initials (4.5:1+ on its
    bright circle, 5:1+ on white and on its pale chip).
  - RATE_PALE sits behind a dark number: the ★ chip.
  At 5.0 the dark is the big 5.0's #166534 and the pale is the chip's #DCFCE7, as before.
- Replaces three scales that disagreed: rateTone (3 colours: chips, numbers, header star), SC (5 colours: star
  rows, by whole star) and profTone's own 10 (circles). rateTone keeps its good / mid / low class (k) on the
  desktop's cut-offs.
- No rating stays neutral grey everywhere.

Applies after no-photo-gray-2026-10-03.py.
Usage: python3 rating-gradient-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const RATE_HUE' in s: sys.exit('already patched')
R = [
 ("const SC=['#E6EAF1','#DC2626','#F97316','#EAB308','#84CC16','#16A34A'];\n",
  "/* ONE rating scale for the whole app (Tate, 2026-10-03): a 5 is the far-left green on everything, the worst\n"
  "   teachers the far-right red. One step per half star along his gradient: 5.0 green → lime → yellow → orange →\n"
  "   0.5 red. BRIGHT fills shapes (circles, star rows, bars), DARK writes (numbers, the star beside a number,\n"
  "   initials on a bright circle, 4.5:1+), PALE sits behind a dark number (the ★ chip). 5.0's dark is the big\n"
  "   5.0's #166534. No rating is never a colour: callers draw grey. */\n"
  "const RATE_HUE = [null, 4, 12, 24, 34, 44, 56, 68, 82, 100, 120];\n"
  "const rateStep = r => Math.min(10, Math.max(1, Math.round(r * 2)));\n"
  "const RATE_BRIGHT = s => { const h = RATE_HUE[s]; return `hsl(${h} 95% ${h < 40 ? 64 : h <= 90 ? 55 : 58}%)`; };\n"
  "const RATE_DARK = s => { const h = RATE_HUE[s]; return s === 10 ? '#166534' : `hsl(${h} 70% ${h < 40 ? 18 : h <= 90 ? 22 : 24}%)`; };\n"
  "const RATE_PALE = s => s === 10 ? '#DCFCE7' : `hsl(${RATE_HUE[s]} 85% 90%)`;\n"),
 ("const starCol = v => SC[Math.ceil(halfOf(v))];",
  "const starCol = v => { const h = halfOf(v); return h ? RATE_BRIGHT(h * 2) : '#E6EAF1'; };"),
 ("const rateTone = r => r == null ? null : r * 0.8 >= 3.3 - 1e-9 ? { k: 'good', star: '#16A34A', ink: '#166534', bg: '#DCFCE7' }\n"
  "  : r * 0.8 >= 2.5 - 1e-9 ? { k: 'mid', star: '#D97706', ink: '#92400E', bg: '#FEF3C7' } : { k: 'low', star: '#DC2626', ink: '#B91C1C', bg: '#FEE2E2' };",
  "const rateTone = r => { if (r == null || !isFinite(r)) return null; const st = rateStep(r);\n"
  "  return { k: r * 0.8 >= 3.3 - 1e-9 ? 'good' : r * 0.8 >= 2.5 - 1e-9 ? 'mid' : 'low', step: st / 2, star: RATE_DARK(st), ink: RATE_DARK(st), bg: RATE_PALE(st), fill: RATE_BRIGHT(st) }; };"),
 ("const PROF_HUE = { 10: 150, 9: 118, 8: 90, 7: 68, 6: 50, 5: 38, 4: 26, 3: 14, 2: 2, 1: 340 }, PROF_L = { 10: 78, 1: 80 };\n"
  "function profTone(r) {\n"
  "  if (typeof r !== 'number' || !isFinite(r) || r <= 0) return { bg: '#E6EAF1', ink: '#475569', step: null };\n"
  "  const step = Math.min(10, Math.max(1, Math.round(r * 2))), h = PROF_HUE[step];\n"
  "  return { bg: `hsl(${h} 80% ${PROF_L[step] || 84}%)`, ink: `hsl(${h} 75% 21%)`, step: step / 2 };\n"
  "}",
  "function profTone(r) {\n"
  "  if (typeof r !== 'number' || !isFinite(r) || r <= 0) return { bg: '#E6EAF1', ink: '#475569', step: null };\n"
  "  const step = rateStep(r);\n"
  "  return { bg: RATE_BRIGHT(step), ink: RATE_DARK(step), step: step / 2 };\n"
  "}"),
 ("  const barC = ['#16A34A', '#84CC16', '#EAB308', '#F97316', '#DC2626'];",
  "  const barC = [10, 8, 6, 4, 2].map(RATE_BRIGHT);"),
 # AVERAGE's star on the purple header: the bright shade (the dark one disappears on purple)
 ("<span class=\"avgstar rt-${rateTone(r).k}\">${starI(15, rateTone(r).star)}</span>",
  "<span class=\"avgstar rt-${rateTone(r).k}\">${starI(15, rateTone(r).fill)}</span>"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
for gone in ('SC[', 'PROF_HUE', 'PROF_L'):
    if gone in s: sys.exit(f'{gone} still used')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
