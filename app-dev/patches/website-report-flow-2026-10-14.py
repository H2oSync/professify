#!/usr/bin/env python3
"""The Degree Progress Report on the website, at the phone's level (Tate, 2026-10-14: "catch the website up to the level
the app is" — Round 1 registration opens Mon Oct 19).

After website-reader-v2 the website READ the report's own verdicts (dprParse → audit) and used none of them: the import
went to class_history / saved_classes and Past Classes judged everyone — quarter catalog included — against the 2026–28
flowchart. This ports the phone's report flow (app/index.html, app/planner.js), with the website's names:

1. The verdicts are kept (degree_audit, RUN 14, live): one row per account, upsert on user_id, only what the phone's
   auditRow keeps (a line's words, verdict, counts, options, the classes the report used — code and term — and the ones it
   listed but didn't count). Never a grade, EMPLID or name (DPR_PII drops a label that looks like one). Until the table
   answers, the device keeps it per account (tc-audit:<uid>) and sends it up at the next load; marks done ride along.
   Lines can be flagged as read wrong (dpr_flags, de-identified) from "Check what was read".
2. GE areas and units (plGeMap, auditUnitsOf, GE_QTR, plGeArea, geSubj, plGeBar) and one way of counting the report
   everywhere (auditLines: filled · left · can't check).
3. In progress now, from the record: a class_history row dated the term you're in (mcNowLabel) or later is a class being
   taken until the term ends (PROFESSIFY_CONFIG.TERM_ENDS, 2026-12-22, as the phone) — never done, never a prerequisite
   met: completedCodes(), the local mirror, plLedgerCompute's count and myTakingCodes() all follow it. Transfer credit
   and undated rows stay finished. (A TERM_ENDS older than NOW_UNTIL is last term's and stops applying from NOW_UNTIL.)
4. Concentrations in their real shape (planner.js CONC_SHAPE / concInfo / schConcClasses / schExpandConc / slotCodes /
   withChoiceCodes): a Business Administration concentration's required classes, its pick-ones and its electives, and a
   "this or that" slot checked like a coded one. The website-only schExpandConcPublic stays; so does the options list
   on an extra concentration slot.
5. The report wins: "already on your record" is the same class in the same TERM; what's on your account and not on the
   report is listed in the review, checked, and taken off at save (your class_history rows; this term's saved_classes and
   my_sections when the report shows this term — never your Spring list) unless you uncheck it. A row that came off
   because the report dates it differently is saved again with the report's term. A new report over an old one opens
   "Your report changed": lines newly filled, open again, new — and each Plan's class that filled a line now done, with
   "Take it out" (TCPlans.setSections).
6. The review list says what was read: "N filled · M left · K can't check", the catalog and printed date, and "Check what
   was read" with every line's verdict and classes.
7. Past classes by requirement when there's a report: Still needed first (Mark done / Undo, lines the app couldn't read,
   "Needs a look" when the report lists a class it didn't count, in progress this term folded), then Major and support ·
   the concentration by name · General education · Degree requirements, folded, each line naming the class the report
   used ("BUS 214 → BUS 2214 · Winter 2025", "· transfer credit", "· this term"); Units only; the 2026–28 flowchart ledger
   only on a semester catalog. A report kept before per-line classes keeps the old screen and asks for the report again.
   Two columns from 1140px.
8. Flowchart marks move to the account (flowchart_marks, RUN 15, live): this device's checklist ticks on rows a mark
   stands for (no class the record can check) go up once per account, then the account's marks are read — they count in
   the ledger (no GE class is spent on a marked row) and show ticked on the checklist; a tick or untick is sent.

Checked by app-dev/tests/check-desktop-report.mjs (+ mutate-desktop-report.mjs) and check-dpr-synth-web.mjs.
Usage: python3 website-report-flow-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-report-flow (2026-10-14)' in s:
    sys.exit('already patched')
pl = (root / 'app' / 'planner.js').read_text()

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ 3. in progress now, from the record
one("""  NOW_UNTIL: '2027-01-25',
""", """  NOW_UNTIL: '2027-01-25',
  /* the last day of NOW_TERM (the registrar's calendar; the phone's CFG.TERM_ENDS) — until then a class_history row dated
     NOW_TERM is a class being taken, never a finished one (website-report-flow, 2026-10-14) */
  TERM_ENDS: '2026-12-22',
""")
one("""  if(mcTwoTerms())NOW_MINE.classes.forEach(function(c){ if(a.indexOf(c)<0)a.push(c); });
  return a;
}""", """  if(mcTwoTerms())NOW_MINE.classes.forEach(function(c){ if(a.indexOf(c)<0)a.push(c); });
  /* website-report-flow (2026-10-14): and your record's rows of this term or later — the phone's takingCodes() */
  try{ var _k={}; a.forEach(function(c){ _k[canonCode(c)||c]=1; });
    (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code&&histNotDone(h)){ var c=canonCode(h.code)||h.code; if(!_k[c]){ _k[c]=1; a.push(c); } } }); }catch(e){}
  return a;
}
/* website-report-flow (2026-10-14), the phone's rule (2026-10-11, Tate): a row on your record dated the term you're in
   (mcNowLabel) or later isn't a finished class — the term isn't over. It's a class you're taking: never "done", never a
   prerequisite met, always "in progress". Undated rows (AP, an old import) and transfer credit stay finished. */
