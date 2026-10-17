/* check-desktop-reg-timeline — Home's registration timeline card and the Friends tab's "Registration days" strip
   (website reg-timeline-2026-10-16; the two mockups the owner approved). Runs the REAL index.html in Chromium, signed in, against the
   PostgREST stand-in, with a fake clock for each state.
   Run: APP_DIR=<repo> node check-desktop-reg-timeline.mjs [--only name] [--quiet]   (APP_PORT to move off 8497)
   The promises:
   · ONE card "Spring 2027": a dot timeline of at most six rows — Your Round 1, Your Round 2, Classes begin, Last day to add / drop /
     withdraw; only the NEXT row is emphasised ("in N days"); past rows are checks; once classes begin Round 1 and 2 fold into
     "Registration done"; "Your game plan" is the one button until open enrollment ends (Jan 22); "All dates" lists the rest;
     dismissible; the old green "Your day…" line and "Change your registration day" button are gone.
   · Round 1 is registration_days exactly as before (the phone's table: same select, same upsert). Round 2 is added inline (date +
     time, Save / Cancel) and is written to registration_round2 only; until that table exists it stays on the device and goes up once.
   · Friends tab: a strip above Messages with friends' faces grouped by day, your own row highlighted, "N friends haven't set theirs";
     Round 1 days until Round 1 closes, Round 2 days (day only, never a time) until Nov 17, then gone; chips at phone width. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 700) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const BASE = +(process.env.APP_PORT || 8497);
let portN = 0; const open = [];
const mk = async (o = {}) => { while (open.length >= 3) { try { await open.shift().close(); } catch (e) {} } const a = await openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: '2026-10-16T10:30:00-07:00', port: BASE + (portN++ % 6) }, o)); open.push(a); return a; };
/* the stand-in answers in real time, the page's clock is fake: wait until what we are waiting for is true */
const until = async (page, fn, n = 30) => { for (let i = 0; i < n; i++) { if (await page.evaluate(fn)) return true; await tick(page, 200); } return false; };
const T = {};
const test = (name, fn) => { T[name] = fn; };
const ME = FX.ME.id, [AVERY, ROWAN, SKY, QUINN, HARPER] = FX.FRIENDS.map(f => f.id);
const tables = ({ r1, r2 } = {}) => {
  const t = JSON.parse(JSON.stringify(FX.TABLES));
  t.registration_days = r1 ? [Object.assign({ user_id: ME, term: '2274', shared: true, updated_at: '2026-10-13T00:00:00Z' }, r1)] : [];
  t.registration_round2 = r2 ? [Object.assign({ user_id: ME, term: '2274', updated_at: '2026-10-13T00:00:00Z' }, r2)] : [];
  return t;
};
const R1 = { day: '2026-10-21', at_time: '11:00:00' }, R2 = { day: '2026-11-05', at_time: '09:00:00' };
const norm = t => String(t || '').replace(/\s+/g, ' ').trim();
/* what the card shows */
const card = page => page.evaluate(() => {
  const c = document.getElementById('hmRegCard'), n = t => (t || '').replace(/\s+/g, ' ').trim(); if (!c) return null;
  return { head: n((c.querySelector('.tl-hd') || {}).textContent), fold: n((c.querySelector('.tl-fold') || {}).textContent), nextN: c.querySelectorAll('.tl-next').length,
    rows: [...c.querySelectorAll('.tl-li')].map(r => ({ k: r.dataset.tlRow, cls: r.className.replace('tl-li', '').trim(), t: n(r.querySelector('.tl-t').textContent), s: n((r.querySelector('.tl-s') || {}).textContent), r: n(r.querySelector('.tl-r').textContent),
      pen: !!r.querySelector('.tl-pen'), add: !!r.querySelector('.tl-add'), check: !!r.querySelector('.tl-dot svg') })),
    go: !!c.querySelector('.tl-go'), all: !!c.querySelector('.tl-all'), x: !!c.querySelector('.hm-regx'), text: n(c.innerText), over: c.scrollWidth > c.clientWidth + 1 };
});
const rowBy = (c, k) => c.rows.find(r => r.k === k);
const w2 = log => log.writes.filter(w => w.table === 'registration_round2');
const w1 = log => log.writes.filter(w => w.table === 'registration_days');

