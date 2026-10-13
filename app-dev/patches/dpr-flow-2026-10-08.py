#!/usr/bin/env python3
r"""The report → Planner → Plans flow (Tate, 2026-10-08; design: dpr-planner-plans-design-2026-10-08.md,
canvas "DPR to Plans Flow", 12 screens approved "i like everything except 6").

What this builds, on the phone app (app/index.html + app/planner.js):

  READER v2 (planner.js)  dprAudit() reads the report's OWN verdicts above the Course History table —
    every requirement's Satisfied / Not Satisfied / In Progress, its units and courses counts and the
    classes that clear it — and dprParse() returns it as `audit`. A grade cell is never read; a verdict
    the reader can't place is 'unknown' ("can't check"). Counts use the finest level the report prints
    (lines inside requirements, requirements inside groups).

  TABS  Schedule's tabs are My Classes · Plans · Planner · Past classes (Past classes last — Tate).

  ONBOARDING  The report is the LAST step (all five pills lit): hero, the three portal steps in the
    portal's own words, the lock chip, Upload DPR / Send the link to my laptop / Skip for now. A
    first-year before the term ends (CFG.TERM_ENDS, the academic calendar's "End of term") gets
    "Nothing on your report yet" with the flowchart's Spring Year 1 list and one Continue — no button
    to decide about. The laptop link is an email to the student's own address (request_planner_link).

  REPORT READ (screen 2)  After the read: "Report read", major · year, the page illustration whose
    lines fill green, 19 filled · 12 left · 16 transfer, See my plan, Check what was read. The counts
    come from the report's verdicts when the reader found them, else from the ledger over the rows
    it is about to save. See my plan saves (class_history, saved_classes, degree_audit) and opens
    the Planner.

  CHECK (screen 3)  Open · Filled · Classes segments, a flag on every row; a flagged line is left out
    of what's saved and its de-identified words go to dpr_flags. "Looks right" is the only button.

  PLANNER  Empty: the upload card plus the laptop link. First open: "What matters most?" — ONE tap
    (degree · professors · friends) and units 12–20 (16) — kept in planner_prefs (on the phone until
    the SQL runs). Then Plan A is DRAFTED ON ARRIVAL into an empty Plan A (and B, C), shown as the
    plan card (week, one row per class with time · professor ★, units · ★ avg · friends · days off,
    Edit Plan A) with an A/B/C switch, and "More picks" under it — no score, no colour bar, "Catch up"
    instead of "Behind". Every pick is scored out of 100 in five parts the Why sheet shows: Requirements
    40 · Urgency 30 · Professor 15 · Friends 10 · Seats 5, the student's first priority ×1.5, second
    ×1.0, third ×0.6. Seats count — and seat chips show — only once registration is open
    (CFG.REGISTRATION_OPENS); before that the Planner says "Registration opens Nov 3". Everything filled
    (the report says 0 open) → the green card and "Something fun" from Tate and Sean's list
    (app-dev/source/fun-classes.json), only classes offered this term, real ratings and seats.
    B is A with the next-best sections (after registration opens: at-risk sections swapped for open
    ones); C re-ranks with friends ×2.5. A drafted plan never overwrites one the student made; Re-draft
    keeps what they added by hand. The Plans tab says how B and C differ from A in one line.

Usage: python3 dpr-flow-2026-10-08.py <repo-dir>   (reads app-dev/source/fun-classes.json).
Replayable: every anchor must match exactly once.
"""
import sys, os, json, re
D = sys.argv[1]
PI = os.path.join(D, 'app', 'index.html'); PP = os.path.join(D, 'app', 'planner.js')
A = open(PI, encoding='utf-8').read(); P = open(PP, encoding='utf-8').read()

def rep(a, b, label, which='A'):
    global A, P
    src = A if which == 'A' else P
    n = src.count(a)
    if n != 1: sys.exit(f'{label}: anchor matched {n}x')
    src = src.replace(a, b)
    if which == 'A': A = src
    else: P = src

FUN = json.load(open(os.path.join(D, 'app-dev', 'source', 'fun-classes.json'), encoding='utf-8'))
FUN_JS = json.dumps([{ 'g': g['name'], 'code': c['code'], 'title': c['title'], 'units': c['units'], **({'needs': c['needs']} if c.get('needs') else {}) } for g in FUN['groups'] for c in g['classes']], ensure_ascii=False, separators=(',', ':'))

# ================================================================================================
# planner.js — reader v2
# ================================================================================================
AUDIT = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dpr-flow-audit.js'), encoding='utf-8').read()
rep("var PDFJS_BASE='https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/legacy/build/';",
    AUDIT + "var PDFJS_BASE='https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/legacy/build/';", 'pl-audit-fn', 'P')
rep("  return {ok:true, rows:out, program:prog, skipped:skipped,",
    "  /* reader v2: the report's own verdicts (never a grade; an unplaceable verdict is 'unknown'). The classes\n     being taken: ungraded rows in a term after the last graded one (this term, or one registered ahead). */\n  var lastGraded=0; out.forEach(function(r){ if(!r._open){ var v=r.year*10+(ORD[r.term]||0); if(v>lastGraded)lastGraded=v; } });\n  var taking=[]; out.forEach(function(r){ if(r._open&&(r.year*10+(ORD[r.term]||0))>lastGraded){ var w='|'+r.term+' '+r.year; if(r.code)taking.push(r.code+w); if(r.cur)taking.push(r.cur+w); } });\n  var audit=null; try{ audit=dprAudit(text, cross, taking); }catch(e){ audit={ok:false,blocks:[],reqs:[],counts:{satisfied:0,not:0,in_progress:0,unknown:0},err:String(e&&e.message||e)}; }\n  return {ok:true, rows:out, program:prog, skipped:skipped, audit:audit,", 'pl-audit-return', 'P')
rep("dprLooksLikeOne: dprLooksLikeOne, dprParse: dprParse,", "dprLooksLikeOne: dprLooksLikeOne, dprParse: dprParse, dprAudit: dprAudit,", 'pl-audit-export', 'P')

# ================================================================================================
# app/index.html — 1. config, tabs, state
# ================================================================================================
rep("""  REGISTRATION_OPENS: '2026-10-19',
  REGISTRATION_TERM: 'Spring 2027',""",
"""  REGISTRATION_OPENS: '2026-10-19',
  REGISTRATION_TERM: 'Spring 2027',
  /* 'December 22 … End of term' — registrar.calpoly.edu/academic-calendar, Fall 2026. Until then a
     first-year has nothing on their Degree Progress Report, so the Planner uses their flowchart. */
  TERM_ENDS: '2026-12-22',""", 'cfg-term-ends')

rep(""" <div class="stabs">${[['mine', 'My Classes'], ['plans', 'Plans'], ['past', 'Past classes'], ['planner', 'Planner']].map(([k, l]) => `<button class="${t === k ? 'on' : ''}" data-a="schedTab" data-x="${k}">${l}</button>`).join('')}</div>""",
""" <div class="stabs">${[['mine', 'My Classes'], ['plans', 'Plans'], ['planner', 'Planner'], ['past', 'Past classes']].map(([k, l]) => `<button class="${t === k ? 'on' : ''}" data-a="schedTab" data-x="${k}">${l}</button>`).join('')}</div>""", 'tabs-order')

# the loads: the audit and the prefs ride with the first load; a missing table (SQL 14 not run) falls back to the phone
rep("""  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads())]);
  loadSuggestions(); loadRateList(); loadFriendPlans();""",
"""  await Promise.all([loadMine(), loadFriends(), loadPlans(), loadWatches(), loadReviews(), blk.then(() => loadThreads()), loadAudit(), loadPrefs()]);
  loadSuggestions(); loadRateList(); loadFriendPlans();""", 'load-audit-prefs')

