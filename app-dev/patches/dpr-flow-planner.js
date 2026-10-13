/* ---- The Planner (2026-10-08): the plan is drafted on arrival ------------------------------------------
   Candidates are the classes offered this term (CFG.TERM) that clear something the student still needs —
   from the REPORT's own verdicts when it was uploaded (degree_audit: a "Not Satisfied" line and the classes
   that clear it), else from the flowchart ledger — not taken, not in progress, prerequisites met (or
   corequisite-only), no more than a year ahead, never HNRS unless the report shows Honors.
   Every candidate is scored out of 100 in five parts the student can check on the Why sheet:
     Requirements 0–40   what it fills: a required class 10 · a "pick 1" 8 · a concentration line 8 · a GE
                         area 5 · upper-division units 6 · a free elective 2 (summed, capped)
     Urgency      0–30   behind the flowchart 12 a year (cap 24) · the flowchart's own class this term +10,
                         this year +6 · unlocks other needed classes +4 each (cap 12)
     Professor    0–15   the best section's PolyRatings score: (r − 2.5) / 2.5 × 15 · no rating = 5
     Friends      0–10   4 per friend taking it (cap 10), +2 in the best section
     Seats        0–5    only once registration is open: 10+ open 5 · 1–9 3 · waitlist 1 · full 0
   "What matters most" weights the three parts the student ranked: first ×1.5, second ×1.0, third ×0.6
   (degree = Requirements + Urgency; professors = Professor; friends = Friends). Seats are never weighted.
   Plan A takes the best weighted picks, one per requirement, no clashes, never over the units target (and
   never more than a class per 3 units when a class's units aren't known); B is A's classes in other
   sections (after registration opens, at-risk sections swapped for open ones); C re-ranks with friends ×2.5.
   Drafting rules (review 2026-10-08):
     · only once the plans have LOADED — a failed read is not an empty plan;
     · only from data — a record, the report, or a first-year's flowchart — and with prerequisites checked;
     · a plan the student made (on any device) is never drafted into; one they changed or emptied is theirs;
     · a drafted plan is private ("Only you") and gets no seat alerts until the student puts a class in it;
     · a new report or new answers re-draft only the plans that still hold exactly what was drafted. */
const PL_PRE_WAIT = 10000;   /* ms the picks wait for the prerequisites table before going on without it */
const PL_YEAR = { Freshman: 1, Sophomore: 2, Junior: 3, Senior: 4, '5th year +': 5 };
const PL_PARTS = [['req', 'Requirements', 40, 'var(--blue)'], ['urg', 'Urgency', 30, '#C2410C'], ['prof', 'Professor', 15, '#15803D'], ['fr', 'Friends', 10, '#BE185D'], ['seat', 'Seats', 5, '#475569']];
const PL_COL = { A: '#0F766E', B: '#C2410C', C: '#BE185D' };
/* two meetings that overlap (async and unposted times never clash) */
const secClash = (s, t) => !!(s && t && s.s != null && t.s != null && !s.async && !t.async && [...s.days].some(d => t.days.includes(d)) && s.s < t.e && t.s < s.e);
function plBestSec(code, avoid, strict) {
  let ss = secsOf(code).filter(s => s && s.id && SEC[s.id]);
  const clash = s => (avoid || []).some(t => secClash(s, t));
  /* strict (drafting): a section that clashes with what's already in the plan is never the pick */
  if (strict) ss = ss.filter(s => !clash(s));
  if (!ss.length) return null;
  /* an open seat first, then a waitlist, then full — seats count only once registration is open; within
     that one that fits, then the best-rated professor */
  const tier = s => (regOpen() ? (s.status === 'full' ? 0 : s.status === 'wait' ? 2 : 4) : 4) + (clash(s) ? 0 : 1);
  return ss.slice().sort((a, b) => tier(b) - tier(a) || (ratingOf(b.prof) || 0) - (ratingOf(a.prof) || 0) || String(a.id).localeCompare(String(b.id)))[0];
}
/* GE areas by class, built once per GE list (scanning the ~600-row list for each of ~3,000 classes froze the phone) */
let PL_GE = null;
function plGeMap() {
  const G = (window.TCPL && TCPL.geCourses) || [];
  if (PL_GE && PL_GE.src === G && PL_GE.n === G.length) return PL_GE.m;
  const m = new Map();
  G.forEach(g => { if (!g || !g.areaKey) return; const c = TCPL.canon(g.code) || g.code, a = m.get(c) || []; if (!a.includes(g.areaKey)) a.push(g.areaKey); m.set(c, a); });
  PL_GE = { src: G, n: G.length, m };
  return m;
}
/* Units of a class, from what the app can vouch for: the flowchart's slot, then the GE list. Unknown = null. */
function unitsOf(code, L) {
  if (!window.TCPL) return null;
  const k = TCPL.canon(code) || code;
  if (L) for (const t of L.grid || []) for (const s of t.slots || []) { if (s.units == null) continue; if ((s.by && (TCPL.canon(s.by) || s.by) === k) || (s.codes && s.codes.some(c => (TCPL.canon(c) || c) === k)) || (s.code && (TCPL.canon(s.code) || s.code) === k) || (s.choice && s.choice.some(c => (TCPL.canon(c) || c) === k))) return +s.units || null; }
  const g = (TCPL.geCourses || []).find(x => (TCPL.canon(x.code) || x.code) === k);
  return g && g.units ? +g.units : null;
}
const plWeights = () => { const p = (TC.prefs && PREF_ORDER[TC.prefs.priority]) ? PREF_ORDER[TC.prefs.priority] : PREF_ORDER.degree; const w = {}; p.forEach((k, i) => { w[k] = [1.5, 1.0, 0.6][i]; }); return w; };
const plUnitsTarget = () => Math.min(20, Math.max(12, (TC.prefs && +TC.prefs.units) || 16));
/* a class per 3 units at most: what keeps a plan of classes whose units aren't known from growing to 8 */
const plClassCap = () => Math.max(3, Math.round(plUnitsTarget() / 3));
const honors = () => !!(TC.audit && TC.audit.reqs.some(b => /honors/i.test(b.label || '')));
/* The degree's total units is one line of the report: it's "N units to go", never a requirement to plan. */
const auditIsTotal = b => !!b && b.kind === 'units' && /total units|units for the degree/i.test(b.label || '');
/* A line the student marked done themselves (Tate, 2026-10-09: "cal poly didnt update the fact that i took a
   class … i know its satisfied"): kept as { code, label } on degree_audit.overrides, so it holds across new
   uploads — matched by the line's code (R179-10), or by its words when the report prints no code. */
const auditOvMatch = (o, b) => !!(o && b && (o.code ? o.code === b.code : (!b.code && !!o.label && o.label === b.label)));
const auditOverrides = () => (TC.audit && Array.isArray(TC.audit.overrides)) ? TC.audit.overrides : [];
/* The report's lines as every screen counts them (Report read, Check, the Planner — the same numbers):
   filled = Satisfied + In Progress + marked done by you; open = Not Satisfied; can't check = a verdict the
   reader couldn't place. A Not Satisfied line that one class finishes, where you're taking one of its
   classes this term, counts as in progress (the report was printed before you added it). Flagged lines
   are left out. */
