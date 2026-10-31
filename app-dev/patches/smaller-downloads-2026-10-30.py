#!/usr/bin/env python3
"""Smaller downloads (2026-10-30, for app 1.0.2). Every app open used to download the whole seat list
(~7,850 Spring rows, ~3 MB of JSON in 8 pages plus 1-2 probe reads) and the whole catalog (~2,970 rows,
~1.9 MB in 3 pages). Now:
  · the seat list, the catalog and the Fall list (Explore's term switch) are kept on the phone in
    IndexedDB (this term's seats fall back to localStorage, else memory only; a storage error never
    stops a load). The old localStorage copy (termchamp_app_seats_v1) is shown once, then removed.
  · an open shows the copy at once, then asks only what changed: the class numbers + timestamps
    newer than the copy (less a look-back for the scraper's late writes), then the changed rows by
    class number, plus a HEAD count. A count that doesn't match (a section was removed) is a whole
    download. Whole download: no usable copy, another term, a copy a day old, a schema change, or
    more than 1,500 changed rows (the daily sweep).
  · the catalog: whole download weekly; in between only classes the copy lacks (or, once
    sql/2026-10-30-seats-changed-at.sql runs, only rows that changed).
  · the select that worked is remembered (no probe reads on an open).
  · a seat reload no longer wipes the catalog's descriptions and prerequisites from the classes.
  · coming back to the app checks seats after 2 minutes instead of 10 (a check is now a few KB).
Run: python3 smaller-downloads-2026-10-30.py app/index.html"""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)

# the Fall list (Explore's term switch): kept on the phone too, then only what changed
one(r"""  NOWT.loading = true; NOWT.err = false;
  const base = CFG.SUPABASE_URL.replace(/\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
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
}""", r"""  NOWT.loading = true; NOWT.err = false;
  /* (2026-10-30) the copy on the phone at once, then only what changed */
  const put = rows => { const box = { courses: {}, byCode: {}, sec: {} }; addNowRows(box, rows, t); Object.assign(NOWT, box, { ready: true }); };
  let shown = null;
  const rows = await seatSync(t, 'seats:' + t + ':now', NOW_SELS, r => { if (NOWT.term !== t) return; shown = r; put(r); matchPolyRatings(); render(true); }, null);
  if (NOWT.term !== t) return;
  NOWT.loading = false;
  if (!rows) { if (!NOWT.ready) NOWT.err = true; render(true); return; }
  if (rows !== shown) put(rows);
  matchPolyRatings(); render(true);
}""")

