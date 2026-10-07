#!/usr/bin/env python3
"""Story rings: a friend with no class today is green (Tate, 2026-10-03, on a row where only Garrett
had a ring: "whats happening with the green and not green . have all of these green because everyone
is avaiable. We eventually want to allow people to input work and stuff so keep that in mind").

- status() already called "No classes today" free, but drew no ring, so a friend with no Friday classes
  looked different from one who was done for the day. Now it is green, like every other free state, and
  its line reads in green too.
- "No classes added" stays not-green: TermChamp doesn't know whether they are free, and a green ring
  would say they are. It gets a light grey ring instead (status().rc), so every story has a ring and the
  grey one reads as "unknown". These friends are still last in the row (stories-now-2026-09-30.py).
- busyToday(id) is now the one place that says what fills someone's day. It is their classes today; work
  shifts and other commitments plug in there later, and the rings and the story order follow.

Applies after friends-one-list-2026-10-03.py.
Usage: python3 rings-free-today-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function busyToday' in s: sys.exit('already patched')
R = [
 ("function status(id) {\n  const today = personSecs(id).filter(s => !s.async && s.s != null && s.days.includes(CLOCK.day)).sort((a, b) => a.s - b.s);\n",
  "/* What fills someone's day, in time order. Classes today for now; work shifts and other commitments\n"
  "   plug in here later (Tate, 2026-10-03), and the rings and the story order follow. */\n"
  "function busyToday(id) { return todaySecs(id); }\n"
  "function status(id) {\n  const today = busyToday(id);\n"),
 ("  if (!personSecs(id).length) return { c: null, t: (PEOPLE[id] && (PEOPLE[id].unplaced || []).length) ? 'Class times not added' : 'No classes added', free: null };\n",
  "  if (!personSecs(id).length) return { c: null, rc: '#CBD5E1', t: (PEOPLE[id] && (PEOPLE[id].unplaced || []).length) ? 'Class times not added' : 'No classes added', free: null };\n"),
 ("  return { c: null, t: 'No classes today', free: true };\n",
  "  return { c: '#16A34A', t: 'No classes today', free: true };\n"),
 ("--rc:${(st && st.c) || 'transparent'}", "--rc:${(st && (st.rc || st.c)) || 'transparent'}"),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:80]}')
    s = s.replace(a, b)
a = "--rc:${st.c || 'transparent'}"
if s.count(a) != 2: sys.exit(f'story ring anchors matched {s.count(a)}x')
s = s.replace(a, "--rc:${st.rc || st.c || 'transparent'}")
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
