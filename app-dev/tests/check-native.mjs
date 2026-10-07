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
  window.__sb = [];
  const SB = { setStyle: o => { __sb.push(o.style); return Promise.resolve(); } };
  window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios', Plugins: { PushNotifications: P, StatusBar: SB } };
`;

async function settings(page) { await click(page, '.homehdr .me-btn'); await click(page, '[data-a="openSettings"]'); await tick(page, 500); }

console.log('# web (no Capacitor): unchanged');
{
  const { page, close, log } = await openApp({ width: 1280, height: 900, port: 8191 });
  ok(await page.evaluate(() => window.TC_NATIVE === false && !document.documentElement.classList.contains('native')), 'web: not native');
  ok(await page.locator('.side').isVisible(), 'web, wide window: the desk panel still shows');
  await settings(page);
  const body = await page.locator('#scroll').innerText();
  ok(/not affiliated with or endorsed by Cal Poly/.test(body), 'web: About says not affiliated');
  ok(/phone app · build/.test(body), 'web: About still says "phone app"');
  ok(await page.locator('[data-a="pushAllow"]').count() === 0, 'web: no "Turn on notifications" button (nothing to turn on in a browser)');
  ok(!log.errors.length, 'web: no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# iPhone app, notifications never asked');
{
  const { page, close, log } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('prompt') });
  await tick(page, 500);
  ok(await page.evaluate(() => window.TC_NATIVE === true && document.documentElement.classList.contains('native') && document.documentElement.classList.contains('pm')), 'native: html.native + phone mode');
  ok(!(await page.locator('.side').isVisible()), 'native: the desk panel is hidden');
  ok(await page.evaluate(() => !window.__push.calls.includes('request')), 'native: iOS is not asked at launch');
  ok(await page.evaluate(() => navigator.serviceWorker ? navigator.serviceWorker.getRegistrations().then(r => r.length === 0) : true), 'native: no service worker registered');
  await settings(page);
  let body = await page.locator('#scroll').innerText();
  ok(/for iPhone · build/.test(body), 'native: About says "for iPhone"');
  ok(/Notifications/.test(body) && await page.locator('#scroll [data-a="pushAllow"]').count() === 1, 'native: Settings › Notifications offers Turn on');
  await click(page, '#scroll [data-a="pushAllow"]'); await tick(page, 600);
  const calls = await page.evaluate(() => window.__push.calls);
  ok(calls.includes('request') && calls.includes('register'), 'native: Turn on asks iOS, then registers', calls);
  const reg = log.rpcs.filter(r => r.fn === 'register_push_token');
  ok(reg.length >= 1 && String(reg[0].body.p_token).toUpperCase() === 'AB'.repeat(32) && reg[0].body.p_platform === 'ios', 'native: the token is filed with register_push_token', reg);
  ok(await page.locator('#scroll [data-a="pushAllow"]').count() === 0 && await page.locator('#scroll [data-a="pushPref"]').count() >= 8, 'native: after allowing, the per-kind switches show and Turn on is gone');
  ok(!log.errors.length, 'native: no page errors', log.errors.slice(0, 3));
  await close();
}

console.log('# iPhone app, already allowed');
{
  const { page, close, log } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('granted') });
  await tick(page, 800);
  const calls = await page.evaluate(() => window.__push.calls);
  ok(!calls.includes('request') && calls.includes('register'), 'native: no prompt, token refreshed on launch', calls);
  ok(log.rpcs.some(r => r.fn === 'register_push_token'), 'native: refreshed token filed');
  const tap = async tc => { await page.evaluate(tc => (window.__push.listeners.pushNotificationActionPerformed || []).forEach(f => f({ notification: { data: { tc } } })), tc); await tick(page, 600); };
  await tap({ t: 'plans' });
  ok(await page.locator('.tabbar .tab.on[data-x="schedule"]').count() === 1, 'native: tapping a registration reminder opens Schedule');
  await tap({ t: 'requests' });
  ok(await page.locator('.tabbar .tab.on[data-x="friends"]').count() === 1, 'native: tapping a friend request opens Friends');
  await click(page, '.tabbar .tab[data-x="home"]');
  await settings(page);
  await click(page, '[data-a="signOut"]'); await tick(page, 900);
  ok(log.rpcs.some(r => r.fn === 'unregister_push_token'), 'native: signing out removes this phone');
  await close();
}

console.log('# iPhone app: status bar text follows the strip behind it');
{
  // signed out on a dark-mode phone: sign-in stays light, so the clock must be dark text
  const { page, close } = await openApp({ width: 390, height: 844, port: 8191, signedIn: false,
    init: nativeShim('prompt') + "try{localStorage.setItem('tc-theme','dark')}catch(e){}" });
  await tick(page, 600);
  let sb = await page.evaluate(() => window.__sb);
  ok(sb.length >= 1 && sb[sb.length - 1] === 'LIGHT', 'native, dark phone, sign-in screen: dark status-bar text on the light strip', sb);
  await close();
}
{
  // signed in, app theme dark: the strip is dark, so light text
  const { page, close } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('prompt') + "try{localStorage.setItem('tc-theme','dark')}catch(e){}" });
  await tick(page, 600);
  const sb = await page.evaluate(() => window.__sb);
  ok(sb[sb.length - 1] === 'DARK', 'native, dark theme, Home: light status-bar text on the dark strip', sb);
  await close();
}
{
  const { page, close } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('prompt') + "try{localStorage.setItem('tc-theme','light')}catch(e){}" });
  await tick(page, 600);
  const sb = await page.evaluate(() => window.__sb);
  ok(sb[sb.length - 1] === 'LIGHT', 'native, light theme, Home: dark status-bar text', sb);
  await close();
}

console.log('# iPhone app, said no before');
{
  const { page, close } = await openApp({ width: 390, height: 844, port: 8191, init: nativeShim('denied') });
  await settings(page); await tick(page, 300);
  const body = await page.locator('#scroll').innerText();
  ok(/Settings › TermChamp › Notifications/.test(body) && await page.locator('#scroll [data-a="pushAllow"]').count() === 0, 'native: denied → points to iPhone Settings, no dead button');
  await close();
}

console.log(`\ncheck-native: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
