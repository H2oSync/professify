#!/usr/bin/env python3
"""The little notification (the toast: "Removed from saved", "Request sent to …") was nearly invisible in dark
mode (Tate, 2026-10-11: "hard to see this little notification when you save a class make sure the case is fixed
for the future also i dont know how the light version looks").

Cause: #toast painted its background with var(--ink), the TEXT colour, and its words in #fff. In light mode --ink
is near-black, so it read; dark mode flips --ink to near-white, leaving white words on a pale grey pill (~1.2:1).

Fix: the toast has its own two tokens, never a text colour. Light: navy-black #0F172A with white words (unchanged
look). Dark: the opposite of the dark page — a near-white #E8EDF5 pill with #0F172A words and a shadow, so it
stands off the dark screen (and a hairline edge); while sign-up / log-in is showing — it stays light — the toast keeps
its light-mode colours; the Undo link turns #1D4ED8 there (#93C5FD stays in light). Every pairing is 4.5:1 or
better. The test that comes with it checks the toast and its Undo in both themes, and that no rule anywhere paints a
background from a text token (--ink…, --muted…) under white words again.

Usage: python3 toast-contrast-2026-10-11.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'toast-contrast (2026-10-11)' in s:
    sys.exit('already patched')
def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)
one("""transform:translate(-50%,-20px);background:var(--ink);color:#fff;font-weight:800;""", """transform:translate(-50%,-20px);background:var(--toast-bg,#0F172A);color:var(--toast-ink,#fff);box-shadow:0 8px 24px var(--toast-shadow,rgba(15,23,42,.18));font-weight:800;""")
one("""max-width:340px;text-align:center;box-shadow:0 10px 30px rgba(15,23,42,.3)}""", """max-width:340px;text-align:center;outline:1px solid var(--toast-edge,transparent)}""")
one("""#toast .tundo{border:0;background:none;color:#93C5FD;""", """#toast .tundo{border:0;background:none;color:var(--toast-link,#93C5FD);""")
one("""#toast.on{opacity:1;transform:translate(-50%,0)}""", """#toast.on{opacity:1;transform:translate(-50%,0)}
/* toast-contrast (2026-10-11): the toast's own colours — never a text token, which flips in dark mode */
:root{--toast-bg:#0F172A;--toast-ink:#FFFFFF;--toast-link:#93C5FD;--toast-shadow:rgba(15,23,42,.3);--toast-edge:transparent}
:root[data-theme="dark"]{--toast-bg:#E8EDF5;--toast-ink:#0F172A;--toast-link:#1D4ED8;--toast-shadow:rgba(0,0,0,.55);--toast-edge:rgba(15,23,42,.35)}
/* sign-up and log-in stay light in dark mode, so the toast does too while they're showing */
:root[data-theme="dark"]:has(.onb){--toast-bg:#0F172A;--toast-ink:#FFFFFF;--toast-link:#93C5FD;--toast-shadow:rgba(15,23,42,.3);--toast-edge:transparent}""")
f.write_text(s)
print('patched', f)