rep("""/* ---- Plans A–C (the same plans table and rules the desktop's Plans use). ---------------------- */
const PLAN_LOCAL = 'termchamp_app_plans_v1';""",
"""/* ---- The report's verdicts (degree_audit) and the Planner's two preferences (planner_prefs) -------
   Both are owner-only tables from sql/professify-planner.sql (RUN 14). Until Tate runs it the phone keeps
   each on the device, per account, and says nothing — the Planner works either way. No grade and no ID
   ever reach either: the reader strips them before anything leaves readDpr(). */
const AUDIT_KEY = () => 'tc-audit:' + ((TC.user && TC.user.id) || '');
const PREFS_KEY = () => 'tc-prefs:' + ((TC.user && TC.user.id) || '');
const PREF_ORDER = { degree: ['degree', 'professors', 'friends'], professors: ['professors', 'degree', 'friends'], friends: ['friends', 'degree', 'professors'] };
const PREF_LABEL = { degree: 'Finishing my degree', professors: 'Great professors', friends: 'Classes with friends' };
/* What's kept of a report line: its words, the verdict, the counts, the classes that clear it — nothing
   else. The reader never keeps a grade or an ID; this checks again before anything is stored or sent: a
   label with a 7-digit number, "EMPLID", "Name:" or a grade beside units is dropped, counts are numbers,
   class codes are class codes. (SQL 14 refuses the same on the server.) */
const DPR_PII = /\\d{7,}|EMPLID|\\bName\\s*:|(?:^|\\s)(?:[A-DF][+-]?|CR|NC|W|WU|IC|I|RP|AU|P|NP|IP|RD|NG)\\s+\\d+\\.\\d{2}\\b/i;
const auditNums = u => { if (!u || typeof u !== 'object') return null; const n = v => v == null || v === '' || !isFinite(+v) ? null : Math.round(+v * 10) / 10; const o = { req: n(u.req), used: n(u.used), need: n(u.need) }; return o.req == null && o.used == null && o.need == null ? null : o; };
function auditRow(b) {
  const label = String(b.label || '').replace(/\\s+/g, ' ').trim().slice(0, 160);
  return { label: DPR_PII.test(label) ? '' : label, status: ['satisfied', 'not', 'in_progress', 'unknown'].includes(b.status) ? b.status : 'unknown',
    kind: /^(ge|conc|units|gwr|uscp|gpa|elective|major)$/.test(b.kind || '') ? b.kind : null, ge: /^[A-Z0-9]{1,4}$/.test(b.ge || '') ? b.ge : null,
    level: /^(RG|RQ|LN)$/.test(b.level || '') ? b.level : null, code: /^R[G\\d]*-\\d{1,6}$/.test(b.code || '') ? b.code : null,
    units: auditNums(b.units), courses: auditNums(b.courses), options: (b.options || []).filter(c => /^[A-Z]{2,5} \\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf };
}
function auditFrom(row) {
  if (!row) return null;
  const reqs = Array.isArray(row.requirements) ? row.requirements : [];
  const n = { satisfied: 0, not: 0, in_progress: 0, unknown: 0 }; reqs.forEach(b => { n[b.status] = (n[b.status] || 0) + 1; });
  return { reqs, counts: n, catalog: row.catalog || '', major: row.major || '', conc: row.concentration || '', units_used: row.units_used, units_needed: row.units_needed, read_at: row.read_at || null, overrides: Array.isArray(row.overrides) ? row.overrides : [] };
}
async function loadAudit() {
  TC.audit = null; TC.auditLocal = false; TC.auditLoaded = false;
  let c = null; try { c = JSON.parse(localStorage.getItem(AUDIT_KEY()) || 'null'); if (c && c.requirements) { TC.audit = auditFrom(c); TC.auditLocal = true; } } catch (e) {}
  let r; try { r = await TC.client().from('degree_audit').select('printed_on,catalog,major,concentration,units_used,units_needed,requirements,overrides,read_at').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.audit = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.audit; TC.auditLoaded = true;
  /* what this phone saved while the account couldn't be reached goes up now: a report read, or marks */
  if (c && c.requirements && c.pending && (!r.data || !r.data.read_at || (c.read_at || '') > r.data.read_at)) { TC.audit = auditFrom(c); TC.auditLocal = true; const up = Object.assign({}, c); delete up.pending; delete up.ovPending;
    /* the account's marks stand unless this phone has marks of its own waiting to go up */
    if (!c.ovPending) { delete up.overrides; TC.audit.overrides = (r.data && Array.isArray(r.data.overrides)) ? r.data.overrides : (c.overrides || []); }
    const q = await TC.client().from('degree_audit').upsert(up, { onConflict: 'user_id' }); if (!q.error) { TC.auditLocal = false; try { localStorage.setItem(AUDIT_KEY(), JSON.stringify(Object.assign({}, up, { overrides: TC.audit.overrides }))); } catch (e) {} } return; }
  if (r.data) { TC.audit = auditFrom(r.data); TC.auditLocal = false;
    if (c && c.ovPending && Array.isArray(c.overrides)) { TC.audit.overrides = c.overrides; TC.saveOverrides(c.overrides); } }
}
TC.saveAudit = async function (a, prog) {
  const reqs = (a && a.ok && a.reqs ? a.reqs : []).filter(b => !b.flag).map(auditRow).filter(b => b.label || b.options.length);
  const num = v => v == null || !isFinite(+v) ? null : Math.round(+v * 10) / 10;
  const row = { user_id: TC.user.id, printed_on: null, catalog: (prog && prog.catalog) || null, major: (prog && prog.major) || null, concentration: (prog && prog.conc) || null,
    units_used: num(a && a.units_used), units_needed: num(a && a.units_needed), requirements: reqs, read_at: new Date().toISOString(),
    /* what the student marked done stays marked through a new upload */
    overrides: (TC.audit && Array.isArray(TC.audit.overrides)) ? TC.audit.overrides : [] };
  try { localStorage.setItem(AUDIT_KEY(), JSON.stringify(Object.assign({ pending: true }, row))); } catch (e) {}
  TC.audit = auditFrom(row); TC.auditLocal = true;
  if (TC.err.audit === 'missing') return null;
  /* marks are only written when this session read them: a failed read never blanks them on the account */
  const up = Object.assign({}, row); if (!TC.auditLoaded) delete up.overrides;
  const q = await TC.client().from('degree_audit').upsert(up, { onConflict: 'user_id' });
  if (q.error) { if (schemaGap(q.error)) { TC.err.audit = 'missing'; return null; } return dbSay(q.error, 'Couldn’t save what your report says — it’s kept on this phone for now.'); }
  try { localStorage.setItem(AUDIT_KEY(), JSON.stringify(row)); } catch (e) {}
  TC.auditLocal = false; return null;
};
async function loadPrefs() {
  TC.prefs = null;
  try { const c = JSON.parse(localStorage.getItem(PREFS_KEY()) || 'null'); if (c && PREF_ORDER[c.priority]) TC.prefs = { priority: c.priority, units: +c.units || 16, local: true }; } catch (e) {}
  let r; try { r = await TC.client().from('planner_prefs').select('priority,units').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.prefs = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  delete TC.err.prefs;
  if (r.data && PREF_ORDER[r.data.priority]) TC.prefs = { priority: r.data.priority, units: +r.data.units || 16, local: false };
}
TC.savePrefs = async function (priority, units) {
  if (!PREF_ORDER[priority]) priority = 'degree';
  units = Math.min(20, Math.max(12, +units || 16));
  TC.prefs = { priority, units, local: true };
  try { localStorage.setItem(PREFS_KEY(), JSON.stringify({ priority, units })); } catch (e) {}
  if (TC.err.prefs === 'missing') return null;
  const q = await TC.client().from('planner_prefs').upsert({ user_id: TC.user.id, priority, units, updated_at: new Date().toISOString() }, { onConflict: 'user_id' });
  if (q.error) { if (schemaGap(q.error)) { TC.err.prefs = 'missing'; return null; } return dbSay(q.error, 'Couldn’t save that — it’s kept on this phone for now.'); }
  TC.prefs.local = false; return null;
};
/* "Send the link to my laptop": one email to the student's own verified address (3 a day, server-side). */
TC.requestPlannerLink = async function () {
  let r; try { r = await TC.client().rpc('request_planner_link'); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) return { err: schemaGap(r.error) ? 'Email isn’t set up on this server yet. On your laptop, open termchamp.com › Schedule › Planner and drop the PDF there.' : dbSay(r.error, 'Couldn’t send the link — try again.') };
  return { to: String(r.data || '') };
};
/* Lines the student marked done (auditOvMatch): { code, label, at } — the line's code, or its words when it
   has none; checked like every other line before it's stored. */
TC.saveOverrides = async function (list) {
  if (!TC.audit) return 'Upload your report first.';
  list = (list || []).slice(0, 100).map(o => { const label = String(o.label || '').replace(/\s+/g, ' ').trim().slice(0, 160);
    return { code: /^R[G\d]*-\d{1,6}$/.test(o.code || '') ? o.code : null, label: DPR_PII.test(label) ? '' : label, at: o.at || new Date().toISOString() }; }).filter(o => o.code || o.label);
  TC.audit.overrides = list;
  const A0 = TC.audit, keep = pending => { try { const c = JSON.parse(localStorage.getItem(AUDIT_KEY()) || 'null') || { user_id: TC.user.id, catalog: A0.catalog || null, major: A0.major || null, concentration: A0.conc || null, units_used: A0.units_used, units_needed: A0.units_needed, requirements: A0.reqs, read_at: A0.read_at }; if (c) { c.overrides = list; if (pending) c.ovPending = true; else delete c.ovPending; localStorage.setItem(AUDIT_KEY(), JSON.stringify(c)); } } catch (e) {} };
  keep(true);
  if (TC.err.audit === 'missing' || TC.auditLocal) return null;
  const q = await TC.client().from('degree_audit').update({ overrides: list }).eq('user_id', TC.user.id);
  if (q.error) return schemaGap(q.error) ? null : dbSay(q.error, 'Couldn’t save that to your account — it’s kept on this phone and goes up next time.');
  keep(false); return null;
};
/* A flagged line of the report, de-identified: the line's words (checked as above), the verdict and the counts. */
TC.flagDprLine = async function (b, prog) {
  const x = auditRow(b);
  const row = { who_hash: '', major: (prog && prog.major) || null, catalog: (prog && prog.catalog) || null, label: x.label || '(no words)', status: b.status === 'row' ? 'row' : x.status, units: x.units };
  try { const q = await TC.client().from('dpr_flags').insert(row); return !q.error; } catch (e) { return false; }
};
/* Today in San Luis Obispo, as YYYY-MM-DD (the registrar's dates are Pacific dates). */
function sloISO() { try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); } catch (e) { return new Date().toISOString().slice(0, 10); } }
/* Seats matter once registration for the term being planned is open; before that every section is at
   capacity and "12 seats" would read as scarcity. A term other than the one registration is coming for
   (today: Fall 2026, in session) is open. */
const regOpen = () => CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || (!!CFG.REGISTRATION_OPENS && sloISO() >= CFG.REGISTRATION_OPENS);
const regOpensText = () => { try { return new Date(CFG.REGISTRATION_OPENS + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); } catch (e) { return CFG.REGISTRATION_OPENS; } };
const termEndsText = () => { try { return new Date(CFG.TERM_ENDS + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); } catch (e) { return CFG.TERM_ENDS; } };
/* A first-year whose first grades haven't posted: the report is empty by definition (the Planner uses the flowchart). */
const firstYearEmpty = standing => standing === 'Freshman' && !!CFG.TERM_ENDS && sloISO() <= CFG.TERM_ENDS && !(TC.myHistory || []).length;

/* ---- Plans A–C (the same plans table and rules the desktop's Plans use). ---------------------- */
const PLAN_LOCAL = 'termchamp_app_plans_v1';""", 'audit-prefs-state')

