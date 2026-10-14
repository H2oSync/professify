/* check-desktop-report — the Degree Progress Report on the website, at the phone's level (website-report-flow, Tate
   2026-10-14: "catch the website up to the level the app is"; Round 1 registration opens Oct 19). Runs the REAL
   index.html in Chromium, signed in, against the PostgREST stand-in (app-harness.mjs), with real report PDFs
   (files/dpr-*.pdf, and a quarter-catalog one from the synthetic corpus).
   Run: APP_DIR=<repo> node check-desktop-report.mjs [--only name] [--quiet]   (APP_PORT to move off 8203; DPR_SYNTH for the corpus)
   The promises:
   - read: the review list says what was read (N filled · M left, the catalog and printed date, every line); the save
     keeps the report's verdicts on the account (degree_audit, upsert on user_id) — never a grade, EMPLID or name — and
     sends a flagged line de-identified; Past classes is laid out by the report's requirements, each naming the class
     and term it used; a quarter catalog never sees the 2026–28 flowchart.
   - semester: a semester catalog does.
   - wins: the report wins — what's on the account and not on the report comes off (unless unchecked), "already" is the
     same class in the same term, this term's classes only when the report shows this term, never the Spring list.
   - diff: a new report over an old one shows what changed and the Plans it touches; "Take it out" takes it out; your
     marks done survive the new upload.
   - inProgress: a record row of the term you're in is a class being taken until the term ends.
   - local / oldAudit / conc / marks: the device fallback, an old saved audit, concentrations' real shape, flowchart marks. */
import { openApp } from './app-harness.mjs';
import * as FX from './app-fixtures.mjs';
import fs from 'node:fs'; import path from 'node:path';

const args = process.argv.slice(2);
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const QUIET = args.includes('--quiet');
const SHOTS = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
let pass = 0, fail = 0; const fails = [];
function ok(c, name, info) {
  if (c) { pass++; if (!QUIET) console.log('  ok  ', name); }
  else { fail++; fails.push(name); console.log('  FAIL', name, info !== undefined ? '→ ' + JSON.stringify(info).slice(0, 500) : ''); }
}
const PORT = +(process.env.APP_PORT || 8203);
const tick = async (p, ms = 400) => { await p.clock.runFor(ms); await p.waitForTimeout(250); };
/* wait for a fact, not for a time: under load the account's reads land late, and a fixed 1.5-2.5s pass was the flake in read/wins */
const until = async (p, fn, arg, max = 60) => { for (let i = 0; i < max; i++) { if (await p.evaluate(fn, arg).catch(() => false)) return true; await tick(p, 250); } return false; };
const loaded = (p, needHistory) => until(p, (h) => { try { return !!sbUser && (!h || ((myHistory || []).some(x => x.code === h) && nowMine().classes.length > 0)); } catch (e) { return false; } }, needHistory || null);
const desk = (o = {}) => openApp(Object.assign({ path: '/', width: 1440, height: 900, wait: 4000, port: PORT }, o));
/* a profile with a major (Business Administration, the fixture account's) on this device, as after a sign-in */
const BA = `try{ localStorage.setItem('professify-profile', JSON.stringify({ major: 'Business Administration' })); }catch(e){}`;
const T = {};
const test = (name, fn) => { T[name] = fn; };
const SYN = process.env.DPR_SYNTH || '/tmp/claude-0/dpr-synth';
const SPRING_CFG = { TERM: '2274', TERM_LABEL: 'Spring 2027', NOW_TERM: '2268', NOW_LABEL: 'Fall 2026', NOW_UNTIL: '2027-01-25', TERM_ENDS: '2026-12-22' };
const ME = FX.ME.id;
const rows = (log, table, m) => log.writes.filter(w => w.table === table && (!m || w.m === m)).flatMap(w => Array.isArray(w.body) ? w.body : [w.body]).filter(Boolean);
const dq = w => decodeURIComponent(String(w.query || '')).replace(/\+/g, ' ');
/* a quarter-catalog report from the synthetic corpus, printed in 2026 */
function quarterReport() {
  const ids = fs.existsSync(SYN) ? fs.readdirSync(SYN).filter(f => /^synth-\d+\.key\.json$/.test(f)).sort() : [];
  for (const f of ids) { const K = JSON.parse(fs.readFileSync(path.join(SYN, f), 'utf8'));
    if (/Quarter/.test(K.catalog || '') && (!K.clock || (K.clock.nowy === 2026 && !K.clock.jan)) && Object.values(K.lines).some(l => l.used.length && l.used.some(e => e.n && e.n !== e.c)) && !K.read.unknown) return { pdf: path.join(SYN, f.replace('.key.json', '.pdf')), K }; }
  return null;
}
function fresh(extra) {
  const t = JSON.parse(JSON.stringify(FX.TABLES));
  for (const k of ['class_history', 'saved_classes', 'my_sections', 'plans', 'class_waivers']) t[k] = (t[k] || []).filter(r => r.user_id !== ME);
  return Object.assign(t, extra || {});
}
async function upload(page, file) {
  await page.locator('#transcriptFile').setInputFiles(file);
  for (let i = 0; i < 80 && !(await page.locator('#tiModal .ti-row').count()); i++) await tick(page, 500);
  await tick(page, 300);
}
async function save(page, log) {
  await page.evaluate(() => [...document.querySelectorAll('#tiModal button')].find(b => /^Add \d+ to Past Classes/.test(b.innerText.trim())).click());
  for (let i = 0; i < 30 && !log.writes.some(w => w.table === 'degree_audit' || w.table === 'class_history'); i++) await tick(page, 400);
  await tick(page, 1500);
}
async function openPast(page) {
  await page.evaluate(() => { try { rsClose(); } catch (e) {} show('sched'); setSchedTab('plan'); const w = document.getElementById('schedPlanWrap'); if (w) w.classList.remove('pl3-deg-closed'); plRenderRecord(); });
  await tick(page, 600);
}
async function shot(page, sel, name) {
  if (!SHOTS) return;
  await page.evaluate(s => { const e = document.querySelector(s); if (e) e.scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); }, sel);
  await page.screenshot({ path: path.join(SHOTS, name + '.png') });
}
const PII = /\d{7,}|EMPLID|\bName\s*:|(?:^|\s)(?:[A-DF][+-]?|CR|NC|W)\s+\d+\.\d{2}\b/;
const REQ_KEYS = ['label', 'status', 'kind', 'ge', 'level', 'code', 'units', 'courses', 'options', 'oneOf', 'used', 'listed'];
const ROW_KEYS = ['user_id', 'printed_on', 'catalog', 'major', 'concentration', 'units_used', 'units_needed', 'requirements', 'read_at', 'overrides'];

