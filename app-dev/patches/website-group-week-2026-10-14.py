#!/usr/bin/env python3
"""The group page gets the phone's coloured week as a SECOND view (Tate, 2026-10-14: "the group schedule coloured week
view is added as a second view"). Phone spec: group-schedule-2026-10-10.py.

The website's group page (Friends > Groups > a group) already answers "when are we all free" with a lane-per-person grid
and a ranked list. It keeps doing that. A switch above the grid, "Free time | Week", adds the phone's picture:

- WEEK: one Mon-Fri grid of the term people are in NOW (Fall: gpMemberBusy reads nowMine() / frNow(f), the same rows the
  Free-time view uses). Every class is a block in its person's colour; a class two people are in together is ONE block
  split into both colours; classes at the same time sit side by side. Work & activities (window.cmBlocks, through
  cmPushBusy) draw too: yours by its name (only you see it), a friend's as "Busy" with no name anywhere. The shared-free
  stretches (the Free-time view's own runs, 30 minutes or more, everyone counted) are green bands with their length. A red
  line marks now on today. The hours are 8a-6p, wider when somebody's class is earlier or later (never past 7a-10p).
  Geometry is clipped to those hours but every label is the REAL time (a free morning from 7a says "7a-10a, 3h" even
  when the grid starts at 8a), and the key says "Free for the N counted" when anyone is muted or has shared nothing.
- Every block is a button: a class opens its class page, a friend's Busy opens that friend, your own Busy opens it in the
  Work & activities editor. Its label says the code, time and who.
- The members list beside the grid is the legend: each person's ball is their week colour, and a tap still mutes them (a
  muted person's blocks leave the week and the free bands recount). Someone who shared nothing is dimmed ("no schedule
  shared") and draws nothing: unknown is never drawn as free, and a time we cannot read is never invented.
- The switch is remembered per signed-in person on this device (professify_group_view_<user>).
- Colours: the phone's eight, each >= 4.5:1 under white text; white text on them holds in light and dark.

Also: cmPushBusy's blocks now say whether they are Work & activities (cm) and which one (cmid), so the week can tell a
shift from a class. Nothing else about the Free-time view changes.

Usage: python3 website-group-week-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-group-week (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# 1. commitments' busy entries say what they are
one("""if (di >= 0) out.push({ di: di, s: b.meet.start, e: b.meet.end, code: b.label }); });
    });
  }""",
    """if (di >= 0) out.push({ di: di, s: b.meet.start, e: b.meet.end, code: b.label, cm: b.cm, cmid: b.id }); });   /* website-group-week (2026-10-14) */
    });
  }""")

# 2. the week view + the switch
one("""function gpRenderDetail(){
  var host=document.getElementById('gpPane'); if(!host)return;""",
    r"""/* ================= website-group-week (2026-10-14): the coloured week, as a second view =================
   The phone's group week (group-schedule, 2026-10-10) on the website's group page. It reads the SAME per-member busy
   blocks and free runs the Free-time view reads (gpRunsFor), so the two views can never disagree about who is free. */
var GW_COL=['#2F5FC4','#B8541A','#B53A72','#1B7F74','#7A4FD0','#8A6A00','#56698A','#8B5A3C'];   /* white text >= 4.5:1 on each */
var GW_PX=0.72;                                        /* px a minute: a 50-minute class is 36px, room for its code and time */
function gwKey(){ var u='anon'; try{ if(typeof sbUser!=='undefined'&&sbUser&&sbUser.id)u=sbUser.id; }catch(e){} return 'professify_group_view_'+u; }
function gwView(){ try{ return localStorage.getItem(gwKey())==='week'?'week':'free'; }catch(e){ return 'free'; } }
window.gpSetView=function(v){ try{ localStorage.setItem(gwKey(),v==='week'?'week':'free'); }catch(e){} gpRenderDetail(); };
function gwSwitch(){
  var w=gwView()==='week';
  return '<div class="gw-sw" role="group" aria-label="Group view">'
    +'<button type="button" class="gw-sb'+(w?'':' on')+'" aria-pressed="'+(w?'false':'true')+'" onclick="gpSetView(\'free\')">Free time</button>'
    +'<button type="button" class="gw-sb'+(w?' on':'')+'" aria-pressed="'+(w?'true':'false')+'" onclick="gpSetView(\'week\')">Week</button></div>';
}
function gwHs(m){ var h=Math.floor(m/60)%24,mm=m%60; return ((h%12)||12)+(mm?':'+(mm<10?'0':'')+mm:'')+(h>=12?'p':'a'); }
function gwRange(a,b){ return gwHs(a)+'–'+gwHs(b); }
function gwFill(cols){ return cols.length===1?cols[0]:'linear-gradient(90deg,'+cols.map(function(c,i){
  return c+' '+(i*100/cols.length).toFixed(2)+'% '+((i+1)*100/cols.length).toFixed(2)+'%'; }).join(',')+')'; }
/* The hours the week covers: 8a-6p, wider when someone's class starts earlier or ends later, never outside 7a-10p. */
function gwSpan(c){
  var lo=8*60, hi=18*60;
  c.members.forEach(function(m){ if(c.muted[m.id]||m.noData)return;
    (m._blocks||[]).forEach(function(b){ lo=Math.min(lo,Math.floor(b.s/60)*60); hi=Math.max(hi,Math.ceil(b.e/60)*60); }); });
  return [Math.max(GP_LO,lo),Math.min(GP_HI,hi)];
}
/* One day's blocks: a block per class (people in the same class at the same time share one), lanes for overlaps. */
function gwDay(c,di,S0,S1){
  var by={}, order=[];
  c.members.forEach(function(m){ if(c.muted[m.id]||m.noData)return;
    (m._blocks||[]).forEach(function(b){
      if(b.di!==di)return;
      /* gs/ge are where it is DRAWN (the grid ends at 7a / 10p); s/e are its real time, which is what is written */
      var gs=Math.max(b.s,S0), ge=Math.min(b.e,S1); if(ge<=gs)return;
      var k=(b.cm?('cm|'+m.id+'|'+(b.cmid||'')):b.code)+'|'+b.s+'|'+b.e;
      if(!by[k]){ by[k]={code:b.code,s:b.s,e:b.e,gs:gs,ge:ge,cm:b.cm||'',cmid:b.cmid||'',who:[]}; order.push(k); }
      if(by[k].who.indexOf(m)<0)by[k].who.push(m);
    }); });
  var blocks=order.map(function(k){ return by[k]; }).sort(function(x,y){ return x.gs-y.gs||y.ge-x.ge||(x.code<y.code?-1:x.code>y.code?1:0); });
  var lanes=[], cl=[], end=-1;
  function flush(){ var n=lanes.length; cl.forEach(function(b){ b.n=n; }); cl=[]; lanes=[]; end=-1; }
  blocks.forEach(function(b){
    if(cl.length&&b.gs>=end)flush();
    var l=-1; for(var i=0;i<lanes.length;i++){ if(lanes[i]<=b.gs){ l=i; break; } }
    if(l<0){ l=lanes.length; lanes.push(0); }
    lanes[l]=b.ge; b.l=l; cl.push(b); end=Math.max(end,b.ge);
  });
  if(cl.length)flush();
  return blocks;
}
function gwWho(b){ return b.who.map(function(m){ return m.me?'you':m.name.split(' ')[0]; }).join(', '); }
function gwBlockHtml(b,S0){
  var h=Math.max(4,(b.ge-b.gs)*GW_PX-2), top=(b.gs-S0)*GW_PX+1, n=b.n||1;
  var st='top:'+top.toFixed(1)+'px;height:'+h.toFixed(1)+'px;left:calc('+(b.l*100/n).toFixed(3)+'% + 2px);width:calc('+(100/n).toFixed(3)+'% - 4px);'
    +'background:'+gwFill(b.who.map(function(m){ return m._wc; }));
  var mineCm=(b.cm==='mine'), busyF=(!!b.cm&&!mineCm), label=busyF?'Busy':b.code;   /* anything of Work & activities that is not yours is a friend's Busy */
  var al=label+', '+gwRange(b.s,b.e)+(busyF?', '+gwWho(b):mineCm?', only you see this':', '+gwWho(b));
  var inner=h>=14?('<b>'+escAcc(label)+'</b>'+(h>=34?'<i>'+gwRange(b.s,b.e)+'</i>':'')):'';
  var cls='gw-b'+(b.cm?' cm':'')+(b.who.length>1?' multi':'');
  var act = busyF ? 'openFriendProfile(\''+jsAttr(b.who[0].id)+'\')'
          : mineCm ? ''
          : 'openClassPage(\''+jsAttr(b.code)+'\',event)';
  return '<button type="button" class="'+cls+'" style="'+st+'" aria-label="'+escAcc(al)+'" title="'+escAcc(al)+'"'
    +(mineCm?(' data-cm-act="edit" data-id="'+escAcc(b.cmid)+'"'):(' onclick="'+act+'"'))+'>'+inner+'</button>';
}
function gwWeek(g,c){
  var span=gwSpan(c), S0=span[0], S1=span[1], H=Math.round((S1-S0)*GW_PX), N=c.members.length;
  var shared=c.active.length>1, now=new Date(), today=now.getDay()-1, nowMin=now.getHours()*60+now.getMinutes();
  var ax='';
  for(var m=Math.ceil(S0/60)*60;m<=S1;m+=60){
    ax+='<div class="gw-t" style="top:'+((m-S0)*GW_PX).toFixed(1)+'px">'+gwHs(m).replace(/[ap]$/,function(x){ return x==='a'?'am':'pm'; })+'</div>'; }
  var head='<div class="gw-gh"><div></div>'+GP_DAYS.map(function(d,di){
    return '<div class="gw-dh'+(di===today?' td':'')+'">'+GP_DAYFULL[d].slice(0,3)+'</div>'; }).join('')+'</div>';
  var cols=GP_DAYS.map(function(d,di){
    var h='<div class="gw-day" style="height:'+H+'px">';
    for(var m2=Math.ceil(S0/60)*60;m2<S1;m2+=60){ if(m2>S0)h+='<div class="gw-rule" style="top:'+((m2-S0)*GW_PX).toFixed(1)+'px"></div>'; }
    if(shared)c.runs.filter(function(r){ return r.di===di&&r.key==='all'; }).forEach(function(r){
      /* drawn inside the grid, written as it really is (a free morning from 7a says 7a even when the grid starts at 8a) */
      var s=Math.max(r.s,S0), e=Math.min(r.e,S1); if(e<=s)return;
      var ht=(e-s)*GW_PX;
      h+='<div class="gw-free" style="top:'+((s-S0)*GW_PX).toFixed(1)+'px;height:'+ht.toFixed(1)+'px" title="'+escAcc('Free '+gwRange(r.s,r.e))+'">'
        +(ht>=30?('<span>Free<br>'+gpDur(r.e-r.s)+'</span>'):ht>=16?('<span>'+gpDur(r.e-r.s)+'</span>'):'')+'</div>';
    });
    gwDay(c,di,S0,S1).forEach(function(b){ h+=gwBlockHtml(b,S0); });
    if(di===today&&nowMin>=S0&&nowMin<=S1)h+='<div class="gw-now" style="top:'+((nowMin-S0)*GW_PX).toFixed(1)+'px"></div>';
    return h+'</div>';
  }).join('');
  var nCounted=c.active.length;
  var key='<div class="gw-key">'+c.members.map(function(m){
      var off=!!c.muted[m.id]||m.noData;
      return '<span class="gw-k'+(off?' off':'')+'"><span class="gw-ball" style="background:'+m._wc+'"></span>'+escAcc(m.me?'You':m.name.split(' ')[0])+'</span>'; }).join('')
    +(shared?('<span class="gw-k"><span class="gp-sw"></span>'+(nCounted===N?'All '+N+' free':'Free for the '+nCounted+' counted')+'</span>'):'')+'</div>';
  var none=!c.members.some(function(m){ return !c.muted[m.id]&&!m.noData&&(m._blocks||[]).length; });
  return '<div class="gw-wk" data-gw="week">'
    +'<div class="gw-cap">'+escAcc((typeof mcNowLabel==='function')?mcNowLabel():'This term')+'</div>'
    +'<div class="gw-grid">'+head+'<div class="gw-gb"><div class="gw-gut" style="height:'+H+'px">'+ax+'</div>'+cols+'</div></div>'
    +(none?'<div class="gp-empty-s">No class times to draw yet.</div>':'')
    +key+'</div>';
}

function gpRenderDetail(){
  var host=document.getElementById('gpPane'); if(!host)return;""")

# 3. week colours on the member list; the grid / week choice
one("""  var muted=Object.keys(c.muted).filter(function(k){return c.muted[k];}).length;
""",
    """  var muted=Object.keys(c.muted).filter(function(k){return c.muted[k];}).length;
  var wk=(gwView()==='week');   /* website-group-week (2026-10-14): the member list is the week's legend */
  c.members.forEach(function(m,i){ m._wc=GW_COL[i%GW_COL.length]; });
""")
one("""+'<span class="gp-av" style="background:'+(off?'transparent':m.color)+';border-color:'+m.color+'">'+escAcc(m.ini)+'</span>'""",
    """+'<span class="gp-av" style="background:'+(off?'transparent':(wk?m._wc:m.color))+';border-color:'+(wk?m._wc:m.color)+(wk?(';color:'+(off?'var(--text)':'#fff')):'')+'">'+escAcc(m.ini)+'</span>'""")
one("""        +gpGrid(g,c,(g._day!=null&&g._day>=0)?g._day:null)
        +'<div class="gp-key"><span class="gp-sw"></span>'+(c.active.length?('all '+c.active.length+' free'):'nobody active')+'</div>'""",
    """        +gwSwitch()
        +(wk?gwWeek(g,c):(gpGrid(g,c,(g._day!=null&&g._day>=0)?g._day:null)
        +'<div class="gp-key"><span class="gp-sw"></span>'+(c.active.length?('all '+c.active.length+' free'):'nobody active')+'</div>'))""")

# 4. styles
one(""".gp-key{display:flex;align-items:center;gap:7px;margin-top:9px;font-size:12px;color:var(--faint)}""",
    """.gp-key{display:flex;align-items:center;gap:7px;margin-top:9px;font-size:12px;color:var(--faint)}
/* website-group-week (2026-10-14): the coloured week */
.gw-sw{display:inline-flex;gap:2px;padding:3px;margin-bottom:12px;background:var(--panel-2);border:1px solid var(--line);border-radius:10px}
.gw-sb{border:0;background:none;color:var(--muted);font:inherit;font-weight:600;font-size:12.5px;padding:0 14px;min-height:34px;border-radius:7px;cursor:pointer}
.gw-sb.on{background:rgba(var(--accent-rgb),.16);color:var(--text);font-weight:700}
.gw-cap{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--faint);margin:0 0 8px}
.gw-gh{display:grid;grid-template-columns:36px repeat(5,1fr);gap:3px;margin-bottom:5px}
.gw-dh{font-size:11px;font-weight:600;letter-spacing:.05em;text-align:center;color:var(--faint)}
.gw-dh.td{color:var(--good)}
.gw-gb{display:grid;grid-template-columns:36px repeat(5,1fr);gap:3px}
.gw-gut{position:relative}
.gw-t{position:absolute;right:5px;transform:translateY(-50%);font-family:var(--mono);font-size:9.5px;line-height:10px;color:var(--faint);white-space:nowrap}
.gw-gut .gw-t:first-child{transform:none}
.gw-day{position:relative;background:rgba(var(--fg-rgb),.03);border-radius:5px;overflow:hidden}
.gw-rule{position:absolute;left:0;right:0;height:1px;background:rgba(var(--fg-rgb),.06)}
.gw-free{position:absolute;left:2px;right:2px;border-radius:5px;background:rgba(34,160,95,.2);border:1px dashed rgba(34,160,95,.65);box-sizing:border-box;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden}
.gw-free span{font-family:var(--mono);font-size:10.5px;font-weight:700;line-height:1.2;color:var(--text);font-variant-numeric:tabular-nums}
.gw-b{position:absolute;box-sizing:border-box;border:0;border-radius:6px;padding:3px 5px;overflow:hidden;text-align:left;color:#fff;container-type:inline-size;font:inherit;cursor:pointer;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:1px;box-shadow:0 0 0 1px var(--panel)}
.gw-b.cm::before{content:'';position:absolute;inset:0;background:repeating-linear-gradient(135deg,rgba(0,0,0,.2) 0 4px,transparent 4px 9px);pointer-events:none}
.gw-b > *{position:relative}
.gw-b b{display:block;font-size:11.5px;font-weight:800;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gw-b i{display:block;font-style:normal;font-size:10.5px;font-weight:700;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media (hover:hover){.gw-b:hover{filter:brightness(.92)}}
.gw-b:focus-visible{outline:2px solid var(--text);outline-offset:1px}
@container (max-width:84px){.gw-b i{display:none}}
@container (max-width:30px){.gw-b b{display:none}}
.gw-now{position:absolute;left:0;right:0;height:2px;background:#DC2626;z-index:3;pointer-events:none}
.gw-key{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px;margin-top:11px;font-size:12px;color:var(--muted)}
.gw-k{display:inline-flex;align-items:center;gap:6px}
.gw-k.off .gw-ball{opacity:.35}
.gw-key .gp-sw{background:rgba(34,160,95,.3);border:1px dashed rgba(34,160,95,.8);box-sizing:border-box}
.gw-ball{width:11px;height:11px;border-radius:50%;flex:none}""")

f.write_text(s)
print('patched', f)
