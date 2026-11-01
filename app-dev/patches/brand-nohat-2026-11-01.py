#!/usr/bin/env python3
"""2026-11-01 (after brand-i1): Tate: "we dont need the green hat"; then, of a fully redrawn version, "I dont like that",
picking the Rubik version without the cap; then "this is the font [the icon's TC] ... have them all same level":
the icon's exact T and C + Rubik 700 lowercase, one baseline and cap height (design/app-icon/2026-11-01/wordmark-builder.py).
809x144 PNGs. Without the cap the letters fill the image, so it is shown a little shorter to keep the word about the
same size: header 36 -> 32px (180px wide), welcome 48 -> 42px, website 36/32 -> 32/28px. Usage: <script> app/index.html [repo root]"""
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
def one(s, a, b):
    if s.count(b) == 1 and s.count(a) == 0: return s
    assert s.count(a) == 1, (a[:70], s.count(a)); return s.replace(a, b)
s = one(s, ".tc-logo-i{display:block;height:36px;", ".tc-logo-i{display:block;height:32px;")
s = one(s, "${tcLogo('', 36)}", "${tcLogo('', 32)}")
s = one(s, 'src="${TC_LOGO}" alt="" height="48" draggable="false" style="display:block;height:48px;', 'src="${TC_LOGO}" alt="" height="42" draggable="false" style="display:block;height:42px;')
open(path, 'w').write(s)
site = os.path.join(root, 'index.html')
if os.path.exists(site):
    w = open(site).read()
    w = swap(w, r'(<img class="brand-logo lg-l" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-light.png'))
    w = swap(w, r'(<img class="brand-logo lg-d" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-dark.png'))
    w = one(w, ".brand .brand-logo{display:block;height:36px;", ".brand .brand-logo{display:block;height:32px;")
    w = one(w, ".brand .brand-logo{height:32px}", ".brand .brand-logo{height:28px}")
    if w.count('alt="" height="36" draggable="false"') == 2: w = w.replace('alt="" height="36" draggable="false"', 'alt="" height="32" draggable="false"')
    open(site, 'w').write(w)
print('brand-nohat: icon T/C + Rubik lowercase, no cap, header 32px / welcome 42px / website 32-28px')
