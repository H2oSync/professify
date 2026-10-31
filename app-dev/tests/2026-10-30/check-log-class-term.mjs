/* "Log a class" starts on the newest term that's over, and Winter 2027+ (no such term: semesters) is refused.
   Fails on 1658ca4: it started on "Spring <this year>" — Spring 2027, unfinished, from Jan 1 2027 — and saved Winter 2027. */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
import { ok, tick, liveTables, done, nextPort } from './lib.mjs';

const cases = [
  ['2026-10-30T12:00:00-07:00', 'Spring', '2026', 'Oct 30 2026 (in Fall)'],
  ['2026-12-28T12:00:00-08:00', 'Fall', '2026', 'Dec 28 2026 (Fall over)'],
  ['2027-02-10T12:00:00-08:00', 'Fall', '2026', 'Feb 10 2027 (in Spring)'],
  ['2027-06-10T12:00:00-07:00', 'Spring', '2027', 'Jun 10 2027 (Spring over)'],
];
for (const [time, term, year, name] of cases) {
  const { page, close, log } = await openApp({ terms: 'live', tables: liveTables(), time, port: nextPort() });
  await page.waitForFunction(() => TC.ready, null, { timeout: 10000 }).catch(() => {});
  await page.evaluate(() => { UI.lc = null; UI.sheet = { type: 'logClass' }; render(true); }); await tick(page, 300);
  const v = { term: await page.inputValue('#lc-term'), year: await page.inputValue('#lc-year') };
  ok(v.term === term && v.year === year, `${name}: “Log a class” starts on ${term} ${year}, the newest term that’s over`, v);
  ok(!log.errors.length, `${name}: no page errors`, log.errors);
  await close();
}
{ const { page, close, log } = await openApp({ terms: 'live', tables: liveTables(), time: '2027-02-10T12:00:00-08:00', port: nextPort() });
  await page.waitForFunction(() => TC.ready, null, { timeout: 10000 }).catch(() => {});
  await page.evaluate(() => { UI.lc = null; UI.sheet = { type: 'logClass' }; render(true); }); await tick(page, 300);
  await page.fill('#lc-code', 'BUS 3431'); await page.selectOption('#lc-term', 'Winter'); await page.selectOption('#lc-year', '2027');
  await page.click('#sheet form button.btn'); await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'class_history');
  const err = await page.evaluate(() => (document.querySelector('#sheet .tc-err') || {}).textContent || '');
  ok(!w.length && /no Winter term/.test(err), 'Winter 2027: not saved, and the sheet says Cal Poly has no Winter term from 2027', { w: w.map(x => x.body), err });
  await page.selectOption('#lc-term', 'Winter'); await page.selectOption('#lc-year', '2026');
  await page.click('#sheet form button.btn'); await tick(page, 800);
  const w2 = log.writes.filter(x => x.table === 'class_history');
  ok(w2.length === 1 && w2[0].body.term === 'Winter' && +w2[0].body.year === 2026, 'Winter 2026 (the quarters) still saves', w2.map(x => x.body));
  await close(); }
done('check-log-class-term');
