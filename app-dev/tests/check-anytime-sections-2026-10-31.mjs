/* (2026-10-31) Anytime fixes + the report's "Pick your sections" step (patches/anytime-fixes-2026-10-31.py,
   patches/dpr-pick-sections-2026-10-31.py). Synthetic fixtures only (invented people, sections and FIX course codes).
   Run: APP_DIR=<site> APP_PORT=<port> node check-anytime-sections-2026-10-31.mjs [--shots <dir>] */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
const port = +(process.env.APP_PORT || 9660);
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : '';
let pass = 0, fail = 0; const fails = [];
function ok(c, m, d) { if (c) { pass++; console.log('  ok  ', m); } else { fail++; fails.push(m); console.log('  FAIL', m, d === undefined ? '' : '→ ' + JSON.stringify(d).slice(0, 500)); } }
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); await p.clock.runFor(50); await p.waitForTimeout(100); };
const until = async (p, fn, arg, n = 30) => { for (let i = 0; i < n; i++) { if (await p.evaluate(fn, arg)) return true; await tick(p, 300); } return false; };
const tap = async (p, sel, txt) => {
  const box = await p.evaluate(([sel, txt]) => { const e = [...document.querySelectorAll(sel)].find(e => { const r = e.getBoundingClientRect(); return r.width && r.height && (!txt || (e.textContent || '').replace(/\s+/g, ' ').includes(txt)); }); if (!e) return null; e.scrollIntoView({ block: 'center' }); const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }, [sel, txt || null]);
  if (!box) return false; await p.touchscreen.tap(box.x, box.y); await tick(p, 500); return true;
};
const sheetText = p => p.evaluate(() => ((document.getElementById('sheet') || {}).innerText || '').replace(/\s+/g, ' '));
const toastText = p => p.evaluate(() => { const t = document.getElementById('toast'); return t && t.classList.contains('on') ? t.textContent.trim() : ''; });
const W = (log, table, m) => log.writes.filter(w => w.table === table && (!m || w.m === m));
const rowsOf = w => [].concat(w.body || []);
const shot = async (p, name) => { if (SHOTS) await p.screenshot({ path: `${SHOTS}/${name}.png` }); };
/* contrast: every listed element's text against the first painted background behind it */
const lum = c => { const m = c.match(/\d+(\.\d+)?/g).map(Number).slice(0, 3).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]; };
const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const pairs = (p, sel) => p.evaluate(sel => [...document.querySelectorAll(sel)].filter(e => e.getBoundingClientRect().width && (e.textContent || '').trim()).map(e => { let n = e, bg = 'rgba(0, 0, 0, 0)'; while (n && /rgba\(0, 0, 0, 0\)|transparent/.test(bg)) { bg = getComputedStyle(n).backgroundColor; n = n.parentElement; } if (/rgba\(0, 0, 0, 0\)|transparent/.test(bg)) bg = getComputedStyle(document.body).backgroundColor; return { t: e.textContent.trim().slice(0, 30), fg: getComputedStyle(e).color, bg, cls: e.className }; }), sel);
const lowOf = ps => ps.filter(x => cr(x.fg, x.bg) < 4.5).map(x => [x.t, x.cls, x.fg, x.bg, cr(x.fg, x.bg).toFixed(2)]);
const setTheme = (p, th) => p.evaluate(th => { try { localStorage.setItem('tc-theme', th); } catch (e) {} applyTheme(true); render(true); }, th);

const ME = FX.ME.id, [AVERY, ROWAN, SKY, QUINN] = FX.FRIENDS.map(f => f.id);
const SC = (code, section, nbr, days, prof = 'Examplewood, Ada', term = '2268', cap = 40, enr = 20) => ({ term, course_code: code, title: 'Fixture ' + code.split(' ')[1], section, instructor: prof, days, status: enr >= cap ? 'Closed' : 'Open', capacity: cap, enrolled: enr, available: Math.max(0, cap - enr), waitlist_total: 0, waitlist_capacity: 10, class_nbr: nbr, instruction_mode: 'P', location: 'Bldg 03-0112' });
/* invented courses for the combination cases (ME's BUS 3438 is MoWe 10:10–12:00, BUS 4442 MoWe 12:10–2:00) */
const FIXSEATS = [
  SC('FIX 1001', '01', '71001', 'MoWe 10:10AM - 12:00PM'), SC('FIX 1001', '02', '71002', 'TuTh 10:10AM - 12:00PM', 'Fixturesen, Bram'),
  SC('FIX 1002', '01', '71003', 'MoWe 10:10AM - 12:00PM'), SC('FIX 1002', '02', '71004', 'Fr 9:10AM - 12:00PM'),
  SC('FIX 2001', '01', '71005', 'TuTh 8:10AM - 9:00AM'), SC('FIX 2001', '02', '71006', 'TuTh 3:10PM - 4:00PM'),
  SC('FIX 2002', '01', '71007', 'Fr 1:10PM - 2:00PM'), SC('FIX 2002', '02', '71008', 'Fr 3:10PM - 4:00PM'),
  SC('FIX 3001', '01', '71009', 'MoWe 10:10AM - 12:00PM'), SC('FIX 3001', '02', '71010', 'MoWe 12:10PM - 2:00PM'),
];
const saved = (user, code, term = '2268', at = '2026-09-10T18:00:00Z') => ({ user_id: user, term, code, class_nbr: null, created_at: at, waitlist_pos: null });
const base = () => { const T = JSON.parse(JSON.stringify(FX.TABLES)); T.course_seats = T.course_seats.concat(FIXSEATS); return T; };

