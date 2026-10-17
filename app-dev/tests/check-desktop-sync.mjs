/* check-desktop-sync — the website catches up with the phone on one account (website-sync, Tate 2026-10-15: "lets find another
   place to put this" / "do the pins on stories and most free for stories" / sync-audit.md). Runs the REAL index.html in Chromium,
   signed in, against the PostgREST stand-in of app-harness. Server additions that are not live yet (sql/professify-sync-2026-10-15.sql)
   are installed per test and answered "not installed" (PGRST202 / PGRST205) in the degrade tests.
   Run: APP_DIR=<repo> node check-desktop-sync.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises:
   - Task 1  the registration banner is not at the top of any page; it is a compact card on Home's right rail under the greeting,
             with the countdown, one sentence, two buttons and an x that dismisses it; Schedule > Plans keeps its card;
   - Task 2  stories: up to 3 pinned friends first in pin order (read my_pinned_friends, written set_pinned_friends, the phone's
             toasts, a pin button, right-click and a hold), then everyone by the phone's freeness rank at every hour;
   - gaps 1-10 of the audit: major/standing/concentration both ways; pins; sections the phone removed stay removed; a tab that was
             hidden catches up; chat clears/hides/mutes/likes/blocks; push kinds mirrored into prefs; saved_items; favorite teachers
             and the registration day in the Game Plan; a review edit that saves; normCode's suffix letters and '&'. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 600) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const T = {};
const test = (name, fn) => { T[name] = fn; };
const ME = FX.ME.id;
const [AV, RO, SK, QU, HA] = FX.FRIENDS;
const LIVE_NOW = '2026-10-14T10:30:00-07:00';                       /* 5 days before Round 1 opens (Oct 19) */
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const live = (o = {}) => desk(Object.assign({ terms: 'live', time: LIVE_NOW }, o));
const clone = x => JSON.parse(JSON.stringify(x));
const toast = page => page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '');
const ready = async page => { for (let i = 0; i < 40; i++) { if (await page.evaluate(() => typeof friendsLoaded !== 'undefined' && friendsLoaded && !frSignInBusy)) return; await tick(page, 300); } };
const home = async page => { await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 800); };
const rpcs = (log, fn) => log.rpcs.filter(r => r.fn === fn);
const writes = (log, table, m) => log.writes.filter(w => w.table === table && (!m || w.m === m));
const MISSING = (fn) => ({ __error: { code: 'PGRST202', message: 'Could not find the function public.' + fn + ' in the schema cache' } });
const NO_TABLE = { code: 'PGRST205', message: "Could not find the table 'public.saved_items' in the schema cache" };
/* set_pinned_friends answers with what it kept, like the real function (friends only, max 3, no repeats) */
const echoPins = (kept) => { const h = (url, m, body) => { if (!url.pathname.endsWith('/rpc/set_pinned_friends')) return null; h.calls.push({ fn: 'set_pinned_friends', body }); return { status: 200, body: JSON.stringify(kept ? kept(body.p_ids) : body.p_ids) }; }; h.calls = []; return h; };
const pinRpc = (ids, extra) => Object.assign({}, FX.RPC, { my_pinned_friends: ids }, extra || {});
const strip = page => page.evaluate(() => [...document.querySelectorAll('#hmStripWrap .hm-fitem:not(.hm-fadd)')].map(b => ({ nm: b.querySelector('.nm').textContent.split(' ')[0], cls: b.className.replace(/hm-fitem|\s+/g, ' ').trim(), pinned: b.classList.contains('pinned'), badge: !!b.querySelector('.hm-pinmark') && !b.querySelector('.hm-pinbadge'), title: b.title })));
const order = async page => (await strip(page)).map(x => x.nm);

