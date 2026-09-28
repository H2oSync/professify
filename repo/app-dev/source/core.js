/* =================================================================================================
   TERMCHAMP BACKEND — the real data behind App 2.0 (termchamp.com/app)
   =================================================================================================
   App 2.0 was designed as a prototype with invented people, classes and ratings. Everything in
   this block replaces that with the same backend termchamp.com uses: the same Supabase project,
   the same tables, the same sign-in (the session is shared, because both pages live on
   termchamp.com), the same PolyRatings feed.

   THE RULE THIS FILE IS BUILT ON: never show a number or a name we do not have. When the data
   is missing, the screen says so, or leaves the element out. Nothing here invents a rating, a
   seat count, a friend, a message or a time.

   Every read and write is in this block, in one place, so the screens below never talk to the
   database directly. Screens read the objects this fills (COURSES, SECTIONS, PROFS, PEOPLE and
   the TC.* lists) and call TC.* to change anything.
   ================================================================================================= */
window.PROFESSIFY_CONFIG = window.PROFESSIFY_CONFIG || {
  SUPABASE_URL: 'https://rqkndeqbcahozidniesn.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_h7Hllays0O3KRORIKfRdzg_iMBVInrD', // publishable — safe to expose
  SITE_URL: 'https://termchamp.com',
  /* THE TERM — keep these two equal to TERM / TERM_LABEL in the desktop index.html. */
  TERM: '2268',
  TERM_LABEL: 'Fall 2026',
  REGISTRATION_OPENS: '2026-10-19',
  REGISTRATION_TERM: 'Spring 2027',
  /* Off, as on the desktop (its button renders only when this is on). */
  GOOGLE_SIGNIN_ENABLED: false
};
const CFG = window.PROFESSIFY_CONFIG;
const POLYRATINGS_API = 'https://api-prod.polyratings.org';

/* The live data. The screens were written against these names, so they keep them; they start
   empty and are filled by TC.load(). */
let COURSES = {};      // 'BUS 4437' → {title, short, units, prereq, desc}
let SECTIONS = [];     // one per real section this term
let SEC = {};          // class number → section
let SECS_BY_CODE = {}; // 'BUS 4437' → [sections]
let PROFS = {};        // professor key → {name, ini, dept, r, count, …}
let PEOPLE = { me: { name: 'You', short: 'You', ini: '?', color: '#FDBA74', secs: [] } };

const TC = {
  sb: null, user: null, profile: null,
  ready: false,            // signed in and the first load finished
  phase: 'boot',           // boot → signin | noprofile | ok
  err: {},                 // per-area load failures, so a screen can say "couldn't load" instead of "none"
  seatsLoaded: false, profsLoaded: false,
  mySecs: [],              // the student's own registered classes (my_sections), as section objects
  myUnplaced: [],          // my classes we know the code of but not a time
  friends: [], requests: [], sent: [], suggestions: [],
  threads: [], rows: {},   // conversations, and the messages of the ones opened
  plans: { A: [], B: [], C: [] }, planShared: { A: true, B: true, C: true },
  watches: {},             // class number → true (seat alerts)
  autoWatch: {},           // class numbers this app watched because they were put in a plan
  reviewsBy: {},           // professor key → TermChamp reviews (reviews_public)
  myReviews: [],           // this student's own reviews
  rateList: [],            // [{term, current, items:[[profKey, code]]}]
  names: {}                // user id → {name, avatar} for anyone a thread refers to
};

/* ---------------------------------------------------------------------------------------------
   Small helpers
   --------------------------------------------------------------------------------------------- */
const PALETTE = ['#FDBA74', '#93C5FD', '#FDE68A', '#C4B5FD', '#F9A8D4', '#86EFAC', '#99F6E4', '#A5B4FC', '#FBCFE8'];
function colorFor(id) { let h = 0; const s = String(id || ''); for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return PALETTE[h % PALETTE.length]; }
function initialsOf(n) { const w = String(n || '').trim().split(/\s+/).filter(Boolean); return ((w[0] || '?')[0] + (w.length > 1 ? w[w.length - 1][0] : '')).toUpperCase(); }
function canonCode(c) { const m = /^([A-Z&]{2,5})\s*(\d{3,4}[A-Z]?)$/.exec(String(c || '').toUpperCase().replace(/\s+/g, ' ').trim()); return m ? m[1] + ' ' + m[2] : null; }
function schemaGap(err) { if (!err) return false; const c = String(err.code || ''), m = String(err.message || ''); return c === '42703' || c === '42P01' || c === 'PGRST204' || c === 'PGRST205' || /does not exist|schema cache/i.test(m); }
function agoText(iso) {
  if (!iso) return '';
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return 'now'; if (s < 3600) return Math.floor(s / 60) + 'm'; if (s < 86400) return Math.floor(s / 3600) + 'h';
  if (s < 604800) return Math.floor(s / 86400) + 'd';
  try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); } catch (e) { return ''; }
}

/* A meeting string from the seat feed or an import: "MoWe 4:10PM - 6:00PM", also "MWF 9:10 AM-10:00 AM".
   Returns {days:'MW', s, e} in the letters the screens use (R = Thursday), or null when there is no
   usable day AND time. Ported from the desktop's parseMeet, which learned these shapes the hard way. */
function parseMeet(str) {
  if (!str) return null; str = String(str).trim();
  if (/tba/i.test(str)) return null;
  str = str.replace(/^\s*([MTWRFU]{2,6})(?=[\s,]|$)/, tok => tok.toUpperCase().split('').map(ch => ({ M: 'Mo', T: 'Tu', W: 'We', R: 'Th', F: 'Fr', U: 'Su' }[ch] || '')).join(''));
  const dm = str.match(/^((?:Mo|Tu|We|Th|Fr|Sa|Su)+)/); if (!dm) return null;
  const two = dm[1].match(/Mo|Tu|We|Th|Fr|Sa|Su/g) || [];
  const tm = str.match(/(\d{1,2}):(\d{2})\s*([AaPp][Mm])\s*[–—-]\s*(\d{1,2}):(\d{2})\s*([AaPp][Mm])/);
  if (!tm || !two.length) return null;
  const to24 = (h, mi, ap) => { h = +h; mi = +mi; ap = ap.toUpperCase(); if (ap === 'PM' && h !== 12) h += 12; if (ap === 'AM' && h === 12) h = 0; return h * 60 + mi; };
  const s = to24(tm[1], tm[2], tm[3]), e = to24(tm[4], tm[5], tm[6]);
  if (e <= s) return null;
  const L = { Mo: 'M', Tu: 'T', We: 'W', Th: 'R', Fr: 'F', Sa: 'S', Su: 'U' };
  return { days: two.map(d => L[d]).join(''), s, e };
}
/* Section status, ported from the desktop's seatStatusOf: a status we do not recognise and no
   seats is "unknown", never "full". */
