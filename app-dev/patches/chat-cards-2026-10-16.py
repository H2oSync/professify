#!/usr/bin/env python3
"""chat-cards (2026-10-16). A shared schedule is a CARD in the website's chat, not a raw link.

Tate (termchamp.com > Friends > a group chat): "these are still sending links and not cards". Messages looked like
  Here's my Plan A for Spring 2027 https://termchamp.com/s?i=<32hex>.png&nm=Sean&tm=Spring%202027&add=<uuid>&pl=A
and a friend answered "The link ain't work".

WHAT THE PHONE APP DOES (read-only look at app/index.html): it sends a plain TEXT message, body
  "Here's my <term> schedule <link>"  /  "Here's my Plan <A|B|C> for <term> <link>"   (kind 'text', payload null)
and draws any text message that has one of our /s?i=<32hex>.png links as a card (SH_RE / shMsg). There is no
'schedule' message kind (the table's check allows text, class, professor, ask only), so there is nothing structured to
send: the card is made on the READING side, and the text-with-link body is the format both clients use.

TASK 1  Rendering. In a thread (and in the chat list's preview line) a text message whose body holds a link of exactly
        the shape  https://<termchamp.com | www.termchamp.com | professify.app | www.professify.app | this site>/s?i=<32 lowercase
        hex>.(png|json)  with only the params i, nm, tm, add, pl (each at most once; pl is A, B or C; no #fragment, no
        user:pass@, no port) is drawn as a card: the picture from the public schedule-cards bucket (the URL share.ts builds),
        a title ("Tate's Fall 2026 schedule", "Sean's Plan A · Spring 2027"), View, and "Add Sean" when the sender is
        not a friend yet. The words around the link stay as a normal bubble above it; the long URL is hidden.
        Anything else (another host, an extra param, a bad pl, a 31-hex id, http:) stays plain text, as before.
        View opens the picture large (the card sheet the Share button uses). Add goes through the existing invite
        confirm card ("Add <name>?", neutral wording, nothing stored, a waiting invite is left alone); it writes nothing itself.
        The Add button and the card title use the sender's real name, and Add is offered only when the link's add= is the
        SENDER's id (a forwarded link, or a crafted add=, gets View only and the link's own nm).
TASK 2  Sending. The website had no way to put a shared schedule in a chat: Share schedule made a link to paste. The
        card sheet now has "Send to a chat" (same picker as sharing a class or professor) that posts the phone's own
        body, "Here's my <term> schedule <link>", as text, so older clients still show the link and both
        clients draw the card. On a desktop (hover + fine pointer) with messaging on, Share schedule shows that sheet
        even when the browser has a native share (a "Share..." button on the sheet keeps it). The picture and the week
        are uploaded as before; the send now WAITS for both uploads and says so if either failed (it used to send the
        link whatever happened to the upload: a dead link, the "link ain't work" shape).
TASK 3  See the notes in the final report (the likely causes). Website-side fix here: the chat shows the link as a card with
        View, so nobody has to copy a text link out of a bubble (bubbles never made links clickable), and a send
        is refused when the card or the week did not upload.
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'chat-cards (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---------------------------------------------------------------------------------------------------- CSS
one(""".msug-b.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
""", """.msug-b.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
/* a shared schedule in a thread (chat-cards, 2026-10-16) */
.ssc-img{position:relative;display:block;width:100%;padding:0;border:0;border-bottom:1px solid var(--line-soft);
  background:var(--panel-2);cursor:pointer;aspect-ratio:16/10;overflow:hidden}
