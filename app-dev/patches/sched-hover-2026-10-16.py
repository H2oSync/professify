#!/usr/bin/env python3
"""WEBSITE sched-hover pass, 2026-10-16 (index.html only; no build stamp - the coordinator stamps at merge).
Tate: "you can make the my classes schedule longer vertically so the class names aren't as packed. also for plans add class
names in them. lets make it so the professors wired show on my classes and plan like we used to have and like we still have
for stories, but instead of always having them show, only show the professor and connector when you hover over a class.
this should also show the class's time in a simple and clean way."

TASK 1  Schedule > My classes week is taller: 0.56 -> 0.88 px per minute on a desktop width (> 640px), so a 50-minute class
        is 44px and shows its code AND a two-line name (ellipsis on line 2 at most). Only the owner's own week (opts.cm
        === 'me'); a friend's profile week, the Watchlist week and the phone keep today's scale.
TASK 2  Schedule > Plans week (the green Plan A / B / C blocks): every block now shows code + class name + time. The grid is
        taller on a laptop (80px per hour) so the name fits; how many name lines fit is MEASURED per block (0, 1 or 2).
TASK 3  The professor wires are now ON HOVER on My classes and Plans. Nothing is drawn at rest. Hover (mouse) or keyboard
        focus on a class block shows that class's professor card (the same .hz-card as the friend profile, with the star
        rating) in the nearest empty spot of the week, a connector to EVERY meeting of that class, and the class time as one plain line
        ("MW 10:10-11:00a") in the card. Every other block dims while one is lit. The card stands in the nearest EMPTY spot on the
        week (never on a class), so no margin is reserved and the week keeps its full width. A touch device (no hover) draws nothing and
        every tap works as before; the click handlers are untouched, and a click clears the overlay first.
        The old always-on layer (hzMount) is no longer called for My classes; the average line under the week stays.
TASK 4  The friend profile and stories are not touched: hzBuild / hzMount / hzTrace and the .frp-cal host are as they were.
        The window resize handler skips the hover hosts ([data-hv]) so it can not rebuild the old layer on them.

Usage: python3 sched-hover-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'sched-hover (2026-10-16)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ My classes: taller week
one("  var PPM=(typeof CAL_PPM!=='undefined')?CAL_PPM:0.56, gridH=(hi-lo)*PPM;",
    "  var PPM=(typeof CAL_PPM!=='undefined')?CAL_PPM:0.56;\n"
    "  /* sched-hover (2026-10-16): the owner's own week is taller on a desktop width, so a 50-minute class (44px) holds its code and a\n"
    "     two-line name. A friend's week, the Watchlist week and the phone keep the old scale. */\n"
    "  var _tall=(opts.cm==='me'&&typeof window!=='undefined'&&window.innerWidth>640);\n"
    "  if(_tall)PPM=0.92;\n"
    "  var gridH=(hi-lo)*PPM;")
# a tall block's code row is 15.5px and a name line is 12px: the room maths has to use what is really there
one("        var room=h-6-13;                                   // padding + the code line",
    "        var room=h-6-(_tall?16:13);                        // padding + the code line (sched-hover: the tall week measures the real 15.5px code row)")
one("""'<i class="cb-nmc" style="-webkit-line-clamp:'+nmLines+'">'""",
    """'<i class="cb-nmc" style="-webkit-line-clamp:'+nmLines+(_tall?';line-height:12px':'')+'">'""")

# the block says which day, start and end it draws, so a hover can say \"MW 10:10-11:00a\"
one("""          +'" data-code="'+escAcc(m.code)+'" data-crn="'+escAcc(m.crn||'')+'" data-prof="'+escAcc(m.prof||'')+'"'
          +' role="button" tabindex="0" onclick="event.stopPropagation();cbTap(\\''+tapCode+'\\'""",
    """          +'" data-code="'+escAcc(m.code)+'" data-crn="'+escAcc(m.crn||'')+'" data-prof="'+escAcc(m.prof||'')+'"'
          +' data-d="'+d+'" data-s="'+m.meet.start+'" data-e="'+m.meet.end+'"'
          +' role="button" tabindex="0" onclick="event.stopPropagation();cbTap(\\''+tapCode+'\\'""")

