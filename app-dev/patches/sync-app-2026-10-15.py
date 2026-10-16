#!/usr/bin/env python3
"""Phone bundle (app/index.html), 2026-10-15: a student's data is the same on the phone app and on the website.
Phone side of the audit gaps in /tmp/claude-0/sec/sync-audit.md. Only app/index.html (and the planner.js build stamp) change.
Server pieces (sql/professify-sync-2026-10-15.sql) may not be live yet: every new call degrades to today's behaviour when it
answers PGRST202 / 42883 / 42P01 / PGRST205 / PGRST204 / 42703 / "does not exist" (syncGap()).

Rule used everywhere below ("server wins, unless this phone has something the server never got"):
  - a server list is read on every load and becomes the local cache;
  - ONE-TIME migration per account (flag tc-<name>-migrated:<uid>): the first time the server answers, whatever this phone
    kept locally goes up if the server has none of it;
  - a write that failed for a reason other than "not installed" sets tc-<name>-dirty:<uid>: the next load pushes this phone's
    state up (this phone wins) and clears it, instead of letting the older server copy overwrite it.
  All of these keys start tc- so the sign-out / delete wipe (TC.wipeDevice) removes them with everything else.

1. Gap 1  concentration: profiles.concentration is read with the profile (it IS granted; retried without it on 42501/42703 and not asked again for 10 minutes
   (TC.noOwnConc), so a database that does not grant it still loads, at the cost of one extra read, once). The database value wins over concRead(); 'General / Open' and empty mean none.
   If the database has none but this phone has one that was never uploaded, it is written once (flag tc-conc-migrated:<uid>,
   set only when that write succeeds); afterwards the database is the truth, so clearing it on the website clears it here.
   Writes were already on every path (saveProfile, updateProfileFields, pickConc, createProfile): unchanged. The 5th-year value
   and the shared major rename map (majorNow) are kept as they were.
2. Gap 2  story pins: my_pinned_friends() / set_pinned_friends(uuid[]) instead of tc-story-pins:<uid> (kept as the cache). Max 3,
   toasts unchanged. Upload once if the server list is empty (tc-pins-migrated:<uid>).
3. Gap 3  commitments: the cache is re-uploaded only once per account (tc-commits-migrated:<uid>), so deleting them all on the
   website does not bring them back.
4. Gap 7  Explore bookmarks (S.saved, 'c:BUS 3431' / 'p:<profKey>') <-> saved_items (kind class|prof, key 'BUS 3431' / reviewKeyOf).
   One-time upload of the local bookmarks (tc-saved-migrated:<uid>); S.saved stays the cache.
5. Gap 8  chat pins: conversation_members.pinned_at replaces tc-chat-pins-<uid> as the truth (kept as the cache), one-time upload
   (tc-chatpins-migrated:<uid>). Waivers, suggestion dismissals, helpful votes and Instagram: the phone has no UI for them; none added.
6. Gap 10 pushPlan keeps the plan's class numbers that are not in the loaded seat feed (their original {code,class_nbr} objects).
7. Gap 6  push settings: the seat-alert switch also writes push_prefs.seats; both are read on load (off in either = off).

Usage: python3 sync-app-2026-10-15.py <repo>
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app/index.html'
s = f.read_text()
if 'sync-app (2026-10-15)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ shared helpers
one("""function schemaGap(err) { if (!err) return false; const c = String(err.code || ''), m = String(err.message || ''); return c === '42703' || c === '42P01' || c === 'PGRST204' || c === 'PGRST205' || /does not exist|schema cache/i.test(m); }
""", """function schemaGap(err) { if (!err) return false; const c = String(err.code || ''), m = String(err.message || ''); return c === '42703' || c === '42P01' || c === 'PGRST204' || c === 'PGRST205' || /does not exist|schema cache/i.test(m); }
/* sync-app (2026-10-15): the server pieces of sql/professify-sync-2026-10-15.sql may not be installed yet. syncGap() is "not installed"
   (a missing function, table or column): the feature then behaves as it did before. Per-account flags live under tc- so the wipe removes them. */
