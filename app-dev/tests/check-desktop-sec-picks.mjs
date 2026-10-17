/* check-desktop-sec-picks — the website side of the 2026-10-16 security picks (app-dev/patches/sec-picks-2026-10-16.py,
   server side sql/professify-security-picks-2026-10-16.sql). Real index.html in Chromium, signed in, PostgREST stand-in.
   classmates  1. strangers come back with codes = [] and a count: the card reads "N classes in common", no class chips;
                  friends-of-friends suggestions with shared_codes = null still render; old servers (codes present) still chip
   trending    2. the strip asks trending_profs for a floor of 3, and draws what comes back
   push        3. pushEnable saves through claim_push_subscription; a database without it falls back to the plain upsert;
                  a real error from the function is reported (not papered over with the upsert)
   Run: APP_DIR=<repo> node check-desktop-sec-picks.mjs [--only classmates|trending|push] [--quiet]   (APP_PORT to move off 8190) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import fs from 'node:fs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const SHOTS = process.env.SHOTS || '';
const shot = async (page, name) => { if (SHOTS) { fs.mkdirSync(SHOTS, { recursive: true }); await page.evaluate(() => { try { setTheme('dark'); } catch (e) {} document.documentElement.setAttribute('data-theme', 'dark'); }); await page.waitForTimeout(400); await page.screenshot({ path: SHOTS + '/' + name + '.png' }); } };
const T = {};
const test = (name, fn) => { T[name] = fn; };

const U1 = '22222222-2222-4222-8222-222222222201', U2 = '22222222-2222-4222-8222-222222222202', U3 = '22222222-2222-4222-8222-222222222203';
const sugText = page => page.evaluate(() => [...document.querySelectorAll('#frSuggestedOut .frv2-card')].map(c => ({
  name: c.querySelector('h4').textContent.trim(), why: c.querySelector('.frv2-why').textContent.trim(), chips: c.querySelectorAll('.fr-cchip').length,
  eyebrow: c.querySelector('.frv2-eyebrow').textContent.trim() })));
const openFriends = async page => {
  await page.evaluate(() => { show('friends'); loadFriendsData(); }); await tick(page, 1800);
  await page.evaluate(async () => { await loadClassmateSuggestions(); renderFriends(); }); await tick(page, 600);
};

test('classmates', async () => {
  /* the new server: a stranger's class codes are gone, the count stays; suggest_friends returns shared_codes = null */
  const rpc = Object.assign({}, FX.RPC, {
    suggest_classmates_v2: [
      { id: U1, display_name: 'Morgan Two', username: 'mtwo', avatar_url: null, overlap: 2, codes: [] },
      { id: U2, display_name: 'Casey One', username: 'cone', avatar_url: null, overlap: 1, codes: [] },
    ],
    suggest_friends: [{ id: U3, display_name: 'Drew Mutual', username: 'dmut', avatar_url: null, reason: '3 mutual friends', mutuals: 3, score: 54, shared_codes: null }],
  });
  const { page, close, log } = await desk({ tables: FX.TABLES, rpc }); await tick(page, 1500);
  await openFriends(page);
  const cards = await sugText(page);
  const by = n => cards.find(c => c.name === n) || {};
  ok(by('Morgan Two').why === '2 classes in common' && by('Morgan Two').chips === 0, 'a stranger sharing 2 classes: "2 classes in common", no chips', cards);
  ok(by('Casey One').why === '1 class in common' && by('Casey One').chips === 0, 'a stranger sharing 1 class: "1 class in common" (singular), no chips', cards);
  ok(/In your classes/.test(by('Morgan Two').eyebrow), 'the eyebrow still says "In your classes · not friends yet"', by('Morgan Two'));
  ok(by('Drew Mutual').why === '3 mutual friends' && by('Drew Mutual').chips === 0, 'a mutual-friends suggestion (shared_codes = null) renders its server sentence, no chips', by('Drew Mutual'));
  ok(!cards.some(c => /undefined|null|NaN/.test(c.why + c.name)), 'no "undefined" / "null" / "NaN" on any card', cards);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await shot(page, 'after-classmates-desktop-dark');
  await close();
  /* an older server that still sends codes: chips come back (nothing is lost on a deploy that has not run the SQL) */
  const rpc2 = Object.assign({}, FX.RPC, { suggest_classmates_v2: [{ id: U1, display_name: 'Morgan Two', username: 'mtwo', avatar_url: null, overlap: 2, codes: ['BUS 3438', 'ECON 2303'] }] });
  const b = await desk({ tables: FX.TABLES, rpc: rpc2 }); await tick(b.page, 1500);
  await openFriends(b.page);
  const old = await sugText(b.page);
  ok(old.some(c => c.name === 'Morgan Two' && c.chips === 2), 'old server (codes present): the two class chips still show', old);
  await shot(b.page, 'before-classmates-desktop-dark');
  await b.close();
  /* phone width */
  const p = await openApp({ tables: FX.TABLES, rpc, path: '/', width: 390, height: 844, wait: 4000 }); await tick(p.page, 1500);
  await openFriends(p.page);
  const pc = await sugText(p.page);
  ok(pc.some(c => c.why === '2 classes in common'), 'phone width: the same card text', pc);
  ok(await p.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'phone width: no sideways scroll');
  await shot(p.page, 'after-classmates-phone-390');
  await p.close();
});

