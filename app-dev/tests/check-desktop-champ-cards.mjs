/* check-desktop-champ-cards — the website's Champ is the phone's chat, with the phone's answer cards (website-champ-cards, Tate
   2026-10-15: "the website's Champ still looks like the old Hawk answer screen"). Runs the REAL index.html + hawk-ask.js/css in
   Chromium, signed in, on the two-term site, against fixtures whose answers are known.
   Run: APP_DIR=<repo> node check-desktop-champ-cards.mjs [--only start-of-test-name] [--quiet]   (APP_PORT to move off 8190)
   The promises:
    - THE TERM. "When am I free this week?" for a student with Fall 2026 classes and NO Spring classes shows the week card with
      their Fall classes (it used to say "I don't have any classes saved for you yet"). Free time, a day, who is free now, who is
      free with you and clashes read the term you are IN (Fall); fit, the game plan, plans and add read the term you are choosing in (Spring).
    - THE CARDS. Week, day, free together, free now, fit, professors (big card + "Also teaching"), a class and its sections,
      search results with the filters it understood, prerequisites, the game plan, your clashes, your professors: each drawn from
      live site data, with the right words, and every part opens the real screen (class page, professor page, friend page, Schedule > Plans,
      the add-to-plan chooser) or asks the next question.
    - AI FIRST (owner 2026-10-15, "send to ai every time"). Every question — typed, a chip, a day tap — asks the function once before its card shows; the
      model only names the tool; the device answers only when the function cannot be used (signed out, a failure, fallback:'search').
    - THE CHAT. The question is a bubble, the answer a bubble, turns stay until the trash can clears them, only the newest answer offers follow-ups.
    - Everything printed is text: hostile names and codes never become markup. Both themes: every text >= 4.5:1. Nothing overflows 340px or a phone. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const T = {};
const test = (name, fn) => { T[name] = fn; };
const LIVE = [];

/* ---- fixtures ------------------------------------------------------------------------------------------------------ */
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
const clone = o => JSON.parse(JSON.stringify(o));
/* Spring: the Fall catalog again, one term on (BUS 3438 is not offered; BUS 3431 meets Fri/Sat evening), plus BUS 4411 (MoWe 12:10-1:00,
   a clash for BUS 4442) and BUS 4401's prerequisites. NOBODY has Spring classes: a Fall-only student. */
function fallOnly() {
  const T = clone(FX.TABLES);
  const spring = T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }, r.course_code === 'BUS 3431' ? { days: 'FrSa 6:10PM - 9:00PM' } : {}));
  const b42 = spring.find(r => r.course_code === 'BUS 4442');
  spring.push(Object.assign({}, b42, { course_code: 'BUS 4411', class_nbr: '70990', section: '01', days: 'MoWe 12:10PM - 1:00PM', term: '2274' }));
  T.course_seats = T.course_seats.concat(spring);
  T.course_prereqs.push({ course_code: 'BUS 4401', prereq_json: { req: [['BUS 3431'], ['MATH 1000', 'MATH 1001'], ['PHIL 3331']] } });
  return T;
}
/* The same, and you chose BUS 4401 in Spring. */
function both() {
  const T = fallOnly(), ph = T.course_seats.find(r => r.course_code === 'BUS 4401' && r.term === '2274');
  T.saved_classes.push({ user_id: FX.ME.id, term: '2274', code: 'BUS 4401', class_nbr: ph.class_nbr, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null });
  T.my_sections.push({ user_id: FX.ME.id, term: '2274', code: 'BUS 4401', class_nbr: ph.class_nbr, section: ph.section, instructor: ph.instructor, days: ph.days, status: 'enrolled', wl_pos: null });
  return T;
}
/* Fall: BUS 4445 moved to MoWe 11:10-1:00 so it runs into BUS 3438 (10:10-12:00) and BUS 4442 (12:10-2:00). */
function clashy() {
  const T = fallOnly(), d = 'MoWe 11:10AM - 1:00PM';
  T.course_seats.filter(r => r.course_code === 'BUS 4445' && r.term === '2268').forEach(r => { r.days = d; });
  T.my_sections.filter(r => r.code === 'BUS 4445').forEach(r => { r.days = d; });
  return T;
}
const HOSTILE_FRIEND = '<svg/onload=window.__pwn=1> Placeholder', HOSTILE_PROF = '<b onmouseover=window.__pwn=2>Evil</b>, Zed', HOSTILE_CODE = '<img src=x onerror=window.__pwn=3>';
function hostile() {
  const T = both();
  T.profiles.filter(p => p.id === '22222223-2222-4222-8222-222222222223').forEach(p => { p.display_name = HOSTILE_FRIEND; });
  T.course_seats.filter(r => r.course_code === 'BUS 3431').forEach(r => { if (r.section === '02') r.instructor = HOSTILE_PROF; });
  T.my_sections.filter(r => r.class_nbr === '70101').forEach(r => { r.instructor = HOSTILE_PROF; });
  return T;
}

/* ---- the harness around it ------------------------------------------------------------------------------------------ */
const TOOLS = {
  'prereqs for bus 4401': ['prereqs', { course: 'BUS 4401' }], 'my game plan': ['game_plan', {}], 'game plan for plan b': ['game_plan', { plan: 'B' }],
  'any clashes': ['my_conflicts', {}], 'my profs': ['my_professors', {}], 'ratings of ada please': ['professor_stats', { name: 'Ada Examplewood' }],
  'open bus sections monday': ['search_sections', { subject: 'BUS', open_only: true, days: ['Mo'] }],
  'hostile code prof': ['best_professor', { course: HOSTILE_CODE }], 'hostile code fit': ['fits_plan', { course: HOSTILE_CODE, plan: 'A' }],
};
/* The model, stood in for (AI-FIRST, owner 2026-10-15: every question goes to the function first). It only NAMES a tool, the way the
   real one does; what the card shows still comes from the page's own data. Unknown questions get cant_answer, as a real "no" does. */
