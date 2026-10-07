/* check-desktop-delete — the WEBSITE's Delete account and Recover screen (2026-10-04), run on the real
   index.html in Chromium with the real supabase-js against the same PostgREST stand-in as check-app.
   Run: APP_DIR=<repo> node check-desktop-delete.mjs   (APP_PORT to move off 8190) */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) { if (c) { pass++; console.log('  ok  ', name); } else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 300) : ''); } }
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const PURGE = '2026-11-03T12:00:00.123456+00:00';
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1280, height: 900, wait: 4000 }, o));
/* my_account_deletion, request_account_deletion and cancel_account_deletion as the database does them */
const delHook = st => (url, m, body) => {
  const fn = url.pathname.startsWith('/rest/v1/rpc/') ? url.pathname.slice(13) : '';
  if (fn === 'my_account_deletion') { st.asked = (st.asked || 0) + 1; return { status: 200, body: JSON.stringify(st.at ? [{ purge_after: st.at, delete_reviews: false }] : []) }; }
  if (fn === 'request_account_deletion') { (st.req = st.req || []).push(body); if (st.reqFail) return { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) }; st.at = PURGE; return { status: 200, body: JSON.stringify(PURGE) }; }
  if (fn === 'cancel_account_deletion') { st.cancels = (st.cancels || 0) + 1; if (st.cancelFail) return { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) }; st.at = null; return { status: 200, body: 'true' }; }
  if (fn === 'delete_my_account') { st.immediate = true; return { status: 200, body: 'null' }; }
  return null;
};

/* 1. Signed in while pending: Recover, over everything */
{
  const st = { at: PURGE };
  const { page, close, log } = await desk({ hook: delHook(st) });
  await tick(page, 1500);
  const box = page.locator('#recBack.open');
  const t = await box.innerText().catch(() => '');
  ok(await box.count() === 1 && /Recover your account\?/.test(t) && /permanently deleted on Nov 3, 2026/.test(t) && /except your profile photo/.test(t), 'website: signing in while pending shows Recover your account? with the date and year', t.slice(0, 200));
  await page.mouse.click(30, 30); await page.keyboard.press('Escape'); await tick(page, 300);
  ok(await page.locator('#recBack.open').count() === 1, 'website: it can’t be clicked or Escaped away');
  st.cancelFail = true;
  await page.click('#recGo'); await tick(page, 400);
  ok(st.cancels === 1 && /still set to be deleted/.test(await page.locator('#recErr').innerText()) && await page.locator('#recBack.open').count() === 1 && !(await page.locator('#recGo').isDisabled()), 'website: a failed recover says the account is still set to be deleted, and can be tried again');
  st.cancelFail = false;
  await Promise.all([page.waitForEvent('load'), page.click('#recGo')]);
  await page.clock.runFor(4000); await page.waitForTimeout(800);
  ok(st.cancels === 2 && await page.locator('#recBack.open').count() === 0, 'website: Recover my account → cancel_account_deletion(), and the page comes back without the question', st);
  ok(/Welcome back/.test(await page.locator('body').innerText()), 'website: …and says welcome back');
  ok(log.errors.length === 0, 'website (recover): no page errors', log.errors);
  await close();
}

/* 2. Sign out instead */
{
  const st = { at: PURGE };
  const { page, close, log } = await desk({ hook: delHook(st) });
  await tick(page, 1500);
  await Promise.all([page.waitForEvent('load'), page.click('#recOut')]);
  await page.clock.runFor(3000); await page.waitForTimeout(500);
  ok(log.writes.some(w => /^auth:logout/.test(w.table)) && !st.cancels, 'website: Sign out signs out and recovers nothing', log.writes.map(w => w.table));
  await close();
}

/* 2b. A check that fails is asked again: Recover still comes up */
{
  const st = { at: PURGE }; let n = 0;
  const inner = delHook(st);
  const hook = (url, m, body) => (url.pathname === '/rest/v1/rpc/my_account_deletion' && ++n === 1) ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : inner(url, m, body);
  const { page, close } = await desk({ hook });
  await tick(page, 1500);
  ok(await page.locator('#recBack.open').count() === 0, 'website: a failed check doesn’t show it yet');
  await page.clock.runFor(6000); await page.waitForTimeout(600);
  ok(n >= 2 && await page.locator('#recBack.open').count() === 1, 'website: …and asks again, then shows Recover', n);
  const z = await page.evaluate(() => [getComputedStyle(document.getElementById('recBack')).zIndex, [...document.body.children].filter(e => e.id !== 'recBack' && !e.inert && e.tagName !== 'SCRIPT').length]);
  ok(+z[0] > 9000, 'website: Recover sits above everything else on the page', z);
  await close();
}

