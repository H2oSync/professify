#!/usr/bin/env python3
"""Explore's term switch (Tate, 2026-10-10). Edits app/index.html only. Run after plans-anytime-2026-10-09.py
(on 23:45 + plans-anytime).

Tate, on a friend's Fall class whose "View class" opened the Spring 2027 page: "no dont do this only have a switch
here but keep it how it looks now, so when its toggled for 2026 it shows 2026 but when its toggled for 2027 show
all the 2027 classes, have it default toggled to the term people are trying to find classes for so thats spring
2027. it will be rare for people to click and look at the current fall 2026 mainly just to look at what friends
are taking". "here" = the "Spring 2027" words beside Filters in Explore.

  1. Explore › Classes: the term words beside Filters are a switch (same look, a small up/down mark). Tap:
     Spring 2027 <-> Fall 2026. It always starts on Spring 2027 (never saved). Fall reads every Fall section once,
     the first time it's chosen, and lists them with the same cards, search and filters. Professors mode is
     unchanged.
  2. A Fall class page: Fall's sections under their professors, read-only (no +, no Watch), each with the friends
     in it, opening that section's sheet. Opened from Explore on Fall, from a block or chip in a Fall week (a
     friend's, a story, My Classes › Fall) and from a Fall section's "View class". Everything else opens Spring,
     as now. A Fall class that isn't offered in Spring is no longer a dead end.
  Fall is kept apart from COURSES/SEC (the spring-wall rule: plans, Add to your week and seat alerts can't see it);
  the list and the page borrow those names for one synchronous render (inNow).
"""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
P = ROOT / 'app' / 'index.html'
s = P.read_text()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f'explore-term-switch: expected {n} of {a[:90]!r}, found {c}')
    s = s.replace(a, b)


# an up/down mark for the switch
rep("""chevR:'<path d="m9 5 7 7-7 7"/>',""", """chevR:'<path d="m9 5 7 7-7 7"/>',updown:'<path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/>',""")

