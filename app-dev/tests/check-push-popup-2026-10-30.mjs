// Tate, 2026-10-30: "build in the enable notifications as a pop up or something, not that you have to go to settings."
// The phone app's notification pop-ups, on the REAL app/index.html with a stand-in Capacitor (as check-native.mjs):
// the once-per-open queue, the existing-student pop-up and its snooze/cap, the "Notifications are off" variant and its
// one-tap Open Settings ('app-settings:'), the Settings button, the trip back from Settings, web, and no stacking.
// Run from app-dev/tests: APP_DIR=<site> APP_PORT=9061 node check-push-popup-2026-10-30.mjs
import { openApp } from './app-harness.mjs';
import fs from 'node:fs';

let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, d === undefined ? '' : JSON.stringify(d)); } };
const SHOTS = process.env.SHOTS || '/tmp/claude-0/fix/pushask/shots';
const DAY = 864e5;
const T0 = Date.parse('2026-09-29T10:30:00-07:00');   /* the harness's page clock at launch; init scripts may run before it is installed */
const pnow = p => p.evaluate(() => Date.now());   /* the page's clock (installed by the harness), not this process's */

/* a stand-in PushNotifications plugin answering like iOS; document.visibilityState follows window.__vis */
const shim = (perm, { createdDaysAgo = null, ls = {} } = {}) => `
  window.__push = { calls: [], perm: ${JSON.stringify(perm)}, listeners: {}, ask: 'granted' };
  const P = {
    checkPermissions: async () => { __push.calls.push('check'); return { receive: __push.perm }; },
    requestPermissions: async () => { __push.calls.push('request'); if (__push.perm === 'prompt') __push.perm = __push.ask; return { receive: __push.perm }; },
    register: async () => { __push.calls.push('register'); setTimeout(() => (__push.listeners.registration || []).forEach(f => f({ value: 'AB'.repeat(32) })), 20); },
    addListener: (ev, f) => { (__push.listeners[ev] = __push.listeners[ev] || []).push(f); return Promise.resolve({ remove() {} }); },
  };
  window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { PushNotifications: P, StatusBar: { setStyle: () => Promise.resolve() } } };
  window.__vis = 'visible';
  /* the real "Connect contacts" pop-up (contacts-2026-10-30) also queues on an app open — these tests are about notifications, so it's done */
  try { const s0 = JSON.parse(localStorage.getItem('sb-rqkndeqbcahozidniesn-auth-token') || 'null'); if (s0 && s0.user) localStorage.setItem('tc_ct:' + s0.user.id, JSON.stringify({ on: true })); } catch (e) {}
  try { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => window.__vis }); } catch (e) {}
  ${createdDaysAgo == null ? '' : `try { const k = 'sb-rqkndeqbcahozidniesn-auth-token', s = JSON.parse(localStorage.getItem(k)); s.user.created_at = new Date(${T0} - ${createdDaysAgo} * 864e5).toISOString(); localStorage.setItem(k, JSON.stringify(s)); } catch (e) {}`}
  ${Object.keys(ls).length ? `if (!sessionStorage.getItem('__lsDone')) { sessionStorage.setItem('__lsDone', '1'); const L = ${JSON.stringify(ls)}; for (const k in L) localStorage.setItem(k, String(${T0} + L[k])); }` : ''}
`;
const sheetType = p => p.evaluate(() => UI.sheet && UI.sheet.type);
const sheetText = p => p.evaluate(() => { const s = document.querySelector('#sheet .sheet, #sheet'); return s ? s.innerText : ''; });
const run = (p, ms) => p.clock.runFor(ms);
/* another app open: a cold launch, same phone (localStorage kept) */
async function readyOf(page) { for (let i = 0; i < 100; i++) { if (await page.evaluate(() => { try { return !!TC.ready; } catch (e) { return false; } }).catch(() => false)) return true; await run(page, 100); await page.waitForTimeout(30); } return false; }
async function relaunch(page, ms = 3000) { await page.reload(); await readyOf(page); await run(page, ms); }
const ls = (p, k) => p.evaluate(k => localStorage.getItem(k), k);
const tap = async (p, sel) => { await p.locator(sel).first().click(); await run(p, 400); };
async function settings(page) { await tap(page, '.homehdr .me-btn'); await tap(page, '[data-a="openSettings"]'); await run(page, 600); }
async function shot(page, name, dark) {
  await page.evaluate(d => { try { document.documentElement.setAttribute('data-theme', d ? 'dark' : 'light'); } catch (e) {} }, dark);
  await run(page, 500); await page.waitForTimeout(900); fs.mkdirSync(SHOTS, { recursive: true });   /* CSS transitions run on real time */
  await page.screenshot({ path: `${SHOTS}/${name}-${dark ? 'dark' : 'light'}.png` });
}

