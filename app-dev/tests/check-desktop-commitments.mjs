/* check-desktop-commitments — "Work & activities" on the website (website-commitments, Tate 2026-10-14: catch the
   website up to the phone's 2026-10-11 feature). Runs the REAL index.html in Chromium, signed in, against the same
   PostgREST stand-in as check-app.
   Run: APP_DIR=<repo> node check-desktop-commitments.mjs [--only name] [--quiet]   (APP_PORT to move off 8190)
   The promises: a card on Schedule › My classes lists what you do every week ("Barista · Mon Wed Fri · 4:00–8:00p · friends see
   Busy"); the modal writes {id, user_id, kind, name, days, start_min, end_min, busy} (upsert on id) and Delete deletes it; a
   missing table keeps it on this device quietly while a refused write (42501) is reported as a failure and goes up again
   later; your week and Home draw it hatched by name, a friend's draws as "Busy" with no name anywhere; free time counts it
   ("Barista shift till 8p" / "Busy till 8p"); a section over it says "Overlaps Barista Mon/Wed 4–8p" and My classes gets a
   pill that is not the red clash; times are read like the Portal shows them. */
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
const NOW = '2026-10-14T10:30:00-07:00';           /* a Wednesday */
let portN = 0; const BASE = +(process.env.APP_PORT || 8190);
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, time: NOW, port: BASE + (portN++ % 2) }, o));
const T = {};
const test = (name, fn) => { T[name] = fn; };
const ME = FX.ME.id, AVERY = FX.FRIENDS[0].id, ROWAN = FX.FRIENDS[1].id;
const row = (o = {}) => Object.assign({ id: 'c0000000-0000-4000-8000-0000000000a1', user_id: ME, kind: 'work', name: 'Barista', days: 'MWF', start_min: 960, end_min: 1200, busy: true }, o);
const withRows = (rows) => { const t = JSON.parse(JSON.stringify(FX.TABLES)); t.commitments = rows; return t; };
const rpcWith = busy => Object.assign({}, FX.RPC, { friend_busy_blocks: busy });
const AVERY_BUSY = [{ user_id: AVERY, days: 'TR', start_min: 600, end_min: 720 }];
const writes = log => log.writes.filter(w => w.table === 'commitments');
const LS = (page, k) => page.evaluate(([u, k]) => localStorage.getItem((k || 'professify_commits_') + u), [ME, k]);
const toast = page => page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '');
const settle = async page => { for (let k = 0; k < 12; k++) { await tick(page, 500); if (await page.evaluate(() => !!(window.TCCommit && TCCommit.state.frAt))) break; } await tick(page, 300); };
const goClasses = async page => { await page.evaluate(() => { show('sched'); setSchedTab('mine'); renderMyClasses(); }); await tick(page, 400); };
const cardRows = page => page.evaluate(() => [...document.querySelectorAll('.cm-card .cm-row')].map(b => b.querySelector('.cm-tx').textContent.replace(/\s+/g, ' ').trim()));
const wire = (url, m, st) => (u, mm, body) => { if (u.pathname !== url || mm === 'GET') return null; st.calls.push({ m: mm, body }); return st.answer ? st.answer(mm, body) : null; };

test('rows', async () => {
  const { page, close, log } = await desk({ tables: withRows([row(), row({ id: 'c0000000-0000-4000-8000-0000000000a2', kind: 'practice', name: '', days: 'TR', start_min: 690, end_min: 840, busy: false })]) });
  await tick(page, 1200); await goClasses(page);
  const rows = await cardRows(page);
  ok(rows.length === 2 && rows[1] === 'Barista · Mon Wed Fri · 4:00–8:00p · friends see Busy', 'row: “Barista · Mon Wed Fri · 4:00–8:00p · friends see Busy” (in time order)', rows);
  ok(rows[0] === 'Sport · Tue Thu · 11:30a–2:00p · only you', 'a row with no name takes its kind (“Sport”), and a private one says “only you”', rows);
  ok(await page.evaluate(() => document.querySelector('.cm-card h3').textContent) === 'Work & activities', 'the card is called “Work & activities”');
  ok(await page.evaluate(() => !!document.querySelector('.cm-card .cm-add') && document.querySelectorAll('.cm-card .cm-x').length === 2), '+ Add and one delete per row');
  const reads = log.reads.map(r => decodeURIComponent(r));
  ok(reads.some(r => /^commitments\?select=id,kind,name,days,start_min,end_min,busy&user_id=eq\.[^&]+&order=start_min\.asc$/.test(r) && r.includes(ME)), 'reads: your own rows, by user', reads.filter(r => /commit/.test(r)));
  ok(reads.includes('rpc:friend_busy_blocks'), 'reads: friends’ busy blocks come from friend_busy_blocks()');
  ok(log.errors.length === 0, 'no page errors', log.errors);
  await close();
  /* nothing yet */
  { const o = await desk({ tables: withRows([]) }); await tick(o.page, 1200); await goClasses(o.page);
    ok(await o.page.evaluate(() => /Nothing added yet/.test(document.querySelector('.cm-card').innerText) && !!document.querySelector('.cm-add')), 'empty: “Nothing added yet” and + Add');
    await o.close(); }
  /* signed out */
  { const o = await desk({ signedIn: false, tables: withRows([row()]) }); await tick(o.page, 1200);
    ok(await o.page.evaluate(() => !document.querySelector('.cm-card') && !document.getElementById('cmBack')), 'signed out: no card');
    ok(!o.log.reads.some(r => /commit|busy/.test(r)), 'signed out: nothing about commitments is read', o.log.reads.filter(r => /commit|busy/.test(r)));
    await o.close(); }
});

