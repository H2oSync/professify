/* check-desktop-hawk-fresh — website-hawk-fresh-2026-10-14: the page asks for Champ's files with the build in the URL,
   so a service worker still holding last build's copies (cache-first, keyed by the full URL) cannot hand them back.
   Run: APP_DIR=<repo> node check-desktop-hawk-fresh.mjs */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, n, i) => { if (c) { pass++; console.log('  ok  ', n); } else { fail++; console.log('  FAIL', n, i !== undefined ? '→ ' + JSON.stringify(i).slice(0, 300) : ''); } };
const { page, close, log } = await openApp({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live' });
await page.waitForTimeout(2500);
const r = await page.evaluate(() => {
  const v = String(window.PROFESSIFY_BUILD || '').replace(/[^0-9]/g, '');
  const css = [...document.querySelectorAll('link[rel=stylesheet]')].map(l => l.getAttribute('href')).filter(h => /hawk-ask\.css/.test(h));
  const js = [...document.scripts].map(s => s.getAttribute('src') || '').filter(s => /hawk-(ask|router)\.js/.test(s));
  return { v, css, js, champ: !!document.querySelector('.hawk-fab__bird'),
           loaded: [...document.styleSheets].some(s => (s.href || '').includes('hawk-ask.css') && [...s.cssRules].some(x => (x.cssText || '').includes('hawk-fab__bird'))) };
});
ok(r.v.length === 12, 'the build stamp has a date and time', r.v);
ok(r.css.length === 1 && r.css[0] === 'hawk-ask.css?v=' + r.v, 'hawk-ask.css carries ?v=<build>', r.css);
ok(r.js.length === 2 && r.js.every(s => s.endsWith('.js?v=' + r.v)), 'hawk-router.js and hawk-ask.js carry ?v=<build>', r.js);
ok(r.champ && r.loaded, 'the versioned files load: Champ is drawn and its stylesheet applied', r);
ok(log.errors.length === 0, 'no page errors', log.errors);
await close();
console.log(`\ncheck-desktop-hawk-fresh: ${pass} passed, ${fail} failed`); if (fail) process.exitCode = 1;
