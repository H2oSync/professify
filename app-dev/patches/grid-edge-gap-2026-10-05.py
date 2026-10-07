#!/usr/bin/env python3
"""Week grids: the first class no longer touches the top of its day (Tate, 2026-10-05: "you see how the
first class touches the very top make it similar to how the last class doesnt fully touch").

The axis is rounded out to whole hours, so a class ending at 8:50 left air under it but a class starting
on the hour (8:00) sat flush against the top of the column. Every grid now keeps GPAD (6px) of air at
the top and the bottom of its body; blocks stay the same size (the gaps are added outside the hour scale, so a card is 12px taller), and the hour
labels move with the classes they line up with.

Usage: python3 grid-edge-gap-2026-10-05.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'GPAD' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

one("  const k = (H - folds.length * FOLD) / vis;\n",
    "  const k = (H - folds.length * FOLD) / vis;\n  /* 6px of air above the first hour and below the last on every day, so a class on the hour never sits\n     flush against the top (Tate, 2026-10-05). The gaps sit outside the hour scale: blocks keep their size\n     and the body is 12px taller than the hours it shows. */\n  const GPAD = 6;\n")
one('<div class="g-body" style="height:${H}px;${tmpl}">', '<div class="g-body" style="height:${H + 2 * GPAD}px;${tmpl}">')
one("const Y = m => { let y = (m - S0) * k;", "const Y = m => { let y = GPAD + (m - S0) * k;")
one("const fb = folds.find(([a]) => a >= s.e), lim = fb ? Y(fb[0]) : H;", "const fb = folds.find(([a]) => a >= s.e), lim = fb ? Y(fb[0]) : H + GPAD;")
f.write_text(s)
print('patched', f)
