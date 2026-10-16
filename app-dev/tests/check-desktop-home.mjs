/* check-desktop-home — the website's Home at the phone's level (website-home-catchup, Tate 2026-10-14). Runs the REAL
   index.html in Chromium, signed in, against the PostgREST stand-in of check-desktop-terms. Fixed clock: Tuesday 10:30 PT.
   Run: APP_DIR=<repo> node check-desktop-home.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises (the phone's spring-wall HOME part, feed-class-recs, stories-freeness):
   - each friend's card shows the newest real thing — Spring classes, else their first shared Spring plan (in its colour),
     else their week now — with a tag and a count line that say which; single-term the feed is exactly what it was;
   - a friend whose Spring classes / plan changed since you last opened Home goes first, once;
   - "Classes your friends are planning": after the 3rd card, not yours, not on your record, the professor most of those
     friends have (a tie shows none), falling back to "taking";
   - stories: no classes today, done, class later (furthest off first), in class (out soonest), then not set up (grey). */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const T = {};
const test = (name, fn) => { T[name] = fn; };
const [AV, RO, SK, QU, HA] = FX.FRIENDS;

const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
const seat = (T, code, s, term) => T.course_seats.find(r => r.course_code === code && r.section === s && r.term === term);
const give = (T, uid, code, s) => {           /* a Spring class: saved + the section row */
  const r = seat(T, code, s, '2274');
  T.saved_classes.push({ user_id: uid, term: '2274', code, class_nbr: r.class_nbr, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null });
  T.my_sections.push({ user_id: uid, term: '2274', code, class_nbr: r.class_nbr, section: r.section, instructor: r.instructor, days: r.days, status: 'enrolled', wl_pos: null });
};
const plan = (T, uid, slot, list) => T.plans.push({ user_id: uid, term: '2274', slot, sections: list.map(([c, s]) => ({ code: c, class_nbr: seat(T, c, s, '2274').class_nbr })), shared: true });
/* Spring seats (Fall's copied with the term changed; Spring reuses Fall's class numbers on purpose). BUS 3438 isn't offered. */
function base() {
  const t = JSON.parse(JSON.stringify(FX.TABLES));
  const spring = t.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }));
  t.course_seats = t.course_seats.concat(spring);
  return t;
}
/* You: BUS 4401 in Spring. Avery: BUS 4401, BUS 3346, BUS 3431 §02, STAT 2170 in Spring. Rowan: no Spring class, shared Plan B
   (BUS 3431 §01, BUS 3346, PHIL 3331) and Plan C (STAT 2170, ECON 2303). Sky, Quinn: Fall only. Harper: nothing. */
function homeTables() {
  const t = base();
  give(t, FX.ME.id, 'BUS 4401', '01');
  give(t, AV.id, 'BUS 4401', '01'); give(t, AV.id, 'BUS 3346', '01'); give(t, AV.id, 'BUS 3431', '02'); give(t, AV.id, 'STAT 2170', '05');
  plan(t, RO.id, 'B', [['BUS 3431', '01'], ['BUS 3346', '01'], ['PHIL 3331', '01']]);
  plan(t, RO.id, 'C', [['STAT 2170', '05'], ['ECON 2303', '03']]);
  t.plans.find(r => r.user_id === RO.id && r.slot === 'B').sections.push({ code: 'BUS 9999', class_nbr: '79999' });   /* a section the Spring feed doesn't have: never drawn, never counted, never suggested */
  return t;
}
const SEED = () => { let s = 12345; Math.random = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; }; };
/* under load the loaders land late: wait for your record, the fresh friends and their plans (the fake clock needs ticking) */
const ready = async page => { for (let i = 0; i < 40; i++) { if (await page.evaluate(() => !!(window._myHistOk && window._friendsFresh && window.TCPlans && TCPlans.friendPlansReady()))) return; await tick(page, 300); } };
const cardOf = (page, id) => page.evaluate(id => {
  const a = document.querySelector('#hmFeed article[data-fid="' + id + '"]'); if (!a) return null;
  const tag = a.querySelector('.hm-fview'), nw = a.querySelector('.hm-fnew');
  return { chg: !!a.querySelector('.hm-chg'), view: a.getAttribute('data-hmview'), cls: a.className, tag: tag ? tag.textContent : null, tagColor: tag ? getComputedStyle(tag).color : null, fresh: nw ? nw.textContent : null,
    ctx: (a.querySelector('.ctx') || {}).textContent || '', txt: a.innerText, blocks: [...a.querySelectorAll('.cal-block')].map(b => b.textContent.replace(/\s+/g, ' ').trim()) };
}, id);
const cardOrder = page => page.evaluate(() => [...document.querySelectorAll('#hmFeed > article.hm-card')].map(a => a.getAttribute('data-fid')));