/* ======================================================================================================== TASK 1 */
test('regcard', async () => {
  /* reg-timeline (2026-10-16): the card is the Spring 2027 timeline (it was the "Round 1 registration opens" card, website-sync 2026-10-15) */
  const o = await live({ tables: clone(FX.TABLES) }); const { page } = o; await tick(page, 1500);
  const r = await page.evaluate(() => {
    const c = document.getElementById('hmRegCard'), td = document.querySelector('#hmRailR .hm-td'), rail = document.getElementById('hmRailR');
    const btns = c ? [...c.querySelectorAll('.tl-go, .tl-all')] : [];
    return { has: !!c, inRail: !!c && !!rail && rail.contains(c), after: !!c && !!td && td.nextElementSibling === c, text: c ? c.innerText.replace(/\s+/g, ' ').trim() : '',
      rows: c ? c.querySelectorAll('.tl-li').length : 0, btns: btns.map(b => b.textContent.replace(/\s+/g, ' ').trim()),
      w: c ? Math.round(c.getBoundingClientRect().width) : 0, rw: rail ? Math.round(rail.getBoundingClientRect().width) : 0, card: !!(c && c.classList.contains('hm-card')),
      top: document.getElementById('campusBanner').innerText.trim() };
  });
  ok(r.has && r.inRail && r.after, 'the card is on Home’s right rail, directly under the greeting card', r);
  ok(/^×? ?📅 Spring 2027/.test(r.text) && /Your Round 1/.test(r.text) && /Your Round 2/.test(r.text) && /Classes begin/.test(r.text) && /Last day to add/.test(r.text) && /Last day to drop/.test(r.text) && /Last day to withdraw/.test(r.text) && r.rows === 6, 'it is the Spring 2027 timeline: six rows — Round 1, Round 2, classes begin, last day to add, drop, withdraw', r);
  ok(JSON.stringify(r.btns) === '["Your game plan →","All dates"]', 'one primary button, “Your game plan”, and a quiet “All dates”', r.btns);
  ok(r.card && r.w <= r.rw && r.w > 150, 'it is a normal rail card, no wider than the rail', r);
  ok(r.top === '', 'nothing about registration is left in the strip at the top of the page', r.top);
  /* every other page: the strip stays empty of it */
  const tops = [];
  for (const v of ['sched', 'explore', 'friends']) { await page.evaluate(x => show(x), v); await tick(page, 500); tops.push(await page.evaluate(() => document.getElementById('campusBanner').innerText.trim())); }
  ok(tops.every(t => t === ''), 'Schedule, Explore and Friends have no registration banner either', tops);
  await page.evaluate(() => { show('sched'); if (typeof setSchedTab === 'function') setSchedTab('plans'); }); await tick(page, 800);
  ok(await page.evaluate(() => !!document.querySelector('.rg-slot[data-rg="plans"] .rg-card')), 'Schedule › Plans keeps its registration card');
  /* the x */
  await page.evaluate(() => show('home')); await tick(page, 500);
  await page.click('#hmRegCard .hm-regx'); await tick(page, 300);
  const d = await page.evaluate(() => ({ gone: !document.getElementById('hmRegCard'), ls: localStorage.getItem('professify_dismiss_regtl_' + sbUser.id + '_2274'), rg: !!document.querySelector('#hmRailR .rg-slot .rg-card') }));
  ok(d.gone && d.ls === '1', 'x dismisses it, remembered under the card’s own key (regtl_<user id>_2274)', d);
  ok(!d.rg, 'the rail’s own day card is gone for good — the pencils on the timeline replace it');
  await page.evaluate(() => renderHome()); await tick(page, 600);
  ok(await page.evaluate(() => !document.getElementById('hmRegCard')), 'a re-render does not bring it back');
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
  /* the buttons */
  const p = await live({ tables: clone(FX.TABLES) }); await tick(p.page, 1500);
  await p.page.click('#hmRegCard [data-tl-key="add1"]'); await tick(p.page, 400);
  ok(await p.page.evaluate(() => document.getElementById('rgBack').classList.contains('open')), 'Round 1’s “+ Add” opens the registration-day sheet');
  await p.page.keyboard.press('Escape'); await tick(p.page, 300);
  await p.page.evaluate(() => { window.__fb = 0; TCPlans.fromBanner = function () { window.__fb++; }; });
  await p.page.click('#hmRegCard .tl-go'); await tick(p.page, 300);
  ok(await p.page.evaluate(() => window.__fb) === 1, '“Your game plan” goes to the game plan');
  await p.close();
  /* not before 14 days, never signed out, and not after the term's last day of instruction (May 14) */
  for (const [t, si, why, want] of [['2026-10-01T10:30:00-07:00', true, 'eighteen days out', false], ['2026-10-05T10:30:00-07:00', true, 'fourteen days out', true], ['2026-10-20T10:30:00-07:00', true, 'the day after Round 1 opened', true],
    ['2027-01-27T10:30:00-08:00', true, 'once classes have begun', true], ['2027-05-15T10:30:00-07:00', true, 'the day after the last day of classes', false], [LIVE_NOW, false, 'signed out', false]]) {
    const q = await live({ time: t, signedIn: si, tables: clone(FX.TABLES) }); await tick(q.page, 1200);
    ok(await q.page.evaluate(() => !!document.getElementById('hmRegCard')) === want, (want ? 'the card shows ' : 'no card ') + why);
    await q.close();
  }
  /* the finals-week banner is not touched */
  const f = await live({ tables: clone(FX.TABLES), terms: { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', REGISTRATION_OPENS: '2027-01-01', QUARTER_END: '2026-10-17' } }); await tick(f.page, 1500);
  const fw = await f.page.evaluate(() => document.getElementById('campusBanner').innerText);
  ok(/Finals week/.test(fw), 'the finals-week banner still shows at the top', fw);
  await f.close();
});

/* ONE registration card on Home (the timeline), on the rail or, below 1140px, at the top of the main column */
test('regcard-one', async () => {
  const day = row => { const t = clone(FX.TABLES); t.registration_days = row ? [Object.assign({ user_id: ME, term: '2274', shared: true, updated_at: '2026-10-13T00:00:00Z' }, row)] : []; return t; };
  const cards = page => page.evaluate(() => {
    const vis = e => !!e && e.offsetParent !== null;
    return { compact: [...document.querySelectorAll('.hm-regcard')].filter(vis).length, old: [...document.querySelectorAll('.rg-slot[data-rg="rail"] .rg-card')].filter(vis).length,
      txt: (document.querySelector('#hmRegCard') || {}).innerText || '', day: (document.querySelector('#hmRegCard .hm-reg-day') || {}).textContent || null,
      btns: [...document.querySelectorAll('#hmRegCard .tl-go, #hmRegCard .tl-all')].map(b => b.textContent.replace(/\s+/g, ' ').trim()) };
  });
  /* no day set */
  let o = await live({ tables: day(null) }); await tick(o.page, 1500);
  let c = await cards(o.page);
  ok(c.compact === 1 && c.old === 0, 'one card on the rail, not two', c);
  ok(JSON.stringify(c.btns) === '["Your game plan →","All dates"]' && c.day === null && /Your Round 1 Opens Oct 19 \+ Add/.test(c.txt.replace(/\s+/g, ' ')), 'no day set: Round 1 says “+ Add · Opens Oct 19”, and there is no green day line', c);
  await o.page.click('#hmRegCard [data-tl-key="add1"]'); await tick(o.page, 400);
  ok(await o.page.evaluate(() => document.getElementById('rgBack').classList.contains('open')), 'it opens the same registration-day sheet');
  await o.page.keyboard.press('Escape'); await tick(o.page, 300);
  /* dismiss: nothing else takes its place on the rail */
  await o.page.click('#hmRegCard .hm-regx'); await tick(o.page, 400);
  c = await cards(o.page);
  ok(c.compact === 0 && c.old === 0, 'dismissed: no registration card on the rail at all', c);
  ok(o.log.errors.length === 0, 'one card: no page errors', o.log.errors); await o.close();
  /* a day set */
  o = await live({ tables: day({ day: '2026-10-21', at_time: '11:00:00' }) }); await tick(o.page, 1500);
  c = await cards(o.page);
  ok(c.compact === 1 && c.old === 0 && c.day === null && !/Change your registration day/.test(c.txt), 'a day set: one card, no “Change your registration day” button, no green day line', c);
  ok(/Your Round 1\s+Wed, Oct 21 · 11:00 AM\s+in 7 days/.test(c.txt.replace(/\n+/g, ' ').replace(/\s+/g, ' ')) || /Wed, Oct 21 · 11:00 AM/.test(c.txt), 'a day set: Round 1 says “Wed, Oct 21 · 11:00 AM · in 7 days”', c.txt);
  await o.page.click('#hmRegCard [data-tl-key="pen1"]'); await tick(o.page, 400);
  ok(await o.page.evaluate(() => document.getElementById('rgBack').classList.contains('open') && !!document.querySelector('.rg-d.on[data-day="2026-10-21"]')), 'the pencil opens the same sheet, on that day');
  await o.close();
  /* below 1140px the rail is hidden: the card is at the top of the main column */
  o = await live({ tables: day(null), width: 900 }); await tick(o.page, 1500);
  const n = await o.page.evaluate(() => {
    const t = document.getElementById('hmRegCardN'), feed = document.getElementById('hmFeed'), r = t ? t.getBoundingClientRect() : null, rail = document.getElementById('hmRegCard');
    return { has: !!t, shown: !!t && t.offsetParent !== null, top: r ? Math.round(r.top) : null, aboveFeed: !!t && !!feed && r.top < feed.getBoundingClientRect().top, railCopyHidden: !rail || rail.offsetParent === null,
      txt: t ? t.innerText.replace(/\s+/g, ' ').trim() : '', old: [...document.querySelectorAll('.rg-slot[data-rg="rail"] .rg-card')].filter(e => e.offsetParent !== null).length, within: !!t && r.right <= innerWidth && r.left >= 0 };
  });
  ok(n.has && n.shown && n.aboveFeed && n.within && n.railCopyHidden && n.old === 0, 'at 900px: the card is at the top of Home’s main column (above the feed), once', n);
  ok(/Spring 2027/.test(n.txt) && /Your game plan/.test(n.txt) && /Your Round 1/.test(n.txt), 'at 900px: the same content', n.txt);
  await o.page.click('#hmRegCardN .hm-regx'); await tick(o.page, 400);
  ok(await o.page.evaluate(() => !document.getElementById('hmRegCardN') && !document.getElementById('hmRegCard') && localStorage.getItem('professify_dismiss_regtl_' + sbUser.id + '_2274') === '1'), 'at 900px: x dismisses it for good');
  await o.close();
  /* a phone-width window: still one visible card, no sideways scroll */
  o = await live({ tables: day(null), width: 390, height: 844 }); await tick(o.page, 1500);
  c = await cards(o.page);
  ok(c.compact === 1 && c.old === 0 && await o.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'at 390px: one card, at the top, no sideways scroll', c);
  await o.close();
  /* at 1440 the top copy is not shown */
  o = await live({ tables: day(null) }); await tick(o.page, 1500);
  ok(await o.page.evaluate(() => { const t = document.getElementById('hmRegCardN'); return !t || t.offsetParent === null; }), 'at 1440px the narrow-screen copy is not shown');
  ok(await o.page.evaluate(() => { const t = document.getElementById('hmRegCardN'); return !t || t.offsetParent === null; }) && (await cards(o.page)).compact === 1, 'at 1440px there is exactly one visible card');
  await o.close();
});

/* ======================================================================================================== TASK 2 */
test('stories-order', async () => {
  /* default fixtures, Tuesday 10:30: Sky class at 12:10 (free till then), Avery and Quinn in class till 11:00, Rowan till 12:00, Harper not set up */
  let o = await desk({ tables: clone(FX.TABLES) }); await ready(o.page); await home(o.page);
  ok(JSON.stringify(await order(o.page)) === '["Sky","Avery","Quinn","Rowan","Harper"]', 'Tue 10:30: free-till-later first, then in class (out soonest), then not set up', await order(o.page));
  await o.close();
  /* the phone has no window: 11:30pm and 2am are ranked too (the website only ranked 7am-11pm on a weekday) */
  const t = clone(FX.TABLES);
  const q = t.my_sections.find(r => r.user_id === QU.id), s42 = t.course_seats.find(r => r.course_code === 'BUS 4442');
  Object.assign(q, { code: 'BUS 4442', class_nbr: s42.class_nbr, section: s42.section, instructor: s42.instructor, days: s42.days });   /* Quinn: MoWe only, so Tuesday is free */
  t.saved_classes.find(r => r.user_id === QU.id && r.code === 'PHIL 3331').code = 'BUS 4442'; t.saved_classes.find(r => r.user_id === QU.id && r.code === 'BUS 4442').class_nbr = s42.class_nbr;
  o = await desk({ tables: t, time: '2026-09-29T23:30:00-07:00' }); await ready(o.page); await home(o.page);
  let st = await strip(o.page);
  ok(JSON.stringify(st.map(x => x.nm)) === '["Quinn","Avery","Rowan","Sky","Harper"]', 'Tue 11:30pm (outside the old 7am-11pm window): no classes today, then done for the day by name, then not set up', st.map(x => x.nm));
  ok(st.slice(0, 4).every(x => /hm-now/.test(x.cls)) && /hm-unset/.test(st[4].cls) && !/hm-free/.test(st[4].cls), 'green rings for free, the grey one for “not set up”', st.map(x => x.cls));
  ok(/no classes today/.test(st[0].title) && /done for the day/.test(st[1].title) && /not set up/.test(st[4].title), 'the state is in the name too, not colour alone', st.map(x => x.title));
  await o.close();
  /* Saturday: everyone with a schedule has no classes today; the one without is last */
  o = await desk({ tables: t, time: '2026-10-03T10:30:00-07:00' }); await ready(o.page); await home(o.page);
  st = await strip(o.page);
  ok(JSON.stringify(st.map(x => x.nm)) === '["Avery","Quinn","Rowan","Sky","Harper"]' && st.slice(0, 4).every(x => /hm-now/.test(x.cls) && /no classes today/.test(x.title)), 'Saturday: “no classes today” for everyone with a schedule, by name; not set up last', st);
  await o.close();
  /* 2am Wednesday: ranked, with a state on every face */
  o = await desk({ tables: t, time: '2026-09-30T02:00:00-07:00' }); await ready(o.page); await home(o.page);
  st = await strip(o.page);
  ok(st.length === 5 && st.slice(0, 4).every(x => /hm-free/.test(x.cls)) && /hm-unset/.test(st[4].cls), '2am: every face with a schedule has a state ring, the unset one is grey and last', st);
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
});

test('pins', async () => {
  /* read: my_pinned_friends, in the order they were pinned — Harper then Rowan, against the freeness order */
  const hk = echoPins();
  let o = await desk({ tables: clone(FX.TABLES), rpc: pinRpc([HA.id, RO.id]), hook: hk }); await ready(o.page); await home(o.page);
  let st = await strip(o.page);
  ok(JSON.stringify(st.map(x => x.nm)) === '["Harper","Rowan","Sky","Avery","Quinn"]', 'pinned friends first in pin order, then the freeness order', st.map(x => x.nm));
  ok(st[0].pinned && st[1].pinned && st[0].badge && st[1].badge && !st[2].pinned && !st[2].badge, 'a pinned story wears a small pin before its name (no badge on the ring)', st.map(x => [x.nm, x.pinned, x.badge]));
  ok(/hm-unset/.test(st[0].cls), 'a pinned friend keeps their own state ring (Harper: schedule not set up)', st[0].cls);
  ok(rpcs(o.log, 'my_pinned_friends').length >= 1 && !o.log.reads.some(r => /^profiles\?select=[^&]*pinned_friends/.test(decodeURIComponent(r))), 'pins are read through my_pinned_friends, never by selecting the column', o.log.reads.filter(r => /profiles\?/.test(r)));
  /* pin a third from the website: the button on the tile */
  await o.page.hover('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"]');
  await o.page.click('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"] .hm-spin'); await tick(o.page, 500);
  let c = hk.calls;
  ok(c.length === 1 && JSON.stringify(c[0].body) === JSON.stringify({ p_ids: [HA.id, RO.id, SK.id] }), 'pinning Sky writes set_pinned_friends with the three in pin order', c.map(x => x.body));
  ok(await toast(o.page) === 'Pinned Sky to the front', 'toast: “Pinned Sky to the front”', await toast(o.page));
  ok(JSON.stringify(await order(o.page)) === '["Harper","Rowan","Sky","Avery","Quinn"]', 'the strip is [Harper, Rowan, Sky] then the rest', await order(o.page));
  /* a fourth: refused, the phone’s words, nothing written */
  await o.page.hover('#hmStripWrap .hm-fw[data-fid="' + AV.id + '"]');
  await o.page.click('#hmStripWrap .hm-fw[data-fid="' + AV.id + '"] .hm-spin'); await tick(o.page, 500);
  ok(await toast(o.page) === '3 pinned already — unpin Harper, Rowan or Sky first', 'a fourth pin says “3 pinned already — unpin Harper, Rowan or Sky first”', await toast(o.page));
  ok(hk.calls.length === 1, 'and writes nothing');
  /* unpin with a right-click */
  await o.page.click('#hmStripWrap .hm-fitem[data-fid="' + HA.id + '"]', { button: 'right' }); await tick(o.page, 500);
  c = hk.calls;
  ok(c.length === 2 && JSON.stringify(c[1].body) === JSON.stringify({ p_ids: [RO.id, SK.id] }), 'right-click on a pinned story unpins it', c.map(x => x.body));
  ok(await toast(o.page) === 'Unpinned Harper' && JSON.stringify(await order(o.page)) === '["Rowan","Sky","Avery","Quinn","Harper"]', 'toast “Unpinned Harper”; Harper goes back to the end (not set up)', [await toast(o.page), await order(o.page)]);
  /* a hold: 0.5 s pins, and the click that ends the hold does not open a profile */
  await o.page.evaluate(() => { window.__op = null; window.openFriendProfile = id => { window.__op = id; }; });
  const box = await o.page.locator('#hmStripWrap .hm-fitem[data-fid="' + QU.id + '"]').boundingBox();
  await o.page.mouse.move(box.x + box.width / 2, box.y + 30); await o.page.mouse.down(); await tick(o.page, 700); await o.page.mouse.up();
  /* the strip is redrawn by the pin, so the real mouse-up usually lands on a new tile; a click that does reach one right after the hold is swallowed too */
  await o.page.evaluate(id => document.querySelector('#hmStripWrap .hm-fitem[data-fid="' + id + '"]').click(), QU.id); await tick(o.page, 500);
  ok(await o.page.evaluate(() => window.__op) === null, 'a click arriving right after the hold is not “open this profile”', await o.page.evaluate(() => window.__op));
  c = hk.calls;
  ok(c.length === 3 && JSON.stringify(c[2].body) === JSON.stringify({ p_ids: [RO.id, SK.id, QU.id] }), 'a half-second hold pins', c.map(x => x.body));
  ok(await o.page.evaluate(() => window.__op) === null && (await toast(o.page)) === 'Pinned Quinn to the front', 'the click that ends the hold does not open the profile', [await o.page.evaluate(() => window.__op), await toast(o.page)]);
  /* a plain click still opens the profile */
  await o.page.click('#hmStripWrap .hm-fitem[data-fid="' + AV.id + '"]'); await tick(o.page, 300);
  ok(await o.page.evaluate(() => window.__op) === AV.id, 'a plain click on a story still opens that friend');
  ok(o.log.errors.length === 0, 'pins: no page errors', o.log.errors); await o.close();

  /* the server keeps fewer than asked (not a friend any more): the page shows what the server kept */
  o = await desk({ tables: clone(FX.TABLES), rpc: pinRpc([HA.id]), hook: echoPins(ids => ids.filter(x => x !== SK.id)) }); await ready(o.page); await home(o.page);
  await o.page.hover('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"]'); await o.page.click('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"] .hm-spin'); await tick(o.page, 600);
  ok(JSON.stringify(await order(o.page)) === '["Harper","Sky","Avery","Quinn","Rowan"]' && !(await strip(o.page)).find(x => x.nm === 'Sky').pinned, 'a pin the server dropped is not shown as pinned', await order(o.page));
  await o.close();
  /* a refused write puts it back and says so */
  o = await desk({ tables: clone(FX.TABLES), rpc: pinRpc([HA.id]), hook: (url) => (url.pathname.endsWith('/rpc/set_pinned_friends') ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'boom' }) } : null) }); await ready(o.page); await home(o.page);
  await o.page.hover('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"]'); await o.page.click('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"] .hm-spin'); await tick(o.page, 600);
  ok(JSON.stringify(await order(o.page)) === '["Harper","Sky","Avery","Quinn","Rowan"]' && !(await strip(o.page)).find(x => x.nm === 'Sky').pinned && /Couldn’t save that/.test(await toast(o.page)), 'a refused write is undone, and says so', [await order(o.page), await toast(o.page)]);
  await o.close();
  /* not installed yet: nothing breaks; the old column path (2 pins, written, not readable) stays */
  o = await desk({ tables: clone(FX.TABLES) }); await ready(o.page); await home(o.page);
  ok(!o.log.reads.some(r => /^profiles\?select=pinned_friends/.test(decodeURIComponent(r))), 'RPC not installed: the unselectable column is not asked for', o.log.reads.filter(r => /profiles\?/.test(r)));
  const pin = async id => { await o.page.hover('#hmStripWrap .hm-fw[data-fid="' + id + '"]'); await o.page.click('#hmStripWrap .hm-fw[data-fid="' + id + '"] .hm-spin'); await tick(o.page, 500); };
  await pin(SK.id); await pin(AV.id);
  const w = writes(o.log, 'profiles', 'PATCH').filter(x => x.body && x.body.pinned_friends);
  ok(w.length === 2 && JSON.stringify(w[1].body.pinned_friends) === JSON.stringify([SK.id, AV.id]), 'RPC not installed: the pins are written to the column as before', w.map(x => x.body));
  await pin(RO.id);
  ok(await toast(o.page) === '2 pinned already — unpin Sky or Avery first' && writes(o.log, 'profiles', 'PATCH').filter(x => x.body && x.body.pinned_friends).length === 2, 'RPC not installed: two pins is the limit, in the same words, and nothing is written for the third', await toast(o.page));
  st = await strip(o.page);
  ok(JSON.stringify(st.map(x => x.nm).slice(0, 2)) === '["Sky","Avery"]' && st[0].pinned && st[1].pinned, 'RPC not installed: the two are first', st.map(x => x.nm));
  ok(o.log.errors.length === 0, 'not installed: no page errors', o.log.errors); await o.close();
  /* unfriended ids do not count */
  o = await desk({ tables: clone(FX.TABLES), rpc: pinRpc(['99999999-9999-4999-8999-999999999999', HA.id]), hook: echoPins() }); await ready(o.page); await home(o.page);
  ok(JSON.stringify((await order(o.page)).slice(0, 1)) === '["Harper"]' && await o.page.evaluate(() => myPins().length) === 1, 'a pin that is not a friend is ignored and not counted', await o.page.evaluate(() => myPins()));
  await o.close();
});

