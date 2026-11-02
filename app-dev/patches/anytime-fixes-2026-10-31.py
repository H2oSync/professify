#!/usr/bin/env python3
"""Tate, 2026-10-31 (approved): My Classes classes with no section (the Anytime tray) — 141 of them live across 17 students,
mostly from Degree Progress Report imports and website degree plans. App-side display/data rules; never invents a section.
  a. a saved class the student already FINISHED in an earlier term (their own class_history) isn't shown as a class of this
     term anywhere (own My Classes / week / Anytime, friends' cards, pages, stories). Hidden, never deleted on its own; the
     owner's My Classes says "N classes you've already taken are hidden · Remove them" (with Undo).
  b. the course has exactly ONE section that term: shown with that section's real times (own and friends' views); when the
     owner opens the app it is saved as their section (my_sections, the usual write path). Never with 2+ sections.
  c. 2+ sections: a card (not a pop-up) at the top of My Classes, and a small row on the owner's Home, "Add times to N
     classes" -> a sheet of each class's sections (days, times, professor + rating, seats, friends in it); Skip per class.
  d. a term with an implausible number of sectionless classes (more than 10, or 12+ saved within 10 minutes): asks once,
     "Are you taking all N of these in <term>?" -> Yes keeps them; "Pick the ones I'm taking" -> a checklist; unticked
     ones come off (with Undo).
Run on app/index.html (then dpr-pick-sections-2026-10-31.py)."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)

# ---- data: when each saved class was added (rule d), own and now-term ----
one("""    sb.from('saved_classes').select('code').eq('user_id', me).eq('term', CFG.TERM),
    sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id', me).eq('term', CFG.TERM)
  ]);""", """    sb.from('saved_classes').select('code,created_at').eq('user_id', me).eq('term', CFG.TERM),   /* created_at (2026-10-31): a whole plan saved at once */
    sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id', me).eq('term', CFG.TERM)
  ]);""")
one("""  TC.mineRows = { secs: secs.error ? [] : (secs.data || []), saved: mine };""",
    """  TC.mineRows = { secs: secs.error ? [] : (secs.data || []), saved: mine, at: (codes.data || []).map(r => r.created_at).filter(Boolean) };""")
one("""      sb.from('saved_classes').select('code').eq('user_id', me).eq('term', t),
      sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id', me).eq('term', t)""",
    """      sb.from('saved_classes').select('code,created_at').eq('user_id', me).eq('term', t),
      sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id', me).eq('term', t)""")
one("""  TC.nowMineRows = { secs: secs && !secs.error ? (secs.data || []) : [], saved: [...new Set((codes.data || []).map(r => canonCode(r.code)).filter(Boolean))] };""",
    """  TC.nowMineRows = { secs: secs && !secs.error ? (secs.data || []) : [], saved: [...new Set((codes.data || []).map(r => canonCode(r.code)).filter(Boolean))], at: (codes.data || []).map(r => r.created_at).filter(Boolean) };""")

# ---- a + b in the one place every view's classes come from ----
one("""function secsFromRows(uid, rows, saved, look, idp) {
  const out = [], unplaced = [], keep = new Set(saved || []), L = look || (n => SEC[n]);   /* look: the now-term's sections (spring-wall) */""",
    """function secsFromRows(uid, rows, saved, look, idp, term) {
  const out = [], unplaced = [], hidden = [], keep = new Set(saved || []), L = look || (n => SEC[n]);   /* look: the now-term's sections (spring-wall) */""")
one("""  /* A saved class with no usable section is still one of their classes: listed, never drawn. */
  keep.forEach(code => { if (!out.some(s => s.code === code)) unplaced.push(code); });
  return { secs: out, unplaced };
}""", """  /* A saved class with no usable section is still one of their classes: listed, never drawn.
     (2026-10-31) With NO my_sections row at all, in a term we know (term): finished before that term => hidden; the
     course's only section that term => that section, marked oneSec (the owner's app saves it, anyQuiet). Never 2+. */
  const done = term ? anyDone(uid, term) : null, has = new Set((rows || []).map(r => canonCode(r.code)));
  keep.forEach(code => {
    if (out.some(s => s.code === code)) return;
    if (done && !has.has(code)) {
      if (done.has(code)) { hidden.push(code); return; }
      const one = anyOneSec(term, code);
      if (one) { out.push(Object.assign({}, one, { oneSec: true })); return; }
    }
    unplaced.push(code);
  });
  return { secs: out, unplaced, hidden };
}""")
one("""function relinkPeople() {
  if (TC.mineRows) { const m = secsFromRows('me', TC.mineRows.secs, TC.mineRows.saved); TC.mySecs = m.secs; TC.myUnplaced = m.unplaced; PEOPLE.me.secs = m.secs; PEOPLE.me.unplaced = m.unplaced; }
  (TC.friendRows ? Object.keys(TC.friendRows) : []).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendRows[uid].secs, TC.friendRows[uid].saved); PEOPLE[uid].secs = m.secs; PEOPLE[uid].unplaced = m.unplaced; });""",
    """function relinkPeople() { relinkPeople0(); anyTick(); }   /* (2026-10-31) then the Anytime work: Fall sections to look up, quiet saves */
function relinkPeople0() {
  TC.anySigs = { now: {} };   /* (2026-10-31) what this relink made of the rows: anyChanged() relinks only when a late arrival changes that */
  if (TC.mineRows) { const m = secsFromRows('me', TC.mineRows.secs, TC.mineRows.saved, null, null, CFG.TERM); TC.mySecs = m.secs; TC.myUnplaced = m.unplaced; PEOPLE.me.secs = m.secs; PEOPLE.me.unplaced = m.unplaced; PEOPLE.me.hidden = m.hidden; TC.anySigs.me = anySig(m); }
  (TC.friendRows ? Object.keys(TC.friendRows) : []).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendRows[uid].secs, TC.friendRows[uid].saved, null, null, CFG.TERM); PEOPLE[uid].secs = m.secs; PEOPLE[uid].unplaced = m.unplaced; });""")
