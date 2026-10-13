#!/usr/bin/env python3
"""Tests for the review fixes in dpr-corpus-fixes-2026-10-12.py (6–8) and for fix 2, which tests.dprCorpusFound didn't
prove (the fixture's crosswalk agreed with its pair). Run after edit-tests-dpr-corpus-2026-10-12.py. Replayable.
  python3 edit-tests-dpr-corpus-review-2026-10-12.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

# dprCorpusFound: plant a crosswalk entry that disagrees with the report's own pair (LA 222 → LA 2222; the report says
# 2212), and keep what the shared reader itself said before the phone's own pass (the website's import uses it as is).
edit('check-app.mjs', [
("""  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-corpus-found.pdf');
  ok(await readPills(page) === '4 filled|1 left',""",
 """  const T0 = XFER_T('Business Administration', 'Senior');   /* (review) a crosswalk that disagrees with the report's pair: LA 222 → LA 2222; the report says (2212) */
  const { page, close, log } = await openApp({ tables: Object.assign({}, T0, { course_equiv: (T0.course_equiv || []).concat([{ legacy_code: 'LA 222', current_code: 'LA 2222' }]) }), height: 2600 });
  await toPlanner(page);
  await page.waitForFunction(() => window.TCPL && TCPL.canon('LA 222') === 'LA 2222', null, { timeout: 8000 });
  await page.evaluate(() => { const f = TCPL.dprParse; TCPL.dprParse = t => { const r = f(t); window.__dprRaw = { text: t, rows: r.rows.map(x => ({ c: x.code, pick: !!x.pick, fail: !!x._fail })) }; return r; }; });
  await uploadFile(page, 'dpr-corpus-found.pdf');
  ok(await readPills(page) === '4 filled|1 left',""", 'plant'),
("""  ok(!row('BUS 207').pick && row('BUS 207').skip && !row('BUS 212').pick && row('BUS 212').skip, 'found: an F and a W are read but not picked to save', [row('BUS 207'), row('BUS 212')]);""",
 """  ok(!row('BUS 207').pick && row('BUS 207').skip && !row('BUS 212').pick && row('BUS 212').skip, 'found: an F and a W are read but not picked to save', [row('BUS 207'), row('BUS 212')]);
  const raw = await page.evaluate(() => window.__dprRaw.rows.filter(x => /BUS 20[7]|BUS 212/.test(x.c)));
  ok(raw.length === 2 && raw.every(x => x.fail && !x.pick), 'found: the shared reader itself leaves the F and the W unpicked (the website’s import unticks them)', raw);
  /* (review) more grades, "IP" in the grade column, and grades never posted as transfer credit. Each re-parse says
     whether its replacement matched, so a miss can't pass. */
  const gr = await page.evaluate(() => { const t = window.__dprRaw.text, out = {};
    const run = (re, rep, code) => { const t2 = t.replace(re, rep); const r = TCPL.dprParse(t2); const x = r.rows.find(y => y.code === code); return { hit: t2 !== t, x }; };
    ['WU', 'NP', 'AU', 'RP', 'P'].forEach(g => { const { hit, x } = run(/(Business Statistics\\s+)W(?=\\s)/g, '$1' + g, 'BUS 212'); out[g] = hit && x ? [!!x._fail, !!x.pick, !!x._open, !!x._prov] : null; });
    { const { hit, x } = run(/(Introduction to Planting Design\\s+)A(?=\\s)/g, '$1IP', 'LA 222'); out.IP = hit && x ? [!!x._open, !!x._fail, String(x._title || x.name || '')] : null; }
    /* a grade on a row with no icon in the term the report was printed in (BUS 3431, Fall 2026, its pictures taken off): a
       posted grade there is transfer credit; WU and AU never are */
    ['WU', 'AU', 'A'].forEach(g => { const { hit, x } = run(/(Security Analysis)\\s+4\\.50[^\\n]*/g, '$1   ' + g + '   4.50', 'BUS 3431'); out['post' + g] = hit && x ? !!x._xfer : null; });
    plSync(); return out; });
  ok(['WU', 'NP', 'AU'].every(g => JSON.stringify(gr[g]) === '[true,false,false,false]'), 'found: WU, NP and AU are grades that didn’t pass — read, not picked, not “being taken”', gr);
  ok(JSON.stringify(gr.RP) === '[true,false,false,true]' && JSON.stringify(gr.P) === '[false,true,false,false]', 'found: RP (grade pending) isn’t saved but is marked pending; P is a pass, picked', [gr.RP, gr.P]);
  ok(gr.IP && gr.IP[0] === true && gr.IP[1] === false && !/\\bIP$/.test(gr.IP[2]), 'found: “IP” in the grade column is in progress, not part of the title', gr.IP);
  ok(gr.postA === true && gr.postWU === false && gr.postAU === false, 'found: a grade posted in the printing term is transfer credit — never a WU or an AU', [gr.postA, gr.postWU, gr.postAU]);""", 'raw'),
])

# Report wins: a class an older import saved that the new report shows NOT passed comes off, and the list says why.
# The "N transfer" pill never counts a transfer row that wasn't passed.
TESTS = r'''/* (Sonnet review, 2026-10-12) report wins never keeps a class the report shows not passed */
tests.dprCorpusStaleFail = async () => {
  const me = FX.ME.id;
  const T = Object.assign({}, XFER_T('Business Administration', 'Senior'), { class_history: [
    { user_id: me, code: 'BUS 2207', term: 'Spring', year: 2025, professor: null },     // the F, saved by an older import
    { user_id: me, code: 'BUS 4401', term: 'Winter', year: 2025, professor: null }] }); // passed (an earlier term): stays
  const { page, close, log } = await openApp({ tables: T, height: 2600 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await toPastTab(page);
  await page.locator('input[data-in="dprfile"]').first().setInputFiles('files/dpr-corpus-found.pdf');
  for (let i = 0; i < 30 && !(await page.locator('#sheet .dr-h1, #sheet .tc-err').count()); i++) await tick(page, 500);
  const rc = await page.evaluate(() => (UI.dpr.rc || []).map(x => x.kind + ':' + x.code + ':' + x.why));
  ok(rc.some(s => /^hist:BUS 2207:On your account as Spring 2025 · your report shows it not passed$/.test(s)) && !rc.some(s => /BUS 4401/.test(s)), 'report wins: an F an older import saved comes off — “your report shows it not passed”; a passed class stays', rc);
  await saveReport(page);
  const del = log.writes.filter(w => w.m === 'DELETE' && w.table === 'class_history').map(w => decodeURIComponent(w.query));
  ok(del.some(q => /code=eq\.BUS\+2207/.test(q)) && !del.some(q => /BUS\+4401/.test(q)), 'report wins: saving deletes it', del);
  /* a failed attempt with a passed retake later: the failed term's row comes off naming the retake; RP (grade pending) keeps its class */
  const st = await page.evaluate(() => { const keep = TC.myHistory;
    TC.myHistory = [{ code: 'BUS 2207', term: 'Spring', year: 2025 }, { code: 'BUS 2207', term: 'Fall', year: 2025 }, { code: 'BUS 4463', term: 'Spring', year: 2025 }];
    const r = { rows: [{ code: 'BUS 207', cur: 'BUS 2207', term: 'Spring', year: 2025, _fail: true }, { code: 'BUS 207', cur: 'BUS 2207', term: 'Fall', year: 2025 }, { code: 'BUS 463', cur: 'BUS 4463', term: 'Spring', year: 2025, _fail: true, _prov: true }] };
    const out = dprStale(r).filter(x => x.kind === 'hist').map(x => x.code + ' ' + x.h.term + ': ' + x.why); TC.myHistory = keep; return out; });
  ok(JSON.stringify(st) === '["BUS 2207 Spring: On your account as Spring 2025 · your report has it Fall 2025"]', 'report wins: an F retaken and passed comes off naming the retake’s term; the passed retake and an RP stay', st);
  const x = await page.evaluate(() => dprCounts({ rows: [{ _xfer: true }, { _xfer: true, _fail: true }, { _xfer: true, flag: true }] }).xfer);
  ok(x === 1, 'transfer pill: counts transfer credit you have — never a transfer row not passed (or flagged)', x);
  ok(log.errors.length === 0, 'report wins (fail): no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [("tests.dprStressQuarter = async () => {", TESTS + "tests.dprStressQuarter = async () => {", 'tests')])

MUT = r'''  ["review: a failed row on the report keeps an old saved F", "rows = all.filter(x => !x._fail || x._prov);", "rows = all;", "dprCorpusStaleFail"],
  ["review: an RP row (grade pending) doesn't keep its class", "rows = all.filter(x => !x._fail || x._prov);", "rows = all.filter(x => !x._fail);", "dprCorpusStaleFail"],
  ["review: a failed attempt said not passed though it was retaken", "const bad = !other && all.some(", "const bad = all.some(", "dprCorpusStaleFail"],
  ["review: no reason given for a failed class coming off", "const why = bad ? `On your account ${at} · your report shows it not passed` : other ?", "const why = other ?", "dprCorpusStaleFail"],
  ["review: the transfer pill counts a transfer not passed", "filter(x => x._xfer && !x.flag && !x._fail).length;", "filter(x => x._xfer && !x.flag).length;", "dprCorpusStaleFail"],
  ["review: WU/NP/AU not read as grades", "F|CR|NC|W|WU|P|NP|AU|IC|RP|333|[1-7]00)$/;   /* P, WU", "F|CR|NC|W|P|IC|RP|333|[1-7]00)$/;   /* P, WU", "dprCorpusFound", "planner"],
  ["review: P not read as a grade", "F|CR|NC|W|WU|P|NP|AU|IC|RP|333|[1-7]00)$/;   /* P, WU", "F|CR|NC|W|WU|NP|AU|IC|RP|333|[1-7]00)$/;   /* P, WU", "dprCorpusFound", "planner"],
  ["review: WU/AU posted as transfer credit in a running term", "!/^(?:W|WU|AU|IC|RP)$/.test(gradeTok);", "!/^(?:W|IC|RP)$/.test(gradeTok);", "dprCorpusFound", "planner"],
  ["review: RP not marked pending", " _prov:gradeTok==='RP',", " _prov:false,", "dprCorpusFound", "planner"],
  ["review: IP in the grade column joins the title", "    if(gradeTok==='IP')gradeTok='';", "", "dprCorpusFound", "planner"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants'),
  # re-aimed: fix 8 changed the grade list this mutant anchors on (same mutation: drop the [1-7]00 transfer grades)
  ('''"var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333|[1-7]00)$/;", "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333)$/;", "dprTransferFirst"''',
   '''"var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|WU|P|NP|AU|IC|RP|333|[1-7]00)$/;", "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|WU|P|NP|AU|IC|RP|333)$/;", "dprTransferFirst"''', 'reaim 300')])
print('edit-tests-dpr-corpus-review: dprCorpusFound +7 checks, dprCorpusStaleFail, 10 mutants, 1 re-aimed')
