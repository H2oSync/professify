#!/usr/bin/env python3
"""Tests for conc-electives-2026-10-11.py. Run AFTER edit-tests-in-progress-now-2026-10-11.py.
Usage: python3 edit-tests-conc-electives-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os, json
D = sys.argv[1]
P = os.path.join(D, 'app-dev', 'tests', 'check-app.mjs')
S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    n = S.count(a)
    if n != 1: sys.exit(f'tests {label}: anchor matched {n}x')
    S = S.replace(a, b)
rep("""
const names = Object.keys(tests).filter(n => !only || n === only);""", """
/* (2026-10-11) Tate: "i dont think blockchain in finance is even required so make sure if this is an elective or
   concentration course to specify that … showing all the possible finance concentration classes that are applicable
   this goes for all majors" */
tests.concSpots = async () => {
  const { page, close, log } = await openApp({});
  await page.waitForFunction(() => TC.ready, null, { timeout: 8000 });
  await page.evaluate(() => TC.loadPlanner()); await page.waitForFunction(() => !!window.TCPL, null, { timeout: 8000 });
  const r = await page.evaluate(() => {
    Object.assign(TC.profile, { major: 'Business Administration', concentration: 'Financial Management' }); plSync();
    const L = TCPL.ledger(), cs = L.grid.flatMap(t => t.slots).filter(s => s.ck);
    const el = cs.find(s => s.ck === 'el'), nd = L.need.find(n => n.choice && n.codes.length > 2);
    return { kinds: cs.map(s => s.ck).join(), req: cs.filter(s => s.ck === 'req').map(s => s.code).join(), one: (cs.find(s => s.ck === 'one') || {}).choice, el: el && el.choice, need: nd && nd.codes };
  });
  ok(r.kinds === 'req,req,req,one,el,el,el' && r.req === 'BUS 3411,BUS 3431,BUS 3438' && JSON.stringify(r.one) === JSON.stringify(['BUS 3440', 'BUS 3441']), 'conc spots: Financial Management is BUS 3411, 3431, 3438 required, "BUS 3440 or BUS 3441" as one spot, then three electives', r);
  ok(r.el && r.el.length === 12 && r.el.includes('BUS 4468') && r.el.includes('BUS 4442') && !r.el.some(c => ['BUS 3411', 'BUS 3431', 'BUS 3438', 'BUS 3440', 'BUS 3441'].includes(c)), 'conc spots: an elective spot is any of the 12 track classes (Blockchain in Finance is one of them, not a required class)', r);
  ok(r.need && r.need.length === 12, 'conc spots: the Planner’s list for an open elective holds every class that counts', r.need);
  /* every major, every concentration: no required class twice, no elective that's a required class, never the required list offered again */
  const all = await page.evaluate(() => {
    const bad = [], seen = { majors: 0, conc: 0 };
    Object.values(SCHED_MAJORS).forEach(m => {
      if (!(m.terms || []).some(t => (t.slots || []).some(s => s.type === 'concentration'))) return;
      const ci = TCPL.concInfo(m.name); if (!ci.list.length) return; seen.majors++;
      ci.list.forEach(c => { seen.conc++;
        Object.assign(TC.profile, { major: m.name, concentration: c.name }); plSync(); const L = TCPL.ledger(); if (!L) return;
        const cells = L.grid.flatMap(t => t.slots).filter(s => s.ck), req = cells.filter(s => s.ck === 'req').map(s => s.code), reqSet = new Set(req.concat(cells.filter(s => s.ck === 'one').flatMap(s => s.choice || [s.code])));
        if (new Set(req).size !== req.length) bad.push(m.name + ' / ' + c.name + ': a required class twice');
        cells.filter(s => s.ck === 'el').forEach(s => { if ((s.choice || [s.code]).some(x => x && reqSet.has(x))) bad.push(m.name + ' / ' + c.name + ': an elective spot offers a required class'); });
        if (cells.some(s => /additional concentration course/.test(s.title))) bad.push(m.name + ' / ' + c.name + ': old "additional concentration course"');
      });
    });
    return { bad: [...new Set(bad)], seen };
  });
  ok(all.seen.conc > 40 && !all.bad.length, 'conc spots: every major with concentrations (' + all.seen.majors + ' majors, ' + all.seen.conc + ' concentrations) — required once, electives never a required class', all);
  /* Past classes says what each spot is */
  await page.evaluate(() => { Object.assign(TC.profile, { major: 'Business Administration', concentration: 'Financial Management' }); });
  await click(page, '[data-a="tab"][data-x="schedule"]'); await click(page, '[data-a="schedTab"][data-x="past"]'); await tick(page, 2000);
  await page.evaluate(() => { for (let y = 1; y <= 5; y++) UI.plYears[y] = true; render(true); }); await tick(page, 500);
  const k = await page.evaluate(() => [...document.querySelectorAll('.pc-kind')].map(e => e.textContent));
  ok(k.filter(x => x === 'Required · Financial Management').length === 3 && k.includes('Required · Financial Management · either one') && k.filter(x => x === 'Elective · Financial Management · any of 12').length >= 1, 'conc spots: on Past classes each spot says Required, Required · either one, or Elective · any of 12', k);
  const soc = await page.evaluate(() => { const c = TCPL.concInfo('Sociology').list[0]; Object.assign(TC.profile, { major: 'Sociology', concentration: c.name }); render(true); return [...document.querySelectorAll('.pc-kind')].map(e => e.textContent); });
  ok(soc.some(x => /^Elective · .* · .+/.test(x)) && !soc.some(x => /any of/.test(x)), 'conc spots: a concentration with no class list for its electives shows the catalog’s note instead', soc);
  ok(log.errors.length === 0, 'conc spots: no page errors', log.errors);
  await close();
};

