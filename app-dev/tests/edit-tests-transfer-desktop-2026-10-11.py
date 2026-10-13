#!/usr/bin/env python3
"""Tests for transfer-reports-desktop-2026-10-11.py: the website's report import (Past Classes › upload) reads the
synthetic transfer reports (files/make-dpr-transfer.py) right. Adds three tests to check-desktop-look.mjs and their
mutants to mutate-desktop.mjs. Replayable.
  python3 edit-tests-transfer-desktop-2026-10-11.py"""
import os, sys, json
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue   # already applied
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

TESTS = r'''/* ============ The website's report import reads transfer students' reports (2026-10-11) ============
   The same synthetic reports as check-app (files/make-dpr-transfer.py: invented people, classes and grades), through
   Past Classes › upload: the review list's "This term" group, its note and button, and what the save sends. */
const XDESK = () => Object.assign({}, FX.TABLES, { class_history: FX.TABLES.class_history.filter(r => r.user_id !== FX.ME.id) });
async function deskImport(file) {
  const app = await desk({ tables: XDESK() }); const { page } = app; await tick(page, 1500);
  await page.locator('#transcriptFile').setInputFiles('files/' + file);
  for (let i = 0; i < 60 && !(await page.locator('#tiModal .ti-row').count()); i++) await tick(page, 500);
  app.r = await page.evaluate(() => { const m = document.getElementById('tiModal');
    return { now: [...m.querySelectorAll('.ti-row.ti-now .hc')].map(e => e.innerText.trim()).sort(),
      tagged: [...m.querySelectorAll('.ti-row')].filter(r => [...r.querySelectorAll('.fr-shared')].some(e => e.innerText.trim() === 'transfer')).map(r => r.querySelector('.hc').innerText.trim()).sort(), names: [...m.querySelectorAll('.ti-row .ti-nm')].map(e => e.innerText), text: m.innerText,
      btn: (([...m.querySelectorAll('button')].find(b => /^Add \d+ to Past Classes/.test(b.innerText.trim())) || {}).innerText || '').trim() }; });
  return app;
}
async function deskSave(page, log) {
  await page.evaluate(() => [...document.querySelectorAll('#tiModal button')].find(b => /^Add \d+ to Past Classes/.test(b.innerText.trim())).click());
  for (let i = 0; i < 20 && !log.writes.some(w => w.table === 'class_history'); i++) await tick(page, 400);
  await tick(page, 600);
  return log.writes.filter(w => w.table === 'class_history' && w.m === 'POST').map(w => w.body).flat();
}

test('deskTransferFirst', async () => {
  const { page, close, log, r } = await deskImport('dpr-transfer-first.pdf');
  ok(JSON.stringify(r.now) === '["ES 3350","NR 1142","NR 3308"]', 'website, first-term transfer: “This term” is only the 3 ungraded classes — never ENGL 1134, MATH 1267 or STAT 1210 (they printed “300”/“400”)', r.now);
  ok(r.btn === 'Add 13 to Past Classes and 3 to My Classes' && /13 are transfer, AP or study-abroad credit/.test(r.text), 'website, first-term transfer: 13 classes to Past Classes, all of them transfer credit (the report’s icons)', { btn: r.btn });
  ok(!r.names.some(n => /\b[1-7]00\b/.test(n)), 'website, first-term transfer: a “300” / “400” never shows as part of a class’s name', r.names);
  const hist = await deskSave(page, log);
  ok(hist.length === 13 && hist.every(x => x.professor === '🌍'), 'website, first-term transfer: the save marks every one as transfer credit', hist.map(x => [x.code, x.professor]));
  ok(log.errors.length === 0, 'website, first-term transfer: no page errors', log.errors);
  await close();
});

test('deskTransferIcons', async () => {
  const { page, close, log, r } = await deskImport('dpr-transfer-continuing.pdf');
  ok(JSON.stringify(r.now) === '["BUS 3431","BUS 3438","BUS 4401"]', 'website, a year on: “This term” is the 3 classes he’s taking — not this term’s study-abroad placeholder (AP 300)', r.now);
  ok(r.btn === 'Add 14 to Past Classes and 3 to My Classes' && /8 are transfer, AP or study-abroad credit/.test(r.text) && !/catalog courses — \d+ are transfer/.test(r.text), 'website, a year on: 8 of the 14 are transfer credit — said on its own, not as part of the “not in the catalog” count', { btn: r.btn });
  ok(JSON.stringify(r.tagged) === JSON.stringify(['AP 300', 'BUS 1TR', 'BUS 2201', 'COMS 1101', 'ECON 2030', 'ENGL 1134', 'MATH 1221', 'PHIL 1T1B']), 'website, a year on: each transfer row says “transfer” in the list', r.tagged);
  const hist = await deskSave(page, log);
  const x = hist.filter(h => h.professor === '🌍').map(h => h.code).sort(), cp = hist.filter(h => h.professor == null).map(h => h.code).sort();
  ok(JSON.stringify(x) === JSON.stringify(['AP 300', 'BUS 1TR', 'BUS 2201', 'COMS 1101', 'ECON 2030', 'ENGL 1134', 'MATH 1221', 'PHIL 1T1B']) && JSON.stringify(cp) === JSON.stringify(['BUS 2207', 'BUS 2212', 'BUS 3346', 'BUS 3387', 'BUS 3391', 'STAT 2170']),
    'website, a year on: transfer credit found by the report’s icons (BUS 2201, MATH 1221 the same term as his Cal Poly classes; ECON 2030 exam credit with no icon) — the Cal Poly classes stay his', { x, cp });
  ok(log.errors.length === 0, 'website, a year on: no page errors', log.errors);
  await close();
});

test('deskTransferNoIcons', async () => {
  const { page, close, log, r } = await deskImport('dpr-transfer-noicons.pdf');
  ok(JSON.stringify(r.now) === '["ES 3350","NR 1142","NR 3308"]' && r.btn === 'Add 14 to Past Classes and 3 to My Classes' && /14 are transfer, AP or study-abroad credit/.test(r.text),
    'website, no pictures: the words alone find the 14 transfer classes (a grade in a term still running when printed; “300”/“400”; PHIL 1T1B) and the 3 he’s taking', { now: r.now, btn: r.btn });
  ok(log.errors.length === 0, 'website, no pictures: no page errors', log.errors);
  await close();
});

'''
edit('check-desktop-look.mjs', [
  ("import { openApp } from './app-harness.mjs';\n", "import { openApp } from './app-harness.mjs';\nimport * as FX from './app-fixtures.mjs';\n", 'import'),
  ("const names = ONLY ? [ONLY] : Object.keys(T);", TESTS + "const names = ONLY ? [ONLY] : Object.keys(T);", 'tests'),
])
MUT = [
 ("website: the transfer icon never marks a row", "const mk = icons.map(c => ({ y: c.y, t: c.sig === xsig, c: csig.has(c.sig) }));", "const mk = icons.map(c => ({ y: c.y, t: false, c: csig.has(c.sig) }));", "deskTransferIcons"),
 ("website: a report's icons never read", "    if(dprLooksLikeOne(pages.map(function(pg){ return pdfItemsToText(pg.items); }).join('\\n\\n')))", "    if(false)", "deskTransferIcons"),
 ("website: pictures read as bitmaps", "{data:new Uint8Array(buf),isOffscreenCanvasSupported:false}", "{data:new Uint8Array(buf)}", "deskTransferIcons"),
 ("website: posted credit with no grade is this term's class", "  out.forEach(function(r){ if(r._xfer)r._now=false; });\n  return {ok:true, rows:out,", "  return {ok:true, rows:out,", "deskTransferIcons"),
 ("website: a grade in a running term isn't posted credit", "  out.forEach(function(r){ if(r._post&&!r._xfer&&!r._cp&&dprTermRunning(r.term,r.year,printed))r._xfer=true; });\n  /* posted credit with no grade (a study-abroad placeholder, \"AP 300\") is not a class being taken */\n  out.forEach(function(r){ if(r._xfer)r._now=false; });\n  return {ok:true, rows:out,", "  out.forEach(function(r){ if(r._xfer)r._now=false; });\n  return {ok:true, rows:out,", "deskTransferNoIcons"),
 ("website: 300 read as a word of the title", "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333|[1-7]00)$/;", "var DPR_GRADE=/^(?:[A-D][+-]?|F|CR|NC|W|IC|RP|333)$/;", "deskTransferNoIcons"),
 ("website: an articulation number is a Cal Poly class", "\n      ||!/^\\d{3,4}[A-Z]{0,2}$/.test(nbr);", ";", "deskTransferNoIcons"),
 ("website: a transfer row isn't tagged", "      +(r._dpr&&r._xfer?'<span class=\"fr-shared\">transfer</span>':'')\n", "", "deskTransferIcons"),
 ("website: the transfer count folded into the catalog note", "  if(isDpr&&nXfer)notes.push(", "  if(false)notes.push(", "deskTransferIcons"),
 ("website: the row's marks left on its end", "    if(xmark||bmark||cmark)ln=ln.split(DPR_XMARK).join('').split(DPR_BMARK).join('').split(DPR_CMARK).join('').trim();\n", "", "deskTransferFirst"),
]
lines = ''.join('  ' + json.dumps([n, a, b, t], ensure_ascii=False) + ',\n' for n, a, b, t in MUT)
edit('mutate-desktop.mjs', [("\n];\nconst html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');",
     "\n  /* the website's report import reads transfer students' reports (2026-10-11; edit-tests-transfer-desktop-2026-10-11.py) */\n" + lines + "];\nconst html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');", 'mutants')])
print('edit-tests-transfer-desktop: done')
