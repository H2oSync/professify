/* Fix 2: a Fall 2026 (NOW_TERM) class the Degree Progress Report saved with no section can get its section —
   "This is my section" writes my_sections under 2268 (upsert user_id,class_nbr,term), stories/status use it, and
   it can be changed and removed. Live two-term config: choose in Spring 2027, now = Fall 2026. */
import { openApp, mk, tap, toastText, sheetType, sheetText, acts, SPRING_CFG, FX } from './tlib.mjs';
const R = mk('t2-now-section'); const port = +(process.env.APP_PORT || 8653);
const T = JSON.parse(JSON.stringify(FX.TABLES));
T.course_seats = T.course_seats.concat(T.course_seats.filter(r => r.course_code !== 'BUS 3438').map(r => Object.assign({}, r, { term: '2274' })));
T.saved_classes.push({ user_id: FX.ME.id, term: '2268', code: 'PHIL 3331' });
const { page, close, log } = await openApp({ port, terms: SPRING_CFG, tables: T });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.nowMineRows, null, { timeout: 15000 }); await page.clock.runFor(800); await page.waitForTimeout(400);
const rows = () => page.evaluate(async () => ({ saved: (await TC.client().from('saved_classes').select('code,term').eq('user_id', TC.user.id).eq('code', 'PHIL 3331')).data, secs: (await TC.client().from('my_sections').select('code,term,class_nbr,days,status').eq('user_id', TC.user.id).eq('code', 'PHIL 3331')).data }));
await page.evaluate(() => { A.tab('schedule'); A.schedTab('mine'); A.pickMineTerm('Fall 2026'); }); await page.clock.runFor(1200); await page.waitForTimeout(300);
const st0 = await page.evaluate(() => status('me').t);
R.ok(await tap(page, '.mine-any .any-c[data-x="PHIL 3331"]', null, { wait: 300 }), 'PHIL 3331 (Fall 2026, no section) is an Anytime chip');
await page.clock.runFor(1500); await page.waitForTimeout(300);
R.ok(await sheetType(page) === 'anyClass', 'its chip opens the class sheet', await sheetType(page));
let a = await acts(page), t = await sheetText(page);
R.ok(a.some(x => /^nowMine:/.test(x)) && /Which section are you in\?/.test(t) && /Fall 2026/.test(t), 'the sheet lists its Fall 2026 sections to pick', { a, t: t.slice(0, 200) });
R.ok(a.some(x => /^anyRemove:Remove from My Classes/.test(x)), 'and Remove from My Classes', a);
if (await sheetType(page) === 'anyClass') await page.screenshot({ path: '/tmp/claude-0/fix/mine/sheet.png' });
const pick = await page.evaluate(() => document.querySelector('#sheet [data-a="nowMine"]').dataset.x);
await tap(page, '#sheet [data-a="nowMine"]', null, { wait: 300 }); await page.clock.runFor(1200); await page.waitForTimeout(300);
let r = await rows();
const nbr = pick.split(':').pop();
R.ok(r.secs.length === 1 && r.secs[0].term === '2268' && String(r.secs[0].class_nbr) === nbr && r.secs[0].days, 'one my_sections row under 2268 with the section and its meeting time', r);
const w = log.writes.filter(x => x.table === 'my_sections' && x.m === 'POST');
R.ok(w.length && w.every(x => /on_conflict=user_id%2Cclass_nbr%2Cterm|on_conflict=user_id,class_nbr,term/.test(x.query)), 'written as an upsert on user_id,class_nbr,term', w.map(x => x.query));
const now = await page.evaluate(id => ({ has: nowSecs('me').some(s => s.id === id && s.s != null), anyChip: document.querySelectorAll('.mine-any .any-c[data-x="PHIL 3331"]').length, st: status('me').t, sheet: UI.sheet && UI.sheet.type }), pick);
R.ok(now.has && now.anyChip === 0 && !now.sheet, 'it is now a timed Fall class (no longer Anytime); the sheet closed', now);
R.ok(now.st !== st0 && /In PHIL 3331 till/.test(now.st), 'your status (stories/rings) uses it: “' + now.st + '” (was “' + st0 + '”)', now.st);
R.ok(/is your Fall 2026 section/.test(await toastText(page)), 'toast says so, with Undo', await toastText(page));
/* the section's own sheet: it's yours, remove from there */
await page.evaluate(id => A.secSheet('PHIL 3331', id), pick); await page.waitForTimeout(300);
a = await acts(page); t = await sheetText(page);
R.ok(/Your Fall 2026 section/.test(t) && a.some(x => /^nowSecRm:Remove from My Classes/.test(x)), 'the section sheet says it’s yours and can remove it', a);
await tap(page, '#sheet [data-a="nowSecRm"]', null, { wait: 300 }); await page.clock.runFor(1200); await page.waitForTimeout(300);
r = await rows();
R.ok(!r.secs.length && !r.saved.some(x => x.term === '2268'), 'Remove takes the class off Fall 2026 (both tables)', r);
await tap(page, '#toast .tundo', null, { wait: 300 }); await page.clock.runFor(1200); await page.waitForTimeout(300);
r = await rows();
R.ok(r.secs.length === 1 && r.saved.some(x => x.term === '2268'), 'Undo puts the class and its section back', r);
/* another class with 2+ Fall sections: a not-mine section offers This is my section; with one already mine, Switch / Keep both */
const two = await page.evaluate(async () => { await loadNowAll(); return Object.keys(NOWT.byCode).find(c => NOWT.byCode[c].length >= 2 && !nowSecs('me').some(s => s.code === c)); });
await page.clock.runFor(800);
const ids = await page.evaluate(c => NOWT.byCode[c].map(s => s.id), two);
await page.evaluate(([c, id]) => A.secSheet(c, id), [two, ids[0]]); await page.waitForTimeout(300);
a = await acts(page);
R.ok(!a.some(x => /^nowMine/.test(x)) && a.some(x => /^openClass:View class/.test(x)), `${two}: not on your Fall list — its section sheet is unchanged (View class only)`, a);
await page.evaluate(async c => { await TC.client().from('saved_classes').upsert({ user_id: TC.user.id, term: '2268', code: c }, { onConflict: 'user_id,code,term' }); await loadMine(); relinkPeople(); A.secSheet(c, NOWT.byCode[c][0].id); }, two); await page.waitForTimeout(300);
a = await acts(page);
R.ok(a.some(x => x === 'nowMine:This is my section'), `${two} saved for Fall with no section (as the report saves it): its section sheet offers “This is my section”`, a);
await tap(page, '#sheet [data-a="nowMine"]', null, { wait: 300 }); await page.clock.runFor(1200); await page.waitForTimeout(300);
await page.evaluate(([c, id]) => A.secSheet(c, id), [two, ids[1]]); await page.waitForTimeout(300);
a = await acts(page);
R.ok(a.some(x => /^nowMine:Switch to this section/.test(x)) && a.some(x => /^nowMine:Keep both/.test(x)), 'another section of a class you have: Switch, or Keep both', a);
await tap(page, '#sheet [data-a="nowMine"]', 'Switch', { wait: 300 }); await page.clock.runFor(1200); await page.waitForTimeout(300);
const sw = await page.evaluate(async c => (await TC.client().from('my_sections').select('class_nbr,term').eq('user_id', TC.user.id).eq('code', c)).data, two);
R.ok(sw.length === 1 && String(sw[0].class_nbr) === ids[1].split(':').pop() && sw[0].term === '2268', 'Switch leaves only the new section', sw);
/* nothing written under Spring */
R.ok(!log.writes.some(x => (x.table === 'my_sections' || x.table === 'saved_classes') && x.m === 'POST' && [].concat(x.body).some(b => b && b.term === '2274')), 'nothing was written under Spring 2027');
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
