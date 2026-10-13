#!/usr/bin/env python3
r"""The Degree Progress Report as the source of truth — the app (app/index.html). Tate, 2026-10-11. Run AFTER
dpr-truth-2026-10-11.py (the reader). Decisions (Tate, 2026-10-11): Past classes shows the report BY REQUIREMENT
(option A); the flowchart years show only when the report's catalog is a semester one; Plans A/B/C stay as they are
(next registration only; C stays the friends draft); no grade is ever stored.

What this changes:
  STORED (auditRow / TC.saveAudit): each report line keeps the classes the report used for it — code as printed,
    today's number, the term, transfer / being-taken flags — and the classes it lists but didn't count ("listed");
    the report's printed date (printed_on). No grade, no title, no ID: the same checks as before, and SQL 14's.
  GE AREAS (plGeArea): a report line's GE area in the app's (semester) vocabulary, from the registrar's own table
    (registrar.calpoly.edu/GE_2026, read 2026-10-11): A1→1C, A2→1A, A3→1B, B1→5A, B2→5B, B3→5C, B4→2, B UD→UD 2/5,
    C1→3A, C2→3B, C UD→UD 3, D1→4A, D2→4B, D UD→UD 4, E→4B ("an additional Area 4B course in fall 2026 or later"),
    F→6; a lower-division C elective is 3A or 3B; "GE Elective: Areas B, C, and D" is any of those. Semester lines
    that printed no area code ("Area 3: Upper-division Arts & Humanities", "(GE UD 2/5)") get theirs from the words.
    The Planner's picks, auditLines' "taking one of its classes" and the flowchart overlay all use it.
  PAST CLASSES (pastView → pcReportView): with a report in, the screen is the report's own requirements —
    Still needed on top (open, can't-read, in progress), then Major and support · Concentration · General education ·
    Degree requirements, each line naming the class the report used (as printed → today's number · term · the
    professor from your record, or "transfer credit", or "this term"); a Not Satisfied line whose listed class is on
    the report's Course History but wasn't counted wears "Needs a look"; "Units only" lists the classes the report
    used for nothing. The flowchart years (pcYears) show under it only for a semester catalog.
  RE-UPLOAD (TC.saveAudit → UI.dprDiff): what changed since the last report — lines newly filled, lines newly open,
    new lines — and which plans hold a class that filled an open line before and fills none now; a sheet after
    the save offers to take each out (never without a tap). Plans still exactly as drafted re-draft as before.

Usage: python3 dpr-truth-app-2026-10-11.py <repo-dir>      Replayable: every anchor must match once."""
import sys, os
D = sys.argv[1]
PA = os.path.join(D, 'app', 'index.html')
S = open(PA, encoding='utf-8').read()

def rep(a, b, label):
    global S
    n = S.count(a)
    if n != 1: sys.exit(f'app {label}: anchor matched {n}x')
    S = S.replace(a, b)

# ---- stored: used / listed / printed_on ----
rep("""    units: auditNums(b.units), courses: auditNums(b.courses), options: (b.options || []).filter(c => /^[A-Z]{2,5} \\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf };
}""", """    units: auditNums(b.units), courses: auditNums(b.courses), options: (b.options || []).filter(c => /^[A-Z]{2,5} \\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf,
    /* (2026-10-11) the classes the report used for this line: code as printed (a transfer placeholder's can lead with a
       digit, "5A5C 1TR"), today's number, the term, transfer / being taken — never a title, a grade or units */
    used: (b.used || []).filter(e => e && AUDIT_USED.test(e.c || '') && AUDIT_TERM.test(e.t || '')).slice(0, 40).map(e => { const o = { c: e.c, t: e.t }; if (e.n && AUDIT_CODE.test(e.n)) o.n = e.n; if (e.x) o.x = true; if (e.p) o.p = true; return o; }),
    listed: (b.listed || []).filter(c => AUDIT_CODE.test(c)).slice(0, 10) };
}
const AUDIT_CODE = /^[A-Z]{2,5}(?:\\/[A-Z]{2,5})? \\d{3,4}[A-Z]{0,2}$/, AUDIT_USED = /^[A-Z0-9]{2,6}(?:\\/[A-Z]{2,5})? [0-9][0-9A-Z]{0,5}$/, AUDIT_TERM = /^(?:Fall|Winter|Spring|Summer) \\d{4}$/;""", 'auditRow')
rep("""  const row = { user_id: TC.user.id, printed_on: null, catalog: (prog && prog.catalog) || null,""",
    """  /* (2026-10-11) what this report changes against the last one, for the sheet after the save */
  UI.dprDiff = auditDiff(TC.audit, a);
  const row = { user_id: TC.user.id, printed_on: (a && /^\\d{4}-\\d{2}-\\d{2}$/.test(a.printed || '')) ? a.printed : null, catalog: (prog && prog.catalog) || null,""", 'saveAudit-printed')