test('read', async () => {
  const Q = quarterReport(); if (!Q) { ok(false, 'read: a quarter-catalog report in the corpus', SYN); return; }
  const { K } = Q;
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: fresh(), time: '2026-10-09T10:30:00-07:00', init: BA }); await tick(page, 500); ok(await loaded(page), 'read: the account has signed in before the report goes in');
  await upload(page, Q.pdf);
  const r = await page.evaluate(() => ({ cnt: (document.getElementById('rfCnt') || {}).textContent || '', cat: ((document.querySelector('#tiModal .rf-cat') || {}).textContent || ''),
    lines: document.querySelectorAll('#tiModal .rf-cl').length, reqs: _dprMeta.audit.reqs.length, printed: _dprMeta.audit.printed }));
  const want = `${K.read.filled} filled · ${K.read.left} left`;
  ok(r.cnt === want, 'read: the review list counts the report the way the phone does', { got: r.cnt, want });
  const pd = new Date(r.printed + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  ok(r.cat === `Your catalog: ${K.catalog} · report printed ${pd}`, 'read: your catalog and the day the report was printed', r.cat);
  ok(r.lines === r.reqs && r.lines > 10, 'read: “Check what was read” lists every line the reader found', r);
  /* flag the first line read as wrong: left out of the counts and of the save, sent de-identified */
  const flagLabel = await page.evaluate(() => { document.querySelector('#tiModal .rf-check').open = true; const b = document.querySelector('#tiModal .rf-flag'); b.click(); return _dprMeta.audit.reqs[0].label; });
  await tick(page, 200);
  const r2 = await page.evaluate(() => ({ struck: document.querySelectorAll('#tiModal .rf-cl.flagged').length, open: document.querySelector('#tiModal .rf-check').open }));
  ok(r2.struck === 1 && r2.open, 'read: a flagged line is struck through and the list stays open', r2);
  log.writes.length = 0;
  await save(page, log);
  const aw = log.writes.filter(w => w.table === 'degree_audit');
  const body = aw.length ? (Array.isArray(aw[0].body) ? aw[0].body[0] : aw[0].body) : null;
  ok(aw.length === 1 && aw[0].m === 'POST' && /on_conflict=user_id/.test(aw[0].query || ''), 'read: the verdicts are kept on the account — one upsert on user_id', aw.map(w => w.m + ' ' + w.query));
  const txt = JSON.stringify(Object.assign({}, body || {}, { user_id: null }));   /* the account's own id is a uuid, not an EMPLID */
  const keysOk = body && Object.keys(body).every(k => ROW_KEYS.includes(k)) && body.requirements.every(b => Object.keys(b).every(k => REQ_KEYS.includes(k)) && (b.used || []).every(e => Object.keys(e).every(k => ['c', 't', 'n', 'x', 'p'].includes(k))));
  ok(body && body.user_id === ME && body.catalog === K.catalog && body.requirements.length === r.reqs - 1 && !body.requirements.some(b => b.label === flagLabel) && keysOk,
    'read: what is kept is the line’s words, verdict, counts and classes (code and term) — the flagged line left out', { n: body && body.requirements.length, keysOk, keys: body && Object.keys(body) });
  const leak = K.secret.filter(x => txt.includes(x));
  ok(!leak.length && !PII.test(txt), 'read: no name, EMPLID or grade reaches the account', { leak, m: PII.exec(txt) });
  const fl = rows(log, 'dpr_flags', 'POST');
  ok(fl.length === 1 && fl[0].label === flagLabel && !('user_id' in fl[0]) && !PII.test(JSON.stringify(fl[0])), 'read: the flagged line is sent de-identified (its words and verdict)', fl);
  const ls = await page.evaluate(id => { try { return JSON.parse(localStorage.getItem('tc-audit:' + id)); } catch (e) { return null; } }, ME);
  ok(ls && ls.requirements && !ls.pending && !PII.test(JSON.stringify(Object.assign({}, ls, { user_id: null }))), 'read: this device keeps the same copy, sent (not pending)', ls && Object.keys(ls));
  /* Past classes by requirement */
  await openPast(page);
  const P = await page.evaluate(() => { const h = document.getElementById('plRecordHead');
    return { top: !!h.querySelector('.rf-top'), sum: (h.querySelector('.rf-sum') || {}).textContent || '', groups: [...h.querySelectorAll('.rf-grp > summary span')].map(e => e.textContent),
      still: h.querySelectorAll('.rf-still > .rf-row').length, used: [...h.querySelectorAll('.rf-used')].map(e => e.textContent), flow: /Your flowchart/.test(h.textContent), cat: (h.querySelector('.rf-catc') || {}).textContent || '' }; });
  ok(P.top && P.groups.includes('Major and support') && P.groups.includes('General education') && P.groups.includes('Degree requirements'), 'past: laid out by the report’s requirements — Major and support · General education · Degree requirements', P.groups);
  const L1 = Object.values(K.lines).find(l => l.used.some(e => e.n && e.n !== e.c)), e1 = L1.used.find(e => e.n && e.n !== e.c);
  const wantUsed = `${e1.c} → ${e1.n} · ${e1.t}`;
  ok(P.used.includes(wantUsed), 'past: each line names the class the report used and its term (“HNRS 102 → HNRS 1102 · Fall 2023”)', { want: wantUsed, some: P.used.slice(0, 6) });
  ok(P.still === K.read.left - 1 + 0 || P.still === K.read.left, 'past: Still needed lists the open lines', { still: P.still, left: K.read.left });
  ok(!P.flow && /Quarter/.test(P.cat), 'past: a quarter catalog never sees the 2026–28 flowchart', P);
  await shot(page, '#plRecord', 'past-quarter');
  ok(log.errors.length === 0, 'read: no page errors', log.errors);
  await close();
});

