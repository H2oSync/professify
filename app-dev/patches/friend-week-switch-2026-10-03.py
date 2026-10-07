#!/usr/bin/env python3
"""A friend's page: a Fall / A / B switch inside the week card (Tate, 2026-10-03: "i like 2", option 2 of the
"Profile Top and Plans" mockup v2, after "i dont like these mocks lets try taking this out" on the stats row).

Before: name, @handle, a status line, Message beside a "N classes with you" pill; the Fall week; the class
list; and, at the very bottom, a separate "<name>'s plans" card with its own Plan A/B/C pills, grid and list.
Now:
- The header is name, then "@handle · <status>" on one line, then one centred Message button. The pill is
  gone: a class you share already wears the yellow ring on the week (as on Home, since 08:00).
- The week card has a title row: "Fall 2026" (or "Plan A") on the left and a small switch on the right —
  Fall / A / B / C, only the plans they share. Picking a plan draws it on the same grid in the plan's colour,
  with a line under it ("2 classes · 1 with you · 1 no longer listed"), and the class list below follows the
  switch (the plan's sections, "You too" on the ones you're in). The separate plans card is gone.
- No shared plans: no switch, and "No plans shared" in the title row. Plans still loading or failed to load:
  no switch and nothing said (never a false "none").
- The choice is kept per friend (UI.fplan[id]) while the app is open.

Applies after still-need-ge-2026-10-03.py (build 05:15).
Usage: python3 friend-week-switch-2026-10-03.py <repo-dir>   (edits <repo-dir>/app/index.html)
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function friendWeek(' in s: sys.exit('already patched')
R = [
 # 1. CSS: the week card on a friend's page carries both grids now; the switch
 (""".fweek .grid,.fplans .plancol .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}
.tc-sec.fplans{margin-left:12px;margin-right:12px}
.fplans .plancol{margin-left:-16px;margin-right:-16px}
""",
  """.fweek .grid{padding:4px 8px 0;--glab:26px;--ggap:5px}
/* the Fall / A / B switch in a friend's week card (2026-10-03) */
.fwk-h{display:flex;align-items:center;gap:10px;padding:0 12px 8px 16px;min-height:46px}
.fwk-t{flex:1;min-width:0;font-weight:900;font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fsw{display:inline-flex;flex:none;background:var(--bg);border-radius:14px;padding:3px;gap:2px}
.fsw button{min-height:40px;min-width:40px;padding:0 10px;border-radius:11px;font-size:13px;font-weight:900;color:var(--muted)}
.fsw button.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(15,23,42,.1)}
.fsw button.on[class*="plan-"]{color:var(--pc-ink)}
.fwk-n{padding:6px 16px 0;font-size:12.5px;font-weight:800;color:var(--muted)}
"""),
 # 2. the plans card becomes the week card's switch
 ("""function friendPlansCard(id, shared) {
  if (!TC.friendPlans || TC.err.friendPlans) return '';     // not loaded (or failed): say nothing rather than "none"
  const fp = TC.friendPlans[id];
  const slots = fp ? ['A', 'B', 'C'].filter(k => fp[k]) : [];
  if (!slots.length) return `<div class="muted b" style="font-size:13px;padding:12px 16px 0">No shared plans.</div>`;
  UI.fplan = UI.fplan || {};
  const k = slots.includes(UI.fplan[id]) ? UI.fplan[id] : slots[0];
  const ids = fp[k], secs = ids.map(x => Object.prototype.hasOwnProperty.call(SEC, x) ? SEC[x] : null).filter(Boolean), miss = ids.length - secs.length;
  const mine = myCodes(), both = new Set(secs.map(s => s.code).filter(c => mine.has(c)));
  return `<div class="card tc-sec fplans"><div class="tc-sech"><span>${esc(PEOPLE[id].short)}’s plans</span><span class="planpick">${slots.map(x => `<button class="plan-${x} ${x === k ? 'on' : ''}" data-a="friendPlan" data-x="${id}" data-y="${x}" aria-pressed="${x === k}"><i class="pdot"></i>Plan ${x}</button>`).join('')}</span></div>
   <div class="muted b" style="font-size:12.5px;margin-bottom:8px">${secs.length} class${secs.length === 1 ? '' : 'es'} · ${esc(CFG.TERM_LABEL)} sections${miss ? ` · ${miss} no longer listed` : ''}</div>
   ${secs.filter(s => s.s != null).length ? `<div class="plancol plan-${k}">${grid(secs, { sel: S.homeDays['plan:' + id + ':' + k], act: 'homeDay', key: 'plan:' + id + ':' + k, blockAct: 'secSheet', shared: both, one: true, H: 260 })}</div>` : ''}
   ${secs.map(s => `<button class="li" data-a="openClass" data-x="${s.code}"><span class="code">${s.code}</span><span class="grow" style="min-width:0"><span class="b" style="display:block;font-size:14.5px">${esc(course(s.code).short)}</span><span class="muted b" style="font-size:12.5px">${s.sec ? esc(secLabel(s.sec)) + ' · ' : ''}${secWhen(s)} · ${esc(profName(s.prof))}</span></span>${both.has(s.code) ? '<span class="st" style="background:#FEF9C3;color:#A16207">You too</span>' : ''}</button>`).join('')}</div>`;
}""",
  """/* A friend's week card (2026-10-03, Tate's option 2): "Fall 2026" or "Plan A" on the left, a Fall / A / B / C
   switch on the right (only the plans they share), one grid, and the class list under it following the switch. */
