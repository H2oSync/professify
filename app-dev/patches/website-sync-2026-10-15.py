#!/usr/bin/env python3
"""WEBSITE sync pass, 2026-10-15 (index.html, sw.js stamp). One account, the same data on the phone and the website.
Written against /tmp/claude-0/sec/sync-audit.md (W = index.html, P = the phone app). Edits only the website; the server
additions it can use are in sql/professify-sync-2026-10-15.sql (not live yet): every call to them treats
PGRST202 / 42883 / 42P01 / PGRST205 / "does not exist" as "not installed" and keeps today's behaviour.

TASK 1  Registration-day banner. The full-width banner ("Round 1 registration opens in 5 days. Your game plan ...") is gone
        from the top of every page (the finals-week banner is not touched). The same content is a compact card on Home's
        right rail directly under the greeting card: #hmRegCard (countdown, one sentence, the two buttons stacked, x to
        dismiss with the same professify_dismiss_reg_<date> key as the banner used, so a dismissal carries over).
        Schedule > Plans keeps its registration card. The regday module's focus/refocus selectors follow the card.
TASK 2  Stories. The strip behaves like the phone's (storyOrder / storyRank / pins):
        * ordering: the phone's freeness rank at EVERY hour (it only ran inside 7am-11pm on a weekday before, "outside
          the window: as it was"); a weekend is "no classes today", exactly the phone's CLOCK.day with no sections;
        * pins: up to 3, first, in pin order; read through my_pinned_friends(), written through set_pinned_friends()
          (profiles.pinned_friends is not selectable, which is why web pins vanished on reload); same toasts as the
          phone ("Pinned X to the front", "Unpinned X", "3 pinned already - unpin A, B or C first");
        * pin from the website: a pin button on a story (hover/focus), right-click or a 0.5 s hold on a story, and the
          existing star on every feed card; a pinned story carries the phone's pin badge.
        When my_pinned_friends is not installed the old path (a direct column write, 2 pins, lost on reload) stays.
GAP 1   Major / standing / concentration follow the account: ensureProfile reads profiles.major/class_standing/
        concentration (concentration is SELECT-granted; if a database refuses it the read is retried without), the
        local profile is replaced by the account's when the account has them, and a change made on the website
        (Settings, onboarding) is written every time, with a pending flag so an unsent change is retried before the
        account overrides it. '5th year +' is in onboarding too, 'General / Open' is no concentration (null), and
        the phone's major-rename map is applied on read and write.
GAP 3   Sections the phone removed are no longer put back: a successful my_sections read REPLACES the term's local
        section list (queued adds survive), the backfill pushes only crns queued as adds (plus one adoption pass per
        account/term for classes imported before the queue existed), and watch_sections removals are honoured the same
        way. pushMySecToDb / pushWatchSecToDb queue the crn before the write and clear it only on a clean answer.
GAP 4   A tab that was hidden for more than 2 minutes reloads the account (frOnSignedIn) when it is shown again.
GAP 5   Chat: conversation_clears, message_hides, conversation_mutes and message_likes are read like the phone
        (P:3840-3857, 5318-5330); hidden messages, messages from before a cleared chat and messages from blocked
        senders are filtered (list previews, open thread, unread); a muted chat says Muted; likes show as a heart.
GAP 6   Push: seats / friends / quiet hours written by the website are mirrored into push_prefs.prefs under the phone's
        names (seats -> seat_open, friends -> free [the server kind; the phone has no matching toggle], quiet_from,
        quiet_to); the card reads prefs.seat_open === false as off; quiet hours are editable in the card.
GAP 7   The website's class and professor watch lists live in public.saved_items (kind 'class'/'prof', key = canonical
        code / review key "name|dept" lowercased). The local lists stay the cache; the first sync per account uploads
        what is only local; afterwards the account is the authority and offline changes are queued.
GAP 8   Favorite teachers (my_favorite_teachers / set_favorite_teacher) in the rating form; the Game Plan's device-only
        "appointment time" is replaced by the registration day (registration_days) through the existing regday sheet.
GAP 9   The review edit no longer sends `term` (reviews has no such column, so every edit failed).
GAP 10  normCode accepts suffix letters and '&' (the phone's canonCode); saved_classes codes read through it.
Build stamp: window.PROFESSIFY_BUILD, sw.js BUILD and the three hawk-* ?v= digits (Los Angeles clock unless given).

Usage: python3 website-sync-2026-10-15.py <repo> ["YYYY-MM-DD HH:MM"]
"""
import sys, os, re, pathlib, subprocess
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
sw = root / 'sw.js'
s = f.read_text()
w = sw.read_text()
if 'website-sync (2026-10-15)' in s:
    sys.exit('already patched')
stamp = sys.argv[2] if len(sys.argv) > 2 else subprocess.check_output(['date', '+%Y-%m-%d %H:%M'], env=dict(os.environ, TZ='America/Los_Angeles')).decode().strip()
assert re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d', stamp), stamp
digits = re.sub(r'\D', '', stamp)


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


def span(start, end, new):
    """replace from `start` up to (not including) `end`, both exact and unique"""
    global s
    assert s.count(start) == 1, (s.count(start), start[:140])
    i = s.index(start)
    j = s.index(end, i + len(start))
    assert s.count(end, i + len(start)) >= 1
    s = s[:i] + new + s[j:]


# ====================================================================================================== TASK 1
one("""  const regIn=(typeof regPacificGap==='function'&&c.REGISTRATION_OPENS)?regPacificGap(c.REGISTRATION_OPENS):daysUntil(c.REGISTRATION_OPENS);   /* regday-fixes (2026-10-14): Pacific, like the card */
  const qtrIn=daysUntil(c.QUARTER_END);
  let html='';
  if(regIn!=null&&regIn>=0&&regIn<=7){
    const key='reg_'+c.REGISTRATION_OPENS;
    if(!campusBannerDismissed(key)){
      const when=regIn===0?'today':regIn===1?'tomorrow':`in ${regIn} days`;
      html=`<div class="campus-banner"><span>📅</span><span><b>Round 1 registration opens ${when}.</b> Your game plan says what to register for first, with a backup for each class.</span><button class="btn primary" style="flex:none" onclick="if(window.TCPlans)TCPlans.fromBanner();else show('sched')">Your game plan</button>${(typeof regDayLabel==='function'&&regDayLabel())?'<button class="btn" style="flex:none" onclick="regDayOpen(&quot;banner&quot;)">'+regDayLabel()+'</button>':''}<button class="cb-x" title="Dismiss" onclick="dismissCampusBanner('${key}')">&times;</button></div>`;
    }
  }else if(qtrIn!=null&&qtrIn<=7&&qtrIn>=-7){""",
    """  /* website-sync (2026-10-15): the "Round 1 registration opens in N days" banner is not in this strip any more. It is a card
     on Home's right rail, under the greeting (hmRegCardHtml below). Only the finals-week banner is left here. */
  const qtrIn=daysUntil(c.QUARTER_END);
  let html='';
  if(qtrIn!=null&&qtrIn<=7&&qtrIn>=-7){""")