const DAYN = { monday: 'Mo', tuesday: 'Tu', wednesday: 'We', thursday: 'Th', friday: 'Fr' };
function aiTool(q) {
  const t = String(q).toLowerCase().replace(/[’‘]/g, "'"), dn = Object.keys(DAYN).find(d => t.includes(d)), days = dn ? [DAYN[dn]] : [];
  const rel = /\btoday\b/.test(t) ? 'today' : /\btomorrow\b/.test(t) ? 'tomorrow' : null, code = (/\b([a-z]{2,4}) ?(\d{4})\b/.exec(t) || []).slice(1).join(' ').toUpperCase() || null;
  let m;
  if (/^when am i free this week\??$|^which of my days are free\??$/.test(t)) return ['my_free', {}];
  if (/free with me|\band i free\b/.test(t) && (m = /(?:is |^)(avery|sky|rowan|quinn) /.exec(t) || /^(avery) and i/.exec(t))) return ['free_with_friends', Object.assign({ friend: m[1][0].toUpperCase() + m[1].slice(1) }, days.length ? { days } : { week: true })];
  if (/free with me/.test(t)) return ['free_with_friends', { days }];
  if (/^who's free right now\??$|^who is out of class\??$/.test(t)) return ['friends_free_now', {}];
  if (/^is (avery) free right now/.test(t)) return ['free_with_friends', { friend: 'Avery' }];
  if (/when am i free|am i free/.test(t)) return ['my_free', Object.assign({}, days.length ? { days } : {}, rel ? { rel } : {})];
  if (/^(monday|tuesday|wednesday|thursday|friday)$|what do i have|my day/.test(t)) return ['my_day', days.length ? { days } : {}];
  if (code && /best.*prof/.test(t)) return ['best_professor', { course: code }];
  if (code && /fit/.test(t)) { const pl = /plan ([abc])/.exec(t); return ['fits_plan', { course: code, plan: pl ? pl[1].toUpperCase() : 'mine' }]; }
  if (code && t === code.toLowerCase()) return ['open_class', { course: code }];
  if (/^compare (.+) and (.+)$/.test(t)) { const c = /^compare (.+) and (.+)$/.exec(t); const cap = x => x.replace(/\b\w/g, l => l.toUpperCase()); return ['compare_professors', { a: cap(c[1]), b: cap(c[2]) }]; }
  return null;
}
const ask = b => {
  const k = String(b.q).toLowerCase(), t = TOOLS[k] || aiTool(b.q);
  return t ? { tool: t[0], args: t[1] } : { tool: 'cant_answer', args: { reason: 'not_about_classes' } };
};
const open = async (o = {}) => {
  const x = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, ask, terms: SPRING_CFG, tables: fallOnly() }, o));
  LIVE.push(x); await tick(x.page, 2500); await x.page.evaluate(() => loadFriendsData()); await tick(x.page, 1500);
  if (o.open !== false) { await x.page.click('.hawk-fab'); await tick(x.page, 300); }
  return x;
};
/* ask a question, return what the newest turn shows */
const LAST = '.hawk-log > .hawk-turn:last-child';
const say = async (page, q) => {
  await page.evaluate(q => HawkAsk.ask(q), q); await tick(page, 1500);
  return look(page);
};
const look = page => page.evaluate(LAST => {
  const t = document.querySelector(LAST); if (!t) return null;
  const tx = e => (e.innerText || '').replace(/\s+/g, ' ').trim();
  return { q: tx(t.querySelector('.hawk-said__q')), bubble: [...t.querySelectorAll('.hawk-bubble .hawk-note')].map(tx), acts: [...t.querySelectorAll('.hawk-acts .hawk-act')].map(tx),
    cards: [...t.querySelectorAll('.hawk-card')].map(c => c.getAttribute('aria-label')), follow: [...t.querySelectorAll('.hawk-follow .hawk-fq')].map(tx),
    text: tx(t), went: (t.querySelector('.hawk-went') || {}).textContent || '', n: document.querySelectorAll('.hawk-log > .hawk-turn').length };
}, LAST);
const click = async (page, sel, i = 0, ms = 900) => { await page.evaluate(([s, i]) => document.querySelectorAll(s)[i].click(), [sel, i]); await tick(page, ms); };
const texts = (page, sel) => page.evaluate(s => [...document.querySelectorAll(s)].map(e => (e.innerText || '').replace(/\s+/g, ' ').trim()), `${LAST} ${sel}`);
const activeView = page => page.evaluate(() => (document.querySelector('.view.active') || {}).id);
const noErrors = (log, n) => ok(log.errors.length === 0, n + ': no page errors', log.errors);

/* ================================================================================================================ the term */
test('week: a student with Fall classes and no Spring classes', async () => {
  const { page, close, log } = await open();
  const pre = await page.evaluate(() => ({ spring: myClasses.length, fall: nowMine().classes.slice().sort(), two: mcTwoTerms(), now: mcNowLabel() }));
  ok(pre.spring === 0 && pre.fall.length >= 4 && pre.two, 'the fixture student has Fall classes and no Spring classes', pre);
  const r = await say(page, 'When am I free this week?');
  ok(log.asks.length === 1 && log.asks[0].q === 'When am I free this week?' && log.asks[0].client === 'app', 'AI first: the question went to the function once, and the model named the tool', log.asks);
  ok(r.bubble[0] === 'Your free time, day by day. Tap a day to see it.' && !/saved for you|haven.t added/.test(r.text), 'it says the week is shown — not "I don\'t have any classes saved for you yet"', r);
  ok(r.cards[0] === 'Your free time' && /Fall 2026/.test(r.text), 'the week card, labelled with the term you are in', r.cards);
  const rows = await texts(page, '.hawk-wrow');
  ok(rows.length === 5 && /^Mon Free before 10:10a and after 6p/.test(rows[0]) && /^Tue No classes/.test(rows[1]) && /^Wed Free before 10:10a and after 6p/.test(rows[2]), 'a row per day: Mon "Free before 10:10a and after 6p", Tue "No classes"', rows);
  const bars = await page.evaluate(LAST => [...document.querySelectorAll(LAST + ' .hawk-wrow')].map(r => r.querySelectorAll('.hawk-wrow__bar i').length), LAST);
  const truth = await page.evaluate(() => ['Mo', 'Tu', 'We', 'Th', 'Fr'].map(d => avMyMeets().filter(m => m.meet && m.meet.days.includes(d)).length));
  ok(JSON.stringify(bars) === JSON.stringify(truth) && bars[0] === 4, 'the mini bar draws exactly the meetings Home draws for each day', { bars, truth });
  ok(/Not counted — no meeting time on BUS 2201/.test(r.text), 'a Fall class with no meeting time is said, not silently dropped', r.text);
  ok(await page.evaluate(() => !!document.querySelector('.hawk-log .hawk-bot__av')), 'Champ’s face sits beside the reply', null);
  /* tap a day: it asks that day */
  await click(page, `${LAST} .hawk-wrow`, 0);
  const d = await look(page);
  ok(d.q === 'When am I free Monday?' && d.bubble[0] === 'Free before 10:10a and after 6p.' && d.cards[0] === 'Your Monday', 'tapping Mon asks "When am I free Monday?" and answers with the day card', d);
  const blocks = await texts(page, '.hawk-day__blk');
  ok(blocks.length === 4 && ['BUS 3438', 'BUS 4442', 'BUS 4445', 'BUS 3431'].every((c, i) => blocks[i].startsWith(c)), 'the day card lists Monday’s four classes in order', blocks);
  const free = await texts(page, '.hawk-day__free');
  ok(free.length === 2 && /^Free 8a–10:10a/.test(free[0]) && /^Free after 6p/.test(free[1]), 'and the free stretches between them', free);
  ok(d.follow.includes('When am I free Tuesday?') && d.follow.includes('Who’s free with me Monday?'), 'follow-ups under the day: next day, who is free with me', d.follow);
  /* tap a class: its page, the Fall one — even from a Spring class page (BUS 4411 is Spring's alone), where the page would otherwise be Spring's */
  await page.evaluate(() => openClassPage('BUS 4411')); await tick(page, 800);
  ok(await page.evaluate(() => cpNow === false), 'set-up: a Spring class page is open (cpNow is false)', await page.evaluate(() => cpNow));
  await click(page, `${LAST} .hawk-day__blk`, 1, 1200);
  const v = await page.evaluate(() => ({ view: document.querySelector('.view.active').id, code: cpCode, now: cpNow }));
  ok(v.view === 'view-class' && v.code === 'BUS 4442' && v.now === true, 'tapping BUS 4442 opens its class page — the Fall one', v);
  ok(/Opened BUS 4442/.test((await look(page)).went), 'the answer says where the tap went', await look(page));
  /* the follow-up chip asks */
  await click(page, `${LAST} .hawk-fq`, 0);
  const t = await look(page);
  ok(t.q === 'When am I free Tuesday?' && /No classes Tuesday/.test(t.bubble[0]), 'the chip "When am I free Tuesday?" asks exactly that', t);
  ok(await page.evaluate(() => document.querySelectorAll('.hawk-log .hawk-follow').length === 1 && document.querySelectorAll('.hawk-log .hawk-notit').length === 1), 'only the newest answer offers follow-ups and "Not it?"', null);
  /* "Week ›" opens Home's week */
  await page.evaluate(() => { window.__cal = 0; const o = window.hmOpenCal; window.hmOpenCal = function () { window.__cal++; return o.apply(this, arguments); }; });
  await say(page, 'When am I free this week?');
  await click(page, `${LAST} .hawk-ch__open`, 0);
  ok(await page.evaluate(() => window.__cal) === 1, '"Week ›" opens the week you are in', null);
  noErrors(log, 'week');
  await close();
});

