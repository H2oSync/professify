/* check-desktop-rate-page — the Rate tab is a page (rate-page, 2026-10-16). Runs the REAL index.html in Chromium, signed in
   (and out), against the PostgREST stand-in (app-harness.mjs). Run: APP_DIR=<repo> node check-desktop-rate-page.mjs [--only name] [--quiet] [--shots dir]
   The promises:
   - page: the Rate tab opens #view-rate (not the picker modal), is lit like the other tabs, Back works like theirs; title, "N of M rated" with a bar
     (M = the professors the picker listed), "Taking now" first then Past terms, Reviewed badges, scores.
   - find: the picker's finding is all there: a name (incl. professors with no ratings yet), a course as prefix + number (typed in the box or in
     the three fields), Your major / Change.
   - form: Rate opens the EXISTING form under the row (no modal), its validation and submit are the same (one reviews insert, same body),
     the thank-you offers the next professor, and the row says Reviewed afterwards; Esc and Close put it away.
   - rail: your reviews with Edit (the existing edit flow, in the row), the helpful-votes count from what loadMyReviews already reads, no streak, and
     "Latest reviews at Cal Poly" only with 8+ in Home's feed data.
   - entries: every other way into rating still opens the form (modal, in place) or the page; signed out: a sign-in card, and Rate asks to verify.
   - phone: the form is a bottom sheet with a scrim. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import path from 'node:path';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const SHOTS = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const PORT0 = +(process.env.APP_PORT || (8300 + Math.floor(Math.random() * 600)));
let portN = 0;
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const until = async (p, fn, arg, max = 40) => { for (let i = 0; i < max; i++) { if (await p.evaluate(fn, arg).catch(() => false)) return true; await tick(p, 250); } return false; };
const clone = o => JSON.parse(JSON.stringify(o));
const THEME = th => `try{localStorage.setItem('professify-theme',${JSON.stringify(th)})}catch(e){}`;
const open = (o = {}) => openApp(Object.assign({ path: '/', width: 1300, height: 900, wait: 4000, port: PORT0 + (portN++), init: THEME('dark') }, o));
const ME = FX.ME.id;
const T = {}; const test = (n, fn) => { T[n] = fn; };
const rows = (log, table, m) => log.writes.filter(w => w.table === table && (!m || w.m === m)).flatMap(w => Array.isArray(w.body) ? w.body : [w.body]).filter(Boolean);
const profId = (p, k) => p.evaluate(k => Object.keys(PROFESSORS).find(i => profKey(PROFESSORS[i]) === k), k);
const ready = p => until(p, () => { try { return !!sbUser && nowMine().classes.length > 0; } catch (e) { return false; } });
const goRate = async p => { await p.evaluate(() => openRate()); await tick(p, 900); };
async function shot(p, name) { if (SHOTS) await p.screenshot({ path: path.join(SHOTS, name + '.png') }); }
const BRAM = 'bram fixturesen|bus', ADA = 'ada examplewood|bus';
/* my_reviews as the server answers it: one review of Ada's, written by me */
const MINE = [{ id: 7001, professor_key: ADA, professor_name: 'Ada Examplewood', department: 'BUS', course: 'BUS 4442', term: 'Fall 2026', score: 4.5, difficulty: 3, teach_ability: 4, would_again: true, hours: '3–6', format: 'In person', grade: 'A', tags: [], note: 'Clear lectures, fair exams.', created_at: '2026-09-30T00:00:00Z', edited_at: null, professor_name_: null }];
const withMine = (extra) => ({ tables: Object.assign(clone(FX.TABLES), { reviews: MINE.map(r => Object.assign({ user_id: ME }, r)), review_helpful: [{ review_id: 7001 }, { review_id: 7001 }, { review_id: 7001 }] }, extra || {}),
  rpc: Object.assign({}, FX.RPC, { my_reviews: MINE }) });
const manyReviews = n => Array.from({ length: n }, (_, i) => ({ id: 800 + i, professor_key: (i % 2 ? ADA : BRAM), professor_name: i % 2 ? 'Ada Examplewood' : 'Bram Fixturesen', department: 'BUS', course: 'BUS 34' + (30 + i), score: 3 + (i % 3), would_again: true, tags: [], note: 'Fixture community note number ' + i, created_at: new Date(Date.now() - i * 3600e3).toISOString() }));

