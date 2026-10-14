/* Mutation check for check-desktop-replace: each mutant breaks one promise of Clash -> Replace on the website
   (website-clash-replace, 2026-10-14); check-desktop-replace must FAIL on every one.
   Run: SRC_DIR=<repo> node mutate-desktop-replace.mjs  (MUT_ONLY="a|b") */
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ["replace: Replace leaves the old class in", "  mcReplaceRemove(cl);\n  mcCommitSection(code,e.s,e.status,e.wlPos);", "  mcCommitSection(code,e.s,e.status,e.wlPos);", 'myClasses'],
  ["replace: the dialog never offers it", "  var e=_enrollState, cl=(e.code&&e.s)?mcClashesOf(e.code,e.s):[];\n  if(!cl.length)return '<div class=\"si-actions\"", "  var e=_enrollState, cl=[];\n  if(!cl.length)return '<div class=\"si-actions\"", 'myClasses'],
  ["replace: a class clashes with itself", "      if(((typeof canonCode==='function')?(canonCode(m.code)||m.code):m.code)===cc)return;\n", "", 'myClasses'],
  ["replace: no overlap check", "      if(!meetsOverlap(meet,m.meet))return;\n      var k=String(m.key||'')", "      var k=String(m.key||'')", 'myClasses'],
  ["replace: Undo keeps the new class", "    if(ix>=0)mcRemoveSection(code,ix); else if(isMyClass(code)&&!arr.length)toggleMyClass(code);\n  }catch(e){}\n  removed.forEach", "  }catch(e){}\n  removed.forEach", 'myClasses'],
  ["replace: Undo doesn't bring the old class back", "  removed.forEach(function(c){\n    try{\n      if(c.rec){", "  [].forEach(function(c){\n    try{\n      if(c.rec){", 'myClasses'],
  ["replace: no Undo on the toast", "  tcToastAct(code+' replaced '+(names.length===1?names[0]:(names.length+' classes')),'Undo',function(){ mcReplaceUndo(code,crn,cl); });", "  try{ frToast(code+' replaced '+(names.length===1?names[0]:(names.length+' classes'))); }catch(_){}", 'myClasses'],
  ["replace: Keep both replaces", "<button class=\"btn\" onclick=\"enConfirm()\">Keep both</button>", "<button class=\"btn\" onclick=\"enReplace()\">Keep both</button>", 'myClasses'],
  ["replace: a clash is added at once in a plan", "      else if (clashesIn(slot, code, crn).length) { clashPanel(slot, code, crn); return; }\n", "", 'plans'],
  ["replace: the plan keeps the clashing section", "filter(function (x) { return !drop[x.class_nbr]; })", "filter(function (x) { return true; })", 'plans'],
  ["replace: the plan's Undo does nothing", "function () { setSections(slot, before); try", "function () { try", 'plans'],
  ["replace: Keep both doesn't add in a plan", "    if (act === 'chkeep') { if (add(slot, code, crn)) toast(code + ' → Plan ' + slot + ' · watching it'); chAfter(crn); return; }", "    if (act === 'chkeep') { chAfter(crn); return; }", 'plans'],
];
const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tmp = fs.mkdtempSync('/tmp/claude-0/mutrp-');
for (const e of fs.readdirSync(SRC)) if (e !== 'index.html' && e !== '.git') fs.symlinkSync(path.join(SRC, e), path.join(tmp, e));
let caught = 0; const survived = [];
const ONLY = process.env.MUT_ONLY ? process.env.MUT_ONLY.split('|') : null;
for (const [name, a, b, test] of M) {
  if (ONLY && !ONLY.includes(name)) continue;
  const n = html.split(a).length - 1;
  if (n !== 1) { console.log('  BAD MUTANT (found ' + n + '×):', name); survived.push(name + ' (bad)'); continue; }
  fs.writeFileSync(path.join(tmp, 'index.html'), html.split(a).join(b));
  let failed = false, out = '';
  try { execFileSync('node', ['check-desktop-replace.mjs', '--quiet', '--only', test], { env: { ...process.env, APP_DIR: tmp }, stdio: 'pipe', timeout: 200000 }); }
  catch (e) { failed = true; out = String(e.stdout || '') + String(e.stderr || ''); }
  if (failed && (!/check-desktop-replace: \d+ passed, [1-9]\d* failed/.test(out) || /EADDRINUSE/.test(out))) { console.log('  BROKE   ', name, '— the run crashed/timed out; rerun it'); survived.push(name + ' (broke)'); continue; }
  if (failed) { caught++; console.log('  caught  ', name); } else { survived.push(name); console.log('  SURVIVED', name); }
}
console.log(`\nmutations: ${caught}/${ONLY ? ONLY.length : M.length} caught`);
if (survived.length) { console.log('survived:', survived.join(' | ')); process.exit(1); }