test('semester', async () => {
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: fresh(), time: '2026-11-04T10:30:00-08:00', init: BA }); await tick(page, 1500);
  await upload(page, 'files/dpr-transfer-continuing.pdf');
  await save(page, log);
  await openPast(page);
  const P = await page.evaluate(() => { const h = document.getElementById('plRecordHead'); return { flow: [...h.querySelectorAll('.rf-grp > summary')].map(e => e.textContent).filter(t => /Your flowchart/.test(t)), cat: (h.querySelector('.rf-catc') || {}).textContent, xfer: [...h.querySelectorAll('.rf-used')].map(e => e.textContent).filter(t => /transfer credit$/.test(t)), now: [...h.querySelectorAll('.rf-used')].map(e => e.textContent).filter(t => /this term$/.test(t)) }; });
  ok(P.flow.length === 1 && /2026–28/.test(P.flow[0]) && /Semester/.test(P.cat), 'semester: a semester catalog sees its 2026–28 flowchart, folded', P);
  ok(P.xfer.includes('ENGL 1134 · Fall 2025 · transfer credit') && P.now.includes('BUS 3431 · Fall 2026 · this term'), 'semester: a line names transfer credit and this term’s class as such', P);
  await shot(page, '#plRecord', 'past-semester');
  ok(log.errors.length === 0, 'semester: no page errors', log.errors);
  await close();
});

