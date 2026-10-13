#!/usr/bin/env python3
"""Past classes, Tate's option A made simple (2026-10-10), on 23:30 (flowchart marks, Planner card A) + the report flow.

Tate: "for past classes make it so you can fill out the professor you took for each of them lets also find a
way to combine your flowchart and classes youve taken" → canvas "Past Classes and Professors" → "lets do A" →
"make it simpler only the most important text" → "redo this into term champ style but more simple
straightforward and only most important information displayed if its not necessary dont even include it" →
"okay i like this update it".

  · ONE screen, 12px from the screen edge like Home: "N of M filled" + one bar (+ "Degree Progress Report · N left ›" when a report is in), the years
    as tint bars ("Year 3 · 5 of 11"), the open year's Fall / Spring bubbles, then "Other classes" (on the record,
    no spot on the flowchart), then + Log a class / Upload report. The ledger card's bars, legend, can't-check
    list and footnote, the flowchart's key and help line, and the separate "Classes you've taken" card are gone.
  · Every spot shows the CLASS that fills it — GE and elective spots too: the ledger's uncodedSatisfied() now
    remembers the class it claimed (res.with → cell.fill; cell.by is left as it was, so the one-tap undo and
    unitsOf() are unchanged).
  · A row: status dot (the existing one-tap check, or 23:30's check-off circle for a GE / elective / can't-check
    row), code chip, the class's name. A second line only for a class on your record — its professor, or
    "+ Professor" — or "Marked done by you" on a row you checked off. Taking-now shows the professor of your
    section, if any. Transfer / exam credit gets no second line.
  · Tap a class → its sheet: Professor ›, Term ›, Rate <professor>, Remove from my record.
  · "+ Professor" → Who taught it?: professors teaching it now (Cal Poly's class search) and those PolyRatings
    lists for it (their course lists, mapped through course_equiv), a search over all professors (or "Use
    “<typed>”"), Save, I don't remember. Nothing is filled until the student picks. Saved to
    class_history.professor (UPDATE; the table's own policy allows it), so Rate lists them.
  · Right after a report is saved: "Who taught these?" — the record's classes from its three latest terms with no
    professor yet (never transfer credit), each → the picker; Done goes on to the Planner.
  python3 past-classes-simple-2026-10-10.py <repo-dir>
"""
import sys, os
D = sys.argv[1]
PI = os.path.join(D, 'app', 'index.html'); PP = os.path.join(D, 'app', 'planner.js')
PD = os.path.join(D, 'index.html')
A = open(PI, encoding='utf-8').read(); P = open(PP, encoding='utf-8').read(); DK = open(PD, encoding='utf-8').read()

def rep(s, a, b, what, n=1):
    c = s.count(a)
    if c != n: sys.exit(f'past-classes-simple: anchor "{what}" found {c}x (want {n})')
    return s.replace(a, b)

# ---- the class each GE / elective spot was filled by --------------------------------------------------------
# uncodedSatisfied() sits in planner.js's @@LIFTED block, which is index.html's (the desktop's) text verbatim: the
# same edit goes into both, so a rebuild of planner.js keeps it. The desktop ignores the extra `with`.
for nm in ('P', 'DK'):
    t = globals()[nm]
    t = rep(t, "  var res={done:{},taking:{}};", "  var res={done:{},taking:{},with:{}};", 'uc res ' + nm)
    t = rep(t, "        if(claim('done',pred)){ res.done[s.id]=1; return; }\n        if(claim('taking',pred)){ res.taking[s.id]=1; }",
            "        var c=claim('done',pred); if(c){ res.done[s.id]=1; res.with[s.id]=c; return; }\n        c=claim('taking',pred); if(c){ res.taking[s.id]=1; res.with[s.id]=c; }", 'uc fill ' + nm)
    globals()[nm] = t
P = rep(P, "          if (uc.done[sl.id]) { row.f++; cell.state = 'done'; }\n          else if (uc.taking[sl.id]) { row.t++; cell.state = 'taking'; }",
        "          if (uc.done[sl.id]) { row.f++; cell.state = 'done'; if (uc.with && uc.with[sl.id]) cell.fill = uc.with[sl.id]; }\n          else if (uc.taking[sl.id]) { row.t++; cell.state = 'taking'; if (uc.with && uc.with[sl.id]) cell.fill = uc.with[sl.id]; }", 'ledger fill')

# ---- index.html: Past classes ---------------------------------------------------------------------------
i = A.index('function pastView() {'); j = A.index('\n/* ---- The Planner (2026-10-08)', i)
A = A[:i] + r'''function pastView() {
  const g = plGate(); if (g.html) return g.html;
  const { L, P } = g, none = plNoRecord();
  pcPlace(L);
  if (!L) return (none ? dprFirstCard() : '') + `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div><p class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">We don’t have this major’s flowchart yet, so we can’t check your requirements.</p></div>` + (none ? '' : `<div class="pc-pg">${pcOther(null) + pcBtns()}</div>`);
  return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L) + pcYears(L) + (none ? '' : pcOther(L) + pcBtns())}</div>`;
}
''' + A[j:]

