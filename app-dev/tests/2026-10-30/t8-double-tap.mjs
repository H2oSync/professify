/* Fix 8: double taps on Accept / Decline send one write; Message twice makes one chat. */
import { openApp, mk, FX } from './tlib.mjs';
const R = mk('t8-double-tap'); const port = +(process.env.APP_PORT || 8669);
const T = JSON.parse(JSON.stringify(FX.TABLES));
const DEC = { id: '33333333-3333-4333-8333-333333333339', display_name: 'Dana Declinee', username: 'ddecline', avatar_url: null, school: 'calpoly' };
T.profiles.push(DEC); T.friend_requests.push({ id: 991, from_user: DEC.id, to_user: FX.ME.id, status: 'pending', created_at: '2026-09-28T00:00:00Z' });
let slowConv = false;
const hook = async (url, m) => { if (slowConv && m === 'POST' && url.pathname === '/rest/v1/conversations') await new Promise(r => setTimeout(r, 600)); if (m !== 'GET' && url.pathname === '/rest/v1/friend_requests') await new Promise(r => setTimeout(r, 400)); return null; };
const { page, close, log } = await openApp({ port, tables: T, hook, time: null });
await page.waitForFunction(() => TC.ready && TC.requests.length === 2, null, { timeout: 15000 }); await page.waitForTimeout(300);
await page.evaluate(() => A.tab('friends')); await page.waitForTimeout(400);
const tap2 = async sel => { const b = await page.evaluate(sel => { const e = [...document.querySelectorAll(sel)].find(x => x.offsetParent); if (!e) return null; e.scrollIntoView({ block: 'center' }); const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }, sel); if (!b) return false; await page.touchscreen.tap(b.x, b.y); await page.touchscreen.tap(b.x, b.y); await page.waitForTimeout(1500); return true; };
R.ok(await tap2('[data-a="acceptReq"]'), 'Accept tapped twice');
R.ok(log.writes.filter(w => w.table === 'friend_requests' && w.m === 'PATCH').length === 1, 'double-tap Accept: one update', log.writes.filter(w => w.table === 'friend_requests').length);
R.ok(await tap2('[data-a="declineReq"]'), 'Decline tapped twice');
R.ok(log.writes.filter(w => w.table === 'friend_requests' && w.m === 'DELETE').length === 1, 'double-tap Decline: one delete', log.writes.filter(w => w.table === 'friend_requests' && w.m === 'DELETE').length);
/* a friend with no direct chat yet: Message twice */
const f = await page.evaluate(() => TC.friends.find(id => !TC.threads.some(t => t.kind === 'direct' && t.members.includes(id))));
R.ok(!!f, '(setup) a friend with no chat yet', f);
slowConv = true;
const ids = await page.evaluate(async id => { A.openFriend(id); const a = A.openChatWith(id), b = A.openChatWith(id); const c = await Promise.all([TC.threadWith(id), TC.threadWith(id)]); await a; await b; return { c, st: S.stack[S.tab].map(e => e.s) }; }, f);
await page.waitForTimeout(800);
R.ok(log.writes.filter(w => w.table === 'conversations' && w.m === 'POST').length === 1 && ids.c[0] && ids.c[0] === ids.c[1], 'Message twice (and two more asks at once): one chat made, the same id for all', { ids, posts: log.writes.filter(w => w.table === 'conversations' && w.m === 'POST').length });
R.ok(ids.st.filter(s => s === 'chat').length === 1, 'the chat is opened once', ids.st);
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
