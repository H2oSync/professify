#!/usr/bin/env python3
r"""A class you're taking this term is in progress, never done — wherever it sits (Tate, 2026-10-11: "for a class im
currenty enrolled in it shouldnt say complete but it should have the in progress thing like intro to futures and
options has. look at the current classes im in and make sure to do this, no matter where the class is in the
flowchart"). Run AFTER quarter-ge-guidelines-2026-10-11.py.

Two ways a class this term showed as done:
  1. A row on your record dated this term (or later). The term isn't over, so it can't be finished — yet the ledger
     counted every record row as done (BUS 3431 "Security Analysis", Fall 2026, showed ✓ + Professor).
     Now such a row is a class you're taking: out of what counts as done (prerequisites too), into what you're taking.
  2. Your report: the registrar prints "Satisfied" on a line whose class is being taken now (BUS 431 (3431), used by
     "2026 Fall BUS 3431"). Now a Satisfied line that the report filled with a class this term is in progress.
And on the lists: a class this term in "Other classes" / "Units only" says "In progress · this term", and a class
in My Classes this term that fills no flowchart spot is listed in "Other classes" as in progress too.

Usage: python3 in-progress-now-2026-10-11.py <repo-dir>      Replayable: every anchor must match the stated count."""
import sys, os
D = sys.argv[1]
PA = os.path.join(D, 'app', 'index.html')
S = open(PA, encoding='utf-8').read()

def rep(a, b, label, n=1):
    global S
    c = S.count(a)
    if c != n: sys.exit(f'app {label}: anchor matched {c}x (want {n})')
    S = S.replace(a, b)

# 1. the record: a row dated this term or later isn't finished
rep("""function plSync() {
  if (!window.TCPL) return;""", """/* (2026-10-11) A row on your record dated this term or later isn't a finished class — the term isn't over. It's a
   class you're taking: never "done", never a prerequisite met, always "in progress" (Tate). Undated rows (AP, an
   old import) stay finished. */
const HT_ORD = { Winter: 1, Spring: 2, Summer: 3, Fall: 4 };
function histNotDone(h) {
  if (!h || !h.term || !h.year) return false;
  if (window.TCPL && h.professor === TCPL.abroadMark) return false;   /* transfer and exam credit: posted, finished */
  const [t, y] = String(nowTerm().label || '').split(' ');
  if (!HT_ORD[t] || !+y) return false;
  const row = (+h.year) * 10 + (HT_ORD[h.term] || 0), now = (+y) * 10 + HT_ORD[t];
  return row > now || (row === now && nowTermOn());
}
/* this term is still on: until its last day (CFG.TERM_ENDS, the registrar's calendar) — after it, grades are in */
function nowTermOn() { return !CFG.TERM_ENDS || sloISO() <= CFG.TERM_ENDS; }
const histDone = () => (TC.myHistory || []).filter(h => !histNotDone(h));
/* what you're taking or registered for, plus your record's rows of this term — what picks, prerequisites and
   "in progress" count as yours (myCodes() stays My Classes only: friends' shared classes, counts) */
function takingCodes() { const s = myCodes(); (TC.myHistory || []).forEach(h => { if (histNotDone(h)) { const c = canonCode(h.code) || h.code; if (c) s.add(c); } }); return s; }
function plSync() {
  if (!window.TCPL) return;""", 'helpers')
rep("""    history: TC.myHistory || [], classes: [...myCodes()], waived: TC.waived || {}, index: idx, names,""",
    """    history: histDone(), classes: [...takingCodes()], waived: TC.waived || {}, index: idx, names,""", 'plSync')
rep("""now = new Set([...myCodes()].map(x => TCPL.canon(x) || x));""", """now = new Set([...takingCodes()].map(x => TCPL.canon(x) || x));""", 'done/now', 2)
rep("""TCPL.prereqStatus(code, TCPL.completed(), [], [...myCodes()])""", """TCPL.prereqStatus(code, TCPL.completed(), [], [...takingCodes()])""", 'prereqs', 3)
rep("""const k = c => (window.TCPL && TCPL.canon(c)) || c, mine = [...myCodes()], mineK = new Set(mine.map(k)), GE = plGeMap();""",
    """const k = c => (window.TCPL && TCPL.canon(c)) || c, mine = [...takingCodes()], mineK = new Set(mine.map(k)), GE = plGeMap();""", 'auditLines mine')