test('cards', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: homeTables(), init: SEED }); await tick(page, 2500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 800);
  const av = await cardOf(page, AV.id), ro = await cardOf(page, RO.id), sk = await cardOf(page, SK.id), qu = await cardOf(page, QU.id), ha = await cardOf(page, HA.id);
  ok(av && av.view === 'next' && av.tag === 'Spring 2027 classes' && /^Planning 4 classes · Spring 2027/.test(av.ctx), 'Avery (Spring classes): tag “Spring 2027 classes”, “Planning 4 classes · Spring 2027”', av && { v: av.view, t: av.tag, c: av.ctx });
  ok(av && /4401/.test(av.txt) && av.blocks.length > 0 && !/4442|PHIL/.test(av.blocks.join(' ')), 'Avery: her week is her Spring classes, none of the Fall ones', av && av.blocks);
  ok(av && /1 with you/.test(av.ctx) && ro && !/with you/.test(ro.ctx), 'overlap: Avery’s Spring class is yours (Spring list); Rowan’s plan shares nothing with it (BUS 3431 is yours in FALL only)', { av: av && av.ctx, ro: ro && ro.ctx });
  ok(ro && ro.view === 'B' && ro.tag === 'Plan B · Spring 2027' && /^Planning 3 classes · Spring 2027/.test(ro.ctx), 'Rowan (only a shared Spring plan): the first shared plan — “Plan B · Spring 2027”, “Planning 3 classes”', ro && { v: ro.view, t: ro.tag, c: ro.ctx });
  ok(ro && /hm-plan-B/.test(ro.cls) && ro.tagColor === 'rgb(154, 52, 18)', 'Rowan: the card and tag are in Plan B’s colour (orange ink #9A3412)', ro && { c: ro.cls, col: ro.tagColor });
  ok(ro && ro.blocks.length > 0 && !/4445|2303|1101/.test(ro.blocks.join(' ')) && /3346|3431/.test(ro.blocks.join(' ')), 'Rowan: the plan’s week, none of her Fall classes (BUS 4445, ECON 2303)', ro && ro.blocks);
  ok(sk && sk.view === 'now' && sk.tag === 'Now · Fall 2026' && /^Taking 2 classes · Fall 2026/.test(sk.ctx), 'Sky (Fall only): her week now — “Now · Fall 2026”, “Taking 2 classes · Fall 2026”', sk && { t: sk.tag, c: sk.ctx });
  ok(qu && qu.view === 'now' && qu.tag === 'Now · Fall 2026' && /^Taking 1 class · Fall 2026/.test(qu.ctx), 'Quinn: “Taking 1 class · Fall 2026” (one class, singular)', qu && qu.ctx);
  ok(ha === null, 'Harper (nothing anywhere): no card');
  const reads = log.reads.map(r => decodeURIComponent(r)).filter(r => /^plans\?/.test(r));
  ok(reads.length > 0 && reads.every(r => /term=eq\.2274/.test(r)), 'wire: every plans read names Spring’s term', reads);
  ok(log.errors.length === 0, 'cards: no page errors', log.errors);
  await close();
});

