/* mutate-desktop-hawk-places — each mutant breaks one promise of website-hawk-help-chips; check-desktop-hawk-places must fail.
   Run: SRC_DIR=<repo> node mutate-desktop-hawk-places.mjs */
import fs from 'fs'; import path from 'path'; import os from 'os'; import { execFileSync } from 'child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ['the router refusal shows no chips', "if (!helpChips(turn, q)) turn.appendChild", 'turn.appendChild'],
  ['not_about_classes shows no chips', "if (helpChips(turn, q)) why = 'shown';\n        else ", ''],
  ['no help rows at all', 'return ks.map(function (k) {', 'return [].map(function (k) {'],
  /* Dropped: "a course question can get a chip" (helpMatch's course guard). On the website the on-device router answers any
     question naming a course before the help path is reached, so no page-level test can tell the guard apart; the guard is
     the phone's verbatim code and is mutation-tested there (champHelp). The check still asserts the promise end to end. */
  ['a chip asks the model', 'render(APP_HELP_Q[k], {', "HawkAsk.ask(APP_HELP_Q[k]); return 'x'; render(APP_HELP_Q[k], {"],
  ['dark mode says System again', 'Settings › Appearance: Light or Dark.', 'Settings › Appearance: System, Light or Dark.'],
  ['Plans button opens the Planner', "'Open Plans', 'watchlist'", "'Open Plans', 'planner'"],
  ['the rules never hear “hawk”', 'ai: /\\b(hawk|champ|', 'ai: /\\b(champ|'],
  ['Not it? / not-sure answers drop the help rows', 'hrows.forEach(function (r) { box.appendChild(rowEl(r)); });', ''],
];
let caught = 0;
for (const [name, a, b] of M) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'hpm-'));
  for (const f of ['index.html', 'hawk-ask.js', 'hawk-router.js', 'hawk-ask.css', 'sw.js']) if (fs.existsSync(path.join(SRC, f))) fs.copyFileSync(path.join(SRC, f), path.join(dir, f));
  fs.mkdirSync(path.join(dir, 'supabase/functions/ask'), { recursive: true }); fs.copyFileSync(path.join(SRC, 'supabase/functions/ask/shared.ts'), path.join(dir, 'supabase/functions/ask/shared.ts'));
  const js = fs.readFileSync(path.join(dir, 'hawk-ask.js'), 'utf8'); const n = js.split(a).length - 1;
  if (n !== 1) { console.log(`  BAD anchor (${n}x): ${name}`); continue; }
  fs.writeFileSync(path.join(dir, 'hawk-ask.js'), js.replace(a, b));
  let failed = false;
  try { execFileSync('node', ['check-desktop-hawk-places.mjs', '--quiet'], { env: { ...process.env, APP_DIR: dir }, stdio: 'pipe', timeout: 600000 }); } catch (e) { failed = true; }
  console.log(`  ${failed ? 'caught  ' : 'SURVIVED'} ${name}`); if (failed) caught++;
}
console.log(`\nmutate-desktop-hawk-places: ${caught}/${M.length} caught`);