console.log('# never asked, new on this phone: not on the 1st open, once on the 2nd, snooze, 3 in all');
{
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt') });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === null, '1st open (account age unknown): no pop-up');
  ok(await ls(page, 'tc_app_opens') === '1', '1st open counted', await ls(page, 'tc_app_opens'));
  ok(await page.evaluate(() => !__push.calls.includes('request')), 'iOS is not asked at launch');
  await relaunch(page);
  ok(await sheetType(page) === 'pushAsk' && await page.evaluate(() => UI.sheet.reason) === 'onboarding', '2nd open: the notifications pop-up shows');
  const t = await sheetText(page);
  ok(/Turn on notifications\?/.test(t) && /Open seats, friend requests and messages\. You choose exactly which in Settings\./.test(t), 'pop-up: title + body copy', t);
  ok(await page.locator('#sheet [data-a="pushAllow"]').count() === 1 && await page.locator('#sheet [data-a="pushLater"]').count() === 1, 'pop-up: Turn on + Not now');
  await shot(page, 'pushask-turn-on', false); await shot(page, 'pushask-turn-on', true);
  await page.evaluate(() => document.documentElement.removeAttribute('data-theme'));
  ok(await ls(page, 'tc_push_ask_n') === '1', 'shown count 1');
  ok(await page.evaluate(() => TC.popQueue('open')) === false, 'queue: nothing else this app open');
  await tap(page, '#sheet [data-a="pushLater"]');
  ok(await sheetType(page) === null, 'Not now closes it');
  const snz = +(await ls(page, 'tc_push_snooze'));
  const pn = await pnow(page);
  ok(snz - pn > 6.9 * DAY && snz - pn < 7.1 * DAY, 'Not now: snoozed 7 days', (snz - pn) / DAY);
  await relaunch(page);
  ok(await sheetType(page) === null, '3rd open, inside the week: no pop-up');
  await page.evaluate(() => localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)));   // the week is up, but it's the same day
  await relaunch(page);
  ok(await sheetType(page) === null, 'one pop-up a day: not again the same day, even on another open');
  for (const n of [2, 3]) {
    await page.evaluate(() => { localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)); localStorage.removeItem('tc_pop_day'); });   // the week is up
    await relaunch(page);
    ok(await sheetType(page) === 'pushAsk', `week later: comes back (show ${n})`);
    ok(await ls(page, 'tc_push_ask_n') === String(n), `shown count ${n}`);
    await tap(page, '#sheet [data-a="pushLater"]');
  }
  await page.evaluate(() => { localStorage.setItem('tc_push_snooze', String(Date.now() - 1000)); localStorage.removeItem('tc_pop_day'); });
  await relaunch(page);
  ok(await sheetType(page) === null, 'after 3 shows in all: never again');
  await page.evaluate(() => { localStorage.setItem('tc_push_ask_n', '2'); localStorage.removeItem('tc_pop_day'); });
  await relaunch(page);
  ok(await sheetType(page) === 'pushAsk', '(control) one show left: it shows');
  await tap(page, '#sheet [data-a="pushAllow"]'); await run(page, 600);
  const calls = await page.evaluate(() => __push.calls);
  ok(calls.includes('request') && calls.includes('register') && await sheetType(page) === null, 'Turn on: asks iOS, registers, closes', calls);
  ok(log.rpcs.some(r => r.fn === 'register_push_token'), 'token filed');
  await page.evaluate(() => localStorage.setItem('tc_push_ask_n', '0'));
  await relaunch(page);
  ok(await sheetType(page) === null, 'granted: no pop-up');
  ok(!log.errors.length, 'no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# a student who signed up before this existed: their first open after the update');
{
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 40 }) });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === 'pushAsk', '1st open, account 40 days old: the pop-up shows');
  ok(!log.errors.length, 'no page errors', log.errors.slice(0, 3));
  await close();
}
{
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 0.2 }) });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === null, '1st open, account 5 hours old: no pop-up');
  await close();
}
{
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 40, ls: { tc_push_snooze: 3 * DAY } }) });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === null, 'snoozed (said Not now to the seat/chat ask): no pop-up');
  await close();
}