test('states', async () => {
  /* A. before Round 1: Round 1 set (next), Round 2 empty */
  { const { page, log } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
    const c = await card(page);
    ok(c && /Spring 2027/.test(c.head) && /Registration & key dates/.test(c.head), 'A: one card titled “Spring 2027”', c && c.head);
    ok(c.rows.map(r => r.k).join() === 'r1,r2,begin,add,drop,withdraw' && c.rows.length <= 6, 'A: six rows — Round 1, Round 2, classes begin, add, drop, withdraw', c.rows.map(r => r.k));
    ok(c.nextN === 1 && /tl-next/.test(rowBy(c, 'r1').cls) && rowBy(c, 'r1').r.startsWith('in 5 days') && rowBy(c, 'r1').s === 'Wed, Oct 21 · 11:00 AM', 'A: only Round 1 is emphasised: “in 5 days”, Wed, Oct 21 · 11:00 AM', rowBy(c, 'r1'));
    ok(rowBy(c, 'r1').pen && !rowBy(c, 'r1').add, 'A: Round 1 has a pencil', rowBy(c, 'r1'));
    ok(/tl-empty/.test(rowBy(c, 'r2').cls) && rowBy(c, 'r2').add && /^Your Round 2 Opens Nov 4 \+ Add$/.test(rowBy(c, 'r2').t + ' ' + rowBy(c, 'r2').s + ' ' + rowBy(c, 'r2').r), 'A: Round 2 is empty: “+ Add · Opens Nov 4”', rowBy(c, 'r2'));
    ok(rowBy(c, 'begin').r === 'Mon, Jan 25' && rowBy(c, 'add').r === 'Fri, Jan 29' && rowBy(c, 'drop').r === 'Fri, Feb 5' && rowBy(c, 'withdraw').r === 'Fri, Apr 23', 'A: Jan 25, Jan 29, Feb 5, Apr 23 (the registrar’s dates)', c.rows);
    ok(c.go && c.all && c.x && !/Your day:|Change your registration day/.test(c.text), 'A: “Your game plan”, “All dates”, the x; no “Your day…” line, no “Change your registration day”', c.text);
    ok(await page.evaluate(() => !document.querySelector('#hmRegCard .btn') && document.querySelectorAll('#hmRegCard .tl-go').length === 1), 'A: “Your game plan” is the only primary button');
    ok(log.errors.length === 0, 'A: no page errors', log.errors); }
  /* B. between the rounds (Nov 2): Round 1 done, Round 2 next */
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2026-11-02T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(/tl-done/.test(rowBy(c, 'r1').cls) && rowBy(c, 'r1').check && rowBy(c, 'r1').r === 'Wed, Oct 21', 'B: Round 1 is a small grey check with its date', rowBy(c, 'r1'));
    ok(c.nextN === 1 && /tl-next/.test(rowBy(c, 'r2').cls) && rowBy(c, 'r2').r.startsWith('in 3 days') && rowBy(c, 'r2').s === 'Thu, Nov 5 · 9:00 AM', 'B: Round 2 is next: “in 3 days”, Thu, Nov 5 · 9:00 AM', rowBy(c, 'r2'));
    ok(c.go, 'B: the game plan button is still there'); }
  /* after Round 1 ends the pencil on Round 1 goes (its sheet only offers Round 1's days); Round 2's stays until Nov 17 */
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2026-11-10T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(!rowBy(c, 'r1').pen && rowBy(c, 'r2').pen && /tl-done/.test(rowBy(c, 'r2').cls), 'Nov 10: Round 1 has no pencil, Round 2 (done) still has one', c.rows.slice(0, 2)); }
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2026-11-18T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(!rowBy(c, 'r1').pen && !rowBy(c, 'r2').pen && c.go, 'Nov 18 (open enrollment): no pencils; the game plan is still there', c.rows.slice(0, 2)); }
  /* nothing set, Round 1 over: that row is not drawn; Round 2 still invites */
  { const { page } = await mk({ tables: tables(), time: '2026-11-10T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(c.rows.map(r => r.k).join() === 'r2,begin,add,drop,withdraw' && rowBy(c, 'r2').add && /^Open now · ends Nov 17$/.test(rowBy(c, 'r2').s), 'Nov 10, nothing set: no empty Round 1 row; Round 2 says “Open now · ends Nov 17”', c.rows); }
  /* the last day to add is the only row that carries a hint */
  /* C. term underway (Jan 27) */
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2027-01-27T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(/Key dates/.test(c.head) && /^Registration done/.test(c.fold) && /Round 1 Oct 21 · Round 2 Nov 5/.test(c.fold), 'C (Jan 27): “Registration done · Round 1 Oct 21 · Round 2 Nov 5”', c.fold);
    ok(c.rows.map(r => r.k).join() === 'begin,add,drop,withdraw' && rowBy(c, 'begin').t === 'Classes began' && /tl-done/.test(rowBy(c, 'begin').cls), 'C: Round 1/2 are folded away; “Classes began” is a check', c.rows);
    ok(c.nextN === 1 && /tl-next/.test(rowBy(c, 'add').cls) && rowBy(c, 'add').r.startsWith('in 2 days') && /permission number/.test(rowBy(c, 'add').s), 'C: the next row is the last day to add: “in 2 days”, after it you need a permission number', rowBy(c, 'add'));
    ok(!c.go && c.all, 'C: no game plan button once open enrollment is over; “All dates” stays', c); }
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2027-01-22T20:00:00-08:00' }); await tick(page, 1500);
    ok((await card(page)).go, 'Jan 22 (open enrollment’s last day, evening): the game plan button is still there'); }
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2027-04-26T10:30:00-07:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(c.rows.map(r => r.k).join() === 'begin,add,drop,withdraw,last' && rowBy(c, 'last').r === 'in 18 days' && /tl-next/.test(rowBy(c, 'last').cls), 'Apr 26: after the withdraw date the last day of classes (May 14) is next', c.rows); }
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2027-05-17T10:30:00-07:00' }); await tick(page, 1500);
    ok(await card(page) === null, 'May 17: the term is over, the card is gone'); }
});