rep("""  let r; try { r = await TC.client().from('degree_audit').select('printed_on,catalog,major,concentration,units_used,units_needed,requirements,overrides,read_at').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.audit = schemaGap(r.error) ? 'missing' : r.error.message; return; }""",
    """  let r; try { r = await TC.client().from('degree_audit').select('printed_on,catalog,major,concentration,units_used,units_needed,requirements,overrides,read_at').eq('user_id', TC.user.id).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.audit = schemaGap(r.error) ? 'missing' : r.error.message; return; }""", 'loadAudit-noop')
rep("""  return { reqs, counts: n, catalog: row.catalog || '', major: row.major || '', conc: row.concentration || '', units_used: row.units_used, units_needed: row.units_needed, read_at: row.read_at || null, overrides: Array.isArray(row.overrides) ? row.overrides : [] };""",
    """  return { reqs, counts: n, catalog: row.catalog || '', major: row.major || '', conc: row.concentration || '', units_used: row.units_used, units_needed: row.units_needed, read_at: row.read_at || null, printed_on: row.printed_on || null, overrides: Array.isArray(row.overrides) ? row.overrides : [] };""", 'auditFrom-printed')

# ---- the diff between two reports, and GE areas in the app's vocabulary ----
rep("""/* The degree's total units is one line of the report: it's "N units to go", never a requirement to plan. */
const auditIsTotal = """, """/* (2026-10-11) A report line's GE area(s) in the app's semester vocabulary. The registrar's table
   (registrar.calpoly.edu/GE_2026): A1→1C, A2→1A, A3→1B, B1→5A, B2→5B, B3→5C, B4→2, B UD→UD 2/5, C1→3A, C2→3B,
   C UD→UD 3, D1→4A, D2→4B, D UD→UD 4, F→6; Area E is no longer offered — "an additional Area 4B course"; a
   lower-division C elective is any 3A or 3B; "GE Elective: Areas B, C, and D" is any of those areas. Semester
   lines that print no area code say it in words ("Area 3: Upper-division …", "(GE UD 2/5)"). [] = unknown. */
const GE_QTR = { A1: ['1C'], A2: ['1A'], A3: ['1B'], B1: ['5A'], B2: ['5B'], B3: ['5C'], B4: ['2'], BUD: ['U25'], C1: ['3A'], C2: ['3B'], CUD: ['UD3'], D1: ['4A'], D2: ['4B'], DUD: ['UD4'], E: ['4B'], F: ['6'],
  '1A': ['1A'], '1B': ['1B'], '1C': ['1C'], 2: ['2'], '3A': ['3A'], '3B': ['3B'], '4A': ['4A'], '4B': ['4B'], '5A': ['5A'], '5B': ['5B'], '5C': ['5C'], 6: ['6'], U25: ['U25'], UD3: ['UD3'], UD4: ['UD4'] };
function plGeArea(b) {
  if (!b || b.kind !== 'ge') return [];
  if (b.ge && GE_QTR[b.ge]) return GE_QTR[b.ge];
  const l = String(b.label || '').replace(/^GE\\s+/i, '');
  /* a line that is a major or support requirement which also counts for GE ("DEI Elective (GE UD 4)", "PSY 2240 (GE
     5B)") takes its own list, never "any UD 4 class" (review 2026-10-11) */
  if (/\\(\\s*GE\\b[^)]*\\)\\s*$/i.test(l)) return [];
  if (/^(?:Area\\s*2\\s*or\\s*5\\s*:\\s*(?:UD|Upper)|UD\\s*2\\s*\\/\\s*5\\b|Upper[- ]division (?:Scientific|Science|Math))/i.test(l)) return ['U25'];
  if (/^(?:Area\\s*3\\s*:\\s*(?:UD|Upper)|UD\\s*3\\b|Upper[- ]division Arts)/i.test(l)) return ['UD3'];
  if (/^(?:Area\\s*4\\s*:\\s*(?:UD|Upper)|UD\\s*4\\b|Upper[- ]division Social)/i.test(l)) return ['UD4'];
  if (/^Lower[- ]division C Elective\\b/i.test(l)) return ['3A', '3B'];
  if (/^Electives?\\b.*\\bAreas? B, C,? and D\\b/i.test(l)) return ['2', '5A', '5B', '5C', '3A', '3B', '4A', '4B'];
  return [];
}
/* (2026-10-11) What a new report changes against the one on the account: lines newly filled or newly open (matched
   by the line's code, else its words), lines the old report didn't have, and the plans holding a class that filled
   an open line before and fills none now (by class code; a GE area fill isn't traced). null = no report before. */
function auditDiff(old, a) {
  const O = old && old.reqs && old.reqs.length ? auditLines(old, null) : null;
  /* the new report as it will be stored (auditRow: the same trimmed words the old one was stored with) */
  const N = a && a.ok ? auditLines({ reqs: (a.reqs || []).filter(b => !b.flag).map(auditRow).filter(b => b.label || b.options.length), catalog: a.catalog || '', overrides: (old && old.overrides) || [] }, null) : null;
  if (!O || !N) return null;
  const k = c => (window.TCPL && TCPL.canon(c)) || c, done = b => b.status === 'satisfied' || b.status === 'in_progress';
  /* a line's key: its code, else its words and which of the same words it is (two "GE Elective" lines stay two) */
  const keys = X => { const n = {}; return new Map(X.live.map(b => { const w = b.code || b.label; n[w] = (n[w] || 0) + 1; return [b, w + '#' + n[w]]; })); };
  const kO = keys(O), kN = keys(N), was = new Map(O.live.map(b => [kO.get(b), b])), now = new Map(N.live.map(b => [kN.get(b), b]));
  const filled = N.live.filter(b => done(b) && was.has(kN.get(b)) && was.get(kN.get(b)).status === 'not').map(b => b.label);
  const opened = N.live.filter(b => b.status === 'not' && was.has(kN.get(b)) && done(was.get(kN.get(b)))).map(b => b.label);
  const added = N.live.filter(b => !was.has(kN.get(b))).length;
  /* a plan's class "is done now" only when the open line it filled is now Satisfied / In Progress on the new report */
  const doneNow = new Set(); O.open.forEach(b => { const nb = now.get(kO.get(b)); if (nb && done(nb)) (b.options || []).forEach(c => doneNow.add(k(c))); });
  const stillOpen = new Set(N.open.flatMap(b => b.options || []).map(k)), affected = {};
  AT_PLANS.forEach(P => { const codes = []; (TC.plans[P] || []).forEach(id => { const s = SEC[id]; if (s && doneNow.has(k(s.code)) && !stillOpen.has(k(s.code)) && !codes.includes(s.code)) codes.push(s.code); }); if (codes.length) affected[P] = codes; });
  return { filled, opened, added, affected, same: !filled.length && !opened.length && !added };
}
/* The degree's total units is one line of the report: it's "N units to go", never a requirement to plan. */
const auditIsTotal = """, 'geArea')
rep("""    if (!by && b.kind === 'ge' && b.ge) by = mine.find(c => (GE.get(k(c)) || []).includes(b.ge));""",
    """    /* (2026-10-11) by area: only a line the report put no class under, only a class the report placed nowhere, and
       one class for one line — Area E ("an additional 4B") is never covered by the 4B class D2 already has */
    if (!by && b.kind === 'ge' && !(b.used || []).length) { const areas = plGeArea(b); if (areas.length) by = mine.find(c => !placed.has(k(c)) && !spent.has(k(c)) && (GE.get(k(c)) || []).some(a => areas.includes(a))); }""", 'auditLines-area')
