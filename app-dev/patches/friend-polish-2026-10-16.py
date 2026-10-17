#!/usr/bin/env python3
"""friend-polish, 2026-10-16 (index.html only; no build stamp - the coordinator stamps at merge). Three cleanups from Tate's screenshots.

1  A friend's page, Their classes tab. The "Schedule | List" words are gone. In their place a single small icon button (calendar / list
   icon, aria-label "Show as a list" / "Show as a schedule"), kept because the list is the only view that can show a class with no
   confirmed time. "Fall 2026 | Spring 2027" is no longer two pills: it is the phone's Explore term switch (exTermCtl / .exterm) -
   the term in plain muted bold words with the small up/down icon, one button that flips to the other term. Both sit in one row.
2  Home friend card, Spring / plan view. The green "No class left today . both open ..." line is gone from any view that is not the
   current term's real week (hmWhoNow). The header says the term once: "Plan A . Spring 2027 . 3 classes" (or "Spring 2027 . 4 classes"
   for registered Spring classes), plus a single small "New" when the plan/classes are new since you last looked. The second chip that
   repeated the plan/term ("Plan A . Spring 2027", pink "New plan") is gone (hmViewTag and its .hm-fview* CSS are deleted); the Fall view no longer repeats "Fall 2026" as a chip either
   (its line, "Taking 2 classes . Fall 2026", and its free-today line are as before).
3  Story pins on Home. The pin badge on the avatar ring is gone; a pinned friend gets a small pin glyph inline before the name under the
   avatar. Pinned first, the hover pin button, right-click and long-press are untouched.

Usage: python3 friend-polish-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'friend-polish (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


def span(start, end, new):
    """replace from `start` up to (not including) `end`, both exact and unique"""
    global s
    assert s.count(start) == 1 and s.count(end) == 1, (s.count(start), s.count(end), start[:100])
    i = s.index(start); j = s.index(end, i + len(start))
    s = s[:i] + new + s[j:]


# ====================================================================================================== 1  friend page
# the term switch: one button, the phone's look
one("""function frpTermChipsHtml(v){
  return '<div class="frp-view frp-terms"><div class="mc-viewtog" role="group" aria-label="Term">'
    +'<button type="button" aria-pressed="'+(v==='now')+'" class="'+(v==='now'?'on':'')+'" onclick="setFrpTerm(\\'now\\')">'+escAcc(mcNowLabel())+'</button>'
    +'<button type="button" aria-pressed="'+(v==='term')+'" class="'+(v==='term'?'on':'')+'" onclick="setFrpTerm(\\'term\\')">'+escAcc(mcTermLabel())+'</button></div></div>';
}""",
"""function frpTermChipsHtml(v){
  /* friend-polish (2026-10-16): the phone's Explore term switch (exTermCtl): the term as plain muted bold words and a small up/down icon, one
     button that flips to the other term. Was two pills. */
  var L=(v==='now')?mcNowLabel():mcTermLabel(), other=(v==='now')?mcTermLabel():mcNowLabel();
  return '<span class="frp-terms"><button type="button" class="frp-termsw" data-term="'+(v==='now'?'now':'term')+'" onclick="setFrpTerm(\\''+(v==='now'?'term':'now')+'\\')" '
    +'title="'+escAcc('Switch to '+other)+'" aria-label="'+escAcc('Showing '+L+'. Switch to '+other)+'">'+escAcc(L)
    +'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/></svg></button></span>';
}""")

# the term control is part of the classes block now (one row with the view icon), not above the tab body
one("""    ${(mcTwoTerms()&&profileTab!=='took'&&profileTab!=='friends'&&profileTab!=='plans')?frpTermChipsHtml(_tv):''}
    <div class="frp-body">""", """    <div class="frp-body">""")

one("""  const frpToggle=frpCal?`<div class="frp-view"><div class="mc-viewtog">
      <button type="button" class="${frpView==='list'?'':'on'}" onclick="setFrpView('cal')">Schedule</button>
      <button type="button" class="${frpView==='list'?'on':''}" onclick="setFrpView('list')">List</button>
    </div></div>`:'';""",
"""  /* friend-polish (2026-10-16): no "Schedule | List" words. The term switch and ONE small icon button (it shows the view you would switch to). */
  const _frpIc=(frpView==='list')
    ? '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>'
    : '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>';
  const frpToggle=(function(){
    var t=mcTwoTerms()?frpTermChipsHtml(_tv):'';
    var v=frpCal?'<button type="button" class="frp-vsw" data-view="'+(frpView==='list'?'list':'cal')+'" onclick="setFrpView(\\''+(frpView==='list'?'cal':'list')+'\\')" '
      +'title="'+(frpView==='list'?'Show as a schedule':'Show as a list')+'" aria-label="'+(frpView==='list'?'Show as a schedule':'Show as a list')+'"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+_frpIc+'</svg></button>':'';
    return (t||v)?'<div class="frp-view frp-bar">'+t+v+'</div>':'';
  })();""")

one("""    : `<p class="fr-mut frp-none">${first} hasn’t added any classes yet.</p>`;
  const classesBlock=(f.classes||[]).length
    ? frpToggle+((frpCal&&frpView!=='list')
        ? `<div class="frp-cal">${frpCal}</div>${unplacedNote}`
        : listHtml)
    : `<p class="fr-mut frp-none">${first} hasn’t added any classes yet.</p>`;""",
"""    : `<p class="fr-mut frp-none">${first} hasn’t added any classes yet.</p>`;
  const classesBlock=(f.classes||[]).length
    ? frpToggle+((frpCal&&frpView!=='list')
        ? `<div class="frp-cal">${frpCal}</div>${unplacedNote}`
        : listHtml)
    : frpToggle+`<p class="fr-mut frp-none">${first} hasn’t added any classes yet.</p>`;""")

# ====================================================================================================== 2  Home friend card
one("""function hmWhoNow(f){
  var now=""", """function hmWhoNow(f){
  /* friend-polish (2026-10-16): "No class left today" is about THIS term's real week. A Spring view or a plan has no "today". */
  if(f&&f._hm&&f._hm!=='now')return '';
  var now=""")

one("""    +'<span class="ctx">'+hmCtxLine(f,ov)+'</span>'+hmViewTag(f,lift)
""", """    +'<span class="ctx">'+hmCtxLine(f,ov,lift)+'</span>'
""")

one("""function hmCtxLine(f,ov){
  var n=f.classes.length, ovh=ov?' · <b style="color:var(--accent)">'+ov+' with you</b>':'';
  if(!f._hm)return 'Taking '+n+' class'+(n===1?'':'es')+' this term'+ovh;
  var now=f._hm==='now';
  return (now?'Taking ':'Planning ')+n+' class'+(n===1?'':'es')+' · '+esc(now?mcNowLabel():mcTermLabel())+ovh;
}""", """function hmCtxLine(f,ov,lift){
  var n=f.classes.length, ovh=ov?' · <b style="color:var(--accent)">'+ov+' with you</b>':'';
  if(!f._hm)return 'Taking '+n+' class'+(n===1?'':'es')+' this term'+ovh;
  var cnt=n+' class'+(n===1?'':'es');
  if(f._hm==='now')return 'Taking '+cnt+' · '+esc(mcNowLabel())+ovh;
  /* friend-polish (2026-10-16): the plan and the term are said ONCE ("Plan A · Spring 2027 · 3 classes"), and "New" is one small marker */
  var nw=lift?'<span class="hm-fnew" title="'+(lift==='next'?'New Spring classes':'New plan')+'" aria-label="'+(lift==='next'?'New Spring classes':'New plan')+'">New</span>':'';
  return (f._hm==='next'?'':'Plan '+esc(f._hm)+' · ')+esc(mcTermLabel())+' · '+cnt+ovh+nw;
}""")

# hmViewTag is deleted (no callers left): the header line says it once
span("""function hmViewTag(f,lift){""", """/* ---- the lift: who changed since you last opened Home ---- */""", "")

# its CSS: the chip rules; .hm-fnew keeps only the small look of the card-level NEW mark (.hm-newmark), in every theme
one(""".hm-fviews{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.hm-fview,.hm-fnew{display:inline-block;padding:3px 9px;border-radius:12px;font-size:12px;font-weight:700;line-height:1.35}
.hm-fview{background:var(--panel-2);color:var(--text-2)}
.hm-fview-next{background:var(--blue-soft);color:var(--blue-ink)}
.hm-fview-now{background:var(--panel-2);color:var(--text-2)}
.hm-fnew{background:#FCE7F1;color:#9D174D}
""", "")
one(""".hm-fview.hm-plan-A,.hm-fview.hm-plan-B,.hm-fview.hm-plan-C{background:var(--pc-soft);color:var(--pc-ink)}
""", "")
one(""":root[data-theme="dark"] .hm-fview-next{background:#172748;color:#A9C6FF}
:root[data-theme="dark"] .hm-fnew{background:#3A1529;color:#F9B4D6}
""", "")
one("""@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]):not([data-theme="dark"]):not([data-theme="cream"]) .hm-fview-next{background:#172748;color:#A9C6FF}
  :root:not([data-theme="light"]):not([data-theme="dark"]):not([data-theme="cream"]) .hm-fnew{background:#3A1529;color:#F9B4D6}
}
""", "")

# ====================================================================================================== 3  story pins
one("""        +(pin?'<i class="hm-pinbadge" aria-hidden="true">'+pinSvg+'</i>':'')+'</span>'
      +'<span class="nm">'+esc(f.name||'Friend')+'</span></button>'""",
"""        +'</span>'
      +'<span class="nm">'+(pin?'<svg class="hm-pinmark" viewBox="0 0 24 24" width="10" height="10" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6l-1 6 3 3v2H7v-2l3-3z"/><path d="M12 14v7" fill="none"/></svg>':'')+esc(f.name||'Friend')+'</span></button>'""")

one(""".hm-pinbadge{position:absolute;right:-4px;bottom:-4px;width:20px;height:20px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;border:2px solid var(--panel,#fff);font-style:normal;pointer-events:none}
""", """.hm-pinmark{display:inline-block;vertical-align:-1px;margin-right:2px;width:10px;height:10px;color:var(--accent);flex:none}   /* friend-polish (2026-10-16): a pinned story is marked by a small pin before the name, not a badge on the ring */
""")

# ====================================================================================================== css
one("""<!-- website-sync (2026-10-15): pins, saved items""", """<style id="friend-polish-css">
/* friend-polish (2026-10-16) */
/* a friend's page: the term (the phone's Explore switch: muted bold words + up/down icon) and one small view icon, in one row */
.frp-view.frp-bar{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 6px}
.frp-bar .frp-terms{margin:0}
.frp-termsw{display:inline-flex;align-items:center;gap:3px;min-height:40px;padding:0 4px;background:none;border:0;color:var(--muted);font:inherit;font-size:13px;font-weight:700;cursor:pointer}
@media (hover:hover){.frp-termsw:hover,.frp-vsw:hover{color:var(--text)}}
.frp-vsw{margin-left:auto;display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;padding:0;background:none;border:0;border-radius:10px;color:var(--muted);cursor:pointer}
.frp-termsw:focus-visible,.frp-vsw:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:8px}
/* a Home friend card's header line: the plan name is plain words, "New" is one small marker */
.hm-fhead .ctx .hm-fnew{display:inline-block;margin-left:7px;vertical-align:1px;font-size:var(--t-label);font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--tab-on,var(--accent));
  background:rgba(var(--accent-rgb),.14);border-radius:5px;padding:3px 6px;line-height:1}   /* the same small mark the card-level NEW (.hm-newmark) is */
</style>
<!-- website-sync (2026-10-15): pins, saved items""")

f.write_text(s)
print('patched', f)
