#!/usr/bin/env python3
r"""Planner: real class names, a one-tap "I took it", choice slots that can be checked, no per-row units.
(Tate, 2026-10-02, on screenshots of the Planner.)

  "for classes you need make sure to give them titles you can keep the Bus in blue and then after
   have the name of the class" — "same for this class for some reason it just names the number
   twice. also take out the 1u 3u for units its not necessary" — "for classes like this [Calculus for
   Data Science I or Business Calculus] make it easy for users to just click the check mark if they
   want to click theyve taken it and dont want to do things after that"

1. NAMES. "Still need" and the flowchart showed "BUS 3411  BUS 3411": the flowchart's slot title IS
   the code for many classes, and a class not offered this term has no title in the seat feed. One
   lookup now, courseName(code), first that has a real name (never a code):
     the seat feed (this term) → course_catalog.title (the scraper's registrar title; read with the
     descriptions, and if the column is missing the old read runs unchanged) → a flowchart slot that
     names it → the desktop's own catalog names, lifted verbatim from index.html at patch time
     (CONC_MODEL, "Cal Poly 2026–28 catalog"; then MAJOR_CATALOG; then GE_COURSES).
   No name anywhere → the code shows once, alone. Nothing is invented.
2. Units per row ("1u", "3u") are gone from the flowchart. The year line keeps its unit total.
3. ONE TAP. On the flowchart, a class still to take has its own round check button: tap it and the
   class is on your record ("Earlier", no term) — nothing to fill in. Tap the ✓ again to undo (only a
   one-tap record, never a dated one or a report import; if the class still counts from a report or a
   waiver, it says so). A class already on the record once (a repeatable one) asks for the term instead,
   so a term-less row can never land on top of a dated one; the write is an insert, never an upsert. The row itself still opens "Log a class"
   for anyone who wants to add the term and professor. If the database ever refuses a record with no
   term, the tap opens "Log a class" with the class filled in instead of failing silently.
4. CHOICE SLOTS ("Calculus for Data Science I or Business Calculus", 162 of them across the
   flowcharts, each with its options listed) were "can't check" even when the record had one of the
   options. The ledger now checks them against their options, like a coded slot — so they count, fill
   from your record and the report, and get the same check button: tap it, pick which one (the only
   question, since the record must name a real class). The desktop still calls them can't-check; it
   should adopt this.

Usage: python3 planner-names-quick-tick-2026-10-02.py <repo-dir>
Edits app/index.html, app/planner.js and app-dev/source/planner-src.js; reads index.html (desktop).
Every anchor must match exactly once, or nothing is written.
"""
import sys, os, re, json
d = sys.argv[1]
P = {k: os.path.join(d, v) for k, v in {'app': 'app/index.html', 'pl': 'app/planner.js', 'src': 'app-dev/source/planner-src.js'}.items()}
S = {k: open(v, encoding='utf-8').read() for k, v in P.items()}
if 'function courseName(' in S['app']: sys.exit('already patched')
desk = open(os.path.join(d, 'index.html'), encoding='utf-8').read()

# ---- lift the desktop's catalog names (first source wins) ----
def block(start, end):
    i = desk.index(start); return desk[i:desk.index(end, i)]
CODE = r"([A-Z]{2,5} \d{4}[A-Z]?)"
NAME = r"((?:[^'\\]|\\.)+)"
names = {}
srcs = [(block('var CONC_MODEL=', '\n};'), [r"\{code:'" + CODE + r"',title:'" + NAME + "'"]),
        (block('const MAJOR_CATALOG=', '\n};'), [r"\{code:'" + CODE + r"',name:'" + NAME + "'", r"\['" + CODE + r"','" + NAME + "'"]),
        (block('const GE_COURSES=', '\n];'), [r"\{code:'" + CODE + r"',name:'" + NAME + "'"])]
for b, pats in srcs:
    for pat in pats:
        for c, n in re.findall(pat, b):
            n = n.replace("\\'", "'").strip()
            if n and c not in names and not re.fullmatch(r"[A-Z]{2,5} ?\d{3,4}[A-Z]?", n): names[c] = n
if len(names) < 400 or names.get('BUS 3411') != 'Finance Practicum' or names.get('BUS 3441') != 'Financial Modeling and Analytics in Python or R':
    sys.exit(f'name lift looks wrong ({len(names)} names)')
