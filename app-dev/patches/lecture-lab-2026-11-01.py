#!/usr/bin/env python3
r"""2026-11-01: lecture + lab. Feedback (Tate): "make it so that people can select multiple sections when choosing their
classes because some classes have lecture + lab, and I couldnt pick two sections".

Cal Poly tags every section with its part ("01-LEC Regular", "02-LAB Regular", "C01-ACT", SEM, DIS, IND); about 520
courses a term have two or more parts. The phone treated a class as ONE section everywhere: Plans dropped the lecture
when the lab went in, My Classes offered to swap it, the Anytime / "which section are you in" / Degree Progress Report
pickers took one tap per class, and the section label hid the part ("Sec 02").

Now: one section PER PART. A swap only ever replaces the same part; every picker groups by part and keeps going until
each part has one; labels say "Sec 02 Lab"; class pages say what a multi-part class needs; a section sheet says which
part is still missing. Lecture and lab are never paired to each other (the feed has no associated-class number).
One-part classes look and behave exactly as before. Usage: <script> app/index.html"""
import sys
path = sys.argv[1]
s = open(path).read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if s.count(b) >= n and (c == 0 or a in b): return          # already applied
    assert c == n, (a[:90], c)
    s = s.replace(a, b)

# ---- A. helpers + the label --------------------------------------------------------------------------------------
rep(r"""function secLabel(v) { const t = String(v == null ? '' : v).trim().split(/[-\s]/)[0]; return /^\d/.test(t) ? 'Sec ' + t : t; }""",
r"""function secLabel(v) { const t = String(v == null ? '' : v).trim().split(/[-\s]/)[0]; return /^\d/.test(t) ? 'Sec ' + t : t; }
/* (2026-11-01) "Sec 11 Lab": the label plus its part, only for a class that has more than one part (a one-part class reads as before) */
function secLab(s) { const b = secLabel(s && s.sec), p = secPart(s); if (!b || !p || !s || !s.code) return b; const l = isNowSecId(s.id) || s.nowTerm ? (NOWT.byCode[s.code] || []) : secsOf(s.code); return multiPart(l) ? b + ' ' + partName(p) : b; }
/* (2026-11-01) Lecture + lab. A section's part, from Cal Poly's token ("02-LAB Regular" → LAB); '' when the row has no tag.
   A class has one section PER PART: a swap only replaces the same part, and every picker asks for one of each. */
const PART_NAME = { LEC: 'Lecture', LAB: 'Lab', ACT: 'Activity', SEM: 'Seminar', DIS: 'Discussion', IND: 'Independent study', SUP: 'Supervision', CLN: 'Clinical' };
const PART_ORDER = ['LEC', 'SEM', 'DIS', 'LAB', 'ACT', 'IND'];
function secPart(v) { const x = v && typeof v === 'object' ? (v.sec != null ? v.sec : v.section) : v; const m = String(x == null ? '' : x).trim().split(/\s/)[0].match(/-([A-Za-z]{2,4})$/); return m ? m[1].toUpperCase() : ''; }
const partName = p => PART_NAME[p] || (p ? p.charAt(0) + p.slice(1).toLowerCase() : 'Section');
function partsOf(list) { return [...new Set((list || []).map(x => secPart(x)))].sort((a, b) => ((PART_ORDER.indexOf(a) + 1) || 99) - ((PART_ORDER.indexOf(b) + 1) || 99) || a.localeCompare(b)); }
const multiPart = list => { const ps = partsOf(list); return ps.length > 1 && !ps.includes(''); };   /* an untagged row: not enough to say */
const samePart = (a, b) => secPart(a) === secPart(b);
/* the parts a class has that `held` (sections or rows) has none of; [] for a one-part class */
function partsMissing(list, held) { if (!multiPart(list)) return []; const h = new Set((held || []).map(x => secPart(x))); return partsOf(list).filter(p => !h.has(p)); }
function partsWords(ps) { const n = ps.map(p => partName(p).toLowerCase()); return n.length < 2 ? (n[0] || '') : n.slice(0, -1).join(', ') + ' and ' + n[n.length - 1]; }
const aPart = p => (/^[aeiou]/i.test(partName(p)) ? 'an ' : 'a ') + partName(p).toLowerCase();
/* a picker's sections under one heading per part ("Lab · pick 1"); a one-part class is one plain group */
function partGroups(list) { const ps = partsOf(list); return multiPart(list) ? ps.map(p => ({ p, name: partName(p), secs: list.filter(x => secPart(x) === p) })) : [{ p: '', name: '', secs: list }]; }
const partHead = (g, held) => g.p ? `<div class="mp-h"><span>${esc(g.name)}</span><small>${held ? ic('check', 12, 3.4) + ' picked' : 'pick 1'}</small></div>` : '';
/* "CHEM 1210 has a lecture and a lab. Add one of each." with a chip per part (✓ when held) — class pages */
function partsNote(code, list, held) {
  if (!multiPart(list)) return '';
  const ps = partsOf(list), h = new Set((held || []).map(x => secPart(x)));
  return `<div class="card mp-note" role="note"><div>${esc(code)} has ${esc(partsWords(ps))} sections. Add one of each.</div><div class="mp-parts">${ps.map(p => `<span class="mp-p${h.has(p) ? ' on' : ''}">${h.has(p) ? ic('check', 12, 3.4) + ' ' : ''}${esc(partName(p))}</span>`).join('')}</div></div>`;
}""")

