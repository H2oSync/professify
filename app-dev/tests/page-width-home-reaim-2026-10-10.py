#!/usr/bin/env python3
"""mutate.mjs: two older mutants named markup that build 08:30's page-width patch changed (that build's own mutate.mjs
was older than 23:30's, so it never saw them). Same promise, same test, new anchor. Replayable.
  python3 page-width-home-reaim-2026-10-10.py"""
import os, sys
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mutate.mjs')
s = open(P, encoding='utf-8').read()
for old, new in [
    (r'''  ["schedule width: no Home-width wrapper", "${t === 'planner' || t === 'past' ? inner : `<div class=\"schpg\">${inner}</div>`}", "${inner}", "homeWidth"],''',
     r'''  ["schedule width: no Home-width wrapper", ": `<div class=\"schpg\">${inner}</div>`}", ": inner}", "homeWidth"],'''),
    (r'''  ['profile button back on Explore', "body: `<div class=\"title\">Explore</div>", "body: `<div class=\"title\">Explore</div>${meBtn()}", 'profileHomeOnly'],''',
     r'''  ['profile button back on Explore', "body: `<div class=\"w12\"><div class=\"title\">Explore</div>", "body: `<div class=\"w12\"><div class=\"title\">Explore</div>${meBtn()}", 'profileHomeOnly'],'''),
]:
    if old in s: s = s.replace(old, new)
    elif new not in s: sys.exit('page-width-home-reaim: missing ' + old[:60])
open(P, 'w', encoding='utf-8').write(s)
print('page-width-home-reaim: done')
