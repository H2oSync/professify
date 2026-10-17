/* check-desktop-term-fix — semester transition (term-fix, 2026-10-16).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in of check-app.
   Run: APP_DIR=<repo> APP_PORT=8517 node check-desktop-term-fix.mjs [--only name] [--quiet]
   The promises: the Explore right rail ("Saved classes", "Still need") shows seats of the term Explore is on (Spring 2027), never
   a printed "0 left" for a class whose seat counts the scrape did not carry; a class with no sections that term says
   "Not offered Spring 2027"; the same wording holds in the class badges; there is no Winter term; nothing says "quarter"
   about the present. */
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
const PORT = process.env.APP_PORT || 8517;
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, port: +PORT }, o));
const T = {};
const test = (name, fn) => { T[name] = fn; };
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };

let nbr = 81000;
/* a section row: counts is [capacity, enrolled, available] or null for "the scrape did not carry the counts" */
const row = (term, code, section, status, counts, wl = 0) => ({
  term, course_code: code, title: 'Fixture ' + code, section, instructor: 'Fixturesen, Bram', days: 'MoWe 10:10AM - 12:00PM', status,
  capacity: counts ? counts[0] : null, enrolled: counts ? counts[1] : null, available: counts ? counts[2] : null,
  waitlist_total: wl, waitlist_capacity: counts ? 10 : null, class_nbr: String(nbr++), instruction_mode: 'P', location: 'Bldg 03-0112',
});
/* Fall 2026 (2268): every class full, as it is mid-semester. Spring 2027 (2274): registration has not opened. */
function tables() {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const fall = c => row('2268', c, '01', 'Closed', [40, 40, 0]);
  const rows = [
    ['BUS 4461', 'sp-null'], ['BUS 4448', 'sp-counts'], ['BUS 3392', 'fall-only'], ['BUS 3347', 'sp-zero-open'],
    ['BUS 4465', 'sp-partial'], ['ECON 2001', 'sp-big'], ['BUS 3306', 'sp-closed'], ['BUS 3411', 'sp-wait'],
  ];
  const out = [];
  rows.forEach(([c, k]) => {
    out.push(fall(c));
    if (k === 'sp-null') { out.push(row('2274', c, '01', 'Open', null)); }                              /* listing only: status, no counts */
    if (k === 'sp-counts') { out.push(row('2274', c, '01', 'Open', [30, 0, 30]), row('2274', c, '02', 'Open', [30, 4, 26])); }
    if (k === 'sp-zero-open') { out.push(row('2274', c, '01', 'Open', [30, 0, 0])); }               /* Open, but the available count is 0: contradicts itself */
    if (k === 'sp-partial') { out.push(row('2274', c, '01', 'Open', [30, 0, 30]), row('2274', c, '02', 'Open', null)); }
    if (k === 'sp-big') { out.push(row('2274', c, '01', 'Open', [300, 0, 300]), row('2274', c, '02', 'Open', [220, 6, 214])); }
    if (k === 'sp-closed') { out.push(row('2274', c, '01', 'Closed', [40, 40, 0])); }
    if (k === 'sp-wait') { out.push(row('2274', c, '01', 'Wait List', [40, 40, 0], 3)); }
  });
  T.course_seats = T.course_seats.concat(out);
  return T;
}
const railRows = page => page.evaluate(() => {
  const o = {};
  document.querySelectorAll('#exRail .ex-mod').forEach(m => {
    const h = (m.querySelector('h3') || {}).textContent || '';
    o[h] = [...m.querySelectorAll('.exm-row')].map(r => ({ code: (r.querySelector('b') || {}).textContent, num: (r.querySelector('.num') || {}).textContent || '', cls: (r.querySelector('.num') || { className: '' }).className }));
  });
  return o;
});
const SAVED = ['BUS 4461', 'BUS 4448', 'BUS 3392', 'BUS 3347', 'BUS 4465'];

async function setup(opts = {}) {
  const app = await desk(Object.assign({ terms: SPRING_CFG, tables: tables() }, opts)); const { page } = app; await tick(page, 2500);
  await page.evaluate(saved => {
    watchClasses = saved.slice(); try { renderWatchClasses(); } catch (e) {}
    myHistory = [{ code: 'BUS 1000', term: 'Fall', year: 2025 }];
    window.plLedgerCompute = () => ({ led: { need: [{ codes: ['ECON 2001'], group: 'ge' }, { codes: ['BUS 3306'], group: 'major' }, { codes: ['BUS 3411'], group: 'major' }], needU: [] } });
    window.schoolLive = () => true;
    show('explore'); renderExplore();
  }, SAVED);
  await tick(page, 800);
  return app;
}

