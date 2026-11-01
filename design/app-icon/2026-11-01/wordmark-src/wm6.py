"""Header wordmark (2026-11-01): Rubik 700 + 0.02em spacing, with the T and C redrawn in the app icon's style
(soft-cornered T, rounded-rectangle C) at Rubik's own weight and size, so the word stays even; every corner a bit rounder."""
from shapely.geometry import Polygon, box
from shapely import affinity
from shapely.ops import unary_union
from txt import text
from rounder import _parse
from geo import rrect
from link import to_d, soften

F, W8, S, TR = 'rubik', 700, 1000, 0.02
def poly_of(d):
    shp = None
    for ring in _parse(d):
        if len(ring) < 3: continue
        p = Polygon(ring).buffer(0); shp = p if shp is None else shp.symmetric_difference(p)
    return shp
def adv(s): return text(F, W8, s, S, 0, 0, TR)[1] + TR * S if s else 0.0

def build(r=0.075, extra=0.0, round_lc=0.015):
    """Shape the whole word once (keeps Rubik's kerning), then swap in the app icon's exact T and C (I1 geometry,
    scaled to Rubik's cap height). The C is narrower than Rubik's, so 'hamp' moves left by the difference."""
    from geo import tee, cee
    d, _, _ = text(F, W8, 'TermChamp', S, 0, 0, TR)
    g = sorted(poly_of(d).geoms, key=lambda p: p.bounds[0])          # T e r m C h a m p
    bH = text(F, W8, 'H', S, 0, 0, 0)[2]; capH = bH[3] - bH[1]; k = capH / 800
    rr = (r + extra) * 800
    T = tee(190, 800, 650); T = soften(T, rr).buffer(rr, join_style='round').buffer(-rr, join_style='round')
    C = soften(cee(190, 545, 800, 0.50, 0.30), rr * 0.8)
    T = affinity.scale(T, k, k, origin=(0, 0)); C = affinity.scale(C, k, k, origin=(0, 0))
    tx0, _, tx1, _ = g[0].bounds; b = T.bounds
    T = affinity.translate(T, (tx0 + tx1) / 2 - (b[0] + b[2]) / 2, -capH - b[1])
    cx0, _, cx1, _ = g[4].bounds; b = C.bounds
    C = affinity.translate(C, cx0 - b[0], -capH - b[1])
    shift = (cx1 - cx0) - (b[2] - b[0])
    def soft(p, rl):
        rl *= capH
        return p.buffer(-rl, join_style='round', quad_segs=32).buffer(rl, join_style='round', quad_segs=32)
    rest = [soft(p, round_lc) for i, p in enumerate(g) if i not in (0, 4)]
    rest = rest[:3] + [affinity.translate(p, -shift, 0) for p in rest[3:]]
    return unary_union([T, C] + rest)

def svg(color, H=144, pad=0.06, **kw):
    s = build(**kw); x0, y0, x1, y1 = s.bounds; p = pad * (y1 - y0)
    vb = (x0 - p, y0 - p, x1 - x0 + 2 * p, y1 - y0 + 2 * p); W = round(H * vb[2] / vb[3])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" width="{W}" height="{H}">'
            f'<path d="{to_d(s)}" fill="{color}" fill-rule="evenodd"/></svg>'), W
