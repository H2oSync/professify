"""Signed out, My classes never stuck on "Loading your Fall 2026 classes…" (2026-10-14).

Found on PR #72's Deploy Preview: a signed-out visitor opening Schedule › My classes landed on the Fall 2026 chip (the
default when they have no Spring class) and saw "Loading your Fall 2026 classes…" forever — NOW_MINE is read from the
account, so with no account it never loads.
  - Signed out, My classes opens on the Spring 2027 chip (the list they build on this device); a remembered or one-off
    choice still wins.
  - If a signed-out visitor taps Fall 2026 anyway, it says "Sign in to see your Fall 2026 classes" with the same line
    about Spring, never a spinner.
Run after website-polish-2026-10-14.py (any later website patch is fine):  python3 <this> <repo>
"""
import sys, pathlib
f = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.') / 'index.html'; s = f.read_text()
def one(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:90]); s = s.replace(old, new)
one("""  return (typeof myClasses!=='undefined'&&myClasses.length)?'term':'now';
}""", """  if(typeof sbUser==='undefined'||!sbUser)return 'term';   /* signed out: Fall lives on an account, Spring on this device */
  return (typeof myClasses!=='undefined'&&myClasses.length)?'term':'now';
}""")
one("""  if(!codes.length){
    out.innerHTML=chips+'<div class="wl-empty"><h3>'+(N.loaded?""", """  if(!codes.length&&(typeof sbUser==='undefined'||!sbUser)){
    out.innerHTML=chips+'<div class="wl-empty"><h3>Sign in to see your '+lab+' classes</h3>'
      +'<p>'+lab+' is the term you’re in now, and it comes from your account. '+next+' is where you add classes — switch to it above.</p></div>';
    return;
  }
  if(!codes.length){
    out.innerHTML=chips+'<div class="wl-empty"><h3>'+(N.loaded?""")
f.write_text(s); print('website-signed-out-fall: applied')
