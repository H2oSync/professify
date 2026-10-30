#!/usr/bin/env python3
"""Stress test, 2026-10-30: the phone's registration day stopped at Round 1. Round 1 ends Nov 3, so from Nov 4
every day in "When do you register?" was greyed out, the term card dropped registration altogether, friends'
days vanished, and Champ still said registration "starts Monday, October 19".
Round 2 is now the phone's too, the way the website already has it (index.html: REGISTRATION_ROUND2, OPEN_ENROLLMENT,
TL_TERMS; seats/registrar-calendar.json): from Nov 4 to Nov 17 "your day" is your Round 2 day —
registration_round2 / friend_registration_round2(p_term) (sql/professify-registration-round2-2026-10-16.sql, live
since 2026-10-17), the same rows the website's timeline reads and writes; friends see the day only. The picker shows
Round 2's weekdays (Nov 5–17), Veterans Day greyed out (a NO_CLASS_DAYS day). "Friends can see your day" is one
switch for both rounds, as on the website: it starts off if either round's is off, and saving it moves Round 1's.
A round that ends while the app is open is read again for the new round. Champ's answer and the game plan's line
say where registration stands today (Round 1 / Round 2 / Open Enrollment / over).
Round 1 (until Nov 3) is unchanged: same table, same key, same words.
Run after no-class-days-2026-10-30.py (Veterans Day comes from CFG.NO_CLASS_DAYS; without it nothing is skipped).
Usage: python3 registration-round2-2026-10-30.py app/index.html"""
import sys, pathlib
p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'app/index.html'); s = p.read_text()
if 'registration-round2 (2026-10-30)' in s:
    sys.exit('already patched')
def one(a, b, n1=1):
    global s
    n = s.count(a); assert n == n1, (a[:70], n); s = s.replace(a, b)

# ---------------------------------------------------------------- the dates
one("""  REGISTRATION_ROUND1_ENDS: '2026-11-03',
  /* 'December 22""", """  REGISTRATION_ROUND1_ENDS: '2026-11-03',
  /* registration-round2 (2026-10-30): Round 2 and Open Enrollment, as the website has them (index.html's config and TL_TERMS;
     seats/registrar-calendar.json, quoting registrar.calpoly.edu/spring-semester-planning-calendar): 'November 4 Round 2
     Registration begins' … 'November 17 End of Registration appointments for continuing students', 'November 18 Open
     Enrollment begins' … 'January 22 Open Enrollment ends'. Round 2's appointments are weekdays from Nov 5
     (REGISTRATION_ROUND2_FIRST, the website's r2a), never a NO_CLASS_DAYS day (Veterans Day, Nov 11). */
  REGISTRATION_ROUND2: '2026-11-04',
  REGISTRATION_ROUND2_FIRST: '2026-11-05',
  REGISTRATION_ROUND2_ENDS: '2026-11-17',
  OPEN_ENROLLMENT: '2026-11-18',
  OPEN_ENROLLMENT_ENDS: '2027-01-22',
  /* 'December 22""")

# ---------------------------------------------------------------- which round, and where it is kept
one("""const REG_KEY = () => 'tc-regday:' + ((TC.user && TC.user.id) || '') + ':' + CFG.REGISTRATION_TERM_CODE;""",
"""/* registration-round2 (2026-10-30): "your day" is the round under way — Round 1 until its last day (Nov 3), then Round 2 until
   its last (Nov 17), kept in registration_round2 and read for friends from friend_registration_round2 (the website's Round 2;
   friends get the day only). 0 = both rounds over (Open Enrollment): Round 2's rows, all behind us. TC.regRound = the round
   TC.regDay was read for; TC.regDay1 = your Round 1 row while Round 2 is on (its "Friends can see your day" switch). */
const regRound = () => { const t = sloISO(); return t <= regEnd() ? 1 : CFG.REGISTRATION_ROUND2_ENDS && t <= CFG.REGISTRATION_ROUND2_ENDS ? 2 : 0; };
const regSrc = r => r === 1 ? { table: 'registration_days', rpc: 'friend_registration_days', key: 'tc-regday:' } : { table: 'registration_round2', rpc: 'friend_registration_round2', key: 'tc-regday2:' };
const regR = () => TC.regRound == null ? regRound() : TC.regRound;
const REG_KEY = r => regSrc(r == null ? regR() : r).key + ((TC.user && TC.user.id) || '') + ':' + CFG.REGISTRATION_TERM_CODE;""")
one("""TC.regDay = null; TC.regFr = null; TC.regFrBusy = 0; TC.regGen = 0;""",
    """TC.regDay = null; TC.regFr = null; TC.regFrBusy = 0; TC.regGen = 0; TC.regRound = null; TC.regDay1 = null;""")