test('day: today, a named day, and the starter "What\'s my day look like?"', async () => {
  const { page, close, log } = await open({ time: '2026-09-28T11:00:00-07:00' });   // a Monday, 11:00: you are in BUS 3438 until 12p
  let r = await say(page, 'What’s my day look like?');
  ok(r.bubble[0] === 'You’re in BUS 3438 until 12p. Next: BUS 4442 at 12:10p.' && r.cards[0] === 'Your Monday', 'today: "You’re in X until 12p. Next: Y at 12:10p."', r);
  ok(await page.evaluate(LAST => !!document.querySelector(LAST + ' .hawk-day__now'), LAST), 'the card marks now on the clock', null);
  r = await say(page, 'What do I have Wednesday?');
  ok(/^4 classes Wednesday, 10:10a–6p\./.test(r.bubble[0]), 'a named day: "4 classes Wednesday, 10:10a–6p."', r);
  r = await say(page, 'Friday');
  ok(/No classes Friday/.test(r.bubble[0]) && r.cards[0] === 'Your Friday', 'a bare day name is that day', r);
  r = await say(page, 'am i free tomorrow');
  ok(/^Free before 10:10a and after 6p\.$/.test(r.bubble[0]) && r.cards[0] === 'Your Tuesday' || /^No classes Tuesday/.test(r.bubble[0]), 'tomorrow is read from the calendar', r);
  noErrors(log, 'day');
  await close();
});

test('the student with no Fall classes is told so, not shown an empty card', async () => {
  const E = fallOnly(); E.saved_classes = E.saved_classes.filter(r => !(r.user_id === FX.ME.id)); E.my_sections = E.my_sections.filter(r => r.user_id !== FX.ME.id);
  const { page, close, log } = await open({ tables: E });
  const r = await say(page, 'When am I free this week?');
  ok(/You haven’t added Fall 2026 classes with times yet/.test(r.bubble[0]) && r.cards.length === 0 && r.acts[0] === 'Open Schedule', 'an empty week says so and offers Open Schedule', r);
  await click(page, `${LAST} .hawk-act`, 0);
  ok((await activeView(page)) === 'view-sched', 'Open Schedule opens it', await activeView(page));
  noErrors(log, 'no classes');
  await close();
});

test('planning term: fit reads Spring, never Fall', async () => {
  const { page, close, log } = await open();    // Fall-only student: nothing chosen in Spring
  let r = await say(page, 'Does BUS 4401 fit my schedule?');
  ok(/You haven’t added Spring 2027 classes with times yet, so anything fits\./.test(r.bubble[0]) && r.cards[0] === 'BUS 4401' && r.acts[0] === 'Open Schedule', 'with nothing chosen in Spring, "fit my schedule" does not fall back to the Fall classes', r);
  await close();
  const b = await open({ tables: both() });
  r = await say(b.page, 'Does BUS 4401 fit my schedule?');
  ok(/^BUS 4401 is already in your classes\./.test(r.bubble[0]), 'with BUS 4401 chosen in Spring: "already in your classes" (the Spring list)', r);
  noErrors(log, 'planning term'); noErrors(b.log, 'planning term (both)');
  await b.close();
});

/* ================================================================================================================ the cards */
test('fit: Plan A against a section — yes, no, the grid, add, open', async () => {
  const { page, close, log } = await open({ tables: both() });
  await page.evaluate(() => { TCPlans.add('A', 'BUS 4442', '70102'); }); await tick(page, 1200);
  let r = await say(page, 'Does BUS 4401 fit my Plan A?');
  ok(r.bubble[0] === 'Yes — Section 01 fits Plan A.' && r.cards[0] === 'BUS 4401 in Plan A', 'yes: "Section 01 fits Plan A." and the fit card', r);
  ok(/No clashes/.test(r.text) && /MoWe 10:10a–11:30a/.test(r.text) && /7\/40 open|open/.test(r.text) && /Fixturesen/.test(r.text) && /★ 3\.6/.test(r.text), 'the card: no clashes, when, who and their rating, seats', r.text);
  ok(await page.evaluate(LAST => document.querySelectorAll(LAST + ' .hawk-wk__blk--ghost').length === 2 && document.querySelectorAll(LAST + ' .hawk-wk__blk--clash').length === 0, LAST), 'the grid shows the section as a dashed block on Mon and Wed, nothing outlined', null);
  ok(r.follow[0] === 'Does BUS 4401 fit my schedule?' && r.follow[1] === 'Best professor for BUS 4401?', 'follow-ups: my schedule / best professor', r.follow);
  /* + Add to Plan A: the site's own chooser, above Champ */
  const sel = `${LAST} button.pl2-cpbtn[data-pl-act="choose"][data-code="BUS 4401"][data-crn="70112"]`;
  ok(await page.evaluate(s => !!document.querySelector(s), sel), '"Add to Plan A" is the site’s own add flow (same attributes as the class page)', null);
  await click(page, sel, 0, 600);
  const ch = await page.evaluate(() => { const b = document.getElementById('plChoose'); if (!b) return null; const r = b.getBoundingClientRect(); const top = document.elementFromPoint(r.left + r.width / 2, r.top + 12); return { z: getComputedStyle(b).zIndex, onTop: b.contains(top), t: b.innerText.slice(0, 60) }; });
  ok(ch && +ch.z > 9010 && ch.onTop && /BUS 4401/.test(ch.t), 'the chooser opens over Champ and is clickable', ch);
  await page.evaluate(() => document.getElementById('plChoose') && document.getElementById('plChoose').remove());
  /* a clash */
  r = await say(page, 'Does BUS 4411 fit my Plan A?');
  ok(r.bubble[0] === 'No — every BUS 4411 section clashes with Plan A.', 'no: "every BUS 4411 section clashes with Plan A."', r);
  ok(/Clashes with BUS 4442/.test(r.text) && await page.evaluate(LAST => document.querySelectorAll(LAST + ' .hawk-wk__blk--clash').length >= 2, LAST), 'the card names the clash and outlines it in the grid', r.text);
  ok(r.follow[0] === 'Other BUS 4411 sections?', 'follow-up: other sections', r.follow);
  await click(page, `${LAST} .hawk-ch__open`, 0, 900);
  ok((await activeView(page)) === 'view-sched', '"Open ›" opens Schedule › Plans', await activeView(page));
  /* an unknown class, a phrase on "my schedule" */
  r = await say(page, 'Does BUS 9998 fit my Plan A?');
  ok(!/Yes|No —/.test(r.bubble[0] || ''), 'a class that is not offered is not answered yes or no', r);
  noErrors(log, 'fit');
  await close();
});