test('wins', async () => {
  const t = fresh();
  t.class_history.push(
    { user_id: ME, code: 'PHIL 3331', term: 'Spring', year: 2026, professor: 'Dov Mockridge' },   // not on the report: comes off
    { user_id: ME, code: 'HIST 1111', term: 'Fall', year: 2025, professor: null },                // not on the report: unchecked, stays
    { user_id: ME, code: 'BUS 2207', term: 'Fall', year: 2025, professor: null },                 // same class, same term: already
    { user_id: ME, code: 'BUS 3346', term: 'Fall', year: 2024, professor: null });                // the report has it Spring 2026
  t.saved_classes = FX.TABLES.saved_classes.slice().concat([{ user_id: ME, term: '2274', code: 'BUS 4488', class_nbr: null, created_at: '2026-10-20T00:00:00Z', waitlist_pos: null }]);
  const fallMine = FX.TABLES.saved_classes.filter(r => r.user_id === ME && r.term === '2268').map(r => r.code);
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: t, time: '2026-11-04T10:30:00-08:00' }); await tick(page, 500); ok(await loaded(page, 'PHIL 3331'), 'wins: the account’s classes and record have loaded before the report goes in');
  await upload(page, 'files/dpr-transfer-continuing.pdf');
  const r = await page.evaluate(() => ({ rc: (_dprMeta.rc || []).map(x => x.code + '|' + x.kind + '|' + x.why), card: [...document.querySelectorAll('#tiModal .rf-rcr')].map(e => e.innerText.replace(/\s+/g, ' ').trim()),
    already: tiRows.filter(x => x.already).map(x => x.cur + '|' + x.term + ' ' + x.year), pick3346: tiRows.filter(x => x.cur === 'BUS 3346').map(x => x.pick) }));
  const wantNow = fallMine.filter(c => !['BUS 3431', 'BUS 3438', 'BUS 4401'].includes(c)).sort();
  const gotNow = r.rc.filter(x => /\|now\|/.test(x)).map(x => x.split('|')[0]).sort();
  ok(JSON.stringify(gotNow) === JSON.stringify(wantNow), 'wins: this term’s classes the report doesn’t show are listed — never the Spring list', { gotNow, wantNow });
  ok(r.rc.some(x => /^PHIL 3331\|hist\|On your account as Spring 2026 · not on your report$/.test(x)) && r.rc.some(x => /^BUS 3346\|hist\|On your account as Fall 2024 · your report has it Spring 2026$/.test(x)) && r.rc.some(x => /^HIST 1111\|hist/.test(x)) && !r.rc.some(x => /^BUS 2207/.test(x)),
    'wins: record rows not on the report are listed with why; the same class in the same term is not', r.rc);
  ok(r.already.includes('BUS 2207|Fall 2025') && JSON.stringify(r.pick3346) === '[true]', '“already on your record” is the same class in the same term — BUS 3346 in another term is saved again', r);
  ok(r.card.length === r.rc.length && r.card.every(Boolean), 'wins: each is a checked row in the review list', r.card);
  await page.evaluate(() => { const lab = [...document.querySelectorAll('#tiModal .rf-rcr')].find(e => /HIST 1111/.test(e.innerText)); lab.querySelector('input').click(); });
  log.writes.length = 0;
  await save(page, log);
  const dels = log.writes.filter(w => w.m === 'DELETE').map(w => w.table + ' ' + dq(w));
  ok(dels.some(d => /^class_history .*code=eq\.PHIL 3331&term=eq\.Spring&year=eq\.2026/.test(d)) && dels.some(d => /^class_history .*code=eq\.BUS 3346&term=eq\.Fall&year=eq\.2024/.test(d)),
    'wins: the checked record rows come off, by class, term and year', dels);
  ok(!dels.some(d => /HIST 1111/.test(d)), 'wins: the unchecked one stays', dels);
  ok(wantNow.every(c => dels.some(d => d.startsWith('saved_classes ') && d.includes('term=eq.2268') && d.includes('code=eq.' + c)) && dels.some(d => d.startsWith('my_sections ') && d.includes('term=eq.2268') && d.includes('code=eq.' + c))) && !dels.some(d => /2274/.test(d)) && dels.every(d => /user_id=eq\./.test(d)),
    'wins: this term’s ones come off this term only (saved_classes and my_sections at 2268), yours only', dels);
  const hi = rows(log, 'class_history', 'POST').map(x => x.code + '|' + x.term + ' ' + x.year);
  ok(hi.includes('BUS 3346|Spring 2026') && !hi.includes('BUS 2207|Fall 2025'), 'wins: the report’s term is saved; the same-term row isn’t written again', hi);
  const st = await page.evaluate(() => ({ now: NOW_MINE.classes.slice(), spring: myClasses.slice(), toast: (document.getElementById('frToast') || {}).textContent || '' }));
  ok(!wantNow.some(c => st.now.includes(c)) && st.spring.includes('BUS 4488'), 'wins: on screen, Fall loses them and Spring keeps BUS 4488', st);
  ok(/Took \d+ off your account so it matches your report\./.test(st.toast), 'wins: the toast says what came off', st.toast);
  ok(log.errors.length === 0, 'wins: no page errors', log.errors);
  await close();
});

