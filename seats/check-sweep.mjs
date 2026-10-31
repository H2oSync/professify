/* TERM / SUBJECT VERIFICATION, DROPPED SECTIONS AND THE FRESHNESS ALARM — 2026-10-30.
   Fixtures are REAL rows read from course_seats on 2026-10-31 (read-only SQL), not invented ones:
   the Fall sections that were filed under Spring 2274, the MATH sections GEOG's search returned,
   PSY's cancelled sections, the Maritime CRU cruise that starts in May. No browser, no network:
   node seats/check-sweep.mjs */
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { loadCalendar, planFor } from './cadence.mjs';
import { parseDates, classesBegin, termCheck, subjectCheck, subjectOf, relabelBySubject, sweepVerdict,
  dropPlan, dropGraceMinutes, freshnessReport, freshLimitMinutes, pruneDropped } from './sweep.mjs';

let pass = 0, fail = 0;
const ok = (c, n, d = '') => { if (c) { pass++; if (process.env.VERBOSE) console.log('  ok  ', n); } else { fail++; console.log('  FAIL', n, d); } };
const HERE = fileURLToPath(new URL('.', import.meta.url));
const cal = loadCalendar();
const term = l => cal.terms.find(t => t.label === l);

/* ---- 1. dates and the calendar ---------------------------------------------------------- */
ok(JSON.stringify(parseDates('01/25/2027 - 05/14/2027')) === '{"start":"2027-01-25","end":"2027-05-14"}', 'parses one range');
ok(JSON.stringify(parseDates('01/11/2027 - 04/23/2027 03/08/2027 - 04/23/2027')) === '{"start":"2027-01-11","end":"2027-04-23"}', 'two ranges -> earliest start, latest end');
ok(parseDates('') === null && parseDates('TBA') === null, 'no date -> null');
ok(classesBegin(term('Fall 2026')) === '2026-08-24', 'Fall 2026 classes begin 2026-08-24 (calendar: "August 24 Fall 2026 Classes Begin")');
ok(classesBegin(term('Spring 2027')) === '2027-01-25', 'Spring 2027 classes begin 2027-01-25');
ok(classesBegin(term('Summer 2027')) === null, 'Summer 2027 has no add/drop window yet -> null, not a guess');

/* ---- 2. the term check ------------------------------------------------------------------- */
const SPRING = '2027-01-25', FALL = '2026-08-24';
const row = (code, dates) => ({ course_code: code, dates, class_nbr: String(Math.floor(Math.random() * 1e6)) });
/* STAT's lane at Oct 29 03:49 UTC: 64 Fall sections stamped 2274. */
const fallImpostors = Array.from({ length: 64 }, (_, i) => row('STAT ' + (2000 + i), '08/24/2026 - 12/11/2026'));
const realSpring = Array.from({ length: 120 }, (_, i) => row('STAT ' + (2000 + i), '01/25/2027 - 05/14/2027'));
ok(termCheck(fallImpostors, SPRING).verdict === 'wrong-term', 'Fall sections searched under Spring are REFUSED', termCheck(fallImpostors, SPRING).note);
ok(termCheck(realSpring, SPRING).verdict === 'ok', 'a real Spring subject passes');
ok(termCheck([row('CRU 2000', '05/05/2027 - 05/25/2027')], SPRING).verdict === 'ok', 'the Maritime cruise (May 5-25, 100 days in) is still Spring');
ok(termCheck([row('EPO 1', '01/11/2027 - 04/23/2027'), row('EPO 2', '01/11/2027 - 03/05/2027')], SPRING).verdict === 'ok', 'Maritime sessions starting Jan 11 are Spring');
ok(termCheck([row('NAU 1', '11/02/2026 - 12/11/2026'), row('NAU 2', '09/28/2026 - 10/30/2026'), row('NAU 3', '08/24/2026 - 12/11/2026')], SPRING).verdict === 'wrong-term',
  'the Fall 7.5-week and sub-session dates that leaked into 2274 are refused too');
