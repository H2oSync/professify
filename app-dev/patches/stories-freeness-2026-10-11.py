#!/usr/bin/env python3
"""Stories, most free furthest left (Tate, 2026-10-11): "people without classes on that day are the furthest left,
then people that have no more classes that day next freest, then people that have the furthest away class for that
day, then people soonest to get out of class, for people that havent set up their schedules yet like dydaniel and
iander15 have them always be the furthest to the right because you cant be sure of there schedule yet".
Asked: "not set up" = no class with a set time this term (none added, only online / no-time classes, or classes
without a section) — they get the grey ring and are never called free. Pinned friends stay first.
Edits app/index.html: status() and storyRank()."""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
R = [
("""  if (!nowSecs(id).length) return { c: null, rc: isDark() ? '#3A4660' : '#CBD5E1', t: nowUnplaced(id).length ? 'Class times not added' : 'No classes added', free: null };""",
 """  /* no class with a set time (none added, only online / no-time classes, or no section yet): TermChamp can't know their
     day, so never "free" (stories-freeness, 2026-10-11). Same test as Champ's chTimed. When work shifts plug into
     busyToday, a shift should count as a set time here too. */
  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return { c: null, rc: isDark() ? '#3A4660' : '#CBD5E1', t: nowSecs(id).length || nowUnplaced(id).length ? 'Class times not added' : 'No classes added', free: null };"""),
("""/* [group, key]: 0 free now (longest free stretch first); 1 busy — in a class, or about to start one —
   by when they're next free, soonest first (a class straight after another counts as the same busy
   stretch); 2 no classes added. */
function storyRank(id) {
  const st = status(id), now = CLOCK.min, today = busyToday(id);
  if (st.free === null) return [2, 0];
  const inc = today.find(x => x.s <= now && now < x.e), nx = today.find(x => x.s > now);
  if (st.free && !inc) return [0, -(nx ? nx.s - now : 1e6)];
  let t = inc ? inc.e : nx ? nx.e : now;
  today.forEach(x => { if (x.e > t && x.s <= t + 10) t = x.e; });
  return [1, t];
}""",
 """/* [group, key], most free first (Tate, 2026-10-11): 0 no classes today; 1 done for the day; 2 not in class, a class
   later today — the furthest-off class first; 3 in class — out soonest first (a class straight after another is the
   same stretch); 4 schedule not set up (no class with a set time) — always last. Ties by name. */
function storyRank(id) {
  const st = status(id), now = CLOCK.min, today = busyToday(id);
  if (st.free === null) return [4, 0];
  if (!today.length) return [0, 0];
  const inc = today.find(x => x.s <= now && now < x.e), nx = today.find(x => x.s > now);
  if (!inc && !nx) return [1, 0];
  if (!inc) return [2, -(nx.s - now)];
  let t = inc.e;
  today.forEach(x => { if (x.e > t && x.s <= t + 10) t = x.e; });
  return [3, t];
}"""),
]
for a, b in R:
    c = s.count(a)
    if c != 1: sys.exit(f'stories-freeness: expected 1 of {a[:70]!r}, found {c}')
    s = s.replace(a, b)
p.write_text(s)
print('stories-freeness: status() and storyRank()')
