/* Mutation check for check-desktop-commitments: each mutant breaks one promise of the website's Work & activities
   (website-commitments, 2026-10-14); check-desktop-commitments must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-commitments.mjs  (MUT_ONLY="a|b"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  // ---- what is written
  ["cm: the upsert has no conflict target", "busy: !!x.busy }, { onConflict: 'id' })", "busy: !!x.busy })", 'modal'],
  ["cm: friends can always see it", "start_min: x.s, end_min: x.e, busy: !!x.busy }", "start_min: x.s, end_min: x.e, busy: true }", 'modal'],
  ["cm: no name is written as an empty string", "name: x.name || null,", "name: x.name,", 'modal'],
  ["cm: Sport is not a kind the table knows", "KIND_ORDER = ['work', 'club', 'practice', 'other']", "KIND_ORDER = ['work', 'club', 'sport', 'other']", 'modal'],
  ["cm: delete is not scoped to you", ".delete().eq('id', x.id).eq('user_id', uid)", ".delete().eq('id', x.id)", 'drop'],
  ["cm: delete does not delete", "gone ? await c.from('commitments').delete()", "gone ? await c.from('commitments').select('id')", 'drop'],
  ["cm: a deleted one stays on this device", "CM.list = CM.list.filter(function (y) { return y.id !== id; }); writeLocal(uid, CM.list);", "CM.list = CM.list.filter(function (y) { return y.id !== id; });", 'drop'],
  // ---- a refused write
  ["cm: a 42501 is treated as a missing table", "return c === '42P01' || c === 'PGRST205' || c === '42703'; }", "return c === '42P01' || c === 'PGRST205' || c === '42703' || c === '42501'; }", 'refused'],
  ["cm: a refused save says it is saved", "return gone ? dropMsg : saveMsg;", "return null;", 'refused'],
  ["cm: a refused save is not marked waiting", "var p = readPend(uid); p[x.id] = 'save'; writePend(uid, p);", "var p = readPend(uid);", 'refused'],
  ["cm: nothing retries when it is back online", "doSave(); }\n  }, true);\n  window.addEventListener('online', function () { retry(); });\n  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { retry(); loadFriends(false); } });", "doSave(); }\n  }, true);\n  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { retry(); loadFriends(false); } });", 'refused'],
  ["cm: a save that is slow overtakes the delete after it", "    var k = uid + ':' + x.id, run = (Q[k] || Promise.resolve()).then(function () { return pushNow(uid, x, gone); });\n    Q[k] = run.catch(function () {});\n    return run;", "    return pushNow(uid, x, gone);", 'order'],
  ["cm: a delete that is waiting does not stop an older save", "    if (!gone && readPend(uid)[x.id] === 'drop') return null;               /* deleted since: do not bring it back */\n", "", 'order'],
  ["cm: a friend with no id gets your own names", "    if (!who) return;\n    blocks(who).forEach(function (b) {", "    blocks(who).forEach(function (b) {", 'free'],
  ["cm: the account's old row beats the change waiting here", ".map(function (x) { return (pend[x.id] === 'save' || touched[x.id]) && cur[x.id] ? cur[x.id] : x; });", ".map(function (x) { return x; });", 'refused'],
  ["cm: a missing table is not remembered (and is hammered)", "if (gapOf(q.error)) { if (CM.uid === uid) CM.gap = true; return null; }", "if (gapOf(q.error)) { return null; }", 'refused'],
  ["cm: a refused delete does not say friends can still see it", "var dropMsg = 'Couldn’t remove that from your account yet — friends can still see it as Busy until it goes through.';", "var dropMsg = 'Couldn’t remove that.';", 'refused'],
  // ---- signing out
  ["cm: a read that lands after a sign-out still paints", "if (CM.uid !== uid || !user() || user().id !== uid) return;            /* signed out or switched while this was in flight */", "", 'reset'],
  ["cm: sign-out keeps your list in memory", "CM.list = []; CM.fr = {}; CM.frAt = 0;", "CM.fr = {}; CM.frAt = 0;", 'reset'],
  ["cm: the card shows to a signed-out student", "function cardHtml() {\n    var u = user(); if (!u || CM.uid !== u.id) return '';", "function cardHtml() {\n    var u = user();", 'rows'],
  // ---- privacy
  ["cm: a friend's week is drawn with your own blocks", "    if (isMe) {\n      return CM.list.map", "    if (true) {\n      return CM.list.map", 'blocks'],
  ["cm: a friend's busy blocks are not asked for", "c.rpc('friend_busy_blocks')", "c.rpc('friend_busy_block')", 'blocks'],
  // ---- the blocks
  ["cm: no weekend column on My classes", "if(_cm.some(function(b){return b.meet.days.indexOf('Sa')>=0;}))DAYS.push('Sa');", "if(false)DAYS.push('Sa');", 'blocks'],
  ["cm: My classes draws none of yours", "renderMyCalendar(codes,conf,undefined,{cm:'me'})", "renderMyCalendar(codes,conf)", 'blocks'],
  ["cm: Home's My schedule draws none of yours", "var i=0,blocks=(typeof cmMiniOwnHtml==='function')?cmMiniOwnHtml(_cm,d,lo,span,H):'';", "var i=0,blocks='';", 'blocks'],
  ["cm: a friend's Home card draws no busy", "win:window._hmFeedWin||null,cm:f.id})", "win:window._hmFeedWin||null})", 'blocks'],
  ["cm: a friend's profile week draws no busy", "peopleFor:frpPeopleFor,cm:f.id", "peopleFor:frpPeopleFor", 'blocks'],
  ["cm: the hatch is the class blue", "transparent 4px 9px),var(--panel-3)}", "transparent 4px 9px),var(--panel-3)}\n.cal-cm{background:var(--clsblk)!important}", 'blocks'],
  ["cm: the choose-in term view has no card", "window.cmEnsureSlot = function (out) { if (out && !out.querySelector('.cm-slot')) out.insertAdjacentHTML('beforeend', slotHtml()); };", "window.cmEnsureSlot = function (out) {};", 'terms'],
  // ---- free time and the status line
  ["cm: your status says “In Barista”", "return st.code+' till '+cmHs(st.until);", "return 'In '+st.code+' till '+cmHs(st.until);", 'free'],
  ["cm: the status uses the long clock", "return st.code+' till '+cmHs(st.until);", "return st.code+' till '+avHM(st.until);", 'free'],
  ["cm: free time ignores your work", "cmPushBusy(out,'me')", "0", 'free'],
  ["cm: free time ignores a friend's busy", "cmPushBusy(out,f.id)", "0", 'free'],
  ["cm: “No class till” is moved by a busy block", "&&!day[i].cm){ next=day[i]; }", "){ next=day[i]; }", 'free'],
  ["cm: a friend with only busy blocks gets “no class”", "if(!_cls)return {state:'unknown'};", "", 'free'],
  ["cm: a busy block beats the class you are in", "if(!(cur&&!cur.cm&&day[i].cm))cur=day[i];", "cur=day[i];", 'free'],
  // ---- overlap
  ["cm: touching counts as overlapping", "if (common.length && meet.start < b.meet.end && b.meet.start < meet.end)", "if (common.length && meet.start <= b.meet.end && b.meet.start <= meet.end)", 'overlap'],
  ["cm: the overlap names every day of the commitment", "out.push({ b: b, days: common })", "out.push({ b: b, days: b.meet.days })", 'overlap'],
  ["cm: the My classes pill is the red one", "tone: 'note', label: labels.length === 1", "tone: 'warn', label: labels.length === 1", 'overlap'],
  ["cm: My classes has no overlap pill", "if(_cf)flags.push(_cf);", "", 'overlap'],
  ["cm: the class page does not say so", "if(!hits.length)return _cmChip;", "if(!hits.length)return '';", 'overlap'],
  // ---- the sheet and the time
  ["cm: an end before the start is saved", "if (f.ok && t.ok && t.min <= f.min)", "if (false)", 'modal'],
  ["cm: a bad time is not tied to its field", "(E.from ? ' aria-invalid=\"true\" aria-describedby=\"cmErrFrom\"' : '')", "''", 'modal'],
  ["cm: no day is fine", "if (!M.days) E.days =", "if (false) E.days =", 'modal'],
  ["cm: focus is lost when the sheet closes", "    focusLive(id);                          /* the row you came from may have been redrawn: focus the live one */", "", 'modal'],
  ["cm: a bare 4 is guessed", "    else if (!(h >= 13 || (m[1].length === 2 && m[1].charAt(0) === '0'))) return { ok: false, min: null, why: h > 23 ? 'bad' : 'ampm' };\n", "", 'parse'],
  ["cm: 12pm is midnight", "h = (h % 12) + (a === 'p' ? 12 : 0);", "h = h + (a === 'p' ? 12 : 0);", 'parse'],
  ["cm: 12am as an end is not midnight", "    if (isEnd && v === 0) v = 1440;\n", "", 'parse'],
  ["cm: 4:75 is a time", "    if (mi > 59) return { ok: false, min: null, why: 'bad' };\n", "", 'parse'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutc-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
const SL = process.env.MUT_SLICE ? process.env.MUT_SLICE.split('/').map(Number) : null;   /* "k/n": every n-th mutant starting at k, to run slices side by side */
let idx = -1;
for (const [name, a, b, test] of M) {
  idx++;
  if (SL && idx % SL[1] !== SL[0]) continue;
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-commitments.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-commitments: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : SL ? M.filter((_, i) => i % SL[1] === SL[0]).length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
