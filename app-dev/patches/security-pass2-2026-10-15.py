#!/usr/bin/env python3
"""Security pass 2 for the WEBSITE (index.html only), 2026-10-15. Eight fixes from the second review of termchamp.com.

1. "Latest reviews" on Home read the reviews TABLE. A signed-out visitor is the anon role, which may only read the view
   reviews_public (same columns, no user_id), so the strip answered 401 and stayed empty. hmLoadRecents() now reads the
   view. The other reads of the table are not "the public list" and are left alone: the author's own reviews
   (user_id = me), the friends policy toggle (update), insert/update/delete, and the one fallback in loadReviews() that
   runs only when reviews_public does not exist yet (a database that has not run the migration).
2. Signing out now clears this browser.
   * tcWipeLocal() removes every localStorage and sessionStorage key that starts professify, tc- or tc_ (classes,
     watchlists, friends cache, regday, commitments, audit, drafts, avatar bytes, profile cache, the invite stash ...)
     except the device preferences below, and puts the page's in-memory copies of the same lists back to empty.
   * KEPT, because they are about the device and not the person: professify-theme (light/dark), professify_ev_salt (the
     analytics pseudonym: random on this device, not derived from or stored against any account; see evWho), the PWA
     install-prompt counters (professify_visits, professify_install_snooze), the review-sound toggle
     (professify_ratesound), public caches (professify_prof_cache = PolyRatings, professify_course_short = the catalog's
     short names, professify_seats_cache* = seat counts) and professify_last_uid (see next). hawk-pos does not start
     with a wiped prefix. There is no cookie/consent choice key on the website (analytics consent is fixed in code).
   * professify_last_uid remembers who was last signed in here. When a DIFFERENT account is seen (at page load from the
     stored session, and again in onAuthStateChange before anything loads), the same wipe runs first, so A's classes
     can never be "adopted" into B's saved_classes by loadMySavedClasses (the professify_mc_adopted_<uid> flag path).
     The invite stash and a half-finished signup handle/phone are kept in that case only: they belong to the person
     signing in now, not to the last account.
   * If web push is subscribed on this browser, sign-out calls pushDisable() first so the previous account's
     notifications stop arriving on a shared machine. It is bounded to 2 seconds, so a slow push service cannot hold
     the sign-out; errors are swallowed.
   * "Sign out" on the account-recovery sheet wipes too.
3. Account deletion's local wipe removed /^(professify|sb-)/ only; it now also removes tc- and tc_ keys.
4. Avatars. profiles.avatar_url is restricted in the database to this project's public avatars bucket, but old cached
   values and other code paths drew any URL. tcAva() (first script on the page) returns a URL only when it starts with
   https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/ (no spaces, quotes, angle brackets,
   backslashes or ".." after that) or is a data: image (this device's own cached copy of the photo is data:image/jpeg;base64; a data: image makes no
   request and cannot run script inside an <img>; the test fixtures use data: SVGs as stand-in photos). Anything else draws the no-photo silhouette. Every avatar <img> also gets
   referrerpolicy="no-referrer". refreshAvatarCache() and the profile editor's probe no longer fetch other URLs.
5. Escaping. escapeHtml() and escAcc() now escape the single quote (&#39;). The one place that HTML-escaped and THEN
   backslash-escaped a quote for a JS string (the sign-in code step's email) now uses jsAttr(). PolyRatings is a third
   party: slugPR() now keeps only [A-Za-z0-9_] of the id it is given (a real uuid is unchanged), every openProf /
   toggleWatch / wpToggleCompare / startRate / submitRate ... handler that printed a professor id raw now goes through
   jsAttr(), and the rating form's course <option> escapes the course.
6. The session fallback cookie (used only when localStorage throws) is Secure, SameSite=Strict, path=/ and lives 7
   days instead of a year.
7. Share links: NOT changed. The &add=<id> on a shared-schedule link is the invite token on purpose ("Add <name>" on the
   landing, see SHARE MY SCHEDULE); it is the same id the QR and /invite?add= links carry, and the schedule-cards
   comment about "no account id" is about the image file's name, which is still a random token. The comment is
   clarified so the two are not confused again.
8. Analytics: evTargetName() named a click by the element's aria-label, value or text, which can be a friend's name or
   something typed. It now uses only data-ev, the element id, or the tag name.

9. The build stamp (window.PROFESSIFY_BUILD in index.html, BUILD in sw.js, and the three hawk-* ?v= digits) is set to one
   value so the service worker and the page's own files refresh together. It defaults to the clock in Los Angeles
   (UTC-7); pass the stamp as the second argument to choose it.

Usage: python3 security-pass2-2026-10-15.py <repo> ["YYYY-MM-DD HH:MM"]
"""
import sys, os, re, pathlib, subprocess
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
sw = root / 'sw.js'
s = f.read_text()
w = sw.read_text()
if 'security-pass2 (2026-10-15)' in s:
    sys.exit('already patched')