# ---- A2. the part shows where sections are listed ------------------------------------------------------------------
rep("""const secRowT = s => `<span class="t"><b>${s.sec ? esc(secLabel(s.sec)) + ' ' : ''}""", """const secRowT = s => `<span class="t"><b>${s.sec ? esc(secLab(s)) + ' ' : ''}""")
rep("""  const nm = x => esc(x.code) + (secLabel(x.sec) ? ' ' + esc(secLabel(x.sec)) : '');""", """  const nm = x => esc(x.code) + (secLabel(x.sec) ? ' ' + esc(secLab(x)) : '');""")
rep("""<div class="at-code"><span>${esc(s.code)}</span>${secLabel(s.sec) ? `<span class="at-sec">${esc(secLabel(s.sec))}</span>` : ''}</div>""", """<div class="at-code"><span>${esc(s.code)}</span>${secLabel(s.sec) ? `<span class="at-sec">${esc(secLab(s))}</span>` : ''}</div>""")
rep("""  return `<div class="row sb"><span class="code">${code}${s.sec ? ' ' + esc(secLabel(s.sec)) : ''}</span>""", """  return `<div class="row sb"><span class="code">${code}${s.sec ? ' ' + esc(secLab(s)) : ''}</span>""")

# ---- B. styles ----------------------------------------------------------------------------------------------------
rep(""".dpk-c{padding:12px;margin-top:12px}""",
""".dpk-c{padding:12px;margin-top:12px}
.mp-note{margin:0 12px 12px;padding:12px 14px;font-size:14px;font-weight:700;line-height:1.4}
.mp-parts{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.mp-p{display:inline-flex;align-items:center;gap:4px;min-height:28px;padding:0 10px;border-radius:999px;border:1.5px solid var(--line);font-size:13px;font-weight:800;color:var(--muted)}
.mp-p.on{background:var(--blue-soft);border-color:transparent;color:var(--blue-ink)}
.mp-h{display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding:14px 2px 6px;font-size:15px;font-weight:900}
.mp-h small{display:inline-flex;align-items:center;gap:3px;font-size:12.5px;font-weight:800;color:var(--muted)}
.mp-left{margin-top:12px;font-size:14px;font-weight:800;color:var(--warn-ink,#9A5B00)}""")

# ---- C. overlaps: a lecture and its lab can clash with each other ---------------------------------------------------
rep("""s.s != null && sec.s != null && s.code !== sec.code && [...s.days]""", """s.s != null && sec.s != null && (s.code !== sec.code || !samePart(s, sec)) && [...s.days]""")
rep("""x.s != null && sec.s != null && x.code !== sec.code && [...x.days]""", """x.s != null && sec.s != null && (x.code !== sec.code || !samePart(x, sec)) && [...x.days]""")

