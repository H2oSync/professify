/* (2026-11-01) Lecture + lab (patches/lecture-lab-2026-11-01.py). Tate: "people can select multiple sections when choosing
   their classes because some classes have lecture + lab, and I couldnt pick two sections". Synthetic fixtures only
   (invented FIX course, invented section numbers). Run: APP_DIR=<site> APP_PORT=<port> node check-lecture-lab-2026-11-01.mjs [--shots <dir>] */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const port = +(process.env.APP_PORT || 9670);
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : '';
let pass = 0, fail = 0; const fails = [];
function ok(c, m, d) { if (c) { pass++; console.log('  ok  ', m); } else { fail++; fails.push(m); console.log('  FAIL', m, d === undefined ? '' : '→ ' + JSON.stringify(d).slice(0, 600)); } }
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
const until = async (p, fn, arg, n = 30) => { for (let i = 0; i < n; i++) { if (await p.evaluate(fn, arg)) return true; await tick(p, 300); } return false; };
const W = (log, table, m) => log.writes.filter(w => w.table === table && (!m || w.m === m));
const rowsOf = w => [].concat(w.body || []);
const shot = async (p, name) => { if (SHOTS) await p.screenshot({ path: `${SHOTS}/${name}.png` }); };
const sheetText = p => p.evaluate(() => ((document.getElementById('sheet') || {}).innerText || '').replace(/\s+/g, ' '));

const ME = FX.ME.id;
const SC = (section, nbr, days, prof = 'Examplewood, Ada') => ({ term: '2268', course_code: 'FIX 1210', title: 'Fixture Chemistry', section, instructor: prof, days, status: 'Open', capacity: 40, enrollment_total: 20, available: 20, waitlist_total: 0, waitlist_capacity: 10, class_nbr: nbr });
const LECLAB = [
  SC('01-LEC Regular', '81001', 'TuTh 8:10AM - 9:00AM'), SC('02-LEC Regular', '81002', 'TuTh 3:10PM - 4:00PM'),
  SC('11-LAB Regular', '81011', 'Fr 9:10AM - 12:00PM', 'Fixturesen, Bram'), SC('12-LAB Regular', '81012', 'Fr 1:10PM - 4:00PM', 'Fixturesen, Bram'),
];
const saved = (user, code, term = '2268') => ({ user_id: user, term, code, class_nbr: null, created_at: '2026-09-10T18:00:00Z', waitlist_pos: null });
const base = () => { const T = JSON.parse(JSON.stringify(FX.TABLES)); T.course_seats = T.course_seats.concat(LECLAB); return T; };
const ready = p => p.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows, null, { timeout: 15000 });
const mineFix = p => p.evaluate(() => personSecs('me').filter(x => x.code === 'FIX 1210').map(x => x.id).sort());
const addTo = async (p, id, dest) => { await p.evaluate(([id, dest]) => { openAddTo(id); UI.sheet.dest = dest; UI.sheet.seq++; render(true); }, [id, dest]); await tick(p, 300); };
const go = async (p, mode = 'add') => { await p.evaluate(m => A.atGo(m), mode); await until(p, () => !UI.busy.at, null, 30); await tick(p, 1200); };

/* ===== A. labels and parts ===== */
{
  const { page, close } = await openApp({ port, tables: base() });
  await ready(page); await tick(page, 600);
  const v = await page.evaluate(() => ({ lab: secLab(SEC['81011']), lec: secLab(SEC['81001']), raw: secLabel('11-LAB Regular'), plain: secLabel('01'), one: secLab(secsOf('BUS 3438')[0]),
    parts: partsOf(secsOf('FIX 1210')), one: partsOf(secsOf('BUS 3438')), miss: partsMissing(secsOf('FIX 1210'), [SEC['81001']]) }));
  ok(v.lab === 'Sec 11 Lab' && v.lec === 'Sec 01 Lecture' && v.raw === 'Sec 11' && v.plain === 'Sec 01' && !/Lecture|Lab/.test(v.one), 'a: in a lecture + lab class each section says its part (“Sec 11 Lab”); one-part classes and secLabel read as before', v);
  ok(v.parts.join() === 'LEC,LAB' && v.one.length <= 1 && v.miss.join() === 'LAB', 'a: FIX 1210 has a Lecture and a Lab; holding a lecture leaves the lab', v);
  await close();
}

