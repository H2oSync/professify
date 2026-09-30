#!/usr/bin/env python3
"""Prerequisites as one answer (Tate, 2026-09-29).

"for prereqs we shouldnt display all of them it should just display fulfilled or not fulfilled
and then if its not you can click it and it brings you to the planner and shows the classes"

The class page's PREREQ tile shows only the verdict. Not fulfilled opens Schedule > Planner with a
card at the top listing the classes still needed. The verdict uses the desktop's own
prereqStatus() and course_prereqs, which is the same rule the Planner already uses.

Run from the repo root:  python3 app-dev/patches/prereq-verdict-2026-09-29.py
Each anchor must match once. Running the script again changes nothing.
"""
import sys, pathlib

P = pathlib.Path('app/index.html')
s = P.read_text()
MARK = '/* ---- Prerequisites, as one answer'
if MARK in s:
    print('already applied'); sys.exit(0)

def sub(a, b):
    global s
    n = s.count(a)
    if n != 1:
        sys.exit(f'anchor matched {n} times: {a[:80]!r}')
    s = s.replace(a, b)

# 1. CSS: the verdict pill on the blue hero, and the tile as a button.
sub(".stat b{font-size:16px;font-weight:900}\n",
    ".stat b{font-size:16px;font-weight:900}\n"
    ".stat.pq{display:block;width:100%;text-align:left;color:inherit;font:inherit;border:0;cursor:pointer;min-height:44px}\n"
    ".stat.pq small{display:flex;align-items:center;justify-content:space-between}\n"
    ".stats.has-pq{grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)}\n"
    ".stat .pqv{display:inline-block;white-space:nowrap;font-size:12.5px;line-height:1.2;padding:4px 8px;border-radius:999px;margin-top:4px}\n"
    ".pqv.ok{background:#DCFCE7;color:#14532D}.pqv.bad{background:#FEE2E2;color:#7F1D1D}.pqv.mid{background:#FEF3C7;color:#78350F}\n"
    ".stat .pqv.plain{padding:0;font-size:14px;white-space:normal}\n"
    ".tc-pqfor{border:2px solid var(--blue)}\n"
    ".tc-pqgroup{padding:8px 0 2px;border-top:1px solid var(--line)}\n"
    ".tc-pqgroup:first-of-type{border-top:0}\n"
    ".tc-pqst{font-size:12.5px;font-weight:900;letter-spacing:.02em}\n"
    ".tc-pqfor .xbtn{width:44px;height:44px}\n"
    ".tc-pqfor .tc-sech .code{min-height:44px;display:inline-flex;align-items:center;padding:0 12px}\n")

# 2. The class page: the tile shows the verdict.
sub("  const prereq = c.prereq || (TC.catalogLoaded ? 'None listed' : '—');\n",
    "  ensurePrereqs();\n  const pqTile = prereqTile(code);\n")
sub("<div class=\"stats\"><div class=\"stat\"><small>SECTIONS</small>", "<div class=\"stats has-pq\"><div class=\"stat\"><small>SECTIONS</small>")
sub("<div class=\"stat\"><small>PREREQ</small><b style=\"font-size:${prereq.length > 9 ? 12 : 16}px;line-height:1.2\">${esc(prereq.length > 60 ? prereq.slice(0, 57) + '…' : prereq)}</b></div>",
    "${pqTile}")

