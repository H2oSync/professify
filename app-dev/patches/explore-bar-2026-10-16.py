#!/usr/bin/env python3
"""explore-bar, 2026-10-16 (index.html only; no build stamp - the coordinator stamps at merge). Mockup option A, "one quiet row", approved.

1  Explore's filter bar is ONE quiet row under the search field: GEs / My major / Saved as plain text tabs with an underline on the active one
   (no pills), the term as the phone's switch (plain muted bold words + a small up/down icon, one button that flips Spring 2027 <-> Fall 2026),
   and a small Classes | Professors toggle at the right. The Classes | Professors toggle left its tall column beside the search field and now sits in
   the row (search is full width). Phone: the tabs + term share the first line (the tabs scroll sideways if they ever must), the toggle is full width
   on the line under. Every behaviour is as before (filters, default Spring 2027, Fall reads, Saved hidden on Fall, professors mode, aria-pressed
   on tabs and toggle, keyboard); the term control is one button now: .ex-termsw[data-term=spring|now], aria-label "Showing X. Switch to Y".
2  Schedule > My classes: the "Fall 2026 | Spring 2027" pill pair (mcTermChipsHtml) is the same single term switch (.mc-termsw[data-term=term|now]).
   The line under it (the Fall "What you're in now. Read-only here ..." note, the empty-state lines) is untouched.
3  tcTermSw(): ONE helper for that switch (reuses the friend page's .frp-termsw CSS and markup: friend-polish 2026-10-16); the friend page's
   frpTermChipsHtml now calls it too (one implementation), and the switch is 14px everywhere (.frp-termsw was 13px).
4  The Classes | Professors toggle uses ONE neutral highlight in both states (the old purple Professors fill is gone) with a hairline ring so it shows in light mode.
   Focus rings are not clipped (tab padding, the scrolling tab row has room for the ring), the divider before the toggle is its own element (not inside the term button),
   a scrolling tab row fades at its right edge while there is more to scroll. The dead .ex-tsep / .ex-term CSS is removed.

Usage: python3 explore-bar-2026-10-16.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'explore-bar (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


# ---- 1 markup: the search + one row (filters, term, toggle); the toggle leaves its own column
one('''        <div id="exContext" class="ex-filters"></div>
      </div>
''', '''        <div class="ex-bar"><!-- explore-bar (2026-10-16): one quiet row: text tabs, the term switch, the Classes | Professors toggle -->
        <div id="exContext" class="ex-filters"></div>
''')
one('''        <button id="ex-profs" aria-pressed="false" onclick="setExMode('professors')">Professors</button>
      </div>
    </div>
''', '''        <button id="ex-profs" aria-pressed="false" onclick="setExMode('professors')">Professors</button>
      </div>
        </div>
      </div>
    </div>
''')

# ---- 2 Explore: the term is one switch button after the tabs (was two .ex-term pills inside the tabs group)
one('''    g.insertAdjacentHTML('beforeend','<span class="ex-tsep" aria-hidden="true"></span>'
      +'<button type="button" class="ex-term'+(on?'':' on')+'" data-term="spring" aria-pressed="'+(!on)+'" onclick="exSetTerm(\\'spring\\')">'+escapeHtml(mcTermLabel())+'</button>'
      +'<button type="button" class="ex-term'+(on?' on':'')+'" data-term="now" aria-pressed="'+on+'" onclick="exSetTerm(\\'now\\')">'+escapeHtml(mcNowLabel())+'</button>');
''', '''    el.insertAdjacentHTML('beforeend',tcTermSw(on,on?'now':'spring',"exSetTerm('"+(on?'spring':'now')+"')",'ex-termsw')+'<span class="ex-tdiv" aria-hidden="true"></span>');   /* explore-bar (2026-10-16) */
''')

# ---- 3 My classes: the pill pair is the same switch
one('''function mcTermChipsHtml(){
  if(!mcTwoTerms())return '';
  var v=mcTermView();
  return '<div class="mc-viewtog mc-terms" role="group" aria-label="Term">'
    +'<button type="button" aria-pressed="'+(v==='now')+'" class="'+(v==='now'?'on':'')+'" onclick="mcSetTermView(\\'now\\')">'+escAcc(mcNowLabel())+'</button>'
    +'<button type="button" aria-pressed="'+(v==='term')+'" class="'+(v==='term'?'on':'')+'" onclick="mcSetTermView(\\'term\\')">'+escAcc(mcTermLabel())+'</button></div>';
}
''', '''/* explore-bar (2026-10-16): the phone's term switch (exTermCtl / .exterm), as ONE button: the term in plain muted bold words and a small up/down icon;
   a tap flips to the other term. isNow = the now term (Fall 2026) is the one showing; dt = its data-term; act = the onclick that flips it. */
function tcTermSw(isNow,dt,act,cls){
  var L=isNow?mcNowLabel():mcTermLabel(), other=isNow?mcTermLabel():mcNowLabel();
  return '<button type="button" class="frp-termsw '+cls+'" data-term="'+dt+'" onclick="'+act+'" title="'+escAcc('Switch to '+other)+'" aria-label="'+escAcc('Showing '+L+'. Switch to '+other)+'">'+escAcc(L)
    +'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/></svg></button>';
}
function mcTermChipsHtml(){
  if(!mcTwoTerms())return '';
  var v=mcTermView();
  return '<div class="mc-terms" role="group" aria-label="Term">'+tcTermSw(v==='now',v==='now'?'now':'term',"mcSetTermView('"+(v==='now'?'term':'now')+"')",'mc-termsw')+'</div>';
}
''')

# ---- 3b the friend page's switch is the same helper (one implementation)
one('''  var L=(v==='now')?mcNowLabel():mcTermLabel(), other=(v==='now')?mcTermLabel():mcNowLabel();
  return '<span class="frp-terms"><button type="button" class="frp-termsw" data-term="'+(v==='now'?'now':'term')+'" onclick="setFrpTerm(\\''+(v==='now'?'term':'now')+'\\')" '
    +'title="'+escAcc('Switch to '+other)+'" aria-label="'+escAcc('Showing '+L+'. Switch to '+other)+'">'+escAcc(L)
    +'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/></svg></button></span>';
''', '''  return '<span class="frp-terms">'+tcTermSw(v==='now',v==='now'?'now':'term',"setFrpTerm('"+(v==='now'?'term':'now')+"')",'')+'</span>';   /* explore-bar (2026-10-16): one implementation */
''')
one('''color:var(--muted);font:inherit;font-size:13px;font-weight:700;cursor:pointer}''', '''color:var(--muted);font:inherit;font-size:14px;font-weight:700;cursor:pointer}''')

# ---- 3c a scrolling tab row fades at its right edge while there is more to scroll (flag set after every render of the filters)
one('''window.exSetTerm=function(t){''', '''/* explore-bar (2026-10-16): the tab row scrolls sideways on a narrow phone; .ex-more fades its right edge while there is more to see */
function exTabsFade(){
  try{ var g=document.querySelector('#exContext .ex-gesw'); if(!g)return;
    var f=function(){ g.classList.toggle('ex-more',g.scrollWidth>g.clientWidth+1&&g.scrollLeft+g.clientWidth<g.scrollWidth-1); };
    g.onscroll=f; f(); }catch(e){}
}
var _exCtx1=renderExContext;
renderExContext=function(){ var r=_exCtx1.apply(this,arguments); exTabsFade(); return r; };
try{ window.addEventListener('resize',exTabsFade); }catch(e){}
window.exSetTerm=function(t){''')

# ---- 4 CSS (ids beat the older pill / app-layout rules, so the position in the file does not matter). The dead two-pill rules (.ex-tsep, .ex-term) go.
one('''.ex-gesw .ex-tsep{width:1px;align-self:stretch;margin:6px 6px;background:var(--line);flex:none}
''', '''/* explore-bar (2026-10-16): Explore's filters are one quiet row: text tabs (underline on the active), the term switch, a small Classes | Professors toggle */
#view-explore .ex-bar{display:flex;align-items:center;flex-wrap:wrap;gap:6px 12px;border-bottom:1px solid var(--line-soft)}
#view-explore .ex-bar .ex-filters{flex:1 1 auto;min-width:0;display:flex;align-items:center;justify-content:flex-start;gap:12px;margin:0}
#view-explore .ex-bar .ex-gesw{display:flex;flex:0 1 auto;min-width:0;gap:14px;margin:0 0 0 -4px;padding:0;background:none;border:0;border-radius:0;box-shadow:none}
#view-explore .ex-bar .ex-gesw button{flex:none;white-space:nowrap;height:auto;min-height:42px;padding:0 4px;border:0;border-bottom:2px solid transparent;border-radius:0;background:none;box-shadow:none;
  font-size:14px;font-weight:700;color:var(--muted)}
#view-explore .ex-bar .ex-gesw button.on{background:none;color:var(--text);border-bottom-color:var(--tab-on,var(--accent));box-shadow:none}
#view-explore .ex-bar .ex-termsw{margin-left:auto;flex:none;white-space:nowrap;padding:0 2px 0 4px}
#view-explore .ex-bar .ex-tdiv{flex:none;width:1px;height:18px;background:var(--line)}
#view-explore .ex-bar .ex-seg-v{width:auto;flex:none;display:inline-grid;grid-template-columns:1fr 1fr;padding:3px;background:none;border:1px solid var(--line);border-radius:999px;box-shadow:none}
/* ONE neutral highlight in both states (the older rule gave Professors the purple fill: its label was 2:1 on it); a hairline ring so it shows in light mode too */
#view-explore .ex-bar .ex-seg-thumb,#view-explore .ex-bar .ex-seg-v:has(#ex-profs.active) .ex-seg-thumb{left:3px;top:3px;width:calc((100% - 6px)/2);height:calc(100% - 6px);border-radius:999px;background:var(--panel-3);box-shadow:0 0 0 1px var(--line);transform:none}
#view-explore .ex-bar .ex-seg-v:has(#ex-profs.active) .ex-seg-thumb{transform:translateX(100%)}
#view-explore .ex-bar .ex-seg-v button{height:30px;min-height:30px;padding:0 14px;white-space:nowrap;font-size:12.5px;font-weight:700;color:var(--muted)}
#view-explore .ex-bar .ex-seg-v button.active{color:var(--text)}
@media (max-width:640px){
  #view-explore .ex-bar{border-bottom:0;gap:4px 10px}
  #view-explore .ex-bar .ex-filters{flex:1 1 100%;border-bottom:1px solid var(--line-soft)}
  /* the row scrolls sideways if it must: 4px of padding (and -4px margin) leave room for the focus ring, which overflow would clip */
  #view-explore .ex-bar .ex-gesw{gap:10px;padding:4px;margin:-4px 0 -4px -8px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
  #view-explore .ex-bar .ex-gesw::-webkit-scrollbar{display:none}
  #view-explore .ex-bar .ex-gesw.ex-more{-webkit-mask-image:linear-gradient(to right,#000 calc(100% - 26px),transparent);mask-image:linear-gradient(to right,#000 calc(100% - 26px),transparent)}
  #view-explore .ex-bar .ex-tdiv{display:none}
  #view-explore .ex-bar .ex-seg-v{flex:1 1 100%;display:grid;margin:4px 0 6px}
  #view-explore .ex-bar .ex-seg-v button{height:36px;min-height:36px;font-size:13.5px}
}
/* Schedule > My classes: the term is the same one switch, flush left */
#watchMineOut > .mc-terms .mc-termsw{padding-left:0}
''')

# the old two-pill media block (flat, nothing matches .ex-term any more)
one('''@media (max-width:640px){
  #exContext .ex-gesw:has(.ex-term){flex-wrap:wrap;overflow:visible;row-gap:6px}
  #exContext .ex-gesw .ex-tsep{flex:0 0 100%;height:0;margin:0;background:none}
}
''', '')

f.write_text(s)
print('patched', f)
