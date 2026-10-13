#!/usr/bin/env python3
"""(2026-10-13) Builder top card as a three-way ledger (mockup 9) + the Pick 1 chip off the Builder cards.
Re-aims the tests that read .pll-who / .pll-cat / .pc-num / .pc-nrow / .pc-bar, adds the ledger checks and mutants.
Run after edit-tests-builder-foot-2026-10-13.py:  python3 edit-tests-builder-top-ledger-2026-10-13.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
m = root / 'app-dev/tests/mutate.mjs'; ms = m.read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90]); s = s.replace(a, b)

# a shared reader for the ledger card
rep("""const pllH = page => page.evaluate(() => ((document.querySelector('#scroll .pll-h') || {}).innerText || '').replace(/\\s+/g, ' ').trim());""",
    """const pllH = page => page.evaluate(() => ((document.querySelector('#scroll .pll-h') || {}).innerText || '').replace(/\\s+/g, ' ').trim());
/* (2026-10-13) the top card's ledger: filled / in progress / left, the bar's label, the meta line (major · conc, catalog chip, report date, "n requirements") */
const pllLedger = page => page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; const t = e => e ? e.innerText.replace(/\\s+/g, ' ').trim() : '';
  const leg = {}; [...c.querySelectorAll('.pll-leg > span')].forEach(e => { leg[e.className] = +t(e).split(' ')[0]; });
  return { h: t(c.querySelector('.pll-h')), first: (c.firstElementChild || {}).className || '', leg, legText: [...c.querySelectorAll('.pll-leg > span')].map(t),
    bar: (c.querySelector('.pll-bar') || { getAttribute: () => '' }).getAttribute('aria-label'), segs: [...c.querySelectorAll('.pll-bar i')].map(i => i.className),
    meta: [...c.querySelectorAll('.pll-info > span')].map(t), who: t(c.querySelector('.pll-info > span:first-child')), cat: t(c.querySelector('.pll-info .pc-catc')), n: +t(c.querySelector('.pll-n')).split(' ')[0] || 0,
    old: c.querySelectorAll('.pll-who, .pll-cat, .pc-num, .pc-nrow, .pc-bar').length }; });