# 3. The helpers, next to the Planner's own prereq badge.
sub("function plannerView() {\n",
r"""/* ---- Prerequisites, as one answer: fulfilled or not (Tate, 2026-09-29). The class page shows
   only the verdict. Anything short of fulfilled opens the Planner with the classes still needed.
   The rule is the desktop's prereqStatus() over course_prereqs, the same one the Planner uses.
   If an input it depends on didn't load, the answer is "Can't check", never a guess. */
function ensurePrereqs() { if (!UI.pl) openPlanner(); }
/* Words in Cal Poly's prerequisite text that name a condition that isn't a class (standing,
   consent, a placement score…). With one of those, having the classes isn't the whole answer. */
const PQ_EXTRA = /standing|junior|senior|sophomore|graduate|consent|permission|instructor|placement|score|GPA|approval|admission|admitted|major|department|equivalent/i;
function prereqCheck(code) {
  const text = String(course(code).prereq || '').trim(), pl = UI.pl;
  if (!pl || pl.state === 'loading' || (pl.state === 'ready' && pl.prereqs === undefined)) return { k: 'wait', text };
  if (pl.state !== 'ready' || pl.prereqs === false) return { k: 'unknown', text, why: 'tables' };
  const rec = TCPL.coursePrereqs(code);
  if (!rec || !rec.req || !rec.req.length) return text ? { k: 'unknown', text } : rec || TC.catalogLoaded ? { k: 'none', text } : { k: 'wait', text };
  /* Past classes, waivers, this term's classes and the quarter→semester crosswalk all feed the
     answer. One that failed makes it unknowable; one still loading makes it not yet known. */
  if (TC.err.history || TC.wavErr || TC.err.mine || pl.equiv === false) return { k: 'unknown', text, why: 'record' };
  if (TC.myHistory === undefined || TC.waived === undefined || !TC.mineRows || pl.equiv === undefined) return { k: 'wait', text };
  plSync();
  const st = TCPL.prereqStatus(code, TCPL.completed(), [], [...myCodes()]);
  const empty = !(TC.myHistory || []).length && !Object.keys(TC.waived || {}).length;
  if (empty && (st.state === 'unmet' || st.state === 'concurrent')) return { k: 'norecord', st, rec, text };
  if (st.state === 'met' && PQ_EXTRA.test(text)) return { k: 'metnote', st, rec, text };
  return { k: st.state, st, rec, text };
}
const PQ_LOOK = { wait: ['—', 'plain'], none: ['None listed', 'plain'], unknown: ['Can’t check', 'plain', 'prereqNote'], norecord: ['Can’t check', 'plain', 'prereqGo'],
  met: ['Fulfilled', 'ok'], metnote: ['Check note', 'mid', 'prereqNote'], inprogress: ['In progress', 'mid', 'prereqGo'], concurrent: ['Take together', 'mid', 'prereqGo'], unmet: ['Not fulfilled', 'bad', 'prereqGo'] };
function prereqTile(code) {
  const [t, tone, act] = PQ_LOOK[prereqCheck(code).k] || PQ_LOOK.wait;
  const v = `<b class="pqv ${tone}">${t}</b>`;
  return act ? `<button class="stat pq" data-a="${act}" data-x="${esc(code)}" aria-label="Prerequisites: ${t}. ${act === 'prereqGo' ? 'Show the classes' : 'Show why'}"><small>PREREQ <span aria-hidden="true">${ic('chevR', 14, 3)}</span></small>${v}</button>`
    : `<div class="stat"><small>PREREQ</small>${v}</div>`;
}
function pqGroup(g) { const seen = {}; return g.map(x => TCPL.canon(x) || x).filter(x => !seen[x] && (seen[x] = 1)); }
function pqRow(code) {
  const offered = !!COURSES[code], badge = prereqBadge(code);
  return `<button class="li" data-a="${offered ? 'openClass' : 'plCourse'}" data-x="${esc(code)}"><span class="code">${esc(code)}</span><span class="grow" style="min-width:0"><span class="b" style="display:block;font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(course(code).title !== code ? course(code).title : '')}</span><span class="muted b" style="font-size:12.5px">${offered ? 'Offered ' : 'Not offered '}${esc(CFG.TERM_LABEL)}</span>${badge ? `<span style="display:block;margin-top:5px">${badge}</span>` : ''}</span><span class="chev">${ic('chevR', 18)}</span></button>`;
}
function pqWhy(r) {
  return r.why === 'tables' ? 'Prerequisites didn’t load, so this can’t be checked right now.'
    : r.why === 'record' ? 'Part of your record didn’t load, so this can’t be checked right now.'
    : 'This one isn’t a list of classes we can check against your record.';
}
/* The card at the top of the Planner after "Not fulfilled" (or In progress / Take together). */
function prereqForCard() {
  const code = UI.plFor; if (!code) return '';
  const r = prereqCheck(code);
  const head = `<div class="tc-sech"><span>Before <button class="code" data-a="${COURSES[code] ? 'openClass' : 'plCourse'}" data-x="${esc(code)}">${esc(code)}</button></span><button class="xbtn" data-a="plForClose" aria-label="Close">${ic('x', 14, 2.4)}</button></div>`;
  const wrap = body => `<div class="card tc-sec tc-pqfor" style="margin-top:14px">${head}${body}</div>`;
  if (r.k === 'wait') return wrap(loadingCard('Checking your record…'));
  if (r.k === 'none') return wrap(`<div class="b" style="font-size:14.5px">${esc(code)} has no prerequisites listed.</div>`);
  if (r.k === 'unknown') return wrap(`<div class="b" style="font-size:14.5px;line-height:1.45">${pqWhy(r)}</div>${r.text ? `<div class="muted b" style="font-size:13px;line-height:1.45;margin-top:6px">Cal Poly lists: ${esc(r.text)}</div>` : ''}`);
  const done = new Set(TCPL.completed().map(x => TCPL.canon(x) || x)), now = new Set([...myCodes()].map(x => TCPL.canon(x) || x));
  const miss = r.st.missing.length, conc = r.st.concurrent.length;
  const lead = r.k === 'met' ? `You’ve got the classes ${esc(code)} needs.`
    : r.k === 'metnote' ? `You’ve got the classes ${esc(code)} needs. Cal Poly also lists: ${esc(r.text)}`
    : r.k === 'norecord' ? `Nothing’s logged in your past classes yet, so we can’t tell. ${esc(code)} needs:`
    : r.k === 'unmet' ? `You need ${miss === 1 ? '1 more class' : miss + ' more classes'} before ${esc(code)}.`
    : r.k === 'inprogress' ? `You’re taking it now. Pass it and you’re set for ${esc(code)}.`
    : `Take this in the same term as ${esc(code)}.`;
  const groups = r.rec.req.map(g0 => {
    const g = pqGroup(g0), d = g.find(x => done.has(x)), n = !d && g.find(x => now.has(x));
    if (d) return `<div class="tc-pqgroup"><span class="tc-pqst" style="color:var(--teal)">✓ ${esc(d)} · on your record</span></div>`;
    if (n) return `<div class="tc-pqgroup"><span class="tc-pqst" style="color:var(--blue-ink)">◐ ${esc(n)} · taking now</span></div>`;
    const isConc = r.st.concurrent.some(c => pqGroup(c).join() === g.join());
    return `<div class="tc-pqgroup"><span class="tc-pqst" style="color:${isConc ? 'var(--amber-ink)' : 'var(--pink-ink)'}">${isConc ? 'Take in the same term' : 'Still need'}${g.length > 1 ? ' · any one' : ''}</span>${g.map(pqRow).join('')}</div>`;
  }).join('');
  const nudge = r.k === 'norecord' ? `<div class="muted b" style="font-size:13px;line-height:1.45;margin-top:10px">Add your past classes and this updates.</div>
    <div class="row" style="gap:8px;margin-top:8px"><button class="btn soft grow" data-a="sheet" data-x="logClass">+ Log a class</button><label class="btn soft grow tc-a" style="cursor:pointer">Import report<input type="file" accept="application/pdf,.pdf" data-in="dprfile" hidden></label></div>` : '';
  return wrap(`<div class="b" style="font-size:14.5px;line-height:1.45;margin-bottom:4px">${lead}</div>${groups}${nudge}`);
}
function plannerView() {
""")

