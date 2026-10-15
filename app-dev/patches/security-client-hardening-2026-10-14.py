#!/usr/bin/env python3
"""Client hardening from the defensive configuration review of termchamp.com (2026-10-14). index.html + sw.js only.

1. An invite link no longer WRITES without a tap.
   Opening /?add=<uuid> (aliases ?ref=, ?invite=), a QR landing, or a shared-schedule landing (?sched= / ?i= with
   &add=) stashed the id, and after sign-in processPendingAdd() called sendFriendRequest() with nothing asked: a
   link in a group chat was enough to make someone's account send a friend request to a stranger. Worse, the
   shared-schedule landing prints a name taken from the URL itself (?nm=), so "Add Mom" could carry anyone's id.
   Now the stashed id raises a confirm card, "Add <name>?" with Add / Not now. The name is fetched read-only with
   get_inviter (the same RPC the signed-out landing uses; it returns the profile's own display_name, not the URL's)
   and falls back to "this person". friend_requests is written on the Add tap and only there. Not now clears it.
   Closing the card any other way (backdrop, Escape) does not answer it: the id is kept, with a timestamp, for 14
   days or until answered, and the card comes back the next time the page is opened signed in. The stash now lives in
   sessionStorage (as before, key professify_pending_add) AND localStorage, because the sign-in email opens in a new
   tab and sessionStorage does not follow it. Someone you are already friends with or have already asked is not
   asked about again. The card waits for the onboarding sheet or any other open sheet instead of stacking on it.
   The invite flow is otherwise untouched: copy, QR, inviter lookup, the signed-out welcome.
2. pdf.js getDocument() gets isEvalSupported:false (font programs are not compiled with new Function()). pdf.js is
   still 3.11.174; the version is NOT changed here (3.11.174 predates the CVE-2024-4367 fix in 4.2.67, and
   isEvalSupported:false is the documented mitigation for it).
3. lazyScript() takes a Subresource Integrity hash; it sets integrity + crossorigin="anonymous". The three scripts
   it loads are pinned to exact versions and hashed (sha384 of the file in the npm tarball, which is what jsDelivr
   serves at /npm/<pkg>@<ver>/<path>):
     tesseract.js@5.1.1  dist/tesseract.min.js            (was the floating tesseract.js@5; 5.1.1 is the newest 5.x)
     pdfjs-dist@3.11.174 legacy/build/pdf.min.js
     qrcode-generator@1.4.4 qrcode.js
   NOT covered by SRI because the browser fetches them, not a <script> tag: pdf.js's worker (pdf.worker.min.js) and
   Tesseract's own worker, wasm core and language data.
4. sw.js: a push payload's url was accepted when it merely started with "/", and "//other.host" does. It is now
   resolved with new URL(u, origin) and used only when the origin is ours; anything else opens "/". The same guard
   runs again when the notification is clicked.

Usage: python3 security-client-hardening-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
sw = root / 'sw.js'
s = f.read_text()
w = sw.read_text()
if 'security-client-hardening (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

def one_sw(old, new):
    global w
    n = w.count(old)
    assert n == 1, (n, old[:120])
    w = w.replace(old, new)

# ================================================================ 1. the stash: one helper, three writers, one reader
one("""        var _pend=(typeof sessionStorage!=='undefined')&&sessionStorage.getItem('professify_pending_add');""",
    """        var _pend=(typeof pendAddGet==='function')?pendAddGet():((typeof sessionStorage!=='undefined')&&sessionStorage.getItem('professify_pending_add'));""")
one("""  try{sessionStorage.setItem('professify_pending_add',id);}catch(e){}
  // Clean the URL so a refresh doesn't re-trigger it.""",
    """  pendAddSet(id);   /* security-client-hardening (2026-10-14): stashed with a date; asked about, never sent */
  // Clean the URL so a refresh doesn't re-trigger it.""")
one("""  if(addId&&typeof UUID_RE!=='undefined'&&UUID_RE.test(addId)){ try{sessionStorage.setItem('professify_pending_add',addId);}catch(e){} }""",
    """  if(addId&&typeof UUID_RE!=='undefined'&&UUID_RE.test(addId)){ pendAddSet(addId); }   /* kept, then ASKED about after sign-in (security-client-hardening 2026-10-14) */""")
