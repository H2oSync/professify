#!/usr/bin/env python3
"""Check off a flowchart row yourself (Tate, 2026-10-09: "make it so you can just click one of these classes
as done so you just check mark it", on Past classes › Your flowchart: "GE · Area 3A" with an empty circle,
"Technology Management Course" with a "?").

A row with a class code already had one tap: the class goes on your record. Rows with no class to log,
a GE area, an elective, or one TermChamp can't check, now take a tap too. The circle becomes a check,
the row says "Marked done by you", and it counts as done everywhere the flowchart is counted: the year and
term counts, the ledger and the Planner's Still need and picks. Tap it again to undo.

Stored per account and major in public.flowchart_marks (sql/professify-flowchart-marks.sql, RUN 15),
with the row's words, so a mark only applies to the row it was made on. Until that SQL runs, and whenever
the server can't be reached, marks are kept on the phone and go up at the next load.

In the ledger (planner.js), a marked row is filled before anything else, and GE and elective classes
from your record are shared out among the rows you didn't mark, so a class is never used up on a row
you already checked.

Usage: python3 flowchart-mark-done-2026-10-09.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')

# ---- planner.js: the ledger knows your marks ----------------------------------------------------
pf = root / 'app' / 'planner.js'
p = pf.read_text()
if 'flowchart-mark-done (2026-10-09)' in p:
    sys.exit('already patched')

def onep(old, new):
    global p
    n = p.count(old)
    assert n == 1, ('planner', n, old[:90])
    p = p.replace(old, new)

onep("""  var myWaived = {};           // class_waivers: code -> reason""",
     """  var myWaived = {};           // class_waivers: code -> reason
  var myMarks = {};            // flowchart rows checked off by the student: slot id -> the row's words (flowchart-mark-done (2026-10-09))""")
onep("""      if (o.waived) myWaived = Object.assign({}, o.waived);""",
     """      if (o.waived) myWaived = Object.assign({}, o.waived);
      if (o.marks) { myMarks = {}; o.marks.forEach(function (m) { if (m && m.slot != null) myMarks[String(m.slot)] = String(m.label || ''); }); }""")
onep("""    var uc = uncodedSatisfied(mm, completedCodes(), myClasses.slice());""",
     """    /* A row the student checked off (no class to log, or one we can't check) is done before anything else.
       Only on the row it was made on: its words must still match. GE and elective classes on the record
       are shared out among the other rows, so none is spent on a row already checked. */
    var marked = function (sl) {
      if (!sl || sl.id == null || !Object.prototype.hasOwnProperty.call(myMarks, String(sl.id))) return false;
      if (sl.code && slotCheckable(sl)) return false;
      return myMarks[String(sl.id)] === String(sl.title || '');
    };
    var mmU = Object.assign({}, mm, { terms: (mm.terms || []).map(function (t) { return Object.assign({}, t, { slots: (t.slots || []).filter(function (sl) { return !(marked(sl) && !sl.code); }) }); }) });
    var uc = uncodedSatisfied(mmU, completedCodes(), myClasses.slice());""")
onep("""        grid[ti].slots.push(cell);
        if (!slotCheckable(sl)) {""",
     """        grid[ti].slots.push(cell);
        if (marked(sl)) {
          var rowM;
          /* an unchosen concentration's row has no name of its own ("Choose a concentration above…" is its note) */
          if (isConc) { if (!rows.conc) { var cnM = sl.code ? String(sl.note || '').replace(/\\s*concentration\\s*$/i, '') : ''; rows.conc = { label: (cnM ? cnM + ' concentration' : 'Concentration'), f: 0, t: 0, n: 0 }; } rowM = rows.conc; }
          else rowM = sl.code || sl.type === 'course' ? rows.major : (sl.type === 'ge' ? rows.ge : rows.el);
          rowM.n++; rowM.f++; cell.state = 'done'; cell.mine = true; done.push({ title: sl.title || '', code: '' });
          return;
        }
        if (!slotCheckable(sl)) {""")
# a coded concentration row met after a marked unnamed one still names the row
onep("""          if (isConc) { if (!rows.conc) { var cn = String(sl.note || '').replace(/\\s*concentration\\s*$/i, ''); rows.conc = { label: (cn ? cn + ' concentration' : 'Concentration'), f: 0, t: 0, n: 0 }; } row = rows.conc; }""",
     """          if (isConc) { var cn = String(sl.note || '').replace(/\\s*concentration\\s*$/i, ''); if (!rows.conc) { rows.conc = { label: (cn ? cn + ' concentration' : 'Concentration'), f: 0, t: 0, n: 0 }; } else if (rows.conc.label === 'Concentration' && cn) rows.conc.label = cn + ' concentration'; row = rows.conc; }""")
pf.write_text(p)
print('patched', pf)

# ---- index.html: store, sync, the circle --------------------------------------------------------
f = root / 'app' / 'index.html'
s = f.read_text()

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, ('index', n, old[:90])
    s = s.replace(old, new)

