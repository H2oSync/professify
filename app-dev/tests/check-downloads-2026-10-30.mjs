/* Smaller downloads (2026-10-30, app 1.0.2): the seat list and the catalog stay on the phone and an open asks only
 * for what changed. Runs the REAL app against a PostgREST stand-in that honours select (an unknown column is a 400,
 * as live), eq / gt / in / the or-keyset filters, order, limit/offset and HEAD counts, at a realistic size
 * (7,851 seat rows, 2,971 catalog rows), and counts requests and bytes per table.
 *   node check-downloads-2026-10-30.mjs           (APP_DIR = the site; BASE_DIR = an unpatched site, for "before")
 */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import zlib from 'node:zlib'; import fs from 'node:fs';

let pass = 0, fail = 0; const failed = [];
function ok(c, name, info) { if (c) { pass++; if (!process.argv.includes('--quiet')) console.log('  ok  ' + name); } else { fail++; failed.push(name); console.log('  FAIL ' + name + (info !== undefined ? ' → ' + JSON.stringify(info).slice(0, 600) : '')); } }

const T0 = '2026-09-29T10:30:00-07:00', at = min => new Date(Date.parse(T0) + min * 60000).toISOString();
const iso = ms => new Date(ms).toISOString().replace('Z', '+00:00');
const OLD = Date.parse('2026-09-28T09:00:00Z');
const SUBJ = 'QA QB QC QD QE QF QG QH QJ QK QL QM QN QP QR QS QT QU QV QW QX QY QZ'.split(' ').map(x => x + 'X');

/* ---- the data: the fixtures plus synthetic rows of the real size ---- */
function build(nSeats = 7851, nCat = 2971) {
  /* stamps spread over the weeks before (10 minutes apart), as a live table's are */
  const seats = FX.TABLES.course_seats.map((r, i) => Object.assign({}, r, { updated_at: iso(OLD - i * 6e5), changed_at: iso(OLD - i * 6e5) }));
  let k = 0;
  while (seats.length < nSeats) {
    const ci = Math.floor(k / 4.6), code = SUBJ[ci % SUBJ.length] + ' ' + (1000 + Math.floor(ci / SUBJ.length)), nbr = String(40000 + k);   /* ~1,700 classes, ~4.6 sections each */
    seats.push({ term: '2268', course_code: code, title: 'Synthetic Course Title ' + (k % 997), section: String(1 + (k % 6)).padStart(2, '0'), instructor: 'Lastnameson, Firstname' + (k % 50),
      days: ['MoWe 10:10AM - 11:30AM', 'TuTh 1:10PM - 2:30PM', 'Fr 9:10AM - 12:00PM', 'TBA'][k % 4], status: ['Open', 'Closed', 'Wait List'][k % 3], capacity: 40, enrolled: 30 + (k % 10), available: 10 - (k % 10),
      waitlist_total: k % 7, waitlist_capacity: 10, class_nbr: nbr, instruction_mode: 'In Person', location: 'Bldg 014-0' + (200 + k % 60), room: '0' + (200 + k % 60), subject: code.split(' ')[0], dates: '01/06/2027 - 03/20/2027',
      updated_at: iso(OLD - (k % 3600) * 6e5), changed_at: iso(OLD - (k % 3600) * 6e5) });
    k++;
  }
  /* a few rows the scraper refreshed shortly before the first open (inside the look-back) */
  for (let i = 100; i < 140; i++) { seats[i].updated_at = iso(Date.parse(at(-30))); }
  const cat = FX.TABLES.course_catalog.map((r, i) => Object.assign({ title: null, subject: null }, r, { updated_at: iso(OLD - i * 6e5), changed_at: iso(OLD - i * 6e5) }));
  const codes = [...new Set(seats.map(r => r.course_code))];
  for (let i = 0; cat.length < nCat; i++) {
    const code = codes[i] && !cat.some(c => c.course_code === codes[i]) ? codes[i] : 'QQX ' + (1000 + i);
    cat.push({ course_code: code, subject: code.split(' ')[0], title: 'Synthetic Course Title ' + i, prereqs: 'Completion of GE Area A1 and MATH 1260 with a grade of C- or better, or consent of instructor.',
      description: 'Synthetic catalog description. '.repeat(18) + 'Course ' + i + '. 3 lectures, 1 laboratory.', updated_at: iso(OLD - (cat.length % 3600) * 6e5), changed_at: iso(OLD - (cat.length % 3600) * 6e5) });
  }
  return { seats, cat };
}

