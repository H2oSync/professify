#!/usr/bin/env python3
r"""Champ asks before sending anything to Anthropic; the legal text says what the app now does; no
screen sends you to the website for something the app does (App Store chunks 4 and 5, 2026-10-04).

Apple 5.1.2(i): an app that sends personal data to a third-party AI must say so and get permission
first. Apple 1.2: Terms with zero tolerance for objectionable content and abusive users, and a way
to report that's acted on within 24 hours.

  · Champ: the first time it's opened (per account, per phone) it shows "Before you ask Champ" —
    Anthropic is named, what goes (only the words typed) and what never goes (name, email, classes,
    friends), what's kept (about 30 days, not linked to the account) — with Allow / Not now.
    Nothing reaches the ask function before Allow: ask() and TC.ask() both check. A question asked
    before allowing waits and is asked after Allow. Settings › Champ turns it off again.
  · Legal (desktop index.html and app/planner.js, the same LEGAL_DOCS; dates 4 October 2026;
    contact support@termchamp.com): zero tolerance; the rules cover messages, group names and
    profiles; reports looked at within 24 hours; Block as it works now; deleting = hidden at once,
    deleted after 30 days, recover by signing in, reviews kept only if you choose, an email when
    it's done; Hawk → Champ (Hawk on the website); Security's stale "no password" and "no analytics"
    lines.
  · Cleanup: Home, My Classes, Rate, Champ and two errors pointed at termchamp.com for things the
    app does (adding classes, past classes, the Planner, editing a review). The leftover profile
    sheet's "Settings & full app on termchamp.com" opens Settings.

Runs after remove-friend-2026-10-04.py (18:30). Usage: python3 champ-consent-legal-2026-10-04.py <repo-dir>.
"""
import sys, os
root = sys.argv[1]
P_APP = os.path.join(root, 'app', 'index.html')
P_PL = os.path.join(root, 'app', 'planner.js')
P_DESK = os.path.join(root, 'index.html')
F = {k: open(v, encoding='utf-8').read() for k, v in (('app', P_APP), ('pl', P_PL), ('desk', P_DESK))}

def rep(k, a, b, label, n=1):
    c = F[k].count(a)
    if c != n: sys.exit(f'{k} {label}: anchor matched {c}x, expected {n}')
    F[k] = F[k].replace(a, b)

# ============ 1. Champ asks first ============
rep('app', """/* ---- Champ = Hawk. The same `ask` function the desktop uses; the model only names ONE tool, and""",
    """/* Champ's AI is Anthropic's (Apple 5.1.2(i), 2026-10-04): nothing is sent until the student taps Allow
   on "Before you ask Champ". Kept per account on this phone; Settings › Champ turns it off again. */
function champKey() { return 'tc_champ_ai:' + ((TC.user && TC.user.id) || 'anon'); }
function champOk() { try { return localStorage.getItem(champKey()) === '1'; } catch (e) { return false; } }
function champSet(on) { try { if (on) localStorage.setItem(champKey(), '1'); else localStorage.removeItem(champKey()); } catch (e) {} }
/* ---- Champ = Hawk. The same `ask` function the desktop uses; the model only names ONE tool, and""",
    'champ-ok')
rep('app', """TC.ask = async function (q) {
  const sb = TC.client(); if (!sb || !TC.user) return null;""",
    """TC.ask = async function (q) {
  const sb = TC.client(); if (!sb || !TC.user || !champOk()) return null;   /* never before Allow */""",
    'ask-guard')
rep('app', """async function ask(q) {
  q = String(q || '').trim().slice(0, 300); if (!q) return;""",
    """async function ask(q) {
  q = String(q || '').trim().slice(0, 300); if (!q) return;
  /* not allowed yet: the question waits on the consent screen and is asked after Allow */
  if (!champOk()) { UI.champPending = q; UI.champ = true; UI.sheet = null; render(true); return; }""",
    'ask-wait')