# the term people are in now, all of it, read on demand
rep("""const NOW_SEC = {}, NOW_TITLES = {}; let NOW_SEC_TERM = '';""",
    """const NOW_SEC = {}, NOW_TITLES = {}; let NOW_SEC_TERM = '';
/* Explore's term switch (2026-10-10): EVERY section of the term people are in now, read once, the first time a
   student switches Explore to it. Like NOW_SEC it never enters COURSES/SECTIONS/SEC — plans, Add to your week and
   seat alerts can't offer it. The class list and a class page borrow those names for one render (inNow). */
const NOWT = { term: '', courses: {}, byCode: {}, sec: {}, codes: {}, ready: false, loading: false, err: false };
let LENS_NOW = false;
async function loadNowAll() {
  if (!splitTerms()) return;
  const t = nowTerm().code;
  nowReset(t);
  if (NOWT.ready || NOWT.loading) return;
  NOWT.loading = true; NOWT.err = false;
  const base = CFG.SUPABASE_URL.replace(/\\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const sel = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr';
  let rows = [], complete = false;
  try {
    for (let off = 0; off < 40000; off += 1000) {
      const res = await fetch(base + '/rest/v1/course_seats?term=eq.' + encodeURIComponent(t) + '&select=' + sel + '&order=course_code.asc,class_nbr.asc&limit=1000&offset=' + off, { headers: hdr });
      if (!res.ok) break;
      const part = await res.json(); if (!Array.isArray(part)) break;
      rows = rows.concat(part);
      if (part.length < 1000) { complete = true; break; }
    }
  } catch (e) {}
  if (NOWT.term !== t) return;
  NOWT.loading = false;
  if (!complete || !rows.length) { NOWT.err = true; render(true); return; }
  const box = { courses: {}, byCode: {}, sec: {} };
  addNowRows(box, rows, t);
  Object.assign(NOWT, box, { ready: true });
  matchPolyRatings(); render(true);
}
function nowReset(t) { if (NOWT.term !== t) Object.assign(NOWT, { term: t, courses: {}, byCode: {}, sec: {}, codes: {}, ready: false, loading: false, err: false }); }
function addNowRows(box, rows, t) {
  rows.forEach(r => {
    const x = nowSecOf(r, t); if (!x || box.sec[x.id]) return;
    box.sec[x.id] = x; (box.byCode[x.code] = box.byCode[x.code] || []).push(x);
    if (!box.courses[x.code]) { const ti = String(r.title || '').trim() || x.code; box.courses[x.code] = { title: ti, short: shortTitle(ti), units: null, prereq: null, desc: null }; }
  });
}
/* One class's sections for its page (a friend's block, a sheet's View class): one small read, not the whole term. */
async function loadNowCode(code) {
  if (!splitTerms()) return;
  const t = nowTerm().code; nowReset(t);
  if (NOWT.ready || NOWT.codes[code] === 'loading' || NOWT.codes[code] === 'done') return;
  NOWT.codes[code] = 'loading';
  const base = CFG.SUPABASE_URL.replace(/\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const sel = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr';
  const forms = [...new Set([code, code.replace(' ', '')])].map(c => '"' + c + '"').join(',');   /* the feed's spelling, with or without the space */
  let rows = null;
  try {
    const res = await fetch(base + '/rest/v1/course_seats?term=eq.' + encodeURIComponent(t) + '&course_code=in.(' + encodeURIComponent(forms) + ')&select=' + sel + '&order=class_nbr.asc&limit=1000', { headers: hdr });
    if (res.ok) { const j = await res.json(); if (Array.isArray(j)) rows = j; }
  } catch (e) {}
  if (NOWT.term !== t) return;
  if (!rows) { NOWT.codes[code] = 'err'; render(true); return; }
  if (!NOWT.ready) addNowRows(NOWT, rows.filter(r => canonCode(r.course_code) === code), t);
  NOWT.codes[code] = 'done'; matchPolyRatings(); render(true);
}
/* Render fn with the now-term's classes under the names the class list and class page read. Synchronous only. */
function inNow(fn) {
  const keep = [COURSES, SECS_BY_CODE, SEC];
  COURSES = NOWT.courses; SECS_BY_CODE = NOWT.byCode; SEC = NOWT.sec; LENS_NOW = true;
  try { return fn(); } finally { COURSES = keep[0]; SECS_BY_CODE = keep[1]; SEC = keep[2]; LENS_NOW = false; }
}
const nowAllReady = () => NOWT.ready && NOWT.term === nowTerm().code;""")

# descriptions for classes that aren't in TERM's feed
rep("""part.forEach(r => { const c = canonCode(r.course_code); const tt""",
    """part.forEach(r => { const c0 = canonCode(r.course_code); if (c0) CAT_INFO[c0] = { desc: cleanDesc(r.description), prereq: cleanPrereq(r.prereqs) }; });
      part.forEach(r => { const c = canonCode(r.course_code); const tt""")
rep("""const CAT_TITLE = {};""", """const CAT_TITLE = {}, CAT_INFO = {};""")

# friends in a class: the now-term's while a now-term list or page is drawn
rep("""const friendsIn = code => TC.friends.filter(""", """const friendsIn = code => LENS_NOW ? nowFriendsIn(code) : TC.friends.filter(""")

# Explore: the list on the chosen term
rep("""function exploreList() {
  if (!S.q.trim() && UI.exFocus && recentShown().length) return recentPanel();""",
    """const exNow = () => S.exMode === 'classes' && UI.exTerm === 'now' && splitTerms();
function exploreList() {
  if (exNow()) {
    const L = nowTerm().label;
    if (!nowAllReady()) { if (NOWT.err && !NOWT.loading && NOWT.term === nowTerm().code) return errCard(`Couldn’t load ${L} classes.`, 'retryNowAll'); loadNowAll(); return loadingCard(`Loading ${L} classes…`); }
    return inNow(exploreListBody);
  }
  if (!S.q.trim() && UI.exFocus && recentShown().length) return recentPanel();""")
rep("""  if (!TC.seatsLoaded) return TC.err.seats ? errCard(`Couldn’t load ${CFG.TERM_LABEL} classes.`, 'retrySeats') : loadingCard(`Loading ${CFG.TERM_LABEL} classes…`);
  const rows = exploreRows();""",
    """  if (!TC.seatsLoaded) return TC.err.seats ? errCard(`Couldn’t load ${CFG.TERM_LABEL} classes.`, 'retrySeats') : loadingCard(`Loading ${CFG.TERM_LABEL} classes…`);
  return exploreListBody();
}
function exploreListBody() {
  const rows = exploreRows();""")

