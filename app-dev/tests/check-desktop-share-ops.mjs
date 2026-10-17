/* check-desktop-share-ops — share-ops (2026-10-16), run on the REAL index.html.
   A shared Plan link (/s forwards ?i=<hex>.png&nm=Sean&tm=Spring%202027&add=<uuid>&pl=A to the website) lands as
   "Sean's Plan A · Spring 2027", not "Sean's Spring 2027 schedule". A link with no pl reads exactly as before, a bad pl is
   ignored, a bad tm falls back to the term inside the stored week, and nothing from the URL is ever written as markup.
   Run: APP_DIR=<repo> APP_PORT=8481 node check-desktop-share-ops.mjs [--quiet]  */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const QUIET = process.argv.includes('--quiet');
let pass = 0, fail = 0;
const ok = (c, name, info) => { if (c) { pass++; if (!QUIET) console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); } };
const tick = async (p, ms = 500) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, port: +(process.env.APP_PORT || 8481) }, o));
const H1 = 'cc68d9c41252dde55d5fb8b2211a8336', SUG = FX.SUGGESTED;
const PATH = '/storage/v1/object/public/schedule-cards/' + H1 + '.json';

const pre = await desk({ signedIn: false, path: '/' });
// the stored week says Fall 2026: a Plan for another term must win over it
const enc = await pre.page.evaluate(() => _b64urlEnc(_shEncode('Fall 2026', [{ c: 'BUS 3438', n: '', t: 'MWF 10:10AM–11:00AM', p: 'Ada Examplewood', s: '01' }]))); await pre.close();

const landing = async search => {
  const o = await desk({ signedIn: false, path: '/', search, hook: (url, m) => (m === 'GET' && url.pathname === PATH) ? { status: 200, contentType: 'text/plain', body: enc } : null });
  await tick(o.page, 1200);
  const r = await o.page.evaluate(() => { const e = document.getElementById('schedLanding'); const h = e && e.querySelector('.sl-h');
    return e && e.style.display === 'flex' ? { h: h.innerText, html: h.innerHTML, all: e.innerHTML } : null; });
  await o.close(); return r;
};
const I = '?i=' + H1 + '.png&nm=Sean';

let r = await landing(I + '&tm=Spring%202027&add=' + SUG.id + '&pl=A');
ok(r && r.h === 'Sean’s Plan A · Spring 2027', 'a shared Plan A for Spring 2027 reads “Sean’s Plan A · Spring 2027”', r && r.h);
r = await landing(I + '&tm=Fall%202026&add=' + SUG.id + '&pl=C');
ok(r && r.h === 'Sean’s Plan C · Fall 2026', 'Plan C, Fall 2026', r && r.h);
r = await landing(I + '&tm=Spring%202027&add=' + SUG.id);
ok(r && r.h === 'Sean’s Spring 2027 schedule', 'no pl: a schedule, as before — and the link’s term beats the stored week’s', r && r.h);
r = await landing(I + '&add=' + SUG.id);
ok(r && r.h === 'Sean’s Fall 2026 schedule', 'no pl and no tm: the stored week’s term, as before', r && r.h);
r = await landing(I + '&tm=Spring%202027&pl=B');
ok(r && r.h === 'Plan B · Spring 2027', 'a Plan with no add= (so no name claimed): “Plan B · Spring 2027”', r && r.h);
r = await landing(I + '&add=' + SUG.id + '&pl=B');
ok(r && r.h === 'Sean’s Plan B · Fall 2026', 'a Plan with no tm: the stored week’s term', r && r.h);
for (const pl of ['D', 'a', 'AB', '%3Cb%3E', '']) {
  r = await landing(I + '&tm=Spring%202027&add=' + SUG.id + '&pl=' + pl);
  ok(r && r.h === 'Sean’s Spring 2027 schedule', 'a bad pl (' + decodeURIComponent(pl) + ') is ignored', r && r.h);
}
for (const tm of ['Autumn%202026', 'Fall%201999', 'Fall%202026%20x', '%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E', 'fall%202026']) {
  r = await landing(I + '&tm=' + tm + '&add=' + SUG.id + '&pl=A');
  ok(r && r.h === 'Sean’s Plan A · Fall 2026' && !/<img|onerror|Autumn|1999/.test(r.all), 'a bad tm (' + decodeURIComponent(tm) + ') is ignored, nothing written as markup', r && r.h);
}
r = await landing('?i=' + H1 + '.png&nm=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E&tm=Spring%202027&add=' + SUG.id + '&pl=A');
ok(r && !/<img src=x/.test(r.all) && /&lt;img/.test(r.all), 'a crafted name is still escaped on a Plan landing', r && r.h);

console.log((fail ? 'FAILED' : 'PASSED') + ': ' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
