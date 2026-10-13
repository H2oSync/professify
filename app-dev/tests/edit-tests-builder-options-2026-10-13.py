#!/usr/bin/env python3
"""Tests for builder-options-2026-10-13.py. Run AFTER edit-tests-builder-termchamp-plan-2026-10-12.py.

The Builder shows what you should take and the best options under each (plain rows; the section sheet on tap). TermChamp's
Plan A/B/C card is gone, so the tests that read it are rewritten or re-aimed; `builderRec` is retired with the code.
Usage: python3 edit-tests-builder-options-2026-10-13.py <repo-dir>   (replayable)"""
import sys, os, json, re
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()

def sub(a, b, label):
    global S
    if b in S and a not in S: return
    if S.count(a) != 1: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
def func(name, body):
    global S
    head = f"tests.{name} = async () => {{"
    if S.count(head) != 1: sys.exit(f'func {name}: {S.count(head)}x')
    i = S.index(head); j = S.index("\n};\n", i) + 4
    if body.strip() in S[i:j]: return
    S = S[:i] + body.strip() + "\n" + S[j:]
def drop(name):
    global S
    head = f"tests.{name} = async () => {{"
    if S.count(head) != 1: return
    i = S.index(head); j = S.index("\n};\n", i) + 4
    k = S.rfind("\n/*", 0, i)   # the comment block right above it, if it is the last thing before
    if k >= 0 and S[k:i].count('*/') == 1 and S[k:i].strip().endswith('*/'): i = k + 1
    S = S[:i] + S[j:]

drop('builderRec')

# ---- the top-card helper (LC): no 'open' flag any more
# the helper is inlined in many places: replace all; it hands back the whole Builder (top card + the requirement cards)
_a = "const o2 = UI.plLeftOpen2; UI.plLeftOpen2 = true; d.innerHTML = plLeftCard(R, L, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A'); UI.plLeftOpen2 = o2; document.body.appendChild(d); return d.firstElementChild;"
_b = "const ro = UI.plReqOpen; UI.plReqOpen = new Proxy({}, { get: () => true, has: () => true }); try { d.innerHTML = plLeftCard(R, L, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A'); } finally { UI.plReqOpen = ro; } document.body.appendChild(d); const c0 = d.firstElementChild; if (c0) [...d.children].slice(1).forEach(x => c0.appendChild(x)); return c0;"
if _a in S: S = S.replace(_a, _b)
elif _b not in S: sys.exit('LC: anchor missing')
# pcRows: the top card's rows live in .plq-card now (unknown lines)
sub("[...document.querySelectorAll('#scroll .pll .pc-row')]", "[...document.querySelectorAll('#scroll .pll .pc-row, #scroll .plq-card .pc-row')]", 'pcRows plq')
sub("still: !!r.closest('.pc-still, .pc-lrows, .pll') })).concat(", "still: !!r.closest('.pc-still, .pc-lrows, .pll, .plq-card') })).concat(", 'pcRows still')
sub("const pcRows = page => page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row')].filter(r => !r.closest('.pll')).concat(document.querySelector('#scroll .pll') ?",
    "const pcRows = page => page.evaluate(() => [...document.querySelectorAll('#scroll .pc-row')].filter(r => !r.closest('.pll, .plq-card')).concat(document.querySelector('#scroll .pll') ?", 'pcRows filter')

# ---- dprStressNoMajor: the requirement cards sit under the top card now; no options to pick from
sub("  await page.evaluate(() => { UI.plLeftOpen2 = true; render(true); }); await tick(page, 300);\n", "", 'nomajor open2')
sub("rows: c.querySelectorAll('.pll-req .pc-row').length, opts: c.querySelectorAll('.pll-opt, .pll-none').length };",
    "rows: document.querySelectorAll('#scroll .plq-card').length, opts: document.querySelectorAll('#scroll .plo').length };", 'nomajor rows')

# ---- plannerRules: the requirement cards stand where the plan card was
sub("card: !!document.querySelector('#scroll .pl-card') })); };\n  let h = await hero(undefined);", "card: !!document.querySelector('#scroll .plq-card') })); };\n  let h = await hero(undefined);", 'rules card')

# ---- every requirement open, for tests that read all the options
sub("const pcRows = page => ", "const openReqs = page => page.evaluate(() => { for (let i = 0; i < 40; i++) { const b = document.querySelector('#scroll .plq[aria-expanded=\"false\"]'); if (!b) break; b.click(); } });\nconst pcRows = page => ", 'openReqs')
sub("  await toPlanner(page);\n  const v = await page.evaluate(() => { const sc = document.getElementById('scroll'), L = TCPL.ledger(), R = planRank(L);\n    return { audit: R.audit, left: R.left,",
    "  await toPlanner(page); await openReqs(page);\n  const v = await page.evaluate(() => { const sc = document.getElementById('scroll'), L = TCPL.ledger(), R = planRank(L);\n    return { audit: R.audit, left: R.left,", 'fromReport open')

# ---- workActivities: the options show under the ask (no waiting card any more)
sub("ok(a0.ask && a0.wait && !a0.drafted && a0.plans === '0,0,0', 'work: before Plans A, B and C first draft, the Builder asks about work and practice — nothing drafts yet', a0);",
    "ok(a0.ask && a0.above && !a0.wait && !a0.drafted && a0.plans === '0,0,0', 'work: the Builder asks about work and practice above the options (they depend on it); nothing is drafted into Plans', a0);", 'work ask')
sub("const a0 = await page.evaluate(() => ({ ask: !!document.querySelector('#scroll .cm-ask'), wait:",
    "const a0 = await page.evaluate(() => ({ ask: !!document.querySelector('#scroll .cm-ask'), above: (() => { const a = document.querySelector('#scroll .cm-ask'), l = document.querySelector('#scroll .plq-list'); return !!(a && l && (a.compareDocumentPosition(l) & 4)); })(), wait:", 'work above')

# ---- newMajors: the count and the flowchart's classes are in the Builder now (pre-existing since 03:20)
sub("  const t = await text(page);\n  const eemL =", "  const t = await withLeft(page);\n  const eemL =", 'majors eem')
sub("  const t2 = await text(o.page);\n  const itpL =", "  const t2 = await withLeft(o.page);\n  const itpL =", 'majors itp')

# ---- the plan card is gone from the Builder: the tests that looked for it look for the requirement cards
sub("tiles: document.querySelectorAll('#scroll .pl-card .pla-stat, #scroll .pl-card .pla-stats').length, card: !!document.querySelector('#scroll .pl-card.pla') };",
    "tiles: document.querySelectorAll('#scroll .pl-card .pla-stat, #scroll .pl-card .pla-stats').length, card: !!document.querySelector('#scroll .plq-card') };", 'regday card')
sub("'regday: the plan card has no Classes · Professors · Day off tiles (Tate: “take out this”)'", "'regday: the Builder has no Classes · Professors · Day off tiles (Tate: “take out this”) — the requirement cards'", 'regday msg')
sub("rows: [...sc.querySelectorAll('.pl-card .pl-row .pl-m')].map(r => r.innerText), seat: R.all.map(c => c.parts.seat),",
    "rows: [...sc.querySelectorAll('.plq-card .plo')].map(r => r.innerText), seat: R.all.map(c => c.parts.seat),", 'regopen rows')
sub("ok(v.rows.length && v.rows.every(r => /seats|Waitlist|Full|open/i.test(r)) && v.seat.some(s => s > 0), 'reg: in session, every plan row carries its seats and Seats counts in the score', v);",
    "ok(v.rows.length && v.rows.every(r => !/seats|Waitlist/i.test(r)) && v.seat.some(s => s > 0), 'reg: in session, Seats counts in the score; the option rows stay plain (seats are on the tap)', v);", 'regopen seats')