rep("""    covered.set(b, by);""", """    covered.set(b, by); spent.add(k(by));""", 'auditLines-spent')
# a quarter catalog's lines need QUARTER units; the app knows a class's semester units: ×1.5, as the registrar
# prints them on a quarter-catalog report (a 4-unit semester class prints 6.00, a 3-unit one 4.50 — read 2026-10-11)
rep("""    if (b.units && b.units.need != null && u != null && u < +b.units.need) return;""",
    """    if (b.units && b.units.need != null && u != null && (qtr ? u * 1.5 : u) < +b.units.need) return;""", 'auditLines-qtr-units')
rep("""  const live = a.reqs.filter(b => b && !b.flag), covered = new Map();""",
    """  const live = a.reqs.filter(b => b && !b.flag), covered = new Map(), qtr = /quarter/i.test(a.catalog || (TC.audit && TC.audit.catalog) || ''), spent = new Set(),
    placed = new Set(live.flatMap(b => (b.used || []).flatMap(e => [k(e.c), e.n ? k(e.n) : null])).filter(Boolean));""", 'auditLines-qtr')
rep("""  auditOpen.forEach(b => { (b.options || []).forEach(c => { (byClass[k(c)] = byClass[k(c)] || []).push(b); }); if (b.kind === 'ge' && b.ge) (byArea[b.ge] = byArea[b.ge] || []).push(b); });""",
    """  auditOpen.forEach(b => { (b.options || []).forEach(c => { (byClass[k(c)] = byClass[k(c)] || []).push(b); }); plGeArea(b).forEach(a => { (byArea[a] = byArea[a] || []).push(b); }); });""", 'planRank-area')
