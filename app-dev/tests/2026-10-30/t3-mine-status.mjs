/* Fix 3: a section already in My Classes can go Waitlisted ↔ Enrolled and change its waitlist spot (one row, upserted). */
import { openApp, mk, tap, toastText, sheetType, sheetText, acts } from './tlib.mjs';
const R = mk('t3-mine-status'); const port = +(process.env.APP_PORT || 8655);
const { page, close, log } = await openApp({ port, time: null });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows, null, { timeout: 15000 }); await page.waitForTimeout(400);
const full = await page.evaluate(() => { const mine = new Set(personSecs('me').map(s => s.code)); const s = Object.values(SEC).find(x => x.rawDays && (x.status === 'full' || x.status === 'wait') && !mine.has(x.code)); return s && { id: s.id, code: s.code }; });
R.ok(!!full, '(setup) a full section', full);
const rows = () => page.evaluate(async c => (await TC.client().from('my_sections').select('class_nbr,status,wl_pos').eq('user_id', TC.user.id).eq('code', c)).data, full.code);
await page.evaluate(id => { openAddTo(id); if (UI.sheet.dest !== 'mine') A.atGroup('classes'); }, full.id); await page.waitForTimeout(300);
await tap(page, '#sheet .at-seg button', 'Waitlisted');
await page.fill('#atwl', '4'); await page.waitForTimeout(100);
await tap(page, '#sheet .at-go', null, { wait: 1800 });
R.ok(JSON.stringify(await rows()) === JSON.stringify([{ class_nbr: String(full.id), status: 'waitlisted', wl_pos: 4 }]) || (await rows()).length === 1 && (await rows())[0].status === 'waitlisted' && +(await rows())[0].wl_pos === 4, '(setup) saved waitlisted #4', await rows());
/* reopen: the seat is there to change, on what's saved */
await page.evaluate(id => openAddTo(id), full.id); await page.waitForTimeout(300);
const seg = await page.evaluate(() => ({ dest: UI.sheet.dest, on: [...document.querySelectorAll('#sheet [data-a="atMineStatus"]')].map(b => b.textContent + (b.classList.contains('on') ? '*' : '')), wl: (document.getElementById('atwl') || {}).value }));
R.ok(seg.on.join() === 'Enrolled,Waitlisted*' && seg.wl === '4', 'reopened: Your seat shows Waitlisted with spot 4', seg);
R.ok(/on the waitlist \(#4\)/.test(await sheetText(page)), 'the note says you’re on the waitlist (#4)', await sheetText(page));
/* got in */
await tap(page, '#sheet [data-a="atMineStatus"]', 'Enrolled', { wait: 1000 });
let r = await rows();
R.ok(r.length === 1 && r[0].status === 'enrolled' && r[0].wl_pos == null, 'tapping Enrolled saves enrolled on the same row', r);
R.ok(/Saved: enrolled/.test(await toastText(page)) && await sheetType(page) === 'addTo', 'a Saved toast; the sheet stays open', await toastText(page));
R.ok(await page.evaluate(id => personSecs('me').some(s => s.id === id && !s.mineWl), full.id), 'My Classes shows it enrolled');
/* back to the waitlist, spot 7 */
await tap(page, '#sheet [data-a="atMineStatus"]', 'Waitlisted', { wait: 1000 });
await page.fill('#atwl', '7'); await page.press('#atwl', 'Enter'); await page.waitForTimeout(1000);
r = await rows();
R.ok(r.length === 1 && r[0].status === 'waitlisted' && +r[0].wl_pos === 7, 'Waitlisted, then spot 7 and Enter: saved waitlisted #7', r);
const posts = log.writes.filter(x => x.table === 'my_sections' && x.m === 'POST');
R.ok(posts.every(x => /on_conflict=user_id%2Cclass_nbr%2Cterm|on_conflict=user_id,class_nbr,term/.test(x.query)), 'every save is an upsert on user_id,class_nbr,term', posts.map(x => x.query));
await page.evaluate(() => A.closeSheet()); await page.waitForTimeout(300);
/* from the week: the section's sheet leads here */
await page.evaluate(id => { A.tab('schedule'); A.schedTab('mine'); A.secSheet(SEC[id].code, id); }, full.id); await page.waitForTimeout(300);
const a = await acts(page);
R.ok(a.some(x => /^addPlanSheet:Waitlisted · change or remove/.test(x)), 'its section sheet on My Classes has “Waitlisted · change or remove”', a);
await tap(page, '#sheet [data-a="addPlanSheet"]', null, { wait: 300 });
R.ok(await page.evaluate(() => UI.sheet.type === 'addTo' && UI.sheet.dest === 'mine' && !!document.querySelector('#sheet [data-a="atMineStatus"]')), 'which opens Add to your week on My Classes, seat editable');
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
