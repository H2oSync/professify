/* check-desktop-hawk-menu — Hawk gets the app's menu on the website (website-hawk-app-menu, Tate 2026-10-13/14: Hawk sends
   client:'app'). Runs the REAL index.html + hawk-ask.js in Chromium, signed in; the harness `ask:` option stands in for the
   edge function (which this slice does not touch).
   Run: APP_DIR=<repo> node check-desktop-hawk-menu.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: the model tier sends client:'app'; the five tools the phone added answer here — who's free now, free with a
   friend, the best professor for a class, whether a class fits a plan (as cards since 2026-10-15; see check-desktop-champ-cards for
   every card), and the sixteen help topics (still a sentence and a row) — each part opens the friend / professor / class / screen
   it names; nothing is guessed (a missing rating shows none). */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 400) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const T = {};
const test = (name, fn) => { T[name] = fn; };
/* what the stand-in function answers: the tool the question is mapped to */
const TOOLS = {};
const ask = body => (TOOLS[body.q] ? { tool: TOOLS[body.q][0], args: TOOLS[body.q][1] } : { tool: 'cant_answer', args: { reason: 'not_about_classes' } });
const open = async o => { const x = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, ask }, o)); await tick(x.page, 2500); await x.page.evaluate(() => loadFriendsData()); await tick(x.page, 1500); return x; };
/* 2026-10-15 (website-champ-cards): Champ is a chat now and the five tools answer as cards. `say` reads the NEWEST turn only: the
   bubble's notes, the section/class rows, and the card parts (friend rows, professor rows). Every question goes to the function
   first (AI-first, owner 2026-10-15), which is what proves client:'app' for all five tools. */
const say = async (page, q) => { await page.evaluate(q => HawkAsk.ask(q), q); await tick(page, 1500); return page.evaluate(() => { const t = [...document.querySelectorAll('.hawk-log > .hawk-turn')].pop(); const tx = e => (e.innerText || '').replace(/\s+/g, ' ').trim(); return { notes: [...t.querySelectorAll('.hawk-bubble .hawk-note')].map(n => n.textContent), rows: [...t.querySelectorAll('.hawk-row')].map(r => ({ name: (r.querySelector('.hawk-row__name') || {}).textContent, sub: (r.querySelector('.hawk-row__sub') || {}).textContent || '', code: (r.querySelector('.hawk-row__code') || {}).textContent || '', chip: (r.querySelector('.hawk-chip') || {}).textContent || '' })), friends: [...t.querySelectorAll('.hawk-fr')].map(f => ({ name: tx(f.querySelector('.hawk-fr__tx b')), sub: tx(f.querySelector('.hawk-fr__tx span')), free: f.classList.contains('hawk-fr--free') })), profs: [...t.querySelectorAll('.hawk-ptop, .hawk-prow')].map(p => ({ name: tx(p.querySelector('b')), pill: tx(p.querySelector('.hawk-pill, .hawk-ptop__avg b')) })), card: (t.querySelector('.hawk-card') || { getAttribute: () => null }).getAttribute('aria-label'), acts: [...t.querySelectorAll('.hawk-act')].map(tx), text: tx(t) }; }); };
const clickRow = async (page, i) => { await page.evaluate(i => document.querySelectorAll('.hawk-log > .hawk-turn:last-child .hawk-row')[i].click(), i); await tick(page, 700); };
const clickSel = async (page, sel, i = 0) => { await page.evaluate(([s, i]) => document.querySelectorAll('.hawk-log > .hawk-turn:last-child ' + s)[i].click(), [sel, i]); await tick(page, 800); };

TOOLS['who is free right now'] = ['friends_free_now', {}];
TOOLS['is avery free right now'] = ['free_with_friends', { friend: 'Avery' }];
TOOLS['best prof for bus 3431'] = ['best_professor', { course: 'BUS3431' }];
TOOLS['does bus 4401 fit plan a'] = ['fits_plan', { course: 'BUS4401', plan: 'A' }];
TOOLS['does bus 4401 fit plan b'] = ['fits_plan', { course: 'BUS4401', plan: 'B' }];
TOOLS['is termchamp free'] = ['app_help', { topic: 'free' }];
TOOLS['how do i contact termchamp'] = ['app_help', { topic: 'contact' }];
TOOLS['what does termchamp do about stuff'] = ['app_help', { topic: 'made_up_topic' }];

