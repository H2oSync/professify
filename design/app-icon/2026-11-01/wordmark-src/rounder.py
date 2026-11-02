"""Round the corners of outlined glyph paths (morphological open/close with shapely)."""
import re
from shapely.geometry import Polygon
from shapely.ops import unary_union

def _parse(d):
    """SVG path (M L Q C Z, absolute, as fontTools SVGPathPen writes it) → list of point rings."""
    toks = re.findall(r'[MLHVQCZ]|-?\d*\.?\d+(?:e-?\d+)?', d)
    rings, ring, i, cur, cmd = [], [], 0, (0, 0), None
    def num():
        nonlocal i; v = float(toks[i]); i += 1; return v
    while i < len(toks):
        t = toks[i]
        if t in 'MLHVQCZ': cmd = t; i += 1
        if cmd == 'Z':
            if ring: rings.append(ring); ring = []
            continue
        if cmd == 'M':
            if ring: rings.append(ring)
            cur = (num(), num()); ring = [cur]; cmd = 'L'
        elif cmd == 'L':
            cur = (num(), num()); ring.append(cur)
        elif cmd == 'H':
            cur = (num(), cur[1]); ring.append(cur)
        elif cmd == 'V':
            cur = (cur[0], num()); ring.append(cur)
        elif cmd == 'Q':
            c = (num(), num()); e = (num(), num())
            for k in range(1, 13):
                u = k/12; ring.append(((1-u)**2*cur[0]+2*(1-u)*u*c[0]+u*u*e[0], (1-u)**2*cur[1]+2*(1-u)*u*c[1]+u*u*e[1]))
            cur = e
        elif cmd == 'C':
            c1 = (num(), num()); c2 = (num(), num()); e = (num(), num())
            for k in range(1, 17):
                u = k/16; a = (1-u)**3; b = 3*(1-u)**2*u; c = 3*(1-u)*u*u; dd = u**3
                ring.append((a*cur[0]+b*c1[0]+c*c2[0]+dd*e[0], a*cur[1]+b*c1[1]+c*c2[1]+dd*e[1]))
            cur = e
    if ring: rings.append(ring)
    return rings

def round_path(d, r_out, r_in=None, ys=1.0, y0=0.0):
    shape = None
    for ring in _parse(d):
        if len(ring) < 3: continue
        ring = [(x, y0 + (y - y0)*ys) for x, y in ring]
        p = Polygon(ring).buffer(0)
        shape = p if shape is None else shape.symmetric_difference(p)
    if r_out:
      shape = shape.buffer(-r_out, join_style='round', quad_segs=24).buffer(r_out, join_style='round', quad_segs=24)
    if r_in: shape = shape.buffer(r_in, join_style='round', quad_segs=24).buffer(-r_in, join_style='round', quad_segs=24)
    geoms = getattr(shape, 'geoms', [shape])
    out = []
    for g in geoms:
        for ring in [g.exterior, *g.interiors]:
            pts = list(ring.coords)
            out.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + 'Z')
    return ''.join(out)
