#!/usr/bin/env python3
"""Until the contacts SQL is on the server, sign-up skips the phone step instead of
asking for a number it can't save (TC.phoneSaved === null means the RPC is missing)."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""    UI.pl = null; onbGo('phone');
  },""", """    UI.pl = null; let off = TC.phoneSaved === null;
    if (TC.phoneSaved === undefined) { try { const r0 = await TC.client().rpc('my_phone_saved'); off = !!(r0 && r0.error && ctMissing(r0.error)); } catch (x) {} }
    onbGo(off ? 'people' : 'phone');
  },""")
p.write_text(s); print('onb-phone-skip-when-off applied')