one("""function dismissCampusBanner(key){try{localStorage.setItem('professify_dismiss_'+key,'1');}catch(e){}var el=document.getElementById('campusBanner');if(el)el.innerHTML='';}""",
    """function dismissCampusBanner(key){try{localStorage.setItem('professify_dismiss_'+key,'1');}catch(e){}var el=document.getElementById('campusBanner');if(el)el.innerHTML='';}
/* website-sync (2026-10-15): the registration banner as a compact card on Home's right rail (Tate: "Card on Home's right side").
   Shown from 7 days before Round 1 opens until it opens, like the banner was; x dismisses it for good (the banner's own
   dismissal key, so a student who closed the banner does not see the card). The two buttons stack to fit the 300px rail. */
/* ONE registration card on Home: while this one shows, the rail's own "Set your registration day / Opens Oct 19" card is not drawn (its
   info is folded in here: the day line and the same button, same sheet); dismiss it, or leave the 7-day window, and that one is back.
   Below 1140px the rail is hidden, so the same card is drawn at the top of Home's main column (#hmRegTop) instead. */
function hmRegCardKey(){
  try{
    if(typeof sbUser==='undefined'||!sbUser)return null;
    var c=cfg(); if(!c||!c.REGISTRATION_OPENS)return null;
    var regIn=(typeof regPacificGap==='function')?regPacificGap(c.REGISTRATION_OPENS):daysUntil(c.REGISTRATION_OPENS);
    if(regIn==null||regIn<0||regIn>7)return null;
    var key='reg_'+c.REGISTRATION_OPENS;
    if(campusBannerDismissed(key))return null;
    return {key:key,regIn:regIn};
  }catch(e){ return null; }
}
function hmRegCardOn(){ return !!hmRegCardKey(); }
function hmRegCardHtml(where){
  var k=hmRegCardKey(); if(!k)return '';
  var top=(where==='top');
  var when=k.regIn===0?'today':k.regIn===1?'tomorrow':'in '+k.regIn+' days';
  var lab=(typeof regDayLabel==='function')?regDayLabel():'';
  var info=null; try{ info=(typeof regDayInfo==='function')?regDayInfo():null; }catch(e){}
  var dayLine='';
  if(info&&info.set){ var m=/^Register (.+)$/.exec(String(info.head||'')); dayLine=m?('Your day: '+m[1]+(info.sub?' · '+info.sub:'')):String(info.head||''); }
  return '<section id="'+(top?'hmRegCardN':'hmRegCard')+'" class="hm-card hm-regcard'+(top?' hm-regtop':'')+'" aria-label="Registration opens">'
    +'<button type="button" class="cb-x hm-regx" title="Dismiss" aria-label="Dismiss" onclick="dismissRegCard(\\''+k.key+'\\')">&times;</button>'
    +'<div class="hm-reg-h"><span class="hm-reg-ic" aria-hidden="true">📅</span><b>Round 1 registration opens '+when+'</b></div>'
    +'<p class="hm-reg-s">Your game plan says what to register for first, with a backup for each class.</p>'
    +(dayLine?'<div class="hm-reg-day">'+escAcc(dayLine)+'</div>':'')
    +'<div class="hm-reg-acts"><button type="button" class="btn primary" onclick="if(window.TCPlans)TCPlans.fromBanner();else show(\\'sched\\')">Your game plan</button>'
    +(lab?'<button type="button" class="btn" onclick="regDayOpen(&quot;banner&quot;)">'+lab+'</button>':'')+'</div></section>';
}
function hmRegTopPaint(){
  var t=document.getElementById('hmRegTop'); if(!t)return;
  var h=''; try{ h=hmRegCardHtml('top'); }catch(e){}
  if(t.innerHTML!==h)t.innerHTML=h;
}
function hmRegCardPaint(){
  var rail=document.getElementById('hmRailR');
  if(rail){
    var old=document.getElementById('hmRegCard'), html='';
    try{ html=hmRegCardHtml('rail'); }catch(e){}
    if(old&&html)old.outerHTML=html;
    else if(old)old.remove();
    else if(html){ var td=rail.querySelector('.hm-td'); if(td)td.insertAdjacentHTML('afterend',html); }
  }
  hmRegTopPaint();
}
function dismissRegCard(key){
  try{localStorage.setItem('professify_dismiss_'+key,'1');}catch(e){}
  ['hmRegCard','hmRegCardN'].forEach(function(id){ var el=document.getElementById(id); if(el)el.remove(); });
  try{ if(typeof regDayRepaint==='function')regDayRepaint(); else hmRegCardPaint(); }catch(e){}   /* the rail's own day card comes back */
  try{ hmPlaceRail(); }catch(e){}
}
try{ window.hmRegCardHtml=hmRegCardHtml; window.hmRegCardOn=hmRegCardOn; window.hmRegCardPaint=hmRegCardPaint; window.dismissRegCard=dismissRegCard; }catch(e){}""")

# the rail: under the greeting card, above the registration-day card
one("""  /* Your registration day — from 14 days before Round 1 until its last day (website-registration-day, 2026-10-14) */
  try{ if(typeof regSlotHtml==='function')out+=regSlotHtml('rail'); }catch(e){}""",
    """  /* website-sync (2026-10-15): the registration banner, as a card, directly under the greeting */
  try{ out+=hmRegCardHtml('rail'); }catch(e){}
  /* Your registration day — from 14 days before Round 1 until its last day (website-registration-day, 2026-10-14) */
  try{ if(typeof regSlotHtml==='function')out+=regSlotHtml('rail'); }catch(e){}""")

# regday-js: the banner's button is the card's button now
one("""    if (a.closest('#campusBanner') && /^regDayOpen/.test(a.getAttribute('onclick') || '')) return { banner: 1 };""",
    """    if (a.closest('.hm-regcard') && /^regDayOpen/.test(a.getAttribute('onclick') || '')) return { banner: 1 };   /* website-sync (2026-10-15): the card on Home's rail, not the top banner */""")
one("""    var all = k.banner ? document.querySelectorAll('#campusBanner button[onclick^="regDayOpen"]') :""",
    """    var all = k.banner ? document.querySelectorAll('.hm-regcard button[onclick^="regDayOpen"]') :""")
one("""      var sel = from === 'banner' ? '#campusBanner button[onclick^="regDayOpen"]' :""",
    """      var sel = from === 'banner' ? '.hm-regcard button[onclick^="regDayOpen"]' : from === 'gp' ? '#plGpBack [data-rg-act="open"]' :""")
one("""    for (var i = 0; i < all.length; i++) if (k.banner || (all[i].getAttribute('data-id') || null) === (k.id || null)) { try { all[i].focus({ preventScroll: true }); } catch (_) {} return; }""",
    """    for (var i = 0; i < all.length; i++) if (k.banner ? all[i].offsetParent !== null : (all[i].getAttribute('data-id') || null) === (k.id || null)) { try { all[i].focus({ preventScroll: true }); } catch (_) {} return; }   /* website-sync: the card has a rail copy and a narrow-screen copy; the visible one */""")
# the rail's own day card is not drawn while the compact card shows
one("""    if (!active() || (where === 'rail' && !railOn())) return '';
    var L = lines(); if (!L) return '';""",
    """    if (!active() || (where === 'rail' && !railOn())) return '';
    /* website-sync (2026-10-15): one card on Home — the compact "Round 1 registration opens" card carries the day and the button, so this one waits */
    if (where === 'rail' && typeof hmRegCardOn === 'function' && hmRegCardOn()) return '';
    var L = lines(); if (!L) return '';""")
# the narrow-screen host, and its paint
one("""        <div id="hmRailSlot"></div>
""", """        <div id="hmRegTop"></div>   <!-- website-sync (2026-10-15): the registration card where the rail is hidden (<1140px) -->
        <div id="hmRailSlot"></div>
""")
one("""  try{ out+=hmRatedCardsHtml('hm-desk'); }catch(e){}
  host.innerHTML=out;
}""", """  try{ out+=hmRatedCardsHtml('hm-desk'); }catch(e){}
  host.innerHTML=out;
  try{ hmRegTopPaint(); }catch(e){}   /* website-sync (2026-10-15) */
}""")
one("""  window.regDayLabel = function () {""",
    """  window.regDayRepaint = repaint;
  window.regDayLabel = function () {""")