# the old cards are gone (nothing else draws them): the ledger card, the flowchart card, "Classes you've taken"
i = A.index('function ledgerCard(L, P) {'); j = A.index('/* Everything still needed, as the Planner listed it before 2026-10-06', i)
A = A[:i] + A[j:]
i = A.index('function gridCard(L) {'); j = A.index('/* ---- sheets ---- */', i)
A = A[:i] + A[j:]
A = rep(A, ".tc-key{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 8px;font-size:11.5px;font-weight:800;color:var(--muted);margin:2px 0 8px}\n.tc-key > span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}\n.tc-key .tc-dot{width:18px;height:18px;font-size:10.5px}\n.tc-key .tc-dot.need{box-shadow:inset 0 0 0 2px var(--line)}\n", "", 'key css')
for dead in ('ledgerCard(', 'gridCard(', 'historyCard('):
    if dead in A: sys.exit('past-classes-simple: ' + dead + ' is still called somewhere')

A = rep(A, "SHEETS.geArea = ({ area }) => {", r'''/* ---- Past classes (2026-10-10, Tate's option A, simple) ------------------------------------------------
   The flowchart and the classes you've taken in one place: a spot shows the class that filled it (and its
   professor); the record's classes with no spot are "Other classes". Only what's needed is on screen. */
const pcK = c => (window.TCPL && TCPL.canon(c)) || canonCode(c) || c;
const PC_TO = { Winter: 0, Spring: 1, Summer: 2, Fall: 3 };
const pcHist = () => (TC.myHistory || []).slice().sort((a, b) => (+b.year || 0) - (+a.year || 0) || (PC_TO[b.term] || 0) - (PC_TO[a.term] || 0));
const pcKey = h => [pcK(h.code), h.term || '', h.year || ''].join('|');
const pcRow = key => (TC.myHistory || []).find(h => pcKey(h) === key);
/* transfer and exam credit carry the abroad mark in the professor column (the DPR import) — no professor to add */
const pcXfer = h => !!h && !!window.TCPL && h.professor === TCPL.abroadMark;
const pcChev = (r = 0) => `<svg class="pc-chev" viewBox="0 0 8 14" aria-hidden="true"${r ? ` style="transform:rotate(${r}deg)"` : ''}><path d="M1 1l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const pcX = () => `<button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button>`;
/* Which row of your record sits in which spot: a done spot takes the oldest unplaced row of its class, so a
   repeated or retaken class shows each attempt once (its own term and professor) and the attempts with no spot
   are "Other classes". */
let PC_PLACE = { slot: new Map(), rest: [] };
function pcPlace(L) {
  const pool = {};
  pcHist().slice().reverse().forEach(h => { const k = pcK(h.code); (pool[k] = pool[k] || []).push(h); });
  const slot = new Map();
  if (L) L.grid.forEach(t => t.slots.forEach(s => { const c = s.state === 'done' && (s.fill || s.by); const q = c && pool[pcK(c)]; if (q && q.length) slot.set(s.id, q.shift()); }));
  const left = new Set(Object.values(pool).flat());
  return (PC_PLACE = { slot, rest: pcHist().filter(h => left.has(h)) });
}
/* the professor line under a class on your record: who taught it, or "+ Professor"; taking now: your section's */
function pcLine(code, state, h) {
  if (state === 'taking') { const s = nowSecs('me').find(x => pcK(x.code) === code && x.prof && PROFS[x.prof]); return s ? `<span class="pc-pf">${esc(PROFS[s.prof].name)}</span>` : ''; }
  /* a class you didn't have to take (AP/IB, transfer, advisor): its reason, the desktop's words */
  if (!h) { const w = Object.keys(TC.waived || {}).find(c => pcK(c) === code); return w ? `<span class="pc-pf">${esc(TCPL.waiveLabel(TC.waived[w]))}</span>` : ''; }
  if (pcXfer(h)) return '';
  return h.professor ? `<span class="pc-pf">${esc(h.professor)}</span>` : `<button class="pc-add" data-a="pcProf" data-x="${esc(pcKey(h))}" aria-label="Add the professor for ${esc(code)}${h.term ? ', ' + esc(h.term + ' ' + h.year) : ''}">+ Professor</button>`;
}
function pcSummary(L) {
  const pct = L.N ? Math.round(100 * L.F / L.N) : 0, X = auditLines(TC.audit, L);
  const conc = TCPL.concInfo(L.major);
  const pick = L.concUnchosen && conc.list.length ? `<div class="pc-conc"><div class="b" style="font-size:14.5px;margin-bottom:8px">Pick your concentration</div><div style="display:flex;flex-wrap:wrap;gap:8px">${conc.list.map(c => `<button class="chip" style="background:var(--bg)" data-a="pickConc" data-x="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div></div>` : '';
  return `<div class="card pc-sum"><div class="pc-num"><b>${L.F} of ${L.N}</b><span>filled</span></div><div class="pc-bar" role="img" aria-label="${L.F} of ${L.N} filled"><i style="width:${pct}%"></i></div>${X ? `<button class="pc-link" data-a="pcReport"><span>Degree Progress Report</span><em>${X.open.length} left</em>${pcChev()}</button>` : ''}${pick}</div>`;
}
function pcSlot(s) {
  const c0 = CELL[s.state] || CELL.need, cls = s.fill || s.by || '';
  /* the can't-check mark reads at 4.5:1 here (CELL's muted2 doesn't on the page) */
  const c = s.state === 'cant' ? [c0[0], 'var(--ink4)', c0[2], c0[3]] : c0;
  const code = cls || (s.code && !s.choice ? ((s.codes && s.codes[0]) || s.code) : '');
  const name = cls ? (courseName(cls) || (s.title && !codeLike(s.title) ? s.title : '')) : s.choice ? s.title : code ? (courseName(code) || (codeLike(s.title) ? '' : s.title)) : String(s.title || '').replace(/\s*·\s*/g, ' ');
  const quick = s.state === 'done' && s.by && (TC.myHistory || []).some(h => TCPL.canon(h.code) === s.by && !h.term && !h.year);
  const tickable = (s.state === 'need' && (s.code || s.choice)) || quick;
  /* no class to log (a GE area, an elective) or one we can't check: the circle checks the row off (flowchart-mark-done, 2026-10-09) */
  const markable = !tickable && !s.choice && (s.mine || s.state === 'cant' || (s.state === 'need' && !s.code));
  const dot = markable
    ? `<button class="pc-dot tc-tick tc-mark ${s.state}" style="color:${c[1]};background:${c[2]}" data-a="plMark" data-x="${esc(s.id)}" aria-pressed="${!!s.mine}" aria-label="Mark ${esc(code || name || s.title)} done" ${(UI.busyMarks || {})[s.id] ? 'disabled' : ''}>${c[0]}</button>`
    : tickable
    ? `<button class="pc-dot tc-tick ${s.state}" style="color:${c[1]};background:${c[2]}" data-a="plTick" data-x="${esc(s.id)}" aria-label="${quick ? 'Undo: ' + esc(s.by) + ' taken' : 'I took ' + esc(s.choice ? s.title : code)}" ${UI.busy.tick === s.id ? 'disabled' : ''}>${c[0]}</button>`
    : `<span class="pc-dot ${s.state}" style="color:${c[1]};background:${c[2]}" role="img" aria-label="${c[3]}">${c[0]}</span>`;
  const row = s.state === 'done' ? PC_PLACE.slot.get(s.id) : null;
  const act = (s.state === 'done' || s.state === 'taking') && cls ? (row ? `data-a="pcOpen" data-x="${esc(pcKey(row))}"` : COURSES[pcK(cls)] ? `data-a="openClass" data-x="${esc(pcK(cls))}"` : '')
    : s.state === 'need' && s.choice ? `data-a="plTick" data-x="${esc(s.id)}"`
    : s.state === 'need' && code ? (COURSES[code] ? `data-a="openClass" data-x="${esc(code)}"` : `data-a="plLogSlot" data-x="${esc(code)}"`)
    : s.state === 'need' && s.type === 'ge' ? `data-a="plGe" data-x="${esc(s.area || '')}"` : '';
  const main = `${code ? `<span class="pc-cc">${esc(code)}</span>` : ''}<span class="pc-nm">${esc(name || '')}</span>${s.state === 'cant' ? '<span class="pc-sr">, we can’t check this from your record</span>' : ''}`;
  const line = s.mine ? '<span class="pc-pf tc-mine">Marked done by you</span>' : (s.state === 'done' || s.state === 'taking') && cls ? pcLine(pcK(cls), s.state, row) : '';
  const pick = s.choice && s.state === 'need' && UI.plPick === s.id
    ? `<div class="tc-pick"><div class="muted b" style="font-size:12.5px;width:100%">Which one did you take?</div>${s.choice.map(o => `<button class="tc-pickb" data-a="plTickCode" data-x="${esc(o)}" data-y="${esc(s.id)}"><span class="tc-ccode">${esc(o)}</span>${esc(courseName(o))}</button>`).join('')}</div>` : '';
  return `<div class="pc-row ${s.state}">${dot}<div class="pc-tx">${act ? `<button class="pc-main" ${act}>${main}</button>` : `<div class="pc-main">${main}</div>`}${line}</div></div>${pick}`;
}
function pcYears(L) {
  UI.plYears = UI.plYears || {};
  const years = [];
  L.grid.forEach(t => { let y = years.find(x => x.year === t.year); if (!y) years.push(y = { year: t.year, terms: [] }); y.terms.push(t); });
  const firstOpen = (years.find(y => y.terms.some(t => t.slots.some(s => s.state === 'need' || s.state === 'taking'))) || {}).year;
  return years.map(y => {
    const slots = y.terms.flatMap(t => t.slots), done = slots.filter(s => s.state === 'done').length, judged = slots.filter(s => s.state !== 'cant').length;
    const open = UI.plYears[y.year] !== undefined ? UI.plYears[y.year] : y.year === firstOpen;
    const head = `<button class="pc-year" data-a="plYear" data-x="${y.year}" aria-expanded="${open}" aria-label="Year ${y.year}, ${done} of ${judged} filled"><span>Year ${y.year}</span><em>${done} of ${judged}</em>${pcChev(open ? 90 : 0)}</button>`;
    return open ? `<div class="pc-open">${head}${y.terms.map(t => `<div class="pc-term"><div class="pc-termh">${esc(String(t.term || '').toUpperCase())}</div>${t.slots.map(pcSlot).join('')}</div>`).join('')}</div>` : head;
  }).join('');
}
/* the classes on your record that fill no spot on the flowchart (L null: no flowchart — every class) */
function pcOther(L) {
  const used = new Set();
  if (L) L.grid.forEach(t => t.slots.forEach(s => { if ((s.state === 'done' || s.state === 'taking') && (s.fill || s.by)) used.add(pcK(s.fill || s.by)); }));
  const rows = PC_PLACE.rest.concat(Object.keys(TC.waived || {}).filter(c => !used.has(pcK(c)) && !(TC.myHistory || []).some(h => pcK(h.code) === pcK(c))).map(c => ({ code: c, waived: true })));
  if (!rows.length) return '';
  const show = UI.pcAll ? rows : rows.slice(0, 4);
  const row = h => { const code = pcK(h.code), nm = courseName(code), main = `<span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(nm)}</span>`;
    return `<div class="pc-orow"><div class="pc-tx">${h.waived ? `<div class="pc-main">${main}</div>` : `<button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}">${main}</button>`}${pcLine(code, 'done', h.waived ? null : h)}</div></div>`; };
  return `<div class="card pc-oth"><div class="pc-hd"><span>${L ? 'Other classes' : 'Classes you’ve taken'}</span><em>${rows.length}</em></div>${show.map(row).join('')}${rows.length > show.length ? `<button class="pc-more" data-a="pcAll">See all ${rows.length}</button>` : ''}</div>`;
}
/* back to the sheet the picker (or the term) was opened from — the who list at the row you were on */
function pcBack(sh) {
  UI.sheet = sh.ret || null;
  if (UI.sheet && UI.sheet.type === 'pcWho' && UI.sheet.scroll) { const y = UI.sheet.scroll; setTimeout(() => { const f = document.querySelector('#sheet .fullpg'); if (f) f.scrollTop = y; }, 0); }
}
const pcBtns = () => `<div class="pc-btns"><button class="pc-btn" data-a="sheet" data-x="logClass">+ Log a class</button><label class="pc-btn">Upload report<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label></div>`;
/* Tap a class on your record */
SHEETS.pcClass = sh => {
  const h = pcRow(sh.key);
  if (!h) return `<div class="row sb"><h3>That class isn’t on your record anymore</h3>${pcX()}</div>`;
  const code = pcK(h.code), nm = courseName(code), xfer = pcXfer(h), pk = !xfer && profKeyOf(h.professor), term = [h.term, h.year].filter(Boolean).join(' ');
  return `<div class="pc-shtop"><div class="pc-shtx"><span class="pc-cc">${esc(code)}</span>${nm ? `<span class="pc-sht">${esc(nm)}</span>` : ''}</div>${pcX()}</div>
 <div class="pc-list">${xfer ? '' : `<button class="pc-it" data-a="pcProf" data-x="${esc(sh.key)}"><span>Professor</span><b class="${h.professor ? '' : 'pc-addt'}">${esc(h.professor || 'Add')}</b>${pcChev()}</button>`}<button class="pc-it" data-a="pcTerm" data-x="${esc(sh.key)}"><span>Term</span><b class="${term ? '' : 'pc-addt'}">${esc(term || 'Add')}</b>${pcChev()}</button></div>
 ${pk && PROFS[pk] ? `<button class="btn" style="width:100%;margin-top:16px" data-a="rateProf" data-x="${esc(pk)}" data-y="${esc(code)}">Rate ${esc(PROFS[pk].name)}</button>` : ''}
 <button class="pc-danger" data-a="pcAskRemove" data-x="${esc(sh.key)}">Remove from my record</button>`;
};
SHEETS.pcTerm = sh => {
  const h = pcRow(sh.key); if (!h) return `<div class="row sb"><h3>That class isn’t on your record anymore</h3>${pcX()}</div>`;
  const y = new Date().getFullYear(), t0 = h.term || '', y0 = +h.year || 0, from = Math.min(y0 || y, y - 10);
  return `<div class="row sb"><h3>When did you take ${esc(pcK(h.code))}?</h3>${pcX()}</div>
 <div class="row" style="gap:10px;margin-top:10px"><label class="grow tc-form">Term<select id="pc-term">${t0 ? '' : '<option value="" selected disabled>Choose</option>'}${['Fall', 'Winter', 'Spring', 'Summer'].map(t => `<option ${t === t0 ? 'selected' : ''}>${t}</option>`).join('')}</select></label>
 <label class="grow tc-form">Year<select id="pc-year">${y0 ? '' : '<option value="" selected disabled>Choose</option>'}${Array.from({ length: y + 2 - from }, (_, i) => y + 1 - i).map(v => `<option ${v === y0 ? 'selected' : ''}>${v}</option>`).join('')}</select></label></div>
 ${sh.err ? `<div class="tc-err">${esc(sh.err)}</div>` : ''}
 <button class="btn" style="width:100%;margin-top:14px" data-a="pcTermSave" ${UI.busy.pct ? 'disabled' : ''}>${UI.busy.pct ? 'Saving…' : 'Save'}</button>`;
};
/* Who taught it? — only real names: who teaches it now (Cal Poly's class search), who PolyRatings lists it for,
   or a professor the student searches for. Nothing is filled in until they pick. */
const pcName = p => ((p.firstName || '') + ' ' + (p.lastName || '')).trim();
const pcPR = p => +p.numEvals > 0 && isFinite(+p.overallRating) ? Math.round(+p.overallRating / 4 * 5 * 100) / 100 : null;
function pcCands(code) {
  UI.pcCache = UI.pcCache || {};
  const ck = code + '|' + (PR_LIST ? PR_LIST.length : 0) + '|' + Object.keys(PROFS).length;
  if (UI.pcCache[ck]) return UI.pcCache[ck];
  const out = new Map(), add = (name, r, n, now) => { const k = profKeyOf(name); if (!k || out.has(k)) return; out.set(k, { name, r, n, now }); };
  courseProfs(code).forEach(pk => { const p = PROFS[pk]; if (p && p.name && pk) add(p.name, ratingOf(pk), p.count || 0, true); });
  (PR_LIST || []).forEach(p => { if (!p || !Array.isArray(p.courses) || !p.courses.some(c => pcK(String(c || '').toUpperCase()) === code)) return; add(pcName(p), pcPR(p), +p.numEvals || 0, false); });
  return (UI.pcCache[ck] = [...out.values()].sort((a, b) => (b.now - a.now) || (b.n - a.n) || a.name.localeCompare(b.name)).slice(0, 8));
}
function pcSearch(q) {
  const s = q.trim().toLowerCase(); if (s.length < 2) return [];
  const out = new Map(), add = (name, r, n) => { const k = profKeyOf(name); if (!k || out.has(k) || !name.toLowerCase().includes(s)) return; out.set(k, { name, r, n }); };
  Object.keys(PROFS).forEach(pk => { const p = PROFS[pk]; if (p && p.name) add(p.name, ratingOf(pk), p.count || 0); });
  (PR_LIST || []).forEach(p => { if (p) add(pcName(p), pcPR(p), +p.numEvals || 0); });
  return [...out.values()].sort((a, b) => (b.n - a.n) || a.name.localeCompare(b.name)).slice(0, 8);
}
function pcPList(sh) {
  const h = pcRow(sh.key); if (!h) return '';
  const q = String(sh.q || '').trim(), list = q.length >= 2 ? pcSearch(q) : pcCands(pcK(h.code));
  const opt = o => { const t = profTone(o.r), on = !!sh.pick && profKeyOf(sh.pick) === profKeyOf(o.name), rt = rateTone(o.r);
    return `<button class="pc-opt${on ? ' on' : ''}" data-a="pcPick" data-x="${esc(o.name)}" aria-pressed="${on}"><span class="pc-av" style="background:${t.bg};color:${t.ink}" aria-hidden="true">${esc(initialsOf(o.name))}</span><span class="pc-on">${esc(o.name)}</span>${rt ? `<span class="rchip" style="background:${rt.bg};color:${rt.ink}">${starI(12, rt.star)} ${o.r.toFixed(1)}</span>` : ''}</button>`; };
  const typed = q.length >= 3 && !list.some(o => o.name.toLowerCase() === q.toLowerCase())
    ? `<button class="pc-opt${sh.pick === q ? ' on' : ''}" data-a="pcPick" data-x="${esc(q)}" aria-pressed="${sh.pick === q}"><span class="pc-on">Use “${esc(q)}”</span></button>` : '';
  const empty = !list.length && !typed ? `<div class="muted b pc-none">${q.length >= 2 ? 'No professor matches that.' : 'Search for your professor.'}</div>` : '';
  return list.map(opt).join('') + typed + empty + (!q && TC.err.poly ? '<div class="muted b pc-none">PolyRatings didn’t load, so only professors teaching it now are listed.</div>' : '');
}
SHEETS.pcProf = sh => {
  const h = pcRow(sh.key); if (!h) return `<div class="row sb"><h3>That class isn’t on your record anymore</h3>${pcX()}</div>`;
  const code = pcK(h.code), nm = courseName(code);
  return `<div class="pc-shtop"><span class="pc-sht">Who taught it?</span><button class="xbtn" data-a="pcProfNone" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <div class="pc-cls"><span class="pc-cc">${esc(code)}</span><span>${esc(nm)}</span></div>
 <label class="pc-search">${ic('search', 16, 2.4)}<input id="pc-q" data-in="pcq" type="search" value="${esc(sh.q || '')}" placeholder="Search professors" aria-label="Search professors" autocomplete="off" data-1p-ignore data-lpignore="true" data-form-type="other" autocapitalize="words" autocorrect="off" spellcheck="false" enterkeyhint="search" maxlength="60"></label>
 <div id="pc-plist" class="pc-plist">${pcPList(sh)}</div>
 ${sh.err ? `<div class="tc-err">${esc(sh.err)}</div>` : ''}
 <button class="btn" style="width:100%;margin-top:14px" data-a="pcProfSave" ${!sh.pick || UI.busy.pcp ? 'disabled' : ''}>${UI.busy.pcp ? 'Saving…' : 'Save'}</button>
 <button class="pc-plain" data-a="pcProfNone">I don’t remember</button>`;
};
/* Right after a report is saved: the three latest terms' classes with no professor yet */
function pcWhoKeys() {
  const rows = pcHist().filter(h => !pcXfer(h) && h.term && h.year);
  const terms = [...new Set(rows.map(h => h.term + ' ' + h.year))].slice(0, 3);
  const pick = rows.filter(h => terms.includes(h.term + ' ' + h.year));
  return pick.some(h => !h.professor) ? pick.map(pcKey) : [];
}
SHEETS.pcWho = sh => {
  const groups = [];
  (sh.keys || []).forEach(k => { const h = pcRow(k); if (!h) return; const t = h.term + ' ' + h.year; let g = groups.find(x => x.t === t); if (!g) groups.push(g = { t, rows: [] }); g.rows.push(h); });
  return `<div class="pc-whop"><div class="pc-shtop"><span class="pc-sht" style="font-size:26px">Who taught these?</span><button class="xbtn" data-a="pcWhoDone" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 ${groups.map(g => `<div class="pc-term"><div class="pc-termh">${esc(g.t.toUpperCase())}</div>${g.rows.map(h => { const code = pcK(h.code); return `<button class="pc-wrow" data-a="pcProf" data-x="${esc(pcKey(h))}"><span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(courseName(code))}</span>${h.professor ? `<span class="pc-who">${esc(h.professor)}</span>` : '<span class="pc-addt">+ Add</span>'}</button>`; }).join('')}</div>`).join('')}
 <button class="btn" style="width:100%;margin-top:6px" data-a="pcWhoDone">Done</button></div>`;
};
SHEETS.pcWho.full = true; SHEETS.pcWho.label = 'Who taught these?';
SHEETS.geArea = ({ area }) => {''', 'geArea')

