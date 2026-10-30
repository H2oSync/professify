#!/usr/bin/env python3
"""Stress test, 2026-10-30: histNotDone() measured every term against CFG.TERM_ENDS — Fall 2026's last day
(Dec 22). From Jan 25 2027 the term you're in is Spring 2027, Dec 22 is behind us, so every Spring 2027
class_history row read as FINISHED: prerequisites met and "done" for a class you are sitting in.
Each term now has its own last day, by term code (CFG.TERM_END_DATES); TERM_ENDS stays NOW_TERM's and
still wins for that term (so a config or test that moves it still moves it). A term with no known last day
is still on (never "finished" by a guess). Run first; no-class-days and log-class-last-term use nowTermEnd().
Usage: python3 term-ends-by-term-2026-10-30.py app/index.html"""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
if 'term-ends-by-term (2026-10-30)' in s:
    sys.exit('already patched')
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)

one("""  TERM_ENDS: '2026-12-22',
""", """  TERM_ENDS: '2026-12-22',
  /* term-ends-by-term (2026-10-30): each term's last day, by term code — after it the term is finished (grades are in).
     TERM_ENDS above is NOW_TERM's and wins for it. 2274: Spring 2027's last final exam, 'Final exams May 15, 17–21'
     (registrar.calpoly.edu/spring-semester-planning-calendar, as the website's TL_TERMS quotes it).
     TODO: swap in the registrar's 'End of term' row for Spring 2027 once it is read (Fall's, Dec 22, comes after its finals). */
  TERM_END_DATES: { '2268': '2026-12-22', '2274': '2027-05-21' },
""")
one("""/* this term is still on: until its last day (CFG.TERM_ENDS, the registrar's calendar) — after it, grades are in */
function nowTermOn() { return !CFG.TERM_ENDS || sloISO() <= CFG.TERM_ENDS; }""",
"""/* this term is still on: until its last day (the registrar's calendar) — after it, grades are in. term-ends-by-term (2026-10-30):
   the last day of the term you're IN — NOW_TERM's is CFG.TERM_ENDS; any other (Spring 2027 from Jan 25) is its own
   CFG.TERM_END_DATES entry. '' = not known: the term is still on. */
function nowTermEnd() {
  const t = nowTerm(), own = String(CFG.NOW_TERM || CFG.TERM || '').trim();
  if (CFG.TERM_ENDS && String(t.code) === own) return String(CFG.TERM_ENDS);
  return String((CFG.TERM_END_DATES || {})[t.code] || '');
}
function nowTermOn() { const e = nowTermEnd(); return !e || sloISO() <= e; }""")
p.write_text(s); print(p, 'term-ends-by-term: ok')