rep("""doneSet = new Set(done.map(c => TCPL.canon(c) || c)), mine = [...myCodes()], mineSet""", """doneSet = new Set(done.map(c => TCPL.canon(c) || c)), mine = [...takingCodes()], mineSet""", 'planRank mine')
rep("""doneSet = new Set(done.map(k)), mine = [...myCodes()], mineSet""", """doneSet = new Set(done.map(k)), mine = [...takingCodes()], mineSet""", 'plan mine')

# 2. the report: a Satisfied line filled by a class this term is in progress
rep("""  const ovs = auditOverrides(), manual = new Set(live.filter(b => (b.status === 'not' || b.status === 'unknown') && ovs.some(o => auditOvMatch(o, b))));""",
    """  /* (2026-10-11) the registrar prints "Satisfied" for a class still being taken (no grade yet): such a line is in
     progress (Tate). A graded class is finished — the report decides. */
  const now = new Set(live.filter(b => b.status === 'satisfied' && (b.used || []).some(e => !e.x && e.p)));
  const ovs = auditOverrides(), manual = new Set(live.filter(b => (b.status === 'not' || b.status === 'unknown') && ovs.some(o => auditOvMatch(o, b))));""", 'now set')
rep("""  return { live, covered, manual, open, unknown:""", """  return { live, covered, manual, now, open, unknown:""", 'now out')
rep("""    inprog: live.filter(b => b.status === 'in_progress' || covered.has(b)), total: live.find(auditIsTotal) || null };""",
    """    inprog: live.filter(b => b.status === 'in_progress' || covered.has(b) || now.has(b)), total: live.find(auditIsTotal) || null };""", 'inprog')
rep("""  const st = X.manual.has(b) ? 'done' : X.covered.has(b) ? 'taking' : b.status === 'satisfied' ? 'done' :""",
    """  const st = X.manual.has(b) ? 'done' : X.covered.has(b) || (X.now && X.now.has(b)) ? 'taking' : b.status === 'satisfied' ? 'done' :""", 'report row')
rep("""  X.live.forEach(b => { const st = b.status === 'satisfied' ? 'done' : b.status === 'in_progress' ? 'taking' : null; if (!st) return;""",
    """  X.live.forEach(b => { const st = b.status === 'satisfied' && !(X.now && X.now.has(b)) ? 'done' : b.status === 'in_progress' || b.status === 'satisfied' ? 'taking' : null; if (!st) return;""", 'overlay')

# 3. Past classes' flowchart: a spot you're taking keeps its row on your record (term, professor), never "Other classes"
rep("""  if (L) L.grid.forEach(t => t.slots.forEach(s => { const c = s.state === 'done' && (s.fill || s.by); const q = c && pool[pcK(c)]; if (q && q.length) slot.set(s.id, q.shift()); }));""",
    """  if (L) L.grid.forEach(t => t.slots.forEach(s => { const c = s.state === 'done' && (s.fill || s.by); const q = c && pool[pcK(c)]; if (q && q.length) slot.set(s.id, q.shift()); }));
  /* a spot you're taking: this term's row of its class (2026-10-11) */
  if (L) L.grid.forEach(t => t.slots.forEach(s => { const c = s.state === 'taking' && (s.fill || s.by); const q = c && pool[pcK(c)]; const i = q ? q.findIndex(histNotDone) : -1; if (i >= 0) slot.set(s.id, q.splice(i, 1)[0]); }));""", 'place taking')
rep("""  if (state === 'taking') { const s = nowSecs('me').find(x => pcK(x.code) === code && x.prof && PROFS[x.prof]); return s ? `<span class="pc-pf">${esc(PROFS[s.prof].name)}</span>` : ''; }""",
    """  if (state === 'taking') { const s = nowSecs('me').find(x => pcK(x.code) === code && x.prof && PROFS[x.prof]); if (s) return `<span class="pc-pf">${esc(PROFS[s.prof].name)}</span>`; if (!h) return ''; }""", 'taking prof')