one("""    try { if (typeof renderCampusBanner === 'function') renderCampusBanner(); } catch (_) {}
    try { if (M) paintModal(); } catch (_) {}""",
    """    try { if (typeof renderCampusBanner === 'function') renderCampusBanner(); } catch (_) {}
    try { if (typeof hmRegCardPaint === 'function') hmRegCardPaint(); } catch (_) {}      /* website-sync (2026-10-15): the card on Home's rail */
    try { if (window.TCPlans && TCPlans.refreshGamePlan) TCPlans.refreshGamePlan(); } catch (_) {}   /* the Game Plan shows your day too */
    try { if (M) paintModal(); } catch (_) {}""")
one("""  window.regDayLabel = function () {""",
    """  /* website-sync (2026-10-15): what the Game Plan shows in place of the device-only "appointment time" */
  window.regDayInfo = function () { if (!active()) return null; var L = lines(); return L ? { set: !!L.set, head: L.head, sub: L.sub, full: L.full || '' } : null; };
  window.regDayLabel = function () {""")

# ====================================================================================================== TASK 2: stories
one("""  var W=hmFreeWindow();
  /* website-home-catchup (2026-10-14): the phone's order (stories-freeness) — see hmStoryState. Outside the window: as it was. */
  var ranked=fr.map(function(f){ return {f:f, fs:W?hmStoryState(f,W):null}; });
  if(W)ranked.sort(hmStoryCmp);
""",
    """  /* website-sync (2026-10-15): the phone's order at every hour — see hmStoryState. It used to apply only inside the 7am-11pm
     weekday window ("outside the window: as it was"); the phone has no window (a weekend is "no classes today"), so neither has this. */
  var W=hmStoryWindow();
  var ranked=fr.map(function(f){ return {f:f, fs:hmStoryState(f,W)}; });
  ranked.sort(hmStoryCmp);
  /* pinned friends first, in the order they were pinned (up to 3), then everyone else in the freeness order (the phone's storyOrder) */
  var _pins=[]; try{ _pins=myPins(); }catch(e){}
  var _pinned=[]; _pins.forEach(function(id){ for(var i=0;i<ranked.length;i++){ if(ranked[i].f.id===id){ _pinned.push(ranked.splice(i,1)[0]); break; } } });
  ranked=_pinned.concat(ranked);
""")
one("""    var fcls=fs?(fs.state==='none'?' hm-unset':' hm-free hm-'+fs.state):'';
    return '<button class="hm-fitem'+fcls+'" onclick="openFriendProfile(\\''+jsAttr(f.id)+'\\')"'
      +' title="'+esc((f.name||'')+(fs&&fs.label!=null?fs.label:hmFreeLabel(fs)))+'">'""",
    """    var fcls=fs?(fs.state==='none'?' hm-unset':' hm-free hm-'+fs.state):'';
    var pin=false; try{ pin=isPinned(f.id); }catch(e){}
    var pinSvg='<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6l-1 6 3 3v2H7v-2l3-3z"/><path d="M12 14v7"/></svg>';
    return '<span class="hm-fw'+(pin?' pinned':'')+'" data-fid="'+esc(f.id)+'"><button class="hm-fitem'+fcls+(pin?' pinned':'')+'" data-fid="'+esc(f.id)+'" onclick="openFriendProfile(\\''+jsAttr(f.id)+'\\')"'
      +' title="'+esc((f.name||'')+(fs&&fs.label!=null?fs.label:hmFreeLabel(fs))+(pin?' — pinned to the front':''))+'">'""")
one("""      +'<span class="ring"><span class="fav" style="background:'+hmFriendColor(f)+'">'
        +((typeof avaHtml==='function')?avaHtml(f.avatar_url,f.name):esc(f.ini||hmIni(f.name)))+'</span></span>'
      +'<span class="nm">'+esc(f.name||'Friend')+'</span></button>';
  }).join('');""",
    """      +'<span class="ring"><span class="fav" style="background:'+hmFriendColor(f)+'">'
        +((typeof avaHtml==='function')?avaHtml(f.avatar_url,f.name):esc(f.ini||hmIni(f.name)))+'</span>'
        +(pin?'<i class="hm-pinbadge" aria-hidden="true">'+pinSvg+'</i>':'')+'</span>'
      +'<span class="nm">'+esc(f.name||'Friend')+'</span></button>'
      +'<button type="button" class="hm-spin'+(pin?' on':'')+'" aria-pressed="'+(pin?'true':'false')+'" aria-label="'+(pin?'Unpin ':'Pin ')+escAcc(f.name||'friend')+(pin?'':' to the front of your stories')+'" '
      +'onclick="togglePin(\\''+jsAttr(f.id)+'\\',event)">'+pinSvg+'</button></span>';
  }).join('');""")

# hmStoryWindow: a day index and the minute, always (a weekend has no index: no class matches, so "no classes today")
one("""function hmStoryCmp(a,b){""",
    """/* website-sync (2026-10-15): the phone's CLOCK.day / CLOCK.min — no window. Mo-Fr index GP_DAYS; a weekend is -1, which no class
   matches, so a friend with a schedule is "no classes today" exactly as on the phone. hmNowOverride is the same seam as hmFreeWindow's. */
function hmStoryWindow(d){
  d=d||(typeof window!=='undefined'&&window.hmNowOverride)||new Date();
  var di=(typeof GP_DAYS!=='undefined')?GP_DAYS.indexOf(HM_JSDAY[d.getDay()]):-1;
  return {di:di,now:d.getHours()*60+d.getMinutes()};
}
try{ window.hmStoryWindow=hmStoryWindow; }catch(e){}
function hmStoryCmp(a,b){""")

# pins
one("""var PIN_MAX=2;
function myPins(){
  try{ return (myProfile&&Array.isArray(myProfile.pinned_friends))?myProfile.pinned_friends.slice(0,PIN_MAX):[]; }catch(e){ return []; }
}""",
    """var PIN_MAX=3;   /* website-sync (2026-10-15): the phone's three. Until set_pinned_friends is installed the column's own check (2) still applies: see pinMax() */
function pinMax(){ try{ return (window.TCSYNC&&TCSYNC.pinsRpc===true)?PIN_MAX:2; }catch(e){ return 2; } }
function pinOrList(a){ return a.length<2?a.join(''):a.slice(0,-1).join(', ')+' or '+a[a.length-1]; }
/* a pin is a friend: once the friend list has loaded, an id that is not on it (unfriended) is not a pin and does not count */
function myPins(){
  try{
    var a=(myProfile&&Array.isArray(myProfile.pinned_friends))?myProfile.pinned_friends.slice():[];
    if(typeof friendsLoaded!=='undefined'&&friendsLoaded&&typeof friendsList!=='undefined')a=a.filter(function(id){ return friendsList.some(function(f){ return f.id===id; }); });
    return a.slice(0,PIN_MAX);
  }catch(e){ return []; }
}""")
span("""async function togglePin(id,ev){""", """/* New information — a pin moved, a friend landed""",
     """async function togglePin(id,ev){
  if(ev&&ev.stopPropagation)ev.stopPropagation();
  if(!(typeof sbUser!=='undefined'&&sbUser)||!myProfile)return false;
  if(!(typeof findFriend==='function'&&findFriend(id)))return false;               /* only a friend can be pinned (the phone: TC.friends.indexOf) */
  if(window._pinBusy)return false;
  var cur=myPins(), next, max=pinMax(), on=cur.indexOf(id)>=0;
  var first=function(x){ var f=(typeof findFriend==='function')?findFriend(x):null; return String((f&&f.name)||'someone').split(/\\s+/)[0]; };
  if(on)next=cur.filter(function(x){ return x!==id; });
  else if(cur.length>=max){
    /* Silently dropping someone's pin to make room would be a change the student did not ask for and cannot see. The phone's words. */
    try{ frToast(max+' pinned already — unpin '+pinOrList(cur.map(first))+' first'); }catch(e){}
    return false;
  }
  else next=cur.concat([id]);
  var was=myProfile.pinned_friends;
  myProfile.pinned_friends=next;
  try{ frToast(on?('Unpinned '+first(id)):('Pinned '+first(id)+' to the front')); }catch(e){}
  var paint=function(){
    try{ hmFreeChanged(); }catch(e){}
    try{ if(document.getElementById('hmStripWrap'))hmRenderStrip(); }catch(e){}
    try{ if(typeof renderFriends==='function')renderFriends(); }catch(e){}
  };
  paint();
  window._pinBusy=true;
  try{
    var viaRpc=!!(window.TCSYNC&&TCSYNC.pinsRpc===true), kept=null;
    if(viaRpc){
      var r=await sb.rpc('set_pinned_friends',{p_ids:next});
      if(r.error)throw r.error;
      kept=Array.isArray(r.data)?r.data.filter(function(x){ return typeof x==='string'; }):null;     /* what the server kept: friends only, max 3 */
    }else{
      var r2=await sb.from('profiles').update({pinned_friends:next}).eq('id',sbUser.id);
      if(r2.error)throw r2.error;
    }
    window._pinBusy=false;
    if(kept&&JSON.stringify(kept)!==JSON.stringify(next)){ myProfile.pinned_friends=kept; paint(); }
    return true;
  }catch(e){
    window._pinBusy=false;
    myProfile.pinned_friends=was;
    paint();
    try{ frToast((window.TCSYNC&&TCSYNC.pinsRpc===true)?'Couldn’t save that — try again.':'Could not save that pin — the column may not be installed yet.'); }catch(_e){}
    return false;
  }
}
""")

