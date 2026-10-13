#!/usr/bin/env python3
"""What's left, once — in the Builder (Tate, 2026-10-12).

Tate, with Past classes' top card and the Builder's "2 left to graduate" side by side: "lets find a way to conjoin these
together and place them under Builder. past classes should only show the stuff below".

- Builder: one card. Your major, concentration and catalog chip; "N left to graduate"; "54 of 56 filled · 5 in progress"
  and the bar; then each requirement as Past classes showed it (its chip, "pick one of 6" / "4 units needed", Mark done,
  Needs a look) with the best options for the term under it; lines the app couldn't read; "Show the N in progress this
  term"; your catalog and when the report was printed; and, when the report names no concentration, the pick.
- Past classes: only what's below — Done, Every class by term, Units only (and the flowchart years where they apply).
  "Best options in the Builder" is gone: the Builder is where what's left lives.
Usage: python3 builder-left-merged-2026-10-12.py <repo-dir>   (replayable on build 2026-10-11 23:45)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)

rep(".pll-ring{width:20px;height:20px;flex:none;border-radius:50%;box-shadow:inset 0 0 0 2.5px var(--ink5,var(--muted));margin-top:1px}",
    """.pll-ring{width:26px;height:26px;flex:none;border-radius:50%;box-shadow:inset 0 0 0 2px var(--line2)}