# ---- D. Add to your week: only the same part is swapped ------------------------------------------------------------
rep("""    o.repl = o.inIt ? [] : others.filter(x => x.code === s.code);
    o.base = others.filter(x => x.code !== s.code || o.inIt);""",
"""    o.repl = o.inIt ? [] : others.filter(x => x.code === s.code && samePart(x, s));   /* a lab never pushes out the lecture (2026-11-01) */
    o.base = others.filter(x => x.code !== s.code || !samePart(x, s) || o.inIt);""")
rep("""    o.repl = o.inIt || sh.keepBoth ? [] : others.filter(x => x.code === s.code && atNbr(x));""",
"""    o.repl = o.inIt || sh.keepBoth ? [] : others.filter(x => x.code === s.code && samePart(x, s) && atNbr(x));""")
rep("""        const prev = (TC.plans[o.P] || []).slice(), had = prev.some(x => SEC[x] && SEC[x].code === s.code), gone = new Set(outs.map(x => x.id));
        TC.setPlan(o.P, prev.filter(x => !(SEC[x] && SEC[x].code === s.code) && !gone.has(x)).concat(sh.id)); S.plan = o.P;
        msg = rp ? 'Replaced ' + [...new Set(outs.map(x => x.code))].join(', ') + ' with ' + s.code + ' in Plan ' + o.P : (had ? 'Swapped ' : 'Added ') + s.code + (had ? ' in Plan ' : ' to Plan ') + o.P;""",
"""        const same = x => SEC[x] && SEC[x].code === s.code && samePart(SEC[x], s);
        const prev = (TC.plans[o.P] || []).slice(), had = prev.some(same), gone = new Set(outs.map(x => x.id));
        TC.setPlan(o.P, prev.filter(x => !same(x) && !gone.has(x)).concat(sh.id)); S.plan = o.P;
        msg = rp ? 'Replaced ' + [...new Set(outs.map(x => x.code))].join(', ') + ' with ' + s.code + ' in Plan ' + o.P : (had ? 'Swapped ' : 'Added ') + atPartNm(s) + (had ? ' in Plan ' : ' to Plan ') + o.P;""")
rep("""        msg = rp ? 'Replaced ' + gone.map(g => g.code).join(', ') + ' with ' + s.code : (swap.length ? 'Swapped ' : 'Added ') + s.code + (swap.length ? ' in My Classes' : ' to My Classes');""",
"""        msg = rp ? 'Replaced ' + gone.map(g => g.code).join(', ') + ' with ' + s.code : (swap.length ? 'Swapped ' : 'Added ') + atPartNm(s) + (swap.length ? ' in My Classes' : ' to My Classes');""")
rep("""    sh.phase = 'done'; sh.seq++; render(true);
    setTimeout(() => { if (UI.sheet === sh) { UI.sheet = null; render(true); setBars(false); } toastUndo(msg, undo); }, 900);""",
"""    sh.phase = 'done'; sh.seq++; render(true);
    { const left = atPartsLeft(o, s); if (left.length) msg += ' · now pick ' + aPart(left[0]); }   /* lecture + lab: say what's still missing */
    setTimeout(() => { if (UI.sheet === sh) { UI.sheet = null; render(true); setBars(false); } toastUndo(msg, undo); }, 900);""")
rep("""/* "Replace BUS 4448 with this class": the button on a clash (Tate, 2026-10-11) */""",
"""/* (2026-11-01) "CHEM 1210 Lab" for a section of a multi-part class, the code alone otherwise */
function atPartNm(s) { return s.code + (multiPart(secsOf(s.code)) && secPart(s) ? ' ' + partName(secPart(s)) : ''); }
/* the parts of s's class the destination will still be missing once s is in */
function atPartsLeft(o, s) {
  const all = secsOf(s.code); if (!multiPart(all)) return [];
  const have = o.P ? (TC.plans[o.P] || []).map(x => SEC[x]).filter(Boolean) : personSecs('me');
  return partsMissing(all, have.filter(x => x.code === s.code).concat([s]));
}
/* "Replace BUS 4448 with this class": the button on a clash (Tate, 2026-10-11) */""")
rep("""Swap ${o.repl.length > 1 ? 'them' : 'it'}, or keep both if one is a lab.""", """Swap ${o.repl.length > 1 ? 'them' : 'it'}, or keep both.""")
rep("""  if (sh.err && !adding) { note = esc(sh.err); tn = 'bad'; }
  const cls = ['addto',""",
"""  if (!o.other && !o.inIt && !sh.err) { const left = atPartsLeft(o, s); if (left.length) note += ` ${esc(s.code)} also needs ${esc(aPart(left[0]))}${left.length > 1 ? ' and ' + esc(partsWords(left.slice(1))) : ''} — add ${left.length > 1 ? 'those' : 'one'} next.`; }
  if (sh.err && !adding) { note = esc(sh.err); tn = 'bad'; }
  const cls = ['addto',""")

