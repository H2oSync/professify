/* Runs the REAL app/index.html, signed in or out, with no network.
 * The real supabase-js runs (the npm tarball, byte-identical to the pinned jsDelivr file); only
 * the far end is ours — a PostgREST stand-in answering from synthetic fixtures, a PolyRatings
 * stand-in, and an `ask` function stand-in. Nothing leaves the machine.
 * Every write is recorded WITH its body, so a test can assert what the app actually sent. */
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import * as FX from './app-fixtures.mjs';

const SB_JS = '/home/claude/mob/vendor/supabase-supabase-js-2.112.4/package/dist/umd/supabase.js';
const SB_HOST = 'https://rqkndeqbcahozidniesn.supabase.co';
const STORAGE_KEY = 'sb-rqkndeqbcahozidniesn-auth-token';
function b64url(o) { return Buffer.from(JSON.stringify(o)).toString('base64url'); }
function session(user) {
  const exp = Math.floor(Date.now() / 1000) + 86400 * 400;
  const jwt = `${b64url({ alg: 'HS256', typ: 'JWT' })}.${b64url({ sub: user.id, email: user.email, role: 'authenticated', exp })}.sig`;
  return { access_token: jwt, refresh_token: 'fixture-refresh', token_type: 'bearer', expires_in: 86400, expires_at: exp,
    user: { id: user.id, aud: 'authenticated', role: 'authenticated', email: user.email, email_confirmed_at: '2026-09-01T00:00:00Z', app_metadata: { provider: 'email' }, user_metadata: {} } };
}
/* Column grants, as the live database has them (professify-lockdown.sql, -schools.sql,
   -reviews-anon-fix.sql). A SELECT that names a column outside the grant — or '*', which PostgREST
   expands to every column — is refused with 42501 for the whole request, own row included. The
   stand-in used to answer any column, which is how a profile read of `concentration` passed every
   test here and failed for Tate's real account on the first sign-in. */
const COL_GRANTS = {
  profiles: ['id', 'display_name', 'username', 'avatar_url', 'major', 'class_standing', 'pinned_friends', 'instagram_handle', 'school'],
  reviews: { not: ['user_id'] },
};
function colDenied(table, select) {
  const g = COL_GRANTS[table]; if (!g) return null;
  const cols = String(select || '*').split(',').map(c => c.trim().split(':').pop().split('(')[0]).filter(Boolean);
  for (const c of cols) {
    if (c === '*') return { code: '42501', message: 'permission denied for table ' + table };
    if (Array.isArray(g) ? !g.includes(c) : g.not.includes(c)) return { code: '42501', message: 'permission denied for table ' + table };
  }
  return null;
}
function applyFilters(rows, params) {
  let out = rows.slice();
  for (const [k, v] of params) {
    if (['select', 'order', 'limit', 'offset', 'on_conflict', 'columns'].includes(k)) continue;
    let m;
    if (k === 'or') {
      const parts = v.replace(/^\(|\)$/g, '').split(',').map(p => /^(\w+)\.eq\.(.*)$/.exec(p)).filter(Boolean);
      out = out.filter(r => parts.some(p => String(r[p[1]]) === p[2]));
    } else if ((m = /^eq\.(.*)$/.exec(v))) out = out.filter(r => String(r[k]) === m[1]);
    else if ((m = /^neq\.(.*)$/.exec(v))) out = out.filter(r => String(r[k]) !== m[1]);
    else if ((m = /^ilike\.(.*)$/.exec(v))) { const re = new RegExp('^' + m[1].replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/[%*]/g, '.*') + '$', 'i'); out = out.filter(r => re.test(String(r[k] ?? ''))); }
    else if ((m = /^in\.\((.*)\)$/.exec(v))) { const set = m[1].split(',').map(s => s.replace(/^"|"$/g, '')); out = out.filter(r => set.includes(String(r[k]))); }
  }
  const ord = params.get('order'); if (ord) { const [col, dir] = ord.split(',')[0].split('.'); out.sort((a, b) => (a[col] > b[col] ? 1 : a[col] < b[col] ? -1 : 0) * (dir === 'desc' ? -1 : 1)); }
  const off = +(params.get('offset') || 0), lim = params.has('limit') ? +params.get('limit') : Infinity;
  return out.slice(off, off + lim);
}