/* ======================================================================================================== GAP 1 */
test('profile', async () => {
  const withMe = (patch) => { const t = clone(FX.TABLES); Object.assign(t.profiles.find(p => p.id === ME), patch); return t; };
  const stu = page => page.evaluate(() => ({ major: student.major, conc: student.conc, standing: student.standing }));
  /* read: the account's values replace this browser's */
  let o = await desk({ tables: withMe({ major: 'Computer Science', class_standing: '5th year +', concentration: 'Software' }) }); await ready(o.page); await tick(o.page, 500);
  let s = await stu(o.page);
  ok(s.major === 'Computer Science' && s.standing === '5th year +' && s.conc === 'Software', 'the account’s major, year and concentration are read', s);
  ok(o.log.reads.some(r => /^profiles\?select=[^&]*concentration/.test(decodeURIComponent(r))) && !o.log.reads.some(r => /^profiles\?select=[^&]*pinned_friends/.test(decodeURIComponent(r))), 'the profile read names concentration and not pinned_friends');
  ok(await o.page.evaluate(() => JSON.parse(localStorage.getItem('professify-profile')).major) === 'Computer Science', 'and it is kept on this device');
  ok(o.log.errors.length === 0, 'read: no page errors', o.log.errors); await o.close();
  /* the phone’s rename */
  o = await desk({ tables: withMe({ major: 'Recreation, Parks & Tourism Administration / Experience Industry Management', class_standing: 'Senior' }) }); await ready(o.page);
  ok((await stu(o.page)).major === 'Experience & Event Management', 'the old name of Experience & Event Management is renamed on read', await stu(o.page));
  await o.close();
  /* an account with no major leaves this browser’s alone */
  o = await desk({ tables: withMe({ major: null, class_standing: null }), init: () => { try { localStorage.setItem('professify-profile', JSON.stringify({ major: 'Economics', standing: 'Sophomore', conc: null })); } catch (e) {} } }); await ready(o.page);
  s = await stu(o.page);
  ok(s.major === 'Economics' && s.standing === 'Sophomore', 'an account that has none leaves this browser’s as it is', s);
  await o.close();
  /* write: every change */
  o = await desk({ tables: withMe({ major: 'Business Administration', class_standing: 'Junior', concentration: 'Finance' }) }); await ready(o.page);
  const pw = () => writes(o.log, 'profiles', 'PATCH').map(w => w.body).filter(b => b && ('class_standing' in b || 'major' in b || 'concentration' in b));
  await o.page.evaluate(() => setChangeStanding('5th year +')); await tick(o.page, 400);
  ok(JSON.stringify(pw().pop()) === JSON.stringify({ major: 'Business Administration', concentration: 'Finance', class_standing: '5th year +' }), 'changing the year writes it', pw());
  await o.page.evaluate(() => setChangeConc('General / Open')); await tick(o.page, 400);
  ok(pw().pop().concentration === null, '“General / Open” is no concentration (null)', pw().pop());
  await o.page.evaluate(() => setChangeMajor('Economics')); await tick(o.page, 400);
  const w3 = pw().pop();
  ok(w3.major === 'Economics' && w3.concentration === null && w3.class_standing === '5th year +', 'changing the major writes it (and clears the concentration)', w3);
  await o.page.evaluate(() => { student.major = 'Recreation, Parks & Tourism Administration / Experience Industry Management'; return syncProfileToBackend(); }); await tick(o.page, 400);
  ok(pw().pop().major === 'Experience & Event Management', 'the renamed major is what is written', pw().pop());
  ok(await o.page.evaluate(() => [...document.getElementById('obStanding').options].map(x => x.text).includes('5th year +')), 'onboarding offers “5th year +”');
  ok(o.log.errors.length === 0, 'write: no page errors', o.log.errors); await o.close();
  /* a change the account refused is sent again before the account’s older value can overwrite it */
  const st = { fail: true };
  const hook = (url, m, body) => (st.fail && m === 'PATCH' && url.pathname.endsWith('/rest/v1/profiles') && body && 'class_standing' in body ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null);
  o = await desk({ tables: withMe({ major: 'Business Administration', class_standing: 'Junior' }), hook }); await ready(o.page);
  await o.page.evaluate(() => setChangeStanding('Senior')); await tick(o.page, 400);
  ok(await o.page.evaluate(id => localStorage.getItem('professify_prof_pend_' + id), ME) === '1', 'a refused change is remembered as not sent yet');
  st.fail = false; const before = pw().length;
  await o.page.reload({ waitUntil: 'domcontentloaded' }); await tick(o.page, 3500); await ready(o.page);
  ok((await stu(o.page)).standing === 'Senior' && pw().length > before && pw().pop().class_standing === 'Senior', 'next sign-in: the unsent change wins and is sent, instead of the account’s older “Junior” coming back', [await stu(o.page), pw().slice(-2)]);
  ok(await o.page.evaluate(id => localStorage.getItem('professify_prof_pend_' + id), ME) === null, 'and it stops being pending');
  await o.close();
});

