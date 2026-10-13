#!/usr/bin/env python3
"""Three small things Tate asked for (2026-10-12).

1. Done, Degree requirements: "is it even necessary to display these at all" — Total Units, Upper Division Units, Units in
   Residence, GPA … are checks the report runs, not classes you take. Done lists only the class-based ones (the writing
   requirement, USCP); the group goes when there are none. An open units line still shows in the Builder's top card.
2. A class page: "for a friend taking a class only have them in the specific section not on the professors thing too" —
   the professor's row loses its faces; each section row keeps its own, and "… are taking this" (with faces) stays on top.
3. Units only: "theres a couple things here i dont even know what they are. also make it compress and expandable" —
   it starts folded ("Units only · 7", a tap opens every one); credit from another school with no catalog name (BUS 3TR,
   AP 300: the report's study-abroad and transfer placeholders) says so, with its term.
Usage: python3 done-classes-section-faces-2026-10-12.py <repo-dir>   (replayable on builder-left-merged-2026-10-12.py)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)

rep("""    const all = X.live.filter(b => pcGroupOf(b) === key); if (!all.length) return '';""",
    """    /* (2026-10-12) units and GPA are the report's checks, not classes: Done lists the writing requirement and USCP only */
    const all = X.live.filter(b => pcGroupOf(b) === key && (key !== 'degree' || /^(gwr|uscp)$/.test(b.kind || ''))); if (!all.length) return '';""", 'done degree')
rep("""<span class="muted">No ratings yet</span>'}</div></div>${avStack(pf, 26)}<span style="color:var(--purple-t,var(--purple))">${ic('chevR', 20)}</span></button>`""",
    """<span class="muted">No ratings yet</span>'}</div></div><span style="color:var(--purple-t,var(--purple))">${ic('chevR', 20)}</span></button>`""", 'prof row faces')
rep("""<div class="muted b" style="font-size:13px">Listed as Staff for now</div></div>${avStack(pf, 26)}</div>`;""",
    """<div class="muted b" style="font-size:13px">Listed as Staff for now</div></div></div>`;""", 'staff row faces')
# and the planning term's page puts each friend on their own section (it only had them on the professor's row)
rep("""      return `<div class="secrow">${secRowT(s)}${secSeatText(s)}""",
    """      const sf = TC.friends.filter(f => personSecs(f).some(x => x.id === s.id));
      return `<div class="secrow">${secRowT(s)}${secSeatText(s)}${sf.length ? `<span class="sec-fr">${avStack(sf, 22)}</span>` : ''}""", 'term section faces')
rep("""  const unitsOnly = rest.length ? `<div class="card pc-oth"><div class="pc-hd"><span>Units only</span><em>${rest.length}</em></div><div class="muted b" style="font-size:12.5px;margin:-2px 0 6px">On your record, counted for no requirement</div>${(UI.pcAll ? rest : rest.slice(0, 4)).map(h => { const code = pcK(h.code); return `<div class="pc-orow"><div class="pc-tx"><button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}"><span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(courseName(code))}</span></button>${pcLine(code, histNotDone(h) ? 'taking' : 'done', h)}${histNotDone(h) ? pcNowTag : ''}</div></div>`; }).join('')}${rest.length > 4 && !UI.pcAll ? `<button class="pc-more" data-a="pcAll">See all ${rest.length}</button>` : ''}</div>` : '';""",
    """  /* (2026-10-12) folded until tapped; a placeholder from another school (BUS 3TR, AP 300) says what it is */
  const uOpen = !!UI.pcAll;
  const xLine = h => `<span class="pc-pf">Credit from another school${h.term && h.year ? ' · ' + esc(h.term + ' ' + h.year) : ''}</span>`;
  const unitsOnly = rest.length ? `<div class="card pc-oth pc-uo"><button class="pc-uh" data-a="pcUnits" aria-expanded="${uOpen}"><span class="pc-tt"><b>Units only</b><span>${rest.length} on your record, counted for no requirement</span></span>${pcChev(uOpen ? 90 : 0)}</button>${uOpen ? rest.map(h => { const code = pcK(h.code); return `<div class="pc-orow"><div class="pc-tx"><button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}"><span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(courseName(code))}</span></button>${pcXfer(h) && !courseName(code) ? xLine(h) : pcLine(code, histNotDone(h) ? 'taking' : 'done', h)}${histNotDone(h) ? pcNowTag : ''}</div></div>`; }).join('') : ''}</div>` : '';""", 'units only')
rep("  pcAll: () => { UI.pcAll = true; render(true); },", "  pcAll: () => { UI.pcAll = true; render(true); },\n  pcUnits: () => { UI.pcAll = !UI.pcAll; render(true); },", 'pcUnits action')
rep(".pc-orow{border-top:1px solid var(--line);padding:4px 0}", """.pc-orow{border-top:1px solid var(--line);padding:4px 0}
.pc-uo{padding:4px 16px}
.pc-uh{display:flex;align-items:center;gap:12px;width:100%;min-height:62px;text-align:left}
.pc-uh .pc-tt{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.pc-uh b{font-size:16px;font-weight:900}
.pc-uh .pc-tt span{font-size:13px;font-weight:800;color:var(--muted)}
.pc-uo .pc-orow:last-child{padding-bottom:8px}
.secrow .sec-fr{flex:none;display:inline-flex;margin-left:6px}""", 'units css')
open(PA, 'w', encoding='utf-8').write(S); print('done-classes-section-faces: done')