# 4. The Planner tab shows the card above everything else.
sub("    inner = plannerView();\n", "    inner = prereqForCard() + plannerView();\n")
sub("  TC._plTables.then(r => { if (UI.pl) UI.pl.prereqs = !!(r && r.prereqs); render(true); });",
    "  TC._plTables.then(r => { if (UI.pl) { UI.pl.prereqs = !!(r && r.prereqs); UI.pl.equiv = !!(r && r.equiv); } render(true); });")
sub("function setTab(t) { ", "function setTab(t) { if (t !== 'schedule') UI.plFor = null; ")
sub("  retryPlanner: () => { UI.pl = null;", "  retryPlanner: () => { TC._plTables = null; UI.pl = null;")

# 5. Actions.
sub("  retryPlanner: () => {",
r"""  prereqGo: code => {
    UI.plFor = code; UI.champ = false; UI.sheet = null; S.schedTab = 'planner'; save();
    const st = S.stack.schedule; S.stack.schedule = [st[0]]; st[0].y = 0;
    setTab('schedule');
  },
  plForClose: () => { UI.plFor = null; render(true); },
  prereqNote: code => { UI.sheet = { type: 'prereqNote', code }; render(true); },
  retryPlanner: () => {""")
sub("  schedTab: t => { S.schedTab = t; save(); render(); },",
    "  schedTab: t => { if (t !== 'planner') UI.plFor = null; S.schedTab = t; save(); render(); },")