function seatStatusOf(raw, available) {
  const t = String(raw == null ? '' : raw).trim().toLowerCase().replace(/[\s_-]+/g, '');
  if (t === 'waitlist' || t === 'waitlisted' || t === 'wl') return 'wait';
  if (t === 'closed' || t === 'full' || t === 'cancelled' || t === 'canceled') return 'full';
  if (t === 'open' || t === 'available') return 'open';
  return available > 0 ? 'open' : 'unknown';
}
/* "Examplewood, Ada" or "Ada Examplewood" → one key per person. Staff/TBA → '' (no professor). */
function profKeyOf(instructor) {
  let n = String(instructor || '').trim();
  if (!n || /^(staff|tba|tbd|to be announced)$/i.test(n)) return '';
  n = n.split(/\s*[;\/]\s*|\s+and\s+/i)[0];                  // co-taught: the first named
  if (n.indexOf(',') >= 0) { const [l, f] = n.split(','); n = (f || '').trim().split(/\s+/)[0] + ' ' + (l || '').trim(); }
  const w = n.toLowerCase().replace(/[.]/g, '').split(/\s+/).filter(Boolean);
  if (!w.length) return '';
  return w.length > 1 ? w[0] + ' ' + w[w.length - 1] : w[0];
}
function displayName(key) { return String(key || '').split(' ').map(x => x ? x[0].toUpperCase() + x.slice(1) : x).join(' '); }
function ensureProf(key, name) {
  if (!key) return null;
  if (!PROFS[key]) PROFS[key] = { name: name || displayName(key), ini: initialsOf(name || displayName(key)), dept: '', r: null, count: 0,
    color: colorFor(key), prId: null, again: null, diff: null, tags: [], dist: null, reviews: [], nReviews: 0 };
  return PROFS[key];
}
function addSection(sec) {
  SECTIONS.push(sec); SEC[sec.id] = sec;
  (SECS_BY_CODE[sec.code] = SECS_BY_CODE[sec.code] || []).push(sec);
}

/* ---------------------------------------------------------------------------------------------
   Sign-in
   --------------------------------------------------------------------------------------------- */
TC.client = function () {
  if (TC.sb) return TC.sb;
  if (!window.supabase || !window.supabase.createClient) return null;
  TC.sb = window.supabase.createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } });
  TC.sb.auth.onAuthStateChange((ev, session) => {
    const was = TC.user && TC.user.id, now = session && session.user && session.user.id;
    if (was === now) return;
    /* Signing out, or switching account, starts clean: nothing of one student's friends, classes
       or messages stays in memory for the next. */
    if (was) { try { location.replace(location.pathname); } catch (e) { location.reload(); } return; }
    TC.user = session ? session.user : null;
    if (now) TC.load();
  });
  return TC.sb;
};
TC.signInGoogle = async function () {
  const sb = TC.client(); if (!sb) return toast('Could not reach TermChamp. Check your connection.');
  const r = await sb.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: location.origin + '/app/' } });
  if (r.error) toast(r.error.message);
};
TC.signInPassword = async function (email, pw) {
  const sb = TC.client(); if (!sb) return 'Could not reach TermChamp.';
  const r = await sb.auth.signInWithPassword({ email, password: pw });
  return r.error ? r.error.message : null;
};
TC.sendCode = async function (email) {
  const sb = TC.client(); if (!sb) return 'Could not reach TermChamp.';
  /* shouldCreateUser:false — a brand-new account is made on termchamp.com, where the setup
     (school, major, username) lives. Here we only sign existing students in. */
  const r = await sb.auth.signInWithOtp({ email, options: { shouldCreateUser: false } });
  return r.error ? r.error.message : null;
};
TC.verifyCode = async function (email, code) {
  const sb = TC.client(); if (!sb) return 'Could not reach TermChamp.';
  const r = await sb.auth.verifyOtp({ email, token: code, type: 'email' });
  return r.error ? r.error.message : null;
};
TC.signOut = async function () { try { await TC.client().auth.signOut(); } catch (e) {} location.replace(location.pathname); };

/* ---------------------------------------------------------------------------------------------
   The load. Public data (seats, PolyRatings) and the student's own data run side by side.
   --------------------------------------------------------------------------------------------- */
TC.boot = async function () {
  const sb = TC.client();
  if (!sb) { TC.phase = 'offline'; render(); return; }
  hydrateSeatsFromCache();
  loadSeats(); loadPolyRatings();
  try { if ('serviceWorker' in navigator && window.isSecureContext && location.protocol !== 'file:') navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {}); } catch (e) {}
  const { data } = await sb.auth.getSession();
  TC.user = data && data.session ? data.session.user : null;
  if (!TC.user) { TC.phase = 'signin'; render(); return; }
  await TC.load();
};
TC.load = function () {
  /* The session can arrive twice at start-up (the auth event and getSession). One load. */
  if (TC._loading) return TC._loading;
  TC._loading = loadAll().finally(() => { TC._loading = null; });
  return TC._loading;
};
async function loadAll() {
  const sb = TC.client(); if (!sb || !TC.user) return;
  TC.loadedAt = Date.now();
  const me = TC.user.id;
  const p = await sb.from('profiles').select('id,display_name,username,avatar_url,major,class_standing').eq('id', me).maybeSingle();
  if (p.error && !schemaGap(p.error)) TC.err.profile = p.error.message;
  TC.profile = p.data || null;
  if (!TC.profile) { TC.phase = 'noprofile'; render(); return; }
  const nm = TC.profile.display_name || TC.profile.username || 'You';
  PEOPLE.me = Object.assign(PEOPLE.me, { name: nm, short: nm.split(/\s+/)[0], ini: initialsOf(nm), avatar: TC.profile.avatar_url || '', color: colorFor(me), handle: TC.profile.username || '' });
  TC.phase = 'ok'; render();
  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), loadThreads()]);
  loadSuggestions(); loadRateList();
  TC.ready = true; render(true);
  startRealtime();
}
TC.refresh = function () { if (TC.user) TC.load(); };

/* ---- Seats: the whole term, paged, all-or-nothing (a partial term is confidently wrong about
   every class on the pages that never arrived — the desktop's rule, kept). ---------------------- */