sub("seats: /\\d+ seats/.test(document.querySelector('#scroll .pl-card').innerText) }));", "seats: /\\d+ seats/.test((document.querySelector('#scroll .plq-list') || {}).innerText || '') }));", 'regopen card')
sub("const pl = await f.page.evaluate(() => ({ dpr: !!document.querySelector('#scroll .tc-dpr'), card: !!document.querySelector('#scroll .pl-card') }));\n  ok(!pl.dpr && pl.card, 'onboarding: a first-year’s Planner goes straight to the drafted plan', pl);",
    "const pl = await f.page.evaluate(() => ({ dpr: !!document.querySelector('#scroll .tc-dpr'), card: !!document.querySelector('#scroll .plq-card') }));\n  ok(!pl.dpr && pl.card, 'onboarding: a first-year’s Builder goes straight to what to take', pl);", 'onb card')
sub("t.indexOf('Before') < t.indexOf('Plan A') && t.indexOf('Before') < t.indexOf('left on your flowchart'), 'prereq: the card sits above the rest of the Builder (the plan and the picks)'",
    "t.indexOf('Before') < t.indexOf('left on your flowchart'), 'prereq: the card sits above the rest of the Builder'", 'prereq above')
sub("/left on your flowchart/.test(await text(page)) && await page.locator('#scroll .pl-card').count() === 1, 'prereq: the card closes and the Builder stays');",
    "/left on your flowchart/.test(await text(page)) && await page.locator('#scroll .plq-card').count() > 0, 'prereq: the card closes and the Builder stays');", 'prereq stays')
sub("{ plan: '.pl-card', left: '.pll', top: '.pl-top' });\n    ok(at(pl, 'plan', 12) && at(pl, 'left', 12) && pl.top[0][0] === 16, `page width ${w}: Builder — what’s left and the plan card are 12px from the edge, the heading 16`, pl);",
    "{ plan: '.plq-card', left: '.pll', top: '.pl-top' });\n    ok(at(pl, 'plan', 12) && at(pl, 'left', 12) && pl.top[0][0] === 16, `page width ${w}: Builder — what’s left and the requirement cards are 12px from the edge, the heading 16`, pl);", 'width builder')

# ---- plannerRegOpen: before registration, Seats counts for nothing in the score
sub("open: regOpen(), seats: /\\d+ seats/.test((document.querySelector('#scroll .plq-list') || {}).innerText || '') }));\n  ok(!v.open && /Opens Oct 19/.test(v.top) && !v.seats, 'reg: planning the term registration is for, before Oct 19 — the line shows and seats don’t', v);",
    "open: regOpen(), seat0: planRank(TCPL.ledger()).all.every(c => !c.parts.seat), seats: /\\d+ seats/.test((document.querySelector('#scroll .plq-list') || {}).innerText || '') }));\n  ok(!v.open && /Opens Oct 19/.test(v.top) && !v.seats && v.seat0, 'reg: planning the term registration is for, before Oct 19 — the line shows, seats don’t, and Seats counts for nothing', v);", 'regopen seat0')

# ---- plannerPrefs: the Builder shows the options, not a plan
sub("rec: sc.querySelectorAll('.plr .pl-row').length, w: plWeights()", "rec: sc.querySelectorAll('.plq-card .plo').length, w: plWeights()", 'prefs rec')
sub("'prefs: the Builder shows your order and the units, then TermChamp’s plan; the order is also kept on the phone'", "'prefs: the Builder shows your order and the units, then the options; the order is also kept on the phone'", 'prefs msg')

# ---- plannerRules
sub("ok(/Prerequisites didn’t load, so TermChamp’s plan doesn’t check them/.test(h.t) && h.card, 'rules: if they failed, the Builder says TermChamp’s plan doesn’t check them'",
    "ok(/Prerequisites didn’t load, so these options don’t check them/.test(h.t) && h.card, 'rules: if they failed, the Builder says the options don’t check them'", 'rules note')

# ---- plannerFromReport: the options under the lines
sub("planA: plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id].code)", "planA: [...document.querySelectorAll('#scroll .plq-card .plo')].map(e => e.dataset.x)", 'fromReport opts')
sub("ok(v.planA.includes('BUS 3346') && !v.planA.includes('BUS 3387') && v.planA.filter(c => c === 'BUS 4401' || c === 'STAT 2170').length === 1, 'report: Plan A takes the required class and ONE of the pick-1 options (BUS 4401 clears both lines it’s on, so STAT 2170 isn’t added beside it), never the satisfied one', v.planA);",
    "ok(v.planA.includes('BUS 3346') && !v.planA.includes('BUS 3387') && v.planA.includes('BUS 4401'), 'report: the options under the lines are the required class and the pick-1 options, never the satisfied one', v.planA);", 'fromReport check')
sub("/Your plans change only when you set one, and are only yours until you share them/.test(v.note), 'report: the footnote says the picks come from the report, that plans change only when set, and are private'",
    "/Your plans change only when you add a class, and are only yours until you share them/.test(v.note), 'report: the footnote says the picks come from the report, that plans change only when you add, and are private'", 'fromReport note')

# ---- workActivities: the options never over the shift; Clear of your work on the top card
sub("const d = await page.evaluate(() => { const P = k => plRecOf(PL_CTX.R, PL_CTX.L, k).map(id => SEC[id]).filter(Boolean);\n    return { drafted: !(TC.plans.A || []).length, n: AT_PLANS.map(k => P(k).length), clash: AT_PLANS.some(k => P(k).some(s => TC.commits.some(c => secClash(s, c)))), ask:",
    "const d = await page.evaluate(() => { const P = k => [...document.querySelectorAll('#scroll .plo:not(.plo-no)')].map(e => SEC[e.dataset.y]).filter(Boolean);\n    return { drafted: !(TC.plans.A || []).length, n: AT_PLANS.map(k => P(k).length), clash: AT_PLANS.some(k => P(k).some(s => TC.commits.some(c => secClash(s, c)))), ask:", 'work d')
sub("'work: then TermChamp’s Plans A, B and C are worked out — none over the shift (and nothing is written into your plans)'", "'work: then the options show, each in a section that isn’t over the shift (and nothing is written into your plans)'", 'work d msg')
sub("const s0 = await page.evaluate(() => { const s = plRecOf(PL_CTX.R, PL_CTX.L, 'A').map(id => SEC[id]).find(x => x && x.s != null && !x.async); return s && { days: s.days, s: s.s, e: s.e }; });",
    "const s0 = await page.evaluate(() => { const s = [...document.querySelectorAll('#scroll .plo:not(.plo-no)')].map(e => SEC[e.dataset.y]).find(x => x && x.s != null && !x.async); return s && { days: s.days, s: s.s, e: s.e }; });", 'work s0')
sub("clash: AT_PLANS.some(k => plRecOf(PL_CTX.R, PL_CTX.L, k).map(id => SEC[id]).filter(Boolean).some(s => TC.commits.some(c => secClash(s, c)))), clear:",
    "clash: [...document.querySelectorAll('#scroll .plo:not(.plo-no)')].map(e => SEC[e.dataset.y]).filter(Boolean).some(s => TC.commits.some(c => secClash(s, c))), clear:", 'work rd')
sub("'work: a new one over a class in TermChamp’s plan — the plans are worked out around it (“Clear of your work and practice”)'", "'work: a new one over an option’s section — the options move to sections around it (“Clear of your work and practice”)'", 'work rd msg')
sub("drafted: document.querySelectorAll('#scroll .plr .pl-row').length > 0, clear: !!document.querySelector('#scroll .pl-clear') }));\n  ok(!sk.ask && sk.drafted && !sk.clear, 'work: Skip — TermChamp’s plan is worked out, nothing to keep clear', sk);",
    "drafted: document.querySelectorAll('#scroll .plq-card .plo').length > 0, clear: !!document.querySelector('#scroll .pl-clear') }));\n  ok(!sk.ask && sk.drafted && !sk.clear, 'work: Skip — the options show, nothing to keep clear', sk);", 'work skip')

# ---- builderMerged: the options follow the top card
sub("rec: !!(c.compareDocumentPosition(document.querySelector('#scroll .plr')) & Node.DOCUMENT_POSITION_FOLLOWING) }; });",
    "rec: !!(c.compareDocumentPosition(document.querySelector('#scroll .plq-list')) & Node.DOCUMENT_POSITION_FOLLOWING) }; });", 'merged rec')