# 6. "Can't check" explains itself in a sheet.
sub("SHEETS.plCourse = ({ code }) => {",
r"""SHEETS.prereqNote = ({ code }) => {
  const r = prereqCheck(code);
  return `<div class="row sb"><h3>Prerequisites · ${esc(code)}</h3><button class="xbtn" data-a="closeSheet">${ic('x', 16, 2.4)}</button></div>
 <p class="muted b" style="font-size:14.5px;line-height:1.45;margin:8px 0">${r.k === 'metnote' ? '✓ The classes it needs are on your record. The rest isn’t something we can check.' : esc(pqWhy(r))}</p>
 ${r.text ? `<div class="b" style="font-size:14.5px;line-height:1.45">Cal Poly lists: ${esc(r.text)}</div>` : ''}`;
};
SHEETS.plCourse = ({ code }) => {""")

# 7. Champ answers the same way.
sub("""    case 'prereqs': { const c = cc(a.course); if (!c) return null; const p = course(c).prereq; return { t: p ? `${c} prerequisite: ${esc(p)}.<br>I can’t check your past classes against it here yet.` : TC.catalogLoaded ? `The catalog lists no prerequisite for ${c}.` : 'The catalog is still loading.' }; }""",
    """    case 'prereqs': {
      const c = cc(a.course); if (!c) return null; ensurePrereqs();
      const r = prereqCheck(c), go = [['Show in Planner', 'prereqGo', c]];
      if (r.k === 'met') return { t: `You’ve got the prerequisites for ${c}.` };
      if (r.k === 'metnote') return { t: `You’ve got the classes ${c} needs. Cal Poly also lists: ${esc(r.text)}.` };
      if (r.k === 'norecord') return { t: `I can’t tell yet. Nothing’s logged in your past classes.`, acts: go };
      if (r.k === 'unmet') return { t: `Not yet. You still need ${esc(r.st.missing.map(g => pqGroup(g).join(' or ')).join(', '))} for ${c}.`, acts: go };
      if (r.k === 'inprogress') return { t: `You’re taking the prerequisite for ${c} now.`, acts: go };
      if (r.k === 'concurrent') return { t: `${c} needs ${esc(r.st.concurrent.map(g => pqGroup(g).join(' or ')).join(', '))} in the same term.`, acts: go };
      if (r.k === 'none') return { t: `The catalog lists no prerequisite for ${c}.` };
      if (r.k === 'wait') return { t: `Still loading your record. The Planner will show it for ${c}.`, acts: go };
      return { t: r.text ? `${c} prerequisite: ${esc(r.text)}.<br>I can’t check that one against your record.` : 'I can’t check that one against your record right now.' };
    }""")

P.write_text(s)
print('applied')
