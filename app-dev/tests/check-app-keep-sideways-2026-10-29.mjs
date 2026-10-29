import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 4, null, { timeout: 10000 });
const sl = () => page.evaluate(() => document.querySelector('.stories').scrollLeft);
const room = await page.evaluate(() => { const s = document.querySelector('.stories'); return s.scrollWidth - s.clientWidth; });
await page.evaluate(() => { const s = document.querySelector('.stories'); s.style.scrollSnapType = 'none'; s.scrollLeft = 150; });
const at = await sl();
ok(room > 0 && at > 0, '(setup) the stories row scrolls sideways', { room, at });
/* open a story further along, then close it */
await page.evaluate(() => { const b = [...document.querySelectorAll('.stories .story')].find(x => x.getBoundingClientRect().left > 100); b.click(); }); await page.waitForTimeout(500);
ok(await page.evaluate(() => !!document.querySelector('#sheet .sheet')), '(setup) the story opened');
ok(Math.abs(await sl() - at) < 2, 'stories: still where you left them with the story open', { now: await sl(), at });
await page.evaluate(() => document.querySelector('#sheet .scrim').click()); await page.waitForTimeout(500);
ok(Math.abs(await sl() - at) < 2, 'stories: still where you left them after closing it', { now: await sl(), at });
/* a background redraw (data landing) */
await page.evaluate(() => render(true)); await page.waitForTimeout(200);
ok(Math.abs(await sl() - at) < 2, 'stories: a background redraw keeps the place', { now: await sl(), at });
/* go to a friend's page and come back */
await page.evaluate(() => document.querySelector('.hfeed .fcard .top[data-a="openFriend"]').click()); await page.waitForTimeout(500);
await page.evaluate(() => document.querySelector('[data-a="back"]').click()); await page.waitForTimeout(500);
ok(Math.abs(await sl() - at) < 2, 'stories: coming back to Home keeps the place', { now: await sl(), at });
/* Friends tab: People you might know */
await page.evaluate(() => document.querySelector('[data-a="tab"][data-x="friends"]').click()); await page.waitForTimeout(600);
const hs = await page.evaluate(() => { const h = document.querySelector('#fbody .hscroll'); if (!h) return null; h.style.scrollSnapType = 'none'; h.scrollLeft = 120; return { at: h.scrollLeft, room: h.scrollWidth - h.clientWidth }; });
if (hs && hs.room > 0) {
  await page.evaluate(() => fRepaint()); await page.waitForTimeout(150);
  const now = await page.evaluate(() => document.querySelector('#fbody .hscroll').scrollLeft);
  ok(Math.abs(now - hs.at) < 2, 'people you might know: a redraw (after Add) keeps the place', { now, at: hs.at });
} else console.log('  (skip) no sideways people row in this fixture', hs);
/* opening a different screen fresh starts at the beginning */
await page.evaluate(() => document.querySelector('[data-a="tab"][data-x="home"]').click()); await page.waitForTimeout(600);
ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); console.log(`hx-test: ${pass} passed, ${fail} failed`);
