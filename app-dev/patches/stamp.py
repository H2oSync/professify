#!/usr/bin/env python3
"""Set one build stamp everywhere it must agree: python3 stamp.py <repo-dir> "YYYY-MM-DD HH:MM"."""
import sys, os, re
d, st = sys.argv[1], sys.argv[2]
def sub(rel, pat, rep):
    p = os.path.join(d, rel); s = open(p, encoding='utf-8').read()
    s2, n = re.subn(pat, rep, s)
    if n != 1: sys.exit(f'{rel}: stamp matched {n}x')
    open(p, 'w', encoding='utf-8').write(s2)
sub('app/index.html', r"window\.TERMCHAMP_APP_BUILD = '[^']+'", f"window.TERMCHAMP_APP_BUILD = '{st}'")
sub('app/planner.js', r'window\.TERMCHAMP_PLANNER_BUILD = "[^"]+"', f'window.TERMCHAMP_PLANNER_BUILD = "{st}"')
sub('index.html', r"window\.PROFESSIFY_BUILD='[^']+'", f"window.PROFESSIFY_BUILD='{st}'")
sub('sw.js', r"const BUILD = '[^']+'", f"const BUILD = '{st}'")
print('stamped', st)
