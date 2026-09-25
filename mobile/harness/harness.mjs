/* Runs the REAL index.html, signed in, with no network.
 *
 * The real supabase-js runs (served from the npm tarball — byte-identical to the pinned jsDelivr
 * file, the SRI hash matches), so every read the app makes goes through its own client code.
 * Only the far end is ours: a small PostgREST stand-in answering from synthetic fixtures.
 * Nothing leaves the machine; termchamp.com, Supabase and PolyRatings are never contacted.
 *
 *   const { page, close, log } = await openApp({ file:'build.html', theme:'cream', signedIn:true });
 */
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as FX from './fixtures.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const V = path.join(HERE, '..', 'vendor');
const SB_JS = path.join(V, 'supabase-supabase-js-2.112.4/package/dist/umd/supabase.js');
const SB_HOST = 'https://rqkndeqbcahozidniesn.supabase.co';
const STORAGE_KEY = 'sb-rqkndeqbcahozidniesn-auth-token';

const FONT_CSS = () => {
  const f = (fam, file, w, st = 'normal') =>
    `@font-face{font-family:'${fam}';font-style:${st};font-weight:${w};font-display:block;src:url(/__font/${file}) format('woff2')}`;
  return [
    f('Inter', 'fontsource-inter-5.3.0/package/files/inter-latin-400-normal.woff2', 400),
    f('Inter', 'fontsource-inter-5.3.0/package/files/inter-latin-500-normal.woff2', 500),
    f('Inter', 'fontsource-inter-5.3.0/package/files/inter-latin-600-normal.woff2', 600),
    f('Inter', 'fontsource-inter-5.3.0/package/files/inter-latin-700-normal.woff2', 700),
    f('Newsreader', 'nr/package/files/newsreader-latin-400-normal.woff2', 400),
    f('Newsreader', 'nr/package/files/newsreader-latin-500-normal.woff2', 500),
    f('Newsreader', 'nr/package/files/newsreader-latin-400-italic.woff2', 400, 'italic'),
    f('Newsreader', 'nr/package/files/newsreader-latin-500-italic.woff2', 500, 'italic'),
  ].join('\n');
};

function b64url(o) { return Buffer.from(JSON.stringify(o)).toString('base64url'); }
function session(user) {
  const exp = Math.floor(Date.now() / 1000) + 86400;
  const jwt = `${b64url({ alg: 'HS256', typ: 'JWT' })}.${b64url({ sub: user.id, email: user.email, role: 'authenticated', exp })}.sig`;
  return { access_token: jwt, refresh_token: 'fixture-refresh', token_type: 'bearer', expires_in: 86400, expires_at: exp,
    user: { id: user.id, aud: 'authenticated', role: 'authenticated', email: user.email,
            email_confirmed_at: '2026-09-01T00:00:00Z', app_metadata: { provider: 'email' }, user_metadata: {} } };
}

/* PostgREST, as much of it as this app uses: eq / in filters, limit/offset, count, single. */
function applyFilters(rows, params) {
  let out = rows.slice();
  for (const [k, v] of params) {
    if (['select', 'order', 'limit', 'offset', 'or', 'on_conflict', 'columns'].includes(k)) continue;
    let m;
    if ((m = /^eq\.(.*)$/.exec(v))) out = out.filter(r => !(k in r) || String(r[k]) === decodeURIComponent(m[1]));
    else if ((m = /^in\.\((.*)\)$/.exec(v))) { const set = m[1].split(',').map(s => s.replace(/^"|"$/g, ''));
      out = out.filter(r => !(k in r) || set.includes(String(r[k]))); }
  }
  const off = +(params.get('offset') || 0), lim = params.has('limit') ? +params.get('limit') : Infinity;
  return out.slice(off, off + lim);
}

