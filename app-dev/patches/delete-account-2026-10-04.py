#!/usr/bin/env python3
r"""Delete your account inside the phone app (App Store chunk 2, 2026-10-04).

Apple 5.1.1(v): an app that lets people make an account must let them delete it IN the app. Until
now the phone's Settings said "To delete your account, use Settings on termchamp.com" and linked to
the homepage, which App Review rejects.

Tate (2026-10-04), on what happens to reviews: keep them up anonymously, but let the person choose.
  · Settings › "Delete account" opens a screen that lists what goes, then one switch:
    "Keep my reviews up anonymously" — ON by default. Off = the reviews are deleted too.
  · It says plainly what is kept (reports you filed stay with moderators, without your name).
  · Type DELETE, then "Delete my account". Nothing happens until the word is typed.
  · Calls delete_my_account_v2(p_delete_reviews) (sql/professify-delete-account-v2.sql). If that
    SQL isn't live yet: keeping reviews falls back to the original delete_my_account(), which keeps
    them anonymously — the same thing; deleting reviews refuses and says nothing was deleted, rather
    than quietly keeping them.
  · After it succeeds: this phone's TermChamp data is cleared, the session is dropped locally, and
    the sign-in screen says "Your account is deleted."

Runs after share-row-2026-10-04.py. Usage: python3 delete-account-2026-10-04.py <repo-dir>.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b, label):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    s = s.replace(a, b)

# 1. CSS
rep(".pbtn.tc-danger{color:#B91C1C;background:#FEF2F2}\n",
    ".pbtn.tc-danger{color:#B91C1C;background:#FEF2F2}\n"
    "/* Delete account (2026-10-04). Red only where the action is; disabled reads grey like every other button. */\n"
    ".btn.tc-del{background:#DC2626;box-shadow:none}\n"
    ".btn.tc-del:disabled{background:#CBD5E1}\n"
    ".tc-dellink{display:block;width:100%;text-align:center;color:#B91C1C;font-weight:900;font-size:15px;min-height:44px}\n"
    ".tc-dlist{margin:2px 0 8px;padding:0;list-style:none;display:grid;gap:8px}\n"
    ".tc-dlist li{display:flex;gap:10px;align-items:flex-start;font-weight:700;font-size:14.5px;line-height:1.35;color:var(--ink)}\n"
    ".tc-dlist li::before{content:'';flex:none;width:7px;height:7px;border-radius:50%;background:#DC2626;margin-top:7px}\n",
    'css')

# 2. Settings: the web-only line becomes a real door.
rep("""  <div class="muted b" style="font-size:12.5px;text-align:center;line-height:1.45">To delete your account, use Settings on ${webLink('termchamp.com', '/')} — it shows exactly what gets deleted first.</div></div>""",
    """  <button class="tc-dellink" data-a="openDeleteAccount">Delete account</button></div>""",
    'settings')

# 3. The screen.
rep("SCREENS.legal = ({ which }) => {",
r"""/* Delete account (2026-10-04, App Store 5.1.1(v)). One screen: what goes, the reviews choice, what
   stays, then type DELETE. The reviews switch is on by default (Tate: keep them, anonymously) and is
   only shown when there are reviews, or when we couldn't tell. */
SCREENS.deleteAccount = () => {
  const d = UI.del || (UI.del = { keep: true, typed: '', err: '', busy: 0 });
  /* The count only counts once a fresh my_reviews() came back on this open; until then, or if it
     failed, the switch shows (we never hide a choice because we couldn't tell). */
  const nRev = d.revs === 'ok' && Array.isArray(TC.myReviews) ? TC.myReviews.length : null;
  const ready = d.typed.trim().toUpperCase() === 'DELETE';
  const revCard = nRev === 0 ? '' : sectionCard(nRev ? `Your ${nRev} ${nRev === 1 ? 'review' : 'reviews'}` : 'Your reviews',
    `<div class="row sb tc-row" style="gap:12px"><div class="b" style="font-size:15px">Keep my reviews up anonymously</div><button class="toggle ${d.keep ? 'on' : 'off'}" data-a="toggleKeepReviews" role="switch" aria-checked="${d.keep}" aria-label="Keep my reviews up anonymously"><i></i></button></div>
  <div class="muted b" id="delRevLine" style="font-size:13.5px;line-height:1.45;padding:2px 0 10px">${d.keep
      ? 'They stay up for other students with no name on them. Nothing links them to you afterwards, so they can’t be edited or removed later.'
      : (nRev === 1 ? 'Your review is' : 'Your reviews are') + ' deleted along with your account.'}</div>`);
  return {
    body: `<div class="topbtns">${backBtn()}</div><div class="title" style="margin-top:-6px">Delete account</div>
 <div class="pad muted b" style="font-size:14.5px;line-height:1.45;margin:-4px 0 12px">This permanently deletes your TermChamp account. It can’t be undone.</div>
 ${sectionCard('What’s deleted', `<ul class="tc-dlist"><li>Your sign-in (email and password)</li><li>Your profile, photo and username</li><li>Your classes, plans and planner</li><li>Your friends and friend requests</li><li>Messages you sent, in every chat</li><li>Your blocks and settings</li></ul>`)}
 ${revCard}
 ${sectionCard('What’s kept', `<div class="muted b" style="font-size:13.5px;line-height:1.45;padding:2px 0 10px">Reports you filed stay with our moderators, without your name, so a case isn’t dropped because you left. Reports about you stay as a moderation record. Pictures of your week you already shared as links stay at those links.</div>`)}
 <form class="tc-form pad" data-submit="deleteAccount" style="margin-top:4px"><label>Type DELETE to confirm<input id="delconfirm" data-in="delconfirm" value="${esc(d.typed)}" autocomplete="off" autocapitalize="characters" autocorrect="off" spellcheck="false" placeholder="DELETE" ${d.busy ? 'disabled' : ''}></label>
  ${d.err ? `<div class="tc-err" role="alert">${esc(d.err)}</div>` : ''}
  <button class="btn tc-del" id="delgo" ${ready && !d.busy ? '' : 'disabled'}>${d.busy ? 'Deleting…' : 'Delete my account'}</button></form>
 <div class="spacer"></div>`, tabbar: false, fab: false
  };
};

