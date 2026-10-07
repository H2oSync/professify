#!/usr/bin/env python3
"""The website in the app's look, pass 2: Home's layout (Tate, 2026-10-04: "okay get to work now on each
screens layout").

Pass 1 (desktop-app-look-2026-10-04.py) moved every screen to the app's look; this moves Home's LAYOUT to
the canvas Tate approved ("Desktop in the App's Look", Main artboard). Nothing is added or taken away —
every card, list, button and handler Home had, it still has; only where and how they sit changes:

  - the page: 1240px wide (was 1176), three columns 290 / the feed / 310 (were 250 / 555 / 300); the
    header's row widens to match, so the tabs line up over the right rail.
  - left: the profile card is a white app card (60px circle, name, @username) instead of a blue band;
    "My schedule" gets the app's soft day columns; the no-set-time row is the app's tray.
  - centre: the friends strip is the app's 72px rings; each friend's week is the app's card — 50px
    circle, the name in 18px black, a coloured dot on the "In BUS 4442 till 1:30p" / "No class till ..."
    line, the day labels with today's dot, soft day columns, and every block wide enough to say its code
    AND its time ("10:10–12:00p", the app's format). All the feed's cards share ONE window fitted to the
    hours the feed actually uses (the phone has done this since 2026-09-24); the desktop drew 7AM–10PM on
    every card, mostly empty. One window for all of them, so two friends' weeks still read against each
    other — the reason the frame was fixed in the first place.
  - right: the app's solid 54px Rate button; professors in the app's rating circles with the score as a
    "★ 4.5" chip in that rating's colour (the five-star row under each name is gone — the chip says it).

Usage: python3 desktop-home-layout-2026-10-04.py <repo-dir>   (after desktop-app-look-2026-10-04.py)
"""
import sys, os
d = sys.argv[1]
p = os.path.join(d, 'index.html')
s = open(p, encoding='utf-8').read()
if 'APP-LOOK 2026-10-04' not in s: sys.exit('run desktop-app-look-2026-10-04.py first')
if 'APP-LAYOUT-HOME 2026-10-04' in s: sys.exit('already patched')