test('rail', async () => {
  const { page, close, log } = await setup();
  const r = await railRows(page);
  const sv = r['Saved classes'] || [], sn = r['Still need'] || [];
  const by = (a, c) => (a.find(x => x.code === c) || { num: '<missing>' }).num;
  ok(sv.length === 5, 'rail: five saved classes listed', sv);
  ok(!sv.some(x => /^0 left/.test(x.num)) && !sn.some(x => /^0 left/.test(x.num)), 'rail: no row says "0 left"', { sv, sn });
  ok(by(sv, 'BUS 4461') === 'open', 'rail: Spring sections with no seat counts say "open", not "0 left"', by(sv, 'BUS 4461'));
  ok(by(sv, 'BUS 4448') === '56 left', 'rail: Spring counts are summed (30 + 26 = 56 left)', by(sv, 'BUS 4448'));
  ok(/^Not offered Spring 2027$/.test(by(sv, 'BUS 3392')) && (sv.find(x => x.code === 'BUS 3392') || {}).cls.indexOf('faint') >= 0, 'rail: a class with no Spring sections (Fall has them) says "Not offered Spring 2027", muted', sv.find(x => x.code === 'BUS 3392'));
  ok(by(sv, 'BUS 3347') === 'open', 'rail: an Open section whose available count is 0 says "open", never "0 left"', by(sv, 'BUS 3347'));
  ok(by(sv, 'BUS 4465') === 'open', 'rail: partly counted sections do not print a partial total', by(sv, 'BUS 4465'));
  ok(by(sn, 'ECON 2001') === '514 left', 'rail: Still need — ECON 2001 shows 514 left', by(sn, 'ECON 2001'));
  ok(by(sn, 'BUS 3306') === 'full', 'rail: Still need — a Closed Spring class says full', by(sn, 'BUS 3306'));
  ok(/waiting|waitlist/.test(by(sn, 'BUS 3411')), 'rail: Still need — a waitlisted Spring class says so', by(sn, 'BUS 3411'));
  ok(log.errors.length === 0, 'rail: no page errors', log.errors);
  await close();
});

test('feedNotUp', async () => {
  const { page, close } = await setup();
  const r = await page.evaluate(() => { const a = [SEAT_SECTIONS, PROFESSIFY_SEATS]; SEAT_SECTIONS = null; PROFESSIFY_SEATS = null; renderExploreRail();
    const o = [...document.querySelectorAll('#exRail .exm-row .num')].map(x => x.textContent); SEAT_SECTIONS = a[0]; PROFESSIFY_SEATS = a[1]; renderExploreRail(); return o; });
  ok(!r.some(x => /Not offered|left/.test(x)), 'feed not loaded yet: the rail claims nothing (no "Not offered", no count)', r);
  await close();
});

test('fallChip', async () => {
  const { page, close } = await setup(); await tick(page, 300);
  await page.evaluate(() => { renderExContext(); exSetTerm('now'); }); await tick(page, 1500);
  const r = await railRows(page); const sv = r['Saved classes'] || [];
  ok(sv.length === 0 || sv.every(x => !/^0 left/.test(x.num)), 'Fall chip: the rail never says "0 left"', sv);
  const bad = sv.find(x => x.code === 'BUS 3392');
  ok(!bad || /Not offered Spring 2027/.test(bad.num), 'Fall chip: the rail is still Spring’s (a Fall-only class is "Not offered Spring 2027")', bad);
  await close();
});

test('staleCache', async () => {
  /* a cache written by the previous build has no avN: the first paint must not turn it into "0 left" */
  const { page, close } = await setup();
  const r = await page.evaluate(() => { const idx = JSON.parse(JSON.stringify(PROFESSIFY_SEATS)); Object.values(idx).forEach(a => delete a.avN); PROFESSIFY_SEATS = idx; renderExploreRail();
    return [...document.querySelectorAll('#exRail .exm-row .num')].map(x => x.textContent); });
  ok(!r.some(x => /^0 left/.test(x)), 'old cache (no avN): still no "0 left"', r);
  await close();
});

