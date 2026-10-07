#!/usr/bin/env python3
r"""Rate form: no "Your grade" (Tate, 2026-10-03, on a screenshot of the grade chips: "take grade out").

  · the "Your grade · Never shown with your name" row (A … F, P/CR) is gone from + Add detail;
  · a new review posts grade: null. A draft saved before this build comes back without its grade,
    so nothing the student can't see is posted;
  · editing an older review that has a grade keeps it as it was (the edit sends the grade it read),
    so taking the field away never wipes data. The desktop still asks for a grade.

Usage: python3 no-grade-2026-10-03.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

rep("   <div class=\"frow2\"><div class=\"row sb\" style=\"margin-bottom:10px\"><span class=\"flabel\">Your grade</span><span class=\"hint\">Never shown with your name</span></div>${sg('grade', GRADES, null, true)}</div>\n", "")
rep("const kept = draftLoad(pid); if (kept) { kept.stars = halfOf(kept.stars); kept.tags =",
    "const kept = draftLoad(pid); if (kept) { kept.stars = halfOf(kept.stars); kept.grade = null; kept.tags =")

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
