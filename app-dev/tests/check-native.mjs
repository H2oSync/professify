// check-native.mjs — the iPhone app's switches (2026-10-06), on the real app/index.html.
//   APP_DIR=<repo root> APP_PORT=8191 node check-native.mjs
// A stand-in window.Capacitor (isNativePlatform → true, a fake PushNotifications plugin that records
// calls and answers like iOS) is injected before the page runs, exactly where Capacitor's native
// bridge would put it. The same checks run once without it, to prove the website is unchanged.
import { openApp } from './app-harness.mjs';

let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, d === undefined ? '' : JSON.stringify(d)); } };
const tick = (p, ms = 300) => p.waitForTimeout(ms);
const click = async (p, sel) => { await p.locator(sel).first().click(); await tick(p, 250); };

const nativeShim = (perm) => `
  window.__push = { calls: [], perm: ${JSON.stringify(perm)}, listeners: {} };
  const P = {
    checkPermissions: async () => { __push.calls.push('check'); return { receive: __push.perm }; },
    requestPermissions: async () => { __push.calls.push('request'); __push.perm = 'granted'; return { receive: 'granted' }; },
    register: async () => { __push.calls.push('register'); setTimeout(() => (__push.listeners.registration || []).forEach(f => f({ value: 'AB'.repeat(32) })), 20); },
    addListener: (ev, f) => { (__push.listeners[ev] = __push.listeners[ev] || []).push(f); return Promise.resolve({ remove() {} }); },
  };
  window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { PushNotifications: P } };
`;

async function settings(page) { await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500); }

console.log('# web (no Capacitor): unchanged');
{
  const { page, close, log } = await openApp({ width: 1280, height: 900, port: 8191 });
  ok(await page.evaluate(() => window.TC_NATIVE === false && !document.documentElement.classList.contains('native')), 'web: not native');
  ok(await page.locator('.side').isVisible(), 'web, wide window: the desk panel still shows');
  await settings(page);
  const body = await page.locator('#scroll').innerText();
  ok(!/Seat alerts/.test(body), 'web: no Notifications section');
  ok(/not affiliated with or endorsed by Cal Poly/.test(body), 'web: About says not affiliated');
  ok(/phone app · build/.test(body), 'web: About still says "phone app"');
  ok(!log.errors.length, 'web: no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# iPhone app, notifications never asked');
{
  const { page, close, log } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('prompt') });
  ok(await page.evaluate(() => window.TC_NATIVE === true && document.documentElement.classList.contains('native') && document.documentElement.classList.contains('pm')), 'native: html.native + phone mode');
  ok(!(await page.locator('.side').isVisible()), 'native: the desk panel is hidden');
  ok(await page.evaluate(() => !(window.__push.calls.includes('request'))), 'native: no permission prompt at launch');
  ok(await page.evaluate(() => navigator.serviceWorker ? navigator.serviceWorker.getRegistrations().then(r => r.length === 0) : true), 'native: no service worker registered');
  await settings(page);
  let body = await page.locator('#scroll').innerText();
  ok(/Seat alerts/.test(body) && await page.locator('[data-a="pushOn"]').count() === 1, 'native: Settings → Notifications with a Turn on button');
  ok(/for iPhone · build/.test(body), 'native: About says "for iPhone"');
  await click(page, '[data-a="pushOn"]'); await tick(page, 400);
  const calls = await page.evaluate(() => window.__push.calls);
  ok(calls.includes('request') && calls.includes('register'), 'native: Turn on asks iOS, then registers', calls);
  const reg = log.rpcs.filter(r => r.fn === 'register_push_device');
  ok(reg.length === 1 && reg[0].body.p_token === 'AB'.repeat(32) && reg[0].body.p_platform === 'ios', 'native: the token is filed with register_push_device', reg);
  body = await page.locator('#scroll').innerText();
  ok(/Seat alerts/.test(body) && /Anything overnight waits until 8am/.test(body) && await page.locator('[data-a="pushOn"]').count() === 0, 'native: Settings now says alerts are on');
  ok(!log.errors.length, 'native: no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# iPhone app, already allowed: re-registers quietly on launch');
{
  const { page, close, log } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('granted') });
  await tick(page, 600);
  const calls = await page.evaluate(() => window.__push.calls);
  ok(!calls.includes('request') && calls.includes('register'), 'native: no prompt, token refreshed', calls);
  ok(log.rpcs.some(r => r.fn === 'register_push_device'), 'native: refreshed token filed');
  await page.evaluate(() => (window.__push.listeners.pushNotificationActionPerformed || []).forEach(f => f({ notification: { data: { url: '/?tab=sched' } } })));
  await tick(page, 400);
  ok(await page.locator('.tabbar .tab.on[data-x="schedule"]').count() === 1, 'native: tapping a seat alert opens Schedule');
  await page.evaluate(() => (window.__push.listeners.pushNotificationActionPerformed || []).forEach(f => f({ notification: { data: { url: '/?tab=friends' } } })));
  await tick(page, 400);
  ok(await page.locator('.tabbar .tab.on[data-x="friends"]').count() === 1, 'native: a friend alert opens Friends');
  await click(page, '.tabbar .tab[data-x="home"]');
  await settings(page);
  await click(page, '[data-a="signOut"]'); await tick(page, 800);
  ok(log.rpcs.some(r => r.fn === 'unregister_push_device' && r.body.p_token === 'AB'.repeat(32)), 'native: signing out unregisters this phone');
  await close();
}

console.log('# iPhone app, said no before');
{
  const { page, close } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('denied') });
  await settings(page);
  const body = await page.locator('#scroll').innerText();
  ok(/iPhone Settings app → TermChamp → Notifications/.test(body) && await page.locator('[data-a="pushOn"]').count() === 0, 'native: denied → points to iPhone Settings, no dead button');
  await close();
}

console.log(`\ncheck-native: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
