/* check-desktop-sem-left — semester leftovers (sem-left, 2026-10-16).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in of check-app.
   Run: APP_DIR=<repo> APP_PORT=8461 node check-desktop-sem-left.mjs [--only name] [--quiet]
   The promises: (1) the synthesized four-year plan is a SEMESTER plan - Fall/Spring only, padded to ~15 units with 3-unit slots,
   never 13 units of 4-unit slots; its year and term totals add up. (2) Explore on Fall 2026 (read only): the right rail
   (Still need, Saved classes, Where your friends are) says "For Spring 2027", keeps Spring's seats, and its rows open the
   Spring 2027 class page; on Spring the rail is as it was (no "For" label). */
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
const PORT = process.env.APP_PORT || 8461;
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


/* The generator only builds a plan for a major that has no hand-authored one - today every major has one - so for these two
   tests the page is served from a copy of the repo root whose index.html lets the generator run for every major too (its plans
   land under 'syn-<major>'). Nothing else in the page differs. */
import fs from 'node:fs'; import path from 'node:path'; import os from 'node:os';
function forcedSynthDir() {
  const src = process.env.APP_DIR || path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
  const dst = fs.mkdtempSync(path.join(os.tmpdir(), 'semleft-'));
  fs.readdirSync(src).forEach(n => { if (n === 'index.html' || n === '.git') return; fs.symlinkSync(path.join(src, n), path.join(dst, n)); });
  const h = fs.readFileSync(path.join(src, 'index.html'), 'utf8'), k = 'if(haveSched[norm(maj)])return;';
  if (h.split(k).length !== 2) throw new Error('anchor for the forced generator is gone');
  fs.writeFileSync(path.join(dst, 'index.html'), h.replace(k, 'if(false)return;'));
  return dst;
}
async function withSynth(fn) {
  const real = process.env.APP_DIR; const d = forcedSynthDir(); process.env.APP_DIR = d;
  try { return await fn(); } finally { process.env.APP_DIR = real; if (real === undefined) delete process.env.APP_DIR; fs.rmSync(d, { recursive: true, force: true }); }
}
const sum = t => t.slots.reduce((a, s) => a + (Array.isArray(s.units) ? s.units[0] : (+s.units || 0)), 0);

test('synthPlan', async () => withSynth(async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: tables() }); await tick(page, 2500);
  const r = await page.evaluate(() => {
    const syn = Object.values(SCHED_MAJORS).filter(m => m.synth);
    const u = s => Array.isArray(s.units) ? s.units[0] : (+s.units || 0);
    const tot = t => t.slots.reduce((a, s) => a + u(s), 0);
    const terms = syn.flatMap(m => m.terms);
    const pads = terms.flatMap(t => t.slots.filter(s => s.type === 'ge' && !s.code && /^(ge[234](Fall|Spring)\d|ge1(Fall|Spring)p\d)/.test(s.id)));   /* the generator's own filler, not the flowchart's GE slots */
    const y1 = syn.flatMap(m => m.terms.filter(t => t.year === 1));
    return { n: syn.length, seasons: [...new Set(terms.map(t => t.term))].join('|'), nT: terms.length,
      pad4: pads.filter(s => u(s) === 4).length, padN: pads.length,
      conc4: terms.flatMap(t => t.slots.filter(s => s.type === 'concentration' && u(s) === 4)).length,
      concN: terms.flatMap(t => t.slots.filter(s => s.type === 'concentration')).length,
      under: terms.filter(t => tot(t) < 12).length, over: terms.filter(t => tot(t) > 19).length,
      avg: Math.round(terms.reduce((a, t) => a + tot(t), 0) / terms.length * 10) / 10,
      padded15: terms.filter(t => t.slots.some(s => !s.code && s.type === 'ge') && tot(t) >= 13 && tot(t) <= 15).length,
      paddedTerms: terms.filter(t => t.slots.some(s => !s.code && s.type === 'ge')).length,
      y1avg: Math.round(y1.reduce((a, t) => a + tot(t), 0) / y1.length * 10) / 10 };
  });
  ok(r.n > 20, 'synth: the generator ran for the majors', r);
  ok(r.seasons === 'Fall|Spring', 'synth: only Fall and Spring terms (no Winter, no Summer)', r.seasons);
  ok(r.pad4 === 0 && r.padN > 0 && r.conc4 === 0, 'synth: GE filler and concentration slots are 3 units, never 4', r);
  ok(r.under === 0 && r.over === 0, 'synth: every term is 12-19 units', r);
  ok(r.avg >= 14 && r.avg <= 17, 'synth: the average term is ~15 units', r);
  ok(r.paddedTerms > 0 && r.padded15 / r.paddedTerms > 0.7, 'synth: most padded terms land on 13-15 units', r);
  ok(log.errors.length === 0, 'synth: no page errors', log.errors);
  await close();
}));

