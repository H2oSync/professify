"""T and C drawn from scratch with ONE stroke thickness for every part (stem, bar, and all of the C)."""
from shapely.geometry import box
from shapely import affinity
from link import to_d, soften
from letterman import svg_icon, BLUE, NAVY

def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, join_style='round', quad_segs=48) if r > 0 else box(x0, y0, x1, y1)

def tee(t, H=800, bw=650):
    return box(-bw/2, 0, bw/2, t).union(box(-t/2, 0, t/2, H))

def cee(t, W=545, H=800, rc=0.42, gap=0.30, term=None):
    R = rc*W
    outer = rrect(0, 0, W, H, R); inner = rrect(t, t, W - t, H - t, max(R - t, 0.12*W))
    ring = outer.difference(inner)
    g0 = H*(0.5 - gap/2); g1 = H*(0.5 + gap/2)
    return ring.difference(box(W*0.5, g0, W + 1, g1))

def geo_icon(bg=BLUE, fg='#FFFFFF', t=190, bw=650, W=545, H=800, rc=0.42, gap=0.30, dx=0.90, dy=0.50,
             r=0.045, fil=1.0, fill=0.70, wfill=0.78):
    T = tee(t, H, bw); T = affinity.translate(T, bw/2, 0)
    C = cee(t, W, H, rc, gap)
    C = affinity.translate(C, bw*dx, H*dy)
    rr = r*H
    T = soften(T, rr).buffer(rr*fil, join_style='round').buffer(-rr*fil, join_style='round')
    C = soften(C, rr*0.8)
    shape = T.union(C)
    X0, Y0, X1, Y1 = shape.bounds
    k = min(fill*1024/(Y1-Y0), wfill*1024/(X1-X0))
    ox = 512 - (X0+X1)/2*k; oy = 512 - (Y0+Y1)/2*k
    return (f'<rect width="1024" height="1024" fill="{bg}"/><g transform="translate({ox:.1f} {oy:.1f}) scale({k:.4f})">'
            f'<path d="{to_d(shape)}" fill="{fg}" fill-rule="evenodd"/></g>')