# the plans: only a read that came back is a plan to draft into or not (review 2026-10-08, finding 1 —
# a failed read leaves TC.plans empty, and drafting into "empty" plans would overwrite the real ones)
rep("""async function loadPlans() {
  try {""", """async function loadPlans() {
  TC.plansLoaded = false;
  try {""", 'plans-loaded-reset')
rep("""  delete TC.err.plans;
  TC.plans = { A: [], B: [], C: [] };""", """  delete TC.err.plans;
  TC.plans = { A: [], B: [], C: [] }; TC.plansLoaded = true;""", 'plans-loaded')
# a drafted section gets no seat alert until the student puts it in a plan themselves (finding 8)
rep("""  if (inP && !w && SEC[id]) { TC.watch(id, true); TC.autoWatch[id] = 1; }""",
    """  if (inP && !w && SEC[id] && !draftOnly(id)) { TC.watch(id, true); TC.autoWatch[id] = 1; }""", 'plan-watch-draft')
# a deleted account leaves nothing of the report, the answers or the drafts on the phone (finding 20)
rep("""  try { [KEY, RECENT_KEY, DRAFT_KEY, ONB_KEY, 'professify_rev_times'].forEach(k => localStorage.removeItem(k)); } catch (e) {}""",
    """  try { [KEY, RECENT_KEY, DRAFT_KEY, ONB_KEY, 'professify_rev_times', AUDIT_KEY(), PREFS_KEY(), PLDRAFT_KEY(), plSkipKey()].forEach(k => localStorage.removeItem(k)); } catch (e) {}""", 'delete-planner-keys')

# ================================================================================================
# app/index.html — 2. the read: Report read (screen 2) and Check what was read (screen 3)
# ================================================================================================
rep("""    UI.dpr = { busy: 'Reading your report…' }; UI.sheet = { type: 'dpr' }; render(true);""",
    """    UI.dpr = { busy: 'Reading your report…' }; UI.sheet = { type: 'dprRead' }; render(true);""", 'dpr-sheet-type')