# ---------------------------------------------------------------- the round's days
one("""/* Round 1's weekdays: the days an appointment falls on */
function regRoundDays() {
  const out = [];
  for (let t = Date.parse(CFG.REGISTRATION_OPENS + 'T12:00:00Z'), e = Date.parse(regEnd() + 'T12:00:00Z'); t <= e && out.length < 60; t += 864e5) {
    const d = new Date(t), wd = d.getUTCDay(); if (wd > 0 && wd < 6) out.push(d.toISOString().slice(0, 10));
  }
  return out;
}""", """/* Round 1's weekdays: the days an appointment falls on. registration-round2 (2026-10-30): from Round 2 (Nov 4), Round 2's —
   weekdays from Nov 5 to Nov 17. regRoundGrid() is every weekday (the picker's grid); regRoundDays() leaves out a day with
   no classes (Veterans Day), which the grid shows greyed out. */
function regRoundGrid(r) {
  r = r == null ? regRound() : r;
  const two = r !== 1 && !!CFG.REGISTRATION_ROUND2_ENDS;
  const from = two ? (CFG.REGISTRATION_ROUND2_FIRST || CFG.REGISTRATION_ROUND2) : CFG.REGISTRATION_OPENS, to = two ? CFG.REGISTRATION_ROUND2_ENDS : regEnd();
  const out = [];
  for (let t = Date.parse(from + 'T12:00:00Z'), e = Date.parse(to + 'T12:00:00Z'); t <= e && out.length < 60; t += 864e5) {
    const d = new Date(t), wd = d.getUTCDay(); if (wd > 0 && wd < 6) out.push(d.toISOString().slice(0, 10));
  }
  return out;
}
const regSkip = d => (Array.isArray(CFG.NO_CLASS_DAYS) ? CFG.NO_CLASS_DAYS : []).find(x => x && x.from && x.from <= d && d <= (x.to || x.from)) || null;
const regRoundDays = r => regRoundGrid(r).filter(d => !regSkip(d));
const regMD = d => regDayText(d).split(', ')[1] || d;
/* where registration stands today, in words: Champ's answer, and the game plan's line */
function regNowText() {
  const T = esc(CFG.REGISTRATION_TERM), t = sloISO(), L = d => esc(new Date(d + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })), at = ' Your exact appointment is in the Cal Poly Portal.';
  if (CFG.REGISTRATION_OPENS && t < CFG.REGISTRATION_OPENS) return `${T} registration starts ${L(CFG.REGISTRATION_OPENS)}.${at}`;
  if (t <= regEnd()) return `${T} Round 1 registration is open until ${L(regEnd())}${CFG.REGISTRATION_ROUND2 ? `; Round 2 starts ${L(CFG.REGISTRATION_ROUND2)}` : ''}.${at}`;
  if (CFG.REGISTRATION_ROUND2_ENDS && t <= CFG.REGISTRATION_ROUND2_ENDS) return `${T} Round 2 registration is open until ${L(CFG.REGISTRATION_ROUND2_ENDS)}${CFG.OPEN_ENROLLMENT ? `; Open Enrollment starts ${L(CFG.OPEN_ENROLLMENT)}` : ''}.${at}`;
  if (CFG.OPEN_ENROLLMENT && t >= CFG.OPEN_ENROLLMENT && (!CFG.OPEN_ENROLLMENT_ENDS || t <= CFG.OPEN_ENROLLMENT_ENDS)) return `${T} registration appointments are over. Open Enrollment is on${CFG.OPEN_ENROLLMENT_ENDS ? ` until ${L(CFG.OPEN_ENROLLMENT_ENDS)}` : ''}: anyone can add an open class in the Cal Poly Portal.`;
  return `${T} registration is over. Changes go through the Cal Poly Portal.`;
}
function regNowShort() {
  const t = sloISO();
  if (CFG.REGISTRATION_OPENS && t < CFG.REGISTRATION_OPENS) return 'registration opens ' + regMD(CFG.REGISTRATION_OPENS);
  if (t <= regEnd()) return 'Round 1 till ' + regMD(regEnd());
  if (CFG.REGISTRATION_ROUND2_ENDS && t <= CFG.REGISTRATION_ROUND2_ENDS) return 'Round 2 till ' + regMD(CFG.REGISTRATION_ROUND2_ENDS);
  if (CFG.OPEN_ENROLLMENT && t >= CFG.OPEN_ENROLLMENT && (!CFG.OPEN_ENROLLMENT_ENDS || t <= CFG.OPEN_ENROLLMENT_ENDS)) return 'Open Enrollment';
  return 'registration is over';
}
/* a round that ended while the app was open (midnight, Nov 3 → 4): your day and friends' are read again for the new one */
function regSync() {
  if (!regWhen() || TC.regSyncing || TC.regRound == null || TC.regRound === regRound()) return;
  TC.regSyncing = 1;
  loadRegDay().then(() => loadRegFriends(true)).catch(() => {}).then(() => { TC.regSyncing = 0; render(true); });
}
const regSyncSoon = () => { if (TC.regRound != null && TC.regRound !== regRound() && !TC.regSyncing) setTimeout(regSync, 0); };""")