stamp = sys.argv[2] if len(sys.argv) > 2 else subprocess.check_output(['date', '+%Y-%m-%d %H:%M'], env=dict(os.environ, TZ='America/Los_Angeles')).decode().strip()
assert re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d', stamp), stamp
digits = re.sub(r'\D', '', stamp)

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)

# ================================================================ 1. Home "latest reviews" reads the public view
one("""    var r=await sb.from('reviews').select('professor_key,professor_name,department,course,score,difficulty,would_again,tags,note,created_at').order('created_at',{ascending:false}).limit(24);""",
    """    /* reviews_public, not the table: signed out, the anon role may read only the view (security-pass2, 2026-10-15) */
    var r=await sb.from('reviews_public').select('professor_key,professor_name,department,course,score,difficulty,would_again,tags,note,created_at').order('created_at',{ascending:false}).limit(24);""")

# ================================================================ 2 + 4. the helpers, in the first script (before anything reads storage)
one("""(function(){ try{ localStorage.removeItem('professify_seats_cache'); }catch(e){} })();
</script>""",
    """(function(){ try{ localStorage.removeItem('professify_seats_cache'); }catch(e){} })();

/* ---- security-pass2 (2026-10-15) --------------------------------------------------------------------------------
   AVATARS. profiles.avatar_url is restricted in the database to this project's public avatars bucket. Old cached
   values and every other path that draws a face go through here too, so a URL that is not ours never becomes an
   <img src> (no request to someone else's server, no tracking pixel). The one other thing allowed is a data: image,
   which makes no request: this device's own cached copy of YOUR photo is one (the bytes the profile editor uploaded). */
var TC_AVA_BASE='https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/';
function tcAva(u){
  u=(u==null)?'':String(u);
  if(!u)return '';
  if(u.indexOf(TC_AVA_BASE)===0)return /[\\s"'<>\\\\]|\\.\\./.test(u.slice(TC_AVA_BASE.length))?'':u;
  /* data: images make no request and cannot run script inside an <img> (an SVG there is drawn as a static picture) */
  if(/^data:image\\/(png|jpeg|webp|gif);base64,[A-Za-z0-9+\\/=]+$/.test(u)||/^data:image\\/svg\\+xml[;,]/.test(u))return u;
  return '';
}

/* SIGNING OUT CLEARS THIS BROWSER, and a different person signing in finds nothing of the last one.
   Everything this site keeps about a person starts professify, tc- or tc_. These keys are about the DEVICE, not the
   person, and stay: theme; the analytics pseudonym (random here, not derived from an account); the install-prompt
   counters; the review-sound toggle; public caches (PolyRatings, catalog short names, seat counts); and the
   remembered last user id itself. */
var TC_KEEP={'professify-theme':1,'professify_ev_salt':1,'professify_visits':1,'professify_install_snooze':1,
             'professify_ratesound':1,'professify_prof_cache':1,'professify_course_short':1,'professify_last_uid':1};
function tcKeepKey(k,o){
  if(TC_KEEP[k])return true;
  if(k.indexOf('professify_seats_cache')===0)return true;
  /* A different account signing in: the invite link it opened and a signup handle/phone it just typed are ITS, not
     the last account's, so they survive that wipe (and only that one). */
  if(o&&o.keepPending&&(k==='professify_pending_add'||k==='professify_pending_add_at'||k==='professify_pending_handle'||k==='professify_pending_phone'))return true;
  return false;
}
/* The same lists as they sit in memory. Without this the next sign-in on this page would still see them and write
   them back to storage (and loadMySavedClasses would upload them to the new account). Each line is its own try
   because some of these are declared in later scripts. */
function tcResetMemory(){
  try{ myClasses=[]; }catch(e){}
  try{ myClassMeta={}; }catch(e){}
  try{ mcPending={}; }catch(e){}
  try{ watchlist=[]; }catch(e){}
  try{ watchSpMeta={}; }catch(e){}
  try{ watchClasses=[]; }catch(e){}
  try{ watchMeta={}; }catch(e){}
  try{ gpList=[]; }catch(e){}
  try{ gpMuted={}; }catch(e){}
  try{ HM_SEEN={}; }catch(e){}
  try{ window._mcDbCodes=[]; }catch(e){}
  try{ if(typeof frSyncSaved==='function')frSyncSaved(); }catch(e){}
  ['renderMyClasses','renderWatch','renderWatchClasses'].forEach(function(fn){ try{ if(typeof window[fn]==='function')window[fn](); }catch(e){} });
}
function tcWipeLocal(o){
  o=o||{};
  ['localStorage','sessionStorage'].forEach(function(n){
    try{
      var st=window[n], dead=[];
      for(var i=0;i<st.length;i++){ var k=st.key(i); if(k&&/^(professify|tc-|tc_)/.test(k)&&!tcKeepKey(k,o))dead.push(k); }
      dead.forEach(function(k){ try{ st.removeItem(k); }catch(e){} });
    }catch(e){}
  });
  if(o.memory)tcResetMemory();
}
/* The signed-in user id as the stored session says it, read straight from storage (this runs before supabase-js). */
function tcStoredUid(){
  try{
    var raw=null;
    for(var i=0;i<localStorage.length;i++){ var k=localStorage.key(i); if(k&&/^sb-.*-auth-token$/.test(k)){ raw=localStorage.getItem(k); break; } }
    if(!raw)return '';
    var j=JSON.parse(raw), x=(j&&(j.currentSession||j.session))||j;
    return (x&&x.user&&x.user.id)?String(x.user.id):'';
  }catch(e){ return ''; }
}
/* Called with whoever is signed in now. A different account than the last one seen on this browser: wipe first, then
   remember the new one. Returns true when it wiped. Storage that cannot be read cannot be compared, so it never wipes. */
function tcSeeUser(uid,memory){
  if(!uid)return false;
  var last=null, wiped=false;
  try{ last=localStorage.getItem('professify_last_uid'); }catch(e){ return false; }
  if(last&&last!==uid){ tcWipeLocal({keepPending:true,memory:!!memory}); wiped=true; }
  try{ localStorage.setItem('professify_last_uid',uid); }catch(e){}
  return wiped;
}
/* At page load, before any later script reads a list from storage. */
(function(){ try{ var u=tcStoredUid(); if(u)tcSeeUser(u,false); }catch(e){} })();
</script>""")

