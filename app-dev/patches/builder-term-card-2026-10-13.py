#!/usr/bin/env python3
"""Tate (2026-10-13), on the Builder's "Spring 2027 · 12 units · Edit" and "You register Wed, Oct 21, 11a · in 9 days ›":
"make this its own editiable togther thing", then "do B." (Builder Term Card Mockups, option B).
  - One card under the term: "Register Wed, Oct 21, 11a" with "in 9 days · 12 units" under it and a chevron. With no day
    yet: "Opens Oct 19 · in 6 days" · "12 units" and "Add your day". Outside registration: "12 units"
    with what matters most under it.
  - Tapping it opens one sheet, titled with the term: units, your registration day (Round 1 grid, time, friends can see),
    and what matters most. One Save writes what changed.
  - The "12 units · Edit" pill is gone. Friends' registration line stays under the card. The regDays page keeps its own
    regDayOpen sheet.
Replayable on 06:30 + catalog chip + no big left + req sub.
  python3 builder-term-card-2026-10-13.py <repo-dir>"""
import pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = ROOT / 'app/index.html'; s = p.read_text()
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit(f'builder-term-card: expected 1 of {a[:80]!r}, found {s.count(a)}')
    s = s.replace(a, b)

# 1. the Builder's top row: the term alone, then the one card (plTermCard) and friends' line
rep("""  return `<div class="pl-top"><div>${term}</div><button class="pl-pill" data-a="plPrefsOpen" aria-label="${esc(w)} · ${plUnitsTarget()} units · Edit">${plUnitsTarget()} units · Edit</button></div>${plRegBanner()}""",
    """  return `<div class="pl-top"><div>${term}</div></div>${plTermCard(w)}""")

# 2. the card: registration headline, "in N days · 12 units" under it; friends' line stays below
rep("""/* The Planner's line (design B): yours, in blue, or Registration opens … with Add your day; friends under it */
function plRegBanner() {""",
"""/* (2026-10-13, Tate's option B) the Builder's one term card: when you register, and your units, edited together */
function plTermCard(w) {
  const u = `${plUnitsTarget()} units`, today = sloISO(), mine = TC.regDay, m = regWhen() && mine && mine.day >= today ? mine : null;
  let head = '', sub = '', add = false;
  if (m) {
    const n = regGap(today, m.day), t = regTimeText(m.time);
    if (n > 1) { head = `Register ${regDayText(m.day)}${t ? ', ' + t : ''}`; sub = `in ${n} days`; }
    else if (n === 1) { head = `Register tomorrow${t ? ', ' + t : ''}`; }
    else {
      const left = m.time ? +m.time.slice(0, 2) * 60 + +m.time.slice(3, 5) - CLOCK.min : null;
      if (left == null) head = 'Register today';
      else if (left > 0) { head = `Register today at ${t}`; sub = `in ${left >= 60 ? Math.floor(left / 60) + 'h ' : ''}${left % 60}m`; }
      else head = `Your registration opened at ${t}`;
    }
  } else if (regWhen() && !mine && today <= regEnd()) {
    const n = regGap(today, CFG.REGISTRATION_OPENS);
    head = n > 0 ? `Opens ${regOpensText()} · in ${regPlural(n, 'day')}` : 'Registration is open'; add = true;
  }
  const line2 = head ? [sub, u].filter(Boolean).join(' · ') : `What matters most: ${w}`;
  const label = `${head || u}.${add ? ' Add your day.' : ''} ${line2}. Edit your registration day, units and what matters most`;
  const card = `<button class="pla-reg pl-tc${m || !head ? ' mine' : ''}" data-a="plTermOpen" aria-label="${esc(label)}">${ic('cal', 18, 2.4)}<span class="grow"><b class="pl-tc-h">${esc(head || u)}</b><span class="pl-tc-s">${esc(line2)}</span></span>${add ? `<span class="pla-add">Add your day${ic('chevR', 14, 2.6)}</span>` : ic('chevR', 15, 2.4)}</button>`;
  return card + (mine && !m ? '' : plRegFriends(m));
}
/* friends' registration line under the term card (unchanged words) */
function plRegFriends(m) {
  if (!regWhen()) return '';
  const today = sloISO();
  if (!TC.regFr && !TC.regFrBusy) setTimeout(() => loadRegFriends(), 0);
  const up = regFrRows().filter(x => x.day >= today);
  if (!up.length) return '';
  let txt;
  if (m) {
    const parts = [[up.filter(x => x.day < m.day).length, 'before you'], [up.filter(x => x.day === m.day).length, 'same day'], [up.filter(x => x.day > m.day).length, 'after']].filter(p => p[0]);
    txt = parts.map((p, i) => i ? `${p[0]} ${p[1]}` : `${regPlural(p[0], 'friend')} ${p[1]}`).join(' · ');
  } else txt = `${regPlural(up.length, 'friend')} added their day`;
  return `<button class="reg-fr" data-a="openRegDays" aria-label="${esc(txt)}. See registration days">${avStack(up.map(x => x.id), 22)}<span class="grow">${esc(txt)}</span>${ic('chevR', 15, 2.4)}</button>`;
}
/* The Planner's line (design B): yours, in blue, or Registration opens … with Add your day; friends under it */
function plRegBanner() {""")

