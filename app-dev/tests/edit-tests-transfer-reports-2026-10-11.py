#!/usr/bin/env python3
"""Tests for transfer-reports-2026-10-11.py (transfer students' reports). Replayable.
  python3 edit-tests-transfer-reports-2026-10-11.py
1. check-dpr-corpus.mjs reads a report the way the app does (dprDocText: text and the transfer icon), and a key
   can also say which classes are transfer credit and which are being taken ("transfer": [...], "taking": [...]).
2. check-app.mjs: the synthetic transfer reports (files/make-dpr-transfer.py) through the real app."""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue   # already applied (an insertion keeps its anchor, so test the new text)
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('check-dpr-corpus.mjs', [
 ("""     <name>.key.json  { "counts": {satisfied, not, in_progress, unknown}, "open": ["…line words…"], "units": [used, needed, required] }""",
  """     <name>.key.json  { "counts": {satisfied, not, in_progress, unknown}, "open": ["…line words…"], "units": [used, needed, required],
                        "transfer": ["SUBJ NNNN", …], "taking": ["SUBJ NNNN", …] }   (the last two optional: the classes the
                        reader calls transfer/test credit, and the ungraded classes in the newest term — by the codes the app saves)""", 'doc'),
 ("""    const doc = await lib.getDocument({ data: bytes }).promise; let text = '';
    for (let p = 1; p <= doc.numPages; p++) { const pg = await doc.getPage(p); const tc = await pg.getTextContent(); text += '\\n\\n' + TCPL.pdfItemsToText(tc && tc.items); }
    const parsed = TCPL.dprParse(text), a = parsed.audit || {};
    return { text, ok: !!parsed.ok, rows: (parsed.rows || []).length, program: parsed.program || null, audit: a,""",
  """    /* exactly as the app reads it (readDpr): the text and the report's transfer icon */
    const doc = await lib.getDocument({ data: bytes, isOffscreenCanvasSupported: false }).promise; const text = await dprDocText(doc);
    const parsed = TCPL.dprParse(text), a = parsed.audit || {}, R = parsed.rows || [];
    return { text, ok: !!parsed.ok, rows: R.length, program: parsed.program || null, audit: a,
      transfer: [...new Set(R.filter(x => x._xfer).map(x => x.cur))].sort(), taking: [...new Set(R.filter(x => x._now).map(x => x.cur))].sort(),""", 'read'),
 ("""  const got = { counts: (r.audit && r.audit.counts) || null, open: r.open.slice().sort(), units: r.units };""",
  """  const got = { counts: (r.audit && r.audit.counts) || null, open: r.open.slice().sort(), units: r.units, transfer: r.transfer, taking: r.taking };""", 'got'),
 ("""    if (key.units && JSON.stringify(key.units) !== JSON.stringify(got.units)) diff.push(`units ${JSON.stringify(got.units)} ≠ key ${JSON.stringify(key.units)}`);""",
  """    if (key.units && JSON.stringify(key.units) !== JSON.stringify(got.units)) diff.push(`units ${JSON.stringify(got.units)} ≠ key ${JSON.stringify(key.units)}`);
    for (const f of ['transfer', 'taking']) if (key[f]) { const k = key[f].slice().sort(); if (JSON.stringify(k) !== JSON.stringify(got[f])) diff.push(`${f}: missing [${k.filter(x => !got[f].includes(x)).join(', ')}], extra [${got[f].filter(x => !k.includes(x)).join(', ')}]`); }""", 'diff'),
 ("""  console.log(`${f}: ${r.rows} classes · ${JSON.stringify(got.counts)} · ${got.open.length} open · ${verdict}""",
  """  console.log(`${f}: ${r.rows} classes · ${got.transfer.length} transfer · ${got.taking.length} taking · ${JSON.stringify(got.counts)} · ${got.open.length} open · ${verdict}""", 'print'),
])
print('edit-tests-transfer-reports: corpus runner done')