rep('app', """  /* The same disclosure the desktop's Hawk carries, and the privacy policy's Hawk section describes. */
  const input = `<form class="cinput" data-submit="champ"><input id="champin" placeholder="Ask Champ…" autocomplete="off" maxlength="300"><button class="sendbtn" aria-label="Send">${ic('arrow', 20, 2.6)}</button></form><div class="muted b" style="font-size:11.5px;text-align:center;margin-top:6px">Questions are read by AI · your classes stay on this phone</div>`;""",
    """  /* The same disclosure the desktop's Hawk carries, and the privacy policy's Champ section describes. */
  const input = `<form class="cinput" data-submit="champ"><input id="champin" placeholder="Ask Champ…" autocomplete="off" maxlength="300"><button class="sendbtn" aria-label="Send">${ic('arrow', 20, 2.6)}</button></form><div class="muted b" style="font-size:11.5px;text-align:center;margin-top:6px">Questions go to Anthropic’s AI · your classes stay on this phone</div>`;
  if (!champOk()) return `<div class="champ-hero"><img src="${CHAMP}" alt="Champ"></div><button class="xbtn" style="position:absolute;right:16px;top:16px" data-a="champNotNow" aria-label="Close">${ic('x', 16, 2.4)}</button>
  <div class="sbody tc-consent" style="padding-top:14px"><div class="ctitle2">Before you ask Champ</div>
  <p class="b" style="font-size:15px;line-height:1.45;margin:6px 0 12px;text-align:center">Champ uses AI from <b>Anthropic</b>, the company that makes Claude, to understand what you ask.</p>
  <ul class="tc-dlist tc-cdl"><li>Each question you ask Champ is sent to Anthropic — the words you type, or the suggestion you tap. Never your name, email or account. If a question names a class or a friend, that goes with it.</li>
  <li>Your schedule, friends and other TermChamp data aren’t sent. Champ works out the answer on this phone.</li>
  <li>TermChamp keeps your questions for about 30 days, not linked to your account, to fix its mistakes. Anthropic doesn’t train its AI on them.</li></ul>
  ${UI.champPending ? `<div class="muted b" style="font-size:13px;margin:4px 0 10px">Your question “${esc(UI.champPending)}” is asked as soon as you allow it.</div>` : ''}
  <button class="btn" data-a="champAllow">Allow</button>
  <button class="btn ghost" style="margin-top:6px" data-a="champNotNow">Not now</button>
  <button class="link b" style="display:block;margin:10px auto 0;color:var(--blue);font-size:14px;min-height:44px" data-a="champPrivacy">How Champ uses your questions</button></div>`;""",
    'consent-view')
rep('app', """  ask: q => ask(q),""",
    """  ask: q => ask(q),
  champAllow: () => { champSet(true); const q = UI.champPending; UI.champPending = null; render(true); if (q) ask(q); },
  champNotNow: () => { UI.champPending = null; UI.champ = false; render(true); setBars(false); },
  champPrivacy: () => { UI.champ = false; A.openLegal('privacy'); },
  toggleChampAi: () => { const on = !champOk(); champSet(on); if (!on) S.champMsgs = []; toast(on ? 'Champ is on' : 'Champ is off — it asks again next time'); render(true); },""",
    'actions')
rep('app', ".li.danger{color:#B91C1C}\n",
    ".li.danger{color:#B91C1C}\n"
    "/* Champ's consent (2026-10-04) */\n"
    ".tc-cdl{margin:0 0 14px;text-align:left}\n",
    'css')
# Settings › Champ
rep('app', """ ${sectionCard('Legal', legal)}""",
    """ ${sectionCard('Champ', `<div class="row sb tc-row" style="gap:12px"><div><div class="b" style="font-size:15px">Answers from Anthropic’s AI</div><div class="muted b" style="font-size:12.5px;line-height:1.4">Questions you type to Champ are sent to Anthropic to work out what you’re asking. Off: Champ asks again before sending anything.</div></div><button class="toggle ${champOk() ? 'on' : 'off'}" data-a="toggleChampAi" role="switch" aria-checked="${champOk()}" aria-label="Champ answers from Anthropic’s AI"><i></i></button></div>`)}
 ${sectionCard('Legal', legal)}""",
    'settings-champ')

# Delete screen: the confirmation email (sql/professify-deletion-emails.sql)
rep('app', """Changed your mind? Sign in before then to recover it. Your profile photo is removed now.</div>""",
    """Changed your mind? Sign in before then to recover it. Your profile photo is removed now. We email you when you ask and again when it’s done.</div>""",
    'delete-email')

# ============ 2. No screen sends you to the website for what the app does ============
rep('app', """Add your ${esc(CFG.TERM_LABEL)} classes on ${webLink('termchamp.com', '/')} and your week shows up here.""",
    """Find your ${esc(CFG.TERM_LABEL)} classes in Explore and tap + to add them — your week shows up here.""",
    'home-empty')
rep('app', """Add past classes on ${webLink('termchamp.com', '/')}.""",
    """Log past classes, or import your degree report, in Schedule → Planner.""",
    'rate-empty')
rep('app', """Import your ${esc(CFG.TERM_LABEL)} schedule on ${webLink('termchamp.com', '/')} and it shows up here.""",
    """Find your classes in Explore and tap + to add them.""",
    'mine-empty')
