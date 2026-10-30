/* Round 2 (Nov 4–17, 2026): pick a Round 2 day, see it on the term card, see friends' Round 2 days, Champ says where
   registration stands. Fails on 1658ca4 (every day greyed out from Nov 4, nothing on the card). */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
import { ok, tick, liveTables, FX, done, nextPort } from './lib.mjs';

const R1 = [{ user_id: FX.FRIENDS[1].id, day: '2026-10-21', at_time: '08:00:00' }];
const R2 = [{ user_id: FX.FRIENDS[0].id, day: '2026-11-10' }, { user_id: FX.FRIENDS[1].id, day: '2026-11-12' }, { user_id: FX.FRIENDS[2].id, day: '2026-11-16' },
  { user_id: FX.STRANGER.id, day: '2026-11-12' }];
const open = async (time, extra = {}) => {
  const T = liveTables(); if (extra.tables) extra.tables(T);
  const app = await openApp({ terms: 'live', tables: T, rpc: { ...FX.RPC, friend_registration_days: R1, friend_registration_round2: R2 }, time, height: 1000, port: nextPort() });
  await app.page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 10000 }).catch(() => {});
  await app.page.evaluate(() => { S.tab = 'schedule'; S.schedTab = 'planner'; render(true); }); await tick(app.page, 900);
  return app;
};
const card = page => page.evaluate(() => {
  const l = document.querySelector('#scroll .pla-reg'), f = document.querySelector('#scroll .reg-fr');
  const hd = l && l.querySelector('.pl-tc-h'), sb = l && l.querySelector('.pl-tc-s'), ad = l && l.querySelector('.pla-add');
  const sub = sb ? sb.textContent.split(' · ').filter(x => !/^\d+ units$/.test(x)).join(' · ') : '';
  return { line: l ? [hd ? hd.textContent : '', sub].filter(Boolean).join(' · ') + (ad ? ' ' + ad.textContent.trim() : '') : null, fr: f ? f.innerText.replace(/\s+/g, ' ').trim() : null };
});
const sheet = page => page.evaluate(() => { const s = document.getElementById('sheet'); return { round: (s.querySelector('.rd-h') || {}).textContent || '',
  days: [...s.querySelectorAll('.rd-d')].map(b => b.getAttribute('data-x') + (b.disabled ? '-' : '')), share: (s.querySelector('[data-a="regShareToggle"]') || { getAttribute: () => null }).getAttribute('aria-checked') }; });

