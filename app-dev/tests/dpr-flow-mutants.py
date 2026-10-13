#!/usr/bin/env python3
"""Writes the report → Planner → Plans flow's mutants into mutate.mjs (between the section's comment and the next
section), after checking that every anchor occurs exactly once in the built app (app-dev/out/app/…).
Usage (app-dev/tests): python3 dpr-flow-mutants.py"""
import json, os, sys
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'app')
HTML = open(os.path.join(OUT, 'index.html'), encoding='utf-8').read()
PL = open(os.path.join(OUT, 'planner.js'), encoding='utf-8').read()
P = 'planner'
M = [
  # the reader (planner.js)
  ("audit: a group (RG) counted", "    if(b.level==='RG')return;\n    if(b.level==='RQ'){", "    if(b.level==='RG'){ b.atomic=true; return; }\n    if(b.level==='RQ'){", "dprAudit", P),
  ("audit: a requirement with lines counted too", "      if(!kids.length){ b.atomic=true; return; }", "      b.atomic=true; if(!kids.length){ return; }", "dprAudit", P),
  ("audit: 1 of N Options counted per option", "if(b.oneOf||(opt.length&&opt.length===kids.length)){", "if(false){", "dprAudit", P),
  ("audit: words with an ID kept as a label", "  if(/\\d{7,}|EMPLID|Name\\s*:/i.test(t)||DPR_GRADEUNITS.test(t)) return '';", "  if(false) return '';", "dprAudit", P),
  ("audit: a bare number doesn't take the subject before it", "    else if(!subj) continue;", "    else continue;", "dprAudit", P),
  ("audit: units needed not read", "if(u){ var c3=dprCounts3(u[2]); if(/^units/i.test(u[1]))cur.units=c3; else cur.courses=c3; lastEnd=k; continue; }", "if(u){ lastEnd=k; continue; }", "dprAudit", P),
  ("audit: a wrapped verdict not joined", "while(!done(words)&&j+1<end&&extra<(NEW?6:3)){", "while(false){", "dprAudit", P),
  ("audit: 2026 layout named by the verdict's note", "      var src=head||words;", "      var src=words;", "dprAudit", P),
  ("audit: 2026 layout closes a block on 'required'", "var done=NEW?function(w){ return DPR_RCODE.test(w); }:", "var done=NEW?function(w){ return DPR_RCODE.test(w)||/required\\s*$/i.test(w); }:", "dprAudit", P),
  ("audit: mixed option lines counted per option", "      if(opt.length){", "      if(false){", "dprAudit", P),
  ("audit: dprParse drops the verdicts", "return {ok:true, rows:out, program:prog, skipped:skipped, audit:audit,", "return {ok:true, rows:out, program:prog, skipped:skipped, audit:null,", "dprAudit", P),
  ("taking now: a class being taken doesn't make its line in progress", "  blocks.forEach(function(b){ if(b.status==='not'&&inNow(b))b.status='in_progress'; });", "", "dprTakingNow", P),
  ("taking now: the class's units not weighed against what's needed", "if(b.units&&b.units.need!=null&&b.units.need>0){", "if(false){", "dprTakingNow", P),
  ("taking now: the code after the advice sentence lost", "      if(!NEW&&!DPR_RCODE.test(words)){", "      if(false){", "dprTakingNow", P),
  ("edges: a label with the student's name kept", "      if(hasWho(b.label)||hasWho(src))b.label='';\n", "", "dprAudit", P),
  ("edges: the repeated page header read into a verdict", "|Degree Progress Report\\s*$|For\\s)/i;", ")/i;", "dprAudit", P),
  ("edges: a course row's tail taken as a heading", "||DPR_GRADEUNITS.test(s)||hasWho(s))return '';", ")return '';", "dprAudit", P),
  ("edges: a requirement's own Not Satisfied dropped", "if(b.status==='not'&&!b.oneOf&&!kids.some(function(x){ return x.status!=='satisfied'; })){", "if(false){", "dprAudit", P),
  ("taking now: any term's row counts as being taken", "return !!(now[c+'|'+term]||(k&&now[k+'|'+term]));", "return Object.keys(now).some(function(x){ var y=x.split('|')[0]; return y===c||y===k; });", "dprTakingNow", P),
  ("taking now: a line with no counts settled by one class", "    if(!b.courses&&!b.units&&!(b.kind==='gwr'||b.kind==='uscp'||b.options.length===1))return false;\n", "", "dprTakingNow", P),
  ("taking now: a line borrows a kind from another section's requirement", "ctx=own?((req&&req.label)||''):'';", "ctx=(req&&req.label)||'';", "dprTakingNow", P),
  ("edges: any line starting 'For' read as the name", "if(fm&&wi-lastTitle<=2)addWho(fm[1]);", "if(/^For\\s/.test(wl))addWho(wl.slice(4));", "dprAudit", P),
  ("taking now: dprParse doesn't pass the classes being taken", "audit=dprAudit(text, cross, taking);", "audit=dprAudit(text, cross, []);", "dprTakingNow", P),
  # Report read, Check, the save
  ("flow: tabs — Planner after Past classes again", "['plans', 'Plans'], ['planner', 'Planner'], ['past', 'Past classes']", "['plans', 'Plans'], ['past', 'Past classes'], ['planner', 'Planner']", "tabsOrder"),
  ("read: the pills count the flowchart even with the report's verdicts", "  if (X) return { filled: X.filled.length, left: X.open.length, unknown: X.unknown.length, xfer, src: 'report' };", "  if (false) return { filled: 0 };", "dprRead"),
  ("read: the report's plan code shown as the major", "const major = dprMajorShown(prog), yr", "const major = prog.major || P.major || '', yr", "dprRead"),
  ("read: the old checkbox list is back", "<div class=\"dr-mid\">${dprPage()}<div class=\"dr-pills\">", "<div class=\"dr-mid\">${dprPage()}<label class=\"tc-dprrow\"><input type=\"checkbox\"></label><div class=\"dr-pills\">", "dprRead"),
  ("read: no way to check what was read", "<button class=\"dr-link\" data-a=\"dprCheck\">Check what was read</button>", "", "dprRead"),
  ("read: the transfer pill counts flagged rows", "xfer = (r && r.rows || []).filter(x => x._xfer && !x.flag).length;", "xfer = (r && r.rows || []).filter(x => x._xfer).length + 1;", "dprRead"),
  ("read: a line you're taking a class for still counts as left", "  const open = live.filter(b => b.status === 'not' && !covered.has(b) && !manual.has(b));", "  const open = live.filter(b => b.status === 'not' && !manual.has(b));", "dprRead"),
  ("check: a flag doesn't strike the line", ".dr-row.flagged .dr-lab,.dr-row.flagged .dr-u{text-decoration:line-through;color:var(--muted)}", ".dr-row.flagged .dr-lab,.dr-row.flagged .dr-u{color:var(--muted)}", "dprRead"),
  ("check: a flagged line is still saved", "const reqs = (a && a.ok && a.reqs ? a.reqs : []).filter(b => !b.flag).map(auditRow)", "const reqs = (a && a.ok && a.reqs ? a.reqs : []).map(auditRow)", "dprRead"),
  ("check: a flag carries the user id", "const row = { who_hash: '', major:", "const row = { who_hash: '', user_id: TC.user.id, major:", "dprRead"),
  ("save: a note rides along in the audit row", "options: (b.options || []).filter(c => /^[A-Z]{2,5} \\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf };", "options: (b.options || []).filter(c => /^[A-Z]{2,5} \\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf: !!b.oneOf, note: String(b.note || '') };", "dprRead"),
  ("save: words with an ID stored", "  return { label: DPR_PII.test(label) ? '' : label,", "  return { label: label,", "dprAudit"),
  ("save: anything stored as a class code", "options: (b.options || []).filter(c => /^[A-Z]{2,5} \\d{3,4}[A-Z]{0,2}$/.test(c)).slice(0, 60), oneOf", "options: (b.options || []).slice(0, 60), oneOf", "dprAudit"),
  ("save: the report's units not saved", "units_used: num(a && a.units_used), units_needed: num(a && a.units_needed),", "units_used: null, units_needed: null,", "dprRead"),
  ("save: See my plan stays put", "      S.tab = 'schedule'; S.schedTab = 'planner'; save();\n    } catch (err)", "      save();\n    } catch (err)", "dprFromProfile"),
  ("save: the old error stays after a retry", "r.saveErr = null; UI.busy.dpr = 1; render(true);", "UI.busy.dpr = 1; render(true);", "dprRead"),
  ("save: a throw leaves the button busy", "    finally { UI.busy.dpr = 0; if (notes.length)", "    finally { if (notes.length)", "dprSaveThrows"),
  ("empty: no laptop link on the upload card", "<button class=\"tc-dpr-link\" data-a=\"plLaptop\" ${UI.busy.laptop ? 'disabled' : ''}>${UI.busy.laptop ? 'Sending…' : 'Send the link to my laptop'}</button>", "", "dprRead"),
  ("wrong: no way to try another PDF", "<div class=\"dr-foot\"><label class=\"btn\" style=\"cursor:pointer\">Try another PDF<input type=\"file\" accept=\"application/pdf,.pdf\" data-in=\"dprfile\" hidden></label></div>", "", "dprWrong"),
  # What matters most
  ("prefs: tapping an answer doesn't move it", "  plPrefPick: k => { if (UI.sheet && UI.sheet.type === 'plPrefs' && PREF_ORDER[k]) { UI.sheet.pick = k; render(true); } },", "  plPrefPick: k => { render(true); },", "plannerPrefs"),
  ("prefs: the first ask can be dismissed", "closeSheet: () => { if (UI.sheet && UI.sheet.type === 'plPrefs' && !TC.prefs) return;", "closeSheet: () => {", "plannerPrefs"),
  ("prefs: a close button on the first ask", "${TC.prefs ? `<button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button>` : ''}</div>\n  <div class=\"muted b\" style=\"font-size:14px;margin:2px 0 12px\">Your plan is built around it.</div>", "<button class=\"xbtn\" data-a=\"closeSheet\" aria-label=\"Close\">${ic('x', 16, 2.4)}</button></div>\n  <div class=\"muted b\" style=\"font-size:14px;margin:2px 0 12px\">Your plan is built around it.</div>", "plannerPrefs"),
  ("prefs: units ignored", "units = Math.min(20, Math.max(12, +units || 16));", "units = 16;", "plannerPrefs"),
  ("prefs: not kept on the phone", "  try { localStorage.setItem(PREFS_KEY(), JSON.stringify({ priority, units })); } catch (e) {}\n", "", "plannerPrefs"),
  ("prefs: Edit pins the saved answer over a tap", "const cur = sh.pick || (TC.prefs && TC.prefs.priority) || 'degree'", "const cur = (TC.prefs && TC.prefs.priority) || sh.pick || 'degree'", "plannerPrefs"),
  ("prefs: the ask never comes back", "  if (TC.prefs || UI.sheet || UI.plPrefsT) return;", "  return;", "plannerPrefs"),
  ("prefs: new answers don't re-draft", "    if (before && (before.priority !== TC.prefs.priority || before.units !== TC.prefs.units)) UI.plRefresh = true;\n", "", "plannerPrefs"),
  # drafting
  ("draft: a drafted plan is shared with friends", "  if (!was.length) TC.planShared[k] = false;", "", "plannerPrefs"),
  ("draft: drafted sections get seat alerts", "  if (inP && !w && SEC[id] && !draftOnly(id)) {", "  if (inP && !w && SEC[id]) {", "plannerPrefs"),
  ("draft: a changed plan re-drafted too", "  const redo = AT_PLANS.filter(k => plUntouched(k, d));", "  const redo = AT_PLANS.slice();", "plannerRefresh"),
  ("draft: drafted into plans that didn't load", "const plCanDraft = () => !!TC.plansLoaded && !TC.err.plans && !!TC.seatsLoaded && (", "const plCanDraft = () => !!TC.seatsLoaded && (", "plannerNoDraft"),
  ("draft: a loaded read never says so", "TC.plans = { A: [], B: [], C: [] }; TC.plansLoaded = true;", "TC.plans = { A: [], B: [], C: [] };", "plannerNoDraft"),
  ("draft: drafted with no record and no report", "  if (data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);", "  if (UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);", "plannerNoDraft"),
  ("draft: drafted without prerequisites", "  if (data && UI.pl.prereqs !== false && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);", "  if (data && plCanDraft() && plAutoDraft(R, L)) R = planRank(L);", "plannerNoDraft"),
  ("draft: a new report doesn't refresh the drafts", "      UI.pl = null; UI.plRefresh = true;\n      const who", "      UI.pl = null;\n      const who", "plannerRefresh"),
  ("draft: Draft it for me drafts every plan", "    const n = plDraftSlot(k, planRank(g.L), g.L);", "    const n = (AT_PLANS.forEach(x => plDraftSlot(x, planRank(g.L), g.L)), 1);", "plannerExistingPlan"),
  ("draft: a student's own plans drafted over", "    if (AT_PLANS.some(k => (TC.plans[k] || []).length)) { plDraftedSet({ own: true, at: Date.now() }); return false; }\n", "", "plannerExistingPlan"),
  ("draft: a clashing section can be the pick", "  if (strict) ss = ss.filter(s => !clash(s));\n", "", "plannerRules"),
  ("draft: units target +1 again", "    if (u != null && units + u > target) continue;", "    if (u != null && units + u > target + 1) continue;", "plannerRules"),
  ("draft: no class cap", "    if (units >= target || chosen.length + regN >= cap) break;", "    if (units >= target) break;", "plannerRules"),
  ("draft: B keeps a clashing section of A's", "    if (!pick && fits(s)) pick = s;\n    if (!pick) return;", "    if (!pick) pick = s;", "plannerRules"),
  ("draft: a pick-1 line gets two classes", "    if (c.fills && c.fills.length && c.fills.every(b => (got.get(b) || 0) >= room(b))) continue;\n", "", "plannerFromReport"),
  ("draft: two classes for one requirement", "    if ((keys[c.key] && !(c.fills && c.fills.some(b => (got.get(b) || 0) < room(b)))) || codes[c.code]) continue;", "    if (codes[c.code]) continue;", "plannerRules"),
  ("draft: a line needing two gets one", "    if ((keys[c.key] && !(c.fills && c.fills.some(b => (got.get(b) || 0) < room(b)))) || codes[c.code]) continue;", "    if (keys[c.key] || codes[c.code]) continue;", "plannerRules"),
  ("draft: the plans not read again before the first draft", "    if (UI.plFresh !== 'done') {", "    if (false) {", "plannerNoDraft"),
  ("draft: drafted again on every visit", "  if (!refresh) return false;\n", "", "plannerPlan"),
  ("draft: what was drafted isn't remembered", "  d[k] = ids; d.at = d.at || Date.now(); plDraftedSet(d);", "", "plannerPlan"),
  # the plan card and picks
  ("plan: Plan B's card says Best fit", "const PL_NAME = { A: 'Best fit', B: 'Backup', C: 'Friends' };", "const PL_NAME = { A: 'Best fit', B: 'Best fit', C: 'Friends' };", "plannerPlan"),
  ("plan: the switch doesn't switch", "  plShowPlan: k => { if (/^[ABC]$/.test(k)) UI.plPlan = k; render(true); },", "  plShowPlan: k => { render(true); },", "plannerPlan"),
  ("plan: Edit opens My Classes", "  plEditPlan: k => { if (/^[ABC]$/.test(k)) S.plan = k; S.schedTab = 'plans'; save(); render(); },", "  plEditPlan: k => { if (/^[ABC]$/.test(k)) S.plan = k; S.schedTab = 'mine'; save(); render(); },", "plannerPlan"),
  ("plan: “Behind” is back", "if (c.behind) return { t: 'Catch up', k: 't-amber',", "if (c.behind) return { t: 'Behind', k: 't-red',", "plannerPlan"),
  ("plan: seats count before registration opens", "const seat = !regOpen() ? 0 : openN >= 10 ? 5 : open ? 3 : waits ? 1 : 0;", "const seat = openN >= 10 ? 5 : open ? 3 : waits ? 1 : 0;", "plannerPlan"),
  ("plan: seat chips before registration opens", "${regOpen() ? ' · ' + secSeatText(x) : ''}</span></span>${right}", "${' · ' + secSeatText(x)}</span></span>${right}", "plannerPlan"),
  ("plan: Why sheet without the Seats part", ", ['seat', 'Seats', 5, '#475569']];", "];", "plannerPlan"),
  ("plan: the score isn't the sum of its parts", "const parts = { req, urg, prof, fr: frP, seat }, score = req + urg + prof + frP + seat;", "const parts = { req, urg, prof, fr: frP, seat }, score = req + urg + prof + frP + seat + 1;", "plannerPlan"),
  ("plan: Edit Plan says the wrong plan", "data-a=\"plEditPlan\" data-x=\"${k}\">Edit Plan ${k}</button>", "data-a=\"plEditPlan\" data-x=\"${k}\">Edit Plan A</button>", "plannerPlan"),
  ("plan: no “Only you” on a private plan", "TC.planShared[k] === false ? 'Only you' : ''", "''", "plannerPrefs"),
  ("plan: the footnote doesn't say drafts are private", "Drafted plans are only yours until you share them. ", "", "plannerFromReport"),
  # ranking
  ("rules: a year behind worth nothing", "const urg = Math.min(30, Math.min(24, behind * 12) +", "const urg = Math.min(30, Math.min(24, behind * 0) +", "plannerRules"),
  ("rules: the first priority not weighted", "const W = opt.weights || plWeights(), frX = opt.friendsX || 1;", "const W = { degree: 1, professors: 1, friends: 1 }, frX = opt.friendsX || 1;", "plannerRules"),
  ("rules: the best section ignores the professor before registration", "const tier = s => (regOpen() ? (s.status === 'full' ? 0 : s.status === 'wait' ? 2 : 4) : 4) + (clash(s) ? 0 : 1);", "const tier = s => (s.status === 'full' ? 0 : s.status === 'wait' ? 2 : 4) + (clash(s) ? 0 : 1);", "plannerRules"),
  ("rules: a plan while prerequisites load", "  if (preWait) return `<div class=\"pl-top\"><div>${term}</div></div>` + loadingCard('Checking prerequisites…');", "  if (false) return '';", "plannerRules"),
  # from the report
  ("report: the flowchart used even with a report", "const X = auditLines(TC.audit, L), audit = X ? TC.audit : null", "const X = null, audit = null", "plannerFromReport"),
  ("report: a pick-1 line worth a required class", "(b.oneOf || (b.courses && b.courses.req === 1 && (b.options || []).length > 1)) ? 8 : b.kind === 'elective' ? 2 : 10;", "(b.oneOf || (b.courses && b.courses.req === 1 && (b.options || []).length > 1)) ? 10 : b.kind === 'elective' ? 2 : 10;", "plannerFromReport"),
  ("report: “left” counts every line", "const left = X ? X.open.length : L.need.length + L.needU.length;", "const left = X ? X.live.length : L.need.length + L.needU.length;", "plannerFromReport"),
  ("report: Still need lists the flowchart", "${concCard}${R.audit ? auditNeedCard(R.X) : stillNeedCard(L)}", "${concCard}${stillNeedCard(L)}", "plannerFromReport"),
  ("report: a class you're taking doesn't cover its line", "    covered.set(b, by);\n", "", "plannerFromReport"),
  # everything filled
  ("done: a plan drafted with nothing open", "  if (R.done) return", "  if (false) return", "plannerDone"),
  ("done: a line the app can't check still says all filled", "const allDone = X ? (!X.open.some(b => !auditIsTotal(b)) && !X.unknown.length)", "const allDone = X ? (!X.open.some(b => !auditIsTotal(b)))", "plannerDone"),
  ("done: the flowchart's unknowns ignored", ": (!L.need.length && !L.needU.length && !L.cant.length && !L.concUnchosen);", ": (!L.need.length && !L.needU.length);", "plannerDone"),
  ("done: the total units line blocks “all filled”", "const auditIsTotal = b => !!b && b.kind === 'units' && /total units|units for the degree/i.test(b.label || '');", "const auditIsTotal = b => false;", "plannerDone"),
  ("done: a fun class already taken still offered", "!doneSet.has(k(f.code)) && !mineSet.has(k(f.code)) && preOk(f.code)", "preOk(f.code)", "plannerDone"),
  ("done: a fun class with no section shown", "FUN_CLASSES.filter(f => COURSES[f.code] && secsOf(f.code).length && ", "FUN_CLASSES.filter(f => true && ", "plannerDone"),
  ("done: units to go invented", "`${auditNum(tot.units.need)} units to go` : '';", "`99 units to go` : '99 units to go';", "plannerDone"),
  # registration
  ("reg: the term in session treated as not open", "const regOpen = () => CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || (", "const regOpen = () => (", "plannerRegOpen"),
  ("reg: the registration line for any term", "  if (regOpen() || CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return '';", "  if (!CFG.REGISTRATION_OPENS) return '';", "plannerRegOpen"),
  ("reg: the registration line stays once it opens", "  if (regOpen() || CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return '';", "  if (CFG.TERM_LABEL !== CFG.REGISTRATION_TERM || !CFG.REGISTRATION_OPENS) return '';", "plannerRegOpen"),
  # Plans tab
  ("plans: no diff line on B", "${planDiffLine(S.plan) ? `<span class=\"pl-diff\">${esc(planDiffLine(S.plan))}</span>` : ''}", "", "plansDiffLine"),
  ("plans: a swapped section not counted", "swapped = b.filter(s => ac.has(s.code) && !aid.has(String(s.id))).length;", "swapped = 0;", "plansDiffLine"),
  # Mark done
  ("mark: no Mark done button", "${i >= 0 && b.status === 'not' ? `<button class=\"pl-mark\" data-a=\"plMarkAsk\" data-x=\"${i}\">Mark done</button>` : ''}", "", "plannerMarkDone"),
  ("mark: a marked line still counts as left", "  const ovs = auditOverrides(), manual = new Set(", "  const ovs = [], manual = new Set(", "plannerMarkDone"),
  ("mark: a new upload forgets what was marked", "    overrides: (TC.audit && Array.isArray(TC.audit.overrides)) ? TC.audit.overrides : [] };", "    overrides: [] };", "plannerMarkDone"),
  ("mark: Undo does nothing", "    let e; try { e = await TC.saveOverrides(auditOverrides().filter(o => !auditOvMatch(o, b))); }", "    let e; try { e = null; }", "plannerMarkDone"),
  ("mark: Mark done offered on a line the app couldn't read", "${i >= 0 && b.status === 'not' ? `<button class=\"pl-mark\"", "${i >= 0 ? `<button class=\"pl-mark\"", "plannerMarkDone"),
  ("mark: a failed read blanks the marks on a new upload", "const up = Object.assign({}, row); if (!TC.auditLoaded) delete up.overrides;", "const up = Object.assign({}, row);", "plannerMarkDone"),
  ("mark: a mark made offline never goes up", "    if (c && c.ovPending && Array.isArray(c.overrides)) { TC.audit.overrides = c.overrides; TC.saveOverrides(c.overrides); } }", " }", "plannerMarkDone"),
  ("pending: a re-pushed read blanks the account's marks", "    if (!c.ovPending) { delete up.overrides;", "    if (!c.ovPending) {", "dprPendingPush"),
  ("mark: marked without asking", "  plMarkAsk: i => { if (TC.audit && TC.audit.reqs[+i]) { UI.sheet = { type: 'plMark', i: +i }; render(true); } },", "  plMarkAsk: i => { UI.sheet = { type: 'plMark', i: +i }; A.plMarkDo(); },", "plannerMarkDone"),
  # onboarding
  ("onboarding: the report back before confirm", "    <button type=\"button\" class=\"ghost pink\" data-a=\"onbStep\" data-x=\"confirm\">${n ? 'Next' : 'Skip for now'}</button></div></div>`;", "    <button type=\"button\" class=\"ghost pink\" data-a=\"onbStep\" data-x=\"degree\">${n ? 'Next' : 'Skip for now'}</button></div></div>`;", "onbReportLast"),
  ("onboarding: People goes to the payoff, skipping the report", "    <div class=\"foot\"><button type=\"button\" class=\"btn\" data-a=\"onbStep\" data-x=\"degree\">Continue</button></div></div>`;\n}\n/* 11 — friends only", "    <div class=\"foot\"><button type=\"button\" class=\"btn\" data-a=\"onbStep\" data-x=\"payoff\">Continue</button></div></div>`;\n}\n/* 11 — friends only", "onbReportLast"),
  ("onboarding: a first-year asked to upload anyway", "const firstYearEmpty = standing => standing === 'Freshman' && !!CFG.TERM_ENDS && sloISO() <= CFG.TERM_ENDS && !(TC.myHistory || []).length;", "const firstYearEmpty = standing => false;", "onbReportLast"),
  ("onboarding: the laptop link sends nothing", "  const r = await TC.requestPlannerLink(); UI.busy.laptop = 0;", "  const r = { to: 'me***@calpoly.edu' }; UI.busy.laptop = 0;", "onbReportLast"),
  ("onboarding: the laptop toast says it's already sent", "`We’ll email the link to ${r.to} within 5 minutes — open it on your laptop`", "`Sent to ${r.to}`", "onbReportLast"),
  ("onboarding: the upload leaves onboarding open", "  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho') && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null);", "  if (false) { onbRemember(null);", "onbReportLast"),
  ("onboarding: a choice slot passed off as one class", "const opts = (s.choice && s.choice.length > 1) ? s.choice : (s.codes && s.codes.length > 1) ? s.codes : null,", "const opts = null,", "onbReportLast"),
  # account deletion
  ("delete: the report, the answers and the drafts stay on the phone", ", AUDIT_KEY(), PREFS_KEY(), PLDRAFT_KEY(), plSkipKey(), MARKS_KEY()].forEach", ", MARKS_KEY()].forEach", "deleteAccount"),
]
bad = 0
for m in M:
    src = PL if len(m) > 4 and m[4] == P else HTML
    n = src.count(m[1])
    if n != 1: print(f'ANCHOR {n}x: {m[0]}'); bad += 1
if bad: sys.exit(1)
lines = ['  /* the report → Planner → Plans flow (2026-10-08; written by dpr-flow-mutants.py, anchors checked) */']
for m in M: lines.append('  ' + json.dumps(list(m), ensure_ascii=False) + ',')
MJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mutate.mjs')
s = open(MJ, encoding='utf-8').read()
i0 = s.index('  /* the report → Planner → Plans flow (2026-10-08')
i1 = min(x for x in (s.find('  /* Champ\'s own menu and the golden set (2026-10-08) */', i0), s.find('  /* a phone never gets the desktop frame (2026-10-06) */', i0)) if x > 0)
s = s[:i0] + '\n'.join(lines) + '\n' + s[i1:]
open(MJ, 'w', encoding='utf-8').write(s)
print(f'{len(M)} mutants written')
