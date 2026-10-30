/* Network resilience fixes (2026-10-30): timeouts, allSettled, auto-recover, 401 refresh, dirty plans, push/seat dedupe.
   Run from app-dev/tests: APP_DIR=/tmp/claude-0/fix/net/site APP_PORT=8801 node /tmp/claude-0/fix/net/tests/net-fix.mjs [section] */
import { openApp } from '/tmp/claude-0/stress/harness.mjs';
const only = process.argv[2];
const PB = +(process.env.PORT_BASE || 0);
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) pass++; else fail++; console.log((c ? '  ok   ' : '  FAIL ') + m + (!c && d !== undefined ? ' ' + JSON.stringify(d).slice(0, 400) : '')); };
const ME = '11111111-1111-4111-8111-111111111111';
const st = page => page.evaluate(() => ({ ready: !!TC.ready, phase: TC.phase, txt: document.body.innerText.replace(/\s+/g, ' ').slice(0, 120) }));
const vis = (page, v) => page.evaluate(v => { Object.defineProperty(document, 'visibilityState', { value: v, configurable: true }); Object.defineProperty(document, 'hidden', { value: v === 'hidden', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }, v);
const run = async (page, ms) => { await page.clock.runFor(ms); await page.waitForTimeout(250); };
const run1 = s => !only || only === s;

/* 1a. one hung read no longer leaves the app loading forever */
if (run1('hang')) {
  for (const t of ['conversation_members', 'plans', 'profiles']) {
    let hang = true;
    const hook = (url, m) => (hang && url.pathname === '/rest/v1/' + t && m === 'GET') ? new Promise(() => {}) : null;
    const { page, close } = await openApp({ hook, port: PB + 8801, wait: 3000 });
    /* 15 s a try; supabase-js retries a failed GET 3 times (1, 2, 4 s apart): a read that never answers gives up at ~67 s */
    for (let k = 0; k < 9; k++) await run(page, 10000);
    const s = await st(page);
    if (t === 'profiles') {
      ok(s.phase === 'profileerr' && /Can.t reach TermChamp/.test(s.txt), 'hang: a hung profile read times out to "Can\'t reach" (not a spinner forever)', s);
      hang = false; await page.evaluate(() => window.dispatchEvent(new Event('online'))); await run(page, 5000);
      await page.waitForFunction(() => TC.ready, null, { timeout: 5000 }).catch(() => {});
      ok((await st(page)).ready, 'hang: back online, the app loads by itself (no Try again tap)', await st(page));
    } else ok(s.ready && s.phase === 'ok', `hang: a hung ${t} read times out and the app is ready`, s);
    await close();
  }
}

/* 1b. one loader that throws doesn't block the rest */
if (run1('settled')) {
  const { page, close } = await openApp({ port: PB + 8802 });
  await page.waitForFunction(() => TC.ready);
  const r = await page.evaluate(async () => { window.loadPlans = () => Promise.reject(new Error('boom')); TC.ready = false; try { await TC.load(); } catch (e) { return 'rejected ' + e.message; } return TC.ready; });
  ok(r === true, 'settled: a loader that rejects still lets the load finish (TC.ready)', r);
  await close();
}

/* 1c. offline at launch (API down, script cached) recovers on 'online' and on foreground */
if (run1('recover')) {
  for (const how of ['online', 'visible']) {
    let down = true;
    const { page, close } = await openApp({ hook: () => down ? 'abort' : null, port: PB + 8803, wait: 3000 });
    await run(page, 20000); await page.waitForFunction(() => TC.phase !== 'boot', null, { timeout: 10000 }).catch(() => {});
    const s0 = await st(page);
    ok(!s0.ready && /Can.t reach TermChamp/.test(s0.txt), `recover/${how}: API down at launch shows "Can't reach"`, s0);
    down = false;
    if (how === 'online') await page.evaluate(() => window.dispatchEvent(new Event('online'))); else await vis(page, 'visible');
    await run(page, 5000); await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }).catch(() => {});
    ok((await st(page)).ready, `recover/${how}: the app loads by itself`, await st(page));
    await close();
  }
  /* the script itself failed (web, no cache): online reloads the page, which is what Try again did */
  let cdnOff = true;
  const pre = async ctx => { await ctx.route('**/supabase-js@2.112.4/**', r => cdnOff ? r.abort('internetdisconnected') : r.fallback()); };
  const { page, close } = await openApp({ hook: () => cdnOff ? 'abort' : null, pre, port: PB + 8804, wait: 3000 });
  ok((await st(page)).phase === 'offline', 'recover/script: script blocked → offline screen', await st(page));
  cdnOff = false;
  await Promise.all([page.waitForEvent('load', { timeout: 8000 }).catch(() => null), page.evaluate(() => window.dispatchEvent(new Event('online')))]);
  await page.waitForTimeout(500); await page.clock.runFor(5000).catch(() => {}); await page.waitForTimeout(500);
  ok(await page.evaluate(() => typeof TC !== 'undefined' && !!TC.ready).catch(() => false), 'recover/script: online reloads and the app loads', await st(page).catch(e => String(e)));
  await close();
}

