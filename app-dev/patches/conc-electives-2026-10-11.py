#!/usr/bin/env python3
r"""Concentration spots say what they are: required, pick one, or an elective with every class that counts (Tate,
2026-10-11, on Business Administration · Financial Management's "BUS 4468 Blockchain in Finance": "i dont think
blockchain in finance is even required so make sure if this is an elective or concentration course to specify that
and then when you are creating the recomendations its showing all the possible finance concentration classes that
are applicable this goes for all majors").

What was wrong: the flowchart's concentration spots were filled with the concentration's class list IN ORDER. For
Business Administration that list (CONC_REQS) runs required classes, then one-of pairs, then every track elective —
so Financial Management's 7 spots became BUS 3411, 3431, 3438, 3441, 3440, 4442, 4468: both halves of "BUS 3440 or
3441" as if each were required, and two track electives (4442, 4468) as if they were the required ones. A spot past
the required classes on any other major became "additional concentration course" offering the REQUIRED classes again.

Now (every major):
  · required classes fill the first spots: "Required · Financial Management" (CONC_CATALOG's classes are the
    catalog's required ones; CONC_REQS gets its required / pick-one / elective split from its own notes, CONC_SHAPE);
  · a pick-one ("BUS 3440 or BUS 3441") is one spot that either class fills;
  · the remaining spots are "Financial Management elective", any of the concentration's electives — the ledger checks
    every one of them, and the Planner's picks consider every one of them;
  · a concentration with no recorded electives says so ("Concentration elective" + the catalog's note), never offering
    the required classes again;
  · the older MAJOR_CATALOG fallback, which can't tell required from elective, says only "Concentration course".
Patches app/planner.js (data + schExpandConc + the ledger cell) and app/index.html (the spot's label).
Run AFTER in-progress-now-2026-10-11.py.  Usage: python3 conc-electives-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
D = sys.argv[1]
PJ = os.path.join(D, 'app', 'planner.js'); PA = os.path.join(D, 'app', 'index.html')
J = open(PJ, encoding='utf-8').read(); A = open(PA, encoding='utf-8').read()

def rj(a, b, label):
    global J
    if J.count(a) != 1: sys.exit(f'planner {label}: anchor matched {J.count(a)}x')
    J = J.replace(a, b)
def ra(a, b, label):
    global A
    if A.count(a) != 1: sys.exit(f'app {label}: anchor matched {A.count(a)}x')
    A = A.replace(a, b)

rj("""function concInfo(majorName){""", """/* (2026-10-11) CONC_REQS lists required classes, one-of pairs and electives in one run; its notes above say which is
   which. The rest of each list is the concentration's electives. */
var CONC_SHAPE={
  'Business Administration':{
    'Accounting':{req:['BUS 3319','BUS 3320','BUS 3321','BUS 3322','BUS 3323'],note:'Plus electives from BUS 4424\\u20134428.'},
    'Consumer Packaging':{req:['BUS 3396','BUS 4418','ITP 2234','ITP 3330','ITP 3334','ITP 4475'],note:'Plus one ITP elective.'},
    'Entrepreneurship':{req:['BUS 3310','BUS 3330','ITP 4406'],one:[['BUS 4447','BUS 4488']],note:'Plus approved electives.'},
    'Financial Management':{req:['BUS 3411','BUS 3431','BUS 3438'],one:[['BUS 3440','BUS 3441']],note:'Plus 9\\u201311 units from one of three tracks.'},
    'Information Systems and Analytics':{req:['BUS 3392','BUS 3393','BUS 3394','BUS 3399','BUS 4497'],note:'Plus a project course and one approved elective.'},
    'Management and Human Resources':{req:['BUS 3384','BUS 3388','BUS 4477','BUS 4489'],note:'Plus a project course and approved electives.'},
    'Marketing Management':{req:['BUS 3396','BUS 4418'],note:'Plus 12 units of approved marketing electives.'},
    'Real Estate Finance':{req:['BUS 3431','BUS 3440','BUS 4434'],note:'Plus 9 units of approved electives.'},
    'Supply Chain Management':{req:['BUS 2208','BUS 3308','BUS 4416','BUS 4417','ITP 3303','ITP 3371','ITP 4410'],note:'Plus one approved elective.'}
  }
};
function concInfo(majorName){""", 'shape')
rj("""      return {known:true,list:c.list||[],kind:c.kind||'concentration',src:c.src||null};""",
   """      return {known:true,list:(c.list||[]).map(function(x){ return Object.assign({reqKnown:true},x); }),kind:c.kind||'concentration',src:c.src||null};""", 'catalog req')
rj("""        return {name:k,units:0,note:'',classes:CONC_REQS[majorName][k].map(function(code){
          return [code,(typeof COURSE_NAME!=='undefined'&&COURSE_NAME[code])||'',3];
        })};""", """        var all=CONC_REQS[majorName][k], sh=(CONC_SHAPE[majorName]||{})[k], nm=function(code){ return [code,(typeof COURSE_NAME!=='undefined'&&COURSE_NAME[code])||'',3]; };
        if(!sh)return {name:k,units:0,note:'',classes:all.map(nm)};
        var taken={}; sh.req.concat.apply(sh.req,sh.one||[]).forEach(function(c){ taken[c]=1; });
        return {name:k,units:0,note:sh.note||'',reqKnown:true,classes:sh.req.map(nm),one:(sh.one||[]).map(function(g){return g.slice();}),
          electives:all.filter(function(c){ return !taken[c]; })};""", 'reqs shape')
rj("""        return {conc:cc,known:true,note:hit.note||'',list:(hit.classes||[]).map(function(a){
          return {code:a[0],name:a[1]||((typeof COURSE_NAME!=='undefined'&&COURSE_NAME[a[0]])||''),units:a[2]||0};
        })};""", """        return {conc:cc,known:true,note:hit.note||'',reqKnown:!!hit.reqKnown,one:hit.one||[],electives:hit.electives||[],list:(hit.classes||[]).map(function(a){
          return {code:a[0],name:a[1]||((typeof COURSE_NAME!=='undefined'&&COURSE_NAME[a[0]])||''),units:a[2]||0};
        })};""", 'conc classes')
rj("""    var out={}; for(var kk in m)out[kk]=m[kk];
    out.terms=m.terms.map(function(t){""", """    /* (2026-10-11) after the required classes: each pick-one is one spot, then the electives — every one of them */
    var oneG=(info.one||[]).map(function(g){ return g.filter(function(c){ return !_req[c]; }); }).filter(function(g){ return g.length; }), oi=0;
    var elec=(info.electives||[]).filter(function(c){ return !_req[c]; });
    var cname=function(c){ return (typeof COURSE_NAME!=='undefined'&&COURSE_NAME[c])||c; };
    var out={}; for(var kk in m)out[kk]=m[kk];
    out.terms=m.terms.map(function(t){""", 'expand vars')
rj("""        if(info.conc&&(list.length||_skipped.length)){""", """        if(info.conc&&(list.length||_skipped.length||oneG.length||elec.length)){""", 'expand cond')
rj("""          if(ci<list.length){ var pk=list[ci++]; ns.code=pk.code; ns.title=pk.name||pk.code; if(pk.units)ns.units=pk.units; ns.type='course'; ns.note=info.conc+' concentration'; }""",
   """          if(ci<list.length){ var pk=list[ci++]; ns.code=pk.code; ns.title=pk.name||pk.code; if(pk.units)ns.units=pk.units; ns.type='course'; ns.note=info.conc+' concentration'; ns.concKind=info.reqKnown?'req':'conc'; }
          else if(oi<oneG.length){ var g=oneG[oi++]; ns.note=info.conc+' concentration'; ns.concKind='one';
            if(g.length===1){ ns.code=g[0]; ns.title=cname(g[0]); ns.type='course'; } else { ns.type='choice'; ns.options=g.slice(); ns.title=g.join(' or '); } }
          else if(elec.length){ ns.note=info.conc+' concentration'; ns.concKind='el'; ns.hint=info.note||''; ns.title=info.conc+' elective';
            if(elec.length===1){ ns.code=elec[0]; ns.type='course'; } else { ns.type='choice'; ns.options=elec.slice(); } }""", 'expand fill')
rj("""          else { ns.title=info.conc+' — additional concentration course'; ns.note=info.note||(list.length+' courses to choose from'); ns.options=list.map(function(x){return x.code;}); }""",
   """          else { ns.title=info.conc+' elective'; ns.note=info.conc+' concentration'; ns.concKind='el'; ns.hint=info.note||'Pick it with your advisor'; }""", 'expand rest')
rj("""        var cell = { id: sl.id, title: sl.title || '', code: sl.code || '', units: sl.units, type: sl.type, note: sl.note || '', area: sl.code ? null : slotAreaKey(sl.title), state: 'cant' };""",
   """        var cell = { id: sl.id, title: sl.title || '', code: sl.code || '', units: sl.units, type: sl.type, note: sl.note || '', area: sl.code ? null : slotAreaKey(sl.title), state: 'cant', ck: sl.concKind || null, hint: sl.hint || '' };""", 'cell')

# the app: the spot says what it is
ra("""  const line = s.mine ? '<span class="pc-pf tc-mine">Marked done by you</span>' :""",
   """  /* (2026-10-11) a concentration spot says what it is: required, pick one, or an elective (any of N) */
  const cn = String(s.note || '').replace(/\\s*concentration\\s*$/i, ''), nOpt = (s.choice || []).length;
  const kind = s.ck === 'req' ? `Required · ${esc(cn)}` : s.ck === 'one' ? `Required · ${esc(cn)} · either one` : s.ck === 'el' ? `Elective · ${esc(cn)}${nOpt > 1 ? ` · any of ${nOpt}` : s.hint && !nOpt ? ` · ${esc(s.hint)}` : ''}` : s.ck === 'conc' ? `Concentration · ${esc(cn)}` : '';
  const kindTag = kind ? `<span class="pc-kind">${kind}</span>` : '';
  const line = s.mine ? '<span class="pc-pf tc-mine">Marked done by you</span>' :""", 'kind')
ra("""  return `<div class="pc-row ${s.state}">${dot}<div class="pc-tx">${act ? `<button class="pc-main" ${act}>${main}</button>` : `<div class="pc-main">${main}</div>`}${line}</div></div>${pick}`;""",
   """  return `<div class="pc-row ${s.state}">${dot}<div class="pc-tx">${act ? `<button class="pc-main" ${act}>${main}</button>` : `<div class="pc-main">${main}</div>`}${kindTag}${line}</div></div>${pick}`;""", 'kind out')
ra(""".pc-nowt{""", """.pc-kind{display:block;font-size:11.5px;font-weight:700;letter-spacing:.01em;color:var(--muted);margin-top:2px}
.pc-nowt{""", 'css')

open(PJ, 'w', encoding='utf-8').write(J); open(PA, 'w', encoding='utf-8').write(A)
print('conc-electives: done')
