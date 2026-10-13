/* Champ understanding test, v3 (2026-10-08) — and the gate before `ask` is deployed.

   Runs dev/golden/model-golden-v3.json (434 questions: the 2026-09-26 set adapted to the phone, the
   phone's own tools, the who's-free / when-am-I-free kind of mix-ups, the 16 TermChamp-help topics asked
   several ways each, and Tate's own questions) through
   the REAL prompt, menu and validator — routeSpec('app', …) from supabase/functions/ask/shared.ts,
   exactly what the phone gets — and scores the tool AND the arguments.

   By default it also runs the same questions on the website's menu (what the phone got before this
   change), so the first run shows what the new menu is worth.

   Run it in Terminal from the repo folder:

     export ASSISTANT_API_KEY='…'        # the same key as the Supabase secret. Type it HERE,
                                         # in your terminal — never in a chat.
     npx deno run --allow-net --allow-env --allow-read --allow-write dev/golden/check-models-v3.ts --accept

   (--accept writes the score only if the run PASSES, so it is safe on every run.)

   Default model: claude-haiku-5-5 (2026-10-11; about $0.06 for both menus). Haiku 4.5 served students
   before it; to compare the two:  … check-models-v3.ts claude-haiku-5-5 claude-haiku-4-5-20251001  (≈ $0.60 more)
   --only-app   skip the website-menu run (half the cost; use it on later runs)

   THE GATE. dev/golden/baseline.json holds the best accepted pass RATE per model, with the menu's
   fingerprint. The run FAILS — don't deploy `ask` — when:
     • more than 2% of the calls errored (a bad key, the network): that run measured nothing;
     • the phone menu passes under 80% of the questions (the 2026-09-26 menu passed 89.7% of its set);
     • on the questions the website menu CAN answer (no new tool among the right answers), the phone
       menu does worse than the website menu — so the four new tools can't hide a loss elsewhere
       (needs both menus, so not with --only-app);
     • its rate is more than ONE question's worth below the accepted rate (one question of slack,
       because the model is not perfectly repeatable from run to run).
   With --accept a passing run is recorded. The accepted rate only ever goes UP — a lower passing
   run is not written — so the slack can't ratchet down. The offline check that runs on every build
   (check-golden.ts) fails when the menu changes after the score was accepted, so a changed prompt
   can't ship unscored.

   It never touches the live site, the database or anyone's limits: it calls the model directly with
   the key, exactly as the function does. Results: dev/golden/model-results-v3-<date>.json */
import * as SH from '../../supabase/functions/ask/shared.ts';
import { passes, matches, expectations, concrete, fingerprint } from './score.ts';

const DRY = Deno.env.get('HAWK_DRY') || '';   // self-test only: 'right' answers with the expected call, 'wrong' with a broken one, 'error' fails every call
const KEY = Deno.env.get('ASSISTANT_API_KEY') || Deno.env.get('ANTHROPIC_API_KEY') || (DRY ? 'dry' : '');
if (!KEY) { console.error('Set ASSISTANT_API_KEY in this terminal first (see the top of this file).'); Deno.exit(1); }
const flags = Deno.args.filter((a) => a.startsWith('--'));
const models = Deno.args.filter((a) => !a.startsWith('--'));
if (!models.length) models.push('claude-haiku-5-5');
const ONLY_APP = flags.includes('--only-app'), ACCEPT = flags.includes('--accept');
const golden = JSON.parse(await Deno.readTextFile(new URL('./model-golden-v3.json', import.meta.url)));
const TERM = 'Fall 2026';
const MENUS: [string, string][] = ONLY_APP ? [['phone menu', 'app']] : [['phone menu', 'app'], ['website menu', 'web']];
const FP = await fingerprint(SH.APP_SYSTEM(TERM), SH.APP_TOOLS, await Deno.readTextFile(new URL('../../supabase/functions/ask/shared.ts', import.meta.url)));
const baseFile = new URL('./baseline.json', import.meta.url);
let baseline: any = {};
try { baseline = JSON.parse(await Deno.readTextFile(baseFile)); } catch (_) { baseline = {}; }

async function one(model: string, client: string, c: any) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 30000);
  const started = Date.now();
  let prev = '';
  if (c.prev) { const p = SH.validate('search_sections', c.prev); if (p?.tool === 'search_sections') prev = JSON.stringify(p.args).slice(0, 400); }
  if (DRY === 'error') return { error: 'dry: no answer', ms: 1, usd: 0 };
  if (DRY) {
    let name = c.tool, args: any = concrete(c.args);
    if (name === 'watch' && !args.kind) args.kind = 'class';
    if (DRY === 'wrong') { if (name !== 'cant_answer') { name = 'cant_answer'; args = { reason: 'ambiguous' }; } else { name = 'help'; args = {}; } }
    return { picked: SH.validate(name, args), raw: { name, args }, ms: 1, usd: 0 };
  }
  try {
    const r: any = await SH.callVendor('anthropic', model, KEY, SH.routeSpec(client, TERM, c.q, prev), ctl.signal);
    return { picked: SH.validate(r.name, r.args), raw: { name: r.name, args: r.args }, ms: Date.now() - started, usd: SH.estimateUsd(model, r.usage) };
  } catch (e) {
    return { error: String(e instanceof Error ? e.message : e).slice(0, 160), ms: Date.now() - started, usd: 0 };
  } finally { clearTimeout(t); }
}
async function pool<T, R>(items: T[], n: number, fn: (x: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length); let i = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (i < items.length) { const k = i++; out[k] = await fn(items[k]); } }));
  return out;
}

