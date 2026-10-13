#!/usr/bin/env python3
"""Your registration day (Tate, 2026-10-11: "people have different registration days so have them be able to upload
their registration day and maybe even display it to friends. but defiantly have them be able to start working on
building the schedule have something like 10 days until registration plan out your perfect schedule"). Canvas
"Your Registration Day": Tate picked B, the slim line ("I like B. but the time is fine to share too"), and the plan
card's three tiles go ("take out this its not that important to show").

- Planner, planning the term registration is for:
  - your day added: a blue line, "You register Fri, Oct 23, 8:30a · in 10 days" ("tomorrow", then on the day
    "today at 8:30a · in 2h 15m", then "Your registration opened at 8:30a"); gone the day after. Tap to change it.
  - no day yet, until Round 1 ends: the amber line, "Opens Oct 19 · in 8 days" (from the 19th "Registration is
    open"), with "Add your day ›".
  - under it, friends who shared a day still to come: faces and "2 friends before you · 1 same day · 1 after" (or
    "3 friends added their day" before you add yours). Tap → Registration days.
- The sheet "When do you register?": Round 1's weekdays (Oct 19 – Nov 3, past days off), a time (optional),
  "Friends can see your day" (on by default, like Plans), Save, and Remove my day.
- Registration days: you and friends with a day still to come, by date then time, each with how far before or after
  you; tap a friend for their page. "N friends haven't added theirs."
- A friend's page: "Registers Wed, Oct 21 · 8a · 2 days before you" under Major · Concentration · Year.
- Kept in registration_days (sql/professify-registration-days.sql, RUN 17): your row is yours alone; friends read
  day and time only through friend_registration_days(), which answers with accepted same-school friends who shared,
  never anyone blocked on either side. Until RUN 17 runs the day stays on this phone (and goes up once it can);
  friends' days don't show.
- The plan card loses its Classes · Professors · Day off tiles (the units are on the pill, each class row has its
  professor's rating).

Usage: python3 registration-day-2026-10-11.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'app' / 'index.html'
s = f.read_text()
if 'reg-day (2026-10-11)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

# 1. config: the registration term's code and Round 1's last day
one("""  REGISTRATION_TERM: 'Spring 2027',
""", """  REGISTRATION_TERM: 'Spring 2027',
  /* reg-day (2026-10-11): the code your registration day is kept under, and Round 1's last day — "Round 1 ends
     Nov 3" (registrar.calpoly.edu, Spring 2027 registration calendar; oct5-to-registration-plan-2026-09-21.md) */
  REGISTRATION_TERM_CODE: '2274',
  REGISTRATION_ROUND1_ENDS: '2026-11-03',
