#!/usr/bin/env python3
"""check-app.mjs edits for Past classes, option A simple (2026-10-10): the old ledger card, key, flowchart cells
and "Classes you've taken" list are gone, so the tests that read them now read the new screen. Replayable:
each edit swaps whole lines found by a unique piece of text.  python3 edit-tests-past-classes-2026-10-10.py"""
import sys, os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'check-app.mjs')
L = open(P, encoding='utf-8').read().split('\n')

def swap(find, new, count=1, also=0):
    """replace the line containing `find` (and the `also` lines after it) with `new` (a string, may hold \n)"""
    hits = [i for i, l in enumerate(L) if find in l]
    if len(hits) != count: sys.exit(f'edit-tests: "{find[:60]}" found {len(hits)}x (want {count})')
    i = hits[0]; L[i:i + 1 + also] = new.split('\n')

# ---- refreshShuffle: watch for the rise-in instead of one fixed wait (the merged build's reload is longer) -----
old = "  await pullOn(page, 120); await page.clock.runFor(700); await page.waitForTimeout(150); await page.clock.runFor(50); await page.waitForTimeout(100);"
if any(old in l for l in L):
    swap(old, r"""  /* watch for the rise-in, 100ms at a time (a fixed wait missed it once the merged build's reload grew) */
  await pullOn(page, 120); let finSeen = false;
  for (let i = 0; i < 40 && !finSeen; i++) { await page.clock.runFor(100); await page.waitForTimeout(40); finSeen = await page.evaluate(() => !!document.querySelector('.hfeed.fin')); }""")
    swap("ok(await page.evaluate(() => !!document.querySelector('.hfeed.fin')), 'refresh: the new cards animate in');", "  ok(finSeen, 'refresh: the new cards animate in');")

# ---- tests.planner ------------------------------------------------------------------------------------
swap("ok(/Business Administration/.test(t) && /2 of 33\\s*requirements filled/.test(t) && /4 in progress/.test(t)", r'''  /* 2026-10-10 (Tate's option A, simple): one number and one bar — the desktop's ledger behind it */
  const lg = await page.evaluate(() => { const L = TCPL.ledger(), b = document.querySelector('.pc-bar i'), bar = document.querySelector('.pc-bar'); return { F: L.F, N: L.N, T: L.T, cant: L.grid.flatMap(x => x.slots).filter(s => s.state === 'cant').length, w: b && b.style.width, label: bar && bar.getAttribute('aria-label') }; });
  ok(/2 of 33\s*filled/.test(t) && lg.F === 2 && lg.N === 33 && lg.T === 4 && lg.w === '6%' && lg.label === '2 of 33 filled', 'planner: the desktop’s ledger — 2 of 33 filled (31 + the 2 choice slots, checked since 2026-10-02), 4 in progress (one via the ENGL 1134 waiver); the bar is 2/33', lg);''')
swap("ok(/We can’t check 10 from your record/.test(t), 'planner: what it can’t judge is listed, not counted');",
     r'''  ok(!/requirements filled|We can’t check|in progress/.test(t), 'past: no legend, no in-progress or can’t-check lines — only the number', (t.match(/[\s\S]{0,60}(in progress|We can’t)[\s\S]{0,60}/) || [''])[0]);''')
# the key block: from "const key = ..." through the 375px check and the viewport reset
i = next(i for i, l in enumerate(L) if "const key = await page.evaluate(() => { const k = document.querySelector('.tc-key');" in l)
j = next(j for j in range(i, i + 14) if "await page.setViewportSize({ width: 390, height: 844 }); await tick(page, 300);" in L[j])
L[i:j + 1] = r'''  for (let i = 0; i < 6; i++) { const closed = page.locator('[data-a="plYear"][aria-expanded="false"]'); if (!(await closed.count())) break; await closed.first().click(); await tick(page, 150); }
  /* no key any more: each mark says what it is to a screen reader, and the can't-check spots are rows, not a list */
  const marks = await page.evaluate(() => ({ done: [...document.querySelectorAll('.pc-row.done .pc-dot')].map(d => d.innerText + '|' + d.getAttribute('aria-label')), taking: [...document.querySelectorAll('.pc-row.taking .pc-dot')].map(d => d.innerText + '|' + d.getAttribute('aria-label')), cant: [...document.querySelectorAll('.pc-row.cant .pc-dot')].map(d => d.innerText + '|' + d.getAttribute('aria-label')), key: !!document.querySelector('.tc-key') }));
  ok(!marks.key && marks.done.length && marks.done.every(x => x === '✓|Done') && marks.taking.length === 4 && marks.taking.every(x => x === '◐|In progress') && marks.cant.length === lg.cant && lg.cant === 10 && marks.cant.every(x => /^\?\|Mark .+ done$/.test(x)), 'past: ✓ Done, ◐ In progress (all 4), ? Can’t check (all 10, as rows, each a circle to check off) — no key', marks);
  ok(await page.evaluate(() => { const r = [...document.querySelectorAll('.pc-row.cant')]; return r.length > 0 && r.every(x => { const e = x.querySelector('.pc-sr'); return !!e && /we can’t check this from your record/.test(e.textContent) && e.getBoundingClientRect().width <= 1; }); }), 'past: a can’t-check row says so to a screen reader (no words on screen)');'''.split('\n')
swap("ok(/PHIL 3331/.test(t) && /Spring 2026/i.test(t) && /ENGL 1134\\s*AP \\/ IB credit/.test(t)", r'''  const t3 = await text(page);
  ok(/PHIL 3331\s*Business Ethics\s*Dov Mockridge/.test(t3) && /ENGL 1134\s*Writing and Rhetoric\s*AP \/ IB credit/.test(t3), 'past: each spot shows the class that filled it — its professor, or a waiver’s reason in the desktop’s words', t3.slice(0, 300));''')
swap("ok(/3 of 33\\s*requirements filled/.test(t), 'planner: the ledger moves when a class is logged'",
     r'''  ok(/3 of 33\s*filled/.test(t), 'planner: the ledger moves when a class is logged', (t.match(/\d+ of 33/) || [''])[0]);''')