const n = golden.cases.length;
const report: any = { at: new Date().toISOString(), cases: n, fingerprint: FP, runs: {}, verdict: {} };
const lines: string[] = [];
let failed = false;
const FLOOR = 0.80, MAX_ERR = 0.02;
const webCan = new Set(SH.TOOLS.map((x: any) => x.name));
const shared = new Set(golden.cases.map((c: any, i: number) => expectations(c).every((e) => webCan.has(e.tool)) ? i : -1).filter((i: number) => i >= 0));
for (const model of models) {
  const got: Record<string, number> = {}, gotShared: Record<string, number> = {}, errs: Record<string, number> = {};
  for (const [mname, client] of MENUS) {
    const key = `${model} · ${mname}`;
    console.log(`\n=== ${key} ===`);
    const res = await pool(golden.cases, 4, async (c: any) => ({ c, r: await one(model, client, c) }));
    let pass = 0, strict = 0, toolRight = 0, usd = 0, passShared = 0, errors = 0; const ms: number[] = []; const misses: any[] = [];
    const bycat: Record<string, [number, number]> = {};
    for (const [i, { c, r }] of (res as any[]).entries()) {
      if (r.error) errors++;
      usd += r.usd || 0; ms.push(r.ms);
      const first = matches(expectations(c)[0], r.picked, c.forbid);
      const ok = passes(c, r.picked);
      if (first !== null && first.length === 0) strict++;
      if (expectations(c).some((e) => r.picked && r.picked.tool === e.tool)) toolRight++;
      if (ok) pass++;
      if (ok && shared.has(i)) passShared++;
      bycat[c.cat] = bycat[c.cat] || [0, 0]; bycat[c.cat][1]++; if (ok) bycat[c.cat][0]++;
      if (!ok) misses.push({ cat: c.cat, q: c.q, want: expectations(c), got: r.error ? { error: r.error } : r.picked, raw: r.raw, wrong: first });
    }
    ms.sort((a, b) => a - b);
    got[client] = pass; gotShared[client] = passShared; errs[client] = errors;
    const s = { pass: +(pass / n).toFixed(3), passed: pass, strict: +(strict / n).toFixed(3), right_tool: +(toolRight / n).toFixed(3), usd: +usd.toFixed(3), p50_ms: ms[Math.floor(n / 2)], p90_ms: ms[Math.floor(n * 0.9)] };
    report.runs[key] = { ...s, bycat, misses };
    const line = `${key.padEnd(44)} ${pass}/${n} = ${(s.pass * 100).toFixed(1)}%  (old-tool questions ${passShared}/${shared.size})  right tool ${(s.right_tool * 100).toFixed(1)}%  errors ${errors}  $${s.usd}  p50 ${s.p50_ms}ms`;
    lines.push(line); console.log(line);
    console.log('  by category: ' + Object.entries(bycat).map(([k, [a, b]]) => `${k} ${a}/${b}`).join(' · '));
    misses.slice(0, 15).forEach((m) => console.log('  MISS', JSON.stringify(m.q), '→', JSON.stringify(m.got).slice(0, 120)));
    if (misses.length > 15) console.log(`  …and ${misses.length - 15} more in the results file`);
  }
  /* the gate */
  const why: string[] = [];
  const b = baseline?.app?.[model], rate = got.app / n;
  for (const [cl, e] of Object.entries(errs)) if (e > n * MAX_ERR) why.push(`${e} of ${n} calls on the ${cl} menu errored — this run measured nothing (check the key and the network)`);
  if (rate < FLOOR) why.push(`the phone menu passes ${(rate * 100).toFixed(1)}%, under the ${FLOOR * 100}% floor`);
  if (gotShared.web != null && gotShared.app < gotShared.web) why.push(`on the ${shared.size} questions the website menu can answer, the phone menu (${gotShared.app}) does worse than the website menu (${gotShared.web})`);
  if (b && rate < b.pass - 1 / n) why.push(`${(rate * 100).toFixed(1)}% is more than one question below the accepted ${(b.pass * 100).toFixed(1)}%`);
  const verdict = why.length ? 'FAIL — don\'t deploy ask: ' + why.join('; ') : `PASS${b ? ` (accepted ${(b.pass * 100).toFixed(1)}%)` : ' (no accepted baseline yet)'}`;
  if (why.length) failed = true;
  report.verdict[model] = verdict;
  lines.push(`${model}: ${verdict}`);
  if (!why.length && ACCEPT && !DRY && (!b || rate >= b.pass)) {
    baseline.app = baseline.app || {};
    baseline.app[model] = { passed: got.app, cases: n, pass: +rate.toFixed(4), fingerprint: FP, at: report.at };
  } else if (!why.length && ACCEPT && !DRY && b) {
    baseline.app[model] = { ...b, fingerprint: FP, at_last_pass: report.at };   // the menu that passed is this one; the bar stays where it was
  }
}
const file = new URL(`./model-results-v3-${new Date().toISOString().slice(0, 10)}${DRY ? '-dry' : ''}.json`, import.meta.url);
await Deno.writeTextFile(file, JSON.stringify(report, null, 1));
if (ACCEPT && !failed && !DRY) { await Deno.writeTextFile(baseFile, JSON.stringify(baseline, null, 1) + '\n'); console.log('\nAccepted: dev/golden/baseline.json updated.'); }
console.log('\nSide by side:\n  ' + lines.join('\n  '));
console.log('\nWrote ' + file.pathname + ' — tell Claude it finished; it can read the file from your Downloads.');
if (failed) Deno.exit(1);
