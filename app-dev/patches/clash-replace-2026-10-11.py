import sys
p=sys.argv[1] if len(sys.argv)>1 else 'repo/app/index.html'
s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
# 1. atPlanOf: while a replace is running, the clashing classes are drawn as swapped out
rep("""    o.full = !o.inIt && !o.repl.length && ids.length >= 12;
  } else if (mine) {""","""    o.full = !o.inIt && !o.repl.length && ids.length >= 12;
    if (sh.replacing && !o.inIt && o.clash.length) { o.repl = o.repl.concat(o.clash); o.base = o.base.filter(x => !o.clash.includes(x)); o.clash = []; }
  } else if (mine) {""")
rep("""    o.needStatus = !o.inIt && (s.status === 'full' || s.status === 'wait') && !sh.status;
  }
  return o;""","""    o.needStatus = !o.inIt && (s.status === 'full' || s.status === 'wait') && !sh.status;
    if (sh.replacing && !o.inIt && o.clash.length) { o.repl = o.repl.concat(o.clash); o.base = o.base.filter(x => !o.clash.includes(x)); o.clash = []; }
  }
  return o;""")
# 2. the buttons
rep("""  else if (adding) { note = o.repl.length ? `Swapping in ${nm(s)}…`""","""  else if (adding && sh.replacing) { note = `Replacing ${sh.replNames} with ${nm(s)}…`; btn = `<button class="btn at-go" disabled aria-disabled="true">Replacing…</button>`; }
  else if (adding) { note = o.repl.length ? `Swapping in ${nm(s)}…`""")
rep("""tn = 'bad'; btn = off('Clashes — can’t add'); }""","""tn = 'bad'; btn = go(atReplaceLabel(o.clash), 'replace'); }""")
rep(""" Add it anyway if that’s really your schedule.`; tn = 'bad'; btn = go('Add anyway', 'anyway'); }""","""`; tn = 'bad'; btn = o.clash.every(atNbr) ? go(atReplaceLabel(o.clash), 'replace') : go('Add anyway', 'anyway'); if (o.clash.every(atNbr)) alt = `<button class="at-alt" data-a="atGo" data-x="anyway">Add anyway</button>`; }""")
rep(""".at-alt{display:block;width:100%;min-height:44px;margin-top:6px;border:0;background:none;color:var(--blue-ink);font-weight:900;font-size:14.5px}""",""".at-alt{display:block;width:100%;min-height:44px;margin-top:6px;border:0;background:none;color:var(--blue-ink);font-weight:900;font-size:14.5px;text-align:center}""")
rep("""SHEETS.addTo = sh => {""","""/* "Replace BUS 4448 with this class": the button on a clash (Tate, 2026-10-11) */
function atReplaceLabel(cl) { const codes = [...new Set(cl.map(x => x.code))]; return codes.length === 1 ? `Replace ${esc(codes[0])} with this class` : `Replace ${codes.length} classes with this one`; }
SHEETS.addTo = sh => {""")
# 3. atGo
rep("""    if (o.other || o.inIt || (o.P && (o.clash.length || o.full)) || (o.mine && o.needStatus)) return;
    UI.busy.at = true; sh.phase = 'adding'; sh.seq++; sh.err = null; render(true);""","""    const rp = mode === 'replace' && !o.other && !o.inIt && o.clash.length > 0 && (!o.mine || o.clash.every(atNbr)), outs = rp ? o.clash.slice() : [];
    if (mode === 'replace' && !rp) return;
    if (o.other || o.inIt || (o.P && ((o.clash.length && !rp) || (o.full && !rp))) || (o.mine && o.needStatus)) return;
    UI.busy.at = true; sh.phase = 'adding'; sh.replacing = rp; sh.replNames = rp ? outs.map(x => esc(x.code) + (secLabel(x.sec) ? ' ' + esc(secLabel(x.sec)) : '')).join(' and ') : ''; sh.seq++; sh.err = null; render(true);""")
