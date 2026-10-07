#!/usr/bin/env python3
"""/s says "Plan A" when a plan is shared (2026-09-30, with share-week-2026-09-30.py).

A link from the phone's "Share Plan A" carries &pl=A. The preview's title becomes
"Look at Tate's Plan A" and the description "Their Fall 2026 Plan A, and whether yours line up."
Only A, B or C is accepted — anything else in pl is ignored and the preview reads exactly as before,
so every link already sent is unchanged.

Usage: python3 share-edge-plan-2026-09-30.py <repo-dir>   (edits <repo-dir>/netlify/edge-functions/share.ts)
"""
import sys, os
p = os.path.join(sys.argv[1], 'netlify', 'edge-functions', 'share.ts')
s = open(p, encoding='utf-8').read()
if 'const plan' in s: sys.exit('already patched')
R = [
 ('  const term= (url.searchParams.get("tm") ?? "").slice(0, 24);\n',
  '  const term= (url.searchParams.get("tm") ?? "").slice(0, 24);\n'
  '  /* A shared PLAN (the phone app, 2026-09-30) carries pl=A|B|C. Anything else is ignored. */\n'
  '  const plan = /^[ABC]$/.test(url.searchParams.get("pl") ?? "") ? (url.searchParams.get("pl") as string) : "";\n'),
 ('  const title = first ? `Look at ${first}\'s schedule this semester` : "Look at my schedule this semester";\n'
  '  const desc  = term\n'
  '    ? `Their ${term} classes, and whether yours line up.`\n'
  '    : "See their classes, and whether yours line up.";\n',
  '  const title = plan\n'
  '    ? (first ? `Look at ${first}\'s Plan ${plan}` : `Look at my Plan ${plan}`)\n'
  '    : (first ? `Look at ${first}\'s schedule this semester` : "Look at my schedule this semester");\n'
  '  const desc  = plan\n'
  '    ? (term ? `Their ${term} Plan ${plan}, and whether yours line up.` : `Their Plan ${plan}, and whether yours line up.`)\n'
  '    : term\n'
  '    ? `Their ${term} classes, and whether yours line up.`\n'
  '    : "See their classes, and whether yours line up.";\n'),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:70]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