# seats + catalog
one(r"""function hydrateSeatsFromCache() {
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
      let res = await fetch(base + '/rest/v1/course_catalog?select=' + (TC.noCatTitle ? '' : 'title,') + 'course_code,prereqs,description&order=course_code.asc&limit=1000&offset=' + off, { headers: hdr });
      if (!res.ok && off === 0 && !TC.noCatTitle) { TC.noCatTitle = true; res = await fetch(base + '/rest/v1/course_catalog?select=course_code,prereqs,description&order=course_code.asc&limit=1000&offset=0', { headers: hdr }); }
      if (!res.ok) return;
      const part = await res.json(); if (!Array.isArray(part)) return;
      part.forEach(r => { const c0 = canonCode(r.course_code); if (c0) CAT_INFO[c0] = { desc: cleanDesc(r.description), prereq: cleanPrereq(r.prereqs) }; });
      part.forEach(r => { const c = canonCode(r.course_code); const tt = String(r.title || '').replace(/\s+/g, ' ').trim(); if (c && tt && !codeLike(tt)) CAT_TITLE[c] = tt; if (c && COURSES[c]) { COURSES[c].desc = cleanDesc(r.description); COURSES[c].prereq = cleanPrereq(r.prereqs); } });
      if (part.length < 1000) break;
    }
    TC.catalogLoaded = true; render(true);
  } catch (e) {}
}""", r"""/* ---- (2026-10-30) Smaller downloads. The seat lists and the catalog are kept on the phone (IndexedDB; this term's
   seats fall back to localStorage; else memory only) and an open asks only for what changed. A whole download: no
   usable copy, another term, a copy a day old (catalog: a week), or a check that doesn't add up. Storage errors never
   stop a load. ---- */
const DL_KEY = 'termchamp_app_seats_v2', DL_DAY = 864e5, DL_WEEK = 7 * 864e5, DL_MAX = 1500, DL_MS = 30000;
/* how far back a check looks: the scraper stamps updated_at when it reads a row and writes it up to ~40 min later;
   changed_at (sql/2026-10-30-seats-changed-at.sql) is stamped by the database */
const DL_LOOK = { changed_at: 5 * 60000, updated_at: 90 * 60000 };
const SEAT_BASE = 'course_code,title,section,instructor,days,status,capacity,enrolled,available,waitlist_total,waitlist_capacity,class_nbr';
const SEAT_SELS = [SEAT_BASE + ',instruction_mode,location,changed_at', SEAT_BASE + ',instruction_mode,location,updated_at', SEAT_BASE + ',instruction_mode,updated_at', SEAT_BASE + ',updated_at', SEAT_BASE];
const NOW_BASE = 'course_code,title,section,instructor,days,status,capacity,available,waitlist_total,class_nbr';
const NOW_SELS = [NOW_BASE + ',changed_at', NOW_BASE + ',updated_at', NOW_BASE];
const CAT_SELS = ['title,course_code,prereqs,description,changed_at', 'title,course_code,prereqs,description,updated_at', 'course_code,prereqs,description,updated_at', 'course_code,prereqs,description'];
const DLS = { p: null, dead: false }, DLM = {};   /* the database handle; the copies in memory, by key */
function dlsOpen() {
  if (DLS.dead) return Promise.resolve(null);
  if (DLS.p) return DLS.p;
  DLS.p = new Promise(res => {
    const t = setTimeout(() => { DLS.dead = true; res(null); }, 3000);
    try {
      if (!window.indexedDB) { clearTimeout(t); DLS.dead = true; return res(null); }
      const rq = indexedDB.open('termchamp-cache', 1);
      rq.onupgradeneeded = () => { try { rq.result.createObjectStore('kv'); } catch (e) {} };
      rq.onsuccess = () => { clearTimeout(t); const db = rq.result; db.onversionchange = () => { try { db.close(); } catch (e) {} DLS.p = null; }; db.onclose = () => { DLS.p = null; }; res(db); };
      rq.onerror = rq.onblocked = () => { clearTimeout(t); res(null); };
    } catch (e) { clearTimeout(t); DLS.dead = true; res(null); }
  }).then(db => { if (!db) DLS.p = null; return db; });
  return DLS.p;
}
function dlsReq(db, write, fn) {   /* one IndexedDB request with a deadline; never throws */
  return new Promise(res => {
    const t = setTimeout(() => res(undefined), 5000);
    try {
      const tx = db.transaction('kv', write ? 'readwrite' : 'readonly'), rq = fn(tx.objectStore('kv'));
      if (write) tx.oncomplete = () => { clearTimeout(t); res(true); }; else rq.onsuccess = () => { clearTimeout(t); res(rq.result); };
      tx.onerror = tx.onabort = () => { clearTimeout(t); res(undefined); };
    } catch (e) { clearTimeout(t); DLS.p = null; res(undefined); }
  });
}
async function dlsGet(k, ls) {
  try { const db = await dlsOpen(); if (db) { const v = await dlsReq(db, false, st => st.get(k)); if (v) return v; } } catch (e) {}
  if (ls) try { const v = JSON.parse(localStorage.getItem(ls) || 'null'); if (v) return v; } catch (e) {}
  return null;
}
async function dlsSet(k, v, ls) {
  let ok = false;
  try { const db = await dlsOpen(); if (db) ok = !!(await dlsReq(db, true, st => st.put(v, k))); } catch (e) {}
  try { localStorage.removeItem(SEATS_CACHE); } catch (e) {}   /* the old copy (v1, ~3 MB of localStorage) */
  if (ls) {
    try { if (ok) localStorage.removeItem(ls); else { localStorage.setItem(ls, JSON.stringify(v)); ok = true; } }
    catch (e) { try { localStorage.removeItem(ls); } catch (e2) {} }   /* full: no copy, never a broken one */
  }
  return ok;
}
async function dlsPrune() {   /* copies for terms the app no longer shows */
  try {
    const db = await dlsOpen(); if (!db) return;
    const keep = ['seats:' + CFG.TERM, 'seats:' + nowTerm().code + ':now'];
    const ks = await dlsReq(db, false, st => st.getAllKeys()); if (!Array.isArray(ks)) return;
    const old = ks.filter(k => /^seats:/.test(k) && keep.indexOf(k) < 0);
    if (old.length) await dlsReq(db, true, st => { let r = null; old.forEach(k => { r = st.delete(k); }); return r; });
  } catch (e) {}
}
const dlMs = x => { const t = Date.parse(String(x || '').replace(/(\.\d{3})\d+/, '$1')); return isNaN(t) ? 0 : t; };
function dlPack(rows) {   /* column names once, not on every row */
  const cols = [];
  rows.forEach(r => { for (const k in r) if (cols.indexOf(k) < 0) cols.push(k); });
  return { cols, data: rows.map(r => cols.map(k => r[k] === undefined ? null : r[k])) };
}
function dlRows(c, key) {   /* a copy's rows, or null when it can't be trusted */
  try {
    if (!c || c.v !== 2 || typeof c.sel !== 'string' || !c.pack || !Array.isArray(c.pack.cols) || !Array.isArray(c.pack.data) || !c.pack.data.length) return null;
    if (key && c.term !== key) return null;
    const cols = c.pack.cols, rows = c.pack.data.map(a => { if (!Array.isArray(a)) return null; const o = {}; for (let i = 0; i < cols.length; i++) o[cols[i]] = a[i]; return o; });
    return rows.every(r => r && (key ? r.class_nbr != null && String(r.class_nbr) !== '' : r.course_code != null)) ? rows : null;
  } catch (e) { return null; }
}
async function dlGet(path, head) {   /* one read of the public tables, with a deadline: { ok, status, rows | total } */
  const base = CFG.SUPABASE_URL.replace(/\/$/, ''), hdr = { apikey: CFG.SUPABASE_ANON_KEY, Authorization: 'Bearer ' + CFG.SUPABASE_ANON_KEY };
  const ctl = typeof AbortController === 'function' ? new AbortController() : null, t = ctl ? setTimeout(() => ctl.abort(), DL_MS) : 0;
  try {
    const res = await fetch(base + '/rest/v1/' + path, { method: head ? 'HEAD' : 'GET', headers: head ? Object.assign({ Prefer: 'count=exact' }, hdr) : hdr, signal: ctl ? ctl.signal : undefined });
    if (!res.ok) return { ok: false, status: res.status };
    if (head) { const m = /\/(\d+)\s*$/.exec(res.headers.get('content-range') || ''); return m ? { ok: true, total: +m[1] } : { ok: false, status: 0 }; }
    const rows = await res.json(); return Array.isArray(rows) ? { ok: true, rows } : { ok: false, status: 0 };
  } catch (e) { return { ok: false, status: 0 }; } finally { clearTimeout(t); }
}
const dlBad = r => r.status >= 400 && r.status < 500;   /* the request itself is wrong (a column went away): start over */
const dlCol = sel => /(^|,)changed_at(,|$)/.test(sel) ? 'changed_at' : /(^|,)updated_at(,|$)/.test(sel) ? 'updated_at' : '';
function dlMark(rows, col, mark) { if (col) rows.forEach(r => { if (r[col] && dlMs(r[col]) > dlMs(mark)) mark = r[col]; }); return mark || ''; }
function dlMerge(rows, got, key) {   /* changed rows in place; a new one beside its class, else at the end */
  const at = {}; rows.forEach((r, i) => { at[String(r[key])] = i; });
  const out = rows.slice(), add = [];
  got.forEach(r => { const i = at[String(r[key])]; if (i != null) out[i] = r; else { at[String(r[key])] = -1; add.push(r); } });
  add.forEach(r => { let j = -1; for (let k = out.length - 1; k >= 0; k--) if (out[k].course_code === r.course_code) { j = k; break; } if (j < 0) out.push(r); else out.splice(j + 1, 0, r); });
  return out;
}
/* One term's seat rows: the copy at once (shown), then only what changed. null = the network couldn't say. */
async function seatSync(term, key, sels, shown, ls) {
  const q = 'course_seats?term=eq.' + encodeURIComponent(term);
  let m = DLM[key];
  if (!m) { const c = await dlsGet(key, ls), rows = dlRows(c, term); if (rows) { m = DLM[key] = { c: Object.assign({}, c, { pack: null }), rows }; shown(rows, c); } }
  const now = Date.now();
  if (m && m.c.col && sels.indexOf(m.c.sel) >= 0 && dlMs(m.c.mark) && now - m.c.full < DL_DAY && m.c.full < now + 36e5) {
    const d = await seatDelta(q, m.c, m.rows);
    if (d === null) return null;
    if (d !== 'full') {
      const ch = d.rows !== m.rows;
      m = DLM[key] = { c: Object.assign({}, m.c, { at: now, mark: d.mark }), rows: d.rows };
      if (ch) dlsSet(key, Object.assign({}, m.c, { pack: dlPack(d.rows) }), ls);
      return d.rows;
    }
  }
  const f = await seatFull(q, sels);
  if (!f) return null;
  const col = dlCol(f.sel), c = { v: 2, term, sel: f.sel, col, mark: dlMark(f.rows, col, ''), full: now, at: now };
  DLM[key] = { c, rows: f.rows };
  dlsSet(key, Object.assign({}, c, { pack: dlPack(f.rows) }), ls).then(dlsPrune);
  return f.rows;
}
async function seatFull(q, sels) {   /* the whole term, paged, all-or-nothing; the first select the database takes */
  for (let s = 0; s < sels.length; s++) {
    let rows = [];
    for (let off = 0; off < 40000; off += 1000) {
      const r = await dlGet(q + '&select=' + sels[s] + '&order=course_code.asc,class_nbr.asc&limit=1000&offset=' + off);
      if (!r.ok) { if (off === 0 && dlBad(r) && s < sels.length - 1) { rows = null; break; } return null; }
      rows = rows.concat(r.rows);
      if (r.rows.length < 1000) return rows.length ? { rows, sel: sels[s] } : null;
    }
    if (rows) return null;
  }
  return null;
}
/* What changed since the copy: class numbers + stamps first (tiny), then only the rows whose stamp moved, then
   the term's row count — a section removed (or one we missed) means a whole download. */
async function seatDelta(q, c, rows) {
  const col = c.col, from = new Date(dlMs(c.mark) - DL_LOOK[col]).toISOString();
  const count = dlGet(q + '&select=class_nbr', true);
  const have = {}; rows.forEach(r => { have[String(r.class_nbr)] = r[col]; });
  const seen = {}, want = []; let mark = c.mark, last = null;
  for (let i = 0; i < 40; i++) {
    const f = last ? '&or=' + encodeURIComponent('(' + col + '.gt."' + last[col] + '",and(' + col + '.eq."' + last[col] + '",class_nbr.gt."' + last.class_nbr + '"))') : '&' + col + '=gt.' + encodeURIComponent(from);
    const r = await dlGet(q + f + '&select=class_nbr,' + col + '&order=' + col + '.asc,class_nbr.asc&limit=1000');
    if (!r.ok) return dlBad(r) ? 'full' : null;
    r.rows.forEach(x => { const n = String(x.class_nbr); if (!(n in seen) && have[n] !== x[col]) want.push(n); seen[n] = 1; if (dlMs(x[col]) > dlMs(mark)) mark = x[col]; });
    if (want.length > DL_MAX) return 'full';
    if (r.rows.length < 1000) break;
    last = r.rows[r.rows.length - 1]; if (!last[col]) return 'full';
  }
  const got = [];
  for (let i = 0; i < want.length; i += 150) {
    const r = await dlGet(q + '&class_nbr=in.(' + encodeURIComponent(want.slice(i, i + 150).map(n => '"' + n + '"').join(',')) + ')&select=' + c.sel);
    if (!r.ok) return dlBad(r) ? 'full' : null;
    got.push(...r.rows);
  }
  const n = await count;
  if (!n.ok) return dlBad(n) ? 'full' : null;
  const out = got.length ? dlMerge(rows, got, 'class_nbr') : rows;
  if (out.length !== n.total) return 'full';
  return { rows: out, mark };
}
function hydrateSeatsFromCache() {   /* at start-up, before the network: a localStorage copy (v2 fallback, or the old v1) */
  try {
    const c = JSON.parse(localStorage.getItem(DL_KEY) || 'null'), rows = dlRows(c, CFG.TERM);
    if (rows) { DLM['seats:' + CFG.TERM] = { c: Object.assign({}, c, { pack: null }), rows }; applySeatRows(rows); TC.seatsAt = c.at; return; }
  } catch (e) {}
  try { const c = JSON.parse(localStorage.getItem(SEATS_CACHE) || 'null'); if (c && c.term === CFG.TERM && Array.isArray(c.rows) && c.rows.length) { applySeatRows(c.rows); TC.seatsAt = c.at; } } catch (e) {}
}
let SEAT_RUN = null;
function loadSeats() { return SEAT_RUN || (SEAT_RUN = seatsRun().catch(() => {}).then(() => { SEAT_RUN = null; })); }
async function seatsRun() {
  const term = CFG.TERM; let shown = null;
  const rows = await seatSync(term, 'seats:' + term, SEAT_SELS, (r, c) => { shown = r; applySeatRows(r); TC.seatsAt = c.at; relinkPeople(); loadCatalog(); matchPolyRatings(); render(true); }, DL_KEY);
  if (!rows) { TC.err.seats = true; render(true); return; }
  delete TC.err.seats;
  if (rows !== shown) applySeatRows(rows);
  TC.seatsAt = Date.now();
  relinkPeople(); loadCatalog(); matchPolyRatings(); render(true);
}
/* Descriptions and prerequisites: the scraper's course_catalog (read with the public key). (2026-10-30) Kept on the
   phone: a whole download weekly; in between only classes the copy lacks, or (changed_at) only rows that changed. */
const CAT = { c: null, rows: null, at: 0 };
let CAT_RUN = null, CAT_NEXT = false;
function catApplyRows(part) {
  part.forEach(r => { const c0 = canonCode(r.course_code); if (c0) CAT_INFO[c0] = { desc: cleanDesc(r.description), prereq: cleanPrereq(r.prereqs) }; });
  part.forEach(r => { const c = canonCode(r.course_code); const tt = String(r.title || '').replace(/\s+/g, ' ').trim(); if (c && tt && !codeLike(tt)) CAT_TITLE[c] = tt; });
}
function catToCourses() { Object.keys(CAT_INFO).forEach(c => { if (COURSES[c]) { COURSES[c].desc = CAT_INFO[c].desc; COURSES[c].prereq = CAT_INFO[c].prereq; } }); }
function loadCatalog() {
  catToCourses();   /* a seat reload rebuilds COURSES: put the descriptions back */
  if (CAT_RUN) { CAT_NEXT = true; return CAT_RUN; }
  CAT_RUN = catRun().catch(() => {}).then(() => { CAT_RUN = null; catToCourses(); if (CAT_NEXT) { CAT_NEXT = false; return loadCatalog(); } });
  return CAT_RUN;
}
function catSave() { if (CAT.c && CAT.rows && CAT.rows.length) dlsSet('catalog', Object.assign({}, CAT.c, { pack: dlPack(CAT.rows) }), null); }
async function catRun() {
  if (!CAT.c) {
    const c = await dlsGet('catalog', null), rows = dlRows(c, null);
    if (rows) { CAT.c = Object.assign({}, c, { pack: null }); CAT.rows = rows; catApplyRows(rows); catToCourses(); TC.catalogLoaded = true; render(true); }
  }
  const now = Date.now(), c = CAT.c;
  if (!c || now - c.full >= DL_WEEK || c.full > now + 36e5) return catFull();
  if (c.col === 'changed_at' && dlMs(c.mark) && now - CAT.at >= 120000) {
    const from = new Date(dlMs(c.mark) - DL_LOOK.changed_at).toISOString();
    let got = [];
    for (let off = 0; off < 20000; off += 1000) {
      const r = await dlGet('course_catalog?changed_at=gt.' + encodeURIComponent(from) + '&select=' + c.sel + '&order=changed_at.asc,course_code.asc&limit=1000&offset=' + off);
      if (!r.ok) return dlBad(r) ? catFull() : undefined;
      got = got.concat(r.rows); if (r.rows.length < 1000) break;
    }
    CAT.at = now;
    if (got.length) { catApplyRows(got); CAT.rows = dlMerge(CAT.rows, got, 'course_code'); c.mark = dlMark(got, 'changed_at', c.mark); catSave(); catToCourses(); render(true); }
  }
  return catMissing();
}
async function catFull() {
  let rows = null, sel = '';
  for (let s = 0; s < CAT_SELS.length && !rows; s++) {
    let acc = []; sel = CAT_SELS[s];
    for (let off = 0; off < 20000; off += 1000) {
      const r = await dlGet('course_catalog?select=' + sel + '&order=course_code.asc&limit=1000&offset=' + off);
      if (!r.ok) { if (off === 0 && dlBad(r) && s < CAT_SELS.length - 1) { acc = null; break; } return; }
      acc = acc.concat(r.rows);
      if (r.rows.length < 1000) { rows = acc; break; }
    }
    if (acc && !rows) return;
  }
  if (!rows) return;
  TC.noCatTitle = !/(^|,)title(,|$)/.test(sel);
  Object.keys(CAT_INFO).forEach(k => { delete CAT_INFO[k]; }); Object.keys(CAT_TITLE).forEach(k => { delete CAT_TITLE[k]; });
  catApplyRows(rows); catToCourses();
  const col = dlCol(sel), now = Date.now();
  CAT.c = { v: 2, sel, col, mark: dlMark(rows, col, ''), full: now, miss: Object.keys(COURSES).filter(k => !CAT_INFO[k]) }; CAT.rows = rows; CAT.at = now;
  catSave();
  TC.catalogLoaded = true; render(true);
}
async function catMissing() {   /* classes in this term's list that the copy has never seen (asked once each) */
  const c = CAT.c; if (!c) return;
  const miss = new Set(c.miss || []), want = Object.keys(COURSES).filter(k => !CAT_INFO[k] && !miss.has(k));
  if (!want.length) return;
  if (want.length > 300) return catFull();
  const got = [];
  for (let i = 0; i < want.length; i += 60) {
    const forms = [...new Set(want.slice(i, i + 60).flatMap(k => [k, k.replace(' ', '')]))].map(x => '"' + x + '"').join(',');
    const r = await dlGet('course_catalog?course_code=in.(' + encodeURIComponent(forms) + ')&select=' + c.sel);
    if (!r.ok) return;
    got.push(...r.rows);
  }
  catApplyRows(got);
  want.forEach(k => { if (!CAT_INFO[k]) miss.add(k); });
  c.miss = [...miss]; if (got.length) CAT.rows = dlMerge(CAT.rows, got, 'course_code');
  catSave(); catToCourses(); render(true);
}""")

# coming back to the app: a seat check is a few KB now, so after 2 minutes instead of 10
one("""/* (2026-10-30) the seat feed is the whole term: downloaded again only when what we have is 10 minutes old */
const SEATS_FRESH_MS = 600000;""", """/* (2026-10-30) the seat check asks only what changed (a few KB): again once what we have is 2 minutes old */
const SEATS_FRESH_MS = 120000;""")

p.write_text(s); print(p, 'smaller-downloads applied')
