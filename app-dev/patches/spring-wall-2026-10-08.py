#!/usr/bin/env python3
"""Spring 2027 for everything you choose; Fall 2026 for where people are right now (Tate, 2026-10-08).

Tate: "once people start trying to register, we need to change everything over to spring 2027. That
includes professors, classes in the schedule, plans, schedule builder ... if it's fall 2026, it could show
a class that's not offered at a time. So we have to create a wall between these two ... For stories, it's
going to be the current schedule you're in ... for the home feed, we want a mix of the current classes
people are in, but also mainly the classes they're planning ... We should also display plans in the feed."
Then, on the recommendation: "whatever your recommendation is ... lets wire it in".

THE WALL. Two terms, never mixed:
- CFG.TERM (Spring 2027, 2274) is the term you CHOOSE in. The seat feed, Explore, class and professor
  pages, Plans, the Planner's picks, Add to your week, seat alerts, the share of My Classes and Champ's
  "does it fit" answers read only its sections, and every write (My Classes, plans, watches) goes to it.
- CFG.NOW_TERM (Fall 2026, 2268) is the term people are SITTING in: stories, rings and "free now", a
  story's day, Champ's "when am I free", and the Fall chip on My Classes and a friend's week. Its
  sections are read by class number from the now-term's seat rows into NOW_SEC (ids "n:<term>:<nbr>",
  so a Fall number can never be taken for the Spring section with the same number) and are never added
  to COURSES, SECTIONS, SEC or a professor's "teaching this term".
- From CFG.NOW_UNTIL (2027-01-25, Spring's first day of classes, Pacific) "now" is TERM by itself.
- With NOW_TERM equal to TERM (or empty) the app is exactly the single-term app it was.

HOME. Each friend's card shows the newest real thing they have: their Spring classes, else their first
shared Spring plan (in its colour), else their week now — with a tag saying which ("Spring 2027
classes", "Plan A · Spring 2027", "Now · Fall 2026"). A friend whose Spring classes or plan changed since
you last opened Home goes to the top with "New plan" / "Spring classes added", once. The swipe row of
classes becomes "Classes your friends are planning" (their Spring classes and shared plans), falling back
to "taking" (their current classes that are offered in Spring). A friend's page switches Fall · Spring ·
A · B · C and opens on the same view as their Home card.

MY CLASSES. Chips Fall 2026 · Spring 2027. Spring is your editable My Classes; Fall is read-only. It
opens on Fall until you've added a Spring class (your pick is remembered).

DEGREE PROGRESS REPORT. In-progress (this term) classes go to Fall's My Classes, and classes you're
registered for in Spring go to Spring's — before, after the flip the report would have filed Fall's
in-progress classes as finished.

Also: CFG is merged over (PROFESSIFY_CONFIG wins key by key) so a page can set just the terms.

Usage: python3 spring-wall-2026-10-08.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'spring-wall (2026-10-08)' in s:
    sys.exit('already patched')

def opt(old, new):   # merge onto the report flow: the old DPR sheet may be gone
    global s
    n = s.count(old)
    assert n <= 1, (n, old[:100])
    if n: s = s.replace(old, new)
    else: print('  (not here: ' + old.strip()[:60] + ')')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:100])
    s = s.replace(old, new)

# ---------------------------------------------------------------- config
one("window.PROFESSIFY_CONFIG = window.PROFESSIFY_CONFIG || {", "window.PROFESSIFY_CONFIG = Object.assign({")
one("""  /* THE TERM — keep these two equal to TERM / TERM_LABEL in the desktop index.html. */
  TERM: '2268',
  TERM_LABEL: 'Fall 2026',""", """  /* THE TERMS (spring-wall (2026-10-08)). TERM is the term students CHOOSE in: the seat feed, Explore,
     class and professor pages, Plans, the Planner, Add to your week, seat alerts and Champ read only its
     sections, and every write goes to it. NOW_TERM is the term they are SITTING in: stories, rings,
     "free now", a story's day and Home's current weeks. From NOW_UNTIL (TERM's first day of classes,
     Pacific) TERM is both. NOW_TERM empty or equal to TERM = the single-term app. The desktop
     index.html is still on Fall 2026 (TERM 2268). */
  TERM: '2274',
  TERM_LABEL: 'Spring 2027',
  NOW_TERM: '2268',
  NOW_LABEL: 'Fall 2026',
  NOW_UNTIL: '2027-01-25',""")
one("  MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '', label: 'Spring 2027' }],",
    "  MY_TERMS: [{ code: '2268', label: 'Fall 2026' }, { code: '2274', label: 'Spring 2027' }],")
one("""  GA_MEASUREMENT_ID: 'G-L98ZTJQ1LY'
};
const CFG = window.PROFESSIFY_CONFIG;""", """  GA_MEASUREMENT_ID: 'G-L98ZTJQ1LY'
}, window.PROFESSIFY_CONFIG || {});
const CFG = window.PROFESSIFY_CONFIG;
/* ---- The wall between the two terms (spring-wall (2026-10-08)) ---- */
function sloYmd() {
  try { const p = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date()).forEach(x => { p[x.type] = x.value; }); return p.year + '-' + p.month + '-' + p.day; }
  catch (e) { return new Date().toISOString().slice(0, 10); }
}
/* the term people are in right now: NOW_TERM until TERM's classes start, then TERM */
function nowTerm() {
  const code = String(CFG.NOW_TERM || '').trim(), until = String(CFG.NOW_UNTIL || '').trim();
  if (!code || code === CFG.TERM || (until && sloYmd() >= until)) return { code: CFG.TERM, label: CFG.TERM_LABEL };
  return { code, label: String(CFG.NOW_LABEL || code) };
}
const splitTerms = () => nowTerm().code !== CFG.TERM;""")

# ---------------------------------------------------------------- now-term seats (by class number only)
one("""const SEATS_CACHE = 'termchamp_app_seats_v1';""", """const SEATS_CACHE = 'termchamp_app_seats_v1';
/* The sections people are in right now (spring-wall): read by class number from the now-term's seat rows.
   They live only here — never in COURSES, SECTIONS, SEC or a professor's "teaching this term" — so
   Explore, class pages, plans and Add to your week can't offer a class that isn't in TERM. A number the
   rows don't have (left the list) keeps the student's own meeting string, as before. */
