#!/usr/bin/env python3
r"""Delete account → 30 days to recover (Tate, 2026-10-04): "have it deleted and have it say you can
recover in 30 days" … "no i only want the one way delete account and you have 30 days to recover".

  · Delete account now asks request_account_deletion(p_delete_reviews) (sql/professify-delete-
    account-30-days.sql). The account is hidden from everyone at once and this phone signs out;
    the sign-in screen says "Your account is deleted. Sign in before <date> to recover it."
  · Signing in within 30 days opens one screen first: "Recover your account?" — Recover my account
    (cancel_account_deletion(), then the app loads as before) or Sign out. Nothing else loads first.
  · After 30 days the database's daily job deletes it for good (and the reviews if the switch was
    off). The photo is removed at once through the Storage API — SQL can't delete Storage files —
    so a recovered account comes back without it (the screens say so).
  · Signs out everywhere (scope 'global'); the pending check runs alongside the profile read, and a
    failed check on a refresh is a toast, never a lock-out.
  · Keeps the delete screen of delete-account-2026-10-04.py: what goes, the reviews switch (on =
    keep them anonymously), what's kept, type DELETE, Enter does nothing.
  · Recovering keeps what's on this phone that only lives here (the concentration, local plans).

Runs after delete-account-2026-10-04.py. Usage: python3 delete-30-days-2026-10-04.py <repo-dir>.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b, label):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    s = s.replace(a, b)

# 1. The delete screen says what actually happens now.
rep("""<div class="pad muted b" style="font-size:14.5px;line-height:1.45;margin:-4px 0 12px">This permanently deletes your TermChamp account. It can’t be undone.</div>""",
    """<div class="pad muted b" style="font-size:14.5px;line-height:1.45;margin:-4px 0 12px">Other students stop seeing your profile, classes and plans right away, and your account is permanently deleted after 30 days. Changed your mind? Sign in before then to recover it. Your profile photo is removed now.</div>""",
    'intro')
rep("""${sectionCard('What’s deleted', `<ul class="tc-dlist">""",
    """${sectionCard('Deleted after 30 days', `<ul class="tc-dlist">""",
    'deleted-heading')

# 2. The call: ask for the deletion; remember the date for the sign-in screen.
rep("""TC.deleteAccount = async function (deleteReviews) {
  await TC.freshSession();
  /* Storage isn't reachable from SQL, so the photo goes first, as on the desktop. A failure here
     must not stop the deletion. */
  try { await TC.client().storage.from('avatars').remove([TC.user.id + '/avatar.jpg']); } catch (e) {}
  let r = await TC.client().rpc('delete_my_account_v2', { p_delete_reviews: !!deleteReviews });
  if (r.error && /^(PGRST202|42883)$/.test(String(r.error.code || ''))) {
    /* delete_my_account_v2 isn't live yet. The original keeps reviews anonymously — the same as
       "keep", and never a quiet stand-in for "delete them". */
    if (deleteReviews) return 'Deleting your reviews along with your account isn’t switched on yet, so your account wasn’t deleted. Turn on “Keep my reviews up anonymously”, or delete your reviews from your profile first.';
    r = await TC.client().rpc('delete_my_account');
  }
  if (r.error) {""",
    """TC.deleteAccount = async function (deleteReviews) {
  await TC.freshSession();
  /* 30 days to recover (2026-10-04): nothing is removed now — the photo included, since a recovered
     account needs it. The database's daily job deletes everything after the 30 days. */
  const r = await TC.client().rpc('request_account_deletion', { p_delete_reviews: !!deleteReviews });
  if (r.error && /^(PGRST202|42883)$/.test(String(r.error.code || ''))) return 'Deleting accounts isn’t switched on yet, so your account wasn’t deleted. Try again later.';
  if (!r.error) {
    TC.purgeAt = r.data || null;
    /* The photo goes now, through the Storage API: SQL can't delete Storage files (Supabase refuses),
       so the 30-day job only clears what's left as a backstop. Best effort — never blocks. */
    let gone = false;
    for (let i = 0; i < 2 && !gone; i++) { try { const x = await TC.client().storage.from('avatars').remove([TC.user.id + '/avatar.jpg']); gone = !x.error; } catch (e) {} }
    /* only stop pointing at the photo once it's really gone (a recovered profile never shows a dead link) */
    if (gone) { try { await TC.client().from('profiles').update({ avatar_url: null }).eq('id', TC.user.id); } catch (e) {} }
  }
  if (r.error) {""",
    'call')

rep("""/* After the account is gone: forget it on this phone too, then back to the sign-in screen. */
TC.afterDelete = async function () {
  try { [CONC_KEY, PLAN_LOCAL, KEY, RECENT_KEY, DRAFT_KEY, ONB_KEY, 'professify-profile', 'professify_rev_times'].forEach(k => localStorage.removeItem(k)); } catch (e) {}
  try { sessionStorage.setItem('tc_deleted', '1'); } catch (e) {}
  try { await TC.client().auth.signOut({ scope: 'local' }); } catch (e) {}""",
    """/* After asking: sign this phone out and say until when it can be recovered. What only lives on the
   phone and a recovered account needs (concentration, local plans) stays; the rest is dropped. */
TC.afterDelete = async function () {
  try { [KEY, RECENT_KEY, DRAFT_KEY, ONB_KEY, 'professify_rev_times'].forEach(k => localStorage.removeItem(k)); } catch (e) {}
  try { sessionStorage.setItem('tc_deleted', String(TC.purgeAt || '1')); } catch (e) {}
  try { await TC.client().auth.signOut({ scope: 'global' }); } catch (e) {}
  /* (global: the account still exists for 30 days, so every device's sign-in is revoked) */""",
    'after')

# 3. Is this account being deleted? Asked on every sign-in, before anything else loads.
rep("""TC.usernameTaken = async function (u) {""",
    """/* null = not being deleted (or the database can't say yet: the SQL isn't live); { at } = pending;
   { err } = couldn't tell. */
TC.pendingDeletion = async function () {
  const r = await TC.client().rpc('my_account_deletion');
  if (r.error) return /^(PGRST202|42883)$/.test(String(r.error.code || '')) ? null : { err: (r.error.code ? r.error.code + ' · ' : '') + (r.error.message || '') };
  const row = Array.isArray(r.data) ? r.data[0] : r.data;
  return row && row.purge_after ? { at: row.purge_after } : null;
};
TC.usernameTaken = async function (u) {""",
    'pending-fn')
rep("""  if (schoolForEmail(TC.user.email || '') !== 'calpoly') { TC.phase = 'otherschool'; render(); return; }
  const me = TC.user.id;""",
    """  if (schoolForEmail(TC.user.email || '') !== 'calpoly') { TC.phase = 'otherschool'; render(); return; }
  /* Is this account being deleted (30 days to recover)? Asked alongside the profile read, so it adds
     no wait; the answer is looked at before anything is shown. */
  const pdAsk = TC.pendingDeletion().catch(() => ({ err: 'network' }));
  const me = TC.user.id;""",
    'boot-ask')
rep("""  const p = await sb.from('profiles').select('id,display_name,username,avatar_url,major,class_standing').eq('id', me).maybeSingle();""",
    """  const p = await sb.from('profiles').select('id,display_name,username,avatar_url,major,class_standing').eq('id', me).maybeSingle();
  const pd = await pdAsk;
  /* a refresh whose check fails keeps the app you have (as the profile read does) */
  if (pd && pd.err && TC.ready) { toast('Couldn’t refresh — check your connection'); return; }
  if (pd && pd.err) { TC.err.profile = pd.err; TC.phase = 'profileerr'; render(); return; }
  if (pd) { TC.pendingDel = pd; TC.phase = 'pendingdelete'; render(); return; }
  TC.pendingDel = null;""",
    'boot-gate')

# 4. The recover screen.
fmt = "(iso => { const d = /^\\d{4}-\\d\\d-\\d\\d/.test(String(iso || '')) ? new Date(iso) : null; return d && !isNaN(d) ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'the end of the 30 days'; })"
rep("""  /* Everything else — landing, sign up, the code, log in, the waitlist and "claim your username" —
     is Sean's onboarding design (onboard.js). */
  return onbSignin();""",
    """  if (TC.phase === 'pendingdelete') return `<div class="tc-signin"><img class="tc-logo" src="${LOGO}" alt="Term Champ"><h1>Recover your account?</h1>
    <p>Your account is set to be permanently deleted on <b>${esc(delDate(TC.pendingDel && TC.pendingDel.at))}</b>. Until then other students can’t see it.</p>
    <p>Recover it and everything comes back — your classes, plans, friends and reviews — except your profile photo, which you can add again.</p>
    ${UI.recErr ? `<div class="tc-err" role="alert">${esc(UI.recErr)}</div>` : ''}
    <button class="btn" data-a="recoverAccount" ${UI.busy.rec ? 'disabled' : ''}>${UI.busy.rec ? 'Recovering…' : 'Recover my account'}</button>
    <button class="btn ghost" style="margin-top:4px" data-a="signOut" ${UI.busy.rec ? 'disabled' : ''}>Sign out</button>
    <p class="muted" style="font-size:12.5px">Signed in as ${esc((TC.user && TC.user.email) || '')}</p></div>`;
  /* Everything else — landing, sign up, the code, log in, the waitlist and "claim your username" —
     is Sean's onboarding design (onboard.js). */
  return onbSignin();""",
    'recover-screen')
rep("""/* ================= sign in ================= */
function signinView() {""",
    """/* ================= sign in ================= */
/* "Nov 3, 2026" — dates always show their year. */
const delDate = """ + fmt + """;
function signinView() {""",
    'date-fmt')
rep("""  openDeleteAccount: () => {""",
    """  recoverAccount: async () => {
    if (UI.busy.rec) return;
    UI.busy.rec = 1; UI.recErr = ''; render();
    let r; try { r = await TC.client().rpc('cancel_account_deletion'); } catch (e) { r = { error: { message: 'failed to fetch' } }; }
    UI.busy.rec = 0;
    if (r.error) { UI.recErr = dbSay(r.error, 'Couldn’t recover your account — it’s still set to be deleted. Try again.'); return render(); }
    TC.pendingDel = null; TC.phase = 'boot'; render(); toast('Welcome back — your account is recovered'); TC.load();
  },
  openDeleteAccount: () => {""",
    'recover-action')

# 5. The sign-in screen after deleting says until when.
rep("""const TC_GONE = (() => { try { const v = sessionStorage.getItem('tc_deleted'); sessionStorage.removeItem('tc_deleted'); return !!v; } catch (e) { return false; } })();""",
    """const TC_GONE = (() => { try { const v = sessionStorage.getItem('tc_deleted'); sessionStorage.removeItem('tc_deleted'); return v || ''; } catch (e) { return ''; } })();""",
    'gone-flag')
rep("""TC_GONE ? '<div class="hint ok" role="status" style="justify-content:center">Your account is deleted.</div>' : ''""",
    """TC_GONE ? `<div class="hint ok" role="status" style="justify-content:center;text-align:center">Your account is scheduled for deletion. Sign in before ${esc(delDate(TC_GONE))} to recover it.</div>` : ''""",
    'landing')

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
