/* Regression for 1.0.1 build 3 (Tate, 2026-10-29: "when you click something it wont let you click
   anything else after"): after swiping a sheet down (or a short pull that springs back, or a tab
   swipe), real taps — touch + the phone's synthesized mouse events + click — must still work. */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready && document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 10000 });
const cdp = await page.context().newCDPSession(page);
const center = sel => page.evaluate(s => { const r = document.querySelector(s).getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }, sel);
const tap = async sel => { const c = await center(sel); await page.touchscreen.tap(c.x, c.y); await page.waitForTimeout(450); };
const drag = async (x, y, dx, dy, steps = 8) => { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
  for (let i = 1; i <= steps; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + dx * i / steps, y: y + dy * i / steps }] }); await page.waitForTimeout(12); }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await page.waitForTimeout(450); };
const sheetTop = () => page.evaluate(() => { const r = document.querySelector('#sheet .sheet').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + 60 }; });
const tabBtn = t => `[data-a="tab"][data-v="${t}"], .tabbar [data-tab="${t}"]`;
const sel = await page.evaluate(() => !!document.querySelector('.tabbar [data-x="home"]') && !!document.querySelector('.tabbar [data-x="explore"]'));
ok(sel, '(setup) found the Home and Explore tab buttons');
/* 1: tap a story, swipe its day down, then tap Explore */
await tap('.stories .story'); ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'story', 'tapping a story opens its day');
let b = await sheetTop(); await drag(b.x, b.y, 0, 230); ok(!(await page.evaluate(() => !!document.querySelector('#sheet .sheet'))), 'swiping it down closes it');
await tap('.tabbar [data-x="explore"]'); ok(await page.evaluate(() => S.tab) === 'explore', 'then a tap on Explore still works', await page.evaluate(() => S.tab));
await tap('.tabbar [data-x="home"]'); ok(await page.evaluate(() => S.tab) === 'home', 'and a tap back on Home works');
await page.waitForFunction(() => document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 5000 });
await tap('.stories .story'); ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'story', 'and a tap on a story opens it again');
/* 2: a short pull that springs back, then close with X, then tap */
b = await sheetTop(); await drag(b.x, b.y, 0, 50, 10); ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'story', 'a short pull springs back');
await page.evaluate(() => A.closeSheet()); await page.waitForTimeout(300);
await tap('.tabbar [data-x="explore"]'); ok(await page.evaluate(() => S.tab) === 'explore', 'after a spring-back, taps still work');
/* 3: a tab swipe, then taps */
await tap('.tabbar [data-x="home"]');
await drag(300, 600, -220, 0, 8); await page.waitForTimeout(300); ok(await page.evaluate(() => S.tab) === 'explore', 'a swipe left moves Home → Explore', await page.evaluate(() => S.tab));
await tap('.tabbar [data-x="home"]'); ok(await page.evaluate(() => S.tab) === 'home', 'after a tab swipe, taps still work');
/* 4: ten taps in a row after a swipe-close */
await page.waitForFunction(() => document.querySelectorAll('.stories .story').length >= 2, null, { timeout: 5000 });
await tap('.stories .story'); b = await sheetTop(); await drag(b.x, b.y, 0, 230);
let n = 0; for (let i = 0; i < 5; i++) { await tap('.tabbar [data-x="explore"]'); if (await page.evaluate(() => S.tab) === 'explore') n++; await tap('.tabbar [data-x="home"]'); if (await page.evaluate(() => S.tab) === 'home') n++; }
ok(n === 10, '10 taps in a row after a swipe-close all land', n);
ok(log.errors.length === 0, 'no page errors', log.errors);
await close();
console.log(`tap-after-swipe: ${pass} passed, ${fail} failed`);
