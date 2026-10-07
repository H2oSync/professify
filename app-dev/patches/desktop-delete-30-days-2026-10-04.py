#!/usr/bin/env python3
r"""The website's Delete account works like the phone's: 30 days to recover (2026-10-04).

Tate (2026-10-04): "only the one way delete account and you have 30 days to recover". The phone has
done that since 16:45; the website still deleted at once (delete_my_account()) and had no Recover
screen, so someone pending who signed in on termchamp.com saw their account as normal and lost it
at day 30 anyway. Now:
  · Settings › Delete account says 30 days; the dialog has the same "Keep my reviews up
    anonymously" switch (on by default; shown whenever there are reviews or we couldn't count).
  · Delete my account → request_account_deletion(p_delete_reviews). The photo goes through the
    Storage API (twice at most), the link is cleared only once it's really gone, every device is
    signed out (global), and the page says until when it can be recovered.
  · Signing in while pending → "Recover your account?" over everything (no way past it but Recover
    my account or Sign out). Recover → cancel_account_deletion(), then the page reloads.
  · If the check can't be made (offline, or the SQL isn't there) the site works as before.

Usage: python3 desktop-delete-30-days-2026-10-04.py <repo-dir>. Edits index.html only.
"""
import sys, os
p = os.path.join(sys.argv[1], 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b, label):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    s = s.replace(a, b)

# 1. Settings card
rep("""          <p class="st-note">Removes your profile, classes, sections, past classes, friends, messages and blocks.
            <b>Your reviews stay up</b>, permanently unlinked from you — delete any you want gone <em>before</em> you close the account.
            Permanent, with no undo and no export.</p>""",
    """          <p class="st-note">Other students stop seeing your account at once. After <b>30 days</b> your profile, classes, sections,
            past classes, friends, messages and blocks are permanently deleted — sign in before then to recover it.
            You choose whether your reviews stay up with no name on them, or go with it.</p>""",
    'settings-note')

# 2. The dialog
rep("""    <h3>Delete your account?</h3>
    <div class="d">This can't be undone. Here's exactly what gets removed:</div>""",
    """    <h3>Delete your account?</h3>
    <div class="d">Other students stop seeing it right away. After <b>30 days</b> it's permanently deleted, with everything below — sign in before then to recover it.</div>""",
    'dialog-lead')
rep(""".del-keep button{background:none;border:0;padding:0;margin-top:7px;font:inherit;font-size:12.5px;""",
    """.del-keep .dk-sw{display:flex;gap:9px;align-items:flex-start;cursor:pointer}
  .del-keep .dk-sw input{margin-top:3px;width:16px;height:16px;accent-color:var(--accent);flex:none}
  .del-keep button{background:none;border:0;padding:0;margin-top:7px;font:inherit;font-size:12.5px;""",
    'css')
rep("""  if(keep&&n.reviews){
    var one=(n.reviews===1);
    keep.innerHTML='<span class="dk-h">Your '+n.reviews+' review'+(one?'':'s')+' stay'+(one?'s':'')+', without your name</span>'
      +'Other students are using '+(one?'it':'them')+', and '+(one?'it\\u2019s':'they\\u2019re')+' already part of the '
      +'professor'+(one?'\\u2019s':'s\\u2019')+' average. We remove the link to you, so afterwards nothing connects '
      +(one?'it':'them')+' to you — which also means <b>'+(one?'it':'they')+' can\\u2019t be edited or taken down later</b>.'
      +'<br><button type="button" onclick="closeDeleteAccount();openMyReviews()">Delete '+(one?'it':'them')+' first instead →</button>';
  }
  if(warn){
    warn.innerHTML='Everything in the list above is gone for good the moment you confirm. '
      +'There is no undo and no backup we can restore from.';
  }""",
    """  /* 30 days to recover (2026-10-04): the reviews are a choice, as on the phone — keep them up with no
     name (on by default), or delete them with the account. Shown whenever there are reviews, or
     when we couldn't count them (a choice is never hidden because a count failed). */
  if(keep&&n.reviews!==0){
    var one=(n.reviews===1), what=n.reviews==null?'my reviews':(one?'my review':'my '+n.reviews+' reviews');
    keep.innerHTML='<label class="dk-sw"><input type="checkbox" id="delKeepRev" checked onchange="delKeepLine()">'
      +'<span><span class="dk-h">Keep '+what+' up anonymously</span><span id="delKeepLine"></span></span></label>';
    delKeepLine();
  }
  if(warn){
    warn.innerHTML='You have 30 days to change your mind: sign in and choose <b>Recover my account</b>. '
      +'After that it\\u2019s gone for good. We email you when you ask and again when it\\u2019s done.';
  }""",
    'dialog-keep')