rep('app', """<a class="btn soft tc-a" href="${WEB}/" target="_blank" rel="noopener">Settings & full app on termchamp.com</a>""",
    """<button class="btn soft" data-a="openSettings">Settings</button>""",
    'profile-sheet')
rep('app', """'GE areas and major requirements aren’t in the phone app yet. The Planner on termchamp.com has them.'""",
    """'Your GE areas and major requirements are in the Planner.'""",
    'champ-ge')
rep('app', """'Units, requirements and whole-term building are in the Planner on termchamp.com for now.'""",
    """'Units and requirements are in the Planner.'""",
    'champ-units')
rep('app', """One review per professor keeps the average honest — edit yours on termchamp.com.""",
    """One review per professor keeps the average honest — edit yours from your profile.""",
    'review-dup')
rep('app', """'Past classes saved, but this term’s classes didn’t — add them on termchamp.com.'""",
    """'Past classes saved, but this term’s classes didn’t — add them from Explore (tap + on a class).'""",
    'onb-classes')

# ============ 3. Legal text (identical in the desktop and planner.js) ============
def legal(a, b, label):
    rep('pl', a, b, label); rep('desk', a, b, label)

legal("var LEGAL_UPDATED='7 September 2026';", "var LEGAL_UPDATED='4 October 2026';", 'date')
legal("var LEGAL_UPDATED_PRIVACY='25 September 2026';", "var LEGAL_UPDATED_PRIVACY='4 October 2026';", 'date-privacy')
# the contact address (support-email-2026-10-04.py did this in 19:15; done here only if it hasn't been)
for k in ('pl', 'desk'):
    if F[k].count("var LEGAL_CONTACT='support@termchamp.com';") != 1:
        rep(k, "var LEGAL_CONTACT='tdogtate@icloud.com';", "var LEGAL_CONTACT='support@termchamp.com';", 'contact')

# Privacy: Hawk is Champ (Hawk on the website). Only inside the privacy document.
for k in ('pl', 'desk'):
    s = F[k]; i = s.index("  privacy:{title:'Privacy',html:"); j = s.index("  security:{title:'Security',html:", i)
    if s[i:j].count('Hawk') < 10: sys.exit(f'{k}: privacy has only {s[i:j].count("Hawk")} Hawk mentions')
    F[k] = s[:i] + s[i:j].replace('Hawk', 'Champ') + s[j:]

legal("""sends the questions you ask Champ to <b>Anthropic</b>\\u2019s AI. None of them""",
      """sends the questions you ask Champ (Hawk on the website) to <b>Anthropic</b>\\u2019s AI \\u2014 in the phone app only once you allow it. None of them""",
      'privacy-key')
legal("""    +'<p>Champ answers the questions you type into the box in the corner. Many answers are worked out '""",
      """    +'<p>Champ (called Hawk on the website) answers the questions you type to it. In the phone app it '
    +'asks first: nothing is sent until you tap <b>Allow</b>, and you can turn it off again in Settings; after that, every question you ask '
    +'Champ in the phone app goes to Anthropic. On the website, many answers are worked out '""",
      'champ-intro')

# Terms: what you post — zero tolerance, all content, 24 hours
legal("""    +'<p>You keep ownership of what you write. By posting, you give TermChamp permission to display it in the app. We can remove a review that breaks these rules, and repeated breaches can end your account. The same rules, written plainly and with the reporting routes, are in the <b>Guidelines</b> tab above.</p>'""",
      """    +'<p>The same rules cover messages, group chat names, your profile and anything else you post. <b>There is no tolerance for objectionable content or abusive users:</b> content that breaks these rules is removed, and the account that posted it can be suspended or closed.</p>'
    +'<p>You keep ownership of what you write. By posting, you give TermChamp permission to display it in the app. You can report anything that breaks these rules and block anyone, and <b>a person looks at every report within 24 hours</b>. The same rules, written plainly and with the reporting routes, are in the <b>Community Guidelines</b>.</p>'""",
      'terms-post')
# Terms: ending it
legal("""    +'<p>Delete your account any time from Settings and your data goes with it — except your reviews, which stay up permanently unlinked from you, because other students are relying on them. Delete individual reviews from <b>Your reviews</b> first if you don’t want them kept. Privacy explains this in full. We can suspend accounts that break these terms.</p>'""",
      """    +'<p>Delete your account any time from Settings. It is hidden from other students straight away and <b>permanently deleted after 30 days</b>; sign in before then to recover it. When you delete it you choose what happens to your reviews: keep them up with no name on them (the default, because other students rely on them), or delete them with the account. We email you when you ask and again when the deletion is done. Privacy explains this in full. We can suspend or close accounts that break these terms.</p>'""",
      'terms-ending')