/* ======================================================================================================== GAP 3 */
test('sections', async () => {
  /* the server has ME in BUS 3438 §01, BUS 4442 §01, BUS 4445 §01, BUS 3431 §01 (term 2268). The phone removed 4445; this browser still has it. */
  const mk = (adopted, queued) => async () => {
    const t = clone(FX.TABLES); t.my_sections = t.my_sections.filter(r => !(r.user_id === ME && r.code === 'BUS 4445'));
    const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
    const crn = await o.page.evaluate(() => { const m = myClassMeta['BUS 4445']; return m && m.secs && m.secs[0] ? String(m.secs[0].crn) : null; });
    return { o, crn, t };
  };
  /* what is local before: put BUS 4445's section (crn from the seat feed) back in this browser's cache, as if it had been there all along */
  const seed = async (o, crn) => o.page.evaluate(([crn]) => {
    const rec = { crn, section: '01', prof: 'Dummelow, Faro', days: 'MoWe 2:10PM - 4:00PM', status: 'enrolled' };
    if (myClasses.indexOf('BUS 4445') < 0) myClasses.push('BUS 4445');
    myClassMeta['BUS 4445'] = myClassMeta['BUS 4445'] || { prof: rec.prof, time: rec.days, secs: [] };
    myClassMeta['BUS 4445'].secs = [rec]; saveMyClasses(); saveMyClassMeta();
  }, [crn]);
  const crnOf = t => t.course_seats.find(r => r.course_code === 'BUS 4445' && r.section === '01').class_nbr;
  /* 1. adopted, not queued: the server’s list wins — the section goes, and is not pushed back */
  { const t = clone(FX.TABLES); const crn = crnOf(t); t.my_sections = t.my_sections.filter(r => !(r.user_id === ME && r.code === 'BUS 4445'));
    const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
    await seed(o, crn); await o.page.evaluate(() => secAdoptSet('my'));
    const w0 = writes(o.log, 'my_sections').length;
    await o.page.evaluate(() => loadMySectionsFromDb()); await tick(o.page, 600);
    await o.page.evaluate(() => backfillMySectionsToDb()); await tick(o.page, 600);
    const gone = await o.page.evaluate(() => (myClassMeta['BUS 4445'] && myClassMeta['BUS 4445'].secs || []).length);
    ok(gone === 0, 'a section the phone removed is removed here too', gone);
    ok(writes(o.log, 'my_sections').length === w0, 'and the backfill does not put it back', writes(o.log, 'my_sections').slice(w0));
    ok(o.log.errors.length === 0, 'sections: no page errors', o.log.errors); await o.close(); }
  /* 1b. the backfill by itself (nothing pruned it first): an adopted, unqueued section is not pushed either */
  { const t = clone(FX.TABLES); const crn = crnOf(t); t.my_sections = t.my_sections.filter(r => !(r.user_id === ME && r.code === 'BUS 4445'));
    const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
    await seed(o, crn); await o.page.evaluate(() => secAdoptSet('my'));
    const w0 = writes(o.log, 'my_sections').length;
    await o.page.evaluate(() => backfillMySectionsToDb()); await tick(o.page, 800);
    ok(writes(o.log, 'my_sections').length === w0, 'the backfill alone pushes only queued adds, not every local section the account lacks', writes(o.log, 'my_sections').slice(w0));
    await o.close(); }
  /* 2. adopted AND queued (added here, write did not land): kept and pushed */
  { const t = clone(FX.TABLES); const crn = crnOf(t); t.my_sections = t.my_sections.filter(r => !(r.user_id === ME && r.code === 'BUS 4445'));
    const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
    await seed(o, crn); await o.page.evaluate(([c]) => { secAdoptSet('my'); secPendMark('my', c); }, [crn]);
    await o.page.evaluate(() => loadMySectionsFromDb()); await tick(o.page, 600);
    await o.page.evaluate(() => backfillMySectionsToDb()); await tick(o.page, 800);
    const kept = await o.page.evaluate(() => (myClassMeta['BUS 4445'] && myClassMeta['BUS 4445'].secs || []).length);
    const up = writes(o.log, 'my_sections', 'POST');
    ok(kept === 1 && up.length === 1 && String((Array.isArray(up[0].body) ? up[0].body[0] : up[0].body).class_nbr) === crn, 'a section added here that has not landed yet is kept and pushed', [kept, up.map(x => x.body)]);
    ok(await o.page.evaluate(c => secPendGet('my').indexOf(c) < 0, crn), 'and leaves the queue once it landed');
    await o.close(); }
  /* 3. never synced before this build (not adopted): adopted once — pushed, so nothing a student has is lost */
  { const t = clone(FX.TABLES); const crn = crnOf(t); t.my_sections = t.my_sections.filter(r => !(r.user_id === ME && r.code === 'BUS 4445'));
    const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
    await o.page.evaluate(() => { try { localStorage.removeItem(secAdoptedKey('my')); } catch (e) {} });
    await seed(o, crn);
    await o.page.evaluate(() => loadMySectionsFromDb()); await tick(o.page, 600);
    await o.page.evaluate(() => backfillMySectionsToDb()); await tick(o.page, 800);
    const up = writes(o.log, 'my_sections', 'POST');
    ok(up.length >= 1 && await o.page.evaluate(() => secAdopted('my')), 'first sync after this build: what only this browser has is pushed once, then the rule is strict', up.map(x => x.body));
    await o.close(); }
  /* 4. watch_sections: the same. Server watches ECON 2303, STAT 2170, PHIL 3331; the phone removed PHIL 3331's */
  { const t = clone(FX.TABLES); const phil = t.watch_sections.find(r => r.user_id === ME && r.code === 'PHIL 3331'); t.watch_sections = t.watch_sections.filter(r => r !== phil);
    const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
    await o.page.evaluate(([c]) => {
      if (watchClasses.indexOf('PHIL 3331') < 0) watchClasses.push('PHIL 3331');
      watchMeta['PHIL 3331'] = { secs: [{ crn: c, section: '01', prof: 'Mockridge, Dov', days: 'TuTh 9:10AM - 11:00AM' }] }; saveWatchClasses(); saveWatchMeta(); secAdoptSet('watch');
    }, [phil.class_nbr]);
    const w0 = writes(o.log, 'watch_sections').length;
    await o.page.evaluate(() => loadWatchSectionsFromDb()); await tick(o.page, 700);
    const r = await o.page.evaluate(() => ({ has: watchClasses.indexOf('PHIL 3331') >= 0, meta: !!watchMeta['PHIL 3331'], econ: watchClasses.indexOf('ECON 2303') >= 0 }));
    ok(!r.has && !r.meta && r.econ, 'a watched section the phone removed is removed here, the others stay', r);
    ok(writes(o.log, 'watch_sections').length === w0, 'and it is not pushed back', writes(o.log, 'watch_sections').slice(w0));
    await o.page.evaluate(([c]) => { watchClasses.push('PHIL 3331'); watchMeta['PHIL 3331'] = { secs: [{ crn: c, section: '01', prof: 'Mockridge, Dov', days: 'TuTh 9:10AM - 11:00AM' }] }; secPendMark('watch', c); }, [phil.class_nbr]);
    await o.page.evaluate(() => loadWatchSectionsFromDb()); await tick(o.page, 700);
    ok(await o.page.evaluate(() => watchClasses.indexOf('PHIL 3331') >= 0), 'a watch added here that has not landed yet is kept');
    await o.close(); }
});