A = rep(A, "  dprCheck: () => { UI.sheet = { type: 'dprCheck', seg: 'open' }; render(true); },\n", r'''  dprCheck: () => { UI.sheet = { type: 'dprCheck', seg: 'open' }; render(true); },
  /* Past classes (2026-10-10) */
  pcReport: () => { S.schedTab = 'planner'; save(); render(); },
  pcAll: () => { UI.pcAll = true; render(true); },
  /* Remove from the class's sheet: that attempt only (a retaken class keeps its other term) */
  pcAskRemove: key => { const h = pcRow(key); if (!h) return; const when = [h.term, h.year].filter(Boolean).join(' ');
    UI.sheet = { type: 'confirm', title: 'Remove ' + pcK(h.code) + (when ? ', ' + when : '') + '?', body: 'It comes off your past classes and stops counting toward your requirements.', yes: 'Remove', act: 'pcRemove', x: key }; render(true); },
  pcRemove: async key => { const h = pcRow(key); UI.sheet = null; if (!h) return render(true); const e = await TC.removeHistory(h.code, h); toast(e || 'Removed ' + pcK(h.code)); render(true); },
  pcOpen: key => { if (!pcRow(key)) return; UI.sheet = { type: 'pcClass', key }; render(true); },
  pcTerm: key => { if (!pcRow(key)) return; UI.sheet = { type: 'pcTerm', key, err: '', ret: UI.sheet && UI.sheet.type === 'pcClass' ? UI.sheet : null }; render(true); },
  pcTermSave: async () => {
    const sh = UI.sheet, h = sh && pcRow(sh.key); if (!h || UI.busy.pct) return;
    const term = (document.getElementById('pc-term') || {}).value, year = parseInt((document.getElementById('pc-year') || {}).value, 10);
    if (!term || !year) { sh.err = 'Choose the term and the year.'; return render(true); }
    UI.busy.pct = 1; render(true);
    try {
      const e = await TC.updateHistory(h, { term, year });
      if (e) { sh.err = e; return; }
      if (UI.sheet === sh) UI.sheet = { type: 'pcClass', key: [pcK(h.code), term, year].join('|') }; toast('Saved');
    } finally { UI.busy.pct = 0; render(true); }
  },
  pcProf: key => {
    const h = pcRow(key); if (!h || pcXfer(h)) return;
    const back = UI.sheet && (UI.sheet.type === 'pcClass' || UI.sheet.type === 'pcWho') ? UI.sheet : null;
    if (back && back.type === 'pcWho') { const f = document.querySelector('#sheet .fullpg'); back.scroll = f ? f.scrollTop : 0; }
    UI.sheet = { type: 'pcProf', key, q: '', pick: h.professor || null, err: '', ret: back }; render(true);
  },
  pcPick: name => { const sh = UI.sheet; if (!sh || sh.type !== 'pcProf') return; sh.pick = String(name || '').trim().slice(0, 60) || null; sh.err = ''; render(true); },
  pcProfSave: async () => {
    const sh = UI.sheet, h = sh && sh.type === 'pcProf' && pcRow(sh.key); if (!h || !sh.pick || UI.busy.pcp) return;
    UI.busy.pcp = 1; render(true);
    try {
      const e = await TC.updateHistory(h, { professor: sh.pick });
      if (e) { sh.err = e; return; }
      toast('Saved ' + sh.pick); if (UI.sheet === sh) pcBack(sh);
    } finally { UI.busy.pcp = 0; render(true); }
  },
  pcProfNone: () => { const sh = UI.sheet; if (sh && sh.type === 'pcProf') pcBack(sh); else UI.sheet = null; render(true); },
  /* the who list closes onto the Planner; from onboarding, the notification ask it held back comes now */
  pcWhoDone: () => { const sh = UI.sheet, onb = !!(sh && sh.type === 'pcWho' && sh.onb); UI.sheet = null; render(true); if (onb) setTimeout(() => TC.pushAsk('onboarding'), 600); },
''', 'actions')