# ---- E. the term people are in now: "this is my section" per part ---------------------------------------------------
rep("""  const mineN = nowSecs('me').filter(x => x.code === code), isMine = mineN.some(x => x.id === id || (s.nbr && x.nbr === s.nbr));""",
"""  const mineA = nowSecs('me').filter(x => x.code === code), mineN = mineA.filter(x => samePart(x, s)), isMine = mineA.some(x => x.id === id || (s.nbr && x.nbr === s.nbr));""")
rep("""${mineN.length > 1 ? 'Remove this section' : 'Remove from My Classes'}</button>`;""", """${mineA.length > 1 ? 'Remove this section' : 'Remove from My Classes'}</button>`;""")
rep("""  return `<button class="btn" data-a="nowMine" data-x="${esc(id)}"${busy}>This is my section</button>`;
}""",
"""  if (mineA.length && secPart(s)) return `<button class="btn" data-a="nowMine" data-x="${esc(id)}" data-y="keep"${busy}>This is my ${esc(partName(secPart(s)).toLowerCase())} section</button>`;   /* the lab next to a lecture you have */
  return `<button class="btn" data-a="nowMine" data-x="${esc(id)}"${busy}>This is my section</button>`;
}""")
rep("""    const swap = y === 'keep' ? [] : snap.rows.filter(r => r.class_nbr != null && String(r.class_nbr) !== '' && String(r.class_nbr) !== String(s.nbr)).map(r => String(r.class_nbr));""",
"""    const swap = y === 'keep' ? [] : snap.rows.filter(r => r.class_nbr != null && String(r.class_nbr) !== '' && String(r.class_nbr) !== String(s.nbr) && (!r.section || secPart(r.section) === secPart(s))).map(r => String(r.class_nbr));   /* only the same part (2026-11-01) */""")
rep("""    if (UI.sheet === sh0) UI.sheet = null;
    relinkPeople(); render(true);
    toastUndo(`${s.code}${secLabel(s.sec) ? ' ' + secLabel(s.sec) : ''} is your ${nowTerm().label} section`,""",
"""    relinkPeople();
    const left = partsMissing(NOWT.byCode[s.code] || [], nowSecs('me').filter(x => x.code === s.code));
    if (UI.sheet === sh0 && !(sh0 && sh0.type === 'anyClass' && left.length)) UI.sheet = null;   /* the "which sections" sheet stays for the lab */
    render(true);
    toastUndo(`${s.code}${secLabel(s.sec) ? ' ' + secLab(s) : ''} is your ${nowTerm().label} section${left.length ? ' · now pick ' + aPart(left[0]) : ''}`,""")
