/* Mutation check for check-desktop-builder: each mutant breaks one promise of the website's Builder
   (website-builder, 2026-10-14); check-desktop-builder must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-builder.mjs  (MUT_ONLY="a|b"; APP_PORT to move off 8190) */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  // ---- what is never a pick
  ["builder: a class you've done is a pick", "if (doneSet[kc] || mineSet[kc] || !offered(code) || !secsOf(code).length) return;", "if (mineSet[kc] || !offered(code) || !secsOf(code).length) return;", 'picks'],
  ["builder: a class you're taking is a pick", "if (doneSet[kc] || mineSet[kc] || !offered(code) || !secsOf(code).length) return;", "if (doneSet[kc] || !offered(code) || !secsOf(code).length) return;", 'picks'],
  ["builder: a class not offered in Spring is a pick", "if (doneSet[kc] || mineSet[kc] || !offered(code) || !secsOf(code).length) return;", "if (doneSet[kc] || mineSet[kc]) return;", 'picks'],
  ["builder: prerequisites are not checked", "var r = prereqOk(code); if (!r.ok) return;", "var r = prereqOk(code);", 'picks'],
  ["builder: HNRS without Honors", "if (/^HNRS\\b/.test(code) && !honors()) return;", "", 'picks'],
  ["builder: the report's satisfied lines count as open", "R.X.open.filter(function (b) { return !auditIsTotal(b); })", "R.X.live.filter(function (b) { return !auditIsTotal(b); })", 'picks'],
  ["builder: the score parts are not the phone's", "var prof = rt == null ? 5 : Math.max(0, Math.min(15, Math.round((rt - 2.5) / 2.5 * 15)));", "var prof = rt == null ? 5 : Math.max(0, Math.min(15, Math.round(rt * 3)));", 'picks'],
  // ---- what matters most
  ["builder: the ranking does not weigh", "w[x] = [1.5, 1.0, 0.6][i];", "w[x] = 1.0;", 'order'],
  ["builder: the ranking is not saved", "if (!UI.noRank) row.ranking = order.join(',');", "", 'order'],
  ["builder: without RUN 19 nothing is saved", "if (q.error && row.ranking && /ranking/.test(q.error.message || '')) {", "if (false) {", 'order'],
  ["builder: the account's answers are not read", "      P = { priority: r.data.priority, units: +r.data.units || 16,", "      if (0) P = { priority: r.data.priority, units: +r.data.units || 16,", 'order'],
  ["builder: units are not saved", "units: async function (v) { var e = await savePrefs(prefOrder(), +v);", "units: async function (v) { var e = await savePrefs(prefOrder(), plUnitsTarget());", 'order'],
  // ---- plans
  ["builder: + adds to another plan", "else if (TCPlans.add(cur, code, id))", "else if (TCPlans.add('B', code, id))", 'add'],
  ["builder: the draft ignores clashes", "var sec = draftSec(c.code, chosen.concat(regTimed), used);", "var sec = draftSec(c.code, [], used);", 'draft'],
  ["builder: the draft ignores commitments", " && !cm.some(function (t) { return secClash(s, t); }); });\n    if (!ss.length) return null;", "; });\n    if (!ss.length) return null;", 'draft'],
  ["builder: the draft goes over the units target", "      if (u != null && units + u > target) continue;\n", "", 'draft'],
  ["builder: a plan you changed is re-drafted without asking", "var changed = SLOTS.filter(function (sl) { return !untouched(sl, d); });", "var changed = [];", 'draft'],
  // ---- states
  ["builder: no upload card", "if (!A && !(R && R.hasFlow)) {", "if (false) {", 'states'],
  ["builder: no done view", "} else if (R && R.done) {", "} else if (false) {", 'states'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutb-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-builder.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-builder: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
