#!/usr/bin/env python3
"""Mutants for Past classes, option A simple (2026-10-10), on 23:30. Each names ONE test. Checks every anchor matches once in the
built app (app-dev/out), then writes them into mutate.mjs just before the list closes. Replayable."""
import os, sys, json
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, '..', 'out', 'app')
html = open(os.path.join(OUT, 'index.html'), encoding='utf-8').read(); pl = open(os.path.join(OUT, 'planner.js'), encoding='utf-8').read()
M = [
 ("past: a GE spot doesn't name its class", "          if (uc.done[sl.id]) { row.f++; cell.state = 'done'; if (uc.with && uc.with[sl.id]) cell.fill = uc.with[sl.id]; }", "          if (uc.done[sl.id]) { row.f++; cell.state = 'done'; }", 'pastSimple', 'planner'),
 ("past: + Professor on transfer credit", "  if (pcXfer(h)) return '';\n  return h.professor ?", "  return h.professor ?", 'pastSimple', None),
 ("past: a waiver's reason isn't shown", "return w ? `<span class=\"pc-pf\">${esc(TCPL.waiveLabel(TC.waived[w]))}</span>` : ''; }", "return ''; }", 'plannerGrid', None),
 ("past: taking now asks for a professor", "  if (state === 'taking') { const s = nowSecs('me')", "  if (0) { const s = nowSecs('me')", 'pastSimple', None),
 ("past: other classes all at once", "  const show = UI.pcAll ? rows : rows.slice(0, 4);", "  const show = rows;", 'pastSimple', None),
 ("past: placed classes repeated under Other", "  if (L) L.grid.forEach(t => t.slots.forEach(s => { if ((s.state === 'done' || s.state === 'taking') && (s.fill || s.by)) used.add(pcK(s.fill || s.by)); }));", "", 'pastSimple', None),
 ("past: no report row", "${X ? `<button class=\"pc-link\" data-a=\"pcReport\">", "${0 ? `<button class=\"pc-link\" data-a=\"pcReport\">", 'pastSimple', None),
 ("past: the bar is always full", "<i style=\"width:${pct}%\"></i></div>${X ?", "<i style=\"width:100%\"></i></div>${X ?", 'planner', None),
 ("past: years count can't-check spots", "judged = slots.filter(s => s.state !== 'cant').length;\n    const open = UI.plYears[y.year] !== undefined ? UI.plYears[y.year] : y.year === firstOpen;\n    const head = `<button class=\"pc-year\"", "judged = slots.length;\n    const open = UI.plYears[y.year] !== undefined ? UI.plYears[y.year] : y.year === firstOpen;\n    const head = `<button class=\"pc-year\"", 'plannerGrid', None),
 ("past: every year opens", "    const open = UI.plYears[y.year] !== undefined ? UI.plYears[y.year] : y.year === firstOpen;\n    const head = `<button class=\"pc-year\"", "    const open = UI.plYears[y.year] !== undefined ? UI.plYears[y.year] : true;\n    const head = `<button class=\"pc-year\"", 'plannerGrid', None),
 ("past: the can't-check mark too faint", "  const c = s.state === 'cant' ? [c0[0], 'var(--ink4)', c0[2], c0[3]] : c0;", "  const c = c0;", 'pastSimple', None),
 ("sheet: a term change hits every term of the class", "  q = h.term == null ? q.is('term', null) : q.eq('term', h.term);\n", "", 'pastClassSheet', None),
 ("sheet: a term change ignores the year", "  q = h.year == null ? q.is('year', null) : q.eq('year', h.year);\n", "", 'pastClassSheet', None),
 ("sheet: transfer credit asks for a professor", "${xfer ? '' : `<button class=\"pc-it\" data-a=\"pcProf\"", "${0 ? '' : `<button class=\"pc-it\" data-a=\"pcProf\"", 'pastClassSheet', None),
 ("sheet: Rate with no professor", "${pk && PROFS[pk] ? `<button class=\"btn\" style=\"width:100%;margin-top:16px\" data-a=\"rateProf\"", "${1 ? `<button class=\"btn\" style=\"width:100%;margin-top:16px\" data-a=\"rateProf\"", 'pastClassSheet', None),
 ("picker: Save before a pick", "${!sh.pick || UI.busy.pcp ? 'disabled' : ''}", "${UI.busy.pcp ? 'disabled' : ''}", 'pastProfPicker', None),
 ("picker: PolyRatings' course lists ignored", "add(pcName(p), pcPR(p), +p.numEvals || 0, false); });", "});", 'pastProfPicker', None),
 ("picker: old codes not crosswalked", "!p.courses.some(c => pcK(String(c || '').toUpperCase()) === code)", "!p.courses.some(c => String(c || '').toUpperCase() === code)", 'pastProfPicker', None),
 ("picker: teaching it now not first", ".sort((a, b) => (b.now - a.now) || (b.n - a.n) || a.name.localeCompare(b.name)).slice(0, 8));", ".sort((a, b) => (b.n - a.n) || a.name.localeCompare(b.name)).slice(0, 8));", 'pastProfPicker', None),
 ("picker: typing redraws the sheet (keyboard drops)", "const el = document.getElementById('pc-plist'); if (el) el.innerHTML = pcPList(UI.sheet); return; }", "render(true); return; }", 'pastProfPicker', None),
 ("picker: can't type someone not listed", "  const typed = q.length >= 3 && !list.some(", "  const typed = false && !list.some(", 'pastProfPicker', None),
 ("picker: a refused save looks saved", "      if (e) { sh.err = e; return; }\n      toast('Saved ' + sh.pick);", "      if (e) { UI.sheet = null; return; }\n      toast('Saved ' + sh.pick);", 'pastProfPicker', None),
 ("picker: the saved name isn't read back", "return 'Couldn’t save that — try again.'; }\n  await TC.reloadHistory(); loadRateList(); return null;", "return 'Couldn’t save that — try again.'; }\n  return null;", 'pastProfPicker', None),
 ("picker: a write that changed nothing counts as saved", "  if (!Array.isArray(r.data) || !r.data.length) { await TC.reloadHistory(); return 'Couldn’t save that — try again.'; }\n", "", 'pastProfPicker', None),
 ("picker: a redraw drops the keyboard", "<input id=\"pc-q\" data-in=\"pcq\"", "<input data-in=\"pcq\"", 'pastProfPicker', None),
 ("picker: a tap outside closes everything", "    if (UI.sheet && (UI.sheet.type === 'pcProf' || UI.sheet.type === 'pcTerm') && UI.sheet.ret) { pcBack(UI.sheet); render(true); return; }", "", 'pastProfPicker', None),
 ("past: a retake shares its spot", "if (q && q.length) slot.set(s.id, q.shift());", "if (q && q.length) slot.set(s.id, q[q.length - 1]);", 'pastSimple', None),
 ("term: a blank term is chosen for you", "t0 = h.term || '', y0 = +h.year || 0,", "t0 = h.term || 'Spring', y0 = +h.year || y,", 'pastClassSheet', None),
 ("term: an old year isn't offered", "from = Math.min(y0 || y, y - 10);", "from = y - 8;", 'pastClassSheet', None),
 ("onboarding: the ask goes off under the list", "if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet.onb = true; else setTimeout(() => TC.pushAsk('onboarding'), 600); }", "setTimeout(() => TC.pushAsk('onboarding'), 600); }", 'onbReportLast', None),
 ("onboarding: Done never asks", "if (onb) setTimeout(() => TC.pushAsk('onboarding'), 600); },", "},", 'onbReportLast', None),
 ("picker: no word when PolyRatings fails", "(!q && TC.err.poly ? '<div class=\"muted b pc-none\">PolyRatings didn’t load", "(0 ? '<div class=\"muted b pc-none\">PolyRatings didn’t load", 'pastProfPicker', None),
 ("who: a save doesn't go back to the list", "      toast('Saved ' + sh.pick); if (UI.sheet === sh) pcBack(sh);", "      toast('Saved ' + sh.pick); UI.sheet = null;", 'pastWhoTaught', None),
 ("who: lists transfer credit", "  const rows = pcHist().filter(h => !pcXfer(h) && h.term && h.year);", "  const rows = pcHist().filter(h => h.term && h.year);", 'pastWhoTaught', None),
 ("who: never asked after a report", "UI.sheet = who.length ? { type: 'pcWho', keys: who } : null;", "UI.sheet = null;", 'pastWhoTaught', None),
 ("marks: the circle never reads pressed", "aria-pressed=\"${!!s.mine}\" aria-label=\"Mark ${esc(code || name || s.title)} done\"", "aria-pressed=\"false\" aria-label=\"Mark ${esc(code || name || s.title)} done\"", 'flowchartMarks', None),
 ("past: Remove takes every attempt", "  if (h) { q = h.term == null ? q.is('term', null) : q.eq('term', h.term); q = h.year == null ? q.is('year', null) : q.eq('year', h.year); }\n", "", 'pastClassSheet', None),
 ("past: Remove doesn't name the term", "title: 'Remove ' + pcK(h.code) + (when ? ', ' + when : '') + '?'", "title: 'Remove ' + pcK(h.code) + '?'", 'pastClassSheet', None),
 ("past: a can't-check row says nothing to a screen reader", "${s.state === 'cant' ? '<span class=\"pc-sr\">, we can’t check this from your record</span>' : ''}", "", 'planner', None),
 ("past: the screen-reader words show on screen", ".pc-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}", ".pc-sr{}", 'planner', None),
 ("marks: a checked-off row opens like a class", "    : s.state === 'need' && s.type === 'ge' ? `data-a=\"plGe\"", "    : (s.state === 'need' || s.mine) && s.type === 'ge' ? `data-a=\"plGe\"", 'flowchartMarks', None),
 ("past: the cards touch the screen edge", ".pc-pg{padding:0 12px}", ".pc-pg{}", 'pageWidthHome', None),
 ("past: a long concentration spills out of the card", ".pc-conc .chip{max-width:100%;height:auto;min-height:36px;padding:7px 14px;white-space:normal;text-align:left}", ".pc-conc .chip{}", 'pastSimple', None),
 ("who: blocks onboarding's end", "  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho') && !(UI.dpr && UI.dpr.saveErr)) {", "  if (wasOnb && !UI.sheet && !(UI.dpr && UI.dpr.saveErr)) {", 'onbReportLast', None),
]
bad = [(n, (pl if t == 'planner' else html).count(a)) for n, a, b, test, t in M if (pl if t == 'planner' else html).count(a) != 1]
if bad: sys.exit('past-classes-mutants: bad anchors ' + json.dumps(bad))
P = os.path.join(H, 'mutate.mjs'); s = open(P, encoding='utf-8').read()
# older mutants whose code this build rewrote: aimed at the new code, same test
for old, new in [
    ("""["dpr first: Past classes without the DPR card", "return (none ? dprFirstCard() : '') + ledgerCard(L, P) + gridCard(L)", "return ledgerCard(L, P) + gridCard(L)", "planner"],""",
     """["dpr first: Past classes without the DPR card", "return (none ? dprFirstCard() : '') + `<div class=\\"pc-pg\\">${pcSummary(L)", "return `<div class=\\"pc-pg\\">${pcSummary(L)", "pastSimple"],"""),
    ("""["dpr first: Past classes without the DPR card", "return (none ? dprFirstCard() : '') + pcSummary(L) + pcYears(L)", "return pcSummary(L) + pcYears(L)", "planner"],""",
     """["dpr first: Past classes without the DPR card", "return (none ? dprFirstCard() : '') + `<div class=\\"pc-pg\\">${pcSummary(L)", "return `<div class=\\"pc-pg\\">${pcSummary(L)", "pastSimple"],"""),
    ("""['grid ignores the ledger (uncoded)', "if (uc.done[sl.id]) { row.f++; cell.state = 'done'; }", "if (uc.done[sl.id]) { row.f++; cell.state = 'need'; }", 'plannerGrid', 'planner'],""",
     """['grid ignores the ledger (uncoded)', "if (uc.done[sl.id]) { row.f++; cell.state = 'done'; if (uc.with", "if (uc.done[sl.id]) { row.f++; cell.state = 'need'; if (uc.with", 'plannerGrid', 'planner'],"""),
    ("""  ['flowchart repeats the code as the name', "    const title = s.choice ? (s.by ? courseName(s.by) : s.title) : code && (codeLike(s.title)", "    const title = s.choice ? (s.by ? courseName(s.by) : s.title) : code && (false", 'plannerQuickTick'],""",
     """  ['flowchart repeats the code as the name', ": code ? (courseName(code) || (codeLike(s.title) ? '' : s.title))", ": code ? (s.title || courseName(code))", 'plannerQuickTick'],"""),
    ("""  ['units back on the rows', "</${act ? 'button' : 'div'}></div>${pick}`;", "</${act ? 'button' : 'div'}><span>${s.units}u</span></div>${pick}`;", 'plannerQuickTick'],""",
     """  ['units back on the rows', "${line}</div></div>${pick}`;", "${line}</div><span>${s.units}u</span></div>${pick}`;", 'plannerQuickTick'],"""),
    ("""  ["split: Past classes puts the record first", "+ ledgerCard(L, P) + gridCard(L) + (none ? '' : historyCard());", "+ (none ? '' : historyCard()) + ledgerCard(L, P) + gridCard(L);", "plannerGrid"],""",
     """  ["split: Past classes puts the record first", "${pcSummary(L) + pcYears(L) + (none ? '' : pcOther(L) + pcBtns())}</div>`;", "${(none ? '' : pcOther(L) + pcBtns()) + pcSummary(L) + pcYears(L)}</div>`;", "pastSimple"],"""),
    ("""  ["split: no term bubbles", "return `<div class=\\"tc-term\\"><div class=\\"tc-termh\\">", "return `<div class=\\"tc-term-x\\"><div class=\\"tc-termh\\">", "plannerGrid"],""",
     """  ["split: no term bubbles", "`<div class=\\"pc-term\\"><div class=\\"pc-termh\\">${esc(String(t.term", "`<div class=\\"pc-term-x\\"><div class=\\"pc-termh\\">${esc(String(t.term", "plannerGrid"],"""),
    # the same as "past: years count can't-check spots" now
    ("""  ['grid counts can’t-check slots as requirements', "judged = slots.length - cant;", "judged = slots.length;", 'plannerGrid'],\n""", ""),
    ("""  ["draft: a new report doesn't refresh the drafts", "      UI.sheet = null; UI.pl = null; UI.plRefresh = true;", "      UI.sheet = null; UI.pl = null;", "plannerRefresh"],""",
     """  ["draft: a new report doesn't refresh the drafts", "      UI.pl = null; UI.plRefresh = true;\\n      const who", "      UI.pl = null;\\n      const who", "plannerRefresh"],"""),
    ("""  ["onboarding: the upload leaves onboarding open", "  if (wasOnb && !UI.sheet && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null);", "  if (false) { onbRemember(null);", "onbReportLast"],""",
     """  ["onboarding: the upload leaves onboarding open", "  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho') && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null);", "  if (false) { onbRemember(null);", "onbReportLast"],"""),
    # 23:30's flowchart marks: "Marked done by you" is the row's second line now
    ("""  ["marks: no 'Marked done by you'", "${s.mine ? '<span class=\\"b tc-mine\\" style=\\"font-size:12px;display:block\\">Marked done by you</span>' :", "${false ? '' :", "flowchartMarks"],""",
     """  ["marks: no 'Marked done by you'", "const line = s.mine ? '<span class=\\"pc-pf tc-mine\\">Marked done by you</span>' :", "const line = false ? '' :", "flowchartMarks"],"""),
    # the flowchart's key is gone (2026-10-10): its CSS too, so "wraps" has nothing to break
    ("""  ['flowchart key wraps', ".tc-key > span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}\\n.tc-key .tc-dot{width:18px;height:18px;font-size:10.5px}", ".tc-key > span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;min-width:120px}\\n.tc-key .tc-dot{width:18px;height:18px;font-size:10.5px}", 'planner'],\n""", ""),
    # equivalent: --teal-t is set in both themes, so dropping the fallback changes nothing on screen
    ("""  ["light: done ✓ loses its teal", "const CELL = { done: ['✓', 'var(--teal-t,var(--teal))',", "const CELL = { done: ['✓', 'var(--teal-t)',", "planner"],\n""", ""),
    # Skip for now is what plannerNoDraft taps (dprRead never does)
    ("""  ["dpr first: show picks not remembered", "plShowPicks: () => { try { localStorage.setItem(plSkipKey(), '1'); } catch (e) {} render(true); },", "plShowPicks: () => { UI.x = 1; render(true); },", "dprRead"],""",
     """  ["dpr first: show picks not remembered", "plShowPicks: () => { try { localStorage.setItem(plSkipKey(), '1'); } catch (e) {} render(true); },", "plShowPicks: () => { UI.x = 1; render(true); },", "plannerNoDraft"],"""),
    # the flowchart's key is gone (2026-10-10): nothing left to put out of order
    ("""  ['flowchart key out of order', "${['done', 'taking', 'need', 'cant'].map(k =>", "${['done', 'need', 'taking', 'cant'].map(k =>", 'planner'],\n""", ""),
]:
    if old in s: s = s.replace(old, new)
    elif new and new not in s: sys.exit('past-classes-mutants: re-aim missing ' + old[:50])
    elif not new and old.split(',')[0] in s: sys.exit('past-classes-mutants: drop missing ' + old[:50])