const syncGap = e => !!e && (schemaGap(e) || /^(PGRST202|42883)$/.test(String(e.code || '')) || /could not find the function|does not exist|schema cache/i.test(String(e.message || '')));
const syncKey = n => 'tc-' + n + ':' + ((TC.user && TC.user.id) || '');
const syncFlag = k => { try { return localStorage.getItem(k) === '1'; } catch (e) { return false; } };
const syncFlagSet = (k, on) => { try { if (on) localStorage.setItem(k, '1'); else localStorage.removeItem(k); } catch (e) {} };
""")

# ================================================================ 1. concentration
one("""  /* Only the columns `authenticated` is granted (professify-lockdown.sql). `concentration` is NOT
     one of them: naming it made PostgREST refuse the whole read with 42501 — for your own row — and
     the app then told a fully set-up student their account "hasn't been set up yet". The desktop
     never reads it back either; it keeps the concentration on the device ('professify-profile'),
     and so does this app (concRead below). */
  const p = await sb.from('profiles').select('id,display_name,username,avatar_url,major,class_standing').eq('id', me).maybeSingle();
""", """  /* Only the columns `authenticated` is granted (professify-lockdown.sql). `concentration` IS one of them now (sync-app (2026-10-15)),
     and the website reads it too, so the account's value follows the student from device to device. A database that does NOT grant it
     refuses the whole read with 42501 — for your own row — which once told a fully set-up student their account "hasn't been set
     up yet": so that answer (or a missing column) is retried without the column, and the concentration stays on the device
     ('professify-profile' / termchamp_app_conc, concRead) as it did before. */
  const askConc = !(TC.noOwnConc && Date.now() - TC.noOwnConc < 600000);   /* refused once => not asked again for 10 minutes (as the friends read does), so a refusal costs one extra round trip, once */
  let p = await sb.from('profiles').select('id,display_name,username,avatar_url,major,class_standing' + (askConc ? ',concentration' : '')).eq('id', me).maybeSingle();
  let concSrv = askConc && !p.error;
  if (askConc && p.error && (String(p.error.code) === '42501' || schemaGap(p.error))) { TC.noOwnConc = Date.now(); p = await sb.from('profiles').select('id,display_name,username,avatar_url,major,class_standing').eq('id', me).maybeSingle(); }