# Explore: the words beside Filters are the switch (Classes only, only while the two terms differ)
rep("""<div class="row" style="gap:8px">${S.subj !== 'All' ? `<span class="muted b" style="font-size:13px">${esc(subjLabel(S.subj))}</span>` : `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`}""",
    """<div class="row" style="gap:8px">${exTermCtl()}""")
rep("""SCREENS.explore = () => {""",
    """/* The term words beside Filters (Tate, 2026-10-10): in Classes, while there are two terms, they are a switch —
   Spring 2027 (what people pick classes for; always where Explore starts) or Fall 2026 (what friends are in). */
function exTermCtl() {
  const subj = S.subj !== 'All' ? `<span class="muted b" style="font-size:13px">${esc(subjLabel(S.subj))}</span>` : '';
  if (!(S.exMode === 'classes' && splitTerms())) return subj || `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`;
  const on = exNow(), L = on ? nowTerm().label : CFG.TERM_LABEL, other = on ? CFG.TERM_LABEL : nowTerm().label;
  return `${subj}<button class="exterm muted b" data-a="exTerm" aria-label="${esc('Showing ' + L + ' classes. Switch to ' + other)}">${esc(L)}${ic('updown', 14, 2.6)}</button>`;
}
SCREENS.explore = () => {""")

# the class page: the now-term's, read-only
rep("""SCREENS.classDetail = ({ code }) => {
""",
    """SCREENS.classDetail = ({ code, term }) => {
  if (term && splitTerms() && term === nowTerm().code) return classDetailNow(code);
""")
rep("""function missingScreen(t) {""",
    """/* A class page for the term people are in now (2026-10-10): its sections under their professors, read-only —
   no +, no Watch (registration is for TERM) — each with the friends in it, opening that section's sheet. */
function classDetailNow(code) {
  const L = nowTerm().label;
  if (!nowAllReady()) {
    const st = NOWT.term === nowTerm().code ? NOWT.codes[code] : undefined;
    if (st === 'err') return { body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button></div>${errCard(`Couldn’t load ${code} for ${L}.`, 'retryNowCode')}`, tabbar: true, fab: true };
    if (st !== 'done') { loadNowCode(code); return missingScreen(`Loading ${code}…`); }
  }
  if (!NOWT.courses[code]) return missingScreen(`${code} isn’t offered in ${L}.`);
  return inNow(() => {
    const c = course(code), desc = c.desc || (CAT_INFO[code] || {}).desc, fr = nowFriendsIn(code), cs = courseSeats(code), mine = nowSecs('me').some(s => s.code === code);
    const order = courseProfs(code).slice().sort((a, b) => (!a) - (!b) || ((ratingOf(b) ?? -1) - (ratingOf(a) ?? -1)));
    const profBlocks = order.map(pid => {
      const ss = secsOf(code).filter(s => s.prof === pid).sort((a, b) => String(a.sec).localeCompare(String(b.sec), undefined, { numeric: true }));
      const pf = TC.friends.filter(f => ss.some(s => nowSecs(f).some(x => x.id === s.id)));
      return `<div class="card" style="margin:0 12px 12px;padding:8px">${classProfHead(pid, pf)}
   ${ss.map(s => {
        const w = nowFriendsInSec(s.id), when = s.async ? 'Online, self-paced' : s.noTime ? 'Time not posted' : daysLabel(s.days) + ' ' + range(s);
        return `<button class="secrow nowrow" data-a="secSheet" data-x="${esc(code)}" data-y="${esc(s.id)}" aria-label="${esc((s.sec ? secLabel(s.sec) + ', ' : '') + when + (w.length ? ', ' + w.map(f => PEOPLE[f].short).join(', ') + ' in it' : ''))}">${secRowT(s)}${secSeatText(s)}${avStack(w, 24)}<span class="chev">${ic('chevR', 18)}</span></button>`;
      }).join('')}
  </div>`;
    }).join('');
    const seatsStat = cs.anyOpen ? (cs.open ? cs.open : 'Open') : cs.allFull ? 'Full' : '—';
    return {
      body: `${classTopBtns(code, false)}
 <div class="hero blue"><div class="row" style="gap:8px;flex-wrap:wrap"><span class="hchip" style="background:#fff;color:#1E40AF">${code}</span><span class="hchip" style="border:1.5px solid rgba(255,255,255,.5)">${esc(L)}</span>${mine ? `<span class="hchip" style="border:1.5px solid rgba(255,255,255,.5)">${ic('check', 14, 3)} Your class</span>` : ''}</div>
  <h1 style="margin-top:12px">${esc(c.title)}</h1>${desc ? `<p class="tc-desc">${esc(desc)}</p>` : `<p style="opacity:.8">${TC.catalogLoaded ? 'No catalog description on file.' : ''}</p>`}
  <div class="stats"><div class="stat"><small>SECTIONS</small><b>${secsOf(code).length}</b></div><div class="stat"><small>FRIENDS</small><b>${fr.length}</b></div><div class="stat"><small>SEATS</small><b>${seatsStat}</b></div></div></div>
 ${fr.length ? `<div class="card row" style="margin:14px 12px 0;padding:12px 14px">${avStack(fr, 30)}<span class="b" style="font-size:14px">${fr.slice(0, 2).map(f => esc(PEOPLE[f].short)).join(', ')}${fr.length > 2 ? ` + ${fr.length - 2} more` : ''} ${fr.length > 1 ? 'are' : 'is'} taking this</span></div>` : ''}
 ${CLASS_SEC_H}
 ${profBlocks}<div class="spacer"></div>`, tabbar: true, fab: true
    };
  });
}
function missingScreen(t) {""")

