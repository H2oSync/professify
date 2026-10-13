#!/usr/bin/env python3
r"""The iPhone app stops sending people to the website (App Review prep, 2026-10-07).

Tate submitted the iPhone app (ios-app/, the phone app inside Capacitor) and asked to get ahead of
what App Review is most likely to send back. The two most common objections for an app like this are
4.2 ("a repackaged website") and 2.1 ("incomplete"), and both are fed by screens that tell a reviewer
to go to a website. Inside the iPhone app (window.TC_NATIVE) these go:

  · Onboarding's "Add this term's schedule": the second way ("Or import a schedule screenshot on
    termchamp.com" + the "Open termchamp.com" button). The app's own way — search your classes — stays.
  · Settings › About: the "Open TermChamp on the web" button.
  · The school waitlist screen: "(Your account / Already have a TermChamp account?) It still works on
    termchamp.com".
  · My Classes on a later term with no classes: "import your <term> schedule on termchamp.com" →
    "Once you've registered, your <term> classes go here."
  · Champ, asked for a screen it can't open: "That's on termchamp.com for now." + an "Open
    termchamp.com" button → "I couldn't find that screen in the app. Try asking another way." with
    Explore as the way out.

Everywhere: Champ, asked to switch the look, said "The phone app has one look for now." — stale since
dark mode (Settings › Appearance) and it reads as unfinished; it now points to Settings › Appearance.
The onboarding card that now has one way heads it "Add your classes", not "Two ways".

Spring 2027 was published by Cal Poly on Oct 5, so "Spring 2027 isn't posted yet" (My Classes' Spring
chip, Add to your week) and "Once the Spring 2027 schedule is posted" (Plans) are no longer true; they
now say Spring 2027 "isn't in TermChamp yet", which is.

On the web nothing else changes, except one line everywhere: the sign-up hint for a school that isn't open
yet said "<school> is coming soon — continue to join the list". "Coming soon" reads as an unfinished
feature to a reviewer; it now says "<school> isn't open yet — continue to join the waitlist".

And one change for both: a message the database refuses (P0001 — the optional slur filter on chats,
sql/professify-message-slur-filter.sql, prepared in case App Review asks for a chat filter under 1.2)
says the database's own sentence instead of "Couldn't send — try again". The draft stays in the box
either way, as before.

Usage: python3 native-review-polish-2026-10-07.py <repo-dir>. Edits app/index.html only.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
A = open(p, encoding='utf-8').read()

def rep(a, b, label):
    global A
    n = A.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    A = A.replace(a, b)

# 1. onboarding: the app's own way only, in the iPhone app
rep("""    <div class="card steps"><div class="label">Two ways</div>
     <div class="row"><div class="stepn">1</div><div><b style="font-weight:900">Search your classes</b> and pick your sections — takes a minute.</div></div>
     <div class="row"><div class="stepn">2</div><div>Or import a <b style="font-weight:900">schedule screenshot</b> on termchamp.com.</div></div>
     <a class="portal" href="${WEB}/" target="_blank" rel="noopener">Open termchamp.com${ONB_I.out}</a></div>""",
    """    <div class="card steps"><div class="label">${window.TC_NATIVE ? 'Add your classes' : 'Two ways'}</div>
     <div class="row"><div class="stepn">1</div><div><b style="font-weight:900">Search your classes</b> and pick your sections — takes a minute.</div></div>
     ${window.TC_NATIVE ? '' : `<div class="row"><div class="stepn">2</div><div>Or import a <b style="font-weight:900">schedule screenshot</b> on termchamp.com.</div></div>
     <a class="portal" href="${WEB}/" target="_blank" rel="noopener">Open termchamp.com${ONB_I.out}</a>`}</div>""",
    'onb-two-ways')

# 2. Settings › About: no "Open TermChamp on the web" in the iPhone app
rep("""  <a class="btn soft tc-a" style="margin-top:12px" href="${WEB}/" target="_blank" rel="noopener">Open TermChamp on the web</a>`)}""",
    """  ${window.TC_NATIVE ? '' : `<a class="btn soft tc-a" style="margin-top:12px" href="${WEB}/" target="_blank" rel="noopener">Open TermChamp on the web</a>`}`)}""",
    'about-web')

# 3. the waitlist screen: no "still works on termchamp.com" in the iPhone app
rep("""    <div class="ghost" style="font-size:13.5px">${signedIn ? 'Your account still works on' : 'Already have a TermChamp account? It still works on'} ${webLink('termchamp.com', '/')}.</div>""",
    """    ${window.TC_NATIVE ? '' : `<div class="ghost" style="font-size:13.5px">${signedIn ? 'Your account still works on' : 'Already have a TermChamp account? It still works on'} ${webLink('termchamp.com', '/')}.</div>`}""",
    'waitlist-web')

# 4. My Classes, a later term with nothing on it
rep("""${later ? `Once you’ve registered, import your ${L} schedule on ${webLink('termchamp.com', '/')} and it shows up here.` : `There are no ${L} classes on your account.`}""",
    """${later ? (window.TC_NATIVE ? `Once you’ve registered, your ${L} classes go here.` : `Once you’ve registered, import your ${L} schedule on ${webLink('termchamp.com', '/')} and it shows up here.`) : `There are no ${L} classes on your account.`}""",
    'later-term-web')

# 5. no "coming soon" anywhere
rep("""html: esc(sc.short) + ' is coming soon — continue to join the list', ok: true };""",
    """html: esc(sc.short) + ' isn’t open yet — continue to join the waitlist', ok: true };""",
    'coming-soon')

# 6. Champ: no website for a screen it can't open (iPhone app); the theme answer is current
rep("""return g ? { t: 'Here you go.', acts: [['Open ' + a.where, g[0], g[1]]] } : { t: `That’s on termchamp.com for now.`, acts: [['Open termchamp.com', 'web', '/']] }; }""",
    """return g ? { t: 'Here you go.', acts: [['Open ' + a.where, g[0], g[1]]] } : window.TC_NATIVE ? { t: 'I couldn’t find that screen in the app. Try asking another way.', acts: [['Open Explore', 'tab', 'explore']] } : { t: `That’s on termchamp.com for now.`, acts: [['Open termchamp.com', 'web', '/']] }; }""",
    'champ-goto-web')
rep("""    case 'set_theme': return { t: 'The phone app has one look for now.' };""",
    """    case 'set_theme': return { t: 'Pick System, Light or Dark in Settings › Appearance.', acts: [['Open Settings', 'openSettings', '']] };""",
    'champ-theme')

# 7. Spring 2027 IS posted (Cal Poly published it Oct 5); what isn't there yet is TermChamp's switch
#    to it. Four lines said "isn't posted yet" / "once the schedule is posted" — untrue now, and the
#    kind of thing a reviewer reads as stale.
rep("""return `<div class="empty" style="margin-top:6px"><b>${L} isn’t posted yet</b>Once Cal Poly posts the ${L} schedule and you’ve registered, your ${L} classes go here.</div>`;""",
    """return `<div class="empty" style="margin-top:6px"><b>${L} isn’t in TermChamp yet</b>Once it is and you’ve registered, your ${L} classes go here.</div>`;""",
    'mine-term-not-in')
rep("""`${esc(otherT ? otherT.label : 'That term')} isn’t posted yet`}</b>${otherT && otherT.code ? `Find the ${esc(otherT.label)} section of ${esc(s.code)} to add it there.` : `Once Cal Poly posts it, add your ${esc(otherT ? otherT.label : '')} classes here.`}""",
    """`${esc(otherT ? otherT.label : 'That term')} isn’t in TermChamp yet`}</b>${otherT && otherT.code ? `Find the ${esc(otherT.label)} section of ${esc(s.code)} to add it there.` : `Once it is, add your ${esc(otherT ? otherT.label : '')} classes here.`}""",
    'addto-term-not-in')
rep("""`${esc(otherT ? otherT.label : 'That term')} sections aren’t posted yet.`""",
    """`${esc(otherT ? otherT.label : 'That term')} sections aren’t in TermChamp yet.`""",
    'addto-sections-not-in')
rep("""Plans use ${esc(CFG.TERM_LABEL)} sections. Once the ${esc(CFG.REGISTRATION_TERM)} schedule is posted, plan with those.""",
    """Plans use ${esc(CFG.TERM_LABEL)} sections. Once ${esc(CFG.REGISTRATION_TERM)} is in TermChamp, plan with those.""",
    'plans-footnote')

# 8. a refused message says why
rep("""  if (r.error) { toast('Couldn’t send — try again'); return false; }""",
    """  if (r.error) { toast(r.error.code === 'P0001' && r.error.message ? dbSay(r.error, '') : 'Couldn’t send — try again'); return false; }""",
    'send-refused')

open(p, 'w', encoding='utf-8').write(A)
print('patched', p)
