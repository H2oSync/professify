#!/usr/bin/env python3
"""2026-11-01: new brand. App header wordmark = icon's T and C + Rubik 700 lowercase, all brand blue (dark: #3B82FF),
green cap on the T. Sign-in logo = the new I1 app icon. Usage: brand-i1-2026-11-01.py app/index.html [repo root]"""
import sys, re, base64, os
path = sys.argv[1]; root = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.dirname(os.path.abspath(path)))
D = os.path.join(root, 'design/app-icon/2026-11-01')
b64 = lambda f: base64.b64encode(open(os.path.join(D, f), 'rb').read()).decode()
s = open(path).read()
def swap(pat, new):
    global s
    m = re.findall(pat, s); assert len(m) == 1, (pat, len(m))
    s = re.sub(pat, lambda mm: mm.group(1) + new + mm.group(2), s)
swap(r"(const TC_LOGO = 'data:image/png;base64,)[A-Za-z0-9+/=]+(', TC_LOGO_DARK = )", b64('termchamp-wm-light.png'))
swap(r"(TC_LOGO_DARK = 'data:image/png;base64,)[A-Za-z0-9+/=]+(')", b64('termchamp-wm-dark.png'))
swap(r"(const LOGO=')data:image/webp;base64,[A-Za-z0-9+/=]+(')", 'data:image/png;base64,' + b64('termchamp-icon-i1-rounded-168.png'))
open(path, 'w').write(s); print('brand-i1: header wordmark (light/dark) + sign-in logo replaced')

# --- the website (root index.html) wears the same identity: header logo (light/dark) and the narrow-window TC tile
site = os.path.join(root, 'index.html')
if os.path.exists(site) and os.path.abspath(site) != os.path.abspath(path):
    w = open(site).read()
    def swap_w(pat, new):
        global w
        m = re.findall(pat, w); assert len(m) == 1, (pat, len(m))
        w = re.sub(pat, lambda mm: mm.group(1) + new + mm.group(2), w)
    swap_w(r'(<img class="brand-logo lg-l" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-light.png'))
    swap_w(r'(<img class="brand-logo lg-d" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-wm-dark.png'))
    swap_w(r'(<img class="brand-tile" src="data:image/png;base64,)[A-Za-z0-9+/=]+(")', b64('termchamp-icon-i1-rounded-168.png'))
    open(site, 'w').write(w); print('brand-i1: website header logo + tile replaced')