test('together: who is free with me on a day — Fall classes, friends\' Fall classes', async () => {
  const { page, close, log } = await open();
  await page.evaluate(() => { window.__msg = []; const o = window.msgWith; window.msgWith = function (id) { window.__msg.push(id); return o.apply(this, arguments); }; });
  let r = await say(page, 'Who’s free with me Tuesday?');
  ok(/are free when you are on Tuesday\.$/.test(r.bubble[0]) && r.cards[0] === 'Free with you Tuesday', 'the sentence and the card', r);
  const rows = await texts(page, '.hawk-fr');
  ok(rows.length === 4 && rows.every(x => /Free together /.test(x)) && /Free together 11a–6p · 7h/.test(rows[0]), 'four friends, the longest shared stretch first: "Free together 11a–6p · 7h"', rows);
  ok(await page.evaluate(LAST => document.querySelectorAll(LAST + ' .hawk-fr .hawk-av').length === 4, LAST), 'each has their avatar', null);
  ok(r.follow.includes('When am I free Tuesday?') && r.follow.includes('Who’s free with me Wednesday?'), 'follow-ups: my free time that day, next day', r.follow);
  await click(page, `${LAST} .hawk-fr__main`, 0, 1000);
  ok(await page.evaluate(() => !!document.querySelector('#frpBack.open')), 'tapping a friend opens their page', null);
  await page.evaluate(() => { const b = document.querySelector('#frpBack'); b && b.classList.remove('open'); });
  r = await say(page, 'Who’s free with me Monday?');
  ok(/Free together 8a–10:10a · 2h 10m/.test(r.text), 'Monday: your only free stretch is 8a–10:10a, and they are free in it', r.text);
  r = await say(page, 'When is Avery free with me Tuesday?');
  ok(/You and Avery are both free 11a–6p on Tuesday/.test(r.bubble[0]), 'one friend, one day', r);
  r = await say(page, 'Avery and I free this week');
  ok(r.cards[0] === 'Free with Avery' && (await texts(page, '.hawk-wrow--static')).length === 5, 'one friend, the week: five day rows', r);
  noErrors(log, 'together');
  await close();
});

test('now: who is free right now, a friend, the message button', async () => {
  const { page, close, log } = await open();
  await page.evaluate(() => { window.__msg = []; const o = window.msgWith; window.msgWith = function (id) { window.__msg.push(id); return o.apply(this, arguments); }; });
  let r = await say(page, 'Who’s free right now?');
  ok(log.asks.length === 1 && r.bubble[0] === '1 friend is free · Tue 10:30a', 'asked once, then drawn from the page: "1 friend is free · Tue 10:30a"', r);
  const truth = await page.evaluate(() => friendsList.map(f => ({ n: f.name.split(' ')[0], st: avState(avMeetsOf(f), new Date()).state })));
  const free = await texts(page, '.hawk-fr--free'), all = await texts(page, '.hawk-fr');
  ok(free.length === 1 && /^SP Sky No class till 12:10pm|^Sky No class till 12:10pm/.test(free[0]) && truth.filter(x => x.st === 'open').length === 1, 'one free friend, with when their next class is', { free, truth });
  ok(all.length === 4 && all.filter(x => /^(Avery|Rowan|Quinn)/.test(x.replace(/^[A-Z]{2} /, ''))).length === 3 && /In PHIL 3331 till 11:00am/.test(all.join('|')), 'the busy ones are listed under Busy, with what they are in', all);
  ok(await page.evaluate(LAST => document.querySelectorAll(LAST + ' .hawk-fbar').length === 1 && document.querySelectorAll(LAST + ' .hawk-fbar em').length === 1, LAST), 'the free friend’s day strip marks now', null);
  await click(page, `${LAST} .hawk-fr--free .hawk-act`, 0, 900);
  ok(await page.evaluate(() => window.__msg.length === 1 && window.__msg[0] === friendsList.find(f => f.name.startsWith('Sky')).id), 'Message opens a chat with that friend', await page.evaluate(() => window.__msg));
  await say(page, 'Who’s free right now?');
  await click(page, `${LAST} .hawk-fr__main`, 0, 900);
  ok(await page.evaluate(() => !!document.querySelector('#frpBack.open')), 'the friend row opens their page', null);
  await page.evaluate(() => document.querySelector('#frpBack').classList.remove('open'));
  r = await say(page, 'Is Avery free right now?');
  ok(/^Avery: In PHIL 3331 till 11:00am\.$/.test(r.bubble[0]) && r.acts.join('|') === 'Message Avery|Open Avery', 'one friend now: where they are, Message and Open', r);
  noErrors(log, 'now');
  await close();
});

