#!/usr/bin/env python3
"""The Builder: what you should take, and the best options under each — plain rows, everything on tap (Tate, 2026-10-13).

Tate: "take out the created plans in builder instead it should show the classes that you should take and under each one should
give you the top options for that requirement so i can click approved elective finance concentration and see all the classes
that are offered with the highest rated professors and friends towards the top … it expands down from the requirement, and
take out the + and only have the professor show up … make it more bland until you click on particular class and then it should
show information like how we have it do when you click on someones schedule class." Canvas *Builder Five Ways*, option 1
(boards 1A, 1B, 1C, 1E).

- No plans in the Builder: TermChamp's Plan A/B/C card (18:05) and its class sheet are gone. Plans still change only when
  you add a class (the Add sheet).
- The top: term, registration, "1 Degree · 2 Professors · 3 Friends", then one card: major · concentration, the report's
  catalog, "N left to graduate", "54 of 56 filled" and the bar.
- Each requirement is a row that opens down (the first starts open): its tag and a line of context ("4 units · 6 offered
  this spring"; folded: "… · best ★ 4.6 Katona"). Open: BEST FOR YOU, three plain rows — class name, the number under it,
  the professor's last name on the right — then "See all N" / "Show top 3" and "Mark done". A line the report lists but
  didn't count still says "Needs a look". A requirement with nothing offered says so (GE → that area's classes).
- Tap a class: the app's own section sheet (as on a friend's schedule): time · seats, the professor's row and rating,
  friends in the section and in other sections, what it fills and that it's clear of your week, then Add to a plan,
  View class, seat alerts.
Usage: python3 builder-options-2026-10-13.py <repo-dir>   (replayable on build 2026-10-12 18:05)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)
def cut(a, b, label):
    """remove from a (inclusive) to b (exclusive)"""
    global S
    if S.count(a) != 1 or S.count(b) != 1: sys.exit(f'{label}: cut anchors {S.count(a)}x / {S.count(b)}x')
    i = S.index(a); j = S.index(b); assert i < j, label
    S = S[:i] + S[j:]

# ---------------------------------------------------------------- TermChamp's plans out of the Builder
cut("/* (2026-10-12) TermChamp's Plan A, B and C — what the Builder would take, apart from your own plans.", "/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */", 'rec block')
cut("  /* (2026-10-12) TermChamp's plans: open a class, swap it, take it out, start over, or set the plan as yours */\n  recOpen:", "  plLeftFold: () =>", 'rec actions')
rep("""  if (UI.plRefresh) { UI.plRefresh = false; }
  const k = /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A';
  PL_CTX = { R, L };
  const recIds = !waiting && data ? plRecOf(R, L, k) : null;""", """  if (UI.plRefresh) { UI.plRefresh = false; }
  const k = /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A';""", 'no rec ids')
rep("left = plLeftCard(R, L, k, recIds);", "left = plLeftCard(R, L, k);", 'left call')
rep("""  ${left}
  ${waiting ? cmWaitCard(k) : plRecCard(R, L, k, data ? '' : 'nodata')}""", """  ${left}""", 'no rec card')
rep("Your plans change only when you set one, and are only yours until you share them.", "Your plans change only when you add a class, and are only yours until you share them.", 'footnote')
rep("Prerequisites didn’t load, so TermChamp’s plan doesn’t check them. Check each class page before you add it.", "Prerequisites didn’t load, so these options don’t check them. Check each class page before you add it.", 'prereq note')
rep("""Set TermChamp’s Plan ${S.plan} from the Builder, or add classes from Explore.""", """Add classes from the Builder or Explore.""", 'plans empty copy')
rep("""${secs.length ? '' : `<button class="btn soft" style="margin-top:10px" data-a="schedTab" data-x="planner">Open the Builder</button>`}""", """${secs.length ? '' : `<button class="btn soft" style="margin-top:10px" data-a="schedTab" data-x="planner">Open the Builder</button>`}""", 'plans btn kept')