/* ===== B. My Classes: lecture, then lab — both stay; a second lab swaps only the lab ===== */
{
  const { page, close, log } = await openApp({ port, tables: base(), height: 900 });
  await ready(page); await tick(page, 600);
  await addTo(page, '81001', 'mine'); await go(page);
  ok((await mineFix(page)).join() === '81001', 'b: the lecture goes into My Classes', await mineFix(page));
  await addTo(page, '81011', 'mine');
  let o = await page.evaluate(() => { const o = atPlanOf(UI.sheet, SEC['81011']); return { repl: o.repl.map(x => x.id), note: document.querySelector('#sheet .at-note').innerText, btn: document.querySelector('#sheet .at-go').innerText }; });
  ok(!o.repl.length && /Fits your week/.test(o.note) && !/Swap/.test(o.btn), 'b: adding the lab does not offer to swap out the lecture', o);
  await shot(page, 'addto-lab');
  await go(page);
  ok((await mineFix(page)).join() === '81001,81011', 'b: lecture + lab are both in My Classes', await mineFix(page));
  ok(!W(log, 'my_sections', 'DELETE').length, 'b: nothing was deleted');
  await addTo(page, '81012', 'mine');
  o = await page.evaluate(() => { const o = atPlanOf(UI.sheet, SEC['81012']); return { repl: o.repl.map(x => x.id), note: document.querySelector('#sheet .at-note').innerText }; });
  ok(o.repl.join() === '81011' && /Sec 11 Lab/.test(o.note), 'b: a different lab offers to swap the lab only', o);
  await go(page, 'swap');
  ok((await mineFix(page)).join() === '81001,81012', 'b: after the swap: the lecture and the new lab', await mineFix(page));
  const del = W(log, 'my_sections', 'DELETE');
  ok(del.length === 1 && /class_nbr=eq\.81011/.test(del[0].query), 'b: the only delete is the old lab', del.map(d => d.query));
  /* adding the lecture first: the note says a lab is still needed */
  await page.evaluate(() => { UI.sheet = null; }); await close();
}
{
  const { page, close } = await openApp({ port, tables: base(), height: 900 });
  await ready(page); await tick(page, 600);
  await addTo(page, '81002', 'mine');
  const n = await page.evaluate(() => document.querySelector('#sheet .at-note').innerText);
  ok(/also needs a lab/.test(n), 'b: adding a lecture says the class also needs a lab', n);
  await shot(page, 'addto-lecture');
  await close();
}

/* ===== C. Plans: lecture + lab both stay in Plan A ===== */
{
  const { page, close } = await openApp({ port, tables: base(), height: 900 });
  await ready(page); await tick(page, 600);
  await page.evaluate(() => TC.setPlan('A', [])); await tick(page, 200);
  await addTo(page, '81001', 'A'); await go(page);
  await addTo(page, '81011', 'A'); await go(page);
  let pl = await page.evaluate(() => TC.plans.A.slice().sort());
  ok(pl.join() === '81001,81011', 'c: Plan A keeps the lecture when the lab goes in', pl);
  await addTo(page, '81002', 'A'); await go(page, 'swap');
  pl = await page.evaluate(() => TC.plans.A.slice().sort());
  ok(pl.join() === '81002,81011', 'c: another lecture swaps the lecture only', pl);
  await close();
}

/* ===== D. the class page says what a multi-part class needs ===== */
{
  const { page, close } = await openApp({ port, tables: base(), height: 1100 });
  await ready(page); await tick(page, 600);
  await addTo(page, '81001', 'mine'); await go(page);
  await page.evaluate(() => { UI.sheet = null; A.openClass('FIX 1210'); }); await tick(page, 800);
  const t = await page.evaluate(() => { const n = document.querySelector('#scroll .mp-note'); return n ? { t: n.innerText.replace(/\s+/g, ' '), on: [...n.querySelectorAll('.mp-p.on')].map(x => x.innerText.trim()) } : null; });
  ok(t && /FIX 1210 has lecture and lab sections\. Add one of each\./.test(t.t) && t.on.join() === 'Lecture', 'd: the class page says lecture + lab, and checks the lecture you have', t);
  const labs = await page.evaluate(() => [...document.querySelectorAll('#scroll .secrow .t b')].map(b => b.innerText.trim()));
  ok(labs.some(x => /^Sec 11 Lab/.test(x)) && labs.some(x => /^Sec 01 Lecture/.test(x)), 'd: the section rows say which ones are labs', labs);
  await shot(page, 'class-page');
  await page.evaluate(() => A.secSheet('FIX 1210', '81001')); await tick(page, 400);
  const st = await sheetText(page);
  ok(/No lab section yet for FIX 1210/.test(st) && /Pick a lab section/.test(st), 'd: your lecture’s sheet says no lab yet, with a button to pick one', st.slice(0, 300));
  await shot(page, 'sec-sheet');
  ok(await page.evaluate(() => { const o = conflicts(['81001'], { code: 'FIX 1210', sec: '13-LAB', days: 'TuTh', s: 500, e: 560, async: false }); return o.length === 1; }), 'd: a lab that overlaps its own lecture counts as a clash');
  await close();
}

