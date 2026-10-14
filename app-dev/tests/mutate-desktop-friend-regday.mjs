/* Mutation check for check-desktop-friend-regday: each mutant breaks one promise of a friend's registration day on their page
   (website-friend-regday, 2026-10-14); check-desktop-friend-regday must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-friend-regday.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["friend regday: the year is dropped", "weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }); } catch (_) { return d; }\n  }\n  function friendRowInner", "weekday: 'short', month: 'short', day: 'numeric' }); } catch (_) { return d; }\n  }\n  function friendRowInner", 'line'],
  ["friend regday: no “before you”", "var t = timeText(x.time), r = x.day === td ? '' : rel(x.day);\n    var when = x.day === td ? 'Registers today'", "var t = timeText(x.time), r = '';\n    var when = x.day === td ? 'Registers today'", 'relative'],
  ["friend regday: a time is made up for a day with none", "var t = timeText(x.time), r = x.day === td ? '' : rel(x.day);\n    var when = x.day === td ? 'Registers today'", "var t = timeText(x.time || '09:00'), r = x.day === td ? '' : rel(x.day);\n    var when = x.day === td ? 'Registers today'", 'line'],
  ["friend regday: today reads as a date", "var when = x.day === td ? 'Registers today' + (t ? ' at ' + t : '') : 'Registers '", "var when = false ? 'Registers today' + (t ? ' at ' + t : '') : 'Registers '", 'relative'],
  ["friend regday: a day that has passed still shows", "    if (!x || x.day < td) return '';\n    var t = timeText(x.time), r = x.day === td", "    if (!x) return '';\n    var t = timeText(x.time), r = x.day === td", 'line'],
  ["friend regday: a non-friend's day is listed", "return F.rows.filter(function (x) { return friendOf(x.id) && !blocked(x.id); })", "return F.rows.filter(function (x) { return !blocked(x.id); })", 'absent'],
  ["friend regday: the page asks again every time", "if (active() && !RG.frBusy) setTimeout(function () { loadFriends(); }, 0);\n    return '<div class=\"rg-frrow\"", "if (active() && !RG.frBusy) setTimeout(function () { loadFriends(true); }, 0);\n    return '<div class=\"rg-frrow\"", 'line'],
  ["friend regday: a list that arrives doesn't fill the open page", "for (var j = 0; j < fr.length; j++) fr[j].innerHTML = friendRowInner(fr[j].getAttribute('data-rg-fr'));", "", 'late'],
  ["friend regday: the header has no line", "${(window.TCReg&&TCReg.friendRow)?TCReg.friendRow(f.id):''}", "", 'line'],
  ["friend regday: an empty line takes room", ".rg-frrow:empty{display:none}", ".rg-frrow:empty{display:flex;min-height:20px}", 'line'],
  ["friend regday: a failed load leaves a line", "'<div class=\"rg-frrow\" data-rg-fr=\"' + esc(id) + '\">' + friendRowInner(id) + '</div>'", "'<div class=\"rg-frrow\" data-rg-fr=\"' + esc(id) + '\">' + (friendRowInner(id) || '<span>Registration day not shared</span>') + '</div>'", 'absent'],
  ["friend regday: the line is faint in light", ".rg-frrow{display:flex;align-items:center;gap:7px;margin-top:6px;font-size:13px;font-weight:600;color:var(--text-2);", ".rg-frrow{display:flex;align-items:center;gap:7px;margin-top:6px;font-size:13px;font-weight:600;color:#aaa;", 'contrast-light'],
  ["friend regday: the date is lost in dark", ".rg-frrow b{font-weight:700;color:var(--text)}", ".rg-frrow b{font-weight:700;color:#444}", 'contrast-dark'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutfr-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-friend-regday.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 400000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-friend-regday: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