R = [
 # one fitted window for the whole feed, on every width (was phones only)
 ("""  try{
    if(window.innerWidth<=640){
      var _wlo=Infinity,_whi=-Infinity;""",
  """  try{
    if(true){   /* every width since 2026-10-04 (the app's layout); was phones only */
      var _wlo=Infinity,_whi=-Infinity;"""),
 ("""  if(opts.win&&opts.win.lo<opts.win.hi&&window.innerWidth<=640){ lo=opts.win.lo; hi=opts.win.hi; }""",
  """  if(opts.win&&opts.win.lo<opts.win.hi){ lo=opts.win.lo; hi=opts.win.hi; }   /* every width since 2026-10-04 */"""),
 # the desktop card is wide enough for the app's scale: about 38px an hour, so a 50-minute class holds its code and time
 ("""  var PPM=HM_CAL_PPM, gridH=Math.round((hi-lo)*PPM), rowH=Math.round(60*PPM);""",
  """  var PPM=(opts.win&&window.innerWidth>640)?HM_FEED_PPM_WIDE:HM_CAL_PPM, gridH=Math.round((hi-lo)*PPM), rowH=Math.round(60*PPM);"""),
 ("""var HM_CAL_PPM=0.47;""",
  """var HM_CAL_PPM=0.47;
var HM_FEED_PPM_WIDE=0.64;   /* the website's feed cards in the app's layout (2026-10-04) */
/* "10:10–11:30a", "1:40–3:00p": the app's gridTime() — minutes always, the a/p once. */
function hmGridTime(a,b){ var f=function(m){ return ((Math.floor(m/60)%12)||12)+':'+String(m%60).padStart(2,'0'); }; return f(a)+'\\u2013'+f(b)+(b>=720?'p':'a'); }"""),
 # hour labels in the app's "9a" form
 ("""    var hr=t/60, lab=(hr%12===0?12:hr%12)+' '+(hr<12||hr===24?'AM':'PM');""",
  """    var hr=t/60, lab=(hr%12===0?12:hr%12)+(hr<12||hr===24?'a':'p');   /* the app's "9a" (2026-10-04) */"""),
 # a block wide and tall enough says its time under its code, like the app's
 ("""        +faces+'</span>'
        /* An explicit clip height""",
  """        +(_ft?'':faces)+'</span>'
        +(_showT?('<span class="cb-time">'+hmGridTime(m.meet.start,m.meet.end)+'</span>'):'')
        +(_ft?('<span class="cb-frow">'+faces+'</span>'):'')
        /* An explicit clip height"""),
 # the time needs its own line; with faces as well, a third — faces move under the time when there is room for all three
 ("""      var faces=(e.lanes===1&&people.length&&h>=16)?hmFaceRow(people):'';""",
  """      var faces=(e.lanes===1&&people.length&&h>=16)?hmFaceRow(people):'';
      var _showT=(window.innerWidth>640&&e.lanes===1&&h>=(faces?58:42)), _ft=!!(faces&&_showT);   /* code / time / faces, the app's three rows (2026-10-04) */"""),
 # today's day label carries the app's dot
 ("""    return '<div class="cal-col"><div class="cal-dh">'+DAY_LABEL[d]+'</div>'
      +'<div class="cal-day" style="height:'+gridH+'px;--calrow:'+rowH+'px">'+html+'</div></div>';""",
  """    var _td=''; try{ _td=['Su','Mo','Tu','We','Th','Fr','Sa'][((typeof hmVisitNow==='function')?hmVisitNow():new Date()).getDay()]; }catch(_t){}
    return '<div class="cal-col"><div class="cal-dh'+(d===_td?' cal-today':'')+'">'+DAY_LABEL[d]+'</div>'
      +'<div class="cal-day" style="height:'+gridH+'px;--calrow:'+rowH+'px">'+html+'</div></div>';"""),
 # the "where they are" line says which kind of line it is, so it can carry the app's coloured dot
 ("""  return '<span class="av-line">'+esc(line+extra)+'</span>';""",
  """  return '<span class="av-line av-'+esc(st.state)+'">'+esc(line+extra)+'</span>';"""),
 # professors: the score as the app's "★ 4.5" chip in the rating's colour
 ("""    ? '<span class="pr-score" style="color:'+scoreColor(rating)+'">'+r5.toFixed(1)+'</span>'""",
  """    ? hmRateChip(rating,r5)"""),
 ("""        +'<span class="pr-score" style="color:'+scoreColor(e.p.rating)+'">'
        +(r5!=null?r5.toFixed(1):'—')+'</span></div>';""",
  """        +(r5!=null?hmRateChip(e.p.rating,r5):'<span class="pr-score">—</span>')+'</div>';"""),
 ("""function hmCurProfRow(r){""",
  """/* The app's rating chip (2026-10-04): "★ 4.5" in the rating's own colour on a tint of its fill. */
function hmRateChip(rating,r5){
  return '<span class="pr-score pr-chip" style="color:'+scoreColor(rating)+';--rcf:'+scoreColor(rating,'fill')+'">'
    +'<span aria-hidden="true">\\u2605</span>'+r5.toFixed(1)+'</span>';
}
try{ window.hmRateChip=hmRateChip; }catch(e){}
function hmCurProfRow(r){"""),
]
for a, b in R:
    if s.count(a) != 1: sys.exit(f'anchor matched {s.count(a)}x: {a[:90]}')
    s = s.replace(a, b)