swap("""await click(page, '[data-a="askRemoveHistory"][data-x="PHIL 3331"]');""", r'''  await click(page, '[data-a="pcOpen"][data-x="PHIL 3331|Spring|2026"]'); await tick(page, 200);
  await click(page, '#sheet [data-a="pcAskRemove"][data-x="PHIL 3331|Spring|2026"]');
  ok(/Remove PHIL 3331, Spring 2026\?/.test(await page.locator('#sheet').innerText()), 'planner: Remove names the class and its term');
  await click(page, '#sheet [data-a="pcRemove"]'); await tick(page, 400);
  ok(log.writes.some(x => x.table === 'class_history' && x.m === 'DELETE' && /code=eq\.PHIL/.test(x.query) && /term=eq\.Spring/.test(x.query) && /year=eq\.2026/.test(x.query)), 'planner: remove asks, then deletes that row (that term only)');''', also=2)

open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests-past-classes-2026-10-10: applied')

# ---- tests.plannerGrid --------------------------------------------------------------------------------
L = open(P, encoding='utf-8').read().split('\n')
i = next(i for i, l in enumerate(L) if l.startswith('tests.plannerGrid = async () => {'))
j = next(j for j in range(i, i + 30) if L[j] == '};')
L[i:j + 1] = r'''tests.plannerGrid = async () => {
  const { page, close, log } = await openApp({});
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500);
  const t = await text(page);
  ok(/Year 1\s*\d+ of \d+[\s\S]*Year 4\s*\d+ of \d+/.test(t) && !/Your flowchart|Classes you’ve taken/.test(t), 'grid: the flowchart by year, in one place with your classes (no separate cards)');
  const y1 = await page.locator('.pc-open').first().innerText();
  ok(/FALL/.test(y1) && /BUS 1100\s*Career Readiness I/.test(y1) && /✓\s*ENGL 1134\s*Writing and Rhetoric\s*AP \/ IB credit/.test(y1) && !/GE · Area 1A|GE Area 1A/.test(y1), 'grid: Year 1 is open, and the GE 1A spot names the class that fills it (the ENGL 1134 waiver, ✓) — the same state the ledger counts', y1.slice(0, 400));
  const bub = await page.locator('.pc-open').first().evaluate(o => [...o.querySelectorAll('.pc-term > .pc-termh')].map(h => h.innerText));
  ok(bub.join('|') === 'FALL|SPRING', 'grid: an open year shows its Fall and Spring as bubbles', bub);
  const heads = await page.locator('.pc-year').allInnerTexts();
  const judged = heads.reduce((a, h) => a + (+((h.match(/of (\d+)/) || [])[1] || 0)), 0);
  ok(judged === 33 && heads.every(h => /^Year \d\s*\d+ of \d+$/.test(h.trim())), 'grid: the years add up to the ledger’s 33 — each just “Year N · d of n”', heads);
  ok(await page.locator('.pc-open').count() === 1 && await page.locator('[data-a="plYear"][data-x="2"]').getAttribute('aria-expanded') === 'false', 'grid: later years start folded');
  await click(page, '[data-a="plYear"][data-x="2"]');
  ok(await page.locator('.pc-open').count() === 2 && await page.locator('.pc-open').nth(1).locator('.pc-row').count() > 3, 'grid: tapping a year opens it');
  await click(page, '.pc-open >> nth=0 >> [data-a="plLogSlot"][data-x="BUS 1100"]');
  ok(await page.locator('#lc-code').inputValue() === 'BUS 1100', 'grid: tapping a class to do (not offered this term) opens Log a class with its code filled in');
  ok(log.errors.length === 0, 'grid: no page errors', log.errors);
  await close();
};'''.split('\n')
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: plannerGrid')

# ---- tests.plannerQuickTick: same checks, the new rows' markup --------------------------------------------
L = open(P, encoding='utf-8').read().split('\n')
i = next(i for i, l in enumerate(L) if l.startswith('tests.plannerQuickTick = async () => {'))
j = next(j for j in range(i, i + 80) if L[j] == '};')
blk = '\n'.join(L[i:j + 1])
for a, b in [
    (""".tc-cell:has(.tc-ccode:text("BUS 3411")) .tc-ctitle""", """.pc-row:has(.pc-cc:text("BUS 3411")) .pc-main"""),
    ("""const cells = await page.locator('.tc-cell').evaluateAll(els => els.map(e => ({ t: e.querySelector('.tc-ctitle') ? e.querySelector('.tc-ctitle').innerText.trim() : '', code: e.querySelector('.tc-ccode') ? e.querySelector('.tc-ccode').innerText.trim() : '', all: e.innerText })));""",
     """const cells = await page.locator('.pc-row').evaluateAll(els => els.map(e => ({ t: e.querySelector('.pc-main') ? e.querySelector('.pc-main').innerText.trim() : '', code: e.querySelector('.pc-cc') ? e.querySelector('.pc-cc').innerText.trim() : '', all: e.innerText })));"""),
    ("""(\\d+) of \\d+\\s*requirements""", """(\\d+) of \\d+\\s*filled"""),
    (""".tc-cell:has(.tc-ccode:text("BUS 1100")) .tc-tick""", """.pc-row:has(.pc-cc:text("BUS 1100")) .tc-tick"""),
    ("""const c1 = page.locator('.tc-cell:has(.tc-ccode:text("BUS 1100"))');""", """const c1 = page.locator('.pc-row:has(.pc-cc:text("BUS 1100"))');"""),
    ("""await c1.locator('.tc-dot').innerText()""", """await c1.locator('.pc-dot').innerText()"""),
    (""".tc-cell:has(.tc-ccode:text("BUS 1100")) .tc-cbody[data-a="plLogSlot"]""", """.pc-row:has(.pc-cc:text("BUS 1100")) .pc-main[data-a="plLogSlot"]"""),
    (""".tc-cell:has-text("Calculus for Data Science I or Business Calculus")""", """.pc-row:has-text("Calculus for Data Science I or Business Calculus")"""),
    ("""await ch.locator('.tc-dot').innerText()""", """await ch.locator('.pc-dot').innerText()"""),
    (""".tc-cell.done:has(.tc-ccode:text("MATH 1267")) .tc-ctitle""", """.pc-row.done:has(.pc-cc:text("MATH 1267")) .pc-main"""),
    (""".tc-cell.done:has(.tc-ccode:text("MATH 1267"))""", """.pc-row.done:has(.pc-cc:text("MATH 1267"))"""),
]:
    if a not in blk: sys.exit('edit-tests quick-tick: missing ' + a[:60])
    blk = blk.replace(a, b)
L[i:j + 1] = blk.split('\n')
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: plannerQuickTick')