test('lift', async () => {
  const o = await desk({ terms: SPRING_CFG, tables: homeTables(), init: SEED }); const { page, log } = o; await tick(page, 2500); await ready(page); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 800);
  let n = await page.evaluate(() => document.querySelectorAll('#hmFeed .hm-fnew').length);
  ok(n === 0, 'first visit: nothing is “new” — there is nothing to compare with', n);
  const seen = await page.evaluate(() => Object.keys(HM_SEEN).filter(k => k.indexOf('@home|') === 0).length);
  ok(seen === 5, 'first visit: each friend’s Home view is remembered (HM_SEEN, @home|you|friend)', seen);
  /* Rowan shares Plan A now; Sky added a Spring class */
  plan(o.tables, RO.id, 'A', [['BUS 4442', '01']]); give(o.tables, SK.id, 'BUS 3346', '01');
  await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 3500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 900);
  const order = await cardOrder(page), ro = await cardOf(page, RO.id), sk = await cardOf(page, SK.id), av = await cardOf(page, AV.id);
  ok(JSON.stringify(order.slice(0, 2).sort()) === JSON.stringify([RO.id, SK.id].sort()), 'after a change: the two friends who changed are the first two cards', order);
  ok(ro && ro.fresh === 'New plan' && ro.view === 'A' && ro.tag === 'Plan A · Spring 2027', 'Rowan: “New plan” on Plan A', ro && { f: ro.fresh, t: ro.tag });
  ok(sk && sk.fresh === 'Spring classes added' && sk.tag === 'Spring 2027 classes', 'Sky: “Spring classes added” on her Spring classes', sk && { f: sk.fresh, t: sk.tag });
  ok(av && av.fresh === null, 'Avery (nothing changed): no mark', av && av.fresh);
  ok(ro && sk && !ro.chg && !sk.chg, 'a new view is not a “changed” card: no Added/Dropped line comparing their Fall week with the Spring one', { ro: ro && ro.chg, sk: sk && sk.chg });
  /* once */
  await page.reload({ waitUntil: 'domcontentloaded' }); await tick(page, 3500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 900);
  n = await page.evaluate(() => document.querySelectorAll('#hmFeed .hm-fnew').length);
  ok(n === 0, 'next visit, nothing changed: the mark is gone — once', n);
  ok(log.errors.length === 0, 'lift: no page errors', log.errors);
  await o.close();
});

