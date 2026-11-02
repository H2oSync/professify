#!/usr/bin/env python3
"""Tate, 2026-10-31 (approved): "its easier to just pick the section from there". Right after a Degree Progress Report is
read and its in-progress classes are saved (this term's and next term's — the report has no section, class number or
time), a "Pick your sections" step: each class with its sections (days, times, professor + rating, seats, friends in it).
The app works out which combinations of sections don't overlap (with the student's other timed classes that term): exactly
one combination => it is pre-selected and one tap saves it; otherwise nothing is pre-selected (friends' sections are only a
label, never picked; a class with only one section is pre-selected — it's the only one, and anytime-fixes saves it anyway).
"Skip for now" leaves them in Anytime (the My Classes card reminds later). Works for the now-term (Fall) and the plan term
(Spring). Run after anytime-fixes-2026-10-31.py."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)

# while the report saves and its step is open, the quiet one-section saves wait (the step picks those too)
one("""    r.saveErr = null; UI.busy.dpr = 1; render(true);
    const notes = [];""", """    r.saveErr = null; UI.busy.dpr = 1; UI.dprPicking = 1; render(true);
    const notes = [];""")
one("""      UI.dprDiff = null;
      S.tab = 'schedule'; S.schedTab = 'planner'; save();""", """      UI.dprDiff = null;
      /* (2026-10-31) the report's classes for this term and next have no section yet: pick them now, then the sheet that was next */
      const pk = await dprPickBuild(r).catch(() => null);
      if (pk) UI.sheet = Object.assign(pk, { ret: UI.sheet });
      S.tab = 'schedule'; S.schedTab = 'planner'; save();""")
one("""    finally { UI.busy.dpr = 0; if (notes.length) toast(notes.join(' ')); render(true); }""",
    """    finally { UI.busy.dpr = 0; if (!(UI.sheet && UI.sheet.type === 'dprPick')) UI.dprPicking = 0; if (notes.length) toast(notes.join(' ')); render(true); if (!UI.dprPicking) anyTick(); }""")
# onboarding's last step: the step comes first, then "Who taught these?" or the notification ask, as before
one("""  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho') && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null); S.stack.home = [{ s: 'home' }]; UI.onbPre = null; UI.onbProgram = null; S.tab = 'schedule'; S.schedTab = 'planner'; save(); render(); if (UI.sheet && UI.sheet.type === 'pcWho') UI.sheet.onb = true; else setTimeout(() => onbAsks(), 600); }""",
    """  const pkOk = sh => !!sh && sh.type === 'dprPick' && (!sh.ret || sh.ret.type === 'pcWho');   /* (2026-10-31) */
  if (wasOnb && (!UI.sheet || UI.sheet.type === 'pcWho' || pkOk(UI.sheet)) && !(UI.dpr && UI.dpr.saveErr)) { onbRemember(null); S.stack.home = [{ s: 'home' }]; UI.onbPre = null; UI.onbProgram = null; S.tab = 'schedule'; S.schedTab = 'planner'; save(); render(); if (UI.sheet && (UI.sheet.type === 'pcWho' || UI.sheet.type === 'dprPick')) UI.sheet.onb = true; else setTimeout(() => onbAsks(), 600); }""")
# a tap outside / Escape on the step = Skip for now
one("""  closeSheet: () => { if (UI.sheet && UI.sheet.type === 'plPrefs' && !TC.prefs) return;""",
    """  closeSheet: () => { if (UI.sheet && UI.sheet.type === 'plPrefs' && !TC.prefs) return;
    if (UI.sheet && UI.sheet.type === 'dprPick') { A.dprPickSkip(); return; }   /* (2026-10-31) */""")

one(""".any-bfoot{display:grid;gap:8px;margin:14px 0 -20px;position:sticky;bottom:-20px;background:var(--card);padding:8px 0 20px}   /* over .sbody's 20px bottom padding */""",
    """.any-bfoot{display:grid;gap:8px;margin:14px 0 -20px;position:sticky;bottom:-20px;background:var(--card);padding:8px 0 20px}   /* over .sbody's 20px bottom padding */
/* (2026-10-31) the report's "Pick your sections" step */
.dpk-why{font-size:14px;font-weight:700;color:var(--any-mut);line-height:1.45;margin:10px 0 2px}
.dpk .dr-sub,.dpk .at-kick,.dpk .dr-link,.dpk-term{color:var(--any-mut)}
.dpk-term{font-size:12px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;margin:20px 2px 0}
.dpk-one{display:flex;gap:8px;align-items:center;margin-top:12px;padding:10px 12px;border-radius:14px;background:var(--teal-soft);color:var(--teal-t,var(--teal));font-size:13.5px;font-weight:900;line-height:1.35}
.dpk-c{padding:12px;margin-top:12px}
.dpk-h{display:flex;align-items:center;gap:8px;min-width:0;min-height:32px}
.dpk-h b{font-size:15px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.dpk-foot{margin-top:18px;position:sticky;bottom:0;background:var(--bg);padding:10px 0 4px}
.dpk-foot .dr-link{height:44px}""")

