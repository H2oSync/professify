#!/usr/bin/env python3
"""Tests for my-classes-agenda-2026-10-11.py. Usage: python3 edit-tests-my-classes-agenda-2026-10-11.py <repo-dir>"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", """
/* (2026-10-11) Tate: "i like how this is for plans do the same thing for my classes" · "bring back the anytime classes
   at the bottom" · (the plan's "Friends can see · Plan A without …" row) "dont need this take away" */
tests.mineAgenda = async () => {
  let { page, close, log } = await openApp({ height: 1700 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]'); await tick(page, 600);
  /* the days fold: names and counts only; a tap opens that day, another closes it (Tate, 2026-10-11) */
  const fold = () => page.evaluate(() => [...document.querySelectorAll('.mine-ag')].map(c => ({ k: c.querySelector('.ag-h').dataset.x, open: c.classList.contains('open'), exp: c.querySelector('.ag-h').getAttribute('aria-expanded'), n: c.querySelector('.ag-h em').textContent, rows: c.querySelectorAll('.arow').length })));
  const f0 = await fold();
  ok(f0.length > 0 && f0.every(c => !c.open && c.exp === 'false' && !c.rows && /^\d+ class(es)?$/.test(c.n)), 'my classes: the days start folded — each shows its name and how many classes', f0);
  await click(page, `.mine-ag .ag-h[data-x="${f0[0].k}"]`); await tick(page, 200);
  const f1 = await fold();
  ok(f1[0].open && f1[0].exp === 'true' && f1[0].rows === +f1[0].n.split(' ')[0] && f1.slice(1).every(c => !c.open && !c.rows), 'my classes: a tap opens that day only', f1);
  await click(page, `.mine-ag .ag-h[data-x="${f0[0].k}"]`); await tick(page, 200);
  ok((await fold()).every(c => !c.open && !c.rows), 'my classes: a second tap closes it');
  await page.evaluate(() => { UI.agOpen = UI.agOpen || {}; document.querySelectorAll('.ag-fold .ag-h').forEach(b => { UI.agOpen[b.dataset.x] = true; }); render(true); }); await tick(page, 200);
  const v = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('.schpg > .card, .schpg > div > .card')].filter(e => e.offsetParent);
    const ag = [...document.querySelectorAll('.mine-ag')].map(c => ({ day: c.querySelector('h4').firstChild.textContent, rows: [...c.querySelectorAll('.arow')].map(r => ({ code: r.dataset.x, act: r.dataset.a, tm: r.querySelector('.tm').firstChild.textContent, sub: r.querySelector('.muted').textContent })) }));
    const any = document.querySelector('.mine-any'), last = [...document.querySelectorAll('#scroll .card')].filter(e => e.offsetParent).pop();
    const untimed = personSecs('me').filter(s => !onWeekSec(s)).map(s => s.code).concat((PEOPLE.me.unplaced || []).filter(c => !personSecs('me').some(s => s.code === c)));
    return { ag, any: any && [...any.querySelectorAll('.any-c')].map(b => b.getAttribute('aria-label')), anyLast: !!any && last === any, untimed, ccards: document.querySelectorAll('#scroll .ccard').length, grid: !!document.querySelector('#scroll .card .wk, #scroll .card [data-a="schedDay"]'),
      want: DAYS.map(d => personSecs('me').filter(s => onWeekSec(s) && s.days.includes(d)).length).filter(Boolean).length };
  });
  ok(v.ccards === 0 && v.ag.length === v.want && v.ag.length > 0 && v.grid, 'my classes: the week, then a card per day like Plans — no card per class', v);
  ok(v.ag.every(c => c.rows.length && c.rows.every(r => r.act === 'secSheet' && r.sub.trim().length)), 'my classes: an open day lists time · code · name · professor, each opening the section', v.ag);
  ok(v.untimed.length > 0 && JSON.stringify(v.any) === JSON.stringify(v.untimed) && v.anyLast, 'my classes: classes with no set time are in an Anytime card at the bottom', v);
  /* Plans: no "Friends can see · Plan A without …" row */
  await click(page, '[data-a="schedTab"][data-x="plans"]'); await tick(page, 400);
  await page.evaluate(() => { TC.plans.A = personSecs('me').map(s => s.id); S.plan = 'A'; render(true); }); await tick(page, 300);
  const pf = await page.evaluate(() => [...document.querySelectorAll('#scroll .ag-fold')].map(c => ({ k: c.querySelector('.ag-h').dataset.x, rows: c.querySelectorAll('.arow').length })));
  ok(pf.length > 0 && pf.every(c => /^planA:/.test(c.k) && !c.rows), 'plans: the days fold the same way', pf);
  await click(page, `#scroll .ag-h[data-x="${pf[0].k}"]`); await tick(page, 200);
  ok(await page.locator('#scroll .ag-fold.open .arow').count() > 0 && await page.locator('#scroll .ag-fold.open').count() === 1, 'plans: a tap opens that day');
  for (const k of ['A', 'B', 'C']) { await click(page, `.seg.plans [data-a="pickPlan"][data-x="${k}"]`); await tick(page, 200);
    ok(!(await page.locator('#scroll .regbar.under, #scroll .pl-diff').count()), `plans: Plan ${k} has no “Friends can see · Plan A without …” row`); }
  ok(log.errors.length === 0, 'my classes: no page errors', log.errors);
  await close();
  /* the term you're in (Fall, while Spring is the pick term): the same layout, and a class with no meeting time shows under Anytime */
  ({ page, close, log } = await openApp({ terms: SPRING_CFG, tables: springTables(), height: 1700 }));
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded && TC.nowMineRows, null, { timeout: 10000 });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]'); await tick(page, 400);
  await click(page, '.seg.terms [data-a="pickMineTerm"][data-x="Fall 2026"]'); await tick(page, 800);
  await page.evaluate(() => { PEOPLE.me.nowUnplaced = (PEOPLE.me.nowUnplaced || []).concat(['UNIV 4401']); UI.agOpen = UI.agOpen || {}; render(true); document.querySelectorAll('.ag-fold .ag-h').forEach(b => { UI.agOpen[b.dataset.x] = true; }); render(true); }); await tick(page, 300);
  const f = await page.evaluate(() => ({ ag: [...document.querySelectorAll('.mine-ag .arow')].map(r => r.dataset.a + '|' + r.dataset.y), any: [...document.querySelectorAll('.mine-any .any-c')].map(b => b.dataset.x + '|' + b.dataset.y), ccards: document.querySelectorAll('#scroll .ccard').length, want: nowSecs('me').filter(onWeekSec).length }));
  ok(f.ccards === 0 && f.ag.length >= f.want && f.want > 0 && f.ag.every(x => x === 'openClass|now'), 'my classes, Fall 2026: a card per day, each class opening its Fall page', f);
  ok(f.any.includes('UNIV 4401|now'), 'my classes, Fall 2026: a class with no meeting time is under Anytime at the bottom', f);
  await page.screenshot({ path: '/tmp/claude-0/probe/mine-fall.png' });
  ok(log.errors.length === 0, 'my classes, Fall 2026: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
OPEN = "await page.evaluate(() => { UI.agOpen = UI.agOpen || {}; document.querySelectorAll('.ag-fold .ag-h').forEach(b => { UI.agOpen[b.dataset.x] = true; }); render(true); }); await tick(page, 200);"
REAIMS = [
  ("""  ok(pl.bars === 1 && pl.barAfter && pl.barL === 14 && pl.gap >= 6 && pl.gap <= 14 && /^(Friends can see|Only you)$/.test(pl.barText) && pl.oldShare === 0, 'share top: a plan keeps “Friends can see” under its week, alone', pl);""",
   """  ok(pl.bars === 0 && pl.oldShare === 0, 'share top: a plan has no “Friends can see” row under its week (Tate, 2026-10-11: “dont need this take away”)', pl);"""),
  ("""    const card = await pg2.locator('.ccard[data-a="openClass"][data-y="now"]').count();
    if (card) await click(pg2, '.ccard[data-a="openClass"][data-y="now"]');""",
   """    await pg2.evaluate(() => { UI.agOpen = UI.agOpen || {}; document.querySelectorAll('.ag-fold .ag-h').forEach(b => { UI.agOpen[b.dataset.x] = true; }); render(true); }); await tick(pg2, 200);
    const card = await pg2.locator('.arow[data-a="openClass"][data-y="now"]').count();
    if (card) await click(pg2, '.arow[data-a="openClass"][data-y="now"]');"""),
  ("""  let t = await text(page);
  ok(/Financial Markets[\\s\\S]*Bram Fixturesen · Mon\\/Wed 10:10–12:00/.test(t) && await page.locator('#scroll .schshare[data-x="mine"]').count() === 1, 'terms: the Fall chip is My Classes as before, with Share');""",
   """  """ + OPEN + """
  let t = await text(page);
  ok(/Financial Markets[\\s\\S]*Bram Fixturesen/.test(t) && await page.locator('#scroll .schshare[data-x="mine"]').count() === 1, 'terms: the Fall chip is My Classes (its days opened), with Share');"""),
  ("""  await page.evaluate(() => { CFG.MY_TERMS[1].code = '2274'; render(true); }); await tick(page, 800);
  t = await text(page);""",
   """  await page.evaluate(() => { CFG.MY_TERMS[1].code = '2274'; render(true); }); await tick(page, 800);
  """ + OPEN + """
  t = await text(page);"""),
  ("""  ok(/BUS 3346[\\s\\S]*Sec 02[\\s\\S]*Principles of Marketing[\\s\\S]*Faro Dummelow · Tue\\/Thu 9:40–11:00/.test(t) && /BUS 4401[\\s\\S]*Bram Fixturesen · Mon\\/Wed 1:10–2:30/.test(t), 'terms: Spring cards from your own rows', t.slice(0, 500));""",
   """  ok(/BUS 3346[\\s\\S]*Principles of Marketing[\\s\\S]*Faro Dummelow/.test(t) && /BUS 4401[\\s\\S]*Bram Fixturesen/.test(t) && /Tuesday/.test(t) && /Monday/.test(t), 'terms: Spring’s days from your own rows', t.slice(0, 500));"""),
  ("""  ok(/BUS 3411[\\s\\S]{0,40}No section yet[\\s\\S]{0,20}Finance Practicum/.test(t), 'terms: a saved Spring class with no section is listed', t.slice(-200));""",
   """  ok(await page.locator('#scroll .mine-any .any-c[data-x="BUS 3411"]').count() === 1, 'terms: a saved Spring class with no section is under Anytime', t.slice(-200));"""),
  ("""  await click(page, '#scroll .ccard[data-x="BUS 4401"]');""",
   """  """ + OPEN + """
  await click(page, '#scroll .arow[data-x="BUS 4401"]');"""),
  ("""  ok(/My Classes/.test(t) && /BUS 2201/.test(t), 'schedule: my classes');""",
   """  ok(/My Classes/.test(t) && await page.locator('#scroll .mine-any .any-c[data-x="BUS 2201"]').count() === 1, 'schedule: my classes');"""),
  ("""  ok(rb && /^(Friends can see|Only you)$/.test(rb.text) && rb.n === 1 && !rb.count, 'schedule: a plan’s bar is who can see it, alone — no class count', rb);""",
   """  ok(rb === null, 'schedule: a plan has no bar under its week (Tate, 2026-10-11)', rb);"""),
  ("""  ok(/BUS 2201[\\s\\S]*No section yet/.test(t), 'schedule: a saved class without a section is listed');
  ok(/Financial Markets[\\s\\S]*Bram Fixturesen · Mon\\/Wed 10:10–12:00/.test(t), 'schedule: section line from the seat feed', t.slice(0, 600));
  ok(/Avery[\\s\\S]*in your section/.test(t), 'schedule: friends in my section');""",
   """  ok(await page.locator('#scroll .mine-any .any-c[data-x="BUS 2201"]').count() === 1, 'schedule: a saved class without a section is under Anytime');
  """ + OPEN + """
  t = await text(page);
  ok(/Financial Markets[\\s\\S]*Bram Fixturesen/.test(t), 'schedule: section line from the seat feed', t.slice(0, 600));
  ok(await page.evaluate(() => [...document.querySelectorAll('.mine-ag .arow')].some(r => r.querySelector('img, .av, [class*="av"]'))), 'schedule: friends in my section show on its row');"""),
  ("""  ok(a === '' && b === 'Plan A with 1 section swapped · + STAT 2170' && c === 'Plan A without BUS 3431', 'plans: A has no diff line; B says what was swapped and added; C says what it is without', { a, b, c, set });""",
   """  ok(a === '' && b === '' && c === '', 'plans: no “Plan A with … / without …” line under any plan (Tate, 2026-10-11: “dont need this take away”)', { a, b, c, set });"""),
  ("""    const mi = await edges('mi', "S.tab='schedule';S.schedTab='mine'", { title: '.title', terms: '.seg.terms', cards: '.ccard' });""",
   """    const mi = await edges('mi', "S.tab='schedule';S.schedTab='mine'", { title: '.title', terms: '.seg.terms', cards: '.agenda, .anytime' });"""),
  ("""  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]');
  const wt = await text(page), gold""",
   """  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="mine"]');
  """ + OPEN + """
  const wt = await text(page), gold"""),
  ("""  ok(!/\\d+ class(es)?\\b/.test(t.split('Share')[0]) && /1 section in this plan is no longer in the Fall 2026 list/.test(t)""",
   """  ok(!/\\d+ class(es)?\\b/.test(t.split('Share')[0].split('\\n').filter(l => !/^\\d+ class(es)?$/.test(l)).join('\\n')) && /1 section in this plan is no longer in the Fall 2026 list/.test(t)"""),
  ("""await click(page, '[data-a="pickPlan"][data-x="B"]');
  await page.waitForFunction(() => document.querySelectorAll('#scroll .agenda .arow').length > 0, null, { timeout: 8000 });""",
   """await click(page, '[data-a="pickPlan"][data-x="B"]');
  await tick(page, 300); """ + OPEN + """
  await page.waitForFunction(() => document.querySelectorAll('#scroll .agenda .arow').length > 0, null, { timeout: 8000 });"""),
  ("""&& /ECON 2303/.test(t), 'plans: plan B loads from the server""", """&& /ECON\\s+2303/.test(t), 'plans: plan B loads from the server"""),
]
for a, b in REAIMS:
    if S.count(a) != 1: sys.exit('reaim anchor ' + a[:80] + f' {S.count(a)}x')
    S = S.replace(a, b)
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("mine agenda: no day cards", "  return week + agenda + anyCard;", "  return week + anyCard;", "mineAgenda", None),
  ("mine agenda: no Anytime card", "  return week + agenda + anyCard;", "  return week + agenda;", "mineAgenda", None),
  ("mine agenda: Anytime on top", "  return week + agenda + anyCard;", "  return week + anyCard + agenda;", "mineAgenda", None),
  ("mine agenda: no-section classes left out", "    .concat((unplaced || []).filter(c => !secs.some(s => s.code === c))", "    .concat([].filter(c => !secs.some(s => s.code === c))", "mineAgenda", None),
  ("days fold: a tap never opens a day", "UI.agOpen[k] = !UI.agOpen[k]; render(true);", "render(true);", "mineAgenda", None),
  ("days fold: a folded day still lists its classes", "${open ? rows() : ''}</div>`;", "${rows()}</div>`;", "mineAgenda", None),
  ("days fold: every day opens together", "const k = scope + ':' + d, open = !!UI.agOpen[k];", "const k = scope + ':' + d, open = Object.values(UI.agOpen).some(Boolean);", "mineAgenda", None),
  ("mine agenda: Fall rows open the pick term's page", "${o.now ? ' data-y=\"now\"' : ''}` : `data-a=\"secSheet\"", "` : `data-a=\"secSheet\"", "mineAgenda", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
T = T.replace(k, "\n  /* My Classes like Plans (2026-10-11; edit-tests-my-classes-agenda-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
# mutants of code these patches removed or reworded (2026-10-11)
RETIRE = ["plans: no diff line on B", "share row: class count back", "share top: Share back in the plan bar", "plan's Share back above the week",
          "term switch: My Classes › Fall card opens Spring", "schedule width: class cards back to 16px"]
lines = T.split('\n')
keep = [l for l in lines if not any(l.lstrip().startswith('[' + json.dumps(n, ensure_ascii=False) + ',') or l.lstrip().startswith("['" + n + "',") for n in RETIRE)]
if len(lines) - len(keep) != len(RETIRE): sys.exit(f'retire: removed {len(lines) - len(keep)}')
T = '\n'.join(keep)
MREAIM = [
  (r'''"if (!(S.exMode === 'classes' && splitTerms())) return subj", "if (!splitTerms()) return subj"''', r'''"if (!(S.exMode === 'classes' && splitTerms())) return `<span", "if (!splitTerms()) return `<span"'''),
  (r'''"if (!(S.exMode === 'classes' && splitTerms())) return subj", "if (!(S.exMode === 'classes')) return subj"''', r'''"if (!(S.exMode === 'classes' && splitTerms())) return `<span", "if (!(S.exMode === 'classes')) return `<span"'''),
  (r'''"margin:10px 12px 0;padding:14px 0 12px\">${grid(secs, {", "margin:10px 16px 0;padding:14px 0 12px\">${grid(secs, {"''', r'''"margin:10px 12px 0;padding:14px 0 12px\">${grid(timed, o.grid)}", "margin:10px 16px 0;padding:14px 0 12px\">${grid(timed, o.grid)}"'''),
]
for a, b in MREAIM:
    if T.count(a) != 1: sys.exit('mreaim ' + a[:60] + f' {T.count(a)}x')
    T = T.replace(a, b)
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-my-classes-agenda: done')