const SEATS_CACHE = 'termchamp_app_seats_v1';
function applySeatRows(rows) {
  COURSES = {}; SECTIONS = []; SEC = {}; SECS_BY_CODE = {};
  const seen = {};
  rows.forEach(r => {
    const code = canonCode(r.course_code); if (!code) return;
    const nbr = String(r.class_nbr || '').trim(); if (!nbr || seen[nbr]) return; seen[nbr] = 1;
    if (!COURSES[code]) COURSES[code] = { title: (r.title || '').trim() || code, units: null, prereq: null, desc: null };
    const m = parseMeet(r.days);
    /* The desktop's secMode rule: asynchronous only when the mode says so in words. */
    const mode = String(r.instruction_mode || r.mode || '').toLowerCase().trim();
    const isAsync = /asynchron|\basync\b|self[- ]paced/.test(mode);
    const av = r.available == null ? null : Math.max(0, r.available);
    const st = seatStatusOf(r.status, av || 0);
    const pk = profKeyOf(r.instructor);
    if (pk) { const P = ensureProf(pk); P.teaches = P.teaches || {}; P.teaches[code] = (P.teaches[code] || 0) + 1; }
    addSection({ id: nbr, code, sec: String(r.section || '').trim(), prof: pk, days: m ? m.days : '', s: m ? m.s : null, e: m ? m.e : null,
      async: isAsync, noTime: !m && !isAsync, seats: st === 'open' ? av : (st === 'unknown' ? null : 0), status: st, cap: r.capacity, wl: r.waitlist_total || 0,
      location: r.location || '', rawDays: r.days || '', instructor: (r.instructor || '').trim() });
  });
  Object.keys(COURSES).forEach(c => { COURSES[c].short = shortTitle(COURSES[c].title); });
  TC.seatsLoaded = true;
}
function shortTitle(t) { t = String(t || ''); return t.length <= 22 ? t : t.slice(0, 21).replace(/\s+\S*$/, '') + '…'; }
function hydrateSeatsFromCache() {
  try { const c = JSON.parse(localStorage.getItem(SEATS_CACHE) || 'null'); if (c && c.term === CFG.TERM && Array.isArray(c.rows) && c.rows.length) { applySeatRows(c.rows); TC.seatsAt = c.at; } } catch (e) {}
}
async function loadSeats() {
  const base = CFG.SUPABASE_URL.replace(/\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const BASE = 'course_code,title,section,instructor,days,status,capacity,enrolled,available,waitlist_total,waitlist_capacity,class_nbr';
  let sel = BASE;
  try {
    for (const extra of ['instruction_mode,location', 'instruction_mode']) {
      const pr = await fetch(base + '/rest/v1/course_seats?term=eq.' + encodeURIComponent(CFG.TERM) + '&select=' + BASE + ',' + extra + '&limit=1', { headers: hdr });
      if (pr.ok) { sel = BASE + ',' + extra; break; }
    }
  } catch (e) {}
  let rows = [], complete = false;
  try {
    for (let off = 0; off < 40000; off += 1000) {
      const res = await fetch(base + '/rest/v1/course_seats?term=eq.' + encodeURIComponent(CFG.TERM) + '&select=' + sel + '&order=course_code.asc,class_nbr.asc&limit=1000&offset=' + off, { headers: hdr });
      if (!res.ok) break;
      const part = await res.json(); if (!Array.isArray(part)) break;
      rows = rows.concat(part);
      if (part.length < 1000) { complete = true; break; }
    }
  } catch (e) {}
  if (!complete || !rows.length) { TC.err.seats = true; render(true); return; }
  delete TC.err.seats;
  applySeatRows(rows); TC.seatsAt = Date.now();
  try { localStorage.setItem(SEATS_CACHE, JSON.stringify({ term: CFG.TERM, at: TC.seatsAt, rows })); } catch (e) {}
  relinkPeople(); loadCatalog(); matchPolyRatings(); render(true);
}
/* Descriptions and prerequisites: the scraper's course_catalog (read with the public key). */
async function loadCatalog() {
  if (TC.catalogLoaded) return;
  const base = CFG.SUPABASE_URL.replace(/\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  try {
    for (let off = 0; off < 20000; off += 1000) {
      const res = await fetch(base + '/rest/v1/course_catalog?select=course_code,prereqs,description&order=course_code.asc&limit=1000&offset=' + off, { headers: hdr });
      if (!res.ok) return;
      const part = await res.json(); if (!Array.isArray(part)) return;
      part.forEach(r => { const c = canonCode(r.course_code); if (c && COURSES[c]) { COURSES[c].desc = cleanDesc(r.description); COURSES[c].prereq = cleanPrereq(r.prereqs); } });
      if (part.length < 1000) break;
    }
    TC.catalogLoaded = true; render(true);
  } catch (e) {}
}
/* The scraper stored the class-search page around some descriptions (seat tables, notes): keep only
   what follows the page's own "Description" label when that chrome is present. The desktop's rule. */
function cleanDesc(t) {
  t = String(t || '').replace(/\s+/g, ' ').trim(); if (!t) return null;
  const CH = /Enrl Tot|Wait Tot|Class Notes|Selected Topic Courses|https?:\/\//;
  if (CH.test(t)) {
    const re = /Enrl Tot|Wait Tot|Class Notes|Selected Topic Courses webpage:?|https?:\/\/\S+|(Open|Closed|Wait List) \d+ \d+/g; let m, end = 0;
    while ((m = re.exec(t))) end = m.index + m[0].length;
    const lab = /\bDescription\s+(?=[A-Z])/g; lab.lastIndex = end; const l = lab.exec(t);
    if (!l) return null; t = t.slice(l.index + l[0].length);
  }
  t = t.replace(/^Offered at Solano Campus\.\s*/i, '');
  return t || null;
}
function cleanPrereq(t) { t = String(t || '').replace(/^\s*(Prerequisite|Prerequisites|Corequisite)s?:\s*/i, '').replace(/\.\s*$/, '').trim(); return t || null; }

/* ---- PolyRatings: the overall rating and how many evaluations it stands on. Nothing else from
   it is shown — the desktop decided per-course numbers from it cannot be trusted (2026-08-31). -- */
let PR_LIST = null;
async function loadPolyRatings() {
  try { const c = JSON.parse(localStorage.getItem('professify_prof_cache') || 'null'); if (c && Array.isArray(c.list) && c.list.length) { PR_LIST = c.list; matchPolyRatings(); } } catch (e) {}
  try {
    const res = await fetch(POLYRATINGS_API + '/professors.all', { headers: { accept: 'application/json' } });
    if (!res.ok) { TC.err.poly = true; return; }
    const j = await res.json();
    let list = (j && j.result && j.result.data) || (Array.isArray(j) ? j : null);
    if (list && !Array.isArray(list) && Array.isArray(list.json)) list = list.json;
    if (!Array.isArray(list) || !list.length) { TC.err.poly = true; return; }
    PR_LIST = list; delete TC.err.poly; matchPolyRatings(); render(true);
  } catch (e) { TC.err.poly = true; }
}
function matchPolyRatings() {
  if (!PR_LIST) return;
  const byName = {};
  PR_LIST.forEach(p => { if (!p || typeof p.overallRating !== 'number') return; const k = profKeyOf(((p.firstName || '') + ' ' + (p.lastName || '')).trim()); if (k) (byName[k] = byName[k] || []).push(p); });
  Object.keys(PROFS).forEach(k => {
    const hits = byName[k]; const P = PROFS[k];
    if (!hits) return;
    /* Two PolyRatings entries with the same first+last name: take the one with more evaluations,
       and say nothing about department unless it came from that entry. */
    const p = hits.slice().sort((a, b) => (b.numEvals || 0) - (a.numEvals || 0))[0];
    /* PolyRatings is on a 0–4 scale; every screen in TermChamp reads out of 5 (the desktop's to5()). */
    P.r = Math.round((+p.overallRating / 4 * 5) * 100) / 100; P.count = p.numEvals || 0; P.dept = p.department || P.dept; P.prId = p.id;
    P.name = ((p.firstName || '') + ' ' + (p.lastName || '')).trim() || P.name; P.ini = initialsOf(P.name);
  });
  TC.profsLoaded = true;
}
/* The key TermChamp's own reviews are filed under: "name|department", lowercase — the desktop's
   profKey(). Reviews are matched by name as well, as the desktop does, so a department change
   doesn't split a professor's reviews in two. */
function reviewKeyOf(pk) { const P = PROFS[pk]; return P ? ((P.name || '') + '|' + (P.dept || '')).toLowerCase().trim() : ''; }

/* ---- My own classes (my_sections, this term). ------------------------------------------------- */
/* saved_classes decides WHICH classes are yours; my_sections only adds the section detail to
   them. A section row whose class is no longer saved is leftover, and is not shown — the
   desktop's rule (2026-08-30), for the same reason: it brought removed classes back. */
async function loadMine() {
  const sb = TC.client(), me = TC.user.id;
  const [codes, secs] = await Promise.all([
    sb.from('saved_classes').select('code').eq('user_id', me).eq('term', CFG.TERM),
    sb.from('my_sections').select('code,class_nbr,section,instructor,days,status,wl_pos').eq('user_id', me).eq('term', CFG.TERM)
  ]);
  if (codes.error) { TC.err.mine = codes.error.message; return; }
  delete TC.err.mine;
  const mine = [...new Set((codes.data || []).map(r => canonCode(r.code)).filter(Boolean))];
  TC.mineRows = { secs: secs.error ? [] : (secs.data || []), saved: mine };
  relinkPeople();
}
/* A person's classes as section objects. A class number we have in the seat feed uses the real
   section (real times, real professor). A row the feed does not have but that carries its own
   meeting string gets a section built from that string alone. A row with neither is listed by
   code only and never drawn on a week. */
function secsFromRows(uid, rows, saved) {
  const out = [], unplaced = [], keep = new Set(saved || []);
  (rows || []).forEach(r => {
    const code = canonCode(r.code); if (!code || !keep.has(code)) return;
    const nbr = r.class_nbr != null ? String(r.class_nbr) : '';
    if (nbr && SEC[nbr]) { out.push(SEC[nbr]); return; }
    const m = parseMeet(r.days);
    if (m) { const pk = profKeyOf(r.instructor); if (pk) ensureProf(pk); out.push({ id: 'x:' + uid + ':' + code + ':' + nbr, code, sec: r.section || '', prof: pk, days: m.days, s: m.s, e: m.e, async: false, seats: null, status: 'unknown', offFeed: true }); return; }
  });
  /* A saved class with no usable section is still one of their classes: listed, never drawn. */
  keep.forEach(code => { if (!out.some(s => s.code === code)) unplaced.push(code); });
  return { secs: out, unplaced };
}
function relinkPeople() {
  if (TC.mineRows) { const m = secsFromRows('me', TC.mineRows.secs, TC.mineRows.saved); TC.mySecs = m.secs; TC.myUnplaced = m.unplaced; PEOPLE.me.secs = m.secs; PEOPLE.me.unplaced = m.unplaced; }
  (TC.friendRows ? Object.keys(TC.friendRows) : []).forEach(uid => { if (!PEOPLE[uid]) return; const m = secsFromRows(uid, TC.friendRows[uid].secs, TC.friendRows[uid].saved); PEOPLE[uid].secs = m.secs; PEOPLE[uid].unplaced = m.unplaced; });
}

/* ---- Friends, requests, and their classes. ---------------------------------------------------- */
function personFrom(p) {
  const nm = (p && (p.display_name || p.username)) || 'Classmate';
  return { id: p.id, name: nm, short: nm.split(/\s+/)[0], ini: initialsOf(nm), color: colorFor(p.id), avatar: p.avatar_url || '', handle: p.username || '', secs: [], unplaced: [] };
}
async function loadFriends() {
  const sb = TC.client(), me = TC.user.id;
  const rq = await sb.from('friend_requests').select('*').or('from_user.eq.' + me + ',to_user.eq.' + me);
  if (rq.error) { TC.err.friends = rq.error.message; return; }
  delete TC.err.friends;
  const all = rq.data || [];
  const acc = all.filter(r => r.status === 'accepted');
  const incoming = all.filter(r => r.status === 'pending' && r.to_user === me);
  const outgoing = all.filter(r => r.status === 'pending' && r.from_user === me);
  const ids = [...new Set(acc.map(r => r.from_user === me ? r.to_user : r.from_user))].filter(x => x && x !== me);
  const other = [...new Set(ids.concat(incoming.map(r => r.from_user), outgoing.map(r => r.to_user)))];
  if (other.length) {
    let profs = null;
    for (const sel of ['id,display_name,username,avatar_url,major', 'id,display_name,username,avatar_url']) {
      const r = await sb.from('profiles').select(sel).in('id', other);
      if (!r.error) { profs = r.data; break; }
      if (!schemaGap(r.error)) break;
    }
    (profs || []).forEach(p => { PEOPLE[p.id] = Object.assign(PEOPLE[p.id] || {}, personFrom(p), { major: p.major || '' }); TC.names[p.id] = { name: PEOPLE[p.id].name, avatar: PEOPLE[p.id].avatar }; });
  }
  TC.friends = ids.filter(id => PEOPLE[id]);
  TC.requests = incoming.map(r => r.from_user).filter(id => PEOPLE[id]);
  TC.requestIds = Object.fromEntries(incoming.map(r => [r.from_user, r.id]));
  TC.sentIds = Object.fromEntries(outgoing.map(r => [r.to_user, r.id]));
  TC.sent = outgoing.map(r => r.to_user);
  TC.friendRows = {};
  if (ids.length) {
    const [secs, saved, hist] = await Promise.all([
      sb.from('my_sections').select('user_id,code,class_nbr,section,instructor,days,status').in('user_id', ids).eq('term', CFG.TERM),
      sb.from('saved_classes').select('user_id,code').in('user_id', ids).eq('term', CFG.TERM),
      sb.from('class_history').select('user_id,code,term,year,professor').in('user_id', ids)
    ]);
    ids.forEach(id => { TC.friendRows[id] = { secs: [], saved: [] }; });
    if (!secs.error) (secs.data || []).forEach(r => { if (TC.friendRows[r.user_id]) TC.friendRows[r.user_id].secs.push(r); });
    else TC.err.friendSecs = secs.error.message;
    if (!saved.error) (saved.data || []).forEach(r => { const c = canonCode(r.code); if (c && TC.friendRows[r.user_id]) TC.friendRows[r.user_id].saved.push(c); });
    else TC.err.friendSecs = saved.error.message;
    /* What friends have already TAKEN, with the professor they named — the only source for
       "friends who took this professor". A row with no professor is not guessed at. */
    TC.took = {};
    if (!hist.error) (hist.data || []).forEach(h => {
      const pk = profKeyOf(h.professor), code = canonCode(h.code); if (!pk || !code) return;
      (TC.took[pk] = TC.took[pk] || []).push({ uid: h.user_id, code, when: [h.term, h.year].filter(Boolean).join(' ') });
    });
  }
  relinkPeople();
}
async function loadSuggestions() {
  try {
    const r = await TC.client().rpc('suggest_friends', { p_limit: 12 });
    if (r.error || !Array.isArray(r.data)) return;
    TC.suggestions = [];
    r.data.forEach(x => {
      const id = x.id || x.user_id; if (!id || id === TC.user.id || TC.friends.indexOf(id) >= 0) return;
      PEOPLE[id] = Object.assign(PEOPLE[id] || {}, personFrom({ id, display_name: x.display_name, username: x.username, avatar_url: x.avatar_url }));
      PEOPLE[id].sub = suggestionReason(x);
      TC.suggestions.push(id);
    });
    render(true);
  } catch (e) {}
}
/* The server decides ONE reason per person. Say only what it said. */
function suggestionReason(x) { return String(x.reason || '').trim(); }
/* One relationship per pair: never ask someone who is already a friend, already asked, or has
   already asked you (the desktop's rule, 2026-08-26). */
TC.relation = function (id) {
  if (TC.friends.indexOf(id) >= 0) return 'friends';
  if (TC.sent.indexOf(id) >= 0) return 'sent';
  if (TC.requests.indexOf(id) >= 0) return 'incoming';
  return '';
};
TC.sendRequest = async function (id) {
  const rel = TC.relation(id);
  if (rel === 'friends') { toast('You two are already friends'); return false; }
  if (rel === 'incoming') { toast('They already asked you — accept it in Friends'); return false; }
  if (rel === 'sent' || id === TC.user.id) return false;
  const r = await TC.client().from('friend_requests').insert({ from_user: TC.user.id, to_user: id, status: 'pending' }).select('id').maybeSingle();
  if (r.error && !/duplicate/i.test(r.error.message || '')) { toast('Couldn’t send the request — check your connection'); return false; }
  TC.sent.push(id); if (r.data && r.data.id) TC.sentIds[id] = r.data.id; return true;
};
TC.cancelRequest = async function (id) {
  const q = TC.sentIds && TC.sentIds[id]
    ? TC.client().from('friend_requests').delete().eq('id', TC.sentIds[id])
    : TC.client().from('friend_requests').delete().eq('from_user', TC.user.id).eq('to_user', id).eq('status', 'pending');
  const r = await q;
  if (r.error) { toast('Couldn’t cancel the request'); return false; }
  TC.sent = TC.sent.filter(x => x !== id); return true;
};
TC.acceptRequest = async function (id) {
  const rid = TC.requestIds[id]; if (!rid) return false;
  const r = await TC.client().from('friend_requests').update({ status: 'accepted' }).eq('id', rid);
  if (r.error) { toast('Couldn’t accept the request — try again'); return false; }
  await loadFriends(); return true;
};
TC.declineRequest = async function (id) {
  const rid = TC.requestIds[id]; if (!rid) return false;
  const r = await TC.client().from('friend_requests').delete().eq('id', rid);
  if (r.error) { toast('Couldn’t decline the request — try again'); return false; }
  TC.requests = TC.requests.filter(x => x !== id); return true;
};
TC.searchPeople = async function (q) {
  q = String(q || '').trim(); if (q.length < 2) return [];
  const jobs = [Promise.resolve(TC.client().rpc('search_people', { q }))];
  const h = q.replace(/^@/, '');
  if (/^[A-Za-z0-9._]+$/.test(h)) jobs.push(Promise.resolve(TC.client().rpc('find_profile_by_handle', { handle: h })).catch(() => ({ data: [] })));
  const res = await Promise.all(jobs);
  if (res[0] && res[0].error) throw res[0].error;
  const seen = {}, out = [];
  res.forEach(r => ((r && r.data) || []).forEach(p => {
    if (!p || !p.id || p.id === TC.user.id || seen[p.id]) return; seen[p.id] = 1;
    PEOPLE[p.id] = Object.assign(PEOPLE[p.id] || {}, personFrom(p)); out.push(p.id);
  }));
  return out;
};

/* ---- Plans A–C (the same plans table and rules the desktop's Plans use). ---------------------- */
const PLAN_LOCAL = 'termchamp_app_plans_v1';
async function loadPlans() {
  try { const c = JSON.parse(localStorage.getItem(PLAN_LOCAL) || 'null'); if (c && c.uid === TC.user.id && c.term === CFG.TERM) TC.autoWatch = c.autoWatch || {}; } catch (e) {}
  const r = await TC.client().from('plans').select('slot,sections,shared').eq('user_id', TC.user.id).eq('term', CFG.TERM);
  if (r.error) { TC.err.plans = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.plans;
  TC.plans = { A: [], B: [], C: [] };
  (r.data || []).forEach(row => {
    if (!TC.plans[row.slot]) return;
    TC.plans[row.slot] = (Array.isArray(row.sections) ? row.sections : []).map(x => String(x.class_nbr)).filter(Boolean);
    TC.planShared[row.slot] = row.shared !== false;
  });
}
function savePlanLocal() { try { localStorage.setItem(PLAN_LOCAL, JSON.stringify({ uid: TC.user.id, term: CFG.TERM, autoWatch: TC.autoWatch })); } catch (e) {} }
const planTimers = {};
TC.setPlan = function (slot, ids) {
  const before = TC.plans[slot].slice();
  TC.plans[slot] = ids.map(String);
  const touched = [...new Set(before.concat(TC.plans[slot]))];
  touched.forEach(syncPlanWatch);
  clearTimeout(planTimers[slot]);
  planTimers[slot] = setTimeout(() => pushPlan(slot), 350);
};
async function pushPlan(slot) {
  const sb = TC.client(); if (!sb || !TC.user) return;
  const list = TC.plans[slot].map(id => { const s = SEC[id]; return s ? { code: s.code, class_nbr: id } : null; }).filter(Boolean);
  const q = list.length
    ? sb.from('plans').upsert({ user_id: TC.user.id, term: CFG.TERM, slot, sections: list, shared: TC.planShared[slot] !== false }, { onConflict: 'user_id,term,slot' })
    : sb.from('plans').delete().eq('user_id', TC.user.id).eq('term', CFG.TERM).eq('slot', slot);
  const r = await q;
  if (r.error) toast('Couldn’t save Plan ' + slot + ' — check your connection');
}
/* Putting a section in a plan watches it (seat alerts). Taking it out of every plan un-watches it
   only if the plan was what watched it — a section watched on its own stays watched. */
function inAnyPlan(id) { return ['A', 'B', 'C'].some(k => TC.plans[k].indexOf(String(id)) >= 0); }
function syncPlanWatch(id) {
  if (!TC.watchesLoaded) return;
  const inP = inAnyPlan(id), w = !!TC.watches[id];
  if (inP && !w && SEC[id]) { TC.watch(id, true); TC.autoWatch[id] = 1; }
  else if (!inP && w && TC.autoWatch[id]) { TC.watch(id, false); delete TC.autoWatch[id]; }
  else if (!inP) delete TC.autoWatch[id];
  savePlanLocal();
}

/* ---- Seat alerts (watch_sections). ------------------------------------------------------------ */
async function loadWatches() {
  const r = await TC.client().from('watch_sections').select('code,class_nbr').eq('user_id', TC.user.id).eq('term', CFG.TERM);
  if (r.error) { TC.err.watches = r.error.message; return; }
  TC.watches = {}; (r.data || []).forEach(w => { if (w.class_nbr) TC.watches[String(w.class_nbr)] = true; });
  TC.watchesLoaded = true;
}
TC.watch = async function (id, on) {
  const s = SEC[id]; if (!s) return false;
  const sb = TC.client();
  const r = on
    ? await sb.from('watch_sections').upsert({ user_id: TC.user.id, term: CFG.TERM, code: s.code, class_nbr: String(id), section: s.sec || null, instructor: s.instructor || null, days: s.rawDays || null })
    : await sb.from('watch_sections').delete().eq('user_id', TC.user.id).eq('term', CFG.TERM).eq('class_nbr', id);
  if (r.error) { toast('Couldn’t update your seat alert'); return false; }
  if (on) TC.watches[id] = true; else delete TC.watches[id];
  return true;
};

/* ---- Reviews: TermChamp's own (reviews_public), and mine. ------------------------------------- */
async function loadReviews() {
  const sb = TC.client();
  const cols = 'professor_key,professor_name,course,score,would_again,tags,note,created_at,difficulty,grade,format';
  let r = await sb.from('reviews_public').select(cols).order('created_at', { ascending: false }).limit(2000);
  if (r.error && schemaGap(r.error)) r = await sb.from('reviews_public').select(cols.replace(',grade', '')).order('created_at', { ascending: false }).limit(2000);
  if (!r.error) {
    TC.reviewsByName = {};
    (r.data || []).forEach(v => { const nm = String(v.professor_key || '').split('|')[0] || String(v.professor_name || '').toLowerCase(); (TC.reviewsByName[nm] = TC.reviewsByName[nm] || []).push(v); });
  } else TC.err.reviews = r.error.message;
  const m = await sb.rpc('my_reviews');
  TC.myReviews = (!m.error && Array.isArray(m.data)) ? m.data : [];
}
/* What TermChamp reviewers said about one professor, and ONLY that — each figure carries the
   number of reviews it stands on. The floors are the desktop's (revRetake/revDifficulty): a
   percentage or an average needs at least 3 answers behind it, or it is not shown. */
const STAT_MIN = 3;
function tcReviewsFor(pk) {
  const P = PROFS[pk]; if (!P || !TC.reviewsByName) return [];
  return TC.reviewsByName[String(P.name || '').toLowerCase().trim()] || [];
}
function reviewStats(pk) {
  const list = tcReviewsFor(pk); const n = list.length;
  if (!n) return null;
  const againN = list.filter(v => v.would_again === true || v.would_again === false);
  const diffN = list.filter(v => typeof v.difficulty === 'number');
  const dist = [5, 4, 3, 2, 1].map(k => Math.round(100 * list.filter(v => Math.round(v.score) === k).length / n));
  const tagCount = {}; list.forEach(v => (v.tags || []).forEach(t => { tagCount[t] = (tagCount[t] || 0) + 1; }));
  return {
    n,
    again: againN.length >= STAT_MIN ? Math.round(100 * againN.filter(v => v.would_again).length / againN.length) : null, againN: againN.length,
    diff: diffN.length >= STAT_MIN ? Math.round(10 * diffN.reduce((a, v) => a + v.difficulty, 0) / diffN.length) / 10 : null, diffN: diffN.length,
    dist, tags: Object.keys(tagCount).sort((a, b) => tagCount[b] - tagCount[a]).slice(0, 5)
  };
}
/* One professor's reviews, read the way the desktop reads them (by that professor's key), so a
   professor with more than the first page of recent reviews still shows all of theirs. */
TC.loadProfReviews = async function (pk) {
  const P = PROFS[pk]; if (!P || !TC.client()) return;
  const nm = String(P.name || '').toLowerCase().trim(); if (!nm) return;
  const cols = 'professor_key,professor_name,course,score,would_again,tags,note,created_at,difficulty,grade,format';
  let r = await TC.client().from('reviews_public').select(cols).ilike('professor_key', nm.replace(/[%_]/g, '') + '|%').order('created_at', { ascending: false }).limit(200);
  if (r.error && schemaGap(r.error)) r = await TC.client().from('reviews_public').select(cols.replace(',grade', '')).ilike('professor_key', nm.replace(/[%_]/g, '') + '|%').order('created_at', { ascending: false }).limit(200);
  if (r.error || !Array.isArray(r.data)) return;
  TC.reviewsByName = TC.reviewsByName || {};
  TC.reviewsByName[nm] = r.data;
  render(true);
};
function iReviewed(pk) {
  const nm = String((PROFS[pk] || {}).name || '').toLowerCase().trim();
  return TC.myReviews.find(v => String(v.professor_key || '').split('|')[0] === nm) || null;
}
/* @@WORDFILTER@@ */
TC.postReview = async function (pk, d) {
  const P = PROFS[pk]; if (!P) return { err: 'Unknown professor' };
  if (iReviewed(pk)) return { err: 'You’ve already reviewed ' + P.name + '. One review per professor keeps the average honest — edit yours on termchamp.com.' };
  const words = String(d.review || '').trim().split(/\s+/).filter(Boolean).length;
  if (words > 300) return { err: 'That’s ' + words + ' words — the limit is 300. Trim ' + (words - 300) + ' and post again; nothing you wrote has been deleted.' };
  const bad = wfHit(d.review || '');
  if (bad) return { err: 'Reviews are public, so “' + bad + '” can’t go in one. Say it about the teaching and post again — nothing you wrote has been deleted.' };
  /* The same hourly cap as the desktop, counted in the same place on this device. The real
     limit is the database's INSERT policy; this only says so before the student is refused. */
  const now = Date.now(); let hits = [];
  try { hits = JSON.parse(localStorage.getItem('professify_rev_times') || '[]'); } catch (e) {}
  hits = (Array.isArray(hits) ? hits : []).filter(t => now - t < 3600000);
  if (hits.length >= 30) return { err: 'That’s 30 reviews in an hour — the limit. Try again a little later.' };
  const row = { professor_key: reviewKeyOf(pk), professor_name: P.name, department: P.dept || null, course: d.code || null, score: d.stars,
    difficulty: d.diff || null, teach_ability: null, hours: null, format: d.format || null, grade: d.grade || null,
    would_again: d.again === 'yes', tags: [], note: (d.review || '').trim() || null };
  let r = await TC.client().from('reviews').insert(row);
  if (r.error && /grade/i.test(r.error.message || '') && schemaGap(r.error)) { const x = Object.assign({}, row); delete x.grade; r = await TC.client().from('reviews').insert(x); }
  if (r.error) {
    const msg = String(r.error.message || '');
    /* The database's own refusals (see professify-review-refusals.sql) are written for students;
       anything else is a raw error, which is not. */
    if (/duplicate|unique/i.test(msg)) return { err: 'You’ve already reviewed ' + P.name + '. One per professor keeps the average honest.' };
    if (r.error.code === 'P0001' && msg && msg.length < 240) return { err: msg };
    if (/row-level security|policy/i.test(msg)) return { err: 'That’s the limit on reviews for now — try again later. Nothing you wrote has been lost.' };
    return { err: 'Couldn’t post your review — check your connection and try again. Nothing you wrote has been lost.' };
  }
  hits.push(now); try { localStorage.setItem('professify_rev_times', JSON.stringify(hits)); } catch (e) {}
  /* Read our own rows back through my_reviews() — the only way this account can see its own
     review ids — so the "show friends" switch has a row to change. */
  const at = new Date().toISOString();
  let id = null;
  try {
    const m = await TC.client().rpc('my_reviews');
    if (!m.error && Array.isArray(m.data)) { TC.myReviews = m.data; const hit = m.data.find(v => v.professor_key === row.professor_key); id = hit ? hit.id : null; }
  } catch (e) {}
  if (!id) TC.myReviews.unshift(Object.assign({}, row, { created_at: at }));
  const nm = String(P.name).toLowerCase().trim();
  if (TC.reviewsByName) (TC.reviewsByName[nm] = TC.reviewsByName[nm] || []).unshift(Object.assign({}, row, { created_at: at, _mine: true }));
  return { id };
};
TC.setShare = async function (id, on) {
  const r = await TC.client().from('reviews').update({ share_with_friends: !!on }).eq('id', id);
  return !r.error;
};
/* Professors to rate: this term's (my_sections) first, then past terms (class_history). */
async function loadRateList() {
  const out = [], seen = {};
  const cur = { term: CFG.TERM_LABEL, current: true, items: [] };
  /* One row per PROFESSOR, because a student reviews a professor once; the form asks which of
     their classes it was when there is more than one. */
  TC.mySecs.forEach(s => { if (s.prof && !seen[s.prof]) { seen[s.prof] = 1; cur.items.push([s.prof, s.code]); } });
  if (cur.items.length) out.push(cur);
  try {
    const r = await TC.client().from('class_history').select('code,term,year,professor').eq('user_id', TC.user.id);
    if (!r.error) {
      TC.myHistory = r.data || [];
      const groups = {};
      (r.data || []).forEach(h => {
        const pk = profKeyOf(h.professor); const code = canonCode(h.code); if (!pk || !code || seen[pk]) return;
        ensureProf(pk, h.professor && h.professor.indexOf(',') < 0 ? h.professor : null); seen[pk] = 1;
        const label = [h.term, h.year].filter(Boolean).join(' ') || 'Earlier';
        (groups[label] = groups[label] || { term: label, items: [], y: +h.year || 0 }).items.push([pk, code]);
      });
      Object.values(groups).sort((a, b) => b.y - a.y).forEach(g => out.push(g));
    }
  } catch (e) {}
  matchPolyRatings();
  TC.rateList = out; render(true);
}

/* ---- Messages. -------------------------------------------------------------------------------- */
async function loadThreads() {
  const sb = TC.client(), me = TC.user.id;
  const mine = await sb.from('conversation_members').select('conversation_id,last_read_at').eq('user_id', me);
  if (mine.error) { TC.err.threads = mine.error.message; return; }
  const ids = (mine.data || []).map(r => r.conversation_id);
  const readAt = Object.fromEntries((mine.data || []).map(r => [r.conversation_id, r.last_read_at]));
  if (!ids.length) { TC.threads = []; return; }
  const [convs, memb, last] = await Promise.all([
    sb.from('conversations').select('id,kind,title,created_by,last_at').in('id', ids),
    sb.from('conversation_members').select('conversation_id,user_id').in('conversation_id', ids),
    sb.from('messages').select('conversation_id,sender,kind,body,created_at').in('conversation_id', ids).order('created_at', { ascending: false }).limit(300)
  ]);
  if (convs.error) { TC.err.threads = convs.error.message; return; }
  const members = {}; ((memb && memb.data) || []).forEach(r => { (members[r.conversation_id] = members[r.conversation_id] || []).push(r.user_id); });
  const lastOf = {}, spoke = {};
  ((last && last.data) || []).forEach(m => { if (!lastOf[m.conversation_id]) lastOf[m.conversation_id] = m; if (m.sender !== me) (spoke[m.conversation_id] = spoke[m.conversation_id] || {})[m.sender] = 1; });
  TC.threads = (convs.data || []).map(c => ({ id: c.id, kind: c.kind, title: c.title, last_at: c.last_at, members: members[c.id] || [], last: lastOf[c.id] || null,
    last_read_at: readAt[c.id], senders: Object.keys(spoke[c.id] || {}) })).sort((a, b) => new Date(b.last_at) - new Date(a.last_at));
  const unknown = [...new Set(TC.threads.flatMap(t => t.members.concat(t.senders)))].filter(u => u !== me && !TC.names[u]);
  if (unknown.length) { const p = await sb.from('profiles').select('id,display_name,username,avatar_url').in('id', unknown); (p.data || []).forEach(x => { TC.names[x.id] = { name: x.display_name || x.username || 'Someone', avatar: x.avatar_url || '' }; }); }
  delete TC.err.threads;
}
function threadOther(t) { const me = TC.user.id; return t.members.find(u => u !== me) || t.senders.find(u => u !== me) || null; }
function nameOf(uid) { if (uid === (TC.user && TC.user.id)) return 'You'; return (PEOPLE[uid] && PEOPLE[uid].name) || (TC.names[uid] && TC.names[uid].name) || 'Someone'; }
function isUnread(t) { return !!(t.last && t.last.sender !== TC.user.id && (!t.last_read_at || new Date(t.last.created_at) > new Date(t.last_read_at))); }
TC.openThread = async function (cid) {
  const r = await TC.client().from('messages').select('*').eq('conversation_id', cid).order('created_at', { ascending: true }).limit(400);
  /* A failed read keeps what was already on screen (the desktop's rule): an empty thread after a
     network blip reads as "your messages are gone". */
  TC.rowsErr = TC.rowsErr || {};
  if (r.error) { TC.rowsErr[cid] = true; if (TC.rows[cid]) toast('Couldn’t load new messages'); render(true); return; }
  delete TC.rowsErr[cid];
  TC.rows[cid] = r.data || [];
  const at = new Date().toISOString();
  TC.client().from('conversation_members').update({ last_read_at: at }).eq('conversation_id', cid).eq('user_id', TC.user.id).then(() => {});
  const t = TC.threads.find(x => x.id === cid); if (t) t.last_read_at = at;
  render(true);
};
TC.send = async function (cid, body) {
  const r = await TC.client().from('messages').insert({ conversation_id: cid, sender: TC.user.id, kind: 'text', body, payload: null }).select().single();
  if (r.error) { toast('Couldn’t send — try again'); return false; }
  (TC.rows[cid] = TC.rows[cid] || []).push(r.data);
  const t = TC.threads.find(x => x.id === cid); if (t) { t.last = r.data; t.last_at = r.data.created_at; }
  TC.threads.sort((a, b) => new Date(b.last_at) - new Date(a.last_at));
  return true;
};
/* One direct thread per pair: find it before making one. */
TC.threadWith = async function (uid) {
  const hit = TC.threads.find(t => t.kind === 'direct' && t.members.length === 2 && t.members.indexOf(uid) >= 0);
  if (hit) return hit.id;
  const sb = TC.client();
  const c = await sb.from('conversations').insert({ kind: 'direct', created_by: TC.user.id }).select().single();
  if (c.error) { toast('Couldn’t start the chat'); return null; }
  const m = await sb.from('conversation_members').insert([{ conversation_id: c.data.id, user_id: TC.user.id }, { conversation_id: c.data.id, user_id: uid }]);
  if (m.error) { toast('Couldn’t start the chat'); return null; }
  await loadThreads();
  return c.data.id;
};
function startRealtime() {
  try {
    const sb = TC.client(); if (!sb || TC.rt) return;
    TC.rt = sb.channel('termchamp-app-messages').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {
      const m = payload.new; if (!m) return;
      const t = TC.threads.find(x => x.id === m.conversation_id);
      if (!t) { loadThreads().then(() => render(true)); return; }
      if (TC.rows[m.conversation_id] && !TC.rows[m.conversation_id].some(x => x.id === m.id)) TC.rows[m.conversation_id].push(m);
      t.last = m; t.last_at = m.created_at;
      if (cur().s === 'chat' && cur().p && cur().p.id === m.conversation_id) { t.last_read_at = new Date().toISOString(); }
      TC.threads.sort((a, b) => new Date(b.last_at) - new Date(a.last_at));
      render(true); if (cur().s === 'chat') scrollEnd();
    }).subscribe();
  } catch (e) {}
}

/* ---- Champ = Hawk. The same `ask` function the desktop uses; the model only names ONE tool, and
   this app answers it from the data above. Signed out or offline, Champ says so. -------------- */
async function evWho() {
  if (TC._who) return TC._who;
  let v = null; try { v = localStorage.getItem('professify_ev_salt'); } catch (e) {}
  if (!v) { try { const a = new Uint8Array(16); crypto.getRandomValues(a); v = Array.from(a).map(x => x.toString(16).padStart(2, '0')).join(''); localStorage.setItem('professify_ev_salt', v); } catch (e) { v = String(Math.random()).slice(2); } }
  try { const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(v + '|v2')); TC._who = Array.from(new Uint8Array(buf)).map(x => x.toString(16).padStart(2, '0')).join('').slice(0, 16); }
  catch (e) { TC._who = ''; }
  return TC._who;
}
TC.ask = async function (q) {
  const sb = TC.client(); if (!sb || !TC.user) return null;
  let tok = null; try { const s = await sb.auth.getSession(); tok = s.data.session && s.data.session.access_token; } catch (e) {}
  if (!tok) return null;
  const who = await evWho();
  const ctl = typeof AbortController === 'function' ? new AbortController() : null;
  const timer = setTimeout(() => { try { ctl && ctl.abort(); } catch (e) {} }, 9000);
  try {
    const nolog = navigator.globalPrivacyControl === true;
    const res = await fetch(CFG.SUPABASE_URL.replace(/\/$/, '') + '/functions/v1/ask', { method: 'POST', headers: { 'content-type': 'application/json', authorization: 'Bearer ' + tok },
      body: JSON.stringify(Object.assign({ q, term: CFG.TERM, who }, nolog ? { nolog: true } : {})), signal: ctl ? ctl.signal : undefined });
    const j = await res.json(); clearTimeout(timer);
    return j && j.tool ? j : null;
  } catch (e) { clearTimeout(timer); return null; }
};