const NOW_SEC = {}, NOW_TITLES = {}; let NOW_SEC_TERM = '';
function nowSecOf(r, t) {
  const code = canonCode(r.course_code), nbr = String(r.class_nbr || '').trim(); if (!code || !nbr) return null;
  const m = parseMeet(r.days), av = r.available == null ? null : Math.max(0, r.available), st = seatStatusOf(r.status, av || 0), pk = profKeyOf(r.instructor);
  if (pk) ensureProf(pk);
  if (r.title && !NOW_TITLES[code]) NOW_TITLES[code] = String(r.title).trim();
  return { id: 'n:' + t + ':' + nbr, nbr, code, sec: String(r.section || '').trim(), prof: pk, days: m ? m.days : '', s: m ? m.s : null, e: m ? m.e : null,
    async: false, noTime: !m, seats: st === 'open' ? av : (st === 'unknown' ? null : 0), status: st, cap: r.capacity, wl: r.waitlist_total || 0,
    rawDays: r.days || '', instructor: String(r.instructor || '').trim(), nowTerm: t };
}
async function loadNowSeats() {
  if (!splitTerms() || !TC.user) return;
  const t = nowTerm().code;
  if (NOW_SEC_TERM !== t) { Object.keys(NOW_SEC).forEach(k => { delete NOW_SEC[k]; }); NOW_SEC_TERM = t; }
  const want = new Set();
  const take = rows => (rows || []).forEach(r => { const n = r && r.class_nbr != null ? String(r.class_nbr).trim() : ''; if (/^\\d{3,6}$/.test(n) && !Object.prototype.hasOwnProperty.call(NOW_SEC, n)) want.add(n); });
  if (TC.nowMineRows) take(TC.nowMineRows.secs);
  Object.values(TC.friendNowRows || {}).forEach(b => take(b.secs));
  if (!want.size) return;
  const base = CFG.SUPABASE_URL.replace(/\\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const sel = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr', list = [...want];
  try {
    for (let i = 0; i < list.length; i += 80) {
      const part = list.slice(i, i + 80);
      const res = await fetch(base + '/rest/v1/course_seats?term=eq.' + encodeURIComponent(t) + '&class_nbr=in.(' + part.join(',') + ')&select=' + sel, { headers: hdr });
      if (!res.ok) break;
      const got = await res.json(); if (!Array.isArray(got)) break;
      got.forEach(r => { const x = nowSecOf(r, t); if (x) NOW_SEC[x.nbr] = x; });
      part.forEach(n => { if (!Object.prototype.hasOwnProperty.call(NOW_SEC, n)) NOW_SEC[n] = null; });
    }
  } catch (e) {}
  relinkPeople(); render(true);
}""")

one("const course = code => COURSES[code] || { title: code, short: code, desc: null, prereq: null };",
    "const course = code => COURSES[code] || (NOW_TITLES[code] ? { title: NOW_TITLES[code], short: shortTitle(NOW_TITLES[code]), desc: null, prereq: null } : { title: code, short: code, desc: null, prereq: null });")

# ---------------------------------------------------------------- your classes in both terms
one("""  TC.mineRows = { secs: secs.error ? [] : (secs.data || []), saved: mine };
  relinkPeople();
}""", """  TC.mineRows = { secs: secs.error ? [] : (secs.data || []), saved: mine };
  if (splitTerms()) await loadNowMine(); else { TC.nowMineRows = null; delete TC.err.nowMine; }
  relinkPeople();
}
/* Your classes in the term you're in right now (spring-wall): read-only here, drawn on the Fall chip,
   your rings and Champ's "when am I free". */
