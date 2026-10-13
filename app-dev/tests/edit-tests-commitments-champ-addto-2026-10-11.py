#!/usr/bin/env python3
"""Tests for commitments-champ-addto-2026-10-11.py. Run AFTER edit-tests-commitments-2026-10-11.py.
Usage: python3 edit-tests-commitments-champ-addto-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'tests {label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", r"""
/* (2026-10-11) Tate: "adding a class should show it intersecting and pose a question or express that it conflicts" ·
   "Champ doesn't know about them" */
tests.workAddChamp = async () => {
  const { page, close, log } = await openApp({ height: 1400 });
  await page.waitForFunction(() => TC.ready && TC.seatsLoaded, null, { timeout: 8000 });
  /* an open section that fits your classes, and a shift over it */
  const s = await page.evaluate(async () => {
    const x = SECTIONS.find(y => y.s != null && !y.async && y.status === 'open' && /^[MTWRF]+$/.test(y.days) && !personSecs('me').some(z => z.code === y.code) && !clashWithMine(y).length);
    await TC.saveCommit({ id: 'c-shift', kind: 'work', name: 'Barista shift', days: x.days, s: x.s - 30, e: x.e + 60, busy: true });
    S.addDest = 'mine'; openAddTo(x.id); return { id: x.id, code: x.code, days: x.days, s: x.s, e: x.e };
  });
  await tick(page, 500);
  const v = await page.evaluate(() => { const n = document.querySelector('#sheet .at-note'); return { note: n.textContent, cls: n.className, btn: document.querySelector('#sheet .at-go').textContent, alt: (document.querySelector('#sheet .at-alt') || {}).textContent || '',
    hit: [...document.querySelectorAll('#sheet .g-cm.ro.hit')].map(b => b.textContent), ro: document.querySelectorAll('#sheet .g-cm.ro').length, btnCm: document.querySelectorAll('#sheet button.g-cm').length }; });
  ok(/^Overlaps your Barista shift · .+\. Add it anyway\?$/.test(v.note) && /\bwarn\b/.test(v.cls) && v.btn === 'Add anyway' && v.alt === 'Edit Barista shift', 'add: a section over your shift says so and asks — “Add anyway”, or edit the shift', v);
  ok(v.hit.length === s.days.length && v.hit.every(x => x === 'Barista shift') && !v.btnCm, 'add: the week shows the shift, outlined where the section crosses it (not tappable here)', v);
  await page.evaluate(() => { S.addDest = 'A'; openAddTo(UI.sheet.id); }); await tick(page, 300);
  ok(await page.evaluate(() => document.querySelector('#sheet .at-go').textContent) === 'Add to Plan A anyway', 'add: a plan asks the same — “Add to Plan A anyway”');
  await page.evaluate(() => { S.addDest = 'mine'; openAddTo(UI.sheet.id); }); await tick(page, 300);
  const before = log.writes.length;
  await click(page, '#sheet .at-go'); await tick(page, 1500);
  ok(log.writes.slice(before).some(w => /saved_classes|my_sections/.test(w.table)), 'add: Add anyway adds it');
  /* Champ */
  const c = await page.evaluate(sec => {
    const work = chIntent('when do i work');
    const freeQ = chIntent('When am I free ' + DAYL[sec.days[0]] + '?');
    const dayCard = chDay({ d: sec.days[0] });
    const fit = ansFit(sec.code, 'mine');
    TC.commits = TC.commits.map(x => Object.assign({}, x, { days: 'MTWRF', s: 0, e: 1439 }));
    const allOver = ansFit(SECTIONS.find(y => y.s != null && !y.async && y.code !== sec.code && !personSecs('me').some(z => z.code === y.code)).code, 'A');
    const conf = chClashes().size;
    return { work: work && work.t, free: freeQ && freeQ.t, day: /chd-cm/.test(dayCard) && /Barista shift/.test(dayCard), fit: fit && fit.t, allOver: allOver && allOver.t, conf };
  }, s);
  ok(/^Barista shift: .+–.+\.$/.test(c.work || ''), 'champ: “When do I work?” — your shift, from this phone', c.work);
  ok(c.day, 'champ: your day card draws the shift', c);
  ok(/^Free /.test(c.free || '') && !/all day/.test(c.free || ''), 'champ: free time goes around the shift', c.free);
  ok(/already in|is in/.test(c.fit || ''), 'champ: (the section just added is in your classes)', c.fit);
  ok(/^No — every .+ section overlaps your work\.$/.test(c.allOver || ''), 'champ: a class whose every section is over your work — “No — every … overlaps your work”', c.allOver);
  ok(c.conf > 0, 'champ: “my conflicts” counts a class over your work', c);
  ok(log.errors.length === 0, 'work add/champ: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
open(P, 'w', encoding='utf-8').write(S)
M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs'); T = open(M, encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("work add: no question over a shift", "    if (tn === 'ok') { note = `Overlaps your ${w}. Add it anyway?`;", "    if (false) { note = `Overlaps your ${w}. Add it anyway?`;", "workAddChamp", None),
  ("work add: the shift isn't drawn", "one: true, fit: 30, H: 300, extra: cmEx })", "one: true, fit: 30, H: 300 })", "workAddChamp", None),
  ("work add: no outline where it crosses", "label: cmLabel(c), ro: true, hit: cmHit.includes(c) }))", "label: cmLabel(c), ro: true, hit: false }))", "workAddChamp", None),
  ("champ: the day leaves the shift out", "  return nowSecs(id).filter(s => chTimed(s) && s.days.includes(d)).concat(c).sort((a, b) => a.s - b.s);", "  return nowSecs(id).filter(s => chTimed(s) && s.days.includes(d)).sort((a, b) => a.s - b.s);", "workAddChamp", None),
  ("champ: fits ignores the shift", "(P === 'mine' ? clashWithMine(s) : conflicts(ids, s)).concat(cmOf(s));", "(P === 'mine' ? clashWithMine(s) : conflicts(ids, s));", "workAddChamp", None),
  ("champ: no answer for when do I work", "  if (CH_CMQ.test(t)) return ansCommits();", "", "workAddChamp", None),
  ("champ: conflicts ignore the shift", "  m.forEach(s => { if (chTimed(s) && TC.commits.some(c => secClash(s, c))) ids.add(s.id); });", "", "workAddChamp", None),
]
for n, a, b, t, g in MUT:
    if A.count(a) != 1: sys.exit(f'mutant anchor {n}: {A.count(a)}x')
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
T = T.replace(k, "\n  /* work & activities in Add to your week and Champ (2026-10-11; edit-tests-commitments-champ-addto-2026-10-11.py) */\n" + ''.join('  ' + json.dumps(list(m), ensure_ascii=False) + ',\n' for m in MUT) + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T); print('edit-tests-commitments-champ-addto: done')
# re-aim older mutants whose anchors this patch moved
T = open(M, encoding='utf-8').read()
for old, new in [
  ('["champ: fit ignores your classes", "P === \'mine\' ? clashWithMine(s) : conflicts(ids, s);", "P === \'mine\' ? [] : conflicts(ids, s);"',
   '["champ: fit ignores your classes", "(P === \'mine\' ? clashWithMine(s) : conflicts(ids, s)).concat(cmOf(s));", "(P === \'mine\' ? [] : conflicts(ids, s)).concat(cmOf(s));"'),
  ('["champ: fit ignores the plan", "P === \'mine\' ? clashWithMine(s) : conflicts(ids, s);", "P === \'mine\' ? clashWithMine(s) : [];"',
   '["champ: fit ignores the plan", "(P === \'mine\' ? clashWithMine(s) : conflicts(ids, s)).concat(cmOf(s));", "(P === \'mine\' ? clashWithMine(s) : []).concat(cmOf(s));"'),
]:
    if T.count(old) == 1: T = T.replace(old, new)
    elif T.count(new) != 1: sys.exit('re-aim failed: ' + old[:50])
open(M, 'w', encoding='utf-8').write(T); print('re-aims: done')