test('modal', async () => {
  const { page, close, log } = await desk({ tables: withRows([]) });
  await tick(page, 1200); await goClasses(page);
  await page.click('.cm-card .cm-add'); await tick(page, 400);
  const m = await page.evaluate(() => ({ open: document.getElementById('cmBack').classList.contains('open'), role: document.getElementById('cmModal').getAttribute('role'), title: document.getElementById('cmTitle').textContent,
    kinds: [...document.querySelectorAll('.cm-k')].map(b => b.textContent), kindOn: document.querySelector('.cm-k.on').textContent, days: [...document.querySelectorAll('.cm-d')].map(b => b.textContent + ':' + b.getAttribute('aria-label')),
    busy: document.querySelector('.cm-tog').getAttribute('aria-checked'), del: !!document.querySelector('[data-cm-act="dropm"]'), focus: document.activeElement && document.activeElement.id }));
  ok(m.open && m.role === 'dialog' && m.title === 'Add work or an activity', 'modal: opens as a dialog, “Add work or an activity”', m);
  ok(m.kinds.join() === 'Work,Club,Sport,Other' && m.kindOn === 'Work', 'modal: Work / Club / Sport / Other, Work first', m.kinds);
  ok(m.days.join() === 'M:Monday,T:Tuesday,W:Wednesday,Th:Thursday,F:Friday,Sa:Saturday,Su:Sunday', 'modal: M T W Th F Sa Su, each named for a screen reader', m.days);
  ok(m.busy === 'true' && !m.del, 'modal: friends see Busy is on by default; no Delete on a new one', m);
  /* errors tied to inputs */
  await page.click('[data-cm-act="save"]'); await tick(page, 300);
  const e1 = await page.evaluate(() => ({ days: (document.getElementById('cmErrDays') || {}).textContent, from: (document.getElementById('cmErrFrom') || {}).textContent, to: (document.getElementById('cmErrTo') || {}).textContent,
    fromInv: document.getElementById('cmFrom').getAttribute('aria-invalid'), fromDesc: document.getElementById('cmFrom').getAttribute('aria-describedby'), focus: document.activeElement.id }));
  ok(e1.days === 'Pick at least one day.' && e1.from === 'Add a start time.' && e1.to === 'Add an end time.' && e1.fromInv === 'true' && e1.fromDesc === 'cmErrFrom', 'Save with nothing says what is missing, under each field, tied by aria', e1);
  ok(e1.focus === 'cmFrom' && writes(log).length === 0, 'the first bad field takes focus and nothing is written', { f: e1.focus, w: writes(log).length });
  await page.click('.cm-d[data-day="M"]'); await page.fill('#cmFrom', '4'); await page.fill('#cmTo', '8pm'); await page.click('[data-cm-act="save"]'); await tick(page, 300);
  ok(await page.evaluate(() => (document.getElementById('cmErrFrom') || {}).textContent) === 'Add am or pm, like 4pm.', 'a bare 4 is not guessed: “Add am or pm, like 4pm.”');
  await page.fill('#cmFrom', '9pm'); await page.click('[data-cm-act="save"]'); await tick(page, 300);
  ok(await page.evaluate(() => (document.getElementById('cmErrTo') || {}).textContent) === 'End has to be after the start.' && writes(log).length === 0, 'an end before the start says so, on the End field');
  ok(await page.evaluate(() => document.querySelector('.cm-d[data-day="M"]').getAttribute('aria-pressed') + '|' + document.getElementById('cmTo').value) === 'true|8pm', 'what was picked and typed survives the errors');
  /* a good save */
  await page.fill('#cmName', 'Barista shift'); await page.fill('#cmFrom', '4:30 pm');
  await page.click('.cm-d[data-day="W"]'); await page.click('.cm-d[data-day="F"]');
  await page.click('.cm-tog'); await tick(page, 150);
  await page.click('[data-cm-act="save"]'); for (let k = 0; k < 10 && writes(log).length < 1; k++) await tick(page, 500);
  const w = writes(log);
  ok(w.length === 1 && w[0].m === 'POST' && /on_conflict=id/.test(w[0].query), 'save: one upsert, on id', w.map(x => x.m + ' ' + x.query));
  const b = w[0] && w[0].body;
  ok(b && /^[0-9a-f-]{36}$/.test(b.id) && b.user_id === ME && b.kind === 'work' && b.name === 'Barista shift' && b.days === 'MWF' && b.start_min === 990 && b.end_min === 1200 && b.busy === false && Object.keys(b).length === 8,
    'save: {id, user_id, kind:work, name, days:MWF, start_min:990, end_min:1200, busy:false}', b);
  ok((await cardRows(page)).join() === 'Barista shift · Mon Wed Fri · 4:30–8:00p · only you' && !(await page.evaluate(() => document.getElementById('cmBack').classList.contains('open'))), 'save: the sheet closes and the card lists it');
  ok(await toast(page) === 'Barista shift added', 'save: a toast says it was added', await toast(page));
  const kept = JSON.parse(await LS(page) || '[]');
  ok(kept.length === 1 && kept[0].s === 990 && !(await LS(page, 'professify_commits_pending_')), 'save: kept on this device and nothing is left waiting', kept);
  ok(await page.evaluate(() => document.activeElement && document.activeElement.classList.contains('cm-row') && document.activeElement.isConnected), 'focus goes back to the live row, not the one that was redrawn');
  /* edit: the sheet opens on what is there */
  await page.click('.cm-card .cm-row'); await tick(page, 400);
  const re = await page.evaluate(() => ({ title: document.getElementById('cmTitle').textContent, name: document.getElementById('cmName').value, from: document.getElementById('cmFrom').value, to: document.getElementById('cmTo').value, days: [...document.querySelectorAll('.cm-d.on')].map(x => x.dataset.day).join(''), busy: document.querySelector('.cm-tog').getAttribute('aria-checked'), del: !!document.querySelector('[data-cm-act="dropm"]') }));
  ok(re.title === 'Edit Barista shift' && re.name === 'Barista shift' && re.from === '4:30pm' && re.to === '8pm' && re.days === 'MWF' && re.busy === 'false' && re.del, 'edit: opens on what you saved, with Delete', re);
  await page.fill('#cmTo', '9pm'); await page.press('#cmTo', 'Enter'); for (let k = 0; k < 10 && writes(log).length < 2; k++) await tick(page, 500);
  const w2 = writes(log);
  ok(w2.length === 2 && w2[1].body.id === b.id && w2[1].body.end_min === 1260, 'edit: Enter saves; the same id goes up again with the new end', w2.map(x => x.body && x.body.end_min));
  /* Escape closes, focus returns */
  await page.click('.cm-card .cm-add'); await tick(page, 400); await page.keyboard.press('Escape'); await tick(page, 300);
  ok(!(await page.evaluate(() => document.getElementById('cmBack').classList.contains('open'))) && await page.evaluate(() => document.activeElement.classList.contains('cm-add')), 'Escape closes the sheet and focus is back on + Add');
  /* kind: Sport is stored as practice; Club; Other with no name draws as Busy */
  await page.click('.cm-card .cm-add'); await tick(page, 400); await page.click('.cm-k[data-kind="practice"]'); await page.click('.cm-d[data-day="S"]'); await page.fill('#cmFrom', '9:00 am'); await page.fill('#cmTo', '12'); await page.click('[data-cm-act="save"]'); await tick(page, 300);
  ok(await page.evaluate(() => (document.getElementById('cmErrTo') || {}).textContent) === 'Add am or pm, like 4pm.', 'a bare 12 is not guessed either');
  await page.fill('#cmTo', '12 pm'); await page.click('[data-cm-act="save"]'); for (let k = 0; k < 10 && writes(log).length < 3; k++) await tick(page, 500);
  const w3 = writes(log);
  ok(w3.length === 3 && w3[2].body.kind === 'practice' && w3[2].body.name === null && w3[2].body.days === 'S' && w3[2].body.start_min === 540 && w3[2].body.end_min === 720 && w3[2].body.busy === true, 'Sport is stored as practice, no name is null, Sa is S', w3[2] && w3[2].body);
  ok(log.errors.length === 0, 'modal: no page errors', log.errors);
  await close();
});