# onAuthStateChange: a different account arriving in this page (session expired, then someone else signs in)
one("""    sb.auth.onAuthStateChange((_e,session)=>{
      sbUser=session?session.user:null;""",
    """    sb.auth.onAuthStateChange((_e,session)=>{
      /* a DIFFERENT account than the last one on this browser: its predecessor's local lists go first, before
         anything below can load or adopt them (security-pass2, 2026-10-15) */
      try{ if(session&&session.user&&typeof tcSeeUser==='function')tcSeeUser(session.user.id,true); }catch(_w){}
      sbUser=session?session.user:null;""")

# sign-out
one("""async function authSignOut(){ try{ if(sb&&sb.auth)await sb.auth.signOut(); }catch(e){} sbUser=null; try{ NOW_MINE={classes:[],meta:{},loaded:false}; NOW_SEATS={}; _nowSeatAsked={}; }catch(e){} eduVerified=false; try{cacheMyProfile(null);}catch(e){} updateAuthUI();""",
    """async function authSignOut(){
  /* Push first, while the session can still delete its own subscription row: on a shared browser the last account's
     notifications must stop. Capped at 2s and never fatal, so a slow push service cannot hold the sign-out (security-pass2, 2026-10-15). */
  try{
    if(typeof pushSupported==='function'&&pushSupported()&&Notification.permission==='granted'&&typeof pushDisable==='function')
      await Promise.race([pushDisable(),new Promise(function(r){ setTimeout(r,2000); })]);
  }catch(e){}
  try{ if(sb&&sb.auth)await sb.auth.signOut(); }catch(e){} sbUser=null; try{ NOW_MINE={classes:[],meta:{},loaded:false}; NOW_SEATS={}; _nowSeatAsked={}; }catch(e){} eduVerified=false; try{cacheMyProfile(null);}catch(e){}
  /* and everything else this browser kept about them (security-pass2, 2026-10-15) */
  try{ tcWipeLocal({memory:true}); }catch(e){}
  updateAuthUI();""")

