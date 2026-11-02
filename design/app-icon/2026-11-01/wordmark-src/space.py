import numpy as np, wm6
from txt import text
from shapely.geometry import LineString
def glyphs(s): return sorted(s.geoms, key=lambda p: p.bounds[0])
def edge(g, y, side):
    l = LineString([(g.bounds[0]-10, y), (g.bounds[2]+10, y)]).intersection(g)
    if l.is_empty: return None
    xs = [c[0] for c in (l.coords if l.geom_type=='LineString' else [p for gg in l.geoms for p in gg.coords])]
    return max(xs) if side=='R' else min(xs)
def optical(a, b, y0, y1, D, n=60):
    gs=[]; mx=a.bounds[2]; mn=b.bounds[0]
    for y in np.linspace(y0, y1, n):
        ra = edge(a, y, 'R'); lb = edge(b, y, 'L')
        ra = mx - D if ra is None else max(ra, mx - D)
        lb = mn + D if lb is None else min(lb, mn + D)
        gs.append(lb - ra)
    return np.mean(gs), mn - mx
def report(s, label, xh=530, D=None):
    g = glyphs(s); D = D or 0.18*700
    names='TermChamp'; out=[]
    for i in range(len(g)-1):
        o, raw = optical(g[i], g[i+1], -xh+5, -5, D)
        out.append((names[i]+names[i+1], round(o), round(raw)))
    print(label, out); return out
if __name__=='__main__':
    d,_,_=text('rubik',700,'TermChamp',1000,0,0,0.02)
    report(wm6.poly_of(d), 'rubik')
    report(wm6.build(), 'A    ')
