/* screenshots for a look: node shot-explore-term.mjs <outdir>  (not part of the suite) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const out = process.argv[2] || '/tmp/claude-0/shots';
const CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
function tables() {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const spring = T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }));
  T.course_seats = T.course_seats.concat(spring); return T;
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
for (const [w, h] of [[1440, 900], [390, 844]]) for (const th of ['light', 'dark']) {
  const { page, close } = await openApp({ path: '/', width: w, height: h, wait: 4000, terms: CFG, tables: tables() });
  await page.evaluate(t => { try { setTheme(t); } catch (e) {} }, th); await tick(page, 500);
  await page.evaluate(() => { show('explore'); renderExContext(); exSetTerm('now'); }); await tick(page, 1500);
  await page.screenshot({ path: `${out}/ex-fall-${w}-${th}.png` });
  await page.evaluate(() => { openClassPage('BUS 3438'); }); await tick(page, 800);
  await page.screenshot({ path: `${out}/cp-fall-${w}-${th}.png` });
  await close();
}
console.log('done');
