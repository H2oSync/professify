/* A class_history row of the term you're in is "being taken" until THAT term's last day — Spring 2027's own (May 25),
   not Fall's (Dec 22). Fails on 1658ca4: from Jan 25 2027 every Spring 2027 row counted as finished (prereqs met). */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
import { ok, liveTables, FX, done, nextPort } from './lib.mjs';

const T = liveTables();
T.class_history = (T.class_history || []).concat([
  { user_id: FX.ME.id, code: 'ZZFALL 1001', term: 'Fall', year: 2026, professor: null },
  { user_id: FX.ME.id, code: 'ZZSPR 1002', term: 'Spring', year: 2027, professor: null }]);
const cases = [
  ['2026-11-10T12:00:00-08:00', true, true, 'Nov 10 (Fall on)'],
  ['2026-12-23T12:00:00-08:00', false, true, 'Dec 23 (Fall over, Spring ahead)'],
  ['2027-01-26T12:00:00-08:00', false, true, 'Jan 26 (Spring’s second day)'],
  ['2027-03-22T12:00:00-07:00', false, true, 'Mar 22 (mid-Spring)'],
  ['2027-05-21T12:00:00-07:00', false, true, 'May 21 (Spring’s last final)'],
  ['2027-05-25T12:00:00-07:00', false, true, 'May 25 (Spring’s end of term)'],
  ['2027-05-26T12:00:00-07:00', false, false, 'May 26 (Spring over)'],
];
for (const [time, fall, spring, name] of cases) {
  const { page, close, log } = await openApp({ terms: 'live', tables: T, time, port: nextPort() });
  await page.waitForFunction(() => TC.ready, null, { timeout: 10000 }).catch(() => {});
  const r = await page.evaluate(() => { const h = c => (TC.myHistory || []).find(x => x.code === c); const tk = takingCodes();
    return { now: nowTerm().label, fall: histNotDone(h('ZZFALL 1001')), spring: histNotDone(h('ZZSPR 1002')), springTaking: tk.has('ZZSPR 1002'), springDone: histDone().some(x => x.code === 'ZZSPR 1002') }; });
  ok(r.fall === fall && r.spring === spring && r.springTaking === spring && r.springDone === !spring,
    `${name}: Fall 2026 row ${fall ? 'in progress' : 'finished'}, Spring 2027 row ${spring ? 'in progress (not a prerequisite met)' : 'finished'}`, r);
  ok(!log.errors.length, `${name}: no page errors`, log.errors);
  await close();
}
/* a term with no known last day stays on — never "finished" by a guess */
{ const { page, close } = await openApp({ terms: 'live', tables: T, time: '2027-03-22T12:00:00-07:00', port: nextPort(), init: () => { window.PROFESSIFY_CONFIG = { TERM_END_DATES: {} }; } });
  await page.waitForFunction(() => TC.ready, null, { timeout: 10000 }).catch(() => {});
  const on = await page.evaluate(() => nowTermOn());
  ok(on === true, 'no last day known for the term you’re in: it is still on (TERM_ENDS is last term’s and doesn’t apply)', on);
  await close(); }
done('check-hist-term-end');