# 3. the one sheet
rep("""/* "Mark done": asked once, saying what it does and doesn't do. */
SHEETS.plMark = sh => {""",
"""/* (2026-10-13) the term card's sheet: units, your registration day, what matters most — one Save */
SHEETS.plTerm = sh => {
  const units = sh.units, rk = sh.rank, done = rk.length === 3, busy = !!(UI.busy.prefs || UI.busy.regDay);
  const opt = (k, ico, bg) => { const n = rk.indexOf(k) + 1; return `<button class="pp-opt ${n ? 'on' : ''}" data-a="plPrefPick" data-x="${k}" aria-pressed="${!!n}" aria-label="${esc(PREF_LABEL[k])}${n ? ', number ' + n : ', not ranked'}"><span class="pp-ic" style="background:${bg}">${ico}</span>${esc(PREF_LABEL[k])}<span class="pp-ck pp-n">${n || ''}</span></button>`; };
  let reg = '';
  if (regWhen()) {
    const today = sloISO(), days = regRoundDays();
    const lead = days.length ? (new Date(days[0] + 'T12:00:00Z').getUTCDay() + 6) % 7 : 0;
    let prev = '';
    const cells = Array.from({ length: lead }, () => '<span></span>').concat(days.map(d => {
      const lab = prev && d.slice(5, 7) !== prev ? regDayText(d).split(', ')[1] : String(+d.slice(8)); prev = d.slice(5, 7);
      const on = d === sh.day, past = d < today;
      return `<button class="rd-d${on ? ' on' : ''}" data-a="regPickDay" data-x="${d}" aria-pressed="${on}" aria-label="${esc(regDayText(d, true))}"${past ? ' disabled' : ''}>${esc(lab)}</button>`;
    }));
    const span = days.length ? `${regDayText(days[0]).split(', ')[1]} – ${regDayText(days[days.length - 1]).split(', ')[1]}` : '';
    reg = `<div class="b pt-h">Your registration day</div>
  <div class="muted b" style="font-size:12.5px;margin:-4px 0 8px;line-height:1.4">Cal Poly Portal › Student Center › Enrollment Dates</div>
  <div class="rd-h">Round 1 · ${esc(span)}</div>
  <div class="rd-grid" role="group" aria-label="Your day"><span class="rd-w" aria-hidden="true">Mon</span><span class="rd-w" aria-hidden="true">Tue</span><span class="rd-w" aria-hidden="true">Wed</span><span class="rd-w" aria-hidden="true">Thu</span><span class="rd-w" aria-hidden="true">Fri</span>${cells.join('')}</div>
  <label class="rd-row"><span class="grow b" style="font-size:15px">Time</span><input id="rd-time" type="time" step="300" value="${esc(sh.time || '')}"></label>
  <div class="rd-row"><span class="grow"><span class="b" style="display:block;font-size:15px">Friends can see your day</span><span class="muted b" style="display:block;font-size:12.5px">Only your friends · the day and time</span></span><button class="toggle ${sh.shared ? 'on' : 'off'}" data-a="regShareToggle" role="switch" aria-checked="${!!sh.shared}" aria-label="Friends can see your day"><i></i></button></div>
  ${TC.regDay ? `<button class="link b pt-rm" data-a="regDayRemove" ${busy ? 'disabled' : ''}>Remove my day</button>` : ''}`;
  }
  return `<div class="row sb"><h3>${esc(CFG.TERM_LABEL)}</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <div class="b pt-h" style="margin-top:6px">Units next term</div>
  <div class="pp-units" role="group" aria-label="Units next term">${[12, 14, 16, 18, 20].map(x => `<button class="${units === x ? 'on' : ''}" data-a="plPrefUnits" data-x="${x}" aria-pressed="${units === x}">${x}</button>`).join('')}</div>
  ${reg}
  <div class="b pt-h">What matters most</div>
  <div class="muted b" style="font-size:12.5px;margin:-4px 0 8px">${done ? 'Your plan is built around them, in this order. Tap 1 to rank again.' : `Tap what matters ${rk.length ? 'next' : 'most'}.`}</div>
  <div class="pp-opts">${opt('degree', ic('check', 22, 2.6), 'var(--blue-soft)')}${opt('professors', ic('star', 22, 2.4), 'var(--teal-soft)')}${opt('friends', ic('users', 22, 2.4), 'var(--pink-tint,#FCE7F3)')}</div>
  ${sh.err ? `<div class="tc-err">${esc(sh.err)}</div>` : ''}
  <button class="btn" style="margin-top:16px" data-a="plTermSave" ${busy || !done ? 'disabled' : ''}>${busy ? 'Saving…' : 'Save'}</button>`;
};
/* "Mark done": asked once, saying what it does and doesn't do. */
SHEETS.plMark = sh => {""")