sub("lines: [...c.querySelectorAll('.pll-line')].map(e => t(e)), rows: [...c.querySelectorAll('.pll-req .pc-row')].map(q => ({ row: t(q.querySelector('.pc-main')), mark: !!q.querySelector('[data-a=\"plMarkAsk\"]') })), opts: c.querySelectorAll('.pll-opt').length,",
    "lines: [...document.querySelectorAll('#scroll .plq')].map(e => t(e.querySelector('.plq-t b'))), rows: [...document.querySelectorAll('#scroll .plq-card.open')].map(q => ({ row: t(q.querySelector('.plq-t b')), mark: !!q.querySelector('[data-a=\"plMarkAsk\"]') })), opts: document.querySelectorAll('#scroll .plq-card .plo').length,", 'merged lines')
sub("ok(b && b.lines.length === 1 && /^Career Readiness III/.test(b.lines[0]) && !b.rows.length && !b.opts && !b.ip && !b.foot && !b.go, 'builder: folded, each requirement is one line; no options, no in-progress row, no catalog footnote, no “Best options” button', b && { lines: b.lines, rows: b.rows.length, opts: b.opts, ip: b.ip });\n  await click(page, '#scroll .pll-h'); await tick(page, 300);\n  b = await rd();\n  ok(b.rows.length === 1 && b.rows[0].mark && /Career Readiness III/.test(b.rows[0].row), 'builder: a tap opens each line in full, with Mark done', b.rows);\n  await click(page, '#scroll .pll-h'); await tick(page, 300);",
    "ok(b && b.lines.length === 1 && /^Career Readiness III/.test(b.lines[0]) && b.rows.length === 1 && b.rows[0].mark && !b.ip && !b.foot && !b.go, 'builder: each requirement is a card (the first open, with Mark done); no in-progress row, no catalog footnote, no “Best options” button', b && { lines: b.lines, rows: b.rows.length, ip: b.ip });", 'merged open')

# ---- rewritten whole
func('plannerNoDraft', r"""
tests.plannerNoDraft = async () => {
  /* 1. the plans read fails: the Builder still shows what you should take and the options; nothing is written */
  let failPlans = true;
  const hook = (url, m) => { if (failPlans && m === 'GET' && /\/rest\/v1\/plans$/.test(url.pathname) && /user_id=eq\./.test(url.search)) return { status: 500, body: JSON.stringify({ message: 'fixture: plans read failed', code: 'XX000' }) }; };
  let o = await openApp({ tables: NOPLANS(), hook });
  await toPlanner(o.page);
  const rd = p => p.evaluate(() => ({ err: TC.err.plans, loaded: TC.plansLoaded, rows: document.querySelectorAll('#scroll .plq-card .plo').length, cards: document.querySelectorAll('#scroll .plq-card').length, nudge: !!document.querySelector('#scroll .tc-dpr-row'), pre: UI.pl && UI.pl.prereqs, all: document.getElementById('scroll').innerText }));
  let v = await rd(o.page);
  ok(v.err && !v.loaded && v.cards > 0 && v.rows > 0 && !o.log.writes.some(w => w.table === 'plans'), 'no draft: when the plans don’t load, the Builder still shows the requirements and their options, and nothing is written', { err: v.err, cards: v.cards, rows: v.rows });
  ok(o.log.errors.length === 0, 'no draft (plans): no page errors', o.log.errors);
  await o.close();
  /* 2. no record and no report (the student skipped the upload): the flowchart's Year 1, and the nudge */
  o = await openApp({ tables: NOREC() });
  await toPlanner(o.page);
  await click(o.page, '.tc-dpr [data-a="plShowPicks"]'); await tick(o.page, 1500);
  v = await rd(o.page);
  ok(v.nudge && v.cards > 0 && planWrites(o.log).length === 0, 'no draft: with no past classes and no report, the flowchart’s requirements show with the report nudge — nothing is written', { nudge: v.nudge, cards: v.cards, writes: planWrites(o.log).length });
  await uploadDpr(o.page, '.tc-dpr-row input[data-in="dprfile"]'); await click(o.page, '[data-a="dprSave"]'); await tick(o.page, 3000);
  await o.page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.sheet = null; S.schedTab = 'planner'; render(true); }); await tick(o.page, 1500);
  v = await rd(o.page);
  ok(v.cards > 0 && planWrites(o.log).length === 0, 'no draft: after the report, the requirements are the report’s — and still nothing is written into Plans', { cards: v.cards, writes: planWrites(o.log).map(w => w.body.slot) });
  ok(o.log.errors.length === 0, 'no draft (no data): no page errors', o.log.errors);
  await o.close();
  /* 3. prerequisites failed to load: the options say they don't check them */
  o = await openApp({ tables: NOPLANS(), hook: (url, m) => m === 'GET' && /\/rest\/v1\/course_prereqs$/.test(url.pathname) ? { status: 500, body: JSON.stringify({ message: 'fixture: prereqs failed', code: 'XX000' }) } : null });
  await toPlanner(o.page);
  v = await rd(o.page);
  ok(v.pre === false && planWrites(o.log).length === 0 && /Prerequisites didn’t load, so these options don’t check them/.test(v.all), 'no draft: without prerequisites, the Builder says the options don’t check them; nothing is written', { pre: v.pre, writes: planWrites(o.log).length });
  await o.close();
};
""")

func('plannerRefresh', r"""
tests.plannerRefresh = async () => {
  const { page, close, log } = await openApp({ tables: NOPLANS() });
  await toPlanner(page);
  const opts = () => page.evaluate(() => ({ audit: !!(planRank(TCPL.ledger()).audit), a: [...document.querySelectorAll('#scroll .plq-card .plo')].map(e => e.dataset.x) }));
  const r0 = await opts();
  ok(!r0.audit && r0.a.length > 0 && planWrites(log).length === 0, 'refresh: the options come from the record, and nothing is written into Plans', r0);
  /* the student puts a class into Plan C by hand: it's theirs, and it gets a seat alert */
  const own = await page.evaluate(() => { const s = Object.values(SEC).find(x => x && x.code && x.s != null && !TC.watches[x.id]); TC.setPlan('C', [String(s.id)]); return String(s.id); });
  await tick(page, 800);
  const w = log.writes.filter(x => x.table === 'watch_sections').map(x => x.body && x.body.class_nbr);
  ok(w.length === 1 && w[0] === own, 'refresh: a class the student adds by hand gets its seat alert', w);
  const c = await page.evaluate(() => TC.plans.C.slice()), n0 = planWrites(log).length;
  await page.evaluate(() => { S.schedTab = 'past'; render(); }); await tick(page, 800);
  await uploadDpr(page); await click(page, '[data-a="dprSave"]'); await tick(page, 3000);
  await page.evaluate(() => { UI.sheet = null; S.schedTab = 'planner'; render(true); }); await tick(page, 1500);
  const r1 = await opts(), c2 = await page.evaluate(() => TC.plans.C.slice());
  ok(r1.audit && r1.a.length > 0 && planWrites(log).length === n0 && JSON.stringify(c2) === JSON.stringify(c), 'refresh: after the report, the requirements and options are the report’s; Plan C stays exactly as the student made it', { r1, c, c2, writes: planWrites(log).length - n0 });
  ok(log.errors.length === 0, 'refresh: no page errors', log.errors);
  await close();
};
""")