one("""  try{ await sb.auth.signOut({scope:'local'}); }catch(e){}   /* this browser only */""",
    """  try{ await sb.auth.signOut({scope:'local'}); }catch(e){}   /* this browser only */
  try{ tcWipeLocal({}); }catch(e){}   /* security-pass2 (2026-10-15): signing out here is signing out */""")

# ================================================================ 3. account deletion's local wipe
one("""      if(/^(professify|sb-)/.test(k))localStorage.removeItem(k);""",
    """      if(/^(professify|sb-|tc-|tc_)/.test(k))localStorage.removeItem(k);   /* tc- and tc_ added 2026-10-15 */""")

# ================================================================ 4. avatars
# first-paint account pill (before the helpers' script? no: the helpers are in an earlier script block)
one("""        if(ac&&typeof ac.data==='string'&&ac.data.slice(0,5)==='data:'&&(!av||ac.url===av))av=ac.data;
      }catch(_a){}""",
    """        if(ac&&typeof ac.data==='string'&&ac.data.slice(0,5)==='data:'&&(!av||ac.url===av))av=ac.data;
      }catch(_a){}
      av=(typeof tcAva==='function')?tcAva(av):'';   /* only our own avatars bucket, or this device's cached bytes (security-pass2, 2026-10-15) */""")
one("""        ? '<img class="ava-img" src="'+String(av).replace(/"/g,'&quot;')+'" alt=""'
          +' onerror="this.parentNode.innerHTML=NOPH_SVG">'""",
    """        ? '<img class="ava-img" src="'+String(av).replace(/"/g,'&quot;')+'" alt="" referrerpolicy="no-referrer"'
          +' onerror="this.parentNode.innerHTML=NOPH_SVG">'""")
one("""    var url=(typeof myProfile!=='undefined'&&myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'';
    var have=cachedAvatar(sbUser.id);""",
    """    var url=tcAva((typeof myProfile!=='undefined'&&myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');   /* never fetch a URL that is not our bucket (security-pass2, 2026-10-15) */
    var have=cachedAvatar(sbUser.id);""")
one("""    if(c&&(!url||c.url===url))return c.data;
    if(url)return url;""",
    """    if(c&&(!url||c.url===url))return c.data;
    if(url)return tcAva(url);   /* a URL that is not our bucket draws the silhouette (security-pass2, 2026-10-15) */""")
one("""  var url=myAvatarUrl();
  if(url)return '<img class="ava-img" src="'+escapeHtml(url)+'" alt="" loading="lazy">';""",
    """  var url=tcAva(myAvatarUrl());
  if(url)return '<img class="ava-img" src="'+escapeHtml(url)+'" alt="" loading="lazy" referrerpolicy="no-referrer">';""")
one("""function avaHtml(url,name,cls){
  if(url)return '<img class="ava-img'+(cls?' '+cls:'')+'" src="'+escapeHtml(url)+'" alt="" loading="lazy"'""",
    """function avaHtml(url,name,cls){
  url=tcAva(url);   /* only our own avatars bucket; anything else is the silhouette (security-pass2, 2026-10-15) */
  if(url)return '<img class="ava-img'+(cls?' '+cls:'')+'" src="'+escapeHtml(url)+'" alt="" loading="lazy" referrerpolicy="no-referrer"'""")