export async function openApp({ signedIn = true, width = 390, height = 844, tables = FX.TABLES, rpc = FX.RPC, poly = FX.POLY,
  ask = null, hook = null, port = 8190, time = '2026-09-29T10:30:00-07:00', init = null, wait = 2500, tz = 'America/Los_Angeles' } = {}) {
  const dir = process.env.APP_DIR || path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'out');
  const log = { reads: [], writes: [], asks: [], errors: [], console: [] };
  const T = JSON.parse(JSON.stringify(tables));
  const srv = http.createServer((q, r) => {
    let u = decodeURIComponent(q.url.split('?')[0]); if (u.endsWith('/')) u += 'index.html';
    const f = path.join(dir, u);
    if (!f.startsWith(dir) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
    const CT = { '.html': 'text/html', '.js': 'text/javascript', '.webmanifest': 'application/manifest+json', '.png': 'image/png' };
    r.writeHead(200, { 'content-type': CT[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
  });
  await new Promise(res => srv.listen(port, res));
  const origin = `http://localhost:${port}`;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, timezoneId: tz, isMobile: width < 700, hasTouch: width < 700 });
  const sess = session(FX.ME);
  let nextId = 5000;
  let authed = signedIn;                 // flips on a successful code or password sign-in
  await ctx.route('**', async route => {
    const req = route.request(); const url = new URL(req.url());
    if (url.origin === origin) return route.continue();
    if (url.href.startsWith('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.112.4/dist/umd/supabase.js'))
      return route.fulfill({ status: 200, contentType: 'text/javascript', headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(SB_JS) });
    if (url.href.startsWith('https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/legacy/build/')) {
      const f = path.join('/tmp/claude-0/pdfjs/package/legacy/build', path.basename(url.pathname));
      if (fs.existsSync(f)) return route.fulfill({ status: 200, contentType: 'text/javascript', headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(f) });
      return route.fulfill({ status: 404, body: '' });
    }
    if (url.hostname === 'api-prod.polyratings.org') {
      if (url.pathname.startsWith('/professors.all') && poly) return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify({ result: { data: poly } }) });
      return route.fulfill({ status: 500, body: '' });
    }
    if (url.origin === SB_HOST) {
      const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*', 'access-control-expose-headers': 'content-range' };
      if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
      const p = url.pathname, m = req.method();
      let body = null; try { body = req.postData() ? JSON.parse(req.postData()) : null; } catch (e) { body = req.postData(); }
      if (hook) { const o = hook(url, m, body); if (o) return route.fulfill({ headers: cors, contentType: 'application/json', ...o }); }
      if (p.startsWith('/functions/v1/ask')) {
        log.asks.push(body);
        const a = ask ? ask(body) : null;
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify(a || { fallback: 'search', reason: 'fixture' }) });
      }
      if (p.startsWith('/storage/v1/object/')) {
        log.writes.push({ m, table: 'storage:' + p.slice(19), body: null, bytes: (req.postDataBuffer() || Buffer.alloc(0)).length, ctype: req.headers()['content-type'] || '' });
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify({ Key: p.slice(19) }) });
      }
      if (p.startsWith('/auth/v1/user') && m !== 'GET') { log.writes.push({ m, table: 'auth:user', body }); return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify(sess.user) }); }
      if (p.startsWith('/auth/v1/user')) return route.fulfill({ status: authed ? 200 : 401, headers: cors, contentType: 'application/json', body: JSON.stringify(authed ? sess.user : { msg: 'no' }) });
      if (p.startsWith('/auth/v1/')) { log.writes.push({ m, table: 'auth:' + p.slice(9), body }); const ok = p.includes('token') || p.includes('verify'); if (ok) authed = true; return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: ok ? JSON.stringify(sess) : '{}' }); }
      if (p.startsWith('/rest/v1/rpc/')) {
        const fn = p.slice(13); log.reads.push('rpc:' + fn);
        const v = fn in rpc ? rpc[fn] : [];
        if (v && v.__error) return route.fulfill({ status: 400, headers: cors, contentType: 'application/json', body: JSON.stringify(v.__error) });
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify(v) });
      }
      if (p.startsWith('/rest/v1/')) {
        const table = p.slice(9);
        if (m !== 'GET' && m !== 'HEAD') {
          log.writes.push({ m, table, body, query: url.search });
          if (url.searchParams.get('select')) { const d = colDenied(table, url.searchParams.get('select')); if (d) return route.fulfill({ status: 403, headers: cors, contentType: 'application/json', body: JSON.stringify(Object.assign({ details: null, hint: null }, d)) }); }
          const prefer = req.headers()['prefer'] || '';
          let rows = [];
          if (m === 'PATCH' || m === 'DELETE') {
            rows = applyFilters(T[table] || [], url.searchParams);
            if (m === 'PATCH') rows.forEach(r => Object.assign(r, body));
            else T[table] = (T[table] || []).filter(r => rows.indexOf(r) < 0);
          }
          if (m === 'POST') {
            const arr = (Array.isArray(body) ? body : [body]).map(r => Object.assign({ id: r.id || (table === 'conversations' ? 'c-new-' + (nextId++) : nextId++), created_at: new Date().toISOString() }, r));
            T[table] = (T[table] || []).concat(arr); rows = arr;
          }
          const accept = req.headers()['accept'] || '';
          if (/return=representation/.test(prefer)) {
            if (accept.includes('vnd.pgrst.object')) return route.fulfill({ status: 201, headers: cors, contentType: 'application/json', body: JSON.stringify(rows[0] || {}) });
            return route.fulfill({ status: 201, headers: cors, contentType: 'application/json', body: JSON.stringify(rows) });
          }
          return route.fulfill({ status: m === 'DELETE' ? 204 : 201, headers: cors, body: '' });
        }
        log.reads.push(table + url.search);
        { const d = colDenied(table, url.searchParams.get('select')); if (d) return route.fulfill({ status: 403, headers: cors, contentType: 'application/json', body: JSON.stringify(Object.assign({ details: null, hint: null }, d)) }); }
        const rows = applyFilters(authed || table === 'course_seats' || table === 'course_catalog' ? (T[table] || []) : [], url.searchParams);
        const h = { ...cors, 'content-range': `0-${Math.max(0, rows.length - 1)}/${rows.length}` };
        const accept = req.headers()['accept'] || '';
        if (accept.includes('vnd.pgrst.object')) {
          if (rows.length !== 1) return route.fulfill({ status: 406, headers: h, contentType: 'application/json', body: JSON.stringify({ code: 'PGRST116', message: 'JSON object requested, multiple (or no) rows returned', details: 'The result contains ' + rows.length + ' rows' }) });
          return route.fulfill({ status: 200, headers: h, contentType: 'application/json', body: JSON.stringify(rows[0]) });
        }
        return route.fulfill({ status: 200, headers: h, contentType: 'application/json', body: m === 'HEAD' ? '' : JSON.stringify(rows) });
      }
      return route.fulfill({ status: 404, headers: cors, body: '' });
    }
    return route.abort();
  });
  /* Realtime is a WebSocket, which ctx.route() does not see: answer it here so nothing ever
     dials Supabase. The socket stays open and silent; tests push nothing through it. */
  await ctx.routeWebSocket(/.*/, ws => { log.reads.push('ws:' + new URL(ws.url()).pathname); });
  await ctx.addInitScript(({ key, sess, signedIn }) => { try { if (signedIn) localStorage.setItem(key, JSON.stringify(sess)); } catch (e) {} }, { key: STORAGE_KEY, sess, signedIn });
  if (init) await ctx.addInitScript(init);
  const page = await ctx.newPage();
  if (time) await page.clock.install({ time: new Date(time) });
  page.on('pageerror', e => log.errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') log.console.push(m.text()); });
  await page.goto(origin + '/app/', { waitUntil: 'domcontentloaded' });
  if (time) await page.clock.runFor(wait); else await page.waitForTimeout(wait);
  await page.waitForTimeout(400);
  const close = async () => { await browser.close(); try { srv.closeAllConnections(); } catch (e) {} await new Promise(res => srv.close(() => res())); };
  return { page, ctx, close, log, origin, tables: T };
}