# the pieces both class pages draw (one place each, so they can't drift apart)
rep("""SCREENS.classDetail = ({ code, term }) => {""",
    """/* What both class pages (TERM's and the now-term's) draw the same way. */
function classTopBtns(code, share = true) { return `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><span class="row" style="gap:8px">${share ? `<button class="iconbtn" data-a="sendCard" data-x="class" data-y="${esc(code)}" aria-label="Send to a friend">${ic('share', 20, 2.2)}</button>` : ''}<button class="iconbtn ${isSaved('c:' + code) ? 'on' : ''}" data-a="save" data-x="c:${code}" aria-label="Save">${ic('bm', 20, 2.2, isSaved('c:' + code) ? 'currentColor' : 'none')}</button></span></div>`; }
function classProfHead(pid, pf) {
  return pid
      ? `<button class="profrow" data-a="openProf" data-x="${esc(pid)}">${profAv(pid, 44, 15)}<div class="grow"><div class="nm">${esc(profName(pid))}</div><div class="row b" style="gap:4px;font-size:14px">${ratingOf(pid) != null ? starI(13, rateTone(ratingOf(pid)).star) + `<span class="rt-${rateTone(ratingOf(pid)).k}" style="color:${rateTone(ratingOf(pid)).ink}">${ratingOf(pid).toFixed(1)}</span>` + `<span class="muted" style="font-weight:700">&nbsp;· ${nRatings(PROFS[pid].count)}</span>` : '<span class="muted">No ratings yet</span>'}</div></div>${avStack(pf, 26)}<span style="color:var(--purple-t,var(--purple))">${ic('chevR', 20)}</span></button>`
      : `<div class="profrow">${avL('?', 44, 15)}<div class="grow"><div class="nm">Instructor not assigned</div><div class="muted b" style="font-size:13px">Listed as Staff for now</div></div>${avStack(pf, 26)}</div>`;
}
const secRowT = s => `<span class="t"><b>${s.sec ? esc(secLabel(s.sec)) + ' ' : ''}${s.async ? 'Online' : s.noTime ? '' : daysLabel(s.days)}</b> <span class="nw">${s.async ? 'self-paced' : s.noTime ? 'Time not posted' : range(s)}</span></span>`;
const CLASS_SEC_H = '<div class="sec-h" style="padding-left:16px"><span>Sections</span></div>';
SCREENS.classDetail = ({ code, term }) => {""")
rep("""    const head = pid
      ? `<button class="profrow" data-a="openProf" data-x="${esc(pid)}">${profAv(pid, 44, 15)}<div class="grow"><div class="nm">${esc(profName(pid))}</div><div class="row b" style="gap:4px;font-size:14px">${ratingOf(pid) != null ? starI(13, rateTone(ratingOf(pid)).star) + `<span class="rt-${rateTone(ratingOf(pid)).k}" style="color:${rateTone(ratingOf(pid)).ink}">${ratingOf(pid).toFixed(1)}</span>` + `<span class="muted" style="font-weight:700">&nbsp;· ${nRatings(PROFS[pid].count)}</span>` : '<span class="muted">No ratings yet</span>'}</div></div>${avStack(pf, 26)}<span style="color:var(--purple-t,var(--purple))">${ic('chevR', 20)}</span></button>`
      : `<div class="profrow">${avL('?', 44, 15)}<div class="grow"><div class="nm">Instructor not assigned</div><div class="muted b" style="font-size:13px">Listed as Staff for now</div></div>${avStack(pf, 26)}</div>`;
""", """    const head = classProfHead(pid, pf);
""")
rep("""      return `<div class="secrow"><span class="t"><b>${s.sec ? esc(secLabel(s.sec)) + ' ' : ''}${s.async ? 'Online' : s.noTime ? '' : daysLabel(s.days)}</b> <span class="nw">${s.async ? 'self-paced' : s.noTime ? 'Time not posted' : range(s)}</span></span>${secSeatText(s)}""",
    """      return `<div class="secrow">${secRowT(s)}${secSeatText(s)}""")
