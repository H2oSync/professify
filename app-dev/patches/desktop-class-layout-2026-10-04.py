#!/usr/bin/env python3
"""The website in the app's look, pass 2: the class page's layout (Tate, 2026-10-04: "okay get to work now
on each screens layout"). The canvas's Class artboard, which Tate approved.

  - the hero is the app's blue card: the course code as a white chip, the title in 40px black, the friend /
    took / prereq chips in white on the blue, Save and Send as round buttons, and Units · Sections · Meets ·
    Seats as four soft tiles.
  - each section is the app's row card: the professor in the app's soft purple box (section number over the
    name and its rating), the days and time large, the friend / conflict / plan chips under them, seats on
    the right, then the Plan and In-My-Classes buttons as the app's pills.
  - on a window 1140px and wider the page gets the canvas's right column: "Friends taking it" (each friend,
    and the section number when it is the same as one listed here) and "Who teaches it" (each professor's
    rating circle and "★ 4.5" chip, and how many sections they teach). Both are built from what the page
    already had — friendsInClass() and the sections' own professors — so nothing new is fetched. Under
    1140px the column drops below the sections.

Usage: python3 desktop-class-layout-2026-10-04.py <repo-dir>   (after desktop-home-layout-2026-10-04.py)
"""
import sys, os
d = sys.argv[1]
p = os.path.join(d, 'index.html')
s = open(p, encoding='utf-8').read()
if 'APP-LAYOUT-HOME 2026-10-04' not in s: sys.exit('run desktop-home-layout-2026-10-04.py first')
if 'APP-LAYOUT-CLASS 2026-10-04' in s: sys.exit('already patched')

R = [
 ("""  out.innerHTML=hero+tabs+note
    +'<div class="cp-list">'+shown.map(function(x){return cpSecRow(x,code);}).join('')+'</div>'+foot;
}
window.renderClassPage=renderClassPage;""",
  """  var side=''; try{ side=cpSideHtml(code,secs); }catch(_s){}
  out.innerHTML='<div class="cp-grid'+(side?' has-side':'')+'"><div class="cp-main">'+hero+tabs+note
    +'<div class="cp-list">'+shown.map(function(x){return cpSecRow(x,code);}).join('')+'</div>'+foot+'</div>'
    +side+'</div>';
}
window.renderClassPage=renderClassPage;
/* The class page's right column (the app's layout, 2026-10-04): who you know in it, and who teaches it.
   Built only from what the page already holds — friendsInClass() and the sections' professors. */
function cpSideHtml(code,secs){
  var out='';
  var frs=[]; try{ frs=(typeof friendsInClass==='function')?friendsInClass(code):[]; }catch(_e){}
  if(frs.length){
    var rows=frs.slice(0,8).map(function(f){
      var mine=secs.filter(function(x){ try{ return x.class_nbr&&friendsInSection(code,x.class_nbr).some(function(g){return g.id===f.id;}); }catch(_e){ return false; } })[0];
      var chip=mine?('<span class="cps-sec">'+escapeHtml(cpSecNum(mine))+'</span>'):'';
      return '<button type="button" class="cps-row" onclick="openFriendProfile(\\''+jsAttr(f.id)+'\\')">'
        +'<span class="cps-av" style="background:'+(f.color||'var(--panel-3)')+'">'+((typeof faceHtml==='function')?faceHtml(f):escapeHtml(window.hmIni?hmIni(f.name):String(f.name||'?').slice(0,2).toUpperCase()))+'</span>'
        +'<span class="cps-nm">'+escapeHtml(f.name||'')+'</span>'+chip+'</button>';
    }).join('');
    out+='<section class="cps-card"><h2 class="cps-h">Friends taking it</h2>'+rows
      +(frs.length>8?('<div class="cps-more">and '+(frs.length-8)+' more</div>'):'')+'</section>';
  }
  var profs={}, order=[];
  secs.forEach(function(x){
    var ppl=(x.people&&x.people.length>1)?x.people:[{name:x.name,pid:x.pid,rating:x.rating}];
    ppl.forEach(function(q){
      if(!q||!q.name)return;
      var nm=cpDispName(q.name,q.pid), k=q.pid||nm;
      if(!profs[k]){ profs[k]={name:nm,pid:q.pid,rating:q.rating,n:0}; order.push(k); }
      profs[k].n++;
    });
  });
  if(order.length){
    var prow=order.map(function(k){
      var q=profs[k], r=(q.rating!=null&&isFinite(q.rating))?q.rating:null, r5=(r!=null&&typeof to5==='function')?to5(r):null;
      var tag=q.pid?('button type="button" class="cps-row cps-prof" onclick="openProf(\\''+jsAttr(q.pid)+'\\')"'):'div class="cps-row cps-prof"';
      return '<'+tag+'>'
        +'<span class="cps-pav" style="'+((typeof profTintStyle==='function')?profTintStyle(r):'')+'">'+escapeHtml(window.hmIni?hmIni(q.name):String(q.name).slice(0,2).toUpperCase())+'</span>'
        +'<span class="cps-mid"><span class="cps-nm">'+escapeHtml(q.name)+'</span>'
        +'<span class="cps-sub">'+q.n+' section'+(q.n===1?'':'s')+'</span></span>'
        +(r5!=null&&window.hmRateChip?window.hmRateChip(r,r5):'<span class="cps-none">No ratings</span>')
        +'</'+(q.pid?'button':'div')+'>';
    }).join('');
    out+='<section class="cps-card"><h2 class="cps-h">Who teaches it</h2>'+prow+'</section>';
  }
  return out?('<aside class="cp-side" aria-label="People in '+escapeHtml(code)+'">'+out+'</aside>'):'';
}"""),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)

