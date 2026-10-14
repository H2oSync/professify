#!/usr/bin/env python3
"""Website Explore gets the phone's Fall / Spring switch (Tate, 2026-10-14; phone: explore-term-switch-2026-10-10,
explore-profs-fall-2026-10-12).

Explore was locked to Spring 2027 (mcTerm(), SEAT_SECTIONS). Now, while there are two terms (mcTwoTerms()), the filter
row beside GEs / My major / Saved carries "Spring 2027 | Fall 2026". It always starts on Spring (never saved).
  - Fall reads the NOW term's whole seat feed once, on demand, into a SEPARATE store (FALL) - never SEAT_SECTIONS /
    PROFESSIFY_SEATS and never the seats cache key (professify_seats_cache:<TERM>).
  - Explore's rows, the class page and a professor's "teaching" list read the chosen term: for one synchronous render
    inFall() lends those names the Fall store (and the friends' / your Fall classes), then gives Spring's back.
  - Fall is read-only: every Add / Save / Watch / plan control on a Fall surface says "Fall 2026 is read-only - switch to
    Spring 2027 to add" and writes nothing (a capture-phase guard, so no write function can run).
  - A class opened from a Fall surface opens its Fall page: from Explore on Fall, from Home (a class you or a friend are in
    now), from a friend's page on its Fall chip, from My Classes > Fall, from a Fall class page or professor page.
Replay on f72f221:  python3 website-explore-term-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-explore-term (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

BLOCK = r"""
/* ================================================================================================
   EXPLORE'S TERM SWITCH — website-explore-term (2026-10-14). The phone's (explore-term-switch, 2026-10-10).
   ================================================================================================
   Spring 2027 (mcTerm) is where Explore starts, every time. Fall 2026 (mcNowTerm) is for looking at what friends are
   in. Fall's sections are read ONCE, on demand, into FALL — a store of their own. They never enter SEAT_SECTIONS /
   PROFESSIFY_SEATS and never the seats cache. For one synchronous render inFall() lends those names the Fall store (and,
   for friends and "mine", their Fall classes); nothing outlives the call. Fall is read-only. */