test('round2', async () => {
  const { page, log } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
  await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300);
  const e = await page.evaluate(() => { const d = document.querySelector('#hmRegCard .tl-in[data-tl-f="day"]'), t = document.querySelector('#hmRegCard .tl-in[data-tl-f="time"]'); return { d: d && [d.type, d.min, d.max], t: t && t.type, lab: (document.querySelector('#hmRegCard .tl-lab') || {}).textContent, save: !!document.querySelector('#hmRegCard .tl-save'), cancel: !!document.querySelector('#hmRegCard .tl-cancel'), focus: document.activeElement && document.activeElement.getAttribute('data-tl-key') }; });
  ok(e.d && e.d[0] === 'date' && e.d[1] === '2026-11-05' && e.d[2] === '2026-11-17' && e.t === 'time' && e.save && e.cancel && e.focus === 'd2' && /Round 2 runs Nov 5–17/.test(e.lab), 'inline editor: date (Nov 5–17) + time, Save / Cancel, focus on the date', e);
  /* Cancel writes nothing */
  await page.click('#hmRegCard .tl-cancel'); await tick(page, 300);
  ok(w2(log).length === 0 && await page.evaluate(() => !document.querySelector('#hmRegCard .tl-edit') && !!document.querySelector('#hmRegCard [data-tl-key="add2"]')), 'Cancel closes it and writes nothing');
  await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300);
  const sv = async () => { await page.click('#hmRegCard .tl-save'); await tick(page, 600); return page.evaluate(() => (document.querySelector('#hmRegCard .tl-err') || {}).textContent || ''); };
  ok(await page.evaluate(() => document.querySelector('#hmRegCard .tl-in[data-tl-f="day"]').value) === '2026-11-05', 'the date starts on Round 2’s first weekday (Nov 5)');
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '');
  ok(/Pick your day first/.test(await sv()) && w2(log).length === 0, 'Save with no day says so and writes nothing');
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-07'); const weekend = await sv();
  ok(/weekdays/.test(weekend) && w2(log).length === 0, 'a Saturday is refused', weekend);
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-20'); const late = await sv();
  ok(/Round 2 runs Nov 5–17/.test(late) && w2(log).length === 0, 'a day after Round 2 is refused', late);
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-04'); const early = await sv();
  ok(/Round 2 runs Nov 5–17/.test(early) && w2(log).length === 0, 'Nov 4 (Round 2 opens, appointments start Nov 5) is refused', early);
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-11'); const vet = await sv();
  ok(/Nov 11 is Veterans Day/.test(vet) && w2(log).length === 0, 'Nov 11 (Veterans Day) is refused', vet);
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-05'); await page.fill('#hmRegCard .tl-in[data-tl-f="time"]', '09:00');
  await page.click('#hmRegCard .tl-save'); await tick(page, 900);
  const w = w2(log);
  ok(w.length === 1 && w[0].m === 'POST' && /on_conflict=user_id%2Cterm/.test(w[0].query), 'Save: one upsert on registration_round2 (user_id, term)', w.map(x => x.m + ' ' + x.query));
  const b = w[0] && w[0].body;
  ok(b && b.user_id === ME && b.term === '2274' && b.day === '2026-11-05' && b.at_time === '09:00' && typeof b.updated_at === 'string' && b.shared === true, 'Save: {user_id, term:2274, day, at_time, shared}', b);
  ok(w1(log).length === 0, 'Round 2 never touches registration_days (the phone’s table)', w1(log));
  const c = await card(page);
  ok(rowBy(c, 'r2').r === 'Thu, Nov 5' && rowBy(c, 'r2').s === '9:00 AM' && rowBy(c, 'r2').pen && !rowBy(c, 'r2').add && !/tl-editing/.test(rowBy(c, 'r2').cls), 'the row now says Thu, Nov 5 and 9:00 AM, with a pencil', rowBy(c, 'r2'));
  ok(await page.evaluate(() => (document.getElementById('frToast') || {}).textContent) === 'Your Round 2 day is saved', 'a toast says it is saved');
  ok(await page.evaluate(([u]) => localStorage.getItem('professify_regday2_' + u + '_2274'), [ME]) === '{"day":"2026-11-05","time":"09:00","shared":true}', 'kept on this device, nothing waiting');
  ok(await page.evaluate(() => document.activeElement && document.activeElement.getAttribute('data-tl-key')) === 'pen2', 'focus goes to the row’s new pencil');
  /* edit it with the pencil; Remove deletes */
  await page.click('#hmRegCard [data-tl-key="pen2"]'); await tick(page, 300);
  ok(await page.evaluate(() => document.querySelector('#hmRegCard .tl-in[data-tl-f="day"]').value === '2026-11-05' && document.querySelector('#hmRegCard .tl-in[data-tl-f="time"]').value === '09:00'), 'the pencil opens it on what you saved');
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-06'); await page.press('#hmRegCard .tl-in[data-tl-f="day"]', 'Enter'); await tick(page, 800);
  ok(w2(log).length === 2 && w2(log)[1].body.day === '2026-11-06' && w2(log)[1].body.at_time === '09:00', 'Enter saves; the second write carries the new day', w2(log).map(x => x.body));
  await page.click('#hmRegCard [data-tl-key="pen2"]'); await tick(page, 300);
  await page.click('#hmRegCard .tl-rm'); await tick(page, 800);
  const del = w2(log).filter(x => x.m === 'DELETE');
  ok(del.length === 1 && decodeURIComponent(del[0].query).includes('user_id=eq.' + ME) && /term=eq\.2274/.test(del[0].query), 'Remove: a delete for your user and term 2274', del.map(x => x.query));
  ok(await page.evaluate(([u]) => localStorage.getItem('professify_regday2_' + u + '_2274'), [ME]) === null && rowBy(await card(page), 'r2').add, 'Remove: nothing kept, the row invites you again');
  /* Escape closes the editor */
  await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300); await page.keyboard.press('Escape'); await tick(page, 300);
  ok(await page.evaluate(() => !document.querySelector('#hmRegCard .tl-edit')), 'Escape closes the editor');
  ok(log.errors.length === 0, 'round 2: no page errors', log.errors);
});

test('round1', async () => {
  /* Round 1 is what the phone has: the same read, the same write, through the same sheet */
  const { page, log } = await mk({ tables: tables() }); await tick(page, 1500);
  const reads = log.reads.map(r => decodeURIComponent(r));
  ok(reads.some(r => /^registration_days\?select=day,at_time,shared,updated_at&user_id=eq\.[^&]+&term=eq\.2274$/.test(r)), 'Round 1: the same read as the phone', reads.filter(r => /registration/.test(r)));
  await page.click('#hmRegCard [data-tl-key="add1"]'); await tick(page, 400);
  await page.click('.rg-d[data-day="2026-10-22"]'); await page.fill('#rgTime', '2:30p'); await page.click('[data-rg-act="save"]'); await tick(page, 900); await until(page, () => !document.getElementById('rgBack').classList.contains('open')); await tick(page, 300);
  const w = w1(log), b = w[0] && w[0].body;
  ok(w.length === 1 && /on_conflict=user_id%2Cterm/.test(w[0].query) && b.day === '2026-10-22' && b.at_time === '14:30' && b.shared === true && b.term === '2274' && Object.keys(b).sort().join() === 'at_time,day,shared,term,updated_at,user_id', 'Round 1: the phone’s upsert, field for field', b);
  const c = await card(page);
  ok(rowBy(c, 'r1').s === 'Thu, Oct 22 · 2:30 PM' && rowBy(c, 'r1').pen && w2(log).length === 0, 'Round 1: the row says Thu, Oct 22 · 2:30 PM, and registration_round2 was not touched', rowBy(c, 'r1'));
  const fk = await page.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '.' + a.className + ' ' + a.getAttribute('data-tl-key') : 'none'; });
  ok(/pen1$/.test(fk), 'focus goes back to the pencil after the sheet closes', fk);
  ok(log.errors.length === 0, 'round 1: no page errors', log.errors);
});