one("""  if (TC.nowMineRows) { const m = secsFromRows('me', TC.nowMineRows.secs, TC.nowMineRows.saved, nowLook, 'xn'); PEOPLE.me.nowSecs = m.secs; PEOPLE.me.nowUnplaced = m.unplaced; }
  Object.keys(TC.friendNowRows || {}).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendNowRows[uid].secs, TC.friendNowRows[uid].saved, nowLook, 'xn'); PEOPLE[uid].nowSecs = m.secs; PEOPLE[uid].nowUnplaced = m.unplaced; });
}""", """  if (TC.nowMineRows) { const m = secsFromRows('me', TC.nowMineRows.secs, TC.nowMineRows.saved, nowLook, 'xn', nowTerm().code); PEOPLE.me.nowSecs = m.secs; PEOPLE.me.nowUnplaced = m.unplaced; PEOPLE.me.nowHidden = m.hidden; TC.anySigs.nowMe = anySig(m); }
  Object.keys(TC.friendNowRows || {}).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendNowRows[uid].secs, TC.friendNowRows[uid].saved, nowLook, 'xn', nowTerm().code); PEOPLE[uid].nowSecs = m.secs; PEOPLE[uid].nowUnplaced = m.unplaced; TC.anySigs.now[uid] = anySig(m, true); });
}
/* ---- (2026-10-31) Anytime fixes (Tate approved). A My Classes class with no section: what it shows, never an invented section.
   · finished in an EARLIER term (the person's own class_history, a finished row) => hidden as a class of this term, everywhere
     (own and friends' views); never deleted here — the owner's My Classes offers Remove (Undo)
   · the course has exactly ONE section that term => that section's real times (own and friends'); the owner's app saves it as
     their section when it opens (anyQuiet: TC.addMySection / TC.setNowSection, the usual writes) so it's real data after
   · 2+ sections => never picked for anyone; the owner gets a card (anyPickList) — not a pop-up, so the pop-up limits don't apply
   · a term with more than 10 of them, or 12+ classes saved in 10 minutes (a degree plan dumped in) => asked once (anyBulk) ---- */
const ANY_ORD = { Winter: 1, Spring: 2, Summer: 3, Fall: 4 };
const anyOrd = (t, y) => ANY_ORD[t] && +y ? (+y) * 10 + ANY_ORD[t] : null;
function anyTermLabel(t) {
  t = String(t || ''); if (!t) return '';
  if (t === String(CFG.TERM)) return CFG.TERM_LABEL;
  const n = nowTerm(); if (t === String(n.code)) return n.label;
  return (myTerms().find(x => x.code === t) || {}).label || '';
}
/* the classes uid finished before term t: a dated class_history row of an earlier term that isn't still in progress */
function anyDone(uid, t) {   /* null while their record isn't known (not loaded, or failed): nothing hidden, nothing filled in */
  const out = new Set(), H = uid === 'me' ? (TC.err.history ? null : TC.myHistory) : (TC.friendHist ? (TC.friendHist[uid] || []) : null);
  const [tt, ty] = anyTermLabel(t).split(' '), o = anyOrd(tt, ty);
  if (!Array.isArray(H) || o == null) return null;
  H.forEach(h => { const k = anyOrd(h.term, h.year); if (k != null && k < o && !histNotDone(h)) { const c = canonCode(h.code); if (c) out.add(c); } });
  return out;
}
const anySecSort = (a, b) => String(a.sec).localeCompare(String(b.sec), undefined, { numeric: true });
/* a course's sections in term t, or null while they aren't known (the plan term: its seat list; the now-term: NOWT) */
function anySecsOf(t, code) {
  t = String(t);
  if (splitTerms() && t === String(nowTerm().code)) {
    if (!(nowAllReady() || (NOWT.term === t && NOWT.codes[code] === 'done'))) return null;
    return (NOWT.byCode[code] || []).slice().sort(anySecSort);
  }
  if (t !== String(CFG.TERM) || !TC.seatsLoaded || LENS_NOW) return null;
  return (SECS_BY_CODE[code] || []).slice().sort(anySecSort);
}
function anyOneSec(t, code) { const l = anySecsOf(t, code); return l && l.length === 1 ? l[0] : null; }
function anyTitle(t, code) {
  const now = splitTerms() && String(t) === String(nowTerm().code);
  const ti = (now ? ((NOWT.courses[code] || {}).title || NOW_TITLES[code]) : '') || courseName(code) || ((COURSES[code] || {}).title) || '';
  return ti && ti !== code ? ti : '';
}
/* this phone's notes, per account: skipped classes, quiet saves done, the once-only question */
function anyLS(k, v) {
  const key = 'tc_any_' + k + ':' + ((TC.user && TC.user.id) || '');
  try { if (v === undefined) return JSON.parse(localStorage.getItem(key) || 'null'); localStorage.setItem(key, JSON.stringify(v)); } catch (e) {}
  return null;
}
const anySkipped = () => new Set(anyLS('skip') || []);
function anySkipSet(keys, on) { const s = anySkipped(); keys.forEach(k => { if (on) s.add(k); else s.delete(k); }); anyLS('skip', [...s].slice(-400)); }
/* the owner's classes in term t (the plan term or the now-term), or null while loading */
function anyMine(t) {
  t = String(t);
  if (t === String(CFG.TERM)) return TC.mineRows ? { box: TC.mineRows, secs: personSecs('me'), unplaced: PEOPLE.me.unplaced || [], hidden: PEOPLE.me.hidden || [] } : null;
  if (splitTerms() && t === String(nowTerm().code)) return TC.nowMineRows && !TC.err.nowMine ? { box: TC.nowMineRows, secs: nowSecs('me'), unplaced: nowUnplaced('me'), hidden: PEOPLE.me.nowHidden || [] } : null;
  return null;
}
/* (d) the classes to ask about, once: more than 10 with no section, or 12+ classes saved in the term within 10 minutes */
function anyBulk(t) {
  t = String(t); const m = anyMine(t); if (!m || (anyLS('bulk') || {})[t]) return null;
  const list = [...new Set(m.unplaced.concat(m.secs.filter(x => x.oneSec).map(x => x.code)))];
  if (list.length < 2) return null;
  const at = (m.box.at || []).map(x => Date.parse(x)).filter(x => !isNaN(x)).sort((a, b) => a - b);
  let burst = false;
  for (let i = 0, j = 0; j < at.length && !burst; j++) { while (at[j] - at[i] > 10 * 60000) i++; burst = j - i + 1 >= 12; }
  return list.length > 10 || burst ? list : null;
}
function anyBulkSet(t, v) { const b = anyLS('bulk') || {}; b[String(t)] = v; anyLS('bulk', b); }
/* (c) the owner's classes in t with 2+ sections there, not skipped — none while the question above is open */
function anyPickList(t) {
  t = String(t); const m = anyMine(t); if (!m || anyBulk(t)) return [];
  const sk = anySkipped();
  return m.unplaced.filter(c => !sk.has(t + ':' + c)).map(c => ({ code: c, secs: anySecsOf(t, c) })).filter(x => x.secs && x.secs.length >= 2);
}
/* the now-term's sections for classes with none (own and friends'), in batches — so (b) and (c) know how many there are */
async function anyNowFetch(codes) {
  if (!splitTerms() || nowAllReady()) return;
  const t = nowTerm().code; nowReset(t);
  const list = [...new Set(codes || [])].filter(c => c && !NOWT.codes[c]); if (!list.length) return;
  list.forEach(c => { NOWT.codes[c] = 'loading'; });
  const base = CFG.SUPABASE_URL.replace(/\\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const sel = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr';
  for (let i = 0; i < list.length; i += 20) {
    const part = list.slice(i, i + 20), P = new Set(part), forms = [...new Set([].concat(...part.map(c => [c, c.replace(' ', '')])))].map(c => '"' + c + '"').join(',');
    let rows = null;
    try {
      const res = await fetch(base + '/rest/v1/course_seats?term=eq.' + encodeURIComponent(t) + '&course_code=in.(' + encodeURIComponent(forms) + ')&select=' + sel + '&order=class_nbr.asc&limit=1000', { headers: hdr });
      if (res.ok) { const j = await res.json(); if (Array.isArray(j)) rows = j; }
    } catch (e) {}
    if (NOWT.term !== t) return;
    if (!rows) { part.forEach(c => { NOWT.codes[c] = 'err'; }); continue; }
    if (!NOWT.ready) addNowRows(NOWT, rows.filter(r => P.has(canonCode(r.course_code))), t);
    part.forEach(c => { NOWT.codes[c] = 'done'; });
  }
}
async function anyNowLoad() {
  if (anyNowLoad.run || !splitTerms() || nowAllReady()) return;
  const t = nowTerm().code, want = [].concat(nowUnplaced('me'), ...(TC.friends || []).map(f => nowUnplaced(f))).filter(c => !(NOWT.term === t && NOWT.codes[c]));
  if (!want.length) return;
  anyNowLoad.run = true;
  try { await anyNowFetch(want); } catch (e) {} finally { anyNowLoad.run = false; }
  matchPolyRatings(); if (anyChanged(true)) relinkPeople(); else anyTick(); render(true);
}
/* did a late arrival (your record; the now-term's sections) change what anyone's classes look like? Only then is
   everything relinked — so nothing is redrawn or re-sorted for no reason. me: your own classes only; now: the now-term's.
   Compared with what the last relink made (TC.anySigs), not with PEOPLE, which views may have reshaped since. */
function anySig(m, noHid) { return [(m.secs || []).map(x => x.id + (x.oneSec ? '*' : '')).join(), (m.unplaced || []).join(), noHid ? '' : (m.hidden || []).join()].join('|'); }
function anyChanged(now) {
  const G = TC.anySigs || { now: {} }, nowLook = n => NOW_SEC[n] || null, nt = splitTerms() ? nowTerm().code : null;
  if (!now && TC.mineRows && anySig(secsFromRows('me', TC.mineRows.secs, TC.mineRows.saved, null, null, CFG.TERM)) !== G.me) return true;
  if (!nt) return false;
  if (TC.nowMineRows && anySig(secsFromRows('me', TC.nowMineRows.secs, TC.nowMineRows.saved, nowLook, 'xn', nt)) !== G.nowMe) return true;
  return !!now && Object.keys(TC.friendNowRows || {}).some(uid => PEOPLE[uid] && anySig(secsFromRows(uid, TC.friendNowRows[uid].secs, TC.friendNowRows[uid].saved, nowLook, 'xn', nt), true) !== G.now[uid]);
}
const anyNowWaiting = () => splitTerms() && !nowAllReady() && nowUnplaced('me').some(c => NOWT.term !== nowTerm().code || !NOWT.codes[c] || NOWT.codes[c] === 'loading');
/* the app opened: each term's one-section classes are saved once their sections are known */
function anyOpen() { TC.anyDue = {}; TC.anyDue[CFG.TERM] = 1; if (splitTerms()) TC.anyDue[nowTerm().code] = 1; anyTick(); }
function anyTick() {
  if (!TC.ready || !TC.user) return;
  if (splitTerms() && !nowAllReady()) anyNowLoad();
  if (TC.anyDue && Object.keys(TC.anyDue).length && !anyQuiet.run) { clearTimeout(anyTick.t); anyTick.t = setTimeout(anyQuiet, 0); }
}
async function anyQuiet() {
  if (anyQuiet.run || !TC.anyDue || !TC.ready || !TC.user || UI.dprPicking) return;   /* the report's own step picks them (dpr-pick) */
  anyQuiet.run = true; let wrote = 0;
  try {
    for (const t of Object.keys(TC.anyDue)) {
      const plan = t === String(CFG.TERM), now = !plan && splitTerms() && t === String(nowTerm().code);
      if (!plan && !now) { delete TC.anyDue[t]; continue; }
      if (plan ? !(TC.seatsLoaded && TC.mineRows) : !(TC.nowMineRows && !anyNowWaiting())) continue;   /* not known yet: next relink */
      if (!Array.isArray(TC.myHistory) && !TC.err.history) continue;   /* your record first: a class you've finished is hidden, never saved */
      delete TC.anyDue[t];
      if (anyBulk(t)) continue;   /* maybe a whole degree plan: asked first, then saved */
      const done = new Set(anyLS('one') || []);
      for (const x of (plan ? personSecs('me') : nowSecs('me')).filter(y => y.oneSec)) {
        const k = t + ':' + x.code; if (done.has(k)) continue;   /* saved once already: a section taken off since stays off */
        const c = Object.assign({}, x); delete c.oneSec;   /* the section itself: setNowSection keeps what it's given in NOW_SEC */
        const e = plan ? await TC.addMySection(c, { hadSaved: true }) : await TC.setNowSection(c);
        if (e) break;
        wrote++; done.add(k); anyLS('one', [...done].slice(-400));
      }
    }
  } catch (e) {} finally { anyQuiet.run = false; }
  if (wrote) { UI.storyOrder = null; relinkPeople(); render(true); }
}
function anyQuietAgain(t) { TC.anyDue = TC.anyDue || {}; TC.anyDue[String(t)] = 1; anyTick(); }
/* several classes off a term at once (taken ones, or the ones not ticked), and back for Undo */
TC.anyRemoveCodes = async function (t, codes) {
  const sb = TC.client(), me = TC.user.id;
  const a = await sb.from('saved_classes').delete().eq('user_id', me).eq('term', t).in('code', codes);
  if (a.error) return dbSay(a.error, 'Couldn’t remove those classes.');
  await sb.from('my_sections').delete().eq('user_id', me).eq('term', t).in('code', codes);
  await loadMine(); return null;
};
TC.anyRestoreCodes = async function (t, snaps) {
  const sb = TC.client(), me = TC.user.id, codes = Object.keys(snaps);
  const saved = codes.filter(c => snaps[c].saved).map(c => ({ user_id: me, term: t, code: c }));
  let r = saved.length ? await sb.from('saved_classes').upsert(saved, { onConflict: 'user_id,code,term' }) : { error: null };
  const rows = [];
  codes.forEach(c => snaps[c].rows.forEach(x => { if (x.class_nbr != null && String(x.class_nbr) !== '') rows.push({ user_id: me, term: t, code: x.code, class_nbr: String(x.class_nbr), section: x.section == null ? null : x.section, instructor: x.instructor == null ? null : x.instructor, days: x.days == null ? null : x.days, status: x.status || 'enrolled', wl_pos: x.wl_pos == null ? null : x.wl_pos }); }));
  if (!r.error && rows.length) r = await sb.from('my_sections').upsert(rows, { onConflict: 'user_id,class_nbr,term' });
  await loadMine(); return r.error ? dbSay(r.error, 'Couldn’t undo that.') : null;
};""")

