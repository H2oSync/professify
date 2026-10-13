#!/usr/bin/env python3
"""Tests for builder-2026-10-11.py. Usage: python3 edit-tests-builder-2026-10-11.py <repo-dir>"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", """
/* (2026-10-11) Tate: "change planner to be called builder … it just displays the recommended classes to take … recommended
   for plan A, vs B, C … no classes in a Plan that we recommend overlap but classes can be at different times in different
   plans … each Plan should be the best combination … but different" */
tests.builderPlans = async () => {
  const { page, close, log } = await openApp({ tables: NOPLANS(), height: 1500 });
  await toPlanner(page, true);
  const v = await page.evaluate(() => { const c = document.querySelector('#scroll .pl-card');
    return { tab: document.querySelector('.stabs .on').innerText.trim(), tabs: [...c.querySelectorAll('.pla-tab')].map(b => b.innerText.trim()), head: (c.querySelector('.pl-rech') || {}).innerText, sum: (c.querySelector('.pl-recs') || {}).innerText,
      grid: c.querySelectorAll('.pla-week, .pla-blk, .pla-any').length, rows: c.querySelectorAll('.pl-row').length, why: c.querySelectorAll('.pl-row .pl-why .pk-tag').length, words: document.getElementById('scroll').innerText }; });
  ok(v.tab === 'Builder' && !/Planner|Best fit|Backup/.test(v.words), 'builder: the tab reads Builder, and no “Planner”, “Best fit” or “Backup” on it', v.tab);
  ok(v.tabs.join('|') === 'Plan A|Plan B|Plan C' && v.head === 'Recommended for Plan A' && /units/.test(v.sum), 'builder: “Recommended for Plan A” with Plan A · Plan B · Plan C and a units line', v);
  ok(v.grid === 0 && v.rows > 0 && v.why > 0, 'builder: no week grid or Anytime strip — the recommended classes, each saying why it counts', v);
  /* three drafts with somewhere to switch to: give two of the picks a second section that fits, then draft A, B, C */
  const d = await page.evaluate(() => {
    plSync(); const L = TCPL.ledger(), R0 = planRank(L), codes = R0.all.slice(0, 2).map(c => c.code), s0 = Object.values(SEC)[0]; let nb = 99300;
    const free = { s: 7 * 60, e: 7 * 60 + 50 }, frees = [{ days: 'F', s: 7 * 60, e: 7 * 60 + 50 }, { days: 'F', s: 18 * 60, e: 18 * 60 + 50 }];
    codes.forEach((code, i) => { const base = secsOf(code)[0]; addSection(Object.assign({}, base, { id: String(nb++), sec: '09', days: frees[i].days, s: frees[i].s, e: frees[i].e, status: 'open', seats: 20 })); });
    /* a tempting section that overlaps the first pick's: the best-rated professor, at the same time — never drafted beside it */
    const top = Object.keys(PROFS).filter(p => ratingOf(p) != null).sort((x, y) => ratingOf(y) - ratingOf(x))[0], b0 = secsOf(codes[0])[0], b1 = secsOf(codes[1])[0];
    addSection(Object.assign({}, b1, { id: String(nb++), sec: '08', prof: top, days: b0.days, s: b0.s, e: b0.e, status: 'open', seats: 20 }));
    TC.plans.A = []; TC.plans.B = []; TC.plans.C = []; plDraftedSet({});
    const R = planRank(L); AT_PLANS.forEach(k => plDraftSlot(k, R, L));
    const P = k => (TC.plans[k] || []).map(id => SEC[id]).filter(Boolean);
    const clash = k => { const s = P(k); return s.some((a, i) => s.some((b, j) => j > i && secClash(a, b))); };
    const sec = (k, code) => (P(k).find(s => s.code === code) || {}).id;
    return { codes, clash: AT_PLANS.map(clash), a: codes.map(c => sec('A', c)), b: codes.map(c => sec('B', c)), n: AT_PLANS.map(k => P(k).length) };
  });
  ok(d.clash.every(x => !x) && d.n.every(n => n > 0), 'builder: every plan is drafted, and nothing inside a plan overlaps', d);
  ok(d.a.every(Boolean) && d.b.every(Boolean) && d.a.every((id, i) => String(id) !== String(d.b[i])), 'builder: a class with another section that fits is in a different section in Plan B — somewhere to switch to', d);
  /* the same goal: C isn't the friends-weighted draft any more; a pick already in A is ranked a touch lower, not dropped */
  const g = await page.evaluate(() => ({ cFr: String(planDraft).includes('friendsX'), same: (() => { plSync(); const L = TCPL.ledger(), R = planRank(L); const a = planDraft(R, 'A', L).ids, c = planDraft(R, 'C', L, [], [a]).ids; return a.length === c.length; })() }));
  ok(!g.cFr && g.same, 'builder: every plan has the same goal (no friends ×2.5 for C); C keeps as many classes as A', g);
  /* a plan with nothing else to switch to says so */
  await page.evaluate(() => { TC.plans.B = TC.plans.A.slice(); UI.plPlan = 'B'; render(true); }); await tick(page, 300);
  ok(/Same as Plan A/.test(await page.locator('#scroll .pl-card').innerText()), 'builder: a plan that came out the same as Plan A says no other section fits');
  ok(log.errors.length === 0, 'builder: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
import re
REAIMS = [
  ("""  ok(a.tabs.map(t => t[0]).join('|') === 'A · Best fit|B · Backup|C · Friends' && a.tabs[0][1] === 'true' && a.tabs.every(t => t[2] >= 44), 'card A: three named plan tabs, 44px, A selected', a.tabs);""",
   """  ok(a.tabs.map(t => t[0]).join('|') === 'Plan A|Plan B|Plan C' && a.tabs[0][1] === 'true' && a.tabs.every(t => t[2] >= 44), 'card A: Plan A · Plan B · Plan C tabs, 44px, A selected (the Builder: no Best fit / Backup / Friends)', a.tabs);"""),
  ("""  ok(a.blocks.length === a.want && a.blocks.length > 0 && a.blocks.every(b => /^\\d{4}[A-Z]?/.test(b)), 'card A: every weekday meeting is a labelled block on the week', { blocks: a.blocks, want: a.want });""",
   """  ok(a.blocks.length === 0 && /Recommended for Plan A/.test(a.text), 'card A: the Builder has no week — “Recommended for Plan A” and its classes (Tate, 2026-10-11)', { blocks: a.blocks });"""),
  ("""  ok(a.any.length === 1 && /^BUS 4488 · (time not posted|online)$/.test(a.any[0]), 'card A: a class with no set time is under Anytime', a.any);""",
   """  ok(a.any.length === 0 && a.rows.some(r => /BUS 4488/.test(r) && /Time not posted|Online/.test(r)), 'card A: a class with no set time is a row like the others, saying so', { any: a.any, rows: a.rows });"""),
  ("""  await page.locator('.pla-blk').first().click(); await tick(page, 400);
  ok(await page.evaluate(() => !!(UI.sheet && UI.sheet.type === 'sec')) || await page.locator('#sheet').count() > 0, 'card A: a block opens its section');""",
   """  await page.locator('.pl-card .pl-row').first().click(); await tick(page, 400);
  ok(await page.evaluate(() => !!(UI.sheet && UI.sheet.type === 'sec')) || await page.locator('#sheet').count() > 0, 'card A: a recommended class opens its section');"""),
  ("""  ok(ov.bl.length === 2 && (ov.bl[0][1] <= ov.bl[1][0] + 1 || ov.bl[1][1] <= ov.bl[0][0] + 1), 'card A: classes that overlap sit side by side, not on top of each other', ov.bl);
  ok(ov.ticks.length && !ov.ticks.some(x => /^12[ap]$/.test(x)), 'card A: a 9pm class’s week ends at midnight (no “12p” at the bottom)', ov.ticks);""",
   """  ok(ov.bl.length === 0 && !ov.ticks.length, 'card A: no week, so no blocks and no hours axis', ov);"""),
  ("""const mon = document.querySelectorAll('.pl-card .pla-col')[0], bl = [...mon.querySelectorAll('.pla-blk')]""", """const mon = document.querySelectorAll('.pl-card .pla-col')[0], bl = [...(mon ? mon.querySelectorAll('.pla-blk') : [])]"""),
  ("""  ok(tabs.join('|') === 'mine:My Classes|plans:Plans|planner:Planner|past:Past classes', 'tabs: My Classes · Plans · Planner · Past classes — Past classes furthest right (Tate, 2026-10-08)', tabs);""",
   """  ok(tabs.join('|') === 'mine:My Classes|plans:Plans|planner:Builder|past:Past classes', 'tabs: My Classes · Plans · Builder · Past classes — Past classes furthest right (Tate, 2026-10-08; Builder 2026-10-11)', tabs);"""),
  ("""  ok(await page.evaluate(() => PL_NAME.A === 'Best fit' && PL_NAME.B === 'Backup' && PL_NAME.C === 'Friends') && /A as your best fit, B as a backup/.test(HELPT.plans.t) && /C with more classes your friends take/.test(HELPT.plans.t), 'help: plans — A best fit, B backup, C friends, as the Plans screen names them'""",
   """  ok(await page.evaluate(() => PL_NAME.A === 'Plan A' && PL_NAME.B === 'Plan B' && PL_NAME.C === 'Plan C') && /Builder/.test(HELPT.plans.t) && /same thing/.test(HELPT.plans.t) && !/best fit|backup/i.test(HELPT.plans.t), 'help: plans — three plans with the same goal, built in the Builder'"""),
  ("""=== 'Planner', 'prereq: “Not fulfilled” opens Schedule › Planner');""", """=== 'Builder', 'prereq: “Not fulfilled” opens Schedule › Builder');"""),
  ("""t.indexOf('Before') < t.indexOf('Best fit') && t.indexOf('Before') < t.indexOf('More picks'), 'prereq: the card sits above the rest of the Planner""", """t.indexOf('Before') < t.indexOf('Plan A') && t.indexOf('Before') < t.indexOf('More picks'), 'prereq: the card sits above the rest of the Builder"""),
  ("""  ok(v.tabs === 'A · Best fit*|B · Backup|C · Friends', 'plan: Plan A “Best fit” with the A · B · C tabs in the card', v.tabs);""",
   """  ok(v.tabs === 'Plan A*|Plan B|Plan C', 'plan: Plan A with the Plan A · B · C tabs in the card', v.tabs);"""),
  ("""  ok(v.days === 'MON,TUE,WED,THU,FRI' && v.blocks > 0, 'plan: the week has day labels and a block per class meeting', v);""",
   """  ok(!v.days && v.blocks === 0, 'plan: the Builder card has no week (Plans shows the schedule)', v);"""),
  ("""  ok(b.on && b.on.trim() === 'B · Backup' && /plan-B/.test(b.cls)""", """  ok(b.on && b.on.trim() === 'Plan B' && /plan-B/.test(b.cls)"""),
  ("""/Your Planner builds everything from it/.test(d.t)""", """/The Builder works out everything from it/.test(d.t)"""),
]
def apply(S, sysx):
    for a, b in REAIMS:
        if S.count(a) != 1: sysx('builder reaim ' + a[:70] + f' {S.count(a)}x')
        S = S.replace(a, b)
    # the day-off column assertion (one long line) — the week is gone
    lines = S.split('\n'); idx = [i for i, l in enumerate(lines) if l.startswith("  ok(a.cols.length === 5 && a.off.length >= 1")]
    if len(idx) != 1: sysx('cols line')
    lines[idx[0]] = "  ok(a.cols.length === 0 && a.dh.length === 0, 'card A: no week columns on the Builder card', { cols: a.cols });"
    return '\n'.join(lines)

S = apply(S, sys.exit)
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("builder: the tab says Planner", "['planner', 'Builder']", "['planner', 'Planner']", "builderPlans", None),
  ("builder: B never moves to another section", "  const fresh = ss.filter(s => !(used || new Set()).has(String(s.id)) && !(regOpen() && s.status === 'full'));", "  const fresh = [];", "builderPlans", None),
  ("builder: a draft's sections may overlap", "const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id] && !(have || []).some(t => secClash(s, t)));", "const W = plWeights(), ss = secsOf(code).filter(s => s && s.id && SEC[s.id]);", "builderPlans", None),
  ("builder: B ignores A", "  const prev = AT_PLANS.slice(0, AT_PLANS.indexOf(k)).map(x => (TC.plans[x] || []).map(String));", "  const prev = [];", "builderPlans", None),
  ("builder: no heading", "<div class=\"pl-rech\">Recommended for Plan ${k}</div>", "", "builderPlans", None),
  ("builder: no same-as-A note", "<div class=\"pl-same\">Same as Plan A — these classes have no other section that fits.</div>", "", "builderPlans", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
T = T.replace(k, "\n  /* the Builder (2026-10-11; edit-tests-builder-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
# older mutants of code the Builder rewrote: re-aimed at the new words, or retired with what they guarded
BRETIRE = ["card A: no Anytime tray"]
_l = T.split('\n'); _k = [x for x in _l if not any(x.lstrip().startswith('[' + json.dumps(n, ensure_ascii=False) + ',') for n in BRETIRE)]
if len(_l) - len(_k) != len(BRETIRE): sys.exit('builder retire')
T = '\n'.join(_k)
BMREAIM = [
  (r'''"['plans', 'Plans'], ['planner', 'Planner'], ['past', 'Past classes']", "['plans', 'Plans'], ['past', 'Past classes'], ['planner', 'Planner']"''', r'''"['plans', 'Plans'], ['planner', 'Builder'], ['past', 'Past classes']", "['plans', 'Plans'], ['past', 'Past classes'], ['planner', 'Builder']"'''),
  (r'''"const PL_NAME = { A: 'Best fit', B: 'Backup', C: 'Friends' };", "const PL_NAME = { A: 'Best fit', B: 'Best fit', C: 'Friends' };"''', r'''"const PL_NAME = { A: 'Plan A', B: 'Plan B', C: 'Plan C' };", "const PL_NAME = { A: 'Plan A', B: 'Plan A', C: 'Plan C' };"'''),
  (r'''"${regOpen() ? ' · ' + secSeatText(x) : ''}</span></span>${right}", "${' · ' + secSeatText(x)}</span></span>${right}"''', r'''"${regOpen() ? ' · ' + secSeatText(x) : ''}</span>${why", "${' · ' + secSeatText(x)}</span>${why"'''),
  (r'''">${x} · ${PL_NAME[x]}</button>", ">${x}</button>"''', r'''">${PL_NAME[x]}</button>", ">${x}</button>"'''),
  (r'''"<div class=\"card pl-card pla plan-${k}\">${head}${week || tray ?", "<div class=\"card pl-card pla plan-${k}\">${head}<div class=\"pla-stats\"><div class=\"pla-stat\"><span>Classes</span><b>${st.n}</b></div></div>${week || tray ?"''', r'''"<div class=\"card pl-card pla plan-${k}\">${head}<div class=\"pl-rech\">", "<div class=\"card pl-card pla plan-${k}\">${head}<div class=\"pla-stats\"><div class=\"pla-stat\"><span>Classes</span><b>${st.n}</b></div></div><div class=\"pl-rech\">"'''),
]
for a, b in BMREAIM:
    if T.count(a) != 1: sys.exit('builder mreaim ' + a[:60] + f' {T.count(a)}x')
    T = T.replace(a, b)
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-builder: done')