start, end = '  /* Past classes, option A simple (2026-10-10; written by past-classes-mutants.py, anchors checked) */\n', '  /* end Past classes (2026-10-10) */\n'
if start in s: s = s[:s.index(start)] + s[s.index(end) + len(end):]
body = start + ''.join('  ' + json.dumps([n, a, b, test] + ([t] if t else []), ensure_ascii=False) + ',\n' for n, a, b, test, t in M) + end
anchor = "];\nconst html = fs.readFileSync(SRC, 'utf8');"
if s.count(anchor) != 1: sys.exit('past-classes-mutants: mutate.mjs anchor')
s = s.replace(anchor, body + anchor)
open(P, 'w', encoding='utf-8').write(s)
print(f'past-classes-mutants: {len(M)} written')
# keep dpr-flow-mutants.py (which writes the flow's section) in step with the two it owns
F = os.path.join(H, 'dpr-flow-mutants.py'); f = open(F, encoding='utf-8').read()
for old, new in [
    ("""("draft: a new report doesn't refresh the drafts", "      UI.sheet = null; UI.pl = null; UI.plRefresh = true;", "      UI.sheet = null; UI.pl = null;", "plannerRefresh"),""",
     """("draft: a new report doesn't refresh the drafts", "      UI.pl = null; UI.plRefresh = true;\\n      const who", "      UI.pl = null;\\n      const who", "plannerRefresh"),"""),
    ("""("onboarding: the upload leaves onboarding open", "  if (wasOnb && !UI.sheet && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null);", "  if (false) { onbRemember(null);", "onbReportLast"),""",
     """("onboarding: the upload leaves onboarding open", "  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho') && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null);", "  if (false) { onbRemember(null);", "onbReportLast"),"""),
]:
    if old in f: f = f.replace(old, new)
    elif new not in f: sys.exit('past-classes-mutants: dpr-flow-mutants.py re-aim missing ' + old[:50])
open(F, 'w', encoding='utf-8').write(f)