# another My Classes term (read-only rows): finished classes hidden there too
one("""  if (splitTerms() && code === nowTerm().code && TC.nowMineRows) return { secs: nowSecs('me'), unplaced: nowUnplaced('me') };   /* spring-wall */""",
    """  if (splitTerms() && code === nowTerm().code && TC.nowMineRows) return { secs: nowSecs('me'), unplaced: nowUnplaced('me'), hidden: PEOPLE.me.nowHidden || [] };   /* spring-wall */""")
one("""  keep.forEach(c => { if (!out.some(x => x.code === c)) unplaced.push(c); });
  return { secs: out, unplaced };
}""", """  const done = anyDone('me', code), hidden = [];   /* (2026-10-31) */
  keep.forEach(c => { if (out.some(x => x.code === c)) return; if (done && done.has(c) && !box.rows.some(r => canonCode(r.code) === c)) hidden.push(c); else unplaced.push(c); });
  return { secs: out, unplaced, hidden };
}""")

# friends' finished classes, by person (rule a on their cards)
one("""    TC.took = {}; TC.tookCode = {};""", """    TC.took = {}; TC.tookCode = {}; TC.friendHist = hist.error ? null : {};
    if (!hist.error) (hist.data || []).forEach(h => { if (TC.friendRows[h.user_id]) (TC.friendHist[h.user_id] = TC.friendHist[h.user_id] || []).push(h); });   /* (2026-10-31) */""")