func('plannerExistingPlan', r"""
tests.plannerExistingPlan = async () => {
  const { page, close, log } = await openApp({});   /* the fixture's ME has sections in Plan B */
  await toPlanner(page);
  const B0 = await page.evaluate(() => TC.plans.B.map(String));
  ok(!log.writes.some(w => w.table === 'plans') && B0.length > 0 && await page.locator('#scroll .plr, #scroll .pl-card').count() === 0, 'existing: the Builder writes nothing into the plans on the account, and shows no plan card', B0);
  /* a class in the Builder opens the section sheet with Add to a plan; the Add sheet puts it in a plan */
  const first = await page.evaluate(() => { const e = document.querySelector('#scroll .plo'); return e && { code: e.dataset.x, id: e.dataset.y }; });
  await click(page, '#scroll .plo'); await tick(page, 400);
  const sh = await page.evaluate(() => ({ type: UI.sheet && UI.sheet.type, add: !!document.querySelector('#sheet [data-a="addPlanSheet"]') }));
  ok(sh.type === 'sec' && sh.add, 'existing: a tap opens the section sheet with Add to a plan', sh);
  await click(page, '#sheet [data-a="addPlanSheet"]'); await tick(page, 400);
  ok(await page.evaluate(id => UI.sheet && UI.sheet.type === 'addTo' && String(UI.sheet.id) === String(id), first.id), 'existing: Add to a plan opens the Add sheet on that section', first);
  await page.evaluate(() => { UI.sheet = null; render(true); });
  /* Plans: an empty plan points to the Builder */
  await page.evaluate(() => { TC.commits = []; S.schedTab = 'plans'; S.plan = 'C'; render(true); }); await tick(page, 400);
  const e = await page.evaluate(() => ({ t: (document.querySelector('#scroll .empty') || {}).innerText || '', btn: !!document.querySelector('#scroll .empty [data-a="schedTab"][data-x="planner"]') }));
  ok(/Nothing in Plan C yet/.test(e.t) && /Add classes from the Builder or Explore/.test(e.t) && e.btn, 'existing: an empty plan in Plans points to the Builder', e);
  ok(log.errors.length === 0, 'existing: no page errors', log.errors);
  await close();
};
""")

func('builderLeft', r"""
tests.builderLeft = async () => {
  const { page, close, log } = await openApp({ height: 1600 });
  await toPlanner(page, true);
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; UI.plPlan = 'A'; render(true); }); await tick(page, 400);
  const read = () => page.evaluate(() => { const c = document.querySelector('#scroll .pll'); if (!c) return null; plSync(); const L = TCPL.ledger(), R = planRank(L);
    return { h: c.querySelector('.pll-h').innerText.replace(/\s+/g, ' ').trim(), n: L.need.length + L.needU.length, first: !!(c.compareDocumentPosition(document.querySelector('#scroll .plq-list')) & Node.DOCUMENT_POSITION_FOLLOWING),
      cards: [...document.querySelectorAll('#scroll .plq-card')].map(q => ({ open: q.classList.contains('open'), label: q.querySelector('.plq-t b').childNodes[0].textContent.trim(), sub: q.querySelector('.plq-t > span').innerText, opts: [...q.querySelectorAll('.plo')].map(o => ({ code: o.dataset.x, id: o.dataset.y, n: o.querySelector('.plo-n').innerText, c: o.querySelector('.plo-c').innerText, p: o.querySelector('.plo-p').innerText, no: o.classList.contains('plo-no') })), more: (q.querySelector('.plq-more') || {}).innerText || '', mark: !!q.querySelector('.plq-mark'), plus: q.querySelectorAll('.pll-add, .plus').length })),
      order: R.all.map(x => x.code), all: !!document.querySelector('#scroll .pll-all'), picks: document.querySelectorAll('#scroll .pl-picks, #scroll .plr, #scroll .pl-card').length }; });
  let v = await read();
  ok(v && v.h === `${v.n} left on your flowchart` && v.first && !v.picks, 'builder: opens with what’s left (the flowchart’s count), then the requirement cards; no plan card', v && { h: v.h, n: v.n, first: v.first, picks: v.picks });
  ok(v.cards.length === Math.min(6, v.n) && (v.n > 6 ? v.all : !v.all) && v.cards[0].open && v.cards.slice(1).every(q => !q.open), 'builder: six requirement cards (All N for the rest); the first starts open, the rest folded', { cards: v.cards.length, n: v.n, open: v.cards.map(q => q.open) });
  const q0 = v.cards[0];
  ok(q0.opts.length >= 1 && q0.opts.length <= 3 && q0.opts.every(o => /^[A-Z]{2,5} \d{4}/.test(o.code) && o.n && o.c === o.code && o.p) && q0.plus === 0 && !/★|seats|Open|Mon|Tue|Wed|Thu|Fri/.test(q0.opts.map(o => o.n + o.c + o.p).join('')), 'builder: plain rows — the name, the number under it, the professor’s last name — no +, no rating, time or seats', q0.opts);
  const codes = q0.opts.filter(o => !o.no).map(o => o.code);
  ok(JSON.stringify(codes) === JSON.stringify(v.order.filter(c => codes.includes(c))), 'builder: options in the Builder’s own order (your priorities)', { codes, order: v.order.slice(0, 12) });
  ok(await page.evaluate(ids => ids.every(id => { const s = SEC[id]; return s && !planSecsOf('A').some(t => t.code !== s.code && secClash(s, t)) && !TC.commits.some(t => secClash(s, t)); }), q0.opts.filter(o => !o.no).map(o => o.id)), 'builder: every option’s section fits — no clash with Plan A or your work');
  ok(v.cards.slice(1).every(q => /offered this|nothing offered/.test(q.sub)), 'builder: a folded requirement says how many are offered (and the best professor when rated)', v.cards.slice(1).map(q => q.sub));
  /* open another; See all; fold */
  await click(page, '#scroll .plq-card:nth-child(2) .plq'); await tick(page, 300);
  v = await read();
  ok(v.cards[1].open && v.cards[0].open, 'builder: a tap opens a second requirement under the first (both stay open)', v.cards.map(q => q.open));
  const big = v.cards.find(q => q.open && /^See all \d+$/.test(q.more));
  if (big) {
    await click(page, `#scroll .plq-card:nth-child(${v.cards.indexOf(big) + 1}) .plq-more`); await tick(page, 300);
    const v2 = await read(), q = v2.cards[v.cards.indexOf(big)];
    ok(q.opts.length > 3 && q.more === 'Show top 3', 'builder: See all N lists every option, and offers Show top 3', { n: q.opts.length, more: q.more });
  } else ok(true, 'builder: (no requirement with more than 3 options in this fixture)');
  await click(page, '#scroll .plq-card:nth-child(1) .plq'); await tick(page, 300);
  v = await read();
  ok(!v.cards[0].open, 'builder: a tap on an open requirement folds it', v.cards[0].open);
  /* a Plan A class over an option's only section: the option says so, dimmed */
  const cl = await page.evaluate(() => {
    plSync(); const R = planRank(TCPL.ledger());
    const c = R.all.find(x => !x.inPlan && secsOf(x.code).length && secsOf(x.code).every(s => s.s != null)); if (!c) return null;
    const ss = secsOf(c.code), other = SECTIONS.find(s => s.code !== c.code && s.s != null && ss.every(t => secClash(s, t)) && !R.all.some(x => x.code === s.code));
    if (!other) return { code: c.code, none: true };
    TC.plans.A = [other.id]; UI.plReqOpen = null; UI.plLeftAll = true; render(true);
    document.querySelectorAll('#scroll .plq-card:not(.open) .plq').forEach(b => A.plReqOpen(b.dataset.x));
    document.querySelectorAll('#scroll .plq-more').forEach(b => A.plLeftOpen(b.dataset.x));
    const o = [...document.querySelectorAll('#scroll .plo')].find(e => e.dataset.x === c.code);
    return { code: c.code, other: other.code, no: !!o && o.classList.contains('plo-no'), c: o ? o.querySelector('.plo-c').innerText : null };
  });
  ok(cl && cl.no && /every section clashes with Plan A or your week$/.test(cl.c), 'builder: an option whose every section clashes with Plan A says so, dimmed', cl);
  ok(log.errors.length === 0, 'builder left: no page errors', log.errors);
  await close();
};
""")

