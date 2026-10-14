/* check-desktop-explore-term — Explore's Fall / Spring switch on the website (website-explore-term, Tate 2026-10-14).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in of check-app.
   Run: APP_DIR=<repo> node check-desktop-explore-term.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises (the phone's, explore-term-switch 2026-10-10): while there are two terms Explore shows "Spring 2027 | Fall 2026",
   always starting on Spring; Fall reads the now term's whole seat feed once, on demand, into a store of its own (never
   SEAT_SECTIONS / PROFESSIFY_SEATS, never the seats cache); the rows, the class page and a professor's "teaching" read the
   chosen term; Fall is read-only (nothing is written, and the control says so); a Fall class opened from Home is the Fall page. */
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
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const T = {};
const test = (name, fn) => { T[name] = fn; };
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
/* Spring = Fall's rows re-termed; BUS 3438 is Fall-only, BUS 3431's Spring sections meet FrSa 6:10PM (Fall: MoWe 4:10PM) */
function springTables() {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const spring = T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }, r.course_code === 'BUS 3431' ? { days: 'FrSa 6:10PM - 9:00PM' } : {}));
  T.course_seats = T.course_seats.concat(spring);
  return T;
}
const search = async (page, q) => { await page.evaluate(q => { show('explore'); const i = document.getElementById('exQuery'); i.value = q; onExSearch(); }, q); await tick(page, 500); };
const exText = page => page.evaluate(() => document.getElementById('exOut').innerText);
const fullFallReads = log => log.reads.map(r => decodeURIComponent(r)).filter(r => /^course_seats\?term=eq\.2268/.test(r) && !/course_code=in\./.test(r));
const clickTerm = (page, t) => page.evaluate(t => document.querySelector('#exContext .ex-term[data-term="' + t + '"]').click(), t);

test('single', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500);
  await page.evaluate(() => { show('explore'); renderExContext(); }); await tick(page, 400);
  ok((await page.$$('#exContext .ex-term')).length === 0, 'single term: no term switch in Explore');
  ok(log.errors.length === 0, 'single term: no page errors', log.errors);
  await close();
});