test('diff', async () => {
  /* pass 1: what this report reads as, to make an older one from */
  let reqs;
  { const { page, close } = await desk({ tables: fresh() }); await tick(page, 1500);
    await upload(page, 'files/dpr-transfer-continuing.pdf');
    reqs = await page.evaluate(() => auditStoredReqs(_dprMeta.audit)); await close(); }
  const old = JSON.parse(JSON.stringify(reqs));
  const a = old.find(b => b.label === 'BUS 3387'), c = old.find(b => b.label === 'BUS 4442'), u = old.find(b => b.kind === 'uscp');
  a.status = 'not'; a.used = []; c.status = 'satisfied';
  const t = fresh();
  t.degree_audit = [{ user_id: ME, printed_on: '2026-06-20', catalog: 'Fall Semester 2025', major: 'BUS', concentration: null, units_used: 40, units_needed: 80, requirements: old, read_at: '2026-06-20T00:00:00Z',
    overrides: [{ code: u.code, label: u.label, at: '2026-06-21T00:00:00Z' }] }];
  const s3387 = FX.TABLES.course_seats.find(r => r.course_code === 'BUS 3387');
  t.plans = [{ user_id: ME, term: '2268', slot: 'A', sections: [{ code: 'BUS 3387', class_nbr: String(s3387.class_nbr) }], shared: true }];
  const { page, close, log } = await desk({ tables: t }); await tick(page, 2500);
  const before = await page.evaluate(() => ({ a: !!curAudit(), ov: auditOverrides().length, plan: TCPlans.get('A').sections.map(x => x.code) }));
  ok(before.a && before.ov === 1 && before.plan.includes('BUS 3387'), 'diff: the old report and its mark are read from the account', before);
  await upload(page, 'files/dpr-transfer-continuing.pdf');
  log.writes.length = 0;
  await save(page, log);
  const m = await page.evaluate(() => { const b = document.getElementById('rfDiffBack'), md = document.getElementById('rfDiffModal');
    return { open: !!(b && b.classList.contains('open')), heads: md ? [...md.querySelectorAll('.rf-dh')].map(e => e.textContent) : [], items: md ? [...md.querySelectorAll('.rf-dl li')].map(e => e.textContent) : [], plans: md ? [...md.querySelectorAll('.rf-dpl span')].map(e => e.textContent) : [] }; });
  ok(m.open && m.heads.includes('Now filled 1') && m.heads.includes('Open again 1') && m.items.includes('BUS 3387') && m.items.includes('BUS 4442'), 'diff: “Your report changed” — newly filled and open again', m);
  ok(JSON.stringify(m.plans) === '["Plan A · BUS 3387"]', 'diff: the Plan class that filled a line now done is offered to take out', m.plans);
  const aw = rows(log, 'degree_audit', 'POST')[0] || {};
  ok(Array.isArray(aw.overrides) && aw.overrides.length === 1 && aw.overrides[0].code === u.code, 'diff: what you marked done stays marked through the new upload', aw.overrides);
  log.writes.length = 0;
  await page.evaluate(() => document.querySelector('#rfDiffModal .rf-dpl button').click()); await tick(page, 1200);
  const pw = log.writes.filter(w => w.table === 'plans').map(w => JSON.stringify(w.body));
  const st = await page.evaluate(() => ({ plan: TCPlans.get('A').sections.map(x => x.code), left: [...document.querySelectorAll('#rfDiffModal .rf-dpl')].length }));
  ok(!st.plan.includes('BUS 3387') && pw.length >= 1 && pw.every(x => !/BUS 3387/.test(x)) && st.left === 0, 'diff: “Take it out” takes it out of Plan A, on the account too', { st, pw });
  await page.evaluate(() => closeDprDiff()); await tick(page, 300);
  ok(!(await page.evaluate(() => document.getElementById('rfDiffBack').classList.contains('open'))), 'diff: Done closes it');
  ok(log.errors.length === 0, 'diff: no page errors', log.errors);
  await close();
});

test('inProgress', async () => {
  const t = fresh();
  t.class_history.push(
    { user_id: ME, code: 'BUS 3431', term: 'Fall', year: 2026, professor: null },        // this term: taking
    { user_id: ME, code: 'BUS 4442', term: 'Spring', year: 2027, professor: null },      // a later term: taking
    { user_id: ME, code: 'ECON 2030', term: 'Fall', year: 2026, professor: '🌍' },       // transfer credit posted this term: done
    { user_id: ME, code: 'STAT 2170', term: null, year: null, professor: null },         // undated: done
    { user_id: ME, code: 'BUS 2201', term: 'Spring', year: 2026, professor: null });     // last term: done
  t.saved_classes = []; t.my_sections = [];
  const probe = () => ({ done: completedCodes().slice().sort(), taking: myTakingCodes().slice().sort(), mirror: (JSON.parse(localStorage.getItem('professify_completed') || '[]')).sort(),
    nums: [...document.querySelectorAll('#plRecordHead .plr-n')].map(e => e.textContent) });
  { const { page, close, log } = await desk({ terms: SPRING_CFG, tables: t, time: '2026-10-14T10:30:00-07:00' }); await tick(page, 2000);
    await openPast(page);
    const r = await page.evaluate(probe);
    ok(!r.done.includes('BUS 3431') && !r.done.includes('BUS 4442') && ['ECON 2030', 'STAT 2170', 'BUS 2201'].every(c => r.done.includes(c)), 'in progress: this term’s and later rows are not done; transfer, undated and past rows are', r.done);
    ok(r.taking.includes('BUS 3431') && r.taking.includes('BUS 4442') && !r.taking.includes('BUS 2201'), 'in progress: they count as taking (prerequisites, the ledger, picks)', r.taking);
    ok(!r.mirror.includes('BUS 3431') && r.mirror.includes('BUS 2201'), 'in progress: this device’s mirror of finished classes doesn’t take them either', r.mirror);
    ok(r.nums.some(x => /^2\s*in progress$/.test(x.trim())), 'in progress: the record says 2 in progress', r.nums);
    ok(log.errors.length === 0, 'in progress: no page errors', log.errors); await close(); }
  { const { page, close } = await desk({ terms: SPRING_CFG, tables: t, time: '2026-12-23T10:30:00-08:00' }); await tick(page, 2000);
    const r = await page.evaluate(probe);
    ok(r.done.includes('BUS 3431') && !r.done.includes('BUS 4442') && !r.taking.includes('BUS 3431'), 'in progress: after Fall’s last day (TERM_ENDS) its rows are finished; Spring’s still aren’t', r); await close(); }
  { const { page, close } = await desk({ terms: SPRING_CFG, tables: t, time: '2027-02-01T10:30:00-08:00' }); await tick(page, 2000);
    const r = await page.evaluate(probe);
    ok(r.done.includes('BUS 3431') && !r.done.includes('BUS 4442') && r.taking.includes('BUS 4442'), 'in progress: in Spring, Spring’s rows are being taken (last term’s TERM_ENDS doesn’t apply)', r); await close(); }
});

