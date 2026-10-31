#!/usr/bin/env python3
"""Scale (2026-10-30): slo() — the day and minute in San Luis Obispo — built a new Intl.DateTimeFormat on every
call, and CLOCK.day / CLOCK.min call it for every class of every friend (todaySecs, status): 1,376 formatters
per Home render with 150 friends, most of the render's script time. Formatters are now made once and kept
(dtf(), keyed by locale + options), and slo() is worked out once per minute: its answer is a function of the
whole minute (every time zone's offset is whole minutes), so a cached answer is never stale.
sloYmd0() and sloISO() use the kept formatters too.
Usage: python3 scale-clock-cache-2026-10-30.py app/index.html"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90]); s = s.replace(old, new)

one("""function sloYmd0() {
  try { const p = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())""",
"""/* One Intl.DateTimeFormat per locale + options, kept: making one is slow (scale, 2026-10-30) */
function dtf(loc, o) { const c = dtf.c || (dtf.c = new Map()), k = loc + '|' + JSON.stringify(o); let f = c.get(k); if (!f) { f = new Intl.DateTimeFormat(loc, o); c.set(k, f); } return f; }
function sloYmd0() {
  try { const p = {}; dtf('en-US', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())""")
one("""function sloISO() { try { return new Intl.DateTimeFormat('en-CA', {""",
"""function sloISO() { try { return dtf('en-CA', {""")
one("""function slo() {
  try {
    const p = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', weekday: 'short', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }).formatToParts(new Date()).forEach(x => { p[x.type] = x.value; });
    return { wd: p.weekday, min: (+p.hour % 24) * 60 + (+p.minute) };
  } catch (e) { const d = new Date(); return { wd: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getDay()], min: d.getHours() * 60 + d.getMinutes() }; }
}""",
"""function slo() {
  const k = Math.floor(Date.now() / 60000); if (slo.k === k && slo.v) return slo.v;   /* once a minute: a render asks ~1,400 times */
  slo.k = k; return (slo.v = slo0());
}
function slo0() {
  try {
    const p = {}; dtf('en-US', { timeZone: 'America/Los_Angeles', weekday: 'short', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }).formatToParts(new Date()).forEach(x => { p[x.type] = x.value; });
    return { wd: p.weekday, min: (+p.hour % 24) * 60 + (+p.minute) };
  } catch (e) { const d = new Date(); return { wd: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getDay()], min: d.getHours() * 60 + d.getMinutes() }; }
}""")
open(p, 'w', encoding='utf-8').write(s); print(p, 'clock: formatters kept, slo() once a minute')