# ---------------------------------------------------------------- the top card and the requirements
i0 = S.index("function plLeftCard(R, L, k, rec) {"); i1 = S.index("/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */", i0)
S = S[:i0] + """function plLeftCard(R, L, k) {
  L = L || {};   /* no flowchart: the report alone (R.bare) */
  const X = R.audit ? R.X : null, unk = X ? X.unknown : [];
  const reqs = plLeftReqs(R, L); if (!reqs.length) return '';   /* only lines it couldn't read: the Still need card below says so */
  const idx = X ? new Map((TC.audit.reqs || []).map((b, i) => [b, i])) : null;
  const pos = c => R.all.indexOf(c), fits = c => !!(c.inPlan || plLeftSec(c, k));
  /* best for you: feasible first, then the Builder's order (your 1-2-3); requirements with a feasible option first */
  reqs.forEach(q => q.cands.sort((a, b) => (fits(b) ? 1 : 0) - (fits(a) ? 1 : 0) || pos(a) - pos(b)));
  const rk = q => q.cands.length ? (fits(q.cands[0]) ? 0 : 1e6) + pos(q.cands[0]) : 2e6;
  reqs.sort((a, b) => rk(a) - rk(b));
  UI.plLeftOpen = UI.plLeftOpen || {};
  if (!UI.plReqOpen || !reqs.some(q => q.key in UI.plReqOpen)) UI.plReqOpen = { [reqs[0].key]: true };   /* the first starts open — again when the requirements change (a new report) */
  const tot = X && X.total && X.total.status === 'not' && X.total.units && X.total.units.need != null ? auditNum(X.total.units.need) : null;
  const secOf = c => plLeftSec(c, k) || c.planSec || c.best;
  const prof = c => { const s = secOf(c); return s && s.prof ? profName(s.prof).split(' ').slice(-1)[0] : ''; };
  const need = q => q.b ? [q.b.oneOf && (q.b.options || []).length > 1 ? 'pick one of ' + q.b.options.length : '', q.b.units && q.b.units.need ? auditNum(q.b.units.need) + (+q.b.units.need === 1 ? ' unit' : ' units') : q.b.courses && q.b.courses.need ? auditNum(q.b.courses.need) + (q.b.courses.need > 1 ? ' classes' : ' class') : ''].filter(Boolean).join(' · ') : q.opts > 1 ? `pick one of ${q.opts}` : '';
  /* (2026-10-13) plain rows: the name, the number under it, the professor's last name — the tap shows the rest */
  const row = (q, c) => { const s = secOf(c), nm = courseName(c.code) || course(c.code).title || c.code;
    return `<button class="plo${fits(c) ? '' : ' plo-no'}" data-a="plOptSheet" data-x="${esc(c.code)}" data-y="${esc(s ? s.id : '')}" data-z="${esc(q.key)}"><span class="plo-t"><span class="plo-n">${esc(nm)}</span><span class="plo-c">${esc(c.code)}${fits(c) ? '' : ' · every section clashes with Plan ' + k + ' or your week'}</span></span><span class="plo-p">${esc(prof(c) || 'Staff')}</span></button>`; };
  const card = q => {
    const open = !!UI.plReqOpen[q.key], all = !!UI.plLeftOpen[q.key], n = q.cands.length, cs = all ? q.cands.slice(0, 12) : q.cands.slice(0, 3);
    const best = q.cands[0], br = best ? ratingOf((secOf(best) || {}).prof) : null;
    const tag = q.b && auditTag(q.b) ? `<span class="pc-tags">${auditTag(q.b)}</span>` : q.n && q.n.group === 'conc' ? '<span class="pc-tags"><span class="pk-tag t-teal">Conc.</span></span>' : '';
    const sub = [need(q), n ? `${n} offered this ${esc(String(CFG.TERM_LABEL).split(' ')[0].toLowerCase())}` : 'nothing offered this term', !open && best ? (br != null ? `best ★ ${br.toFixed(1)}${prof(best) ? ' ' + esc(prof(best)) : ''}` : prof(best) ? 'best with ' + esc(prof(best)) : '') : ''].filter(Boolean).join(' · ');
    const head = `<button class="plq" data-a="plReqOpen" data-x="${esc(q.key)}" aria-expanded="${open}"><span class="pll-ring${open ? ' on' : ''}" aria-hidden="true"></span><span class="plq-t"><b>${esc(q.label)}${tag}</b><span>${sub}</span></span>${pcChev(open ? 90 : 0)}</button>`;
    if (!open) return `<div class="card plq-card">${head}</div>`;
    const none = n ? '' : `<div class="pll-none">${q.area ? `Nothing for GE ${esc(q.area)} fits yet. <button data-a="plGe" data-x="${esc(q.area)}">See GE ${esc(q.area)} classes</button>`
      : q.opts === 0 ? 'Your report doesn’t name the classes for this one. Your advisor or the catalog has the list.'
      : `${q.one ? `${esc(q.one)} isn’t` : q.opts === 1 ? 'Its class isn’t' : 'None of its classes are'} offered in ${esc(CFG.TERM_LABEL)}${UI.pl && UI.pl.prereqs ? ', or you need a prerequisite first' : ''}.`}</div>`;
    const look = q.b && (q.b.listed || []).length ? `<div class="pc-look plq-look">Needs a look: your report lists ${esc(q.b.listed.slice(0, 3).join(', '))} on your record but didn’t count ${q.b.listed.length > 1 ? 'them' : 'it'} here — ask your advisor</div>` : '';
    const more = n > 3 ? `<button class="plq-more" data-a="plLeftOpen" data-x="${esc(q.key)}">${all ? 'Show top 3' : `See all ${Math.min(n, 12)}`}</button>` : '';
    const mark = q.b && !auditIsTotal(q.b) && idx ? `<button class="plq-mark" data-a="plMarkAsk" data-x="${idx.get(q.b)}">Mark done</button>` : '';
    return `<div class="card plq-card open">${head}<div class="plq-body">${n ? '<div class="plq-lab">Best for you</div>' : ''}${cs.map(c => row(q, c)).join('')}${none}${look}${more || mark ? `<div class="plq-foot">${more}${mark}</div>` : ''}</div></div>`;
  };
  const show = UI.plLeftAll ? reqs : reqs.slice(0, 6);
  const unkRows = unk.map(b => `<div class="card plq-card"><div class="pll-req">${pcReqRow(b, X, L, idx.get(b))}</div></div>`).join('');
  const P = TC.profile || {}, major = P.major || L.major || (TC.audit && TC.audit.major) || '';
  const c0 = P.concentration && P.concentration !== 'General / Open' ? meConc(P.concentration) : (TC.audit && TC.audit.conc ? meConc(TC.audit.conc) : '');
  const who = major ? `<div class="pll-who">${esc(major)}${c0 ? ' · ' + esc(c0) : ''}</div>` : '';
  const catRow = X && TC.audit.catalog ? `<div class="pll-cat"><span class="pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}">${esc(TC.audit.catalog)} catalog</span><span>from your report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span></div>` : '';
  const F = X ? X.filled.length : L.F || 0, N = X ? X.live.length : L.N || 0, pct = N ? Math.round(100 * F / N) : 0;
  const num = N ? `<div class="pc-nrow"><div class="pc-num"><b>${F} of ${N}</b><span>filled</span></div>${tot ? `<span class="pc-inp">· plus ${tot} units to go</span>` : ''}</div><div class="pc-bar" role="img" aria-label="${F} of ${N} filled"><i style="width:${pct}%"></i></div>` : '';
  const clear = TC.commits.length ? `<button class="pl-clear" data-a="sheet" data-x="cmList"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"></path></svg>Clear of your ${esc(cmWords())}</button>` : '';
  const ci = X && !TC.audit.conc && L.concUnchosen ? TCPL.concInfo(L.major) : null;
  const pick = ci && ci.list.length ? `<div class="pc-conc"><div class="b" style="font-size:14.5px;margin-bottom:8px">Pick your concentration</div><div style="display:flex;flex-wrap:wrap;gap:8px">${ci.list.map(c => `<button class="chip" style="background:var(--bg)" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  const top = `<div class="card pll">${who}${catRow}<div class="pll-h"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span></div>${num}${clear}${pick}</div>`;
  return top + `<div class="plq-list">${show.map(card).join('')}${unkRows}${reqs.length > 6 ? `<button class="pll-all" data-a="plLeftAll">${UI.plLeftAll ? 'Fewer' : `All ${reqs.length} ›`}</button>` : ''}</div>`;
}
""" + S[i1:]

