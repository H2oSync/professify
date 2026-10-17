/* check-desktop-regday — "Your registration day" on the website (website-registration-day, Tate 2026-10-14: catch the
   website up to the phone's 2026-10-11 feature). Runs the REAL index.html in Chromium, signed in, against the same
   PostgREST stand-in as check-app, with Spring 2027's shipped config (terms:'live': TERM 2274, Round 1 Oct 19 – Nov 3).
   Run: APP_DIR=<repo> node check-desktop-regday.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: a card on Schedule › Plans and Home's rail says your day (or invites you to set it), only for a signed-in
   student, only until Round 1's last day, and Home's only from 14 days before; the modal writes {user_id, term '2274',
   day, at_time, shared} upserted on user_id,term and Clear deletes it; a refused write keeps what you chose on this
   device and goes up again later; friends' days come from friend_registration_days('2274'), soonest first, friends only;
   a time is read the way the Portal shows it, and anything else says so. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
const NOW = '2026-10-14T10:30:00-07:00';           /* 5 days before Round 1 opens */
/* one-card (2026-10-15): the compact "Round 1 registration opens" card hides the rail's own day card while it shows; most of these tests are about
   that day card, so the page starts with the compact card dismissed, and UNDISMISS brings it back for the tests about the compact card */
const DISMISS = () => { try { localStorage.setItem('professify_dismiss_reg_2026-10-19', '1'); } catch (e) {} };
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, terms: 'live', time: NOW, init: DISMISS }, o));
const R1BTN = '#hmRegCard [data-tl-key="pen1"], #hmRegCard [data-tl-key="add1"]';   /* reg-timeline (2026-10-16): Home's one card is the timeline; Round 1's pencil / + Add opens the same sheet */
const UNDISMISS = async page => {};   /* reg-timeline (2026-10-16): the timeline card is not hidden by the old key */
const T = {};
const test = (name, fn) => { T[name] = fn; };
const ME = FX.ME.id, F = FX.FRIENDS.map(f => f.id);
const withDay = (row) => { const t = JSON.parse(JSON.stringify(FX.TABLES)); t.registration_days = row ? [Object.assign({ user_id: ME, term: '2274', shared: true, updated_at: '2026-10-13T00:00:00Z' }, row)] : []; return t; };
const rpcWith = rows => Object.assign({}, FX.RPC, { friend_registration_days: rows });
const regWrites = log => log.writes.filter(w => w.table === 'registration_days');
const LS = (page, k) => page.evaluate(([u, t]) => localStorage.getItem('professify_regday_' + u + '_' + t), [ME, k || '2274']);
/* what the page shows: each slot's card, its state and text */
const SLOTS = `(() => [...document.querySelectorAll('.rg-slot')].map(s => { const c = s.querySelector('.rg-card'); return { where: s.dataset.rg, has: !!c, state: c ? c.dataset.rgState : '', head: c ? (c.querySelector('.rg-h') || {}).textContent : '', sub: c ? (c.querySelector('.rg-s') || {}).textContent || '' : '', friends: c ? [...c.querySelectorAll('.rg-f')].map(b => b.querySelector('.rg-fn').textContent + ' | ' + b.querySelector('.rg-fd').textContent) : [], miss: c ? (c.querySelector('.rg-miss') || {}).textContent || '' : '', note: c ? (c.querySelector('.rg-note') || {}).textContent || '' : '', btn: c ? (c.querySelector('.rg-btn') || {}).textContent : '' }; }))()`;
const slots = async page => { const r = await page.evaluate(SLOTS); const o = { plans: { has: false, friends: [] }, rail: { has: false, friends: [] } }; r.forEach(x => { o[x.where] = x; }); return o; };
const toast = page => page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '');

test('cards', async () => {
  /* none */
  { const { page, close, log } = await desk({ tables: withDay(null) }); await tick(page, 1500);
    const s = await slots(page);
    ok(s.plans && s.plans.has && s.plans.state === 'none' && s.plans.head === 'Set your registration day' && /^Opens Oct 19 · in 5 days$/.test(s.plans.sub) && s.plans.btn === 'Set day', 'none: Plans says “Set your registration day” with when it opens', s.plans);
    ok(await page.evaluate(() => { const c = document.getElementById('hmRegCard'); return !!c && /Spring 2027/.test(c.innerText) && !!c.querySelector('[data-tl-key="add1"]') && /Opens Oct 19/.test(c.innerText); }), 'none: Home’s card is the Spring 2027 timeline, with “+ Add” on Your Round 1 (Round 1 opens Oct 19)');
    const reads = log.reads.map(r => decodeURIComponent(r));
    ok(reads.some(r => /^registration_days\?select=day,at_time,shared,updated_at&user_id=eq\.[^&]+&term=eq\.2274$/.test(r)), 'reads: your row is read by user and term 2274', reads.filter(r => /registration/.test(r)));
    ok(log.errors.length === 0, 'none: no page errors', log.errors);
    await close(); }
  /* set */
  { const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }) }); await tick(page, 1500);
    const s = await slots(page);
    ok(s.plans.state === 'set' && s.plans.head === 'Register Wed, Oct 21, 11a' && s.plans.sub === 'in 7 days' && s.plans.btn === 'Change', 'set: “Register Wed, Oct 21, 11a · in 7 days” on Plans', s.plans);
    ok(await page.evaluate(() => { const r = document.querySelector('#hmRegCard [data-tl-row="r1"]'); return !!r && /Wed, Oct 21 · 11:00 AM/.test(r.innerText) && /in 7 days/.test(r.innerText); }), 'set: …and Home’s timeline says Wed, Oct 21 · 11:00 AM, in 7 days');
    ok(await page.evaluate(() => document.querySelector('.rg-card').title) === 'Wednesday, October 21, 2026', 'set: the full date, with its year, is on the card');
    /* reg-timeline (2026-10-16): the old green “Your day…” line and the grey “Change your registration day” button are gone; the top strip has nothing */
    ok(await page.evaluate(() => !/Change your registration day|Your day:/.test(document.getElementById('hmRegCard').innerText) && !document.querySelector('#hmRegCard .hm-reg-day') && !/registration/i.test(document.getElementById('campusBanner').innerText)), 'timeline: no “Your day…” line, no “Change your registration day” button, nothing at the top');
    ok(log.errors.length === 0, 'set: no page errors', log.errors);
    await close(); }
  /* no time, tomorrow, today before / after, the day after */
  for (const [t, day, at, want, why] of [
    [NOW, '2026-10-21', null, 'Register Wed, Oct 21', 'a day with no time'],
    ['2026-10-20T10:30:00-07:00', '2026-10-21', '08:30:00', 'Register tomorrow, 8:30a', 'tomorrow'],
    ['2026-10-21T09:30:00-07:00', '2026-10-21', '11:00:00', 'Register today at 11a|in 1h 30m', 'today, before'],
    ['2026-10-21T11:45:00-07:00', '2026-10-21', '11:00:00', 'Your registration opened at 11a|', 'today, after'],
    ['2026-10-22T09:00:00-07:00', '2026-10-21', '11:00:00', 'NONE', 'the day after your day (like the phone, it is gone)'],
  ]) {
    const { page, close } = await desk({ tables: withDay({ day, at_time: at }), time: t }); await tick(page, 1500);
    const s = (await slots(page)).plans;
    const got = s.has ? s.head + (want.includes('|') ? '|' + s.sub : '') : 'NONE';
    ok(got === want, 'wording: ' + why, { got, want });
    await close();
  }
});