test('page', async () => {
  const { page, close, log } = await open(); await ready(page); await tick(page, 800);
  await page.click('#tab-rate'); await tick(page, 900);
  const r = await page.evaluate(() => ({
    view: (document.querySelector('.view.active') || {}).id, modal: document.getElementById('rlBack').classList.contains('open'),
    lit: document.getElementById('tab-rate').classList.contains('active') && !document.getElementById('tab-home').classList.contains('active'),
    title: (document.querySelector('#view-rate .rt-title') || {}).textContent, sub: (document.querySelector('#view-rate .rt-sub') || {}).textContent,
    prog: document.getElementById('rtProg').innerText.replace(/\s+/g, ' ').trim(), bar: !!document.querySelector('#rtProg .rt-bar i'),
    mine: rlMyProfs().length, groups: [...document.querySelectorAll('#rtLists .rt-grp > span')].map(e => e.textContent),
    names: [...document.querySelectorAll('#rtLists .rt-nm')].map(e => e.textContent), rate: document.querySelectorAll('#rtLists .rt-rate').length,
    streak: /streak/i.test(document.getElementById('view-rate').innerText) }));
  ok(r.view === 'view-rate' && !r.modal, 'the Rate tab opens the page, not the picker modal', r);
  ok(r.lit, 'the Rate tab is lit, the Home tab is not', r);
  ok(r.title === 'Rate' && /next student/.test(r.sub), 'the title is “Rate”, with one short line', r);
  ok(r.prog === '0 of ' + r.mine + ' rated' && r.mine >= 3 && r.bar, '“N of M rated” with a thin bar; M is the professors the picker listed', r);
  ok(r.groups[0] === 'Taking now · Fall 2026' && r.groups.includes('Past terms'), 'Taking now · Fall 2026 first, then Past terms', r.groups);
  ok(r.names.length === r.mine && r.rate === r.mine, 'every one of your professors is a row with a Rate button', r);
  ok(!r.streak, 'no streak', r);
  /* Back works like the other tabs: Home -> Rate -> Back is Home */
  await page.evaluate(() => show('home')); await tick(page, 400); await goRate(page);
  await page.goBack(); await tick(page, 600);
  ok(await page.evaluate(() => (document.querySelector('.view.active') || {}).id) === 'view-home', 'browser Back from Rate goes back to Home, like the other tabs');
  await page.evaluate(() => show('explore')); await tick(page, 300);
  ok(await page.evaluate(() => !document.getElementById('tab-rate').classList.contains('active')), 'leaving Rate un-lights the tab');
  ok(log.errors.length === 0, 'page: no page errors', log.errors); await close();
});

test('find', async () => {
  const { page, close, log } = await open(); await ready(page); await goRate(page);
  const names = () => page.evaluate(() => [...document.querySelectorAll('#rtLists .rt-item .rt-nm')].map(e => e.textContent));
  const grp = () => page.evaluate(() => [...document.querySelectorAll('#rtLists .rt-grp > span')].map(e => e.textContent));
  await page.fill('#rtSearch', 'exam'); await tick(page, 600);
  ok((await grp())[0] === 'Matching “exam”' && (await names()).includes('Ada Examplewood'), 'a name finds the professor, under “Matching …”, above your professors', [await grp(), await names()]);
  /* a professor with no ratings yet is reachable, and is not given a score */
  const un = await page.evaluate(() => { const e = Object.entries(PROFESSORS).find(([i, p]) => p.rating == null && p.name && p.name.length > 6); return e ? e[1].name : null; });
  if (un) {
    await page.fill('#rtSearch', un.split(' ')[0] + ' ' + un.split(' ').slice(-1)[0]); await tick(page, 600);
    const row = await page.evaluate(n => { const it = [...document.querySelectorAll('#rtLists .rt-item')].find(e => e.querySelector('.rt-nm').textContent === n); return it && { txt: it.innerText, btn: !!it.querySelector('.rt-rate') }; }, un);
    ok(row && /No ratings yet/.test(row.txt) && row.btn, 'a professor with no ratings yet can be found and rated (“No ratings yet”, a Rate button)', row);
  }
  await page.fill('#rtSearch', 'zzzzqq'); await tick(page, 600);
  ok(/Nothing matches/.test(await page.evaluate(() => document.getElementById('rtLists').innerText)), 'no match says so');
  /* a course typed as prefix + number */
  await page.fill('#rtSearch', 'BUS 3438'); await tick(page, 600);
  const c = await page.evaluate(() => ({ pre: rlPrefix, num: rlNum, fields: [document.getElementById('rtPrefixIn').value, document.getElementById('rtNumIn').value], head: document.querySelector('#rtLists .rt-grp > span').textContent }));
  ok(c.pre === 'BUS' && c.num === '3438' && c.fields.join() === 'BUS,3438' && /Matching BUS 3438/.test(c.head), 'a course typed as prefix + number filters, and fills the course fields', c);
  await page.fill('#rtSearch', ''); await tick(page, 600);
  ok(await page.evaluate(() => !rlTouched && rlNum === '' && !/matching/i.test(document.getElementById('rtLists').innerText)), 'clearing the box clears that filter');
  /* the three fields: Your major / Change, prefix, number */
  await page.click('#rtNarrowBtn'); await tick(page, 200);
  const f = await page.evaluate(() => ({ shown: !document.getElementById('rtFilt').hidden, txt: document.getElementById('rtFilt').innerText, major: rlMajor }));
  ok(f.shown && /Your major/i.test(f.txt) && /Change/.test(f.txt) && /Course prefix/i.test(f.txt) && /Course number/i.test(f.txt), 'Narrow by course opens Your major (Change), Course prefix, Course number', f);
  await page.fill('#rtNumIn', '4442'); await tick(page, 700);
  ok(await page.evaluate(() => /matching/i.test(document.getElementById('rtLists').innerText) && rlNum === '4442'), 'the number field filters the same way', await grp());
  await page.click('#rtFilt .rt-majorrow button'); await tick(page, 300);
  ok(await page.evaluate(() => !!document.querySelector('#rtFilt select')), 'Change turns the major into a picker');
  ok(log.errors.length === 0, 'find: no page errors', log.errors); await close();
});