console.log('# no stacking: another sheet, a chat, Champ');
{
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 40 }), wait: 100 });
  ok(await readyOf(page), 'ready');
  await page.evaluate(() => { UI.sheet = { type: 'addFriend' }; render(true); });
  await run(page, 3000);
  ok(await sheetType(page) === 'addFriend', 'a sheet already open: the pop-up does not replace it');
  await page.evaluate(() => A.closeSheet()); await run(page, 300);
  await run(page, 5000);
  ok(await sheetType(page) === null, '...and does not jump in after it closes (it waits for the next open)');
  await close();
}
{
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 40 }), wait: 100 });
  ok(await readyOf(page), 'ready');
  await page.evaluate(() => { UI.champ = true; render(true); });
  await run(page, 3000);
  ok(await sheetType(page) === null && await page.evaluate(() => UI.champ), 'Champ open: no pop-up over it');
  await close();
}
{
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 40 }), wait: 100 });
  ok(await readyOf(page), 'ready');
  await page.evaluate(() => { S.stack[S.tab].push({ s: 'settings' }); render(true); });
  await run(page, 3000);
  ok(await sheetType(page) === null, 'deep in a tab (not its own screen): no pop-up');
  await close();
}
{
  // the "Connect contacts" pop-up joins the queue ahead of this one: one per app open, then the other
  const init = shim('prompt', { createdDaysAgo: 40 }) + `
    document.addEventListener('DOMContentLoaded', () => { TC.pops.unshift({ kind: 'contacts', due: () => localStorage.getItem('tc_test_contacts') !== 'done',
      show: () => { localStorage.setItem('tc_test_contacts', 'done'); UI.sheet = { type: 'addFriend' }; render(true); } }); });`;
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === 'addFriend' && await ls(page, 'tc_push_ask_n') === null, 'queue: a higher kind shows, the notifications one waits');
  await relaunch(page);
  ok(await sheetType(page) === 'pushAsk', 'queue: next open, the notifications one');
  ok(!log.errors.length, 'no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# said no to iOS before: "Notifications are off", Open Settings in one tap');
{
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('denied', { createdDaysAgo: 40 }) });
  const launches = [];
  page.on('request', r => { if (/^app-settings:/.test(r.url())) launches.push(r.url()); });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === 'pushAsk' && await page.evaluate(() => UI.sheet.reason) === 'off', 'denied, app open: the off pop-up shows');
  const t = await sheetText(page);
  ok(/Notifications are off/.test(t) && /Turn them on in Settings to hear about open seats and messages\./.test(t), 'off: title + body', t);
  ok(await page.locator('#sheet [data-a="pushOpenIOS"]').count() === 1 && await page.locator('#sheet [data-a="pushAllow"]').count() === 0, 'off: Open Settings, no dead Turn on');
  ok(/Open Settings/.test(await page.locator('#sheet [data-a="pushOpenIOS"]').innerText()), 'button says Open Settings');
  await shot(page, 'pushask-off', false); await shot(page, 'pushask-off', true);
  await page.evaluate(() => document.documentElement.removeAttribute('data-theme'));
  const url0 = page.url();
  await tap(page, '#sheet [data-a="pushOpenIOS"]'); await run(page, 300);
  ok(launches.length >= 1, 'Open Settings navigates the page to app-settings:', launches);
  ok(page.url() === url0 && await page.evaluate(() => !!TC.ready && !!PUSH.toSettingsAt), 'the app page stays where it was', page.url());
  ok(await sheetType(page) === null, 'the pop-up closes');
  // back from iPhone Settings with them on
  await page.evaluate(() => { window.__vis = 'hidden'; document.dispatchEvent(new Event('visibilitychange')); });
  await page.evaluate(() => { __push.perm = 'granted'; __push.calls.length = 0; window.__vis = 'visible'; document.dispatchEvent(new Event('visibilitychange')); });
  await run(page, 500);
  const tt = await page.locator('#toast').innerText().catch(() => '');
  ok(/^Notifications on$/.test(tt.trim()) && await page.evaluate(() => __push.calls.includes('register')), 'back from Settings: registers + toast "Notifications on"', { tt, calls: await page.evaluate(() => __push.calls) });
  ok(!log.errors.length, 'no page errors', log.errors.slice(0, 3));
  await close();
}
{
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('denied', { createdDaysAgo: 40, ls: { tc_push_off_at: -10 * DAY } }) });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === null, 'denied, shown 10 days ago: not on open (30-day clock)');
  // right after watching a seat, though
  await page.evaluate(() => TC.pushAsk('seat')); await run(page, 300);
  ok(await sheetType(page) === 'pushAsk' && await page.evaluate(() => UI.sheet.reason) === 'off', 'denied + watch a seat: the off pop-up right after');
  await page.evaluate(() => A.closeSheet()); await run(page, 200);
  await page.evaluate(() => TC.pushAsk('seat')); await run(page, 300);
  ok(await sheetType(page) === null, 'a second seat this run: not again');
  await page.evaluate(() => TC.pushAsk('chat')); await run(page, 300);
  ok(await sheetType(page) === null, 'sending a chat: only on the 30-day clock');
  await close();
}
{
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('denied', { createdDaysAgo: 40, ls: { tc_push_off_at: -31 * DAY } }) });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === 'pushAsk', 'denied, shown 31 days ago: shows again');
  await tap(page, '#sheet [data-a="pushLater"]');
  ok(await sheetType(page) === null && await page.evaluate(() => Date.now() - +localStorage.getItem('tc_push_off_at') < 60000), 'shown again: the 30-day clock restarts; Not now closes');
  ok(await ls(page, 'tc_push_off_n') === '1', '"Notifications are off": counted (1 of 2)');
  await relaunch(page);
  ok(await sheetType(page) === null, 'next open: not again');
  await close();
}
{
  // "Notifications are off" has been shown twice already: never again, on an open or after a tap
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('denied', { createdDaysAgo: 40, ls: { tc_push_off_at: -61 * DAY } }) + "localStorage.setItem('tc_push_off_n', '2');" });
  await readyOf(page); await run(page, 2500);
  ok(await sheetType(page) === null, '"Notifications are off": after 2 shows in all, never again on an open');
  await page.evaluate(() => TC.pushAsk('chat')); await run(page, 300);
  ok(await sheetType(page) === null, '"Notifications are off": nor after sending a chat');
  await close();
}
{
  // the student taps Turn on, then "Don't Allow" in iOS's own dialog: no "off" pop-up the next morning
  const { page, close } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('prompt', { createdDaysAgo: 40 }) + "__push.ask = 'denied';" });
  await readyOf(page); await run(page, 2500);
  await tap(page, '#sheet [data-a="pushAllow"]'); await run(page, 300);
  ok(await page.evaluate(() => PUSH.state) === 'denied' && +(await ls(page, 'tc_push_off_at')) > 0, "Don't Allow in iOS: the 30-day clock starts");
  await relaunch(page);
  ok(await sheetType(page) === null, 'next open: no "off" pop-up right after they said no');
  await close();
}