function auditLines(a, L) {
  if (!a || !Array.isArray(a.reqs) || !a.reqs.length) return null;
  const k = c => (window.TCPL && TCPL.canon(c)) || c, mine = [...myCodes()], mineK = new Set(mine.map(k)), GE = plGeMap();
  const live = a.reqs.filter(b => b && !b.flag), covered = new Map();
  live.forEach(b => {
    if (b.status !== 'not' || auditIsTotal(b)) return;
    if (b.courses && b.courses.need != null && +b.courses.need > 1) return;
    let by = (b.options || []).find(c => mineK.has(k(c)));
    if (!by && b.kind === 'ge' && b.ge) by = mine.find(c => (GE.get(k(c)) || []).includes(b.ge));
    if (!by) return;
    const u = unitsOf(by, L);
    if (b.units && b.units.need != null && u != null && u < +b.units.need) return;
    covered.set(b, by);
  });
  const ovs = auditOverrides(), manual = new Set(live.filter(b => (b.status === 'not' || b.status === 'unknown') && ovs.some(o => auditOvMatch(o, b))));
  const open = live.filter(b => b.status === 'not' && !covered.has(b) && !manual.has(b));
  return { live, covered, manual, open, unknown: live.filter(b => b.status === 'unknown' && !manual.has(b)),
    filled: live.filter(b => b.status === 'satisfied' || b.status === 'in_progress' || covered.has(b) || manual.has(b)),
    inprog: live.filter(b => b.status === 'in_progress' || covered.has(b)), total: live.find(auditIsTotal) || null };
}
/* The tag a report line wears, the same on Check and in Still need. */
function auditTag(b) {
  const t = (x, c) => `<span class="pk-tag ${c}">${esc(x)}</span>`;
  if (b.status === 'unknown') return t('?', 't-plain');
  if (b.kind === 'ge') return t(b.ge ? 'GE ' + b.ge : 'GE', 't-purple');
  if (b.kind === 'conc') return t('Conc.', 't-teal');
  if (b.kind === 'units') return t(/upper/i.test(b.label || '') ? 'UD' : 'Units', 't-amber');
  if (b.kind === 'gwr') return t('GWR', 't-amber');
  if (b.kind === 'uscp') return t('USCP', 't-purple');
  if (b.kind === 'gpa') return t('GPA', 't-plain');
  if (b.kind === 'elective') return t('Elective', 't-blue');
  if (b.oneOf || (b.courses && b.courses.req === 1 && (b.options || []).length > 1)) return t('Pick 1', 't-blue');
  return t('Major', 't-blue');
}
const auditNum = v => String(+(+v).toFixed(1)).replace(/\.0$/, '');
function planRank(L, opt) {
  opt = opt || {};
  const Y = PL_YEAR[(TC.profile || {}).class_standing] || 0;
  const done = TCPL.completed(), doneSet = new Set(done.map(c => TCPL.canon(c) || c)), mine = [...myCodes()], mineSet = new Set(mine.map(c => TCPL.canon(c) || c));
  const canPre = !!(UI.pl && UI.pl.prereqs), k = c => TCPL.canon(c) || c;
  const needOf = {}; L.need.forEach(n => n.codes.forEach(c => { if (!needOf[k(c)]) needOf[k(c)] = n; }));
  const geNeed = {}; L.needU.forEach(n => { if (n.type === 'ge' && n.area && !geNeed[n.area]) geNeed[n.area] = n; });
  const yearOfTi = ti => (L.grid[ti] && L.grid[ti].year) || 0;
  const GE = plGeMap(), geOf = c => GE.get(k(c)) || [];
  const termNow = String(CFG.TERM_LABEL || '').split(' ')[0].toLowerCase();
  const W = opt.weights || plWeights(), frX = opt.friendsX || 1;
  /* the report's open lines, by class and by GE area */
  const X = auditLines(TC.audit, L), audit = X ? TC.audit : null, auditOpen = X ? X.open : [];
  const byClass = {}, byArea = {};
  auditOpen.forEach(b => { (b.options || []).forEach(c => { (byClass[k(c)] = byClass[k(c)] || []).push(b); }); if (b.kind === 'ge' && b.ge) (byArea[b.ge] = byArea[b.ge] || []).push(b); });
  /* what a line is worth: by its shape, not its words — "1 of 2 options" is a pick-1 whatever it's called */
  const reqPts = b => b.kind === 'ge' ? 5 : b.kind === 'conc' ? 8 : (b.kind === 'units' && /upper/i.test(b.label || '')) ? 6 : (b.oneOf || (b.courses && b.courses.req === 1 && (b.options || []).length > 1)) ? 8 : b.kind === 'elective' ? 2 : 10;
  /* what each needed class unlocks: other requirements that list it as a prerequisite */
  const unl = {};
  if (canPre) L.need.forEach(n2 => { const seen = {}; n2.codes.forEach(c2 => {
    const rec = TCPL.coursePrereqs(c2); if (!rec || !rec.req) return;
    rec.req.forEach(g => { if (g.some(x => doneSet.has(k(x)) || mineSet.has(k(x)))) return;
      g.forEach(x => { const kx = k(x); if (needOf[kx] && needOf[kx] !== n2 && !seen[kx]) { seen[kx] = 1; (unl[kx] = unl[kx] || []).push(c2); } }); });
  }); });
  const ready = code => {
    if (!canPre) return { ok: true, st: null };
    const rec = TCPL.coursePrereqs(code);
    if (!rec || !rec.req || !rec.req.length) return { ok: true, st: rec ? 'none' : null };
    const st = TCPL.prereqStatus(code, done, [], mine).state;
    return { ok: st === 'met' || st === 'concurrent', st };
  };
  const cands = [], seen = {};
  const consider = code => {
    const kc = k(code); if (seen[kc]) return; seen[kc] = 1;
    if (doneSet.has(kc) || mineSet.has(kc) || !secsOf(code).length) return;
    if (/^HNRS\b/.test(code) && !honors()) return;
    const r = ready(code); if (!r.ok) return;
    const n = needOf[kc] || null;
    /* what it fills — the report's verdicts first, the flowchart otherwise */
    let fills = [], geA = [];
    if (audit) {
      fills = (byClass[kc] || []).slice();
      geOf(code).forEach(a => { (byArea[a] || []).forEach(b => { if (!fills.includes(b)) fills.push(b); }); if (!geA.includes(a) && byArea[a]) geA.push(a); });
      if (!fills.length) return;
    } else {
      geA = geOf(code).filter(a => geNeed[a]);
      if (!n && !geA.length) return;
    }
    const ys = geA.map(a => geNeed[a] ? yearOfTi(geNeed[a].ti) : 0).filter(Boolean);
    const yr = n ? (n.year || 0) : (ys.length ? Math.min(...ys) : 0);
    if (Y && yr > Y + 1) return;   /* more than a year ahead of the student: not a pick yet */
    const best = plBestSec(code), rt = best ? ratingOf(best.prof) : null;
    const fr = friendsIn(code), frSec = best ? friendsInSec(best.id) : [], un = n ? (unl[kc] || []) : [];
    const behind = Y && yr ? Math.max(0, Y - yr) : 0;
    const onTerm = !!(n && n.term && String(n.term).toLowerCase() === termNow && yr === Y), onYear = !!(n && yr === Y);
    const open = secsOf(code).some(s => s.status === 'open'), openN = Math.max(0, ...secsOf(code).map(s => s.status === 'open' ? (s.seats || 0) : 0)), waits = secsOf(code).some(s => s.status === 'wait');
    const req = Math.min(40, audit ? fills.reduce((a, b) => a + reqPts(b), 0) : ((n ? (n.group === 'conc' ? 8 : n.choice ? 8 : 10) : 0) + geA.length * 5));
    const urg = Math.min(30, Math.min(24, behind * 12) + (onTerm ? 10 : onYear ? 6 : 0) + Math.min(12, un.length * 4));
    const prof = rt == null ? 5 : Math.max(0, Math.min(15, Math.round((rt - 2.5) / 2.5 * 15)));
    const frP = Math.min(10, fr.length * 4 + (frSec.length ? 2 : 0));
    const seat = !regOpen() ? 0 : openN >= 10 ? 5 : open ? 3 : waits ? 1 : 0;
    const parts = { req, urg, prof, fr: frP, seat }, score = req + urg + prof + frP + seat;
    const wscore = (req + urg) * W.degree + prof * W.professors + frP * W.friends * frX + seat;
    let inPlan = null, planSec = null;
    for (const Pk of AT_PLANS) { const id = (TC.plans[Pk] || []).find(x => SEC[x] && SEC[x].code === code); if (id) { inPlan = Pk; planSec = SEC[id]; break; } }
    const key = audit ? 'a:' + fills.map(b => TC.audit.reqs.indexOf(b)).sort().join('+') : (n ? 'n:' + L.need.indexOf(n) : 'ge:' + geA.slice().sort().join('+'));
    cands.push({ code, n, geA, fills, yr, Y, behind, onTerm, onYear, best, rt, fr, frSec, un, open, parts, score, wscore, inPlan, planSec, prereq: r.st, key, units: unitsOf(code, L) });
  };
  if (audit) { Object.keys(byClass).forEach(c => { if (COURSES[c]) consider(c); }); Object.keys(COURSES).forEach(c => { if (geOf(c).some(a => byArea[a])) consider(c); }); }
  else { L.need.forEach(n => n.codes.forEach(c => { if (COURSES[c]) consider(c); })); Object.keys(COURSES).forEach(c => { if (!needOf[k(c)] && geOf(c).some(a => geNeed[a])) consider(c); }); }
  cands.sort((a, b) => b.wscore - a.wscore || b.score - a.score || a.code.localeCompare(b.code));
  /* Everything filled — only when nothing is open AND nothing is uncheckable: the report's open lines other
     than the total units (that's "N units to go"), or the flowchart's needs, unknowns and an unchosen
     concentration. Never "you're done" on a guess. */
  const left = X ? X.open.length : L.need.length + L.needU.length;
  const allDone = X ? (!X.open.some(b => !auditIsTotal(b)) && !X.unknown.length)
    : (!L.need.length && !L.needU.length && !L.cant.length && !L.concUnchosen);
  return { all: cands, left, audit: !!audit, X, done: allDone };
}
/* One plan's draft: one class per requirement and per code, no clashes, never over the units target or the
   class cap. `keep` = sections already in the plan that the student added — they count toward the units,
   the cap and the clashes, and their classes aren't picked again. C: friends ×2.5. */
