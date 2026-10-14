/* check-desktop-replace — Clash -> Replace on the website (website-clash-replace, Tate 2026-10-14; the phone's atReplaceLabel).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in of check-app.
   Run: APP_DIR=<repo> node check-desktop-replace.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: adding a section that overlaps one in My Classes or in a Plan offers "Replace BUS 3438 with this class" and
   "Keep both" BEFORE anything is added; Replace takes the old one out and puts the new one in (and writes both), with an Undo
   toast that puts it all back; Keep both keeps both; a section that clashes with nothing is added as before. */
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
/* You are in BUS 3438 (MoWe 10:10-12:00), BUS 4442, 4445, 3431 (MoWe 12:10-6:00). BUS 4401 #70112 is MoWe 10:10-11:30: it
   clashes with BUS 3438 only. BUS 3387 #70111 is TuTh 2:10-3:30: it clashes with nothing. */
const state = page => page.evaluate(() => ({ mine: myClasses.slice().sort(), secs: Object.fromEntries(Object.keys(myClassMeta).map(k => [k, (myClassMeta[k].secs || []).map(x => x.crn)])) }));
const dialog = page => page.evaluate(() => { const m = document.getElementById('enrollModal'); return { open: !!document.querySelector('#enrollBack.open'), txt: m ? m.innerText : '', btns: m ? [...m.querySelectorAll('.si-actions button, .btn')].map(b => b.textContent.trim()) : [] }; });
const toast = page => page.evaluate(() => { const t = document.getElementById('frToast'); return { on: !!(t && t.classList.contains('on')), txt: t ? t.textContent : '', undo: !!(t && t.querySelector('.fr-toast-act')) }; });
const wrote = (log, code) => log.writes.filter(w => /my_sections|saved_classes/.test(w.table)).map(w => (w.m + ' ' + w.table + ' ' + JSON.stringify(w.body || '') + ' ' + (w.query || '')));

test('myClasses', async () => {
  const { page, close, log } = await desk(); await tick(page, 2500);
  const s0 = await state(page);
  ok(s0.mine.includes('BUS 3438') && !s0.mine.includes('BUS 4401'), 'my classes: you are in BUS 3438, not BUS 4401', s0.mine);
  /* a class that clashes with nothing: the plain dialog, nothing about replacing */
  await page.evaluate(() => openEnrollDialog('BUS 3387', secByCrn('BUS 3387', '70111'))); await tick(page, 400);
  let d = await dialog(page);
  ok(d.open && d.btns.includes('Add to My Classes') && !/Replace|Clashes|Keep both/.test(d.txt), 'no clash: the dialog is the plain “Add to My Classes”', d);
  await page.evaluate(() => closeEnrollDialog());
  /* a section of a class you are already in never clashes with that class itself */
  await page.evaluate(() => openEnrollDialog('BUS 3431', secByCrn('BUS 3431', '70100'))); await tick(page, 400);
  d = await dialog(page);
  ok(d.open && !/Replace|Clashes/.test(d.txt), 'same class: a section never clashes with its own class', d);
  await page.evaluate(() => closeEnrollDialog());
  /* a clash: the choice, before anything is added */
  log.writes.length = 0;
  await page.evaluate(() => openEnrollDialog('BUS 4401', secByCrn('BUS 4401', '70112'))); await tick(page, 400);
  d = await dialog(page);
  ok(/Clashes with BUS 3438/.test(d.txt) && d.btns.includes('Replace BUS 3438 with this class') && d.btns.includes('Keep both') && !d.btns.includes('Add to My Classes'), 'clash: “Clashes with BUS 3438 · MoWe …”, Replace BUS 3438 with this class, Keep both', d);
  ok((await state(page)).mine.join() === s0.mine.join() && log.writes.length === 0, 'clash: nothing is added or written until you choose', log.writes.length);
  /* Keep both */
  await page.evaluate(() => [...document.querySelectorAll('#enrollModal button')].find(b => b.textContent.trim() === 'Keep both').click()); await tick(page, 1200);
  let s1 = await state(page);
  ok(s1.mine.includes('BUS 3438') && s1.mine.includes('BUS 4401') && s1.secs['BUS 4401'].join() === '70112', 'keep both: BUS 4401 is in and BUS 3438 stays', s1);
  /* take 4401 back out, then Replace */
  await page.evaluate(() => mcLeaveSec('BUS 4401', '70112')); await tick(page, 800);
  ok(!(await state(page)).mine.includes('BUS 4401'), 'setup: BUS 4401 is out again', await state(page));
  log.writes.length = 0;
  await page.evaluate(() => openEnrollDialog('BUS 4401', secByCrn('BUS 4401', '70112'))); await tick(page, 400);
  await page.evaluate(() => [...document.querySelectorAll('#enrollModal button')].find(b => /^Replace BUS 3438/.test(b.textContent.trim())).click()); await tick(page, 1500);
  const s2 = await state(page), t2 = await toast(page);
  ok(!s2.mine.includes('BUS 3438') && s2.mine.includes('BUS 4401') && s2.secs['BUS 4401'].join() === '70112', 'replace: BUS 3438 is out, BUS 4401 is in', s2);
  const w = wrote(log).join('\n');
  ok(/DELETE my_sections [^\n]*class_nbr=eq\.70104/.test(w) && /DELETE saved_classes [^\n]*BUS\+3438/.test(w) && /(POST|PATCH|PUT) (my_sections|saved_classes) [^\n]*BUS 4401/.test(w), 'replace: the wire says it — BUS 3438 removed, BUS 4401 added', w.slice(0, 700));
  ok(t2.on && /BUS 4401 replaced BUS 3438/.test(t2.txt) && t2.undo, 'replace: the toast says what happened and has Undo', t2);
  ok(!(await dialog(page)).open, 'replace: the dialog closes');
  /* Undo */
  await page.evaluate(() => document.querySelector('#frToast .fr-toast-act').click()); await tick(page, 1500);
  const s3 = await state(page);
  ok(s3.mine.includes('BUS 3438') && !s3.mine.includes('BUS 4401') && s3.secs['BUS 3438'].join() === '70104', 'undo: BUS 3438 is back (same section), BUS 4401 is out', s3);
  ok(log.errors.length === 0, 'my classes: no page errors', log.errors);
  await close();
});

