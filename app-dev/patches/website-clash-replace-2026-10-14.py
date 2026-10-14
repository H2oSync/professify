#!/usr/bin/env python3
"""Clash -> Replace on the website (Tate, 2026-10-14; phone: clash-replace, SHEETS.addTo / atReplaceLabel, 2026-10-11).

A section that overlaps one you already have used to be added without a word (My Classes) or flagged only afterwards
as a "time conflict" pill. Now, adding it offers the choice at the moment of adding:
  - My Classes: the "Add to My Classes" dialog (the one "I'm in this" opens) says "Clashes with BUS 3438 · MoWe ..." and
    offers "Replace BUS 3438 with this class" and "Keep both". Replace takes the clashing section(s) out (a class whose
    last section goes leaves My Classes, as removing it always did), puts the new one in, and the toast has Undo
    (the new section out, the old ones back exactly as they were).
  - Plans: choosing Plan A / B / C on a clashing section (the + Plan chooser) shows the same two choices before anything
    is added; Replace swaps the clashing sections of that plan for this one (Undo puts the plan back as it was).
A section of the SAME course never clashes with its own other section (lecture + lab), as everywhere else here.
Replay on f72f221:  python3 website-clash-replace-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-clash-replace (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

MC = r"""/* website-clash-replace (2026-10-14): adding a section that clashes with one in My Classes offers Replace / Keep both. */
function tcToastAct(msg,label,fn){
  try{
    if(typeof frToast!=='function')return;
    frToast(msg,7000);
    var t=document.getElementById('frToast'); if(!t)return;
    var b=document.createElement('button'); b.className='fr-toast-act'; b.textContent=label;
    b.onclick=function(e){ try{ e.stopPropagation(); }catch(_){} t.classList.remove('on'); try{ fn(); }catch(_){} };
    t.appendChild(b);
  }catch(e){}
}
window.tcToastAct=tcToastAct;
/* The sections in My Classes (another course) this one overlaps: [{code, ix, rec (the stored section or null), when}] */
function mcClashesOf(code,s){
  try{
    var meet=parseMeet(s&&s.days); if(!okMeet(meet))return [];
    var cc=(typeof canonCode==='function')?(canonCode(code)||code):code, out=[];
    myClassMeets(myClasses.slice()).forEach(function(m){
      if(((typeof canonCode==='function')?(canonCode(m.code)||m.code):m.code)===cc)return;
      if(!meetsOverlap(meet,m.meet))return;
      var k=String(m.key||''), h=k.lastIndexOf('#'), ix=h>=0?parseInt(k.slice(h+1),10):-1;
      var all=secsOf(myClassMeta[m.code]), rec=(ix>=0&&all&&all[ix])?Object.assign({},all[ix]):null;
      out.push({code:m.code,ix:ix,rec:rec,when:rec?(rec.days||''):(myClassTime(m.code)||'')});
    });
    return out;
  }catch(e){ return []; }
}
function mcClashCodes(cl){ var a=[]; cl.forEach(function(c){ if(a.indexOf(c.code)<0)a.push(c.code); }); return a; }
function mcReplaceLabel(cl){ var a=mcClashCodes(cl); return a.length===1?('Replace '+a[0]+' with this class'):('Replace '+a.length+' classes with this one'); }
/* take the clashing sections out of My Classes (a class whose last section goes goes with it) */
function mcReplaceRemove(cl){
  cl.forEach(function(c){
    if(c.rec){
      var arr=(myClassMeta[c.code]&&Array.isArray(myClassMeta[c.code].secs))?myClassMeta[c.code].secs:[];
      var ix=arr.findIndex(function(x){ return x&&String(x.crn)===String(c.rec.crn)&&x.section===c.rec.section; });
      if(ix<0)ix=c.ix;
      if(ix>=0)mcRemoveSection(c.code,ix);
    }else if(isMyClass(c.code))toggleMyClass(c.code);
  });
}
/* Undo: the new section out, each old one back as it was */
function mcReplaceUndo(code,crn,removed){
  try{
    var arr=(myClassMeta[code]&&Array.isArray(myClassMeta[code].secs))?myClassMeta[code].secs:[];
    var ix=arr.findIndex(function(x){ return x&&String(x.crn)===String(crn); });
    if(ix>=0)mcRemoveSection(code,ix); else if(isMyClass(code)&&!arr.length)toggleMyClass(code);
  }catch(e){}
  removed.forEach(function(c){
    try{
      if(c.rec){
        var s=(typeof secByCrn==='function')?secByCrn(c.code,c.rec.crn):null;
        if(!s)s={class_nbr:c.rec.crn,section:c.rec.section,name:c.rec.prof,days:c.rec.days,seat:null};
        mcCommitSection(c.code,s,c.rec.status||'enrolled',c.rec.wlPos||null);
      }else if(!isMyClass(c.code))toggleMyClass(c.code);
    }catch(e){}
  });
  try{ renderMyClasses(); }catch(e){} try{ cpRefresh(); }catch(e){}
}
function enReplace(){
  var e=_enrollState; if(!e.code||!e.s)return;
  var cl=mcClashesOf(e.code,e.s); if(!cl.length){ enConfirm(); return; }
  var code=e.code, crn=String(e.s.class_nbr||''), names=mcClashCodes(cl);
  mcReplaceRemove(cl);
  mcCommitSection(code,e.s,e.status,e.wlPos); closeEnrollDialog();
  tcToastAct(code+' replaced '+(names.length===1?names[0]:(names.length+' classes')),'Undo',function(){ mcReplaceUndo(code,crn,cl); });
}
function enActionsHtml(){
  var e=_enrollState, cl=(e.code&&e.s)?mcClashesOf(e.code,e.s):[];
  if(!cl.length)return '<div class="si-actions" style="margin-top:18px"><span class="fr-mut" style="font-size:12px">My Classes = official only</span><button class="btn primary" onclick="enConfirm()">Add to My Classes</button></div>';
  return '<div class="en-clash" role="status"><b>Clashes with</b> '+cl.map(function(c){ return escapeHtml(c.code)+(c.when?' · '+escapeHtml(c.when):''); }).join(', ')+'</div>'
    +'<div class="si-actions en-clash-acts"><button class="btn" onclick="enConfirm()">Keep both</button><button class="btn primary" onclick="enReplace()">'+escapeHtml(mcReplaceLabel(cl))+'</button></div>';
}
"""
one("/* ---- Enrolled/Waitlist confirm dialog (used by \"I'm enrolled\" + Watchlist promote) ---- */\n",
    MC + "/* ---- Enrolled/Waitlist confirm dialog (used by \"I'm enrolled\" + Watchlist promote) ---- */\n")
one("""    +'<div class="si-actions" style="margin-top:18px"><span class="fr-mut" style="font-size:12px">My Classes = official only</span><button class="btn primary" onclick="enConfirm()">Add to My Classes</button></div>'
    +'</div></div>';""", """    +enActionsHtml()
    +'</div></div>';""")

# ---- Plans: the + Plan chooser
PL = r"""  /* website-clash-replace (2026-10-14): a section that overlaps one already in the plan offers Replace / Keep both */
  function clashesIn(slot, code, crn) {
    var me = info(code, crn); if (!me.meet) return [];
    return plan(slot).sections.map(function (x) { return info(x.code, x.class_nbr); })
      .filter(function (i) { return canon(i.code) !== canon(code) && i.meet && overlap(me.meet, i.meet); });
  }
  function canon(c) { try { return has('canonCode') ? (canonCode(c) || c) : c; } catch (_) { return c; } }
  function clashPanel(slot, code, crn) {
    var box = document.getElementById('plChoose'); if (!box) return;
    var cl = clashesIn(slot, code, crn), codes = [];
    cl.forEach(function (i) { if (codes.indexOf(i.code) < 0) codes.push(i.code); });
    var lab = codes.length === 1 ? 'Replace ' + codes[0] + ' with this class' : 'Replace ' + codes.length + ' classes with this one';
    var at = ' data-slot="' + slot + '" data-code="' + esc(code) + '" data-crn="' + esc(crn) + '"';
    box.innerHTML = '<div class="pl2-chhd">' + esc(code) + ' · Plan ' + slot + '</div>'
      + '<div class="pl2-clash" role="status"><b>Clashes with</b> ' + cl.map(function (i) { return esc(i.label) + (i.meet && i.when ? ' · ' + esc(i.when) : ''); }).join(', ') + '</div>'
      + '<button type="button" class="pl2-chi pl2-chi--go" data-pl-act="chreplace"' + at + '>' + esc(lab) + '</button>'
      + '<button type="button" class="pl2-chi" data-pl-act="chkeep"' + at + '>Keep both</button>';
    try { var fb = box.querySelector('button'); if (fb) fb.focus(); } catch (_) {}
  }
  function chAfter(crn) {
    closeChooser();
    try { if (has('cpRefresh')) cpRefresh(crn); } catch (_) {}
    try { if (has('renderExplore')) renderExplore(); } catch (_) {}
  }
