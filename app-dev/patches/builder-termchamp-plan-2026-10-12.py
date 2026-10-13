#!/usr/bin/env python3
"""The Builder: what's left, then TermChamp's plan as a week; your plans change only when you set one (Tate, 2026-10-12).

Tate: "Builder ... shows spring 2027 ... the units ... your registration date, the what matters most ... make that to where
you rank them ... one, two, and three ... shows your major, business administration, financial management ... maybe it
doesn't need to show concentration underneath ... it should show the catalog that the degree progress report captures ...
its own thing ... two left to graduate ... maybe those collapse, which just shows the two ... underneath ... the recommended
term champ plan and take away, show the five in progress this term ... Plan A puts in the classes already into a little
mocked up schedule week ... the best possible one of that and the approved elective ... Plan B should show maybe different
option for both. And then plan C ... the plans are separate from this ... they could click a button like set as plan A, or
it could be like change out this class ... you go to plans, it is kind of what you've created in Builder."

- What matters most is ranked 1, 2, 3 (tap them in order); the ranking weighs the picks (1.5 / 1.0 / 0.6 as before). The
  ranking is saved with planner_prefs.ranking when RUN 19 is in, else on the phone (the first stays in `priority`).
- The top card: "Business Administration · Financial Management" on one line; the report's catalog as its own row
  ("Fall Quarter 2023" · from your report, Oct 8, 2026); "N left to graduate" (a tap opens or folds) and the count and bar.
  Folded, each requirement is one line saying which class TermChamp's plan has for it; open, each is the full row with
  Mark done. No options under each line any more (the plan below has them), no in-progress row, no catalog footnote.
- TermChamp's Plan A, B, C: a week (the app's own grid, your work and practice on it), Anytime classes, then each class.
  A: the best class for each requirement left first, then the best picks to your units. B and C: a different class for
  each requirement where one fits (else another section), then picks that differ. A requirement the report names no
  classes for (Approved Elective, a concentration line) gets one from your concentration's electives, and says so.
- Tap a class: why it's there, Swap for (another section, another class for the same requirement or slot), Take it out,
  or Add just this to your plan. Swaps stay on this phone for the term ("Back to TermChamp's pick" undoes them).
- "Set as Plan A" copies it to your Plan A (Undo). The Builder no longer drafts into Plans by itself: Plans holds what you
  set or added. An empty plan points to the Builder.
Usage: python3 builder-termchamp-plan-2026-10-12.py <repo-dir>   (replayable on build 2026-10-12 03:20)"""
import sys, os
PA = os.path.join(sys.argv[1], 'app', 'index.html'); S = open(PA, encoding='utf-8').read()
def rep(a, b, label, n=1):
    global S
    if S.count(a) != n: sys.exit(f'{label}: anchor matched {S.count(a)}x (want {n})')
    S = S.replace(a, b)

# ---------------------------------------------------------------- what matters most, ranked
rep("""const PREF_LABEL = { degree: 'Finishing my degree', professors: 'Great professors', friends: 'Classes with friends' };""",
    """const PREF_LABEL = { degree: 'Finishing my degree', professors: 'Great professors', friends: 'Classes with friends' };
const PREF_SHORT = { degree: 'Degree', professors: 'Professors', friends: 'Friends' };
/* (2026-10-12) ranked 1, 2, 3 (Tate: "make that to where you rank them"); a ranking that isn't all three falls back to the first's */
const prefOk = o => Array.isArray(o) && o.length === 3 && ['degree', 'professors', 'friends'].every(k => o.includes(k));
const prefOrder = () => TC.prefs && prefOk(TC.prefs.order) ? TC.prefs.order : PREF_ORDER[(TC.prefs && TC.prefs.priority) || 'degree'] || PREF_ORDER.degree;""", 'pref order')
rep("""  try { const c = JSON.parse(localStorage.getItem(PREFS_KEY()) || 'null'); if (c && PREF_ORDER[c.priority]) TC.prefs = { priority: c.priority, units: +c.units || 16, local: true }; } catch (e) {}
  let r; try { r = await TC.client().from('planner_prefs').select('priority,units').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.prefs = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.prefs;
  if (r.data && PREF_ORDER[r.data.priority]) TC.prefs = { priority: r.data.priority, units: +r.data.units || 16, local: false };""",
    """  let lo = null; try { const c = JSON.parse(localStorage.getItem(PREFS_KEY()) || 'null'); if (c && PREF_ORDER[c.priority]) { lo = prefOk(c.order) && c.order[0] === c.priority ? c.order : null; TC.prefs = { priority: c.priority, units: +c.units || 16, order: lo, local: true }; } } catch (e) {}
  /* the ranking column is RUN 19's: without it, read the rest and keep the ranking on the phone */
  const sel = cols => TC.client().from('planner_prefs').select(cols).eq('user_id', TC.user.id).maybeSingle();
  let r; try { r = await sel('priority,units,ranking'); if (r.error && /ranking/.test(r.error.message || '')) { TC.prefsNoRank = true; r = await sel('priority,units'); } } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.prefs = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.prefs;
  if (r.data && PREF_ORDER[r.data.priority]) { const ro = r.data.ranking ? String(r.data.ranking).split(',') : null;
    TC.prefs = { priority: r.data.priority, units: +r.data.units || 16, order: prefOk(ro) && ro[0] === r.data.priority ? ro : lo && lo[0] === r.data.priority ? lo : null, local: false }; }""", 'load prefs')
