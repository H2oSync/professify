#!/usr/bin/env python3
"""Three small changes (Tate, 2026-10-09).

1. Explore › Filters › Subject: "just have all, the persons major and GEs". The chips are All, your
   major's subject (the subject most of your flowchart's major classes carry, BUS for Business
   Administration), and GEs (classes that count toward a GE area). A subject you type in the search box
   still works. One already picked before this build stays visible, so you can clear it.
2. Rate: "when you click on a professor who your already rated make it so you can click and go to their
   page". A professor you've rated opens their page (before, a toast said you'd already reviewed them).
3. The review form: "if i click on the professors name in the review form it brings you to the professors
   page". Their photo and name open their page. Back returns to the form, with what you'd filled in.

Usage: python3 subject-filter-prof-links-2026-10-09.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'subject-filter-prof-links (2026-10-09)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# 1. the Subject chips
one("""function subjectsForFilter() {
  const count = {};
  [...myCodes()].concat(...TC.friends.map(f => personSecs(f).map(s => s.code))).forEach(c => { const s = c.split(' ')[0]; count[s] = (count[s] || 0) + 1; });
  const l = Object.keys(count).sort((a, b) => count[b] - count[a]).slice(0, 10);
  if (S.subj !== 'All' && l.indexOf(S.subj) < 0) l.unshift(S.subj);
  return ['All', ...l];
}""",
"""/* Explore's Subject filter (subject-filter-prof-links (2026-10-09)): All · your major · GEs.
   Your major's subject is the one most of its flowchart's major classes carry (BUS for Business
   Administration); with no flowchart, the commonest subject in your own classes. */
