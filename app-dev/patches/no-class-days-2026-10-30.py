#!/usr/bin/env python3
"""Stress test, 2026-10-30: status() and busyToday() knew the weekday and nothing else, so on Veterans Day, in
finals and all through winter break (Fall's last day is Dec 22, Spring starts Jan 25) every friend's ring read
"In BUS 3438 till 11:00". Now a day Cal Poly holds no classes (CFG.NO_CLASS_DAYS), and any day after the term
you're in has ended (nowTermEnd(), from term-ends-by-term), has no classes in it: todaySecs() is empty, so
busyToday(), the story's day and Champ's "free now" follow; and status() says what the day is ("Veterans Day",
"Finals week", "Spring break", "Winter break") with a grey ring — not "free", not in class. Work and practice
still count on those days. Run after term-ends-by-term-2026-10-30.py.
Only dates the repo cites are listed; the rest are a TODO in the config, never guessed.
Usage: python3 no-class-days-2026-10-30.py app/index.html"""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
if 'no-class-days (2026-10-30)' in s:
    sys.exit('already patched')
assert 'function nowTermEnd()' in s, 'run term-ends-by-term-2026-10-30.py first'
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)

one("""  TERM_END_DATES: { '2268': '2026-12-22', '2274': '2027-05-21' },
""", """  TERM_END_DATES: { '2268': '2026-12-22', '2274': '2027-05-21' },
  /* no-class-days (2026-10-30): Pacific days Cal Poly holds no classes, and what a friend's ring says on them. Only dates
     the repo cites: Veterans Day (the website's TL_TERMS r2skip; oct5-to-registration-plan-2026-09-21.md), Spring 2027's
     break and finals (registrar.calpoly.edu/spring-semester-planning-calendar, as TL_TERMS quotes them). Winter and
     summer break need no row: after the term you're in ends (TERM_ENDS / TERM_END_DATES) nobody is in its classes.
     TODO — not in the repo, add from registrar.calpoly.edu/academic-calendar, never guess: Fall 2026 Thanksgiving
     break; Fall 2026 final exams week (before Dec 22); Spring 2027 Cesar Chavez Day; any other campus holiday. */
  NO_CLASS_DAYS: [
    { from: '2026-11-11', to: '2026-11-11', t: 'Veterans Day' },
    { from: '2027-03-15', to: '2027-03-21', t: 'Spring break' },
    { from: '2027-05-15', to: '2027-05-21', t: 'Finals week' }
  ],
""")
one("""function todaySecs(id) { return nowSecs(id).filter(""",
"""/* no-class-days (2026-10-30): a day with no classes — a holiday, a break, finals, or after the term you're in ended.
   { t: what the day is } or null. d: 'YYYY-MM-DD' (Pacific), today when left out (sloYmd: worked out once a minute). */
function noClassDay(d) {
  d = d || sloYmd();
  const x = (Array.isArray(CFG.NO_CLASS_DAYS) ? CFG.NO_CLASS_DAYS : []).find(r => r && r.from && r.from <= d && d <= (r.to || r.from));
  if (x) return { t: String(x.t || 'No classes today') };
  const e = nowTermEnd();
  if (e && d > e) { const n = String(nowTerm().label || ''); return { t: /^Fall\\b/.test(n) ? 'Winter break' : /^Spring\\b/.test(n) ? 'Summer break' : 'Break' }; }
  return null;
}
function todaySecs(id) { if (noClassDay()) return []; return nowSecs(id).filter(""")
one("""  const inc = today.find(s => s.s <= now && now < s.e);
  if (inc && inc.busy) return""", """  const inc = today.find(s => s.s <= now && now < s.e);
  /* no-class-days (2026-10-30): no classes today (busyToday has none): say what the day is, grey — unless work or practice is on now */
  const off = noClassDay();
  if (off && !inc) return { c: isDark() ? '#8F9BAE' : '#64748B', rc: isDark() ? '#3A4660' : '#CBD5E1', t: off.t, free: null, off: true };
  if (inc && inc.busy) return""")
p.write_text(s); print(p, 'no-class-days: ok')