.ssc-img img{display:block;width:100%;height:100%;object-fit:cover;object-position:top center}
.ssc-img.bad img{display:none}
.ssc-img.bad::after{content:"Preview isn\\2019t available";position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;font-size:12.5px;color:var(--muted)}
.ssc-img:focus-visible,.msug-b:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.ssc .msug-top{border-bottom:0;padding-bottom:6px}
""")

# ---------------------------------------------------------------------------------------------------- reading
one("""function msgRowHtml(t,m,prev){
  var mine=msgIsMe(m.sender);
  var card=(m.kind==='class'||m.kind==='professor');
""", r"""/* ---- a shared schedule, in a thread (chat-cards, 2026-10-16) ------------------------------------
   Tate: "these are still sending links and not cards". Both clients send the same thing, a TEXT message:
   "Here's my Fall 2026 schedule https://termchamp.com/s?i=<32hex>.png&nm=Tate&tm=Fall%202026&add=<uuid>" (and
   "...&pl=A" for a plan). The table has no schedule kind, so the card is made HERE, when the message is read.
   Only the strict shape is a card; anything else stays the plain text it always was. Everything printed is
   escaped, and the message body is never trusted for more than: a 32-hex id, a short name and term, A|B|C, a uuid. */
var MSG_SS_HOSTS={'termchamp.com':1,'www.termchamp.com':1,'professify.app':1,'www.professify.app':1};
function msgSchedHostOk(h){
  h=String(h||'').toLowerCase();
  if(MSG_SS_HOSTS[h])return true;
  try{ var s=String(cfg().SITE_URL||''); if(s){ var sh=new URL(s).host.toLowerCase(); if(sh&&sh===h)return true; } }catch(e){}
  return false;
}
function msgSchedParse(body){
  if(typeof body!=='string'||body.length>2000||body.indexOf('/s?')<0)return null;
  var re=/(^|\s)(https:\/\/[^\s]+)/g, hit, tries=0;
  /* a few candidates at most: a 2000-character message of links must not cost a URL parse each */
  while(tries++<5&&(hit=re.exec(body))){
    var start=hit.index+hit[1].length, end=start+hit[2].length;
    /* "...look at this https://termchamp.com/s?i=....png!" — the punctuation after a link is not part of it */
    var raw=hit[2].replace(/[.,)!?]+$/,''), u;
    try{ u=new URL(raw); }catch(e){ continue; }
    if(u.protocol!=='https:'||u.username||u.password||u.hash||u.pathname!=='/s'||!msgSchedHostOk(u.host))continue;
    /* known params once each; a professor / class / old ?sched= link is not a schedule card; anything else (utm_*, v=) is ignored */
    var bad=false, seen={};
    u.searchParams.forEach(function(v,k){
      if(/^(i|nm|tm|add|pl)$/.test(k)){ if(seen[k])bad=true; seen[k]=1; }
      else if(/^(k|p|c|sched)$/.test(k))bad=true;
    });
    if(bad)continue;
    var q=u.searchParams, im=/^([0-9a-f]{32})\.(png|json)$/.exec(q.get('i')||'');
    if(!im)continue;
    var pl=q.get('pl'); if(pl!==null&&!/^[ABC]$/.test(pl))continue;
    var add=q.get('add'); if(add!==null&&!(typeof UUID_RE!=='undefined'&&UUID_RE.test(add)))add=null;
    /* control characters and the invisible / direction-flipping ones (zero-width, bidi marks and overrides, BOM) out of a name */
    var clean=function(x,n){ return String(x||'').replace(/[\u0000-\u001f\u007f​-‏‪-‮⁠-⁩﻿]/g,' ').replace(/\s+/g,' ').trim().slice(0,n); };
    return { id:im[1], nm:clean(q.get('nm'),40), tm:clean(q.get('tm'),24), pl:pl||'', add:add||'',
             text:(body.slice(0,start)+' '+body.slice(end)).replace(/\s+/g,' ').trim() };
  }
  return null;
}
/* parsed once per message object (a thread redraws on every like and every new message) */
function msgSchedOf(m){
  if(!m||(m.kind&&m.kind!=='text')||!m.body)return null;
  if(m._ssBody===m.body)return m._ss;
  var ss=msgSchedParse(m.body); m._ss=ss; m._ssBody=m.body; return ss;
}
/* WHOSE schedule: when the link's add= is the sender's own id the name is the sender's real one (friend list / profile),
   never the link's nm; nm is only used when it cannot be checked (a forwarded link, a link with no add=). */