""")

# 2. the tiles go
a = s.index('  /* the tiles */\n'); b = s.index('  /* the week: Mon–Fri')
assert s.count('  /* the tiles */\n') == 1 and s.count('  /* the week: Mon–Fri') == 1 and 'const tiles = `<div class="pla-stats">' in s[a:b]
s = s[:a] + s[b:]
one("""  return `<div class="card pl-card pla plan-${k}">${head}${tiles}${week || tray ?""", """  return `<div class="card pl-card pla plan-${k}">${head}${week || tray ?""")
one("""/* The plan card, design A (spring-card-a (2026-10-09)): named A/B/C tabs, three tiles, a week you can read,""",
    """/* The plan card, design A (spring-card-a (2026-10-09)): named A/B/C tabs (the three tiles went 2026-10-11), a week you can read,""")

# 3. the line, the sheet, the list, loading and saving
old_banner_start = '/* "Registration opens Oct 19 · in 10 days", until it opens (the plan\'s term only) */\nfunction plRegBanner() {'
a = s.index(old_banner_start); b = s.index('\nfunction planCard(k, L, R, why) {', a)
assert s.count(old_banner_start) == 1
s = s[:a] + r'''/* ================= reg-day (2026-10-11) =================
   Your registration day. TC.regDay = { day 'YYYY-MM-DD', time 'HH:MM' or '', shared, local } | null — yours, from
   registration_days (owner-only; RUN 17) or, before RUN 17 or offline, this phone. TC.regFr = { rows: [{ id, day,
   time }], at, off } | { err, at } — friends' days from friend_registration_days(), which answers only with your
   accepted same-school friends who shared, never anyone blocked on either side. Days are Pacific calendar days. */
const REG_KEY = () => 'tc-regday:' + ((TC.user && TC.user.id) || '') + ':' + CFG.REGISTRATION_TERM_CODE;
const REG_TTL = 120000, REG_ERR_TTL = 15000;
TC.regDay = null; TC.regFr = null; TC.regFrBusy = 0; TC.regGen = 0;
const regWhen = () => !!TC.user && CFG.TERM_LABEL === CFG.REGISTRATION_TERM && !!CFG.REGISTRATION_TERM_CODE && !!CFG.REGISTRATION_OPENS;
const regDayOk = d => /^\d{4}-\d{2}-\d{2}$/.test(String(d || ''));
const regTimeOk = t => /^([01]\d|2[0-3]):[0-5]\d$/.test(String(t || ''));
const regTime5 = t => { const v = String(t || '').slice(0, 5); return regTimeOk(v) ? v : ''; };
const regEnd = () => CFG.REGISTRATION_ROUND1_ENDS || CFG.REGISTRATION_OPENS;
/* Round 1's weekdays: the days an appointment falls on */
function regRoundDays() {
  const out = [];
  for (let t = Date.parse(CFG.REGISTRATION_OPENS + 'T12:00:00Z'), e = Date.parse(regEnd() + 'T12:00:00Z'); t <= e && out.length < 60; t += 864e5) {
    const d = new Date(t), wd = d.getUTCDay(); if (wd > 0 && wd < 6) out.push(d.toISOString().slice(0, 10));
  }
  return out;
}
const regGap = (a, b) => Math.round((Date.parse(b + 'T12:00:00Z') - Date.parse(a + 'T12:00:00Z')) / 864e5);
const regDayText = (d, long) => { try { return new Date(d + 'T12:00:00Z').toLocaleDateString('en-US', { timeZone: 'UTC', weekday: long ? 'long' : 'short', month: long ? 'long' : 'short', day: 'numeric' }); } catch (e) { return d; } };
const regTimeText = t => regTimeOk(t) ? hs(+t.slice(0, 2) * 60 + +t.slice(3, 5)) : '';
const regPlural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
function regKeep(v, pending) {
  try {
    if (!pending) { if (v) localStorage.setItem(REG_KEY(), JSON.stringify({ day: v.day, time: v.time, shared: v.shared })); else localStorage.removeItem(REG_KEY()); }
    else localStorage.setItem(REG_KEY(), JSON.stringify(v ? { day: v.day, time: v.time, shared: v.shared, at: Date.now(), pending: true } : { gone: true, at: Date.now(), pending: true }));
  } catch (e) {}
}
/* Yours: the server's row, unless this phone has a change the server never got (then that goes up) */
async function loadRegDay() {
  TC.regDay = null; TC.regFr = null; delete TC.err.regDay;
  if (!regWhen()) return;
  let loc = null; try { loc = JSON.parse(localStorage.getItem(REG_KEY()) || 'null'); } catch (e) {}
  if (loc && !loc.gone && !regDayOk(loc.day)) loc = null;
  if (loc && !loc.gone) TC.regDay = { day: loc.day, time: regTime5(loc.time), shared: loc.shared !== false, local: true };
  const gen = TC.regGen;
  let r; try { r = await TC.client().from('registration_days').select('day,at_time,shared,updated_at').eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
  if (TC.regGen !== gen) return;   /* a save while this was in flight: that one stands */
  if (r.error) { TC.err.regDay = schemaGap(r.error) ? 'missing' : r.error.message; return; }
  const row = r.data && regDayOk(r.data.day) ? r.data : null;
  if (loc && loc.pending && (!row || !row.updated_at || Date.parse(row.updated_at) < (+loc.at || 0))) { await regPush(loc.gone ? null : TC.regDay); return; }
  TC.regDay = row ? { day: row.day, time: regTime5(row.at_time), shared: row.shared !== false, local: false } : null;
  regKeep(TC.regDay, false);
}
/* up to the server; null removes it. Returns what to tell the student, or null. */
async function regPush(v) {
  if (TC.err.regDay === 'missing') return null;
  let q;
  try {
    q = v ? await TC.client().from('registration_days').upsert({ user_id: TC.user.id, term: CFG.REGISTRATION_TERM_CODE, day: v.day, at_time: v.time || null, shared: !!v.shared, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' })
      : await TC.client().from('registration_days').delete().eq('user_id', TC.user.id).eq('term', CFG.REGISTRATION_TERM_CODE);
  } catch (e) { q = { error: { message: String((e && e.message) || e) } }; }
  if (q.error) {
    if (schemaGap(q.error)) { TC.err.regDay = 'missing'; return null; }
    /* taking it away or hiding it: until it goes through, friends still see it — say so, never "saved" */
    const say = dbSay(q.error, 'Couldn’t save that — it’s kept on this phone for now.');
    return !v || !v.shared ? 'Not done yet — friends can still see your day until it goes through. It’ll try again when you’re back online.' : say;
  }
  if (v && TC.regDay === v) v.local = false;
  regKeep(v, false); return null;
}
TC.saveRegDay = async function (v) {
  TC.regGen++;
  TC.regDay = v ? { day: v.day, time: regTime5(v.time), shared: v.shared !== false, local: true } : null;
  regKeep(TC.regDay, true);
  const e = await regPush(TC.regDay);
  TC.regFr = TC.regFr && TC.regFr.rows ? Object.assign(TC.regFr, { at: 0 }) : TC.regFr;   /* "before you" counts move with your day */
  return e;
};
/* a change kept on this phone goes up when the phone is back online or the app comes back to the front */
async function regRetry() {
  if (!regWhen() || TC.regRetrying || TC.err.regDay === 'missing') return;
  let loc = null; try { loc = JSON.parse(localStorage.getItem(REG_KEY()) || 'null'); } catch (e) {}
  if (!loc || !loc.pending || (!loc.gone && !TC.regDay)) return;
  TC.regRetrying = 1;
  try { const e = await regPush(loc.gone ? null : TC.regDay); if (!e) loadRegFriends(true); } finally { TC.regRetrying = 0; }
}
window.addEventListener('online', () => { regRetry(); });
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') regRetry(); });
/* the time you type is kept as you type it, so nothing that redraws the sheet can lose it */
['input', 'change'].forEach(ev => document.addEventListener(ev, e => { const t = e.target; if (t && t.id === 'rd-time' && UI.sheet && UI.sheet.type === 'regDay') UI.sheet.time = String(t.value || '').slice(0, 5); }, true));
/* Friends' days: asked once, again after 2 minutes (keeping the list meanwhile), 15 seconds after a failure */
async function loadRegFriends(force) {
  if (!regWhen() || TC.regFrBusy) return;
  const was = TC.regFr;
  if (!force && was && (was.off || Date.now() - was.at < (was.err ? REG_ERR_TTL : REG_TTL))) return;
  TC.regFrBusy = 1;
  let r; try { r = await Promise.race([TC.client().rpc('friend_registration_days', { p_term: CFG.REGISTRATION_TERM_CODE }), new Promise((_, no) => setTimeout(() => no(new Error('timeout')), 10000))]); }
  catch (e) { r = { error: { message: String((e && e.message) || e) } }; }
  TC.regFrBusy = 0;
  if (r.error && noRpc(r.error)) TC.regFr = { rows: [], at: Date.now(), off: true };
  else if (r.error) { if (was && was.rows) was.at = Date.now() - REG_TTL + REG_ERR_TTL; else TC.regFr = { err: 1, at: Date.now() }; }
  else {
    const seen = new Set();
    TC.regFr = { rows: (Array.isArray(r.data) ? r.data : []).filter(x => x && x.user_id && regDayOk(x.day) && !seen.has(x.user_id) && seen.add(x.user_id)).map(x => ({ id: x.user_id, day: x.day, time: regTime5(x.at_time) })), at: Date.now() };
  }
  if (!UI.sheet) render(true);
}
/* friends' days as they stand now: friends only, never someone you blocked, by day then time */
function regFrRows() {
  const F = TC.regFr; if (!F || !F.rows) return [];
  return F.rows.filter(x => TC.friends.includes(x.id) && !isBlocked(x.id) && PEOPLE[x.id]).sort((a, b) => a.day.localeCompare(b.day) || (a.time || '99').localeCompare(b.time || '99') || String(PEOPLE[a.id].name || '').localeCompare(String(PEOPLE[b.id].name || '')));
}
/* "2 days before you" · "same day as you" · "3 days after you" */
function regRel(day) {
  const m = TC.regDay; if (!m) return '';
  const d = regGap(m.day, day);
  return !d ? 'same day as you' : d < 0 ? regPlural(-d, 'day') + ' before you' : regPlural(d, 'day') + ' after you';
}
/* The Planner's line (design B): yours, in blue, or Registration opens … with Add your day; friends under it */
function plRegBanner() {
  if (!regWhen()) return '';
  const today = sloISO(), mine = TC.regDay, m = mine && mine.day >= today ? mine : null;
  let line = '';
  if (m) {
    const n = regGap(today, m.day), t = regTimeText(m.time);
    let txt;
    if (n > 1) txt = `You register ${regDayText(m.day)}${t ? ', ' + t : ''} · in ${n} days`;
    else if (n === 1) txt = `You register tomorrow${t ? ', ' + t : ''}`;
    else {
      const left = m.time ? +m.time.slice(0, 2) * 60 + +m.time.slice(3, 5) - CLOCK.min : null;
      txt = left == null ? 'You register today' : left > 0 ? `You register today at ${t} · in ${left >= 60 ? Math.floor(left / 60) + 'h ' : ''}${left % 60}m` : `Your registration opened at ${t}`;
    }
    line = `<button class="pla-reg mine" data-a="regDayOpen" aria-label="${esc(txt)}. Change your registration day">${ic('cal', 16, 2.4)}<span class="grow">${esc(txt)}</span>${ic('chevR', 15, 2.4)}</button>`;
  } else if (!mine && today <= regEnd()) {
    const n = regGap(today, CFG.REGISTRATION_OPENS);
    const txt = n > 0 ? `Opens ${regOpensText()} · in ${regPlural(n, 'day')}` : 'Registration is open';
    line = `<button class="pla-reg" data-a="regDayOpen" aria-label="${esc(txt)} · Add your day${n > 0 ? `. Registration opens ${regOpensText()}` : ''}">${ic('cal', 16, 2.4)}<span class="grow">${esc(txt)}</span><span class="pla-add">Add your day${ic('chevR', 14, 2.6)}</span></button>`;
  }
  if (!line) return '';
  if (!TC.regFr && !TC.regFrBusy) setTimeout(() => loadRegFriends(), 0);
  const up = regFrRows().filter(x => x.day >= today);
  if (!up.length) return line;
  let txt;
  if (m) {
    const parts = [[up.filter(x => x.day < m.day).length, 'before you'], [up.filter(x => x.day === m.day).length, 'same day'], [up.filter(x => x.day > m.day).length, 'after']].filter(p => p[0]);
    txt = parts.map((p, i) => i ? `${p[0]} ${p[1]}` : `${regPlural(p[0], 'friend')} ${p[1]}`).join(' · ');
  } else txt = `${regPlural(up.length, 'friend')} added their day`;
  return `${line}<button class="reg-fr" data-a="openRegDays" aria-label="${esc(txt)}. See registration days">${avStack(up.map(x => x.id), 22)}<span class="grow">${esc(txt)}</span>${ic('chevR', 15, 2.4)}</button>`;
}
/* On a friend's page: "Registers Wed, Oct 21 · 8a · 2 days before you" */
function regFriendRow(id) {
  if (!regWhen()) return '';
  if (!TC.regFr && !TC.regFrBusy) setTimeout(() => loadRegFriends(), 0);
  const x = regFrRows().find(r => r.id === id), today = sloISO();
  if (!x || x.day < today) return '';
  const t = regTimeText(x.time), rel = x.day === today ? '' : regRel(x.day);
  const when = x.day === today ? `Registers today${t ? ' at ' + t : ''}` : `Registers ${regDayText(x.day)}${t ? ' · ' + t : ''}`;
  return `<div class="regrow">${ic('cal', 18, 2.4)}<span class="grow"><b>${esc(when)}</b>${rel ? ' · ' + esc(rel) : ''}</span></div>`;
}
SCREENS.regDays = () => {
  const head = `<div class="topbtns mehd"><button class="iconbtn" data-a="back" aria-label="Back">${ic('chevL', 22, 2.4)}</button><div class="mehd-t">Registration days</div><span style="width:44px"></span></div>`;
  const F = TC.regFr, today = sloISO();
  let body;
  if (!regWhen()) body = `<div class="empty"><b>Registration days show while you’re planning ${esc(CFG.REGISTRATION_TERM)}</b></div>`;
  else if (F && F.off) body = `<div class="empty"><b>Not available yet</b></div>`;
  else if (!F || (!F.rows && TC.regFrBusy)) { if (!F && !TC.regFrBusy) setTimeout(() => loadRegFriends(), 0); body = loadingCard('Loading registration days…'); }
  else if (!F.rows) body = `<div class="empty"><b>Couldn’t load your friends’ days.</b><button class="pbtn pink" style="margin-top:10px" data-a="regDaysRetry">Try again</button></div>`;
  else {
    const fr = regFrRows(), up = fr.filter(x => x.day >= today), mine = TC.regDay && TC.regDay.day >= today ? TC.regDay : null;
    const list = up.map(x => ({ id: x.id, day: x.day, time: x.time })).concat(mine ? [{ id: 'me', day: mine.day, time: mine.time }] : [])
      .sort((a, b) => a.day.localeCompare(b.day) || (a.time || '99').localeCompare(b.time || '99') || (a.id === 'me' ? -1 : b.id === 'me' ? 1 : 0));
    const row = x => {
      const me = x.id === 'me', t = regTimeText(x.time), dt = regDayText(x.day).split(', ');
      const sub = me ? [t, TC.regDay.shared ? '' : 'Only you can see it'].filter(Boolean).join(' · ') : [t, x.day === today ? 'today' : regRel(x.day)].filter(Boolean).join(' · ');
      return `<button class="li regd${me ? ' me' : ''}" data-a="${me ? 'regDayOpen' : 'openFriend'}"${me ? '' : ` data-x="${esc(x.id)}"`}><span class="regd-d"><b>${x.day === today ? 'TODAY' : esc((dt[0] || '').toUpperCase())}</b><span>${esc(dt[1] || x.day)}</span></span>${pav(x.id, 40, 14)}<span class="grow regd-w"><span class="regd-n">${me ? 'You' : esc(PEOPLE[x.id].name)}</span>${sub ? `<span class="regd-s">${esc(sub)}</span>` : ''}</span></button>`;
    };
    const missing = TC.friends.filter(id => !isBlocked(id) && PEOPLE[id] && !fr.some(x => x.id === id)).length;
    body = (list.length ? `<div class="card list regd-l">${list.map(row).join('')}</div>` : `<div class="empty"><b>No friends have added their day yet</b></div>`)
      + (!mine ? `<button class="btn soft regd-add" data-a="regDayOpen">Add your day</button>` : '')
      + (missing ? `<div class="regd-note">${regPlural(missing, 'friend')} ${missing === 1 ? 'hasn’t' : 'haven’t'} added theirs.</div>` : '');
  }
  return { body: `<div class="mepg regpg">${head}${body}</div><div class="spacer"></div>`, tabbar: true, fab: true };
};
/* "When do you register?" — Round 1's weekdays, a time, and whether friends see it */
SHEETS.regDay = sh => {
  const today = sloISO(), days = regRoundDays(), busy = !!UI.busy.regDay;
  const lead = days.length ? (new Date(days[0] + 'T12:00:00Z').getUTCDay() + 6) % 7 : 0;
  let prev = '';
  const cells = Array.from({ length: lead }, () => '<span></span>').concat(days.map(d => {
    const lab = prev && d.slice(5, 7) !== prev ? regDayText(d).split(', ')[1] : String(+d.slice(8)); prev = d.slice(5, 7);
    const on = d === sh.day, past = d < today;
    return `<button class="rd-d${on ? ' on' : ''}" data-a="regPickDay" data-x="${d}" aria-pressed="${on}" aria-label="${esc(regDayText(d, true))}"${past ? ' disabled' : ''}>${esc(lab)}</button>`;
  }));
  const span = days.length ? `${regDayText(days[0]).split(', ')[1]} – ${regDayText(days[days.length - 1]).split(', ')[1]}` : '';
  return `<div class="row sb"><h3>When do you register?</h3><button class="xbtn" data-a="closeSheet" aria-label="Close">${ic('x', 16, 2.4)}</button></div>
  <div class="muted b" style="font-size:13.5px;margin:2px 0 12px;line-height:1.4">Cal Poly Portal › Student Center › Enrollment Dates</div>
  <div class="rd-h">Round 1 · ${esc(span)}</div>
  <div class="rd-grid" role="group" aria-label="Your day"><span class="rd-w" aria-hidden="true">Mon</span><span class="rd-w" aria-hidden="true">Tue</span><span class="rd-w" aria-hidden="true">Wed</span><span class="rd-w" aria-hidden="true">Thu</span><span class="rd-w" aria-hidden="true">Fri</span>${cells.join('')}</div>
  <label class="rd-row"><span class="grow b" style="font-size:15px">Time</span><input id="rd-time" type="time" step="300" value="${esc(sh.time || '')}"></label>
  <div class="rd-row"><span class="grow"><span class="b" style="display:block;font-size:15px">Friends can see your day</span><span class="muted b" style="display:block;font-size:12.5px">Only your friends · the day and time</span></span><button class="toggle ${sh.shared ? 'on' : 'off'}" data-a="regShareToggle" role="switch" aria-checked="${!!sh.shared}" aria-label="Friends can see your day"><i></i></button></div>
  ${sh.err ? `<div class="tc-err">${esc(sh.err)}</div>` : ''}
  <button class="btn" style="margin-top:14px" data-a="regDaySave" ${busy || !sh.day ? 'disabled' : ''}>${busy ? 'Saving…' : 'Save'}</button>
  ${TC.regDay ? `<button class="btn soft" style="margin-top:8px" data-a="regDayRemove" ${busy ? 'disabled' : ''}>Remove my day</button>` : ''}`;
};
''' + s[b:]

# 4. actions
one("""  plPrefsOpen: () => { UI.sheet = { type: 'plPrefs' }; render(true); },""",
    """  plPrefsOpen: () => { UI.sheet = { type: 'plPrefs' }; render(true); },
  /* reg-day (2026-10-11) */
  regDayOpen: () => { if (!regWhen()) return; const m = TC.regDay; UI.sheet = { type: 'regDay', day: m ? m.day : '', time: m ? m.time : '', shared: m ? m.shared !== false : true }; render(true); },
  regPickDay: d => { const sh = UI.sheet; if (!sh || sh.type !== 'regDay' || !regRoundDays().includes(d) || d < sloISO()) return; regReadTime(sh); sh.day = d; sh.err = null; render(true); },
  regShareToggle: () => { const sh = UI.sheet; if (!sh || sh.type !== 'regDay') return; regReadTime(sh); sh.shared = !sh.shared; render(true); },
  regDaySave: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'regDay' || UI.busy.regDay) return;
    regReadTime(sh);
    if (!regDayOk(sh.day) || !regRoundDays().includes(sh.day)) { sh.err = 'Pick your day first.'; return render(true); }
    if (sh.time && !regTimeOk(sh.time)) { sh.err = 'That time doesn’t look right.'; return render(true); }
    UI.busy.regDay = 1; render(true);
    let e; try { e = await TC.saveRegDay({ day: sh.day, time: sh.time || '', shared: !!sh.shared }); } catch (x) { e = 'Couldn’t save that — it’s kept on this phone for now.'; }
    UI.busy.regDay = 0; if (UI.sheet === sh) UI.sheet = null;
    toast(e || (TC.err.regDay === 'missing' ? 'Saved on this phone' : 'Your day is saved')); render(true); loadRegFriends(true);
  },
  regDayRemove: async () => {
    const sh = UI.sheet; if (!sh || sh.type !== 'regDay' || UI.busy.regDay) return;
    UI.busy.regDay = 1; render(true);
    let e; try { e = await TC.saveRegDay(null); } catch (x) { e = 'Couldn’t remove it — try again.'; }
    UI.busy.regDay = 0; if (UI.sheet === sh) UI.sheet = null; toast(e || 'Your day is removed'); render(true);
  },
  openRegDays: () => { loadRegFriends(); go('regDays', {}); },
  regDaysRetry: () => { loadRegFriends(true); render(true); },""")
one("""function planCard(k, L, R, why) {""", """function regReadTime(sh) { const el = document.getElementById('rd-time'); if (el) sh.time = String(el.value || '').slice(0, 5); }
function planCard(k, L, R, why) {""")

# 5. loading with everything else; a friend's page asks again when it's stale
one("""blk.then(() => loadThreads()), loadAudit(), loadPrefs()]);""", """blk.then(() => loadThreads()), loadAudit(), loadPrefs(), loadRegDay()]);
  loadRegFriends(true);""")
one("""if (TC.user && TC.friends.includes(id)) loadFof(id); go('friend', { id }); },""",
    """if (TC.user && TC.friends.includes(id)) { loadFof(id); loadRegFriends(); } go('friend', { id }); },""")
one("""  ${isF && !bl ? friendBubbles(p) + fofRow(id) : ''}""", """  ${isF && !bl ? friendBubbles(p) + regFriendRow(id) + fofRow(id) : ''}""")

# 5b. deleting the account leaves nothing of it on the phone
one("""PLDRAFT_KEY(), plSkipKey(), MARKS_KEY()].forEach(k => localStorage.removeItem(k)); } catch (e) {}""", """PLDRAFT_KEY(), plSkipKey(), MARKS_KEY(), REG_KEY()].forEach(k => localStorage.removeItem(k)); } catch (e) {}""")

# 5c. the tiles' styles go with them
a = s.index('.pla-stats{display:grid;'); b = s.index('.pla-dh{display:grid;', a)
assert s.count('.pla-stats{display:grid;') == 1 and s[a:b].count('\n') == 9 and '@media (max-width:345px){.pla-stat{' in s[a:b]
s = s[:a] + s[b:]

# 6. styles
one(""".pla-reg svg{flex:none}""", """.pla-reg svg{flex:none}
/* reg-day (2026-10-11): the line is a button; yours is blue; friends' days under it */
button.pla-reg{width:calc(100% - 32px);min-height:44px;border:0;text-align:left;font:inherit;font-size:13.5px;font-weight:900;line-height:1.3;cursor:pointer}
.w12 button.pla-reg{width:calc(100% - 24px)}
.pla-reg .grow{flex:1;min-width:0}
.pla-reg.mine{background:var(--blue-soft);color:var(--blue-ink)}
.pla-add{flex:none;display:inline-flex;align-items:center;gap:2px;white-space:nowrap}
.reg-fr{display:flex;align-items:center;gap:8px;width:calc(100% - 32px);min-height:44px;margin:2px 16px 0;padding:4px 6px;border:0;background:none;color:var(--ink3);font:inherit;font-size:13px;font-weight:800;text-align:left;cursor:pointer}
.w12 .reg-fr{margin-left:12px;margin-right:12px;width:calc(100% - 24px)}
.reg-fr .grow{flex:1;min-width:0}
.reg-fr svg{flex:none}
.regrow{display:flex;align-items:center;gap:10px;min-height:44px;padding:8px 12px;border-radius:16px;background:var(--blue-soft);color:var(--blue-ink);font-size:13.5px;font-weight:700;line-height:1.3;box-sizing:border-box}
.regrow b{font-weight:900}
.regrow svg{flex:none}
.regd-l{margin:0 12px}
.regd{display:flex;align-items:center;gap:12px;width:100%;min-height:64px;text-align:left}
.regd.me{background:var(--blue-soft);color:var(--blue-ink)}
.regd-d{flex:none;width:56px;text-align:center;line-height:1.15}
.regd-d b{display:block;font-size:11px;font-weight:900;letter-spacing:.06em;opacity:.8}
.regd-d span{display:block;font-size:17px;font-weight:900}
.regd-w{min-width:0}
.regd-n{display:block;font-size:15px;font-weight:900;overflow-wrap:anywhere}
.regd-s{display:block;font-size:12.5px;font-weight:800;color:var(--muted)}
.regd.me .regd-s{color:inherit}
.regd-add{margin:12px 12px 0;width:calc(100% - 24px)}
.regd-note{margin:12px 18px 0;font-size:13px;font-weight:800;color:var(--muted)}
.rd-h{font-size:12px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.rd-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;margin-bottom:12px}
.rd-w{font-size:10.5px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);text-align:center}
.rd-d{min-height:44px;border:0;border-radius:12px;background:var(--bg);color:var(--ink);font:inherit;font-size:15px;font-weight:900;cursor:pointer}
.rd-d.on{background:var(--blue);color:#fff}
.rd-d:disabled{background:none;color:var(--muted2);cursor:default;text-decoration:line-through}
.rd-row{display:flex;align-items:center;gap:12px;min-height:52px;padding:6px 12px;margin-top:8px;border-radius:14px;background:var(--bg)}
.rd-row .toggle{position:relative}
.rd-row .toggle::after{content:'';position:absolute;left:-6px;right:-6px;top:-6px;bottom:-6px}   /* 46px to tap */
.rd-row input[type=time]{height:40px;min-width:118px;border:0;border-radius:10px;padding:0 10px;background:var(--card);color:var(--ink);font:inherit;font-size:15px;font-weight:900}""")

f.write_text(s)
print('patched', f)