rep("""TC.savePrefs = async function (priority, units) {
  if (!PREF_ORDER[priority]) priority = 'degree';
  units = Math.min(20, Math.max(12, +units || 16));
  TC.prefs = { priority, units, local: true };
  try { localStorage.setItem(PREFS_KEY(), JSON.stringify({ priority, units })); } catch (e) {}
  if (TC.err.prefs === 'missing') return null;
  const q = await TC.client().from('planner_prefs').upsert({ user_id: TC.user.id, priority, units, updated_at: new Date().toISOString() }, { onConflict: 'user_id' });""",
    """TC.savePrefs = async function (priority, units, order) {
  if (!PREF_ORDER[priority]) priority = 'degree';
  units = Math.min(20, Math.max(12, +units || 16));
  order = prefOk(order) && order[0] === priority ? order.slice() : PREF_ORDER[priority];
  TC.prefs = { priority, units, order, local: true };
  try { localStorage.setItem(PREFS_KEY(), JSON.stringify({ priority, units, order })); } catch (e) {}
  if (TC.err.prefs === 'missing') return null;
  const row = { user_id: TC.user.id, priority, units, updated_at: new Date().toISOString() };
  if (!TC.prefsNoRank) row.ranking = order.join(',');
  let q = await TC.client().from('planner_prefs').upsert(row, { onConflict: 'user_id' });
  if (q.error && row.ranking && /ranking/.test(q.error.message || '')) { TC.prefsNoRank = true; delete row.ranking; q = await TC.client().from('planner_prefs').upsert(row, { onConflict: 'user_id' }); }""", 'save prefs')
rep("""const plWeights = () => { const p = (TC.prefs && PREF_ORDER[TC.prefs.priority]) ? PREF_ORDER[TC.prefs.priority] : PREF_ORDER.degree; const w = {};""",
    """const plWeights = () => { const p = prefOrder(); const w = {};""", 'weights')

rep("Prerequisites didn’t load, so nothing was drafted and these picks don’t check them.", "Prerequisites didn’t load, so TermChamp’s plan doesn’t check them.", 'prereq note')
rep("Picks re-rank, and plans still as they were drafted are drafted again. Plans you’ve changed stay as they are.", "TermChamp’s plans are worked out again in this order. Your own plans stay as they are.", 'prefs note')
# the sheet: tap them in order
rep("""SHEETS.plPrefs = sh => {
  const cur = sh.pick || (TC.prefs && TC.prefs.priority) || 'degree', units = sh.units || (TC.prefs && TC.prefs.units) || 16;
  const changed = !!TC.prefs && (cur !== TC.prefs.priority || units !== TC.prefs.units);
  const opt = (k, ico, bg) => `<button class="pp-opt ${cur === k ? 'on' : ''}" data-a="plPrefPick" data-x="${k}" aria-pressed="${cur === k}"><span class="pp-ic" style="background:${bg}">${ico}</span>${esc(PREF_LABEL[k])}<span class="pp-ck">${cur === k ? ic('check', 14, 3.4) : ''}</span></button>`;
  return `<div class="row sb"><h3>What matters most?</h3>${TC.prefs ? `<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button>` : ''}</div>
  <div class="muted b" style="font-size:14px;margin:2px 0 12px">Your plan is built around it.</div>""",
    """SHEETS.plPrefs = sh => {
  if (!sh.rank) sh.rank = prefOrder().slice();
  const units = sh.units || (TC.prefs && TC.prefs.units) || 16, rk = sh.rank, done = rk.length === 3;
  const changed = !!TC.prefs && (rk.join() !== prefOrder().join() || units !== TC.prefs.units);
  /* (2026-10-12) ranked: tap them in order; a ranked one tapped again un-ranks it and what came after */
  const opt = (k, ico, bg) => { const n = rk.indexOf(k) + 1; return `<button class="pp-opt ${n ? 'on' : ''}" data-a="plPrefPick" data-x="${k}" aria-pressed="${!!n}" aria-label="${esc(PREF_LABEL[k])}${n ? ', number ' + n : ', not ranked'}"><span class="pp-ic" style="background:${bg}">${ico}</span>${esc(PREF_LABEL[k])}<span class="pp-ck pp-n">${n || ''}</span></button>`; };
  return `<div class="row sb"><h3>What matters most?</h3>${TC.prefs ? `<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button>` : ''}</div>
  <div class="muted b" style="font-size:14px;margin:2px 0 12px">${done ? 'Your plan is built around them, in this order. Tap 1 to rank again.' : `Tap what matters ${rk.length ? 'next' : 'most'}.`}</div>""", 'prefs sheet')