test('drop', async () => {
  const { page, close, log } = await desk({ tables: withRows([row()]) });
  await tick(page, 1200); await goClasses(page);
  await page.click('.cm-card .cm-x'); await tick(page, 800);
  const del = writes(log).filter(x => x.m === 'DELETE');
  ok(del.length === 1 && decodeURIComponent(del[0].query).includes('id=eq.c0000000-0000-4000-8000-0000000000a1') && decodeURIComponent(del[0].query).includes('user_id=eq.' + ME), 'delete: a DELETE for that id and your user', del.map(x => x.query));
  ok((await cardRows(page)).length === 0 && JSON.parse(await LS(page) || '[]').length === 0 && await toast(page) === 'Barista removed', 'delete: gone from the card and this device, a toast says so');
  ok(await page.evaluate(() => document.querySelectorAll('.cal-cm').length === 0), 'delete: and from the week');
  ok(!(await LS(page, 'professify_commits_pending_')), 'delete: nothing left waiting');
  /* Delete inside the sheet */
  await page.evaluate(() => TCCommit.save({ id: 'c0000000-0000-4000-8000-0000000000b1', kind: 'club', name: 'Chess', days: 'T', s: 600, e: 660, busy: true })); await tick(page, 600);
  await page.click('.cm-card .cm-row'); await tick(page, 400); await page.click('[data-cm-act="dropm"]'); await tick(page, 800);
  ok(writes(log).filter(x => x.m === 'DELETE').length === 2 && (await cardRows(page)).length === 0, 'the sheet’s Delete deletes too');
  ok(log.errors.length === 0, 'delete: no page errors', log.errors);
  await close();
});