function planDraft(R, mode, L, keep) {
  keep = (keep || []).filter(Boolean);
  const target = plUnitsTarget(), cap = plClassCap();
  const list = (mode === 'C' ? planRank(L, { friendsX: 2.5 }) : R).all.slice();
  if (mode !== 'C') list.sort((a, b) => (b.onTerm ? 1 : 0) - (a.onTerm ? 1 : 0) || b.wscore - a.wscore || b.score - a.score || a.code.localeCompare(b.code));
  const chosen = keep.map(s => ({ c: null, sec: s })), keys = {}, codes = {};
  /* a report line takes as many classes as it still needs (one, unless it says "2 needed"): a class whose
     every line is already taken care of by the plan isn't added — BUS 4401 clears both "pick 1" lines it's
     on, so STAT 2170 (the other option of one of them) isn't added beside it */
  const got = new Map(), take = c => (c && c.fills || []).forEach(b => got.set(b, (got.get(b) || 0) + 1));
  /* how many classes a line still takes: "· Courses: … 2 needed", else a class per 3 units needed, else one */
  const room = b => Math.max(1, Math.round((b.courses && +b.courses.need) || (b.units && +b.units.need >= 6 ? Math.floor(+b.units.need / 3) : 0) || 1));
  let units = 0;
  keep.forEach(s => { codes[s.code] = 1; const u = unitsOf(s.code, L); if (u != null) units += u; const c = R.all.find(x => x.code === s.code); if (c) { keys[c.key] = 1; take(c); } });
  for (const c of list) {
    if (units >= target || chosen.length >= cap) break;
    if ((keys[c.key] && !(c.fills && c.fills.some(b => (got.get(b) || 0) < room(b)))) || codes[c.code]) continue;
    if (c.fills && c.fills.length && c.fills.every(b => (got.get(b) || 0) >= room(b))) continue;
    const u = c.units;
    if (u != null && units + u > target) continue;
    const sec = plBestSec(c.code, chosen.map(x => x.sec), true); if (!sec) continue;
    chosen.push({ c, sec }); keys[c.key] = 1; codes[c.code] = 1; take(c); if (u != null) units += u;
  }
  return { ids: chosen.filter(x => x.c).map(x => String(x.sec.id)), units };
}
/* B: A's classes in another section (after registration opens, an at-risk one for an open one). A class
   with no other section that fits keeps A's section only if that one fits next to the rest of B. */
function planDraftB(aIds, keep) {
  keep = (keep || []).filter(Boolean);
  const have = keep.slice(), out = [], codes = new Set(keep.map(s => s.code));
  const byProf = (a, b) => (ratingOf(b.prof) || 0) - (ratingOf(a.prof) || 0) || String(a.id).localeCompare(String(b.id));
  aIds.forEach(id => {
    const s = SEC[id]; if (!s || codes.has(s.code)) return;
    const fits = t => !have.some(h => secClash(t, h));
    const alt = secsOf(s.code).filter(t => t && t.id !== s.id && SEC[t.id] && fits(t));
    const risky = regOpen() && (s.status === 'full' || s.status === 'wait');
    let pick = null;
    if (risky) pick = alt.filter(t => t.status === 'open').sort(byProf)[0] || null;
    if (!pick) pick = alt.filter(t => !regOpen() || t.status !== 'full').sort(byProf)[0] || null;
    if (!pick && fits(s)) pick = s;
    if (!pick) return;
    out.push(String(pick.id)); have.push(pick); codes.add(s.code);
  });
  return out;
}
/* What this phone drafted (tc-drafted:<uid>:<term>): { A: [ids], B: [ids], C: [ids], at, own }. A plan is
   untouched while it holds exactly what was drafted into it; `own` = the student had plans of their own the
   first time the Planner looked, so nothing is ever drafted on this account this term. */
