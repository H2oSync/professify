/* Tate, 2026-10-29: "its not easy to swipe when your on the last page" — on Friends, a right swipe on
   a chat row goes back to Schedule; a left swipe on a row still opens Pin/Delete. */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready, null, { timeout: 10000 });
const cdp = await page.context().newCDPSession(page);
const drag = async (x, y, dx, dy, steps = 8) => { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
  for (let i = 1; i <= steps; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + dx * i / steps, y: y + dy * i / steps }] }); await page.waitForTimeout(14); }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await page.waitForTimeout(650); };
const toFriends = async () => { await page.evaluate(() => A.tab('friends')); await page.waitForTimeout(700); };
const row = () => page.evaluate(() => { const r = document.querySelector('#fbody .swrow'); if (!r) return null; const b = r.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; });
await toFriends(); let r = await row(); ok(!!r, '(setup) Friends shows chat rows', r);
if (r) {
  await drag(r.x - 120, r.y, 220, 0); ok(await page.evaluate(() => S.tab) === 'schedule', 'swipe right on a chat row: Friends → Schedule', await page.evaluate(() => S.tab));
  await toFriends(); r = await row();
  await drag(r.x + 120, r.y, -150, 0); ok(await page.evaluate(() => S.tab) === 'friends', 'swipe left on a chat row stays on Friends');
  ok(await page.evaluate(() => !!SW.open), 'and opens the row’s Pin/Delete', await page.evaluate(() => SW.open));
  r = await row(); await drag(r.x - 120, r.y, 200, 0);
  ok(await page.evaluate(() => S.tab) === 'friends' && !(await page.evaluate(() => SW.open)), 'swipe right on an open row only closes it', await page.evaluate(() => [S.tab, SW.open]));
  await page.waitForTimeout(400); r = await row(); await drag(r.x - 120, r.y, 220, 0);
  ok(await page.evaluate(() => S.tab) === 'schedule', 'once closed, a swipe right goes back to Schedule');
  /* then a tap still works */
  const c = await page.evaluate(() => { const b = document.querySelector('.tabbar [data-x="home"]').getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; });
  await page.touchscreen.tap(c.x, c.y); await page.waitForTimeout(450); ok(await page.evaluate(() => S.tab) === 'home', 'a tap on Home afterwards works');
}
ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); console.log(`tsw-chats: ${pass} passed, ${fail} failed`);