rep("""        const prev = (TC.plans[o.P] || []).slice(), had = prev.some(x => SEC[x] && SEC[x].code === s.code);
        TC.setPlan(o.P, prev.filter(x => !(SEC[x] && SEC[x].code === s.code)).concat(sh.id)); S.plan = o.P;
        msg = (had ? 'Swapped ' : 'Added ') + s.code + (had ? ' in Plan ' : ' to Plan ') + o.P;""","""        const prev = (TC.plans[o.P] || []).slice(), had = prev.some(x => SEC[x] && SEC[x].code === s.code), gone = new Set(outs.map(x => x.id));
        TC.setPlan(o.P, prev.filter(x => !(SEC[x] && SEC[x].code === s.code) && !gone.has(x)).concat(sh.id)); S.plan = o.P;
        msg = rp ? 'Replaced ' + [...new Set(outs.map(x => x.code))].join(', ') + ' with ' + s.code + ' in Plan ' + o.P : (had ? 'Swapped ' : 'Added ') + s.code + (had ? ' in Plan ' : ' to Plan ') + o.P;""")
rep("""        err = await TC.addMySection(s, { status: sh.status || 'enrolled', wlPos: sh.status === 'waitlisted' ? (parseInt(sh.wlPos, 10) || null) : null, swap, hadSaved: snap.saved });
        msg = (swap.length ? 'Swapped ' : 'Added ') + s.code + (swap.length ? ' in My Classes' : ' to My Classes');
        undo = async () => { const e = await TC.restoreMyCode(s.code, snap, String(s.id)); render(true); toast(e || 'Undone'); };""","""        /* a replace takes the clashing classes out too: a class with other sections keeps them, one with only this section goes */
        const gone = rp ? [...new Set(outs.map(x => x.code))].map(code => ({ code, snap: mineSnap(code), nbrs: outs.filter(x => x.code === code).map(atNbr), only: personSecs('me').filter(x => x.code === code).every(x => outs.some(y => y.id === x.id)) })) : [];
        err = await TC.addMySection(s, { status: sh.status || 'enrolled', wlPos: sh.status === 'waitlisted' ? (parseInt(sh.wlPos, 10) || null) : null, swap, hadSaved: snap.saved });
        half = gone.length > 0; for (const g of gone) { if (err) break; if (g.only) err = await TC.removeMyClass(g.code); else for (const n of g.nbrs) { if (!err) err = await TC.removeMySection(g.code, n); } }
        msg = rp ? 'Replaced ' + gone.map(g => g.code).join(', ') + ' with ' + s.code : (swap.length ? 'Swapped ' : 'Added ') + s.code + (swap.length ? ' in My Classes' : ' to My Classes');
        undo = async () => { let e = null; for (const g of gone) { if (!e) e = await TC.restoreMyCode(g.code, g.snap, null); } if (!e) e = await TC.restoreMyCode(s.code, snap, String(s.id)); render(true); toast(e || 'Undone'); };""")
rep("""    if (err) { sh.phase = 'preview'; sh.err = err; sh.seq++; render(true); return; }
    sh.phase = 'done'; sh.seq++; render(true);""","""    if (err) { sh.phase = 'preview'; sh.replacing = false; sh.err = err; sh.seq++; render(true); return; }
    sh.phase = 'done'; sh.seq++; render(true);""")
rep("""    const t0 = Date.now(); let err = null, undo = null, msg = '';""","""    const t0 = Date.now(); let err = null, undo = null, msg = '', half = false;""")
rep("""    if (UI.sheet !== sh) { if (err) toast(err); else toastUndo(msg, undo);""","""    if (err && half && undo) toastUndo(err + ' Undo to put it all back.', undo);   /* the new class went in and some old ones came out: never leave that without a way back */
    if (UI.sheet !== sh) { if (err) { if (!(half && undo)) toast(err); } else toastUndo(msg, undo);""")
open(p,'w').write(s)
