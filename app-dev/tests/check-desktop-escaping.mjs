/* check-desktop-escaping — a FRIEND's class code / crn / term / year can no longer break out of the website (security-escaping, 2026-10-14).
   Runs the REAL index.html in Chromium, signed in, against the PostgREST stand-in. NOTHING is clicked and no handler is ever run:
   every inline handler the page generated is PARSED with acorn, and the poisoned value must be one string argument (no identifier MARK
   outside a string, no stray statement). Markup is checked by looking for a real <b>Bold</b> element.
   Two layers, because the fix has two layers:
     door — poisoned rows arrive through the API (saved_classes, my_sections, class_history); the page must drop / coerce them
            before they reach memory, and must still show the real codes (CSC 1001L, A&B 123).
     use  — the poison is put INTO memory (bypassing the door) and every surface that prints it must still escape it.
   Run: APP_DIR=<repo> node check-desktop-escaping.mjs [--only name] [--quiet]   (APP_PORT, default 8420)  */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import * as acorn from '/opt/npm-tools/node_modules/acorn/dist/acorn.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const BASE_PORT = +(process.env.APP_PORT || 8420);
let portN = 0;
/* frNow(f) caches its view on the friend (f.__nowView); the test puts poison INTO a friend and renders, so the cache is switched off. */
const desk = async (o = {}) => {
  const r = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 3500, port: BASE_PORT + (portN++ % 10), time: '2026-10-14T10:30:00-07:00' }, o));
  await r.page.evaluate(() => { const orig = window.frNow; window.frNow = function (f) { if (f) delete f.__nowView; return orig(f); }; });
  return r;
};
const clone = o => JSON.parse(JSON.stringify(o));
const T = {};
const test = (name, fn) => { T[name] = fn; };
const FR = FX.FRIENDS.map(f => f.id);

/* What a hostile friend stores. All ≤ 40 characters, all uppercase-safe (the page upper-cases codes). */
const P_HTML = 'Q 1"><b>Bold</b>';            // breaks out of an attribute and makes an element
const P_JS = "Z 9');MARK;//";                // ends a JS string argument
const P_BS = 'X 7\\';                         // a trailing backslash that would eat the closing quote
const C_JS = "1');MARK;//";                  // a hostile crn
const C_ATTR = '1"onmouseover="MARK';        // a hostile crn that closes the attribute
const POISONS = [P_HTML, P_JS, P_BS];
const same = (a, b) => String(a).toUpperCase().replace(/\s+/g, ' ').trim() === String(b).toUpperCase().replace(/\s+/g, ' ').trim();

/* ---- browser side: every inline handler that mentions the poison, and every real element a poisoned string could have made ---- */
const SNAP = () => {
  const handlers = [];
  document.querySelectorAll('*').forEach(el => { for (const a of el.attributes) if (/^on/i.test(a.name) && /mark|bold/i.test(a.value)) handlers.push({ name: a.name, tag: el.tagName.toLowerCase(), cls: String(el.className).split(' ')[0], value: a.value }); });
  const bolds = [...document.querySelectorAll('b,strong,i,em,u,span,div')].filter(e => e.children.length === 0 && /^bold$/i.test(e.textContent.trim()) && e.tagName !== 'SPAN' && e.tagName !== 'DIV').map(e => e.parentElement.tagName.toLowerCase() + '.' + String(e.parentElement.className).split(' ')[0]);
  const injected = [...document.querySelectorAll('[onmouseover]')].map(e => e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]);
  return { handlers, bolds, injected, lit: (document.body.innerText.match(/<b>Bold<\/b>/gi) || []).length };
};
/* node side: parse a handler. Returns { parses, breakout, args } — breakout = the marker identifier appears outside a string literal. */
function judge(h) {
  let ast;
  try { ast = acorn.parse('(function(){' + h.value + '\n})', { ecmaVersion: 'latest' }); } catch (e) { return { parses: false, err: e.message }; }
  let breakout = false; const lits = [];
  (function w(n) { if (!n || typeof n !== 'object') return; if (n.type === 'Identifier' && /^mark$/i.test(n.name)) breakout = true; if (n.type === 'Literal' && typeof n.value === 'string') lits.push(n.value); for (const k in n) if (k !== 'type' && k !== 'start' && k !== 'end') w(n[k]); })(ast);
  return { parses: true, breakout, lits };
}
/* Every handler that carries poison must parse, must not contain code outside a string, and must carry a poisoned string whole. */
function judgeAll(label, snap, expectWhole) {
  const bad = []; let whole = 0;
  for (const h of snap.handlers) {
    const j = judge(h);
    if (!j.parses) bad.push({ why: 'syntax', h: h.value.slice(0, 120), err: j.err });
    else if (j.breakout) bad.push({ why: 'code outside the string', h: h.value.slice(0, 120) });
    else if (j.lits.some(l => POISONS.concat([C_JS, C_ATTR]).some(p => same(l, p)))) whole++;
  }
  ok(bad.length === 0, `${label}: every inline handler parses, with the poison inside one string (${snap.handlers.length} handlers checked)`, bad.slice(0, 3));
  ok(snap.bolds.length === 0, `${label}: no real <b>Bold</b> element was created`, snap.bolds);
  ok(snap.injected.length === 0, `${label}: no element grew an onmouseover attribute`, snap.injected);
  if (expectWhole) ok(whole >= expectWhole, `${label}: at least ${expectWhole} handler(s) carry the poisoned value whole, as an argument (${whole})`, { whole, n: snap.handlers.length });
}