const ledgerAddsUp = v => !!v && v.n > 0 && (v.leg.f || 0) + (v.leg.p || 0) + (v.leg.l || 0) + (v.leg.u || 0) === v.n && v.leg.l === +v.h.split(' ')[0] && v.bar === v.legText.join(', ') + ` of ${v.n}` && v.old === 0;""")

# past: the major on the Builder (5150)
rep("""  const left = await pllH(r2.page), who = await r2.page.evaluate(() => ((document.querySelector('#scroll .pll .pll-who') || {}).innerText || '').replace(/\\s+/g, ' ').trim());""",
    """  const left = await pllH(r2.page), who = ((await pllLedger(r2.page)) || {}).who || '';""")

# no flowchart (8644)
rep("""  const nb = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); return c && { h: c.querySelector('.pll-h').innerText.replace(/\\s+/g, ' ').trim(), num: c.querySelector('.pc-num').innerText.replace(/\\s+/g, ' ').trim(), rows: document.querySelectorAll('#scroll .plq-card').length, opts: document.querySelectorAll('#scroll .plo').length }; });
  ok(nb && /^\\d+ left to graduate$/.test(nb.h) && nb.num === '2 of 5 filled' && nb.rows >= 2 && nb.opts === 0, 'no flowchart: the Builder still opens with what’s left from the report (no options to pick from)', nb);""",
    """  const nb = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); return c && { h: c.querySelector('.pll-h').innerText.replace(/\\s+/g, ' ').trim(), rows: document.querySelectorAll('#scroll .plq-card').length, opts: document.querySelectorAll('#scroll .plo').length }; });
  const nl = await pllLedger(page);
  ok(nb && /^\\d+ left to graduate$/.test(nb.h) && ledgerAddsUp(nl) && nl.n === 5 && (nl.leg.f || 0) + (nl.leg.p || 0) === 2 && nl.h === `${nl.leg.l} left to graduate` && nb.rows >= 2 && nb.opts === 0, 'no flowchart: the Builder still opens with what’s left from the report — 5 requirements, 2 filled or in progress, the rest left (no options to pick from)', { nb, nl });""")

# past kinds (9471-9483)
rep("""const w = c.querySelector('.pll-who'), cr = c.querySelector('.pll-cat .pc-catc'), dn = document.querySelector('#scroll .pc-done');
    return { who: w ? w.textContent.split(' · ') : null, cat: (cr || {}).textContent || '', num: c.querySelector('.pc-num b').textContent, first: c.firstElementChild.className, left: ((c.querySelector('.pll-h') || {}).innerText || '').replace(/\\s+/g, ' ').trim(),""",
    """const w = c.querySelector('.pll-info > span:first-child'), cr = c.querySelector('.pll-info .pc-catc'), dn = document.querySelector('#scroll .pc-done'), leg = {}; [...c.querySelectorAll('.pll-leg > span')].forEach(e => { leg[e.className] = +e.textContent.trim().split(' ')[0]; });
    return { who: w ? w.textContent.split(' · ') : null, cat: (cr || {}).textContent || '', leg, n: +((c.querySelector('.pll-n') || {}).textContent || '').split(' ')[0] || 0, num: `${leg.f || 0} of ${+((c.querySelector('.pll-n') || {}).textContent || '').split(' ')[0] || 0}`, first: c.firstElementChild.className, left: ((c.querySelector('.pll-h') || {}).innerText || '').replace(/\\s+/g, ' ').trim(),""")
rep("""  ok(v && /^pll-who/.test(v.first) && JSON.stringify(v.who) === '["Business Administration"]' && /^\\d+ left on your flowchart$/.test(v.left), 'past kinds: the card opens with your major (no concentration yet — “Pick your concentration” asks), then what’s left on your flowchart', v);""",
    """  ok(v && /^pll-hd/.test(v.first) && JSON.stringify(v.who) === '["Business Administration"]' && /^\\d+ left on your flowchart$/.test(v.left), 'past kinds: the card opens with what’s left on your flowchart (the ledger), your major on the meta line (no concentration yet — “Pick your concentration” asks)', v);""")
rep("""  ok(v && v.num === `${sumF} of ${sumN}` && v.num === `${L.F} of ${L.N}` && v.left === `${L.need.length + L.needU.length} left on your flowchart`, 'past kinds: the rows add up to the count, and what’s left is the flowchart’s spots to do', [v && v.num, sumF, sumN, v && v.left]);""",
    """  ok(v && v.num === `${sumF} of ${sumN}` && v.num === `${L.F} of ${L.N}` && v.left === `${L.need.length + L.needU.length} left on your flowchart`, 'past kinds: the rows add up to the count, and what’s left is the flowchart’s spots to do', [v && v.num, sumF, sumN, v && v.left]);
  ok(v && (v.leg.f || 0) + (v.leg.p || 0) + (v.leg.l || 0) === L.N && v.leg.p === L.T && v.left === `${v.leg.l} left on your flowchart`, 'past kinds (flowchart): the ledger adds up — filled + in progress (what you’re taking) + left = the flowchart’s spots, and “left” is the heading’s number', [v && v.leg, L.F, L.T, L.N]);""")

# builder merged (9690)
rep("""    return { order: [...c.children].map(e => e.className.split(' ')[0]), who: t(c.querySelector('.pll-who')), cat: t(c.querySelector('.pll-cat')), h: t(c.querySelector('.pll-h')), num: t(c.querySelector('.pc-nrow')), bar: (c.querySelector('.pc-bar') || { getAttribute: () => '' }).getAttribute('aria-label'),""",
    """    return { order: [...c.children].map(e => e.className.split(' ')[0]), meta: [...c.querySelectorAll('.pll-info > span')].map(t), h: t(c.querySelector('.pll-h')), leg: [...c.querySelectorAll('.pll-leg > span')].map(t), bar: (c.querySelector('.pll-bar') || { getAttribute: () => '' }).getAttribute('aria-label'), old: c.querySelectorAll('.pll-who, .pll-cat, .pc-num, .pc-nrow, .pc-bar').length,""")
rep("""  ok(b && b.who === 'Business Administration · Financial Management' && /^Fall Quarter 2023 catalog from your report · Oct 9, 2026$/.test(b.cat) && b.h === '2 left to graduate' && b.num === '37 of 39 filled' && b.bar === '37 of 39 filled' && b.rec,
    'builder: one card on top — major · concentration on one line, the report’s catalog as its own row, “1 left to graduate”, the count and bar — then TermChamp’s plan', b && { who: b.who, cat: b.cat, h: b.h, num: b.num, rec: b.rec });""",
    """  const lg = b ? Object.fromEntries(b.leg.map(x => [x.split(' ').slice(1).join(' '), +x.split(' ')[0]])) : {};
  const nq = b ? +(b.meta[b.meta.length - 1] || '').split(' ')[0] : 0;
  ok(b && b.order.slice(0, 4).join() === 'pll-hd,pll-bar,pll-leg,pll-info' && b.h === '2 left to graduate' && lg.left === 2 && nq >= 38 && (lg.filled || 0) + (lg['in progress'] || 0) === nq - 2 && b.bar === b.leg.join(', ') + ' of ' + nq && b.meta.join('|') === `Business Administration · Financial Management|Fall Quarter 2023 catalog|report · Oct 9, 2026|${nq} requirements` && b.old === 0 && b.rec,
    'builder: one card on top — “2 left to graduate”, the three-way bar and its legend (filled · in progress · left add up to the requirements), then major · concentration, the catalog chip, the report date and “39 requirements” on one meta line (mockup 9, Tate 2026-10-13) — then TermChamp’s plan', b && { order: b.order, h: b.h, leg: b.leg, bar: b.bar, meta: b.meta, rec: b.rec });""")

# builder options (9749-9753)
rep("""    return { who: t(document.querySelector('#scroll .pll-who')), cat: t(document.querySelector('#scroll .pll-cat')), h: t(document.querySelector('#scroll .pll-h')), plan: document.querySelectorAll('#scroll .pl-card, #scroll .plr, #scroll .pla-tab').length,""",
    """    return { who: t(document.querySelector('#scroll .pll-info > span:first-child')), cat: [...document.querySelectorAll('#scroll .pll-info > span')].slice(1, 3).map(t).join(' '), h: t(document.querySelector('#scroll .pll-h')), plan: document.querySelectorAll('#scroll .pl-card, #scroll .plr, #scroll .pla-tab').length,
      tags: [...document.querySelectorAll('#scroll .plq-card .pk-tag')].map(t),""")
rep("""  ok(v.who === 'Business Administration · Financial Management' && v.cat === 'Fall Quarter 2023 catalog from your report · Oct 8, 2026' && v.h === '2 left to graduate' && v.plan === 0, 'options: the top card — major · concentration, the report’s catalog, “2 left to graduate” — and no plan card', v);
  ok(v.cards.length === 2 && v.cards[0].open && !v.cards[1].open && v.cards.map(c => c.label).join('|') === 'Approved Elective Conc.|Business Major Senior Project Pick 1', 'options: one card per requirement, the first open, with its tag', v.cards.map(c => [c.label, c.open]));""",
    """  ok(v.who === 'Business Administration · Financial Management' && v.cat === 'Fall Quarter 2023 catalog report · Oct 8, 2026' && v.h === '2 left to graduate' && v.plan === 0, 'options: the top card — “2 left to graduate”, then major · concentration, the report’s catalog chip and date — and no plan card', v);
  const lv = await pllLedger(page);
  ok(ledgerAddsUp(lv) && lv.leg.l === 2 && lv.segs.join() === ['f', 'p', 'l', 'u'].filter(k => lv.leg[k]).join() && lv.meta[lv.meta.length - 1] === `${lv.n} requirements`, 'options: the ledger — filled, in progress, left add up to the requirements; one bar segment per non-zero part; “n requirements” ends the meta line', lv);
  ok(v.cards.length === 2 && v.cards[0].open && !v.cards[1].open && v.cards.map(c => c.label).join('|') === 'Approved Elective Conc.|Business Major Senior Project' && !v.tags.includes('Pick 1') && /pick one of \\d+/.test(v.cards[1].sub), 'options: one card per requirement, the first open; Conc. keeps its tag, a pick-one line has no “Pick 1” chip — its line already says “pick one of n” (Tate 2026-10-13)', v.cards.map(c => [c.label, c.open, c.sub]));""")

rep("""  ok(v.num === '5 of 8', 'past (report): the count is still the report’s (5 of its 8 lines — GWR and total units included)', v.num);""",
    """  ok(v && v.leg.f === 4 && v.leg.p === 1 && v.leg.l === 2 && v.n === 7 && !('u' in v.leg), 'past (report): the ledger is the report’s — 4 filled · 1 in progress · 2 left of 7 lines (GWR counted; the total-units line is the “units to go” note, not a requirement)', v && [v.leg, v.n]);""")

# the readers that still looked for the old "F of N filled" number — now the legend's filled + in progress, of "n requirements"
NUM = "(c => { const g = {}; [...c.querySelectorAll('.pll-leg > span')].forEach(e => { g[e.className] = +e.textContent.trim().split(' ')[0]; }); const n = +((c.querySelector('.pll-n') || {}).textContent || '').split(' ')[0] || 0; return n ? `${(g.f || 0) + (g.p || 0)} of ${n} filled` : ''; })"
rep("""return c0; })(), b = c && c.querySelector('.pc-bar i'), bar = c && c.querySelector('.pc-bar'); setTimeout(() => document.getElementById('__lc')?.remove()); return { F: L.F, N: L.N, T: L.T, cant: L.grid.flatMap(x => x.slots).filter(s => s.state === 'cant').length, w: b && b.style.width, label: bar && bar.getAttribute('aria-label') }; });""",
    """return c0; })(), bar = c && c.querySelector('.pll-bar'), b = bar && bar.querySelector('i.f'); setTimeout(() => document.getElementById('__lc')?.remove()); return { F: L.F, N: L.N, T: L.T, cant: L.grid.flatMap(x => x.slots).filter(s => s.state === 'cant').length, w: b && b.style.width, label: bar && bar.getAttribute('aria-label') }; });""")
rep("""  ok(/2 of 33\\s*filled/.test(t) && lg.F === 2 && lg.N === 33 && lg.T === 4 && lg.w === '6%' && lg.label === '2 of 33 filled', 'planner: the desktop’s ledger — 2 of 33 filled (31 + the 2 choice slots, checked since 2026-10-02), 4 in progress (one via the ENGL 1134 waiver); the bar is 2/33', lg);""",
    """  ok(/2 filled\\s*4 in progress\\s*27 left/.test(t) && lg.F === 2 && lg.N === 33 && lg.T === 4 && lg.w === '6.1%' && lg.label === '2 filled, 4 in progress, 27 left of 33', 'planner: the desktop’s ledger — 2 filled (31 + the 2 choice slots, checked since 2026-10-02), 4 in progress (one via the ENGL 1134 waiver), 27 left of 33; the bar’s filled part is 2/33', lg);""")
rep("""return c0; })(), t = ((c && c.querySelector('.pc-num b')) || {}).textContent || ''; document.getElementById('__lc')?.remove(); return t; })).match(/^(\\d+) of \\d+$/) || [0, -1])[1];""",
    """return c0; })(), t = c ? """ + NUM + """(c) : ''; document.getElementById('__lc')?.remove(); return t; })).match(/^(\\d+) of \\d+ filled$/) || [0, -1])[1];""")
rep("""return c0; })(); return c && { num: [...c.querySelector('.pc-num').children].map(e => e.textContent).join(' ').replace(/\\s+/g, ' ').trim(), left: ((c.querySelector('.pll-h') || {}).textContent || '').replace(/\\s+/g, ' ').replace(/^(\\d+)(?=[a-z])/, '$1 ').trim(), bar: c.querySelector('.pc-bar').getAttribute('aria-label'), _: document.getElementById('__lc')?.remove() }; });
  ok(sum && sum.num === '18 of 30 filled' && sum.bar === '18 of 30 filled' && sum.left === '11 left to graduate', 'transfer, first term: the Builder’s top card says the report’s “18 of 30 filled” (the flowchart can’t see transfer credit)', sum);""",
    """return c0; })(); return c && { num: """ + NUM + """(c), left: ((c.querySelector('.pll-h') || {}).textContent || '').replace(/\\s+/g, ' ').replace(/^(\\d+)(?=[a-z])/, '$1 ').trim(), bar: c.querySelector('.pll-bar').getAttribute('aria-label'), _: document.getElementById('__lc')?.remove() }; });
  ok(sum && sum.num === '18 of 29 filled' && /, 11 left of 29$/.test(sum.bar) && sum.left === '11 left to graduate', 'transfer, first term: the Builder’s top card says the report’s 18 filled or in progress, 11 left of 29 (the flowchart can’t see transfer credit; the total-units line isn’t a requirement)', sum);""")
rep("""return c0; })()) || document.createElement('div')).querySelector('.pc-num')?.innerText, document.getElementById('__lc')?.remove()][0]);
  ok(/^18 of 23\\s*filled$/.test(String(num).trim()), 'transfer, a year on: “18 of 23 filled” — the report’s 17, and BUS 4401 now that it’s in his classes this term', num);""",
    """return c0; })()) || document.createElement('div'))?.classList?.contains('pll') ? """ + NUM + """(document.getElementById('__lc').firstElementChild) : '', document.getElementById('__lc')?.remove()][0]);
  ok(/^18 of 2[23] filled$/.test(String(num).trim()), 'transfer, a year on: 18 filled or in progress — the report’s 17, and BUS 4401 now that it’s in his classes this term', num);""")
rep("""return c0; })()) || document.createElement('div')).querySelector('.pc-num')?.innerText, document.getElementById('__lc')?.remove()][0]);
  ok(/^7 of 8\\s*filled$/.test(String(num).trim()), 'by report: the count is the report’s — 5 Satisfied + 1 In Progress + 1 you marked done, of 8', num);""",
    """return c0; })()) || document.createElement('div'))?.classList?.contains('pll') ? """ + NUM + """(document.getElementById('__lc').firstElementChild) : '', document.getElementById('__lc')?.remove()][0]);
  ok(/^7 of [78] filled$/.test(String(num).trim()), 'by report: the count is the report’s — 5 Satisfied + 1 In Progress + 1 you marked done', num);""")
rep("""return c0; })(); return c && { num: [...c.querySelector('.pc-num').children].map(e => e.textContent).join(' ').replace(/\\s+/g, ' ').trim(), link: (c.querySelector('.pc-link') || {}).textContent || '', left: ((c.querySelector('.pll-h') || {}).textContent || '').replace(/\\s+/g, ' ').replace(/^(\\d+)(?=[a-z])/, '$1 ').trim(), cat: [...((c.querySelector('.pll-cat') || {}).children || [])].map(e => e.textContent).join(' '),""",
    """return c0; })(); return c && { num: """ + NUM + """(c), link: (c.querySelector('.pc-link') || {}).textContent || '', left: ((c.querySelector('.pll-h') || {}).textContent || '').replace(/\\s+/g, ' ').replace(/^(\\d+)(?=[a-z])/, '$1 ').trim(), cat: [...c.querySelectorAll('.pll-info > span')].slice(1, 3).map(e => e.textContent).join(' '),""")
rep("""/^\\s*Business Administration\\s*\\d+\\s*left on your flowchart\\s*\\d+ of \\d+\\s*filled/.test(lt)""",
    """/^\\s*\\d+\\s*left on your flowchart\\s*\\d+ filled[\\s\\S]*\\d+ left\\s*Business Administration\\s*\\d+ requirements/.test(lt)""")

rep("""  ok(!/requirements filled|We can’t check/.test(t) && !/in progress/.test(t.replace(/\\+ \\d+ in progress|· \\d+ in progress/g, '')),""",
    """  ok(!/requirements filled|We can’t check/.test(t) && !/in progress/.test(t.replace(/\\+ \\d+ in progress|· \\d+ in progress|\\b\\d+ in progress\\b/g, '')),""")  # (2026-10-13) the Builder card's legend says "n in progress" too

rep("""  ok(sum && sum.num === '37 of 39 filled' && sum.left === '2 left to graduate' && !sum.link && !sum.past && sum.cat === 'Fall Quarter 2023 catalog from your report · Oct 9, 2026', 'quarter catalog: Past classes counts the report (36, plus the Approved Elective in progress now that BUS 4442 is in My Classes) and names its catalog and date', sum);""",
    """  ok(sum && sum.num === '36 of 38 filled' && sum.left === '2 left to graduate' && !sum.link && !sum.past && sum.cat === 'Fall Quarter 2023 catalog report · Oct 9, 2026', 'quarter catalog: the Builder’s card counts the report (35, plus the Approved Elective in progress now that BUS 4442 is in My Classes, of 38 — the total-units line isn’t a requirement) and names its catalog and date', sum);""")
rep("""  ok(sum2 && sum2.num === '37 of 39 filled' && sum2.left === '2 left to graduate' &&""", """  ok(sum2 && sum2.num === '36 of 38 filled' && sum2.left === '2 left to graduate' &&""")
rep("""  ok(/3 of 33\\s*filled/.test(t), 'planner: the ledger moves when a class is logged', (t.match(/\\d+ of 33/) || [''])[0]);""",
    """  ok(/3 filled\\s*4 in progress\\s*26 left/.test(t), 'planner: the ledger moves when a class is logged (3 filled, 26 left)', (t.match(/\\d+ filled\\s*\\d+ in progress\\s*\\d+ left/) || [''])[0]);""")

# the flowchart readers that pulled "F of N filled" from the card's text now read the legend's "F filled … L left"
rep("""(await withLeft(page)).match(/(\\d+) of \\d+\\s*filled/)[1]""", """(await withLeft(page)).match(/(\\d+) filled\\s*(?:\\d+ in progress\\s*)?\\d+ left/)[1]""", 5)
rep("""  ok(/\\d+ of \\d+\\s*filled/.test(t) && !/Finance concentration""", """  ok(/\\d+ filled\\s*(?:\\d+ in progress\\s*)?\\d+ left/.test(t) && !/Finance concentration""")

p.write_text(s)

# mutants
def mrep(a, b, n=1):
    global ms
    assert ms.count(a) == n, (ms.count(a), a[:90]); ms = ms.replace(a, b)
mrep("""  ["foot: the pill back",""",
     """  ["ledger: filled counts the in-progress lines too", "nF = Math.max(0, N - nP - nL - nU);", "nF = Math.max(0, N - nL - nU);", "pastKinds"],
  ["ledger: the flowchart forgets what you’re taking", "nP = X ? X.inprog.filter(noTot).length : (L.T || 0),", "nP = X ? X.inprog.filter(noTot).length : 0,", "pastKinds"],
  ["ledger: the total-units line counted as a requirement", "N = X ? X.live.filter(noTot).length : (L.N || 0),", "N = X ? X.live.length : (L.N || 0),", "pastKinds"],
  ["ledger: left isn’t what the Builder lists", "nL = reqs.length,", "nL = X ? X.open.length : reqs.length,", "pastKinds"],
  ["ledger: the bar says something else than the legend", "aria-label=\\"${legend.map(x => x[1] + ' ' + x[2]).join(', ')} of ${N}\\"", "aria-label=\\"${nF} of ${N} filled\\"", "builderOptions"],
  ["ledger: the catalog chip dropped", "<span class=\\"pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}\\">${esc(TC.audit.catalog)} catalog</span><span>report", "<span>report", "builderMerged"],
  ["ledger: no “n requirements”", "${N ? `<span class=\\"pll-n\\">${N} requirements</span>` : ''}", "", "builderMerged"],
  ["builder: the Pick 1 chip back", "tag = at && !/>Pick 1</.test(at) ?", "tag = at ?", "builderOptions"],
  ["foot: the pill back",""")
m.write_text(ms)
print('edit-tests-builder-top-ledger: applied')
