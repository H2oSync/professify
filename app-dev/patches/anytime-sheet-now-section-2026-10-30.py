#!/usr/bin/env python3
r"""2026-10-30 (stuck/can't edit pass), Tate: classes the Degree Progress Report saved "can't be edited".
1. A class on My Classes with no section (the Anytime chip) opened its class page, and that was a dead end: no way to
   take it off My Classes, and a class not offered that term ("BUS 4999 isn't offered in Fall 2026") had nothing on
   it at all. The chip now opens a small sheet: the class's name and term, Pick a time (this term: its class page,
   where + adds a section) — or, for the term people are in now, its sections right there, each one "this is
   mine" — and Remove from My Classes (with Undo), offered or not.
2. The term people are in now (NOW_TERM, Fall 2026 while Spring is the term you choose in) could never get a
   section: its class pages and section sheets only had View class (Add to your week is TERM-only by design). A
   now-term section's sheet — for a class on your Fall list — now has "This is my section" (or "Switch to this section" / "Keep both" when the class
   already has one), writing my_sections under nowTerm().code with an upsert on user_id,class_nbr,term (the class
   saved under that term too, upsert on user_id,code,term), and "Remove from My Classes" / "Remove this section"
   once it's yours. The section goes straight into NOW_SEC, so stories, rings and "free now" (nowSecs) use it at
   once. TC.removeMyClass takes an optional term."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
# --- data: removeMyClass in any term; the now-term section; undo in any term
one(r"""TC.removeMyClass = async function (code) {
  const sb = TC.client(), me = TC.user.id;
  const a = await sb.from('saved_classes').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', code);
  if (a.error) return dbSay(a.error, 'Couldn’t remove ' + code + '.');
  await sb.from('my_sections').delete().eq('user_id', me).eq('term', CFG.TERM).eq('code', code);
  await loadMine(); return null;
};""",
    r"""TC.removeMyClass = async function (code, term) {
  const sb = TC.client(), me = TC.user.id, t = term || CFG.TERM;   /* term: another My Classes term (2026-10-30) */
  const a = await sb.from('saved_classes').delete().eq('user_id', me).eq('term', t).eq('code', code);
  if (a.error) return dbSay(a.error, 'Couldn’t remove ' + code + '.');
  await sb.from('my_sections').delete().eq('user_id', me).eq('term', t).eq('code', code);
  await loadMine(); return null;
};
/* (2026-10-30) One class's rows in any My Classes term, for an Undo; and putting them back (TC.restoreMyCode's rule:
   the old rows go back first, then only the number the change added comes out). */
function mineSnapIn(code, term) {
  if (!term || term === CFG.TERM) return mineSnap(code);
  const M = splitTerms() && term === nowTerm().code ? TC.nowMineRows : TC.termMine[term];
  return { saved: !!M && (M.saved || []).includes(code), rows: ((M && (M.secs || M.rows)) || []).filter(r => canonCode(r.code) === code).map(r => Object.assign({}, r)) };
}
TC.restoreMyCodeIn = async function (code, term, snap, added) {
  if (!term || term === CFG.TERM) return TC.restoreMyCode(code, snap, added);
  const sb = TC.client(), me = TC.user.id;
  const back = snap.rows.filter(x => x.class_nbr != null && String(x.class_nbr) !== '');
  let r = { error: null };
  for (const x of back) {
    r = await sb.from('my_sections').upsert({ user_id: me, term, code: x.code, class_nbr: String(x.class_nbr), section: x.section == null ? null : x.section, instructor: x.instructor == null ? null : x.instructor, days: x.days == null ? null : x.days, status: x.status || 'enrolled', wl_pos: x.wl_pos == null ? null : x.wl_pos }, { onConflict: 'user_id,class_nbr,term' });
    if (r.error) break;
  }
  if (!r.error && added && !back.some(x => String(x.class_nbr) === String(added))) r = await sb.from('my_sections').delete().eq('user_id', me).eq('term', term).eq('code', code).eq('class_nbr', String(added));
  if (!r.error) r = snap.saved ? await sb.from('saved_classes').upsert({ user_id: me, term, code }, { onConflict: 'user_id,code,term' }) : await sb.from('saved_classes').delete().eq('user_id', me).eq('term', term).eq('code', code);
  await loadMine(); return r.error ? dbSay(r.error, 'Couldn’t undo that.') : null;
};
/* (2026-10-30) "This is my section" in the term people are in now (a Degree Progress Report saves those classes with
   no section). The row goes under nowTerm().code; o.swap: the class's other section numbers that term, taken out. */
