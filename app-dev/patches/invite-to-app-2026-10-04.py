#!/usr/bin/env python3
r"""An invite from the phone app opens the phone app (Tate, 2026-10-04): "right now on the app
https://termchamp.com/invite?add=<id> takes them just to termchamp.com not to sign up for the app …
or termchamp.com/app".

  · The phone's invite link (QR and Share) is /invite?add=<id>&to=app. /invite keeps its preview
    card for iMessage and the rest; invite.html then sends the person to /app/?add=<id> — for a
    to=app link, and for ANY invite opened on a phone (the phone app is TermChamp on a phone). An
    invite opened on a computer still goes to the website (/?add=<id>), as before.
  · The phone app keeps the invite (localStorage, 14 days) until the person is signed in, so it
    survives sign-up: the landing says "<Name> invited you to TermChamp", and once they're in,
    a friend request goes to whoever invited them (the website's rule: a request, not an
    auto-accept). If that person had already sent them one, it's accepted instead. Already
    friends, already asked, blocked, or your own link: nothing is sent.

Usage: python3 invite-to-app-2026-10-04.py <repo-dir>. Edits app/index.html and invite.html.
"""
import sys, os
root = sys.argv[1]
pa, pi = os.path.join(root, 'app', 'index.html'), os.path.join(root, 'invite.html')
A = open(pa, encoding='utf-8').read(); I = open(pi, encoding='utf-8').read()

def rep(which, a, b, label):
    global A, I
    s = A if which == 'a' else I
    n = s.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    s = s.replace(a, b)
    if which == 'a': A = s
    else: I = s

# 1. The link
rep('a', """function inviteUrl() { return String(WEB || '').replace(/\\/+$/, '') + (TC.user ? '/invite?add=' + encodeURIComponent(TC.user.id) : '/'); }""",
    """/* to=app (2026-10-04): invite.html sends the friend to the phone app, not the website. */
function inviteUrl() { return String(WEB || '').replace(/\\/+$/, '') + (TC.user ? '/invite?add=' + encodeURIComponent(TC.user.id) + '&to=app' : '/app/'); }""",
    'invite-url')

# 2. Keep the invite until signed in; say who it's from on the landing
rep('a', """const TC_GONE = (() => {""",
    """/* An invite (/app/?add=<id>, 2026-10-04): kept until this person is signed in, 14 days at most, so it
   survives sign-up. The id leaves the address bar at once. */
const INVITE_KEY = 'tc_pending_add', UUID_OK = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function pendingInvite() { try { const v = JSON.parse(localStorage.getItem(INVITE_KEY) || 'null'); return v && UUID_OK.test(String(v.id || '')) && Date.now() - (+v.at || 0) < 14 * 864e5 ? String(v.id).toLowerCase() : ''; } catch (e) { return ''; } }
(() => { try { const q = new URLSearchParams(location.search), id = q.get('add') || q.get('ref') || q.get('invite');
  if (id && UUID_OK.test(id)) { localStorage.setItem(INVITE_KEY, JSON.stringify({ id: id.toLowerCase(), at: Date.now() })); q.delete('add'); q.delete('ref'); q.delete('invite'); history.replaceState(null, '', location.pathname + (String(q) ? '?' + q : '') + location.hash); }
} catch (e) {} })();
/* who invited you, for the landing (get_inviter is open to signed-out visitors) */
TC.inviter = null;
async function loadInviter() {
  const id = pendingInvite(); if (!id || TC.inviter !== null) return;
  TC.inviter = '';
  try { const r = await TC.client().rpc('get_inviter', { ref: id }); const row = r && !r.error ? (Array.isArray(r.data) ? r.data[0] : r.data) : null; TC.inviter = (row && row.display_name) || ''; } catch (e) {}
  /* the sign-in screens keep their own DOM while you type, so the line is filled in place */
  const el = document.querySelector('.tc-invited'); if (el && TC.inviter) el.textContent = TC.inviter + ' invited you to TermChamp. Sign up and you’ll be connected.';
}
/* Signed in: a friend request to whoever invited you — the website's rule (a request, not an
   auto-accept). Theirs to you already waiting: accepted. Nothing for friends, a request already
   sent, someone you blocked, or your own link. */
TC.processInvite = async function () {
  const id = pendingInvite();
  try { localStorage.removeItem(INVITE_KEY); } catch (e) {}
  if (!id || !TC.user || id === TC.user.id || isBlocked(id)) return;
  const rel = TC.relation(id);
  if (rel === 'friends' || rel === 'sent') return;
  let name = (PEOPLE[id] && PEOPLE[id].short) || '';
  if (!name) { try { const r = await TC.client().rpc('get_inviter', { ref: id }); const row = r && !r.error ? (Array.isArray(r.data) ? r.data[0] : r.data) : null; name = row && row.display_name ? String(row.display_name).split(/\\s+/)[0] : ''; } catch (e) {} }
  if (rel === 'incoming') { if (await TC.acceptRequest(id)) toast(`You and ${name || 'your friend'} are now friends`); render(true); return; }
  if (await TC.sendRequest(id)) { toast(name ? `Friend request sent to ${name} — you’re friends once they accept` : 'Friend request sent — you’re friends once they accept'); render(true); }
};
const TC_GONE = (() => {""",
    'pending')