""")
one("""  TC.profile.concentration = concRead(TC.profile);
""", """  TC.profile.concentration = concResolve(TC.profile, concSrv);
""")
one("""async function loadAll() {
  const sb = TC.client(); if (!sb || !TC.user) return;
  TC.loadedAt = Date.now();""", """/* sync-app (2026-10-15): the concentration the account says. 'General / Open' (the website's word for none) and empty are none. Read from the
   database => it wins over this device's copy. A device copy the database never got is uploaded ONCE (flag set when that write lands);
   after that the database is the truth, so clearing it on the website clears it here. Column not readable => today's behaviour. */
function concClean(c) { c = String(c == null ? '' : c).trim(); return c && c !== 'General / Open' ? c : ''; }
function concResolve(p, srv) {
  if (!srv) return concRead(p);
  const db = concClean(p.concentration), mk = syncKey('conc-migrated');
  if (db) { concRemember(p.major, db); return db; }
  const loc = concRead(p);
  if (loc && !syncFlag(mk)) {
    try { TC.client().from('profiles').update({ concentration: loc }).eq('id', TC.user.id).select('id').then(r => { if (r && !r.error && (r.data || []).length) syncFlagSet(mk, true); }, () => {}); } catch (e) {}
    return loc;
  }
  syncFlagSet(mk, true);
  if (loc) concRemember(p.major, '');
  return null;
}
async function loadAll() {
  const sb = TC.client(); if (!sb || !TC.user) return;
  TC.loadedAt = Date.now();""")

# loads that run with the rest of the student's data
one("""  await Promise.all([loadMine(), loadFriends(), loadPlans(),""",
    """  TC._cpSynced = false;
  await Promise.all([loadMine(), loadFriends().then(v => { loadPins().catch(() => {}); return v; }), loadSaved().catch(() => {}), loadPlans(),""")

# ================================================================ 2. story pins
one("""/* ---- pinned stories (Tate, 2026-10-04: "pin 3 friends on stories") ----
   Up to three, first in the row in the order pinned. Kept on this phone per account; never sent. */
const PIN_MAX = 3;
function pinKey() { return 'tc-story-pins:' + (TC.user ? TC.user.id : ''); }""", """/* ---- pinned stories (Tate, 2026-10-04: "pin 3 friends on stories") ----
   Up to three, first in the row in the order pinned. sync-app (2026-10-15): the account keeps them (profiles.pinned_friends, read with
   my_pinned_friends(), written with set_pinned_friends(); the server keeps only friends, max 3) so the website shows the same row. This
   phone's list (tc-story-pins:<uid>) is the cache. Not installed yet => it stays on this phone, as before. */
const PIN_MAX = 3;
const PN = { on: null, q: Promise.resolve(), seq: 0 };
function pinKey() { return 'tc-story-pins:' + (TC.user ? TC.user.id : ''); }""")
one("""function pinsSet(a) { try { localStorage.setItem(pinKey(), JSON.stringify(a)); return true; } catch (e) { return false; } }
""", """function pinsLocal(a) { try { localStorage.setItem(pinKey(), JSON.stringify(a)); return true; } catch (e) { return false; } }
function pinsSet(a) { if (!pinsLocal(a)) return false; pinsPush(a); return true; }
/* up to the account, in order. The server answers with what it kept; that becomes the cache unless the student has pinned again since. */
function pinsPush(a) {
  if (PN.on === false || !TC.user) return;
  const ids = a.filter(x => TC.friends.indexOf(x) >= 0).slice(0, PIN_MAX), seq = ++PN.seq;
  PN.q = PN.q.then(async () => {
    if (PN.on === false) return;
    let r; try { r = await TC.client().rpc('set_pinned_friends', { p_ids: ids }); } catch (e) { r = { error: e }; }
    if (r.error) { if (syncGap(r.error)) PN.on = false; else syncFlagSet(syncKey('pins-dirty'), true); return; }
    PN.on = true; syncFlagSet(syncKey('pins-dirty'), false);
    const keep = Array.isArray(r.data) ? r.data.map(String) : null;
    if (keep && seq === PN.seq && JSON.stringify(keep) !== JSON.stringify(pinsGet())) { pinsLocal(keep); render(true); }
  }).catch(() => {});
}
/* On every load: the account's pins become the cache. First time on this account with none on the server: this phone's go up (once).
   A change that never reached the server (tc-pins-dirty) goes up instead of being overwritten. */
async function loadPins() {
  if (!TC.user || !TC.friends.length) return;
  let r; try { r = await TC.client().rpc('my_pinned_friends'); } catch (e) { r = { error: e }; }
  if (r.error) { if (syncGap(r.error)) PN.on = false; return; }
  PN.on = true;
  const mk = syncKey('pins-migrated'), seq = PN.seq;
  const srv = (Array.isArray(r.data) ? r.data : []).map(String).filter(x => TC.friends.indexOf(x) >= 0).slice(0, PIN_MAX), loc = pinsGet();
  const up = syncFlag(syncKey('pins-dirty')) || (!syncFlag(mk) && !srv.length && loc.length);
  syncFlagSet(mk, true);
  if (up) { pinsPush(loc); return; }
  if (seq === PN.seq && JSON.stringify(srv) !== JSON.stringify(loc)) { pinsLocal(srv); render(true); }
}
""")

# ================================================================ 3. commitments
one("""  /* kept on this phone before RUN 18: the first time the table answers with nothing, they go up */
  if (!rows.length && TC.commits.length) { for (const x of TC.commits) await cmPush(x); return; }
  TC.commits = rows.sort((a, b) => a.s - b.s); cmKeep();""", """  /* kept on this phone before RUN 18: the first time the table answers with nothing, they go up. sync-app (2026-10-15): ONCE per account
     (tc-commits-migrated:<uid>) — an empty list later means the student deleted them (on the website), not that the server lost them. */
  const mk = syncKey('commits-migrated');
  if (!rows.length && TC.commits.length && !syncFlag(mk)) { for (const x of TC.commits) await cmPush(x); if (!TC.err.commits) syncFlagSet(mk, true); return; }
  syncFlagSet(mk, true);
  TC.commits = rows.sort((a, b) => a.s - b.s); cmKeep();""")

# ================================================================ 4. Explore bookmarks
one("""const isSaved = k => S.saved.includes(k);
""", """const isSaved = k => S.saved.includes(k);
/* ---- sync-app (2026-10-15): Explore bookmarks <-> saved_items(kind 'class'|'prof', key). S.saved ('c:BUS 3431', 'p:<profKey>') is the cache.
   class key 'BUS 3431'; professor key = the review key 'name|dept' lowercased (reviewKeyOf) — for a row that came FROM the account we keep the key it
   had (SV.srv), so removing it deletes that row. One-time upload of what this phone had (tc-saved-migrated:<uid>); a toggle that failed for a reason
   other than "not installed" sets tc-saved-dirty:<uid> and the next load pushes this phone's list instead of reading over it. ---- */
const SV = { on: null, srv: {}, q: Promise.resolve(), seq: 0 };
function svRow(k) {
  const m = /^([cp]):(.+)$/.exec(String(k)); if (!m) return null;
  if (m[1] === 'c') return { kind: 'class', key: canonCode(m[2]) || m[2] };
  return { kind: 'prof', key: SV.srv[k] || reviewKeyOf(m[2]) || (m[2] + '|') };
}
function svLocal(r) {
  if (!r || !r.key) return null;
  if (r.kind === 'class') return 'c:' + (canonCode(r.key) || r.key);
  if (r.kind === 'prof') { const pk = profKeyOf(String(r.key).split('|')[0]); if (!pk) return null; SV.srv['p:' + pk] = String(r.key); return 'p:' + pk; }
  return null;
}
function svPush(k, add) {
  const row = svRow(k); if (!row || SV.on === false || !TC.user) return;
  SV.seq++;
  SV.q = SV.q.then(async () => {
    if (SV.on === false) return;
    const sb = TC.client(); let r;
    try { r = add ? await sb.from('saved_items').insert(row) : await sb.from('saved_items').delete().eq('user_id', TC.user.id).eq('kind', row.kind).eq('key', row.key); } catch (e) { r = { error: e }; }
    if (r.error && add && String(r.error.code) === '23505') return;
    if (r.error) { if (syncGap(r.error)) SV.on = false; else syncFlagSet(syncKey('saved-dirty'), true); }
  }).catch(() => {});
}
function svWaitProfs() { return new Promise(res => { let n = 0; const t = () => (TC.profsLoaded || ++n > 40) ? res() : setTimeout(t, 250); t(); }); }
async function loadSaved() {
  if (!TC.user) return;
  const seq0 = SV.seq, me = TC.user.id, sb = TC.client();
  let r; try { r = await sb.from('saved_items').select('kind,key,created_at').eq('user_id', me).order('created_at', { ascending: true }); } catch (e) { r = { error: e }; }
  if (r.error) { if (syncGap(r.error)) SV.on = false; return; }
  SV.on = true;
  const rows = Array.isArray(r.data) ? r.data : [], srv = [];
  rows.forEach(x => { const k = svLocal(x); if (k && srv.indexOf(k) < 0) srv.push(k); });
  const mk = syncKey('saved-migrated'), dk = syncKey('saved-dirty'), migrated = syncFlag(mk), dirty = syncFlag(dk);
  if (migrated && !dirty) { if (SV.seq === seq0 && JSON.stringify(srv) !== JSON.stringify(S.saved)) { S.saved = srv; save(); render(true); } return; }
  /* first time on this account, or a change that never got there: what this phone has goes up */
  if (S.saved.some(k => /^p:/.test(k) && !SV.srv[k])) await svWaitProfs();
  const loc = S.saved.slice(), have = new Set(rows.map(x => x.kind + '|' + x.key)), want = new Map();
  loc.forEach(k => { const w = svRow(k); if (w) want.set(w.kind + '|' + w.key, w); });
  const add = [...want].filter(([id]) => !have.has(id)).map(([, w]) => w), del = dirty ? rows.filter(x => !want.has(x.kind + '|' + x.key)) : [];
  let bad = false;
  if (add.length) { let q; try { q = await sb.from('saved_items').insert(add); } catch (e) { q = { error: e }; } if (q.error) { bad = true; if (syncGap(q.error)) SV.on = false; } }
  for (const x of del) { let q; try { q = await sb.from('saved_items').delete().eq('user_id', me).eq('kind', x.kind).eq('key', x.key); } catch (e) { q = { error: e }; } if (q.error) bad = true; }
  if (bad) return;
  syncFlagSet(mk, true); syncFlagSet(dk, false);
  if (!dirty) { const un = srv.concat(loc.filter(k => srv.indexOf(k) < 0)); if (SV.seq === seq0 && JSON.stringify(un) !== JSON.stringify(S.saved)) { S.saved = un; save(); render(true); } }
}
""")
one("""  save: k => { const on = isSaved(k); S.saved = on ? S.saved.filter(x => x !== k) : [...S.saved, k]; toast(on ? 'Removed from saved' : 'Saved on this phone'); save(); render(true); },""",
    """  save: k => { const on = isSaved(k); S.saved = on ? S.saved.filter(x => x !== k) : [...S.saved, k]; toast(on ? 'Removed from saved' : 'Saved on this phone'); save(); render(true); svPush(k, !on); },""")

# ================================================================ 5. chat pins
one("""/* Pinned chats (Tate, 2026-10-04): kept on this phone, per account, in the order pinned, up to 3. */""",
    """/* Pinned chats (Tate, 2026-10-04): in the order pinned, up to 3. sync-app (2026-10-15): the account keeps them (conversation_members.pinned_at, own row);
   this phone's list (tc-chat-pins-<uid>) is the cache. Not installed yet => it stays on this phone, as before. */""")
one("""function chatPinSet(list) { try { localStorage.setItem(chatPinKey(), JSON.stringify(list)); return true; } catch (e) { return false; } }
""", """function chatPinLocal(list) { try { localStorage.setItem(chatPinKey(), JSON.stringify(list)); return true; } catch (e) { return false; } }
const CP = { on: null, q: Promise.resolve() };
function chatPinSet(list) {
  const prev = chatPins(), now = list.map(String); if (!chatPinLocal(list)) return false;
  chatPinPush(now.filter(x => prev.indexOf(x) < 0), prev.filter(x => now.indexOf(x) < 0), false);
  return true;
}
/* pinned_at is the order: a new pin is stamped now; a one-time upload is stamped in the past, oldest first, so the order survives. A failure that isn't
   "not installed" sets tc-chatpins-dirty:<uid>; the next load pushes this phone's list. */
function chatPinPush(add, del, past) {
  if (CP.on === false || !TC.user || !(add.length || del.length)) return;
  const me = TC.user.id, base = Date.now();
  CP.q = CP.q.then(async () => {
    if (CP.on === false) return;
    const sb = TC.client(), ops = add.map((id, i) => [id, new Date(past ? base - (add.length - i) * 1000 : base + i).toISOString()]).concat(del.map(id => [id, null]));
    let bad = false;
    for (const [id, at] of ops) {
      let r; try { r = await sb.from('conversation_members').update({ pinned_at: at }).eq('conversation_id', id).eq('user_id', me); } catch (e) { r = { error: e }; }
      if (r.error) { if (syncGap(r.error) || String(r.error.code) === '42501') { CP.on = false; return; } bad = true; }
    }
    if (bad) syncFlagSet(syncKey('chatpins-dirty'), true);
  }).catch(() => {});
}
function chatPinsSync(res, ids) {
  if (!res) return;
  TC._cpSynced = true;
  if (res.error) { if (syncGap(res.error) || String(res.error.code) === '42501') CP.on = false; return; }
  CP.on = true;
  const have = new Set(ids.map(String)), mk = syncKey('chatpins-migrated'), dk = syncKey('chatpins-dirty');
  const srv = (res.data || []).filter(r => r && r.pinned_at && have.has(String(r.conversation_id))).sort((a, b) => new Date(a.pinned_at) - new Date(b.pinned_at)).map(r => String(r.conversation_id)).slice(0, CHAT_PIN_MAX);
  const loc = chatPins().filter(x => have.has(x)).slice(0, CHAT_PIN_MAX), dirty = syncFlag(dk);
  const up = dirty || (!syncFlag(mk) && !srv.length && loc.length);
  syncFlagSet(mk, true);
  if (up) { syncFlagSet(dk, false); chatPinPush(loc.filter(x => srv.indexOf(x) < 0), srv.filter(x => loc.indexOf(x) < 0), true); return; }
  if (JSON.stringify(srv) !== JSON.stringify(chatPins())) chatPinLocal(srv);
}
""")
one("""  const [convs, memb, last, clr, hid, mut] = await Promise.all([""", """  const [convs, memb, last, clr, hid, mut, cpin] = await Promise.all([""")
one("""    sb.from('conversation_mutes').select('conversation_id')
  ]);
  chatXRead(clr, hid);""", """    sb.from('conversation_mutes').select('conversation_id'),
    TC._cpSynced ? null : sb.from('conversation_members').select('conversation_id,pinned_at').eq('user_id', me)   /* sync-app (2026-10-15): chat pins, once per load */
  ]);
  chatPinsSync(cpin, ids);
  chatXRead(clr, hid);""")

# ================================================================ 6. pushPlan keeps unknown class numbers (Gap 10)
one("""    TC.plans[row.slot] = (Array.isArray(row.sections) ? row.sections : []).map(x => String(x.class_nbr)).filter(Boolean);
    TC.planShared[row.slot] = row.shared !== false;""", """    TC.plans[row.slot] = (Array.isArray(row.sections) ? row.sections : []).map(x => String(x.class_nbr)).filter(Boolean);
    /* sync-app (2026-10-15): the rows as the account has them, so a class number this phone's seat feed doesn't hold goes back up as it was */
    (Array.isArray(row.sections) ? row.sections : []).forEach(x => { if (x && x.class_nbr != null) PLAN_RAW[String(x.class_nbr)] = x; });
    TC.planShared[row.slot] = row.shared !== false;""")
one("""const PLAN_LOCAL = 'termchamp_app_plans_v1';
""", """const PLAN_LOCAL = 'termchamp_app_plans_v1';
const PLAN_RAW = {};   /* class_nbr -> the {code, class_nbr} object the plans table holds (sync-app (2026-10-15)) */
""")
one("""async function pushPlan(slot) {
  const sb = TC.client(); if (!sb || !TC.user) return;
  const list = TC.plans[slot].map(id => { const s = SEC[id]; return s ? { code: s.code, class_nbr: id } : null; }).filter(Boolean);""",
    """/* sync-app (2026-10-15): the rows a plan goes up as. A class number missing from the loaded seat feed keeps its original object (the website's plan, or a section
   the feed no longer lists); dropping it here silently shortened a plan the student never touched. Used by pushPlan and setPlanShared. */
function planList(slot) { return TC.plans[slot].map(id => { const s = SEC[id]; return s ? { code: s.code, class_nbr: id } : (PLAN_RAW[id] ? Object.assign({}, PLAN_RAW[id]) : null); }).filter(Boolean); }
async function pushPlan(slot) {
  const sb = TC.client(); if (!sb || !TC.user) return;
  const list = planList(slot);""")
one("""  TC.planShared[slot] = !!on;
  const list = TC.plans[slot].map(id => { const s = SEC[id]; return s ? { code: s.code, class_nbr: id } : null; }).filter(Boolean);""",
    """  TC.planShared[slot] = !!on;
  const list = planList(slot);""")

# ================================================================ 7. push settings: seat alerts <-> push_prefs.seats
one("""  let r; try { r = await TC.client().from('push_prefs').select('prefs').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: e }; }
  if (r.error) { PUSH.prefsErr = true; if (!PUSH.prefs) PUSH.prefs = {}; return; }
  PUSH.prefsErr = false;
  PUSH.prefs = r.data && r.data.prefs && typeof r.data.prefs === 'object' ? r.data.prefs : {};""", """  let r; try { r = await TC.client().from('push_prefs').select('prefs,seats').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: e }; }
  if (r.error) { PUSH.prefsErr = true; if (!PUSH.prefs) PUSH.prefs = {}; return; }
  PUSH.prefsErr = false;
  PUSH.prefs = r.data && r.data.prefs && typeof r.data.prefs === 'object' ? Object.assign({}, r.data.prefs) : {};
  /* sync-app (2026-10-15): the website's "seat alerts" switch is push_prefs.seats; off in either place is off in both */
  if (r.data && r.data.seats === false) PUSH.prefs.seat_open = false;""")
one("""    let r; try { r = await TC.client().from('push_prefs').upsert({ user_id: TC.user.id, prefs: next, updated_at: new Date().toISOString() }); } catch (e) { r = { error: e }; }""",
    """    const row = { user_id: TC.user.id, prefs: next, updated_at: new Date().toISOString() };
    if (k === 'seat_open') row.seats = pushPrefOn('seat_open');   /* sync-app (2026-10-15): the website's column for the same switch */
    let r; try { r = await TC.client().from('push_prefs').upsert(row); } catch (e) { r = { error: e }; }""")

# ================================================================ build stamp
STAMP = '2026-10-15 12:00'
one("window.TERMCHAMP_APP_BUILD = '2026-10-13 07:45';", "window.TERMCHAMP_APP_BUILD = '" + STAMP + "';")

f.write_text(s)
pj = root / 'app/planner.js'
t = pj.read_text()
t2, n = re.subn(r'window\.TERMCHAMP_PLANNER_BUILD = "[^"]+"', 'window.TERMCHAMP_PLANNER_BUILD = "' + STAMP + '"', t)
assert n == 1
pj.write_text(t2)
print('patched', f, 'stamp', STAMP)