test('freeNow', async () => {
  const { page, close, log } = await open();
  const r = await say(page, 'who is free right now');
  ok(log.asks.length >= 1 && log.asks.every(a => a.client === 'app'), 'the question goes to the function as client:"app"', log.asks.map(a => a.client));
  const truth = await page.evaluate(() => friendsList.map(f => ({ name: f.name, st: avState(avMeetsOf(f), new Date()).state })));
  const freeNames = truth.filter(x => x.st === 'open').map(x => x.name.split(' ')[0]).sort(), unk = truth.filter(x => x.st === 'unknown').length;
  const shown = r.friends.filter(x => x.free).map(x => x.name).sort();
  ok(JSON.stringify(shown) === JSON.stringify(freeNames), 'friends_free_now: a free row per friend who is free right now — and only them', { shown, freeNames });
  ok(r.card === 'Who is free' && (freeNames.length ? /friends? (is|are) free · /.test(r.notes[0]) : /None of your friends/.test(r.notes[0])), 'friends_free_now: the first line says who', r.notes);
  if (unk && freeNames.length) ok(r.notes.some(n => /no times I can read/.test(n)), 'friends_free_now: friends with no readable times are counted, not guessed', r.notes);
  if (shown.length) {
    await clickSel(page, '.hawk-fr__main', 0);
    ok(await page.evaluate(() => !!document.querySelector('#frpBack.open')), 'friends_free_now: a row opens that friend’s profile', null);
  }
  ok(log.errors.length === 0, 'freeNow: no page errors', log.errors);
  await close();
});

test('freeWith', async () => {
  const { page, close, log } = await open();
  const r = await say(page, 'is avery free right now');
  const name = await page.evaluate(() => (friendsList.find(f => /^Avery/.test(f.name)) || {}).name || null);
  ok(!!name && /^Avery: /.test(r.notes[0]) && r.acts.join('|') === 'Message Avery|Open Avery', 'free_with_friends: one friend named — where they are, with Message and Open', { name, r });
  await clickSel(page, '.hawk-act', 1);
  ok(await page.evaluate(() => !!document.querySelector('#frpBack.open')), 'free_with_friends: Open opens their profile', null);
  ok(log.errors.length === 0, 'freeWith: no page errors', log.errors);
  await close();
});

test('bestProf', async () => {
  const { page, close, log } = await open();
  const r = await say(page, 'best prof for bus 3431');
  const want = await page.evaluate(() => { const by = {}; (SEAT_SECTIONS['BUS 3431'] || []).forEach(x => { const id = matchProfId(x.instructor); if (id) by[PROFESSORS[id].name] = to5(PROFESSORS[id].rating); }); return Object.entries(by).sort((a, b) => b[1] - a[1]); });
  ok(r.profs.length === want.length && JSON.stringify(r.profs.map(x => x.name)) === JSON.stringify(want.map(x => x[0])), 'best_professor: the professors teaching BUS 3431, best-rated first (big card, then Also teaching)', { got: r.profs.map(x => x.name), want });
  ok(r.profs.every((x, i) => x.pill.includes(want[i][1].toFixed(1))), 'best_professor: each carries their rating', r.profs);
  await clickSel(page, '.hawk-ptop', 0);
  ok(await page.evaluate(() => document.querySelector('.view.active').id === 'view-prof'), 'best_professor: the card opens the professor', null);
  ok(log.errors.length === 0, 'bestProf: no page errors', log.errors);
  await close();
});

test('fitsPlan', async () => {
  const { page, close, log } = await open();
  await tick(page, 3000);
  await page.evaluate(() => { TCPlans.add('A', 'BUS 3438', '70104'); }); await tick(page, 1500);
  let r = await say(page, 'does bus 4401 fit plan a');
  ok(r.notes[0] === 'No — every BUS 4401 section clashes with Plan A.' && /Clashes with BUS 3438/.test(r.text), 'fits_plan: BUS 4401 (MoWe 10:10) clashes with Plan A’s BUS 3438 — the card says so', r);
  r = await say(page, 'does bus 4401 fit plan b');
  ok(/^Yes — Section 01 fits Plan B\./.test(r.notes[0]) && /No clashes/.test(r.text) && /Fixturesen/.test(r.text), 'fits_plan: it fits the empty Plan B — the section is on the card', r);
  await clickSel(page, '.hawk-btn--soft', 0);
  ok(await page.evaluate(() => document.querySelector('.view.active').id === 'view-class' && cpCode === 'BUS 4401'), 'fits_plan: the card opens that class’s page', null);
  ok(log.errors.length === 0, 'fitsPlan: no page errors', log.errors);
  await close();
});

test('appHelp', async () => {
  const { page, close, log } = await open();
  let r = await say(page, 'is termchamp free');
  ok(r.notes.length === 1 && /TermChamp is free/.test(r.notes[0]) && r.rows.length === 1 && r.rows[0].name === 'Privacy policy', 'app_help: the answer in a sentence and a Go-there row', r);
  await clickRow(page, 0);
  ok(await page.evaluate(() => !!document.querySelector('.view.active') && /privacy/i.test(document.body.innerText.slice(0, 200000)) ), 'app_help: the row goes to the screen', null);
  r = await say(page, 'how do i contact termchamp');
  ok(/support@termchamp\.com/.test(r.notes[0] || '') && r.rows[0].name === 'Email support', 'app_help: contact says the address', r);
  r = await say(page, 'what does termchamp do about stuff');
  ok(r.notes.length === 1 && /not sure which question/.test(r.notes[0]) && r.rows.length === 0, 'app_help: a topic that is not one of the sixteen is not answered on a guess', r);
  ok(log.errors.length === 0, 'appHelp: no page errors', log.errors);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-hawk-menu: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