/* Round 1's dates: when the card is there at all */
test('window', async () => {
  /* Round 1 running, nothing set */
  { const { page, close } = await desk({ tables: withDay(null), time: '2026-10-27T10:00:00-07:00' }); await tick(page, 1500);
    const s = await slots(page);
    ok(s.plans.has && s.plans.sub === 'Round 1 is open · ends Nov 3' && await page.evaluate(() => !!document.getElementById('hmRegCard')), 'running: Round 1 is open, ends Nov 3 — Plans card and Home’s timeline still there', s);
    await close(); }
  /* the rail waits until 14 days before; Plans does not */
  { const a = await desk({ tables: withDay(null), time: '2026-10-01T10:00:00-07:00' }); await tick(a.page, 1500);
    const s = await slots(a.page);
    ok(s.plans.has && await a.page.evaluate(() => !document.getElementById('hmRegCard')), '18 days out: Plans has the card, Home’s timeline does not', s);
    await a.close();
    const b = await desk({ tables: withDay(null), time: '2026-10-05T10:00:00-07:00' }); await tick(b.page, 1500);
    const s2 = await slots(b.page);
    ok(s2.plans.has && await b.page.evaluate(() => !!document.getElementById('hmRegCard')), '14 days out: Home’s timeline has it too', s2);
    await b.close(); }
  /* after Round 1: nothing, and nothing asked */
  { const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21' }), time: '2026-11-04T09:00:00-08:00' }); await tick(page, 1500);
    const s = await slots(page);
    ok(!s.plans.has && await page.evaluate(() => { const c = document.getElementById('hmRegCard'); return !!c && /Your Round 1/.test(c.innerText) && !c.querySelector('[data-tl-key="pen1"]'); }), 'after Round 1 (Nov 4): the Schedule card is gone; Home’s timeline stays, Round 1 done with no pencil', s);
    ok(!log.reads.some(r => r === 'rpc:friend_registration_days') && log.reads.some(r => /^registration_days\?/.test(r)), 'after Round 1: friends’ Round 1 days (the RPC) are never asked; your own rows are still read for the timeline', log.reads.filter(r => /registration/.test(r)));
    await close(); }
  /* the last day itself still shows */
  { const { page, close } = await desk({ tables: withDay(null), time: '2026-11-03T20:00:00-08:00' }); await tick(page, 1500);
    ok((await slots(page)).plans.has, 'on Nov 3 itself (Pacific, evening) the card is still there');
    await close(); }
  /* signed out */
  { const { page, close, log } = await desk({ signedIn: false, tables: withDay({ day: '2026-10-21' }) }); await tick(page, 1500);
    const s = await slots(page);
    ok(!s.plans.has, 'signed out: no card', s);
    ok(!log.reads.some(r => /registration/.test(r)) && log.writes.length === 0, 'signed out: nothing about registration is read or written', log.reads.filter(r => /registration/.test(r)));
    ok(await page.evaluate(() => !document.getElementById('hmRegCard') && !/registration day/i.test(document.getElementById('campusBanner').innerText)), 'signed out: no banner card');   /* websync (2026-10-15) */
    await close(); }
  /* not the registration term */
  { const { page, close, log } = await desk({ terms: 'single', tables: withDay({ day: '2026-10-21' }) }); await tick(page, 1500);
    const s = await slots(page);
    ok(!s.plans.has && !log.reads.some(r => /registration/.test(r)), 'a site choosing in another term (Fall 2026) shows no card and asks nothing', s);
    await close(); }
});