function msgSchedWho(m,ss){
  var own=!!(ss.add&&ss.add===m.sender);
  if(own&&msgIsMe(m.sender))return {mine:true,first:''};
  var first='';
  if(own){ try{ var p=msgPerson(m.sender); if(p&&p.first&&p.first!=='Someone')first=p.first; }catch(e){} }
  if(!first)first=String(ss.nm||'').split(/\s+/)[0]||'';
  return {mine:false,first:first};
}
function msgSchedTitle(ss,who){
  var what=ss.pl?('Plan '+ss.pl+(ss.tm?(' · '+ss.tm):'')):((ss.tm?(ss.tm+' '):'')+'schedule');
  if(who.mine)return 'Your '+what;
  return who.first?(who.first+'’s '+what):(ss.pl?what:('Shared '+what));
}
/* the same public URL netlify/edge-functions/share.ts puts in og:image */
function msgSchedImg(ss){
  var b=''; try{ b=String(cfg().SUPABASE_URL||'').replace(/\/+$/,''); }catch(e){}
  return /^https:\/\//.test(b)?(b+'/storage/v1/object/public/schedule-cards/'+ss.id+'.png'):'';
}
/* "Add <name>" is offered for the SENDER's own link only, and only to someone who is neither a friend nor already asked */
function msgSchedCanAdd(m,ss){
  try{
    if(!ss.add||ss.add!==m.sender||msgIsMe(m.sender))return false;
    if(typeof peopleRelState!=='function')return false;
    var st=peopleRelState(m.sender);
    return st==='none'||st==='incoming';
  }catch(e){ return false; }
}
function msgSchedPrev(last){
  var ss=msgSchedOf(last);
  return ss?(ss.text||'Shared a schedule'):'';
}
function msgSchedFind(mid){
  mid=String(mid);
  for(var cid in msgRows){
    if(!Object.prototype.hasOwnProperty.call(msgRows,cid))continue;
    var arr=msgRows[cid]||[];
    for(var i=0;i<arr.length;i++){
      if(String(arr[i].id)===mid){ var ss=msgSchedOf(arr[i]); return ss?{m:arr[i],ss:ss}:null; }
    }
  }
  return null;
}
function msgSchedCardHtml(t,m,ss){
  var who=msgSchedWho(m,ss), title=msgSchedTitle(ss,who), img=msgSchedImg(ss), mid=jsAttr(String(m.id)), first=who.first;
  var add=msgSchedCanAdd(m,ss);
  return (ss.text?('<div class="msg-b '+(msgIsMe(m.sender)?'me':'them')+'">'+msgEsc(ss.text)+'</div>'):'')
    +'<div class="msug ssc"'+(ss.text?' style="margin-top:6px"':'')+'>'
    +(img?('<button class="ssc-img" onclick="msgSchedView(\''+mid+'\',event)" aria-label="View '+msgEsc(title)+'">'
        +'<img src="'+msgEsc(img)+'" alt="'+msgEsc(title)+'" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.className+=\' bad\'"></button>'):'')
    +'<div class="msug-top"><div class="msug-kick">Schedule</div>'
    +'<div class="msug-code">'+msgEsc(title)+'</div></div>'
    +'<div class="msug-acts"><button class="msug-b pri" onclick="msgSchedView(\''+mid+'\',event)">View</button>'
    +(add?('<button class="msug-b" onclick="msgSchedAdd(\''+mid+'\',event)">Add'+(first?(' '+msgEsc(first)):'')+'</button>'):'')
    +'</div></div>';
}
window.msgSchedView=function(mid,ev){
  if(ev)ev.stopPropagation();
  var f=msgSchedFind(mid); if(!f)return;
  var m=f.m, ss=f.ss, who=msgSchedWho(m,ss), img=msgSchedImg(ss), title=msgSchedTitle(ss,who), first=who.first;
  var back=document.getElementById('scSheet');
  if(!back){ back=document.createElement('div'); back.id='scSheet'; back.className='sc-back'; document.body.appendChild(back); }
  back.innerHTML='<div class="sc-card" role="dialog" aria-label="'+msgEsc(title)+'">'
    +'<button class="sc-x" id="scSheetX" onclick="schedCardClose()" aria-label="Close">&times;</button>'
    +'<div class="sc-kick">Shared schedule</div>'
    +'<h3 class="sc-h">'+msgEsc(title)+'</h3>'
    +(img?('<img class="sc-img" src="'+msgEsc(img)+'" alt="'+msgEsc('A shared week of classes: '+title)+'" referrerpolicy="no-referrer" onerror="msgSchedImgBad(this)">'):'')
    +'<div class="sc-acts">'
    +(msgSchedCanAdd(m,ss)?('<button class="btn primary" onclick="msgSchedAdd(\''+jsAttr(String(m.id))+'\',event)">Add'+(first?(' '+msgEsc(first)):'')+'</button>'):'')
    +'<button class="fr-chip" onclick="schedCardClose()">Close</button>'
    +'</div></div>';
  back.classList.add('open');
  back.onclick=function(e){ if(e.target===back)schedCardClose(); };
  try{ var x=document.getElementById('scSheetX'); if(x)x.focus(); }catch(e){}
};
window.msgSchedImgBad=function(el){
  try{
    var p=document.createElement('p'); p.className='sc-fine';
    p.textContent='This picture isn’t available any more. Ask them to send their schedule again.';
    el.parentNode.replaceChild(p,el);
  }catch(e){}
};
/* Add asks "Add <name>?" through the same card an invite link uses, but it is asked right here: nothing is stored (no 14-day
   pending invite that comes back after a reload), a waiting invite is not overwritten, and the card does not say "You opened
   their invite link". Nothing is written until that card's Add. */