rep("""  const rows = now && list.length ? `<div class="sec-h" style="padding:16px 2px 6px;font-size:16px"><span>Which section are you in?</span></div>${list.map(x => {
      const when = x.async ? 'Online, self-paced' : x.noTime ? 'Time not posted' : daysLabel(x.days) + ' ' + range(x);
      return `<button class="secrow nowrow any-pick" data-a="nowMine" data-x="${esc(x.id)}" aria-label="${esc((x.sec ? secLabel(x.sec) + ', ' : '') + when + ', ' + profName(x.prof) + ' — this is my section')}"${busy}>${secRowT(x)}<span class="muted b" style="font-size:13px">${esc(profName(x.prof))}</span><span class="pbtn" style="height:32px;padding:0 12px;font-size:13px">Mine</span></button>`; }).join('')}` : '';""",
"""  const held = now ? nowSecs('me').filter(x => x.code === code) : [], mp = multiPart(list);
  const rows = now && list.length ? `<div class="sec-h" style="padding:16px 2px 6px;font-size:16px"><span>${mp ? 'Which sections are you in?' : 'Which section are you in?'}</span></div>${mp ? `<div class="muted b" style="font-size:13.5px;margin:-2px 2px 0">${esc(code)} has ${esc(partsWords(partsOf(list)))} sections — pick one of each.</div>` : ''}${partGroups(list).map(g => partHead(g, held.some(h => samePart(h, g.secs[0]))) + g.secs.map(x => {
      const when = x.async ? 'Online, self-paced' : x.noTime ? 'Time not posted' : daysLabel(x.days) + ' ' + range(x), yours = held.some(h => h.nbr === x.nbr);
      return `<button class="secrow nowrow any-pick${yours ? ' on' : ''}" data-a="nowMine" data-x="${esc(x.id)}" aria-label="${esc((x.sec ? secLabel(x.sec) + ', ' : '') + when + ', ' + profName(x.prof) + (yours ? ' — your section' : ' — this is my section'))}"${busy}>${secRowT(x)}<span class="muted b" style="font-size:13px">${esc(profName(x.prof))}</span><span class="pbtn${yours ? ' soft' : ''}" style="height:32px;padding:0 12px;font-size:13px">${yours ? ic('check', 12, 3.4) + ' Yours' : 'Mine'}</span></button>`; }).join('')).join('')}` : '';""")
rep("""<span class="muted">In My Classes · no section yet</span>""",
"""<span class="muted">${held.length ? (partsMissing(list, held).length ? 'In My Classes · ' + esc(partsWords(partsMissing(list, held))) + ' still to pick' : 'In My Classes') : 'In My Classes · no section yet'}</span>""")

# ---- F. Anytime "Add times to your classes": a class stays until each part has one ---------------------------------
rep("""  return m.unplaced.filter(c => !sk.has(t + ':' + c)).map(c => ({ code: c, secs: anySecsOf(t, c) })).filter(x => x.secs && x.secs.length >= 2);""",
"""  const has = c => m.secs.filter(x => x.code === c), part = [...new Set(m.secs.map(x => x.code))].filter(c => !m.unplaced.includes(c));
  return m.unplaced.concat(part).filter(c => !sk.has(t + ':' + c)).map(c => ({ code: c, secs: anySecsOf(t, c), held: has(c) }))
    .filter(x => x.secs && (m.unplaced.includes(x.code) ? x.secs.length >= 2 : partsMissing(x.secs, x.held).length > 0));   /* + a lecture still missing its lab (2026-11-01) */""")
rep("""${x.secs.map(s2 => anySecBtn(s2, { act: 'anyChoose', x: t + '|' + x.code + '|' + s2.id, fr: anyFriendsIn(t, s2), clash: mine.filter(m => m.code !== s2.code && secClash(s2, m)), busy })).join('')}</div>`;""",
"""${partGroups(x.secs).map(g => { const hp = (x.held || []).filter(h => g.p && samePart(h, g.secs[0])); return partHead(g, hp.length) + g.secs.map(s2 => anySecBtn(s2, { act: 'anyChoose', x: t + '|' + x.code + '|' + s2.id, on: hp.some(h => String(h.id) === String(s2.id) || (h.nbr && h.nbr === s2.nbr)), radio: !!g.p, fr: anyFriendsIn(t, s2), clash: mine.filter(m => (m.code !== s2.code || !samePart(m, s2)) && secClash(s2, m)), busy })).join(''); }).join('')}</div>`;""")
rep("""    const snap = mineSnapIn(code, t); UI.busy.anyPick = 1; render(true);
    let e = null; try { e = plan ? await TC.addMySection(s, { hadSaved: true }) : await TC.setNowSection(s); } catch (x) { e = 'Couldn’t save that — check your connection.'; } finally { UI.busy.anyPick = 0; }""",
"""    const snap = mineSnapIn(code, t), m0 = anyMine(t), mineIn = ((m0 && m0.secs) || []).filter(x => x.code === code);
    if (mineIn.some(x => String(x.id) === String(s.id) || (x.nbr && x.nbr === s.nbr))) return;   /* already yours */
    const swap = mineIn.filter(x => samePart(x, s)).map(x => String(plan ? x.id : (x.nbr || String(x.id).split(':').pop())));   /* the same part only: the lecture stays when the lab goes in */
    UI.busy.anyPick = 1; render(true);
    let e = null; try { e = plan ? await TC.addMySection(s, { hadSaved: true, swap }) : await TC.setNowSection(s, { swap }); } catch (x) { e = 'Couldn’t save that — check your connection.'; } finally { UI.busy.anyPick = 0; }""")

