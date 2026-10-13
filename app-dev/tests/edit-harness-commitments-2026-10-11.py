#!/usr/bin/env python3
"""The harness answers the Builder's "Before we build your plans" (work & activities, 2026-10-11) for every test,
as a student who already did; tests of that question pass cmAsked: false. Usage: python3 <this> <repo-dir>"""
import sys, os
P = os.path.join(sys.argv[1], 'app-dev', 'tests', 'app-harness.mjs'); S = open(P, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep("ask = null, hook = null, champ = true, path:", "ask = null, hook = null, champ = true, cmAsked = true, path:", 'param')
rep("  if (champ) await ctx.addInitScript(", "  if (cmAsked) await ctx.addInitScript(id => { try { localStorage.setItem('tc-commits-asked:' + id, '1'); } catch (e) {} }, FX.ME.id);\n  if (champ) await ctx.addInitScript(", 'init')
open(P, 'w', encoding='utf-8').write(S); print('edit-harness-commitments: done')
