#!/usr/bin/env python3
"""check-app.mjs + mutants: the report flow's Planner tests (plannerPlan, plannerRegOpen) read 23:30's plan card
design A (tabs, tiles, week, rows) instead of the card it replaced. What they promise is unchanged. Replayable.
  python3 edit-tests-card-a-flow-2026-10-10.py"""
import sys, os
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, 'check-app.mjs'); s = open(P, encoding='utf-8').read()

def block(a, b, new, what):
    """replace from the line holding `a` through the line holding `b` (first after a)"""
    global s
    L = s.split('\n'); i = [k for k, l in enumerate(L) if a in l]
    if len(i) != 1: sys.exit(f'edit-tests-card-a: "{what}" start found {len(i)}x')
    j = next((k for k in range(i[0], len(L)) if b in L[k]), None)
    if j is None: sys.exit(f'edit-tests-card-a: "{what}" end missing')
    L[i[0]:j + 1] = new.split('\n'); s = '\n'.join(L)

NEW_PLAN = r'''  const v = await page.evaluate(() => { const sc = document.getElementById('scroll'), card = sc.querySelector('.pl-card');
    return { top: (sc.querySelector('.pl-top') || {}).innerText, reg: (sc.querySelector('.pla-reg') || {}).innerText || '', tabs: card && [...card.querySelectorAll('.pla-tab')].map(b => b.innerText.trim() + (b.getAttribute('aria-selected') === 'true' ? '*' : '')).join('|'),
      days: card && [...card.querySelectorAll('.pla-dh span')].map(x => x.innerText).join(), blocks: card && card.querySelectorAll('.pla-blk').length,
      rows: card && [...card.querySelectorAll('.pl-row')].map(r => [(r.querySelector('.pla-code') || {}).innerText, (r.querySelector('.pl-n') || {}).innerText, (r.querySelector('.pl-m') || {}).innerText]),
      tiles: card && [...card.querySelectorAll('.pla-stat')].map(e => e.innerText.replace(/\s+/g, ' ').trim()), edit: card && (card.querySelector('.pl-edit') || {}).innerText, score: !!sc.querySelector('.pk-n, .bar, .pk-score'), behind: /Behind/.test(sc.innerText), seats: /\d+ seats/.test(sc.innerText),
      more: [...sc.querySelectorAll('.pl-picks .pk-card')].map(c => c.innerText.replace(/\s+/g, ' ').trim()), sech: [...sc.querySelectorAll('.pl-sech')].map(s => s.innerText.replace(/\s+/g, ' ').trim()), ledger: !!sc.querySelector('.tc-lrow, .pc-sum'), old: !!sc.querySelector('.pk-hero') }; });
  ok(/Fall 2026/.test(v.top) && /\d+ requirements left/.test(v.top) && /16 units · Edit/.test(v.top) && /^Registration opens Oct 19/.test(v.reg.trim()), 'plan: the top is the term, requirements left and the units pill; registration’s date is its own line', { top: v.top, reg: v.reg });
  ok(v.tabs === 'A · Best fit*|B · Backup|C · Friends', 'plan: Plan A “Best fit” with the A · B · C tabs in the card', v.tabs);
  ok(v.days === 'MON,TUE,WED,THU,FRI' && v.blocks > 0, 'plan: the week has day labels and a block per class meeting', v);
  ok(v.rows.length >= 2 && v.rows.every(([c, n, m]) => /^[A-Z]{2,4} \d{4}[A-Z]?$/.test(c) && n && /^((Mon|Tue|Wed|Thu|Fri|Sat|Sun|[MTWFSU]|Th)(\/(Mon|Tue|Wed|Thu|Fri|Sat|Sun|[MTWFSU]|Th))* \d{1,2}(:\d\d)?[ap]|Online · anytime|Time not posted)/.test(m)), 'plan: one row per class — code, name, when (days and time, online, or time not posted)', v.rows);
  ok(v.tiles.length === 3 && /^Classes \d+/i.test(v.tiles[0]) && v.edit === 'Edit Plan A', 'plan: the tiles (classes, professors, day off) and an Edit Plan A button', { tiles: v.tiles, edit: v.edit });
  ok(!v.score && !v.behind && !v.seats && !v.old && !v.ledger, 'plan: no score numbers, no colour bars, no “Behind”, no seat chips before registration opens, no ledger, no old picks hero', v);
  ok(v.sech[0] === 'More picks' || /^More picks/.test(v.sech[0]), 'plan: “More picks” under the plan', v.sech);
  /* the switch */
  await click(page, '[data-a="plShowPlan"][data-x="B"]'); await tick(page, 300);
  const b = await page.evaluate(() => { const card = document.querySelector('#scroll .pl-card'); return { on: (card.querySelector('.pla-tab[aria-selected="true"]') || {}).innerText, cls: card.className, edit: card.querySelector('.pl-edit') ? card.querySelector('.pl-edit').innerText : (card.querySelector('[data-a="plRedraft"]') || {}).innerText }; });
  ok(b.on && b.on.trim() === 'B · Backup' && /plan-B/.test(b.cls) && /^(Edit Plan B|Draft it for me)$/.test(b.edit), 'plan: the switch shows Plan B (Backup) in the same card', b);'''