# ---------------------------------------------------------------- yours: read the round's row
one("""async function loadRegDay() {
  TC.regDay = null; TC.regFr = null; delete TC.err.regDay;
  if (!regWhen()) return;
  let loc = null; try { loc = JSON.parse(localStorage.getItem(REG_KEY()) || 'null'); } catch (e) {}""",
"""async function loadRegDay() {
  TC.regDay = null; TC.regFr = null; TC.regDay1 = null; delete TC.err.regDay;
  const R = TC.regRound = regRound(), src = regSrc(R);
  if (!regWhen()) return;
  let loc = null; try { loc = JSON.parse(localStorage.getItem(REG_KEY(R)) || 'null'); } catch (e) {}""")
one("""  let r; try { r = await TC.client().from('registration_days').select('day,at_time,shared,updated_at').eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (TC.regGen !== gen) return;   /* a save while this was in flight: that one stands */
  if (r.error) { TC.err.regDay = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  const row = r.data && regDayOk(r.data.day) ? r.data : null;""",
"""  let r; try { r = await TC.client().from(src.table).select('day,at_time,shared,updated_at').eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (TC.regGen !== gen) return;   /* a save while this was in flight: that one stands */
  if (r.error) { TC.err.regDay = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  /* Round 2: "Friends can see your day" is one switch for both rounds (the website's; friend_registration_round2 asks both) */
  if (R !== 1) {
    let q; try { q = await TC.client().from('registration_days').select('day,at_time,shared').eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE).maybeSingle(); } catch (e) { q = { error: { message: String(e) } }; }
    if (TC.regGen !== gen) return;
    TC.regDay1 = !q.error && q.data && regDayOk(q.data.day) ? { day: q.data.day, time: regTime5(q.data.at_time), shared: q.data.shared !== false } : null;
  }
  const row = r.data && regDayOk(r.data.day) ? r.data : null;""")
