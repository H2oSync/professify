#!/usr/bin/env python3
"""share-ops (2026-10-16/17): a shared Plan lands on the website as "Sean's Plan A · Spring 2027".

The /s edge function (netlify/edge-functions/share.ts) now forwards tm and pl to the app. The website landing
(initSchedShare -> schedShareFrom -> renderSharedScheduleLanding) reads them, validates them again on this side
(pl in A|B|C; tm = Fall|Spring|Summer|Winter 20xx), and when pl is present the heading is "<First>'s Plan A · <term>"
(or "Plan A · <term>" for a link with no add=). A link with no pl reads exactly as before. The term in the link wins
over the term inside the stored week, because a Plan can belong to a term other than the build's own.
Edits index.html only. No build stamp (the coordinator stamps at merge).

Usage: python3 share-ops-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'share-ops (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# 1. read pl / tm out of the link, validated
one("""  var enc=null,nm='A friend',addId=null,imgId=null;
  try{ var q=new URLSearchParams(qs!=null?qs:location.search); enc=q.get('sched'); nm=q.get('nm')||'A friend';
       addId=q.get('add')||null; imgId=q.get('i')||null; }catch(e){ return; }""",
"""  var enc=null,nm='A friend',addId=null,imgId=null,plan='',tm='';
  try{ var q=new URLSearchParams(qs!=null?qs:location.search); enc=q.get('sched'); nm=q.get('nm')||'A friend';
       addId=q.get('add')||null; imgId=q.get('i')||null;
       /* share-ops (2026-10-16): a shared Plan carries pl=A|B|C and tm=<term>; anything else is ignored */
       var pl0=q.get('pl')||'', tm0=q.get('tm')||'';
       plan=/^[ABC]$/.test(pl0)?pl0:'';
       tm=/^(Fall|Spring|Summer|Winter) 20\\d\\d$/.test(tm0)?tm0:''; }catch(e){ return; }""")

# 2. pass them on
one("""        if(txt)schedShareFrom(String(txt).trim(),nm,addId);""",
    """        if(txt)schedShareFrom(String(txt).trim(),nm,addId,plan,tm);""")
one("""  if(!enc)return;
  schedShareFrom(enc,nm,addId);
}""", """  if(!enc)return;
  schedShareFrom(enc,nm,addId,plan,tm);
}""")
one("""function schedShareFrom(enc,nm,addId){
  if(!enc)return;""", """function schedShareFrom(enc,nm,addId,plan,tm){
  if(!enc)return;""")
one("""  renderSharedScheduleLanding(nm, data.cl, (addId&&UUID_RE.test(addId))?addId:null, data.term||'');""",
    """  renderSharedScheduleLanding(nm, data.cl, (addId&&UUID_RE.test(addId))?addId:null, tm||data.term||'', plan||'');""")

# 3. the landing heading
one("""function renderSharedScheduleLanding(nm, cl, addId, term){""",
    """function renderSharedScheduleLanding(nm, cl, addId, term, plan){""")
one("""  var termLabel=String(term||((typeof APP_TERM!=='undefined')?APP_TERM:'')||'').trim();""",
    """  var termLabel=String(term||((typeof APP_TERM!=='undefined')?APP_TERM:'')||'').trim();
  var planLetter=/^[ABC]$/.test(String(plan||''))?String(plan):'';   /* share-ops (2026-10-16) */""")
one("""    +'<h2 class="sl-h">'+(addId?(first+'’s '):'')+(termLabel?(escapeHtml(termLabel)+' '):'')+'schedule</h2>'""",
    """    +'<h2 class="sl-h">'+(planLetter
        ? ((addId?(first+'’s '):'')+'Plan '+planLetter+(termLabel?(' · '+escapeHtml(termLabel)):''))
        : ((addId?(first+'’s '):'')+(termLabel?(escapeHtml(termLabel)+' '):'')+'schedule'))+'</h2>'""")
s = s.replace("function initSchedShare(qs){", "/* share-ops (2026-10-16) */\nfunction initSchedShare(qs){", 1)
f.write_text(s)
print('share-ops patch applied')