one("""var _av=(typeof myAvatarUrl==='function')?myAvatarUrl():'';
    var _ini=escapeHtml(""",
    """var _av=tcAva((typeof myAvatarUrl==='function')?myAvatarUrl():'');
    var _ini=escapeHtml(""")
one("""      ? '<img class="ava-img" src="'+escapeHtml(_av)+'" alt="" onerror="this.parentNode.innerHTML=NOPH_SVG">'""",
    """      ? '<img class="ava-img" src="'+escapeHtml(_av)+'" alt="" referrerpolicy="no-referrer" onerror="this.parentNode.innerHTML=NOPH_SVG">'""")
one("""    var avu=(typeof myAvatarUrl==='function')?myAvatarUrl():'';
    el.innerHTML='<div class="set-acct">""",
    """    var avu=tcAva((typeof myAvatarUrl==='function')?myAvatarUrl():'');
    el.innerHTML='<div class="set-acct">""")
one("""      +(avu?'<img class="ava-img" src="'+escAcc(avu)+'" alt="">':escAcc(initials(nm||'?')))""",
    """      +(avu?'<img class="ava-img" src="'+escAcc(avu)+'" alt="" referrerpolicy="no-referrer">':escAcc(initials(nm||'?')))""")
one("""    ? '<span class="msg-av '+(cls||'')+'"><img src="'+msgEsc(p.avatar)+'" alt="" loading="lazy"></span>'""",
    """    ? '<span class="msg-av '+(cls||'')+'"><img src="'+msgEsc(p.avatar)+'" alt="" loading="lazy" referrerpolicy="no-referrer"></span>'""")
one("""function msgAva(p,cls){
  var ini=msgIni(p.name);
  return p.avatar""",
    """function msgAva(p,cls){
  var ini=msgIni(p.name);
  p=Object.assign({},p,{avatar:tcAva(p.avatar)});   /* only our own avatars bucket (security-pass2, 2026-10-15) */
  return p.avatar""")
one("""    return av?('<i><img src="'+msgEsc(av)+'" alt="" loading="lazy"></i>'):('<i>'+msgEsc(ini)+'</i>');""",
    """    av=tcAva(av);   /* only our own avatars bucket (security-pass2, 2026-10-15) */
    return av?('<i><img src="'+msgEsc(av)+'" alt="" loading="lazy" referrerpolicy="no-referrer"></i>'):('<i>'+msgEsc(ini)+'</i>');""")
one("""    var inner=p.img
      ? '<img src="'+esc2(p.img)+'" alt="" loading="lazy">'""",
    """    var inner=tcAva(p.img)
      ? '<img src="'+esc2(tcAva(p.img))+'" alt="" loading="lazy" referrerpolicy="no-referrer">'""")
one("""  if(url)return '<span class="pl-face"><img src="'+attr(url)+'" alt="" loading="lazy"></span>';""",
    """  url=tcAva(url);   /* only our own avatars bucket (security-pass2, 2026-10-15) */
  if(url)return '<span class="pl-face"><img src="'+attr(url)+'" alt="" loading="lazy" referrerpolicy="no-referrer"></span>';""")
one("""    var img = f.avatar_url ? '<img src="' + esc(f.avatar_url) + '" alt="" loading="lazy" onerror="this.outerHTML=NOPH_SVG">' : NOPH_SVG;
    return '<span class="rg-face" style="background:' + (f.avatar_url ? esc(bg) : 'var(--nophoto)') + '" aria-hidden="true">' + img + '</span>';""",
    """    var _au = tcAva(f.avatar_url);   /* only our own avatars bucket (security-pass2, 2026-10-15) */
    var img = _au ? '<img src="' + esc(_au) + '" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.outerHTML=NOPH_SVG">' : NOPH_SVG;
    return '<span class="rg-face" style="background:' + (_au ? esc(bg) : 'var(--nophoto)') + '" aria-hidden="true">' + img + '</span>';""")
