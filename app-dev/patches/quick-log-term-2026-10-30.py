#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): the Builder's one-tap "I took this" inserted class_history with term null and
year null, but on production term and year are NOT NULL (part of the key) — every one-tap failed and fell back to
the Log a class sheet. The tap now files the class under the most recent finished term (Fall/Winter/Spring before
the term people are in now — the same default the Log a class sheet now starts on), and says which term in the
toast; the class sheet changes it. ✓ again (quickUnlog) takes off that row — or an older term-less one — and for a
class on the record any other way opens its class sheet instead of doing nothing."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
one("""/* One tap = this class is on your record, with no term (the history list files it under "Earlier"). */
async function quickLog(code, id) {""",
    """/* The term a class is filed under when nobody picked one: the most recent finished term — Fall, Winter or Spring
   (summer skipped) before the term people are in now. Log a class starts on it too. (2026-10-30) */
function lcDefault() {
  const m = String(nowTerm().label || '').match(/(Winter|Spring|Summer|Fall)\\s+(\\d{4})/);
  if (!m) return { term: 'Spring', year: new Date().getFullYear() };
  const t = m[1], y = +m[2];
  return t === 'Fall' ? { term: 'Spring', year: y } : t === 'Winter' ? { term: 'Fall', year: y - 1 } : t === 'Spring' ? { term: 'Winter', year: y } : { term: 'Spring', year: y };
}
/* The row a one-tap made (✓ again takes it off): lcDefault()'s term with no professor, or an older one with no term. */
function quickRowOf(code) {
  const dt = lcDefault(), rows = (TC.myHistory || []).filter(h => window.TCPL && TCPL.canon(h.code) === code);
  return rows.find(h => !h.term && !h.year) || rows.find(h => h.term === dt.term && +h.year === dt.year && !h.professor) || null;
}
/* One tap = this class is on your record, filed under lcDefault()'s term (production's class_history needs a term
   and a year: a term-less row is refused). The class sheet changes the term. */
async function quickLog(code, id) {""")
one("""  const r = await TC.client().from('class_history').insert({ user_id: TC.user.id, code, term: null, year: null, professor: null });""",
    """  const dt = lcDefault();
  const r = await TC.client().from('class_history').insert({ user_id: TC.user.id, code, term: dt.term, year: dt.year, professor: null });""")
one("""  if (r.error && (r.error.code === '23502' || /null value/i.test(r.error.message || ''))) { UI.lc = { code, err: 'Add the term you took it, then save.' }; UI.sheet = { type: 'logClass' }; return render(true); }""",
    """  if (r.error && (r.error.code === '23502' || r.error.code === '23505' || /null value|duplicate/i.test(r.error.message || ''))) { UI.lc = { code, err: 'Add the term you took it, then save.' }; UI.sheet = { type: 'logClass' }; return render(true); }""")
one("""  toast(fresh ? `${code} is on your record · tap ✓ to undo` : `${code} saved — pull down to refresh your record`);""",
    """  toast(fresh ? `${code} is on your record for ${dt.term} ${dt.year} · tap ✓ to undo` : `${code} saved — pull down to refresh your record`);""")
one("""  const row = (TC.myHistory || []).find(h => TCPL.canon(h.code) === code && !h.term && !h.year); if (!row) return;
  UI.busy.tick = id; render(true);
  const r = await TC.client().from('class_history').delete().eq('user_id', TC.user.id).eq('code', row.code).is('term', null).is('year', null);
  UI.busy.tick = 0;
  if (r.error) { toast(dbSay(r.error, 'Couldn’t undo that.')); return render(true); }
  await TC.reloadHistory(); loadRateList(); render(true);""",
    """  const rows = (TC.myHistory || []).filter(h => TCPL.canon(h.code) === code), row = quickRowOf(code);
  if (!row) { if (rows.length) { UI.sheet = { type: 'pcClass', key: pcKey(rows[0]) }; return render(true); } toast(`${code} counts from your degree report or a waiver`); return; }
  UI.busy.tick = id; render(true);
  let e = null; try { e = await TC.removeHistory(row.code, row); } catch (x) { e = 'Couldn’t undo that — check your connection.'; }
  UI.busy.tick = 0;
  if (e) { toast(e); return render(true); }
  render(true);""")
one("""  const quick = s.state === 'done' && s.by && (TC.myHistory || []).some(h => TCPL.canon(h.code) === s.by && !h.term && !h.year);""",
    """  const quick = s.state === 'done' && s.by && !!quickRowOf(s.by);   /* the one-tap's row, dated since 2026-10-30 */""")
one("""<option ${t === (f.term || 'Spring') ? 'selected' : ''}>${t}</option>""",
    """<option ${t === (f.term || lcDefault().term) ? 'selected' : ''}>${t}</option>""")
one("""<option ${v === (f.year || y) ? 'selected' : ''}>${v}</option>""",
    """<option ${v === (+f.year || lcDefault().year) ? 'selected' : ''}>${v}</option>""")
p.write_text(s); print('quick-log-term applied')