rep("""    body: `<div class="topbtns"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><span class="row" style="gap:8px"><button class="iconbtn" data-a="sendCard" data-x="class" data-y="${esc(code)}" aria-label="Send to a friend">${ic('share', 20, 2.2)}</button><button class="iconbtn ${isSaved('c:' + code) ? 'on' : ''}" data-a="save" data-x="c:${code}" aria-label="Save">${ic('bm', 20, 2.2, isSaved('c:' + code) ? 'currentColor' : 'none')}</button></span></div>
 <div class="hero blue"><div class="row" style="gap:8px;flex-wrap:wrap"><span class="hchip" style="background:#fff;color:#1E40AF">${code}</span><span class="hchip" style="border:1.5px solid rgba(255,255,255,.5)">${esc(CFG.TERM_LABEL)}</span>""",
    """    body: `${classTopBtns(code)}
 <div class="hero blue"><div class="row" style="gap:8px;flex-wrap:wrap"><span class="hchip" style="background:#fff;color:#1E40AF">${code}</span><span class="hchip" style="border:1.5px solid rgba(255,255,255,.5)">${esc(CFG.TERM_LABEL)}</span>""")
rep(""" <div class="sec-h" style="padding-left:16px"><span>Sections</span></div>
 ${profBlocks}<div class="spacer"></div>`, tabbar: true, fab: true
  };
};""", """ ${CLASS_SEC_H}
 ${profBlocks}<div class="spacer"></div>`, tabbar: true, fab: true
  };
};""")

# opening a class: the now-term's page from a now-term place
rep("""  openClass: (code, y, el) => { if (el && el.closest && el.closest('#exlist') && S.q.trim()) recentAdd('c', code); UI.champ = false; go('classDetail', { code }); },""",
    """  openClass: (code, y, el) => {
    const inEx = !!(el && el.closest && el.closest('#exlist'));
    /* the term people are in now: Explore switched to it, a block or chip in a now-term week, a now-term sheet */
    const now = splitTerms() && (y === 'now' || isNowSecId(y) || (inEx && exNow()));
    if (inEx && S.q.trim() && !now) recentAdd('c', code); UI.champ = false;
    const e = cur(), term = now ? nowTerm().code : undefined;
    if (e && e.s === 'classDetail' && e.p && e.p.code === code && (e.p.term || undefined) === term) { UI.sheet = null; return render(true); }   /* View class on the page you're on */
    go('classDetail', now ? { code, term } : { code });
  },
  retryNowCode: () => { const e = cur(), code = e && e.p && e.p.code; if (!code) return; if (NOWT.codes[code] === 'err') delete NOWT.codes[code]; loadNowCode(code); render(true); },
  exTerm: () => { UI.exTerm = UI.exTerm === 'now' ? null : 'now'; S.exLimit = 40; render(true); },
  retryNowAll: () => { NOWT.err = false; loadNowAll(); render(true); },""")