# ================================================================ My classes: hover layer instead of the always-on one
one("  try{ hzMount(out.querySelector('.mc-cal')); }catch(_e){}\n}",
    "  try{ hvMount(out.querySelector('.mc-cal'),'mc'); }catch(_e){}   /* sched-hover (2026-10-16): on hover, not always */\n}")
one("""+'</div>'+((typeof cmSlotHtml==='function')?cmSlotHtml():'');
}
function renderMyClasses(){""",
    """+'</div>'+((typeof cmSlotHtml==='function')?cmSlotHtml():'');
  try{ hvMount(out.querySelector('.mc-cal'),'mc'); }catch(_e){}   /* sched-hover (2026-10-16) */
}
function renderMyClasses(){""")
one("    document.querySelectorAll('.frp-cal,.mc-cal').forEach(function(h){\n      try{ hzBuild(h,true);",
    "    document.querySelectorAll('.frp-cal,.mc-cal:not([data-hv])').forEach(function(h){\n      try{ hzBuild(h,true);")

# ================================================================ Plans week: name in the block + the data the hover reads
one("""    var h = '<div class="pl3-week' + (edit ? ' pl3-week--edit' : '') + '" role="group" aria-label="Plan ' + slot + ', week">'""",
    """    var h = '<div class="pl3-week' + (edit ? ' pl3-week--edit' : '') + '"' + (edit ? '' : ' style="--pl3-hrs:' + (span / 60) + '"') + ' role="group" aria-label="Plan ' + slot + ', week">'""")
one("""data-pl-act="open" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '"'
            + ' aria-label="' + esc(i.label + ', ' + dayLetters(i.meet) + ' ' + time + (clashes[i.crn] ? ', clashes with another class' : '')) + '"><b>' + esc(i.code) + '</b><span>' + esc(time) + '</span></button>';""",
    """data-pl-act="open" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '"'
            + ' data-prof="' + esc(i.prof || '') + '" data-d="' + d + '" data-s="' + c.s + '" data-e="' + c.e + '"'
            + ' aria-label="' + esc(i.label + ', ' + dayLetters(i.meet) + ' ' + time + (clashes[i.crn] ? ', clashes with another class' : '')) + '"><b>' + esc(i.code) + '</b>'
            + '<span class="pl3-nmw"><i class="pl3-nm">' + esc(nameOf(i.code)) + '</i></span><span class="pl3-tm">' + esc(time) + '</span></button>';""")
one("""    var bw = document.getElementById('schedPlanWrap');
    if (bw && bw.style.display !== 'none') { if (typeof window.tcBuilderRender""",
    """    try { if (out && typeof window.hvMount === 'function') window.hvMount(out.querySelector('.pl3-week'), 'plan'); } catch (_) {}   /* sched-hover (2026-10-16) */
    var bw = document.getElementById('schedPlanWrap');
    if (bw && bw.style.display !== 'none') { if (typeof window.tcBuilderRender""")

