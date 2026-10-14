#!/usr/bin/env python3
"""The website matches the phone in three places the 2026-10-14 audit found (Tate: "make the website match the phone").

1. Friends is pink, as on the phone (friends-search-invite 09-30, friends-one-list 10-03, new-group-text 10-04):
   the Invite pill #DB2777 with white text, "+ New group" in #CC1F6C, the Accept button, the search icon, the unread
   dot, and the request card's pink ring. Scoped to #view-friends (as Explore > Professors has its purple), light and
   dark; dark uses the phone's --pink-t (#F472B6) for text. Fills are #DB2777 under white text (4.6:1).
2. Plans are teal / orange / rose, as on the phone (schedule-share-colour 10-04) and as Home already draws them
   (.hm-plan-A/B/C): the Plans pills, the Builder's "Filling" pills, and on the Plans tab the week's card top edge
   and class blocks (the phone's .plancol: soft2 block, ink text). The chosen pill is filled with the plan colour
   under white text (>= 5.1:1, in dark as well: the phone keeps the same fill).
3. Schedule's tabs are the phone's: My classes / Plans / Builder / Past classes. "Planner" is now "Builder" wherever
   it is visible on this screen (rail, page title "Builder . Spring 2027", empty-state copy, back-chip labels), the
   ids and functions keep their names. "Past classes" is a fourth rail item: setSchedTab('past') (which Hawk's
   go_to uses) still lands on the record (the degree section opens, as it already did), now with that item lit and the title "Past classes".

Usage: python3 website-friends-plans-tabs-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-friends-plans-tabs' in s:
    sys.exit('already patched')

def one(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:120])
    s = s.replace(old, new)

# ---- 3. tabs and labels ----
one('''      <button id="stab-plan" class="wl-tab" onclick="setSchedTab('plan')">Planner<span id="stabPastN"></span></button>
''', '''      <button id="stab-plan" class="wl-tab" onclick="setSchedTab('plan')">Builder</button>
      <button id="stab-past" class="wl-tab" onclick="setSchedTab('past')">Past classes<span id="stabPastN"></span></button>
''')
one("var SCHED_LABEL={mine:'My classes',watch:'Plans',plan:'Planner',past:'Planner'};",
    "var SCHED_LABEL={mine:'My classes',watch:'Plans',plan:'Builder',past:'Past classes'};   /* website-friends-plans-tabs (2026-10-14): the phone's four */")
one("    h.textContent=SCHED_LABEL[t]||SCHED_LABEL.mine;\n",
    "    h.textContent=SCHED_LABEL[t]||SCHED_LABEL.mine;\n"
    "    var _rec=(t==='plan'&&window.schedRecord===true); if(_rec)h.textContent=SCHED_LABEL.past;   /* the Past classes rail item */\n")
one("    if(t!=='past'){\n      var sp=document.createElement('span');",
    "    if(t!=='past'&&!_rec){\n      var sp=document.createElement('span');")
one("lbl='planning '+window.plPlanningLabel();", "lbl=window.plPlanningLabel();")
one("  var _toRecord=(t==='past'); if(_toRecord)t='plan';\n",
    "  var _toRecord=(t==='past'); if(_toRecord)t='plan';\n  window.schedRecord=_toRecord;   /* the record is the lower half of the Builder pane; this says which rail item is lit */\n")
one("[['plan','stab-plan','schedPlanWrap'],['mine','stab-mine','schedMineWrap'],['watch','stab-watch','schedWatchWrap']].forEach(function(x){\n    var btn=document.getElementById(x[1]),box=document.getElementById(x[2]);\n    if(btn)btn.classList.toggle('on',t===x[0]);",
    "[['plan','stab-plan','schedPlanWrap'],['mine','stab-mine','schedMineWrap'],['watch','stab-watch','schedWatchWrap'],['past','stab-past',null]].forEach(function(x){\n    var btn=document.getElementById(x[1]),box=document.getElementById(x[2]);\n    if(btn)btn.classList.toggle('on',x[0]==='past'?_toRecord:(t===x[0]&&!(x[0]==='plan'&&_toRecord)));")
one("planner:'Planner',plan:'Planner'})[t]||'Schedule'};", "planner:'Builder',plan:'Builder'})[t]||'Schedule'};")
one("              plan:'Planner'})[t]||'Schedule'};", "              plan:'Builder'})[t]||'Schedule'};")
one("<span>Planner shows the classes you need and where each one fits.</span>", "<span>Builder shows the classes you need and where each one fits.</span>")
one("Planner couldn’t be drawn just now.", "Builder couldn’t be drawn just now.", 3)
one("Open My planner →", "Open Builder →")
one("Pick your major on My planner and this", "Pick your major in the Builder and this")
one("frToast('Planner cleared — logged Past Classes stay checked.", "frToast('Builder cleared — logged Past Classes stay checked.")

one("      var t=(typeof window.schedTab!=='undefined')?window.schedTab:'mine';\n      return {kind:'sched',tab:t,label:",
    "      var t=(typeof window.schedTab!=='undefined')?window.schedTab:'mine'; if(t==='plan'&&window.schedRecord===true)t='past';   /* Back returns to Past classes */\n      return {kind:'sched',tab:t,label:", 2)
one("if(st&&window.schedTab==='plan')st.textContent='planning '+planningLabel();", "if(st&&window.schedTab==='plan')st.textContent=planningLabel();   /* the title is \"Builder . Spring 2027\" */")

# ---- 2. plan colours: the pills carry the plan, the Plans pane carries the current one ----
one("""class="pl3-pill' + (on ? ' on' : '')""", """class="pl3-pill tcpl-' + s + (on ? ' on' : '')""")
one("""var h = '<div class="pl3">' + (has('regSlotHtml')""", """var h = '<div class="pl3 tcpl-' + slot + '">' + (has('regSlotHtml')""")
one("""return '<button type="button" class="bd-slot' + (sl === cur ? ' on' : '')""", """return '<button type="button" class="bd-slot tcpl-' + sl + (sl === cur ? ' on' : '')""")