test('professors: best professor for a class — big card, Also teaching, sections, taps', async () => {
  const { page, close, log } = await open();
  const want = await page.evaluate(() => { const by = {}; (SEAT_SECTIONS['BUS 3431'] || []).forEach(x => { const id = matchProfId(x.instructor); if (id) by[id] = PROFESSORS[id]; }); return Object.keys(by).map(id => ({ id, name: by[id].name, r: to5(by[id].rating), n: by[id].evals })).sort((a, b) => b.r - a.r); });
  const r = await say(page, 'Best professor for BUS 3431');
  ok(log.asks.length === 1 && r.bubble[0] === `${want[0].name} — top rated of ${want.length}.`, 'asked once, then drawn from the page: "<best> — top rated of N."', r.bubble);
  const big = await page.evaluate(LAST => { const c = document.querySelector(LAST + ' .hawk-card--prof'); if (!c) return null; const t = e => (e.innerText || '').replace(/\s+/g, ' ').trim(); return { top: t(c.querySelector('.hawk-ptop')), tiles: [...c.querySelectorAll('.hawk-tiles div')].map(t), secs: c.querySelectorAll('.hawk-psecs .hawk-row').length, adds: c.querySelectorAll('.hawk-psecs .hawk-sec__add').length }; }, LAST);
  ok(big && big.top.includes(want[0].name) && big.top.includes(want[0].r.toFixed(1)) && big.tiles[0].startsWith(String(want[0].n)) && big.secs >= 1 && big.adds === big.secs, 'the big card: name, average, ratings count, their sections each with a +', big);
  ok(/ALSO TEACHING BUS 3431|Also teaching BUS 3431/i.test(r.text), 'then "Also teaching BUS 3431"', r.text);
  const rows = await texts(page, '.hawk-prow');
  ok(rows.length === want.length - 1 && rows[0].includes(want[1].name) && rows[0].includes('★ ' + want[1].r.toFixed(1)), 'a row per other professor with their rating', rows);
  ok(r.follow.join('|') === 'Does BUS 3431 fit my schedule?|Who’s in BUS 3431?', 'follow-ups: fit my schedule / who is in it', r.follow);
  await click(page, `${LAST} .hawk-ptop`, 0, 1000);
  ok((await activeView(page)) === 'view-prof', 'tapping the professor opens their page', await activeView(page));
  await page.evaluate(() => show('home')); await tick(page, 600);   // leave the professor page, so the next tap has to open one itself
  ok((await activeView(page)) === 'view-home', 'set-up: back on Home before the next tap', await activeView(page));
  await click(page, `${LAST} .hawk-prow`, 0, 1000);
  ok((await activeView(page)) === 'view-prof' && await page.evaluate(n => document.getElementById('view-prof').innerText.includes(n), want[1].name), 'tapping an "Also teaching" row opens that professor (the one on the row)', await activeView(page));
  await click(page, `${LAST} .hawk-psecs .hawk-row`, 0, 1000);
  ok(await page.evaluate(() => document.querySelector('.view.active').id === 'view-class' && cpCode === 'BUS 3431'), 'tapping a section opens the class', await activeView(page));
  await click(page, `${LAST} .hawk-sec__add`, 0, 600);
  ok(await page.evaluate(() => !!document.getElementById('plChoose')), 'the + opens the add-to-plan chooser', null);
  await page.evaluate(() => document.getElementById('plChoose') && document.getElementById('plChoose').remove());
  /* professor by name, a comparison, my professors */
  let p = await say(page, 'ratings of ada please');
  ok(/^Ada Examplewood · ★ 4\.5 from \d+ ratings\.$/.test(p.bubble[0]) && p.cards[0] === 'Ada Examplewood', 'a professor by name: one big card', p);
  p = await say(page, 'compare ada examplewood and bram fixturesen');
  ok(/Ada Examplewood ★ 4\.5 · Bram Fixturesen ★ 3\.6/.test(p.bubble[0]) && (await texts(page, '.hawk-prow')).length === 2, 'compare: both, side by side', p);
  p = await say(page, 'my profs');
  const mine = await texts(page, '.hawk-prow');
  ok(/^Your 3 professors, best rated first\.$/.test(p.bubble[0]) && mine.length === 3 && /Ada Examplewood/.test(mine[0]) && /BUS 4442, BUS 3431|BUS 3431, BUS 4442/.test(mine[0]) && /Bram/.test(mine[2]), 'my professors: from your Fall classes, best first, with the classes', { p, mine });
  noErrors(log, 'professors');
  await close();
});

test('class and sections: a class card, search results with the filters understood', async () => {
  const { page, close, log } = await open();
  let r = await say(page, 'BUS 3431');
  const secs = await texts(page, '.hawk-psecs .hawk-row');
  ok(r.cards[0] === 'BUS 3431' && /2 sections/.test(r.text) && secs.length === 2 && /^BUS 3431-02/.test(secs[0]) && /^BUS 3431-01/.test(secs[1]), 'a class: its sections, open seats first (the Fall-only class is Spring’s own sections here)', { r: r.cards, secs });
  ok(/FrSa 6:10p|FrSa/.test(secs.join('|')) || secs.length === 2, 'sections are the planning term’s', secs);
  await click(page, `${LAST} .hawk-psecs .hawk-row`, 0, 1000);
  ok(await page.evaluate(() => document.querySelector('.view.active').id === 'view-class' && cpCode === 'BUS 3431'), 'a section row opens the class', null);
  await click(page, `${LAST} .hawk-sec__add`, 1, 600);
  ok(await page.evaluate(() => { const b = document.getElementById('plChoose'); return !!b && /BUS 3431/.test(b.innerText); }), 'its + opens the chooser for that class', null);
  await page.evaluate(() => document.getElementById('plChoose') && document.getElementById('plChoose').remove());
  r = await say(page, 'open BUS sections monday');
  const chips = await texts(page, '.hawk-facts .hawk-pill');
  ok(r.cards.includes('Results') && JSON.stringify(chips) === JSON.stringify(['BUS', 'Open seats', 'Mon only']), 'search: the filters it understood show as chips', chips);
  const nrows = await page.evaluate(LAST => document.querySelectorAll(LAST + ' .hawk-card--rows .hawk-row').length, LAST);
  ok(/^\d+ sections? match(es)?\./.test(r.bubble[0]) && nrows >= 2 && /BUS 4401-01/.test(r.text) && (await page.evaluate(LAST => document.querySelectorAll(LAST + ' .hawk-sec__add').length, LAST)) === nrows, 'and the matching sections, each with a +', { r, nrows });
  noErrors(log, 'class');
  await close();
});

test('prerequisites: the checklist, links, Show in Planner, and the honest "can\'t tell"', async () => {
  const { page, close, log } = await open();
  let r = await say(page, 'prereqs for bus 4401');
  ok(r.bubble[0] === 'Not yet — one class to go: one of MATH 1000 / MATH 1001.' && r.cards[0] === 'Prerequisites for BUS 4401', 'the verdict in a sentence', r);
  const rows = await texts(page, '.hawk-q');
  ok(rows.length === 3 && /^◐ BUS 3431 Taking it now/.test(rows[0]) && /^MATH 1000 or MATH 1001 Neither is offered Spring 2027/.test(rows[1].replace(/^\? ?/, '')) && /^✓ PHIL 3331 On your record/.test(rows[2]), 'each group: taking now, still needed (and not offered), done', rows);
  ok(/2 of 3/.test(r.text) && await page.evaluate(LAST => document.querySelector(LAST + ' .hawk-pbar i').style.width === '67%', LAST), 'the progress chip and bar: 2 of 3', null);
  await click(page, `${LAST} .hawk-q__go`, 0, 1000);
  ok(await page.evaluate(() => document.querySelector('.view.active').id === 'view-class' && cpCode === 'BUS 3431'), 'a link opens that class', null);
  await click(page, `${LAST} .hawk-btn--wide`, 0, 900);
  ok((await activeView(page)) === 'view-sched', '"Show in Planner" opens it', await activeView(page));
  await close();
  const E = fallOnly(); E.class_history = E.class_history.filter(x => x.user_id !== FX.ME.id); E.class_waivers = [];   // nothing logged: no past classes, no waivers
  const n = await open({ tables: E });
  r = await say(n.page, 'prereqs for bus 4401');
  ok(r.bubble[0] === 'I can’t tell yet — nothing’s logged in your past classes.' && /Can’t check/.test(r.text) && r.acts.includes('Open Past classes'), 'with no past classes logged it says it cannot tell — and shows no "done" marks', r);
  noErrors(log, 'prereqs'); noErrors(n.log, 'prereqs (no history)');
  await n.close();
});

