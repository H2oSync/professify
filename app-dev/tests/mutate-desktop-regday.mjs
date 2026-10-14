/* Mutation check for check-desktop-regday: each mutant breaks one promise of the website's registration day
   (website-registration-day, 2026-10-14); check-desktop-regday must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-regday.mjs  (MUT_ONLY="a|b"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  // ---- what is written, and where
  ["regday: the term is not the registration term", "  REGISTRATION_TERM_CODE: '2274',", "  REGISTRATION_TERM_CODE: '2268',", 'cards'],
  ["regday: the write names another term", "user_id: u.id, term: term, day: v.day", "user_id: u.id, term: '2268', day: v.day", 'save'],
  ["regday: the upsert has no conflict target", ", { onConflict: 'user_id,term' })\n        : await c.from", ")\n        : await c.from", 'save'],
  ["regday: no time is written as an empty string", "at_time: v.time || null", "at_time: v.time", 'save'],
  ["regday: friends can always see it", "shared: !!v.shared, updated_at: new Date()", "shared: true, updated_at: new Date()", 'save'],
  ["regday: Clear does not delete", ": await c.from('registration_days').delete().eq('user_id', u.id).eq('term', term);", ": await c.from('registration_days').select('day').eq('user_id', u.id).eq('term', term);", 'save'],
  // ---- a refused write
  ["regday: a refused write drops what you chose", "if (writeGap(q.error)) { RG.gap = true; return null; }\n      /* taking it away", "if (writeGap(q.error)) { RG.gap = true; return null; }\n      RG.day = null; keep(null, false);\n      /* taking it away", 'refused'],
  ["regday: nothing retries when it is back online", "  window.addEventListener('online', function () { retry(); });", "", 'refused'],
  ["regday: nothing retries on a timer", "RG.retryT = setTimeout(function () { RG.retryT = null; retry(); }, RETRY_EVERY);", "RG.retryT = 0;", 'refused'],
  ["regday: the account's old row beats the change waiting here", "if (loc && loc.pending && (!row || !row.updated_at || Date.parse(row.updated_at) < (+loc.at || 0))) {", "if (false) {", 'refused'],
  ["regday: a refused Clear does not say friends can still see it", "return (!v || !v.shared) ? 'Not done yet", "return false ? 'Not done yet", 'refused'],
  ["regday: a missing table is not remembered (and is hammered)", "if (writeGap(q.error)) { RG.gap = true; return null; }\n      /* taking it away", "if (writeGap(q.error)) { return null; }\n      /* taking it away", 'schemaGap'],
  // ---- the card's rules
  ["regday: Round 1 never ends", "    return today() <= endDay();", "    return true;", 'window'],
  ["regday: signed-out students get the card", "if (!user() || !client() || !code() || !cfgv('REGISTRATION_OPENS')) return false;", "if (!client() || !code() || !cfgv('REGISTRATION_OPENS')) return false;", 'window'],
  ["regday: Home's rail is there all term", "function railOn() { return active() && today() >= isoAdd(cfgv('REGISTRATION_OPENS'), -14); }", "function railOn() { return active(); }", 'window'],
  ["regday: another term shows the card too", "    try { if (String(mcTerm()) !== code()) return false; } catch (_) { return false; }\n", "", 'window'],
  ["regday: your day is still there the day after", "    if (mine) return null;", "    if (mine) return { set: true, head: 'Register', sub: '' };", 'cards'],
  ["regday: the banner has no link", "?'<button class=\"btn\" style=\"flex:none\" onclick=\"regDayOpen(&quot;banner&quot;)\">'+regDayLabel()+'</button>':''", "?'':''", 'banner'],
  // ---- friends' days
  ["regday: the RPC is asked for another term", "rpc('friend_registration_days', { p_term: code() })", "rpc('friend_registration_days', { p_term: '2268' })", 'friends'],
  ["regday: friends sort by time, not day", "return a.day.localeCompare(b.day) || (a.time || '99')", "return (a.time || '99').localeCompare(b.time || '99') || (a.time || '99')", 'friends'],
  ["regday: people who are not friends are drawn", "return friendOf(x.id) && !blocked(x.id); }).sort(", "return !!x; }).sort(", 'friends'],
  ["regday: days already gone are listed", "var td = today(), up = frRows().filter(function (x) { return x.day >= td; });", "var td = today(), up = frRows();", 'friends'],
  ["regday: a friend's day is listed twice", "!seen[x.user_id] && (seen[x.user_id] = 1)", "true", 'friends'],
  ["regday: the friends section shows with nobody in it", "    if (up.length) {\n      var cap", "    if (true) {\n      var cap", 'friends'],
  ["regday: “haven't set theirs” counts everyone", "if (!shared[f.id] && !blocked(f.id)) missing++;", "if (!blocked(f.id)) missing++;", 'friends'],
  ["regday: the rail lists everyone", "var cap = where === 'rail' ? 3 : 12", "var cap = 12", 'friends'],
  // ---- the sheet and the time
  ["regday: weekends are offered", "var d = new Date(t), wd = d.getUTCDay(); if (wd > 0 && wd < 6) out.push", "var d = new Date(t), wd = d.getUTCDay(); if (true) out.push", 'save'],
  ["regday: days already gone can be picked", "(d < td ? ' disabled' : '')", "''", 'save'],
  ["regday: the span has no year", " + ', ' + days[days.length - 1].slice(0, 4) : '';", " : '';", 'save'],
  ["regday: Save with no day writes", "if (!dayOk(M.day) || roundDays().indexOf(M.day) < 0 || M.day < today()) {", "if (false) {", 'save'],
  ["regday: a time it cannot read is saved anyway", "if (!p.ok) { M.err =", "if (false) { M.err =", 'save'],
  ["regday: a bare 8 is guessed", "    else if (!(h >= 13 || (m[1].length === 2 && m[1].charAt(0) === '0'))) return { ok: false, time: '' };\n", "", 'parse'],
  ["regday: 12a is noon", "h = (h % 12) + (ap === 'p' ? 12 : 0);", "h = h + (ap === 'p' ? 12 : 0);", 'parse'],
  ["regday: 11:75 is a time", "    if (mi > 59) return { ok: false, time: '' };\n", "", 'parse'],
  // ---- review fixes (regday-fixes)
  ["regday: a blocked friend is drawn", "return friendOf(x.id) && !blocked(x.id); }).sort(", "return friendOf(x.id); }).sort(", 'blocked'],
  ["regday: a failed friends load is never asked again", "if (++RG.frN <= 6) setTimeout(function () { loadFriends(); }, REG_ERR_TTL + 250);", "", 'friendsRefresh'],
  ["regday: the tab coming back does not refresh friends", "{ retry(); loadFriends(); } });", "{ retry(); } });", 'friendsRefresh'],
  ["regday: opening the sheet does not refresh friends", "    loadFriends();\n    var b = back();", "    var b = back();", 'friendsRefresh'],
  ["regday: retry pushes over a newer row from another device", "if (loc && loc.pending && (!row || !row.updated_at || Date.parse(row.updated_at) < (+loc.at || 0))) {", "if (loc && loc.pending) {", 'retryNewer'],
  ["regday: an older write finishing marks itself saved over a newer pending one", "    if (current) { if (v) v.local = false; keep(v, false, k); }", "    if (true) { if (v) v.local = false; keep(v, false, k); }", 'inFlight'],
  /* focus is kept two ways (repaint finds the focused button again; restoreFocus goes back to the opener), so a mutant removes both */
  ["regday: focus is lost after Save", [["    refocus(fk);\n    try { loadFriends(); } catch (_) {}", "    try { loadFriends(); } catch (_) {}"], ["if (fk && fk.slot === where) setTimeout(function () { refocus(fk); }, 0);", ""], ["repaint(); loadFriends(true); restoreFocus(from);", "repaint(); loadFriends(true);"]], null, 'focus'],
  ["regday: focus is lost after Clear", [["    refocus(fk);\n    try { loadFriends(); } catch (_) {}", "    try { loadFriends(); } catch (_) {}"], ["if (fk && fk.slot === where) setTimeout(function () { refocus(fk); }, 0);", ""], ["repaint(); restoreFocus(from);", "repaint();"]], null, 'focus'],
  ["regday: a policy refusal on a write is a missing table", "if (writeGap(q.error)) { RG.gap = true; return null; }\n      /* taking it away", "if (schemaGap(q.error)) { RG.gap = true; return null; }\n      /* taking it away", 'permission'],
  ["regday: the sheet is a dialog inside the dialog", "id=\"rgModal\"></div>';", "id=\"rgModal\" role=\"dialog\"></div>';", 'save'],
  ["regday: the time error is not tied to the field", "' aria-invalid=\"true\" aria-describedby=\"rgErr\"'", "''", 'a11y'],
  ["regday: the banner counts days on the browser's clock", "(typeof regPacificGap==='function'&&c.REGISTRATION_OPENS)?regPacificGap(c.REGISTRATION_OPENS):daysUntil(c.REGISTRATION_OPENS)", "daysUntil(c.REGISTRATION_OPENS)", 'a11y'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutr-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  /* a mutant is one [from, to] pair, or a list of pairs applied together */
  const pairs = Array.isArray(a) ? a : [[a, b]];
  let mutated = html, bad = null;
  for (const [from, to] of pairs) { const n = mutated.split(from).length - 1; if (n !== 1) { bad = n; break; } mutated = mutated.split(from).join(to); }
  if (bad !== null) { console.log('  BAD MUTANT (found ' + bad + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), mutated);
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-regday.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-regday: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
