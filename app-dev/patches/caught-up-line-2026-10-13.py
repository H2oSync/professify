#!/usr/bin/env python3
"""Tate (2026-10-13), on the report's "all caught up" note: "take out the little -- between up and every". Replayable.
  python3 caught-up-line-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
a = 'You’re all caught up — every class on this report is already in TermChamp.'
b = 'You’re all caught up. Every class on this report is already in TermChamp.'
if s.count(a) != 1: sys.exit(f'caught-up-line: expected 1, found {s.count(a)}')
p.write_text(s.replace(a, b)); print('caught-up-line: applied')