one("""(f.avatar_url ? '<img src="' + esc(f.avatar_url) + '" alt="" loading="lazy" onerror="this.outerHTML=NOPH_SVG" style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block">' : NOPH_SVG)""",
    """(tcAva(f.avatar_url) ? '<img src="' + esc(tcAva(f.avatar_url)) + '" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.outerHTML=NOPH_SVG" style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block">' : NOPH_SVG)""")
one("""function epAvatarUrlFor(prof){
  var u=prof&&prof.avatar_url;
  return u?String(u):'';
}""",
    """function epAvatarUrlFor(prof){
  var u=prof&&prof.avatar_url;
  return u?tcAva(String(u)):'';   /* security-pass2 (2026-10-15) */
}""")
one("""  var url=(myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'';
  if(!url)return;
  var ok=await epImgLoads(url);""",
    """  var url=tcAva((myProfile&&myProfile.avatar_url)?String(myProfile.avatar_url):'');   /* security-pass2 (2026-10-15) */
  if(!url)return;
  var ok=await epImgLoads(url);""")

# ================================================================ 5. escaping
one("""function escapeHtml(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}""",
    """function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}   /* ' added 2026-10-15 (security-pass2): a single-quoted attribute can no longer be broken out of */""")
one("""function escAcc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}""",
    """function escAcc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}   /* ' added 2026-10-15 (security-pass2) */""")
# HTML-escape THEN backslash-escape no longer works once ' is an entity (the browser turns &#39; back into ' before the JS runs)
one("""  var esc=escapeHtml(email).replace(/'/g,"\\\\'");""",
    """  var esc=jsAttr(email);   /* was escapeHtml(email).replace(/'/g,"\\\\'"): with ' now an entity that order breaks out of the string (security-pass2, 2026-10-15) */""")
# the id PolyRatings hands us becomes a PROFESSORS key that is printed into handlers and attributes: keep it plain
one("""function slugPR(uuid){return 'pr_'+String(uuid).replace(/-/g,'');}""",
    """/* PolyRatings is a third party and this id is printed into handlers and attributes all over the page, so it keeps only
   plain characters. A real uuid is unchanged. (security-pass2, 2026-10-15) */
function slugPR(uuid){return 'pr_'+String(uuid).replace(/-/g,'').replace(/[^A-Za-z0-9_]/g,'');}""")
# what PolyRatings sends is text for people to read: no markup characters, a sane length, numbers that are numbers
one(r"""    list.forEach(p=>{
      if(!p||typeof p.overallRating!=='number')return;
      const id=slugPR(p.id);
      PROFESSORS[id]={name:((p.firstName||'')+' '+(p.lastName||'')).trim()||'Instructor',dept:p.department,field:p.department,
        rating:+p.overallRating,evals:p.numEvals||0,live:true,courses:Array.isArray(p.courses)?p.courses:[],prId:p.id};
      (PR_LIVE_DEPT[p.department]=PR_LIVE_DEPT[p.department]||[]).push(id);
    });""",
    r"""    list.forEach(p=>{
      if(!p||typeof p.overallRating!=='number')return;
      const id=slugPR(p.id);
      /* security-pass2 (2026-10-15): a department, a name and a course are labels. PolyRatings is a third party, so they
         lose markup characters (< > " ` and control characters) and are cut to a sane length here, once, before any
         screen can print them; the evaluation count must be a number. */
      const dep=prText(p.department,40), nm=prText((prText(p.firstName)+' '+prText(p.lastName)).trim(),80)||'Instructor';
      PROFESSORS[id]={name:nm,dept:dep,field:dep,
        rating:+p.overallRating,evals:(isFinite(+p.numEvals)?+p.numEvals:0)||0,live:true,courses:(Array.isArray(p.courses)?p.courses:[]).map(c=>prText(c,40)).filter(Boolean),prId:p.id};
      (PR_LIVE_DEPT[dep]=PR_LIVE_DEPT[dep]||[]).push(id);
    });""")