const PLDRAFT_KEY = () => 'tc-drafted:' + ((TC.user && TC.user.id) || '') + ':' + CFG.TERM;
function plDrafted() { try { return JSON.parse(localStorage.getItem(PLDRAFT_KEY()) || 'null') || {}; } catch (e) { return {}; } }
function plDraftedSet(d) { try { localStorage.setItem(PLDRAFT_KEY(), JSON.stringify(d)); } catch (e) {} }
const sameIds = (a, b) => a.length === b.length && a.every(x => b.includes(x));
function plUntouched(k, d) { d = d || plDrafted(); return Array.isArray(d[k]) && sameIds((TC.plans[k] || []).map(String), d[k].map(String)); }
/* A section that's in plans only because it was drafted there: no seat alert for it (syncPlanWatch). */
function draftOnly(id) {
  try { const d = plDrafted(); let any = false; id = String(id);
    for (const k of AT_PLANS) { if ((TC.plans[k] || []).map(String).includes(id)) { if (!(d[k] || []).map(String).includes(id)) return false; any = true; } }
    return any; } catch (e) { return false; }
}
/* Drafting needs the plans to have loaded (a failed read is not an empty plan) and this term's sections. */
const plCanDraft = () => !!TC.plansLoaded && !TC.err.plans && !!TC.seatsLoaded;
function plDraftSlot(k, R, L) {
  const d = plDrafted(), was = (TC.plans[k] || []).map(String), mineIds = (d[k] || []).map(String);
  const keep = was.filter(id => SEC[id] && !mineIds.includes(id)).map(id => SEC[id]);
  const ids = k === 'B' ? planDraftB((TC.plans.A || []).length ? TC.plans.A.slice() : planDraft(R, 'A', L).ids, keep) : planDraft(R, k, L, keep).ids;
  d[k] = ids; d.at = d.at || Date.now(); plDraftedSet(d);
  if (!was.length) TC.planShared[k] = false;   /* drafted, not chosen: private until the student shares it */
  TC.setPlan(k, [...new Set(keep.map(s => String(s.id)).concat(ids))]);
  return ids.length;
}
/* On arrival: the first time, all three — unless the student has plans of their own. After a new report or
   new answers (UI.plRefresh), only the plans still exactly as drafted. */
function plAutoDraft(R, L) {
  const d = plDrafted(), refresh = !!UI.plRefresh; UI.plRefresh = false;
  if (d.own) return false;
  if (!d.at) {
    if (UI.plFresh !== 'done') { if (!UI.plFresh) { UI.plFresh = 'loading'; Promise.resolve().then(() => loadPlans()).catch(() => {}).then(() => { UI.plFresh = 'done'; render(true); }); } return false; }
    if (AT_PLANS.some(k => (TC.plans[k] || []).length)) { plDraftedSet({ own: true, at: Date.now() }); return false; }
    AT_PLANS.forEach(k => plDraftSlot(k, R, L)); return true;
  }
  if (!refresh) return false;
  /* an untouched plan holds only drafted sections, so nothing of the student's is kept or lost */
  const redo = AT_PLANS.filter(k => plUntouched(k, d));
  redo.forEach(k => plDraftSlot(k, R, L));
  return redo.length > 0;
}
const plNames = ids => { const n = ids.map(f => (PEOPLE[f] || {}).short).filter(Boolean); return n.length <= 2 ? n.join(' and ') : n.slice(0, 2).join(', ') + ' and ' + (n.length - 2) + ' more'; };
const plAreas = a => a.length === 1 ? 'GE Area ' + a[0] : 'GE Areas ' + a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
/* The one reason a pick leads with. Never "Behind": "Catch up" (Tate, 2026-10-08). */
function pickReason(c) {
  if (c.behind) return { t: 'Catch up', k: 't-amber', why: c.n ? `A Year ${c.yr} class — you’re in Year ${c.Y}` : `${plAreas(c.geA)} was due Year ${c.yr}` };
  if (c.fills && c.fills.length >= 2) return { t: 'Counts twice', k: 't-teal', why: c.fills.slice(0, 2).map(b => b.label).join(' · ') };
  if (c.un.length >= 2) return { t: `Unlocks ${c.un.length}`, k: 't-blue', why: `Needed before ${c.un[0]} and ${c.un.length - 1} more` };
  if (c.fills && c.fills.length) { const b = c.fills[0]; return b.kind === 'ge' ? { t: b.ge ? 'GE ' + b.ge : 'GE', k: 't-purple', why: b.label } : b.kind === 'conc' ? { t: 'Concentration', k: 't-teal', why: b.label } : (b.oneOf || (b.courses && b.courses.req === 1 && (b.options || []).length > 1)) ? { t: `Pick 1 of ${b.options.length}`, k: 't-blue', why: b.label } : { t: 'Major', k: 't-blue', why: b.label }; }
  if (c.geA.length && !c.n) return { t: plAreas(c.geA).replace('GE Areas', 'GE').replace('GE Area', 'GE'), k: 't-purple', why: `Fills ${plAreas(c.geA)}` };
  if (c.n) return c.n.group === 'conc' ? { t: 'Concentration', k: 't-teal', why: c.n.title || '' } : c.n.choice ? { t: `Pick 1 of ${c.n.codes.length}`, k: 't-blue', why: 'Any one of ' + c.n.codes.join(', ') } : { t: 'Major', k: 't-blue', why: c.onTerm ? 'Next on your flowchart, this term' : `Year ${c.yr}${c.n.term ? ' · ' + c.n.term : ''}` };
  return { t: 'Pick', k: 't-plain', why: '' };
}
/* Everything the report still says is open, folded at the bottom of the Planner (the ledger's list when
   there's no report) — each open line with "Mark done", and the lines the student marked done with Undo. */
