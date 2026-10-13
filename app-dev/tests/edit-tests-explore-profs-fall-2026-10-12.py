#!/usr/bin/env python3
"""Tests for explore-profs-fall-2026-10-12.py and schedule-rows-2026-10-12.py. Replayable.
  python3 edit-tests-explore-profs-fall-2026-10-12.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('check-app.mjs', [
 ("  ok(f.ccards === 0 && f.ag.length >= f.want && f.want > 0 && f.ag.every(x => x === 'openClass|now'), 'my classes, Fall 2026: a card per day, each class opening its Fall page', f);",
  "  ok(f.ccards === 0 && f.ag.length >= f.want && f.want > 0 && f.ag.every(x => /^secSheet\\|n:/.test(x)), 'my classes, Fall 2026: a card per day, each class opening its section’s sheet first (Tate, 2026-10-12)', f);", 'mineAgenda'),
("""  ok(flSp === 'Spring 2027', 'switch: Professors with a subject chosen shows only the term too', flSp);""",
 """  ok(flSp === 'Fall 2026', 'switch: Professors with a subject chosen shows only the term too — the one you’re on (one switch for both, 2026-10-12)', flSp);""", 'subj'),
("""  /* Professors: unchanged words, no switch */
  await click(page, '[data-a="exMode"][data-x="profs"]');
  const pr = await page.evaluate(() => ({ btn: !!document.querySelector('.frow .exterm'), t: [...document.querySelectorAll('.frow .muted.b')].map(e => e.textContent).join('|') }));
  ok(!pr.btn && pr.t === 'Spring 2027', 'switch: Professors keeps the plain Spring 2027 words', pr);
  await click(page, '[data-a="exMode"][data-x="classes"]');""",
 """  /* (Tate, 2026-10-12: "make it so professors also show fall professors … and you can toggle between them too") */
  await click(page, '[data-a="exMode"][data-x="profs"]');
  const pr = await page.evaluate(() => { const b = document.querySelector('.frow .exterm'); return { btn: b ? b.textContent : '', aria: b ? b.getAttribute('aria-label') : '', n: document.querySelectorAll('#exlist .pcard').length }; });
  ok(pr.btn === 'Spring 2027' && pr.aria === 'Showing Spring 2027 professors. Switch to Fall 2026' && pr.n > 0, 'profs: Professors has the same switch, on Spring 2027', pr);
  await click(page, '.frow .exterm'); await settle(page, 600);
  const pf = await page.evaluate(() => { const fall = inNow(() => Object.keys(PROFS).filter(passProf)), spring = Object.keys(PROFS).filter(passProf);
    const cards = [...document.querySelectorAll('#exlist .pcard')].map(c => ({ pk: c.dataset.x, codes: [...c.querySelectorAll('.code')].map(e => e.textContent) }));
    return { btn: (document.querySelector('.frow .exterm') || {}).textContent, cards, fall, spring, fallC: Object.fromEntries(fall.map(pk => [pk, inNow(() => profCourses(pk))])), springC: Object.fromEntries(spring.map(pk => [pk, profCourses(pk)])) }; });
  const fallOnly = pf.fall.filter(pk => Object.keys(pf.springC).every(k => k !== pk) || pf.fallC[pk].some(c => !pf.springC[pk].includes(c)));
  ok(pf.btn === 'Fall 2026' && pf.cards.length === pf.fall.length && pf.cards.every(c => pf.fall.includes(c.pk)) && pf.cards.every(c => c.codes.every(x => pf.fallC[c.pk].includes(x))),
    'profs: Fall lists the professors teaching a Fall section, each card with their Fall classes', pf);
  ok(pf.cards.some(c => c.codes.includes('BUS 3438')) && fallOnly.length > 0, 'profs: a Fall-only class’s professor shows with it (BUS 3438 isn’t offered in Spring)', { fallOnly, cards: pf.cards });
  /* a professor only Fall has (read in later, as a class page's read adds rows): on Fall's list, never Spring's */
  await page.evaluate(() => { addNowRows(NOWT, [{ course_code: 'BUS 3438', title: 'Corporate Finance', section: '09', instructor: 'Fallonly, Pat', days: 'TuTh 9:10AM - 10:00AM', status: 'Open', capacity: 30, available: 5, waitlist_total: 0, class_nbr: '79999' }], nowTerm().code); render(true); }); await settle(page, 300);
  const fo = await page.evaluate(() => { const pk = profKeyOf('Fallonly, Pat'); return { pk, fall: [...document.querySelectorAll('#exlist .pcard')].some(c => c.dataset.x === pk), spring: Object.keys(PROFS).filter(passProf).includes(pk) }; });
  ok(fo.pk && fo.fall && !fo.spring, 'profs: a professor teaching only in Fall is on Fall’s list (and never Spring’s)', fo);
  pf.cards = await page.evaluate(() => [...document.querySelectorAll('#exlist .pcard')].map(c => ({ pk: c.dataset.x, codes: [...c.querySelectorAll('.code')].map(e => e.textContent) })));
  const truth = await page.evaluate(() => [...new Set(Object.values(NOWT.sec).map(x => x.prof).filter(Boolean))].sort());
  ok(JSON.stringify(pf.cards.map(c => c.pk).sort()) === JSON.stringify(truth) && pf.cards.every(c => c.codes.length > 0), 'profs: Fall’s cards are exactly the professors on Fall’s sections, each naming a class', { truth, cards: pf.cards.map(c => c.pk) });
  const pk0 = pf.cards.find(c => c.codes.includes('BUS 3438')).pk;
  await page.evaluate(pk => A.openProf(pk), pk0); await settle(page, 500);
  const pp = await page.evaluate(() => [...document.querySelectorAll('.prof-teach')].map(c => ({ h: c.querySelector('div').textContent, codes: [...c.querySelectorAll('.teach')].map(b => b.dataset.x + (b.dataset.y === 'now' ? '·now' : '')) })));
  ok(pp.length === 2 && pp[0].h === 'Teaching Fall 2026' && pp[0].codes.includes('BUS 3438·now') && pp[0].codes.every(c => /·now$/.test(c)) && pp[1].h === 'Teaching Spring 2027' && pp[1].codes.every(c => !/·now$/.test(c)),
    'profs: their page lists what they teach in Fall first (from Fall’s list), each opening Fall’s class page; Spring’s after', pp);
  await click(page, '[data-a="back"]'); await settle(page, 300);
  await click(page, '[data-a="exMode"][data-x="classes"]');
  ok(await page.evaluate(() => (document.querySelector('.frow .exterm') || {}).textContent) === 'Fall 2026', 'profs: one switch — Classes is on Fall too');
  await click(page, '.frow .exterm'); await settle(page, 300);
  await page.evaluate(pk => A.openProf(pk), pk0); await settle(page, 400);
  const pp2 = await page.evaluate(() => [...document.querySelectorAll('.prof-teach')].map(c => c.querySelector('div').textContent));
  ok(pp2.join('|') === 'Teaching Spring 2027|Teaching Fall 2026', 'profs: on Spring, a professor’s page lists Spring first', pp2);
  await click(page, '[data-a="back"]'); await settle(page, 300);""", 'profs'),
("""    const card = await pg2.locator('.arow[data-a="openClass"][data-y="now"]').count();
    if (card) await click(pg2, '.arow[data-a="openClass"][data-y="now"]');
    ok(card > 0 && await chip() === 'Fall 2026', 'tap: a class in My Classes › Fall opens its Fall page', { card });""",
 """    /* (Tate, 2026-10-12: "the initial should just show that little pop-up") — the section's sheet first, then View class */
    const card = await pg2.locator('.arow[data-a="secSheet"]').count(), blocks = await pg2.locator('#scroll [data-a="secSheet"].g-blk, #scroll .g-col [data-a="secSheet"]').count();
    if (card) await click(pg2, '.arow[data-a="secSheet"]');
    const sh2 = await pg2.evaluate(() => ({ t: UI.sheet && UI.sheet.type, term: (document.querySelector('#sheet .secterm') || {}).textContent, open: !!document.querySelector('.arow[data-a="openClass"]') }));
    ok(card > 0 && blocks > 0 && sh2.t === 'sec' && sh2.term === 'Fall 2026' && !sh2.open, 'tap: a class in My Classes › Fall (its row or its block) opens its section’s sheet first, as a friend’s week does', { card, blocks, sh2 });
    await click(pg2, '#sheet [data-a="openClass"][data-y="now"]');
    ok(await chip() === 'Fall 2026', 'tap: …and View class opens its Fall page', await chip());""", 'mine tap'),
])

# the day lists name the professor's rating
TESTS = r'''/* (Tate, 2026-10-12: "this view should show the professors rating. same with the plans view.") */
tests.rowRatings = async () => {
  const { page, close, log } = await openApp({ height: 1600 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => { setTab('schedule'); S.schedTab = 'mine'; UI.agOpen = {}; render(true); }); await tick(page, 400);
  const read = () => page.evaluate(() => { UI.agOpen = UI.agOpen || {}; document.querySelectorAll('.ag-fold .ag-h').forEach(b => { UI.agOpen[b.dataset.x] = true; }); render(true);
    return [...document.querySelectorAll('#scroll .arow')].map(r => { const sec = SEC[r.dataset.y] || personSecs('me').find(x => x.id === r.dataset.y); const line = r.querySelector('.muted.b'); const rt = line && line.querySelector('.rowrt');
      return { prof: sec && sec.prof, want: sec && ratingOf(sec.prof) != null ? 'rated ' + ratingOf(sec.prof).toFixed(1) : null, got: rt ? rt.textContent.trim() : null, ink: !rt || (rt.getAttribute('style') || '').includes(rateTone(ratingOf(sec.prof)).ink), color: rt ? getComputedStyle(rt).color : '', star: !!(rt && rt.querySelector('svg')), text: line ? line.innerText.replace(/\s+/g, ' ').trim() : '' }; }); });
  const mine = await read();
  ok(mine.length > 0 && mine.every(r => r.got === r.want) && mine.some(r => r.got) && mine.filter(r => r.got).every(r => r.star && r.ink), 'ratings: My Classes’ day list names each professor’s rating, with its star, in the rating’s colour (none when PolyRatings has none; “rated” is read aloud)', mine);
  const one = mine.find(r => r.got);
  ok(one && one.text.includes(' ' + one.got + ' · ') && one.text.indexOf(one.got) > 3, 'ratings: name, rating, then the seats — “Name ★ 3.2 · Full”', one);
  await page.evaluate(() => { TC.plans.A = SECTIONS.filter(s => s.s != null && s.prof && ratingOf(s.prof) != null).slice(0, 3).map(s => s.id); S.schedTab = 'plans'; S.plan = 'A'; render(true); }); await tick(page, 300);
  const plans = await read();
  ok(plans.length > 0 && plans.every(r => r.got === r.want) && plans.some(r => r.got), 'ratings: Plans’ day list too', plans);
  ok(log.errors.length === 0, 'ratings: no page errors', log.errors);
  await close();
};

'''
edit('check-app.mjs', [("tests.dprStressQuarter = async () => {", TESTS + "tests.dprStressQuarter = async () => {", 'tests')])

edit('mutate.mjs', [
 ('''  ["term switch: a failed Fall load spins forever", "if (!nowAllReady()) { if (NOWT.err && !NOWT.loading && NOWT.term === nowTerm().code) return errCard(`Couldn’t load ${L} classes.`, 'retryNowAll'); loadNowAll();",''',
  '''  ["term switch: a failed Fall load spins forever", "if (!nowAllReady()) { if (NOWT.err && !NOWT.loading && NOWT.term === nowTerm().code) return errCard(`Couldn’t load ${L} ${what}.`, 'retryNowAll'); loadNowAll();",''', 'reaim spins'),
 ('''  ["term switch: plain words, not a button", "<button class=\\"exterm muted b\\" data-a=\\"exTerm\\" aria-label=\\"${esc('Showing ' + L + ' classes. Switch to ' + other)}\\">${esc(L)}${ic('updown', 14, 2.6)}</button>",''',
  '''  ["term switch: plain words, not a button", "<button class=\\"exterm muted b\\" data-a=\\"exTerm\\" aria-label=\\"${esc('Showing ' + L + (S.exMode === 'profs' ? ' professors' : ' classes') + '. Switch to ' + other)}\\">${esc(L)}${ic('updown', 14, 2.6)}</button>",''', 'reaim plain'),
 ('''  ["term switch: starts on Fall", "const exNow = () => S.exMode === 'classes' && UI.exTerm === 'now' && splitTerms();", "const exNow = () => S.exMode === 'classes' && UI.exTerm !== 'spring' && splitTerms();",''',
  '''  ["term switch: starts on Fall", "const exNow = () => UI.exTerm === 'now' && splitTerms();", "const exNow = () => UI.exTerm !== 'spring' && splitTerms();",''', 'reaim starts'),
 ('''  ["term switch: shown with one term", "if (!(S.exMode === 'classes' && splitTerms())) return `<span", "if (!(S.exMode === 'classes')) return `<span", "exploreTerm"],''',
  '''  ["term switch: shown with one term", "  if (!splitTerms()) return `<span class=\\"muted b\\"", "  if (false) return `<span class=\\"muted b\\"", "exploreTerm"],''', 'reaim one term'),
])
MUT = r'''  ["profs: no switch in Professors", "  if (!splitTerms()) return `<span class=\"muted b\" style=\"font-size:13px\">${esc(CFG.TERM_LABEL)}</span>`;", "  if (!splitTerms() || S.exMode === 'profs') return `<span class=\"muted b\" style=\"font-size:13px\">${esc(CFG.TERM_LABEL)}</span>`;", "exploreTerm"],
  ["profs: Fall lists Spring's professors", "  if (!(LENS_NOW ? profCourses(pk).length : p.teaches)) return false;", "  if (!p.teaches) return false;", "exploreTerm"],
  ["profs: Fall cards name Spring's classes", "  if (LENS_NOW) {\n    if (PROF_NOW.src !== SEC", "  if (false) {\n    if (PROF_NOW.src !== SEC", "exploreTerm"],
  ["profs: the Fall map never refreshed", "PROF_NOW.gen !== NOW_GEN", "false", "exploreTerm"],
  ["profs: a switch per mode", "const exNow = () => UI.exTerm === 'now' && splitTerms();", "const exNow = () => S.exMode === 'classes' && UI.exTerm === 'now' && splitTerms();", "exploreTerm"],
  ["profs: the page has no Fall classes", "fa = splitTerms() && nowAllReady() ?", "fa = false ?", "exploreTerm"],
  ["profs: the page's Fall classes open Spring's page", "data-x=\"${c}\"${now ? ' data-y=\"now\"' : ''}>", "data-x=\"${c}\">", "exploreTerm"],
  ["profs: Spring first even from Fall's list", "return exNow() ? fa + sp : sp + fa;", "return sp + fa;", "exploreTerm"],
  ["mine: Fall rows open the class page", "  const act = s => o.other && !o.now ? `data-a=\"openClass\" data-x=\"${esc(s.code)}\"` : `data-a=\"secSheet\"", "  const act = s => o.other || o.now ? `data-a=\"openClass\" data-x=\"${esc(s.code)}\"` : `data-a=\"secSheet\"", "exploreTerm"],
  ["mine: Fall blocks open the class page", "blockAct: isNowT ? 'secSheet' : 'openClass'", "blockAct: 'openClass'", "exploreTerm"],
  ["ratings: none in My Classes", "<span class=\"muted b\" style=\"display:block;font-size:14px\">${rowProf(s.prof)}${seat(s)}${wl(s)}</span>", "<span class=\"muted b\" style=\"display:block;font-size:14px\">${esc(profName(s.prof))}${seat(s)}${wl(s)}</span>", "rowRatings"],
  ["ratings: none in Plans", "<span class=\"muted b\" style=\"display:block;font-size:14px\">${rowProf(s.prof)} · ${secSeatText(s)}</span>", "<span class=\"muted b\" style=\"display:block;font-size:14px\">${esc(profName(s.prof))} · ${secSeatText(s)}</span>", "rowRatings"],
  ["ratings: no star", "${starI(12, rateTone(r).star)}<span class=\"pc-sr\">rated </span>", "<span class=\"pc-sr\">rated </span>", "rowRatings"],
  ["ratings: not in the rating's colour", "<span class=\"rowrt rt-${rateTone(r).k}\" style=\"color:${rateTone(r).ink}\">", "<span class=\"rowrt rt-${rateTone(r).k}\">", "rowRatings"],
  ["profs: Fall-first always", "return exNow() ? fa + sp : sp + fa;", "return fa + sp;", "exploreTerm"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants')])
p = os.path.join(H, 'mutate.mjs'); s = open(p, encoding='utf-8').read()
import re
for name in ('term switch: shown on Professors', "mine agenda: Fall rows open the pick term's page"):   # retired: Professors has the switch now; Fall rows open the sheet
    s = re.sub(r'\n  \["' + re.escape(name) + r'", [^\n]*\n', '\n', s, count=1)
open(p, 'w', encoding='utf-8').write(s)
print('edit-tests-explore-profs-fall: exploreTerm re-aimed (+6 checks), rowRatings, 12 mutants, 2 re-aimed')
