/* The golden set's offline check — runs on every build, needs no key, costs nothing.
     deno run --allow-read --allow-env dev/golden/check-golden.ts

   1. Every question is well formed: a tool on the phone's menu, argument names that tool has.
   2. Every expected answer is REACHABLE: the function's own validator keeps it when the model gives it
      (a case the validator would throw away can never be passed, and would only look like a model miss).
   3. The scorer can fail: right answers score 100%, broken ones almost nothing.
   4. Coverage: about 300 questions, every phone tool asked about, the four new tools 15+ times each,
      Tate's own questions present.
   5. The gate: if a score was accepted (baseline.json) and the phone's prompt or menu has changed
      since, this FAILS — run check-models-v3.ts with the key and --accept before shipping `ask`.
      With no accepted score yet it says so loudly but does not fail. */
import * as SH from '../../supabase/functions/ask/shared.ts';
import { passes, expectations, concrete, fingerprint } from './score.ts';

let ok = 0, bad = 0;
const t = (name: string, cond: boolean, extra?: unknown) => { if (cond) { ok++; console.log('  ok  ' + name); } else { bad++; console.log('FAIL  ' + name, extra ?? ''); } };
const golden = JSON.parse(await Deno.readTextFile(new URL('./model-golden-v3.json', import.meta.url)));
const cases: any[] = golden.cases;
const menu = new Map(SH.APP_TOOLS.map((x: any) => [x.name, x]));

// 1. shape
const shapeBad: string[] = [];
for (const c of cases) {
  if (typeof c.q !== 'string' || !c.q.trim() || !c.cat) shapeBad.push('no q/cat: ' + JSON.stringify(c).slice(0, 60));
  for (const e of expectations(c)) {
    const tool: any = menu.get(e.tool);
    if (!tool) { shapeBad.push(`${c.q}: ${e.tool} is not on the phone menu`); continue; }
    for (const k of Object.keys(e.args || {})) if (!(k in (tool.parameters.properties || {}))) shapeBad.push(`${c.q}: ${e.tool} has no ${k}`);
  }
  for (const k of c.forbid || []) if (!(k in ((menu.get(c.tool) as any)?.parameters.properties || {}))) shapeBad.push(`${c.q}: forbid ${k} is not an argument of ${c.tool}`);
}
t('every question names a phone tool and only arguments it has', !shapeBad.length, shapeBad.slice(0, 8));
const qs = cases.map((c) => c.q.toLowerCase().trim());
t('no question appears twice', new Set(qs).size === qs.length, qs.filter((q, i) => qs.indexOf(q) !== i));

// 2. reachable
const unreach: string[] = [];
for (const c of cases) {
  for (const e of expectations(c)) {
    let args: any = concrete(e.args);
    if (e.tool === 'watch' && !args.kind) args.kind = 'class';
    const picked = SH.validate(e.tool, args);
    if (!passes({ ...c, tool: e.tool, args: e.args, alt: [] }, picked)) unreach.push(`${c.q} → ${e.tool} ${JSON.stringify(e.args)} validates to ${JSON.stringify(picked)}`);
  }
}
t('every expected answer survives the function\'s validator (it can be passed)', !unreach.length, unreach.slice(0, 8));

// 3. the scorer can fail
const wrong = cases.filter((c) => { const picked = c.tool !== 'cant_answer' ? SH.validate('cant_answer', { reason: 'ambiguous' }) : SH.validate('help', {}); return passes(c, picked); }).length;
t(`a broken model scores almost nothing (${wrong}/${cases.length})`, wrong / cases.length < 0.12, wrong);
const swapped = cases.filter((c) => c.tool === 'friends_free_now').filter((c) => passes(c, SH.validate('my_free', {}))).length;
t('“who\'s free” answered with my_free is a miss — the mix-up Tate hit', swapped === 0, swapped);
const ownProfs = cases.filter((c) => c.tool === 'best_professor').filter((c) => passes(c, SH.validate('my_professors', {}))).length;
t('“best professor for X” answered with my_professors is a miss', ownProfs === 0, ownProfs);

// 4. coverage
t(`about 300 questions (${cases.length})`, cases.length >= 300, cases.length);
const asked = new Set(cases.flatMap((c) => expectations(c).map((e) => e.tool)));
const never = [...menu.keys()].filter((n) => !asked.has(n));
t('every tool on the phone menu is asked about', !never.length, never);
for (const n of SH.APP_NEW_NAMES) t(`${n}: 15+ questions`, cases.filter((c) => c.tool === n).length >= 15, cases.filter((c) => c.tool === n).length);
const tate = ["Who's free right now?", 'When am I free Monday', 'Best professor for biz 3431', 'Does BUS 4401 fit my Plan A?'];
t('Tate\'s own questions are in it, with the right answers', tate.every((q) => cases.some((c) => c.q === q && c.from === 'tate')));

// 5. the gate
const FP = await fingerprint(SH.APP_SYSTEM('Fall 2026'), SH.APP_TOOLS, await Deno.readTextFile(new URL('../../supabase/functions/ask/shared.ts', import.meta.url)));
let base: any = null;
try { base = JSON.parse(await Deno.readTextFile(new URL('./baseline.json', import.meta.url))); } catch (_) { base = null; }
const accepted = base?.app ? Object.entries(base.app) as [string, any][] : [];
if (!accepted.length) {
  console.log(`\n  NOT SCORED YET — the phone menu (${FP}) has never been run against the model.`);
  console.log('  Before deploying `ask`: run dev/golden/check-models-v3.ts --accept with the key; it must say PASS.');
} else {
  for (const [m, b] of accepted) t(`${m}: the scored menu is the one in this build (${b.fingerprint} = ${FP})`, b.fingerprint === FP, 'the prompt or tools changed after the score was accepted — rerun check-models-v3.ts');
}
console.log(`\n${ok} ok, ${bad} fail`);
if (bad) Deno.exit(1);