one("""  TC.regDay = row ? { day: row.day, time: regTime5(row.at_time), shared: row.shared !== false, local: false } : null;
  regKeep(TC.regDay, false);""",
"""  TC.regDay = row ? { day: row.day, time: regTime5(row.at_time), shared: row.shared !== false && (!TC.regDay1 || TC.regDay1.shared), local: false } : null;
  regKeep(TC.regDay, false);""")

# ---------------------------------------------------------------- yours: write the round's row
one("""  if (TC.err.regDay === 'missing') return null;
  let q;
  try {
    q = v ? await TC.client().from('registration_days').upsert({ user_id: TC.user.id, term: CFG.REGISTRATION_TERM_CODE, day: v.day, at_time: v.time || null, shared: !!v.shared, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' })
      : await TC.client().from('registration_days').delete().eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE);""",
"""  if (TC.err.regDay === 'missing') return null;
  const R = regR(), src = regSrc(R);
  let q;
  try {
    q = v ? await TC.client().from(src.table).upsert({ user_id: TC.user.id, term: CFG.REGISTRATION_TERM_CODE, day: v.day, at_time: v.time || null, shared: !!v.shared, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' })
      : await TC.client().from(src.table).delete().eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE);""")
one("""  if (v && TC.regDay === v) v.local = false;
  regKeep(v, false); return null;
}""", """  if (v && TC.regDay === v) v.local = false;
  regKeep(v, false);
  /* Round 2: the one "Friends can see your day" switch follows into your Round 1 row when that row is the other way (as on the website) */
  const r1 = TC.regDay1;
  if (R !== 1 && v && r1 && r1.shared !== !!v.shared) {
    let q1; try { q1 = await TC.client().from('registration_days').upsert({ user_id: TC.user.id, term: CFG.REGISTRATION_TERM_CODE, day: r1.day, at_time: r1.time || null, shared: !!v.shared, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' }); } catch (e) { q1 = { error: { message: String((e && e.message) || e) } }; }
    if (q1.error) return dbSay(q1.error, 'Your day is saved, but who can see it didn’t change — try again.');
    r1.shared = !!v.shared;
  }
  return null;
}""")

# ---------------------------------------------------------------- friends: the round's days
one("""  let r; try { r = await Promise.race([TC.client().rpc('friend_registration_days', { p_term: CFG.REGISTRATION_TERM_CODE }),""",
    """  const R = regRound();
  let r; try { r = await Promise.race([TC.client().rpc(regSrc(R).rpc, { p_term: CFG.REGISTRATION_TERM_CODE }),""")
one("""    TC.regFr = { rows: (Array.isArray(r.data) ? r.data : []).filter(x => x && x.user_id && regDayOk(x.day) && !seen.has(x.user_id) && seen.add(x.user_id)).map(x => ({ id: x.user_id, day: x.day, time: regTime5(x.at_time) })), at: Date.now() };""",
    """    TC.regFr = { rows: (Array.isArray(r.data) ? r.data : []).filter(x => x && x.user_id && regDayOk(x.day) && !seen.has(x.user_id) && seen.add(x.user_id)).map(x => ({ id: x.user_id, day: x.day, time: regTime5(x.at_time) })), at: Date.now(), round: R };""")

# ---------------------------------------------------------------- the term card
one("""  const u = `${plUnitsTarget()} units`, today = sloISO(), mine = TC.regDay, m = regWhen() && mine && mine.day >= today ? mine : null;
  let head = '', sub = '', add = false;""",
"""  regSyncSoon();
  const u = `${plUnitsTarget()} units`, today = sloISO(), mine = TC.regDay, m = regWhen() && mine && mine.day >= today ? mine : null;
  let head = '', sub = '', add = false;""")