test('save', async () => {
  const { page, close, log } = await desk({ tables: withDay(null) }); await tick(page, 1500);
  await page.evaluate(() => { show('sched'); setSchedTab('watch'); TCPlans.render(); }); await tick(page, 400);
  await page.click('.rg-slot[data-rg="plans"] [data-rg-act="open"]'); await tick(page, 400);
  const m = await page.evaluate(() => ({ open: document.getElementById('rgBack').classList.contains('open'), role: document.getElementById('rgBack').getAttribute('role'), inner: document.getElementById('rgModal').getAttribute('role'), by: document.getElementById('rgBack').getAttribute('aria-labelledby'), title: document.getElementById('rgTitle').textContent,
    days: [...document.querySelectorAll('.rg-d')].map(b => b.getAttribute('data-day')), off: [...document.querySelectorAll('.rg-d:disabled')].length, clear: !!document.querySelector('[data-rg-act="clear"]'),
    sec: document.querySelector('.rg-sec').textContent, share: document.querySelector('[data-rg-act="share"]').getAttribute('aria-checked'), time: document.getElementById('rgTime').value, focus: document.activeElement && document.activeElement.className }));
  ok(m.open && m.role === 'dialog' && m.inner === null && m.by === 'rgTitle' && m.title === 'When do you register?', 'modal: “When do you register?”, one dialog (#rgBack, labelled by its title), not a dialog in a dialog', m);
  ok(m.days.length === 12 && m.days[0] === '2026-10-19' && m.days[11] === '2026-11-03' && !m.days.some(d => ['2026-10-24', '2026-10-25', '2026-10-31', '2026-11-01'].includes(d)), 'modal: Round 1’s twelve weekdays, Oct 19 – Nov 3, no weekends', m.days);
  ok(/Oct 19 – Nov 3, 2026/.test(m.sec), 'modal: the span carries its year', m.sec);
  ok(m.share === 'true' && m.time === '' && !m.clear && m.off === 0, 'modal: friends can see it by default, no time, no Clear yet, no day is in the past', m);
  /* Save with no day, a bad time: nothing is written */
  await page.click('[data-rg-act="save"]'); await tick(page, 300);
  ok(/Pick your day first/.test(await page.evaluate(() => (document.getElementById('rgErr') || {}).textContent || '')) && regWrites(log).length === 0, 'Save with no day says so and writes nothing');
  await page.click('.rg-d[data-day="2026-10-22"]'); await page.fill('#rgTime', '25:61'); await page.click('[data-rg-act="save"]'); await tick(page, 300);
  const bad = await page.evaluate(() => (document.getElementById('rgErr') || {}).textContent || '');
  ok(/That time doesn’t look right/.test(bad) && regWrites(log).length === 0 && await page.evaluate(() => document.getElementById('rgBack').classList.contains('open')), 'a time it can’t read says so, keeps the sheet open and writes nothing', bad);
  ok(await page.evaluate(() => document.querySelector('.rg-d[data-day="2026-10-22"]').getAttribute('aria-pressed')) === 'true' && await page.evaluate(() => document.getElementById('rgTime').value) === '25:61', 'the day picked and the time typed survive the error');
  /* a good save */
  await page.fill('#rgTime', '2:30 pm');
  await page.click('[data-rg-act="share"]'); await tick(page, 200);
  ok(await page.evaluate(() => [document.querySelector('[data-rg-act="share"]').getAttribute('aria-checked'), document.getElementById('rgTime').value].join('|')) === 'false|2:30 pm', 'toggling “Friends can see” keeps the time typed');
  await page.click('[data-rg-act="save"]'); await tick(page, 800);
  const w = regWrites(log);
  ok(w.length === 1 && w[0].m === 'POST' && /on_conflict=user_id%2Cterm/.test(w[0].query), 'save: one upsert, on user_id,term', w.map(x => x.m + ' ' + x.query));
  const b = w[0] && w[0].body;
  ok(b && b.user_id === ME && b.term === '2274' && b.day === '2026-10-22' && b.at_time === '14:30' && b.shared === false && typeof b.updated_at === 'string', 'save: {user_id, term:2274, day, at_time:14:30, shared:false}', b);
  const s = await slots(page);
  ok(s.plans.head === 'Register Thu, Oct 22, 2:30p' && s.plans.sub === 'in 8 days' && await page.evaluate(() => /Thu, Oct 22 · 2:30 PM/.test(document.getElementById('hmRegCard').innerText)), 'save: the cards say Thu, Oct 22, 2:30p', s);
  ok(await toast(page) === 'Your registration day is saved' && !(await page.evaluate(() => document.getElementById('rgBack').classList.contains('open'))), 'save: the sheet closes and a toast says it is saved');
  const kept = JSON.parse(await LS(page) || 'null');
  ok(kept && kept.day === '2026-10-22' && kept.time === '14:30' && kept.shared === false && !kept.pending, 'save: kept on this device, nothing waiting', kept);
  /* change it: no time, shared on; the sheet opens with what is there */
  await page.click('.rg-slot[data-rg="plans"] [data-rg-act="open"]'); await tick(page, 400);
  const re = await page.evaluate(() => ({ on: document.querySelector('.rg-d.on').getAttribute('data-day'), time: document.getElementById('rgTime').value, share: document.querySelector('[data-rg-act="share"]').getAttribute('aria-checked'), clear: !!document.querySelector('[data-rg-act="clear"]') }));
  ok(re.on === '2026-10-22' && re.time === '2:30p' && re.share === 'false' && re.clear, 'change: the sheet opens on what you saved (2:30p, friends off, Clear offered)', re);
  await page.fill('#rgTime', ''); await page.click('.rg-d[data-day="2026-10-26"]'); await page.click('[data-rg-act="share"]'); await page.click('[data-rg-act="save"]'); await tick(page, 800);
  const b2 = regWrites(log)[1] && regWrites(log)[1].body;
  ok(b2 && b2.day === '2026-10-26' && b2.at_time === null && b2.shared === true && b2.term === '2274', 'save with no time sends at_time null', b2);
  ok((await slots(page)).plans.head === 'Register Mon, Oct 26', 'no time: “Register Mon, Oct 26”');
  /* Clear */
  await page.click('.rg-slot[data-rg="plans"] [data-rg-act="open"]'); await tick(page, 400);
  await page.click('[data-rg-act="clear"]'); await tick(page, 800);
  const del = regWrites(log).filter(x => x.m === 'DELETE');
  ok(del.length === 1 && /user_id=eq\.[^&]+/.test(decodeURIComponent(del[0].query)) && /term=eq\.2274/.test(del[0].query) && decodeURIComponent(del[0].query).includes('user_id=eq.' + ME), 'Clear: a delete for your user and term 2274', del.map(x => x.query));
  ok((await slots(page)).plans.state === 'none' && await LS(page) === null && await toast(page) === 'Your registration day is cleared', 'Clear: the card invites you again, nothing is kept, a toast says so');
  /* keyboard: Escape closes, focus goes back */
  await page.click('.rg-slot[data-rg="plans"] [data-rg-act="open"]'); await tick(page, 400);
  await page.keyboard.press('Escape'); await tick(page, 300);
  ok(!(await page.evaluate(() => document.getElementById('rgBack').classList.contains('open'))), 'Escape closes the sheet');
  /* Enter in the time field saves */
  await page.click('.rg-slot[data-rg="plans"] [data-rg-act="open"]'); await tick(page, 400);
  await page.click('.rg-d[data-day="2026-10-20"]'); await page.fill('#rgTime', '9a'); await page.press('#rgTime', 'Enter'); await tick(page, 800);
  ok((await slots(page)).plans.head === 'Register Tue, Oct 20, 9a', 'Enter in the time field saves');
  ok(log.errors.length === 0, 'save: no page errors', log.errors);
  await close();
  /* past days are off once Round 1 has started */
  { const o = await desk({ tables: withDay(null), time: '2026-10-21T10:00:00-07:00' }); await tick(o.page, 1500);
    await o.page.click(R1BTN); await tick(o.page, 400);
    const off = await o.page.evaluate(() => [...document.querySelectorAll('.rg-d:disabled')].map(b => b.getAttribute('data-day')));
    ok(JSON.stringify(off) === '["2026-10-19","2026-10-20"]', 'Oct 21: Oct 19 and 20 are off, today is not', off);
    await o.close(); }
});

