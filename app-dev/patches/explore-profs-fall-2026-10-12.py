#!/usr/bin/env python3
"""Explore › Professors shows Fall's professors too, with the same term switch as Classes (Tate, 2026-10-12, on a
screenshot of Explore › Professors with "Spring 2027": "make it so professors also show fall professors." / "and you
can toggle between them too").
  - The term words beside Filters are the switch in Professors as well (one switch for both: Fall picked in Classes is
    Fall in Professors). Fall lists every professor teaching a Fall section (the now-term's sections, read once, as
    Classes reads them), each card with their Fall classes; search, the subject filter and Saved work the same.
  - A professor's page lists "Teaching Fall 2026" under "Teaching Spring 2027" once the Fall sections are read (first,
    when Explore is on Fall); a Fall class opens Fall's class page.
Replayable on 18:05.  python3 explore-profs-fall-2026-10-12.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'explore-profs-fall: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)

rep("""const profCourses = pk => [...new Set(SECTIONS.filter(s => s.prof === pk).map(s => s.code))];""",
    """/* (2026-10-12) inside the now-term lens (inNow), what a professor teaches THAT term: one map per read of its sections
   (NOW_GEN counts the reads — addNowRows bumps it) */
let PROF_NOW = { src: null, gen: -1, map: Object.create(null) };
const profCourses = pk => {
  if (LENS_NOW) {
    if (PROF_NOW.src !== SEC || PROF_NOW.gen !== NOW_GEN) { const m = Object.create(null); Object.values(SEC).forEach(x => { if (x.prof) { const a = m[x.prof] || (m[x.prof] = []); if (!a.includes(x.code)) a.push(x.code); } }); PROF_NOW = { src: SEC, gen: NOW_GEN, map: m }; }
    return PROF_NOW.map[pk] || [];
  }
  return [...new Set(SECTIONS.filter(s => s.prof === pk).map(s => s.code))];
};""")
rep("""  if (!p.teaches) return false;
  if (S.savedOnly && !isSaved('p:' + pk)) return false;""",
    """  if (!(LENS_NOW ? profCourses(pk).length : p.teaches)) return false;   /* (2026-10-12) Fall's: teaching a Fall section */
  if (S.savedOnly && !isSaved('p:' + pk)) return false;""")
rep("""const exNow = () => S.exMode === 'classes' && UI.exTerm === 'now' && splitTerms();""",
    """/* (2026-10-12) one switch for Classes and Professors */
const exNow = () => UI.exTerm === 'now' && splitTerms();""")
rep("""    if (!nowAllReady()) { if (NOWT.err && !NOWT.loading && NOWT.term === nowTerm().code) return errCard(`Couldn’t load ${L} classes.`, 'retryNowAll'); loadNowAll(); return loadingCard(`Loading ${L} classes…`); }""",
    """    const what = S.exMode === 'profs' ? 'professors' : 'classes';
    if (!nowAllReady()) { if (NOWT.err && !NOWT.loading && NOWT.term === nowTerm().code) return errCard(`Couldn’t load ${L} ${what}.`, 'retryNowAll'); loadNowAll(); return loadingCard(`Loading ${L} ${what}…`); }""")
rep("""/* The term words beside Filters (Tate, 2026-10-10): in Classes, while there are two terms, they are a switch —
   Spring 2027 (what people pick classes for; always where Explore starts) or Fall 2026 (what friends are in). */""",
    """/* The term words beside Filters (Tate, 2026-10-10): while there are two terms, they are a switch — Spring 2027 (what
   people pick classes for; always where Explore starts) or Fall 2026 (what friends are in). Classes and (2026-10-12)
   Professors alike. */""")
rep("""  if (!(S.exMode === 'classes' && splitTerms())) return `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`;
  const on = exNow(), L = on ? nowTerm().label : CFG.TERM_LABEL, other = on ? CFG.TERM_LABEL : nowTerm().label;
  return `${subj}<button class="exterm muted b" data-a="exTerm" aria-label="${esc('Showing ' + L + ' classes. Switch to ' + other)}">${esc(L)}${ic('updown', 14, 2.6)}</button>`;""",
    """  if (!splitTerms()) return `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`;
  const on = exNow(), L = on ? nowTerm().label : CFG.TERM_LABEL, other = on ? CFG.TERM_LABEL : nowTerm().label;
  return `${subj}<button class="exterm muted b" data-a="exTerm" aria-label="${esc('Showing ' + L + (S.exMode === 'profs' ? ' professors' : ' classes') + '. Switch to ' + other)}">${esc(L)}${ic('updown', 14, 2.6)}</button>`;""")
# the professor's page: Fall's classes too
rep(""" ${profCourses(id).length ? `<div class="card" style="margin:14px 12px 0;padding:16px"><div style="font-weight:900;font-size:17px">Teaching ${esc(CFG.TERM_LABEL)}</div>
  ${profCourses(id).map(c => `<button class="teach" data-a="openClass" data-x="${c}"><span class="code">${c}</span><span class="grow b teach-nm">${esc(course(c).title)}</span><span class="teach-go">${ic('chevR', 20, 2.8)}</span></button>`).join('')}</div>` : ''}""",
    """ ${(() => {
   /* (2026-10-12) what they teach in each term: Spring's, and Fall's once its sections are read (first when Explore is on Fall) */
   const card = (L, cs, now) => cs.length ? `<div class="card prof-teach" style="margin:14px 12px 0;padding:16px"><div style="font-weight:900;font-size:17px">Teaching ${esc(L)}</div>
  ${cs.map(c => `<button class="teach" data-a="openClass" data-x="${c}"${now ? ' data-y="now"' : ''}><span class="code">${c}</span><span class="grow b teach-nm">${esc(now ? ((NOWT.courses[c] || {}).title || c) : course(c).title)}</span><span class="teach-go">${ic('chevR', 20, 2.8)}</span></button>`).join('')}</div>` : '';
   const sp = card(CFG.TERM_LABEL, profCourses(id), false), fa = splitTerms() && nowAllReady() ? card(nowTerm().label, inNow(() => profCourses(id)), true) : '';
   return exNow() ? fa + sp : sp + fa;
 })()}""")
rep("""function addNowRows(box, rows, t) {
  rows.forEach(r => {""", """let NOW_GEN = 0;
function addNowRows(box, rows, t) {
  NOW_GEN++;
  rows.forEach(r => {""")
# a professor's page reads Fall's sections when it hasn't yet (opened from a Fall class page, Home, a friend's sheet)
rep("""  if (!p._loadedReviews) { p._loadedReviews = true; TC.loadProfReviews(id); }
  const r = ratingOf(id), st = reviewStats(id), mine = iReviewed(id);""", """  if (!p._loadedReviews) { p._loadedReviews = true; TC.loadProfReviews(id); }
  if (splitTerms() && !nowAllReady() && !NOWT.err) loadNowAll();   /* (2026-10-12) their Fall classes */
  const r = ratingOf(id), st = reviewStats(id), mine = iReviewed(id);""")
# Recents: a Fall-only professor isn't one Spring's list can show (like a Fall class)
rep("""  openProf: (id, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim()) recentAdd('p', id);""",
    """  openProf: (id, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim() && !exNow()) recentAdd('p', id);""")
p.write_text(s)
print('explore-profs-fall: applied')
