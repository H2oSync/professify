#!/usr/bin/env python3
"""Ratings: the star and number take the rating's colour (green / yellow / red), and counts read
"42 ratings" instead of "42 PolyRatings evaluations". (Tate, 2026-09-30: "for the stars have it the
color that matches like green, yellow, red. also dont have it say poly ratings just have it say #
ratings.")

Cut-offs are the desktop's scoreColor(): PolyRatings >= 3.3 of 4 is green, >= 2.5 is yellow, else red
(4.13 and 3.13 on the app's 5-point scale). The professor page keeps its one source line ("Overall
rating from PolyRatings … Read their reviews") because that is where the number comes from.

Usage: python3 rating-colors-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
Applied in order; every anchor must match exactly once at its turn, or nothing is written.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'const rateTone' in s: sys.exit('already patched')
R = [
 ("const ratingOf = pk => (pk && PROFS[pk] && typeof PROFS[pk].r === 'number') ? PROFS[pk].r : null;",
  "const ratingOf = pk => (pk && PROFS[pk] && typeof PROFS[pk].r === 'number') ? PROFS[pk].r : null;\n"
  "/* A rating's colour, on the desktop's scoreColor() cut-offs: PolyRatings 3.3+ of 4 green, 2.5+ yellow,\n"
  "   below that red (2026-09-30). r is on the app's 5-point scale. */\n"
  "const rateTone = r => r == null ? null : r * 0.8 >= 3.3 - 1e-9 ? { k: 'good', star: '#16A34A', ink: '#166534', bg: '#DCFCE7' }\n"
  "  : r * 0.8 >= 2.5 - 1e-9 ? { k: 'mid', star: '#D97706', ink: '#92400E', bg: '#FEF3C7' } : { k: 'low', star: '#DC2626', ink: '#B91C1C', bg: '#FEE2E2' };\n"
  "const nRatings = n => `${n} rating${n === 1 ? '' : 's'}`;"),
 # Explore professor cards
 ("const line = [p.count ? `${p.count} PolyRatings evaluation${p.count === 1 ? '' : 's'}` : (r == null ? 'Not on PolyRatings' : ''),",
  "const line = [p.count ? nRatings(p.count) : (r == null && !st ? 'No ratings yet' : ''),"),
 ("${r != null ? `<span class=\"rchip\">${starI(13)} ${r.toFixed(1)}</span>` : ''}",
  "${r != null ? `<span class=\"rchip rt-${rateTone(r).k}\" style=\"background:${rateTone(r).bg};color:${rateTone(r).ink}\">${starI(13, rateTone(r).star)} ${r.toFixed(1)}</span>` : ''}"),
 # class page professor rows
 ("${ratingOf(pid) != null ? starI(13, '#D97706') + ratingOf(pid).toFixed(1) + `<span class=\"muted\" style=\"font-weight:700\">&nbsp;· ${PROFS[pid].count} eval${PROFS[pid].count === 1 ? '' : 's'}</span>` : '<span class=\"muted\">Not on PolyRatings</span>'}",
  "${ratingOf(pid) != null ? starI(13, rateTone(ratingOf(pid)).star) + `<span class=\"rt-${rateTone(ratingOf(pid)).k}\" style=\"color:${rateTone(ratingOf(pid)).ink}\">${ratingOf(pid).toFixed(1)}</span>` + `<span class=\"muted\" style=\"font-weight:700\">&nbsp;· ${nRatings(PROFS[pid].count)}</span>` : '<span class=\"muted\">No ratings yet</span>'}"),
 # professor page
 ("<div class=\"stat\"><small>POLYRATINGS</small><b>${r != null ? '★ ' + r.toFixed(1) : '—'}</b></div><div class=\"stat\"><small>EVALUATIONS</small><b>${p.count || '—'}</b></div>",
  "<div class=\"stat\"><small>AVERAGE</small><b>${r != null ? '★ ' + r.toFixed(1) : '—'}</b></div><div class=\"stat\"><small>RATINGS</small><b>${p.count || '—'}</b></div>"),
 ("<div style=\"text-align:center;width:80px\"><div style=\"font-size:44px;font-weight:1000;line-height:1\">${r.toFixed(1)}</div><div class=\"muted b\" style=\"font-size:12.5px;margin-top:4px\">${p.count} on PolyRatings</div>",
  "<div style=\"text-align:center;min-width:80px\"><div class=\"rt-${rateTone(r).k}\" style=\"font-size:44px;font-weight:1000;line-height:1;color:${rateTone(r).ink};display:flex;align-items:center;justify-content:center;gap:4px\">${starI(24, rateTone(r).star)}${r.toFixed(1)}</div><div class=\"muted b\" style=\"font-size:12.5px;margin-top:4px\">${nRatings(p.count)}</div>"),
 # a PolyRatings entry with no evaluations has no rating (it would read as a red 0.0)
 ("P.r = Math.round((+p.overallRating / 4 * 5) * 100) / 100; P.count = p.numEvals || 0;",
  "P.r = +p.numEvals === 0 || !isFinite(+p.overallRating) ? null : Math.round((+p.overallRating / 4 * 5) * 100) / 100; P.count = p.numEvals || 0;"),
 ("None of the ${code} professors ${ps.length ? 'are on PolyRatings yet' : 'have been assigned yet'}",
  "None of the ${code} professors ${ps.length ? 'have ratings yet' : 'have been assigned yet'}"),
 # Champ's professor line
 ("★${ratingOf(pk).toFixed(1)} from ${PROFS[pk].count} PolyRatings` : 'not on PolyRatings'}",
  "★${ratingOf(pk).toFixed(1)} from ${nRatings(PROFS[pk].count)}` : 'no ratings yet'}"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