const MAJOR_SUBJ = {};
/* the GE list and the flowcharts live in planner.js: load it once, then draw again */
function needPlanner() { if (window.TCPL || TC._plWait || TC._plFailed) return; TC._plWait = 1; TC.loadPlanner().then(ok => { TC._plWait = 0; if (!ok) TC._plFailed = true; render(true); }); }
const subjOf = c => String(c || '').trim().toUpperCase().split(/[\\s/]+/)[0];   /* "CSC/CPE 1234" → CSC */
const topSubj = n => Object.keys(n).sort((a, b) => n[b] - n[a] || a.localeCompare(b))[0] || '';
/* your major's subject, from its flowchart — '' until that's here, or when TermChamp has no flowchart for it */
function majorSubj() {
  const m = (TC.profile && TC.profile.major) || ''; if (!m) return '';
  if (MAJOR_SUBJ[m] !== undefined) return MAJOR_SUBJ[m];
  if (!window.TCPL) { needPlanner(); return ''; }
  const n = {}, M = TCPL.majorFor(m);
  ((M && M.terms) || []).forEach(t => (t.slots || []).forEach(sl => { if (!sl || !sl.code || sl.type === 'ge') return; const sj = subjOf(sl.code); if (/^[A-Z&]{2,5}$/.test(sj)) n[sj] = (n[sj] || 0) + 1; }));
  return (MAJOR_SUBJ[m] = topSubj(n));
}
/* no flowchart: the subject most of your own classes carry stands in (not called your major) */
function mySubj() { const n = {}; [...myCodes()].forEach(c => { const sj = subjOf(c); n[sj] = (n[sj] || 0) + 1; }); return topSubj(n); }
/* a class counts toward a GE area (the planner's GE list) */
function isGeClass(code) {
  if (!window.TCPL) { needPlanner(); return false; }
  return (plGeMap().get(TCPL.canon(code) || code) || []).length > 0;
}
const subjLabel = c => c === 'GE' ? 'GEs' : c;
function subjectsForFilter() {
  const hasMajor = !!(TC.profile && TC.profile.major), waiting = hasMajor && !window.TCPL && !TC._plFailed;   /* no stand-in while the flowchart loads: the chip would change under you */
  const mj = majorSubj() || (waiting ? '' : mySubj()), l = ['All'].concat(mj ? [mj] : [], ['GE']);
  if (S.subj !== 'All' && l.indexOf(S.subj) < 0) l.splice(1, 0, S.subj);   /* one picked before stays, so it can be cleared */
  return l;
}""")
one("""${subjectsForFilter().map(c => `<button class="chip ${S.subj === c ? 'on' : ''}" style="${S.subj === c ? 'background:var(--blue)' : 'background:var(--bg)'}" data-a="setSubj" data-x="${c}">${esc(c)}</button>`).join('')}</div>
 <div class="hint" style="margin-top:8px">Or type any subject, like CSC, in the search box.</div>""",
    """${subjectsForFilter().map(c => `<button class="chip ${S.subj === c ? 'on' : ''}" style="${S.subj === c ? 'background:var(--blue)' : 'background:var(--bg)'}" data-a="setSubj" data-x="${esc(c)}" aria-pressed="${S.subj === c}">${esc(subjLabel(c))}</button>`).join('')}</div>
 <div class="hint" style="margin-top:8px">${majorSubj() ? `${esc(majorSubj())} is your major. ` : ''}GEs count toward a GE area. Or type any subject, like CSC, in the search box.</div>""")
one("""  if (S.subj !== 'All' && code.split(' ')[0] !== S.subj) return false;
  if (S.openOnly && !courseSeats(code).anyOpen) return false;""",
    """  if (S.subj === 'GE' ? !isGeClass(code) : S.subj !== 'All' && code.split(' ')[0] !== S.subj) return false;
  if (S.openOnly && !courseSeats(code).anyOpen) return false;""")
one("""  if (S.subj !== 'All' && !profCourses(pk).some(c => c.split(' ')[0] === S.subj)) return false;""",
    """  if (S.subj === 'GE' ? !profCourses(pk).some(isGeClass) : S.subj !== 'All' && !profCourses(pk).some(c => c.split(' ')[0] === S.subj)) return false;""")
one("""${S.subj !== 'All' ? `<span class="muted b" style="font-size:13px">${esc(S.subj)}</span>` : `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`}""",
    """${S.subj !== 'All' ? `<span class="muted b" style="font-size:13px">${esc(subjLabel(S.subj))}</span>` : `<span class="muted b" style="font-size:13px">${esc(CFG.TERM_LABEL)}</span>`}""")
one("""function emptyEx() { return S.savedOnly ?""",
    """function emptyEx() { if (S.subj === 'GE' && !window.TCPL) return TC._plFailed ? errCard('Couldn’t load the GE list.', 'retryGeList') : loadingCard('Loading GE classes…'); return S.savedOnly ?""")
one("""  setSubj: c => {""", """  retryGeList: () => { TC._plFailed = false; needPlanner(); render(true); },
  setSubj: c => {""")

# 2. Rate: a professor you've rated opens their page
one("""return `<button class="li" data-a="rateProf" data-x="${esc(pid)}" data-y="${code}">${profAv(pid, 46, 16)}""",
    """return `<button class="li" data-a="${r ? 'openProf' : 'rateProf'}" data-x="${esc(pid)}" data-y="${code}"${r ? ` aria-label="${esc(p.name)} · ${code} · you rated ${(+r.score).toFixed(1)} · open their page"` : ''}>${profAv(pid, 46, 16)}""")

# 3. the review form: their photo and name open their page
one("""  <div class="rf-head">${profAv(d.prof, 48, 16)}<div class="grow">${d.editing ? '<div class="eyebrow">EDIT YOUR REVIEW OF</div>' : ''}<div style="font-size:24px;font-weight:900;line-height:1.15">${esc(p.name)}</div></div><button class="xbtn" data-a="back" aria-label="Cancel">""",
    """  <div class="rf-head"><button class="rf-who" data-a="openProf" data-x="${esc(d.prof)}" aria-label="${esc(p.name)} — open their page" ${UI.busy.rate ? 'disabled' : ''}>${profAv(d.prof, 48, 16)}<span class="grow">${d.editing ? '<span class="eyebrow" style="display:block">EDIT YOUR REVIEW OF</span>' : ''}<span class="rf-name" style="display:block;font-size:24px;font-weight:900;line-height:1.15">${esc(p.name)}</span></span></button><button class="xbtn" data-a="back" aria-label="Cancel">""")
one(""".rf-head{display:flex;align-items:center;gap:12px;padding:16px 2px 16px}""",
    """.rf-head{display:flex;align-items:center;gap:12px;padding:16px 2px 16px}
.rf-who{flex:1;min-width:0;display:flex;align-items:center;gap:12px;background:none;border:0;padding:0;margin:0;text-align:left;color:inherit;font:inherit;cursor:pointer;border-radius:14px}
.rf-who .grow{flex:1;min-width:0}""")

# a second Rate for the professor whose form is already open (form → their page → Rate) goes back to that form
one("""    if (iReviewed(pid)) { toast('You’ve already reviewed ' + profName(pid)); return; }""",
    """    if (iReviewed(pid)) { toast('You’ve already reviewed ' + profName(pid)); return; }
    { const st = S.stack[S.tab] || [], fi = st.map(e => e.s).lastIndexOf('rateForm');
      if (fi >= 0 && S.draft && S.draft.prof === pid) { saveScroll(); st.length = fi + 1; UI.sheet = null; UI.champ = false; return render(); } }""")
f.write_text(s)
print('patched', f)