# ================================================================ the hover layer itself (CSS + JS), after the Plans CSS
CSS = r'''<style id="sched-hover-css">
/* sched-hover (2026-10-16). Professor wires on hover for Schedule > My classes and Schedule > Plans. Nothing is drawn at rest. */
.hv-host{position:relative}
.hv-svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible;z-index:0}
.hv-svg path{fill:none;stroke-width:1.6;stroke-linecap:round;opacity:.92;stroke-dasharray:1;stroke-dashoffset:0;animation:hv-draw .24s ease-out}
.hv-svg circle{opacity:.95}
.hv-card{pointer-events:none;z-index:6;animation:hv-in .14s ease-out}
.hv-when{margin-top:8px;padding-top:7px;border-top:1px solid var(--line);font-size:var(--t-body);font-weight:700;line-height:1.25;
  color:var(--text);font-variant-numeric:tabular-nums;white-space:nowrap}
@keyframes hv-draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes hv-in{from{opacity:0;transform:translateX(4px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.hv-svg path,.hv-card{animation:none}}
/* dim the rest, ring the lit class */
.hv-host .cal-block,.hv-host .pl3-blk{transition:opacity .12s ease,box-shadow .12s ease}
.hv-live .cal-block:not(.hv-me),.hv-live .pl3-blk:not(.hv-me){opacity:.5}
.hv-live .cal-block.hv-me,.hv-live .pl3-blk.hv-me{box-shadow:0 0 0 2px var(--panel),0 0 0 4px currentColor}
/* every meeting of the lit class looks the same: the old per-block hover lift/brighten would single out the one under the pointer */
.hv-live .cal-block.hv-me,.hv-live .pl3-blk.hv-me{filter:none;transform:none}
.pl3-week.hv-host .hv-svg{z-index:1}
.pl3-week.hv-host .pl3-blk{z-index:2}
@media (prefers-reduced-motion:reduce){.hv-host .cal-block,.hv-host .pl3-blk{transition:none}}
/* Plans: the name sits between the code and the time. How many lines fit is measured per block (hvFit). */
.pl3-blk .pl3-nmw{display:block;overflow:hidden}
.pl3-blk .pl3-nm{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;font-style:normal;font-size:var(--t-label);line-height:1.2;opacity:.95}
.pl3-blk .pl3-tm{opacity:.95}
/* Plans: a taller week on a laptop so a 50-minute class holds code + name + time (the Planner's week is untouched) */
@media (min-width:521px){
  #view-sched .pl3-week:not(.pl3-week--edit) .pl3-grid{height:calc(var(--pl3-hrs,10) * 64px)}
}
@media (min-width:1000px){
  #view-sched .pl3-week:not(.pl3-week--edit) .pl3-grid{height:calc(var(--pl3-hrs,10) * 80px)}
}
/* on a phone the columns are ~50px wide: code only, as before */
@media (max-width:520px){.pl3-blk .pl3-nmw{display:none}}
</style>
<script id="sched-hover-js">
/* sched-hover (2026-10-16). One hover layer for the two weeks that are the student's own: My classes (.mc-cal) and Plans
   (.pl3-week). It reuses the friend profile's card (hzCardHtml) and its curved connector, but draws them for ONE class at a
   time, only while the pointer is over it (or it has keyboard focus), and removes them again. hzBuild / hzTrace are untouched. */
(function(){
  var HV_CW=142;   /* the card is as wide as the friend profile's */
  var HV_SEL='.cal-block[data-code],.pl3-blk[data-code]';
  var DN={Mo:'M',Tu:'Tu',We:'W',Th:'Th',Fr:'F',Sa:'Sa',Su:'Su'}, DO=['Mo','Tu','We','Th','Fr','Sa','Su'];
  var hosts=[], ro=null;
  function canHover(){ try{ return !!(window.matchMedia&&matchMedia('(hover: hover) and (pointer: fine)').matches); }catch(e){ return false; } }
  function pad(n){ return n<10?('0'+n):(''+n); }
  function clk(m){ var h=Math.floor(m/60); return {t:(((h+11)%12)+1)+':'+pad(m%60), pm:h>=12}; }
  /* 10:10-11:00a   (the letter is written once when both ends are the same half of the day) */
  function range(s,e){
    var a=clk(s), b=clk(e);
    return (a.pm===b.pm)?(a.t+'–'+b.t+(b.pm?'p':'a')):(a.t+(a.pm?'p':'a')+'–'+b.t+(b.pm?'p':'a'));
  }
  function keyOf(b){ return (b.getAttribute('data-code')||'')+'|'+(b.getAttribute('data-crn')||''); }
  function whenOf(blocks){
    var by={}, order=[], tag='';
    blocks.forEach(function(b){
      var s=b.getAttribute('data-s'), e=b.getAttribute('data-e'), d=b.getAttribute('data-d');
      if(s==null||e==null||!d){
        tag=b.classList.contains('cal-tbablk')?'Time TBA':(b.classList.contains('cal-anyblk')?'Online, no set time':tag);
        return;
      }
      var k=s+'|'+e;
      if(!by[k]){ by[k]={s:+s,e:+e,days:[]}; order.push(k); }
      if(by[k].days.indexOf(d)<0)by[k].days.push(d);
    });
    if(!order.length)return tag;
    order.sort(function(a,b){ return by[a].s-by[b].s; });
    return order.map(function(k){
      var o=by[k]; o.days.sort(function(a,b){ return DO.indexOf(a)-DO.indexOf(b); });
      return o.days.map(function(d){ return DN[d]||d; }).join('')+' '+range(o.s,o.e);
    }).join(' · ');
  }
  /* The same lookup hzTeachers does: a named instructor, matched to PolyRatings when we can. "Staff" is not a person. */
  function teacher(name){
    name=String(name||'').trim();
    if(!name||/^(staff|tba|to be arranged|to be announced)$/i.test(name))return null;
    var pid=null, p=null;
    try{ pid=(typeof matchProfId==='function')?matchProfId(name):null; }catch(e){}
    try{ if(pid&&typeof PROFESSORS!=='undefined'&&PROFESSORS[pid])p=PROFESSORS[pid]; }catch(e){}
    return {name:name, pid:null, rating:(p&&p.rating!=null)?p.rating:null, evals:(p&&p.evals!=null)?p.evals:null};
  }
  function esc(x){ return (typeof escapeHtml==='function')?escapeHtml(String(x)):String(x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function cardHtml(t,code,when,pos){
    var whenHtml=when?('<div class="hv-when">'+esc(when)+'</div>'):'';
    var style=' style="left:0;top:0;width:'+pos.w+'px"';
    if(t){
      t.ix='hv'; t.codes=[code];
      var h=hzCardHtml(t,{side:'left',y:0,w:pos.w});
      h=h.replace('class="hz-card"','class="hz-card hv-card in"').replace(/style="left:0;top:0px;width:\d+px"/,style.slice(1));
      return h.replace(/<\/div>$/,whenHtml+'</div>');
    }
    return '<div class="hz-card hv-card in" data-hz="hv"'+style+'><div class="hz-row"><span class="hz-av">–</span>'
      +'<span class="hz-who"><span class="hz-nm">Instructor not listed</span><span class="hz-dept">'+esc(code)+'</span></span></div>'+whenHtml+'</div>';
  }
  function hide(host){
    host.classList.remove('hv-live');
    var k=host.querySelectorAll('.hv-svg,.hv-card'); for(var i=0;i<k.length;i++)k[i].parentNode.removeChild(k[i]);
    var m=host.querySelectorAll('.hv-me'); for(var j=0;j<m.length;j++)m[j].classList.remove('hv-me');
  }
  /* One connector between a block and the card, leaving each on the side that faces the other. */
  function link(r,c){
    var ax,ay,bx,by,horiz=true;
    if(c.x>=r.x+r.w-1){ ax=c.x; ay=c.y+c.h/2; bx=r.x+r.w; by=r.y+r.h/2; }
    else if(c.x+c.w<=r.x+1){ ax=c.x+c.w; ay=c.y+c.h/2; bx=r.x; by=r.y+r.h/2; }
    else if(c.y>=r.y+r.h-1){ horiz=false; ax=c.x+c.w/2; ay=c.y; bx=r.x+r.w/2; by=r.y+r.h; }
    else if(c.y+c.h<=r.y+1){ horiz=false; ax=c.x+c.w/2; ay=c.y+c.h; bx=r.x+r.w/2; by=r.y; }
    else return null;
    var reach=horiz?Math.abs(ax-bx):Math.abs(ay-by), kk=Math.min(54,Math.max(10,reach*0.42));
    var d=horiz?(bx>=ax?1:-1):(by>=ay?1:-1);
    return {bx:bx,by:by,d:'M'+ax+','+ay+' C'+(horiz?(ax+d*kk)+','+ay+' '+(bx-d*kk)+','+by:(ax+','+(ay+d*kk)+' '+bx+','+(by-d*kk)))+' '+bx+','+by};
  }
  /* Where the card goes: the empty spot on the week closest to the class, never on top of another class, a work/activity
     block, or the class itself. A packed week with no gap at all falls back to the right edge of the week. */
  function place(host,rects,cw,ch,plan){
    var hb=host.getBoundingClientRect();
    var rel=function(el){ var r=el.getBoundingClientRect(); return {x:r.left-hb.left,y:r.top-hb.top,w:r.width,h:r.height}; };
    var cols=[].slice.call(host.querySelectorAll(plan?'.pl3-col':'.cal-day')).map(rel).filter(function(r){ return r.w>0; });
    if(!cols.length)cols=[{x:0,y:0,w:host.clientWidth,h:host.clientHeight}];
    var x0=Math.min.apply(null,cols.map(function(r){return r.x;})), x1=Math.max.apply(null,cols.map(function(r){return r.x+r.w;}));
    var y0=Math.min.apply(null,cols.map(function(r){return r.y;})), y1=Math.max.apply(null,cols.map(function(r){return r.y+r.h;}));
    var mine=rects.map(function(r){ return {x:r.x-16,y:r.y-8,w:r.w+32,h:r.h+16}; });
    var others=[].slice.call(host.querySelectorAll('.cal-block,.cal-cm,.pl3-blk,.pl3-ghost')).filter(function(el){ return !el.classList.contains('hv-me'); }).map(rel)
      .map(function(r){ return {x:r.x-6,y:r.y-6,w:r.w+12,h:r.h+12}; });
    var obs=mine.concat(others);
    var cx=rects.reduce(function(a,r){return a+r.x+r.w/2;},0)/rects.length, cy=rects.reduce(function(a,r){return a+r.y+r.h/2;},0)/rects.length;
    var best=null, bd=1e12;
    for(var x=x0+4;x<=x1-cw-4;x+=10){
      for(var y=y0+4;y<=y1-ch-4;y+=6){
        var hit=false;
        for(var k=0;k<obs.length;k++){ var o=obs[k]; if(x<o.x+o.w&&x+cw>o.x&&y<o.y+o.h&&y+ch>o.y){ hit=true; break; } }
        if(hit)continue;
        var d=Math.pow(x+cw/2-cx,2)+Math.pow(y+ch/2-cy,2);
        if(d<bd){ bd=d; best={x:x,y:y}; }
      }
    }
    if(best)return best;
    return {x:Math.max(0,x1-cw-2), y:Math.max(y0,Math.min(Math.round(cy-ch/2),y1-ch))};
  }
  function show(host,key){
    hide(host);
    var blocks=[].slice.call(host.querySelectorAll(HV_SEL)).filter(function(b){ return keyOf(b)===key; });
    if(!blocks.length)return;
    var first=blocks[0], code=first.getAttribute('data-code')||'';
    var t=teacher(first.getAttribute('data-prof'));
    var when=whenOf(blocks);
    var plan=host.getAttribute('data-hv')==='plan';
    var hb=host.getBoundingClientRect(), W=host.clientWidth, H=host.clientHeight;
    if(!W||!H)return;
    var rects=blocks.map(function(b){ var r=b.getBoundingClientRect(); return {x:r.left-hb.left,y:r.top-hb.top,w:r.width,h:r.height}; });
    var cw=Math.min(HV_CW,Math.max(110,W-8));
    host.insertAdjacentHTML('beforeend',cardHtml(t,code,when,{w:cw}));
    var card=host.querySelector('.hv-card'); if(!card)return;
    var ch=card.offsetHeight;
    var pos=place(host,rects,cw,ch,plan);
    card.style.left=pos.x+'px'; card.style.top=pos.y+'px';
    var box={x:pos.x,y:pos.y,w:cw,h:ch};
    var col=(t&&t.rating!=null&&typeof scoreColor==='function')?scoreColor(t.rating,'fill'):'var(--muted)';
    var svg='';
    rects.forEach(function(r){
      var l=link(r,box); if(!l)return;
      svg+='<path pathLength="1" style="stroke:'+col+'" d="'+l.d+'"></path>'
        +'<circle cx="'+l.bx+'" cy="'+l.by+'" r="2.8" style="fill:'+col+'"></circle>';
    });
    host.insertAdjacentHTML('afterbegin','<svg class="hv-svg" viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" aria-hidden="true">'+svg+'</svg>');
    blocks.forEach(function(b){ b.classList.add('hv-me'); });
    host.classList.add('hv-live');
  }
  function bind(host){
    if(host._hvB)return; host._hvB=1;
    var cur=null;
    function set(key){ if(key===cur)return; cur=key; if(key==null)hide(host); else show(host,key); }
    host._hvSet=set;
    /* mousemove as well as mouseover: after a resize cleared the card, the next nudge of a still-hovering pointer brings it back */
    var onMove=function(e){
      if(!canHover())return;
      var b=e.target&&e.target.closest?e.target.closest(HV_SEL):null;
      set(b?keyOf(b):null);
    };
    host.addEventListener('mouseover',onMove);
    host.addEventListener('mousemove',onMove);
    host.addEventListener('mouseleave',function(){ set(null); });
    host.addEventListener('focusin',function(e){
      var b=e.target&&e.target.closest?e.target.closest(HV_SEL):null; if(!b)return;
      var vis=false; try{ vis=b.matches(':focus-visible'); }catch(_e){}
      if(vis)set(keyOf(b));
    });
    host.addEventListener('focusout',function(e){ if(!host.contains(e.relatedTarget))set(null); });
    host.addEventListener('keydown',function(e){ if(e.key==='Escape')set(null); });
    /* a tap or click opens the class exactly as before; the overlay just gets out of its way */
    host.addEventListener('click',function(){ set(null); },true);
  }
  /* How many lines of a Plans block's name fit under its code and above its time: measured, never guessed. */
  function fit(host){
    if(host.getAttribute('data-hv')!=='plan')return;
    var phone=false; try{ phone=!!(window.matchMedia&&matchMedia('(max-width:520px)').matches); }catch(e){}
    host.querySelectorAll('.pl3-blk').forEach(function(b){
      var w=b.querySelector('.pl3-nmw'), n=b.querySelector('.pl3-nm'), c=b.querySelector('b'), tm=b.querySelector('.pl3-tm');
      if(!w||!n||!b.clientHeight)return;                      /* not laid out (hidden pane): leave it for the next measure */
      if(phone){ w.style.display=''; w.style.maxHeight=''; return; }
      var cs=getComputedStyle(b), lh=parseFloat(getComputedStyle(n).lineHeight)||13;
      var room=b.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom)-(c?c.offsetHeight:0)-(tm?tm.offsetHeight:0)-2;
      var lines=Math.max(0,Math.min(2,Math.floor(room/lh)));
      if(!lines){ w.style.display='none'; return; }
      w.style.display='block'; w.style.maxHeight=(lines*lh)+'px'; n.style.webkitLineClamp=String(lines);
    });
  }
  function size(host){
    var full=host.clientWidth; if(!full)return;                 /* hidden pane: measured again when it is shown */
    if(host._hvSet)host._hvSet(null);                           /* the week just changed size: an open card would be stale */
    fit(host);
  }
  function watch(host){
    hosts=hosts.filter(function(h){ return h.isConnected; }); hosts.push(host);
    var p=host.parentNode; if(!p)return;
    try{
      if(!ro&&typeof ResizeObserver==='function'){
        ro=new ResizeObserver(function(){
          hosts=hosts.filter(function(h){ return h.isConnected; });
          hosts.forEach(function(h){ try{ size(h); }catch(e){} });
        });
      }
      if(ro)ro.observe(p);
    }catch(e){}
  }
  /* The tall My classes week is decided at render from the window width (> 640px). Cross that line and the week is drawn again. */
  var wide=window.innerWidth>640, rsT=null;
  window.addEventListener('resize',function(){
    clearTimeout(rsT);
    rsT=setTimeout(function(){
      var w=window.innerWidth>640; if(w===wide)return; wide=w;
      try{ if(document.querySelector('.mc-cal[data-hv="mc"]')&&typeof renderMyClasses==='function')renderMyClasses(); }catch(e){}
    },200);
  });
  window.hvMount=function(host,kind){
    if(!host)return;
    if(kind==='plan'&&!host.querySelector('.pl3-blk[data-code]'))return;   /* an empty plan has nothing to point at */
    host.setAttribute('data-hv',kind||'mc'); host.classList.add('hv-host');
    bind(host);
    if(kind==='mc'){
      /* the one number the old layer carried under the week stays */
      try{
        var T=hzTeachers(host);
        if(T.length)host.insertAdjacentHTML('beforeend',hzFootHtml(T,host.getAttribute('data-hz-who'),hzCourseCount(host)).replace('class="hz-foot"','class="hz-foot in"'));
      }catch(e){}
    }
    size(host); watch(host);
    /* the name lines are measured, so measure again once the page font is in */
    try{ if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){ if(host.isConnected)size(host); }); }catch(e){}
  };
})();
</script>
'''
one('<script id="plans-js">', CSS + '<script id="plans-js">')

f.write_text(s)
print('ok')
