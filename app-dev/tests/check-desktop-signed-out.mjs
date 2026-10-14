/* check-desktop-signed-out — website-signed-out-fall-2026-10-14: signed out, My classes opens on Spring 2027 and the
   Fall 2026 chip says to sign in; it never shows a loading line that cannot finish. Run: APP_DIR=<repo> node check-desktop-signed-out.mjs */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, n, i) => { if (c) { pass++; console.log('  ok  ', n); } else { fail++; console.log('  FAIL', n, i !== undefined ? '→ ' + JSON.stringify(i).slice(0, 300) : ''); } };
const { page, close, log } = await openApp({ path: '/?tab=sched', width: 1440, height: 900, wait: 4000, terms: 'live', signedIn: false });
await page.waitForTimeout(3000);
const st = await page.evaluate(() => ({ signed: !!(typeof sbUser !== 'undefined' && sbUser), two: mcTwoTerms(), view: mcTermView() }));
ok(!st.signed && st.two, 'set-up: signed out, two terms', st);
ok(st.view === 'term', 'signed out, My classes opens on Spring 2027', st);
await page.evaluate(() => { show('sched'); setSchedTab('mine'); mcSetTermView('now'); });
await page.waitForTimeout(800);
const t = await page.evaluate(() => (document.querySelector('#view-sched') || {}).innerText || '');
ok(/Sign in to see your Fall 2026 classes/.test(t) && !/Loading your Fall 2026 classes/.test(t), 'the Fall chip says to sign in, never “Loading…”', t.slice(0, 400));
ok(log.errors.length === 0, 'no page errors', log.errors);
await close();
console.log(`\ncheck-desktop-signed-out: ${pass} passed, ${fail} failed`); if (fail) process.exitCode = 1;