async function loadNowMine() {
  const t = nowTerm().code, sb = TC.client(), me = TC.user.id;
  let codes, secs;
  try {
    [codes, secs] = await Promise.all([
      sb.from('saved_classes').select('code').eq('user_id', me).eq('term', t),
      sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id', me).eq('term', t)
    ]);
  } catch (e) { codes = { error: { message: String(e) } }; }
  if (codes.error) { TC.err.nowMine = codes.error.message || 'error'; return; }
  delete TC.err.nowMine;
  TC.nowMineRows = { secs: secs && !secs.error ? (secs.data || []) : [], saved: [...new Set((codes.data || []).map(r => canonCode(r.code)).filter(Boolean))] };
}""")

one("function secsFromRows(uid, rows, saved) {\n  const out = [], unplaced = [], keep = new Set(saved || []);",
    "function secsFromRows(uid, rows, saved, look, idp) {\n  const out = [], unplaced = [], keep = new Set(saved || []), L = look || (n => SEC[n]);   /* look: the now-term's sections (spring-wall) */")
one("""    if (nbr && SEC[nbr]) { out.push(r.status === 'waitlisted' ? Object.assign({}, SEC[nbr], { mineWl: true, wlPos: r.wl_pos == null ? null : r.wl_pos }) : SEC[nbr]); return; }""",
    """    const hit = nbr ? L(nbr) : null;
    if (hit) { out.push(r.status === 'waitlisted' ? Object.assign({}, hit, { mineWl: true, wlPos: r.wl_pos == null ? null : r.wl_pos }) : hit); return; }""")
one("""out.push({ id: 'x:' + uid + ':' + code + ':' + nbr, code, sec: r.section || '',""",
    """out.push({ id: (idp || 'x') + ':' + uid + ':' + code + ':' + nbr, code, sec: r.section || '',""")
one("""  (TC.friendRows ? Object.keys(TC.friendRows) : []).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendRows[uid].secs, TC.friendRows[uid].saved); PEOPLE[uid].secs = m.secs; PEOPLE[uid].unplaced = m.unplaced; });
}""", """  (TC.friendRows ? Object.keys(TC.friendRows) : []).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendRows[uid].secs, TC.friendRows[uid].saved); PEOPLE[uid].secs = m.secs; PEOPLE[uid].unplaced = m.unplaced; });
  /* the term people are in right now (spring-wall): its own rows, looked up only in NOW_SEC */
  if (!splitTerms()) return;
  const nowLook = n => NOW_SEC[n] || null;
  if (TC.nowMineRows) { const m = secsFromRows('me', TC.nowMineRows.secs, TC.nowMineRows.saved, nowLook, 'xn'); PEOPLE.me.nowSecs = m.secs; PEOPLE.me.nowUnplaced = m.unplaced; }
  Object.keys(TC.friendNowRows || {}).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendNowRows[uid].secs, TC.friendNowRows[uid].saved, nowLook, 'xn'); PEOPLE[uid].nowSecs = m.secs; PEOPLE[uid].nowUnplaced = m.unplaced; });
}""")

# ---------------------------------------------------------------- friends' rows in both terms
one("""  TC.friendRows = {}; delete TC.err.friendSecs;
  if (ids.length) {
    const [secs, saved, hist] = await Promise.all([
      sb.from('my_sections').select('user_id,code,class_nbr,section,instructor,days,status').in('user_id', ids).eq('term', CFG.TERM),
      sb.from('saved_classes').select('user_id,code').in('user_id', ids).eq('term', CFG.TERM),""",
"""  TC.friendRows = {}; TC.friendNowRows = {}; delete TC.err.friendSecs;
  if (ids.length) {
    /* both terms in one read when they differ (spring-wall); a row goes to the term it names */
    const split = splitTerms(), nowT = nowTerm().code, byTerm = q => split ? q.in('term', [CFG.TERM, nowT]) : q.eq('term', CFG.TERM);
    const [secs, saved, hist] = await Promise.all([
      byTerm(sb.from('my_sections').select('user_id,code,class_nbr,section,instructor,days,status' + (split ? ',term' : '')).in('user_id', ids)),
      byTerm(sb.from('saved_classes').select('user_id,code' + (split ? ',term' : '')).in('user_id', ids)),""")
one("""    ids.forEach(id => { TC.friendRows[id] = { secs: [], saved: [] }; });
    if (!secs.error) (secs.data || []).forEach(r => { if (TC.friendRows[r.user_id]) TC.friendRows[r.user_id].secs.push(r); });
    else TC.err.friendSecs = secs.error.message;
    if (!saved.error) (saved.data || []).forEach(r => { const c = canonCode(r.code); if (c && TC.friendRows[r.user_id]) TC.friendRows[r.user_id].saved.push(c); });""",
"""    ids.forEach(id => { TC.friendRows[id] = { secs: [], saved: [] }; if (split) TC.friendNowRows[id] = { secs: [], saved: [] }; });
    const boxOf = r => split && String(r.term) !== String(CFG.TERM) ? TC.friendNowRows[r.user_id] : TC.friendRows[r.user_id];
    if (!secs.error) (secs.data || []).forEach(r => { const b = boxOf(r); if (b) b.secs.push(r); });
    else TC.err.friendSecs = secs.error.message;
    if (!saved.error) (saved.data || []).forEach(r => { const c = canonCode(r.code), b = boxOf(r); if (c && b) b.saved.push(c); });""")

one("""  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads()), loadAudit(), loadPrefs()]);
  loadSuggestions(); loadRateList(); loadFriendPlans();""",
"""  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads()), loadAudit(), loadPrefs()]);
  loadSuggestions(); loadRateList(); loadFriendPlans(); loadNowSeats();""")
one("""async function loadFriendPlans() {
""", """async function loadFriendPlans() {
  UI.feedNew = null;   /* Home works out again who has something new (spring-wall) */
""")

# ---------------------------------------------------------------- derived: now vs plan
one("""const myCodes = () => new Set(personSecs('me').map(s => s.code).concat(PEOPLE.me.unplaced || []));""",
"""/* spring-wall (2026-10-08): personSecs = the term you choose in (TERM); nowSecs = the term people are
   in right now. One and the same when the terms are. */
const nowSecs = id => splitTerms() ? ((PEOPLE[id] && PEOPLE[id].nowSecs) || []) : personSecs(id);
const nowUnplaced = id => splitTerms() ? ((PEOPLE[id] && PEOPLE[id].nowUnplaced) || []) : ((PEOPLE[id] && PEOPLE[id].unplaced) || []);
const planCodes = () => new Set(personSecs('me').map(s => s.code).concat(PEOPLE.me.unplaced || []));
const nowCodes = () => new Set(nowSecs('me').map(s => s.code).concat(nowUnplaced('me')));
/* everything you're taking or registered for — what picks and prerequisites count as yours */
const myCodes = () => new Set([...planCodes(), ...nowCodes()]);""")
one("""  if (!personSecs(id).length) return { c: null, rc: isDark() ? '#3A4660' : '#CBD5E1', t: (PEOPLE[id] && (PEOPLE[id].unplaced || []).length) ? 'Class times not added' : 'No classes added', free: null };""",
    """  if (!nowSecs(id).length) return { c: null, rc: isDark() ? '#3A4660' : '#CBD5E1', t: nowUnplaced(id).length ? 'Class times not added' : 'No classes added', free: null };""")
one("""const friendsInSec = id => TC.friends.filter(f => personSecs(f).some(s => s.id === id));""",
    """const friendsInSec = id => TC.friends.filter(f => personSecs(f).some(s => s.id === id));
const nowFriendsIn = code => TC.friends.filter(f => nowSecs(f).some(s => s.code === code) || nowUnplaced(f).includes(code));
const nowFriendsInSec = id => TC.friends.filter(f => nowSecs(f).some(s => s.id === id));
/* a section of the term people are in right now (never on a TERM list) */
const isNowSecId = id => splitTerms() && /^(n|xn):/.test(String(id));""")
one("""function todaySecs(id) { return personSecs(id).filter(""", """function todaySecs(id) { return nowSecs(id).filter(""")

# ---------------------------------------------------------------- a story's day = now
one("""  const st = status(id), now = CLOCK.min, today = todaySecs(id), mine = personSecs('me');""",
    """  const st = status(id), now = CLOCK.min, today = todaySecs(id), mine = nowSecs('me');""")
one("""  const all = personSecs(id), anyC = [...new Set(all.filter(x => x.async || x.s == null || x.e == null).map(x => x.code).concat((p.unplaced || []).filter(c => !all.some(x => x.code === c))))]""",
    """  const all = nowSecs(id), anyC = [...new Set(all.filter(x => x.async || x.s == null || x.e == null).map(x => x.code).concat(nowUnplaced(id).filter(c => !all.some(x => x.code === c))))]""")
one("""  const withThem = x => { const w = friendsInSec(x.id).filter(f => f !== id), me = mine.some(y => y.id === x.id);""",
    """  const withThem = x => { const w = nowFriendsInSec(x.id).filter(f => f !== id), me = mine.some(y => y.id === x.id);""")

# ---------------------------------------------------------------- a section's preview knows its term
one("""function secPeople(code, id) {
  const meIn = personSecs('me').some(x => x.id === id), meCode = myCodes().has(code);
  const here = (meIn ? ['me'] : []).concat(friendsInSec(id));
  const other = (!meIn && meCode ? ['me'] : []).concat(friendsIn(code).filter(f => !here.includes(f)));""",
"""function secPeople(code, id) {
  const isNow = isNowSecId(id), sf = isNow ? nowSecs : personSecs;   /* only people in the same term (spring-wall) */
  const meIn = sf('me').some(x => x.id === id), meCode = (isNow ? nowCodes() : planCodes()).has(code);
  const here = (meIn ? ['me'] : []).concat(isNow ? nowFriendsInSec(id) : friendsInSec(id));
  const other = (!meIn && meCode ? ['me'] : []).concat((isNow ? nowFriendsIn(code) : friendsIn(code)).filter(f => !here.includes(f)));""")
one("""  const s = SEC[id] || personSecs('me').find(x => x.id === id) || TC.friends.map(f => personSecs(f).find(x => x.id === id)).find(Boolean); if (!s) return '';
  const c = course(code), who = secPeople(code, id), inP = TC.plans[S.plan].includes(id), w = !!TC.watches[id];""",
"""  const s = SEC[id] || personSecs('me').find(x => x.id === id) || TC.friends.map(f => personSecs(f).find(x => x.id === id)).find(Boolean)
    || nowSecs('me').find(x => x.id === id) || TC.friends.map(f => nowSecs(f).find(x => x.id === id)).find(Boolean); if (!s) return '';
  const c = course(code), who = secPeople(code, id), inP = TC.plans[S.plan].includes(id), w = !!TC.watches[id];
  const termTag = splitTerms() ? `<span class="secterm">${esc(isNowSecId(id) ? nowTerm().label : CFG.TERM_LABEL)}</span> · ` : '';""")
one("""<h3 style="margin-top:10px">${esc(c.title)}</h3><div class="b secwhen" style="margin-top:4px;font-size:14px"><span class="muted">${secWhen(s)}</span> · ${secSeatText(s)}</div>""",
    """<h3 style="margin-top:10px">${esc(c.title)}</h3><div class="b secwhen" style="margin-top:4px;font-size:14px">${termTag}<span class="muted">${secWhen(s)}</span> · ${secSeatText(s)}</div>""")

# ---------------------------------------------------------------- Home: what each card shows
one("""function homeWeekCard(id) {
  const isMe = id === 'me', P = PEOPLE[id], mine = myCodes();
  const secs = personSecs(id);
  const shared = new Set(isMe ? [] : secs.map(s => s.code).filter(c => mine.has(c)));
  const st = isMe ? null : status(id);
  const unplaced = P.unplaced || [];""",
"""/* What a Home card shows (spring-wall (2026-10-08)): the newest real thing someone has — their Spring
   classes, else their first shared Spring plan, else their week right now. */
function feedView(id) {
  const P = PEOPLE[id] || {};
  if (!splitTerms()) return { k: 'now', secs: personSecs(id), unplaced: P.unplaced || [] };
  if (personSecs(id).length || (P.unplaced || []).length) return { k: 'next', secs: personSecs(id), unplaced: P.unplaced || [] };
  const fp = id === 'me' ? TC.plans : (TC.friendPlans && !TC.err.friendPlans ? TC.friendPlans[id] : null);
  const has = x => Object.prototype.hasOwnProperty.call(SEC, x);
  const slot = fp && ['A', 'B', 'C'].find(k => (fp[k] || []).some(has));
  if (slot) return { k: slot, secs: fp[slot].filter(has).map(x => SEC[x]), unplaced: [] };
  return { k: 'now', secs: nowSecs(id), unplaced: nowUnplaced(id) };
}
const feedLabel = k => k === 'now' ? nowTerm().label : k === 'next' ? CFG.TERM_LABEL : 'Plan ' + k + ' · ' + CFG.TERM_LABEL;
function feedTag(id, v) {
  if (!splitTerms()) return '';
  const nw = (UI.feedNew || []).includes(id);
  return `<div class="fviews"><span class="fview${/^[ABC]$/.test(v.k) ? ' plan-' + v.k : v.k === 'next' ? ' next' : ''}">${esc(v.k === 'now' ? 'Now · ' + nowTerm().label : v.k === 'next' ? CFG.TERM_LABEL + ' classes' : feedLabel(v.k))}</span>${nw ? `<span class="fnew">${v.k === 'next' ? 'Spring classes added' : 'New plan'}</span>` : ''}</div>`;
}
/* Friends whose Spring classes or shared plan changed since you last opened Home: first in the feed, with
   a tag, once. Worked out when friends and their plans have loaded; remembered on this phone per account. */
function feedSig(id) { const v = feedView(id); return v.k === 'now' ? 'now' : v.k + ':' + v.secs.map(x => x.id).concat(v.unplaced).sort().join(','); }
function feedNew() {
  if (!splitTerms() || !TC.ready || !TC.user || !(TC.friendPlans || TC.err.friendPlans)) return [];
  if (UI.feedNew) return UI.feedNew;
  const key = 'tc-feed-seen:' + TC.user.id, sig = {};
  let seen = null; try { seen = JSON.parse(localStorage.getItem(key) || 'null'); } catch (e) {}
  TC.friends.forEach(f => { sig[f] = feedSig(f); });
  UI.feedNew = seen && typeof seen === 'object' ? TC.friends.filter(f => sig[f] !== 'now' && Object.prototype.hasOwnProperty.call(seen, f) && seen[f] !== sig[f]) : [];
  try { localStorage.setItem(key, JSON.stringify(sig)); } catch (e) {}
  return UI.feedNew;
}
function homeWeekCard(id) {
  const isMe = id === 'me', P = PEOPLE[id], v = feedView(id), mine = v.k === 'now' ? nowCodes() : planCodes();
  const secs = v.secs;
  const shared = new Set(isMe ? [] : secs.map(s => s.code).filter(c => mine.has(c)));
  const st = isMe ? null : status(id);
  const unplaced = v.unplaced;""")
one("""  else week = grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300 }) + anyRow;""",
    """  else week = (/^[ABC]$/.test(v.k) ? `<div class="plancol plan-${v.k}">` : '') + grid(secs, { sel: S.homeDays[id], act: 'homeDay', key: id, blockAct: 'secSheet', shared, one: true, fit: 30, H: 300 }) + (/^[ABC]$/.test(v.k) ? '</div>' : '') + anyRow;""")
one("""    ${isMe ? `<span class="pillchip">${esc(CFG.TERM_LABEL)} · ${nClasses} class${nClasses === 1 ? '' : 'es'}</span>` : ''}""",
    """    ${isMe ? `<span class="pillchip">${esc(feedLabel(v.k))} · ${nClasses} class${nClasses === 1 ? '' : 'es'}</span>` : feedTag(id, v)}""")
one("""  const feed = TC.friends.length ? (cards => { const at = Math.min(3, cards.length); cards.splice(at, 0, recsRow(friendClassRecs())); return cards; })(feedOrder().map(homeWeekCard)).join('')""",
    """  const feed = TC.friends.length ? (cards => { const at = Math.min(3, cards.length); cards.splice(at, 0, recsRow(friendClassRecs())); return cards; })((n => n.length ? n.concat(feedOrder().filter(f => !n.includes(f))) : feedOrder())(feedNew()).map(homeWeekCard)).join('')""")

# ---------------------------------------------------------------- the swipe row: planning first
one("""  TC.friends.forEach(fr => { personSecs(fr).forEach(x => add(x.code, fr, x.prof)); (PEOPLE[fr].unplaced || []).forEach(c => add(c, fr, null)); });""",
"""  TC.friends.forEach(fr => { personSecs(fr).forEach(x => add(x.code, fr, x.prof)); (PEOPLE[fr].unplaced || []).forEach(c => add(c, fr, null)); });
  /* spring-wall: friends' shared Spring plans count as planning; with nobody planning yet, the classes
     they're in now — only those offered in TERM, so a card never opens a class with no sections */
  const split = splitTerms();
  if (split) { const fp = TC.friendPlans || {}; TC.friends.forEach(fr => ['A', 'B', 'C'].forEach(k => ((fp[fr] || {})[k] || []).forEach(x => { const s = Object.prototype.hasOwnProperty.call(SEC, x) ? SEC[x] : null; if (s) add(s.code, fr, s.prof); }))); }
  TC.recsPlanning = split && Object.keys(by).length > 0;
  if (split && !TC.recsPlanning) TC.friends.forEach(fr => { nowSecs(fr).forEach(x => { if (secsOf(x.code).length) add(x.code, fr, null); }); nowUnplaced(fr).forEach(c => { if (secsOf(c).length) add(c, fr, null); }); });""")
one("""  return `<section class="recs" aria-label="Suggested: classes your friends are taking"><div class="recs-h"><span>Classes your friends are taking</span>""",
    """  const what = TC.recsPlanning ? 'planning' : 'taking';
  return `<section class="recs" aria-label="Suggested: classes your friends are ${what}"><div class="recs-h"><span>Classes your friends are ${what}</span>""")

# ---------------------------------------------------------------- a friend's week: Fall · Spring · A · B · C
one("""  const k = slots.includes(UI.fplan[id]) ? UI.fplan[id] : 'now', season = String(CFG.TERM_LABEL).split(' ')[0];
  const sw = slots.length ? `<span class="fsw" role="group" aria-label="Show ${esc(p.short)}’s week or a plan">${['now'].concat(slots).map(x => `<button class="${x === 'now' ? '' : 'plan-' + x}${x === k ? ' on' : ''}" data-a="friendPlan" data-x="${id}" data-y="${x}" aria-pressed="${x === k}" aria-label="${x === 'now' ? esc(CFG.TERM_LABEL) : 'Plan ' + x}">${x === 'now' ? esc(season) : x}</button>`).join('')}</span>`""",
"""  /* spring-wall: Fall (now) · Spring (their Spring classes) · A · B · C; opens on what their Home card shows */
  const split = splitTerms(), hasNext = split && (personSecs(id).length || (p.unplaced || []).length) ? ['next'] : [];
  const chips = ['now'].concat(hasNext, slots), fv = split ? feedView(id).k : 'now';
  const k = chips.includes(UI.fplan[id]) ? UI.fplan[id] : chips.includes(fv) ? fv : 'now';
  const nowLab = split ? nowTerm().label : CFG.TERM_LABEL, season = String(nowLab).split(' ')[0], nextSeason = String(CFG.TERM_LABEL).split(' ')[0];
  if (split && (k === 'now' || k === 'next')) {
    secs = k === 'now' ? nowSecs(id) : personSecs(id);
    const mc = k === 'now' ? nowCodes() : planCodes();
    shared = new Set(secs.map(s => s.code).concat(k === 'now' ? nowUnplaced(id) : (p.unplaced || [])).filter(c => mc.has(c)));
  }
  const unp = split && k === 'now' ? nowUnplaced(id) : (p.unplaced || []), headLab = k === 'next' ? CFG.TERM_LABEL : nowLab;
  const sw = chips.length > 1 ? `<span class="fsw" role="group" aria-label="Show ${esc(p.short)}’s week or a plan">${chips.map(x => `<button class="${x === 'now' ? '' : x === 'next' ? 'next' : 'plan-' + x}${x === k ? ' on' : ''}" data-a="friendPlan" data-x="${id}" data-y="${x}" aria-pressed="${x === k}" aria-label="${x === 'now' ? esc(nowLab) : x === 'next' ? esc(CFG.TERM_LABEL) : 'Plan ' + x}">${x === 'now' ? esc(season) : x === 'next' ? esc(nextSeason) : x}</button>`).join('')}</span>`""")
one("""  if (k === 'now') {
    const codes = [...new Set(secs.map(s => s.code))];
    head = esc(CFG.TERM_LABEL);
    body = secs.length ? grid(secs, { sel: S.homeDays['f:' + id], act: 'homeDay', key: 'f:' + id, blockAct: 'secSheet', shared, one: true, H: 280 })
      : `<div class="fwk-n" style="padding-top:0">No ${esc(CFG.TERM_LABEL)} sections added.</div>`;
    list = codes.map(code => row(code, secWhen(secs.find(x => x.code === code)), shared.has(code) ? 'Shared' : '')).join('')
      + (p.unplaced || []).map(code => row(code, 'No section yet', shared.has(code) ? 'Shared' : '')).join('')
      + (!codes.length && !(p.unplaced || []).length ? `<div class="empty"><b>No ${esc(CFG.TERM_LABEL)} classes added</b></div>` : '');""",
"""  if (k === 'now' || k === 'next') {
    const codes = [...new Set(secs.map(s => s.code))];
    head = esc(headLab);
    body = secs.length ? grid(secs, { sel: S.homeDays['f:' + id + (k === 'next' ? ':n' : '')], act: 'homeDay', key: 'f:' + id + (k === 'next' ? ':n' : ''), blockAct: 'secSheet', shared, one: true, H: 280 })
      : `<div class="fwk-n" style="padding-top:0">No ${esc(headLab)} sections added.</div>`;
    list = codes.map(code => row(code, secWhen(secs.find(x => x.code === code)), shared.has(code) ? 'Shared' : '')).join('')
      + unp.map(code => row(code, 'No section yet', shared.has(code) ? 'Shared' : '')).join('')
      + (!codes.length && !unp.length ? `<div class="empty"><b>No ${esc(headLab)} classes added</b></div>` : '');""")
one("""  friendPlan: (id, k) => { UI.fplan = UI.fplan || {}; UI.fplan[id] = k === 'now' ? null : k; render(true); },""",
    """  friendPlan: (id, k) => { UI.fplan = UI.fplan || {}; UI.fplan[id] = k; render(true); },""")

# ---------------------------------------------------------------- My Classes: Fall (read-only) · Spring
one("""function mineTerm() { const L = myTerms(); return L.find(t => t.label === S.mineTerm) || L.find(t => t.code === CFG.TERM); }""",
"""function mineTerm() {
  const L = myTerms(), pick = L.find(t => t.label === S.mineTerm); if (pick) return pick;
  /* spring-wall: until you've added a Spring class, My Classes opens on the term you're in */
  if (splitTerms() && TC.mineRows && !TC.mineRows.saved.length) { const n = L.find(t => t.code === nowTerm().code); if (n) return n; }
  return L.find(t => t.code === CFG.TERM);
}""")
one("""  pickMineTerm: k => { const t = myTerms().find(x => x.label === k); S.mineTerm = t && t.code !== CFG.TERM ? k : null;""",
    """  pickMineTerm: k => { const t = myTerms().find(x => x.label === k); S.mineTerm = t && (t.code !== CFG.TERM || splitTerms()) ? k : null;""")
one("""function termSecs(code) {
  const box = TC.termMine[code]; if (!box || !box.rows) return null;""",
"""function termSecs(code) {
  if (splitTerms() && code === nowTerm().code && TC.nowMineRows) return { secs: nowSecs('me'), unplaced: nowUnplaced('me') };   /* spring-wall */
  const box = TC.termMine[code]; if (!box || !box.rows) return null;""")
one("""  const box = TC.termMine[tm.code];
  if (!box) { loadTermMine(tm.code); return loadingCard('Loading your ' + tm.label + ' classes…'); }""",
"""  const isNowT = splitTerms() && tm.code === nowTerm().code;   /* spring-wall: the term you're in is already loaded */
  const box = isNowT ? (TC.err.nowMine ? { err: TC.err.nowMine } : TC.nowMineRows ? { rows: TC.nowMineRows.secs } : { loading: true }) : TC.termMine[tm.code];
  if (!box) { loadTermMine(tm.code); return loadingCard('Loading your ' + tm.label + ' classes…'); }""")
one("""(TC.termMine[tm.code].rows || []).some(r => canonCode(r.c""", """(box.rows || []).some(r => canonCode(r.c""")
one("""  ${TC.mineRows && !secs.length && !unplaced.length ? `<div class="empty"><b>No classes yet</b>Find your classes in Explore and tap + to add them.</div>` : ''}""",
    """  ${TC.mineRows && !secs.length && !unplaced.length ? (splitTerms() ? `<div class="empty"><b>No ${esc(CFG.TERM_LABEL)} classes yet</b>Once you’ve registered, add them from Explore (tap + on a class), or upload your Degree Progress Report.</div>` : `<div class="empty"><b>No classes yet</b>Find your classes in Explore and tap + to add them.</div>`) : ''}""")

# ---------------------------------------------------------------- Champ: "when am I free" is now
for old in [
    "function chDaySecs(id, d) { return personSecs(id).filter(",
]:
    one(old, old.replace('personSecs(', 'nowSecs('))
for old in [
    "  if (!personSecs('me').some(chTimed)) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.`, acts: [['Open Schedule', 'tab', 'schedule']] };\n  const l = chDaySecs('me', d)",
    "  return TC.friends.filter(f => personSecs(f).some(chTimed)).map(f => {",
    "  if (!personSecs('me').some(chTimed)) return { t: `Add your ${esc(CFG.TERM_LABEL)} classes and I can match your free time with friends’.`",
    "  if (!l.length) return { t: TC.friends.some(f => personSecs(f).some(chTimed))",
    "  if (!personSecs('me').some(chTimed)) return { t: `None of your ${esc(CFG.TERM_LABEL)} classes have set times yet, so I can’t match your free time with ${nm}’s.`",
    "  if (!personSecs(f).some(chTimed)) return { t: `None of ${nm}’s ${esc(CFG.TERM_LABEL)} classes have set times, so I can’t match your free time.`",
]:
    one(old, old.replace('personSecs(', 'nowSecs(').replace('esc(CFG.TERM_LABEL)', 'esc(nowTerm().label)'))
# the week's free time (the second "You haven't added … classes with times yet")
i = s.index("function ansDayCard(d, mode)")
j = s.index("  if (!personSecs('me').some(chTimed)) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.`", i + 10)
old = "  if (!personSecs('me').some(chTimed)) return { t: `You haven’t added ${esc(CFG.TERM_LABEL)} classes with times yet.`"
s = s[:j] + old.replace('personSecs(', 'nowSecs(').replace('esc(CFG.TERM_LABEL)', 'esc(nowTerm().label)') + s[j + len(old):]

# ---------------------------------------------------------------- Degree Progress Report: each term to its own
one("""  const [ct, cy] = CFG.TERM_LABEL.split(' '), cur = key(ct, cy);""",
    """  /* spring-wall: in progress = the term you're in (to its My Classes); registered for TERM when that's the
     next one = TERM's My Classes; later than both = not added */
  const nt = nowTerm(), [ct, cy] = nt.label.split(' '), cur = key(ct, cy);
  const [pt, py] = CFG.TERM_LABEL.split(' '), nxt = splitTerms() ? key(pt, py) : -1;""")
one("""    if (x._open && k === cur) x._now = true;
    else if (x._open && k > cur) {""", """    if (x._open && k === cur) x._now = true;
    else if (x._open && k === nxt) { x._now = false; x._next = true; }
    else if (x._open && k > cur) {""")
one("""    if (x._now && myCodes().has(x.cur)) { x.already = true; x.pick = false; }
  });
  r.latestTerm = CFG.TERM_LABEL;""", """    if (x._now && nowCodes().has(x.cur)) { x.already = true; x.pick = false; }
    if (x._next && planCodes().has(x.cur)) { x.already = true; x.pick = false; }
  });
  r.latestTerm = nt.label; r.nextTerm = splitTerms() ? CFG.TERM_LABEL : '';""")
one("""  const past = pick.filter(x => !x._now), now = pick.filter(x => x._now);""",
    """  const past = pick.filter(x => !x._now && !x._next), now = pick.filter(x => x._now), next = pick.filter(x => x._next);""")
one("""    const q = await TC.client().from('saved_classes').upsert(now.map(x => ({ user_id: TC.user.id, term: CFG.TERM, code: x.cur })));
    if (q.error) { await TC.reloadHistory(); return dbSay(q.error, 'Past classes saved, but this term’s classes didn’t — add them from Explore (tap + on a class).'); }
  }""", """    const q = await TC.client().from('saved_classes').upsert(now.map(x => ({ user_id: TC.user.id, term: nowTerm().code, code: x.cur })));
    if (q.error) { await TC.reloadHistory(); return dbSay(q.error, 'Past classes saved, but this term’s classes didn’t — add them from Explore (tap + on a class).'); }
  }
  if (next.length) {
    const q = await TC.client().from('saved_classes').upsert(next.map(x => ({ user_id: TC.user.id, term: CFG.TERM, code: x.cur })));
    if (q.error) { await Promise.all([TC.reloadHistory(), loadMine()]); return dbSay(q.error, `Saved the rest, but your ${CFG.TERM_LABEL} classes didn’t — add them from Explore (tap + on a class).`); }
  }""")
one("""  toast((past.length ? past.length + ' past class' + (past.length === 1 ? '' : 'es') : '') + (past.length && now.length ? ' and ' : '') + (now.length ? now.length + ' class' + (now.length === 1 ? '' : 'es') + ' this term' : '') + ' added');""",
    """  toast([past.length ? past.length + ' past class' + (past.length === 1 ? '' : 'es') : '', now.length ? now.length + ' class' + (now.length === 1 ? '' : 'es') + ' this term' : '', next.length ? next.length + ' for ' + CFG.TERM_LABEL : ''].filter(Boolean).join(' and ') + ' added');""")
opt("""  const past = r.rows.map((x, i) => [x, i]).filter(([x]) => !x._now && !(x.skip && x._open)), now = r.rows.map((x, i) => [x, i]).filter(([x]) => x._now),""",
    """  const past = r.rows.map((x, i) => [x, i]).filter(([x]) => !x._now && !x._next && !(x.skip && x._open)), now = r.rows.map((x, i) => [x, i]).filter(([x]) => x._now), next = r.rows.map((x, i) => [x, i]).filter(([x]) => x._next),""")
opt("""  ${now.length ? `<div class="tc-hterm">In progress · ${esc(r.latestTerm || '')}</div>${now.map(([x, i]) => row(x, i)).join('')}` : ''}""",
    """  ${now.length ? `<div class="tc-hterm">In progress · ${esc(r.latestTerm || '')}</div>${now.map(([x, i]) => row(x, i)).join('')}` : ''}
  ${next.length ? `<div class="tc-hterm">Registered · ${esc(r.nextTerm || '')}</div>${next.map(([x, i]) => row(x, i)).join('')}` : ''}""")

# ---------------------------------------------------------------- onboarding asks for Spring classes honestly
one("""<h1>Add this term’s schedule</h1><p class="lead">Add the classes you’re taking in ${esc(CFG.TERM_LABEL)}, then we show which friends are in them.</p>""",
    """<h1>${splitTerms() ? `Add your ${esc(CFG.TERM_LABEL)} classes` : 'Add this term’s schedule'}</h1><p class="lead">${splitTerms() ? `Registered already? Add the classes you’re taking in ${esc(CFG.TERM_LABEL)}, then we show which friends are in them. Not yet? Skip — add them after you register.` : `Add the classes you’re taking in ${esc(CFG.TERM_LABEL)}, then we show which friends are in them.`}</p>""")

# ---------------------------------------------------------------- CSS
one(""".pillchip{""", """.fviews{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.fview{display:inline-block;padding:3px 9px;border-radius:12px;font-size:12px;font-weight:900;line-height:1.35;background:var(--bg);color:var(--ink3)}
.fview.next{background:var(--blue-soft);color:var(--blue-ink)}
.fview.plan-A,.fview.plan-B,.fview.plan-C{background:var(--pc-soft);color:var(--pc-ink)}
.fnew{display:inline-block;padding:3px 9px;border-radius:12px;font-size:12px;font-weight:900;line-height:1.35;background:var(--pink-soft);color:var(--pink-ink)}
.secterm{color:var(--ink3)}
.pillchip{""")
f.write_text(s)
print('patched', f)
