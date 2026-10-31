/* Days with no classes: Veterans Day, winter break (after Fall's last day, before Spring starts), Spring break, finals,
   summer break. A friend's ring is grey and says what the day is, never "In BUS 3438 till 11:00". Fails on 1658ca4. */
import { openApp } from '/home/claude/tc/app-icon/app-dev/tests/app-harness.mjs';
import { ok, tick, liveTables, done, nextPort } from './lib.mjs';

const cases = [
  ['2026-11-10', '-08:00', null, 'a normal Tuesday in Fall'],
  ['2026-11-11', '-08:00', 'Veterans Day', 'Veterans Day'],
  ['2026-11-24', '-08:00', 'Thanksgiving break', 'Thanksgiving week (Fall Break, Nov 23-29)'],
  ['2026-12-10', '-08:00', null, 'Fall’s second-to-last day of classes'],
  ['2026-12-15', '-08:00', 'Finals week', 'Fall finals (Dec 12, 14-18)'],
  ['2026-12-21', '-08:00', 'Winter break', 'faculty workday after finals (Dec 21)'],
  ['2026-12-23', '-08:00', 'Winter break', 'the day after Fall’s last day (Dec 22)'],
  ['2027-01-05', '-08:00', 'Winter break', 'January, before Spring starts'],
  ['2027-01-26', '-08:00', null, 'Spring’s second day'],
  ['2027-02-15', '-08:00', 'Presidents’ Day', 'Presidents’ Day'],
  ['2027-03-16', '-07:00', 'Spring break', 'Spring break'],
  ['2027-03-31', '-07:00', 'César Chávez Day', 'César Chávez Day (Farmworkers Day)'],
  ['2027-05-18', '-07:00', 'Finals week', 'Spring finals'],
  ['2027-05-25', '-07:00', 'Summer break', 'after Spring’s last final'],
];
for (const [date, off, want, name] of cases) {
  const { page, close, log } = await openApp({ terms: 'live', tables: liveTables(), time: `${date}T06:00:00${off}`, port: nextPort() });
  await page.waitForFunction(() => TC.ready, null, { timeout: 10000 }).catch(() => {});
  /* a friend with a class on this weekday, and that class's start */
  const pick = await page.evaluate(() => { for (const f of TC.friends) { const s = nowSecs(f).find(x => !x.async && x.s != null && x.e != null && x.days.includes(CLOCK.day)); if (s) return { f, s: s.s, code: s.code }; } return null; });
  if (!pick) { ok(false, `${name}: a fixture friend has a class on this weekday`, date); await close(); continue; }
  const hh = String(Math.floor((pick.s + 5) / 60)).padStart(2, '0'), mm = String((pick.s + 5) % 60).padStart(2, '0');
  await page.clock.setSystemTime(new Date(`${date}T${hh}:${mm}:00${off}`)); await page.clock.runFor(61000); await page.evaluate(() => render(true)); await tick(page, 300);
  const r = await page.evaluate(f => { const st = status(f); return { t: st.t, free: st.free, rc: st.rc || st.c, today: todaySecs(f).length, story: (() => { const b = [...document.querySelectorAll('.stories .story')].find(x => x.dataset.x === f); return b ? b.querySelector('.ring').getAttribute('style') : null; })() }; }, pick.f);
  if (!want) ok(/^In /.test(r.t) && r.today > 0, `${name} (${date}): friends in class still read “In ${pick.code} …”`, r);
  else ok(r.t === want && r.free === null && r.today === 0 && /#CBD5E1|#3A4660/i.test(r.rc || '') && /#CBD5E1|#3A4660/i.test(r.story || ''), `${name} (${date}): “${want}”, grey ring, no class today — not “In ${pick.code} till …”`, r);
  ok(!log.errors.length, `${name}: no page errors`, log.errors);
  await close();
}
done('check-no-class-days');
