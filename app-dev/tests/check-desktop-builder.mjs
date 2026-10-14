/* check-desktop-builder — the Builder replaces the website's "My planner" (website-builder, Tate 2026-10-14).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in, with Spring 2027's shipped
   config (terms:'live': TERM 2274). Run: APP_DIR=<repo> node check-desktop-builder.mjs [--only name] [--quiet]
   The promises: picks come from the report's open lines and never a class done, being taken, not offered in Spring,
   with prerequisites unmet, or HNRS without an Honors line; the order follows "What matters most" (flip it → the order
   changes) and that's saved to planner_prefs (with the ranking, and without it when RUN 19 isn't there); a tile's +
   writes that section to Plan A for term 2274; Draft my plans makes clash-free A/B/C under the units cap and never
   over a commitment, and doesn't re-draft a plan you changed unless you say so; the old planner's DOM is gone;
   no report and no flowchart → "Upload your Degree Progress Report"; nothing left → the done view. */
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
const NOW = '2026-10-14T10:30:00-07:00';
const ME = FX.ME.id;
const T = {}; const test = (n, fn) => { T[n] = fn; };
const rows = (log, table, m) => log.writes.filter(w => w.table === table && (!m || w.m === m)).flatMap(w => Array.isArray(w.body) ? w.body : [w.body]).filter(Boolean);

/* Spring 2027's sections: the fixture sections again, as term 2274, plus a class with a prerequisite you lack and an Honors class */
let nbr = 81000;
const SPRING = FX.TABLES.course_seats.map(r => ({ ...r, term: '2274', class_nbr: String(nbr++) }))
  .concat([{ ...FX.TABLES.course_seats[0], course_code: 'STAT 1210', title: 'Fixture Stats', section: '01', term: '2274', class_nbr: '81900' },
           { ...FX.TABLES.course_seats[0], course_code: 'HNRS 1100', title: 'Fixture Honors', section: '01', term: '2274', class_nbr: '81901' }]);
const line = (label, options, x = {}) => Object.assign({ label, code: null, kind: 'major', status: 'not', options, used: [] }, x);
const REQS = [
  line('BUS 4401', ['BUS 4401']), line('BUS 3346', ['BUS 3346']), line('BUS 3387', ['BUS 3387']),
  line('Statistics', ['STAT 2170', 'BUS 4401'], { oneOf: true }),
  line('Ethics', ['PHIL 3331']),             /* done: on your record (Spring 2026) */
  line('Finance electives', ['BUS 4442', 'BUS 4445'], { courses: { need: 2 } }),   /* both being taken (Fall 2026); two needed, so the line stays open */
  line('Capstone', ['BUS 4499']),            /* not offered in Spring */
  line('Intro stats', ['STAT 1210']),        /* prerequisite MATH 1000 not met */
  line('Seminar', ['HNRS 1100']),            /* Honors, without an Honors line */
  line('BUS 3438', ['BUS 3438'], { status: 'satisfied' }),
];
const tables = (o = {}) => {
  const t = JSON.parse(JSON.stringify(FX.TABLES));
  t.course_seats = t.course_seats.concat(SPRING);
  t.degree_audit = o.reqs === null ? [] : [{ user_id: ME, printed_on: '2026-09-20', catalog: 'Fall Semester 2025', major: 'BUS', concentration: null, units_used: 40, units_needed: 120, read_at: '2026-09-20T00:00:00Z', overrides: [], requirements: o.reqs || REQS }];
  if (o.prefs !== undefined) t.planner_prefs = o.prefs;
  return t;
};
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: NOW }, o));
const toPlanner = async page => { await page.evaluate(() => { show('sched'); setSchedTab('plan'); }); await tick(page, 1500); };
const picks = page => page.evaluate(() => TCBuilder.rank().all.map(c => c.code));
const tiles = page => page.evaluate(() => [...document.querySelectorAll('#plBuilderOut .bd-tile')].map(t => t.dataset.code + '#' + t.dataset.rank));

