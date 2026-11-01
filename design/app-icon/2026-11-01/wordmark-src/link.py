"""Interlocked TC, drawn from scratch: the T's stem threads through the C like two chain links.
C over the stem at the top crossing, stem over the C at the bottom crossing."""
import math
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from letterman import cap, svg_icon, BLUE, NAVY

def to_d(shape):
    out = []
    for g in getattr(shape, 'geoms', [shape]):
        for ring in [g.exterior, *g.interiors]:
            out.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in ring.coords) + 'Z')
    return ''.join(out)

def soften(s, r):
    return s.buffer(-r, join_style='round', quad_segs=16).buffer(r, join_style='round', quad_segs=16) if r else s

def geometry(w=118, R=252, open_deg=44, offset=0.40, gap_bar=46, bar_w=500, r=16):
    cx, cy = 0.0, 0.0
    a0, a1 = math.radians(open_deg), math.radians(360 - open_deg)
    pts = [(cx + R*math.cos(a0 + (a1-a0)*i/240), cy + R*math.sin(a0 + (a1-a0)*i/240)) for i in range(241)]
    C = soften(LineString(pts).buffer(w/2, cap_style='flat', quad_segs=32), r)
    sx = cx - offset*R
    c_top = cy - R - w/2; c_bot = cy + R + w/2
    bar_bot = c_top - gap_bar; bar_top = bar_bot - w
    stem = box(sx - w/2, bar_top + 1, sx + w/2, c_bot)
    bar = box(sx - bar_w/2, bar_top, sx + bar_w/2, bar_bot)
    T = soften(unary_union([stem, bar]), r)
    stem_only = soften(stem, r)
    return dict(C=C, T=T, stem=stem_only, sx=sx, cy=cy, bar=(sx - bar_w/2, bar_top, sx + bar_w/2, bar_bot),
                box=(min(sx - bar_w/2, cx - R - w/2), bar_top, cx + R + w/2, c_bot), w=w)

def link_icon(bg=BLUE, fg='#FFFFFF', hat=False, fill=0.64, gap=26, uid='l', capw=0.80, **kw):
    G = geometry(**kw)
    X0, Y0, X1, Y1 = G['box']
    bx0, by0, bx1, by1 = G['bar']; B = (bx1 - bx0) * capw
    top = Y0 - (B*0.5 if hat else 0)
    k = min(fill*1024/(Y1 - top), 0.80*1024/(X1 - X0))
    ox = 512 - (X0 + X1)/2*k; oy = 512 - (top + Y1)/2*k
    big = 99999; cy = G['cy']
    import math as _m
    R_ = kw.get('R', 252); yc = -_m.sqrt(max(R_**2 - G['sx']**2, 0)); band = G['w']*0.95
    ring = f'stroke="{bg}" stroke-width="{2*gap}" stroke-linejoin="round" paint-order="stroke"'
    defs = (f'<clipPath id="u{uid}"><rect x="-{big}" y="-{big}" width="{2*big}" height="{big + yc + band:.1f}"/></clipPath>'
            f'<clipPath id="d{uid}"><rect x="-{big}" y="{-yc - band:.1f}" width="{2*big}" height="{big}"/></clipPath>')
    T, C, S = to_d(G['T']), to_d(G['C']), to_d(G['stem'])
    body = (f'<path d="{T}" fill="{fg}"/><path d="{C}" fill="{fg}"/>'
            f'<g clip-path="url(#u{uid})"><path d="{C}" fill="{fg}" {ring}/></g>'      # top crossing: C over the stem
            f'<g clip-path="url(#d{uid})"><path d="{S}" fill="{fg}" {ring}/></g>')     # bottom crossing: stem over the C                                 # bottom: stem over the C
    if hat:
        body += cap((bx0 + bx1)/2, by0 + 4, B)
    return (f'<defs>{defs}</defs><rect width="1024" height="1024" fill="{bg}"/>'
            f'<g transform="translate({ox:.1f} {oy:.1f}) scale({k:.4f})">{body}</g>')