"""
one("  function openChooser(btn, code, crn) {\n", PL + "  function openChooser(btn, code, crn) {\n")
one("""      else if (add(slot, code, crn)) toast(code + ' → Plan ' + slot + ' · watching it');
      closeChooser();""", """      else if (clashesIn(slot, code, crn).length) { clashPanel(slot, code, crn); return; }
      else if (add(slot, code, crn)) toast(code + ' → Plan ' + slot + ' · watching it');
      closeChooser();""")
one("""    if (act === 'gpclose') { closeGamePlan(); return; }""", """    if (act === 'chkeep') { if (add(slot, code, crn)) toast(code + ' → Plan ' + slot + ' · watching it'); chAfter(crn); return; }
    if (act === 'chreplace') {
      var cl = clashesIn(slot, code, crn), drop = {}, names = [];
      if (!cl.length) { if (add(slot, code, crn)) toast(code + ' → Plan ' + slot + ' · watching it'); chAfter(crn); return; }
      cl.forEach(function (i) { drop[i.crn] = 1; if (names.indexOf(i.code) < 0) names.push(i.code); });
      var keep = plan(slot).sections.filter(function (x) { return !drop[x.class_nbr]; }).concat([{ code: code, class_nbr: String(crn) }]);
      var before = setSections(slot, keep, 'replace');
      chAfter(crn);
      try { if (typeof tcToastAct === 'function') tcToastAct(code + ' replaced ' + (names.length === 1 ? names[0] : names.length + ' classes') + ' in Plan ' + slot, 'Undo', function () { setSections(slot, before); try { if (has('cpRefresh')) cpRefresh(crn); } catch (_) {} }); } catch (_) {}
      return;
    }
    if (act === 'gpclose') { closeGamePlan(); return; }""")
one(""".ex-gesw button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}""",
    """.ex-gesw button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
/* website-clash-replace (2026-10-14) */
.en-clash,.pl2-clash{margin-top:14px;padding:9px 12px;border-radius:10px;border:1px solid var(--line);border-left:3px solid var(--low);background:var(--panel-2);color:var(--text);font-size:13.5px;line-height:1.4}
.pl2-clash{margin:6px 8px 8px}
.en-clash-acts{margin-top:14px;gap:8px;flex-wrap:wrap}
.pl2-chi--go{white-space:normal;text-align:left;line-height:1.3;font-weight:700}""")
f.write_text(s)
print('ok')