/* ---- the PostgREST stand-in ---- */
const CORS = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*', 'access-control-expose-headers': 'content-range' };
const SEAT_COLS = ['term', 'class_nbr', 'subject', 'course_code', 'title', 'section', 'instructor', 'days', 'dates', 'status', 'capacity', 'enrolled', 'available', 'waitlist_total', 'waitlist_capacity', 'updated_at', 'instruction_mode', 'location', 'room'];
const CAT_COLS = ['course_code', 'subject', 'title', 'prereqs', 'description', 'updated_at'];
function fake(S) {
  /* S: { seats, cat, changedAt: bool, fail: (url, m) => bool, log: [] } */
  const cmp = (a, b) => { const ta = /^\d{4}-\d\d-\d\dT/.test(String(a)) ? Date.parse(a) : NaN, tb = /^\d{4}-\d\d-\d\dT/.test(String(b)) ? Date.parse(b) : NaN;
    if (!isNaN(ta) && !isNaN(tb)) return ta - tb; return String(a) < String(b) ? -1 : String(a) > String(b) ? 1 : 0; };
  const unq = v => String(v).replace(/^"|"$/g, '');
  function test1(r, col, op, v) {
    v = unq(v);
    if (op === 'eq') return r[col] != null && cmp(r[col], v) === 0;
    if (op === 'gt') return r[col] != null && cmp(r[col], v) > 0;
    if (op === 'gte') return r[col] != null && cmp(r[col], v) >= 0;
    throw new Error('op ' + op);
  }
  /* or=(c.gt."X",and(c.eq."X",class_nbr.gt."N")) — the app's keyset page */
  function orTest(r, v) {
    const m = /^\((\w+)\.(\w+)\.("[^"]*"|[^,()]*),and\((\w+)\.(\w+)\.("[^"]*"|[^,()]*),(\w+)\.(\w+)\.("[^"]*"|[^,()]*)\)\)$/.exec(v);
    if (!m) throw new Error('or ' + v);
    return test1(r, m[1], m[2], m[3]) || (test1(r, m[4], m[5], m[6]) && test1(r, m[7], m[8], m[9]));
  }
  return (url, m) => {
    const p = url.pathname, t = p.endsWith('/course_seats') ? 'course_seats' : p.endsWith('/course_catalog') ? 'course_catalog' : null;
    if (!t) return null;
    const q = decodeURIComponent(url.search), entry = { t, m, q, bytes: 0, gz: 0, status: 200 };
    S.log.push(entry);
    if (S.fail && S.fail(url, m, t)) { entry.status = 500; return { status: 500, headers: CORS, body: '{}' }; }
    const P = url.searchParams, cols = (t === 'course_seats' ? SEAT_COLS : CAT_COLS).concat(S.changedAt ? ['changed_at'] : []);
    const sel = (P.get('select') || '*').split(',').map(x => x.trim()).filter(Boolean);
    const bad = sel.find(c => c !== '*' && !cols.includes(c));
    if (bad) { entry.status = 400; const body = JSON.stringify({ code: '42703', details: null, hint: null, message: `column ${t}.${bad} does not exist` }); entry.bytes = body.length; return { status: 400, headers: CORS, contentType: 'application/json', body }; }
    let rows = (t === 'course_seats' ? S.seats : S.cat).slice();
    for (const [k, v] of P) {
      if (['select', 'order', 'limit', 'offset'].includes(k)) continue;
      if (k === 'or') { rows = rows.filter(r => orTest(r, v)); continue; }
      let mm;
      if ((mm = /^in\.\((.*)\)$/.exec(v))) { const set = mm[1].split(',').map(unq); rows = rows.filter(r => set.includes(String(r[k]))); continue; }
      if ((mm = /^(eq|gt|gte)\.(.*)$/.exec(v))) { rows = rows.filter(r => test1(r, k, mm[1], mm[2])); continue; }
      throw new Error('filter ' + k + '=' + v);
    }
    const ord = (P.get('order') || '').split(',').filter(Boolean).map(o => o.split('.'));
    if (ord.length) rows.sort((a, b) => { for (const [c, d] of ord) { const x = cmp(a[c] ?? '', b[c] ?? ''); if (x) return d === 'desc' ? -x : x; } return 0; });
    const total = rows.length, off = +(P.get('offset') || 0), lim = P.has('limit') ? +P.get('limit') : Infinity;
    rows = rows.slice(off, off + lim);
    const out = sel.includes('*') ? rows : rows.map(r => Object.fromEntries(sel.map(c => [c, r[c] === undefined ? null : r[c]])));
    const body = m === 'HEAD' ? '' : JSON.stringify(out);
    entry.bytes = body.length; entry.gz = body.length ? zlib.gzipSync(body).length : 0; entry.rows = out.length;
    return { status: 200, headers: Object.assign({}, CORS, { 'content-range': `${off}-${Math.max(off, off + out.length - 1)}/${total}` }), contentType: 'application/json', body };
  };
}
function sum(log, from, t) {
  const L = log.slice(from).filter(e => e.t === t);
  return { req: L.length, bytes: L.reduce((a, e) => a + e.bytes, 0), gz: L.reduce((a, e) => a + e.gz, 0), full: L.filter(e => e.status === 200 && /offset=\d/.test(e.q) && /order=course_code/.test(e.q)).length, qs: L.map(e => e.m + ' ' + e.q.slice(0, 160)) };
}
const kb = n => (n / 1024).toFixed(1) + ' KB';

/* wait until loading is over and the copies are written */
async function settled(page, newApp = true) {
  await page.waitForFunction(() => typeof TC !== 'undefined' && TC.seatsLoaded && TC.catalogLoaded && (typeof SEAT_RUN === 'undefined' || (!SEAT_RUN && !CAT_RUN)), null, { timeout: 30000 });
  if (newApp) {
    await page.waitForFunction(async () => {
      const k = 'seats:' + CFG.TERM, m = DLM[k]; if (!m) return true;
      const c = await dlsGet(k, DL_KEY), cc = await dlsGet('catalog', null);
      return c && c.mark === m.c.mark && c.full === m.c.full && (!CAT.c || (cc && cc.full === CAT.c.full && cc.mark === CAT.c.mark && (cc.miss || []).length === (CAT.c.miss || []).length));
    }, null, { timeout: 30000, polling: 200 });
  }
  await page.waitForTimeout(300);
}
/* the next app open: a new page in the same phone (same storage), the clock moved on */
async function reopen(o, min, init, arg) {
  await o.page.close();
  const p = await o.ctx.newPage();
  if (init) await p.addInitScript(init, arg);
  await p.clock.install({ time: new Date(at(min)) });
  p.on('pageerror', e => o.log.errors.push(e.message));
  await p.goto(o.origin + '/app/', { waitUntil: 'domcontentloaded' });
  await p.clock.runFor(2500); await p.waitForTimeout(400);
  o.page = p; return p;
}
const port = () => +(process.env.APP_PORT || 9850);

/* ================================================================================================ */
const D = build();
const N = D.seats.length;
const REAL = { seats: [], cat: [] };

/* ---- 1. before: the unpatched app, two opens ---- */
let before = null;
if (process.env.BASE_DIR && fs.existsSync(process.env.BASE_DIR + '/app/index.html')) {
  const keep = process.env.APP_DIR; process.env.APP_DIR = process.env.BASE_DIR;
  const S = { seats: JSON.parse(JSON.stringify(D.seats)), cat: JSON.parse(JSON.stringify(D.cat)), log: [] };
  const o = await openApp({ hook: fake(S), time: T0, port: port() });
  await settled(o.page, false); const a1 = sum(S.log, 0, 'course_seats'), c1 = sum(S.log, 0, 'course_catalog');
  const n0 = S.log.length; await reopen(o, 60); await settled(o.page, false);
  before = { s1: a1, c1, s2: sum(S.log, n0, 'course_seats'), c2: sum(S.log, n0, 'course_catalog') };
  await o.close(); process.env.APP_DIR = keep;
}

/* ---- 2. updated_at only (today's database) ---- */
{
  const S = { seats: JSON.parse(JSON.stringify(D.seats)), cat: JSON.parse(JSON.stringify(D.cat)), log: [] };
  const o = await openApp({ hook: fake(S), time: T0, port: port() });
  await settled(o.page);
  const s1 = sum(S.log, 0, 'course_seats'), c1 = sum(S.log, 0, 'course_catalog');
  const st1 = await o.page.evaluate(() => ({ n: SECTIONS.length, err: !!TC.err.seats, col: DLM['seats:' + CFG.TERM].c.col, sel: DLM['seats:' + CFG.TERM].c.sel, cat: CAT.c && CAT.c.col, desc: !!(COURSES['BUS 3346'] || {}).desc, v1: localStorage.getItem('termchamp_app_seats_v1') }));
  ok(st1.n === N && !st1.err && st1.col === 'updated_at' && st1.cat === 'updated_at', '1st open: the whole term arrives (no copy yet) and the select that worked is kept', { st1, s1: s1.qs.slice(0, 3) });
  ok(s1.full === 8 && s1.req === 9, '1st open: 8 pages of seats + one refused changed_at try (no limit=1 probes)', s1.qs);
  ok(c1.full === 3 && st1.desc, '1st open: the catalog arrives whole and the classes have their descriptions', c1.qs);
  REAL.seats.push(['1st open (no copy)', s1]); REAL.cat.push(['1st open (no copy)', c1]);

  /* the server moves on: a seat count changes, a new section, 40 rows re-stamped with no change */
  const fx = S.seats.find(r => r.course_code === 'BUS 3431' && r.available > 2);
  const was = fx.available; fx.available -= 2; fx.enrolled += 2; fx.updated_at = iso(Date.parse(at(50)));
  S.seats.push(Object.assign({}, fx, { class_nbr: '79999', section: '09', available: 7, updated_at: iso(Date.parse(at(50))) }));
  for (let i = 3000; i < 3040; i++) S.seats[i].updated_at = iso(Date.parse(at(45)));
  let n0 = S.log.length;
  let page = await reopen(o, 60); await settled(page);
  let s2 = sum(S.log, n0, 'course_seats'), c2 = sum(S.log, n0, 'course_catalog');
  let st2 = await page.evaluate(nbr => ({ n: SECTIONS.length, seats: (SEC[nbr] || {}).seats, nw: !!SEC['79999'], desc: !!(COURSES['BUS 3346'] || {}).desc, err: !!TC.err.seats, at: TC.seatsAt }), fx.class_nbr);
  ok(s2.full === 0 && s2.req === 3 && s2.bytes < 40000, '2nd open: no page of the whole term — a count, the changed stamps, the changed rows', s2.qs);
  ok(st2.seats === was - 2 && st2.nw && st2.n === N + 1 && !st2.err, '2nd open: the new seat count and the new section show, merged into the copy', { st2, want: was - 2 });
  ok(c2.req === 0 && st2.desc, '2nd open: the catalog comes from the copy (no request) and descriptions survive the seat reload', c2.qs);
  REAL.seats.push(['2nd open, 42 rows re-stamped (2 changed)', s2]); REAL.cat.push(['2nd open', c2]);

  /* nothing new */
  n0 = S.log.length; page = await reopen(o, 65); await settled(page);
  const s3 = sum(S.log, n0, 'course_seats');
  ok(s3.req === 2 && s3.full === 0 && s3.bytes < 8000, '3rd open, nothing new: two tiny reads (count + stamps), no rows', s3.qs);
  REAL.seats.push(['open, nothing new', s3]);

  /* coming back to the app after 2+ minutes: a check, not a download */
  n0 = S.log.length;
  fx.available += 1; fx.updated_at = iso(Date.parse(at(66)));
  await page.clock.runFor(125000); await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await page.waitForTimeout(300); await settled(page);
  const s4 = sum(S.log, n0, 'course_seats'), st4 = await page.evaluate(nbr => (SEC[nbr] || {}).seats, fx.class_nbr);
  ok(s4.full === 0 && s4.req === 3 && st4 === was - 1, 'back to the front: a delta check picks up the new count', { qs: s4.qs, st4 });

  /* a section removed: the count doesn't match → the whole term again, without it */
  const gone = S.seats.splice(500, 1)[0];
  n0 = S.log.length; page = await reopen(o, 80); await settled(page);
  const s5 = sum(S.log, n0, 'course_seats'), st5 = await page.evaluate(nbr => ({ has: !!SEC[nbr], n: SECTIONS.length }), gone.class_nbr);
  ok(s5.full === 8 && !st5.has && st5.n === N, 'removed section: the count check catches it → a whole download, and it is gone', { st5, qs: s5.qs.slice(0, 4) });

  /* the daily sweep re-stamps every row → too many to ask one by one → the whole term */
  S.seats.forEach(r => { r.updated_at = iso(Date.parse(at(100))); });
  n0 = S.log.length; page = await reopen(o, 110); await settled(page);
  const s6 = sum(S.log, n0, 'course_seats');
  ok(s6.full === 8, 'sweep (every row re-stamped): a whole download', s6.qs.slice(0, 4));
  REAL.seats.push(['open after the daily sweep (updated_at)', s6]);
  /* and the open after it, still inside the look-back: stamps only, no rows */
  n0 = S.log.length; page = await reopen(o, 115); await settled(page);
  const s7 = sum(S.log, n0, 'course_seats');
  ok(s7.full === 0 && s7.req <= 10 && s7.bytes < 700000, 'the open after the sweep (inside the look-back): stamps only, no rows', { req: s7.req, bytes: s7.bytes });
  REAL.seats.push(['next open, inside the 90-min look-back', s7]);

  /* a day later: a whole download (removed sections, and anything a delta could miss) */
  n0 = S.log.length; page = await reopen(o, 60 * 27); await settled(page);
  const s8 = sum(S.log, n0, 'course_seats');
  ok(s8.full === 8, 'a day later: a whole download', s8.qs.slice(0, 3));
  /* a week later: the catalog again too */
  n0 = S.log.length; page = await reopen(o, 60 * 24 * 8); await settled(page);
  const c9 = sum(S.log, n0, 'course_catalog');
  ok(c9.full === 3, 'a week later: the catalog is downloaded whole again', c9.qs);

  /* a corrupt copy → whole download, no errors */
  await page.evaluate(() => new Promise(res => { const rq = indexedDB.open('termchamp-cache', 1); rq.onsuccess = () => { const tx = rq.result.transaction('kv', 'readwrite'); tx.objectStore('kv').put({ v: 2, term: CFG.TERM, sel: 'x', col: 'updated_at', mark: 'junk', full: Date.now(), pack: { cols: ['a'], data: [[1], 'no'] } }, 'seats:' + CFG.TERM); tx.objectStore('kv').put('garbage', 'catalog'); tx.oncomplete = () => res(); }; }));
  n0 = S.log.length; page = await reopen(o, 60 * 24 * 8 + 10); await settled(page);
  const s10 = sum(S.log, n0, 'course_seats'), c10 = sum(S.log, n0, 'course_catalog'), st10 = await page.evaluate(() => ({ n: SECTIONS.length, err: !!TC.err.seats, desc: !!(COURSES['BUS 3346'] || {}).desc }));
  ok(s10.full === 8 && c10.full === 3 && st10.n === N && !st10.err && st10.desc, 'corrupt copies: whole downloads, the app loads as usual', { s10: s10.qs.slice(0, 2), c10: c10.qs, st10 });

  /* the term changes (a new app build): that term's whole list, never the old copy */
  const T2 = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2274', NOW_LABEL: 'Spring 2027', MY_TERMS: [{ code: '2274', label: 'Spring 2027' }] };
  S.seats.push(...S.seats.slice(0, 300).map(r => Object.assign({}, r, { term: '2274' })));
  n0 = S.log.length;
  page = await reopen(o, 60 * 24 * 8 + 20, cfg => { let v = cfg; Object.defineProperty(window, 'PROFESSIFY_CONFIG', { configurable: true, get: () => v, set: x => { v = Object.assign({}, x, cfg); } }); }, T2);
  await settled(page);
  const s11 = sum(S.log, n0, 'course_seats'), st11 = await page.evaluate(async () => ({ term: CFG.TERM, n: SECTIONS.length, old: !!(await dlsGet('seats:2268', null)) }));
  ok(st11.term === '2274' && st11.n === 300 && s11.full === 1 && s11.qs.every(x => /term=eq\.2274/.test(x)), 'term change: the new term is downloaded whole', { st11, qs: s11.qs });
  ok(!st11.old, 'term change: the old term’s copy is removed from the phone', st11);

  /* a delta that fails (network): the copy stays, Try again works */
  page = await reopen(o, 60 * 24 * 8 + 30); await settled(page);
  S.fail = (url, m, t) => t === 'course_seats';
  fx.available = 0; fx.updated_at = iso(Date.parse(at(60 * 24 * 8 + 35)));
  page = await reopen(o, 60 * 24 * 8 + 40);
  await page.waitForFunction(() => TC.seatsLoaded && !SEAT_RUN && TC.err.seats, null, { timeout: 20000 });
  await page.click('[data-a="tab"][data-x="explore"]'); await page.waitForTimeout(300);
  const st12 = await page.evaluate(() => ({ n: SECTIONS.length, err: !!TC.err.seats, txt: document.body.innerText }));
  ok(st12.n === N && st12.err && !/Couldn’t load Fall 2026 classes/.test(st12.txt), 'delta fails: the copy stays on screen (no error card), the failure is noted', { n: st12.n, err: st12.err });
  S.fail = null;
  await page.evaluate(() => A.retrySeats()); await settled(page);
  const st13 = await page.evaluate(nbr => ({ err: !!TC.err.seats, seats: (SEC[nbr] || {}).seats }), fx.class_nbr);
  ok(!st13.err && st13.seats === 0, 'Try again: the delta arrives', st13);
  ok(o.log.errors.length === 0, 'updated_at run: no page errors', o.log.errors);
  await o.close();
}

/* ---- 3. with sql/2026-10-30-seats-changed-at.sql: changed_at, a sweep that changed nothing is nothing ---- */
{
  const S = { seats: JSON.parse(JSON.stringify(D.seats)), cat: JSON.parse(JSON.stringify(D.cat)), log: [], changedAt: true };
  const o = await openApp({ hook: fake(S), time: T0, port: port() });
  await settled(o.page);
  const s1 = sum(S.log, 0, 'course_seats'), c1 = sum(S.log, 0, 'course_catalog');
  const st1 = await o.page.evaluate(() => ({ col: DLM['seats:' + CFG.TERM].c.col, cat: CAT.c.col }));
  ok(st1.col === 'changed_at' && st1.cat === 'changed_at' && s1.req === 8 && c1.req === 3, 'changed_at: used when the column is there (no refused try)', { st1, s: s1.req, c: c1.req });
  /* the sweep re-stamps updated_at everywhere but changes 3 rows; a catalog description changes */
  S.seats.forEach(r => { r.updated_at = iso(Date.parse(at(40))); });
  const ch = S.seats.filter(r => r.status === 'Open' && +r.class_nbr >= 40000).slice(0, 3); ch.forEach(r => { r.available = 1; r.changed_at = iso(Date.parse(at(40))); });
  const cr = S.cat.find(r => r.course_code === 'BUS 3346'); cr.description = 'A new fixture description for the delta.'; cr.changed_at = iso(Date.parse(at(40)));
  const n0 = S.log.length; const page = await reopen(o, 60); await settled(page);
  const s2 = sum(S.log, n0, 'course_seats'), c2 = sum(S.log, n0, 'course_catalog');
  const st2 = await page.evaluate(n => ({ seats: n.map(x => (SEC[x] || {}).seats), desc: (COURSES['BUS 3346'] || {}).desc }), ch.map(r => r.class_nbr));
  ok(s2.full === 0 && s2.req === 3 && s2.bytes < 10000 && st2.seats.every(x => x === 1), 'changed_at: after a sweep that changed 3 rows, only those 3 arrive', { qs: s2.qs, bytes: s2.bytes, st2 });
  ok(c2.req === 1 && /changed_at=gt\./.test(c2.qs[0]) && st2.desc === 'A new fixture description for the delta.', 'changed_at: the catalog asks only for changed rows, and the new description shows', { qs: c2.qs, desc: st2.desc });
  REAL.seats.push(['open after the sweep (with changed_at SQL)', s2]); REAL.cat.push(['open (with changed_at SQL)', c2]);
  ok(o.log.errors.length === 0, 'changed_at run: no page errors', o.log.errors);
  await o.close();
}

/* ---- 4. storage that fails: IndexedDB gone and localStorage full → it still loads ---- */
{
  const S = { seats: JSON.parse(JSON.stringify(D.seats)), cat: JSON.parse(JSON.stringify(D.cat)), log: [] };
  const o = await openApp({ hook: fake(S), time: T0, port: port(), init: () => {
    try { Object.defineProperty(window, 'indexedDB', { configurable: true, get: () => ({ open: () => { throw new DOMException('no', 'SecurityError'); } }) }); } catch (e) {}
    const set = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { if (String(v).length > 20000) throw new DOMException('full', 'QuotaExceededError'); return set.call(this, k, v); };
  } });
  await o.page.waitForFunction(() => TC.seatsLoaded && TC.catalogLoaded && !SEAT_RUN && !CAT_RUN, null, { timeout: 30000 });
  const st = await o.page.evaluate(() => ({ n: SECTIONS.length, err: !!TC.err.seats, desc: !!(COURSES['BUS 3346'] || {}).desc, ready: TC.ready, v2: localStorage.getItem('termchamp_app_seats_v2') }));
  ok(st.n === N && !st.err && st.desc && st.ready && st.v2 === null, 'no IndexedDB and a full localStorage: seats and catalog load, nothing half-written', st);
  /* the next open: no copy, so a whole download again — still fine */
  const n0 = S.log.length; const page = await reopen(o, 30);
  await page.waitForFunction(() => TC.seatsLoaded && !SEAT_RUN, null, { timeout: 30000 });
  ok(sum(S.log, n0, 'course_seats').full === 8 && o.log.errors.length === 0, 'no storage: every open downloads the term, as before, no errors', o.log.errors);
  await o.close();
}
/* IndexedDB writes refused (quota) but localStorage works: this term's seats fall back to localStorage, deltas still work */
{
  const S = { seats: JSON.parse(JSON.stringify(D.seats)), cat: JSON.parse(JSON.stringify(D.cat)), log: [] };
  const o = await openApp({ hook: fake(S), time: T0, port: port(), init: () => { IDBObjectStore.prototype.put = function () { throw new DOMException('quota', 'QuotaExceededError'); }; } });
  await o.page.waitForFunction(() => TC.seatsLoaded && TC.catalogLoaded && !SEAT_RUN && !CAT_RUN && localStorage.getItem('termchamp_app_seats_v2'), null, { timeout: 30000 });
  const sz = await o.page.evaluate(() => localStorage.getItem('termchamp_app_seats_v2').length);
  const n0 = S.log.length; const page = await reopen(o, 60); await settled(page, false);
  const s2 = sum(S.log, n0, 'course_seats');
  ok(s2.full === 0 && s2.req === 2 && o.log.errors.length === 0, 'IndexedDB full: this term’s seats fall back to localStorage (packed) and the next open is a delta', { sz, qs: s2.qs });
  console.log(`  (localStorage fallback copy of ${N} rows, packed: ${kb(sz * 2)} as UTF-16, ${kb(sz)} of characters)`);
  await o.close();
}
/* the old localStorage copy (v1): shown at once, then replaced and removed */
{
  const S = { seats: JSON.parse(JSON.stringify(D.seats)), cat: JSON.parse(JSON.stringify(D.cat)), log: [] };
  const v1 = JSON.stringify({ term: '2268', at: Date.parse(T0) - 3600e3, rows: D.seats.slice(0, 50) });
  const o = await openApp({ hook: fake(S), time: T0, port: port(), init: v => { if (!sessionStorage.getItem('v1once')) { sessionStorage.setItem('v1once', '1'); localStorage.setItem('termchamp_app_seats_v1', v); } } });
  await settled(o.page);
  const st = await o.page.evaluate(() => ({ v1: localStorage.getItem('termchamp_app_seats_v1'), n: SECTIONS.length }));
  ok(st.v1 === null && st.n === N, 'old v1 copy: replaced by the new copy and removed from localStorage', st);
  await o.close();
}

/* ---- 5. Explore's Fall list (two terms): kept on the phone too, so the next switch is a check, not 1.8 MB ---- */
{
  const SPRING = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25', MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '2274', label: 'Spring 2027' }] };
  const fall = JSON.parse(JSON.stringify(D.seats)), spring = fall.slice(0, 2000).map(r => Object.assign({}, r, { term: '2274' }));
  const S = { seats: fall.concat(spring), cat: JSON.parse(JSON.stringify(D.cat)), log: [] };
  const fallOnly = from => S.log.slice(from).filter(e => /term=eq\.2268/.test(e.q) && !/class_nbr=in\.\(\d/.test(e.q));   /* not the friends' few Fall sections (loadNowSeats) */
  const o = await openApp({ hook: fake(S), time: T0, port: port(), terms: SPRING });
  await settled(o.page);
  let n0 = S.log.length;
  await o.page.click('[data-a="tab"][data-x="explore"]'); await o.page.click('.frow .exterm');
  await o.page.waitForFunction(() => NOWT.ready && !NOWT.loading, null, { timeout: 30000 });
  await o.page.waitForFunction(async () => !!(await dlsGet('seats:2268:now', null)), null, { timeout: 30000, polling: 200 });
  const f1 = sum(fallOnly(n0), 0, 'course_seats'), k1 = await o.page.evaluate(() => Object.keys(NOWT.sec).length);
  ok(k1 === N && f1.full === 8, 'Fall list, first switch: the whole Fall term (no copy yet)', { k1, full: f1.full });
  const fx = fall.find(r => r.status === 'Open' && +r.class_nbr >= 40000); fx.available = 3; fx.updated_at = iso(Date.parse(at(50)));
  S.seats.find(r => r.term === '2268' && r.class_nbr === fx.class_nbr).available = 3;
  S.seats.find(r => r.term === '2268' && r.class_nbr === fx.class_nbr).updated_at = fx.updated_at;
  const page = await reopen(o, 60); await settled(page);
  n0 = S.log.length;
  await page.click('[data-a="tab"][data-x="explore"]'); await page.click('.frow .exterm');
  await page.waitForFunction(() => NOWT.ready && !NOWT.loading, null, { timeout: 30000 });
  const f2 = sum(fallOnly(n0), 0, 'course_seats'), st = await page.evaluate(n => ({ k: Object.keys(NOWT.sec).length, seats: (NOWT.sec['n:2268:' + n] || {}).seats, codes: document.querySelectorAll('#exlist .ccard').length }), fx.class_nbr);
  ok(f2.full === 0 && f2.req === 3 && st.k === N && st.seats === 3 && st.codes > 0, 'Fall list, next app open: shown from the copy, then only the changed row', { qs: f2.qs, st });
  REAL.seats.push(['Explore › Fall, next open (was 1.8 MB every time)', f2]);
  ok(o.log.errors.length === 0, 'Fall list: no page errors', o.log.errors);
  await o.close();
}

/* ---- the numbers ---- */
console.log('\n  Downloads per app open (stand-in at production size: ' + N + ' seat rows, ' + D.cat.length + ' catalog rows; JSON bytes, gzip in brackets)');
if (before) {
  console.log(`  BEFORE  1st open   seats ${before.s1.req} req ${kb(before.s1.bytes)} (${kb(before.s1.gz)})   catalog ${before.c1.req} req ${kb(before.c1.bytes)} (${kb(before.c1.gz)})`);
  console.log(`  BEFORE  every open seats ${before.s2.req} req ${kb(before.s2.bytes)} (${kb(before.s2.gz)})   catalog ${before.c2.req} req ${kb(before.c2.bytes)} (${kb(before.c2.gz)})`);
}
for (const [n, x] of REAL.seats) console.log(`  AFTER   seats    ${n.padEnd(46)} ${String(x.req).padStart(2)} req ${kb(x.bytes).padStart(10)} (${kb(x.gz)})`);
for (const [n, x] of REAL.cat) console.log(`  AFTER   catalog  ${n.padEnd(46)} ${String(x.req).padStart(2)} req ${kb(x.bytes).padStart(10)} (${kb(x.gz)})`);
console.log(`\ncheck-downloads: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed: ' + failed.join(' | ')); process.exit(1); }
process.exit(0);
