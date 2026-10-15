#!/usr/bin/env python3
"""Security fixes for the PHONE APP bundle app/index.html (termchamp.com/app, later inside the iOS app), 2026-10-15.
Ports security-client-hardening-2026-10-14.py (which did the website's index.html) and adds three app-only fixes.
Only app/index.html changes.

1. pdf.js (CVE-2024-4367): getDocument({data, isOffscreenCanvasSupported:false}) also passes isEvalSupported:false, so
   font programs in a PDF are never compiled with new Function(). pdf.js stays 3.11.174 (the documented mitigation).
   Its <script> already carries integrity + crossorigin (loadPdfJs, sha384 of legacy/build/pdf.min.js), so that part
   needed no change. The WORKER is not a script tag: pdf.js starts it from GlobalWorkerOptions.workerSrc
   (TCPL.pdfBase + 'pdf.worker.min.js'), which cannot carry an integrity hash. A comment says so. Closing that gap
   means bundling pdf.min.js + pdf.worker.min.js into the app (a build-step change, deliberately NOT done here).

2. An invite link is a question, not a write. ?add=<uuid> (aliases ?ref=, ?invite=) was stashed (INVITE_KEY) and, once
   signed in, TC.processInvite() sent the friend request with nothing asked, and ACCEPTED a request that person had
   already sent: a link in a group chat could make an account befriend a stranger, or confirm a stranger's request.
   Now it opens a sheet, "Add <name>?" with Add / Not now (name from the profile through the read-only get_inviter RPC,
   never from the link; "this person" when there is none; the sheet escapes it). friend_requests is written when Add is
   tapped and only then; if they have already sent a request, Add accepts it (the same tap). Not now clears the invite.
   Closing the sheet any other way (scrim, X) does not answer it: the id stays, up to 14 days (pendingInvite's TTL, as
   before), and the sheet is offered again the next time the app is opened signed in (once per page load, so a
   pull-to-refresh does not nag). Friends / already-asked / blocked / your own link: nothing is asked and the stash is
   dropped. The sheet waits for any other open sheet or Champ instead of stacking on it. The signed-out landing's copy
   ("Sign up and you'll be connected.") is unchanged.

3. Sign-out on a shared browser. TC.signOut only signed the session out; every per-account key stayed (tc-audit:<uid>,
   tc-commits:, tc-marks:, tc-regday:, tc-drafted:, tc-pl-nodpr:, tc-prefs:, tc-chat-pins-, tc-story-pins:,
   tc-feed-seen:, tc_champ_ai:<uid> (Champ's chat), tc_pending_add, tc_push_token, termchamp_app_* (plans, recent,
   concentration, rate drafts, onboarding), termchamp-app-v1 (UI state), professify-* (the website's profile on the shared
   origin), professify_rev_times, professify_ev_salt...). New TC.wipeDevice() removes EVERY localStorage and
   sessionStorage key that starts tc-, tc_, professify or termchamp, except the KEEP list: tc-theme (light/dark: a
   device choice), termchamp_app_seats_v1 (public seat counts cache), professify_prof_cache (public PolyRatings cache),
   and tc_deleted (the one-shot "account scheduled for deletion" note the sign-in screen reads right after a delete).
   TC.wipeDevice(true) also removes supabase-js's own sb-*-auth-token / -code-verifier keys. signOut order: push token
   forgotten (it needs its key), wipe, auth.signOut(), wipe again (anything a render wrote meanwhile, and the auth keys
   if signOut could not reach the server). TC.afterDelete does the same, and sets tc_deleted AFTER the wipe. Before this
   it kept the concentration and local plans for a recovered account; the account is recoverable from the server and the
   next sign-in re-reads what it needs.

4. Avatars. safeImg() accepted any https:// URL, so a profile's avatar_url could point an <img> at a tracking host. It
   now accepts only URLs under exactly
   https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/ (checked again after URL normalisation, so
   .. / backslash tricks cannot leave that folder) or a raster data:image (png/jpeg/webp/gif, base64). Every <img> keeps
   referrerpolicy="no-referrer" where it had it. (The edit-profile preview uses a blob: URL it made itself and does not go
   through safeImg.)

5. Auth flow. createClient had detectSessionInUrl:true and no flowType, so supabase-js used the implicit flow and signed
   in whoever opened /app/#access_token=...&refresh_token=...: a link could sign a victim into the attacker's account
   (session fixation). How /app signs in: an emailed 6-digit code typed into the page (signInWithOtp + verifyOtp
   type:'email') or email + password (signInWithPassword). Neither reads the URL. A Google redirect (signInGoogle ->
   signInWithOAuth, redirectTo /app/) exists in the code but is switched off (CFG.GOOGLE_SIGNIN_ENABLED false, no
   button). So: flowType:'pkce' (the website's setting). In supabase-js 2.112.4 an #access_token URL is still
   recognised as an implicit callback whatever flowType says, and _getSessionFromURL then REFUSES it ("Not a valid PKCE
   flow url"), so no session is made. detectSessionInUrl stays true so the dormant Google redirect keeps working if it is
   turned on: PKCE returns ?code=, which can only be exchanged by the browser that holds the matching code verifier,
   so a link cannot carry someone else's code in either. The OTP code still verifies (verifyOtp does not use the verifier).

Usage: python3 security-app-2026-10-15.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app/index.html'
s = f.read_text()
if 'security-app (2026-10-15)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ 1. pdf.js
one("""    doc = await lib.getDocument({ data: new Uint8Array(await TCPL.fileBytes(file)), isOffscreenCanvasSupported: false }).promise;""",
    """    /* security-app (2026-10-15): isEvalSupported:false = no new Function() for font programs (CVE-2024-4367) */
    doc = await lib.getDocument({ data: new Uint8Array(await TCPL.fileBytes(file)), isOffscreenCanvasSupported: false, isEvalSupported: false }).promise;""")
one("""    s.onload = () => { try { window.pdfjsLib.GlobalWorkerOptions.workerSrc = TCPL.pdfBase + 'pdf.worker.min.js'; } catch (e) {} res(window.pdfjsLib); };""",
    """    /* security-app (2026-10-15): the WORKER is started by pdf.js from workerSrc, not by a <script> tag, so it cannot carry an
       integrity hash. Closing that gap means shipping pdf.min.js + pdf.worker.min.js inside the app bundle (a build step). */
    s.onload = () => { try { window.pdfjsLib.GlobalWorkerOptions.workerSrc = TCPL.pdfBase + 'pdf.worker.min.js'; } catch (e) {} res(window.pdfjsLib); };""")

# ================================================================ 5. auth flow
one("""{ auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } });
  TC.sb.auth.onAuthStateChange(""",
    """{ auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true,
    /* security-app (2026-10-15): PKCE, like the website. The default (implicit) flow signed in anyone who opened /app/#access_token=...&refresh_token=...,
       so a link could sign a victim into the attacker's account. Sign-in here is an emailed code or a password; neither reads the URL. */
    flowType: 'pkce' } });
  TC.sb.auth.onAuthStateChange(""")

# ================================================================ 3. sign-out / delete wipe
one("""TC.signOut = async function () { await TC.pushForget(false); try { await TC.client().auth.signOut(); } catch (e) {} location.replace(location.pathname); };""",
    """/* security-app (2026-10-15): a shared browser keeps nothing of the person who just left. Every localStorage / sessionStorage key this app
   (or the website on the same origin) writes starts tc-, tc_, professify or termchamp; all of them go EXCEPT the device's own non-personal
   choices and public caches below. wipeDevice(true) also drops supabase-js's own session keys. */
const WIPE_PREFIXES = ['tc-', 'tc_', 'professify', 'termchamp'];
const WIPE_KEEP = ['tc-theme', 'termchamp_app_seats_v1', 'professify_prof_cache', 'tc_deleted'];
TC.wipeDevice = function (auth) {
  [['localStorage'], ['sessionStorage']].forEach(([w]) => {
    try {
      const st = window[w], ks = [];
      for (let i = 0; i < st.length; i++) ks.push(st.key(i));
      ks.forEach(k => {
        if (k == null || WIPE_KEEP.indexOf(k) >= 0) return;
        if (WIPE_PREFIXES.some(p => k.indexOf(p) === 0) || (auth && /^sb-.*-(auth-token|code-verifier)/.test(k))) { try { st.removeItem(k); } catch (e) {} }
      });
    } catch (e) {}
  });
};
TC.signOut = async function () { await TC.pushForget(false); TC.wipeDevice(); try { await TC.client().auth.signOut(); } catch (e) {} TC.wipeDevice(true); location.replace(location.pathname); };""")
one("""  try { [KEY, RECENT_KEY, DRAFT_KEY, ONB_KEY, 'professify_rev_times', AUDIT_KEY(), PREFS_KEY(), PLDRAFT_KEY(), plSkipKey(), MARKS_KEY(), REG_KEY()].forEach(k => localStorage.removeItem(k)); } catch (e) {}
  try { sessionStorage.setItem('tc_deleted', String(TC.purgeAt || '1')); } catch (e) {}
  try { await TC.client().auth.signOut({ scope: 'global' }); } catch (e) {}""",
    """  TC.wipeDevice();   /* security-app (2026-10-15): everything of theirs on this browser, not a hand-picked list (concentration and local plans too; the account is recoverable from the server) */
  try { sessionStorage.setItem('tc_deleted', String(TC.purgeAt || '1')); } catch (e) {}
  try { await TC.client().auth.signOut({ scope: 'global' }); } catch (e) {}
  TC.wipeDevice(true);""")

# ================================================================ 4. avatars
one("""function safeImg(u) { return /^https:\\/\\//.test(String(u || '')) ? u : ''; }""",
    """/* security-app (2026-10-15): only OUR avatars bucket (or a local raster data: preview). Any other host would let a profile's avatar_url
   make every viewer's phone fetch from a server the profile's owner chose. The check runs again on the normalised URL (../ and \\ tricks). */
const AVATAR_BASE = 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/';
function safeImg(u) {
  u = String(u || '');
  if (/^data:image\\/(png|jpe?g|webp|gif);base64,[A-Za-z0-9+\\/=]+$/.test(u)) return u;
  if (u.indexOf(AVATAR_BASE) !== 0) return '';
  try { return new URL(u).href.indexOf(AVATAR_BASE) === 0 ? u : ''; } catch (e) { return ''; }
}""")

# ================================================================ 2. the invite is a question
one("""/* Signed in: a friend request to whoever invited you — the website's rule (a request, not an
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
};""",
    """/* Signed in: an invite link is a QUESTION, never a write (security-app, 2026-10-15; the website's rule since 2026-10-14).
   A sheet asks "Add <name>?"; friend_requests is written when Add is tapped and nowhere else, and if they already asked
   you, that same tap accepts. Not now clears the invite. Closing the sheet any other way does not answer it: the id stays
   (up to 14 days, pendingInvite) and the sheet comes back the next time the app is opened. Nothing is asked for a friend,
   a request already sent, someone you blocked, or your own link. The name is the profile's own (get_inviter), not the link's. */
TC.processInvite = async function () {
  if (TC._inviteAsked || !TC.user) return;
  const id = pendingInvite(); if (!id) return;
  const drop = () => { try { localStorage.removeItem(INVITE_KEY); } catch (e) {} };
  if (id === TC.user.id || isBlocked(id)) { drop(); return; }
  const rel0 = TC.relation(id);
  if (rel0 === 'friends' || rel0 === 'sent') { drop(); return; }
  let name = '';
  try {
    const r = await Promise.race([TC.client().rpc('get_inviter', { ref: id }), new Promise(res => setTimeout(() => res(null), 3000))]);
    const row = r && !r.error ? (Array.isArray(r.data) ? r.data[0] : r.data) : null;
    if (row && row.display_name) name = String(row.display_name).slice(0, 80);
  } catch (e) {}
  if (!name && rel0 === 'incoming' && PEOPLE[id] && PEOPLE[id].name) name = String(PEOPLE[id].name).slice(0, 80);
  if (TC._inviteAsked || !TC.user || pendingInvite() !== id) return;          /* answered, cleared or asked while we looked */
  const rel = TC.relation(id);
  if (rel === 'friends' || rel === 'sent') { drop(); return; }
  if (UI.sheet || UI.champ) {                                                /* something else is open: look again in a moment, never stack on it */
    if (!TC._inviteWait && (TC._inviteTries = (TC._inviteTries || 0) + 1) <= 60) TC._inviteWait = setTimeout(() => { TC._inviteWait = 0; TC.processInvite().catch(() => {}); }, 1500);
    return;
  }
  TC._inviteAsked = true; TC._inviteTries = 0;
  UI.sheet = { type: 'inviteAsk', id, name, err: '', busy: false }; render(true);
};""")
one("""SHEETS.leaveAsk = ({ cid }) => {""",
    """/* An invite link's question (security-app, 2026-10-15): nothing is sent until Add. */
SHEETS.inviteAsk = ({ id, name, err, busy }) => {
  const who = name ? esc(name) : 'this person', inc = TC.relation(id) === 'incoming';
  return `<h3>Add ${who}?</h3>
 <div class="muted b" style="font-size:14.5px;margin:8px 0 16px;line-height:1.45">${inc ? 'They already asked to be your friend. Adding accepts it.' : 'You opened their invite link. Adding sends a friend request, and they choose whether to accept it.'}</div>
 ${err ? `<div class="tc-err" role="alert" style="margin-bottom:10px">${esc(err)}</div>` : ''}
 <div style="display:grid;gap:8px"><button class="btn" data-a="inviteAdd"${busy ? ' disabled' : ''}>${busy ? 'Adding…' : 'Add'}</button><button class="btn soft" data-a="inviteNo">Not now</button></div>`;
};
SHEETS.leaveAsk = ({ cid }) => {""")
one("""  blockGo: async uid => {""",
    """  inviteAdd: async () => {   /* the one place an invite link writes (security-app, 2026-10-15) */
    const sh = UI.sheet; if (!sh || sh.type !== 'inviteAsk' || sh.busy) return;
    const id = sh.id, rel = TC.relation(id); sh.busy = true; sh.err = ''; render(true);
    let ok = false;
    try { ok = (rel === 'friends' || rel === 'sent') ? true : rel === 'incoming' ? await TC.acceptRequest(id) : await TC.sendRequest(id); } catch (e) {}
    sh.busy = false;
    if (!ok) { if (UI.sheet === sh) { sh.err = 'Couldn’t add them. Check your connection and try again.'; render(true); } return; }   /* the invite stays */
    try { localStorage.removeItem(INVITE_KEY); } catch (e) {}
    const first = sh.name ? sh.name.split(/\\s+/)[0] : '';
    if (UI.sheet === sh) A.closeSheet(); else render(true);
    toast(rel === 'incoming' ? `You and ${first || 'your friend'} are now friends` : first ? `Friend request sent to ${first} — you’re friends once they accept` : 'Friend request sent — you’re friends once they accept');
  },
  inviteNo: () => {   /* Not now: answered, nothing written */
    try { localStorage.removeItem(INVITE_KEY); } catch (e) {}
    A.closeSheet();
  },
  blockGo: async uid => {""")

f.write_text(s)
print('patched', f)