# the store: this phone first, the account when the table is there
one("""TC.loadWaivers = async function () {""",
"""/* Flowchart rows checked off by you (flowchart-mark-done (2026-10-09)): { major, slot, label } per row, in
   public.flowchart_marks; on this phone too, so a mark made offline or before the table exists goes up
   at the next load. */
const MARKS_KEY = () => 'tc-marks:' + ((TC.user && TC.user.id) || '');
const markOk = m => !!(m && typeof m.major === 'string' && m.major.length >= 1 && m.major.length <= 120 && /^[A-Za-z0-9_.:-]{1,80}$/.test(String(m.slot || '')));
const markClean = m => ({ major: m.major, slot: String(m.slot), label: String(m.label || '').slice(0, 160) });
const markKey = m => m.major + '\\u0001' + m.slot;
/* ops: the changes this phone made that the account hasn't confirmed, oldest first, one per row (the
   newest wins). Only those are ever sent: a phone never deletes a mark it didn't remove itself. */
const applyMarkOps = (list, ops) => { let out = list.slice(); ops.forEach(o => { out = out.filter(x => markKey(x) !== markKey(o.m)); if (o.on) out.push(o.m); }); return out; };
function marksKeep() { try { localStorage.setItem(MARKS_KEY(), JSON.stringify({ list: TC.marks || [], ops: TC.markOps || [] })); } catch (e) {} }
TC.loadMarks = async function () {
  let c = null; try { c = JSON.parse(localStorage.getItem(MARKS_KEY()) || 'null'); } catch (e) {}
  TC.markOps = c && Array.isArray(c.ops) ? c.ops.filter(o => o && markOk(o.m)).map(o => ({ on: !!o.on, m: markClean(o.m) })) : [];
  TC.marks = c && Array.isArray(c.list) ? c.list.filter(markOk).map(markClean) : [];
  let r; try { r = await TC.client().from('flowchart_marks').select('major,slot_id,label').eq('user_id', TC.user.id); } catch (e) { r = { error: { message: String(e) } }; }
  if (r.error) { TC.err.marks = schemaGap(r.error) ? 'missing' : (r.error.message || 'error'); return; }
  delete TC.err.marks;
  const server = (r.data || []).map(x => ({ major: x.major, slot: String(x.slot_id), label: x.label || '' })).filter(markOk).map(markClean);
  TC.marks = applyMarkOps(server, TC.markOps); marksKeep();
  if (TC.markOps.length) await TC.pushMarks();
};
/* one change to the account: the row is replaced, never kept stale (a mark made again rewrites its words) */
async function markSend(o) {
  const me = TC.user.id, m = o.m;
  try {
    const d = await TC.client().from('flowchart_marks').delete().eq('user_id', me).eq('major', m.major).eq('slot_id', m.slot);
    if (d.error) return d.error;
    if (!o.on) return null;
    const q = await TC.client().from('flowchart_marks').insert({ user_id: me, major: m.major, slot_id: m.slot, label: m.label });
    return q.error && q.error.code !== '23505' ? q.error : null;   /* 23505: another phone just added it */
  } catch (e) { return { message: String(e) }; }
}
/* an op is the same change when it's the same row and the same way (copies made by a reload included) */
const sameOp = (a, b) => markKey(a.m) === markKey(b.m) && !!a.on === !!b.on;
TC.pushMarks = async function () {
  for (const o of (TC.markOps || []).slice()) {
    const e = await markSend(o);
    if (e) { if (schemaGap(e)) { TC.err.marks = 'missing'; return; } if (!e.code) return; continue; }   /* offline: stop; a refused row: keep it, send the rest */
    TC.markOps = (TC.markOps || []).filter(x => !sameOp(x, o)); marksKeep();
  }
};
TC.setMark = async function (major, slot, label, on) {
  const m = markClean({ major, slot, label });
  if (!markOk(m)) return 'Couldn’t mark that row.';
  const o = { on: !!on, m };
  TC.marks = applyMarkOps(TC.marks || [], [o]);
  TC.markOps = (TC.markOps || []).filter(x => markKey(x.m) !== markKey(m)).concat([o]);
  marksKeep();
  if (TC.err.marks === 'missing') return null;
  const e = await markSend(o);
  if (e) { if (schemaGap(e)) { TC.err.marks = 'missing'; return null; } return dbSay(e, 'Couldn’t save that to your account — it’s kept on this phone and goes up next time.'); }
  TC.markOps = (TC.markOps || []).filter(x => !sameOp(x, o)); marksKeep();
  if (TC.markOps.length) await TC.pushMarks();   /* older changes that didn't go up go now */
  return null;
};
TC.loadWaivers = async function () {""")

# the ledger gets them (your major's only)
one("""    history: TC.myHistory || [], classes: [...myCodes()], waived: TC.waived || {}, index: idx, names });""",
    """    history: TC.myHistory || [], classes: [...myCodes()], waived: TC.waived || {}, index: idx, names,
    marks: (TC.marks || []).filter(m => m.major === ((TC.profile && TC.profile.major) || '')) });""")
