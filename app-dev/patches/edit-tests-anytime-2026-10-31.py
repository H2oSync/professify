#!/usr/bin/env python3
"""(2026-10-31) Tests that need to change with anytime-fixes and dpr-pick-sections: a saved class whose course has ONE section now shows that
section (and the owner's app saves it), so the 2026-10-30 Anytime tests use a class with two or more sections instead.
And after a report is saved, its "Pick your sections" step now comes first (check-app.mjs: dprRead and onbReportLast check
it, then Skip for now; pastWhoTaught, dprTransferContinuing and saveReport()'s users skip it). The now-term's sections
are also read by course code for classes saved with no section (springWall, exploreTerm).
Run from the repo root (or pass it): python3 edit-tests-anytime-2026-10-31.py [root]"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
def edit(rel, pairs):
    p = root / rel; s = p.read_text()
    for a, b in pairs:
        n = s.count(a); assert n == 1, (rel, a[:70], n); s = s.replace(a, b)
    p.write_text(s); print(p, 'edited')

# t1: "an offered class saved with no section" — one with 2+ sections (a one-section class now gets its section)
edit('app-dev/tests/2026-10-30/t1-anytime-sheet.mjs', [(
    "const c = Object.keys(COURSES).find(k => !mine.has(k) && secsOf(k).length);",
    "const c = Object.keys(COURSES).find(k => !mine.has(k) && secsOf(k).length >= 2);   /* (2026-10-31) one section => shown with it */")])
# t2: PHIL 3331 gets a second (synthetic) Fall section, so it stays "no section yet" until the student picks; and it is
#     no longer on the fixture student's record as finished in Spring 2026 (a finished class is hidden now)
edit('app-dev/tests/2026-10-30/t2-now-section.mjs', [(
    "T.saved_classes.push({ user_id: FX.ME.id, term: '2268', code: 'PHIL 3331' });",
    "T.saved_classes.push({ user_id: FX.ME.id, term: '2268', code: 'PHIL 3331' });\n"
    "/* (2026-10-31) a second Fall section (invented): a class with ONE section now shows it, so this one needs two to stay Anytime */\n"
    "T.course_seats.push(Object.assign({}, T.course_seats.find(r => r.term === '2268' && r.course_code === 'PHIL 3331'), { section: '02', class_nbr: '70950', days: 'MoWe 1:10PM - 3:00PM' }));\n"
    "/* (2026-10-31) and not one you finished last spring (the fixtures' record has PHIL 3331, Spring 2026): that one is now hidden */\n"
    "T.class_history = T.class_history.filter(h => !(h.user_id === FX.ME.id && h.code === 'PHIL 3331'));")])

# check-app.mjs: the report's save now opens "Pick your sections" first (this term's class BUS 4488 has 3 sections, none
# picked); Skip for now goes on to "Who taught these?" exactly as before — and the notification ask still waits for both
edit('app-dev/tests/check-app.mjs', [(
    "  ok(after.tab === 'schedule' && after.sub === 'planner' && after.sheet === 'pcWho' && !after.busy, 'save: lands on the Planner, with “Who taught these?” over it first', after);\n",
    "  /* (2026-10-31) first the report's new step, Pick your sections (BUS 4488 has three: nothing picked for you) — Skip for now */\n"
    "  ok(after.tab === 'schedule' && after.sub === 'planner' && after.sheet === 'dprPick' && !after.busy, 'save: lands on the Planner, with “Pick your sections” over it first', after);\n"
    "  ok(await page.evaluate(() => UI.sheet.groups.length === 1 && UI.sheet.groups[0].classes.join() === 'BUS 4488' && !Object.keys(UI.sheet.groups[0].sel).length), 'save: … this term’s class, no section picked for you (three fit)');\n"
    "  await click(page, '#sheet .dpk-foot [data-a=\"dprPickSkip\"]'); await tick(page, 600);\n"
    "  ok(await page.evaluate(() => UI.sheet && UI.sheet.type) === 'pcWho', 'save: Skip for now → “Who taught these?”, as before');\n"), (
    "  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho'), 'onboarding: the report’s classes ask who taught them first');\n",
    "  /* (2026-10-31) Pick your sections comes first now; Skip for now, then who taught them, then the notification ask */\n"
    "  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'dprPick'), 'onboarding: the report’s classes ask for their sections first');\n"
    "  await tick(page, 900); const held0 = await page.evaluate(() => window.__asks.length);\n"
    "  await click(page, '#sheet .dpk-foot [data-a=\"dprPickSkip\"]'); await tick(page, 600);\n"
    "  ok(held0 === 0 && await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho'), 'onboarding: then who taught them (no notification ask yet)', held0);\n")])

# the report's step is skipped where a test is about what comes after it
edit('app-dev/tests/check-app.mjs', [(
    "const saveReport = async page => { await click(page, '[data-a=\"dprSave\"]'); await tick(page, 2500); await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet = null; render(true); }); };",
    "const saveReport = async page => { await click(page, '[data-a=\"dprSave\"]'); await tick(page, 2500); await skipPick(page); await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet = null; render(true); }); };"), (
    "tests.pastWhoTaught = async () => {",
    "/* (2026-10-31) the report's \"Pick your sections\" step, when it opens: Skip for now (it's checked in check-anytime-sections-2026-10-31.mjs) */\n"
    "async function skipPick(page) { if (await page.evaluate(() => !!(UI.sheet && UI.sheet.type === 'dprPick'))) { await click(page, '#sheet .dpk-foot [data-a=\"dprPickSkip\"]'); await tick(page, 600); } }\n"
    "tests.pastWhoTaught = async () => {"), (
    "  await click(page, '[data-a=\"dprSave\"]'); await tick(page, 2500);\n  const got = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys : null);",
    "  await click(page, '[data-a=\"dprSave\"]'); await tick(page, 2500); await skipPick(page);\n  const got = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys : null);"), (
    "  const who = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys.slice().sort() : null);",
    "  await skipPick(page);\n  const who = await page.evaluate(() => UI.sheet && UI.sheet.type === 'pcWho' ? UI.sheet.keys.slice().sort() : null);"), (
    # springWall: Fall is never read whole — by class number, or (2026-10-31) by the codes of classes saved with no section
    "fallSeat.every(r => /class_nbr=in\\.\\(/.test(r)), 'wall: Spring’s whole list is read; Fall is read only by the class numbers people are in'",
    "fallSeat.every(r => /class_nbr=in\\.\\(|course_code=in\\.\\(/.test(r)), 'wall: Spring’s whole list is read; Fall is read only by the class numbers people are in (and, 2026-10-31, by the codes of classes saved with no section)'"), (
    # exploreTerm: the reads the tap makes (the Anytime look-up at open is before it)
    "    await pg2.evaluate(id => A.openFriend(id), fr); await settle(pg2);\n",
    "    const r0 = reads().length;   /* (2026-10-31) the Anytime look-up at open (codes saved with no section) came before */\n"
    "    await pg2.evaluate(id => A.openFriend(id), fr); await settle(pg2);\n"), (
    "    const c1 = await chip(), r1 = reads();",
    "    const c1 = await chip(), r1 = reads().slice(r0);")])