/* ==================================================================== the door */
function poisonedTables() {
  const t = clone(FX.TABLES);
  const add = (tbl, row) => t[tbl].push(row);
  /* real codes that must survive: a letter suffix and an & subject, and the ordinary ones the fixtures already have */
  add('saved_classes', { user_id: FR[0], term: '2268', code: 'CSC 1001L', class_nbr: null, created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
  add('saved_classes', { user_id: FR[0], term: '2268', code: 'a&b  123', class_nbr: null, created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
  /* the poison */
  add('saved_classes', { user_id: FR[1], term: '2268', code: P_HTML, class_nbr: null, created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
  add('saved_classes', { user_id: FR[2], term: '2268', code: P_JS, class_nbr: null, created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
  add('saved_classes', { user_id: FR[2], term: '2268', code: 'BUS 3346', class_nbr: C_JS, created_at: '2026-09-28T00:00:00Z', waitlist_pos: '<b>Bold</b>' });   // a real code with a hostile crn: kept, crn dropped
  add('my_sections', { user_id: FR[3], term: '2268', code: P_BS, class_nbr: C_ATTR, section: '01', instructor: 'Staff', days: 'TBA', status: 'enrolled', wl_pos: null });
  add('my_sections', { user_id: FR[2], term: '2268', code: 'BUS 3346', class_nbr: C_ATTR, section: '01', instructor: 'Staff', days: 'TBA', status: 'waitlisted', wl_pos: '<b>Bold</b>' });
  add('class_history', { user_id: FR[0], code: P_JS, term: 'Fall', year: 2025, professor: null });
  add('class_history', { user_id: FR[1], code: 'BUS 2201', term: '<b>Bold</b>', year: '<b>Bold</b>', professor: null });
  add('class_history', { user_id: FR[2], code: 'CSC 1001L', term: 'sPRING', year: '2024', professor: null });
  return t;
}
const MEM = () => JSON.stringify({ f: friendsList.map(f => ({ id: f.id, classes: f.classes, crns: f.crns, secs: f.secs, history: f.history, now: f.now })), F: FRIENDS.map(f => ({ classes: f.classes, secs: f.secs, history: f.history })) });

test('door', async () => {
  const { page, close, log } = await desk({ tables: poisonedTables() }); await tick(page, 1500);
  await page.evaluate(() => loadFriendsData()); await tick(page, 1500);
  const m = await page.evaluate(MEM);
  ok(!/MARK|<b>|Bold|"><|\);/i.test(m), 'door: no poisoned code, crn, term or year is held in memory', (m.match(/.{20}(MARK|<b>|Bold).{20}/i) || [])[0]);
  const r2 = await page.evaluate(ids => {
    const f = id => friendsList.find(x => x.id === id) || { classes: [], secs: [], history: [] };
    return { f0: f(ids[0]).classes, f2: f(ids[2]).classes, f2crns: f(ids[2]).secs.filter(s => s.code === 'BUS 3346').map(s => s.crn), f1h: f(ids[1]).history, f2h: f(ids[2]).history, f0h: f(ids[0]).history };
  }, FR);
  ok(r2.f0.includes('CSC 1001L'), 'door: a letter-suffix code (CSC 1001L) still comes through', r2.f0);
  ok(r2.f0.includes('A&B 123'), 'door: an & subject (a&b  123 → A&B 123) still comes through, normalised', r2.f0);
  ok(r2.f0.includes('BUS 3346') || r2.f0.length > 0, 'door: the friend’s ordinary classes are still there', r2.f0);
  ok(r2.f2.includes('BUS 3346') && r2.f2crns.every(c => c === '' || /^\d+$/.test(c)), 'door: a real code with a hostile crn keeps the class and loses the crn', { classes: r2.f2, crns: r2.f2crns });
  ok(!r2.f2.includes(P_JS.toUpperCase()), 'door: the hostile code is not in the friend’s classes', r2.f2);
  const h1 = r2.f1h.find(h => h.code === 'BUS 2201');
  ok(h1 && h1.term === '' && h1.year === '', 'door: a hostile term and year are blanked, the row stays', r2.f1h);
  const h2 = r2.f2h.find(h => h.code === 'CSC 1001L');
  ok(h2 && h2.term === 'Spring' && h2.year === 2024, 'door: term "sPRING" and year "2024" come out as Spring 2024 (number)', r2.f2h);
  ok(!r2.f0h.some(h => /MARK/i.test(h.code)), 'door: a history row with a hostile code is dropped', r2.f0h);
  /* and what the surfaces made of it */
  await page.evaluate(id => { openFriendProfile(id); }, FR[2]); await tick(page, 800);
  judgeAll('door: a friend’s profile', await page.evaluate(SNAP), 0);
  await page.evaluate(() => { try { closeFriendProfile(); } catch (e) {} show('home'); hmRenderFeed(); }); await tick(page, 800);
  judgeAll('door: Home', await page.evaluate(SNAP), 0);
  ok(log.errors.length === 0, 'door: no page errors', log.errors);
  await close();
});

/* the same door in the two-term site: a friend's now-term rows (Fall) and shared plans (Spring) */
test('doorNow', async () => {
  const tb = poisonedTables();
  tb.plans.push({ user_id: FR[1], term: '2274', slot: 'A', sections: [{ code: P_JS, class_nbr: '12345' }, { code: 'BUS 3346', class_nbr: C_JS }, { code: 'BUS 3438', class_nbr: '70001' }], shared: true });
  const { page, close, log } = await desk({ terms: 'live', tables: tb }); await tick(page, 2500);
  await page.evaluate(() => loadFriendsData()); await tick(page, 1500);
  await page.evaluate(() => TCPlans.loadFriendPlans()); await tick(page, 1200);
  const m = await page.evaluate(MEM);
  ok(!/MARK|<b>|Bold|"><|\);/i.test(m), 'doorNow: no poisoned code, crn, term or year is held in memory (their Fall week included)', (m.match(/.{20}(MARK|<b>|Bold).{20}/i) || [])[0]);
  const r = await page.evaluate(ids => {
    const f0 = friendsList.find(x => x.id === ids[0]), f2 = friendsList.find(x => x.id === ids[2]);
    return { n0: f0 && f0.now && f0.now.classes, n2: f2 && f2.now && f2.now.classes, c2: f2 && f2.now && f2.now.crns, plans: TCPlans.friendPlansOf(ids[1]).map(r => r.sections) };
  }, FR);
  ok(r.n0 && r.n0.includes('CSC 1001L') && r.n0.includes('A&B 123'), 'doorNow: their Fall week keeps CSC 1001L and A&B 123', r.n0);
  ok(r.n2 && r.n2.includes('BUS 3346') && (r.c2 || []).every(c => /^\d+$/.test(c)), 'doorNow: a real Fall code with a hostile crn keeps the class and loses the crn', r);
  ok(r.plans.length === 1 && r.plans[0].length === 1 && r.plans[0][0].code === 'BUS 3438', 'doorNow: a friend’s shared plan keeps only the entries with a course code and a numeric crn', r.plans);
  ok(log.errors.length === 0, 'doorNow: no page errors', log.errors);
  await close();
});

/* ==================================================================== the use: calendar rails on a friend's profile */
test('profileRails', async () => {
  for (const asyncRail of [false, true]) {
    const { page, close, log } = await desk(); await tick(page, 1200);
    await page.evaluate(([ids, P, C, forceAsync]) => {
      if (forceAsync) window.calIsAsync = function () { return true; };
      const f = friendsList.find(x => x.id === ids[0]);
      f.classes = f.classes.concat(P); f.secs = (f.secs || []).concat(P.map((c, i) => ({ code: c, crn: C[i % C.length] }))); f.crns = (f.crns || []).concat(C); f.now = null;
      const g = FRIENDS.find(x => x.id === ids[0]); if (g) { g.classes = f.classes; g.secs = f.secs; g.crns = f.crns; g.now = null; }
      openFriendProfile(ids[0]);
    }, [FR, POISONS, [C_JS, C_ATTR], asyncRail]);
    await tick(page, 1000);
    const s = await page.evaluate(SNAP);
    judgeAll(`profile calendar, ${asyncRail ? 'Async' : 'Time TBA'} rail`, s, 2);
    const rail = await page.evaluate(() => [...document.querySelectorAll('#frpBack .cal-anyblk')].map(e => e.getAttribute('onclick')));
    ok(rail.length >= 3, `profile calendar, ${asyncRail ? 'Async' : 'Time TBA'} rail: the three poisoned classes are drawn in the rail`, rail);
    ok(rail.length >= 3 && rail.every(h => { const j = judge({ value: h }); return j.parses && !j.breakout; }), `profile calendar, ${asyncRail ? 'Async' : 'Time TBA'} rail: each rail block's handler parses with no code outside a string`, rail);
    ok(log.errors.length === 0, 'profile rails: no page errors', log.errors);
    await close();
  }
});

/* ==================================================================== Home: chips and recommendations */
test('home', async () => {
  const { page, close, log } = await desk({ terms: 'live' }); await tick(page, 1500);
  /* chips: a friend with nothing placeable on the week shows their classes as chips (hmClassChips) */
  await page.evaluate(([ids, P]) => {
    const f = friendsList.find(x => x.id === ids[4]);
    f.classes = P.slice(); f.secs = []; f.crns = []; f.now = { classes: P.slice(), crns: [], secs: [], wl: {}, classAdds: [] };
    const g = FRIENDS.find(x => x.id === ids[4]); if (g) { g.classes = f.classes; g.secs = []; g.now = f.now; }
    show('home'); hmRenderFeed();
  }, [FR, POISONS]);
  await tick(page, 800);
  judgeAll('Home friend-card chips (hmClassChips)', await page.evaluate(SNAP), 3);
  const nChips = (await page.$$('.hm-chip')).length;
  ok(nChips >= 3, 'Home chips: the poisoned classes are drawn as chips', nChips);
  /* the recommendations row: classes friends are taking that the feed offers */
  await page.evaluate(([ids, P]) => {
    window._myHistOk = true;
    if (!SEAT_SECTIONS) SEAT_SECTIONS = {};
    P.forEach((c, i) => { SEAT_SECTIONS[c.toUpperCase()] = [{ class_nbr: '9' + i, section: '01', course_code: c.toUpperCase(), instructor: 'Staff', days: 'TBA' }]; });
    for (const id of [ids[3], ids[4]]) { const f = friendsList.find(x => x.id === id); f.now = { classes: P.map(c => c.toUpperCase()), crns: [], secs: [], wl: {}, classAdds: [] }; }
    show('home'); hmRenderFeed();
  }, [FR, POISONS]);
  await tick(page, 800);
  judgeAll('Home "classes your friends are taking" row (hmHomeRecsHtml)', await page.evaluate(SNAP), 3);
  const nRecs = (await page.$$('.hm-rec')).length;
  ok(nRecs === 3, 'Home recs row: the three poisoned classes are drawn', nRecs);
  /* a normal code renders and opens its class page */
  await page.evaluate(ids => { const f = friendsList.find(x => x.id === ids[4]); f.classes = ['BUS 3346']; f.secs = []; f.now = { classes: ['BUS 3346'], crns: [], secs: [], wl: {}, classAdds: [] }; show('home'); hmRenderFeed(); }, FR);
  await tick(page, 800);
  const txt = await page.evaluate(() => [...document.querySelectorAll('.hm-chip,.hm-rec')].map(e => e.innerText + '|' + e.getAttribute('onclick')).join('\n'));
  ok(/BUS 3346/.test(txt) && /openClassFromFeed\('BUS 3346'\)/.test(txt), 'Home: a normal code renders as written and its handler names it', txt.slice(0, 200));
  await page.evaluate(() => { const e = [...document.querySelectorAll('.hm-chip,.hm-rec')].find(x => /BUS 3346/.test(x.innerText)); e.click(); }); await tick(page, 800);
  const cp = await page.evaluate(() => ({ view: !!document.querySelector('#view-class') && getComputedStyle(document.querySelector('#view-class')).display !== 'none', txt: (document.querySelector('#view-class') || {}).innerText || '' }));
  ok(cp.view && /BUS 3346/.test(cp.txt), 'Home: a normal code opens its class page', cp.txt.slice(0, 80));
  ok(log.errors.length === 0, 'home: no page errors', log.errors);
  await close();
});

/* ==================================================================== the class page, for a poisoned code and for hostile crns */
test('classPage', async () => {
  const t = clone(FX.TABLES);
  const base = t.course_seats.find(r => r.course_code === 'BUS 3438' && r.term === '2268');
  /* the database itself offering a section row whose class number is hostile (a crn column that is text) */
  t.course_seats.push(Object.assign({}, base, { term: '2274', course_code: P_JS.toUpperCase(), class_nbr: C_JS, section: '01' }));
  t.course_seats.push(Object.assign({}, base, { term: '2274', course_code: P_JS.toUpperCase(), class_nbr: C_ATTR, section: '02' }));
  t.course_seats.push(Object.assign({}, base, { term: '2268', course_code: P_JS.toUpperCase(), class_nbr: C_JS, section: '01' }));
  const { page, close, log } = await desk({ terms: 'live', tables: t }); await tick(page, 2000);
  for (const code of POISONS) {
    await page.evaluate(c => { gotoSection(c); }, code); await tick(page, 1200);
    const s = await page.evaluate(SNAP);
    judgeAll(`class page for ${JSON.stringify(code)}`, s, /MARK/.test(code) ? 2 : 0);
  }
  /* the Save and Send buttons are the two the review named: they must be there and carry the code whole */
  await page.evaluate(c => { gotoSection(c); }, P_JS); await tick(page, 1200);
  const btns = await page.evaluate(() => [...document.querySelectorAll('#view-class .cp-save, #view-class .cp-send')].map(e => e.getAttribute('onclick')));
  ok(btns.length >= 2 && btns.every(h => { const j = judge({ value: h }); return j.parses && !j.breakout && j.lits.some(l => same(l, P_JS)); }), 'class page: the Save and Send buttons each pass the code as one string', btns);
  /* a normal class page still works: its handlers carry the ordinary code */
  await page.evaluate(() => { gotoSection('BUS 3346'); }); await tick(page, 1200);
  const n = await page.evaluate(() => ({ txt: document.querySelector('#view-class').innerText.slice(0, 200), save: (document.querySelector('#view-class .cp-save') || {}).getAttribute && document.querySelector('#view-class .cp-save').getAttribute('onclick') }));
  ok(/BUS 3346/.test(n.txt) && /toggleSaveClass\('BUS 3346'\)/.test(n.save || ''), 'class page: a normal code renders and its Save button names it', n);
  ok(log.errors.length === 0, 'class page: no page errors', log.errors);
  await close();
});

/* ==================================================================== "a friend took this", a friend's Took tab, the notification */
test('history', async () => {
  const { page, close, log } = await desk({ terms: 'live' }); await tick(page, 1800);
  await page.evaluate(ids => {
    const f = friendsList.find(x => x.id === ids[0]);
    f.history = [{ code: 'BUS 3346', term: '<b>Bold</b>', year: '<b>Bold</b>', professor: '', at: '2026-09-01T00:00:00Z' }];
    const g = FRIENDS.find(x => x.id === ids[0]); if (g) g.history = f.history;
    window.__multi = false;
    openClassPage('BUS 3346');
  }, FR); await tick(page, 1200);
  const s = await page.evaluate(SNAP);
  ok(s.bolds.length === 0 && s.lit >= 1, '"friend took this" chip: a hostile term and year are shown as text, not as an element', { bolds: s.bolds, lit: s.lit });
  const chip = await page.evaluate(() => (document.querySelector('#view-class .fr-chip-took') || {}).innerText || '');
  ok(/took this/.test(chip), '"friend took this" chip is there', chip);
  /* two friends took it: the "+1 other ... most recently <term year>" wording. Set and read in ONE call — a friends reload in between would put the fixtures back. */
  const s1b = await page.evaluate(ids => {
    ids.slice(0, 2).forEach(id => {
      const f = friendsList.find(x => x.id === id); f.history = [{ code: 'BUS 3346', term: '<b>Bold</b>', year: '<b>Bold</b>', professor: '', at: '2026-09-01T00:00:00Z' }];
      const g = FRIENDS.find(x => x.id === id); if (g) g.history = f.history;
    });
    openClassPage('BUS 3346');
    const c = document.querySelector('#view-class .fr-chip-took'); return { txt: c ? c.innerText : '', bolds: c ? c.querySelectorAll('b').length : -1 };
  }, FR);
  ok(/most recently/.test(s1b.txt) && s1b.bolds === 0 && /<b>Bold<\/b>/.test(s1b.txt), '"+1 other already took this, most recently ...": a hostile term and year are text', s1b);
  const s2 = await page.evaluate(id => {
    const f = friendsList.find(x => x.id === id); f.history = [{ code: 'BUS 3346', term: '<b>Bold</b>', year: '<b>Bold</b>', professor: '', at: '2026-09-01T00:00:00Z' }];
    const g = FRIENDS.find(x => x.id === id); if (g) g.history = f.history;
    openFriendProfile(id); profileTab = 'took'; renderFriendProfile();
    const b = document.getElementById('frpBack');
    return { lit: (b.innerText.match(/<b>Bold<\/b>/g) || []).length, bAll: [...b.querySelectorAll('b')].map(x => x.textContent), txt: b.innerText.slice(0, 300) };
  }, FR[0]);
  ok(!s2.bAll.some(x => /bold/i.test(x)) && s2.lit >= 1, 'friend profile "Already took": a hostile term and year are shown as text, not as an element', s2);
  /* the notification line: n.term / n.year */
  const nt = await page.evaluate(ids => {
    try { const f = friendsList.find(x => x.id === ids[0]); const fn = (typeof ntRowHtml === 'function') ? ntRowHtml : (typeof notifRowHtml === 'function' ? notifRowHtml : null); if (!fn) return { skip: true };
      return { html: fn({ kind: 'friend', type: 'took', who: f, code: 'BUS 3346', term: '<b>Bold</b>', year: '<b>Bold</b>', professor: '', at: '2026-09-01T00:00:00Z' }) }; } catch (e) { return { err: String(e) }; }
  }, FR);
  if (nt.skip) { ok(false, 'notification row: its renderer was found (ntRowHtml/notifRowHtml)', nt); }
  else { ok(!!nt.html && !/<b>Bold<\/b>/.test(nt.html) && /&lt;b&gt;Bold&lt;\/b&gt;/.test(nt.html), 'notification row: a hostile term and year are escaped', nt); }
  /* a normal term and year are shown as Term Year */
  await page.evaluate(id => { const f = friendsList.find(x => x.id === id); f.history = [{ code: 'BUS 3346', term: 'Spring', year: 2026, professor: '', at: '2026-09-01T00:00:00Z' }]; const g = FRIENDS.find(x => x.id === id); if (g) g.history = f.history; openClassPage('BUS 3346'); }, FR[0]); await tick(page, 800);
  ok(/Spring 2026/.test(await page.evaluate(() => (document.querySelector('#view-class .fr-chip-took') || {}).innerText || '')), '"friend took this": a normal term and year read "Spring 2026"');
  ok(log.errors.length === 0, 'history: no page errors', log.errors);
  await close();
});

/* ==================================================================== my own lists (My Classes / Watchlist rows), whose codes come from the database */
test('myClasses', async () => {
  const t = clone(FX.TABLES);
  t.saved_classes.push({ user_id: FX.ME.id, term: '2268', code: P_JS.toUpperCase(), class_nbr: null, created_at: '2026-09-28T00:00:00Z', waitlist_pos: 4 });
  t.saved_classes.push({ user_id: FX.ME.id, term: '2268', code: "Y 9');MARK;//", class_nbr: '70001', created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
  t.my_sections.push({ user_id: FX.ME.id, term: '2268', code: "Y 9');MARK;//", class_nbr: '70001', section: '01', instructor: 'Staff', days: 'TBA', status: 'waitlisted', wl_pos: 3 });
  t.saved_classes.push({ user_id: FX.ME.id, term: '2268', code: P_HTML.toUpperCase(), class_nbr: null, created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
  const { page, close, log } = await desk({ tables: t }); await tick(page, 1800);
  await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} setMyClassesView('list'); }); await tick(page, 1000);
  const have = await page.evaluate(() => /Z 9/.test(document.body.textContent));
  const s = await page.evaluate(SNAP);
  ok(have, 'My Classes: the poisoned saved classes are listed (so the rows below were really built)');
  judgeAll('My Classes rows', s, 4);
  ok(log.errors.length === 0, 'myClasses: no page errors', log.errors);
  await close();
});

/* ==================================================================== my own week: a timed block, the Async rail and the Time TBA rail, with hostile codes AND class numbers */
test('myCalendar', async () => {
  for (const asyncRail of [false, true]) {
    const t = clone(FX.TABLES);
    const row = (code, nbr, days) => {
      t.saved_classes.push({ user_id: FX.ME.id, term: '2268', code, class_nbr: nbr, created_at: '2026-09-28T00:00:00Z', waitlist_pos: null });
      t.my_sections.push({ user_id: FX.ME.id, term: '2268', code, class_nbr: nbr, section: '01', instructor: 'Staff', days, status: 'enrolled', wl_pos: null });
    };
    row("W 5');MARK;//", C_JS, 'MWF 10:10AM - 11:00AM');   // a timed block
    row("V 4');MARK;//", C_ATTR, 'TBA');                    // a rail block
    row(P_HTML.toUpperCase(), C_JS, 'TBA');
    const { page, close, log } = await desk({ tables: t }); await tick(page, 1800);
    if (asyncRail) await page.evaluate(() => { window.calIsAsync = function (c) { return /^[VQ] /.test(c); }; });
    await page.evaluate(() => { show('sched'); try { setSchedTab('mine'); } catch (e) {} setMyClassesView('calendar'); renderMyClasses(); }); await tick(page, 1000);
    const s = await page.evaluate(SNAP);
    const lab = `my calendar (${asyncRail ? 'Async' : 'Time TBA'} rail)`;
    judgeAll(lab, s, 3);
    const kinds = await page.evaluate(() => ({ timed: document.querySelectorAll('.cal-block.cb-tap:not(.cal-anyblk)').length, rail: document.querySelectorAll('.cal-anyblk').length }));
    ok(kinds.rail >= 2, `${lab}: the poisoned classes are drawn in the rail`, kinds);
    if (!asyncRail) ok(kinds.timed >= 1, `${lab}: and one on the grid at its hour`, kinds);
    /* the class number is passed as its own string argument, on the timed block and on the rail */
    const crnArgs = await page.evaluate(() => [...document.querySelectorAll('.cb-tap')].map(e => e.getAttribute('onclick')).filter(h => /mark/i.test(h)));
    const lits = crnArgs.map(h => judge({ value: h })).filter(j => j.parses && !j.breakout).flatMap(j => j.lits);
    ok(lits.some(l => same(l, C_JS)) && lits.some(l => same(l, C_ATTR)), `${lab}: both hostile class numbers arrive whole as a string argument`, lits);
    ok(log.errors.length === 0, 'myCalendar: no page errors', log.errors);
    await close();
  }
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-escaping: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