test('trending', async () => {
  const { page, close, log } = await desk({ tables: FX.TABLES, rpc: Object.assign({}, FX.RPC, { trending_profs: [] }) }); await tick(page, 1500);
  await page.evaluate(() => { show('explore'); setExMode('professors'); renderExplore(); }); await tick(page, 800);
  const hasWrap = await page.evaluate(() => !!document.getElementById('trendWrap'));
  ok(hasWrap, 'set-up: the Explore professor list has the trending strip slot');
  const calls = log.rpcs.filter(r => r.fn === 'trending_profs');
  ok(calls.length >= 1 && calls.every(c => c.body && c.body.p_min === 3 && c.body.p_limit === 10), 'trending_profs is asked for p_min 3 (p_limit 10)', calls);
  ok(await page.evaluate(() => document.getElementById('trendWrap').innerHTML === ''), 'an empty answer draws nothing');
  /* a professor three students looked at is drawn */
  const key = await page.evaluate(() => Object.keys(profIdByKey())[0]);
  await close();
  const b = await desk({ tables: FX.TABLES, rpc: Object.assign({}, FX.RPC, { trending_profs: [{ prof_key: key, viewers: 3 }] }) }); await tick(b.page, 1500);
  await b.page.evaluate(() => { show('explore'); setExMode('professors'); renderExplore(); }); await tick(b.page, 1200);
  const txt = await b.page.evaluate(() => document.getElementById('trendWrap') ? document.getElementById('trendWrap').textContent : null);
  ok(txt && /3/.test(txt) && txt.length > 5, 'a professor with 3 viewers is drawn in the strip', txt);
  ok(b.log.errors.length === 0, 'no page errors', b.log.errors);
  await shot(b.page, 'after-trending-desktop-dark');
  await b.close();
});

const fakePush = (endpoint) => () => {
  window.PROFESSIFY_CONFIG = Object.assign(window.PROFESSIFY_CONFIG || {}, { VAPID_PUBLIC_KEY: 'BAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' });
  Notification.requestPermission = async () => 'granted';
  const sub = { endpoint: '__EP__', toJSON() { return { endpoint: '__EP__', keys: { p256dh: 'P256', auth: 'AUTHK' } }; } };
  const reg = { pushManager: { getSubscription: async () => sub, subscribe: async () => sub }, };
  try { Object.defineProperty(navigator.serviceWorker, 'ready', { get: () => Promise.resolve(reg), configurable: true }); } catch (e) { navigator.serviceWorker.ready = Promise.resolve(reg); }
};
const EP = 'https://fcm.googleapis.com/fcm/send/abc123';

test('push', async () => {
  const initFor = () => `(${fakePush(EP).toString().replace(/__EP__/g, EP)})()`;
  /* 1. the function exists: one rpc call, no table write */
  let o = await desk({ tables: FX.TABLES, init: initFor() }); await tick(o.page, 1500);
  let r = await o.page.evaluate(() => pushEnable());
  const claim = o.log.rpcs.filter(x => x.fn === 'claim_push_subscription');
  ok(r.ok === true, 'pushEnable succeeds through the function', r);
  ok(claim.length === 1 && claim[0].body.p_endpoint === EP && claim[0].body.p_p256dh === 'P256' && claim[0].body.p_auth === 'AUTHK' && typeof claim[0].body.p_ua === 'string', 'it calls claim_push_subscription(endpoint, p256dh, auth, ua)', claim);
  ok(!o.log.writes.some(w => w.table === 'push_subscriptions'), 'and writes nothing to the table directly', o.log.writes.filter(w => /push/.test(w.table)));
  await o.close();
  /* 2. the function is not installed: falls back to the old upsert */
  const missing = Object.assign({}, FX.RPC, { claim_push_subscription: { __error: { code: 'PGRST202', message: 'Could not find the function public.claim_push_subscription(p_auth, p_endpoint, p_p256dh, p_ua) in the schema cache' } } });
  o = await desk({ tables: FX.TABLES, rpc: missing, init: initFor() }); await tick(o.page, 1500);
  r = await o.page.evaluate(() => pushEnable());
  const up = o.log.writes.filter(w => w.table === 'push_subscriptions' && w.m === 'POST');
  ok(r.ok === true && up.length === 1 && /on_conflict=endpoint/.test(up[0].query) && up[0].body.endpoint === EP && up[0].body.user_id === FX.ME.id, 'function missing: the old upsert on endpoint is used and succeeds', { r, up });
  await o.close();
  /* 3. a real error from the function (e.g. the endpoint is refused) is reported, not retried through the table */
  const bad = Object.assign({}, FX.RPC, { claim_push_subscription: { __error: { code: '23514', message: 'new row for relation "push_subscriptions" violates check constraint "push_subs_endpoint_is_push_service"' } } });
  o = await desk({ tables: FX.TABLES, rpc: bad, init: initFor() }); await tick(o.page, 1500);
  r = await o.page.evaluate(() => pushEnable());
  ok(r.ok === false && r.why === 'save-failed' && !o.log.writes.some(w => w.table === 'push_subscriptions'), 'a real error: save-failed, and no fallback write', { r, w: o.log.writes.filter(w => /push/.test(w.table)) });
  await o.close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-sec-picks: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