test('refused', async () => {
  /* a table that is not there yet: the read says so, and nothing is sent after that */
  { const st = { calls: [] };
    const gone = { status: 404, body: JSON.stringify({ code: 'PGRST205', message: 'Could not find the table public.commitments in the schema cache' }) };
    const { page, close, log } = await desk({ tables: withRows([]), hook: (u, m, body) => { if (u.pathname !== '/rest/v1/commitments') return null; if (m !== 'GET') st.calls.push({ m, body }); return gone; } });
    await tick(page, 1200); await goClasses(page);
    await page.evaluate(() => TCCommit.save({ id: 'c0000000-0000-4000-8000-0000000000c1', kind: 'work', name: 'Barista', days: 'M', s: 960, e: 1200, busy: true })); await tick(page, 600);
    ok((await cardRows(page)).length === 1 && JSON.parse(await LS(page) || '[]').length === 1, 'no table: it is kept on this device and the card lists it');
    ok(!/Couldn’t/.test(await toast(page)), 'no table: no complaint', await toast(page));
    ok(await page.evaluate(() => /Kept on this device only/.test(document.querySelector('.cm-card').innerText)), 'no table: the card says it is on this device only');
    ok(st.calls.length === 0, 'no table: nothing is sent once the read has said so', st.calls.length);
    ok(log.errors.length === 0, 'no table: no page errors', log.errors);
    await close(); }
  /* a table the read can see but a write says is missing: asked once, remembered, no complaint */
  { const st = { calls: [] };
    const { page, close, log } = await desk({ tables: withRows([]), hook: (u, m, body) => { if (u.pathname !== '/rest/v1/commitments' || m === 'GET') return null; st.calls.push({ m, body }); return { status: 404, body: JSON.stringify({ code: '42P01', message: 'relation "public.commitments" does not exist' }) }; } });
    await tick(page, 1200); await goClasses(page);
    await page.evaluate(() => TCCommit.save({ id: 'c0000000-0000-4000-8000-0000000000c1', kind: 'work', name: 'Barista', days: 'M', s: 960, e: 1200, busy: true })); await tick(page, 600);
    ok(st.calls.length === 1 && (await cardRows(page)).length === 1 && !/Couldn’t/.test(await toast(page)), 'a write that finds no table (42P01): kept here, no complaint, one attempt', { n: st.calls.length, t: await toast(page) });
    await page.evaluate(() => TCCommit.save({ id: 'c0000000-0000-4000-8000-0000000000c2', kind: 'work', name: 'Two', days: 'T', s: 600, e: 700, busy: true })); await tick(page, 600);
    ok(st.calls.length === 1, 'and it is not asked again once it has said so', st.calls.length);
    ok(log.errors.length === 0, 'no page errors', log.errors);
    await close(); }
  /* 42501 is a failure, not a gap */
  { const st = { calls: [], refuse: true };
    const hook = (u, m, body) => { if (u.pathname !== '/rest/v1/commitments' || m === 'GET') return null; st.calls.push({ m, body }); return st.refuse ? { status: 403, body: JSON.stringify({ code: '42501', message: 'new row violates row-level security policy for table "commitments"', details: null, hint: null }) } : null; };
    const { page, close, log } = await desk({ tables: withRows([]), hook });
    await tick(page, 1200); await goClasses(page);
    await page.click('.cm-card .cm-add'); await tick(page, 400); await page.fill('#cmName', 'Barista'); await page.click('.cm-d[data-day="M"]'); await page.fill('#cmFrom', '4pm'); await page.fill('#cmTo', '8pm'); await page.click('[data-cm-act="save"]'); await tick(page, 800);
    ok(/Couldn’t save that to your account yet — it’s kept on this device/.test(await toast(page)) && !/added|saved$/.test(await toast(page)), '42501: the toast says it could not be saved', await toast(page));
    ok((await cardRows(page)).length === 1 && await page.evaluate(() => /not saved to your account yet/.test(document.querySelector('.cm-card').innerText)), '42501: it stays on the card, marked as not saved');
    const pend = JSON.parse(await LS(page, 'professify_commits_pending_') || '{}');
    ok(Object.values(pend).join() === 'save' && JSON.parse(await LS(page) || '[]').length === 1, '42501: kept on this device and marked waiting', pend);
    ok(st.calls.length === 1, '42501: one attempt so far', st.calls.length);
    /* back online: it goes up again, the note goes away */
    st.refuse = false; await page.evaluate(() => window.dispatchEvent(new Event('online'))); for (let k = 0; k < 10 && await LS(page, 'professify_commits_pending_'); k++) await tick(page, 500);
    ok(st.calls.length === 2 && st.calls[1].body.name === 'Barista', 'back online: it goes up again', st.calls.length);
    ok(!(await LS(page, 'professify_commits_pending_')) && await page.evaluate(() => !document.querySelector('[data-cm-note]')), 'back online: nothing waiting, the note is gone');
    /* a refused delete says friends can still see it */
    st.refuse = true; await page.click('.cm-card .cm-x'); await tick(page, 800);
    ok(/friends can still see it as Busy/.test(await toast(page)), 'a refused delete says friends can still see it', await toast(page));
    ok((await cardRows(page)).length === 0 && JSON.parse(await LS(page, 'professify_commits_pending_') || '{}')[Object.keys(pend)[0]] === 'drop', 'and the delete is kept waiting');
    st.refuse = false; await page.evaluate(() => window.dispatchEvent(new Event('online'))); for (let k = 0; k < 10 && await LS(page, 'professify_commits_pending_'); k++) await tick(page, 500);
    ok(st.calls.filter(x => x.m === 'DELETE').length === 2 && !(await LS(page, 'professify_commits_pending_')), 'the delete goes up when it can', [st.calls.map(x => x.m), await LS(page, 'professify_commits_pending_')]);
    ok(log.errors.length === 0, '42501: no page errors', log.errors);
    await close(); }
  /* a change waiting here beats the server's older copy after a reload */
  { const tables = withRows([row({ end_min: 1100 })]);
    const hook = (u, m) => (u.pathname === '/rest/v1/commitments' && m !== 'GET') ? { status: 403, body: JSON.stringify({ code: '42501', message: 'denied' }) } : null;
    const init = ([u]) => { try { if (!localStorage.getItem('professify_commits_' + u)) { localStorage.setItem('professify_commits_' + u, JSON.stringify([{ id: 'c0000000-0000-4000-8000-0000000000a1', kind: 'work', name: 'Barista', days: 'MWF', s: 960, e: 1260, busy: true }])); localStorage.setItem('professify_commits_pending_' + u, JSON.stringify({ 'c0000000-0000-4000-8000-0000000000a1': 'save' })); } } catch (e) {} };
    const { page, close } = await desk({ tables, hook, init: `(${init.toString()})(['${ME}'])` });
    await tick(page, 1500); await goClasses(page);
    ok((await cardRows(page))[0] === 'Barista · Mon Wed Fri · 4:00–9:00p · friends see Busy', 'a change still waiting here beats the server’s older copy after a reload', await cardRows(page));
    await close(); }
});