test('badges', async () => {
  const { page, close } = await setup();
  const r = await page.evaluate(() => ({
    nul: seatBadge(realSeat('BUS 4461')), counted: seatBadge(realSeat('BUS 4448')), zero: seatBadge(realSeat('BUS 3347')),
    sec: (clsSections('BUS 3347')[0] || {}).seat, conc: concAvail('BUS 4448') }));
  ok(r.nul === 'Open', 'badge: Open with no counts reads "Open", not "0 open"', r.nul);
  ok(/^56\/\d+ open/.test(r.counted), 'badge: counted sections read "56/60 open"', r.counted);
  ok(r.zero === 'Open' && r.sec && r.sec.n === null, 'badge: an Open section with 0 available is a count we do not have', r);
  ok(/Spring 2027/.test(r.conc) && !/Fall 2026/.test(r.conc), 'concentration availability names the chosen term (Spring 2027), not a literal Fall 2026', r.conc);
  await close();
});

test('classPageRow', async () => {
  const { page, close } = await setup();
  await page.evaluate(() => { openClassPage('BUS 4461'); }); await tick(page, 700);
  const t = await page.evaluate(() => document.getElementById('cpOut').innerText);
  ok(!/\b0 open\b|\b0 left\b|0\/\d+ open/.test(t), 'class page: a class with no seat counts never shows "0 open"', t.slice(0, 300));
  await close();
});

test('semesterTerms', async () => {
  /* once Spring 2027 is the term you are in: rate-a-professor offers Spring 2027, Fall 2026, Summer 2026, Spring 2026 - never Winter 2027 */
  const { page, close } = await desk({ terms: { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2274', NOW_LABEL: 'Spring 2027' }, tables: tables() }); await tick(page, 2500);
  const o = await page.evaluate(() => ({
    spring: rateTermOptions(4), summer27: (() => { const f = mcNowLabel; window.mcNowLabel = () => 'Summer 2027'; const r = rateTermOptions(4); window.mcNowLabel = f; return r; })(),
    fall27: (() => { const f = mcNowLabel; window.mcNowLabel = () => 'Fall 2027'; const r = rateTermOptions(5); window.mcNowLabel = f; return r; })(),
    fall26: (() => { const f = mcNowLabel; window.mcNowLabel = () => 'Fall 2026'; const r = rateTermOptions(5); window.mcNowLabel = f; return r; })(),
    next: [termNext({ term: 'Fall', year: 2026 }), termNext({ term: 'Spring', year: 2027 }), termNext({ term: 'Fall', year: 2027 })],
    prev: [termPrev({ term: 'Spring', year: 2027 }), termPrev({ term: 'Fall', year: 2027 })],
    sys: [termSystemWord({ term: 'Fall', year: 2026 }), termSystemWord({ term: 'Summer', year: 2026 }), termSystemWord({ term: 'Spring', year: 2027 })],
    now: [termNowLabel(new Date(2027, 0, 10)), termNowLabel(new Date(2026, 9, 16))],
    last: termsBack(3).map(t => t.term + ' ' + t.year) }));
  ok(JSON.stringify(o.spring) === JSON.stringify(['Spring 2027', 'Fall 2026', 'Summer 2026', 'Spring 2026']), 'terms: from Spring 2027 the rate form offers Spring 2027, Fall 2026, Summer 2026, Spring 2026', o.spring);
  ok(JSON.stringify(o.summer27) === JSON.stringify(['Summer 2027', 'Spring 2027', 'Fall 2026', 'Summer 2026']), 'terms: from Summer 2027 it goes Spring 2027, Fall 2026', o.summer27);
  ok(JSON.stringify(o.fall27) === JSON.stringify(['Fall 2027', 'Summer 2027', 'Spring 2027', 'Fall 2026', 'Summer 2026']), 'terms: Fall 2027 steps back through Summer and Spring to Fall 2026', o.fall27);
  ok(JSON.stringify(o.fall26) === JSON.stringify(['Fall 2026', 'Summer 2026', 'Spring 2026', 'Winter 2026', 'Fall 2025']), 'terms: Winter 2026 still exists in the quarter era', o.fall26);
  ok(![o.spring, o.summer27, o.fall27].some(a => a.some(x => /Winter 20(2[7-9]|[3-9]\d)/.test(x))), 'terms: no Winter 2027 or later is ever offered', o);
  ok(o.next[0].term === 'Spring' && o.next[0].year === 2027 && o.next[1].term === 'Fall' && o.next[2].term === 'Spring' && o.next[2].year === 2028, 'terms: termNext walks Fall 2026 -> Spring 2027 -> Fall 2027 -> Spring 2028', o.next);
  ok(o.prev[0].term === 'Fall' && o.prev[0].year === 2026 && o.prev[1].term === 'Spring' && o.prev[1].year === 2027, 'terms: termPrev walks Spring 2027 -> Fall 2026; Fall 2027 -> Spring 2027', o.prev);
  ok(o.sys.join() === 'semester,quarter,semester', 'terms: Fall 2026 and Spring 2027 are semesters, Summer 2026 is the last quarter', o.sys);
  ok(o.now[0] === 'Spring 2027' && o.now[1] === 'Fall 2026', 'terms: the calendar says Spring 2027 in January 2027 and Fall 2026 in October 2026 (no Winter)', o.now);
  ok(o.last[0] === 'Spring 2026' || o.last[0] === 'Fall 2026', 'terms: termsBack starts at a finished term', o.last);
  await close();
});

test('pastClassForm', async () => {
  const { page, close, log } = await setup();
  await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} });
  const r = await page.evaluate(async () => {
    const mk = (id, v) => { let e = document.getElementById(id); if (!e) { e = document.createElement('input'); e.id = id; document.body.appendChild(e); } e.value = v; return e; };
    if (!document.getElementById('histErr')) { const e = document.createElement('p'); e.id = 'histErr'; document.body.appendChild(e); }
    mk('histCode', 'BUS 2050'); mk('histYear', '2027'); mk('histProf', '');
    let sel = document.getElementById('histTerm'); if (sel) sel.value = 'Winter'; else { sel = document.createElement('input'); sel.id = 'histTerm'; sel.value = 'Winter'; document.body.appendChild(sel); }
    await addPastClass(); return document.getElementById('histErr').textContent; });
  ok(/no Winter term/.test(r), 'past class form: Winter 2027 is refused with a plain sentence', r);
  ok(!log.writes.some(w => w.table === 'class_history'), 'past class form: nothing is written for Winter 2027', log.writes.map(w => w.table));
  await close();
});

