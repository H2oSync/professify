#!/usr/bin/env python3
"""The website gets the app's wall between the two terms (Tate, 2026-10-14: "do the fall / spring").

Same rule as the phone app (spring-wall, 2026-10-08), now in index.html:
- CFG.TERM (Spring 2027, 2274) is the term you CHOOSE in: the seat feed, Explore, class and professor pages,
  Plans, the Planner, watches, adds and seat alerts. My Classes on the website is now your SPRING list —
  the one you add to.
- CFG.NOW_TERM (Fall 2026, 2268) is the term you are SITTING in: Home (your schedule, today's classes, the
  stories strip, friends' week cards, "in class till 3", "free now"), group free-time, Rate's "taking now"
  professors and the Fall chip on My Classes and on a friend's page. Your Fall classes are read-only here and
  are read by term from saved_classes / my_sections; their times come from your own section rows, and a
  missing time is looked up in the NOW term's seat rows for that course only (NOW_SEATS) — never in Spring's.
- From CFG.NOW_UNTIL (2027-01-25, Spring's first day of classes, Pacific) "now" is TERM by itself, and with
  NOW_TERM empty or equal to TERM the website is exactly the single-term site it was.

Also fixed on the way, because two terms make them real:
- a friend's my_sections rows were read with no term, so their Spring sections would have drawn on their Fall week;
- the seat cache, this device's My Classes and the friends cache were not keyed by term (a Fall list cached on
  this device would have been offered back as Spring);
- the Degree Progress Report filed every ungraded class in a term older than the newest one as FINISHED — so a
  report printed after Spring registration would have put your Fall classes in Past Classes. Now: ungraded in
  Fall 2026 → Fall (now); registered for Spring 2027 → your Spring My Classes; finished → Past Classes;
- the waitlist-position write had no term;
- the static Fall 2026 instructor table stops answering for Spring; "Not on the Fall 2026 class schedule" and
  the Planner's planningTerm() follow the term.
- PROFESSIFY_CONFIG is merged over (a page may set just the terms), as on the phone.

Usage: python3 website-spring-wall-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-spring-wall (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ config
one("window.PROFESSIFY_CONFIG = {\n  SUPABASE_URL:", "window.PROFESSIFY_CONFIG = Object.assign({\n  SUPABASE_URL:")
one("""  TERM: '2268',
  TERM_LABEL: 'Fall 2026',
  /* Both halves of the link-preview path""", """  /* THE TERMS — website-spring-wall (2026-10-14), the same wall as the phone app (app/index.html CFG).
     TERM is the term students CHOOSE in: the seat feed, Explore, class and professor pages, Plans, the
     Planner, watches and every write to My Classes. NOW_TERM is the term they are SITTING in: Home, the
     stories strip, friends' weeks, "in class now", group free time and Rate's current professors. From
     NOW_UNTIL (TERM's first day of classes, Pacific) TERM is both. NOW_TERM empty or equal to TERM = the
     single-term site. Keep these equal to the phone's. */
  TERM: '2274',
  TERM_LABEL: 'Spring 2027',
  NOW_TERM: '2268',
  NOW_LABEL: 'Fall 2026',
  NOW_UNTIL: '2027-01-25',
  /* Both halves of the link-preview path""")
one("""  SHARE_PREVIEW: true
};
</script>""", """  SHARE_PREVIEW: true
}, window.PROFESSIFY_CONFIG || {});   /* a page (or a test) may set just the terms — website-spring-wall (2026-10-14) */
</script>""")

# ================================================================ the two-term helpers
one("""try{ window.mcTerm=mcTerm; window.mcTermLabel=mcTermLabel; }catch(e){}""",
"""try{ window.mcTerm=mcTerm; window.mcTermLabel=mcTermLabel; }catch(e){}
/* ================================================================================================
   TWO TERMS — website-spring-wall (2026-10-14). The phone's wall (spring-wall, 2026-10-08), here.
   ================================================================================================
   mcTerm() is the term you CHOOSE in (Spring 2027): everything that picks, plans, watches or saves.
   mcNowTerm() is the term you are SITTING in (Fall 2026): Home, the stories strip, a friend's week
   now, "in class till 3", group free time and the professors you have right now.
   They are never mixed. Your Fall classes live in NOW_MINE (read-only here), a friend's in f.now, and
   the only Fall seat rows this page ever holds are NOW_SEATS — the courses someone here is actually
   in, used for one thing: the time of a Fall section we know only by course or class number. They
   never enter SEAT_SECTIONS, Explore, a professor's "teaching" list or a seat count.
   From NOW_UNTIL (Spring's first day of classes, Pacific) "now" is TERM, and every helper below
   collapses to the single-term site: nowMine() is My Classes, frNow(f) is f. */