rep("""  <button class="btn" style="margin-top:16px" data-a="plPrefsSave" ${UI.busy.prefs ? 'disabled' : ''}>${UI.busy.prefs ? 'Saving…' : TC.prefs ? 'Save' : 'Build my plan'}</button>`;
};""", """  <button class="btn" style="margin-top:16px" data-a="plPrefsSave" ${UI.busy.prefs || !done ? 'disabled' : ''}>${UI.busy.prefs ? 'Saving…' : TC.prefs ? 'Save' : 'Build my plan'}</button>`;
};""", 'prefs save btn')
rep("""  plPrefPick: k => { if (UI.sheet && UI.sheet.type === 'plPrefs' && PREF_ORDER[k]) { UI.sheet.pick = k; render(true); } },""",
    """  plPrefPick: k => { const sh = UI.sheet; if (!sh || sh.type !== 'plPrefs' || !PREF_ORDER[k]) return;
    const rk = sh.rank || prefOrder().slice(), i = rk.indexOf(k);
    if (i >= 0) rk.splice(i); else { rk.push(k); if (rk.length === 2) rk.push(['degree', 'professors', 'friends'].find(x => !rk.includes(x))); }
    sh.rank = rk; render(true); },""", 'pref pick')
rep("""    const before = TC.prefs ? { priority: TC.prefs.priority, units: TC.prefs.units } : null;
    sh.err = null; UI.busy.prefs = 1; render(true);
    let e; try { e = await TC.savePrefs(sh.pick || (before && before.priority) || 'degree', sh.units || (before && before.units) || 16); } catch (x) { e = 'Couldn’t save that — try again.'; }
    UI.busy.prefs = 0; if (e) { sh.err = e; return render(true); }
    /* new answers: picks re-rank, and plans still exactly as drafted are drafted again */
    if (before && (before.priority !== TC.prefs.priority || before.units !== TC.prefs.units)) UI.plRefresh = true;""",
    """    const before = TC.prefs ? { order: prefOrder().join(), units: TC.prefs.units } : null, rk = sh.rank || prefOrder();
    if (rk.length !== 3) return;
    sh.err = null; UI.busy.prefs = 1; render(true);
    let e; try { e = await TC.savePrefs(rk[0], sh.units || (TC.prefs && TC.prefs.units) || 16, rk); } catch (x) { e = 'Couldn’t save that — try again.'; }
    UI.busy.prefs = 0; if (e) { sh.err = e; return render(true); }
    /* new answers: TermChamp's plans are worked out again (your own plans stay as they are) */
    if (before && (before.order !== prefOrder().join() || before.units !== TC.prefs.units)) UI.plRefresh = true;""", 'prefs save')

# ---------------------------------------------------------------- a concentration line the report names no classes for
rep("""  auditOpen.forEach(b => { (b.options || []).forEach(c => { (byClass[k(c)] = byClass[k(c)] || []).push(b); }); plGeArea(b).forEach(a => { (byArea[a] = byArea[a] || []).push(b); }); });""",
    """  auditOpen.forEach(b => { (b.options || []).forEach(c => { (byClass[k(c)] = byClass[k(c)] || []).push(b); }); plGeArea(b).forEach(a => { (byArea[a] = byArea[a] || []).push(b); }); });
  /* (2026-10-12) a concentration line the report names no classes for (Approved Elective): TermChamp suggests from your
     concentration's electives on the flowchart — and says that's what it is */
  const sugg = new Set(), concNm = (TC.audit && TC.audit.conc) || ((TC.profile || {}).concentration) || '';
  const concE = concNm ? ((TCPL.concInfo(L.major).list || []).find(x => x.name === concNm || meConc(x.name) === meConc(concNm)) || null) : null;
  if (concE) auditOpen.filter(b => b.kind === 'conc' && !(b.options || []).length && !plGeArea(b).length && !auditIsTotal(b)).forEach(b => {
    (concE.electives || (concE.classes || []).map(x => x[0])).map(c => Array.isArray(c) ? c[0] : c).filter(c => c && !doneSet.has(k(c)) && !mineSet.has(k(c))).forEach(c => { (byClass[k(c)] = byClass[k(c)] || []).push(b); sugg.add(b); });
  });""", 'conc electives')
rep("""  return { all: cands, left, audit: !!audit, X, done: allDone };""", """  return { all: cands, left, audit: !!audit, X, done: allDone, sugg };""", 'R sugg')

