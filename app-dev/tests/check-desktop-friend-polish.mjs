/* check-desktop-friend-polish — three cleanups (friend-polish, Tate 2026-10-16), the REAL index.html signed in, same stand-in as check-desktop-home.
   Run: APP_DIR=<repo> node check-desktop-friend-polish.mjs [--only name] [--quiet] [--shots DIR] [--width N]   (APP_PORT to move off 8190)
   - a friend's page, Their classes: no "Schedule | List" words; ONE small icon button for the view; the term is the phone's Explore switch
     (muted bold words + up/down icon, one button that flips), not two pills;
   - a Home friend card on Spring classes / a plan: no free-today line; the header says the plan and term once, one small "New";
     the Fall card keeps its free-today line;
   - story pins: no badge on the ring; a pin before the name; pinned first; the hover button and right-click still work. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const SHOTS = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
const DARK = args.includes('--dark');
const WIDTH = args.includes('--width') ? +args[args.indexOf('--width') + 1] : 1440;
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: WIDTH, height: 900, wait: 4000 }, o));
const T = {}; const test = (name, fn) => { T[name] = fn; };
const shot = async (page, name, sel) => {
  if (!SHOTS) return;
  try { if (DARK) await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark')); await page.waitForTimeout(150); if (sel) await (await page.$(sel)).screenshot({ path: SHOTS + '/' + name + '-' + WIDTH + (DARK ? '-dark' : '') + '.png' }); else await page.screenshot({ path: SHOTS + '/' + name + '-' + WIDTH + (DARK ? '-dark' : '') + '.png' }); }
  catch (e) { console.log('shot failed', name, String(e).slice(0, 120)); }
};
const [AV, RO, SK, QU, HA] = FX.FRIENDS;
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
const clone = x => JSON.parse(JSON.stringify(x));
const seat = (t, code, s, term) => t.course_seats.find(r => r.course_code === code && r.section === s && r.term === term);
const give = (t, uid, code, s) => {
  const r = seat(t, code, s, '2274'); t.saved_classes.push({ user_id: uid, term: '2274', code, class_nbr: r.class_nbr, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null });
  t.my_sections.push({ user_id: uid, term: '2274', code, class_nbr: r.class_nbr, section: r.section, instructor: r.instructor, days: r.days, status: 'enrolled', wl_pos: null });
};
const plan = (t, uid, slot, list) => t.plans.push({ user_id: uid, term: '2274', slot, sections: list.map(([c, s]) => ({ code: c, class_nbr: seat(t, c, s, '2274').class_nbr })), shared: true });
function tables() {
  const t = clone(FX.TABLES);
  const spring = t.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }));
  t.course_seats = t.course_seats.concat(spring);
  give(t, FX.ME.id, 'BUS 4401', '01');
  give(t, AV.id, 'BUS 4401', '01'); give(t, AV.id, 'BUS 3346', '01'); give(t, AV.id, 'BUS 3431', '02'); give(t, AV.id, 'STAT 2170', '05');
  plan(t, RO.id, 'A', [['BUS 3431', '01'], ['BUS 3346', '01'], ['PHIL 3331', '01']]);
  return t;
}
const SEED = () => { let s = 12345; Math.random = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; }; };
const ready = async page => { for (let i = 0; i < 40; i++) { if (await page.evaluate(() => !!(window._myHistOk && window._friendsFresh && window.TCPlans && TCPlans.friendPlansReady()))) return; await tick(page, 300); } };

test('friend page', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: tables(), init: SEED }); await tick(page, 2500); await ready(page);
  await page.evaluate(id => openFriendProfile(id), AV.id); await tick(page, 700);
  const q = () => page.evaluate(() => {
    const m = document.getElementById('frpModal'), bar = m.querySelector('.frp-bar'), tw = m.querySelectorAll('.frp-termsw'), vs = m.querySelectorAll('.frp-vsw');
    const r = e => e ? e.getBoundingClientRect() : null, a = r(tw[0]), b = r(vs[0]);
    return { tw: tw.length, twTxt: tw[0] ? tw[0].textContent.trim() : null, twSvg: !!(tw[0] && tw[0].querySelector('svg')), twAria: tw[0] && tw[0].getAttribute('aria-label'),
      vs: vs.length, vsTxt: vs[0] ? vs[0].textContent.trim() : null, vsAria: vs[0] && vs[0].getAttribute('aria-label'), pills: m.querySelectorAll('.mc-viewtog').length, list: !!m.querySelector('.frp-list'), cal: !!m.querySelector('.frp-cal'),
      sameRow: !!(a && b && Math.abs((a.top + a.bottom) / 2 - (b.top + b.bottom) / 2) < 6), twColor: tw[0] ? getComputedStyle(tw[0]).color : null, twH: a ? Math.round(a.height) : 0, vsW: b ? Math.round(b.width) : 0, vsH: b ? Math.round(b.height) : 0, twTitle: tw[0] && tw[0].title, vsTitle: vs[0] && vs[0].title,
      words: /\bSchedule\b|\bList\b/.test(bar ? bar.innerText : '') };
  });
  let r = await q();
  ok(r.tw === 1 && r.pills === 0 && r.twTxt === 'Fall 2026' && r.twSvg && /Showing Fall 2026\. Switch to Spring 2027/.test(r.twAria), 'term: ONE switch (not two pills): “Fall 2026” + the up/down icon, labelled', r);
  ok(r.vs === 1 && r.vsTxt === '' && r.vsAria === 'Show as a list' && !r.words && r.sameRow, 'view: one small icon button (no words), in the same row as the term', r);
  ok(r.cal && !r.list, 'view: opens on the schedule', r);
  ok(r.twTitle === 'Switch to Spring 2027' && r.vsTitle === 'Show as a list' && r.twH >= 40 && r.vsW >= 40 && r.vsH >= 40, 'both controls have a tooltip and are at least 40px touch targets', r);
  await shot(page, 'friend-modal-fall-schedule', '#frpModal');
  await page.click('#frpModal .frp-termsw'); await tick(page, 500);
  r = await q();
  ok(r.twTxt === 'Spring 2027' && /Showing Spring 2027\. Switch to Fall 2026/.test(r.twAria) && r.tw === 1, 'term: one tap flips Fall 2026 → Spring 2027', r);
  await shot(page, 'friend-modal-spring', '#frpModal');
  ok(await page.evaluate(() => /BUS 4401/.test(document.getElementById('frpModal').innerText)), 'Spring shows her Spring class');
  await page.click('#frpModal .frp-termsw'); await tick(page, 500);
  ok((await q()).twTxt === 'Fall 2026', 'term: and back');
  await page.click('#frpModal .frp-vsw'); await tick(page, 500);
  r = await q();
  ok(r.list && !r.cal && r.vsAria === 'Show as a schedule' && r.vs === 1, 'view: the icon flips to the list (and now offers the schedule)', r);
  await shot(page, 'friend-modal-fall-list', '#frpModal');
  await page.click('#frpModal .frp-vsw'); await tick(page, 400);
  ok((await q()).cal, 'view: and back to the schedule');
  await page.evaluate(() => closeFriendProfile());
  await page.evaluate(id => openFriendProfile(id), QU.id); await tick(page, 600);
  await page.click('#frpModal .frp-termsw'); await tick(page, 500);
  const e = await page.evaluate(() => ({ sw: document.querySelectorAll('#frpModal .frp-termsw').length, vs: document.querySelectorAll('#frpModal .frp-vsw').length, none: /hasn’t added any classes/.test(document.getElementById('frpModal').innerText) }));
  ok(e.sw === 1 && e.vs === 0 && e.none, 'a term with no classes: the switch stays (to get back), no view icon, the plain sentence', e);
  ok(log.errors.length === 0, 'friend page: no page errors', log.errors);
  await close();
});

test('home card', async () => {
  const { page, close, log, tables: tabs } = await desk({ terms: SPRING_CFG, tables: tables(), init: SEED }); await tick(page, 2500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 900);
  const card = id => page.evaluate(id => {
    const a = document.querySelector('#hmFeed article[data-fid="' + id + '"]'); if (!a) return null;
    return { head: a.querySelector('.fhead-t').innerText.replace(/\s+/g, ' ').trim(), line: (a.querySelector('.av-line') || {}).textContent || null, chips: a.querySelectorAll('.hm-fview').length, news: a.querySelectorAll('.hm-fnew').length, txt: a.innerText };
  }, id);
  const ro = await card(RO.id), av = await card(AV.id), sk = await card(SK.id), qu = await card(QU.id);
  ok(ro && ro.head === 'Rowan Testa Plan A · Spring 2027 · 3 classes' && ro.chips === 0 && ro.news === 0, 'plan card: “Plan A · Spring 2027 · 3 classes”, once, no chips', ro);
  ok(av && /^Avery.* Spring 2027 · 4 classes/.test(av.head) && (av.head.match(/Spring 2027/g) || []).length === 1, 'Spring-classes card: “Spring 2027 · 4 classes”, once', av);
  ok([ro, av].every(x => x && x.line === null && !/left today|both open|No class till/i.test(x.txt)), 'neither Spring card has a free-today line', [ro && ro.line, av && av.line]);
  ok(sk && sk.chips === 0 && /Taking 2 classes · Fall 2026/.test(sk.head) && (sk.head.match(/Fall 2026/g) || []).length === 1, 'Fall card: “Taking 2 classes · Fall 2026”, once', sk);
  const fall = [sk, qu].filter(x => x && x.line);
  ok(fall.length >= 1, 'Fall cards keep their free-today line (“In BUS … till …” / “No class …”)', [sk && sk.line, qu && qu.line]);
  await shot(page, 'home-cards', '#hmFeed');
  /* the "New" marker: change what Rowan shares (Plan A gets another class) and Sky adds a Spring class, then look again */
  const seen = await page.evaluate(() => Object.keys(HM_SEEN).filter(k => k.indexOf('@home|') === 0).length);
  ok(seen >= 3, 'first visit remembers each friend’s view', seen);
  tabs.plans.find(r => r.user_id === RO.id && r.slot === 'A').sections.push({ code: 'STAT 2170', class_nbr: seat(tabs, 'STAT 2170', '05', '2274').class_nbr });
  give(tabs, SK.id, 'BUS 3346', '01');
  await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 3500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 900);
  const ro2 = await card(RO.id), sk2 = await card(SK.id), av2 = await card(AV.id);
  ok(ro2 && ro2.news === 1 && ro2.chips === 0 && /^Rowan Testa Plan A · Spring 2027 · 4 classes ?NEW$/i.test(ro2.head) && (ro2.head.match(/Spring 2027/g) || []).length === 1, 'changed plan: one small “New”, plan and term said once', ro2);
  ok(sk2 && sk2.news === 1 && sk2.chips === 0 && /Spring 2027 · 1 class ?NEW$/i.test(sk2.head) && sk2.line === null, 'new Spring classes: one small “New”, no free-today line', sk2);
  ok(av2 && av2.news === 0, 'nothing changed: no marker', av2);
  const same = await page.evaluate(() => {
    const n = document.querySelector('#hmFeed .hm-fnew'), m = document.createElement('span'); m.className = 'hm-newmark'; m.textContent = 'New'; n.parentNode.appendChild(m);
    const g = e => { const c = getComputedStyle(e); return [c.color, c.backgroundColor, c.fontSize, c.fontWeight, c.borderRadius, c.padding, c.letterSpacing, c.textTransform].join('|'); };
    const r = { a: g(n), b: g(m) }; m.remove(); return r;
  });
  ok(same.a === same.b, 'the “New” in the header line looks exactly like the card-level New mark (.hm-newmark)', same);
  await shot(page, 'home-cards-new', '#hmFeed');
  ok(log.errors.length === 0, 'home card: no page errors', log.errors);
  await close();
});