# your own record arrives after My Classes: draw again with it
one("""      delete TC.err.history; TC.myHistory = r.data || [];
      const groups = {};""", """      delete TC.err.history; TC.myHistory = r.data || []; if (anyChanged()) relinkPeople(); else anyTick();   /* (2026-10-31) finished classes hide */
      const groups = {};""")
one("""  delete TC.err.history; TC.myHistory = r.data || []; return true;""",
    """  delete TC.err.history; TC.myHistory = r.data || []; if (anyChanged()) relinkPeople(); else anyTick(); return true;""")
# opened: the quiet saves are due
one("""  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);""",
    """  UI.storyOrder = null; TC.ready = true; TC.loadDone = Date.now(); render(true);
  anyOpen();   /* (2026-10-31) one-section classes become your section */""")

# ---- the card and the note on My Classes (both terms), the row on Home ----
one("""    else inner = chips + `
  ${TC.err.mine ? errCard('Couldn’t load your classes.', 'refresh') : !TC.mineRows ? loadingCard('Loading your classes…') : ''}""",
    """    else inner = chips + anyMineTop(CFG.TERM) + `
  ${TC.err.mine ? errCard('Couldn’t load your classes.', 'refresh') : !TC.mineRows ? loadingCard('Loading your classes…') : ''}""")
