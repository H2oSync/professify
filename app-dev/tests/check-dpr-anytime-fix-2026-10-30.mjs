/* Tate, 2026-10-30: a Degree Progress Report saves your classes with no section ("Anytime"), and then
   "Add to My Classes" for one of them said "That's already there." — production's saved_classes /
   my_sections have no primary key, so an upsert without onConflict was a plain INSERT. The harness now
   refuses a duplicate the same way (409 / 23505); every upsert names its unique key. */
import { openApp } from './app-harness.mjs';
let pass = 0, fail = 0; const ok = (c, m, d) => { if (c) { pass++; console.log('  ok  ', m); } else { fail++; console.log('  FAIL', m, JSON.stringify(d)); } };
const { page, close, log } = await openApp({});
await page.waitForFunction(() => TC.ready, null, { timeout: 10000 });
const pick = await page.evaluate(() => {
  const mine = new Set((TC.mine || []).map(x => x.code || x));
  const s = Object.values(SEC).find(x => x && x.code && x.id && x.rawDays && !mine.has(x.code) && !(TC.mySecs || []).some(m => m.code === x.code));
  return s ? { id: s.id, code: s.code } : null;
});
ok(!!pick, '(setup) a class with a timed section to add', pick);
/* what the report does: the class is saved with no section */
const r0 = await page.evaluate(async c => { const q = await TC.client().from('saved_classes').upsert({ user_id: TC.user.id, term: CFG.TERM, code: c }, { onConflict: 'user_id,code,term' }); await loadMine(); render(); return q.error; }, pick.code);
ok(!r0, '(setup) saved like the report saves it', r0);
const raw = await page.evaluate(async c => { const q = await TC.client().from('saved_classes').insert({ user_id: TC.user.id, term: CFG.TERM, code: c }); return q.error && q.error.code; }, pick.code);
ok(raw === '23505', '(harness) a second plain insert is refused like production (23505)', raw);
await page.evaluate(() => { A.tab('schedule'); S.schedTab = 'mine'; render(); }); await page.waitForTimeout(500);
ok(await page.evaluate(c => [...document.querySelectorAll('.any-c, [data-a="openClass"]')].some(b => (b.textContent || '').replace(/\s+/g, ' ').includes(c.split(' ')[1])), pick.code), 'it shows on My Classes with no time (Anytime)');
/* Add to My Classes: a section for the class the report saved */
const e1 = await page.evaluate(async id => await TC.addMySection(SEC[id], { hadSaved: true }), pick.id);
ok(e1 === null, 'adding a section to a class the report saved works (no "That’s already there.")', e1);
const st = await page.evaluate(id => ({ secs: (TC.mySecs || []).filter(m => String(m.class_nbr || m.id) === String(id)).length, rows: null }), pick.id);
const db = await page.evaluate(async (c) => { const q = await TC.client().from('my_sections').select('class_nbr,code').eq('user_id', TC.user.id).eq('code', c); return q.data; }, pick.code);
ok(Array.isArray(db) && db.length === 1 && String(db[0].class_nbr) === String(pick.id), 'the section is saved, once', db);
/* doing it again (status change / re-add) updates instead of failing */
const e2 = await page.evaluate(async id => await TC.addMySection(SEC[id], { status: 'waitlisted', wlPos: 3 }), pick.id);
const db2 = await page.evaluate(async (c) => { const q = await TC.client().from('my_sections').select('class_nbr,status,wl_pos').eq('user_id', TC.user.id).eq('code', c); return q.data; }, pick.code);
ok(e2 === null && db2.length === 1 && db2[0].status === 'waitlisted', 'changing it to waitlisted updates the same row', { e2, db2 });
/* the report saved twice (re-upload) doesn't fail */
const e3 = await page.evaluate(async c => { const q = await TC.client().from('saved_classes').upsert([{ user_id: TC.user.id, term: CFG.TERM, code: c }], { onConflict: 'user_id,code,term' }); return q.error; }, pick.code);
ok(!e3, 'uploading the report again doesn’t fail on classes already saved', e3);
ok(log.errors.length === 0, 'no page errors', log.errors);
await close();
console.log(`dpr-anytime-fix: ${pass} passed, ${fail} failed`);