test('gap', async () => {
  /* the table is not there yet: Round 2 stays on this device (no hammering), then goes up once when it is */
  const gone = { status: 404, body: JSON.stringify({ code: 'PGRST205', message: "Could not find the table 'public.registration_round2' in the schema cache" }) };
  let hits = 0; const hook = (url, m) => url.pathname === '/rest/v1/registration_round2' ? (m !== 'GET' && hits++, gone) : null;
  const o = await mk({ tables: tables({ r1: R1 }), hook }); await tick(o.page, 1500);
  await o.page.click('#hmRegCard [data-tl-key="add2"]'); await tick(o.page, 300);
  await o.page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-05'); await o.page.click('#hmRegCard .tl-save'); await tick(o.page, 900);
  const c = await card(o.page);
  ok(rowBy(c, 'r2').r === 'Thu, Nov 5' && rowBy(c, 'r2').s === '', 'no table: the row still says Thu, Nov 5 (nothing alarming)', rowBy(c, 'r2'));
  ok(await o.page.evaluate(() => (document.getElementById('frToast') || {}).textContent) === 'Saved on this device', 'no table: the toast says “Saved on this device”');
  const kept = JSON.parse(await o.page.evaluate(([u]) => localStorage.getItem('professify_regday2_' + u + '_2274'), [ME]));
  ok(kept && kept.day === '2026-11-05' && kept.pending === true, 'no table: kept on the device, marked as waiting', kept);
  const n = hits;
  await o.page.evaluate(() => window.dispatchEvent(new Event('online'))); await o.page.clock.runFor(61000); await tick(o.page, 500);
  ok(hits === 0 && n === 0, 'no table: the read already said so, so nothing is written, now or a minute later', { n, now: hits });
  ok(o.log.errors.length === 0, 'no table: no page errors', o.log.errors);
  await o.close();
  /* the table appears: a fresh load sends what this device kept, once */
  const init = `try{ if(!localStorage.getItem('__seeded')){ localStorage.setItem('__seeded','1'); localStorage.setItem('professify_regday2_${ME}_2274', JSON.stringify({ day:'2026-11-05', time:'09:00', at: ${Date.parse('2026-10-16T10:00:00-07:00')}, pending:true })); } }catch(e){}`;
  const p = await mk({ tables: tables({ r1: R1 }), init }); await tick(p.page, 1800);
  const w = w2(p.log);
  ok(w.length === 1 && w[0].m === 'POST' && w[0].body.day === '2026-11-05' && w[0].body.at_time === '09:00' && w[0].body.user_id === ME, 'the table is there now: what the device kept goes up once', w.map(x => x.body));
  ok(JSON.parse(await p.page.evaluate(([u]) => localStorage.getItem('professify_regday2_' + u + '_2274'), [ME])).pending === undefined, 'and nothing is waiting any more');
  await p.page.evaluate(() => { const l = TCReg.loadMine2(); }); await tick(p.page, 800);
  ok(w2(p.log).length === 1, 'a later load does not send it again', w2(p.log).length);
  /* the account's newer row beats an older device copy */
  const init2 = `try{ if(!localStorage.getItem('__seeded')){ localStorage.setItem('__seeded','1'); localStorage.setItem('professify_regday2_${ME}_2274', JSON.stringify({ day:'2026-11-05', time:'09:00', at: ${Date.parse('2026-10-14T10:00:00-07:00')}, pending:true })); } }catch(e){}`;
  const q = await mk({ tables: tables({ r1: R1, r2: { day: '2026-11-09', at_time: '10:00:00', updated_at: '2026-10-15T00:00:00Z' } }), init: init2 }); await tick(q.page, 1800);
  ok(w2(q.log).length === 0 && rowBy(await card(q.page), 'r2').r === 'Mon, Nov 9' && rowBy(await card(q.page), 'r2').s === '10:00 AM', 'a newer row on the account is not overwritten by an older device copy', w2(q.log).length);
});

test('allDates', async () => {
  const { page } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
  await page.click('#hmRegCard .tl-all'); await tick(page, 400);
  const m = await page.evaluate(() => ({ open: document.getElementById('tlBack').classList.contains('open'), role: document.getElementById('tlBack').getAttribute('role'), title: document.getElementById('tlAllT').textContent,
    rows: [...document.querySelectorAll('#tlModal .tl-dates li')].map(li => li.querySelector('span').textContent + ' | ' + li.querySelector('b').textContent), link: (document.querySelector('#tlModal a') || {}).href }));
  ok(m.open && m.role === 'dialog' && m.title === 'Spring 2027 dates', '“All dates” opens a dialog', m);
  ok(JSON.stringify(m.rows) === JSON.stringify(['Last day to add with a permission number | Fri, Feb 12', 'Last day to change CR/NC | Fri, Mar 26', 'Spring break | Mar 15–21', 'Last day to withdraw (reasons beyond your control) · last day of classes | Fri, May 14', 'Final exams | May 15, 17–21']), 'it lists permission-number add Feb 12, CR/NC Mar 26, spring break Mar 15–21, May 14 (withdraw for reasons beyond your control · last day of classes), finals May 15 and 17–21', m.rows);
  ok(m.link === 'https://registrar.calpoly.edu/spring-semester-planning-calendar', 'it points at the registrar’s calendar', m.link);
  await page.keyboard.press('Escape'); await tick(page, 300);
  ok(await page.evaluate(() => !document.getElementById('tlBack').classList.contains('open') && document.activeElement && document.activeElement.getAttribute('data-tl-key') === 'all'), 'Escape closes it and focus goes back to “All dates”');
  /* only what is still to come */
  const l = await mk({ tables: tables({ r1: R1 }), time: '2027-03-20T10:00:00-07:00' }); await tick(l.page, 1500);
  await l.page.click('#hmRegCard .tl-all'); await tick(l.page, 400);
  const rest = await l.page.evaluate(() => [...document.querySelectorAll('#tlModal .tl-dates li')].map(li => li.querySelector('span').textContent));
  ok(rest.length === 4 && rest[0] === 'Last day to change CR/NC' && rest[1] === 'Spring break' && /^Last day to withdraw \(reasons beyond your control\) · last day of classes$/.test(rest[2]) && rest[3] === 'Final exams', 'on Mar 20 (in spring break) the permission-number date (Feb 12) is gone and the rest are still listed', rest);
});

test('dismiss', async () => {
  const { page } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
  await page.click('#hmRegCard .hm-regx'); await tick(page, 400);
  ok(await page.evaluate(() => !document.getElementById('hmRegCard') && localStorage.getItem('professify_dismiss_regtl_11111111-1111-4111-8111-111111111111_2274') === '1'), 'x dismisses it, remembered under your own user id', await page.evaluate(() => Object.keys(localStorage).filter(k => /dismiss/.test(k))));
  await page.evaluate(() => { renderHome(); }); await tick(page, 600);
  ok(await page.evaluate(() => !document.getElementById('hmRegCard')), 'a re-render does not bring it back');
  /* the old banner's dismissal does not hide the new card */
  const o = await mk({ tables: tables({ r1: R1 }), init: () => { try { localStorage.setItem('professify_dismiss_reg_2026-10-19', '1'); } catch (e) {} } }); await tick(o.page, 1500);
  ok(await o.page.evaluate(() => !!document.getElementById('hmRegCard')), 'a student who closed the old “Round 1 opens” card still sees the timeline once');
});