# ---------------------------------------------------------------- TermChamp's plans
rep("""/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */""",
    """/* (2026-10-12) TermChamp's Plan A, B and C — what the Builder would take, apart from your own plans.
   The best class for each requirement left first (B and C: one an earlier plan didn't use, where one fits; else another
   section), then the best picks to your units, never over each other, your registered classes or your work. */
function plRecDraft(R, L, k, prev) {
  const reqs = plLeftReqs(R, L), prevIds = new Set(prev.flat().map(String));
  const prevCodes = new Set(prev.flat().map(id => SEC[id] && SEC[id].code).filter(Boolean));
  const reg = splitTerms() ? personSecs('me').filter(s => s && s.code && !s.noTime && !s.async) : [];
  const keep = [], have = new Set(), covered = new Set();
  reqs.forEach(q => {
    if (q.b && covered.has(q.b)) return;
    const ord = q.cands.filter(c => !have.has(c.code)).sort((a, b) => (prevCodes.has(a.code) ? 1 : 0) - (prevCodes.has(b.code) ? 1 : 0) || R.all.indexOf(a) - R.all.indexOf(b));
    for (const c of ord) { const sec = plDraftSec(c.code, keep.concat(reg), prevIds); if (!sec) continue; keep.push(sec); have.add(c.code); (c.fills || []).forEach(b => covered.add(b)); break; }
  });
  return [...new Set(keep.map(s => String(s.id)).concat(planDraft(R, k, L, keep, prev).ids))];
}
const RECK = () => 'tc-rec:' + ((TC.user && TC.user.id) || '') + ':' + CFG.TERM;
function recEdits() {
  if (!UI.recEdit || UI.recEdit._k !== RECK()) { let o = {}; try { o = JSON.parse(localStorage.getItem(RECK()) || '{}') || {}; } catch (e) {} UI.recEdit = Object.assign({}, o, { _k: RECK() }); }
  return UI.recEdit;
}
function recEditSet(k, ids) {
  const e = recEdits(); if (ids) e[k] = ids.map(String); else delete e[k];
  try { const o = Object.assign({}, e); delete o._k; localStorage.setItem(RECK(), JSON.stringify(o)); } catch (x) {}
}
function plRecIds(R, L) {
  if (!R._rec) { const A = plRecDraft(R, L, 'A', []), B = plRecDraft(R, L, 'B', [A]), C = plRecDraft(R, L, 'C', [A, B]); R._rec = { A, B, C }; }
  return R._rec;
}
function plRecOf(R, L, k) { const e = recEdits()[k]; return Array.isArray(e) ? e.filter(id => SEC[id]) : plRecIds(R, L)[k]; }
let PL_CTX = null;   /* the Builder's last R and L, for the class sheet and its swaps */
function plRecCard(R, L, k, why) {
  const head = planTabs(k), col = PL_COL[k];
  if (why === 'nodata') return `<div class="card pl-card pla plr plan-${k}">${head}<div class="pl-empty">TermChamp’s Plan ${k} is worked out once it has your past classes — upload your report or add them in Past classes.</div></div>`;
  const ids = plRecOf(R, L, k), secs = ids.map(id => SEC[id]).filter(Boolean), edited = Array.isArray(recEdits()[k]);
  const reset = edited ? `<button class="plr-reset" data-a="recReset" data-x="${k}">Back to TermChamp’s pick</button>` : '';
  if (!secs.length) return `<div class="card pl-card pla plr plan-${k}">${head}<div class="pl-rech">TermChamp’s Plan ${k}</div><div class="pl-empty">Nothing fits ${esc(CFG.TERM_LABEL)} yet.</div>${reset}</div>`;
  const timed = secs.filter(plOnWeek), any = secs.filter(s => !plOnWeek(s));
  let units = 0, unk = 0; secs.forEach(s => { const u = unitsOf(s.code, L); if (u == null) unk++; else units += u; });
  const rs = secs.map(s => ratingOf(s.prof)).filter(r => r != null), avg = rs.length ? rs.reduce((a, b) => a + b, 0) / rs.length : null;
  const fr = new Set(); secs.forEach(s => friendsInSec(s.id).forEach(f => fr.add(f)));
  const free = PL_DAYS.filter(([d]) => !timed.some(s => s.days.includes(d)) && !TC.commits.some(c => String(c.days || '').includes(d))).map(([d]) => DAYN[d]);
  const reqOf = s => { const c = R.all.find(y => y.code === s.code); return c && c.fills && c.fills.length ? c.fills[0] : c && c.n ? { label: c.n.title || '' } : null; };
  const rows = secs.slice().sort((a, b) => (a.s == null ? 9999 : a.s) - (b.s == null ? 9999 : b.s) || a.code.localeCompare(b.code)).map(x => {
    const r = ratingOf(x.prof), t = rateTone(r), who = x.prof ? esc(profName(x.prof).split(' ').slice(-1)[0]) : '', q = reqOf(x), c = R.all.find(y => y.code === x.code), why2 = c ? pickReason(c) : null;
    const tag = q && q.label && !auditIsTotal(q) ? `<span class="pk-tag t-amber plr-for">${esc(String(q.label).replace(/^Business Major /, '').slice(0, 32))}</span>` : why2 && why2.t !== 'Pick' ? `<span class="pk-tag ${why2.k}">${esc(why2.t)}</span>` : '';
    const right = t ? `<span class="pla-rt"><b style="color:${t.ink}">★ ${r.toFixed(1)}</b>${who ? `<small>${who}</small>` : ''}</span>` : who ? `<span class="pla-rt"><small>${who}</small></span>` : '';
    return `<button class="pl-row" data-a="recOpen" data-x="${esc(x.code)}" data-y="${esc(x.id)}"><span class="code pla-code">${esc(x.code)}</span><span class="pl-t"><span class="pl-n">${esc(courseName(x.code) || course(x.code).title)}</span><span class="pl-m">${x.async ? 'Online · anytime' : x.s == null ? 'Time not posted' : esc(daysLabel(x.days) + ' ' + hs(x.s) + '–' + hs(x.e))}${regOpen() ? ' · ' + esc(String(secSeatText(x)).replace(/<[^>]*>/g, '')) : ''}</span>${tag ? `<span class="pl-tags">${tag}</span>` : ''}</span>${right}</button>`;
  }).join('');
  const week = timed.length || TC.commits.length ? `<div class="plancol plan-${k} plr-wk">${grid(timed, { sel: S.homeDays['rec:' + k], act: 'homeDay', key: 'rec:' + k, blockAct: 'recOpen', H: 280, faces: true, extra: cmBlocks('me') })}</div>` : '';
  const anyTxt = x => x.async ? 'online' : x.s == null ? 'time not posted' : daysLabel(x.days) + ' ' + hs(x.s);
  const anyRow = any.length ? `<div class="pla-any plr-any"><span class="pla-anyl">Anytime</span>${any.map(x => `<button class="pla-chip" data-a="recOpen" data-x="${esc(x.code)}" data-y="${esc(x.id)}">${esc(x.code)} · ${esc(anyTxt(x))}</button>`).join('')}</div>` : '';
  const chips = [unk ? '' : `${units} units`, avg != null ? `★ ${avg.toFixed(1)} professors` : '', fr.size ? `${fr.size} friend${fr.size === 1 ? '' : 's'}` : '', free.length && free.length < 5 ? `${free.join(', ')} free` : ''].filter(Boolean).map(x => `<span class="chip pl-chip">${esc(x)}</span>`).join('');
  const mine = (TC.plans[k] || []).map(String), same = mine.length === ids.length && ids.every(id => mine.includes(String(id)));
  const recA = k === 'A' ? null : plRecOf(R, L, 'A').map(String), likeA = recA && recA.length === ids.length && ids.every(id => recA.includes(String(id)));
  const act = TC.err.plans ? `<div class="pl-empty">Couldn’t load your plans, so this can’t be set as Plan ${k} yet.</div><div class="pl-chips"><button class="btn soft" data-a="plRetryPlans" ${UI.busy.plans ? 'disabled' : ''}>${UI.busy.plans ? 'Loading…' : 'Try again'}</button></div>`
    : same ? `<div class="plr-same">${ic('check', 16, 3)} This is your Plan ${k}</div>`
    : `<button class="btn plr-set" data-a="recSet" data-x="${k}" style="background:${col}">Set as Plan ${k}</button><div class="plr-note">${mine.length ? `Replaces the ${mine.length} class${mine.length === 1 ? '' : 'es'} in your Plan ${k} — you can undo it.` : `Your Plan ${k} is empty.`}</div>`;
  return `<div class="card pl-card pla plr plan-${k}">${head}<div class="pl-rech">TermChamp’s Plan ${k}</div><div class="plr-sub">What TermChamp would take: what you have left first, then your priorities and your week. Tap a class to change it out.</div>${TC.commits.length ? `<button class="pl-clear" data-a="sheet" data-x="cmList"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"></path></svg>Clear of your ${esc(cmWords())}</button>` : ''}${week}${anyRow}${chips ? `<div class="pl-chips">${chips}</div>` : ''}<div class="plr-rows">${rows}</div>${likeA ? '<div class="pl-same">Same as Plan A — these classes have no other section that fits.</div>' : ''}${act}${reset}</div>`;
}
/* A class in TermChamp's plan: why it's there, and what it could be instead */
SHEETS.recSec = sh => {
  const s = SEC[sh.id], ctx = PL_CTX; if (!s || !ctx) return '';
  const { R, L } = ctx, k = sh.k, ids = plRecOf(R, L, k), others = ids.filter(id => String(id) !== String(sh.id)).map(id => SEC[id]).filter(Boolean);
  const reg = splitTerms() ? personSecs('me').filter(x => x && x.code && !x.noTime && !x.async) : [], around = others.concat(reg);
  const fits = x => x && x.id && SEC[x.id] && !around.some(t => secClash(x, t)) && !TC.commits.some(t => secClash(x, t));
  const c = R.all.find(y => y.code === s.code), lines = c && c.fills && c.fills.length ? c.fills : [], r = ratingOf(s.prof), fr = friendsInSec(s.id), why = c ? pickReason(c) : null;
  const chip = (t, cls) => `<span class="chip pl-chip${cls ? ' ' + cls : ''}">${esc(t)}</span>`;
  const whyChips = [lines.length ? chip('Left to graduate · ' + String(lines[0].label || '').slice(0, 40), 'plr-ch-req') : '', r != null ? chip(`★ ${r.toFixed(1)} professor`) : '', fr.length ? chip(`${fr.length} friend${fr.length === 1 ? '' : 's'} in this section`) : '', TC.commits.length ? chip('Clear of your work') : '', why && why.t !== 'Pick' && !lines.length ? chip(why.t) : ''].filter(Boolean).join('');
  const sug = lines.some(b => R.sugg && R.sugg.has(b)) ? `<div class="plr-sug">Your report doesn’t name the classes for ${esc(lines.find(b => R.sugg.has(b)).label || 'this line')}. This one is from your concentration’s electives — check with your advisor that it counts.</div>` : '';
  const inRec = new Set(others.map(x => x.code));
  const sameCls = secsOf(s.code).filter(x => String(x.id) !== String(s.id) && fits(x)).slice(0, 3);
  const pool = lines.length ? R.all.filter(y => y.code !== s.code && !inRec.has(y.code) && (y.fills || []).some(b => lines.includes(b))) : R.all.filter(y => y.code !== s.code && !inRec.has(y.code));
  const alts = []; for (const y of pool) { if (alts.length >= 3) break; const x = plDraftSec(y.code, around, null); if (x) alts.push(x); }
  const opt = (x, lab) => { const rt = ratingOf(x.prof); return `<div class="plr-alt"><span class="grow" style="min-width:0"><span class="code">${esc(x.code)}</span>${lab ? ` <span class="plr-altl">${esc(lab)}</span>` : ''}<span class="plr-altn">${esc(courseName(x.code) || course(x.code).title || '')}</span><span class="plr-altm">${esc([x.async ? 'Online' : x.s == null ? 'Time not posted' : daysLabel(x.days) + ' ' + hs(x.s) + '–' + hs(x.e), x.prof ? profName(x.prof).split(' ').slice(-1)[0] + (rt != null ? ` ★ ${rt.toFixed(1)}` : '') : '', String(secSeatText(x)).replace(/<[^>]*>/g, '')].filter(Boolean).join(' · '))}</span></span><button class="plr-swap" data-a="recSwap" data-x="${esc(k + '|' + s.id + '|' + x.id)}">Swap</button></div>`; };
  const swaps = sameCls.map(x => opt(x, 'other section')).join('') + alts.map(x => opt(x, '')).join('');
  return `<div class="row sb"><div style="min-width:0"><span class="code">${esc(s.code)}</span><h3 style="margin-top:8px">${esc(courseName(s.code) || course(s.code).title || s.code)}</h3></div><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <div class="muted b" style="font-size:14px;margin:4px 0 0">${esc([s.async ? 'Online · anytime' : s.s == null ? 'Time not posted' : daysLabel(s.days) + ' ' + hs(s.s) + '–' + hs(s.e), s.prof ? profName(s.prof) : 'Instructor not listed', String(secSeatText(s)).replace(/<[^>]*>/g, '')].filter(Boolean).join(' · '))}</div>
  ${whyChips ? `<div class="plr-h">Why TermChamp picked it</div><div class="pl-chips">${whyChips}</div>` : ''}${sug}
  <div class="plr-h">Change it out</div>${swaps || `<div class="muted b" style="font-size:13.5px">Nothing else fits this plan’s week.</div>`}
  <button class="btn" style="margin-top:16px;background:${PL_COL[k]}" data-a="addPlanSheet" data-x="${esc(String(sh.id))}">Add just this to my Plan ${k}</button>
  <button class="btn soft plr-drop" style="margin-top:8px" data-a="recDrop" data-x="${esc(k + '|' + s.id)}">Take it out of TermChamp’s plan</button>`;
};

/* ---- the year-by-year grid: the flowchart, every slot in the state the ledger gave it ---- */""", 'rec plans')

