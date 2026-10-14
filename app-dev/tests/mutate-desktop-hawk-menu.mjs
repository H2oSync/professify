/* Mutation check for check-desktop-hawk-menu: each mutant breaks one promise of Hawk's app menu on the website
   (website-hawk-app-menu, 2026-10-14); check-desktop-hawk-menu must FAIL on every one. The mutants edit hawk-ask.js.
   Run: SRC_DIR=<repo> node mutate-desktop-hawk-menu.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["hawk-menu: the question isn't sent as the app", "callAsk({ q: q, client: 'app' })", "callAsk({ q: q })", 'freeNow'],
  ["hawk-menu: everyone is free now", "      if (st.state === 'open') free.push({ f: f, st: st });\n      else if (st.state === 'unknown') unknown += 1;", "      free.push({ f: f, st: st });", 'freeNow'],
  ["hawk-menu: a friend with no times is guessed free", "      else if (st.state === 'unknown') unknown += 1;", "      else if (st.state === 'unknown') { free.push({ f: f, st: st }); }", 'freeNow'],
  ["hawk-menu: the named friend is ignored", "    if (a.friend) {\n      var f = friendByName(a.friend);", "    if (false) {\n      var f = friendByName(a.friend);", 'freeWith'],
  ["hawk-menu: best professor isn't ranked", "    order.sort(function (x, y) { var rx = by[x].p.rating, ry = by[y].p.rating; return (ry == null ? -1 : ry) - (rx == null ? -1 : rx); });", "    order.reverse();", 'bestProf'],
  ["hawk-menu: best professor shows no rating", "        chip: p.rating != null ? ratingChip(p.rating) : null,\n        go: function () { return p.id ? goProfessor", "        chip: null,\n        go: function () { return p.id ? goProfessor", 'bestProf'],
  ["hawk-menu: the plan asked about is ignored", "fit = T.fitFor(code, slot); } catch (_) {}", "fit = T.fitFor(code, 'B'); } catch (_) {}", 'fitsPlan'],
  ["hawk-menu: a fitting section doesn't open its class", "        go: function () { return goSection(code, i.crn, i.label); } }));", "        go: function () { return 'Opened'; } }));", 'fitsPlan'],
  ["hawk-menu: an unknown help topic is answered on a guess", "Object.prototype.hasOwnProperty.call(APP_HELP, k) ? APP_HELP[k] : null;", "Object.prototype.hasOwnProperty.call(APP_HELP, k) ? APP_HELP[k] : APP_HELP.free;", 'appHelp'],
  ["hawk-menu: help has no Go there row", "    turn.appendChild(rowEl({ code: '', name: h[1], chip: null,\n      go: function () { if (h[2] === 'mailto')", "    if (0) turn.appendChild(rowEl({ code: '', name: h[1], chip: null,\n      go: function () { if (h[2] === 'mailto')", 'appHelp'],
];
const file = 'hawk-ask.js';
const src = fs.readFileSync(path.join(SRC, file), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/muthk-');
for (const e of fs.readdirSync(SRC)) if (e !== file && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = src.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, file), src.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-hawk-menu.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 200000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-hawk-menu: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed/timed out; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
