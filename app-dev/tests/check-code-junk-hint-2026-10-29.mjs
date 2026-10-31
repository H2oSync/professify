/* Tate, 2026-10-29: codes that land in Junk, and a student who tapped Resend four times in 45s (429s).
   Phone app: the code screen says check Junk and names the sender; code log-in waits 60s like sign-up;
   a refused resend counts down from the seconds Supabase names. Website: the same hint, a 60s wait
   (was 45s, and 20s after a failure), and the refused-resend countdown. */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const LIMIT = 'For security purposes, you can only request this after 37 seconds.';
/* ---------- phone app, signed out */
{
  const { page, close, log } = await openApp({ signedIn: false });
  await page.waitForTimeout(1500);
  await page.evaluate(() => { window.__sent = []; TC.sendCode = async (e, c) => { window.__sent.push([e, c]); return window.__next || null; }; });
  /* sign-up → code screen */
  await page.evaluate(() => { Object.assign(UI.signin, { mode: 'signup', email: 'tester@calpoly.edu', pw: 'abcdefgh1', agree: true }); render(); });
  await page.waitForTimeout(300);
  await page.evaluate(() => { const f = document.querySelector('form[data-submit="signup"]'); f.querySelector('#su-email').value = 'tester@calpoly.edu'; f.querySelector('#su-pw').value = 'abcdefgh1'; f.querySelector('#su-agree').checked = true; f.requestSubmit(); });
  await page.waitForTimeout(500);
  const st = await page.evaluate(() => ({ mode: UI.signin.mode, junk: (document.getElementById('junkHint') || {}).textContent || '', resend: document.getElementById('resend').textContent, wait: Math.round((UI.signin.resendAt - Date.now()) / 1000) }));
  ok(st.mode === 'suVerify', 'sign-up opens the code screen', st);
  ok(/Junk/.test(st.junk) && /Spam/.test(st.junk) && /noreply@termchamp\.com/.test(st.junk) && /Your TermChamp code/.test(st.junk), 'it says to check Junk/Spam and names the sender and subject', st.junk);
  ok(/Resend in 0:\d\d/.test(st.resend) && !/button/i.test(await page.evaluate(() => document.getElementById('resend').innerHTML)) && st.wait >= 58, 'Resend is a 60s countdown, not a button', st);
  /* after the countdown, a refused resend counts down from Supabase's number */
  await page.evaluate(lim => { UI.signin.resendAt = Date.now() - 1; window.__next = lim; document.getElementById('resend').innerHTML = onbResendHtml(); }, LIMIT);
  await page.waitForTimeout(1100);
  await page.evaluate(() => document.querySelector('#resend [data-a="suResend"]').click()); await page.waitForTimeout(400);
  const r = await page.evaluate(() => ({ err: UI.signin.err, wait: Math.round((UI.signin.resendAt - Date.now()) / 1000), shown: document.getElementById('codeErr').textContent, resend: document.getElementById('resend').textContent }));
  ok(/wait 37 seconds/.test(r.err) && /Junk/.test(r.err) && !/hourly/.test(r.err), 'a refused resend says "wait 37 seconds … check Junk", not "hourly limit"', r);
  ok(r.wait >= 36 && r.wait <= 38 && /Resend in 0:3\d/.test(r.resend), 'and the Resend countdown restarts from 37s', r);
  /* a good resend */
  await page.evaluate(() => { UI.signin.resendAt = Date.now() - 1; window.__next = null; document.getElementById('resend').innerHTML = onbResendHtml(); });
  await page.evaluate(() => document.querySelector('#resend [data-a="suResend"]').click()); await page.waitForTimeout(400);
  const g = await page.evaluate(() => ({ note: UI.signin.note, wait: Math.round((UI.signin.resendAt - Date.now()) / 1000) }));
  ok(/New code sent/.test(g.note) && /Junk/.test(g.note) && g.wait >= 58, 'a good resend: "New code sent … Check Junk too", 60s again', g);
  /* "Email me a code" log-in waits 60s too */
  await page.evaluate(() => { Object.assign(UI.signin, { mode: 'code', err: '', note: '' }); render(); }); await page.waitForTimeout(300);
  await page.evaluate(() => { const f = document.querySelector('form[data-submit="sendCode"]'); f.querySelector('#si-email').value = 'tester@calpoly.edu'; f.requestSubmit(); }); await page.waitForTimeout(500);
  const c = await page.evaluate(() => ({ mode: UI.signin.mode, wait: Math.round((UI.signin.resendAt - Date.now()) / 1000), junk: !!document.getElementById('junkHint') }));
  ok(c.mode === 'verify' && c.wait >= 58 && c.junk, 'code log-in: 60s wait (was 45s) and the Junk hint', c);
  ok(log.errors.length === 0, 'no page errors (app)', log.errors);
  await close();
}
/* ---------- website */
{
  const { page, close, log } = await openApp({ path: '/', width: 1440, height: 900, wait: 4000, signedIn: false });
  await page.waitForTimeout(1500);
  const w = await page.evaluate(() => { authCodeStep('tester@calpoly.edu'); const b = document.getElementById('authResend'); const j = document.getElementById('authJunk'); return { junk: j ? j.textContent : '', dis: b.disabled, txt: b.textContent }; });
  ok(/Junk/.test(w.junk) && /noreply@termchamp\.com/.test(w.junk), 'website code step: the Junk hint names the sender', w.junk);
  ok(w.dis && /in 60s/.test(w.txt), 'website: Resend waits 60s (was 45s)', w);
  const f = await page.evaluate(async lim => { sb.auth.signInWithOtp = async () => ({ error: { message: lim } }); const b = document.getElementById('authResend'); b.disabled = false; await authResend('tester@calpoly.edu'); return { txt: document.getElementById('authResend').textContent, err: (document.getElementById('authErr') || {}).textContent || '' }; }, LIMIT);
  ok(/in 38s/.test(f.txt), 'website: a refused resend waits the 37s Supabase names (+1), not 20s', f);
  ok(/wait 37 seconds/.test(f.err) && !/hourly/.test(f.err), 'website: and says how long to wait', f.err);
  ok(log.errors.length === 0, 'no page errors (website)', log.errors);
  await close();
}
console.log(`code-junk-hint: ${pass} passed, ${fail} failed`);
