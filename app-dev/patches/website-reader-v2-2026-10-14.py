#!/usr/bin/env python3
"""The website gets the phone's reader v2 (Tate, 2026-10-14: "catch the website up to the level the app is").

The phone has read the Degree Progress Report's OWN verdicts since 2026-10-08 (`dpr-flow`, `dpr-truth-2026-10-11`):
every requirement line with the registrar's Satisfied / Not Satisfied / In Progress, its code, units, the classes the
report used for it (code + term only — never a grade, title or unit count of a class), the options of a "1 of N"
line, the classes it lists but didn't count. The website's reader stopped at the Course History rows and judged
everyone against the 2026-28 semester flowchart — wrong for every quarter-catalog student.

This lifts the phone's block (`app/planner.js` between "Reader v2" and PDFJS_BASE) into `index.html` verbatim, and
gives the website's `dprParse` the phone's tail: `_pass` on a row, the classes being taken, the history map, and
`audit` on the result (with the report's catalog and printed date). `app-dev/source/build.py` declares index.html
the source planner.js is lifted from; after this they agree again on the reader.

Checked by app-dev/tests/check-dpr-synth-web.mjs against the 300 synthetic reports.
Usage: python3 website-reader-v2-2026-10-14.py <repo>
"""
import sys, pathlib, re
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-reader-v2 (2026-10-14)' in s:
    sys.exit('already patched')
pl = (root / 'app' / 'planner.js').read_text()

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# the phone's reader v2 block, verbatim
a = pl.index("/* ---- Reader v2 (2026-10-08): the report's OWN verdicts, requirement by requirement")
b = pl.index("var PDFJS_BASE=", a)
block = pl[a:b].rstrip() + "\n"
assert 'function dprAudit(text, cross, taking, hist)' in block and block.count('function dprAudit(') == 1
assert 'dprAudit' not in s

# 1. the row knows whether its grade passed
one("""      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units, _post:postable, _cp:cmark,""",
    """      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units, _post:postable, _cp:cmark, _pass:!!gradeTok&&/^(?:[A-D][+-]?|CR|P|333|[1-7]00)$/.test(gradeTok),""")

# 2. the tail: classes being taken, the history map, the audit
one("""  return {ok:true, rows:out, program:prog, skipped:skipped,""",
    """  /* website-reader-v2 (2026-10-14): the phone's tail. The classes being taken for the audit are the ungraded rows in
     a term after the last graded one (this term, or one registered ahead) — the audit's own notion, independent of
     the two-term `_now/_reg` filing above. Posted credit says nothing about which terms are over. */
  var lastGraded=0; out.forEach(function(r){ if(!r._open&&!r._xfer){ var v=r.year*10+(ORD[r.term]||0); if(v>lastGraded)lastGraded=v; } });
  var taking=[]; out.forEach(function(r){ if(r._open&&!r._xfer&&(r.year*10+(ORD[r.term]||0))>lastGraded){ var w='|'+r.term+' '+r.year; if(r.code)taking.push(r.code+w); if(r.cur)taking.push(r.cur+w); } });
  /* what each Course History row is — today's number, transfer credit, no grade yet, a credit grade — for the
     "Courses Used" rows under each requirement. Never the grade. */
  var hist={}; out.forEach(function(r){ hist[r.code+'|'+r.term+' '+r.year]={cur:r.cur,x:!!r._xfer,o:!!r._open,g:!!r._pass}; });
  var audit=null; try{ audit=dprAudit(text, cross, taking, hist); }catch(e){ audit={ok:false,blocks:[],reqs:[],counts:{satisfied:0,not:0,in_progress:0,unknown:0},err:String(e&&e.message||e)}; }
  /* the report's catalog rides on the audit, so every count of it knows quarter from semester */
  try{ if(audit&&prog&&prog.catalog)audit.catalog=prog.catalog; }catch(e){}
  try{ if(audit&&printed)audit.printed=printed.getFullYear()+'-'+String(printed.getMonth()+1).padStart(2,'0')+'-'+String(printed.getDate()).padStart(2,'0'); }catch(e){}
  return {ok:true, rows:out, program:prog, skipped:skipped, audit:audit,""")

# 3. the block itself, right after the reader's exports
one("""window.dprParse=dprParse;
window.dprScrub=dprScrub;
""", """window.dprParse=dprParse;
window.dprScrub=dprScrub;
/* website-reader-v2 (2026-10-14): lifted verbatim from app/planner.js — edit it HERE; build.py lifts it back. */
""" + block + """window.dprAudit=dprAudit;
""")
f.write_text(s)
print('patched', f)