TESTS = r'''/* ============ Transfer students' reports (Tate, 2026-10-11) ============
   A friend's real report — a junior in his first term after transferring — and the app said "only 7 of his
   requirements fulfilled". Every community-college and exam class printed in "2026 Fall" WITH a grade (some
   "300"/"400"), and only the report's icon says they're transfer credit. Synthetic reports in the same shape
   (files/make-dpr-transfer.py: invented people, classes and grades — never a real report): */
const XFER_T = (major, standing) => Object.assign({}, NOREC(), { planner_prefs: [],
  saved_classes: FX.TABLES.saved_classes.filter(r => r.user_id !== FX.ME.id), my_sections: FX.TABLES.my_sections.filter(r => r.user_id !== FX.ME.id),
  profiles: FX.TABLES.profiles.map(p => p.id === FX.ME.id ? Object.assign({}, p, { major, class_standing: standing }) : p) });
const uploadFile = async (page, file) => { await page.locator('.tc-dpr input[data-in="dprfile"]').first().setInputFiles('files/' + file); for (let i = 0; i < 30 && !(await page.locator('#sheet .dr-h1, #sheet .tc-err').count()); i++) await tick(page, 500); };
const readPills = page => page.evaluate(() => [...document.querySelectorAll('#sheet .dr-pill')].map(p => p.innerText.trim()).join('|'));
const checkRows = async (page, seg) => { await click(page, `[data-a="dprSeg"][data-x="${seg}"]`); await tick(page, 200); return page.evaluate(() => [...document.querySelectorAll('#sheet .dr-row')].map(r => r.innerText.replace(/\s+/g, ' ').trim())); };
const posted = (log, t) => log.writes.filter(w => w.table === t && w.m === 'POST').map(w => w.body).flat();
const xferOf = rows => rows.filter(r => /· transfer$/.test(r)).map(r => r.split(' ').slice(0, 2).join(' ')).sort();

/* 1. His shape: first term after transferring (Environmental Management & Protection, a junior) */
tests.dprTransferFirst = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Environmental Management & Protection', 'Junior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-first.pdf');
  ok(await readPills(page) === '18 filled|12 left|13 transfer', 'transfer, first term: Report read counts the report — 17 Satisfied + 1 in progress = 18 filled, 12 left — and all 13 transfer classes', await readPills(page));
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(cls.length === 16 && JSON.stringify(xferOf(cls)) === JSON.stringify(['BIO 1114', 'BUS 1TR', 'COMS 1102', 'CSC 1TR', 'ECON 2030', 'ENGL 1134', 'ENGL 1T13', 'ES 4A1', 'HIST 4A1', 'MATH 1267', 'MU 1T3A', 'POLS 4AA', 'STAT 1210']) && ['ES 3350', 'NR 1142', 'NR 3308'].every(c => cls.some(r => r.startsWith(c + ' ') && !/transfer/.test(r))),
    'transfer, first term: every graded “2026 Fall” class is transfer credit (its icon, and a grade in a term still running); the 3 ungraded are the ones he’s taking', cls);
  ok(!cls.some(r => /\b[1-7]00\b/.test(r)), 'transfer, first term: a “300” / “400” where a grade goes is never shown as part of a class’s name', cls.filter(r => /\b[1-7]00\b/.test(r)));
  const open = await checkRows(page, 'open');
  ok(open.length === 12 && open.filter(r => /^Pick 1 Major Core Courses - Option\b/.test(r)).length === 1 && !open.some(r => /NR 3319|NR 4402/.test(r)) && open.includes('Conc. Concentration Undeclared'),
    'transfer, first term: “Choose one” with “Option 1 of 2” / “Option 2 of 2” is ONE line to fill; “(2026)” is off the words', open);
  const filled = await checkRows(page, 'filled');
  ok(filled.length === 18 && filled.some(r => /^USCP U\.S\. Cultural Pluralism .* in progress$/.test(r)), 'transfer, first term: a “Not Satisfied” line whose own table lists a class he’s taking now (USCP, ES 3350) is in progress — transfer credit doesn’t hide this term', filled.filter(r => /USCP/.test(r)));
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  const hist = posted(log, 'class_history'), mine = posted(log, 'saved_classes');
  ok(hist.length === 13 && hist.every(r => r.professor === '🌍' && r.term === 'Fall' && r.year === 2026), 'transfer, first term: the 13 transfer classes go to the record, each marked transfer credit (no professor to ask about)', hist.map(r => [r.code, r.professor]));
  ok(JSON.stringify(mine.map(r => r.code).sort()) === JSON.stringify(['ES 3350', 'NR 1142', 'NR 3308']), 'transfer, first term: My Classes gets only the 3 ungraded classes — never ENGL 1134, MATH 1267 or STAT 1210 (they printed “300”/“400”)', mine);
  ok(await page.evaluate(() => !UI.sheet || UI.sheet.type !== 'pcWho'), 'transfer, first term: no “Who taught these?” — nothing on the record is a Cal Poly class');
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.sheet = null; render(true); });
  await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 1500); await openYears(page);
  const sum = await page.evaluate(() => { const c = document.querySelector('.pc-sum'); return c && { num: c.querySelector('.pc-num').innerText.replace(/\s+/g, ' ').trim(), link: (c.querySelector('.pc-link') || {}).innerText || '', bar: c.querySelector('.pc-bar').getAttribute('aria-label') }; });
  ok(sum && sum.num === '18 of 30 filled' && sum.bar === '18 of 30 filled' && /Degree Progress Report\s*12 left/.test(sum.link), 'transfer, first term: Past classes says the report’s “18 of 30 filled” (the flowchart can’t see transfer credit)', sum);
  const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-row')].map(r => ({ st: r.className.replace('pc-row', '').trim(), main: ((r.querySelector('.pc-main') || {}).innerText || '').replace(/\s+/g, ' ').trim(), pf: (r.querySelector('.pc-pf') || {}).innerText || '', add: !!r.querySelector('.pc-add') })));
  const g1b = rows.find(r => /^GE Area 1B$/.test(r.main)), stat = rows.find(r => /^STAT 1110\b/.test(r.main));
  ok(g1b && g1b.st === 'done' && g1b.pf === 'On your report' && stat && stat.st === 'done' && stat.pf === 'On your report', 'transfer, first term: a flowchart spot the report says is Satisfied (GE 1B, STAT 1110) is filled, “On your report”', { g1b, stat });
  ok(!(await page.locator('#scroll .pc-add').count()), 'transfer, first term: no “+ Professor” anywhere — transfer credit has no Cal Poly professor');
  await page.evaluate(() => { UI.sheet = null; render(true); document.getElementById('scroll').scrollTop = 0; }); await tick(page, 600); await click(page, '[data-a="tab"][data-x="home"]'); await click(page, '.homehdr .me-btn'); await tick(page, 800);
  const me = await page.evaluate(() => [...document.querySelectorAll('.merow')].map(r => r.innerText.replace(/\s+/g, ' ').trim()).find(t => /requirements filled/.test(t)));
  ok(me === '18 of 30 requirements filled Environmental Management & Protection · 1 in progress', 'transfer, first term: the profile’s row is the report’s count too', me);
  ok(log.errors.length === 0, 'transfer, first term: no page errors', log.errors);
  await close();
};

/* 2. A senior who transferred a year ago: his transfer credit prints in 2025 Fall with letter grades, beside the
   Cal Poly classes he took that term — only the report's icons tell them apart. Exam credit: "CR" and no icon. */
tests.dprTransferContinuing = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-continuing.pdf');
  ok(await readPills(page) === '17 filled|6 left|8 transfer', 'transfer, a year on: 14 Satisfied + 3 in progress = 17 filled, 6 left, 8 transfer', await readPills(page));
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(cls.length === 17 && JSON.stringify(xferOf(cls)) === JSON.stringify(['AP 300', 'BUS 1TR', 'BUS 2201', 'COMS 1101', 'ECON 2030', 'ENGL 1134', 'MATH 1221', 'PHIL 1T1B']),
    'transfer, a year on: the classes the report draws with the transfer icon (and exam credit drawn with none) are transfer — the Cal Poly classes of the same term are not', cls);
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  const hist = posted(log, 'class_history'), mine = posted(log, 'saved_classes');
  const x = hist.filter(r => r.professor === '🌍').map(r => r.code).sort(), cp = hist.filter(r => r.professor == null).map(r => r.code).sort();
  ok(hist.length === 14 && JSON.stringify(x) === JSON.stringify(['AP 300', 'BUS 1TR', 'BUS 2201', 'COMS 1101', 'ECON 2030', 'ENGL 1134', 'MATH 1221', 'PHIL 1T1B']) && JSON.stringify(cp) === JSON.stringify(['BUS 2207', 'BUS 2212', 'BUS 3346', 'BUS 3387', 'BUS 3391', 'STAT 2170']),
    'transfer, a year on: the record keeps 8 transfer (marked) and 6 Cal Poly classes', { x, cp });
  ok(JSON.stringify(mine.map(r => r.code).sort()) === JSON.stringify(['BUS 3431', 'BUS 3438', 'BUS 4401']), 'transfer, a year on: My Classes gets the 3 he’s taking — not this term’s study-abroad placeholder (AP 300, no grade, transfer icon)', mine);
  const who = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys.slice().sort() : null);
  ok(JSON.stringify(who) === JSON.stringify(['BUS 2207|Fall|2025', 'BUS 2212|Fall|2025', 'BUS 3346|Spring|2026', 'BUS 3387|Spring|2026', 'BUS 3391|Spring|2026', 'STAT 2170|Fall|2025']),
    'transfer, a year on: “Who taught these?” asks only about his Cal Poly classes — not BUS 2201 or MATH 1221, which he took at a community college the same term', who);
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.sheet = null; S.schedTab = 'past'; render(true); }); await tick(page, 1500); await openYears(page);
  const num = await page.evaluate(() => (document.querySelector('.pc-sum .pc-num') || {}).innerText);
  ok(/^18 of 23\s*filled$/.test(String(num).trim()), 'transfer, a year on: “18 of 23 filled” — the report’s 17, and BUS 4401 now that it’s in his classes this term', num);
  const add = await page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row, #scroll .pc-orow')].map(r => [((r.querySelector('.pc-cc') || {}).innerText || '').trim(), !!r.querySelector('.pc-add')]).filter(([c]) => c));
  const has = c => add.find(([k]) => k === c);
  ok(has('BUS 2201') && !has('BUS 2201')[1] && has('MATH 1221') && !has('MATH 1221')[1] && has('BUS 2212') && has('BUS 2212')[1], 'transfer, a year on: “+ Professor” on his Cal Poly classes, never on his transfer ones', add);
  ok(log.errors.length === 0, 'transfer, a year on: no page errors', log.errors);
  await close();
};

/* 2b. The same senior's report with Cal Poly's check drawn as a picture too big to be an icon: the page's pictures
   can't all be matched, so nothing is called "no icon" (ECON 2030's "CR" stays as it is) — the arrows still count */
tests.dprTransferPartial = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-partial.pdf');
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(cls.length === 17 && JSON.stringify(xferOf(cls)) === JSON.stringify(['AP 300', 'BUS 1TR', 'BUS 2201', 'COMS 1101', 'ENGL 1134', 'MATH 1221', 'PHIL 1T1B']) && cls.some(r => /^ECON 2030 /.test(r) && !/transfer/.test(r)),
    'partial icons: rows wearing the transfer icon are still transfer; with pictures the app couldn’t match on the page, a row isn’t called “no icon” (ECON 2030 stays a class)', cls);
  ok(log.errors.length === 0, 'partial icons: no page errors', log.errors);
  await close();
};

/* 2c. Review 2026-10-11: pictures the legend doesn't name, a legend that can't be trusted, pictures inside forms */
tests.dprTransferOddLegend = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Environmental Management & Protection', 'Junior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-oddlegend.pdf');
  ok(await readPills(page) === '18 filled|12 left|13 transfer', 'odd legend: the table’s arrows aren’t the legend’s picture — they’re not taken for Cal Poly’s, and the words still find all 13 transfer classes', await readPills(page));
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  ok(JSON.stringify(posted(log, 'saved_classes').map(r => r.code).sort()) === JSON.stringify(['ES 3350', 'NR 1142', 'NR 3308']), 'odd legend: My Classes gets only the 3 ungraded classes (no “300”/“400” class filed as this term’s)', posted(log, 'saved_classes'));
  ok(log.errors.length === 0, 'odd legend: no page errors', log.errors);
  await close();
};
tests.dprTransferBadLegend = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-badlegend.pdf');
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(JSON.stringify(xferOf(cls)) === JSON.stringify(['AP 300', 'BUS 1TR', 'ENGL 1134', 'PHIL 1T1B']), 'bad legend: a legend that gives the transfer label Cal Poly’s own picture isn’t used — only the words decide, and no Cal Poly class is called transfer', cls);
  ok(log.errors.length === 0, 'bad legend: no page errors', log.errors);
  await close();
};
tests.dprTransferForm = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-form.pdf');
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(JSON.stringify(xferOf(cls)) === JSON.stringify(['AP 300', 'BUS 1TR', 'BUS 2201', 'COMS 1101', 'ECON 2030', 'ENGL 1134', 'MATH 1221', 'PHIL 1T1B']), 'forms: icons drawn inside a form with its own matrix still land on their rows', cls);
  ok(log.errors.length === 0, 'forms: no page errors', log.errors);
  await close();
};

/* 3. The same first-term report with no pictures (a copy that lost them): the words are enough — a grade in a term
   still running when it was printed, and an articulation number (PHIL 1T1B, Summer 2025) */
tests.dprTransferNoIcons = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Environmental Management & Protection', 'Junior') });
  await toPlanner(page); await uploadFile(page, 'dpr-transfer-noicons.pdf');
  ok(await readPills(page) === '18 filled|12 left|14 transfer', 'no icons: the same counts, and 14 transfer (13 + the Summer 2025 PHIL 1T1B)', await readPills(page));
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(xferOf(cls).length === 14 && xferOf(cls).includes('PHIL 1T1B') && xferOf(cls).includes('BIO 1114') && ['ES 3350', 'NR 1142', 'NR 3308'].every(c => cls.some(r => r.startsWith(c + ' ') && !/transfer/.test(r))), 'no icons: graded classes in the running term and an articulation number are transfer; the 3 ungraded are taking', cls);
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  ok(posted(log, 'class_history').length === 14 && posted(log, 'class_history').every(r => r.professor === '🌍') && posted(log, 'saved_classes').length === 3, 'no icons: 14 transfer on the record, 3 in My Classes', posted(log, 'saved_classes'));
  ok(log.errors.length === 0, 'no icons: no page errors', log.errors);
  await close();
};

/* 4. Not a transfer: printed December 20, after Fall's grades posted — graded Fall 2026 is Cal Poly work */
tests.dprFallGraded = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Sophomore') });
  await toPlanner(page); await uploadFile(page, 'dpr-fall-graded.pdf');
  ok(await readPills(page) === '3 filled|2 left', 'after grades post: no transfer pill — nothing on it is transfer credit', await readPills(page));
  await click(page, '[data-a="dprCheck"]');
  const cls = await checkRows(page, 'classes');
  ok(!xferOf(cls).length && cls.some(r => /^BUS 2201 .*Fall 2026$/.test(r)), 'after grades post: Fall 2026’s graded classes are Cal Poly classes', cls);
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  const hist = posted(log, 'class_history');
  ok(hist.length === 6 && hist.every(r => r.professor == null) && hist.some(r => r.code === 'BUS 2201' && r.term === 'Fall' && r.year === 2026), 'after grades post: the 6 finished classes go to the record as Cal Poly classes', hist);
  const who = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys : null);
  ok(who && who.includes('BUS 2201|Fall|2026') && who.includes('COMS 1101|Fall|2026'), 'after grades post: “Who taught these?” asks about Fall 2026’s classes', who);
  ok(log.errors.length === 0, 'after grades post: no page errors', log.errors);
  await close();
};

/* The reader's new rules, one at a time */
tests.dprReaderTransfer = async () => {
  const { page, close } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 }); await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  const r = await page.evaluate(() => {
    const X = TCPL.dprXMark, B = TCPL.dprBMark, it = (s, x, y) => ({ str: s, transform: [1, 0, 0, 1, x, y], width: s.length * 4 });
    const rowsAt = (ys, marks) => TCPL.pdfItemsToText(ys.map((y, i) => it(`2025 Fall ART ${1160 + i} Intro B 3.00`, 44, y)).concat([it('Satisfied: 3 units', 40, 300)]), marks).split('\n');
    const C = TCPL.dprCMark;
    const mk = (a, bare) => { a.bare = bare; return a; };
    const d = TCPL.dprPrinted('Date Printed: October 10, 2026 18:05');
    const p = (printed, rows) => TCPL.dprParse(['Degree Progress Report', printed, 'Course History', ...rows].join('\n')).rows.map(x => [x.cur, x._xfer, x._open, x.name]);
    const audit = TCPL.dprAudit(['MAJOR CORE COURSES (2026)', 'Overall Requirement Not Satisfied: 31 units', '(R797)', 'NR/SS 4431 OR NR 4442', 'Not Satisfied: 3 units', '(R797-80)', 'MAJOR CORE COURSES - OPTION (2026)', 'Not Satisfied: Choose one', '3-4 units', '(R2865)', 'NR 3319 & 3320', 'Not Satisfied: Option 1 of 2', '3 units', '(R2865-10)', 'NR/AGB 3326, NR 4418, or NR 4445', 'Not Satisfied: Option 2 of 2', '3-4 units', '(R2865-20)'].join('\n'), {}, []);
    return {
      xfer: rowsAt([100, 88.6], mk([{ y: 101.8, t: true }], true)), icon: rowsAt([100, 88.6], mk([{ y: 101.8, t: false, c: true }], true)), allIcons: rowsAt([100], mk([{ y: 101.8, t: false, c: true }], true)),
      noneHit: rowsAt([100], mk([{ y: 300 + 1.8, t: false, c: true }], true)), far: rowsAt([100], [{ y: 106.5, t: true }]), X, B, C,
      onlyXfer: rowsAt([100, 88.6], mk([{ y: 101.8, t: true }], true)), offRow: rowsAt([100, 88.6], mk([{ y: 101.8, t: false, c: true }, { y: 88.6 + 1.8 - 5.5, t: false, c: true }], true)),
      notBare: rowsAt([100, 88.6], mk([{ y: 101.8, t: false, c: true }], false)),
      unnamed: rowsAt([100, 88.6], mk([{ y: 101.8, t: false, c: false }], true)),
      parse: (() => { const rows = ln => TCPL.dprParse(['Degree Progress Report', 'Date Printed: October 10, 2026 18:05', 'Course History', ...ln].join('\n')).rows.map(x => [x.cur, x._xfer, x._open, x._now, x.name]);
        return { bareLetter: rows([`2025 Fall BUS 2207 Legal B+ 4.00 ${B}`]), bareCr: rows([`2025 Fall ECON 2030 Microeconomics CR 3.00 ${B}`]),
          cpScore: rows([`2026 Fall ENGR 1000 Senior Project 400 3.00 ${C}`]), cpGraded: rows([`2026 Fall BUS 2201 Financial Accounting A 4.00 ${C}`]),
          w: rows(['2026 Fall BUS 2201 Financial Accounting W 4.00']), apNow: rows([`2026 Fall AP 300 Affiliated Programs Outgoing 12.00 ${X}`, '2026 Fall NR 1142 Environmental Management 4.00']),
          past300: rows(['2024 Fall CHEM 1120 Gen Chem 300 4.00', '2024 Spr BUS 2201 Financial Accounting A 4.00']) }; })(),
      legend: [dprLegendSig([it('Transfer/Test/Other Credit', 338, 482.9)], [{ x: 314, y: 484.6, sig: 'arrow' }, { x: 290, y: 484.6, sig: 'other' }, { x: 44, y: 484.6, sig: 'left' }], /Transfer\s*\/\s*Test/i),
        dprLegendSig([it('Transfer/Test/Other Credit', 338, 482.9)], [{ x: 314, y: 492, sig: 'arrow' }], /Transfer\s*\/\s*Test/i)],
      date: d && [d.getFullYear(), d.getMonth(), d.getDate()], none: TCPL.dprPrinted('no date here'),
      last: (x => x && [x.getFullYear(), x.getMonth(), x.getDate()])(TCPL.dprPrinted('Date Printed: October 1, 2025 10:00\nCourse History\nDate Printed: October 10, 2026 18:05')),
      run: [TCPL.dprTermRunning('Fall', 2026, d), TCPL.dprTermRunning('Fall', 2026, new Date(2026, 11, 20)), TCPL.dprTermRunning('Spring', 2026, d), TCPL.dprTermRunning('Spring', 2027, d), TCPL.dprTermRunning('Fall', 2026, null), TCPL.dprTermRunning('Summer', 2026, new Date(2026, 5, 15)), TCPL.dprTermRunning('Summer', 2026, new Date(2026, 4, 20))],
      oct: p('Date Printed: October 10, 2026 18:05', ['2026 Fall BIO 1114 Plant Diversity A 4.00', '2026 Fall CHEM 1120 Gen Chem 300 4.00', '2026 Fall NR 1142 Environmental Management 4.00']),
      dec: p('Date Printed: December 20, 2026 09:00', ['2026 Fall BIO 1114 Plant Diversity A 4.00']), nodate: p('', ['2026 Fall BIO 1114 Plant Diversity A 4.00']),
      opts: audit.reqs.map(b => [b.code, b.status, b.oneOf, b.label, b.options.join('/')]),
      /* "Choose one" over lines that don't say "Option N of M"; and "Option N of M" lines beside a plain line, with no "Choose one" */
      choose: TCPL.dprAudit(['SUPPORT COURSES - OPTION (2026)', 'Not Satisfied: Choose one', '4 units', '(R2866)', 'BIO 1111 & 1112', 'Not Satisfied: 4 units', '(R2866-10)', 'BIO 1150 or BIO 1151', 'Not Satisfied: 4 units', '(R2866-20)'].join('\n'), {}, []).reqs.map(b => [b.code, b.oneOf, b.options.length]),
      mixed: TCPL.dprAudit(['MATH COURSES (2026)', 'Overall Requirement Not Satisfied: 7 units', '(R620)', 'MATH 1261', 'Not Satisfied: Option 1 of 2', '4 units', '(R620-10)', 'MATH 1221', 'Not Satisfied: Option 2 of 2', '4 units', '(R620-20)', 'STAT 1210', 'Not Satisfied: 3 units', '(R620-30)'].join('\n'), {}, []).reqs.map(b => [b.code, b.oneOf, b.options.join('/')]) };
  });
  ok(r.xfer[0].endsWith(' ' + r.X) && !r.xfer[1].includes(r.X) && !r.xfer[2].includes(r.X), 'reader: a class row wearing the transfer icon (its centre 1.8 above the baseline) ends in the transfer mark — the row below and a verdict line don’t', r.xfer);
  ok(!r.xfer[0].includes(r.B) && !r.xfer[1].includes(r.B), 'reader: with only transfer icons on the page, no row is marked “no icon”', r.xfer);
  ok(r.icon[0].endsWith(' ' + r.C) && !r.icon[0].includes(r.B) && r.icon[1].endsWith(' ' + r.B) && r.allIcons[0].endsWith(' ' + r.C), 'reader: a row wearing Cal Poly’s own icon ends in its mark; on a page whose icons were all read (and some row wore Cal Poly’s), a row wearing none ends in the no-icon mark', r.icon);
  ok(!r.unnamed[0].includes(r.C) && !r.unnamed[0].includes(r.X) && !r.unnamed[1].includes(r.B), 'reader: a picture the legend doesn’t name marks nothing — not Cal Poly’s, and it doesn’t make other rows “no icon”', r.unnamed);
  ok(!r.offRow[1].includes(r.B), 'reader: a picture 5.5pt off a row (not its icon by position) still keeps that row from being called “no icon”', r.offRow);
  ok(!r.notBare[1].includes(r.B), 'reader: on a page with a picture the app couldn’t read, no row is called “no icon”', r.notBare);
  const P = r.parse;
  ok(P.bareLetter[0][1] === false && P.bareCr[0][1] === true, 'reader: no icon makes a row credit only with a credit grade — “CR” yes, a letter grade no', P);
  ok(P.cpScore[0][1] === false && P.cpScore[0][2] === true && P.cpScore[0][3] === true && /400$/.test(P.cpScore[0][4]), 'reader: on a row wearing Cal Poly’s icon, “400” is the end of the title — the class is being taken, not transfer', P.cpScore);
  ok(P.cpGraded[0][1] === false, 'reader: a graded row wearing Cal Poly’s icon is never posted credit, whatever the date', P.cpGraded);
  ok(P.w[0][1] === false, 'reader: a W in the running term (a withdrawal posts mid-term) isn’t posted credit', P.w);
  ok(P.apNow[0][1] === true && P.apNow[0][3] === false && P.apNow[1][3] === true, 'reader: an ungraded transfer placeholder this term (AP 300) isn’t being taken; the ungraded class beside it is', P.apNow);
  ok(P.past300[0][1] === true && P.past300[0][2] === false && P.past300[1][1] === false, 'reader: “300” with no icon in an earlier term is credit (transfer); a letter grade beside it isn’t', P.past300);
  ok(r.legend[0] === 'arrow' && r.legend[1] === null, 'reader: the legend’s transfer picture is the one just left of its label on its line (not one further left, not one off the line)', r.legend);
  ok(!r.noneHit[0].includes(r.B), 'reader: on a page where no class row wears an icon, nothing is marked “no icon”', r.noneHit);
  ok(!r.far[0].includes(r.X), 'reader: an icon 6.5 above a row (the row above’s) isn’t that row’s', r.far);
  ok(JSON.stringify(r.date) === '[2026,9,10]' && r.none === null, 'reader: the date the report was printed', r.date);
  ok(JSON.stringify(r.last) === '[2026,9,10]', 'reader: with two dates (files read together), the last one — the file whose Course History is read', r.last);
  ok(JSON.stringify(r.run) === '[true,false,false,true,false,false,true]', 'reader: a term is still running until its finals — Fall 2026 on Oct 10 yes, on Dec 20 no; Spring 2026 no; Spring 2027 yes; no date, no; Summer 2026 on Jun 15 no, on May 20 yes', r.run);
  ok(JSON.stringify(r.oct) === JSON.stringify([['BIO 1114', true, false, 'BIO 1114'], ['CHEM 1120', true, false, 'CHEM 1120'], ['NR 1142', false, true, 'NR 1142']].map((x, i) => [x[0], x[1], x[2], r.oct[i][3]])) && !r.oct.some(x => /\b300\b/.test(x[3])),
    'reader: printed in October, a graded Fall 2026 class is transfer; “300” is a grade (never part of the name); the ungraded one is being taken', r.oct);
  ok(r.dec[0][1] === false && r.nodate[0][1] === false, 'reader: printed after Fall’s grades (or with no date), a graded Fall 2026 class is a Cal Poly class', { dec: r.dec, nodate: r.nodate });
  ok(r.opts.length === 2 && r.opts[1][0] === 'R-2865' && r.opts[1][2] === true && r.opts[1][3] === 'Major Core Courses - Option' && /NR 3319/.test(r.opts[1][4]) && /NR 4445/.test(r.opts[1][4]) && !/4431/.test(r.opts[1][4]), 'reader: (2026 layout) “Choose one” over “Option 1 of 2” / “Option 2 of 2” is one pick-1 with every option’s classes', r.opts);
  ok(r.opts[0][0] === 'R797-80' && r.opts[0][3] === 'NR/SS 4431 or NR 4442', 'reader: a cross-listed subject keeps its capitals (NR/SS, not Nr/ss)', r.opts[0]);
  ok(JSON.stringify(r.choose) === '[["R-2866",true,3]]', 'reader: (2026 layout) “Choose one” is one line even when its lines don’t say “Option N of M”', r.choose);
  ok(JSON.stringify(r.mixed) === '[["R620-10",true,"MATH 1261/MATH 1221"],["R620-30",false,"STAT 1210"]]', 'reader: (2026 layout) “Option 1 of 2” / “Option 2 of 2” beside a plain line: the options are one pick-1, the plain line its own', r.mixed);
  await close();
};

/* Past classes reads the report's own verdicts onto the flowchart — only those: not a line you marked done, not each
   class a "Select from …" line lists */
tests.pastByReport = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Environmental Management & Protection', 'Junior'), height: 2400 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => {
    const L = (label, status, extra) => Object.assign({ label, status, kind: 'major', ge: null, level: 'LN', code: null, units: null, courses: null, options: [], oneOf: false }, extra || {});
    TC.audit = { reqs: [
      L('1B: Critical Thinking Course', 'satisfied', { kind: 'ge', ge: '1B' }),
      L('4B: Select from SS 1120, ES 1112, or GOV 2200', 'satisfied', { kind: 'ge', ge: '4B', options: ['SS 1120', 'ES 1112', 'GOV 2200'] }),
      L('Approved Electives: SS 1120, ES 1112 or GOV 2200', 'satisfied', { options: ['SS 1120', 'ES 1112', 'GOV 2200'] }),
      L('STAT 1110', 'satisfied', { options: ['STAT 1110'] }),
      L('MATH 1264 or 1267 (GE 2)', 'satisfied', { options: ['MATH 1264', 'MATH 1267'] }),
      L('NR 3363', 'not', { code: 'R797-30', options: ['NR 3363'] }),
      L('NR 2208, BIO 2215, or BIO 2217', 'not', { options: ['NR 2208', 'BIO 2215', 'BIO 2217'] }),
      L('SS 1120', 'in_progress', { options: ['SS 1120'] })], counts: {}, overrides: [{ code: 'R797-30' }] };
  });
  await toPast(page); await openYears(page);
  const num = await page.evaluate(() => (document.querySelector('.pc-sum .pc-num') || {}).innerText);
  ok(/^7 of 8\s*filled$/.test(String(num).trim()), 'by report: the count is the report’s — 5 Satisfied + 1 In Progress + 1 you marked done, of 8', num);
  const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-row')].map(r => ({ st: r.className.replace('pc-row', '').trim(), main: ((r.querySelector('.pc-main') || {}).innerText || '').replace(/\s+/g, ' ').trim(), pf: (r.querySelector('.pc-pf') || {}).innerText || '' })));
  const at = re => rows.find(r => re.test(r.main)) || {};
  ok(at(/^GE Area 1B$/).st === 'done' && at(/^GE Area 1B$/).pf === 'On your report', 'by report: a GE spot whose area the report says is Satisfied is filled, “On your report”', at(/^GE Area 1B$/));
  ok(at(/^STAT 1110\b/).st === 'done' && at(/^STAT 1110\b/).pf === 'On your report', 'by report: a class spot whose own line is Satisfied is filled', at(/^STAT 1110\b/));
  ok(at(/^Choose one \(3-4 units, use lower\)/).st === 'done' && at(/^Choose one \(3-4 units, use lower\)/).pf === 'On your report', 'by report: a choose-one spot is filled by a Satisfied line naming only classes it takes (MATH 1264 or 1267)', at(/^Choose one \(3-4 units, use lower\)/));
  ok(at(/^SS 1120\b/).st === 'taking' && at(/^SS 1120\b/).pf === 'On your report', 'by report: SS 1120 is in progress by its own line — a Satisfied “Select from SS 1120, ES 1112 …” line doesn’t make it done', at(/^SS 1120\b/));
  ok(at(/^NR 3363\b/).st === 'need' && at(/^NR 3363\b/).pf !== 'On your report', 'by report: a line YOU marked done isn’t put on the flowchart as the report’s', at(/^NR 3363\b/));
  ok(rows.filter(r => r.pf === 'On your report').length === 4, 'by report: nothing else says “On your report”', rows.filter(r => r.pf === 'On your report'));
  ok(log.errors.length === 0, 'by report: no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [("tests.planColors = async () => {", TESTS + "tests.planColors = async () => {", 'tests')])
print('edit-tests-transfer-reports: check-app tests done')

# ---- mutants: each breaks one promise and names ONE test ----
import json
MUT = [
 ("transfer: the transfer icon never marks a row", "const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) }));", "const mk = icons.map(c => ({ y: c.y, t: false, c: csig.has(c.sig) }));", "dprTransferContinuing", None),
 ("transfer: any picture but the transfer one is Cal Poly's", "const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) }));", "const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: c.sig !== xsig }));", "dprTransferOddLegend", None),
 ("transfer: a legend giving transfer Cal Poly's picture still used", "  if (!xsig || xsig === gsig) return null;", "  if (!xsig) return null;", "dprTransferBadLegend", None),
 ("transfer: a form's own matrix ignored", "if (a && a[0] && a[0].length === 6) m = mul(m, a[0]);", "", "dprTransferForm", None),
 ("transfer: an unnamed picture counts as Cal Poly's for no-icon marks", "var k=mk.t?'T':mk.c?'C':'O'; if(k==='C')cp=true;", "var k=mk.t?'T':mk.c?'C':'O'; if(k!=='T')cp=true;", "dprReaderTransfer", 'planner'),
 ("transfer: the legend's picture not found", "Math.abs(i.y - y) < 4).sort((a, b) => b.x - a.x)[0];", "Math.abs(i.y - y) < 0).sort((a, b) => b.x - a.x)[0];", "dprTransferContinuing", None),
 ("transfer: the legend's picture taken from further left", "Math.abs(i.y - y) < 4).sort((a, b) => b.x - a.x)[0];", "Math.abs(i.y - y) < 4).sort((a, b) => a.x - b.x)[0];", "dprReaderTransfer", None),
 ("transfer: pictures read as bitmaps (no pixels to compare)", "TCPL.fileBytes(file)), isOffscreenCanvasSupported: false }).promise;", "TCPL.fileBytes(file)) }).promise;", "dprTransferContinuing", None),
 ("transfer: a page whose pictures weren't all read still marks no-icon rows", "icons.all = !other && icons.length === out.length;", "icons.all = true;", "dprTransferPartial", None),
 ("transfer: icons read only on page 1", "for (let i = ch; i < pages.length; i++) {", "for (let i = 0; i < 1; i++) {", "dprTransferContinuing", None),
 ("transfer: a row with no icon isn't marked", "else if(!hit[i]&&marks.bare&&cp&&!near(l))l.text+=' '+DPR_BMARK;", "", "dprTransferContinuing", 'planner'),
 ("transfer: no-icon marks with no Cal Poly icon on the page", "marks.bare&&cp&&!near(l)", "marks.bare&&!near(l)", "dprReaderTransfer", 'planner'),
 ("transfer: a picture just off a row doesn't stop a no-icon mark", "marks.bare&&cp&&!near(l)", "marks.bare&&cp", "dprReaderTransfer", 'planner'),
 ("transfer: no-icon marks on a page with unread pictures", "marks.bare&&cp&&!near(l)", "cp&&!near(l)", "dprReaderTransfer", 'planner'),
 ("transfer: Cal Poly's icon not marked", "else if(hit[i]==='C')l.text+=' '+DPR_CMARK;", "", "dprReaderTransfer", 'planner'),
 ("transfer: a graded row with no icon stays a Cal Poly class", "var xfer=xmark||(bmark&&DPR_CREDIT.test(gradeTok))||", "var xfer=xmark||", "dprTransferContinuing", 'planner'),
 ("transfer: no icon makes any graded row credit", "(bmark&&DPR_CREDIT.test(gradeTok))", "(bmark&&!!gradeTok)", "dprReaderTransfer", 'planner'),
 ("transfer: the row's marks left on its end", "if(xmark||bmark||cmark)ln=ln.split(DPR_XMARK).join('').split(DPR_BMARK).join('').split(DPR_CMARK).join('').trim();", "", "dprTransferContinuing", 'planner'),
 ("transfer: 300 read as a word of the title", "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333|[1-7]00)$/;", "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333)$/;", "dprTransferFirst", 'planner'),
 ("transfer: 300 with no icon in a past term isn't credit", "||DPR_TEST.test(gradeTok)||(gradeTok==='333')", "||(gradeTok==='333')", "dprReaderTransfer", 'planner'),
 ("transfer: Cal Poly's icon doesn't make 400 a title word", "||(cmark&&DPR_TEST.test(gradeTok))))", "))", "dprReaderTransfer", 'planner'),
 ("transfer: a grade in a running term isn't posted credit", "out.forEach(function(r){ if(r._post&&!r._xfer&&!r._cp&&dprTermRunning(r.term,r.year,printed))r._xfer=true; });", "", "dprTransferNoIcons", 'planner'),
 ("transfer: Cal Poly's icon doesn't stop the date rule", "if(r._post&&!r._xfer&&!r._cp&&dprTermRunning(", "if(r._post&&!r._xfer&&dprTermRunning(", "dprReaderTransfer", 'planner'),
 ("transfer: a mid-term W is posted credit", "if(r._post&&!r._xfer&&!r._cp&&dprTermRunning(", "if(!r._open&&!r._xfer&&!r._cp&&dprTermRunning(", "dprReaderTransfer", 'planner'),
 ("transfer: Fall runs to New Year's", "var end={Fall:[11,1],", "var end={Fall:[11,31],", "dprReaderTransfer", 'planner'),
 ("transfer: Summer runs to July", "Spring:[4,1],Summer:[5,1]}[term];", "Spring:[4,1],Summer:[6,1]}[term];", "dprReaderTransfer", 'planner'),
 ("transfer: an articulation number (1T1B) is a Cal Poly class", "\n      ||!/^\\d{3,4}[A-Z]{0,2}$/.test(nbr);", ";", "dprTransferNoIcons", 'planner'),
 ("transfer: posted credit counts as a finished term", "var lastGraded=0; out.forEach(function(r){ if(!r._open&&!r._xfer){", "var lastGraded=0; out.forEach(function(r){ if(!r._open){", "dprTransferFirst", 'planner'),
 ("transfer: an ungraded transfer placeholder is being taken (reader)", "  out.forEach(function(r){ if(r._xfer)r._now=false; });", "", "dprReaderTransfer", 'planner'),
 ("transfer: an ungraded transfer placeholder goes to My Classes", "    if (x._open && !x._xfer && k === cur) x._now = true;", "    if (x._open && k === cur) x._now = true;", "dprTransferContinuing", None),
 ("2026 layout: Option 1 of 2 counted per option", "||(NEW&&/^\\s*Option\\s+\\d+\\s+of\\s+\\d+\\b/i.test(v[2])),", ",", "dprReaderTransfer", 'planner'),
 ("2026 layout: Choose one not read", "||(NEW&&/^\\s*Choose\\s+one\\b/i.test(v[2])) };", " };", "dprReaderTransfer", 'planner'),
 ("2026 layout: (2026) left on a label", "  t=t.replace(/\\b([A-Za-z]{3,})\\s*\\((?:19|20)\\d\\d\\)(?=\\s*$|\\s*[-:,])/g,'$1');", "", "dprTransferFirst", 'planner'),
 ("labels: a cross-listed subject title-cased", "if(/^[A-Z]{2,5}(?:\\/[A-Z]{2,5})*$/.test(w)&&", "if(/^[A-Z]{2,5}$/.test(w)&&", "dprReaderTransfer", 'planner'),
 ("past classes: counts the flowchart with a report in", "  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L, { F, N }); }", "", "dprTransferFirst", None),
 ("profile: counts the flowchart with a report in", "    if (X) deg = meRow('schedTabGo', 'past', 'meCheck', `${X.filled.length} of ${X.live.length} requirements filled`", "    if (false) deg = meRow('schedTabGo', 'past', 'meCheck', `${X.filled.length} of ${X.live.length} requirements filled`", "dprTransferFirst", None),
 ("past classes: the report doesn't fill a flowchart spot", "    if (s.state !== 'need') return s;\n    let st = s.type === 'ge'", "    return s;\n    let st = s.type === 'ge'", "dprTransferFirst", None),
 ("past classes: a spot filled by the report doesn't say so", "s.rep ? '<span class=\"pc-pf\">On your report</span>' :", "s.rep ? '' :", "dprTransferFirst", None),
 ("past classes: a list line fills each class it lists", "if (l.o.every(c => ok.has(c)) && rank[l.st]", "if (l.o.some(c => ok.has(c)) && rank[l.st]", "pastByReport", None),
 ("past classes: a line you marked done shown as the report's", "const st = b.status === 'satisfied' ? 'done' : b.status === 'in_progress' ? 'taking' : null;", "const st = b.status === 'satisfied' || X.manual.has(b) ? 'done' : b.status === 'in_progress' ? 'taking' : null;", "pastByReport", None),
 ("past classes: a GE area not read onto the flowchart", "let st = s.type === 'ge' ? (s.area && ge[s.area]) || null : null;", "let st = null;", "pastByReport", None),
 ("reader: an icon far above a row still marks it", "var best=-1,bd=4;", "var best=-1,bd=8;", "dprReaderTransfer", 'planner'),
 ("reader: the first Date Printed read, not the last", "  while((x=re.exec(t)))m=x;", "  m=re.exec(t);", "dprReaderTransfer", 'planner'),
]
lines = ''.join('  ' + json.dumps([n, a, b, t] + ([tg] if tg else []), ensure_ascii=False) + ',\n' for n, a, b, t, tg in MUT)
edit('mutate.mjs', [("\n];\nconst html = fs.readFileSync(SRC, 'utf8');", "\n  /* transfer students' reports (2026-10-11; edit-tests-transfer-reports-2026-10-11.py) */\n" + lines + "];\nconst html = fs.readFileSync(SRC, 'utf8');", 'mutants')])
print('edit-tests-transfer-reports: mutants done')

# ---- one older mutant named markup this build changed (pastView now draws the years from the report-aware copy) ----
edit('mutate.mjs', [(
 '''  ["split: Past classes puts the record first", "${pcSummary(L) + pcYears(L) + (none ? '' : pcOther(L) + pcBtns())}</div>`;", "${(none ? '' : pcOther(L) + pcBtns()) + pcSummary(L) + pcYears(L)}</div>`;", "pastSimple"],''',
 '''  ["split: Past classes puts the record first", "${pcSummary(L) + pcYears(LR) + (none ? '' : pcOther(L) + pcBtns())}</div>`;", "${(none ? '' : pcOther(L) + pcBtns()) + pcSummary(L) + pcYears(LR)}</div>`;", "pastSimple"],''', 'reaim-split')])
print('edit-tests-transfer-reports: re-aim done')
