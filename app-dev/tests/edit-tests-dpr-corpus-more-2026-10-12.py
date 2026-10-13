#!/usr/bin/env python3
"""Tests for dpr-corpus-more-2026-10-12.py: tests.dprCorpusMore on files/dpr-corpus-more.pdf (make-dpr-corpus.py
--fixture-more) — a Summer term, a minor, an Incomplete, a class being taken whose title ends in "I". Replayable.
  python3 edit-tests-dpr-corpus-more-2026-10-12.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

TESTS = r'''/* (Tate, 2026-10-12: "also add these Not covered yet: Summer terms, minors and double majors, the "I" grade, and
   semester-catalog students past their first term") — the corpus draws all four; this report holds one of each the
   reader has to tell apart. The account already holds BUS 3391 (an older import saved the Incomplete as done). */
tests.dprCorpusMore = async () => {
  const me = FX.ME.id;
  const T = Object.assign({}, XFER_T('Business Administration', 'Senior'), { class_history: [{ user_id: me, code: 'BUS 3391', term: 'Fall', year: 2025, professor: null }] });
  const { page, close, log } = await openApp({ tables: T, height: 2600 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await toPastTab(page);
  await page.waitForFunction(() => window.TCPL, null, { timeout: 8000 });
  await page.evaluate(() => { const f = TCPL.dprParse; TCPL.dprParse = t => { window.__dprText = t; return f(t); }; });
  await page.locator('input[data-in="dprfile"]').first().setInputFiles('files/dpr-corpus-more.pdf');
  for (let i = 0; i < 30 && !(await page.locator('#sheet .dr-h1, #sheet .tc-err').count()); i++) await tick(page, 500);
  ok(await readPills(page) === '3 filled|2 left', 'more: 3 filled (the Summer class, the class being taken, the minor’s first), 2 left (the Incomplete’s line, the minor’s second)', await readPills(page));
  const rd = await page.evaluate(() => Object.fromEntries(UI.dpr.rows.map(x => [x.code, { cur: x.cur, term: x.term + ' ' + x.year, pick: !!x.pick, now: !!x._now, fail: !!x._fail, prov: !!x._prov, open: !!x._open, title: x._title, skip: x.skip || '' }])));
  const R = c => rd[c] || {};
  ok(R('BUS 214').term === 'Summer 2024' && R('BUS 214').cur === 'BUS 2214' && R('BUS 214').pick, 'more: a class taken in a Summer term reads as Summer 2024, by today’s number, picked to save', R('BUS 214'));
  ok(R('BUS 391').fail && R('BUS 391').prov && !R('BUS 391').pick && !R('BUS 391').open && String(R('BUS 391').title).replace(/^\(\d{4}\)\s*/, '') === 'Career Readiness II', 'more: “I” in a term that’s over is an Incomplete — read, not passed, grade pending, never “being taken”, and not part of the title', R('BUS 391'));
  ok(R('BUS 3392').now && !R('BUS 3392').fail && R('BUS 3392').title === 'Career Readiness I', 'more: a class being taken whose title ends in “I” is being taken, not an Incomplete (no class in its term is graded yet)', R('BUS 3392'));
  ok(/^grade pending/.test(R('BUS 391').skip), 'more: the phone says an Incomplete’s grade is pending — not “not passed”', R('BUS 391').skip);
  /* (review) the same report read other ways: printed after finals; an AP placeholder; a transfer-icon row; a row whose icon was lost */
  const vr = await page.evaluate(() => { const t = window.__dprText, out = {};
    const row = (txt, code) => { const r = TCPL.dprParse(txt), x = r.rows.find(y => y.code === code); return x && { fail: !!x._fail, prov: !!x._prov, now: !!x._now, open: !!x._open, pick: !!x.pick, xfer: !!x._xfer, title: String(x._title || '').replace(/^\(\d{4}\)\s*/, '') }; };
    const at = (re, add) => { const m = re.exec(t); return m ? t.slice(0, m.index) + add + '\n' + t.slice(m.index) : t; };
    const t1 = t.replace(/2025 Fall(\s+BUS\s+391)/, '2026 Fall$1').replace(/(Security Analysis)\s+(4\.50)[^\n]*/, '$1   A   $2\uE002');
    out.dec = t1 !== t ? row(t1, 'BUS 391') : null;
    out.ap = row(at(/2025 Fall\s+BUS\s+391/, '2025 Fall AP 300 Calculus I 12.00'), 'AP 300');
    out.tr = row(at(/2025 Fall\s+BUS\s+391/, '2025 Spr MU 1T3A Music Theory I 4.00\uE000'), 'MU 1T3A');
    out.bm = row(at(/2025 Fall\s+BUS\s+391/, '2025 Spr BUS 393 (3393) Career Readiness III I 4.00\uE001'), 'BUS 393');
    /* October's report also lists Spring, registered ahead: Fall's "Career Readiness I" is still being taken */
    out.ahead = row(at(/2025 Fall\s+BUS\s+391/, '2027 Spr BUS 3450 Managerial Analysis 4.50\uE002'), 'BUS 3392');
    plSync(); return out; });
  ok(vr.dec && vr.dec.fail && vr.dec.prov && !vr.dec.now && !vr.dec.open && vr.dec.title === 'Career Readiness II', 'more: printed after finals (a class in the newest term graded), an “I” in that term is an Incomplete too — not being taken', vr.dec);
  ok(vr.ap && !vr.ap.fail && vr.ap.xfer && vr.ap.title === 'Calculus I' && vr.tr && !vr.tr.fail && vr.tr.xfer && vr.tr.title === 'Music Theory I', 'more: transfer and exam credit whose title ends in “I” is never an Incomplete (an AP placeholder, a transfer-icon row)', [vr.ap, vr.tr]);
  ok(vr.bm && !vr.bm.fail && /Career Readiness III I$/.test(vr.bm.title), 'more: a row whose icon was lost is never read as an Incomplete (exam credit wears no icon) — the I stays a word', vr.bm);
  ok(vr.ahead && !vr.ahead.fail && vr.ahead.open && vr.ahead.title === 'Career Readiness I', 'more: with Spring registered ahead on the report, Fall’s class whose title ends in “I” is still being taken — its term isn’t over on the report’s date', vr.ahead);
  const lines = await page.evaluate(() => (UI.dpr.audit.reqs || []).filter(b => /^R89-/.test(b.code)).map(b => b.code + ':' + b.status + ':' + b.kind));
  ok(JSON.stringify(lines) === '["R89-10:satisfied:major","R89-20:not:major"]', 'more: a minor’s lines are read and counted, as the report counts them', lines);
  const rc = await page.evaluate(() => (UI.dpr.rc || []).map(x => x.kind + ':' + x.code + ':' + x.why));
  ok(!rc.some(s => /BUS 3391/.test(s)), 'more: an Incomplete keeps its class on the account (its grade is pending, like RP)', rc);
  await saveReport(page);
  const hist = posted(log, 'class_history').map(r => r.code + ' ' + r.term + ' ' + r.year).sort(), mine = posted(log, 'saved_classes').map(r => r.code);
  ok(JSON.stringify(hist) === '["BUS 2214 Summer 2024","ECON 2201 Spring 2025"]', 'more: Past classes gets the Summer class (as Summer 2024) and the minor’s class — never the Incomplete', hist);
  ok(mine.includes('BUS 3392') && mine.includes('BUS 3431'), 'more: both classes being taken go to My Classes', mine);
  ok(!JSON.stringify(log.writes).match(/Morecase|9811002/), 'more: nothing personal stored');
  ok(log.errors.length === 0, 'more: no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [("tests.dprStressQuarter = async () => {", TESTS + "tests.dprStressQuarter = async () => {", 'tests')])
MUT = r'''  ["more: an Incomplete read as the end of a title", "out.forEach(function(r){ if(r._iTok&&(pd?", "out.forEach(function(r){ if(false&&(pd?", "dprCorpusMore", "planner"],
  ["more: an “I” in the term being taken read as an Incomplete", "(pd?!dprTermRunning(r.term,r.year,pd):", "(pd?true:", "dprCorpusMore", "planner"],
  ["more: a term counted over because a later one is listed", "(pd?!dprTermRunning(r.term,r.year,pd):(r.year*10+(ORD[r.term]||0))<latest)", "((r.year*10+(ORD[r.term]||0))<latest)", "dprCorpusMore", "planner"],
  ["more: an Incomplete missed beside a graded class in its term", "var k=r.year*10+(ORD[r.term]||0); if(out.some(", "var k=r.year*10+(ORD[r.term]||0); if(false&&out.some(", "dprCorpusMore", "planner"],
  ["more: an Incomplete taken off the account", "r._fail=true; r._prov=true; r.pick=false; r._title=", "r._fail=true; r.pick=false; r._title=", "dprCorpusMore", "planner"],
  ["more: an Incomplete's title keeps its I", "r._title=String(r._title||'').replace(/\\s+I$/,'');", "r._title=String(r._title||'');", "dprCorpusMore", "planner"],
  ["more: a transfer row's I taken for an Incomplete", "var iTok=rawI&&!xfer&&!pmark&&!bmark;", "var iTok=rawI&&!pmark&&!bmark;", "dprCorpusMore", "planner"],
  ["more: a row with a lost icon taken for an Incomplete", "var iTok=rawI&&!xfer&&!pmark&&!bmark;", "var iTok=rawI&&!xfer&&!pmark;", "dprCorpusMore", "planner"],
  ["more: an Incomplete said not passed", "x.skip = x._prov ? 'grade pending — not a finished class' : 'not passed — not a finished class';", "x.skip = 'not passed — not a finished class';", "dprCorpusMore"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants'),
  # re-aimed: the phone's skip line now says "grade pending" for an Incomplete or RP (same mutation: drop the line)
  ('''  ["corpus: a failed class not skipped on the phone", "    if (x._fail) { x._now = false; x.skip = 'not passed — not a finished class'; x.pick = false; return; }", "", "dprCorpusFound"],''',
   '''  ["corpus: a failed class not skipped on the phone", "    if (x._fail) { x._now = false; x.skip = x._prov ? 'grade pending — not a finished class' : 'not passed — not a finished class'; x.pick = false; return; }", "", "dprCorpusFound"],''', 'reaim skip')])
print('edit-tests-dpr-corpus-more: dprCorpusMore + 8 mutants, 1 re-aimed')
