import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 10000 });
const cdp = await page.context().newCDPSession(page);
const where = () => page.evaluate(() => ({ tab: S.tab, s: cur().s, n: S.stack[S.tab].length }));
const swipeAt = async (x, y, dx, dy = 0, steps = 10, pause = 12) => { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
  for (let i = 1; i <= steps; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + dx * i / steps, y: y + dy * i / steps }] }); await page.waitForTimeout(pause); }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await page.waitForTimeout(500); };
/* a spot on a friend's week card (not the stories, not a sideways row) */
const spot = () => page.evaluate(() => { const el = document.querySelector('.hfeed .fcard .top') || document.querySelector('#scroll .title') || document.querySelector('#scroll h1') || document.getElementById('scroll'); const r = el.getBoundingClientRect(); return { x: 200, y: Math.min(700, Math.max(160, r.top + 20)) }; });
let p = await spot(); await swipeAt(330, p.y, -200);
ok((await where()).tab === 'explore', 'Home: swipe left → Explore', await where());
await page.waitForTimeout(300); await swipeAt(330, 300, -200); ok((await where()).tab === 'rate', 'Explore: swipe left → Rate', await where());
await swipeAt(60, 300, 200); ok((await where()).tab === 'explore', 'Rate: swipe right → back to Explore', await where());
await swipeAt(60, 300, 200); ok((await where()).tab === 'home', 'Explore: swipe right → Home', await where());
await swipeAt(60, 300, 200); ok((await where()).tab === 'home', 'Home: swipe right does nothing (no tab before Home)', await where());
await page.evaluate(() => A.tab('friends')); await page.waitForTimeout(400);
await swipeAt(330, 140, -200); ok((await where()).tab === 'friends', 'Friends: swipe left does nothing (last tab)', await where());
/* a short or mostly-vertical move doesn't switch */
await page.evaluate(() => A.tab('home')); await page.waitForTimeout(400);
p = await spot(); await swipeAt(250, p.y, -30, 0, 6, 40); ok((await where()).tab === 'home', 'a short, slow sideways nudge (30px) stays put', await where());
ok(await page.evaluate(() => { const s = document.getElementById('scroll'); return s.style.transform === '' && (s.style.opacity === '' || s.style.opacity === '1'); }), '…and the page springs back into place');
await swipeAt(200, 600, -60, -300); ok((await where()).tab === 'home', 'a mostly-vertical swipe scrolls, it doesn’t switch tabs', await where());
/* the stories row keeps its own sideways scroll */
const sy = await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; const r = document.querySelector('.stories').getBoundingClientRect(); return r.top + r.height / 2; });
await page.waitForTimeout(200); await swipeAt(330, sy, -220); ok((await where()).tab === 'home', 'swiping along the stories scrolls them, it doesn’t switch tabs', await where());
/* a sheet open: no tab switching */
await page.evaluate(() => document.querySelector('.stories .story').click()); await page.waitForTimeout(500);
await swipeAt(330, 300, -200); ok((await where()).tab === 'home' && await page.evaluate(() => !!UI.sheet), 'with a sheet open, a sideways swipe doesn’t switch tabs', await where());
await page.evaluate(() => A.closeSheet()); await page.waitForTimeout(300);
/* a pushed screen: swipe right = back; left = nothing */
await page.evaluate(() => { const c = SECTIONS.find(s => s.code).code; go('classDetail', { code: c }); }); await page.waitForTimeout(500);
await swipeAt(330, 400, -200); ok((await where()).s === 'classDetail', 'a class page: swipe left does nothing', await where());
await swipeAt(60, 400, 200); ok((await where()).s === 'home' && (await where()).tab === 'home', 'a class page: swipe right goes back', await where());
/* chat rows keep their own swipe (Pin / Delete) */
await page.evaluate(() => A.tab('friends')); await page.waitForTimeout(500);
const row = await page.evaluate(() => { const r = document.querySelector('.swrow'); if (!r) return null; const b = r.getBoundingClientRect(); return { x: b.left + b.width - 30, y: b.top + b.height / 2 }; });
if (row) { await swipeAt(row.x, row.y, -150); ok((await where()).tab === 'friends', 'a chat row swipes open its Pin / Delete, it doesn’t switch tabs', await where()); }
ok(log.errors.length === 0, 'no page errors (touch)', log.errors);
await close();
/* Desktop preview: mouse drag */
const d = await openApp({ width: 390, height: 844, touch: false });
await d.page.waitForFunction(() => TC.ready, null, { timeout: 10000 }); await d.page.waitForTimeout(500);
await d.page.mouse.move(330, 400); await d.page.mouse.down(); for (let i = 1; i <= 10; i++) { await d.page.mouse.move(330 - 22 * i, 402); await d.page.waitForTimeout(10); } await d.page.mouse.up(); await d.page.waitForTimeout(500);
ok(await d.page.evaluate(() => S.tab) === 'explore', 'preview: a mouse drag left moves Home → Explore');
await d.page.evaluate(() => document.querySelector('[data-a="tab"][data-x="home"]').click()); await d.page.waitForTimeout(400);
ok(await d.page.evaluate(() => S.tab) === 'home', 'preview: a plain click on a tab still works');
ok(d.log.errors.length === 0, 'no page errors (mouse)', d.log.errors);
await d.close();
console.log(`tsw-test: ${pass} passed, ${fail} failed`);
