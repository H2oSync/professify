#!/usr/bin/env python3
"""Tate (2026-10-13), a screen recording of Schedule: "also fix this glitch in this video". Switching between My Classes,
Plans, Builder and Past classes opened the new tab at a stale scroll position (the one saved the last time you left the
Schedule tab, from whichever sub-tab you were on), so a tab could open half-way down with the Schedule title and its
top cut off, then jump. A sub-tab now always opens at its top, with the title shown. Replayable.
  python3 schedtab-top-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
a = """  schedTab: t => { if (t !== 'planner') UI.plFor = null; UI.pcTerms = false; S.schedTab = t; save(); render(); },"""
b = """  schedTab: t => { if (t !== 'planner') UI.plFor = null; UI.pcTerms = false; const e = cur(); if (e && t !== S.schedTab) e.y = 0; S.schedTab = t; save(); render(); },   /* a sub-tab opens at its top (2026-10-13) */"""
if s.count(a) != 1: sys.exit(f'schedtab-top: expected 1, found {s.count(a)}')
p.write_text(s.replace(a, b)); print('schedtab-top: applied')