/* (2026-10-12) what's left, once: Past classes' top in the Builder's card */
.pll .pc-me{margin-bottom:10px}
.pll .pc-num b{font-size:15px}
.pll .pc-num span{font-size:14px}
.pll .pll-s{padding-top:10px}
.pll-req > .pc-row{background:none;padding:0 2px;min-height:40px;border-radius:0}
.pll-rh{align-items:center}
.pll-ip{border-top:1px solid var(--line);margin-top:12px;padding-top:4px}
.pll-ip .pc-row + .pc-row,.pll-ip .pc-row{margin-top:6px}
.pll .pc-cat{padding:0 2px 8px}
.pll .pc-conc{border-top:1px solid var(--line);padding:12px 2px 10px}""", 'css ring')
for sel in ('.pll-opt{display:flex;align-items:center;gap:10px;background:var(--bg);border-radius:16px;padding:10px 10px 10px 12px;margin:6px 0 0 30px}',
            '.pll-more{display:block;margin:4px 0 0 30px;', '.pll-none{margin:2px 0 0 30px;'):
    rep(sel, sel.replace('0 0 30px', '0 0 38px'), 'indent ' + sel[:9])

# plLeftReqs: keep the report line itself, so its row reads as on Past classes
rep("""R.X.open.filter(b => !auditIsTotal(b)).map(b => ({ key: 'a' + TC.audit.reqs.indexOf(b), label:""",
    """R.X.open.filter(b => !auditIsTotal(b)).map(b => ({ b, key: 'a' + TC.audit.reqs.indexOf(b), label:""", 'reqs b')

rep("""function plLeftCard(R, L, k) {
  const reqs = plLeftReqs(R, L); if (!reqs.length) return '';""", """function plLeftCard(R, L, k) {
  L = L || {};   /* no flowchart: the report alone (R.bare — nothing to pick from) */
  const X = R.audit ? R.X : null, unk = X ? X.unknown : [];
  const reqs = plLeftReqs(R, L); if (!reqs.length) return '';   /* only lines it couldn't read: the Still need card below says so */
  const idx = X ? new Map((TC.audit.reqs || []).map((b, i) => [b, i])) : null;""", 'card head')
rep("""    return `<div class="pll-req"><div class="pll-rh"><span class="pll-ring" aria-hidden="true"></span><span class="pll-rl">${esc(q.label)}</span></div>${cs.map(c => plLeftOpt(c, k, q.label)).join('')}${none}${more}</div>`;
  };""", """    if (R.bare) return `<div class="pll-req">${pcReqRow(q.b, X, L, idx.get(q.b))}</div>`;
    const head = q.b ? pcReqRow(q.b, X, L, idx.get(q.b)) : `<div class="pll-rh"><span class="pll-ring" aria-hidden="true"></span><span class="pll-rl">${esc(q.label)}</span></div>`;
    return `<div class="pll-req">${head}${cs.map(c => plLeftOpt(c, k, q.label)).join('')}${none}${more}</div>`;
  };
  /* (2026-10-12) Past classes' top, here: who you are and your catalog, the count and bar, the lines you're finishing */
  const lf = pcLeft(L, X), F = X ? X.filled.length : L.F || 0, N = X ? X.live.length : L.N || 0, pct = N ? Math.round(100 * F / N) : 0;
  const num = N ? `<div class="pc-nrow"><div class="pc-num"><b>${F} of ${N}</b><span>filled</span></div>${lf.inp ? `<span class="pc-inp">· ${lf.inp} in progress</span>` : ''}</div><div class="pc-bar" role="img" aria-label="${F} of ${N} filled"><i style="width:${pct}%"></i></div>` : '';
  const cat = X && TC.audit.catalog ? `<div class="pc-cat">Your catalog: ${esc(TC.audit.catalog)}${TC.audit.printed_on ? ' · report printed ' + esc(pcDate(TC.audit.printed_on)) : ''}</div>` : '';
  const ci = X && !TC.audit.conc && L.concUnchosen ? TCPL.concInfo(L.major) : null;
  const pick = ci && ci.list.length ? `<div class="pc-conc"><div class="b" style="font-size:14.5px;margin-bottom:8px">Pick your concentration</div><div style="display:flex;flex-wrap:wrap;gap:8px">${ci.list.map(c => `<button class="chip" style="background:var(--bg)" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  /* lines the app couldn't read: the report's, so they're what's left too */
  const unkRows = unk.map(b => `<div class="pll-req">${pcReqRow(b, X, L, idx.get(b))}</div>`).join('');""", 'card rows')
rep("""  return `<div class="card pll"><div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div><div class="pll-s">${sub}</div>${show.map(row).join('')}${reqs.length > 4 ? `<button class="pll-all" data-a="plLeftAll">${UI.plLeftAll ? 'Fewer' : `All ${reqs.length} ›`}</button>` : ''}</div>`;""",
    """  return `<div class="card pll">${pcWho(L, TC.profile)}<div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div>${num}<div class="pll-s">${sub}</div>${show.map(row).join('')}${unkRows}${reqs.length > 4 ? `<button class="pll-all" data-a="plLeftAll">${UI.plLeftAll ? 'Fewer' : `All ${reqs.length} ›`}</button>` : ''}${lf.ip ? `<div class="pll-ip">${lf.ip}</div>` : ''}${cat}${pick}</div>`;""", 'card return')

rep("  const X = R.X, tot = X && X.total && X.total.status", "  const tot = X && X.total && X.total.status", "tot")
rep("  const sub = `Best options for ${esc(CFG.TERM_LABEL)}${tot", "  const sub = R.bare ? (tot ? `Plus ${tot} units to go` : '') : `Best options for ${esc(CFG.TERM_LABEL)}${tot", 'bare sub')
rep("""${num}<div class="pll-s">${sub}</div>""", """${num}${sub ? `<div class="pll-s">${sub}</div>` : ''}""", 'sub opt')
# no flowchart for this major: the report still says what's left — the top card, without options
rep("""  if (!L) return (plNoRecord() && !TC.audit && !plSkipped() ? dprFirstCard() : '') + `<div class="card tc-sec" style="margin-top:14px">""",
    """  const X0 = !L ? auditLines(TC.audit, null) : null;
  if (!L) return (plNoRecord() && !TC.audit && !plSkipped() ? dprFirstCard() : '') + (X0 ? plLeftCard({ audit: true, X: X0, all: [], bare: true }, null, 'A') : '') + `<div class="card tc-sec" style="margin-top:14px">""", 'no flowchart')
# pcLeft hands back the in-progress toggle on its own
rep("""    return { n, head, rows, inp };
  }""", """    return { n, head, rows, inp, ip: ipRows };
  }""", 'pcLeft ip')

# Past classes: only what's below
i0 = S.index("function pcSummary(L, P) {"); i1 = S.index("/* (2026-10-11) What's left: the report's open lines", i0)
if S.count("function pcSummary(L, P) {") != 1: sys.exit('pcSummary anchor')
S = S[:i0] + """/* (2026-10-12) Tate: "past classes should only show the stuff below" — what's left, the count, your catalog and the
   concentration pick live in the Builder's top card (plLeftCard); Past classes keeps what's done. */
function pcSummary(L, P) {
  const X = auditLines(TC.audit, L);
  return `${pcDone(L, X)}${pcTermsBtn()}`;
}
""" + S[i1:]
open(PA, 'w', encoding='utf-8').write(S); print('builder-left-merged: done')
