/* Fix 9: the Builder's one-tap log writes a term and year (production refuses a null term), and ✓ again undoes it. */
import { openApp, mk, toastText, sheetType } from './tlib.mjs';
const R = mk('t9-quick-log'); const port = +(process.env.APP_PORT || 8670);
/* production: class_history.term / year are NOT NULL */
const hook = (url, m, body) => url.pathname === '/rest/v1/class_history' && m === 'POST' && [].concat(body).some(b => b && (b.term == null || b.year == null)) ? { status: 400, body: JSON.stringify({ code: '23502', message: 'null value in column "term" of relation "class_history" violates not-null constraint' }) } : null;
const { page, close, log } = await openApp({ port, hook, time: null });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 15000 });
await page.evaluate(() => { A.tab('schedule'); A.schedTab('past'); }); await page.waitForFunction(() => window.TCPL && TC.myHistory !== undefined, null, { timeout: 15000 }); await page.waitForTimeout(800);
const def = await page.evaluate(() => typeof lcDefault === 'function' ? lcDefault() : null);
R.ok(def && def.term === 'Spring' && def.year === 2026, 'the default term is the most recent finished one (now = Fall 2026 → Spring 2026)', def);
await page.evaluate(() => quickLog('BUS 1100', 'x')); await page.waitForTimeout(1200);
const posts = log.writes.filter(x => x.table === 'class_history' && x.m === 'POST');
R.ok(posts.length === 1 && posts[0].body.term === 'Spring' && posts[0].body.year === 2026, 'one tap writes the class under Spring 2026 (never a null term)', posts.map(x => x.body));
R.ok(await sheetType(page) == null && await page.evaluate(() => (TC.myHistory || []).some(h => h.code === 'BUS 1100' && h.term === 'Spring' && +h.year === 2026)), 'it lands on the record — no fallback to the sheet', await sheetType(page));
R.ok(/BUS 1100 is on your record for Spring 2026/.test(await toastText(page)), 'the toast names the term', await toastText(page));
await page.evaluate(() => quickUnlog('BUS 1100', 'x')); await page.waitForTimeout(1200);
const dels = log.writes.filter(x => x.table === 'class_history' && x.m === 'DELETE');
R.ok(dels.length === 1 && /term=eq\.Spring/.test(dels[0].query) && /year=eq\.2026/.test(dels[0].query) && await page.evaluate(() => !(TC.myHistory || []).some(h => h.code === 'BUS 1100')), '✓ again deletes exactly that row', dels.map(x => x.query));
/* Log a class starts on the same term */
await page.evaluate(() => { UI.lc = null; A.sheet('logClass'); }); await page.waitForTimeout(300);
const sel = await page.evaluate(() => ({ t: document.getElementById('lc-term').value, y: document.getElementById('lc-year').value }));
R.ok(sel.t === 'Spring' && sel.y === '2026', 'Log a class starts on the same term', sel);
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
