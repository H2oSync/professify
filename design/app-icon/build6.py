import json, re
from geo import *
CAPC=(('g2','#13533C'),('g1','#1D6B4B'),('gold','#F2B94E'))
cap=''.join('<path d="%s" fill="%s" stroke="%s" stroke-width="0.8" stroke-linejoin="round" fill-rule="evenodd"/>'%(CAP[k],c,c) for k,c in CAPC)
_n=[float(v) for k in CAP for v in re.findall(r'-?\d+\.?\d*',CAP[k])]
CAPX0,CAPY0=min(_n[0::2]),min(_n[1::2])
def place(t,c,target):
    # horizontal space between the T's right edge and the C's left edge
    lo,hi=-800,-300
    for _ in range(60):
        m=(lo+hi)/2
        if affinity.translate(c,m,0).bounds[0]-t.bounds[2]>target: hi=m
        else: lo=m
    return affinity.translate(c,hi,0)
def solve(t,c0,m_px,size=1024):
    # equal spacing: left margin = T-to-C gap = right margin = m_px
    s=1.9
    for _ in range(40):
        c=place(t,c0,m_px/s)
        x0=min(CAPX0,t.bounds[0]); x1=c.bounds[2]
        s=(size-2*m_px)/(x1-x0)
    return c,s,x0,x1
def svg(t,c,s,x0,size=1024,rounded=False,tile='#FFFFFF',tcol='#0D2E6E',ccol='#0B64FD'):
    y0=min(CAPY0,t.bounds[1]); y1=max(t.bounds[3],c.bounds[3])
    k=size/1024; S=s*k; m=(1024-(c.bounds[2]-x0)*s)/2*k
    tx=m-x0*S; ty=(size-(y1-y0)*S)/2-y0*S+size*0.01
    r=size*0.2237 if rounded else 0
    body='<path d="%s" fill="%s" fill-rule="evenodd"/><path d="%s" fill="%s" fill-rule="evenodd"/>%s'%(d(t),tcol,d(c),ccol,cap)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {0} {0}" width="{0}" height="{0}"><rect width="{0}" height="{0}" rx="{1:.1f}" fill="{2}"/>'
            '<g transform="translate({3:.2f} {4:.2f}) scale({5:.4f})">{6}</g></svg>').format(size,r,tile,tx,ty,S,body)
STEPS=[  # equal spacing in px at 1024, T bubble (step 1 -> step 2), C stays near the original
 dict(m=58,rt=33.0,stem=89.0,bar=77.0,rc=0,n=2,ring=80.0),
 dict(m=55,rt=31.5,stem=88.5,bar=76.5,rc=0,n=2,ring=80.0),
 dict(m=52,rt=30.0,stem=88.0,bar=76.0,rc=0,n=2,ring=80.0),
 dict(m=49,rt=28.5,stem=87.5,bar=75.5,rc=0,n=2,ring=80.0),
 dict(m=46,rt=27.0,stem=87.0,bar=75.0,rc=0,n=2,ring=80.0),
]
info=[]
for i,p in enumerate(STEPS,1):
    t=T(p['rt'],p['stem'],p['bar']); c,s,x0,x1=solve(t,C2(p['ring']),p['m'])
    open('e-%d-ios-1024.svg'%i,'w').write(svg(t,c,s,x0))
    open('e-%d-preview.svg'%i,'w').write(svg(t,c,s,x0,512,True))
    y0=min(CAPY0,t.bounds[1]); y1=max(t.bounds[3],c.bounds[3])
    info.append(dict(i=i,m=p['m'],gap=round((c.bounds[0]-t.bounds[2])*s,1),w=round((x1-x0)*s/10.24,1),h=round((y1-y0)*s/10.24,1)))
print(info); json.dump(info,open('e-info.json','w'))