/* Fall's real oddities: June sessions in mostly-August subjects. A minority, so kept. */
const asci = [...Array.from({ length: 6 }, (_, i) => row('ASCI 3' + i, '06/22/2026 - 07/24/2026')), ...Array.from({ length: 130 }, (_, i) => row('ASCI ' + (1000 + i), '08/24/2026 - 12/11/2026'))];
const asciV = termCheck(asci, FALL);
ok(asciV.verdict === 'ok' && asciV.foreign === 6, 'a Fall subject with a June minority passes, and says how many were odd', JSON.stringify(asciV));
ok(termCheck(realSpring, FALL).verdict === 'wrong-term', 'the reverse also holds: Spring sections searched under Fall are refused');
ok(termCheck(fallImpostors, null).verdict === 'unverifiable', 'no classes-begin date -> unverifiable, never a guess');
ok(termCheck([], SPRING).verdict === 'ok', 'an empty list is not a wrong term');
ok(termCheck([{ course_code: 'X 1', dates: 'TBA' }], SPRING).verdict === 'unverifiable', 'rows with no dates cannot be verified');
/* Measured on the live table: every one of the 678 impostors fails and no genuine Spring row does. */
ok(['08/24/2026 - 12/11/2026', '09/28/2026 - 10/30/2026', '11/02/2026 - 12/11/2026', '08/24/2026 - 09/25/2026', '08/24/2026 - 10/13/2026', '10/15/2026 - 12/11/2026', '08/24/2026 - 10/14/2026']
  .every(d => termCheck([row('X 1', d)], SPRING).verdict === 'wrong-term'), 'every Fall date shape found in 2274 is foreign to Spring');
ok(['01/25/2027 - 05/14/2027', '01/11/2027 - 04/23/2027', '03/25/2027 - 05/14/2027', '03/22/2027 - 04/23/2027', '01/25/2027 - 02/15/2027', '02/12/2027 - 03/12/2027', '05/05/2027 - 05/25/2027', '01/11/2027 - 02/10/2027', '02/23/2027 - 04/22/2027']
  .every(d => termCheck([row('X 1', d)], SPRING).verdict === 'ok'), 'every genuine Spring date shape found in 2274 passes');

/* ---- 3. the subject check ---------------------------------------------------------------- */
/* GEOG's search at 00:09 Oct 31 returned 278 MATH sections. */
const geogGotMath = Array.from({ length: 278 }, (_, i) => row('MATH ' + (1000 + i), '01/25/2027 - 05/14/2027'));
ok(subjectCheck(geogGotMath, 'GEOG').verdict === 'wrong-subject', 'GEOG returning MATH is refused', subjectCheck(geogGotMath, 'GEOG').note);
ok(subjectCheck(geogGotMath, 'MATH').verdict === 'ok', 'MATH returning MATH is fine');
const busWithStray = [...Array.from({ length: 30 }, (_, i) => row('CM ' + (1000 + i), 'x')), row('BUS 3306', 'x')];
ok(subjectCheck(busWithStray, 'CM').verdict === 'mixed', 'a stray other-subject row in a real list is "mixed", not a failure');
ok(subjectOf('MATH 1241') === 'MATH' && subjectOf('  bus 3306 ') === 'BUS' && subjectOf('') === '', 'subjectOf reads the prefix');
ok(subjectOf('CS 1000') !== subjectOf('CSC 1000'), 'CS and CSC are different subjects');
const rel = relabelBySubject([{ course_code: 'MATH 1241', subject: 'GEOG' }, { course_code: '', subject: 'GEOG' }], 'GEOG');
ok(rel[0].subject === 'MATH' && rel[1].subject === 'GEOG', 'rows are labelled by their own course code; a blank code keeps the searched subject');

