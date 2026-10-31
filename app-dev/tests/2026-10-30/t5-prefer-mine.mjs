/* Fix 5: a section in both My Classes and a plan opens Add to your week on My Classes. */
import { openApp, mk } from './tlib.mjs';
const R = mk('t5-prefer-mine'); const port = +(process.env.APP_PORT || 8657);
const { page, close, log } = await openApp({ port, time: null });
await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.mineRows, null, { timeout: 15000 }); await page.waitForTimeout(400);
const id = await page.evaluate(() => { const s = personSecs('me').find(x => SEC[x.id]); TC.setPlan('A', (TC.plans.A || []).filter(x => x !== s.id).concat(s.id)); return s.id; });
await page.evaluate(id => openAddTo(id), id); await page.waitForTimeout(300);
const d = await page.evaluate(() => ({ dest: UI.sheet.dest, rm: (document.querySelector('#sheet .at-rm') || {}).textContent }));
R.ok(d.dest === 'mine' && /Remove from My Classes/.test(d.rm || ''), 'in both: it opens on My Classes', d);
await page.evaluate(() => A.closeSheet());
const p = await page.evaluate(() => { const s = Object.values(SEC).find(x => !personSecs('me').some(m => m.id === x.id)); TC.setPlan('B', [s.id]); openAddTo(s.id); return UI.sheet.dest; });
R.ok(p === 'B', 'only in a plan: it still opens on that plan', p);
R.ok(log.errors.length === 0, 'no page errors', log.errors);
await close(); R.end();