rep("  plLeftFold: () => { UI.plLeftOpen2 = !UI.plLeftOpen2; render(true); },", """  plReqOpen: key => { UI.plReqOpen = UI.plReqOpen || {}; UI.plReqOpen[key] = !UI.plReqOpen[key]; render(true); },
  /* (2026-10-13) a class in the Builder opens the app's section sheet, with what it fills and Add to a plan */
  plOptSheet: (code, id, el) => { const key = el && el.dataset ? el.dataset.z : ''; const s = SEC[id] || secsOf(code)[0]; if (!s) return A.openClass(code);
    const q = (PL_LEFT_REQS || []).find(x => x.key === key), c = PL_LEFT_ALL && PL_LEFT_ALL.find(x => x.code === code);
    UI.sheet = { type: 'sec', code, id: String(s.id), fill: q ? q.label : '', fits: !!(c && (c.inPlan || plLeftSec(c, /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A'))), k: /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A' }; render(true); },""", 'actions')
rep("""function plLeftReqs(R, L) {
  if (R.audit && R.X)""", """let PL_LEFT_REQS = null, PL_LEFT_ALL = null;   /* the Builder's last requirements and candidates, for a tapped class */
function plLeftReqs(R, L) {
  PL_LEFT_ALL = R.all;
  return (PL_LEFT_REQS = plLeftReqs0(R, L));
}
function plLeftReqs0(R, L) {
  if (R.audit && R.X)""", 'reqs memo')