# ====================================================================================================== GAP 1: profile
one("""  const PROFILE_COLS='id,display_name,username,avatar_url,instagram_handle,major,class_standing';""",
    """  /* website-sync (2026-10-15): major, class_standing and concentration are SELECT-granted and are the account's own — they are read
     back now (they never were; the website kept them in this browser only). pinned_friends is NOT selectable by `authenticated`
     (the pins come from my_pinned_friends()), so it is not asked for here any more: asking was a 42501 on every sign-in. */
  const PROFILE_COLS='id,display_name,username,avatar_url,instagram_handle,major,class_standing';""")
one("""  let {data}=await sb.from('profiles').select(PROFILE_COLS+',pinned_friends').eq('id',sbUser.id).maybeSingle();
  if(!data){""",
    """  let {data}=await sb.from('profiles').select(PROFILE_COLS+',concentration').eq('id',sbUser.id).maybeSingle();
  if(!data){""")
one("""  if(data){myProfile=data;cacheMyProfile(data);try{refreshAvatarCache();}catch(_a){}return;}
  let name=(sbUser.email||'')""",
    """  if(data){
    myProfile=data;cacheMyProfile(data);try{refreshAvatarCache();}catch(_a){}
    try{ if(typeof tcApplyAccountProfile==='function')tcApplyAccountProfile(data); }catch(_a){}   /* website-sync (2026-10-15): the account's major/year/concentration */
    return;
  }
  let name=(sbUser.email||'')""")
one("""async function syncProfileToBackend(){
  if(typeof backendReady!=='function'||!backendReady()||!sbUser)return;
  var patch={major:student.major||null,concentration:student.conc||null,class_standing:student.standing||null};
  try{ await sb.from('profiles').update(patch).eq('id',sbUser.id); if(myProfile)Object.assign(myProfile,patch); }catch(e){}
}""",
    """/* website-sync (2026-10-15): written on EVERY change (Settings used to change this browser only), with the phone's conversions:
   the renamed major, "General / Open" is no concentration (null). profile_pend marks a change the account has not taken yet, so
   the next sign-in sends it instead of letting the account's older value overwrite it. */
var TC_MAJOR_RENAMED={"Recreation, Parks & Tourism Administration / Experience Industry Management":"Experience & Event Management"};
function tcMajorNow(m){ return (m&&TC_MAJOR_RENAMED[m])||m; }
function tcConcClean(c){ return (c&&c!=='General / Open')?String(c):null; }
async function syncProfileToBackend(){
  if(typeof backendReady!=='function'||!backendReady()||!sbUser)return;
  var patch={major:tcMajorNow(student.major)||null,concentration:tcConcClean(student.conc),class_standing:student.standing||null};
  var uid=sbUser.id, pk='professify_prof_pend_'+uid;
  try{ localStorage.setItem(pk,'1'); }catch(e){}
  try{
    var r=await sb.from('profiles').update(patch).eq('id',uid);
    if(r.error&&/concentration|column|schema/i.test((r.error.message||'')+' '+(r.error.code||''))){ var p2=Object.assign({},patch); delete p2.concentration; r=await sb.from('profiles').update(p2).eq('id',uid); }
    if(r.error){ console.warn('[professify] profile sync:',r.error.message); return; }
    try{ localStorage.removeItem(pk); }catch(e){}
    if(myProfile&&sbUser&&sbUser.id===uid)Object.assign(myProfile,patch);
  }catch(e){}
}""")
one("""function setChangeMajor(v){ student.major=v; student.conc=null; renderSetConc(); applyStudentChange(); }
function setChangeConc(v){ student.conc=v||null; applyStudentChange(); }
function setChangeStanding(v){ student.standing=v; saveProfile(); try{if(window.schSyncToStudent)window.schSyncToStudent();}catch(e){} }""",
    """function setChangeMajor(v){ student.major=v; student.conc=null; renderSetConc(); applyStudentChange(); try{syncProfileToBackend();}catch(e){} }
function setChangeConc(v){ student.conc=v||null; applyStudentChange(); try{syncProfileToBackend();}catch(e){} }
function setChangeStanding(v){ student.standing=v; saveProfile(); try{if(window.schSyncToStudent)window.schSyncToStudent();}catch(e){} try{syncProfileToBackend();}catch(e){} }""")
one("""  student.major=(p.major==="Recreation, Parks & Tourism Administration / Experience Industry Management")?"Experience & Event Management":p.major;   /* renamed 2026-10-06 */""",
    """  student.major=tcMajorNow(p.major);   /* renamed 2026-10-06 (the one map, shared with the account sync) */""")
one("""<select id="obStanding"><option>Freshman</option><option>Sophomore</option><option>Junior</option><option>Senior</option></select>""",
    """<select id="obStanding"><option>Freshman</option><option>Sophomore</option><option>Junior</option><option>Senior</option><option>5th year +</option></select>""")