/* ===== A. one term (Fall 2026): hide finished, one section shown + saved quietly, the card, the sheet, Skip, Undo ===== */
{
  const T = base();
  T.saved_classes.push(saved(ME, 'PHIL 3331'), saved(ME, 'BUS 4401'), saved(ME, 'ECON 2303'), saved(ME, 'STAT 2170'),   /* finished · one section · 2 · 2 */
    saved(QUINN, 'BUS 2201'), saved(ROWAN, 'BUS 3346'), saved(ROWAN, 'STAT 2170'));   /* Quinn took BUS 2201 (Winter 2026); BUS 3346 has one section; STAT 2170 two */
  const { page, close, log } = await openApp({ port, tables: T });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows && TC.myHistory, null, { timeout: 15000 });
  await tick(page, 1500); await tick(page, 800);
  const nbr4401 = FX.SEATS.find(r => r.course_code === 'BUS 4401').class_nbr;
  const v = await page.evaluate(() => ({ unp: PEOPLE.me.unplaced, hid: PEOPLE.me.hidden, my: personSecs('me').map(s => s.code + ':' + (s.s != null) + ':' + !!s.oneSec),
    quinn: { unp: PEOPLE['22222224-2222-4222-8222-222222222224'].unplaced, hid: (PEOPLE['22222224-2222-4222-8222-222222222224'] || {}).hidden },
    rowan: personSecs('22222222-2222-4222-8222-222222222222').filter(s => s.code === 'BUS 3346').map(s => ({ s: s.s, e: s.e, days: s.days, one: !!s.oneSec, id: s.id })), rowanUnp: PEOPLE['22222222-2222-4222-8222-222222222222'].unplaced }));
  /* a. finished earlier: hidden, everywhere */
  ok(!v.unp.includes('PHIL 3331') && !v.my.some(x => x.startsWith('PHIL 3331')) && v.hid.includes('PHIL 3331'), 'a: PHIL 3331 (you finished it Spring 2026) is not a Fall class of yours — hidden, not in Anytime', v);
  ok(!v.quinn.unp.includes('BUS 2201'), 'a: friends’ view — Quinn’s BUS 2201 (finished Winter 2026) is not one of Quinn’s classes', v.quinn);
  ok(!W(log, 'saved_classes', 'DELETE').length, 'a: nothing is deleted on its own');
  /* b. one section: shown with its times, and saved for the owner */
  const ms = W(log, 'my_sections', 'POST').filter(w => rowsOf(w).some(r => r.code === 'BUS 4401'));
  ok(ms.length === 1 && rowsOf(ms[0]).every(r => r.user_id === ME && r.term === '2268' && String(r.class_nbr) === nbr4401 && r.days === 'MoWe 10:10AM - 11:30AM' && r.status === 'enrolled') && /on_conflict=user_id(%2C|,)class_nbr(%2C|,)term/.test(ms[0].query), 'b: on open, BUS 4401 (its only Fall section) is saved as your section — one upsert, its real class number and time', ms.map(w => [w.body, w.query]));
  ok(v.my.includes('BUS 4401:true:false'), 'b: BUS 4401 is now a real timed class of yours (no longer marked as a guess)', v.my);
  ok(v.rowan.length === 1 && v.rowan[0].s != null && v.rowan[0].days === 'MW' && v.rowan[0].one && !v.rowanUnp.includes('BUS 3346'), 'b: friends’ view — Rowan’s BUS 3346 (no section, one offered) shows that section’s real times', v);
  ok(!W(log, 'my_sections').some(w => rowsOf(w).some(r => r.user_id && r.user_id !== ME)), 'b: nothing is ever written for a friend');
  ok(!W(log, 'my_sections', 'POST').some(w => rowsOf(w).some(r => r.code === 'ECON 2303' || r.code === 'STAT 2170')) && v.unp.includes('ECON 2303') && v.unp.includes('STAT 2170') && v.rowanUnp.includes('STAT 2170'), 'b: 2+ sections are never picked — ECON 2303 / STAT 2170 stay with no section (mine and Rowan’s)', v);
  /* the friend's page draws the one-section class on the week */
  await page.evaluate(id => A.openFriend(id), ROWAN); await tick(page, 800);
  const fp = await page.evaluate(() => ({ grid: [...document.querySelectorAll('#scroll .g-b')].map(b => b.textContent.trim()), any: [...document.querySelectorAll('#scroll .any-c')].map(b => b.textContent.trim()) }));
  ok(fp.grid.some(t => /BUS\s*3346/.test(t)) && !fp.any.some(t => /3346/.test(t)), 'b: on Rowan’s page BUS 3346 is on the week, not in Anytime', fp);
  await page.evaluate(id => A.openFriend(id), QUINN); await tick(page, 800);
  ok(!/BUS\s*2201/.test(await page.evaluate(() => document.getElementById('scroll').innerText)), 'a: Quinn’s page doesn’t show BUS 2201');
  await page.evaluate(() => { S.stack.friends = [{ s: 'friends' }]; setTab('home'); }); await tick(page, 600);
  /* c. Home row (owner) and the My Classes card */
  const home = await page.evaluate(() => [...document.querySelectorAll('#scroll .any-home')].map(b => ({ t: b.innerText.replace(/\s+/g, ' '), a: b.dataset.a, h: b.getBoundingClientRect().height })));
  ok(home.length === 1 && /Add times to 2 classes/.test(home[0].t) && home[0].a === 'anyPickOpen' && home[0].h >= 44, 'c: Home has one small row for you — “Add times to 2 classes”', home);
  ok(await page.evaluate(() => !document.querySelectorAll('#scroll .fcard .any-home, #scroll .any-card').length), 'c: it’s a row on Home, not on a friend’s card');
  await shot(page, 'home-row-light');
  await page.evaluate(() => { setTab('schedule'); A.schedTab('mine'); }); await tick(page, 600);
  const card = await page.evaluate(() => { const c = document.querySelector('#scroll .any-times'); return c && { t: c.innerText.replace(/\s+/g, ' '), top: c.getBoundingClientRect().top < document.querySelector('#scroll .mine-any, #scroll .card.agenda, #scroll .g-col, #scroll .card').getBoundingClientRect().top + 400, x: !!c.querySelector('[data-a="anyPickNo"]') }; });
  ok(card && /Add times to 2 classes/.test(card.t) && card.x, 'c: My Classes has the card at the top: “Add times to 2 classes”, with Not now', card);
  const hidN = await page.evaluate(() => { const e = document.querySelector('#scroll .any-hid'); return e && e.innerText.replace(/\s+/g, ' '); });
  ok(/1 class you’ve already taken is hidden · Remove it/.test(hidN || ''), 'a: My Classes says “1 class you’ve already taken is hidden · Remove it”', hidN);
  ok(await page.evaluate(() => !UI.sheet && !document.querySelector('#sheet .sheet')), 'c: no pop-up — it’s a card (the pop-up limits are untouched)');
  ok(await page.evaluate(() => { try { return !localStorage.getItem('tc_pop_day'); } catch (e) { return false; } }), 'c: the card doesn’t use up the day’s pop-up');
  await shot(page, 'card-light');
  /* the sheet */
  await tap(page, '#scroll .any-times .any-cmain');
  let t = await sheetText(page);
  const secs = await page.evaluate(() => [...document.querySelectorAll('#sheet .any-sec')].map(b => ({ x: b.dataset.x, t: b.innerText.replace(/\s+/g, ' '), h: b.getBoundingClientRect().height, rt: !!b.querySelector('.rowrt') })));
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'anyPick' && /ECON 2303/.test(t) && /STAT 2170/.test(t) && secs.length === 4, 'c: the sheet lists each class with its sections (ECON 2303 ×2, STAT 2170 ×2)', { t: t.slice(0, 300), n: secs.length });
  const e3 = secs.find(s => /\|ECON 2303\|/.test(s.x) && /Sec 03/.test(s.t));
  ok(e3 && /Tu\/Th|TuTh|Tue|Th/.test(e3.t) && /10:10/.test(e3.t) && /Stubbington/.test(e3.t) && e3.rt && /seat/i.test(e3.t) && /1 friend in Sec 03/.test(e3.t), 'c: a section row: days, times, professor + rating, seats, and “1 friend in Sec 03” (Rowan)', e3);
  ok(secs.every(s => s.h >= 44) && await page.evaluate(() => [...document.querySelectorAll('#sheet .any-skip')].every(b => b.getBoundingClientRect().height >= 44)), 'c: 44px tap targets (sections, Skip)');
  await shot(page, 'picker-light');
  /* Skip, and its Undo */
  await tap(page, '#sheet .any-skip[data-x$="STAT 2170"]');
  ok(!/STAT 2170/.test(await sheetText(page)) && /STAT 2170 stays in Anytime/.test(await toastText(page)), 'c: Skip takes STAT 2170 off the list (toast with Undo)', await toastText(page));
  await tap(page, '#toast .tundo');
  ok(/STAT 2170/.test(await sheetText(page)), 'c: Undo puts it back');
  await tap(page, '#sheet .any-skip[data-x$="STAT 2170"]');
  /* choose ECON 2303 Sec 04 → onto the week; Undo takes the section back off */
  const nbr04 = FX.SEATS.find(r => r.course_code === 'ECON 2303' && r.section === '04').class_nbr;
  await tap(page, `#sheet .any-sec[data-x="2268|ECON 2303|${nbr04}"]`); await tick(page, 800);
  const w04 = W(log, 'my_sections', 'POST').filter(w => rowsOf(w).some(r => r.code === 'ECON 2303'));
  const st = await page.evaluate(() => ({ sheet: UI.sheet && UI.sheet.type, sec: personSecs('me').filter(s => s.code === 'ECON 2303').map(s => String(s.id) + ':' + !!s.oneSec), unp: PEOPLE.me.unplaced }));
  ok(w04.length === 1 && String(rowsOf(w04[0])[0].class_nbr) === nbr04 && st.sec.join() === nbr04 + ':false' && !st.unp.includes('ECON 2303'), 'c: tapping Sec 04 saves it (my_sections) and ECON 2303 moves onto the week', { w: w04.map(w => w.body), st });
  ok(st.sheet == null && /ECON 2303 Sec 04 is on your week/.test(await toastText(page)), 'c: nothing left to pick → the sheet closes; toast with Undo', { st, toast: await toastText(page) });
  await tap(page, '#toast .tundo'); await tick(page, 800);
  ok(await page.evaluate(() => PEOPLE.me.unplaced.includes('ECON 2303') && !personSecs('me').some(s => s.code === 'ECON 2303')), 'c: Undo — ECON 2303 is back in Anytime with no section');
  ok(await page.evaluate(() => !!document.querySelector('#scroll .any-times') && /Add times to 1 class\b/.test(document.querySelector('#scroll .any-times').innerText)), 'c: the card counts what’s left (STAT 2170 skipped): “Add times to 1 class”');
  /* Not now on the card: skipped, the card goes */
  await tap(page, '#scroll .any-times [data-a="anyPickNo"]');
  ok(await page.evaluate(() => !document.querySelector('#scroll .any-times') && !document.querySelector('.any-home')), 'c: Not now hides the card for good (those classes stay in Anytime)');
  await tap(page, '#toast .tundo');
  /* a. Remove the taken one (and Undo) */
  await tap(page, '#scroll .any-hrm');
  const del = W(log, 'saved_classes', 'DELETE');
  ok(del.length === 1 && /PHIL/.test(decodeURIComponent(del[0].query)) && /term=eq\.2268/.test(del[0].query) && !(await page.evaluate(() => TC.mineRows.saved.includes('PHIL 3331'))), 'a: Remove it deletes PHIL 3331 from your Fall classes (saved_classes)', del.map(d => decodeURIComponent(d.query)));
  ok(/Removed 1 class you’ve taken/.test(await toastText(page)) && !(await page.evaluate(() => !!document.querySelector('#scroll .any-hid'))), 'a: toast with Undo; the note is gone', await toastText(page));
  await tap(page, '#toast .tundo'); await tick(page, 800);
  ok(await page.evaluate(() => TC.mineRows.saved.includes('PHIL 3331') && PEOPLE.me.hidden.includes('PHIL 3331') && !PEOPLE.me.unplaced.includes('PHIL 3331')), 'a: Undo saves it back — still hidden');
  /* dark mode contrast: card, note, Home row, sheet */
  for (const th of ['light', 'dark']) {
    await setTheme(page, th); await page.evaluate(() => { anySkipSet(['2268:STAT 2170', '2268:ECON 2303'], false); render(true); }); await tick(page, 300);
    let ps = await pairs(page, '#scroll .any-ct, #scroll .any-cs, #scroll .any-hid span, #scroll .any-hrm, #scroll .any-card .pbtn');
    ok(ps.length >= 5 && !lowOf(ps).length, `contrast (${th}): the card and the note read 4.5:1+`, lowOf(ps).length ? lowOf(ps) : ps.length);
    if (th === 'dark') await shot(page, 'card-dark');
    await page.evaluate(() => A.anyPickOpen('2268')); await tick(page, 400);
    ps = await pairs(page, '#sheet h3, #sheet .muted.b, #sheet .any-pcn, #sheet .any-skip, #sheet .any-sm, #sheet .any-fr > span:last-child, #sheet .any-sb .t b, #sheet .any-sb .t .nw, #sheet .any-sec .pbtn, #sheet .code');
    ok(ps.length >= 10 && !lowOf(ps).length, `contrast (${th}): the section sheet reads 4.5:1+`, lowOf(ps).length ? lowOf(ps) : ps.length);
    if (th === 'dark') await shot(page, 'picker-dark');
    await page.evaluate(() => { UI.sheet = null; setTab('home'); }); await tick(page, 400);
    ps = await pairs(page, '#scroll .any-home .any-ct, #scroll .any-home .any-cs');
    ok(ps.length === 2 && !lowOf(ps).length, `contrast (${th}): the Home row reads 4.5:1+`, lowOf(ps).length ? lowOf(ps) : ps);
    if (th === 'dark') await shot(page, 'home-row-dark');
    await page.evaluate(() => { setTab('schedule'); A.schedTab('mine'); }); await tick(page, 300);
  }
  ok(log.errors.length === 0, 'A: no page errors', log.errors);
  await close();
}