LIFT = json.dumps(dict(sorted(names.items())), ensure_ascii=False, separators=(',', ':'))

A = [
 # 1. the one name lookup
 ("const course = code => COURSES[code] || { title: code, short: code, desc: null, prereq: null };",
  "const course = code => COURSES[code] || { title: code, short: code, desc: null, prereq: null };\n"
  "/* A class's NAME, never its code (Tate, 2026-10-02: \"it just names the number twice\"). First that has one:\n"
  "   this term's seat feed → course_catalog.title (the registrar's, via the scraper) → the desktop's own catalog\n"
  "   names (CONC_MODEL \"Cal Poly 2026–28 catalog\", MAJOR_CATALOG, GE_COURSES), lifted verbatim from index.html by\n"
  "   planner-names-quick-tick-2026-10-02.py → a flowchart slot that names it (one course only, its GE tag dropped). None → ''. */\n"
  "const LIFTED_NAMES = " + LIFT + ";\n"
  "const CAT_TITLE = {};\n"
  "const codeLike = t => /^[A-Z&]{2,5}\\s*\\d{3,4}[A-Z]?(\\s*(&|and|or|\\/)\\s*([A-Z&]{2,5}\\s*)?\\d{3,4}[A-Z]?L?)*$/i.test(String(t || '').trim());\n"
  "let FLOW_NAMES = null;\n"
  "function flowNames() {\n"
  "  if (FLOW_NAMES) return FLOW_NAMES;\n"
  "  const M = window.SCHED_MAJORS; if (!M) return {};\n"
  "  const out = {};\n"
  "  Object.keys(M).forEach(k => ((M[k] && M[k].terms) || []).forEach(t => (t.slots || []).forEach(sl => {\n"
  "    if (!sl || !sl.code || !sl.title || codeLike(sl.title) || /[&,]|\\bor\\b/i.test(sl.code)) return;   // \"X & XL\" titles name both\n"
  "    const c = canonCode(sl.code), t = String(sl.title).replace(/\\s*\\((?:[0-9A-C/ &,-]+|Upper-Division[^)]*|USCP[^)]*)\\)\\s*$/i, '').trim();\n"
  "    if (c && t && !out[c]) out[c] = t;\n"
  "  })));\n"
  "  return (FLOW_NAMES = out);\n"
  "}\n"
  "function courseName(code) {\n"
  "  const c = COURSES[code]; if (c && c.title && c.title !== code && !codeLike(c.title)) return c.title;\n"
  "  return CAT_TITLE[code] || LIFTED_NAMES[code] || flowNames()[code] || '';\n"
  "}"),
 # 2. course_catalog: read the registrar's title too (falls back to the old read if the column is missing)
 ("      const res = await fetch(base + '/rest/v1/course_catalog?select=course_code,prereqs,description&order=course_code.asc&limit=1000&offset=' + off, { headers: hdr });\n"
  "      if (!res.ok) return;",
  "      let res = await fetch(base + '/rest/v1/course_catalog?select=' + (TC.noCatTitle ? '' : 'title,') + 'course_code,prereqs,description&order=course_code.asc&limit=1000&offset=' + off, { headers: hdr });\n"
  "      if (!res.ok && off === 0 && !TC.noCatTitle) { TC.noCatTitle = true; res = await fetch(base + '/rest/v1/course_catalog?select=course_code,prereqs,description&order=course_code.asc&limit=1000&offset=0', { headers: hdr }); }\n"
  "      if (!res.ok) return;"),
 ("      part.forEach(r => { const c = canonCode(r.course_code); if (c && COURSES[c]) {",
  "      part.forEach(r => { const c = canonCode(r.course_code); const tt = String(r.title || '').replace(/\\s+/g, ' ').trim(); if (c && tt && !codeLike(tt)) CAT_TITLE[c] = tt; if (c && COURSES[c]) {"),
 # 3. Still need: the code chip, then the class's name (a choice slot: "Pick 1", its own words, and its options)
 ("    const offered = !!COURSES[code];\n"
  "    return `<button class=\"li\" data-a=\"${offered ? 'openClass' : 'plCourse'}\" data-x=\"${esc(code)}\"><span class=\"code\">${esc(code)}</span><span class=\"grow\" style=\"min-width:0\"><span class=\"b\" style=\"display:block;font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis\">${esc(n.title || course(code).title)}</span><span class=\"muted b\" style=\"font-size:12.5px\">${esc(yearTerm(n))} · ${offered ? 'offered ' + esc(CFG.TERM_LABEL) : 'not offered ' + esc(CFG.TERM_LABEL)}</span>",
  "    const offered = !!COURSES[code];\n"
  "    const nm = n.choice ? n.title : (n.title && !codeLike(n.title) ? n.title : courseName(code));\n"
  "    const opts = n.choice ? n.codes.map(c => c + (courseName(c) ? ' ' + courseName(c) : '')).join(' or ') + ' · ' : '';\n"
  "    return `<button class=\"li\" data-a=\"${offered ? 'openClass' : 'plCourse'}\" data-x=\"${esc(code)}\"><span class=\"code\">${n.choice ? 'Pick 1' : esc(code)}</span><span class=\"grow\" style=\"min-width:0\">${nm ? `<span class=\"b tc-nm\" style=\"display:block;font-size:14.5px\">${esc(nm)}</span>` : ''}<span class=\"muted b\" style=\"font-size:12.5px\">${esc(opts)}${esc(yearTerm(n))} · ${offered ? 'offered ' + esc(CFG.TERM_LABEL) : 'not offered ' + esc(CFG.TERM_LABEL)}</span>"),
 # 4. the flowchart cell: a check button of its own, the name once, no units
 ("  const cell = s => {\n"
  "    const c = CELL[s.state] || CELL.need, code = s.code ? (s.by || (s.codes && s.codes[0]) || s.code) : '';\n"
  "    const act = s.state === 'need' && s.code ? `data-a=\"plLogSlot\" data-x=\"${esc((s.codes && s.codes[0]) || s.code)}\"`",
  "  const cell = s => {\n"
  "    const c = CELL[s.state] || CELL.need, code = s.choice && !s.by ? '' : s.code ? (s.by || (s.codes && s.codes[0]) || s.code) : '';\n"
  "    /* the name, once: a slot that names its class keeps its words; one that only repeats the code\n"
  "       (or a choice already filled by one of its options) gets the class's real name, if anyone has it */\n"
  "    const title = s.choice ? (s.by ? courseName(s.by) : s.title) : code && (codeLike(s.title) || !s.title || (s.by && s.code && s.by !== TCPL.canon(s.code))) ? courseName(code) || (codeLike(s.title) ? '' : s.title) : s.title;\n"
  "    /* one tap = on your record (Tate, 2026-10-02); a one-tap record unticks the same way */\n"
  "    const quick = s.state === 'done' && s.by && (TC.myHistory || []).some(h => TCPL.canon(h.code) === s.by && !h.term && !h.year);\n"
  "    const tickable = (s.state === 'need' && (s.code || s.choice)) || quick;\n"
  "    const dot = tickable\n"
  "      ? `<button class=\"tc-dot tc-tick\" style=\"color:${c[1]};background:${c[2]}\" data-a=\"plTick\" data-x=\"${esc(s.id)}\" aria-label=\"${quick ? 'Undo: ' + esc(s.by) + ' taken' : 'I took ' + esc(s.choice ? s.title : code)}\" ${UI.busy.tick === s.id ? 'disabled' : ''}>${c[0]}</button>`\n"
  "      : `<span class=\"tc-dot\" style=\"color:${c[1]};background:${c[2]}\" aria-label=\"${c[3]}\">${c[0]}</span>`;\n"
  "    const pick = s.choice && s.state === 'need' && UI.plPick === s.id\n"
  "      ? `<div class=\"tc-pick\"><div class=\"muted b\" style=\"font-size:12.5px;width:100%\">Which one did you take?</div>${s.choice.map(o => `<button class=\"tc-pickb\" data-a=\"plTickCode\" data-x=\"${esc(o)}\" data-y=\"${esc(s.id)}\"><span class=\"tc-ccode\">${esc(o)}</span>${esc(courseName(o))}</button>`).join('')}</div>` : '';\n"
  "    const act = s.state === 'need' && s.choice ? `data-a=\"plTick\" data-x=\"${esc(s.id)}\"`\n"
  "      : s.state === 'need' && s.code ? `data-a=\"plLogSlot\" data-x=\"${esc((s.codes && s.codes[0]) || s.code)}\"`"),
 ("    return `<${act ? 'button' : 'div'} class=\"tc-cell ${s.state}\" ${act}><span class=\"tc-dot\" style=\"color:${c[1]};background:${c[2]}\" aria-label=\"${c[3]}\">${c[0]}</span>\n"
  "      <span class=\"grow\" style=\"min-width:0\"><span class=\"b tc-ctitle\">${code ? `<span class=\"tc-ccode\">${esc(code)}</span>` : ''}${esc(s.title)}</span>${s.state === 'cant' && s.note ? `<span class=\"muted b\" style=\"font-size:12px;display:block\">${esc(s.note)}</span>` : ''}</span>\n"
  "      <span class=\"muted b\" style=\"font-size:12px;flex:none\">${s.units != null ? esc(s.units) + 'u' : ''}</span></${act ? 'button' : 'div'}>`;\n"
  "  };",
  "    return `<div class=\"tc-cell ${s.state}\">${dot}<${act ? 'button' : 'div'} class=\"grow tc-cbody\" ${act}><span class=\"b tc-ctitle\">${code ? `<span class=\"tc-ccode\">${esc(code)}</span>` : ''}${esc(title)}</span>${s.state === 'cant' && s.note ? `<span class=\"muted b\" style=\"font-size:12px;display:block\">${esc(s.note)}</span>` : ''}</${act ? 'button' : 'div'}></div>${pick}`;\n"
  "  };"),
 ("Tap a class you’ve taken to log it; tap a GE area to see this term’s classes for it.",
  "Tap the circle when you’ve taken a class. Tap a class to add its term, or a GE area to see this term’s classes for it."),
 # 5. the actions
 ("  plLogSlot: code => { UI.lc = { code }; UI.sheet = { type: 'logClass' }; render(true); },",
  "  plLogSlot: code => { UI.lc = { code }; UI.sheet = { type: 'logClass' }; render(true); },\n"
  "  plTick: async id => {\n"
  "    if (UI.busy.tick) return toast('One moment — still saving');\n"
  "    const L = window.TCPL && TCPL.ledger(); const s = L && L.grid.flatMap(t => t.slots).find(x => x.id === id); if (!s) return;\n"
  "    if (s.state === 'done' && s.by) return quickUnlog(s.by, id);\n"
  "    if (s.state !== 'need') return;\n"
  "    if (s.choice) { UI.plPick = UI.plPick === id ? null : id; return render(true); }\n"
  "    quickLog((s.codes && s.codes[0]) || s.code, id);\n"
  "  },\n"
  "  plTickCode: (code, id) => { UI.plPick = null; quickLog(code, id); },"),
 ("SHEETS.logClass = () => {",
  "/* One tap = this class is on your record, with no term (the history list files it under \"Earlier\"). */\n"
  "async function quickLog(code, id) {\n"
  "  if (window.TCPL) { const cur = TCPL.canon(code); if (cur) code = cur; }\n"
  "  /* already on the record once (a repeatable class): a second, term-less row could collide with it — ask for the term */\n"
  "  if ((TC.myHistory || []).some(h => TCPL.canon(h.code) === code)) { UI.lc = { code, err: `${code} is already on your record once — add the term you took it again.` }; UI.sheet = { type: 'logClass' }; return render(true); }\n"
  "  UI.busy.tick = id; render(true);\n"
  "  const r = await TC.client().from('class_history').insert({ user_id: TC.user.id, code, term: null, year: null, professor: null });\n"
  "  UI.busy.tick = 0;\n"
  "  if (r.error && (r.error.code === '23502' || /null value/i.test(r.error.message || ''))) { UI.lc = { code, err: 'Add the term you took it, then save.' }; UI.sheet = { type: 'logClass' }; return render(true); }\n"
  "  if (r.error) { toast(dbSay(r.error, 'Couldn’t save that class.')); return render(true); }\n"
  "  const fresh = await TC.reloadHistory(); loadRateList(); render(true);\n"
  "  toast(fresh ? `${code} is on your record · tap ✓ to undo` : `${code} saved — pull down to refresh your record`);\n"
  "}\n"
  "async function quickUnlog(code, id) {\n"
  "  const row = (TC.myHistory || []).find(h => TCPL.canon(h.code) === code && !h.term && !h.year); if (!row) return;\n"
  "  UI.busy.tick = id; render(true);\n"
  "  const r = await TC.client().from('class_history').delete().eq('user_id', TC.user.id).eq('code', row.code).is('term', null).is('year', null);\n"
  "  UI.busy.tick = 0;\n"
  "  if (r.error) { toast(dbSay(r.error, 'Couldn’t undo that.')); return render(true); }\n"
  "  await TC.reloadHistory(); loadRateList(); render(true);\n"
  "  const L = TCPL.ledger(), s = L && L.grid.flatMap(t => t.slots).find(x => x.id === id);\n"
  "  toast(s && s.state === 'done' ? `${code} still counts — it’s on your degree report or a waiver` : `${code} taken off your record`);\n"
  "}\n"
  "SHEETS.logClass = () => {"),
 # 6. styles
 (".tc-cell{display:flex;align-items:center;gap:10px;width:100%;padding:8px 0;text-align:left;border-top:1px solid var(--line)}",
  ".tc-cell{display:flex;align-items:center;gap:10px;width:100%;padding:8px 0;text-align:left;border-top:1px solid var(--line)}\n"
  ".tc-cbody{min-width:0;text-align:left;align-self:stretch;display:flex;flex-direction:column;justify-content:center;background:none;border:0;padding:8px 0;margin:-8px 0;min-height:44px;font:inherit;color:inherit}\n"
  ".tc-tick{position:relative;border:0;padding:0;font:inherit;cursor:pointer}\n"
  ".tc-tick::after{content:\"\";position:absolute;inset:-9px}\n"
  ".tc-cell.need .tc-tick{box-shadow:inset 0 0 0 2px var(--muted)}\n"
  ".tc-pick{display:flex;flex-wrap:wrap;gap:8px;padding:2px 0 10px 36px}\n"
  ".tc-pickb{min-height:44px;padding:8px 12px;border-radius:12px;background:var(--bg);border:0;font:inherit;font-weight:800;font-size:13.5px;color:var(--ink2);text-align:left}"),
]
B = [
 # the ledger: choice slots check against their listed options
 ("  function ledger() {",
  "  /* A choice slot (\"Calculus for Data Science I or Business Calculus\") lists its options. Checked against\n"
  "     them like a coded slot (Tate, 2026-10-02) instead of \"can't check\": its first option stands in as\n"
  "     the code, and _opts carries them all to slotCodes() and the ledger below. */\n"
  "  function withChoiceCodes(m) {\n"
  "    var CODE = /^[A-Z&]{2,5} \\d{3,4}[A-Z]?$/;\n"
  "    return Object.assign({}, m, { terms: (m.terms || []).map(function (t) { return Object.assign({}, t, { slots: (t.slots || []).map(function (sl) {\n"
  "      if (!sl || sl.code || sl.type !== 'choice' || !Array.isArray(sl.options) || sl.options.length < 2) return sl;\n"
  "      var o = sl.options.map(function (c) { var raw = String(c || '').trim().toUpperCase(); return canonCode(raw) || raw; });\n"
  "      if (!o.every(function (c) { return CODE.test(c); })) return sl;\n"
  "      return Object.assign({}, sl, { code: o[0], _opts: o });\n"
  "    }) }); }) });\n"
  "  }\n"
  "  function ledger() {"),
 ("    var mm = schExpandConc(base);", "    var mm = withChoiceCodes(schExpandConc(base));"),
 ("          var cs = window.schSlotCodes(sl.code);",
  "          var cs = sl._opts ? sl._opts.slice() : window.schSlotCodes(sl.code);\n"
  "          if (sl._opts) cell.choice = sl._opts.slice();"),
 ("need.push({ title: sl.title || '', codes: cs, group:", "need.push({ title: sl.title || '', codes: cs, choice: !!sl._opts, group:"),
]
C = [  # the lifted helper (app/planner.js only — it comes from the desktop at build time)
 ("function slotCodes(s){ if(!s.code)return [];", "function slotCodes(s){ if(s._opts)return s._opts.slice(); if(!s.code)return [];"),
]
for key, reps in (('app', A), ('pl', B + C), ('src', B)):
    for a, b in reps:
        n = S[key].count(a)
        if n != 1: sys.exit(f'{key}: anchor matched {n}x: {a[:90]}')
        S[key] = S[key].replace(a, b)
for k in S: open(P[k], 'w', encoding='utf-8').write(S[k])
print('patched', len(names), 'lifted names')
