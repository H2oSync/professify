/* check-desktop-friend-regday — a friend's registration day on their page (website-friend-regday, Tate 2026-10-14; the phone's
   registration-day 2026-10-11: "Registers Wed, Oct 21 · 8a · 2 days before you" on a friend's page). Runs the REAL index.html
   in Chromium, signed in, against the PostgREST stand-in.
   Run: APP_DIR=<repo> node check-desktop-friend-regday.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: a friend who shared a day still to come has "Registers Wed, Oct 21, 2026 · 8a" (the year is written) under
   their name, with "· 2 days before you" / "same day as you" / "after you" only when you've set yours; "Registers today at 8a"
   on the day; NOTHING (no line, no placeholder) when they didn't share, the day has passed, the function is missing, the
   load failed, or registering isn't what you're doing; only accepted friends' days (the cards' rows); the list is asked once
   (not per page) and a list that arrives while the page is open fills the line in; text holds 4.5:1 in light and dark. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const NOW = '2026-10-14T10:30:00-07:00';
let portN = 0; const BASE = +(process.env.APP_PORT || 8190);
const open = [];
const desk = async (o = {}) => { const a = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: NOW, port: BASE + (portN++ % 3) }, o)); open.push(a); return a; };
const T = {};
const test = (name, fn) => { T[name] = fn; };
const ME = FX.ME.id, [AVERY, ROWAN, SKY, QUINN, HARPER] = FX.FRIENDS.map(f => f.id);
const withDay = row => { const t = JSON.parse(JSON.stringify(FX.TABLES)); t.registration_days = row ? [Object.assign({ user_id: ME, term: '2274', shared: true, updated_at: '2026-10-13T00:00:00Z' }, row)] : []; return t; };
const rpcWith = rows => Object.assign({}, FX.RPC, { friend_registration_days: rows });
const DAYS = [{ user_id: AVERY, day: '2026-10-21', at_time: '08:00:00' }, { user_id: ROWAN, day: '2026-10-19', at_time: null }, { user_id: SKY, day: '2026-10-10', at_time: '09:00:00' }];
const withTheme = t => `try{localStorage.setItem('professify-theme',${JSON.stringify(t)})}catch(e){}`;
/* the line on a friend's page: its text, and whether it takes any room */
const lineOf = async (page, id) => {
  await page.evaluate(id => { closeFriendProfile && closeFriendProfile(); openFriendProfile(id); }, id); await tick(page, 500);
  return page.evaluate(() => { const e = document.querySelector('#frpModal .rg-frrow'); return e ? { text: e.innerText.replace(/\s+/g, ' ').trim(), shown: getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().height > 0, name: document.querySelector('#frpModal .frp-nameline h2').textContent } : null; });
};

test('line', async () => {
  const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), rpc: rpcWith(DAYS) }); await tick(page, 2000);
  let l = await lineOf(page, AVERY);
  ok(l && l.name === 'Avery Quill' && l.text === 'Registers Wed, Oct 21, 2026 · 8a · same day as you' && l.shown, 'Avery shared Oct 21 8a, the day you registered: “Registers Wed, Oct 21, 2026 · 8a · same day as you” (with its year)', l);
  l = await lineOf(page, ROWAN);
  ok(l && l.text === 'Registers Mon, Oct 19, 2026 · 2 days before you', 'Rowan shared a day and no time: no time is made up (“…Oct 19, 2026 · 2 days before you”)', l);
  l = await lineOf(page, SKY);
  ok(l && l.text === '' && !l.shown, 'Sky’s day (Oct 10) has passed: nothing, and the empty line takes no room', l);
  l = await lineOf(page, QUINN);
  ok(l && l.text === '' && !l.shown, 'Quinn shared nothing: nothing at all (no “not shared”, no gap)', l);
  l = await lineOf(page, HARPER);
  ok(l && l.text === '' && !l.shown, 'Harper shared nothing: nothing', l);
  const calls = log.rpcs.filter(r => r.fn === 'friend_registration_days');
  ok(calls.length === 1 && JSON.stringify(calls[0].args || calls[0].body || {}).includes('2274'), 'the days were asked once for term 2274, not once per page', calls);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

test('relative', async () => {
  /* yours isn't set: nothing to compare with, so no “before you” */
  { const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(DAYS) }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === 'Registers Wed, Oct 21, 2026 · 8a', 'no day of yours: just “Registers Wed, Oct 21, 2026 · 8a”', l); await close(); }
  /* after you */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-19', at_time: '09:00:00' }), rpc: rpcWith(DAYS) }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === 'Registers Wed, Oct 21, 2026 · 8a · 2 days after you', 'you on Oct 19: “… · 2 days after you”', l); await close(); }
  /* today, and a minutes time */
  { const rows = [{ user_id: AVERY, day: '2026-10-21', at_time: '08:30:00' }];
    const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(rows), time: '2026-10-21T09:30:00-07:00' }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === 'Registers today at 8:30a', 'on the day: “Registers today at 8:30a”', l); await close(); }
});

