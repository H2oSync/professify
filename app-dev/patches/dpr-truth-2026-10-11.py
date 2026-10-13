#!/usr/bin/env python3
r"""The Degree Progress Report as the source of truth (Tate, 2026-10-11): "When a student uploads their DPR,
TermChamp should accurately understand which classes they've completed, what requirements those classes
satisfy, and what they still need to graduate."

PART 1 — THE READER (app/planner.js): the classes the report used for each requirement.
  Every requirement line on the report prints a "Courses Used" table: term, subject, number, title, GRADE,
  units. Until now the reader looked at those rows only to see whether a class being taken sat under a line.
  It now keeps, per line, the class (as printed: "FSN 250", "5A5C 1TR") and its term — never the title, the
  grade or the units — with today's number when the report or the crosswalk gives one ("BUS 214" → "BUS 2214"),
  and whether the report's own Course History calls it transfer credit or a class still being taken.
  A line the report says is Not Satisfied also keeps the classes its Course History holds (finished, a credit
  grade — never a W/IC/RP) that the line lists but doesn't count: "listed". The report decides; the app says so.

Usage: python3 dpr-truth-2026-10-11.py <repo-dir>      Replayable from 1f8cc5b: every anchor must match once."""
import sys, os
D = sys.argv[1]
PP = os.path.join(D, 'app', 'planner.js')
P = open(PP, encoding='utf-8').read()

def rep(a, b, label):
    global P
    n = P.count(a)
    if n != 1: sys.exit(f'planner {label}: anchor matched {n}x')
    P = P.replace(a, b)

# ---- dprParse: what each Course History row is, for the rows under each requirement ----
rep("""  var audit=null; try{ audit=dprAudit(text, cross, taking); }""",
    """  /* (2026-10-11, the report as the source of truth) what each Course History row is — today's number, transfer
     credit, no grade yet, a credit grade — for the "Courses Used" rows under each requirement. Never the grade. */
  var hist={}; out.forEach(function(r){ hist[r.code+'|'+r.term+' '+r.year]={cur:r.cur,x:!!r._xfer,o:!!r._open,g:!!r._pass}; });

  var audit=null; try{ audit=dprAudit(text, cross, taking, hist); }""", 'parse-hist')

# (review 2026-10-11) a passing grade, for "listed" only: a class failed or withdrawn from is no conflict
rep("""      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units, _post:postable, _cp:cmark,""",
    """      _dpr:true, _open:stillOpen, _xfer:xfer, _units:units, _post:postable, _cp:cmark, _pass:!!gradeTok&&/^(?:[A-D][+-]?|CR|P|333|[1-7]00)$/.test(gradeTok),""", 'row-pass')

# ---- dprAudit ----
rep("function dprAudit(text, cross, taking){", """/* (2026-10-11) a row of a requirement's "Courses Used" table: term, subject (a transfer GE placeholder's can lead
   with a digit: "5A5C 1TR", "A1GE 1TR"), number. Only these three are read; the title, grade and units after them
   never are. */
var DPR_USEDROW=/^(\\d{4})\\s+(Fall|Wtr|Win|Spr|Sum)\\s+([A-Z0-9]{2,6}(?:\\/[A-Z]{2,5})?)\\s+([0-9][0-9A-Z]{0,5})(?=\\s|$)/;
function dprAudit(text, cross, taking, hist){""", 'audit-sig')

rep("""      var rw=/^\\d{4}\\s+(?:Fall|Wtr|Spr|Sum)\\s+([A-Z]{2,5})\\s+(\\d{3,4}[A-Z]?)\\b/.exec(ln);""",
    """      /* (2026-10-11) the class the report used for this line, and its term */
      var ru=DPR_USEDROW.exec(ln.replace(/[\\uE000-\\uE002]/g,'').trim());
      if(ru&&/[A-Z]/.test(ru[3]))usedAdd(cur,ru);
      var rw=/^\\d{4}\\s+(?:Fall|Wtr|Spr|Sum)\\s+([A-Z]{2,5})\\s+(\\d{3,4}[A-Z]?)\\b/.exec(ln);""", 'audit-row')
rep("""      if(rw){ var rt=/^(\\d{4})\\s+(\\w+)/.exec(ln);""", """      if(ru&&!rw)continue;
      if(rw){ var rt=/^(\\d{4})\\s+(\\w+)/.exec(ln);""", 'audit-row-skip')