rep("""  pickWhy: code => { UI.sheet = { type: 'pickWhy', code }; render(true); },""",
    """  pickWhy: code => { UI.sheet = { type: 'pickWhy', code }; render(true); },
  /* (2026-10-12) TermChamp's plans: open a class, swap it, take it out, start over, or set the plan as yours */
  recOpen: (code, id) => { if (!SEC[id]) return; UI.sheet = { type: 'recSec', k: /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A', id: String(id) }; render(true); },
  recSwap: x => { const [k, from, to] = String(x).split('|'); if (!PL_CTX || !SEC[to]) return; const ids = plRecOf(PL_CTX.R, PL_CTX.L, k).map(String);
    recEditSet(k, ids.map(id => id === from ? to : id)); UI.sheet = null; toast(`${SEC[to].code} is in TermChamp’s Plan ${k}`); render(true); },
  recDrop: x => { const [k, id] = String(x).split('|'); if (!PL_CTX) return; const ids = plRecOf(PL_CTX.R, PL_CTX.L, k).map(String);
    recEditSet(k, ids.filter(y => y !== id)); UI.sheet = null; render(true); },
  recReset: k => { recEditSet(k, null); render(true); },
  recSet: k => { if (!/^[ABC]$/.test(k) || !PL_CTX) return; const ids = plRecOf(PL_CTX.R, PL_CTX.L, k).map(String), before = (TC.plans[k] || []).slice();
    TC.setPlan(k, ids); const d = plDrafted(); d.own = true; plDraftedSet(d);
    toastUndo(`Plan ${k} is set — see it in Plans`, () => { TC.setPlan(k, before); render(true); }); render(true); },
  plLeftFold: () => { UI.plLeftOpen2 = !UI.plLeftOpen2; render(true); },""", 'rec actions')