rep("""    if (b.kind === 'ge' && b.ge && rank[st] > (rank[ge[b.ge]] || 0)) ge[b.ge] = st;""",
    """    { const ar = plGeArea(b); if (ar.length === 1 && rank[st] > (rank[ge[ar[0]]] || 0)) ge[ar[0]] = st; }""", 'pcByReport-area')

# ---- Past classes: the report by requirement ----
rep("""function pcSummary(L) {
  const X = auditLines(TC.audit, L);
  /* (2026-10-11) with a report in, its count: filled of every line it prints (the Planner's count) */
  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L, { F, N }); }""",
    """function pcSummary(L, P) {
  const X = auditLines(TC.audit, L);
  /* (2026-10-11) with a report in, its count: filled of every line it prints (the Planner's count) — and the
     report's catalog, so a quarter-catalog student can see the app checks THAT, not the semester flowchart */
  if (X) { const F = X.filled.length, N = X.live.length; L = Object.assign({}, L || { major: (P || TC.profile || {}).major }, { F, N }); }
  const cat = X && TC.audit.catalog ? `<div class="pc-cat">Your catalog: ${esc(TC.audit.catalog)}${TC.audit.printed_on ? ' · report printed ' + esc(pcDate(TC.audit.printed_on)) : ''}</div>` : '';""", 'pcSummary-sig')
