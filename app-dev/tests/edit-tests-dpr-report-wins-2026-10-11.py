#!/usr/bin/env python3
"""Test for dpr-report-wins-2026-10-11.py. Run AFTER edit-tests-dpr-short-ge-heads-2026-10-11.py.
Usage: python3 edit-tests-dpr-report-wins-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
if 'tests.dprReportWins' not in S:
    a = "\nconst names = Object.keys(tests).filter(n => !only || n === only);"
    if S.count(a) != 1: sys.exit('report wins: anchor')
    S = S.replace(a, r"""
/* (2026-10-11) Tate's account, as older imports left it: BUS 3431 under Fall 2025 (he's taking it now), BUS 3346 under the
   wrong term, credit no report lists (BUS 4446, CHEM 1110), credit with no term (BUS 4401), a class in this term's My Classes
   he isn't taking (BUS 3440). Re-reading the report lists each, checked, with why; what he unchecks stays; "See my plan" takes
   the rest off before saving, so the account matches the report. */
tests.dprReportWins = async () => {
  const me = FX.ME.id, ab = '🌍';
  const T = Object.assign({}, XFER_T('Business Administration', 'Senior'), {
    class_history: [
      { user_id: me, code: 'BUS 3431', term: 'Fall', year: 2025, professor: null },
      { user_id: me, code: 'BUS 3346', term: 'Spring', year: 2024, professor: null },
      { user_id: me, code: 'ECON 2040', term: 'Winter', year: 2024, professor: 'Lee' },
      { user_id: me, code: 'BUS 4446', term: 'Fall', year: 2025, professor: ab },
      { user_id: me, code: 'BUS 4401', term: null, year: null, professor: ab },
      { user_id: me, code: 'CHEM 1110', term: null, year: null, professor: ab }],
    saved_classes: FX.TABLES.saved_classes.filter(r => r.user_id !== me).concat([{ user_id: me, term: '2268', code: 'BUS 3431' }, { user_id: me, term: '2268', code: 'BUS 3440' }]) });
  const { page, close, log } = await openApp({ tables: T, height: 2600 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await toPastTab(page);
  await page.locator('input[data-in="dprfile"]').first().setInputFiles('files/dpr-stress-quarter.pdf');
  for (let i = 0; i < 30 && !(await page.locator('#sheet .dr-h1, #sheet .tc-err').count()); i++) await tick(page, 500);
  const rc = await page.evaluate(() => (UI.dpr.rc || []).map(x => x.kind + ':' + x.code + ':' + x.why));
  const has = (k, c, re) => rc.some(s => s.startsWith(k + ':' + c + ':') && re.test(s));
  ok(rc.length === 6 && has('hist', 'BUS 3431', /as Fall 2025 · your report has it Fall 2026 \(this term\)/) && has('hist', 'BUS 3346', /as Spring 2024 · your report has it Fall 2024/) && has('hist', 'BUS 4446', /Credit on your account · not on your report/) && has('hist', 'BUS 4401', /with no term · your report has it Fall 2025/) && has('hist', 'CHEM 1110', /not on your report/) && has('now', 'BUS 3440', /My Classes for Fall 2026 · your report doesn’t show you taking it/),
    'report wins: what’s on the account but not on the report — the wrong term (BUS 3431, BUS 3346), credit it doesn’t list (BUS 4446, CHEM 1110), credit it dates (BUS 4401), a class this term it doesn’t show (BUS 3440) — each with why; ECON 2040 (same term) isn’t', rc);
  const pk = await page.evaluate(() => Object.fromEntries(UI.dpr.rows.filter(x => /BUS 3346|ECON 2040|BUS 3431/.test(x.cur)).map(x => [x.cur, [!!x.already, !!x.pick]])));
  ok(JSON.stringify(pk['BUS 3346']) === '[false,true]' && JSON.stringify(pk['ECON 2040']) === '[true,false]', 'report wins: “already on your record” is the same class in the same term — BUS 3346 under another term is added, ECON 2040 isn’t added twice', pk);
  const card = await page.evaluate(() => { const c = document.querySelector('#sheet .dr-rc'); return c && { h: c.querySelector('.dr-rch').innerText, on: c.querySelectorAll('.dr-rcr[aria-pressed="true"]').length, all: c.querySelectorAll('.dr-rcr').length, after: !!c.nextElementSibling && !!c.parentElement.querySelector('[data-a="dprSave"]') }; });
  ok(card && card.h === '6 on your account, not on your report' && card.on === 6 && card.all === 6, 'report wins: the report-read sheet shows them, all checked', card);
  await click(page, '#sheet .dr-rcr[data-x^="h:BUS 4446"]'); await click(page, '#sheet .dr-rcr[data-x^="h:CHEM 1110"]');
  const on = await page.evaluate(() => [document.querySelectorAll('#sheet .dr-rcr[aria-pressed="true"]').length, document.querySelector('#sheet .dr-rcr[data-x^="h:BUS 4446"]').getAttribute('aria-pressed')]);
  ok(on[0] === 4 && on[1] === 'false', 'report wins: a tap unchecks one to keep it', on);
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  const del = log.writes.filter(w => w.m === 'DELETE').map(w => w.table + ' ' + decodeURIComponent(w.query).replace(/^\?/, '').replace('user_id=eq.' + me + '&', 'ME&'));
  ok(del.length === 5 && del.includes('class_history ME&code=eq.BUS+3431&term=eq.Fall&year=eq.2025') && del.includes('class_history ME&code=eq.BUS+3346&term=eq.Spring&year=eq.2024') && del.includes('class_history ME&code=eq.BUS+4401&term=is.null&year=is.null') && del.includes('saved_classes ME&term=eq.2268&code=eq.BUS+3440') && del.includes('my_sections ME&term=eq.2268&code=eq.BUS+3440'),
    'report wins: saving takes the checked ones off — that row, that term, only that user — and leaves the unchecked', del);
  const st = await page.evaluate(() => ({ h: (TC.myHistory || []).map(h => h.code + ' ' + (h.term || '-') + ' ' + (h.year || '-')), now: [...nowCodes()].sort(), toast: (document.getElementById('toast') || {}).textContent || '' }));
  ok(st.h.includes('BUS 3346 Fall 2024') && !st.h.includes('BUS 3346 Spring 2024') && st.h.includes('BUS 4401 Fall 2025') && !st.h.includes('BUS 4401 - -') && !st.h.some(s => /^BUS 3431/.test(s)) && st.h.includes('BUS 4446 Fall 2025') && st.h.includes('CHEM 1110 - -') && st.h.filter(s => s === 'ECON 2040 Winter 2024').length === 1,
    'report wins: the account then matches the report — BUS 3346 in Fall 2024, BUS 4401 dated Fall 2025, BUS 3431 not a past class; what was kept, kept', st.h);
  ok(JSON.stringify(st.now) === '["BUS 3431","BUS 3438","BUS 4442","UNIV 4401"]', 'report wins: this term’s My Classes are what the report shows you taking (BUS 3440 off; BUS 3431 kept, BUS 3438 and BUS 4442 added)', st.now);
  ok(/Took 4 off your account so it matches your report/.test(st.toast), 'report wins: it says what it took off', st.toast);
  ok(await page.evaluate(() => { const r = UI.dpr || {}; return !(r.rc || []).length; }), 'report wins: nothing listed after saving');
  /* every class, by term: credit earned abroad after the first term sits in its term; credit with no term sits apart */
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.sheet = null; render(true); }); await tick(page, 400); await toPastTab(page);
  await page.evaluate(() => { UI.pcTerms = true; UI.pcTermYr = { 2025: true, x: true }; render(true); }); await tick(page, 600);
  const tv = await page.evaluate(() => { const rows = [...document.querySelectorAll('.pc-tv .pc-ty')]; const yr = rows.find(c => /2025–26/.test(c.innerText)), x = rows.find(c => /Credit from other schools/.test(c.innerText)), now = rows.find(c => /· now/.test(c.innerText));
    const r4446 = yr && [...yr.querySelectorAll('.pc-trow')].find(b => /BUS 4446/.test(b.innerText));
    return { y: !!r4446 && /Other school/.test(r4446.innerText), x: x && x.innerText.replace(/\s+/g, ' '), now: now && [...now.querySelectorAll('.pc-cc')].map(e => e.innerText) }; });
  ok(tv.y && tv.x && /1 · AP, test and transfer credit/.test(tv.x) && /CHEM 1110/.test(tv.x) && !/BUS 4446|BUS 4401/.test(tv.x), 'by term: credit earned after your first term (BUS 4446, Fall 2025) sits in that term, marked Other school; credit with no term sits apart', tv);
  ok(tv.now && tv.now.includes('BUS 3431'), 'by term: this term shows the class you’re taking', tv.now);
  /* a report that doesn't show this term never touches this term's My Classes */
  const noNow = await page.evaluate(() => { const r = { rows: (UI.dpr ? UI.dpr.rows : []).filter(x => !x._now) }; return dprStale(r).filter(x => x.kind === 'now').length; });
  ok(noNow === 0, 'report wins: a report with nothing this term leaves this term’s My Classes alone', noNow);
  ok(log.errors.length === 0, 'report wins: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""")
    open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
IX = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("report wins: already by number alone", "&& (!h.term || !h.year || (h.term === x.term && String(h.year) === String(x.year))));\n    x.pick = !x.already;", "&& true);\n    x.pick = !x.already;", "dprReportWins"),
  ("report wins: nothing listed", "  const out = [];\n  (TC.myHistory || []).forEach(h => {", "  const out = [];\n  [].forEach(h => {", "dprReportWins"),
  ("report wins: undated credit kept", ": !(x.term && x.year)))) return;", ": true))) return;", "dprReportWins"),
  ("report wins: this term untouched", "  if (nowRep.length) {", "  if (false) {", "dprReportWins"),
  ("report wins: this term listed without the report", "  if (nowRep.length) {", "  if (true) {", "dprReportWins"),
  ("report wins: unchecked still taken off", "const drop = (r.rc || []).filter(x => !(r.rcOff || new Set()).has(x.key));", "const drop = (r.rc || []);", "dprReportWins"),
  ("report wins: never taken off", "      if (drop.length) { const e0 = await TC.dropStale(drop);", "      if (false) { const e0 = await TC.dropStale(drop);", "dprReportWins"),
  ("report wins: any term deleted", "q = x.h.term == null ? q.is('term', null) : q.eq('term', x.h.term);", "", "dprReportWins"),
  ("report wins: not recomputed after", "if (e0) { r.saveErr = e0; return; } dprRecompute(r);", "if (e0) { r.saveErr = e0; return; }", "dprReportWins"),
  ("by term: abroad credit apart", "const away = hist.filter(h => pcXfer(h) && h.term && +h.year && tk(h) > k0)", "const away = hist.filter(h => false)", "dprReportWins"),
  ("by term: no Other school chip", "(h.oth ? '<i class=\"d\">Other school</i>' : '')", "''", "dprReportWins"),
]
for n, a, b, t in MUT:
    if IX.count(a) != 1: sys.exit(f'mutant anchor {n}: {IX.count(a)}x')
if 'edit-tests-dpr-report-wins-2026-10-11.py' not in T:
    k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
    if T.count(k) != 1: sys.exit('mutate anchor')
    T = T.replace(k, "\n  /* the report wins over the account (2026-10-11; edit-tests-dpr-report-wins-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T)

# pastKinds, re-aimed: credit earned abroad after the first term (ART 3TC1, Fall 2025) now sits in its term; credit from before
# Cal Poly (HIST 1206, Summer 2024) sits apart
S = open(P, encoding='utf-8').read()
RE = [
  ("{ code: 'ART 3TC1', term: 'Fall', year: 2025, professor: TCPL.abroadMark }];", "{ code: 'ART 3TC1', term: 'Fall', year: 2025, professor: TCPL.abroadMark }, { code: 'HIST 1206', term: 'Summer', year: 2024, professor: TCPL.abroadMark }];"),
  ("tv.ys.some(y => /^Year 2 · 2025–26 Quarters · 1 class$/.test(y)) && /^Transfer and AP credit 1 · not tied to a term you took$/.test(tv.ys[tv.ys.length - 1]),\n    'by term: Year 1 is your first Cal Poly year (Fall 2024), each year says quarters or semesters, and transfer credit sits apart', tv.ys);",
   "tv.ys.some(y => /^Year 2 · 2025–26 Quarters · 2 classes$/.test(y)) && /^Credit from other schools 1 · before Cal Poly$/.test(tv.ys[tv.ys.length - 1]),\n    'by term: Year 1 is your first Cal Poly year (Fall 2024), each year says quarters or semesters; credit earned abroad since (Fall 2025) sits in its term, credit from before Cal Poly sits apart', tv.ys);"),
  ("tv2.rows.some(r => /^ART 3TC1 GE C1$/.test(r))", "tv2.rows.some(r => /^ART 3TC1 Other school GE C1$/.test(r)) && tv2.rows.some(r => /^HIST 1206\\b.*Units only$/.test(r)) && tv2.th.includes('FALL 2025 quarter')"),
]
for a, b in RE:
    if b in S: continue
    if S.count(a) != 1: sys.exit('pastKinds re-aim: ' + a[:50])
    S = S.replace(a, b)
open(P, 'w', encoding='utf-8').write(S)
T = open(M, encoding='utf-8').read()
oa = '["by term: transfer in a term", "const hist = pcHist(), xfer = hist.filter(pcXfer), real = hist.filter(h => !pcXfer(h) && h.term && +h.year);", "const hist = pcHist(), xfer = [], real = hist.filter(h => h.term && +h.year);", "pastKinds", null]'
na = '["by term: transfer in a term", "const xfer = hist.filter(h => pcXfer(h) && !(h.term && +h.year && tk(h) > k0)), real = real0.concat(away);", "const xfer = [], real = hist.filter(h => h.term && +h.year);", "pastKinds", null]'
if oa in T: T = T.replace(oa, na)
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-dpr-report-wins: done')