test('picks', async () => {
  const { page, close, log } = await desk({ tables: tables() }); await tick(page, 1500); await toPlanner(page);
  const p = await picks(page);
  ok(['BUS 4401', 'BUS 3346', 'BUS 3387', 'STAT 2170'].every(c => p.includes(c)), 'the open lines’ offered classes are picks', p);
  ok(!p.includes('PHIL 3331'), 'never a class you’ve done', p);
  ok(!p.includes('BUS 4442') && !p.includes('BUS 4445'), 'never a class you’re taking', p);
  ok(!p.includes('BUS 4499'), 'never a class not offered in Spring', p);
  ok(!p.includes('STAT 1210'), 'never a class whose prerequisites are unmet', p);
  ok(!p.includes('HNRS 1100'), 'never HNRS without an Honors line', p);
  ok(!p.includes('BUS 3438'), 'never a satisfied line’s class', p);
  const dom = await page.evaluate(() => ({ head: (document.querySelector('.bd-head h2') || {}).textContent, chip: (document.querySelector('.bd-head .bd-chip') || {}).textContent || '',
    reqs: [...document.querySelectorAll('.bd-req')].map(e => e.dataset.req), tile: (document.querySelector('.bd-tile[data-code="BUS 4401"]') || {}).innerText || '',
    reg: !!document.querySelector('.bd-term .rg-slot[data-rg="builder"]'), old: ['plPlanning', 'plEligibleCard', 'plTray', 'schBuildBtn', 'plEligible'].filter(id => document.getElementById(id)),
    rec: !!document.getElementById('plRecord') }));
  ok(dom.head === 'Spring 2027' && /Fall Semester 2025 catalog/.test(dom.chip), '“Spring 2027” with the report’s catalog chip', dom);
  ok(dom.reqs.includes('BUS 4401') && dom.reqs.includes('Statistics') && !dom.reqs.includes('BUS 3438'), 'a card per open line', dom.reqs);
  ok(/BUS 4401/.test(dom.tile) && /Strategic Management/.test(dom.tile) && /MoWe 10:10AM/.test(dom.tile) && /3\.6 ★/.test(dom.tile) && /open/.test(dom.tile), 'a tile: code, name, the section’s time, professor ★, seats', dom.tile);
  ok(dom.reg, 'the term card carries your registration day line');
  ok(dom.old.length === 0 && dom.rec, 'the old planner’s DOM is gone; Past classes stays', dom);
  /* Why it's #N */
  await page.click('.bd-tile[data-code="BUS 4401"] .bd-why'); await tick(page);
  const pop = await page.evaluate(() => (document.querySelector('.bd-tile[data-code="BUS 4401"] .bd-pop') || {}).innerText || '');
  ok(/Requirements\s*18 \/ 40/.test(pop) && /Urgency/.test(pop) && /Professor\s*6 \/ 15/.test(pop) && /Friends/.test(pop) && /Seats\s*0 \/ 5/.test(pop), '“Why it’s #N” lists the score parts', pop);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

test('order', async () => {
  const { page, close, log } = await desk({ tables: tables() }); await tick(page, 1500); await toPlanner(page);
  const before = await picks(page);
  const rk = await page.evaluate(() => [...document.querySelectorAll('.bd-rank li')].map(l => l.dataset.pref));
  ok(JSON.stringify(rk) === '["degree","professors","friends"]', 'Requirements · Professors · Friends by default', rk);
  log.writes.length = 0;
  await page.click('.bd-rank li[data-pref="professors"] .bd-mv[aria-label^="Move Professors up"]'); await tick(page, 800);
  const after = await picks(page);
  ok(JSON.stringify(before) !== JSON.stringify(after), 'putting Professors first changes the order', { before, after });
  const up = rows(log, 'planner_prefs', 'POST');
  ok(up.length && up[up.length - 1].user_id === ME && up[up.length - 1].priority === 'professors' && up[up.length - 1].ranking === 'professors,degree,friends' && up[up.length - 1].units === 16, 'saved: planner_prefs {priority, units, ranking}', up);
  ok(log.writes.some(w => w.table === 'planner_prefs' && /on_conflict=user_id/.test(w.query || '')), 'upserted on user_id', log.writes.filter(w => w.table === 'planner_prefs').map(w => w.query));
  await page.selectOption('#bdUnits', '14'); await tick(page, 800);
  const u2 = rows(log, 'planner_prefs', 'POST').pop() || {};
  ok(u2.units === 14 && u2.ranking === 'professors,degree,friends', 'units per term saved', u2);
  await close();
  /* read back from the account */
  { const { page, close } = await desk({ tables: tables({ prefs: [{ user_id: ME, priority: 'friends', units: 18, ranking: 'friends,professors,degree' }] }) }); await tick(page, 1500); await toPlanner(page);
    const r = await page.evaluate(() => ({ rk: [...document.querySelectorAll('.bd-rank li')].map(l => l.dataset.pref), u: document.getElementById('bdUnits').value }));
    ok(JSON.stringify(r.rk) === '["friends","professors","degree"]' && r.u === '18', 'the account’s answers are read back', r);
    await close(); }
  /* RUN 19 not there: read and write without the ranking, keep it on this device */
  { let noRank = 0;
    const h = (url, m, body) => { if (!/\/rest\/v1\/planner_prefs/.test(url.pathname)) return null;
      const has = /ranking/.test(decodeURIComponent(url.search)) || (body && /"ranking"/.test(typeof body === 'string' ? body : JSON.stringify(body)));
      if (has) { noRank++; return { status: 400, body: JSON.stringify({ code: '42703', message: 'column planner_prefs.ranking does not exist' }) }; } return null; };
    const { page, close, log } = await desk({ tables: tables(), hook: h }); await tick(page, 1500); await toPlanner(page);
    log.writes.length = 0;
    await page.click('.bd-rank li[data-pref="friends"] .bd-mv[aria-label^="Move Friends up"]'); await tick(page, 800);
    const w = rows(log, 'planner_prefs', 'POST');
    const ls = await page.evaluate(u => JSON.parse(localStorage.getItem('professify_prefs_' + u) || 'null'), ME);
    ok(noRank > 0 && w.some(x => !('ranking' in x) && x.priority === 'degree') && ls && ls.order.join(',') === 'degree,friends,professors', 'without the ranking column: saved without it, the order kept on this device', { noRank, w, ls });
    await close(); }
  /* the column goes missing between the read and the save: the save is tried again without it */
  { let refused = 0;
    const h = (url, m, body) => { if (!/\/rest\/v1\/planner_prefs/.test(url.pathname) || m !== 'POST') return null;
      if (body && /"ranking"/.test(JSON.stringify(body))) { refused++; return { status: 400, body: JSON.stringify({ code: 'PGRST204', message: "Could not find the 'ranking' column of 'planner_prefs' in the schema cache" }) }; } return null; };
    const { page, close, log } = await desk({ tables: tables(), hook: h }); await tick(page, 1500); await toPlanner(page);
    log.writes.length = 0;
    await page.click('.bd-rank li[data-pref="friends"] .bd-mv[aria-label^="Move Friends up"]'); await tick(page, 800);
    const w = rows(log, 'planner_prefs', 'POST');
    ok(refused === 1 && w.length === 1 && !('ranking' in w[0]) && w[0].priority === 'degree' && w[0].units === 16, 'a save refused for the ranking is sent again without it', { refused, w });
    await close(); }
});

test('add', async () => {
  const { page, close, log } = await desk({ tables: tables() }); await tick(page, 1500); await toPlanner(page);
  log.writes.length = 0;
  const crn = await page.evaluate(() => TCBuilder.rank().all.find(c => c.code === 'BUS 4401').best.id);
  await page.click('.bd-tile[data-code="BUS 4401"] .bd-add'); await tick(page, 1200);
  const w = rows(log, 'plans', 'POST').pop() || {};
  ok(w.user_id === ME && w.term === '2274' && w.slot === 'A' && (w.sections || []).some(s => s.code === 'BUS 4401' && s.class_nbr === crn), '+ writes that section to Plan A, term 2274', w);
  ok(await page.evaluate(() => document.querySelector('.bd-tile[data-code="BUS 4401"] .bd-add').classList.contains('in')), 'the tile says it’s in Plan A');
  /* + on a class Plan A already holds in another section swaps it, never a second section of one class */
  const other = await page.evaluate(() => { const s = (SEAT_SECTIONS['STAT 2170'] || []).map(r => String(r.class_nbr)); const best = TCBuilder.rank().all.find(c => c.code === 'STAT 2170').best.id; const o = s.find(x => x !== best); TCPlans.add('A', 'STAT 2170', o); return { best, o }; });
  await tick(page, 600);
  await page.click('.bd-tile[data-code="STAT 2170"] .bd-add'); await tick(page, 800);
  const st = await page.evaluate(() => TCPlans.get('A').sections.filter(x => x.code === 'STAT 2170').map(x => x.class_nbr));
  ok(st.length === 1 && st[0] === other.best, '+ on a class already in the plan swaps its section', { st, other });
  /* Mark done: kept on the report's overrides, and the card goes */
  log.writes.length = 0;
  await page.click('.bd-req[data-req="BUS 3387"] .bd-mark'); await tick(page, 1200);
  const ov = rows(log, 'degree_audit', 'PATCH').pop() || {};
  ok((ov.overrides || []).some(o => o.label === 'BUS 3387') && !(await page.evaluate(() => !!document.querySelector('.bd-req[data-req="BUS 3387"]'))), 'Mark done is saved on degree_audit.overrides and the card goes', ov);
  await close();
});

test('draft', async () => {
  const { page, close, log } = await desk({ tables: tables() }); await tick(page, 1500); await toPlanner(page);
  /* a commitment over BUS 4401's only Spring time */
  await page.evaluate(() => { window.cmBlocks = [parseMeet('MoWe 10:10AM–11:30AM')]; });
  await page.selectOption('#bdUnits', '13'); await tick(page, 600);
  log.writes.length = 0;
  await page.click('#bdDraft'); await tick(page, 1500);
  const r = await page.evaluate(() => {
    const out = {};
    ['A', 'B', 'C'].forEach(sl => {
      const ss = TCPlans.get(sl).sections.map(x => ({ code: x.code, crn: x.class_nbr, m: parseMeet(prettyTime((SEAT_SECTIONS[x.code] || []).find(r => String(r.class_nbr) === x.class_nbr).days)) }));
      let clash = false; ss.forEach((a, i) => ss.forEach((b, j) => { if (i < j && meetsOverlap(a.m, b.m)) clash = true; }));
      const cm = ss.some(a => meetsOverlap(a.m, window.cmBlocks[0]));
      const units = ss.reduce((t, a) => t + (auditUnitsOf(a.code, null) || Number((classInfo(a.code) || {}).units) || 0), 0);
      out[sl] = { codes: ss.map(x => x.code), clash, cm, units, n: ss.length };
    });
    return out;
  });
  ok(r.A.n > 0 && r.B.n > 0 && r.C.n > 0, 'Draft fills Plans A, B and C', r);
  ok(!r.A.clash && !r.B.clash && !r.C.clash, 'no clashes in any plan', r);
  ok(!r.A.cm && !r.B.cm && !r.C.cm && !r.A.codes.includes('BUS 4401'), 'never over a commitment', r);
  ok(r.A.units > 0 && r.A.units <= 13 && r.B.units <= 13 && r.C.units <= 13 && r.A.n <= 4, 'under the units target (13) and a class per 3 units', r);
  const w = rows(log, 'plans', 'POST');
  ok(['A', 'B', 'C'].every(sl => w.some(x => x.slot === sl && x.term === '2274')), 'all three written for term 2274', w.map(x => x.slot + x.term));
  /* change Plan A, then Draft again and say no: A stays as you left it */
  const extra = await page.evaluate(() => { const s = (SEAT_SECTIONS['BUS 3438'] || [])[0]; TCPlans.add('A', 'BUS 3438', String(s.class_nbr)); return String(s.class_nbr); });
  await tick(page, 600);
  const aBefore = await page.evaluate(() => TCPlans.get('A').sections.map(x => x.class_nbr).join());
  let asked = '';
  page.once('dialog', d => { asked = d.message(); d.dismiss(); });
  await page.click('#bdDraft'); await tick(page, 1200);
  const aAfter = await page.evaluate(() => TCPlans.get('A').sections.map(x => x.class_nbr).join());
  ok(/Plan A has classes you chose/.test(asked) && aBefore === aAfter && aAfter.includes(extra), 'a plan you changed is never re-drafted without asking', { asked, aBefore, aAfter });
  page.once('dialog', d => d.accept());
  await page.click('#bdDraft'); await tick(page, 1200);
  const aYes = await page.evaluate(() => TCPlans.get('A').sections.map(x => x.class_nbr).join());
  ok(!aYes.includes(extra), '…and is when you say yes', aYes);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
  /* four classes that fit together, 3 + 3 + 3 + 4 units: a 12-unit target leaves one out */
  { const { page, close } = await desk({ tables: tables({ reqs: REQS.concat([line('Economics', ['ECON 2303'])]) }) }); await tick(page, 1500); await toPlanner(page);
    await page.selectOption('#bdUnits', '12'); await tick(page, 600);
    const d = await page.evaluate(() => { const o = window.classInfo; window.classInfo = function (c) { const r = o.apply(this, arguments) || {}; if (c === 'ECON 2303') r.units = 4; return r; };
      const r = TCBuilder.draftOnly(); const u = s => s.reduce((t, x) => t + (auditUnitsOf(x.code, null) || Number((classInfo(x.code) || {}).units) || 0), 0);
      return { cands: TCBuilder.rank().all.map(c => c.code + ':' + c.units), A: r.A.map(x => x.code), uA: u(r.A), uC: u(r.C) }; });
    ok(d.cands.includes('ECON 2303:4') && d.A.length === 3 && d.uA <= 12 && d.uC <= 12, 'the draft stops short of the units target', d);
    await close(); }
});

test('states', async () => {
  /* nothing left */
  { const { page, close } = await desk({ tables: tables({ reqs: [line('BUS 3438', ['BUS 3438'], { status: 'satisfied' }), line('Ethics', ['PHIL 3331'], { status: 'satisfied' })] }) }); await tick(page, 1500); await toPlanner(page);
    const d = await page.evaluate(() => (document.querySelector('#plBuilderOut .bd-done') || {}).innerText || '');
    ok(/Nothing left to plan/.test(d), 'every line filled → the done view', d);
    await close(); }
  /* no report, no major */
  { const rpc = Object.assign({}, FX.RPC, { my_private_profile: [{ ...FX.ME, major: null }] });
    const t = tables({ reqs: null }); t.profiles = t.profiles.map(p => p.id === ME ? { ...p, major: null } : p);
    const { page, close } = await desk({ tables: t, rpc, init: () => { try { localStorage.removeItem('professify-profile'); } catch (e) {} } }); await tick(page, 1500);
    await page.evaluate(() => { student.major = null; }); await toPlanner(page);
    const u = await page.evaluate(() => { const c = document.querySelector('#plBuilderOut .bd-upload'); return c ? { t: c.innerText, on: (c.querySelector('button') || {}).getAttribute('onclick') } : null; });
    ok(u && /Upload your Degree Progress Report/.test(u.t) && u.on === 'dprPick()', 'no report and no flowchart → “Upload your Degree Progress Report”', u);
    await close(); }
  /* no report, a flowchart: picks from the flowchart */
  { const { page, close, log } = await desk({ tables: tables({ reqs: null }) }); await tick(page, 1500);
    await page.evaluate(() => { student.major = 'Business Administration'; student.standing = 'Junior'; try { schSyncToStudent(); } catch (e) {} }); await toPlanner(page);
    const r = await page.evaluate(() => { const R = TCBuilder.rank(); return { audit: R.audit, n: R.all.length, codes: R.all.map(c => c.code), tiles: document.querySelectorAll('#plBuilderOut .bd-tile').length }; });
    ok(!r.audit && r.n > 0 && r.tiles > 0 && !r.codes.includes('PHIL 3331') && !r.codes.includes('BUS 4442'), 'no report: the flowchart’s needs, never done or taking', r);
    ok(log.errors.length === 0, 'flowchart: no page errors', log.errors);
    await close(); }
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-builder: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