func('plannerPlan', r"""
tests.plannerPlan = async () => {
  const { page, close, log } = await openApp({ tables: NOPLANS() });
  await toPlanner(page, true);
  const v = await page.evaluate(() => { const sc = document.getElementById('scroll');
    return { top: (sc.querySelector('.pl-top') || {}).innerText, reg: (sc.querySelector('.pla-reg') || {}).innerText || '', card: sc.querySelectorAll('.pl-card, .plr').length, cards: sc.querySelectorAll('.plq-card').length,
      score: !!sc.querySelector('.pk-n, .bar, .pk-score'), behind: /Behind/.test(sc.innerText), seats: /\d+ seats/.test(sc.innerText), ledger: !!sc.querySelector('.tc-lrow, .pc-sum'), old: !!sc.querySelector('.pk-hero'), sech: [...sc.querySelectorAll('.pl-sech')].map(s => s.innerText.replace(/\s+/g, ' ').trim()) }; });
  const pll = await pllH(page);
  ok(/Fall 2026/.test(v.top) && !/left|Registration/.test(v.top) && /16 units · Edit/.test(v.top) && /^Opens Oct 19/.test(v.reg.trim()) && /^\d+ left on your flowchart$/.test(pll), 'plan: the top is the term and the units pill; registration’s date is its own line; then what’s left', { top: v.top, reg: v.reg, pll });
  ok(v.card === 0 && v.cards > 0, 'plan: no plan card in the Builder — the requirements and their options (2026-10-13)', { card: v.card, cards: v.cards });
  ok(!v.score && !v.behind && !v.seats && !v.old && !v.ledger && !v.sech.some(s => /More picks/.test(s)), 'plan: no score numbers, no colour bars, no “Behind”, no seat chips before registration opens, no ledger, no “More picks”', v);
  /* nothing drafted on arrival */
  ok(planWrites(log).length === 0 && await page.evaluate(() => !localStorage.getItem('tc-drafted:' + TC.user.id + ':' + CFG.TERM)), 'plan: nothing is drafted into Plans on arrival (2026-10-13)', planWrites(log).map(w => w.body.slot));
  /* the rules every option follows */
  const rules = await page.evaluate(() => { const L = TCPL.ledger(), R = planRank(L), done = new Set(TCPL.completed().map(c => TCPL.canon(c) || c)), mine = new Set([...myCodes()].map(c => TCPL.canon(c) || c));
    const opts = [...document.querySelectorAll('#scroll .plo')].map(e => ({ code: e.dataset.x, sec: SEC[e.dataset.y], no: e.classList.contains('plo-no') }));
    return { bad: opts.filter(o => done.has(TCPL.canon(o.code) || o.code) || mine.has(TCPL.canon(o.code) || o.code)).map(o => o.code), noSec: opts.filter(o => !o.sec).length, n: opts.length, sorted: R.all.every((c, i) => !i || R.all[i - 1].wscore >= c.wscore), parts: R.all.every(c => c.parts.req <= 40 && c.parts.urg <= 30 && c.parts.prof <= 15 && c.parts.fr <= 10 && c.parts.seat <= 5 && c.score === c.parts.req + c.parts.urg + c.parts.prof + c.parts.fr + c.parts.seat) }; });
  ok(rules.n > 0 && !rules.bad.length && rules.noSec === 0, 'options: never a class you’ve taken or are taking; each has a section', rules);
  ok(rules.sorted && rules.parts, 'rank: candidates are ordered by weighted score; the five parts stay in range and add up; Seats is 0 before registration opens', rules);
  /* Why: from the class page's pick reason (the Builder's rows open the section sheet) */
  await page.evaluate(() => A.pickWhy(planRank(TCPL.ledger()).all[0].code)); await tick(page, 400);
  const why = await page.evaluate(() => { const s = document.getElementById('sheet'); return { labs: [...s.querySelectorAll('.pw-lab')].map(x => x.innerText), vals: [...s.querySelectorAll('.pw-val')].map(x => x.innerText) }; });
  ok(why.labs.join() === 'Requirements,Urgency,Professor,Friends,Seats' && why.vals[4] === 'Oct 19', 'why: the five parts — Seats reads “Oct 19” until registration opens', why);
  await page.evaluate(() => A.closeSheet()); await tick(page, 200);
  const sen = await page.evaluate(() => { const was = TC.profile.class_standing; TC.profile.class_standing = 'Senior'; const R = planRank(TCPL.ledger()); TC.profile.class_standing = was; const top = R.all.find(c => c.behind); return top && { code: top.code, tag: pickReason(top).t, urg: top.parts.urg }; });
  ok(sen && sen.tag === 'Catch up' && sen.urg >= 12, 'rank: for a senior a class from an earlier year is tagged “Catch up” and gains urgency', sen);
  ok(log.errors.length === 0, 'plan: no page errors', log.errors);
  await close();
};
""")

func('springCardA', r"""
tests.springCardA = async () => {
  const cfg = Object.assign({}, SPRING_CFG, { REGISTRATION_TERM: 'Spring 2027', REGISTRATION_OPENS: '2026-10-19' });
  const T = springTables(); T.planner_prefs = [{ user_id: FX.ME.id, priority: 'degree', units: 12 }];
  const { page, close, log } = await openApp({ terms: cfg, tables: T, time: '2026-10-09T16:30:00-07:00', height: 1600 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await page.evaluate(() => { S.tab = 'schedule'; S.schedTab = 'planner'; render(true); }); await tick(page, 800);
  const a = await page.evaluate(() => ({ reg: (document.querySelector('.pla-reg') || {}).textContent || '', sub: (document.querySelector('.pl-sub') || {}).textContent || '', card: document.querySelectorAll('.pl-card, .plr, .pla-tab, .pla-blk').length, rows: [...document.querySelectorAll('.plo')].map(r => r.innerText.replace(/\s+/g, ' ')), text: document.getElementById('scroll').innerText }));
  ok(/^Opens Oct 19 · in 10 days\s*Add your day$/.test(a.reg.trim()) && !/Registration|Opens/.test(a.sub), 'card A: registration is its own amber line, with the days to go', a.reg);
  ok(a.card === 0 && a.rows.length > 0 && !/Recommended for Plan|TermChamp’s Plan/.test(a.text), 'card A: no plan card, tabs or week in the Builder — the requirements and their options (2026-10-13)', { card: a.card, rows: a.rows.length });
  ok(a.rows.every(r => /^[^★]+ [A-Z]{2,5} \d{4}[A-Z]? /.test(r) && !/★/.test(r)), 'card A: each row is the name, the number and the professor — no rating or time until you tap', a.rows.slice(0, 3));
  await page.locator('.plo').first().click(); await tick(page, 400);
  ok(await page.evaluate(() => !!(UI.sheet && UI.sheet.type === 'sec' && UI.sheet.fill)), 'card A: a tap opens the section sheet, saying what it fills');
  await page.evaluate(() => { UI.sheet = null; render(true); });
  const one = await page.evaluate(() => { const d = new Date(sloISO() + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + 1); const was = CFG.REGISTRATION_OPENS; CFG.REGISTRATION_OPENS = d.toISOString().slice(0, 10); render(true);
    const t = (document.querySelector('.pla-reg') || {}).textContent || ''; CFG.REGISTRATION_OPENS = was; render(true); return t; });
  ok(/· in 1 day\s*Add your day$/.test(one.trim()), 'card A: “in 1 day” the day before', one);
  await page.setViewportSize({ width: 320, height: 1400 }); await page.evaluate(() => render(true)); await tick(page, 400);
  const narrow = await page.evaluate(() => ({ spill: [...document.querySelectorAll('.pla-reg .grow, .pla-add, .plq-t b, .plo-p')].filter(e => e.offsetParent && (e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > e.parentElement.getBoundingClientRect().right + 1)).map(e => e.textContent.trim().slice(0, 30)), w: document.documentElement.scrollWidth }));
  ok(!narrow.spill.length && narrow.w <= 320, 'card A: at 320px nothing spills out of its row', narrow);
  ok(log.errors.length === 0, 'card A: no page errors', log.errors);
  await close();
};
""")