# ---- the major and the ledger: read from the ledger now that the summary is just the number ----------------
L = open(P, encoding='utf-8').read().split('\n')
swap("ok(/Experience & Event Management/.test(t) && /requirements filled/.test(t) && !/Recreation, Parks/.test(t)", r'''  const eemL = await page.evaluate(() => { const L = TCPL.ledger(); return L && { major: L.major, N: L.N }; });
  ok(eemL && eemL.major === 'Experience & Event Management' && new RegExp('\\d+ of ' + eemL.N + '\\s*filled').test(t) && !/Recreation, Parks/.test(t), 'majors: the old-name student’s Planner opens on Experience & Event Management with its ledger', { eemL, t: t.slice(0, 200) });''')
swap("ok(/Industrial Technology & Packaging/.test(t2) && /requirements filled/.test(t2) && /ITP 1100/.test(t2)", r'''  const itpL = await o.page.evaluate(() => { const L = TCPL.ledger(); return L && { major: L.major, N: L.N }; });
  ok(itpL && itpL.major === 'Industrial Technology & Packaging' && new RegExp('\\d+ of ' + itpL.N + '\\s*filled').test(t2) && /ITP 1100/.test(t2), 'majors: an ITP student’s Planner shows the ITP ledger and flowchart', { itpL, t: t2.slice(0, 200) });''')
swap("ok(/requirements filled/.test(t) && !/Finance concentration|Graduating Spring 2027/.test(t), 'schedule: the planner is the real ledger, not the prototype’s invented requirements');",
     r'''  ok(/\d+ of \d+\s*filled/.test(t) && !/Finance concentration|Graduating Spring 2027/.test(t), 'schedule: the planner is the real ledger, not the prototype’s invented requirements');''')
swap("ok(/Financial Management/.test(t) && !/Pick your concentration/.test(t), 'profile: the concentration picked on the desktop carries over (same origin, same major)', t.slice(0, 300));",
     r'''  const cc = await page.evaluate(() => ({ conc: TC.profile && TC.profile.concentration, unchosen: TCPL.ledger().concUnchosen }));
  ok(cc.conc === 'Financial Management' && cc.unchosen === 0 && !/Pick your concentration/.test(t), 'profile: the concentration picked on the desktop carries over (same origin, same major)', cc);''')
# the report's save now asks "Who taught these?" first (the fixture's classes have no professors), then the Planner asks what matters most
swap("ok(after.tab === 'schedule' && after.sub === 'planner' && after.sheet === 'plPrefs' && after.prefs && !after.busy, 'save: lands on the Planner, which asks what matters most (first open)', after);", r'''  ok(after.tab === 'schedule' && after.sub === 'planner' && after.sheet === 'pcWho' && !after.busy, 'save: lands on the Planner, with “Who taught these?” over it first', after);
  await click(page, '#sheet [data-a="pcWhoDone"].btn'); await tick(page, 600);
  const after2 = await page.evaluate(() => ({ sheet: UI.sheet && UI.sheet.type, prefs: !!document.querySelector('#sheet [data-a="plPrefsSave"]') }));
  ok(after2.sheet === 'plPrefs' && after2.prefs, 'save: then the Planner asks what matters most (first open)', after2);''')
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: majors, schedule, profile, dprRead')