# ---- G. Degree Progress Report "Pick your sections": one pick per part ----------------------------------------------
rep("""async function dprPickBuild(r) {""",
"""/* (2026-11-01) a pick slot: "CHEM 1210" for a one-part class, "CHEM 1210#LAB" for each part of a multi-part one */
const slotCode = k => String(k).split('#')[0], slotPart = k => String(k).split('#')[1] || '';
function slotSecs(t, k) { const l = anySecsOf(t, slotCode(k)) || []; return slotPart(k) ? l.filter(x => secPart(x) === slotPart(k)) : l; }
async function dprPickBuild(r) {""")
rep("""    const classes = want[t].filter(c => unp.has(c) || one1.has(c)).map(c => ({ code: c, secs: anySecsOf(t, c) || [] })).filter(x => x.secs.length);
    if (!classes.length) continue;
    const fixed = m.secs.filter(x => onWeekSec(x) && !classes.some(c => c.code === x.code));""",
"""    const classes = want[t].filter(c => unp.has(c) || one1.has(c)).map(c => ({ code: c, secs: anySecsOf(t, c) || [] })).filter(x => x.secs.length)
      .flatMap(c => multiPart(c.secs) ? partsOf(c.secs).map(p => ({ code: c.code + '#' + p, secs: c.secs.filter(x => secPart(x) === p) })) : [c]);   /* lecture + lab: a slot each */
    if (!classes.length) continue;
    const fixed = m.secs.filter(x => onWeekSec(x) && !classes.some(c => slotCode(c.code) === x.code));""")
rep("""  const all = sh.groups.reduce((n, g) => n + g.classes.length, 0), nSel = sh.groups.reduce((n, g) => n + Object.keys(g.sel).length, 0);
  const sub = sh.groups.map(g => g.label).join(' and ') + ' · ' + all + ' class' + (all === 1 ? '' : 'es');""",
"""  const all = sh.groups.reduce((n, g) => n + g.classes.length, 0), nSel = sh.groups.reduce((n, g) => n + Object.keys(g.sel).length, 0);
  const nCls = sh.groups.reduce((n, g) => n + new Set(g.classes.map(slotCode)).size, 0);
  const sub = sh.groups.map(g => g.label).join(' and ') + ' · ' + nCls + ' class' + (nCls === 1 ? '' : 'es');""")
rep("""    const m = anyMine(g.term) || { secs: [] }, fixed = m.secs.filter(x => onWeekSec(x) && !g.classes.includes(x.code));
    const chosen = g.classes.map(c => g.sel[c] && (anySecsOf(g.term, c) || []).find(x => String(x.id) === g.sel[c])).filter(Boolean);""",
"""    const m = anyMine(g.term) || { secs: [] }, fixed = m.secs.filter(x => onWeekSec(x) && !g.classes.some(k => slotCode(k) === x.code));
    const chosenK = g.classes.map(c => [c, g.sel[c] && slotSecs(g.term, c).find(x => String(x.id) === g.sel[c])]).filter(p => p[1]), chosen = chosenK.map(p => p[1]);""")