test('wording', async () => {
  const { page, close } = await setup();
  const r = await page.evaluate(() => {
    const out = {}; const c = cfg(); const old = c.QUARTER_END;
    const d = new Date(); const iso = d.toISOString().slice(0, 10);
    c.QUARTER_END = iso; try { localStorage.clear(); } catch (e) {}
    renderCampusBanner(); out.banner = (document.getElementById('campusBanner') || {}).innerText || ''; c.QUARTER_END = old;
    return out; });
  ok(!/quarter/i.test(r.banner), 'wording: the finals-week banner does not say quarter', r.banner);
  await close();
});

test('noWinter', async () => {
  const { page, close, log } = await setup();
  const opts = id => page.evaluate(id => [...document.getElementById(id).options].map(o => o.text).join('|'), id);
  /* 1. the manual form: histTerm follows histYear */
  await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} });
  const y = v => page.evaluate(v => { const e = document.getElementById('histYear'); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); }, v);
  ok(await opts('histTerm') === 'Fall|Winter|Spring|Summer', 'manual form: with no year yet every season is there', await opts('histTerm'));
  await y('2025'); ok((await opts('histTerm')).includes('Winter'), 'manual form: 2025 offers Winter', await opts('histTerm'));
  await y('2026'); ok((await opts('histTerm')).includes('Winter'), 'manual form: 2026 still offers Winter (the last quarter year)', await opts('histTerm'));
  await page.evaluate(() => { document.getElementById('histTerm').value = 'Winter'; });
  await y('2027'); ok(await opts('histTerm') === 'Fall|Spring|Summer', 'manual form: 2027 does not offer Winter', await opts('histTerm'));
  ok(await page.evaluate(() => document.getElementById('histTerm').value) !== 'Winter', 'manual form: a Winter pick is moved off Winter when the year goes to 2027', null);
  await y('2026'); ok((await opts('histTerm')).includes('Winter'), 'manual form: back to 2026 brings Winter back', await opts('histTerm'));
  /* 2. the "I took it" dialog */
  const pq = await page.evaluate(async () => {
    pqTookIt('BUS 2050'); const ys = document.getElementById('pqYear'); const o = document.createElement('option'); o.text = '2027'; ys.insertBefore(o, ys.firstChild); ys.value = '2027'; ys.dispatchEvent(new Event('change'));
    const seasons = [...document.getElementById('pqTerm').options].map(x => x.text).join('|');
    document.getElementById('pqTerm').innerHTML = '<option>Winter</option>'; document.getElementById('pqTerm').value = 'Winter';
    await pqSubmit(); return { seasons, toast: (document.getElementById('frToast') || {}).textContent || '' }; });
  ok(pq.seasons === 'Fall|Spring|Summer', 'took-it dialog: 2027 does not offer Winter', pq);
  ok(/no Winter term/.test(pq.toast), 'took-it dialog: a forced Winter 2027 is refused with a sentence', pq.toast);
  /* 3. the transcript import */
  await page.evaluate(() => { tiRows = [{ pick: true, code: 'BUS 2201', cur: 'BUS 2201', term: 'Winter', year: 2027, known: true }, { pick: true, code: 'BUS 2202', cur: 'BUS 2202', term: 'Winter', year: 2026, known: true }];
    window.pqRerender = window.pqRerender || function () {}; try { document.getElementById('tiModal'); } catch (e) {} });
  const ti = await page.evaluate(async () => { const m = document.getElementById('tiModal'); if (m) { try { tiRender('review'); } catch (e) {} }
    const rows = m ? [...m.querySelectorAll('.ti-row')].map(r => { const s = r.querySelectorAll('select'); return [...s[0].options].map(o => o.text).join('|'); }) : null;
    await confirmTranscriptImport(); return { rows, toast: (document.getElementById('frToast') || {}).textContent || '' }; });
  ok(!!ti.rows && (ti.rows[0] === 'Term?|Fall|Spring|Summer' && ti.rows[1] === 'Fall|Winter|Spring|Summer'), 'transcript import: a Winter 2027 row has no Winter option; a Winter 2026 row keeps it', ti.rows);
  ok(/no Winter term/.test(ti.toast), 'transcript import: submitting a Winter 2027 row is refused', ti.toast);
  ok(!log.writes.some(w => w.table === 'class_history'), 'no Winter 2027 is ever written to class_history', log.writes.map(w => w.table));
  const fx = await page.evaluate(() => { const d = document.createElement('div'); d.innerHTML = '<select><option>Fall</option><option>Winter</option><option>Spring</option><option>Summer</option></select><select><option>2026</option><option>2027</option></select>';
    const [a, b] = d.querySelectorAll('select'); b.value = '2027'; a.value = 'Winter'; tiFixTerm(b, 0); return [[...a.options].map(o => o.text).join('|'), a.value, termOk('Winter', 2026), termOk('Winter', 2027), termOk('Spring', 2027)]; });
  ok(fx[0] === 'Fall|Spring|Summer' && fx[1] !== 'Winter' && fx[2] === true && fx[3] === false && fx[4] === true, 'helpers: tiFixTerm / termOk', fx);
  await close();
});

