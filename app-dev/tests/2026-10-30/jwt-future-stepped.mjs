/* check-app-jwt-future-2026-10-28.mjs with the fake clock stepped 1 s at a time (the original jumps 9-12 s in one
   runFor, which leaves no real time for the retried requests and fails on HEAD too). Same three assertions. */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const future = { status: 401, body: JSON.stringify({ code: 'PGRST303', details: null, hint: null, message: 'JWT issued at future' }) };
const step = async (page, s) => { for (let i = 0; i < s; i++) { await page.clock.runFor(1000); await page.waitForTimeout(120); } };
let n = 0;
let o = await openApp({ hook: (url, m) => { if (url.pathname === '/rest/v1/profiles' && m === 'GET' && n < 3) { n++; return future; } return null; }, wait: 0 });
await step(o.page, 12);
let st = await o.page.evaluate(() => ({ phase: TC.phase, retries: TC.jwtRetries || 0, refreshes: TC.jwtRefreshes || 0 }));
ok(n === 3 && st.retries >= 3 && st.phase === 'ok' && !st.refreshes, 'PGRST303 three times: retried quietly (no token refresh), the profile loads', st);
ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
let m2 = 0;
o = await openApp({ hook: (url, m) => { if (url.pathname === '/rest/v1/profiles' && m === 'GET') { m2++; return future; } return null; }, wait: 0 });
await step(o.page, 25);
st = await o.page.evaluate(() => ({ phase: TC.phase, h: document.querySelector('.tc-signin h1') && document.querySelector('.tc-signin h1').innerText }));
ok(/Couldn.t load your profile/.test(st.h || '') && m2 >= 5, 'PGRST303 every time: gives up after the retries and says so', { st, m2 });
await o.close();
let m3 = 0, tok = 0;
o = await openApp({ hook: (url, m) => { if (url.pathname.startsWith('/auth/v1/token')) tok++; if (url.pathname === '/rest/v1/profiles' && m === 'GET') { m3++; return { status: 401, body: JSON.stringify({ code: 'PGRST301', message: 'JWT expired' }) }; } return null; }, wait: 0 });
await step(o.page, 6);
ok(m3 >= 1 && m3 <= 2, 'another 401 (PGRST301) is not retry-looped', [m3, tok]);
await o.close();
console.log(`jwt-future-stepped: ${pass} passed, ${fail} failed`);