# 4. actions: open, the shared pickers accept the term sheet, one Save
rep("""  plPrefsOpen: () => { UI.sheet = { type: 'plPrefs' }; render(true); },""",
    """  plPrefsOpen: () => { UI.sheet = { type: 'plPrefs' }; render(true); },
  plTermOpen: () => { const m = TC.regDay; UI.sheet = { type: 'plTerm', units: (TC.prefs && TC.prefs.units) || 16, rank: prefOrder().slice(), day: m ? m.day : '', time: m ? m.time : '', shared: m ? m.shared !== false : true }; render(true); },
  plTermSave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'plTerm' || UI.busy.prefs || UI.busy.regDay) return;
    regReadTime(sh); sh.err = null;
    const rk = sh.rank; if (rk.length !== 3) return;
    const m = TC.regDay, regOn = regWhen() && !!sh.day, regChanged = regOn && (!m || m.day !== sh.day || (m.time || '') !== (sh.time || '') || (m.shared !== false) !== !!sh.shared);
    if (regWhen() && !sh.day && sh.time) { sh.err = 'Pick your day too, or clear the time.'; return render(true); }
    if (regChanged && (!regDayOk(sh.day) || !regRoundDays().includes(sh.day))) { sh.err = 'Pick your day first.'; return render(true); }
    if (regChanged && sh.time && !regTimeOk(sh.time)) { sh.err = 'That time doesn’t look right.'; return render(true); }
    const before = TC.prefs ? { order: prefOrder().join(), units: TC.prefs.units } : null, prefChanged = !before || before.order !== rk.join() || before.units !== sh.units || !!sh.prefsDirty || !!(TC.prefs && TC.prefs.local);
    if (before && (before.order !== rk.join() || before.units !== sh.units)) sh.prefsDirty = true;
    let e = null;
    if (prefChanged) {
      UI.busy.prefs = 1; render(true);
      try { e = await TC.savePrefs(rk[0], sh.units, rk); } catch (x) { e = 'Couldn’t save that — try again.'; }
      UI.busy.prefs = 0;
      if (sh.prefsDirty) UI.plRefresh = true;   /* new answers: TermChamp's plans are worked out again (your own plans stay as they are) */
      if (e) { sh.err = e; return render(true); }
      sh.prefsDirty = false;
    }
    let re = null;
    if (regChanged) {
      UI.busy.regDay = 1; render(true);
      try { re = await TC.saveRegDay({ day: sh.day, time: sh.time || '', shared: !!sh.shared }); } catch (x) { re = 'Couldn’t save your day — it’s kept on this phone for now.'; }
      UI.busy.regDay = 0; loadRegFriends(true);
    }
    if (UI.sheet === sh) UI.sheet = null;
    toast(re || (regChanged && TC.err.regDay === 'missing' ? 'Saved on this phone' : 'Saved')); render(true);
  },""")