OLD_SHEET_START = "SHEETS.dpr = () => {\n  const r = UI.dpr; if (!r) return '';"
# the old sheet's last line: as of 23:15, or as of 19:15 (which added "You're all caught up" + Done — kept below on Report read)
OLD_SHEET_END = "  <button class=\"btn\" style=\"margin-top:12px\" data-a=\"dprSave\" ${n && !UI.busy.dpr ? '' : 'disabled'}>${UI.busy.dpr ? 'Saving…' : n ? `Add ${n} class${n === 1 ? '' : 'es'}` : 'Nothing selected'}</button>`;\n};\n"
OLD_SHEET_END_1915 = "  <button class=\"btn\" style=\"margin-top:10px\" data-a=\"closeSheet\">Done</button>` : `<button class=\"btn\" style=\"margin-top:12px\" data-a=\"dprSave\" ${n && !UI.busy.dpr ? '' : 'disabled'}>${UI.busy.dpr ? 'Saving…' : n ? `Add ${n} class${n === 1 ? '' : 'es'}` : 'Nothing selected'}</button>`}`;\n};\n"
if A.count(OLD_SHEET_END_1915) == 1: OLD_SHEET_END = OLD_SHEET_END_1915
i0 = A.find(OLD_SHEET_START); i1 = A.find(OLD_SHEET_END)
if i0 < 0 or i1 < 0 or A.count(OLD_SHEET_START) != 1: sys.exit('dpr-sheet: old sheet not found once')
A = A[:i0] + r'''/* ---- Screen 2 · Report read (Tate's look A, 2026-10-08) and screen 3 · Check what was read -------
   The report is never shown — a page illustration fills green as the read finishes — and only the
   essentials are: major · year, filled · left · transfer. The counts are the report's own verdicts when
   the reader found them; otherwise the ledger over the rows about to be saved (and the pills say so). */
function dprCounts(r) {
  const a = r && r.audit, xfer = (r && r.rows || []).filter(x => x._xfer && !x.flag).length;
  /* the report's verdicts, counted the way the Planner counts them (auditLines): filled = Satisfied + In
     Progress, left = Not Satisfied, can't check = a verdict the reader couldn't place */
  const X = a && a.ok ? auditLines(a, null) : null;
  if (X) return { filled: X.filled.length, left: X.open.length, unknown: X.unknown.length, xfer, src: 'report' };
  /* no verdicts read: the flowchart ledger over the record as it will be after the save (this term's
     classes included — they count as filled, in progress, as they will on the Planner) */
  if (!window.TCPL || !(TC.profile && TC.profile.major)) return { filled: null, left: null, unknown: 0, xfer, src: null };
  try {
    const add = (r.rows || []).filter(x => x.pick && !x.already && !x.skip && !x.flag).map(x => ({ code: x.cur, term: x.term, year: x.year }));
    plSync(); TCPL.set({ history: (TC.myHistory || []).concat(add) });
    const L = TCPL.ledger(); plSync();
    return L ? { filled: L.F + L.T, left: L.need.length + L.needU.length, unknown: L.cant.length + L.concUnchosen, xfer, src: 'flowchart' } : { filled: null, left: null, unknown: 0, xfer, src: null };
  } catch (e) { try { plSync(); } catch (x) {} return { filled: null, left: null, unknown: 0, xfer, src: null }; }
}
/* The major a screen shows: the profile's, or the report's when it's one of the app's majors (the report
   prints a plan code like "BUS", never shown on its own). */
const dprMajorShown = prog => (TC.profile || {}).major || (prog && prog.major && window.TCPL && TCPL.majors.includes(prog.major) ? prog.major : '');
const dprPage = () => `<div class="dr-pg" aria-hidden="true"><i style="width:70%"></i><i style="width:45%"></i><i class="g" style="width:90%"></i><i class="g" style="width:80%"></i><i class="g" style="width:85%"></i><i style="width:60%"></i><i class="g" style="width:88%"></i><i style="width:50%"></i><i class="g" style="width:75%"></i><span class="dr-badge">${ic('check', 36, 3.4)}</span></div>`;
SHEETS.dprRead = () => {
  const r = UI.dpr; if (!r) return '';
  const top = `<div class="at-top"><span class="at-kick">DEGREE PROGRESS REPORT</span><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>`;
  if (r.busy) return `<div class="dr">${top}<div class="dr-mid"><div class="dr-pg busy" aria-hidden="true"><i style="width:70%"></i><i style="width:45%"></i><i style="width:90%"></i><i style="width:80%"></i><i style="width:85%"></i><i style="width:60%"></i><i style="width:88%"></i><i style="width:50%"></i><i style="width:75%"></i></div><div class="dr-h">Reading your report…</div></div></div>`;
  if (r.err) return `<div class="dr">${top}<div class="dr-mid"><div class="dr-h">Couldn’t read it</div><div class="tc-err" style="margin-top:4px">${esc(r.err)}</div></div><div class="dr-foot"><label class="btn" style="cursor:pointer">Try another PDF<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label></div></div>`;
  const P = TC.profile || {}, prog = r.program || {}, c = dprCounts(r);
  const major = dprMajorShown(prog), yr = P.class_standing || '';
  const pills = [c.filled != null ? `<span class="dr-pill ok">${c.filled} filled</span>` : '', c.left != null ? `<span class="dr-pill left">${c.left} left</span>` : '', c.unknown ? `<span class="dr-pill unk">${c.unknown} can’t check</span>` : '', c.xfer ? `<span class="dr-pill xfer">${c.xfer} transfer</span>` : ''].filter(Boolean).join('');
  return `<div class="dr">${top}
  <h1 class="dr-h1">Report read</h1>
  <div class="dr-sub">${esc([major, yr].filter(Boolean).join(' · ') || `${r.rows.length} classes`)}</div>
  <div class="dr-mid">${dprPage()}<div class="dr-pills">${pills || `<span class="dr-pill ok">${r.rows.length} classes</span>`}</div>${c.src === 'flowchart' ? '<div class="dr-note">Counted against your flowchart — this report doesn’t print verdicts the app can read.</div>' : ''}${r.rows.length && r.rows.every(x => x.already) ? '<div class="dr-note dr-allin">You’re all caught up — every class on this report is already in TermChamp.</div>' : ''}</div>
  ${r.saveErr ? `<div class="tc-err">${esc(r.saveErr)}</div>` : ''}
  <div class="dr-foot"><button class="btn" data-a="dprSave" ${UI.busy.dpr ? 'disabled' : ''}>${UI.busy.dpr ? 'Saving…' : 'See my plan'}</button><button class="dr-link" data-a="dprCheck">Check what was read</button></div></div>`;
};
SHEETS.dprRead.full = true; SHEETS.dprRead.label = 'Report read';
SHEETS.dprCheck = sh => {
  const r = UI.dpr; if (!r) return '';
  const a = r.audit, X = a && a.ok ? auditLines(Object.assign({}, a, { reqs: (a.reqs || []).map(b => b.flag ? Object.assign({}, b, { flag: false, _was: b }) : b) }), null) : null, has = !!X, seg = sh.seg || 'open';
  /* flagged lines stay on screen (struck through) so a mis-tap can be undone; the counts leave them out */
  const orig = b => b._was || b, cov = b => X && X.covered.get(b);
  const open = has ? X.open : [], unk = has ? X.unknown : [], filled = has ? X.filled : [];
  const live = b => !orig(b).flag;
  const rows = r.rows.filter(x => !x.skip);
  const flag = (kind, i, on) => `<button class="dr-flag ${on ? 'on' : ''}" data-a="dprFlag" data-x="${kind}" data-y="${i}" aria-label="${on ? 'Flagged as wrong' : 'Flag this line as wrong'}" aria-pressed="${on}">${ic('flag', 15, 2.6)}</button>`;
  const req = b => { const o = orig(b); return `<div class="dr-row ${o.flag ? 'flagged' : ''}">${auditTag(o)}<span class="dr-lab">${esc(o.label || 'Requirement')}</span><span class="dr-u">${X && X.manual.has(b) ? 'marked done' : o.status === 'unknown' ? 'can’t check' : cov(b) ? 'taking ' + esc(cov(b)) : o.status === 'not' && o.units && o.units.need != null ? auditNum(o.units.need) + ' u' : o.status === 'not' && o.courses && o.courses.need != null ? auditNum(o.courses.need) + (+o.courses.need === 1 ? ' class' : ' classes') : o.status === 'in_progress' ? 'in progress' : ''}</span>${flag('req', a.reqs.indexOf(o), !!o.flag)}</div>`; };
  const cls = (x, i) => `<div class="dr-row ${x.flag ? 'flagged' : ''}"><span class="code">${esc(x.cur)}</span><span class="dr-lab">${esc(String(x.name || x._title || '').replace(/^\(\d{4}\)\s*/, ''))}</span><span class="dr-u">${esc(x.term + ' ' + x.year)}${x._xfer ? ' · transfer' : ''}</span>${flag('row', r.rows.indexOf(x), !!x.flag)}</div>`;
  const body = seg === 'classes' ? (rows.length ? rows.map(cls).join('') : '<div class="dr-empty">No classes on the report.</div>')
    : !has ? `<div class="dr-empty">This report doesn’t print verdicts the app can read, so what you still need is counted against your flowchart. Your classes are under <b>Classes</b>.</div>`
    : seg === 'filled' ? (filled.length ? filled.map(req).join('') : '<div class="dr-empty">Nothing filled yet.</div>')
    : (open.length ? open.map(req).join('') : unk.length ? '' : '<div class="dr-empty">Nothing open — every requirement is filled.</div>') + (unk.length ? `<div class="dr-subh">Can’t check · ${unk.filter(live).length}</div>${unk.map(req).join('')}` : '');
  const n = { open: open.filter(live).length, filled: filled.filter(live).length, classes: rows.filter(x => !x.flag).length };
  return `<div class="dr dr-check"><div class="at-top"><button class="xbtn" data-a="dprBack" aria-label="Back">${ic('chevL', 18, 2.6)}</button><span class="at-kick">YOUR REPORT</span><span style="width:40px"></span></div>
  <div class="seg dr-seg" role="tablist">${[['open', 'Open'], ['filled', 'Filled'], ['classes', 'Classes']].map(([k, l]) => `<button class="${seg === k ? 'on' : ''}" data-a="dprSeg" data-x="${k}" role="tab" aria-selected="${seg === k}">${l} · ${n[k]}</button>`).join('')}</div>
  <div class="card dr-list">${body}</div>
  ${r.flagged ? `<div class="dr-note">${r.flagged} line${r.flagged === 1 ? '' : 's'} flagged — left out and sent to TermChamp without your name.</div>` : ''}
  ${r.saveErr ? `<div class="tc-err">${esc(r.saveErr)}</div>` : ''}
  <div class="dr-foot"><button class="btn" data-a="dprSave" ${UI.busy.dpr ? 'disabled' : ''}>${UI.busy.dpr ? 'Saving…' : 'Looks right'}</button></div></div>`;
};
SHEETS.dprCheck.full = true; SHEETS.dprCheck.label = 'Check what was read';
''' + A[i1 + len(OLD_SHEET_END):]