/* ===== E. Anytime "Add times": lecture then lab, the class stays until both ===== */
{
  const T = base(); T.saved_classes.push(saved(ME, 'FIX 1210'));
  const { page, close, log } = await openApp({ port, tables: T, height: 1000 });
  await ready(page); await tick(page, 1200);
  ok(await page.evaluate(() => anyPickList('2268').some(x => x.code === 'FIX 1210')), 'e: FIX 1210 (no section) is in “Add times”');
  await page.evaluate(() => A.anyPickOpen('2268')); await tick(page, 400);
  let t = await sheetText(page);
  ok(/Lecture pick 1/.test(t) && /Lab pick 1/.test(t), 'e: the picker groups FIX 1210 into Lecture and Lab', t.slice(0, 400));
  await page.evaluate(() => A.anyChoose('2268|FIX 1210|81001')); await until(page, () => !UI.busy.anyPick, null, 30); await tick(page, 600);
  t = await sheetText(page);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'anyPick' && anyPickList('2268').some(x => x.code === 'FIX 1210')) && /Lecture picked/.test(t), 'e: after the lecture, the sheet stays open for the lab', t.slice(0, 400));
  await shot(page, 'anypick-after-lecture');
  await page.evaluate(() => A.anyChoose('2268|FIX 1210|81012')); await until(page, () => !UI.busy.anyPick, null, 30); await tick(page, 600);
  ok((await mineFix(page)).join() === '81001,81012' && !W(log, 'my_sections', 'DELETE').length, 'e: lecture + lab saved, nothing deleted', await mineFix(page));
  ok(await page.evaluate(() => !anyPickList('2268').some(x => x.code === 'FIX 1210')), 'e: with both parts, FIX 1210 leaves “Add times”');
  await close();
}

/* ===== F. the report's "Pick your sections": one pick per part ===== */
{
  const T = base(); T.saved_classes.push(saved(ME, 'FIX 1210'));
  const { page, close, log } = await openApp({ port, tables: T, height: 1000 });
  await ready(page); await tick(page, 800);
  const g = await page.evaluate(async () => { const r = await dprPickBuild({ rows: [{ cur: 'FIX 1210', code: 'FIX 1210', _next: true }] }); if (r) { UI.sheet = r; render(true); } return r && r.groups.map(g => g.classes); });
  ok(g && g[0] && g[0].join() === 'FIX 1210#LEC,FIX 1210#LAB', 'f: FIX 1210 is two picks: a lecture and a lab', g);
  await tick(page, 300);
  let t = await sheetText(page);
  ok(/Lecture · Fixture Chemistry/.test(t) && /Lab · Fixture Chemistry/.test(t) && /1 class/.test(t), 'f: the sheet shows a Lecture card and a Lab card', t.slice(0, 400));
  await page.evaluate(() => { A.dprPickSec('0|FIX 1210#LEC|81002'); A.dprPickSec('0|FIX 1210#LAB|81011'); }); await tick(page, 300);
  ok(/Save 2 sections/.test(await page.evaluate(() => document.querySelector('#sheet [data-a="dprPickSave"]').innerText)), 'f: picking one of each → “Save 2 sections”');
  await shot(page, 'dpr-pick');
  await page.evaluate(() => A.dprPickSave()); await until(page, () => !UI.busy.dpk, null, 30); await tick(page, 600);
  ok((await mineFix(page)).join() === '81002,81011', 'f: both are saved', await mineFix(page));
  await close();
}

/* ===== G. onboarding "Add your classes": stays open for the lab ===== */
{
  const { page, close } = await openApp({ port, tables: base(), height: 1000 });
  await ready(page); await tick(page, 600);
  await page.evaluate(() => A.onbAdd('FIX 1210', '81001')); await until(page, () => !UI.busy.onb, null, 30); await tick(page, 400);
  ok(await page.evaluate(() => UI.onbExpand === 'FIX 1210'), 'g: after the lecture, the class stays open for its lab');
  await page.evaluate(() => A.onbAdd('FIX 1210', '81011')); await until(page, () => !UI.busy.onb, null, 30); await tick(page, 400);
  ok(await page.evaluate(() => UI.onbExpand === null) && (await mineFix(page)).join() === '81001,81011', 'g: after the lab it closes; both are saved', await mineFix(page));
  await close();
}

console.log(`\ncheck-lecture-lab: ${pass} passed, ${fail} failed`); if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