rep("""  regPickDay: d => { const sh = UI.sheet; if (!sh || sh.type !== 'regDay' ||""",
    """  regPickDay: d => { const sh = UI.sheet; if (!sh || (sh.type !== 'regDay' && sh.type !== 'plTerm') ||""")
rep("""  regShareToggle: () => { const sh = UI.sheet; if (!sh || sh.type !== 'regDay') return;""",
    """  regShareToggle: () => { const sh = UI.sheet; if (!sh || (sh.type !== 'regDay' && sh.type !== 'plTerm')) return;""")
rep("""    const sh = UI.sheet; if (!sh || sh.type !== 'regDay' || UI.busy.regDay) return;
    UI.busy.regDay = 1; render(true);
    let e; try { e = await TC.saveRegDay(null); } catch (x) { e = 'Couldn’t remove it — try again.'; }
    UI.busy.regDay = 0; if (UI.sheet === sh) UI.sheet = null; toast(e || 'Your day is removed'); render(true);""",
    """    const sh = UI.sheet; if (!sh || (sh.type !== 'regDay' && sh.type !== 'plTerm') || UI.busy.regDay) return;
    UI.busy.regDay = 1; render(true);
    let e; try { e = await TC.saveRegDay(null); } catch (x) { e = 'Couldn’t remove it — try again.'; }
    UI.busy.regDay = 0;
    if (sh.type === 'plTerm') { if (!e) { sh.day = ''; sh.time = ''; } toast(e || 'Your day is removed'); return render(true); }   /* the term sheet stays open */
    if (UI.sheet === sh) UI.sheet = null; toast(e || 'Your day is removed'); render(true);""")
rep("""  plPrefPick: k => { const sh = UI.sheet; if (!sh || sh.type !== 'plPrefs' || !PREF_ORDER[k]) return;""",
    """  plPrefPick: k => { const sh = UI.sheet; if (!sh || (sh.type !== 'plPrefs' && sh.type !== 'plTerm') || !PREF_ORDER[k]) return; if (sh.type === 'plTerm') regReadTime(sh);""")
rep("""  plPrefUnits: u => { if (UI.sheet && UI.sheet.type === 'plPrefs') { UI.sheet.units = +u; render(true); } },""",
    """  plPrefUnits: u => { const sh = UI.sheet; if (sh && (sh.type === 'plPrefs' || sh.type === 'plTerm')) { if (sh.type === 'plTerm') regReadTime(sh); sh.units = +u; render(true); } },""")

# 5. CSS: the card is a two-line row; the sheet's section heads
rep(""".pla-reg.mine{background:var(--blue-soft);color:var(--blue-ink)}""",
    """.pla-reg.mine{background:var(--blue-soft);color:var(--blue-ink)}
.pla-reg.pl-tc{min-height:56px;padding:10px 14px;gap:12px;border-radius:16px}
.pl-tc-h{display:block;font-size:15px;font-weight:900;line-height:1.25}
.pl-tc-s{display:block;font-size:12.5px;font-weight:800;opacity:.85;margin-top:1px}
.pt-h{font-size:15px;margin:18px 0 8px}
.pt-rm{display:block;margin:10px auto 0;color:var(--muted);font-size:13.5px;min-height:44px}""")
# the old banner has no caller now
i = s.index("/* The Planner's line (design B): yours, in blue, or Registration opens … with Add your day; friends under it */\nfunction plRegBanner() {")
j = s.index("/* On a friend's page:", i)
s = s[:i] + s[j:]
rep("""if (t && t.id === 'rd-time' && UI.sheet && UI.sheet.type === 'regDay') UI.sheet.time""",
    """if (t && t.id === 'rd-time' && UI.sheet && (UI.sheet.type === 'regDay' || UI.sheet.type === 'plTerm')) UI.sheet.time""")
# the pill's CSS has no element any more
rep(""".pl-pill{flex:none;height:32px;padding:0 12px;border-radius:999px;background:var(--blue-soft);color:var(--blue-ink);font-size:13px;font-weight:900;white-space:nowrap}
""", "")
p.write_text(s); print('builder-term-card: applied')
