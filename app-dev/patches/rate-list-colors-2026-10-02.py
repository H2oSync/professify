#!/usr/bin/env python3
r"""Rate tab: the score you gave a professor is coloured like every other rating (Tate, 2026-10-02:
"stars should reflect their color so a 5 should be green like we had"). The rows under "N professors
waiting on your rating" kept the old amber star and brown number; they now use rateTone() — green
(≥ 4.125 of 5), amber, red — like the class and professor pages since rating-colors (09-30).

Usage: python3 rate-list-colors-2026-10-02.py <repo-dir>. The anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
a = "${r ? `<span class=\"rscore\">${starI(17, '#F59E0B')} ${(+r.score).toFixed(1)}</span>` : '<span class=\"pbtn\">Rate</span>'}"
b = "${r ? `<span class=\"rscore rt-${rateTone(+r.score).k}\" style=\"color:${rateTone(+r.score).ink}\">${starI(17, rateTone(+r.score).star)} ${(+r.score).toFixed(1)}</span>` : '<span class=\"pbtn\">Rate</span>'}"
if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x')
open(p, 'w', encoding='utf-8').write(s.replace(a, b))
print('patched', p)
