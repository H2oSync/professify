#!/usr/bin/env python3
"""Tests for dpr-truth-2026-10-11.py and dpr-truth-app-2026-10-11.py (the report as the source of truth), plus the
stress reports (files/make-dpr-stress.py) run end to end: upload → Report read → save → Past classes → Planner →
Plans → reload. Re-aims two older tests to the new Past classes screen. Replayable.
  python3 edit-tests-dpr-truth-2026-10-11.py"""
import os, sys, json
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue   # already applied
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

TESTS = r'''/* ============ The report as the source of truth (Tate, 2026-10-11) ============
   "Use the DPR as the primary reference … account for the quarter-to-semester transition … respect my original
   catalog … avoid incorrectly marking requirements as incomplete … identify conflicts instead of guessing." And:
   "run a good amount of fake dprs … to try and find breaks in the flow of the system from past classes, planner to
   plans". files/make-dpr-stress.py draws five (invented people, classes and grades). */
const pcRows = page => page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row')].map(r => ({ st: r.className.replace('pc-row', '').replace('look', '').trim(), look: /\blook\b/.test(r.className), main: ((r.querySelector('.pc-main') || {}).innerText || '').replace(/\s+/g, ' ').trim(), sub: [...r.querySelectorAll('.pc-used, .pc-pf, .pc-look, .pc-add')].map(e => e.innerText.replace(/\s+/g, ' ').trim()).join(' | '), still: !!r.closest('.pc-still') })));
const pcSum = page => page.evaluate(() => { const c = document.querySelector('.pc-sum'); return c && { num: c.querySelector('.pc-num').innerText.replace(/\s+/g, ' ').trim(), link: (c.querySelector('.pc-link') || {}).innerText || '', cat: (c.querySelector('.pc-cat') || {}).innerText || '' }; });
const openGroups = async page => { for (let i = 0; i < 6; i++) { const c = page.locator('[data-a="pcGroup"][aria-expanded="false"]'); if (!(await c.count())) break; await c.first().click(); await tick(page, 150); } };
const saveReport = async page => { await click(page, '[data-a="dprSave"]'); await tick(page, 2500); await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet = null; render(true); }); };
const toPastTab = async page => { await page.evaluate(() => { document.getElementById('scroll').scrollTop = 0; }); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 1500); };

/* 1. A senior on the Fall Quarter 2023 catalog: the old layout, lettered GE, quarter numbers with their pairs, a
      listed-but-not-counted class, a repeated class, the closing "COURSE CREDITS NOT USED" table */
tests.dprStressQuarter = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-stress-quarter.pdf');
  ok(await readPills(page) === '36 filled|2 left|5 transfer', 'quarter catalog: Report read — 33 Satisfied + 3 in progress = 36 filled, 2 left, 5 transfer (ART 3TC1, DUD 3TR, PORT 1TC2, BUS 401, TRAN 302)', await readPills(page));
  await saveReport(page);
  const hist = posted(log, 'class_history');
  ok(hist.length === 34 && hist.filter(r => r.code === 'BUS 2207').length === 2 && hist.filter(r => r.code === 'BUS 3306').length === 1, 'quarter catalog: 34 finished classes to the record (both attempts of BUS 207 → BUS 2207, as the report prints them), 4 in progress kept out', { n: hist.length, b207: hist.filter(r => r.code === 'BUS 2207').map(r => r.term + ' ' + r.year) });
  const au = log.writes.find(w => w.table === 'degree_audit' && w.m === 'POST'); const reqs = au ? au.body.requirements : [];
  const bus214 = reqs.find(b => b.label === 'BUS 2214'), cr3 = reqs.find(b => /^Career Readiness III/.test(b.label)), ge1 = reqs.find(b => /^C1:/.test(b.label));
  ok(au && au.body.catalog === 'Fall Quarter 2023' && au.body.printed_on === '2026-10-09', 'quarter catalog: the account keeps the report’s catalog and printed date', au && [au.body.catalog, au.body.printed_on]);
  ok(bus214 && JSON.stringify(bus214.used) === '[{"c":"BUS 214","t":"Winter 2025","n":"BUS 2214"}]', 'quarter catalog: a line keeps the class the report used — as printed (BUS 214), today’s number (BUS 2214), the term — never its grade or title', bus214 && bus214.used);
  ok(ge1 && ge1.used.length === 1 && ge1.used[0].c === 'ART 3TC1' && ge1.used[0].x === true && !ge1.used[0].n, 'quarter catalog: a transfer placeholder (ART 3TC1) is kept as transfer credit, with no number to translate it to', ge1 && ge1.used);
  ok(cr3 && cr3.status === 'not' && JSON.stringify(cr3.listed) === '["BUS 3306"]', 'quarter catalog: a Not Satisfied line that lists a class on the Course History (BUS 3306, finished) the report didn’t count keeps it as "listed" — a conflict, never a guess', cr3 && cr3.listed);
  ok(!reqs.some(b => (b.used || []).some(e => /BUS 100|TRAN 302/.test(e.c))), 'quarter catalog: the closing "COURSE CREDITS NOT USED" table (BUS 100, TRAN 302) is no line’s classes', reqs.filter(b => (b.used || []).some(e => /BUS 100|TRAN 302/.test(e.c))).map(b => b.label));
  ok(!JSON.stringify(au ? au.body : {}).match(/\b(?:[A-DF][+-]?|W|CR)\s+\d+\.\d\d\b|9711001|Stressquarter/), 'quarter catalog: nothing stored carries a grade beside units, the EMPLID or the name');
  await toPastTab(page);
  const sum = await pcSum(page);
  ok(sum && sum.num === '37 of 38 filled' && /1 left/.test(sum.link) && sum.cat === 'Your catalog: Fall Quarter 2023 · report printed Oct 9, 2026', 'quarter catalog: Past classes counts the report (36, plus the Approved Elective in progress now that BUS 4442 is in My Classes) and names its catalog and date', sum);
  ok(!(await page.locator('[data-a="plYear"]').count()) && !(await page.locator('.pc-fhd').count()), 'quarter catalog: NO flowchart years — the 2026–28 semester flowchart isn’t this student’s catalog', await page.locator('[data-a="plYear"]').count());
  let rows = await pcRows(page);
  const still = rows.filter(r => r.still);
  ok(still.length === 5 && still.filter(r => r.st === 'need').map(r => r.main).join('|') === 'Career Readiness III: BUS 3306' && still.filter(r => r.st === 'taking').length === 4 && still.some(r => /^Approved Elective/.test(r.main) && r.st === 'taking' && /Taking BUS 4442 this term/.test(r.sub)), 'quarter catalog: Still needed on top — the open line, then the 4 in progress (GWR, BUS 3431, BUS 3438, and the Approved Elective by BUS 4442 in My Classes — the report hadn’t attached it)', still.map(r => r.st + ':' + r.main + ' [' + r.sub + ']'));
  const cr = still.find(r => /^Career Readiness III/.test(r.main));
  ok(cr && cr.look && /^1 unit needed \| Needs a look: your report lists BUS 3306 on your record but didn’t count it here/.test(cr.sub), 'quarter catalog: the conflict wears "Needs a look" and says which class — the report decides, the app says so', cr);
  ok(!rows.some(r => !r.still), 'quarter catalog: the groups start folded');
  await openGroups(page); rows = await pcRows(page);
  const heads = await page.evaluate(() => [...document.querySelectorAll('[data-a="pcGroup"]')].map(b => b.innerText.replace(/\s+/g, ' ').trim()));
  ok(heads.join('|') === 'Major and support 11 filled|Financial Management concentration 1 filled|General education 19 filled|Degree requirements 2 filled', 'quarter catalog: the report’s groups — major and support, the concentration by name, GE, degree requirements', heads);
  const b214 = rows.find(r => r.main === 'BUS 2214'), c1 = rows.find(r => /^C1: Arts Course/.test(r.main)), tech = rows.find(r => /^TECHNOLOGY MANAGEMENT COURSE/i.test(r.main) || /^Technology Management Course/.test(r.main)), e = rows.find(r => /^E: /.test(r.main));
  ok(b214 && b214.st === 'done' && /^BUS 214 → BUS 2214 Winter 2025 \| \+ Professor$/.test(b214.sub), 'quarter catalog: a major line names the class as taken, today’s number, the term, and asks for the professor', b214);
  ok(c1 && c1.st === 'done' && c1.sub === 'ART 3TC1 Fall 2025 · transfer credit', 'quarter catalog: a GE line filled by transfer credit says so — and asks for no professor', c1);
  ok(tech && tech.st === 'done' && /BUS 310 → BUS 3310 Winter 2026/.test(tech.sub), 'quarter catalog: a "1 of 2 Options" requirement counts once, as done, with the option’s class', tech);
  ok(e && e.st === 'done' && /FSN 250 Winter 2024/.test(e.sub), 'quarter catalog: Area E (gone from the semester catalog) stays Satisfied with its class — the student’s own catalog is respected', e);
  ok(rows.filter(r => r.st === 'done').length === 38 - 5 && !rows.some(r => r.st === 'need' && !r.still), 'quarter catalog: 33 lines done, and nothing the report says is Satisfied shows as to do', rows.filter(r => r.st === 'need' && !r.still).map(r => r.main));
  const units = await page.evaluate(() => { const c = [...document.querySelectorAll('.pc-oth')].find(x => /Units only/.test(x.innerText)); return c ? [...c.querySelectorAll('.pc-cc')].map(e => e.innerText) : null; });
  ok(units && units.includes('BUS 1100') && units.includes('TRAN 302') && units.includes('BUS 3306') && !units.includes('BUS 2214'), 'quarter catalog: "Units only" lists the classes the report used for nothing (BUS 100 → today’s BUS 1100, the study-abroad placeholder, BUS 3306)', units);
  /* the Planner: picks only for what the report leaves open — never a class whose line is Satisfied */
  await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 3000);
  const pk = await page.evaluate(() => { plSync(); const R = planRank(TCPL.ledger()); return { left: R.left, codes: R.all.map(c => c.code), done: R.done }; });
  ok(pk.left === 1 && !pk.codes.some(c => /^(BUS 3431|BUS 3438|BUS 3346|BUS 3387|PHIL 3331|BUS 4401|BUS 4442)$/.test(c)), 'quarter catalog: the Planner sees 1 open line and never picks a class the report says is done or being taken (BUS 3431, 3438, 3346, 3387, PHIL 3331, BUS 4401, 4442)', pk);
  /* reload: the account’s row carries everything */
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 12000 }); await tick(page, 1500);
  await page.evaluate(() => { S.tab = 'schedule'; S.schedTab = 'past'; save(); render(true); }); await tick(page, 2500); await openGroups(page);
  const sum2 = await pcSum(page), rows2 = await pcRows(page), b2 = rows2.find(r => r.main === 'BUS 2214');
  ok(sum2 && sum2.num === '37 of 38 filled' && b2 && /BUS 214 → BUS 2214 Winter 2025/.test(b2.sub) && rows2.filter(r => r.still).length === 5, 'quarter catalog: after a reload everything is read back from the account — the same counts, the same classes per line', { sum2, b2 });
  ok(log.errors.length === 0, 'quarter catalog: no page errors', log.errors);
  await close();
};

/* 2. A junior on a quarter catalog in Fall 2026: quarter past, semester present (quarter-equivalent units), Area E
      and the C elective open, a line the reader can’t place — then the January report over it */
tests.dprStressMixed = async () => {
  const T = XFER_T('Business Administration', 'Junior');
  T.plans = FX.TABLES.plans.filter(p => p.user_id !== FX.ME.id).concat([{ user_id: FX.ME.id, term: '2268', slot: 'B', sections: [{ code: 'BUS 3387', class_nbr: '70111' }], shared: true }, { user_id: FX.ME.id, term: '2268', slot: 'C', sections: [{ code: 'ECON 2303', class_nbr: '70105' }], shared: false }]);
  const { page, close, log } = await openApp({ tables: T, height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-stress-mixed.pdf');
  ok(await readPills(page) === '9 filled|7 left|1 can’t check', 'mixed, October: 8 Satisfied + D UD in progress (NR 3308 this term: 4.50 quarter-equivalent units cover its 4) = 9 filled, 7 left, 1 the reader couldn’t place', await readPills(page));
  await saveReport(page);
  await toPastTab(page);
  let rows = await pcRows(page); const still = rows.filter(r => r.still);
  ok(still.length === 9 && still.some(r => r.st === 'cant' && /couldn’t read this line/.test(r.sub)) && still.some(r => r.st === 'taking' && /^D UD/.test(r.main) && /NR 3308 Fall 2026 · this term/.test(r.sub)), 'mixed: Still needed shows the open lines, the unplaceable one as "can’t check", and D UD in progress by the class being taken', still.map(r => r.st + ':' + r.main + ' [' + r.sub + ']'));
  ok(!(await page.locator('[data-a="plYear"]').count()), 'mixed: no semester flowchart for a Fall Quarter 2024 catalog');
  /* the Planner: an open quarter GE line gets picks in today’s areas — C UD → UD 3 (PHIL 3331 has a section); E → 4B */
  await click(page, '[data-a="schedTab"][data-x="planner"]'); await tick(page, 3000);
  const pk = await page.evaluate(() => { plSync(); const R = planRank(TCPL.ledger()); return { left: R.left, codes: R.all.map(c => c.code), phil: (R.all.find(c => c.code === 'PHIL 3331') || {}).fills, areas: (TC.audit.reqs || []).filter(b => b.kind === 'ge' && b.status === 'not').map(b => b.label.split(':')[0] + '→' + plGeArea(b).join('/')) }; });
  ok(pk.codes.includes('PHIL 3331') && (pk.phil || []).some(b => /^C UD/.test(b.label)), 'mixed: the Planner offers PHIL 3331 for the open "C UD" line — a quarter area matched to today’s UD 3 by the registrar’s table', pk);
  ok(pk.areas.join('|') === 'C UD→UD3|E→4B|Lower-division C Elective→3A/3B', 'mixed: C UD is UD 3, Area E is "an additional 4B", the C elective is 3A or 3B (registrar.calpoly.edu/GE_2026)', pk.areas);
  /* the January report over it: Fall grades posted, BUS 3387 a late add the student had in Plan B, one new line */
  await toPastTab(page); await page.locator('.pc-btns input[data-in="dprfile"]').first().setInputFiles('files/dpr-stress-mixed-v2.pdf'); for (let i = 0; i < 30 && !(await page.locator('#sheet .dr-h1, #sheet .tc-err').count()); i++) await tick(page, 500);
  ok(await readPills(page) === '11 filled|6 left|1 can’t check', 'mixed, January: 11 filled (C UD, D UD, BUS 3387 now Satisfied), 6 left', await readPills(page));
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  const sh = await page.evaluate(() => UI.sheet && UI.sheet.type === 'dprDiff' ? { d: UI.sheet.d, text: document.querySelector('#sheet').innerText.replace(/\s+/g, ' ') } : null);
  ok(sh && sh.d.filled.length === 2 && /^C UD/.test(sh.d.filled[0]) && sh.d.filled[1] === 'BUS 3387' && sh.d.added === 1 && !sh.d.opened.length, 'mixed, re-upload: the app says what changed — 2 lines now filled (D UD was already in progress), 1 new line, nothing reopened', sh && sh.d);
  ok(sh && JSON.stringify(sh.d.affected) === '{"B":["BUS 3387"]}' && /Plan B · BUS 3387/.test(sh.text) && /Take it out/.test(sh.text), 'mixed, re-upload: Plan B holds BUS 3387, which filled an open line before and is done now — offered, not removed', sh && sh.d.affected);
  const histAll = posted(log, 'class_history');
  ok(histAll.filter(r => r.code === 'BUS 2214').length === 1 && !histAll.some(r => r.code === 'BUS 2215' || r.code === 'BUS 3391'), 'mixed, re-upload: classes already on the record aren’t written again; Spring 2027’s registered classes aren’t finished classes', histAll.map(r => r.code + '@' + r.term + r.year));
  await click(page, '[data-a="dprDrop"]'); await tick(page, 600);
  const plans = await page.evaluate(() => ({ B: (TC.plans.B || []).map(id => SEC[id] && SEC[id].code), C: (TC.plans.C || []).map(id => SEC[id] && SEC[id].code) }));
  ok(plans.B.length === 0 && plans.C.join() === 'ECON 2303', 'mixed, re-upload: "Take it out" removes BUS 3387 from Plan B; Plan C (the student’s own) is untouched', plans);
  ok(log.errors.length === 0, 'mixed: no page errors', log.errors);
  await close();
};

/* 3. A major the app has no flowchart for: the report is still the whole screen */
tests.dprStressNoMajor = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Dance', 'Freshman'), height: 2000 });
  await toPlanner(page); await uploadFile(page, 'dpr-stress-nomajor.pdf');
  ok(await readPills(page) === '2 filled|3 left', 'no flowchart: Report read still counts the report', await readPills(page));
  await saveReport(page); await toPastTab(page);
  const sum = await pcSum(page), t = await text(page);
  ok(sum && sum.num === '2 of 5 filled' && !/don’t have this major’s flowchart/.test(t), 'no flowchart: Past classes shows the report’s 2 of 5 — not "we don’t have this major’s flowchart"', { sum, t: t.slice(0, 200) });
  await openGroups(page); const rows = await pcRows(page);
  ok(rows.some(r => r.main === 'DANC 1100' && r.st === 'done' && /DANC 1100 Fall 2026/.test(r.sub)) && rows.filter(r => r.still).length === 3, 'no flowchart: the major line, its class and the 3 open lines', rows.map(r => r.st + ':' + r.main));
  ok(log.errors.length === 0, 'no flowchart: no page errors', log.errors);
  await close();
};

/* 4. A sophomore who moved to the semester catalog: bare quarter numbers, a duplicated row, a class two lines use,
      "Choose one" with an option in progress — and the flowchart years, since it IS this student’s catalog */
tests.dprStressDupes = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Sophomore'), height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-stress-dupes.pdf');
  ok(await readPills(page) === '5 filled|2 left', 'semester catalog: 4 Satisfied + the option in progress = 5 filled, 2 left — "Choose one" counted once', await readPills(page));
  await saveReport(page);
  const hist = posted(log, 'class_history');
  ok(hist.length === 3 && hist.filter(r => r.code === 'MATH 1267').length === 1 && hist.some(r => r.code === 'ECON 2040'), 'semester catalog: the duplicated MATH 221 row goes on the record ONCE, under today’s number', hist.map(r => r.code));
  const au = log.writes.find(w => w.table === 'degree_audit' && w.m === 'POST');
  ok(au && !au.body.requirements.some(b => (b.used || []).some(e => /^PSY 200/.test(e.c))), 'semester catalog: the closing "FREE ELECTIVES" table (no verdict, "(RG8)" / "(R30)" on their own lines) is no line’s classes', au && au.body.requirements.filter(b => (b.used || []).some(e => /^PSY 200/.test(e.c))).map(b => b.label));
  await toPastTab(page); await openGroups(page);
  const rows = await pcRows(page), stat = rows.find(r => /^Statistics - Option/.test(r.main)), m = rows.filter(r => /MATH 221 → MATH 1267/.test(r.sub));
  ok(stat && stat.st === 'taking' && /STAT 1210 Fall 2026 · this term/.test(stat.sub), 'semester catalog: the pick-1 line is in progress by STAT 1210 this term', stat);
  ok(m.length === 2, 'semester catalog: a class two lines use (GE 2 and MATH 1267) is named under both — the report double counts it, the record holds it once', m.map(r => r.main));
  ok((await page.locator('.pc-fhd').count()) === 1 && (await page.locator('[data-a="plYear"]').count()) > 0, 'semester catalog: the 2026–28 flowchart years show under the report — they ARE this student’s catalog');
  const units = await page.evaluate(() => { const c = [...document.querySelectorAll('.pc-oth')].find(x => /Units only/.test(x.innerText)); return c ? [...c.querySelectorAll('.pc-cc')].map(e => e.innerText) : null; });
  ok(units && units.join() === 'PSY 2200', 'semester catalog: PSY 200 (today’s PSY 2200) is "Units only"', units);
  ok(log.errors.length === 0, 'semester catalog: no page errors', log.errors);
  await close();
};

/* 5. The reader alone, on the quarter report: what it keeps per line */
tests.dprReaderUsed = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  const r = await page.evaluate(async b64 => {
    const lib = await loadPdfJs(); const doc = await lib.getDocument({ data: Uint8Array.from(atob(b64), c => c.charCodeAt(0)), isOffscreenCanvasSupported: false }).promise; const t = await dprDocText(doc); doc.destroy();
    plSync(); const p = TCPL.dprParse(t); const by = l => p.audit.reqs.find(b => b.label === l || new RegExp('^' + l).test(b.label));
    return { printed: p.audit.printed, a1: by('A1:').used, tech: by('TECHNOLOGY MANAGEMENT').used, cr3: by('Career Readiness III').listed, ae: by('Approved Elective').listed, gwr: by('Graduation Writing').used, conc: by('BUS 3431').used, units: by('Total Units').used, n: p.audit.reqs.length,
      nowhere: p.audit.reqs.filter(b => (b.used || []).some(e => e.c === 'BUS 100')).map(b => b.label) };
  }, nodeFs.readFileSync(nodePath.join('files', 'dpr-stress-quarter.pdf')).toString('base64'));
  ok(r.printed === '2026-10-09', 'reader: the printed date, as a date', r.printed);
  ok(JSON.stringify(r.a1) === '[{"c":"COMS 101","t":"Spring 2024","n":"COMS 1101"}]' && Object.keys(r.conc[0]).sort().join() === 'c,n,p,t', 'reader: a GE line’s class — printed number, term, today’s number from the report’s own (NNNN) pair — and nothing else (no title, no grade, no units)', [r.a1, r.conc]);
  ok(JSON.stringify(r.ae) === '[]', 'reader: a class the line lists that’s being TAKEN (BUS 4442, ungraded) is not a conflict — only a finished, uncounted one is', r.ae);
  ok(r.tech && r.tech.length === 1 && r.tech[0].c === 'BUS 310' && r.tech[0].n === 'BUS 3310', 'reader: a "1 of 2 Options" requirement carries the option’s class', r.tech);
  ok(JSON.stringify(r.cr3) === '["BUS 3306"]', 'reader: a Not Satisfied line lists BUS 3306, finished on the Course History and not counted', r.cr3);
  ok(r.gwr && r.gwr.length === 1 && r.gwr[0].p === true && !r.gwr[0].x, 'reader: a class being taken is marked so (never transfer)', r.gwr);
  ok(r.conc && r.conc[0].c === 'BUS 431' && r.conc[0].n === 'BUS 3431' && r.conc[0].p === true, 'reader: a quarter-numbered class being taken is translated and marked taking', r.conc);
  ok(!r.units.length && !r.nowhere.length, 'reader: the units line has no classes, and the "COURSE CREDITS NOT USED" table is attached to no line', { units: r.units, nowhere: r.nowhere });
  ok(log.errors.length === 0, 'reader: no page errors', log.errors);
  await close();
};


/* 6. The review's cases, one rule at a time (review 2026-10-11): what the area map, the conflict flag and the diff
      must never do */
tests.dprTruthRules = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Psychology', 'Junior'), height: 2400 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  const r = await page.evaluate(() => {
    const L = (label, status, extra) => Object.assign({ label, status, kind: 'ge', ge: null, level: 'LN', code: null, units: null, courses: null, options: [], oneOf: false, used: [], listed: [] }, extra || {});
    const areas = l => plGeArea(L(l, 'not')).join('/');
    const out = { dei: areas('Diversity, Equity, & Inclusion Elective (GE UD 4)') + areas('Upper-division Science Elective (GE UD 2/5)'), psy: areas('PSY 2240 (GE 5B)'), a4: areas('GE Area 4: 4B Social & Behavioral Sciences'), a3: areas('Area 3: Upper-division Arts & Humanities Course'),
      a25: areas('Area 2 or 5: UD Math & Quantitative Reasoning or Physical & Life Sciences Course'), ldc: areas('Lower-division C Elective'), el: areas('GE Elective: Areas B, C, and D') };
    /* a class in My Classes (PHIL 3331, UD 3) that the report already put under one UD 3 line never covers another */
    const ph = (plGeMap().get('PHIL 3331') || []).includes('UD3'); PEOPLE.me.unplaced = (PEOPLE.me.unplaced || []).concat(['PHIL 3331']);
    const X = auditLines({ catalog: 'Fall Quarter 2024', reqs: [L('C UD: Upper-division Arts & Humanities Course', 'in_progress', { ge: 'CUD', used: [{ c: 'PHIL 3331', t: 'Fall 2026', p: true }] }), L('Area 3: Upper-division Arts & Humanities Course', 'not')] }, null);
    out.ph = ph; out.eCovered = X.covered.size;
    /* two open UD 3 lines and that one class: it covers ONE of them */
    const X2 = auditLines({ catalog: 'Fall Quarter 2024', reqs: [L('Area 3: Upper-division Arts & Humanities Course', 'not'), L('C UD: Upper-division Arts & Humanities Course', 'not', { ge: 'CUD' })] }, null);
    out.twoCovered = X2.covered.size;
    /* the diff: two same-word lines, the second flips — one "now filled", not two; a line that vanished isn't "done" */
    TC.plans = { A: [], B: [], C: [] };
    const d = auditDiff({ reqs: [L('GE Elective: Areas B, C, and D', 'satisfied'), L('GE Elective: Areas B, C, and D', 'not')], overrides: [] }, { ok: true, reqs: [L('GE Elective: Areas B, C, and D', 'satisfied'), L('GE Elective: Areas B, C, and D', 'satisfied')] });
    out.diff = d && { filled: d.filled.length, opened: d.opened.length, added: d.added };
    const sec = Object.values(SEC)[0]; TC.plans = { A: [sec.id], B: [], C: [] };
    const d2 = auditDiff({ reqs: [L(sec.code, 'not', { kind: 'major', options: [sec.code] })], overrides: [] }, { ok: true, reqs: [L('Something else', 'not', { kind: 'major' })] });
    const d3 = auditDiff({ reqs: [L(sec.code, 'not', { kind: 'major', code: 'R40-10', options: [sec.code] })], overrides: [] }, { ok: true, reqs: [L(sec.code, 'satisfied', { kind: 'major', code: 'R40-10', options: [sec.code] })] });
    out.vanished = d2 && d2.affected; out.doneNow = d3 && d3.affected; out.sec = sec.code;
    /* the wrong attempt: a class taken twice, and the report's term matches neither — no row, so no professor */
    TC.myHistory = [{ code: 'BUS 2207', term: 'Winter', year: 2024, professor: 'First Attempt' }, { code: 'BUS 2207', term: 'Fall', year: 2024, professor: 'Second Attempt' }];
    out.attempt = pcUsedRow({ c: 'BUS 207', n: 'BUS 2207', t: 'Spring 2025' });
    out.attempt2 = (pcUsedRow({ c: 'BUS 207', n: 'BUS 2207', t: 'Fall 2024' }) || {}).professor;
    return out;
  });
  ok(r.dei === '' && r.psy === '', 'rules: a major line that also counts for GE ("DEI Elective (GE UD 4)", "Upper-division Science Elective (GE UD 2/5)", "PSY 2240 (GE 5B)") is never "any class of that area"', r);
  ok(r.a4 === '' && r.a3 === 'UD3' && r.a25 === 'U25', 'rules: "Area 3: Upper-division …" is UD 3, "Area 2 or 5: UD …" is UD 2/5 — but "GE Area 4: 4B …" (a lower-division heading) is not UD 4', r);
  ok(r.ldc === '3A/3B' && r.el === '2/5A/5B/5C/3A/3B/4A/4B', 'rules: the C elective is 3A or 3B; a GE elective is any lower-division B, C or D area', r);
  ok(r.ph && r.eCovered === 0, 'rules: a class the report already put under one line (PHIL 3331 under C UD) never covers another line of its area — as Area E ("an additional 4B") must never be covered by D2’s class', r);
  ok(r.ph && r.twoCovered === 1, 'rules: one class in My Classes covers ONE of two open lines of its area, never both', r);
  ok(r.diff && r.diff.filled === 1 && !r.diff.opened && !r.diff.added, 'rules: two lines with the same words stay two — the one that flipped is "now filled", the other isn’t "added"', r.diff);
  ok(JSON.stringify(r.vanished) === '{}' && JSON.stringify(r.doneNow) === JSON.stringify({ A: [r.sec] }), 'rules: a plan’s class is "done now" only when the line it filled is Satisfied on the new report — not when the line just vanished', { vanished: r.vanished, doneNow: r.doneNow });
  ok(r.attempt === null && r.attempt2 === 'Second Attempt', 'rules: a class taken twice shows the attempt in the report’s term, never the other one’s professor', r);
  /* the reader: an F is no conflict, a class used for another line is no conflict, a NOTE naming a code keeps the table */
  const t = await page.evaluate(() => {
    const H = ['Degree Progress Report', 'Current Academic Objective Requirement (Catalog) Term', 'PSY Primary BS UG Major Fall Quarter 2024', 'DEGREE PROGRESS REPORT'];
    const rows = ['Satisfied: D1: AMERICAN INSTITUTIONS COURSE - Select from PSY 2240 or POLS 112 (1112) - 4 Units Required (R73-10)', 'Courses Used', '2025 Fall PSY 2240 Biopsych A 4.00 D1',
      'Not Satisfied: D2: LOWER-DIVISION SOCIAL SCIENCES COURSE: PSY 2240 or ECON 222 (2040) - 4 Units Required (R73-20)', '· Units: 4.00 required, 0.00 used, 4.00 needed',
      'Not Satisfied: B4: MATHEMATICS COURSE: MATH 1410 - 4 Units Required (R71-40)', '· Units: 4.00 required, 0.00 used, 4.00 needed',
      'Satisfied: C1: ARTS COURSE - 4 Units Required (R74-10)', 'Courses Used', '2024 Fall ART 101 Art A 4.00 C1', 'NOTE: this also counts toward (R-0099)', '2025 Wtr ART 102 Art B 4.00 C1',
      'Course History', '2024 Fall ART 101 Art A 4.00', '2025 Wtr ART 102 Art B 4.00', '2025 Fall PSY 2240 Biopsych A 4.00', '2025 Fall MATH 1410 Calc F 4.00'];
    const p = TCPL.dprParse(H.concat(rows).join('\n')); const by = l => p.audit.reqs.find(b => b.label.startsWith(l)) || {};
    return { d2: by('D2').listed, b4: by('B4').listed, c1: (by('C1').used || []).map(e => e.c) };
  });
  ok(JSON.stringify(t.d2) === '[]', 'rules: PSY 2240 is listed under D2 but the report used it for D1 — not a conflict', t);
  ok(JSON.stringify(t.b4) === '[]', 'rules: a class failed (F) on a line that lists it is no conflict to flag', t);
  ok(t.c1.join() === 'ART 101,ART 102', 'rules: a NOTE naming another code inside a table doesn’t end the line’s classes', t);
  /* a report saved before this build (no classes per line): the old screen and a line asking for it again */
  await page.evaluate(() => { TC.myHistory = []; TC.audit = { reqs: [{ label: 'PSY 1102', status: 'satisfied', kind: 'major', ge: null, level: 'LN', code: 'R40-10', units: null, courses: null, options: ['PSY 1102'], oneOf: false }], counts: {}, overrides: [], catalog: 'Fall Semester 2026' }; });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2000);
  ok((await page.locator('.pc-again').count()) === 1 && (await page.locator('[data-a="plYear"]').count()) > 0 && !(await page.locator('.pc-still').count()), 'rules: a report saved before this build keeps the old screen, with "Upload your report again to see which class filled each requirement"');
  /* a save that fails: no "Your report changed" sheet for changes that weren't saved */
  const sh = await page.evaluate(async () => { UI.dpr = { rows: [], audit: { ok: true, reqs: [{ label: 'PSY 1102', status: 'not', kind: 'major', level: 'LN', code: 'R40-10', options: ['PSY 1102'], used: [], listed: [] }] }, program: { catalog: 'Fall Semester 2026' } };
    TC.saveDpr = async () => null; const real = TC.saveAudit; TC.saveAudit = async (a, prog) => { UI.dprDiff = auditDiff(TC.audit, a); return 'Couldn’t save what your report says'; };
    await A.dprSave(); TC.saveAudit = real; return UI.sheet && UI.sheet.type; });
  ok(sh !== 'dprDiff', 'rules: a report that didn’t save never says "Your report changed"', sh);
  ok(log.errors.length === 0, 'rules: no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [
  ("const names = Object.keys(tests).filter(n => !only || n === only);", TESTS + "const names = Object.keys(tests).filter(n => !only || n === only);", 'tests'),
  # the stored row now carries the classes the report used and the ones it listed
  ("Object.keys(row).sort().join() === 'code,courses,ge,kind,label,level,oneOf,options,status,units'", "Object.keys(row).sort().join() === 'code,courses,ge,kind,label,level,listed,oneOf,options,status,units,used'", 'audit-keys'),
  ("ok(aud && aud.requirements.every(b => Object.keys(b).sort().join() === 'code,courses,ge,kind,label,level,oneOf,options,status,units'), 'save: each line is only its words, verdict, kind, code, counts and classes — no note, nothing else'", "ok(aud && aud.requirements.every(b => Object.keys(b).sort().join() === 'code,courses,ge,kind,label,level,listed,oneOf,options,status,units,used'), 'save: each line is only its words, verdict, kind, code, counts, classes and the classes used/listed — no note, nothing else'", 'read-keys'),
  # Past classes is the report's lines now: a class shows in a line's "used" words, not as a code chip
  ("const add = await page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row, #scroll .pc-orow')].map(r => [((r.querySelector('.pc-cc') || {}).innerText || '').trim(), !!r.querySelector('.pc-add')]).filter(([c]) => c));\n  const has = c => add.find(([k]) => k === c);",
   "await openGroups(page);\n  const add = await page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row, #scroll .pc-orow')].map(r => [[...r.querySelectorAll('.pc-used, .pc-cc')].map(e => e.innerText.replace(/\\s+/g, ' ').trim()).join(' | '), !!r.querySelector('.pc-add')]).filter(([c]) => c));\n  const has = c => add.find(([k]) => k.split(' | ').some(x => x.startsWith(c + ' ') || x === c));", 'xfer-cont-add'),
  # the first-term transfer: "Area 2 or 5" is UD 2/5 now, and ES 3350 (UD 2/5) is being taken → in progress
  # (the Report read, before the save, still says 18: "Area 2 or 5" is covered by ES 3350 only once it's in My Classes)
  # (after the review) "Area 2 or 5" is UD 2/5 now, but ES 3350 is the class the report put under USCP: placed, so it
  # covers no other line by area — 18 of 30 stays
])
# pastByReport and dprTransferFirst looked at the flowchart spots under a report: those show only for a semester
# catalog now, under the report's own lines — scope the rows to the flowchart's
s = open(os.path.join(H, 'check-app.mjs'), encoding='utf-8').read()
old = "L('SS 1120', 'in_progress', { options: ['SS 1120'] })], counts: {}, overrides: [{ code: 'R797-30' }] };"
new = "L('SS 1120', 'in_progress', { options: ['SS 1120'] })], counts: {}, overrides: [{ code: 'R797-30' }], catalog: 'Fall Semester 2026' };"
s = s.replace("const L = (label, status, extra) => Object.assign({ label, status, kind: 'major', ge: null, level: 'LN', code: null, units: null, courses: null, options: [], oneOf: false }, extra || {});\n    TC.audit = { reqs: [\n      L('1B: Critical", "const L = (label, status, extra) => Object.assign({ label, status, kind: 'major', ge: null, level: 'LN', code: null, units: null, courses: null, options: [], oneOf: false, used: [], listed: [] }, extra || {});\n    TC.audit = { reqs: [\n      L('1B: Critical")
if old in s: s = s.replace(old, new)
i = s.index("tests.pastByReport = async () => {"); j = s.index("tests.planColors = async () => {")
blk = s[i:j]
blk2 = blk.replace("const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-row')]", "const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-fhd ~ * .pc-row, .pc-fhd ~ .pc-row')]")
s = s[:i] + blk2 + s[j:]
i = s.index("tests.dprTransferFirst = async () => {"); j = s.index("tests.dprTransferContinuing = async () => {")
blk = s[i:j]
blk2 = blk.replace("const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-row')]", "const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-fhd ~ * .pc-row, .pc-fhd ~ .pc-row')]")
s = s[:i] + blk2 + s[j:]
open(os.path.join(H, 'check-app.mjs'), 'w', encoding='utf-8').write(s)
print('edit-tests-dpr-truth: done')

# ---- mutants: each breaks one promise of this build; check-app must fail on every one ----
MUT = [
 # the reader (planner.js)
 ("truth: the classes a line used aren't kept", "      if(ru&&/[A-Z]/.test(ru[3]))usedAdd(cur,ru);\n", "", "dprReaderUsed", "planner"),
 ("truth: a used class keeps no term", "    var e={c:c,t:t}; if(n&&n!==c)e.n=n;", "    var e={c:c,t:''}; if(n&&n!==c)e.n=n;", "dprReaderUsed", "planner"),
 ("truth: a quarter number isn't translated", "    if(CPSUBJ.test(m[3])){ n=(h&&h.cur)||(cross&&cross[c])||null;", "    if(false){ n=(h&&h.cur)||(cross&&cross[c])||null;", "dprReaderUsed", "planner"),
 ("truth: transfer credit under a line isn't marked", "    if((h&&h.x)||!CPSUBJ.test(m[3])||!/^\\d{3,4}[A-Z]{0,2}$/.test(m[4]))e.x=true;", "    if(false)e.x=true;", "dprStressQuarter", "planner"),
 ("truth: a class being taken under a line isn't marked", "    else if(isNow(c,t)||(n&&isNow(n,t)))e.p=true;", "    else if(false)e.p=true;", "dprReaderUsed", "planner"),
 ("truth: an option's classes don't reach the requirement that counts", "        b.atomic=true; kids.forEach(function(x){ x.inOption=true; usedMerge(b,x);", "        b.atomic=true; kids.forEach(function(x){ x.inOption=true;", "dprReaderUsed", "planner"),
 ("truth: a listed-but-not-counted class isn't flagged", "    b.listed=b.options.filter(function(c){ return (done[c]||done[canon(c)])&&!mine[canon(c)]; }).slice(0,10); });", "    b.listed=[]; });", "dprReaderUsed", "planner"),
 ("truth: a failed class counts as a conflict", "_pass:!!gradeTok&&/^(?:[A-D][+-]?|CR|P|333|[1-7]00)$/.test(gradeTok),", "_pass:!!gradeTok&&!/^(?:W|IC|RP)$/.test(gradeTok),", "dprTruthRules", "planner"),
 ("truth: a class used for another line counts as a conflict", "    var mine=anyUsed;", "    var mine={}; (b.used||[]).forEach(function(e){ mine[canon(e.c)]=1; if(e.n)mine[canon(e.n)]=1; });", "dprTruthRules", "planner"),
 ("truth: a NOTE naming a code ends a line's table", "&&!/^NOTE\\s*:/i.test(ln)&&!DPR_UNITLINE.test(ln)){ var oc=dprCode(ln);", "&&!DPR_UNITLINE.test(ln)){ var oc=dprCode(ln);", "dprTruthRules", "planner"),
 ("truth: a major line that counts for GE mapped to any class of the area", "  if (/\\(\\s*GE\\b[^)]*\\)\\s*$/i.test(l)) return [];", "", "dprTruthRules", None),
 ("truth: one class covers two lines by area", "    covered.set(b, by); spent.add(k(by));", "    covered.set(b, by);", "dprTruthRules", None),
 ("truth: a class the report placed covers another line by area", "by = mine.find(c => !placed.has(k(c)) && !spent.has(k(c))", "by = mine.find(c => !spent.has(k(c))", "dprTruthRules", None),
 ("truth: a report saved before this build shows an empty screen", "  if (X && !fresh && L) return", "  if (false) return", "dprTruthRules", None),
 ("truth: the diff sheet opens for a report that didn't save", "      if (!e2 && UI.dprDiff && !UI.dprDiff.same) UI.sheet", "      if (UI.dprDiff && !UI.dprDiff.same) UI.sheet", "dprTruthRules", None),
 ("truth: the wrong attempt's professor", "  return rows.find(h => h.term === t && String(h.year) === y) || (rows.length === 1 ? rows[0] : null);", "  return rows.find(h => h.term === t && String(h.year) === y) || rows[0] || null;", "dprTruthRules", None),
 ("truth: the closing free-electives table filed under the last line", "    if(cur&&cur.code&&/\\(R[^)]*\\)\\**\\s*$/.test(ln)&&!/^NOTE\\s*:/i.test(ln)&&!DPR_UNITLINE.test(ln)){ var oc=dprCode(ln); if(oc&&oc.code!==cur.code){ cur=null; continue; } }\n", "", "dprStressDupes", "planner"),
 ("truth: the printed date isn't kept", "  try{ if(audit&&printed)audit.printed=", "  try{ if(false)audit.printed=", "dprReaderUsed", "planner"),
 ("truth: a used class can carry anything (the title)", "    var e={c:c,t:t}; if(n&&n!==c)e.n=n;", "    var e={c:c,t:t,title:ln}; if(n&&n!==c)e.n=n;", "dprReaderUsed", "planner"),
 ("truth: a verdict wrapping across a page break loses its code", "          if(DPR_FURN.test(pl)||(!pl&&DPR_FURN.test(String(lines[pk+1]||'').trim())))continue;\n", "", "dprStressQuarter", "planner"),
 # stored (index.html)
 ("truth: the account doesn't keep the used classes", "    used: (b.used || []).filter(e => e && AUDIT_USED.test(e.c || '') && AUDIT_TERM.test(e.t || '')).slice(0, 40)", "    used: [].slice(0, 40)", "dprStressQuarter", None),
 ("truth: the account doesn't keep the listed classes", "    listed: (b.listed || []).filter(c => AUDIT_CODE.test(c)).slice(0, 10) };", "    listed: [] };", "dprStressQuarter", None),
 ("truth: the printed date isn't stored", "printed_on: (a && /^\\d{4}-\\d{2}-\\d{2}$/.test(a.printed || '')) ? a.printed : null,", "printed_on: null,", "dprStressQuarter", None),
 # GE areas
 ("truth: quarter GE areas aren't matched to today's", "  if (b.ge && GE_QTR[b.ge]) return GE_QTR[b.ge];", "  if (b.ge && GE_QTR[b.ge]) return [b.ge];", "dprStressMixed", None),
 ("truth: Area E isn't an extra 4B", "D1: ['4A'], D2: ['4B'], DUD: ['UD4'], E: ['4B'], F: ['6'],", "D1: ['4A'], D2: ['4B'], DUD: ['UD4'], E: [], F: ['6'],", "dprStressMixed", None),
 ("truth: the C elective isn't 3A or 3B", "  if (/^Lower[- ]division C Elective\\b/i.test(l)) return ['3A', '3B'];", "  if (/^Lower[- ]division C Elective\\b/i.test(l)) return [];", "dprStressMixed", None),
 ("truth: a semester UD line's words don't name its area", "  if (/^(?:Area\\s*2\\s*or\\s*5\\s*:\\s*(?:UD|Upper)|UD\\s*2\\s*\\/\\s*5\\b|Upper[- ]division (?:Scientific|Science|Math))/i.test(l)) return ['U25'];", "  if (false) return ['U25'];", "dprTruthRules", None),
 ("truth: the Planner's picks ignore the area map", "plGeArea(b).forEach(a => { (byArea[a] = byArea[a] || []).push(b); }); });", "(b.kind === 'ge' && b.ge ? [b.ge] : []).forEach(a => { (byArea[a] = byArea[a] || []).push(b); }); });", "dprStressMixed", None),
 ("truth: a quarter catalog's units compared to semester units as they are", "    if (b.units && b.units.need != null && u != null && (qtr ? u * 1.5 : u) < +b.units.need) return;", "    if (b.units && b.units.need != null && u != null && u < +b.units.need) return;", "dprStressQuarter", None),
 # Past classes
 ("truth: Past classes still draws the flowchart over the report", "  if (X) return (none ? dprFirstCard() : '') + `<div class=\"pc-pg\">${pcSummary(L, P) + pcReportView(X, L) + pcBtns()}</div>`;\n", "", "dprStressQuarter", None),
 ("truth: the flowchart years shown for a quarter catalog", "  const sem = /semester/i.test(TC.audit.catalog || '');", "  const sem = true;", "dprStressQuarter", None),
 ("truth: the flowchart years hidden for a semester catalog too", "  const sem = /semester/i.test(TC.audit.catalog || '');", "  const sem = false;", "dprStressDupes", None),
 ("truth: Still needed leaves out what's in progress", "  const still = X.open.concat(X.unknown, X.inprog.filter(b => !X.open.includes(b)));", "  const still = X.open.concat(X.unknown);", "dprStressQuarter", None),
 ("truth: a line's classes aren't named", "  const parts = u.slice(0, 3).map(e =>", "  const parts = u.slice(0, 0).map(e =>", "dprStressQuarter", None),
 ("truth: today's number isn't shown", "${e.n && e.n !== e.c ? ` <i>→</i> ${esc(e.n)}` : ''}", "", "dprStressQuarter", None),
 ("truth: the conflict isn't shown", "      + ((b.listed || []).length ? `<span class=\"pc-look\">Needs a look:", "      + (false ? `<span class=\"pc-look\">Needs a look:", "dprStressQuarter", None),
 ("truth: the catalog line is missing", "  const cat = X && TC.audit.catalog ? `<div class=\"pc-cat\">", "  const cat = false ? `<div class=\"pc-cat\">", "dprStressQuarter", None),
 ("truth: Units only lists used classes too", "  const rest = pcHist().filter(h => !usedK.has(pcK(h.code)));", "  const rest = pcHist();", "dprStressQuarter", None),
 ("truth: no flowchart means no Past classes even with a report", "  if (!L && !auditLines(TC.audit, null)) return", "  if (!L) return", "dprStressNoMajor", None),
 ("truth: no flowchart means no upload card", "  if (!L) return (plNoRecord() && !TC.audit && !plSkipped() ? dprFirstCard() : '') + `<div class=\"card tc-sec\"", "  if (!L) return `<div class=\"card tc-sec\"", "dprStressNoMajor", None),
 ("truth: a group's rows hidden when open", "    return open ? `<div class=\"pc-open\">${head}<div class=\"pc-term pc-grp\">${rows.map(b => pcReqRow(b, X, L, idx.get(b))).join('')}</div></div>` : head;", "    return head;", "dprStressQuarter", None),
 # re-upload
 ("truth: a new report says nothing of what changed", "  UI.dprDiff = auditDiff(TC.audit, a);", "  UI.dprDiff = null;", "dprStressMixed", None),
 ("truth: newly filled lines not found", "  const filled = N.live.filter(b => done(b) && was.has(kN.get(b)) && was.get(kN.get(b)).status === 'not').map(b => b.label);", "  const filled = [];", "dprStressMixed", None),
 ("truth: new lines not counted", "  const added = N.live.filter(b => !was.has(kN.get(b))).length;", "  const added = 0;", "dprStressMixed", None),
 ("truth: plans holding a now-done class not found", "if (s && doneNow.has(k(s.code)) && !stillOpen.has(k(s.code)) && !codes.includes(s.code)) codes.push(s.code);", "if (false) codes.push(s.code);", "dprStressMixed", None),
 ("truth: two same-word lines collapse into one", "const w = b.code || b.label; n[w] = (n[w] || 0) + 1; return [b, w + '#' + n[w]];", "const w = b.code || b.label; return [b, w];", "dprTruthRules", None),
 ("truth: a class that left the open list without its line being done is 'done now'", "O.open.forEach(b => { const nb = now.get(kO.get(b)); if (nb && done(nb)) (b.options || []).forEach(c => doneNow.add(k(c))); });", "O.open.forEach(b => { (b.options || []).forEach(c => doneNow.add(k(c))); });", "dprTruthRules", None),
 ("truth: a plan edited without a tap", "  dprDrop: x => { const [P, code] = String(x).split('|'); const prev = (TC.plans[P] || []).slice(), next = prev.filter(id => !(SEC[id] && SEC[id].code === code)); if (next.length === prev.length) return; TC.setPlan(P, next);", "  dprDrop: x => { const [P, code] = String(x).split('|'); const prev = (TC.plans[P] || []).slice(), next = prev.filter(id => !(SEC[id] && SEC[id].code === code)); if (next.length === prev.length) return; TC.setPlan('C', []); TC.setPlan(P, next);", "dprStressMixed", None),
 ("truth: the diff sheet never opens", "      if (!e2 && UI.dprDiff && !UI.dprDiff.same) UI.sheet = { type: 'dprDiff', d: UI.dprDiff, ret: UI.sheet };", "      if (false) UI.sheet = { type: 'dprDiff', d: UI.dprDiff, ret: UI.sheet };", "dprStressMixed", None),
]
lines = ''.join('  ' + json.dumps([n, a, b, t, g], ensure_ascii=False) + ',\n' for n, a, b, t, g in MUT)
edit('mutate.mjs', [("\n];\nconst html = fs.readFileSync(SRC, 'utf8');", "\n  /* the report as the source of truth (2026-10-11; edit-tests-dpr-truth-2026-10-11.py) */\n" + lines + "];\nconst html = fs.readFileSync(SRC, 'utf8');", 'mutants')])
print('edit-tests-dpr-truth: mutants done')

# ---- seven older mutants named code this build changed: re-aimed (same promise, new words) ----
REAIM = [
[
"  [\"taking now: dprParse doesn't pass the classes being taken\", \"audit=dprAudit(text, cross, taking);\", \"audit=dprAudit(text, cross, []);\", \"dprTakingNow\", \"planner\"],",
"  [\"taking now: dprParse doesn't pass the classes being taken\", \"audit=dprAudit(text, cross, taking, hist);\", \"audit=dprAudit(text, cross, [], hist);\", \"dprTakingNow\", \"planner\"],"
],
[
"  [\"save: a note rides along in the audit row\", \"options: (b.options || []).filter(c => /^[A-Z]{2,5} \\\\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf };\", \"options: (b.options || []).filter(c => /^[A-Z]{2,5} \\\\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf, note: String(b.note || '') };\", \"dprRead\"],",
"  [\"save: a note rides along in the audit row\", \"    listed: (b.listed || []).filter(c => AUDIT_CODE.test(c)).slice(0, 10) };\", \"    listed: (b.listed || []).filter(c => AUDIT_CODE.test(c)).slice(0, 10), note: String(b.note || '') };\", \"dprRead\"],"
],
[
"  [\"report: a class you're taking doesn't cover its line\", \"    covered.set(b, by);\\n\", \"\", \"plannerFromReport\"],",
"  [\"report: a class you're taking doesn't cover its line\", \"    covered.set(b, by); spent.add(k(by));\\n\", \"\", \"plannerFromReport\"],"
],
[
"  [\"split: Past classes puts the record first\", \"${pcSummary(L) + pcYears(LR) + (none ? '' : pcOther(L) + pcBtns())}</div>`;\", \"${(none ? '' : pcOther(L) + pcBtns()) + pcSummary(L) + pcYears(LR)}</div>`;\", \"pastSimple\"],",
"  [\"split: Past classes puts the record first\", \"${pcSummary(L, P) + pcYears(LR) + (none ? '' : pcOther(L) + pcBtns())}</div>`;\", \"${(none ? '' : pcOther(L) + pcBtns()) + pcSummary(L, P) + pcYears(LR)}</div>`;\", \"pastSimple\"],"
],
[
"  [\"dpr first: Past classes without the DPR card\", \"return (none ? dprFirstCard() : '') + `<div class=\\\"pc-pg\\\">${pcSummary(L)\", \"return `<div class=\\\"pc-pg\\\">${pcSummary(L)\", \"pastSimple\"],",
"  [\"dpr first: Past classes without the DPR card\", \"  return (none ? dprFirstCard() : '') + `<div class=\\\"pc-pg\\\">${pcSummary(L, P) + pcYears(LR)\", \"  return `<div class=\\\"pc-pg\\\">${pcSummary(L, P) + pcYears(LR)\", \"pastSimple\"],"
],
[
"  [\"picker: a tap outside closes everything\", \"    if (UI.sheet && (UI.sheet.type === 'pcProf' || UI.sheet.type === 'pcTerm') && UI.sheet.ret) { pcBack(UI.sheet); render(true); return; }\", \"\", \"pastProfPicker\"],",
"  [\"picker: a tap outside closes everything\", \"    if (UI.sheet && (UI.sheet.type === 'pcProf' || UI.sheet.type === 'pcTerm' || UI.sheet.type === 'dprDiff') && UI.sheet.ret) { pcBack(UI.sheet); render(true); return; }\", \"\", \"pastProfPicker\"],"
],
[
"  [\"past classes: counts the flowchart with a report in\", \"  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L, { F, N }); }\", \"\", \"dprTransferFirst\"],",
"  [\"past classes: counts the flowchart with a report in\", \"  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L || { major: (P || TC.profile || {}).major }, { F, N }); }\", \"\", \"dprTransferFirst\"],"
]
]
edit('mutate.mjs', [(a, b, 'reaim') for a, b in REAIM])
print('edit-tests-dpr-truth: re-aims done')
