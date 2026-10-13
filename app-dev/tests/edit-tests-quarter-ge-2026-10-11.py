#!/usr/bin/env python3
"""Tests for quarter-ge-guidelines-2026-10-11.py (the registrar's "Staying on QUARTER Catalog: GE Pattern Guidelines").
Run AFTER edit-tests-dpr-truth-2026-10-11.py. Usage: python3 edit-tests-quarter-ge-2026-10-11.py <repo-dir>  (replayable)"""
import sys, os
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs')
S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    n = S.count(a)
    if n != 1: sys.exit(f'tests {label}: anchor matched {n}x')
    S = S.replace(a, b)

rep("""  ok(r.ldc === '3A/3B' && r.el === '2/5A/5B/5C/3A/3B/4A/4B', 'rules: the C elective is 3A or 3B; a GE elective is any lower-division B, C or D area', r);""",
    """  ok(r.ldc === '3A/3B' && r.el === '2/5A/5B/5C/3A/3B/4A/4B/U25/UD3/UD4', 'rules: the C elective is 3A or 3B; a GE elective is any B, C or D area, lower or upper division (the registrar\\u2019s quarter GE sheet)', r);""", 're-aim el')

rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", """
/* (2026-10-11) The registrar's sheet "Staying on QUARTER Catalog: GE Pattern Guidelines" */
tests.dprQuarterGeSheet = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Psychology', 'Junior'), height: 2400 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  const r = await page.evaluate(() => {
    const L = (label, status, extra) => Object.assign({ label, status, kind: 'ge', ge: null, level: 'LN', code: null, units: null, courses: null, options: [], oneOf: false, used: [], listed: [] }, extra || {});
    const areas = l => plGeArea(L(l, 'not')).join('/');
    const out = { el: areas('GE Elective: Areas B, C, and D'), be: areas('Area B Electives'), be2: areas('B Elective'), bud: plGeArea(L('B UD: Upper-Division B', 'not', { ge: 'BUD' })).join('/') };
    /* the subject with the most 3A/3B classes the planner knows — the one most likely to be picked twice */
    const G = plGeMap(), sub = c => c.split(' ')[0], cnt = {};
    const isC = c => (G.get(c) || []).some(a => a === '3A' || a === '3B');
    [...G.keys()].forEach(c => { if (isC(c)) cnt[sub(c)] = (cnt[sub(c)] || 0) + 1; });
    const P = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0], Q = Object.keys(cnt).find(s => s !== P);
    const pcs = [...G.keys()].filter(c => sub(c) === P && isC(c)).slice(0, 2), pc = pcs[0], qc = [...G.keys()].find(c => sub(c) === Q && isC(c));
    out.P = P; out.Q = Q; out.pc = pc; out.qc = qc;
    /* the term's seats here hold no 3A/3B class: give two of C1's subject and one of another a section, like the real list does */
    const s0 = Object.values(SEC)[0]; let nb = 99100;
    pcs.concat([qc]).forEach(c => { COURSES[c] = COURSES[c] || { title: c, units: null, prereq: null, desc: null, short: c }; addSection(Object.assign({}, s0, { id: String(nb++), code: c, sec: '01' })); });
    const reqs = (c1) => [L('C1: Arts Course', 'satisfied', { ge: 'C1', used: [{ c: c1 + ' 101', n: c1 + ' 1101', t: 'Fall 2024' }] }), L('C2: Letters Course', 'satisfied', { ge: 'C2', used: [{ c: 'LIT 230', t: 'Winter 2025' }] }), L('Lower-division C Elective', 'not')];
    const RP = reqs(P), RQ = reqs(Q);
    out.barP = plGeBar(RP[2], pc, RP); out.barQ = plGeBar(RP[2], qc, RP); out.barOther = plGeBar(L('GE Elective: Areas B, C, and D', 'not'), pc, RP);
    out.barEngl = plGeBar(RP[2], 'LIT 2230', RP);
    /* a class in My Classes of C1's subject never puts the C elective in progress; one of another subject does */
    PEOPLE.me.unplaced = (PEOPLE.me.unplaced || []).concat([pc]);
    out.covP = auditLines({ catalog: 'Fall Quarter 2024', reqs: RP }, null).covered.size;
    out.covQ = auditLines({ catalog: 'Fall Quarter 2024', reqs: RQ }, null).covered.size;
    PEOPLE.me.unplaced = PEOPLE.me.unplaced.filter(c => c !== pc);
    /* the Planner never picks a class of C1's subject for the C elective */
    TC.audit = { reqs: RP, counts: {}, overrides: [], catalog: 'Fall Quarter 2024' }; plSync();
    const R = planRank(TCPL.ledger()), forC = R.all.filter(c => (c.fills || []).some(b => /C Elective/.test(b.label)));
    out.picks = forC.map(c => c.code); out.badPicks = out.picks.filter(c => sub(c) === P); out.qPicked = out.picks.includes(qc);
    return out;
  });
  ok(r.el === '2/5A/5B/5C/3A/3B/4A/4B/U25/UD3/UD4', 'quarter GE sheet: "GE Elective: Area B, C or D" is any additional Area 2, 3, 4 or 5, lower or upper division', r);
  ok(r.be === '5A/5B/5C' && r.be2 === '5A/5B/5C', 'quarter GE sheet: the high-unit template\\u2019s "Area B Electives" is any 5A\\u20135C course', r);
  ok(r.bud === 'U25', 'quarter GE sheet: Upper-Division B is UD 2 or UD 5', r);
  ok(r.barP === true && r.barQ === false && r.barOther === false && r.barEngl === true, 'quarter GE sheet: the C elective must be "in a different subject" from C1 and C2 \\u2014 only the C elective is barred', r);
  ok(r.covP === 0 && r.covQ === 1, 'quarter GE sheet: a class of C1\\u2019s subject in My Classes never puts the C elective in progress; another subject\\u2019s does', r);
  ok(r.qPicked && r.badPicks.length === 0, 'quarter GE sheet: the Planner never picks a class of C1\\u2019s subject for the C elective', r);
  ok(log.errors.length === 0, 'quarter GE sheet: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
open(P, 'w', encoding='utf-8').write(S)
PA_APP = os.path.join(D, 'app', 'index.html')
import json
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs')
T = open(M, encoding='utf-8').read()
MUT = [
  ("quarter GE: a GE elective is lower-division only", "return ['2', '5A', '5B', '5C', '3A', '3B', '4A', '4B', 'U25', 'UD3', 'UD4'];", "return ['2', '5A', '5B', '5C', '3A', '3B', '4A', '4B'];", "dprQuarterGeSheet", None),
  ("quarter GE: Area B Electives get no area", "  if (/^(?:Area\\s+)?B\\s+Electives?\\b/i.test(l)) return ['5A', '5B', '5C'];", "", "dprQuarterGeSheet", None),
  ("quarter GE: the C elective takes any subject", "  return used.has(geSubj(code));\n}", "  return false;\n}", "dprQuarterGeSheet", None),
  ("quarter GE: C1's subject ignored", "if (x === b || /^(C1|C2)$/.test(x.ge || '') || /^(?:GE\\s+)?C[12]\\s*:/i.test(String(x.label || '')))", "if (x === b)", "dprQuarterGeSheet", None),
  ("quarter GE: the bar applies to every line", "  if (!b || !/^(?:GE\\s+)?Lower[- ]division C Elective\\b/i.test(String(b.label || ''))) return false;", "  if (!b) return false;", "dprQuarterGeSheet", None),
  ("quarter GE: My Classes ignores the bar", "!spent.has(k(c)) && !plGeBar(b, c, a.reqs) &&", "!spent.has(k(c)) &&", "dprQuarterGeSheet", None),
  ("quarter GE: the Planner ignores the bar", "const ok = (byArea[a] || []).filter(b => !plGeBar(b, code));", "const ok = (byArea[a] || []);", "dprQuarterGeSheet", None),
]
for n, a, b, t, g in MUT:
    if open(PA_APP, encoding='utf-8').read().count(a) != 1: sys.exit(f'mutant anchor {n}')
lines = ''.join('  ' + json.dumps([n, a, b, t, g], ensure_ascii=False) + ',\n' for n, a, b, t, g in MUT)
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
if T.count(k) != 1: sys.exit('mutate anchor')
T = T.replace(k, "\n  /* the registrar's quarter GE sheet (2026-10-11; edit-tests-quarter-ge-2026-10-11.py) */\n" + lines + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-quarter-ge: done')