test('switch', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  await page.evaluate(() => { show('explore'); renderExContext(); }); await tick(page, 600);
  const sw = () => page.evaluate(() => [...document.querySelectorAll('#exContext .ex-term')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')).join('|'));
  ok(await sw() === 'Spring 2027*|Fall 2026', 'switch: Spring 2027 | Fall 2026, starting on Spring', await sw());
  ok(fullFallReads(log).length === 0, 'switch: nothing of Fall’s feed is read until it is asked for', fullFallReads(log));
  await search(page, 'BUS 3431');
  const spRows = await page.evaluate(() => [...document.querySelectorAll('#exOut .cls-row')].map(r => r.innerText).join(' || '));
  ok(/BUS 3431/.test(spRows) && !/friend taking it/.test(spRows), 'spring: BUS 3431 is listed, with no friend in it', spRows.slice(0, 200));
  const cacheBefore = await page.evaluate(() => localStorage.getItem('professify_seats_cache:2274'));
  const nBefore = await page.evaluate(() => { window.__ss = SEAT_SECTIONS; window.__ps = PROFESSIFY_SEATS; return Object.keys(SEAT_SECTIONS).length; });
  await clickTerm(page, 'now'); await tick(page, 1500);
  ok(await sw() === 'Spring 2027|Fall 2026*', 'switch: Fall 2026 is now lit', await sw());
  ok(fullFallReads(log).length === 1, 'fall: the now term’s whole feed is read once, on demand', fullFallReads(log));
  const st = await page.evaluate(() => ({ same: SEAT_SECTIONS === window.__ss && PROFESSIFY_SEATS === window.__ps, has38: !!SEAT_SECTIONS['BUS 3438'], fall38: !!(FALL.sec && FALL.sec['BUS 3438']), n: Object.keys(SEAT_SECTIONS).length,
    keys: Object.keys(localStorage).filter(k => /^professify_seats_cache/.test(k)), cache: localStorage.getItem('professify_seats_cache:2274') }));
  ok(st.same && !st.has38 && st.fall38 && st.n === nBefore, 'fall: Spring’s SEAT_SECTIONS / PROFESSIFY_SEATS are untouched; Fall sits in its own store', st);
  ok(!st.keys.includes('professify_seats_cache:2268') && st.cache === cacheBefore, 'fall: the seats cache is not written for Fall and Spring’s is unchanged', st.keys);
  await search(page, 'BUS 3438');
  ok(/BUS 3438/.test(await exText(page)), 'fall: BUS 3438 (Fall-only) is listed in Explore', (await exText(page)).slice(0, 200));
  await search(page, 'BUS 3431');
  const rows = await page.evaluate(() => [...document.querySelectorAll('#exOut .cls-row')].map(r => r.innerText).join(' || '));
  ok(/BUS 3431/.test(rows) && /1 friend taking it/.test(rows), 'fall: rows read Fall — BUS 3431 shows the friend who is in it now (nobody is in it in Spring)', rows.slice(0, 300));
  await clickTerm(page, 'spring'); await tick(page, 600);
  await search(page, 'BUS 3438');
  const sp = await page.evaluate(() => ({ rows: document.querySelectorAll('#exOut .cls-row[data-code="BUS 3438"]').length, txt: document.getElementById('exOut').innerText }));
  ok(/No section data this term/.test(sp.txt), 'spring: BUS 3438 has no Spring sections (Fall’s are not in the Spring list)', sp.txt.slice(0, 200));
  ok(await page.evaluate(() => !SEAT_SECTIONS['BUS 3438'] && SEAT_SECTIONS === window.__ss), 'spring: back on Spring, the globals are Spring’s', null);
  await clickTerm(page, 'now'); await tick(page, 600);
  ok(fullFallReads(log).length === 1, 'fall: switching back and forth reads the feed once', fullFallReads(log).length);
  ok(log.errors.length === 0, 'switch: no page errors', log.errors);
  await close();
});

test('classPage', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  await page.evaluate(() => { show('explore'); renderExContext(); }); await tick(page, 400);
  await page.evaluate(() => exSetTerm('now')); await tick(page, 1500);
  await page.evaluate(() => openClassPage('BUS 3438')); await tick(page, 600);
  let cp = await page.evaluate(() => ({ secs: document.querySelectorAll('#cpOut .cp-sec').length, note: (document.querySelector('#cpOut .cp-fallnote') || {}).innerText || '', txt: document.getElementById('cpOut').innerText, now: cpNow }));
  ok(cp.now && cp.secs === 1 && /Fall 2026/.test(cp.note) && /read-only/.test(cp.note), 'class page: opened from Explore on Fall it is the Fall page (BUS 3438: 1 section, read-only note)', cp);
  ok(/Bram|Fixturesen/.test(cp.txt) && /10:10/.test(cp.txt), 'class page: shows Fall’s section and professor', cp.txt.slice(0, 300));
  log.writes.length = 0;
  await page.evaluate(() => { document.querySelector('#cpOut .cp-c4 button, #cpOut .cp-save').click(); }); await tick(page, 600);
  const toast = await page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '');
  ok(toast === 'Fall 2026 is read-only — switch to Spring 2027 to add' && log.writes.length === 0, 'class page: an Add / Watch control says Fall is read-only and writes nothing', { toast, w: log.writes.length });
  const nb = await page.evaluate(() => { let n = 0; document.querySelectorAll('#cpOut button').forEach(b => { if (/mcEnrollSec|wcWatchSec|toggleSaveClass|data-pl-act/.test(b.outerHTML) && !/data-pl-act="open"/.test(b.outerHTML)) { n++; b.click(); } }); return n; }); await tick(page, 600);
  ok(nb > 0 && log.writes.length === 0, 'class page: no write on any Fall control', { nb, w: log.writes.map(w => w.table) });
  await page.evaluate(() => cpViewSpring()); await tick(page, 500);
  cp = await page.evaluate(() => ({ secs: document.querySelectorAll('#cpOut .cp-sec').length, note: !!document.querySelector('#cpOut .cp-fallnote') }));
  ok(cp.secs === 0 && !cp.note, 'class page: “View Spring 2027” is the Spring page — no sections for a Fall-only class', cp);
  await page.evaluate(() => { show('explore'); openClassPage('BUS 3431'); }); await tick(page, 600);
  const f31 = await page.evaluate(() => document.getElementById('cpOut').innerText);
  await page.evaluate(() => cpViewSpring()); await tick(page, 500);
  const s31 = await page.evaluate(() => document.getElementById('cpOut').innerText);
  ok(/4:10/.test(f31) && !/6:10/.test(f31) && /6:10/.test(s31), 'class page: Fall BUS 3431 meets 4:10; Spring BUS 3431 meets 6:10', { f: f31.slice(0, 160), s: s31.slice(0, 160) });
  ok(log.errors.length === 0, 'class page: no page errors', log.errors);
  await close();
});

