#!/usr/bin/env python3
"""chat-links (2026-10-16), index.html only. Two small website fixes.

1. Chat: http(s) links in a message bubble are clickable. Only http: and https: (never javascript:, data:, ...), everything
   escaped, the href is URL.href from `new URL()`, displayed text is the escaped URL (non-ASCII URLs show the punycode href so a
   lookalike host cannot pass for another), target=_blank rel="noopener noreferrer nofollow ugc", trailing . , ) ! ? ; : not part
   of the link (a ")" closing a "(" inside the URL is kept), long URLs shown cut with an ellipsis, a linear scan with no
   backtracking and at most 10 links per message, links with user:pass@ or a dotless host stay plain text. A schedule link is still
   a card first (msgSchedOf runs before this); chat-list previews are untouched (plain text). A termchamp.com/?p=<professor> or
   /?c=<class> link opens in the same tab through the site's own deep-link router (dlFindProf/openProf, dlOpenClass).
2. Rate page on a phone: Back closes the review bottom sheet before it leaves the page. The sheet pushes one history entry when it
   opens; popstate closes it; closing it any other way takes that entry back off (history.back(), swallowed by the nav handler),
   or, if the page navigates in the same breath, the next navPush replaces the entry instead of stacking on it.
Usage: python3 chat-links-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'chat-links (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---------------------------------------------------------------------------------------------- 1. links in a chat bubble
one(""".msg-note{margin-top:5px;font-size:12.5px;color:var(--muted);padding:0 3px}
""", """.msg-note{margin-top:5px;font-size:12.5px;color:var(--muted);padding:0 3px}
/* chat-links (2026-10-16): a link in a bubble takes the bubble's own text color */
.msg-b a.msg-link{color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px;overflow-wrap:anywhere}
.msg-b a.msg-link:hover{text-decoration-thickness:2px}
.msg-b a.msg-link:focus-visible{outline:2px solid currentColor;outline-offset:2px;border-radius:3px}
""")

one("""/* ---- rendering ------------------------------------------------------------------------------- */
function msgBodyHtml(t,m){""", r"""/* ---- links in a message (chat-links, 2026-10-16) ---------------------------------------------------
   The text of a bubble is written by whoever is in the chat, so it is untrusted. Everything is escaped; the only markup made
   here is the <a>, built from URL.href of an http: or https: URL that `new URL()` accepted. One pass over the text with a
   character-class regex (no nested quantifiers: linear), at most MSG_LINK_TRY candidates and MSG_LINK_MAX links per message. */
var MSG_LINK_MAX=10, MSG_LINK_TRY=20, MSG_LINK_SHOW=56;
var MSG_URL_RE=/https?:\/\/[^\s<>"'`\u0000-\u001f\u007f-\u009f\u200b-\u200f\u2028-\u202f\u2060-\u2069\ufeff]+/gi;
function msgLinkHtml(text){
  text=String(text==null?'':text);
  if(text.indexOf('//')<0)return msgEsc(text);
  var re=new RegExp(MSG_URL_RE.source,'gi'), out='', last=0, links=0, tries=0, hit;
  while(links<MSG_LINK_MAX&&tries<MSG_LINK_TRY&&(hit=re.exec(text))){
    tries++;
    var raw=hit[0], at=hit.index, end=raw.length, o=0, c=0, i;
    /* "...see https://x.com/a." / "(https://x.com/a)" / "https://x.com/a!" - the punctuation after a link is not part of it;
       a ")" that closes a "(" inside the URL is (en.wikipedia.org/wiki/Foo_(bar)). One count, then trim from the end. */
    for(i=0;i<end;i++){ var ch=raw.charCodeAt(i); if(ch===40)o++; else if(ch===41)c++; }
    while(end>0){
      var l=raw.charAt(end-1);
      if(l==='.'||l===','||l==='!'||l==='?'||l===';'||l===':')end--;
      else if(l===')'&&c>o){ c--; end--; }
      else break;
    }
    var url=raw.slice(0,end), u=null;
    if(url.length<=url.indexOf('//')+2)continue;
    try{ u=new URL(url); }catch(e){ continue; }
    if(u.protocol!=='http:'&&u.protocol!=='https:')continue;
    if(u.username||u.password||u.hostname.indexOf('.')<1||u.hostname.slice(-1)==='.')continue;
    var shown=/^[\x21-\x7e]+$/.test(url)?url:u.href;     /* a non-ASCII address is shown as the browser will really send it */
    var cut=shown.length>MSG_LINK_SHOW;
    if(cut)shown=shown.slice(0,MSG_LINK_SHOW-1)+'…';
    /* a professor or class link to this site opens inside it (click handler below); every other link opens in a new tab */
    var site=null;
    try{
      if(u.protocol==='https:'&&msgSchedHostOk(u.host)&&(u.pathname==='/'||u.pathname==='')&&!u.hash){
        var keys=[]; u.searchParams.forEach(function(v,k){ keys.push(k); });
        if(keys.length===1&&keys[0]==='p'){ var pv=u.searchParams.get('p')||''; if(pv&&pv.length<=120&&!/[\u0000-\u001f\u007f]/.test(pv))site=['p',pv]; }
        else if(keys.length===1&&keys[0]==='c'){ var cv=(u.searchParams.get('c')||'').trim(); if(/^[A-Za-z]{2,6}[ \-]?\d{2,4}[A-Za-z]?$/.test(cv))site=['c',cv]; }
      }
    }catch(e){ site=null; }
    out+=msgEsc(text.slice(last,at))
      +'<a class="msg-link" href="'+msgEsc(u.href)+'"'+(site?(' data-site="'+site[0]+'" data-v="'+msgEsc(site[1])+'"'):' target="_blank"')
      +' rel="noopener noreferrer nofollow ugc"'+(cut?(' title="'+msgEsc(u.href.slice(0,300))+'"'):'')+'>'+msgEsc(shown)+'</a>';
    last=at+end; links++;
  }
  return out+msgEsc(text.slice(last));
}

/* ---- rendering ------------------------------------------------------------------------------- */
function msgBodyHtml(t,m){""")

one("""  return '<div class="msg-b '+(mine?'me':'them')+'">'+msgEsc(m.body||'')+'</div>';
}""", """  return '<div class="msg-b '+(mine?'me':'them')+'">'+msgLinkHtml(m.body||'')+'</div>';
}""")

one("""'<div class="msg-b '+(msgIsMe(m.sender)?'me':'them')+'">'+msgEsc(ss.text)+'</div>'):'')""",
    """'<div class="msg-b '+(msgIsMe(m.sender)?'me':'them')+'">'+msgLinkHtml(ss.text)+'</div>'):'')""")

one("""window.msgOpenProf=function(key,ev){ if(ev)ev.stopPropagation(); try{ if(typeof openProf==='function')openProf(key); }catch(e){} };
""", """window.msgOpenProf=function(key,ev){ if(ev)ev.stopPropagation(); try{ if(typeof openProf==='function')openProf(key); }catch(e){} };
/* chat-links (2026-10-16): a termchamp.com/?p=<professor> or /?c=<class> link in a bubble opens inside the site, in this tab.
   A plain click only (a new-tab click, a modifier or a middle click is left to the browser); if the site cannot find it the
   link simply opens like any other. */
