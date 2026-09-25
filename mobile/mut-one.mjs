import fs from 'node:fs'; import { execFileSync } from 'node:child_process';
const src = fs.readFileSync(process.env.SRC || 'build.html', 'utf8'); const t = fs.readFileSync('mutate.mjs', 'utf8');
const M = eval(t.slice(t.indexOf('const M = [') + 10, t.indexOf('];\nlet caught') + 1));
for (const name of process.argv.slice(2)) { const m = M.find(x => x[0].startsWith(name)); const n = src.split(m[1]).length - 1;
  if (n !== 1) { console.log('SKIP', m[0], n); continue; }
  fs.writeFileSync('mut-x.html', src.replace(m[1], m[2])); let rc = 0;
  try { execFileSync('node', ['check-mobile.mjs', 'mut-x.html'], { stdio: 'pipe', timeout: 700000 }); } catch (e) { rc = e.status || 1; }
  console.log(rc ? 'CAUGHT ' : 'MISSED ', m[0]); }
