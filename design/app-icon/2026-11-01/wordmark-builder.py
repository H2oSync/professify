"""Header wordmark v4 (2026-11-01): the icon's exact T and C (same proportions, stroke and corners as the app icon),
Rubik 700 lowercase, everything on one baseline and one cap height, all brand blue, no cap."""
from shapely.geometry import Polygon, box
from shapely import affinity
from txt import text
from rounder import _parse
from geo import tee, cee
from link import to_d, soften

F, W8, S = 'rubik', 700, 1000
def poly_of(d):
    shp = None
    for ring in _parse(d):
        if len(ring) < 3: continue
        p = Polygon(ring).buffer(0); shp = p if shp is None else shp.symmetric_difference(p)
    return shp

def build(color, gap=0.07):
    bH = text(F, W8, 'H', S, 0, 0, 0)[2]
    capH = bH[3] - bH[1]; base = 0.0; capTop = -capH          # Rubik baseline y=0, flat cap height
    k = capH / 800.0                                           # icon T/C are drawn on an 800 cap
    t = 190 * k
    T = affinity.scale(tee(190, 800, 650), k, k, origin=(0, 0)); T = affinity.translate(T, 325 * k, capTop)
    C = affinity.scale(cee(190, 545, 800, 0.50, 0.30), k, k, origin=(0, 0))
    r = 60 * k
    T = soften(T, r).buffer(r, join_style='round').buffer(-r, join_style='round')
    C = soften(C, r * 0.8)
    # lowercase runs from Rubik, spaced off the shapes' real edges
    erm = poly_of(text(F, W8, 'erm', S, 0, 0, 0)[0])
    hamp = poly_of(text(F, W8, 'hamp', S, 0, 0, 0)[0])
    g = gap * capH
    stem_r = 325 * k + t / 2                                  # the e tucks under the T's right arm
    erm = affinity.translate(erm, stem_r + g - erm.bounds[0], 0)
    C = affinity.translate(C, erm.bounds[2] + g * 1.15 - C.bounds[0], capTop)
    hamp = affinity.translate(hamp, C.bounds[2] + g - hamp.bounds[0], 0)
    shape = T.union(C).union(erm).union(hamp)
    return shape

def svg(color, H=144, pad=0.06):
    s = build(color); x0, y0, x1, y1 = s.bounds; capH = text(F, W8, 'H', S, 0, 0, 0)[2]; p = pad * (y1 - y0)
    vb = (x0 - p, y0 - p, x1 - x0 + 2 * p, y1 - y0 + 2 * p); W = round(H * vb[2] / vb[3])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" width="{W}" height="{H}">'
            f'<path d="{to_d(s)}" fill="{color}" fill-rule="evenodd"/></svg>'), W
