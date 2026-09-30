#!/usr/bin/env python3
"""The profile picture button only on Home (Tate, 2026-09-30).

"lets take out the profile from every page but home. so its reverted back to how the current term
champ is." Explore, Rate and Schedule go back to a plain page title, as on the live /app (main
978381b). Home keeps its button next to the bell; the profile page is still one tap from there.

Run from the repo root:  python3 app-dev/patches/profile-home-only-2026-09-30.py
Each anchor must match once. Running it again changes nothing.
"""
import sys, pathlib
P = pathlib.Path('app/index.html'); s = P.read_text()
if 'tc-titlerow' not in s and '(tap your picture anywhere)' not in s:
    print('already applied'); sys.exit(0)
def sub(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n} times: {a[:70]!r}')
    s = s.replace(a, b)
sub('.tc-titlerow{display:flex;align-items:center;justify-content:space-between;padding-right:16px}\n.tc-titlerow .me-btn{flex:none}\n', '')
sub('Your profile (tap your picture anywhere)', 'Your profile (tap your picture on Home)')
for t in ('Explore', 'Rate', 'Schedule'):
    a = f'<div class="tc-titlerow"><div class="title">{t}</div>${{meBtn()}}</div>'
    sub(a, f'<div class="title">{t}</div>')
P.write_text(s); print('applied')