rep("""${X ? `<button class="pc-link" data-a="pcReport"><span>Degree Progress Report</span><em>${X.open.length} left</em>${pcChev()}</button>` : ''}${pick}</div>`;
}""", """${X ? `<button class="pc-link" data-a="pcReport"><span>Degree Progress Report</span><em>${X.open.length} left</em>${pcChev()}</button>` : ''}${cat}${pick}</div>`;
}
const pcDate = iso => { try { return new Date(iso + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); } catch (e) { return iso; } };
/* (2026-10-11) Past classes from the report: its own requirements, by group, each naming the class the report used.
   The report decides; the app only says what it read. */
const PC_GROUPS = [['major', 'Major and support'], ['conc', 'Concentration'], ['ge', 'General education'], ['degree', 'Degree requirements']];
const pcGroupOf = b => b.kind === 'ge' ? 'ge' : b.kind === 'conc' ? 'conc' : /^(units|gpa|gwr|uscp)$/.test(b.kind || '') ? 'degree' : 'major';
/* a used class's row on your record, by today's number and (when the record has one) the term */
function pcUsedRow(e) {
  const code = pcK(e.n || e.c), [t, y] = String(e.t || '').split(' ');
  const rows = (TC.myHistory || []).filter(h => pcK(h.code) === code || pcK(h.code) === pcK(e.c));
  return rows.find(h => h.term === t && String(h.year) === y) || (rows.length === 1 ? rows[0] : null);
}
function pcUsedLine(b, st) {
  const u = b.used || [];
  if (!u.length) return '';
  const parts = u.slice(0, 3).map(e => `<span class="pc-used">${esc(e.c)}${e.n && e.n !== e.c ? ` <i>→</i> ${esc(e.n)}` : ''}<em>${esc(e.t || '')}${e.x ? ' · transfer credit' : e.p ? ' · this term' : ''}</em></span>`);
  if (u.length > 3) parts.push(`<span class="pc-used"><em>+${u.length - 3} more</em></span>`);
  /* the professor line: the first Cal Poly class the report used that's on your record */
  const first = u.find(e => !e.x && !e.p), h = first ? pcUsedRow(first) : null;
  const prof = h && !pcXfer(h) ? (h.professor ? `<span class="pc-pf">${esc(h.professor)}</span>` : `<button class="pc-add" data-a="pcProf" data-x="${esc(pcKey(h))}" aria-label="Add the professor for ${esc(pcK(h.code))}">+ Professor</button>`) : '';
  return `<div class="pc-usedw">${parts.join('')}</div>${prof}`;
}
function pcReqRow(b, X, L, i) {
  const st = X.manual.has(b) ? 'done' : X.covered.has(b) ? 'taking' : b.status === 'satisfied' ? 'done' : b.status === 'in_progress' ? 'taking' : b.status === 'not' ? 'need' : 'cant';
  const c = CELL[st] || CELL.need, mine = X.manual.has(b);
  const one = (b.options || []).length === 1 ? b.options[0] : '', first = (b.used || []).find(e => !e.x), h = first ? pcUsedRow(first) : null;
  const areas = plGeArea(b);
  const act = st === 'done' && h ? `data-a="pcOpen" data-x="${esc(pcKey(h))}"` : st === 'need' && one && COURSES[pcK(one)] ? `data-a="openClass" data-x="${esc(pcK(one))}"` : st === 'need' && areas.length === 1 ? `data-a="plGe" data-x="${esc(areas[0])}"` : '';
  const sub = st === 'done' || st === 'taking' ? pcUsedLine(b, st)
    : st === 'need' ? `<span class="pc-pf">${esc([b.oneOf && (b.options || []).length > 1 ? 'pick one of ' + b.options.length : '', b.units && b.units.need ? auditNum(b.units.need) + (+b.units.need === 1 ? ' unit needed' : ' units needed') : b.courses && b.courses.need ? auditNum(b.courses.need) + (b.courses.need > 1 ? ' classes needed' : ' class needed') : ''].filter(Boolean).join(' · '))}</span>`
      + ((b.listed || []).length ? `<span class="pc-look">Needs a look: your report lists ${esc(b.listed.slice(0, 3).join(', '))} on your record but didn’t count ${b.listed.length > 1 ? 'them' : 'it'} here — ask your advisor</span>` : '')
    : `<span class="pc-pf">The app couldn’t read this line</span>`;
  const tag = mine ? '<span class="pc-pf tc-mine">Marked done by you</span>' : X.covered.has(b) && !(b.used || []).length ? `<span class="pc-pf">Taking ${esc(X.covered.get(b))} this term</span>` : '';
  const mark = st === 'need' && !auditIsTotal(b) ? `<button class="pc-mark" data-a="plMarkAsk" data-x="${i}">Mark done</button>` : mine ? `<button class="pc-mark" data-a="plUnmark" data-x="${i}">Undo</button>` : '';
  const main = `<span class="pc-nm pc-wrap">${esc(b.label)}</span>`;
  return `<div class="pc-row ${st}${(b.listed || []).length && st === 'need' ? ' look' : ''}"><span class="pc-dot ${st}" style="color:${c[1]};background:${c[2]}" role="img" aria-label="${c[3]}">${c[0]}</span><div class="pc-tx">${act ? `<button class="pc-main" ${act}>${main}</button>` : `<div class="pc-main">${main}</div>`}${auditTag(b) ? `<span class="pc-tags">${auditTag(b)}</span>` : ''}${sub}${tag}</div>${mark}</div>`;
}
function pcReportView(X, L) {
  UI.pcGroups = UI.pcGroups || {};
  const idx = new Map((TC.audit.reqs || []).map((b, i) => [b, i]));
  const still = X.open.concat(X.unknown, X.inprog.filter(b => !X.open.includes(b)));
  const stillCard = still.length ? `<div class="card pc-still"><div class="pc-hd"><span>Still needed</span><em>${X.open.length + X.unknown.length}</em></div>${still.map(b => pcReqRow(b, X, L, idx.get(b))).join('')}</div>`
    : `<div class="card pc-still pc-alldone"><div class="pc-hd"><span>Nothing left on your report</span></div></div>`;
  const groups = PC_GROUPS.map(([key, label]) => {
    const rows = X.live.filter(b => pcGroupOf(b) === key && !still.includes(b)); if (!rows.length) return '';
    const open = !!UI.pcGroups[key], lab = key === 'conc' && TC.audit.conc ? esc(TC.audit.conc) + ' concentration' : label;
    const head = `<button class="pc-year" data-a="pcGroup" data-x="${key}" aria-expanded="${open}" aria-label="${lab}, ${rows.length} filled"><span>${lab}</span><em>${rows.length} filled</em>${pcChev(open ? 90 : 0)}</button>`;
    return open ? `<div class="pc-open">${head}<div class="pc-term pc-grp">${rows.map(b => pcReqRow(b, X, L, idx.get(b))).join('')}</div></div>` : head;
  }).join('');
  /* classes on your record the report used for nothing (its "Free electives" — units only) */
  const usedK = new Set(X.live.flatMap(b => (b.used || []).flatMap(e => [pcK(e.c), e.n ? pcK(e.n) : null])).filter(Boolean));
  const rest = pcHist().filter(h => !usedK.has(pcK(h.code)));
  const unitsOnly = rest.length ? `<div class="card pc-oth"><div class="pc-hd"><span>Units only</span><em>${rest.length}</em></div><div class="muted b" style="font-size:12.5px;margin:-2px 0 6px">On your record, counted for no requirement</div>${(UI.pcAll ? rest : rest.slice(0, 4)).map(h => { const code = pcK(h.code); return `<div class="pc-orow"><div class="pc-tx"><button class="pc-main" data-a="pcOpen" data-x="${esc(pcKey(h))}"><span class="pc-cc">${esc(code)}</span><span class="pc-nm">${esc(courseName(code))}</span></button>${pcLine(code, 'done', h)}</div></div>`; }).join('')}${rest.length > 4 && !UI.pcAll ? `<button class="pc-more" data-a="pcAll">See all ${rest.length}</button>` : ''}</div>` : '';
  /* the flowchart years only when they're the student's own catalog (a semester one); a quarter catalog never sees them */
  const sem = /semester/i.test(TC.audit.catalog || '');
  const years = sem && L ? `<div class="pc-hd pc-fhd"><span>Your flowchart</span><em>2026–28</em></div>${pcYears(pcByReport(L, X))}` : '';
  return stillCard + groups + unitsOnly + years;
}""", 'pcReportView')
rep("""  const LR = pcByReport(L, auditLines(TC.audit, L));
  return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L) + pcYears(LR) + (none ? '' : pcOther(L) + pcBtns())}</div>`;
}""", """  const X = auditLines(TC.audit, L);
  /* (2026-10-11) the report is the truth: its requirements, not the flowchart's spots (those only for its own catalog).
     A report saved before this build kept no classes per line: the old screen, and a line asking for it again. */
  const fresh = X && X.live.some(b => Array.isArray(b.used));
  if (X && !fresh && L) return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L, P) + '<div class="pc-again">Upload your report again to see which class filled each requirement.</div>' + pcYears(pcByReport(L, X)) + (none ? '' : pcOther(L) + pcBtns())}</div>`;
  if (X) return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L, P) + pcReportView(X, L) + pcBtns()}</div>`;
  const LR = pcByReport(L, X);
  return (none ? dprFirstCard() : '') + `<div class="pc-pg">${pcSummary(L, P) + pcYears(LR) + (none ? '' : pcOther(L) + pcBtns())}</div>`;
}""", 'pastView')
rep("""  if (!L) return (none ? dprFirstCard() : '') + `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div><p class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">We don’t have this major’s flowchart yet, so we can’t check your requirements.</p></div>` + (none ? '' : `<div class="pc-pg">${pcOther(null) + pcBtns()}</div>`);""",
    """  /* no flowchart for this major: the report, when there is one, still says everything */
  if (!L && !auditLines(TC.audit, null)) return (none ? dprFirstCard() : '') + `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div><p class="muted b" style="font-size:14px;margin-top:6px;line-height:1.45">We don’t have this major’s flowchart yet, so we can’t check your requirements.</p></div>` + (none ? '' : `<div class="pc-pg">${pcOther(null) + pcBtns()}</div>`);""", 'pastView-noL')
