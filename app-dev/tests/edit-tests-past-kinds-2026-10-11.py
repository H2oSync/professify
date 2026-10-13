#!/usr/bin/env python3
"""Tests for past-kinds-2026-10-11.py and builder-no-sum-2026-10-11.py. Run AFTER edit-tests-commitments-champ-addto-2026-10-11.py.
Usage: python3 edit-tests-past-kinds-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""v.head === 'Recommended for Plan A' && /units/.test(v.sum), 'builder: “Recommended for Plan A” with Plan A · Plan B · Plan C and a units line', v);""",
    """v.head === 'Recommended for Plan A' && v.sum === undefined, 'builder: “Recommended for Plan A” with Plan A · Plan B · Plan C — no units · professors line under it (Tate 2026-10-11: “take this out”)', v);""", 'builder sum')
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", r"""
/* (2026-10-11) Tate: "add in on Past classes where it says your Major and concentration then shows a simple version of
   the Major classes GE classes and Concentration and elective classes that have been fulfilled" */
tests.pastKinds = async () => {
  const { page, close, log } = await openApp({ height: 1400 });
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  const read = () => page.evaluate(() => { const c = document.querySelector('.pc-sum'); if (!c) return null; const w = c.querySelector('.pc-me');
    return { who: w ? [...w.children].map(x => x.textContent) : null, num: c.querySelector('.pc-num b').textContent, first: c.firstElementChild.className,
      kinds: [...c.querySelectorAll('.pc-k')].map(k => ({ k: k.dataset.k, l: k.querySelector('.pc-kl').textContent, v: k.querySelector('.pc-kv').textContent, full: k.classList.contains('full'), tick: !!k.querySelector('.pc-kv svg'), w: k.querySelector('.pc-kb i').style.width, t: (k.querySelector('.pc-kt') || {}).textContent || '' })) }; });
  await page.evaluate(() => { TC.prefs = TC.prefs || { priority: 'degree', units: 16 }; setTab('schedule'); S.schedTab = 'past'; render(true); }); await tick(page, 1200);
  /* the flowchart, no concentration picked */
  let v = await read();
  const L = await page.evaluate(() => TCPL.ledger());
  ok(v && v.first === 'pc-me' && JSON.stringify(v.who) === '["Business Administration"]', 'past kinds: the card opens with your major (no concentration yet — “Pick your concentration” asks)', v);
  ok(v && v.kinds.map(k => k.l).join('|') === 'Major classes|GE classes|Electives' && v.kinds.map(k => k.k).join('|') === 'major|ge|el', 'past kinds: Major classes · GE classes · Electives, in that order', v && v.kinds);
  const sumF = v ? v.kinds.reduce((a, k) => a + +k.v.split(' of ')[0], 0) : -1, sumN = v ? v.kinds.reduce((a, k) => a + +k.v.split(' of ')[1], 0) : -1;
  ok(v && v.num === `${sumF} of ${sumN}` && v.num === `${L.F} of ${L.N}`, 'past kinds: the rows add up to the big number', [v && v.num, sumF, sumN]);
  const ge = v && v.kinds.find(k => k.k === 'ge'), lg = L.rows.find(r => r.label === 'General education');
  ok(ge && ge.v === `${lg.f} of ${lg.n}` && ge.w === Math.round(100 * lg.f / lg.n) + '%' && (lg.t ? ge.t === `+ ${lg.t} in progress` : !ge.t), 'past kinds: a row says finished of how many, its bar, and “+ N in progress” for classes you’re taking', [ge, lg]);
  /* a concentration picked */
  await page.evaluate(() => { TC.profile.concentration = 'Financial Management'; TCPL.set({ student: { major: TC.profile.major, conc: 'Financial Management', standing: '' } }); render(true); }); await tick(page, 600);
  v = await read();
  ok(v && JSON.stringify(v.who) === '["Business Administration","Financial Management concentration"]' && v.kinds.map(k => k.l).join('|') === 'Major classes|GE classes|Concentration|Electives', 'past kinds: your major and concentration, then Major · GE · Concentration · Electives', v);
  /* with a report: its lines by kind; degree-wide lines only in the big number; in progress counts as filled, like the big number */
  await page.evaluate(() => { TC.audit = { catalog: '2026-2027', reqs: [
    { label: 'BUS 2201', kind: 'major', status: 'satisfied', used: [{ c: 'BUS 2201', t: 'Fall 2025' }] },
    { label: 'BUS 3306', kind: 'major', status: 'not', used: [] },
    { label: 'Area 1A', kind: 'ge', status: 'satisfied', used: [{ c: 'ENGL 1133', t: 'Fall 2024' }] },
    { label: 'Area 2', kind: 'ge', status: 'satisfied', used: [{ c: 'MATH 1221', t: 'Fall 2024' }] },
    { label: 'Finance concentration', kind: 'conc', status: 'in_progress', used: [{ c: 'BUS 3431', t: 'Fall 2026', p: true }] },
    { label: 'Free electives', kind: 'elective', status: 'not', used: [] },
    { label: 'GWR', kind: 'gwr', status: 'satisfied', used: [] },
    { label: 'Total units for the degree', kind: 'units', status: 'not', used: [] } ] }; render(true); }); await tick(page, 800);
  v = await read();
  const by = k => (v.kinds.find(x => x.k === k) || {});
  ok(v && v.kinds.map(k => k.k).join('|') === 'major|ge|conc|el', 'past kinds (report): Major · GE · Concentration · Electives from the report’s own lines', v && v.kinds);
  ok(by('major').v === '1 of 2' && by('el').v === '0 of 1' && !by('major').full, 'past kinds (report): each row counts the report’s lines (GWR and total units only in the big number)', v && v.kinds);
  ok(by('ge').v === '2 of 2' && by('ge').full && by('ge').tick && by('ge').w === '100%', 'past kinds (report): a kind that’s all done is ticked and full', by('ge'));
  ok(by('conc').v === '1 of 1' && !by('conc').full && !by('conc').tick && by('conc').t === 'In progress', 'past kinds (report): a line you’re still taking counts as filled (like the big number) but isn’t ticked — “In progress”', by('conc'));
  ok(v.num === '5 of 8', 'past kinds (report): the big number is still the report’s (5 of its 8 lines — GWR and total units included)', v.num);
  ok(log.errors.length === 0, 'past kinds: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("past kinds: no major line", "<div class=\"card pc-sum\">${pcWho(L, P)}<div", "<div class=\"card pc-sum\"><div", "pastKinds", None),
  ("past kinds: no rows", "</div>${pcKinds(L, X)}${X ?", "</div>${X ?", "pastKinds", None),
  ("past kinds: concentration left out", "const conc = c0 ? `<span>${esc(c0)} concentration</span>` : '';", "const conc = '';", "pastKinds", None),
  ("past kinds: electives under major", "b.kind === 'elective' ? 'el' : 'major'", "'major'", "pastKinds", None),
  ("past kinds: degree lines counted", "      if (auditIsTotal(b) || /^(units|gpa|gwr|uscp)$/.test(b.kind || '')) return;\n", "", "pastKinds", None),
  ("past kinds: in progress ticked", "full = r.f >= r.n && !(X && r.t)", "full = r.f >= r.n", "pastKinds", None),
  ("past kinds: no in-progress note", "${r.t ? `<span class=\"pc-kt\">", "${false ? `<span class=\"pc-kt\">", "pastKinds", None),
  ("past kinds: GE before major", "const PC_KINDS = [['major', 'Major classes'], ['ge', 'GE classes'],", "const PC_KINDS = [['ge', 'GE classes'], ['major', 'Major classes'],", "pastKinds", None),
  ("builder: the units line back", "<div class=\"pl-rech\">Recommended for Plan ${k}</div>${TC.commits.length", "<div class=\"pl-rech\">Recommended for Plan ${k}</div><div class=\"pl-recs\">${planUnitsChip(st)}</div>${TC.commits.length", "builderPlans", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
if 'edit-tests-past-kinds-2026-10-11.py' not in T:
    T = T.replace(k, "\n  /* Past classes by kind; the Builder without its units line (2026-10-11; edit-tests-past-kinds-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-past-kinds: done')
# re-aim: the summary bar is now followed by the kinds
T = open(M, encoding='utf-8').read()
old = '["past: the bar is always full", "<i style=\\"width:${pct}%\\"></i></div>${X ?", "<i style=\\"width:100%\\"></i></div>${X ?"'
new = '["past: the bar is always full", "<i style=\\"width:${pct}%\\"></i></div>${pcKinds(L, X)}", "<i style=\\"width:100%\\"></i></div>${pcKinds(L, X)}"'
if T.count(old) == 1: T = T.replace(old, new)
elif T.count(new) != 1: sys.exit('re-aim failed: past bar')
open(M, 'w', encoding='utf-8').write(T); print('re-aim: done')
# 2026-10-10's "only the number" (option A) gives way to today's kinds: re-aim the two older checks
S = open(P, encoding='utf-8').read()
for old, new in [
  ("""  ok(!/requirements filled|We can’t check|in progress/.test(t), 'past: no legend, no in-progress or can’t-check lines — only the number', (t.match(/[\\s\\S]{0,60}(in progress|We can’t)[\\s\\S]{0,60}/) || [''])[0]);""",
   """  ok(!/requirements filled|We can’t check/.test(t) && !/in progress/.test(t.replace(/\\+ \\d+ in progress/g, '')), 'past: no legend or can’t-check lines — the number, then Major · GE · Concentration · Electives (in progress only as a row’s “+ N in progress”, Tate 2026-10-11)', (t.match(/[\\s\\S]{0,60}(in progress|We can’t)[\\s\\S]{0,60}/) || [''])[0]);"""),
  ("""  ok(/^\\s*\\d+ of \\d+\\s*filled/.test(t.slice(t.indexOf('Past classes') + 12)) &&""",
   """  ok(/^\\s*Business Administration\\s*\\d+ of \\d+\\s*filled/.test(t.slice(t.indexOf('Past classes') + 12)) &&"""),
  ("""'past: the number first; no report row without a report; no × on any row'""", """'past: your major, then the number; no report row without a report; no × on any row'"""),
]:
    if S.count(old) == 1: S = S.replace(old, new)
    elif S.count(new) != 1: sys.exit('re-aim failed: ' + old[:60])
open(P, 'w', encoding='utf-8').write(S); print('re-aim tests: done')
# My Classes: Anytime under the week, days under it (mine-anytime-up-2026-10-11.py)
S = open(P, encoding='utf-8').read()
for old, new in [
  ("""    const any = document.querySelector('.mine-any'), last = [...document.querySelectorAll('#scroll .card')].filter(e => e.offsetParent).pop();""",
   """    const any = document.querySelector('.mine-any'), cs = [...document.querySelectorAll('#scroll .card')].filter(e => e.offsetParent), wk = cs.findIndex(e => e.querySelector('.wk, [data-a="schedDay"]')), ai = cs.indexOf(any), d1 = cs.findIndex(e => e.classList.contains('mine-ag'));"""),
  ("""anyLast: !!any && last === any,""", """anyUp: !!any && wk >= 0 && ai === wk + 1 && d1 > ai,"""),
  ("""JSON.stringify(v.any) === JSON.stringify(v.untimed) && v.anyLast, 'my classes: classes with no set time are in an Anytime card at the bottom', v);""",
   """JSON.stringify(v.any) === JSON.stringify(v.untimed) && v.anyUp, 'my classes: classes with no set time are in an Anytime card right under the week, the days under it — like Plans (Tate 2026-10-11)', v);"""),
]:
    if S.count(old) == 1: S = S.replace(old, new)
    elif S.count(new) != 1: sys.exit('anytime re-aim failed: ' + old[:60])
open(P, 'w', encoding='utf-8').write(S)
T = open(M, encoding='utf-8').read()
for old, new in [
  ('["mine agenda: no day cards", "  return week + agenda + anyCard;", "  return week + anyCard;"', '["mine agenda: no day cards", "  return week + anyCard + agenda;", "  return week + anyCard;"'),
  ('["mine agenda: no Anytime card", "  return week + agenda + anyCard;", "  return week + agenda;"', '["mine agenda: no Anytime card", "  return week + anyCard + agenda;", "  return week + agenda;"'),
  ('["mine agenda: Anytime on top", "  return week + agenda + anyCard;", "  return week + anyCard + agenda;"', '["mine agenda: Anytime back at the bottom", "  return week + anyCard + agenda;", "  return week + agenda + anyCard;"'),
]:
    if T.count(old) == 1: T = T.replace(old, new)
    elif T.count(new) != 1: sys.exit('anytime mutant re-aim failed: ' + old[:50])
open(M, 'w', encoding='utf-8').write(T); print('anytime up: done')