one(r"""function applyPolyList(list,fromCache){""",
    r"""function prText(s,n){ return String(s==null?'':s).replace(/[<>"`\u0000-\u001f\u007f]/g,'').replace(/\s+/g,' ').trim().slice(0,n||80); }   /* security-pass2 (2026-10-15) */
function applyPolyList(list,fromCache){""")
# two department labels that printed it raw
one("""<div class="pd">${profDeptLabel(p)}${p.reviews!=null""", """<div class="pd">${escapeHtml(profDeptLabel(p))}${p.reviews!=null""")
one("""<div class="mc-name">${pdept(p)||p.dept||''}</div><div class="mc-sub">${nrev}</div>""", """<div class="mc-name">${escapeHtml(pdept(p)||p.dept||'')}</div><div class="mc-sub">${nrev}</div>""")
# the rating form's course list
one("""courses.map(c=>`<option ${d.course===c?'selected':''}>${c}</option>`).join('')""",
    """courses.map(c=>`<option ${d.course===c?'selected':''}>${escapeHtml(c)}</option>`).join('')""")
# professor ids in handlers
one("""onclick="event.stopPropagation();openProf(\\''+q.pid+'\\')">'+escapeHtml(q.name)""",
    """onclick="event.stopPropagation();openProf(\\''+jsAttr(q.pid)+'\\')">'+escapeHtml(q.name)""")
one("""onclick="event.stopPropagation();openProf(\\''+s.pid+'\\')" style="cursor:pointer">""",
    """onclick="event.stopPropagation();openProf(\\''+jsAttr(s.pid)+'\\')" style="cursor:pointer">""")
one("""data-surface="explore" onclick="openProf('${id}')">${watchBtn(id)}""",
    """data-surface="explore" onclick="openProf('${jsAttr(id)}')">${watchBtn(id)}""")
one("""onclick="rfStartOver('${id}')">Start over""", """onclick="rfStartOver('${jsAttr(id)}')">Start over""")
one("""onclick="submitRate('${id}')">""", """onclick="submitRate('${jsAttr(id)}')">""")
one("""onclick="closeMyReviews();openProf(\\''+id+'\\')" style="cursor:pointer\"""",
    """onclick="closeMyReviews();openProf(\\''+jsAttr(id)+'\\')" style="cursor:pointer\"""")
one("""onclick="rlOpenProf('${id}','${jsAttr(code||'')}')\"""", """onclick="rlOpenProf('${jsAttr(id)}','${jsAttr(code||'')}')\"""")
one("""onclick="toggleWatch('${id}',event)">${on?WL_ON:WL_OFF}""", """onclick="toggleWatch('${jsAttr(id)}',event)">${on?WL_ON:WL_OFF}""")
one("""onclick="toggleWatch('${id}',event)">&times;""", """onclick="toggleWatch('${jsAttr(id)}',event)">&times;""")
one("""<div class="pcmp-nm" onclick="openProf(\\''+s.id+'\\')">""", """<div class="pcmp-nm" onclick="openProf(\\''+jsAttr(s.id)+'\\')">""")
one("""onclick="openProf(\\''+s.id+'\\')">View profile →""", """onclick="openProf(\\''+jsAttr(s.id)+'\\')">View profile →""")
one("""onclick="wpToggleCompare(\\''+s.id+'\\',event)">Remove from compare""", """onclick="wpToggleCompare(\\''+jsAttr(s.id)+'\\',event)">Remove from compare""")
one("""onclick="wpToggleCompare('${id}',event)">${on?'✓ In compare'""", """onclick="wpToggleCompare('${jsAttr(id)}',event)">${on?'✓ In compare'""")
one("""onclick="openWatchedProf('${id}')">""", """onclick="openWatchedProf('${jsAttr(id)}')">""")
one("""onclick="wpToggleCompare('${id}',event)">✕""", """onclick="wpToggleCompare('${jsAttr(id)}',event)">✕""")
one("""<div class="pm sec" onclick="openProf('${profs[0]}')" style="margin-top:4px">""", """<div class="pm sec" onclick="openProf('${jsAttr(profs[0])}')" style="margin-top:4px">""")
one("""onclick="togglePlanCourse('${jsAttr(code)}','${profs[0]}','Uploaded')\"""", """onclick="togglePlanCourse('${jsAttr(code)}','${jsAttr(profs[0])}','Uploaded')\"""")
one("""<div class="pm" onclick="openProf('${r.profId}')">""", """<div class="pm" onclick="openProf('${jsAttr(r.profId)}')">""")
one("""<div class="pm sec" onclick="openProf('${profId}')">""", """<div class="pm sec" onclick="openProf('${jsAttr(profId)}')">""")
one("""onclick="togglePlanCourse('${jsAttr(code)}','${profId}','${term}')\"""", """onclick="togglePlanCourse('${jsAttr(code)}','${jsAttr(profId)}','${jsAttr(term)}')\"""")
one("""<div class="pm sec" onclick="openProf('${o.prof}')">""", """<div class="pm sec" onclick="openProf('${jsAttr(o.prof)}')">""")
one("""<span class="ge-prof" onclick="openProf('${c.prof}')">""", """<span class="ge-prof" onclick="openProf('${jsAttr(c.prof)}')">""")
one("""onclick="startRate('${pid}','${jsAttr(h.code)}')">Rate ★""", """onclick="startRate('${jsAttr(pid)}','${jsAttr(h.code)}')">Rate ★""")

