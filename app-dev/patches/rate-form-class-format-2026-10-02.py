#!/usr/bin/env python3
r"""Rate form: the class's name, no "RATE A PROFESSOR", and Format as In person / Online / Async.
(Tate, 2026-10-02: "somewhere on the rating we should have the actual class name so maybe once you
click a professor, also take out when it says rate a professor. for format have it in person, asynch
and online also give the opportunity to click online and in person having both clicked but not asynch
and in person.")

- Class row: "BUS 3438 · Fall 2026" with the class's name under it (courseName(), from
  planner-names-quick-tick; nothing shown when no source names it). With several classes to pick from,
  the picked one's name shows under the chips.
- The "RATE A PROFESSOR" eyebrow is gone. Editing keeps "EDIT YOUR REVIEW OF" — the form still says
  which job it is doing (the 2026-09-19 rule).
- Format: In person, Online, Async — tap to turn each on or off. In person + Online can both be on
  (saved as "Hybrid", the desktop's own word for it); Async and In person can't (turning one on turns
  the other off). Saved values: "In person", "Online", "Asynchronous", "Hybrid", "Online and
  asynchronous" — reviews.format is free text and the desktop shows it as written. A saved review
  reads back into the same chips.

Usage: python3 rate-form-class-format-2026-10-02.py <repo-dir>. Run after planner-names-quick-tick.
"""
import sys, os
p = os.path.join(sys.argv[1], 'app', 'index.html')
s = open(p, encoding='utf-8').read()
if 'function fmtSet(' in s: sys.exit('already patched')
if 'function courseName(' not in s: sys.exit('run planner-names-quick-tick first')
R = [
 ("<div class=\"grow\"><div class=\"eyebrow\">${d.editing ? 'EDIT YOUR REVIEW OF' : 'RATE A PROFESSOR'}</div>",
  "<div class=\"grow\">${d.editing ? '<div class=\"eyebrow\">EDIT YOUR REVIEW OF</div>' : ''}"),
 ("   <div class=\"frow2\">${codes.length > 1 ? `<div class=\"flabel\" style=\"margin-bottom:10px\">Class</div>${sg('code', codes, null, true)}` : `<div class=\"row sb\"><span class=\"flabel\">Class</span><span class=\"b\" style=\"color:var(--ink3)\">${esc(d.code || '')}${d.term ? ' · ' + esc(d.term) : ''}</span></div>`}</div>",
  "   <div class=\"frow2\">${codes.length > 1 ? `<div class=\"flabel\" style=\"margin-bottom:10px\">Class</div>${sg('code', codes, null, true)}${d.code && courseName(d.code) ? `<div class=\"b rf-cname\" style=\"margin-top:8px\">${esc(courseName(d.code))}</div>` : ''}` : `<div class=\"row sb\" style=\"align-items:flex-start;gap:12px\"><span class=\"flabel\">Class</span><span class=\"b\" style=\"color:var(--ink3);text-align:right\">${esc(d.code || '')}${d.term ? ' · ' + esc(d.term) : ''}${d.code && courseName(d.code) ? `<span class=\"rf-cname\" style=\"display:block\">${esc(courseName(d.code))}</span>` : ''}</span></div>`}</div>"),
 ("   <div class=\"frow2\"><div class=\"flabel\" style=\"margin-bottom:10px\">Format</div>${sg('format', ['In person', 'Hybrid', 'Online'])}</div>",
  "   <div class=\"frow2\"><div class=\"row sb\" style=\"margin-bottom:10px\"><span class=\"flabel\">Format</span><span class=\"hint\" style=\"color:var(--muted)\">In person + Online = hybrid</span></div><div class=\"sg fmt\">${FMT_CHIPS.map(([v, l]) => { const on = fmtSet(d.format).includes(v); return `<button class=\"${on ? 'on' : ''}\" data-a=\"fmtTog\" data-x=\"${v}\" aria-pressed=\"${on}\">${l}</button>`; }).join('')}</div></div>"),
 ("SCREENS.rateForm = () => {",
  "/* Format, as chips that combine (Tate, 2026-10-02): In person + Online = \"Hybrid\" (the desktop's word);\n"
  "   Async never goes with In person. reviews.format stays one string. */\n"
  "const FMT_CHIPS = [['In person', 'In person'], ['Online', 'Online'], ['Asynchronous', 'Async']];\n"
  "function fmtSet(f) { return f === 'Hybrid' ? ['In person', 'Online'] : f === 'Online and asynchronous' ? ['Online', 'Asynchronous'] : FMT_CHIPS.some(c => c[0] === f) ? [f] : []; }\n"
  "function fmtOf(set) { const h = v => set.includes(v); return h('In person') && h('Online') ? 'Hybrid' : h('Online') && h('Asynchronous') ? 'Online and asynchronous' : set[0] || null; }\n"
  "SCREENS.rateForm = () => {"),
 ("  draft: (k, v) => {",
  "  fmtTog: v => { const d = S.draft; let set = fmtSet(d.format); set = set.includes(v) ? set.filter(x => x !== v) : set.concat(v);\n"
  "    if (v === 'Asynchronous' && set.includes(v)) set = set.filter(x => x !== 'In person');\n"
  "    if (v === 'In person' && set.includes(v)) set = set.filter(x => x !== 'Asynchronous');\n"
  "    d.format = fmtOf(set); d.err = ''; draftSave(); render(true); },\n"
  "  draft: (k, v) => {"),
 (".rscore{", ".rf-cname{font-size:13.5px;color:var(--muted);font-weight:800;margin-top:2px}\n.sg.fmt button{height:44px}\n.rscore{"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor matched {n}x: {a[:90]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('patched', p)
