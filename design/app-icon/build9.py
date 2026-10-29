import json
from build6 import *
def place_min(t,c,target):
    lo,hi=-900,-300
    for _ in range(60):
        m=(lo+hi)/2
        if t.distance(affinity.translate(c,m,0))>target: hi=m
        else: lo=m
    return affinity.translate(c,hi,0)
def solve3(t,c0,side,touch,size=1024):
    s=1.9
    for _ in range(50):
        c=place_min(t,c0,touch/s); x0=min(CAPX0,t.bounds[0]); s=(size-2*side)/(c.bounds[2]-x0)
    return c,s,x0
SIDE=55; TOUCH=[44,36,28,20,12]
info=[]
for i,g in enumerate(TOUCH,1):
    t=T(30,88,76); c,s,x0=solve3(t,C2(80),SIDE,g)
    open('g-%d-ios-1024.svg'%i,'w').write(svg(t,c,s,x0)); open('g-%d-preview.svg'%i,'w').write(svg(t,c,s,x0,512,True))
    y0=min(CAPY0,t.bounds[1]); y1=max(t.bounds[3],c.bounds[3])
    info.append(dict(i=i,m=SIDE,gap=g,h=round((y1-y0)*s/10.24,1)))
print(info); json.dump(info,open('g-info.json','w'))