const strip = (page) => page.evaluate(() => {
  const e = document.getElementById('frRegStrip'), n = t => (t || '').replace(/\s+/g, ' ').trim();
  return { rows: [...(e ? e.querySelectorAll('.rs-row') : [])].map(r => ({ day: n([...r.querySelector('.rs-d').children].map(c => c.textContent).join(' ')), names: n(r.querySelector('.rs-n').textContent), rel: n(r.querySelector('.rs-rel').textContent), me: r.classList.contains('rs-me'),
      faces: r.querySelectorAll('.rs-fb').length })), miss: n((e && e.querySelector('.rs-ft span') || {}).textContent), round: n((e && e.querySelector('.rs-rnd') || {}).textContent), text: n(e ? e.innerText : ''), empty: !e || e.innerHTML.trim() === '' };
});
const F1 = [{ user_id: AVERY, day: '2026-10-21', at_time: '08:00:00' }, { user_id: ROWAN, day: '2026-10-20', at_time: '08:00:00' }, { user_id: SKY, day: '2026-10-22', at_time: '09:30:00' }];
const F2 = [{ user_id: AVERY, day: '2026-11-05' }, { user_id: ROWAN, day: '2026-11-05' }, { user_id: SKY, day: '2026-11-09' }];
const rpcs = (a, b) => Object.assign({}, FX.RPC, { friend_registration_days: a, friend_registration_round2: b });
const friendsTab = async page => { await page.evaluate(() => show('friends')); await tick(page, 600); };

test('strip', async () => {
  /* Round 1 */
  { const { page, log } = await mk({ tables: tables({ r1: R1 }), rpc: rpcs(F1, F2) }); await tick(page, 1800);
    const s = await strip(page);
    ok(s.round === 'Round 1 · Oct 19–Nov 3' && s.rows.map(r => r.day + '|' + r.names + '|' + r.rel).join(' ; ') === 'Tue Oct 20 8a|Rowan Testa|1 day before you ; Wed Oct 21 8a|Avery Quill|same day as you ; Wed Oct 21 11a|You|your day ; Thu Oct 22 9:30a|Sky Placeholder|1 day after you', 'strip: Round 1 days, soonest first, your row in its place, friends’ times as the Schedule card showed them', s);
    ok(s.rows.filter(r => r.me).length === 1 && s.rows[2].me && s.miss === '2 friends haven’t set theirs', 'strip: only your row is highlighted; “2 friends haven’t set theirs”', s);
    ok(log.rpcs.filter(r => r.fn === 'friend_registration_round2').length === 0, 'strip: Round 2’s days are not asked for until Round 1 is over', log.rpcs.map(r => r.fn));
    await friendsTab(page);
    const pos = await page.evaluate(() => { const a = document.getElementById('frRegStrip').getBoundingClientRect(), m = document.getElementById('frMsgSec').getBoundingClientRect(); return { aTop: Math.round(a.top), aBottom: Math.round(a.bottom), mTop: Math.round(m.top), w: Math.round(a.width), vis: a.height > 0 }; });
    ok(pos.vis && pos.aBottom <= pos.mTop, 'strip: it sits above the Messages list', pos);
    ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'strip: no sideways scroll at 1440');
    ok(log.errors.length === 0, 'strip: no page errors', log.errors); }
  /* between the rounds: Round 2 days, day only (a time in the data is never shown) */
  { const F2t = F2.map(r => Object.assign({ at_time: '09:00:00' }, r));
    const { page, log } = await mk({ tables: tables({ r1: R1, r2: R2 }), rpc: rpcs(F1, F2t), time: '2026-11-05T08:00:00-08:00' }); await tick(page, 1800);
    const s = await strip(page);
    ok(s.round === 'Round 2 · Nov 5–17' && s.rows.map(r => r.day + '|' + r.names + '|' + r.rel).join(' ; ') === 'Today|You · Avery, Rowan|your day ; Mon Nov 9|Sky Placeholder|4 days after you', 'strip: between the rounds it shows Round 2 days, day only', s);
    ok(!/\d(:\d\d)?[ap]\b/.test(s.text.replace(/Nov 4–17/, '')) && s.miss === '2 friends haven’t set theirs', 'strip: Round 2 never shows a time; “2 friends haven’t set theirs”', s.text);
    ok(log.rpcs.filter(r => r.fn === 'friend_registration_round2').every(r => r.body && r.body.p_term === '2274') && log.rpcs.filter(r => r.fn === 'friend_registration_days').length === 0, 'strip: Round 2’s RPC is asked for term 2274, Round 1’s no more');
    ok(s.rows[0].me && s.rows[0].faces === 3, 'strip: your row carries your face and your friends’', s.rows[0]); }
  /* after Round 2 closes (Nov 17): gone */
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), rpc: rpcs(F1, [{ user_id: SKY, day: '2026-11-17' }]), time: '2026-11-17T20:00:00-08:00' }); await tick(page, 1800);
    ok((await strip(page)).rows.length > 0, 'strip: on Nov 17 itself (evening) it is still there');
    const o = await mk({ tables: tables({ r1: R1, r2: R2 }), rpc: rpcs(F1, F2), time: '2026-11-18T09:00:00-08:00' }); await tick(o.page, 1800);
    const s = await strip(o.page);
    ok(s.empty && o.log.rpcs.filter(r => /^friend_registration/.test(r.fn)).length === 0, 'strip: from Nov 18 it is gone entirely and nothing is asked', s); }
  /* before Round 1 has anyone, and nothing set */
  { const { page } = await mk({ tables: tables(), rpc: rpcs([], []) }); await tick(page, 1800);
    ok((await strip(page)).empty, 'strip: nobody set a day, you have not either → no strip'); }
  /* a missing function / a failing one: nothing, quietly */
  { const miss = url => url.pathname === '/rest/v1/rpc/friend_registration_round2' ? { status: 404, body: JSON.stringify({ code: 'PGRST202', message: 'Could not find the function public.friend_registration_round2(p_term) in the schema cache' }) } : null;
    const { page, log } = await mk({ tables: tables({ r1: R1, r2: R2 }), rpc: rpcs(F1, F2), hook: miss, time: '2026-11-05T08:00:00-08:00' }); await tick(page, 1800);
    ok((await strip(page)).empty && log.errors.length === 0, 'strip: the Round 2 function is not installed yet → no strip, no error', log.errors);
    const n = log.rpcs.filter(r => r.fn === 'friend_registration_round2').length;
    await page.clock.runFor(130000); await page.waitForTimeout(300); await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await tick(page, 600);
    ok(log.rpcs.filter(r => r.fn === 'friend_registration_round2').length === n, 'strip: and it does not keep asking', n); }
  /* a blocked friend and a non-friend are never drawn */
  { const rpc = Object.assign(rpcs([...F1, { user_id: '33333333-3333-4333-8333-333333333399', day: '2026-10-20', at_time: '07:00:00' }], F2), { my_blocks: [{ id: ROWAN, display_name: 'Rowan Testa', username: 'rtesta', avatar_url: null, created_at: '2026-09-01T00:00:00Z' }] });
    const { page } = await mk({ tables: tables({ r1: R1 }), rpc }); await tick(page, 2000);
    const s = await strip(page);
    ok(!/Rowan|3333/.test(s.text) && s.rows.length === 3 && s.miss === '2 friends haven’t set theirs', 'strip: a blocked friend and a non-friend are never drawn, nor counted as unset', s); }
  /* tapping a face opens their page */
  { const { page } = await mk({ tables: tables({ r1: R1 }), rpc: rpcs(F1, F2) }); await tick(page, 1800); await friendsTab(page);
    await page.click('#frRegStrip .rs-fb[data-id="' + SKY + '"]'); await tick(page, 600);
    ok(await page.evaluate(() => document.getElementById('frpBack').classList.contains('open') && /Sky/.test(document.getElementById('frpBack').innerText)), 'strip: a face opens that friend’s page'); }
});

