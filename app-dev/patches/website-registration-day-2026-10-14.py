#!/usr/bin/env python3
"""Your registration day, on the website (Tate, 2026-10-14: catch termchamp.com up to the phone).

The phone has had this since 2026-10-11 (app-dev/patches/registration-day-2026-10-11.py, "Your Registration Day"):
people have different registration appointments, so you can say yours and let friends see it, and start planning
before it. This is the same thing in index.html, against the same table and function (sql/professify-registration-days.sql,
RUN 17: registration_days is yours alone; friend_registration_days(p_term) answers only with your accepted same-school
friends who shared, never anyone blocked on either side).

- Config: REGISTRATION_TERM_CODE '2274' and REGISTRATION_ROUND1_ENDS '2026-11-03' (the phone's CFG), beside the
  existing REGISTRATION_OPENS / ROUND2 / OPEN_ENROLLMENT / REGISTRATION_TERM.
- Data layer (its own <script>, ahead of the Plans module): yours is local-first — the change is kept on this device the
  moment you save it, goes up to registration_days (upsert on user_id,term; delete for Clear), and if the write is
  refused or offline the local value stays and goes up again on `online`, when the tab comes back, and on a slow timer.
  The server's row wins only when this device has nothing waiting. Friends' days come from the RPC (term '2274'), asked
  once, again after 2 minutes, 15 seconds after a failure, 10 s timeout. A missing table/function (schemaGap / rpcMissing)
  degrades exactly like the phone: your day stays on this device, friends' days don't show.
- The card, "Your registration day": on Schedule > Plans (top of the pane) and on Home's right rail (only from 14 days
  before Round 1 through its last day). "Register Wed, Oct 21, 11a · in 9 days" (tomorrow / today at 11a · in 2h 15m /
  "Your registration opened at 11a" — the phone's words), or "Set your registration day" with when Round 1 opens.
  Gone when you are signed out, when the term you choose in is not the registration term, after Round 1's last day, and
  (like the phone) the day after your own day.
- The modal "When do you register?": Round 1's weekdays (Oct 19 – Nov 3, 2026, past days off), a time you type like
  the Portal shows it (11a, 11:30 am, 2pm, 14:30 — anything else says so), "Friends can see your day" (on by default,
  like Plans), Save and Clear. Website modal pattern (.mback, openModalA11y, Escape, focus back).
- Friends' days under the card: only friends who shared and whose day is still to come, soonest first, each with how
  far before or after yours; "N friends haven't set theirs". Not drawn at all until at least one friend shared.
- The campus banner ("Round 1 registration opens in N days") gains "Set your registration day" ("Change your registration day" once you have one).
- Kept under professify_regday_<user>_<term>, so Delete my account (which clears every professify* key) takes it too.
  Nothing about a grade, an EMPLID or a non-friend is stored.

Usage: python3 website-registration-day-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-registration-day (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

# ================================================================ 1. config
one("""  REGISTRATION_TERM: 'Spring 2027',
  QUARTER_END: '',""", """  REGISTRATION_TERM: 'Spring 2027',
  /* website-registration-day (2026-10-14), the phone's CFG: the code your registration day is kept under, and
     Round 1's last day — "Round 1 ends Nov 3" (registrar.calpoly.edu, Spring 2027 registration calendar). */
  REGISTRATION_TERM_CODE: '2274',
  REGISTRATION_ROUND1_ENDS: '2026-11-03',
  QUARTER_END: '',""")

# ================================================================ 2. the module: styles + data layer + card + modal
BLOCK = r'''<!-- REGDAY:BEGIN website-registration-day (2026-10-14) — patches/website-registration-day-2026-10-14.py -->
<style id="regday-css">
/* Your registration day. App tokens only; 44px targets; text on --blue-soft uses --blue-ink. */
.rg-slot:empty{display:none}
.rg-card{display:flex;flex-direction:column;gap:10px;margin-bottom:12px}
.pl3 > .rg-slot .rg-card{margin-bottom:0;max-width:760px;width:100%}
.rg-top{display:flex;align-items:center;gap:12px}
.rg-ic{flex:none;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--blue-soft);color:var(--blue-ink)}
.rg-ic svg{width:19px;height:19px}
.rg-tx{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px}
.rg-h{font-size:15px;font-weight:700;color:var(--text);line-height:1.3;letter-spacing:-.01em}
.rg-nw{white-space:nowrap}
.rg-s{font-size:13px;font-weight:600;color:var(--text-2);line-height:1.3}
.rg-btn{flex:none;min-height:44px;padding:0 16px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--text);font:inherit;font-size:13.5px;font-weight:700;cursor:pointer}
.rg-btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
@media (hover:hover){.rg-btn:hover{border-color:rgba(var(--accent-rgb),.55)}.rg-f:hover{background:var(--panel-2)}}
.rg-btn:focus-visible,.rg-f:focus-visible,.rg-d:focus-visible,.rg-tog:focus-visible,.rg-in:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.rg-note{font-size:12.5px;font-weight:600;color:var(--text-2);margin:-2px 0 0 48px}
.rg-fr{border-top:1px solid var(--line);padding-top:8px;display:flex;flex-direction:column;gap:2px}
.rg-frh{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-2);padding:2px 6px}
.rg-fl{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.rg-f{display:flex;align-items:center;gap:10px;width:100%;min-height:48px;padding:5px 6px;border:0;border-radius:12px;background:none;color:var(--text);font:inherit;text-align:left;cursor:pointer}
.rg-face{flex:none;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;color:#fff;font-size:11.5px;font-weight:700}
.rg-face img{width:100%;height:100%;object-fit:cover;display:block}
.rg-fw{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px}
.rg-fn{font-size:14px;font-weight:700;line-height:1.25;overflow-wrap:anywhere}
.rg-fd{font-size:12.5px;font-weight:600;color:var(--text-2);line-height:1.3}
.rg-more,.rg-miss{font-size:12.5px;font-weight:600;color:var(--text-2);padding:4px 6px}
button.rg-more{border:0;background:none;font:inherit;font-size:12.5px;font-weight:700;color:var(--blue-ink);text-align:left;min-height:36px;cursor:pointer}
/* the banner now carries a second button: let it wrap instead of running off a phone */
@media (max-width:760px){.campus-banner{flex-wrap:wrap}.campus-banner>span:nth-child(2){flex:1 1 calc(100% - 40px);min-width:0}.campus-banner .btn{min-height:44px}.campus-banner .cb-x{margin-left:auto}}
/* the modal */
.rg-modal{max-width:460px;position:relative}
#rgModal .mclose{position:absolute;top:14px;right:14px;left:auto;z-index:3}
.rg-m{padding:26px 24px 22px;display:flex;flex-direction:column}
.rg-m .rate-h{margin:0 40px 4px 0}
.rg-hint{font-size:13.5px;color:var(--text-2);margin:0 0 14px;line-height:1.4}
.rg-sec{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-2);margin-bottom:6px}
.rg-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;margin-bottom:12px}
.rg-w{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-2);text-align:center}
.rg-d{min-height:44px;border:1px solid var(--line);border-radius:12px;background:var(--panel-2);color:var(--text);font:inherit;font-size:15px;font-weight:700;cursor:pointer}
.rg-d.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.rg-d:disabled{background:none;border-color:transparent;color:var(--text-2);opacity:.7;cursor:default;text-decoration:line-through}
.rg-row{display:flex;align-items:center;gap:12px;min-height:54px;padding:6px 12px;margin-top:8px;border-radius:14px;background:var(--panel-2)}
.rg-rl{flex:1;min-width:0;font-size:14.5px;font-weight:700;color:var(--text)}
.rg-rl em{display:block;font-style:normal;font-size:12.5px;font-weight:600;color:var(--text-2)}
.rg-in{width:130px;height:40px;border:1px solid var(--line);border-radius:10px;padding:0 10px;background:var(--panel);color:var(--text);font:inherit;font-size:15px;font-weight:700}
.rg-tog{flex:none;position:relative;width:46px;height:28px;border-radius:999px;border:1px solid var(--line);background:var(--panel-3);cursor:pointer;padding:0}
.rg-tog::before{content:'';position:absolute;left:3px;top:3px;width:20px;height:20px;border-radius:50%;background:var(--text-2);transition:transform .15s}
.rg-tog::after{content:'';position:absolute;inset:-8px -4px}
.rg-tog[aria-checked="true"]{background:var(--accent);border-color:var(--accent)}
.rg-tog[aria-checked="true"]::before{transform:translateX(18px);background:var(--accent-ink)}
.rg-err{margin-top:10px;font-size:13.5px;font-weight:600;color:var(--low)}
.rg-acts{display:flex;gap:8px;margin-top:16px}
.rg-acts .btn{flex:1;min-height:46px;border-radius:999px}
.rg-acts .btn:not(.primary){background:var(--panel-2);border-color:var(--line);color:var(--text)}
.rg-acts .btn:disabled{opacity:.55;cursor:default}
@media (max-width:520px){.rg-m{padding:22px 16px 18px}.rg-note{margin-left:0}}
@media (max-width:359px){.rg-top{flex-wrap:wrap}}
</style>
<script id="regday-js">
(function () {
  'use strict';
  /* RG.day = { day 'YYYY-MM-DD', time 'HH:MM' or '', shared, local } | null — yours, from registration_days (RUN 17) or
     this device. RG.fr = { rows: [{ id, day, time }], at, off } | { err, at } — friends' days from
     friend_registration_days(). Days are Pacific calendar days, like the registrar's. */
  var RG = { day: null, fr: null, frBusy: 0, gen: 0, gap: false, retrying: 0, retryN: 0, retryT: null, uid: null, loaded: false };
  var M = null;                                   /* the open modal: { day, time, shared, err, busy } */
  var REG_TTL = 120000, REG_ERR_TTL = 15000, RETRY_EVERY = 60000, RETRY_MAX = 8;
  function cfgv(k) { try { return String((window.PROFESSIFY_CONFIG || {})[k] || ''); } catch (_) { return ''; } }
  function user() { try { return (typeof sbUser !== 'undefined' && sbUser) ? sbUser : null; } catch (_) { return null; } }
  function client() { try { return (typeof sb !== 'undefined' && sb) ? sb : null; } catch (_) { return null; } }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function code() { return cfgv('REGISTRATION_TERM_CODE'); }
  function key() { var u = user(); return 'professify_regday_' + (u ? u.id : '') + '_' + code(); }
  function today() { try { return mcPacificDay(); } catch (_) { return new Date().toISOString().slice(0, 10); } }
  function endDay() { return cfgv('REGISTRATION_ROUND1_ENDS') || cfgv('REGISTRATION_OPENS'); }
  function isoAdd(iso, n) { return new Date(Date.parse(iso + 'T12:00:00Z') + n * 864e5).toISOString().slice(0, 10); }
  function gap(a, b) { return Math.round((Date.parse(b + 'T12:00:00Z') - Date.parse(a + 'T12:00:00Z')) / 864e5); }
  function plural(n, w) { return n + ' ' + w + (n === 1 ? '' : 's'); }
  var dayOk = function (d) { return /^\d{4}-\d{2}-\d{2}$/.test(String(d || '')); };
  var timeOk = function (t) { return /^([01]\d|2[0-3]):[0-5]\d$/.test(String(t || '')); };
  var time5 = function (t) { var v = String(t || '').slice(0, 5); return timeOk(v) ? v : ''; };
  /* Registering is for the term you choose in; signed in; and only until Round 1's last day */
  function active() {
    if (!user() || !client() || !code() || !cfgv('REGISTRATION_OPENS')) return false;
    try { if (String(mcTerm()) !== code()) return false; } catch (_) { return false; }
    return today() <= endDay();
  }
  /* Home's rail: from 14 days before Round 1 through its last day */
  function railOn() { return active() && today() >= isoAdd(cfgv('REGISTRATION_OPENS'), -14); }
  function roundDays() {
    var out = [], o = cfgv('REGISTRATION_OPENS'), e = endDay();
    for (var t = Date.parse(o + 'T12:00:00Z'), end = Date.parse(e + 'T12:00:00Z'); t <= end && out.length < 60; t += 864e5) {
      var d = new Date(t), wd = d.getUTCDay(); if (wd > 0 && wd < 6) out.push(d.toISOString().slice(0, 10));
    }
    return out;
  }
  function dayText(d, long) {
    try { return new Date(d + 'T12:00:00Z').toLocaleDateString('en-US', { timeZone: 'UTC', weekday: long ? 'long' : 'short', month: long ? 'long' : 'short', day: 'numeric' }); } catch (_) { return d; }
  }
  function timeText(t) {
    if (!timeOk(t)) return '';
    var h = +t.slice(0, 2), m = +t.slice(3, 5), ap = h >= 12 ? 'p' : 'a';
    h = h % 12 || 12; return h + (m ? ':' + (m < 10 ? '0' : '') + m : '') + ap;
  }
  function pacificMin() {
    try {
      var p = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
      return (+p.hour % 24) * 60 + +p.minute;
    } catch (_) { var d = new Date(); return d.getHours() * 60 + d.getMinutes(); }
  }
  /* A time as the Portal shows it: 11a · 11:30 am · 2pm · 2:15 P.M. · 14:30 · 08:30 · 830a. Empty is fine (it is
     optional). A bare "8" or "9:30" could be either half of the day, so it is not guessed. → { ok, time:'HH:MM'|'' } */
  function parseTime(raw) {
    var s = String(raw == null ? '' : raw).toLowerCase().replace(/[\s.]/g, '');
    if (!s) return { ok: true, time: '' };
    var m = /^(\d{1,2}):?(\d{2})?(am|pm|a|p)?$/.exec(s);
    if (!m) return { ok: false, time: '' };
    var h = +m[1], mi = m[2] ? +m[2] : 0, ap = m[3] ? m[3].charAt(0) : '';
    if (mi > 59) return { ok: false, time: '' };
    if (ap) { if (h < 1 || h > 12) return { ok: false, time: '' }; h = (h % 12) + (ap === 'p' ? 12 : 0); }
    else if (!(h >= 13 || (m[1].length === 2 && m[1].charAt(0) === '0'))) return { ok: false, time: '' };
    if (h > 23) return { ok: false, time: '' };
    return { ok: true, time: (h < 10 ? '0' : '') + h + ':' + (mi < 10 ? '0' : '') + mi };
  }

  /* ---------------------------------------------------------------- yours: this device first, then the account */
  function keep(v, pending) {
    try {
      if (!pending) { if (v) localStorage.setItem(key(), JSON.stringify({ day: v.day, time: v.time, shared: v.shared })); else localStorage.removeItem(key()); }
      else localStorage.setItem(key(), JSON.stringify(v ? { day: v.day, time: v.time, shared: v.shared, at: Date.now(), pending: true } : { gone: true, at: Date.now(), pending: true }));
    } catch (_) {}
  }
  function readLocal() { var loc = null; try { loc = JSON.parse(localStorage.getItem(key()) || 'null'); } catch (_) {} return loc; }
  function pendingLocal() { var l = readLocal(); return !!(l && l.pending); }
  async function loadMine() {
    RG.day = null; RG.gap = false; RG.loaded = false;
    if (!active()) return;
    var loc = readLocal();
    if (loc && !loc.gone && !dayOk(loc.day)) loc = null;
    if (loc && !loc.gone) RG.day = { day: loc.day, time: time5(loc.time), shared: loc.shared !== false, local: true };
    var gen = RG.gen, u = user(), r;
    try { r = await client().from('registration_days').select('day,at_time,shared,updated_at').eq('user_id', u.id).eq('term', code()).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
    if (RG.gen !== gen || !user() || user().id !== u.id) return;           /* a save while this was in flight: that one stands */
    RG.loaded = true;
    if (r.error) { if (schemaGap(r.error)) RG.gap = true; repaint(); return; }
    var row = r.data && dayOk(r.data.day) ? r.data : null;
    if (loc && loc.pending && (!row || !row.updated_at || Date.parse(row.updated_at) < (+loc.at || 0))) { await push(loc.gone ? null : RG.day); armRetry(); repaint(); return; }
    RG.day = row ? { day: row.day, time: time5(row.at_time), shared: row.shared !== false, local: false } : null;
    keep(RG.day, false); repaint();
  }
  /* up to the account; null removes it. Returns what to tell the student, or null. */
  async function push(v) {
    if (RG.gap) return null;
    var c = client(), u = user(); if (!c || !u) return null;
    var q;
    try {
      q = v ? await c.from('registration_days').upsert({ user_id: u.id, term: code(), day: v.day, at_time: v.time || null, shared: !!v.shared, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' })
        : await c.from('registration_days').delete().eq('user_id', u.id).eq('term', code());
    } catch (e) { q = { error: { message: String((e && e.message) || e) } }; }
    if (q.error) {
      if (schemaGap(q.error)) { RG.gap = true; return null; }
      /* taking it away or hiding it: until it goes through, friends still see it — say so, never "saved" */
      return (!v || !v.shared) ? 'Not done yet — friends can still see your day until it goes through.' : 'Couldn’t save that to your account yet — it’s kept on this device.';
    }
    if (v && RG.day === v) v.local = false;
    keep(v, false); return null;
  }
  async function saveMine(v) {
    RG.gen++;
    RG.day = v ? { day: v.day, time: time5(v.time), shared: v.shared !== false, local: true } : null;
    keep(RG.day, true);
    var e = await push(RG.day);
    if (e) armRetry();
    RG.fr = RG.fr && RG.fr.rows ? Object.assign(RG.fr, { at: 0 }) : RG.fr;   /* "before you" moves with your day */
    return e;
  }
  /* a change kept on this device goes up when it is back online, the tab comes to the front, and on a slow timer */
  async function retry() {
    if (!active() || RG.retrying || RG.gap) return;
    var loc = readLocal();
    if (!loc || !loc.pending || (!loc.gone && !RG.day)) return;
    RG.retrying = 1;
    try { var e = await push(loc.gone ? null : RG.day); if (!e) { loadFriends(true); repaint(); } else armRetry(); } finally { RG.retrying = 0; }
  }
  function armRetry() {
    if (RG.retryT || RG.retryN >= RETRY_MAX) return;
    RG.retryN++;
    RG.retryT = setTimeout(function () { RG.retryT = null; retry(); }, RETRY_EVERY);
  }

  /* ---------------------------------------------------------------- friends' days */
  async function loadFriends(force) {
    if (!active() || RG.frBusy) return;
    var was = RG.fr;
    if (!force && was && (was.off || Date.now() - was.at < (was.err ? REG_ERR_TTL : REG_TTL))) return;
    RG.frBusy = 1;
    var u = user(), r, timer;
    try {
      r = await Promise.race([client().rpc('friend_registration_days', { p_term: code() }), new Promise(function (_, no) { timer = setTimeout(function () { no(new Error('timeout')); }, 10000); })]);
    } catch (e) { r = { error: { message: String((e && e.message) || e) } }; }
    clearTimeout(timer);
    RG.frBusy = 0;
    if (!user() || user().id !== (u && u.id)) return;
    if (r.error && (typeof rpcMissing === 'function' ? rpcMissing(r.error) : schemaGap(r.error))) RG.fr = { rows: [], at: Date.now(), off: true };
    else if (r.error) { if (was && was.rows) was.at = Date.now() - REG_TTL + REG_ERR_TTL; else RG.fr = { err: 1, at: Date.now() }; }
    else {
      var seen = {};
      RG.fr = { rows: (Array.isArray(r.data) ? r.data : []).filter(function (x) { return x && x.user_id && dayOk(x.day) && !seen[x.user_id] && (seen[x.user_id] = 1); })
        .map(function (x) { return { id: x.user_id, day: x.day, time: time5(x.at_time) }; }), at: Date.now() };
    }
    repaint();
  }
  function friendOf(id) { try { return (typeof friendsList !== 'undefined' ? friendsList : []).filter(function (f) { return f.id === id; })[0] || null; } catch (_) { return null; } }
  function blocked(id) { try { return typeof isBlocked === 'function' && isBlocked(id); } catch (_) { return false; } }
  /* friends' days as they stand now: friends only, never someone you blocked, by day then time then name */
  function frRows() {
    var F = RG.fr; if (!F || !F.rows) return [];
    return F.rows.filter(function (x) { return friendOf(x.id) && !blocked(x.id); }).sort(function (a, b) {
      return a.day.localeCompare(b.day) || (a.time || '99').localeCompare(b.time || '99') || String(friendOf(a.id).name || '').localeCompare(String(friendOf(b.id).name || ''));
    });
  }
  /* "2 days before you" · "same day as you" · "3 days after you" */
  function rel(day) {
    var m = RG.day; if (!m) return '';
    var d = gap(m.day, day);
    return !d ? 'same day as you' : d < 0 ? plural(-d, 'day') + ' before you' : plural(d, 'day') + ' after you';
  }

  /* ---------------------------------------------------------------- the card */
  var ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4.5" width="18" height="16" rx="2.5"/><path d="M3 9h18M8 2.5v4M16 2.5v4"/></svg>';
  function face(f) {
    var ini = ''; try { ini = (typeof hmIni === 'function') ? hmIni(f.name) : String(f.name || '?').slice(0, 2).toUpperCase(); } catch (_) { ini = '?'; }
    var bg = '#5E7A8A'; try { bg = hmFriendColor(f) || bg; } catch (_) {}
    var img = f.avatar_url ? '<img src="' + esc(f.avatar_url) + '" alt="" loading="lazy">' : esc(String(ini).slice(0, 2));
    return '<span class="rg-face" style="background:' + esc(bg) + '" aria-hidden="true">' + img + '</span>';
  }
  /* head + sub for the card, from your day or from Round 1's dates */
  function lines() {
    var td = today(), mine = RG.day, m = mine && mine.day >= td ? mine : null;
    if (m) {
      var n = gap(td, m.day), t = timeText(m.time), head, sub = '';
      if (n > 1) { head = 'Register ' + dayText(m.day) + (t ? ', ' + t : ''); sub = 'in ' + n + ' days'; }
      else if (n === 1) head = 'Register tomorrow' + (t ? ', ' + t : '');
      else {
        var left = m.time ? +m.time.slice(0, 2) * 60 + +m.time.slice(3, 5) - pacificMin() : null;
        if (left == null) head = 'Register today';
        else if (left > 0) { head = 'Register today at ' + t; sub = 'in ' + (left >= 60 ? Math.floor(left / 60) + 'h ' : '') + (left % 60) + 'm'; }
        else head = 'Your registration opened at ' + t;
      }
      return { set: true, head: head, sub: sub, full: dayText(m.day, true) + ', ' + m.day.slice(0, 4) };
    }
    if (mine) return null;                           /* the day has passed: gone, like the phone */
    var o = cfgv('REGISTRATION_OPENS'), k = gap(td, o), s2;
    var oShort = dayText(o).split(', ')[1];
    if (k > 1) s2 = 'Opens ' + oShort + ' · in ' + k + ' days';
    else if (k === 1) s2 = 'Opens tomorrow';
    else s2 = 'Round 1 is open · ends ' + dayText(endDay()).split(', ')[1];
    return { set: false, head: 'Set your registration day', sub: s2 };
  }
  /* the date part never breaks across lines: "Register" over "Wed, Oct 21, 11a" on a narrow rail */
  function headHtml(h) { var m = /^(Register |Your registration opened at )(.+)$/.exec(h); return m ? esc(m[1]) + '<span class="rg-nw">' + esc(m[2]) + '</span>' : esc(h); }
  function cardHtml(where) {
    if (!active() || (where === 'rail' && !railOn())) return '';
    var L = lines(); if (!L) return '';
    if (!RG.fr && !RG.frBusy) setTimeout(function () { loadFriends(); }, 0);
    var td = today(), up = frRows().filter(function (x) { return x.day >= td; });
    var h = '<section class="hm-card rg-card" data-rg-state="' + (L.set ? 'set' : 'none') + '" aria-label="Your registration day"' + (L.full ? ' title="' + esc(L.full) + '"' : '') + '>'
      + '<div class="rg-top"><span class="rg-ic">' + ICON + '</span><div class="rg-tx"><b class="rg-h">' + headHtml(L.head) + '</b>'
      + (L.sub ? '<span class="rg-s">' + esc(L.sub) + '</span>' : '') + '</div>'
      + '<button type="button" class="rg-btn' + (L.set ? '' : ' pri') + '" data-rg-act="open">' + (L.set ? 'Change' : 'Set day') + '</button></div>';
    if (RG.day && (RG.gap || RG.day.local)) {
      h += '<div class="rg-note" data-rg-note="1">' + (RG.gap ? 'Kept on this device only.' : 'Kept on this device — not saved to your account yet.') + '</div>';
    }
    if (up.length) {
      var cap = where === 'rail' ? 3 : 12, shown = up.slice(0, cap);
      var shared = {}; frRows().forEach(function (x) { shared[x.id] = 1; });
      var missing = 0; try { friendsList.forEach(function (f) { if (!shared[f.id] && !blocked(f.id)) missing++; }); } catch (_) {}
      h += '<div class="rg-fr"><div class="rg-frh">Friends’ days</div><ul class="rg-fl">' + shown.map(function (x) {
        var f = friendOf(x.id), t = timeText(x.time), r = x.day === td ? 'today' : rel(x.day);
        var d = x.day === td ? ('Today' + (t ? ' at ' + t : '')) : (dayText(x.day) + (t ? ' · ' + t : ''));
        return '<li><button type="button" class="rg-f" data-rg-act="friend" data-id="' + esc(x.id) + '">' + face(f)
          + '<span class="rg-fw"><span class="rg-fn">' + esc(f.name || 'Classmate') + '</span><span class="rg-fd">' + esc(d + (r && x.day !== td ? ' · ' + r : '')) + '</span></span></button></li>';
      }).join('') + '</ul>';
      if (up.length > shown.length) {
        var more = up.length - shown.length;
        h += where === 'rail' ? '<button type="button" class="rg-more" data-rg-act="all">+' + more + ' more in Plans</button>' : '<div class="rg-more">+' + more + ' more</div>';
      }
      if (missing) h += '<div class="rg-miss">' + plural(missing, 'friend') + ' ' + (missing === 1 ? 'hasn’t' : 'haven’t') + ' set theirs</div>';
      h += '</div>';
    }
    return h + '</section>';
  }
  function slotHtml(where) { return '<div class="rg-slot" data-rg="' + where + '">' + cardHtml(where) + '</div>'; }
  function repaint() {
    try { var els = document.querySelectorAll('.rg-slot'); for (var i = 0; i < els.length; i++) els[i].innerHTML = cardHtml(els[i].getAttribute('data-rg')); } catch (_) {}
    try { if (typeof renderCampusBanner === 'function') renderCampusBanner(); } catch (_) {}
    try { if (M) paintModal(); } catch (_) {}
  }

  /* ---------------------------------------------------------------- the modal */
  function back() {
    var b = document.getElementById('rgBack');
    if (!b) {
      b = document.createElement('div'); b.id = 'rgBack'; b.className = 'mback';
      b.innerHTML = '<div class="modal rg-modal" id="rgModal" role="dialog" aria-modal="true" aria-labelledby="rgTitle"></div>';
      b.addEventListener('click', function (e) { if (e.target === b) closeModal(); });
      document.body.appendChild(b);
    }
    return b;
  }
  function modalHtml() {
    var td = today(), days = roundDays(), busy = !!M.busy;
    var lead = days.length ? (new Date(days[0] + 'T12:00:00Z').getUTCDay() + 6) % 7 : 0, prev = '';
    var cells = []; for (var i = 0; i < lead; i++) cells.push('<span></span>');
    days.forEach(function (d) {
      var lab = prev && d.slice(5, 7) !== prev ? dayText(d).split(', ')[1] : String(+d.slice(8)); prev = d.slice(5, 7);
      var on = d === M.day;
      cells.push('<button type="button" class="rg-d' + (on ? ' on' : '') + '" data-rg-act="day" data-day="' + d + '" data-rg-key="d:' + d + '" aria-pressed="' + on + '" aria-label="' + esc(dayText(d, true)) + '"' + (d < td ? ' disabled' : '') + '>' + esc(lab) + '</button>');
    });
    var span = days.length ? dayText(days[0]).split(', ')[1] + ' – ' + dayText(days[days.length - 1]).split(', ')[1] + ', ' + days[days.length - 1].slice(0, 4) : '';
    return '<button type="button" class="mclose" data-rg-act="close" aria-label="Close">&times;</button><div class="rg-m">'
      + '<h2 class="rate-h" id="rgTitle">When do you register?</h2>'
      + '<p class="rg-hint">Cal Poly Portal › Student Center › Enrollment Dates</p>'
      + '<div class="rg-sec">Round 1 · ' + esc(span) + '</div>'
      + '<div class="rg-grid" role="group" aria-label="Your day"><span class="rg-w" aria-hidden="true">Mon</span><span class="rg-w" aria-hidden="true">Tue</span><span class="rg-w" aria-hidden="true">Wed</span><span class="rg-w" aria-hidden="true">Thu</span><span class="rg-w" aria-hidden="true">Fri</span>' + cells.join('') + '</div>'
      + '<label class="rg-row"><span class="rg-rl">Time<em>Optional · like 11a or 2:30p</em></span><input id="rgTime" class="rg-in" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-rg-key="time" placeholder="11a" value="' + esc(M.time) + '"></label>'
      + '<div class="rg-row"><span class="rg-rl" id="rgShareL">Friends can see your day<em>Only your friends · the day and time</em></span><button type="button" class="rg-tog" role="switch" aria-checked="' + !!M.shared + '" aria-labelledby="rgShareL" data-rg-act="share" data-rg-key="share"></button></div>'
      + (M.err ? '<div class="rg-err" role="alert" id="rgErr">' + esc(M.err) + '</div>' : '')
      + '<div class="rg-acts"><button type="button" class="btn primary" data-rg-act="save" data-rg-key="save"' + (busy ? ' disabled' : '') + '>' + (busy ? 'Saving…' : 'Save') + '</button>'
      + (RG.day ? '<button type="button" class="btn" data-rg-act="clear" data-rg-key="clear"' + (busy ? ' disabled' : '') + '>Clear</button>' : '') + '</div></div>';
  }
  function paintModal() {
    var el = document.getElementById('rgModal'); if (!el || !M) return;
    var a = document.activeElement, k = a && a.getAttribute && a.getAttribute('data-rg-key'), inside = a && el.contains(a), caret = null;
    if (inside && a.id === 'rgTime') { try { caret = a.selectionStart; } catch (_) {} }
    el.innerHTML = modalHtml();
    if (inside && k) { var n = el.querySelector('[data-rg-key="' + k + '"]'); if (n && !n.disabled) { n.focus({ preventScroll: true }); if (caret != null) { try { n.setSelectionRange(caret, caret); } catch (_) {} } } }
  }
  function readTime() { var el = document.getElementById('rgTime'); if (el && M) M.time = String(el.value || '').slice(0, 24); }
  function openModal() {
    if (!active()) return;
    var m = RG.day;
    M = { day: m ? m.day : '', time: m ? timeText(m.time) : '', shared: m ? m.shared !== false : true, err: '', busy: 0 };
    var b = back(); paintModal();
    b.classList.add('open'); document.body.style.overflow = 'hidden';
    openModalA11y('rgBack');
    var f = document.querySelector('#rgModal .rg-d.on') || document.querySelector('#rgModal .rg-d:not(:disabled)'); if (f) setTimeout(function () { try { f.focus({ preventScroll: true }); } catch (_) {} }, 60);
  }
  function closeModal() {
    var b = document.getElementById('rgBack'); if (b) b.classList.remove('open');
    M = null;
    document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : '';
    try { closeModalA11y(); } catch (_) {}
  }
  async function doSave() {
    if (!M || M.busy) return;
    readTime();
    if (!dayOk(M.day) || roundDays().indexOf(M.day) < 0 || M.day < today()) { M.err = 'Pick your day first.'; return paintModal(); }
    var p = parseTime(M.time);
    if (!p.ok) { M.err = 'That time doesn’t look right — try 11a or 2:30p.'; return paintModal(); }
    var mm = M; M.busy = 1; M.err = ''; paintModal();
    var e; try { e = await saveMine({ day: M.day, time: p.time, shared: !!M.shared }); } catch (x) { e = 'Couldn’t save that to your account yet — it’s kept on this device.'; }
    mm.busy = 0; if (M === mm) closeModal();
    toast(e || (RG.gap ? 'Saved on this device' : 'Your registration day is saved'));
    repaint(); loadFriends(true);
  }
  async function doClear() {
    if (!M || M.busy) return;
    var mm = M; M.busy = 1; paintModal();
    var e; try { e = await saveMine(null); } catch (x) { e = 'Couldn’t remove it — try again.'; }
    mm.busy = 0; if (M === mm) closeModal();
    toast(e || 'Your registration day is cleared'); repaint();
  }
  function toast(m) { try { frToast(m); } catch (_) {} }

  document.addEventListener('click', function (e) {
    var t = e.target && e.target.closest ? e.target.closest('[data-rg-act]') : null; if (!t) return;
    var a = t.getAttribute('data-rg-act');
    if (a === 'open') openModal();
    else if (a === 'close') closeModal();
    else if (a === 'day') { if (!M) return; readTime(); var d = t.getAttribute('data-day'); if (roundDays().indexOf(d) < 0 || d < today()) return; M.day = d; M.err = ''; paintModal(); }
    else if (a === 'share') { if (!M) return; readTime(); M.shared = !M.shared; paintModal(); }
    else if (a === 'save') doSave();
    else if (a === 'clear') doClear();
    else if (a === 'friend') { try { openFriendProfile(t.getAttribute('data-id')); } catch (_) {} }
    else if (a === 'all') { try { show('sched'); setSchedTab('watch'); } catch (_) {} }
  });
  document.addEventListener('input', function (e) { if (e.target && e.target.id === 'rgTime' && M) { M.time = String(e.target.value || '').slice(0, 24); } }, true);
  document.addEventListener('keydown', function (e) {
    var b = document.getElementById('rgBack'); if (!b || !b.classList.contains('open')) return;
    if (e.key === 'Escape' || e.key === 'Esc') { e.preventDefault(); e.stopPropagation(); closeModal(); }
    else if (e.key === 'Enter' && e.target && e.target.id === 'rgTime') { e.preventDefault(); doSave(); }
  }, true);
  window.addEventListener('online', function () { retry(); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') retry(); });

  /* ---------------------------------------------------------------- signing in and out */
  function boot() {
    var u = user();
    if (!u) { reset(); return; }
    if (RG.uid !== u.id) { if (RG.uid) reset(); RG.uid = u.id; }
    if (!active()) { repaint(); return; }
    loadMine().then(function () { if (!RG.fr) loadFriends(true); });
    /* the friends list (names, faces) may land after the days do: draw again once it has */
    var tries = 0; (function wait() {
      var ok = false; try { ok = !!friendsLoaded; } catch (_) {}
      if (ok || ++tries > 20) { repaint(); return; }
      setTimeout(wait, 500);
    })();
  }
  function reset() {
    RG.day = null; RG.fr = null; RG.frBusy = 0; RG.gen++; RG.gap = false; RG.loaded = false; RG.uid = null; RG.retryN = 0;
    clearTimeout(RG.retryT); RG.retryT = null; M = null;
    var b = document.getElementById('rgBack'); if (b && b.classList.contains('open')) { b.classList.remove('open'); document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : ''; }
    repaint();
  }
  window.regSlotHtml = slotHtml;
  window.regDayOpen = openModal;
  /* the campus banner's link: "Set your registration day", or "Change your registration day" once you have one */
  window.regDayLabel = function () { return !active() ? '' : (RG.day && RG.day.day >= today()) ? 'Change your registration day' : (RG.day ? '' : 'Set your registration day'); };
  window.regDayBoot = boot;
  window.regDayReset = reset;
  window.TCReg = { parseTime: parseTime, state: RG, rows: frRows, retry: retry, loadFriends: loadFriends, roundDays: roundDays, cardHtml: cardHtml, save: saveMine, timeText: timeText };
}());
</script>
'''
one("<!-- PLANS:BEGIN (apply-plans.mjs — edit plans/plans.js and plans/plans.css, not this) -->",
    BLOCK + "<!-- PLANS:BEGIN (apply-plans.mjs — edit plans/plans.js and plans/plans.css, not this) -->")

# ================================================================ 3. Schedule > Plans: the card tops the pane
one("""    var h = '<div class="pl3">' + notesHtml() + pillsHtml('cur');
    if (!pi.items.length) {""", """    var h = '<div class="pl3">' + (has('regSlotHtml') ? regSlotHtml('plans') : '') + notesHtml() + pillsHtml('cur');   /* website-registration-day (2026-10-14) */
    if (!pi.items.length) {""")

# ================================================================ 4. Home's right rail: under the date card
one("""  /* the supply verb — right above Highest rated (Tate's placement) */
  out+='<button class="hm-ratebtn""", """  /* Your registration day — from 14 days before Round 1 until its last day (website-registration-day, 2026-10-14) */
  try{ if(typeof regSlotHtml==='function')out+=regSlotHtml('rail'); }catch(e){}
  /* the supply verb — right above Highest rated (Tate's placement) */
  out+='<button class="hm-ratebtn""")

# ================================================================ 5. the campus banner links to it
one("""onclick="if(window.TCPlans)TCPlans.fromBanner();else show('sched')">Your game plan</button><button class="cb-x""",
    """onclick="if(window.TCPlans)TCPlans.fromBanner();else show('sched')">Your game plan</button>${(typeof regDayLabel==='function'&&regDayLabel())?'<button class="btn" style="flex:none" onclick="regDayOpen()">'+regDayLabel()+'</button>':''}<button class="cb-x""")

# ================================================================ 6. signing in loads it, signing out clears it
one("""      if(!uid)window._pdAsked=null;""", """      if(!uid)window._pdAsked=null;
      /* Your registration day and your friends' (website-registration-day, 2026-10-14) */
      try{ if(uid){ if(window._rgAsked!==uid){window._rgAsked=uid;setTimeout(function(){try{regDayBoot();}catch(_e){}},0);} } else if(window._rgAsked){window._rgAsked=null;regDayReset();} }catch(_e){}""")

f.write_text(s)
print('patched', f)