rep("""window.closeDeleteAccount=function(){""",
    """window.delKeepLine=function(){
  var cb=document.getElementById('delKeepRev'), el=document.getElementById('delKeepLine'); if(!el)return;
  el.innerHTML=(!cb||cb.checked)
    ? 'They stay up for other students with no name on them. Nothing links them to you afterwards, so they <b>can\\u2019t be edited or removed later</b>.'
    : 'They\\u2019re deleted along with your account.';
};
window.closeDeleteAccount=function(){""",
    'keep-line')

# The review count: reviews can't be read with select('*') (user_id isn't granted), so the old count
# always failed live; my_reviews() is how the site reads your own reviews.
rep("""    n.reviews=await q('reviews');""",
    """    try{ var mr=await sb.rpc('my_reviews'); n.reviews=(mr&&!mr.error&&Array.isArray(mr.data))?mr.data.length:null; }catch(e){ n.reviews=null; }""",
    'review-count')

# 3. Asking for the deletion
rep("""  var uid=sbUser.id;
  /* Storage isn't reachable from SQL, so the photo goes first. A failure here must not stop
     the deletion — an orphaned image is a far smaller problem than an account that says it
     deleted itself and didn't. */
  try{ await sb.storage.from('avatars').remove([uid+'/avatar.jpg']); }catch(e){}
  var r;
  try{ r=await sb.rpc('delete_my_account'); }
  catch(e){ r={error:{message:(e&&e.message)||'network error'}}; }""",
    """  var uid=sbUser.id;
  var cb=document.getElementById('delKeepRev'), delRev=!!(cb&&!cb.checked);
  /* 30 days to recover (2026-10-04): nothing is deleted now; the database's nightly job deletes it
     after the 30 days (sql/professify-delete-account-30-days.sql). */
  var r;
  try{ r=await sb.rpc('request_account_deletion',{p_delete_reviews:delRev}); }
  catch(e){ r={error:{message:(e&&e.message)||'network error'}}; }
  if(r&&!r.error){
    /* The photo goes now, through the Storage API (SQL can't delete Storage files). Best effort,
       never blocks; the link is cleared only once the photo is really gone. */
    var gone=false;
    for(var i=0;i<2&&!gone;i++){ try{ var x=await sb.storage.from('avatars').remove([uid+'/avatar.jpg']); gone=!(x&&x.error); }catch(e){} }
    if(gone){ try{ await sb.from('profiles').update({avatar_url:null}).eq('id',uid); }catch(e){} }
    /* Every device, and BEFORE this device's storage is wiped below: with the session gone first,
       supabase-js has nothing to sign out and never tells the server (the old order did that). */
    try{ await sb.auth.signOut({scope:'global'}); }catch(e){}
  }""",
    'del-call')
rep("""  try{ await sb.auth.signOut(); }catch(e){}
  try{ sessionStorage.clear(); }catch(e){}
  location.replace(location.pathname+'?deleted=1');""",
    """  try{ await sb.auth.signOut({scope:'local'}); }catch(e){}   /* (already signed out everywhere, above) */
  try{ sessionStorage.clear(); }catch(e){}
  location.replace(location.pathname+'?deleted='+encodeURIComponent(String((r&&r.data)||'1')));""",
    'del-after')
rep("""  if(/[?&]deleted=1/.test(location.search)){
    setTimeout(function(){
      /* Precise, because the previous wording ("everything on it") was no longer true once
         reviews began surviving — and a farewell message that overstates what was deleted is
         exactly the sentence someone screenshots later. */
      try{ frToast('Your account has been deleted. Any reviews you wrote are still up, no longer linked to you.',8000); }catch(e){}""",
    """  if(/[?&]deleted=/.test(location.search)){
    setTimeout(function(){
      /* 30 days to recover (2026-10-04): say until when. */
      var at=decodeURIComponent((location.search.match(/[?&]deleted=([^&]*)/)||[])[1]||'');
      try{ frToast('Your account is scheduled for deletion. Sign in before '+delDateText(at)+' to recover it.',9000); }catch(e){}""",
    'deleted-toast')