rep("""  const row = s.state === 'done' ? PC_PLACE.slot.get(s.id) : null;""", """  const row = s.state === 'done' || s.state === 'taking' ? PC_PLACE.slot.get(s.id) || null : null;""", 'slot row')
# the lists: a class this term says so
rep("""/* the classes on your record that fill no spot on the flowchart (L null: no flowchart — every class) */
function pcOther(L) {""", """const pcNowTag = '<span class="pc-pf pc-nowt"><b aria-hidden="true">◐</b> In progress · this term</span>';
/* the classes on your record that fill no spot on the flowchart (L null: no flowchart — every class) */
function pcOther(L) {""", 'now tag')
rep("""  const rows = PC_PLACE.rest.concat(Object.keys(TC.waived || {}).filter(c => !used.has(pcK(c)) && !(TC.myHistory || []).some(h => pcK(h.code) === pcK(c))).map(c => ({ code: c, waived: true })));""",
    """  const rows = PC_PLACE.rest.concat(Object.keys(TC.waived || {}).filter(c => !used.has(pcK(c)) && !(TC.myHistory || []).some(h => pcK(h.code) === pcK(c))).map(c => ({ code: c, waived: true })));
  /* (2026-10-11) a class in My Classes this term that fills no spot and isn't on your record: listed, in progress */
  [...nowCodes()].map(pcK).filter((c, i, a) => a.indexOf(c) === i && !used.has(c) && !(TC.myHistory || []).some(h => pcK(h.code) === c)).forEach(c => rows.unshift({ code: c, now: true }));""", 'other now')
rep("""    return `<div class="pc-orow"><div class="pc-tx">${h.waived ? `<div class="pc-main">${main}</div>` : `<button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}">${main}</button>`}${pcLine(code, 'done', h.waived ? null : h)}</div></div>`; };""",
    """    if (h.now) return `<div class="pc-orow"><div class="pc-tx">${COURSES[code] ? `<button class="pc-main" data-a="openClass" data-x="${esc(code)}">${main}</button>` : `<div class="pc-main">${main}</div>`}${pcLine(code, 'taking', null)}${pcNowTag}</div></div>`;
    const nw = !h.waived && histNotDone(h);
    return `<div class="pc-orow"><div class="pc-tx">${h.waived ? `<div class="pc-main">${main}</div>` : `<button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}">${main}</button>`}${pcLine(code, nw ? 'taking' : 'done', h.waived ? null : h)}${nw ? pcNowTag : ''}</div></div>`; };""", 'other row')
rep("""<span class="pc-nm">${esc(courseName(code))}</span></button>${pcLine(code, 'done', h)}</div></div>`; }).join('')}""",
    """<span class="pc-nm">${esc(courseName(code))}</span></button>${pcLine(code, histNotDone(h) ? 'taking' : 'done', h)}${histNotDone(h) ? pcNowTag : ''}</div></div>`; }).join('')}""", 'units only row')
rep("""    plSync(); TCPL.set({ history: (TC.myHistory || []).concat(add) });""", """    plSync(); TCPL.set({ history: histDone().concat(add) });""", 'dpr counts')
# the re-upload diff: a plan's class is "done now" when the line the OLD REPORT left open is filled on the new one — the
# report's own verdict, not whether a class on your record this term already puts it in progress
rep("""  const doneNow = new Set(); O.open.forEach(b => {""", """  const doneNow = new Set(); O.live.filter(b => b.status === 'not' && !O.manual.has(b)).forEach(b => {""", 'diff old open')
# the reader's "already on your record" sees every row, this term's included (a re-upload never writes a class twice)
rep("""  const r = TCPL.dprParse(text); text = '';""", """  TCPL.set({ history: TC.myHistory || [] });   /* "already on your record": every row, this term's too */
  const r = TCPL.dprParse(text); text = ''; plSync();""", 'reader already')
# style
rep(""".pc-look{""", """.pc-nowt{color:var(--blue-ink)!important;font-weight:700}.pc-nowt b{font-weight:800;margin-right:2px}
.pc-look{""", 'css')

open(PA, 'w', encoding='utf-8').write(S)
print('in-progress-now: done')