test('phone', async () => {
  /* the card at 390 */
  { const { page } = await mk({ tables: tables({ r1: R1 }), width: 390, height: 844 }); await tick(page, 1800);
    const r = await page.evaluate(() => { const c = document.getElementById('hmRegCardN'), b = c.getBoundingClientRect(); return { shown: c.offsetParent !== null, l: Math.round(b.left), r: Math.round(b.right), w: innerWidth, sw: document.documentElement.scrollWidth, over: c.scrollWidth > c.clientWidth + 1,
      go: Math.round(c.querySelector('.tl-go').getBoundingClientRect().height), pen: Math.round(c.querySelector('.tl-pen').getBoundingClientRect().height), copies: [...document.querySelectorAll('.hm-regcard')].filter(e => e.offsetParent !== null).length }; });
    ok(r.shown && r.copies === 1 && r.l >= 0 && r.r <= r.w && r.sw <= r.w && !r.over, 'phone: the card fits 390px, one copy, no sideways scroll', r);
    ok(r.go >= 40, 'phone: the game plan button is a full-size target', r);
    /* the editor at 390 */
    await page.click('#hmRegCardN [data-tl-key="add2"]'); await tick(page, 300);
    const e = await page.evaluate(() => { const c = document.getElementById('hmRegCardN'), f = [...c.querySelectorAll('.tl-in')].map(i => { const b = i.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.right), Math.round(b.height)]; }); return { f, over: c.scrollWidth > c.clientWidth + 1, sw: document.documentElement.scrollWidth, w: innerWidth, cr: Math.round(c.getBoundingClientRect().right) }; });
    ok(e.f.length === 2 && e.f.every(x => x[1] <= e.cr && x[2] >= 36) && !e.over && e.sw <= e.w, 'phone: the date and time fields fit inside the card', e); }
  /* the strip at 390: a horizontal row of day chips with faces */
  { const { page } = await mk({ tables: tables({ r1: R1 }), rpc: rpcs(F1, F2), width: 390, height: 844 }); await tick(page, 1800); await friendsTab(page);
    const r = await page.evaluate(() => { const l = document.querySelector('#frRegStrip .rs-l'), rows = [...l.querySelectorAll('.rs-row')], t = rows.map(x => Math.round(x.getBoundingClientRect().top));
      return { dir: getComputedStyle(l).flexDirection, sameLine: new Set(t).size === 1, n: rows.length, names: rows.map(x => getComputedStyle(x.querySelector('.rs-n')).display), faces: rows.every(x => x.querySelectorAll('.rs-fb').length > 0), sw: document.documentElement.scrollWidth, w: innerWidth, me: rows.some(x => x.classList.contains('rs-me')), strip: Math.round(document.getElementById('frRegStrip').getBoundingClientRect().height) }; });
    ok(r.dir === 'row' && r.sameLine && r.n === 4 && r.names.every(d => d === 'none') && r.faces && r.me && r.sw <= r.w, 'phone: the strip is one row of day chips with faces, yours highlighted, no sideways page scroll', r); }
});