/* the quiet save happens once: a section taken off since (on another device) isn't put back */
{
  const T = base(); T.saved_classes.push(saved(ME, 'BUS 4401'));
  const { page, close, log } = await openApp({ port, tables: T, init: `try { localStorage.setItem('tc_any_one:${ME}', JSON.stringify(['2268:BUS 4401'])); } catch (e) {}` });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 15000 }); await tick(page, 1500);
  ok(!W(log, 'my_sections', 'POST').length && await page.evaluate(() => personSecs('me').some(s => s.code === 'BUS 4401' && s.oneSec)), 'b: saved once already on this phone → shown with its one section, not written again');
  await close();
}

/* ===== B. the 29-class question (one term) ===== */
{
  const T = base();
  const codes = Array.from({ length: 28 }, (_, i) => 'ZZZ ' + (1100 + i));   /* not offered: no sections */
  codes.concat(['BUS 4401']).forEach(c => T.saved_classes.push(saved(ME, c, '2268', '2026-10-30T19:0' + (c.length % 9) + ':00Z')));
  const { page, close, log } = await openApp({ port, tables: T });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows, null, { timeout: 15000 }); await tick(page, 1500);
  ok(!W(log, 'my_sections', 'POST').length, 'd: while the question is open, the one-section class (BUS 4401) isn’t saved yet');
  const home = await page.evaluate(() => [...document.querySelectorAll('#scroll .any-home')].map(b => b.innerText.replace(/\s+/g, ' ')));
  ok(home.length === 1 && /Are you taking all 30 Fall 2026 classes\?/.test(home[0]), 'd: Home row asks “Are you taking all 30 Fall 2026 classes?” (28 + BUS 4401 + BUS 2201)', home);
  await page.evaluate(() => { setTab('schedule'); A.schedTab('mine'); }); await tick(page, 600);
  const c = await page.evaluate(() => { const e = document.querySelector('#scroll .any-bulk'); return e && { t: e.innerText.replace(/\s+/g, ' '), b: [...e.querySelectorAll('button')].map(b => [b.dataset.a, b.getBoundingClientRect().height]) }; });
  ok(c && /Are you taking all 30 of these in Fall 2026\?/.test(c.t) && c.b.some(b => b[0] === 'anyBulkYes') && c.b.some(b => b[0] === 'anyBulkPick') && c.b.every(b => b[1] >= 44) && !(await page.evaluate(() => !!document.querySelector('#scroll .any-times'))), 'd: My Classes asks once — Yes / Pick the ones I’m taking (no “Add times” card meanwhile)', c);
  await shot(page, 'bulk-card-light');
  await tap(page, '#scroll .any-bulk [data-a="anyBulkPick"]');
  let sh = await page.evaluate(() => ({ t: UI.sheet && UI.sheet.type, n: document.querySelectorAll('#sheet .dr-rcr[aria-pressed="true"]').length, btn: (document.querySelector('#sheet [data-a="anyBulkSave"]') || {}).innerText }));
  ok(sh.t === 'anyBulk' && sh.n === 30 && /Keep all 30/.test(sh.btn), 'd: Pick → a checklist of all 30, all ticked', sh);
  for (const x of ['ZZZ 1100', 'ZZZ 1101', 'ZZZ 1102']) await tap(page, `#sheet .dr-rcr[data-x="${x}"]`);
  sh = await page.evaluate(() => ({ n: document.querySelectorAll('#sheet .dr-rcr[aria-pressed="true"]').length, btn: (document.querySelector('#sheet [data-a="anyBulkSave"]') || {}).innerText }));
  ok(sh.n === 27 && /Keep 27 · remove 3/.test(sh.btn), 'd: untick 3 → “Keep 27 · remove 3”', sh);
  await shot(page, 'bulk-pick-light');
  for (const th of ['light', 'dark']) { await setTheme(page, th); await tick(page, 200); const ps = await pairs(page, '#sheet h3, #sheet .muted.b, #sheet .dr-rct b, #sheet .btn'); ok(ps.length >= 5 && !lowOf(ps).length, `contrast (${th}): the checklist reads 4.5:1+`, lowOf(ps)); if (th === 'dark') await shot(page, 'bulk-pick-dark'); }
  await setTheme(page, 'light');
  await tap(page, '#sheet [data-a="anyBulkSave"]'); await tick(page, 800);
  const d = W(log, 'saved_classes', 'DELETE').map(w => decodeURIComponent(w.query.replace(/\+/g, ' ')));
  const left = await page.evaluate(() => TC.mineRows.saved);
  ok(d.length === 1 && /ZZZ 1100/.test(d[0]) && /ZZZ 1102/.test(d[0]) && !/ZZZ 1103/.test(d[0]) && !left.includes('ZZZ 1101') && left.includes('ZZZ 1103') && left.length === 31, 'd: the 3 unticked come off (one delete), the rest stay', { d, n: left.length });
  ok(/Removed 3 classes from Fall 2026/.test(await toastText(page)), 'd: toast with Undo', await toastText(page));
  await tap(page, '#toast .tundo'); await tick(page, 800);
  ok(await page.evaluate(() => ['ZZZ 1100', 'ZZZ 1101', 'ZZZ 1102'].every(c => TC.mineRows.saved.includes(c))), 'd: Undo saves the 3 back');
  ok(await page.evaluate(() => !document.querySelector('#scroll .any-bulk') && !anyBulk('2268')), 'd: asked once — answered, it doesn’t come back (even after Undo)');
  await tick(page, 800);
  ok(W(log, 'my_sections', 'POST').some(w => rowsOf(w).some(r => r.code === 'BUS 4401')), 'd: once answered, the one-section class is saved');
  ok(log.errors.length === 0, 'B: no page errors', log.errors);
  await close();
  /* Yes keeps them; a dark card */
  const o = await openApp({ port, tables: T, init: () => { try { localStorage.setItem('tc-theme', 'dark'); } catch (e) {} } });
  await o.page.waitForFunction(() => TC.ready && TC.mineRows, null, { timeout: 15000 }); await tick(o.page, 1200);
  await o.page.evaluate(() => { setTab('schedule'); A.schedTab('mine'); }); await tick(o.page, 500);
  const ps = await pairs(o.page, '#scroll .any-bulk .any-ct, #scroll .any-bulk .any-cs, #scroll .any-bulk .pbtn');
  ok(ps.length === 4 && !lowOf(ps).length, 'contrast (dark): the question card reads 4.5:1+', lowOf(ps));
  await shot(o.page, 'bulk-card-dark');
  await tap(o.page, '#scroll .any-bulk [data-a="anyBulkYes"]');
  ok(await o.page.evaluate(() => !document.querySelector('#scroll .any-bulk') && !anyBulk('2268') && ['ZZZ 1100', 'ZZZ 1127', 'BUS 4401', 'BUS 2201'].every(c => TC.mineRows.saved.includes(c))) && !W(o.log, 'saved_classes', 'DELETE').length, 'd: Yes keeps all of them and the question goes');
  await o.close();
}
/* the 10-minute rule: 8 with no section but 12+ saved at once → asked; spread over days → not */
{
  const T = base(); for (let i = 0; i < 7; i++) T.saved_classes.push(saved(ME, 'ZZZ ' + (2100 + i)));   /* + the fixtures' 5 at 2026-09-10T18:00 (BUS 2201 among them) */
  let o = await openApp({ port, tables: T }); await o.page.waitForFunction(() => TC.ready && TC.mineRows, null, { timeout: 15000 }); await tick(o.page, 800);
  ok(await o.page.evaluate(() => (anyBulk('2268') || []).length) === 8, 'd: 12 classes saved within 10 minutes, 8 with no section → asked about the 8');
  await o.close();
  const T2 = base(); for (let i = 0; i < 7; i++) T2.saved_classes.push(saved(ME, 'ZZZ ' + (2100 + i), '2268', `2026-10-0${i + 1}T18:00:00Z`));
  o = await openApp({ port, tables: T2 }); await o.page.waitForFunction(() => TC.ready && TC.mineRows, null, { timeout: 15000 }); await tick(o.page, 800);
  ok(await o.page.evaluate(() => anyBulk('2268') === null && !!document.querySelector('.any-home') === false), 'd: 8 with no section saved over a week → not asked');
  await o.close();
}