var HT_ORD={Winter:1,Spring:2,Summer:3,Fall:4};
/* the term you're in is still on until its last day (TERM_ENDS); a TERM_ENDS older than NOW_UNTIL is last term's */
function nowTermOn(){
  var c=cfg(), e=String(c.TERM_ENDS||'').trim(), u=String(c.NOW_UNTIL||'').trim(), d=mcPacificDay();
  if(!e)return true;
  if(u&&d>=u&&e<u)return true;
  return d<=e;
}
function histNotDone(h){
  if(!h||!h.term||!h.year)return false;
  try{ if(typeof pcReadSource==='function'){ var s=pcReadSource(h.professor); if(s&&s.src&&s.src.mark)return false; } }catch(e){}   /* transfer and exam credit: posted, finished */
  var m=/^([A-Za-z]+)\\s+(\\d{4})$/.exec(String(mcNowLabel()||'').trim()); if(!m||!HT_ORD[m[1]])return false;
  var row=(+h.year)*10+(HT_ORD[h.term]||0), now=(+m[2])*10+HT_ORD[m[1]];
  return row>now||(row===now&&nowTermOn());
}
/* codes whose every row on the record is one being taken (a retake of a finished class is still finished) */
function histTakingOnly(){
  var nd={}, dn={};
  try{ (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(!h||!h.code)return; var k=canonCode(h.code)||h.code; if(histNotDone(h))nd[k]=1; else dn[k]=1; }); }catch(e){}
  Object.keys(dn).forEach(function(k){ delete nd[k]; });
  return nd;
}
try{ window.histNotDone=histNotDone; window.nowTermOn=nowTermOn; window.histTakingOnly=histTakingOnly; }catch(e){}""")
one("""  try{ (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code)add(h.code); }); }catch(e){}
  try{ completedLocal().forEach(add); }catch(e){}
  try{ waivedCodes().forEach(add); }catch(e){}""", """  /* website-report-flow (2026-10-14): a class you're taking this term isn't satisfied yet — from the record or its mirror */
  var _nd={}; try{ if(typeof histTakingOnly==='function')_nd=histTakingOnly(); }catch(e){}
  try{ (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code&&!(typeof histNotDone==='function'&&histNotDone(h)))add(h.code); }); }catch(e){}
  try{ completedLocal().forEach(function(c){ var k=c; try{ k=canonCode(c)||c; }catch(e){} if(!_nd[k])add(c); }); }catch(e){}
  try{ waivedCodes().forEach(add); }catch(e){}""")
one("""    var codes=(typeof myHistory!=='undefined'?myHistory:[])
      .map(function(h){ return h&&h.code?canonCode(h.code):''; }).filter(Boolean);""", """    var codes=(typeof myHistory!=='undefined'?myHistory:[])
      .filter(function(h){ return !(typeof histNotDone==='function'&&histNotDone(h)); })   /* website-report-flow: finished rows only */
      .map(function(h){ return h&&h.code?canonCode(h.code):''; }).filter(Boolean);""")
one("""      (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code){ var k=canonCode(h.code); have[k]=(have[k]||0)+1; } });""",
    """      (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code&&!(typeof histNotDone==='function'&&histNotDone(h))){ var k=canonCode(h.code); have[k]=(have[k]||0)+1; } });   /* website-report-flow: a row of this term is in progress */""")

# ================================================================ 4. concentrations in their real shape (planner.js)
a = pl.index("/* (2026-10-11) CONC_REQS lists required classes, one-of pairs and electives in one run;")
b = pl.index("function concInfo(majorName){", a)
shape = pl[a:b]
assert shape.count('var CONC_SHAPE={') == 1 and 'CONC_SHAPE' not in s
one("function concInfo(majorName){", "/* website-report-flow (2026-10-14): lifted from app/planner.js */\n" + shape + "function concInfo(majorName){")
one("""      return {known:true,list:c.list||[],kind:c.kind||'concentration',src:c.src||null};""",
    """      return {known:true,list:(c.list||[]).map(function(x){ return Object.assign({reqKnown:true},x); }),kind:c.kind||'concentration',src:c.src||null};""")
one("""        return {name:k,units:0,note:'',classes:CONC_REQS[majorName][k].map(function(code){
          return [code,(typeof COURSE_NAME!=='undefined'&&COURSE_NAME[code])||'',3];
        })};""", """        var all=CONC_REQS[majorName][k], sh=(CONC_SHAPE[majorName]||{})[k], nm=function(code){ return [code,(typeof COURSE_NAME!=='undefined'&&COURSE_NAME[code])||'',3]; };
        if(!sh)return {name:k,units:0,note:'',classes:all.map(nm)};
        var taken={}; sh.req.concat.apply(sh.req,sh.one||[]).forEach(function(c){ taken[c]=1; });
        return {name:k,units:0,note:sh.note||'',reqKnown:true,classes:sh.req.map(nm),one:(sh.one||[]).map(function(g){return g.slice();}),
          electives:all.filter(function(c){ return !taken[c]; })};""")
one("""        return {conc:cc,known:true,note:hit.note||'',list:(hit.classes||[]).map(function(a){""",
    """        return {conc:cc,known:true,note:hit.note||'',reqKnown:!!hit.reqKnown,one:hit.one||[],electives:hit.electives||[],list:(hit.classes||[]).map(function(a){""")
one("""      return true;
    });
    var out={}; for(var kk in m)out[kk]=m[kk];""", """      return true;
    });
    /* (2026-10-11, planner.js) after the required classes: each pick-one is one spot, then the electives — every one of them */
    var oneG=(info.one||[]).map(function(g){ return g.filter(function(c){ return !_req[c]; }); }).filter(function(g){ return g.length; }), oi=0;
    var elec=(info.electives||[]).filter(function(c){ return !_req[c]; });
    var cname=function(c){ return (typeof COURSE_NAME!=='undefined'&&COURSE_NAME[c])||c; };
    var out={}; for(var kk in m)out[kk]=m[kk];""")
one("""        if(info.conc&&(list.length||_skipped.length)){""", """        if(info.conc&&(list.length||_skipped.length||oneG.length||elec.length)){""")
one("""          if(ci<list.length){ var pk=list[ci++]; ns.code=pk.code; ns.title=pk.name||pk.code; if(pk.units)ns.units=pk.units; ns.type='course'; ns.note=info.conc+' concentration'; }
          else if(_skipped.length&&!list.length){""", """          if(ci<list.length){ var pk=list[ci++]; ns.code=pk.code; ns.title=pk.name||pk.code; if(pk.units)ns.units=pk.units; ns.type='course'; ns.note=info.conc+' concentration'; ns.concKind=info.reqKnown?'req':'conc'; }
          else if(oi<oneG.length){ var g=oneG[oi++]; ns.note=info.conc+' concentration'; ns.concKind='one';
            if(g.length===1){ ns.code=g[0]; ns.title=cname(g[0]); ns.type='course'; } else { ns.type='choice'; ns.options=g.slice(); ns.title=g.join(' or '); } }
          else if(elec.length){ ns.note=info.conc+' concentration'; ns.concKind='el'; ns.hint=info.note||''; ns.title=info.conc+' elective';
            if(elec.length===1){ ns.code=elec[0]; ns.type='course'; } else { ns.type='choice'; ns.options=elec.slice(); } }
          else if(_skipped.length&&!list.length){""")
one("""          else { ns.title=info.conc+' — additional concentration course'; ns.note=info.note||(list.length+' courses to choose from'); ns.options=list.map(function(x){return x.code;}); }""",
    """          else { ns.title=info.conc+' elective'; ns.note=info.conc+' concentration'; ns.concKind='el'; ns.hint=info.note||'Pick it with your advisor'; ns.options=list.map(function(x){return x.code;}); }""")
one("function slotCodes(s){ if(!s.code)return [];", "function slotCodes(s){ if(s._opts)return s._opts.slice(); if(!s.code)return [];")
one("window.plLedgerCompute=function(){", """/* A choice slot ("Calculus for Data Science I or Business Calculus") lists its options: checked against them like a coded
   slot, its first option standing in as the code and _opts carrying them all (planner.js withChoiceCodes, 2026-10-02). */
function withChoiceCodes(m){
  var CODE=/^[A-Z&]{2,5} \\d{3,4}[A-Z]?$/;
  if(!m||!m.terms)return m;
  return Object.assign({},m,{terms:(m.terms||[]).map(function(t){ return Object.assign({},t,{slots:(t.slots||[]).map(function(sl){
    if(!sl||sl.code||sl.type!=='choice'||!Array.isArray(sl.options)||sl.options.length<2)return sl;
    var o=sl.options.map(function(c){ var raw=String(c||'').trim().toUpperCase(); return canonCode(raw)||raw; });
    if(!o.every(function(c){ return CODE.test(c); }))return sl;
    return Object.assign({},sl,{code:o[0],_opts:o});
  })}); })});
}
window.plLedgerCompute=function(){""")
one("""    if(mm&&typeof window.schExpandConcPublic==='function')mm=window.schExpandConcPublic(mm);""",
    """    if(mm&&typeof window.schExpandConcPublic==='function')mm=window.schExpandConcPublic(mm);
    if(mm)mm=withChoiceCodes(mm);   /* website-report-flow (2026-10-14) */""")
one("""        var cs=(typeof window.schSlotCodes==='function')?window.schSlotCodes(sl.code):[canonCode(sl.code)];""",
    """        var cs=sl._opts?sl._opts.slice():(typeof window.schSlotCodes==='function')?window.schSlotCodes(sl.code):[canonCode(sl.code)];""")

# ================================================================ 1, 2, 5, 6, 7: the report flow
MAIN = r'''/* ======================================================================================================
   website-report-flow (2026-10-14) — the Degree Progress Report on the website, at the phone's level.
   The phone (app/index.html) is the spec; each piece below names the phone function it is lifted from.
   1. The report's verdicts are KEPT (degree_audit, RUN 14): one row per account, the lines as auditRow keeps
      them — words, verdict, counts, the classes that cleared each (code + term only). Never a grade, an
      EMPLID or a name. Until the table answers, this device keeps it per account and sends it up later.
   2. Every screen counts the report the same way (auditLines): filled = Satisfied + In Progress + marked done
      by you; left = Not Satisfied; can't check = a verdict the reader couldn't place.
   5. The report wins: what's on your account but not on your report comes off when you save (unless you
      uncheck it); a new report over an old one shows what changed, and the Plans it touches.
   6. The review list says what was read: the counts, your catalog, every line.
   7. Past classes is laid out by the report's own requirements when there is one.
   ====================================================================================================== */
var AUDIT=null, AUDIT_UID=null, AUDIT_LOCAL=false, AUDIT_LOADED=false, AUDIT_ERR=null;
function auditKey(){ return 'tc-audit:'+((typeof sbUser!=='undefined'&&sbUser&&sbUser.id)||''); }
/* the audit of whoever is signed in — never another account's from this tab */
function curAudit(){ return (AUDIT&&typeof sbUser!=='undefined'&&sbUser&&AUDIT_UID===sbUser.id)?AUDIT:null; }
/* What's kept of a report line (phone auditRow): its words, the verdict, the counts, the classes that clear it.
   A label with a 7-digit number, "EMPLID", "Name:" or a grade beside units is dropped. */
var DPR_PII=/\d{7,}|EMPLID|\bName\s*:|(?:^|\s)(?:[A-DF][+-]?|CR|NC|W|WU|IC|I|RP|AU|P|NP|IP|RD|NG)\s+\d+\.\d{2}\b/i;
var AUDIT_CODE=/^[A-Z]{2,5}(?:\/[A-Z]{2,5})? \d{3,4}[A-Z]{0,2}$/, AUDIT_USED=/^[A-Z0-9]{2,6}(?:\/[A-Z]{2,5})? [0-9][0-9A-Z]{0,5}$/, AUDIT_TERM=/^(?:Fall|Winter|Spring|Summer) \d{4}$/;
function auditNums(u){
  if(!u||typeof u!=='object')return null;
  var n=function(v){ return v==null||v===''||!isFinite(+v)?null:Math.round(+v*10)/10; };
  var o={req:n(u.req),used:n(u.used),need:n(u.need)};
  return o.req==null&&o.used==null&&o.need==null?null:o;
}
function auditRow(b){
  var label=String(b.label||'').replace(/\s+/g,' ').trim().slice(0,160);
  return { label:DPR_PII.test(label)?'':label, status:['satisfied','not','in_progress','unknown'].indexOf(b.status)>=0?b.status:'unknown',
    kind:/^(ge|conc|units|gwr|uscp|gpa|elective|major)$/.test(b.kind||'')?b.kind:null, ge:/^[A-Z0-9]{1,4}$/.test(b.ge||'')?b.ge:null,
    level:/^(RG|RQ|LN)$/.test(b.level||'')?b.level:null, code:/^R[G\d]*-\d{1,6}$/.test(b.code||'')?b.code:null,
    units:auditNums(b.units), courses:auditNums(b.courses), options:(b.options||[]).filter(function(c){ return /^[A-Z]{2,5} \d{3,4}[A-Z]{0,2}$/.test(c); }).slice(0,60), oneOf:!!b.oneOf,
    used:(b.used||[]).filter(function(e){ return e&&AUDIT_USED.test(e.c||'')&&AUDIT_TERM.test(e.t||''); }).slice(0,40).map(function(e){ var o={c:e.c,t:e.t}; if(e.n&&AUDIT_CODE.test(e.n))o.n=e.n; if(e.x)o.x=true; if(e.p)o.p=true; return o; }),
    listed:(b.listed||[]).filter(function(c){ return AUDIT_CODE.test(c); }).slice(0,10) };
}
/* the report's header words (catalog, major, concentration): checked like a line's, and no longer than the table takes */
function auditWords(v,n){ v=String(v||'').replace(/\s+/g,' ').trim().slice(0,n); return v&&!DPR_PII.test(v)?v:null; }
function auditFrom(row){
  if(!row)return null;
  var reqs=Array.isArray(row.requirements)?row.requirements:[];
  var n={satisfied:0,not:0,in_progress:0,unknown:0}; reqs.forEach(function(b){ n[b.status]=(n[b.status]||0)+1; });
  return { reqs:reqs, counts:n, catalog:row.catalog||'', major:row.major||'', conc:row.concentration||'', units_used:row.units_used, units_needed:row.units_needed,
    read_at:row.read_at||null, printed_on:row.printed_on||null, overrides:Array.isArray(row.overrides)?row.overrides:[] };
}
function auditStoreLocal(o){ try{ localStorage.setItem(auditKey(),JSON.stringify(o)); }catch(e){} }
async function loadAudit(){
  if(typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return;
  var uid=sbUser.id;
  AUDIT=null; AUDIT_UID=uid; AUDIT_LOCAL=false; AUDIT_LOADED=false;
  var c=null; try{ c=JSON.parse(localStorage.getItem(auditKey())||'null'); if(c&&c.requirements){ AUDIT=auditFrom(c); AUDIT_LOCAL=true; } }catch(e){}
  var r; try{ r=await sb.from('degree_audit').select('printed_on,catalog,major,concentration,units_used,units_needed,requirements,overrides,read_at').eq('user_id',uid).maybeSingle(); }catch(e){ r={error:{message:String(e)}}; }
  if(!sbUser||sbUser.id!==uid)return;
  if(r.error){ AUDIT_ERR=schemaGap(r.error)?'missing':(r.error.message||'error'); return; }
  AUDIT_ERR=null; AUDIT_LOADED=true;
  /* what this device saved while the account couldn't be reached goes up now: a report read, or marks */
  if(c&&c.requirements&&c.pending&&(!r.data||!r.data.read_at||(c.read_at||'')>r.data.read_at)){
    AUDIT=auditFrom(c); AUDIT_LOCAL=true;
    var up=Object.assign({},c); delete up.pending; delete up.ovPending; up.user_id=uid;
    /* the account's marks stand unless this device has marks of its own waiting to go up */
    if(!c.ovPending){ delete up.overrides; AUDIT.overrides=(r.data&&Array.isArray(r.data.overrides))?r.data.overrides:(c.overrides||[]); }
    var q=await sb.from('degree_audit').upsert(up,{onConflict:'user_id'});
    if(!q.error){ AUDIT_LOCAL=false; auditStoreLocal(Object.assign({},up,{overrides:AUDIT.overrides})); }
    return;
  }
  if(r.data){ AUDIT=auditFrom(r.data); AUDIT_LOCAL=false;
    if(c&&c.ovPending&&Array.isArray(c.overrides)){ AUDIT.overrides=c.overrides; auditSaveOverrides(c.overrides); } }
}
/* once per account, beside the record (loadMyHistory); repaints Past classes when it lands */
var AUDIT_ASKED=null;
function auditEnsure(){
  if(typeof sbUser==='undefined'||!sbUser||AUDIT_ASKED===sbUser.id)return;
  var uid=sbUser.id; AUDIT_ASKED=uid;
  Promise.all([loadAudit(),loadMarks()]).then(function(){
    /* a read that failed (not a missing table) is asked again the next time the record loads */
    if((AUDIT_ERR&&AUDIT_ERR!=='missing')||(MARKS_ERR&&MARKS_ERR!=='missing'))AUDIT_ASKED=null;
    try{ if(typeof plRenderRecord==='function')plRenderRecord(); }catch(e){} });
}
/* the lines of a parsed report as they'll be stored: flagged lines out, each line through auditRow */
function auditStoredReqs(a){ return (a&&a.ok&&a.reqs?a.reqs:[]).filter(function(b){ return !b.flag; }).map(auditRow).filter(function(b){ return b.label||b.options.length; }); }
/* (phone TC.saveAudit) null when saved, or what to tell the student */
async function saveAudit(a,prog){
  if(typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return null;
  if(AUDIT_UID!==sbUser.id)await loadAudit();
  var reqs=auditStoredReqs(a);
  var num=function(v){ return v==null||!isFinite(+v)?null:Math.round(+v*10)/10; };
  var old=curAudit();
  window._rfDiff=auditDiff(old,a);
  var row={ user_id:sbUser.id, printed_on:(a&&/^\d{4}-\d{2}-\d{2}$/.test(a.printed||''))?a.printed:null, catalog:auditWords(prog&&prog.catalog,80), major:auditWords(prog&&prog.major,120), concentration:auditWords(prog&&prog.conc,120),
    units_used:num(a&&a.units_used), units_needed:num(a&&a.units_needed), requirements:reqs, read_at:new Date().toISOString(),
    /* what the student marked done stays marked through a new upload */
    overrides:(old&&Array.isArray(old.overrides))?old.overrides:[] };
  auditStoreLocal(Object.assign({pending:true},row));
  AUDIT=auditFrom(row); AUDIT_UID=sbUser.id; AUDIT_LOCAL=true;
  if(AUDIT_ERR==='missing')return null;
  /* marks are only written when this session read them: a failed read never blanks them on the account */
  var up=Object.assign({},row); if(!AUDIT_LOADED)delete up.overrides;
  var q; try{ q=await sb.from('degree_audit').upsert(up,{onConflict:'user_id'}); }catch(e){ q={error:{message:String(e)}}; }
  if(q.error){ if(schemaGap(q.error)){ AUDIT_ERR='missing'; return null; } return 'Couldn’t save what your report says — it’s kept on this device for now.'; }
  auditStoreLocal(row); AUDIT_LOCAL=false; return null;
}
/* (phone TC.saveOverrides) lines the student marked done: {code, label, at} — the line's code, or its words */
async function auditSaveOverrides(list){
  var A0=curAudit(); if(!A0)return 'Upload your report first.';
  list=(list||[]).slice(0,100).map(function(o){ var label=String(o.label||'').replace(/\s+/g,' ').trim().slice(0,160);
    return {code:/^R[G\d]*-\d{1,6}$/.test(o.code||'')?o.code:null, label:DPR_PII.test(label)?'':label, at:o.at||new Date().toISOString()}; }).filter(function(o){ return o.code||o.label; });
  A0.overrides=list;
  var keep=function(pending){ try{ var c=JSON.parse(localStorage.getItem(auditKey())||'null')||{user_id:sbUser.id,catalog:A0.catalog||null,major:A0.major||null,concentration:A0.conc||null,units_used:A0.units_used,units_needed:A0.units_needed,requirements:A0.reqs,read_at:A0.read_at};
    c.overrides=list; if(pending)c.ovPending=true; else delete c.ovPending; auditStoreLocal(c); }catch(e){} };
  keep(true);
  if(AUDIT_ERR==='missing'||AUDIT_LOCAL)return null;
  var q; try{ q=await sb.from('degree_audit').update({overrides:list}).eq('user_id',sbUser.id); }catch(e){ q={error:{message:String(e)}}; }
  if(q.error)return schemaGap(q.error)?null:'Couldn’t save that to your account — it’s kept on this device and goes up next time.';
  keep(false); return null;
}
/* (phone TC.flagDprLine) a line the student flagged as read wrong, de-identified: its words, verdict and counts */
async function dprFlagLine(b,prog){
  var x=auditRow(b);
  var row={who_hash:'', major:auditWords(prog&&prog.major,120), catalog:auditWords(prog&&prog.catalog,80), label:x.label||'(no words)', status:b.status==='row'?'row':x.status, units:x.units};
  try{ var q=await sb.from('dpr_flags').insert(row); return !q.error; }catch(e){ return false; }
}

/* ---- 2. GE areas and units (phone plGeMap, unitsOf, GE_QTR, plGeArea, geSubj, plGeBar) ---- */
var PL_GE=null;
function plGeMap(){
  var G=(typeof GE_COURSES!=='undefined'&&GE_COURSES)||[];
  if(PL_GE&&PL_GE.src===G&&PL_GE.n===G.length)return PL_GE.m;
  var m=new Map();
  G.forEach(function(g){ if(!g||!g.areaKey)return; var c=canonCode(g.code)||g.code, a=m.get(c)||[]; if(a.indexOf(g.areaKey)<0)a.push(g.areaKey); m.set(c,a); });
  PL_GE={src:G,n:G.length,m:m};
  return m;
}
/* Units of a class, from what the app can vouch for: a flowchart's slot (mm: a major's terms), then the GE list. */
function auditUnitsOf(code,mm){
  var k=canonCode(code)||code, K=function(c){ return canonCode(c)||c; };
  if(mm)for(var i=0;i<(mm.terms||[]).length;i++){ var sl=mm.terms[i].slots||[]; for(var j=0;j<sl.length;j++){ var s=sl[j]; if(s.units==null)continue;
    if((s.code&&K(s.code)===k)||(s._opts&&s._opts.some(function(c){ return K(c)===k; }))||(s.options&&s.options.some(function(c){ return K(c)===k; })))return +s.units||null; } }
  var g=((typeof GE_COURSES!=='undefined'&&GE_COURSES)||[]).find(function(x){ return K(x.code)===k; });
  return g&&g.units?+g.units:null;
}
/* A report line's GE area(s) in the app's semester vocabulary (the registrar's quarter-to-semester GE sheet). */
var GE_QTR={A1:['1C'],A2:['1A'],A3:['1B'],B1:['5A'],B2:['5B'],B3:['5C'],B4:['2'],BUD:['U25'],C1:['3A'],C2:['3B'],CUD:['UD3'],D1:['4A'],D2:['4B'],DUD:['UD4'],E:['4B'],F:['6'],
  '1A':['1A'],'1B':['1B'],'1C':['1C'],2:['2'],'3A':['3A'],'3B':['3B'],'4A':['4A'],'4B':['4B'],'5A':['5A'],'5B':['5B'],'5C':['5C'],6:['6'],U25:['U25'],UD3:['UD3'],UD4:['UD4']};
function plGeArea(b){
  if(!b||b.kind!=='ge')return [];
  if(b.ge&&GE_QTR[b.ge])return GE_QTR[b.ge];
  var l=String(b.label||'').replace(/^GE\s+/i,'');
  if(/\(\s*GE\b[^)]*\)\s*$/i.test(l))return [];
  if(/^(?:Area\s*2\s*or\s*5\s*:\s*(?:UD|Upper)|UD\s*2\s*\/\s*5\b|Upper[- ]division (?:Scientific|Science|Math))/i.test(l))return ['U25'];
  if(/^(?:Area\s*3\s*:\s*(?:UD|Upper)|UD\s*3\b|Upper[- ]division Arts)/i.test(l))return ['UD3'];
  if(/^(?:Area\s*4\s*:\s*(?:UD|Upper)|UD\s*4\b|Upper[- ]division Social)/i.test(l))return ['UD4'];
  if(/^Lower[- ]division C Elective\b/i.test(l))return ['3A','3B'];
  if(/^Electives?\b.*\bAreas? B, C,? and D\b/i.test(l))return ['2','5A','5B','5C','3A','3B','4A','4B','U25','UD3','UD4'];
  if(/^(?:Area\s+)?B\s+Electives?\b/i.test(l))return ['5A','5B','5C'];
  return [];
}
function geSubj(c){ return String(c||'').trim().split(/\s+/)[0].toUpperCase(); }
/* "All three lower division C courses must come from three different course prefixes": true = barred */
function plGeBar(b,code,reqs){
  if(!b||!/^(?:GE\s+)?Lower[- ]division C Elective\b/i.test(String(b.label||'')))return false;
  var used={}, A=curAudit();
  (reqs||(A&&A.reqs)||[]).forEach(function(x){ if(x===b||/^(C1|C2)$/.test(x.ge||'')||/^(?:GE\s+)?C[12]\s*:/i.test(String(x.label||'')))(x.used||[]).forEach(function(e){ used[geSubj(e.c)]=1; if(e.n)used[geSubj(e.n)]=1; }); });
  return !!used[geSubj(code)];
}

/* ---- the report's lines, counted one way everywhere (phone auditIsTotal … auditNum) ---- */
function auditIsTotal(b){ return !!b&&b.kind==='units'&&/total units|units for the degree/i.test(b.label||''); }
function auditOvMatch(o,b){ return !!(o&&b&&(o.code?o.code===b.code:(!b.code&&!!o.label&&o.label===b.label))); }
function auditOverrides(){ var A=curAudit(); return (A&&Array.isArray(A.overrides))?A.overrides:[]; }
function auditLines(a,L){
  if(!a||!Array.isArray(a.reqs)||!a.reqs.length)return null;
  var k=function(c){ return canonCode(c)||c; };
  var mine=[]; try{ mine=myTakingCodes().slice(); }catch(e){}
  var mineK={}; mine.forEach(function(c){ mineK[k(c)]=1; });
  var GE=plGeMap(), A=curAudit();
  var live=a.reqs.filter(function(b){ return b&&!b.flag; }), covered=new Map(), qtr=/quarter/i.test(a.catalog||(A&&A.catalog)||''), spent={}, placed={};
  live.forEach(function(b){ (b.used||[]).forEach(function(e){ placed[k(e.c)]=1; if(e.n)placed[k(e.n)]=1; }); });
  live.forEach(function(b){
    if(b.status!=='not'||auditIsTotal(b))return;
    if(b.courses&&b.courses.need!=null&&+b.courses.need>1)return;
    var by=(b.options||[]).find(function(c){ return mineK[k(c)]; });
    /* by area: only a line the report put no class under, only a class the report placed nowhere, one class for one line */
    if(!by&&b.kind==='ge'&&!(b.used||[]).length){ var areas=plGeArea(b); if(areas.length)by=mine.find(function(c){ return !placed[k(c)]&&!spent[k(c)]&&!plGeBar(b,c,a.reqs)&&(GE.get(k(c))||[]).some(function(x){ return areas.indexOf(x)>=0; }); }); }
    if(!by)return;
    var u=auditUnitsOf(by,L);
    if(b.units&&b.units.need!=null&&u!=null&&(qtr?u*1.5:u)<+b.units.need)return;
    covered.set(b,by); spent[k(by)]=1;
  });
  /* the registrar prints "Satisfied" for a class still being taken: such a line is in progress */
  var now=new Set(live.filter(function(b){ return b.status==='satisfied'&&(b.used||[]).some(function(e){ return !e.x&&e.p; }); }));
  var ovs=auditOverrides(), manual=new Set(live.filter(function(b){ return (b.status==='not'||b.status==='unknown')&&ovs.some(function(o){ return auditOvMatch(o,b); }); }));
  var open=live.filter(function(b){ return b.status==='not'&&!covered.has(b)&&!manual.has(b); });
  return { live:live, covered:covered, manual:manual, now:now, open:open, unknown:live.filter(function(b){ return b.status==='unknown'&&!manual.has(b); }),
    filled:live.filter(function(b){ return b.status==='satisfied'||b.status==='in_progress'||covered.has(b)||manual.has(b); }),
    inprog:live.filter(function(b){ return b.status==='in_progress'||covered.has(b)||now.has(b); }), total:live.find(auditIsTotal)||null };
}
function auditTag(b){
  var t=function(x,c){ return '<span class="rf-tag '+c+'">'+escapeHtml(x)+'</span>'; };
  if(b.status==='unknown')return t('?','t-plain');
  if(b.kind==='ge')return t(b.ge?'GE '+b.ge:'GE','t-purple');
  if(b.kind==='conc')return t('Conc.','t-teal');
  if(b.kind==='units')return t(/upper/i.test(b.label||'')?'UD':'Units','t-amber');
  if(b.kind==='gwr')return t('GWR','t-amber');
  if(b.kind==='uscp')return t('USCP','t-purple');
  if(b.kind==='gpa')return t('GPA','t-plain');
  if(b.kind==='elective')return t('Elective','t-blue');
  if(b.oneOf||(b.courses&&b.courses.req===1&&(b.options||[]).length>1))return t('Pick 1','t-blue');
  return t('Major','t-blue');
}
function auditNum(v){ return String(+(+v).toFixed(1)).replace(/\.0$/,''); }
/* (phone auditDiff) what a new report changes against the one on the account; null = no report before */
function auditDiff(old,a){
  var O=old&&old.reqs&&old.reqs.length?auditLines(old,null):null;
  var N=a&&a.ok?auditLines({reqs:auditStoredReqs(a),catalog:a.catalog||'',overrides:(old&&old.overrides)||[]},null):null;
  if(!O||!N)return null;
  var k=function(c){ return canonCode(c)||c; }, done=function(b){ return b.status==='satisfied'||b.status==='in_progress'; };
  var keys=function(X){ var n={}; return new Map(X.live.map(function(b){ var w=b.code||b.label; n[w]=(n[w]||0)+1; return [b,w+'#'+n[w]]; })); };
  var kO=keys(O), kN=keys(N), was=new Map(O.live.map(function(b){ return [kO.get(b),b]; })), now=new Map(N.live.map(function(b){ return [kN.get(b),b]; }));
  var filled=N.live.filter(function(b){ return done(b)&&was.has(kN.get(b))&&was.get(kN.get(b)).status==='not'; }).map(function(b){ return b.label; });
  var opened=N.live.filter(function(b){ return b.status==='not'&&was.has(kN.get(b))&&done(was.get(kN.get(b))); }).map(function(b){ return b.label; });
  var added=N.live.filter(function(b){ return !was.has(kN.get(b)); }).length;
  /* a plan's class "is done now" only when the open line it filled is now Satisfied / In Progress */
  var doneNow={}; O.live.filter(function(b){ return b.status==='not'&&!O.manual.has(b); }).forEach(function(b){ var nb=now.get(kO.get(b)); if(nb&&done(nb))(b.options||[]).forEach(function(c){ doneNow[k(c)]=1; }); });
  var stillOpen={}; N.open.forEach(function(b){ (b.options||[]).forEach(function(c){ stillOpen[k(c)]=1; }); });
  var affected={};
  try{ if(window.TCPlans)(TCPlans.slots||[]).forEach(function(P){ var codes=[]; ((TCPlans.get(P)||{}).sections||[]).forEach(function(s){ var c=s&&s.code; if(c&&doneNow[k(c)]&&!stillOpen[k(c)]&&codes.indexOf(c)<0)codes.push(c); }); if(codes.length)affected[P]=codes; }); }catch(e){}
  return {filled:filled, opened:opened, added:added, affected:affected, same:!filled.length&&!opened.length&&!added};
}

/* ---- 5. the report wins (phone dprRecompute, dprStale, dprRcCard, TC.dropStale) ---- */
function rfK(c){ try{ return canonCode(c)||c; }catch(e){ return c; } }
/* "Already on your record" = the same class in the same term (or a row with no term). By number alone, an older
   import's wrong row hid the class you're taking now. Classes in progress or registered are My Classes' business. */
function dprRecompute(rows){
  var H=(typeof myHistory!=='undefined'&&myHistory)||[];
  (rows||[]).forEach(function(x){
    if(!x||!x._dpr||x._fail||x._later)return;
    if(x._now||x._reg){ if(x.already){ x.already=false; x.pick=true; } return; }
    x.already=H.some(function(h){ return h&&(rfK(h.code)===rfK(x.cur)||rfK(h.code)===rfK(x.code))&&(!h.term||!h.year||(h.term===x.term&&String(h.year)===String(x.year))); });
    x.pick=!x.already;
  });
}
function rfXfer(h){ try{ var s=pcReadSource(h&&h.professor); return !!(s&&s.src&&s.src.mark); }catch(e){ return false; } }
/* What's on your account but not on your report: it comes off when you save — unless you uncheck it. This term's
   classes only when the report shows this term (it lists what you're taking). Never your Spring list. */
function dprStale(rows){
  var all=(rows||[]).filter(function(x){ return x&&x._dpr; }), keep=all.filter(function(x){ return !x._fail||x._prov; });
  var same=function(x,h){ return rfK(x.cur)===rfK(h.code)||rfK(x.code)===rfK(h.code); };
  var out=[];
  ((typeof myHistory!=='undefined'&&myHistory)||[]).forEach(function(h){
    if(!h||!h.code)return;
    if(keep.some(function(x){ return same(x,h)&&(h.term&&h.year?(x.term===h.term&&String(x.year)===String(h.year)):!(x.term&&x.year)); }))return;
    var other=keep.find(function(x){ return same(x,h); }), at=h.term&&h.year?('as '+h.term+' '+h.year):'with no term';
    var bad=!other&&all.some(function(x){ return x._fail&&same(x,h); });
    var why=bad?('On your account '+at+' · your report shows it not passed')
      :other?('On your account '+at+' · your report has it '+other.term+' '+other.year+(other._now?' (this term)':''))
      :rfXfer(h)?'Credit on your account · not on your report':('On your account '+at+' · not on your report');
    out.push({key:'h:'+rfK(h.code)+'|'+(h.term||'')+'|'+(h.year||''), kind:'hist', h:h, code:rfK(h.code), why:why});
  });
  /* the report shows the term you're in only when it has rows of that term in progress */
  var nowRep=keep.filter(function(x){ return x._now&&(x.term+' '+x.year)===mcNowLabel(); });
  if(nowRep.length){
    var want={}; nowRep.forEach(function(x){ want[rfK(x.cur||x.code)]=1; });
    var seen={};
    ((typeof nowMine==='function'?nowMine().classes:[])||[]).forEach(function(c){ var k=rfK(c); if(seen[k]||want[k])return; seen[k]=1;
      out.push({key:'n:'+k, kind:'now', code:k, raw:c, why:'In My Classes for '+mcNowLabel()+' · your report doesn’t show you taking it'}); });
  }
  return out;
}
function rfAfterRead(dpr){
  var M=window._dprMeta; if(!M)return;
  M.audit=dpr.audit||null; M.rcOff={}; M.flagged=0; M.checkOpen=false;
  dprRecompute(tiRows);
  M.rc=dprStale(tiRows);
}
window.rfStaleToggle=function(key,on){ var M=window._dprMeta; if(!M)return; M.rcOff=M.rcOff||{}; if(on)delete M.rcOff[key]; else M.rcOff[key]=1; };
function rfStaleCard(){
  var M=window._dprMeta, rc=(M&&M.rc)||[]; if(!rc.length)return '';
  var off=M.rcOff||{}, n=rc.filter(function(x){ return !off[x.key]; }).length;
  return '<div class="rf-rc" role="group" aria-label="On your account, not on your report"><div class="rf-rch">'+rc.length+' on your account, not on your report</div>'
    +'<div class="rf-rcs">Your report decides. We’ll take the checked '+(n===1?'one':'ones')+' off so your account matches it.</div>'
    +rc.map(function(x){ var nm=''; try{ nm=(typeof fp_name==='function'&&fp_name(x.code))||''; }catch(e){}
      return '<label class="rf-rcr"><input type="checkbox" '+(off[x.key]?'':'checked ')+'onchange="rfStaleToggle(\''+jsAttr(x.key)+'\',this.checked)">'
        +'<span class="rf-rct"><b>'+escapeHtml(x.code)+(nm?' · '+escapeHtml(nm):'')+'</b><span>'+escapeHtml(x.why)+'</span></span></label>'; }).join('')+'</div>';
}
/* (phone TC.dropStale) the checked ones come off; {n} or {err} */
async function rfDropStale(){
  var M=window._dprMeta, list=((M&&M.rc)||[]).filter(function(x){ return !(M.rcOff||{})[x.key]; });
  if(!list.length||typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return {n:0};
  var me=sbUser.id, nt=mcNowTerm(), two=mcTwoTerms(), done=0;
  for(var i=0;i<list.length;i++){
    var x=list[i], q;
    if(x.kind==='hist'){ q=sb.from('class_history').delete().eq('user_id',me).eq('code',x.h.code); q=x.h.term?q.eq('term',x.h.term):q.is('term',null); q=x.h.year?q.eq('year',x.h.year):q.is('year',null); }
    else q=sb.from('saved_classes').delete().eq('user_id',me).eq('term',nt).eq('code',x.raw);
    var d; try{ d=await q; }catch(e){ d={error:{message:String(e)}}; }
    if(d.error){ try{ await loadMyHistory(); }catch(e){} return {n:done,err:'Couldn’t take '+x.code+' off your account — nothing was added. Try again.'}; }
    if(x.kind==='now'){
      try{ await sb.from('my_sections').delete().eq('user_id',me).eq('term',nt).eq('code',x.raw); }catch(e){}
      try{
        if(two){ var j=NOW_MINE.classes.indexOf(x.raw); if(j>=0)NOW_MINE.classes.splice(j,1); delete NOW_MINE.meta[x.raw]; try{ localStorage.setItem(nowMineKey(),JSON.stringify(NOW_MINE)); }catch(e){} }
        else{ var j2=myClasses.indexOf(x.raw); if(j2>=0)myClasses.splice(j2,1); if(myClassMeta&&myClassMeta[x.raw]){ delete myClassMeta[x.raw]; try{ saveMyClassMeta(); }catch(e){} } try{ saveMyClasses(); }catch(e){} }
      }catch(e){}
    }
    done++;
  }
  /* a row that came off because the report dates it differently is saved again with the report's term */
  var was=tiRows.filter(function(r){ return r&&r._dpr&&r.already; });
  try{ await loadMyHistory(); }catch(e){}
  dprRecompute(was);
  M.rc=[];
  try{ if(two)nowAfterLoad(); else if(typeof renderMyClasses==='function')renderMyClasses(); }catch(e){}
  return {n:done};
}

/* ---- 6. what the report says, on the review list ---- */
function rfFmtDate(iso){ try{ return new Date(iso+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}); }catch(e){ return iso; } }
function rfReadLines(){ var M=window._dprMeta, a=M&&M.audit; return a&&a.ok?auditLines(a,null):null; }
function rfCountsText(X){ return X.filled.length+' filled · '+X.open.length+' left'+(X.unknown.length?' · '+X.unknown.length+' can’t check':''); }
/* the classes a line used, as the report printed them: "BUS 214 → BUS 2214 · Winter 2025" */
function rfUsedText(e){ return e.c+(e.n&&e.n!==e.c?' → '+e.n:'')+(e.t?' · '+e.t:'')+(e.x?' · transfer credit':e.p?' · this term':''); }
function rfVerdict(b,X){
  if(X.manual.has(b))return 'marked done';
  if(b.status==='unknown')return 'can’t check';
  if(X.covered.has(b))return 'taking '+X.covered.get(b);
  if(b.status==='in_progress'||X.now.has(b))return 'in progress';
  if(b.status==='satisfied')return 'filled';
  if(b.units&&b.units.need!=null)return auditNum(b.units.need)+(+b.units.need===1?' unit':' units')+' left';
  if(b.courses&&b.courses.need!=null)return auditNum(b.courses.need)+(+b.courses.need===1?' class':' classes')+' left';
  return 'open';
}
function rfReportHead(){
  var M=window._dprMeta, a=M&&M.audit; if(!a||!a.ok)return '';
  var X=rfReadLines(); if(!X)return '';
  var prog=M.program||{};
  var cat=prog.catalog?('Your catalog: '+prog.catalog+(a.printed?' · report printed '+rfFmtDate(a.printed):'')):(a.printed?'Report printed '+rfFmtDate(a.printed):'');
  var all=(a.reqs||[]).map(function(b,i){ return {b:b,i:i}; }).filter(function(o){ return o.b&&(o.b.label||(o.b.options||[]).length); });
  var line=function(o){ var b=o.b, live=!b.flag;
    var used=(b.used||[]).slice(0,4).map(function(e){ return '<span class="rf-cu">'+escapeHtml(rfUsedText(e))+'</span>'; }).join('')+((b.used||[]).length>4?'<span class="rf-cu">+'+((b.used||[]).length-4)+' more</span>':'');
    return '<div class="rf-cl'+(live?'':' flagged')+'">'+auditTag(b)+'<span class="rf-clx"><span class="rf-cll">'+escapeHtml(b.label||'Requirement')+'</span>'+(used?'<span class="rf-cus">'+used+'</span>':'')+'</span>'
      +'<span class="rf-clv">'+escapeHtml(live?rfVerdict(b,X):'left out')+'</span>'
      +'<button type="button" class="rf-flag'+(b.flag?' on':'')+'" aria-pressed="'+(!!b.flag)+'" onclick="rfFlag('+o.i+')">'+(b.flag?'Flagged':'Flag')+'</button></div>'; };
  return '<div class="rf-read" id="rfRead"><div class="rf-cnt" id="rfCnt">'+escapeHtml(rfCountsText(X))+'</div>'
    +(cat?'<div class="rf-cat">'+escapeHtml(cat)+'</div>':'')
    +'<details class="rf-check"'+(M.checkOpen?' open':'')+' ontoggle="window._dprMeta&&(window._dprMeta.checkOpen=this.open)"><summary>Check what was read</summary>'
    +'<div class="rf-cls">'+all.map(line).join('')+'</div></details></div>';
}
/* a line read wrong: struck through, left out of the counts and of what's saved, and sent (de-identified) on save */
window.rfFlag=function(i){
  var M=window._dprMeta, a=M&&M.audit, b=a&&a.reqs&&a.reqs[i]; if(!b)return;
  b.flag=!b.flag;
  var box=document.getElementById('rfRead');
  if(box){ var keep=box.querySelector('details'); var open=keep&&keep.open; var d=document.createElement('div'); d.innerHTML=rfReportHead(); var nb=d.firstChild; if(nb){ var det=nb.querySelector('details'); if(det&&open)det.open=true; box.replaceWith(nb); } }
};

/* ---- 5 (cont.) the diff after a save, and the Plans it touches (phone SHEETS.dprDiff) ---- */
function rfDiffEl(){
  var b=document.getElementById('rfDiffBack');
  if(!b){ b=document.createElement('div'); b.className='mback'; b.id='rfDiffBack'; b.setAttribute('onclick','if(event.target===this)closeDprDiff()'); b.innerHTML='<div class="modal rf-diff" id="rfDiffModal"></div>'; document.body.appendChild(b);
    try{ if(typeof A11Y_MODALS!=='undefined'&&!A11Y_MODALS.some(function(m){ return m.id==='rfDiffBack'; }))A11Y_MODALS.push({id:'rfDiffBack',close:'closeDprDiff'}); }catch(e){} }
  return b;
}
function rfDiffHtml(d){
  var li=function(t){ return '<li>'+escapeHtml(t)+'</li>'; }, aff=Object.keys(d.affected||{});
  return '<button class="auth-x" style="float:right" aria-label="Close" onclick="closeDprDiff()">&times;</button>'
    +'<div class="rate-kicker">Degree Progress Report</div><h3 style="margin:4px 0 12px">Your report changed</h3>'
    +(d.filled.length?'<div class="rf-dh">Now filled <em>'+d.filled.length+'</em></div><ul class="rf-dl">'+d.filled.slice(0,8).map(li).join('')+(d.filled.length>8?'<li class="rf-dmore">+'+(d.filled.length-8)+' more</li>':'')+'</ul>':'')
    +(d.opened.length?'<div class="rf-dh">Open again <em>'+d.opened.length+'</em></div><ul class="rf-dl">'+d.opened.slice(0,8).map(li).join('')+(d.opened.length>8?'<li class="rf-dmore">+'+(d.opened.length-8)+' more</li>':'')+'</ul>':'')
    +(d.added?'<div class="rf-dh">New on this report <em>'+d.added+'</em></div><p class="rf-dp">'+d.added+' line'+(d.added===1?'':'s')+' this report prints that the last one didn’t.</p>':'')
    +(aff.length?'<div class="rf-dh">Your plans</div><p class="rf-dp">These classes filled something you needed before. Your report now says that’s done.</p>'
      +aff.map(function(P){ return d.affected[P].map(function(code){ return '<div class="rf-dpl"><span>Plan '+escapeHtml(P)+' · '+escapeHtml(code)+'</span><button type="button" class="plr-btn" onclick="rfDiffDrop(\''+jsAttr(P)+'\',\''+jsAttr(code)+'\',this)">Take it out</button></div>'; }).join(''); }).join(''):'')
    +'<div class="si-actions" style="margin-top:16px;justify-content:flex-end"><button class="btn primary" onclick="closeDprDiff()">Done</button></div>';
}
function rfShowDiff(d){
  if(!d||d.same)return false;
  var b=rfDiffEl(); document.getElementById('rfDiffModal').innerHTML=rfDiffHtml(d);
  window._rfDiffShown=d; b.classList.add('open'); document.body.style.overflow='hidden';
  try{ openModalA11y('rfDiffBack'); }catch(e){}
  return true;
}
window.closeDprDiff=function(){
  var b=document.getElementById('rfDiffBack'); if(b)b.classList.remove('open'); document.body.style.overflow='';
  window._rfDiffShown=null;
  try{ if(a11yLastFocus&&a11yLastFocus.focus)a11yLastFocus.focus(); }catch(e){}
  if(window._rfAfterDiff){ window._rfAfterDiff=false; setTimeout(function(){ try{ if(typeof rsOpen==='function')rsOpen('dpr'); }catch(e){} },300); }
};
window.rfDiffDrop=function(P,code,btn){
  try{ var secs=((TCPlans.get(P)||{}).sections||[]).filter(function(s){ return rfK(s.code)!==rfK(code); }); TCPlans.setSections(P,secs); }catch(e){ return; }
  var d=window._rfDiffShown; if(d&&d.affected&&d.affected[P]){ d.affected[P]=d.affected[P].filter(function(c){ return c!==code; }); if(!d.affected[P].length)delete d.affected[P]; }
  try{ frToast('Took '+code+' out of Plan '+P+'.'); }catch(e){}
  if(d)document.getElementById('rfDiffModal').innerHTML=rfDiffHtml(d);
};
/* the save's report half, run by confirmDprImport after the classes: the verdicts kept, flags sent; notes for the toast */
async function rfSaveReport(){
  var M=window._dprMeta, notes=[]; window._rfDiff=null;
  if(!M||!M.audit||!M.audit.ok)return notes;
  var e2=await saveAudit(M.audit,M.program); if(e2)notes.push(e2);
  var flagged=(M.audit.reqs||[]).filter(function(b){ return b.flag; });
  if(flagged.length){ var sent=await Promise.all(flagged.map(function(b){ return dprFlagLine(b,M.program); })); if(!sent.every(Boolean))notes.push('The flags couldn’t be sent — those lines are still left out.'); }
  if(!e2&&window._rfDiff&&window._rfDiff.same)notes.push('Your report says the same as before.');
  if(e2)window._rfDiff=null;
  return notes;
}

/* ---- 7. Past classes by requirement (phone pastView, pcDone, pcLeft, pcReqRow, pcReportView) ---- */
var RF_GROUPS=[['major','Major and support'],['conc','Concentration'],['ge','General education'],['degree','Degree requirements']];
function rfGroupOf(b){ return b.kind==='ge'?'ge':b.kind==='conc'?'conc':/^(units|gpa|gwr|uscp)$/.test(b.kind||'')?'degree':'major'; }
window._rfOpen=window._rfOpen||{};
function rfFold(key,head,body,cls){
  return '<details class="rf-fold'+(cls?' '+cls:'')+'"'+(window._rfOpen[key]?' open':'')+' ontoggle="window._rfOpen[\''+key+'\']=this.open"><summary>'+head+'</summary>'+body+'</details>';
}
function rfReqRow(b,X,i){
  var st=X.manual.has(b)?'done':(X.covered.has(b)||X.now.has(b))?'taking':b.status==='satisfied'?'done':b.status==='in_progress'?'taking':b.status==='not'?'need':'cant';
  var dot={done:'✓',taking:'',need:'',cant:'?'}[st], lab={done:'Filled',taking:'In progress',need:'Still needed',cant:'Can’t check'}[st];
  var mine=X.manual.has(b), sub='';
  /* a line that is one class ("BUS 2201") says which class that is */
  var nm=''; if(AUDIT_CODE.test(b.label||''))try{ nm=(typeof fp_name==='function'&&fp_name(rfK(b.label)))||''; }catch(e){}
  if(st==='done'||st==='taking'){
    var u=b.used||[];
    sub=u.slice(0,3).map(function(e){ return '<span class="rf-used">'+escapeHtml(rfUsedText(e))+'</span>'; }).join('')+(u.length>3?'<span class="rf-used">+'+(u.length-3)+' more</span>':'');
    if(!u.length&&X.covered.has(b))sub='<span class="rf-used">Taking '+escapeHtml(X.covered.get(b))+' this term</span>';
  } else if(st==='need'){
    var bits=[b.oneOf&&(b.options||[]).length>1?'pick one of '+b.options.length:'', b.units&&b.units.need?auditNum(b.units.need)+(+b.units.need===1?' unit needed':' units needed'):b.courses&&b.courses.need?auditNum(b.courses.need)+(+b.courses.need>1?' classes needed':' class needed'):''].filter(Boolean);
    sub=(bits.length?'<span class="rf-need">'+escapeHtml(bits.join(' · '))+'</span>':'')
      +((b.listed||[]).length?'<span class="rf-look">Needs a look: your report lists '+escapeHtml(b.listed.slice(0,3).join(', '))+' on your record but didn’t count '+(b.listed.length>1?'them':'it')+' here — ask your advisor</span>':'');
  } else sub='<span class="rf-need">The app couldn’t read this line</span>';
  if(mine)sub+='<span class="rf-mine">Marked done by you</span>';
  var act=st==='need'&&!auditIsTotal(b)?'<button type="button" class="rf-mark" onclick="rfMark('+i+',true)">Mark done</button>':mine?'<button type="button" class="rf-mark" onclick="rfMark('+i+',false)">Undo</button>':'';
  return '<div class="rf-row '+st+((b.listed||[]).length&&st==='need'?' look':'')+'"><span class="rf-dot '+st+'" role="img" aria-label="'+lab+'">'+dot+'</span>'
    +'<div class="rf-tx"><div class="rf-l1"><span class="rf-lab">'+escapeHtml(b.label||'Requirement')+'</span>'+(nm?'<span class="rf-nm">'+escapeHtml(nm)+'</span>':'')+auditTag(b)+'</div>'+(sub?'<div class="rf-l2">'+sub+'</div>':'')+'</div>'+act+'</div>';
}
window.rfMark=async function(i,on){
  var A=curAudit(), b=A&&A.reqs&&A.reqs[i]; if(!b)return;
  var list=auditOverrides().filter(function(o){ return !auditOvMatch(o,b); });
  if(on)list.push({code:b.code||null,label:b.label||'',at:new Date().toISOString()});
  try{ plRenderRecord(); }catch(e){}
  var e=await auditSaveOverrides(list);
  try{ plRenderRecord(); }catch(x){}
  if(e)try{ frToast(e); }catch(x){}
};
/* true: drawn; 'old': a report kept before per-line classes — the old screen, and the ask; false: no report */
function rfRenderPast(host,ledHtml){
  var A=curAudit(); if(!A||!A.reqs||!A.reqs.length)return false;
  var X=auditLines(A,null); if(!X)return false;
  if(!X.live.some(function(b){ return Array.isArray(b.used); }))return 'old';
  var idx=new Map(A.reqs.map(function(b,i){ return [b,i]; })), row=function(b){ return rfReqRow(b,X,idx.get(b)); };
  /* the count is requirements; the total-units line is listed ("N units to go") but not counted */
  var items=X.open.concat(X.unknown);
  var ip=X.inprog.filter(function(b){ return items.indexOf(b)<0; });
  var stillHead='<div class="rf-h"><span>Still needed</span><em>'+(X.open.length?X.open.length+' left':'nothing left')+(X.unknown.length?' \u00b7 '+X.unknown.length+' can\u2019t check':'')+'</em></div>';
  var stillBody=(items.length?items.map(row).join(''):'<div class="rf-empty">'+(X.open.length?'Only units left on your report.':'Nothing left on your report.')+'</div>')
    +(ip.length?rfFold('ip','In progress this term <em>'+ip.length+'</em>',ip.map(row).join(''),'rf-ip'):'');
  var left=new Set(items);
  var groups=RF_GROUPS.map(function(g){
    var key=g[0], all=X.live.filter(function(b){ return rfGroupOf(b)===key&&(key!=='degree'||/^(gwr|uscp)$/.test(b.kind||'')); }); if(!all.length)return '';
    var done=all.filter(function(b){ return !left.has(b); }), lab=key==='conc'&&A.conc?escapeHtml(A.conc)+' concentration':g[1];
    var fin=done.length===all.length;
    return rfFold('g-'+key,'<span>'+lab+'</span><em class="'+(fin?'rf-fin':'')+'">'+(fin?'✓ ':'')+done.length+' of '+all.length+' filled</em>',done.length?done.map(row).join(''):'<div class="rf-empty">None filled yet.</div>','rf-grp');
  }).join('');
  /* classes on your record the report used for nothing — units only */
  var usedK={}; X.live.forEach(function(b){ (b.used||[]).forEach(function(e){ usedK[rfK(e.c)]=1; if(e.n)usedK[rfK(e.n)]=1; }); });
  var rest=((typeof myHistory!=='undefined'&&myHistory)||[]).filter(function(h){ return h&&h.code&&!usedK[rfK(h.code)]; });
  var units=rest.length?rfFold('units','<span>Units only</span><em>'+rest.length+' class'+(rest.length===1?'':'es')+'</em>',
    '<div class="rf-uo">'+rest.map(function(h){ var c=rfK(h.code), nm=''; try{ nm=(typeof fp_name==='function'&&fp_name(c))||''; }catch(e){}
      var when=[h.term,h.year].filter(Boolean).join(' '), tag=rfXfer(h)?'transfer credit':(typeof histNotDone==='function'&&histNotDone(h))?'this term':'';
      return '<div class="rf-uor"><b>'+escapeHtml(c)+'</b><span>'+escapeHtml([nm,when,tag].filter(Boolean).join(' · '))+'</span></div>'; }).join('')+'</div>','rf-grp'):'';
  /* the 2026–28 flowchart only for a student on it (a semester catalog); a quarter catalog never sees it */
  var sem=/semester/i.test(A.catalog||'');
  var flow=sem&&ledHtml?rfFold('flow','<span>Your flowchart</span><em>2026–28</em>',ledHtml,'rf-grp'):'';
  var nRec=((typeof myHistory!=='undefined'&&myHistory)||[]).length, open=!!window.plRecordOpen;
  var catChip=A.catalog?'<span class="rf-catc'+(/quarter/i.test(A.catalog)?' q':'')+'">'+escapeHtml(A.catalog)+' catalog</span>':'';
  host.innerHTML='<div class="plr-top rf-top"><div class="rf-who"><b>Your degree report</b>'+catChip
      +'<span class="rf-sum">'+escapeHtml(rfCountsText(X))+(A.printed_on?' · printed '+escapeHtml(rfFmtDate(A.printed_on)):'')+'</span></div>'
    +'<div class="plr-acts"><button type="button" class="plr-btn" onclick="document.getElementById(\'transcriptFile\').click()">Upload a new report</button>'
      +'<button type="button" class="plr-btn" onclick="pcShowManual();try{document.getElementById(\'histCode\').focus();}catch(e){}">Log a class</button></div></div>'
    +'<div class="rf-cols"><section class="rf-col rf-still" aria-label="Still needed">'+stillHead+stillBody+'</section>'
    +'<section class="rf-col rf-done" aria-label="By requirement"><div class="rf-h"><span>By requirement</span></div>'+groups+units+flow
    +(nRec?'<button type="button" class="plr-link rf-all" onclick="plToggleRecord()">'+(open?'Hide every class':'Every class, by term · '+nRec)+'</button>':'')+'</section></div>';
  var sec=document.getElementById('plRecord'); if(sec)sec.classList.toggle('open',open);
  return true;
}

/* ---- 8. flowchart marks on the account (flowchart_marks, RUN 15; phone TC.loadMarks / pushMarks / setMark) ----
   A row of the flowchart with no class the record can check (a GE area, an elective) that you ticked is "marked done by
   you", kept with the account: {major, slot, label} — the row's words, so a mark only ever applies to the row it was made
   on. This device's own ticks (the checklist's professify_sched_done_<major>) go up once per account; from then on the
   account's marks are read, and a tick or untick here is sent as it happens. */
var MY_MARKS=[], MARKS_UID=null, MARKS_ERR=null;
function markOk(m){ return !!(m&&typeof m.major==='string'&&m.major.length>=1&&m.major.length<=120&&/^[A-Za-z0-9_.:-]{1,80}$/.test(String(m.slot||''))); }
function markClean(m){ return {major:m.major, slot:String(m.slot), label:String(m.label||'').slice(0,160)}; }
function rfNormMajor(x){ return String(x||'').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]/g,''); }
/* a row a mark stands for: no class the record can check */
function rfSlotMarkable(sl){ return !!sl&&sl.id!=null&&!(sl.code&&(typeof window.plSlotCheckable!=='function'||window.plSlotCheckable(sl))); }
function rfMarked(major,sl){
  if(!rfSlotMarkable(sl)||typeof sbUser==='undefined'||!sbUser||MARKS_UID!==sbUser.id)return false;
  var mj=rfNormMajor(major), id=String(sl.id), w=String(sl.title||'');
  return MY_MARKS.some(function(m){ return rfNormMajor(m.major)===mj&&m.slot===id&&m.label===w; });
}
function rfMarkedIds(major,m){ var out=[]; ((m&&m.terms)||[]).forEach(function(t){ (t.slots||[]).forEach(function(sl){ if(rfMarked(major,sl))out.push(String(sl.id)); }); }); return out; }
/* this device's ticks on the student's own major, as marks */
function rfDeviceTicks(){
  var out=[], major=(typeof student!=='undefined'&&student&&student.major)||''; if(!major||typeof SCHED_MAJORS==='undefined')return out;
  Object.keys(SCHED_MAJORS).forEach(function(key){
    var mj=SCHED_MAJORS[key]; if(rfNormMajor(mj.name)!==rfNormMajor(major))return;
    var ids=[]; try{ ids=JSON.parse(localStorage.getItem('professify_sched_done_'+key)||'[]'); }catch(e){}
    if(!Array.isArray(ids)||!ids.length)return;
    var m=mj; try{ if(typeof window.schExpandConcPublic==='function')m=window.schExpandConcPublic(mj); }catch(e){}
    var by={}; (m.terms||[]).forEach(function(t){ (t.slots||[]).forEach(function(sl){ by[sl.id]=sl; }); });
    ids.forEach(function(id){ var sl=by[id]; if(!rfSlotMarkable(sl))return; var mk=markClean({major:mj.name,slot:id,label:sl.title||''}); if(markOk(mk))out.push(mk); });
  });
  return out;
}
async function loadMarks(){
  if(typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return;
  var uid=sbUser.id; MARKS_UID=uid; MY_MARKS=[];
  var r; try{ r=await sb.from('flowchart_marks').select('major,slot_id,label').eq('user_id',uid); }catch(e){ r={error:{message:String(e)}}; }
  if(!sbUser||sbUser.id!==uid)return;
  if(r.error){ MARKS_ERR=schemaGap(r.error)?'missing':(r.error.message||'error'); return; }
  MARKS_ERR=null;
  MY_MARKS=(r.data||[]).map(function(x){ return {major:x.major,slot:String(x.slot_id),label:x.label||''}; }).filter(markOk).map(markClean);
  /* once per account: what this device ticked goes up (never deleting anything the account has) */
  var flag='tc-marks-pushed:'+uid, sent=false; try{ sent=localStorage.getItem(flag)==='1'; }catch(e){}
  if(sent||!(typeof student!=='undefined'&&student&&student.major))return;
  /* the checklist's ticks on this device aren't kept per account: they go up only for the account they were made on —
     the first one to read its marks here — never for someone else who signs in on the same browser */
  var owner=null; try{ owner=localStorage.getItem('tc-marks-owner'); if(!owner){ owner=uid; localStorage.setItem('tc-marks-owner',uid); } }catch(e){ return; }
  if(owner!==uid){ try{ localStorage.setItem(flag,'1'); }catch(e){} return; }
  var have={}; MY_MARKS.forEach(function(m){ have[rfNormMajor(m.major)+'\u0001'+m.slot]=1; });
  var up=rfDeviceTicks().filter(function(m){ return !have[rfNormMajor(m.major)+'\u0001'+m.slot]; }), allOk=true;
  for(var i=0;i<up.length;i++){
    var m=up[i], q; try{ q=await sb.from('flowchart_marks').insert({user_id:uid,major:m.major,slot_id:m.slot,label:m.label}); }catch(e){ q={error:{message:String(e)}}; }
    if(q.error&&q.error.code!=='23505'){ allOk=false; if(schemaGap(q.error)||!q.error.code)break; continue; }   /* 23505: already there */
    MY_MARKS.push(m);
  }
  if(allOk)try{ localStorage.setItem(flag,'1'); }catch(e){}
}
/* a tick or untick on the checklist, for a row a mark stands for: the row on the account is replaced, never kept stale */
async function rfSetMark(major,sl,on){
  if(!rfSlotMarkable(sl)||typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser||MARKS_ERR==='missing'||MARKS_UID!==sbUser.id)return;
  var m=markClean({major:major,slot:sl.id,label:sl.title||''}); if(!markOk(m))return;
  var uid=sbUser.id, spell=[m.major];
  MY_MARKS.forEach(function(x){ if(rfNormMajor(x.major)===rfNormMajor(m.major)&&x.slot===m.slot&&spell.indexOf(x.major)<0)spell.push(x.major); });
  MY_MARKS=MY_MARKS.filter(function(x){ return !(rfNormMajor(x.major)===rfNormMajor(m.major)&&x.slot===m.slot); }); if(on)MY_MARKS.push(m);
  try{
    var d=await sb.from('flowchart_marks').delete().eq('user_id',uid).in('major',spell).eq('slot_id',m.slot);
    var q=(!d.error&&on)?await sb.from('flowchart_marks').insert({user_id:uid,major:m.major,slot_id:m.slot,label:m.label}):null;
    var e=d.error||(q&&q.error&&q.error.code!=='23505'?q.error:null);
    /* not saved: this device still has the tick, and sends its ticks again at the next load */
    if(e&&!schemaGap(e)){ try{ localStorage.removeItem('tc-marks-pushed:'+uid); }catch(x){} try{ frToast('Couldn’t save that to your account — it’s kept on this device and goes up next time.'); }catch(x){} }
  }catch(e){}
  try{ if(typeof plRenderRecord==='function')plRenderRecord(); }catch(e){}
}
/* ---- the look ---- */
(function(){
  if(document.getElementById('rf-style'))return;
  var st=document.createElement('style'); st.id='rf-style';
  st.textContent=[
    /* amber that reads at 4.5:1 on its own tint in both themes */
    ':root,:root[data-theme="light"]{--rf-amber:#92400E}:root[data-theme="dark"]{--rf-amber:#FBBF24}',
    '.rf-read{margin:0 0 12px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel-2)}',
    '.rf-cnt{font-weight:700;font-size:15px;color:var(--text)}',
    '.rf-cat{font-size:13px;color:var(--muted);margin-top:2px}',
    '.rf-check{margin-top:8px}.rf-check>summary{cursor:pointer;font-size:13px;font-weight:600;color:var(--accent)}',
    '.rf-cls{display:flex;flex-direction:column;gap:2px;margin-top:8px;max-height:34vh;overflow-y:auto}',
    '.rf-cl{display:grid;grid-template-columns:auto 1fr auto auto;gap:8px;align-items:start;padding:6px 2px;border-top:1px solid var(--line-soft);font-size:13px}',
    '.rf-cl.flagged .rf-cll,.rf-cl.flagged .rf-clv{text-decoration:line-through;color:var(--faint)}',
    '.rf-clx{display:flex;flex-direction:column;gap:2px;min-width:0}.rf-cll{color:var(--text);overflow-wrap:anywhere}',
    '.rf-cus{display:flex;flex-wrap:wrap;gap:4px 10px}.rf-cu{font-size:12px;color:var(--muted)}',
    '.rf-clv{font-size:12px;color:var(--text-2);white-space:nowrap}',
    '.rf-flag{font-size:11.5px;border:1px solid var(--line);background:var(--panel);color:var(--text-2);border-radius:999px;padding:2px 9px;cursor:pointer}',
    '.rf-flag.on{border-color:var(--low);color:var(--low)}',
    '.rf-tag{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.02em;border-radius:6px;padding:1px 6px;white-space:nowrap;background:var(--panel-3);color:var(--text-2)}',
    '.rf-tag.t-blue{background:var(--blue-soft);color:var(--blue-ink)}.rf-tag.t-purple{background:rgba(124,58,237,.12);color:var(--prof-ink)}',
    '.rf-tag.t-teal{background:rgba(13,148,136,.13);color:var(--good-ink)}.rf-tag.t-amber{background:rgba(180,83,9,.12);color:var(--rf-amber)}',
    '.rf-rc{margin:12px 0 0;padding:12px 14px;border:1px solid var(--line);border-radius:12px}',
    '.rf-rch{font-weight:700;font-size:14px;color:var(--text)}.rf-rcs{font-size:12.5px;color:var(--muted);margin:2px 0 6px}',
    '.rf-rcr{display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-top:1px solid var(--line-soft);cursor:pointer}',
    '.rf-rcr input{margin-top:3px}.rf-rct{display:flex;flex-direction:column;font-size:13px;color:var(--text)}.rf-rct span{font-size:12px;color:var(--muted)}',
    '.rf-diff{padding:22px 24px}.rf-dh{display:flex;gap:8px;align-items:baseline;margin:14px 0 4px;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--text-2)}',
    '.rf-dh em{font-style:normal;color:var(--muted)}.rf-dl{margin:0;padding-left:18px;font-size:14px;color:var(--text)}.rf-dl li{margin:3px 0}.rf-dmore{list-style:none;color:var(--muted)}',
    '.rf-dp{font-size:13px;color:var(--muted);margin:2px 0 6px}.rf-dpl{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid var(--line-soft);font-size:14px;color:var(--text)}',
    '.rf-top{flex-wrap:wrap}.rf-who{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px;min-width:0}.rf-who b{font-size:17px;color:var(--text)}',
    '.rf-catc{font-size:11.5px;font-weight:700;border-radius:999px;padding:2px 9px;background:var(--blue-soft);color:var(--blue-ink)}.rf-catc.q{background:rgba(180,83,9,.12);color:var(--rf-amber)}',
    '.rf-sum{font-size:13.5px;color:var(--text-2);flex-basis:100%}',
    '.rf-cols{display:grid;grid-template-columns:minmax(0,1fr);gap:14px;margin-top:12px}',
    '@media(min-width:1140px){.rf-cols{grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:start}}',
    '.rf-col{min-width:0}.rf-h{display:flex;align-items:baseline;justify-content:space-between;gap:8px;padding:0 0 6px;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--text-2)}',
    '.rf-h em{font-style:normal;letter-spacing:0;text-transform:none;font-size:12.5px;color:var(--muted);font-weight:600}',
    '.rf-row{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-top:1px solid var(--line-soft)}',
    '.rf-dot{flex:none;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:800;border:2px solid var(--line)}',
    '.rf-dot.done{background:var(--good);border-color:var(--good);color:var(--panel)}.rf-dot.taking{border-color:var(--accent);background:linear-gradient(90deg,var(--accent) 50%,transparent 50%)}',
    '.rf-nm{font-size:13px;color:var(--muted)}',
    '#tiModal{padding:22px 24px 20px}@media(max-width:640px){#tiModal{padding:18px 14px 16px}}',
    '.rf-dot.need{border-color:var(--muted)}.rf-dot.cant{border-style:dashed;color:var(--muted)}',
    '.rf-tx{flex:1;min-width:0}.rf-l1{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 8px}.rf-lab{font-size:14px;color:var(--text);font-weight:600;overflow-wrap:anywhere}',
    '.rf-l2{display:flex;flex-direction:column;gap:2px;margin-top:3px}.rf-used,.rf-need,.rf-mine{font-size:12.5px;color:var(--muted)}.rf-mine{color:var(--good-ink)}',
    '.rf-look{font-size:12.5px;color:var(--rf-amber);font-weight:600}',
    '.rf-mark{flex:none;font-size:12px;font-weight:600;border:1px solid var(--line);background:var(--panel);color:var(--accent);border-radius:999px;padding:4px 11px;cursor:pointer}',
    '.rf-empty{font-size:13.5px;color:var(--muted);padding:8px 0;border-top:1px solid var(--line-soft)}',
    '.rf-fold{border-top:1px solid var(--line-soft)}.rf-fold>summary{display:flex;align-items:baseline;justify-content:space-between;gap:8px;cursor:pointer;padding:10px 0;font-size:14.5px;font-weight:600;color:var(--text);list-style:none}',
    '.rf-fold>summary::-webkit-details-marker{display:none}.rf-fold>summary::after{content:"\\203A";color:var(--muted);margin-left:6px;transition:transform .15s}.rf-fold[open]>summary::after{transform:rotate(90deg)}',
    '.rf-fold>summary em{font-style:normal;font-size:12.5px;color:var(--muted);font-weight:600;margin-left:auto}.rf-fold>summary em.rf-fin{color:var(--good-ink)}',
    '.rf-ip>summary{font-size:13.5px;color:var(--accent)}',
    '.rf-uo{display:flex;flex-direction:column}.rf-uor{display:flex;gap:10px;align-items:baseline;padding:6px 0;border-top:1px solid var(--line-soft);font-size:13px}.rf-uor b{color:var(--text);white-space:nowrap}.rf-uor span{color:var(--muted)}',
    '.rf-all{display:block;margin-top:10px}',
    '.rf-again{margin-top:10px;font-size:13px;color:var(--rf-amber);font-weight:600}'
  ].join('\n');
  (document.head||document.documentElement).appendChild(st);
}());
/* the page's other scripts and the inline handlers reach these through window */
try{ Object.assign(window,{auditLines:auditLines,auditRow:auditRow,auditFrom:auditFrom,auditStoredReqs:auditStoredReqs,loadAudit:loadAudit,auditEnsure:auditEnsure,saveAudit:saveAudit,auditSaveOverrides:auditSaveOverrides,curAudit:curAudit,auditOverrides:auditOverrides,auditIsTotal:auditIsTotal,auditDiff:auditDiff,plGeMap:plGeMap,plGeArea:plGeArea,auditUnitsOf:auditUnitsOf,dprStale:dprStale,dprRecompute:dprRecompute,rfAfterRead:rfAfterRead,rfReportHead:rfReportHead,rfStaleCard:rfStaleCard,rfDropStale:rfDropStale,rfSaveReport:rfSaveReport,rfShowDiff:rfShowDiff,rfRenderPast:rfRenderPast,rfCountsText:rfCountsText,loadMarks:loadMarks,rfMarked:rfMarked,rfMarkedIds:rfMarkedIds,rfSetMark:rfSetMark,rfMarksState:function(){ return {marks:MY_MARKS.slice(),uid:MARKS_UID,err:MARKS_ERR}; }}); }catch(e){}
'''
one("window.dprAudit=dprAudit;\n", "window.dprAudit=dprAudit;\n" + MAIN)
# the audit loads beside the record, once per account
one("""  try{ await loadMyWaived(); }catch(e){}
}""", """  try{ await loadMyWaived(); }catch(e){}
  try{ if(typeof auditEnsure==='function')auditEnsure(); }catch(e){}   /* website-report-flow (2026-10-14) */
}""")
# the read: same-term "already", and what's on the account but not on the report
one("""  window._dprMeta=(dpr&&dpr.ok)?{program:dpr.program,skipped:dpr.skipped}:null;
  tiRows=(dpr&&dpr.ok&&dpr.rows.length)?dpr.rows:tiParse(allText);
""", """  window._dprMeta=(dpr&&dpr.ok)?{program:dpr.program,skipped:dpr.skipped}:null;
  tiRows=(dpr&&dpr.ok&&dpr.rows.length)?dpr.rows:tiParse(allText);
  if(dpr&&dpr.ok&&dpr.rows.length)try{ rfAfterRead(dpr); }catch(e){}   /* website-report-flow (2026-10-14) */
""")
# the review list: what was read, and what comes off
one("""      ? '<div class="ti-list">'+rows+'</div>'""", """      ? (isDpr?rfReportHead():'')+'<div class="ti-list">'+rows+'</div>'+(isDpr?rfStaleCard():'')""")
# the save: the report wins first, then the classes, then the verdicts and the diff
# a report with nothing new to add is still saved (its verdicts, and what came off)
one("""  if(!past.length&&!now.length){ try{frToast('Nothing selected.');}catch(e){} return; }""",
    """  if(!past.length&&!now.length&&!_rfDropped&&!(window._dprMeta&&window._dprMeta.audit&&window._dprMeta.audit.ok)){ try{frToast('Nothing selected.');}catch(e){} return; }""")
one("""window.confirmDprImport=async function(){
""", """window.confirmDprImport=async function(){
  /* website-report-flow (2026-10-14): what's on your account but not on your report comes off first (unless unchecked) */
  var _rfDropped=0;
  if(window._dprMeta&&(window._dprMeta.rc||[]).length){
    var _rd=await rfDropStale(); _rfDropped=_rd.n||0;
    if(_rd.err){ try{ frToast(_rd.err); }catch(e){} try{ tiRender('done'); }catch(e){} return; }
  }
""")
one("""  closeTranscriptImport();
  /* =====""", """  /* website-report-flow (2026-10-14): the report's verdicts are kept, flagged lines sent */
  var _rfNotes=[]; try{ _rfNotes=await rfSaveReport(); }catch(e){}
  if(_rfDropped)_rfNotes.unshift('Took '+_rfDropped+' off your account so it matches your report.');
  closeTranscriptImport();
  try{ if(typeof plRenderRecord==='function')plRenderRecord(); }catch(e){}
  /* =====""")
# the toast says what the report changed too (one toast, not two racing)
one("""  try{
    if(failed==='not-signed-in')frToast('Added '+addedNow+' to My Classes. Log in to save your past classes too.');
    else if(failed)frToast('Couldn’t save your past classes — '+failed);
    else if(nowFailed)frToast(""", """  var _rfSay=function(m){ frToast(m+(_rfNotes.length?' '+_rfNotes.join(' '):''),_rfNotes.length?6000:undefined); };
  try{
    if(failed==='not-signed-in')_rfSay('Added '+addedNow+' to My Classes. Log in to save your past classes too.');
    else if(failed)_rfSay('Couldn’t save your past classes — '+failed);
    else if(nowFailed)_rfSay(""")
one("""    else if(bits.length)frToast('Added '+bits.join(' and ')+' \\u2713'
      +(addedNow?' — import your schedule for times and professors.':''));
    else frToast('Everything in that report was already logged.');""", """    else if(bits.length)_rfSay('Added '+bits.join(' and ')+' \\u2713'
      +(addedNow?' — import your schedule for times and professors.':''));
    else _rfSay(_rfDropped?'Nothing new to add.':'Everything in that report was already logged.');""")
one("""  if(!failed&&(savedPast||addedNow)){
    setTimeout(function(){ try{ if(typeof rsOpen==='function')rsOpen('dpr'); }catch(e){} },900);
  }""", """  /* a new report over an old one: what changed, and the Plans it touches, before the rating stack */
  var _rfDiffOn=false; try{ _rfDiffOn=rfShowDiff(window._rfDiff); }catch(e){}
  window._rfDiff=null;
  if(_rfDiffOn)window._rfAfterDiff=!failed&&!!(savedPast||addedNow);
  else if(!failed&&(savedPast||addedNow)){
    setTimeout(function(){ try{ if(typeof rsOpen==='function')rsOpen('dpr'); }catch(e){} },900);
  }""")
# Past classes: by requirement when there's a report
one("""  host.innerHTML=
    '<div class="plr-top">'""", """  /* website-report-flow (2026-10-14): with a report, Past classes is laid out by its requirements */
  var _rf=false; try{ if(typeof rfRenderPast==='function')_rf=rfRenderPast(host,ledHtml); }catch(e){ _rf=false; }
  if(_rf===true)return;
  host.innerHTML=
    '<div class="plr-top">'""")
one("""  var sec=document.getElementById('plRecord'); if(sec)sec.classList.toggle('open',open);
};""", """  if(_rf==='old')host.innerHTML+='<div class="rf-again">Upload your report again to see which class filled each requirement.</div>';
  var sec=document.getElementById('plRecord'); if(sec)sec.classList.toggle('open',open);
};""")

# ================================================================ 8. flowchart marks on the account
one("""    var uc={done:{},taking:{}};
    try{ if(typeof window.plUncodedSatisfied==='function')uc=window.plUncodedSatisfied(mm,completedCodes(),myTakingCodes()); }catch(e){}""",
    """    var uc={done:{},taking:{}};
    /* website-report-flow (2026-10-14): a row you marked done (flowchart_marks) is done before anything else, and no
       GE or elective class on the record is spent on it */
    var _mk=function(sl){ try{ return typeof window.rfMarked==='function'&&window.rfMarked(mm.name,sl); }catch(e){ return false; } };
    var mmU=Object.assign({},mm,{terms:(mm.terms||[]).map(function(t){ return Object.assign({},t,{slots:(t.slots||[]).filter(function(sl){ return !(_mk(sl)&&!sl.code); })}); })});
    try{ if(typeof window.plUncodedSatisfied==='function')uc=window.plUncodedSatisfied(mmU,completedCodes(),myTakingCodes()); }catch(e){}""")
one("""    (mm.terms||[]).forEach(function(t,ti){ (t.slots||[]).forEach(function(sl){
      var isConc=(sl.type==='concentration')||/concentration/i.test(sl.note||'');
""", """    (mm.terms||[]).forEach(function(t,ti){ (t.slots||[]).forEach(function(sl){
      var isConc=(sl.type==='concentration')||/concentration/i.test(sl.note||'');
      if(_mk(sl)){
        var rowM;
        if(isConc){ if(!rows.conc){ var cnM=sl.code?String(sl.note||'').replace(/\\s*concentration\\s*$/i,''):''; rows.conc={label:(cnM?esc(cnM)+' concentration':'Concentration'),f:0,t:0,n:0}; } rowM=rows.conc; }
        else rowM=(sl.code||sl.type==='course')?rows.major:(sl.type==='ge'?rows.ge:rows.el);
        rowM.n++; rowM.f++; return;
      }
""")
one("""    var savedDone={}; schLoadDone(key).forEach(function(id){savedDone[id]=1;});""",
    """    var savedDone={}; schLoadDone(key).forEach(function(id){savedDone[id]=1;});
    try{ if(typeof window.rfMarkedIds==='function')window.rfMarkedIds(SCHED_MAJORS[key].name,m).forEach(function(id){ savedDone[id]=1; }); }catch(e){}   /* website-report-flow: your marks on the account */""")
one("""          schSaveDone();
          /* coded course + signed in → this IS your Past Classes record (one source of truth) */""",
    """          schSaveDone();
          try{ if(typeof window.rfSetMark==='function'&&curKey&&SCHED_MAJORS[curKey])window.rfSetMark(SCHED_MAJORS[curKey].name,s,nowOn); }catch(e){}   /* website-report-flow: a mark goes to the account */
          /* coded course + signed in → this IS your Past Classes record (one source of truth) */""")

f.write_text(s)
print('patched', f)