# ---- new tests: the simple Past classes, a class's sheet, Who taught it?, Who taught these? ---------------
NEW = r'''/* Past classes, Tate's option A, simple (2026-10-10): the flowchart and the classes you've taken in one place —
   a spot names the class that filled it and its professor; the rest is "Other classes"; only what's needed. */
const PAST_HIST = [['COMS 1101', 'Spring', 2024, null], ['BUS 2214', 'Fall', 2024, null], ['ECON 3021', 'Spring', 2026, null], ['BUS 3310', 'Winter', 2026, null], ['ITP 3371', 'Winter', 2026, null],
  ['BUS 4434', 'Summer', 2026, null], ['BUS 4439', 'Spring', 2026, null], ['FSN 1121', 'Spring', 2024, null], ['NUTR 1101', 'Fall', 2023, null], ['AP 300', 'Fall', 2025, '🌍']]
  .map(([code, term, year, professor]) => ({ user_id: FX.ME.id, code, term, year, professor }));
const PAST_T = (extra) => Object.assign({}, FX.TABLES, { class_history: FX.TABLES.class_history.concat(PAST_HIST) }, extra || {});
const toPast = async page => { await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2500); };
const openYears = async page => { for (let i = 0; i < 6; i++) { const c = page.locator('[data-a="plYear"][aria-expanded="false"]'); if (!(await c.count())) break; await c.first().click(); await tick(page, 150); } };
tests.pastSimple = async () => {
  const { page, close, log } = await openApp({ tables: PAST_T(), height: 2400 });
  await toPast(page); await openYears(page);
  const t = await text(page);
  ok(/^\s*\d+ of \d+\s*filled/.test(t.slice(t.indexOf('Past classes') + 12)) && !/Degree Progress Report/.test(t) && !/×/.test(t) && !(await page.locator('#scroll [data-a="askRemoveHistory"]').count()), 'past: the number first; no report row without a report; no × on any row', t.slice(0, 200));
  const rows = await page.evaluate(() => [...document.querySelectorAll('.pc-row')].map(r => ({ st: r.className.replace('pc-row', '').trim(), main: (r.querySelector('.pc-main') || {}).innerText || '', pf: (r.querySelector('.pc-pf') || {}).innerText || '', add: !!r.querySelector('.pc-add') })));
  const coms = rows.find(r => /COMS 1101/.test(r.main)), bus = rows.find(r => /BUS 2214/.test(r.main));
  ok(coms && coms.st === 'done' && /^COMS 1101\s*Public Speaking$/.test(coms.main.trim()) && coms.add && !rows.some(r => /GE Area 1C/.test(r.main)), 'past: a GE spot names the class that filled it (COMS 1101 for 1C), with “+ Professor”', coms);
  ok(bus && bus.st === 'done' && /^BUS 2214\s*Financial Accounting$/.test(bus.main.trim()) && bus.add, 'past: a class spot shows the class you took, with “+ Professor”', bus);
  const phil = rows.find(r => /PHIL 3331/.test(r.main));
  ok(phil && phil.pf === 'Dov Mockridge' && !phil.add, 'past: a class with its professor shows the name, no button', phil);
  const taking = rows.filter(r => r.st === 'taking');
  ok(taking.length && taking.every(r => !r.add), 'past: taking now has nothing to add', taking);
  ok(rows.filter(r => r.st === 'need' || r.st === 'cant').every(r => !r.pf && !r.add), 'past: spots still to take, and ones it can’t check, are one line', rows.filter(r => (r.st === 'need' || r.st === 'cant') && (r.pf || r.add)));
  /* Other classes: the record's classes with no spot; four, then See all */
  const oth = await page.evaluate(() => { const c = document.querySelector('.pc-oth'); return c && { head: c.querySelector('.pc-hd').innerText.replace(/\s+/g, ' '), rows: [...c.querySelectorAll('.pc-orow')].map(r => ({ main: r.querySelector('.pc-main').innerText.replace(/\s+/g, ' '), add: !!r.querySelector('.pc-add'), btn: r.querySelector('.pc-main').tagName })), more: (c.querySelector('[data-a="pcAll"]') || {}).innerText || '' }; });
  const n = oth && +oth.head.replace(/\D+/g, '');
  ok(oth && /^Other classes \d+$/.test(oth.head) && n > 4 && oth.rows.length === 4 && oth.more === 'See all ' + n, 'past: “Other classes” — four rows, then “See all N”', oth);
  await click(page, '[data-a="pcAll"]');
  const all = await page.evaluate(() => [...document.querySelectorAll('.pc-oth .pc-orow')].map(r => ({ main: r.querySelector('.pc-main').innerText.replace(/\s+/g, ' '), add: !!r.querySelector('.pc-add'), pf: (r.querySelector('.pc-pf') || {}).innerText || '' })));
  const ap = all.find(r => /^AP 300/.test(r.main));
  ok(all.length === n && !(await page.locator('[data-a="pcAll"]').count()) && ap && !ap.add && !ap.pf && all.filter(r => r !== ap).every(r => r.add), 'past: See all shows every one; transfer credit (AP 300) gets no “+ Professor”, the others do', all);
  ok(await page.locator('.pc-btns [data-a="sheet"][data-x="logClass"]').count() === 1 && await page.locator('.pc-btns input[data-in="dprfile"]').count() === 1, 'past: + Log a class and Upload report at the bottom');
  ok(!/We can’t check|Cal Poly’s degree audit decides|Tap the circle/.test(await text(page)), 'past: no help lines or footnotes');
  /* a long concentration name wraps inside the summary card on a 320px phone */
  await page.setViewportSize({ width: 320, height: 2400 }); await page.evaluate(() => render(true)); await tick(page, 300);
  const cc = await page.evaluate(() => { const c = document.querySelector('.pc-sum'); if (!c) return null; const r = c.getBoundingClientRect(), pr = parseFloat(getComputedStyle(c).paddingRight), chips = [...c.querySelectorAll('.pc-conc .chip')]; return { n: chips.length, out: chips.filter(e => e.getBoundingClientRect().right > r.right - pr + 0.5 || e.scrollWidth > e.clientWidth + 1).map(e => e.textContent) }; });
  ok(cc && cc.n > 0 && !cc.out.length, 'past: at 320px every concentration name fits inside the summary card', cc);
  await page.setViewportSize({ width: 390, height: 2400 }); await page.evaluate(() => render(true)); await tick(page, 300);
  /* a row you checked off (“Marked done by you”) is in the contrast scan too */
  await page.evaluate(() => { for (let y = 1; y <= 5; y++) UI.plYears[y] = true; const c = TCPL.ledger().grid.flatMap(t => t.slots).find(s => s.state === 'need' && !s.code && s.type === 'ge'); if (c) A.plMark(c.id); }); await tick(page, 600);
  ok(await page.locator('.pc-pf.tc-mine').count() === 1, 'past: (a GE row checked off, for the contrast scan)');
  /* contrast, light and dark */
  for (const th of ['light', 'dark']) {
    await page.evaluate(th => { document.documentElement.setAttribute('data-theme', th); render(true); }, th); await tick(page, 300);
    const bad = await page.evaluate(scan => (new Function('return ' + scan))()(4.5).filter(x => /\bpc-/.test(x.cls)), CONTRAST_SCAN.toString());
    ok(!bad.length, `past: every word on Past classes is 4.5:1 or better (${th})`, bad.slice(0, 4));
  }
  ok(log.errors.length === 0, 'past: no page errors', log.errors);
  await close();
  /* with a report: one row with the report's own count, which opens the Planner */
  const reqs = [RQ('Approved Elective', 'not', { kind: 'conc', code: 'R179-10' }), RQ('Business Major Senior Project', 'not', { code: 'R-0037', oneOf: true, options: ['BUS 4461', 'BUS 4462'] }), RQ('BUS 3346', 'satisfied', { code: 'R35-60', options: ['BUS 3346'] })];
  const r2 = await openApp({ tables: PAST_T({ degree_audit: [{ user_id: FX.ME.id, catalog: 'Fall Quarter 2023', major: 'BUS', concentration: null, units_used: 170, units_needed: 10, requirements: reqs, overrides: [], read_at: '2026-10-08T00:00:00Z' }] }) });
  await toPast(r2.page);
  const link = await r2.page.locator('.pc-link').innerText().catch(() => '');
  ok(/^Degree Progress Report\s*2 left$/.test(link.trim()), 'past: with a report, one row — “Degree Progress Report · 2 left”, the same count as the Planner', link);
  await click(r2.page, '.pc-link'); await tick(r2.page, 400);
  ok(await r2.page.evaluate(() => S.schedTab) === 'planner', 'past: that row opens the Planner');
  await r2.close();
  /* nothing on the record yet: the report's upload card leads, and there's no Other card or bottom buttons */
  const r4 = await openApp({ tables: NOREC() });
  await toPast(r4.page);
  ok(await r4.page.locator('#scroll .tc-dpr').count() === 1 && await r4.page.locator('.pc-oth, .pc-btns').count() === 0 && await r4.page.evaluate(() => { const d = document.querySelector('#scroll .tc-dpr'), s = document.querySelector('.pc-sum'); return !!(d && s && (d.compareDocumentPosition(s) & Node.DOCUMENT_POSITION_FOLLOWING)); }), 'past: an empty record starts with the report’s upload card');
  await r4.close();
  /* a class taken twice: the spot holds the first attempt; the retake is under Other, with its own term */
  const r5 = await openApp({ tables: PAST_T({ class_history: FX.TABLES.class_history.concat(PAST_HIST, [{ user_id: FX.ME.id, code: 'BUS 2214', term: 'Spring', year: 2025, professor: 'Esme Samplesworth' }]) }), height: 2400 });
  await toPast(r5.page); await openYears(r5.page); await click(r5.page, '[data-a="pcAll"]');
  const tw = await r5.page.evaluate(() => ({ spot: [...document.querySelectorAll('.pc-row.done')].filter(r => /BUS 2214/.test(r.innerText)).map(r => r.querySelector('.pc-main').dataset.x + '|' + ((r.querySelector('.pc-pf') || {}).innerText || (r.querySelector('.pc-add') ? 'add' : ''))), other: [...document.querySelectorAll('.pc-oth .pc-orow')].filter(r => /BUS 2214/.test(r.innerText)).map(r => r.querySelector('.pc-main').dataset.x + '|' + ((r.querySelector('.pc-pf') || {}).innerText || '')) }));
  ok(tw.spot.join() === 'BUS 2214|Fall|2024|add' && tw.other.join() === 'BUS 2214|Spring|2025|Esme Samplesworth', 'past: a retaken class shows each attempt once — the first in its spot, the retake under Other with its own professor', tw);
  await r5.close();
  /* taking now: the professor of your section (here a Free Elective spot holds BUS 3438, Bram Fixturesen's section) */
  const r3 = await openApp({ height: 2400 });
  await toPast(r3.page); await openYears(r3.page);
  const tk = await r3.page.evaluate(() => [...document.querySelectorAll('.pc-row.taking')].map(r => ({ main: r.querySelector('.pc-main').innerText.replace(/\s+/g, ' '), pf: (r.querySelector('.pc-pf') || {}).innerText || '', add: !!r.querySelector('.pc-add') })));
  ok(tk.some(r => /^BUS 3438/.test(r.main) && r.pf === 'Bram Fixturesen' && !r.add) && tk.every(r => !r.add), 'past: taking now shows your section’s professor', tk);
  await r3.close();
};
/* Tap a class on your record: its professor and term, Rate, Remove — a term change is an UPDATE of that row only */
tests.pastClassSheet = async () => {
  const { page, close, log, tables } = await openApp({ tables: PAST_T(), height: 1400 });
  await toPast(page); await openYears(page);
  await click(page, '[data-a="pcOpen"][data-x="PHIL 3331|Spring|2026"]'); await tick(page, 200);
  let sh = await page.locator('#sheet').innerText();
  ok(/PHIL 3331/.test(sh) && /Business Ethics/.test(sh) && /Professor\s*Dov Mockridge/.test(sh) && /Term\s*Spring 2026/.test(sh) && /Rate Dov Mockridge/.test(sh) && /Remove from my record/.test(sh), 'class sheet: code, name, Professor ›, Term ›, Rate them, Remove', sh);
  ok(await page.locator('#sheet [data-a="rateProf"][data-x="dov mockridge"][data-y="PHIL 3331"]').count() === 1, 'class sheet: Rate opens that professor’s form for this class');
  await click(page, '#sheet [data-a="pcTerm"]'); await tick(page, 200);
  await page.locator('#pc-term').selectOption('Fall'); await page.locator('#pc-year').selectOption('2025');
  await click(page, '#sheet [data-a="pcTermSave"]'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'class_history' && x.m === 'PATCH');
  ok(w.length === 1 && w.every(x => !/is\.null/.test(x.query)) && JSON.stringify(w[0].body) === JSON.stringify({ term: 'Fall', year: 2025 }) && /user_id=eq\.11111111/.test(w[0].query) && /code=eq\.PHIL(\+|%20)3331/.test(w[0].query) && /term=eq\.Spring/.test(w[0].query) && /year=eq\.2026/.test(w[0].query), 'class sheet: a new term updates only that row (its code, its old term and year)', w);
  sh = await page.locator('#sheet').innerText();
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcClass' && /Term\s*Fall 2025/.test(sh), 'class sheet: back on the class, with the new term', sh);
  /* a one-tap row (no term): Term starts blank — Save asks for a choice rather than writing one */
  await click(page, '#sheet [data-a="closeSheet"]');
  await page.evaluate(() => quickLog('BUS 1100', 'x')); await tick(page, 600);
  await click(page, '[data-a="pcOpen"][data-x="BUS 1100||"]'); await tick(page, 200);
  ok(/Term\s*Add/.test(await page.locator('#sheet').innerText()), 'class sheet: a class logged without a term says Term · Add');
  await click(page, '#sheet [data-a="pcTerm"]'); await tick(page, 200);
  const blank = await page.evaluate(() => ({ t: document.getElementById('pc-term').value, y: document.getElementById('pc-year').value }));
  const before = log.writes.filter(x => x.m === 'PATCH').length;
  await click(page, '#sheet [data-a="pcTermSave"]'); await tick(page, 300);
  ok(blank.t === '' && blank.y === '' && log.writes.filter(x => x.m === 'PATCH').length === before && /Choose the term and the year/.test(await page.locator('#sheet').innerText()), 'term: nothing is chosen for you — blank until you pick, and Save says so', blank);
  await page.locator('#pc-term').selectOption('Fall'); await page.locator('#pc-year').selectOption('2023');
  await click(page, '#sheet [data-a="pcTermSave"]'); await tick(page, 600);
  const wn = log.writes.filter(x => x.table === 'class_history' && x.m === 'PATCH').slice(before);
  ok(wn.length === 1 && /code=eq\.BUS(\+|%20)1100/.test(wn[0].query) && /term=is\.null/.test(wn[0].query) && /year=is\.null/.test(wn[0].query) && JSON.stringify(wn[0].body) === JSON.stringify({ term: 'Fall', year: 2023 }), 'term: a row with no term is found by “is null” — one write', wn);
  /* a class with no professor: Professor reads Add, and no Rate */
  await click(page, '#sheet [data-a="closeSheet"]');
  await click(page, '[data-a="pcOpen"][data-x="BUS 2214|Fall|2024"]'); await tick(page, 200);
  sh = await page.locator('#sheet').innerText();
  ok(/Professor\s*Add/.test(sh) && !/Rate /.test(sh), 'class sheet: no professor yet — “Add”, and nothing to rate', sh);
  /* a class from long ago keeps its year in the list */
  await click(page, '#sheet [data-a="closeSheet"]');
  await page.evaluate(() => { TC.myHistory.push({ code: 'HIST 2223', term: 'Fall', year: 2012, professor: null }); UI.pcAll = true; render(true); }); await tick(page, 200);
  await click(page, '[data-a="pcOpen"][data-x="HIST 2223|Fall|2012"]'); await click(page, '#sheet [data-a="pcTerm"]'); await tick(page, 200);
  ok(await page.evaluate(() => document.getElementById('pc-year').value) === '2012', 'term: a 2012 class opens on 2012, not on a year it was never taken');
  await click(page, '#sheet [data-a="closeSheet"]'); await tick(page, 200);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcClass', 'term: its X goes back to the class');
  /* transfer credit: no professor row */
  await click(page, '#sheet [data-a="closeSheet"]'); await page.evaluate(() => { UI.pcAll = true; render(true); }); await tick(page, 200);
  await click(page, '[data-a="pcOpen"][data-x="AP 300|Fall|2025"]'); await tick(page, 200);
  ok(!(await page.locator('#sheet [data-a="pcProf"]').count()) && /Term\s*Fall 2025/.test(await page.locator('#sheet').innerText()), 'class sheet: transfer credit has no professor to add');
  await click(page, '#sheet [data-a="pcAskRemove"]'); await tick(page, 100);
  ok(/Remove AP 300, Fall 2025\?/.test(await page.locator('#sheet').innerText()), 'class sheet: Remove names the class and its term');
  await click(page, '#sheet [data-a="pcRemove"]'); await tick(page, 400);
  ok(log.writes.some(x => x.table === 'class_history' && x.m === 'DELETE' && /code=eq\.AP(\+|%20)300/.test(x.query) && /term=eq\.Fall/.test(x.query) && /year=eq\.2025/.test(x.query)), 'class sheet: Remove asks, then deletes that row');
  /* a class taken twice: Remove takes off only the attempt you opened */
  tables.class_history.push({ user_id: FX.ME.id, code: 'BUS 2214', term: 'Spring', year: 2025, professor: null });
  await page.evaluate(() => TC.reloadHistory().then(() => { UI.pcAll = true; render(true); })); await tick(page, 400);
  await click(page, '[data-a="pcOpen"][data-x="BUS 2214|Spring|2025"]'); await tick(page, 200);
  await click(page, '#sheet [data-a="pcAskRemove"]'); await click(page, '#sheet [data-a="pcRemove"]'); await tick(page, 600);
  const left = await page.evaluate(() => TC.myHistory.filter(h => h.code === 'BUS 2214').map(h => h.term + ' ' + h.year));
  ok(left.join() === 'Fall 2024', 'class sheet: a class taken twice — Remove takes off only the attempt you opened', left);
  ok(log.errors.length === 0, 'class sheet: no page errors', log.errors);
  await close();
};
/* Who taught it? — only real names: teaching it now, or listed for it on PolyRatings (old codes through the crosswalk),
   or one the student searches for; nothing is filled until they pick */
tests.pastProfPicker = async () => {
  const poly = FX.POLY.map((p, i) => Object.assign({}, p, { courses: i === 0 ? ['COMS 101', 'PHIL 3331'] : i === 2 ? ['COMS 101', 'BUS 214'] : [] }));
  const { page, close, log } = await openApp({ tables: PAST_T(), poly, height: 1400 });
  await toPast(page); await openYears(page);
  await click(page, '.pc-row:has(.pc-cc:text("COMS 1101")) .pc-add'); await tick(page, 300);
  let names = await page.locator('#sheet .pc-opt .pc-on').allInnerTexts();
  const p0 = FX.POLY[0].firstName + ' ' + FX.POLY[0].lastName, p2 = FX.POLY[2].firstName + ' ' + FX.POLY[2].lastName;
  ok(/Who taught it\?/.test(await page.locator('#sheet').innerText()) && names.length === 2 && names.includes(p0) && names.includes(p2) && await page.locator('#sheet [data-a="pcProfSave"]').isDisabled(), 'picker: the professors PolyRatings lists for COMS 101 (= COMS 1101), and Save waits for a pick', names);
  ok(names[0] === (FX.POLY[0].numEvals >= FX.POLY[2].numEvals ? p0 : p2), 'picker: most-rated first', names);
  /* teaching it now comes first */
  await click(page, '#sheet [data-a="closeSheet"]');
  const cands = await page.evaluate(() => pcCands('PHIL 3331').map(o => o.name + (o.now ? '*' : '')));
  ok(cands[0] === 'Dov Mockridge*', 'picker: a professor teaching it now is listed first', cands);
  /* search: type, the list follows, the keyboard stays */
  await click(page, '.pc-row:has(.pc-cc:text("COMS 1101")) .pc-add'); await tick(page, 200);
  await page.evaluate(() => { window.__pcq = document.getElementById('pc-q'); });
  await page.locator('#sheet input[data-in="pcq"]').fill('fixtur'); await tick(page, 200);
  names = await page.locator('#sheet .pc-opt .pc-on').allInnerTexts();
  ok(names.some(n => /Fixturesen/.test(n)) && await page.evaluate(() => document.activeElement && document.activeElement.dataset.in === 'pcq' && document.getElementById('pc-q') === window.__pcq), 'picker: search finds any professor, and typing keeps the keyboard up (the same search box, never redrawn)', names);
  await page.locator('#sheet input[data-in="pcq"]').fill('Quinn Notlisted'); await tick(page, 200);
  names = await page.locator('#sheet .pc-opt .pc-on').allInnerTexts();
  ok(names.length === 1 && names[0] === 'Use “Quinn Notlisted”', 'picker: someone not listed can be typed in', names);
  await page.locator('#sheet input[data-in="pcq"]').fill(''); await tick(page, 200);
  await click(page, `#sheet .pc-opt:has-text("${p2}")`); await tick(page, 150);
  ok(await page.locator('#sheet .pc-opt.on').count() === 1 && !(await page.locator('#sheet [data-a="pcProfSave"]').isDisabled()), 'picker: a pick lights up and Save turns on');
  ok(!log.writes.some(x => x.table === 'class_history' && x.m === 'PATCH'), 'picker: nothing is saved until Save');
  await click(page, '#sheet [data-a="pcProfSave"]'); await tick(page, 600);
  const w = log.writes.filter(x => x.table === 'class_history' && x.m === 'PATCH');
  ok(w.length === 1 && JSON.stringify(w[0].body) === JSON.stringify({ professor: p2 }) && /code=eq\.COMS(\+|%20)1101/.test(w[0].query) && /term=eq\.Spring/.test(w[0].query) && /year=eq\.2024/.test(w[0].query), 'picker: Save writes that name to that class on your record', w);
  const row = await page.locator('.pc-row:has(.pc-cc:text("COMS 1101"))').innerText();
  ok(new RegExp(p2).test(row) && !/\+ Professor/.test(row) && !(await page.locator('#sheet .pc-opt').count()), 'picker: the row now shows them', row);
  ok(await page.evaluate(n => (TC.rateList || []).some(t => t.items.some(i => PROFS[i[0]] && PROFS[i[0]].name === n)), p2), 'picker: and they’re in Rate’s list to review');
  /* I don't remember: closes, writes nothing */
  const before = log.writes.length;
  await click(page, '.pc-row:has(.pc-cc:text("BUS 2214")) .pc-add'); await tick(page, 200);
  await click(page, '#sheet [data-a="pcProfNone"]'); await tick(page, 200);
  ok(!(await page.evaluate(() => UI.sheet)) && log.writes.length === before, 'picker: “I don’t remember” closes and saves nothing');
  ok(log.errors.length === 0, 'picker: no page errors', log.errors);
  await close();
  /* a refused save says so and stays */
  const f = await openApp({ tables: PAST_T(), poly, height: 1400, hook: (url, m) => url.pathname.endsWith('/class_history') && m === 'PATCH' ? { status: 500, body: '{}' } : null });
  await toPast(f.page); await openYears(f.page);
  await click(f.page, '.pc-row:has(.pc-cc:text("COMS 1101")) .pc-add'); await tick(f.page, 200);
  await click(f.page, `#sheet .pc-opt:has-text("${p0}")`); await click(f.page, '#sheet [data-a="pcProfSave"]'); await tick(f.page, 600);
  ok(await f.page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcProf' && await f.page.locator('#sheet .tc-err').count() === 1 && !(await f.page.locator('#sheet [data-a="pcProfSave"]').isDisabled()), 'picker: a refused save says so and keeps the pick to try again');
  await f.close();
  /* a write that changes nothing (refused, or the row moved) isn't "Saved" */
  const z = await openApp({ tables: PAST_T(), poly, height: 1400, hook: (url, m) => url.pathname.endsWith('/class_history') && m === 'PATCH' ? { status: 200, body: '[]' } : null });
  await toPast(z.page); await openYears(z.page);
  await click(z.page, '.pc-row:has(.pc-cc:text("COMS 1101")) .pc-add'); await tick(z.page, 200);
  await click(z.page, `#sheet .pc-opt:has-text("${p0}")`); await click(z.page, '#sheet [data-a="pcProfSave"]'); await tick(z.page, 600);
  ok(await z.page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcProf' && /Couldn’t save that/.test(await z.page.locator('#sheet').innerText()), 'picker: a write that changed nothing says so — never “Saved”');
  /* any redraw (a reload, the seats) keeps the search and its keyboard */
  await z.page.locator('#sheet input[data-in="pcq"]').fill('ad'); await z.page.evaluate(() => render(true)); await tick(z.page, 200);
  ok(await z.page.evaluate(() => document.activeElement && document.activeElement.id === 'pc-q' && document.activeElement.value === 'ad'), 'picker: a redraw while typing keeps the search box focused');
  /* the X goes back to the class it came from; so does a tap outside */
  await click(z.page, '#sheet [data-a="pcProfNone"]'); await tick(z.page, 200);
  await click(z.page, '[data-a="pcOpen"][data-x="COMS 1101|Spring|2024"]'); await click(z.page, '#sheet [data-a="pcProf"]'); await tick(z.page, 200);
  await click(z.page, '#sheet .xbtn'); await tick(z.page, 200);
  ok(await z.page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcClass', 'picker: its X goes back to the class sheet');
  await click(z.page, '#sheet [data-a="pcProf"]'); await tick(z.page, 200);
  await z.page.evaluate(() => A.closeSheet()); await tick(z.page, 200);
  ok(await z.page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcClass', 'picker: a tap outside goes back too');
  await z.close();
  /* PolyRatings didn't load: it says so */
  const g = await openApp({ tables: PAST_T(), poly: null, height: 1400 });
  await toPast(g.page); await openYears(g.page);
  await click(g.page, '.pc-row:has(.pc-cc:text("COMS 1101")) .pc-add'); await tick(g.page, 200);
  ok(/PolyRatings didn’t load/.test(await g.page.locator('#sheet').innerText()), 'picker: without PolyRatings it says only professors teaching it now are listed');
  await g.close();
};
/* Right after a report is saved: "Who taught these?" — the three latest terms' classes, never transfer credit */
tests.pastWhoTaught = async () => {
  const { page, close, log } = await openApp({ tables: NOREC() });
  await toPlanner(page);
  await uploadDpr(page, '.tc-dpr input[data-in="dprfile"]');
  await click(page, '[data-a="dprSave"]'); await tick(page, 2500);
  const got = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys : null);
  const hist = await page.evaluate(() => (TC.myHistory || []).map(h => [TCPL.canon(h.code) || h.code, h.term, h.year, h.professor]));
  const TO = { Winter: 0, Spring: 1, Summer: 2, Fall: 3 };
  const real = hist.filter(h => h[3] !== '🌍' && h[1] && h[2]).sort((a, b) => b[2] - a[2] || TO[b[1]] - TO[a[1]]);
  const latest = [...new Set(real.map(h => h[1] + ' ' + h[2]))].slice(0, 3);
  const want = real.filter(h => latest.includes(h[1] + ' ' + h[2])).map(h => [h[0], h[1], h[2]].join('|'));
  ok(got && got.length && JSON.stringify(got) === JSON.stringify(want) && got.every(k => !/^AP /.test(k)), 'who: after the save, “Who taught these?” lists the record’s latest terms (no transfer credit)', { got, hist });
  const sh = await page.locator('#sheet').innerText();
  ok(/Who taught these\?/.test(sh) && /\+ Add/.test(sh) && /Done/.test(sh) && !/Skip/.test(sh), 'who: one list with “+ Add”, and Done', sh.slice(0, 300));
  /* the X on the picker opened from the list goes back to the list */
  await click(page, '#sheet .pc-wrow >> nth=0'); await tick(page, 200);
  await click(page, '#sheet [data-a="pcProfNone"].xbtn'); await tick(page, 200);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcWho', 'who: the picker’s X goes back to the list');
  await click(page, '#sheet .pc-wrow >> nth=0'); await tick(page, 200);
  ok(await page.evaluate(() => UI.sheet.type) === 'pcProf', 'who: a row opens Who taught it?');
  const xf = await page.evaluate(() => { const keep = TC.myHistory; TC.myHistory = keep.concat([{ code: 'AP 300', term: 'Fall', year: 2026, professor: TCPL.abroadMark }, { code: 'ECON 3021', term: 'Fall', year: 2026, professor: null }]); const k = pcWhoKeys(); TC.myHistory = keep; return k; });
  ok(xf.includes('ECON 3021|Fall|2026') && !xf.some(k => /^AP 300/.test(k)), 'who: transfer credit in the latest term stays out; a class beside it is in', xf);
  await page.locator('#sheet input[data-in="pcq"]').fill('Ada'); await tick(page, 200);
  await click(page, '#sheet .pc-opt >> nth=0'); await click(page, '#sheet [data-a="pcProfSave"]'); await tick(page, 600);
  const back = await page.evaluate(() => ({ t: UI.sheet && UI.sheet.type, txt: document.getElementById('sheet').innerText }));
  ok(back.t === 'pcWho' && /Ada Examplewood/.test(back.txt), 'who: saving returns to the list, with the name in place of “+ Add”', back);
  await click(page, '#sheet [data-a="pcWhoDone"].btn'); await tick(page, 600);
  const done = await page.evaluate(() => ({ sheet: UI.sheet && UI.sheet.type, tab: S.schedTab, plan: !!document.querySelector('#scroll .pl-card, #scroll [data-a="plPrefsOpen"], #scroll .pk-card') }));
  ok(done.sheet !== 'pcWho' && done.tab === 'planner' && (done.sheet === null || done.sheet === 'plPrefs'), 'who: Done closes it, onto the Planner', done);
  ok(log.errors.length === 0, 'who: no page errors', log.errors);
  await close();
};

tests.planColors = async () => {'''
i = next(i for i, l in enumerate(L) if l.startswith('tests.planColors = async () => {'))
L[i:i + 1] = NEW.split('\n')
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: new past tests')

