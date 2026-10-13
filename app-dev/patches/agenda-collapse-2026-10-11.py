#!/usr/bin/env python3
r"""Plans' and My Classes' day cards fold: the days only, a tap opens that day (Tate, 2026-10-11, with a plan's day
list: "also make these all collapsable like just showing the days and then when you click it opens up each day you
click that one opens up" · "make that the same for my classes"). Run AFTER my-classes-agenda-2026-10-11.py.
Usage: python3 agenda-collapse-2026-10-11.py <repo-dir>   (replayable)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label):
    global S
    if S.count(a) != 1: sys.exit(f'{label}: anchor matched {S.count(a)}x')
    S = S.replace(a, b)
rep('  ${days.map(([d, list]) => `<div class="card agenda"><h4>${DAYL[d]}${d === CLOCK.day ? \'<span class="today">Today</span>\' : \'\'}</h4>\n   ${list.map(s => { const fr = friendsInSec(s.id); return `<button class="arow" data-a="secSheet" data-x="${s.code}" data-y="${esc(s.id)}"><span class="tm">${hs(s.s)}<small>${hs(s.e)}</small></span><span class="vb"></span><span class="grow"><span style="font-weight:900;font-size:16px">${s.code}</span>${courseName(s.code) ? `<span class="cn">${esc(courseName(s.code))}</span>` : \'\'}<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))} · ${secSeatText(s)}</span></span>${avStack(fr, 26)}</button>`; }).join(\'\')}</div>`).join(\'\')}', '  ${days.map(([d, list]) => agCard(\'plan\' + S.plan, d, list.length, d === CLOCK.day, \'\', () => list.map(s => { const fr = friendsInSec(s.id); return `<button class="arow" data-a="secSheet" data-x="${s.code}" data-y="${esc(s.id)}"><span class="tm">${hs(s.s)}<small>${hs(s.e)}</small></span><span class="vb"></span><span class="grow"><span style="font-weight:900;font-size:16px">${s.code}</span>${courseName(s.code) ? `<span class="cn">${esc(courseName(s.code))}</span>` : \'\'}<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))} · ${secSeatText(s)}</span></span>${avStack(fr, 26)}</button>`; }).join(\'\'))).join(\'\')}', 'plan days')
rep("/* (2026-10-11) My Classes laid out like Plans", '/* (2026-10-11) Plans\' and My Classes\' day cards fold (Tate: "make these all collapsable like just showing the days and\n   then when you click it opens up each day you click that one opens up" · "make that the same for my classes"):\n   each day shows its name and how many classes; a tap opens that day, another tap closes it. Remembered per plan /\n   term while the app is open. */\nfunction agCard(scope, d, n, today, cls, rows) {\n  UI.agOpen = UI.agOpen || {};\n  const k = scope + \':\' + d, open = !!UI.agOpen[k];\n  return `<div class="card agenda ag-fold${open ? \' open\' : \'\'}${cls ? \' \' + cls : \'\'}"><button class="ag-h" data-a="agDay" data-x="${esc(k)}" aria-expanded="${open}"><h4>${DAYL[d]}${today ? \'<span class="today">Today</span>\' : \'\'}</h4><em>${n} class${n === 1 ? \'\' : \'es\'}</em>${pcChev(open ? 90 : 0)}</button>${open ? rows() : \'\'}</div>`;\n}\n/* (2026-10-11) My Classes laid out like Plans', 'helper')
rep("""  const agenda = days.map(([d, list]) => `<div class="card agenda mine-ag"><h4>${DAYL[d]}${d === CLOCK.day && !o.other ? '<span class="today">Today</span>' : ''}</h4>${list.map(row).join('')}</div>`).join('');""",
    """  const agenda = days.map(([d, list]) => agCard('mine' + o.label, d, list.length, d === CLOCK.day && !o.other, 'mine-ag', () => list.map(s => row(s)).join(''))).join('');""", 'mine days')
rep("""  pcProfNone: () =>""", """  agDay: k => { UI.agOpen = UI.agOpen || {}; UI.agOpen[k] = !UI.agOpen[k]; render(true); },
  pcProfNone: () =>""", 'action')
rep(""".agenda h4{""", """.ag-fold{padding:0}.ag-fold .ag-h{display:flex;align-items:center;gap:10px;width:100%;padding:15px 16px;background:none;border:0;color:inherit;font:inherit;text-align:left;cursor:pointer}
.ag-fold .ag-h h4{flex:1;padding:0;border:0;margin:0}.ag-fold .ag-h em{font-style:normal;font-size:13px;font-weight:800;color:var(--muted)}
.ag-fold.open .ag-h{border-bottom:1px solid var(--line);margin:0 16px;padding:15px 0 12px;width:calc(100% - 32px)}.ag-fold.open{padding-bottom:6px}.ag-fold .arow{margin:0 16px;width:calc(100% - 32px)}
.agenda h4{""", 'css')
# keep My Classes' markup distinct from Plans' (older mutants anchor on Plans' exact words)
rep("""${courseName(s.code) ? `<span class="cn">${esc(courseName(s.code))}</span>` : ''}<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))}${seat(s)}""",
    """${(courseName(s.code) || '') ? `<span class="cn">${esc(courseName(s.code))}</span>` : ''}<span class="muted b" style="display:block;font-size:14px">${esc(profName(s.prof))}${seat(s)}""", 'mine names')
rep("""classes with no set time"><span style="font-weight:900;font-size:16px;margin-right:4px">Anytime</span>${anyItems""",
    """classes with no set time"><span style="margin-right:4px;font-weight:900;font-size:16px">Anytime</span>${anyItems""", 'mine anytime')
open(PA, 'w', encoding='utf-8').write(S); print('agenda-collapse: done')