# ====================================================================================================== GAP 3: sections
one("""async function pushMySecToDb(code,rec){
  if(!backendReady()||typeof sbUser==='undefined'||!sbUser||!rec||!rec.crn)return;
  try{ await sb.from('my_sections').upsert({user_id:sbUser.id,term:mcTerm(),code:code,class_nbr:String(rec.crn),section:rec.section||null,instructor:rec.prof||null,days:rec.days||null,status:(rec.status==='waitlisted'?'waitlisted':'enrolled'),wl_pos:(rec.status==='waitlisted'?(rec.wlPos||null):null)}); }
  catch(e){ /* table may not exist yet */ }
}
async function deleteMySecFromDb(crn){
  if(!backendReady()||typeof sbUser==='undefined'||!sbUser||!crn)return;
  try{ await sb.from('my_sections').delete().eq('user_id',sbUser.id).eq('class_nbr',String(crn)).eq('term',mcTerm()); }catch(e){}
}
async function pushWatchSecToDb(code,s,added){
  if(!backendReady()||typeof sbUser==='undefined'||!sbUser||!s||!s.class_nbr)return;
  try{
    if(added){ await sb.from('watch_sections').upsert({user_id:sbUser.id,term:mcTerm(),code:code,class_nbr:String(s.class_nbr),section:s.section||null,instructor:s.name||null,days:(typeof _secTime==='function'?_secTime(s):s.days)||null}); }
    else{ await sb.from('watch_sections').delete().eq('user_id',sbUser.id).eq('class_nbr',String(s.class_nbr)).eq('term',mcTerm()); }
  }catch(e){}
}""",
    """/* website-sync (2026-10-15): the queue of section ADDS this device has not landed yet (per account and term), the one thing the
   server's list may lack and still be right. A section the server lacks that is NOT queued was removed somewhere else (the phone's
   remove / swap), and the website must not put it back — see loadMySectionsFromDb / backfillMySectionsToDb / loadWatchSectionsFromDb. */
function secPendKey(kind){ return 'professify_secpend_'+kind+'_'+((typeof sbUser!=='undefined'&&sbUser)?sbUser.id:'')+'_'+mcTerm(); }
function secPendGet(kind){ try{ var a=JSON.parse(localStorage.getItem(secPendKey(kind))||'[]'); return Array.isArray(a)?a.map(String):[]; }catch(e){ return []; } }
function secPendSet(kind,a){ try{ localStorage.setItem(secPendKey(kind),JSON.stringify(a)); }catch(e){} }
function secPendMark(kind,crn){ crn=String(crn); var a=secPendGet(kind); if(a.indexOf(crn)<0){ a.push(crn); secPendSet(kind,a); } }
function secPendClear(kind,crn){ crn=String(crn); var a=secPendGet(kind), i=a.indexOf(crn); if(i>=0){ a.splice(i,1); secPendSet(kind,a); } }
/* once per account and term: sections that were on this device before the queue existed are adopted (pushed), then the rule is strict */
function secAdoptedKey(kind){ return 'professify_secadopt_'+kind+'_'+((typeof sbUser!=='undefined'&&sbUser)?sbUser.id:'')+'_'+mcTerm(); }
function secAdopted(kind){ try{ return localStorage.getItem(secAdoptedKey(kind))==='1'; }catch(e){ return false; } }
function secAdoptSet(kind){ try{ localStorage.setItem(secAdoptedKey(kind),'1'); }catch(e){} }
async function pushMySecToDb(code,rec){
  if(!backendReady()||typeof sbUser==='undefined'||!sbUser||!rec||!rec.crn)return;
  secPendMark('my',rec.crn);
  try{
    var r=await sb.from('my_sections').upsert({user_id:sbUser.id,term:mcTerm(),code:code,class_nbr:String(rec.crn),section:rec.section||null,instructor:rec.prof||null,days:rec.days||null,status:(rec.status==='waitlisted'?'waitlisted':'enrolled'),wl_pos:(rec.status==='waitlisted'?(rec.wlPos||null):null)});
    if(r&&!r.error)secPendClear('my',rec.crn);
  }
  catch(e){ /* table may not exist yet */ }
}
async function deleteMySecFromDb(crn){
  if(!backendReady()||typeof sbUser==='undefined'||!sbUser||!crn)return;
  secPendClear('my',crn);          /* a removal cancels an add that was still queued */
  try{ await sb.from('my_sections').delete().eq('user_id',sbUser.id).eq('class_nbr',String(crn)).eq('term',mcTerm()); }catch(e){}
}
async function pushWatchSecToDb(code,s,added){
  if(!backendReady()||typeof sbUser==='undefined'||!sbUser||!s||!s.class_nbr)return;
  try{
    if(added){
      secPendMark('watch',s.class_nbr);
      var r=await sb.from('watch_sections').upsert({user_id:sbUser.id,term:mcTerm(),code:code,class_nbr:String(s.class_nbr),section:s.section||null,instructor:s.name||null,days:(typeof _secTime==='function'?_secTime(s):s.days)||null});
      if(r&&!r.error)secPendClear('watch',s.class_nbr);
    }
    else{ secPendClear('watch',s.class_nbr); await sb.from('watch_sections').delete().eq('user_id',sbUser.id).eq('class_nbr',String(s.class_nbr)).eq('term',mcTerm()); }
  }catch(e){}
}""")

# my_sections: the server's list replaces the term's local sections (queued adds kept)
one("""    var _ok=Object.keys(_orphans);
    if(_ok.length){""",
    """    /* website-sync (2026-10-15): the server's list REPLACES this term's local sections. A section only this device has is kept
       only when it is a queued add (or, once per account and term, adopted by the backfill that runs next); anything else was
       removed or swapped on another device (the phone), and putting it back is exactly what the backfill used to do. */
    try{
      var _srv={}; data.forEach(function(r){ if(r&&r.class_nbr!=null)_srv[String(r.class_nbr)]=1; });
      var _pend=secPendGet('my'), _ad=secAdopted('my');
      if(_ad){
        Object.keys(myClassMeta||{}).forEach(function(code){
          var m=myClassMeta[code]; if(!m||!Array.isArray(m.secs)||myClasses.indexOf(code)<0)return;
          var before=m.secs.length;
          m.secs=m.secs.filter(function(x){ return !x||!x.crn||_srv[String(x.crn)]||_pend.indexOf(String(x.crn))>=0; });
          if(m.secs.length!==before){
            var f0=m.secs[0]; if(f0){ m.prof=f0.prof||m.prof; if(f0.days)m.time=f0.days; }
            try{ mcSyncWaitlist(code); }catch(e){}
          }
        });
      }
    }catch(e){}
    var _ok=Object.keys(_orphans);
    if(_ok.length){""")
# backfill: only queued adds (and the one adoption pass)
one("""      if(myClasses.indexOf(code)<0||mcPendingDeleted(code))return;
      m.secs.forEach(function(rec){ if(rec&&rec.crn)pending.push({code:code,rec:rec}); });
    });
  }catch(e){ return 0; }""",
    """      if(myClasses.indexOf(code)<0||mcPendingDeleted(code))return;
      /* website-sync (2026-10-15): only a queued add, or (once) a section from before the queue existed; never "everything local the
         server lacks" — that put back sections the phone had removed */
      var _q=secPendGet('my'), _adopt=!secAdopted('my');
      m.secs.forEach(function(rec){ if(rec&&rec.crn&&(_adopt||_q.indexOf(String(rec.crn))>=0))pending.push({code:code,rec:rec}); });
    });
  }catch(e){ return 0; }""")
one("""  var missing=pending.filter(function(p){return !have[String(p.rec.crn)];});
  if(!missing.length)return 0;""",
    """  var missing=pending.filter(function(p){return !have[String(p.rec.crn)];});
  secAdoptSet('my');                               /* the adoption pass is done once the server has been read */
  pending.forEach(function(p){ if(have[String(p.rec.crn)])secPendClear('my',p.rec.crn); });
  if(!missing.length)return 0;""")