func('builderPlans', r"""
tests.builderPlans = async () => {
  const { page, close, log } = await openApp({ tables: NOPLANS(), height: 1500 });
  await toPlanner(page, true);
  const v = await page.evaluate(() => ({ tab: document.querySelector('.stabs .on').innerText.trim(), words: document.getElementById('scroll').innerText, card: document.querySelectorAll('#scroll .pl-card, #scroll .plr, #scroll .pla-tab').length, rows: document.querySelectorAll('#scroll .plo').length, profs: [...document.querySelectorAll('#scroll .plo .plo-p')].map(e => e.innerText) }));
  ok(v.tab === 'Builder' && !/Planner|Best fit|Backup|Recommended for Plan/.test(v.words), 'builder: the tab reads Builder, and no “Planner”, “Best fit”, “Backup” or “Recommended for Plan” on it', v.tab);
  ok(v.card === 0 && v.rows > 0 && v.profs.every(p => p && p.length < 24), 'builder: no plan card; each option row ends with the professor’s last name', { card: v.card, rows: v.rows, profs: v.profs.slice(0, 4) });
  /* the drafting rules still hold for the Add sheet's "Draft it for me" and the plans a student keeps: every plan free of overlaps, another section where one fits */
  const d = await page.evaluate(() => {
    plSync(); const L = TCPL.ledger(), R0 = planRank(L), codes = R0.all.slice(0, 2).map(c => c.code); let nb = 99300;
    const frees = [{ days: 'F', s: 7 * 60, e: 7 * 60 + 50 }, { days: 'F', s: 18 * 60, e: 18 * 60 + 50 }];
    codes.forEach((code, i) => { const base = secsOf(code)[0]; addSection(Object.assign({}, base, { id: String(nb++), sec: '09', days: frees[i].days, s: frees[i].s, e: frees[i].e, status: 'open', seats: 20 })); });
    const top = Object.keys(PROFS).filter(p => ratingOf(p) != null).sort((x, y) => ratingOf(y) - ratingOf(x))[0], b0 = secsOf(codes[0])[0], b1 = secsOf(codes[1])[0];
    addSection(Object.assign({}, b1, { id: String(nb++), sec: '08', prof: top, days: b0.days, s: b0.s, e: b0.e, status: 'open', seats: 20 }));
    const R = planRank(L), a = planDraft(R, 'A', L).ids, b = planDraft(R, 'B', L, [], [a]).ids, c = planDraft(R, 'C', L, [], [a, b]).ids;
    const P = ids => ids.map(id => SEC[id]).filter(Boolean), clash = ids => { const s = P(ids); return s.some((x, i) => s.some((y, j) => j > i && secClash(x, y))); };
    const sec = (ids, code) => (P(ids).find(s => s.code === code) || {}).id;
    return { codes, clash: [a, b, c].map(clash), a: codes.map(x => sec(a, x)), b: codes.map(x => sec(b, x)), n: [a, b, c].map(x => x.length), same: a.length === c.length };
  });
  ok(d.clash.every(x => !x) && d.n.every(n => n > 0), 'draft: every plan is drafted, and nothing inside a plan overlaps', d);
  ok(d.a.every(Boolean) && d.b.every(Boolean) && d.a.every((id, i) => String(id) !== String(d.b[i])), 'draft: a class with another section that fits is in a different section in Plan B — somewhere to switch to', d);
  ok(!String(await page.evaluate(() => String(planDraft))).includes('friendsX') && d.same, 'draft: every plan has the same goal (no friends ×2.5 for C); C keeps as many classes as A', d);
  ok(log.errors.length === 0, 'builder: no page errors', log.errors);
  await close();
};
""")