one("""  const ts = termSecs(tm.code), later = terms.findIndex(x => x.label === tm.label) > terms.findIndex(x => x.code === CFG.TERM);
  if (!ts.secs.length && !ts.unplaced.length) return `""", """  const ts = termSecs(tm.code), later = terms.findIndex(x => x.label === tm.label) > terms.findIndex(x => x.code === CFG.TERM), top = anyMineTop(tm.code);
  if (!ts.secs.length && !ts.unplaced.length) return top + `""")
one("""  return mineAgenda(ts.secs, ts.unplaced, { now: isNowT, other: !isNowT, label: tm.label, grid:""",
    """  return top + mineAgenda(ts.secs, ts.unplaced, { now: isNowT, other: !isNowT, label: tm.label, grid:""")
one(""" <div class="stories">${stories}${TC.friends.length || !TC.ready || friendsErr ? '' : addStory}</div>
 ${hptr()}""", """ <div class="stories">${stories}${TC.friends.length || !TC.ready || friendsErr ? '' : addStory}</div>
 ${anyHomeRow()}${hptr()}""")

# ---- the look ----
one(""".dr-link{height:36px;font-size:15px;font-weight:900;color:var(--muted);background:none}""",
    """.dr-link{height:36px;font-size:15px;font-weight:900;color:var(--muted);background:none}
/* (2026-10-31) Anytime: add times, the once-only question, picking a section. --any-mut: muted text that keeps 4.5:1 on
   --bg too (a section row and the report's step sit on --bg, where --muted is 4.4:1 in light) */
:root{--any-mut:#5B6B80}:root[data-theme="dark"]{--any-mut:var(--muted)}
.any-card{margin:12px 12px 0;padding:14px 16px;position:relative}
.any-card.any-times{padding:0}
.any-cmain{display:flex;align-items:center;gap:12px;width:100%;min-height:64px;padding:12px 52px 12px 14px;text-align:left}
.any-ic{width:40px;height:40px;flex:none;border-radius:13px;display:grid;place-items:center;background:var(--blue-soft);color:var(--blue-ink)}
.any-ct{display:block;font-size:15.5px;font-weight:900;color:var(--ink);line-height:1.3}
.any-cs{display:block;font-size:13px;font-weight:700;color:var(--muted);margin-top:2px;line-height:1.35}
.any-cx{position:absolute;top:10px;right:8px;width:44px;height:44px}
.any-cb{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.any-cb .pbtn{height:44px;border-radius:22px}
.any-cb .pbtn.soft,.any-cmain .pbtn.soft{background:var(--bg);color:var(--ink2)}
.any-hid{margin:10px 16px 0;font-size:13px;font-weight:800;color:var(--any-mut);display:flex;align-items:center;flex-wrap:wrap;gap:0 4px}
.any-hrm{font-size:13px;font-weight:900;color:var(--blue-t,var(--blue));min-height:44px;padding:0 4px}
.any-home{display:flex;align-items:center;gap:12px;width:calc(100% - 2 * var(--hg,16px));margin:12px var(--hg,16px) 0;padding:12px 14px;min-height:64px;text-align:left}
.any-home .chev{color:var(--muted);flex:none}
.any-pc{margin-top:16px}
.any-pch{gap:8px;min-height:44px}
.any-pcn{font-size:15px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.any-skip{min-height:44px;padding:0 10px;font-size:14px;font-weight:900;color:var(--ink3);flex:none}
.secrow.any-sec{width:100%;text-align:left;min-height:56px;gap:10px}
.any-sb{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.secrow .any-sb .t{flex:none}
.any-sm{font-size:13px;font-weight:800;color:var(--any-mut)}
.any-sx{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;margin-top:2px}
.any-fr{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:900;color:var(--purple-ink)}
.any-cl{font-size:12.5px;font-weight:900;color:var(--amber-ink)}
.any-tag{align-self:flex-start;font-size:11.5px;font-weight:900;color:var(--teal-t,var(--teal));background:var(--teal-soft);padding:2px 8px;border-radius:8px;margin-top:2px}
.any-rd{width:24px;height:24px;flex:none;border-radius:50%;display:grid;place-items:center;box-shadow:inset 0 0 0 2px var(--ink5,var(--muted));color:#fff}
.secrow.any-sec.on{box-shadow:inset 0 0 0 2px var(--blue)}
.any-sec.on .any-rd{background:var(--blue);box-shadow:none}
.any-codes{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;max-height:180px;overflow:auto}
.any-bfoot{display:grid;gap:8px;margin:14px 0 -20px;position:sticky;bottom:-20px;background:var(--card);padding:8px 0 20px}   /* over .sbody's 20px bottom padding */""")

