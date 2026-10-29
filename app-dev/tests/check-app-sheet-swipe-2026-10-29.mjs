import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 10000 });
const cdp = await page.context().newCDPSession(page);
const openStory = async () => { await page.evaluate(() => { A.closeSheet(); }); await page.waitForTimeout(200); await page.evaluate(() => document.querySelector('.stories .story').click()); await page.waitForTimeout(500); };
const open = () => page.evaluate(() => !!document.querySelector('#sheet .sheet') && UI.sheet && UI.sheet.type);
const box = () => page.evaluate(() => { const r = document.querySelector('#sheet .sheet').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + 60 }; });
const swipe = async (dx, dy, steps = 8, pause = 12) => { const b = await box(); await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: b.x, y: b.y }] });
  for (let i = 1; i <= steps; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: b.x + dx * i / steps, y: b.y + dy * i / steps }] }); await page.waitForTimeout(pause); }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await page.waitForTimeout(450); };
await openStory(); ok(await open() === 'story', '(setup) a story’s day is open');
await swipe(0, 220); ok(!(await open()), 'swipe down 220px: the story closes');
await openStory(); await swipe(0, 60, 10, 40); ok(await open() === 'story', 'a short, slow pull (60px) springs back and stays open');
ok(await page.evaluate(() => document.querySelector('#sheet .sheet').style.transform === '' || /translateY\(0/.test(document.querySelector('#sheet .sheet').style.transform)), 'after springing back the sheet sits where it was');
await swipe(0, 70, 3, 5); ok(!(await open()), 'a quick flick down (70px) closes it');
await openStory(); await swipe(0, -200); ok(await open() === 'story', 'swiping up never closes it');
await swipe(220, 30); ok(await open() === 'story', 'a sideways swipe never closes it');
/* a long sheet scrolled down scrolls back up instead of closing */
const sc = await page.evaluate(() => { const b = document.querySelector('#sheet .sbody'); b.style.maxHeight = '200px'; b.style.overflowY = 'auto'; const pad = document.createElement('div'); pad.style.height = '900px'; b.appendChild(pad); b.scrollTop = 150; return b.scrollTop; });
await swipe(0, 220); ok(sc > 0 && await open() === 'story', 'with its content scrolled down, a downward swipe scrolls — it doesn’t close', sc);
/* other sheets: the section preview */
await page.evaluate(() => { A.closeSheet(); }); await page.waitForTimeout(200);
const opened = await page.evaluate(() => { const b = document.querySelector('.hfeed .g-b[data-a="secSheet"]'); if (!b) return false; b.click(); return true; }); await page.waitForTimeout(500);
if (opened) { const t = await open(); await swipe(0, 220); ok(t && !(await open()), 'the section preview closes the same way', t); }
ok(log.errors.length === 0, 'no page errors (touch)', log.errors);
await close();
/* the Desktop preview: a mouse drag */
const d = await openApp({ width: 390, height: 844, touch: false });
await d.page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 10000 });
await d.page.evaluate(() => document.querySelector('.stories .story').click()); await d.page.waitForTimeout(500);
const b2 = await d.page.evaluate(() => { const r = document.querySelector('#sheet .sheet').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + 60 }; });
await d.page.mouse.move(b2.x, b2.y); await d.page.mouse.down(); for (let i = 1; i <= 10; i++) { await d.page.mouse.move(b2.x, b2.y + 22 * i); await d.page.waitForTimeout(10); } await d.page.mouse.up(); await d.page.waitForTimeout(450);
ok(!(await d.page.evaluate(() => !!document.querySelector('#sheet .sheet'))), 'preview: a mouse drag down closes the story');
await d.page.evaluate(() => document.querySelector('.stories .story').click()); await d.page.waitForTimeout(500);
ok(await d.page.evaluate(() => UI.sheet && UI.sheet.type) === 'story', 'preview: a plain click still opens a story (no swallowed clicks)');
ok(d.log.errors.length === 0, 'no page errors (mouse)', d.log.errors);
await d.close();
console.log(`swd-test: ${pass} passed, ${fail} failed`);