# the actions: save (rows + the report's verdicts + flags) and the check screen's taps
rep("""  dprSave: async () => { if (UI.busy.dpr) return; UI.busy.dpr = 1; render(true); const e = await TC.saveDpr(UI.dpr); UI.busy.dpr = 0; if (e) { UI.dpr.saveErr = e; return render(true); } UI.sheet = null; UI.pl = null; render(true); },""",
"""  dprCheck: () => { UI.sheet = { type: 'dprCheck', seg: 'open' }; render(true); },
  dprBack: () => { UI.sheet = { type: 'dprRead' }; render(true); },
  dprSeg: k => { if (UI.sheet && UI.sheet.type === 'dprCheck') { UI.sheet.seg = k; render(true); } },
  dprFlag: (kind, i) => {
    const r = UI.dpr; if (!r) return;
    const it = kind === 'req' ? (r.audit && r.audit.reqs || [])[+i] : r.rows[+i]; if (!it) return;
    it.flag = !it.flag; if (kind === 'row') it.pick = !it.flag && !it.already;
    r.flagged = (r.audit && r.audit.reqs || []).filter(b => b.flag).length + r.rows.filter(x => x.flag).length;
    render(true);
  },
  /* See my plan / Looks right: the rows (minus flagged ones), the report's verdicts, the flags — then the Planner */
  dprSave: async () => {
    const r = UI.dpr; if (!r || UI.busy.dpr) return;
    r.saveErr = null; UI.busy.dpr = 1; render(true);
    const notes = [];
    try {
      r.rows.forEach(x => { if (x.flag) x.pick = false; });
      const e = await TC.saveDpr(r);
      if (e) { r.saveErr = e; return; }
      const e2 = await TC.saveAudit(r.audit, r.program);
      if (e2) notes.push(e2);
      const flagged = (r.audit && r.audit.reqs || []).filter(b => b.flag).concat(r.rows.filter(x => x.flag).map(x => ({ label: x.cur + ' · ' + x.term + ' ' + x.year, status: 'row' })));
      if (flagged.length) { const sent = await Promise.all(flagged.map(b => TC.flagDprLine(b, r.program))); if (!sent.every(Boolean)) notes.push('The flags couldn’t be sent — those lines are still left out.'); }
      /* the report fills blanks on the profile, never overwrites a choice: the major only when it's one of
         the app's majors (reports print a plan code like "BUS"), the concentration only when it's one of
         that major's */
      const prog = r.program || {}, P = TC.profile || {}, patch = {};
      if (prog.major && !P.major && window.TCPL && TCPL.majors.includes(prog.major)) patch.major = prog.major;
      const maj = patch.major || P.major;
      if (prog.conc && maj && !P.concentration && window.TCPL) { const ci = TCPL.concInfo(maj), hit = ci && (ci.list || []).find(c => c.name.toLowerCase() === String(prog.conc).toLowerCase()); if (hit) patch.concentration = hit.name; }
      if (Object.keys(patch).length) { const e3 = await TC.updateProfileFields(patch); if (e3) notes.push('Your major from the report wasn’t saved: ' + e3); }
      /* the Planner re-drafts any plan still exactly as it was drafted, from what the report says now */
      UI.sheet = null; UI.pl = null; UI.plRefresh = true;
      S.tab = 'schedule'; S.schedTab = 'planner'; save();
    } catch (err) { r.saveErr = 'Couldn’t save that — try again.'; }
    finally { UI.busy.dpr = 0; if (notes.length) toast(notes.join(' ')); render(true); }
  },""", 'dpr-actions')

# ================================================================================================
# app/index.html — 3. onboarding: the report is the LAST step
# ================================================================================================
rep("""    <button type="button" class="ghost pink" data-a="onbStep" data-x="degree">${n ? 'Next' : 'Skip for now'}</button></div></div>`;
}
function onbDegree() {""",
"""    <button type="button" class="ghost pink" data-a="onbStep" data-x="confirm">${n ? 'Next' : 'Skip for now'}</button></div></div>`;
}
/* The last step (Tate, 2026-10-08): the report is where the Planner starts, and it's the hardest thing to
   do on a phone (portal → PDF → upload), so it never blocks the easy steps and has a way out to a laptop.
   A first-year whose first grades haven't posted has nothing on theirs: no button to decide about — the
   flowchart's first year is the plan until the term ends (CFG.TERM_ENDS). */
function onbDegree() {
  const calpoly = schoolForEmail((TC.user && TC.user.email) || '') === 'calpoly';
  const pre = UI.onbPre || {}, P = TC.profile || {}, standing = pre.standing || P.class_standing || '';
  if (firstYearEmpty(standing)) {
    const L = window.TCPL && P.major ? (plSync(), TCPL.ledger()) : null;
    const spring = L ? (L.grid || []).find(t => t.year === 1 && /spring/i.test(t.term)) : null;
    const slots = spring ? spring.slots.slice(0, 6) : [];
    return `<div class="scr">${onbTop({ progress: 4 })}<div class="body">
    <div class="stack"><div class="onb-ico teal">${ic('grad', 38, 2.2)}</div><h1>Nothing on your report yet</h1><p class="lead">Your flowchart is the plan until grades post.</p></div>
    ${slots.length ? `<div class="card pad col onb-fy"><div class="label">${esc(spring.term)} · Year 1</div>${slots.map(s => { const opts = (s.choice && s.choice.length > 1) ? s.choice : (s.codes && s.codes.length > 1) ? s.codes : null, code = s.code && !opts ? ((s.codes && s.codes[0]) || s.code) : ''; return `<div class="row"><span class="code">${esc(opts ? 'Pick 1' : code || 'GE')}</span><span class="t">${esc(opts ? (s.title || opts.join(' or ')) : code ? (courseName(code) || s.title) : (s.title || (s.area ? 'Area ' + s.area : 'General education')))}</span>${s.units != null ? `<span class="u">${esc(String(s.units))} u</span>` : ''}</div>`; }).join('')}</div>` : ''}
    <span class="chip blue onb-when">${ic('cal', 13, 2.6)}We’ll ask for it after ${esc(termEndsText())}</span></div>
    <div class="foot"><button type="button" class="btn" data-a="onbStep" data-x="payoff">Continue</button></div></div>`;
  }
  return `<div class="scr">${onbTop({ progress: 4 })}<div class="body">
    <div class="stack"><div class="onb-ico">${ic('check', 38, 2.4)}</div><h1>Upload your degree progress report</h1><p class="lead">Your Planner builds everything from it.</p></div>
    <div class="card steps"><div class="label">In Cal Poly’s portal</div>
     <div class="row"><div class="stepn">1</div><div><b style="font-weight:900">Cal Poly Portal</b><small>Student Center › Academic Progress</small></div></div>
     <div class="row"><div class="stepn">2</div><div><b style="font-weight:900">Degree Progress Report (DPR)</b><small>View PDF › Download</small></div></div>
     <div class="row"><div class="stepn">3</div><div><b style="font-weight:900">Upload it here</b></div></div></div>
    <div class="lock"><span class="dot">${ONB_I.lock}</span>Private · grades and ID never saved.</div></div>
    <div class="foot">${calpoly ? `<label class="btn" style="cursor:pointer">${ONB_I.file}Upload DPR<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label>
    <button type="button" class="btn soft onb-laptop" data-a="plLaptop" ${UI.busy.laptop ? 'disabled' : ''}>${ONB_I.mail}${UI.busy.laptop ? 'Sending…' : 'Send the link to my laptop'}</button>` : ''}
    <button type="button" class="ghost" data-a="onbStep" data-x="payoff">Skip for now</button></div></div>`;
}
function onbDegreeOld() {""", 'onb-degree')

# the old degree screen's function is kept under its old name but nothing calls it; its text was the
# previous step 2 of 2. Remove it outright so no stale copy ships.
i0 = A.find("function onbDegreeOld() {"); i1 = A.find("function onbConfirm() {")
if i0 < 0 or i1 < 0 or i1 < i0: sys.exit('onb-degree-old: bounds')
A = A[:i0] + A[i1:]

