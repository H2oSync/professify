/* check-desktop-terms — the website's wall between the two terms (website-spring-wall, Tate 2026-10-14: "do the fall /
   spring"). Runs the REAL index.html in Chromium, signed in, against the same PostgREST stand-in as check-app.
   Run: APP_DIR=<repo> node check-desktop-terms.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises, the phone's (spring-wall 2026-10-08): Spring 2027 is the term you choose in — the seat feed, Explore,
   My Classes you add to, every write; Fall 2026 is the term you are in — Home, your week now, friends' weeks, who is in
   class, Rate's current professors. They never mix: a Fall class never takes a Spring section's time, and a Spring
   class never shows up on the week someone is in now. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 400) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000 }, o));
const T = {};
const test = (name, fn) => { T[name] = fn; };

const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25' };
/* Spring reuses Fall's class numbers on purpose (the wall must keep them apart); BUS 3438 isn't offered in Spring and
   BUS 3431's Spring sections meet at another time. You have one Spring class (BUS 4401); Avery has one (BUS 4401). */
function springTables() {
  const T = JSON.parse(JSON.stringify(FX.TABLES));
  const spring = T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' }, r.course_code === 'BUS 3431' ? { days: 'FrSa 6:10PM - 9:00PM' } : {}));
  T.course_seats = T.course_seats.concat(spring);
  const ph = spring.find(r => r.course_code === 'BUS 4401');
  for (const uid of [FX.ME.id, FX.FRIENDS[0].id]) {
    T.saved_classes.push({ user_id: uid, term: '2274', code: 'BUS 4401', class_nbr: ph.class_nbr, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null });
    T.my_sections.push({ user_id: uid, term: '2274', code: 'BUS 4401', class_nbr: ph.class_nbr, section: ph.section, instructor: ph.instructor, days: ph.days, status: 'enrolled', wl_pos: null });
  }
  return T;
}
const fallCodes = FX.TABLES.saved_classes.filter(r => r.user_id === FX.ME.id && r.term === '2268').map(r => r.code).sort();

/* What "right now" looks like on the single-term site, to compare the wall against. */
const NOW_PROBE = () => ({
  two: mcTwoTerms(),
  mine: nowMine().classes.slice().sort(),
  friends: friendsList.map(f => ({ id: f.id, codes: (hmFriendMeets(frNow(f)).meets || []).filter(m => m.meet && !m.assumed).map(m => m.code + '@' + m.meet.days.join('') + m.meet.start).sort() })),
  states: friendsList.map(f => avState(avMeetsOf(f), new Date()).state),
  myWeek: avMyMeets().map(m => m.code + '@' + m.meet.days.join('') + m.meet.start).sort(),
  busy: friendsList.map(f => { const r = gpMemberBusy({ id: f.id }); return r.noData ? 'none' : r.busy.length; }),
  curProfs: rlMyProfs().filter(x => x.now).map(x => x.p.name).sort(),
});

test('single', async () => {
  const { page, close, log } = await desk(); await tick(page, 1500);
  const r = await page.evaluate(() => ({ two: mcTwoTerms(), t: mcTerm(), n: mcNowTerm(), same: nowMine().classes === myClasses, f: friendsList.length && frNow(friendsList[0]) === friendsList[0] }));
  ok(!r.two && r.t === '2268' && r.n === '2268' && r.same && r.f, 'single term: every helper is the site it was (nowMine is My Classes, frNow(f) is f)', r);
  ok(!(await page.$('#watchMineOut > .mc-terms')), 'single term: no term chips on My Classes');
  ok(log.errors.length === 0, 'single term: no page errors', log.errors);
  await close();
});