# ---- onbReportLast: the notification ask waits for "Who taught these?" to close ---------------------------
L = open(P, encoding='utf-8').read().split('\n')
swap("ok(/Report read/.test(await page.locator('#sheet').innerText()), 'onboarding: the upload opens Report read');", r"""  ok(/Report read/.test(await page.locator('#sheet').innerText()), 'onboarding: the upload opens Report read');
  await page.evaluate(() => { window.__asks = []; const real = TC.pushAsk; TC.pushAsk = r => { window.__asks.push(r); return real(r); }; });""")
swap("ok(end.tab === 'schedule' && end.sub === 'planner' && !end.onb && !end.key, 'onboarding: after the report, onboarding is over (not remembered as unfinished) and the Planner is open', end);", r"""  ok(end.tab === 'schedule' && end.sub === 'planner' && !end.onb && !end.key, 'onboarding: after the report, onboarding is over (not remembered as unfinished) and the Planner is open', end);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho'), 'onboarding: the report’s classes ask who taught them first');
  await tick(page, 900); const held = await page.evaluate(() => window.__asks.slice());
  await click(page, '#sheet [data-a="pcWhoDone"].btn'); await tick(page, 900);
  const asked = await page.evaluate(() => window.__asks.slice());
  ok(held.length === 0 && asked.join() === 'onboarding', 'onboarding: the notification ask waits for “Who taught these?”, then comes once', { held, asked });""")
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: onboarding ask')