test('banner', async () => {
  const { page, close } = await desk({ tables: withDay(null) }); await tick(page, 1500);
  await page.click('#hmRegCard [data-tl-key="add1"]'); await tick(page, 400);   /* reg-timeline: Round 1's “+ Add” on Home's card */
  ok(await page.evaluate(() => document.getElementById('rgBack').classList.contains('open') && document.getElementById('rgTitle').textContent === 'When do you register?'), 'banner card: “Set your registration day” opens the sheet');
  await close();
});

/* A write the server refuses: what you chose stays, it says so, and it goes up again later */
test('refused', async () => {
  const st = { refuse: true, calls: [] };
  const hook = (url, m, body) => {
    if (url.pathname !== '/rest/v1/registration_days' || m === 'GET') return null;
    st.calls.push({ m, body });
    return st.refuse ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down', details: null, hint: null }) } : null;
  };
  const { page, close, log } = await desk({ tables: withDay(null), hook }); await tick(page, 1500);
  await page.click(R1BTN); await tick(page, 400);
  await page.click('.rg-d[data-day="2026-10-21"]'); await page.fill('#rgTime', '11a'); await page.click('[data-rg-act="save"]'); await tick(page, 1000);
  let s = await slots(page);
  ok(s.plans.state === 'set' && s.plans.head === 'Register Wed, Oct 21, 11a', 'refused: the card still says what you chose', s.plans);
  ok(/not saved to your account yet/.test(s.plans.note), 'refused: and says it is only on this device (never “saved”)', s.plans.note);
  const t = await toast(page);
  ok(/Couldn’t save that to your account yet — it’s kept on this device/.test(t) && !/is saved/.test(t), 'refused: the toast says so', t);
  let kept = JSON.parse(await LS(page) || 'null');
  ok(kept && kept.day === '2026-10-21' && kept.time === '11:00' && kept.pending === true, 'refused: kept on this device, marked as waiting', kept);
  ok(st.calls.length === 1, 'refused: one attempt so far', st.calls.length);
  /* back online: the same change goes up */
  st.refuse = false;
  await page.evaluate(() => window.dispatchEvent(new Event('online'))); await tick(page, 1000);
  ok(st.calls.length === 2 && st.calls[1].m === 'POST' && st.calls[1].body.day === '2026-10-21' && st.calls[1].body.at_time === '11:00' && st.calls[1].body.term === '2274' && st.calls[1].body.user_id === ME, 'retry: coming back online sends it again, the same day and time', st.calls);
  s = await slots(page); kept = JSON.parse(await LS(page) || 'null');
  ok(s.plans.note === '' && kept && !kept.pending, 'retry: the note goes and nothing is waiting', { note: s.plans.note, kept });
  ok(log.errors.length === 0, 'refused: no page errors', log.errors);
  await close();
  /* the slow timer does it too, and the tab coming back */
  { const st2 = { refuse: true, calls: [] };
    const h2 = (url, m, body) => { if (url.pathname !== '/rest/v1/registration_days' || m === 'GET') return null; st2.calls.push({ m, body }); return st2.refuse ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null; };
    const o = await desk({ tables: withDay(null), hook: h2 }); await tick(o.page, 1500);
    await o.page.click(R1BTN); await tick(o.page, 400);
    await o.page.click('.rg-d[data-day="2026-10-23"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
    st2.refuse = false; await o.page.clock.runFor(61000); await o.page.waitForTimeout(400);
    ok(st2.calls.length === 2 && st2.calls[1].body.day === '2026-10-23', 'retry: a minute later it tries again by itself', st2.calls.length);
    await o.close(); }
  /* reload while it waits: this device's value shows, and goes up */
  { const st3 = { refuse: true, calls: [] };
    const tables = withDay({ day: '2026-10-19', at_time: '08:00:00' });     /* the account still holds an older day */
    const h3 = (url, m, body) => { if (url.pathname !== '/rest/v1/registration_days' || m === 'GET') return null; st3.calls.push({ m, body }); return st3.refuse ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null; };
    const init = `try{ if(!localStorage.getItem('__seeded')){ localStorage.setItem('__seeded','1'); localStorage.setItem('professify_regday_${ME}_2274', JSON.stringify({ day:'2026-10-22', time:'10:00', shared:true, at: ${Date.parse(NOW) + 1000}, pending:true })); } }catch(e){}`;
    const o = await desk({ tables, hook: h3, init }); st3.refuse = false; await tick(o.page, 1500);
    const s3 = (await slots(o.page)).plans;
    ok(s3.head === 'Register Thu, Oct 22, 10a', 'waiting: after a reload the account’s older day does not win over the change waiting here', s3);
    await o.page.evaluate(() => TCReg.retry()); await tick(o.page, 800);
    ok(st3.calls.some(c => c.m === 'POST' && c.body.day === '2026-10-22' && c.body.at_time === '10:00'), 'waiting: and it goes up', st3.calls);
    await o.close(); }
  /* Clear refused: it says friends can still see it */
  { const st4 = { refuse: true, calls: [] };
    const h4 = (url, m, body) => { if (url.pathname !== '/rest/v1/registration_days' || m === 'GET') return null; st4.calls.push({ m }); return st4.refuse ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null; };
    const o = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), hook: h4 }); await tick(o.page, 1500);
    await o.page.click(R1BTN); await tick(o.page, 400);
    await o.page.click('[data-rg-act="clear"]'); await tick(o.page, 800);
    const tt = await toast(o.page);
    ok(/Not done yet — friends can still see your day until it goes through/.test(tt) && st4.calls.some(c => c.m === 'DELETE'), 'clear refused: “Not done yet — friends can still see your day until it goes through”', tt);
    st4.refuse = false; await o.page.evaluate(() => window.dispatchEvent(new Event('online'))); await tick(o.page, 800);
    ok(st4.calls.filter(c => c.m === 'DELETE').length === 2, 'clear refused: the delete is sent again when it can be', st4.calls);
    await o.close(); }
});

