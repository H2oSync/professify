/* Fix 1: a My Classes class with no section (Anytime chip) opens a sheet — Pick a time / Remove — offered or not. */
import { openApp, mk, tap, toastText, sheetType, sheetText, acts } from './tlib.mjs';
const R = mk('t1-anytime-sheet'); const port = +(process.env.APP_PORT || 8651);
const { page, close, log } = await openApp({ port, time: null });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows, null, { timeout: 15000 }); await page.waitForTimeout(400);
const db = () => page.evaluate(async () => (await TC.client().from('saved_classes').select('code,term').eq('user_id', TC.user.id)).data.map(r => r.code).sort());
await page.evaluate(() => { A.tab('schedule'); A.schedTab('mine'); }); await page.waitForTimeout(400);
/* an offered class saved with no section */
const off = await page.evaluate(async () => { const mine = new Set(personSecs('me').map(s => s.code).concat(PEOPLE.me.unplaced || [])); const c = Object.keys(COURSES).find(k => !mine.has(k) && secsOf(k).length); await TC.client().from('saved_classes').upsert({ user_id: TC.user.id, term: CFG.TERM, code: c }, { onConflict: 'user_id,code,term' }); await loadMine(); relinkPeople(); render(true); return c; });
R.ok(await tap(page, `.mine-any .any-c[data-x="${off}"]`), `${off} (offered, no section) is an Anytime chip`);
R.ok(await sheetType(page) === 'anyClass', 'its chip opens the class sheet, not a dead-end page', await sheetType(page));
let a = await acts(page);
R.ok(a.some(x => /^openClass:Pick a time/.test(x)) && a.some(x => /^anyRemove:Remove from My Classes/.test(x)), 'the sheet offers Pick a time and Remove from My Classes', a);
R.ok((await sheetText(page)).includes(off), 'the sheet names the class', await sheetText(page));
await tap(page, '#sheet [data-a="openClass"]', 'Pick a time', { wait: 500 });
const w = await page.evaluate(() => ({ s: cur().s, p: cur().p, sheet: UI.sheet && UI.sheet.type, plus: document.querySelectorAll('#scroll .secrow .addbtn').length }));
R.ok(w.s === 'classDetail' && w.p.code === off && !w.sheet && w.plus > 0, 'Pick a time opens its class page with the + on each section', w);
await page.evaluate(() => A.back()); await page.waitForTimeout(300);
await tap(page, `.mine-any .any-c[data-x="${off}"]`);
await tap(page, '#sheet [data-a="anyRemove"]', null, { wait: 900 });
R.ok(!(await db()).includes(off), 'Remove takes it off saved_classes', await db());
R.ok(/Removed/.test(await toastText(page)) && await page.locator(`.mine-any .any-c[data-x="${off}"]`).count() === 0, 'a Removed toast with Undo; the chip is gone', await toastText(page));
await tap(page, '#toast .tundo', null, { wait: 1000 });
R.ok((await db()).includes(off), 'Undo saves it back', await db());
await page.evaluate(async c => { await TC.removeMyClass(c); render(true); }, off);
/* not offered this term */
await page.evaluate(async () => { await TC.client().from('saved_classes').upsert({ user_id: TC.user.id, term: CFG.TERM, code: 'BUS 4999' }, { onConflict: 'user_id,code,term' }); await loadMine(); relinkPeople(); render(true); });
await page.waitForTimeout(300);
R.ok(await tap(page, '.mine-any .any-c[data-x="BUS 4999"]'), 'an unoffered saved class (BUS 4999) is an Anytime chip');
const t = await sheetText(page); a = await acts(page);
R.ok(await sheetType(page) === 'anyClass' && /isn’t offered in Fall 2026/.test(t) && !a.some(x => /Pick a time/.test(x)), 'its sheet says it isn’t offered (no Pick a time)', { t, a });
R.ok(a.some(x => /^anyRemove/.test(x)), 'and it can still be removed', a);
/* a double tap on Remove sends one delete */
const before = log.writes.filter(x => x.table === 'saved_classes' && x.m === 'DELETE').length;
const b = await page.evaluate(() => { const e = document.querySelector('#sheet [data-a="anyRemove"]'); const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
await page.touchscreen.tap(b.x, b.y); await page.touchscreen.tap(b.x, b.y); await page.waitForTimeout(1000);
R.ok(log.writes.filter(x => x.table === 'saved_classes' && x.m === 'DELETE').length === before + 1 && !(await db()).includes('BUS 4999'), 'Remove (double-tapped): one delete, BUS 4999 gone', await db());
R.ok(await sheetType(page) == null, 'the sheet closes after removing');
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