/* ---- 4. the verdict: failed vs prune-safe ------------------------------------------------ */
const good = { term: { verdict: 'ok' }, subject: { verdict: 'ok' }, msgs: [''], count: 40, openOnly: 'on->off' };
ok(sweepVerdict(good).pruneSafe && !sweepVerdict(good).failed, 'a clean sweep is prune-safe');
ok(sweepVerdict({ ...good, subject: { verdict: 'mixed' } }).pruneSafe, 'a mixed list (relabelled strays) is still prune-safe');
ok(sweepVerdict({ ...good, term: { verdict: 'wrong-term', note: 'x' } }).failed, 'wrong term FAILS');
ok(sweepVerdict({ ...good, subject: { verdict: 'wrong-subject', note: 'x' } }).failed, 'wrong subject FAILS');
ok(sweepVerdict({ ...good, error: 'boom' }).failed, 'an error FAILS');
ok(sweepVerdict({ ...good, uncoverable: true }).failed, 'over the 300 cap after every split FAILS');
ok(sweepVerdict({ ...good, openOnly: 'STUCK-ON' }).failed, 'open-only stuck on FAILS');
for (const [n, o] of Object.entries({
  'unverifiable term': { term: { verdict: 'unverifiable' } }, 'open-only leak': { openOnlyLeak: true }, 'cap note': { capNote: true },
  'a need-criteria message': { msgs: ['need-criteria'] }, 'zero rows without "no results"': { count: 0, msgs: [''] },
})) { const v = sweepVerdict({ ...good, ...o }); ok(!v.pruneSafe && !v.failed, `${n}: not prune-safe, but not a failure either`, JSON.stringify(v)); }
ok(sweepVerdict({ ...good, count: 0, msgs: ['no-results'] }).pruneSafe, 'an explicit "no results" is a complete sweep');
const no = sweepVerdict({ notOffered: true });
ok(!no.failed && !no.pruneSafe, 'a subject not offered this term is neither failed nor prune-safe');

/* ---- 5. dropped sections ----------------------------------------------------------------- */
const T0 = '2026-10-31T00:00:00Z', ago = h => new Date(Date.parse(T0) - h * 3600000).toISOString();
/* PSY, Spring 2027: 63 sections seen this sweep, cancelled ones last seen Oct 5-20. */
const psySeen = Array.from({ length: 63 }, (_, i) => ({ class_nbr: String(5000 + i), course_code: 'PSY ' + (2000 + i), updated_at: T0 }));
const psyGone = [['6001', 600], ['6002', 400], ['6003', 30], ['6004', 2]].map(([n, h]) => ({ class_nbr: n, course_code: 'PSY 3350', updated_at: ago(h) }));
const g = dropGraceMinutes(20);
ok(g === 24 * 60, 'grace during registration (every 20m) is 24h');
ok(dropGraceMinutes(1440) === 3 * 1440, 'grace in a daily phase is three days');
let dp = dropPlan({ existing: [...psySeen, ...psyGone], seen: new Set(psySeen.map(r => r.class_nbr)), subject: 'PSY', sweepStartedAt: T0, graceMin: g });
ok(!dp.refused && JSON.stringify(dp.remove.sort()) === '["6001","6002","6003"]', 'prunes only sections unseen for over 24h — the one seen 2h ago survives', JSON.stringify(dp));
dp = dropPlan({ existing: [...psySeen, ...psyGone], seen: new Set([...psySeen.map(r => r.class_nbr), '6001']), subject: 'PSY', sweepStartedAt: T0, graceMin: g });
ok(!dp.remove.includes('6001'), 'a section in this sweep\'s results is never pruned, whatever its stored timestamp');
dp = dropPlan({ existing: [...psySeen, { class_nbr: '7001', course_code: 'PSYC 1', updated_at: ago(900) }, { class_nbr: '7002', course_code: 'MATH 1241', updated_at: ago(900) }], seen: new Set(psySeen.map(r => r.class_nbr)), subject: 'PSY', sweepStartedAt: T0, graceMin: g });
ok(dp.remove.length === 0, 'only rows whose course code IS this subject are considered (PSYC, MATH untouched)');
/* A sweep that "completed" with most of the subject missing is a broken sweep. */
const big = Array.from({ length: 100 }, (_, i) => ({ class_nbr: String(8000 + i), course_code: 'CSC ' + (1000 + i), updated_at: ago(48) }));
dp = dropPlan({ existing: big, seen: new Set(big.slice(0, 30).map(r => r.class_nbr)), subject: 'CSC', sweepStartedAt: T0, graceMin: g });
ok(dp.refused && dp.remove.length === 0, '70 of 100 unseen -> refused (cap 50%), nothing removed', dp.reason);
dp = dropPlan({ existing: big, seen: new Set(), subject: 'CSC', sweepStartedAt: T0, graceMin: g });
ok(dp.refused, 'a sweep that saw nothing never prunes');
const tiny = [{ class_nbr: '1', course_code: 'ECO 1', updated_at: T0 }, { class_nbr: '2', course_code: 'ECO 2', updated_at: ago(100) }, { class_nbr: '3', course_code: 'ECO 3', updated_at: ago(100) }];
dp = dropPlan({ existing: tiny, seen: new Set(['1']), subject: 'ECO', sweepStartedAt: T0, graceMin: g });
ok(!dp.refused && dp.remove.length === 2, 'a small subject can lose a couple of sections (floor of 10 under the cap)');