/* The table or the function isn't there yet (RUN 17 not run): the day stays on this device, friends' days don't show */
test('schemaGap', async () => {
  const hook = (url, m) => {
    if (url.pathname === '/rest/v1/registration_days') return { status: 404, body: JSON.stringify({ code: '42P01', message: 'relation "public.registration_days" does not exist' }) };
    if (url.pathname === '/rest/v1/rpc/friend_registration_days') return { status: 404, body: JSON.stringify({ code: 'PGRST202', message: 'Could not find the function public.friend_registration_days(p_term) in the schema cache' }) };
    return null;
  };
  const { page, close, log } = await desk({ tables: withDay(null), hook }); await tick(page, 1500);
  let s = await slots(page);
  ok(s.plans.has && s.plans.state === 'none' && !s.plans.friends.length, 'no table: the card still invites you; no friends’ days', s.plans);
  await page.click(R1BTN); await tick(page, 400);
  await page.click('.rg-d[data-day="2026-10-21"]'); await page.click('[data-rg-act="save"]'); await tick(page, 1000);
  s = await slots(page);
  ok(s.plans.head === 'Register Wed, Oct 21' && /Kept on this device only/.test(s.plans.note), 'no table: it is kept on this device and says “Kept on this device only”', s.plans);
  ok(await toast(page) === 'Saved on this device', 'no table: the toast says “Saved on this device”', await toast(page));
  const n = regWrites(log).length;
  await page.evaluate(() => window.dispatchEvent(new Event('online'))); await page.clock.runFor(61000); await tick(page, 500);
  ok(regWrites(log).length === n && JSON.parse(await LS(page)).day === '2026-10-21', 'no table: it does not keep hammering, and the day stays', { n, now: regWrites(log).length });
  ok(log.errors.length === 0, 'no table: no page errors', log.errors);
  await close();
  /* the table reads fine but a write says it is not there: remembered, not retried */
  { let nw = 0;
    const h2 = (url, m) => (url.pathname === '/rest/v1/registration_days' && m !== 'GET' && ++nw) ? { status: 404, body: JSON.stringify({ code: '42P01', message: 'relation "public.registration_days" does not exist' }) } : null;
    const o = await desk({ tables: withDay(null), hook: h2 }); await tick(o.page, 1500);
    await o.page.click(R1BTN); await tick(o.page, 400);
    await o.page.click('.rg-d[data-day="2026-10-21"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
    const n2 = nw, s2 = (await slots(o.page)).plans;
    ok(n2 === 1 && /Kept on this device only/.test(s2.note) && await toast(o.page) === 'Saved on this device', 'write-only gap: one attempt, “Kept on this device only”, “Saved on this device”', { n2, note: s2.note });
    await o.page.evaluate(() => window.dispatchEvent(new Event('online'))); await o.page.clock.runFor(61000); await tick(o.page, 500);
    ok(nw === 1, 'write-only gap: and it is not tried again', nw);
    await o.close(); }
});

test('friends', async () => {
  const rows = [
    { user_id: F[0], day: '2026-10-21', at_time: '08:00:00' },       /* Avery: Wed 8a */
    { user_id: F[1], day: '2026-10-19', at_time: null },             /* Rowan: Mon, no time */
    { user_id: F[2], day: '2026-10-21', at_time: '14:30:00' },       /* Sky: Wed 2:30p */
    { user_id: '33333333-3333-4333-8333-333333333399', day: '2026-10-19', at_time: '07:00:00' },   /* not a friend: never shown */
    { user_id: F[2], day: '2026-10-30', at_time: '09:00:00' },       /* a duplicate id: the first stands */
  ];
  /* mine: Wed Oct 21 11a. Friends: Quinn and Harper have not set theirs */
  { const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), rpc: rpcWith(rows) }); await tick(page, 1500);
    const calls = log.rpcs.filter(r => r.fn === 'friend_registration_days');
    ok(calls.length >= 1 && calls.every(c => c.body && c.body.p_term === '2274'), 'friends: the RPC is asked for term 2274', calls);
    const s = await stripOf(page);
    const want = ['Mon Oct 19|Rowan Testa|2 days before you', 'Wed Oct 21 8a|Avery Quill|same day as you', 'Wed Oct 21 11a|You|your day', 'Wed Oct 21 2:30p|Sky Placeholder|same day as you'];
    ok(JSON.stringify(s.rows.map(r => r.label + '|' + r.names + '|' + r.rel)) === JSON.stringify(want), 'friends: soonest first (by day, then time), friends only, yours in its place, each with how far from yours', s.rows);
    ok(s.rows.filter(r => r.me).length === 1 && s.rows[2].me, 'friends: your own row is the highlighted one', s.rows);
    ok(s.miss === '2 friends haven’t set theirs' && s.round === 'Round 1 · Oct 19–Nov 3', 'friends: “2 friends haven’t set theirs”, Round 1 · Oct 19–Nov 3', s);
    await page.evaluate(() => show('friends')); await tick(page, 500);
    await page.click('#frRegStrip .rs-fb[data-id="' + F[1] + '"]'); await tick(page, 600);
    ok(await page.evaluate(() => document.getElementById('frpBack').classList.contains('open') && /Rowan/.test(document.getElementById('frpBack').innerText)), 'friends: tapping a face opens their page');
    ok(log.errors.length === 0, 'friends: no page errors', log.errors);
    await close(); }
  /* nothing set by me: no “before you”, and the strip still lists them */
  { const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(rows) }); await tick(page, 1500);
    const s = await stripOf(page);
    ok(s.rows.length === 3 && s.rows.every(r => r.rel === '' && !r.me) && /^Mon Oct 19/.test(s.rows[0].label), 'friends: with no day of yours there is no “before you”, no row of yours', s.rows);
    await close(); }
  /* a friend whose day has passed is not “to come”; the ones who haven't set theirs are still counted */
  { const r = [{ user_id: F[1], day: '2026-10-19', at_time: null }, { user_id: F[0], day: '2026-10-22', at_time: '09:00:00' }];
    const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith(r), time: '2026-10-21T10:00:00-07:00' }); await tick(page, 1500);
    const s = await stripOf(page);
    ok(s.rows.length === 1 && /Avery/.test(s.rows[0].names) && s.miss === '3 friends haven’t set theirs', 'friends: a day already gone is not listed (and that friend is not “unset”)', s);
    await close(); }
  /* nobody shared: with a day of yours the strip is your row and “5 friends haven’t set theirs”; with none, no strip at all */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-21' }), rpc: rpcWith([]) }); await tick(page, 1500);
    const s = await stripOf(page);
    ok(s.rows.length === 1 && s.rows[0].me && s.miss === '5 friends haven’t set theirs', 'friends: nobody shared → just your row and “5 friends haven’t set theirs”', s);
    await close(); }
  { const { page, close } = await desk({ tables: withDay(null), rpc: rpcWith([]) }); await tick(page, 1500);
    ok((await stripOf(page)).text === '', 'friends: nobody shared and no day of yours → no strip at all');
    await close(); }
  /* only non-friends shared: still nothing of theirs */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-21' }), rpc: rpcWith([rows[3]]) }); await tick(page, 1500);
    ok(await page.evaluate(() => !document.querySelector('#frRegStrip [data-id="33333333-3333-4333-8333-333333333399"]') && document.querySelectorAll('#frRegStrip .rs-row').length === 1), 'friends: a day from someone who is not your friend is never drawn');
    await close(); }
  /* the RPC fails: no strip, no error text, no crash, and your own card is left alone */
  { const hook = url => url.pathname === '/rest/v1/rpc/friend_registration_days' ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null;
    const { page, close, log } = await desk({ tables: withDay({ day: '2026-10-21' }), hook }); await tick(page, 1500);
    const s = await slots(page);
    ok(s.plans.has && s.plans.head === 'Register Wed, Oct 21' && (await stripOf(page)).text === '' && log.errors.length === 0, 'friends: a failing RPC leaves your card alone and shows no strip', { s: s.plans, e: log.errors });
    await close(); }
  /* the Schedule card no longer lists friends */
  { const { page, close } = await desk({ tables: withDay({ day: '2026-10-21' }), rpc: rpcWith(rows) }); await tick(page, 1500);
    ok(await page.evaluate(() => !document.querySelector('.rg-fr') && !document.querySelector('.rg-slot .rg-f')), 'friends: the Schedule card has no friends’ list any more');
    await close(); }
  /* five days fit; a sixth day is behind “+1 more day” */
  { const many = FX.FRIENDS.slice(0, 5).map((f, i) => ({ user_id: f.id, day: '2026-10-2' + i, at_time: null }));
    const a = await desk({ tables: withDay(null), rpc: rpcWith(many) }); await tick(a.page, 1500);
    ok(await a.page.evaluate(() => document.querySelectorAll('#frRegStrip .rs-row').length === 5 && !document.querySelector('#frRegStrip .rs-more')), 'friends: five days are all there, no “more”');
    await a.close();
    const b = await desk({ tables: withDay({ day: '2026-10-26' }), rpc: rpcWith(many) }); await tick(b.page, 1500);
    await b.page.evaluate(() => show('friends')); await tick(b.page, 500);
    const hid = () => b.page.evaluate(() => [...document.querySelectorAll('#frRegStrip .rs-row')].map(r => r.offsetParent !== null));
    ok(JSON.stringify(await hid()) === '[true,true,true,true,true,false]' && /\+1 more day/.test(await b.page.evaluate(() => document.querySelector('#frRegStrip .rs-more').textContent)), 'friends: a sixth day waits behind “+1 more day”', await hid());
    await b.page.click('#frRegStrip .rs-more'); await tick(b.page, 300);
    ok((await hid()).every(Boolean), 'friends: “+1 more day” shows it');
    await b.close(); }
});