one("""  } else if (regWhen() && !mine && today <= regEnd()) {
    const n = regGap(today, CFG.REGISTRATION_OPENS);
    head = n > 0 ? `Opens ${regOpensText()} · in ${regPlural(n, 'day')}` : 'Registration is open'; add = true;
  }""", """  } else if (regWhen() && !mine && today <= regEnd()) {
    const n = regGap(today, CFG.REGISTRATION_OPENS);
    head = n > 0 ? `Opens ${regOpensText()} · in ${regPlural(n, 'day')}` : 'Registration is open'; add = true;
  } else if (regWhen() && !mine && regRound() === 2) {
    head = 'Round 2 is open'; sub = `till ${regMD(CFG.REGISTRATION_ROUND2_ENDS)}`; add = true;   /* registration-round2 (2026-10-30) */
  }
  if (m && regR() === 2) sub = ['Round 2', sub].filter(Boolean).join(' · ');""")
one("""function regFriendRow(id) {
  if (!regWhen()) return '';""", """function regFriendRow(id) {
  if (!regWhen()) return '';
  regSyncSoon();""")
one("""  const F = TC.regFr, today = sloISO();
  let body;
  if (!regWhen()) body""", """  regSyncSoon();
  const F = TC.regFr, today = sloISO();
  let body;
  if (!regWhen()) body""")

# ---------------------------------------------------------------- the two pickers ("When do you register?" and the term sheet)
one("""  const today = sloISO(), days = regRoundDays(), busy = !!UI.busy.regDay;""", """  const today = sloISO(), days = regRoundGrid(), busy = !!UI.busy.regDay;""")
one("""    const today = sloISO(), days = regRoundDays();""", """    const today = sloISO(), days = regRoundGrid();""")
one("""      const on = d === sh.day, past = d < today;""", """      const on = d === sh.day, past = d < today || !!regSkip(d);""")
one("""    const on = d === sh.day, past = d < today;""", """    const on = d === sh.day, past = d < today || !!regSkip(d);""")
one("""<div class="rd-h">Round 1 · ${esc(span)}</div>""", """<div class="rd-h">Round ${regRound() === 1 ? 1 : 2} · ${esc(span)}</div>""", 2)
one("""Only your friends · the day and time</span>""", """${regRound() === 1 ? 'Only your friends · the day and time' : 'Only your friends · the day'}</span>""", 2)

# ---------------------------------------------------------------- Champ
one("""    case 'when_registration': return { t: `${esc(CFG.REGISTRATION_TERM)} registration starts ${esc(new Date(CFG.REGISTRATION_OPENS + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }))}. Your exact appointment is in the Cal Poly Portal.` };""",
    """    case 'when_registration': return { t: regNowText() };   /* registration-round2 (2026-10-30): where it stands today */""")
one("""  const open = new Date(CFG.REGISTRATION_OPENS + 'T12:00:00');
  return `<section class="chc" aria-label="${esc('Plan ' + P + ' game plan')}"><div class="chc-h plan-${P}"><span class="chplan">Plan ${P}</span><span class="chc-t" style="font-size:13px;color:var(--muted)">${order.length} class${order.length === 1 ? '' : 'es'} · registration opens ${esc(open.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }))}</span>""",
    """  return `<section class="chc" aria-label="${esc('Plan ' + P + ' game plan')}"><div class="chc-h plan-${P}"><span class="chplan">Plan ${P}</span><span class="chc-t" style="font-size:13px;color:var(--muted)">${order.length} class${order.length === 1 ? '' : 'es'} · ${esc(regNowShort())}</span>""")
# "Friends can see your day" starts off when either round's is off (no Round 2 day yet, Round 1's off)
one("""shared: m ? m.shared !== false : true };""", """shared: m ? m.shared !== false : !TC.regDay1 || TC.regDay1.shared !== false };""", 2)
p.write_text(s); print(p, 'registration-round2: ok')
