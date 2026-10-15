/* check-desktop-invite-confirm — security-client-hardening (2026-10-14), run on the REAL index.html and sw.js.
   1. An invite link is a question, not a write: no friend_requests write on load, signed in or signed out then in;
      the card says "Add <name>?" (name from get_inviter, "this person" when there is none); Add writes exactly one
      request; Not now writes none and clears; closing the sheet any other way keeps the invite; 14 days.
   2. pdf.js getDocument() is called with isEvalSupported:false.
   3. The three lazily loaded scripts carry integrity + crossorigin, are pinned, and the browser really accepts the
      bytes (SRI_DIR holds the npm tarballs' files) and really refuses changed ones.
   4. sw.js: a push url that is not ours opens "/".
   Run: APP_DIR=<repo> node check-desktop-invite-confirm.mjs [--only card|signedout|expiry|landing|pdf|sri|sw] [--quiet]
   (APP_PORT to move off 8190; SRI_DIR defaults to /tmp/claude-0/sri — see the layout in sriFiles below) */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const want = n => !ONLY || ONLY === n;
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 400) : ''); } };
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const DIR = process.env.APP_DIR || path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'out');
const SUG = FX.SUGGESTED, ME = FX.ME;
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const inviter = name => Object.assign({}, FX.RPC, { get_inviter: name ? [{ display_name: name }] : [] });
const frWrites = log => log.writes.filter(w => w.table === 'friend_requests');
const store = page => page.evaluate(() => ({ s: sessionStorage.getItem('professify_pending_add'), l: localStorage.getItem('professify_pending_add'), sat: sessionStorage.getItem('professify_pending_add_at'), lat: localStorage.getItem('professify_pending_add_at') }));
const cardText = async page => (await page.locator('#modal [data-pendadd]').count()) ? await page.locator('#modal [data-pendadd]').innerText() : null;
/* a click that cannot find its button is a failed check, not a crashed run */
const clk = async (page, sel) => { try { await page.locator(sel).click({ timeout: 2500 }); return true; } catch (e) { ok(false, 'could not press ' + sel); return false; } };
const cardOpen = page => page.evaluate(() => !!(document.querySelector('#mback.open #modal [data-pendadd]')));

