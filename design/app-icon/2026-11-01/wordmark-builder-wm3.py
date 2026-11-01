"""Header wordmark, 2026-11-01 v3: every letter drawn the same way as the app icon's T and C
(monoline strokes, rounded-rectangle bowls, the same soft corners), so the whole word matches the icon."""
from shapely.geometry import box
from shapely.ops import unary_union
from shapely import affinity
from geo import tee, cee, rrect
from link import to_d, soften

CH = 800.0           # cap height (= the icon's T and C)
T_ = 190.0           # the icon's stroke
XH = 0.76 * CH       # x-height
TV = 168.0           # lowercase vertical stroke
TH = 136.0           # lowercase horizontal stroke (bowl tops/bottoms, arches)
DESC = 0.24 * CH
R_CORNER = 0.316     # soft corner radius as a share of the stroke (the icon uses 60 on 190)

def ring(x0, y0, x1, y1, rc, tv=TV, th=TH):
    """rounded-rect bowl with vertical sides tv and top/bottom th"""
    w = x1 - x0; R = rc * w
    outer = rrect(x0, y0, x1, y1, R)
    inner = rrect(x0 + tv, y0 + th, x1 - tv, y1 - th, max(R - (tv + th) / 2, 0.10 * w))
    return outer.difference(inner)

def arch(x0, x1, top, base, rc=0.5, tv=TV, th=TH):
    """an n: two legs and a rounded top"""
    w = x1 - x0; R = rc * w
    outer = rrect(x0, top, x1, base + R + 10, R).intersection(box(x0 - 1, top - 1, x1 + 1, base))
    inner = rrect(x0 + tv, top + th, x1 - tv, base + R + 10, max(R - (tv + th) / 2, 0.08 * w))
    return outer.difference(inner)

base = CH; top = CH - XH
def g_e(x):
    W = 0.80 * XH; mid = top + XH * 0.50
    s = ring(x, top, x + W, base, 0.48)
    s = s.union(box(x + TV * 0.5, mid - TH * 0.42, x + W - TV * 0.5, mid + TH * 0.42))
    s = s.difference(box(x + W * 0.55, mid + TH * 0.42 + 0.0, x + W + 1, base - TH * 1.05))   # the e's opening
    return s, W
def g_r(x):
    W = 0.52 * XH
    a = arch(x, x + W * 1.55, top, base, 0.55)
    a = a.intersection(box(x - 1, top - 1, x + W + 1, base + 1))
    a = a.difference(box(x + TV + 10, top + TH + 40, x + W + 2, base + 1))
    return a.union(box(x, top, x + TV, base)), W
def g_m(x):
    W1 = 0.70 * XH
    a = arch(x, x + W1, top, base).union(arch(x + W1 - TV, x + 2 * W1 - TV, top, base))
    return a, 2 * W1 - TV
def g_h(x):
    W = 0.74 * XH
    return arch(x, x + W, top, base).union(box(x, 0, x + TV, base)), W
def g_a(x):
    W = 0.78 * XH
    return ring(x, top, x + W, base, 0.48).union(box(x + W - TV, top + TH * 0.6, x + W, base)), W
def g_p(x):
    W = 0.78 * XH
    return ring(x, top, x + W, base, 0.48).union(box(x, top + TH * 0.6, x + TV, base + DESC)), W

GAP = 0.085 * CH
def build_shape():
    parts = []
    # T: the icon's T (bar 650 wide on 800), C: the icon's C (545 x 800)
    bw = 650.0; T = affinity.translate(tee(T_, CH, bw), bw / 2, 0); parts.append(T)
    stem_r = bw / 2 + T_ / 2
    x = stem_r + GAP * 0.9                       # the e tucks under the T's arm
    for g in (g_e, g_r, g_m):
        s, w = g(x); parts.append(s); x += w + GAP
    C = affinity.translate(cee(T_, 545.0, CH, 0.50, 0.30), x - GAP * 0.1, 0); parts.append(C); x += 545 + GAP
    for g in (g_h, g_a, g_m, g_p):
        s, w = g(x); parts.append(s); x += w + GAP
    out = []
    for i, p in enumerate(parts):
        stroke = T_ if i in (0, 4) else TH
        r = R_CORNER * stroke; f = r if i in (0, 4) else r * 0.45   # outer corners soft, inner joins lightly filleted
        p = soften(p, r).buffer(f, join_style='round').buffer(-f, join_style='round')
        out.append(p)
    return unary_union(out)

def svg(color, h=None, pad=0.04):
    s = build_shape(); x0, y0, x1, y1 = s.bounds
    p = pad * CH; vb = (x0 - p, y0 - p, x1 - x0 + 2 * p, y1 - y0 + 2 * p)
    hh = f' height="{h}" width="{h * vb[2] / vb[3]:.0f}"' if h else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}"{hh}>'
            f'<path d="{to_d(s)}" fill="{color}" fill-rule="evenodd"/></svg>'), vb
