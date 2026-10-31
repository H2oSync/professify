/* Fix 7: render() on an emptied stack starts the tab again instead of throwing (reading 'hx'). */
import { openApp, mk } from './tlib.mjs';
const R = mk('t7-empty-stack'); const port = +(process.env.APP_PORT || 8668);
const { page, close, log } = await openApp({ port });
await page.waitForFunction(() => TC.ready, null, { timeout: 15000 }); await page.waitForTimeout(300);
const r = await page.evaluate(() => { A.tab('schedule'); S.stack[S.tab] = []; try { render(true); } catch (e) { return { err: e.message }; } A.openClass(Object.keys(COURSES)[0]); return { st: S.stack.schedule.map(e => e.s), tabbar: !!document.querySelector('.tabbar') }; });
R.ok(!r.err && r.st.join('>') === 'schedule>classDetail' && r.tabbar, 'an emptied stack draws the tab’s root, and going on from it works', r);
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