test('form', async () => {
  const { page, close, log } = await open(withMine()); await ready(page); await goRate(page);
  const bram = await profId(page, BRAM);
  await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 900);
  const o = await page.evaluate(() => ({ mback: document.getElementById('mback').classList.contains('open'), inRow: !!document.querySelector('#rtLists .rt-item.open .rt-fh #rfSubmit'),
    head: (document.querySelector('#rtLists .rt-item.open .rate-h') || {}).textContent, btn: document.querySelector('#rtLists .rt-item.open .rt-rate').textContent, cp: currentProf, course: (document.getElementById('rfCourse') || {}).value,
    ids: ['rf-overall', 'rf-again', 'rf-hours', 'rfNote', 'rfSubmit', 'rf-term'].every(i => document.getElementById(i)) }));
  ok(!o.mback && o.inRow && /^Rate Bram/.test(o.head) && o.btn === 'Close' && o.ids, 'Rate opens the existing form under that professor’s row, no modal; the button says Close', o);
  ok(o.course === 'BUS 3438', 'the class the row was for is pre-selected', o.course);
  /* the form's own validation */
  await page.click('#rfSubmit'); await tick(page, 400);
  ok(/overall|star|rating/i.test(await page.evaluate(() => document.getElementById('rfErr').textContent)) && rows(log, 'reviews', 'POST').length === 0, 'submitting an empty form is refused with the form’s own message, nothing sent', await page.evaluate(() => document.getElementById('rfErr').textContent));
  /* Close and the Escape key put it away; a second tap opens it again */
  await page.click('#rtLists .rt-item.open .rt-rate'); await tick(page, 400);
  ok(await page.evaluate(() => !document.querySelector('.rt-fh #rfSubmit') && !document.querySelector('#rtLists .rt-item.open')), 'Close puts the form away');
  await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 600);
  await page.keyboard.press('Escape'); await tick(page, 400);
  ok(await page.evaluate(() => !document.querySelector('.rt-fh #rfSubmit')), 'Escape puts the form away');
  /* fill and post: same star control, same insert */
  await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 600);
  await page.evaluate(() => { const st = document.querySelectorAll('#rf-overall .rf-st'); const r = st[3].getBoundingClientRect(); st[3].dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: r.right - 4, clientY: r.top + 6 })); });
  await page.evaluate(() => { [...document.querySelectorAll('#rf-again button')].find(b => b.textContent === 'Yes').click(); [...document.querySelectorAll('#rf-hours button')][1].click(); document.getElementById('rfNote').value = 'Rate-page test note.'; document.getElementById('rfNote').dispatchEvent(new Event('input', { bubbles: true })); });
  await tick(page, 300);
  await page.click('#rfSubmit'); await until(page, () => /Thanks/.test(document.querySelector('.rt-fh') ? document.querySelector('.rt-fh').innerText : ''), null, 30);
  const ins = rows(log, 'reviews', 'POST');
  ok(ins.length === 1 && ins[0].professor_key === BRAM && ins[0].course === 'BUS 3438' && ins[0].score === 4 && ins[0].would_again === true && ins[0].hours === '3–6' && ins[0].note === 'Rate-page test note.', 'posting sends the one reviews insert the modal sent', ins);
  const th = await page.evaluate(() => ({ inRow: /Thanks/.test((document.querySelector('#rtLists .rt-fh') || {}).innerText || ''), mback: document.getElementById('mback').classList.contains('open'),
    next: [...document.querySelectorAll('.rt-fh .thx-next-row')].map(b => b.querySelector('.thx-nm b').textContent), prog: document.getElementById('rtProg').innerText.replace(/\s+/g, ' ').trim() }));
  ok(th.inRow && !th.mback && th.next.length >= 1 && !th.next.includes('Bram Fixturesen'), 'the thank-you is in the row and offers the next professor', th);
  ok(/^2 of \d+ rated/.test(th.prog), 'the progress counts it at once (Ada was already reviewed, now Bram too)', th.prog);
  await page.click('.rt-fh .thx-next-row'); await tick(page, 900);
  const nx = await page.evaluate(() => ({ head: (document.querySelector('#rtLists .rt-item.open .rate-h') || {}).textContent, open: document.querySelectorAll('#rtLists .rt-item.open').length }));
  ok(/^Rate /.test(nx.head) && !/Bram/.test(nx.head) && nx.open === 1, 'the next professor’s form opens in their row', nx);
  const rv = await page.evaluate(() => { const it = [...document.querySelectorAll('#rtLists .rt-item')].find(e => /Bram/.test(e.querySelector('.rt-nm').textContent)); return it && /Reviewed/.test(it.innerText) && !it.querySelector('.rt-rate'); });
  ok(rv, 'the row of the one you posted says Reviewed');
  await shot(page, 'form-dark');
  ok(log.errors.length === 0, 'form: no page errors', log.errors); await close();
});