# the helper, a closure over isNow / cross / hist — defined right after isNow
rep("""  var isNow=function(c,term){ var k=null; try{ k=(typeof canonCode==='function')?canonCode(c):null; }catch(e){} return !!(now[c+'|'+term]||(k&&now[k+'|'+term])); };""",
    """  var isNow=function(c,term){ var k=null; try{ k=(typeof canonCode==='function')?canonCode(c):null; }catch(e){} return !!(now[c+'|'+term]||(k&&now[k+'|'+term])); };
  /* (2026-10-11) one "Courses Used" row → { c: as printed, t: "Winter 2024", n: today's number when it differs,
     x: transfer / test / other credit, p: being taken now } — at most 40 a line, each class+term once */
  var CPSUBJ=/^[A-Z]{2,5}(?:\\/[A-Z]{2,5})?$/;
  var usedAdd=function(b,m){
    var t=(DPR_TERMOF[m[2]]||m[2])+' '+m[1], c=m[3]+' '+m[4], u=b.used||(b.used=[]);
    if(u.length>=40||u.some(function(x){ return x.c===c&&x.t===t; }))return;
    var h=(hist&&hist[c+'|'+t])||null, n=null;
    if(CPSUBJ.test(m[3])){ n=(h&&h.cur)||(cross&&cross[c])||null; if(!n){ try{ n=(typeof canonCode==='function')?canonCode(c):null; }catch(e){} } }
    var e={c:c,t:t}; if(n&&n!==c)e.n=n;
    /* a subject that isn't Cal Poly's (a GE placeholder), a number that isn't (1TR, 1T13), or the Course History's word */
    if((h&&h.x)||!CPSUBJ.test(m[3])||!/^\\d{3,4}[A-Z]{0,2}$/.test(m[4]))e.x=true;
    else if(isNow(c,t)||(n&&isNow(n,t)))e.p=true;
    u.push(e);
  };
  var usedMerge=function(to,from){ (from.used||[]).forEach(function(e){ var u=to.used||(to.used=[]); if(u.length<40&&!u.some(function(x){ return x.c===e.c&&x.t===e.t; }))u.push(e); }); };""", 'audit-helper')

# option groups: the requirement that counts carries every option's classes
rep("""      if(b.status==='not'&&!b.oneOf&&!kids.some(function(x){ return x.status!=='satisfied'; })){ b.atomic=true; kids.forEach(function(x){ x.inOption=true; }); return; }""",
    """      if(b.status==='not'&&!b.oneOf&&!kids.some(function(x){ return x.status!=='satisfied'; })){ b.atomic=true; kids.forEach(function(x){ x.inOption=true; usedMerge(b,x); }); return; }""", 'merge-min')
rep("""        b.atomic=true; kids.forEach(function(x){ x.inOption=true; x.options.forEach(function(c){ if(b.options.indexOf(c)<0)b.options.push(c); }); });""",
    """        b.atomic=true; kids.forEach(function(x){ x.inOption=true; usedMerge(b,x); x.options.forEach(function(c){ if(b.options.indexOf(c)<0)b.options.push(c); }); });""", 'merge-oneof')
rep("""        var rep=opt[0]; opt.forEach(function(x){ if(x!==rep)x.inOption=true; x.options.forEach(function(c){ if(rep.options.indexOf(c)<0)rep.options.push(c); }); });""",
    """        var rep=opt[0]; opt.forEach(function(x){ if(x!==rep){ x.inOption=true; usedMerge(rep,x); } x.options.forEach(function(c){ if(rep.options.indexOf(c)<0)rep.options.push(c); }); });""", 'merge-opt')

# listed but not counted: a Not Satisfied line, a class on the Course History it lists (finished, a credit grade)
rep("""  var reqs=blocks.filter(function(b){ return b.atomic; }).map(function(b){""",
    """  /* (2026-10-11) a Not Satisfied line that lists a class the Course History holds, finished with a PASSING grade (`g`:
     A–D, CR, P, credit — never an F / NC / W, never one still being taken), which the report used for no line at all:
     the report decides; the app says so */
  var done={}; Object.keys(hist||{}).forEach(function(k){ var h=hist[k]; if(!h.g||h.o)return; var c=k.split('|')[0]; done[c]=1; if(h.cur)done[h.cur]=1; });
  var canon=function(c){ try{ return (typeof canonCode==='function'&&canonCode(c))||c; }catch(e){ return c; } };
  var anyUsed={}; blocks.forEach(function(b){ (b.used||[]).forEach(function(e){ anyUsed[canon(e.c)]=1; if(e.n)anyUsed[canon(e.n)]=1; }); });
  blocks.forEach(function(b){ if(!b.atomic||b.status!=='not')return;
    var mine=anyUsed;   /* used by this line or another: the report placed it, so it's no conflict */
    b.listed=b.options.filter(function(c){ return (done[c]||done[canon(c)])&&!mine[canon(c)]; }).slice(0,10); });
  var reqs=blocks.filter(function(b){ return b.atomic; }).map(function(b){""", 'listed')