one("""/* "Send the link to my laptop" — from onboarding's last step and the empty Planner. */""",
    """/* ---- (2026-10-31) the report's "Pick your sections" step ----
   Combinations: one section per class, none overlapping each other or the student's other timed classes that term. Counted
   up to 2 (all that matters: exactly one or not); a search that runs too long counts as "not exactly one". */
function anyCombos(lists, fixed, budget) {
  let n = 0, first = null, steps = 0; const chosen = [], B = budget || 200000;
  const order = lists.map((l, i) => i).sort((a, b) => lists[a].length - lists[b].length);
  (function go(k) {
    if (n >= 2 || steps > B) return;
    if (k === order.length) { n++; if (!first) first = chosen.slice(); return; }
    const i = order[k];
    for (const x of lists[i]) {
      if (++steps > B || n >= 2) return;
      if (fixed.some(f => secClash(x, f)) || chosen.some(c => c && secClash(x, c))) continue;
      chosen[i] = x; go(k + 1); chosen[i] = undefined;
    }
  })(0);
  return { n: steps > B ? -1 : n, pick: first };
}
async function dprPickBuild(r) {
  if (!TC.ready || !TC.user) return null;
  const want = {};
  (r.rows || []).forEach(x => { if (x.skip || x.flag || !(x._now || x._next) || !x.cur) return; const t = String(x._now ? nowTerm().code : CFG.TERM); (want[t] = want[t] || []).includes(x.cur) || want[t].push(x.cur); });
  const groups = [];
  for (const t of Object.keys(want)) {
    if (t !== String(CFG.TERM)) await anyNowFetch(want[t]);
    relinkPeople();
    const m = anyMine(t); if (!m) continue;
    const unp = new Set(m.unplaced), one1 = new Set(m.secs.filter(x => x.oneSec).map(x => x.code));
    const classes = want[t].filter(c => unp.has(c) || one1.has(c)).map(c => ({ code: c, secs: anySecsOf(t, c) || [] })).filter(x => x.secs.length);
    if (!classes.length) continue;
    const fixed = m.secs.filter(x => onWeekSec(x) && !classes.some(c => c.code === x.code));
    const k = anyCombos(classes.map(c => c.secs), fixed), sel = {};
    if (k.n === 1) classes.forEach((c, i) => { sel[c.code] = String(k.pick[i].id); });
    else classes.forEach(c => { if (c.secs.length === 1) sel[c.code] = String(c.secs[0].id); });
    groups.push({ term: t, label: anyTermLabel(t), classes: classes.map(c => c.code), sel, unique: k.n === 1, combos: k.n });
  }
  return groups.length ? { type: 'dprPick', groups } : null;
}
SHEETS.dprPick = sh => {
  const all = sh.groups.reduce((n, g) => n + g.classes.length, 0), nSel = sh.groups.reduce((n, g) => n + Object.keys(g.sel).length, 0);
  const sub = sh.groups.map(g => g.label).join(' and ') + ' · ' + all + ' class' + (all === 1 ? '' : 'es');
  const busy = UI.busy.dpk ? ' disabled' : '';
  const grp = (g, gi) => {
    const m = anyMine(g.term) || { secs: [] }, fixed = m.secs.filter(x => onWeekSec(x) && !g.classes.includes(x.code));
    const chosen = g.classes.map(c => g.sel[c] && (anySecsOf(g.term, c) || []).find(x => String(x.id) === g.sel[c])).filter(Boolean);
    return `${sh.groups.length > 1 ? `<div class="dpk-term">${esc(g.label)}</div>` : ''}${g.unique && g.classes.some(c => (anySecsOf(g.term, c) || []).length > 1) ? `<div class="dpk-one">${ic('check', 14, 3)}<span>Only one set of sections fits together, so we picked it. Check it and save.</span></div>` : ''}${g.classes.map(c => {
      const secs = anySecsOf(g.term, c) || [];
      return `<div class="card dpk-c" role="group" aria-label="${esc(c)} sections"><div class="dpk-h"><span class="code">${esc(c)}</span><b>${esc(anyTitle(g.term, c))}</b></div>${secs.map(x => anySecBtn(x, { act: 'dprPickSec', x: gi + '|' + c + '|' + x.id, on: g.sel[c] === String(x.id), radio: true, fr: anyFriendsIn(g.term, x), clash: fixed.concat(chosen.filter(y => y.code !== c)).filter(y => secClash(x, y)), tag: secs.length === 1 ? 'Only section' : '', busy })).join('')}</div>`;
    }).join('')}`;
  };
  const allUnique = sh.groups.every(g => g.unique) && nSel === all;
  return `<div class="dr dpk"><div class="at-top"><span class="at-kick">DEGREE PROGRESS REPORT</span><button class="xbtn" data-a="dprPickSkip" aria-label="Skip for now">${ic('x', 16, 2.4)}</button></div>
  <h1 class="dr-h1">Pick your sections</h1><div class="dr-sub">${esc(sub)}</div>
  <div class="dpk-why">Your report doesn’t say which section you’re in. Tap yours and it goes on your week.</div>
  ${sh.groups.map(grp).join('')}${sh.err ? `<div class="tc-err" style="margin-top:12px">${esc(sh.err)}</div>` : ''}
  <div class="dr-foot dpk-foot"><button class="btn" data-a="dprPickSave"${nSel && !UI.busy.dpk ? '' : ' disabled'}>${UI.busy.dpk ? 'Saving…' : !nSel ? 'Tap a section to pick it' : allUnique ? 'Save these sections' : `Save ${nSel} section${nSel === 1 ? '' : 's'}`}</button><button class="dr-link" data-a="dprPickSkip"${busy}>Skip for now</button></div></div>`;
};
SHEETS.dprPick.full = true; SHEETS.dprPick.label = 'Pick your sections';
function dprPickClose(sh) {
  const ret = (sh && sh.ret) || null;
  if (ret && sh.onb && ret.type === 'pcWho') ret.onb = true;
  UI.sheet = ret; UI.dprPicking = 0; relinkPeople(); render(true);
  if (sh && sh.onb && !ret) setTimeout(() => onbAsks(), 600);
}
Object.assign(A, {
  dprPickSec: v => {
    const sh = UI.sheet; if (!sh || sh.type !== 'dprPick' || UI.busy.dpk) return;
    const [gi, code, id] = String(v || '').split('|'), g = sh.groups[+gi]; if (!g || !g.classes.includes(code)) return;
    if (g.sel[code] === id) delete g.sel[code]; else g.sel[code] = id;
    render(true);
  },
  dprPickSkip: () => { const sh = UI.sheet; if (!sh || sh.type !== 'dprPick' || UI.busy.dpk) return; dprPickClose(sh); toast('They’re in My Classes with no times — add them any time'); },
  dprPickSave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'dprPick' || UI.busy.dpk) return;
    UI.busy.dpk = 1; sh.err = ''; render(true);
    let n = 0, err = null;
    try {
      for (const g of sh.groups) {
        const plan = g.term === String(CFG.TERM);
        for (const c of g.classes) {
          const id = g.sel[c]; if (!id || err) continue;
          const x = (anySecsOf(g.term, c) || []).find(y => String(y.id) === id); if (!x) continue;
          err = plan ? await TC.addMySection(x, { hadSaved: true }) : await TC.setNowSection(x);
          if (!err) { n++; delete g.sel[c]; g.classes = g.classes.filter(y => y !== c); }
        }
      }
    } catch (e) { err = 'Couldn’t save that — check your connection.'; } finally { UI.busy.dpk = 0; }
    UI.storyOrder = null;
    if (err) { sh.groups = sh.groups.filter(g => g.classes.length); sh.err = err + (n ? ` (${n} saved)` : ''); if (!sh.groups.length) dprPickClose(sh); else { relinkPeople(); render(true); } return; }
    dprPickClose(sh); toast(`${n} class${n === 1 ? '' : 'es'} on your week`);
  }
});
/* "Send the link to my laptop" — from onboarding's last step and the empty Planner. */""")
p.write_text(s); print(p, 'dpr-pick-sections applied')
