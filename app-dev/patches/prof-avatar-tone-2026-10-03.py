#!/usr/bin/env python3
"""A professor's initials circle takes the colour of their rating (Tate, 2026-10-03, on Ryan Tully-Doyle's
Explore card: "make the circlar professor profile the color of their rating so it'll be green for 5 star and
color coordinated down to .5 of a star").

- profTone(r): the rating rounded to the nearest half star (0.5 … 5.0) picks one of ten steps, green at 5.0
  through lime, yellow, amber and orange to red at 0.5. Each step is a soft fill with dark initials in the
  same hue (contrast 6:1 or better), so the circle stays readable.
- Every professor circle uses it: Explore cards and search rows, class-page professor rows, the class
  preview, the rate list's form and thanks screen, and the professor page's header (white ring on purple).
- No rating → a neutral grey circle, never a colour that reads as a score. "Instructor not assigned" keeps
  its plain "?" circle.
- The circle is decoration for screen readers (aria-hidden): the name and the written rating sit beside it.

Applies after chat-actions-2026-10-03.py.
Usage: python3 prof-avatar-tone-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function profTone' in s: sys.exit('already patched')
R = [
 ("const profAv = (pk, size, fs) => avL(PROFS[pk] ? PROFS[pk].ini : '?', size, fs);",
  "/* A professor's circle in their rating's colour, by half star: 5.0 green … 0.5 red (Tate, 2026-10-03).\n"
  "   No rating → neutral grey; the colour never stands in for a score that isn't there. */\n"
  "const PROF_HUE = { 10: 150, 9: 118, 8: 90, 7: 68, 6: 50, 5: 38, 4: 26, 3: 14, 2: 2, 1: 340 }, PROF_L = { 10: 78, 1: 80 };\n"
  "function profTone(r) {\n"
  "  if (typeof r !== 'number' || !isFinite(r) || r <= 0) return { bg: '#E6EAF1', ink: '#475569', step: null };\n"
  "  const step = Math.min(10, Math.max(1, Math.round(r * 2))), h = PROF_HUE[step];\n"
  "  return { bg: `hsl(${h} 80% ${PROF_L[step] || 84}%)`, ink: `hsl(${h} 75% 21%)`, step: step / 2 };\n"
  "}\n"
  "const profAv = (pk, size, fs) => {\n"
  "  if (!PROFS[pk]) return avL('?', size, fs);\n"
  "  const t = profTone(ratingOf(pk));\n"
  "  return `<span class=\"av pav-t\" data-step=\"${t.step == null ? '' : t.step}\" aria-hidden=\"true\" style=\"width:${size}px;height:${size}px;background:${t.bg};color:${t.ink};font-size:${fs}px\">${esc(PROFS[pk].ini)}</span>`;\n"
  "};"),
 # the professor page's header circle
 ("<span class=\"av\" style=\"width:70px;height:70px;background:#EDE9FE;color:#3B0764;font-size:22px;box-shadow:0 0 0 3px #fff\">${esc(p.ini)}</span>",
  "${(t => `<span class=\"av pav-t\" data-step=\"${t.step == null ? '' : t.step}\" aria-hidden=\"true\" style=\"width:70px;height:70px;background:${t.bg};color:${t.ink};font-size:22px;box-shadow:0 0 0 3px #fff\">${esc(p.ini)}</span>`)(profTone(ratingOf(id)))}"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
