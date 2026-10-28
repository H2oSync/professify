import json, numpy as np
from shapely.geometry import box, Polygon, Point
from shapely.ops import unary_union
from shapely import affinity
P=json.load(open('paths.json')); CAP=P['cap']
def sq(cx,cy,a,b,n,N=720):
    t=np.linspace(0,2*np.pi,N,endpoint=False); c,s=np.cos(t),np.sin(t)
    return Polygon(np.c_[cx+a*np.sign(c)*np.abs(c)**(2/n), cy+b*np.sign(s)*np.abs(s)**(2/n)])
def rnd(g,r,rc=8):
    g=g.buffer(-r,quad_segs=32).buffer(r,quad_segs=32) if r>0 else g
    return g.buffer(rc,quad_segs=16).buffer(-rc,quad_segs=16) if rc>0 else g
def T(r=39, stem=91, bar=78):
    cx=265.75; top=225
    g=unary_union([box(146,top,397,top+bar), box(cx-stem/2,top,cx+stem/2,488)])
    return rnd(g,min(r,bar/2-0.6))
def C(r=30, n=2.0, ring=80, slot=(333,394)):
    cx,cy,R=1071,362,126
    outer=sq(cx,cy,R,R,n); inner=sq(cx,cy+2,R-ring,R-ring,n)
    g=outer.difference(inner).difference(box(cx,slot[0],1300,slot[1])).difference(box(1164,0,1400,800))
    return rnd(g,r)
def d(g):
    out=[]
    for poly in getattr(g,'geoms',[g]):
        for ring in [poly.exterior,*poly.interiors]:
            xs,ys=ring.xy; out.append('M'+' L'.join('%.1f,%.1f'%(x,y) for x,y in zip(xs,ys))+'Z')
    return ' '.join(out)
from shapely.geometry import LineString
def C2(ring=80, phi=55, R=126, cx=1071, cy=362, n=2.0):
    # a bubbly C: a thick arc with fully round ends, like the original's terminals
    Rm=R-ring/2; a=np.radians(np.linspace(phi,360-phi,400))
    c,s=np.cos(a),np.sin(a)
    pts=np.c_[cx+Rm*np.sign(c)*np.abs(c)**(2/n), cy-Rm*np.sign(s)*np.abs(s)**(2/n)]
    return LineString(pts).buffer(ring/2,quad_segs=48,cap_style='round')