/* 3. Not pending, and a check that fails: the site as before */
{
  const st = {};
  const { page, close } = await desk({ hook: delHook(st) });
  await tick(page, 1500);
  ok(st.asked >= 1 && await page.locator('#recBack.open').count() === 0, 'website: not pending → no question');
  await close();
  const o = await desk({ hook: (url) => url.pathname === '/rest/v1/rpc/my_account_deletion' ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : null });
  await tick(o.page, 1500);
  ok(await o.page.locator('#recBack.open').count() === 0 && o.log.errors.length === 0, 'website: a failed check leaves the site as it was');
  await o.close();
}

/* 4. Delete account: 30 days, the reviews switch, every device signed out */
{
  const st = {};
  const rpc = Object.assign({}, FX.RPC, { my_reviews: [Object.assign({}, FX.MY_REVIEW, { id: 1 }), Object.assign({}, FX.MY_REVIEW, { id: 2 })] });
  const { page, close, log } = await desk({ hook: delHook(st), rpc });
  await tick(page, 1500);
  await page.evaluate(() => openDeleteAccount()); await tick(page, 800);
  const dlg = await page.locator('#delBack').innerText();
  ok(/After 30 days it's permanently deleted/.test(dlg) && /You have 30 days to change your mind/.test(dlg) && !/can't be undone/i.test(dlg), 'website: the delete dialog says 30 days and how to recover', dlg.slice(0, 300));
  const sw = page.locator('#delKeepRev');
  ok(await sw.count() === 1 && await sw.isChecked() && /Keep my 2 reviews up anonymously/.test(dlg) && /can’t be edited or removed later/.test(dlg), 'website: “Keep my 2 reviews up anonymously”, on by default', dlg.slice(-400));
  const keepDefault = await page.evaluate(() => !!document.getElementById('delKeepRev').checked);
  ok(keepDefault, 'website: keeping reviews is the default');
  await sw.uncheck(); await tick(page, 100);
  ok(/deleted along with your account/.test(await page.locator('#delKeepLine').innerText()), 'website: off says they’re deleted with the account');
  await page.fill('#delConfirm', 'delete'); await page.evaluate(() => delValidate());
  await Promise.all([page.waitForEvent('load'), page.click('#delGo')]);
  await page.clock.runFor(3000); await page.waitForTimeout(800);
  ok(st.req && st.req.length === 1 && st.req[0].p_delete_reviews === true && !st.immediate, 'website: asks request_account_deletion(p_delete_reviews: true) — never the immediate delete', st);
  ok(log.writes.some(w => /^storage:/.test(w.table)) && log.writes.some(w => w.table === 'profiles' && w.m === 'PATCH' && w.body && w.body.avatar_url === null), 'website: the photo goes through the Storage API, then the link is cleared');
  const lo = log.writes.find(w => /^auth:logout/.test(w.table));
  ok(lo && /scope=global/.test(lo.query || ''), 'website: every device is signed out', log.writes.filter(w => /^auth:/.test(w.table)));
  const body = await page.locator('body').innerText();
  ok(/scheduled for deletion\. Sign in before Nov 3, 2026 to recover it/.test(body), 'website: the page says until when it can be recovered', body.slice(0, 200));
  ok(log.errors.length === 0, 'website (delete): no page errors', log.errors);
  await close();
}

/* 5. Refused: nothing changes, and it says so */
{
  const st = { reqFail: true };
  const { page, close, log } = await desk({ hook: delHook(st) });
  await tick(page, 1500);
  await page.evaluate(() => openDeleteAccount()); await tick(page, 600);
  await page.fill('#delConfirm', 'DELETE'); await page.evaluate(() => delValidate());
  await page.click('#delGo'); await tick(page, 600);
  ok(!st.immediate && st.req[0].p_delete_reviews === false, 'website: with the switch left on, reviews are kept — and never the immediate delete', st.req);
  ok(st.req.length === 1 && (await page.locator('#delErr').innerText()).length > 0 && !(await page.locator('#delGo').isDisabled()) && !log.writes.some(w => /^storage:|^auth:logout/.test(w.table)), 'website: a refused delete says so, keeps you signed in and touches nothing');
  await close();
}

console.log(`\ncheck-desktop-delete: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