test('blocks', async () => {
  const rows = [row({ id: 'c0000000-0000-4000-8000-0000000000a1', name: 'Barista' }), row({ id: 'c0000000-0000-4000-8000-0000000000a3', kind: 'club', name: 'Secret Club', days: 'S', start_min: 540, end_min: 780 })];
  const { page, close, log } = await desk({ tables: withRows(rows), rpc: rpcWith(AVERY_BUSY) });
  await tick(page, 1500); await goClasses(page);
  const cal = await page.evaluate(() => {
    const cols = [...document.querySelectorAll('#watchMineOut .mc-cal .cal-col')].filter(c => c.querySelector('.cal-dh') && !c.classList.contains('cal-any'));
    return cols.map(c => ({ day: c.querySelector('.cal-dh').textContent.trim(), cm: [...c.querySelectorAll('.cal-cm')].map(b => b.textContent + '|' + b.getAttribute('aria-label')) }));
  });
  ok(cal.map(c => c.day).join() === 'Mon,Tue,Wed,Thu,Fri,Sat', 'my week: Saturday’s column appears because Secret Club meets then (and Sunday’s does not)', cal.map(c => c.day));
  ok(cal[0].cm[0] === 'Barista|Edit Barista, 4:00–8:00p' && cal[2].cm.length === 1 && cal[4].cm.length === 1 && cal[1].cm.length === 0 && cal[5].cm[0].startsWith('Secret Club|'), 'my week: Barista hatched on Mon, Wed, Fri by name; Secret Club on Sat', cal);
  const geo = await page.evaluate(() => {
    const b = document.querySelector('.mc-cal .cal-col:nth-of-type(2) .cal-cm'), col = b.parentElement, cs = getComputedStyle(b), blk = document.querySelector('.mc-cal .cal-block');
    return { cls: b.className, top: b.offsetTop, h: b.offsetHeight, bg: cs.backgroundImage.slice(0, 40), blue: blk ? getComputedStyle(blk).backgroundColor : '', cmBg: cs.backgroundColor, inside: b.offsetTop >= 0 && b.offsetTop + b.offsetHeight <= col.offsetHeight + 1, tag: b.tagName };
  });
  ok(/repeating-linear-gradient/.test(geo.bg) && geo.inside && geo.tag === 'BUTTON' && geo.cmBg !== geo.blue, 'my week: hatched (not the class blue), inside its column, and a button you can press', geo);
  /* Home: yours on My schedule */
  await page.evaluate(() => { show('home'); }); await tick(page, 600);
  ok(await page.evaluate(() => document.querySelectorAll('.hmc-card .hmc-cm').length) === 4, 'Home: “My schedule” hatches Mon, Wed, Fri and Sat', await page.evaluate(() => document.querySelectorAll('.hmc-cm').length));
  /* Home: the friend's card — Busy, never a name */
  const fr = await page.evaluate((id) => {
    const cards = [...document.querySelectorAll('.hm-card')].filter(c => /Avery/.test(c.innerText));
    const c = cards[0]; if (!c) return null;
    const b = [...c.querySelectorAll('.cal-cm')];
    return { n: b.length, text: [...new Set(b.map(x => x.textContent))], fr: b.every(x => x.classList.contains('fr')), html: c.innerHTML.includes('Barista') || c.innerHTML.includes('Secret') };
  }, AVERY);
  ok(fr && fr.n === 2 && fr.text.join() === 'Busy' && fr.fr && !fr.html, 'Home: Avery’s card hatches Tue and Thu as “Busy” — no name', fr);
  ok(await page.evaluate(() => !/Barista|Secret Club/.test([...document.querySelectorAll('.hm-card')].filter(c => /Avery|Rowan|Sky|Quinn|Harper/.test(c.innerText)).map(c => c.innerHTML).join(''))), 'Home: no friend’s card carries your names');
  /* the friend's profile week */
  await page.evaluate(id => { openFriendProfile(id); }, AVERY); await tick(page, 800);
  const prof = await page.evaluate(() => ({ n: document.querySelectorAll('.frp-cal .cal-cm').length, text: [...new Set([...document.querySelectorAll('.frp-cal .cal-cm')].map(x => x.textContent))].join(), label: (document.querySelector('.frp-cal .cal-cm') || {}).getAttribute && document.querySelector('.frp-cal .cal-cm').getAttribute('aria-label'), mine: /Barista|Secret/.test((document.querySelector('.frp-cal') || { innerHTML: '' }).innerHTML) }));
  ok(prof.n === 2 && prof.text === 'Busy' && prof.label === 'Busy, 10:00a–12:00p' && !prof.mine, 'profile: Avery’s week draws “Busy, 10:00a–12:00p” on Tue and Thu, and carries none of your names', prof);
  /* what goes over the wire for friends: nothing about names */
  ok(log.rpcs.filter(r => r.fn === 'friend_busy_blocks').length >= 1, 'the RPC is asked for friends’ blocks');
  ok(log.errors.length === 0, 'blocks: no page errors', log.errors);
  await close();
  /* a friend who left the item off sends nothing: nothing is drawn */
  { const o = await desk({ tables: withRows([row()]), rpc: rpcWith([]) }); await tick(o.page, 1500);
    ok(await o.page.evaluate(() => document.querySelectorAll('.hm-card .cal-cm').length) === 0, 'no busy blocks from the RPC: nothing is drawn on friends’ cards');
    await o.close(); }
  /* an error from the RPC draws nothing either */
  { const o = await desk({ tables: withRows([row()]), rpc: rpcWith({ __error: { code: '42883', message: 'function does not exist' } }) }); await tick(o.page, 1500);
    ok(await o.page.evaluate(() => document.querySelectorAll('.hm-card .cal-cm').length) === 0 && o.log.errors.length === 0, 'RPC missing: nothing is drawn and nothing breaks', o.log.errors);
    await o.close(); }
});