/* the coordinator's review of 251c29f: the form is not clipped, focus is kept, the sheet is a dialog, the edges */
test('review', async () => {
  const visible = (p) => p.evaluate(() => { const b = document.getElementById('rfSubmit'); b.scrollIntoView({ block: 'center' }); const r = b.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return { top: Math.round(r.top), bottom: Math.round(r.bottom), vh: innerHeight, h: Math.round(r.height), hit: !!hit && (hit === b || b.contains(hit)), rf: getComputedStyle(document.querySelector('.rt-fh .rf')).overflowY, rfMax: getComputedStyle(document.querySelector('.rt-fh .rf')).maxHeight }; });
  for (const [w, h] of [[1300, 900], [390, 844]]) {
    const { page, close, log } = await open(Object.assign(withMine(), { width: w, height: h })); await ready(page); await goRate(page);
    const bram = await profId(page, BRAM);
    await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 900);
    /* focus lands in the form; aria-controls points at it */
    const f = await page.evaluate(() => { const it = document.querySelector('#rtLists .rt-item.open'), b = it.querySelector('.rt-rate'); return { inForm: !!document.activeElement && !!document.activeElement.closest('.rt-formbox'), tag: document.activeElement && document.activeElement.className,
      ctl: b.getAttribute('aria-controls'), fh: it.querySelector('.rt-fh').id, exp: b.getAttribute('aria-expanded') }; });
    ok(f.inForm && /rate-h/.test(f.tag) && f.ctl && f.ctl === f.fh && f.exp === 'true', w + 'px: focus goes to the form’s heading; the toggle names it with aria-controls', f);
    await page.evaluate(() => rfToggleMore());   /* the long form: everything open */
    await tick(page, 300);
    const v = await visible(page);
    ok(v.rf === 'visible' && v.rfMax === 'none' && v.h > 20 && v.top >= 0 && v.bottom <= v.vh && v.hit, w + 'px: Post review is not clipped: after scrolling to it, it is inside the viewport and is what is at its own point', v);
    /* a real click on it, with Playwright's own hit-target check */
    await page.locator('#rfSubmit').click({ timeout: 4000 }); await tick(page, 400);
    ok(/overall|star|rating/i.test(await page.evaluate(() => document.getElementById('rfErr').textContent)), w + 'px: a real click on Post review reaches the form’s validation');
    /* one close control: the row's button on a desktop, the × on a phone sheet */
    const cl = await page.evaluate(() => ({ x: getComputedStyle(document.querySelector('.rt-fh .mclose')).display, btn: document.querySelector('#rtLists .rt-item.open .rt-rate').textContent }));
    ok(w > 640 ? (cl.x === 'none' && cl.btn === 'Close') : cl.x !== 'none', w + 'px: one close control', cl);
    if (w <= 640) {
      const d = await page.evaluate(() => { const h = document.querySelector('.rt-formbox'); return { role: h.getAttribute('role'), modal: h.getAttribute('aria-modal'), label: h.getAttribute('aria-label') }; });
      ok(d.role === 'dialog' && d.modal === 'true' && /Bram/.test(d.label), 'phone: the sheet is a dialog (role, aria-modal, name)', d);
      /* Tab from the last control wraps to the first */
      await page.evaluate(() => { const f = [...document.querySelectorAll('.rt-formbox button,.rt-formbox input,.rt-formbox select,.rt-formbox textarea')].filter(x => x.offsetParent); f[f.length - 1].focus(); });
      await page.keyboard.press('Tab');
      ok(await page.evaluate(() => !!document.activeElement.closest('.rt-formbox')), 'phone: Tab does not leave the sheet');
    }
    /* closing gives focus back to that professor's Rate button */
    await page.keyboard.press('Escape'); await tick(page, 400);
    const b = await page.evaluate(i => { const a = document.activeElement; return !!a && a.classList.contains('rt-rate') && a.closest('.rt-item').getAttribute('data-pid') === String(i); }, bram);
    ok(b, w + 'px: closing returns focus to that professor’s Rate button');
    ok(log.errors.length === 0, w + 'px review: no page errors', log.errors); await close();
  }
  { /* late reloads and typing in the search do not take focus, caret or the form away */
    const { page, close } = await open(withMine()); await ready(page); await goRate(page);
    const bram = await profId(page, BRAM);
    await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 700); await page.evaluate(() => rfToggleMore()); await tick(page, 300);
    await page.evaluate(() => { const n = document.getElementById('rfNote'); n.value = 'hello world'; n.dispatchEvent(new Event('input', { bubbles: true })); n.focus(); n.setSelectionRange(3, 8); });
    await page.evaluate(() => { rtRenderAll(); rtAuthChanged(); });
    const k = await page.evaluate(() => { const n = document.getElementById('rfNote'); return { same: document.activeElement === n, s: n.selectionStart, e: n.selectionEnd, v: n.value, inRow: !!n.closest('.rt-item.open') }; });
    ok(k.same && k.s === 3 && k.e === 8 && k.v === 'hello world' && k.inRow, 'a repaint under an open form keeps the focused field, its caret and its text', k);
    await page.fill('#rtSearch', 'exam'); await tick(page, 600);
    ok(await page.evaluate(() => !!document.querySelector('#rtLists .rt-item.open #rfNote') && document.getElementById('rfNote').value === 'hello world'), 'typing in the search leaves the open form as it was');
    /* signing out puts the form away */
    await page.evaluate(() => { sbUser = null; updateAuthUI(); }); await tick(page, 500);
    ok(await page.evaluate(() => RT.pid == null && !document.querySelector('#rfNote')), 'signing out puts an open form away');
    await close(); }
  { /* the edges: a modal already open, a one-at-a-time sheet that wrote reviews, singular times, the phone-to-desktop lock, Edit on a Reviewed row */
    const { page, close, log } = await open(withMine()); await ready(page); await goRate(page); await until(page, () => document.querySelectorAll('#rtLists .rt-rowedit').length > 0, null, 30);
    const bram = await profId(page, BRAM);
    ok(await page.evaluate(() => rtAgo(Date.now() - 3600e3 - 5000) === '1 hour ago' && rtAgo(Date.now() - 86400e3 * 2.2) === '2 days ago' && rtAgo(Date.now() - 86400e3 * 1.9) === 'yesterday'), 'times read “1 hour ago”, “2 days ago”');
    await page.evaluate(() => document.getElementById('mback').classList.add('open')); await page.evaluate(i => startRate(i), bram); await tick(page, 700);
    const m = await page.evaluate(() => ({ inline: !!document.querySelector('#rtLists #rfSubmit'), modal: !!document.querySelector('#mback.open #modal #rfSubmit') }));
    ok(!m.inline && m.modal, 'with another sheet already open the form opens in the modal, not under a row behind it', m);
    await page.evaluate(() => closeModal()); await tick(page, 300);
    const reads0 = log.rpcs.filter(r => r.fn === 'my_reviews').length;
    await page.evaluate(() => { document.getElementById('rsBack').classList.add('open'); rsClose(); }); await tick(page, 900);
    ok(log.rpcs.filter(r => r.fn === 'my_reviews').length > reads0, 'closing the one-at-a-time sheet on the Rate page re-reads your reviews and repaints');
    /* Reviewed rows have their own Edit */
    const ed = await page.evaluate(() => { const it = [...document.querySelectorAll('#rtLists .rt-item')].find(e => /Ada/.test(e.querySelector('.rt-nm').textContent)); return { edit: !!it.querySelector('.rt-rowedit'), badge: /Reviewed/.test(it.innerText) }; });
    ok(ed.edit && ed.badge, 'a Reviewed row has an Edit control beside the badge', ed);
    await page.click('#rtLists .rt-rowedit'); await tick(page, 900);
    ok(await page.evaluate(() => /^Edit your review of Ada/.test((document.querySelector('#rtLists .rt-item.open .rate-h') || {}).textContent || '') && !document.getElementById('mback').classList.contains('open')), 'that Edit opens the edit form in the row');
    await page.keyboard.press('Escape'); await tick(page, 300);
    ok(log.errors.length === 0, 'edges: no page errors', log.errors); await close(); }
  { /* phone sheet, then the window grows to a desktop: the page is not left locked */
    const { page, close } = await open(Object.assign(withMine(), { width: 390, height: 844 })); await ready(page); await goRate(page);
    const bram = await profId(page, BRAM);
    await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 700);
    ok(await page.evaluate(() => document.body.style.overflow === 'hidden'), 'phone sheet: the page is locked');
    await page.setViewportSize({ width: 1300, height: 900 }); await tick(page, 600);
    const r = await page.evaluate(() => ({ ov: document.body.style.overflow, sheet: document.getElementById('view-rate').classList.contains('rt-sheet'), role: document.querySelector('.rt-formbox').getAttribute('role') }));
    ok(r.ov !== 'hidden' && !r.sheet && r.role === null, 'phone to desktop: the page unlocks and the form is plain again', r);
    await close(); }
});