/* review fixes (2026-10-16) */
test('lit', async () => {
  /* the lit row is the empty one you can fill in, not "Classes begin in 101 days" */
  { const { page } = await mk({ tables: tables() }); await tick(page, 1500);
    const c = await card(page), r1 = rowBy(c, 'r1');
    ok(c.nextN === 1 && /tl-next/.test(r1.cls) && /tl-empty/.test(r1.cls) && r1.add && r1.s === 'Opens Oct 19' && !/tl-next/.test(rowBy(c, 'begin').cls), 'Oct 16, nothing set: the lit row is “Your Round 1 · + Add” (opens Oct 19), not “Classes begin”', c.rows.map(r => r.k + ':' + r.cls)); }
  { const { page } = await mk({ tables: tables(), time: '2026-10-20T10:30:00-07:00' }); await tick(page, 1500);
    const c = await card(page), r1 = rowBy(c, 'r1');
    ok(c.nextN === 1 && /tl-next/.test(r1.cls) && r1.add && r1.s === 'Open now · ends Nov 3' && !/in \d+ days/.test(r1.r), 'Oct 20, nothing set: Round 1 is lit, “Open now · ends Nov 3”, + Add', r1); }
  { const { page } = await mk({ tables: tables({ r1: R1 }), time: '2026-11-02T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(!/tl-next/.test(rowBy(c, 'r2').cls) && rowBy(c, 'r2').s === 'Opens Nov 4' && /tl-next/.test(rowBy(c, 'begin').cls), 'Nov 2, Round 2 not open yet: it is not lit (the next date is)', c.rows.map(r => r.k + ':' + r.cls)); }
  for (const t of ['2026-11-04T09:00:00-08:00', '2026-11-10T10:30:00-08:00']) {
    const { page } = await mk({ tables: tables(t.startsWith('2026-11-04') ? { r1: R1 } : undefined), time: t }); await tick(page, 1500);
    const c = await card(page), r2 = rowBy(c, 'r2');
    ok(c.nextN === 1 && /tl-next/.test(r2.cls) && /tl-empty/.test(r2.cls) && r2.add && r2.s === 'Open now · ends Nov 17' && !/tl-next/.test(rowBy(c, 'begin').cls), t.slice(5, 10) + ': an empty Round 2 is the lit row (“Open now · ends Nov 17”, + Add)', c.rows.map(r => r.k + ':' + r.cls)); }
  /* once it is filled in the lit row moves on */
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2026-11-10T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(c.nextN === 1 && /tl-next/.test(rowBy(c, 'begin').cls), 'Nov 10 with both set: the next date (Classes begin) is lit', c.rows.map(r => r.k + ':' + r.cls)); }
  /* after Round 1 closes the empty Round 1 row is not drawn and nothing else is lit by it */
  { const { page } = await mk({ tables: tables(), time: '2026-11-18T10:30:00-08:00' }); await tick(page, 1500);
    const c = await card(page);
    ok(c.rows.map(r => r.k).join() === 'begin,add,drop,withdraw' && /tl-next/.test(rowBy(c, 'begin').cls), 'Nov 18, nothing set: no empty rows, Classes begin is lit', c.rows.map(r => r.k)); }
});

test('hints', async () => {
  const { page } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
  const c = await card(page);
  ok(rowBy(c, 'drop').s === 'Until 11:59 PM' && rowBy(c, 'drop').r === 'Fri, Feb 5', 'drop row: Fri, Feb 5 · until 11:59 PM', rowBy(c, 'drop'));
  ok(rowBy(c, 'withdraw').s === 'For a serious and compelling reason · 5 PM' && rowBy(c, 'withdraw').r === 'Fri, Apr 23', 'withdraw row: Fri, Apr 23 · for a serious and compelling reason · 5 PM', rowBy(c, 'withdraw'));
  ok(c.rows.length <= 6, 'still six rows at most', c.rows.length);
});

test('share', async () => {
  /* Round 2 editor: the line, and the switch (one setting for both rounds) */
  { const { page, log } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
    await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300);
    const t = await page.evaluate(() => { const b = document.querySelector('#hmRegCard .tl-share [role="switch"]'); return { text: norm0(document.querySelector('#hmRegCard .tl-share').textContent), on: b && b.getAttribute('aria-checked'), name: b && b.getAttribute('aria-labelledby') }; function norm0(t) { return t.replace(/\s+/g, ' ').trim(); } });
    ok(t.on === 'true' && /Friends can see your day/.test(t.text) && /Friends can see this day, not the time/.test(t.text), 'editor: “Friends can see this day, not the time” and the “Friends can see your day” switch (on)', t);
    await page.click('#hmRegCard .tl-share [role="switch"]'); await tick(page, 300);
    const t2 = await page.evaluate(() => ({ on: document.querySelector('#hmRegCard .tl-share [role="switch"]').getAttribute('aria-checked'), text: document.querySelector('#hmRegCard .tl-share').textContent, open: !!document.querySelector('#hmRegCard .tl-edit'), foc: document.activeElement && document.activeElement.getAttribute('data-tl-key') }));
    ok(t2.on === 'false' && /Hidden from your friends/.test(t2.text) && t2.open && t2.foc === 'sh2', 'turning it off keeps the editor open and the focus on the switch', t2);
    await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-06'); await page.click('#hmRegCard .tl-save'); await tick(page, 900);
    ok(w2(log).length === 1 && w2(log)[0].body.shared === false && w2(log)[0].body.day === '2026-11-06', 'Save: Round 2 is written with shared = false', w2(log).map(x => x.body));
    const r1w = w1(log);
    ok(r1w.length === 1 && r1w[0].m === 'POST' && r1w[0].body.shared === false && r1w[0].body.day === '2026-10-21' && r1w[0].body.at_time === '11:00' && /on_conflict=user_id%2Cterm/.test(r1w[0].query), 'and the same switch follows into Round 1’s row (same day and time, shared = false), the way the phone writes it', r1w.map(x => x.body));
    /* open it again: still off */
    await page.click('#hmRegCard [data-tl-key="pen2"]'); await tick(page, 300);
    ok(await page.evaluate(() => document.querySelector('#hmRegCard .tl-share [role="switch"]').getAttribute('aria-checked')) === 'false', 'the editor opens with the switch as you left it (off)'); }
  /* someone with only Round 2 can opt out: no Round 1 row, so registration_days is never written */
  { const { page, log } = await mk({ tables: tables(), time: '2026-11-10T10:30:00-08:00' }); await tick(page, 1500);
    await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300);
    await page.click('#hmRegCard .tl-share [role="switch"]'); await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-12'); await page.click('#hmRegCard .tl-save'); await tick(page, 900);
    ok(w2(log).length === 1 && w2(log)[0].body.shared === false && w1(log).length === 0, 'only Round 2 set: opting out writes registration_round2 only, never registration_days', { r2: w2(log).map(x => x.body), r1: w1(log).length }); }
  /* turning it back on when Round 1 was hidden: Round 1 follows */
  { const { page, log } = await mk({ tables: tables({ r1: Object.assign({}, R1, { shared: false }) }) }); await tick(page, 1500);
    await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300);
    ok(await page.evaluate(() => document.querySelector('#hmRegCard .tl-share [role="switch"]').getAttribute('aria-checked')) === 'false', 'Round 1 hidden from friends: the Round 2 switch starts off too');
    await page.click('#hmRegCard .tl-share [role="switch"]'); await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-06'); await page.click('#hmRegCard .tl-save'); await tick(page, 900);
    ok(w2(log)[0] && w2(log)[0].body.shared === true && w1(log).length === 1 && w1(log)[0].body.shared === true, 'switching it on writes Round 2 shared and Round 1 shared', { r2: w2(log).map(x => x.body), r1: w1(log).map(x => x.body) }); }
  /* with the shared column missing (SQL not run) it is the same "kept on this device" path */
  { const gone = { status: 400, body: JSON.stringify({ code: 'PGRST204', message: "Could not find the 'shared' column of 'registration_round2' in the schema cache" }) };
    const { page, log } = await mk({ tables: tables({ r1: R1 }), hook: (url, m) => url.pathname === '/rest/v1/registration_round2' && m !== 'GET' ? gone : null }); await tick(page, 1500);
    await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300); await page.click('#hmRegCard .tl-save'); await tick(page, 900);
    const l = await page.evaluate(([u]) => JSON.parse(localStorage.getItem('professify_regday2_' + u + '_2274') || 'null'), [ME]);
    ok(l && l.pending === true && l.shared === true && rowBy(await card(page), 'r2').pen, 'column not there yet: it is kept on this device, shows on the card', l); }
});