test('parse', async () => {
  const { page, close } = await desk({ tables: withDay(null) }); await tick(page, 1200);
  const table = [
    ['11a', true, '11:00'], ['11:30 am', true, '11:30'], ['2pm', true, '14:00'], ['2:15 P.M.', true, '14:15'], ['12a', true, '00:00'], ['12p', true, '12:00'],
    ['14:30', true, '14:30'], ['08:30', true, '08:30'], ['830a', true, '08:30'], ['  9 AM ', true, '09:00'], ['', true, ''], ['   ', true, ''],
    ['8', false], ['9:30', false], ['13pm', false], ['0a', false], ['25:00', false], ['11:75a', false], ['noon', false], ['abc', false], ['11:3a', false], ['1p2', false],
  ];
  const got = await page.evaluate(t => t.map(r => TCReg.parseTime(r[0])), table);
  table.forEach((r, i) => ok(got[i].ok === r[1] && (!r[1] || got[i].time === r[2]), 'time: ' + JSON.stringify(r[0]) + ' → ' + (r[1] ? JSON.stringify(r[2]) : 'invalid'), got[i]));
  const txt = await page.evaluate(() => ['00:00', '08:30', '11:00', '12:00', '14:15', '23:59', 'x'].map(TCReg.timeText));
  ok(JSON.stringify(txt) === '["12a","8:30a","11a","12p","2:15p","11:59p",""]', 'time: how it reads back — 12a, 8:30a, 11a, 12p, 2:15p, 11:59p', txt);
  await close();
});