function auditNeedCard(X) {
  const open = X ? X.open : [], unk = X ? X.unknown : [], man = X ? [...X.manual] : [];
  if (!open.length && !unk.length && !man.length) return '';
  const idx = b => TC.audit ? TC.audit.reqs.indexOf(b) : -1;
  const row = b => { const offered = (b.options || []).filter(c => COURSES[c]), one = offered.length === 1 ? offered[0] : null, i = idx(b);
    return `<div class="li pl-need">${auditTag(b)}<span class="grow" style="min-width:0"><span class="b tc-nm" style="display:block;font-size:14.5px">${esc(b.label || 'Requirement')}</span><span class="muted b" style="font-size:12.5px">${b.status === 'unknown' ? 'can’t check' : [b.units && b.units.need != null ? auditNum(b.units.need) + ' units' : b.courses && b.courses.need != null ? auditNum(b.courses.need) + ' class' + (+b.courses.need === 1 ? '' : 'es') : '', (b.options || []).length ? (offered.length ? `${offered.length} of ${b.options.length} offered ${esc(CFG.TERM_LABEL)}` : `none of ${b.options.length} offered ${esc(CFG.TERM_LABEL)}`) : ''].filter(Boolean).join(' · ')}</span></span>${one ? `<button class="chev pl-need-go" data-a="openClass" data-x="${esc(one)}" aria-label="Open ${esc(one)}">${ic('chevR', 18)}</button>` : ''}${i >= 0 && b.status === 'not' ? `<button class="pl-mark" data-a="plMarkAsk" data-x="${i}">Mark done</button>` : ''}</div>`; };
  const mrow = b => { const i = idx(b); return `<div class="li pl-manual">${auditTag(b)}<span class="grow" style="min-width:0"><span class="b tc-nm" style="display:block;font-size:14.5px">${esc(b.label || 'Requirement')}</span><span class="muted b" style="font-size:12.5px">Marked done by you · your report says not yet</span></span>${i >= 0 ? `<button class="pl-mark" data-a="plUnmark" data-x="${i}">Undo</button>` : ''}</div>`; };
  const head = open.length || unk.length ? `Still need · all ${open.length}${unk.length ? ` · ${unk.length} can’t check` : ''}${man.length ? ` · ${man.length} marked done` : ''}` : `Marked done by you · ${man.length}`;
  return `<details class="card tc-sec pk-all"${UI.plAllOpen ? ' open' : ''}><summary class="tc-sech" data-a="plAll"><span>${head}</span><span class="chev">${ic('chevR', 18)}</span></summary>${open.map(row).join('')}${unk.map(row).join('')}${man.length ? `${open.length || unk.length ? '<div class="pl-subh">Marked done by you</div>' : ''}${man.map(mrow).join('')}` : ''}</details>`;
}
function planSecsOf(k) { return (TC.plans[k] || []).map(id => SEC[id]).filter(Boolean); }
function planStats(k, L) {
  const secs = planSecsOf(k); let units = 0, unknown = 0; const rs = [];
  secs.forEach(s => { const u = unitsOf(s.code, L); if (u == null) unknown++; else units += u; const r = ratingOf(s.prof); if (r != null) rs.push(r); });
  const fr = new Set(); secs.forEach(s => friendsIn(s.code).forEach(f => fr.add(f)));
  const busy = new Set(); secs.forEach(s => { if (s.s != null && !s.async) [...s.days].forEach(d => busy.add(d)); });
  const off = DAYS.filter(d => !busy.has(d));
  return { n: secs.length, units, unknown, avg: rs.length ? rs.reduce((a, b) => a + b, 0) / rs.length : null, friends: fr.size, off, risky: secs.filter(s => regOpen() && (s.status === 'full' || s.status === 'wait')).length };
}
/* The units chip, never a made-up total: "15 units", "12+ units" when some aren't known, "4 classes" when none are. */
const planUnitsChip = st => !st.unknown ? `${st.units} units` : st.units ? `${st.units}+ units` : `${st.n} class${st.n === 1 ? '' : 'es'}`;
/* One line on how B or C differs from A (Plans tab, Tate's rec 8). */
function planDiffLine(k) {
  if (k === 'A') return '';
  const a = planSecsOf('A'), b = planSecsOf(k); if (!a.length || !b.length) return '';
  const ac = new Set(a.map(s => s.code)), bc = new Set(b.map(s => s.code)), aid = new Set(a.map(s => String(s.id)));
  const added = [...bc].filter(c => !ac.has(c)), gone = [...ac].filter(c => !bc.has(c)), swapped = b.filter(s => ac.has(s.code) && !aid.has(String(s.id))).length;
  const bits = [];
  if (swapped) bits.push(`${swapped} section${swapped === 1 ? '' : 's'} swapped`);
  if (added.length) bits.push('+ ' + added.slice(0, 3).join(', ') + (added.length > 3 ? ` and ${added.length - 3} more` : ''));
  if (gone.length) bits.push('without ' + gone.slice(0, 3).join(', '));
  return bits.length ? 'Plan A ' + (bits[0].startsWith('+') || bits[0].startsWith('without') ? '' : 'with ') + bits.join(' · ') : 'Same classes as Plan A';
}
const PL_DAYS = [['M', 'MON'], ['T', 'TUE'], ['W', 'WED'], ['R', 'THU'], ['F', 'FRI']];
/* why a plan is empty decides what the card offers: a failed read (try again), no data yet (nothing to
   draft from), or a plan the student emptied (Draft it for me — that plan only) */