test('plans', async () => {
  const { page, close, log } = await desk(); await tick(page, 2500);
  await tick(page, 3000);   /* let the plans' own server load land first, or it replaces what the test adds */
  await page.evaluate(() => { TCPlans.add('A', 'BUS 3438', '70104'); }); await tick(page, 1500);
  const secs = () => page.evaluate(() => TCPlans.get('A').sections.map(x => x.class_nbr));
  ok((await secs()).join() === '70104', 'plans: Plan A holds BUS 3438 #70104', await secs());
  const choose = async (code, crn) => { await page.evaluate(([c, n]) => { show('explore'); openClassPage(c); }, [code, crn]); await tick(page, 500);
    await page.evaluate(n => document.querySelector('#cpOut [data-pl-act="choose"][data-crn="' + n + '"]').click(), crn); await tick(page, 300); };
  /* no clash: straight in */
  await choose('BUS 3387', '70111');
  await page.evaluate(() => document.querySelector('#plChoose [data-pl-act="chtoggle"][data-slot="A"]').click()); await tick(page, 600);
  ok((await secs()).join() === '70104,70111', 'plans: a section that fits is added at once', await secs());
  await page.evaluate(() => TCPlans.remove('A', '70111')); await tick(page, 300);
  /* clash: the choice */
  await choose('BUS 4401', '70112');
  await page.evaluate(() => document.querySelector('#plChoose [data-pl-act="chtoggle"][data-slot="A"]').click()); await tick(page, 500);
  let p = await page.evaluate(() => { const b = document.getElementById('plChoose'); return { txt: b ? b.innerText : '', btns: b ? [...b.querySelectorAll('button')].map(x => x.textContent.trim()) : [] }; });
  ok(/Clashes with BUS 3438/.test(p.txt) && p.btns.includes('Replace BUS 3438 with this class') && p.btns.includes('Keep both'), 'plans: the chooser says it clashes and offers Replace BUS 3438 with this class / Keep both', p);
  ok((await secs()).join() === '70104', 'plans: nothing is added until you choose', await secs());
  await page.evaluate(() => document.querySelector('#plChoose [data-pl-act="chreplace"]').click()); await tick(page, 800);
  ok((await secs()).join() === '70112', 'plans: Replace swaps BUS 3438 out of Plan A and BUS 4401 in', await secs());
  const t = await toast(page);
  ok(t.on && /BUS 4401 replaced BUS 3438 in Plan A/.test(t.txt) && t.undo, 'plans: the toast says so and has Undo', t);
  await page.evaluate(() => document.querySelector('#frToast .fr-toast-act').click()); await tick(page, 600);
  ok((await secs()).join() === '70104', 'plans: Undo puts Plan A back as it was', await secs());
  /* keep both */
  await choose('BUS 4401', '70112');
  await page.evaluate(() => document.querySelector('#plChoose [data-pl-act="chtoggle"][data-slot="A"]').click()); await tick(page, 500);
  await page.evaluate(() => document.querySelector('#plChoose [data-pl-act="chkeep"]').click()); await tick(page, 600);
  ok((await secs()).join() === '70104,70112', 'plans: Keep both adds it next to BUS 3438', await secs());
  ok(log.errors.length === 0, 'plans: no page errors', log.errors);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-replace: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
