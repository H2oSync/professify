#!/usr/bin/env python3
"""Mutants for the 12px page width on Explore/Rate/Planner/Past/Friends. Usage: python3 page-width-home-mutants-2026-10-10.py app-dev/tests/mutate.mjs"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
M = [
 ("page width: Explore back to 16", 'body: `<div class="w12"><div class="title">Explore</div>', 'body: `<div><div class="title">Explore</div>'),
 ('page width: Rate lists back to 16', '<div class="card list" style="margin:0 12px">${t.items.map', '<div class="card list" style="margin:0 16px">${t.items.map'),
 ("page width: Friends back to 16", 'body: `<div class="w12"><div class="fhdr">', 'body: `<div><div class="fhdr">'),
 ("page width: Planner and Past back to 16", '`<div class="w12">${inner}</div>`', "inner"),
 ("page width: search and cards 16 again", ".w12 .search,.w12 .fsearch,.w12 .tc-sec,.w12 .pl-card,.w12 .pla-reg,.w12 .pl-picks,.w12 .pl-done,.w12 .pk-empty{margin-left:12px;margin-right:12px}", ".w12 .search,.w12 .fsearch,.w12 .tc-sec,.w12 .pl-card,.w12 .pla-reg,.w12 .pl-picks,.w12 .pl-done,.w12 .pk-empty{margin-left:16px;margin-right:16px}"),
 ("page width: the picks stay at 16", ".w12 .pla-reg,.w12 .pl-picks,.w12 .pl-done,.w12 .pk-empty{margin-left:12px", ".w12 .pla-reg,.w12 .pl-done,.w12 .pk-empty{margin-left:12px"),
 ("page width: chips and lists padded 16", ".w12 .pad,.w12 .frow,.w12 .hscroll{padding-left:12px;padding-right:12px}", ".w12 .pad,.w12 .frow,.w12 .hscroll{padding-left:16px;padding-right:16px}"),
 ("page width: titles pulled out to 12", ".w12 .term,.w12 .fs-h,.w12 .sec-h,.w12 .fs-note,.w12 .pk-note{padding-left:16px;padding-right:16px}", ".w12 .term,.w12 .fs-h,.w12 .sec-h,.w12 .fs-note,.w12 .pk-note{padding-left:12px;padding-right:12px}"),
]
i = s.index('];\n', s.index('const M = [')) if 0 else None
anchor = '  ["friend strip: green again"'
k = s.index(anchor); e = s.index('\n', k)
add = ''.join('  [%s, %s, %s, "pageWidthHome"],\n' % tuple(__import__('json').dumps(x) for x in m) for m in M)
s = s[:e+1] + add + s[e+1:]
open(p, 'w', encoding='utf-8').write(s)