# the section sheet, as on a friend's schedule, plus what it fills and Add to a plan
rep("""SHEETS.sec = ({ code, id }) => {""", """SHEETS.sec = sh => { const { code, id } = sh;""", 'sec sig')
rep(""" ${secPeopleRow(who.here, 'In this section')}${secPeopleRow(who.other, 'Other sections')}
 <div style="display:grid;gap:8px;margin-top:18px"><button class="btn" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>View class</button>""",
    """ ${secPeopleRow(who.here, 'In this section')}${secPeopleRow(who.other, 'Other sections')}
 ${sh.fill ? `<div class="sec-fill${sh.fits ? '' : ' no'}">${sh.fits ? `Fills ${esc(sh.fill)} · clear of Plan ${sh.k}${TC.commits.length ? ' and your ' + esc(cmWords()) : ''}` : `Fills ${esc(sh.fill)} · over a class in Plan ${sh.k} or your week`}</div>` : ''}
 <div style="display:grid;gap:8px;margin-top:18px">${sh.fill && !inP && SEC[id] ? `<button class="btn" data-a="addPlanSheet" data-x="${esc(id)}">Add to a plan</button>` : ''}<button class="btn${sh.fill && !inP && SEC[id] ? ' soft' : ''}" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>View class</button>""", 'sec sheet')

# ---------------------------------------------------------------- CSS
rep("button.pll-h{width:100%;text-align:left;min-height:52px;margin-top:6px}", """.pll-h{margin-top:8px}
/* (2026-10-13) the requirements as cards that open down; plain option rows */
.plq-list{display:flex;flex-direction:column;gap:10px;margin:10px 12px 0}
.plq-card{margin:0;padding:0}
.plq-card.open{box-shadow:inset 0 0 0 2px var(--blue)}
.plq{display:flex;align-items:center;gap:14px;width:100%;min-height:76px;padding:14px 16px;text-align:left}
.plq .pll-ring.on{box-shadow:inset 0 0 0 2.5px var(--blue)}
.plq-t{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.plq-t b{font-size:17px;font-weight:900;line-height:1.25;display:flex;align-items:center;flex-wrap:wrap;gap:4px 8px}
.plq-t b .pc-tags{display:inline-flex}
.plq-t > span{font-size:12.5px;font-weight:800;color:var(--muted);line-height:1.4}
.plq-body{padding:0 16px 6px}
.plq-lab{font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:2px 0 4px}
.plo{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;padding:11px 0;border-top:1px solid var(--line);text-align:left}
.plo:first-of-type{border-top:0}
.plo-t{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.plo-n{font-size:15px;font-weight:900;line-height:1.25}
.plo-c{font-size:12.5px;font-weight:800;color:var(--muted)}
.plo-p{flex:none;font-size:13px;font-weight:800;color:var(--muted);max-width:40%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.plo-no .plo-n{color:var(--muted)}
.plq-look{display:block;font-size:12.5px;font-weight:800;color:var(--amber-ink);margin:6px 0 2px;line-height:1.4}
.plq-foot{display:flex;gap:8px;align-items:center;padding:10px 0;border-top:1px solid var(--line);margin-top:4px}
.plq-more{flex:1;min-height:44px;border-radius:12px;background:var(--tint1);color:var(--blue-t,var(--blue));font-size:14px;font-weight:900}
.plq-mark{flex:none;min-height:44px;padding:0 14px;border-radius:12px;color:var(--muted);font-size:13.5px;font-weight:900}
.plq-foot .plq-mark:only-child{margin-left:auto}
.pll .pl-clear{margin:10px 0 0}
.sec-fill{margin-top:14px;padding:10px 12px;border-radius:12px;background:var(--teal-soft);color:var(--teal-t,var(--teal));font-size:13px;font-weight:900;line-height:1.4}
.sec-fill.no{background:var(--amber-soft);color:var(--amber-ink)}""", 'css')
# the waiting card went with TermChamp's plans
rep(".cm-wait{opacity:.5}\n", "", 'cm-wait css')
i = S.index("const cmWaitCard = k => "); j = S.index("\n", i) + 1; S = S[:i] + S[j:]
open(PA, 'w', encoding='utf-8').write(S); print('builder-options: done')