rep("""  pcAll: () => { UI.pcAll = true; render(true); },""",
    """  pcAll: () => { UI.pcAll = true; render(true); },
  pcGroup: key => { UI.pcGroups = UI.pcGroups || {}; UI.pcGroups[key] = !UI.pcGroups[key]; render(true); },
  /* the sheet after a new report: take a class the report now says is done out of a plan — only on a tap */
  dprDrop: x => { const [P, code] = String(x).split('|'); const prev = (TC.plans[P] || []).slice(), next = prev.filter(id => !(SEC[id] && SEC[id].code === code)); if (next.length === prev.length) return; TC.setPlan(P, next); if (UI.sheet && UI.sheet.type === 'dprDiff' && UI.sheet.d && UI.sheet.d.affected[P]) { UI.sheet.d.affected[P] = UI.sheet.d.affected[P].filter(c => c !== code); if (!UI.sheet.d.affected[P].length) delete UI.sheet.d.affected[P]; } toast(`Removed ${code} from Plan ${P}`); render(true); },""", 'actions')
rep("""      UI.pl = null; UI.plRefresh = true;
      const who = pcWhoKeys(); UI.sheet = who.length ? { type: 'pcWho', keys: who } : null;""",
    """      UI.pl = null; UI.plRefresh = true;
      const who = pcWhoKeys(); UI.sheet = who.length ? { type: 'pcWho', keys: who } : null;
      /* a new report over an old one: what changed, and the plans it touches, before anything else */
      if (!e2 && UI.dprDiff && !UI.dprDiff.same) UI.sheet = { type: 'dprDiff', d: UI.dprDiff, ret: UI.sheet };
      else if (!e2 && UI.dprDiff && UI.dprDiff.same) notes.push('Your report says the same as before.');
      UI.dprDiff = null;""", 'dprSave-diff')