# loaded with the rest of the planner's inputs
one("""  await Promise.all([TC.myHistory ? null : TC.reloadHistory(), TC.waived ? null : TC.loadWaivers()]);""",
    """  await Promise.all([TC.myHistory ? null : TC.reloadHistory(), TC.waived ? null : TC.loadWaivers(), TC.marks ? null : TC.loadMarks()]);""")
one("""    Promise.all([TC.reloadMyReviews(), TC.loadPlanner(), TC.waived ? null : TC.loadWaivers(), TC.myHistory ? null : TC.reloadHistory()]).then(() => render(true));""",
    """    Promise.all([TC.reloadMyReviews(), TC.loadPlanner(), TC.waived ? null : TC.loadWaivers(), TC.myHistory ? null : TC.reloadHistory(), TC.marks ? null : TC.loadMarks()]).then(() => render(true));""")
one("""  if (window.TCPL && P.major && TC.waived && TC.myHistory) { plSync();""", """  if (window.TCPL && P.major && TC.waived && TC.myHistory && TC.marks) { plSync();""")
# the ledger's footnote
one("""Filled means a course on your record is placed against a requirement — Cal Poly’s degree audit decides what’s complete.""",
    """Filled means a course on your record is placed against a requirement, or a row you marked done — Cal Poly’s degree audit decides what’s complete.""")
one("""  retryPlanner: () => { TC._plTables = null; UI.pl = null; TC.myHistory = undefined; TC.waived = undefined;""",
    """  retryPlanner: () => { TC._plTables = null; UI.pl = null; TC.myHistory = undefined; TC.waived = undefined; TC.marks = undefined;""")
# deleting the account clears them from the phone too
one("""AUDIT_KEY(), PREFS_KEY(), PLDRAFT_KEY(), plSkipKey()].forEach(k => localStorage.removeItem(k));""",
    """AUDIT_KEY(), PREFS_KEY(), PLDRAFT_KEY(), plSkipKey(), MARKS_KEY()].forEach(k => localStorage.removeItem(k));""")

# the circle
one("""    const tickable = (s.state === 'need' && (s.code || s.choice)) || quick;
    const dot = tickable""",
    """    const tickable = (s.state === 'need' && (s.code || s.choice)) || quick;
    /* no class to log (a GE area, an elective) or one we can't check: the circle checks it off (flowchart-mark-done (2026-10-09)) */
    const markable = !tickable && !s.choice && (s.mine || s.state === 'cant' || (s.state === 'need' && !s.code));
    const what = s.choice ? s.title : code || title || s.title;
    const dot = markable
      ? `<button class="tc-dot tc-tick tc-mark" style="color:${c[1]};background:${c[2]}" data-a="plMark" data-x="${esc(s.id)}" aria-pressed="${!!s.mine}" aria-label="Mark ${esc(what)} done" ${(UI.busyMarks || {})[s.id] ? 'disabled' : ''}>${c[0]}</button>`
      : tickable""")
one("""${s.state === 'cant' && s.note ? `<span class="muted b" style="font-size:12px;display:block">${esc(s.note)}</span>` : ''}</${act ? 'button' : 'div'}></div>${pick}`;""",
    """${s.mine ? '<span class="b tc-mine" style="font-size:12px;display:block">Marked done by you</span>' : s.state === 'cant' && s.note ? `<span class="muted b" style="font-size:12px;display:block">${esc(s.note)}</span>` : ''}</${act ? 'button' : 'div'}></div>${pick}`;""")
one("""Tap the circle when you’ve taken a class. Tap a class to add its term, or a GE area to see this term’s classes for it.""",
    """Tap the circle when you’ve taken a class or finished a requirement. Tap a class to add its term, or a GE area to see this term’s classes for it.""")
one(""".tc-cell.need .tc-tick{box-shadow:inset 0 0 0 2px var(--muted)}""",
    """.tc-cell.need .tc-tick{box-shadow:inset 0 0 0 2px var(--muted)}
.tc-cell.cant .tc-mark{box-shadow:inset 0 0 0 2px var(--line2)}
.tc-mine{color:var(--teal-t,var(--teal))}""")

# the action
one("""  plTickCode: (code, id) => { UI.plPick = null; quickLog(code, id); },""",
    """  plTickCode: (code, id) => { UI.plPick = null; quickLog(code, id); },
  plMark: async id => {
    const major = (TC.profile && TC.profile.major) || ''; if (!major || !window.TCPL) return;
    UI.busyMarks = UI.busyMarks || {}; if (UI.busyMarks[id]) return;   /* one row at a time; other rows still take taps */
    plSync(); const L = TCPL.ledger(); const c = L && L.grid.flatMap(t => t.slots).find(x => String(x.id) === String(id)); if (!c) return;
    const on = !c.mine;
    if (on && !(c.state === 'cant' || (c.state === 'need' && !c.code && !c.choice))) return;
    UI.busyMarks[c.id] = 1;
    try {
      const p = TC.setMark(major, String(c.id), c.title, on);   /* the row changes at once; the account follows */
      render(true);
      const e = await p; if (e) toast(e);
    } finally { delete UI.busyMarks[c.id]; render(true); }
  },""")

f.write_text(s)
print('patched', f)