test('terms', async () => {
  /* both term views of My classes carry the card and the hatching */
  const { page, close, log } = await desk({ terms: 'live', tables: withRows([row()]) });
  await settle(page);
  await page.evaluate(() => { show('sched'); setSchedTab('mine'); mcSetTermView('now'); }); await tick(page, 500);
  const a = await page.evaluate(() => ({ card: !!document.querySelector('.cm-card .cm-row'), cm: document.querySelectorAll('.mc-cal .cal-cm').length, view: mcTermView() }));
  ok(a.view === 'now' && a.card && a.cm === 3, 'now-term view: the card and three hatched blocks', a);
  await page.evaluate(() => { mcSetTermView('term'); }); await tick(page, 500);
  const b = await page.evaluate(() => ({ card: !!document.querySelector('.cm-card .cm-row'), view: mcTermView() }));
  ok(b.view === 'term' && b.card, 'choose-in term view (no classes there yet): the card is still there', b);
  await page.click('.cm-card .cm-add'); await tick(page, 400);
  ok(await page.evaluate(() => document.getElementById('cmBack').classList.contains('open')), 'and + Add opens from it');
  ok(log.errors.length === 0, 'terms: no page errors', log.errors);
  await close();
});

test('free', async () => {
  const rows = [row({ name: 'Barista shift' })];
  const { page, close } = await desk({ tables: withRows(rows), rpc: rpcWith(AVERY_BUSY) });
  await settle(page);
  const r = await page.evaluate((id) => {
    const wed7pm = new Date(2026, 9, 14, 19, 0), wed5pm = new Date(2026, 9, 14, 17, 0), tue1130 = new Date(2026, 9, 13, 11, 30), tue1030 = new Date(2026, 9, 13, 10, 30);
    const mine = avMyMeets(), fr = avMeetsOf(findFriend(id));
    const g = gpMemberBusy({ me: true }), gf = gpMemberBusy({ id });
    return { me: avLine(avState(mine, wed7pm)), me5: avLine(avState(mine, wed5pm)), fr: avLine(avState(fr, tue1130)), frClass: avLine(avState(fr, tue1030)), frOpen: avLine(avState(fr, new Date(2026, 9, 13, 8, 0))),
      meBusy: g.busy.filter(b => b.code === 'Barista shift').map(b => [b.di, b.s, b.e].join('-')).join(), frBusy: gf.busy.filter(b => b.code === 'Busy').map(b => [b.di, b.s, b.e].join('-')).join(),
      frNames: JSON.stringify(gf).includes('Barista'), kinds: mine.filter(m => m.cm).length };
  }, AVERY);
  ok(r.me === 'Barista shift till 8p', 'status: yours reads “Barista shift till 8p”', r.me);
  ok(r.fr === 'Busy till 12p', 'status: a friend’s reads “Busy till 12p”', r.fr);
  ok(r.me5 === 'In BUS 3431 till 6:00pm', 'status: while you are in a class that is over your shift, the class wins', r.me5);
  ok(r.frClass === 'In PHIL 3331 till 11:00am', 'status: a class keeps its own wording and beats a busy block (“In PHIL 3331 till 11:00am”)', r.frClass);
  ok(r.frOpen === 'No class till 8:10am', 'status: before their first class it is “No class till 8:10am”, never moved by a busy block', r.frOpen);
  ok(r.meBusy === '0-960-1200,2-960-1200,4-960-1200', 'free time: gpMemberBusy counts yours (Mon, Wed, Fri 4–8p)', r.meBusy);
  ok(r.frBusy === '1-600-720,3-600-720' && !r.frNames, 'free time: and a friend’s as Busy (Tue, Thu 10–12), no name', { b: r.frBusy, n: r.frNames });
  await close();
  /* a friend with no classes and a busy block: only the block that is on now says anything, and "no class" is never claimed */
  { const o = await desk({ tables: withRows([]), rpc: rpcWith([{ user_id: FX.FRIENDS[4].id, days: 'T', start_min: 600, end_min: 720 }]) }); await settle(o.page);
    const l = await o.page.evaluate((id) => [avLine(avState(avMeetsOf(findFriend(id)), new Date(2026, 9, 13, 11, 0))), avLine(avState(avMeetsOf(findFriend(id)), new Date(2026, 9, 13, 8, 0)))], FX.FRIENDS[4].id);
    ok(l[0] === 'Busy till 12p' && l[1] === '', 'a friend with no classes: “Busy till 12p” while it is on, nothing otherwise (never “No class”)', l);
    await o.close(); }
  /* a busy block EARLIER than the first class: "No class till" still names the first class (a block is not a class) */
  { const o = await desk({ tables: withRows([row({ days: 'W', start_min: 420, end_min: 480 })]) }); await settle(o.page);
    const r = await o.page.evaluate(() => {
      const m = avMyMeets(), wed6 = new Date(2026, 9, 14, 6, 0);
      return { line: avLine(avState(m, wed6)), want: avLine(avState(m.filter(x => !x.cm), wed6)), blocks: m.filter(x => x.cm).map(x => x.meet.start + '-' + x.meet.end).join() };
    });
    ok(r.blocks === '420-480' && /^No class till /.test(r.want) && r.line === r.want, 'a shift at 7am before your first class: at 6am it is the same “No class till <first class>” as without the shift', r);
    await o.close(); }
  /* a friend with no id is nobody: your own shifts are never read as theirs */
  { const o = await desk({ tables: withRows([row()]), rpc: rpcWith(AVERY_BUSY) }); await settle(o.page);
    const r = await o.page.evaluate(() => {
      const out = []; cmPushBusy(out, undefined); cmPushBusy(out, null); cmPushBusy(out, '');
      const g = gpMemberBusy({}), g2 = gpMemberBusy({ id: undefined });
      return { out: out.length, mine: cmBlocks('me').length, g: g.busy.filter(b => b.code === 'Barista shift').length, g2: g2.busy.filter(b => b.code === 'Barista shift').length };
    });
    ok(r.mine === 1 && r.out === 0 && r.g === 0 && r.g2 === 0, 'a friend with no id gets none of your shifts in their free time', r);
    await o.close(); }
});