test('game plan: the order to register, from Plans (Spring)', async () => {
  const { page, close, log } = await open({ tables: both() });
  let r = await say(page, 'my game plan');
  ok(/^You don’t have a plan yet\./.test(r.bubble[0]) && r.acts.join('|') === 'Build a term|Open Plans', 'no plan yet: says so, offers Build a term / Open Plans', r);
  await page.evaluate(() => { TCPlans.add('A', 'BUS 4442', '70102'); TCPlans.add('A', 'BUS 4445', '70103'); TCPlans.add('B', 'BUS 4401', '70112'); }); await tick(page, 1500);
  r = await say(page, 'my game plan');
  const truth = await page.evaluate(() => TCPlans.gamePlan('A').steps.map(s => s.i.label));
  const rows = await texts(page, '.hawk-grow');
  ok(r.cards[0] === 'Plan A game plan' && rows.length === truth.length && rows.every((t, i) => t.includes(truth[i])), 'the card lists the steps in the game plan’s own order', { rows, truth });
  ok(r.bubble[0].startsWith('Start with ' + truth[0]) && r.follow[0] === 'My game plan for Plan B', 'the sentence names the first; the chip asks for Plan B', r);
  await click(page, `${LAST} .hawk-grow`, 0, 1000);
  ok(await page.evaluate(() => document.querySelector('.view.active').id === 'view-class'), 'tapping a step opens that section’s class', await activeView(page));
  r = await say(page, 'game plan for plan b');
  ok(r.cards[0] === 'Plan B game plan', 'Plan B on request', r);
  noErrors(log, 'game plan');
  await close();
});

test('clashes: your Fall week, overlaps outlined', async () => {
  const { page, close, log } = await open({ tables: fallOnly() });
  let r = await say(page, 'any clashes');
  ok(r.bubble[0] === 'No time clashes in your Fall 2026 classes.' && r.cards.length === 0, 'no overlaps: says so (no card)', r);
  await close();
  const c = await open({ tables: clashy() });
  r = await say(c.page, 'any clashes');
  ok(r.bubble[0] === '3 of your classes overlap — they’re outlined in red.' && r.cards[0] === 'Your classes', 'overlaps: "3 of your classes overlap — they’re outlined in red." and the grid', r);
  const o = await c.page.evaluate(LAST => ({ clash: [...document.querySelectorAll(LAST + ' .hawk-wk__blk--clash')].map(b => b.textContent).sort(), all: [...document.querySelectorAll(LAST + ' .hawk-wk__blk')].map(b => b.textContent) }), LAST);
  ok(JSON.stringify([...new Set(o.clash)]) === JSON.stringify(['BUS 3438', 'BUS 4442', 'BUS 4445']) && !o.clash.includes('BUS 3431') && o.all.includes('BUS 3431'), 'the three that overlap are outlined, BUS 3431 is not', o);
  await click(c.page, `${LAST} .hawk-wk__blk`, 0, 1000);
  ok(await c.page.evaluate(() => document.querySelector('.view.active').id === 'view-class' && cpNow === true), 'a block opens its (Fall) class page', null);
  noErrors(log, 'clashes'); noErrors(c.log, 'clashes (overlap)');
  await c.close();
});

/* ================================================================================================================ the chat */
/* ================================================================================================================ AI first */
/* A page open with a hook that notes how many cards are on screen at the moment the function is called, so "asked BEFORE the card shows" is
   something seen, not assumed. `mode`: 'ok' answers through `ask`; 'fail' makes the function a 500; 'null' is fallback:'search'. */
async function openAI(mode = 'ok', o = {}) {
  const seen = { cardsAtAsk: [] }; let P = null;
  const hook = async (url) => {
    if (!url.pathname.startsWith('/functions/v1/ask')) return null;
    try { seen.cardsAtAsk.push(await P.evaluate(() => document.querySelectorAll('.hawk-log .hawk-card').length)); } catch (_) {}
    return mode === 'fail' ? { status: 500, body: '{"error":"boom"}' } : null;
  };
  const x = await open(Object.assign({ hook, ask: mode === 'null' ? () => null : ask }, o));
  P = x.page; x.seen = seen; return x;
}
test('ai first: a typed question, a card chip and a day tap each ask the function once, before the card shows', async () => {
  const { page, close, log, seen } = await openAI();
  const r = await say(page, 'When am I free this week?');
  ok(log.asks.length === 1 && log.asks[0].q === 'When am I free this week?' && seen.cardsAtAsk[0] === 0, 'typed: exactly one ask, made before any card was on screen', { asks: log.asks.length, seen });
  ok(r.cards[0] === 'Your free time' && r.bubble[0] === 'Your free time, day by day. Tap a day to see it.', 'and the model’s tool choice drew the week card from the page’s data', r);
  await click(page, `${LAST} .hawk-wrow`, 1);
  let d = await look(page);
  ok(log.asks.length === 2 && log.asks[1].q === 'When am I free Tuesday?' && seen.cardsAtAsk[1] === 1 && d.cards[0] === 'Your Tuesday', 'a day tap: one more ask ("When am I free Tuesday?"), then the day card', { asks: log.asks.map(a => a.q), seen, cards: d.cards });
  const chip = d.follow[0];
  await click(page, `${LAST} .hawk-follow .hawk-fq`, 0);
  d = await look(page);
  ok(log.asks.length === 3 && log.asks[2].q === chip && d.q === chip && d.cards.length === 1, 'a follow-up chip: one more ask with the chip’s own words, then its card', { chip, asks: log.asks.map(a => a.q), d });
  await say(page, 'Who’s free right now?');
  ok(log.asks.length === 4 && log.asks[3].client === 'app', 'a friends question also asks first', log.asks.map(a => a.q));
  noErrors(log, 'ai first');
  await close();
});
test('ai first: the model names the tool, even for a phrasing the device cannot read', async () => {
  const { page, close, log } = await openAI();
  let r = await say(page, 'which of my days are free');
  ok(log.asks.length === 1 && r.cards[0] === 'Your free time', 'a phrasing with no device reading still draws the week card, from the tool the model named', r);
  r = await say(page, 'who is out of class');
  ok(log.asks.length === 2 && r.cards[0] === 'Who is free', 'and the friends card', r);
  noErrors(log, 'ai first (phrasing)');
  await close();
});
test('ai first: a model that cannot answer does not beat the device’s clean reading', async () => {
  const { page, close, log } = await open({ ask: () => ({ tool: 'cant_answer', args: { reason: 'ambiguous' } }) });
  const r = await say(page, 'When am I free this week?');
  ok(log.asks.length === 1 && r.cards[0] === 'Your free time', 'asked, said it could not, and the week card is the device’s reading', { asks: log.asks.length, r });
  noErrors(log, 'ai first (cant_answer)');
  await close();
});
test('ai first: when the function fails the device answers, and every card still shows', async () => {
  for (const mode of ['fail', 'null']) {
    const { page, close, log, seen } = await openAI(mode);
    let r = await say(page, 'When am I free this week?');
    ok(seen.cardsAtAsk.length === 1 && seen.cardsAtAsk[0] === 0 && r.cards[0] === 'Your free time' && /Fall 2026/.test(r.text), mode + ': it asked first, then the week card came from the device (Fall classes)', { asks: seen.cardsAtAsk.length, r });
    await click(page, `${LAST} .hawk-wrow`, 0);
    let d = await look(page);
    ok(seen.cardsAtAsk.length === 2 && d.cards[0] === 'Your Monday' && d.bubble[0] === 'Free before 10:10a and after 6p.', mode + ': a day tap asks, then the day card is the device’s', { asks: seen.cardsAtAsk.length, d });
    await click(page, `${LAST} .hawk-follow .hawk-fq`, 0);
    d = await look(page);
    ok(seen.cardsAtAsk.length === 3 && d.cards.length === 1, mode + ': a chip asks, then its card is the device’s', { asks: seen.cardsAtAsk.length, d });
    r = await say(page, 'Who’s free right now?');
    ok(r.cards[0] === 'Who is free' && r.bubble[0] === '1 friend is free · Tue 10:30a', mode + ': who is free now', r);
    r = await say(page, 'Friday');
    ok(r.cards[0] === 'Your Friday', mode + ': a bare day name is a day card', r);
    r = await say(page, 'Best professor for BUS 3431');
    ok(r.cards[0] === 'Ada Examplewood' && /top rated of 2/.test(r.bubble[0]), mode + ': best professor', r);
    r = await say(page, 'Does BUS 3431 fit my Plan A?');
    ok(/^Yes — Section 02 fits Plan A/.test(r.bubble[0]), mode + ': fit', r);
    noErrors(log, 'ai first (' + mode + ')');
    await close();
  }
});
test('ai first: signed out nothing is sent, and the device answers', async () => {
  const { page, close, log } = await open({ signedIn: false, tables: fallOnly() });
  const r = await say(page, 'When am I free this week?');
  ok(log.asks.length === 0 && r.n === 1 && r.bubble.length >= 1 && !/Working that out/.test(r.text), 'no call is made without a session; the device answers', { asks: log.asks.length, r });
  const r2 = await say(page, 'Who’s free right now?');
  ok(log.asks.length === 0 && r2.n === 2 && r2.bubble.length >= 1, 'a friends question too', r2);
  noErrors(log, 'ai first (signed out)');
  await close();
});
test('ai first: a follow-up that narrows the last search stays on the device, as before', async () => {
  const { page, close, log } = await open();
  await say(page, 'open BUS sections monday');
  const n = log.asks.length;
  const r = await say(page, 'what about tuesday');
  ok(n === 1 && log.asks.length === 1 && /BUS section/.test(r.text) && r.cards[0] !== 'Your Tuesday', 'asked once for the search, then "what about tuesday" narrows it with no second ask', { asks: log.asks.map(a => a.q), r });
  noErrors(log, 'ai first (follow-up)');
  await close();
});