test('recs', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: homeTables(), init: SEED }); await tick(page, 2500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 800);
  const r = await page.evaluate(() => {
    const row = document.querySelector('#hmFeed .hm-recs'); if (!row) return null;
    let before = 0, p = row.previousElementSibling; while (p) { if (p.matches('article.hm-card')) before++; p = p.previousElementSibling; }
    const sib = [...document.getElementById('hmFeed').children].indexOf(row);
    return { head: row.querySelector('.hm-recs-h span').textContent, before, sib, scrolls: getComputedStyle(row.querySelector('.hm-recs-row')).overflowX,
      cards: [...row.querySelectorAll('.hm-rec')].map(c => ({ code: c.getAttribute('data-code'), name: (c.querySelector('.hm-rec-n') || {}).textContent || '', who: c.querySelector('.hm-rec-w').textContent.trim(), faces: c.querySelectorAll('.sav').length, chip: (c.querySelector('.hm-rec-p') || {}).textContent || null })) };
  });
  ok(r && r.head === 'Classes your friends are planning', 'row: “Classes your friends are planning”', r && r.head);
  ok(r && r.before === 3, 'row: after the third friend’s card', r && r.before);
  ok(r && r.scrolls === 'auto', 'row: scrolls sideways', r && r.scrolls);
  ok(r && JSON.stringify(r.cards.map(c => c.code)) === '["BUS 3346","BUS 3431","STAT 2170","ECON 2303"]', 'row: the classes friends are planning (every shared plan counts), not yours (BUS 4401) and not on your record (PHIL 3331), most friends first, then code', r && r.cards.map(c => c.code));
  const b46 = r && r.cards.find(c => c.code === 'BUS 3346'), b31 = r && r.cards.find(c => c.code === 'BUS 3431');
  ok(b46 && /2 friends/.test(b46.who) && b46.faces === 2 && b46.name.length > 3, 'BUS 3346: the name, two faces, “2 friends”', b46);
  ok(b46 && /^★ 3\.8 · Dummelow$/.test(b46.chip), 'BUS 3346: both friends have Dummelow — “★ 3.8 · Dummelow”', b46 && b46.chip);
  ok(b31 && /2 friends/.test(b31.who) && b31.chip === null, 'BUS 3431: Avery has one professor, Rowan’s plan another — a tie shows no rating', b31);
  await page.evaluate(() => { window.__opened = null; const o = window.openClassFromFeed; window.openClassFromFeed = c => { window.__opened = c; }; window.__o = o; });
  await page.click('#hmFeed .hm-rec[data-code="BUS 3346"]');
  ok(await page.evaluate(() => window.__opened) === 'BUS 3346', 'a card opens its class');
  await page.evaluate(() => { window.openClassFromFeed = window.__o; });
  await page.click('#hmFeed .hm-rec[data-code="BUS 3346"]'); await tick(page, 700);
  ok(await page.evaluate(() => cpCode === 'BUS 3346' && document.getElementById('view-class').classList.contains('active')), 'the real click opens the class page');
  ok(log.errors.length === 0, 'recs: no page errors', log.errors);
  await close();
  /* nobody planning anything: "taking" — their classes now that Spring offers */
  const t2 = base();
  const f = await desk({ terms: SPRING_CFG, tables: t2, init: SEED }); await tick(f.page, 2500); await ready(f.page);
  await f.page.evaluate(() => { show('home'); renderHome(); }); await tick(f.page, 800);
  const w = await f.page.evaluate(() => { const row = document.querySelector('#hmFeed .hm-recs'); return row ? { head: row.querySelector('.hm-recs-h span').textContent, codes: [...row.querySelectorAll('.hm-rec')].map(c => c.getAttribute('data-code')) } : null; });
  ok(w && w.head === 'Classes your friends are taking', 'nobody planning: “Classes your friends are taking”', w);
  ok(w && JSON.stringify(w.codes) === '["ECON 2303","STAT 2170"]', 'taking: their Fall classes Spring offers, not ones you are in now (BUS 3431, 4442, 4445) or on your record (PHIL 3331); BUS 3438 (not offered) and UNIV 1101 (no sections) left out', w && w.codes);
  await f.close();
});


test('liftHidden', async () => {
  /* a render nobody looked at (the tab is hidden) must not spend the lift: nothing is remembered until Home is really seen */
  const o = await desk({ terms: SPRING_CFG, tables: homeTables(), init: () => { Object.defineProperty(document, 'hidden', { get: () => !!window.__hid, configurable: true }); window.__hid = true; } }); const { page } = o; await tick(page, 2500); await ready(page);
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 800);
  const hid = await page.evaluate(() => Object.keys(HM_SEEN).filter(k => k.indexOf('@home|') === 0).length);
  ok(hid === 0, 'Home not on screen: nothing is remembered, so no lift is spent', hid);
  await page.evaluate(() => { window.__hid = false; hmRenderFeed(); }); await tick(page, 500);
  const vis = await page.evaluate(() => Object.keys(HM_SEEN).filter(k => k.indexOf('@home|') === 0).length);
  ok(vis === 5, 'Home on screen: each friend’s view is remembered', vis);
  await o.close();
});

