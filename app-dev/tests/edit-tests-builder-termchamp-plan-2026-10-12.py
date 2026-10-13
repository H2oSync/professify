#!/usr/bin/env python3
"""Tests for builder-termchamp-plan-2026-10-12.py. Run AFTER edit-tests-builder-left-merged-2026-10-12.py.

The Builder no longer drafts into Plans: it shows TermChamp's Plan A, B and C (a week), and a plan changes only with "Set as
Plan X". What matters most is ranked 1-2-3. The top card folds to one line per requirement; its options and in-progress row
are gone. Tests about drafting into Plans and the old plan card are rewritten to that; the rest re-aimed.
Usage: python3 edit-tests-builder-termchamp-plan-2026-10-12.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()

def sub(a, b, label, n=None):
    global S
    if b in S and a not in S: return
    c = S.count(a)
    if c == 0 or (n is not None and c != n): sys.exit(f'{label}: anchor matched {c}x')
    S = S.replace(a, b)

def func(name, body):
    """replace a whole test by its name"""
    global S
    head = f"tests.{name} = async () => {{"
    if S.count(head) != 1: sys.exit(f'func {name}: {S.count(head)}x')
    i = S.index(head); j = S.index("\n};\n", i) + 4
    if body.strip() in S[i:j]: return
    S = S[:i] + body.strip() + "\n" + S[j:]

# ---- helpers: the top card drawn open (its full rows), and its catalog row
sub("d.innerHTML = plLeftCard(R, L, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A');",
    "const o2 = UI.plLeftOpen2; UI.plLeftOpen2 = true; d.innerHTML = plLeftCard(R, L, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A'); UI.plLeftOpen2 = o2;", 'LC open')
sub("cat: (c.querySelector('.pc-cat') || {}).textContent || '', past:",
    "cat: [...((c.querySelector('.pll-cat') || {}).children || [])].map(e => e.textContent).join(' '), past:", 'pcSum cat')

# ---- dprStressQuarter / dprStressMixed: the in-progress lines live in Past classes' Done now, not under what's left
sub("sum.cat === 'Your catalog: Fall Quarter 2023 · report printed Oct 9, 2026', 'quarter catalog: Past classes counts the report",
    "sum.cat === 'Fall Quarter 2023 catalog from your report · Oct 9, 2026', 'quarter catalog: Past classes counts the report", 'quarter cat')
sub("  ok(still.length === 5 && still.filter(r => r.st === 'need').map(r => r.main).join('|') === 'Career Readiness III: BUS 3306' && still.filter(r => r.st === 'taking').length === 4 && still.some(r => /^Approved Elective/.test(r.main) && r.st === 'taking' && /Taking BUS 4442 this term/.test(r.sub)), 'quarter catalog: Still needed on top — the open line, then the 4 in progress",
    "  await openGroups(page); const rowsOpen = await pcRows(page); await page.evaluate(() => { UI.pcGroups = {}; render(true); }); await tick(page, 200);\n  ok(rows.filter(r => r.still).length === 1 && still.filter(r => r.st === 'need').map(r => r.main).join('|') === 'Career Readiness III: BUS 3306' && rowsOpen.filter(r => !r.still && r.st === 'taking').length >= 4 && rowsOpen.some(r => !r.still && /^Approved Elective/.test(r.main) && r.st === 'taking' && /Taking BUS 4442 this term/.test(r.sub)), 'quarter catalog: what’s left is the open line; the 4 in progress (GWR, BUS 3431, BUS 3438, and the Approved Elective by BUS 4442 in My Classes) sit in Done (2026-10-12: not under what’s left)", 'quarter still')
sub("rows2.filter(r => r.still).length === 5, 'quarter catalog: after a reload", "rows2.filter(r => r.still).length === 1, 'quarter catalog: after a reload", 'quarter reload')
sub("  let rows = await pcRows(page); const still = rows.filter(r => r.still);\n  ok(still.length === 8 && still.some(r => r.st === 'cant' && /couldn’t read this line/.test(r.sub)) && still.some(r => r.st === 'taking' && /^D UD/.test(r.main) && /NR 3308 Fall 2026 · this term/.test(r.sub)), 'mixed: Still needed shows the open lines, the unplaceable one as \"can’t check\", and D UD in progress by the class being taken'",
    "  await openGroups(page); let rows = await pcRows(page); const still = rows.filter(r => r.still);\n  ok(still.length === 7 && still.some(r => r.st === 'cant' && /couldn’t read this line/.test(r.sub)) && rows.some(r => !r.still && r.st === 'taking' && /^D UD/.test(r.main) && /NR 3308 Fall 2026 · this term/.test(r.sub)), 'mixed: what’s left shows the open lines and the unplaceable one as \"can’t check\"; D UD, in progress by the class being taken, sits in Done'", 'mixed still')

# ---- pastSimple, pastKinds: who you are is one line now ("Business Administration · Financial Management")
sub("who = await r2.page.evaluate(() => ((document.querySelector('#scroll .pll .pc-me') || {}).innerText || '').replace(/\\s+/g, ' ').trim());",
    "who = await r2.page.evaluate(() => ((document.querySelector('#scroll .pll .pll-who') || {}).innerText || '').replace(/\\s+/g, ' ').trim());", 'pastSimple who')
sub("const w = c.querySelector('.pc-me'), dn = document.querySelector('#scroll .pc-done');",
    "const w = c.querySelector('.pll-who'), cr = c.querySelector('.pll-cat .pc-catc'), dn = document.querySelector('#scroll .pc-done');", 'pastKinds w')
sub("return { who: w ? [...(w.querySelector('.pc-mw') || w).children].map(x => x.textContent) : null, cat: ((w && w.querySelector('.pc-catc')) || {}).textContent || '',",
    "return { who: w ? w.textContent.split(' · ') : null, cat: (cr || {}).textContent || '',", 'pastKinds who')
sub("ok(v && /^pc-me/.test(v.first) && JSON.stringify(v.who) === '[\"Business Administration\"]'", "ok(v && /^pll-who/.test(v.first) && JSON.stringify(v.who) === '[\"Business Administration\"]'", 'pastKinds first')
sub("JSON.stringify(v.who) === '[\"Business Administration\",\"Financial Management concentration\"]'", "JSON.stringify(v.who) === '[\"Business Administration\",\"Financial Management\"]'", 'pastKinds conc')
sub("ok(v && v.left === '2 left to graduate' && v.cat === 'Semester catalog', 'past (report): “2 left to graduate” on top, and the catalog your report judges you by'",
    "ok(v && v.left === '2 left to graduate' && v.cat === '2026-2027 catalog', 'past (report): “2 left to graduate” on top, and the catalog your report judges you by, by name'", 'pastKinds cat')

# ---- dprStressNoMajor: the Builder's card, folded, then open
sub("const nb = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); return c && {",
    "await page.evaluate(() => { UI.plLeftOpen2 = true; render(true); }); await tick(page, 300);\n  const nb = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); return c && {", 'nomajor open')

# ---- workActivities: TermChamp's plans, worked out around the shift (nothing is drafted into Plans)
sub("const d = await page.evaluate(() => { const P = k => (TC.plans[k] || []).map(id => SEC[id]).filter(Boolean);\n    return { drafted: !!plDrafted().at,",
    "const d = await page.evaluate(() => { const P = k => plRecOf(PL_CTX.R, PL_CTX.L, k).map(id => SEC[id]).filter(Boolean);\n    return { drafted: !(TC.plans.A || []).length,", 'work d')
sub("'work: then Plans A, B and C draft — none over the shift'", "'work: then TermChamp’s Plans A, B and C are worked out — none over the shift (and nothing is written into your plans)'", 'work msg')
sub("const s0 = await page.evaluate(() => { const s = (TC.plans.A || []).map(id => SEC[id]).find(", "const s0 = await page.evaluate(() => { const s = plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id]).find(", 'work s0')
sub("clash: AT_PLANS.some(k => (TC.plans[k] || []).map(id => SEC[id]).filter(Boolean).some(s => TC.commits.some(c => secClash(s, c)))), clear:",
    "clash: AT_PLANS.some(k => plRecOf(PL_CTX.R, PL_CTX.L, k).map(id => SEC[id]).filter(Boolean).some(s => TC.commits.some(c => secClash(s, c)))), clear:", 'work rd')
sub("'work: a new one over a drafted class — the plans re-draft around it", "'work: a new one over a class in TermChamp’s plan — the plans are worked out around it", 'work rd msg')

# ---- plannerFromReport: TermChamp's Plan A
sub("planA: (TC.plans.A || []).map(id => SEC[id].code)", "planA: plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id].code)", 'fromReport planA')
sub("/Drafted plans are only yours until you share them/.test(v.note), 'report: the footnote says the picks come from the report, and that drafted plans are private'",
    "/Your plans change only when you set one, and are only yours until you share them/.test(v.note), 'report: the footnote says the picks come from the report, that plans change only when set, and are private'", 'fromReport note')

# ---- springCardA: the card is TermChamp's Plan A — a week now
sub("const a = await page.evaluate(() => { const c = document.querySelector('.pl-card'); const secs = planSecsOf('A'), timed = secs.filter(plOnWeek);",
    "const a = await page.evaluate(() => { const c = document.querySelector('.pl-card'); const secs = plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id]).filter(Boolean), timed = secs.filter(plOnWeek);", 'cardA secs')
sub("await page.evaluate(() => { const tba = SECTIONS.find(s => s.code === 'BUS 4488' && s.s == null); if (tba && !TC.plans.A.map(String).includes(String(tba.id))) TC.plans.A = TC.plans.A.concat([String(tba.id)]); render(true); });",
    "await page.evaluate(() => { const tba = SECTIONS.find(s => s.code === 'BUS 4488' && s.s == null); const ids = plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(String); if (tba && !ids.includes(String(tba.id))) recEditSet('A', ids.concat([String(tba.id)])); render(true); });", 'cardA tba')
sub("ok(a.blocks.length === 0 && /Recommended for Plan A/.test(a.text), 'card A: the Builder has no week — “Recommended for Plan A” and its classes (Tate, 2026-10-11)', { blocks: a.blocks });",
    "ok(await page.locator('.pl-card .plr-wk [data-a=\"recOpen\"]').count() > 0 && /TermChamp’s Plan A/.test(a.text), 'card A: TermChamp’s Plan A as a week — the app’s own grid — and its classes (Tate, 2026-10-12)', { text: a.text.slice(0, 80) });", 'cardA week')
sub("ok(a.any.length === 0 && a.rows.some(r => /BUS 4488/.test(r) && /Time not posted|Online/.test(r)), 'card A: a class with no set time is a row like the others, saying so', { any: a.any, rows: a.rows });",
    "ok(a.any.some(x => /^BUS 4488 · time not posted$/.test(x)) && a.rows.some(r => /BUS 4488/.test(r) && /Time not posted|Online/.test(r)), 'card A: a class with no set time sits under the week as Anytime, and is a row like the others', { any: a.any, rows: a.rows });", 'cardA any')
sub("  await click(page, '.pla-tab[data-x=\"B\"]'); await tick(page, 400);", "  await page.evaluate(() => recEditSet('A', null));\n  await click(page, '.pla-tab[data-x=\"B\"]'); await tick(page, 400);", 'cardA reset')

# ---- plannerPlan: Set as Plan A in place of Edit; nothing drafted on arrival; the rules hold for TermChamp's plans
sub("ok(!v.days && v.blocks === 0, 'plan: the Builder card has no week (Plans shows the schedule)', v);",
    "ok(await page.locator('#scroll .plr .plr-wk [data-a=\"recOpen\"]').count() > 0, 'plan: TermChamp’s Plan A is a week (the app’s grid) — a tap on a class changes it out', v);", 'plan week')
sub("ok(v.tiles.length === 0 && v.edit === 'Edit Plan A', 'plan: no tiles (2026-10-11) and an Edit Plan A button', { tiles: v.tiles, edit: v.edit });",
    "ok(v.tiles.length === 0 && !v.edit && await page.locator('#scroll .plr-set').innerText() === 'Set as Plan A', 'plan: no tiles, and “Set as Plan A” in place of Edit Plan A (2026-10-12)', { tiles: v.tiles, edit: v.edit });", 'plan set')
i = S.find("  ok(b.on && b.on.trim() === 'Plan B' && /plan-B/.test(b.cls) && /^(Edit Plan B|Draft it for me)$/.test(b.edit), 'plan: the switch shows Plan B (Backup) in the same card', b);")
if i >= 0:
    S = S.replace("  ok(b.on && b.on.trim() === 'Plan B' && /plan-B/.test(b.cls) && /^(Edit Plan B|Draft it for me)$/.test(b.edit), 'plan: the switch shows Plan B (Backup) in the same card', b);",
                  "  ok(b.on && b.on.trim() === 'Plan B' && /plan-B/.test(b.cls) && await page.locator('#scroll .plr-set').innerText() === 'Set as Plan B', 'plan: the switch shows TermChamp’s Plan B in the same card', b);")
sub("  await click(page, '.pl-card .pl-edit'); await tick(page, 400);\n  ok(await page.evaluate(() => S.schedTab === 'plans' && S.plan === 'A' && document.querySelector('.seg.plans button.on').innerText.trim() === 'Plan A'), 'plan: Edit Plan A opens the Plans tab on Plan A');",
    "  const recA = await page.evaluate(() => plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(String));\n  await click(page, '#scroll .plr-set'); await tick(page, 600);\n  ok(await page.evaluate(ids => JSON.stringify(TC.plans.A.map(String)) === JSON.stringify(ids) && /This is your Plan A/.test(document.querySelector('#scroll .plr').innerText), recA), 'plan: Set as Plan A makes your Plan A TermChamp’s, and the card says so');\n  await click(page, '[data-a=\"schedTab\"][data-x=\"plans\"]'); await tick(page, 400);\n  ok(await page.evaluate(() => S.schedTab === 'plans' && S.plan === 'A' && document.querySelector('.seg.plans button.on').innerText.trim() === 'Plan A' && planSecs('A').length > 0), 'plan: Plans then holds it');", 'plan edit')
sub("  ok(pw.length === 3 && pw.map(w => w.body.slot).sort().join() === 'A,B,C' && pw.every(w => w.body.sections.every(s => s.class_nbr && s.code)) && pw.find(w => w.body.slot === 'A').body.sections.length > 0, 'plan: A, B and C were drafted into the empty plans once, as real sections', pw.map(w => [w.body.slot, w.body.sections.map(s => s.code)]));",
    "  ok(pw.length === 1 && pw[0].body.slot === 'A' && pw[0].body.sections.every(s => s.class_nbr && s.code) && pw[0].body.sections.length > 0, 'plan: nothing is drafted into Plans on arrival — the one write is the Set (2026-10-12)', pw.map(w => [w.body.slot, w.body.sections.map(s => s.code)]));", 'plan writes')
sub("  ok(drafted && Array.isArray(drafted.A) && drafted.A.length === pw.find(w => w.body.slot === 'A').body.sections.length && !drafted.own, 'plan: what was drafted is remembered on the phone, per plan', drafted);",
    "  ok(drafted && drafted.own, 'plan: once one is set, the phone remembers the plans are the student’s', drafted);", 'plan drafted')
sub("for (const k of ['A', 'B', 'C']) { const a = (TC.plans[k] || []).map(id => SEC[id]), keys = a.map(s => (R.all.find(c => c.code === s.code) || {}).key), st = planStats(k, L);",
    "for (const k of ['A', 'B', 'C']) { const a = plRecOf(PL_CTX.R, PL_CTX.L, k).map(id => SEC[id]), keys = a.map(s => (R.all.find(c => c.code === s.code) || {}).key), st = { units: a.reduce((t, s) => t + (unitsOf(s.code, L) || 0), 0), n: a.length };", 'plan rules')

# ---- builderPlans
sub("v.head === 'Recommended for Plan A' && v.sum === undefined, 'builder: “Recommended for Plan A” with Plan A · Plan B · Plan C — no units · professors line under it (Tate 2026-10-11: “take this out”)'",
    "v.head === 'TermChamp’s Plan A' && v.sum === undefined, 'builder: “TermChamp’s Plan A” with Plan A · Plan B · Plan C (2026-10-12)'", 'bp head')
sub("ok(v.grid === 0 && v.rows > 0 && v.why > 0, 'builder: no week grid or Anytime strip — the recommended classes, each saying why it counts', v);",
    "ok(await page.locator('#scroll .plr .plr-wk [data-a=\"recOpen\"]').count() > 0 && v.rows > 0 && await page.locator('#scroll .plr .pl-row .pl-tags .pk-tag').count() > 0, 'builder: TermChamp’s plan as a week, then each class saying why it counts', v);", 'bp grid')
sub("await page.evaluate(() => { TC.plans.B = TC.plans.A.slice(); UI.plPlan = 'B'; render(true); }); await tick(page, 300);",
    "await page.evaluate(() => { recEditSet('B', plRecOf(PL_CTX.R, PL_CTX.L, 'A')); UI.plPlan = 'B'; render(true); }); await tick(page, 300);", 'bp same')
sub("ok(/Same as Plan A/.test(await page.locator('#scroll .pl-card').innerText()), 'builder: a plan that came out the same as Plan A says no other section fits');",
    "ok(/Same as Plan A/.test(await page.locator('#scroll .pl-card').innerText()), 'builder: a plan that came out the same as Plan A says no other section fits');\n  await page.evaluate(() => { recEditSet('B', null); render(true); });", 'bp same reset')

# ---- rewritten whole: prefs ranked; plans never drafted into; TermChamp's plans; the folded top card
func('plannerPrefs', r"""
tests.plannerPrefs = async () => {
  const T = Object.assign({}, NOPLANS(), { planner_prefs: [] });
  let noRank = false;
  const { page, close, log } = await openApp({ tables: T, hook: (url, m, body) => noRank && m === 'POST' && /\/rest\/v1\/planner_prefs$/.test(url.pathname) && body && 'ranking' in body ? { status: 400, body: JSON.stringify({ message: "Could not find the 'ranking' column of 'planner_prefs' in the schema cache", code: 'PGRST204' }) } : null });
  await toPlanner(page);
  const read = () => page.evaluate(() => { const s = document.getElementById('sheet'); return { type: UI.sheet && UI.sheet.type, t: s.innerText, rank: [...s.querySelectorAll('.pp-opt')].map(b => [b.dataset.x, (b.querySelector('.pp-n') || {}).textContent || '', b.getAttribute('aria-pressed')]), units: [...s.querySelectorAll('.pp-units button')].map(b => [b.innerText.trim(), b.className]), x: !!s.querySelector('.xbtn'), save: !!(s.querySelector('[data-a="plPrefsSave"]') || {}).disabled }; });
  let sh = await read();
  ok(sh.type === 'plPrefs' && /What matters most\?/.test(sh.t) && sh.rank.map(r => r[0] + r[1]).join() === 'degree1,professors2,friends3' && !sh.x && !sh.save, 'prefs: the first open asks what matters most, ranked 1 · 2 · 3 (degree, professors, friends to start), no close button', sh);
  ok(sh.units.map(u => u[0]).join() === '12,14,16,18,20' && sh.units.find(u => u[0] === '16')[1].includes('on'), 'prefs: units 12 · 14 · 16 · 18 · 20 with 16 picked', sh.units);
  ok(await page.evaluate(() => { A.closeSheet(); return UI.sheet && UI.sheet.type === 'plPrefs'; }), 'prefs: tapping outside (the scrim’s close) doesn’t dismiss the first ask');
  await page.evaluate(() => { UI.sheet = null; render(true); }); await tick(page, 400);
  const again = await page.evaluate(() => ({ type: UI.sheet && UI.sheet.type, card: !!document.querySelector('#scroll .pl-ask [data-a="plPrefsOpen"]') }));
  ok(again.type === 'plPrefs' && again.card, 'prefs: if the ask is closed some other way it comes back — and the Builder shows a button for it', again);
  /* rank: tapping number 1 starts over; then tap in order, and the last fills itself */
  await click(page, '[data-a="plPrefPick"][data-x="degree"]');
  sh = await read();
  ok(sh.rank.every(r => !r[1] && r[2] === 'false') && sh.save && /Tap what matters most/.test(sh.t), 'prefs: tapping number 1 starts the ranking over — Save waits for all three', sh);
  await click(page, '[data-a="plPrefPick"][data-x="friends"]');
  sh = await read();
  ok(sh.rank.map(r => r[1]).join() === ',,1' && sh.save && /Tap what matters next/.test(sh.t), 'prefs: the first tap is number 1', sh.rank);
  await click(page, '[data-a="plPrefPick"][data-x="degree"]');
  sh = await read();
  ok(sh.rank.map(r => r[0] + r[1]).join() === 'degree2,professors3,friends1' && !sh.save, 'prefs: the second tap is number 2, and the last is number 3 by itself', sh.rank);
  await click(page, '[data-a="plPrefUnits"][data-x="18"]');
  await click(page, '[data-a="plPrefsSave"]'); await tick(page, 3000);
  const pw = log.writes.filter(w => w.table === 'planner_prefs');
  ok(pw.length === 1 && pw[0].body.priority === 'friends' && pw[0].body.ranking === 'friends,degree,professors' && pw[0].body.units === 18 && pw[0].body.user_id === FX.ME.id, 'prefs: saved as one row — the first as priority, the whole order as ranking, and the units', pw[0] && pw[0].body);
  const after = await page.evaluate(() => { const sc = document.getElementById('scroll'); return { sheet: UI.sheet, rank: ((sc.querySelector('.pl-rank') || {}).innerText || '').replace(/\s+/g, ' ').trim(), pill: (sc.querySelector('.pl-pill') || {}).innerText, rec: sc.querySelectorAll('.plr .pl-row').length, w: plWeights(), local: JSON.parse(localStorage.getItem('tc-prefs:' + TC.user.id) || 'null') }; });
  ok(!after.sheet && after.rank === '1 Friends 2 Degree 3 Professors' && after.pill === '18 units · Edit' && after.rec > 0 && after.local && after.local.order.join() === 'friends,degree,professors', 'prefs: the Builder shows your order and the units, then TermChamp’s plan; the order is also kept on the phone', after);
  ok(after.w.friends === 1.5 && after.w.degree === 1.0 && after.w.professors === 0.6, 'prefs: the order weighs the picks — 1st 1.5, 2nd 1.0, 3rd 0.6', after.w);
  ok(planWrites(log).length === 0 && log.writes.filter(w => w.table === 'watch_sections').length === 0, 'prefs: nothing is written into Plans (or seat alerts) by itself — plans change when you set one', planWrites(log).map(w => w.body.slot));
  /* Edit reopens on the saved order and says what a new one changes */
  await click(page, '[data-a="plPrefsOpen"]'); await tick(page, 200);
  let re = await read();
  ok(re.x && re.rank.map(r => r[0] + r[1]).join() === 'degree2,professors3,friends1' && /Save/.test(re.t) && !/worked out again/.test(re.t), 'prefs: Edit reopens on the saved order, with a close button and Save', re);
  await click(page, '[data-a="plPrefPick"][data-x="friends"]'); await click(page, '[data-a="plPrefPick"][data-x="professors"]');
  re = await read();
  ok(re.rank.map(r => r[0] + r[1]).join() === 'degree3,professors1,friends2' && /worked out again in this order\. Your own plans stay as they are/.test(re.t), 'prefs: a new order says TermChamp’s plans are worked out again, and your own plans stay', re);
  /* before RUN 19: the first is saved, the order kept on the phone */
  noRank = true; await click(page, '[data-a="plPrefsSave"]'); await tick(page, 1500);
  const tries = log.writes.filter(w => w.table === 'planner_prefs').slice(-2);
  ok(tries.length === 2 && 'ranking' in tries[0].body && !('ranking' in tries[1].body) && tries[1].body.priority === 'professors' && await page.evaluate(() => !UI.sheet && TC.prefsNoRank && prefOrder().join() === 'professors,friends,degree'), 'prefs: without the ranking column (RUN 19 not run yet) the save is tried again without it — the first is saved, the order kept on the phone', tries.map(t => t.body));
  ok(log.errors.length === 0, 'prefs: no page errors', log.errors);
  await close();
};
""")

func('plannerNoDraft', r"""
tests.plannerNoDraft = async () => {
  /* 1. the plans read fails: TermChamp's plan still shows, but it can't be set over plans that didn't load */
  let failPlans = true;
  const hook = (url, m) => { if (failPlans && m === 'GET' && /\/rest\/v1\/plans$/.test(url.pathname) && /user_id=eq\./.test(url.search)) return { status: 500, body: JSON.stringify({ message: 'fixture: plans read failed', code: 'XX000' }) }; };
  let o = await openApp({ tables: NOPLANS(), hook });
  await toPlanner(o.page);
  const rd = p => p.evaluate(() => ({ err: TC.err.plans, loaded: TC.plansLoaded, t: (document.querySelector('#scroll .plr') || {}).innerText || '', retry: !!document.querySelector('#scroll .plr [data-a="plRetryPlans"]'), set: !!document.querySelector('#scroll [data-a="recSet"]'), rows: document.querySelectorAll('#scroll .plr .pl-row').length, nudge: !!document.querySelector('#scroll .tc-dpr-row'), pre: UI.pl && UI.pl.prereqs, all: document.getElementById('scroll').innerText }));
  let v = await rd(o.page);
  ok(v.err && !v.loaded && v.rows > 0 && /Couldn’t load your plans, so this can’t be set as Plan A yet/.test(v.t) && v.retry && !v.set && !o.log.writes.some(w => w.table === 'plans'), 'no draft: when the plans don’t load, TermChamp’s plan still shows — but it can’t be set over them; Try again', v);
  failPlans = false;
  await click(o.page, '#scroll .plr [data-a="plRetryPlans"]'); await tick(o.page, 1500);
  v = await rd(o.page);
  ok(v.loaded && v.set && planWrites(o.log).length === 0, 'no draft: once they load, “Set as Plan A” is back — and nothing was written', { loaded: v.loaded, set: v.set, writes: planWrites(o.log).length });
  ok(o.log.errors.length === 0, 'no draft (plans): no page errors', o.log.errors);
  await o.close();
  /* 2. no record and no report: nothing to work a plan out from */
  o = await openApp({ tables: NOREC() });
  await toPlanner(o.page);
  await click(o.page, '.tc-dpr [data-a="plShowPicks"]'); await tick(o.page, 1500);
  v = await rd(o.page);
  ok(/worked out once it has your past classes/.test(v.t) && !v.set && v.nudge && planWrites(o.log).length === 0, 'no draft: with no past classes and no report, TermChamp’s plan says what it needs — nothing is written', v);
  await uploadDpr(o.page, '.tc-dpr-row input[data-in="dprfile"]'); await click(o.page, '[data-a="dprSave"]'); await tick(o.page, 3000);
  await o.page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.sheet = null; S.schedTab = 'planner'; render(true); }); await tick(o.page, 1500);
  v = await rd(o.page);
  ok(v.rows > 0 && planWrites(o.log).length === 0, 'no draft: after the report, TermChamp’s plan is worked out from it — and still nothing is written into Plans', { rows: v.rows, writes: planWrites(o.log).map(w => w.body.slot) });
  ok(o.log.errors.length === 0, 'no draft (no data): no page errors', o.log.errors);
  await o.close();
  /* 3. prerequisites failed to load: the plan says it doesn't check them */
  o = await openApp({ tables: NOPLANS(), hook: (url, m) => m === 'GET' && /\/rest\/v1\/course_prereqs$/.test(url.pathname) ? { status: 500, body: JSON.stringify({ message: 'fixture: prereqs failed', code: 'XX000' }) } : null });
  await toPlanner(o.page);
  v = await rd(o.page);
  ok(v.pre === false && planWrites(o.log).length === 0 && /Prerequisites didn’t load, so TermChamp’s plan doesn’t check them/.test(v.all), 'no draft: without prerequisites, TermChamp’s plan says it doesn’t check them; nothing is written', { pre: v.pre, writes: planWrites(o.log).length });
  await o.close();
};
""")

func('plannerRefresh', r"""
tests.plannerRefresh = async () => {
  const { page, close, log } = await openApp({ tables: NOPLANS() });
  await toPlanner(page);
  const rec = () => page.evaluate(() => ({ audit: !!(PL_CTX && PL_CTX.R.audit), a: plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id].code) }));
  const r0 = await rec();
  ok(!r0.audit && r0.a.length > 0 && planWrites(log).length === 0, 'refresh: TermChamp’s Plan A is worked out from the record, and nothing is written into Plans', r0);
  /* the student puts a class into Plan C by hand: it's theirs, and it gets a seat alert */
  const own = await page.evaluate(() => { const s = Object.values(SEC).find(x => x && x.code && x.s != null && !TC.watches[x.id]); TC.setPlan('C', [String(s.id)]); return String(s.id); });
  await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'watch_sections').map(x => x.body && x.body.class_nbr);
  ok(w.length === 1 && w[0] === own, 'refresh: a class the student adds by hand gets its seat alert', w);
  const c = await page.evaluate(() => TC.plans.C.slice()), n0 = planWrites(log).length;
  await page.evaluate(() => { S.schedTab = 'past'; render(); }); await tick(page, 800);
  await uploadDpr(page); await click(page, '[data-a="dprSave"]'); await tick(page, 3000);
  await page.evaluate(() => { UI.sheet = null; S.schedTab = 'planner'; render(true); }); await tick(page, 1500);
  const r1 = await rec(), c2 = await page.evaluate(() => TC.plans.C.slice());
  ok(r1.audit && r1.a.length > 0 && planWrites(log).length === n0 && JSON.stringify(c2) === JSON.stringify(c), 'refresh: after the report, TermChamp’s plans are worked out from it; Plan C stays exactly as the student made it', { r1, c, c2, writes: planWrites(log).length - n0 });
  ok(log.errors.length === 0, 'refresh: no page errors', log.errors);
  await close();
};
""")

func('plannerExistingPlan', r"""
tests.plannerExistingPlan = async () => {
  const { page, close, log } = await openApp({});   /* the fixture's ME has sections in Plan B */
  await toPlanner(page);
  const B0 = await page.evaluate(() => TC.plans.B.map(String));
  ok(!log.writes.some(w => w.table === 'plans') && B0.length > 0, 'existing: the Builder writes nothing into the plans on the account', B0);
  await click(page, '[data-a="plShowPlan"][data-x="B"]'); await tick(page, 300);
  const v = await page.evaluate(() => ({ head: (document.querySelector('#scroll .plr .pl-rech') || {}).innerText, note: (document.querySelector('#scroll .plr-note') || {}).innerText || '', set: (document.querySelector('#scroll .plr-set') || {}).innerText, ids: plRecOf(PL_CTX.R, PL_CTX.L, 'B').map(String) }));
  ok(v.head === 'TermChamp’s Plan B' && v.set === 'Set as Plan B' && new RegExp(`Replaces the ${B0.length} class`).test(v.note), 'existing: TermChamp’s Plan B says setting it replaces the classes in your Plan B', v);
  await click(page, '#scroll .plr-set'); await tick(page, 800);
  const pw = planWrites(log), t = await page.evaluate(() => ({ toast: document.getElementById('toast').textContent, undo: !!document.querySelector('#toast [data-a="toastUndo"]'), same: (document.querySelector('#scroll .plr-same') || {}).innerText || '' }));
  ok(pw.length === 1 && pw[0].body.slot === 'B' && JSON.stringify(pw[0].body.sections.map(s => String(s.class_nbr)).sort()) === JSON.stringify(v.ids.slice().sort()), 'existing: Set as Plan B writes Plan B only, with TermChamp’s classes', pw.map(w => [w.body.slot, w.body.sections.length]));
  ok(/Plan B is set/.test(t.toast) && t.undo && /This is your Plan B/.test(t.same), 'existing: it says so, with Undo, and the card says it’s your Plan B now', t);
  await click(page, '#toast [data-a="toastUndo"]'); await tick(page, 800);
  ok(await page.evaluate(b => JSON.stringify(TC.plans.B.map(String)) === JSON.stringify(b), B0), 'existing: Undo puts Plan B back as it was');
  /* Plans: an empty plan points to the Builder */
  await page.evaluate(() => { TC.commits = []; S.schedTab = 'plans'; S.plan = 'C'; render(true); }); await tick(page, 400);
  const e = await page.evaluate(() => ({ t: (document.querySelector('#scroll .empty') || {}).innerText || '', btn: !!document.querySelector('#scroll .empty [data-a="schedTab"][data-x="planner"]') }));
  ok(/Nothing in Plan C yet/.test(e.t) && /Set TermChamp’s Plan C from the Builder/.test(e.t) && e.btn, 'existing: an empty plan in Plans points to the Builder', e);
  ok(log.errors.length === 0, 'existing: no page errors', log.errors);
  await close();
};
""")

func('builderLeft', r"""
tests.builderLeft = async () => {
  const { page, close, log } = await openApp({ height: 1600 });
  await toPlanner(page, true);
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.plPlan = 'A'; render(true); }); await tick(page, 400);
  const read = () => page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; plSync(); const L = TCPL.ledger(), k = /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A';
    return { h: c.querySelector('.pll-h').innerText.replace(/\s+/g, ' ').trim(), exp: c.querySelector('.pll-h').getAttribute('aria-expanded'), n: L.need.length + L.needU.length, first: !!(c.compareDocumentPosition(document.querySelector('#scroll .plr')) & Node.DOCUMENT_POSITION_FOLLOWING),
      lines: [...c.querySelectorAll('.pll-line')].map(q => ({ label: q.querySelector('.pll-rl').innerText, inn: (q.querySelector('.pll-in') || {}).innerText || '' })), opts: c.querySelectorAll('.pll-opt, .pll-add, .pll-meta').length, more: !!c.querySelector('.pll-all'), ip: !!c.querySelector('[data-a="pcInpOpen"], .pll-ip'), rec: plRecOf(PL_CTX.R, PL_CTX.L, k).map(id => SEC[id].code) }; });
  let v = await read();
  ok(v && v.h === `${v.n} left on your flowchart` && v.exp === 'false' && v.first, 'builder: opens with what’s left (folded), above TermChamp’s plan', v && { h: v.h, n: v.n, exp: v.exp, first: v.first });
  ok(v.lines.length === Math.min(6, v.n) && (v.n > 6 ? v.more : !v.more) && v.opts === 0 && !v.ip, 'builder: folded, one line per requirement (six, then All N) — no options under them (the plan has them), no in-progress row (Tate 2026-10-12)', { lines: v.lines.length, n: v.n, opts: v.opts, ip: v.ip });
  const named = v.lines.filter(l => l.inn);
  ok(named.length > 0 && named.every(l => /^Plan A · [A-Z]{2,5} \d{4}/.test(l.inn) && v.rec.includes(l.inn.replace(/^Plan A · /, ''))), 'builder: a line TermChamp’s Plan A fills names the class it uses', named);
  await click(page, '[data-a="plShowPlan"][data-x="B"]'); await tick(page, 300);
  v = await read();
  ok(v.lines.filter(l => l.inn).every(l => /^Plan B · /.test(l.inn) && v.rec.includes(l.inn.replace(/^Plan B · /, ''))), 'builder: on Plan B the lines name Plan B’s classes', v.lines);
  await click(page, '#scroll .pll-h'); await tick(page, 300);
  v = await read();
  ok(v.exp === 'true', 'builder: a tap on “N left” opens it, and again folds it', v.exp);
  if (v.more) { await click(page, '.pll [data-a="plLeftAll"]'); await tick(page, 300); v = await read(); }
  ok(v.lines.length === v.n, 'builder: “All N” lists every requirement left', [v.lines.length, v.n]);
  await click(page, '#scroll .pll-h'); await tick(page, 300);
  ok((await read()).exp === 'false', 'builder: and folds again');
  ok(log.errors.length === 0, 'builder left: no page errors', log.errors);
  await close();
};
""")

func('builderMerged', r"""
tests.builderMerged = async () => {
  const { page, close, log } = await openApp({ tables: XFER_T('Business Administration', 'Senior'), height: 2600 });
  await toPlanner(page); await uploadFile(page, 'dpr-stress-quarter.pdf'); await saveReport(page);
  await page.evaluate(() => { UI.plPlan = 'A'; S.schedTab = 'planner'; render(true); }); await tick(page, 1500);
  const rd = () => page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; const t = e => e ? e.innerText.replace(/\s+/g, ' ').trim() : '';
    return { order: [...c.children].map(e => e.className.split(' ')[0]), who: t(c.querySelector('.pll-who')), cat: t(c.querySelector('.pll-cat')), h: t(c.querySelector('.pll-h')), num: t(c.querySelector('.pc-nrow')), bar: (c.querySelector('.pc-bar') || { getAttribute: () => '' }).getAttribute('aria-label'),
      lines: [...c.querySelectorAll('.pll-line')].map(e => t(e)), rows: [...c.querySelectorAll('.pll-req .pc-row')].map(q => ({ row: t(q.querySelector('.pc-main')), mark: !!q.querySelector('[data-a="plMarkAsk"]') })), opts: c.querySelectorAll('.pll-opt').length,
      ip: !!document.querySelector('#scroll [data-a="pcInpOpen"]'), foot: !!c.querySelector('.pc-cat'), go: !!c.querySelector('.pc-go'), rec: !!(c.compareDocumentPosition(document.querySelector('#scroll .plr')) & Node.DOCUMENT_POSITION_FOLLOWING) }; });
  let b = await rd();
  ok(b && b.who === 'Business Administration · Financial Management' && /^Fall Quarter 2023 catalog from your report · Oct 9, 2026$/.test(b.cat) && b.h === '1 left to graduate' && b.num === '37 of 38 filled' && b.bar === '37 of 38 filled' && b.rec,
    'builder: one card on top — major · concentration on one line, the report’s catalog as its own row, “1 left to graduate”, the count and bar — then TermChamp’s plan', b && { who: b.who, cat: b.cat, h: b.h, num: b.num, rec: b.rec });
  ok(b && b.lines.length === 1 && /^Career Readiness III/.test(b.lines[0]) && !b.rows.length && !b.opts && !b.ip && !b.foot && !b.go, 'builder: folded, each requirement is one line; no options, no in-progress row, no catalog footnote, no “Best options” button', b && { lines: b.lines, rows: b.rows.length, opts: b.opts, ip: b.ip });
  await click(page, '#scroll .pll-h'); await tick(page, 300);
  b = await rd();
  ok(b.rows.length === 1 && b.rows[0].mark && /Career Readiness III/.test(b.rows[0].row), 'builder: a tap opens each line in full, with Mark done', b.rows);
  await click(page, '#scroll .pll-h'); await tick(page, 300);
  /* a report that names no concentration: the pick sits in the card, and a long name wraps inside it on a 320px phone */
  await page.setViewportSize({ width: 320, height: 2600 });
  await page.evaluate(() => { TC.audit.conc = null; TC.profile.concentration = null; TCPL.set({ student: { major: TC.profile.major, conc: '', standing: '' } }); render(true); }); await tick(page, 600);
  const cc = await page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; const r = c.getBoundingClientRect(), pr = parseFloat(getComputedStyle(c).paddingRight), chips = [...c.querySelectorAll('.pc-conc .chip')]; return { n: chips.length, out: chips.filter(e => e.getBoundingClientRect().right > r.right - pr + 0.5 || e.scrollWidth > e.clientWidth + 1).map(e => e.textContent) }; });
  ok(cc && cc.n > 0 && !cc.out.length, 'builder: with no concentration on the report, the pick is in the card — every name fits inside it at 320px', cc);
  await page.setViewportSize({ width: 390, height: 2600 });
  await page.evaluate(() => { TC.audit.conc = 'Financial Management'; render(true); }); await tick(page, 300);
  /* Past classes: only what's below */
  await toPastTab(page);
  const p = await page.evaluate(() => ({ first: (document.querySelector('#scroll .pc-pg > *') || {}).className || '', top: document.querySelectorAll('#scroll .pc-sum, #scroll .pc-left, #scroll .pc-num, #scroll .pc-go, #scroll .pc-cat, #scroll .pc-catc, #scroll .pc-me, #scroll .pll').length,
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
  const f = await r.page.evaluate(() => ({ prof: [...document.querySelectorAll('#scroll .profrow')].map(e => e.querySelectorAll('.av, img').length), secs: document.querySelectorAll('#scroll .secrow .av, #scroll .secrow img, #scroll [data-a="secSheet"] .av, #scroll [data-a="secSheet"] img').length, strip: /taking this/.test(document.getElementById('scroll').innerText) }));
  ok(code && f.prof.length && f.prof.every(n => n <= 1) && f.secs > 0 && f.strip, 'class page: a friend’s face sits on their section, not the professor’s row; “… taking this” stays on top', { code, f });
  ok(r.log.errors.length === 0, 'class page faces: no page errors', r.log.errors);
  await r.close();
};
""")

# ---- new: TermChamp's plans themselves
if 'tests.builderRec = ' not in S:
    a = "\nconst names = Object.keys(tests).filter(n => !only || n === only);"
    if S.count(a) != 1: sys.exit('builderRec anchor')
    S = S.replace(a, r"""
/* (2026-10-12) Tate: "the best possible term champ plan … Plan A puts in the classes already into a little mocked up schedule
   week … Plan B should show maybe different option for both … the plans are separate from this … set as plan A, or … change
   out this class". TermChamp's Plan A, B and C: a week, why each class, swap / take out / start over, Set as Plan X (Undo). */
tests.builderRec = async () => {
  const { page, close, log } = await openApp({ tables: NOPLANS(), height: 2000 });
  await toPlanner(page, true);
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.plPlan = 'A'; render(true); }); await tick(page, 600);
  const st = () => page.evaluate(() => { const c = document.querySelector('#scroll .plr'), R = PL_CTX.R, L = PL_CTX.L, done = new Set(TCPL.completed().map(x => TCPL.canon(x) || x)), mine = new Set([...takingCodes()].map(x => TCPL.canon(x) || x));
    const P = k => plRecOf(R, L, k).map(id => SEC[id]).filter(Boolean);
    return { head: (c.querySelector('.pl-rech') || {}).innerText, blocks: c.querySelectorAll('.plr-wk [data-a="recOpen"]').length, rows: c.querySelectorAll('.pl-row').length, n: P('A').length, set: (c.querySelector('.plr-set') || {}).innerText || '', note: (c.querySelector('.plr-note') || {}).innerText || '',
      codes: { A: P('A').map(s => s.code), B: P('B').map(s => s.code), C: P('C').map(s => s.code) }, ids: { A: P('A').map(s => String(s.id)), B: P('B').map(s => String(s.id)) },
      bad: ['A', 'B', 'C'].some(k => P(k).some((s, i, a) => a.slice(i + 1).some(t => secClash(s, t)) || done.has(TCPL.canon(s.code) || s.code) || mine.has(TCPL.canon(s.code) || s.code))),
      reset: !!c.querySelector('[data-a="recReset"]'), plansA: (TC.plans.A || []).map(String) }; });
  let v = await st();
  ok(v.head === 'TermChamp’s Plan A' && v.blocks > 0 && v.rows === v.n && v.n > 0 && v.set === 'Set as Plan A' && /Your Plan A is empty/.test(v.note), 'rec: TermChamp’s Plan A as a week, one row per class, and “Set as Plan A” (your Plan A is empty)', v);
  ok(!v.bad, 'rec: in A, B and C nothing overlaps, and never a class you’ve taken or are taking', v.codes);
  ok(JSON.stringify(v.ids.A) !== JSON.stringify(v.ids.B), 'rec: Plan B isn’t Plan A — another class or section where one fits', v.ids);
  /* tap a class: why, and what it could be instead */
  const first = v.ids.A[0];
  await page.locator('#scroll .plr .pl-row').first().click(); await tick(page, 400);
  const sh = await page.evaluate(() => { const s = document.getElementById('sheet'); return { type: UI.sheet && UI.sheet.type, t: s.innerText, swaps: [...s.querySelectorAll('[data-a="recSwap"]')].map(b => b.dataset.x), add: !!s.querySelector('[data-a="addPlanSheet"]'), drop: !!s.querySelector('[data-a="recDrop"]') }; });
  ok(sh.type === 'recSec' && /Why TermChamp picked it/i.test(sh.t) && /Change it out/i.test(sh.t) && sh.add && sh.drop, 'rec: a class opens why TermChamp picked it, what to change it out for, Add just this, and Take it out', sh);
  ok(!sh.swaps.some(x => /\|99499$/.test(x)), 'rec: a section over another class in the plan is never offered as a swap', sh.swaps);
  /* what's left comes first, even when a better-scoring pick would fill the units */
  const ord = await page.evaluate(() => { const R = PL_CTX.R, L = PL_CTX.L, cs = R.all.filter(c => plDraftSec(c.code, [], null)).slice(0, 2); if (cs.length < 2) return null;
    const b = { label: 'Fixture line', status: 'not', kind: 'major', options: [cs[1].code], oneOf: false };
    const R2 = { all: [Object.assign({}, cs[0], { fills: [], wscore: 100, score: 100, onTerm: true, units: 12 }), Object.assign({}, cs[1], { fills: [b], wscore: 1, score: 1, onTerm: false, units: 4 })], audit: true, X: { open: [b], unknown: [], total: null, filled: [], live: [b], inprog: [] }, sugg: new Set() };
    const was = TC.prefs.units, au = TC.audit; TC.prefs.units = 12; TC.audit = { reqs: [b], overrides: [] }; let ids; try { ids = plRecDraft(R2, L, 'A', []); } finally { TC.prefs.units = was; TC.audit = au; } return { got: ids.map(id => SEC[id].code), want: cs[1].code }; });
  ok(ord && ord.got.includes(ord.want), 'rec: the class for what’s left goes in first, ahead of a better-scoring pick', ord);
  /* your work on the week */
  const cm = await page.evaluate(() => { const was = TC.commits; TC.commits = [{ id: 'cm1', kind: 'work', name: 'Shift', days: 'M', s: 7 * 60, e: 8 * 60, busy: true }]; render(true); const n = document.querySelectorAll('#scroll .plr .g-cm').length; TC.commits = was; render(true); return n; });
  ok(cm === 1, 'rec: your work and practice are drawn on TermChamp’s week', cm);
  if (sh.swaps.length) {
    const [, from, to] = sh.swaps[0].split('|');
    await page.locator('#sheet [data-a="recSwap"]').first().click(); await tick(page, 500);
    v = await st();
    ok(v.ids.A.includes(to) && !v.ids.A.includes(from) && v.reset && planWrites(log).length === 0, 'rec: Swap changes TermChamp’s plan (not yours), and offers “Back to TermChamp’s pick”', { ids: v.ids.A, from, to });
    ok(await page.evaluate(() => !!JSON.parse(localStorage.getItem('tc-rec:' + TC.user.id + ':' + CFG.TERM) || '{}').A), 'rec: a swap stays on the phone for the term');
    await click(page, '#scroll [data-a="recReset"]'); await tick(page, 400);
    v = await st();
    ok(v.ids.A.includes(first) && !v.reset, 'rec: “Back to TermChamp’s pick” undoes the swaps', v.ids.A);
  } else ok(false, 'rec: the first class has something to swap for', sh);
  await page.evaluate(id => A.recDrop('A|' + id), first); await tick(page, 300);
  v = await st();
  ok(!v.ids.A.includes(first) && v.reset, 'rec: Take it out drops it from TermChamp’s plan', v.ids.A);
  await click(page, '#scroll [data-a="recReset"]'); await tick(page, 300);
  /* Set as Plan A, and Undo */
  v = await st();
  await click(page, '#scroll .plr-set'); await tick(page, 800);
  let pw = planWrites(log);
  ok(pw.length === 1 && pw[0].body.slot === 'A' && JSON.stringify(pw[0].body.sections.map(s => String(s.class_nbr))) === JSON.stringify(v.ids.A) && /This is your Plan A/.test(await page.locator('#scroll .plr').innerText()), 'rec: Set as Plan A writes your Plan A with TermChamp’s classes, and the card says it’s yours', pw.map(w => w.body.slot));
  await click(page, '#toast [data-a="toastUndo"]'); await tick(page, 800);
  ok(await page.evaluate(() => (TC.plans.A || []).length === 0), 'rec: Undo empties Plan A again');
  ok(log.errors.length === 0, 'rec: no page errors', log.errors);
  await close();
  /* a concentration line the report names no classes for: one of your concentration's electives, said so */
  const AE = { label: 'Approved Elective', status: 'not', kind: 'conc', ge: null, level: 'LN', code: 'R179-10', units: { req: 4, used: 0, need: 4 }, courses: null, options: [], oneOf: false };
  const T = Object.assign({}, NOPLANS(), { course_seats: FX.TABLES.course_seats.concat([{ term: '2268', course_code: 'BUS 4448', title: 'Mergers and Acquisitions', section: '01', instructor: 'Rastad, Ali', days: 'MoWe 10:10AM - 11:30AM', status: 'Open', capacity: 30, enrolled: 10, available: 20, waitlist_total: 0, waitlist_capacity: 0, class_nbr: '79448', instruction_mode: 'P', location: '' }]),
    profiles: FX.TABLES.profiles.map(p => p.id === FX.ME.id ? Object.assign({}, p, { major: 'Business Administration', concentration: 'Financial Management' }) : p),
    degree_audit: [{ user_id: FX.ME.id, printed_on: null, catalog: 'Fall Quarter 2023', major: 'BUS', concentration: 'Financial Management', units_used: 170, units_needed: 10, requirements: [AE], read_at: '2026-10-08T00:00:00Z' }] });
  const o = await openApp({ tables: T, height: 2000 });
  await toPlanner(o.page, true);
  await o.page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; render(true); }); await tick(o.page, 600);
  const s2 = await o.page.evaluate(() => ({ a: plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id].code), sugg: PL_CTX.R.sugg && PL_CTX.R.sugg.size, line: ((document.querySelector('#scroll .pll-line .pll-in') || {}).innerText || '') }));
  ok(s2.a.includes('BUS 4448') && s2.sugg === 1 && s2.line === 'Plan A · BUS 4448', 'rec: Approved Elective (no classes named) gets one of your concentration’s electives — BUS 4448', s2);
  await o.page.evaluate(() => { const id = Object.keys(SEC).find(i => SEC[i].code === 'BUS 4448'); A.recOpen('BUS 4448', id); }); await tick(o.page, 300);
  ok(/doesn’t name the classes for Approved Elective\. This one is from your concentration’s electives — check with your advisor/.test(await o.page.locator('#sheet').innerText()), 'rec: and its sheet says where it came from, and to check with your advisor');
  ok(o.log.errors.length === 0, 'rec (elective): no page errors', o.log.errors);
  await o.close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""")

# ---- second-pass re-aims
sub("const sk = await page.evaluate(() => ({ ask: !!document.querySelector('#scroll .cm-ask'), drafted: !!plDrafted().at, clear: !!document.querySelector('#scroll .pl-clear') }));\n  ok(!sk.ask && sk.drafted && !sk.clear, 'work: Skip — the plans draft, nothing to keep clear', sk);",
    "const sk = await page.evaluate(() => ({ ask: !!document.querySelector('#scroll .cm-ask'), drafted: document.querySelectorAll('#scroll .plr .pl-row').length > 0, clear: !!document.querySelector('#scroll .pl-clear') }));\n  ok(!sk.ask && sk.drafted && !sk.clear, 'work: Skip — TermChamp’s plan is worked out, nothing to keep clear', sk);", 'work skip')
sub("ok(a.any.some(x => /^BUS 4488 · time not posted$/.test(x))", "ok(a.any.some(x => /^BUS 4488 · (time not posted|online)$/.test(x))", 'cardA any regex')
sub("await page.evaluate(() => { recEditSet('B', plRecOf(PL_CTX.R, PL_CTX.L, 'A')); UI.plPlan = 'B'; render(true); }); await tick(page, 300);",
    "await page.evaluate(() => { render(true); recEditSet('B', plRecOf(PL_CTX.R, PL_CTX.L, 'A')); UI.plPlan = 'B'; render(true); }); await tick(page, 300);", 'bp same render')
sub("  await click(page, '[data-a=\"plPrefPick\"][data-x=\"friends\"]'); await click(page, '[data-a=\"plPrefPick\"][data-x=\"professors\"]');\n  re = await read();",
    "  await click(page, '[data-a=\"plPrefPick\"][data-x=\"friends\"]'); await click(page, '[data-a=\"plPrefPick\"][data-x=\"professors\"]'); await click(page, '[data-a=\"plPrefPick\"][data-x=\"friends\"]');\n  re = await read();", 'prefs retap')
# builderRec: give the first two picks a second section that fits, so B can differ and a class has somewhere to go
sub("  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.plPlan = 'A'; render(true); }); await tick(page, 600);\n  const st = () =>",
    "  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.plPlan = 'A'; render(true);\n    const codes = plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id].code).slice(0, 2); let nb = 99400; const frees = [{ days: 'F', s: 7 * 60, e: 7 * 60 + 50 }, { days: 'F', s: 18 * 60, e: 18 * 60 + 50 }];\n    codes.forEach((code, i) => { const base = secsOf(code)[0]; addSection(Object.assign({}, base, { id: String(nb++), sec: '09', days: frees[i].days, s: frees[i].s, e: frees[i].e, status: 'open', seats: 20 })); });\n    /* and a section of the first pick's class right over the second pick's: never a swap */\n    const over = plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id])[1]; if (over) addSection(Object.assign({}, secsOf(codes[0])[0], { id: '99499', sec: '10', days: over.days, s: over.s, e: over.e, status: 'open', seats: 20 })); render(true); }); await tick(page, 600);\n  const st = () =>", 'rec sections')
sub("ok(/Prerequisites didn’t load, so nothing was drafted and these picks don’t check them/.test(h.t) && h.card, 'rules: if they failed, the Planner says so — nothing drafted, picks unchecked'",
    "ok(/Prerequisites didn’t load, so TermChamp’s plan doesn’t check them/.test(h.t) && h.card, 'rules: if they failed, the Builder says TermChamp’s plan doesn’t check them'", 'rules prereq')
open(P, 'w', encoding='utf-8').write(S)

# ---- mutants: new ones, and the older ones whose code moved (re-aimed) or went (retired)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
IX = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("rec: no week", "const week = timed.length || TC.commits.length ? `<div class=\"plancol plan-${k} plr-wk\">", "const week = false ? `<div class=\"plancol plan-${k} plr-wk\">", "builderRec"),
  ("rec: B the same as A", "const A = plRecDraft(R, L, 'A', []), B = plRecDraft(R, L, 'B', [A]), C = plRecDraft(R, L, 'C', [A, B]);", "const A = plRecDraft(R, L, 'A', []), B = A, C = A;", "builderRec"),
  ("rec: what's left not first", "    const ord = q.cands.filter(c => !have.has(c.code)).sort(", "    const ord = [].sort(", "builderRec"),
  ("rec: swaps overlap", "const fits = x => x && x.id && SEC[x.id] && !around.some(t => secClash(x, t)) && !TC.commits.some(t => secClash(x, t));", "const fits = x => x && x.id && SEC[x.id];", "builderRec"),
  ("rec: swap ignored", "    recEditSet(k, ids.map(id => id === from ? to : id)); UI.sheet = null;", "    UI.sheet = null;", "builderRec"),
  ("rec: swaps not kept", "  try { const o = Object.assign({}, e); delete o._k; localStorage.setItem(RECK(), JSON.stringify(o)); } catch (x) {}", "", "builderRec"),
  ("rec: reset ignored", "  recReset: k => { recEditSet(k, null); render(true); },", "  recReset: k => { render(true); },", "builderRec"),
  ("rec: drop ignored", "    recEditSet(k, ids.filter(y => y !== id)); UI.sheet = null; render(true); },", "    UI.sheet = null; render(true); },", "builderRec"),
  ("rec: set writes nothing", "    TC.setPlan(k, ids); const d = plDrafted(); d.own = true; plDraftedSet(d);", "    const d = plDrafted(); d.own = true; plDraftedSet(d);", "builderRec"),
  ("rec: no undo", "toastUndo(`Plan ${k} is set — see it in Plans`, () => { TC.setPlan(k, before); render(true); });", "toast(`Plan ${k} is set — see it in Plans`);", "builderRec"),
  ("rec: never 'this is your plan'", "const mine = (TC.plans[k] || []).map(String), same = mine.length === ids.length && ids.every(id => mine.includes(String(id)));", "const mine = (TC.plans[k] || []).map(String), same = false;", "builderRec"),
  ("rec: no elective for an unnamed line", "  if (concE) auditOpen.filter(b => b.kind === 'conc'", "  if (false) auditOpen.filter(b => b.kind === 'conc'", "builderRec"),
  ("rec: suggestion unsaid", "  const sug = lines.some(b => R.sugg && R.sugg.has(b)) ?", "  const sug = false ?", "builderRec"),
  ("rec: set over plans that didn't load", "  const act = TC.err.plans ?", "  const act = false ?", "plannerNoDraft"),
  ("rec: drafted into Plans again", "  if (UI.plRefresh) { UI.plRefresh = false; }", "  if (UI.plRefresh) { UI.plRefresh = false; } if (plCanDraft()) plAutoDraft(R, L);", "plannerPrefs"),
  ("prefs: weights ignore the order", "const plWeights = () => { const p = prefOrder(); const w = {};", "const plWeights = () => { const p = PREF_ORDER[(TC.prefs && TC.prefs.priority) || 'degree']; const w = {};", "plannerPrefs"),
  ("prefs: last one not filled in", "if (rk.length === 2) rk.push(['degree', 'professors', 'friends'].find(x => !rk.includes(x)));", "", "plannerPrefs"),
  ("prefs: save before all three", "${UI.busy.prefs || !done ? 'disabled' : ''}", "${UI.busy.prefs ? 'disabled' : ''}", "plannerPrefs"),
  ("prefs: ranking not saved", "  if (!TC.prefsNoRank) row.ranking = order.join(',');", "", "plannerPrefs"),
  ("prefs: no RUN 19 fallback", "  if (q.error && row.ranking && /ranking/.test(q.error.message || '')) { TC.prefsNoRank = true;", "  if (false) { TC.prefsNoRank = true;", "plannerPrefs"),
  ("prefs: no order on the Builder", "${plUnitsTarget()} units · Edit</button></div>${rankRow}${plRegBanner()}", "${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}", "plannerPrefs"),
  ("builder: folded shows the full rows", "  const body = (open ? show.map(full)", "  const body = (true ? show.map(full)", "builderLeft"),
  ("plans: empty plan doesn't point to the Builder", "Set TermChamp’s Plan ${S.plan} from the Builder, or add classes from Explore.", "Add classes from Explore.", "plannerExistingPlan"),
]
for n, a, b, t in MUT:
    if IX.count(a) != 1: sys.exit(f'mutant anchor {n}: {IX.count(a)}x')
if 'edit-tests-builder-termchamp-plan-2026-10-12.py' not in T:
    k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
    if T.count(k) != 1: sys.exit('mutate anchor')
    T = T.replace(k, "\n  /* TermChamp's plans, what matters most ranked, the folded top card (2026-10-12; edit-tests-builder-termchamp-plan-2026-10-12.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
OLD = {
  "prefs: tapping an answer doesn't move it": ["prefs: tapping an answer doesn't move it", "const rk = sh.rank || prefOrder().slice(), i = rk.indexOf(k);", "const rk = prefOrder().slice(), i = rk.indexOf(k);", "plannerPrefs"],
  "prefs: a close button on the first ask": ["prefs: a close button on the first ask", "<h3>What matters most?</h3>${TC.prefs ? `<button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button>` : ''}", "<h3>What matters most?</h3><button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button>", "plannerPrefs"],
  "prefs: not kept on the phone": ["prefs: not kept on the phone", "  try { localStorage.setItem(PREFS_KEY(), JSON.stringify({ priority, units, order })); } catch (e) {}\n", "", "plannerPrefs"],
  "prefs: Edit pins the saved answer over a tap": ["prefs: Edit pins the saved answer over a tap", "  if (!sh.rank) sh.rank = prefOrder().slice();", "  sh.rank = prefOrder().slice();", "plannerPrefs"],
  "prefs: new answers don't re-draft": None,   # nothing re-drafts into Plans now
  "draft: drafted with no record and no report": ["draft: drafted with no record and no report", "${waiting ? cmWaitCard(k) : plRecCard(R, L, k, data ? '' : 'nodata')}", "${waiting ? cmWaitCard(k) : plRecCard(R, L, k, '')}", "plannerNoDraft"],
  "draft: drafted without prerequisites": ["draft: drafted without prerequisites", "Prerequisites didn’t load, so TermChamp’s plan doesn’t check them.", "", "plannerNoDraft"],
  "plan: the footnote doesn't say drafts are private": ["plan: the footnote doesn't say drafts are private", "Your plans change only when you set one, and are only yours until you share them. ", "", "plannerFromReport"],
  "card A: registration back in the sub line": ["card A: registration back in the sub line", "${rankRow}${plRegBanner()}", "${rankRow}", "springCardA"],
  "truth: the catalog line is missing": ["truth: the catalog line is missing", "  const catRow = X && TC.audit.catalog ?", "  const catRow = false ?", "dprStressQuarter", None],
  "builder: no same-as-A note": ["builder: no same-as-A note", "${likeA ? '<div class=\"pl-same\">Same as Plan A — these classes have no other section that fits.</div>' : ''}", "", "builderPlans", None],
  "work: the Builder drafts before asking": ["work: the Builder drafts before asking", "${waiting ? cmWaitCard(k) : plRecCard(", "${false ? cmWaitCard(k) : plRecCard(", "workActivities", None],
  "work: plans don't draw it": ["rec: your work isn't drawn", "blockAct: 'recOpen', H: 280, faces: true, extra: cmBlocks('me') })", "blockAct: 'recOpen', H: 280, faces: true, extra: [] })", "builderRec", None],
  "builder left: no card": ["builder left: no card", "  ${left}\n", "", "plannerPlan", None],
  "builder left: no options": ["builder left: lines don't name the plan's class", "${code ? `<span class=\"pll-in\">Plan ${k} · ${esc(code)}</span>` : ''}", "", "builderLeft", None],
  "builder left: worst first": ["builder left: the plan's lines not first", "  if (rec) { const has = q => recFor(q) ? 0 : 1; reqs.sort((a, b) => has(a) - has(b)); }", "", "builderLeft", None],
  "builder: no who line": ["builder: no who line", "${who}${catRow}<button class=\"pll-h\"", "${catRow}<button class=\"pll-h\"", "builderMerged"],
  "builder: no count": ["builder: no count", "</button>${num}<div class=\"pll-list\">", "</button><div class=\"pll-list\">", "builderMerged"],
  "builder: plain requirement rows": ["builder: plain requirement rows", "const full = q => q.b ? `<div class=\"pll-req\">${pcReqRow(q.b, X, L, idx.get(q.b))}</div>` : line(q);", "const full = q => line(q);", "builderMerged"],
  "builder: no in-progress toggle": None,   # the toggle is gone from the Builder (Tate 2026-10-12)
  "builder: no catalog line": ["builder: the catalog row loses its date", "from your report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span></div>", "from your report</span></div>", "builderMerged"],
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
print('edit-tests-builder-termchamp-plan: done')
