/* Tate, 2026-10-30: concentration spots we can't check ("Event Planning and Management elective")
   showed "?" and were left out of every count, so the concentration looked finished. Now: not taken
   by default (empty circle, counted, on "left"), "Not taken yet · I took this" → ✓ "Marked done by you
   · Undo". A concentration not chosen yet still says to choose one. */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const shot = process.argv[2];
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready, null, { timeout: 10000 });
await page.evaluate(() => { A.tab('schedule'); S.schedTab = 'past'; render(); }); await page.waitForTimeout(1500);
const unchosen = await page.evaluate(() => { plSync(); const L = TCPL.ledger(); return { un: L.concUnchosen, cant: L.grid.flatMap(t => t.slots).filter(s => s.state === 'cant').every(s => /^Concentration course$/.test(s.title)) }; });
ok(unchosen.un > 0 && unchosen.cant, 'a concentration not chosen yet: its spots still say choose one (not counted as anything)', unchosen);
await page.evaluate(() => { TC.profile.major = 'Experience & Event Management'; TC.profile.concentration = 'Event Planning and Management'; plSync(); UI.plYears = UI.plYears || {}; for (let y = 1; y <= 5; y++) UI.plYears[y] = true; render(true); });
await page.waitForTimeout(800);
const L0 = await page.evaluate(() => { const L = TCPL.ledger(), conc = L.rows.find(r => /concentration/i.test(r.label)), c = L.grid.flatMap(t => t.slots).filter(s => /Event Planning and Management elective/.test(s.title)); return { concF: conc.f, concN: conc.n, cells: c.map(s => ({ id: s.id, state: s.state })), left: L.needU.filter(n => /Event Planning and Management elective/.test(n.title)).length, cant: L.cant.length, concUn: L.concUnchosen }; });
ok(L0.cells.length === 2 && L0.cells.every(c => c.state === 'need'), 'the two “Event Planning and Management elective” spots are NOT taken (was “?”)', L0.cells);
ok(L0.concN === 6 && L0.concF === 0 && L0.left === 2 && L0.cant === 0 && L0.concUn === 0, 'they count: concentration 0 of 6 (was 0 of 4 — hidden), and both are on what’s left', L0);
const id = L0.cells[0].id, row = () => page.locator(`.pc-row:has([data-a="plMark"][data-x="${id}"])`).first();
await row().scrollIntoViewIfNeeded(); if (shot) await page.screenshot({ path: shot.replace('.png', '-before.png') });
const r0 = await row().evaluate(e => ({ cls: e.className, dot: e.querySelector('.pc-dot').innerText.trim(), txt: e.innerText.replace(/\s+/g, ' '), label: e.querySelector('.tc-mark').getAttribute('aria-label') }));
ok(/\bneed\b/.test(r0.cls) && r0.dot !== '?' && /Not taken yet · I took this/.test(r0.txt) && /^I took /.test(r0.label), 'the row: empty circle, “Not taken yet · I took this”', r0);
await page.locator(`.pc-row .pc-took[data-x="${id}"]`).first().click(); await page.waitForTimeout(700);
const r1 = await row().evaluate(e => ({ cls: e.className, dot: e.querySelector('.pc-dot').innerText.trim(), txt: e.innerText.replace(/\s+/g, ' ') }));
const L1 = await page.evaluate(() => TCPL.ledger().rows.find(r => /concentration/i.test(r.label)).f);
ok(/\bdone\b/.test(r1.cls) && r1.dot === '✓' && /Marked done by you · Undo/.test(r1.txt) && L1 === 1, 'tap “I took this”: ✓ “Marked done by you · Undo”, concentration 1 of 6', { r1, L1 });
if (shot) await page.screenshot({ path: shot.replace('.png', '-after.png') });
ok(log.writes.some(w => w.table === 'flowchart_marks' && w.m === 'POST' && w.body.slot_id === id), 'saved to the account (flowchart_marks)');
await page.locator(`.pc-row .pc-took[data-x="${id}"]`).first().click(); await page.waitForTimeout(700);
const r2 = await row().evaluate(e => ({ cls: e.className, txt: e.innerText.replace(/\s+/g, ' ') }));
ok(/\bneed\b/.test(r2.cls) && /Not taken yet/.test(r2.txt) && await page.evaluate(() => TCPL.ledger().rows.find(r => /concentration/i.test(r.label)).f) === 0, 'Undo: back to not taken', r2);
ok(log.errors.length === 0, 'no page errors', log.errors);
await close();
console.log(`unknown-slots: ${pass} passed, ${fail} failed`);