test('overlap', async () => {
  const { page, close, log } = await desk({ tables: withRows([row()]) });
  await tick(page, 1500);
  const chip = await page.evaluate(() => secConflictChip('BUS 3431', { days: 'MoWe 4:10PM - 6:00PM' }));
  ok(/class="cs-cm"[^>]*>Overlaps Barista Mon\/Wed 4–8p<\/span>/.test(chip), 'class page chip: “Overlaps Barista Mon/Wed 4–8p”', chip);
  ok(!/cs-clash/.test(chip), 'and it is not the red clash', chip);
  ok(await page.evaluate(() => cmChipHtml({ days: 'TuTh 8:10AM - 10:00AM' })) === '', 'a section that misses it says nothing');
  ok(await page.evaluate(() => cmChipHtml({ days: 'MoWe 8:00PM - 9:00PM' })) === '' && await page.evaluate(() => cmChipHtml({ days: 'MoWe 3:00PM - 4:00PM' })) === '', 'a section that starts when it ends, or ends when it starts, says nothing');
  /* the class page really draws it */
  await page.evaluate(() => { gotoSection('BUS 3431'); }); await tick(page, 1000);
  const dom = await page.evaluate(() => [...document.querySelectorAll('.cs-cm')].map(x => x.textContent));
  ok(dom.length > 0 && dom.every(t => t === 'Overlaps Barista Mon/Wed 4–8p'), 'the class page shows it on the section that overlaps', dom);
  /* My classes: an amber pill, not a red clash */
  await goClasses(page);
  const pill = await page.evaluate(() => [...document.querySelectorAll('.sf-pill')].map(b => ({ t: b.textContent.replace(/[▴▾]/g, '').trim(), warn: b.classList.contains('sf-warn') })));
  ok(pill.filter(p => p.t === 'Overlaps Barista').length === 1 && !pill.find(p => p.t === 'Overlaps Barista').warn, 'My classes: one “Overlaps Barista” pill, and it is not a red clash (sf-warn)', pill);
  ok(pill.filter(p => p.warn).map(p => p.t).join() === '1 time conflict', 'the red time-conflict pill is the fixture’s own and is not made by Barista', pill);
  await page.click('.sf-pill:has-text("Overlaps Barista")'); await tick(page, 300);
  ok(await page.evaluate(() => /BUS 3431 overlaps Barista Mon\/Wed 4–8p/.test(document.querySelector('.sf-detail').innerText)), 'and its detail names the class and the overlap');
  ok(await page.evaluate(() => ![...document.querySelectorAll('.mc-card')].some(c => /BUS 3431/.test(c.innerText) && c.querySelector('.mc-clash'))), 'no “Time clash” on BUS 3431 for it');
  ok(log.errors.length === 0, 'overlap: no page errors', log.errors);
  await close();
});

test('blocksApi', async () => {
  const { page, close } = await desk({ tables: withRows([row(), row({ id: 'c0000000-0000-4000-8000-0000000000a4', name: 'Secret', days: 'U', start_min: 600, end_min: 660, busy: false })]), rpc: rpcWith(AVERY_BUSY) });
  await settle(page);
  const r = await page.evaluate((id) => ({ me: cmBlocks('me').map(b => [b.label, b.meet.days.join(''), b.meet.start, b.meet.end, b.mine, b.cm].join('|')), dflt: cmBlocks().length, obj: cmBlocks({ x: 1 }).length, fr: cmBlocks(id).map(b => [b.label, b.code, b.name, b.meet.days.join(''), b.mine].join('|')), none: cmBlocks('nobody').length,
    okMeet: cmBlocks('me').every(b => okMeet(b.meet)) }), AVERY);
  ok(r.me.join() === 'Secret|Su|600|660|true|mine,Barista|MoWeFr|960|1200|true|mine' && r.dflt === 2 && r.obj === 2 && r.okMeet, 'window.cmBlocks(): meet-shaped blocks of yours (okMeet-clean), by name; the default is yours', r);
  ok(r.fr.join() === 'Busy|Busy|Busy|TuTh|false', 'window.cmBlocks(friend id): one Busy block — label, code and name all “Busy”, no name', r.fr);
  ok(r.none === 0, 'someone who is not a friend has none');
  await close();
});

test('reset', async () => {
  /* a slow read that lands after a sign-out must not paint or write anything */
  let release; const gate = new Promise(r => { release = r; });
  const hook = async (u, m) => { if (u.pathname === '/rest/v1/commitments' && m === 'GET') { await gate; return null; } return null; };
  const { page, close, log } = await desk({ tables: withRows([row()]), hook, wait: 2500 });
  await tick(page, 600);
  await page.evaluate(() => { cmReset(); });
  release(); await tick(page, 800); await goClasses(page);
  const st = await page.evaluate(() => ({ list: TCCommit.state.list.length, uid: TCCommit.state.uid, blocks: cmBlocks('me').length, card: !!document.querySelector('.cm-card') }));
  ok(st.list === 0 && st.uid === null && st.blocks === 0 && !st.card, 'sign-out while the read is in flight: nothing lands afterwards', st);
  ok(writes(log).length === 0, 'and nothing is written', writes(log));
  await close();
  /* an account switch: the other account's list is not shown */
  { const o = await desk({ tables: withRows([row()]) }); await tick(o.page, 1500);
    await o.page.evaluate(() => { cmReset(); }); await tick(o.page, 300);
    const s2 = await o.page.evaluate(() => ({ blocks: cmBlocks('me').length, card: !!document.querySelector('.cm-card'), home: document.querySelectorAll('.hmc-cm').length }));
    const m2 = await o.page.evaluate(() => ({ list: TCCommit.state.list.length, fr: Object.keys(TCCommit.state.fr).length, uid: TCCommit.state.uid}));
    ok(s2.blocks === 0 && !s2.card && s2.home === 0, 'sign-out: the card, the week and Home let go of them', s2);
    ok(m2.list === 0 && m2.fr === 0 && m2.uid === null, 'sign-out: your list is gone from memory, not just hidden (the next account never holds it)', m2);
    await o.close(); }
});

