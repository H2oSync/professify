#!/usr/bin/env python3
r"""Quarter-catalog GE, checked against the registrar's own sheet (Tate, 2026-10-11, uploaded "Staying on QUARTER
Catalog: GE Pattern Guidelines" — "For Quarter Catalog Students: Taking Semester Courses", 2022–2026 quarter catalog
requirements). Run AFTER dpr-truth-app-2026-10-11.py.

The sheet confirms the table plGeArea already used (A1→1C, A2→1A, A3→1B, B1→5A, B2→5B, B3→5C embedded in a 5A or 5B,
B4→2, Upper-Division B→UD 2 or UD 5, C1→3A, C2→3B, Upper-Division C→UD 3, D1→4A, D2→4B, Upper-Division D→UD 4,
Area E→a 4B course taken Fall 2026 or later ("Quarter D2 courses will not apply"), F→6) and differs in three places:
  1. "GE Elective: Area B, C or D" → "Any additional Area 2, 3, 4 or 5 … may be lower or upper division": the
     upper-division areas (UD 2/5, UD 3, UD 4) count too. plGeArea had lower-division only.
  2. "Area B Electives" (the high-unit template: ARCE, BRAE and the College of Engineering) → "Select Courses from
     5A–5C". plGeArea had no rule, so such a line got no picks.
  3. "All three lower division C courses must come from three different course prefixes": the Lower-Division C
     Elective is "any 3A or 3B in a different subject". A class whose subject is one the report already used for C1,
     C2 or the elective itself is never picked for it, and never counts it as in progress.
Rules the app still can't check, and so never claims (the report decides): the standard template's D1 / D2 / D UD
from at least two prefixes, and the second GE Elective from a different area than the first.

Usage: python3 quarter-ge-guidelines-2026-10-11.py <repo-dir>      Replayable: every anchor must match once."""
import sys, os
D = sys.argv[1]
PA = os.path.join(D, 'app', 'index.html')
S = open(PA, encoding='utf-8').read()

def rep(a, b, label):
    global S
    n = S.count(a)
    if n != 1: sys.exit(f'app {label}: anchor matched {n}x')
    S = S.replace(a, b)

rep("""/* (2026-10-11) A report line's GE area(s) in the app's semester vocabulary. The registrar's table
   (registrar.calpoly.edu/GE_2026):""", """/* (2026-10-11) A report line's GE area(s) in the app's semester vocabulary. The registrar's sheet "Staying on QUARTER
   Catalog: GE Pattern Guidelines" (For Quarter Catalog Students: Taking Semester Courses) and its GE 2026 page:""", 'comment')
rep("""  if (/^Lower[- ]division C Elective\\b/i.test(l)) return ['3A', '3B'];
  if (/^Electives?\\b.*\\bAreas? B, C,? and D\\b/i.test(l)) return ['2', '5A', '5B', '5C', '3A', '3B', '4A', '4B'];""",
    """  if (/^Lower[- ]division C Elective\\b/i.test(l)) return ['3A', '3B'];
  /* "GE Elective: Area B, C or D" → "any additional Area 2, 3, 4 or 5 … may be lower or upper division" (the sheet) */
  if (/^Electives?\\b.*\\bAreas? B, C,? and D\\b/i.test(l)) return ['2', '5A', '5B', '5C', '3A', '3B', '4A', '4B', 'U25', 'UD3', 'UD4'];
  /* the high-unit template's "Area B Electives" (ARCE, BRAE, College of Engineering) → "select courses from 5A–5C" */
  if (/^(?:Area\\s+)?B\\s+Electives?\\b/i.test(l)) return ['5A', '5B', '5C'];""", 'electives')
rep("""/* (2026-10-11) What a new report changes against the one on the account:""",
    """/* (2026-10-11, the registrar's quarter GE sheet) "All three lower division C courses must come from three different
   course prefixes": a class whose subject the report already used for C1, C2 or the elective itself never counts for
   the Lower-Division C Elective. true = barred. */
const geSubj = c => String(c || '').trim().split(/\\s+/)[0].toUpperCase();
function plGeBar(b, code, reqs) {
  if (!b || !/^(?:GE\\s+)?Lower[- ]division C Elective\\b/i.test(String(b.label || ''))) return false;
  const used = new Set();
  (reqs || (TC.audit && TC.audit.reqs) || []).forEach(x => { if (x === b || /^(C1|C2)$/.test(x.ge || '') || /^(?:GE\\s+)?C[12]\\s*:/i.test(String(x.label || ''))) (x.used || []).forEach(e => { used.add(geSubj(e.c)); if (e.n) used.add(geSubj(e.n)); }); });
  return used.has(geSubj(code));
}
/* (2026-10-11) What a new report changes against the one on the account:""", 'bar-fn')
rep("""by = mine.find(c => !placed.has(k(c)) && !spent.has(k(c)) && (GE.get(k(c)) || []).some(a => areas.includes(a)));""",
    """by = mine.find(c => !placed.has(k(c)) && !spent.has(k(c)) && !plGeBar(b, c, a.reqs) && (GE.get(k(c)) || []).some(a => areas.includes(a)));""", 'bar-cover')
rep("""      geOf(code).forEach(a => { (byArea[a] || []).forEach(b => { if (!fills.includes(b)) fills.push(b); }); if (!geA.includes(a) && byArea[a]) geA.push(a); });""",
    """      geOf(code).forEach(a => { const ok = (byArea[a] || []).filter(b => !plGeBar(b, code)); ok.forEach(b => { if (!fills.includes(b)) fills.push(b); }); if (!geA.includes(a) && ok.length) geA.push(a); });""", 'bar-picks')

open(PA, 'w', encoding='utf-8').write(S)
print('quarter-ge-guidelines: done')
