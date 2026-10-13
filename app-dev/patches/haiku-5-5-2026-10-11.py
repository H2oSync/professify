#!/usr/bin/env python3
"""Champ on Claude Haiku 5.5 (Tate, 2026-10-11: "theres a new model … haiku 5.5 thats way cheaper to run lets
make sure Champ runs on this"). Edits supabase/functions/ask/shared.ts, dev/golden/check-models-v3.ts and
dev/tests/check-ask-function.ts. The model itself is picked by assistant_config (an UPDATE Tate runs after the
gate passes); this makes the function send Haiku 5.5 a request it accepts and count its cost right.

From platform.claude.com (read 2026-10-11):
  • model id `claude-haiku-5-5`; $0.10 in / $0.50 out / $0.01 cache read per million tokens for prompts up to
    100K tokens (ours are a few thousand), $0.125 cache write (1.25× input, as the code already counts).
  • thinking: "Adaptive only", default ON; `disabled` is accepted at effort high or below (default effort is
    medium). Thinking off keeps a router call short and lets the tool be FORCED, as on Haiku 4.5.
  • temperature with Claude 5 has been refused before (2026-09-24, Fable); it is left out — the forced tool and
    the validator are what keep answers in shape, not temperature.
"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def patch(rel, reps):
    p = ROOT / rel; s = p.read_text()
    for a, b in reps:
        c = s.count(a)
        if c != 1: sys.exit(f'haiku-5-5: {rel}: expected 1 of {a[:80]!r}, found {c}')
        s = s.replace(a, b)
    p.write_text(s)

patch('supabase/functions/ask/shared.ts', [
("""   The two are told apart by name.""",
"""   Haiku 5.5 (2026-10-11) is a third shape: adaptive by default like the Claude 5 models, but it
   ACCEPTS `thinking: {type: 'disabled'}` at its default effort. Off, it is a plain fast router again,
   so the tool is forced as on Haiku 4.5. Temperature is left out: a Claude 5 model has refused it
   before, and the forced tool plus validate() are what keep the answer in shape.

   The two are told apart by name."""),
("""  const adaptive = /fable|mythos|opus-5|sonnet-5/.test(model);""",
 """  const adaptive = /fable|mythos|opus-5|sonnet-5/.test(model);
  const noThink = /haiku-5/.test(model);"""),
("""  return { ...shared, temperature: 0,
           tool_choice: spec.force ? { type: 'tool', name: spec.force } : { type: 'any' } };""",
 """  const forced = spec.force ? { type: 'tool', name: spec.force } : { type: 'any' };
  if (noThink) return { ...shared, thinking: { type: 'disabled' }, tool_choice: forced };
  return { ...shared, temperature: 0, tool_choice: forced };"""),
("""  'claude-haiku-4-5-20251001': [1.00, 0.10, 5.00],""",
 """  'claude-opus-5-5':           [4.00, 0.20, 20.00],
  'claude-sonnet-5-5':         [2.00, 0.10, 10.00],
  'claude-haiku-5-5':          [0.10, 0.01, 0.50],     // prompts up to 100K tokens (2026-10-11); ours are far under
  'claude-haiku-4-5-20251001': [1.00, 0.10, 5.00],"""),
])

patch('dev/golden/check-models-v3.ts', [
("""   Default model: claude-haiku-4-5-20251001, the one serving students (about $0.60 for both menus).
   Name others to compare:  … check-models-v3.ts claude-haiku-4-5-20251001 claude-fable-5-1  (Fable ≈ $15 more)""",
 """   Default model: claude-haiku-5-5 (2026-10-11; about $0.06 for both menus). Haiku 4.5 served students
   before it; to compare the two:  … check-models-v3.ts claude-haiku-5-5 claude-haiku-4-5-20251001  (≈ $0.60 more)"""),
("""if (!models.length) models.push('claude-haiku-4-5-20251001');""",
 """if (!models.length) models.push('claude-haiku-5-5');"""),
])

patch('dev/tests/check-ask-function.ts', [
("""t('explain forces the explain tool on haiku', lastVendorBody.tool_choice.name === 'explain');""",
 """t('explain forces the explain tool on haiku', lastVendorBody.tool_choice.name === 'explain');
{ /* Haiku 5.5 (2026-10-11): thinking off, tool forced, no temperature; priced at its own rate */
  const SH: any = await import('../../supabase/functions/ask/shared.ts');
  const b = SH.anthropicBody('claude-haiku-5-5', { system: 's', tools: [{ name: 'x', description: 'd', parameters: { type: 'object', properties: {} } }], user: 'u' });
  t('haiku 5.5: thinking off, tool forced, no temperature, no effort', b.thinking?.type === 'disabled' && b.tool_choice?.type === 'any' && !('temperature' in b) && !b.output_config);
  const e = SH.anthropicBody('claude-haiku-5-5', { system: 's', tools: [], user: 'u', force: 'explain' });
  t('haiku 5.5: explain is forced by name', e.tool_choice?.type === 'tool' && e.tool_choice?.name === 'explain' && e.thinking?.type === 'disabled');
  const h45 = SH.anthropicBody('claude-haiku-4-5-20251001', { system: 's', tools: [], user: 'u' });
  t('haiku 4.5 unchanged: temperature 0, forced, no thinking field', h45.temperature === 0 && h45.tool_choice?.type === 'any' && !('thinking' in h45));
  const f = SH.anthropicBody('claude-sonnet-5-5', { system: 's', tools: [], user: 'u' });
  t('sonnet 5.5 stays adaptive (not the haiku-5 shape)', f.thinking?.type === 'adaptive' && f.tool_choice?.type === 'auto');
  const usd = SH.estimateUsd('claude-haiku-5-5', { in: 1_000_000, cached: 0, out: 1_000_000 });
  t('haiku 5.5 is priced at $0.10 in / $0.50 out per million', Math.abs(usd - 0.60) < 1e-9, usd);
  t('haiku 5.5 cache reads at $0.01 per million', Math.abs(SH.estimateUsd('claude-haiku-5-5', { in: 1_000_000, cached: 1_000_000, out: 0 }) - 0.01) < 1e-9);
}"""),
])
print('haiku-5-5-2026-10-11: ok')
