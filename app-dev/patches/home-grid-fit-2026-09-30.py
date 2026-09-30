#!/usr/bin/env python3
"""Home week cards: sized to the hours the classes fill, and each card's day picker on its own.
(Tate, 2026-09-30: "make it not as big. make it only as large as the time and friends fill in.
also have each one work independently so if i click Monday it doesn't click everything.")

Usage: python3 home-grid-fit-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html in place)
Every anchor must match exactly once, or nothing is written. Re-running on a patched file is refused.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'homeDays' in s: sys.exit('already patched')
R = [
 # 1. the axis can be shorter than six hours when a grid asks for it (min span in minutes)
 ("function gridSpan(secs) {", "function gridSpan(secs, minSpan) {"),
 ("  if (b - a < 360) { b = Math.min(a + 360, 1440); a = b - 360; }",
  "  const m = minSpan || 360;   /* fitted grids (Home cards) go down to three hours */\n  if (b - a < m) { b = Math.min(a + m, 1440); a = b - m; }"),
 # 2. o.fit = pixels per hour: the body is exactly as tall as the hours the classes cover
 ("  const [S0, S1] = gridSpan(secs);\n  const has = d =>",
  "  const [S0, S1] = gridSpan(secs, o.fit ? 180 : 360);\n  const has = d =>"),
 ("  const H = dur.length ? Math.min(900, Math.max(o.H || 320, Math.ceil(need * (S1 - S0) / Math.min(...dur)))) : (o.H || 320);",
  "  /* o.fit (px per hour) sizes the body to the hours the classes fill, never taller than o.H (a long\n     day squeezes instead of growing); otherwise a fixed height. */\n  const base = o.fit ? Math.min(o.H || 300, Math.round((S1 - S0) / 60 * o.fit)) : (o.H || 320);\n  const H = dur.length ? Math.min(900, Math.max(base, Math.ceil(need * (S1 - S0) / Math.min(...dur)))) : base;"),
 # unfocused blocks in a fitted grid: 26px minimum (two lines of code) so hourly classes keep a gap,
 # and a block never hangs past the bottom of the body
 ("      const top = Math.max(0, (s.s - S0) * k), h = Math.max((s.e - s.s) * k, wide ? (faces ? 52 : 34) : (o.one ? 30 : 24));",
  "      const h = Math.max((s.e - s.s) * k, wide ? (faces ? 52 : 34) : o.fit ? 26 : (o.one ? 30 : 24));\n      const top = Math.max(0, Math.min((s.s - S0) * k, H - h));"),
 # 3. o.key: which grid a day tap belongs to, so one card's day never opens another's
 ("data-a=\"${o.act}\" data-x=\"${d}\" aria-pressed=\"${d === focus}\">",
  "data-a=\"${o.act}\" data-x=\"${d}\"${o.key != null ? ` data-y=\"${esc(o.key)}\"` : ''} aria-pressed=\"${d === focus}\">"),
 ("    homeDay: null,\n", "    homeDay: null, homeDays: {},   /* focused day per grid, keyed by o.key (2026-09-30) */\n"),
 ("  homeDay: d => { S.homeDay = S.homeDay === d ? null : d; render(true); },",
  "  homeDay: (d, key) => { const k = key || '_'; S.homeDays[k] = S.homeDays[k] === d ? null : d; render(true); },"),
 # a card whose classes have no set times draws no empty grid, just the list of them
 ("  else week = grid(secs, { sel: S.homeDay,",
  "  else if (!secs.some(s => !s.async && s.s != null && s.e != null)) week = `<div class=\"foot\">No set times for ${[...new Set(secs.map(s => s.code).concat(unplaced))].map(esc).join(', ')}</div>`;\n  else week = grid(secs, { sel: S.homeDay,"),
 ("grid(secs, { sel: S.homeDay, act: 'homeDay', shared: both, one: true, H: 260 })",
  "grid(secs, { sel: S.homeDays['plan:' + id + ':' + k], act: 'homeDay', key: 'plan:' + id + ':' + k, shared: both, one: true, H: 260 })"),
 ("grid(secs, { sel: S.homeDay, act: 'homeDay', shared, one: true, H: 280 })",
  "grid(secs, { sel: S.homeDays['f:' + id], act: 'homeDay', key: 'f:' + id, shared, one: true, H: 280 })"),
 # 4. the three grids that used the shared S.homeDay
 ("grid(secs, { sel: S.homeDay, act: 'homeDay', shared, one: true, H: 300 })",
  "grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, shared, one: true, fit: 30, H: 300 })"),
]
for a, b in R:   # applied in order; each anchor must match exactly once at its turn
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:80]}')
    s = s.replace(a, b)
assert 'sel: S.homeDay,' not in s and 'sel: S.homeDay ' not in s, 'a grid still uses the shared homeDay'
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