const names = Object.keys(tests).filter(n => !only || n === only);""", 'new test')
open(P, 'w', encoding='utf-8').write(S)

M = os.path.join(D, 'app-dev', 'tests', 'mutate.mjs')
T = open(M, encoding='utf-8').read()
J = open(os.path.join(D, 'app', 'planner.js'), encoding='utf-8').read()
A = open(os.path.join(D, 'app', 'index.html'), encoding='utf-8').read()
MUT = [
  ("conc: CONC_REQS keeps its whole list as required", "        if(!sh)return {name:k,units:0,note:'',classes:all.map(nm)};", "        if(true)return {name:k,units:0,note:'',classes:all.map(nm)};", "concSpots", "planner"),
  ("conc: a pick-one becomes two spots", "          else if(oi<oneG.length){", "          else if(false){", "concSpots", "planner"),
  ("conc: electives offer the required classes", "var taken={}; sh.req.concat.apply(sh.req,sh.one||[]).forEach(function(c){ taken[c]=1; });", "var taken={};", "concSpots", "planner"),
  ("conc: an elective spot holds one class", "if(elec.length===1){ ns.code=elec[0]; ns.type='course'; } else { ns.type='choice'; ns.options=elec.slice(); }", "ns.code=elec[0]; ns.type='course';", "concSpots", "planner"),
  ("conc: the spot never says what it is", "${kindTag}${line}", "${line}", "concSpots", None),
  ("conc: no catalog note on an elective with no list", " : s.hint && !nOpt ? ` · ${esc(s.hint)}` : ''}`", " : ''}`", "concSpots", None),
]
for n, a, b, t, g in MUT:
    src = J if g == 'planner' else A
    if src.count(a) != 1: sys.exit(f'mutant anchor {n}: {src.count(a)}x')
lines = ''.join('  ' + json.dumps([n, a, b, t, g], ensure_ascii=False) + ',\n' for n, a, b, t, g in MUT)
k = "\n];\nconst html = fs.readFileSync(SRC, 'utf8');"
if T.count(k) != 1: sys.exit('mutate anchor')
T = T.replace(k, "\n  /* concentration spots say what they are (2026-10-11; edit-tests-conc-electives-2026-10-11.py) */\n" + lines + "];\nconst html = fs.readFileSync(SRC, 'utf8');")
open(M, 'w', encoding='utf-8').write(T)
print('edit-tests-conc-electives: done')