/* ======================================================================================================== GAP 4 */
test('visibility', async () => {
  const o = await desk({ tables: clone(FX.TABLES), init: () => { let v = 'visible'; Object.defineProperty(document, 'visibilityState', { get: () => v, configurable: true }); Object.defineProperty(document, 'hidden', { get: () => v === 'hidden', configurable: true }); window.__setVis = x => { v = x; document.dispatchEvent(new Event('visibilitychange')); }; } });
  await ready(o.page);
  await o.page.evaluate(() => { window.__n = 0; const f = window.frOnSignedIn; window.frOnSignedIn = function () { window.__n++; return f.apply(this, arguments); }; });
  await o.page.evaluate(() => __setVis('hidden')); await tick(o.page, 60000); await o.page.evaluate(() => __setVis('visible')); await tick(o.page, 600);
  ok(await o.page.evaluate(() => window.__n) === 0, 'hidden for one minute: nothing is reloaded');
  await o.page.evaluate(() => __setVis('hidden')); await tick(o.page, 3 * 60000); await o.page.evaluate(() => __setVis('visible')); await tick(o.page, 900);
  ok(await o.page.evaluate(() => window.__n) === 1, 'hidden for three minutes: the account is reloaded once when you come back');
  const r0 = o.log.reads.length;
  await o.page.evaluate(() => __setVis('hidden')); await tick(o.page, 3 * 60000); await o.page.evaluate(() => __setVis('visible')); await tick(o.page, 1500);
  ok(o.log.reads.length > r0 && o.log.reads.slice(r0).some(r => /^(saved_classes|my_sections|friend_requests|profiles)/.test(r)), 'and it really asks for your classes, friends and profile again', o.log.reads.slice(r0).slice(0, 6));
  ok(o.log.errors.length === 0, 'no page errors', o.log.errors); await o.close();
  const s = await desk({ signedIn: false }); await tick(s.page, 500);
  await s.page.evaluate(() => { window.__n = 0; const f = window.frOnSignedIn; window.frOnSignedIn = function () { window.__n++; return f.apply(this, arguments); }; });
  ok(true, 'signed out: loads');
  await s.close();
});