/* ---- 5b. pruneDropped against a fake PostgREST: exactly which requests it makes -------------- */
{
  const calls = [];
  const table = [...psySeen, ...psyGone].map(r => ({ ...r, section: 'S01-LEC Regular' }));
  const fakeFetch = async (url, opt = {}) => {
    const u = new URL(url); calls.push({ method: opt.method || 'GET', url: decodeURIComponent(u.search) });
    if ((opt.method || 'GET') === 'GET') return { ok: true, status: 200, json: async () => table.filter(r => r.course_code.startsWith(u.searchParams.get('course_code').replace(/^like\./, '').replace('*', ''))) };
    const ids = u.searchParams.get('class_nbr').replace(/^in\.\(|\)$/g, '').split(',');
    const lt = u.searchParams.get('updated_at').replace(/^lt\./, '');
    return { ok: true, status: 200, json: async () => table.filter(r => ids.includes(r.class_nbr) && r.updated_at < lt) };
  };
  const quiet = { log() {}, error() {} };
  const rep = [
    { subject: 'PSY', pruneSafe: true, seen: psySeen.map(r => r.class_nbr), reasons: [] },
    { subject: 'GEOG', pruneSafe: false, seen: [], reasons: ['wrong subject'] },
  ];
  const res = await pruneDropped(rep, { enabled: true, base: 'https://x.supabase.co/', key: 'k', term: '2274', begin: SPRING, graceMin: g, sweepStartedAt: T0, fetchImpl: fakeFetch, log: quiet });
  ok(res.removed.length === 3 && res.refused.length === 0, 'prunes PSY\'s three long-gone sections', JSON.stringify(res));
  ok(calls.length === 2 && calls[0].method === 'GET' && calls[1].method === 'DELETE', 'one read and one delete — nothing at all for the subject that was not prune-safe', JSON.stringify(calls));
  ok(/term=eq\.2274/.test(calls[1].url) && /updated_at=lt\.2026-10-30T00:00:00\.000Z/.test(calls[1].url), 'the DELETE is scoped to the term AND re-checks updated_at < (sweep start - 24h)', calls[1].url);
  ok(/course_code=like\.PSY \*/.test(calls[0].url), 'rows are read by course-code prefix "PSY *" (not the subject column, which used to be wrong)', calls[0].url);
  ok(res.skipped.length === 1 && /GEOG/.test(res.skipped[0]), 'the skipped subject is reported, with why');
  calls.length = 0;
  const off = await pruneDropped(rep, { enabled: true, base: 'https://x', key: 'k', term: '9999', begin: null, graceMin: g, sweepStartedAt: T0, fetchImpl: fakeFetch, log: quiet });
  ok(calls.length === 0 && off.removed.length === 0, 'no classes-begin date -> no request at all');
  const dis = await pruneDropped(rep, { enabled: false, base: 'https://x', key: 'k', term: '2274', begin: SPRING, graceMin: g, sweepStartedAt: T0, fetchImpl: fakeFetch, log: quiet });
  ok(calls.length === 0 && dis.removed.length === 0, 'CP_PRUNE=0 -> no request at all');
}