# 4. Recover on sign-in
rep("""/* The danger section only exists for a signed-in account. */""",
    """/* "Nov 3, 2026" — dates always show their year. */
window.delDateText=function(iso){
  var d=/^\\d{4}-\\d\\d-\\d\\d/.test(String(iso||''))?new Date(iso):null;
  return d&&!isNaN(d)?d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}):'the end of the 30 days';
};
/* Signed in while the account is being deleted: one question, over everything, before anything
   else is used. Couldn't tell (offline, or the SQL isn't there): the site works as before. */
window.checkPendingDeletion=async function(tries){
  if(typeof sb==='undefined'||!sb||typeof sbUser==='undefined'||!sbUser)return;
  tries=tries||0;
  var r; try{ r=await sb.rpc('my_account_deletion'); }catch(e){ r={error:{message:'network'}}; }
  if(!r||r.error){
    /* couldn't tell: ask again a little later (a function that isn't there yet stops asking) */
    if(r&&r.error&&/PGRST202|42883/.test(String(r.error.code||'')))return;
    if(tries<5)setTimeout(function(){ try{ window.checkPendingDeletion(tries+1); }catch(e){} },Math.min(60000,5000*Math.pow(2,tries)));
    return;
  }
  var row=Array.isArray(r.data)?r.data[0]:r.data;
  if(row&&row.purge_after)showRecover(row.purge_after);
};
window.showRecover=function(at){
  var b=document.getElementById('recBack');
  if(!b){ b=document.createElement('div'); b.id='recBack'; b.className='pq-back'; b.style.zIndex='2147483000'; document.body.appendChild(b); }
  /* over everything (onboarding, sign-in, settings, search), and nothing behind it can be reached */
  Array.prototype.forEach.call(document.body.children,function(el){ if(el!==b&&el.id!=='frToast'&&!/toast/i.test(el.id||el.className||''))try{ el.inert=true; }catch(e){} });
  b.innerHTML='<div class="pq-dlg del-dlg" role="dialog" aria-modal="true" aria-labelledby="recH">'
    +'<h3 id="recH">Recover your account?</h3>'
    +'<div class="d">Your account is set to be permanently deleted on <b>'+escapeHtml(delDateText(at))+'</b>. Until then other students can\\u2019t see it.</div>'
    +'<div class="d" style="margin-top:8px">Recover it and everything comes back \\u2014 your classes, plans, friends and reviews \\u2014 except your profile photo, which you can add again.</div>'
    +'<div id="recErr" class="rate-err" style="min-height:0"></div>'
    +'<div class="acts"><button class="no" id="recOut" onclick="recoverSignOut()">Sign out</button>'
    +'<button class="go" id="recGo" onclick="recoverAccount()">Recover my account</button></div></div>';
  b.classList.add('open');
  setTimeout(function(){ var g=document.getElementById('recGo'); if(g)g.focus(); },60);
};
window.recoverAccount=async function(){
  var g=document.getElementById('recGo'), err=document.getElementById('recErr');
  if(!g||g.disabled)return;
  g.disabled=true; g.textContent='Recovering…'; if(err)err.textContent='';
  var r; try{ r=await sb.rpc('cancel_account_deletion'); }catch(e){ r={error:{message:(e&&e.message)||'network error'}}; }
  if(r&&r.error){
    g.disabled=false; g.textContent='Recover my account';
    if(err)err.textContent=/fetch|network|load failed/i.test(r.error.message||'')
      ? 'Couldn\\u2019t reach TermChamp \\u2014 your account is still set to be deleted. Check your connection and try again.'
      : 'Couldn\\u2019t recover your account \\u2014 it\\u2019s still set to be deleted. Try again.';
    return;
  }
  try{ sessionStorage.setItem('tc_recovered','1'); }catch(e){}
  location.reload();
};
window.recoverSignOut=async function(){
  try{ await sb.auth.signOut({scope:'local'}); }catch(e){}   /* this browser only */
  location.replace(location.pathname);
};
try{
  if(sessionStorage.getItem('tc_recovered')){
    sessionStorage.removeItem('tc_recovered');
    setTimeout(function(){ try{ frToast('Welcome back \\u2014 your account is recovered.',6000); }catch(e){} },900);
  }
}catch(e){}
/* The danger section only exists for a signed-in account. */""",
    'recover')
rep("""      if(uid&&(uid!==lastAuthUid||notLoaded)){lastAuthUid=uid;""",
    """      /* 30 days to recover (2026-10-04): asked once per signed-in account */
      if(uid&&window._pdAsked!==uid){window._pdAsked=uid;setTimeout(function(){try{if(typeof window.checkPendingDeletion==='function')window.checkPendingDeletion();}catch(_e){}},0);}
      if(!uid)window._pdAsked=null;
      if(uid&&(uid!==lastAuthUid||notLoaded)){lastAuthUid=uid;""",
    'auth-hook')

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
