/* shared bits for the 2026-10-30 stuck/can't-edit tests. Run with APP_DIR=<site> APP_PORT=<port>. */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
import * as FX from '/home/claude/tc/app-icon/app-dev/tests/app-fixtures.mjs';
export { openApp, FX };
export function mk(name) {
  const R = { pass: 0, fail: 0, name };
  R.ok = (c, m, d) => { if (c) { R.pass++; console.log('  ok  ', m); } else { R.fail++; console.log('  FAIL', m, d === undefined ? '' : JSON.stringify(d).slice(0, 400)); } };
  R.end = () => { console.log(`${name}: ${R.pass} passed, ${R.fail} failed`); process.exit(R.fail ? 1 : 0); };
  return R;
}
export async function tap(page, sel, txt, opts = {}) {
  const box = await page.evaluate(([sel, txt]) => {
    const els = [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height && (!txt || (e.textContent || '').replace(/\s+/g, ' ').includes(txt) || (e.getAttribute('aria-label') || '').includes(txt)); });
    const e = els[0]; if (!e) return null; e.scrollIntoView({ block: 'center' });
    const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }, [sel, txt || null]);
  if (!box) return false;
  await page.waitForTimeout(80); await page.touchscreen.tap(box.x, box.y); await page.waitForTimeout(opts.wait ?? 400);
  return true;
}
export const toastText = page => page.evaluate(() => { const t = document.getElementById('toast'); return t && t.classList.contains('on') ? t.textContent.trim() : ''; });
export const sheetType = page => page.evaluate(() => UI.sheet && UI.sheet.type);
export const sheetText = page => page.evaluate(() => ((document.getElementById('sheet') || {}).textContent || '').replace(/\s+/g, ' '));
export const acts = (page, root = '#sheet') => page.evaluate(r => [...document.querySelectorAll(r + ' [data-a]')].map(b => b.dataset.a + ':' + (b.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40)), root);
export const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25', MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '2274', label: 'Spring 2027' }] };