# watch_sections
one("""    data.forEach(function(r){
      var code=(r.code||'').trim(); if(!code)return;
      if(watchClasses.indexOf(code)<0)watchClasses.push(code);
      watchMeta[code]=watchMeta[code]||{}; watchMeta[code].secs=Array.isArray(watchMeta[code].secs)?watchMeta[code].secs:[];
      var rec={crn:String(r.class_nbr||''),section:r.section||'',prof:r.instructor||'',days:r.days||''};
      var arr=watchMeta[code].secs, ix=arr.findIndex(function(x){return String(x.crn)===rec.crn&&rec.crn;});
      if(ix>=0)arr[ix]=rec; else arr.push(rec);
    });
    try{saveWatchClasses();saveWatchMeta();}catch(e){}""",
    """    /* website-sync (2026-10-15): what the server's list does not hold is dropped unless it is a queued add (or, once per account and
       term, adopted: pushed now). A watch the phone removed stays removed. */
    var _srvW={}; data.forEach(function(r){ if(r&&r.class_nbr!=null)_srvW[String(r.class_nbr)]=1; });
    var _pendW=secPendGet('watch'), _adW=secAdopted('watch');
    if(!_adW){
      Object.keys(watchMeta||{}).forEach(function(code){ var m=watchMeta[code]; if(m&&Array.isArray(m.secs))m.secs.forEach(function(x){ if(x&&x.crn&&!_srvW[String(x.crn)]){ secPendMark('watch',x.crn); _pendW.push(String(x.crn));
        try{ pushWatchSecToDb(code,{class_nbr:x.crn,section:x.section,name:x.prof,days:x.days},true); }catch(e){} } }); });
      secAdoptSet('watch');
    }else{
      Object.keys(watchMeta||{}).forEach(function(code){
        var m=watchMeta[code]; if(!m||!Array.isArray(m.secs)||!m.secs.length)return;
        m.secs=m.secs.filter(function(x){ return !x||!x.crn||_srvW[String(x.crn)]||_pendW.indexOf(String(x.crn))>=0; });
        if(!m.secs.length){ delete watchMeta[code]; var wi=watchClasses.indexOf(code); if(wi>=0)watchClasses.splice(wi,1); }   /* the last watched section went: the same as wcWatchSec */
      });
    }
    data.forEach(function(r){
      var code=(r.code||'').trim(); if(!code)return;
      if(watchClasses.indexOf(code)<0)watchClasses.push(code);
      watchMeta[code]=watchMeta[code]||{}; watchMeta[code].secs=Array.isArray(watchMeta[code].secs)?watchMeta[code].secs:[];
      var rec={crn:String(r.class_nbr||''),section:r.section||'',prof:r.instructor||'',days:r.days||''};
      var arr=watchMeta[code].secs, ix=arr.findIndex(function(x){return String(x.crn)===rec.crn&&rec.crn;});
      if(ix>=0)arr[ix]=rec; else arr.push(rec);
    });
    try{saveWatchClasses();saveWatchMeta();}catch(e){}""")

# ---- the sign-in pipeline: pins, saved items, favourite teachers
one("""      .then(()=>{renderFriends();maybeOnboardAfterSignup();});   // fills in name/handle; new accounts get one-step setup""",
    """      .then(()=>{renderFriends();maybeOnboardAfterSignup();});   // fills in name/handle; new accounts get one-step setup
    /* website-sync (2026-10-15): your pins (my_pinned_friends) and your favourite teachers, once the profile row exists; neither gates a render */
    const syncP=profileP.then(function(){ return Promise.all([
      withTimeout((typeof tcPinsLoad==='function'?tcPinsLoad():Promise.resolve()),6000,'tcPinsLoad'),
      withTimeout((typeof tcFavsLoad==='function'?tcFavsLoad():Promise.resolve()),6000,'tcFavsLoad')]); }).catch(function(){});""")
one("""    const watchP=withTimeout(loadWatchSectionsFromDb(),8000,'loadWatchSectionsFromDb')
      .finally(function(){ try{ pfSyncDone('Watchlist'); }catch(e){} });""",
    """    /* website-sync (2026-10-15): the saved list first (saved_items), then the section watches that sit on it */
    const watchP=withTimeout(Promise.resolve().then(function(){ return (typeof tcSavedLoad==='function')?tcSavedLoad():null; }).catch(function(){}).then(function(){ return loadWatchSectionsFromDb(); }),14000,'loadWatchSectionsFromDb')
      .finally(function(){ try{ pfSyncDone('Watchlist'); }catch(e){} });""")
one("""    await Promise.allSettled([friendsP,profileP,historyP,classesP,watchP,safetyP,pendingP,nowP]);""",
    """    await Promise.allSettled([friendsP,profileP,historyP,classesP,watchP,safetyP,pendingP,nowP,syncP]);""")
one("""    [hmFreeChanged,renderExplore,renderFriends,renderCampusBanner,startFriendRealtime,""",
    """    [hmFreeChanged,function(){ if(document.getElementById('hmStripWrap'))hmRenderStrip(); },renderExplore,renderFriends,renderCampusBanner,startFriendRealtime,""")

# ====================================================================================================== GAP 7 hooks: every watch-list save tells the saved_items sync
one("""function saveWatch(){try{localStorage.setItem('professify_watch',JSON.stringify(watchlist));}catch(e){}}""",
    """function saveWatch(){try{localStorage.setItem('professify_watch',JSON.stringify(watchlist));}catch(e){} try{ if(window.tcSavedChanged)tcSavedChanged(); }catch(e){}}""")
one("""function saveWatchClasses(){try{localStorage.setItem(MC_LS('professify_watch_classes'),JSON.stringify(watchClasses));}catch(e){}}""",
    """function saveWatchClasses(){try{localStorage.setItem(MC_LS('professify_watch_classes'),JSON.stringify(watchClasses));}catch(e){} try{ if(window.tcSavedChanged)tcSavedChanged(); }catch(e){}}""")

# ====================================================================================================== GAP 5: chat
one("""  latestMessages:function(ids){ return sb.from('messages').select('conversation_id,sender,kind,body,created_at').in('conversation_id',ids).order('created_at',{ascending:false}).limit(300); },""",
    """  latestMessages:function(ids){ return sb.from('messages').select('id,conversation_id,sender,kind,body,created_at').in('conversation_id',ids).order('created_at',{ascending:false}).limit(300); },
  /* website-sync (2026-10-15): what the phone already honours — chats you deleted, messages you deleted for yourself, chats you muted, likes */
  clears:        function(){ return sb.from('conversation_clears').select('conversation_id,cleared_at'); },
  hides:         function(){ return sb.from('message_hides').select('message_id').limit(5000); },
  mutes:         function(){ return sb.from('conversation_mutes').select('conversation_id'); },
  likes:         function(ids){ return sb.from('message_likes').select('message_id,user_id').in('message_id',ids); },""")