/* ---- 6. freshness ------------------------------------------------------------------------ */
ok(freshLimitMinutes(20) === 120 && freshLimitMinutes(60) === 180 && freshLimitMinutes(180) === 420 && freshLimitMinutes(1440) === 2940, 'limits: 2h / 3h / 7h / 49h');
const NOW = new Date('2026-10-31T01:00:00Z');                       // Oct 30 18:00 PT: Spring appointments, Fall dark
const plan = planFor(NOW, cal);
const ph = c => plan.terms.find(t => t.term_code === c);
ok(ph('2268').phase === 'dark' && ph('2274').phase === 'appointments', 'on Oct 30 Fall is dark and Spring is in appointments (fixture sanity)');
const minsAgo = m => new Date(NOW.getTime() - m * 60000).toISOString();
const fresh = [...Array.from({ length: 50 }, (_, i) => ({ course_code: 'MATH ' + i, updated_at: minsAgo(20) })), ...Array.from({ length: 20 }, (_, i) => ({ course_code: 'PSY ' + i, updated_at: minsAgo(30) }))];
const fallOld = [{ course_code: 'BUS 1', updated_at: '2026-10-29T05:30:34Z' }, { course_code: 'BUS 2', updated_at: '2026-08-04T16:18:10Z' }];
const begins = { '2268': FALL, '2274': SPRING };
let fr = freshnessReport(plan.terms, { '2268': fallOld, '2274': fresh }, NOW, begins);
ok(fr.problems.length === 0, 'fresh Spring + months-old Fall (dark) -> no problem: a finished term never cries wolf', JSON.stringify(fr.problems));
fr = freshnessReport(plan.terms, { '2274': fresh.map(r => ({ ...r, updated_at: minsAgo(200) })) }, NOW, begins);
ok(fr.problems.length === 1 && /newest row is 3h old/.test(fr.problems[0]), 'Spring with no row under 2h old -> "sweeps are not landing"', JSON.stringify(fr.problems));
fr = freshnessReport(plan.terms, { '2274': [...fresh, { course_code: 'GEOG 1150', updated_at: minsAgo(300) }] }, NOW, begins);
ok(fr.problems.length === 1 && /GEOG 5h/.test(fr.problems[0]), 'one subject behind -> named, with its age', JSON.stringify(fr.problems));
fr = freshnessReport(plan.terms, { '2274': [...fresh, { course_code: 'MATH 9999', updated_at: '2026-10-05T22:14:35Z' }] }, NOW, begins);
ok(fr.problems.length === 1 && /unseen for over/.test(fr.problems[0]), 'a fresh subject still holding a row unseen for weeks -> pruning is not keeping up', JSON.stringify(fr.problems));
fr = freshnessReport(plan.terms, { '2274': [...fresh, { course_code: 'MATH 9999', updated_at: '2026-10-05T22:14:35Z' }] }, NOW, {});
ok(fr.problems.length === 0 && fr.warnings.length === 1, '…but only a warning where the term has no begin date (pruning is off there)');
fr = freshnessReport(plan.terms, { '2274': [...fresh, { course_code: 'MATH 9999', updated_at: minsAgo(25 * 60) }] }, NOW, begins);
ok(fr.problems.length === 0, 'a dropped section inside its grace (25h) is not an alarm yet');
fr = freshnessReport(plan.terms, { '2274': [] }, NOW, begins);
ok(fr.problems.length === 1 && /NO rows/.test(fr.problems[0]), 'a live term with no rows at all is a problem');