rep("""    <button type="button" class="ghost pink" data-a="onbStep" data-x="degree">Upload DPR too</button></div></div>`;""",
    """</div></div>`;""", 'onb-manual-no-dpr')
rep("""    <div class="foot"><button type="button" class="btn" data-a="onbStep" data-x="payoff">Continue</button></div></div>`;
}
/* 11 — friends only (Tate): friends who took your classes, and friends in them this term. */""",
"""    <div class="foot"><button type="button" class="btn" data-a="onbStep" data-x="degree">Continue</button></div></div>`;
}
/* 11 — friends only (Tate): friends who took your classes, and friends in them this term. */""", 'onb-people-next')
rep("""    const st = S.stack[S.tab], top = st[st.length - 1], order = ['schedule', 'degree', 'confirm', 'people', 'payoff'];""",
    """    const st = S.stack[S.tab], top = st[st.length - 1], order = ['schedule', 'confirm', 'people', 'degree', 'payoff'];""", 'onb-order')
rep("""    <div class="stack"><div class="kicker">Step 1 of 2 · About 30 sec</div><h1>Add this term’s schedule</h1>""",
    """    <div class="stack"><div class="kicker">Step 1 of 4 · About 30 sec</div><h1>Add this term’s schedule</h1>""", 'onb-step1-kicker')
# the report saved during onboarding: straight to the Planner, onboarding done (was: on to "confirm")
rep("""/* The report's sheet is the app's own; when it's saved during onboarding, carry on to "confirm". */
const onbDprSave = A.dprSave;
A.dprSave = async () => {
  const prog = UI.dpr && UI.dpr.program;
  await onbDprSave();
  const top = cur();
  if (!UI.sheet && top && top.s === 'onb' && top.p && top.p.step === 'degree') { UI.onbProgram = prog || null; if (UI.onbPre && !TC.profile.major) delete UI.onbPre.major; onbGo('confirm'); }
};""",
"""/* The report saved during onboarding's last step: onboarding is done and the Planner opens on the plan. */
const onbDprSave = A.dprSave;
A.dprSave = async () => {
  const wasOnb = (() => { const top = cur(); return !!(top && top.s === 'onb' && top.p && top.p.step === 'degree'); })();
  await onbDprSave();
  if (wasOnb && !UI.sheet && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null); S.stack.home = [{ s: 'home' }]; UI.onbPre = null; UI.onbProgram = null; S.tab = 'schedule'; S.schedTab = 'planner'; save(); render(); setTimeout(() => TC.pushAsk('onboarding'), 600); }
};
/* "Send the link to my laptop" — from onboarding's last step and the empty Planner. */
A.plLaptop = async () => {
  if (UI.busy.laptop) return; UI.busy.laptop = 1; render(true);
  const r = await TC.requestPlannerLink(); UI.busy.laptop = 0;
  /* the email is queued: send_planner_links() runs every 5 minutes */
  toast(r.err ? r.err : `We’ll email the link to ${r.to} within 5 minutes — open it on your laptop`); render(true);
};""", 'onb-dpr-save-wrap')

# ================================================================================================
# app/index.html — 4. the Planner (replaces the 2026-10-06 picks view and the Why sheet)
# ================================================================================================
PLANNER = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dpr-flow-planner.js'), encoding='utf-8').read().replace('__FUN__', FUN_JS)
PL_A, PL_B = PLANNER.split('/* ---- sheets ---- */\n')
i0 = A.find("/* ---- TermChamp's picks ----"); i1 = A.find("/* ---- the year-by-year grid: the flowchart")
if i0 < 0 or i1 < 0 or i1 < i0: sys.exit('planner: bounds A')
A = A[:i0] + PL_A + A[i1:]
j0 = A.find("/* Why a pick is where it is: every reason planRecs() used, in plain words. */"); j1 = A.find("/* One tap = this class is on your record, with no term")
if j0 < 0 or j1 < 0 or j1 < j0: sys.exit('planner: bounds B')
A = A[:j0] + PL_B + A[j1:]

# the empty Planner: one card — Upload PDF, the laptop link, add by hand, skip (Planner only; Past classes keeps the card too)
rep("""function dprFirstCard() {
  return `<div class="tc-dpr"><div class="tc-dpr-ey">START HERE</div><h3>Upload your Degree Progress Report</h3>
  <p>Your past classes, what you’re taking now and what you still need fill in from one PDF. Then the Planner can pick your next classes.</p>
  <label class="btn tc-dpr-go">Upload the PDF<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label>
  <button class="btn tc-dpr-alt" data-a="sheet" data-x="logClass">Add classes one at a time</button>
  <small>It’s the PDF from the Cal Poly Portal. It’s read on your phone; only class codes and terms are saved — never your EMPLID or grades.</small></div>`;
}""",
"""function dprFirstCard() {
  return `<div class="tc-dpr"><div class="tc-dpr-ico">${ic('check', 40, 2.4)}</div><h3>Upload your degree report</h3>
  <p>Your picks and plans start here.</p>
  <label class="btn tc-dpr-go">Upload PDF<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label>
  <button class="tc-dpr-link" data-a="plLaptop" ${UI.busy.laptop ? 'disabled' : ''}>${UI.busy.laptop ? 'Sending…' : 'Send the link to my laptop'}</button>
  <button class="btn tc-dpr-alt" data-a="sheet" data-x="logClass">Add classes one at a time</button>
  <button class="tc-dpr-skip" data-a="plShowPicks">Skip for now</button></div>`;
}""", 'dpr-first-card')

# actions
rep("""  plShowPicks: () => { try { localStorage.setItem(plSkipKey(), '1'); } catch (e) {} render(true); },""",
"""  plShowPicks: () => { try { localStorage.setItem(plSkipKey(), '1'); } catch (e) {} render(true); },
  plShowPlan: k => { if (/^[ABC]$/.test(k)) UI.plPlan = k; render(true); },
  plEditPlan: k => { if (/^[ABC]$/.test(k)) S.plan = k; S.schedTab = 'plans'; save(); render(); },
  plMoreAll: () => { UI.plMoreAll = !UI.plMoreAll; render(true); },
  plFunAll: () => { UI.plFunAll = !UI.plFunAll; render(true); },
  /* "Draft it for me" on an empty plan: that plan only (the others are the student's) */
  plRedraft: k => {
    if (!/^[ABC]$/.test(k)) return; const g = plGate(); if (!g.L || !plCanDraft()) return;
    const n = plDraftSlot(k, planRank(g.L), g.L);
    toast(n ? `Plan ${k} drafted — only you can see it` : `Nothing fits Plan ${k} yet — add classes from the picks below`); render(true);
  },
  plMarkAsk: i => { if (TC.audit && TC.audit.reqs[+i]) { UI.sheet = { type: 'plMark', i: +i }; render(true); } },
  plMarkDo: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'plMark' || UI.busy.mark) return;
    const b = TC.audit && TC.audit.reqs[sh.i]; if (!b) return;
    UI.busy.mark = 1; render(true);
    let e; try { e = await TC.saveOverrides(auditOverrides().filter(o => !auditOvMatch(o, b)).concat([{ code: b.code || null, label: b.label || '' }])); } catch (x) { e = 'Couldn’t save that — try again.'; }
    UI.busy.mark = 0; UI.sheet = null; UI.plRefresh = true;
    toast(e || 'Marked done — undo it under Still need'); render(true);
  },
  plUnmark: async i => {
    const b = TC.audit && TC.audit.reqs[+i]; if (!b || UI.busy.mark) return;
    UI.busy.mark = 1;
    let e; try { e = await TC.saveOverrides(auditOverrides().filter(o => !auditOvMatch(o, b))); } catch (x) { e = 'Couldn’t save that — try again.'; }
    UI.busy.mark = 0; UI.plRefresh = true;
    toast(e || 'Back on your list'); render(true);
  },
  plRetryPlans: async () => { if (UI.busy.plans) return; UI.busy.plans = 1; render(true); try { await loadPlans(); } catch (e) { TC.err.plans = String(e && e.message || e); } finally { UI.busy.plans = 0; render(true); } },
  plPrefsOpen: () => { UI.sheet = { type: 'plPrefs' }; render(true); },
  plPrefPick: k => { if (UI.sheet && UI.sheet.type === 'plPrefs' && PREF_ORDER[k]) { UI.sheet.pick = k; render(true); } },
  plPrefUnits: u => { if (UI.sheet && UI.sheet.type === 'plPrefs') { UI.sheet.units = +u; render(true); } },
  plPrefsSave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'plPrefs' || UI.busy.prefs) return;
    const before = TC.prefs ? { priority: TC.prefs.priority, units: TC.prefs.units } : null;
    sh.err = null; UI.busy.prefs = 1; render(true);
    let e; try { e = await TC.savePrefs(sh.pick || (before && before.priority) || 'degree', sh.units || (before && before.units) || 16); } catch (x) { e = 'Couldn’t save that — try again.'; }
    UI.busy.prefs = 0; if (e) { sh.err = e; return render(true); }
    /* new answers: picks re-rank, and plans still exactly as drafted are drafted again */
    if (before && (before.priority !== TC.prefs.priority || before.units !== TC.prefs.units)) UI.plRefresh = true;
    UI.sheet = null; render(true);
  },""", 'planner-actions')

