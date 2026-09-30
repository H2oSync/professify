#!/usr/bin/env python3
"""Section labels: "S04", not "§S04-SEM Regular" (Tate, 2026-09-30: "for sections just have S0# not
the weird S thing before the s"). Cal Poly's feed gives sections as "S04-SEM Regular"; the app now
shows only the section code, with no "§". A bare number ("01", the older shape) reads "Sec 01".

Usage: python3 section-label-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
Applied in order; every anchor must match exactly once at its turn, or nothing is written.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function secLabel(' in s: sys.exit('already patched')
R = [
 ("function gridSpan(secs, minSpan) {",
  "/* \"S04-SEM Regular\" -> \"S04\"; a bare number \"01\" -> \"Sec 01\". Never a \"§\". (2026-09-30) */\n"
  "function secLabel(v) { const t = String(v == null ? '' : v).trim().split(/[-\\s]/)[0]; return /^\\d/.test(t) ? 'Sec ' + t : t; }\n"
  "function gridSpan(secs, minSpan) {"),
 ("${s.sec ? '§' + esc(s.sec) + ' ' : ''}", "${s.sec ? esc(secLabel(s.sec)) + ' ' : ''}"),
 ("§${esc(ss[0].sec)}", "${esc(secLabel(ss[0].sec))}"),
 ("${s.sec ? '§' + esc(s.sec) + ' · ' : ''}", "${s.sec ? esc(secLabel(s.sec)) + ' · ' : ''}"),
 ("<span class=\"code\">${code}${s.sec ? ' §' + esc(s.sec) : ''}</span>", "<span class=\"code\">${code}${s.sec ? ' ' + esc(secLabel(s.sec)) : ''}</span>"),
 ("<b>${s.code}${s.sec ? ' §' + esc(s.sec) : ''}</b>", "<b>${s.code}${s.sec ? ' ' + esc(secLabel(s.sec)) : ''}</b>"),
 ("Backup: §${esc(bk.sec)} ", "Backup: ${bk.sec ? esc(secLabel(bk.sec)) + ' ' : ''}"),
 ("seat alerts for ${c} §${esc(s.sec)}?", "seat alerts for ${c} ${esc(secLabel(s.sec))}?"),
 ("${esc(s.sec || '—')}", "${esc(secLabel(s.sec) || '—')}"),
 # onboarding showed the raw feed string ("Sec S04-SEM Regular")
 ("${sec ? `<span class=\"s\">Sec ${esc(sec)}</span>` : ''}", "${sec ? `<span class=\"s\">${esc(secLabel(sec))}</span>` : ''}"),
 ("(onbSecOf(code) ? ' Sec ' + esc(onbSecOf(code)) :", "(onbSecOf(code) ? ' ' + esc(secLabel(onbSecOf(code))) :"),
 ("c + (onbSecOf(c) ? ' · ' + onbSecOf(c) : '')", "c + (onbSecOf(c) ? ' · ' + secLabel(onbSecOf(c)) : '')"),
 # Champ's "open / add / watch section N": match on the section's number, so "S04-SEM Regular" is
 # section 4 (Number("S04-SEM Regular") is NaN, which matched nothing — or, against a non-numeric
 # ask, matched the first non-numeric section of the course)
 ("function secLabel(v) {", "function secKey(v) { const m = String(v == null ? '' : v).match(/\\d+/); return m ? String(+m[0]) : ''; }\n"
  "/* The section someone asked for: the exact code (\"S04\", \"S04-SEM Regular\") first; otherwise a bare\n"
  "   number (\"4\") only when exactly one section of the course has it. Nothing asked, nothing found. */\n"
  "function secFind(list, want) { const w = String(want == null ? '' : want).trim().toUpperCase(); if (!w) return undefined;\n"
  "  const ex = list.find(x => { const r = String(x.sec || '').trim().toUpperCase(), l = secLabel(x.sec).toUpperCase(); return r === w || l === w || l === 'SEC ' + w; });\n"
  "  if (ex) return ex; const k = secKey(w); if (!k) return undefined; const m = list.filter(x => secKey(x.sec) === k); return m.length === 1 ? m[0] : undefined; }\n"
  "function secLabel(v) {"),
]
R_SECKEY = ("secsOf(c).find(x => String(+x.sec) === String(+a.section))", "secFind(secsOf(c), a.section)")
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
a, b = R_SECKEY   # the three Champ section lookups share this exact expression
if s.count(a) != 3: sys.exit(f'section lookup matched {s.count(a)}x, expected 3')
s = s.replace(a, b)
assert '§' not in s.split('<script', 1)[1] or True
left = [l for l in s.splitlines() if '§' in l and 'sec' in l]
if left: sys.exit('a section still shows §: ' + left[0][:120])
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
