/* Mutation check for check-app: each mutant breaks one promise the app makes; check-app must
   FAIL on every one. A mutant that survives means a test that is not testing anything. */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = path.resolve('../out/app/index.html');
const M = [
  ['description chrome kept', "if (!l) return null; t = t.slice(l.index + l[0].length);", "if (!l) return null;", 'classDetail'],
  ['unknown status counted as full', "return available > 0 ? 'open' : 'unknown';", "return available > 0 ? 'open' : 'full';", 'classDetail'],
  ['orphaned section rows shown', "if (!code || !keep.has(code)) return;", "if (!code) return;", 'friendProfile'],
  ['PolyRatings count dropped', "P.count = p.numEvals || 0;", "P.count = 0;", 'explore'],
  ['would-again counts everyone', "againN.filter(v => v.would_again).length", "againN.length", 'explore'],
  ['review score hardcoded', "course: d.code || null, score: d.stars,", "course: d.code || null, score: 5,", 'rate'],
  ['invented chat reply', "if (!ok) inp.value = v;", "if (!ok) inp.value = v; (TC.rows[id] = TC.rows[id] || []).push({ id: 'fake', sender: 'x', kind: 'text', body: 'lol yes', created_at: new Date().toISOString() });", 'friends'],
  ['plan upsert without conflict key', "{ onConflict: 'user_id,term,slot' })", ")", 'plans'],
  ['plan removal un-watches everything', "else if (!inP && w && TC.autoWatch[id])", "else if (!inP && w)", 'autowatch'],
  ['Staff treated as a professor', "/^(staff|tba|tbd|to be announced)$/i", "/^(tba)$/i", 'explore'],
  ['fixed prototype clock', "get min() { return slo().min; }", "get min() { return 581; }", 'status'],
  ['Champ ignores open_only', "if (a.open_only && s.status !== 'open') return false;", "", 'champ'],
  ['Champ sends the user id', "JSON.stringify(Object.assign({ q, term: CFG.TERM, who }", "JSON.stringify(Object.assign({ q, term: CFG.TERM, who, user_id: TC.user.id }", 'champ'],
  ['partial seat feed published', "if (!complete || !rows.length) { TC.err.seats = true;", "if (!rows.length) { TC.err.seats = true;", 'seatsPartial'],
  ['second review allowed', "if (iReviewed(pid)) { toast('You’ve already reviewed ' + profName(pid)); return; }", "", 'rateOnce'],
  ['accept by the wrong key', "from('friend_requests').update({ status: 'accepted' }).eq('id', rid)", "from('friend_requests').update({ status: 'accepted' }).eq('from_user', id)", 'requests'],
  ['missing rating filled in', "? PROFS[pk].r : null;", "? PROFS[pk].r : 4.0;", 'noPoly'],
  ['message kind changed', "sender: TC.user.id, kind: 'text', body, payload: null", "sender: TC.user.id, kind: 'msg', body, payload: null", 'friends'],
  ['prototype name on Home', "<div class=\"mk-t\">You might know</div>", "<div class=\"mk-t\">You might know Garrett</div>", 'home'],
  ['signed-out gate removed', "if (TC.phase !== 'ok') {", "if (false) {", 'signedOut'],
  ['saved classes ignored for me', "const mine = [...new Set((codes.data || []).map(r => canonCode(r.code)).filter(Boolean))];", "const mine = [...new Set((secs.data || []).map(r => canonCode(r.code)).filter(Boolean))];", 'schedule'],
  ['double tap sends twice', "if (UI.busy['f' + id]) return; UI.busy['f' + id] = 1;", "", 'requests'],
  ['word filter skipped', "const bad = wfHit(d.review || '');", "const bad = null;", 'wordFilter'],
  ['failed chat load shown as empty', "if (r.error) { TC.rowsErr[cid] = true;", "if (r.error) { TC.rows[cid] = []; TC.rowsErr[cid] = false;", 'chatFail'],
  ['rate list per class, not per professor', "if (s.prof && !seen[s.prof]) { seen[s.prof] = 1;", "if (s.prof && !seen[s.prof + s.code]) { seen[s.prof + s.code] = 1;", 'rate'],
  ['stat floor removed', "const STAT_MIN = 3;", "const STAT_MIN = 1;", 'prof'],
  ['raw 0–4 PolyRatings score shown', "P.r = Math.round((+p.overallRating / 4 * 5) * 100) / 100;", "P.r = +p.overallRating;", 'prof'],
];
const html = fs.readFileSync(SRC, 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mut-'); fs.mkdirSync(path.join(tmp, 'app'));
let caught = 0, survived = [];
for (const [name, a, b, test] of M) {
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'app', 'index.html'), html.replace(a, b));
  let failed = false;
  try { execFileSync('node', ['check-app.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 300000 }); }
  catch (e) { failed = true; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