/* ===== C. combinations (unit) ===== */
{
  const o = await openApp({ port }); await o.page.waitForFunction(() => TC.ready, null, { timeout: 15000 });
  const r = await o.page.evaluate(() => {
    const S = (code, days, s, e) => ({ id: code + days + s, code, days, s, e, async: false });
    const A1 = S('A', 'MW', 600, 720), A2 = S('A', 'TR', 600, 720), B1 = S('B', 'MW', 600, 720), B2 = S('B', 'F', 540, 720);
    const one = anyCombos([[A1, A2], [B1, B2]], [S('X', 'MW', 610, 700)]);
    const two = anyCombos([[A1, A2], [B1, B2]], []);
    const zero = anyCombos([[A1], [B1]], []);
    /* 10 classes, each with the same 9 Monday hours: none fit (pigeonhole), and proving it takes far more than 5000 steps */
    const big = anyCombos(Array.from({ length: 10 }, (_, i) => Array.from({ length: 9 }, (_, j) => S('C' + i, 'M', 480 + 60 * j, 530 + 60 * j))), [], 5000);
    return { one: [one.n, one.pick && one.pick.map(x => x.id)], two: two.n, zero: zero.n, big: big.n };
  });
  ok(r.one[0] === 1 && r.one[1].join() === 'ATR600,BF540', 'combos: exactly one way to fit → found, with its sections', r.one);
  ok(r.two === 2 && r.zero === 0, 'combos: two ways → 2 (counting stops there); none → 0', r);
  ok(r.big === -1, 'combos: a search that runs too long is “not exactly one” (never preselects)', r.big);
  await o.close();
}

