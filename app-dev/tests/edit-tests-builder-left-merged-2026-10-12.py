#!/usr/bin/env python3
"""Tests for builder-left-merged-2026-10-12.py and done-classes-section-faces-2026-10-12.py.
Run AFTER edit-tests-dpr-report-wins-2026-10-11.py.

What's left (the count, "N left to graduate", the open lines, the in-progress toggle, the catalog line, the pick) moved from
Past classes into the Builder's top card. Tests that read them from Past classes now read that card: rendered where it lives
(the Builder) by builderMerged, and for the older tests read off the same function the Builder draws with (LC below), so
their checks stay what they were.
Usage: python3 edit-tests-builder-left-merged-2026-10-12.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
# the Builder's top card, drawn as the Builder draws it (planRank → plLeftCard; no flowchart: the report alone)
LC = "(() => { const g = plGate(); if (g.html) return null; const L = g.L, X = auditLines(TC.audit, L), R = L ? planRank(L) : X ? { audit: true, X, all: [], bare: true } : null; if (!R || R.done) return null; const o = document.getElementById('__lc'); if (o) o.remove(); const d = document.createElement('div'); d.id = '__lc'; d.style.cssText = 'position:absolute;left:-10000px;top:0;width:390px'; d.innerHTML = plLeftCard(R, L, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A'); document.body.appendChild(d); return d.firstElementChild; })()"
RE = [
  # helpers
  ("const pcRows = page => page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row')].map(r => ({",
   "const pcRows = page => page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row')].filter(r => !r.closest('.pll')).concat(document.querySelector('#scroll .pll') ? [...document.querySelectorAll('#scroll .pll .pc-row')] : [...((" + LC + ") || document.createElement('div')).querySelectorAll('.pc-row')]).map(r => ({"),
  ("still: !!r.closest('.pc-still, .pc-lrows') })));", "still: !!r.closest('.pc-still, .pc-lrows, .pll') })).concat((() => { const o = document.getElementById('__lc'); if (o) o.remove(); return []; })()));"),
  ("ok(heads.join('|') === 'Major and support 11 of 12|Financial Management 4 of 4|General education 19 of 19|Degree requirements 3 of 3', 'quarter catalog: the report’s groups — major and support, the concentration by name, GE, degree requirements', heads);",
   "ok(heads.join('|') === 'Major and support 11 of 12|Financial Management 4 of 4|General education 19 of 19|Degree requirements 2 of 2', 'quarter catalog: the report’s groups — major and support, the concentration by name, GE, degree requirements (the writing requirement and USCP; units and GPA checks aren’t listed)', heads);"),
  ("ok(rows.filter(r => r.st === 'done' && !r.still).length === 38 - 5 && !rows.some(r => r.st === 'need' && !r.still), 'quarter catalog: 33 lines done,",
   "ok(rows.filter(r => r.st === 'done' && !r.still).length === 38 - 5 - 1 && !rows.some(r => r.st === 'need' && !r.still), 'quarter catalog: 32 lines done (33, less the upper-division units check),"),
  ("ok(still.length === 9 && still.some(r => r.st === 'cant'", "ok(still.length === 8 && still.some(r => r.st === 'cant'"),   # the total-units line is the card's "plus N units to go", not a row
  ("await page.evaluate(() => { UI.pcInpOpen = true; UI.pcLeftAll = true; render(true); }); await tick(page, 200);   /* (2026-10-11) in progress opens from under what's left */",
   "await page.evaluate(() => { UI.pcInpOpen = true; UI.pcLeftAll = true; UI.plLeftAll = true; render(true); }); await tick(page, 200);   /* (2026-10-12) in progress opens from under what's left, in the Builder */"),
  ("const pcSum = page => page.evaluate(() => { const c = document.querySelector('.pc-sum'); return c && { num: c.querySelector('.pc-num').innerText.replace(/\\s+/g, ' ').trim(), link: (c.querySelector('.pc-link') || {}).innerText || '', left: ((c.querySelector('.pc-left') || {}).innerText || '').replace(/\\s+/g, ' ').trim(), cat: (c.querySelector('.pc-cat') || {}).innerText || '' }; });",
   "const pcSum = page => page.evaluate(() => { const c = " + LC + "; return c && { num: [...c.querySelector('.pc-num').children].map(e => e.textContent).join(' ').replace(/\\s+/g, ' ').trim(), link: (c.querySelector('.pc-link') || {}).textContent || '', left: ((c.querySelector('.pll-h') || {}).textContent || '').replace(/\\s+/g, ' ').replace(/^(\\d+)(?=[a-z])/, '$1 ').trim(), cat: (c.querySelector('.pc-cat') || {}).textContent || '', past: !!document.querySelector('#scroll .pc-left, #scroll .pc-num, #scroll .pc-go'), _: document.getElementById('__lc')?.remove() }; });"),
  # dprStressQuarter: what's left is the Builder's; Past classes has none of it
  ("sum.left === '1 left to graduate' && /Builder/.test(sum.link) && sum.cat ===", "sum.left === '1 left to graduate' && !sum.link && !sum.past && sum.cat ==="),
  ("  await click(page, '[data-a=\"pcInpOpen\"]'); await tick(page, 200);   /* (2026-10-11) the 4 in progress open from under what's left */",
   "  await page.evaluate(() => { UI.pcInpOpen = true; render(true); }); await tick(page, 200);   /* (2026-10-12) the in-progress lines open from under what's left — in the Builder */"),
  # dprTransferFirst
  ("const sum = await page.evaluate(() => { const c = document.querySelector('.pc-sum'); return c && { num: c.querySelector('.pc-num').innerText.replace(/\\s+/g, ' ').trim(), link: (c.querySelector('.pc-link') || {}).innerText || '', left: ((c.querySelector('.pc-left') || {}).innerText || '').replace(/\\s+/g, ' ').trim(), bar: c.querySelector('.pc-bar').getAttribute('aria-label') }; });",
   "const sum = await page.evaluate(() => { const c = " + LC + "; return c && { num: [...c.querySelector('.pc-num').children].map(e => e.textContent).join(' ').replace(/\\s+/g, ' ').trim(), left: ((c.querySelector('.pll-h') || {}).textContent || '').replace(/\\s+/g, ' ').replace(/^(\\d+)(?=[a-z])/, '$1 ').trim(), bar: c.querySelector('.pc-bar').getAttribute('aria-label'), _: document.getElementById('__lc')?.remove() }; });"),
  ("sum.bar === '18 of 30 filled' && /Builder/.test(sum.link) && sum.left === '11 left to graduate', 'transfer, first term: Past classes says",
   "sum.bar === '18 of 30 filled' && sum.left === '11 left to graduate', 'transfer, first term: the Builder’s top card says"),
  # dprTransferContinuing, pastByReport: the count, from the Builder's card
  ("const num = await page.evaluate(() => (document.querySelector('.pc-sum .pc-num') || {}).innerText);",
   "const num = await page.evaluate(() => [((" + LC + ") || document.createElement('div')).querySelector('.pc-num')?.innerText, document.getElementById('__lc')?.remove()][0]);"),
  # the count, read from the Builder's top card where tests read it off Past classes
  ("const pcSum = page => page.evaluate(", "const withLeft = async page => (await text(page)) + '\\n' + (await page.evaluate(() => { const c = " + LC + "; const t = c ? c.innerText : ''; document.getElementById('__lc')?.remove(); return t; }));\nconst pcSum = page => page.evaluate("),
  ("(await text(page)).match(/(\\d+) of \\d+\\s*filled/)", "(await withLeft(page)).match(/(\\d+) of \\d+\\s*filled/)"),
  ("  await tick(page, 2500); t = await text(page);\n  ok(/\\d+ of \\d+\\s*filled/.test(t) && !/Finance concentration", "  await tick(page, 2500); t = await withLeft(page);\n  ok(/\\d+ of \\d+\\s*filled/.test(t) && !/Finance concentration"),
  ("  let t = await text(page);\n  /* 2026-10-10 (Tate's option A, simple)", "  let t = await withLeft(page);\n  /* 2026-10-10 (Tate's option A, simple)"),
  ("b = document.querySelector('.pc-bar i'), bar = document.querySelector('.pc-bar'); return {", "c = " + LC + ", b = c && c.querySelector('.pc-bar i'), bar = c && c.querySelector('.pc-bar'); setTimeout(() => document.getElementById('__lc')?.remove()); return {"),
  ("ok(/Pick your concentration/.test(t) && /Financial Management/.test(t), 'planner: concentration choices from the catalog');",
   "ok(await page.evaluate(() => TCPL.ledger().concUnchosen && TCPL.concInfo(TCPL.ledger().major).list.some(c => c.name === 'Financial Management')), 'planner: concentration choices from the catalog (the pick is the Builder’s, 2026-10-12)');"),
  ("  t = await text(page);\n  ok(/3 of 33\\s*filled/.test(t), 'planner: the ledger moves", "  t = await withLeft(page);\n  ok(/3 of 33\\s*filled/.test(t), 'planner: the ledger moves"),
  ("const filled = async page => +((await page.evaluate(() => (document.querySelector('.pc-num b') || {}).textContent || '')).match(", "const filled = async page => +((await page.evaluate(() => { const c = " + LC + ", t = ((c && c.querySelector('.pc-num b')) || {}).textContent || ''; document.getElementById('__lc')?.remove(); return t; })).match("),
  ("  ok(/Pick your concentration/.test(await text(page)), 'profile: a desktop memory for another major is ignored');",
   "  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; }); await click(page, '[data-a=\"schedTab\"][data-x=\"planner\"]'); await tick(page, 2500);   /* the pick is the Builder's (2026-10-12) */\n  ok(/Pick your concentration/.test(await text(page)), 'profile: a desktop memory for another major is ignored');"),
]
for a, b in RE:
    n = S.count(a)
    if n == 0 and S.count(b): continue
    if n == 0: sys.exit('re-aim anchor: ' + a[:90])
    S = S.replace(a, b)
open(P, 'w', encoding='utf-8').write(S)

# pastSimple: line-level re-aims (whole lines, by their start)
S = open(P, encoding='utf-8').read()
def line(start, new):
    global S
    L = S.split('\n'); hits = [i for i, l in enumerate(L) if l.startswith(start)]
    if len(hits) != 1:
        if new.split('\n')[0] in S: return
        sys.exit('line anchor: ' + start[:70] + f' ({len(hits)}x)')
    L[hits[0]] = new; S = '\n'.join(L)
line("  ok(/^\\s*Business Administration\\s*\\d+\\s*left on your flowchart",
     "  const lt = (await withLeft(page)).slice(t.length + 1);   /* (2026-10-12) your major and the number open the Builder's top card; Past classes opens on Done */\n"
     "  ok(/^\\s*DONE/.test(t.slice(t.indexOf('Past classes') + 12)) && /^\\s*Business Administration\\s*\\d+\\s*left on your flowchart\\s*\\d+ of \\d+\\s*filled/.test(lt) && !/Degree Progress Report/.test(t) && !/×/.test(t) && !(await page.locator('#scroll [data-a=\"askRemoveHistory\"]').count()), 'past: Past classes opens on Done; your major, then the number, open the Builder’s card; no report row without a report; no × on any row', [t.slice(0, 120), lt.slice(0, 120)]);")
line("  const cc = await page.evaluate(() => { const c = document.querySelector('.pc-sum'); if (!c) return null;",
     "  const cc = await page.evaluate(() => ({ sum: document.querySelectorAll('#scroll .pc-sum, #scroll .pc-conc, #scroll .pc-left, #scroll .pc-go').length }));")
line("  ok(cc && cc.n > 0 && !cc.out.length, 'past: at 320px every concentration name fits inside the summary card', cc);",
     "  ok(cc.sum === 0, 'past: no summary card, count, concentration pick or Builder button on Past classes — they’re the Builder’s (2026-10-12)', cc);")
line("  const link = await r2.page.locator('.pc-link').innerText().catch(() => ''), left = await r2.page.evaluate(",
     "  const pastLeft = await r2.page.locator('#scroll .pc-left, #scroll .pc-link').count();\n"
     "  await r2.page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; }); await click(r2.page, '[data-a=\"schedTab\"][data-x=\"planner\"]'); await tick(r2.page, 2500);\n"
     "  const left = await pllH(r2.page), who = await r2.page.evaluate(() => ((document.querySelector('#scroll .pll .pc-me') || {}).innerText || '').replace(/\\s+/g, ' ').trim());")
line("  ok(/^Best options in the Builder$/.test(link.trim()) && left === '2 left to graduate',",
     "  ok(pastLeft === 0 && left === '2 left to graduate' && /^Business Administration/.test(who), 'past: with a report, “2 left to graduate” and your major sit on top of the Builder, not Past classes (Tate 2026-10-12)', { pastLeft, left, who });")
line("  await click(r2.page, '.pc-link'); await tick(r2.page, 400);", "")
line("  ok(await r2.page.evaluate(() => S.schedTab) === 'planner', 'past: that row opens the Planner');", "")
line("  ok(/Pick your concentration/.test(await text(page)), 'profile: another account’s memory on this device is not used');",
     "  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; }); await click(page, '[data-a=\"schedTab\"][data-x=\"planner\"]'); await tick(page, 2500);   /* the pick is the Builder's (2026-10-12) */\n  ok(/Pick your concentration/.test(await text(page)), 'profile: another account’s memory on this device is not used');")
# Units only now starts folded: the tests that read its rows open it first
S = S.replace("  const units = await page.evaluate(() => { const c = [...document.querySelectorAll('.pc-oth')].find(x => /Units only/.test(x.innerText));",
              "  await page.evaluate(() => { UI.pcAll = true; render(true); }); await tick(page, 200);   /* Units only starts folded (2026-10-12) */\n  const units = await page.evaluate(() => { const c = [...document.querySelectorAll('.pc-oth')].find(x => /Units only/.test(x.innerText));")
if 'tests.builderMerged' not in S:
    a = "\nconst names = Object.keys(tests).filter(n => !only || n === only);"
    if S.count(a) != 1: sys.exit('builderMerged anchor')
    S = S.replace(a, r"""