rep("""             group:b.parent?b.parent.label:null, oneOf:!!b.oneOf };""",
    """             group:b.parent?b.parent.label:null, oneOf:!!b.oneOf, used:(b.used||[]).slice(0,40), listed:(b.listed||[]).slice() };""", 'reqs-out')

# a code line no verdict owns ends the line above: the report's closing "FREE ELECTIVES" / "COURSE CREDITS NOT USED"
# (R30 / R-0030) prints no verdict, and its whole table had been read as the last GE units line's classes
rep("""      blocks.push(b); cur=b; continue;
    }
    if(cur){""", """      blocks.push(b); cur=b; continue;
    }
    /* (2026-10-11) a group or requirement code on a line no verdict owns — "(RG8)", "(R30)", "… (R-0030)", a heading
       that prints no verdict — starts something else: the rows under it aren't the line above's. The report's
       closing "FREE ELECTIVES" table (classes it used for nothing) sat under the last GE units line. */
    if(cur&&cur.code&&/\(R[^)]*\)\**\s*$/.test(ln)&&!/^NOTE\s*:/i.test(ln)&&!DPR_UNITLINE.test(ln)){ var oc=dprCode(ln); if(oc&&oc.code!==cur.code){ cur=null; continue; } }
    if(cur){""", 'code-ends-block')

# the printed date (a date, never an ID) rides on the audit, for "report printed Oct 8" on Past classes
rep("""  var audit=null; try{ audit=dprAudit(text, cross, taking, hist); }catch(e){ audit={ok:false,blocks:[],reqs:[],counts:{satisfied:0,not:0,in_progress:0,unknown:0},err:String(e&&e.message||e)}; }""",
    """  var audit=null; try{ audit=dprAudit(text, cross, taking, hist); }catch(e){ audit={ok:false,blocks:[],reqs:[],counts:{satisfied:0,not:0,in_progress:0,unknown:0},err:String(e&&e.message||e)}; }
  /* the report's catalog rides on the audit, so every count of it (Report read, Check, the diff) knows quarter from semester */
  try{ if(audit&&prog&&prog.catalog)audit.catalog=prog.catalog; }catch(e){}
  try{ if(audit&&printed)audit.printed=printed.getFullYear()+'-'+String(printed.getMonth()+1).padStart(2,'0')+'-'+String(printed.getDate()).padStart(2,'0'); }catch(e){}""", 'printed')

# (stress test, 2026-10-11) the older layout's verdict that wraps ACROSS a page break: the page's blank line and its
# furniture (Page / Name / EMPLID / Date Printed) sat between the verdict and its last words, so the code was lost and
# a requirement with lines ("GE ELECTIVES IN AREAS B, C, & D … (R-83)") was counted as a line of its own
rep("""        for(var pk=j+1;pk<=j+2&&pk<end;pk++){
          var pl=String(lines[pk]||'').trim();
          if(!pl||DPR_VERDICT.test(pl)""", """        for(var pk=j+1,seen=0;seen<2&&pk<end;pk++){
          var pl=String(lines[pk]||'').trim();
          if(DPR_FURN.test(pl)||(!pl&&DPR_FURN.test(String(lines[pk+1]||'').trim())))continue;
          seen++;
          if(!pl||DPR_VERDICT.test(pl)""", 'peek-page-break')
rep("""          if(DPR_RCODE.test(pl)){ for(var q=j+1;q<=pk;q++)words+=' '+String(lines[q]||'').trim(); j=pk; break; }""",
    """          if(DPR_RCODE.test(pl)){ for(var q=j+1;q<=pk;q++){ var ql=String(lines[q]||'').trim(); if(ql&&!DPR_FURN.test(ql))words+=' '+ql; } j=pk; break; }""", 'peek-join')

open(PP, 'w', encoding='utf-8').write(P)
print('dpr-truth: part 1 (reader) done')
