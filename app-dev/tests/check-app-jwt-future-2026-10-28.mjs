import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const future = { status: 401, body: JSON.stringify({ code: 'PGRST303', details: null, hint: null, message: 'JWT issued at future' }) };
/* 1. the first three profile reads are refused "issued at future": the app waits, retries, and loads */
let n = 0;
let o = await openApp({ hook: (url, m) => { if (url.pathname === '/rest/v1/profiles' && m === 'GET' && n < 3) { n++; return future; } return null; }, wait: 9000 });
let st = await o.page.evaluate(() => ({ phase: TC.phase, retries: TC.jwtRetries || 0, err: !!document.querySelector('.tc-signin h1') && document.querySelector('.tc-signin h1').innerText }));
ok(n === 3 && st.retries >= 3 && st.phase !== 'profileerr' && !/Couldn.t load/.test(st.err || ''), 'PGRST303 three times: retried quietly, the profile loads', st);
ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
/* 2. it never clears: after 4 retries the honest error shows */
let m2 = 0;
o = await openApp({ hook: (url, m) => { if (url.pathname === '/rest/v1/profiles' && m === 'GET') { m2++; return future; } return null; }, wait: 12000 });
st = await o.page.evaluate(() => ({ phase: TC.phase, h: document.querySelector('.tc-signin h1') && document.querySelector('.tc-signin h1').innerText }));
ok(/Couldn.t load your profile/.test(st.h || '') && m2 >= 5, 'PGRST303 every time: gives up after the retries and says so', { st, m2 });
await o.close();
/* 3. a different 401 is not retried */
let m3 = 0;
o = await openApp({ hook: (url, m) => { if (url.pathname === '/rest/v1/profiles' && m === 'GET') { m3++; return { status: 401, body: JSON.stringify({ code: 'PGRST301', message: 'JWT expired' }) }; } return null; }, wait: 4000 });
ok(m3 >= 1 && m3 <= 2, 'another 401 (PGRST301) is passed straight through, not retried', m3);
await o.close();
console.log(`jwt-test: ${pass} passed, ${fail} failed`);