# Guidelines: zero tolerance, reporting, blocking, 24 hours
legal("""    +'<p>A review that breaks these rules is removed. Repeatedly breaking them ends the account. Suspended accounts cannot post, message, or send friend requests \\u2014 the database enforces that, not the interface.</p>'""",
      """    +'<p><b>There is no tolerance for objectionable content or abusive users.</b> These rules cover messages, group chat names and profiles as well as reviews. Anything that breaks them is removed; a serious or repeated breach suspends or closes the account. Suspended accounts cannot post, message, or send friend requests \\u2014 the database enforces that, not the interface.</p>'""",
      'guidelines-breach')
legal("""    +'<p>Every review, message, post and profile has a <b>Report</b> control. It asks for one of nine reasons and goes to a moderator queue. You can also <b>Block</b> anyone from their profile or a message thread: they can no longer message you or send you a request, they are not told, and they cannot see that they have been blocked.</p>'""",
      """    +'<p>Reviews, messages, profiles and group chat names can all be reported: pick a reason and it goes to a moderator. <b>A person looks at every report within 24 hours</b> and removes what breaks these rules. You can also <b>Block</b> anyone from their profile or a chat: you can no longer message each other or send each other requests, they are not told, and they cannot see that they have been blocked. Something urgent, or something the app won\\u2019t let you report? Email <b>'+LEGAL_CONTACT+'</b>.</p>'""",
      'guidelines-report')
# Privacy: how long, reviews, Resend, choices
legal("""    +'<p>While your account exists. Delete your account and your profile, classes, sections, past classes, plans, watchlist, friend links, suggestions, posts, blocks and messages are deleted with it. Backups may keep copies for a short period before rolling off.</p>'""",
      """    +'<p>While your account exists. Delete your account and it is hidden from other students straight away; <b>after 30 days</b> your profile, classes, sections, past classes, plans, watchlist, friend links, suggestions, posts, blocks and messages are deleted with it. Sign in during those 30 days to recover it. Your email address is used for two emails about it \\u2014 one when you ask, one when it is done \\u2014 and is then removed. Backups may keep copies for a short period before rolling off.</p>'""",
      'privacy-kept')
legal("""    +'<h4>Reviews are the one exception</h4>'""", """    +'<h4>Your reviews, when you delete your account</h4>'""", 'privacy-rev-h')
legal("""    +'<p><b>Your reviews stay up when you delete your account — but they stop being yours.</b> We set the author field to null,""",
      """    +'<p><b>You choose.</b> The delete screen has a <b>Keep my reviews up anonymously</b> switch, on unless you turn it off. Off: your reviews are deleted with your account. On: they stay up, but they stop being yours \\u2014 we set the author field to null,""",
      'privacy-rev-1')
legal("""    +'<p>Why: a review is what another student came here to read,""",
      """    +'<p>Why keeping them is the default: a review is what another student came here to read,""",
      'privacy-rev-2')
legal("""<li><b>Resend</b> — sends your sign-in codes; sees your email address.</li>""",
      """<li><b>Resend</b> — sends your sign-in codes and the emails about deleting your account; sees your email address.</li>""",
      'privacy-resend')
legal("""<li>Delete your account from Settings.</li>""",
      """<li>Delete your account from Settings. You have 30 days to change your mind.</li>""",
      'privacy-choices')
# Security: stale lines
legal("""    +'<p>There is no password to steal — sign-in is a one-time code emailed to your school address. Sessions are held in your browser and refresh in the background; signing out clears them.</p>'""",
      """    +'<p>Sign in with a one-time code emailed to your school address, or with a password you set. A password is stored only as a hash by the authentication service; nobody can read it, us included. Sessions are held in your browser and refresh in the background; signing out clears them.</p>'""",
      'security-signin')
legal("""    +'<li>No advertising or analytics trackers.</li>'""",
      """    +'<li>No advertising trackers. Google Analytics counts visits, as Privacy explains; it is never told what you look at or type.</li>'""",
      'security-ga')
legal("""    +'<li>No storing of passwords or phone numbers.</li>'""",
      """    +'<li>No phone numbers, and passwords only as a hash.</li>'""",
      'security-pw')
legal("""If someone is using this to harass you, email the address below.</li>'""",
      """If someone is using this to harass you, report or block them in the app, or email the address below.</li>'""",
      'security-harass')

for k, v in (('app', P_APP), ('pl', P_PL), ('desk', P_DESK)):
    open(v, 'w', encoding='utf-8').write(F[k])
print('patched', P_APP, P_PL, P_DESK)
