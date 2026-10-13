#!/usr/bin/env python3
"""Tests for in-progress-now-2026-10-11.py. Run AFTER edit-tests-quarter-ge-2026-10-11.py.
Usage: python3 edit-tests-in-progress-now-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs')
S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    n = S.count(a)
    if n != 1: sys.exit(f'tests {label}: anchor matched {n}x')
    S = S.replace(a, b)
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", """
/* (2026-10-11) Tate: "for a class im currenty enrolled in it shouldnt say complete but it should have the in progress
   thing … no matter where the class is in the flowchart" */
tests.inProgressNow = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  const r = await page.evaluate(() => {
    plSync(); const L0 = TCPL.ledger(), slots = L0.grid.flatMap(t => t.slots);
    const need = slots.filter(s => s.state === 'need' && s.code && !s.choice && COURSES[(s.codes || [s.code])[0]] === undefined ? true : s.state === 'need' && s.code && !s.choice);
    const a = need[0], b = need[1], ca = (a.codes || [a.code])[0], cb = (b.codes || [b.code])[0];
    const onSlot = new Set(slots.flatMap(s => [s.code, ...(s.codes || []), ...(s.choice || [])]).filter(Boolean).map(c => TCPL.canon(c) || c));
    const other = Object.keys(COURSES).find(c => !onSlot.has(TCPL.canon(c) || c) && !myCodes().has(c) && !(TC.myHistory || []).some(h => (TCPL.canon(h.code) || h.code) === c));
    const nowLab = nowTerm().label, [nt, ny] = nowLab.split(' ');
    /* this term: a flowchart class and a class on no spot; last summer: another flowchart class */
    TC.myHistory = (TC.myHistory || []).concat([{ code: ca, term: nt, year: +ny, professor: 'Pat Nowterm' }, { code: other, term: nt, year: +ny, professor: null }, { code: cb, term: 'Summer', year: +ny, professor: null }]);
    const xr = { code: 'ZZ 9999', term: nt, year: +ny, professor: TCPL.abroadMark };
    plSync(); const L = TCPL.ledger(), st = id => L.grid.flatMap(t => t.slots).find(s => s.id === id).state;
    const out = { ca, cb, other, nowLab, sa: st(a.id), sb: st(b.id), doneHasA: TCPL.completed().map(c => TCPL.canon(c) || c).includes(TCPL.canon(ca) || ca), doneHasB: TCPL.completed().map(c => TCPL.canon(c) || c).includes(TCPL.canon(cb) || cb), taking: takingCodes().has(ca), aId: a.id, xferNow: histNotDone(xr) };
    /* the report: Satisfied, filled by a class being taken now — in progress */
    const R = (label, status, used) => ({ label, status, kind: 'major', ge: null, level: 'LN', code: null, units: null, courses: null, options: [], oneOf: false, used, listed: [] });
    const A = { catalog: 'Fall Quarter 2023', reqs: [R('BUS 431 (3431)', 'satisfied', [{ c: 'BUS 3431', t: nowLab, p: true }]), R('BUS 342 (3342)', 'satisfied', [{ c: 'BUS 342', n: 'BUS 3342', t: 'Spring 2025' }]), R('ART 101', 'satisfied', [{ c: 'ART 3TC1', t: nowLab, x: true }]), R('DANC 1100', 'satisfied', [{ c: 'DANC 1100', t: nowLab }])] };
    const X = auditLines(A, null);
    out.now = X.now.size; out.inprog = X.inprog.map(b => b.label); out.filled = X.filled.length;
    /* after the term's last day, grades are in: this term's row is finished */
    const keep = CFG.TERM_ENDS; CFG.TERM_ENDS = '2000-01-01'; plSync(); out.after = TCPL.ledger().grid.flatMap(t => t.slots).find(s => s.id === a.id).state; out.afterRep = auditLines(A, null).now.size; CFG.TERM_ENDS = keep; plSync();
    out.rowNow = /pc-row taking/.test(pcReqRow(A.reqs[0], X, null, 0)); out.rowPast = /pc-row done/.test(pcReqRow(A.reqs[1], X, null, 1));
    render(true); return out;
  });
  ok(r.sa === 'taking' && r.taking && !r.doneHasA, 'in progress: a class on your record dated this term is in progress on its flowchart spot, not done — and no prerequisite counts it finished', r);
  ok(r.xferNow === false, 'in progress: transfer credit posted this term is finished, never in progress', r);
  ok(r.sb === 'done' && r.doneHasB, 'in progress: a class from an earlier term (last summer) is still done', r);
  await page.evaluate(() => { for (let y = 1; y <= 5; y++) UI.plYears[y] = true; UI.pcAll = 1; render(true); }); await tick(page, 600);
  const v = await page.evaluate(([ca, other]) => {
    const rows = [...document.querySelectorAll('.pc-row')], slot = rows.find(e => (e.querySelector('.pc-cc') || {}).textContent === ca);
    const oth = [...document.querySelectorAll('.pc-orow')].find(e => (e.querySelector('.pc-cc') || {}).textContent === other);
    const othA = [...document.querySelectorAll('.pc-orow')].some(e => (e.querySelector('.pc-cc') || {}).textContent === ca);
    return { slot: slot && { cls: slot.className, dot: slot.querySelector('.pc-dot').textContent.trim(), prof: (slot.querySelector('.pc-pf') || {}).textContent || '' }, oth: oth && oth.innerText.replace(/\\s+/g, ' '), othA };
  }, [r.ca, r.other]);
  ok(v.slot && /taking/.test(v.slot.cls) && v.slot.dot === '◐' && v.slot.prof === 'Pat Nowterm', 'in progress: on Past classes its spot shows ◐ with the professor from your record', v);
  ok(!v.othA, 'in progress: the class isn\\u2019t also listed under Other classes', v);
  ok(v.oth && /In progress · this term/.test(v.oth), 'in progress: a class this term on no flowchart spot says “In progress · this term” in Other classes', v);
  /* a class in My Classes this term on no spot, not on your record: listed as in progress */
  const m = await page.evaluate(other => { TC.myHistory = TC.myHistory.filter(h => h.code !== other); PEOPLE.me.unplaced = (PEOPLE.me.unplaced || []).concat([other]); if (PEOPLE.me.nowUnplaced) PEOPLE.me.nowUnplaced = PEOPLE.me.nowUnplaced.concat([other]); render(true);
    const e = [...document.querySelectorAll('.pc-orow')].find(x => (x.querySelector('.pc-cc') || {}).textContent === other); return e ? e.innerText.replace(/\\s+/g, ' ') : null; }, r.other);
  ok(m && /In progress · this term/.test(m), 'in progress: a class in My Classes this term that fills no spot is listed under Other classes as in progress', m);
  ok(r.now === 1 && r.inprog.join() === 'BUS 431 (3431)' && r.filled === 4 && r.rowNow && r.rowPast, 'in progress: a report line the registrar marked Satisfied with a class being taken now (no grade) is in progress (still counted filled); transfer credit, past classes and a class graded this term stay done', r);
  ok(r.after === 'done' && r.afterRep === 1, 'in progress: once the term has ended (CFG.TERM_ENDS) a row of it is done; a line the report says is being taken stays in progress', r);
  ok(log.errors.length === 0, 'in progress: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
# re-aims: classes being taken this term are in progress (Tate, 2026-10-11)
rep("""  ok(me === '18 of 30 requirements filled Environmental Management & Protection · 1 in progress', 'transfer, first term: the profile’s row is the report’s count too', me);""",
    """  ok(me === '18 of 30 requirements filled Environmental Management & Protection · 3 in progress', 'transfer, first term: the profile’s row is the report’s count too — in progress counts the Satisfied lines whose class is still being taken (NR 3308, NR 1142)', me);""", 're-aim transfer first')
rep("""  const all = await page.evaluate(() => [...document.querySelectorAll('.pc-oth .pc-orow')].map(r => ({ main: r.querySelector('.pc-main').innerText.replace(/\\s+/g, ' '), add: !!r.querySelector('.pc-add'), pf: (r.querySelector('.pc-pf') || {}).innerText || '' })));
  const ap = all.find(r => /^AP 300/.test(r.main));
  ok(all.length === n && !(await page.locator('[data-a="pcAll"]').count()) && ap && !ap.add && !ap.pf && all.filter(r => r !== ap).every(r => r.add), 'past: See all shows every one; transfer credit (AP 300) gets no “+ Professor”, the others do', all);""",
    """  const all = await page.evaluate(() => [...document.querySelectorAll('.pc-oth .pc-orow')].map(r => ({ main: r.querySelector('.pc-main').innerText.replace(/\\s+/g, ' '), add: !!r.querySelector('.pc-add'), pf: (r.querySelector('.pc-pf') || {}).innerText || '', now: !!r.querySelector('.pc-nowt') })));
  const ap = all.find(r => /^AP 300/.test(r.main));
  ok(all.length === n && !(await page.locator('[data-a="pcAll"]').count()) && ap && !ap.add && !ap.pf && all.filter(r => r !== ap && !r.now).every(r => r.add), 'past: See all shows every one; transfer credit (AP 300) gets no “+ Professor”, the others do', all);
  ok(all.some(r => r.now) && all.filter(r => r.now).every(r => !r.add && r.pf) && all.findIndex(r => !r.now) > all.findLastIndex(r => r.now), 'past: the classes you\\u2019re taking this term that fill no spot come first, “In progress · this term”, with your section\\u2019s professor', all.filter(r => r.now));""", 're-aim past simple')

open(P, 'w', encoding='utf-8').write(S)

M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs')
T = open(M, encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("now: a record row this term counts as done", "history: histDone(), classes:", "history: TC.myHistory || [], classes:", "inProgressNow", None),
  ("now: a record row this term isn't taking", "classes: [...takingCodes()], waived:", "classes: [...myCodes()], waived:", "inProgressNow", None),
  ("now: every dated row counts as unfinished", "  return row > now || (row === now && nowTermOn());", "  return true;", "inProgressNow", None),
  ("now: transfer credit this term is in progress", "  if (window.TCPL && h.professor === TCPL.abroadMark) return false;", "", "inProgressNow", None),
  ("now: this term's rows stay unfinished after the term ends", "function nowTermOn() { return !CFG.TERM_ENDS || sloISO() <= CFG.TERM_ENDS; }", "function nowTermOn() { return true; }", "inProgressNow", None),
  ("now: a Satisfied line being taken stays done", "b.status === 'satisfied' && (b.used || []).some(e => !e.x && e.p)", "false", "inProgressNow", None),
  ("now: a graded class this term is in progress", "(b.used || []).some(e => !e.x && e.p)", "(b.used || []).some(e => !e.x && (e.p || e.t === nowTerm().label))", "inProgressNow", None),
  ("now: the report row ignores in progress", "X.covered.has(b) || (X.now && X.now.has(b)) ? 'taking'", "X.covered.has(b) ? 'taking'", "inProgressNow", None),
  ("now: a taking spot loses its record row", "if (i >= 0) slot.set(s.id, q.splice(i, 1)[0]);", "", "inProgressNow", None),
  ("now: a taking spot shows no professor from the record", "if (s) return `<span class=\"pc-pf\">${esc(PROFS[s.prof].name)}</span>`; if (!h) return ''; }", "return s ? `<span class=\"pc-pf\">${esc(PROFS[s.prof].name)}</span>` : ''; }", "inProgressNow", None),
  ("now: Other classes never says this term", "${nw ? pcNowTag : ''}", "", "inProgressNow", None),
  ("now: My Classes on no spot isn't listed", ".forEach(c => rows.unshift({ code: c, now: true }));", ";", "inProgressNow", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
lines = ''.join('  ' + json.dumps([n, a, b, t, g], ensure_ascii=False) + ',\n' for n, a, b, t, g in MUT)
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
if T.count(k) != 1: sys.exit('mutate anchor')
T = T.replace(k, "\n  /* a class this term is in progress (2026-10-11; edit-tests-in-progress-now-2026-10-11.py) */\n" + lines + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
# re-aim older mutants whose code this patch rewrote (same meaning, new words)
REAIM = [
  ("""['waivers ignored by the planner', "classes: [...myCodes()], waived: TC.waived || {},", "classes: [...myCodes()], waived: {},", 'planner'],""",
   """['waivers ignored by the planner', "classes: [...takingCodes()], waived: TC.waived || {},", "classes: [...takingCodes()], waived: {},", 'planner'],"""),
  ("""['prereq: this term’s classes ignored', "const st = TCPL.prereqStatus(code, TCPL.completed(), [], [...myCodes()]);\\n  const empty", "const st = TCPL.prereqStatus(code, TCPL.completed(), [], []);\\n  const empty", 'prereqVerdict'],""",
   """['prereq: this term’s classes ignored', "const st = TCPL.prereqStatus(code, TCPL.completed(), [], [...takingCodes()]);\\n  const empty", "const st = TCPL.prereqStatus(code, TCPL.completed(), [], []);\\n  const empty", 'prereqVerdict'],"""),
  ("""["past classes: a line you marked done shown as the report's", "const st = b.status === 'satisfied' ? 'done' : b.status === 'in_progress' ? 'taking' : null;", "const st = b.status === 'satisfied' || X.manual.has(b) ? 'done' : b.status === 'in_progress' ? 'taking' : null;", "pastByReport"],""",
   """["past classes: a line you marked done shown as the report's", "const st = b.status === 'satisfied' && !(X.now && X.now.has(b)) ? 'done' :", "const st = (b.status === 'satisfied' || X.manual.has(b)) && !(X.now && X.now.has(b)) ? 'done' :", "pastByReport"],"""),
  ("""["truth: a class that left the open list without its line being done is 'done now'", "O.open.forEach(b => { const nb = now.get(kO.get(b)); if (nb && done(nb)) (b.options || []).forEach(c => doneNow.add(k(c))); });", "O.open.forEach(b => { (b.options || []).forEach(c => doneNow.add(k(c))); });", "dprTruthRules", null],""",
   """["truth: a class that left the open list without its line being done is 'done now'", "forEach(b => { const nb = now.get(kO.get(b)); if (nb && done(nb)) (b.options || []).forEach(c => doneNow.add(k(c))); });", "forEach(b => { (b.options || []).forEach(c => doneNow.add(k(c))); });", "dprTruthRules", null],"""),
]
for a, b in REAIM:
    if T.count(a) != 1: sys.exit('reaim anchor: ' + a[:70] + f' ({T.count(a)}x)')
    T = T.replace(a, b)
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-in-progress-now: done')
