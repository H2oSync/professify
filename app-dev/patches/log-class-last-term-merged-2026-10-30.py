#!/usr/bin/env python3
"""Merge of log-class-last-term (dates) onto quick-log-term (mine), 2026-10-30. quick-log-term's lcDefault() said
"Winter <year>" when the term you're in is Spring — from Spring 2027 a term Cal Poly no longer has. lcDefault() now
returns lastDoneTerm(): the term you're in once it has ended (nowTermOn(), from term-ends-by-term), otherwise the regular
term before it; Summer is never the guess. Winter 2027 or later is refused on "Log a class" and on a past class's
"When did you take it?". Run after quick-log-term-2026-10-30.py and term-ends-by-term-2026-10-30.py."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
assert 'function nowTermEnd()' in s and 'function lcDefault()' in s
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""function lcDefault() {
  const m = String(nowTerm().label || '').match(/(Winter|Spring|Summer|Fall)\\s+(\\d{4})/);
  if (!m) return { term: 'Spring', year: new Date().getFullYear() };
  const t = m[1], y = +m[2];
  return t === 'Fall' ? { term: 'Spring', year: y } : t === 'Winter' ? { term: 'Fall', year: y - 1 } : t === 'Spring' ? { term: 'Winter', year: y } : { term: 'Spring', year: y };
}""", """function lcDefault() { return lastDoneTerm(); }
/* log-class-last-term (2026-10-30): the newest term that's over. The term you're in once it has ended; until then the
   regular term before it (semesters from Fall 2026: Fall, Spring; the quarters before them had Winter). Summer is never
   the guess. */
function lastDoneTerm() {
  const [t, y0] = String(nowTerm().label || '').split(' '), y = +y0;
  if (!y || !HT_ORD[t]) { const d = new Date(), late = d.getMonth() >= 6; return { term: late ? 'Spring' : 'Fall', year: late ? d.getFullYear() : d.getFullYear() - 1 }; }
  if (!nowTermOn()) return { term: t, year: y };
  if (t === 'Fall' || t === 'Summer') return { term: 'Spring', year: y };
  if (t === 'Spring') return y <= 2026 ? { term: 'Winter', year: y } : { term: 'Fall', year: y - 1 };
  return { term: 'Fall', year: y - 1 };
}
/* Cal Poly has had no Winter term since semesters began (Fall 2026) */
const noWinter = (t, y) => t === 'Winter' && +y >= 2027;
const NO_WINTER_SAY = 'Cal Poly has no Winter term from 2027 — semesters are Fall, Spring and Summer.';""")
one("""    if (!code) { UI.lc.err = 'Enter a class code like BUS 3431.'; return render(true); }
    UI.busy.lc = 1; render(true);""", """    if (!code) { UI.lc.err = 'Enter a class code like BUS 3431.'; return render(true); }
    if (noWinter(term, year)) { UI.lc.err = NO_WINTER_SAY; return render(true); }
    UI.busy.lc = 1; render(true);""")
one("""    if (!term || !year) { sh.err = 'Choose the term and the year.'; return render(true); }
    UI.busy.pct = 1; render(true);""", """    if (!term || !year) { sh.err = 'Choose the term and the year.'; return render(true); }
    if (noWinter(term, year)) { sh.err = NO_WINTER_SAY; return render(true); }
    UI.busy.pct = 1; render(true);""")
p.write_text(s); print(p, 'log-class-last-term (merged): ok')
