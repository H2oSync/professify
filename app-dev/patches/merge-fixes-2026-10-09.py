#!/usr/bin/env python3
"""Fixes from the second-model review of the merge (spring wall + the report → Planner → Plans flow), 2026-10-09.

Once Spring 2027 is the term you choose in and Fall 2026 is the term you're in (splitTerms()):
1. The Planner's picks and "something fun" count a Fall class you're taking now as done by Spring
   (prerequisite met), and a Spring class you're registered for as in progress. Before, every Fall
   class in progress blocked the Spring class it leads to.
2. The Planner waits for your Fall classes: a failed read is said, not counted as "none", and Plan A
   isn't drafted without them (it could pick a class you're taking now). Retry reads them again.
3. Home's card for you shows your Fall week, not an auto-drafted Plan A you never opened.
4. Drafting a plan counts the Spring classes you're already registered for: their units come off the
   target, they count toward the most classes a plan takes, and a drafted section can't clash with them.
5. Onboarding's "Taking now" tab says "Spring 2027": that's where what you add there goes.

Usage: python3 merge-fixes-2026-10-09.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'merge-fixes (2026-10-09)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# 1. prerequisites by term
one("""    const st = TCPL.prereqStatus(code, done, [], mine).state;
    return { ok: st === 'met' || st === 'concurrent', st };""",
"""    const st = plPre(code, done, mine).state;
    return { ok: st === 'met' || st === 'concurrent', st };""")
one("""const s = TCPL.prereqStatus(code, done, [], mine).state; return s === 'met' || s === 'concurrent'; };""",
    """const s = plPre(code, done, mine).state; return s === 'met' || s === 'concurrent'; };""")
one("""function plBestSec(code, avoid, strict) {""",
"""/* A Spring pick's prerequisites (merge-fixes (2026-10-09)): with two terms, a Fall class you're taking now
   is finished by Spring, so it counts as taken before; a Spring class you're registered for is in progress.
   One term: everything you're taking is in progress, as before. */
function plPre(code, done, mine) {
  return splitTerms() ? TCPL.prereqStatus(code, done, [...nowCodes()], [...planCodes()]) : TCPL.prereqStatus(code, done, [], mine);
}
function plBestSec(code, avoid, strict) {""")

# 2. the Planner needs your Fall classes too
one("""TC.err.mine ? 'this term’s classes' : ''].filter(Boolean);""",
    """TC.err.mine ? (splitTerms() ? 'your ' + CFG.TERM_LABEL + ' classes' : 'this term’s classes') : '', splitTerms() && (TC.err.nowMine || !TC.nowMineRows) ? 'your ' + nowTerm().label + ' classes' : ''].filter(Boolean);""")
one("""const plCanDraft = () => !!TC.plansLoaded && !TC.err.plans && !!TC.seatsLoaded;""",
    """const plCanDraft = () => !!TC.plansLoaded && !TC.err.plans && !!TC.seatsLoaded && (!splitTerms() || (!!TC.nowMineRows && !TC.err.nowMine));""")
one("""  retryPlanner: () => { TC._plTables = null; UI.pl = null; TC.myHistory = undefined; TC.waived = undefined; render(true); },""",
    """  retryPlanner: () => { TC._plTables = null; UI.pl = null; TC.myHistory = undefined; TC.waived = undefined;
    if (splitTerms() && (TC.err.nowMine || !TC.nowMineRows)) loadNowMine().then(() => { relinkPeople(); render(true); });
    render(true); },""")

# 3. your Home card: an untouched drafted plan isn't "your plan"
one("""  const slot = fp && ['A', 'B', 'C'].find(k => (fp[k] || []).some(has));""",
    """  const slot = fp && ['A', 'B', 'C'].find(k => (fp[k] || []).some(has) && !(id === 'me' && plUntouched(k)));""")

# 4. drafting around the Spring classes you're registered for
one("""  let units = 0;
  keep.forEach(s => { codes[s.code] = 1; const u = unitsOf(s.code, L); if (u != null) units += u; const c = R.all.find(x => x.code === s.code); if (c) { keys[c.key] = 1; take(c); } });""",
"""  let units = 0;
  keep.forEach(s => { codes[s.code] = 1; const u = unitsOf(s.code, L); if (u != null) units += u; const c = R.all.find(x => x.code === s.code); if (c) { keys[c.key] = 1; take(c); } });
  /* Spring classes you're already registered for (merge-fixes (2026-10-09)): their units count toward the
     target and nothing drafted may clash with them. They stay in My Classes, not in the plan. */
  const reg = splitTerms() ? personSecs('me').filter(s => s && s.code && !codes[s.code]) : [];
  reg.forEach(s => { codes[s.code] = 1; const u = unitsOf(s.code, L); if (u != null) units += u; const c = R.all.find(x => x.code === s.code); if (c) { keys[c.key] = 1; take(c); } });
  let regN = reg.length;
  (splitTerms() ? (PEOPLE.me.unplaced || []) : []).forEach(code => { if (codes[code]) return; codes[code] = 1; regN++; const u = unitsOf(code, L); if (u != null) units += u; });""")
one("""    if (units >= target || chosen.length >= cap) break;""", """    if (units >= target || chosen.length + regN >= cap) break;""")
one("""    const sec = plBestSec(c.code, chosen.map(x => x.sec), true); if (!sec) continue;
    chosen.push({ c, sec });""",
    """    const sec = plBestSec(c.code, chosen.map(x => x.sec).concat(reg.filter(x => !x.noTime && !x.async)), true); if (!sec) continue;
    chosen.push({ c, sec });""")

# 5. onboarding: what you add goes to Spring
one("""data-a="onbTab" data-x="now">Taking now</button>""",
    """data-a="onbTab" data-x="now">${splitTerms() ? esc(CFG.TERM_LABEL) : 'Taking now'}</button>""")

f.write_text(s)
print('patched', f)