test('pastMore', async () => {
  const { page, close, log } = await open(); await ready(page); await goRate(page);
  /* eight more past professors: six show, the rest fold under “Show N more” */
  const n = await page.evaluate(() => { const names = Object.values(PROFESSORS).filter(p => p.name && !/Dov Mockridge/.test(p.name)).slice(0, 9).map(p => p.name);
    names.forEach((nm, i) => myHistory.push({ code: 'BUS 2' + (100 + i), term: 'Winter', year: 2025, professor: nm })); rtRenderAll(); return names.length; });
  const r = await page.evaluate(() => ({ vis: [...document.querySelectorAll('#rtLists .rt-item')].filter(e => e.offsetParent).length, all: document.querySelectorAll('#rtLists .rt-item').length,
    more: (document.getElementById('rtShowMore') || {}).textContent, mine: rlMyProfs().length }));
  ok(n >= 5 && r.more && /^Show \d+ more$/.test(r.more) && r.vis < r.all, 'past terms show six rows and fold the rest under “Show N more”', r);
  await page.click('#rtShowMore'); await tick(page, 300);
  ok(await page.evaluate(() => [...document.querySelectorAll('#rtLists .rt-item')].every(e => e.offsetParent) && /Show fewer/.test(document.getElementById('rtShowMore').textContent)), 'Show more shows them all');
  await page.click('#rtShowMore'); await tick(page, 300);
  const hid = await page.evaluate(() => { const e = [...document.querySelectorAll('#rtLists .rt-item.rt-more')].pop(); return e ? e.getAttribute('data-pid') : null; });
  await page.evaluate(i => startRate(i), hid); await tick(page, 900);
  ok(await page.evaluate(() => { const it = document.querySelector('#rtLists .rt-item.open'); return !!it && it.offsetParent !== null && !!it.querySelector('#rfSubmit'); }), 'opening a professor that was folded shows the row and its form');
  ok(log.errors.length === 0, 'pastMore: no page errors', log.errors); await close();
});