one("""  try{sessionStorage.setItem('professify_pending_add',id);}catch(e){}
  try{history.replaceState({},'',location.pathname);}catch(e){}   // clean ?add= from the URL""",
    """  pendAddSet(id);   /* security-client-hardening (2026-10-14): stashed with a date; asked about, never sent */
  try{history.replaceState({},'',location.pathname);}catch(e){}   // clean ?add= from the URL""")
# the signed-out welcome is marked so that, once signed in, only IT is closed to make room for the card
one("""  modal.innerHTML='<div class="rate-wrap"><div class="rate-step">'
    +'<div class="rate-kicker">'+(known?('Invite from '""",
    """  modal.innerHTML='<div class="rate-wrap" data-invite-landing="1"><div class="rate-step">'
    +'<div class="rate-kicker">'+(known?('Invite from '""")

# ================================================================ 1. the confirm card replaces the silent send
one("""async function processPendingAdd(){
  if(!backendReady()||!sbUser)return;
  let id=null;
  try{id=sessionStorage.getItem('professify_pending_add');}catch(e){}
  if(!id||!UUID_RE.test(id)||id===sbUser.id){
    try{sessionStorage.removeItem('professify_pending_add');}catch(e){}
    return;
  }
  try{sessionStorage.removeItem('professify_pending_add');}catch(e){}
  // Opening an invite link auto-SENDS a friend request to the inviter (so the
  // invitee never has to search/add them) — but it stays pending until the
  // inviter approves it. Not an auto-accept.
  await sendFriendRequest(id);
  show('friends');
  const area=document.getElementById('frQrArea');
  if(area){area.style.display='';area.innerHTML='<p class="fr-mut" style="color:#6f9e6a;text-align:center;padding:14px">Friend request sent ✓</p>';setTimeout(closeQrArea,2500);}
}
""", r"""/* ---- a pending invite (security-client-hardening, 2026-10-14) ---------------------------------
   An invite link used to be a WRITE: stash the id, sign in, and processPendingAdd() sent the friend request with
   nothing asked. Now the id is only ever ASKED about: a card says "Add <name>?" and friend_requests is written on
   the Add tap and nowhere else. The id is kept, with the day it arrived, until it is answered or 14 days pass.
   sessionStorage keeps the key the site has always used; localStorage is added because the sign-in email opens in
   a new tab, which sessionStorage does not follow. */
function pendAddStores(){
  var out=[];
  try{ if(window.sessionStorage)out.push(window.sessionStorage); }catch(e){}
  try{ if(window.localStorage)out.push(window.localStorage); }catch(e){}
  return out;
}
function pendAddSet(id){
  if(!id||!UUID_RE.test(id))return;
  var now=String(Date.now());
  pendAddStores().forEach(function(st){ try{ st.setItem('professify_pending_add',id); st.setItem('professify_pending_add_at',now); }catch(e){} });
}
function pendAddClear(){
  pendAddStores().forEach(function(st){ try{ st.removeItem('professify_pending_add'); st.removeItem('professify_pending_add_at'); }catch(e){} });
}
function pendAddGet(){
  var TTL=14*86400000, found=null;
  pendAddStores().forEach(function(st){
    if(found)return;
    try{
      var id=st.getItem('professify_pending_add'); if(!id)return;
      var at=+st.getItem('professify_pending_add_at');
      if(!at){ at=Date.now(); st.setItem('professify_pending_add_at',String(at)); }   /* stashed before this date existed: it starts now */
      if(!UUID_RE.test(id)||Date.now()-at>TTL){ st.removeItem('professify_pending_add'); st.removeItem('professify_pending_add_at'); return; }
      found=id;
    }catch(e){}
  });
  return found;
}
function pendAddCardOpen(id){
  var mb=document.getElementById('mback'), el=document.querySelector('#modal [data-pendadd]');
  return !!(mb&&mb.classList.contains('open')&&el&&(!id||el.getAttribute('data-pendadd')===id));
}
function pendAddBlocked(){
  var ob=document.getElementById('onboard'), mb=document.getElementById('mback');
  if(ob&&ob.style.display==='flex')return true;
  if(window._schedLandingOpen)return true;                               /* the shared-schedule page is above the sheet: its own button asks */
  var rb=document.getElementById('recBack'); if(rb&&rb.classList.contains('open'))return true;   /* Recover your account? comes first */
  return !!(mb&&mb.classList.contains('open')&&!pendAddCardOpen());
}
/* The sheet is in the way (onboarding, a profile, a rating): look again in a moment instead of stacking on it. */
function pendAddLater(){
  if(window._pendAddWait||(window._pendAddTries=(window._pendAddTries||0)+1)>400)return;
  window._pendAddWait=setTimeout(function(){ window._pendAddWait=0; try{ processPendingAdd(); }catch(e){} },1500);
}
function pendAddPaint(id,name){
  var modal=document.getElementById('modal'), mb=document.getElementById('mback'); if(!modal||!mb)return;
  var who=name?escapeHtml(name):'this person';
  modal.innerHTML='<div class="rate-wrap" role="dialog" aria-modal="true" aria-labelledby="pendAddH" data-pendadd="'+escapeHtml(id)+'"><div class="rate-step">'
    +'<div class="rate-kicker">Friend request</div>'
    +'<h2 class="rate-h" id="pendAddH">Add '+who+'?</h2>'
    +'<p class="rate-sub">You opened their invite link. Adding sends a friend request, and they choose whether to accept it.</p>'
    +'<div class="rate-err" id="pendAddErr" style="min-height:0"></div>'
    +'<button class="btn primary rate-submit" id="pendAddYes" type="button" onclick="pendAddAnswer(true)">Add</button>'
    +'<button class="rate-skip" id="pendAddNo" type="button" onclick="pendAddAnswer(false)">Not now</button>'
    +'</div></div>';
  mb.classList.add('open'); document.body.style.overflow='hidden';
  window._pendAddTries=0;
}
async function pendAddAnswer(yes){
  var host=document.querySelector('#modal [data-pendadd]'), id=host&&host.getAttribute('data-pendadd');
  if(!id||!UUID_RE.test(id)){ closeModal(); return; }
  if(!yes){ pendAddClear(); closeModal(); return; }                       /* Not now: answered, nothing written */
  if(window._pendAddBusy)return;
  window._pendAddBusy=true;
  var btn=document.getElementById('pendAddYes'); if(btn){ btn.disabled=true; btn.textContent='Sending…'; }
  var ok=false;
  try{ ok=await sendFriendRequest(id); }catch(e){}
  window._pendAddBusy=false;
  if(!ok){                                                                /* sendFriendRequest said why; the invite stays */
    if(btn){ btn.disabled=false; btn.textContent='Add'; }
    return;
  }
  pendAddClear();
  closeModal();
  show('friends');
  const area=document.getElementById('frQrArea');
  if(area){area.style.display='';area.innerHTML='<p class="fr-mut" style="color:#6f9e6a;text-align:center;padding:14px">Friend request sent ✓</p>';setTimeout(closeQrArea,2500);}
}
async function processPendingAdd(){
  if(!backendReady()||!sbUser)return;
  var id=pendAddGet();
  if(!id||id===sbUser.id){ pendAddClear(); return; }
  /* Someone you are already friends with, or have already asked, is not a question. */
  try{
    if(typeof peopleRelState==='function'){ var st=peopleRelState(id); if(st==='friends'||st==='sent'){ pendAddClear(); return; } }
  }catch(e){}
  if(pendAddCardOpen(id))return;
  /* Signed in now, so the signed-out welcome (Connect with ...) has nothing left to say: it must not hold the card back. */
  if(window._inviteLandingOpen){ window._inviteLandingOpen=false; if(document.querySelector('#modal [data-invite-landing]'))closeModal(); }
  if(pendAddBlocked()){ pendAddLater(); return; }
  /* The name comes from the profile (read-only RPC, the one the signed-out welcome uses), never from the link. */
  var name=null;
  try{
    var r=await withTimeout(sb.rpc('get_inviter',{ref:id}),3000,'get_inviter');
    if(r&&!r.error&&r.data){ var row=Array.isArray(r.data)?r.data[0]:r.data; if(row&&row.display_name)name=String(row.display_name).slice(0,80); }
  }catch(e){}
  if(!sbUser||pendAddGet()!==id||pendAddCardOpen(id))return;               /* answered, cleared or painted while we asked */
  if(pendAddBlocked()){ pendAddLater(); return; }
  pendAddPaint(id,name);
}
""")

