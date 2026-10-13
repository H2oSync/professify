#!/usr/bin/env python3
"""Past classes: your major and concentration, then what's filled by kind (Tate, 2026-10-11):
"add in on Past classes where it says your Major and concentration then shows a simple version of the Major classes
GE classes and Concentration and elective classes that have been fulfilled."
Usage: python3 past-kinds-2026-10-11.py <repo-dir>   (replayable on build 19:05)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)

rep(".pc-cat{font-size:12.5px;font-weight:800;color:var(--muted);margin-top:10px}", """.pc-cat{font-size:12.5px;font-weight:800;color:var(--muted);margin-top:10px}
/* Past classes (2026-10-11): who it's for, then filled by kind */
.pc-me{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:8px;row-gap:2px;margin-bottom:12px}
.pc-me b{font-size:16px;font-weight:900;line-height:1.25}
.pc-me span{font-size:14px;font-weight:800;color:var(--muted)}
.pc-kinds{display:grid;gap:10px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
.pc-k{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;column-gap:10px;row-gap:5px}
.pc-kl{font-size:15px;font-weight:800;min-width:0}
.pc-kv{display:inline-flex;align-items:center;gap:6px;font-size:14.5px;font-weight:900;color:var(--muted);font-variant-numeric:tabular-nums}
.pc-k.full .pc-kv{color:var(--teal-t,var(--teal))}
.pc-kb{grid-column:1 / -1;height:4px;border-radius:2px;background:var(--track,var(--fill2));overflow:hidden}
.pc-kb i{display:block;height:100%;background:var(--teal-t,var(--teal));border-radius:2px}
.pc-kt{grid-column:1 / -1;font-size:12.5px;font-weight:800;color:var(--muted);margin-top:-2px}""", 'css')

rep("""const pcDate = iso => { try {""", """/* (2026-10-11) Past classes, simply: Major classes · GE · Concentration · Electives — finished of how many,
   and how many you're taking now. From the report when there is one (the report decides; like its big number, a
   line in progress counts as filled, and says so), else the flowchart (whose big number counts finished only).
   Degree-wide lines (units, GPA, GWR, USCP) count in the big number only. */
const PC_KINDS = [['major', 'Major classes'], ['ge', 'GE classes'], ['conc', 'Concentration'], ['el', 'Electives']];
function pcKinds(L, X) {
  const k = { major: null, ge: null, conc: null, el: null }, add = (key, f, t, n) => { const r = k[key] || (k[key] = { f: 0, t: 0, n: 0 }); r.f += f; r.t += t; r.n += n; };
  if (X) {
    const fill = new Set(X.filled), prog = new Set(X.inprog);
    X.live.forEach(b => {
      if (auditIsTotal(b) || /^(units|gpa|gwr|uscp)$/.test(b.kind || '')) return;
      const key = b.kind === 'ge' ? 'ge' : b.kind === 'conc' ? 'conc' : b.kind === 'elective' ? 'el' : 'major';
      add(key, fill.has(b) ? 1 : 0, prog.has(b) ? 1 : 0, 1);
    });
  } else if (L && L.rows) {
    L.rows.forEach(r => add(r.label === 'Major courses' ? 'major' : r.label === 'General education' ? 'ge' : r.label === 'Electives' ? 'el' : 'conc', r.f, r.t, r.n));
  }
  const rows = PC_KINDS.filter(([key]) => k[key] && k[key].n).map(([key, label]) => {
    const r = k[key], full = r.f >= r.n && !(X && r.t), pct = Math.round(100 * Math.min(r.f, r.n) / r.n);
    return `<div class="pc-k${full ? ' full' : ''}" data-k="${key}"><span class="pc-kl">${label}</span><span class="pc-kv">${full ? ic('check', 16, 3) : ''}${r.f} of ${r.n}</span><span class="pc-kb" aria-hidden="true"><i style="width:${pct}%"></i></span>${r.t ? `<span class="pc-kt">${X ? (r.t === r.f ? (r.t === 1 ? 'In progress' : 'All in progress') : `${r.t} of these in progress`) : `+ ${r.t} in progress`}</span>` : ''}</div>`;
  });
  return rows.length ? `<div class="pc-kinds" role="list" aria-label="Filled by kind">${rows.join('')}</div>` : '';
}
function pcWho(L, P) {
  P = P || TC.profile || {};
  const major = P.major || (L && L.major) || (TC.audit && TC.audit.major) || '';
  if (!major) return '';
  const c0 = P.concentration && P.concentration !== 'General / Open' ? meConc(P.concentration) : (TC.audit && TC.audit.conc ? meConc(TC.audit.conc) : '');
  /* no concentration yet: the card's own "Pick your concentration" asks */
  const conc = c0 ? `<span>${esc(c0)} concentration</span>` : '';
  return `<div class="pc-me"><b>${esc(major)}</b>${conc}</div>`;
}
const pcDate = iso => { try {""", 'helpers')

rep("""  return `<div class="card pc-sum"><div class="pc-num"><b>${L.F} of ${L.N}</b><span>filled</span></div><div class="pc-bar" role="img" aria-label="${L.F} of ${L.N} filled"><i style="width:${pct}%"></i></div>${X ?""",
    """  return `<div class="card pc-sum">${pcWho(L, P)}<div class="pc-num"><b>${L.F} of ${L.N}</b><span>filled</span></div><div class="pc-bar" role="img" aria-label="${L.F} of ${L.N} filled"><i style="width:${pct}%"></i></div>${pcKinds(L, X)}${X ?""", 'summary')
open(PA, 'w', encoding='utf-8').write(S); print('past-kinds: done')