function friendWeek(id, secs, shared) {
  const p = PEOPLE[id], loaded = !!TC.friendPlans && !TC.err.friendPlans;   // not loaded (or failed): no switch, and never "none"
  const fp = loaded ? TC.friendPlans[id] : null, slots = fp ? ['A', 'B', 'C'].filter(k => fp[k]) : [];
  UI.fplan = UI.fplan || {};
  const k = slots.includes(UI.fplan[id]) ? UI.fplan[id] : 'now', season = String(CFG.TERM_LABEL).split(' ')[0];
  const sw = slots.length ? `<span class="fsw" role="group" aria-label="Show ${esc(p.short)}’s week or a plan">${['now'].concat(slots).map(x => `<button class="${x === 'now' ? '' : 'plan-' + x}${x === k ? ' on' : ''}" data-a="friendPlan" data-x="${id}" data-y="${x}" aria-pressed="${x === k}" aria-label="${x === 'now' ? esc(CFG.TERM_LABEL) : 'Plan ' + x}">${x === 'now' ? esc(season) : x}</button>`).join('')}</span>`
    : loaded ? '<span class="muted b" style="font-size:12.5px;flex:none">No plans shared</span>' : '';
  const row = (code, sub, mark) => `<button class="li" data-a="openClass" data-x="${code}"><span class="code">${code}</span><span class="grow" style="min-width:0"><span class="b" style="font-size:15px;display:block">${esc(course(code).short)}</span><span class="muted b" style="font-size:12.5px">${sub}</span></span>${mark ? `<span class="st" style="background:#FEF9C3;color:#A16207">${mark}</span>` : ''}</button>`;
  let head, body, list;
  if (k === 'now') {
    const codes = [...new Set(secs.map(s => s.code))];
    head = esc(CFG.TERM_LABEL);
    body = secs.length ? grid(secs, { sel: S.homeDays['f:' + id], act: 'homeDay', key: 'f:' + id, blockAct: 'secSheet', shared, one: true, H: 280 })
      : `<div class="fwk-n" style="padding-top:0">No ${esc(CFG.TERM_LABEL)} sections added.</div>`;
    list = codes.map(code => row(code, secWhen(secs.find(x => x.code === code)), shared.has(code) ? 'Shared' : '')).join('')
      + (p.unplaced || []).map(code => row(code, 'No section yet', shared.has(code) ? 'Shared' : '')).join('')
      + (!codes.length && !(p.unplaced || []).length ? `<div class="empty"><b>No ${esc(CFG.TERM_LABEL)} classes added</b></div>` : '');
  } else {
    const ids = fp[k], ps = ids.map(x => Object.prototype.hasOwnProperty.call(SEC, x) ? SEC[x] : null).filter(Boolean), miss = ids.length - ps.length;
    const mine = myCodes(), both = new Set(ps.map(s => s.code).filter(c => mine.has(c))), n = new Set(ps.map(s => s.code)).size;
    head = 'Plan ' + k;
    body = (ps.some(s => s.s != null) ? `<div class="plancol plan-${k}">${grid(ps, { sel: S.homeDays['plan:' + id + ':' + k], act: 'homeDay', key: 'plan:' + id + ':' + k, blockAct: 'secSheet', shared: both, one: true, H: 280 })}</div>` : '')
      + `<div class="fwk-n">${n} class${n === 1 ? '' : 'es'}${both.size ? ` · ${both.size} with you` : ''}${miss ? ` · ${miss} no longer listed` : ''}</div>`;
    list = ps.map(s => row(s.code, `${s.sec ? esc(secLabel(s.sec)) + ' · ' : ''}${secWhen(s)} · ${esc(profName(s.prof))}`, both.has(s.code) ? 'You too' : '')).join('');
  }
  return `<div class="card fweek" style="margin:18px 12px 0;padding:12px 0 12px"><div class="fwk-h"><span class="fwk-t">${head}</span>${sw}</div>${body}</div>
 ${list ? `<div class="card list" style="margin:12px 12px 0">${list}</div>` : ''}`;
}"""),
 # 3. the header: "@handle · status" on one line, one Message button, no pill; the week card holds the rest
 ("""  <div style="font-size:26px;font-weight:900;margin-top:8px">${esc(p.name)}</div>${p.handle ? `<div class="muted b" style="font-size:14px">@${esc(p.handle)}</div>` : ''}${st && st.free !== null ? `<div class="b" style="color:${st.c || 'var(--muted)'};font-size:14px">● ${esc(st.t)}</div>` : ''}""",
  """  <div style="font-size:26px;font-weight:900;margin-top:8px">${esc(p.name)}</div>${p.handle || (st && st.free !== null) ? `<div class="muted b fhandle" style="font-size:14px">${p.handle ? '@' + esc(p.handle) : ''}${p.handle && st && st.free !== null ? ' · ' : ''}${st && st.free !== null ? `<span style="color:${st.c || 'var(--muted)'}">${esc(st.t)}</span>` : ''}</div>` : ''}"""),
 ("""${isF ? `<button class="pbtn pink" style="height:42px;padding:0 22px" data-a="openChatWith" data-x="${id}">Message</button>` :""",
  """${isF ? `<button class="pbtn pink" style="height:42px;width:200px" data-a="openChatWith" data-x="${id}">Message</button>` :"""),
 ("""${isF ? `<span class="pillchip" style="margin:0">${shared.size} class${shared.size === 1 ? '' : 'es'} with you</span>` : ''}</div></div>""",
  """</div></div>"""),
 (""" ${isF ? `${secs.length ? `<div class="card fweek" style="margin:18px 12px 0;padding:14px 0 12px">${grid(secs, { sel: S.homeDays['f:' + id], act: 'homeDay', key: 'f:' + id, blockAct: 'secSheet', shared, one: true, H: 280 })}</div>` : ''}
 <div class="card list" style="margin:12px 12px 0">${codes.map(code => { const s = secs.find(x => x.code === code); return `<button class="li" data-a="openClass" data-x="${code}"><span class="code">${code}</span><span class="grow"><span class="b" style="font-size:15px;display:block">${esc(course(code).short)}</span><span class="muted b" style="font-size:12.5px">${secWhen(s)}</span></span>${shared.has(code) ? '<span class="st" style="background:#FEF9C3;color:#A16207">Shared</span>' : ''}</button>`; }).join('')}
  ${(p.unplaced || []).map(code => `<button class="li" data-a="openClass" data-x="${code}"><span class="code">${code}</span><span class="grow"><span class="b" style="font-size:15px;display:block">${esc(course(code).short)}</span><span class="muted b" style="font-size:12.5px">No section yet</span></span>${shared.has(code) ? '<span class="st" style="background:#FEF9C3;color:#A16207">Shared</span>' : ''}</button>`).join('')}
  ${!codes.length && !(p.unplaced || []).length ? `<div class="empty"><b>No ${esc(CFG.TERM_LABEL)} classes added</b></div>` : ''}</div>
 ${friendPlansCard(id, shared)}`""",
  """ ${isF ? friendWeek(id, secs, shared)"""),
 # 4. the switch: 'now' is the week
 ("  const st = isF ? status(id) : null;\n  const codes = [...new Set(secs.map(s => s.code))];\n",
  "  const st = isF ? status(id) : null;\n"),
 ("  friendPlan: (id, k) => { UI.fplan = UI.fplan || {}; UI.fplan[id] = k; render(true); },",
  "  friendPlan: (id, k) => { UI.fplan = UI.fplan || {}; UI.fplan[id] = k === 'now' ? null : k; render(true); },"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