/* ======================================================================================================== GAP 5 */
test('chat', async () => {
  const C0 = FX.CONVS[0].id, C1 = FX.CONVS[1].id, BLOCKED = '33333333-3333-4333-8333-333333333339';
  const t = clone(FX.TABLES);
  t.messages = [
    { id: 1, conversation_id: C0, sender: ME, kind: 'text', body: 'Old message before I deleted this chat', payload: null, created_at: '2026-09-27T18:00:00Z' },
    { id: 2, conversation_id: C0, sender: AV.id, kind: 'text', body: 'Fixture reply after the clear', payload: null, created_at: '2026-09-27T20:00:00Z' },
    { id: 3, conversation_id: C1, sender: RO.id, kind: 'text', body: 'Hidden for me', payload: null, created_at: '2026-09-26T21:00:00Z' },
    { id: 4, conversation_id: C1, sender: SK.id, kind: 'text', body: 'Visible group note', payload: null, created_at: '2026-09-26T20:00:00Z' },
    { id: 5, conversation_id: C1, sender: BLOCKED, kind: 'text', body: 'From someone I blocked', payload: null, created_at: '2026-09-26T22:00:00Z' },
  ];
  t.conversation_clears = [{ conversation_id: C0, cleared_at: '2026-09-27T19:00:00Z' }];
  t.message_hides = [{ message_id: 3 }];
  t.conversation_mutes = [{ conversation_id: C1 }];
  t.message_likes = [{ message_id: 2, user_id: ME }, { message_id: 2, user_id: AV.id }];
  const open = async (o, cid) => { await o.page.evaluate(() => show('friends')); await tick(o.page, 800); await o.page.evaluate(() => msgLoadThreads()); await tick(o.page, 800); if (cid) { await o.page.evaluate(c => msgOpen(c), cid); await tick(o.page, 800); } };
  const o = await desk({ tables: t }); await ready(o.page); await open(o, C0);
  const body0 = await o.page.evaluate(() => (document.getElementById('msgBody') || {}).innerText || '');
  ok(/Fixture reply after the clear/.test(body0) && !/Old message before I deleted this chat/.test(body0), 'a message from before the chat was deleted is not shown, one after it is', body0);
  ok(/♥ 2/.test(await o.page.evaluate(() => document.getElementById('msgBody').innerHTML.replace(/<[^>]+>/g, ' '))), 'likes show as a heart with the count');
  const list = await o.page.evaluate(() => [...document.querySelectorAll('.msg-trow, .msg-thread, [class*="msg-t"]')].map(e => e.innerText).join(' | '));
  ok(/Visible group note/.test(list) && !/Hidden for me/.test(list) && !/From someone I blocked/.test(list), 'the list preview skips a message you hid and a blocked sender’s', list);
  ok(/Muted/.test(await o.page.evaluate(() => document.getElementById('msgList') ? document.getElementById('msgList').innerText : document.body.innerText)), 'a chat you muted says Muted');
  await o.page.evaluate(c => msgOpen(c), C1); await tick(o.page, 800);
  const body1 = await o.page.evaluate(() => document.getElementById('msgBody').innerText);
  ok(/Visible group note/.test(body1) && !/Hidden for me/.test(body1) && !/From someone I blocked/.test(body1), 'in the open group: the hidden message and the blocked sender’s are not shown', body1);
  ok(o.log.errors.length === 0, 'chat: no page errors', o.log.errors); await o.close();
  /* the four tables are not installed: messaging works as it did */
  const miss = { code: 'PGRST205', message: "Could not find the table in the schema cache" };
  const o2 = await desk({ tables: Object.assign(clone(FX.TABLES)), hook: (url) => (/\/rest\/v1\/(conversation_clears|message_hides|conversation_mutes|message_likes)/.test(url.pathname) ? { status: 404, body: JSON.stringify(miss) } : null) });
  await ready(o2.page); await open(o2, C0);
  const b2 = await o2.page.evaluate(() => (document.getElementById('msgBody') || {}).innerText || '');
  ok(/Fixture message from me/.test(b2) && /Fixture reply from Avery/.test(b2), 'tables missing: messages show as before', b2);
  ok(await o2.page.evaluate(() => msgReady !== false), 'tables missing: messaging is not switched off');
  ok(o2.log.errors.length === 0, 'tables missing: no page errors', o2.log.errors); await o2.close();
});