/* a slow save must not come back after the delete that followed it (review, 2026-10-14) */
test('order', async () => {
  let release; const gate = new Promise(r => { release = r; });
  const st = { calls: [] };
  const hook = async (u, m, body) => { if (u.pathname !== '/rest/v1/commitments' || m === 'GET') return null; st.calls.push(m); if (m === 'POST') await gate; return null; };
  const { page, close, tables, log } = await desk({ tables: withRows([]), hook });
  await tick(page, 1200);
  await page.evaluate(() => { const x = { id: 'c0000000-0000-4000-8000-0000000000d1', kind: 'work', name: 'Slow', days: 'M', s: 600, e: 700, busy: true }; window._p = TCCommit.save(x).then(() => TCCommit.drop(x.id)); });
  await tick(page, 500);
  ok(st.calls.join() === 'POST', 'order: the delete waits for the save that is still on its way', st.calls);
  release(); await tick(page, 800);
  ok(st.calls.join() === 'POST,DELETE' && !(tables.commitments || []).some(r => r.id === 'c0000000-0000-4000-8000-0000000000d1') && !(await LS(page, 'professify_commits_pending_')), 'order: then it is deleted, and nothing is left on the server or waiting', { c: st.calls, t: tables.commitments });
  /* a delete asked for while a save is still waiting to go up: the older save is not sent afterwards */
  await page.evaluate(() => { const x = { id: 'c0000000-0000-4000-8000-0000000000d2', kind: 'work', name: 'Two', days: 'T', s: 600, e: 700, busy: true }; window._q = TCCommit.save(x); window._r = TCCommit.drop(x.id); });
  await tick(page, 800);
  ok(st.calls.filter(c => c === 'POST').length === 1 && !(tables.commitments || []).some(r => r.id === 'c0000000-0000-4000-8000-0000000000d2'), 'order: a save overtaken by a delete is not sent after it', st.calls);
  ok(log.errors.length === 0, 'order: no page errors', log.errors);
  await close();
});

test('parse', async () => {
  const { page, close } = await desk({ tables: withRows([]), wait: 2500 });
  const P = await page.evaluate(() => {
    const t = (s, e) => { const r = TCCommit.parseTime(s, e); return r.ok ? r.min : r.why; };
    return { '4pm': t('4pm'), '4:30 pm': t('4:30 pm'), '16:30': t('16:30'), '4:30p': t('4:30p'), '4 p.m.': t('4 p.m.'), '8a': t('8a'), '8AM': t('8AM'), '12pm': t('12pm'), '12am': t('12am'), '12am end': t('12am', true), '1630': t('1630'), '08:00': t('08:00'),
      'noon': t('noon'), '4': t('4'), '9:30': t('9:30'), '8:00': t('8:00'), '': t(''), '25:00': t('25:00'), '4:75pm': t('4:75pm'), '13pm': t('13pm'), '0pm': t('0pm'), 'abc': t('abc'), '24:00': t('24:00'), '23:59': t('23:59'), ' 4 pm ': t(' 4 pm ') };
  });
  const W = { '4pm': 960, '4:30 pm': 990, '16:30': 990, '4:30p': 990, '4 p.m.': 960, '8a': 480, '8AM': 480, '12pm': 720, '12am': 0, '12am end': 1440, '1630': 990, '08:00': 480, 'noon': 720, '4': 'ampm', '9:30': 'ampm', '8:00': 'ampm', '': 'empty', '25:00': 'bad', '4:75pm': 'bad', '13pm': 'bad', '0pm': 'bad', 'abc': 'bad', '24:00': 'bad', '23:59': 1439, ' 4 pm ': 960 };
  ok(Object.keys(W).every(k => P[k] === W[k]), 'times are read like the Portal shows them (4pm, 4:30 pm, 16:30, 12am end = midnight…), a bare number is not guessed', Object.keys(W).filter(k => P[k] !== W[k]).map(k => k + ' → ' + P[k] + ' (want ' + W[k] + ')'));
  const R = await page.evaluate(() => [TCCommit.range(960, 1200), TCCommit.range(660, 840), TCCommit.range(570, 690), TCCommit.rangeShort(960, 1200), TCCommit.rangeShort(660, 780), TCCommit.rangeShort(570, 690)]);
  ok(R.join() === '4:00–8:00p,11:00a–2:00p,9:30–11:30a,4–8p,11a–1p,9:30–11:30a', 'ranges: 4:00–8:00p · 11:00a–2:00p · 4–8p · 11a–1p', R);
  await close();
});

const names = Object.keys(T).filter(n => !ONLY || n === ONLY);
for (const n of names) { if (!QUIET) console.log('\n' + n); try { await T[n](); } catch (e) { fail++; fails.push(n + ' (threw)'); console.log('  FAIL', n, 'threw', String(e && e.stack || e).slice(0, 900)); } }
console.log(`\ncheck-desktop-commitments: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