try{ document.addEventListener('click',function(e){
  var a=e.target&&e.target.closest&&e.target.closest('a.msg-link[data-site]');
  if(!a||e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
  var k=a.getAttribute('data-site'), v=a.getAttribute('data-v')||'', done=false;
  try{
    if(k==='p'&&typeof dlFindProf==='function'){ var id=dlFindProf(v); if(id&&typeof openProf==='function'){ openProf(id); done=true; } }
    else if(k==='c'&&typeof dlOpenClass==='function')done=!!dlOpenClass(v);
  }catch(x){}
  if(done)e.preventDefault();
}); }catch(e){}
""")

# ---------------------------------------------------------------------------------------------- 2. Back closes the phone sheet
one("""function navPush(kind,val){
  if(_navPushing)return;
  try{ history.pushState({pf:1,kind:kind,val:val},''); }catch(e){}
}""", """function navPush(kind,val){
  if(_navPushing)return;
  /* chat-links (2026-10-16): the Rate page's phone sheet pushed an entry that its closing has not taken back yet: this step replaces it */
  try{ var _hs=history.state; if(_hs&&_hs.pf&&_hs.kind==='rtsheet'&&!window._rtNav){ history.replaceState({pf:1,kind:kind,val:val},''); return; } }catch(e){}
  try{ history.pushState({pf:1,kind:kind,val:val},''); }catch(e){}
}""")

one("""  window.addEventListener('popstate',function(ev){
    /* Overlays first""", """  window.addEventListener('popstate',function(ev){
    /* chat-links (2026-10-16): the Back that rtSheet() asked for itself is not a navigation; Back with the Rate page's phone sheet
       open (and nothing above it) closes the sheet and stays on the page */
    if(window._navSwallow){ window._navSwallow=false; return; }
    if(window._rtNav&&!navOpenOverlays().length){ window._rtNav=false; try{ rtClose(); }catch(e){} return; }
    /* Overlays first""")

one("""function rtSheet(on){
  var sheet=!!on&&rtPhone();
""", """function rtSheet(on){
  var sheet=!!on&&rtPhone();
  /* chat-links (2026-10-16): the phone sheet is one history step. Opening pushes it (or takes back the one a close has not yet
     removed); popstate closes the sheet (see the nav handler); any other close takes the step off again, unless the page has
     already moved on (then navPush replaced it). */
  try{
    if(sheet&&!window._rtNav){
      window._rtNav=true;
      var _s=history.state; if(!(_s&&_s.pf&&_s.kind==='rtsheet'))history.pushState({pf:1,kind:'rtsheet'},'');
    }else if(!sheet&&window._rtNav){
      window._rtNav=false;
      setTimeout(function(){ try{
        var s=history.state;
        if(!window._rtNav&&s&&s.pf&&s.kind==='rtsheet'){ window._navSwallow=true; setTimeout(function(){ window._navSwallow=false; },800); history.back(); }
      }catch(e){} },0);
    }
  }catch(e){}
""")

f.write_text(s)
print('chat-links patched', f)