window.msgSchedAdd=function(mid,ev){
  if(ev)ev.stopPropagation();
  var f=msgSchedFind(mid); if(!f||!msgSchedCanAdd(f.m,f.ss))return;
  try{ schedCardClose(); }catch(e){}
  msgSchedAsk(f.m.sender);
};
async function msgSchedAsk(id){
  try{
    if(!backendReady()||!sbUser||!id||id===sbUser.id||!UUID_RE.test(id))return;
    var st=(typeof peopleRelState==='function')?peopleRelState(id):'none';
    if(st==='friends'||st==='sent')return;
    if(pendAddBlocked()||document.querySelector('#modal [data-pendadd]')){ try{ frToast('Finish what is open first, then tap Add again'); }catch(e){} return; }
    var name=null; try{ var p=msgPerson(id); if(p&&p.name&&p.name!=='Someone')name=p.name; }catch(e){}
    if(!name){
      try{
        var r=await withTimeout(sb.rpc('get_inviter',{ref:id}),3000,'get_inviter');
        if(r&&!r.error&&r.data){ var row=Array.isArray(r.data)?r.data[0]:r.data; if(row&&row.display_name)name=String(row.display_name).slice(0,80); }
      }catch(e){}
    }
    if(pendAddBlocked()||document.querySelector('#modal [data-pendadd]'))return;
    pendAddPaint(id,name,'chat');
  }catch(e){}
}