/* (2026-10-12) Tate: "conjoin these together and place them under Builder. past classes should only show the stuff below";
   Degree requirements' units and GPA lines: "is it even necessary to display these at all"; Units only: "make it compress
   and expandable" and say what BUS 3TR / AP 300 are; a class page: a friend's face on their section, not the professor too. */
tests.builderMerged = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-stress-quarter.pdf'); await saveReport(page);
  await page.evaluate(() => { UI.plPlan = 'A'; S.schedTab = 'planner'; render(true); }); await tick(page, 1500);
  const b = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; const t = e => e ? e.innerText.replace(/\s+/g, ' ').trim() : '';
    return { order: [...c.children].map(e => e.className.split(' ')[0]), who: t(c.querySelector('.pc-me')), cat: t(c.querySelector('.pc-catc')), h: t(c.querySelector('.pll-h')), num: t(c.querySelector('.pc-nrow')), bar: (c.querySelector('.pc-bar') || { getAttribute: () => '' }).getAttribute('aria-label'),
      reqs: [...c.querySelectorAll('.pll-req')].map(q => ({ row: t(q.querySelector('.pc-row .pc-main')), mark: !!q.querySelector('.pc-row [data-a="plMarkAsk"]'), opts: q.querySelectorAll('.pll-opt').length, none: t(q.querySelector('.pll-none')) })),
      ip: t(c.querySelector('.pll-ip [data-a="pcInpOpen"]')), line: t(c.querySelector('.pc-cat')), go: !!c.querySelector('.pc-go'), first: !!(c.compareDocumentPosition(document.querySelector('#scroll .pl-card')) & Node.DOCUMENT_POSITION_FOLLOWING) }; });
  ok(b && /^Business Administration\b/.test(b.who) && b.cat === 'Quarter catalog' && b.h === '1 left to graduate' && b.num === '37 of 38 filled · 4 in progress' && b.bar === '37 of 38 filled' && b.first,
    'builder: one card on top — your major and catalog, “1 left to graduate”, the count and bar — above the plan', b && { who: b.who, cat: b.cat, h: b.h, num: b.num, bar: b.bar, first: b.first });
  ok(b && b.reqs.length === 1 && b.reqs[0].mark && /Approved Elective|Career Readiness/.test(b.reqs[0].row) && b.order.indexOf('pll-req') > b.order.indexOf('pll-h'), 'builder: each requirement left reads as Past classes did — its row with Mark done — with its options or why there are none under it', b && b.reqs);
  ok(b && /^Show the \d+ in progress this term$/.test(b.ip) && b.line === 'Your catalog: Fall Quarter 2023 · report printed Oct 9, 2026' && !b.go, 'builder: the lines in progress open from one row; the catalog line closes the card; no “Best options in the Builder” (you’re in it)', b && { ip: b.ip, line: b.line, go: b.go });
  await click(page, '#scroll .pll [data-a="pcInpOpen"]');
  ok(await page.locator('#scroll .pll .pll-ip .pc-row').count() === 4, 'builder: tapping it shows the 4 lines in progress', await page.locator('#scroll .pll .pll-ip .pc-row').count());
  /* a report that names no concentration: the pick sits in the card, and a long name wraps inside it on a 320px phone */
  await page.setViewportSize({ width: 320, height: 2600 });
  await page.evaluate(() => { TC.audit.conc = null; TC.profile.concentration = null; TCPL.set({ student: { major: TC.profile.major, conc: '', standing: '' } }); render(true); }); await tick(page, 600);
  const cc = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; const r = c.getBoundingClientRect(), pr = parseFloat(getComputedStyle(c).paddingRight), chips = [...c.querySelectorAll('.pc-conc .chip')]; return { n: chips.length, out: chips.filter(e => e.getBoundingClientRect().right > r.right - pr + 0.5 || e.scrollWidth > e.clientWidth + 1).map(e => e.textContent) }; });
  ok(cc && cc.n > 0 && !cc.out.length, 'builder: with no concentration on the report, the pick is in the card — every name fits inside it at 320px', cc);
  await page.setViewportSize({ width: 390, height: 2600 });
  await page.evaluate(() => { TC.audit.conc = 'Financial Management'; render(true); }); await tick(page, 300);
  /* Past classes: only what's below */
  await toPastTab(page);
  const p = await page.evaluate(() => ({ first: (document.querySelector('#scroll .pc-pg > *') || {}).className || '', top: document.querySelectorAll('#scroll .pc-sum, #scroll .pc-left, #scroll .pc-num, #scroll .pc-go, #scroll .pc-cat, #scroll .pc-catc, #scroll .pc-me').length,
    degree: (() => { UI.pcGroups = { degree: true }; render(true); const g = [...document.querySelectorAll('.pc-done .pc-year')].find(e => e.dataset.x === 'degree'); const o = g && g.closest('.pc-open'); return { head: g ? g.innerText.replace(/\s+/g, ' ').trim() : '', rows: o ? [...o.querySelectorAll('.pc-row .pc-main')].map(e => e.innerText.trim()) : [] }; })() }));
  ok(/pc-done/.test(p.first) && p.top === 0, 'past: opens on Done — no count, “left”, catalog or major (the Builder has them)', p);
  ok(/^Degree requirements\s*2 of 2/.test(p.degree.head) && p.degree.rows.length === 2 && !p.degree.rows.some(r => /Units|GPA/.test(r)), 'past: Degree requirements lists the writing requirement and USCP, not the report’s units and GPA checks', p.degree);
  const u0 = await page.evaluate(() => { const c = document.querySelector('.pc-uo'); return c && { head: c.querySelector('.pc-uh').innerText.replace(/\s+/g, ' ').trim(), exp: c.querySelector('.pc-uh').getAttribute('aria-expanded'), rows: c.querySelectorAll('.pc-orow').length }; });
  ok(u0 && /^Units only \d+ on your record, counted for no requirement$/.test(u0.head) && u0.exp === 'false' && u0.rows === 0, 'past: Units only starts folded — its name and how many', u0);
  await click(page, '.pc-uo [data-a="pcUnits"]');
  const u1 = await page.evaluate(() => { const c = document.querySelector('.pc-uo'); return { exp: c.querySelector('.pc-uh').getAttribute('aria-expanded'), rows: [...c.querySelectorAll('.pc-orow')].map(r => r.innerText.replace(/\s+/g, ' ').trim()) }; });
  ok(u1.exp === 'true' && u1.rows.length === +u0.head.match(/\d+/)[0] && u1.rows.some(r => /^TRAN 302 Credit from another school · Fall 2025$/.test(r)), 'past: a tap opens every one; credit from another school with no name says so, and its term', u1);
  await click(page, '.pc-uo [data-a="pcUnits"]');
  ok(await page.locator('.pc-uo .pc-orow').count() === 0, 'past: and folds again');
  ok(log.errors.length === 0, 'builder merged: no page errors', log.errors);
  await close();
  /* a class page: a friend's face on their section only */
  const r = await openApp({});
  await r.page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  const code = await r.page.evaluate(() => Object.keys(COURSES).find(c => secsOf(c).some(s => friendsInSec(s.id).length)));
  await r.page.evaluate(c => A.openClass(c), code); await settle(r.page, 500);
  const f = await r.page.evaluate(() => ({ prof: [...document.querySelectorAll('#scroll .profrow')].map(e => e.querySelectorAll('.av, img').length), secs: document.querySelectorAll('#scroll .secrow .av, #scroll .secrow img, #scroll [data-a="secSheet"] .av, #scroll [data-a="secSheet"] img').length, strip: !!document.querySelector('#scroll .frstrip, #scroll [class*="taking"]') || /taking this/.test(document.getElementById('scroll').innerText) }));
  ok(code && f.prof.length && f.prof.every(n => n <= 1) && f.secs > 0 && f.strip, 'class page: a friend’s face sits on their section, not the professor’s row; “… taking this” stays on top', { code, f });
  ok(r.log.errors.length === 0, 'class page faces: no page errors', r.log.errors);
  await r.close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""")
line("  ok(log.errors.length === 0, 'no flowchart: no page errors', log.errors);",
     "  await click(page, '[data-a=\"schedTab\"][data-x=\"planner\"]'); await tick(page, 1500);   /* (2026-10-12) what's left is the Builder's, even with no flowchart */\n"
     "  const nb = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); return c && { h: c.querySelector('.pll-h').innerText.replace(/\\s+/g, ' ').trim(), num: c.querySelector('.pc-num').innerText.replace(/\\s+/g, ' ').trim(), rows: c.querySelectorAll('.pll-req .pc-row').length, opts: c.querySelectorAll('.pll-opt, .pll-none').length }; });\n"
     "  ok(nb && /^\\d+ left to graduate$/.test(nb.h) && nb.num === '2 of 5 filled' && nb.rows >= 2 && nb.opts === 0, 'no flowchart: the Builder still opens with what’s left from the report (no options to pick from)', nb);\n"
     "  ok(log.errors.length === 0, 'no flowchart: no page errors', log.errors);")
# pastKinds: the who line, count and "left" are the Builder's card; Done stays on Past classes
S = S.replace("  const read = () => page.evaluate(() => { const c = document.querySelector('.pc-sum'); if (!c) return null; const w = c.querySelector('.pc-me'), dn = document.querySelector('.pc-done');",
              "  const read = () => page.evaluate(() => { const c = " + LC + "; if (!c) return null; setTimeout(() => document.getElementById('__lc')?.remove()); const w = c.querySelector('.pc-me'), dn = document.querySelector('#scroll .pc-done');")
S = S.replace("first: c.firstElementChild.className, left: ((c.querySelector('.pc-left') || {}).innerText || '')", "first: c.firstElementChild.className, left: ((c.querySelector('.pll-h') || {}).innerText || '')")
S = S.replace("ok(v && v.heads.join('|') === 'Major and support 1 of 3|Concentration 1 of 1|General education 2 of 2|Degree requirements 1 of 2', 'past (report): Done is the report’s groups, each “N of M” — a line in progress counts, and the total units sit with the degree requirements', v && v.heads);",
              "ok(v && v.heads.join('|') === 'Major and support 1 of 3|Concentration 1 of 1|General education 2 of 2|Degree requirements 1 of 1', 'past (report): Done is the report’s groups, each “N of M” — a line in progress counts; Degree requirements lists the writing requirement, not the total-units check (2026-10-12)', v && v.heads);")
S = S.replace("ok(await page.locator('.pc-sum').count() === 1 && await page.locator('.pc-tv').count() === 0, 'by term: back returns to Past classes');",
              "ok(await page.locator('#scroll .pc-done').count() === 1 && await page.locator('.pc-tv').count() === 0, 'by term: back returns to Past classes');")
S = S.replace("const d = document.querySelector('#scroll .tc-dpr'), s = document.querySelector('.pc-sum'); return !!(d && s &&", "const d = document.querySelector('#scroll .tc-dpr'), s = document.querySelector('#scroll .pc-pg'); return !!(d && s &&")
open(P, 'w', encoding='utf-8').write(S)

M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
IX = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("builder: no who line", "return `<div class=\"card pll\">${pcWho(L, TC.profile)}<div class=\"pll-h\">", "return `<div class=\"card pll\"><div class=\"pll-h\">", "builderMerged"),
  ("builder: no count", "${num}${sub ? `<div class=\"pll-s\">${sub}</div>` : ''}", "${sub ? `<div class=\"pll-s\">${sub}</div>` : ''}", "builderMerged"),
  ("builder: plain requirement rows", "    const head = q.b ? pcReqRow(q.b, X, L, idx.get(q.b)) :", "    const head = false ? pcReqRow(q.b, X, L, idx.get(q.b)) :", "builderMerged"),
  ("builder: no in-progress toggle", "${lf.ip ? `<div class=\"pll-ip\">${lf.ip}</div>` : ''}${cat}${pick}</div>`;", "${cat}${pick}</div>`;", "builderMerged"),
  ("builder: no catalog line", "  const cat = X && TC.audit.catalog ? `<div class=\"pc-cat\">Your catalog:", "  const cat = false ? `<div class=\"pc-cat\">Your catalog:", "builderMerged"),
  ("past: the summary stays", "  return `${pcDone(L, X)}${pcTermsBtn()}`;\n}", "  return `<div class=\"card pc-sum\"><div class=\"pc-num\"><b>${X ? X.filled.length : 0} of ${X ? X.live.length : 0}</b></div></div>${pcDone(L, X)}${pcTermsBtn()}`;\n}", "builderMerged"),
  ("done: units and GPA listed", "pcGroupOf(b) === key && (key !== 'degree' || /^(gwr|uscp)$/.test(b.kind || ''))", "pcGroupOf(b) === key", "builderMerged"),
  ("units only: starts open", "  const uOpen = !!UI.pcAll;", "  const uOpen = !UI.pcAll;", "builderMerged"),
  ("units only: placeholders unnamed", "${pcXfer(h) && !courseName(code) ? xLine(h) : pcLine(", "${false ? xLine(h) : pcLine(", "builderMerged"),
  ("class page: faces on the professor", "</button>`\n      : `<div class=\"profrow\">${avL('?', 44, 15)}", "${avStack(pf, 26)}</button>`\n      : `<div class=\"profrow\">${avL('?', 44, 15)}", "builderMerged"),
  ("class page: no faces on sections", "${sf.length ? `<span class=\"sec-fr\">${avStack(sf, 22)}</span>` : ''}", "", "builderMerged"),
  ("builder: no flowchart, no card", "(X0 ? plLeftCard({ audit: true, X: X0, all: [], bare: true }, null, 'A') : '')", "''", "dprStressNoMajor"),
]
for n, a, b, t in MUT:
    if IX.count(a) != 1: sys.exit(f'mutant anchor {n}: {IX.count(a)}x')
if 'edit-tests-builder-left-merged-2026-10-12.py' not in T:
    k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
    if T.count(k) != 1: sys.exit('mutate anchor')
    T = T.replace(k, "\n  /* what's left, once, in the Builder; Past classes below (2026-10-12; edit-tests-builder-left-merged-2026-10-12.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T)

# older mutants whose code moved (re-aimed at the Builder's card) or went (retired)
OLD = {
  "past: the bar is always full": ["past: the bar is always full", "aria-label=\"${F} of ${N} filled\"><i style=\"width:${pct}%\"></i></div>` : '';", "aria-label=\"${F} of ${N} filled\"><i style=\"width:100%\"></i></div>` : '';", "planner"],
  "past classes: counts the flowchart with a report in": ["past classes: counts the flowchart with a report in", "F = X ? X.filled.length : L.F || 0, N = X ? X.live.length : L.N || 0", "F = L.F || 0, N = L.N || 0", "dprTransferFirst"],
  "truth: no flowchart means no upload card": ["truth: no flowchart means no upload card", "  if (!L) return (plNoRecord() && !TC.audit && !plSkipped() ? dprFirstCard() : '') + (X0 ?", "  if (!L) return (X0 ?", "dprStressNoMajor", None],
  "past left: no way into the Builder": None,
  "past left: no count on top": None,                 # pcLeft's head isn't drawn any more: the Builder card has its own (pll-h)
  "past left: the flowchart's left unsaid": None,
  "truth: a group's rows hidden when open": None,     # pcReportView's old group list has been empty since 22:18 (Done draws the groups)
  "past: a long concentration spills out of the card": ["past: a long concentration spills out of the card", ".pc-conc .chip{max-width:100%;height:auto;min-height:36px;padding:7px 14px;white-space:normal;text-align:left}", ".pc-conc .chip{}", "builderMerged"],
}
Ls = T.split('\n')
for i, l in enumerate(Ls):
    for n, m in OLD.items():
        if l.lstrip().startswith('[' + json.dumps(n, ensure_ascii=False) + ','):
            Ls[i] = '' if m is None else '  ' + json.dumps(m, ensure_ascii=False) + ','
T = '\n'.join(Ls)
for n, m in OLD.items():
    if m and IX.count(m[1]) != 1: sys.exit(f're-aimed mutant anchor {n}: {IX.count(m[1])}x')
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-builder-left-merged: done')