rep("""${g.unique && g.classes.some(c => (anySecsOf(g.term, c) || []).length > 1) ?""", """${g.unique && g.classes.some(c => slotSecs(g.term, c).length > 1) ?""")
rep("""${g.classes.map(c => {
      const secs = anySecsOf(g.term, c) || [];
      return `<div class="card dpk-c" role="group" aria-label="${esc(c)} sections"><div class="dpk-h"><span class="code">${esc(c)}</span><b>${esc(anyTitle(g.term, c))}</b></div>${secs.map(x => anySecBtn(x, { act: 'dprPickSec', x: gi + '|' + c + '|' + x.id, on: g.sel[c] === String(x.id), radio: true, fr: anyFriendsIn(g.term, x), clash: fixed.concat(chosen.filter(y => y.code !== c)).filter(y => secClash(x, y)), tag: secs.length === 1 ? 'Only section' : '', busy })).join('')}</div>`;""",
"""${g.classes.map(c => {
      const secs = slotSecs(g.term, c), cc = slotCode(c), pp = slotPart(c);
      return `<div class="card dpk-c" role="group" aria-label="${esc(cc + (pp ? ' ' + partName(pp) : ''))} sections"><div class="dpk-h"><span class="code">${esc(cc)}</span><b>${esc(pp ? partName(pp) + ' · ' + anyTitle(g.term, cc) : anyTitle(g.term, cc))}</b></div>${secs.map(x => anySecBtn(x, { act: 'dprPickSec', x: gi + '|' + c + '|' + x.id, on: g.sel[c] === String(x.id), radio: true, fr: anyFriendsIn(g.term, x), clash: fixed.concat(chosenK.filter(p => p[0] !== c).map(p => p[1])).filter(y => secClash(x, y)), tag: secs.length === 1 ? (pp ? 'Only ' + partName(pp).toLowerCase() + ' section' : 'Only section') : '', busy })).join('')}</div>`;""")
rep("""        for (const c of g.classes) {
          const id = g.sel[c]; if (!id || err) continue;
          const x = (anySecsOf(g.term, c) || []).find(y => String(y.id) === id); if (!x) continue;""",
"""        for (const c of g.classes) {
          const id = g.sel[c]; if (!id || err) continue;
          const x = slotSecs(g.term, c).find(y => String(y.id) === id); if (!x) continue;""")
rep("""          if (!err) { n++; delete g.sel[c]; g.classes = g.classes.filter(y => y !== c); }""",
"""          if (!err) { n++; nC.add(g.term + ':' + slotCode(c)); delete g.sel[c]; g.classes = g.classes.filter(y => y !== c); }""")
rep("""    let n = 0, err = null;
    try {
      for (const g of sh.groups) {""", """    let n = 0, err = null; const nC = new Set();   /* classes, not slots: a lecture + its lab is one class */
    try {
      for (const g of sh.groups) {""")
rep("""    dprPickClose(sh); toast(`${n} class${n === 1 ? '' : 'es'} on your week`);""",
"""    dprPickClose(sh); toast(`${nC.size} class${nC.size === 1 ? '' : 'es'} on your week`);""")

# ---- H. onboarding "Add your classes": a lecture, then its lab, without closing ------------------------------------
rep("""    const have = now ? mine.has(code) : took.has(code), open = UI.onbExpand === code && !have;""",
"""    const held = now ? personSecs('me').filter(x => x.code === code) : [], lacks = now && mine.has(code) && held.length ? partsMissing(secsOf(code), held) : [];
    const have = (now ? mine.has(code) : took.has(code)) && !lacks.length, open = UI.onbExpand === code && !have;   /* lecture + lab: stays open until both (2026-11-01) */""")
rep("""    const ss = secsOf(code);
    return head + `<div class="secs"><div class="s">Pick your section</div>${ss.map(s => { const n = fr(code, s.id);""",
"""    const ss = secsOf(code), mp = multiPart(ss), gs = partGroups(ss);
    return head + `<div class="secs"><div class="s">${mp ? `Pick your sections — one ${esc(partsWords(partsOf(ss)))}` : 'Pick your section'}</div>${gs.map(g => partHead(g, held.some(h => g.p && samePart(h, g.secs[0]))) + g.secs.map(s => { const n = fr(code, s.id);""")
rep("""<span class="s">${s.status === 'wait' ? 'Waitlist' : 'Full'}</span>` : '')}</button>`; }).join('')}
      <button type="button" class="secbtn" data-a="onbAdd" data-x="${esc(code)}" data-y=""><span>Add without a section</span></button></div>`;""",
"""<span class="s">${s.status === 'wait' ? 'Waitlist' : 'Full'}</span>` : '')}</button>`; }).join('')).join('')}
      <button type="button" class="secbtn" data-a="onbAdd" data-x="${esc(code)}" data-y=""><span>${held.length ? 'Done with this class' : 'Add without a section'}</span></button></div>`;""")
