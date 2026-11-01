#!/usr/bin/env python3
"""2026-11-01 (after brand-i1): Tate: "we dont need the green hat" + "make sure it is consistent with the TC font we made".
The header wordmark is now drawn letter by letter the way the icon's T and C are (one stroke, rounded-rectangle bowls,
the same soft corners; /home/claude/lm/wm3.py), no cap, all brand blue. 700x144 PNGs, same sizes as before (36px header,
48px welcome, 36/32px website). Usage: <script> app/index.html [repo root]"""
import sys, re, base64, os
path = sys.argv[1]; root = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.dirname(os.path.abspath(path)))
D = os.path.join(root, 'design/app-icon/2026-11-01')
b64 = lambda f: base64.b64encode(open(os.path.join(D, f), 'rb').read()).decode()
def swap(s, pat, new):
    m = re.findall(pat, s); assert len(m) == 1, (pat, len(m))
    return re.sub(pat, lambda mm: mm.group(1) + new + mm.group(2), s)
s = open(path).read()
s = swap(s, r"(const TC_LOGO = 'data:image/png;base64,)[A-Za-z0-9+/=]+(', TC_LOGO_DARK = )", b64('termchamp-wm-light.png'))
s = swap(s, r"(TC_LOGO_DARK = 'data:image/png;base64,)[A-Za-z0-9+/=]+(')", b64('termchamp-wm-dark.png'))
open(path, 'w').write(s)
site = os.path.join(root, 'index.html')
if os.path.exists(site):
    w = open(site).read()
    w = swap(w, r'(<img class="brand-logo lg-l" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-light.png'))
    w = swap(w, r'(<img class="brand-logo lg-d" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-dark.png'))
    open(site, 'w').write(w)
print('brand-nohat: header wordmark redrawn in the icon style, no cap')