# ---- the screens and taps (after the report's onboarding wrapper, where every sheet and action exists) ----
one("""/* "Send the link to my laptop" — from onboarding's last step and the empty Planner. */""",
    """/* ---- (2026-10-31) Anytime: the card and note on My Classes, the row on Home (owner only), the two sheets ---- */
function anyMineTop(t) {
  if (!TC.user || !TC.ready) return '';
  t = String(t); const L = anyTermLabel(t), m = anyMine(t), hid = m ? m.hidden : ((termSecs(t) || {}).hidden || []);
  let out = '';
  const bulk = anyBulk(t), pick = bulk ? [] : anyPickList(t);
  if (bulk) out += `<div class="card any-card any-bulk" role="group" aria-label="${esc(L)}: check these classes"><div class="any-ct">Are you taking all ${bulk.length} of these in ${esc(L)}?</div><div class="any-cs">They came in together with no times. Keep the ones you’re taking.</div><div class="any-cb"><button class="pbtn" data-a="anyBulkYes" data-x="${esc(t)}">Yes</button><button class="pbtn soft" data-a="anyBulkPick" data-x="${esc(t)}">Pick the ones I’m taking</button></div></div>`;
  else if (pick.length) out += `<div class="card any-card any-times" role="group" aria-label="${esc(L)}: add times"><button class="any-cmain" data-a="anyPickOpen" data-x="${esc(t)}"><span class="any-ic">${ic('clock', 20, 2.4)}</span><span class="grow"><span class="any-ct">Add times to ${pick.length} class${pick.length === 1 ? '' : 'es'}</span><span class="any-cs">Pick your section and it goes on your week.</span></span><span class="pbtn">Pick</span></button><button class="xbtn any-cx" data-a="anyPickNo" data-x="${esc(t)}" aria-label="Not now">${ic('x', 14, 2.4)}</button></div>`;
  if (hid.length) out += `<div class="any-hid"><span>${hid.length === 1 ? '1 class you’ve already taken is hidden' : hid.length + ' classes you’ve already taken are hidden'}</span><span aria-hidden="true">·</span><button class="any-hrm" data-a="anyHidRm" data-x="${esc(t)}"${UI.busy.anyHid ? ' disabled' : ''}>Remove ${hid.length === 1 ? 'it' : 'them'}</button></div>`;
  return out;
}
function anyHomeRow() {
  if (!TC.ready || !TC.user) return '';
  const terms = (splitTerms() ? [nowTerm().code, CFG.TERM] : [CFG.TERM]).map(String);
  const row = (a, t, h, sub) => `<button class="card any-home" data-a="${a}" data-x="${esc(t)}"><span class="any-ic">${ic('clock', 20, 2.4)}</span><span class="grow"><span class="any-ct">${esc(h)}</span><span class="any-cs">${esc(sub)}</span></span><span class="chev">${ic('chevR', 18)}</span></button>`;
  for (const t of terms) { const b = anyBulk(t); if (b) return row('anyBulkOpen', t, `Are you taking all ${b.length} ${anyTermLabel(t)} classes?`, 'Tap to check them'); }
  for (const t of terms) { const p = anyPickList(t); if (p.length) return row('anyPickOpen', t, `Add times to ${p.length} class${p.length === 1 ? '' : 'es'}`, `${anyTermLabel(t)} · pick your sections`); }
  return '';
}
/* one section as a tappable row: days and times, professor and rating, seats, friends in it, what it overlaps */
function anySecBtn(s, o) {
  const when = s.async ? 'Online, self-paced' : s.noTime ? 'Time not posted' : daysLabel(s.days) + ' ' + range(s);
  const f = o.fr || [], cl = [...new Set((o.clash || []).map(x => x.code))], sl = secLabel(s.sec) || 'this section';
  const frT = f.length ? `<span class="any-fr">${avStack(f, 22)}<span>${f.length} friend${f.length === 1 ? '' : 's'} in ${esc(sl)}</span></span>` : '';
  const clT = cl.length ? `<span class="any-cl">Overlaps ${esc(cl.join(', '))}</span>` : '';
  const lab = [(s.sec ? secLabel(s.sec) + ', ' : '') + when, profName(s.prof), f.length ? f.length + ' friend' + (f.length === 1 ? '' : 's') + ' in it' : '', cl.length ? 'overlaps ' + cl.join(', ') : '', o.radio ? '' : 'pick this section'].filter(Boolean).join(', ');
  return `<button class="secrow any-sec${o.on ? ' on' : ''}" data-a="${o.act}" data-x="${esc(o.x)}"${o.radio ? ` aria-pressed="${!!o.on}"` : ''} aria-label="${esc(lab)}"${o.busy || ''}>${o.radio ? `<span class="any-rd" aria-hidden="true">${o.on ? ic('check', 13, 3.4) : ''}</span>` : ''}<span class="any-sb">${secRowT(s)}<span class="any-sm">${rowProf(s.prof)} · ${secSeatText(s)}</span>${frT || clT ? `<span class="any-sx">${frT}${clT}</span>` : ''}${o.tag ? `<span class="any-tag">${esc(o.tag)}</span>` : ''}</span>${o.radio ? '' : '<span class="pbtn" style="height:32px;padding:0 12px;font-size:13px">Pick</span>'}</button>`;
}
const anyFriendsIn = (t, s) => TC.friends.filter(f => (String(t) === String(CFG.TERM) ? personSecs(f) : nowSecs(f)).some(x => String(x.id) === String(s.id)));
SHEETS.anyPick = sh => {
  const t = sh.term, L = anyTermLabel(t), list = anyPickList(t), mine = ((anyMine(t) || {}).secs || []).filter(onWeekSec);
  const busy = UI.busy.anyPick ? ' disabled' : '';
  const cls = x => `<div class="any-pc"><div class="row sb any-pch"><span class="row" style="gap:8px;min-width:0"><span class="code">${esc(x.code)}</span><b class="any-pcn">${esc(anyTitle(t, x.code))}</b></span><button class="any-skip" data-a="anySkip" data-x="${esc(t + '|' + x.code)}" aria-label="Skip ${esc(x.code)}"${busy}>Skip</button></div>${x.secs.map(s2 => anySecBtn(s2, { act: 'anyChoose', x: t + '|' + x.code + '|' + s2.id, fr: anyFriendsIn(t, s2), clash: mine.filter(m => m.code !== s2.code && secClash(s2, m)), busy })).join('')}</div>`;
  return `<div class="row sb"><h3>Add times to your classes</h3>${pcX()}</div><div class="muted b" style="font-size:14px;margin-top:4px">${esc(L)} · tap the section you’re in</div>${list.length ? list.map(cls).join('') : '<div class="muted b" style="margin-top:14px;font-size:14px">All set.</div>'}`;
};
SHEETS.anyBulk = sh => {
  const t = sh.term, L = anyTermLabel(t);
  if (!sh.list) {
    const b = anyBulk(t) || [];
    return `<div class="row sb"><h3>Are you taking all ${b.length} of these in ${esc(L)}?</h3>${pcX()}</div><div class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">They came into ${esc(L)} together, with no times. If that was your whole plan, keep just the ones you’re taking.</div><div class="any-codes">${b.map(c => `<span class="code">${esc(c)}</span>`).join('')}</div><div style="display:grid;gap:8px;margin-top:16px"><button class="btn" data-a="anyBulkYes" data-x="${esc(t)}">Yes, I’m taking all ${b.length}</button><button class="btn soft" data-a="anyBulkPick" data-x="${esc(t)}">Pick the ones I’m taking</button></div>`;
  }
  const keep = sh.list.length - sh.off.length;
  return `<div class="row sb"><h3>Which are you taking in ${esc(L)}?</h3>${pcX()}</div><div class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">Untick the ones you’re not taking. They come off ${esc(L)}.</div>
  <div style="margin-top:8px">${sh.list.map(c => { const on = !sh.off.includes(c), ti = anyTitle(t, c); return `<button class="dr-rcr" data-a="anyBulkTog" data-x="${esc(c)}" aria-pressed="${on}"><span class="dr-rcb" aria-hidden="true">${on ? ic('check', 14, 3.4) : ''}</span><span class="dr-rct"><b>${esc(c)}</b>${ti ? `<span>${esc(ti)}</span>` : ''}</span></button>`; }).join('')}</div>
  <div class="any-bfoot"><button class="btn" data-a="anyBulkSave"${UI.busy.anyBulk ? ' disabled' : ''}>${UI.busy.anyBulk ? 'Saving…' : sh.off.length ? `Keep ${keep} · remove ${sh.off.length}` : `Keep all ${keep}`}</button></div>`;
};
Object.assign(A, {
  anyPickOpen: t => { if (!t) return; UI.champ = false; UI.sheet = { type: 'anyPick', term: String(t) }; render(true); },
  anyPickNo: t => { const l = anyPickList(t); if (!l.length) return; anySkipSet(l.map(x => t + ':' + x.code), true); render(true); toastUndo('Okay — they stay in Anytime', () => { anySkipSet(l.map(x => t + ':' + x.code), false); render(true); }); },
  anySkip: v => {
    const [t, code] = String(v || '').split('|'); if (!t || !code) return;
    anySkipSet([t + ':' + code], true);
    if (UI.sheet && UI.sheet.type === 'anyPick' && !anyPickList(t).length) UI.sheet = null;
    render(true); toastUndo(`${code} stays in Anytime`, () => { anySkipSet([t + ':' + code], false); render(true); });
  },
  anyChoose: async v => {
    const [t, code, id] = String(v || '').split('|'); if (UI.busy.anyPick || !t || !code || !id) return;
    const plan = t === String(CFG.TERM), s = (anySecsOf(t, code) || []).find(x => String(x.id) === id); if (!s) return;
    const snap = mineSnapIn(code, t); UI.busy.anyPick = 1; render(true);
    let e = null; try { e = plan ? await TC.addMySection(s, { hadSaved: true }) : await TC.setNowSection(s); } catch (x) { e = 'Couldn’t save that — check your connection.'; } finally { UI.busy.anyPick = 0; }
    if (e) { toast(e); return render(true); }
    UI.storyOrder = null; relinkPeople();
    if (UI.sheet && UI.sheet.type === 'anyPick' && !anyPickList(t).length) UI.sheet = null;
    render(true);
    toastUndo(`${code}${secLabel(s.sec) ? ' ' + secLabel(s.sec) : ''} is on your week`, async () => { const r = await TC.restoreMyCodeIn(code, t, snap, plan ? s.id : s.nbr); relinkPeople(); render(true); toast(r || 'Undone'); });
  },
  anyHidRm: async t => {
    if (UI.busy.anyHid || !t) return; t = String(t);
    const m = anyMine(t), codes = (m ? m.hidden : ((termSecs(t) || {}).hidden || [])).slice(); if (!codes.length) return;
    const snaps = {}; codes.forEach(c => { snaps[c] = mineSnapIn(c, t); });
    UI.busy.anyHid = 1; render(true);
    let e = null; try { e = await TC.anyRemoveCodes(t, codes); } catch (x) { e = 'Couldn’t remove those — check your connection.'; } finally { UI.busy.anyHid = 0; }
    if (e) { toast(e); return render(true); }
    relinkPeople(); render(true);
    toastUndo(`Removed ${codes.length} class${codes.length === 1 ? '' : 'es'} you’ve taken`, async () => { const r = await TC.anyRestoreCodes(t, snaps); relinkPeople(); render(true); toast(r || 'Undone'); });
  },
  anyBulkOpen: t => { if (!t || !anyBulk(t)) return; UI.champ = false; UI.sheet = { type: 'anyBulk', term: String(t) }; render(true); },
  anyBulkYes: t => { if (!t) return; anyBulkSet(t, 'yes'); if (UI.sheet && UI.sheet.type === 'anyBulk') UI.sheet = null; render(true); toast('Got it — keeping them all'); anyQuietAgain(t); },
  anyBulkPick: t => { const l = anyBulk(t); if (!l) return; UI.champ = false; UI.sheet = { type: 'anyBulk', term: String(t), list: l.slice(), off: [] }; render(true); },
  anyBulkTog: code => { const sh = UI.sheet; if (!sh || sh.type !== 'anyBulk' || !sh.list) return; const i = sh.off.indexOf(code); if (i >= 0) sh.off.splice(i, 1); else sh.off.push(code); render(true); },
  anyBulkSave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'anyBulk' || !sh.list || UI.busy.anyBulk) return;
    const t = sh.term, L = anyTermLabel(t), gone = sh.off.filter(c => sh.list.includes(c));
    if (!gone.length) { anyBulkSet(t, 'picked'); UI.sheet = null; render(true); toast(`Keeping all ${sh.list.length}`); anyQuietAgain(t); return; }
    const snaps = {}; gone.forEach(c => { snaps[c] = mineSnapIn(c, t); });
    UI.busy.anyBulk = 1; render(true);
    let e = null; try { e = await TC.anyRemoveCodes(t, gone); } catch (x) { e = 'Couldn’t remove those — check your connection.'; } finally { UI.busy.anyBulk = 0; }
    if (e) { toast(e); return render(true); }
    anyBulkSet(t, 'picked'); if (UI.sheet === sh) UI.sheet = null;
    relinkPeople(); render(true);
    toastUndo(`Removed ${gone.length} class${gone.length === 1 ? '' : 'es'} from ${L}`, async () => { const r = await TC.anyRestoreCodes(t, snaps); relinkPeople(); render(true); toast(r || 'Undone'); });
    anyQuietAgain(t);
  }
});
/* "Send the link to my laptop" — from onboarding's last step and the empty Planner. */""")
p.write_text(s); print(p, 'anytime-fixes applied')