# ================================================================ 2. pdf.js
one("""var doc=await lib.getDocument({data:new Uint8Array(buf),isOffscreenCanvasSupported:false}).promise;""",
    """var doc=await lib.getDocument({data:new Uint8Array(buf),isOffscreenCanvasSupported:false,isEvalSupported:false}).promise;   /* security-client-hardening (2026-10-14): no new Function() for font programs */""")

# ================================================================ 3. Subresource Integrity on lazily loaded scripts
one("""function lazyScript(src,globalName,timeoutMs){""",
    """function lazyScript(src,globalName,timeoutMs,integrity){   /* integrity: a sha384 SRI hash; the script is refused if the bytes differ (security-client-hardening 2026-10-14) */""")
one("""      el.src=src; el.async=true;
      var timer=setTimeout(function(){""",
    """      if(integrity){ el.integrity=integrity; el.crossOrigin='anonymous'; }
      el.src=src; el.async=true;
      var timer=setTimeout(function(){""")
one("""function loadOcr(){return lazyScript('https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js','Tesseract',45000);}""",
    """/* Pinned (security-client-hardening, 2026-10-14): tesseract.js@5.1.1 was what @5 resolved to; the hash is sha384 of dist/tesseract.min.js in the npm tarball.
   To bump: npm pack tesseract.js@<ver>, sha384 the file, change both. */
function loadOcr(){return lazyScript('https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js','Tesseract',45000,'sha384-GJqSu7vueQ9qN0E9yLPb3Wtpd7OrgK8KmYzC8T1IysG1bcvxvIO4qtYR/D3A991F');}""")
one("""  return lazyScript(PDFJS_BASE+'pdf.min.js','pdfjsLib',45000).then(function(lib){""",
    """  /* sha384 of pdfjs-dist@3.11.174 legacy/build/pdf.min.js (security-client-hardening, 2026-10-14). The worker is not a <script>, so SRI cannot cover it. */
  return lazyScript(PDFJS_BASE+'pdf.min.js','pdfjsLib',45000,'sha384-OemFRmhjDZwhIKuUld0HJozkF2YErsgDaCL41trxGQZt4/WgnopJQqQl2DvDZ07Z').then(function(lib){""")