# ---- flowchartMarks (23:30): the same checks on the new rows — .pc-row, "N of M filled", can't-check rows counted on screen
L = open(P, encoding='utf-8').read().split('\n')
swap("  const filled = async page => +((await text(page)).match(/(\\d+) of \\d+\\s*requirements/) || [0, -1])[1];",
     "  const filled = async page => +((await page.evaluate(() => (document.querySelector('.pc-num b') || {}).textContent || '')).match(/^(\\d+) of \\d+$/) || [0, -1])[1];")
swap("  const cell = id => o.page.locator(`.tc-cell:has([data-a=\"plMark\"][data-x=\"${id}\"])`);",
     "  const cell = id => o.page.locator(`.pc-row:has([data-a=\"plMark\"][data-x=\"${id}\"])`);")
swap("  const cantN = async () => +((await o.page.locator('.tc-yearh').allInnerTexts()).join(' ').match(/(\\d+) can’t check/g) || []).reduce((n, x) => n + +x.match(/\\d+/)[0], 0);",
     "  const cantN = async () => await o.page.locator('.pc-row.cant').count();")
open(P, 'w', encoding='utf-8').write('\n'.join(L))
k = [i for i, l in enumerate(L) if "'marks: one tap — ✓, “Marked done by you”, pressed (same label)', c1);" in l]
if len(k) != 1: sys.exit('edit-tests: marks c1 line')
if "marks: a checked-off row is not a class" not in L[k[0] + 1]:
    L[k[0] + 1:k[0] + 1] = ["  ok(await cell(g.ge.id).evaluate(e => !e.querySelector('.pc-add') && e.querySelector('.pc-main').tagName === 'DIV' && !e.querySelector('.pc-main').hasAttribute('data-a')), 'marks: a checked-off row is not a class — no sheet to open, no “+ Professor”');"]
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: flowchart marks')