function planCard(k, L, R, why) {
  const secs = planSecsOf(k), st = planStats(k, L), timed = secs.filter(s => !s.async && s.s != null);
  const col = PL_COL[k], nm = { A: 'Best fit', B: 'Backup', C: 'With friends' }[k];
  const seg = `<div class="pl-seg" role="tablist" aria-label="Plan">${['A', 'B', 'C'].map(x => `<button class="pl-seg-${x} ${x === k ? 'on' : ''}" data-a="plShowPlan" data-x="${x}" role="tab" aria-selected="${x === k}">${x}</button>`).join('')}</div>`;
  const head = `<div class="pl-head"><span class="pl-letter" style="background:${col}">${k}</span><span class="pl-name">${esc(nm)}</span>${seg}</div>`;
  if (TC.err.plans) return `<div class="card pl-card plan-${k}">${head}<div class="pl-empty">Couldn’t load your plans, so nothing was drafted.</div><div class="pl-chips"><button class="btn soft" data-a="plRetryPlans" ${UI.busy.plans ? 'disabled' : ''}>${UI.busy.plans ? 'Loading…' : 'Try again'}</button></div></div>`;
  if (!secs.length) {
    if (why === 'nodata') return `<div class="card pl-card plan-${k}">${head}<div class="pl-empty">Plan ${k} drafts itself once TermChamp has your past classes — upload your report or add them in Past classes.</div></div>`;
    return `<div class="card pl-card plan-${k}">${head}<div class="pl-empty">${k === 'A' ? 'Nothing fits yet — add classes from the picks below.' : `Plan ${k} is empty.`}</div><div class="pl-chips"><button class="btn soft" data-a="plRedraft" data-x="${k}">Draft it for me</button></div></div>`;
  }
  /* the week: five columns, 8a–6p to scale, each class a bar — enough to see the shape of the week */
  const lo = 8 * 60, hi = 18 * 60, span = hi - lo;
  const week = `<div class="pl-days" aria-hidden="true">${PL_DAYS.map(d => `<span>${d[1]}</span>`).join('')}</div><div class="pl-wk" aria-label="Plan ${k} week">${PL_DAYS.map(([d]) => `<div>${timed.filter(s => s.days.includes(d)).map(s => { const top = Math.max(0, Math.min(1, (s.s - lo) / span)), h = Math.max(.08, Math.min(1 - top, (s.e - s.s) / span)); return `<i style="top:${(top * 100).toFixed(1)}%;height:${(h * 100).toFixed(1)}%;background:${col}" title="${esc(s.code)}"></i>`; }).join('')}</div>`).join('')}</div>`;
  const rows = secs.slice().sort((a, b) => (a.s == null ? 9999 : a.s) - (b.s == null ? 9999 : b.s) || a.code.localeCompare(b.code)).map(s => { const r = ratingOf(s.prof), u = unitsOf(s.code, L), c = R ? R.all.find(x => x.code === s.code) : null, ge = c && c.fills && c.fills.find(b => b.kind === 'ge' && b.ge);
    return `<button class="pl-row" data-a="secSheet" data-x="${esc(s.code)}" data-y="${esc(s.id)}"><span class="code">${esc(s.code)}</span><span class="pl-t"><span class="pl-n">${esc(courseName(s.code) || course(s.code).title)}</span><span class="pl-m">${s.async ? 'Online · anytime' : s.s == null ? 'Time not posted' : `${daysLabel(s.days)} ${hs(s.s)}`}${s.prof ? ` · ${esc(profName(s.prof).split(' ').slice(-1)[0])}${r != null ? ' ★ ' + r.toFixed(1) : ''}` : ''}${ge ? ` · GE ${esc(ge.ge)}` : ''}${regOpen() ? ' · ' + secSeatText(s) : ''}</span></span><span class="pl-u">${u != null ? u + ' u' : '— u'}</span></button>`; }).join('');
  const chips = [planUnitsChip(st), st.avg != null ? `★ ${st.avg.toFixed(1)} avg` : '', st.friends ? `${st.friends} friend${st.friends === 1 ? '' : 's'}` : '', st.off.length && st.off.length < 5 ? `${st.off.map(d => DAYN[d].slice(0, 3)).join(', ')} off` : '', st.risky ? `${st.risky} at risk` : '', TC.planShared[k] === false ? 'Only you' : ''].filter(Boolean).map(t => `<span class="chip pl-chip">${esc(t)}</span>`).join('');
  return `<div class="card pl-card plan-${k}">${head}${week}<div class="pl-rows">${rows}</div><div class="pl-chips">${chips}</div><button class="btn pl-edit" style="background:${col}" data-a="plEditPlan" data-x="${k}">Edit Plan ${k}</button></div>`;
}
function pickCard(c) {
  const r = pickReason(c), t = rateTone(c.rt), sec = c.planSec || c.best, nm = courseName(c.code) || course(c.code).title;
  const add = !sec ? '' : c.inPlan ? `<button class="pk-add on" data-a="addPlanSheet" data-x="${esc(sec.id)}" aria-label="${esc(c.code)} is in Plan ${c.inPlan} — change">${ic('check', 20, 2.8)}</button>` : `<button class="pk-add" data-a="addPlanSheet" data-x="${esc(sec.id)}" aria-label="Add ${esc(c.code)} to your plan">${ic('plus', 20, 2.8)}</button>`;
  const prof = sec && sec.prof ? (t ? `<span class="rchip rt-${t.k}" style="background:${t.bg};color:${t.ink}">${starI(12, t.star)} ${c.rt.toFixed(1)} · ${esc(profName(sec.prof).split(' ').slice(-1)[0])}</span>` : `<span class="pk-tag t-plain">No ratings yet · ${esc(profName(sec.prof).split(' ').slice(-1)[0])}</span>`) : '<span class="pk-tag t-plain">Instructor not listed yet</span>';
  const fr = c.fr.length ? `<span class="pk-fr">${avStack(c.fr, 22)}</span>` : '';
  return `<div class="card pk-card"><button class="pk-main" data-a="pickWhy" data-x="${esc(c.code)}"><span class="pk-chips"><span class="code">${esc(c.code)}</span><span class="pk-tag ${r.k}">${esc(r.t)}</span>${c.geA.length && c.fills && !c.fills.some(b => b.kind === 'ge') ? `<span class="pk-tag t-purple">GE ${esc(c.geA[0])}</span>` : ''}</span><span class="pk-nm">${esc(nm)}</span></button><div class="pk-foot">${prof}${fr}${add}</div></div>`;
}
/* Everything filled: the report's every line is filled or in progress (the total units aside), or the
   flowchart has nothing left, nothing it can't check and no concentration to choose — a green card and
   something fun (Tate and Sean's list): only classes with a real section this term, not ones taken or
   being taken, and not ones whose prerequisites aren't met. */