# ---------------------------------------------------------------- the top card
i0 = S.index("function plLeftCard(R, L, k) {"); i1 = S.index("/* (2026-10-12) TermChamp's Plan A, B and C", i0)
if S.count("function plLeftCard(R, L, k) {") != 1: sys.exit('plLeftCard anchor')
S = S[:i0] + """function plLeftCard(R, L, k, rec) {
  L = L || {};   /* no flowchart: the report alone (R.bare) */
  const X = R.audit ? R.X : null, unk = X ? X.unknown : [];
  const reqs = plLeftReqs(R, L); if (!reqs.length) return '';   /* only lines it couldn't read: the Still need card below says so */
  const idx = X ? new Map((TC.audit.reqs || []).map((b, i) => [b, i])) : null;
  const tot = X && X.total && X.total.status === 'not' && X.total.units && X.total.units.need != null ? auditNum(X.total.units.need) : null;
  /* (2026-10-12) folded: one line each, with the class TermChamp's plan has for it; open: the full row with Mark done */
  const open = !!UI.plLeftOpen2, inRec = new Set((rec || []).map(id => SEC[id] && SEC[id].code).filter(Boolean));
  const recFor = q => (q.cands.find(c => inRec.has(c.code)) || {}).code || '';
  /* the lines TermChamp's plan fills come first (the rest keep their order) */
  if (rec) { const has = q => recFor(q) ? 0 : 1; reqs.sort((a, b) => has(a) - has(b)); }
  const show = UI.plLeftAll ? reqs : reqs.slice(0, 6);
  const line = q => { const code = rec ? recFor(q) : '';
    return `<div class="pll-req pll-line"><span class="pll-ring" aria-hidden="true"></span><span class="pll-rl">${esc(q.label)}</span>${q.b && auditTag(q.b) ? `<span class="pc-tags">${auditTag(q.b)}</span>` : ''}${code ? `<span class="pll-in">Plan ${k} · ${esc(code)}</span>` : ''}</div>`; };
  const full = q => q.b ? `<div class="pll-req">${pcReqRow(q.b, X, L, idx.get(q.b))}</div>` : line(q);
  const body = (open ? show.map(full).join('') + unk.map(b => `<div class="pll-req">${pcReqRow(b, X, L, idx.get(b))}</div>`).join('') : show.map(line).join(''))
    + (reqs.length > 6 ? `<button class="pll-all" data-a="plLeftAll">${UI.plLeftAll ? 'Fewer' : `All ${reqs.length} ›`}</button>` : '');
  /* who you are on one line, and the catalog your report judges you by as its own row */
  const P = TC.profile || {}, major = P.major || L.major || (TC.audit && TC.audit.major) || '';
  const c0 = P.concentration && P.concentration !== 'General / Open' ? meConc(P.concentration) : (TC.audit && TC.audit.conc ? meConc(TC.audit.conc) : '');
  const who = major ? `<div class="pll-who">${esc(major)}${c0 ? ' · ' + esc(c0) : ''}</div>` : '';
  const catRow = X && TC.audit.catalog ? `<div class="pll-cat"><span class="pc-catc ${/quarter/i.test(TC.audit.catalog) ? 'q' : 's'}">${esc(TC.audit.catalog)} catalog</span><span>from your report${TC.audit.printed_on ? ' · ' + esc(pcDate(TC.audit.printed_on)) : ''}</span></div>` : '';
  const F = X ? X.filled.length : L.F || 0, N = X ? X.live.length : L.N || 0, pct = N ? Math.round(100 * F / N) : 0;
  const num = N ? `<div class="pc-nrow"><div class="pc-num"><b>${F} of ${N}</b><span>filled</span></div>${tot ? `<span class="pc-inp">· plus ${tot} units to go</span>` : ''}</div><div class="pc-bar" role="img" aria-label="${F} of ${N} filled"><i style="width:${pct}%"></i></div>` : '';
  const ci = X && !TC.audit.conc && L.concUnchosen ? TCPL.concInfo(L.major) : null;
  const pick = ci && ci.list.length ? `<div class="pc-conc"><div class="b" style="font-size:14.5px;margin-bottom:8px">Pick your concentration</div><div style="display:flex;flex-wrap:wrap;gap:8px">${ci.list.map(c => `<button class="chip" style="background:var(--bg)" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  return `<div class="card pll">${who}${catRow}<button class="pll-h" data-a="plLeftFold" aria-expanded="${open}"><b>${reqs.length}</b><span>${R.audit ? 'left to graduate' : 'left on your flowchart'}</span>${pcChev(open ? 90 : 0)}</button>${num}<div class="pll-list">${body}</div>${pick}</div>`;
}
""" + S[i1:]