# a now-term section's sheet: found in the full list too; "View class" opens that term's page
rep("""    || nowSecs('me').find(x => x.id === id) || TC.friends.map(f => nowSecs(f).find(x => x.id === id)).find(Boolean); if (!s) return '';""",
    """    || nowSecs('me').find(x => x.id === id) || TC.friends.map(f => nowSecs(f).find(x => x.id === id)).find(Boolean) || (isNowSecId(id) ? NOWT.sec[id] : null); if (!s) return '';""")
rep("""<button class="btn" data-a="openClass" data-x="${code}">View class</button>""",
    """<button class="btn" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>View class</button>""")

# Home's Anytime chips for a class with no section, on a now-term week
rep("""    .concat(loose.map(c => `<button class="any-c${ring(c)}" data-a="openClass" data-x="${esc(c)}" title""",
    """    .concat(loose.map(c => `<button class="any-c${ring(c)}" data-a="openClass" data-x="${esc(c)}"${v.k === 'now' ? ' data-y="now"' : ''} title""")
# My Classes › Fall (read-only) cards
rep("""Object.keys(byCode).map(code => { const ss = byCode[code]; return `<button class="card ccard" style="margin:12px 12px 0;width:calc(100% - 24px)" data-a="openClass" data-x="${code}">""",
    """Object.keys(byCode).map(code => { const ss = byCode[code]; return `<button class="card ccard" style="margin:12px 12px 0;width:calc(100% - 24px)" data-a="openClass" data-x="${code}"${isNowT ? ' data-y="now"' : ''}>""")
rep("""${ts.unplaced.map(code => `<button class="card ccard" style="margin:12px 12px 0;width:calc(100% - 24px)" data-a="openClass" data-x="${code}">""",
    """${ts.unplaced.map(code => `<button class="card ccard" style="margin:12px 12px 0;width:calc(100% - 24px)" data-a="openClass" data-x="${code}"${isNowT ? ' data-y="now"' : ''}>""")
# a friend's page: their Fall list rows
rep("""  const row = (code, sub, mark) => `<button class="li" data-a="openClass" data-x="${code}">""",
    """  const row = (code, sub, mark) => `<button class="li" data-a="openClass" data-x="${code}"${k === 'now' ? ' data-y="now"' : ''}>""")
# Champ's day (your classes now)
rep("""px" data-a="openClass" data-x="${esc(s.code)}"><b>${esc(s.code)}</b><span>${hs(s.s)}–${hs(s.e)}<""",
    """px" data-a="openClass" data-x="${esc(s.code)}" data-y="${esc(s.id || '')}"><b>${esc(s.code)}</b><span>${hs(s.s)}–${hs(s.e)}<""")
# leaving Explore puts it back on TERM (it always starts where people pick classes)
rep("""function setTab(t) { if (t === 'home') UI.storyOrder = null;""",
    """function setTab(t) { if (t !== 'explore') UI.exTerm = null; if (t === 'home') UI.storyOrder = null;""")
# a story's day (today = the term people are in)
rep("""<button class="stbox" data-a="openClass" data-x="${esc(x.code)}">""",
    """<button class="stbox" data-a="openClass" data-x="${esc(x.code)}" data-y="${esc(x.id || '')}">""")

# CSS: the switch keeps the words' look; a read-only section row is a full-width button
rep(""".frow{display:flex;justify-content:space-between;align-items:center;padding:14px 16px 12px}""",
    """.frow{display:flex;justify-content:space-between;align-items:center;padding:14px 16px 12px}
.exterm{display:inline-flex;align-items:center;gap:3px;font-size:13px;min-height:44px;padding:0 2px;color:var(--muted)}
.secrow.nowrow{width:100%;min-height:52px;cursor:pointer}
.secrow.nowrow .chev{color:var(--muted);flex:none}""")

P.write_text(s)
print('explore-term-switch-2026-10-10: ok')
