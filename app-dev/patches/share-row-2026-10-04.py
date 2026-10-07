#!/usr/bin/env python3
r"""Schedule's bars: no class count; Share on the far right (Tate, 2026-10-04).

  My Classes, on "Fall 2026 · Share · 6 classes": "take the amount of classes away and put the share
  where that was to to the right more". Plans, on "4 classes · Share · Friends can see": "put friends
  can see on the far left where 4 classes is and move share to far right where friends can see is".

  · My Classes: the term on the left, Share alone on the right. The "N classes" pill is gone.
  · Plans: "Friends can see" / "Only you" on the left (in place of "N classes"), Share on the right.

Usage: python3 share-row-2026-10-04.py <repo-dir>. Every anchor must match exactly once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)

rep("<div class=\"regbar\"><span>${secs.length} class${secs.length === 1 ? '' : 'es'}</span><span class=\"rgt\"><button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"${S.plan}\" aria-label=\"Share Plan ${S.plan}\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button><span class=\"regbadge\" style=\"background:var(--bg);color:var(--muted)\">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span></span></div>",
    "<div class=\"regbar\"><span class=\"regbadge\" style=\"background:var(--bg);color:var(--muted)\">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span><button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"${S.plan}\" aria-label=\"Share Plan ${S.plan}\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>")
rep("<span class=\"rgt\"><button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"mine\" aria-label=\"Share your week\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button><span class=\"regbadge\">${Object.keys(byCode).length + unplaced.length} classes</span></span></div>",
    "<button class=\"shbtn\" data-a=\"shareOpen\" data-x=\"mine\" aria-label=\"Share your week\" ${TC.seatsLoaded ? '' : 'disabled'}>${ic('share', 15, 2.4)}Share</button></div>")

open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