test('local', async () => {
  const t = fresh();
  const gap = (url) => /\/rest\/v1\/degree_audit/.test(url.pathname) ? { status: 404, body: JSON.stringify({ code: '42P01', message: 'relation "public.degree_audit" does not exist' }) } : null;
  let stored;
  { const { page, close, log } = await desk({ terms: SPRING_CFG, tables: t, time: '2026-11-04T10:30:00-08:00', hook: gap }); await tick(page, 1500);
    await upload(page, 'files/dpr-transfer-continuing.pdf');
    await save(page, log);
    stored = await page.evaluate(id => localStorage.getItem('tc-audit:' + id), ME);
    const s = stored ? JSON.parse(stored) : null;
    ok(s && s.pending && Array.isArray(s.requirements) && s.requirements.length > 10 && s.user_id === ME, 'local: without the table the report is kept on this device, per account, to send later', s && Object.keys(s));
    await openPast(page);
    ok(await page.evaluate(() => !!document.querySelector('#plRecordHead .rf-top')), 'local: Past classes still reads it');
    const tm = await page.evaluate(() => (document.getElementById('frToast') || {}).textContent || '');
    ok(!/Couldn.t save what your report says/.test(tm), 'local: a missing table is not an error to the student', tm);
    ok(log.errors.length === 0, 'local: no page errors', log.errors); await close(); }
  /* the table is there now: what waited goes up */
  { const { page, close, log } = await desk({ terms: SPRING_CFG, tables: t, time: '2026-11-05T10:30:00-08:00', init: `try{ if(!sessionStorage.getItem('x')){ sessionStorage.setItem('x','1'); localStorage.setItem('tc-audit:${ME}', ${JSON.stringify(stored)}); } }catch(e){}` });
    await tick(page, 2500);
    const up = rows(log, 'degree_audit', 'POST');
    ok(up.length === 1 && up[0].user_id === ME && up[0].requirements.length > 10 && !('pending' in up[0]), 'local: the next load sends it up (and only what the account keeps)', up.map(x => Object.keys(x)));
    const s = await page.evaluate(id => JSON.parse(localStorage.getItem('tc-audit:' + id)), ME);
    ok(s && !s.pending, 'local: then it is no longer waiting', s && s.pending);
    ok(log.errors.length === 0, 'local: no page errors (2)', log.errors); await close(); }
  /* another account on this browser never sees it */
  { const { page, close } = await desk({ terms: SPRING_CFG, tables: t, init: `try{ localStorage.setItem('tc-audit:someone-else', ${JSON.stringify(stored)}); }catch(e){}` }); await tick(page, 2000);
    await openPast(page);
    ok(!(await page.evaluate(() => !!document.querySelector('#plRecordHead .rf-top'))), 'local: another account’s copy on this device is never read'); await close(); }
});

test('oldAudit', async () => {
  const t = fresh();
  t.degree_audit = [{ user_id: ME, printed_on: '2026-06-20', catalog: 'Fall Semester 2025', major: 'BUS', concentration: null, units_used: 40, units_needed: 80, read_at: '2026-06-20T00:00:00Z', overrides: [],
    requirements: [{ label: 'BUS 2201', status: 'satisfied', kind: 'major', code: 'R510-10', options: ['BUS 2201'] }, { label: 'BUS 4401', status: 'not', kind: 'major', code: 'R510-70', options: ['BUS 4401'] }] }];
  const { page, close, log } = await desk({ tables: t }); await tick(page, 2000);
  await openPast(page);
  const r = await page.evaluate(() => { const h = document.getElementById('plRecordHead'); return { again: (h.querySelector('.rf-again') || {}).textContent || '', old: !!h.querySelector('.plr-nums'), rf: !!h.querySelector('.rf-top') }; });
  ok(r.again === 'Upload your report again to see which class filled each requirement.' && r.old && !r.rf, 'old audit: a report kept before per-line classes keeps the old screen and asks for the report again', r);
  ok(log.errors.length === 0, 'old audit: no page errors', log.errors);
  await close();
});

test('conc', async () => {
  const t = fresh(); t.class_history.push({ user_id: ME, code: 'BUS 3441', term: 'Spring', year: 2026, professor: null });
  const { page, close, log } = await desk({ tables: t, init: BA }); await tick(page, 2000);
  const r = await page.evaluate(() => {
    const fm = concInfo('Business Administration').list.find(x => x.name === 'Financial Management');
    window.SCHED_LAST_CONC = 'Financial Management';
    const base = Object.values(SCHED_MAJORS).find(m => m.name === 'Business Administration');
    const ex = schExpandConcPublic(base), slots = ex.terms.flatMap(t => t.slots).filter(s => s.concKind);
    const one = slots.find(s => s.concKind === 'one');
    student.conc = 'Financial Management';
    const L = plLedgerCompute();
    return { req: fm && fm.classes.map(c => c[0]), one: fm && fm.one, el: fm && fm.electives.length, kinds: slots.map(s => s.concKind), oneSlot: one && { type: one.type, options: one.options, title: one.title },
      conc: L.led && L.led.rows.find(x => /Financial Management/.test(x.label)), needOne: L.led && L.led.need.some(n => n.codes.includes('BUS 3440')) };
  });
  ok(JSON.stringify(r.req) === '["BUS 3411","BUS 3431","BUS 3438"]' && JSON.stringify(r.one) === '[["BUS 3440","BUS 3441"]]' && r.el > 0, 'conc: a Business concentration’s required classes, its pick-one and its electives (planner.js CONC_SHAPE)', r);
  ok(r.oneSlot && r.oneSlot.type === 'choice' && JSON.stringify(r.oneSlot.options) === '["BUS 3440","BUS 3441"]' && r.kinds.includes('req') && r.kinds.includes('el'), 'conc: the flowchart’s concentration spots are required · pick one · elective', r);
  ok(r.conc && r.conc.f >= 1 && !r.needOne, 'conc: “BUS 3440 or BUS 3441” is checked like a coded spot — BUS 3441 on the record fills it', r);
  ok(log.errors.length === 0, 'conc: no page errors', log.errors);
  await close();
});