/* ---- review fixes (regday-fixes, 2026-10-14) ---- */
/* reg-timeline (2026-10-16): friends' days are the strip above Messages on the Friends tab (#frRegStrip), not a list in the Schedule card */
const stripOf = page => page.evaluate(() => {
  const e = document.getElementById('frRegStrip'), n = t => (t || '').replace(/\s+/g, ' ').trim();
  return { rows: [...(e ? e.querySelectorAll('.rs-row') : [])].map(r => ({ label: n([...r.querySelector('.rs-d').children].map(c => c.textContent).join(' ')), names: n(r.querySelector('.rs-n').textContent), rel: n(r.querySelector('.rs-rel').textContent), me: r.classList.contains('rs-me') })),
    miss: n((e && e.querySelector('.rs-ft span') || {}).textContent), text: n(e ? e.innerText : ''), round: n((e && e.querySelector('.rs-rnd') || {}).textContent) };
});
const frRowsOf = async page => (await stripOf(page)).rows.map(r => r.names);

test('blocked', async () => {
  const rows = [{ user_id: F[1], day: '2026-10-19', at_time: null }, { user_id: F[0], day: '2026-10-21', at_time: '08:00:00' }];
  const rpc = Object.assign({}, rpcWith(rows), { my_blocks: [{ id: F[1], display_name: 'Rowan Testa', username: 'rtesta', avatar_url: null, created_at: '2026-09-01T00:00:00Z' }] });
  const { page, close, log } = await desk({ tables: withDay(null), rpc }); await tick(page, 2000);
  const pre = await page.evaluate(id => ({ blocked: isBlocked(id), friend: !!friendsList.find(f => f.id === id) }), F[1]);
  ok(pre.blocked && pre.friend, 'blocked: precondition — Rowan is a friend and blocked', pre);
  const names = await frRowsOf(page);
  ok(JSON.stringify(names) === '["Avery Quill"]', 'blocked: a blocked friend in the RPC rows is not drawn', names);
  const s = await stripOf(page);
  ok(s.miss === '3 friends haven’t set theirs', 'blocked: …and is not counted among those who haven’t set theirs', s.miss);
  ok(log.errors.length === 0, 'blocked: no page errors', log.errors);
  await close();
});

test('friendsRefresh', async () => {
  /* a failed first load is asked again by itself */
  { let n = 0;
    const rpc = rpcWith([{ user_id: F[0], day: '2026-10-21', at_time: '08:00:00' }]);
    const hook = url => (url.pathname === '/rest/v1/rpc/friend_registration_days' && ++n === 1) ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null;
    const o = await desk({ tables: withDay(null), rpc, hook }); await tick(o.page, 1500);
    ok(n >= 1 && (await frRowsOf(o.page)).length === 0, 'friends refresh: the first load failed — nothing drawn yet', { n });
    await o.page.clock.runFor(16500); await o.page.waitForTimeout(500);
    ok(n >= 2 && JSON.stringify(await frRowsOf(o.page)) === '["Avery Quill"]', 'friends refresh: …and it asks again by itself, 15 seconds on', { n, rows: await frRowsOf(o.page) });
    await o.close(); }
  /* a loaded list ages out: the tab coming back asks again */
  { const rpc = rpcWith([{ user_id: F[1], day: '2026-10-19', at_time: null }]);
    const o = await desk({ tables: withDay(null), rpc }); await tick(o.page, 1500);
    ok(JSON.stringify(await frRowsOf(o.page)) === '["Rowan Testa"]', 'friends refresh: first list is Rowan');
    rpc.friend_registration_days = [{ user_id: F[0], day: '2026-10-21', at_time: '08:00:00' }, { user_id: F[1], day: '2026-10-19', at_time: null }];
    await o.page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await tick(o.page, 600);
    ok((await frRowsOf(o.page)).length === 1, 'friends refresh: within two minutes the list is left alone', await frRowsOf(o.page));
    await o.page.clock.runFor(125000); await o.page.waitForTimeout(300);
    await o.page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await tick(o.page, 800);
    ok(JSON.stringify(await frRowsOf(o.page)) === '["Rowan Testa","Avery Quill"]', 'friends refresh: after two minutes the tab coming back asks again and shows the new list', await frRowsOf(o.page));
    await o.close(); }
  /* opening the sheet asks too */
  { const rpc = rpcWith([]);
    const o = await desk({ tables: withDay(null), rpc }); await tick(o.page, 1500);
    /* websync (2026-10-15): the sign-in now also asks my_pinned_friends / my_favorite_teachers, which can land after this snapshot, so
       counting every RPC let the promise pass without the sheet asking. Count the one the promise is about. */
    const nReg = () => o.log.rpcs.filter(r => r.fn === 'friend_registration_days').length, before = nReg();
    await o.page.clock.runFor(125000); await o.page.waitForTimeout(300);
    await o.page.click(R1BTN); await tick(o.page, 800);
    ok(nReg() > before, 'friends refresh: opening the sheet asks the RPC again once the list is stale', { before, after: nReg() });
    await o.close(); }
});