test('wall', async () => {
  let o = await desk({ tables: springTables() }); await tick(o.page, 1500);
  await o.page.evaluate(() => loadFriendsData()); await tick(o.page, 1500);
  const before = await o.page.evaluate(NOW_PROBE);
  await o.close();
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  await page.evaluate(() => loadFriendsData()); await tick(page, 1500);
  const w = await page.evaluate(() => ({
    two: mcTwoTerms(), t: mcTerm(), n: mcNowTerm(), nl: mcNowLabel(),
    feed38: !!(SEAT_SECTIONS && SEAT_SECTIONS['BUS 3438']), b31: (SEAT_SECTIONS['BUS 3431'] || []).map(r => r.days),
    mine: myClasses.slice().sort(), nowMine: NOW_MINE.classes.slice().sort(), loaded: NOW_MINE.loaded,
    nowSeats: Object.keys(NOW_SEATS).sort(),
    wanted: (function () { const o = NOW_MINE.classes.slice(); friendsList.forEach(f => (frNow(f).classes || []).forEach(c => { if (!o.includes(c)) o.push(c); })); return o.sort(); })(),
  }));
  ok(w.two && w.t === '2274' && w.n === '2268' && w.nl === 'Fall 2026', 'wall: two terms — choose in Spring 2027, now is Fall 2026', w);
  ok(!w.feed38 && w.b31.every(d => d === 'FrSa 6:10PM - 9:00PM'), 'wall: the seat feed is Spring’s alone — a Fall-only class is not in it, Spring’s own times', w);
  ok(JSON.stringify(w.mine) === '["BUS 4401"]', 'wall: My Classes is your Spring list', w.mine);
  ok(w.loaded && JSON.stringify(w.nowMine) === JSON.stringify(fallCodes), 'wall: your Fall classes are read by term into the now list', { got: w.nowMine, want: fallCodes });
  ok(w.nowSeats.length > 0 && JSON.stringify(w.nowSeats) === JSON.stringify(w.wanted), 'wall: Fall seat rows are held for exactly the courses someone here is in now', { held: w.nowSeats, wanted: w.wanted });
  const reads = log.reads.map(r => decodeURIComponent(r));
  const fallSeat = reads.filter(r => /^course_seats\?term=eq\.2268/.test(r)), springSeat = reads.filter(r => /^course_seats\?term=eq\.2274/.test(r));
  ok(springSeat.length > 0 && fallSeat.length > 0 && fallSeat.every(r => /course_code=in\.\(/.test(r)), 'wall: Spring’s whole list is read; Fall only by the courses people are in', { fall: fallSeat.slice(0, 2) });
  const mySec = reads.filter(r => /^my_sections\?/.test(r));
  ok(mySec.length > 0 && mySec.every(r => /term=eq\.(2268|2274)/.test(r)), 'wall: every my_sections read names its term (a friend’s was term-blind)', mySec.filter(r => !/term=eq/.test(r)));
  const after = await page.evaluate(NOW_PROBE);
  ok(JSON.stringify(after.friends) === JSON.stringify(before.friends), 'home: friends’ weeks are the term they’re in — the same as the single-term site, and no Spring class on them', { before: before.friends, after: after.friends });
  ok(!JSON.stringify(after.friends).includes('BUS 4401'), 'home: Avery’s Spring class is not on the week she’s in now');
  ok(JSON.stringify(after.states) === JSON.stringify(before.states) && JSON.stringify(after.busy) === JSON.stringify(before.busy), 'home: who’s in class now and group free time read Fall, as before', { before: [before.states, before.busy], after: [after.states, after.busy] });
  ok(JSON.stringify(after.myWeek) === JSON.stringify(before.myWeek.filter(x => !/^BUS 4401@/.test(x))), 'home: your week now is your Fall week (and never your Spring class)', { before: before.myWeek, after: after.myWeek });
  ok(after.curProfs.length > 0 && JSON.stringify(after.curProfs) === JSON.stringify(before.curProfs), 'rate: the professors you have now are Fall’s — the same as the single-term site', { before: before.curProfs, after: after.curProfs });
  await page.evaluate(() => { show('home'); renderHome(); }); await tick(page, 600);
  const feed = await page.evaluate(() => { const h = document.getElementById('hmFeed'); const s = document.getElementById('hmStripWrap'); return { n: h ? h.querySelectorAll('article.hm-card').length : 0, txt: h ? h.innerText : '', has4401: h ? [...h.querySelectorAll('article.hm-card')].filter(a => /4401/.test(a.innerText)).map(a => a.getAttribute('data-fid')) : null }; });
  /* website-home-catchup (2026-10-14): a card shows the newest real thing — Avery has a Spring class, so hers is Spring; the others are Fall weeks */
  ok(feed.n > 0 && JSON.stringify(feed.has4401) === JSON.stringify([FX.FRIENDS[0].id]), 'home: the feed draws each friend’s newest thing — Avery’s Spring class on her card only; everyone else’s week now', { n: feed.n, has4401: feed.has4401 });
  const card = await page.evaluate(id => { const f = friendsList.find(x => x.id === id); const h = hmFriendSchedCard(f, { force: true }); return { spring: /4401/.test(h), n: (h.match(/BUS \d{4}|\b\d{4}\b/g) || []).length }; }, FX.FRIENDS[0].id);
  ok(card.spring && card.n > 0, 'home: a card opened on its own (a settled row expanded) is the same view as in the feed (Avery: her Spring class)', card);
  const cal = await page.evaluate(() => { const h = hmMiniCalHtml(); return { tag: /hm-termtag[^>]*>Fall 2026</.test(h), b38: /3438/.test(h), b01: />4401</.test(h) }; });
  ok(cal.tag && cal.b38 && !cal.b01, 'home: “My schedule” is your Fall week, tagged Fall 2026', cal);
  /* My Classes: Fall 2026 · Spring 2027 — opens on Spring (you have a Spring class); Fall is read-only */
  await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} renderMyClasses(); }); await tick(page, 600);
  let mc = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#watchMineOut > .mc-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')), add: !!document.querySelector('#watchMineOut .mc-addbtn'), txt: document.getElementById('watchMineOut').innerText }));
  ok(mc.chips.join('|') === 'Fall 2026|Spring 2027*' && mc.add && /4401/.test(mc.txt) && !/3438/.test(mc.txt), 'my classes: Fall 2026 · Spring 2027, open on Spring — the list you add to', mc);
  ok(await page.evaluate(() => (document.getElementById('schedTerm') || {}).textContent) === 'Spring 2027', 'my classes: the header names Spring 2027 over the Spring list');
  await page.evaluate(() => mcSetTermView('now')); await tick(page, 600);
  mc = await page.evaluate(() => ({ chips: [...document.querySelectorAll('#watchMineOut > .mc-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')), add: !!document.querySelector('#watchMineOut .mc-addbtn'), note: (document.querySelector('.mc-now-note') || {}).textContent || '', blocks: [...document.querySelectorAll('#watchMineOut .mc-cal-now [onclick*="cbTap"]')].length, txt: document.getElementById('watchMineOut').innerText }));
  ok(await page.evaluate(() => (document.getElementById('schedTerm') || {}).textContent) === 'Fall 2026', 'my classes: …and Fall 2026 over the Fall week');
  ok(mc.chips.join('|') === 'Fall 2026*|Spring 2027' && !mc.add && /Read-only/.test(mc.note) && mc.blocks > 0 && /3438/.test(mc.txt) && !/4401/.test(mc.txt), 'my classes: Fall shows your week now, read-only, nothing to add', mc);
  /* a friend's page: Fall · Spring, opens on now */
  await page.evaluate(id => openFriendProfile(id), FX.FRIENDS[0].id); await tick(page, 600);
  let fp = await page.evaluate(() => ({ chips: [...document.querySelectorAll('.frp-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')), txt: document.getElementById('frpModal').innerText }));
  ok(fp.chips.join('|') === 'Fall 2026*|Spring 2027' && !/BUS 4401/.test(fp.txt), 'friend page: Fall 2026 · Spring 2027, open on their week now (no Spring class on it)', fp.chips);
  await page.evaluate(() => setFrpTerm('term')); await tick(page, 500);
  fp = await page.evaluate(() => ({ chips: [...document.querySelectorAll('.frp-terms button')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')), txt: document.getElementById('frpModal').innerText }));
  ok(fp.chips.join('|') === 'Fall 2026|Spring 2027*' && /BUS 4401/.test(fp.txt), 'friend page: Spring shows their Spring classes', fp.chips);
  await page.evaluate(() => closeFriendProfile()); await tick(page, 300);
  const misc = await page.evaluate(id => ({ next: friendNextTogether(friendsList.find(x => x.id === id)) || '', taking: myTakingCodes().slice().sort(), enrolled: enrolledNowCodes().slice().sort() }), FX.FRIENDS[0].id);
  ok(!/4401/.test(misc.next), 'friends: “together tomorrow” is a Fall class you share, never a Spring one (Spring hasn’t started)', misc.next);
  ok(misc.taking.includes('BUS 4401') && misc.taking.includes('BUS 3438') && misc.enrolled.includes('BUS 4401') && misc.enrolled.includes('BUS 3438'), 'requirements: “taking” is both terms — Fall in progress and Spring registered', misc);
  /* every write is Spring's */
  log.writes.length = 0;
  await page.evaluate(() => toggleMyClass('BUS 3346', null)); await tick(page, 1200);
  const wr = log.writes.filter(x => x.table === 'saved_classes' || x.table === 'my_sections').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).filter(Boolean);
  ok(wr.length > 0 && wr.every(r => r.term === '2274'), 'wall: adding a class writes Spring’s row', wr);
  log.writes.length = 0;
  await page.evaluate(() => { wlOpen('BUS 4401'); wlGotIn(); }); await tick(page, 800);
  const wl = log.writes.filter(x => x.table === 'saved_classes').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).filter(Boolean).filter(x => 'waitlist_pos' in x);
  ok(wl.length >= 1 && wl.every(x => x.term === '2274'), 'wall: a waitlist position is written to its term (it had none)', wl);
  ok(log.errors.length === 0, 'wall: no page errors', log.errors);
  await close();
});