test('professor', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  await page.evaluate(() => { show('explore'); renderExContext(); }); await tick(page, 400);
  const pid = await page.evaluate(() => matchProfId('Fixturesen, Bram'));
  ok(!!pid, 'professor: Bram Fixturesen is a known professor', pid);
  await page.evaluate(id => openProf(id), pid); await tick(page, 800);
  let p = await page.evaluate(() => ({ h: [...document.querySelectorAll('#pfOut .pp-sec h3')].map(x => x.textContent), t: [...document.querySelectorAll('#pfOut .pp-row')].map(x => x.innerText).join(' | ') }));
  ok(p.h.some(x => /^Teaching this term/.test(x)) && !/BUS 3438/.test(p.t), 'professor: on Spring they teach Spring’s classes (no BUS 3438)', p.h);
  await page.evaluate(() => { show('explore'); exSetTerm('now'); }); await tick(page, 1500);
  await page.evaluate(id => openProf(id), pid); await tick(page, 800);
  p = await page.evaluate(() => ({ h: [...document.querySelectorAll('#pfOut .pp-sec h3')].map(x => x.textContent), t: document.getElementById('pfOut').innerText, pn: pfNow }));
  ok(p.pn && p.h.some(x => /^Teaching Fall 2026/.test(x)) && /BUS 3438/.test(p.t), 'professor: opened from Explore on Fall, “Teaching Fall 2026” lists BUS 3438', p);
  await page.evaluate(() => { document.querySelector('#pfOut .pp-row[onclick*="BUS 3438"]').click(); }); await tick(page, 600);
  const cp = await page.evaluate(() => ({ now: cpNow, secs: document.querySelectorAll('#cpOut .cp-sec').length }));
  ok(cp.now && cp.secs === 1, 'professor: a Fall class from their page opens its Fall page', cp);
  ok(log.errors.length === 0, 'professor: no page errors', log.errors);
  await close();
});

test('home', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  await page.evaluate(() => loadFriendsData()); await tick(page, 1500);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 800);
  await page.evaluate(() => openClassFromFeed('BUS 3438')); await tick(page, 1800);
  const cp = await page.evaluate(() => ({ now: cpNow, secs: document.querySelectorAll('#cpOut .cp-sec').length, note: !!document.querySelector('#cpOut .cp-fallnote'), view: document.querySelector('.view.active').id }));
  ok(cp.view === 'view-class' && cp.now && cp.secs === 1 && cp.note, 'home: a Fall class opened from Home is its Fall page (sections shown, read-only)', cp);
  await page.evaluate(() => { show('home'); openClassFromFeed('BUS 4401'); }); await tick(page, 600);
  ok(await page.evaluate(() => !cpNow), 'home: a class nobody is in now opens Spring’s page', null);
  await page.evaluate(id => openFriendProfile(id), FX.FRIENDS[0].id); await tick(page, 600);
  await page.evaluate(() => setFrpTerm('now')); await tick(page, 400);
  await page.evaluate(() => gotoSection('BUS 3438')); await tick(page, 1500);
  ok(await page.evaluate(() => cpNow && document.querySelectorAll('#cpOut .cp-sec').length === 1), 'friend page: a class on their Fall chip opens the Fall page', null);
  await page.evaluate(() => { show('explore'); }); await tick(page, 300);
  await page.evaluate(id => openFriendProfile(id), FX.FRIENDS[0].id); await tick(page, 600);
  await page.evaluate(() => setFrpTerm('term')); await tick(page, 400);
  await page.evaluate(() => gotoSection('BUS 4401')); await tick(page, 600);
  ok(await page.evaluate(() => !cpNow), 'friend page: on their Spring chip a class opens Spring’s page', null);
  ok(log.errors.length === 0, 'home: no page errors', log.errors);
  await close();
});

test('failure', async () => {
  const { page, close } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  await page.evaluate(() => {
    show('explore'); renderExContext(); window.__realFetch = window.fetch;
    window.fetch = (u, o) => (/course_seats\?term=eq\.2268/.test(String(u)) && !/course_code=in/.test(String(u))) ? Promise.resolve(new Response('[]', { status: 500 })) : window.__realFetch(u, o);
  });
  await page.evaluate(() => exSetTerm('now')); await tick(page, 1200);
  const t = await exText(page);
  ok(/Couldn.t load Fall 2026/.test(t) && !!(await page.$('#exOut button[onclick="fallRetry()"]')), 'failure: a failed read says so and offers Retry (never an empty Fall)', t.slice(0, 200));
  await page.evaluate(() => { window.fetch = window.__realFetch; fallRetry(); }); await tick(page, 1500);
  ok(await page.evaluate(() => FALL.ready), 'failure: Retry loads it', null);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-explore-term: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
