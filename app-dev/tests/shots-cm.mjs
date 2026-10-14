/* screenshots of Work & activities: node shots-cm.mjs <width> <light|dark> <outprefix>  (APP_DIR, APP_PORT) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const [w, theme, out] = [+process.argv[2], process.argv[3], process.argv[4]];
const t = JSON.parse(JSON.stringify(FX.TABLES));
t.commitments = [
  { id: 'c0000000-0000-4000-8000-0000000000a1', user_id: FX.ME.id, kind: 'work', name: 'Barista', days: 'MWF', start_min: 960, end_min: 1200, busy: true },
  { id: 'c0000000-0000-4000-8000-0000000000a3', user_id: FX.ME.id, kind: 'practice', name: 'Club soccer', days: 'S', start_min: 540, end_min: 660, busy: false },
];
const rpc = Object.assign({}, FX.RPC, { friend_busy_blocks: [{ user_id: FX.FRIENDS[0].id, days: 'TR', start_min: 600, end_min: 720 }, { user_id: FX.FRIENDS[0].id, days: 'M', start_min: 900, end_min: 1080 }] });
const { page, close, log } = await openApp({ path: '/', width: w, height: w < 700 ? 844 : 900, wait: 4000, time: '2026-10-14T10:30:00-07:00', tables: t, rpc, port: +(process.env.APP_PORT || 8228) });
await page.evaluate(th => { document.documentElement.setAttribute('data-theme', th); try { localStorage.setItem('professify_theme', th); } catch (e) {} }, theme);
const tick = async ms => { await page.clock.runFor(ms); await page.waitForTimeout(300); };
await tick(1500);
await page.evaluate(() => { show('sched'); setSchedTab('mine'); renderMyClasses(); }); await tick(600);
const cal = await page.$('#watchMineOut'); if (cal) await cal.scrollIntoViewIfNeeded();
await page.evaluate(() => { const c = document.querySelector('.cm-card'); if (c) c.scrollIntoView({ block: 'end' }); }); await tick(300);
await page.screenshot({ path: out + '-myclasses.png' });
await page.evaluate(() => { const c = document.querySelector('.mc-cal'); if (c) c.scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); }); await tick(300);
await page.screenshot({ path: out + '-week.png' });
await page.click('.cm-card .cm-row'); await tick(600);
await page.fill('#cmFrom', '4:30'); await page.click('[data-cm-act="save"]'); await tick(300);
await page.screenshot({ path: out + '-modal.png' });
await page.keyboard.press('Escape'); await tick(300);
await page.evaluate(() => { show('home'); renderHome(); }); await tick(800);
await page.evaluate(() => { const c = [...document.querySelectorAll('.hm-card')].find(x => /Avery/.test(x.innerText)); if (c) c.scrollIntoView({ block: 'center' }); }); await tick(300);
await page.screenshot({ path: out + '-home.png' });
console.log('errors:', log.errors.join('|'));
await close();