# after a report is saved: who taught these? (then the Planner, as before)
A = rep(A, "      UI.sheet = null; UI.pl = null; UI.plRefresh = true;\n      S.tab = 'schedule'; S.schedTab = 'planner'; save();",
        "      UI.pl = null; UI.plRefresh = true;\n      const who = pcWhoKeys(); UI.sheet = who.length ? { type: 'pcWho', keys: who } : null;\n      S.tab = 'schedule'; S.schedTab = 'planner'; save();", 'dprSave end')

A = rep(A, "  closeSheet: () => { if (UI.sheet && UI.sheet.type === 'plPrefs' && !TC.prefs) return;", "  closeSheet: () => { if (UI.sheet && UI.sheet.type === 'plPrefs' && !TC.prefs) return;\n    if (UI.sheet && (UI.sheet.type === 'pcProf' || UI.sheet.type === 'pcTerm') && UI.sheet.ret) { pcBack(UI.sheet); render(true); return; }", 'closeSheet ret')

# onboarding's last step ends on a saved report — "Who taught these?" open over the Planner counts as saved
A = rep(A, "  if (wasOnb && !UI.sheet && !(UI.dpr && UI.dpr.saveErr)) {", "  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho') && !(UI.dpr && UI.dpr.saveErr)) {", 'onb dprSave')
A = rep(A, "S.tab = 'schedule'; S.schedTab = 'planner'; save(); render(); setTimeout(() => TC.pushAsk('onboarding'), 600); }", "S.tab = 'schedule'; S.schedTab = 'planner'; save(); render(); if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet.onb = true; else setTimeout(() => TC.pushAsk('onboarding'), 600); }", 'onb ask')

