/* screenshots for a look at the Replace dialog, the Hawk app rows and the mobile Explore switch (not part of the suite) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const out = process.argv[2] || '/tmp/claude-0/shots';
const CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
const TOOLS = { 'who is free right now': ['friends_free_now', {}], 'best prof for bus 3431': ['best_professor', { course: 'BUS3431' }], 'is termchamp free': ['app_help', { topic: 'free' }] };
const ask = b => (TOOLS[b.q] ? { tool: TOOLS[b.q][0], args: TOOLS[b.q][1] } : { tool: 'cant_answer', args: { reason: 'not_about_classes' } });
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
for (const [w, h] of [[1440, 900], [390, 844]]) for (const th of ['light', 'dark']) {
  const { page, close } = await openApp({ path: '/', width: w, height: h, wait: 4000, ask });
  await tick(page, 2500);
  await page.evaluate(t => { try { setTheme(t); } catch (e) {} }, th); await tick(page, 500);
  await page.evaluate(() => openEnrollDialog('BUS 4401', secByCrn('BUS 4401', '70112'))); await tick(page, 600);
  await page.screenshot({ path: `${out}/replace-${w}-${th}.png` });
  await page.evaluate(() => closeEnrollDialog()); await tick(page, 300);
  await page.addStyleTag({ path: '../../hawk-ask.css' }); await page.evaluate(t => { try { setTheme(t); } catch (e) {} }, th);
  await page.evaluate(() => HawkAsk.ask('best prof for bus 3431')); await tick(page, 1500);
  await page.screenshot({ path: `${out}/hawk-prof-${w}-${th}.png` });
  await page.evaluate(() => HawkAsk.ask('is termchamp free')); await tick(page, 1500);
  await page.screenshot({ path: `${out}/hawk-help-${w}-${th}.png` });
  await close();
}
{
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  T.course_seats = T.course_seats.concat(T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' })));
  const { page, close } = await openApp({ path: '/', width: 390, height: 844, wait: 4000, terms: CFG, tables: T });
  await page.evaluate(() => { show('explore'); renderExContext(); exSetTerm('now'); }); await tick(page, 1500);
  await page.screenshot({ path: `${out}/ex-fall-390-light-2.png` });
  await close();
}
console.log('done');