test('synthScreen', async () => withSynth(async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: tables() }); await tick(page, 2500);
  const r = await page.evaluate(async () => {
    show('sched'); try { setSchedTab('plan'); } catch (e) {}
    const k = Object.keys(SCHED_MAJORS).find(k => SCHED_MAJORS[k].synth); const sel = document.getElementById('schMajorSel');
    if (![...sel.options].some(o => o.value === k)) return { noOption: true, k };
    sel.value = k; sel.dispatchEvent(new Event('change', { bubbles: true }));
    await new Promise(r => setTimeout(r, 600));
    document.querySelectorAll('#schChecklist .sp-year, #schChecklist [data-year]').forEach(e => e.classList && e.classList.remove('sp-shut'));
    const heads = [...document.querySelectorAll('#schChecklist .sp-th')].map(h => ({ u: +((h.querySelector('.un') || {}).textContent || '').replace(/[^\d]/g, ''), t: h.innerText.replace(/\s+/g, ' ').slice(0, 40) }));
    const yrs = [...document.querySelectorAll('#schChecklist .sp-yr-meta, #schChecklist .sp-yhead')].map(e => e.innerText.replace(/\s+/g, ' ')).slice(0, 4);
    const yu = yrs.map(y => +((y.match(/(\d+) units/) || [])[1] || 0));
    const sumsByYear = [0, 1, 2, 3].map(i => (heads[2 * i] ? heads[2 * i].u : 0) + (heads[2 * i + 1] ? heads[2 * i + 1].u : 0));
    return { name: SCHED_MAJORS[k].name, heads: heads.slice(0, 4), nHeads: heads.length, yrs, yu, sumsByYear };
  });
  ok(!r.noOption, 'synth screen: a synthesized major is selectable in Plans', r);
  ok(r.nHeads > 0, 'synth screen: the plan paints its terms', r);
  ok(r.yu.length === 4 && r.yu.every((u, i) => u === r.sumsByYear[i]), 'synth screen: each year\'s "N units" is the sum of its two term headers', r);
  ok(r.heads.every(h => h.u >= 9 && h.u <= 19), 'synth screen: term headers read semester loads (9-19 units)', r);
  ok(log.errors.length === 0, 'synth screen: no page errors', log.errors);
  await close();
}));

const railFor = page => page.evaluate(() => [...document.querySelectorAll('#exRail .ex-mod')].map(m => ({ h: m.querySelector('h3').textContent, p: m.querySelector('.exm-h p').innerText })));
test('railLabelFall', async () => {
  const { page, close, log } = await setup();
  let r = await railFor(page);
  ok(r.every(x => !/^For /.test(x.p)), 'Spring: the rail has no "For" label (as before)', r);
  await page.evaluate(() => { renderExContext(); exSetTerm('now'); }); await tick(page, 1500);
  r = await railFor(page);
  const need = r.find(x => x.h === 'Still need'), sv = r.find(x => x.h === 'Saved classes');
  ok(need && /^For Spring 2027 · \d+ of \d+ with a course code are offered$/.test(need.p), 'Fall: Still need reads "For Spring 2027 · 3 of 3 with a course code are offered" (term named once)', need);
  ok(sv && /^For Spring 2027 · 5 on your list/.test(sv.p), 'Fall: Saved classes reads "For Spring 2027 · 5 on your list"', sv);
  ok(!r.some(x => /Fall 2026/.test(x.p)), 'Fall: no rail card names Fall 2026', r);
  const rows = await railRows(page);
  ok((rows['Saved classes'] || []).some(x => x.code === 'BUS 4448' && x.num === '56 left'), 'Fall: the rail still shows Spring seats (BUS 4448 56 left)', rows['Saved classes']);
  /* back to Spring */
  await page.evaluate(() => { exSetTerm('spring'); }); await tick(page, 800);
  r = await railFor(page);
  ok(r.every(x => !/^For /.test(x.p)), 'back on Spring: the "For" label is gone', r);
  ok(log.errors.length === 0, 'rail label: no page errors', log.errors);
  await close();
});

test('railRowOpensSpring', async () => {
  const { page, close } = await setup();
  await page.evaluate(() => { renderExContext(); exSetTerm('now'); }); await tick(page, 1500);
  await page.evaluate(() => { document.querySelector('#exRail .ex-mod:nth-child(2) .exm-row, #exRail .exm-row').click(); }); await tick(page, 900);
  const o = await page.evaluate(() => ({ view: fallViewId(), cpNow, fallNote: !!document.querySelector('.cp-fallnote'), code: cpCode }));
  ok(o.view === 'class' && o.cpNow === false && !o.fallNote, 'a rail row on Fall opens the Spring 2027 class page (not the Fall one)', o);
  /* a row of the Fall list itself still opens the Fall page */
  await page.evaluate(() => { show('explore'); exSetTerm('now'); }); await tick(page, 800);
  const o2 = await page.evaluate(() => { openClassPage('BUS 4448'); return { cpNow }; });
  ok(o2.cpNow === true, 'a Fall list row still opens the Fall page (the lens is only for the rail)', o2);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-sem-left: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