block("  const v = await page.evaluate(() => { const sc = document.getElementById('scroll'), card = sc.querySelector('.pl-card');",
      "'plan: the switch shows Plan B (Backup) in the same card', b);", NEW_PLAN, 'plannerPlan card')

# plannerRegOpen: "Registration opens Oct 19" is card A's own amber line now (.pla-reg), under the top
TOP = "(sc.querySelector('.pl-top') || {}).innerText"
if "(sc.querySelector('.pla-reg') || {}).innerText" not in s.split('tests.plannerRegOpen = ')[1].split('\n};')[0]:
    a, rest = s.split('tests.plannerRegOpen = ', 1); body, tail = rest.split('\n};', 1)
    n0 = body.count("(document.querySelector('#scroll .pl-top') || {}).innerText") + body.count(TOP)
    if n0 != 3: sys.exit(f'edit-tests-card-a: plannerRegOpen tops {n0}')
    body = body.replace(TOP, "(sc.querySelector('.pl-top') || {}).innerText + '\\n' + ((sc.querySelector('.pla-reg') || {}).innerText || '')")
    body = body.replace("(document.querySelector('#scroll .pl-top') || {}).innerText", "(document.querySelector('#scroll .pl-top') || {}).innerText + '\\n' + ((document.querySelector('#scroll .pla-reg') || {}).innerText || '')")
    s = a + 'tests.plannerRegOpen = ' + body + '\n};' + tail
# (a first version also added a `reg` key there, which the object's own `reg` overwrote)
s = s.replace("|| ''), reg: (sc.querySelector('.pla-reg') || {}).innerText, rows:", "|| ''), rows:")
open(P, 'w', encoding='utf-8').write(s)

M2 = os.path.join(H, 'mutate.mjs'); t = open(M2, encoding='utf-8').read()
o = '  ["reg: the registration line for any term", "const plRegLine = () => !regOpen() && CFG.TERM_LABEL === CFG.REGISTRATION_TERM ?", "const plRegLine = () => CFG.REGISTRATION_OPENS ?", "plannerRegOpen"],\n'
n = ('  ["reg: the registration line for any term", "  if (regOpen() || CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return \'\';", "  if (!CFG.REGISTRATION_OPENS) return \'\';", "plannerRegOpen"],\n'
     '  ["reg: the registration line stays once it opens", "  if (regOpen() || CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return \'\';", "  if (CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return \'\';", "plannerRegOpen"],\n')
if o in t: t = t.replace(o, n)
elif n not in t: sys.exit('edit-tests-card-a: reg mutant missing')
open(M2, 'w', encoding='utf-8').write(t)
F2 = os.path.join(H, 'dpr-flow-mutants.py'); t = open(F2, encoding='utf-8').read()
o2 = '("' + o.strip()[2:-2] + '),'
n2 = ''.join('  ("' + l.strip()[2:-2] + '),\n' for l in n.strip('\n').split('\n'))
if '  ' + o2 in t: t = t.replace('  ' + o2 + '\n', n2)
elif n2 not in t: sys.exit('edit-tests-card-a: dpr-flow-mutants.py reg mutant missing')
open(F2, 'w', encoding='utf-8').write(t)

# the seat-chip mutant aims at card A's row (the Why sheet's seat line isn't what plannerPlan reads)
old_m = ('  if (regOpen() && sec) out.push(', '  if (sec) out.push(')
new_m = ("${regOpen() ? ' · ' + secSeatText(x) : ''}</span></span>${right}", "${' · ' + secSeatText(x)}</span></span>${right}")
import json
for fn, fmt in [('dpr-flow-mutants.py', lambda a, b: '("plan: seat chips before registration opens", ' + json.dumps(a, ensure_ascii=False) + ', ' + json.dumps(b, ensure_ascii=False) + ', "plannerPlan"),'),
                ('mutate.mjs', lambda a, b: '["plan: seat chips before registration opens", ' + json.dumps(a, ensure_ascii=False) + ', ' + json.dumps(b, ensure_ascii=False) + ', "plannerPlan"],')]:
    F = os.path.join(H, fn); t = open(F, encoding='utf-8').read()
    o, n = fmt(*old_m), fmt(*new_m)
    if o in t: t = t.replace(o, n)
    elif n not in t: sys.exit(f'edit-tests-card-a: {fn} seat mutant missing')
    open(F, 'w', encoding='utf-8').write(t)
print('edit-tests-card-a-flow: done')