rep("""SHEETS.dprRead.full = true; SHEETS.dprRead.label = 'Report read';""",
    """SHEETS.dprRead.full = true; SHEETS.dprRead.label = 'Report read';
/* (2026-10-11) What a new report changed. Plans still as drafted were re-drafted; a plan the student made is only
   offered the change. */
SHEETS.dprDiff = sh => {
  const d = sh.d || {}, aff = Object.keys(d.affected || {});
  const li = (t, k) => `<div class="pc-orow"><div class="pc-tx"><div class="pc-main"><span class="pc-nm pc-wrap">${esc(t)}</span></div>${k ? `<span class="pc-pf">${esc(k)}</span>` : ''}</div></div>`;
  return `<div class="row sb"><h3>Your report changed</h3>${pcX()}</div>
  ${d.filled.length ? `<div class="pc-hd" style="margin-top:8px"><span>Now filled</span><em>${d.filled.length}</em></div>${d.filled.slice(0, 8).map(t => li(t)).join('')}` : ''}
  ${d.opened.length ? `<div class="pc-hd" style="margin-top:8px"><span>Open again</span><em>${d.opened.length}</em></div>${d.opened.slice(0, 8).map(t => li(t)).join('')}` : ''}
  ${d.added ? `<div class="muted b" style="font-size:13px;margin-top:8px">${d.added} line${d.added === 1 ? '' : 's'} this report prints that the last one didn’t.</div>` : ''}
  ${aff.length ? `<div class="pc-hd" style="margin-top:12px"><span>Your plans</span></div><div class="muted b" style="font-size:13px;margin-bottom:6px">These classes filled something you needed before. Your report now says that’s done.</div>${aff.map(P => d.affected[P].map(code => `<div class="pc-orow" style="display:flex;align-items:center;gap:10px"><span class="grow b" style="font-size:14.5px">Plan ${esc(P)} · ${esc(code)}</span><button class="pc-mark" data-a="dprDrop" data-x="${esc(P + '|' + code)}">Take it out</button></div>`).join('')).join('')}` : ''}
  <button class="btn" style="width:100%;margin-top:16px" data-a="closeSheet">Done</button>`;
};""", 'dprDiff-sheet')