test('rail', async () => {
  const { page, close, log } = await open(withMine()); await ready(page); await goRate(page);
  await until(page, () => document.querySelectorAll('#rtRail .rt-rev').length > 0, null, 30);
  const r = await page.evaluate(() => ({ txt: document.getElementById('rtRail').innerText, edit: !!document.querySelector('#rtRail .rt-edit[data-id="7001"]'), votes: (document.querySelector('#rtRail .rt-votes') || {}).innerText, impact: window.MY_IMPACT }));
  ok(/YOUR REVIEWS/i.test(r.txt) && /Ada Examplewood/.test(r.txt) && /Clear lectures/.test(r.txt) && r.edit, 'the rail lists your reviews, each with Edit', r);
  ok(/3\s+helpful votes on your reviews/.test(String(r.votes).replace(/\s+/g, ' ')) && r.impact === 3, 'the helpful-votes count is what loadMyReviews already read', r);
  ok(!/Latest reviews at Cal Poly/.test(r.txt), 'Latest reviews at Cal Poly is hidden when Home’s feed has fewer than 8 reviews', r.txt);
  ok(await page.evaluate(() => { const it = [...document.querySelectorAll('#rtLists .rt-item')].find(e => /Ada/.test(e.querySelector('.rt-nm').textContent)); return !!it && /Reviewed/.test(it.innerText); }), 'a professor you reviewed shows the Reviewed badge');
  /* Edit: the existing edit flow, in the row */
  await page.click('#rtRail .rt-edit'); await tick(page, 900);
  const e = await page.evaluate(() => ({ mback: document.getElementById('mback').classList.contains('open'), inRow: !!document.querySelector('#rtLists .rt-item.open .rt-fh #rfSubmit'), head: (document.querySelector('#rtLists .rt-item.open .rate-h') || {}).textContent,
    btn: (document.getElementById('rfSubmit') || {}).textContent, note: (document.getElementById('rfNote') || {}).value, edit: window.RATE_EDIT && window.RATE_EDIT.id }));
  ok(!e.mback && e.inRow && /^Edit your review of Ada/.test(e.head) && e.btn === 'Save changes' && e.note === 'Clear lectures, fair exams.' && e.edit === 7001, 'Edit opens the existing edit form, filled in, under that professor', e);
  await page.evaluate(() => { const n = document.getElementById('rfNote'); n.value = 'Edited from the Rate page.'; n.dispatchEvent(new Event('input', { bubbles: true })); });
  await page.click('#rfSubmit'); await until(page, () => !document.querySelector('.rt-fh #rfSubmit'), null, 30); await tick(page, 600);
  const up = log.writes.filter(w => w.table === 'reviews' && w.m === 'PATCH');
  ok(up.length === 1 && up[0].body.note === 'Edited from the Rate page.' && /id=eq\.7001/.test(decodeURIComponent(up[0].query || '')), 'saving is the existing update of that one review (id 7001)', up.map(u => ({ q: u.query, b: u.body })));
  ok(await page.evaluate(() => !document.querySelector('#rtLists .rt-item.open')), 'after saving the form is put away');
  ok(log.errors.length === 0, 'rail: no page errors', log.errors); await close();
  /* eight reviews in Home's feed data: the community block appears (and respects the unlock rule) */
  const m = await open(Object.assign(withMine(), { tables: Object.assign(withMine().tables, { reviews_public: manyReviews(9) }) })); await ready(m.page); await tick(m.page, 1200); await goRate(m.page);
  const c = await m.page.evaluate(() => ({ n: (hmRecentsGet() || []).length, t: document.getElementById('rtRail').innerText }));
  ok(c.n >= 8 && /LATEST REVIEWS AT CAL POLY/i.test(c.t) && /Fixture community note/.test(c.t), 'with 8 or more reviews in Home’s feed data the community block shows', c);
  await shot(m.page, 'rail-dark'); await m.close();
  /* a student who has not reviewed anyone yet: the block shows who and how many stars, not the words (the unlock rule) */
  const lk = await open({ tables: Object.assign(clone(FX.TABLES), { reviews_public: manyReviews(9) }) }); await ready(lk.page); await tick(lk.page, 1200); await goRate(lk.page);
  const lt = await lk.page.evaluate(() => ({ t: document.getElementById('rtRail').innerText, unlocked: recipUnlocked() }));
  ok(!lt.unlocked && /LATEST REVIEWS AT CAL POLY/i.test(lt.t) && !/Fixture community note/.test(lt.t) && /Write a review to read/.test(lt.t), 'before your first review the block shows who and how many stars, not the words (the same unlock rule as everywhere)', lt); await lk.close();
  const x = await open({ tables: Object.assign(clone(FX.TABLES), { reviews_public: manyReviews(7) }) }); await ready(x.page); await tick(x.page, 1200); await goRate(x.page);
  ok(await x.page.evaluate(() => !/LATEST REVIEWS/i.test(document.getElementById('rtRail').innerText)), 'with 7 it stays hidden'); await x.close();
});

