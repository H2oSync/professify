#!/usr/bin/env python3
"""2026-10-30 (stuck/can't edit pass): once a section was in My Classes, Add to your week hid "Did you get a seat?",
so a waitlisted class could never become Enrolled (or its waitlist spot change) — and a full section saved as
Enrolled could never become Waitlisted. With the section in My Classes the sheet now shows Your seat: Enrolled |
Waitlisted (and Spot # when waitlisted), opened on what is saved; a tap, or a changed spot, saves at once through
TC.addMySection (an upsert on user_id,class_nbr,term — the same row). A My Classes section's sheet (tapping it on
the week) gets "Seat or remove" into that screen."""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
def one(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
# open on what is saved
one("""  UI.sheet = { type: 'addTo', id, dest, phase: 'preview', status: null, wlPos: '', keepBoth: false, err: null, seq: 1 };""",
    """  const mineS = inMine ? personSecs('me').find(x => x.id === id) : null;   /* (2026-10-30) the seat you saved */
  UI.sheet = { type: 'addTo', id, dest, phase: 'preview', status: mineS ? (mineS.mineWl ? 'waitlisted' : 'enrolled') : null, wlPos: mineS && mineS.wlPos != null ? String(mineS.wlPos) : '', keepBoth: false, err: null, seq: 1 };""")
# the segment for a section already in My Classes
one("""  const pick = `<div class="at-pick"><div class="at-seg" role="group" aria-label="Add to">""",
    """  const mineSeat = o.mine && o.inIt && !sh.removing
    ? `<div class="at-status at-mine-seat"><span>Your seat</span><div class="at-seg" role="group" aria-label="Enrolled or waitlisted">${[['enrolled', 'Enrolled'], ['waitlisted', 'Waitlisted']].map(([k, l]) => `<button class="${(sh.status || 'enrolled') === k ? 'on' : ''}" data-a="atMineStatus" data-x="${k}" aria-pressed="${(sh.status || 'enrolled') === k}" ${UI.busy.atm ? 'disabled' : ''}>${l}</button>`).join('')}</div>
     ${sh.status === 'waitlisted' ? `<label class="at-wl">Spot #<input id="atwl" data-in="atwl" inputmode="numeric" pattern="[0-9]*" maxlength="3" value="${esc(sh.wlPos || '')}" placeholder="?" aria-label="Your waitlist spot (optional)" enterkeyhint="done"></label>` : ''}</div>` : '';
  const pick = `<div class="at-pick"><div class="at-seg" role="group" aria-label="Add to">""")
one("""  <div class="at-chips">${chips}</div>${status}</div>`;""",
    """  <div class="at-chips">${chips}</div>${status}${mineSeat}</div>`;""")
# what the note says while it's in My Classes
one("""  else if (o.inIt) { note = untimed ? `${nm(s)} is already in ${o.where} — under Anytime, since ${whyAny}.` : `${nm(s)} is in ${o.where}.`;""",
    """  else if (o.inIt) { note = (untimed ? `${nm(s)} is already in ${o.where} — under Anytime, since ${whyAny}.` : `${nm(s)} is in ${o.where}.`) + (o.mine && sh.status === 'waitlisted' ? ` You’re on the waitlist${parseInt(sh.wlPos, 10) ? ' (#' + parseInt(sh.wlPos, 10) + ')' : ''}.` : '');""")
# the actions
one("""  atBoth: () => {""",
    """  /* (2026-10-30) a section already in My Classes: Enrolled ↔ Waitlisted and the spot, saved on the tap */
  atMineStatus: v => { const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.dest !== 'mine' || UI.busy.atm) return; const nv = v === 'waitlisted' ? 'waitlisted' : 'enrolled'; if ((sh.status || 'enrolled') === nv) return; sh.status = nv; if (nv === 'enrolled') sh.wlPos = ''; A.atMineSave(); },
  atMineSave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'addTo' || sh.phase !== 'preview' || UI.busy.atm || UI.busy.at) return;
    const s = SEC[sh.id]; if (!s) return;
    const o = atPlanOf(sh, s); if (!o.mine || !o.inIt) return;
    const st = sh.status === 'waitlisted' ? 'waitlisted' : 'enrolled', wl = st === 'waitlisted' ? (parseInt(sh.wlPos, 10) || null) : null;
    const was = personSecs('me').find(x => x.id === sh.id);
    if (was && !!was.mineWl === (st === 'waitlisted') && (was.wlPos == null ? null : +was.wlPos) === wl) return;
    UI.busy.atm = 1; sh.err = null; render(true);
    let err = null; try { err = await TC.addMySection(s, { status: st, wlPos: wl, hadSaved: true }); } catch (e) { err = 'Couldn’t save that — check your connection.'; } finally { UI.busy.atm = 0; }
    if (UI.sheet === sh) { sh.err = err; render(true); } else render(true);
    toast(err || (st === 'waitlisted' ? `Saved: waitlisted for ${s.code}${wl ? ' (#' + wl + ')' : ''}` : `Saved: enrolled in ${s.code}`));
  },
  atBoth: () => {""")
# a changed spot saves when the field is done (blur / Enter)
one("""document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });""",
    """document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && (UI.sheet || UI.champ)) A.closeSheet(); });
document.addEventListener('change', ev => { const t = ev.target; if (t && t.id === 'atwl' && UI.sheet && UI.sheet.type === 'addTo' && UI.sheet.dest === 'mine' && personSecs('me').some(x => x.id === UI.sheet.id)) A.atMineSave(); });
document.addEventListener('keydown', ev => { const t = ev.target; if (ev.key === 'Enter' && t && t.id === 'atwl' && UI.sheet && UI.sheet.type === 'addTo' && personSecs('me').some(x => x.id === UI.sheet.id)) { ev.preventDefault(); t.blur(); } });""")
# the section's sheet: a way in
one(""" ${inP ? `<button class="btn soft" style="color:var(--red-ink)" data-a="removeSec" data-x="${esc(id)}">Remove from Plan ${S.plan}</button>` : ''}</div>`;
};""",
    """ ${SEC[id] && !isNowSecId(id) && personSecs('me').some(x => x.id === id) ? `<button class="btn soft" data-a="addPlanSheet" data-x="${esc(id)}">${personSecs('me').find(x => x.id === id).mineWl ? 'Waitlisted · change or remove' : 'Enrolled · change or remove'}</button>` : ''}
 ${inP ? `<button class="btn soft" style="color:var(--red-ink)" data-a="removeSec" data-x="${esc(id)}">Remove from Plan ${S.plan}</button>` : ''}</div>`;
};""")
p.write_text(s); print('addto-mine-status applied')