/* 1d. tcFetch timeouts: REST 15 s, storage longer; a caller's signal still aborts */
if (run1('timeout')) {
  let release = null;
  const hook = url => (url.pathname.includes('/slow')) ? new Promise(res => { release = () => res({ status: 200, body: '{"ok":1}' }); }) : null;
  const { page, close } = await openApp({ hook, port: PB + 8805 });
  await page.waitForFunction(() => TC.ready);
  const B = 'https://rqkndeqbcahozidniesn.supabase.co';
  await page.evaluate(B => { window.__r = {}; tcFetch(B + '/rest/v1/slow').then(r => window.__r.rest = r.status, e => window.__r.rest = 'ERR ' + e.message); }, B);
  await run(page, 16000);
  const rest = await page.evaluate(() => window.__r.rest);
  ok(/^ERR .*failed to fetch/i.test(String(rest)), 'timeout: a REST request with no answer fails after ~15 s, worded as a network failure', rest);
  await page.evaluate(B => { tcFetch(B + '/storage/v1/object/avatars/slow.jpg', { method: 'POST', body: 'x' }).then(r => window.__r.st = r.status, e => window.__r.st = 'ERR ' + e.message); }, B);
  await run(page, 20000); release(); await page.waitForTimeout(400);
  ok((await page.evaluate(() => window.__r.st)) === 200, 'timeout: a storage upload is not cut off at 15 s', await page.evaluate(() => window.__r.st));
  await page.evaluate(B => { const c = new AbortController(); tcFetch(B + '/rest/v1/slow', { signal: c.signal }).then(r => window.__r.ab = r.status, e => window.__r.ab = 'ERR ' + e.name); setTimeout(() => c.abort(), 1000); }, B);
  await run(page, 1500);
  ok(/^ERR AbortError/.test(String(await page.evaluate(() => window.__r.ab))), 'timeout: the caller\'s own signal still aborts', await page.evaluate(() => window.__r.ab));
  await close();
}

/* 2. expired sign-in (401 PGRST301) is refreshed once and the request retried */
if (run1('jwt')) {
  let expired = true, tokCalls = 0;
  const hook = (url, m) => {
    if (url.pathname.startsWith('/auth/v1/token')) { tokCalls++; expired = false; return null; }
    if (expired && url.pathname.startsWith('/rest/')) return { status: 401, body: JSON.stringify({ code: 'PGRST301', message: 'JWT expired', details: null, hint: null }) };
    return null;
  };
  const { page, close, log } = await openApp({ hook, port: PB + 8806, wait: 3000 });
  await run(page, 3000);
  const s = await st(page);
  ok(s.ready && s.phase === 'ok', 'jwt: an expired token at launch is refreshed and the app loads', s);
  ok(tokCalls === 1, 'jwt: one refresh for the whole wave of 401s', tokCalls);
  /* mid-session: a send */
  await run(page, 15000); expired = true; tokCalls = 0;   /* past the 10 s in which a fresh token is reused */
  if (s.ready) await page.evaluate(() => { A.tab('friends'); A.openChat(TC.threads[0].id); }); await page.waitForTimeout(600);
  if (s.ready) { await page.fill('#chatin', 'after expiry'); await page.press('#chatin', 'Enter'); await run(page, 2000); }
  ok(log.writes.some(w => w.table === 'messages' && JSON.stringify(w.body).includes('after expiry')) && tokCalls === 1, 'jwt: a message sent with an expired token goes through after one refresh', [tokCalls, log.writes.filter(w => w.table === 'messages').length]);
  await close();
  /* refresh refused (refresh token revoked) → sign-in */
  const hook2 = (url) => {
    if (url.pathname.startsWith('/auth/v1/token')) { tokCalls++; return { status: 400, body: JSON.stringify({ code: 'refresh_token_not_found', error_code: 'refresh_token_not_found', msg: 'Invalid Refresh Token: Refresh Token Not Found' }) }; }
    if (url.pathname.startsWith('/rest/')) return { status: 401, body: JSON.stringify({ code: 'PGRST301', message: 'JWT expired', details: null, hint: null }) };
    return null;
  };
  tokCalls = 0;
  /* the harness puts the session back on every page load; keep a removal the app made, as a real phone would */
  const keepRemoval = () => { const K = 'sb-rqkndeqbcahozidniesn-auth-token';
    if (sessionStorage.getItem('t-gone')) localStorage.removeItem(K);
    const rm = Storage.prototype.removeItem; Storage.prototype.removeItem = function (k) { if (k === K) sessionStorage.setItem('t-gone', '1'); return rm.call(this, k); }; };
  const b = await openApp({ hook: hook2, init: keepRemoval, port: PB + 8807, wait: 3000 });
  await run(b.page, 5000); await b.page.waitForTimeout(500);
  const s2 = await st(b.page).catch(e => ({ e: String(e) }));
  ok(s2.phase === 'signin', 'jwt: a refresh the server refuses shows sign-in', s2);
  ok(tokCalls >= 1 && tokCalls <= 3, 'jwt: no refresh loop', tokCalls);
  await b.close();
}