var FALL={term:'',sec:null,idx:null,ready:false,loading:false,err:false,on:false,c:{}};
var exTermSel='spring', cpNow=false, pfNow=false;
function fallActive(){ return exTermSel==='now'&&mcTwoTerms(); }
async function loadFallAll(){
  if(!mcTwoTerms())return;
  var t=mcNowTerm();
  if(FALL.term!==t)Object.assign(FALL,{term:t,sec:null,idx:null,ready:false,loading:false,err:false,on:false,c:{}});
  if(FALL.ready||FALL.loading)return;
  var c=cfg(); if(!c.SUPABASE_URL||!c.SUPABASE_ANON_KEY){ FALL.err=true; fallRepaint(); return; }
  FALL.loading=true; FALL.err=false;
  var base=c.SUPABASE_URL.replace(/\/$/,''), hdr={apikey:c.SUPABASE_ANON_KEY,Authorization:'Bearer '+c.SUPABASE_ANON_KEY};
  var sel='course_code,title,section,instructor,days,status,capacity,enrolled,available,waitlist_total,waitlist_capacity,class_nbr'+(window._seatModeCols?(','+window._seatModeCols):'');
  var rows=[], complete=false;
  try{
    for(var off=0; off<40000; off+=1000){
      var res=await fetch(base+'/rest/v1/course_seats?term=eq.'+encodeURIComponent(t)+'&select='+sel+'&order=course_code.asc,class_nbr.asc&limit=1000&offset='+off,{headers:hdr});
      if(!res.ok)break;
      var part=await res.json(); if(!Array.isArray(part))break;
      rows=rows.concat(part);
      if(part.length<1000){ complete=true; break; }
    }
  }catch(e){}
  if(FALL.term!==t)return;
  FALL.loading=false;
  if(!complete||!rows.length){ FALL.err=true; fallRepaint(); return; }
  var idx={}, sec={}, seen={};
  rows.forEach(function(r){
    var code=String(r.course_code||'').trim(); if(!code)return;
    var nbr=String(r.class_nbr||'').trim(); if(nbr){ if(seen[nbr])return; seen[nbr]=1; }
    var a=idx[code]||(idx[code]={open:0,wait:0,closed:0,unk:0,seats:0,wl:0,cap:0,wlcap:0});
    var st=seatStatusOf(r.status,Math.max(0,r.available||0));
    if(st==='open')a.open++;else if(st==='wait')a.wait++;else if(st==='full')a.closed++;else a.unk=(a.unk||0)+1;
    a.seats+=Math.max(0,r.available||0); a.wl+=Math.max(0,r.waitlist_total||0);
    a.cap+=Math.max(0,r.capacity||0); a.wlcap+=Math.max(0,r.waitlist_capacity||0);
    (sec[code]||(sec[code]=[])).push(r);
  });
  FALL.idx=idx; FALL.sec=sec; FALL.ready=true;
  fallRepaint();
}
function fallEnsure(){ if(mcTwoTerms()&&!FALL.ready&&!FALL.loading&&!FALL.err)loadFallAll(); }   /* a failed read waits for Retry, it does not loop */
window.fallRetry=function(){ FALL.err=false; FALL.loading=false; loadFallAll(); fallRepaint(); };
function fallViewId(){ var a=document.querySelector('.view.active'); return a?String(a.id||'').replace(/^view-/,''):''; }
function fallRepaint(){
  var v=fallViewId();
  try{ if(v==='explore'&&exTermSel==='now')renderExplore(); }catch(e){}
  try{ if(v==='class'&&cpNow)renderClassPage(); }catch(e){}
  try{ if(v==='prof'&&pfNow)renderProfPage(); }catch(e){}
}
/* Is the page in front of the student a Fall one? (what the read-only guard asks) */
function fallViewing(){
  if(!mcTwoTerms())return false;
  var v=fallViewId();
  return v==='explore'?exTermSel==='now':(v==='class'?cpNow:(v==='prof'?pfNow:false));
}
/* Run fn with Fall's names: the seat feed, the friends' and your classes of that term, nothing watched. */
function inFall(fn){
  if(FALL.on||!FALL.ready)return fn();
  var sv={ss:SEAT_SECTIONS,ps:PROFESSIFY_SEATS,fr:FRIENDS,mc:myClasses,mm:myClassMeta,wc:watchClasses,wm:watchMeta,
          ge:window._fpGe,al:window._fpAll,pn:_profByName,sp:window._scrapedProfs,pt:_pfTeachCache,pz:_pfTeachSize,ks:__knownSubs,kn:__knownSubsSeatN,
          ai:null}, T=window.TCPlans;
  FALL.on=true;
  try{
    SEAT_SECTIONS=FALL.sec; PROFESSIFY_SEATS=FALL.idx;
    FRIENDS=sv.fr.map(function(x){ return frNow(x); });
    myClasses=NOW_MINE.classes; myClassMeta=NOW_MINE.meta; watchClasses=[]; watchMeta={};
    window._fpGe=FALL.c.ge||null; window._fpAll=FALL.c.al||null; _profByName=FALL.c.pn||null; window._scrapedProfs=FALL.c.sp||null;
    _pfTeachCache=null; _pfTeachSize=-1; __knownSubs=null; __knownSubsSeatN=-1;
    try{ if(T){ sv.ai=T.askInterest; T.askInterest=function(){}; } }catch(e){}
    return fn();
  }finally{
    FALL.c={ge:window._fpGe,al:window._fpAll,pn:_profByName,sp:window._scrapedProfs};
    SEAT_SECTIONS=sv.ss; PROFESSIFY_SEATS=sv.ps; FRIENDS=sv.fr; myClasses=sv.mc; myClassMeta=sv.mm; watchClasses=sv.wc; watchMeta=sv.wm;
    window._fpGe=sv.ge; window._fpAll=sv.al; _profByName=sv.pn; window._scrapedProfs=sv.sp;
    _pfTeachCache=sv.pt; _pfTeachSize=sv.pz; __knownSubs=sv.ks; __knownSubsSeatN=sv.kn;
    try{ if(T&&sv.ai)T.askInterest=sv.ai; }catch(e){}
    FALL.on=false;
  }
}
try{ window.inFall=inFall; window.FALL=FALL; }catch(e){}
function fallCard(what){
  if(FALL.err&&!FALL.loading)return '<div class="ex-empty"><p class="t">Couldn’t load '+escapeHtml(mcNowLabel())+' '+what+'.</p><div style="margin-top:12px"><button class="btn primary" onclick="fallRetry()">Retry</button></div></div>';
  return '<div class="ex-empty"><p class="t">Loading '+escapeHtml(mcNowLabel())+' '+what+'…</p></div>';
}
/* ---- Explore ---- */
var _exRender0=renderExplore;
renderExplore=function(){
  if(!fallActive())return _exRender0.apply(this,arguments);
  try{ renderExploreRail(); }catch(e){}
  if(!FALL.ready){ fallEnsure(); var o=document.getElementById('exOut'); if(o)o.innerHTML=fallCard(exMode==='professors'?'professors':'classes'); return; }
  var r=inFall(function(){ return _exRender0(); });
  /* the lists' headings say "this term": on Fall, name it */
  try{ var o2=document.getElementById('exOut'); if(o2)o2.querySelectorAll('.grouphead,.ex-hl').forEach(function(h){
    var w=document.createTreeWalker(h,NodeFilter.SHOW_TEXT,null,false), n; while((n=w.nextNode()))n.nodeValue=n.nodeValue.replace(/this term/i,mcNowLabel()); }); }catch(e){}
  return r;
};
var _exRail0=renderExploreRail;
renderExploreRail=function(){ if(FALL.on)return; return _exRail0.apply(this,arguments); };
var _exCtx0=renderExContext;
renderExContext=function(){
  if(!mcTwoTerms()){ exTermSel='spring'; return _exCtx0.apply(this,arguments); }
  var r=_exCtx0.apply(this,arguments);
  try{
    var el=document.getElementById('exContext'), g=el&&el.querySelector('.ex-gesw'); if(!g)return r;
    if(exTermSel==='now'){ var b=[].slice.call(g.querySelectorAll('button')).filter(function(x){ return /^Saved$/.test(x.textContent.trim()); })[0]; if(b)b.remove(); }
    var on=exTermSel==='now';
    g.insertAdjacentHTML('beforeend','<span class="ex-tsep" aria-hidden="true"></span>'
      +'<button type="button" class="ex-term'+(on?'':' on')+'" data-term="spring" aria-pressed="'+(!on)+'" onclick="exSetTerm(\'spring\')">'+escapeHtml(mcTermLabel())+'</button>'
      +'<button type="button" class="ex-term'+(on?' on':'')+'" data-term="now" aria-pressed="'+on+'" onclick="exSetTerm(\'now\')">'+escapeHtml(mcNowLabel())+'</button>');
  }catch(e){}
  return r;
};
window.exSetTerm=function(t){
  t=(t==='now'&&mcTwoTerms())?'now':'spring';
  if(t===exTermSel)return;
  exTermSel=t;
  if(t==='now'){ window.exSaved=false; fallEnsure(); }
  try{ renderExContext(); }catch(e){}
  try{ renderExplore(); }catch(e){}
};
/* ---- which term does a page opened from HERE belong to? ---- */
function fallLensForOpen(code,forProf){
  if(!mcTwoTerms())return false;
  var v=fallViewId();
  if(!forProf){
    var frp=document.getElementById('frpBack');
    if(frp&&frp.classList.contains('open')){ try{ var f=findFriend(profileFriendId); return !!f&&frpTermOf(f)==='now'; }catch(e){ return false; } }
  }
  if(v==='explore')return exTermSel==='now';
  if(v==='class')return cpNow;
  if(v==='prof')return pfNow;
  if(forProf)return false;
  if(v==='home'){ try{ return nowCodesWanted().indexOf(code)>=0; }catch(e){ return false; } }
  if(v==='sched'){ try{ return window.schedTab==='mine'&&mcTermView()==='now'; }catch(e){ return false; } }
  return false;
}
var _ocp0=window.openClassPage;
window.openClassPage=function(code,ev){
  cpNow=!!code&&fallLensForOpen(code,false);
  if(cpNow)fallEnsure();
  return _ocp0.apply(this,arguments);
};
var _op0=openProf;
openProf=function(id){
  pfNow=fallLensForOpen(null,true);
  if(pfNow)fallEnsure();
  return _op0.apply(this,arguments);
};
window.openProf=openProf;
/* ---- the class page and the professor page ---- */
var _rcp0=renderClassPage;
renderClassPage=function(){
  if(!(cpNow&&mcTwoTerms()))return _rcp0.apply(this,arguments);
  var out=document.getElementById('cpOut'); if(!out)return;
  if(!FALL.ready){
    fallEnsure();
    var crumb=document.getElementById('cpCrumb'); if(crumb)crumb.textContent=cpCode||'';
    var bt=document.getElementById('cpBackTxt'); if(bt)bt.textContent=cpBackLabel();
    out.innerHTML=fallCard('classes'); return;
  }
  inFall(function(){ return _rcp0(); });
  try{ [].slice.call(out.querySelectorAll('.cp-fallnote')).forEach(function(n){ n.remove(); }); }catch(e){}
  out.insertAdjacentHTML('afterbegin','<div class="cp-fallnote" role="note"><b>'+escapeHtml(mcNowLabel())+'</b> · read-only'
    +'<button type="button" onclick="cpViewSpring()">View '+escapeHtml(mcTermLabel())+'</button></div>');
};
window.cpViewSpring=function(){ cpNow=false; renderClassPage(); try{ window.scrollTo({top:0}); }catch(e){} };
var _rpp0=renderProfPage;
renderProfPage=function(){
  if(!(pfNow&&mcTwoTerms()))return _rpp0.apply(this,arguments);
  var out=document.getElementById('pfOut'); if(!out)return;
  if(!FALL.ready){ fallEnsure(); out.innerHTML=fallCard('professors'); return; }
  return inFall(function(){ return _rpp0(); });
};
/* ---- Fall is read-only: Add / Save / Watch / plan controls say so and write nothing ---- */
var FALL_WRITE_RE=/\b(toggleSaveClass|wcWatchSec|mcEnrollSec|mcLeaveSec|toggleMyClass|toggleSecSwap|toggleWatchClass|mcAddSec)\b/;
document.addEventListener('click',function(e){
  try{
    if(!fallViewing())return;
    var t=e.target&&e.target.closest?e.target.closest('#view-explore,#view-class,#view-prof'):null; if(!t)return;
    var el=e.target.closest('[onclick],[data-pl-act]'), hit=false;
    while(el&&t.contains(el)){
      var pa=el.getAttribute('data-pl-act');
      if(pa&&pa!=='open'&&pa!=='q'){ hit=true; break; }
      var oc=el.getAttribute('onclick')||'';
      if(FALL_WRITE_RE.test(oc)){ hit=true; break; }
      el=el.parentElement&&el.parentElement.closest?el.parentElement.closest('[onclick],[data-pl-act]'):null;
    }
    if(!hit)return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    if(typeof frToast==='function')frToast(mcNowLabel()+' is read-only — switch to '+mcTermLabel()+' to add');
  }catch(_e){}
},true);
"""

one("try{ window.loadNowMine=loadNowMine; window.loadNowSeats=loadNowSeats; }catch(e){}\n",
    "try{ window.loadNowMine=loadNowMine; window.loadNowSeats=loadNowSeats; }catch(e){}\n/* website-explore-term (2026-10-14) */" + BLOCK)

# a professor's "teaching" list names its term
one("""teachHtml='<section class="pp-sec"><h3>Teaching this term<em>'""",
    """teachHtml='<section class="pp-sec"><h3>Teaching '+((pfNow&&mcTwoTerms())?escAcc(mcNowLabel()):'this term')+'<em>'""")

# a Fall professor page never borrows the sections a scraped professor record carries from Spring's feed
one("  if(!teach.length&&p._spTeaches&&p._spTeaches.length)teach=p._spTeaches;",
    "  if(!teach.length&&p._spTeaches&&p._spTeaches.length&&!(pfNow&&mcTwoTerms()))teach=p._spTeaches;   /* Spring's sections never sit under Fall */")

# the switch + the read-only strip look
one(""".ex-gesw button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}""",
    """.ex-gesw button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
/* website-explore-term (2026-10-14): Spring 2027 | Fall 2026 beside the filters; Fall pages say they are read-only */
.ex-gesw .ex-tsep{width:1px;align-self:stretch;margin:6px 6px;background:var(--line);flex:none}
.cp-fallnote{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 12px;padding:9px 14px;border-radius:12px;
  border:1px solid var(--line);background:var(--panel-2);color:var(--text-2);font-size:14px}
.cp-fallnote button{margin-left:auto;border:1px solid var(--line);background:var(--panel);color:var(--accent);border-radius:999px;
  padding:5px 13px;font:inherit;font-weight:700;cursor:pointer}
@media (hover:hover){.cp-fallnote button:hover{border-color:rgba(var(--accent-rgb),.45)}}
@media (max-width:640px){
  #exContext .ex-gesw:has(.ex-term){flex-wrap:wrap;overflow:visible;row-gap:6px}
  #exContext .ex-gesw .ex-tsep{flex:0 0 100%;height:0;margin:0;background:none}
}""")

f.write_text(s)
print('ok')