# the picker's search repaints only its list, so the keyboard stays up
A = rep(A, "document.addEventListener('input', ev => {\n  const t = ev.target;\n  if (t.dataset.in === 'ep' && UI.ep) {",
        "document.addEventListener('input', ev => {\n  const t = ev.target;\n  if (t.dataset.in === 'pcq' && UI.sheet && UI.sheet.type === 'pcProf') { UI.sheet.q = t.value; const el = document.getElementById('pc-plist'); if (el) el.innerHTML = pcPList(UI.sheet); return; }\n  if (t.dataset.in === 'ep' && UI.ep) {", 'input pcq')

# one attempt of a class comes off the record (the sheet's Remove); without a row, every attempt, as before
A = rep(A, "TC.removeHistory = async function (code) {\n  const r = await TC.client().from('class_history').delete().eq('user_id', TC.user.id).eq('code', code);\n",
        "TC.removeHistory = async function (code, h) {\n  let q = TC.client().from('class_history').delete().eq('user_id', TC.user.id).eq('code', code);\n"
        "  if (h) { q = h.term == null ? q.is('term', null) : q.eq('term', h.term); q = h.year == null ? q.is('year', null) : q.eq('year', h.year); }\n"
        "  const r = await q;\n", 'removeHistory row')

# saving a professor or term on a class already on the record (the table's own policy allows UPDATE)
A = rep(A, "/* The desktop's dbFriendlyErr, in short: our own sentences through, raw database text never. */",
        r'''TC.updateHistory = async function (h, patch) {
  let q = TC.client().from('class_history').update(patch).eq('user_id', TC.user.id).eq('code', h.code);
  q = h.term == null ? q.is('term', null) : q.eq('term', h.term);
  q = h.year == null ? q.is('year', null) : q.eq('year', h.year);
  const r = await q.select('code');
  if (r.error) return dbSay(r.error, 'Couldn’t save that.');
  if (!Array.isArray(r.data) || !r.data.length) { await TC.reloadHistory(); return 'Couldn’t save that — try again.'; }
  await TC.reloadHistory(); loadRateList(); return null;
};
/* The desktop's dbFriendlyErr, in short: our own sentences through, raw database text never. */''', 'updateHistory')

