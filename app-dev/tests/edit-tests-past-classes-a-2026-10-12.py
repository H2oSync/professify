#!/usr/bin/env python3
"""Tests for past-classes-a-2026-10-12.py (Past classes = option A; Every class, by term = option B's timeline). Replayable.
  python3 edit-tests-past-classes-a-2026-10-12.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

BYTERM_OLD_START = "  await click(page, '[data-a=\"pcTerms\"]'); await tick(page, 400);\n  const tv = await page.evaluate(() => ({ h: (document.querySelector('.pc-tvh h2') || {}).textContent, ys:"
BYTERM_OLD_END = "'by term: each class says the number it was taken as, and what your report counted it for — or “Units only”', tv2.rows);\n"
BYTERM_NEW = r"""  /* (2026-10-12, Tate's option B) a timeline, newest first: a dot and a card per term, the term being taken open */
  await click(page, '[data-a="pcTerms"]'); await tick(page, 400);
  const tl = () => page.evaluate(() => ({ h: (document.querySelector('.pc-tvh h2') || {}).textContent,
    terms: [...document.querySelectorAll('.pc-tlh')].map(b => [b.dataset.x, b.getAttribute('aria-expanded'), b.innerText.replace(/\s+/g, ' ').trim()]),
    dots: [...document.querySelectorAll('.pc-tld')].map(d => d.classList.contains('now')),
    sw: document.querySelectorAll('.pc-tsw').length, swAfter: (() => { const s = document.querySelector('.pc-tsw'), p = s && s.previousElementSibling, b = p && p.querySelector('.pc-tlh'); return b ? b.dataset.x : null; })(),
    old: ((document.querySelector('.pc-tlold') || {}).innerText || '').replace(/\s+/g, ' ').trim(),
    rows: [...document.querySelectorAll('.pc-tls .pc-trow')].map(r => (r.querySelector('.pc-glb') ? '🌐 ' : '') + r.innerText.replace(/\s+/g, ' ').trim()),
    x: [...document.querySelectorAll('.pc-tv .pc-ty .pc-tyh')].map(b => b.innerText.replace(/\s+/g, ' ').trim()),
    head: document.querySelectorAll('.pc-tv [data-a="pcGroup"], .pc-tv .chip').length }));
  let t1 = await tl();
  ok(t1.h === 'Every class, by term' && t1.terms.map(x => x[0]).join() === 'Fall 2026,Spring 2026,Fall 2025,Spring 2025,Winter 2025,Fall 2024' && !t1.head,
    'by term: one card per term, newest first — no group chips on top (Tate: “take out this”)', t1);
  ok(t1.terms.filter(x => x[1] === 'true').map(x => x[0]).join() === 'Fall 2026' && /^Fall 2026 In progress \d+ classes$/.test(t1.terms[0][2]) && t1.dots[0] === true && t1.dots.slice(1).every(d => !d),
    'by term: the term being taken is open, says In progress and wears the blue dot; the rest fold to one line', t1.terms);
  ok(/^Spring 2026 quarter · 1 class$/.test(t1.terms[1][2]) && /^Fall 2025 quarter · 1 class · other school$/.test(t1.terms[2][2]), 'by term: a folded term says quarter or semester and how many — and “other school” when it holds credit from one', t1.terms);
  ok(t1.sw === 1 && t1.swAfter === 'Fall 2026' && !t1.old, 'by term: “SWITCHED TO SEMESTERS” once, under the first semester; six terms all show', t1);
  ok(t1.rows.length && t1.rows.every(r => !/In progress/.test(r)) && t1.rows.some(r => /^BUS 3431 Concentration$/.test(r)), 'by term: in the term being taken a class says what it counts for (the pill already says in progress)', t1.rows);
  ok(t1.x.length === 1 && /^Credit from other schools 1 · before Cal Poly$/.test(t1.x[0]), 'by term: credit from before Cal Poly keeps its own card at the end', t1.x);
  await page.evaluate(() => { UI.pcTermOpen = { 'Fall 2026': false, 'Spring 2026': true, 'Fall 2025': true, 'Spring 2025': true, 'Fall 2024': true }; UI.pcTermYr = { x: true }; render(true); }); await tick(page, 200);
  const t2 = await tl();
  ok(t2.rows.some(r => /^ENGL 1134 was ENGL 134 · GE A2$/.test(r)) && t2.rows.some(r => /^🌐 ART 3TC1 GE C1$/.test(r)) && t2.rows.some(r => /^KINE 1109 Extra · counted for nothing$/.test(r)) && t2.rows.some(r => /^BUS 2201 was BUS 201 · Major$/.test(r)),
    'by term: each class reads “CODE  what it counted for” — the number it was taken as, a globe for another school, “Extra · counted for nothing”', t2.rows);
  await click(page, '[data-a="pcTermOpen"][data-x="Spring 2026"]'); await tick(page, 200);
  ok(await page.getAttribute('[data-a="pcTermOpen"][data-x="Spring 2026"]', 'aria-expanded') === 'false', 'by term: a tap folds a term');
  /* past six terms, the oldest fold into one row */
  await page.evaluate(() => { TC.myHistory.push({ code: 'ECON 2010', term: 'Winter', year: 2026, professor: '' }, { code: 'PSY 2010', term: 'Summer', year: 2025, professor: '' }); render(true); }); await tick(page, 200);
  const t3 = await tl();
  ok(t3.terms.length === 5 && t3.old === 'Fall 2024 – Spring 2025 · 3 quarters', 'by term: past six terms the oldest fold into one dashed row naming the span', t3);
  await click(page, '[data-a="pcTermOld"]'); await tick(page, 200);
  ok((await tl()).terms.length === 8, 'by term: a tap shows them all');
