/* Fix 4: dead section ids in a plan — Clear them; they don't count toward the 12 limit. */
import { openApp, mk, tap, toastText, sheetText } from './tlib.mjs';
const R = mk('t4-plan-dead'); const port = +(process.env.APP_PORT || 8656);
const { page, close, log } = await openApp({ port, time: null });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.plansLoaded !== false, null, { timeout: 15000 }); await page.waitForTimeout(600);
await page.evaluate(() => { A.tab('schedule'); A.schedTab('plans'); A.pickPlan('B'); }); await page.waitForTimeout(400);
const b0 = await page.evaluate(() => ({ ids: TC.plans.B.slice(), dead: TC.plans.B.filter(x => !SEC[x]), line: (document.querySelector('#scroll .plan-dead') || {}).textContent || '' }));
R.ok(b0.dead.length >= 1, '(setup) Plan B has a section that left the list', b0);
R.ok(await tap(page, '#scroll [data-a="planClearDead"]', 'Clear', { wait: 500 }), 'the “no longer in the list” line has Clear', b0.line);
const b1 = await page.evaluate(() => ({ ids: TC.plans.B.slice(), line: !!document.querySelector('#scroll .plan-dead') }));
R.ok(b1.ids.length === b0.ids.length - b0.dead.length && b1.ids.every(x => b0.ids.includes(x)) && !b1.ids.some(x => b0.dead.includes(x)) && !b1.line, 'Clear drops only the dead ids, and the line goes', { b0, b1 });
R.ok(/Cleared 1 unlisted section from Plan B/.test(await toastText(page)), 'toast with Undo', await toastText(page));
await tap(page, '#toast .tundo', null, { wait: 300 });
R.ok(JSON.stringify(await page.evaluate(() => TC.plans.B)) === JSON.stringify(b0.ids), 'Undo puts them back');
/* before the seat list loads, nothing looks dead (Clear must never empty a plan) */
R.ok(await page.evaluate(() => { const k = TC.seatsLoaded; TC.seatsLoaded = false; const n = planMissing('B'); A.planClearDead('B'); TC.seatsLoaded = k; return n === 0 && TC.plans.B.length > 0; }), 'with the seat list not loaded: no dead count, Clear does nothing');
/* 9 real + 3 dead: a 10th real section can still go in */
const fill = await page.evaluate(() => { const all = Object.values(SEC); const nx = all[all.length - 1]; const ids = all.filter(s => s.code !== nx.code).slice(0, 9).map(s => s.id); TC.setPlan('C', ids.concat(['79996', '79997', '79998'])); return { next: nx.id }; });
await page.evaluate(id => { openAddTo(id); A.atGroup('plans'); A.atPick('C'); }, fill.next); await page.waitForTimeout(400);
const t = await sheetText(page);
R.ok(!/already has 12 sections/.test(t) && !/is full/.test(t), 'Plan C with 9 listed + 3 dead ids is not “full”', t.match(/Plan C[^.]*\./g));
await page.evaluate(() => A.closeSheet());
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
