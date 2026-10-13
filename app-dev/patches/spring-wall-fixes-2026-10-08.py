#!/usr/bin/env python3
"""spring-wall, review fixes (Sonnet review of 2026-10-08):
- Rate's "current" professors are the ones you have now (Fall), not the Spring ones you haven't had.
- Fall's seat rows are read after any reload of your or your friends' classes, not only at sign-in, and
  the story order is worked out again when they arrive.
- "New" tags on Home wait for the seat list and the plans, are worked out after the plans arrive, and a
  friend you've removed never gets a card back.
- A failed Spring read no longer leaves the Fall chip loading forever; its error card retries.
- "Your class" on a class page and "with you" on a friend's plan mean your Spring classes.
- Champ's "what is <friend> taking" lists both terms.
- The Pacific date is worked out once a minute, not on every check.
- "Spring classes added" names the term from the config; the friend switch wraps on narrow phones.
Usage: python3 spring-wall-fixes-2026-10-08.py <repo>   (after spring-wall-2026-10-08.py)
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'spring-wall fixes (2026-10-08)' in s:
    sys.exit('already patched')
def one(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:100]); s = s.replace(old, new)

one("""function sloYmd() {
  try {""", """function sloYmd() {
  /* spring-wall fixes (2026-10-08): worked out once a minute — splitTerms() runs many times a render */
  const t = Date.now(); if (sloYmd.c && t - sloYmd.t < 60000) return sloYmd.c;
  sloYmd.t = t; sloYmd.c = sloYmd0(); return sloYmd.c;
}
function sloYmd0() {
  try {""")

# 1. Rate: current = now
one("""  const cur = { term: CFG.TERM_LABEL, current: true, items: [] };""",
    """  const cur = { term: nowTerm().label, current: true, items: [] };""")
one("""  TC.mySecs.forEach(s => { if (s.prof && !seen[s.prof]) { seen[s.prof] = 1; cur.items.push([s.prof, s.code]); } });""",
    """  (splitTerms() ? nowSecs('me') : TC.mySecs).forEach(s => { if (s.prof && !seen[s.prof]) { seen[s.prof] = 1; cur.items.push([s.prof, s.code]); } });""")
one("""    const taken = [...new Set(personSecs('me').filter(s => s.prof === pid)""",
    """    const taken = [...new Set(personSecs('me').concat(splitTerms() ? nowSecs('me') : []).filter(s => s.prof === pid)""")

# 2/3. now seats after any reload; story order again when they arrive
one("""      part.forEach(n => { if (!Object.prototype.hasOwnProperty.call(NOW_SEC, n)) NOW_SEC[n] = null; });""", """      part.forEach(n => { if (NOW_SEC[n] === undefined) NOW_SEC[n] = null; });""")
one("""  if (!want.size) return;
  const base = CFG.SUPABASE_URL.replace(/\\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const sel = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr', list = [...want];""",
"""  if (!want.size) return;
  const base = CFG.SUPABASE_URL.replace(/\\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const sel = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr', list = [...want];
  list.forEach(n => { NOW_SEC[n] = NOW_SEC[n] || undefined; });   /* asked once; a second reload while this runs doesn't ask again */""")
one("""  } catch (e) {}
  relinkPeople(); render(true);
}""", """  } catch (e) {}
  list.forEach(n => { if (NOW_SEC[n] === undefined) delete NOW_SEC[n]; });   /* a failed read is asked again next time */
  UI.storyOrder = null;   /* who's free now can change once the times are in */
  relinkPeople(); loadRateList(); render(true);
}""")
one("""  if (splitTerms()) await loadNowMine(); else { TC.nowMineRows = null; delete TC.err.nowMine; }
  relinkPeople();
}""", """  if (splitTerms()) await loadNowMine(); else { TC.nowMineRows = null; delete TC.err.nowMine; }
  relinkPeople();
  if (splitTerms() && TC.ready) loadNowSeats();
}""")
one("""  if (codes.error) { TC.err.mine = codes.error.message; return; }
  delete TC.err.mine;""", """  if (codes.error) { TC.err.mine = codes.error.message; if (splitTerms()) { await loadNowMine(); relinkPeople(); } return; }
  delete TC.err.mine;""")
# loadFriends end
i = s.index("async function loadFriends() {")
j = s.index("  relinkPeople();\n}", i)
s = s[:j] + "  relinkPeople();\n  if (splitTerms() && TC.ready) loadNowSeats();   /* spring-wall fixes: a new friend's Fall classes */\n}" + s[j + len("  relinkPeople();\n}"):]

# 4/5/6. feedNew: wait for seats; reset after plans arrive; only current friends
one("""  if (!splitTerms() || !TC.ready || !TC.user || !(TC.friendPlans || TC.err.friendPlans)) return [];
  if (UI.feedNew) return UI.feedNew;""", """  if (!splitTerms() || !TC.ready || !TC.user || !TC.seatsLoaded || !(TC.friendPlans || TC.err.friendPlans)) return [];
  if (UI.feedNew) return UI.feedNew.filter(f => TC.friends.includes(f));""")
one("""async function loadFriendPlans() {
  UI.feedNew = null;   /* Home works out again who has something new (spring-wall) */
""", """async function loadFriendPlans() {
""")
one("""    if (ids.length) (TC.friendPlans[row.user_id] = TC.friendPlans[row.user_id] || {})[row.slot] = ids;
  });
  render(true);""", """    if (ids.length) (TC.friendPlans[row.user_id] = TC.friendPlans[row.user_id] || {})[row.slot] = ids;
  });
  UI.feedNew = null;   /* Home works out again who has something new, from the plans just read (spring-wall) */
  render(true);""")

# 7. Fall chip error retries
one("""  mineTermRetry: () => { const t = mineTerm(); if (t && t.code) { delete TC.termMine[t.code]; render(true); } },""",
    """  mineTermRetry: async () => { const t = mineTerm(); if (splitTerms() && t && t.code === nowTerm().code) { await loadNowMine(); relinkPeople(); loadNowSeats(); render(true); return; } if (t && t.code) { delete TC.termMine[t.code]; render(true); } },""")

# 9. "yours" = Spring on Spring screens; Champ friend_profile lists both terms
one("""${esc(CFG.TERM_LABEL)}</span>${myCodes().has(code) ? `<span class="hchip\"""", """${esc(CFG.TERM_LABEL)}</span>${planCodes().has(code) ? `<span class="hchip\"""")
one("""    const mine = myCodes(), both = new Set(ps.map(s => s.code).filter(c => mine.has(c))), n = new Set(ps.map(s => s.code)).size;""",
    """    const mine = planCodes(), both = new Set(ps.map(s => s.code).filter(c => mine.has(c))), n = new Set(ps.map(s => s.code)).size;""")
i = s.index("    case 'friend_profile': {"); j = s.index("\n", i)
line = s[i:j]
old = "personSecs(f).map(s => s.code).concat(PEOPLE[f].unplaced || [])"
assert line.count(old) == 1, line[:200]
s = s[:i] + line.replace(old, "personSecs(f).map(s => s.code).concat(PEOPLE[f].unplaced || [], splitTerms() ? nowSecs(f).map(s => s.code).concat(nowUnplaced(f)) : [])") + s[j:]

# 11. wording + narrow switch
one("""${nw ? `<span class="fnew">${v.k === 'next' ? 'Spring classes added' : 'New plan'}</span>` : ''}""",
    """${nw ? `<span class="fnew">${v.k === 'next' ? esc(String(CFG.TERM_LABEL).split(' ')[0]) + ' classes added' : 'New plan'}</span>` : ''}""")
one(""".fwk-h{display:flex;align-items:center;gap:10px;padding:0 12px 8px 16px;min-height:46px}""",
    """.fwk-h{display:flex;align-items:center;gap:10px;padding:0 12px 8px 16px;min-height:46px;flex-wrap:wrap}""")
f.write_text(s); print('patched', f)
