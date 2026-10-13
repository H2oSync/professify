import sys
p=sys.argv[1] if len(sys.argv)>1 else 'repo/app/index.html'
s=open(p).read()
a="""    case 'my_professors': { const ps = [...new Set(personSecs('me').map(s => s.prof)"""
assert s.count(a)==1
s=s.replace(a,"""    case 'my_professors': { const ps = [...new Set((splitTerms() ? personSecs('me').concat(nowSecs('me')) : personSecs('me')).map(s => s.prof)""")
open(p,'w').write(s)