# ---- new: the options and the sheet, on a report
if 'tests.builderOptions = ' not in S:
    a = "\nconst names = Object.keys(tests).filter(n => !only || n === only);"
    if S.count(a) != 1: sys.exit('builderOptions anchor')
    S = S.replace(a, r"""
/* (2026-10-13) Tate: "the classes that you should take and under each one … the top options for that requirement … click
   approved elective … see all the classes … highest rated professors and friends towards the top … bland until you click on
   particular class and then it should show information like … when you click on someones schedule class." */
tests.builderOptions = async () => {
  const AE = { label: 'Approved Elective', status: 'not', kind: 'conc', ge: null, level: 'LN', code: 'R179-10', units: { req: 4, used: 0, need: 4 }, courses: null, options: [], oneOf: false };
  const SP = { label: 'Business Major Senior Project', status: 'not', kind: 'major', ge: null, level: 'RQ', code: 'R-0037', units: null, courses: null, options: ['BUS 4461', 'BUS 4462', 'BUS 4464', 'BUS 4465', 'BUS 4466', 'BUS 4467'], oneOf: true };
  const sec = (course_code, title, section, instructor, days, class_nbr) => ({ term: '2268', course_code, title, section, instructor, days, status: 'Open', capacity: 30, enrolled: 10, available: 20, waitlist_total: 0, waitlist_capacity: 0, class_nbr, instruction_mode: 'P', location: '' });
  const T = Object.assign({}, NOPLANS(), { course_seats: FX.TABLES.course_seats.concat([sec('BUS 4448', 'Mergers and Acquisitions', '01', 'Rastad, Ali', 'MoWe 10:10AM - 11:30AM', '79448'), sec('BUS 4469', 'Fixed Income Securities', '01', 'Examplewood, Ada', 'TuTh 12:10PM - 1:30PM', '79469'), sec('BUS 4461', 'Senior Project I', '01', 'Ramezani, Cyrus', 'Mo 4:10PM - 5:50PM', '79461'), sec('BUS 4464', 'Applied Senior Project Seminar', '01', 'Birdsall, Kevin', 'MoWe 12:10PM - 1:30PM', '79464'), sec('BUS 4465', 'Senior Project: Building and Launching a Venture', '01', 'Katona, Jon', 'MoWe 6:10PM - 7:30PM', '79465'), sec('BUS 4462', 'Senior Project II', '01', 'Ramezani, Cyrus', 'We 4:10PM - 5:50PM', '79462')]),
    profiles: FX.TABLES.profiles.map(p => p.id === FX.ME.id ? Object.assign({}, p, { major: 'Business Administration', concentration: 'Financial Management', class_standing: 'Senior' }) : p),
    degree_audit: [{ user_id: FX.ME.id, printed_on: '2026-10-08', catalog: 'Fall Quarter 2023', major: 'BUS', concentration: 'Financial Management', units_used: 170, units_needed: 10, requirements: [AE, SP], read_at: '2026-10-08T00:00:00Z' }] });
  const { page, close, log } = await openApp({ tables: T, height: 2200 });
  await toPlanner(page, true);
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; render(true); }); await tick(page, 600);
  const rd = () => page.evaluate(() => { const t = e => e ? e.innerText.replace(/\s+/g, ' ').trim() : '';
    return { who: t(document.querySelector('#scroll .pll-who')), cat: t(document.querySelector('#scroll .pll-cat')), h: t(document.querySelector('#scroll .pll-h')), plan: document.querySelectorAll('#scroll .pl-card, #scroll .plr, #scroll .pla-tab').length,
      cards: [...document.querySelectorAll('#scroll .plq-card')].map(q => ({ open: q.classList.contains('open'), label: t(q.querySelector('.plq-t b')), sub: t(q.querySelector('.plq-t > span')), lab: t(q.querySelector('.plq-lab')), opts: [...q.querySelectorAll('.plo')].map(o => [o.dataset.x, t(o.querySelector('.plo-n')), t(o.querySelector('.plo-c')), t(o.querySelector('.plo-p'))]), more: t(q.querySelector('.plq-more')), mark: !!q.querySelector('[data-a="plMarkAsk"]'), none: t(q.querySelector('.pll-none')) })) }; });
  let v = await rd();
  ok(v.who === 'Business Administration · Financial Management' && v.cat === 'Fall Quarter 2023 catalog from your report · Oct 8, 2026' && v.h === '2 left to graduate' && v.plan === 0, 'options: the top card — major · concentration, the report’s catalog, “2 left to graduate” — and no plan card', v);
  ok(v.cards.length === 2 && v.cards[0].open && !v.cards[1].open && v.cards.map(c => c.label).join('|') === 'Approved Elective Conc.|Business Major Senior Project Pick 1', 'options: one card per requirement, the first open, with its tag', v.cards.map(c => [c.label, c.open]));
  const ae = v.cards[0], sp = v.cards[1];
  ok(/^4 units · 2 offered this fall$/.test(ae.sub) && ae.lab === 'BEST FOR YOU' && ae.opts.length === 2 && ae.opts.every(o => /^BUS 44(48|69)$/.test(o[0]) && o[1] && o[2] === o[0] && /^(Rastad|Examplewood)$/.test(o[3])), 'options: Approved Elective (no classes named) lists the concentration’s electives offered — name, number, professor; nothing else', ae);
  ok(/^pick one of 6 · 4 offered this fall · best (★ \d\.\d |with )?\w+$/.test(sp.sub) && sp.opts.length === 0, 'options: a folded requirement previews how many are offered and the best professor', sp.sub);
  await click(page, '#scroll .plq-card:nth-child(2) .plq'); await tick(page, 300);
  v = await rd(); const sp2 = v.cards[1];
  ok(sp2.open && sp2.opts.length === 3 && sp2.more === 'See all 4' && sp2.mark && sp2.opts.every(o => /^BUS 446[1245]$/.test(o[0])), 'options: Senior Project opens down to its top three, See all 4, Mark done', sp2);
  await click(page, '#scroll .plq-card:nth-child(2) .plq-more'); await tick(page, 300);
  v = await rd();
  ok(v.cards[1].opts.length === 4 && v.cards[1].more === 'Show top 3', 'options: See all lists every one, then Show top 3', [v.cards[1].opts.length, v.cards[1].more]);
  /* the order: best for you — the Builder's rank (a rated professor ahead of none) */
  const ord = await page.evaluate(() => { const R = planRank(TCPL.ledger()); return [...document.querySelectorAll('#scroll .plq-card:nth-child(2) .plo')].map(e => R.all.findIndex(c => c.code === e.dataset.x)); });
  ok(ord.every((x, i) => x >= 0 && (!i || ord[i - 1] <= x)), 'options: in the Builder’s order (your 1-2-3)', ord);
  /* tap: the section sheet, as on a friend's schedule, with what it fills and Add to a plan */
  await click(page, '#scroll .plq-card:nth-child(1) .plo'); await tick(page, 400);
  const sh = await page.evaluate(() => { const s = document.getElementById('sheet'); return { type: UI.sheet && UI.sheet.type, t: s.innerText.replace(/\s+/g, ' '), prof: !!s.querySelector('.profrow'), fill: (s.querySelector('.sec-fill') || {}).innerText || '', add: !!s.querySelector('[data-a="addPlanSheet"]'), view: !!s.querySelector('[data-a="openClass"]'), watch: !!s.querySelector('[data-a="watch"]') }; });
  ok(sh.type === 'sec' && /BUS 44(48|69)/.test(sh.t) && /(Mon\/Wed|Tue\/Thu)/.test(sh.t) && sh.prof && sh.add && sh.view && sh.watch, 'options: a tap opens the section sheet — time, seats, the professor’s row, View class, seat alerts — plus Add to a plan', sh);
  ok(/^Fills Approved Elective · clear of Plan A$/.test(sh.fill), 'options: the sheet says what the class fills, and that it’s clear of your plan', sh.fill);
  await click(page, '#sheet [data-a="addPlanSheet"]'); await tick(page, 400);
  ok(await page.evaluate(() => UI.sheet && UI.sheet.type === 'addTo'), 'options: Add to a plan opens the Add sheet (plans change only there)');
  await page.evaluate(() => { UI.sheet = null; render(true); });
  ok(planWrites(log).length === 0, 'options: nothing is written into Plans by the Builder', planWrites(log).map(w => w.body.slot));
  /* a shift over an option's only section: it's dimmed and says so; the sheet says so too */
  const dim = await page.evaluate(() => { TC.commits = [{ id: 'cm1', kind: 'work', name: 'Shift', days: 'MW', s: 10 * 60, e: 11 * 60 + 30, busy: true }]; render(true);
    const o = [...document.querySelectorAll('#scroll .plo')].find(e => e.dataset.x === 'BUS 4448'); const r = { no: !!o && o.classList.contains('plo-no'), c: o ? o.querySelector('.plo-c').innerText : '', clear: (document.querySelector('#scroll .pl-clear') || {}).innerText || '' };
    if (o) { A.plOptSheet('BUS 4448', o.dataset.y, o); r.fill = (document.querySelector('#sheet .sec-fill') || {}).innerText || ''; } UI.sheet = null; TC.commits = []; render(true); return r; });
  ok(dim.no && /every section clashes with Plan A or your week$/.test(dim.c) && dim.clear === 'Clear of your work' && /over a class in Plan A or your week$/.test(dim.fill), 'options: a class whose only section is over your shift is dimmed and says so; its sheet says so; the top card says “Clear of your work”', dim);
  ok(log.errors.length === 0, 'options: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""")
# ---- pcRows: the Builder's requirement cards read as rows (every one open, off screen), the unknown lines as before
_i = S.index("const pcRows = page => "); _j = S.index("\n", _i)
_line = S[_i:_j]
if 'const Q = q =>' not in _line:
    _a = _line.index("(() => { const g = plGate();"); _b = _line.index("return c0; })", _a) + len("return c0; })")
    LCB = _line[_a:_b]
    _new = ("const pcRows = page => page.evaluate(() => { const ro = UI.plReqOpen; UI.plReqOpen = new Proxy({}, { get: () => true, has: () => true }); let c; try { c = " + LCB + "(); } finally { UI.plReqOpen = ro; } c = c || document.createElement('div');"
      " const M = r => ({ st: r.className.replace('pc-row', '').replace('look', '').trim(), look: /\\blook\\b/.test(r.className), main: ((r.querySelector('.pc-main') || {}).innerText || '').replace(/\\s+/g, ' ').trim(), sub: [...r.querySelectorAll('.pc-used, .pc-pf, .pc-look, .pc-add')].map(e => e.innerText.replace(/\\s+/g, ' ').trim()).join(' | '), still: !!r.closest('.pc-still, .pc-lrows, .pll, .plq-card') });"
      " const Q = q => { const b = q.querySelector('.plq-t b'), lk = q.querySelector('.plq-look'); return { st: 'need', look: !!lk, main: (b && b.firstChild ? b.firstChild.textContent : '').replace(/\\s+/g, ' ').trim(), sub: [((q.querySelector('.plq-t > span') || {}).textContent || '').replace(/\\s+/g, ' ').trim(), lk ? lk.textContent.replace(/\\s+/g, ' ').trim() : ''].filter(Boolean).join(' | '), still: true, opts: [...q.querySelectorAll('.plo')].map(e => e.dataset.x) }; };"
      " const out = [...document.querySelectorAll('#scroll .pc-row')].filter(r => !r.closest('.pll, .plq-card')).map(M).concat([...c.querySelectorAll('.pc-row')].map(M), [...c.querySelectorAll('.plq-card')].filter(q => q.querySelector(':scope > .plq')).map(Q));"
      " document.getElementById('__lc')?.remove(); return out; });")
    S = S[:_i] + _new + S[_j:]
sub("ok(cr && cr.look && /^1 unit needed \\| Needs a look: your report lists BUS 3306 on your record but didn’t count it here/.test(cr.sub),",
    "ok(cr && cr.look && /^1 unit\\b[^|]* \\| Needs a look: your report lists BUS 3306 on your record but didn’t count it here/.test(cr.sub),", 'quarter look')

open(P, 'w', encoding='utf-8').write(S)