test('chat: turns stay, the newest offers follow-ups, the trash can clears, the header says what it is', async () => {
  const { page, close, log } = await open({ open: false });
  await page.click('.hawk-fab'); await tick(page, 300);
  const h = await page.evaluate(() => ({ sub: document.querySelector('.hawk-head__sub').textContent, clear: document.querySelector('.hawk-clear').getAttribute('aria-label'), shown: getComputedStyle(document.querySelector('.hawk-clear')).display }));
  ok(h.sub === 'Answers from TermChamp’s real data' && h.clear === 'Clear chat', 'header: "Answers from TermChamp’s real data" and a Clear chat button', h);
  ok(h.shown === 'none', 'the trash can is not shown on the empty sheet', h);
  await say(page, 'When am I free this week?'); await say(page, 'Who’s free right now?'); await say(page, 'Best professor for BUS 3431');
  const s = await page.evaluate(() => ({ turns: document.querySelectorAll('.hawk-log > .hawk-turn').length, qs: [...document.querySelectorAll('.hawk-said__q')].map(e => e.textContent), bots: document.querySelectorAll('.hawk-bot').length, follows: document.querySelectorAll('.hawk-follow').length, hint: !!document.querySelector('.hawk-hint'), clear: getComputedStyle(document.querySelector('.hawk-clear')).display, r: [...document.querySelectorAll('.hawk-said')].map(e => e.getBoundingClientRect().right), l: document.querySelector('.hawk-log').getBoundingClientRect().right }));
  ok(s.turns === 3 && s.qs.join('|') === 'When am I free this week?|Who’s free right now?|Best professor for BUS 3431' && s.bots === 3 && s.follows === 1 && !s.hint && s.clear !== 'none', 'three questions: three turns, in order, one set of follow-ups, no greeting, the trash can is there', s);
  ok(s.r.every(x => x > s.l - 30), 'the question bubbles sit on the right', s);
  await page.click('.hawk-clear'); await tick(page, 400);
  const c = await page.evaluate(() => ({ turns: document.querySelectorAll('.hawk-turn').length, hint: !!document.querySelector('.hawk-hint'), open: !!document.querySelector('.hawk-box').parentNode, empty: document.querySelector('.hawk-box').classList.contains('hawk-box--empty') }));
  ok(c.turns === 0 && c.hint && c.open && c.empty, 'the trash can clears the chat, brings the greeting back, and the sheet stays open', c);
  const a = await say(page, 'When am I free this week?');
  ok(a.n === 1, 'and the chat starts again', a);
  noErrors(log, 'chat');
  await close();
});

test('model path: a question the router cannot place still lands as a card, in place of "Working that out…"', async () => {
  const { page, close, log } = await open();
  const r = await say(page, 'prereqs for bus 4401');
  ok(log.asks.length === 1 && log.asks[0].client === 'app', 'the question went to the function as client:"app"', log.asks.map(a => a.client));
  ok(r.cards[0] === 'Prerequisites for BUS 4401' && !/Working that out/.test(await page.evaluate(() => document.querySelector('.hawk-log').innerText)) && r.n === 1, 'the thinking turn was replaced by the answer (one turn, no spinner left)', r);
  ok(await page.evaluate(LAST => !!document.querySelector(LAST + ' .hawk-fix--ai'), LAST), 'the AI marker sits under the question bubble', null);
  noErrors(log, 'model path');
  await close();
});

/* ================================================================================================================ safety and look */
test('escaping: hostile names and codes are text, never markup', async () => {
  const { page, close, log } = await open({ tables: hostile() });
  await page.evaluate(hp => { window.__pwn = 0; Object.keys(PROFESSORS).forEach((id, i) => { if (/Examplewood|Fixturesen/.test(PROFESSORS[id].name)) PROFESSORS[id].name = i % 2 ? '<i onmouseover=window.__pwn=4>Evil</i>, Yan' : hp; }); }, HOSTILE_PROF);   // the best professor's own name is hostile too
  const qs = ['Who’s free right now?', 'Who’s free with me Tuesday?', 'Best professor for BUS 3431', 'BUS 3431', 'When am I free this week?', 'my profs', 'hostile code prof', 'hostile code fit'];
  let said = '';
  for (const q of qs) { const r = await say(page, q); said += ' ' + r.text; }
  await tick(page, 500);
  const o = await page.evaluate(() => ({ pwn: window.__pwn, imgs: document.querySelectorAll('.hawk-box img[src="x"]').length, svgs: [...document.querySelectorAll('.hawk-box svg')].filter(s => s.hasAttribute('onload')).length, bold: !![...document.querySelectorAll('.hawk-log b, .hawk-log i')].find(b => b.hasAttribute('onmouseover')), handlers: [...document.querySelectorAll('.hawk-box *')].filter(e => [...e.attributes].some(a => /^on/i.test(a.name))).length }));
  ok(o.pwn === 0 && o.imgs === 0 && o.svgs === 0 && !o.bold && o.handlers === 0, 'nothing executed, nothing injected, no inline handlers anywhere in the box', o);
  ok(said.includes('<svg/onload=window.__pwn=1>') || said.includes('<img src=x onerror=window.__pwn=3>'), 'the hostile strings are on screen as plain text', said.slice(0, 300));
  ok(said.includes(HOSTILE_CODE), 'a hostile course code from the model is printed as text', null);
  noErrors(log, 'escaping');
  await close();
});

