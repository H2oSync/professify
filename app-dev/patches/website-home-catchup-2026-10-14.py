#!/usr/bin/env python3
"""Home at the phone's level, on the website (Tate, 2026-10-14: catch termchamp.com up to the phone).

The phone's Home (spring-wall 2026-10-08 HOME part, spring-card-a, feed-class-recs 2026-10-04, stories-freeness
2026-10-11), in index.html, with the website's data names. Everything below is two-term only (mcTwoTerms()); on the
single-term site #hmFeed is byte-for-byte what it was (the stories order is the one change that applies to both).

1. EACH FRIEND'S CARD SHOWS THE NEWEST REAL THING. Their Spring classes (f.classes / f.secs, the term you choose in),
   else their first shared Spring plan (A, B, C; plan colour; only sections the Spring feed has), else their week now
   (frNow(f)). A tag says which: "Spring 2027 classes", "Plan A · Spring 2027", "Now · Fall 2026"; the count line
   follows: "Planning 4 classes · Spring 2027" / "Taking 5 classes · Fall 2026". hmHomeView(f) builds the view
   (a copy of the friend with classes / secs of that thing, _hm = 'next' | 'A' | 'B' | 'C' | 'now'); hmRenderFeed,
   hmFriendSchedCard and the "N with you" count read it. A view keeps its OWN seen-signatures (hmFeedSig of id~view),
   so "added / dropped" never compares a Fall week with a Spring one. Your side of "N with you" and of the shared
   marks on the week is your Spring list for Spring/plan views, your Fall week for Now.
2. NEW-PLAN LIFT. A friend whose Spring classes or shared plan changed since you last opened Home goes first, with
   "New plan" / "Spring classes added", once. Worked out once per page load when friends AND their plans have loaded
   and Home is on screen; remembered in HM_SEEN (the feed's per-viewer localStorage map) under '@home|<you>|<friend>'
   = {t,n,d,g: signature}. A friend you have never seen, or one whose signature is "now", is not lifted.
3. SWIPE ROW "Classes your friends are planning", after the 3rd card (or the last, with fewer): classes in friends'
   Spring lists and shared plans, not on your Spring list, not on your record (class_history); code, name, up to three
   faces + "N friends", "★ 4.6 · Lee" for the professor most of those friends have (a tie, no majority, or no rating, shows no
   chip); the card opens the class page. With nobody planning anything it falls back to "taking" (their classes now
   that the Spring feed offers). At most 8, most friends first. Not drawn until your record has loaded.
4. STORIES, THE PHONE'S FREENESS ORDER (stories-freeness 2026-10-11, the newest word; it supersedes the 10-04
   "free now, longest first" order): no classes today, then done for the day, then not in class with a class later
   (the furthest-off class first), then in class (out soonest first; a class straight after another is the same
   stretch); friends whose schedule isn't set up (no class with a set time, no window of busy time) last, grey ring.
   Rings: green = free (no class today, done, or between classes), orange = a class within 30 minutes, blue = in class.
   Reads the Fall view (gpMemberBusy uses frNow) and window.cmBlocks(friendId) when another patch defines it
   ([{days:['M','T',...], s, e}] in minutes). Kept from before: the 7am-11pm weekday window (outside it nobody is
   ranked or ringed, so there is no wall of green at 2am).

Plans module (TCPlans): friendPlansOf(id), friendPlansReady(), and Home repaints when friends' plans land.
loadMyHistory sets window._myHistOk on success (the row waits for your record).

Usage: python3 website-home-catchup-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-home-catchup (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ 1. TCPlans: friends' plans out, and a hook when they land
one("""  function friendById(id) {""", """  /* website-home-catchup (2026-10-14): a friend's shared plans for this term, slot order — Home shows the first one */
  function friendPlansOf(id) { return (friendPlansFor[id] || []).slice().sort(function (a, b) { return a.slot < b.slot ? -1 : a.slot > b.slot ? 1 : 0; }); }
  function friendById(id) {""")
one("""      refresh();
      return friendPlans;""", """      refresh();
      try { if (typeof window.hmFriendPlansLanded === 'function') window.hmFriendPlansLanded(); } catch (_) {}   // website-home-catchup (2026-10-14)
      return friendPlans;""")
one("loadFriendPlans: loadFriendPlans, askInterest", "loadFriendPlans: loadFriendPlans, friendPlansOf: friendPlansOf, friendPlansReady: function () { return friendPlans !== null; }, askInterest")

# ================================================================ 2. your record has loaded
one("""  myHistory=(data||[]).sort(""", """  window._myHistOk=true;   /* website-home-catchup (2026-10-14): the "friends are planning" row waits for this */
  myHistory=(data||[]).sort(""")

# ================================================================ 2b. fresh friends (the cached list paints first)
one("""  saveFriendsCache();   // persist the fresh list for an instant next load
}""", """  saveFriendsCache();   // persist the fresh list for an instant next load
  /* website-home-catchup (2026-10-14): the cached friends paint first and can be a visit old. The lift compares what you
     saw with what they have NOW, so it waits for this — and Home repaints once, the first time it lands. */
  try{ var _fu=(typeof sbUser!=='undefined'&&sbUser)?sbUser.id:null; if(_fu&&window._friendsFresh!==_fu){ window._friendsFresh=_fu; if(typeof window.hmFriendPlansLanded==='function')window.hmFriendPlansLanded(); } }catch(e){}
}""")

# ================================================================ 3. the helpers, in the feed's IIFE (beside HM_SEEN)
HELPERS = r'''function hmSeen(sig){ return !!HM_SEEN[sig]; }
/* ================================================================================================
   HOME AT THE PHONE'S LEVEL — website-home-catchup (2026-10-14)
   ================================================================================================
   See app-dev/patches/website-home-catchup-2026-10-14.py. Two terms only (mcTwoTerms()); single-term the
   views below are frNow(f) and every string this block adds is empty. */
function hmSigId(f){ return (f&&f._sigId)||(f&&f.id); }
function hmCodeN(c){ return String(c||'').trim().toUpperCase().replace(/\s+/g,' '); }
/* the first shared Spring plan that has at least one section the Spring feed offers, as a friend-shaped view */
function hmFirstPlan(fid){
  try{
    if(!(window.TCPlans&&TCPlans.friendPlansOf&&TCPlans.info))return null;
    var rows=TCPlans.friendPlansOf(fid);
    for(var i=0;i<rows.length;i++){
      var seen={}, classes=[], crns=[], secs=[];
      (rows[i].sections||[]).forEach(function(x){
        var code=hmCodeN(x&&x.code), crn=String((x&&(x.class_nbr||x.crn))||'').trim();
        if(!code||!/^\d{3,6}$/.test(crn)||seen[crn])return;
        var inf=TCPlans.info(code,crn); if(!inf||inf.missing||!inf.row)return;
        seen[crn]=1; if(classes.indexOf(code)<0)classes.push(code); crns.push(crn);
        secs.push({code:code,crn:crn,section:inf.row.section||'',instructor:inf.row.instructor||'',days:inf.row.days||''});
      });
      if(secs.length)return {slot:rows[i].slot,classes:classes,crns:crns,secs:secs};
    }
  }catch(e){}
  return null;
}
/* THE NEWEST REAL THING a friend has: Spring classes, else their first shared Spring plan, else their week now. */
function hmHomeView(f){
  if(!f)return f;
  if(f._hm)return f;
  if(!mcTwoTerms())return frNow(f);
  if(f._now)return f;
  if((f.classes||[]).length)return Object.assign({},f,{_hm:'next',_sigId:f.id+'~next'});
  var pl=hmFirstPlan(f.id);
  if(pl)return Object.assign({},f,{_hm:pl.slot,_sigId:f.id+'~'+pl.slot,classes:pl.classes,crns:pl.crns,secs:pl.secs,wl:{},classAdds:[]});
  return Object.assign({},frNow(f),{_hm:'now'});
}
function hmViewIsNow(f){ return !f||!f._hm||f._hm==='now'; }
/* how many of THEIR classes are YOURS: Now compares with your Fall week, a Spring class or plan with your Spring list */
function hmOverlapFor(f){
  if(hmViewIsNow(f))return hmOverlap(f&&f.classes);
  var n=0; try{ var m={}; (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(c){ m[c]=1; });
    (f.classes||[]).forEach(function(c){ if(m[c])n++; }); }catch(e){}
  return n;
}
function hmCtxLine(f,ov){
  var n=f.classes.length, ovh=ov?' · <b style="color:var(--accent)">'+ov+' with you</b>':'';
  if(!f._hm)return 'Taking '+n+' class'+(n===1?'':'es')+' this term'+ovh;
  var now=f._hm==='now';
  return (now?'Taking ':'Planning ')+n+' class'+(n===1?'':'es')+' · '+esc(now?mcNowLabel():mcTermLabel())+ovh;
}
function hmViewTag(f,lift){
  if(!f||!f._hm)return '';
  var k=f._hm, txt=k==='next'?(mcTermLabel()+' classes'):(k==='now'?('Now · '+mcNowLabel()):('Plan '+k+' · '+mcTermLabel()));
  return '<span class="hm-fviews"><span class="hm-fview hm-fview-'+(k==='next'||k==='now'?k:'plan hm-plan-'+k)+'">'+esc(txt)+'</span>'
    +(lift?('<span class="hm-fnew">'+(lift==='next'?esc(String(mcTermLabel()).split(' ')[0])+' classes added':'New plan')+'</span>'):'')+'</span>';
}
/* ---- the lift: who changed since you last opened Home ---- */
function hmHomeSig(v){
  if(!v||v._hm==='now'||!v._hm)return 'now';
  return v._hm+':'+(v.classes||[]).slice().sort().join(',')+'|'+(v.crns||[]).slice().sort().join(',')
    +'|'+(v.secs||[]).map(function(x){ return (x&&x.crn)||''; }).filter(Boolean).sort().join(',');
}
var HM_HNEW=null;
function hmHomeNew(){
  try{
    if(!mcTwoTerms()||typeof sbUser==='undefined'||!sbUser)return {};
    if(typeof friendsLoaded==='undefined'||!friendsLoaded||window._friendsFresh!==sbUser.id)return {};
    if(!(window.TCPlans&&TCPlans.friendPlansReady&&TCPlans.friendPlansReady()))return {};
    /* a plan's sections are read from the Spring feed: before it lands a plan friend looks like "now" and would be remembered so */
    if(typeof SEAT_SECTIONS==='undefined'||!SEAT_SECTIONS||!Object.keys(SEAT_SECTIONS).length)return {};
    if(HM_HNEW&&HM_HNEW.uid===sbUser.id&&HM_HNEW.term===mcTerm())return HM_HNEW.ids;
    if(!hmFeedVisible())return {};            /* a render nobody looked at must not spend the lift */
    var pre='@home|'+sbUser.id+'|', ids={}, now=Date.now(), today=hmDayKey(now);
    (friendsList||[]).forEach(function(fr){
      if(!fr||!fr.id)return;
      var v=hmHomeView(fr), sig=hmHomeSig(v), key=pre+fr.id, prev=HM_SEEN[key];
      if(sig!=='now'&&prev&&typeof prev==='object'&&typeof prev.g==='string'&&prev.g!==sig)ids[fr.id]=(v._hm==='next')?'next':'plan';
      HM_SEEN[key]={t:now,n:1,d:today,g:sig};
    });
    hmSeenSave();
    HM_HNEW={uid:sbUser.id,term:mcTerm(),ids:ids};
    return ids;
  }catch(e){ return {}; }
}
function hmHomeLift(id){ var m=hmHomeNew(); return (m&&m[id])||''; }
/* friends' plans landed after Home first drew: draw it again so the plan cards and the row appear */
window.hmFriendPlansLanded=function(){ try{ if(mcTwoTerms()&&document.getElementById('hmFeed'))hmRenderFeed(); }catch(e){} };   /* single-term: no repaint, the feed is as it was */
/* ---- the swipe row ---- */
function hmHomeRecs(){
  try{
    if(!mcTwoTerms()||!window._myHistOk)return null;
    var fr=(typeof friendsList!=='undefined'&&friendsList)?friendsList:[];
    if(!fr.length)return null;
    var mine={}, took={};
    (typeof myClasses!=='undefined'?myClasses:[]).forEach(function(c){ mine[canonCode(c)||c]=1; });
    (typeof myHistory!=='undefined'?myHistory:[]).forEach(function(h){ if(h&&h.code){ var c=canonCode(h.code)||h.code; took[c]=1; } });
    var by={};
    function add(code,fr1,instr){
      var k=canonCode(code)||code; if(!k||mine[k]||took[k])return;
      var e=by[code]||(by[code]={code:code,who:[],ids:{},profs:{}});
      if(!e.ids[fr1.id]){ e.ids[fr1.id]=1; e.who.push(fr1); }
      var pid=instr&&typeof matchProfId==='function'?matchProfId(instr):null;
      if(pid)(e.profs[pid]=e.profs[pid]||{})[fr1.id]=1;
    }
    fr.forEach(function(x){
      (x.classes||[]).forEach(function(c){
        var any=false;
        (x.secs||[]).forEach(function(sr){ if(sr&&sr.code===c){ any=true; add(c,x,sr.instructor); } });
        if(!any)add(c,x,null);
      });
      if(window.TCPlans&&TCPlans.friendPlansOf)TCPlans.friendPlansOf(x.id).forEach(function(row){
        (row.sections||[]).forEach(function(sx){
          var code=hmCodeN(sx&&sx.code), crn=String((sx&&(sx.class_nbr||sx.crn))||'').trim();
          var inf=(code&&crn)?TCPlans.info(code,crn):null;
          if(inf&&!inf.missing&&inf.row)add(code,x,inf.row.instructor);
        });
      });
    });
    var planning=Object.keys(by).length>0;
    if(!planning){
      fr.forEach(function(x){
        (frNow(x).classes||[]).forEach(function(c){
          var S=(typeof SEAT_SECTIONS!=='undefined')?SEAT_SECTIONS:null;
          if(S&&S[c]&&S[c].length&&!isNowMine(c))add(c,x,null);   /* a class you are in now is not a suggestion */
        });
      });
    }
    var list=Object.keys(by).map(function(c){
      var e=by[c], ps=Object.keys(e.profs).map(function(p){ return [p,Object.keys(e.profs[p]).length]; }).sort(function(a,b){ return b[1]-a[1]; });
      /* the professor most of those friends have — a tie shows none rather than an arbitrary one */
      var lead=(ps.length&&(ps.length===1||ps[0][1]>ps[1][1])&&ps[0][1]*2>e.who.length)?ps[0][0]:null;
      return {code:e.code,who:e.who,prof:lead};
    }).sort(function(a,b){ return b.who.length-a.who.length||(a.code<b.code?-1:a.code>b.code?1:0); }).slice(0,8);
    return {planning:planning,list:list};
  }catch(e){ return null; }
}
function hmHomeRecsHtml(){
  var r=hmHomeRecs(); if(!r||!r.list.length)return '';
  var what=r.planning?'planning':'taking';
  return '<section class="hm-recs" aria-label="Suggested: classes your friends are '+what+'"><div class="hm-recs-h"><span>Classes your friends are '+what+'</span><span class="hm-recs-tag">Suggested</span></div>'
    +'<div class="hm-recs-row">'+r.list.map(function(x){
      var nm=''; try{ nm=(typeof fp_name==='function'&&fp_name(x.code))||((typeof classInfo==='function'?classInfo(x.code):null)||{}).name||''; }catch(e){}
      var chip='';
      try{
        var P=x.prof&&typeof PROFESSORS!=='undefined'?PROFESSORS[x.prof]:null;
        if(P&&P.rating!=null&&isFinite(Number(P.rating))){
          var last=String(P.name||'').trim().split(/\s+/).pop();
          chip='<span class="hm-rec-p"><span style="color:'+scoreColor(P.rating)+'">★ '+to5(P.rating).toFixed(1)+'</span>'+(last?' · '+esc(last):'')+'</span>';
        }
      }catch(e){}
      var faces=x.who.slice(0,3).map(function(fr){ return '<span class="sav" style="background:'+hmFriendColor(fr)+'">'+faceHtml(fr)+'</span>'; }).join('');
      return '<button type="button" class="hm-rec" data-code="'+esc(x.code)+'" onclick="openClassFromFeed(\''+escAcc(x.code)+'\')">'
        +'<span class="hm-rec-k">'+esc(x.code)+'</span>'+(nm?'<span class="hm-rec-n">'+esc(nm)+'</span>':'')
        +'<span class="hm-rec-w"><span class="hm-avstack">'+faces+'</span><span>'+x.who.length+' friend'+(x.who.length===1?'':'s')+'</span></span>'+chip+'</button>';
    }).join('')+'</div></section>';
}
/* ---- stories: the phone's storyRank (stories-freeness 2026-10-11) ---- */
var HM_BLKDAY={M:0,T:1,W:2,R:3,F:4,Mo:0,Tu:1,We:2,Th:3,Fr:4};
/* {rank:[group,key], state:'now'|'next'|'in'|'none', label} for one friend today, or null when it can't be told */
function hmStoryState(f,W){
  try{
    if(!W||!f||!f.id||typeof gpMemberBusy!=='function')return null;
    var r=gpMemberBusy({id:f.id}), busy=(r&&!r.noData)?(r.busy||[]):[], cm=[];
    try{ if(typeof window.cmBlocks==='function')(window.cmBlocks(f.id)||[]).forEach(function(b){
      if(!b||b.s==null||b.e==null)return;
      (b.days||[]).forEach(function(d){ if(HM_BLKDAY[d]!=null)cm.push({di:HM_BLKDAY[d],s:b.s,e:b.e}); });
    }); }catch(e){}
    /* no class with a set time (and nothing else that fills the week): we can't know their day, so never "free" */
    if(!busy.length&&!cm.length)return {rank:[4,0],state:'none',label:' — schedule not set up'};
    var today=busy.concat(cm).filter(function(b){ return b.di===W.di; }).sort(function(a,b){ return a.s-b.s; });
    var now=W.now, fm=(typeof fmtMin==='function')?fmtMin:String;
    if(!today.length)return {rank:[0,0],state:'now',label:' — no classes today'};
    var inc=null, nx=null, i;
    for(i=0;i<today.length;i++){ if(!inc&&today[i].s<=now&&now<today[i].e)inc=today[i]; if(!nx&&today[i].s>now)nx=today[i]; }
    if(!inc&&!nx)return {rank:[1,0],state:'now',label:' — done for the day'};
    if(!inc)return {rank:[2,-(nx.s-now)],state:(nx.s-now<=30)?'next':'now',label:(nx.s-now<=30)?(' — class at '+fm(nx.s)):(' — free till '+fm(nx.s))};
    var t=inc.e; today.forEach(function(x){ if(x.e>t&&x.s<=t+10)t=x.e; });   /* a class straight after another is the same stretch */
    return {rank:[3,t],state:'in',label:' — in class till '+fm(t)};
  }catch(e){ return null; }
}
function hmStoryCmp(a,b){
  var ra=a.fs?a.fs.rank:[4,0], rb=b.fs?b.fs.rank:[4,0];
  if(ra[0]!==rb[0])return ra[0]-rb[0];
  if(ra[1]!==rb[1])return ra[1]-rb[1];
  var na=String(a.f.name||''), nb=String(b.f.name||'');
  return na.localeCompare(nb)||(a.f.id<b.f.id?-1:a.f.id>b.f.id?1:0);
}
try{ window.hmHomeView=hmHomeView; window.hmHomeNew=hmHomeNew; window.hmHomeRecs=hmHomeRecs; window.hmStoryState=hmStoryState; window.hmHomeSig=hmHomeSig; }catch(e){}'''
one("function hmSeen(sig){ return !!HM_SEEN[sig]; }", HELPERS)

# ================================================================ 4. the card
one("""  f=frNow(f);                       /* Home shows where they are now — website-spring-wall (2026-10-14) */
  var ov=hmOverlap(f.classes);""", """  f=hmHomeView(f);                  /* Home shows the newest real thing — website-home-catchup (2026-10-14); single-term: frNow(f) = f */
  var ov=hmOverlapFor(f);
  var lift=f._hm?hmHomeLift(f.id):'';""")
one("""  return '<article class="hm-card">'
    +'<button type="button" class="hm-fhead hm-fhead-btn\"""", """  return '<article class="hm-card'+(f._hm?(' hm-vw-'+(f._hm==='next'||f._hm==='now'?f._hm:'plan hm-plan-'+f._hm)):'')+'"'+(f._hm?(' data-hmview="'+f._hm+'" data-fid="'+esc(f.id)+'"'):'')+'>'
    +'<button type="button" class="hm-fhead hm-fhead-btn\"""")
one("""    +'<span class="ctx">Taking '+f.classes.length+' class'+(f.classes.length===1?'':'es')+' this term'+(ov?' · <b style="color:var(--accent)">'+ov+' with you</b>':'')+'</span>'""",
    """    +'<span class="ctx">'+hmCtxLine(f,ov)+'</span>'+hmViewTag(f,lift)""")
one("""    +hmNewMark(f.id,f.classes,f.secs)+'</button>'""", """    +(lift?'':hmNewMark(hmSigId(f),f.classes,f.secs))+'</button>'""")
# Anchor kept short so it lands whether or not website-commitments (which adds cm:f.id after win:) went first.
one("""hmMiniWeekHtml(confirmed,{excludeId:f.id,anytime:anyt,mark:mark,win:window._hmFeedWin||null""",
    """hmMiniWeekHtml(confirmed,{excludeId:f.id,anytime:anyt,mark:mark,spring:!hmViewIsNow(f),win:window._hmFeedWin||null""")
one("""      var mine=isNowMine(m.code);""", """      var mine=opts.spring?(typeof myClasses!=='undefined'&&myClasses.indexOf(m.code)>=0):isNowMine(m.code);   /* website-home-catchup: a Spring card is read against your Spring list */""")
one("""      if(isNowMine(code))return ' &mdash; <b class="cl-you">you""", """      if(hmViewIsNow(f)?isNowMine(code):(typeof myClasses!=='undefined'&&myClasses.indexOf(code)>=0))return ' &mdash; <b class="cl-you">you""")
one("""    var mine={}, n=0, _nmeta=nowMine().meta||{};""", """    var mine={}, n=0, _nmeta=nowMine().meta||{};
    if(f&&f._hm&&f._hm!=='now')_nmeta=(typeof myClassMeta!=='undefined'?myClassMeta:{})||{};   /* website-home-catchup: a Spring card shares sections with your Spring list */""")
one("""    var last=hmLastSeenFor(f&&f.id);""", """    var last=hmLastSeenFor(hmSigId(f));""")
one("""    var nowSig=hmFeedSig(f.id,f.classes,f.secs);""", """    var nowSig=hmFeedSig(hmSigId(f),f.classes,f.secs);""")

# ================================================================ 5. the feed
one("""      (friendsList||[]).forEach(function(f){
        f=frNow(f);
        if(!f||!f.classes||!f.classes.length)return;""", """      (friendsList||[]).forEach(function(f){
        f=hmHomeView(f);
        if(!f||!f.classes||!f.classes.length)return;""")
one("""    (friendsList||[]).forEach(function(f){
      f=frNow(f);
      if(f.classes&&f.classes.length&&!schedUsers[f.id]){
        items.push({score:hmOverlap(f.classes),secShared:hmSecShared(f),t:hmSchedAt(f),
                    uid:f.id,meets:avMeetsOf(f),
                    sig:hmFeedSig(f.id,f.classes,f.secs),html:hmFriendSchedCard(f)});""", """    (friendsList||[]).forEach(function(f){
      f=hmHomeView(f);
      if(f.classes&&f.classes.length&&!schedUsers[f.id]){
        items.push({score:hmOverlapFor(f),secShared:hmSecShared(f),t:hmSchedAt(f),
                    uid:f.id,meets:avMeetsOf(f),lift:f._hm?hmHomeLift(f.id):'',
                    sig:hmFeedSig(hmSigId(f),f.classes,f.secs),html:hmFriendSchedCard(f)});""")
one("""  items.sort(function(a,b){
    /* One tier now.""", """  items.sort(function(a,b){
    /* website-home-catchup (2026-10-14): a friend whose Spring classes or plan changed since you last opened Home goes first, once */
    if(!!a.lift!==!!b.lift)return a.lift?-1:1;
    /* One tier now.""")
one("""  var out=shown.map(function(i){return i.html;}).join('');""", """  var out=shown.map(function(i){return i.html;});
  /* "Classes your friends are planning", after the third card (website-home-catchup, 2026-10-14) — two terms only; '' otherwise */
  try{ var _rc=hmHomeRecsHtml(); if(_rc&&out.length)out.splice(Math.min(3,out.length),0,_rc); }catch(e){}
  out=out.join('');""")

# ================================================================ 6. stories
one("""  var ranked=fr.map(function(f){ return {f:f, fs:W?hmFreeState(f,W):null}; });
  ranked.sort(function(a,b){
    var ra=a.fs?(a.fs.state==='now'?0:1):2, rb=b.fs?(b.fs.state==='now'?0:1):2;
    if(ra!==rb)return ra-rb;
    if(ra<2)return b.fs.mins-a.fs.mins;
    return 0;
  });""", """  /* website-home-catchup (2026-10-14): the phone's order (stories-freeness) — see hmStoryState. Outside the window: as it was. */
  var ranked=fr.map(function(f){ return {f:f, fs:W?hmStoryState(f,W):null}; });
  if(W)ranked.sort(hmStoryCmp);""")
one("""    var fcls=fs?(' hm-free hm-'+fs.state):'';""", """    var fcls=fs?(fs.state==='none'?' hm-unset':' hm-free hm-'+fs.state):'';""")
one("""+esc((f.name||'')+hmFreeLabel(fs))+'">'""", """+esc((f.name||'')+(fs&&fs.label!=null?fs.label:hmFreeLabel(fs)))+'">'""")

# ================================================================ 7. look
CSS = r'''<!-- PLANS:END -->
<style id="hm-catchup-css">
/* website-home-catchup (2026-10-14): Home's view tag, the swipe row, the story rings. Plan colours are the phone's. */
.hm-fviews{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.hm-fview,.hm-fnew{display:inline-block;padding:3px 9px;border-radius:12px;font-size:12px;font-weight:700;line-height:1.35}
.hm-fview{background:var(--panel-2);color:var(--text-2)}
.hm-fview-next{background:var(--blue-soft);color:var(--blue-ink)}
.hm-fview-now{background:var(--panel-2);color:var(--text-2)}
.hm-fnew{background:#FCE7F1;color:#9D174D}
.hm-plan-A{--pc:#0F766E;--pc-soft:#DDF5F1;--pc-soft2:#BDEBE2;--pc-ink:#115E59}
.hm-plan-B{--pc:#C2410C;--pc-soft:#FFEDD5;--pc-soft2:#FED7AA;--pc-ink:#9A3412}
.hm-plan-C{--pc:#BE185D;--pc-soft:#FCE7F1;--pc-soft2:#F9CFE2;--pc-ink:#9D174D}
.hm-fview.hm-plan-A,.hm-fview.hm-plan-B,.hm-fview.hm-plan-C{background:var(--pc-soft);color:var(--pc-ink)}
.hm-card.hm-vw-plan{box-shadow:inset 0 3px 0 var(--pc)}
.hm-card.hm-vw-plan .cal-block:not(.wl){background:var(--pc-soft2);color:var(--pc-ink)}
.hm-recs{min-width:0;margin:0 0 14px}
.hm-recs-h{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:15px;font-weight:700;color:var(--text);padding:2px 4px 9px}
.hm-recs-tag{flex:none;font-size:10.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--blue-ink);background:var(--blue-soft);padding:3px 8px;border-radius:99px}
.hm-recs-row{display:flex;gap:10px;overflow-x:auto;padding:0 2px 4px;scroll-snap-type:x proximity;scrollbar-width:none;overscroll-behavior-x:contain}
.hm-recs-row::-webkit-scrollbar{display:none}
.hm-rec{flex:0 0 190px;min-height:44px;display:flex;flex-direction:column;align-items:flex-start;gap:6px;text-align:left;padding:12px;border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);color:var(--text);font-family:inherit;cursor:pointer;scroll-snap-align:start;box-shadow:var(--card-sh)}
.hm-rec:hover{border-color:rgba(var(--accent-rgb),.5)}
.hm-rec-k{font-size:13px;font-weight:800;color:var(--course)}
.hm-rec-n{font-size:14px;font-weight:700;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.hm-rec-w{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-2);margin-top:auto}
.hm-rec-w .hm-avstack{display:inline-flex}
.hm-rec-p{font-size:12px;font-weight:700;color:var(--text-2)}
.hm-fitem.hm-free.hm-in .ring{border-color:var(--clsblk);border-width:2.5px}
.hm-fitem.hm-free.hm-next .ring{border-color:#F97316;border-width:2.5px}
#view-home .hm-fitem.hm-unset:not(.hm-fadd) .ring{border-color:#CBD5E1}   /* beats the neutral --line rule above, which is nearly invisible on white */
.hm-fitem.hm-unset .nm{color:var(--muted)}
:root[data-theme="dark"] .hm-fview-next{background:#172748;color:#A9C6FF}
:root[data-theme="dark"] .hm-fnew{background:#3A1529;color:#F9B4D6}
:root[data-theme="dark"] .hm-plan-A{--pc:#14A394;--pc-soft:#0E2D2B;--pc-soft2:#14403C;--pc-ink:#8FE3D8}
:root[data-theme="dark"] .hm-plan-B{--pc:#EA6A2A;--pc-soft:#35200F;--pc-soft2:#4A2B13;--pc-ink:#FDBA8C}
:root[data-theme="dark"] .hm-plan-C{--pc:#E0457E;--pc-soft:#3A1529;--pc-soft2:#521D39;--pc-ink:#F9B4D6}
:root[data-theme="dark"] .hm-recs-tag{background:#172748;color:#A9C6FF}
:root[data-theme="dark"] #view-home .hm-fitem.hm-unset:not(.hm-fadd) .ring{border-color:#3A4660}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]):not([data-theme="dark"]):not([data-theme="cream"]) .hm-fview-next{background:#172748;color:#A9C6FF}
  :root:not([data-theme="light"]):not([data-theme="dark"]):not([data-theme="cream"]) .hm-fnew{background:#3A1529;color:#F9B4D6}
}
</style>'''
one("<!-- PLANS:END -->", CSS)

f.write_text(s)
print('website-home-catchup: applied')