export async function openApp({ file = 'build.html', dir = process.cwd(), theme = 'cream', signedIn = true,
  width = 390, height = 844, tables = FX.TABLES, rpc = FX.RPC, poly = FX.POLY, extraInit = null, port = 8140, hook = null } = {}) {
  const log = { reads: [], writes: [], errors: [], console: [] };
  const srv = http.createServer((q, r) => {
    const u = decodeURIComponent(q.url.split('?')[0]);
    const f = path.join(dir, u === '/' ? file : u);
    if (!f.startsWith(dir) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
    const T = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png',
      '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml' };
    r.writeHead(200, { 'content-type': T[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
  });
  await new Promise(res => srv.listen(port, res));
  const origin = `http://localhost:${port}`;

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 2,
    isMobile: width < 700, hasTouch: width < 700 });
  const sess = session(FX.ME);

  await ctx.route('**', async route => {
    const req = route.request(); const url = new URL(req.url());
    if (url.origin === origin) return route.continue();
    if (url.href.startsWith('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.112.4/dist/umd/supabase.js'))
      return route.fulfill({ status: 200, contentType: 'text/javascript', headers: { 'access-control-allow-origin': '*' },
        body: fs.readFileSync(SB_JS) });
    if (url.hostname === 'fonts.googleapis.com')
      return route.fulfill({ status: 200, contentType: 'text/css', body: FONT_CSS().replace(/\/__font\//g, `${origin}/__font/`) });
    if (url.hostname === 'api-prod.polyratings.org') {
      if (url.pathname.startsWith('/professors.all'))
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ result: { data: poly } }) });
      return route.fulfill({ status: 404, body: '' });
    }
    if (url.origin === SB_HOST) {
      const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*',
        'access-control-allow-methods': '*', 'access-control-expose-headers': 'content-range' };
      if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
      const p = url.pathname;
      if (p.startsWith('/auth/v1/user')) {
        if (!signedIn) return route.fulfill({ status: 401, headers: cors, contentType: 'application/json', body: '{"msg":"no"}' });
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify(sess.user) });
      }
      if (p.startsWith('/auth/v1/token'))
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify(sess) });
      if (p.startsWith('/auth/v1/'))
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: '{}' });
      if (p.startsWith('/rest/v1/rpc/')) {
        const fn = p.slice('/rest/v1/rpc/'.length);
        log.reads.push('rpc:' + fn);
        const v = fn in rpc ? rpc[fn] : [];
        return route.fulfill({ status: 200, headers: cors, contentType: 'application/json', body: JSON.stringify(v) });
      }
      if (hook) { const o = hook(url, req.method()); if (o) return route.fulfill({ headers: cors, contentType: 'application/json', ...o }); }
      if (p.startsWith('/rest/v1/')) {
        const table = p.slice('/rest/v1/'.length);
        const m = req.method();
        if (m !== 'GET' && m !== 'HEAD') {
          log.writes.push(`${m} ${table}`);
          return route.fulfill({ status: m === 'DELETE' ? 204 : 201, headers: cors, contentType: 'application/json', body: '[]' });
        }
        log.reads.push(table);
        const rows = applyFilters((signedIn || table === 'course_seats') ? (tables[table] || []) : [], url.searchParams);
        const h = { ...cors, 'content-range': `0-${Math.max(0, rows.length - 1)}/${rows.length}` };
        const accept = req.headers()['accept'] || '';
        if (accept.includes('vnd.pgrst.object')) {
          if (rows.length !== 1) return route.fulfill({ status: 406, headers: h, contentType: 'application/json',
            body: JSON.stringify({ code: 'PGRST116', message: 'JSON object requested, multiple (or no) rows returned' }) });
          return route.fulfill({ status: 200, headers: h, contentType: 'application/json', body: JSON.stringify(rows[0]) });
        }
        return route.fulfill({ status: 200, headers: h, contentType: 'application/json', body: m === 'HEAD' ? '' : JSON.stringify(rows) });
      }
      return route.fulfill({ status: 404, headers: cors, body: '' });
    }
    return route.abort();
  });

  await ctx.addInitScript(({ theme, key, sess, signedIn }) => {
    try { localStorage.setItem('professify-theme', theme); } catch (e) {}
    try { if (signedIn) localStorage.setItem(key, JSON.stringify(sess)); } catch (e) {}
    /* The PWA install nudge and first-run tours are real, but they cover the screen under test. */
    try { localStorage.setItem('professify_install_dismissed', String(Date.now())); } catch (e) {}
    /* The local profile the onboarding form writes — the fixture student's major and standing. */
    try { if (signedIn && !localStorage.getItem('professify-profile')) localStorage.setItem('professify-profile',
      JSON.stringify({ school: 'Cal Poly, San Luis Obispo', major: 'Business Administration', conc: null, year: '2026', standing: 'Junior', minor: 'None' })); } catch (e) {}
  }, { theme, key: STORAGE_KEY, sess, signedIn });
  if (extraInit) await ctx.addInitScript(extraInit);

  /* Inter stands in for the phone's system face (SF on iPhone); the container has neither. */
  const page = await ctx.newPage();
  page.on('pageerror', e => log.errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') log.console.push(m.text()); });
  await page.goto(origin + '/', { waitUntil: 'domcontentloaded' });
  await page.addStyleTag({ content: FONT_CSS().replace(/\/__font\//g, `${origin}/__font/`) });
  await page.waitForFunction(() => document.readyState === 'complete');
  await page.waitForTimeout(3000);

  const close = async () => { await browser.close(); srv.close(); };
  return { page, ctx, close, log, origin };
}

/* /__font/ is served out of vendor/ by a symlink the render script creates. */
export function linkFonts(dir) {
  const l = path.join(dir, '__font');
  if (!fs.existsSync(l)) fs.symlinkSync(V, l);
}
