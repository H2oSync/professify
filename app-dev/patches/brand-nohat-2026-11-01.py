#!/usr/bin/env python3
"""2026-11-01 (after brand-i1): Tate: "we dont need the green hat"; then, of a fully redrawn version, "I dont like that",
picking the Rubik version without the cap; then "this is the font [the icon's TC] ... have them all same level":
then, of mixed letters, "the letters are inconsistent ... the spacing": the whole word in ONE font, Rubik 700 with
+0.02em tracking, brand blue (design/app-icon/2026-11-01/wordmark-builder.py). 886x144 PNGs, shown so the word keeps
its width: header 36 -> 30px (185px wide), welcome 48 -> 40px, website 36/32 -> 30/26px. Usage: <script> app/index.html [repo root]"""
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
s = one(s, ".tc-logo-i{display:block;height:36px;", ".tc-logo-i{display:block;height:30px;")
s = one(s, "${tcLogo('', 36)}", "${tcLogo('', 30)}")
s = one(s, 'src="${TC_LOGO}" alt="" height="48" draggable="false" style="display:block;height:48px;', 'src="${TC_LOGO}" alt="" height="40" draggable="false" style="display:block;height:40px;')
open(path, 'w').write(s)
site = os.path.join(root, 'index.html')
if os.path.exists(site):
    w = open(site).read()
    w = swap(w, r'(<img class="brand-logo lg-l" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-light.png'))
    w = swap(w, r'(<img class="brand-logo lg-d" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-dark.png'))
    w = one(w, ".brand .brand-logo{display:block;height:36px;", ".brand .brand-logo{display:block;height:30px;")
    w = one(w, ".brand .brand-logo{height:32px}", ".brand .brand-logo{height:26px}")
    if w.count('alt="" height="36" draggable="false"') == 2: w = w.replace('alt="" height="36" draggable="false"', 'alt="" height="30" draggable="false"')
    open(site, 'w').write(w)
print('brand-nohat: Rubik 700 wordmark, no cap, header 30px / welcome 40px / website 30-26px')