/* ---- 7. the CLIs, offline ---------------------------------------------------------------- */
const dir = mkdtempSync(join(tmpdir(), 'sweep-'));
const runCli = (args, env) => { try { return { code: 0, out: execFileSync('node', args, { cwd: HERE, env: { ...process.env, ...env }, encoding: 'utf8' }) }; } catch (e) { return { code: e.status, out: String(e.stdout) + String(e.stderr) }; } };
writeFileSync(join(dir, 'fresh.json'), JSON.stringify({ '2274': fresh }));
writeFileSync(join(dir, 'stale.json'), JSON.stringify({ '2274': [...fresh, { course_code: 'GEOG 1150', updated_at: minsAgo(300) }] }));
let c = runCli(['freshness.mjs', '--at', NOW.toISOString()], { CP_FRESHNESS_ROWS: join(dir, 'fresh.json'), GITHUB_STEP_SUMMARY: '' });
ok(c.code === 0, 'freshness.mjs exits 0 when Spring is fresh and only Fall (dark) is old', c.out);
c = runCli(['freshness.mjs', '--at', NOW.toISOString()], { CP_FRESHNESS_ROWS: join(dir, 'stale.json'), GITHUB_STEP_SUMMARY: '' });
ok(c.code === 1 && /::error title=Seat data is stale::.*GEOG/.test(c.out), 'freshness.mjs exits 1 with an ::error naming the stale subject', c.out);
/* The alarm slot: one firing per 3-hour Pacific block. 01:05Z = 18:05 PT (block start at 18:00). */
const outFile = t => { const f = join(dir, 'out-' + t.replace(/\W/g, '')); writeFileSync(f, ''); runCli(['plan.mjs', '--at', t], { GITHUB_OUTPUT: f, GITHUB_STEP_SUMMARY: '', CP_LAST_PULLS: '{}' }); return readFileSync(f, 'utf8'); };
ok(/freshness_check=true/.test(outFile('2026-10-31T01:05:00Z')), 'plan.mjs: 18:05 PT is a freshness slot');
ok(/freshness_check=false/.test(outFile('2026-10-31T01:15:00Z')), 'plan.mjs: 18:15 PT is not');
let slots = 0;
for (let m = 0; m < 1440; m += 10) slots += /freshness_check=true/.test(outFile(new Date(Date.parse('2026-10-30T07:00:00Z') + m * 60000).toISOString())) ? 1 : 0;
ok(slots === 8, 'exactly 8 freshness slots in a day of 10-minute runs', slots);

/* ---- 8. the scraper is wired the way the rules above assume -------------------------------- */
const src = readFileSync(join(HERE, 'scrape-seats.mjs'), 'utf8');
const before = (a, b, from = 0) => { const i = src.indexOf(a, from), j = src.indexOf(b, i); return i > -1 && j > i; };
ok(before("checkBand(subj, r, 'all');", 'await enrichLive(r.list, subj);'), 'the whole-subject band is checked BEFORE a detail page is opened');
ok(before('checkBand(subj, loRes, lo.label);', 'await enrichLive(loRes.list'), 'the low band is checked before enrichment');
ok(before('checkBand(subj, highHalf,', 'await enrichLive(highHalf.list'), 'the high band is checked before enrichment');
ok(/if \(!subjectSet\) throw new Mismatch/.test(src), 'a subject that will not set stops the search instead of searching the previous subject');
ok(before('relabelBySubject(list, subj);', 'all.push(...list);'), 'rows are relabelled by course code before they are queued for the upsert');
ok(before('await upsertSupabase(all);', 'await pruneDropped(report'), 'pruning runs only after the upsert succeeded');
ok(/enabled: CFG\.PRUNE && /.test(src), 'the scraper passes CP_PRUNE through to pruneDropped');

ok(/process\.exit\(3\)/.test(src) && /CFG\.FAIL_ON_INCOMPLETE/.test(src), 'a failed subject makes the lane exit 3 (switchable)');
const wf = readFileSync(join(HERE, '..', '.github', 'workflows', 'update-seats.yml'), 'utf8');
ok(/freshness:\s*\n\s*needs: plan/.test(wf) && /node freshness\.mjs/.test(wf), 'the workflow has the freshness job');
ok(/seats\/sweep-report\.json/.test(wf), 'the per-subject sweep report is uploaded with the diagnostics');

console.log(`check-sweep: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
