#!/usr/bin/env python3
"""Tests for past-left-builder-top-2026-10-11.py. Run AFTER edit-tests-past-kinds-2026-10-11.py.
Usage: python3 edit-tests-past-left-builder-top-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(b) == n and S.count(a) == 0: return   # already applied
    if S.count(a) != n: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)

# helpers: the left rows count as "still needed"; the summary's count of what's left; the Builder's
rep("""still: !!r.closest('.pc-still') })));""", """still: !!r.closest('.pc-still, .pc-lrows') })));
const pllH = page => page.evaluate(() => ((document.querySelector('#scroll .pll-h') || {}).innerText || '').replace(/\\s+/g, ' ').trim());""", 'pcRows')
rep("""link: (c.querySelector('.pc-link') || {}).innerText || '', cat: (c.querySelector(""", """link: (c.querySelector('.pc-link') || {}).innerText || '', left: ((c.querySelector('.pc-left') || {}).innerText || '').replace(/\\s+/g, ' ').trim(), cat: (c.querySelector(""", 'pcSum')

# Past classes: what's left first
rep("""  ok(sum && sum.num === '37 of 38 filled' && /1 left/.test(sum.link) &&""", """  ok(sum && sum.num === '37 of 38 filled' && sum.left === '1 left to graduate' && /Builder/.test(sum.link) &&""", 'quarter sum')
rep("""  let rows = await pcRows(page);
  const still = rows.filter(r => r.still);
  ok(still.length === 5 &&""", """  await click(page, '[data-a="pcInpOpen"]'); await tick(page, 200);   /* (2026-10-11) the 4 in progress open from under what's left */
  let rows = await pcRows(page);
  const still = rows.filter(r => r.still);
  ok(still.length === 5 &&""", 'quarter still')
rep("""heads.join('|') === 'Major and support 11 filled|Financial Management concentration 1 filled|General education 19 filled|Degree requirements 2 filled'""",
    """heads.join('|') === 'Major and support 11 of 12|Financial Management 4 of 4|General education 19 of 19|Degree requirements 3 of 3'""", 'quarter heads')
rep("""rows.filter(r => r.st === 'done').length === 38 - 5 && !rows.some(r => r.st === 'need' && !r.still)""", """rows.filter(r => r.st === 'done' && !r.still).length === 38 - 5 && !rows.some(r => r.st === 'need' && !r.still)""", 'quarter done count')
rep("""  await page.evaluate(() => { S.tab = 'schedule'; S.schedTab = 'past'; save(); render(true); }); await tick(page, 2500); await openGroups(page);
  const sum2 = await pcSum(page), rows2 = await pcRows(page), b2 = rows2.find(r => r.main === 'BUS 2214');
  ok(sum2 && sum2.num === '37 of 38 filled' && b2 && /BUS 214 → BUS 2214 Winter 2025/.test(b2.sub) && rows2.filter(r => r.still).length === 5,""",
    """  await page.evaluate(() => { S.tab = 'schedule'; S.schedTab = 'past'; UI.pcInpOpen = true; save(); render(true); }); await tick(page, 2500); await openGroups(page);
  const sum2 = await pcSum(page), rows2 = await pcRows(page), b2 = rows2.find(r => r.main === 'BUS 2214');
  ok(sum2 && sum2.num === '37 of 38 filled' && sum2.left === '1 left to graduate' && b2 && /BUS 214 → BUS 2214 Winter 2025/.test(b2.sub) && rows2.filter(r => r.still).length === 5,""", 'quarter reload')
rep("""/Degree Progress Report\\s*12 left/.test(sum.link)""", """/Builder/.test(sum.link) && sum.left === '11 left to graduate'""", 'transfer link')
rep("""link: (c.querySelector('.pc-link') || {}).innerText || '', bar: c.querySelector('.pc-bar').getAttribute('aria-label') }; });""",
    """link: (c.querySelector('.pc-link') || {}).innerText || '', left: ((c.querySelector('.pc-left') || {}).innerText || '').replace(/\\s+/g, ' ').trim(), bar: c.querySelector('.pc-bar').getAttribute('aria-label') }; });""", 'transfer sum')
rep("""  ok(/^\\s*Business Administration\\s*\\d+ of \\d+\\s*filled/.test(t.slice(t.indexOf('Past classes') + 12))""",
    """  ok(/^\\s*Business Administration\\s*\\d+\\s*left on your flowchart\\s*\\d+ of \\d+\\s*filled/.test(t.slice(t.indexOf('Past classes') + 12))""", 'past simple top')
rep("""  const link = await r2.page.locator('.pc-link').innerText().catch(() => '');
  ok(/^Degree Progress Report\\s*2 left$/.test(link.trim()), 'past: with a report, one row — “Degree Progress Report · 2 left”, the same count as the Planner', link);""",
    """  const link = await r2.page.locator('.pc-link').innerText().catch(() => ''), left = await r2.page.evaluate(() => ((document.querySelector('.pc-left') || {}).innerText || '').replace(/\\s+/g, ' ').trim());
  ok(/^Best options in the Builder$/.test(link.trim()) && left === '2 left to graduate', 'past: with a report, “2 left to graduate” on top — the same count as the Builder — and one way into the Builder (Tate 2026-10-11)', { link, left });""", 'past simple link')
rep("""!/in progress/.test(t.replace(/\\+ \\d+ in progress/g, ''))""", """!/in progress/.test(t.replace(/\\+ \\d+ in progress|· \\d+ in progress/g, ''))""", 'planner past')
# the mixed report: its in-progress lines open from under what's left
rep("""  ok(still.length === 9 && still.some(r => r.st === 'ca""", """  ok(still.length === 9 && still.some(r => r.st === 'ca""", 'mixed anchor')
open(P, 'w', encoding='utf-8').write(S)
S = open(P, encoding='utf-8').read()
i = S.index("  ok(still.length === 9 && still.some(r => r.st === 'ca")
j = S.rfind('\n', 0, i); k = S.rfind('\n', 0, j)
prev2 = S[k+1:j]
if 'pcInpOpen' not in S[S.rfind('tests.dprStressMixed', 0, i):i]:
    # open the in-progress lines right before the rows are read
    m = S.rfind('await pcRows(page)', 0, i)
    line_start = S.rfind('\n', 0, m) + 1
    S = S[:line_start] + "  await page.evaluate(() => { UI.pcInpOpen = true; UI.pcLeftAll = true; render(true); }); await tick(page, 200);   /* (2026-10-11) in progress opens from under what's left */\n" + S[line_start:]

# the Builder: the term on top; what's left is the card under it
rep("""  ok(/Fall 2026/.test(v.top) && /\\d+ requirements left/.test(v.top) && /16 units · Edit/.test(v.top) && /^Opens Oct 19/.test(v.reg.trim()), 'plan: the top is the term, requirements left and the units pill; registration’s date is its own line', { top: v.top, reg: v.reg });""",
    """  const pll = await pllH(page);
  ok(/Fall 2026/.test(v.top) && !/left|Registration/.test(v.top) && /16 units · Edit/.test(v.top) && /^Opens Oct 19/.test(v.reg.trim()) && /^\\d+ left on your flowchart$/.test(pll), 'plan: the top is the term and the units pill; registration’s date is its own line; what’s left is the card under it (Tate 2026-10-11)', { top: v.top, reg: v.reg, pll });""", 'plan top')
rep("""  ok(v.sech[0] === 'More picks' || /^More picks/.test(v.sech[0]), 'plan: “More picks” under the plan', v.sech);""",
    """  ok(!v.sech.some(s => /More picks/.test(s)) && await page.evaluate(() => { const a = document.querySelector('#scroll .pll'), b = document.querySelector('#scroll .pl-card'); return !!a && !!b && !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING); }), 'plan: no “More picks” — the options sit under what’s left, above the plan (Tate 2026-10-11)', v.sech);""", 'plan more picks')
rep("""v.left === 5 && /^Fall 2026\\s*5 requirements left/.test(v.top)""", """v.left === 5 && /^Fall 2026/.test(v.top) && await pllH(page) === (await page.evaluate(() => { plSync(); return planRank(TCPL.ledger()).X.open.filter(b => !auditIsTotal(b)).length; })) + ' left to graduate'""", 'report left')
rep("""  ok(/2 requirements left/.test(v.top) && v.open.length === 3 && v.open.filter(""", """  ok(await pllH(page) === '2 left to graduate' && v.open.length === 3 && v.open.filter(""", 'mark 1')
rep("""  ok(/1 requirement left/.test(v.top) && v.open.length === 2""", """  ok(await pllH(page) === '1 left to graduate' && v.open.length === 2""", 'mark 2')
rep("""  ok(/2 requirements left/.test(v.top) && v.open.length === 3 && !v.marked.length""", """  ok(await pllH(page) === '2 left to graduate' && v.open.length === 3 && !v.marked.length""", 'mark 3')
rep("""  ok(/0 requirements left/.test(v.top) && !v.done,""", """  ok(await pllH(page) === '' && !v.done,""", 'mark 4')
rep("""t.indexOf('Before') >= 0 && t.indexOf('More picks') > 0 && t.indexOf('Before') < t.indexOf('Plan A') && t.indexOf('Before') < t.indexOf('More picks')""",
    """t.indexOf('Before') >= 0 && t.indexOf('left on your flowchart') > 0 && t.indexOf('Before') < t.indexOf('Plan A') && t.indexOf('Before') < t.indexOf('left on your flowchart')""", 'prereq order')
rep("""/More picks/.test(await text(page)) && await page.locator('#scroll .pl-card').count() === 1, 'prereq: the card closes and the Planner stays');""",
    """/left on your flowchart/.test(await text(page)) && await page.locator('#scroll .pl-card').count() === 1, 'prereq: the card closes and the Builder stays');""", 'prereq stays')
rep("""{ plan: '.pl-card', picks: '.pl-picks', pk: '.pk-card', top: '.pl-top', sech: '.pl-sech' });""", """{ plan: '.pl-card', left: '.pll', top: '.pl-top' });""", 'width edges')
rep("""    ok(at(pl, 'plan', 12) && at(pl, 'picks', 12) && at(pl, 'pk', 12) && pl.top[0][0] === 16 && pl.sech[0][0] === 16, `page width ${w}: Planner — the plan card and the picks are 12px from the edge, the headings 16`, pl);""",
    """    ok(at(pl, 'plan', 12) && at(pl, 'left', 12) && pl.top[0][0] === 16, `page width ${w}: Builder — what’s left and the plan card are 12px from the edge, the heading 16`, pl);""", 'width check')

# the kinds test (2026-10-11): the flowchart's kinds now sit in the Done card; with a report, the Done card is the report's groups
rep("""{ const c = document.querySelector('.pc-sum'); if (!c) return null; const w = c.querySelector('.pc-me');
    return { who: w ? [...w.children].map(x => x.textContent) : null, num: c.querySelector('.pc-num b').textContent, first: c.firstElementChild.className,
      kinds: [...c.querySelectorAll('.pc-k')]""", """{ const c = document.querySelector('.pc-sum'); if (!c) return null; const w = c.querySelector('.pc-me'), dn = document.querySelector('.pc-done');
    return { who: w ? [...(w.querySelector('.pc-mw') || w).children].map(x => x.textContent) : null, cat: ((w && w.querySelector('.pc-catc')) || {}).textContent || '', num: c.querySelector('.pc-num b').textContent, first: c.firstElementChild.className, left: ((c.querySelector('.pc-left') || {}).innerText || '').replace(/\\s+/g, ' ').trim(),
      heads: dn ? [...dn.querySelectorAll('[data-a="pcGroup"]')].map(b => b.innerText.replace(/\\s+/g, ' ').trim()) : [],
      kinds: [...(dn || c).querySelectorAll('.pc-k')]""", 'kinds read')
rep("""  ok(v && v.first === 'pc-me' && JSON.stringify(v.who) === '["Business Administration"]', 'past kinds: the card opens with your major (no concentration yet — “Pick your concentration” asks)', v);""",
    """  ok(v && /^pc-me/.test(v.first) && JSON.stringify(v.who) === '["Business Administration"]' && /^\\d+ left on your flowchart$/.test(v.left), 'past kinds: the card opens with your major (no concentration yet — “Pick your concentration” asks), then what’s left on your flowchart', v);""", 'kinds who')
rep("""'past kinds: Major classes · GE classes · Electives, in that order'""", """'past kinds: under Done — Major classes · GE classes · Electives, in that order'""", 'kinds order label')
rep("""  ok(v && v.num === `${sumF} of ${sumN}` && v.num === `${L.F} of ${L.N}`, 'past kinds: the rows add up to the big number', [v && v.num, sumF, sumN]);""",
    """  ok(v && v.num === `${sumF} of ${sumN}` && v.num === `${L.F} of ${L.N}` && v.left === `${L.need.length + L.needU.length} left on your flowchart`, 'past kinds: the rows add up to the count, and what’s left is the flowchart’s spots to do', [v && v.num, sumF, sumN, v && v.left]);""", 'kinds sum')
i = S.index("  ok(v && v.kinds.map(k => k.k).join('|') === 'major|ge|conc|el', 'past kinds (report)")
j = S.index("  ok(log.errors.length === 0, 'past kinds: no page errors', log.errors);")
S = S[:i] + r"""  ok(v && v.left === '2 left to graduate' && v.cat === 'Semester catalog', 'past (report): “2 left to graduate” on top, and the catalog your report judges you by', v && [v.left, v.cat]);
  ok(v && v.heads.join('|') === 'Major and support 1 of 3|Concentration 1 of 1|General education 2 of 2|Degree requirements 1 of 2', 'past (report): Done is the report’s groups, each “N of M” — a line in progress counts, and the total units sit with the degree requirements', v && v.heads);
  ok(v.num === '5 of 8', 'past (report): the count is still the report’s (5 of its 8 lines — GWR and total units included)', v.num);
  /* every class, by term: Year 1 from the first Cal Poly term, quarters and semesters tagged, what each counted for */
  await page.evaluate(() => { TC.myHistory = [{ code: 'ENGL 1134', term: 'Fall', year: 2024, professor: '' }, { code: 'ECON 2040', term: 'Winter', year: 2025, professor: '' }, { code: 'BUS 2201', term: 'Spring', year: 2026, professor: '' }, { code: 'KINE 1109', term: 'Spring', year: 2025, professor: '' }, { code: 'ART 3TC1', term: 'Fall', year: 2025, professor: TCPL.abroadMark }];
    TC.audit.reqs.push({ label: 'A2: Written Communication Course', kind: 'ge', status: 'satisfied', used: [{ c: 'ENGL 134', n: 'ENGL 1134', t: 'Fall 2024' }] }, { label: 'C1: Arts Course', kind: 'ge', status: 'satisfied', used: [{ c: 'ART 3TC1', t: 'Fall 2025', x: true }] });
    TC.audit.reqs[0].used = [{ c: 'BUS 201', n: 'BUS 2201', t: 'Spring 2026' }]; render(true); });
  await click(page, '[data-a="pcTerms"]'); await tick(page, 400);
  const tv = await page.evaluate(() => ({ h: (document.querySelector('.pc-tvh h2') || {}).textContent, ys: [...document.querySelectorAll('.pc-tyh')].map(b => b.innerText.replace(/\s+/g, ' ').trim()),
    open: [...document.querySelectorAll('.pc-tyh[aria-expanded="true"]')].map(b => b.dataset.x), th: [...document.querySelectorAll('.pc-th')].map(e => e.innerText.replace(/\s+/g, ' ').trim()),
    rows: [...document.querySelectorAll('.pc-trow')].map(r => r.innerText.replace(/\s+/g, ' ').trim()) }));
  ok(tv.h === 'Every class, by term' && /^Year 1 · 2024–25 Quarters · 3 classes$/.test(tv.ys.find(y => /^Year 1 /.test(y)) || '') && tv.ys.some(y => /^Year 3 · 2026–27 · now Semesters/.test(y)) && tv.ys.some(y => /^Year 2 · 2025–26 Quarters · 1 class$/.test(y)) && /^Transfer and AP credit 1 · not tied to a term you took$/.test(tv.ys[tv.ys.length - 1]),
    'by term: Year 1 is your first Cal Poly year (Fall 2024), each year says quarters or semesters, and transfer credit sits apart', tv.ys);
  ok(tv.open.length === 1 && tv.th.every(t => / semester$/.test(t)), 'by term: the latest year starts open, each term tagged semester or quarter', tv);
  await page.evaluate(() => { UI.pcTermYr = { 2024: true, 2025: true, x: true }; render(true); }); await tick(page, 200);
  const tv2 = await page.evaluate(() => ({ th: [...document.querySelectorAll('.pc-th')].map(e => e.innerText.replace(/\s+/g, ' ').trim()), rows: [...document.querySelectorAll('.pc-trow')].map(r => r.innerText.replace(/\s+/g, ' ').trim()) }));
  ok(tv2.th.includes('FALL 2024 quarter') && tv2.th.includes('WINTER 2025 quarter') && tv2.th.includes('SPRING 2025 quarter') && tv2.th.includes('SPRING 2026 quarter') && tv2.th.includes('FALL 2026 semester'), 'by term: quarters before Fall 2026 say so (Spring 2026 too)', tv2.th);
  ok(tv2.rows.some(r => /^ENGL 1134 was ENGL 134 .*GE A2$/.test(r)) && tv2.rows.some(r => /^ART 3TC1 GE C1$/.test(r)) && tv2.rows.some(r => /^KINE 1109 .*Units only$/.test(r)) && tv2.rows.some(r => /^BUS 2201 was BUS 201 .*Major$/.test(r)),
    'by term: each class says the number it was taken as, and what your report counted it for — or “Units only”', tv2.rows);
  await click(page, '.pc-tvh [data-a="pcTerms"]'); await tick(page, 300);
  ok(await page.locator('.pc-sum').count() === 1 && await page.locator('.pc-tv').count() === 0, 'by term: back returns to Past classes');
""" + S[j:]
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", r"""
/* (2026-10-11) Tate: "the classes you have left … should be where Builder takes over and be at the top of builder (2 left to
   graduate) then show the best feasable options that fulfil those classes." */
tests.builderLeft = async () => {
  const { page, close, log } = await openApp({ height: 1600 });
  await toPlanner(page, true);
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.plPlan = 'A'; render(true); }); await tick(page, 400);
  const read = () => page.evaluate(() => {
    const c = document.querySelector('#scroll .pll'); if (!c) return null;
    plSync(); const L = TCPL.ledger(), R = planRank(L);
    return { h: c.querySelector('.pll-h').innerText.replace(/\s+/g, ' ').trim(), n: L.need.length + L.needU.length, first: !!(c.compareDocumentPosition(document.querySelector('#scroll .pl-card')) & Node.DOCUMENT_POSITION_FOLLOWING),
      reqs: [...c.querySelectorAll('.pll-req')].map(q => ({ label: q.querySelector('.pll-rl').innerText, opts: [...q.querySelectorAll('.pll-opt')].map(o => ({ code: o.querySelector('.code').innerText, id: (o.querySelector('.pll-add') || { dataset: {} }).dataset.x, add: (o.querySelector('.pll-add') || {}).innerText || '', meta: (o.querySelector('.pll-meta') || {}).innerText || '', clash: o.classList.contains('clash') })), none: (q.querySelector('.pll-none') || {}).innerText || '' })),
      order: R.all.map(x => x.code), more: !!c.querySelector('.pll-all'), picks: document.querySelectorAll('#scroll .pl-picks').length };
  });
  let v = await read();
  ok(v && v.h === `${v.n} left on your flowchart` && v.first && !v.picks, 'builder: opens with what’s left (the flowchart’s count) above the plan; no “More picks”', v && { h: v.h, n: v.n, first: v.first, picks: v.picks });
  ok(v.reqs.length === 4 && v.more && v.reqs[0].opts.length >= 1 && v.reqs[0].opts.every(o => /^\+ Plan A$/.test(o.add.trim()) && /\d/.test(o.meta)), 'builder: the first 4 requirements (All N for the rest), each with its best options — time, professor, “+ Plan A”', v.reqs.map(q => [q.label, q.opts.map(o => o.code + ' ' + o.add)]));
  const q0 = v.reqs.find(q => q.opts.length >= 1), codes = q0.opts.map(o => o.code);
  ok(JSON.stringify(codes) === JSON.stringify(v.order.filter(c => codes.includes(c))), 'builder: options in the Builder’s own order (your priorities)', { codes, order: v.order.slice(0, 12) });
  ok(await page.evaluate(ids => ids.every(id => { const s = SEC[id]; return s && !planSecsOf('A').some(t => t.code !== s.code && secClash(s, t)) && !TC.commits.some(t => secClash(s, t)); }), v.reqs.flatMap(q => q.opts.filter(o => !o.clash).map(o => o.id))), 'builder: every option offered fits — no clash with Plan A’s classes or your work');
  /* once registration opens, the seat words — never their markup (found with the real Spring 2027 sections) */
  const seatMeta = await page.evaluate(() => { const was = CFG.REGISTRATION_OPENS; CFG.REGISTRATION_OPENS = '2026-01-01'; render(true); const m = [...document.querySelectorAll('#scroll .pll-meta')].map(e => e.textContent); CFG.REGISTRATION_OPENS = was; render(true); return m; });
  ok(seatMeta.length && seatMeta.every(m => !/[<>]/.test(m)) && seatMeta.some(m => /Open|Full|Wait|seat/i.test(m)), 'builder: once registration opens, each option says its seats in words', seatMeta.slice(0, 3));
  /* a Plan A class over an option's only section: the option says so */
  const cl = await page.evaluate(() => {
    plSync(); const R = planRank(TCPL.ledger());
    const c = R.all.find(x => !x.inPlan && secsOf(x.code).length && secsOf(x.code).every(s => s.s != null)); if (!c) return null;
    const ss = secsOf(c.code), other = SECTIONS.find(s => s.code !== c.code && s.s != null && ss.every(t => secClash(s, t)) && !R.all.some(x => x.code === s.code));
    if (!other) return { code: c.code, none: true };
    TC.plans.A = [other.id]; render(true);
    const o = [...document.querySelectorAll('#scroll .pll-opt')].find(e => e.querySelector('.code').innerText === c.code);
    return { code: c.code, other: other.code, clash: !!o && o.classList.contains('clash'), warn: o ? (o.querySelector('.pll-warn') || {}).innerText || '' : null };
  });
  ok(cl && cl.clash && /^Every section clashes with Plan A or your week$/.test(cl.warn), 'builder: an option whose every section clashes with Plan A says so — never offered as if it fits', cl);
  /* + Plan A opens Add to your week on that section */
  await page.evaluate(() => { TC.plans.A = []; render(true); }); await tick(page, 300);
  v = await read();
  const opt = v.reqs.flatMap(q => q.opts).find(o => o.id);
  await click(page, `.pll [data-a="addPlanSheet"][data-x="${opt.id}"]`); await tick(page, 400);
  ok(await page.evaluate(id => UI.sheet && UI.sheet.type === 'addTo' && String(UI.sheet.id) === String(id), opt.id), '“+ Plan A” opens Add to your week on that section', opt);
  await page.evaluate(() => { UI.sheet = null; render(true); }); await tick(page, 200);
  /* all of them */
  await click(page, '.pll [data-a="plLeftAll"]'); await tick(page, 300);
  v = await read();
  ok(v.reqs.length === v.n, 'builder: “All N” lists every requirement left', [v.reqs.length, v.n]);
  /* several options for one requirement: the best (the Builder's own order) first */
  const ord = await page.evaluate(() => {
    plSync(); const L = TCPL.ledger(), R = planRank(L), n0 = L.need[0];
    const cs = R.all.slice(0, 3).map(c => Object.assign({}, c, { n: n0, inPlan: null, planSec: null }));
    const div = document.createElement('div'); div.innerHTML = plLeftCard({ all: cs, audit: false, X: null, left: L.need.length + L.needU.length }, L, 'A');
    const q = [...div.querySelectorAll('.pll-req')].find(e => e.querySelectorAll('.pll-opt').length >= 2);
    return { want: cs.slice(0, 2).map(c => c.code), got: q ? [...q.querySelectorAll('.pll-opt .code')].map(e => e.textContent) : [] };
  });
  ok(ord.got.length === 2 && JSON.stringify(ord.got) === JSON.stringify(ord.want), 'builder: where a requirement has several options, the best (your priorities) comes first', ord);
  ok(log.errors.length === 0, 'builder left: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'builderLeft')
open(P, 'w', encoding='utf-8').write(S)

M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
# retire the kinds mutants whose code the report no longer reaches (pcKinds is the flowchart's now)
for name in ['past kinds: electives under major', 'past kinds: degree lines counted', 'past kinds: in progress ticked', 'past kinds: no rows', 'past kinds: no major line']:
    lines = [l for l in T.split('\n') if l.strip().startswith('[' + json.dumps(name, ensure_ascii=False) + ',')]
    for l in lines: T = T.replace(l + '\n', '')
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("past left: no count on top", "<div class=\"pc-left\"><b>${n}</b><span>left to graduate</span></div>", "<div class=\"pc-left\"><b></b><span>left to graduate</span></div>", "pastSimple", None),
  ("past left: the flowchart's left unsaid", "<div class=\"pc-left\"><b>${n}</b><span>left on your flowchart</span></div>", "<div class=\"pc-left\"><b>${n + 1}</b><span>left on your flowchart</span></div>", "pastKinds", None),
  ("past left: no way into the Builder", "<button class=\"pc-link pc-go\" data-a=\"pcReport\">", "<button class=\"pc-link pc-go\" data-a=\"pcTerms\">", "pastSimple", None),
  ("past left: in progress never opens", "${ipOpen ? ip.map(b => pcReqRow(b, X, L, idx.get(b))).join('') : ''}", "", "dprStressQuarter", None),
  ("past done: no Done card", "  return rows ? `<div class=\"card pc-done\"><div class=\"pc-dh\">DONE</div>${rows}</div>` : '';", "  return '';", "dprStressQuarter", None),
  ("past done: open lines counted done", "const done = all.filter(b => !left.has(b)), f = done.length", "const done = all, f = done.length", "dprStressQuarter", None),
  ("past done: the flowchart kinds gone", "  if (!X) { const k = pcKinds(L, null); return k ?", "  if (!X) { const k = ''; return k ?", "pastKinds", None),
  ("past catalog: no chip", "const cat = TC.audit && TC.audit.catalog ? (/quarter/i.test(TC.audit.catalog) ?", "const cat = false ? (/quarter/i.test(TC.audit.catalog) ?", "pastKinds", None),
  ("by term: no way in", "${pcDone(L, X)}${pcTermsBtn()}", "${pcDone(L, X)}", "pastKinds", None),
  ("by term: year 1 from the latest", "const first = rows.length ? Math.min(...rows.map(ay)) : 0;", "const first = rows.length ? Math.max(...rows.map(ay)) : 0;", "pastKinds", None),
  ("by term: Spring 2026 a semester", "const pcQtr = (t, y) => +y < 2026 || (+y === 2026 && t !== 'Fall');", "const pcQtr = (t, y) => +y < 2026;", "pastKinds", None),
  ("by term: transfer in a term", "const hist = pcHist(), xfer = hist.filter(pcXfer), real = hist.filter(h => !pcXfer(h) && h.term && +h.year);", "const hist = pcHist(), xfer = [], real = hist.filter(h => h.term && +h.year);", "pastKinds", None),
  ("by term: no number as taken", "if (String(e.c || '').replace(/\\s+/g, ' ').trim().toUpperCase() !== k && !was) was = e.c;", "", "pastKinds", None),
  ("by term: units only unsaid", ": f && !f.lines.length ? '<i class=\"u\">Units only</i>' : '');", ": '');", "pastKinds", None),
  ("builder left: no card", "  ${plLeftCard(R, L, k)}\n", "", "plannerPlan", None),
  ("builder left: report lines unread", "  if (R.audit && R.X) return R.X.open.filter(b => !auditIsTotal(b)).map(", "  if (false) return R.X.open.filter(b => !auditIsTotal(b)).map(", "plannerFromReport", None),
  ("builder left: no options", "${cs.map(c => plLeftOpt(c, k, q.label)).join('')}", "", "builderLeft", None),
  ("builder left: a clashing section offered", "  return plDraftSec(c.code, planSecsOf(k).filter(s => s.code !== c.code), null);", "  return c.best;", "builderLeft", None),
  ("builder left: no add button", "`<button class=\"pll-add\" data-a=\"addPlanSheet\" data-x=\"${esc(sec.id)}\" aria-label=\"Add ${esc(c.code)} to Plan ${k}\">+ Plan ${k}</button>`", "''", "builderLeft", None),
  ("builder left: worst first", "reqs.forEach(q => q.cands.sort((a, b) => (fits(b) ? 1 : 0) - (fits(a) ? 1 : 0) || pos(a) - pos(b)));", "reqs.forEach(q => q.cands.sort((a, b) => pos(b) - pos(a)));", "builderLeft", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
# re-aim the older Past classes mutants onto the new code
for old, new in [
  ('  ["past: no report row", "${X ? `<button class=\\"pc-link\\" data-a=\\"pcReport\\">", "${0 ? `<button class=\\"pc-link\\" data-a=\\"pcReport\\">", "pastSimple"],\n', ''),
  ('["past: the bar is always full", "<i style=\\"width:${pct}%\\"></i></div>${pcKinds(L, X)}", "<i style=\\"width:100%\\"></i></div>${pcKinds(L, X)}", "planner"]',
   '["past: the bar is always full", "<i style=\\"width:${pct}%\\"></i></div>${lf.rows}", "<i style=\\"width:100%\\"></i></div>${lf.rows}", "planner"]'),
  ('["truth: Still needed leaves out what\'s in progress", "  const still = X.open.concat(X.unknown, X.inprog.filter(b => !X.open.includes(b)));", "  const still = X.open.concat(X.unknown);", "dprStressQuarter", null]',
   '["truth: Still needed leaves out what\'s in progress", "const ip = X.inprog.filter(b => !X.open.includes(b) && !X.unknown.includes(b)), ipOpen", "const ip = [].filter(b => !X.open.includes(b) && !X.unknown.includes(b)), ipOpen", "dprStressQuarter", null]'),
]:
    if T.count(old) == 1: T = T.replace(old, new)
    elif new and T.count(new) != 1: sys.exit('re-aim failed: ' + old[:50])
if 'edit-tests-past-left-builder-top-2026-10-11.py' not in T:
    k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
    T = T.replace(k, "\n  /* Past classes, what's left first; the Builder opens with it (2026-10-11; edit-tests-past-left-builder-top-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-past-left-builder-top: done')
