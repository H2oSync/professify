#!/usr/bin/env python3
"""My Classes: Anytime right under the week, the day cards under it — like Plans (Tate, 2026-10-11: "bring the anytime up
right under the schedule because then the days like Monday wed need to be under anytime classes plans does this right").
Usage: python3 mine-anytime-up-2026-10-11.py <repo-dir>   (replayable on build 19:05)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
a = "  return week + agenda + anyCard;\n"
if S.count(a) != 1: sys.exit(f'order: anchor matched {S.count(a)}x')
S = S.replace(a, "  /* Anytime under the week, then the days — Plans' order (Tate, 2026-10-11) */\n  return week + anyCard + agenda;\n")
open(PA, 'w', encoding='utf-8').write(S); print('mine-anytime-up: done')