test('lastDone', async () => {
  const { page, close } = await setup();
  const at = async d => { await page.clock.setSystemTime(new Date(d)); return page.evaluate(() => { const t = termLastDone(); return t.term + ' ' + t.year; }); };
  const cases = [['2026-10-16T12:00:00-07:00', 'Spring 2026'], ['2026-12-10T12:00:00-08:00', 'Spring 2026'], ['2026-12-21T12:00:00-08:00', 'Spring 2026'], ['2026-12-22T12:00:00-08:00', 'Fall 2026'], ['2026-12-31T12:00:00-08:00', 'Fall 2026'],
    ['2027-01-10T12:00:00-08:00', 'Fall 2026'], ['2027-05-13T12:00:00-07:00', 'Fall 2026'], ['2027-05-14T12:00:00-07:00', 'Spring 2027'], ['2027-06-15T12:00:00-07:00', 'Spring 2027'], ['2027-12-22T12:00:00-08:00', 'Fall 2027'], ['2028-02-01T12:00:00-08:00', 'Fall 2027']];
  for (const [d, want] of cases) { const got = await at(d); ok(got === want, 'termLastDone on ' + d.slice(0, 10) + ' is ' + want, got); }
  const q = await at('2026-05-20T12:00:00-07:00'); ok(q === 'Winter 2026', 'termLastDone: quarter-era May 2026 is unchanged (Winter 2026 was the last finished quarter)', q);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-term-fix: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