# ---- mutants
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
IX = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("options: the first doesn't start open", "UI.plReqOpen = { [reqs[0].key]: true };   /* the first starts open", "UI.plReqOpen = {};   /* the first starts open", "builderOptions"),
  ("options: a new report opens nothing", "if (!UI.plReqOpen || !reqs.some(q => q.key in UI.plReqOpen)) UI.plReqOpen", "if (!UI.plReqOpen) UI.plReqOpen", "plannerRefresh"),
  ("options: more than three", "cs = all ? q.cands.slice(0, 12) : q.cands.slice(0, 3);", "cs = q.cands.slice(0, 12);", "builderOptions"),
  ("options: See all gone", "const more = n > 3 ? `<button class=\"plq-more\"", "const more = false ? `<button class=\"plq-more\"", "builderOptions"),
  ("options: no professor", "<span class=\"plo-p\">${esc(prof(c) || 'Staff')}</span>", "<span class=\"plo-p\"></span>", "builderOptions"),
  ("options: a clash isn't said", "${fits(c) ? '' : ' · every section clashes with Plan ' + k + ' or your week'}", "", "builderOptions"),
  ("options: a clash isn't dimmed", "class=\"plo${fits(c) ? '' : ' plo-no'}\"", "class=\"plo\"", "builderOptions"),
  ("options: the folded preview loses the best", "!open && best ? (br != null ? `best ★ ${br.toFixed(1)}", "false ? (br != null ? `best ★ ${br.toFixed(1)}", "builderOptions"),
  ("options: no Mark done", "const mark = q.b && !auditIsTotal(q.b) && idx ?", "const mark = false ?", "builderOptions"),
  ("options: the tap opens the class page", "    UI.sheet = { type: 'sec', code, id: String(s.id), fill:", "    return A.openClass(code); UI.sheet = { type: 'sec', code, id: String(s.id), fill:", "builderOptions"),
  ("options: the sheet doesn't say what it fills", "${sh.fill ? `<div class=\"sec-fill${sh.fits ? '' : ' no'}\">", "${false ? `<div class=\"sec-fill${sh.fits ? '' : ' no'}\">", "builderOptions"),
  ("options: no Add to a plan", "${sh.fill && !inP && SEC[id] ? `<button class=\"btn\" data-a=\"addPlanSheet\" data-x=\"${esc(id)}\">Add to a plan</button>` : ''}", "", "builderOptions"),
  ("options: a tap doesn't fold", "  plReqOpen: key => { UI.plReqOpen = UI.plReqOpen || {}; UI.plReqOpen[key] = !UI.plReqOpen[key]; render(true); },", "  plReqOpen: key => { UI.plReqOpen = UI.plReqOpen || {}; UI.plReqOpen[key] = true; render(true); },", "builderLeft"),
  ("options: the sheet says clear when it isn't", "fits: !!(c && (c.inPlan || plLeftSec(c, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A')))", "fits: true", "builderOptions"),
]
for n, a, b, t in MUT:
    if IX.count(a) != 1: sys.exit(f'mutant anchor {n}: {IX.count(a)}x')
if 'edit-tests-builder-options-2026-10-13.py' not in T:
    k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
    if T.count(k) != 1: sys.exit('mutate anchor')
    T = T.replace(k, "\n  /* the Builder: what to take, the options under each, the section sheet on tap (2026-10-13; edit-tests-builder-options-2026-10-13.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
# retire the mutants of the code that went (TermChamp's plans card and sheet); re-aim the rest
GONE = ["rec: no week", "rec: B the same as A", "rec: what's left not first", "rec: swaps overlap", "rec: swap ignored", "rec: swaps not kept", "rec: reset ignored", "rec: drop ignored", "rec: set writes nothing", "rec: no undo", "rec: never 'this is your plan'", "rec: set over plans that didn't load", "rec: drafted into Plans again", "rec: your work isn't drawn", "builder: folded shows the full rows", "builder: no in-progress toggle", "builder: no who line", "builder: no count", "builder: plain requirement rows", "builder: the catalog row loses its date", "builder left: lines don't name the plan's class", "builder left: the plan's lines not first", "draft: drafted with no record and no report", "builder: no same-as-A note", "work: the Builder drafts before asking", "work: plans don't draw it", "past left: no count on top", "card A: registration back in the sub line", "truth: the catalog line is missing", "prefs: no order on the Builder", "builder left: no card", "draft: drafted without prerequisites", "plan: the footnote doesn't say drafts are private", "rec: no elective for an unnamed line", "rec: suggestion unsaid"]
RE = {
  "plans: empty plan doesn't point to the Builder": ["plans: empty plan doesn't point to the Builder", "Add classes from the Builder or Explore.", "Add classes from Explore.", "plannerExistingPlan"],
  "builder: no who line": ["builder: no who line", "const top = `<div class=\"card pll\">${who}${catRow}", "const top = `<div class=\"card pll\">${catRow}", "builderOptions"],
  "builder: no count": ["builder: no count", "</div>${num}${clear}${pick}</div>`;", "</div>${clear}${pick}</div>`;", "builderMerged"],
  "builder: the catalog row loses its date": ["builder: the catalog row loses its date", "from your report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span></div>", "from your report</span></div>", "builderOptions"],
  "card A: registration back in the sub line": ["card A: registration back in the sub line", "${rankRow}${plRegBanner()}", "${rankRow}", "springCardA"],
  "truth: the catalog line is missing": ["truth: the catalog line is missing", "  const catRow = X && TC.audit.catalog ?", "  const catRow = false ?", "dprStressQuarter", None],
  "prefs: no order on the Builder": ["prefs: no order on the Builder", "${plUnitsTarget()} units · Edit</button></div>${rankRow}${plRegBanner()}", "${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}", "plannerPrefs"],
  "builder left: no card": ["builder left: no card", "  ${left}\n", "", "plannerPlan", None],
  "draft: drafted without prerequisites": ["draft: drafted without prerequisites", "Prerequisites didn’t load, so these options don’t check them.", "", "plannerNoDraft"],
  "plan: the footnote doesn't say drafts are private": ["plan: the footnote doesn't say drafts are private", "Your plans change only when you add a class, and are only yours until you share them. ", "", "plannerFromReport"],
  "rec: no elective for an unnamed line": ["options: no elective for an unnamed line", "  if (concE) auditOpen.filter(b => b.kind === 'conc'", "  if (false) auditOpen.filter(b => b.kind === 'conc'", "builderOptions"],
  "work: plans don't draw it": None,
  "work: the Builder drafts before asking": ["work: the Builder asks after showing", "  ${asked ? '' : cmAskCard()}\n  ${left}", "  ${left}\n  ${asked ? '' : cmAskCard()}", "workActivities", None],
}
GONE.append("plans: empty plan doesn't point to the Builder")
# unreachable since the plan card left the Builder (planCard, planTabs, plRedraft, plAutoDraft are no longer drawn or called)
for _n in ["plan: the switch doesn't switch", "plan: Plan B's card says Best fit", "draft: a pick-1 line gets two classes", "draft: a loaded read never says so", "card A: tabs without names", "builder: B ignores A"]: GONE.append(_n)
GONE.append("truth: the conflict isn't shown"); GONE.append("plan: seats count before registration opens")
RE["truth: the conflict isn't shown"] = ["truth: the conflict isn't shown", "const look = q.b && (q.b.listed || []).length ?", "const look = false && (q.b.listed || []).length ?", "dprStressQuarter", None]
RE["plan: seats count before registration opens"] = ["plan: seats count before registration opens", "const seat = !regOpen() ? 0 : openN >= 10 ? 5 : open ? 3 : waits ? 1 : 0;", "const seat = openN >= 10 ? 5 : open ? 3 : waits ? 1 : 0;", "plannerRegOpen"]
Ls = T.split('\n')
for i, l in enumerate(Ls):
    for n in GONE:
        if l.lstrip().startswith('[' + json.dumps(n, ensure_ascii=False) + ','):
            m = RE.get(n, None)
            Ls[i] = '' if m is None else '  ' + json.dumps(m, ensure_ascii=False) + ','
T = '\n'.join(Ls)
for n, m in RE.items():
    if m and IX.count(m[1]) != 1: sys.exit(f're-aimed mutant anchor {n}: {IX.count(m[1])}x')
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-builder-options: done')