TC.setNowSection = async function (s, o) {
  o = o || {};
  const sb = TC.client(), me = TC.user.id, t = nowTerm().code, nbr = String((s && s.nbr) || '');
  if (!splitTerms() || !nbr || (s.nowTerm && s.nowTerm !== t)) return 'That section isn’t in ' + nowTerm().label + '.';
  let r = await sb.from('saved_classes').upsert({ user_id: me, term: t, code: s.code }, { onConflict: 'user_id,code,term' });
  if (r.error) return dbSay(r.error, 'Couldn’t save ' + s.code + '.');
  r = await sb.from('my_sections').upsert({ user_id: me, term: t, code: s.code, class_nbr: nbr, section: s.sec || null, instructor: s.instructor || null, days: s.rawDays || null, status: 'enrolled', wl_pos: null }, { onConflict: 'user_id,class_nbr,term' });
  if (r.error) { await loadMine(); return dbSay(r.error, 'Couldn’t save that section.'); }
  /* known at once: stories, rings and "free now" read nowSecs, which looks the number up here */
  if (!NOW_SEC_TERM || NOW_SEC_TERM === t) { NOW_SEC_TERM = t; NOW_SEC[nbr] = s; }
  for (const old of (o.swap || [])) {
    if (String(old) === nbr) continue;
    const d = await sb.from('my_sections').delete().eq('user_id', me).eq('term', t).eq('code', s.code).eq('class_nbr', String(old));
    if (d.error) { await loadMine(); return dbSay(d.error, 'Saved, but your other section is still there — remove it from its sheet.'); }
  }
  UI.storyOrder = null;
  await loadMine(); return null;
};
TC.removeNowSection = async function (code, nbr) {
  const sb = TC.client(), me = TC.user.id, t = nowTerm().code;
  const r = await sb.from('my_sections').delete().eq('user_id', me).eq('term', t).eq('code', code).eq('class_nbr', String(nbr));
  if (r.error) return dbSay(r.error, 'Couldn’t remove that section.');
  UI.storyOrder = null;
  await loadMine(); return null;
};""")
# --- the Anytime chip opens the sheet
one(r"""    .concat((unplaced || []).filter(c => !secs.some(s => s.code === c)).map(c => `<button class="any-c" data-a="openClass" data-x="${esc(c)}"${o.now ? ' data-y="now"' : ''} aria-label="${esc(c)}">${anyCodeHtml(c)}</button>`));""",
    r"""    .concat((unplaced || []).filter(c => !secs.some(s => s.code === c)).map(c => `<button class="any-c" data-a="anySheet" data-x="${esc(c)}"${o.now ? ' data-y="now"' : ''} aria-label="${esc(c)}">${anyCodeHtml(c)}</button>`));""")
# --- the sheets
one(r"""SHEETS.sec = sh => { const { code, id } = sh;""",
    r"""/* (2026-10-30) A My Classes class with no section: its name and term, a way to give it a time, and Remove. */
SHEETS.anyClass = sh => {
  const { code, term } = sh, now = splitTerms() && term === nowTerm().code, choose = !now && term === CFG.TERM;
  const L = now ? nowTerm().label : choose ? CFG.TERM_LABEL : ((myTerms().find(t => t.code === term) || {}).label || 'this term');
  const st = !now ? 'done' : nowAllReady() ? 'done' : NOWT.term === term ? NOWT.codes[code] : undefined;
  const list = now ? (NOWT.byCode[code] || []).slice().sort((a, b) => String(a.sec).localeCompare(String(b.sec), undefined, { numeric: true })) : choose ? secsOf(code) : [];
  const title = (now ? ((NOWT.courses[code] || {}).title || NOW_TITLES[code]) : '') || courseName(code) || ((COURSES[code] || {}).title !== code && (COURSES[code] || {}).title) || '';
  const off = (st === 'done' || !now) && !list.length && (now || choose);
  const busy = UI.busy.nm || UI.busy.anyRm ? ' disabled' : '';
  const rows = now && list.length ? `<div class="sec-h" style="padding:16px 2px 6px;font-size:16px"><span>Which section are you in?</span></div>${list.map(x => {
      const when = x.async ? 'Online, self-paced' : x.noTime ? 'Time not posted' : daysLabel(x.days) + ' ' + range(x);
      return `<button class="secrow nowrow any-pick" data-a="nowMine" data-x="${esc(x.id)}" aria-label="${esc((x.sec ? secLabel(x.sec) + ', ' : '') + when + ', ' + profName(x.prof) + ' — this is my section')}"${busy}>${secRowT(x)}<span class="muted b" style="font-size:13px">${esc(profName(x.prof))}</span><span class="pbtn" style="height:32px;padding:0 12px;font-size:13px">Mine</span></button>`; }).join('')}` : '';
  const wait = now && st !== 'done' && st !== 'err' ? `<div class="muted b" style="margin-top:14px;font-size:14px">Looking up ${esc(code)}’s ${esc(L)} sections…</div>`
    : now && st === 'err' ? `<div class="muted b" style="margin-top:14px;font-size:14px">Couldn’t load ${esc(code)}’s ${esc(L)} sections. <button class="link b" style="font-size:14px;padding:10px 4px;margin:-10px 0" data-a="anyRetry">Try again</button></div>` : '';
  const why = off ? `<div class="sec-fill no" style="margin-top:14px">${esc(code)} isn’t offered in ${esc(L)}, so it can’t get a time here.</div>` : '';
  return `<div class="row sb"><span class="code">${esc(code)}</span><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
 <h3 style="margin-top:10px">${esc(title || code)}</h3><div class="b secwhen" style="margin-top:4px;font-size:14px"><span class="secterm">${esc(L)}</span> · <span class="muted">In My Classes · no section yet</span></div>
 ${why}${wait}${rows}
 <div style="display:grid;gap:8px;margin-top:18px">${choose && list.length ? `<button class="btn" data-a="openClass" data-x="${esc(code)}">Pick a time</button>` : ''}${now && list.length ? `<button class="btn soft" data-a="openClass" data-x="${esc(code)}" data-y="now">View class</button>` : ''}
 <button class="btn soft" style="color:var(--red-ink)" data-a="anyRemove"${busy}>${UI.busy.anyRm ? 'Removing…' : 'Remove from My Classes'}</button></div>`;
};
/* (2026-10-30) a now-term section's sheet: this is mine / switch / keep both, or remove it once it's yours */
function nowSecActs(code, id, s) {
  if (!isNowSecId(id) || !TC.user || !TC.nowMineRows || TC.err.nowMine) return '';
  const mineN = nowSecs('me').filter(x => x.code === code), isMine = mineN.some(x => x.id === id || (s.nbr && x.nbr === s.nbr));
  const busy = UI.busy.nm ? ' disabled' : '';
  if (isMine) return `<div class="muted b" style="font-size:14px;text-align:center">${ic('check', 14, 3)} Your ${esc(nowTerm().label)} section</div><button class="btn soft" style="color:var(--red-ink)" data-a="nowSecRm" data-x="${esc(id)}"${busy}>${mineN.length > 1 ? 'Remove this section' : 'Remove from My Classes'}</button>`;
  /* only for a class on your list for that term (a friend's class you're not in keeps its plain sheet) */
  if (!s.nbr || String(id).startsWith('xn:') || !nowCodes().has(code)) return '';
  if (mineN.length) return `<button class="btn" data-a="nowMine" data-x="${esc(id)}"${busy}>Switch to this section</button><button class="at-alt" style="margin-top:-4px" data-a="nowMine" data-x="${esc(id)}" data-y="keep"${busy}>Keep both — add as another section</button>`;
  return `<button class="btn" data-a="nowMine" data-x="${esc(id)}"${busy}>This is my section</button>`;
}
SHEETS.sec = sh => { const { code, id } = sh;""")
one(r"""  const termTag = splitTerms() ? `<span class="secterm">${esc(isNowSecId(id) ? nowTerm().label : CFG.TERM_LABEL)}</span> · ` : '';""",
    r"""  const termTag = splitTerms() ? `<span class="secterm">${esc(isNowSecId(id) ? nowTerm().label : CFG.TERM_LABEL)}</span> · ` : '';
  const nowActs = nowSecActs(code, id, s);""")
one(r""" <div style="display:grid;gap:8px;margin-top:18px">${sh.fill && !inP && SEC[id] ? `<button class="btn" data-a="addPlanSheet" data-x="${esc(id)}">Add to a plan</button>` : ''}<button class="btn${sh.fill && !inP && SEC[id] ? ' soft' : ''}" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>View class</button>""",
    r""" <div style="display:grid;gap:8px;margin-top:18px">${nowActs}${sh.fill && !inP && SEC[id] ? `<button class="btn" data-a="addPlanSheet" data-x="${esc(id)}">Add to a plan</button>` : ''}<button class="btn${(sh.fill && !inP && SEC[id]) || nowActs ? ' soft' : ''}" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>View class</button>""")
# --- the actions
one(r"""  secSheet: (code, id) => {""",
    r"""  /* (2026-10-30) the Anytime chip's sheet, and the now-term section's "this is mine" */
  anySheet: (code, y) => {
    if (!code) return;
    const term = y === 'now' && splitTerms() ? nowTerm().code : ((mineTerm() || {}).code || CFG.TERM);
    UI.champ = false; UI.sheet = { type: 'anyClass', code, term };
    if (splitTerms() && term === nowTerm().code && !nowAllReady()) loadNowCode(code);
    render(true);
  },
  anyRetry: () => { const sh = UI.sheet; if (!sh || sh.type !== 'anyClass') return; if (NOWT.codes[sh.code] === 'err') delete NOWT.codes[sh.code]; loadNowCode(sh.code); render(true); },
  anyRemove: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'anyClass' || UI.busy.anyRm) return;
    const { code, term } = sh, snap = mineSnapIn(code, term);
    UI.busy.anyRm = 1; render(true);
    let err = null; try { err = await TC.removeMyClass(code, term); } catch (e) { err = 'Couldn’t remove that — check your connection.'; } finally { UI.busy.anyRm = 0; }
    if (err) { toast(err); return render(true); }
    if (UI.sheet === sh) UI.sheet = null;
    relinkPeople(); render(true);
    toastUndo(`Removed ${code} from My Classes`, async () => { const e = await TC.restoreMyCodeIn(code, term, snap, null); relinkPeople(); render(true); toast(e || 'Undone'); });
  },
  nowMine: async (id, y) => {
    if (UI.busy.nm || !splitTerms()) return;
    const s = NOWT.sec[id] || Object.values(NOW_SEC).find(x => x && x.id === id); if (!s || !s.nbr) return;
    const t = nowTerm().code, snap = mineSnapIn(s.code, t);
    const swap = y === 'keep' ? [] : snap.rows.filter(r => r.class_nbr != null && String(r.class_nbr) !== '' && String(r.class_nbr) !== String(s.nbr)).map(r => String(r.class_nbr));
    const sh0 = UI.sheet; UI.busy.nm = 1; render(true);
    let err = null; try { err = await TC.setNowSection(s, { swap }); } catch (e) { err = 'Couldn’t save that — check your connection.'; } finally { UI.busy.nm = 0; }
    if (err) { toast(err); return render(true); }
    if (UI.sheet === sh0) UI.sheet = null;
    relinkPeople(); render(true);
    toastUndo(`${s.code}${secLabel(s.sec) ? ' ' + secLabel(s.sec) : ''} is your ${nowTerm().label} section`, async () => { const e = await TC.restoreMyCodeIn(s.code, t, snap, s.nbr); relinkPeople(); render(true); toast(e || 'Undone'); });
  },
  nowSecRm: async id => {
    if (UI.busy.nm || !splitTerms()) return;
    const mine = nowSecs('me'), s = mine.find(x => x.id === id) || NOWT.sec[id]; if (!s) return;
    const t = nowTerm().code, snap = mineSnapIn(s.code, t), n = mine.filter(x => x.code === s.code).length, nbr = s.nbr || String(id).split(':').pop();
    const sh0 = UI.sheet; UI.busy.nm = 1; render(true);
    let err = null; try { err = n > 1 ? await TC.removeNowSection(s.code, nbr) : await TC.removeMyClass(s.code, t); } catch (e) { err = 'Couldn’t remove that — check your connection.'; } finally { UI.busy.nm = 0; }
    if (err) { toast(err); return render(true); }
    if (UI.sheet === sh0) UI.sheet = null;
    relinkPeople(); render(true);
    toastUndo(n > 1 ? `Removed that ${s.code} section` : `Removed ${s.code} from My Classes`, async () => { const e = await TC.restoreMyCodeIn(s.code, t, snap, null); relinkPeople(); render(true); toast(e || 'Undone'); });
  },
  secSheet: (code, id) => {""")
# --- the section rows in the sheet's list
one(r""".secterm{color:var(--ink3)}""",
    r""".secterm{color:var(--ink3)}
.secrow.any-pick{width:100%;display:grid;grid-template-columns:1fr auto;align-items:center;gap:2px 10px;text-align:left}
.secrow.any-pick .t{grid-column:1}.secrow.any-pick .muted{grid-column:1}.secrow.any-pick .pbtn{grid-column:2;grid-row:1 / span 2}""")
p.write_text(s); print('anytime-sheet-now-section applied')
