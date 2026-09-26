/* Score candidate models on Hawk's REAL prompt and tools (imported from the function itself) against
   golden/model-golden.json, and print accuracy, cost and speed side by side.

   Run it in Terminal, from the termchamp-hawk-ai-2026-09-21 folder:

     export ASSISTANT_API_KEY='…'        # the same key you set as the Supabase secret. Type it
                                         # here, in your terminal, never in a chat.
     npx deno run --allow-net --allow-env --allow-read --allow-write golden/check-models.ts

   Optional: pass model ids to compare others, e.g.
     … golden/check-models.ts claude-fable-5-1 claude-haiku-4-5-20251001 claude-sonnet-5

   Cost: about $3–5 for Fable and $0.30 for Haiku per full run (108 questions each). */
import { SYSTEM, TOOLS, callVendor, validate, estimateUsd } from '../../supabase/functions/ask/shared.ts';

const KEY = Deno.env.get('ASSISTANT_API_KEY') || Deno.env.get('ANTHROPIC_API_KEY') || '';
if (!KEY) { console.error('Set ASSISTANT_API_KEY in this terminal first (see the top of this file).'); Deno.exit(1); }
const models = Deno.args.length ? Deno.args : ['claude-fable-5-1', 'claude-haiku-4-5-20251001'];
const golden = JSON.parse(await Deno.readTextFile(new URL('./model-golden.json', import.meta.url)));
const TERM = 'Spring 2027';
const NAMEISH = new Set(['friend', 'name', 'person', 'a', 'b']);

const lc = (v: unknown) => String(v ?? '').toLowerCase().trim();
function argOk(k: string, want: unknown, got: unknown): boolean {
  if (Array.isArray(want)) return Array.isArray(got) && want.length === got.length && want.every((w) => (got as unknown[]).includes(w));
  if (NAMEISH.has(k)) {
    const w = lc(want), g = lc(got);
    if (!g) return false;
    return k === 'friend' ? g.split(/\s+/)[0] === w.split(/\s+/)[0] : (g === w || g.includes(w) || w.includes(g));
  }
  if (typeof want === 'string') return lc(want) === lc(got);
  return want === got;
}

async function one(model: string, q: string) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 30000);
  const started = Date.now();
  try {
    const r: any = await callVendor('anthropic', model, KEY, { system: SYSTEM(TERM), tools: TOOLS, user: q }, ctl.signal);
    const picked = validate(r.name, r.args);
    return { picked, usage: r.usage, ms: Date.now() - started, usd: estimateUsd(model, r.usage) };
  } catch (e) {
    return { error: String(e instanceof Error ? e.message : e).slice(0, 160), ms: Date.now() - started, usd: 0 };
  } finally { clearTimeout(t); }
}

async function pool<T, R>(items: T[], n: number, fn: (x: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length); let i = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (i < items.length) { const k = i++; out[k] = await fn(items[k]); } }));
  return out;
}

const report: any = { at: new Date().toISOString(), models: {} };
for (const model of models) {
  console.log(`\n=== ${model} ===`);
  const res = await pool(golden.cases, 4, async (c: any) => ({ c, r: await one(model, c.q) }));
  let tool = 0, full = 0, usd = 0; const ms: number[] = []; const misses: any[] = [];
  for (const { c, r } of res as any[]) {
    usd += r.usd || 0; ms.push(r.ms);
    const got = r.picked;
    const toolOk = !!got && got.tool === c.tool;
    let gotArgs = { ...(got?.args || {}) };
    /* a/b are a pair: "compare X and Y" answered as (Y, X) is right. */
    if (toolOk && 'a' in (c.args || {}) && argOk('a', c.args.a, gotArgs.b) && argOk('b', c.args.b, gotArgs.a)) gotArgs = { ...gotArgs, a: gotArgs.b, b: gotArgs.a };
    const bad = toolOk ? Object.keys(c.args || {}).filter((k) => !argOk(k, c.args[k], (gotArgs as any)[k])) : [];
    if (toolOk) tool++;
    if (toolOk && !bad.length) full++;
    else misses.push({ q: c.q, want: { tool: c.tool, args: c.args }, got: r.error ? { error: r.error } : got, wrongArgs: bad });
  }
  ms.sort((a, b) => a - b);
  const n = golden.cases.length;
  const s = { cases: n, tool_accuracy: +(tool / n).toFixed(3), full_accuracy: +(full / n).toFixed(3), usd: +usd.toFixed(4),
              usd_per_1000_questions: +(usd / n * 1000).toFixed(2), p50_ms: ms[Math.floor(n / 2)], p90_ms: ms[Math.floor(n * 0.9)] };
  report.models[model] = { ...s, misses };
  console.log(JSON.stringify(s));
  misses.slice(0, 12).forEach((m) => console.log('  MISS', JSON.stringify(m.q), '→', JSON.stringify(m.got).slice(0, 140)));
  if (misses.length > 12) console.log(`  …and ${misses.length - 12} more in the results file`);
}
const file = new URL(`./model-results-${new Date().toISOString().slice(0, 10)}.json`, import.meta.url);
await Deno.writeTextFile(file, JSON.stringify(report, null, 1));
console.log('\nSide by side:');
for (const [m, s] of Object.entries(report.models) as any) console.log(`  ${m.padEnd(30)} tool ${(s.tool_accuracy * 100).toFixed(1)}%  exact ${(s.full_accuracy * 100).toFixed(1)}%  $${s.usd_per_1000_questions}/1k  p50 ${s.p50_ms}ms  p90 ${s.p90_ms}ms`);
console.log('\nWrote ' + file.pathname + ' — paste the "Side by side" lines back to Claude.');
