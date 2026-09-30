#!/usr/bin/env python3
"""Home week cards: classes that don't sit on a time slot get a row below the week (Tate, 2026-09-30:
"lets find a place to put asynch classes and projects that dont sit on a time slot we should put them
below the main schedule").

Before: a section with no meeting time — online/self-paced, or one whose time isn't posted (senior
projects, supervision) — was filtered out of the grid and appeared nowhere on the card. A class saved
with no section showed as a grey "No times yet for …" line.
Now one "No set time" row under the week holds all of them as chips, styled like the grid's blocks:
  - online / self-paced sections: code + "Online"; tap opens the section preview, as a block does;
  - sections whose time isn't posted: the code; tap opens the section preview;
  - a section that meets only on a weekend (the week has no column for it): code + its days;
  - when the same class is also drawn on the week (a timed lecture, an online lab), the chip adds the
    section ("S02") so the two can be told apart;
  - classes saved with no section: code + "No section"; tap opens the class (there's no section to preview).
A class you share gets the same yellow ring as on the grid. A card with no timed classes at all shows
just the row (was the grey "No set times for …" line), never an empty grid.

Applies after grid-text-fill-2026-09-30.py.
Usage: python3 home-no-set-time-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="anyrow"' in s: sys.exit('already patched')
R = [
 ("  let week;\n  if (isMe && !TC.ready && !TC.mineRows) week = loadingCard('Loading your week…');",
  "  /* Classes with no time slot sit in one row under the week (Tate, 2026-09-30). */\n"
  "  /* On the week = a start, an end and a weekday column to draw it in (a Saturday-only section has no column). */\n"
  "  const onGrid = s => !s.async && s.s != null && s.e != null && [...s.days].some(d => DAYS.includes(d)), drawn = new Set(secs.filter(onGrid).map(s => s.code));\n"
  "  const untimed = secs.filter(s => !onGrid(s)), loose = unplaced.filter(c => !secs.some(s => s.code === c));\n"
  "  /* what the chip can truthfully add: online; a weekend day; the section, when the same class is also on the week */\n"
  "  const note = s => [s.async ? 'Online' : '', !s.async && s.s != null && s.days ? daysLabel(s.days) : '', drawn.has(s.code) && s.sec ? secLabel(s.sec) : ''].filter(Boolean).join(' · ');\n"
  "  const ring = c => !isMe && mine.has(c) ? ' shared' : '';\n"
  "  const anyRow = untimed.length || loose.length ? `<div class=\"anyrow\"><span class=\"any-h\">No set time</span>${untimed.map(s => `<button class=\"any-c${ring(s.code)}\" data-a=\"secSheet\" data-x=\"${esc(s.code)}\" data-y=\"${esc(s.id)}\" title=\"${esc(s.code + ' · ' + secWhen(s))}\"><b>${esc(s.code)}</b>${note(s) ? `<small>${esc(note(s))}</small>` : ''}</button>`).join('')}${loose.map(c => `<button class=\"any-c${ring(c)}\" data-a=\"openClass\" data-x=\"${esc(c)}\"><b>${esc(c)}</b><small>No section</small></button>`).join('')}</div>` : '';\n"
  "  let week;\n  if (isMe && !TC.ready && !TC.mineRows) week = loadingCard('Loading your week…');"),
 ("  else if (!secs.some(s => !s.async && s.s != null && s.e != null)) week = `<div class=\"foot\">No set times for ${[...new Set(secs.map(s => s.code).concat(unplaced))].map(esc).join(', ')}</div>`;\n",
  "  else if (!secs.some(onGrid)) week = anyRow;\n"),
 (" shared, one: true, fit: 30, H: 300 }) + (unplaced.length ? `<div class=\"foot\">No times yet for ${unplaced.map(esc).join(', ')}</div>` : '');\n",
  " shared, one: true, fit: 30, H: 300 }) + anyRow;\n"),
 (".foot{padding:12px 18px 0;color:var(--muted);font-weight:800;font-size:14px}\n",
  ".foot{padding:12px 18px 0;color:var(--muted);font-weight:800;font-size:14px}\n"
  "/* the \"No set time\" row under a Home week: online sections, unposted times, classes with no section */\n"
  ".anyrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:12px 16px 0}\n"
  ".homepg .fcard .anyrow{padding:10px 8px 0}\n"
  ".any-h{font-size:11px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-right:2px}\n"
  ".any-c{display:inline-flex;align-items:center;gap:5px;min-height:42px;padding:8px 11px;border-radius:8px;background:var(--blue-soft2);color:var(--blue-ink);font-size:13px;font-weight:900;letter-spacing:.02em;white-space:nowrap}\n"
  ".any-c small{font-size:11px;font-weight:700;opacity:.8;letter-spacing:0}\n"
  ".any-c.shared{box-shadow:0 0 0 2.5px var(--yellow)}\n"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:70]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