test('retryNewer', async () => {
  const st = { refuse: true, posts: 0 };
  const hook = (url, m) => { if (url.pathname !== '/rest/v1/registration_days' || m === 'GET') return null; st.posts++; return st.refuse ? { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) } : null; };
  const o = await desk({ tables: withDay(null), hook }); await tick(o.page, 1500);
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-21"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
  ok(st.posts === 1 && JSON.parse(await LS(o.page)).pending === true, 'retry newer: this device’s change is waiting (refused once)', st.posts);
  /* another device saves a later day to the account meanwhile */
  o.tables.registration_days = [{ user_id: ME, term: '2274', day: '2026-10-26', at_time: '09:00:00', shared: true, updated_at: new Date(Date.parse(NOW) + 3600e3).toISOString() }];
  st.refuse = false;
  await o.page.evaluate(() => window.dispatchEvent(new Event('online'))); await tick(o.page, 1200);
  ok(st.posts === 1, 'retry newer: coming back online does not push the older change over the newer row', st.posts);
  const s = (await slots(o.page)).plans, kept = JSON.parse(await LS(o.page) || 'null');
  ok(s.head === 'Register Mon, Oct 26, 9a' && s.note === '' && kept && !kept.pending && kept.day === '2026-10-26', 'retry newer: the card shows the account’s later day and nothing is waiting', { s, kept });
  await o.close();
});

test('inFlight', async () => {
  const st = { n: 0, release: null };
  const hook = (url, m) => {
    if (url.pathname !== '/rest/v1/registration_days' || m === 'GET') return null;
    st.n++;
    if (st.n === 1) return new Promise(res => { st.release = () => res({ status: 201, body: '' }); });   /* the first write is slow */
    return { status: 500, body: JSON.stringify({ code: 'XX000', message: 'down' }) };                    /* the newer one is refused */
  };
  const o = await desk({ tables: withDay(null), hook }); await tick(o.page, 1500);
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-21"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 600);
  await o.page.evaluate(() => { window.__b = TCReg.save({ day: '2026-10-23', time: '', shared: true }); }); await tick(o.page, 800);
  ok(st.n === 2, 'in flight: a newer save went out while the first was still on its way', st.n);
  st.release(); await tick(o.page, 1200);
  const kept = JSON.parse(await LS(o.page) || 'null'), s = (await slots(o.page)).plans;
  ok(kept && kept.day === '2026-10-23' && kept.pending === true, 'in flight: the first write finishing does not mark its older day as saved over the newer pending one', kept);
  ok(s.head === 'Register Fri, Oct 23' && /not saved to your account yet/.test(s.note), 'in flight: the card still shows the newer day, still waiting', s);
  await o.close();
});

test('focus', async () => {
  const o = await desk({ tables: withDay(null) }); await tick(o.page, 1500);
  const focusOn = sel => o.page.evaluate(q => !!document.activeElement && document.activeElement.isConnected && document.activeElement.matches(q), sel);
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-21"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
  ok(await focusOn(R1BTN), 'focus: after Save it is on the slot’s new Change button, not on a button that was drawn away');
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('[data-rg-act="clear"]'); await tick(o.page, 1000);
  ok(await focusOn(R1BTN), 'focus: after Clear it is on the slot’s new Set day button');
  await o.page.click('#hmRegCard [data-tl-key="add1"]'); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-22"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
  ok(await focusOn('#hmRegCard [data-tl-key="pen1"]'), 'focus: opened from the timeline’s “+ Add”, it goes back to the row’s pencil');
  await o.close();
});

test('permission', async () => {
  const hook = (url, m) => (url.pathname === '/rest/v1/registration_days' && m !== 'GET') ? { status: 403, body: JSON.stringify({ code: '42501', message: 'new row violates row-level security policy for table "registration_days"' }) } : null;
  const o = await desk({ tables: withDay({ day: '2026-10-21', at_time: '11:00:00' }), hook }); await tick(o.page, 1500);
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('[data-rg-act="clear"]'); await tick(o.page, 1000);
  const t1 = await toast(o.page);
  ok(/Not done yet — friends can still see your day/.test(t1) && !/cleared|removed/.test(t1), 'permission: a refused Clear (42501) says it is not done, never “cleared”', t1);
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-22"]'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 1000);
  const t2 = await toast(o.page), s = (await slots(o.page)).plans;
  ok(/Couldn’t save/.test(t2) && !/is saved|Saved on this device/.test(t2) && /not saved to your account yet/.test(s.note) && !/Kept on this device only/.test(s.note), 'permission: a refused save (42501) says it failed and is only on this device for now — not a missing table', { t2, note: s.note });
  ok(o.log.errors.length === 0, 'permission: no page errors', o.log.errors);
  await o.close();
});

test('a11y', async () => {
  const o = await desk({ tables: withDay(null) }); await tick(o.page, 1500);
  await o.page.click(R1BTN); await tick(o.page, 400);
  await o.page.click('.rg-d[data-day="2026-10-22"]'); await o.page.fill('#rgTime', 'soon'); await o.page.click('[data-rg-act="save"]'); await tick(o.page, 400);
  const r = await o.page.evaluate(() => { const i = document.getElementById('rgTime'), d = i.getAttribute('aria-describedby'); return { inv: i.getAttribute('aria-invalid'), d, txt: d && document.getElementById(d) ? document.getElementById(d).textContent : null }; });
  ok(r.inv === 'true' && r.d === 'rgErr' && /doesn’t look right/.test(r.txt || ''), 'a11y: the time error is tied to the time field (aria-invalid + aria-describedby)', r);
  await o.close();
  const p = await desk({ tables: withDay({ day: '2026-10-21' }), tz: 'Pacific/Auckland' }); await tick(p.page, 1500);
  const b = await p.page.evaluate(() => document.getElementById('hmRegCard').innerText);
  ok(/in 7 days/.test(b), 'timeline: the day count is Pacific’s (7), even in a browser that is already on the 15th', b);
  await p.close();
});

const names = ONLY ? [ONLY] : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-regday: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
/* reg-timeline (2026-10-16): this file was updated by edit-tests-reg-timeline-2026-10-16.py */