console.log('# Settings › Notifications when off: a button, not directions');
{
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init: shim('denied') });
  const launches = []; page.on('request', r => { if (/^app-settings:/.test(r.url())) launches.push(r.url()); });
  await readyOf(page); await run(page, 1500);
  ok(await sheetType(page) === null, '1st open: nothing');
  await settings(page);
  const body = await page.locator('#scroll').innerText();
  ok(/Notifications are off for TermChamp/.test(body) && !/Settings › TermChamp › Notifications/.test(body), 'Settings: says off, no directions');
  ok(await page.locator('#scroll [data-a="pushOpenIOS"]').count() === 1 && await page.locator('#scroll [data-a="pushAllow"]').count() === 0, 'Settings: Open Settings button');
  await tap(page, '#scroll [data-a="pushOpenIOS"]'); await run(page, 300);
  ok(launches.length >= 1, 'Settings button: app-settings:', launches);
  ok(!log.errors.length, 'no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# web (no Capacitor): never');
{
  const { page, close, log } = await openApp({ port: +(process.env.APP_PORT || 9061), init: "try{const k='sb-rqkndeqbcahozidniesn-auth-token',s=JSON.parse(localStorage.getItem(k));s.user.created_at='2026-01-01T00:00:00Z';localStorage.setItem(k,JSON.stringify(s));localStorage.setItem('tc_ct:'+s.user.id,JSON.stringify({on:true}));}catch(e){}" });
  await readyOf(page); await run(page, 2500); await relaunch(page);
  ok(await sheetType(page) === null, 'web, 2nd open, old account: no pop-up');
  await page.evaluate(() => { TC.pushAsk('seat'); TC.pushAsk('onboarding'); TC.popQueue('open'); }); await run(page, 500);
  ok(await sheetType(page) === null, 'web: seat/onboarding/queue asks: nothing');
  ok(!log.errors.length, 'no page errors', log.errors.slice(0, 3));
  await close();
}

console.log(`\ncheck-push-popup: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