SCREENS.legal = ({ which }) => {""",
    'screen')

# 4. The call.
rep("TC.usernameTaken = async function (u) {",
r"""/* Returns null on success, or a sentence. The database does it all in one transaction, so a failure
   means nothing was deleted. */
TC.deleteAccount = async function (deleteReviews) {
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
  if (r.error) {
    /* A lost connection can't say whether the delete happened, so it isn't told it didn't. */
    const m = dbSay(r.error, 'Couldn’t delete your account — it’s still here. Try again.');
    if (/Couldn’t reach TermChamp|sign-in expired/.test(m) || /still here/.test(m)) return m;
    return m.replace(/[.\s]*$/, '.') + ' Your account wasn’t deleted.';
  }
  return null;
};
/* After the account is gone: forget it on this phone too, then back to the sign-in screen. */
TC.afterDelete = async function () {
  try { [CONC_KEY, PLAN_LOCAL, KEY, RECENT_KEY, DRAFT_KEY, ONB_KEY, 'professify-profile', 'professify_rev_times'].forEach(k => localStorage.removeItem(k)); } catch (e) {}
  try { sessionStorage.setItem('tc_deleted', '1'); } catch (e) {}
  try { await TC.client().auth.signOut({ scope: 'local' }); } catch (e) {}
  location.replace(location.pathname);
};
TC.usernameTaken = async function (u) {""",
    'tc')

# 5. Actions.
rep("  openSettings: () => { TC.loadBlocks().then(() => render(true)); go('settings'); },",
    "  openSettings: () => { TC.loadBlocks().then(() => render(true)); go('settings'); },\n"
    "  openDeleteAccount: () => { UI.del = { keep: true, typed: '', err: '', busy: 0, revs: 'loading' }; TC.reloadMyReviews().then(() => { if (UI.del) UI.del.revs = TC.myReviewsErr ? 'err' : 'ok'; render(true); }, () => { if (UI.del) UI.del.revs = 'err'; render(true); }); go('deleteAccount'); },\n"
    "  toggleKeepReviews: () => { if (!UI.del || UI.del.busy) return; UI.del.keep = !UI.del.keep; render(true); },",
    'actions')

# 6. Typing DELETE enables the button without a re-render (keeps the keyboard up).
rep("  else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }",
    "  else if (k === 'ngTitle') { if (UI.ng) UI.ng.title = ev.target.value; }\n"
    "  else if (k === 'delconfirm') { if (UI.del) { UI.del.typed = ev.target.value; const b = document.getElementById('delgo'); if (b) b.disabled = !!UI.del.busy || UI.del.typed.trim().toUpperCase() !== 'DELETE'; } }",
    'input')

# 7. Submit.
rep("  setPw: async form => {",
r"""  deleteAccount: async form => {
    const d = UI.del; if (!d || d.busy) return;
    d.typed = form.querySelector('#delconfirm').value;
    if (d.typed.trim().toUpperCase() !== 'DELETE') { d.err = 'Type DELETE to confirm.'; return render(true); }
    d.busy = 1; d.err = ''; render(true);
    let e; try { e = await TC.deleteAccount(!d.keep); } catch (x) { e = 'Couldn’t delete your account — it’s still here. Try again.'; }
    if (e) { d.busy = 0; d.err = e; return render(true); }
    await TC.afterDelete();
  },
  setPw: async form => {""",
    'submit')

# 8. The sign-in screen says it happened.
rep("function onbSignin() {",
    "/* Enter in the DELETE box never submits — pressing the red button is the only way (2026-10-04). */\n"
    "document.addEventListener('keydown', ev => { if (ev.key === 'Enter' && ev.target && ev.target.id === 'delconfirm') { ev.preventDefault(); ev.target.blur(); } });\n"
    "/* Set by TC.afterDelete for the one reload that follows a deleted account. */\n"
    "const TC_GONE = (() => { try { const v = sessionStorage.getItem('tc_deleted'); sessionStorage.removeItem('tc_deleted'); return !!v; } catch (e) { return false; } })();\n"
    "function onbSignin() {",
    'gone-flag')
rep("""    <div class="foot">${si.err ? `<div class="hint bad" role="alert" style="justify-content:center">${esc(si.err)}</div>` : ''}
    <button type="button" class="btn" data-a="siMode" data-x="signup">Get started</button>""",
    """    <div class="foot">${si.err ? `<div class="hint bad" role="alert" style="justify-content:center">${esc(si.err)}</div>` : TC_GONE ? '<div class="hint ok" role="status" style="justify-content:center">Your account is deleted.</div>' : ''}
    <button type="button" class="btn" data-a="siMode" data-x="signup">Get started</button>""",
    'landing')

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