test('nowTimes', async () => {
  /* A Fall class you saved by class number with no section row: its time is FALL's section with that number — never
     Spring's section with the same number (Spring reuses Fall's numbers here), and never Spring's first section. */
  const T = springTables();
  T.my_sections = T.my_sections.filter(r => !(r.user_id === FX.ME.id && r.term === '2268' && r.code === 'BUS 3431'));
  const fall = FX.TABLES.course_seats.find(r => r.course_code === 'BUS 3431' && r.section === '01');
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: T }); await tick(page, 2500);
  const r = await page.evaluate(() => { const m = avMyMeets().filter(x => x.code === 'BUS 3431'); return { crn: (NOW_MINE.meta['BUS 3431'] || {}).crn, meets: m.map(x => x.meet.days.join('') + ' ' + x.meet.start + '-' + x.meet.end) }; });
  ok(r.crn === fall.class_nbr && JSON.stringify(r.meets) === '["MoWe 970-1080"]', 'times: a Fall class known only by its number takes Fall’s section time (MoWe 4:10–6:00), not Spring’s (FrSa)', r);
  ok(log.errors.length === 0, 'times: no page errors', log.errors);
  await close();
});

test('staleLocal', async () => {
  /* This device's lists are the term's own keys: Fall's (the old names) are never read as Spring's, and an old tab
     still open on Fall, writing Fall's keys after the new page loaded, can't reach Spring either. */
  const fallList = JSON.stringify(['BUS 3438', 'PHIL 3331', 'ZZZ 1000']);
  const init = `try{if(!sessionStorage.getItem('once')){sessionStorage.setItem('once','1');localStorage.setItem('professify_my_classes',${JSON.stringify(fallList)});localStorage.setItem('professify_mc_pending',JSON.stringify({'ZZZ 1000':{op:'add',at:Date.now()}}));localStorage.setItem('professify_seats_cache','{"ts":1,"idx":{},"sec":{}}');}}catch(e){}`;
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables(), init }); await tick(page, 2500);
  let r = await page.evaluate(() => ({ mine: myClasses.slice().sort(), fallKept: localStorage.getItem('professify_my_classes'), springKey: JSON.parse(localStorage.getItem('professify_my_classes:2274') || '[]'), oldCache: localStorage.getItem('professify_seats_cache') }));
  ok(JSON.stringify(r.mine) === '["BUS 4401"]' && JSON.stringify(r.springKey) === '["BUS 4401"]' && r.oldCache === null, 'device: Spring’s list is its own key — the Fall list on this device is not shown as Spring', r);
  ok(r.fallKept === fallList, 'device: Fall’s local list is left alone, not purged (an old Fall tab keeps working)', r.fallKept);
  /* an old tab, still on the old page, rewrites Fall's keys after this one loaded */
  await page.evaluate(l => { localStorage.setItem('professify_my_classes', l); localStorage.setItem('professify_mc_pending', JSON.stringify({ 'PHIL 3331': { op: 'add', at: Date.now() } })); }, fallList);
  await page.reload(); await tick(page, 2500);
  r = await page.evaluate(() => ({ mine: myClasses.slice().sort() }));
  const wr = log.writes.filter(x => x.table === 'saved_classes').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).filter(Boolean);
  ok(JSON.stringify(r.mine) === '["BUS 4401"]', 'device: after an old Fall tab writes, Spring still loads Spring', r);
  ok(!wr.some(x => ['BUS 3438', 'PHIL 3331', 'ZZZ 1000'].includes(x.code)), 'device: nothing from Fall’s local list or queue is written to Spring', wr);
  ok(log.errors.length === 0, 'device: no page errors', log.errors);
  await close();
  /* and the single-term site keeps a device's list exactly where it was */
  const o2 = await desk({ init: `try{if(!sessionStorage.getItem('x')){sessionStorage.setItem('x','1');localStorage.setItem('professify_watch_classes',JSON.stringify(['ZZZ 1000']));}}catch(e){}` }); await tick(o2.page, 1500);
  const r2 = await o2.page.evaluate(() => ({ kept: watchClasses.includes('ZZZ 1000'), key: MC_LS('professify_watch_classes') }));
  ok(r2.kept && r2.key === 'professify_watch_classes', 'device: on Fall alone the keys are the old ones and nothing local is dropped', r2);
  await o2.close();
});

