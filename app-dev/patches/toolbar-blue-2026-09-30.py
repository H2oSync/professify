#!/usr/bin/env python3
"""Tab bar: every tab turns the same blue as Home when selected (was blue / purple / orange / teal /
pink). Explore: the search magnifying glass is blue on Classes and purple on Professors.
(Tate, 2026-09-30: "make all the color for the toolbar when you click blue not dfferent colors same
color as the home tab. make this magnifying class blew when on classes and purple when on professors")

Usage: python3 toolbar-blue-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
Every anchor must match exactly once, or nothing is written. Touches only TABS and the Explore search
row, so it applies before or after the grid patches (focus-no-grow) in either order.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'class="sico"' in s: sys.exit('already patched')
R = [
 ("const TABS = [['home', 'Home', 'home', '#1D4ED8', '#E3ECFF'], ['explore', 'Explore', 'search', '#7C3AED', '#EFE7FF'], ['rate', 'Rate', 'star', '#D97706', '#FEF1DC'], ['schedule', 'Schedule', 'cal', '#0F766E', '#DDF5F1'], ['friends', 'Friends', 'users', '#DB2777', '#FCE4F0']];",
  "/* Every tab is Home's blue when selected (2026-09-30). */\n"
  "const TABS = [['home', 'Home', 'home', '#1D4ED8', '#E3ECFF'], ['explore', 'Explore', 'search', '#1D4ED8', '#E3ECFF'], ['rate', 'Rate', 'star', '#1D4ED8', '#E3ECFF'], ['schedule', 'Schedule', 'cal', '#1D4ED8', '#E3ECFF'], ['friends', 'Friends', 'users', '#1D4ED8', '#E3ECFF']];"),
 ("<label class=\"search\"><span style=\"color:var(--purple)\">${ic('search', 22, 2.4)}</span><input id=\"exq\"",
  "<label class=\"search\"><span class=\"sico\" style=\"color:var(--${S.exMode === 'profs' ? 'purple' : 'blue'})\">${ic('search', 22, 2.4)}</span><input id=\"exq\""),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