/* ===== D. the report's Pick your sections step (one term) ===== */
{
  const T = base();
  T.my_sections.push({ user_id: AVERY, term: '2268', code: 'FIX 2001', class_nbr: '71005', section: '01', instructor: 'Examplewood, Ada', days: 'TuTh 8:10AM - 9:00AM', status: 'enrolled', wl_pos: null });
  T.saved_classes.push(saved(AVERY, 'FIX 2001'));
  const { page, close, log } = await openApp({ port, tables: T, height: 900 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows, null, { timeout: 15000 }); await tick(page, 800);
  const row = (c, extra) => Object.assign({ cur: c, code: c, name: 'Fixture', term: 'Fall', year: 2026, _now: true, pick: true }, extra || {});
  const report = async rows => { await page.evaluate(rows => { UI.dpr = { rows, latestTerm: 'Fall 2026', audit: null, program: {} }; UI.sheet = { type: 'dprRead' }; render(true); A.dprSave(); }, rows); return until(page, () => !UI.busy.dpr, null, 40); };
  /* unique: FIX 1001 / FIX 1002 Sec 01 sit on your BUS 3438 → only Sec 02 + Sec 02 fit */
  await report([row('FIX 1001'), row('FIX 1002')]);
  let s = await page.evaluate(() => UI.sheet && UI.sheet.type === 'dprPick' ? { g: UI.sheet.groups.map(g => ({ t: g.term, c: g.classes, sel: g.sel, u: g.unique })), txt: document.getElementById('sheet').innerText.replace(/\s+/g, ' '), btn: document.querySelector('#sheet [data-a="dprPickSave"]').innerText, pressed: [...document.querySelectorAll('#sheet .any-sec[aria-pressed="true"]')].map(b => b.dataset.x) } : UI.sheet && UI.sheet.type);
  ok(s && s.g && s.g.length === 1 && s.g[0].u && s.g[0].sel['FIX 1001'] === '71002' && s.g[0].sel['FIX 1002'] === '71004' && s.pressed.length === 2, '2: right after the save, “Pick your sections” — the only combination that fits is pre-selected', s);
  ok(s && /Pick your sections/.test(s.txt) && /Fall 2026 · 2 classes/.test(s.txt) && /Only one set of sections fits together/.test(s.txt) && /Overlaps BUS 3438/.test(s.txt) && s.btn === 'Save these sections' && /Skip for now/.test(s.txt), '2: it says so; the clashing sections say “Overlaps BUS 3438”; one tap saves', s && s.txt.slice(0, 400));
  ok(!W(log, 'my_sections', 'POST').some(w => rowsOf(w).some(r => /^FIX/.test(r.code))), '2: nothing is written until the student saves');
  await shot(page, 'dpr-pick-unique-light');
  for (const th of ['light', 'dark']) { await setTheme(page, th); await tick(page, 200); const ps = await pairs(page, '#sheet .dr-h1, #sheet .dr-sub, #sheet .dpk-why, #sheet .dpk-one span, #sheet .dpk-h b, #sheet .any-sb .t b, #sheet .any-sm, #sheet .any-cl, #sheet .dr-link, #sheet .btn, #sheet .at-kick'); ok(ps.length >= 10 && !lowOf(ps).length, `contrast (${th}): the Pick your sections step reads 4.5:1+`, lowOf(ps)); if (th === 'dark') await shot(page, 'dpr-pick-unique-dark'); }
  await setTheme(page, 'light');
  await tap(page, '#sheet [data-a="dprPickSave"]'); await until(page, () => !UI.busy.dpk && !(UI.sheet && UI.sheet.type === 'dprPick'), null, 30);
  let w = W(log, 'my_sections', 'POST').filter(x => rowsOf(x).some(r => /^FIX 100/.test(r.code))).map(x => rowsOf(x)[0].class_nbr).sort();
  ok(w.join() === '71002,71004' && await page.evaluate(() => ['FIX 1001', 'FIX 1002'].every(c => personSecs('me').some(s => s.code === c && s.s != null))), '2: Save → both sections saved (my_sections) and on your week', w);
  ok(/2 classes on your week/.test(await toastText(page)), '2: toast says so', await toastText(page));
  /* not unique: two ways or more → nothing pre-selected; a friend's section is only a label */
  await page.evaluate(() => { UI.sheet = null; render(true); });
  await report([row('FIX 2001'), row('FIX 2002')]);
  s = await page.evaluate(() => UI.sheet && UI.sheet.type === 'dprPick' ? { sel: UI.sheet.groups[0].sel, u: UI.sheet.groups[0].unique, txt: document.getElementById('sheet').innerText.replace(/\s+/g, ' '), dis: document.querySelector('#sheet [data-a="dprPickSave"]').disabled } : null);
  ok(s && !s.u && !Object.keys(s.sel).length && s.dis && !/Only one set/.test(s.txt), '2: 2+ combinations → nothing pre-selected (Save waits for a tap)', s);
  ok(s && /1 friend in Sec 01/.test(s.txt) && !s.sel['FIX 2001'], '2: friends shown on their section (“1 friend in Sec 01”) — never picked for you', s && s.txt.slice(0, 500));
  await shot(page, 'dpr-pick-light');
  await setTheme(page, 'dark'); await tick(page, 200); await shot(page, 'dpr-pick-dark');
  { const ps = await pairs(page, '#sheet .any-fr > span:last-child, #sheet .any-sm, #sheet .any-sb .t .nw'); ok(ps.length >= 4 && !lowOf(ps).length, 'contrast (dark): friends’ label and section lines read 4.5:1+', lowOf(ps)); }
  await setTheme(page, 'light');
  await tap(page, '#sheet .any-sec[data-x="0|FIX 2001|71006"]');
  ok(await page.evaluate(() => UI.sheet.groups[0].sel['FIX 2001'] === '71006' && /Save 1 section/.test(document.querySelector('#sheet [data-a="dprPickSave"]').innerText)), '2: tap a section → picked; “Save 1 section”');
  await tap(page, '#sheet .any-sec[data-x="0|FIX 2001|71006"]');
  ok(await page.evaluate(() => !UI.sheet.groups[0].sel['FIX 2001']), '2: tap it again → unpicked');
  /* Skip for now: stays Anytime, and the My Classes card reminds later */
  await tap(page, '#sheet [data-a="dprPickSkip"]');
  ok(await page.evaluate(() => !(UI.sheet && UI.sheet.type === 'dprPick') && ['FIX 2001', 'FIX 2002'].every(c => PEOPLE.me.unplaced.includes(c))) && !W(log, 'my_sections', 'POST').some(x => rowsOf(x).some(r => /^FIX 200/.test(r.code))), '2: Skip for now — saved with no section (Anytime), nothing picked');
  ok(await page.evaluate(() => anyPickList('2268').map(x => x.code).sort().join()) === 'FIX 2001,FIX 2002', '2: … and the My Classes card lists them later (rule c)');
  /* none fit: FIX 3001's two sections both sit on your classes → nothing pre-selected */
  await page.evaluate(() => { UI.sheet = null; render(true); });
  await report([row('FIX 3001')]);
  s = await page.evaluate(() => UI.sheet && UI.sheet.type === 'dprPick' ? { sel: UI.sheet.groups[0].sel, n: UI.sheet.groups[0].combos } : null);
  ok(s && s.n === 0 && !Object.keys(s.sel).length, '2: no combination fits → nothing pre-selected', s);
  await page.evaluate(() => A.closeSheet()); await tick(page, 300);
  ok(await page.evaluate(() => !(UI.sheet && UI.sheet.type === 'dprPick')), '2: a tap outside is Skip for now');
  /* a class with ONE section in the report is pre-selected (it's the only one); no step when every class already has a section */
  await page.evaluate(() => { UI.sheet = null; render(true); });
  await report([row('BUS 4401')]);
  s = await page.evaluate(() => UI.sheet && UI.sheet.type);
  const w4401 = W(log, 'my_sections', 'POST').filter(x => rowsOf(x).some(r => r.code === 'BUS 4401'));
  ok(s === 'dprPick' && w4401.length === 0 && await page.evaluate(() => Object.keys(UI.sheet.groups[0].sel).length === 1 && /Only section/.test(document.getElementById('sheet').innerText)), '2: a one-section class is pre-selected (“Only section”), and the quiet save waits for the step', { s, w: w4401.length });
  await tap(page, '#sheet [data-a="dprPickSave"]'); await until(page, () => !UI.busy.dpk, null, 20);
  ok(W(log, 'my_sections', 'POST').filter(x => rowsOf(x).some(r => r.code === 'BUS 4401')).length === 1, '2: saved once (not again by the quiet save)');
  await page.evaluate(() => { UI.sheet = null; render(true); });
  await report([row('BUS 3438', { already: true, pick: false })]);
  ok(await page.evaluate(() => !(UI.sheet && UI.sheet.type === 'dprPick')), '2: nothing without a section → no step');
  ok(log.errors.length === 0, 'D: no page errors', log.errors);
  await close();
}

/* ===== E. two terms (choose in Spring 2027, now = Fall 2026): the now-term rules and the step for both ===== */
{
  const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25', MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '2274', label: 'Spring 2027' }] };
  const T = base();
  T.course_seats = T.course_seats.concat(T.course_seats.filter(r => r.term === '2268').map(r => Object.assign({}, r, { term: '2274' })));
  T.planner_prefs = [{ user_id: ME, priority: 'degree', units: 12 }];
  T.saved_classes.push(saved(ME, 'BUS 4401'), saved(ME, 'ECON 2303'), saved(ME, 'PHIL 3331'), saved(ROWAN, 'BUS 3346'), saved(ROWAN, 'ECON 2303', '2274'));
  const { page, close, log } = await openApp({ port, terms: SPRING_CFG, tables: T, height: 900 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.nowMineRows && TC.myHistory, null, { timeout: 15000 });
  await until(page, () => nowSecs('me').some(s => s.code === 'BUS 4401' && !s.oneSec), null, 30);
  const fall = await page.evaluate(() => ({ my: nowSecs('me').map(s => s.code + ':' + (s.s != null) + ':' + !!s.oneSec), unp: nowUnplaced('me'), hid: PEOPLE.me.nowHidden, rowan: nowSecs('22222222-2222-4222-8222-222222222222').filter(s => s.code === 'BUS 3346').map(s => [s.days, s.s, s.oneSec]), rowanSpring: (PEOPLE['22222222-2222-4222-8222-222222222222'].unplaced || []) }));
  const wf = W(log, 'my_sections', 'POST').filter(x => rowsOf(x).some(r => r.code === 'BUS 4401'));
  ok(wf.length === 1 && rowsOf(wf[0])[0].term === '2268' && fall.my.includes('BUS 4401:true:false'), 'b (Fall): BUS 4401, one Fall section → saved under 2268 when you open the app', { wf: wf.map(x => x.body), fall });
  ok(fall.unp.includes('ECON 2303') && !W(log, 'my_sections', 'POST').some(x => rowsOf(x).some(r => r.code === 'ECON 2303')), 'b (Fall): ECON 2303 (2 Fall sections) is never picked');
  ok(fall.hid.includes('PHIL 3331') && !fall.unp.includes('PHIL 3331'), 'a (Fall): PHIL 3331 (finished Spring 2026) is hidden from Fall', fall);
  ok(fall.rowan.length === 1 && fall.rowan[0][0] === 'MW' && fall.rowan[0][1] != null && fall.rowan[0][2], 'b (Fall): friends’ view — Rowan’s BUS 3346 shows its one Fall section’s times', fall.rowan);
  ok(fall.rowanSpring.includes('ECON 2303'), 'b (Spring): Rowan’s ECON 2303 (2 Spring sections) stays with no section', fall.rowanSpring);
  ok(await page.evaluate(() => /In BUS 3346/.test(status('22222222-2222-4222-8222-222222222222').t || '') || status('22222222-2222-4222-8222-222222222222').t != null), 'b: Rowan’s status/story reads his week (BUS 3346 included)');
  await page.evaluate(() => { setTab('schedule'); A.schedTab('mine'); A.pickMineTerm('Fall 2026'); }); await tick(page, 800);
  const top = await page.evaluate(() => ({ card: (document.querySelector('#scroll .any-times') || {}).innerText, hid: (document.querySelector('#scroll .any-hid') || {}).innerText }));
  ok(/Add times to 1 class/.test(top.card || '') && /already taken is hidden/.test(top.hid || ''), 'c (Fall): the Fall My Classes has the card (ECON 2303) and the hidden note', top);
  await page.evaluate(() => A.anyPickOpen('2268')); await tick(page, 600);
  const ft = await sheetText(page);
  ok(/Fall 2026/.test(ft) && /Sec 03/.test(ft) && /Sec 04/.test(ft) && /1 friend in Sec 03/.test(ft), 'c (Fall): the sheet lists ECON 2303’s Fall sections (Rowan in Sec 03 in Fall)', ft.slice(0, 300));
  await page.evaluate(() => { UI.sheet = null; render(true); });
  /* the step: Fall in-progress + Spring registered */
  await page.evaluate(() => { UI.dpr = { rows: [
    { cur: 'FIX 1001', code: 'FIX 1001', term: 'Fall', year: 2026, _now: true, pick: true }, { cur: 'FIX 1002', code: 'FIX 1002', term: 'Fall', year: 2026, _now: true, pick: true },
    { cur: 'FIX 2001', code: 'FIX 2001', term: 'Spring', year: 2027, _next: true, pick: true }], latestTerm: 'Fall 2026', nextTerm: 'Spring 2027', audit: null, program: {} }; UI.sheet = { type: 'dprRead' }; render(true); A.dprSave(); });
  await until(page, () => !UI.busy.dpr, null, 40);
  const s = await page.evaluate(() => UI.sheet && UI.sheet.type === 'dprPick' ? { g: UI.sheet.groups.map(g => ({ t: g.term, sel: g.sel, u: g.unique, c: g.classes })), txt: document.getElementById('sheet').innerText.replace(/\s+/g, ' ') } : UI.sheet && UI.sheet.type);
  ok(s && s.g && s.g.length === 2 && s.g[0].t === '2268' && s.g[0].u && s.g[0].sel['FIX 1001'] === 'n:2268:71002' && s.g[1].t === '2274' && !s.g[1].u && !Object.keys(s.g[1].sel).length, '2: both terms — Fall’s only combination pre-selected; Spring’s FIX 2001 (two ways) not', s && s.g);
  ok(s && /Fall 2026 and Spring 2027 · 3 classes/.test(s.txt), '2: “Fall 2026 and Spring 2027 · 3 classes”', s && s.txt.slice(0, 200));
  await shot(page, 'dpr-pick-two-terms-light');
  await tap(page, '#sheet .any-sec[data-x="1|FIX 2001|71005"]');
  await tap(page, '#sheet [data-a="dprPickSave"]'); await until(page, () => !UI.busy.dpk && !(UI.sheet && UI.sheet.type === 'dprPick'), null, 30);
  const w = W(log, 'my_sections', 'POST').map(x => rowsOf(x)[0]).filter(r => /^FIX/.test(r.code)).map(r => r.code + '@' + r.term + '#' + r.class_nbr).sort();
  ok(w.join() === 'FIX 1001@2268#71002,FIX 1002@2268#71004,FIX 2001@2274#71005', '2: saved under the right terms — Fall’s two (2268), Spring’s one (2274)', w);
  ok(await page.evaluate(() => nowSecs('me').some(s => s.code === 'FIX 1001' && s.s != null) && personSecs('me').some(s => s.code === 'FIX 2001' && s.s != null)), '2: on the Fall week and the Spring week');
  ok(log.errors.length === 0, 'E: no page errors', log.errors);
  await close();
}
console.log(`\ncheck-anytime-sections-2026-10-31: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:\n  ' + fails.join('\n  ')); process.exit(1); }