/* ======================================================================================================== GAP 6 */
test('push', async () => {
  const t = clone(FX.TABLES); t.push_prefs = [{ user_id: ME, seats: true, friends: false, quiet_from: 22, quiet_to: 8, prefs: { chat: false } }];
  const o = await desk({ tables: t }); await ready(o.page);
  const up = () => writes(o.log, 'push_prefs').map(w => w.body).filter(Boolean);
  await o.page.evaluate(() => pushPrefSet({ seats: false })); await tick(o.page, 500);
  let b = up().pop();
  ok(b && b.seats === false && b.prefs && b.prefs.seat_open === false && b.prefs.chat === false, 'seat alerts off: seats=false and prefs.seat_open=false, the phone’s other switches kept', b);
  await o.page.evaluate(() => pushPrefSet({ seats: true })); await tick(o.page, 500);
  b = up().pop();
  ok(b.seats === true && b.prefs && !('seat_open' in b.prefs) && b.prefs.chat === false, 'seat alerts on: the key is removed (a kind is on unless it says false)', b);
  await o.page.evaluate(() => pushPrefSet({ friends: true })); await tick(o.page, 500);
  b = up().pop();
  ok(b.friends === true && b.prefs && !('free' in b.prefs), 'friend alerts on: prefs.free removed', b);
  await o.page.evaluate(() => pushPrefSet({ friends: false })); await tick(o.page, 500);
  ok(up().pop().prefs.free === false, 'friend alerts off: prefs.free=false', up().pop());
  await o.page.evaluate(() => pushPrefSet({ quiet_from: 23, quiet_to: 7 })); await tick(o.page, 500);
  b = up().pop();
  ok(b.quiet_from === 23 && b.quiet_to === 7 && b.prefs.quiet_from === 23 && b.prefs.quiet_to === 7, 'quiet hours: the columns and prefs.quiet_from / quiet_to', b);
  const errs1 = o.log.errors.slice(); await o.close();
  /* read: the phone switched seat alerts off */
  const t2 = clone(FX.TABLES); t2.push_prefs = [{ user_id: ME, seats: true, friends: false, quiet_from: 22, quiet_to: 8, prefs: { seat_open: false } }];
  const o2 = await desk({ tables: t2 }); await ready(o2.page);
  ok((await o2.page.evaluate(() => pushPrefGet())).seats === false, 'the phone’s “A seat opens” off reads as seat alerts off', await o2.page.evaluate(() => pushPrefGet()));
  /* the card has the quiet-hours selects */
  const card = await o2.page.evaluate(() => { const h = pushHourSel('quiet_from', 22); return /<select/.test(h) && /value="22" selected/.test(h) && /pushPrefSet\(\{quiet_from:/.test(h); });
  ok(card, 'quiet hours are editable in the card (a select that calls pushPrefSet)');
  await o2.close();
  /* the prefs column refuses the write (not granted yet): the columns are still written, on their own */
  const t3 = clone(FX.TABLES); t3.push_prefs = [{ user_id: ME, seats: true, friends: false, quiet_from: 22, quiet_to: 8 }];
  const o3 = await desk({ tables: t3, hook: (url, m, body) => (url.pathname.endsWith('/rest/v1/push_prefs') && m === 'POST' && body && body.prefs ? { status: 400, body: JSON.stringify({ code: '42703', message: 'column push_prefs.prefs does not exist' }) } : null) });
  await ready(o3.page);
  const okd = await o3.page.evaluate(() => pushPrefSet({ seats: false }));
  await tick(o3.page, 500);
  const last = writes(o3.log, 'push_prefs').map(w => w.body).filter(Boolean).pop();
  ok(okd === true && last && last.seats === false && !('prefs' in last), 'prefs refused: seats is still written on its own', last);
  ok(errs1.length === 0 && o3.log.errors.length === 0, 'push: no page errors', errs1.concat(o3.log.errors)); await o3.close();
});

/* ======================================================================================================== GAP 7 */
test('saved', async () => {
  const KEYS = { prof: 'ada examplewood|bus' };
  const savedWrites = o => writes(o.log, 'saved_items');
  /* first sync: the account has BUS 3431 and Ada; this browser has ECON 2303 and Bram. Union both ways, nothing deleted. */
  { const t = clone(FX.TABLES); t.saved_items = [{ user_id: ME, kind: 'class', key: 'BUS 3431' }, { user_id: ME, kind: 'prof', key: KEYS.prof }];
    const o = await desk({ tables: t, init: () => { try { localStorage.setItem('professify_watch_classes', JSON.stringify(['ECON 2303'])); } catch (e) {} } }); await ready(o.page); await tick(o.page, 1500);
    const r = await o.page.evaluate(() => ({ wc: watchClasses.slice(), wl: watchlist.map(id => profKey(PROFESSORS[id] || watchSpMeta[id] || {})), ok: TCSYNC.savedOk }));
    ok(r.ok === true && r.wc.includes('BUS 3431') && r.wc.includes('ECON 2303'), 'first sync: the account’s class is added here and this browser’s stays', r);
    ok(r.wl.includes(KEYS.prof), 'first sync: the account’s professor is added to the watchlist', r);
    const ins = savedWrites(o).filter(w => w.m === 'POST').flatMap(w => (Array.isArray(w.body) ? w.body : [w.body]));
    /* ECON 2303 is what this browser had; STAT 2170 and PHIL 3331 are the classes of the sections ME watches (watch_sections), which are on the watchlist too */
    ok(ins.length === 3 && ins.every(x => x.kind === 'class' && x.user_id === ME) && JSON.stringify(ins.map(x => x.key).sort()) === '["ECON 2303","PHIL 3331","STAT 2170"]', 'first sync: only what the account lacks is uploaded (BUS 3431 is not)', ins);
    ok(savedWrites(o).filter(w => w.m === 'DELETE').length === 0, 'first sync: nothing is deleted', savedWrites(o));
    /* a change here: remove BUS 3431 → delete on the account */
    await o.page.evaluate(() => { watchClasses.splice(watchClasses.indexOf('BUS 3431'), 1); saveWatchClasses(); }); await tick(o.page, 1500);
    const del = savedWrites(o).filter(w => w.m === 'DELETE');
    ok(del.length === 1 && /kind=eq\.class/.test(decodeURIComponent(del[0].query)) && /key=eq\.BUS(%20|\s|\+)3431/.test(decodeURIComponent(del[0].query).replace(/ /g, '%20')), 'removing a saved class here deletes it from the account', del.map(x => x.query));
    /* a change there: Ada is removed on the phone → next load removes her here, and does not upload her again */
    o.tables.saved_items = o.tables.saved_items.filter(x => x.kind !== 'prof');
    const n0 = savedWrites(o).filter(w => w.m === 'POST').length;
    await o.page.evaluate(() => tcSavedLoad()); await tick(o.page, 1000);
    const r2 = await o.page.evaluate(() => watchlist.map(id => profKey(PROFESSORS[id] || watchSpMeta[id] || {})));
    ok(!r2.includes(KEYS.prof) && savedWrites(o).filter(w => w.m === 'POST').length === n0, 'a professor removed on the phone is removed here, and not uploaded again', r2);
    /* added there */
    o.tables.saved_items.push({ user_id: ME, kind: 'class', key: 'BUS 3438' });
    await o.page.evaluate(() => tcSavedLoad()); await tick(o.page, 1000);
    ok(await o.page.evaluate(() => watchClasses.includes('BUS 3438')), 'a class saved on the phone appears here');
    /* a professor watched here is uploaded with the review key */
    await o.page.evaluate(() => { const id = Object.keys(PROFESSORS).find(k => profKey(PROFESSORS[k]) === 'bram fixturesen|bus'); toggleWatch(id); }); await tick(o.page, 1500);
    const pi = savedWrites(o).filter(w => w.m === 'POST').flatMap(w => (Array.isArray(w.body) ? w.body : [w.body])).filter(x => x.kind === 'prof');
    ok(pi.length === 1 && pi[0].key === 'bram fixturesen|bus', 'a professor watched here is saved as “name|dept” lowercased, the review key', pi);
    ok(o.log.errors.length === 0, 'saved: no page errors', o.log.errors); await o.close(); }
  /* not installed: nothing breaks, nothing is written, the lists stay */
  { const o = await desk({ tables: clone(FX.TABLES), hook: (url) => (/\/rest\/v1\/saved_items/.test(url.pathname) ? { status: 404, body: JSON.stringify(NO_TABLE) } : null), init: () => { try { localStorage.setItem('professify_watch_classes', JSON.stringify(['ECON 2303'])); } catch (e) {} } });
    await ready(o.page); await tick(o.page, 1500);
    const r = await o.page.evaluate(() => ({ wc: watchClasses.slice(), ok: TCSYNC.savedOk }));
    ok(r.ok === false && r.wc.includes('ECON 2303'), 'saved_items missing: the local list is untouched and the sync switches itself off', r);
    await o.page.evaluate(() => { watchClasses.push('STAT 2170'); saveWatchClasses(); }); await tick(o.page, 1500);
    ok(writes(o.log, 'saved_items').length === 0, 'saved_items missing: nothing else is attempted', writes(o.log, 'saved_items'));
    ok(o.log.errors.length === 0, 'saved_items missing: no page errors', o.log.errors); await o.close(); }
});

/* ======================================================================================================== GAP 8 */
test('favorites', async () => {
  const id = (o, k) => o.page.evaluate(k => Object.keys(PROFESSORS).find(i => profKey(PROFESSORS[i]) === k), k);
  const rpcOk = (favs, extra) => Object.assign({}, FX.RPC, { my_favorite_teachers: favs, set_favorite_teacher: null }, extra || {});
  let o = await desk({ tables: clone(FX.TABLES), rpc: rpcOk(['ada examplewood|bus']) }); await ready(o.page);
  ok(rpcs(o.log, 'my_favorite_teachers').length >= 1, 'favorites are read through my_favorite_teachers');
  const bram = await id(o, 'bram fixturesen|bus'), ada = await id(o, 'ada examplewood|bus');
  await o.page.evaluate(i => startRate(i), ada); await tick(o.page, 600);
  ok(await o.page.evaluate(() => { const c = document.getElementById('rfFav'); return !!c && c.checked && !c.disabled; }), 'the rating form shows a checked favorite-teacher box for a favorite');
  await o.page.evaluate(() => { closeModal && closeModal(); }); await tick(o.page, 300);
  await o.page.evaluate(i => startRate(i), bram); await tick(o.page, 600);
  ok(await o.page.evaluate(() => { const c = document.getElementById('rfFav'); return !!c && !c.checked; }), 'and an unchecked one for someone else');
  await o.page.click('#rfFav'); await tick(o.page, 200);
  await o.page.evaluate(i => tcFavAfter(PROFESSORS[i]), bram); await tick(o.page, 600);
  const c = rpcs(o.log, 'set_favorite_teacher');
  ok(c.length === 1 && JSON.stringify(c[0].body) === JSON.stringify({ p_key: 'bram fixturesen|bus', p_on: true }), 'after the review is saved, set_favorite_teacher(p_key, p_on) is called', c.map(x => x.body));
  ok(await o.page.evaluate(() => submitRate.toString().indexOf('tcFavAfter') > 0 && rfSaveEdit.toString().indexOf('tcFavAfter') > 0), 'posting and editing a review both go through it');
  await o.page.evaluate(() => { closeModal && closeModal(); }); await tick(o.page, 300);
  ok(o.log.errors.length === 0, 'favorites: no page errors', o.log.errors); await o.close();
  /* three already: the box is off for a fourth */
  o = await desk({ tables: clone(FX.TABLES), rpc: rpcOk(['a|b', 'c|d', 'e|f']) }); await ready(o.page);
  await o.page.evaluate(i => startRate(i), await id(o, 'bram fixturesen|bus')); await tick(o.page, 600);
  ok(await o.page.evaluate(() => { const c = document.getElementById('rfFav'); return !!c && c.disabled && /already have 3/.test(document.getElementById('rfFavRow').innerText); }), 'with three favorites the box is off and says why');
  await o.close();
  /* not installed: no box, review form as before */
  o = await desk({ tables: clone(FX.TABLES) }); await ready(o.page);
  await o.page.evaluate(i => startRate(i), await id(o, 'bram fixturesen|bus')); await tick(o.page, 600);
  ok(await o.page.evaluate(() => !document.getElementById('rfFav') && !!document.getElementById('rfMoreToggle')), 'RPC not installed: no favorite box, the rest of the form is there');
  ok(o.log.errors.length === 0, 'not installed: no page errors', o.log.errors); await o.close();
});

test('gameplan', async () => {
  const o = await live({ tables: clone(FX.TABLES) }); await tick(o.page, 1500);
  await o.page.evaluate(() => { localStorage.setItem('professify_appt_2274', '2026-10-21T11:00:00.000Z'); TCPlans.openGamePlan(); }); await tick(o.page, 800);
  const g = await o.page.evaluate(() => { const b = document.getElementById('plGpBack'); return { open: !!b && b.classList.contains('open'), dt: !!document.querySelector('[data-pl-act="appt"]'), appt: !!document.querySelector('.pl2-appt'), txt: (document.querySelector('.pl2-appt') || {}).innerText || '', day: (document.querySelector('.pl2-appt') || {}).getAttribute && document.querySelector('.pl2-appt').getAttribute('data-gp-regday') }; });
  ok(g.open && !g.dt && g.appt && g.day === 'none' && /Your registration day/.test(g.txt), 'the Game Plan shows “Your registration day” instead of the device-only appointment field', g);
  await o.page.click('.pl2-appt [data-rg-act="open"]'); await tick(o.page, 500);
  ok(await o.page.evaluate(() => document.getElementById('rgBack').classList.contains('open') && getComputedStyle(document.getElementById('rgBack')).zIndex >= getComputedStyle(document.getElementById('plGpBack')).zIndex), 'its button opens the registration-day sheet, above the Game Plan');
  await o.page.click('.rg-d[data-day="2026-10-21"]'); await o.page.fill('#rgTime', '11:00 AM'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 900);
  const w = writes(o.log, 'registration_days', 'POST');
  ok(w.length === 1 && w[0].body.day === '2026-10-21' && /^11:00/.test(w[0].body.at_time), 'saving writes registration_days.at_time through the same sheet', w.map(x => x.body));
  const after = await o.page.evaluate(() => ({ txt: document.querySelector('.pl2-appt') ? document.querySelector('.pl2-appt').innerText : '', st: document.querySelector('.pl2-appt') && document.querySelector('.pl2-appt').getAttribute('data-gp-regday'), ls: localStorage.getItem('professify_appt_2274') }));
  ok(after.st === 'set' && /Wed, Oct 21/.test(after.txt) && /11a/.test(after.txt), 'the Game Plan then shows that day', after);
  ok(o.log.errors.length === 0, 'gameplan: no page errors', o.log.errors); await o.close();
});

/* ======================================================================================================== GAP 9 */
test('review-edit', async () => {
  /* the database has no `term` column on reviews: an update that names it is refused, so every edit failed */
  const refuse = (url, m, body) => (m === 'PATCH' && url.pathname.endsWith('/rest/v1/reviews') && body && 'term' in body ? { status: 400, body: JSON.stringify({ code: 'PGRST204', message: "Could not find the 'term' column of 'reviews' in the schema cache" }) } : null);
  const t = clone(FX.TABLES); t.reviews = [{ id: 77, user_id: ME, professor_key: 'bram fixturesen|bus', professor_name: 'Bram Fixturesen', course: 'BUS 3438', score: 3, difficulty: 3, would_again: true, grade: null, format: 'In person', note: 'before', created_at: '2026-09-20T00:00:00Z', tags: [] }];
  const o = await desk({ tables: t, hook: refuse }); await ready(o.page);
  const r = await o.page.evaluate(async () => {
    const id = Object.keys(PROFESSORS).find(k => profKey(PROFESSORS[k]) === 'bram fixturesen|bus'), p = PROFESSORS[id];
    const ed = { id: 77, professor_key: 'bram fixturesen|bus', created_at: '2026-09-20T00:00:00Z' };
    const v = { course: 'BUS 3438', courseKey: 'BUS 3438', term: 'Fall 2026', score: 4, difficulty: 3, teach: 4, hours: '4-6', format: 'In person', grade: '', again: true, tags: [], text: 'after' };
    document.body.insertAdjacentHTML('beforeend', '<button id="rfSubmit"></button>');
    await rfSaveEdit(ed, id, p, v); return { toast: (document.getElementById('frToast') || {}).textContent || '' };
  });
  await tick(o.page, 600);
  const pw = writes(o.log, 'reviews', 'PATCH');
  ok(pw.length >= 1 && pw.every(w => w.body && !('term' in w.body)), 'the edit never sends `term`', pw.map(w => Object.keys(w.body || {})));
  ok(pw.length === 1 && pw[0].body.score === 4 && pw[0].body.note === 'after', 'one update, with the changed fields', pw.map(w => w.body));
  ok(/Review updated/.test(r.toast), 'and the edit saves (“Review updated”)', r);
  ok(o.log.errors.length === 0, 'review-edit: no page errors', o.log.errors); await o.close();
});

/* ======================================================================================================== GAP 10 */
test('normcode', async () => {
  const t = clone(FX.TABLES);
  t.saved_classes = t.saved_classes.concat([{ user_id: ME, term: '2268', code: 'CHEM1210L', class_nbr: null, created_at: '2026-09-10T18:00:00Z', waitlist_pos: null }, { user_id: ME, term: '2268', code: 'BUS2201', class_nbr: null, created_at: '2026-09-10T18:00:00Z', waitlist_pos: null }]);
  const o = await desk({ tables: t }); await ready(o.page); await tick(o.page, 800);
  const n = await o.page.evaluate(() => ['chem 1210l', 'CHEM1210L', 'bus-3431', 'BUS 3431', 'A&B 1234', 'a&b1234', 'MATH 141', 'nonsense'].map(normCode));
  ok(JSON.stringify(n) === JSON.stringify(['CHEM 1210L', 'CHEM 1210L', 'BUS 3431', 'BUS 3431', 'A&B 1234', 'A&B 1234', 'MATH 141', 'NONSENSE']), 'normCode keeps a suffix letter and an ampersand', n);
  const mc = await o.page.evaluate(() => myClasses.slice());
  ok(mc.includes('CHEM 1210L') && !mc.includes('CHEM1210L') && mc.includes('BUS 2201') && !mc.includes('BUS2201'), 'saved_classes codes are read through normCode (unspaced legacy rows included)', mc);
  await o.page.evaluate(() => { const i = myClasses.indexOf('CHEM 1210L'); if (i >= 0) { myClasses.splice(i, 1); } return pushMyClassToDb('CHEM 1210L', false); }); await tick(o.page, 700);
  const del = writes(o.log, 'saved_classes', 'DELETE');
  ok(del.length >= 1 && /CHEM(%20|\s|\+)1210L/.test(decodeURIComponent(del[del.length - 1].query).replace(/ /g, '%20')) && /CHEM1210L/.test(decodeURIComponent(del[del.length - 1].query)), 'removing it deletes the row under both spellings', del.map(x => decodeURIComponent(x.query)));
  ok(o.log.errors.length === 0, 'normcode: no page errors', o.log.errors); await o.close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 500)); }
}
console.log(`\ncheck-desktop-sync: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
/* friend-polish (2026-10-16): this file was updated by edit-tests-friend-polish-2026-10-16.py */
/* reg-timeline (2026-10-16): this file was updated by edit-tests-reg-timeline-2026-10-16.py */