CSS = """<style id="app-layout-class">
/* ================================================================================================
   APP-LAYOUT-CLASS 2026-10-04 — the class page in the app's layout (the canvas's Class artboard).
   ================================================================================================ */
@media (min-width:1140px){
  .cp-grid.has-side{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:24px;align-items:start}
}
.cp-main{min-width:0}
.cp-side{display:flex;flex-direction:column;gap:16px;margin-top:16px}

/* the hero: the app's blue card */
#view-class .cp-hero{background:#2563EB;color:#fff;border:0;border-radius:28px;padding:26px 28px 24px;box-shadow:0 14px 30px rgba(37,99,235,.25)}
:root[data-theme="dark"] #view-class .cp-hero{box-shadow:0 14px 30px rgba(0,0,0,.4)}
#view-class .cp-htop{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"tile act" "mid mid";gap:14px 18px;align-items:start}
#view-class .cp-tile{grid-area:tile;justify-self:start;width:auto;min-height:0;flex-direction:row;gap:5px;background:#fff;color:#1E40AF;border-radius:10px;padding:6px 12px;font-size:14px;font-weight:900;line-height:1.3}
#view-class .cp-tile span{display:inline}
#view-class .cp-hmid{grid-area:mid;padding:0}
#view-class .cp-title{color:#fff;font-size:40px;font-weight:900;letter-spacing:-.02em;line-height:1.1}
#view-class .cp-hchips{margin-top:12px}
/* chips and tiles darken the blue rather than lighten it, so white text keeps 4.5:1 */
#view-class .cp-hchips > *{background:rgba(15,23,42,.18)!important;color:#fff!important;border-color:transparent!important;box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.35)}
#view-class .cp-hchips > * *:not(.fr-av):not(.fr-av *){color:#fff!important}
#view-class .cp-hact{grid-area:act;gap:10px}
#view-class .cp-nprof{color:#fff;opacity:.92;font-weight:800}
#view-class .cp-save,#view-class .cp-send{width:44px;height:44px;padding:0;justify-content:center;border-radius:50%;border:0;background:rgba(255,255,255,.18);color:#fff}
#view-class .cp-send span{display:none}
#view-class .cp-save.on{background:#fff;color:#1E40AF}
#view-class .cp-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:20px;padding-top:0;border:0}
#view-class .cp-stats{align-items:stretch}
#view-class .cp-st,#view-class .cp-seat-st{background:rgba(15,23,42,.16);border-radius:16px;padding:12px 14px;min-width:0;margin:0;text-align:left;flex:none}
#view-class .cp-st .k{color:#fff;opacity:.92;font-size:11px;font-weight:900;letter-spacing:.09em}
#view-class .cp-st .v,#view-class .cp-st .v.open,#view-class .cp-st .v.wait,#view-class .cp-st .v.full,#view-class .cp-st .v.faint{color:#fff;font-size:20px;font-weight:900;margin-top:2px}
#view-class .cp-meets .v{font-size:16px;line-height:1.3}
#view-class .cp-hwl{color:#fff;opacity:.9;font-size:13px;font-weight:800}

/* the section rows: the app's row card */
#view-class .cp-list{gap:12px}
#view-class .cp-tabs + .cp-list,#view-class .cp-note + .cp-list{margin-top:4px}
#view-class .cp-sec{border:0;border-radius:22px;box-shadow:var(--card-sh);padding:14px 16px 14px 14px;gap:16px}
#view-class .cp-c1{width:250px;background:#F3EEFF;border-radius:16px;padding:10px 14px}
:root[data-theme="dark"] #view-class .cp-c1{background:#271F42}
#view-class .cp-secn{font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
#view-class .cp-profs{margin-top:2px}
#view-class .cp-pn{font-size:15px;font-weight:900;color:#5B21B6}
:root[data-theme="dark"] #view-class .cp-pn{color:#CDB9FF}
#view-class .cp-pn.muted{color:var(--muted)}
#view-class .cp-rt{font-size:15px;font-weight:900}
#view-class .cp-when{font-size:16px;font-weight:900;color:var(--text)}
#view-class .cp-when .cp-ci{display:none}
#view-class .cp-chips{margin-top:8px}
#view-class .cp-so{font-size:15px;font-weight:900}
#view-class .cp-sw{font-size:12px;font-weight:800;color:var(--muted)}
#view-class .cp-c4 .cp-watch,#view-class .cp-c4 .cp-enroll,#view-class .cp-c4 .cp-inmine,#view-class .cp-c4 button{border-radius:99px;font-weight:900}
#view-class .cp-c4 .cp-enroll{background:var(--clsblk);color:var(--clsblk-ink);border:0}
#view-class .cp-sec.clash{box-shadow:var(--card-sh),inset 0 0 0 2px rgba(220,38,38,.4)}

/* the right column */
.cps-card{background:var(--panel);border-radius:24px;box-shadow:var(--card-sh);padding:18px 18px 8px}
.cps-h{margin:0 0 6px;font-size:18px;font-weight:900}
.cps-row{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;border:0;border-top:1px solid var(--line-soft);background:none;padding:8px 0;font:inherit;color:inherit;text-align:left}
button.cps-row{cursor:pointer}
@media (hover:hover){ button.cps-row:hover .cps-nm{color:var(--tab-on)} }
.cps-av{width:40px;height:40px;border-radius:50%;flex:none;display:grid;place-items:center;overflow:hidden;color:#4F4F56;font-weight:900;font-size:14px}
.cps-av img{width:100%;height:100%;object-fit:cover}
.cps-pav{width:42px;height:42px;border-radius:50%;flex:none;display:grid;place-items:center;font-size:14px;font-weight:900;background:var(--panel-3);color:var(--text-2)}
.cps-mid{flex:1;min-width:0;display:flex;flex-direction:column}
.cps-nm{flex:1;min-width:0;font-size:15px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cps-sub{font-size:13px;font-weight:800;color:var(--muted)}
.cps-sec{flex:none;font-size:12px;font-weight:900;padding:4px 10px;border-radius:99px;background:var(--blue-soft);color:var(--tab-on)}
.cps-none{flex:none;font-size:12.5px;font-weight:800;color:var(--muted)}
.cps-more{font-size:13px;font-weight:800;color:var(--muted);padding:8px 0}

@media (min-width:1140px){ .cp-side{margin-top:0} #view-class .has-side .cp-c1{width:210px} #view-class .has-side .cp-sec{gap:14px} }
@media (max-width:840px){
  #view-class .cp-c1{width:auto}
  #view-class .cp-stats{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:640px){
  #view-class .cp-hero{padding:18px;border-radius:22px}
  #view-class .cp-title{font-size:28px}
  #view-class .cp-htop{grid-template-areas:"tile act" "mid mid"}
}
</style>
"""
if s.count('</body>') != 1: sys.exit('body end')
s = s.replace('</body>', CSS + '</body>')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