# ================================================================ 6. the session fallback cookie
one("""          /* a year, refreshed on every write; Secure everywhere but a local file/http test page */
          document.cookie=k+'='+encodeURIComponent(v)+'; path=/; max-age=31536000; SameSite=Lax'
            +(location.protocol==='https:'?'; Secure':'');""",
    """          /* a week (was a year), refreshed on every write; Secure and SameSite=Strict, so it is never sent in the clear
             or with a request another site starts (security-pass2, 2026-10-15). Only used when localStorage throws. */
          document.cookie=k+'='+encodeURIComponent(v)+'; path=/; max-age=604800; Secure; SameSite=Strict';""")
one("""        try{ document.cookie=k+'=; path=/; max-age=0; SameSite=Lax'+(location.protocol==='https:'?'; Secure':''); }catch(e){}""",
    """        try{ document.cookie=k+'=; path=/; max-age=0; Secure; SameSite=Strict'; }catch(e){}""")

# ================================================================ 7. share links: unchanged, the comment says why
one("""/* A random name, not the account id. The image URL travels inside a link that gets forwarded, and
   a user id in it would be an identifier handed to everyone down the chain for nothing. */""",
    """/* A random name, not the account id. The image URL travels inside a link that gets forwarded, and
   a user id in it would be an identifier handed to everyone down the chain for nothing.
   (This is about the IMAGE'S NAME. The link itself still carries &add=<your id> on purpose: that is the invite token
   the landing's "Add <name>" button needs, the same id the QR and /invite?add= links carry. Reviewed 2026-10-15, kept.) */""")

# ================================================================ 8. analytics: a click is named by id / data-ev / tag, never by text
one("""   In preference order: an explicit data-ev label (stable across redesigns, which a CSS path is
   not), then an id, then a role with its own short text. Text is trimmed hard — a label, never a
   sentence, and never anything a student typed. */""",
    """   In preference order: an explicit data-ev label (stable across redesigns, which a CSS path is
   not), then an id, then the element's tag name. NEVER its text, aria-label or value (security-pass2, 2026-10-15):
   a button's label can be a friend's name and an input's value is whatever was typed. */""")
one("""      var kind = (n.tagName || '').toLowerCase();
      var label = (n.getAttribute('aria-label') || n.value || n.textContent || '').replace(/\\s+/g,' ').trim();
      return (kind + (label ? ':' + label.slice(0,40) : '')).slice(0,60);""",
    """      return (n.tagName || '').toLowerCase().slice(0,60);""")
one("""     · `target` and `last` — evTargetName() falls back to an element's own text, so a tap on a
       professor card is legitimately "a:Jim Mueller" in our own table. Handing that to Google
       would build the professor history by the back door, one button label at a time. GA gets
       the event and the surface it happened on, which is what the question "where do people rage
       click" actually needs.""",
    """     · `target` and `last` — evTargetName() names a click by data-ev, id or tag (it used to fall back to the
       element's own text, 2026-10-15), and an id can still be specific, so these stay out of GA. GA gets
       the event and the surface it happened on, which is what the question "where do people rage
       click" actually needs.""")

# ================================================================ 9. the build stamp
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