const stories = page => page.evaluate(() => [...document.querySelectorAll('#hmStripWrap .hm-fitem:not(.hm-fadd)')].map(b => ({ nm: b.querySelector('.nm').textContent, cls: b.className.replace(/hm-fitem|\s+/g, ' ').trim(), title: b.title })));
test('stories', async () => {
  /* Tuesday 10:30. Avery: in PHIL till 11:00. Rowan: in ECON till 12:00. Sky: STAT at 12:10. Quinn: MoWe only. Harper: nothing set up. */
  const t = JSON.parse(JSON.stringify(FX.TABLES));
  const q = t.my_sections.find(r => r.user_id === QU.id), s42 = t.course_seats.find(r => r.course_code === 'BUS 4442');
  Object.assign(q, { code: 'BUS 4442', class_nbr: s42.class_nbr, section: s42.section, instructor: s42.instructor, days: s42.days });
  t.saved_classes.find(r => r.user_id === QU.id && r.code === 'PHIL 3331').code = 'BUS 4442'; t.saved_classes.find(r => r.user_id === QU.id && r.code === 'BUS 4442').class_nbr = s42.class_nbr;
  let o = await desk({ tables: t, init: SEED }); await tick(o.page, 2500); await ready(o.page);
  await o.page.evaluate(() => { show('home'); renderHome(); }); await tick(o.page, 800);
  let st = await stories(o.page);
  ok(JSON.stringify(st.map(x => x.nm.split(' ')[0])) === '["Quinn","Sky","Avery","Rowan","Harper"]', 'Tue 10:30: no classes today, then a class later, then in class (out 11:00 before 12:00), then not set up', st.map(x => x.nm));
  const by = n => st.find(x => x.nm.indexOf(n) === 0);
  ok(/hm-now/.test(by('Quinn').cls) && /hm-now/.test(by('Sky').cls), 'free (no classes today / class later): green ring', [by('Quinn').cls, by('Sky').cls]);
  ok(/hm-in/.test(by('Avery').cls) && /hm-in/.test(by('Rowan').cls), 'in class: blue ring', [by('Avery').cls, by('Rowan').cls]);
  ok(/hm-unset/.test(by('Harper').cls) && !/hm-free/.test(by('Harper').cls), 'schedule not set up: grey ring, never called free', by('Harper').cls);
  ok(/no classes today/.test(by('Quinn').title) && /in class till 11/.test(by('Avery').title) && /not set up/.test(by('Harper').title), 'the ring’s state is in the face’s name (not colour alone)', st.map(x => x.title));
  const ring = await o.page.evaluate(() => { const g = n => getComputedStyle([...document.querySelectorAll('#hmStripWrap .hm-fitem')].find(b => b.textContent.indexOf(n) >= 0).querySelector('.ring')).borderTopColor; return { sky: g('Sky'), avery: g('Avery'), harper: g('Harper') }; });
  ok(ring.sky !== ring.avery && ring.harper !== ring.avery && ring.harper !== ring.sky && ring.harper === 'rgb(203, 213, 225)', 'the three rings are three different colours, and the unset one is the visible grey (#CBD5E1)', ring);
  ok(o.log.errors.length === 0, 'stories: no page errors', o.log.errors); await o.close();
  /* 3:30pm: everyone with a class today is done; done-for-day ranks after no-class-today, ties by name */
  o = await desk({ tables: t, init: SEED, time: '2026-09-29T15:30:00-07:00' }); await tick(o.page, 2500); await ready(o.page);
  await o.page.evaluate(() => { show('home'); renderHome(); }); await tick(o.page, 800);
  st = await stories(o.page);
  ok(JSON.stringify(st.map(x => x.nm.split(' ')[0])) === '["Quinn","Avery","Rowan","Sky","Harper"]', 'Tue 3:30pm: no classes today, then done for the day (by name), then not set up', st.map(x => x.nm));
  ok(/done for the day/.test(by2(st, 'Avery').title) && /hm-now/.test(by2(st, 'Avery').cls), 'done for the day: green ring', by2(st, 'Avery'));
  await o.close();
  /* a work shift/other commitment (window.cmBlocks, added by another patch): Harper has Tue 10:00–11:00 */
  o = await desk({ tables: t, init: () => { let s = 12345; Math.random = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; }; } }); await tick(o.page, 2500); await ready(o.page);
  /* the real cmBlocks (website-commitments) is defined when the page loads and would replace one set in init; so it is stood in for after, in its own shape: meet-shaped blocks, a friend's as Busy */
  await o.page.evaluate(() => { window.cmBlocks = id => id === '22222225-2222-4222-8222-222222222225' ? [{ code: 'Busy', name: 'Busy', label: 'Busy', cm: 'friend', meet: { days: ['Tu'], start: 600, end: 660 } }] : []; });
  await o.page.evaluate(() => { show('home'); renderHome(); }); await tick(o.page, 800);
  st = await stories(o.page);
  ok(JSON.stringify(st.map(x => x.nm.split(' ')[0])) === '["Quinn","Sky","Avery","Harper","Rowan"]' && /hm-in/.test(by2(st, 'Harper').cls), 'with cmBlocks: a Tuesday shift makes Harper set up — in “class” till 11:00, ranked with the others, blue ring', st.map(x => x.nm + ' ' + x.cls));
  await o.close();
});
const by2 = (st, n) => st.find(x => x.nm.indexOf(n) === 0);

