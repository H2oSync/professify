#!/usr/bin/env python3
"""Tests for champ-help-2026-10-11.py (Champ answers the questions people ask about TermChamp itself, and offers the
closest topic when a question is worded differently). Adds tests.champHelp and its mutants. Replayable.
  python3 edit-tests-champ-help-2026-10-11.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue   # already applied
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

PHRASINGS = r'''{
"note": "2026-10-11. Ways students might ask about TermChamp itself (pos: [question, topic]) and everyday questions that share words (neg), written by two separate model runs that never saw the matcher. Set 1 was then used to widen the rules; set 2 scored 59/80 found, 0 wrong topic, 1/50 offered by mistake before any change for it. A regression floor, not a target.",
"pos": [
[
"wait what even is this app",
"what_is"
],
[
"is termchamp an official cal poly thing or nah",
"what_is"
],
[
"who made this app lol",
"what_is"
],
[
"so what does termchamp do exactly",
"what_is"
],
[
"is this affiliated w/ the school or just some students",
"what_is"
],
[
"explain the app to me real quick, new here",
"what_is"
],
[
"do i have to pay for this",
"free"
],
[
"is termchamp free or is there a subscription",
"free"
],
[
"any ads in here?",
"free"
],
[
"r u gonna sell my info to advertisers",
"free"
],
[
"does it cost money to use all the features",
"free"
],
[
"is there a premium tier or paywall",
"free"
],
[
"can ppl see my schedule",
"who_sees"
],
[
"who can view what classes im taking",
"who_sees"
],
[
"is my schedule private or does everyone see it",
"who_sees"
],
[
"will my friends see my plans b and c too",
"who_sees"
],
[
"can random students look at my classes",
"who_sees"
],
[
"how do i control who sees my timetable",
"who_sees"
],
[
"if i leave a review can the prof see its me",
"ratings_anonymous"
],
[
"are my ratings anon",
"ratings_anonymous"
],
[
"will my friends know which review i wrote",
"ratings_anonymous"
],
[
"is it anonymous when i rate a professor",
"ratings_anonymous"
],
[
"does my name show up next to my review",
"ratings_anonymous"
],
[
"can someone figure out who posted a review",
"ratings_anonymous"
],
[
"where do the prof ratings come from",
"ratings_source"
],
[
"are the professor reviews legit or fake",
"ratings_source"
],
[
"who writes the ratings u see on here",
"ratings_source"
],
[
"is the rating data scraped from somewhere",
"ratings_source"
],
[
"how do u get the scores for each instructor",
"ratings_source"
],
[
"can i trust the professor ratings",
"ratings_source"
],
[
"where do u get the seat counts",
"seats_source"
],
[
"how up to date are the open seats numbers",
"seats_source"
],
[
"is the seat info live or delayed",
"seats_source"
],
[
"how accurate are the seats shown",
"seats_source"
],
[
"seat numbers wrong sometimes, where do they pull from",
"seats_source"
],
[
"how often do the available seats refresh",
"seats_source"
],
[
"how do i put a class on my schedule",
"add_class"
],
[
"how to add a course",
"add_class"
],
[
"where do i add classes to my week",
"add_class"
],
[
"pls show me how to put my classes in",
"add_class"
],
[
"adding my classes to the app, whats the process",
"add_class"
],
[
"idk how to enter my courses",
"add_class"
],
[
"what r plans a b and c",
"plans"
],
[
"whats the point of having multiple plans",
"plans"
],
[
"how do backup schedules work here",
"plans"
],
[
"can i make a plan b schedule",
"plans"
],
[
"what do the different plan tabs mean",
"plans"
],
[
"how do i switch between plan a and plan c",
"plans"
],
[
"can i get notified when a seat opens up",
"seat_alerts"
],
[
"how do seat alerts work",
"seat_alerts"
],
[
"how do i watch a full class",
"seat_alerts"
],
[
"will i get a push when someone drops a class",
"seat_alerts"
],
[
"set up a notification for a class that's full",
"seat_alerts"
],
[
"how do i turn off the seat notifications",
"seat_alerts"
],
[
"how do i upload my dpr",
"degree_report"
],
[
"where do i put my degree progress report",
"degree_report"
],
[
"can i import my degree audit",
"degree_report"
],
[
"what do i do with my dpr pdf",
"degree_report"
],
[
"does the app read my degree progress report",
"degree_report"
],
[
"how to add my degree requirements from the report",
"degree_report"
],
[
"how do i add my friends on here",
"add_friends"
],
[
"how to find friends in the app",
"add_friends"
],
[
"can i invite my roommate",
"add_friends"
],
[
"where do i search for people to friend",
"add_friends"
],
[
"send a friend request how",
"add_friends"
],
[
"how do friends get connected on termchamp",
"add_friends"
],
[
"how do i block someone",
"block_report"
],
[
"someone posted a rude review, how do i report it",
"block_report"
],
[
"report a user pls",
"block_report"
],
[
"can i block a person who is bugging me",
"block_report"
],
[
"how to flag an inappropriate review",
"block_report"
],
[
"theres a creepy user, what can i do",
"block_report"
],
[
"how do i delete my account",
"delete_account"
],
[
"i wanna quit the app and erase everything",
"delete_account"
],
[
"what happens to my data if i delete my account",
"delete_account"
],
[
"remove my profile permanently pls",
"delete_account"
],
[
"will my reviews disappear if i delete my account",
"delete_account"
],
[
"how to close my termchamp account",
"delete_account"
],
[
"what can champ do",
"champ"
],
[
"who is champ",
"champ"
],
[
"does champ see my schedule and stuff",
"champ"
],
[
"where do my questions to champ go",
"champ"
],
[
"is the ai reading my personal info",
"champ"
],
[
"is champ a real person or a bot",
"champ"
],
[
"is there dark mode",
"dark_mode"
],
[
"how do i make the app dark",
"dark_mode"
],
[
"can i change the theme to light",
"dark_mode"
],
[
"my eyes hurt at night, any dark setting",
"dark_mode"
],
[
"how to change how the app looks",
"dark_mode"
],
[
"switch to night mode pls",
"dark_mode"
],
[
"how do i contact support",
"contact"
],
[
"found a bug, who do i tell",
"contact"
],
[
"where can i send feedback",
"contact"
],
[
"app keeps crashing, need help from a human",
"contact"
],
[
"is there an email for the team",
"contact"
],
[
"how do i report a problem with the app",
"contact"
],
[
"so what even is this app",
"what_is"
],
[
"is termchamp made by cal poly?",
"what_is"
],
[
"who built this thing",
"what_is"
],
[
"whats termchamp",
"what_is"
],
[
"is this an official poly app or just some student project",
"what_is"
],
[
"cost?",
"free"
],
[
"do i have to pay for this",
"free"
],
[
"are there ads in here",
"free"
],
[
"u guys sell my info?",
"free"
],
[
"is there a premium version or is it all free",
"free"
],
[
"i dont want my ex seeing my classes",
"who_sees"
],
[
"can everyone see my schedule or just friends",
"who_sees"
],
[
"who can look at my plans",
"who_sees"
],
[
"is my schedule public",
"who_sees"
],
[
"can random people at poly see what im taking",
"who_sees"
],
[
"if i leave a review will the prof know its me",
"ratings_anonymous"
],
[
"are reviews anonymous?",
"ratings_anonymous"
],
[
"can my friends see which review is mine",
"ratings_anonymous"
],
[
"will my name show on a rating i post",
"ratings_anonymous"
],
[
"is it safe to write a bad review lol",
"ratings_anonymous"
],
[
"where do the prof ratings come from",
"ratings_source"
],
[
"are the ratings legit",
"ratings_source"
],
[
"who writes the reviews on professors",
"ratings_source"
],
[
"r these ratings real or scraped from somewhere",
"ratings_source"
],
[
"can i trust the stars on a professor",
"ratings_source"
],
[
"how do u know how many seats are left",
"seats_source"
],
[
"seat counts accurate?",
"seats_source"
],
[
"how often do the open seats update",
"seats_source"
],
[
"where does the seat info come from",
"seats_source"
],
[
"is the seat number live or like a day old",
"seats_source"
],
[
"how do i put a class on my schedule",
"add_class"
],
[
"adding classes?",
"add_class"
],
[
"i cant figure out how to add a class",
"add_class"
],
[
"how to get a course into my week",
"add_class"
],
[
"where do i tap to add a class",
"add_class"
],
[
"whats plan a b c",
"plans"
],
[
"what are the plans tabs for",
"plans"
],
[
"can i make a backup schedule",
"plans"
],
[
"how do i keep multiple versions of my schedule",
"plans"
],
[
"plan b?",
"plans"
],
[
"how do i get notified when a seat opens up",
"seat_alerts"
],
[
"seat alerts",
"seat_alerts"
],
[
"watch a full class for me",
"seat_alerts"
],
[
"will u text me if somebody drops the class",
"seat_alerts"
],
[
"how does watching a section work",
"seat_alerts"
],
[
"where do i upload my dpr",
"degree_report"
],
[
"how do i import my degree progress report",
"degree_report"
],
[
"dpr upload?",
"degree_report"
],
[
"can the app read my degree audit",
"degree_report"
],
[
"do i need to send my progress report in",
"degree_report"
],
[
"how do i find my friends on here",
"add_friends"
],
[
"add friend",
"add_friends"
],
[
"can i invite my roommate",
"add_friends"
],
[
"how do i see my buddies schedules",
"add_friends"
],
[
"where do i search for people to add",
"add_friends"
],
[
"how do i block someone",
"block_report"
],
[
"report a review",
"block_report"
],
[
"this person keeps bugging me how do i report them",
"block_report"
],
[
"theres a nasty review on a prof, can i flag it",
"block_report"
],
[
"block user?",
"block_report"
],
[
"how do i delete my account",
"delete_account"
],
[
"i want out, remove all my data",
"delete_account"
],
[
"deleting account?",
"delete_account"
],
[
"what happens to my stuff if i delete my profile",
"delete_account"
],
[
"how to quit termchamp and wipe everything",
"delete_account"
],
[
"what can champ do",
"champ"
],
[
"does the ai read my schedule",
"champ"
],
[
"where do my questions to champ go",
"champ"
],
[
"is champ a real person or a bot",
"champ"
],
[
"what does the ai helper see about me",
"champ"
],
[
"dark mode?",
"dark_mode"
],
[
"how do i make the app dark",
"dark_mode"
],
[
"change the theme",
"dark_mode"
],
[
"too bright at night, can i switch the look",
"dark_mode"
],
[
"light mode setting",
"dark_mode"
],
[
"how do i reach support",
"contact"
],
[
"found a bug",
"contact"
],
[
"who do i email about a problem",
"contact"
],
[
"how can i send feedback",
"contact"
],
[
"app keeps crashing who do i tell",
"contact"
]
],
"neg": [
"who's free tuesday afternoon",
"which of my friends are free at 2pm thursday",
"how many seats are left in BUS 3431",
"are there open seats in csc 1001",
"is prof martinez a good teacher",
"what's the rating for the stats professor",
"what does jake have on monday",
"what classes is my roommate taking this quarter",
"plans for dinner tonight?",
"what are my plans for cse 2305 this week",
"i need to drop a class, which one should i drop",
"how do i delete a class from my schedule",
"add jordan to my group study session",
"can you add sarah to the thursday lunch",
"is it dark outside yet",
"light or dark roast, which is better",
"how do i contact a professor",
"what's the email for my advisor",
"what are support courses for the finance major",
"what does ECON 2301 cover",
"what's the difference between acct 2101 and acct 2102",
"hi",
"hey champ",
"good morning",
"thanks!",
"lol ok",
"what's the weather in slo today",
"best burrito near campus",
"where can i park on campus",
"when does the library close",
"how do i get to the rec center",
"what time is finals week",
"when is the last day to withdraw from a class",
"is calc 2 hard",
"should i take stats before finance",
"which gen ed is the easiest",
"how many units do i need to graduate",
"how many units am i taking this quarter",
"who teaches math 141",
"what time is my first class tomorrow",
"do i have any classes on friday",
"what's a good elective for a business major",
"tell me a joke",
"how do i write a good cover letter",
"how do i study for midterms",
"recommend a podcast",
"what should i eat for lunch",
"which professor has the best reviews for ENGL 134",
"is there a seat open in my friend's section",
"can i swap sections with my friend",
"what is a degree in financial management good for",
"what's a dpr in general, like what is a degree progress report used for at cal poly",
"how do i get my transcript",
"how do i report a lost id card",
"how do i delete my old emails",
"are there any free tutoring services on campus",
"where do i get free food on campus",
"what's the cheapest way to get textbooks",
"how do i make friends at cal poly",
"what are some good ratings for restaurants in slo",
"hey",
"hi there",
"thanks!",
"what time does the library close",
"is the gym free for students",
"where is the rec center",
"what's good to eat near campus",
"is BUS 3431 hard",
"how many seats are in CSC 1001 right now",
"what's the rating for Dr. Smith in ECON 2301",
"does csc 1001 have a lab",
"my friend is free on tuesday afternoon, what should we do",
"are my friends going to the game friday",
"what are my friend's plans for spring break",
"can I add MATH 1421 after the deadline",
"should I add ACCT 2171 or ACCT 2181",
"delete BUS 3431 from my plan",
"drop FIN 3301 before add/drop ends",
"how do I report card grades for my transcript",
"who made the syllabus for ECON 2301",
"contact my advisor",
"how do I email Professor Johnson",
"who is the best professor for STAT 2121",
"are ads allowed on campus bulletin boards",
"how much does a parking permit cost",
"is the bookstore selling used textbooks for MKTG 3011",
"what's the weather in SLO today",
"can you explain depreciation",
"explain NPV vs IRR",
"what does csc 2103 cover",
"who can see my grades on canvas",
"how do I block off time in my google calendar",
"what is the dark roast at Mustang coffee",
"how do I change my major",
"when does registration open for winter",
"what are the prereqs for BUS 3431",
"is there a waitlist for ARCH 2511",
"tell me a joke",
"what's the capital of France",
"how do I get a refund on my meal plan",
"can I take FIN 3301 and FIN 3302 together",
"how do i delete a file off my laptop",
"what's the best way to study for finals",
"how long is the drive to Encinitas",
"where do I upload my homework for MATH 1421",
"how do I report a broken light on campus",
"is the student health center free",
"what does the A in plan A mean on my financial aid letter",
"who is my academic advisor for finance",
"what's a good intro commercial real estate book"
]
}
'''

TESTS = r'''/* ============ Champ: questions about TermChamp itself (Tate, 2026-10-11) ============
   "make sure Champ can ask basic question that people ask about termchamp … still tight and regulated and only
   specific but … a useful tool", and "when someone asks a quesiton that is similar it has this show up … because
   its close to the question". The model picks one of 16 topics; the phone shows that topic's fixed answer. When the
   model can't place a question, or can't be reached, the phone offers the closest topics as "Did you mean" chips. */
tests.champHelp = async () => {
  const KEYS = ['what_is', 'free', 'who_sees', 'ratings_anonymous', 'ratings_source', 'seats_source', 'add_class', 'plans', 'seat_alerts', 'degree_report', 'add_friends', 'block_report', 'delete_account', 'champ', 'dark_mode', 'contact'];
  const asks = Object.fromEntries(KEYS.map(k => ['topic ' + k, { tool: 'app_help', args: { topic: k } }]));
  Object.assign(asks, {
    'topic refund': { tool: 'app_help', args: { topic: 'refund' } },
    'topic constructor': { tool: 'app_help', args: { topic: 'constructor' } },
    'does the ai keep my chats': { tool: 'cant_answer', args: { reason: 'not_about_classes' } },
    'whats the weather': { tool: 'cant_answer', args: { reason: 'not_about_classes' } },
    'is bus 4442 worth it if the seats are always wrong': { tool: 'cant_answer', args: { reason: 'needs_judgment' } },
    'who can see my schedule and is champ private': { tool: 'cant_answer', args: { reason: 'ambiguous' } },
    'who can see my schedule': { tool: 'app_help', args: { topic: 'who_sees' } },
  });
  const { page, close, log } = await openApp({ ask: b => asks[b.q.toLowerCase()] || null });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  const HELPT = await page.evaluate(() => JSON.parse(JSON.stringify(HELP)));
  ok(JSON.stringify(Object.keys(HELPT)) === JSON.stringify(KEYS), 'help: the phone answers exactly the 16 topics the function offers', Object.keys(HELPT));
  const last = () => page.evaluate(() => { const b = [...document.querySelectorAll('#champscroll .bot')].pop(), f = document.querySelector('#champscroll .chfollow');
    return { t: b.querySelector('.msg').innerText.trim(), acts: [...b.querySelectorAll('.acts .act')].map(x => [x.innerText.trim(), x.dataset.a, x.dataset.x || '']),
      chips: f ? [...f.querySelectorAll('button')].map(x => [x.innerText.trim(), x.dataset.a, x.dataset.x || '', x.className]) : [], n: S.champMsgs.length }; });
  const say = async q => { const n = log.asks.length; await page.evaluate(q => { UI.champ = true; render(true); return ask(q); }, q); await tick(page, 400); return Object.assign(await last(), { sent: log.asks.length - n }); };

  /* 1. every topic: its own words and its one button */
  const wrong = [];
  for (const k of KEYS) { const r = await say('topic ' + k), h = HELPT[k];
    if (r.sent !== 1 || !r.t.startsWith(h.t) || r.acts.length !== 1 || JSON.stringify(r.acts[0]) !== JSON.stringify(h.a) || r.chips.length) wrong.push({ k, r }); }
  ok(!wrong.length, 'help: each of the 16 topics shows its fixed answer and its one button, nothing else', wrong.slice(0, 3));
  /* 2. the words are what the app, the Terms and the Privacy Policy say */
  await page.evaluate(() => { UI.champ = false; A.openLegal('terms'); }); await tick(page, 900);
  const terms = await text(page);
  await page.evaluate(() => A.openLegal('privacy')); await tick(page, 900);
  const priv = await text(page);
  const LC = ((terms.match(/Questions: ([\w.+-]+@[\w.-]+\.[a-z]+)/) || [])[1]) || '';
  ok(LC === 'support@termchamp.com' && HELPT.contact.t.includes(LC) && terms.includes(LC) && await page.evaluate(() => SUPPORT_EMAIL) === LC, 'help: the support address is the one the Terms give', LC);
  ok(/refreshed roughly once a day/.test(terms) && /about once a day/.test(HELPT.seats_source.t) && /public class search/.test(terms) && /public class search/.test(HELPT.seats_source.t), 'help: seats — Cal Poly’s public class search, about once a day, as the Terms say');
  ok(/permanently deleted after 30 days/.test(terms) && /deleted after 30 days/.test(HELPT.delete_account.t) && /sign in before then to recover it/.test(terms), 'help: deleting — 30 days to recover, as the Terms say');
  ok(/does not sell your data and does not run ads/.test(priv) && /no ads/.test(HELPT.free.t) && /never sold/.test(HELPT.free.t), 'help: free — no ads, data never sold, as the Privacy Policy says');
  ok(/Ratings come from PolyRatings/.test(terms) && /PolyRatings/.test(HELPT.ratings_source.t), 'help: ratings come from PolyRatings');
  ok(/a person looks at every report within 24 hours/i.test(terms) && /within 24 hours/.test(HELPT.block_report.t), 'help: reports — a person, within 24 hours, as the Terms say');
  ok(await page.evaluate(() => PL_NAME.A === 'Best fit' && PL_NAME.B === 'Backup' && PL_NAME.C === 'Friends') && /A as your best fit, B as a backup/.test(HELPT.plans.t) && /C with more classes your friends take/.test(HELPT.plans.t), 'help: plans — A best fit, B backup, C friends, as the Plans screen names them');
  ok(await page.evaluate(() => PUSH_KINDS.some(([, l]) => l.some(x => x[0] === 'seat_open' && /watching or have in a plan/.test(x[2])))) && /iPhone app/.test(HELPT.seat_alerts.t) && /notifications on/.test(HELPT.seat_alerts.t), 'help: seat alerts — watched or in a plan, on the iPhone app with notifications on');
  ok((await page.content()).includes('about 30 days, not linked to your account') && /about 30 days, not linked to you/.test(HELPT.champ.t) && /doesn’t train on them/.test(HELPT.champ.t) && /a class or friend you name goes with it/.test(HELPT.champ.t), 'help: Champ — kept about 30 days, not linked to you, not trained on; a named class or friend goes with the question');
  ok((await page.content()).includes('Never your name, email or account') && /never your name or account/.test(HELPT.champ.t) && /Anthropic’s AI/.test(HELPT.champ.t) && /stay on this phone/.test(HELPT.champ.t), 'help: Champ — Anthropic, never your name or account, your data stays on the phone (the consent screen’s words)');
  await page.evaluate(() => { go('home'); });
  /* 3. every button lands where it says */
  const LAND = { tab: s => s.tab, openLegal: s => s.scr + ':' + s.which, openSettings: s => s.scr, openMyRatings: s => s.scr, exModeGo: s => s.tab + ':' + s.ex, schedTabGo: s => s.tab + ':' + s.sch, sheet: s => s.sheet, champPrivacy: s => s.scr + ':' + s.which, copySupport: s => s.toast };
  const WANT = { what_is: 'explore', free: 'legal:privacy', who_sees: 'settings', ratings_anonymous: 'myRatings', ratings_source: 'explore:profs', seats_source: 'explore', add_class: 'explore', plans: 'schedule:plans', seat_alerts: 'explore', degree_report: 'schedule:past', add_friends: 'addFriend', block_report: 'friends', delete_account: 'settings', champ: 'legal:privacy', dark_mode: 'settings', contact: /support@termchamp\.com|Email copied/ };
  const land = [];
  for (const k of KEYS) {
    await page.evaluate(() => { UI.sheet = null; UI.champ = false; setTab('home'); S.champMsgs = []; });
    await say('topic ' + k);
    await click(page, '#champscroll .bot .acts .act'); await tick(page, 500);
    const st = await page.evaluate(() => ({ tab: S.tab, scr: cur().s, which: (cur().p || {}).which, ex: S.exMode, sch: S.schedTab, sheet: UI.sheet && UI.sheet.type, toast: (document.getElementById('toast') || {}).innerText || '', champ: UI.champ }));
    const got = LAND[HELPT[k].a[1]](st), w = WANT[k];
    if (!(w instanceof RegExp ? w.test(got) : got === w) || (st.champ && k !== 'contact')) land.push({ k, got, w: String(w) });
  }
  ok(!land.length, 'help: every topic’s button opens the place it names (Copy email copies it)', land);
  await page.evaluate(() => { UI.sheet = null; setTab('home'); S.champMsgs = []; });
  /* 4. the model can't place it → the closest topic is offered; the chip answers from the phone */
  let r = await say('does the ai keep my chats');
  ok(r.sent === 1 && r.t === 'Did you mean this?' && r.chips.length === 1 && r.chips[0][0] === 'What does Champ do and where does my information go?' && r.chips[0][1] === 'champHelp' && r.chips[0][2] === 'champ', 'help: a question the model couldn’t place → “Did you mean this?” with the closest topic', r);
  const n0 = log.asks.length, m0 = r.n;
  await click(page, '#champscroll .chfollow .chhelp'); await tick(page, 300);
  r = await last();
  const me = await page.evaluate(() => [...document.querySelectorAll('#champscroll .msg.me')].pop().innerText.trim());
  ok(log.asks.length === n0 && r.n === m0 + 2 && me === 'What does Champ do and where does my information go?' && r.t.startsWith(HELPT.champ.t) && r.acts.length === 1 && !r.chips.length, 'help: tapping it asks it as the topic’s question and answers on the phone — nothing sent to the model', { r, me, sent: log.asks.length - n0 });
  r = await say('who can see my schedule and is champ private');
  ok(r.t === 'Did you mean one of these?' && r.chips.length === 2 && r.chips.map(c => c[2]).sort().join() === 'champ,who_sees', 'help: two close topics → both offered, no more', r.chips);
  r = await say('whats the weather');
  ok(/^I only know Cal Poly classes/.test(r.t) && !r.chips.length, 'help: nothing close → the usual answer, no chips', r);
  r = await say('is bus 4442 worth it if the seats are always wrong');
  ok(/^That one’s your call/.test(r.t) && !r.chips.length, 'help: a question naming a course is never offered a TermChamp topic', r);
  r = await say('topic constructor');
  ok(/^Can you say that another way/.test(r.t) && !r.acts.length, 'help: a topic named like a built-in (constructor) is not answered', r);
  r = await say('topic refund');
  ok(/^Can you say that another way/.test(r.t) && !r.acts.length, 'help: a topic the phone doesn’t know is not guessed at', r);
  /* 5. no model (the fixture's search fallback) → still offered */
  r = await say('is termchamp free');
  ok(r.sent === 1 && r.t === 'Did you mean this?' && r.chips.length === 1 && r.chips[0][2] === 'free', 'help: with no model answer, the closest topic is still offered', r);
  r = await say('how much is a parking permit');
  ok(!r.chips.some(c => c[1] === 'champHelp') && /can’t reach|not sure/i.test(r.t), 'help: with no model answer and nothing close, the usual line', r);
  /* 6. chips belong to the last answer only, and only real topics answer */
  await say('does the ai keep my chats'); r = await say('whats the weather');
  ok(await page.locator('#champscroll .chhelp').count() === 0, 'help: an older answer’s chips go when a new answer comes');
  const before = await page.evaluate(() => S.champMsgs.length);
  await page.evaluate(() => { A.champHelp('constructor'); A.champHelp('__proto__'); A.champHelp('toString'); A.champHelp('nope'); });
  ok(await page.evaluate(() => S.champMsgs.length) === before, 'help: champHelp answers only the 16 topics (not constructor, __proto__, …)');
  /* 7. the matcher: every golden way of asking finds its topic; nothing else is offered one */
  const here = nodePath.dirname(new URL(import.meta.url).pathname);
  const gf = [process.env.APP_DIR && nodePath.join(process.env.APP_DIR, 'dev', 'golden', 'model-golden-v3.json'), nodePath.resolve(here, '..', '..', 'dev', 'golden', 'model-golden-v3.json')].filter(Boolean).find(f => nodeFs.existsSync(f));
  const cases = JSON.parse(nodeFs.readFileSync(gf, 'utf8')).cases;
  const mr = await page.evaluate(cases => { const out = { miss: [], extra: [], n: 0 };
    for (const c of cases) { const m = helpMatch(c.q), want = [c, ...(c.alt || [])].filter(e => e.tool === 'app_help').map(e => e.args.topic);
      if (want.length) { out.n++; if (!want.includes(m[0])) out.miss.push([c.q, m]); } else if (m.length) out.extra.push([c.q, c.tool, m]); }
    return out; }, cases);
  ok(!mr.miss.length && mr.n >= 50, `help: each of the ${mr.n} golden ways of asking about TermChamp finds its topic on the phone`, mr.miss.slice(0, 6));
  ok(!mr.extra.length, 'help: none of the other golden questions is offered a TermChamp topic', mr.extra.slice(0, 6));
  const HELD = [['whats termchamp', 'what_is'], ['who runs this app', 'what_is'], ['do i have to pay for termchamp', 'free'], ['how much does it cost', 'free'], ['will you sell my information', 'free'],
    ['can anyone see my classes', 'who_sees'], ['how do i hide my schedule', 'who_sees'], ['is my name on my review', 'ratings_anonymous'], ['can the teacher see what i wrote', 'ratings_anonymous'],
    ['are the reviews real', 'ratings_source'], ['how often do seats update', 'seats_source'], ['how to add classes', 'add_class'], ['what is plan b for', 'plans'], ['how does watching work', 'seat_alerts'],
    ['what is a dpr', 'degree_report'], ['how do i invite friends', 'add_friends'], ['someone is being mean to me', 'block_report'], ['close my account', 'delete_account'],
    ['does anthropic train on my questions', 'champ'], ['is termchamp free in 2027', 'free'], ['who can see my schedule for fall 2026', 'who_sees'], ['where does my data go', 'champ'], ['night mode', 'dark_mode'], ['the app crashed', 'contact'], ['how do i reach a human', 'contact']];
  const NOT = ["who's free", 'is anyone free', 'when am i free monday', "who's in my classes", 'can i see my classes', 'is bus 4442 open', 'how many seats in stat 2170', 'are the seats in stat 2170 live', 'who made the stat 2170 final', 'hi', 'thanks champ',
    'hey champ whos free', 'support classes for my major', "what's my progress report say about ge", 'is lee a good professor', 'how do i rate a professor', 'delete my review', "what's in my plan b", 'what can you do', 'add jordan',
    'who built this campus', 'who runs this class', 'is it free to park', 'how much does this class cost', 'what does it cost to attend', 'ads class', 'advertising major classes',
    'how do i contact my professor', 'contact info for professor lee', 'how do i block off time in my google calendar'];
  const hr = await page.evaluate(([H, N]) => ({ h: H.filter(([q, k]) => helpMatch(q)[0] !== k).map(([q]) => [q, helpMatch(q)]), n: N.filter(q => helpMatch(q).length).map(q => [q, helpMatch(q)]) }), [HELD, NOT]);
  ok(!hr.h.length, `help: ${HELD.length} other ways of asking each find their topic`, hr.h);
  ok(!hr.n.length, `help: ${NOT.length} everyday questions that sound close are not offered one`, hr.n);
  const PH = JSON.parse(nodeFs.readFileSync(nodePath.join(here, 'files', 'champ-help-phrasings.json'), 'utf8'));
  const pr = await page.evaluate(P => ({ found: P.pos.filter(([q, k]) => helpMatch(q)[0] === k).length, wrong: P.pos.filter(([q, k]) => helpMatch(q).length && !helpMatch(q).includes(k)).map(([q, k]) => [q, k, helpMatch(q)]), fp: P.neg.filter(q => helpMatch(q).length).map(q => [q, helpMatch(q)]) }), PH);
  ok(pr.found >= 155 && !pr.wrong.length && pr.fp.length <= 1, `help: ${PH.pos.length} independently written ways of asking — ${pr.found} find their topic, none a wrong one; ${pr.fp.length} of ${PH.neg.length} everyday questions offered one`, pr);
  /* 8. the chip, light and dark: blue outline, reads, wraps inside the sheet */
  await say('does the ai keep my chats');
  for (const th of ['light', 'dark']) {
    await page.evaluate(th => { document.documentElement.setAttribute('data-theme', th); render(true); }, th); await tick(page, 300);
    const lk = await page.evaluate(() => { const c = document.querySelector('#champscroll .chhelp'), s = getComputedStyle(c), sh = document.getElementById('sheet').getBoundingClientRect(), b = c.getBoundingClientRect();
      const rgb = v => (v.match(/[\d.]+/g) || []).slice(0, 3).map(Number), L = v => { const [r, g, bb] = rgb(v).map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * bb; };
      const a = L(s.color), bg = L(s.backgroundColor); return { cr: (Math.max(a, bg) + 0.05) / (Math.min(a, bg) + 0.05), border: s.borderTopColor, blue: getComputedStyle(document.documentElement).getPropertyValue('--blue').trim(), padT: parseFloat(s.paddingTop), right: b.right <= sh.right - 8, h: b.height }; });
    ok(lk.cr >= 4.5 && lk.padT >= 8 && lk.right && lk.h >= 44, `help: the Did-you-mean chip reads and fits (${th})`, lk);
  }
  await page.evaluate(() => { document.documentElement.setAttribute('data-theme', 'light'); render(true); });
  ok(log.errors.length === 0, 'help: no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [("tests.champGolden = async () => {", TESTS + "tests.champGolden = async () => {", 'tests')])
open(os.path.join(H, 'files', 'champ-help-phrasings.json'), 'w', encoding='utf-8').write(PHRASINGS)

MUT = r'''  /* Champ: questions about TermChamp (2026-10-11) */
  ["help: app_help answers nothing", "    case 'app_help': return Object.prototype.hasOwnProperty.call(HELP, a.topic) ? helpAns(a.topic) :", "    case 'app_help': return null && HELP[a.topic] ? helpAns(a.topic) :", "champHelp"],
  ["help: app_help answers a prototype key", "    case 'app_help': return Object.prototype.hasOwnProperty.call(HELP, a.topic) ? helpAns(a.topic) :", "    case 'app_help': return HELP[a.topic] ? helpAns(a.topic) :", "champHelp"],
  ["help: a year read as a course", ".test(t.replace(/\\b(fall|winter|spring|summer|in|of|since|by|until|for|class of) (19|20)\\d\\d\\b/g, ' '))) return [];", ".test(t)) return [];", "champHelp"],
  ["help: a topic answered with its question", "const helpAns = k => ({ t: HELP[k].t,", "const helpAns = k => ({ t: HELP[k].q,", "champHelp"],
  ["help: cant_answer never offers a topic", "  if (!a || a.cant) { const hk = helpMatch(q);", "  if (!a) { const hk = helpMatch(q);", "champHelp"],
  ["help: no model → no topic offered", "  if (!a || a.cant) { const hk = helpMatch(q);", "  if (a && a.cant) { const hk = helpMatch(q);", "champHelp"],
  ["help: the chip asks the model again", "`<button class=\"chhelp\" data-a=\"${esc(f[1])}\" data-x=\"${esc(f[2])}\">", "`<button class=\"chhelp\" data-a=\"ask\" data-x=\"${esc(f[0])}\">", "champHelp"],
  ["help: a course-naming question offered a topic", "if (t.trim().length < 4 || /\\b[a-z]{2,5} ?\\d{3,4}[a-z]?\\b/.test(t.replace(", "if (t.trim().length < 4 || false && /\\b[a-z]{2,5} ?\\d{3,4}[a-z]?\\b/.test(t.replace(", "champHelp"],
  ["help: a rule's 'not' words ignored", " && !(not && not.not.test(t)) ? n + w : n;", " ? n + w : n;", "champHelp"],
  ["help: champHelp answers anything on HELP's prototype", "champHelp: k => { if (!Object.prototype.hasOwnProperty.call(HELP, k)) return;", "champHelp: k => { if (!HELP[k]) return;", "champHelp"],
  ["help: one topic only", ".filter(x => x.s >= 2).sort((x, y) => y.s - x.s).slice(0, 2)", ".filter(x => x.s >= 2).sort((x, y) => y.s - x.s).slice(0, 1)", "champHelp"],
  ["help: the chip is a plain chip", ".chfollow button.chhelp{text-align:left;padding:10px 14px;", ".chfollow button.chhelp{text-align:left;", "champHelp"],
  ["help: the wrong support address", "const SUPPORT_EMAIL = 'support@termchamp.com';", "const SUPPORT_EMAIL = 'help@termchamp.com';", "champHelp"],
  ["help: seats said to be live", "From Cal Poly’s public class search, refreshed about once a day", "From Cal Poly’s public class search, updated live", "champHelp"],
  ["help: the Champ answer goes to the wrong place", "a: ['How Champ uses your questions', 'champPrivacy', '']", "a: ['How Champ uses your questions', 'openSettings', '']", "champHelp"],
  ["help: who-sees matches any 'see my classes'", "access)\\b/, HW.mine, /\\b(who|whom|ppl|people|someone|somebody|anyone|anybody|everyone|strangers|random|others|public|friends|students|professors?)\\b/],", "access)\\b/, HW.mine],", "champHelp"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants')])
print('edit-tests-champ-help: tests.champHelp + 14 mutants')