test('dprTwoTerms', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables() }); await tick(page, 2500);
  log.writes.length = 0;
  await page.evaluate(async () => {
    tiRows = [{ _dpr: true, _now: true, pick: true, code: 'BUS 4488', cur: 'BUS 4488', term: 'Fall', year: 2026, known: true },
              { _dpr: true, _reg: true, pick: true, code: 'BUS 4442', cur: 'BUS 4442', term: 'Spring', year: 2027, known: true },
              { _dpr: true, pick: true, code: 'BUS 2201', cur: 'BUS 2201', term: 'Spring', year: 2026, known: true }];
    await confirmDprImport();
  }); await tick(page, 1500);
  const sv = log.writes.filter(x => x.table === 'saved_classes').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).filter(Boolean);
  const hi = log.writes.filter(x => x.table === 'class_history').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).filter(Boolean);
  ok(sv.some(r => r.code === 'BUS 4488' && r.term === '2268') && sv.some(r => r.code === 'BUS 4442' && r.term === '2274') && !sv.some(r => r.code === 'BUS 4488' && r.term === '2274'), 'dpr: in progress goes to your Fall classes, registered for Spring to My Classes (Spring)', sv);
  ok(hi.length === 1 && hi[0].code === 'BUS 2201', 'dpr: only finished classes go to Past Classes — Fall’s in-progress ones are not filed as finished', hi);
  const r = await page.evaluate(() => ({ now: NOW_MINE.classes.includes('BUS 4488'), mine: myClasses.includes('BUS 4442') && !myClasses.includes('BUS 4488') }));
  ok(r.now && r.mine, 'dpr: each lands in its own list on screen', r);
  ok(log.errors.length === 0, 'dpr: no page errors', log.errors);
  await close();
});