{ /* Thursday Nov 5: Round 2 is on */
  const { page, close, log } = await open('2026-11-05T10:00:00-08:00');
  let v = await card(page);
  ok(v.line === 'Round 2 is open · till Nov 17 Add your day', 'round2: no day yet — the term card says Round 2 is open, with Add your day', v);
  ok(v.fr === '3 friends added their day', 'round2: friends’ Round 2 days under it (not a stranger)', v);
  ok(log.rpcs.some(r => r.fn === 'friend_registration_round2' && r.body && r.body.p_term === '2274'), 'round2: friends’ days come from friend_registration_round2 for 2274', log.rpcs.map(r => r.fn));
  await page.evaluate(() => A.regDayOpen()); await tick(page, 300);
  let sh = await sheet(page);
  ok(sh.round === 'Round 2 · Nov 5 – Nov 17', 'round2: the picker is Round 2’s', sh.round);
  ok(sh.days.join(' ') === '2026-11-05 2026-11-06 2026-11-09 2026-11-10 2026-11-11- 2026-11-12 2026-11-13 2026-11-16 2026-11-17', 'round2: Round 2’s weekdays, Veterans Day (Nov 11) greyed out, today’s and later pickable', sh.days);
  await page.evaluate(() => A.regPickDay('2026-11-11')); await tick(page, 100);
  ok(await page.evaluate(() => UI.sheet.day) === '', 'round2: Veterans Day can’t be picked');
  await page.click('#sheet .rd-d[data-x="2026-11-12"]'); await tick(page, 100);
  await page.fill('#rd-time', '09:30');
  await page.click('#sheet [data-a="regDaySave"]'); await tick(page, 1200);
  const w = log.writes.filter(x => x.table === 'registration_round2'), w1 = log.writes.filter(x => x.table === 'registration_days');
  ok(w.length === 1 && w[0].body.day === '2026-11-12' && w[0].body.at_time === '09:30' && w[0].body.term === '2274' && w[0].body.shared === true && /on_conflict=user_id%2Cterm/.test(w[0].query) && !w1.length,
    'round2: Save writes your Round 2 row (registration_round2), not Round 1’s', { w: w.map(x => x.body), w1: w1.length });
  v = await card(page);
  ok(v.line === 'Register Thu, Nov 12, 9:30a · Round 2 · in 7 days', 'round2: the term card shows your Round 2 day', v);
  ok(v.fr === '1 friend before you · 1 same day · 1 after', 'round2: friends counted against your Round 2 day', v);
  const st = await page.evaluate(() => localStorage.getItem('tc-regday2:' + TC.user.id + ':2274'));
  ok(st && JSON.parse(st).day === '2026-11-12', 'round2: this phone keeps it under its own key', st);
  await page.evaluate(id => A.openFriend(id), FX.FRIENDS[0].id); await tick(page, 600);
  const fr = await page.evaluate(() => { const r = document.querySelector('.fpg .regrow'); return r && r.innerText.replace(/\s+/g, ' ').trim(); });
  ok(fr === 'Registers Tue, Nov 10 · 2 days before you', 'round2: a friend’s page shows their Round 2 day (day only)', fr);
  const champ = await page.evaluate(() => answerTool({ tool: 'when_registration', args: {} }, '').t);
  ok(/Round 2/.test(champ) && /November 17/.test(champ) && !/starts Monday, October 19/.test(champ), 'round2: Champ says Round 2 is open until Nov 17 (not “starts October 19”)', champ);
  ok(!log.errors.length, 'round2: no page errors', log.errors);
  await close();
}
{ /* Round 1's "Friends can see your day" off: Round 2 starts off too, and turning it on moves Round 1's */
  const { page, close, log } = await open('2026-11-06T10:00:00-08:00', { tables: T => { T.registration_days = [{ user_id: FX.ME.id, term: '2274', day: '2026-10-22', at_time: '08:00:00', shared: false, updated_at: '2026-10-12T00:00:00Z' }]; } });
  await page.evaluate(() => A.regDayOpen()); await tick(page, 300);
  ok((await sheet(page)).share === 'false', 'round2 share: off when your Round 1 day is hidden from friends');
  await page.click('#sheet .rd-d[data-x="2026-11-09"]'); await page.click('#sheet [data-a="regShareToggle"]'); await page.click('#sheet [data-a="regDaySave"]'); await tick(page, 1200);
  const w = log.writes.filter(x => x.table === 'registration_round2'), w1 = log.writes.filter(x => x.table === 'registration_days');
  ok(w.length === 1 && w[0].body.shared === true && w1.length === 1 && w1[0].body.shared === true && w1[0].body.day === '2026-10-22', 'round2 share: switching it on saves Round 2 and turns Round 1’s on (one switch, as on the website)', { w: w.map(x => x.body), w1: w1.map(x => x.body) });
  await close();
}
{ /* Round 1 is untouched: Oct 21 still Round 1, registration_days */
  const { page, close } = await open('2026-10-21T09:00:00-07:00');
  await page.evaluate(() => A.regDayOpen()); await tick(page, 300);
  const sh = await sheet(page);
  ok(sh.round === 'Round 1 · Oct 19 – Nov 3' && sh.days.length === 12, 'round1: before Nov 4 the picker is still Round 1’s twelve weekdays', sh);
  const champ = await page.evaluate(() => answerTool({ tool: 'when_registration', args: {} }, '').t);
  ok(/Round 1/.test(champ) && /November 3/.test(champ), 'round1: Champ says Round 1 is open until Nov 3', champ);
  await close();
}
{ /* the app left open over midnight Nov 3 → 4 reads Round 2 */
  const { page, close, log } = await open('2026-11-03T23:58:00-08:00');
  await page.clock.runFor(4 * 60000); await page.evaluate(() => render(true)); await tick(page, 1500);
  const v = await card(page);
  ok(v.line === 'Round 2 is open · till Nov 17 Add your day' && log.rpcs.some(r => r.fn === 'friend_registration_round2'), 'rollover: open across midnight Nov 3 → 4, the card and friends move to Round 2', { v, rpcs: log.rpcs.map(r => r.fn) });
  await close();
}
{ /* Open Enrollment (Nov 18): Champ says so */
  const { page, close } = await open('2026-11-20T10:00:00-08:00');
  const champ = await page.evaluate(() => answerTool({ tool: 'when_registration', args: {} }, '').t);
  ok(/Open Enrollment/.test(champ) && !/starts Monday, October 19/.test(champ), 'open enrollment: Champ says Open Enrollment is on', champ);
  await close();
}
done('check-reg-round2');
