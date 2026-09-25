import fs from 'node:fs'; import { spawn } from 'node:child_process';
const src = fs.readFileSync(process.env.SRC || 'build.html', 'utf8');
const Mtxt = fs.readFileSync('mutate.mjs', 'utf8');
const M = eval(Mtxt.slice(Mtxt.indexOf('const M = [') + 10, Mtxt.indexOf('];\nlet caught') + 1));
const jobs = M.map(([name, a, b], i) => ({ name, a, b, i }));
const results = []; let next = 0;
async function worker(w) {
  while (next < jobs.length) {
    const j = jobs[next++]; const n = src.split(j.a).length - 1;
    if (n !== 1) { results.push(`SKIP    ${j.name} — anchor ×${n}`); continue; }
    const f = `mut-${w}.html`; fs.writeFileSync(f, src.replace(j.a, j.b));
    const rc = await new Promise(r => { const p = spawn('node', ['check-mobile.mjs', f], { env: { ...process.env, PORT_BASE: String(100 * (w + 1)) }, stdio: 'ignore' });
      const t = setTimeout(() => p.kill(), 400000); p.on('exit', c => { clearTimeout(t); r(c); }); });
    results.push(`${rc ? 'CAUGHT ' : 'MISSED '} ${j.name}`); fs.appendFileSync('mut-progress.txt', results[results.length - 1] + '\n');
  }
}
fs.writeFileSync('mut-progress.txt', '');
await Promise.all([0, 1].map(worker));
results.sort((x, y) => x.slice(8).localeCompare(y.slice(8)));
console.log(results.join('\n')); console.log(`\n${results.filter(r => r.startsWith('CAUGHT')).length}/${M.length} caught`);
fs.writeFileSync('mut-result.txt', results.join('\n'));
