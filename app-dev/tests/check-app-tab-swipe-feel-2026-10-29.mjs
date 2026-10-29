import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const shot = process.argv[2];
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 10000 });
const cdp = await page.context().newCDPSession(page);
const T = (type, x, y) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: type === 'touchEnd' ? [] : [{ x, y }] });
/* hold a swipe halfway: the next tab is drawn right beside, the page moves with the finger, nothing fades */
await T('touchStart', 340, 420); for (let i = 1; i <= 10; i++) { await T('touchMove', 340 - 16 * i, 421); await page.waitForTimeout(16); }
const mid = await page.evaluate(() => { const sc = document.getElementById('scroll'), g = document.querySelector('.tswghost'); const m = s => { const t = getComputedStyle(s).transform; return t === 'none' ? 0 : +t.split(',')[4]; };
  return { ghost: !!g, ghostText: g ? g.innerText.slice(0, 40) : '', curX: m(sc), ghostX: g ? m(g) : null, w: sc.clientWidth, op: getComputedStyle(sc).opacity, gop: g ? getComputedStyle(g).opacity : null, filter: getComputedStyle(sc).filter }; });
if (shot) await page.screenshot({ path: shot });
ok(mid.ghost && /Explore/.test(mid.ghostText), 'mid-swipe: Explore is already drawn beside Home', mid);
ok(Math.abs(mid.curX - (-160)) <= 2, 'mid-swipe: Home moves 1:1 with the finger (160px)', mid);
ok(mid.ghostX != null && Math.abs(mid.ghostX - (mid.w + mid.curX)) <= 2, 'mid-swipe: Explore’s edge sits right against Home’s (no gap, no overlap)', mid);
ok(mid.op === '1' && mid.gop === '1' && mid.filter === 'none', 'mid-swipe: no fade and no blur', mid);
await T('touchEnd'); await page.waitForTimeout(450);
const after = await page.evaluate(() => ({ tab: S.tab, ghosts: document.querySelectorAll('.tswghost').length, t: document.getElementById('scroll').style.transform }));
ok(after.tab === 'explore' && after.ghosts === 0 && after.t === '', 'landed on Explore; the ghost is gone and the page sits flat', after);
/* a quick flick lands fast */
const t0 = Date.now(); await T('touchStart', 340, 420); for (let i = 1; i <= 3; i++) { await T('touchMove', 340 - 25 * i, 421); await page.waitForTimeout(8); } await T('touchEnd');
await page.waitForFunction(() => S.tab === 'rate', null, { timeout: 2000 }).catch(() => {}); const took = Date.now() - t0;
ok(await page.evaluate(() => S.tab) === 'rate' && took < 600, 'a quick 75px flick lands on the next tab, fast', { took });
/* pull back before letting go: cancels, nothing left behind */
await T('touchStart', 340, 420); for (let i = 1; i <= 8; i++) { await T('touchMove', 340 - 20 * i, 421); await page.waitForTimeout(16); } for (let i = 1; i <= 8; i++) { await T('touchMove', 180 + 18 * i, 421); await page.waitForTimeout(16); } await T('touchEnd'); await page.waitForTimeout(450);
const back = await page.evaluate(() => ({ tab: S.tab, ghosts: document.querySelectorAll('.tswghost').length, t: document.getElementById('scroll').style.transform }));
ok(back.tab === 'rate' && back.ghosts === 0 && back.t === '', 'drag then pull back: stays on Rate, nothing left behind', back);
ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); console.log(`tsw2-test: ${pass} passed, ${fail} failed`);