# ---------------------------------------------------------------- the Builder screen
rep("""  if (asked && data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);
  const k = /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A';""",
    """  /* (2026-10-12) the Builder no longer drafts into Plans: TermChamp's plans live here, yours change when you set one */
  if (UI.plRefresh) { UI.plRefresh = false; }
  const k = /^[ABC]$/.test(UI.plPlan) ? UI.plPlan : 'A';
  PL_CTX = { R, L };
  const recIds = !waiting && data ? plRecOf(R, L, k) : null;""", 'no auto draft')
rep("""  const w = PREF_LABEL[(TC.prefs || {}).priority] || PREF_LABEL.degree;
  return `<div class="pl-top"><div>${term}</div><button class="pl-pill" data-a="plPrefsOpen" aria-label="${esc(w)} · ${plUnitsTarget()} units · Edit">${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}""",
    """  const w = PREF_LABEL[(TC.prefs || {}).priority] || PREF_LABEL.degree, left = plLeftCard(R, L, k, recIds);
  /* what matters most, in your order */
  const rankRow = `<button class="pl-rank" data-a="plPrefsOpen" aria-label="What matters most: ${esc(prefOrder().map((x, i) => (i + 1) + ' ' + PREF_LABEL[x]).join(', '))} · Edit">${prefOrder().map((x, i) => `<span><b>${i + 1}</b>${esc(PREF_SHORT[x])}</span>`).join('')}</button>`;
  return `<div class="pl-top"><div>${term}</div><button class="pl-pill" data-a="plPrefsOpen" aria-label="${esc(w)} · ${plUnitsTarget()} units · Edit">${plUnitsTarget()} units · Edit</button></div>${rankRow}${plRegBanner()}""", 'header rank')