one("""function loadQrGen(){return lazyScript('https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js','qrcode');}""",
    """function loadQrGen(){return lazyScript('https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js','qrcode',undefined,'sha384-8FWZA6BGMXhsfO+BLtrJK0We6gg5o1JyO8xQm6peWDEUs17ACA5ziE/NIAkl9z2k');}   /* sha384 of qrcode.js in the 1.4.4 npm tarball */""")

# ================================================================ 4. sw.js: the push click URL
one_sw("""self.addEventListener('push', (e) => {""",
       """/* security-client-hardening (2026-10-14). A push payload's url is data from outside this worker. "starts with /" also
   accepts "//other.host" (and "/\\\\other.host", which URL parsing reads the same way), so resolve it against our own
   origin and use it only when the origin is ours. Anything else, or anything that does not parse, is "/". */
function safePushUrl(u) {
  try {
    if (typeof u !== 'string' || !u) return '/';
    const x = new URL(u, self.location.origin);
    if (x.origin !== self.location.origin) return '/';
    return x.pathname + x.search + x.hash;
  } catch (_) { return '/'; }
}

self.addEventListener('push', (e) => {""")
one_sw("""    data: { url: typeof d.url === 'string' && d.url.charAt(0) === '/' ? d.url : '/' }""",
       """    data: { url: safePushUrl(d.url) }""")
one_sw("""  const target = (e.notification.data && e.notification.data.url) || '/';""",
       """  const target = safePushUrl(e.notification.data && e.notification.data.url);""")

f.write_text(s)
sw.write_text(w)
print('patched', f, sw)