CSS = r'''<style id="website-friends-plans-tabs">
/* website-friends-plans-tabs (2026-10-14): Friends is pink; Plans are teal / orange / rose; the phone's plan palette */
.tcpl-A{--pc:#0F766E;--pc-t:#0F766E;--pc-soft:#DDF5F1;--pc-soft2:#BDEBE2;--pc-ink:#115E59}
.tcpl-B{--pc:#C2410C;--pc-t:#C2410C;--pc-soft:#FFEDD5;--pc-soft2:#FED7AA;--pc-ink:#9A3412}
.tcpl-C{--pc:#BE185D;--pc-t:#BE185D;--pc-soft:#FCE7F1;--pc-soft2:#F9CFE2;--pc-ink:#9D174D}
:root[data-theme="dark"] .tcpl-A{--pc-t:#3CC9B8;--pc-soft:#0E2D2B;--pc-soft2:#14403C;--pc-ink:#8FE3D8}
:root[data-theme="dark"] .tcpl-B{--pc-t:#FB9A5B;--pc-soft:#35200F;--pc-soft2:#4A2B13;--pc-ink:#FDBA8C}
:root[data-theme="dark"] .tcpl-C{--pc-t:#F47BA8;--pc-soft:#3A1529;--pc-soft2:#521D39;--pc-ink:#F9B4D6}
@media (prefers-color-scheme:dark){
:root:not([data-theme="light"]):not([data-theme="dark"]) .tcpl-A{--pc-t:#3CC9B8;--pc-soft:#0E2D2B;--pc-soft2:#14403C;--pc-ink:#8FE3D8}
:root:not([data-theme="light"]):not([data-theme="dark"]) .tcpl-B{--pc-t:#FB9A5B;--pc-soft:#35200F;--pc-soft2:#4A2B13;--pc-ink:#FDBA8C}
:root:not([data-theme="light"]):not([data-theme="dark"]) .tcpl-C{--pc-t:#F47BA8;--pc-soft:#3A1529;--pc-soft2:#521D39;--pc-ink:#F9B4D6}}
.pl3-pill[class*="tcpl-"] b::before,.bd-slot[class*="tcpl-"]::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--pc-t);margin-right:6px;vertical-align:1px}
#view-sched .pl3-pill.on[class*="tcpl-"]{background:var(--pc);box-shadow:0 4px 12px rgba(0,0,0,.18)}
#view-sched .pl3-pill.on[class*="tcpl-"] b,#view-sched .pl3-pill.on[class*="tcpl-"] span{color:#fff}
#view-sched .pl3-pill.on[class*="tcpl-"] b::before{background:#fff}
.bd-slot.on[class*="tcpl-"]{background:var(--pc);border-color:var(--pc);color:#fff}
.bd-slot.on[class*="tcpl-"]::before{background:#fff}
#view-sched .pl3[class*="tcpl-"] .pl3-week{box-shadow:var(--card-sh),inset 0 4px 0 var(--pc)}
#view-sched .pl3[class*="tcpl-"] .pl3-blk{background:var(--pc-soft2);color:var(--pc-ink)}

#view-friends{--frp:#DB2777;--frp-t:#CC1F6C;--frp-ring:#FBCFE8}
:root[data-theme="dark"] #view-friends{--frp-t:#F472B6;--frp-ring:rgba(244,114,182,.5)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]):not([data-theme="dark"]) #view-friends{--frp-t:#F472B6;--frp-ring:rgba(244,114,182,.5)}}
#view-friends .frv2-invite{background:var(--frp);color:#fff;box-shadow:0 4px 12px rgba(219,39,119,.25)}
#view-friends .frv2-findico{color:var(--frp-t)}
#view-friends .frv2-find:focus-within{border-color:var(--frp-t);box-shadow:0 0 0 3px rgba(219,39,119,.18)}
#view-friends .fr-secl[onclick^="msgNewConv"]{color:var(--frp-t);font-weight:900}
#view-friends .fr-secl[onclick^="msgNewConv"]::before{content:"+ "}
#view-friends .frv2-card.fr-pending{box-shadow:0 0 0 2px var(--frp-ring)}
#view-friends .frv2-card.fr-pending .frv2-eyebrow{color:var(--frp-t)}
#view-friends .frv2-cact .frv2-go{background:var(--frp);color:#fff}
#view-friends .msg-tdot{background:var(--frp)}
</style>
'''
one('<style id="website-spring-wall">', CSS + '<style id="website-spring-wall">')
f.write_text(s)
print('ok')