const FUN_CLASSES = __FUN__;
function plDoneView(R) {
  const X = R.X, tot = X && X.total, toGo = tot && tot.status === 'not' && tot.units && tot.units.need != null ? `${auditNum(tot.units.need)} units to go` : '';
  const inp = X ? X.inprog.length : 0;
  const k = c => TCPL.canon(c) || c, done = TCPL.completed(), doneSet = new Set(done.map(k)), mine = [...myCodes()], mineSet = new Set(mine.map(k));
  const preOk = code => { if (!(UI.pl && UI.pl.prereqs)) return true; const rec = TCPL.coursePrereqs(code); if (!rec || !rec.req || !rec.req.length) return true; const s = TCPL.prereqStatus(code, done, [], mine).state; return s === 'met' || s === 'concurrent'; };
  const offered = FUN_CLASSES.filter(f => COURSES[f.code] && secsOf(f.code).length && !doneSet.has(k(f.code)) && !mineSet.has(k(f.code)) && preOk(f.code)).map(f => { const best = plBestSec(f.code), r = best ? ratingOf(best.prof) : null; return { f, best, r, fr: friendsIn(f.code) }; })
    .sort((x, y) => y.fr.length - x.fr.length || (y.r || 0) - (x.r || 0) || x.f.code.localeCompare(y.f.code));
  const show = UI.plFunAll ? offered : offered.slice(0, 4);
  const card = ({ f, best, r, fr }) => { const t = rateTone(r); return `<div class="card pk-card"><button class="pk-main" data-a="openClass" data-x="${esc(f.code)}"><span class="pk-chips"><span class="code">${esc(f.code)}</span><span class="pk-tag t-teal">${esc(f.g)}</span><span class="pk-tag t-plain">${esc(String(f.units))} u</span></span><span class="pk-nm">${esc(f.title)}</span>${f.needs ? `<span class="pk-why">${esc(f.needs)}</span>` : ''}</button><div class="pk-foot">${best && best.prof ? (t ? `<span class="rchip rt-${t.k}" style="background:${t.bg};color:${t.ink}">${starI(12, t.star)} ${r.toFixed(1)} · ${esc(profName(best.prof).split(' ').slice(-1)[0])}</span>` : `<span class="pk-tag t-plain">No ratings yet</span>`) : ''}${regOpen() && best ? `<span class="pk-tag t-plain">${secSeatText(best)}</span>` : ''}${fr.length ? `<span class="pk-fr">${avStack(fr, 22)}</span>` : ''}${best ? `<button class="pk-add" data-a="addPlanSheet" data-x="${esc(best.id)}" aria-label="Add ${esc(f.code)} to your plan">${ic('plus', 20, 2.8)}</button>` : ''}</div></div>`; };
  const sub = [toGo, inp ? `${inp} in progress` : '', X && X.manual.size ? `${X.manual.size} marked done by you` : ''].filter(Boolean).join(' · ');
  return `<div class="pl-done"><div class="pl-done-ico">${ic('check', 30, 3.2)}</div><div class="pl-done-h">All requirements filled</div>${sub ? `<div class="pl-done-s">${esc(sub)}</div>` : ''}</div>
  <div class="pl-sech"><span>Something fun</span>${offered.length > 4 ? `<button class="pl-more" data-a="plFunAll">${UI.plFunAll ? 'Fewer' : `All ${offered.length}`} ›</button>` : ''}</div>
  ${show.length ? `<div class="pl-picks">${show.map(card).join('')}</div>` : `<div class="pk-empty">None of the fun classes have a section you can take in ${esc(CFG.TERM_LABEL)}.</div>`}
  ${X && X.manual.size ? auditNeedCard(X) : ''}`;
}
/* "Registration opens Oct 19" — only when the Planner is planning the term that registration is for. */
const plRegLine = () => !regOpen() && CFG.TERM_LABEL === CFG.REGISTRATION_TERM ? ` · Registration opens ${esc(regOpensText())}` : '';
/* What matters most is asked once, on the Planner, until it's answered — reopened if anything closed it. */
function plAskPrefs() {
  if (TC.prefs || UI.sheet || UI.plPrefsT) return;
  UI.plPrefsT = setTimeout(() => { UI.plPrefsT = 0; if (!TC.prefs && !UI.sheet && S.schedTab === 'planner') { UI.sheet = { type: 'plPrefs' }; render(true); } }, 50);
}
function plannerView() {
  const g = plGate(); if (g.html) return g.html;
  const { L, P } = g;
  if (!L) return `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div><p class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">We don’t have this major’s flowchart yet, so we can’t pick your next classes. Explore has every class this term.</p><button class="btn soft" style="margin-top:12px" data-a="tab" data-x="explore">Open Explore</button></div>`;
  const none = plNoRecord(), fy = firstYearEmpty(P.class_standing);
  /* no report yet: the one card (a first-year before grades post goes straight to the flowchart) */
  if (none && !fy && !TC.audit && !plSkipped()) return dprFirstCard();
  const term = `<div class="pl-term">${esc(CFG.TERM_LABEL)}</div>`;
  /* first open: what matters most — asked where the answer changes what's on screen */
  if (!TC.prefs) { plAskPrefs(); return `<div class="pl-top"><div>${term}</div></div><div class="card tc-sec pl-ask"><div class="b" style="font-size:17px">What matters most?</div><p class="muted b" style="font-size:14px;margin:6px 0 12px;line-height:1.45">Your plan is built around it.</p><button class="btn" data-a="plPrefsOpen">Answer</button></div>`; }
  const preWait = UI.pl.prereqs === undefined;
  if (!TC.seatsLoaded) return `<div class="pl-top"><div>${term}</div></div>` + (TC.err.seats ? `<div class="pk-empty">Couldn’t load this term’s classes, so there’s nothing to plan with right now.<button class="btn soft" style="margin-top:10px" data-a="retrySeats">Try again</button></div>` : loadingCard('Loading this term’s classes…'));
  if (preWait) return `<div class="pl-top"><div>${term}</div></div>` + loadingCard('Checking prerequisites…');
  if (TC.err.plans === 'missing') return `<div class="pl-top"><div>${term}</div></div><div class="pk-empty">Plans aren’t set up on this server yet.</div>`;
  let R = planRank(L);
  if (R.done) return `<div class="pl-top"><div>${term}<div class="pl-sub">Nothing left open${plRegLine()}</div></div></div>` + plDoneView(R);
  /* drafted on arrival — only with data to draft from, prerequisites checked, and the plans loaded */
  const data = !none || !!TC.audit || fy;
  if (data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);
  const k = /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A';
  const inPlan = new Set(planSecsOf(k).map(s => s.code));
  const more = R.all.filter(c => !inPlan.has(c.code));
  const shown = UI.plMoreAll ? more : more.slice(0, 3);
  const conc = L.concUnchosen ? TCPL.concInfo(L.major) : null;
  const concCard = conc && conc.list && conc.list.length && !R.audit ? `<div class="card tc-sec pk-conc"><div class="b" style="font-size:15px">Pick your concentration</div><div class="muted b" style="font-size:13px;margin:2px 0 10px;line-height:1.4">Its classes join your picks once you choose.</div><div class="pk-concrow">${conc.list.map(c => `<button class="chip" style="background:var(--bg);min-height:44px;flex:none" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  const w = PREF_LABEL[(TC.prefs || {}).priority] || PREF_LABEL.degree;
  return `<div class="pl-top"><div>${term}<div class="pl-sub">${R.left} requirement${R.left === 1 ? '' : 's'} left${plRegLine()}</div></div><button class="pl-pill" data-a="plPrefsOpen" aria-label="${esc(w)} · ${plUnitsTarget()} units · Edit">${plUnitsTarget()} units · Edit</button></div>
  ${UI.pl.prereqs === false ? '<div class="pk-pre">Prerequisites didn’t load, so nothing was drafted and these picks don’t check them. Check each class page before you add it.</div>' : ''}
  ${none && !R.audit ? dprNudgeRow() : ''}
  ${planCard(k, L, R, data ? '' : 'nodata')}
  <div class="pl-sech"><span>More picks</span>${more.length > 3 ? `<button class="pl-more" data-a="plMoreAll">${UI.plMoreAll ? 'Fewer' : `All ${more.length}`} ›</button>` : ''}</div>
  ${shown.length ? `<div class="pl-picks">${shown.map(pickCard).join('')}</div>` : `<div class="pk-empty">Nothing else on the ${esc(CFG.TERM_LABEL)} list fits what you still need${UI.pl.prereqs ? ' — or you need a prerequisite first' : ''}.</div>`}
  ${concCard}${R.audit ? auditNeedCard(R.X) : stillNeedCard(L)}
  <div class="pk-note">Picks come from what your ${R.audit ? 'report says you still need' : 'flowchart still needs'}, what each class unlocks, who teaches it and who’s in it — never from ads. Drafted plans are only yours until you share them. Cal Poly’s degree audit decides what counts.</div>`;
}
/* ---- sheets ---- */
/* First open: what matters most — one tap (Tate: not three in order) — and units next term. */
SHEETS.plPrefs = sh => {
  const cur = sh.pick || (TC.prefs && TC.prefs.priority) || 'degree', units = sh.units || (TC.prefs && TC.prefs.units) || 16;
  const changed = !!TC.prefs && (cur !== TC.prefs.priority || units !== TC.prefs.units);
  const opt = (k, ico, bg) => `<button class="pp-opt ${cur === k ? 'on' : ''}" data-a="plPrefPick" data-x="${k}" aria-pressed="${cur === k}"><span class="pp-ic" style="background:${bg}">${ico}</span>${esc(PREF_LABEL[k])}<span class="pp-ck">${cur === k ? ic('check', 14, 3.4) : ''}</span></button>`;
  return `<div class="row sb"><h3>What matters most?</h3>${TC.prefs ? `<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button>` : ''}</div>
  <div class="muted b" style="font-size:14px;margin:2px 0 12px">Your plan is built around it.</div>
  <div class="pp-opts">${opt('degree', ic('check', 22, 2.6), 'var(--blue-soft)')}${opt('professors', ic('star', 22, 2.4), 'var(--teal-soft)')}${opt('friends', ic('users', 22, 2.4), 'var(--pink-tint,#FCE7F3)')}</div>
  <div class="b" style="font-size:15px;margin:16px 0 8px">Units next term</div>
  <div class="pp-units" role="group" aria-label="Units next term">${[12, 14, 16, 18, 20].map(u => `<button class="${units === u ? 'on' : ''}" data-a="plPrefUnits" data-x="${u}" aria-pressed="${units === u}">${u}</button>`).join('')}</div>
  ${changed ? '<div class="muted b pp-note" style="font-size:12.5px;margin-top:12px;line-height:1.45">Picks re-rank, and plans still as they were drafted are drafted again. Plans you’ve changed stay as they are.</div>' : ''}
  ${sh.err ? `<div class="tc-err">${esc(sh.err)}</div>` : ''}
  <button class="btn" style="margin-top:16px" data-a="plPrefsSave" ${UI.busy.prefs ? 'disabled' : ''}>${UI.busy.prefs ? 'Saving…' : TC.prefs ? 'Save' : 'Build my plan'}</button>`;
};
/* "Mark done": asked once, saying what it does and doesn't do. */
SHEETS.plMark = sh => {
  const b = TC.audit && TC.audit.reqs[sh.i]; if (!b) return '';
  return `<div class="row sb"><h3>Mark it done?</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <div class="pm-line">${auditTag(b)}<b>${esc(b.label || 'Requirement')}</b></div>
  <p class="muted b pm-p">Your report says this isn’t satisfied yet. If you know it counts — a class Cal Poly hasn’t moved onto this line — TermChamp will treat it as done: it won’t count as left and gets no picks.</p>
  <p class="muted b pm-p small">Cal Poly’s degree audit still decides what counts, so ask your advisor to fix it there too. Undo it any time under Still need.</p>
  <button class="btn" style="margin-top:16px" data-a="plMarkDo" ${UI.busy.mark ? 'disabled' : ''}>${UI.busy.mark ? 'Saving…' : 'Mark as done'}</button>`;
};
/* Why a pick is where it is: the five parts, with the facts behind each. */
SHEETS.pickWhy = sh => {
  const g = plGate(); const L = g.L; if (!L || !TC.seatsLoaded) return `<div class="row sb"><h3>Why it’s here</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>${g.html || loadingCard('Loading…')}`;
  const R = planRank(L), c = R.all.find(x => x.code === sh.code);
  if (!c) return `<div class="row sb"><h3>Why it’s here</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div><div class="muted b" style="margin-top:8px">${esc(sh.code)} isn’t one of your picks any more.</div>`;
  const r = pickReason(c), nm = courseName(c.code) || course(c.code).title, sec = c.planSec || c.best, W = plWeights();
  const bars = PL_PARTS.map(([k, lab, max, col]) => { const v = c.parts[k], off = k === 'seat' && !regOpen(); return `<div class="pw-row ${off ? 'off' : ''}"><span class="pw-lab">${lab}</span><span class="pw-track">${off ? '' : `<i style="width:${Math.round(100 * v / max)}%;background:${col}"></i>`}</span><span class="pw-val">${off ? esc(regOpensText()) : v}</span></div>`; }).join('');
  const out = [];
  if (c.fills && c.fills.length) out.push(['#1D4ED8', c.fills.length === 1 ? `Not satisfied on your report: ${c.fills[0].label}` : `Fills ${c.fills.length} on your report: ${c.fills.map(b => b.label).join(' · ')}`]);
  else if (c.n) out.push(['#1D4ED8', c.n.choice ? `Your flowchart: any one of ${c.n.codes.join(', ')}` : `On your flowchart · Year ${c.yr}${c.n.term ? ' ' + c.n.term : ''}`]);
  else if (c.geA.length) out.push(['#1D4ED8', `Fills ${plAreas(c.geA)}`]);
  if (c.behind) out.push(['#C2410C', `Due Year ${c.yr} — you’re in Year ${c.Y}`]); else if (c.onTerm) out.push(['#C2410C', 'Your flowchart’s own class this term']); else if (c.onYear) out.push(['#C2410C', `Your flowchart’s class this year`]);
  if (c.un.length) out.push(['#C2410C', `Unlocks ${c.un.slice(0, 2).join(' and ')}${c.un.length > 2 ? ` and ${c.un.length - 2} more` : ''}`]);
  if (sec && sec.prof) { const top = Math.max(0, ...secsOf(c.code).map(s => ratingOf(s.prof) || 0)), wr = ratingOf(sec.prof); out.push(['#15803D', `${profName(sec.prof)}${wr != null ? ' ★ ' + wr.toFixed(1) : ' · no ratings yet'}${secsOf(c.code).length > 1 ? (wr != null && wr >= top ? ` · best of ${secsOf(c.code).length}` : ` · 1 of ${secsOf(c.code).length} sections`) : ''}`]); }
  if (c.fr.length) out.push(['#BE185D', `${plNames(c.fr)} ${c.fr.length === 1 ? 'is' : 'are'} taking it${c.frSec.length ? ' · same section' : ''}`]);
  if (regOpen() && sec) out.push(['#475569', secSeatText(sec).replace(/<[^>]+>/g, '')]);
  if (c.prereq === 'concurrent') out.push(['#475569', 'Take it with its corequisite']);
  const wline = `Weighted for ${esc(PREF_LABEL[(TC.prefs || {}).priority] || PREF_LABEL.degree).toLowerCase()} (×${W.degree === 1.5 ? '1.5 on requirements' : W.professors === 1.5 ? '1.5 on professors' : '1.5 on friends'})`;
  return `<div class="row sb"><span class="pk-chips"><span class="code">${esc(c.code)}</span><span class="pk-tag ${r.k}">${esc(r.t)}</span></span><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <div class="row sb" style="margin-top:8px;align-items:flex-start"><h3 style="font-size:20px;flex:1;margin:0">${esc(nm)}</h3><span class="pw-score">${c.score}</span></div>
  <div class="pw-bars">${bars}</div>
  <div class="pw-why">${out.map(x => `<div class="why"><span class="dot" style="background:${x[0]}"></span>${esc(x[1])}</div>`).join('')}</div>
  <div class="muted b" style="font-size:12px;margin-top:6px">${wline}</div>
  <div class="pw-acts">${sec ? `<button class="btn" data-a="addPlanSheet" data-x="${esc(sec.id)}">${c.inPlan ? 'In Plan ' + c.inPlan + ' · change' : 'Add to Plan ' + (/^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A')}</button>` : '<span></span>'}<button class="btn soft" data-a="openClass" data-x="${esc(c.code)}">Class</button></div>`;
};