# the Planner with no flowchart for the major: the report can still be uploaded (Past classes shows it whole)
rep("""  const { L, P } = g;
  if (!L) return `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div>""",
    """  const { L, P } = g;
  if (!L) return (plNoRecord() && !TC.audit && !plSkipped() ? dprFirstCard() : '') + `<div class="card tc-sec" style="margin-top:14px"><div class="b" style="font-size:17px">${esc(P.major)}</div>""", 'planner-noL')

rep("""    if (UI.sheet && (UI.sheet.type === 'pcProf' || UI.sheet.type === 'pcTerm') && UI.sheet.ret) { pcBack(UI.sheet); render(true); return; }""",
    """    if (UI.sheet && (UI.sheet.type === 'pcProf' || UI.sheet.type === 'pcTerm' || UI.sheet.type === 'dprDiff') && UI.sheet.ret) { pcBack(UI.sheet); render(true); return; }""", 'closeSheet-ret')

# ---- CSS ----
rep(""".pc-btns{display:flex;gap:8px;margin-top:14px}""",
    """.pc-btns{display:flex;gap:8px;margin-top:14px}
.pc-cat{font-size:12.5px;font-weight:800;color:var(--muted);margin-top:10px}
.pc-still{margin-top:14px;padding:10px 12px 8px;box-shadow:inset 0 0 0 2px var(--amber-wash)}
.pc-still .pc-hd{padding:0 4px 6px}
.pc-still .pc-row{background:var(--bg)}
.pc-still .pc-row + .pc-row{margin-top:6px}
.pc-alldone{box-shadow:inset 0 0 0 2px var(--ok-soft)}
.pc-grp{margin-top:0}
.pc-wrap{white-space:normal;line-height:1.3}
.pc-tags{display:flex;gap:6px;margin:-2px 0 4px}
.pc-usedw{display:flex;flex-direction:column;gap:2px;margin:-4px 0 6px}
.pc-used{font-size:13px;font-weight:800;color:var(--ink4);display:flex;flex-wrap:wrap;gap:0 6px}
.pc-used i{font-style:normal;color:var(--muted2)}
.pc-used em{font-style:normal;font-weight:700;color:var(--muted)}
.pc-usedw + .pc-pf,.pc-usedw + .pc-add{margin-top:-4px}
.pc-look{display:block;font-size:12.5px;font-weight:800;color:var(--amber-ink);margin:-2px 0 8px;line-height:1.35}
.pc-row.look{box-shadow:inset 0 0 0 2px var(--amber-wash)}
.pc-mark{flex:none;font-size:12.5px;font-weight:900;color:var(--blue-ink);background:var(--blue-soft);border-radius:999px;padding:0 10px;min-height:32px;align-self:center}
.pc-fhd{margin-top:16px;padding:0 4px}
.pc-again{margin-top:10px;padding:10px 14px;border-radius:14px;background:var(--blue-soft);color:var(--blue-ink);font-size:13.5px;font-weight:800;line-height:1.4}""", 'css')

open(PA, 'w', encoding='utf-8').write(S)
print('dpr-truth-app: done')
