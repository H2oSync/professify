/* Screenshots of Champ's chat and cards for the owner: desktop light + dark and a phone-width sheet, for a student with Fall classes and
   nothing chosen in Spring. Run: APP_DIR=<repo> APP_PORT=<port> SHOT_OUT=<dir> node shot-champ-cards.mjs   (ports APP_PORT .. +2) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const OUT = (process.env.SHOT_OUT || '/tmp/claude-0/sec/shots') + '/';
const BASE = +(process.env.APP_PORT || 8471);
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(300); };
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
function tables() {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const spring = T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }));
  const b42 = spring.find(r => r.course_code === 'BUS 4442');
  spring.push(Object.assign({}, b42, { course_code: 'BUS 4411', class_nbr: '70990', section: '01', days: 'MoWe 12:10PM - 1:00PM', term: '2274' }));
  T.course_seats = T.course_seats.concat(spring);
  return T;   // a Fall-only student: Fall classes, nothing chosen in Spring
}
const ask = () => ({ tool: 'cant_answer', args: { reason: 'not_about_classes' } });
const SHOTS = [['week', 'When am I free this week?'], ['now', 'Who’s free right now?'], ['prof', 'Best professor for BUS 3431'], ['fit', 'Does BUS 3431 fit my Plan A?'], ['fitclash', 'Does BUS 4411 fit my Plan A?'], ['day', 'Monday'], ['class', 'BUS 3431'], ['classq', 'Is BUS 3431 open?']];
async function run(theme, width, height, port, only) {
  process.env.APP_PORT = String(port);
  const { page, close, log } = await openApp({ path: '/', width, height, wait: 4000, terms: SPRING_CFG, tables: tables(), ask });
  await tick(page, 2500); await page.evaluate(() => loadFriendsData()); await tick(page, 1500);
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), theme); await tick(page, 300);
  await page.evaluate(() => { TCPlans.add('A', 'BUS 4442', '70102'); TCPlans.add('A', 'BUS 4445', '70103'); }); await tick(page, 1200);
  await page.click('.hawk-fab'); await tick(page, 400);
  const tag = width < 700 ? 'phone' : theme;
  for (const [k, q] of SHOTS) {
    if (only && !only.includes(k)) continue;
    await page.evaluate(() => { const c = document.querySelector('.hawk-clear'); if (c && getComputedStyle(c).display !== 'none') c.click(); }); await tick(page, 300);
    await page.evaluate(q => HawkAsk.ask(q), q); await tick(page, 1600);
    await page.screenshot({ path: `${OUT}after-champ-${k}-${tag}.png`, ...(width < 700 ? {} : { clip: { x: width - 372, y: 60, width: 372, height: height - 70 } }) });
  }
  if (width >= 700) {   // a full desktop view and a two-turn conversation
    await page.evaluate(() => { const c = document.querySelector('.hawk-clear'); c && c.click(); }); await tick(page, 300);
    await page.evaluate(() => HawkAsk.ask('When am I free this week?')); await tick(page, 1500);
    await page.evaluate(() => document.querySelector('.hawk-wrow').click()); await tick(page, 1500);
    await page.screenshot({ path: `${OUT}after-champ-chat-${tag}.png` });
  }
  console.log(tag, 'errors', JSON.stringify(log.errors));
  await close();
}
await run('light', 1440, 900, BASE);
await run('dark', 1440, 900, BASE + 1);
await run('light', 390, 844, BASE + 2, ['week', 'now', 'prof', 'fit', 'day', 'class']);
process.exit(0);
