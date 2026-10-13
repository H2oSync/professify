#!/usr/bin/env python3
"""The second round of synthetic reports (Tate, 2026-10-12: "also add these Not covered yet: Summer terms, minors and
double majors, the "I" grade, and semester-catalog students past their first term"). make-dpr-corpus.py draws all four;
the reader read Summer terms, minors, second majors and later semester students right as it was. What it got wrong:

9. An Incomplete. "I" prints in the grade column, but a title cut short after a Roman numeral ("Career Readiness I") ends
   the same way, so "I" can't simply be a grade. A row is graded "I" only when the term it's in is over — before the
   newest term the report lists (where ungraded classes are the ones being taken) — and it isn't transfer credit or a
   class marked "Course In Progress". Then it's an Incomplete: read, never saved as taken, and like RP (grade pending)
   a class on the account isn't taken off for it. Before, the row read as ungraded in a past term, so the phone saved it
   to Past classes as finished. (Review) A term is over by the report's date (dprTermRunning), never just by being older
   than the newest term listed (October's report lists Spring, registered ahead, while Fall's classes are being taken);
   also when a Cal Poly class in its term or a later one is graded. Never on transfer-shaped rows (AP, TRAN, 1TR) or
   rows whose icon was lost. The phone says "grade pending" for it (and RP), not "not passed".
Edits app/planner.js and index.html (the website's import reader). Replayable on dpr-corpus-fixes-2026-10-12.py.
  python3 dpr-corpus-more-2026-10-12.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
R = [
("""    if(gradeTok==='IP')gradeTok='';   /* (2026-10-12) "IP" in the grade column: in progress */
""", """    if(gradeTok==='IP')gradeTok='';   /* (2026-10-12) "IP" in the grade column: in progress */
    /* (2026-10-12) "I" may be an Incomplete or the end of a title ("… I"): decided below, once the newest term is known */
    var rawI=gradeTok==='I';
"""),
("""      ||!/^\\d{3,4}[A-Z]{0,2}$/.test(nbr);
""", """      ||!/^\\d{3,4}[A-Z]{0,2}$/.test(nbr);
    /* never transfer or exam credit (an "AP … Calculus I" placeholder), never a class marked in progress, never a row whose
       icon was lost (exam credit wears none) */
    var iTok=rawI&&!xfer&&!pmark&&!bmark;
"""),
("""      pick:!already&&!fail, _fail:fail, _prov:gradeTok==='RP',""", """      pick:!already&&!fail, _fail:fail, _prov:gradeTok==='RP', _iTok:iTok,"""),
("""  out.forEach(function(r){ r._now=r._open&&((r.year*10+(ORD[r.term]||0))===latest); });""",
 """  /* (2026-10-12) "I" on a row in a term that's over is an Incomplete: graded, not passed, its grade still pending */
  var incomplete=function(r){ r._open=false; r._now=false; r._fail=true; r._prov=true; r.pick=false; r._title=String(r._title||'').replace(/\\s+I$/,''); if(!r.known)r.name=r._title; };
  /* a term is over when the report's date is past its last weeks (dprTermRunning) — not merely older than the newest
     term listed: in October the report also lists Spring, registered ahead, while Fall's classes are still being taken */
  var pd=dprPrinted(text);
  out.forEach(function(r){ if(r._iTok&&(pd?!dprTermRunning(r.term,r.year,pd):(r.year*10+(ORD[r.term]||0))<latest))incomplete(r); });
  out.forEach(function(r){ r._now=r._open&&((r.year*10+(ORD[r.term]||0))===latest); });"""),
("""  out.forEach(function(r){ if(r._xfer)r._now=false; });""",
 """  out.forEach(function(r){ if(r._xfer)r._now=false; });
  /* (2026-10-12) …and whenever a Cal Poly class in its term or a later one is graded (a report with no date, say) */
  out.forEach(function(r){ if(!r._iTok||!r._open)return; var k=r.year*10+(ORD[r.term]||0); if(out.some(function(o){ return o!==r&&!o._xfer&&!o._open&&!o._fail&&(o.year*10+(ORD[o.term]||0))>=k; }))incomplete(r); });
  out.forEach(function(r){ delete r._iTok; });"""),
]
for f in ('app/planner.js', 'index.html'):
    p = ROOT / f; s = p.read_text()
    for a, b in R:
        if s.count(a) != 1: sys.exit(f'dpr-corpus-more: {f}: expected 1 of {a[:70]!r}, found {s.count(a)}')
        s = s.replace(a, b)
    p.write_text(s)
p = ROOT / 'app/index.html'; s = p.read_text()
a = """    if (x._fail) { x._now = false; x.skip = 'not passed — not a finished class'; x.pick = false; return; }"""
b = """    if (x._fail) { x._now = false; x.skip = x._prov ? 'grade pending — not a finished class' : 'not passed — not a finished class'; x.pick = false; return; }"""
if s.count(a) != 1: sys.exit('dpr-corpus-more: app/index.html: the skip line')
p.write_text(s.replace(a, b))
print('dpr-corpus-more: applied')