function msgRowHtml(t,m,prev){
  var mine=msgIsMe(m.sender);
  var card=(m.kind==='class'||m.kind==='professor'||!!msgSchedOf(m));
""")

one("""  return '<div class="msg-b '+(mine?'me':'them')+'">'+msgEsc(m.body||'')+'</div>';
}
""", """  var _ss=msgSchedOf(m);
  if(_ss)return msgSchedCardHtml(t,m,_ss);
  return '<div class="msg-b '+(mine?'me':'them')+'">'+msgEsc(m.body||'')+'</div>';
}
""")

one("""             :(t.last.body||'');
      pv=who+txt;""", """             :(msgSchedPrev(t.last)||t.last.body||'');
      pv=who+txt;""")

# ---------------------------------------------------------------------------------------------------- sending
# the two uploads report whether they worked (they were fire-and-forget and returned nothing)
one("""    sb.storage.from(SC_BUCKET).upload(id,file,{contentType:'image/png'})
      .then(function(r){ if(r&&r.error)scUploadFailed('card',r.error.message); },
            function(e){ scUploadFailed('card',e&&e.message); });""",
    """    return sb.storage.from(SC_BUCKET).upload(id,file,{contentType:'image/png'})
      .then(function(r){ if(r&&r.error){ scUploadFailed('card',r.error.message); return false; } return true; },
            function(e){ scUploadFailed('card',e&&e.message); return false; });""")
one("""    sb.storage.from(SC_BUCKET).upload(name,blob,{contentType:'application/json'})
      .then(function(r){ if(r&&r.error)scUploadFailed('payload',r.error.message); },
            function(e){ scUploadFailed('payload',e&&e.message); });""",
    """    return sb.storage.from(SC_BUCKET).upload(name,blob,{contentType:'application/json'})
      .then(function(r){ if(r&&r.error){ scUploadFailed('payload',r.error.message); return false; } return true; },
            function(e){ scUploadFailed('payload',e&&e.message); return false; });""")

one("""    scUploadCard(_id,file);
    scUploadPayload(_id,scPayloadStr());
    link=schedPreviewLink(_id);
  }
  if(navigator.share){""", """    var _up=[scUploadCard(_id,file),scUploadPayload(_id,scPayloadStr())];
    link=schedPreviewLink(_id);
    /* chat-cards (2026-10-16): what "Send to a chat" waits on. The link is only worth sending once BOTH objects are in the
       bucket; a failed upload used to be sent anyway, and the friend got "That schedule link has expired". */
    if(/\\/s\\?i=/.test(link))window._scLast={link:link,ready:Promise.all(_up.map(function(p){
      return Promise.resolve(p).then(function(r){ return r===true; },function(){ return false; }); })).then(function(a){ return a.every(Boolean); })};
  }
  /* A desktop with messaging on shows the card sheet (it has Send to a chat) even when the browser can share natively. */
  var _deskChat=false;
  try{ _deskChat=!!(schedChatOk(link)&&window.matchMedia&&window.matchMedia('(hover:hover) and (pointer:fine)').matches); }catch(e){}
  if(navigator.share&&!_deskChat){""")
one("""  var file=schedCardFileSync(schedCardOpts());
  /* The id is chosen HERE""", """  var file=schedCardFileSync(schedCardOpts());
  window._scLast=null;
  /* The id is chosen HERE""")

one("""    +'<button class="fr-chip" onclick="schedCardCopy()">Copy the link</button>'
""", """    +'<button class="fr-chip" onclick="schedCardCopy()">Copy the link</button>'
    +(schedChatOk(link)?'<button class="fr-chip" onclick="schedSendToChat()">Send to a chat</button>':'')
    +((navigator.share&&schedChatOk(link))?'<button class="fr-chip" onclick="schedCardNativeShare()">Share\\u2026</button>':'')
""")

one("""window.schedCardSheet=schedCardSheet;
""", """window.schedCardSheet=schedCardSheet;
/* chat-cards (2026-10-16): a chat can be the destination only when the link is the short /s?i= one (a long ?sched= link is
   no card) and the uploads behind it were started by this very share. */
function schedChatOk(link){
  try{ return !!(link&&window._scLast&&window._scLast.link===link&&typeof msgOn==='function'&&msgOn()); }catch(e){ return false; }
}
window.schedSendToChat=function(){
  var w=window._scLast; if(!w||!w.link)return;
  var term=''; try{ term=(typeof APP_TERM!=='undefined'?String(APP_TERM||''):''); }catch(e){}
  /* the phone app's own words, so a card is made on either side and an older client still shows a readable line */
  window._scShare={link:w.link,ready:w.ready,label:(term?('My '+term+' schedule'):'My schedule'),
                   body:'Here\\u2019s my '+(term?(term+' '):'')+'schedule'};
  try{ schedCardClose(); }catch(e){}
  shOpen('week');
};
window.schedCardNativeShare=function(){
  var el=document.getElementById('scLink'); var v=el?el.value:'';
  if(!v||!navigator.share)return;
  try{ navigator.share({url:v}).catch(function(){}); }catch(e){}
};
""")

one("""function pendAddPaint(id,name){
  var modal=document.getElementById('modal'), mb=document.getElementById('mback'); if(!modal||!mb)return;""", """function pendAddPaint(id,name,src){
  var modal=document.getElementById('modal'), mb=document.getElementById('mback'); if(!modal||!mb)return;""")
one("""    +'<p class="rate-sub">You opened their invite link. Adding sends a friend request, and they choose whether to accept it.</p>'""",
    """    +'<p class="rate-sub">'+(src==='chat'?'':'You opened their invite link. ')+'Adding sends a friend request, and they choose whether to accept it.</p>'""")
one("""  if(!yes){ pendAddClear(); closeModal(); return; }                       /* Not now: answered, nothing written */""",
    """  if(!yes){ pendAddClearIf(id); closeModal(); return; }                   /* Not now: answered, nothing written */""")
one("""  pendAddClear();
  closeModal();
  show('friends');""", """  pendAddClearIf(id);
  closeModal();
  show('friends');""")
one("""function pendAddGet(){""", """/* answering a card clears the waiting invite only when it is THAT person's (an Add asked from a chat stores nothing) */
function pendAddClearIf(id){ if(pendAddGet()===id)pendAddClear(); }
function pendAddGet(){""")

# the picker (shOpen / shRender / shSendTo / shCopyLink) learns a third thing to send
one("""    shShare={kind:'prof',key:idOrCode,label:label};
  }else{""", """    shShare={kind:'prof',key:idOrCode,label:label};
  }else if(kind==='week'){
    var _w=window._scShare; if(!_w||!_w.link)return;
    label=_w.label||'My schedule';
    shShare={kind:'week',link:_w.link,ready:_w.ready,body:_w.body,label:label};
  }else{""")
one("""(shShare.kind==='prof'?'their page':'this class')""", """(shShare.kind==='prof'?'their page':shShare.kind==='week'?'your schedule':'this class')""")
span_start = """window.shSendTo=async function(cid,uid){"""
span_end = """/* msgSendClass() posts to whatever thread is OPEN"""
i = s.index(span_start); assert s.count(span_start) == 1 and s.count(span_end) == 1
j = s.index(span_end, i)
s = s[:i] + """/* chat-cards (2026-10-16): the sheet's own state is held in `sh` (closing the sheet mid-send used to throw after the message was
   already out), a second tap while one is in flight does nothing (the rows are disabled too), and a schedule whose picture or week
   did not upload is refused BEFORE a conversation is created for it. */
window.shSendTo=async function(cid,uid){
  var sh=shShare;
  if(!sh||sh.busy)return;
  sh.busy=true; try{ shRender(); }catch(e){}
  try{
    if(sh.kind==='week'){
      var up=false; try{ up=await sh.ready; }catch(e){}
      if(!up){
        /* the result is cached: asking again cannot succeed, so say so and start over from Share schedule */
        try{ if(shShare===sh)shClose(); }catch(e){}
        try{ frToast('Couldn\\u2019t get the schedule link ready. Close this and share your schedule again.'); }catch(e){}
        return;
      }
    }
    var target=cid;
    if(!target&&uid){
      target=await msgThreadWith(uid);
      if(!target){ try{ frToast('Couldn\\u2019t open that conversation'); }catch(e){} return; }
    }
    if(!target)return;
    var ok=(sh.kind==='week')
      ? await msgSendWeek(sh,target)
      : (sh.kind==='prof')
      ? await msgSendProf(sh.key,target)
      : await msgSendClass2(sh.code,target);
    if(!ok)return;
    var label=sh.label;
    if(shShare===sh)shClose();
    /* Land them in the thread they just sent to — the message is the start of a conversation,
       not a fire-and-forget. */
    try{ if(typeof show==='function')show('friends'); }catch(e){}
    try{ msgRenderList(); msgOpen(target); }catch(e){}
    try{ frToast('Sent '+label+' \\u2713'); }catch(e){}
  }finally{
    sh.busy=false;
    try{ if(shShare===sh)shRender(); }catch(e){}
  }
};

/* A schedule goes as the phone sends it: plain text, "Here's my Fall 2026 schedule <link>" (shSendTo has already checked that
   the picture and the week are in the bucket). */
async function msgSendWeek(sh,cid){
  var ok=await msgSend(cid,'text',sh.body+' '+sh.link,null);
  if(!ok){ try{ frToast('Couldn\\u2019t send that \\u2014 try again'); }catch(e){} return false; }
  return true;
}
""" + s[j:]
one("""        return '<button class="sh-row" onclick="shSendTo(\\''+jsAttr(t.id)+'\\',null)">'""", """        return '<button class="sh-row"'+(shShare.busy?' disabled':'')+' onclick="shSendTo(\\''+jsAttr(t.id)+'\\',null)">'""")
one("""        return '<button class="sh-row" onclick="shSendTo(null,\\''+jsAttr(f.id)+'\\')">'""", """        return '<button class="sh-row"'+(shShare.busy?' disabled':'')+' onclick="shSendTo(null,\\''+jsAttr(f.id)+'\\')">'""")
one("""    url=(shShare.kind==='prof')
      ? ((typeof dlProfUrl==='function')?dlProfUrl(shShare.key):'')
      : ((typeof dlClassUrl==='function')?dlClassUrl(shShare.code):'');""", """    url=(shShare.kind==='week')
      ? shShare.link
      : (shShare.kind==='prof')
      ? ((typeof dlProfUrl==='function')?dlProfUrl(shShare.key):'')
      : ((typeof dlClassUrl==='function')?dlClassUrl(shShare.code):'');""")

f.write_text(s)
print('patched', f)
