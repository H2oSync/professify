/* mutate-desktop-champ — each mutant breaks one promise of check-desktop-champ; check-desktop-champ must fail.
   Each mutant names the file it changes (hawk-ask.js, hawk-ask.css or index.html).
   Run: SRC_DIR=<repo> node mutate-desktop-champ.mjs */
import fs from 'fs'; import path from 'path'; import os from 'os'; import { execFileSync } from 'child_process';
const SRC = process.env.SRC_DIR || path.resolve('../..');
const M = [
  ['a starter chip asks a different question', 'hawk-ask.js', "['cc2', 'Who\\'s free right now?']", "['cc2', 'Where is my next class?']"],
  ['"Hawk" is back in the header', 'hawk-ask.js', "make('span', 'hawk-head__name', 'Champ')", "make('span', 'hawk-head__name', 'Hawk')"],
  ['the placeholder says Hawk', 'hawk-ask.js', "input.placeholder = 'Ask Champ…';", "input.placeholder = 'Ask Hawk…';"],
  ['a hardcoded white surface', 'hawk-ask.css', "background: var(--hawk-navy-lift);\n  color: var(--hawk-ink);\n  border: 1px solid var(--hawk-rule);", "background: #ffffff;\n  color: var(--hawk-ink);\n  border: 1px solid var(--hawk-rule);"],
  ['a low-contrast chip', 'hawk-ask.css', '.hawk-cc1 { background: var(--hawk-cc1-bg); color: var(--hawk-cc1-ink); }', '.hawk-cc1 { background: var(--hawk-cc1-bg); color: #cccccc; }'],
  ['the footer never mentions Anthropic', 'hawk-ask.js', "'Some questions go to Anthropic’s AI · your classes stay on this device'", "'Some questions go to our AI · your classes stay on this device'"],
];
let caught = 0;
for (const [name, file, a, b] of M) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cpm-'));
  for (const f of ['index.html', 'hawk-ask.js', 'hawk-router.js', 'hawk-ask.css', 'sw.js']) if (fs.existsSync(path.join(SRC, f))) fs.copyFileSync(path.join(SRC, f), path.join(dir, f));
  fs.mkdirSync(path.join(dir, 'supabase/functions/ask'), { recursive: true }); fs.copyFileSync(path.join(SRC, 'supabase/functions/ask/shared.ts'), path.join(dir, 'supabase/functions/ask/shared.ts'));
  const txt = fs.readFileSync(path.join(dir, file), 'utf8'); const n = txt.split(a).length - 1;
  if (n !== 1) { console.log(`  BAD anchor (${n}x): ${name}`); continue; }
  fs.writeFileSync(path.join(dir, file), txt.replace(a, () => b));
  let failed = false;
  try { execFileSync('node', ['check-desktop-champ.mjs', '--quiet'], { env: { ...process.env, APP_DIR: dir }, stdio: 'pipe', timeout: 600000 }); } catch (e) { failed = true; }
  console.log(`  ${failed ? 'caught  ' : 'SURVIVED'} ${name}`); if (failed) caught++;
}
console.log(`\nmutate-desktop-champ: ${caught}/${M.length} caught`);