test('absent', async () => {
  /* the function isn't there (RUN 17 not run): nothing, no error */
  { const hook = url => url.pathname === '/rest/v1/rpc/friend_registration_days' ? { status: 404, body: JSON.stringify({ code: 'PGRST202', message: 'Could not find the function public.friend_registration_days(p_term) in the schema cache' }) } : null;
    const { page, close, log } = await desk({ tables: withDay(null), hook }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === '' && !l.shown, 'no function: nothing on the page', l);
    ok(log.errors.length === 0, 'no function: no page errors', log.errors); await close(); }
  /* the load failed */
  { const hook = url => url.pathname === '/rest/v1/rpc/friend_registration_days' ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null;
    const { page, close } = await desk({ tables: withDay(null), hook }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === '' && !l.shown, 'a failed load: nothing (no error line on a friend’s page)', l); await close(); }
  /* registering isn't what you're doing: the term you choose in isn't the registration term */
  { const { page, close, log } = await desk({ terms: 'single', tables: withDay(null), rpc: rpcWith(DAYS) }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === '' && !l.shown, 'choosing in another term: nothing', l);
    ok(!log.rpcs.some(r => r.fn === 'friend_registration_days'), 'and the days are not even asked for', log.rpcs.map(r => r.fn)); await close(); }
  /* after Round 1 */
  { const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(DAYS), time: '2026-11-04T10:00:00-08:00' }); await tick(page, 2000);
    const l = await lineOf(page, AVERY);
    ok(l && l.text === '' && !l.shown, 'after Round 1’s last day: nothing', l); await close(); }
  /* only friends: a row for someone who isn't an accepted friend is never drawn */
  { const rows = DAYS.concat([{ user_id: FX.STRANGER.id, day: '2026-10-22', at_time: '10:00:00' }]);
    const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(rows) }); await tick(page, 2000);
    const r = await page.evaluate(() => TCReg.rows().map(x => x.id));
    ok(r.length === 3 && !r.includes(FX.STRANGER.id), 'only accepted friends’ days are listed', r);
    const txt = await page.evaluate(() => document.body.innerText);
    ok(!/Oct 22, 2026/.test(txt), 'and a non-friend’s day is nowhere on the page'); await close(); }
});

test('late', async () => {
  /* the list arrives while the page is open: the line fills in (and nothing was shown meanwhile) */
  let release; const gate = new Promise(r => { release = r; });
  const hook = async url => { if (url.pathname === '/rest/v1/rpc/friend_registration_days') await gate; return null; };
  const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), rpc: rpcWith(DAYS), hook });
  await tick(page, 1500);
  let l = await lineOf(page, AVERY);
  ok(l && l.text === '' && !l.shown, 'before the days arrive: nothing on the open page', l);
  release(); await tick(page, 1500);
  const t = await page.evaluate(() => { const e = document.querySelector('#frpModal .rg-frrow'); return e ? e.innerText.replace(/\s+/g, ' ').trim() : null; });
  ok(t === 'Registers Wed, Oct 21, 2026 · 8a · same day as you', 'when they arrive the open page fills the line in', t);
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
});

const CONTRAST = `window.__rgb = s => { const c = document.createElement('canvas').getContext('2d'); c.fillStyle = '#000'; c.fillStyle = s; c.fillRect(0,0,1,1); const d = c.getImageData(0,0,1,1).data; return [d[0],d[1],d[2],d[3]/255]; };
window.__L = a => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126*f(a[0]) + .7152*f(a[1]) + .0722*f(a[2]); };
window.__ratio = (a, b) => { const x = __L(a), y = __L(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
window.__behind = el => { let layers = []; for (let n = el; n; n = n.parentElement) { const c = __rgb(getComputedStyle(n).backgroundColor); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } } let base = [255,255,255]; layers.reverse().forEach(c => { base = base.map((v, i) => Math.round(c[i] * c[3] + v * (1 - c[3]))); }); return base; };`;
for (const theme of ['light', 'dark']) {
  test('contrast-' + theme, async () => {
    const { page, close } = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), rpc: rpcWith(DAYS), init: withTheme(theme) }); await tick(page, 2000);
    await lineOf(page, AVERY); await page.evaluate(CONTRAST);
    const r = await page.evaluate(() => [...document.querySelectorAll('#frpModal .rg-frrow, #frpModal .rg-frrow b, #frpModal .rg-frrow svg')].map(e => [e.tagName, +__ratio(__rgb(getComputedStyle(e).color), __behind(e)).toFixed(2)]));
    ok(document_theme(await page.evaluate(() => document.documentElement.getAttribute('data-theme')), theme) && r.length === 3 && r.every(x => x[1] >= 4.5), theme + ': the line holds 4.5:1 on the sheet', r);
    await close();
  });
}
const document_theme = (a, b) => a === b;

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
  for (const a of open.splice(0)) { try { await a.close(); } catch (e) {} }
}
console.log(`\ncheck-desktop-friend-regday: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