test('marks', async () => {
  /* the fixture major's flowchart: a GE row (no class to log) and a coded one */
  const pick = () => { const key = Object.keys(SCHED_MAJORS).find(k => SCHED_MAJORS[k].name === 'Business Administration'); const sl = SCHED_MAJORS[key].terms.flatMap(t => t.slots);
    const ge = sl.filter(s => s.type === 'ge' && !s.code); return { key, ge: ge[0], ge2: ge[1], coded: sl.find(s => s.code) }; };
  const t = fresh(); t.flowchart_marks = [];
  { const { page, close, log } = await desk({ tables: t, init: BA }); await tick(page, 2500);
    const P = await page.evaluate(pick);
    const pushes0 = log.writes.filter(w => w.table === 'flowchart_marks').length;
    await page.evaluate(P => { localStorage.removeItem('tc-marks-pushed:' + sbUser.id); localStorage.setItem('professify_sched_done_' + P.key, JSON.stringify([P.ge.id, P.coded.id])); }, P);
    await page.evaluate(() => loadMarks()); await tick(page, 600);
    const ins = rows(log, 'flowchart_marks', 'POST');
    ok(pushes0 === 0 && ins.length === 1 && ins[0].slot_id === P.ge.id && ins[0].label === P.ge.title && ins[0].major === 'Business Administration' && ins[0].user_id === ME,
      'marks: this device’s tick on a row with no class to log goes up to the account (a coded row is the record’s business)', { pushes0, ins, want: P.ge.id });
    /* unticked on the phone since: the account no longer has it, and this device's old tick must not bring it back */
    await page.evaluate(() => sb.from('flowchart_marks').delete().eq('user_id', sbUser.id)); await tick(page, 300);
    await page.evaluate(() => loadMarks()); await tick(page, 600);
    ok(rows(log, 'flowchart_marks', 'POST').length === 1 && (await page.evaluate(() => rfMarksState().marks.length)) === 0, 'marks: only once — after that the account decides (a mark removed elsewhere stays removed)', rows(log, 'flowchart_marks', 'POST').length);
    ok(log.reads.some(r => /^flowchart_marks\?select=major%2Cslot_id%2Clabel&user_id=eq\./.test(r) || /^flowchart_marks\?.*user_id=eq\./.test(r)), 'marks: read from the account, yours only', log.reads.filter(r => /flowchart/.test(r)));
    ok(log.errors.length === 0, 'marks: no page errors', log.errors); await close(); }
  /* the account's marks count: on its own row, with its own words */
  { const t2 = fresh(); t2.flowchart_marks = [];
    const probe = async (tables) => { const { page, close } = await desk({ tables, init: BA + `try{ localStorage.setItem('tc-marks-pushed:${ME}','1'); }catch(e){}` }); await tick(page, 2500);
      const P = await page.evaluate(pick);
      await page.evaluate(() => { show('sched'); setSchedTab('plan'); }); await tick(page, 600);
      const ge = await page.evaluate(() => { const L = plLedgerCompute(); return L.led && L.led.rows.find(r => r.label === 'General education').f; });
      await close(); return { P, ge }; };
    const a = await probe(t2);
    const t3 = fresh(); t3.flowchart_marks = [{ user_id: ME, major: 'Business Administration', slot_id: a.P.ge.id, label: a.P.ge.title }, { user_id: ME, major: 'Business Administration', slot_id: a.P.ge2.id, label: 'Some other words' }];
    const b = await probe(t3);
    ok(b.ge === a.ge + 1, 'marks: the account’s mark fills its row in the ledger — only where its words still match', { without: a.ge, with: b.ge }); }
  /* ticks made on this browser by another account never go up to yours */
  { const t4 = fresh(); t4.flowchart_marks = [];
    const { page, close, log } = await desk({ tables: t4, init: BA + `try{ localStorage.setItem('tc-marks-owner','someone-else'); }catch(e){}` }); await tick(page, 2500);
    const P = await page.evaluate(pick);
    await page.evaluate(P => { localStorage.removeItem('tc-marks-pushed:' + sbUser.id); localStorage.setItem('professify_sched_done_' + P.key, JSON.stringify([P.ge.id])); }, P);
    await page.evaluate(() => loadMarks()); await tick(page, 600);
    ok(rows(log, 'flowchart_marks', 'POST').length === 0, 'marks: another account’s ticks on this browser are never sent up as yours', rows(log, 'flowchart_marks', 'POST'));
    await close(); }
});