rep("""  onbAdd: async (code, secId) => { if (UI.busy.onb) return; UI.busy.onb = 1; UI.onbErr = ''; const e = await TC.addMyClass(code, secId || null); UI.busy.onb = 0; UI.onbErr = e || ''; UI.onbExpand = null; if (!e) toast(`Added ${code}`); render(true); },""",
"""  onbAdd: async (code, secId) => {
    if (UI.busy.onb) return;
    if (!secId && personSecs('me').some(x => x.code === code)) { UI.onbExpand = null; return render(true); }   /* "Done with this class" */
    const s = secId ? SEC[secId] : null, old = s ? personSecs('me').filter(x => x.code === code && samePart(x, s) && x.id !== s.id) : [];
    UI.busy.onb = 1; UI.onbErr = '';
    let e = await TC.addMyClass(code, secId || null);
    for (const x of old) { if (!e) e = await TC.removeMySection(code, x.id); }   /* a second pick of the same part replaces the first */
    UI.busy.onb = 0; UI.onbErr = e || '';
    const left = s && !e ? partsMissing(secsOf(code), personSecs('me').filter(x => x.code === code)) : [];
    UI.onbExpand = left.length ? code : null;
    if (!e) toast(left.length ? `Added ${atPartNm(s)} · now pick ${aPart(left[0])}` : `Added ${code}`);
    render(true);
  },""")

# ---- I. class pages + the section sheet say what a multi-part class still needs -------------------------------------
rep("""  const pqTile = prereqTile(code);""", """  const pqTile = prereqTile(code), mpNote = partsNote(code, secsOf(code), personSecs('me').filter(x => x.code === code));""")
rep(""" ${CLASS_SEC_H}
 ${profBlocks}<div class="spacer"></div>`, tabbar: true, fab: true""", """ ${CLASS_SEC_H}
 ${mpNote}${profBlocks}<div class="spacer"></div>`, tabbar: true, fab: true""", n=2)
rep("""    const seatsStat = cs.anyOpen ? (cs.open ? cs.open : 'Open') : cs.allFull ? 'Full' : '—';
""", """    const seatsStat = cs.anyOpen ? (cs.open ? cs.open : 'Open') : cs.allFull ? 'Full' : '—', mpNote = partsNote(code, secsOf(code), nowSecs('me').filter(x => x.code === code));
""")
open(path, 'w').write(s)

s = open(path).read()
rep("""  const nowActs = nowSecActs(code, id, s);""",
"""  const nowActs = nowSecActs(code, id, s);
  /* (2026-11-01) your section of a multi-part class: say which part is still missing, one tap from the class page */
  const mineHere = (isNowSecId(id) ? nowSecs('me') : personSecs('me')).filter(x => x.code === code), mpAll = isNowSecId(id) ? (NOWT.byCode[code] || []) : secsOf(code);
  const mpLeft = mineHere.some(x => x.id === id) ? partsMissing(mpAll, mineHere) : [];
  const mpLine = mpLeft.length ? `<div class="mp-left" role="note">No ${esc(partsWords(mpLeft))} section yet for ${esc(code)}.</div>` : '';""")
rep(""" ${secProfRow(s.prof)}
 ${secPeopleRow(who.here, 'In this section')}""", """ ${secProfRow(s.prof)}${mpLine}
 ${secPeopleRow(who.here, 'In this section')}""")
rep("""<button class="btn${(sh.fill && !inP && SEC[id]) || nowActs ? ' soft' : ''}" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>View class</button>""",
"""<button class="btn${((sh.fill && !inP && SEC[id]) || nowActs) && !mpLeft.length ? ' soft' : ''}" data-a="openClass" data-x="${code}"${isNowSecId(id) ? ' data-y="now"' : ''}>${mpLeft.length ? 'Pick ' + esc(aPart(mpLeft[0])) + ' section' : 'View class'}</button>""")
open(path, 'w').write(s)
print('lecture-lab: one section per part — swaps, pickers, labels, class pages, section sheet')
