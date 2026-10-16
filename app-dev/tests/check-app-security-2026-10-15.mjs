/* check-app-security — the PHONE app (app/index.html) against the five security fixes of app-dev/patches/security-app-2026-10-15.py.
   1. pdf.js getDocument() is called with isEvalSupported:false (and the pdf.js <script> still carries its integrity hash).
   2. An invite link (?add=<uuid>) is a question: no friend_requests write until Add is tapped; an incoming request is accepted
      by that same tap, never automatically; Not now clears; closing any other way keeps it (14 days); the name is the profile's.
   3. Sign-out / account delete on a shared browser removes every tc- / tc_ / professify / termchamp key, keeps the theme and the
      public caches, and still does so when the server cannot be reached.
   4. safeImg() only lets our own avatars bucket (or a raster data:image) through; a tracking host is never requested.
   5. #access_token=...&refresh_token=... in the URL does NOT sign anyone in; the real sign-ins (code, password) still do, and the
      dormant Google redirect is PKCE.
   Run: APP_DIR=<repo root> node check-app-security-2026-10-15.mjs [--only pdf|invite|wipe|avatar|auth] [--quiet]   (APP_PORT to move off 8190) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const want = n => !ONLY || ONLY === n;
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); } };
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const SUG = FX.SUGGESTED, STR = FX.STRANGER, ME = FX.ME, AVQ = FX.FRIENDS[0];
const NOW = new Date('2026-09-29T10:30:00-07:00').getTime();
const inviter = name => Object.assign({}, FX.RPC, { get_inviter: name ? [{ display_name: name }] : [] });
const frWrites = log => log.writes.filter(w => w.table === 'friend_requests');
const sheetText = page => page.evaluate(() => { const s = document.querySelector('#sheet .sbody'); return s ? s.innerText : null; });
const inviteOpen = page => page.evaluate(() => !!(UI.sheet && UI.sheet.type === 'inviteAsk' && document.querySelector('#sheet [data-a="inviteAdd"]')));
const pend = page => page.evaluate(() => localStorage.getItem('tc_pending_add'));
const clk = async (page, sel) => { try { await page.locator(sel).first().click({ timeout: 2500 }); return true; } catch (e) { ok(false, 'could not press ' + sel); return false; } };
const app = (o = {}) => openApp(Object.assign({ path: '/app/' }, o));

/* ------------------------------------------------------------------ 1. pdf.js */
if (want('pdf')) {
  const { page, close } = await app({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => window.TCPL && TCPL.pdfBase, null, { timeout: 8000 });   // the planner module carries TCPL.pdfBase / fileBytes
  const r = await page.evaluate(async () => {
    const lib = await loadPdfJs();                                    // the real script, through its integrity check
    const tag = document.querySelector('script[src*="pdfjs-dist"]');
    const real = window.pdfjsLib; let seen = null;
    window.pdfjsLib = { GlobalWorkerOptions: real.GlobalWorkerOptions, getDocument(o) { seen = o; return real.getDocument(o); } };
    try { await Promise.race([readDpr(new File([new Uint8Array([37, 80, 68, 70])], 'x.pdf')), new Promise(r => setTimeout(r, 3000))]); } catch (e) {}
    return { loaded: !!(lib && real.getDocument), tag: tag && { i: tag.integrity, c: tag.crossOrigin }, seen: seen && { eval: seen.isEvalSupported, data: !!seen.data, off: seen.isOffscreenCanvasSupported } };
  });
  ok(r.loaded && r.tag && /^sha384-/.test(r.tag.i) && r.tag.c === 'anonymous', 'pdf.js loads through its integrity hash (script tag has integrity + crossorigin)', r);
  ok(r.seen && r.seen.eval === false && r.seen.data, 'getDocument() is called with isEvalSupported:false (and the data)', r.seen);
  ok(r.seen && r.seen.off === false, 'getDocument() keeps isOffscreenCanvasSupported:false', r.seen);
  await close();
}

/* ------------------------------------------------------------------ 2. the invite is a question */
if (want('invite')) {
  /* signed in, an invite link: asked, not sent; Add writes exactly one request */
  {
    const { page, close, log } = await app({ path: '/app/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 1500);
    const t = await sheetText(page);
    ok(frWrites(log).length === 0, 'signed in, ?add=: nothing is written to friend_requests on load', frWrites(log));
    ok(t && /Add Pat Suggestia\?/.test(t) && /\bAdd\b/.test(t) && /Not now/.test(t) && await inviteOpen(page), 'the sheet asks “Add Pat Suggestia?” with Add and Not now', t);
    ok(log.rpcs.some(r => r.fn === 'get_inviter' && r.body && r.body.ref === SUG.id), 'the name is read with get_inviter');
    ok(await pend(page) !== null && !/add=/.test(page.url()), 'the invite is kept while the question is up, and the id is off the address bar', { p: await pend(page), url: page.url() });
    await clk(page, '#sheet [data-a="inviteAdd"]'); await tick(page, 1200);
    const w = frWrites(log);
    ok(w.length === 1 && w[0].m === 'POST' && w[0].body.to_user === SUG.id && w[0].body.from_user === ME.id && w[0].body.status === 'pending', 'Add writes exactly one pending request, from me to them', w);
    ok(await pend(page) === null && !(await inviteOpen(page)), 'answered: the sheet closes and the invite is cleared', await pend(page));
    ok(/Friend request sent to Pat/.test(await page.locator('#toast').innerText()), 'and says so');
    ok(log.errors.length === 0, 'no page errors (Add)', log.errors);
    await close();
  }
  /* Not now: nothing written, cleared, does not come back */
  {
    const { page, close, log } = await app({ path: '/app/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 1500);
    ok(await inviteOpen(page), 'set-up: the question is up');
    await clk(page, '#sheet [data-a="inviteNo"]'); await tick(page, 600);
    ok(frWrites(log).length === 0 && !(await inviteOpen(page)) && await pend(page) === null, 'Not now writes nothing, closes the sheet and clears the invite', { w: frWrites(log), p: await pend(page) });
    await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 3000);
    ok(frWrites(log).length === 0 && !(await inviteOpen(page)), 'after Not now, a reload asks nothing and writes nothing');
    await close();
  }
  /* closing it any other way is not an answer: kept, asked again next load, still nothing written */
  {
    const { page, close, log } = await app({ path: '/app/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 1500);
    await page.evaluate(() => A.closeSheet()); await tick(page, 400);     // what the scrim and the X do
    ok(!(await inviteOpen(page)) && await pend(page) !== null && frWrites(log).length === 0, 'closing the sheet (scrim / X) keeps the invite and writes nothing', { p: await pend(page), w: frWrites(log) });
    const ld = await page.evaluate(() => TC.loadDone);
    await page.evaluate(() => TC.refresh());
    for (let i = 0; i < 20 && (await page.evaluate(() => TC.loadDone)) === ld; i++) await tick(page, 500);
    await tick(page, 3500); await page.waitForTimeout(500); await tick(page, 500);
    ok((await page.evaluate(() => TC.loadDone)) !== ld && !(await inviteOpen(page)), 'a refresh in the same visit (a completed reload of the data) does not nag', { loaded: (await page.evaluate(() => TC.loadDone)) !== ld });
    await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 3000);
    ok(await inviteOpen(page) && frWrites(log).length === 0, 'the next load asks again (still nothing written)');
    await close();
  }
  /* they ALREADY asked me: no auto-accept; the question's Add accepts (same tap), one PATCH, no POST */
  {
    const { page, close, log } = await app({ path: '/app/?add=' + STR.id, rpc: inviter(STR.display_name) });
    await tick(page, 1500);
    const t = await sheetText(page);
    ok(frWrites(log).length === 0 && await inviteOpen(page), 'an incoming request is NOT accepted by the link: the question comes first, nothing written', { w: frWrites(log), t });
    ok(/Add Morgan Nobody\?/.test(t || '') && /already asked/.test(t || ''), 'it says they already asked', t);
    await clk(page, '#sheet [data-a="inviteAdd"]'); await tick(page, 1200);
    const w = frWrites(log);
    ok(w.length === 1 && w[0].m === 'PATCH' && w[0].body.status === 'accepted' && !w.some(x => x.m === 'POST'), 'Add accepts it: exactly one PATCH to accepted, no second request', w);
    ok(await pend(page) === null && !(await inviteOpen(page)), 'answered and cleared');
    await close();
  }
  /* ... and Not now on an incoming request accepts nothing */
  {
    const { page, close, log } = await app({ path: '/app/?add=' + STR.id, rpc: inviter(STR.display_name) });
    await tick(page, 1500); await clk(page, '#sheet [data-a="inviteNo"]'); await tick(page, 600);
    ok(frWrites(log).length === 0, 'Not now on an incoming request writes nothing (it stays in Friends)', frWrites(log));
    await close();
  }
  /* a failed send keeps the question and the invite */
  {
    const hook = (url, m) => (m === 'POST' && url.pathname === '/rest/v1/friend_requests') ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : null;
    const { page, close, log } = await app({ path: '/app/?add=' + SUG.id, rpc: inviter(SUG.display_name), hook });
    await tick(page, 1500); await clk(page, '#sheet [data-a="inviteAdd"]'); await tick(page, 1200);
    ok(await inviteOpen(page) && await pend(page) !== null && /Couldn’t add them/.test(await sheetText(page) || ''), 'a failed send keeps the question open (with a message) and the invite', { open: await inviteOpen(page), p: await pend(page) });
    await close();
  }
  /* two quick taps on Add are one request */
  {
    const hook = (url, m) => (m === 'POST' && url.pathname === '/rest/v1/friend_requests') ? new Promise(res => setTimeout(() => res(null), 600)) : null;
    const { page, close, log } = await app({ path: '/app/?add=' + SUG.id, rpc: inviter(SUG.display_name), hook });
    await tick(page, 1500);
    await page.evaluate(() => { A.inviteAdd(); A.inviteAdd(); });
    await tick(page, 2500); await page.waitForTimeout(1500); await tick(page, 500);   // the stand-in answers the POST 600ms (real time) late
    ok(frWrites(log).filter(w => w.m === 'POST').length === 1, 'two quick taps on Add send one request', frWrites(log));
    await close();
  }
  /* no name to be had: "this person" */
  {
    const { page, close } = await app({ path: '/app/?add=' + SUG.id, rpc: Object.assign({}, FX.RPC, { get_inviter: { __error: { code: '42883', message: 'function get_inviter does not exist', details: null, hint: null } } }) });
    await tick(page, 1500);
    ok(/Add this person\?/.test(await sheetText(page) || ''), 'no name: “Add this person?”', await sheetText(page));
    await close();
  }
  /* a name with markup stays text */
  {
    const evil = '<img src=x onerror=window.__pwn=1>Mallory';
    const { page, close } = await app({ path: '/app/?add=' + SUG.id, rpc: inviter(evil) });
    await tick(page, 1500);
    const r = await page.evaluate(() => ({ imgs: document.querySelectorAll('#sheet .sbody img').length, pwn: window.__pwn || 0, h: (document.querySelector('#sheet .sbody h3') || {}).textContent || '' }));
    ok(r.imgs === 0 && !r.pwn && r.h.indexOf('<img') >= 0, 'the inviter’s name is escaped: markup is shown as text, never run', r);
    await close();
  }
  /* friend / your own link / a request already sent: nothing is asked */
  for (const [label, id] of [['a friend’s link', AVQ.id], ['your own link', ME.id]]) {
    const { page, close, log } = await app({ path: '/app/?add=' + id });
    await tick(page, 1500);
    ok(!(await inviteOpen(page)) && !frWrites(log).length && await pend(page) === null, label + ': nothing is asked, nothing is sent, the stash is dropped', { open: await inviteOpen(page), p: await pend(page) });
    await close();
  }
  /* 14 days: 13 days old is still asked, 15 days old is gone */
  for (const [days, expect] of [[13, true], [15, false]]) {
    const init = `try{localStorage.setItem('tc_pending_add', JSON.stringify({id:'${SUG.id}',at:${NOW - days * 864e5}}));}catch(e){}`;
    const { page, close, log } = await app({ path: '/app/', rpc: inviter(SUG.display_name), init });
    await tick(page, 1500);
    ok(await inviteOpen(page) === expect && !frWrites(log).length, `an invite ${days} days old is ${expect ? 'still asked about' : 'forgotten'}, and nothing is written`, { open: await inviteOpen(page) });
    await close();
  }
  /* signed out first, then signed in: kept through sign-in, then asked (not sent) */
  {
    const { page, close, log } = await app({ signedIn: false, path: '/app/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 800);
    ok(await pend(page) !== null && !frWrites(log).length, 'signed out, ?add=: the invite is kept and nothing is written');
    await page.evaluate(() => TC.client().auth.verifyOtp({ email: 'fixture@calpoly.edu', token: '123456', type: 'email' }));
    await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(page, 1500);
    ok(await inviteOpen(page) && !frWrites(log).length, 'after signing in it is a question, still nothing written', { open: await inviteOpen(page), w: frWrites(log) });
    await close();
  }
}

/* ------------------------------------------------------------------ 3. sign-out / delete wipe */
const SEED = [
  ['tc-audit:' + ME.id, '{"x":1}'], ['tc-commits:' + ME.id, '[]'], ['tc-commits-asked:' + ME.id, '1'], ['tc-marks:' + ME.id, '{}'], ['tc-regday:' + ME.id + ':2268', '{}'],
  ['tc-drafted:' + ME.id + ':2268', '{}'], ['tc-pl-nodpr:' + ME.id, '1'], ['tc-prefs:' + ME.id, '{}'], ['tc-chat-pins-' + ME.id, '[]'], ['tc-story-pins:' + ME.id, '[]'],
  ['tc-feed-seen:' + ME.id, '{}'], ['tc_champ_ai:' + ME.id, '1'], ['tc_pending_add', '{"id":"x","at":1}'], ['tc_push_token', 'tok'], ['tc_push_snooze', '1'],
  ['termchamp-app-v1', '{"saved":[]}'], ['termchamp_app_conc', '{}'], ['termchamp_app_plans_v1', '{}'], ['termchamp_app_recent', '{}'], ['termchamp_app_rate_drafts', '{}'], ['termchamp_app_onb', '{}'],
  ['professify-profile', '{"major":"x"}'], ['professify_rev_times', '[]'], ['professify_ev_salt', 'abc'], ['professify_pending_add', 'x'], ['professify_avatar_' + ME.id, 'data:x'],
];
const KEEP = [['tc-theme', 'dark'], ['termchamp_app_seats_v1', '{"rows":[]}'], ['professify_prof_cache', '{"list":[]}'], ['unrelated-site-key', 'stay']];
const PREFIX = /^(tc-|tc_|professify|termchamp)/;
async function seed(page) {
  await page.evaluate(([seed, keep]) => {
    seed.concat(keep).forEach(([k, v]) => localStorage.setItem(k, v));
    ['tc-dl', 'tc_champ_x', 'professify_pending_add'].forEach(k => sessionStorage.setItem(k, 'v'));
    sessionStorage.setItem('unrelated-session-key', 'stay');
  }, [SEED, KEEP]);
}
const keysOf = page => page.evaluate(() => ({ l: Object.keys(localStorage), s: Object.keys(sessionStorage) }));
if (want('wipe')) {
  for (const mode of ['signOut', 'signOut-fails', 'afterDelete', 'afterDelete-fails']) {
    const { page, close, log } = await app({ champ: false, cmAsked: false });
    await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(page, 600);
    await seed(page);
    const before = await keysOf(page);
    ok(SEED.every(([k]) => before.l.includes(k)) && before.l.some(k => /^sb-/.test(k)), mode + ': set-up — personal keys and the session are in storage', before.l.length);
    /* read straight after the call returns: the page reloads after it (and the harness would re-seed the session on that reload) */
    const after = await page.evaluate(async m => {
      /* '-fails': the server cannot be reached, so supabase-js returns an error and (unlike a clean sign-out) leaves its own session keys in storage */
      if (/fails/.test(m)) TC.client().auth.signOut = async () => ({ error: { message: 'failed to fetch' } });
      if (/^afterDelete/.test(m)) await TC.afterDelete(); else await TC.signOut();
      return { l: Object.keys(localStorage), s: Object.keys(sessionStorage), tcd: sessionStorage.getItem('tc_deleted') };
    }, mode);
    const left = after.l.concat(after.s).filter(k => PREFIX.test(k) && !['tc-theme', 'termchamp_app_seats_v1', 'professify_prof_cache', 'tc_deleted'].includes(k));
    ok(left.length === 0, mode + ': no tc- / tc_ / professify / termchamp key is left behind (other than the kept ones)', left);
    ok(KEEP.every(([k]) => after.l.includes(k)) && after.s.includes('unrelated-session-key'), mode + ': the theme, the two public caches and other sites’ keys stay', after);
    ok(!after.l.some(k => /^sb-/.test(k)), mode + ': the auth session keys are gone from storage', after.l.filter(k => /^sb-/.test(k)));
    if (/^afterDelete/.test(mode)) ok(after.tcd && after.tcd !== 'null', 'afterDelete: the one-shot “scheduled for deletion” note survives the wipe', after.tcd);
    else ok(after.tcd === null, mode + ': no deletion note', after.tcd);
    await close();
  }
}

/* ------------------------------------------------------------------ 4. avatars */
if (want('avatar')) {
  const BASE = 'https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/';
  const { page, close } = await app({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await tick(page, 400);
  const cases = [
    [BASE + ME.id + '/avatar.jpg?v=1700000000000', true, 'our bucket'],
    [BASE + 'x.png', true, 'our bucket (plain)'],
    ['https://tracker.example.invalid/pixel.png', false, 'another https host'],
    ['https://rqkndeqbcahozidniesn.supabase.co.evil.example/storage/v1/object/public/avatars/x.png', false, 'look-alike host'],
    ['https://rqkndeqbcahozidniesn.supabase.co@evil.example/storage/v1/object/public/avatars/x.png', false, 'userinfo trick'],
    ['https://evil.example/https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/x.png', false, 'prefix in the path'],
    ['https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/other-bucket/x.png', false, 'another bucket'],
    ['https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/../../../../auth/v1/x', false, 'dot-dot out of the folder'],
    ['https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/..%2f..%2fx', true, 'encoded dots stay inside (the server, not the browser, reads them)'],
    ['https://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars\\..\\..\\x', false, 'backslash path'],
    ['http://rqkndeqbcahozidniesn.supabase.co/storage/v1/object/public/avatars/x.png', false, 'plain http'],
    ['javascript:alert(1)', false, 'javascript:'],
    ['data:image/svg+xml;base64,PHN2Zy8+', false, 'svg data URL'],
    ['data:text/html;base64,PGI+', false, 'html data URL'],
    ['data:image/png;base64,iVBORw0KGgo=', true, 'raster data URL (local preview)'],
    ['', false, 'empty'], [null, false, 'null'],
  ];
  const got = await page.evaluate(cs => cs.map(([u]) => safeImg(u)), cases);
  cases.forEach(([u, allowed, why], i) => ok(allowed ? got[i] === u : got[i] === '', 'safeImg: ' + why + (allowed ? ' → kept' : ' → refused'), { u, got: got[i] }));
  const html = await page.evaluate(([bad, good, ids]) => {
    PEOPLE[ids[0]].avatar = bad; PEOPLE[ids[1]].avatar = good;
    return { bad: pav(ids[0], 40), good: pav(ids[1], 40) };
  }, ['https://tracker.example.invalid/pixel.png', BASE + 'a/avatar.jpg', [AVQ.id, FX.FRIENDS[1].id]]);
  ok(!/<img/.test(html.bad) && !/tracker/.test(html.bad), 'pav(): a foreign avatar renders the silhouette, no <img>', html.bad);
  ok(/<img[^>]*src="https:\/\/rqkndeqbcahozidniesn\.supabase\.co\/storage\/v1\/object\/public\/avatars\/a\/avatar\.jpg"[^>]*referrerpolicy="no-referrer"/.test(html.good), 'pav(): our own avatar still renders, with referrerpolicy="no-referrer"', html.good);
  await close();
  /* end to end: a friend whose profile row points at a tracking host is never fetched */
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  T.profiles = T.profiles.map(p => p.id === AVQ.id ? Object.assign({}, p, { avatar_url: 'https://tracker.example.invalid/pixel.png' }) : p);
  const o = await app({ tables: T });
  const seen = []; o.page.on('request', r => { if (/tracker\.example\.invalid/.test(r.url())) seen.push(r.url()); });
  await o.page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await o.page.evaluate(() => render(true));
  await tick(o.page, 1500);
  const imgs = await o.page.evaluate(() => [...document.querySelectorAll('img')].map(i => i.getAttribute('src') || '').filter(s => /tracker/.test(s)));
  const raw = await o.page.evaluate(id => PEOPLE[id] && PEOPLE[id].avatar, AVQ.id);
  ok(/tracker\.example\.invalid/.test(raw || ''), 'set-up: the friend’s profile row really carries the foreign avatar_url', raw);
  ok(seen.length === 0 && imgs.length === 0, 'end to end: a friend’s avatar_url on a foreign host is never put in the page or requested', { seen, imgs });
  await o.close();
}

/* ------------------------------------------------------------------ 5. auth flow */
if (want('auth')) {
  const atk = { id: '99999999-9999-4999-8999-999999999999', aud: 'authenticated', role: 'authenticated', email: 'attacker@calpoly.edu', email_confirmed_at: '2026-09-01T00:00:00Z', app_metadata: { provider: 'email' }, user_metadata: {} };
  const b64 = o => Buffer.from(JSON.stringify(o)).toString('base64url');
  const exp = Math.floor(NOW / 1000) + 3600;
  const jwt = `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64({ sub: atk.id, email: atk.email, role: 'authenticated', exp })}.sig`;
  /* the attacker's server answers "valid" for their token, as a real project would */
  const mk = () => { const calls = { user: 0, token: 0 }; return { calls, hook: (url, m) => { if (url.pathname === '/auth/v1/user' && m === 'GET') { calls.user++; return { status: 200, body: JSON.stringify(atk) }; } if (url.pathname === '/auth/v1/token') calls.token++; return null; } }; };
  const frag = `#access_token=${jwt}&refresh_token=attacker-refresh&token_type=bearer&expires_in=3600&expires_at=${exp}&type=magiclink`;
  {
    const c = mk();
    const { page, close, log } = await app({ signedIn: false, path: '/app/', search: frag, hook: c.hook });
    await tick(page, 1500);
    const r = await page.evaluate(() => ({ user: TC.user && TC.user.email, phase: TC.phase, keys: Object.keys(localStorage).filter(k => /^sb-/.test(k)), flow: TC.client().auth.flowType, text: document.body.innerText.slice(0, 200) }));
    ok(!r.user && r.keys.length === 0, 'a URL with #access_token=…&refresh_token=… does NOT create a session (nothing stored, nobody signed in)', r);
    ok(r.phase === 'signin' && /Get started/.test(r.text), 'the visitor still sees the sign-in screen', r);
    ok(c.calls.user === 0, 'the fragment’s token is never even sent to the server to be validated', c.calls);
    ok(r.flow === 'pkce', 'the client uses the PKCE flow', r.flow);
    await close();
  }
  {
    const c = mk();
    const { page, close } = await app({ signedIn: false, path: '/app/?code=attacker-minted-code', hook: c.hook });
    await tick(page, 1500);
    const r = await page.evaluate(() => ({ user: TC.user && TC.user.email, keys: Object.keys(localStorage).filter(k => /^sb-/.test(k)) }));
    ok(!r.user && r.keys.length === 0 && c.calls.token === 0, 'a URL with ?code=… that this browser never asked for does NOT create a session', { r, c: c.calls });
    await close();
  }
  /* the real sign-ins still work */
  {
    const { page, close, log } = await app({ signedIn: false, path: '/app/' });
    await tick(page, 600);
    const err = await page.evaluate(() => TC.verifyCode('fixture@calpoly.edu', '123456'));
    await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
    ok(err === null && await page.evaluate(() => !!TC.user), 'email code sign-in (verifyOtp) still signs in', err);
    await close();
  }
  {
    const { page, close } = await app({ signedIn: false, path: '/app/' });
    await tick(page, 600);
    const err = await page.evaluate(() => TC.signInPassword('fixture@calpoly.edu', 'a-long-password'));
    await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
    ok(err === null && await page.evaluate(() => !!TC.user), 'email + password sign-in still signs in', err);
    await close();
  }
  {
    const { page, close } = await app({ signedIn: false, path: '/app/' });
    await tick(page, 600);
    const u = await page.evaluate(async () => { const r = await TC.client().auth.signInWithOAuth({ provider: 'google', options: { redirectTo: location.origin + '/app/', skipBrowserRedirect: true } }); return r && r.data && r.data.url; });
    ok(u && /code_challenge=/.test(u) && /code_challenge_method=s256/i.test(u), 'the (switched-off) Google redirect would be PKCE: it carries a code_challenge', u);
    await close();
  }
}

console.log(`\ncheck-app-security-2026-10-15: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
