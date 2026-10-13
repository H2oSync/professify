#!/usr/bin/env python3
"""Tests for dpr-corpus-fixes-2026-10-12.py — what the 300 synthetic reports found (make-dpr-corpus.py,
check-dpr-synth.mjs). Adds tests.dprCorpusFound on files/dpr-corpus-found.pdf (make-dpr-corpus.py --fixture) and its
mutants. Replayable.  python3 edit-tests-dpr-corpus-2026-10-12.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

TESTS = r'''/* ============ What the 300 synthetic reports found (Tate, 2026-10-12) ============
   "create 300 different (artificial ones …) so we know every scenario we might be up against". check-dpr-synth.mjs runs
   all 300; this report (make-dpr-corpus.py --fixture) holds one of each thing they found. */
tests.dprCorpusFound = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-corpus-found.pdf');
  ok(await readPills(page) === '4 filled|1 left', 'found: after a "1 of 2 Options" requirement, the major’s next lines count as themselves (4 filled: the two classes, the option, MATE 4300 in progress; 1 left: BUS 207)', await readPills(page));
  const rd = await page.evaluate(() => { const a = UI.dpr.audit; const g = c => (a.reqs || []).find(b => b.code === c);
    return { r10: g('R40-10') && g('R40-10').options, r95: g('R40-95') && g('R40-95').status, r96: g('R40-96') && g('R40-96').status, opt: g('R-0041') && g('R-0041').options,
      rows: UI.dpr.rows.map(x => ({ c: x.code, cur: x.cur, pick: !!x.pick, now: !!x._now, skip: x.skip || '' })) }; });
  ok(rd.r95 === 'not' && rd.r96 === 'in_progress' && JSON.stringify(rd.opt) === '["BUS 4401","BUS 4411"]', 'found: R40-95 (open) and R40-96 (in progress) are their own lines, not more options of R-0041', rd);
  ok(JSON.stringify(rd.r10) === '["CSC 1001"]', 'found: a renamed subject — "CPE 101 (1001)" names CSC 1001, the crosswalk’s subject with the report’s number', rd.r10);
  const row = c => rd.rows.find(x => x.c === c) || {};
  ok(row('LA 222').cur === 'LA 2212', 'found: the report’s own pair wins — LA 222 (2212) is LA 2212, not the crosswalk’s LA 2222', row('LA 222'));
  ok(row('CPE 101').cur === 'CSC 1001', 'found: …and the crosswalk keeps a renamed subject when it agrees on the number (CPE 101 (1001) → CSC 1001)', row('CPE 101'));
  ok(row('MATE 4300').now === true && row('MATE 4300').pick, 'found: a class being taken whose cut-off title ends in a letter ("…Life C") is being taken, not graded C', row('MATE 4300'));
  ok(!row('BUS 207').pick && row('BUS 207').skip && !row('BUS 212').pick && row('BUS 212').skip, 'found: an F and a W are read but not picked to save', [row('BUS 207'), row('BUS 212')]);
  await saveReport(page);
  const hist = posted(log, 'class_history').map(r => r.code).sort(), mine = posted(log, 'saved_classes').map(r => r.code).sort();
  ok(JSON.stringify(hist) === '["BUS 4401","CSC 1001","LA 2212"]', 'found: Past classes gets the three passed classes, by today’s numbers — never the F or the W', hist);
  ok(mine.includes('MATE 4300') && mine.includes('BUS 3431'), 'found: the two classes being taken go to My Classes', mine);
  const comp = await page.evaluate(() => { plSync(); return TCPL.completed().map(c => TCPL.canon(c) || c); });
  ok(!comp.includes('BUS 2207') && !comp.includes('BUS 2212') && comp.includes('LA 2212'), 'found: a class never passed doesn’t count as completed (prerequisites, the flowchart, the Builder)', comp);
  ok(!JSON.stringify(log.writes).match(/Foundcase|9811001/), 'found: nothing personal stored');
  ok(log.errors.length === 0, 'found: no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [("tests.dprStressQuarter = async () => {", TESTS + "tests.dprStressQuarter = async () => {", 'tests')])


# Re-aims (as of build 23:19): dpr-stress-quarter.pdf's "Business Major Senior Project" (R40-95) follows its "1 of 2 Options" requirement
# (R-0041) and was being read as another option of it — dropped from every count, so the tests counted it out too. It is
# its own open line: 3 left on Report read, 2 left to graduate, 6 still needed. And the W attempt of BUS 207 isn't
# saved: 33 classes to the record, BUS 2207 once (its C in Fall 2024).
REAIM = [
 ("ok(await readPills(page) === '36 filled|2 left|5 transfer', 'quarter catalog: Report read — 33 Satisfied + 3 in progress = 36 filled, 2 left, 5 transfer",
  "ok(await readPills(page) === '36 filled|3 left|5 transfer', 'quarter catalog: Report read — 33 Satisfied + 3 in progress = 36 filled, 3 left (the Senior Project is its own line, 2026-10-12), 5 transfer"),
 ("ok(hist.length === 34 && hist.filter(r => r.code === 'BUS 2207').length === 2 && hist.filter(r => r.code === 'BUS 3306').length === 1, 'quarter catalog: 34 finished classes to the record (both attempts of BUS 207 → BUS 2207, as the report prints them)",
  "ok(hist.length === 33 && hist.filter(r => r.code === 'BUS 2207').length === 1 && hist.filter(r => r.code === 'BUS 3306').length === 1, 'quarter catalog: 33 finished classes to the record (BUS 207’s W attempt isn’t a class taken — only its C, as BUS 2207 (2026-10-12))"),
 ("ok(sum && sum.num === '37 of 38 filled' && sum.left === '1 left to graduate' && !sum.link",
  "ok(sum && sum.num === '37 of 39 filled' && sum.left === '2 left to graduate' && !sum.link"),
 ("ok(rows.filter(r => r.still).length === 1 && still.filter(r => r.st === 'need').map(r => r.main).join('|') === 'Career Readiness III: BUS 3306' &&",
  "ok(rows.filter(r => r.still).length === 2 && still.filter(r => r.st === 'need').map(r => r.main).join('|') === 'Career Readiness III: BUS 3306|Business Major Senior Project: BUS 4463 or BUS 4464' &&"),
 ("ok(heads.join('|') === 'Major and support 11 of 12|Financial Management 4 of 4",
  "ok(heads.join('|') === 'Major and support 11 of 13|Financial Management 4 of 4"),
 ("ok(rows.filter(r => r.st === 'done' && !r.still).length === 38 - 5 - 1 &&",
  "ok(rows.filter(r => r.st === 'done' && !r.still).length === 39 - 6 - 1 &&"),
 ("ok(pk.left === 1 && !pk.codes.some(c =>", "ok(pk.left === 2 && !pk.codes.some(c =>"),
 ("ok(sum2 && sum2.num === '37 of 38 filled' && sum2.left === '1 left to graduate' && b2 && /BUS 214 → BUS 2214 Winter 2025/.test(b2.sub) && rows2.filter(r => r.still).length === 1,",
  "ok(sum2 && sum2.num === '37 of 39 filled' && sum2.left === '2 left to graduate' && b2 && /BUS 214 → BUS 2214 Winter 2025/.test(b2.sub) && rows2.filter(r => r.still).length === 2,"),
 ("b.h === '1 left to graduate' && b.num === '37 of 38 filled' && b.bar === '37 of 38 filled' && b.rec,",
  "b.h === '2 left to graduate' && b.num === '37 of 39 filled' && b.bar === '37 of 39 filled' && b.rec,"),
 ("ok(b && b.lines.length === 1 && /^Career Readiness III/.test(b.lines[0]) && b.rows.length === 1 && b.rows[0].mark &&",
  "ok(b && b.lines.length === 2 && b.lines.some(l => /^Career Readiness III/.test(l)) && b.lines.some(l => /Senior Project/.test(l)) && b.rows.length === 1 && b.rows[0].mark &&"),
]
edit('check-app.mjs', [(a, b, 'reaim') for a, b in REAIM])

MUT = r'''  /* the 300 synthetic reports' findings (2026-10-12) */
  ["corpus: a line after 1 of N Options read as another option", "      b.parent=level==='LN'&&own?req:null;", "      b.parent=level==='LN'?req:null;", "dprCorpusFound", "planner"],
  ["corpus: the crosswalk beats the report's own pair", "      cur=(eq&&(!pr||String(eq).split(' ')[1]===String(pr).split(' ')[1]))?eq", "      cur=eq?eq", "dprCorpusFound", "planner"],
  ["corpus: the pair beats a renamed subject", "      cur=(eq&&(!pr||String(eq).split(' ')[1]===String(pr).split(' ')[1]))?eq", "      cur=(eq&&!pr)?eq", "dprCorpusFound", "planner"],
  ["corpus: an in-progress row's last letter read as a grade", "(cmark&&DPR_TEST.test(gradeTok))||pmark)){", "(cmark&&DPR_TEST.test(gradeTok)))){", "dprCorpusFound", "planner"],
  ["corpus: the in-progress picture not told apart", "p: !!psig && c.sig === psig && psig !== gsig }));", "p: false }));", "dprCorpusFound"],
  ["corpus: an option keeps the old subject", "if(m[3]&&eq&&String(eq).split(' ')[1]===m[3])now=eq;", "", "dprCorpusFound", "planner"],
  ["corpus: a failed class picked to save", "      pick:!already&&!fail, _fail:fail,", "      pick:!already, _fail:fail,", "dprCorpusFound", "planner"],
  ["corpus: a failed class not skipped on the phone", "    if (x._fail) { x._now = false; x.skip = 'not passed — not a finished class'; x.pick = false; return; }", "", "dprCorpusFound"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants')])
print('edit-tests-dpr-corpus: dprCorpusFound + 8 mutants')

# mutants whose anchors the fixes moved (re-aimed, same mutation)
MREAIM = [
 ('"const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) }));", "const mk = icons.map(c => ({ y: c.y, t: false, c: csig.has(c.sig) }));"',
  '"const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig), p:", "const mk = icons.map(c => ({ y: c.y, t: false, c: csig.has(c.sig), p:"'),
 ('"const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) }));", "const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: c.sig !== xsig }));"',
  '"const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig), p:", "const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: c.sig !== xsig, p:"'),
 ('"var k=mk.t?\'T\':mk.c?\'C\':\'O\'; if(k===\'C\')cp=true;", "var k=mk.t?\'T\':mk.c?\'C\':\'O\'; if(k!==\'T\')cp=true;"',
  '"var k=mk.t?\'T\':mk.c?(mk.p?\'P\':\'C\'):\'O\'; if(k===\'C\'||k===\'P\')cp=true;", "var k=mk.t?\'T\':mk.c?(mk.p?\'P\':\'C\'):\'O\'; if(k!==\'T\')cp=true;"'),
 ('"if(xmark||bmark||cmark)ln=ln.split(DPR_XMARK).join(\'\').split(DPR_BMARK).join(\'\').split(DPR_CMARK).join(\'\').trim();", ""',
  '"if(xmark||bmark||cmark||pmark)ln=ln.split(DPR_XMARK).join(\'\').split(DPR_BMARK).join(\'\').split(DPR_CMARK).join(\'\').split(DPR_PMARK).join(\'\').trim();", ""'),
 ('"||(cmark&&DPR_TEST.test(gradeTok))))", "))"', '"||(cmark&&DPR_TEST.test(gradeTok))||pmark)){", "||pmark)){"'),
]
edit('mutate.mjs', [(a, b, 'mreaim') for a, b in MREAIM])
print('edit-tests-dpr-corpus: 5 mutants re-aimed')

# three story mutants aimed at storyRank as it was before stories-freeness (2026-10-11): its "freeness:" mutants replace them
p = os.path.join(H, 'mutate.mjs'); s = open(p, encoding='utf-8').read()
for name in ('free stretch ignored', 'busy friends ordered by name', 'heading to class counted as free'):
    lines = [l for l in s.split('\n') if l.startswith("  ['" + name + "',")]
    for l in lines: s = s.replace(l + '\n', '')
open(p, 'w', encoding='utf-8').write(s)
print('edit-tests-dpr-corpus: 3 superseded story mutants dropped')