one("""function msgDb(){ return window.msgDbOverride||MSG_DB; }""",
    """function msgDb(){ return window.msgDbOverride||MSG_DB; }
/* website-sync (2026-10-15): the phone's msgVisible / chatCleared (P:5318-5330). A table that is not there is "nothing hidden", not a failure. */
var msgX={clears:{},hidden:{},mutes:{},likes:{}};
function msgVisible(m){
  if(!m)return false;
  if(msgX.hidden[String(m.id)])return false;                                    /* deleted for me */
  try{ if(typeof isBlocked==='function'&&isBlocked(m.sender))return false; }catch(e){}     /* a blocked sender's words, old ones too */
  var c=msgX.clears[m.conversation_id];
  return !c||new Date(m.created_at)>new Date(c);                               /* not from before I deleted the chat */
}
function msgCleared(t){ var c=t&&msgX.clears[t.id]; return !!c&&new Date(t.last_at)<=new Date(c); }
async function msgLoadHides(){
  var db=msgDb(); if(!db||typeof db.clears!=='function')return;
  var r; try{ r=await Promise.all([db.clears(),db.hides(),db.mutes()]); }catch(e){ return; }
  var clr=r[0], hid=r[1], mut=r[2];
  if(clr&&!clr.error&&Array.isArray(clr.data)){ var c={}; clr.data.forEach(function(x){ c[x.conversation_id]=x.cleared_at; }); msgX.clears=c; }
  if(hid&&!hid.error&&Array.isArray(hid.data)){ var h={}; hid.data.forEach(function(x){ h[String(x.message_id)]=1; }); msgX.hidden=h; }
  if(mut&&!mut.error&&Array.isArray(mut.data)){ var u={}; mut.data.forEach(function(x){ u[String(x.conversation_id)]=1; }); msgX.mutes=u; }
}
async function msgLoadLikes(cid){
  var db=msgDb(); if(!db||typeof db.likes!=='function')return;
  var ids=(msgRows[cid]||[]).slice(-100).map(function(m){ return m.id; }); if(!ids.length)return;
  var r; try{ r=await db.likes(ids); }catch(e){ return; }
  if(!r||r.error||!Array.isArray(r.data))return;
  var L={}; r.data.forEach(function(x){ (L[String(x.message_id)]=L[String(x.message_id)]||[]).push(x.user_id); });
  msgX.likes=Object.assign({},msgX.likes,L);
}""")
one("""    var readAt={}; (mine.data||[]).forEach(function(r){readAt[r.conversation_id]=r.last_read_at;});

    var convs=await msgDb().conversations(ids);""",
    """    var readAt={}; (mine.data||[]).forEach(function(r){readAt[r.conversation_id]=r.last_read_at;});
    await msgLoadHides();           /* website-sync (2026-10-15): before the previews, which must not show a hidden message */

    var convs=await msgDb().conversations(ids);""")
one("""      if(!lastOf[m.conversation_id])lastOf[m.conversation_id]=m;
      /* Everyone who has SENT something""",
    """      if(!lastOf[m.conversation_id]&&msgVisible(m))lastOf[m.conversation_id]=m;      /* the newest message you can still see */
      /* Everyone who has SENT something""")
one("""  msgRows[cid]=res.data||[];
  return msgRows[cid];""",
    """  msgRows[cid]=res.data||[];
  try{ await msgLoadLikes(cid); }catch(e){}
  return msgRows[cid];""")
one("""  var rows=msgRows[t.id]||[];
  var body=rows.length""",
    """  var rows=(msgRows[t.id]||[]).filter(msgVisible);          /* website-sync (2026-10-15): not hidden, not from before a cleared chat, not a blocked sender's */
  var body=rows.length""")
one("""    +msgBodyHtml(t,m)+'</div>';
}""",
    """    +msgBodyHtml(t,m)
    +((msgX.likes[String(m.id)]||[]).length?('<span class="msg-lk" title="'+(msgX.likes[String(m.id)].length)+' like'+(msgX.likes[String(m.id)].length===1?'':'s')+'">♥ '+(msgX.likes[String(m.id)].length)+'</span>'):'')
    +'</div>';
}""")
one("""  var shown=msgThreads.filter(function(t){
    return t.kind==='group'||!!t.last||(typeof msgOpenId!=='undefined'&&t.id===msgOpenId);
  });""",
    """  var shown=msgThreads.filter(function(t){
    if(msgCleared(t)&&!(typeof msgOpenId!=='undefined'&&t.id===msgOpenId))return false;      /* website-sync (2026-10-15): a chat you deleted on the phone */
    return t.kind==='group'||!!t.last||(typeof msgOpenId!=='undefined'&&t.id===msgOpenId);
  });""")
one("""      +'<span class="msg-twhen">'+msgEsc(msgAgo(t.last_at))+'</span>'
      +(un?'<span class="msg-tdot"></span>':'')+'</div>';""",
    """      +'<span class="msg-twhen">'+msgEsc(msgAgo(t.last_at))+'</span>'
      +(msgX.mutes[String(t.id)]?'<span class="msg-tmute" title="You muted this chat">Muted</span>':'')
      +(un?'<span class="msg-tdot"></span>':'')+'</div>';""")

# ====================================================================================================== GAP 6: push
span("""async function pushPrefGet(){""", """window.pushSupported=pushSupported;""",
     """async function pushPrefGet(){
  try{
    if(typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return null;
    /* website-sync (2026-10-15): prefs is the jsonb the phone writes one switch per kind into; a database without it answers with the columns only */
    var r=await sb.from('push_prefs').select('seats,friends,quiet_from,quiet_to,prefs').eq('user_id',sbUser.id).maybeSingle();
    if(r.error)r=await sb.from('push_prefs').select('seats,friends,quiet_from,quiet_to').eq('user_id',sbUser.id).maybeSingle();
    if(r.error)return null;
    var d=r.data||{seats:true,friends:false,quiet_from:22,quiet_to:8};   /* the table's own defaults */
    if(d.prefs&&typeof d.prefs==='object'&&d.prefs.seat_open===false)d=Object.assign({},d,{seats:false});   /* the phone's "A seat opens" switch is the same switch */
    return d;
  }catch(e){ return null; }
}
/* seats -> prefs.seat_open (the phone's name for it), friends -> prefs.free (the server kind the "done for the day" push is sent as;
   the phone has no switch for it), quiet hours -> prefs.quiet_from / quiet_to. true removes the key: a kind is on unless it says false. */
async function pushPrefSet(patch){
  try{
    if(typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return false;
    var row=Object.assign({user_id:sbUser.id}, patch);
    var prefs=null;
    try{
      var g=await sb.from('push_prefs').select('prefs').eq('user_id',sbUser.id).maybeSingle();
      if(!g.error)prefs=(g.data&&g.data.prefs&&typeof g.data.prefs==='object'&&!Array.isArray(g.data.prefs))?Object.assign({},g.data.prefs):{};
    }catch(e){}
    if(prefs){
      if('seats' in patch){ if(patch.seats)delete prefs.seat_open; else prefs.seat_open=false; }
      if('friends' in patch){ if(patch.friends)delete prefs.free; else prefs.free=false; }
      if('quiet_from' in patch)prefs.quiet_from=patch.quiet_from;
      if('quiet_to' in patch)prefs.quiet_to=patch.quiet_to;
      row.prefs=prefs;
    }
    var r=await sb.from('push_prefs').upsert(row,{onConflict:'user_id'});
    if(r.error&&row.prefs){ delete row.prefs; r=await sb.from('push_prefs').upsert(row,{onConflict:'user_id'}); }
    return !r.error;
  }catch(e){ return false; }
}
""")
one("""      +'<p class="st-note" style="margin:10px 0 8px">Nothing is sent between '
      +pushHour(pf.quiet_from)+' and '+pushHour(pf.quiet_to)+'. Anything that happens overnight waits until morning.</p>'""",
    """      +'<p class="st-note push-quiet" style="margin:10px 0 8px">Quiet hours: nothing is sent between '
      +pushHourSel('quiet_from',pf.quiet_from)+' and '+pushHourSel('quiet_to',pf.quiet_to)+'. Anything that happens overnight waits until morning.</p>'""")
one("""function pushHour(h){ h=parseInt(h,10)||0; var ap=h<12?'am':'pm'; var v=h%12; return (v===0?12:v)+ap; }""",
    """function pushHour(h){ h=parseInt(h,10)||0; var ap=h<12?'am':'pm'; var v=h%12; return (v===0?12:v)+ap; }
function pushHourSel(key,cur){
  cur=parseInt(cur,10); if(!(cur>=0&&cur<=23))cur=0;
  var o=''; for(var h=0;h<24;h++)o+='<option value="'+h+'"'+(h===cur?' selected':'')+'>'+pushHour(h)+'</option>';
  return '<select class="push-hr" aria-label="'+(key==='quiet_from'?'Quiet hours start':'Quiet hours end')+'" onchange="pushPrefSet({'+key+':parseInt(this.value,10)})">'+o+'</select>';
}""")

