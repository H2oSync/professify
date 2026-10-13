#!/usr/bin/env python3
"""Re-aims the older Planner tests at registration-day-2026-10-11.py: the amber line now reads "Opens Oct 19 · in N
days" with "Add your day" beside it (Tate picked the slim line B), and the plan card has no tiles (Tate: "take out
this its not that important to show"). Usage: python3 edit-tests-registration-day-2026-10-11.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app-dev' / 'tests' / 'check-app.mjs'
s = f.read_text()
if 'reg-day re-aim (2026-10-11)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)

one("""  ok(/^Registration opens Oct 19 · in 10 days$/.test(a.reg.trim()) && !/Registration/.test(a.sub), 'card A: registration is its own amber line, with the days to go', a.reg);""",
    """  /* reg-day re-aim (2026-10-11): the line is "Opens Oct 19 · in 10 days", with Add your day beside it */
  ok(/^Opens Oct 19 · in 10 days\\s*Add your day$/.test(a.reg.trim()) && !/Registration|Opens/.test(a.sub), 'card A: registration is its own amber line, with the days to go', a.reg);""")
one("""  ok(a.stats.length === 3 && new RegExp('^Classes ' + a.n + '\\\\b', 'i').test(a.stats[0]) && /^Professors /i.test(a.stats[1]) && (a.avg == null ? /—/.test(a.stats[1]) : a.stats[1].includes(a.avg.toFixed(1))) && /^Days? off /i.test(a.stats[2]) && a.off.every(d => a.stats[2].includes(DAYN_[d])), 'card A: tiles for classes, professors and the day off', a.stats);""",
    """  ok(a.stats.length === 0, 'card A: no tiles (Tate, 2026-10-11: “take out this its not that important to show”)', a.stats);""")
one("""  ok(/· in 1 day$/.test(one.trim()), 'card A: “in 1 day” the day before', one);""",
    """  ok(/· in 1 day\\s*Add your day$/.test(one.trim()), 'card A: “in 1 day” the day before', one);""")
one("""const narrow = await page.evaluate(() => ({ spill: [...document.querySelectorAll('.pla-stat span, .pla-tab')]""",
    """const narrow = await page.evaluate(() => ({ spill: [...document.querySelectorAll('.pla-reg .grow, .pla-add, .pla-tab')]""")
one("""/16 units · Edit/.test(v.top) && /^Registration opens Oct 19/.test(v.reg.trim()), 'plan: the top is the term""",
    """/16 units · Edit/.test(v.top) && /^Opens Oct 19/.test(v.reg.trim()), 'plan: the top is the term""")
one("""  ok(v.tiles.length === 3 && /^Classes \\d+/i.test(v.tiles[0]) && v.edit === 'Edit Plan A', 'plan: the tiles (classes, professors, day off) and an Edit Plan A button', { tiles: v.tiles, edit: v.edit });""",
    """  ok(v.tiles.length === 0 && v.edit === 'Edit Plan A', 'plan: no tiles (2026-10-11) and an Edit Plan A button', { tiles: v.tiles, edit: v.edit });""")
one("""  ok(!v.open && /Registration opens Oct 19/.test(v.top) && !v.seats, 'reg: planning the term registration is for, before Oct 19 — the line shows and seats don’t', v);""",
    """  ok(!v.open && /Opens Oct 19/.test(v.top) && !v.seats, 'reg: planning the term registration is for, before Oct 19 — the line shows and seats don’t', v);""")
one("""v.reg === 'Spring 2027' && !/Registration opens/.test(v.top), 'reg: planning Fall 2026 (in session)""",
    """v.reg === 'Spring 2027' && !/Registration opens|Opens Oct|Add your day|You register/.test(v.top), 'reg: planning Fall 2026 (in session)""")
one("""/^Fall 2026\\s*5 requirements left/.test(v.top) && !/Registration opens/.test(v.top), 'report:""",
    """/^Fall 2026\\s*5 requirements left/.test(v.top) && !/Registration opens|Opens Oct/.test(v.top), 'report:""")
f.write_text(s)
print('patched', f)