"""

edit('check-app.mjs', [
 # pastKinds: Done's heads (a finished group shows a check)
 ("ok(v && v.heads.join('|') === 'Major and support 1 of 3|Concentration 1 of 1|General education 2 of 2|Degree requirements 1 of 1', 'past (report): Done is the report’s groups, each “N of M” — a line in progress counts;",
  "ok(v && v.heads.join('|') === 'Major and support 1 of 3|Concentration ✓ Done|General education ✓ Both|Degree requirements ✓ Done', 'past (report): Done is the report’s groups, each “N of M” — a finished one only a check (option A, 2026-10-12) — a line in progress counts;", 'heads'),
 # dprStressQuarter heads
 ("ok(heads.join('|') === 'Major and support 11 of 13|Financial Management 4 of 4|General education 19 of 19|Degree requirements 2 of 2',",
  "ok(heads.join('|') === 'Major and support 11 of 13|Financial Management ✓ All 4|General education ✓ All 19|Degree requirements ✓ Both',", 'sq heads'),
 # Units only now lives in the slim-rows card (.pc-uo)
 ("  const units = await page.evaluate(() => { const c = [...document.querySelectorAll('.pc-oth')].find(x => /Units only/.test(x.innerText)); return c ? [...c.querySelectorAll('.pc-cc')].map(e => e.innerText) : null; });\n  ok(units && units.includes('BUS 1100')",
  "  const units = await page.evaluate(() => { const c = document.querySelector('.pc-uo'); return c ? [...c.querySelectorAll('.pc-cc')].map(e => e.innerText) : null; });\n  ok(units && units.includes('BUS 1100')", 'sq units'),
 ("  const units = await page.evaluate(() => { const c = [...document.querySelectorAll('.pc-oth')].find(x => /Units only/.test(x.innerText)); return c ? [...c.querySelectorAll('.pc-cc')].map(e => e.innerText) : null; });\n  ok(units && units.join() === 'PSY 2200'",
  "  const units = await page.evaluate(() => { const c = document.querySelector('.pc-uo'); return c ? [...c.querySelectorAll('.pc-cc')].map(e => e.innerText) : null; });\n  ok(units && units.join() === 'PSY 2200'", 'dupes units'),
 # builderMerged: Past classes opens on the answer
 ("  ok(/pc-done/.test(p.first) && p.top === 0, 'past: opens on Done — no count, “left”, catalog or major (the Builder has them)', p);",
  """  ok(/pc-hero/.test(p.first) && p.top === 0, 'past: opens on the answer (Tate’s option A, 2026-10-12) — no Builder card, major or catalog chip', p);
  const hero = await page.evaluate(() => { const h = document.querySelector('#scroll .pc-hero'); return h && { t: h.innerText.replace(/\\s+/g, ' ').trim(), a: h.dataset.a, x: h.dataset.x, next: (h.nextElementSibling || {}).className }; });
  ok(hero && hero.t === '95% 2 left to graduate 37 of 39 filled · Fall Quarter 2023 catalog See them in the Builder ›' && hero.a === 'schedTab' && hero.x === 'planner' && /pc-done/.test(hero.next), 'past: a ring and “2 left to graduate”, the count and your catalog — the card opens the Builder; Done follows', hero);
  const links = await page.evaluate(() => [...document.querySelectorAll('#scroll .pc-links > .pc-lk')].map(b => b.innerText.replace(/\\s+/g, ' ').trim()).concat([...document.querySelectorAll('#scroll .pc-qb .pc-btn')].map(b => b.innerText.trim())));
  ok(/^Every class, by term \\d+ classes · quarters, then semesters$/.test(links[0] || '') && /^Units only \\d+ classes that counted for no requirement$/.test(links[1] || '') && links.slice(2).join('|') === '+ Log a class|Upload a new report', 'past: Every class, by term and Units only are two rows of one card; Log a class and Upload a new report are quiet links', links);""", 'merged first'),
 ("ok(/^Degree requirements\\s*2 of 2/.test(p.degree.head) && p.degree.rows.length === 2", "ok(/^Degree requirements\\s*✓ Both/.test(p.degree.head) && p.degree.rows.length === 2", 'merged degree'),
 ("ok(u0 && /^Units only \\d+ on your record, counted for no requirement$/.test(u0.head) && u0.exp === 'false'", "ok(u0 && /^Units only \\d+ classes? that counted for no requirement$/.test(u0.head) && u0.exp === 'false'", 'merged units'),
 # dprReportWins: by term
 ("""  await page.evaluate(() => { UI.pcTerms = true; UI.pcTermYr = { 2025: true, x: true }; render(true); }); await tick(page, 600);
  const tv = await page.evaluate(() => { const rows = [...document.querySelectorAll('.pc-tv .pc-ty')]; const yr = rows.find(c => /2025–26/.test(c.innerText)), x = rows.find(c => /Credit from other schools/.test(c.innerText)), now = rows.find(c => /· now/.test(c.innerText));
    const r4446 = yr && [...yr.querySelectorAll('.pc-trow')].find(b => /BUS 4446/.test(b.innerText));
    return { y: !!r4446 && /Other school/.test(r4446.innerText), x: x && x.innerText.replace(/\\s+/g, ' '), now: now && [...now.querySelectorAll('.pc-cc')].map(e => e.innerText) }; });
  ok(tv.y && tv.x && /1 · AP, test and transfer credit/.test(tv.x) && /CHEM 1110/.test(tv.x) && !/BUS 4446|BUS 4401/.test(tv.x), 'by term: credit earned after your first term (BUS 4446, Fall 2025) sits in that term, marked Other school; credit with no term sits apart', tv);""",
  """  await page.evaluate(() => { UI.pcTerms = true; UI.pcTermOpen = { 'Fall 2025': true }; UI.pcTermYr = { x: true }; render(true); }); await tick(page, 600);
  const tv = await page.evaluate(() => { const card = k => { const h = document.querySelector(`.pc-tlh[data-x="${k}"]`); return h && h.closest('.pc-tlc'); };
    const yr = card('Fall 2025'), now = card('Fall 2026'), x = [...document.querySelectorAll('.pc-tv .pc-ty')].find(c => /Credit from other schools/.test(c.innerText));
    const r4446 = yr && [...yr.querySelectorAll('.pc-trow')].find(b => /BUS 4446/.test(b.innerText));
    return { y: !!r4446 && !!r4446.querySelector('.pc-glb'), x: x && x.innerText.replace(/\\s+/g, ' '), now: now && [...now.querySelectorAll('.pc-cc')].map(e => e.innerText) }; });
  ok(tv.y && tv.x && /1 · AP, test and transfer credit/.test(tv.x) && /CHEM 1110/.test(tv.x) && !/BUS 4446|BUS 4401/.test(tv.x), 'by term: credit earned after your first term (BUS 4446, Fall 2025) sits in that term with the other-school globe; credit with no term sits apart', tv);""", 'wins byterm'),
])
p = os.path.join(H, 'check-app.mjs'); s = open(p, encoding='utf-8').read()
if BYTERM_NEW not in s:
    i = s.index(BYTERM_OLD_START); j = s.index(BYTERM_OLD_END, i) + len(BYTERM_OLD_END)
    s = s[:i] + BYTERM_NEW + s[j:]
    open(p, 'w', encoding='utf-8').write(s)

edit('mutate.mjs', [
 ('  ["past done: no Done card", "  return rows ? `<div class=\\"card pc-done\\"><div class=\\"pc-dh\\">DONE</div>${rows}</div>` : \'\';", "  return \'\';", "dprStressQuarter", null],',
  '  ["past done: no Done card", "  return rows ? `<div class=\\"card pc-done\\"><div class=\\"pc-dh\\">DONE SO FAR</div>${rows}</div>` : \'\';", "  return \'\';", "dprStressQuarter", null],', 'reaim done'),
 ('  ["by term: no way in", "${pcDone(L, X)}${pcTermsBtn()}", "${pcDone(L, X)}", "pastKinds", null],',
  '  ["by term: no way in", "  const tBtn = pcTermsBtn(true);", "  const tBtn = \'\';", "pastKinds", null],', 'reaim way in'),
])
p = os.path.join(H, 'mutate.mjs'); s = open(p, encoding='utf-8').read()
import re
s2 = re.sub(r'\n  \["past: the summary stays", [^\n]*\n', '\n', s, count=1)   # retired: Past classes shows the answer first now (option A)
if s2 != s: open(p, 'w', encoding='utf-8').write(s2)
# (review) the flowchart-only page keeps its own way into Every class, by term; the answer never says "nothing left"
# while lines are unread
edit('check-app.mjs', [
 ("  ok(v && /^pll-who/.test(v.first)",
  "  ok(await page.locator('#scroll .pc-terms[data-a=\"pcTerms\"]').count() === 1 && !(await page.locator('#scroll .pc-hero').count()), 'past (flowchart only): Done, then Every class, by term as its own card — no answer card without a report');\n  ok(v && /^pll-who/.test(v.first)", 'flow terms'),
 ("  ok(v && v.left === '2 left to graduate' && v.cat ===",
  "  const hz = await page.evaluate(() => [pcHero({ open: [], unknown: [{}], filled: [1, 2], live: [1, 2, 3] }), pcHero({ open: [], unknown: [], filled: [], live: [] })].map(h => { const d = document.createElement('div'); d.innerHTML = h; return d.innerText.replace(/\\s+/g, ' ').trim(); }));\n  ok(/^\\d+%\\s*1 line we couldn’t read\\s*2 of 3 filled/.test(hz[0]) && !/100%/.test(hz[0]) && hz[1] === '', 'past (report): lines the app couldn’t read are never “nothing left” (and no ring at 0 lines)', hz);\n  ok(v && v.left === '2 left to graduate' && v.cat ===", 'hero unknown'),
])
p = os.path.join(H, 'mutate.mjs'); s = open(p, encoding='utf-8').read()
for name in ('by term: year 1 from the latest', 'by term: units only unsaid', 'by term: no Other school chip'):   # retired: the year cards and their chips are gone
    s = re.sub(r'\n  \["' + re.escape(name) + r'", [^\n]*\n', '\n', s, count=1)
open(p, 'w', encoding='utf-8').write(s)
MUT = r'''  ["past A: no answer first", "  if (X && fresh) return `${pcHero(X)}${pcDone(L, X)}`;", "  if (X && fresh) return `${pcDone(L, X)}`;", "builderMerged"],
  ["past A: the answer doesn't open the Builder", "<button class=\"pc-hero\" data-a=\"schedTab\" data-x=\"planner\" aria-label", "<button class=\"pc-hero\" aria-label", "builderMerged"],
  ["past A: a finished group keeps its bar", "${fin ? `<em class=\"pc-dok\">${ok}</em>` : `<span class=\"pc-dbar\"", "${false ? '' : `<span class=\"pc-dbar\"", "dprStressQuarter"],
  ["past A: big buttons back", "<div class=\"pc-btns pc-qb\">", "<div class=\"pc-btns\">", "builderMerged"],
  ["by term B: the term being taken starts folded", " : k === newest;", " : false;", "pastKinds"],
  ["by term B: no semester divider", "if (nx && !qOf(k) && qOf(nx)) html +=", "if (false) html +=", "pastKinds"],
  ["by term B: old terms never fold", "keys.length > SHOW && !oldOpen ?", "false ?", "pastKinds"],
  ["by term B: a class counted for nothing not said", "else if (f && !f.lines.length) parts.push('Extra · counted for nothing');", "", "pastKinds"],
  ["by term B: In progress said in its own term", "if (ip) { if (!here) parts.push('In progress'); }", "if (ip) { parts.push('In progress'); }", "pastKinds"],
  ["by term B: no globe for another school", "${h.oth ? globe : ''}", "", "dprReportWins"],
  ["by term B: the term being taken has no pill", "${isNow ? '<span class=\"pc-tlnow\">In progress</span>' : ''}", "", "pastKinds"],
  ["by term B: a tap doesn't fold a term", "UI.pcTermOpen[k] = !(cur && cur.getAttribute('aria-expanded') === 'true');", "UI.pcTermOpen[k] = !!(cur && cur.getAttribute('aria-expanded') === 'true');", "pastKinds"],
  ["by term: no way in (flowchart only)", "  return `${pcDone(L, X)}${pcTermsBtn()}`;", "  return `${pcDone(L, X)}`;", "pastKinds"],
  ["past A: nothing left said while lines are unread", "u ? `${u} line${u === 1 ? '' : 's'} we couldn’t read` :", "", "pastKinds"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants')])
print('edit-tests-past-classes-a: pastKinds by-term rewritten (+2 checks), 6 tests re-aimed, 14 mutants, 2 re-aimed, 4 retired')