rep('a', """TC_GONE ? `<div class="hint ok" role="status" style="justify-content:center;text-align:center">Your account is scheduled for deletion. Sign in before ${esc(delDate(TC_GONE))} to recover it.</div>` : ''}""",
    """TC_GONE ? `<div class="hint ok" role="status" style="justify-content:center;text-align:center">Your account is scheduled for deletion. Sign in before ${esc(delDate(TC_GONE))} to recover it.</div>` : pendingInvite() ? `<div class="hint ok tc-invited" role="status" style="justify-content:center;text-align:center">${TC.inviter ? esc(TC.inviter) + ' invited you to TermChamp.' : 'You’re invited to TermChamp.'} Sign up and you’ll be connected.</div>` : ''}""",
    'landing')
rep('a', """function onbSignin() {
  const si = UI.signin;""",
    """function onbSignin() {
  const si = UI.signin;
  if (pendingInvite() && TC.inviter === null && TC.client()) setTimeout(loadInviter, 0);""",
    'landing-load')
rep('a', """  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);""",
    """  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);
  if (pendingInvite()) TC.processInvite().catch(() => {});""",
    'after-load')

# 3. invite.html: to=app, or a phone → the phone app
rep('i', """  var out='/';
  try{
    var q=new URLSearchParams(location.search);
    var id=q.get('add')||q.get('ref')||q.get('invite');
    if(id&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))
      out='/?add='+encodeURIComponent(id);
  }catch(e){}""",
    """  /* WHICH APP (2026-10-04): an invite sent from the phone app (to=app), or any invite opened on a
     phone, goes to the phone app at /app/ — that is TermChamp on a phone, with sign-up built in.
     On a computer it goes to the website, as before. */
  var out='/', app=false;
  try{
    var q=new URLSearchParams(location.search);
    var ua=navigator.userAgent||'';
    app=q.get('to')==='app'||/iPhone|iPod|Android.+Mobile|Mobile.+Android/i.test(ua)
      ||(/iPad|Macintosh/.test(ua)&&navigator.maxTouchPoints>1&&Math.min(screen.width,screen.height)<700);
    out=app?'/app/':'/';
    var id=q.get('add')||q.get('ref')||q.get('invite');
    if(id&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))
      out=(app?'/app/?add=':'/?add=')+encodeURIComponent(id);
  }catch(e){}""",
    'invite-html')

open(pa, 'w', encoding='utf-8').write(A); open(pi, 'w', encoding='utf-8').write(I)
print('patched', pa, pi)