test('single', async () => {
  /* the single-term site: #hmFeed is byte-identical to the base commit's (same seed, same clock, same fixtures) */
  const get = async dir => {
    const prev = process.env.APP_DIR; process.env.APP_DIR = dir;
    try {
      const o = await desk({ init: SEED }); await tick(o.page, 2500);
      for (let i = 0; i < 30; i++) { if (await o.page.evaluate(() => !!document.querySelector('#hmFeed article.hm-card') && typeof friendsLoaded !== 'undefined' && friendsLoaded)) break; await tick(o.page, 300); }
      await o.page.evaluate(() => { show('home'); renderHome(); }); await tick(o.page, 1500);
      const r = await o.page.evaluate(() => ({ feed: document.getElementById('hmFeed').innerHTML, two: mcTwoTerms(), recs: !!document.querySelector('.hm-recs') }));
      const errs = o.log.errors.slice(); await o.close(); return Object.assign(r, { errs });
    } finally { process.env.APP_DIR = prev; }
  };
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'home-base-'));
  const repo = process.env.APP_DIR || process.cwd(), gitDir = process.env.SRC_DIR || repo;
  fs.writeFileSync(path.join(tmp, 'index.html'), execSync('git -C ' + JSON.stringify(gitDir) + ' show f72f221:index.html', { maxBuffer: 1 << 28 }));
  const b = await get(tmp), p = await get(repo);
  /* website-identity (2026-10-14): a person with no photo is the grey person now, not initials; read both sides alike */
  const NF = h => h.replace(/<svg class="nophoto"[\s\S]*?<\/svg>/g, '@@NOPH@@').replace(/background:var\(--nophoto\)/g, 'background:#CBCBD0')
    .replace(/onerror="this\.(replaceWith\(document\.createTextNode\('[A-Z?]*'\)\)|outerHTML=NOPH_SVG)"/g, 'onerror="@@"')
    .replace(/(style="background:#CBCBD0">)[A-Z?]{1,3}(<\/)/g, '$1@@NOPH@@$2')
    .replace(/ referrerpolicy="no-referrer"/g, '');   /* security-pass2 (2026-10-15): every avatar <img> is no-referrer now; the base commit's has no such attribute */
  b.feed = NF(b.feed); p.feed = NF(p.feed);
  ok(!p.two && !p.recs && p.feed.length > 500, 'single term: one term, no “friends are planning” row', { two: p.two, recs: p.recs, n: p.feed.length });
  ok(b.feed === p.feed, 'single term: #hmFeed HTML is identical to the base commit’s', b.feed === p.feed ? '' : { base: b.feed.length, now: p.feed.length, at: [...b.feed].findIndex((c, i) => c !== p.feed[i]) });
  ok(p.errs.length === 0, 'single: no page errors', p.errs);
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-home: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