# the Plans tab: one line on how B or C differs from A
rep("""  <div class="regbar under"><span class="regbadge" style="background:var(--bg);color:var(--muted)">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span></div>""",
"""  <div class="regbar under"><span class="regbadge" style="background:var(--bg);color:var(--muted)">${TC.planShared[S.plan] !== false ? 'Friends can see' : 'Only you'}</span>${planDiffLine(S.plan) ? `<span class="pl-diff">${esc(planDiffLine(S.plan))}</span>` : ''}</div>""", 'plans-diff-line')

# the sheet behind the week stays interactive; the prefs sheet can't be dismissed before the first answer
rep("""  closeSheet: () => { UI.sheet = null; UI.champ = false; render(true); setBars(false); },""",
"""  closeSheet: () => { if (UI.sheet && UI.sheet.type === 'plPrefs' && !TC.prefs) return; UI.sheet = null; UI.champ = false; render(true); setBars(false); },""", 'close-sheet-prefs')

# ================================================================================================
# app/index.html — 5. CSS
# ================================================================================================
rep(""".pk-note{font-size:12.5px;font-weight:700;color:var(--muted);line-height:1.5;padding:14px 20px 0}""",
""".pk-note{font-size:12.5px;font-weight:700;color:var(--muted);line-height:1.5;padding:14px 20px 0}
/* DPR flow 2026-10-08 — Report read, Check, the Planner's plan card and picks, the prefs sheet, the Why sheet */
.pk-tag.t-amber,.t-amber{background:var(--amber-soft);color:var(--amber-ink)}
.dr{display:flex;flex-direction:column;min-height:100%;padding:calc(var(--sb) + 2px) 16px 24px;box-sizing:border-box}
.dr .at-top{padding:0 0 0 4px}
.dr-h1{font-size:34px;font-weight:900;line-height:40px;letter-spacing:-.02em;margin:8px 0 0}
.dr-sub{margin-top:8px;font-size:15px;line-height:20px;font-weight:800;color:var(--muted)}
.dr-mid{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;padding:24px 0}
.dr-h{font-size:22px;font-weight:900;text-align:center}
.dr-pg{position:relative;width:192px;height:240px;background:var(--card);border-radius:16px;box-shadow:0 20px 48px rgba(15,23,42,.14);padding:28px 24px;box-sizing:border-box;display:flex;flex-direction:column;gap:14px;animation:drRise .5s ease-out both}
.dr-pg i{display:block;height:8px;border-radius:4px;background:var(--fill)}
.dr-pg i.g{animation:drFill .35s ease-out both}
.dr-pg i.g:nth-child(3){animation-delay:.5s}.dr-pg i.g:nth-child(4){animation-delay:.65s}.dr-pg i.g:nth-child(5){animation-delay:.8s}.dr-pg i.g:nth-child(7){animation-delay:.95s}.dr-pg i.g:nth-child(9){animation-delay:1.1s}
.dr-pg.busy i{animation:drPulse 1.2s ease-in-out infinite}
.dr-badge{position:absolute;right:-20px;bottom:-20px;width:72px;height:72px;border-radius:50%;background:#0F766E;border:6px solid var(--bg);box-sizing:border-box;display:grid;place-items:center;color:#fff;animation:drPop .4s cubic-bezier(.2,1.4,.4,1) 1.35s both}
.dr-pills{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;animation:drUp .4s ease-out 1.5s both}
.dr-pill{display:inline-flex;align-items:center;height:40px;padding:0 16px;border-radius:20px;font-size:16px;font-weight:900}
.dr-pill.ok{background:var(--teal-soft);color:var(--teal-t,var(--teal))}
.dr-pill.left{background:var(--blue);color:#fff}
.dr-pill.xfer{background:var(--amber-soft);color:var(--amber-ink)}
.dr-pill.unk{background:var(--fill);color:var(--ink3)}
.dr-subh{padding:16px 0 4px;font-size:12px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);border-top:1px solid var(--line)}
.dr-note{font-size:12.5px;font-weight:700;color:var(--muted);text-align:center;line-height:1.45;padding:0 8px}
.dr-foot{display:flex;flex-direction:column;gap:8px}
.dr-foot .btn{height:52px;border-radius:18px}
.dr-link{height:36px;font-size:15px;font-weight:900;color:var(--muted);background:none}
.dr-check{padding-top:calc(var(--sb) + 2px)}
.dr-seg{margin:8px 0 14px;display:flex;gap:4px}
.dr-seg button{flex:1}
.dr-list{padding:4px 12px;flex:1}
.dr-row{display:flex;align-items:center;gap:10px;min-height:52px;padding:8px 0;border-top:1px solid var(--line);font-size:15px;font-weight:800}
.dr-row:first-child{border-top:0}
.dr-row.flagged .dr-lab,.dr-row.flagged .dr-u{text-decoration:line-through;color:var(--muted)}
.dr-row .pk-tag{flex:none;min-width:44px;justify-content:center;display:inline-flex}
.dr-lab{flex:1;min-width:0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.25}
.dr-u{flex:none;font-size:13px;font-weight:800;color:var(--muted);white-space:nowrap}
.dr-flag{flex:none;width:32px;height:32px;border-radius:50%;display:grid;place-items:center;color:var(--line2,#C3CBD8);background:none}
.dr-flag.on{background:var(--red-soft);color:var(--red-ink)}
.dr-empty{padding:14px 2px;font-size:14px;font-weight:800;color:var(--ink3);line-height:1.45}
.dr-empty b{color:var(--ink)}
@keyframes drFill{to{background:#BBF7D0}}
@keyframes drPop{from{transform:scale(0)}to{transform:scale(1)}}
@keyframes drRise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes drUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes drPulse{0%,100%{opacity:.5}50%{opacity:1}}
@media (prefers-reduced-motion:reduce){.dr-pg,.dr-pg i.g,.dr-badge,.dr-pills{animation:none}.dr-pg i.g{background:#BBF7D0}}
.tc-dpr-ico{width:56px;height:56px;border-radius:18px;background:rgba(255,255,255,.18);display:grid;place-items:center;color:#fff;margin-bottom:10px}
.tc-dpr .tc-dpr-link{display:block;width:100%;min-height:40px;margin-top:4px;font-size:14px;font-weight:900;color:#fff;background:none;text-align:center}
.tc-dpr .tc-dpr-skip{display:block;width:100%;min-height:36px;margin-top:4px;font-size:13.5px;font-weight:800;color:rgba(255,255,255,.8);background:none;text-align:center}
.pl-top{display:flex;align-items:flex-start;gap:12px;margin:24px 16px 0}
.pl-top>div{flex:1;min-width:0}
.pl-term{font-size:22px;font-weight:900;line-height:28px}
.pl-sub{font-size:14px;font-weight:800;color:var(--ink4);line-height:20px;margin-top:4px}
.pl-pill{flex:none;height:32px;padding:0 12px;border-radius:999px;background:var(--blue-soft);color:var(--blue-ink);font-size:13px;font-weight:900;white-space:nowrap}
.pl-card{margin:16px 16px 0;padding:16px;border-radius:22px;display:flex;flex-direction:column;gap:16px}
.pl-head{display:flex;align-items:center;gap:10px}
.pl-letter{display:inline-flex;align-items:center;justify-content:center;height:28px;padding:0 12px;border-radius:9px;color:#fff;font-size:14px;font-weight:900}
.pl-name{font-size:17px;font-weight:900;flex:1}
.pl-seg{display:flex;background:var(--fill);border-radius:12px;padding:3px;gap:2px}
.pl-seg button{width:36px;height:30px;border-radius:9px;font-size:13px;font-weight:900;color:var(--muted);background:none}
.pl-seg button.on{color:#fff}
.pl-seg .pl-seg-A.on{background:#0F766E}.pl-seg .pl-seg-B.on{background:#C2410C}.pl-seg .pl-seg-C.on{background:#BE185D}
.pl-days{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;font-size:11px;font-weight:900;color:var(--muted);text-align:center;letter-spacing:.04em;margin-bottom:-10px}
.pl-wk{height:72px;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}
.pl-wk>div{position:relative;background:var(--bg);border-radius:8px;overflow:hidden}
.pl-wk i{position:absolute;left:0;right:0;border-radius:4px;display:block;min-height:8px}
.pl-rows{display:flex;flex-direction:column}
.pl-row{display:flex;align-items:center;gap:12px;min-height:56px;padding:8px 0;border-top:1px solid var(--line);text-align:left;width:100%;color:inherit;background:none}
.pl-row:first-child{border-top:0}
.pl-row .code{flex:none;min-width:84px;justify-content:center;display:inline-flex;height:28px;align-items:center;font-size:13px}
.pl-t{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.pl-n{font-size:15px;font-weight:900;line-height:18px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pl-m{font-size:12.5px;font-weight:800;line-height:16px;color:var(--ink4);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pl-u{flex:none;font-size:13px;font-weight:800;color:var(--muted)}
.pl-chips{display:flex;gap:8px;flex-wrap:wrap}
.pl-chip{height:28px;padding:0 10px;border-radius:14px;background:var(--bg);font-size:12px;font-weight:900;color:var(--ink3);display:inline-flex;align-items:center}
.pl-edit{height:48px;border-radius:16px;font-size:16px;box-shadow:none}
.pl-empty{font-size:14px;font-weight:800;color:var(--ink3);line-height:1.45}
.pl-sech{display:flex;align-items:baseline;margin:32px 16px 0;font-size:18px;font-weight:900}
.pl-sech>span{flex:1}
.pl-more{font-size:14px;font-weight:900;color:var(--blue-t,var(--blue));background:none;min-height:32px}
.pl-picks{display:flex;flex-direction:column;gap:12px;margin:12px 16px 0}
.pk-card{padding:16px;border-radius:22px;display:flex;flex-direction:column;gap:10px}
.pk-card .pk-main{gap:8px}
.pk-card .pk-foot{margin:0;padding:0;border:0;gap:8px}
.pk-card .pk-add{width:40px;height:40px;margin-left:auto}
.pl-ask{margin:16px 16px 0}
.pl-done{margin:16px 16px 0;padding:22px 18px;border-radius:24px;background:#0F766E;color:#fff;display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
.pl-done-ico{width:52px;height:52px;border-radius:50%;background:rgba(255,255,255,.2);display:grid;place-items:center}
.pl-done-h{font-size:22px;font-weight:900;line-height:1.15}
.pl-done-s{font-size:14px;font-weight:800;opacity:.9}
.pl-diff{font-size:12.5px;font-weight:800;color:var(--muted);margin-left:auto;text-align:right}
.pk-all .pl-need,.pk-all .pl-manual{display:flex;align-items:center;gap:10px}
.pl-mark{flex:none;min-height:36px;padding:0 12px;border-radius:12px;background:var(--bg);color:var(--blue-t,var(--blue));font-size:13px;font-weight:900;white-space:nowrap}
.pl-need-go{flex:none;min-width:36px;min-height:36px;display:grid;place-items:center;background:none}
.pl-subh{padding:14px 0 4px;font-size:12px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.pm-line{display:flex;align-items:center;gap:10px;margin-top:10px;font-size:16px}
.pm-p{font-size:14px;line-height:1.5;margin:12px 0 0}.pm-p.small{font-size:13px;margin-top:8px}
.pp-opts{display:flex;flex-direction:column;gap:10px}
.pp-opt{display:flex;align-items:center;gap:14px;background:var(--bg);border-radius:20px;padding:14px 16px;border:2px solid transparent;font-size:17px;font-weight:900;text-align:left;width:100%;color:var(--ink)}
.pp-opt.on{border-color:var(--blue);background:var(--blue-wash,var(--blue-soft))}
.pp-ic{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;flex:none;color:var(--ink)}
.pp-ck{margin-left:auto;width:26px;height:26px;border-radius:50%;border:2px solid var(--line2,#D5DCE8);flex:none;display:grid;place-items:center;color:#fff}
.pp-opt.on .pp-ck{background:var(--blue);border-color:var(--blue)}
.pp-units{display:flex;gap:8px}
.pp-units button{flex:1;height:46px;border-radius:14px;border:2px solid var(--blue-soft);background:var(--card);font-size:16px;font-weight:900;color:var(--blue-t,var(--blue))}
.pp-units button.on{background:var(--blue);border-color:var(--blue);color:#fff}
.pw-score{font-size:34px;font-weight:900;line-height:1;flex:none}
.pw-bars{display:flex;flex-direction:column;gap:10px;margin-top:14px}
.pw-row{display:grid;grid-template-columns:104px minmax(0,1fr) 48px;gap:10px;align-items:center}
.pw-row.off{opacity:.55}
.pw-lab{font-size:14px;font-weight:900}
.pw-track{height:12px;border-radius:6px;background:var(--fill);overflow:hidden}
.pw-track i{display:block;height:100%;border-radius:6px}
.pw-val{font-size:14px;font-weight:900;text-align:right;font-variant-numeric:tabular-nums}
.pw-why{display:flex;flex-direction:column;gap:8px;margin-top:14px;padding-top:12px;border-top:1px solid var(--line)}
.pw-why .why{display:flex;align-items:flex-start;gap:10px;font-size:14px;font-weight:800;line-height:1.35}
.pw-why .dot{width:10px;height:10px;border-radius:50%;flex:none;margin-top:5px}""", 'css')
# onboarding rules go AFTER Sean's unlayered block: everything under .onb is reset by @layer onbreset, so a rule
# inside @layer app never reaches it
rep("""@container phone (min-height: 900px){.onb .body{gap:22px}
.onb .clist{max-height:258px}
.onb h1{font-size:32px}}
""", """@container phone (min-height: 900px){.onb .body{gap:22px}
.onb .clist{max-height:258px}
.onb h1{font-size:32px}}
/* DPR flow 2026-10-08: the report step and the first-year state */
.onb .onb-ico{width:72px;height:72px;border-radius:22px;background:var(--blue);color:#fff;display:grid;place-items:center}
.onb .onb-ico.teal{background:#0F766E}
.onb .steps .row small{display:block;font-size:12.5px;font-weight:700;color:var(--muted);margin-top:2px}
.onb .onb-fy{gap:10px}
.onb .onb-fy .row{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:800;min-height:28px}
.onb .onb-fy .code{flex:none;white-space:nowrap;display:inline-flex;align-items:center;height:26px;padding:0 9px;border-radius:7px;background:var(--blue);color:#fff;font-size:12.5px;font-weight:900}
.onb .onb-fy .t{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.onb .onb-fy .u{flex:none;font-size:13px;font-weight:800;color:var(--muted);white-space:nowrap}
.onb .onb-when{gap:6px;align-self:flex-start;height:28px;display:inline-flex;align-items:center}
.onb .btn.soft.onb-laptop{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:8px;color:var(--blue-ink)}
.onb .btn.soft.onb-laptop svg{width:18px;height:18px}
""", 'css-onb')

# ================================================================================================
# write
# ================================================================================================
for bad in ['onbDegreeOld', '__FUN__']:
    if bad in A: sys.exit(f'leftover: {bad}')
open(PI, 'w', encoding='utf-8').write(A); open(PP, 'w', encoding='utf-8').write(P)
print('dpr-flow-2026-10-08: applied')