test('validate', async () => {
  const { page, log } = await mk({ tables: tables({ r1: R1 }) }); await tick(page, 1500);
  await page.click('#hmRegCard [data-tl-key="add2"]'); await tick(page, 300);
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-17'); await page.click('#hmRegCard .tl-save'); await tick(page, 900);
  ok(w2(log).length === 1 && w2(log)[0].body.day === '2026-11-17', 'Nov 17 (the last weekday) is accepted', w2(log).map(x => x.body));
  await page.click('#hmRegCard [data-tl-key="pen2"]'); await tick(page, 300);
  await page.fill('#hmRegCard .tl-in[data-tl-f="day"]', '2026-11-09'); await page.click('#hmRegCard .tl-save'); await tick(page, 900);
  ok(w2(log).length === 2 && w2(log)[1].body.day === '2026-11-09', 'Nov 9 is accepted', w2(log).map(x => x.body));
  /* the default skips Veterans Day */
  const { page: p2 } = await mk({ tables: tables({ r1: R1 }), time: '2026-11-11T08:00:00-08:00' }); await tick(p2, 1500);
  await p2.click('#hmRegCard [data-tl-key="add2"]'); await tick(p2, 300);
  ok(await p2.evaluate(() => document.querySelector('#hmRegCard .tl-in[data-tl-f="day"]').value) === '2026-11-12', 'on Veterans Day the date starts on Nov 12, not today');
});

test('dismiss2', async () => {
  const UID = '11111111-1111-4111-8111-111111111111', seed = k => `try{ localStorage.setItem('professify_dismiss_${k}', '1'); }catch(e){}`;
  const shown = async o => { const { page } = await mk(Object.assign({ tables: tables({ r1: R1, r2: R2 }) }, o)); await tick(page, 1500); return page.evaluate(() => !!document.getElementById('hmRegCard')); };
  ok(!(await shown({ init: seed('regtl_' + UID + '_2274') })), 'dismissed with your own key: stays gone');
  ok(await shown({ init: seed('regtl_someone-else_2274') }), 'another student’s dismissal on this browser does not hide yours');
  ok(await shown({ init: seed('regtl_2274') }), 'the draft key (regtl_2274, no user) hides nothing');
  ok(!(await shown({ init: seed('regtl_' + UID + '_2274'), time: '2027-01-17T10:30:00-08:00' })), 'Jan 17: still dismissed');
  ok(await shown({ init: seed('regtl_' + UID + '_2274'), time: '2027-01-18T10:30:00-08:00' }), 'Jan 18 (a week before classes): the card is back so drop / withdraw are not hidden all term');
  ok(!(await shown({ init: seed('regtl_' + UID + '_2274') + seed('regtl_' + UID + '_2274_late'), time: '2027-01-20T10:30:00-08:00' })), 'dismissing it again in the last week keeps it gone');
  { const { page } = await mk({ tables: tables({ r1: R1, r2: R2 }), time: '2027-01-19T10:30:00-08:00' }); await tick(page, 1500);
    await page.click('#hmRegCard .hm-regx'); await tick(page, 400);
    ok(await page.evaluate(([u]) => !document.getElementById('hmRegCard') && localStorage.getItem('professify_dismiss_regtl_' + u + '_2274_late') === '1' && localStorage.getItem('professify_dismiss_regtl_' + u + '_2274') === null, [UID]), 'the x on Jan 19 stores the “late” key and leaves the early one alone'); }
});

test('pacific', async () => {
  /* 7 PM Pacific on Oct 16 is already Oct 17 in UTC. Without mcPacificDay the fallback must still be the Pacific day. */
  const { page } = await mk({ tables: tables({ r1: R1 }), time: '2026-10-16T19:00:00-07:00' }); await tick(page, 1500);
  const before = (rowBy(await card(page), 'r1') || {}).r;
  await page.evaluate(() => { window.mcPacificDay = undefined; hmRegCardPaint(); }); await tick(page, 300);
  const after = (rowBy(await card(page), 'r1') || {}).r;
  ok(/^in 5 days/.test(before) && /^in 5 days/.test(after), 'without mcPacificDay the date is still the Pacific day (“in 5 days” at 7 PM Pacific, not 4)', { before, after });
});

test('hawk', async () => {
  const { page } = await mk({ tables: tables({ r1: R1 }), width: 390, height: 844 }); await tick(page, 2000);
  const vis = () => page.evaluate(() => { const f = document.querySelector('.hawk-fab'); return f ? getComputedStyle(f).visibility : 'none'; });
  const v0 = await vis();
  if (v0 === 'none') { ok(true, 'hawk: no Ask Me! bird in this harness page (nothing to hide)'); return; }
  ok(v0 === 'visible', 'the Ask Me! bird shows normally', v0);
  await page.click('#hmRegCardN .tl-all'); await tick(page, 400);
  ok(await vis() === 'hidden', 'with the All dates sheet open the bird is hidden (phone)');
  await page.keyboard.press('Escape'); await tick(page, 300);
  ok(await vis() === 'visible', 'closing the sheet brings it back');
  await page.click('#hmRegCardN [data-tl-key="pen1"]'); await tick(page, 400);
  ok(await vis() === 'hidden', 'any other sheet (the Round 1 day picker) hides it too');
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 500)); }
  while (open.length) { try { await open.pop().close(); } catch (e) {} }
}
console.log(`\ncheck-desktop-reg-timeline: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