test('dprReport', async () => {
  /* The real report, read on the website: printed Oct 25 with Fall in progress and Spring registered (files/make-dpr-two-terms.py).
     Before the wall, "this term" was the newest term on it — Spring — and Fall's in-progress classes went to Past Classes. */
  const T = springTables(); T.class_history = T.class_history.filter(r => r.user_id !== FX.ME.id);
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: T, time: '2026-10-25T12:00:00-07:00' }); await tick(page, 2500);
  await page.locator('#transcriptFile').setInputFiles('files/dpr-two-terms.pdf');
  for (let i = 0; i < 60 && !(await page.locator('#tiModal .ti-row').count()); i++) await tick(page, 500);
  const r = await page.evaluate(() => { const m = document.getElementById('tiModal');
    return { now: [...m.querySelectorAll('.ti-row.ti-now .hc')].map(e => e.innerText.trim()).sort(), groups: [...m.querySelectorAll('.ti-grp b')].map(e => e.textContent),
      btn: (([...m.querySelectorAll('button')].find(b => /^Add \d+ to Past Classes/.test(b.innerText.trim())) || {}).innerText || '').trim() }; });
  ok(JSON.stringify(r.now) === '["BUS 2201","COMS 1101"]', 'report: Fall’s ungraded classes are in progress now — not finished, not Spring', r.now);
  ok(r.groups.includes('Fall 2026 · in progress') && r.groups.includes('Spring 2027 · registered') && r.groups.includes('Already finished'), 'report: three groups — finished, Fall in progress, Spring registered', r.groups);
  ok(r.btn === 'Add 4 to Past Classes, 2 to Fall 2026 and 2 to Spring 2027', 'report: the button says where each goes', r.btn);
  await page.evaluate(() => [...document.querySelectorAll('#tiModal button')].find(b => /^Add \d+ to Past Classes/.test(b.innerText.trim())).click());
  for (let i = 0; i < 20 && !log.writes.some(w => w.table === 'class_history'); i++) await tick(page, 400);
  await tick(page, 800);
  const sv = log.writes.filter(x => x.table === 'saved_classes').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).filter(Boolean).map(x => x.code + '@' + x.term).sort();
  const hi = log.writes.filter(x => x.table === 'class_history' && x.m === 'POST').flatMap(x => Array.isArray(x.body) ? x.body : [x.body]).map(x => x.code).sort();
  const nm = await page.evaluate(() => NOW_MINE.classes.slice());
  ok(['COMS 1101@2268', 'BUS 2207@2274', 'BUS 2212@2274'].every(x => sv.includes(x)) && !sv.some(x => /^(BUS 2201|COMS 1101)@2274/.test(x)) && !sv.includes('BUS 2201@2268') && nm.includes('BUS 2201') && nm.includes('COMS 1101'),
    'report: Fall in progress saved to Fall (BUS 2201 was already there), Spring registered to Spring', { sv, nm });
  ok(JSON.stringify(hi) === '["BUS 1100","ECON 2030","ENGL 1134","STAT 2170"]', 'report: only the graded classes go to Past Classes', hi);
  ok(log.errors.length === 0, 'report: no page errors', log.errors);
  await close();
});