# ---- pageWidthHome (08:30): Past classes' blocks are 12px from the edge (it read the old .tc-sec cards)
L = open(P, encoding='utf-8').read().split('\n')
swap("    const pa = await edges('pa', \"S.tab='schedule';S.schedTab='past'\", { sec: '.tc-sec' });",
     "    const pa = await edges('pa', \"S.tab='schedule';S.schedTab='past'\", { sec: '.pc-sum, .pc-year, .pc-term, .pc-oth, .pc-btns' });")
swap("    ok(at(pa, 'sec', 12), `page width ${w}: Past classes — the cards are 12px from the edge`, pa);",
     "    ok(at(pa, 'sec', 12) && pa.sec.length >= 4, `page width ${w}: Past classes — the summary, the years, the terms and the buttons are 12px from the edge`, pa);")
open(P, 'w', encoding='utf-8').write('\n'.join(L))
print('edit-tests: page width')

# ---- the harness answers "is null" (a class logged with no term) the way PostgREST does
HP = os.path.join(os.path.dirname(P), 'app-harness.mjs'); h = open(HP, encoding='utf-8').read()
isn = "    else if (v === 'is.null') out = out.filter(r => r[k] == null);\n"
if isn not in h:
    a = "    else if ((m = /^neq\\.(.*)$/.exec(v))) out = out.filter(r => String(r[k]) !== m[1]);\n"
    if h.count(a) != 1: sys.exit('edit-tests: harness anchor')
    h = h.replace(a, a + isn); open(HP, 'w', encoding='utf-8').write(h)
print('edit-tests: harness is.null')
