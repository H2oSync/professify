/* Mutation check for check-app-sync-2026-10-15: each mutant reverts or breaks ONE promise of sync-app-2026-10-15.py in a
   temporary copy of app/index.html; check-app-sync-2026-10-15 must FAIL (in the named section) on every one.
   Run: SRC_DIR=<repo root> node mutate-app-sync-2026-10-15.mjs   (MUT_ONLY="name|name"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const I = 'app/index.html';
const M = [
  /* 1. concentration */
  ['conc: the profile read does not ask for concentration', "class_standing' + (askConc ? ',concentration' : '')", "class_standing'", 'conc'],
  ['conc: a database that does not grant it breaks the profile read', "if (askConc && p.error && (String(p.error.code) === '42501' || schemaGap(p.error))) {", "if (false) {", 'conc'],
  ['conc: a refused column is asked for on every load', "TC.noOwnConc = Date.now(); p = await", "p = await", 'conc'],
  ['conc: the device copy beats the account', "if (db) { concRemember(p.major, db); return db; }", "if (db) { return concRead(p) || db; }", 'conc'],
  ['conc: General / Open is a concentration', "return c && c !== 'General / Open' ? c : ''; }", "return c; }", 'conc'],
  ['conc: the upload never marks itself done', "if (r && !r.error && (r.data || []).length) syncFlagSet(mk, true); }", "}", 'conc'],
  ['conc: the device copy is kept after the account clears it', "if (loc) concRemember(p.major, '');\n  return null;", "return null;", 'conc'],
  ['conc: the account is not the truth after the first time', "syncFlagSet(mk, true);\n  if (loc) concRemember", "if (loc) return loc;\n  syncFlagSet(mk, true);\n  if (loc) concRemember", 'conc'],
  ['conc: not-readable no longer falls back to the device copy', "  if (!srv) return concRead(p);", "  if (!srv) return null;", 'conc'],
  /* 2. story pins */
  ['pins: nothing is uploaded the first time', "const up = syncFlag(syncKey('pins-dirty')) || (!syncFlag(mk) && !srv.length && loc.length);", "const up = syncFlag(syncKey('pins-dirty'));", 'pins'],
  ['pins: this phone’s pins are uploaded every load', "const up = syncFlag(syncKey('pins-dirty')) || (!syncFlag(mk) && !srv.length && loc.length);", "const up = syncFlag(syncKey('pins-dirty')) || (!srv.length && loc.length);", 'pins'],
  ['pins: the migration is never marked', "syncFlagSet(mk, true);\n  if (up) { pinsPush(loc); return; }", "if (up) { pinsPush(loc); return; }", 'pins'],
  ['pins: the account’s pins do not replace the phone’s', "if (seq === PN.seq && JSON.stringify(srv) !== JSON.stringify(loc)) { pinsLocal(srv); render(true); }", "", 'pins'],
  ['pins: a pin is never sent', "r = await TC.client().rpc('set_pinned_friends', { p_ids: ids });", "r = await TC.client().rpc('set_pinned_friends_x', { p_ids: ids });", 'pins'],
  ['pins: the pins are never read', "try { r = await TC.client().rpc('my_pinned_friends'); }", "try { r = await TC.client().rpc('my_pinned_friends_x'); }", 'pins'],
  ['pins: a failed write is forgotten', "else syncFlagSet(syncKey('pins-dirty'), true); return; }\n    PN.on = true;", "return; }\n    PN.on = true;", 'pins'],
  ['pins: a missing function counts as a failure', "if (syncGap(r.error)) PN.on = false; else syncFlagSet(syncKey('pins-dirty'), true); return; }\n    PN.on = true;", "syncFlagSet(syncKey('pins-dirty'), true); return; }\n    PN.on = true;", 'pins'],
  ['pins: what the server kept is ignored', "if (keep && seq === PN.seq && JSON.stringify(keep)", "if (false && keep && seq === PN.seq && JSON.stringify(keep)", 'pins'],
  ['pins: a pin that never reached the server is read over', "const up = syncFlag(syncKey('pins-dirty')) || (", "const up = (", 'pins'],
  ['pins: the dirty flag is never cleared', "PN.on = true; syncFlagSet(syncKey('pins-dirty'), false);", "PN.on = true;", 'pins'],
  ['pins: unpinning is not sent', "if (a.indexOf(id) >= 0) { if (!pinsSet(all.filter(x => x !== id)))", "if (a.indexOf(id) >= 0) { if (!pinsLocal(all.filter(x => x !== id)))", 'pins'],
  /* 3. commitments */
  ['cm: the cache is re-uploaded whenever the server list is empty', "if (!rows.length && TC.commits.length && !syncFlag(mk)) {", "if (!rows.length && TC.commits.length) {", 'cm'],
  ['cm: the upload never marks itself done', "if (!TC.err.commits) syncFlagSet(mk, true); return; }", "return; }", 'cm'],
  ['cm: a server list never ends the migration', "syncFlagSet(mk, true);\n  TC.commits = rows.sort", "TC.commits = rows.sort", 'cm'],
  /* 4. bookmarks */
  ['saved: this phone’s bookmarks are never uploaded', "const add = [...want].filter(([id]) => !have.has(id)).map(([, w]) => w), del", "const add = [], del", 'saved'],
  ['saved: a professor goes up under the bare key', "return { kind: 'prof', key: SV.srv[k] || reviewKeyOf(m[2]) || (m[2] + '|') };", "return { kind: 'prof', key: m[2] };", 'saved'],
  ['saved: a class goes up under the phone’s own key', "return { kind: 'class', key: canonCode(m[2]) || m[2] };", "return { kind: 'class', key: m[0] };", 'saved'],
  ['saved: removing a professor guesses the key', "key: SV.srv[k] || reviewKeyOf(m[2])", "key: reviewKeyOf(m[2])", 'saved'],
  ['saved: a toggle is never sent', "toast(on ? 'Removed from saved' : 'Saved on this phone'); save(); render(true); svPush(k, !on); },", "toast(on ? 'Removed from saved' : 'Saved on this phone'); save(); render(true); },", 'saved'],
  ['saved: the account’s list does not replace the phone’s', "if (SV.seq === seq0 && JSON.stringify(srv) !== JSON.stringify(S.saved)) { S.saved = srv; save(); render(true); } return; }", "return; }", 'saved'],
  ['saved: a change that never reached the server is read over', "migrated = syncFlag(mk), dirty = syncFlag(dk);", "migrated = syncFlag(mk), dirty = false;", 'saved'],
  ['saved: the migration is never marked', "syncFlagSet(mk, true); syncFlagSet(dk, false);\n  if (!dirty)", "syncFlagSet(dk, false);\n  if (!dirty)", 'saved'],
  ['saved: a missing table counts as a failure', "if (syncGap(r.error)) SV.on = false; else syncFlagSet(syncKey('saved-dirty'), true); }\n  }).catch", "syncFlagSet(syncKey('saved-dirty'), true); }\n  }).catch", 'saved'],
  ['saved: the account’s bookmarks replace the phone’s instead of joining them', "const un = srv.concat(loc.filter(k => srv.indexOf(k) < 0));", "const un = loc;", 'saved'],
  ['saved: a failed save is forgotten', "if (syncGap(r.error)) SV.on = false; else syncFlagSet(syncKey('saved-dirty'), true); }\n  }).catch", "if (syncGap(r.error)) SV.on = false; }\n  }).catch", 'saved'],
  /* 5. chat pins */
  ['chat: nothing is uploaded the first time', "const up = dirty || (!syncFlag(mk) && !srv.length && loc.length);", "const up = dirty;", 'chat'],
  ['chat: the phone’s pins are uploaded every load', "const up = dirty || (!syncFlag(mk) && !srv.length && loc.length);", "const up = dirty || (!srv.length && loc.length);", 'chat'],
  ['chat: pin order is lost', ".sort((a, b) => new Date(a.pinned_at) - new Date(b.pinned_at))", "", 'chat'],
  ['chat: unpinning is not sent', "prev.filter(x => now.indexOf(x) < 0), false);", "[], false);", 'chat'],
  ['chat: pinning is not sent', "chatPinPush(now.filter(x => prev.indexOf(x) < 0), prev.filter", "chatPinPush([], prev.filter", 'chat'],
  ['chat: a missing column on write counts as a failure', "if (syncGap(r.error) || String(r.error.code) === '42501') { CP.on = false; return; } bad = true; }", "bad = true; }", 'chat'],
  ['chat: a failed write is forgotten', "if (bad) syncFlagSet(syncKey('chatpins-dirty'), true);", "", 'chat'],
  ['chat: a pin that never reached the account is read over', "const loc = chatPins().filter(x => have.has(x)).slice(0, CHAT_PIN_MAX), dirty = syncFlag(dk);", "const loc = chatPins().filter(x => have.has(x)).slice(0, CHAT_PIN_MAX), dirty = false;", 'chat'],
  ['chat: the account’s pins do not replace the phone’s', "if (JSON.stringify(srv) !== JSON.stringify(chatPins())) chatPinLocal(srv);", "", 'chat'],
  ['chat: the migration is never marked', "syncFlagSet(mk, true);\n  if (up) { syncFlagSet(dk, false);", "if (up) { syncFlagSet(dk, false);", 'chat'],
  /* 6. plans */
  ['plan: a class number the seat feed lacks is dropped', "return s ? { code: s.code, class_nbr: id } : (PLAN_RAW[id] ? Object.assign({}, PLAN_RAW[id]) : null); }).filter(Boolean); }", "return s ? { code: s.code, class_nbr: id } : null; }).filter(Boolean); }", 'plan'],
  ['plan: the share switch drops it', "  const list = planList(slot);\n  const r = await TC.client().from('plans').upsert({ user_id: TC.user.id, term: CFG.TERM, slot, sections: list, shared: !!on }", "  const list = TC.plans[slot].map(id => { const s = SEC[id]; return s ? { code: s.code, class_nbr: id } : null; }).filter(Boolean);\n  const r = await TC.client().from('plans').upsert({ user_id: TC.user.id, term: CFG.TERM, slot, sections: list, shared: !!on }", 'plan'],
  ['plan: the account’s rows are not remembered', "if (x && x.class_nbr != null) PLAN_RAW[String(x.class_nbr)] = x; });", "});", 'plan'],
  /* 7. push */
  ['push: the seat switch does not write seats', "if (k === 'seat_open') row.seats = pushPrefOn('seat_open');", "", 'push'],
  ['push: every switch writes seats', "if (k === 'seat_open') row.seats = pushPrefOn('seat_open');", "row.seats = pushPrefOn('seat_open');", 'push'],
  ['push: the website’s seats switch is not read', "if (r.data && r.data.seats === false) PUSH.prefs.seat_open = false;", "", 'push'],
  ['push: seats is not asked for', "select('prefs,seats')", "select('prefs')", 'push'],
  ['push: the phone’s off is turned back on by seats', "if (r.data && r.data.seats === false) PUSH.prefs.seat_open = false;", "if (r.data && r.data.seats !== false) delete PUSH.prefs.seat_open; if (r.data && r.data.seats === false) PUSH.prefs.seat_open = false;", 'push'],
];
const orig = fs.readFileSync(path.join(SRC, I), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutt-appsync-');
for (const e of fs.readdirSync(SRC)) if (e !== 'app' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
fs.mkdirSync(path.join(tmp, 'app'));
for (const e of fs.readdirSync(path.join(SRC, 'app'))) if (e !== 'index.html') fs.symlinkSync(path.join(SRC, 'app', e), path.join(tmp, 'app', e));
let caught = 0, ran = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test, special] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  ran++;
  let src;
  const pairs = Array.isArray(a) ? a : [[a, b]]; src = orig; let bad = false;
  for (const [x, y] of pairs) { const n = src.split(x).length - 1; if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name, x.slice(0, 60)); bad = true; break; } src = src.split(x).join(y); }
  if (bad) { survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, I), src);
  let failed = false, out = '';
  try { execFileSync('node', [path.join(HERE, 'check-app-sync-2026-10-15.mjs'), '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-app-sync-2026-10-15: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ran} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