/* 3. a plan edit made offline is kept, not overwritten, and saved once back online */
if (run1('plan')) {
  let mode = 'ok', planWrites = 0;
  const hook = (url, m) => {
    if (url.pathname === '/rest/v1/plans' && m !== 'GET') planWrites++;
    if (mode === 'abort') return 'abort';
    if (mode === 'nowrite' && url.pathname === '/rest/v1/plans' && m !== 'GET') return { status: 500, body: '{"message":"x"}' };
    return null;
  };
  const { page, close, tables } = await openApp({ hook, port: PB + 8808 });
  await page.waitForFunction(() => TC.ready);
  mode = 'abort';
  await page.evaluate(() => TC.setPlan('B', TC.plans.B.concat(['70104']))); await run(page, 1500);
  const dirty = await page.evaluate(() => localStorage.getItem('tc_plan_dirty'));
  ok(!!dirty && dirty.includes('70104'), 'plan: an unsaved edit is kept on the phone', dirty);
  /* back to the front with the plans write still failing: the next load must not overwrite the edit */
  mode = 'nowrite'; await page.evaluate(() => { TC.loadedAt = 0; }); await vis(page, 'visible'); await run(page, 4000);
  ok((await page.evaluate(() => TC.plans.B)).includes('70104'), 'plan: a refresh does not overwrite the unsaved edit', await page.evaluate(() => TC.plans.B));
  /* a cold start while still unsaved: the edit survives a reload */
  await page.reload({ waitUntil: 'domcontentloaded' }); await run(page, 3000); await page.waitForFunction(() => TC.ready);
  ok((await page.evaluate(() => TC.plans.B)).includes('70104'), 'plan: the unsaved edit survives a restart', await page.evaluate(() => TC.plans.B));
  mode = 'ok'; await page.evaluate(() => window.dispatchEvent(new Event('online'))); await run(page, 3000);
  const srv = (tables.plans.find(p => p.user_id === ME && p.slot === 'B') || {}).sections;
  ok(JSON.stringify(srv || '').includes('70104'), 'plan: back online, the edit is saved', srv);
  ok(!(await page.evaluate(() => localStorage.getItem('tc_plan_dirty'))), 'plan: saved → no longer marked unsaved', await page.evaluate(() => localStorage.getItem('tc_plan_dirty')));
  await page.evaluate(() => { TC.loadedAt = 0; }); await vis(page, 'visible'); await run(page, 3000);
  ok((await page.evaluate(() => TC.plans.B)).includes('70104'), 'plan: and the next refresh shows it', await page.evaluate(() => TC.plans.B));
  await close();
}

/* 4. foreground: one push registration per resume; seats not re-downloaded within 10 minutes */
if (run1('resume')) {
  const NATIVE = () => {
    const L = {}; window.__push = { reg: 0 };
    window.Capacitor = { isNativePlatform: () => true, Plugins: { PushNotifications: {
      addListener: (ev, fn) => { (L[ev] = L[ev] || []).push(fn); return Promise.resolve({ remove() {} }); },
      checkPermissions: () => Promise.resolve({ receive: 'granted' }), requestPermissions: () => Promise.resolve({ receive: 'granted' }),
      register: () => { window.__push.reg++; setTimeout(() => (L.registration || []).forEach(f => f({ value: 'tok-abc' })), 5); return Promise.resolve(); } } } };
  };
  const { page, close, log } = await openApp({ init: NATIVE, port: PB + 8809 });
  await page.waitForFunction(() => TC.ready); await run(page, 1000);
  const regs = () => log.rpcs.filter(x => x.fn === 'register_push_token').length;
  const seats = a => log.all.slice(a).filter(x => x.u.includes('course_seats') && !x.u.includes('class_nbr=in')).length;
  const plans = a => log.all.slice(a).filter(x => x.u.startsWith('/rest/v1/plans')).length;
  ok(regs() === 1, 'resume: one token save at launch', regs());
  /* away 3 minutes */
  await vis(page, 'hidden'); await run(page, 180000); let a = log.all.length, r0 = regs();
  await vis(page, 'visible'); await run(page, 3000);
  ok(regs() - r0 === 1, 'resume: one token save per resume (was two)', regs() - r0);
  ok(seats(a) === 0, 'resume: seats fetched <10 min ago are not downloaded again', seats(a));
  ok(plans(a) > 0, 'resume: plans/messages/friends still refresh', plans(a));
  /* away 11 minutes */
  await vis(page, 'hidden'); await run(page, 660000); a = log.all.length; r0 = regs();
  await vis(page, 'visible'); await run(page, 3000);
  ok(seats(a) > 0, 'resume: after 10 minutes the seats are refreshed', seats(a));
  ok(regs() - r0 === 1, 'resume: still one token save', regs() - r0);
  await close();
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