A = rep(A, ".tc-term .tc-pick{background:var(--card);border-radius:14px;margin-top:4px;padding:10px}",
        ".tc-term .tc-pick{background:var(--card);border-radius:14px;margin-top:4px;padding:10px}\n" + r'''/* Past classes (2026-10-10); 12px from the screen edge like Home (the 08:30 page width) */
.pc-pg{padding:0 12px}
.pc-sum{margin-top:14px;padding:16px}
.pc-num{display:flex;align-items:baseline;gap:8px}
.pc-num b{font-size:34px;font-weight:1000;line-height:1}
.pc-num span{font-size:15px;font-weight:800;color:var(--muted)}
.pc-bar{height:8px;border-radius:4px;background:var(--track,var(--fill2));overflow:hidden;margin-top:12px}
.pc-bar i{display:block;height:100%;background:var(--teal-t,var(--teal));border-radius:4px}
.pc-link{display:flex;align-items:center;gap:8px;width:100%;border-top:1px solid var(--line);padding:14px 0 0;margin-top:14px;text-align:left;font-weight:800;font-size:15px;min-height:44px}
.pc-link span{flex:1}
.pc-link em{font-style:normal;color:var(--muted)}
.pc-chev{flex:none;width:8px;height:14px;color:var(--blue-ink)}
.pc-conc{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.pc-conc .chip{max-width:100%;height:auto;min-height:36px;padding:7px 14px;white-space:normal;text-align:left}
.pc-year{display:flex;align-items:center;gap:10px;width:100%;margin-top:10px;background:var(--tint1);border-radius:18px;padding:0 16px;min-height:54px;text-align:left;font-weight:900;font-size:16px}
.pc-year span{flex:1}
.pc-year em{font-style:normal;font-size:14px;font-weight:800;color:var(--ink4)}
.pc-open .pc-year{margin-bottom:8px}
.pc-term{background:var(--tint2);box-shadow:inset 0 0 0 1px var(--tint-line);border-radius:20px;padding:8px;margin-top:8px;display:flex;flex-direction:column;gap:6px}
.pc-termh{font-size:12.5px;font-weight:900;letter-spacing:.08em;color:var(--blue-ink);padding:4px 8px 2px}
.pc-row{display:flex;align-items:center;gap:10px;background:var(--card);border-radius:14px;padding:6px 12px;min-height:52px}
.pc-dot{flex:none;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-weight:900;font-size:13px}
.pc-dot.need{box-shadow:inset 0 0 0 2px var(--line2)}
.pc-dot.tc-tick.need{box-shadow:inset 0 0 0 2px var(--muted)}
.pc-dot.tc-mark.cant{box-shadow:inset 0 0 0 2px var(--muted)}
.pc-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.pc-pf.tc-mine{color:var(--teal-t,var(--teal))}
.pc-tx{flex:1;min-width:0;display:flex;flex-direction:column;align-items:flex-start}
.pc-main{display:flex;align-items:center;gap:8px;width:100%;min-height:40px;text-align:left;min-width:0}
.pc-cc{flex:none;font-size:12.5px;font-weight:900;color:var(--blue-ink);background:var(--blue-soft2);border-radius:8px;padding:3px 7px}
.pc-nm{font-size:14.5px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.pc-row.done .pc-nm{color:var(--ink)}
.pc-pf{font-size:13px;font-weight:800;color:var(--muted);margin:-4px 0 6px}
.pc-add{font-size:13px;font-weight:900;color:var(--blue-t,var(--blue));min-height:44px;margin:-12px 0 -6px;padding:0 12px 0 0}
.pc-oth{margin-top:14px;padding:12px 16px}
.pc-hd{display:flex;justify-content:space-between;align-items:baseline;font-size:17px;font-weight:900;padding:4px 0}
.pc-hd em{font-style:normal;font-size:14px;font-weight:800;color:var(--muted)}
.pc-orow{border-top:1px solid var(--line);padding:4px 0}
.pc-more{color:var(--blue-t,var(--blue));font-weight:900;font-size:14px;min-height:44px;text-align:left}
.pc-btns{display:flex;gap:8px;margin-top:14px}
.pc-btn{flex:1;display:flex;align-items:center;justify-content:center;min-height:48px;border-radius:16px;background:var(--card);color:var(--ink);font-weight:900;font-size:14px;cursor:pointer;margin:0}
.pc-shtop{display:flex;align-items:flex-start;gap:12px;margin-bottom:14px}
.pc-shtx{flex:1;min-width:0;display:flex;flex-direction:column;align-items:flex-start;gap:6px}
.pc-sht{flex:1;font-size:21px;font-weight:900;line-height:1.2}
.pc-list{background:var(--fill);border-radius:18px;padding:0 14px}
.pc-it{display:flex;align-items:center;gap:10px;width:100%;min-height:54px;text-align:left;font-weight:800;font-size:15px}
.pc-it + .pc-it{border-top:1px solid var(--line2)}
.pc-it span{flex:1;color:var(--ink4)}
.pc-it b{font-weight:900;max-width:60%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-addt{color:var(--blue-t,var(--blue));font-weight:900}
.pc-danger{display:block;margin:10px auto 0;color:var(--red-ink);font-weight:900;font-size:14px;min-height:44px}
.pc-cls{display:flex;align-items:center;gap:8px;margin:-6px 0 12px;min-width:0}
.pc-cls span:last-child{font-size:14px;font-weight:800;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-search{display:flex;align-items:center;gap:8px;background:var(--fill);border-radius:14px;padding:0 14px;min-height:48px;color:var(--muted)}
.pc-search input{flex:1;border:0;background:transparent;color:var(--ink);font:800 16px Nunito,system-ui,sans-serif;outline:none;min-width:0}
.pc-search input::placeholder{color:var(--muted)}
.pc-plist{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.pc-opt{display:flex;align-items:center;gap:12px;width:100%;background:var(--fill);border-radius:16px;padding:0 14px;min-height:58px;text-align:left;font-weight:900;font-size:15px}
.pc-opt.on{background:var(--blue-soft);box-shadow:inset 0 0 0 2px var(--blue-t,var(--blue))}
.pc-av{flex:none;width:36px;height:36px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:900}
.pc-on{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-none{font-size:13.5px;padding:8px 2px}
.pc-plain{display:block;margin:8px auto 0;color:var(--blue-t,var(--blue));font-weight:900;font-size:14px;min-height:44px}
.pc-whop{padding:calc(var(--sb,0px) + 14px) 12px calc(env(safe-area-inset-bottom,0px) + 28px);display:flex;flex-direction:column;gap:12px}
.pc-whop .pc-shtop{padding:0 4px;margin:0}
.pc-wrow{display:flex;align-items:center;gap:10px;width:100%;background:var(--card);border-radius:14px;padding:0 12px;min-height:56px;text-align:left}
.pc-wrow .pc-nm{flex:1}
.pc-who{flex:none;max-width:120px;font-size:13.5px;font-weight:800;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}''', 'css')

open(PI, 'w', encoding='utf-8').write(A); open(PP, 'w', encoding='utf-8').write(P); open(PD, 'w', encoding='utf-8').write(DK)
print('past-classes-simple-2026-10-10: applied')
