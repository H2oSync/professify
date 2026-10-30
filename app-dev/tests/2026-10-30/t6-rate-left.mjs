/* Fix 6: leaving the rate form while it posts doesn't turn the page you went back to into Thanks; X is disabled
   while posting; an edit saved after you left doesn't pop the page you're on. */
import { openApp, mk, toastText } from './tlib.mjs';
const R = mk('t6-rate-left'); const port = +(process.env.APP_PORT || 8667);
let slow = false; const revs = []; let nid = 9100;
const hook = async (url, m, body) => {
  const p = url.pathname;
  if (slow && m !== 'GET' && p === '/rest/v1/reviews') await new Promise(r => setTimeout(r, 2000));
  if (p === '/rest/v1/rpc/my_reviews') return { status: 200, body: JSON.stringify(revs) };
  if (p === '/rest/v1/reviews' && m === 'POST') { revs.push(Object.assign({ id: nid++, created_at: new Date().toISOString(), share_with_friends: false }, body)); return { status: 201, body: '' }; }
  if (p === '/rest/v1/reviews' && m === 'PATCH') { const id = +url.searchParams.get('id').slice(3); const r = revs.find(x => x.id === id); if (r) Object.assign(r, body); return { status: 200, body: JSON.stringify(r ? [{ id }] : []) }; }
  return null;
};
const { page, close, log } = await openApp({ port, hook, time: null });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 15000 }); await page.waitForTimeout(400);
const stacks = () => page.evaluate(() => Object.fromEntries(Object.entries(S.stack).map(([k, v]) => [k, v.map(e => e.s).join('>')])));
const pid = await page.evaluate(() => unrated()[0][0]);
await page.evaluate(p => { A.tab('explore'); go('profDetail', { id: p }); A.rateProf(p); if (!S.draft.code) A.draft('code', S.draft.codes[0]); A.draft('stars', 4); }, pid); await page.waitForTimeout(300);
slow = true;
await page.evaluate(() => { A.postRating(); }); await page.waitForTimeout(300);
R.ok(await page.evaluate(() => { const x = document.querySelector('.rf .xbtn[data-a="back"]'); return !!x && x.disabled; }), 'the form’s X is disabled while it posts');
await page.evaluate(() => A.back()); await page.waitForTimeout(2600);
let s = await stacks();
R.ok(s.explore === 'explore>profDetail', 'left while posting: the professor page stays (no Thanks over it)', s.explore);
R.ok(/Rating posted\./.test(await toastText(page)) && revs.length === 1, 'a “Rating posted.” toast instead', await toastText(page));
/* stay on the form: Thanks as before */
slow = false;
const pid2 = await page.evaluate(() => unrated()[0][0]);
await page.evaluate(p => { A.tab('rate'); A.rateProf(p); if (!S.draft.code) A.draft('code', S.draft.codes[0]); A.draft('stars', 3); }, pid2); await page.waitForTimeout(300);
await page.evaluate(() => A.postRating()); await page.waitForTimeout(1200);
R.ok((await stacks()).rate.endsWith('rateThanks'), 'staying on the form: Thanks, as before', (await stacks()).rate);
await page.evaluate(() => A.rateDone()); await page.waitForTimeout(300);
/* switch tabs while it posts: the other tab's page is untouched, the form leaves its stack */
slow = true;
const pid3 = await page.evaluate(() => unrated()[0] && unrated()[0][0]);
if (pid3) {
  await page.evaluate(p => { A.tab('rate'); A.rateProf(p); if (!S.draft.code) A.draft('code', S.draft.codes[0]); A.draft('stars', 5); }, pid3); await page.waitForTimeout(300);
  await page.evaluate(() => { A.postRating(); }); await page.waitForTimeout(200);
  await page.evaluate(() => { A.tab('home'); A.openMyRatings && A.openMyRatings(); }); await page.waitForTimeout(2600);
  s = await stacks();
  R.ok(!/rateThanks/.test(s.home) && !/rateForm|rateThanks/.test(s.rate), 'switched tabs while posting: Home untouched, the posted form is gone from Rate', s);
}
/* an edit saved after leaving the form doesn't pop the page you're on */
await page.evaluate(() => { A.tab('home'); A.openMyRatings(); }); await page.waitForTimeout(800);
await page.evaluate(() => A.editReview(TC.myReviews[0].id)); await page.waitForTimeout(300);
await page.evaluate(() => { A.draft('stars', 2); A.postRating(); }); await page.waitForTimeout(200);
await page.evaluate(() => A.back()); await page.waitForTimeout(2600);
s = await stacks();
R.ok(/myRatings$/.test(s.home), 'edit: left while saving — still on My ratings (not popped further)', s.home);
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
