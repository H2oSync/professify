#!/usr/bin/env python3
"""The Builder's top card as the three-way ledger (Tate, 2026-10-13, on the Builder Top Card — Ten Ways canvas: "do 9 and
also put this somewhere", pointing at the "Fall Quarter 2023 catalog" chip; then "you dont need pick 1").
  - "2 left to graduate" stays the heading.
  - One stacked bar: filled (teal) · in progress (blue) · left (amber) · can't check (grey, only when the report has lines
    the app couldn't read), with a dot legend. Filled means finished — the in-progress lines are their own colour — and
    "left" is exactly what the Builder lists below, so the parts add up to every requirement. With a report, the
    total-units line isn't a requirement in the count: it stays the "n units to go" note.
  - One meta line below: the major · concentration, the catalog chip (kept, as asked), "report · Oct 8", "n requirements".
  - The Pick 1 chip comes off the Builder's cards; their line already says "pick one of n".
Without a report (the flowchart alone) the bar is done · taking (L.T) · left (need + needU). Replayable on 05:50.
  python3 builder-top-ledger-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-top-ledger: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)
# the old card's CSS goes; the ledger's comes (pll-hd / pll-info, not pll-top / pll-meta — those names belong to the option rows)
rep(""".pll-who{font-size:16px;font-weight:900;line-height:1.3;padding:0 2px}
.pll-cat{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-top:8px;padding:0 2px;font-size:12.5px;font-weight:800;color:var(--muted)}
.pll-cat .pc-catc{flex:none}""",
"""/* (2026-10-13) the three-way ledger: the heading, a stacked bar, its legend, then who you are with the catalog chip */
.pll-hd{display:flex;align-items:baseline;gap:10px;padding:0 2px}
.pll-hd .pll-h{flex:1;margin:0;padding:0;flex-wrap:wrap}
.pll-hd .pll-h span{font-size:17px}
.pll-n{margin-left:auto}
.pll-bar{display:flex;gap:2px;height:10px;border-radius:5px;overflow:hidden;margin-top:12px}
.pll-bar i{display:block;height:100%;min-width:3px}
.pll-bar .f{background:var(--teal-t,var(--teal))}.pll-bar .p{background:var(--blue-t,var(--blue))}.pll-bar .l{background:var(--amber)}.pll-bar .u{background:var(--track,var(--fill2))}
.pll-leg{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:10px;padding:0 2px;font-size:12.5px;font-weight:900}
.pll-leg span{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.pll-leg i{width:9px;height:9px;border-radius:50%;flex:none}
.pll-leg .f{color:var(--ok-ink)}.pll-leg .f i{background:var(--teal-t,var(--teal))}
.pll-leg .p{color:var(--blue-ink)}.pll-leg .p i{background:var(--blue-t,var(--blue))}
.pll-leg .l{color:var(--amber-ink)}.pll-leg .l i{background:var(--amber)}
.pll-leg .u{color:var(--muted)}.pll-leg .u i{background:var(--track,var(--fill2));box-shadow:inset 0 0 0 1.5px var(--line)}
.pll-info{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-top:12px;padding:0 2px;font-size:12.5px;font-weight:800;color:var(--muted);line-height:1.4}
.pll-info .pc-catc{flex:none}
.pll-info .pc-inp{font-size:12.5px}""")
for dead in (""".pc-num{display:flex;align-items:baseline;gap:8px}
.pc-num b{font-size:34px;font-weight:1000;line-height:1}
.pc-num span{font-size:15px;font-weight:800;color:var(--muted)}
.pc-bar{height:8px;border-radius:4px;background:var(--track,var(--fill2));overflow:hidden;margin-top:12px}
.pc-bar i{display:block;height:100%;background:var(--teal-t,var(--teal));border-radius:4px}
""", """.pc-nrow{display:flex;align-items:baseline;flex-wrap:wrap;gap:6px;margin-top:8px}
.pc-nrow .pc-num{margin:0}
""", """.pc-sum .pc-num b{font-size:15px}
.pc-sum .pc-num span{font-size:14px}
""", """.pll .pc-num b{font-size:15px}
.pll .pc-num span{font-size:14px}
"""):
    rep(dead, '')
rep("""  const top = `<div class="card pll">${who}${catRow}<div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div>${num}${clear}${pick}</div>`;""",
    """  /* (2026-10-13, Tate's option 9) the three-way ledger: filled · in progress · left (· can't check) add up to N.
     With a report: left is what the Builder lists (X.open less the total-units line, which stays the "units to go" note), in progress
     the lines in progress or covered by this term's classes, can't check the lines it couldn't read. Flowchart: done · taking · need + needU. */
  const noTot = b => !X.total || b !== X.total;
  const nU = X ? X.unknown.filter(noTot).length : 0, nP = X ? X.inprog.filter(noTot).length : (L.T || 0), nL = reqs.length,
    N = X ? X.live.filter(noTot).length : (L.N || 0), nF = Math.max(0, N - nP - nL - nU);
  const seg = (k, v) => v ? `<i class="${k}" style="width:${(100 * v / N).toFixed(1)}%"></i>` : '';
  const legend = [['f', nF, 'filled'], ['p', nP, 'in progress'], ['l', nL, 'left'], ['u', nU, 'can’t check']].filter(x => x[1] || x[0] === 'f' || x[0] === 'l');
  const bar = N ? `<div class="pll-bar" role="img" aria-label="${legend.map(x => x[1] + ' ' + x[2]).join(', ')} of ${N}">${legend.map(x => seg(x[0], x[1])).join('')}</div>
  <div class="pll-leg" aria-hidden="true">${legend.map(x => `<span class="${x[0]}"><i></i>${x[1]} ${x[2]}</span>`).join('')}</div>` : '';
  const meta = `<div class="pll-info">${major ? `<span>${esc(major)}${c0 ? ' · ' + esc(c0) : ''}</span>` : ''}${X && TC.audit.catalog ? `<span class="pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}">${esc(TC.audit.catalog)} catalog</span><span>report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span>` : ''}${tot ? `<span class="pc-inp">· ${tot} units to go</span>` : ''}${N ? `<span class="pll-n">${N} requirements</span>` : ''}</div>`;
  const top = `<div class="card pll"><div class="pll-hd"><div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div></div>${bar}${meta}${clear}${pick}</div>`;""")
# the old who / catRow / num / F / N strings are unused now
rep("""  const who = major ? `<div class="pll-who">${esc(major)}${c0 ? ' · ' + esc(c0) : ''}</div>` : '';
  const catRow = X && TC.audit.catalog ? `<div class="pll-cat"><span class="pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}">${esc(TC.audit.catalog)} catalog</span><span>from your report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span></div>` : '';
""", "")
rep("""  const num = N ? `<div class="pc-nrow"><div class="pc-num"><b>${F} of ${N}</b><span>filled</span></div>${tot ? `<span class="pc-inp">· plus ${tot} units to go</span>` : ''}</div><div class="pc-bar" role="img" aria-label="${F} of ${N} filled"><i style="width:${pct}%"></i></div>` : '';
""", "")
rep("""  const F = X ? X.filled.length : L.F || 0, N = X ? X.live.length : L.N || 0, pct = N ? Math.round(100 * F / N) : 0;
""", "")
# (2026-10-13) the Pick 1 chip off the Builder cards — the line under the name says "pick one of n" for every line the chip covered
rep('    const tag = q.b && auditTag(q.b) ? `<span class="pc-tags">${auditTag(q.b)}</span>` : q.n && q.n.group === \'conc\' ? \'<span class="pc-tags"><span class="pk-tag t-teal">Conc.</span></span>\' : \'\';\n    const sub = [need(q),',
    '    const at = q.b ? auditTag(q.b) : \'\', tag = at && !/>Pick 1</.test(at) ? `<span class="pc-tags">${at}</span>` : !at && q.n && q.n.group === \'conc\' ? \'<span class="pc-tags"><span class="pk-tag t-teal">Conc.</span></span>\' : \'\';\n    const sub = [need(q),')
rep("""  const need = q => q.b ? [q.b.oneOf && (q.b.options || []).length > 1 ? 'pick one of ' + q.b.options.length : '',""",
    """  const need = q => q.b ? [(q.b.oneOf || (q.b.courses && q.b.courses.req === 1)) && (q.b.options || []).length > 1 ? 'pick one of ' + q.b.options.length : '',""")

p.write_text(s)
print('builder-top-ledger: applied')
