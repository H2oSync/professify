#!/usr/bin/env python3
"""The Planner's plan card, design A (Tate, 2026-10-09: "I like A. lets do that", from the Spring 2027 Planner
Card canvas, after "lets redesign how spring 2027 page looks").

- Registration: an amber line under the header, "Registration opens Oct 19 · in 10 days", until it opens.
- Plans: A · Best fit, B · Backup, C · Friends as three full-width tabs, 44px tall.
- Three tiles: CLASSES (with the units when TermChamp knows them), PROFESSORS (the average rating), DAY OFF
  (the weekdays with no class).
- The week you can read: Mon–Fri columns over the hours the plan uses, every class a labelled block (its
  number and start time) that opens the section; a weekday with no class says FREE.
- Anytime: classes with no set weekday time (online, time not posted, weekend-only) as chips under the week.
- Each class: its code, name, days and time (with GE and seats as before), and on the right its
  professor's rating in the rating colour with their last name. The "— u" units column is gone.
- Edit Plan A stays. Friends, seats at risk and Only you stay as small chips when they apply.

Usage: python3 spring-card-a-2026-10-09.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'spring-card-a (2026-10-09)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# the card
i = s.index('function planCard(k, L, R, why) {')
j = s.index('function pickCard(c) {')
old_card = s[i:j]
assert "const head = `<div class=\"pl-head\">" in old_card and 'pl-wk' in old_card
new_card = r'''/* The plan card, design A (spring-card-a (2026-10-09)): named A/B/C tabs, three tiles, a week you can read,
   an Anytime tray, then each class with its professor's rating. */
const PL_NAME = { A: 'Best fit', B: 'Backup', C: 'Friends' };
const plOnWeek = s => !!s && !s.async && s.s != null && s.e != null && [...String(s.days || '')].some(d => DAYS.includes(d));
function planTabs(k) {
  return `<div class="pla-tabs" role="tablist" aria-label="Plan">${['A', 'B', 'C'].map(x => `<button class="pla-tab${x === k ? ' on' : ''}"${x === k ? ` style="background:${PL_COL[x]};color:#fff"` : ''} data-a="plShowPlan" data-x="${x}" role="tab" aria-selected="${x === k}">${x} · ${PL_NAME[x]}</button>`).join('')}</div>`;
}
/* "Registration opens Oct 19 · in 10 days", until it opens (the plan's term only) */
function plRegBanner() {
  if (regOpen() || CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return '';
  const days = Math.round((Date.parse(CFG.REGISTRATION_OPENS + 'T12:00:00Z') - Date.parse(sloISO() + 'T12:00:00Z')) / 864e5);
  return `<div class="pla-reg" role="note">${ic('cal', 16, 2.4)}<span>Registration opens ${esc(regOpensText())}${days > 0 ? ` · in ${days} day${days === 1 ? '' : 's'}` : ''}</span></div>`;
}
function planCard(k, L, R, why) {
  const secs = planSecsOf(k), st = planStats(k, L), col = PL_COL[k], head = planTabs(k);
  if (TC.err.plans) return `<div class="card pl-card pla plan-${k}">${head}<div class="pl-empty">Couldn’t load your plans, so nothing was drafted.</div><div class="pl-chips"><button class="btn soft" data-a="plRetryPlans" ${UI.busy.plans ? 'disabled' : ''}>${UI.busy.plans ? 'Loading…' : 'Try again'}</button></div></div>`;
  if (!secs.length) {
    if (why === 'nodata') return `<div class="card pl-card pla plan-${k}">${head}<div class="pl-empty">Plan ${k} drafts itself once TermChamp has your past classes — upload your report or add them in Past classes.</div></div>`;
    return `<div class="card pl-card pla plan-${k}">${head}<div class="pl-empty">${k === 'A' ? 'Nothing fits yet — add classes from the picks below.' : `Plan ${k} is empty.`}</div><div class="pl-chips"><button class="btn soft" data-a="plRedraft" data-x="${k}">Draft it for me</button></div></div>`;
  }
  const timed = secs.filter(plOnWeek), any = secs.filter(s => !plOnWeek(s));
  /* the tiles */
  const offN = st.off.length, off = timed.length ? (offN ? st.off.map(d => DAYN[d]).join(', ') : 'None') : '—';
  const uw = n => n === 1 ? 'unit' : 'units', units = !st.unknown ? `${st.units} ${uw(st.units)}` : st.units ? `${st.units}+ units` : '';
  const avgT = st.avg != null ? rateTone(st.avg) : null;
  const tiles = `<div class="pla-stats"><div class="pla-stat"><span>Classes</span><b>${st.n}</b>${units ? `<i>${units}</i>` : ''}</div><div class="pla-stat"><span class="pla-wide">Professors</span><span class="pla-narrow">Rating</span><b>${st.avg != null ? `<em class="pla-star" aria-hidden="true" style="color:${avgT ? avgT.ink : 'inherit'}">★</em> ${st.avg.toFixed(1)}` : '—'}</b>${st.avg != null ? '<i>average</i>' : ''}</div><div class="pla-stat"><span>${offN > 1 && timed.length ? 'Days off' : 'Day off'}</span><b class="${offN > 1 ? 'sm' : ''}">${esc(off)}</b></div></div>`;
  /* the week: Mon–Fri over the hours the plan uses (at least four), each class a labelled block */
  let week = '';
  if (timed.length) {
    /* the hours the plan uses (at least four, never past midnight), tall enough that a 50-minute class keeps its time */
    const [lo, hi] = gridSpan(timed, 240), H = Math.max(208, Math.min(380, Math.round((hi - lo) / 60 * 34))), px = m => (m - lo) / (hi - lo) * H, ticks = [];
    for (let t = Math.ceil((lo + 1) / 120) * 120; t < hi; t += 120) ticks.push(t);
    const used = d => timed.some(x => x.days.includes(d));
    const cols = PL_DAYS.map(([d, nm]) => {
      const day = timed.filter(x => x.days.includes(d)).sort((a, b) => a.s - b.s || a.e - b.e);
      if (!day.length) return `<div class="pla-col pla-free"><span>Free</span></div>`;
      /* classes that overlap share the column side by side, never on top of each other */
      const lanes = [], lane = new Map();
      day.forEach(x => { let l = lanes.findIndex(end => end <= x.s); if (l < 0) { l = lanes.length; lanes.push(0); } lanes[l] = x.e; lane.set(x, l); });
      const n = lanes.length;
      return `<div class="pla-col">${day.map(x => { const h = Math.max(18, px(x.e) - px(x.s)), top = Math.max(0, Math.min(px(x.s), H - h)), num = x.code.split(' ').slice(1).join(' ') || x.code, l = lane.get(x);
        return `<button class="pla-blk" style="top:${top.toFixed(1)}px;height:${h.toFixed(1)}px;left:calc(${(l * 100 / n).toFixed(3)}% + 2px);width:calc(${(100 / n).toFixed(3)}% - 4px);background:${col}" data-a="secSheet" data-x="${esc(x.code)}" data-y="${esc(x.id)}" aria-label="${esc(x.code)}, ${DAYN[d]} ${hs(x.s)}"><b>${esc(n > 1 ? num.replace(/^(\d{2}).*/, '$1…') : num)}</b>${h >= 29 && n === 1 ? `<i>${hs(x.s)}</i>` : ''}</button>`; }).join('')}</div>`;
    }).join('');
    week = `<div class="pla-week" role="group" aria-label="Plan ${k} week"><div class="pla-dh" aria-hidden="true">${PL_DAYS.map(([d, nm]) => `<span class="${used(d) ? '' : 'free'}">${nm}</span>`).join('')}</div><div class="pla-grid" style="height:${H}px">${ticks.map(t => `<span class="pla-ax" style="top:${px(t).toFixed(1)}px" aria-hidden="true">${hs(t)}</span><i class="pla-hl" style="top:${px(t).toFixed(1)}px"></i>`).join('')}<div class="pla-cols">${cols}</div></div></div>`;
  }
  /* Anytime: no set weekday time */
  const anyTxt = x => x.async ? 'online' : x.s == null ? 'time not posted' : daysLabel(x.days) + ' ' + hs(x.s);
  const wkend = x => [...String(x.days || '')].filter(d => d === 'S' || d === 'U').join('');
  const trayItems = any.map(x => [x, anyTxt(x)]).concat(timed.filter(x => wkend(x)).map(x => [x, daysLabel(wkend(x)) + ' ' + hs(x.s)]));
  const tray = trayItems.length ? `<div class="pla-any"><span class="pla-anyl">${any.length ? 'Anytime' : 'Weekend'}</span>${trayItems.map(([x, t]) => `<button class="pla-chip" data-a="secSheet" data-x="${esc(x.code)}" data-y="${esc(x.id)}">${esc(x.code)} · ${esc(t)}</button>`).join('')}</div>` : '';
  /* each class, with its professor's rating on the right */
  const rows = secs.slice().sort((a, b) => (a.s == null ? 9999 : a.s) - (b.s == null ? 9999 : b.s) || a.code.localeCompare(b.code)).map(x => {
    const r = ratingOf(x.prof), t = rateTone(r), c = R ? R.all.find(y => y.code === x.code) : null, ge = c && c.fills && c.fills.find(b => b.kind === 'ge' && b.ge);
    const who = x.prof ? esc(profName(x.prof).split(' ').slice(-1)[0]) : '';
    const right = t ? `<span class="pla-rt"><b style="color:${t.ink}">★ ${r.toFixed(1)}</b>${who ? `<small>${who}</small>` : ''}</span>` : who ? `<span class="pla-rt"><small>${who}</small></span>` : '';
    return `<button class="pl-row" data-a="secSheet" data-x="${esc(x.code)}" data-y="${esc(x.id)}"><span class="code pla-code">${esc(x.code)}</span><span class="pl-t"><span class="pl-n">${esc(courseName(x.code) || course(x.code).title)}</span><span class="pl-m">${x.async ? 'Online · anytime' : x.s == null ? 'Time not posted' : `${daysLabel(x.days)} ${hs(x.s)}`}${ge ? ` · GE ${esc(ge.ge)}` : ''}${regOpen() ? ' · ' + secSeatText(x) : ''}</span></span>${right}</button>`;
  }).join('');
  const extra = [st.friends ? `${st.friends} friend${st.friends === 1 ? '' : 's'}` : '', st.risky ? `${st.risky} at risk` : '', TC.planShared[k] === false ? 'Only you' : ''].filter(Boolean).map(x => `<span class="chip pl-chip">${esc(x)}</span>`).join('');
  return `<div class="card pl-card pla plan-${k}">${head}${tiles}${week || tray ? `<div>${week}${tray}</div>` : ''}<div class="pl-rows">${rows}</div>${extra ? `<div class="pl-chips">${extra}</div>` : ''}<button class="btn pl-edit" style="background:${col}" data-a="plEditPlan" data-x="${k}">Edit Plan ${k}</button></div>`;
}
'''
s = s[:i] + new_card + s[j:]

# the header: the registration date moves to its own amber line
one("""  return `<div class="pl-top"><div>${term}<div class="pl-sub">${R.left} requirement${R.left === 1 ? '' : 's'} left${plRegLine()}</div></div><button class="pl-pill" data-a="plPrefsOpen" aria-label="${esc(w)} · ${plUnitsTarget()} units · Edit">${plUnitsTarget()} units · Edit</button></div>""",
    """  return `<div class="pl-top"><div>${term}<div class="pl-sub">${R.left} requirement${R.left === 1 ? '' : 's'} left</div></div><button class="pl-pill" data-a="plPrefsOpen" aria-label="${esc(w)} · ${plUnitsTarget()} units · Edit">${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}""")

one(""".pl-edit{height:48px;border-radius:16px;font-size:16px;box-shadow:none}""",
""".pl-edit{height:48px;border-radius:16px;font-size:16px;box-shadow:none}
.pla{gap:14px;padding:14px}
.pla-reg{display:flex;align-items:center;gap:8px;min-height:36px;margin:12px 16px 0;padding:6px 12px;border-radius:12px;background:var(--amber-soft);color:var(--amber-ink);font-size:13.5px;font-weight:900;box-sizing:border-box}
.pla-reg svg{flex:none}
.pla-tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;background:var(--fill);border-radius:14px;padding:4px}
.pla-tab{height:44px;border-radius:11px;font-size:13.5px;font-weight:900;color:var(--ink4);background:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 4px;text-align:center}
.pla-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.pla-stat{background:var(--fill);border-radius:12px;padding:8px 10px;display:flex;flex-direction:column;min-width:0}
.pla-stat span{font-size:10.5px;font-weight:900;color:var(--ink4);letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
.pla-stat b{font-size:18px;font-weight:900;line-height:1.25;overflow-wrap:anywhere}
.pla-stat b.sm{font-size:14px;line-height:1.35}
.pla-stat i{font-style:normal;font-size:11.5px;font-weight:800;color:var(--ink4)}
.pla-star{font-style:normal}
.pla-narrow{display:none}
@media (max-width:345px){.pla-stat{padding:8px}.pla-stat span{font-size:9.5px;letter-spacing:.02em}.pla-stat .pla-wide{display:none}.pla-stat .pla-narrow{display:inline}}
.pla-dh{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px;margin-left:30px;font-size:10.5px;font-weight:900;color:var(--muted);text-align:center;letter-spacing:.05em;margin-bottom:6px;text-transform:uppercase}
.pla-dh .free{color:var(--green-ink3)}
.pla-grid{position:relative}
.pla-ax{position:absolute;left:0;width:26px;font-size:10px;font-weight:800;color:var(--muted);transform:translateY(-50%);text-align:right}
.pla-hl{position:absolute;left:30px;right:0;border-top:1px dashed var(--line2);z-index:1;pointer-events:none;opacity:.7}
.pla-cols{position:absolute;left:30px;right:0;top:0;bottom:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px}
.pla-col{position:relative;background:var(--bg);border-radius:8px}
.pla-free{display:flex;align-items:center;justify-content:center;background:var(--green-wash)}
.pla-free span{font-size:11px;font-weight:900;color:var(--green-ink2);writing-mode:vertical-rl;letter-spacing:.08em;text-transform:uppercase}
.pla-blk{position:absolute;z-index:2;border-radius:7px;color:#fff;padding:2px 5px;box-sizing:border-box;text-align:left;overflow:hidden;display:flex;flex-direction:column;gap:1px;line-height:1.1}
.pla-blk b{font-size:11px;font-weight:900}
.pla-blk i{font-style:normal;font-size:10px;font-weight:800;opacity:.92}
.pla-any{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:10px}
.pla-anyl{font-size:10.5px;font-weight:900;color:var(--ink4);letter-spacing:.06em;text-transform:uppercase}
.pla-chip{min-height:30px;padding:4px 10px;border-radius:10px;background:var(--pc-soft);color:var(--pc-ink);font-size:12px;font-weight:900;text-align:left}
.pla .pla-code{background:var(--pc-soft);color:var(--pc-ink)}
.pla-rt{flex:none;max-width:30%;display:flex;flex-direction:column;align-items:flex-end;text-align:right;min-width:0}
.pla-rt b{font-size:13px;font-weight:900;white-space:nowrap}
.pla-rt small{font-size:11.5px;font-weight:800;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}""")

f.write_text(s)
print('patched', f)