test('pins', async () => {
  const pinRpc = ids => Object.assign({}, FX.RPC, { my_pinned_friends: ids });
  const hk = (url, m, body) => { if (!url.pathname.endsWith('/rpc/set_pinned_friends')) return null; hk.calls.push(body); return { status: 200, body: JSON.stringify(body.p_ids) }; }; hk.calls = [];
  const o = await desk({ tables: clone(FX.TABLES), rpc: pinRpc([HA.id, RO.id]), hook: hk }); const { page, log } = o; await tick(page, 2500);
  for (let i = 0; i < 40; i++) { if (await page.evaluate(() => typeof friendsLoaded !== 'undefined' && friendsLoaded && !frSignInBusy)) break; await tick(page, 300); }
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 900);
  const strip = () => page.evaluate(() => [...document.querySelectorAll('#hmStripWrap .hm-fitem:not(.hm-fadd)')].map(b => ({
    nm: b.querySelector('.nm').textContent.split(' ')[0], mark: !!b.querySelector('.nm .hm-pinmark'), ringKids: b.querySelector('.ring').children.length, badge: !!b.querySelector('.hm-pinbadge'), cls: b.classList.contains('pinned') })));
  let st = await strip();
  ok(JSON.stringify(st.map(x => x.nm).slice(0, 2)) === '["Harper","Rowan"]' && st[0].cls && st[1].cls, 'pinned friends still come first, in pin order', st.map(x => x.nm));
  ok(st[0].mark && st[1].mark && st.slice(2).every(x => !x.mark), 'a pinned story has a small pin before the name; the others do not', st);
  ok(st.every(x => !x.badge && x.ringKids === 1), 'no badge on any ring (the ring holds only the face)', st);
  const geo = await page.evaluate(() => {
    const b = document.querySelector('#hmStripWrap .hm-fitem.pinned'), ring = b.querySelector('.ring').getBoundingClientRect(), m = b.querySelector('.nm .hm-pinmark').getBoundingClientRect(), n = b.querySelector('.nm').getBoundingClientRect(), it = b.getBoundingClientRect();
    return { markBelowRing: m.top >= ring.bottom - 1, markInItem: m.left >= it.left - 1 && m.right <= it.right + 1, nmInItem: n.right <= it.right + 1 };
  });
  const mk = await page.evaluate(() => { const m = document.querySelector('#hmStripWrap .hm-fitem.pinned .nm .hm-pinmark').getBoundingClientRect(); return { w: Math.round(m.width), h: Math.round(m.height) }; });
  ok(mk.w <= 10 && mk.h <= 10, 'the pin mark is 10px or less', mk);
  const lg = await page.evaluate(() => { const b = document.querySelector('#hmStripWrap .hm-fitem.pinned'), nm = b.querySelector('.nm'), t = nm.lastChild; const old = t.textContent; t.textContent = 'Bartholomew Longname-Smithington'; const m = nm.querySelector('.hm-pinmark').getBoundingClientRect(), n = nm.getBoundingClientRect(), r = { shown: m.width > 0 && m.left >= n.left - 1 && m.right <= n.right + 1, clipped: nm.scrollWidth > nm.clientWidth }; t.textContent = old; return r; });
  ok(lg.shown && lg.clipped, 'a long name: the pin still shows and the name is what gets clipped', lg);
  ok(geo.markBelowRing && geo.markInItem && geo.nmInItem, 'the pin sits under the avatar, inside the tile', geo);
  await shot(page, 'stories', '#hmStripWrap');
  await page.hover('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"]'); await shot(page, 'stories-hover', '#hmStripWrap');
  await page.click('#hmStripWrap .hm-fw[data-fid="' + SK.id + '"] .hm-spin'); await tick(page, 500);
  ok(hk.calls.length === 1 && JSON.stringify(hk.calls[0]) === JSON.stringify({ p_ids: [HA.id, RO.id, SK.id] }), 'the hover pin button still pins (set_pinned_friends)', hk.calls);
  st = await strip();
  ok(st[2].nm === 'Sky' && st[2].mark, 'and Sky gets the pin mark', st.map(x => [x.nm, x.mark]));
  await page.click('#hmStripWrap .hm-fitem[data-fid="' + HA.id + '"]', { button: 'right' }); await tick(page, 500);
  ok(hk.calls.length === 2 && JSON.stringify(hk.calls[1]) === JSON.stringify({ p_ids: [RO.id, SK.id] }), 'right-click still unpins', hk.calls);
  st = await strip();
  ok(!st.find(x => x.nm === 'Harper').mark, 'and the mark goes with it', st.map(x => [x.nm, x.mark]));
  ok(log.errors.length === 0, 'pins: no page errors', log.errors);
  await o.close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-friend-polish: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
