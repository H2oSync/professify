#!/usr/bin/env python3
"""Tests for stories-freeness-2026-10-11.py: the story row, most free furthest left; schedules not set up always last.
Re-aims two storyOrder assertions and one ringsToday assertion (the new groups), adds tests.storyFreeness and mutants.
Replayable.  python3 edit-tests-stories-freeness-2026-10-11.py"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
def edit(name, pairs):
    p = os.path.join(H, name); s = open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if new in s: continue
        if s.count(old) != 1: sys.exit(f'{name} {label}: anchor matched {s.count(old)}x')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

TESTS = r'''/* ============ Stories, most free furthest left (Tate, 2026-10-11) ============
   No classes today → done for the day → a class later today, the furthest-off first → in class, out soonest first →
   schedule not set up (no class with a set time), always last. Pinned friends stay first. */
tests.storyFreeness = async () => {
  for (const split of [false, true]) {
    const { page, close, log } = await openApp(split ? { terms: SPRING_CFG } : {});   /* Tuesday 10:30a */
    await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
    const tag = split ? ' (Fall classes while picking Spring)' : '';
    /* secs: [code, start, end, days] or { async } / { tba }; null = nothing added; 'unplaced' = a class with no section */
    const set = plan => page.evaluate(plan => {
      const F = TC.friends.slice().sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name));   /* Avery, Harper, Quinn, Rowan, Sky */
      const mk = (i, x, j) => x.async ? { id: 'sf' + i + j, code: 'ONL ' + i, async: true, s: null, e: null, days: '' } : x.tba ? { id: 'sf' + i + j, code: 'TBA ' + i, async: false, s: null, e: null, days: 'TR' }
        : { id: 'sf' + i + j, code: x[0], s: x[1], e: x[2], days: x[3], async: false, sec: '01', prof: null };
      plan.forEach((secs, i) => { const id = F[i], list = secs === 'unplaced' ? [] : (secs || []).map((x, j) => mk(i, x, j)), un = secs === 'unplaced' ? ['UNIV 1101'] : [];
        PEOPLE[id].secs = list; PEOPLE[id].unplaced = un; PEOPLE[id].nowSecs = list; PEOPLE[id].nowUnplaced = un; });
      UI.storyOrder = null; render(true);
    }, plan);
    const names = () => page.locator('.story .nm').allInnerTexts();
    const ranks = () => page.evaluate(() => TC.friends.slice().sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name)).map(id => storyRank(id)[0]));
    /* Avery: Mon/Wed only · Harper: done at 9 · Quinn: class at 2 · Rowan: class at 10:40 (not in it yet) · Sky: in class till 10:35 */
    await set([[['BUS 1', 600, 700, 'MW']], [['BUS 2', 480, 540, 'TR']], [['BUS 3', 840, 900, 'TR']], [['BUS 4', 640, 720, 'TR']], [['BUS 5', 600, 635, 'TR']]]);
    let n = await names();
    ok(n.join(',') === 'Avery,Harper,Quinn,Rowan,Sky' && (await ranks()).join() === '0,1,2,2,3', 'freeness: no classes today, then done for the day, then the furthest-off class (even one 10 minutes off), then in class (even out in 5)' + tag, n);
    /* reversed: the furthest-off class first, whoever's name comes first */
    await set([[['BUS 1', 660, 720, 'TR']], [['BUS 2', 840, 900, 'TR']], [['BUS 3', 900, 960, 'TR']], [['BUS 4', 480, 540, 'TR'], ['BUS 6', 560, 600, 'TR']], [['BUS 5', 600, 700, 'MWF']]]);
    n = await names();
    ok(n.join(',') === 'Sky,Rowan,Quinn,Harper,Avery', 'freeness: among friends with a class later, the furthest-off class is furthest left (3p, 2p, 11a)' + tag, n);
    /* in class: out soonest first; a class straight after counts as the same stretch */
    await set([[['BUS 1', 600, 680, 'TR']], [['BUS 2', 600, 650, 'TR'], ['BUS 6', 655, 760, 'TR']], [['BUS 3', 620, 640, 'TR']], [['BUS 4', 600, 700, 'TR']], [['BUS 5', 615, 645, 'TR'], ['BUS 7', 700, 760, 'TR']]]);
    n = await names();
    ok(n.join(',') === 'Quinn,Sky,Avery,Rowan,Harper', 'freeness: in class, out soonest first (10:40, 10:45, 11:20, 11:40, then back-to-back till 12:40)' + tag, n);
    /* not set up: only online, only no-time, a class with no section, nothing — always right, grey, never free; even on a day with no classes */
    await set([[{ async: 1 }], [{ tba: 1 }], 'unplaced', null, [['BUS 5', 600, 660, 'TR']]]);
    n = await names();
    const st = await page.evaluate(() => TC.friends.slice().sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name)).map(id => { const s = status(id), el = document.querySelector(`.story[data-x="${id}"] .ring`); return [s.free, s.t, (el.getAttribute('style').match(/--rc:([^;"]+)/) || [])[1]]; }));
    ok(n.join(',') === 'Sky,Avery,Harper,Quinn,Rowan' && (await ranks()).join() === '4,4,4,4,3', 'freeness: no class with a set time (online only, no time, no section, nothing) — always furthest right, even behind someone in class' + tag, n);
    ok(st.slice(0, 4).every(x => x[0] === null && x[2] === '#CBD5E1') && st[0][1] === 'Class times not added' && st[1][1] === 'Class times not added' && st[2][1] === 'Class times not added' && st[3][1] === 'No classes added', 'freeness: …with the grey ring and “Class times not added” / “No classes added”, never called free' + tag, st);
    const champFree = await page.evaluate(() => TC.friends.filter(f => status(f).free === true).map(f => PEOPLE[f].short));
    ok(champFree.length === 0, 'freeness: Champ’s “who’s free” doesn’t count them either' + tag, champFree);
    /* one timed class among online ones is enough to know their day */
    await set([[{ tba: 1 }], null, null, null, [{ async: 1 }, ['BUS 1', 480, 540, 'TR']]]);
    n = await names();
    ok(n[0] === 'Sky' && (await ranks()).join() === '4,4,4,4,1' && await page.evaluate(() => status(TC.friends.find(f => PEOPLE[f].short === 'Sky')).free) === true, 'freeness: an online class plus one with a set time counts as set up (done for the day here)' + tag, n);
    /* pinned friends stay first, whatever their freeness */
    await set([[['BUS 1', 600, 700, 'MW']], [['BUS 2', 480, 540, 'TR']], [['BUS 3', 840, 900, 'TR']], null, [['BUS 5', 600, 660, 'TR']]]);
    await page.evaluate(() => { const r = TC.friends.find(f => PEOPLE[f].short === 'Rowan'); pinsSet([r]); UI.storyOrder = null; render(true); });
    n = await names();
    ok(n.join(',') === 'Rowan,Avery,Harper,Quinn,Sky', 'freeness: a pinned friend stays first (even with no schedule); the rest follow the order' + tag, n);
    await page.evaluate(() => { pinsSet([]); render(true); });
    ok(log.errors.length === 0, 'freeness: no page errors' + tag, log.errors);
    await close();
  }
  /* the weekend: everyone with a set-up schedule has no classes today, by name; not set up still last */
  const { page, close } = await openApp({ time: '2026-10-03T12:00:00-07:00' });
  await page.waitForFunction(() => TC.ready && document.querySelectorAll('.story').length === 5, null, { timeout: 8000 });
  const w = await page.evaluate(() => { const F = TC.friends.slice().sort((a, b) => PEOPLE[a].name.localeCompare(PEOPLE[b].name));
    PEOPLE[F[0]].secs = [{ id: 'w1', code: 'ONL 1', async: true, s: null, e: null, days: '' }]; PEOPLE[F[0]].unplaced = [];
    [1, 2, 3, 4].forEach(i => { PEOPLE[F[i]].secs = [{ id: 'w' + i, code: 'BUS ' + i, async: false, s: 600 + i, e: 660, days: 'TR' }]; PEOPLE[F[i]].unplaced = []; }); UI.storyOrder = null; render(true);
    return { n: [...document.querySelectorAll('.story .nm')].map(e => e.innerText), r: F.map(id => storyRank(id)[0]) }; });
  ok(w.n.join(',') === 'Harper,Quinn,Rowan,Sky,Avery' && w.r.join() === '4,0,0,0,0', 'freeness: on a Saturday everyone set up has no classes today (by name); the online-only friend is still furthest right', w);
  await close();
};

'''
edit('check-app.mjs', [
 ("'stories: free now (longest stretch first), then in class (out soonest first), then no classes added', n);",
  "'stories: no classes today, then a class later (furthest off first), then in class (out soonest first), then no classes added', n);", 'reaim0'),
 ("""  ok(n.join(',') === 'Sky,Rowan,Quinn,Avery,Harper', 'stories: busy friends — in class or about to start one — by when they’re next free (back-to-back classes count as one stretch)', n);""",
  """  ok(n.join(',') === 'Sky,Rowan,Harper,Quinn,Avery', 'stories: not in class yet counts with the free (Harper’s class at 10:40 is the nearest, so last of them); in class, out soonest first (2026-10-11)', n);""", 'reaim1'),
 ("""  ok(n.join(',') === 'Rowan,Quinn,Avery,Sky,Harper', 'stories: opening Home again re-sorts (Sky, now in class till noon, moves in among the busy)', n);""",
  """  ok(n.join(',') === 'Rowan,Harper,Quinn,Avery,Sky', 'stories: opening Home again re-sorts (Sky, now in class till noon, moves in among the busy)', n);""", 'reaim2'),
 ("""  ok(busy.last && busy.rk[0] === 1 && busy.rk[1] === busy.end,""", """  ok(busy.last && busy.rk[0] === 3 && busy.rk[1] === busy.end,""", 'reaim3'),
 ("tests.storyDay = async () => {", TESTS + "tests.storyDay = async () => {", 'tests'),
])
MUT = r'''  /* stories, most free furthest left (2026-10-11) */
  ["freeness: done for the day ahead of no classes today", "  if (!today.length) return [0, 0];", "  if (!today.length) return [1, 1];", "storyFreeness"],
  ["freeness: the nearest class first", "  if (!inc) return [2, -(nx.s - now)];", "  if (!inc) return [2, nx.s - now];", "storyFreeness"],
  ["freeness: about to start a class counts as busy", "  if (!inc) return [2, -(nx.s - now)];", "  if (!inc && nx.s - now > 15) return [2, -(nx.s - now)];\n  if (!inc) return [3, nx.e];", "storyFreeness"],
  ["freeness: not set up ahead of in class", "  if (st.free === null) return [4, 0];", "  if (st.free === null) return [3, 9999];", "storyFreeness"],
  ["freeness: back-to-back not one stretch", "  today.forEach(x => { if (x.e > t && x.s <= t + 10) t = x.e; });\n  return [3, t];", "  return [3, t];", "storyFreeness"],
  ["freeness: online-only counts as set up", "  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return", "  if (!nowSecs(id).length && !nowUnplaced(id).length) return", "storyFreeness"],
  ["freeness: no-time classes count as set up", "  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return", "  if (!nowSecs(id).some(x => !x.async)) return", "storyFreeness"],
  ["freeness: one timed class isn't enough", "  if (!nowSecs(id).some(x => !x.async && x.s != null && x.e != null)) return", "  if (!nowSecs(id).every(x => !x.async && x.s != null && x.e != null)) return", "storyFreeness"],
  ["freeness: in class out latest first", "  return [3, t];\n}", "  return [3, -t];\n}", "storyFreeness"],
'''
edit('mutate.mjs', [("const M = [\n", "const M = [\n" + MUT, 'mutants')])
print('edit-tests-stories-freeness: storyFreeness + 8 mutants, 3 re-aims')
