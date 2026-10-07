#!/usr/bin/env python3
r"""+ New group as plain pink text, no pill (Tate, 2026-10-04, on the 09:20 pill: "dont have new group
have a bubble around it just have it that color").

  · No background, no shadow: just "+ New group" in pink at the right end of the CHATS label.
  · #CC1F6C — Invite's #DB2777 darkened just enough to read on the page grey (4.54:1; Invite's pink is
    3.95:1 there, under the 4.5:1 text floor). The 44px tap area (::after) is unchanged.

Runs after groups-2026-10-03.py. Usage: python3 new-group-text-2026-10-04.py <repo-dir>.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
a = ".ngbtn{position:relative;display:inline-flex;align-items:center;gap:4px;min-height:32px;padding:0 12px 0 10px;border-radius:999px;background:var(--pink);color:#fff;font-weight:900;font-size:13.5px;letter-spacing:0;text-transform:none;box-shadow:0 3px 10px rgba(219,39,119,.22)}"
b = ("/* Plain pink text, no pill (2026-10-04). Invite's #DB2777 is 3.95:1 on the page grey; #CC1F6C reads as the same pink at 4.54:1. */\n"
     ".ngbtn{position:relative;display:inline-flex;align-items:center;gap:4px;min-height:32px;padding:0 4px;margin-right:-4px;background:none;color:#CC1F6C;font-weight:900;font-size:14px;letter-spacing:0;text-transform:none}")
n = s.count(a)
if n != 1: sys.exit(f'anchor matched {n}x')
open(p, 'w', encoding='utf-8').write(s.replace(a, b))
print('patched', p)