rep("""  ${plLeftCard(R, L, k)}
  ${waiting ? cmWaitCard(k) : planCard(k, L, R, data ? '' : 'nodata')}""", """  ${left}
  ${waiting ? cmWaitCard(k) : plRecCard(R, L, k, data ? '' : 'nodata')}""", 'rec card in')
rep("""Drafted plans are only yours until you share them. Cal Poly’s degree audit decides what counts.</div>`;""",
    """Your plans change only when you set one, and are only yours until you share them. Cal Poly’s degree audit decides what counts.</div>`;""", 'note')

# Plans: an empty plan points to the Builder
rep("""'<div class="empty"><b>No timed classes</b>Add classes from Explore.</div>'}</div>""",
    """`<div class="empty"><b>${secs.length ? 'No timed classes' : `Nothing in Plan ${S.plan} yet`}</b>${secs.length ? 'Add classes from Explore.' : `Set TermChamp’s Plan ${S.plan} from the Builder, or add classes from Explore.`}${secs.length ? '' : `<button class="btn soft" style="margin-top:10px" data-a="schedTab" data-x="planner">Open the Builder</button>`}</div>`}</div>""", 'plans empty')

# ---------------------------------------------------------------- CSS
rep(".pll-h{display:flex;align-items:baseline;gap:10px;padding:0 2px}",
    """.pll-h{display:flex;align-items:baseline;gap:10px;padding:0 2px}
/* (2026-10-12) the top card, folded; TermChamp's plans; what matters most, ranked */
button.pll-h{width:100%;text-align:left;min-height:52px;margin-top:6px}
button.pll-h svg{margin-left:auto;align-self:center}
.pll-who{font-size:16px;font-weight:900;line-height:1.3;padding:0 2px}
.pll-cat{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-top:8px;padding:0 2px;font-size:12.5px;font-weight:800;color:var(--muted)}
.pll-cat .pc-catc{flex:none}
.pll-list{margin-top:6px}
.pll-line{display:flex;align-items:center;flex-wrap:wrap;gap:6px 10px;padding:10px 2px;margin-top:0}
.pll-line .pll-rl{font-size:15px}
.pll-line .pc-tags{display:inline-flex}
.pll-in{margin-left:auto;font-size:12.5px;font-weight:900;color:var(--blue-t,var(--blue))}
.pl-rank{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:8px 16px 0;padding:0;text-align:left;min-height:32px}
.pl-rank span{display:inline-flex;align-items:center;gap:5px;height:28px;padding:0 10px 0 4px;border-radius:999px;background:var(--tint1);font-size:12.5px;font-weight:900;color:var(--ink)}
.pl-rank b{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;background:var(--blue);color:#fff;font-size:11.5px;font-weight:900}
.pp-n{font-size:13px;font-weight:1000}
.plr-sub{font-size:13px;font-weight:800;color:var(--muted);line-height:1.4;margin:2px 0 12px}
.plr-wk{margin:0 -6px}
.plr-any{margin-top:8px}
.plr-rows{margin-top:10px}
.pl-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:3px}
.plr-set{margin-top:14px;color:#fff}
.plr-note{font-size:12.5px;font-weight:800;color:var(--muted);margin-top:6px;line-height:1.4}
.plr-same{display:flex;align-items:center;gap:6px;margin-top:14px;font-size:14px;font-weight:900;color:var(--teal-t,var(--teal))}
.plr-reset{display:block;margin-top:8px;min-height:40px;font-size:13.5px;font-weight:900;color:var(--blue-t,var(--blue))}
.plr-h{font-size:11.5px;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:16px 0 8px}
.plr-sug{margin-top:10px;padding:10px 12px;border-radius:12px;background:var(--amber-soft);color:var(--amber-ink);font-size:13px;font-weight:800;line-height:1.4}
.plr-alt{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:14px;background:var(--bg);margin-top:6px}
.plr-altl{font-size:12px;font-weight:900;color:var(--muted)}
.plr-altn{display:block;font-size:14.5px;font-weight:900;margin-top:3px}
.plr-altm{display:block;font-size:12.5px;font-weight:800;color:var(--muted)}
.plr-swap{flex:none;height:38px;padding:0 14px;border-radius:999px;background:var(--blue);color:#fff;font-size:13.5px;font-weight:900}
.plr-drop{color:var(--red-ink)}""", 'css')
open(PA, 'w', encoding='utf-8').write(S); print('builder-termchamp-plan: done')
