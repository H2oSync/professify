#!/usr/bin/env python3
"""What the 300 synthetic Degree Progress Reports found (make-dpr-corpus.py, check-dpr-synth.mjs; Tate, 2026-10-12:
"create 300 different (artificial ones …) so we know every scenario we might be up against"). Edits app/planner.js
(the report reader) and app/index.html. Each fix says which reports found it.
  python3 dpr-corpus-fixes-2026-10-12.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
def patch(rel, reps):
    p = ROOT / rel; s = p.read_text()
    for a, b in reps:
        c = s.count(a)
        if c != 1: sys.exit(f'dpr-corpus-fixes: {rel}: expected 1 of {a[:80]!r}, found {c}')
        s = s.replace(a, b)
    p.write_text(s)

patch('app/planner.js', [
# 1. A line belongs to the requirement above it only when it's that requirement's own line (R41-10 under R-0041). On the
#    older layout a major's lines (R40-170 …) follow a "1 of 3 Options" requirement (R-0041) with no requirement of
#    their own: they were read as more options of it — every one of them dropped from the count, and their classes
#    made the options' (249 of 300 reports had lines go missing this way or by the same path).
("""      b.parent=level==='LN'?req:null;
      /* the requirement above lends its words to a line's kind only when the line is its own: R11-10 under
         R-0011 / R11 — a line whose number differs (a new section the reader saw no heading code for) doesn't */
      var own=!(cd&&cd.level==='LN'&&req&&req.code)||(+String(req.code).replace(/^R-?/,''))===(+String(cd.code).replace(/^R(\\d+)-.*$/,'$1'));""",
 """      /* the requirement above owns a line only when it's its own: R11-10 under R-0011 / R11 — a line whose number
         differs (a new section the reader saw no heading code for) is neither its line nor an option of it
         (2026-10-12, the synthetic reports: a major's R40-170 … after "1 of 3 Options" (R-0041) were read as more options) */
      var own=!(cd&&cd.level==='LN'&&req&&req.code)||(+String(req.code).replace(/^R-?/,''))===(+String(cd.code).replace(/^R(\\d+)-.*$/,'$1'));
      b.parent=level==='LN'&&own?req:null;"""),
])

# 2. A class's number today: the report's own pair decides the number ("LA 222 (2212)" is LA 2212 — the registrar's word
#    for this student's record); TermChamp's crosswalk is kept when it agrees on the number (it knows a subject that
#    changed: CPE 101 (1001) is CSC 1001) and used alone for a number printed bare. The crosswalk won outright before, so
#    where the two disagree the record got another class. (Found by synth-258 / synth-281, whose disagreement was the
#    generator's own invented number colliding with the crosswalk — no real report seen does this, but the report is the
#    registrar's word, so it wins. tests.dprCorpusFound plants a disagreeing crosswalk entry to prove it.)
READER = [
("""      cur=((typeof COURSE_EQUIV!=='undefined')&&COURSE_EQUIV[n])||cross[code]
          ||((typeof canonCode==='function')?canonCode(code):code)||code;""",
 """      /* (2026-10-12) the report's own pair decides the NUMBER; the crosswalk is kept when it agrees on the number (it
         knows a subject that changed: CPE 101 (1001) is CSC 1001), and used alone for a number printed bare */
      var eq=(typeof COURSE_EQUIV!=='undefined')&&COURSE_EQUIV[n], pr=cross[code];
      cur=(eq&&(!pr||String(eq).split(' ')[1]===String(pr).split(' ')[1]))?eq
          :pr?(((typeof canonCode==='function')&&canonCode(pr))||pr)
          :((typeof canonCode==='function')?canonCode(code):code)||code;"""),
# 3. A class being taken has no grade, but its title is cut short on the report: "Materials Selection for the Life C"
#    ends in a letter that reads as a grade, so the class read as FINISHED with a C — off My Classes, onto Past classes,
#    and its requirement not in progress (synth-043 MATE 4300, synth-138 / 283 ART 1184, synth-188 ENGL 3374). The row
#    wears the report's "Course In Progress" icon: such a row has no grade, whatever its last word is.
("""var DPR_XMARK='\\uE000', DPR_BMARK='\\uE001', DPR_CMARK='\\uE002';""",
 """var DPR_XMARK='\\uE000', DPR_BMARK='\\uE001', DPR_CMARK='\\uE002', DPR_PMARK='\\uE003';   /* PMARK (2026-10-12): Cal Poly's "Course In Progress" picture */"""),
("""    var xmark=ln.indexOf(DPR_XMARK)>=0, bmark=ln.indexOf(DPR_BMARK)>=0, cmark=ln.indexOf(DPR_CMARK)>=0;
    if(xmark||bmark||cmark)ln=ln.split(DPR_XMARK).join('').split(DPR_BMARK).join('').split(DPR_CMARK).join('').trim();""",
 """    var xmark=ln.indexOf(DPR_XMARK)>=0, bmark=ln.indexOf(DPR_BMARK)>=0, cmark=ln.indexOf(DPR_CMARK)>=0, pmark=ln.indexOf(DPR_PMARK)>=0;
    if(xmark||bmark||cmark||pmark)ln=ln.split(DPR_XMARK).join('').split(DPR_BMARK).join('').split(DPR_CMARK).join('').split(DPR_PMARK).join('').trim();"""),
("""    if(gradeTok&&(!DPR_GRADE.test(gradeTok)||(cmark&&DPR_TEST.test(gradeTok)))){ title=(title+' '+gradeTok).trim(); gradeTok=''; }""",
 """    if(gradeTok&&(!DPR_GRADE.test(gradeTok)||(cmark&&DPR_TEST.test(gradeTok))||pmark)){ title=(title+' '+gradeTok).trim(); gradeTok=''; }"""),
("""    var rowRe=/^\\s*\\d{4}\\s+(Fall|Wtr|Win|Winter|Spr|Spring|Sum|Summer)\\b/, hit=[], cp=false, RANK={T:3,C:2,O:1};""",
 """    var rowRe=/^\\s*\\d{4}\\s+(Fall|Wtr|Win|Winter|Spr|Spring|Sum|Summer)\\b/, hit=[], cp=false, RANK={T:3,C:2,P:2,O:1};"""),
("""      var k=mk.t?'T':mk.c?'C':'O'; if(k==='C')cp=true;""",
 """      var k=mk.t?'T':mk.c?(mk.p?'P':'C'):'O'; if(k==='C'||k==='P')cp=true;"""),
("""      if(hit[i]==='T')l.text+=' '+DPR_XMARK; else if(hit[i]==='C')l.text+=' '+DPR_CMARK; else""",
 """      if(hit[i]==='T')l.text+=' '+DPR_XMARK; else if(hit[i]==='C')l.text+=' '+DPR_CMARK; else if(hit[i]==='P')l.text+=' '+DPR_CMARK+DPR_PMARK; else"""),
]
MARKS = [
("""  const csig = new Set([gsig, dprLegendSig(pages[0].items, legend, /Course In Progress/i), dprLegendSig(pages[0].items, legend, /^\\s*Planned\\s*$/i)].filter(g => g && g !== xsig));""",
 """  const psig = dprLegendSig(pages[0].items, legend, /Course In Progress/i);
  const csig = new Set([gsig, psig, dprLegendSig(pages[0].items, legend, /^\\s*Planned\\s*$/i)].filter(g => g && g !== xsig));"""),
("""const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) }));""",
 """const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig), p: !!psig && c.sig === psig && psig !== gsig }));   /* p (2026-10-12): "Course In Progress" — no grade on that row */"""),
]
for f in ('app/planner.js', 'index.html'): patch(f, READER)
patch('app/planner.js', [("""      var ru=DPR_USEDROW.exec(ln.replace(/[\\uE000-\\uE002]/g,'').trim());""",
 """      var ru=DPR_USEDROW.exec(ln.replace(/[\\uE000-\\uE003]/g,'').trim());""")])   # the requirement reader is the phone's only    # the website's report import reads with the same code
for f in ('app/index.html', 'index.html'): patch(f, MARKS)

# 4. The same for the classes a requirement names ("CPE 101 (1001) or …"): the pair's number with the crosswalk's subject
#    when they agree on the number — the option is CSC 1001, so a CSC 1001 in My Classes covers the line and the Builder
#    offers the right class (29 reports, every CPE→CSC and ES→NR renumbering).
patch('app/planner.js', [
("""    var old=subj+' '+m[2], now=m[3]?(subj+' '+m[3]):((cross&&cross[old])||null);""",
 """    var old=subj+' '+m[2], now=m[3]?(subj+' '+m[3]):((cross&&cross[old])||null);
    var eq=(typeof COURSE_EQUIV!=='undefined')&&COURSE_EQUIV[old]; if(m[3]&&eq&&String(eq).split(' ')[1]===m[3])now=eq;   /* (2026-10-12) a renamed subject */"""),
])

# 5. A class failed, withdrawn from, incomplete or no-credit (F, W, NC, IC, RP) isn't a class you've taken: it went to Past
#    classes all the same, so the flowchart ticked it off, prerequisites counted it as met and the Builder stopped offering
#    it (synth-005 ARCH 2000 W; every "F never retaken", "W", "NC" report). It's read (its line stays open, the report
#    says so) but not saved — unticked on the website's import, left out on the phone. Never its grade: only that it
#    didn't pass.
for f in ('app/planner.js', 'index.html'):
    patch(f, [
    ("""    var postable=!!gradeTok&&!/^(?:W|IC|RP)$/.test(gradeTok);""",
     """    var postable=!!gradeTok&&!/^(?:W|IC|RP)$/.test(gradeTok);
    /* (2026-10-12) graded but not passed — F, W, NC, IC, RP: not a class taken (never saved, never the grade itself) */
    var fail=!!gradeTok&&!/^(?:[A-D][+-]?|CR|P|333|[1-7]00)$/.test(gradeTok);"""),
    ("""      pick:!already,""", """      pick:!already&&!fail, _fail:fail,"""),
    ])
patch('app/index.html', [
("""  r.rows.forEach(x => {
    const k = key(x.term, x.year);
    if (x._open && !x._xfer && k === cur) x._now = true;""",
 """  r.rows.forEach(x => {
    const k = key(x.term, x.year);
    if (x._fail) { x._now = false; x.skip = 'not passed — not a finished class'; x.pick = false; return; }   /* (2026-10-12) */
    if (x._open && !x._xfer && k === cur) x._now = true;"""),
])
# 6. (Sonnet review) A class already on the account that the new report shows NOT passed (an F or W that an older import
#    saved) was kept, because any report row with its code and term kept it. Only a passed or ungraded row keeps a class;
#    a failed one comes off at save, and the list says why.
patch('app/index.html', [
("""  const K = c => pcK(c), rows = r.rows || [];   // any row on the report, flagged or later-term too, keeps its class""",
 """  const K = c => pcK(c), all = r.rows || [], rows = all.filter(x => !x._fail || x._prov);   // any row on the report, flagged or later-term too, keeps its class — never one it shows not passed (2026-10-12); RP (grade pending) still keeps it"""),
("""    const other = rows.find(x => same(x, h)), at = h.term && h.year ? `as ${h.term} ${h.year}` : 'with no term';
    const why = other ?""",
 """    const other = rows.find(x => same(x, h)), at = h.term && h.year ? `as ${h.term} ${h.year}` : 'with no term';
    const bad = !other && all.some(x => x._fail && same(x, h));
    const why = bad ? `On your account ${at} · your report shows it not passed` : other ?"""),
# 7. The "N transfer" pill counts transfer credit you have — not a transfer row the report shows not passed (an NC).
("""  const a = r && r.audit, xfer = (r && r.rows || []).filter(x => x._xfer && !x.flag).length;""",
 """  const a = r && r.audit, xfer = (r && r.rows || []).filter(x => x._xfer && !x.flag && !x._fail).length;   /* (2026-10-12) never one not passed */"""),
])

# 8. (Sonnet review) More grades: P (pass), and WU (unofficial withdrawal), NP (no pass), AU (audit — no credit), which
#    aren't a pass. They read as grades now (before, they joined the title and the row read as being taken); WU and AU,
#    like W, are never posted transfer credit in a running term. RP (report in progress: a senior project still being
#    graded) stays unsaved but is marked _prov, so report wins (6) never deletes the class from the account for it. IC
#    is Cal Poly's "Incomplete Charged" — it counts as an F. "IP" printed in the grade
#    column means in progress: no grade. "I" (incomplete) is left out on purpose — a title cut short after a Roman
#    numeral ("Career Readiness I") would read as one.
for f in ('app/planner.js', 'index.html'):
    patch(f, [
    ("""var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333|[1-7]00)$/;""",
     """var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|WU|P|NP|AU|IC|RP|333|[1-7]00)$/;   /* P, WU, NP, AU (2026-10-12): read as grades */"""),
    ("""    var postable=!!gradeTok&&!/^(?:W|IC|RP)$/.test(gradeTok);""",
     """    var postable=!!gradeTok&&!/^(?:W|WU|AU|IC|RP)$/.test(gradeTok);"""),
    ("""      pick:!already&&!fail, _fail:fail,""", """      pick:!already&&!fail, _fail:fail, _prov:gradeTok==='RP',"""),
    ("""    if(gradeTok&&(!DPR_GRADE.test(gradeTok)||(cmark&&DPR_TEST.test(gradeTok))||pmark)){""",
     """    if(gradeTok==='IP')gradeTok='';   /* (2026-10-12) "IP" in the grade column: in progress */
    if(gradeTok&&(!DPR_GRADE.test(gradeTok)||(cmark&&DPR_TEST.test(gradeTok))||pmark)){"""),
    ])
print('dpr-corpus-fixes: applied')
