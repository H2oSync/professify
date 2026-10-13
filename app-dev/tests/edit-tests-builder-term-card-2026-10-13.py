#!/usr/bin/env python3
"""(2026-10-13) tests for: the Builder's one term card + sheet (option B), Rate's professor cards, option tiles, and a
Schedule sub-tab opening at its top. Run after edit-tests-builder-req-sub-2026-10-13.py:
  python3 edit-tests-builder-term-card-2026-10-13.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'app-dev/tests/check-app.mjs'; s = p.read_text()
m = root / 'app-dev/tests/mutate.mjs'; ms = m.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90]); s = s.replace(a, b)
def mrep(a, b, n=1):
    global ms
    assert ms.count(a) == n, (ms.count(a), a[:90]); ms = ms.replace(a, b)

# the registration line is the card's headline and its sub line without the units ("in 10 days · 16 units")
rep("""  const l = document.querySelector('#scroll .pla-reg'), f = document.querySelector('#scroll .reg-fr');
  return { line: l ? l.innerText.replace(/\\s+/g, ' ').trim() : null,""",
"""  const l = document.querySelector('#scroll .pla-reg'), f = document.querySelector('#scroll .reg-fr');
  const hd = l && l.querySelector('.pl-tc-h'), sb = l && l.querySelector('.pl-tc-s'), ad = l && l.querySelector('.pla-add');
  const sub = sb ? sb.textContent.split(' · ').filter(x => !/^\\d+ units$/.test(x)).join(' · ') : '';
  return { line: l ? [hd ? hd.textContent : '', sub].filter(Boolean).join(' · ') + (ad ? ' ' + ad.textContent.trim() : '') : null, units: sb ? +((sb.textContent.match(/(\\d+) units/) || [])[1] || 0) : null,""")
s = s.replace("v.line === 'You register ", "v.line === 'Register ")
rep("&& !v.mine && v.act === 'regDayOpen', 'regday: no day yet — the amber line,", "&& !v.mine && v.act === 'plTermOpen' && v.units > 0, 'regday: no day yet — the amber line (with your units under it),")
rep("ok(v.aria === 'Opens Oct 19 · in 6 days · Add your day. Registration opens Oct 19', 'regday: … its spoken name starts with what it shows (voice control), then says what opens', v.aria);",
    "ok(/^Opens Oct 19 · in 6 days\\. Add your day\\. \\d+ units\\. Edit your registration day, units and what matters most$/.test(v.aria), 'regday: … its spoken name starts with what it shows (voice control), then says what it edits', v.aria);")
rep("&& v.mine && v.act === 'regDayOpen', 'regday: design B —", "&& v.mine && v.act === 'plTermOpen', 'regday: design B —")
# the regDay sheet itself is now opened from Registration days (its own button); the Builder's card opens the term sheet
rep("  await click(page, '#scroll .pla-reg'); await tick(page, 300);\n  const sheet = ", "  await page.evaluate(() => A.regDayOpen()); await tick(page, 300);\n  const sheet = ")
rep("  await click(page, '#scroll .pla-reg'); sh = await sheet();", "  await page.evaluate(() => A.regDayOpen()); await tick(page, 300); sh = await sheet();")
rep("  await click(page, '#scroll .pla-reg'); await click(page, '#sheet [data-a=\"regDayRemove\"]');", "  await page.evaluate(() => A.regDayOpen()); await tick(page, 300); await click(page, '#sheet [data-a=\"regDayRemove\"]');")

# card A
rep(r"ok(/^Opens Oct 19 · in 10 days\s*Add your day$/.test(a.reg.trim())", r"ok(/^Opens Oct 19 · in 10 days\s*12 units\s*Add your day$/.test(a.reg.trim())")
rep(r"ok(/· in 1 day\s*Add your day$/.test(one.trim())", r"ok(/· in 1 day\s*\d+ units\s*Add your day$/.test(one.trim())")

# prefs: the units live in the term card now
rep("pill: (sc.querySelector('.pl-pill') || {}).innerText,", "pill: (sc.querySelector('.pl-tc .pl-tc-h') || {}).innerText,")
rep("after.pill === '18 units · Edit'", "after.pill === '18 units'")
rep("'prefs: the Builder shows the units (no 1 · 2 · 3 chips — the order lives in the sheet Edit opens, Tate 2026-10-12)", "'prefs: the Builder’s term card shows the units (no 1 · 2 · 3 chips — the order lives in the sheet the card opens, Tate 2026-10-12/13)")
rep(r"&& /16 units · Edit/.test(v.top) && /^Opens Oct 19/.test(v.reg.trim())", r"&& /^Opens Oct 19[\s\S]*16 units/.test(v.reg.trim())")

# Rate: each professor its own card, 12px from the edge
rep("""const ra = await edges('ra', "S.tab='rate'", { title: '.title', cards: '.card.list' });""", """const ra = await edges('ra', "S.tab='rate'", { title: '.title', cards: '.rate-cards .li' });""")

# new tests
rep("tests.registrationDay = async () => {", r"""tests.builderTermCard = async () => {   /* (2026-10-13, Tate's option B) units + registration day, one card, one sheet */
  const { page, close, log } = await regOpenPlanner({});
  let v = await regLine(page);
  ok(v.act === 'plTermOpen' && v.units > 0 && !document && true || (v.act === 'plTermOpen' && v.units > 0), 'term card: one card with the registration line and your units', v);
  const pill = await page.evaluate(() => document.querySelectorAll('#scroll .pl-pill, #scroll [data-a="plPrefsOpen"]').length);
  ok(pill === 0, 'term card: no separate “N units · Edit” pill', pill);
  await click(page, '#scroll .pl-tc'); await tick(page, 300);
  const sh = () => page.evaluate(() => { const s = document.getElementById('sheet'); return { type: UI.sheet && UI.sheet.type, h: (s.querySelector('h3') || {}).textContent, units: [...s.querySelectorAll('[data-a="plPrefUnits"]')].map(b => b.textContent + (b.getAttribute('aria-pressed') === 'true' ? '*' : '')),
    days: s.querySelectorAll('.rd-d').length, time: !!s.querySelector('#rd-time'), share: !!s.querySelector('[data-a="regShareToggle"]'), rank: s.querySelectorAll('[data-a="plPrefPick"]').length, save: !!s.querySelector('[data-a="plTermSave"]'), err: (s.querySelector('.tc-err') || {}).textContent || '' }; });
  let a = await sh();
  ok(a.type === 'plTerm' && a.h === 'Spring 2027' && a.units.length === 5 && a.units.some(u => u.endsWith('*')) && a.days > 0 && a.time && a.share && a.rank === 3 && a.save, 'term card: its sheet holds units, your registration day (day, time, who can see it) and what matters most, with one Save', a);
  /* a typed time survives other taps */
  await page.fill('#rd-time', '09:15'); await page.evaluate(() => A.plPrefUnits(14)); await tick(page, 100);
  ok(await page.inputValue('#rd-time') === '09:15', 'term sheet: a typed time survives picking units', await page.inputValue('#rd-time'));
  await page.evaluate(() => render(true)); await tick(page, 100);
  ok(await page.inputValue('#rd-time') === '09:15', 'term sheet: … and any other redraw', await page.inputValue('#rd-time'));
  /* a time with no day says so */
  await click(page, '#sheet [data-a="plTermSave"]'); await tick(page, 300); a = await sh();
  ok(a.type === 'plTerm' && /Pick your day too/.test(a.err), 'term sheet: a time with no day asks for the day', a.err);
  const day = await page.evaluate(() => regRoundDays().find(d => d >= sloISO()));
  await page.evaluate(d => A.regPickDay(d), day); await tick(page, 100);
  const before = log.writes.length;
  await click(page, '#sheet [data-a="plTermSave"]'); await tick(page, 1200);
  const w = log.writes.slice(before);
  const pw = w.filter(x => x.table === 'planner_prefs'), rw = w.filter(x => x.table === 'registration_days');
  ok(pw.length === 1 && pw[0].body.units === 14 && rw.length === 1 && rw[0].body.day === day && rw[0].body.at_time === '09:15' && !(await page.evaluate(() => UI.sheet)), 'term sheet: one Save writes the units and your day, then closes', { pw: pw.map(x => x.body), rw: rw.map(x => x.body) });
  v = await regLine(page);
  ok(v.mine && v.units === 14 && /^Register /.test(v.line), 'term card: then reads “Register …” with 14 units, in blue', v);
  /* nothing changed: nothing written */
  await click(page, '#scroll .pl-tc'); await tick(page, 300);
  const b2 = log.writes.length; await click(page, '#sheet [data-a="plTermSave"]'); await tick(page, 800);
  ok(log.writes.length === b2, 'term sheet: Save with nothing changed writes nothing', log.writes.slice(b2).map(x => x.table));
  /* Remove my day keeps the sheet open */
  await click(page, '#scroll .pl-tc'); await tick(page, 300);
  await click(page, '#sheet [data-a="regDayRemove"]'); await tick(page, 600); a = await sh();
  ok(a.type === 'plTerm' && a.save, 'term sheet: Remove my day leaves the sheet open (your other changes stay)', a);
  await page.evaluate(() => { UI.sheet = null; render(true); });
  /* outside registration the card is your units and what matters most, in blue */
  await page.evaluate(() => { CFG.REGISTRATION_TERM = 'Winter 2099'; render(true); }); await tick(page, 200);
  v = await regLine(page);
  ok(v.mine && /^14 units · What matters most: /.test(v.line) && v.fr === null, 'term card: with no registration ahead, “14 units” and what matters most, blue, no friends line', v);
  ok(log.errors.length === 0, 'term card: no page errors', log.errors);
  await close();
};
tests.schedTabTop = async () => {   /* (2026-10-13, Tate's screen recording) a Schedule sub-tab opens at its top */
  const { page, close, log } = await openApp({ height: 700 });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 1200);
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 400; }); await tick(page, 200);
  const y0 = await page.evaluate(() => document.getElementById('scroll').scrollTop);
  await page.evaluate(() => A.tab('home')); await tick(page, 300);
  await page.evaluate(() => A.tab('schedule')); await tick(page, 300);
  const back = await page.evaluate(() => document.getElementById('scroll').scrollTop);
  await page.evaluate(() => A.schedTab('plans')); await tick(page, 300);
  const y1 = await page.evaluate(() => document.getElementById('scroll').scrollTop);
  ok(y0 > 100 && y1 === 0, 'tabs: Past classes scrolled down, Home, back to Schedule, then Plans — Plans opens at its top', { y0, back, y1 });
  await page.evaluate(() => { document.getElementById('scroll').scrollTop = 300; }); await tick(page, 100);
  await page.evaluate(() => A.schedTab('mine')); await tick(page, 300);
  ok(await page.evaluate(() => document.getElementById('scroll').scrollTop) === 0, 'tabs: and Plans → My Classes too');
  ok(log.errors.length === 0, 'tabs: no page errors', log.errors);
  await close();
};
tests.registrationDay = async () => {""")
# a silly leftover guard in the first check above: keep it plain
rep("ok(v.act === 'plTermOpen' && v.units > 0 && !document && true || (v.act === 'plTermOpen' && v.units > 0), ", "ok(v.act === 'plTermOpen' && v.units > 0, ")
# plannerPrefs: the plPrefs sheet (still the first-time ask) is opened directly; the Builder's card opens the term sheet
rep("""  await click(page, '[data-a="plPrefsOpen"]'); await tick(page, 200);
  let re = await read();""", """  await page.evaluate(() => A.plPrefsOpen()); await tick(page, 200);
  let re = await read();""")
# registration states: the card's headline says "Register …"; a day that's over leaves the units line
rep("""    ['2026-10-22T12:00:00-07:00', 'You register tomorrow, 8:30a', '1 friend same day'],
    ['2026-10-23T06:15:00-07:00', 'You register today at 8:30a · in 2h 15m', '1 friend same day'],
    ['2026-10-23T08:20:00-07:00', 'You register today at 8:30a · in 10m', '1 friend same day'],""",
"""    ['2026-10-22T12:00:00-07:00', 'Register tomorrow, 8:30a', '1 friend same day'],
    ['2026-10-23T06:15:00-07:00', 'Register today at 8:30a · in 2h 15m', '1 friend same day'],
    ['2026-10-23T08:20:00-07:00', 'Register today at 8:30a · in 10m', '1 friend same day'],""")
rep("""    ok(v.line === want && v.fr === fr, `regday states: ${time.slice(5, 16)} → ${want || 'no line (your day is over)'}`, v);""",
    """    ok((want ? v.line === want : /^\\d+ units · What matters most: /.test(v.line)) && v.fr === fr, `regday states: ${time.slice(5, 16)} → ${want || 'just your units (your day is over)'}`, v);""")
rep("""  ok(v.line === null && v.fr === null, 'regday states: Round 1 over, no day — nothing', v);""",
    """  ok(/^\\d+ units · What matters most: /.test(v.line) && !v.units && v.fr === null, 'regday states: Round 1 over, no day — just your units', v);""")
# schedTabTop: the tab bar hides while scrolled down; switch tabs the way a tap does
s = s.replace("await click(page, '[data-a=\"tab\"][data-x=\"home\"]'); await tick(page, 300);\n  await click(page, '[data-a=\"tab\"][data-x=\"schedule\"]'); await tick(page, 300);", "await page.evaluate(() => A.tab('home')); await tick(page, 300);\n  await page.evaluate(() => A.tab('schedule')); await tick(page, 300);")
rep("""  ok(v.line === null && !o.log.rpcs.some(r => r.fn === 'friend_registration_days') && !o.log.reads.some(r => /registration_days/.test(r)), 'regday states: planning a term registration isn’t for — no line, and nothing is asked', v);""",
    """  ok(/^\\d+ units · What matters most: /.test(v.line) && !v.units && !o.log.rpcs.some(r => r.fn === 'friend_registration_days') && !o.log.reads.some(r => /registration_days/.test(r)), 'regday states: planning a term registration isn’t for — just your units, and nothing is asked', v);""")
p.write_text(s)

# stale mutants on the old pill + banner, re-aimed
i = ms.index('  ["card A: registration back in the sub line"'); j = ms.index('\n', i)
ms = ms[:i] + '''  ["card A: units back as their own pill", "  return `<div class=\\"pl-top\\"><div>${term}</div></div>${plTermCard(w)}", "  return `<div class=\\"pl-top\\"><div>${term}</div><button class=\\"pl-pill\\" data-a=\\"plPrefsOpen\\">${plUnitsTarget()} units · Edit</button></div>${plTermCard(w)}", "builderTermCard"],''' + ms[j:]
i = ms.index('  ["prefs: the 1 · 2 · 3 chips back on the Builder"'); j = ms.index('\n', i)
ms = ms[:i] + '''  ["prefs: the 1 · 2 · 3 chips back on the Builder", "  return `<div class=\\"pl-top\\"><div>${term}</div></div>${plTermCard(w)}", "  return `<div class=\\"pl-top\\"><div>${term}</div></div><div class=\\"pl-rank\\">1 · 2 · 3</div>${plTermCard(w)}", "plannerPrefs"],''' + ms[j:]
mrep('''  ["foot: the pill back",''', '''  ["term sheet: the typed time lost on a redraw", "if (t && t.id === 'rd-time' && UI.sheet && (UI.sheet.type === 'regDay' || UI.sheet.type === 'plTerm')) UI.sheet.time", "if (t && t.id === 'rd-time' && UI.sheet && UI.sheet.type === 'regDay') UI.sheet.time", "builderTermCard"],
  ["term sheet: Save writes even when nothing changed", "prefChanged = !before || before.order !== rk.join() || before.units !== sh.units || !!sh.prefsDirty || !!(TC.prefs && TC.prefs.local);", "prefChanged = true;", "builderTermCard"],
  ["term sheet: Remove my day closes it", "if (sh.type === 'plTerm') { if (!e) { sh.day = ''; sh.time = ''; } toast(e || 'Your day is removed'); return render(true); }", "", "builderTermCard"],
  ["term sheet: a time with no day saved as nothing", "if (regWhen() && !sh.day && sh.time) { sh.err = 'Pick your day too, or clear the time.'; return render(true); }", "", "builderTermCard"],
  ["term card: amber with nothing to register", "pl-tc${m || !head ? ' mine' : ''}", "pl-tc${m ? ' mine' : ''}", "builderTermCard"],
  ["tabs: a sub-tab opens where the last one was", "const e = cur(); if (e && t !== S.schedTab) e.y = 0; S.schedTab = t;", "S.schedTab = t;", "schedTabTop"],
  ["rate: one card with hairlines again", "  <div class=\\"list rate-cards\\">${t.items.map(", "  <div class=\\"card list\\" style=\\"margin:0 12px\\">${t.items.map(", "pageWidthHome"],
  ["foot: the pill back",''')
m.write_text(ms)
print('edit-tests-builder-term-card: applied')