test('again', async () => {
  /* a newer report with nothing new to add: its verdicts are still kept */
  const { page, close, log } = await desk({ terms: SPRING_CFG, tables: fresh(), time: '2026-11-04T10:30:00-08:00' }); await tick(page, 1500);
  await upload(page, 'files/dpr-transfer-continuing.pdf');
  await page.evaluate(() => { tiRows.forEach(r => { r.pick = false; }); });
  log.writes.length = 0;
  await save(page, log);
  const r = await page.evaluate(() => ({ open: document.getElementById('tiBack').classList.contains('open'), toast: (document.getElementById('frToast') || {}).textContent || '' }));
  ok(rows(log, 'degree_audit', 'POST').length === 1 && !rows(log, 'class_history', 'POST').length && !r.open, 'again: with nothing to add, the report’s verdicts are still saved and the list closes', { r, w: log.writes.map(w => w.m + ' ' + w.table) });
  ok(/already logged|Nothing new to add/.test(r.toast) && !/Nothing selected/.test(r.toast), 'again: it says so', r.toast);
  ok(log.errors.length === 0, 'again: no page errors', log.errors);
  await close();
});

/* every word this flow adds reads at 4.5:1 or better, light (the default) and dark */
const CONTRAST = sel => {
  const rgb = s => { const m = /rgba?\(([^)]+)\)/.exec(s); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (f, b) => ({ r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1 });
  const bgOf = el => { const stack = []; for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; } }
    let b = { r: 255, g: 255, b: 255, a: 1 }; if (!stack.length || stack[stack.length - 1].a < 1) b = rgb(getComputedStyle(document.body).backgroundColor) || b; for (let i = stack.length - 1; i >= 0; i--) b = over(stack[i], b); return b; };
  const L = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const out = [];
  document.querySelectorAll(sel).forEach(el => { if (!el.textContent.trim() || !el.offsetParent) return; const b = bgOf(el), f = over(rgb(getComputedStyle(el).color), b);
    const r = (Math.max(L(f), L(b)) + 0.05) / (Math.min(L(f), L(b)) + 0.05); if (r < 4.5) out.push({ cls: el.className, t: el.textContent.trim().slice(0, 30), r: +r.toFixed(2) }); });
  return out;
};
test('contrast', async () => {
  for (const theme of ['light', 'dark']) {
    const t = fresh(); t.class_history.push({ user_id: ME, code: 'PHIL 3331', term: 'Spring', year: 2026, professor: null });
    const { page, close, log } = await desk({ terms: SPRING_CFG, tables: t, time: '2026-11-04T10:30:00-08:00', init: BA + (theme === 'dark' ? `try{ localStorage.setItem('professify-theme','dark'); }catch(e){}` : '') }); await tick(page, 1500);
    await upload(page, 'files/dpr-transfer-continuing.pdf');
    await page.evaluate(() => { document.querySelector('#tiModal .rf-check').open = true; }); await tick(page, 200);
    const th = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    const r1 = await page.evaluate(CONTRAST, '#tiModal .rf-cnt, #tiModal .rf-cat, #tiModal .rf-check summary, #tiModal .rf-tag, #tiModal .rf-cll, #tiModal .rf-cu, #tiModal .rf-clv, #tiModal .rf-flag, #tiModal .rf-rch, #tiModal .rf-rcs, #tiModal .rf-rct b, #tiModal .rf-rct span');
    await save(page, log); await page.evaluate(() => { try { closeDprDiff(); } catch (e) {} }); await openPast(page);
    await page.evaluate(() => document.querySelectorAll('#plRecordHead details').forEach(d => { d.open = true; })); await tick(page, 200);
    const r2 = await page.evaluate(CONTRAST, '#plRecordHead .rf-who b, #plRecordHead .rf-catc, #plRecordHead .rf-sum, #plRecordHead .rf-h span, #plRecordHead .rf-h em, #plRecordHead .rf-lab, #plRecordHead .rf-nm, #plRecordHead .rf-tag, #plRecordHead .rf-used, #plRecordHead .rf-need, #plRecordHead .rf-look, #plRecordHead .rf-mark, #plRecordHead .rf-fold > summary span, #plRecordHead .rf-fold > summary em, #plRecordHead .rf-uor b, #plRecordHead .rf-uor span, #plRecordHead .rf-dot');
    ok(th === theme && !r1.length && !r2.length, `contrast (${theme}): every word of the review list and Past classes reads at 4.5:1 or better`, { th, r1, r2 });
    ok(log.errors.length === 0, `contrast (${theme}): no page errors`, log.errors);
    await close();
  }
});

const names = ONLY ? ONLY.split(',') : Object.keys(T);
for (const n of names) {
  if (!T[n]) { console.log('no such test', n); process.exit(2); }
  if (!QUIET) console.log('\n' + n);
  try { await T[n](); } catch (e) { fail++; fails.push(n + ' threw'); console.log('  FAIL', n, 'threw', String(e).slice(0, 400)); }
}
console.log(`\ncheck-desktop-report: ${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', fails.join(' | ')); process.exit(1); }