function mcPacificDay(){
  try{ return new Intl.DateTimeFormat('en-CA',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()); }
  catch(e){ var d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
}
function mcNowTerm(){
  var c=cfg(), n=String(c.NOW_TERM||'').trim(), u=String(c.NOW_UNTIL||'').trim();
  if(!n||n===mcTerm())return mcTerm();
  if(u&&mcPacificDay()>=u)return mcTerm();
  return n;
}
function mcTwoTerms(){ return mcNowTerm()!==mcTerm(); }
function mcNowLabel(){ return mcTwoTerms()?String(cfg().NOW_LABEL||mcNowTerm()):mcTermLabel(); }
try{ window.mcNowTerm=mcNowTerm; window.mcTwoTerms=mcTwoTerms; window.mcNowLabel=mcNowLabel; }catch(e){}
/* Your classes in the now-term: {classes:[code], meta:{code:{secs:[{crn,section,prof,days,status,wlPos}], time, prof, crn}}}.
   Same shape as myClasses / myClassMeta, so every function that takes (codes, meta) reads it unchanged. */
var NOW_MINE={classes:[],meta:{},loaded:false};
/* The now-term's seat rows, by course code — only for courses in NOW_MINE or a friend's now list. */
var NOW_SEATS={};
function nowMine(){
  if(mcTwoTerms())return NOW_MINE;
  return {classes:(typeof myClasses!=='undefined'?myClasses:[]),meta:(typeof myClassMeta!=='undefined'?myClassMeta:{})};
}
function isNowMine(code){ return nowMine().classes.indexOf(code)>=0; }
/* A friend as they are NOW. The loader builds f.now; a friend with no now-term rows is in nothing now. */
function frNow(f){
  if(!f||f._now||!mcTwoTerms())return f;
  return f.now||Object.assign({},f,{classes:[],crns:[],secs:[],wl:{},classAdds:[],_now:true});
}
/* What you are taking, either term — for requirements and prerequisites, where a Fall class in progress and a
   Spring class you are registered for both count as "taking", and neither as finished. */
function myTakingCodes(){
  var a=(typeof myClasses!=='undefined'?myClasses:[]).slice();
  if(mcTwoTerms())NOW_MINE.classes.forEach(function(c){ if(a.indexOf(c)<0)a.push(c); });
  return a;
}
try{ window.nowMine=nowMine; window.frNow=frNow; window.isNowMine=isNowMine; window.myTakingCodes=myTakingCodes; }catch(e){}
/* The now-term rows for one course, in the shape clsSections() gives (the time is all a now view asks of them). */
function nowSections(code){ return (typeof clsSections==='function')?clsSections(code,NOW_SEATS):[]; }
function nowSecByCrn(code,crn){ return (typeof secByCrn==='function')?secByCrn(code,crn,NOW_SEATS):null; }
function nowMineKey(){ return (typeof sbUser!=='undefined'&&sbUser)?('professify_now_mine:'+sbUser.id+':'+mcNowTerm()):''; }
function nowMineHydrate(){
  if(!mcTwoTerms()||NOW_MINE.loaded||NOW_MINE.classes.length)return;
  try{ var k=nowMineKey(); var c=k?JSON.parse(localStorage.getItem(k)||'null'):null;
       if(c&&Array.isArray(c.classes))NOW_MINE={classes:c.classes,meta:(c.meta&&typeof c.meta==='object')?c.meta:{},loaded:false,uid:sbUser.id}; }catch(e){}
}
/* Read-only: the only now-term write on this page is a Degree Progress Report's in-progress classes (confirmDprImport),
   as on the phone. saved_classes decides WHICH classes; my_sections adds the
   section, professor and meeting days — and may not add a course on its own (the friends loader's rule). */
async function loadNowMine(){
  if(!mcTwoTerms()||typeof backendReady!=='function'||!backendReady()||typeof sbUser==='undefined'||!sbUser)return;
  if(NOW_MINE.uid&&NOW_MINE.uid!==sbUser.id)NOW_MINE={classes:[],meta:{},loaded:false};   /* another account's, from this tab */
  nowMineHydrate();
  var t=mcNowTerm(), uid=sbUser.id;
  try{
    var a=await sb.from('saved_classes').select('code,class_nbr').eq('user_id',uid).eq('term',t);
    if(a.error||!Array.isArray(a.data))return;          /* a failed read is not "no classes" — keep what we have */
    var b=await sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id',uid).eq('term',t);
    if(!sbUser||sbUser.id!==uid)return;                 /* signed out or switched while we waited */
    var classes=[], meta={};
    a.data.forEach(function(r){ var c=String(r.code||'').trim(); if(c&&classes.indexOf(c)<0)classes.push(c); });
    if(!b.error&&Array.isArray(b.data))b.data.forEach(function(r){
      var c=String(r.code||'').trim(); if(!c||classes.indexOf(c)<0)return;
      var m=meta[c]||(meta[c]={secs:[]}); m.secs=m.secs||[];
      m.secs.push({crn:String(r.class_nbr||''),section:r.section||'',prof:r.instructor||'',days:r.days||'',
                   status:(r.status==='waitlisted'?'waitlisted':'enrolled'),wlPos:(r.wl_pos!=null?r.wl_pos:null)});
      var f0=m.secs[0]; if(f0){ m.prof=f0.prof||m.prof; if(f0.days)m.time=f0.days; }
    });
    /* A class number saved with the course but no section row: kept, so its time can come from the now-term rows. */
    a.data.forEach(function(r){ var c=String(r.code||'').trim(); if(!c||r.class_nbr==null||r.class_nbr==='')return;
      var m=meta[c]||(meta[c]={}); if(!m.secs||!m.secs.length)m.crn=String(r.class_nbr); });
    NOW_MINE={classes:classes,meta:meta,loaded:true,uid:uid};
    try{ localStorage.setItem(nowMineKey(),JSON.stringify(NOW_MINE)); }catch(e){}
  }catch(e){ return; }
  nowAfterLoad();
}
/* Every course anyone on this page is in now, so their Fall times can be found. */
function nowCodesWanted(){
  var out=NOW_MINE.classes.slice();
  try{ (typeof friendsList!=='undefined'?friendsList:[]).forEach(function(f){ var n=frNow(f); (n&&n.classes||[]).forEach(function(c){ if(out.indexOf(c)<0)out.push(c); }); }); }catch(e){}
  return out;
}
var _nowSeatAsked={};
async function loadNowSeats(){
  if(!mcTwoTerms())return;
  var c=cfg(); if(!c.SUPABASE_URL||!c.SUPABASE_ANON_KEY)return;
  var want=nowCodesWanted().filter(function(x){ return x&&!_nowSeatAsked[x]; });
  if(!want.length)return;
  want.forEach(function(x){ _nowSeatAsked[x]=1; });
  var base=c.SUPABASE_URL.replace(/\\/$/,''), hdr={apikey:c.SUPABASE_ANON_KEY,Authorization:'Bearer '+c.SUPABASE_ANON_KEY};
  var got=false;
  for(var i=0;i<want.length;i+=40){
    var chunk=want.slice(i,i+40);
    var list='('+chunk.map(function(x){ return '"'+String(x).replace(/["\\\\]/g,'')+'"'; }).join(',')+')';
    try{
      var res=await fetch(base+'/rest/v1/course_seats?term=eq.'+encodeURIComponent(mcNowTerm())+'&course_code=in.'+encodeURIComponent(list)
        +'&select=course_code,title,section,instructor,days,status,class_nbr&order=course_code.asc,class_nbr.asc&limit=1000',{headers:hdr});
      if(!res.ok){ chunk.forEach(function(x){ delete _nowSeatAsked[x]; }); continue; }
      var rows=await res.json(); if(!Array.isArray(rows)){ chunk.forEach(function(x){ delete _nowSeatAsked[x]; }); continue; }
      chunk.forEach(function(x){ NOW_SEATS[x]=[]; });
      rows.forEach(function(r){ var k=String(r.course_code||'').trim(); if(k&&NOW_SEATS[k])NOW_SEATS[k].push(r); });
      got=true;
    }catch(e){ chunk.forEach(function(x){ delete _nowSeatAsked[x]; }); }
  }
  if(got)nowRepaint();
}
function nowRepaint(){
  try{ if(typeof renderHome==='function'&&document.getElementById('view-home')&&document.getElementById('view-home').classList.contains('active'))renderHome(); }catch(e){}
  try{ if(typeof renderMyClasses==='function')renderMyClasses(); }catch(e){}
  try{ if(typeof renderFriendProfile==='function'&&typeof profileFriendId!=='undefined'&&profileFriendId&&document.getElementById('frpModal')&&document.getElementById('frpModal').classList.contains('open'))renderFriendProfile(); }catch(e){}
}
function nowAfterLoad(){ nowRepaint(); try{ loadNowSeats(); }catch(e){} }
try{ window.loadNowMine=loadNowMine; window.loadNowSeats=loadNowSeats; }catch(e){}""")

# frNow builds a friend's NOW view from the loader's partial f.now (cached, not enumerable — never saved)
one("""function frNow(f){
  if(!f||f._now||!mcTwoTerms())return f;
  return f.now||Object.assign({},f,{classes:[],crns:[],secs:[],wl:{},classAdds:[],_now:true});
}""", """function frNow(f){
  if(!f||f._now||!mcTwoTerms())return f;
  if(f.__nowView)return f.__nowView;
  var n=(f.now&&typeof f.now==='object')?f.now:{};
  var v=Object.assign({},f,{classes:(n.classes||[]).slice(),crns:(n.crns||[]).slice(),secs:(n.secs||[]).slice(),
    wl:Object.assign({},n.wl||{}),classAdds:(n.classAdds||[]).slice(),history:f.history||[],_now:true});
  delete v.now;
  try{ Object.defineProperty(f,'__nowView',{value:v,enumerable:false,configurable:true,writable:true}); }catch(e){}
  return v;
}""")

# ================================================================ this device's lists belong to one term
one("""<script>
/* Theme: set before paint to avoid a flash.""", """<script>
/* THIS DEVICE'S LISTS BELONG TO ONE TERM — website-spring-wall (2026-10-14). My Classes, its sections, the pending-
   change queue and the watchlist were kept in localStorage with no term, so the morning the site moved to Spring this
   device would have shown its Fall list as Spring, and the sign-in sync would have been one queued "add" away from
   writing Fall courses into Spring. Each key is now the term's own: 2268 keeps the old names (that is all a device has
   ever held), any other term adds ":<term>". Nothing is purged, so an old tab still open on Fall writes Fall's keys and
   can never reach Spring's. The seat cache moves to a per-term key; the old one is dropped. */
window.MC_LS=function(k){ var t=String((window.PROFESSIFY_CONFIG||{}).TERM||'2268'); return t==='2268'?k:(k+':'+t); };
(function(){ try{ localStorage.removeItem('professify_seats_cache'); }catch(e){} })();
</script>
<script>
/* Theme: set before paint to avoid a flash.""")
one("try{const _wc=JSON.parse(localStorage.getItem('professify_watch_classes')||'[]')",
    "try{const _wc=JSON.parse(localStorage.getItem(MC_LS('professify_watch_classes'))||'[]')")
one("try{const _wm=JSON.parse(localStorage.getItem('professify_watch_meta')||'{}')",
    "try{const _wm=JSON.parse(localStorage.getItem(MC_LS('professify_watch_meta'))||'{}')")
one("function saveWatchMeta(){try{localStorage.setItem('professify_watch_meta',",
    "function saveWatchMeta(){try{localStorage.setItem(MC_LS('professify_watch_meta'),")
one("function saveWatchClasses(){try{localStorage.setItem('professify_watch_classes',",
    "function saveWatchClasses(){try{localStorage.setItem(MC_LS('professify_watch_classes'),")
one("try{const _mc=JSON.parse(localStorage.getItem('professify_my_classes')||'[]')",
    "try{const _mc=JSON.parse(localStorage.getItem(MC_LS('professify_my_classes'))||'[]')")
one("function saveMyClasses(){try{localStorage.setItem('professify_my_classes',",
    "function saveMyClasses(){try{localStorage.setItem(MC_LS('professify_my_classes'),")
one("var MC_PEND_KEY='professify_mc_pending';",
    "var MC_PEND_KEY=MC_LS('professify_mc_pending');")
one("try{const _mcm=JSON.parse(localStorage.getItem('professify_my_class_meta')||'{}')",
    "try{const _mcm=JSON.parse(localStorage.getItem(MC_LS('professify_my_class_meta'))||'{}')")
one("function saveMyClassMeta(){try{localStorage.setItem('professify_my_class_meta',",
    "function saveMyClassMeta(){try{localStorage.setItem(MC_LS('professify_my_class_meta'),")
one("""  try{ localStorage.setItem('professify_seats_cache',JSON.stringify({ts:SEATS_UPDATED_AT,idx:idx,sec:sec})); }catch(e){/* over quota — skip caching */}""",
    """  try{ localStorage.setItem('professify_seats_cache:'+mcTerm(),JSON.stringify({ts:SEATS_UPDATED_AT,idx:idx,sec:sec})); }catch(e){/* over quota — skip caching */}""")
one("""    var raw=localStorage.getItem('professify_seats_cache'); if(!raw)return false;""",
    """    var raw=localStorage.getItem('professify_seats_cache:'+mcTerm()); if(!raw)return false;""")
one("""    localStorage.setItem('professify_friends_cache_'+sbUser.id,JSON.stringify({""",
    """    localStorage.setItem('professify_friends_cache_'+sbUser.id+':'+mcTerm(),JSON.stringify({""")
one("""    var raw=localStorage.getItem('professify_friends_cache_'+sbUser.id); if(!raw)return false;""",
    """    var raw=localStorage.getItem('professify_friends_cache_'+sbUser.id+':'+mcTerm()); if(!raw)return false;""")

# ================================================================ the seat accessors take a source
one("""function clsSections(code){
  var secs=(typeof SEAT_SECTIONS!=='undefined'&&SEAT_SECTIONS&&SEAT_SECTIONS[code])?SEAT_SECTIONS[code]:[];""",
"""function clsSections(code,src){
  /* src: another term's rows (NOW_SEATS) — website-spring-wall (2026-10-14). Default: this term's feed. */
  var S=src||((typeof SEAT_SECTIONS!=='undefined')?SEAT_SECTIONS:null);
  var secs=(S&&S[code])?S[code]:[];""")
one("""function secByCrn(code,crn){var list=(typeof clsSections==='function')?clsSections(code):[];""",
    """function secByCrn(code,crn,src){var list=(typeof clsSections==='function')?clsSections(code,src):[];""")

# ================================================================ my classes' times: a Fall class reads Fall's rows
one("""function myClassTime(code,meta){
  meta=meta||myClassMeta;
  if(meta[code]&&meta[code].time)return meta[code].time;""",
"""function myClassTime(code,meta){
  meta=meta||myClassMeta;
  if(meta[code]&&meta[code].time)return meta[code].time;
  /* A now-term class with no section row: its own class number in the now-term rows, else that course's first
     timed section there — the same rule as below, but never Spring's sections (website-spring-wall, 2026-10-14). */
  if(meta===NOW_MINE.meta&&mcTwoTerms()){
    var _m=meta[code], _s=(_m&&_m.crn)?nowSecByCrn(code,_m.crn):null;
    if(!_s){ var _t=nowSections(code).filter(function(x){ return x.days&&parseMeet(x.days); }); if(_t.length)_s=_t[0]; }
    return (_s&&_s.days)||'';
  }""")
one("""    else { list.push({code:code,key:code,meet:parseMeet(myClassTime(code))}); }""",
    """    else { list.push({code:code,key:code,meet:parseMeet(myClassTime(code,meta===NOW_MINE.meta?meta:undefined))}); }""")

# ================================================================ a friend's week: their now view reads now rows
one("""    if(byCode[code]&&typeof secByCrn==='function')sec=secByCrn(code,byCode[code]);""",
    """    if(byCode[code]&&typeof secByCrn==='function')sec=secByCrn(code,byCode[code],(f&&f._now)?NOW_SEATS:null);""")
one("""      var all=(typeof clsSections==='function')?clsSections(code):[];
      var timed=all.filter(function(x){return x.days&&typeof parseMeet==='function'&&parseMeet(x.days);});""",
    """      var all=(typeof clsSections==='function')?clsSections(code,(f&&f._now)?NOW_SEATS:null):[];
      var timed=all.filter(function(x){return x.days&&typeof parseMeet==='function'&&parseMeet(x.days);});""")

# ================================================================ "right now" is the now-term
one("""    var fm=(typeof hmFriendMeets==='function')?hmFriendMeets(f):{meets:[]};
    return (fm.meets||[]).filter(function(m){ return m&&!m.assumed&&okMeet(m.meet); });""",
    """    var fm=(typeof hmFriendMeets==='function')?hmFriendMeets(frNow(f)):{meets:[]};
    return (fm.meets||[]).filter(function(m){ return m&&!m.assumed&&okMeet(m.meet); });""")
one("""    var mm=(typeof myClassMeets==='function')?myClassMeets(myClasses):[];""",
    """    var _nm=nowMine(), mm=(typeof myClassMeets==='function')?myClassMeets(_nm.classes,_nm.meta):[];""")
one("""    if(!(typeof myClasses!=='undefined'&&myClasses.length))return {busy:[],unknown:[],noData:true};
    (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(code){
      var meta=(typeof myClassMeta!=='undefined')?myClassMeta[code]:null;
      var secs=(meta&&Array.isArray(meta.secs)&&meta.secs.length)?meta.secs:null;
      if(secs)secs.forEach(function(sec){ push(code,sec.days||''); });
      else push(code,(typeof myClassTime==='function')?myClassTime(code):'');
    });""", """    /* Free time is about the week you are in: the now-term (website-spring-wall, 2026-10-14). */
    var _nm=nowMine();
    if(!_nm.classes.length)return {busy:[],unknown:[],noData:true};
    _nm.classes.forEach(function(code){
      var meta=_nm.meta[code];
      var secs=(meta&&Array.isArray(meta.secs)&&meta.secs.length)?meta.secs:null;
      if(secs)secs.forEach(function(sec){ push(code,sec.days||''); });
      else push(code,(typeof myClassTime==='function')?myClassTime(code,_nm.meta===NOW_MINE.meta?_nm.meta:undefined):'');
    });""")
one("""    var f=(typeof findFriend==='function')?findFriend(m.id):null;
    if(!f)return {busy:[],unknown:[],noData:true};""",
    """    var f=frNow((typeof findFriend==='function')?findFriend(m.id):null);
    if(!f)return {busy:[],unknown:[],noData:true};""")

# ================================================================ Home is the now-term
one("""  var mine={}; try{(myClasses||[]).forEach(function(c){mine[c]=1;});}catch(e){}""",
    """  var mine={}; try{(nowMine().classes||[]).forEach(function(c){mine[c]=1;});}catch(e){}""")
one("""function hmOverlap(codes){
  var n=0;
  try{(codes||[]).forEach(function(c){if(typeof isMyClass==='function'&&isMyClass(c))n++;});}catch(e){}""",
"""function hmOverlap(codes){
  var n=0;
  try{(codes||[]).forEach(function(c){if(isNowMine(c))n++;});}catch(e){}""")
one("""    var sh=(typeof isMyClass==='function'&&isMyClass(c));
    return '<span class="hm-chip'+(sh?' shared':'')""", """    var sh=isNowMine(c);
    return '<span class="hm-chip'+(sh?' shared':'')""")
one("""    (typeof FRIENDS!=='undefined'?FRIENDS:[]).forEach(function(f){
      if(!f||f.id===excludeId)return;
      if((f.classes||[]).indexOf(code)<0)return;""", """    (typeof FRIENDS!=='undefined'?FRIENDS:[]).forEach(function(f){
      if(!f||f.id===excludeId)return;
      if((frNow(f).classes||[]).indexOf(code)<0)return;""")
one("""      var mine=(typeof isMyClass==='function'&&isMyClass(m.code));""", """      var mine=isNowMine(m.code);""")
one("""      if(typeof isMyClass==='function'&&isMyClass(code))return ' &mdash; <b class="cl-you">""",
    """      if(isNowMine(code))return ' &mdash; <b class="cl-you">""")
one("""function hmFriendSchedCard(f,opts){
  var ov=hmOverlap(f.classes);""", """function hmFriendSchedCard(f,opts){
  f=frNow(f);                       /* Home shows where they are now — website-spring-wall (2026-10-14) */
  var ov=hmOverlap(f.classes);""")
one("""    var mine={}, n=0;
    Object.keys((typeof myClassMeta!=='undefined'&&myClassMeta)||{}).forEach(function(c){
      var mm=myClassMeta[c]; if(!mm)return;""", """    var mine={}, n=0, _nmeta=nowMine().meta||{};
    Object.keys(_nmeta).forEach(function(c){
      var mm=_nmeta[c]; if(!mm)return;""")
one("""      (friendsList||[]).forEach(function(f){
        if(!f||!f.classes||!f.classes.length)return;
        var fm=hmFriendMeets(f);""", """      (friendsList||[]).forEach(function(f){
        f=frNow(f);
        if(!f||!f.classes||!f.classes.length)return;
        var fm=hmFriendMeets(f);""")
one("""    (friendsList||[]).forEach(function(f){
      if(f.classes&&f.classes.length&&!schedUsers[f.id]){""", """    (friendsList||[]).forEach(function(f){
      f=frNow(f);
      if(f.classes&&f.classes.length&&!schedUsers[f.id]){""")
one("""function hmMiniCalHtml(){
  var codes=(typeof myClasses!=='undefined')?myClasses:[];
  // Section-aware: one block per section a student is in, so BOTH sides of a time
  // conflict show (not just the first). Overlaps split into side-by-side lanes below.
  var meetsAll=(typeof myClassMeets==='function')?myClassMeets(codes):[];""", """function hmMiniCalHtml(){
  var _nm=nowMine(), codes=_nm.classes;      /* the week you are in — website-spring-wall (2026-10-14) */
  // Section-aware: one block per section a student is in, so BOTH sides of a time
  // conflict show (not just the first). Overlaps split into side-by-side lanes below.
  var meetsAll=(typeof myClassMeets==='function')?myClassMeets(codes,_nm.meta):[];""")
one("""  var conf=(typeof myClassConflicts==='function')?myClassConflicts(codes):{bad:{}};
  var cols=DAYS.map(function(d,di){""", """  var conf=(typeof myClassConflicts==='function')?myClassConflicts(codes,_nm.meta):{bad:{}};
  var cols=DAYS.map(function(d,di){""")
one("""  var head='<div class="hm-ct">My schedule<button class="hm-more" onclick="event.stopPropagation();hmOpenCal()">Open →</button></div>';""",
    """  var head='<div class="hm-ct">My schedule'+(mcTwoTerms()?' <span class="hm-termtag">'+esc(mcNowLabel())+'</span>':'')+'<button class="hm-more" onclick="event.stopPropagation();hmOpenCal()">Open →</button></div>';""")
one("""function hmCurProfList(){
  var out=[], byKey={};
  var codes=(typeof myClasses!=='undefined'&&myClasses)?myClasses:[];
  codes.forEach(function(code){
    var meta=(typeof myClassMeta!=='undefined')?myClassMeta[code]:null;""", """function hmCurProfList(){
  var out=[], byKey={};
  var _nm=nowMine(), codes=_nm.classes;      /* the professors you have right now — the now-term */
  codes.forEach(function(code){
    var meta=_nm.meta[code];""")

# ================================================================ Rate: "taking now" and the terms you can rate
one("""    var tn=(typeof termNow==='function')?termNow():{term:'',year:0};
    (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(code){
      var nm=(typeof myClassMeta!=='undefined'&&myClassMeta[code]&&myClassMeta[code].prof)||'';
      if(!nm){var ci=(typeof classInfo==='function')?classInfo(code):null;nm=(ci&&ci.best&&ci.best.name)||'';}""",
"""    var tn=(typeof termNow==='function')?termNow():{term:'',year:0};
    var _nm=nowMine();                  /* the now-term — website-spring-wall (2026-10-14) */
    _nm.classes.forEach(function(code){
      var nm=(_nm.meta[code]&&_nm.meta[code].prof)||'';
      /* Never this term's feed for a now-term class: Spring's first instructor is not who teaches you in Fall. */
      if(!nm&&_nm.meta===NOW_MINE.meta&&mcTwoTerms()){ var _c=_nm.meta[code], _s=(_c&&_c.crn)?nowSecByCrn(code,_c.crn):null; nm=(_s&&_s.name)||''; }
      else if(!nm){var ci=(typeof classInfo==='function')?classInfo(code):null;nm=(ci&&ci.best&&ci.best.name)||'';}""")
one("""  var m=/^([A-Za-z]+)\\s+(\\d{4})$/.exec(APP_TERM); if(!m)return [];""",
    """  var m=/^([A-Za-z]+)\\s+(\\d{4})$/.exec(mcNowLabel()||APP_TERM); if(!m)return [];   /* you rate the term you are in, not the one you are choosing */""")

# ================================================================ friends: their now-term, read by term, kept apart
one("""  let classMap={},histMap={},addMap={},wlMap={},crnsMap={},secsMap={};""",
    """  let classMap={},histMap={},addMap={},wlMap={},crnsMap={},secsMap={},nowMap={};""")
one("""      const fs=await sb.from('my_sections')
        .select('user_id,code,class_nbr,section,instructor,days,status,wl_pos')
        .in('user_id',friendIds);""", """      /* .eq('term') — website-spring-wall (2026-10-14). This read had no term, so with two terms a friend's
         Spring sections would have drawn on the week they're in now. */
      const fs=await sb.from('my_sections')
        .select('user_id,code,class_nbr,section,instructor,days,status,wl_pos')
        .in('user_id',friendIds).eq('term',mcTerm());""")
one("""    // classes friends have already completed (see class_history_migration.sql).""", """    /* THEIR NOW-TERM — website-spring-wall (2026-10-14). The same two reads for the term they are sitting in,
       kept in their own map so nothing that chooses (class pages, plans, alerts) ever sees them. Same rule as
       above: saved_classes says which classes, my_sections only adds the section, time and professor. A failed
       read leaves them with no now-term classes — Home then says nothing about them, which is honest. */
    if(mcTwoTerms()){
      try{
        var _nt=mcNowTerm();
        var _na=await sb.from('saved_classes').select('user_id,code,class_nbr,waitlist_pos,created_at').in('user_id',friendIds).eq('term',_nt);
        if(_na.error&&schemaGap(_na.error))_na=await sb.from('saved_classes').select('user_id,code,class_nbr').in('user_id',friendIds).eq('term',_nt);
        if(!_na.error&&Array.isArray(_na.data)){
          var _nb=await sb.from('my_sections').select('user_id,code,class_nbr,section,instructor,days,status,wl_pos').in('user_id',friendIds).eq('term',_nt);
          _na.data.forEach(function(c){
            if(!c||!c.code)return;
            var o=nowMap[c.user_id]||(nowMap[c.user_id]={classes:[],crns:[],secs:[],wl:{},classAdds:[]});
            if(o.classes.indexOf(c.code)<0)o.classes.push(c.code);
            o.classAdds.push({code:c.code,at:c.created_at});
            if(c.waitlist_pos!=null)o.wl[c.code]=c.waitlist_pos;
            if(c.class_nbr){ var n=String(c.class_nbr); if(o.crns.indexOf(n)<0)o.crns.push(n); o.secs.push({code:c.code,crn:n,at:c.created_at}); }
          });
          if(!_nb.error&&Array.isArray(_nb.data))_nb.data.forEach(function(r){
            var o=nowMap[r.user_id]; if(!o||!r||!r.code||o.classes.indexOf(r.code)<0)return;
            var crn=r.class_nbr!=null?String(r.class_nbr):'';
            var ix=o.secs.findIndex(function(x){ return x.code===r.code&&(!crn||String(x.crn)===crn); });
            var rec={code:r.code,crn:crn,section:r.section||'',instructor:r.instructor||'',days:r.days||'',status:r.status||'enrolled',wlPos:r.wl_pos!=null?r.wl_pos:null};
            if(ix>=0)o.secs[ix]=Object.assign({},o.secs[ix],rec); else o.secs.push(rec);
            if(crn&&o.crns.indexOf(crn)<0)o.crns.push(crn);
          });
        }
      }catch(e){}
    }
    // classes friends have already completed (see class_history_migration.sql).""")
one("""secs:secsMap[id]||[],history:histMap[id]||[],classAdds:addMap[id]||[],wl:wlMap[id]||{},color:colorForId(id)}));""",
    """secs:secsMap[id]||[],history:histMap[id]||[],classAdds:addMap[id]||[],wl:wlMap[id]||{},color:colorForId(id),
    now:mcTwoTerms()?Object.assign({classes:[],crns:[],secs:[],wl:{},classAdds:[]},nowMap[id]||{}):null}));""")
one("""  FRIENDS=friendsList.map(f=>({id:f.id,name:f.name,ini:initials(f.name),color:colorForId(f.id),school:f.school||'',classes:f.classes,crns:f.crns||f.sections||[],secs:f.secs||[],history:f.history,avatar_url:f.avatar_url||''}));""",
    """  FRIENDS=friendsList.map(f=>({id:f.id,name:f.name,ini:initials(f.name),color:colorForId(f.id),school:f.school||'',classes:f.classes,crns:f.crns||f.sections||[],secs:f.secs||[],history:f.history,avatar_url:f.avatar_url||'',now:f.now||null}));""")
one("""  try{ if(classAlertsOn())scanFriendSections(); }catch(e){}""", """  try{ if(classAlertsOn())scanFriendSections(); }catch(e){}
  try{ loadNowSeats(); }catch(e){}      /* their now-term courses' times — website-spring-wall (2026-10-14) */""")

# ================================================================ sign-in: your now-term classes load beside this term's
one("""    const watchP=withTimeout(loadWatchSectionsFromDb(),8000,'loadWatchSectionsFromDb')""",
    """    /* Your now-term classes, read-only, beside this term's — website-spring-wall (2026-10-14). */
    const nowP=withTimeout(loadNowMine(),8000,'loadNowMine');
    const watchP=withTimeout(loadWatchSectionsFromDb(),8000,'loadWatchSectionsFromDb')""")
one("""    await Promise.allSettled([friendsP,profileP,historyP,classesP,watchP,safetyP,pendingP]);""",
    """    await Promise.allSettled([friendsP,profileP,historyP,classesP,watchP,safetyP,pendingP,nowP]);""")

# ================================================================ the waitlist write had no term
one("""      sb.from('saved_classes').upsert({user_id:sbUser.id,code:code,waitlist_pos:pos}),""",
    """      sb.from('saved_classes').upsert({user_id:sbUser.id,term:mcTerm(),code:code,waitlist_pos:pos}),""")

# ================================================================ "taking" means either term (requirements, prerequisites)
one("""function enrolledNowCodes(){
  var out=[];
  try{
    (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(code){
      var m=(typeof myClassMeta!=='undefined')?myClassMeta[code]:null;
      var secs=secsOf(m);
      /* No section data means the student added the course by hand; treat that as enrolled,
         which is what "My Classes" means. With sections, at least one must be enrolled. */
      if(!secs||secs.some(function(x){return x.status!=='waitlisted';}))out.push(canonCode(code));
    });
  }catch(e){}
  return out;
}""", """function enrolledNowCodes(){
  var out=[];
  try{
    /* Both terms: a Fall class in progress and a Spring class you are registered for are both "enrolled, not yet
       finished" to a prerequisite — website-spring-wall (2026-10-14). Each list with its own sections. */
    var lists=[{codes:(typeof myClasses!=='undefined'?myClasses:[]),meta:(typeof myClassMeta!=='undefined'?myClassMeta:{})}];
    if(mcTwoTerms())lists.push({codes:NOW_MINE.classes,meta:NOW_MINE.meta});
    lists.forEach(function(L){ L.codes.forEach(function(code){
      var m=L.meta[code];
      var secs=secsOf(m);
      /* No section data means the student added the course by hand; treat that as enrolled,
         which is what "My Classes" means. With sections, at least one must be enrolled. */
      if(!secs||secs.some(function(x){return x.status!=='waitlisted';})){ var k=canonCode(code); if(out.indexOf(k)<0)out.push(k); }
    }); });
  }catch(e){}
  return out;
}""")
one("""    (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(code){ add(code,'taking now'); });""",
    """    myTakingCodes().forEach(function(code){ add(code,'taking now'); });""")
one("""    var rec=0; try{ rec=(myHistory||[]).length+(myClasses||[]).length+completedCodes().length; }catch(e){}""",
    """    var rec=0; try{ rec=(myHistory||[]).length+myTakingCodes().length+completedCodes().length; }catch(e){}""")
one("""    var takingM={}; try{ (myClasses||[]).forEach(function(c){ var k=canonCode(c); takingM[k]=(takingM[k]||0)+1; }); }catch(e){}""",
    """    var takingM={}; try{ myTakingCodes().forEach(function(c){ var k=canonCode(c); takingM[k]=(takingM[k]||0)+1; }); }catch(e){}""")
one("""uc=window.plUncodedSatisfied(mm,completedCodes(),(myClasses||[]).slice());""",
    """uc=window.plUncodedSatisfied(mm,completedCodes(),myTakingCodes());""")
one("""  try{ (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(c){taking[canon(c)]=1;}); }catch(e){}""",
    """  try{ myTakingCodes().forEach(function(c){taking[canon(c)]=1;}); }catch(e){}""")
one("""  var taken=(typeof myClasses!=='undefined'?myClasses:[]).slice();""",
    """  var taken=myTakingCodes();""")

# ================================================================ Fall-only facts stop answering for Spring
one("""function planningTerm(){const d=new Date();const y=d.getFullYear();return d.getMonth()>=5?`Fall ${y}`:`Spring ${y}`;}""",
    """function planningTerm(){ return mcTermLabel(); }   /* the term you choose in (was: "Fall" from June on, so Fall 2026 in October) — website-spring-wall (2026-10-14) */""")
one("""(notOffered?'Not on the Fall 2026 class schedule':""", """(notOffered?'Not on the '+fpEsc(mcTermLabel())+' class schedule':""")
one("""function confirmedProfs(code){const sec=CONFIRMED_SECTIONS[code];""",
    """/* CONFIRMED_SECTIONS is Fall 2026's instructors (term 2268). It answers only while that is the term you choose in —
   Spring's instructors come from Spring's feed or not at all. website-spring-wall (2026-10-14) */
function confirmedForTerm(){ try{ return mcTerm()==='2268'; }catch(e){ return true; } }
function confirmedProfs(code){if(!confirmedForTerm())return null;const sec=CONFIRMED_SECTIONS[code];""")
one("""function pfCoursesTaught(p){const out=[];if(typeof CONFIRMED_SECTIONS!=='undefined'){""",
    """function pfCoursesTaught(p){const out=[];if(typeof CONFIRMED_SECTIONS!=='undefined'&&confirmedForTerm()){""")

# ================================================================ My Classes: Fall 2026 · Spring 2027
one("""function renderMyClasses(){
  var out=document.getElementById('watchMineOut');if(!out)return;""", """/* MY CLASSES, TWO TERMS — website-spring-wall (2026-10-14), as on the phone. Chips: Fall 2026 · Spring 2027.
   Spring is the list you add to (myClasses, saved under TERM); Fall is what you are in now, read-only, drawn by
   the same calendar from NOW_MINE. It opens on Fall until you have a Spring class; your pick is remembered. */
var MC_TERMVIEW_KEY='tc-mc-term-view';
function mcTermView(){
  if(!mcTwoTerms())return 'term';
  var v=null; try{ v=localStorage.getItem(MC_TERMVIEW_KEY); }catch(e){}
  if(v==='now'||v==='term')return v;
  return (typeof myClasses!=='undefined'&&myClasses.length)?'term':'now';
}
window.mcSetTermView=function(v){
  try{ localStorage.setItem(MC_TERMVIEW_KEY,v==='now'?'now':'term'); }catch(e){}
  try{ renderMyClasses(); }catch(e){}
};
function mcTermChipsHtml(){
  if(!mcTwoTerms())return '';
  var v=mcTermView();
  return '<div class="mc-viewtog mc-terms" role="group" aria-label="Term">'
    +'<button type="button" aria-pressed="'+(v==='now')+'" class="'+(v==='now'?'on':'')+'" onclick="mcSetTermView(\\'now\\')">'+escAcc(mcNowLabel())+'</button>'
    +'<button type="button" aria-pressed="'+(v==='term')+'" class="'+(v==='term'?'on':'')+'" onclick="mcSetTermView(\\'term\\')">'+escAcc(mcTermLabel())+'</button></div>';
}
/* Friends in one of your now-term classes, for the faces on its block. */
function mcNowPeopleFor(code){
  var out=[];
  try{ (typeof FRIENDS!=='undefined'?FRIENDS:[]).forEach(function(o){
    var n=frNow(o); if(!n||(n.classes||[]).indexOf(code)<0)return;
    out.push({name:o.name,ini:o.ini||(typeof hmIni==='function'?hmIni(o.name):'?'),
              color:o.color||(typeof hmFriendColor==='function'?hmFriendColor(o):'#5E7A8A'),rel:'unknown'});
  }); }catch(e){}
  return out;
}
function mcRenderNow(out){
  try{ schedWideSync(); }catch(e){}
  var N=NOW_MINE, codes=N.classes.slice(), chips=mcTermChipsHtml(), lab=escAcc(mcNowLabel()), next=escAcc(mcTermLabel());
  if(!codes.length){
    out.innerHTML=chips+'<div class="wl-empty"><h3>'+(N.loaded?('No '+lab+' classes on your account'):('Loading your '+lab+' classes…'))+'</h3>'
      +(N.loaded?'<p>'+lab+' is the term you’re in now, and it’s read-only here. '+next+' is where you add classes — switch to it above.</p>':'')+'</div>';
    return;
  }
  var conf=(typeof myClassConflicts==='function')?myClassConflicts(codes,N.meta):{bad:{}};
  out.innerHTML=chips
    +'<p class="mc-now-note">What you’re in now. Read-only here — '+next+' is where you add classes.</p>'
    +'<div class="mc-cal mc-cal-now" data-hz-who="your">'+renderMyCalendar(codes,conf,N.meta,{peopleFor:mcNowPeopleFor})+'</div>';
}
function renderMyClasses(){
  var out=document.getElementById('watchMineOut');if(!out)return;
  if(mcTwoTerms()&&mcTermView()==='now'){ mcRenderNow(out); return; }
  renderMyClassesTerm();
  if(mcTwoTerms()){
    try{ var o2=document.getElementById('watchMineOut'); if(o2&&!o2.querySelector(':scope > .mc-terms'))o2.insertAdjacentHTML('afterbegin',mcTermChipsHtml()); }catch(e){}
  }
}
function renderMyClassesTerm(){
  var out=document.getElementById('watchMineOut');if(!out)return;""")
one("""window.hmOpenCal=function(){
  show('sched');""", """window.hmOpenCal=function(){
  /* Home's "My schedule" is the week you are in, so its Open goes to the same week. */
  try{ if(mcTwoTerms())localStorage.setItem(MC_TERMVIEW_KEY,'now'); }catch(e){}
  show('sched');""")

# ================================================================ a friend's page: Fall 2026 · Spring 2027
one("""  profileFriendId=id;profileTab=tab||'overlap';""", """  profileFriendId=id;profileTab=tab||'overlap';
  frpTermV=null;                       /* each friend opens on their own default — website-spring-wall (2026-10-14) */""")
one("""function renderFriendProfile(){
  const f=findFriend(profileFriendId);if(!f)return;""", """/* A FRIEND'S PAGE, TWO TERMS — website-spring-wall (2026-10-14). Their classes now (what Home shows) or this term's.
   Opens on now, unless they have nothing now and something in TERM. */
var frpTermV=null;
function frpTermOf(f0){
  if(!mcTwoTerms())return 'term';
  if(frpTermV==='now'||frpTermV==='term')return frpTermV;
  var n=frNow(f0); return (!(n.classes||[]).length&&(f0.classes||[]).length)?'term':'now';
}
window.setFrpTerm=function(v){ frpTermV=(v==='now')?'now':'term'; try{ renderFriendProfile(); }catch(e){} };
function frpTermChipsHtml(v){
  return '<div class="frp-view frp-terms"><div class="mc-viewtog" role="group" aria-label="Term">'
    +'<button type="button" aria-pressed="'+(v==='now')+'" class="'+(v==='now'?'on':'')+'" onclick="setFrpTerm(\\'now\\')">'+escAcc(mcNowLabel())+'</button>'
    +'<button type="button" aria-pressed="'+(v==='term')+'" class="'+(v==='term'?'on':'')+'" onclick="setFrpTerm(\\'term\\')">'+escAcc(mcTermLabel())+'</button></div></div>';
}
function nowCrnsFor(code){
  var m=NOW_MINE.meta[code], out=[];
  if(m){ if(m.crn)out.push(String(m.crn)); (Array.isArray(m.secs)?m.secs:[]).forEach(function(x){ if(x&&x.crn&&out.indexOf(String(x.crn))<0)out.push(String(x.crn)); }); }
  return out;
}
function renderFriendProfile(){
  const f0=findFriend(profileFriendId);if(!f0)return;
  const _tv=frpTermOf(f0), _fnow=mcTwoTerms()&&_tv==='now';
  const f=_fnow?frNow(f0):f0;""")
one("""  const mine=(typeof myClasses!=='undefined'?myClasses:[]);
  const shared=(f.classes||[]).filter(c=>mine.indexOf(c)>=0);""", """  const mine=_fnow?nowMine().classes:(typeof myClasses!=='undefined'?myClasses:[]);
  const shared=(f.classes||[]).filter(c=>mine.indexOf(c)>=0);""")
one("""      if(typeof isMyClass==='function'&&isMyClass(code)){
        var meNm=""", """      if(_fnow?isNowMine(code):(typeof isMyClass==='function'&&isMyClass(code))){
        var meNm=""")
one("""        var mine=(typeof myCrnsFor==='function')?myCrnsFor(code):[];""",
    """        var mine=_fnow?nowCrnsFor(code):((typeof myCrnsFor==='function')?myCrnsFor(code):[]);""")
one("""        if(!o||o.id===f.id)return;
        if((o.classes||[]).indexOf(code)<0)return;""", """        if(!o||o.id===f.id)return;
        if(_fnow)o=frNow(o);
        if((o.classes||[]).indexOf(code)<0)return;""")
one("""      var secs=(typeof clsSections==='function')?clsSections(c):[];
      if(!secs.length)return true;                  // nothing listed anywhere -> Time TBA""", """      var secs=(typeof clsSections==='function')?clsSections(c,_fnow?NOW_SEATS:null):[];
      if(!secs.length)return true;                  // nothing listed anywhere -> Time TBA""")
one("""      ${together?'':`<button class="fh-review" onclick="event.stopPropagation();addClassFromFriend('${jsAttr(c)}')">Add to mine</button>`}""",
    """      ${(together||_fnow)?'':`<button class="fh-review" onclick="event.stopPropagation();addClassFromFriend('${jsAttr(c)}')">Add to mine</button>`}""")
one("""    <div class="frp-body">${profileTab==='plans'&&window.TCPlans""", """    ${(mcTwoTerms()&&profileTab!=='took'&&profileTab!=='friends'&&profileTab!=='plans')?frpTermChipsHtml(_tv):''}
    <div class="frp-body">${profileTab==='plans'&&window.TCPlans""")

# ================================================================ styles
one("""</style>
</body>
</html>""", """</style>
<style id="website-spring-wall">
/* website-spring-wall (2026-10-14): the term chips on My Classes and a friend's page, the "now" note and tag */
#watchMineOut > .mc-terms{margin:0 0 12px}
.frp-terms{margin:4px 0 10px}
.mc-now-note{margin:0 0 12px;color:var(--muted);font-size:var(--t-body,12.5px)}
.hm-termtag{display:inline-block;margin-left:6px;padding:1px 8px;border-radius:999px;background:var(--panel-2);color:var(--text-2);font-size:var(--t-label,10.5px);font-weight:700;vertical-align:middle}
</style>
</body>
</html>""")

# ================================================================ the Degree Progress Report, two terms
one("""  out.forEach(function(r){ if(!r._iTok||!r._open)return; var k=r.year*10+(ORD[r.term]||0); if(out.some(function(o){ return o!==r&&!o._xfer&&!o._open&&!o._fail&&(o.year*10+(ORD[o.term]||0))>=k; }))incomplete(r); });""",
"""  out.forEach(function(r){ if(!r._iTok||!r._open)return; var k=r.year*10+(ORD[r.term]||0); if(out.some(function(o){ return o!==r&&!o._xfer&&!o._open&&!o._fail&&(o.year*10+(ORD[o.term]||0))>=k; }))incomplete(r); });
  /* TWO TERMS — website-spring-wall (2026-10-14), the phone's rule. "This term" used to mean the NEWEST term on the
     report, so a report printed after Spring registration filed every Fall class still in progress as finished. By
     name now: ungraded in the term you are in → your classes now (_now); ungraded in the term you are choosing →
     registered, your My Classes (_reg); ungraded and later still → shown, never saved. Finished is unchanged. */
  if(typeof mcTwoTerms==='function'&&mcTwoTerms()){
    var _nl=mcNowLabel(), _tl=mcTermLabel(), _tm=/^([A-Za-z]+)\\s+(\\d{4})$/.exec(_tl), _tk=_tm?(+_tm[2]*10+(ORD[_tm[1]]||0)):0;
    out.forEach(function(r){
      if(!r._open||r._xfer||r._fail)return;
      var lab=r.term+' '+r.year, k=r.year*10+(ORD[r.term]||0);
      if(lab===_nl){ r._now=true; r._reg=false; }
      else if(lab===_tl){ r._now=false; r._reg=true; }
      else if(_tk&&k>_tk){ r._now=false; r._reg=false; r._later=true; r.pick=false; }
      else r._now=false;          /* an older term still marked "newest" on a stale report is not the term you are in */
    });
  }""")
one("""    tiRows.sort(function(a,b){ return (a._now?1:0)-(b._now?1:0); });""",
    """    tiRows.sort(function(a,b){ var o=function(r){ return r._reg?2:(r._now?1:0); }; return o(a)-o(b); });""")
one("""    if(r._dpr&&r._now&&!prevNow){ grp='<div class="ti-grp"><b>This term</b><span>goes to My Classes — we know the courses, not the times</span></div>'; }
    if(r._dpr&&!r._now&&prevNow===null){ grp='<div class="ti-grp"><b>Already finished</b><span>goes to Past Classes</span></div>'; }
    prevNow=!!r._now;""", """    var _two=(typeof mcTwoTerms==='function'&&mcTwoTerms());
    if(r._dpr&&r._now&&!prevNow){ grp=_two
      ? '<div class="ti-grp"><b>'+esc(mcNowLabel())+' · in progress</b><span>your classes now — we know the courses, not the times</span></div>'
      : '<div class="ti-grp"><b>This term</b><span>goes to My Classes — we know the courses, not the times</span></div>'; }
    if(r._dpr&&r._reg&&prevNow!=='reg'){ grp='<div class="ti-grp"><b>'+esc(mcTermLabel())+' · registered</b><span>goes to My Classes for '+esc(mcTermLabel())+'</span></div>'; }
    if(r._dpr&&!r._now&&!r._reg&&prevNow===null){ grp='<div class="ti-grp"><b>Already finished</b><span>goes to Past Classes</span></div>'; }
    prevNow=r._reg?'reg':!!r._now;""")
one("""  var nNowPick=tiRows.filter(function(r){return r._dpr&&r._now&&r.pick;}).length;
  var nPastPick=tiRows.filter(function(r){return r._dpr&&!r._now&&r.pick&&!r.already;}).length;
  var dprBtn=nNowPick
    ? ('Add '+nPastPick+' to Past Classes and '+nNowPick+' to My Classes')
    : ('Add '+nPastPick+' to Past Classes');""", """  var nNowPick=tiRows.filter(function(r){return r._dpr&&r._now&&r.pick;}).length;
  var nRegPick=tiRows.filter(function(r){return r._dpr&&r._reg&&r.pick;}).length;
  var nPastPick=tiRows.filter(function(r){return r._dpr&&!r._now&&!r._reg&&!r._later&&r.pick&&!r.already;}).length;
  var dprBtn=nNowPick
    ? ('Add '+nPastPick+' to Past Classes and '+nNowPick+' to My Classes')
    : ('Add '+nPastPick+' to Past Classes');
  if(typeof mcTwoTerms==='function'&&mcTwoTerms()&&(nNowPick||nRegPick)){
    var _bp=['Add '+nPastPick+' to Past Classes'];
    if(nNowPick)_bp.push(nNowPick+' to '+mcNowLabel());
    if(nRegPick)_bp.push(nRegPick+' to '+mcTermLabel());
    dprBtn=_bp.length===2?_bp.join(' and '):(_bp.slice(0,-1).join(', ')+' and '+_bp[_bp.length-1]);
  }""")
one("""  var past=tiRows.filter(function(r){return r.pick&&!r._now&&!r.already;});
  var now =tiRows.filter(function(r){return r.pick&&r._now;});
  if(!past.length&&!now.length){ try{frToast('Nothing selected.');}catch(e){} return; }

  var addedNow=0;
  now.forEach(function(r){""", """  var past=tiRows.filter(function(r){return r.pick&&!r._now&&!r._reg&&!r._later&&!r.already;});
  var now =tiRows.filter(function(r){return r.pick&&(r._now||r._reg);});
  if(!past.length&&!now.length){ try{frToast('Nothing selected.');}catch(e){} return; }

  var addedNow=0, nowFailed=null;
  /* TWO TERMS — website-spring-wall (2026-10-14). In progress in the term you are in goes to your classes NOW, as the
     phone does: the one write this page makes to the now-term. Registered for TERM goes to My Classes as before. */
  if(typeof mcTwoTerms==='function'&&mcTwoTerms()){
    var _nowRows=now.filter(function(r){ return r._now; });
    now=now.filter(function(r){ return !r._now; });
    if(_nowRows.length&&typeof sb!=='undefined'&&sb&&typeof sbUser!=='undefined'&&sbUser){
      var _nt=mcNowTerm(), _add=[];
      _nowRows.forEach(function(r){ var c=r.cur||r.code; if(c&&NOW_MINE.classes.indexOf(c)<0&&_add.indexOf(c)<0)_add.push(c); });
      if(_add.length){
        try{
          var _w=await sb.from('saved_classes').upsert(_add.map(function(c){ return {user_id:sbUser.id,term:_nt,code:c}; }));
          if(_w.error)throw _w.error;
          _add.forEach(function(c){ NOW_MINE.classes.push(c); }); addedNow+=_add.length;
          try{ localStorage.setItem(nowMineKey(),JSON.stringify(NOW_MINE)); }catch(e){} try{ nowAfterLoad(); }catch(e){}
        }catch(e){ nowFailed=(e&&e.message)||'save failed'; }
      }
    }else if(_nowRows.length){ nowFailed='not-signed-in'; }
  }
  now.forEach(function(r){""")
one("""    var nNow=tiRows.filter(function(r){return r._now;}).length;
    note='Read straight from your Degree Progress Report'+(nNow?(' — '+nNow+' of these are in progress, so they go to My Classes instead'):'')+'.';""",
"""    var nNow=tiRows.filter(function(r){return r._now;}).length;
    note='Read straight from your Degree Progress Report'+(nNow?(' — '+nNow+' of these are in progress, so they go to My Classes instead'):'')+'.';
    if(typeof mcTwoTerms==='function'&&mcTwoTerms()){
      var nReg=tiRows.filter(function(r){return r._reg;}).length, nLater=tiRows.filter(function(r){return r._later;}).length;
      var _np=[]; if(nNow)_np.push(nNow+' in progress this '+mcNowLabel().split(' ')[0]); if(nReg)_np.push(nReg+' registered for '+mcTermLabel());
      note='Read straight from your Degree Progress Report'+(_np.length?(' — '+_np.join(', ')+', so they go to your classes instead of Past Classes'):'')
        +(nLater?(' '+nLater+' in a later term '+(nLater===1?'is':'are')+' shown but not saved.'):'')+'.';
    }""")

# ================================================================ the Schedule header names the term on screen
one("""      if(t==='plan'){ try{ if(typeof window.plPlanningLabel==='function')lbl='planning '+window.plPlanningLabel(); }catch(e){} }
      sp.textContent=lbl;""", """      if(t==='plan'){ try{ if(typeof window.plPlanningLabel==='function')lbl='planning '+window.plPlanningLabel(); }catch(e){} }
      /* Two terms: the header says which one is on screen — Fall when My Classes shows Fall, else the term you're
         choosing in (website-spring-wall, 2026-10-14). It read the calendar's guess, so "Fall 2026" over Spring. */
      else if(typeof mcTwoTerms==='function'&&mcTwoTerms()){ lbl=(t==='mine'&&typeof mcTermView==='function'&&mcTermView()==='now')?mcNowLabel():mcTermLabel(); }
      sp.textContent=lbl;""")
one("""  try{ localStorage.setItem(MC_TERMVIEW_KEY,v==='now'?'now':'term'); }catch(e){}
  try{ renderMyClasses(); }catch(e){}""", """  try{ localStorage.setItem(MC_TERMVIEW_KEY,v==='now'?'now':'term'); }catch(e){}
  try{ renderMyClasses(); }catch(e){}
  try{ schedLabelSync(); }catch(e){}""")

# ================================================================ sharing is the list you add to (Spring) — say so
one("""  if(!(myClasses&&myClasses.length)){ if(typeof frToast==='function')frToast('Add a class to My Classes first, then share your schedule.'); return; }""",
    """  if(!(myClasses&&myClasses.length)){ if(typeof frToast==='function')frToast(mcTwoTerms()?('Add your '+mcTermLabel()+' classes to My Classes first, then share them.'):'Add a class to My Classes first, then share your schedule.'); return; }""")

# ================================================================ sign-out forgets the now-term list; the cache keeps a friend's now-term
one("""async function authSignOut(){ try{ if(sb&&sb.auth)await sb.auth.signOut(); }catch(e){} sbUser=null;""",
    """async function authSignOut(){ try{ if(sb&&sb.auth)await sb.auth.signOut(); }catch(e){} sbUser=null; try{ NOW_MINE={classes:[],meta:{},loaded:false}; NOW_SEATS={}; _nowSeatAsked={}; }catch(e){}""")

one("""secs:f.secs||[],history:f.history||[],avatar_url:f.avatar_url||''};});""",
    """secs:f.secs||[],history:f.history||[],avatar_url:f.avatar_url||'',now:f.now||null};});""")
# ================================================================ review fixes (second-model review, 2026-10-13)
# "next together" is about the week you are in
one("""    if(typeof myClassMeta==='undefined')return null;
    var theirs={}; ((f.crns||f.sections)||[]).forEach(function(x){theirs[String(x)]=1;});""",
    """    if(typeof myClassMeta==='undefined')return null;
    f=frNow(f); var _nm=nowMine();      /* "together tomorrow" is the week you are in — website-spring-wall (2026-10-14) */
    var theirs={}; ((f.crns||f.sections)||[]).forEach(function(x){theirs[String(x)]=1;});""")
one("""    (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(code){
      var m=myClassMeta[code]; var secs=(m&&Array.isArray(m.secs))?m.secs:[];
      secs.forEach(function(sec){
        var crn=sec&&(sec.class_nbr||sec.crn);""", """    _nm.classes.forEach(function(code){
      var m=_nm.meta[code]; var secs=(m&&Array.isArray(m.secs))?m.secs:[];
      secs.forEach(function(sec){
        var crn=sec&&(sec.class_nbr||sec.crn);""")
# the rest of the "taking" sites: Fall in progress and Spring registered both count
one("""    try{ (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(c){
      try{ _haveCode[(typeof canonCode==='function')?canonCode(c):c]=1; }catch(_e){} }); }catch(e){}""",
    """    try{ myTakingCodes().forEach(function(c){
      try{ _haveCode[(typeof canonCode==='function')?canonCode(c):c]=1; }catch(_e){} }); }catch(e){}""")
one("""  var now=(typeof myClasses!=='undefined'?myClasses:[]).length;
  var _lc=window.plLedgerCompute();""", """  var now=myTakingCodes().length;
  var _lc=window.plLedgerCompute();""")
one("""  var taking={}; try{ (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(c){taking[canonCode(c)]=1;}); }catch(e){}
  var cands=Object.keys(power)""", """  var taking={}; try{ myTakingCodes().forEach(function(c){taking[canonCode(c)]=1;}); }catch(e){}
  var cands=Object.keys(power)""")
one("""  var taking=(typeof myClasses!=='undefined')?myClasses.map(canonCode):[];
  var done=plan.filter(""", """  var taking=myTakingCodes().map(canonCode);
  var done=plan.filter(""")
one("""      var taking={}; try{ (myClasses||[]).forEach(function(c){taking[canon(c)]=1;}); }catch(e){}
      parts.push('<b>Prerequisites</b> '""", """      var taking={}; try{ myTakingCodes().forEach(function(c){taking[canon(c)]=1;}); }catch(e){}
      parts.push('<b>Prerequisites</b> '""")
# a friend's change line on Home is about Fall; the watchlist and the seat feed are Spring's — don't cross them
one("""      if(typeof isWatchedClass==='function'&&isWatchedClass(code))return ' &mdash; <b class="cl-you">on your watchlist</b>';""",
    """      if(!mcTwoTerms()&&typeof isWatchedClass==='function'&&isWatchedClass(code))return ' &mdash; <b class="cl-you">on your watchlist</b>';""")
one("""function hmDropSeatNote(code){
  try{""", """function hmDropSeatNote(code){
  try{
    if(mcTwoTerms())return '';      /* a Fall drop, and the seat feed is Spring's: nothing we can stand behind */""")
# a friend's now-term that could not be read is unknown (null), not "in nothing"
one("""        if(!_na.error&&Array.isArray(_na.data)){
          var _nb=await sb.from('my_sections')""", """        if(!_na.error&&Array.isArray(_na.data)){
          _nowOk=true;
          var _nb=await sb.from('my_sections')""")
one("""    now:mcTwoTerms()?Object.assign({classes:[],crns:[],secs:[],wl:{},classAdds:[]},nowMap[id]||{}):null}));""",
    """    now:(mcTwoTerms()&&_nowOk)?Object.assign({classes:[],crns:[],secs:[],wl:{},classAdds:[]},nowMap[id]||{}):null}));""")
one("""  let classMap={},histMap={},addMap={},wlMap={},crnsMap={},secsMap={},nowMap={};""",
    """  let classMap={},histMap={},addMap={},wlMap={},crnsMap={},secsMap={},nowMap={},_nowOk=false;""")
# a session that ends forgets your now-term list too
one("""      if(!uid){lastAuthUid=null;try{FRIENDS=[];""", """      if(!uid){lastAuthUid=null;try{ NOW_MINE={classes:[],meta:{},loaded:false}; NOW_SEATS={}; _nowSeatAsked={}; }catch(_n){}try{FRIENDS=[];""")
# Home's idle repaint notices your now-term list landing
one("""             (typeof myClasses!=='undefined'?myClasses.length:0),
             (typeof myHistory!=='undefined'?myHistory.length:0),""", """             (typeof myClasses!=='undefined'?myClasses.length:0),
             (typeof NOW_MINE!=='undefined'?NOW_MINE.classes.length:0),
             (typeof myHistory!=='undefined'?myHistory.length:0),""")
one("""/* Every section you are in, with its parsed meeting — the same source the week on Home uses,
   so the card and the app can never disagree about what you are taking. */""", """/* Every section you are in, with its parsed meeting — from My Classes, the list you share. With two terms that is the
   term you are choosing in (Spring), while Home's week is the term you are in (website-spring-wall, 2026-10-14). */""")
# Home's "Open" shows Fall this time, without pinning My Classes to Fall
one("""  try{ if(mcTwoTerms())localStorage.setItem(MC_TERMVIEW_KEY,'now'); }catch(e){}
  show('sched');""", """  try{ if(mcTwoTerms())window._mcTermOnce='now'; }catch(e){}
  show('sched');""")
one("""  var v=null; try{ v=localStorage.getItem(MC_TERMVIEW_KEY); }catch(e){}
  if(v==='now'||v==='term')return v;""", """  if(window._mcTermOnce==='now'||window._mcTermOnce==='term')return window._mcTermOnce;
  var v=null; try{ v=localStorage.getItem(MC_TERMVIEW_KEY); }catch(e){}
  if(v==='now'||v==='term')return v;""")
one("""window.mcSetTermView=function(v){
  try{ localStorage.setItem(MC_TERMVIEW_KEY,v==='now'?'now':'term'); }catch(e){}""", """window.mcSetTermView=function(v){
  window._mcTermOnce=null;
  try{ localStorage.setItem(MC_TERMVIEW_KEY,v==='now'?'now':'term'); }catch(e){}""")
# the build stamp (sw.js moves with it)
one("""window.PROFESSIFY_BUILD='2026-10-13 07:45';""", """window.PROFESSIFY_BUILD='2026-10-13 22:00';""")

one("""    else if(bits.length)frToast('Added '+bits.join(' and ')+' \\u2713'""",
    """    else if(nowFailed)frToast('Couldn\\u2019t save your '+mcNowLabel()+' classes \\u2014 '+(nowFailed==='not-signed-in'?'log in, then upload the report again.':'try the report again.'));
    else if(bits.length)frToast('Added '+bits.join(' and ')+' \\u2713'""")

f.write_text(s)
print('patched', f)
sw = root / 'sw.js'
t = sw.read_text()
assert t.count("const BUILD = '2026-10-13 07:45';") == 1
sw.write_text(t.replace("const BUILD = '2026-10-13 07:45';", "const BUILD = '2026-10-13 22:00';"))
print('patched', sw)