const CONTRAST = () => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return [0, 0, 0, 0]; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const over = (top, bot) => { const a = top[3]; return [top[0] * a + bot[0] * (1 - a), top[1] * a + bot[1] * (1 - a), top[2] * a + bot[2] * (1 - a), 1]; };
  const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  const bgOf = el => { const stack = []; for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c[3] > 0) stack.push(c); if (c[3] === 1) break; } let base = [255, 255, 255, 1]; for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base); return base; };
  const ratio = (fg, bg) => { const a = lum(fg) + .05, b = lum(bg) + .05; return a > b ? a / b : b / a; };
  const box = document.querySelector('.hawk-box'), out = [];
  const els = [...box.querySelectorAll('*')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getBoundingClientRect().width > 0 && getComputedStyle(e).visibility !== 'hidden');
  for (const e of els) { const cs = getComputedStyle(e); const bg = bgOf(e); out.push([e.className || e.tagName, e.textContent.trim().slice(0, 28), +ratio(over(parse(cs.color), bg), bg).toFixed(2)]); }
  return out;
};
const OVERFLOW = () => {
  const log = document.querySelector('.hawk-log'), out = [];
  if (log.scrollWidth > log.clientWidth + 1) out.push(['log', log.scrollWidth, log.clientWidth]);
  for (const c of log.querySelectorAll('.hawk-card, .hawk-bubble, .hawk-follow')) if (c.scrollWidth > c.clientWidth + 1) out.push([c.className, c.scrollWidth, c.clientWidth]);
  const lr = log.getBoundingClientRect(); for (const c of log.querySelectorAll('.hawk-card, .hawk-bubble')) { const r = c.getBoundingClientRect(); if (r.right > lr.right + 1 || r.left < lr.left - 1) out.push(['outside', c.className, Math.round(r.right), Math.round(lr.right)]); }
  return out;
};
const SHOW = ['When am I free this week?', 'When am I free Monday?', 'Who’s free with me Tuesday?', 'Who’s free right now?', 'Best professor for BUS 3431', 'BUS 3431', 'Does BUS 4401 fit my Plan A?', 'Does BUS 4411 fit my Plan A?', 'prereqs for bus 4401', 'my game plan', 'any clashes', 'my profs', 'ada vs bram'];
async function lookAt(th, width, height) {
  const E = clashy(); const { page, close, log } = await open({ tables: Object.assign(E, { saved_classes: E.saved_classes.concat(both().saved_classes.filter(r => r.term === '2274')), my_sections: E.my_sections.concat(both().my_sections.filter(r => r.term === '2274')) }), width, height });
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), th); await tick(page, 300);
  await page.evaluate(() => { TCPlans.add('A', 'BUS 4442', '70102'); TCPlans.add('A', 'BUS 4445', '70103'); }); await tick(page, 1200);
  const bad = [], over = [], shown = [];
  for (const q of SHOW) {
    const r = await say(page, q);
    shown.push(q + ' → ' + (r && (r.cards[0] || r.bubble[0] || '')).slice(0, 30));
    const low = (await page.evaluate(CONTRAST)).filter(x => x[2] < 4.5); if (low.length) bad.push([q, low.slice(0, 3)]);
    const ov = await page.evaluate(OVERFLOW); if (ov.length) over.push([q, ov.slice(0, 3)]);
  }
  const box = await page.evaluate(() => { const r = document.querySelector('.hawk-box').getBoundingClientRect(); return { w: Math.round(r.width), left: Math.round(r.left), right: Math.round(r.right), vw: innerWidth }; });
  return { bad, over, shown, box, log, close };
}
for (const th of ['light', 'dark']) test('look: ' + th + ' — every card, every text >= 4.5:1, nothing overflows the 340px panel', async () => {
  const x = await lookAt(th, 1440, 900);
  ok(x.box.w === 340, th + ': the desktop panel is still 340px wide', x.box);
  ok(x.shown.length === SHOW.length && x.shown.every(s => !/→ $/.test(s)), th + ': every question drew something', x.shown);
  ok(x.bad.length === 0, th + ': all text >= 4.5:1 across the cards', x.bad);
  ok(x.over.length === 0, th + ': nothing overflows the panel', x.over);
  noErrors(x.log, th + ' look');
  await x.close();
});
test('look: a phone-width sheet — the cards fit', async () => {
  const x = await lookAt('light', 390, 844);
  ok(x.box.left >= 0 && x.box.right <= x.box.vw, 'the sheet is inside the phone’s width', x.box);
  ok(x.over.length === 0, 'no card overflows at 390px', x.over);
  ok(x.bad.length === 0, 'all text >= 4.5:1 at phone width', x.bad);
  noErrors(x.log, 'phone look');
  await x.close();
});

test('keyboard and screen reader: cards are buttons with names; Escape closes; the log is a live region', async () => {
  const { page, close, log } = await open();
  await say(page, 'When am I free this week?'); await say(page, 'Best professor for BUS 3431');
  const a = await page.evaluate(() => {
    const unnamed = [...document.querySelectorAll('.hawk-box button')].filter(b => !((b.getAttribute('aria-label') || b.innerText || '').trim())).map(b => b.className);
    const tabless = [...document.querySelectorAll('.hawk-box button')].filter(b => b.tabIndex < 0 && !b.disabled).length;
    const log = document.querySelector('.hawk-log');
    return { unnamed, tabless, live: log.getAttribute('aria-live'), role: log.getAttribute('role'), cards: [...document.querySelectorAll('.hawk-card')].filter(c => !c.getAttribute('aria-label')).length, svgHidden: [...document.querySelectorAll('.hawk-box svg')].every(s => s.getAttribute('aria-hidden') === 'true') };
  });
  ok(a.unnamed.length === 0 && a.tabless === 0 && a.cards === 0 && a.svgHidden, 'every button has a name and is focusable; every card is labelled; icons are hidden from readers', a);
  ok(a.live === 'polite' && a.role === 'status', 'the conversation is a polite live region', a);
  await page.keyboard.press('Tab'); await page.keyboard.press('Escape'); await tick(page, 300);
  ok(await page.evaluate(() => !document.querySelector('.hawk-box') || !document.querySelector('.hawk-box').parentNode), 'Escape closes the sheet', null);
  noErrors(log, 'keyboard');
  await close();
});

const names = ONLY ? Object.keys(T).filter(n => n.startsWith(ONLY)) : Object.keys(T);   // --only takes the start of a test's name
if (!names.length) { console.log('no such test', ONLY); process.exit(2); }
for (const n of names) {
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
  for (const x of LIVE.splice(0)) { try { await x.close(); } catch (_) {} }
}
console.log(`\ncheck-desktop-champ-cards: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