test('shipped', async () => {
  /* the config that ships, not a copy of it */
  const { page, close, log } = await desk({ terms: 'live' }); await tick(page, 1500);
  const r = await page.evaluate(() => ({ t: mcTerm(), tl: mcTermLabel(), n: mcNowTerm(), nl: mcNowLabel(), u: PROFESSIFY_CONFIG.NOW_UNTIL, two: mcTwoTerms() }));
  ok(r.t === '2274' && r.tl === 'Spring 2027' && r.n === '2268' && r.nl === 'Fall 2026' && r.u === '2027-01-25' && r.two, 'shipped: choose in Spring 2027 (2274), now Fall 2026 (2268) until 2027-01-25', r);
  ok(log.errors.length === 0, 'shipped: no page errors', log.errors);
  await close();
});

test('nowUntil', async () => {
  { const { page, close } = await desk({ terms: SPRING_CFG, tables: springTables(), time: '2027-01-24T23:30:00-08:00' }); await tick(page, 1500);
    const r = await page.evaluate(() => ({ two: mcTwoTerms(), n: mcNowTerm() }));
    ok(r.two && r.n === '2268', 'the evening before Spring starts (Pacific), now is still Fall', r); await close(); }
  /* From Spring's first day of classes, "now" is Spring and the site is single-term again — no manual flip. */
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: springTables(), time: '2027-01-25T09:00:00-08:00' }); await tick(page, 1500);
  const r = await page.evaluate(() => ({ two: mcTwoTerms(), n: mcNowTerm(), same: nowMine().classes === myClasses }));
  ok(!r.two && r.n === '2274' && r.same, 'from Jan 25 (Pacific) now is Spring — one term again', r);
  await page.evaluate(() => { show('home'); renderHome(); show('sched'); try { setSchedTab('mine'); } catch (e) {} renderMyClasses(); }); await tick(page, 600);
  ok(!(await page.$('#watchMineOut > .mc-terms')) && /4401/.test(await page.evaluate(() => document.getElementById('watchMineOut').innerText)), 'from Jan 25 My Classes is just Spring, no chips', null);
  ok(log.errors.length === 0, 'nowUntil: no page errors', log.errors);
  await close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 300)); }
}
console.log(`\ncheck-desktop-terms: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