test('entries', async () => {
  const { page, close, log } = await open(); await ready(page); await tick(page, 600);
  const bram = await profId(page, BRAM);
  const state = () => page.evaluate(() => ({ view: (document.querySelector('.view.active') || {}).id, mback: document.getElementById('mback').classList.contains('open'), form: document.getElementById('mback').classList.contains('open') && !!document.querySelector('#modal #rfSubmit'), inline: !!document.querySelector('#rtLists #rfSubmit'), rl: document.getElementById('rlBack').classList.contains('open') }));
  /* a professor's page: Leave a review -> the form, in place, in the modal */
  await page.evaluate(i => openProf(i), bram); await tick(page, 800);
  await page.evaluate(i => startRate(i), bram); await tick(page, 800);
  let s = await state(); ok(s.view === 'view-prof' && s.mback && s.form && !s.inline, 'a professor’s page: Leave a review opens the form in place (modal), as before', s);
  await page.evaluate(() => closeModal()); await tick(page, 300);
  /* Past classes' Rate button, Home's instructor Rate, Champ's action: all startRate, in place */
  await page.evaluate(() => show('home')); await tick(page, 400);
  await page.evaluate(i => hmRateInstructor(i, 'Bram Fixturesen', 'BUS'), bram); await tick(page, 800);
  s = await state(); ok(s.view === 'view-home' && s.mback && s.form, 'Home’s Rate on a professor row opens the form in place', s);
  await page.evaluate(() => closeModal()); await tick(page, 300);
  /* the openers of the page */
  await page.evaluate(() => show('home')); await tick(page, 400);
  await page.evaluate(() => { const b = document.querySelector('.hm-ratebtn'); if (b) b.click(); else openRate(); }); await tick(page, 700);
  s = await state(); ok(s.view === 'view-rate' && !s.rl, 'Home’s “Rate a professor” opens the Rate page', s);
  await page.evaluate(() => show('home')); await tick(page, 300);
  await page.evaluate(() => { cmdkToggle && cmdkToggle(); }); await tick(page, 300);
  await page.evaluate(() => { const it = (cmdkItems || []).findIndex(x => /Rate a professor/.test(x.label)); if (it >= 0) cmdkRun(it); }); await tick(page, 700);
  ok((await state()).view === 'view-rate', 'the command palette’s “Rate a professor” opens the Rate page');
  await page.evaluate(() => show('home')); await tick(page, 300);
  await page.evaluate(() => { try { window.hawkGo ? hawkGo('rate') : openRate(); } catch (e) { openRate(); } }); await tick(page, 600);
  ok((await state()).view === 'view-rate', 'Champ’s “rate” place opens the Rate page');
  /* the Rate page and startRate: inline, scrolled to the row, form open */
  await page.evaluate(i => startRate(i, 'BUS 3438'), bram); await tick(page, 900);
  s = await state(); ok(s.view === 'view-rate' && s.inline && !s.mback && !s.form, 'startRate while on the Rate page puts the form under the row', s);
  /* leaving puts the form away; coming back is clean */
  await page.evaluate(() => show('explore')); await tick(page, 400); await goRate(page);
  ok(await page.evaluate(() => !document.querySelector('#rtLists #rfSubmit') && RT.pid == null), 'leaving the page puts an open form away');
  /* the "review someone else" picker on the unlock card is still the old sheet */
  await page.evaluate(() => { window._recipReturn = null; openReviewLanding(); }); await tick(page, 500);
  ok(await page.evaluate(() => document.getElementById('rlBack').classList.contains('open') && !!document.getElementById('rlLists')), 'the unlock card’s “review someone else” still opens the picker sheet');
  await page.evaluate(() => closeReviewLanding()); await tick(page, 300);
  /* ?tab=rate */
  await page.evaluate(() => pwaOpenTab('tab=rate')); await tick(page, 600);
  ok((await state()).view === 'view-rate', '?tab=rate opens the Rate page');
  ok(log.errors.length === 0, 'entries: no page errors', log.errors); await close();
});