/* ------------------------------------------------------------------ 1. the card */
if (want('card')) {
  /* signed in, an invite link: asked, not sent */
  {
    const { page, close, log } = await desk({ path: '/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 1500);
    const t = await cardText(page);
    ok(frWrites(log).length === 0, 'signed in, ?add=: nothing is written to friend_requests on load', frWrites(log));
    ok(t && /Add Pat Suggestia\?/.test(t) && /\bAdd\b/.test(t) && /Not now/.test(t) && await cardOpen(page), 'signed in, ?add=: the card asks “Add Pat Suggestia?” with Add and Not now', t);
    ok(log.rpcs.some(r => r.fn === 'get_inviter' && r.body && r.body.ref === SUG.id), 'the name is read with get_inviter');
    const st = await store(page);
    ok(st.s === SUG.id && st.l === SUG.id && +st.sat > 0 && +st.lat > 0 && !/add=/.test(page.url()), 'the invite is kept (with its date) while the card is up, and the id is off the address bar', { st, url: page.url() });
    await clk(page, '#pendAddYes'); await tick(page, 1200);
    const w = frWrites(log);
    ok(w.length === 1 && w[0].m === 'POST' && w[0].body.to_user === SUG.id && w[0].body.from_user === ME.id && w[0].body.status === 'pending', 'Add writes exactly one pending request, from me to them', w);
    const st2 = await store(page);
    ok(!st2.s && !st2.l && !st2.sat && !st2.lat && !(await cardOpen(page)), 'answered: the card closes and the invite is cleared', st2);
    ok(log.errors.length === 0, 'no page errors (Add)', log.errors);
    await close();
  }
  /* Not now: nothing written, cleared, and it does not come back */
  {
    const { page, close, log } = await desk({ path: '/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 1500);
    ok(await cardOpen(page), 'set-up: the card is up');
    await clk(page, '#pendAddNo'); await tick(page, 600);
    const st = await store(page);
    ok(frWrites(log).length === 0 && !(await cardOpen(page)) && !st.s && !st.l && !st.sat && !st.lat, 'Not now writes nothing, closes the card and clears the invite', { w: frWrites(log), st });
    await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 4000);
    ok(frWrites(log).length === 0 && !(await cardOpen(page)), 'after Not now, a reload asks nothing and writes nothing');
    await close();
  }
  /* closing the sheet any other way is not an answer: kept, asked again next load, still nothing written */
  {
    const { page, close, log } = await desk({ path: '/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
    await tick(page, 1500);
    await page.mouse.click(8, 8); await tick(page, 500);     // the backdrop
    const st = await store(page);
    ok(!(await cardOpen(page)) && st.s === SUG.id && st.l === SUG.id && frWrites(log).length === 0, 'closing the sheet by its backdrop keeps the invite and writes nothing', { st, w: frWrites(log) });
    await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 4000);
    ok(await cardOpen(page) && frWrites(log).length === 0, 'the next load asks again (still nothing written)');
    await close();
  }
  /* no name to be had: "this person" */
  {
    const { page, close, log } = await desk({ path: '/?add=' + SUG.id, rpc: Object.assign({}, FX.RPC, { get_inviter: { __error: { code: '42883', message: 'function get_inviter does not exist', details: null, hint: null } } }) });
    await tick(page, 1500);
    const t = await cardText(page);
    ok(t && /Add this person\?/.test(t) && frWrites(log).length === 0, 'when get_inviter fails the card says “Add this person?” and still writes nothing', t);
    await close();
  }
  /* a name that is markup is text */
  {
    const { page, close } = await desk({ path: '/?add=' + SUG.id, rpc: inviter('<img src=x onerror="window.__pwn=1">Eve') });
    await tick(page, 1500);
    ok(await page.evaluate(() => !window.__pwn && !document.querySelector('#modal [data-pendadd] img')), 'a display name is shown as text, never as markup');
    await close();
  }
  /* already friends / already asked / my own id: nothing to ask */
  for (const [label, id] of [['already friends', FX.FRIENDS[0].id], ['my own link', ME.id]]) {
    const { page, close, log } = await desk({ path: '/?add=' + id, rpc: inviter('Someone') });
    await tick(page, 1500);
    const st = await store(page);
    ok(!(await cardOpen(page)) && frWrites(log).length === 0 && !st.s && !st.l, label + ': no card, nothing written, the invite is cleared', { st, w: frWrites(log) });
    await close();
  }
  /* a send that fails keeps the card and the invite; two quick taps are one request; then it goes through */
  {
    const hs = { n: 0, fail: true };
    const hook = (url, m) => (url.pathname === '/rest/v1/friend_requests' && m === 'POST') ? (hs.n++, hs.fail ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : null) : null;
    const { page, close, log } = await desk({ path: '/?add=' + SUG.id, rpc: inviter(SUG.display_name), hook });
    await tick(page, 1500);
    await page.evaluate(() => { pendAddAnswer(true); pendAddAnswer(true); });
    await tick(page, 1000);
    const st = await store(page);
    ok(hs.n === 1, 'two quick Add taps are one request', hs.n);
    ok(await cardOpen(page) && st.s === SUG.id && (await page.locator('#pendAddYes').isDisabled({ timeout: 1500 }).catch(() => null)) === false, 'a failed send keeps the card, keeps the invite and lets Add be tried again', { st });
    hs.fail = false;
    await clk(page, '#pendAddYes'); await tick(page, 1200);
    const w = frWrites(log), st2 = await store(page);
    ok(hs.n === 2 && w.length === 1 && w[0].body.to_user === SUG.id && !(await cardOpen(page)) && !st2.s && !st2.l, 'then Add goes through once and clears the invite', { n: hs.n, w, st2 });
    await close();
  }
}

/* ------------------------------------------------------------------ 1b. signed out, then in */
if (want('signedout')) {
  const { page, close, log } = await desk({ signedIn: false, path: '/?add=' + SUG.id, rpc: inviter(SUG.display_name) });
  await tick(page, 1500);
  const land = await page.locator('#modal').innerText().catch(() => '');
  ok(/Pat Suggestia wants to compare schedules/.test(land) && frWrites(log).length === 0, 'signed out: the welcome names who invited you and nothing is written', land.slice(0, 160));
  const st = await store(page);
  ok(st.s === SUG.id && st.l === SUG.id, 'signed out: the invite is kept for after sign-in', st);
  await page.evaluate(async () => { await sb.auth.signInWithPassword({ email: 'tester@calpoly.edu', password: 'fixture-pass' }); });
  await tick(page, 2500);
  ok(await page.evaluate(() => !!(typeof sbUser !== 'undefined' && sbUser)), 'set-up: signed in');
  for (let i = 0; i < 6 && !(await cardOpen(page)); i++) await tick(page, 1600);
  const t = await cardText(page);
  ok(t && /Add Pat Suggestia\?/.test(t) && frWrites(log).length === 0, 'signing in shows the card and still writes nothing', { t, w: frWrites(log) });
  await clk(page, '#pendAddYes'); await tick(page, 1200);
  const w = frWrites(log);
  ok(w.length === 1 && w[0].body.to_user === SUG.id && w[0].body.from_user === ME.id, 'then Add writes exactly one request', w);
  /* the signed-out welcome still on screen when the invite is asked about (signing in from the header, say) must not hold the card back */
  await page.evaluate(id => { pendAddSet(id); paintInviteLanding(null); processPendingAdd(); }, FX.STRANGER.id);
  for (let i = 0; i < 4 && !(await cardOpen(page)); i++) await tick(page, 1600);
  const t2 = await cardText(page);
  ok(t2 && /^Friend request\s+Add /i.test(t2.replace(/\n+/g, ' ')) && await page.evaluate(() => !document.querySelector('#modal [data-invite-landing]')), 'a welcome left open from before sign-in is closed for the card', t2);
  ok(log.errors.length === 0, 'no page errors (signed out, then in)', log.errors);
  await close();
}

/* ------------------------------------------------------------------ 1c. 14 days */
if (want('expiry')) {
  const seed = ageDays => `(function(){ var t=new Date('2026-09-29T10:30:00-07:00').getTime()-(${ageDays})*864e5; ` +
    `if(${ageDays}<0){ sessionStorage.setItem('professify_pending_add','${SUG.id}'); return; } ` +
    `sessionStorage.setItem('professify_pending_add','${SUG.id}'); sessionStorage.setItem('professify_pending_add_at',String(t)); ` +
    `localStorage.setItem('professify_pending_add','${SUG.id}'); localStorage.setItem('professify_pending_add_at',String(t)); })();`;
  for (const [days, shows] of [[15, false], [13, true], [-1, true]]) {
    const { page, close, log } = await desk({ path: '/', rpc: inviter(SUG.display_name), init: seed(days) });
    await tick(page, 1500);
    const st = await store(page);
    const label = days < 0 ? 'an invite stashed before it carried a date' : 'an invite ' + days + ' days old';
    ok((await cardOpen(page)) === shows && frWrites(log).length === 0, label + (shows ? ': still asked about' : ': is not asked about'), { st });
    if (!shows) ok(!st.s && !st.l && !st.sat && !st.lat, label + ': and is cleared', st);
    if (days < 0) ok(+st.sat > 0, label + ': starts its 14 days now', st);
    await close();
  }
}

/* ------------------------------------------------------------------ 1d. the shared-schedule landing */
if (want('landing')) {
  const enc = Buffer.from(JSON.stringify({ cl: [{ c: 'CSC 101', n: 'Intro to Computing', t: 'MoWe 9:00AM-10:00AM', p: 'Staff', s: '01' }] })).toString('base64url');
  const { page, close, log } = await desk({ path: '/?sched=' + enc + '&nm=Mom&add=' + SUG.id, rpc: inviter(SUG.display_name) });
  await tick(page, 1500);
  const land = await page.locator('#schedLanding').innerText().catch(() => '');
  ok(/Add Mom/.test(land) && frWrites(log).length === 0, 'a shared schedule signed in: the landing shows and nothing is written', { land: land.slice(0, 120), w: frWrites(log) });
  ok(!(await cardOpen(page)) && (await store(page)).s === SUG.id, 'the card waits behind the landing, and the invite is kept');
  await clk(page, '#schedLanding .sl-cta'); await tick(page, 1200);
  const t = await cardText(page);
  ok(t && /Add Pat Suggestia\?/.test(t) && !/Mom/.test(t) && frWrites(log).length === 0, 'its button asks too, with the name from the profile, not the one in the link', t);
  await clk(page, '#pendAddYes'); await tick(page, 1200);
  const w = frWrites(log);
  ok(w.length === 1 && w[0].body.to_user === SUG.id, 'Add writes exactly one request', w);
  await close();
}

/* ------------------------------------------------------------------ 2. pdf.js */
if (want('pdf')) {
  const { page, close } = await desk({});
  const r = await page.evaluate(async () => {
    const lib = await loadPdfJs();                                    // the real script, through its integrity check
    const tag = document.querySelector('script[src*="pdfjs-dist"]');
    const real = window.pdfjsLib; let seen = null;
    window.pdfjsLib = { GlobalWorkerOptions: real.GlobalWorkerOptions, getDocument(o) { seen = o; return real.getDocument(o); } };
    try { await Promise.race([pdfToText(new File([new Uint8Array([37, 80, 68, 70])], 'x.pdf')), new Promise(r => setTimeout(r, 3000))]); } catch (e) {}
    return { loaded: !!(lib && real.getDocument), tag: tag && { i: tag.integrity, c: tag.crossOrigin }, seen: seen && { eval: seen.isEvalSupported, data: !!seen.data, off: seen.isOffscreenCanvasSupported } };
  });
  ok(r.loaded, 'pdf.js loads through its integrity hash', r);
  ok(r.seen && r.seen.eval === false && r.seen.data, 'getDocument() is called with isEvalSupported:false (and the data)', r.seen);
  ok(r.seen && r.seen.off === false, 'getDocument() keeps isOffscreenCanvasSupported:false', r.seen);
  await close();
}

/* ------------------------------------------------------------------ 3. SRI */
const SRI = {
  tess: { loader: 'loadOcr()', global: 'Tesseract', url: 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js', sri: 'sha384-GJqSu7vueQ9qN0E9yLPb3Wtpd7OrgK8KmYzC8T1IysG1bcvxvIO4qtYR/D3A991F', file: 'tesseract.js_5.1.1/package/dist/tesseract.min.js' },
  pdf: { loader: 'loadPdfJs()', global: 'pdfjsLib', url: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/legacy/build/pdf.min.js', sri: 'sha384-OemFRmhjDZwhIKuUld0HJozkF2YErsgDaCL41trxGQZt4/WgnopJQqQl2DvDZ07Z', file: 'pdfjs-dist_3.11.174/package/legacy/build/pdf.min.js' },
  qr: { loader: 'loadQrGen()', global: 'qrcode', url: 'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js', sri: 'sha384-8FWZA6BGMXhsfO+BLtrJK0We6gg5o1JyO8xQm6peWDEUs17ACA5ziE/NIAkl9z2k', file: 'qrcode-generator_1.4.4/package/qrcode.js' },
};
if (want('sri')) {
  const SRI_DIR = process.env.SRI_DIR || '/tmp/claude-0/sri';
  const { page, ctx, close } = await desk({});
  for (const [k, e] of Object.entries(SRI)) {
    /* the tag the page puts in */
    await page.evaluate(([g, loader]) => { window[g] = undefined; window.__lazy = {}; window.__p = eval(loader).catch(() => 'rejected'); }, [e.global, e.loader]);
    const tag = await page.evaluate(u => { const t = document.querySelector('script[src="' + u + '"]'); return t && { i: t.integrity, c: t.crossOrigin, a: t.async }; }, e.url);
    ok(tag && tag.i === e.sri && tag.c === 'anonymous', k + ': the script tag is the pinned URL with integrity + crossorigin="anonymous"', tag);
    await page.evaluate(() => Promise.race([window.__p, new Promise(r => setTimeout(r, 5000))]));   // let the first request settle before the same URL is asked for again
    ok(!/tesseract\.js@5\//.test(e.url) && /@\d+\.\d+\.\d+\//.test(e.url), k + ': an exact version, not a floating one', e.url);
    await page.evaluate(() => { document.querySelectorAll('script[src*="cdn.jsdelivr.net"]').forEach(s => s.remove()); window.__lazy = {}; });
    /* the bytes the browser checks it against */
    const f = path.join(SRI_DIR, e.file);
    if (!fs.existsSync(f)) { console.log('  skip  ' + k + ': no ' + f + ' (npm pack the package into SRI_DIR to run the byte check)'); continue; }
    const body = fs.readFileSync(f);
    let serve = body;
    await ctx.route(u => u.href === e.url, route => route.fulfill({ status: 200, contentType: 'text/javascript', headers: { 'access-control-allow-origin': '*' }, body: serve }));
    const good = await page.evaluate(async ([g, loader]) => { window[g] = undefined; window.__lazy = {}; try { const r = await eval(loader); return !!r && !!window[g]; } catch (err) { return String(err); } }, [e.global, e.loader]);
    ok(good === true, k + ': the real file passes its hash in the browser', good);
    serve = Buffer.concat([body, Buffer.from('\n;window.__tampered=1;\n')]);
    const bad = await page.evaluate(async ([g, loader]) => { window[g] = undefined; window.__lazy = {}; window.__tampered = 0; document.querySelectorAll('script[src*="cdn.jsdelivr.net"]').forEach(s => s.remove()); try { await eval(loader); return 'loaded'; } catch (err) { return /Could not load/.test(String(err)) ? 'refused' : String(err); } }, [e.global, e.loader]);
    const ran = await page.evaluate(() => window.__tampered);
    ok(bad === 'refused' && !ran, k + ': a changed file is refused and does not run', { bad, ran });
  }
  await close();
}

/* ------------------------------------------------------------------ 4. sw.js */
if (want('sw')) {
  const src = fs.readFileSync(path.join(DIR, 'sw.js'), 'utf8');
  const load = () => {
    const h = {}, shown = [], opened = [], navs = [];
    let clientList = [];
    const self = { location: new URL('https://termchamp.com/sw.js'), addEventListener: (t, f) => { h[t] = f; }, registration: { showNotification: (t, o) => { shown.push(o); return Promise.resolve(); } },
      clients: { matchAll: async () => clientList, openWindow: async u => { opened.push(u); }, claim: async () => {} }, skipWaiting() {} };
    vm.runInNewContext(src, { self, URL, Promise, console, caches: {}, fetch: async () => ({}), setTimeout, clearTimeout });
    return { h, shown, opened, navs, setClients: l => { clientList = l; } };
  };
  const push = async (w, d) => { let p; await w.h.push({ data: { json: () => d }, waitUntil: x => { p = x; } }); await p; return w.shown[w.shown.length - 1].data.url; };
  const w = load();
  const cases = [['/x', '/x'], ['/x?a=1#h', '/x?a=1#h'], ['/', '/'], ['//evil.example', '/'], ['//evil.example/path', '/'], ['/\\evil.example', '/'], ['/\\/evil.example', '/'], ['https://evil.example/', '/'], ['https://evil.example/steal?x=1', '/'],
    ['http://termchamp.com@evil.example/', '/'], ['javascript:alert(1)', '/'], ['https://termchamp.com/y?q=1', '/y?q=1'], ['', '/'], [null, '/'], [12, '/'], [undefined, '/']];
  for (const [u, want] of cases) { const got = await push(w, { title: 't', body: 'b', url: u }); ok(got === want, 'sw push url ' + JSON.stringify(u) + ' → ' + JSON.stringify(want), got); }
  /* a notification made by an older worker is checked again on click */
  for (const [u, want] of [['//evil.example', '/'], ['/\\evil.example', '/'], ['/ok', '/ok'], [undefined, '/']]) {
    const w2 = load(); const navs = [];
    w2.setClients([{ url: 'https://termchamp.com/', focus: async () => {}, navigate: async x => { navs.push(x); } }]);
    let p; w2.h.notificationclick({ notification: { close() {}, data: u === undefined ? undefined : { url: u } }, waitUntil: x => { p = x; } }); await p;
    ok(navs.length === 1 && navs[0] === want, 'sw click on a stored url ' + JSON.stringify(u) + ' navigates to ' + JSON.stringify(want), navs);
    const w3 = load(); w3.setClients([]); let p3; w3.h.notificationclick({ notification: { close() {}, data: { url: u } }, waitUntil: x => { p3 = x; } }); await p3;
    ok(w3.opened.length === 1 && w3.opened[0] === want, 'sw click with no window opens ' + JSON.stringify(want), w3.opened);
  }
}

console.log(`\ncheck-desktop-invite-confirm: ${pass} passed, ${fail} failed`);
if (fail) process.exitCode = 1;