# ====================================================================================================== GAP 8: Game Plan registration day, favourite teacher row
one("""    h += '<label class="pl2-appt"><span>Your appointment time <em>(from the Portal)</em></span>'
      + '<input type="datetime-local" data-pl-act="appt" value="' + (a && !isNaN(a) ? esc(new Date(a.getTime() - a.getTimezoneOffset() * 60000).toISOString().slice(0, 16)) : '') + '">'
      + (a && !isNaN(a) ? '<b>' + esc(countdown(a)) + '</b>' : '') + '</label>';""",
    """    /* website-sync (2026-10-15): your registration day is the account's (registration_days, the phone's), set through the same sheet as the
       cards; this used to be a device-only "appointment time" (professify_appt_2274) that nothing else ever read. */
    var rdi = null; try { rdi = (typeof regDayInfo === 'function') ? regDayInfo() : null; } catch (_) {}
    if (rdi) h += '<div class="pl2-appt" data-gp-regday="' + (rdi.set ? 'set' : 'none') + '"><span>Your registration day</span> <b>' + esc(rdi.head + (rdi.sub ? ' · ' + rdi.sub : '')) + '</b>'
      + '<button type="button" class="rg-btn' + (rdi.set ? '' : ' pri') + '" data-rg-act="open">' + (rdi.set ? 'Change' : 'Set day') + '</button></div>';""")
one("""    var g = gamePlan(gpSlot);
    var a = appt();""",
    """    var g = gamePlan(gpSlot);""")
one("""    if (act === 'appt') {
      try { if (t.value) localStorage.setItem(apptKey(), new Date(t.value).toISOString()); else localStorage.removeItem(apptKey()); } catch (_) {}
      renderGamePlan();
    }""",
    """    /* (the "appt" field is gone: website-sync, 2026-10-15 — the registration day replaces it) */""")
one("""    fromBanner: function () {
      ensure();""",
    """    refreshGamePlan: function () { var gp = document.getElementById('plGpBack'); if (gp && gp.classList.contains('open')) renderGamePlan(); },
    fromBanner: function () {
      ensure();""")
# the Game Plan's own registration-day button opens the sheet from inside the plan
one("""    if (a === 'open') { var sl = t.closest('.rg-slot'); openModal(sl ? sl.getAttribute('data-rg') : ''); }""",
    """    if (a === 'open') { var sl = t.closest('.rg-slot'); openModal(sl ? sl.getAttribute('data-rg') : (t.closest('#plGpBack') ? 'gp' : '')); }""")

one("""function startRate(id,course){
  currentProf=id;rateErrMsg='';pendingRateCourse=course||'';""",
    """function startRate(id,course){
  window._rfFav=null;                       /* website-sync (2026-10-15): a new form starts from what the account says about this professor */
  currentProf=id;rateErrMsg='';pendingRateCourse=course||'';""")
one("""      <button type="button" class="rf-more-toggle" id="rfMoreToggle" onclick="rfToggleMore()" """,
    """      ${(typeof tcFavRow==='function')?tcFavRow(id):''}
      <button type="button" class="rf-more-toggle" id="rfMoreToggle" onclick="rfToggleMore()" """)
one("""      (dbReviews[profKey(p)]=dbReviews[profKey(p)]||[]).unshift({...review,_db:true});
      reviewsGiven++;""",
    """      (dbReviews[profKey(p)]=dbReviews[profKey(p)]||[]).unshift({...review,_db:true});
      try{ if(typeof tcFavAfter==='function')tcFavAfter(p); }catch(_f){}      /* website-sync (2026-10-15): a favorite goes with the review, so after it lands */
      reviewsGiven++;""")
# ---- GAP 9: no `term` column on reviews
one("""  var patch={course:v.course||null,course_key:v.courseKey||null,term:v.term||'',score:v.score,""",
    """  /* website-sync (2026-10-15): NO `term`. reviews has no such column, so this update answered "column not found" and every edit failed
     (the retry below only drops `grade`). The term a reviewer taps is not stored by the new-review insert either. */
  var patch={course:v.course||null,course_key:v.courseKey||null,score:v.score,""")
one("""  /* The server's copy, including whether it stamped edited_at. */""",
    """  try{ if(typeof tcFavAfter==='function')tcFavAfter(p); }catch(_f){}      /* website-sync (2026-10-15) */
  /* The server's copy, including whether it stamped edited_at. */""")

# ====================================================================================================== GAP 10: normCode, saved_classes codes
one("""  const m=String(s||'').toUpperCase().replace(/[^A-Z0-9]/g,'').match(/^([A-Z]{2,5})(\\d{3,4})$/);
  return m?`${m[1]} ${m[2]}`:String(s||'').toUpperCase().trim();""",
    """  /* website-sync (2026-10-15): the phone's canonCode — "&" in the subject (A&B 1234) and a suffix letter (CHEM 1210L) are codes too */
  const m=String(s||'').toUpperCase().replace(/[^A-Z0-9&]/g,'').match(/^([A-Z&]{2,5})(\\d{3,4}[A-Z]?)$/);
  return m?`${m[1]} ${m[2]}`:String(s||'').toUpperCase().trim();""")
one("""  const dbCodes=(data||[]).map(r=>r.code);""",
    """  /* website-sync (2026-10-15): rows may hold an unspaced legacy code (the CHECK allows it); read them the way the rest of the page names a class.
     _mcRawCode remembers the spelling the server has, so removing the class deletes THAT row. */
  window._mcRawCode={};
  const dbCodes=(data||[]).map(r=>{ const n=normCode(r.code); if(n!==r.code)window._mcRawCode[n]=r.code; return n; });""")
one("""      : await sb.from('saved_classes').delete().eq('user_id',sbUser.id).eq('code',code).eq('term',mcTerm());""",
    """      : await sb.from('saved_classes').delete().eq('user_id',sbUser.id).in('code',[code].concat((window._mcRawCode&&window._mcRawCode[code])?[window._mcRawCode[code]]:[])).eq('term',mcTerm());""")

# ====================================================================================================== boot order
# The PolyRatings answer repaints Explore from a script block that is parsed BEFORE the (much larger) block that defines jsAttr; whichever
# finishes first wins, and the answer arrives from the stand-in at once. The page is a few hundred lines bigger, which is all it took to
# make renderExplore() throw "jsAttr is not defined" (check-desktop-home lift, check-desktop-delete recover). Wait until the later block exists.
one("""loadPolyRatings().then(ok=>{if(ok){window._ratingsStale=false;""",
    """loadPolyRatings().then(ok=>{ return (typeof jsAttr==='function')?ok:new Promise(function(res){ (function w(){ if(typeof jsAttr==='function')res(ok); else setTimeout(w,25); })(); }); }).then(ok=>{if(ok){window._ratingsStale=false;""")

# ====================================================================================================== the block: CSS + the sync script
BLOCK = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'website-sync-2026-10-15.block.html')).read()
one("</body>", BLOCK + "</body>")

# ================================================================ the build stamp
def sub_once(pat, rep, text):
    n = len(re.findall(pat, text))
    assert n == 1, (n, pat)
    return re.sub(pat, rep, text)
s = sub_once(r"window\.PROFESSIFY_BUILD='[^']*';", "window.PROFESSIFY_BUILD='" + stamp + "';", s)
for name in ('hawk-ask\\.css', 'hawk-router\\.js', 'hawk-ask\\.js'):
    s = sub_once(name + r"\?v=\d+", name.replace('\\', '') + '?v=' + digits, s)
w = sub_once(r"const BUILD = '[^']*';", "const BUILD = '" + stamp + "';", w)

f.write_text(s)
sw.write_text(w)
print('patched', f, sw, 'build', stamp)