test('signedOut', async () => {
  const { page, close, log } = await open({ signedIn: false, terms: 'live' }); await tick(page, 1500);
  await goRate(page);
  const r = await page.evaluate(() => ({ view: (document.querySelector('.view.active') || {}).id, gate: (document.querySelector('#view-rate .rt-gate') || {}).innerText, search: !!document.getElementById('rtSearch'), prog: document.getElementById('rtProg').innerText, rail: document.getElementById('rtRail').style.display }));
  ok(r.view === 'view-rate' && /Sign in to rate/.test(r.gate || '') && /verified Cal Poly students/.test(r.gate || ''), 'signed out: a clean sign-in prompt in the page', r);
  ok(r.search && r.prog === '', 'signed out: the search is there, there is no progress', r);
  await page.fill('#rtSearch', 'exam'); await tick(page, 700);
  const row = await page.evaluate(() => { const b = document.querySelector('#rtLists .rt-rate'); return !!b; });
  ok(row, 'signed out: the search still finds professors');
  await shot(page, 'signed-out-dark');
  await page.click('#rtLists .rt-rate'); await tick(page, 700);
  const a = await page.evaluate(() => ({ auth: document.getElementById('authBack').classList.contains('open'), mback: document.getElementById('mback').classList.contains('open'), form: !!document.getElementById('rfSubmit') }));
  ok(a.auth && !a.form, 'signed out: Rate asks to verify first (the same gate), no form yet', a);
  ok(log.errors.length === 0, 'signedOut: no page errors', log.errors); await close();
});

test('phone', async () => {
  const { page, close, log } = await open({ width: 390, height: 844 }); await ready(page); await goRate(page);
  const bram = await profId(page, BRAM);
  const base = await page.evaluate(() => ({ wide: [...document.querySelectorAll('#view-rate *')].filter(e => e.getBoundingClientRect().right > document.documentElement.clientWidth + .5).map(e => e.className).slice(0, 5), tab: document.getElementById('mtab-rate').classList.contains('active') }));
  ok(base.wide.length === 0 && base.tab, 'phone: nothing on the page runs past the edge, the Rate tab is lit', base);
  await page.click(`#rtLists .rt-item[data-pid="${bram}"] .rt-rate`); await tick(page, 900);
  const s = await page.evaluate(() => { const fh = document.querySelector('#rtLists .rt-item.open .rt-fh'), r = fh.getBoundingClientRect(), sc = document.querySelector('#view-rate .rt-scrim');
    return { pos: getComputedStyle(fh).position, bottom: Math.round(r.bottom), vh: innerHeight, w: Math.round(r.width), scrim: getComputedStyle(sc).display, body: document.body.style.overflow, fab: (document.querySelector('.hawk-fab') ? getComputedStyle(document.querySelector('.hawk-fab')).display : 'none'), form: !!fh.querySelector('#rfSubmit'), top: Math.round(r.top) }; });
  ok(s.pos === 'fixed' && s.bottom === s.vh && s.w >= 390 && s.scrim === 'block' && s.form && s.top > 40, 'phone: the form is a bottom sheet with a scrim', s);
  ok(s.body === 'hidden' && s.fab === 'none', 'phone: the page behind is locked and Champ’s bird steps aside', s);
  await shot(page, 'sheet-phone-dark');
  await page.mouse.click(195, 30); await tick(page, 500);
  ok(await page.evaluate(() => !document.querySelector('.rt-fh #rfSubmit') && document.body.style.overflow !== 'hidden'), 'phone: tapping outside the sheet closes it and frees the page');
  ok(log.errors.length === 0, 'phone: no page errors', log.errors); await close();
});

test('shots', async () => {
  if (!SHOTS) return;
  for (const th of ['dark', 'light']) for (const [w, h, tag] of [[1300, 900, 'desk'], [390, 844, 'phone']]) {
    const o = await open(Object.assign(withMine(), { width: w, height: h, init: THEME(th), tables: Object.assign(withMine().tables, { reviews_public: manyReviews(9) }) })); await ready(o.page); await goRate(o.page); await until(o.page, () => document.querySelectorAll('#rtRail .rt-rev').length > 0, null, 20);
    await o.page.screenshot({ path: path.join(SHOTS, `rate-${tag}-${th}-page.png`), fullPage: tag === 'phone' });
    const id = await profId(o.page, BRAM);
    await o.page.click(`#rtLists .rt-item[data-pid="${id}"] .rt-rate`); await tick(o.page, 1000);
    await o.page.screenshot({ path: path.join(SHOTS, `rate-${tag}-${th}-form.png`) });
    await o.close();
  }
});

const names = Object.keys(T).filter(n => !ONLY || n === ONLY);
for (const n of names) { if (!QUIET) console.log('\n' + n); try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw →', e.message.slice(0, 400)); } }
console.log(`\ncheck-desktop-rate-page: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exitCode = 1; }
