import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const shot = process.argv[2];
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 10000 });
const cdp = await page.context().newCDPSession(page);
const T = (type, x, y) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: type === 'touchEnd' ? [] : [{ x, y }] });
const m = () => page.evaluate(() => { const sc = document.getElementById('scroll'), g = document.querySelector('.tswghost'), tx = s => { const t = getComputedStyle(s).transform; return t === 'none' ? 0 : Math.round(+t.split(',')[4]); };
  return { tab: S.tab, ghost: !!g, gtext: g ? g.innerText.slice(0, 20) : '', cur: tx(sc), gx: g ? tx(g) : null, op: getComputedStyle(sc).opacity, filter: getComputedStyle(sc).filter, inline: sc.style.transform }; });
/* 1. a slide that's still held: it doesn't sit halfway — it glides to Explore on its own */
await T('touchStart', 340, 420); for (let i = 1; i <= 3; i++) { await T('touchMove', 340 - 14 * i, 421); await page.waitForTimeout(16); }   // 42px, then the finger stops
await page.waitForTimeout(120); const during = await m(); if (shot) await page.screenshot({ path: shot });
ok(during.ghost && /Explore/.test(during.gtext) && during.cur < -60, 'once it’s clearly a slide, Explore glides in by itself (no holding needed)', during);
ok(during.op === '1' && during.filter === 'none', 'no fade or blur while it glides', during);
for (let i = 1; i <= 6; i++) { await T('touchMove', 298 + 20 * i, 421); await page.waitForTimeout(16); }   // drag back the other way while it glides
await page.waitForTimeout(300); let st = await m();
ok(st.tab === 'explore' && !st.ghost && st.inline === '', 'it lands on Explore even if the finger keeps moving — no stopping in between', st);
await T('touchEnd'); await page.waitForTimeout(200);
ok((await m()).tab === 'explore', 'letting go afterwards changes nothing', await m());
/* 2. below the slide threshold nothing moves at all */
await T('touchStart', 300, 420); for (let i = 1; i <= 4; i++) { await T('touchMove', 300 - 6 * i, 421); await page.waitForTimeout(20); }
const small = await m(); await T('touchEnd'); await page.waitForTimeout(300);
ok(!small.ghost && small.cur === 0 && (await m()).tab === 'explore', 'a 24px nudge: nothing moves, stays on Explore', small);
/* 3. timing: from the start of the slide to landing is quick */
const t0 = Date.now(); await T('touchStart', 340, 420); for (let i = 1; i <= 3; i++) { await T('touchMove', 340 - 15 * i, 421); await page.waitForTimeout(8); } await T('touchEnd');
await page.waitForFunction(() => S.tab === 'rate' && !document.querySelector('.tswghost'), null, { timeout: 2000 }).catch(() => {});
const took = Date.now() - t0; ok((await m()).tab === 'rate' && took < 650, 'a quick slide lands on Rate fast', { took });
ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); console.log(`tsw2-test: ${pass} passed, ${fail} failed`);