CSS = """<style id="app-layout-home">
/* ================================================================================================
   APP-LAYOUT-HOME 2026-10-04 — Home in the app's layout (pass 2; the canvas's Main artboard).
   ================================================================================================ */
@media (min-width:1140px){
  .wrap{max-width:1240px}   /* the header's row is a .wrap too, so it widens with the page */
  .wrap.hm-wrap{grid-template-columns:280px minmax(0,1fr) 280px;gap:20px;max-width:1240px;justify-content:stretch}
  #view-sched > .wrap{max-width:1240px}
}
@media (min-width:1300px){
  .wrap.hm-wrap{grid-template-columns:290px minmax(0,1fr) 310px;gap:24px}
}
.hm-wrap{padding-top:20px}
#view-home .hm-rail > *,#view-home .hm-center > * > .hm-card,#view-home #hmFeed > .hm-card{margin-bottom:16px}
#view-home .hm-card{border-radius:24px}

/* ---- left: who you are ---- */
#view-home .hm-id{padding:20px 20px 0}
#view-home .hm-id .idhead{background:none;padding:0;display:flex;align-items:center;gap:14px;color:var(--text)}
#view-home .hm-id .fav{width:60px;height:60px;font-size:20px;font-weight:900;border:0;background:var(--panel-3);color:var(--text-2)}
#view-home .hm-id .idwho .nm{font-size:20px;font-weight:900;color:var(--text);letter-spacing:-.01em;line-height:1.2}
#view-home .hm-id .idun{color:var(--muted);font-size:14px;font-weight:700}
#view-home .hm-id .idun-btn{margin-top:6px;background:var(--blue-soft);color:var(--tab-on);border:0;border-radius:99px;font-size:12.5px;font-weight:900;padding:5px 11px}
#view-home .hm-id .mj{padding:14px 0 18px;font-size:13px;font-weight:700;color:var(--muted)}
#view-home .hm-id .mj-setup{margin:16px -20px 0;width:calc(100% + 40px);padding:14px 20px;background:var(--blue-soft);border:0;border-radius:0}
#view-home .hm-id .mj-setup .mjs-t{font-weight:900}
#view-home .hm-id .mj-setup .mjs-s{color:var(--muted)}
#view-home .hm-id .mjs-a{color:var(--text);opacity:1}
#view-home .hm-id .signin{margin:14px 0 18px}

/* card titles: the app's 18px black */
#view-home .hm-ct{font-size:18px;font-weight:900}
#view-home .hm-ct .hm-more{font-size:13px;font-weight:900;color:var(--tab-on);background:var(--blue-soft);border-radius:99px;padding:5px 11px}

/* ---- left: your week, in the app's soft day columns ---- */
#view-home .hmc-card{padding:18px 16px 0}
#view-home .hmc-card .hm-ct{padding:0 4px}
#view-home .hmc-grid{gap:4px;margin-top:12px}
#view-home .hmc-dh{font-size:11px;font-weight:900;letter-spacing:.05em;color:var(--muted);margin-bottom:6px}
#view-home .hmc-day,#view-home .hmc-col > div:last-child{background:var(--panel-2);border-radius:10px;border:0}
#view-home .hmc-blk{border-radius:7px;font-weight:900}
#view-home .hmc-async{margin:12px 0 0;padding:10px 12px;border:0;border-radius:14px;background:var(--panel-2)}
#view-home .hmc-al{font-size:11px;font-weight:900;letter-spacing:.08em}
#view-home .hmc-ac{background:var(--blk);color:var(--blk-ink);border:0;border-radius:9px;font-weight:900;font-size:12px;padding:5px 9px}
#view-home .hmc-share{margin:14px -16px 0;width:calc(100% + 32px);padding:14px 20px;border-radius:0}

/* ---- centre: the friends strip, the app's 72px rings ---- */
#view-home .hm-strip{gap:14px;padding:2px 2px 4px}
#view-home .hm-fitem{width:74px}
#view-home .hm-fitem .ring{width:72px;height:72px;padding:0;border-width:3.5px}
#view-home .hm-fitem .fav{width:60px;height:60px;font-size:19px;font-weight:900}
#view-home .hm-fitem .nm{font-size:13px;font-weight:900;color:var(--text-2)}

/* ---- centre: a friend's week, the app's card ---- */
#view-home #hmFeed > article.hm-card{padding:18px 20px}
#view-home .hm-fhead{gap:14px;align-items:center;padding-bottom:12px}
#view-home .hm-fhead .fav{width:50px;height:50px;font-size:17px;font-weight:900}
#view-home .hm-fhead .fhead-t .nm{font-size:18px;font-weight:900;color:var(--text)}
#view-home .hm-fhead .fhead-t .ctx{font-size:13px;font-weight:700;color:var(--muted)}
#view-home .av-line{display:flex;align-items:flex-start;gap:6px;font-size:13px;font-weight:800;white-space:normal;overflow:visible;text-overflow:clip}
#view-home .av-line::before{content:"";flex:none;width:8px;height:8px;margin-top:5px;border-radius:50%;background:var(--faint)}
#view-home .av-line.av-class{color:var(--tab-on)}
#view-home .av-line.av-class::before{background:var(--accent)}
#view-home .av-line.av-open{color:var(--good-ink)}
#view-home .av-line.av-open::before{background:var(--good)}

#hmFeed .cal-mini{border:0;border-radius:0;background:none;overflow:visible;gap:2px}
@media (min-width:641px){ #hmFeed .cal-mini{gap:6px} }
#hmFeed .cal-mini .cal-times{width:30px;border:0}
#hmFeed .cal-mini .cal-hr{font-size:11px;font-weight:800;color:var(--faint);right:2px}
#hmFeed .cal-mini .cal-col{border:0}
#hmFeed .cal-mini .cal-dh{height:28px;box-sizing:border-box;align-items:flex-start;padding:2px 0 0;background:none;border:0;font-size:12px;font-weight:900;letter-spacing:.06em;color:var(--muted);position:relative}
#hmFeed .cal-mini .cal-dh.cal-today{color:var(--tab-on)}
#hmFeed .cal-mini .cal-dh.cal-today::after{content:"";position:absolute;left:50%;bottom:6px;width:5px;height:5px;margin-left:-2.5px;border-radius:50%;background:var(--accent)}
#hmFeed .cal-mini .cal-day{background:var(--panel-2);border-radius:12px}
/* the app's wide blocks (code over time) on the website's layout; a phone keeps its compact centred block */
@media (min-width:641px){
#hmFeed .cal-mini .cal-block{border-radius:9px;padding:6px 7px;box-shadow:none;align-items:flex-start;justify-content:flex-start;gap:1px}
#hmFeed .cal-mini .cal-block.narrow{padding:4px 4px}
#hmFeed .cal-mini .cal-block .cb-top{justify-content:flex-start}
#hmFeed .cal-mini .cal-block .cb-code{font-size:13px;font-weight:900;letter-spacing:0}
#hmFeed .cal-mini .cal-block.narrow .cb-code{font-size:11px}
#hmFeed .cal-mini .cal-block .cb-time{font-size:10.5px;font-weight:700;opacity:.9;white-space:nowrap;line-height:1.2}
}
#hmFeed .cal-mini .cal-any{background:none}
/* a narrow day (a 1140px window, or two classes at one hour) keeps the code and the time whole */
#hmFeed .cal-mini .cal-day{container-type:inline-size}
@media (min-width:641px){
@container (max-width:84px){
  #hmFeed .cal-mini .cal-block{padding:5px 5px}
  #hmFeed .cal-mini .cal-block .cb-code{font-size:12px}
  #hmFeed .cal-mini .cal-block .cb-time{font-size:10px;letter-spacing:-.01em}
}
#hmFeed .cal-mini .cal-block .cb-frow{margin-top:auto;display:flex;padding-left:4px}
#hmFeed .cal-mini .cal-block .cb-frow .qw-faces{position:static}
#hmFeed .cal-mini .cal-block:has(.cb-top .qw-faces){padding-right:18px}
#hmFeed .cal-mini .cal-block:has(.cb-top .qw-faces) .cb-code{font-size:11.5px}
}
#hmFeed .qw-note{font-size:13px;font-weight:700}

/* ---- right: today, Rate, professors ---- */
#view-home .hm-td{padding:20px}
#view-home .hm-td-d{font-size:12px;font-weight:900;letter-spacing:.1em;color:var(--muted)}
#view-home .hm-tdg{font-size:25px;font-weight:900;letter-spacing:-.01em;margin-top:4px}
#view-home .hm-ratebtn{min-height:54px;border-radius:18px;font-size:17px;font-weight:900;box-shadow:0 8px 20px rgba(37,99,235,.28)}
:root[data-theme="dark"] #view-home .hm-ratebtn{box-shadow:0 8px 20px rgba(0,0,0,.35)}
#view-home .hm-pcard,#view-home .cp-card{padding:18px 18px 8px}
#view-home .hm-pct{font-size:18px;font-weight:900}
#view-home .hm-prow{gap:12px;padding:10px 0;min-height:62px;border-top:1px solid var(--line-soft)}
#view-home .hm-prow .pr-av,#view-home .cp-narrow .cp-row .pr-av{width:42px;height:42px;border-radius:50%;font-size:14px;font-weight:900}
#view-home .hm-prow .pr-nm{font-size:15px;font-weight:900}
#view-home .hm-prow .pr-dept{font-size:13px;font-weight:800;color:var(--muted)}
#view-home .hm-prow .pr-stars{display:none}
#view-home .pr-score.pr-chip,.pr-chip{margin-left:auto;flex:none;display:inline-flex;align-items:center;gap:3px;font-size:13px;font-weight:900;padding:5px 10px;border-radius:99px;
  background:color-mix(in srgb,var(--rcf) 20%,var(--panel));letter-spacing:0}
:root[data-theme="dark"] .pr-chip{background:color-mix(in srgb,var(--rcf) 16%,var(--panel));color:color-mix(in srgb,var(--rcf) 62%,#fff)!important}   /* the fill lifted toward white: the darker greens alone were under 4.5:1 on the dark tint */
#view-home .cp-rate{height:34px;padding:0 14px;border-radius:17px;border:0;background:var(--clsblk);color:var(--clsblk-ink);font-size:14px;font-weight:900}
/* (last, so it wins over the titles above) */
@media (min-width:1140px) and (max-width:1299px){
  #view-home .hm-ct{font-size:17px}
  #view-home .hm-ct .hm-more{padding:5px 9px;font-size:12.5px}
}
</style>
"""
if s.count('</body>') != 1: sys.exit('body end')
s = s.replace('</body>', CSS + '</body>')
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
