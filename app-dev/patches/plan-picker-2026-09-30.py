#!/usr/bin/env python3
r"""Class page: one blue "+" per section; it opens a small "Add to a plan" sheet with Plan A / B / C
and a preview of that plan's week with the new section drawn see-through, so a clash shows before
you add it. (Tate, 2026-09-30: "dont have a specific color maybe make it the regular blue for now and a
small thing pops up saying add, to Plan A, B, C. and you get a preview of what that looks like on the
card it shows the class in a transusive state on the schedule and you can see the other classes to
easily tell if it interferes")

Usage: python3 plan-picker-2026-09-30.py <repo-dir>   (edits <repo-dir>/app/index.html)
Needs section-label-2026-09-30.py first (secLabel). Applied in order; each anchor must match once.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'SHEETS.addPlan' in s: sys.exit('already patched')
if 'function secLabel(' not in s: sys.exit('run section-label-2026-09-30.py first')

SHEET = r'''
/* "Add to a plan" (2026-09-30): pick Plan A, B or C and see that plan's week with this section drawn
   see-through. A clash is drawn red and the Add button says why it can't; the same class in another
   section is shown as the one it replaces. */
SHEETS.addPlan = ({ id, k }) => {
  const s = SEC[id];
  if (!s) return `<div class="row sb"><b>Add to a plan</b><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div><div class="empty"><b>That section is no longer listed.</b></div>`;
  const ids = TC.plans[k] || [], inK = ids.includes(id);
  const others = ids.map(x => SEC[x]).filter(Boolean);
  const replaced = inK ? [] : others.filter(x => x.code === s.code);
  const keep = others.filter(x => x.code !== s.code);
  const clash = inK ? [] : conflicts(keep.map(x => x.id), s);
  const full = !inK && !replaced.length && ids.length >= 12;
  const secs = keep.concat([s]);
  const timed = secs.some(x => !x.async && x.s != null && x.e != null);
  const nm = x => esc(x.code) + (secLabel(x.sec) ? ' ' + esc(secLabel(x.sec)) : '');
  const when = s.async ? 'Online · self-paced' : s.noTime ? 'Time not posted' : `${daysLabel(s.days)} ${range(s)}`;
  const pills = ['A', 'B', 'C'].map(x => { const n = (TC.plans[x] || []).filter(i => SEC[i]).length; const has = (TC.plans[x] || []).includes(id); return `<button class="${x === k ? 'on' : ''} ${has ? 'has' : ''}" data-a="addPlanPick" data-x="${x}" aria-pressed="${x === k}"${has ? ` aria-label="Plan ${x}, has this section"` : ''}>${has ? ic('check', 13, 3) : ''}Plan ${x}<small>${n}</small></button>`; }).join('');
  const note = inK ? `${nm(s)} is already in Plan ${k}.`
    : clash.length ? `<span class="ap-bad">Clashes with ${clash.map(c => `${nm(c)} (${daysLabel(c.days)} ${range(c)})`).join(', ')}</span>`
    : replaced.length ? `Replaces ${nm(replaced[0])} in Plan ${k}.`
    : full ? `Plan ${k} already has 12 sections.`
    : `Fits Plan ${k}.`;
  const btn = inK ? `<button class="btn soft" style="color:#B91C1C" data-a="addPlanGo">Remove from Plan ${k}</button>`
    : clash.length ? `<button class="btn" disabled aria-disabled="true">Clashes — can’t add</button>`
    : full ? `<button class="btn" disabled aria-disabled="true">Plan ${k} is full</button>`
    : `<button class="btn" data-a="addPlanGo">${replaced.length ? 'Switch' : 'Add'} to Plan ${k}</button>`;
  return `<div class="row sb"><span class="b" style="font-size:18px;font-weight:900">Add to a plan</span><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="ap-sec"><span class="code">${esc(s.code)}</span>${secLabel(s.sec) ? ` <b>${esc(secLabel(s.sec))}</b>` : ''} <span class="muted">· ${when} · ${esc(profName(s.prof))}</span></div>
 <div class="ap-pick">${pills}</div>
 <div class="ap-prev">${timed ? grid(secs, { sel: S.homeDays.addprev, act: 'homeDay', key: 'addprev', blockAct: 'none', ghost: inK ? null : id, clash: clash.length > 0, one: true, fit: 30, H: 300 }) : `<div class="empty"><b>Nothing to draw yet</b>${s.async || s.noTime ? 'This section has no set time.' : ''}</div>`}
  ${timed && (s.async || s.noTime) ? `<div class="foot">${esc(s.code)} has no set time, so it isn’t drawn.</div>` : ''}</div>
 <div class="ap-note">${note}</div>
 <div style="display:grid;margin-top:12px">${btn}</div>`;
};
'''

CSS = r'''
/* Class page "+" is always the regular blue (2026-09-30), whatever plan was last picked. */
.secrow .addbtn{background:var(--blue);color:#fff;box-shadow:0 4px 10px rgba(37,99,235,.3)}
.secrow .addbtn.in{background:#fff;color:var(--blue);box-shadow:inset 0 0 0 2.5px var(--blue)}
/* "Add to a plan" sheet: the section being added is drawn see-through; red when it clashes. */
.ap-sec{margin-top:8px;font-size:14px}
.ap-pick{display:flex;gap:8px;margin:14px 0 12px}
.ap-pick button{flex:1;height:40px;border-radius:12px;background:var(--bg);color:var(--ink);font-weight:900;font-size:14px;display:flex;align-items:center;justify-content:center;gap:6px}
.ap-pick button small{font-size:11px;font-weight:800;color:var(--muted)}
.ap-pick button.on{background:var(--blue);color:#fff}
.ap-pick button.on small{color:rgba(255,255,255,.8)}
.ap-pick button.has:not(.on){color:var(--blue-ink);box-shadow:inset 0 0 0 2px var(--blue-soft2)}
/* a sheet that is already open redraws in place: no slide-in again, same scroll */
.sheet.re,.scrim.re{animation:none}
.ap-prev{margin:0 -4px}
.g-b.ghost{background:rgba(37,99,235,.14);color:var(--blue-ink);box-shadow:inset 0 0 0 2px var(--blue);border:0;opacity:.95;z-index:2}
.g-b.ghost.clash{background:rgba(220,38,38,.14);color:#B91C1C;box-shadow:inset 0 0 0 2px #DC2626}
.ap-note{margin-top:10px;font-size:14px;font-weight:800;color:var(--muted)}
.ap-bad{color:#B91C1C}
'''

R = [
 # grid: o.ghost marks the section being previewed (see-through), o.clash turns it red
 ("const cls = ['g-b', wide ? 'wide' : '', live ? 'live' : '', o.shared && o.shared.has(s.code) ? 'shared' : ''].join(' ');",
  "const cls = ['g-b', wide ? 'wide' : '', live ? 'live' : '', o.shared && o.shared.has(s.code) ? 'shared' : '', o.ghost === s.id ? (o.clash ? 'ghost clash' : 'ghost') : ''].join(' ');"),
 # class page: no plan pills; one blue + per section that opens the sheet
 ('<div class="sec-h" style="padding-left:18px"><span>Sections</span><span class="planpick">${[\'A\', \'B\', \'C\'].map(k => `<button class="plan-${k} ${S.plan === k ? \'on\' : \'\'}" data-a="pickPlan" data-x="${k}" aria-pressed="${S.plan === k}"><i class="pdot"></i>Plan ${k}</button>`).join(\'\')}</span></div>',
  '<div class="sec-h" style="padding-left:18px"><span>Sections</span></div>'),
 ("Tap + to add a section to Plan ${S.plan}", "Tap + to add a section to a plan"),
 ("      const inP = plan.includes(s.id), w = !!TC.watches[s.id], closed = s.status === 'full' || s.status === 'wait';",
  "      const inP = ['A', 'B', 'C'].some(k => (TC.plans[k] || []).includes(s.id)), w = !!TC.watches[s.id], closed = s.status === 'full' || s.status === 'wait';"),
 ('<button class="addbtn ${inP ? \'in\' : \'\'}" data-a="addSec" data-x="${esc(s.id)}" aria-label="${inP ? \'Remove from\' : \'Add to\'} Plan ${S.plan}">',
  '<button class="addbtn ${inP ? \'in\' : \'\'}" data-a="addPlanSheet" data-x="${esc(s.id)}" aria-label="${inP ? \'In a plan — change\' : \'Add to a plan\'}">'),
 # addSec takes the plan to add to (default: the last one used)
 ("function addSec(id) {\n  const sec = SEC[id]; if (!sec) return false;\n  const plan = TC.plans[S.plan];\n  if (plan.includes(id)) { TC.setPlan(S.plan, plan.filter(x => x !== id)); toast(`Removed ${sec.code} from Plan ${S.plan}`); render(true); return true; }",
  "function addSec(id, slot) {\n  const sec = SEC[id]; if (!sec) return false;\n  const P = ['A', 'B', 'C'].includes(slot) ? slot : S.plan, plan = TC.plans[P];\n  if (plan.includes(id)) { TC.setPlan(P, plan.filter(x => x !== id)); toast(`Removed ${sec.code} from Plan ${P}`); render(true); return true; }"),
 ("  TC.setPlan(S.plan, next);\n  toast(had ? `Switched to this ${sec.code} section` : `Added ${sec.code} to Plan ${S.plan}`); render(true); return true;\n}",
  "  TC.setPlan(P, next);\n  toast(had ? `Switched to this ${sec.code} section in Plan ${P}` : `Added ${sec.code} to Plan ${P}`); render(true); return true;\n}\n" + SHEET),
 # actions
 ("  addSec: id => addSec(id),",
  "  addSec: id => addSec(id),\n"
  "  addPlanSheet: id => { const hold = ['A', 'B', 'C'].find(x => (TC.plans[x] || []).includes(id)); UI.sheet = { type: 'addPlan', id, k: hold || (['A', 'B', 'C'].includes(S.plan) ? S.plan : 'A') }; S.homeDays.addprev = null; render(true); },\n"
  "  addPlanPick: k => { if (UI.sheet && UI.sheet.type === 'addPlan') { UI.sheet.k = k; render(true); } },\n"
  "  addPlanGo: () => { const sh = UI.sheet; if (!sh || sh.type !== 'addPlan') return; UI.sheet = null; if (addSec(sh.id, sh.k)) { S.plan = sh.k; save(); render(true); } else { UI.sheet = sh; render(true); } },"),
 # render: an already-open sheet of the same kind is redrawn without the slide-in, keeping its scroll
 ("  else if (UI.sheet) sh.innerHTML = `<div class=\"scrim\" data-a=\"closeSheet\"></div><div class=\"sheet\"><div class=\"grab\"></div><div class=\"sbody\">${SHEETS[UI.sheet.type](UI.sheet)}</div></div>`;\n  else sh.innerHTML = '';",
  "  else if (UI.sheet) { const again = sh.dataset.open === UI.sheet.type, ob = sh.querySelector('.sbody'), oy = again && ob ? ob.scrollTop : 0;\n"
  "    sh.innerHTML = `<div class=\"scrim${again ? ' re' : ''}\" data-a=\"closeSheet\"></div><div class=\"sheet${again ? ' re' : ''}\"><div class=\"grab\"></div><div class=\"sbody\">${SHEETS[UI.sheet.type](UI.sheet)}</div></div>`;\n"
  "    if (again) { const nb = sh.querySelector('.sbody'); if (nb) nb.scrollTop = oy; } sh.dataset.open = UI.sheet.type; }\n"
  "  else sh.innerHTML = '';\n  if (UI.champ || !UI.sheet) delete sh.dataset.open;"),
 # CSS, after the planpick rules
 (".planpick button.on{background:var(--blue);color:#fff}", ".planpick button.on{background:var(--blue);color:#fff}" + CSS),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
