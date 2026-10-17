#!/usr/bin/env python3
"""WEBSITE reg-timeline, 2026-10-16 (index.html only). Two approved mockups.

A. Home's registration card is now ONE timeline card for the term ("Spring 2027"): a vertical dot timeline of at most six rows
   (Your Round 1, Your Round 2, Classes begin, Last day to add, Last day to drop, Last day to withdraw). Only the NEXT row is loud
   (accent dot, bold, "in N days"); past rows are small grey checks; once classes begin Round 1/2 fold into "Registration done".
   Round 1 is the existing registration day (pencil -> the same sheet; registration_days, untouched). Round 2 is added inline
   (date + time, Save / Cancel). "Your game plan" is the one button until open enrollment ends (Jan 22). "All dates" lists the rest.
   The term's dates are one config object, TL_TERMS, keyed by term code ('2274'); a future term adds an entry.
   Round 2 is stored in public.registration_round2 (sql/professify-registration-round2-2026-10-16.sql). Until that table exists
   the website keeps Round 2 in localStorage and uploads it once when the table answers. The phone reads/writes nothing new.
   Removed: the old green "Your day..." line and the grey "Change your registration day" button; Home's second "rail" day card.
B. Friends tab: a "Registration days" strip above Messages (#frRegStrip): friends' faces grouped by day (and time, Round 1), your row
   highlighted, "N friends haven't set theirs". Same data and privacy as the Schedule card had (Round 1: friend_registration_days,
   day and time for friends who shared); Round 2 days come from friend_registration_round2 (day only, never a time). Between the rounds
   it shows Round 2 days; after Round 2 closes (Nov 17) it is gone. At phone width it is a horizontal row of day chips with faces.
   The friends' list is removed from the Schedule page's registration card; that card stays (it is where you set/change your Round 1
   day while planning) and says nothing about friends any more.
Usage: python3 reg-timeline-2026-10-16.py <repo>"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'index.html'
s = f.read_text()
if 'website-reg-timeline (2026-10-16)' in s:
    sys.exit('already patched')


def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:140])
    s = s.replace(old, new)


def span(start, end, new):
    """replace from `start` up to (not including) `end`, both exact and unique"""
    global s
    assert s.count(start) == 1, (s.count(start), start[:140])
    i = s.index(start)
    j = s.index(end, i + len(start))
    s = s[:i] + new + s[j:]


BLOCK_JS = r'''  /* ================================================================ website-reg-timeline (2026-10-16)
     One card on Home: your Round 1 and Round 2, then the term's add / drop / withdraw dates (hmRegCardHtml calls regTimelineHtml);
     the friends' days strip on the Friends tab (#frRegStrip). Round 1 is registration_days, as the phone has it (nothing here
     changes what the phone reads or writes). Round 2 is public.registration_round2 (sql/professify-registration-round2-2026-10-16.sql);
     until that table exists Round 2 stays on this device and goes up once when it does. */
  /* One entry per term code; a future term only adds an entry. Dates: registrar.calpoly.edu/spring-semester-planning-calendar */
  var TL_TERMS = {
    '2274': {
      name: 'Spring 2027', r1: ['2026-10-19', '2026-11-03'], r2: ['2026-11-04', '2026-11-17'], openEnds: '2027-01-22',
      r2a: ['2026-11-05', '2026-11-17'], r2skip: { '2026-11-11': 'Veterans Day' },     /* Round 2 opens Nov 4; the appointments are weekdays Nov 5-17, not Veterans Day */
      begin: '2027-01-25', add: '2027-01-29', drop: '2027-02-05', withdraw: '2027-04-23', last: '2027-05-14',
      more: [
        { t: 'Last day to add with a permission number', d: '2027-02-12' },
        { t: 'Last day to change CR/NC', d: '2027-03-26' },
        { t: 'Spring break', d: '2027-03-15', e: '2027-03-21' },
        { t: 'Last day to withdraw (reasons beyond your control) · last day of classes', d: '2027-05-14' },
        { t: 'Final exams', d: '2027-05-15', e: '2027-05-21', text: 'May 15, 17–21' }
      ],
      calendar: 'https://registrar.calpoly.edu/spring-semester-planning-calendar'
    }
  };
  RG.r2 = null; RG.r2gap = false; RG.r2loaded = false; RG.gen2 = 0; RG.fr2 = null; RG.fr2Busy = 0; RG.fr2N = 0; RG.r2err = ''; RG.stripAll = false;
  RG.tl = { edit: null, dirty: 0 };
  function tlT() { return TL_TERMS[code()] || null; }
  /* your own days (both rounds) are read until the term's last date, so the card can show them as done */
  function mineOn() {
    var T = tlT();
    if (!T || !user() || !client()) return false;
    try { if (String(mcTerm()) !== code()) return false; } catch (_) { return false; }
    return today() <= T.last;
  }
  /* the card: from 14 days before Round 1 until the term's last day of instruction */
  function tlOn() { var T = tlT(); if (!mineOn()) return false; var td = today(); return td >= isoAdd(T.r1[0], -14) && td <= T.last; }
  /* the card's dismiss key: per student, and a fresh one from a week before classes (Jan 18) so the drop / withdraw dates are not hidden all term */
  function tlKey() {
    var T = tlT(), u = user(); if (!T || !u) return '';
    return 'regtl_' + u.id + '_' + code() + (today() >= isoAdd(T.begin, -7) ? '_late' : '');
  }
  function shortDay(d) { return dayText(d).split(', ')[1]; }
  function rangeText(d, e) { var a = shortDay(d), b = shortDay(e); return a.slice(0, 3) === b.slice(0, 3) ? a + '–' + b.split(' ')[1] : a + '–' + b; }
  function time12(t) { if (!timeOk(t)) return ''; var h = +t.slice(0, 2), m = t.slice(3, 5); return (h % 12 || 12) + ':' + m + ' ' + (h >= 12 ? 'PM' : 'AM'); }
  function whenText(d, td) { var n = gap(td, d); return n === 0 ? 'today' : n === 1 ? 'tomorrow' : 'in ' + n + ' days'; }

  /* ---------------------------------------------------------------- Round 2: yours (this device first, then the account) */
  function key2() { var u = user(); return 'professify_regday2_' + (u ? u.id : '') + '_' + code(); }
  function read2() { var l = null; try { l = JSON.parse(localStorage.getItem(key2()) || 'null'); } catch (_) {} return l; }
  function keep2(v, pending, k) {
    k = k || key2();
    try {
      if (!pending) { if (v) localStorage.setItem(k, JSON.stringify({ day: v.day, time: v.time, shared: v.shared !== false })); else localStorage.removeItem(k); }
      else localStorage.setItem(k, JSON.stringify(v ? { day: v.day, time: v.time, shared: v.shared !== false, at: Date.now(), pending: true } : { gone: true, at: Date.now(), pending: true }));
    } catch (_) {}
  }
  async function push2(v) {
    if (RG.r2gap) return null;
    var c = client(), u = user(); if (!c || !u) return null;
    var gen = RG.gen2, k = key2(), term = code(), q;
    try {
      q = v ? await c.from('registration_round2').upsert({ user_id: u.id, term: term, day: v.day, at_time: v.time || null, shared: v.shared !== false, updated_at: new Date().toISOString() }, { onConflict: 'user_id,term' })
        : await c.from('registration_round2').delete().eq('user_id', u.id).eq('term', term);
    } catch (e) { q = { error: { message: String((e && e.message) || e) } }; }
    if (q.error) {
      if (writeGap(q.error) || schemaGap(q.error)) { RG.r2gap = true; return null; }     /* the table is not there yet: it stays on this device and goes up once it is */
      return 'Couldn’t save that to your account yet — it’s kept on this device.';
    }
    var current = RG.gen2 === gen && !!user() && user().id === u.id && (v ? RG.r2 === v : !RG.r2);
    if (current) { if (v) v.local = false; keep2(v, false, k); }
    return null;
  }
  async function loadMine2() {
    if (!mineOn()) { RG.r2 = null; return; }
    var loc = read2(); if (loc && !loc.gone && !dayOk(loc.day)) loc = null;
    RG.r2 = loc && !loc.gone ? { day: loc.day, time: time5(loc.time), shared: loc.shared !== false, local: true } : null;
    if (RG.r2gap) { repaint(); return; }
    var gen = RG.gen2, u = user(), r;
    try { r = await client().from('registration_round2').select('day,at_time,shared,updated_at').eq('user_id', u.id).eq('term', code()).maybeSingle(); } catch (e) { r = { error: { message: String(e) } }; }
    if (RG.gen2 !== gen || !user() || user().id !== u.id) return;
    RG.r2loaded = true;
    if (r.error) { if (schemaGap(r.error)) RG.r2gap = true; repaint(); return; }
    var row = r.data && dayOk(r.data.day) ? r.data : null;
    /* this device holds a change the account does not (kept while the table was missing, or while offline): it goes up once */
    if (loc && loc.pending && (!row || !row.updated_at || Date.parse(row.updated_at) < (+loc.at || 0))) {
      var e0 = await push2(loc.gone ? null : RG.r2); RG.r2err = e0 || ''; repaint(); return;
    }
    RG.r2 = row ? { day: row.day, time: time5(row.at_time), shared: row.shared !== false, local: false } : null;
    keep2(RG.r2, false); repaint();
  }
  async function saveMine2(v) {
    RG.gen2++;
    RG.r2 = v ? { day: v.day, time: time5(v.time), shared: v.shared !== false, local: true } : null;
    keep2(RG.r2, true);
    var e = await push2(RG.r2); RG.r2err = e || '';
    return e;
  }

  /* ---------------------------------------------------------------- the card */
  var CHK = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.2 6.3l2.4 2.4 5.2-5.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var PEN = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M11.2 2.3l2.5 2.5-8 8L2.6 13.4l.6-3.1 8-8z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  /* the rows, in order: [{ k, title, date, time, mine, round, empty, sub }] — at most six */
  function tlRows(T, td) {
    var rows = [];
    function mineRow(n, round, v, span, canEdit) {
      var title = 'Your Round ' + n;
      if (v) rows.push({ k: 'r' + n, title: title, date: v.day, time: v.time, mine: true, edit: canEdit, local: v.local });
      /* an empty row you can fill in is the lit one: Round 1 from the day the card appears, Round 2 once it is open (Nov 4) */
      else if (td <= span[1]) rows.push({ k: 'r' + n, title: title, date: '', empty: true, edit: canEdit, lit: !!canEdit && (n === 1 || td >= span[0]), sub: td < span[0] ? 'Opens ' + shortDay(span[0]) : 'Open now · ends ' + shortDay(span[1]) });
    }
    if (td < T.begin) {
      mineRow(1, 1, RG.day, T.r1, active());
      mineRow(2, 2, RG.r2, T.r2, td <= T.r2[1]);
    }
    rows.push({ k: 'begin', title: td >= T.begin ? 'Classes began' : 'Classes begin', date: T.begin });
    rows.push({ k: 'add', title: 'Last day to add', date: T.add, hint: 'After this you need a permission number' });
    rows.push({ k: 'drop', title: 'Last day to drop', date: T.drop, note: 'Until 11:59 PM' });
    rows.push({ k: 'withdraw', title: 'Last day to withdraw', date: T.withdraw, note: 'For a serious and compelling reason · 5 PM' });
    if (td > T.withdraw) rows.push({ k: 'last', title: 'Last day of classes', date: T.last });
    return rows;
  }
  function tlEditHtml(T, td) {
    var e = RG.tl.edit, lo = T.r2a[0], hi = T.r2a[1];
    return '<div class="tl-edit"><p class="tl-lab">Find it in your Student Center. Round 2 runs ' + esc(rangeText(lo, hi)) + ', weekdays.</p>'
      + '<div class="tl-fields"><input type="date" class="tl-in" data-tl-f="day" data-tl-key="d2" min="' + lo + '" max="' + hi + '" value="' + esc(e.day) + '" aria-label="Round 2 date"' + (e.err ? ' aria-invalid="true"' : '') + '>'
      + '<input type="time" class="tl-in tl-tm" data-tl-f="time" data-tl-key="t2" value="' + esc(e.time) + '" aria-label="Round 2 time (optional)"></div>'
      + '<div class="rg-row tl-share"><span class="rg-rl" id="tlShareL">Friends can see your day<em>' + (e.shared ? 'Friends can see this day, not the time' : 'Hidden from your friends') + '</em></span>'
      + '<button type="button" class="rg-tog" role="switch" aria-checked="' + !!e.shared + '" aria-labelledby="tlShareL" data-tl-act="share2" data-tl-key="sh2"></button></div>'
      + (e.err ? '<div class="tl-err" role="alert">' + esc(e.err) + '</div>' : '')
      + '<div class="tl-acts"><button type="button" class="tl-save" data-tl-act="save2" data-tl-key="s2"' + (e.busy ? ' disabled' : '') + '>' + (e.busy ? 'Saving…' : 'Save') + '</button>'
      + '<button type="button" class="tl-cancel" data-tl-act="cancel2" data-tl-key="c2">Cancel</button>'
      + (RG.r2 ? '<button type="button" class="tl-cancel tl-rm" data-tl-act="clear2" data-tl-key="x2">Remove</button>' : '') + '</div></div>';
  }
  function regTimelineHtml(where, key) {
    var T = tlT(); if (!T || !tlOn()) return '';
    var td = today(), rows = tlRows(T, td), began = td >= T.begin, i, next = -1;
    for (i = 0; i < rows.length; i++) if (rows[i].lit) { next = i; break; }     /* the empty row you can fill in beats the next date */
    if (next < 0) for (i = 0; i < rows.length; i++) if (rows[i].date && rows[i].date >= td) { next = i; break; }
    var h = '<section id="' + (where === 'top' ? 'hmRegCardN' : 'hmRegCard') + '" class="hm-card hm-regcard tl-card" aria-label="' + esc(T.name) + ' registration and key dates">'
      + '<button type="button" class="cb-x hm-regx" title="Dismiss" aria-label="Dismiss" onclick="dismissRegCard(\'' + esc(key) + '\')">&times;</button>'
      + '<div class="tl-hd"><b><span aria-hidden="true">📅</span> ' + esc(T.name) + '</b><span>' + (began ? 'Key dates' : 'Registration &amp; key dates') + '</span></div>';
    if (began) {
      var parts = []; if (RG.day) parts.push('Round 1 ' + shortDay(RG.day.day)); if (RG.r2) parts.push('Round 2 ' + shortDay(RG.r2.day));
      h += '<div class="tl-fold"><span class="tl-tick">' + CHK + '</span><div><div class="tl-t">Registration done</div>' + (parts.length ? '<div class="tl-s">' + esc(parts.join(' · ')) + '</div>' : '') + '</div></div>';
    }
    h += '<ol class="tl-ol">';
    rows.forEach(function (r, n) {
      var isNext = n === next, done = !!r.date && r.date < td, cls = 'tl-li' + (isNext ? ' tl-next' : done ? ' tl-done' : '') + (r.empty ? ' tl-empty' : '');
      var editing = r.k === 'r2' && RG.tl.edit, sub = '', right = '';
      if (editing) cls += ' tl-editing';
      if (r.empty) {
        sub = r.sub;
        right = r.edit ? '<button type="button" class="tl-add" data-tl-act="add' + r.k.slice(1) + '" data-tl-key="add' + r.k.slice(1) + '" aria-label="Add your Round ' + r.k.slice(1) + ' day">+ Add</button>' : '';
      } else {
        var when = isNext ? whenText(r.date, td) : '';
        if (r.mine) {
          var tt = time12(r.time);
          if (isNext) sub = dayText(r.date) + (tt ? ' · ' + tt : '');
          else if (!done && tt) sub = tt;
          var note = r.k === 'r1' ? (RG.gap ? 'kept on this device' : r.local ? 'not saved to your account yet' : '') : (r.local && RG.r2err ? 'not saved to your account yet' : '');
          if (note) sub += (sub ? ' · ' : '') + note;
        } else if (r.note) sub = r.note;
        else if (isNext && r.hint) sub = r.hint;
        right = (isNext ? esc(when) : esc(dayText(r.date)));
        if (r.mine && r.edit) right += '<button type="button" class="tl-pen" data-tl-act="pen' + r.k.slice(1) + '" data-tl-key="pen' + r.k.slice(1) + '" aria-label="Edit your Round ' + r.k.slice(1) + '">' + PEN + '</button>';
      }
      h += '<li class="' + cls + '" data-tl-row="' + r.k + '"><span class="tl-dot">' + (done && !editing ? CHK : '') + '</span>'
        + '<div class="tl-mid"><div class="tl-t">' + esc(r.title) + '</div>' + (sub && !editing ? '<div class="tl-s">' + esc(sub) + '</div>' : '') + '</div>'
        + (editing ? '<div class="tl-r"></div>' : '<div class="tl-r">' + right + '</div>') + (editing ? tlEditHtml(T, td) : '') + '</li>';
    });
    h += '</ol>';
    var plan = td <= T.openEnds;
    h += '<div class="tl-ft">' + (plan ? '<button type="button" class="tl-go" data-tl-key="plan" onclick="if(window.TCPlans)TCPlans.fromBanner();else show(\'sched\')">Your game plan <span aria-hidden="true">→</span></button>' : '<span></span>')
      + '<button type="button" class="tl-all" data-tl-act="all" data-tl-key="all">All dates</button></div></section>';
    return h;
  }
  /* drawing the card again must not drop the keyboard, nor what is being typed in Round 2's date and time */
  function tlPaint() {
    var a = document.activeElement, card = a && a.closest ? a.closest('.hm-regcard') : null;
    if (card && RG.tl.edit && a.matches && a.matches('.tl-in')) { RG.tl.dirty = 1; return; }
    var k = card && a.getAttribute ? a.getAttribute('data-tl-key') : null, top = card && card.id === 'hmRegCardN';
    try { if (typeof hmRegCardPaint === 'function') hmRegCardPaint(); } catch (_) {}
    if (k) tlFocus(k, top);
  }
  function tlFocus(k, top) {
    try {
      var all = document.querySelectorAll('.hm-regcard [data-tl-key="' + k + '"]'), pick = null;
      for (var i = 0; i < all.length; i++) { if (all[i].offsetParent !== null && (top == null || (all[i].closest('.hm-regcard').id === 'hmRegCardN') === !!top)) { pick = all[i]; break; } }
      if (!pick) for (i = 0; i < all.length; i++) if (all[i].offsetParent !== null) { pick = all[i]; break; }
      if (pick) pick.focus({ preventScroll: true });
    } catch (_) {}
  }
  /* the first weekday of Round 2 that is not behind us: what the date field starts on */
  function r2Default(T, td) {
    var d = td > T.r2a[0] ? td : T.r2a[0];
    for (var i = 0; i < 9 && d <= T.r2a[1]; i++, d = isoAdd(d, 1)) { var w = new Date(d + 'T12:00:00Z').getUTCDay(); if (w > 0 && w < 6 && !T.r2skip[d]) return d; }
    return '';
  }
  function tlEdit(on) {
    if (on) { var v = RG.r2; RG.tl.edit = { day: v ? v.day : r2Default(tlT(), today()), time: v ? v.time : '', err: '', busy: 0,
      shared: (v ? v.shared !== false : true) && (RG.day ? RG.day.shared !== false : true) }; }     /* one setting for both rounds: off if either is off */
    else RG.tl.edit = null;
    RG.tl.dirty = 0;
    try { hmRegCardPaint(); } catch (_) {}
    setTimeout(function () { tlFocus(on ? 'd2' : (RG.r2 ? 'pen2' : 'add2')); }, 0);
  }
  async function tlSave2() {
    var e = RG.tl.edit, T = tlT(); if (!e || e.busy || !T) return;
    var td = today(), d = e.day, wd = dayOk(d) ? new Date(d + 'T12:00:00Z').getUTCDay() : -1;
    if (!dayOk(d)) e.err = 'Pick your day first.';
    else if (d < T.r2a[0] || d > T.r2a[1]) e.err = 'Round 2 runs ' + rangeText(T.r2a[0], T.r2a[1]) + '.';
    else if (wd === 0 || wd === 6) e.err = 'Round 2 is on weekdays.';
    else if (T.r2skip[d]) e.err = shortDay(d) + ' is ' + T.r2skip[d] + ' — pick another weekday.';
    else if (d < td) e.err = 'That day has passed.';
    else if (e.time && !timeOk(e.time)) e.err = 'That time doesn’t look right.';
    else e.err = '';
    if (e.err) { try { hmRegCardPaint(); } catch (_) {} setTimeout(function () { tlFocus('d2'); }, 0); return; }
    e.busy = 1; try { hmRegCardPaint(); } catch (_) {}
    var msg, sh = e.shared !== false;
    try {
      msg = await saveMine2({ day: d, time: e.time || '', shared: sh });
      /* "Friends can see your day" is one setting for both rounds: it follows into Round 1's row only when that row is on the other side of it */
      if (RG.day && RG.day.shared !== sh) { var m1 = await saveMine({ day: RG.day.day, time: RG.day.time, shared: sh }); msg = msg || m1; }
    } catch (x) { msg = 'Couldn’t save that to your account yet — it’s kept on this device.'; }
    RG.tl.edit = null; RG.tl.dirty = 0;
    toast(msg || (RG.r2gap ? 'Saved on this device' : 'Your Round 2 day is saved'));
    repaint(); loadFriends2(true); setTimeout(function () { tlFocus('pen2'); }, 0);
  }
  async function tlClear2() {
    var e = RG.tl.edit; if (e && e.busy) return;
    var msg; try { msg = await saveMine2(null); } catch (x) { msg = 'Couldn’t remove it — try again.'; }
    RG.tl.edit = null; RG.tl.dirty = 0;
    toast(msg || 'Your Round 2 day is cleared'); repaint(); setTimeout(function () { tlFocus('add2'); }, 0);
  }
  /* "All dates": the dates that are not on the card */
  function allHtml(T, td) {
    var items = T.more.filter(function (x) { return (x.e || x.d) >= td; });
    return '<button type="button" class="mclose" data-tl-act="allx" aria-label="Close">&times;</button><div class="rg-m">'
      + '<h2 class="rate-h" id="tlAllT">' + esc(T.name) + ' dates</h2><p class="rg-hint">The rest of the term, from the registrar.</p>'
      + (items.length ? '<ul class="tl-dates">' + items.map(function (x) {
        return '<li><span>' + esc(x.t) + '</span><b>' + esc(x.text || (x.e ? rangeText(x.d, x.e) : dayText(x.d))) + '</b></li>';
      }).join('') + '</ul>' : '<p class="rg-hint">That is everything left this term.</p>')
      + '<p class="rg-hint tl-src"><a href="' + esc(T.calendar) + '" target="_blank" rel="noopener noreferrer">Registrar’s calendar</a></p></div>';
  }
  function allOpen() {
    var T = tlT(); if (!T) return;
    var b = document.getElementById('tlBack');
    if (!b) {
      b = document.createElement('div'); b.id = 'tlBack'; b.className = 'mback';
      b.innerHTML = '<div class="modal rg-modal" id="tlModal"></div>';
      b.setAttribute('aria-labelledby', 'tlAllT');
      b.addEventListener('click', function (e) { if (e.target === b) allClose(); });
      document.body.appendChild(b);
    }
    document.getElementById('tlModal').innerHTML = allHtml(T, today());
    b.classList.add('open'); document.body.style.overflow = 'hidden';
    try { openModalA11y('tlBack'); } catch (_) {}
  }
  function allClose() {
    var b = document.getElementById('tlBack'); if (b) b.classList.remove('open');
    document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : '';
    try { closeModalA11y(); } catch (_) {}
    setTimeout(function () { tlFocus('all'); }, 0);
  }
  document.addEventListener('click', function (e) {
    var t = e.target && e.target.closest ? e.target.closest('[data-tl-act]') : null; if (!t) return;
    var a = t.getAttribute('data-tl-act');
    if (a === 'pen1' || a === 'add1') openModal('timeline');
    else if (a === 'pen2' || a === 'add2') tlEdit(true);
    else if (a === 'cancel2') tlEdit(false);
    else if (a === 'save2') tlSave2();
    else if (a === 'clear2') tlClear2();
    else if (a === 'share2') { if (RG.tl.edit) { RG.tl.edit.shared = !RG.tl.edit.shared; try { hmRegCardPaint(); } catch (_) {} setTimeout(function () { tlFocus('sh2'); }, 0); } }
    else if (a === 'all') allOpen();
    else if (a === 'allx') allClose();
    else if (a === 'more') { RG.stripAll = !RG.stripAll; stripPaint(); }
  });
  document.addEventListener('input', function (e) {
    var t = e.target; if (!t || !t.getAttribute || !RG.tl.edit) return;
    var f = t.getAttribute('data-tl-f'); if (f === 'day' || f === 'time') { RG.tl.edit[f] = String(t.value || '').slice(0, 10); RG.tl.edit.err = ''; }
  }, true);
  document.addEventListener('change', function (e) { var t = e.target; if (t && t.getAttribute && RG.tl.edit && t.getAttribute('data-tl-f')) { RG.tl.edit[t.getAttribute('data-tl-f')] = String(t.value || '').slice(0, 10); } }, true);
  document.addEventListener('keydown', function (e) {
    var t = e.target;
    if (e.key === 'Escape' || e.key === 'Esc') {
      var b = document.getElementById('tlBack');
      if (b && b.classList.contains('open')) { e.preventDefault(); e.stopPropagation(); allClose(); return; }
      if (RG.tl.edit && t && t.closest && t.closest('.tl-edit')) { e.preventDefault(); tlEdit(false); }
    } else if (e.key === 'Enter' && RG.tl.edit && t && t.matches && t.matches('.tl-in')) { e.preventDefault(); tlSave2(); }
  }, true);

  /* ---------------------------------------------------------------- friends' Round 2 days (day only: never a time) */
  async function loadFriends2(force) {
    if (!mineOn() || RG.fr2Busy || stripPhase() !== 2) return;
    var was = RG.fr2;
    if (!force && was && (was.off || Date.now() - was.at < (was.err ? REG_ERR_TTL : REG_TTL))) return;
    RG.fr2Busy = 1;
    var u = user(), r, timer;
    try {
      r = await Promise.race([client().rpc('friend_registration_round2', { p_term: code() }), new Promise(function (_, no) { timer = setTimeout(function () { no(new Error('timeout')); }, 10000); })]);
    } catch (e) { r = { error: { message: String((e && e.message) || e) } }; }
    clearTimeout(timer);
    RG.fr2Busy = 0;
    if (!user() || user().id !== (u && u.id)) return;
    if (r.error && (typeof rpcMissing === 'function' ? rpcMissing(r.error) : schemaGap(r.error))) RG.fr2 = { rows: [], at: Date.now(), off: true };
    else if (r.error) {
      if (was && was.rows) was.at = Date.now() - REG_TTL + REG_ERR_TTL; else RG.fr2 = { err: 1, at: Date.now() };
      if (++RG.fr2N <= 6) setTimeout(function () { loadFriends2(); }, REG_ERR_TTL + 250);
    } else {
      var seen = {}; RG.fr2N = 0;
      RG.fr2 = { rows: (Array.isArray(r.data) ? r.data : []).filter(function (x) { return x && x.user_id && dayOk(x.day) && !seen[x.user_id] && (seen[x.user_id] = 1); })
        .map(function (x) { return { id: x.user_id, day: x.day, time: '' }; }), at: Date.now() };
    }
    repaint();
  }
  function frRows2() {
    var F = RG.fr2; if (!F || !F.rows) return [];
    return F.rows.filter(function (x) { return friendOf(x.id) && !blocked(x.id); }).sort(function (a, b) {
      return a.day.localeCompare(b.day) || String(friendOf(a.id).name || '').localeCompare(String(friendOf(b.id).name || ''));
    });
  }

  /* ---------------------------------------------------------------- the Friends tab: "Registration days" above Messages */
  /* 1 = Round 1 (friends' Round 1 days), 2 = between the rounds and until Round 2 closes (Round 2 days), 0 = nothing */
  function stripPhase() {
    var T = tlT(); if (!T || !user() || !client()) return 0;
    try { if (String(mcTerm()) !== code()) return 0; } catch (_) { return 0; }
    var td = today();
    return td <= T.r1[1] ? 1 : td <= T.r2[1] ? 2 : 0;
  }
  function firstName(f) { return String((f && f.name) || 'Classmate').split(/\s+/)[0]; }
  function stripHtml() {
    var ph = stripPhase(); if (!ph) return '';
    var T = tlT(), td = today(), F = ph === 1 ? RG.fr : RG.fr2;
    if (ph === 1 ? !RG.frBusy : !RG.fr2Busy) setTimeout(function () { ph === 1 ? loadFriends() : loadFriends2(); }, 0);
    if (!F || !F.rows || F.off) return '';
    var all = ph === 1 ? frRows() : frRows2(), mine = ph === 1 ? RG.day : RG.r2;
    if (mine && mine.day < td) mine = null;
    var up = all.filter(function (x) { return x.day >= td; }), nf = 0;
    try { friendsList.forEach(function (f) { if (!blocked(f.id)) nf++; }); } catch (_) {}
    if (!nf || (!up.length && !mine)) return '';
    var groups = [], idx = {};
    function slot(day, time) { var k = day + '|' + (ph === 1 ? time || '' : ''); if (!idx[k]) { idx[k] = { day: day, time: ph === 1 ? time || '' : '', ids: [], me: false }; groups.push(idx[k]); } return idx[k]; }
    up.forEach(function (x) { slot(x.day, x.time).ids.push(x.id); });
    if (mine) slot(mine.day, mine.time).me = true;
    groups.sort(function (a, b) { return a.day.localeCompare(b.day) || (a.time || '99').localeCompare(b.time || '99'); });
    var meF = { name: (typeof myProfile !== 'undefined' && myProfile && myProfile.display_name) || 'You', avatar_url: (typeof myProfile !== 'undefined' && myProfile && myProfile.avatar_url) || '', id: user().id };
    var CAP = 5, lis = groups.map(function (g, n) {
      var fr = g.ids.map(friendOf).filter(Boolean), faces = [];
      if (g.me) faces.push('<span class="rs-fb" role="img" aria-label="You">' + face(meF) + '</span>');
      fr.slice(0, g.me ? 2 : 3).forEach(function (f) { faces.push('<button type="button" class="rs-fb" data-rg-act="friend" data-id="' + esc(f.id) + '" aria-label="' + esc(f.name || 'Classmate') + '">' + face(f) + '</button>'); });
      var hid = fr.length - (g.me ? 2 : 3);
      if (hid > 0) faces.push('<span class="rs-plus" aria-hidden="true">+' + hid + '</span>');
      var others = fr.map(function (f) { return fr.length === 1 && !g.me ? (f.name || 'Classmate') : firstName(f); });
      var d = g.day === td ? 'Today' : dayText(g.day).replace(',', ''), t = ph === 1 ? timeText(g.time) : '';
      var rel = g.me ? 'your day' : mine ? (function () { var n = gap(mine.day, g.day); return !n ? 'same day as you' : n < 0 ? plural(-n, 'day') + ' before you' : plural(n, 'day') + ' after you'; })() : '';
      return '<li class="rs-row' + (g.me ? ' rs-me' : '') + (n >= CAP ? ' rs-x' : '') + '" data-rs-day="' + g.day + '"><div class="rs-d"><b>' + esc(d) + '</b>' + (t ? '<span>' + esc(t) + '</span>' : '') + '</div>'
        + '<div class="rs-f">' + faces.join('') + '</div><div class="rs-n">' + esc((g.me ? 'You' + (others.length ? ' · ' : '') : '') + others.join(', ')) + '</div><div class="rs-rel">' + esc(rel) + '</div></li>';
    });
    var shared = {}; all.forEach(function (x) { shared[x.id] = 1; });
    var missing = 0; try { friendsList.forEach(function (f) { if (!shared[f.id] && !blocked(f.id)) missing++; }); } catch (_) {}
    var more = groups.length - CAP, round = ph === 1 ? 'Round 1 · ' + rangeText(T.r1[0], T.r1[1]) : 'Round 2 · ' + rangeText(T.r2a[0], T.r2a[1]);
    return '<div class="fr-sec rs-sec" id="frRegSec"><div class="fr-sech"><span class="fr-seck">Registration days</span><span class="rs-rnd">' + esc(round) + '</span></div>'
      + '<div class="rs-card' + (RG.stripAll ? ' rs-open' : '') + '"><ul class="rs-l">' + lis.join('') + '</ul>'
      + ((missing || more > 0) ? '<div class="rs-ft"><span>' + (missing ? plural(missing, 'friend') + ' ' + (missing === 1 ? 'hasn’t' : 'haven’t') + ' set theirs' : '') + '</span>'
        + (more > 0 ? '<button type="button" class="rs-more" data-tl-act="more" aria-expanded="' + !!RG.stripAll + '">' + (RG.stripAll ? 'Show fewer' : '+' + more + ' more day' + (more === 1 ? '' : 's')) + '</button>' : '') + '</div>' : '')
      + '</div></div>';
  }
  function stripPaint() {
    var el = document.getElementById('frRegStrip'); if (!el) return;
    var a = document.activeElement, k = a && el.contains(a) ? { act: a.getAttribute('data-rg-act') || a.getAttribute('data-tl-act'), id: a.getAttribute('data-id') } : null;
    var h = ''; try { h = stripHtml(); } catch (_) {}
    if (el.getAttribute('data-h') === h) return;
    el.setAttribute('data-h', h); el.innerHTML = h;
    if (k) { try { var n = el.querySelectorAll('button'); for (var i = 0; i < n.length; i++) if ((n[i].getAttribute('data-rg-act') || n[i].getAttribute('data-tl-act')) === k.act && (n[i].getAttribute('data-id') || null) === (k.id || null)) { n[i].focus({ preventScroll: true }); break; } } catch (_) {} }
  }
  window.addEventListener('online', function () { try { var l = read2(); if (l && l.pending && !RG.r2gap && mineOn()) loadMine2(); } catch (_) {} });
  document.addEventListener('visibilitychange', function () { try { if (document.visibilityState !== 'visible') return; var l = read2(); if (l && l.pending && !RG.r2gap && mineOn()) loadMine2(); } catch (_) {} });'''
CARD_CSS = r'''/* website-reg-timeline (2026-10-16): Home's one registration card — a vertical timeline. Only the NEXT row is loud; past rows are small
   grey checks. App tokens only (accent = the school's / theme's), so light and dark follow the theme. */
.hm-regcard{display:block;padding:16px 18px 14px}
.hm-regcard .hm-regx{position:absolute;top:8px;right:10px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;padding:0;border-radius:8px;color:var(--faint);font-size:20px;line-height:1;background:none;border:0;cursor:pointer}
@media (hover:hover){.hm-regcard .hm-regx:hover{color:var(--text);background:rgba(var(--fg-rgb),.07)}}
.hm-regcard .hm-regx:focus-visible,.tl-card button:focus-visible,.tl-in:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tl-hd{display:flex;align-items:baseline;flex-wrap:wrap;gap:2px 8px;padding-right:28px;margin-bottom:12px}
.tl-hd b{font-size:var(--t-name);font-weight:800;color:var(--text)}
.tl-hd span{font-size:var(--t-label);color:var(--faint);font-weight:700}
.tl-hd b span{font-size:14px;color:inherit}
.tl-ol{list-style:none;margin:0;padding:0}
.tl-li{position:relative;display:grid;grid-template-columns:16px minmax(0,1fr) auto;column-gap:12px;align-items:start;padding:7px 0 9px}
.tl-li::before{content:"";position:absolute;left:7px;top:22px;bottom:-6px;width:2px;background:var(--line-soft);border-radius:2px}
.tl-li:last-child::before{display:none}
.tl-dot{width:16px;height:16px;border-radius:50%;border:2px solid rgba(var(--fg-rgb),.28);background:var(--panel);margin-top:1px;position:relative;z-index:1;display:flex;align-items:center;justify-content:center;color:var(--faint)}
.tl-t{font-size:var(--t-body);font-weight:700;color:var(--muted);line-height:1.3}
.tl-s{font-size:var(--t-label);color:var(--faint);line-height:1.35;margin-top:2px;font-weight:600}
.tl-r{font-size:var(--t-body);font-weight:700;color:var(--muted);text-align:right;white-space:nowrap;line-height:1.3;display:flex;align-items:center;gap:6px;justify-content:flex-end}
.tl-pen{width:28px;height:28px;margin:-6px -7px -6px 0;display:inline-flex;align-items:center;justify-content:center;border:0;background:none;color:var(--faint);border-radius:8px;cursor:pointer;padding:0}
.tl-pen svg{width:13px;height:13px}
.tl-pen::after,.tl-add::after{content:'';position:absolute;inset:-8px -6px}
.tl-pen,.tl-add{position:relative}
@media (hover:hover){.tl-pen:hover{color:var(--text);background:rgba(var(--fg-rgb),.07)}}
.tl-add{font:inherit;font-size:var(--t-body);font-weight:800;color:var(--accent);background:none;border:0;padding:4px 0 4px 8px;margin:-4px 0;cursor:pointer;min-height:28px}
.tl-done .tl-dot{border-color:transparent;background:rgba(var(--fg-rgb),.12);color:var(--faint)}
.tl-done .tl-dot svg{width:9px;height:9px}
.tl-done .tl-t,.tl-done .tl-r{color:var(--faint);font-weight:600}
.tl-empty .tl-dot,.tl-editing .tl-dot{border-style:dashed}
.tl-empty .tl-t{color:var(--text-2)}
.tl-next{padding:10px 0 12px}
.tl-next .tl-dot{border-color:var(--accent);background:var(--accent);box-shadow:0 0 0 4px rgba(var(--accent-rgb),.16)}
.tl-next .tl-dot::after{content:"";width:4px;height:4px;border-radius:50%;background:var(--accent-ink)}
.tl-next .tl-t{font-size:15px;font-weight:800;color:var(--text);line-height:1.25}
.tl-next .tl-s{font-size:12px;color:var(--text-2);margin-top:3px;font-weight:600}
.tl-next .tl-r{font-size:15px;font-weight:800;color:var(--accent)}
.tl-next .tl-pen{color:var(--text-2)}
.tl-next.tl-empty .tl-dot{background:var(--panel)}
.tl-next.tl-empty .tl-dot::after{background:var(--accent)}
.tl-next .tl-add{font-size:15px}
.tl-editing .tl-t{color:var(--text)}
.tl-share{margin-top:10px;min-height:48px;padding:4px 12px}
.tl-fold{display:flex;align-items:flex-start;gap:12px;padding:2px 0 10px}
.tl-fold>div{min-width:0}
.tl-fold .tl-t{color:var(--faint);font-weight:600}
.tl-tick{width:16px;height:16px;margin-top:1px;border-radius:50%;background:rgba(var(--fg-rgb),.12);display:flex;align-items:center;justify-content:center;color:var(--faint);flex:none}
.tl-tick svg{width:9px;height:9px}
.tl-edit{grid-column:2 / 4;margin-top:8px}
.tl-lab{margin:0 0 8px;font-size:var(--t-label);color:var(--faint);font-weight:600;line-height:1.4}
.tl-fields{display:flex;gap:8px}
.tl-in{flex:1 1 0;min-width:0;height:40px;background:var(--panel-2);border:1px solid var(--line);border-radius:12px;color:var(--text);font:inherit;font-size:13px;font-weight:700;padding:0 8px;color-scheme:light dark}
.tl-in.tl-tm{flex:0 0 116px}
.tl-in[aria-invalid="true"]{border-color:var(--low)}
.tl-err{margin-top:8px;font-size:var(--t-body);font-weight:600;color:var(--low)}
.tl-acts{display:flex;align-items:center;gap:14px;margin-top:10px}
.tl-save{font:inherit;font-size:var(--t-body);font-weight:800;color:var(--accent-ink);background:var(--accent);border:0;border-radius:12px;min-height:36px;padding:0 18px;cursor:pointer}
.tl-save:disabled{opacity:.6;cursor:default}
.tl-cancel{font:inherit;font-size:var(--t-body);font-weight:700;color:var(--muted);background:none;border:0;cursor:pointer;padding:6px 0;min-height:36px}
.tl-rm{margin-left:auto}
.tl-ft{display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:1px solid var(--line-soft);margin-top:6px;padding-top:12px}
.tl-go{display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:var(--t-body);font-weight:800;color:var(--accent-ink);background:var(--accent);border:0;border-radius:14px;padding:0 14px;min-height:40px;cursor:pointer;box-shadow:0 8px 20px rgba(var(--accent-rgb),.22)}
.tl-all{font:inherit;font-size:var(--t-label);font-weight:700;color:var(--muted);background:none;border:0;cursor:pointer;padding:10px 0 10px 10px;min-height:40px}
@media (hover:hover){.tl-all:hover{color:var(--text)}}
#hmRegTop{display:none}
@media (max-width:1139px){
  #hmRegTop{display:block;margin:0 0 14px}
  #hmRailR #hmRegCard{display:none}
}
#tlModal .mclose{position:absolute;top:14px;right:14px;left:auto;z-index:3}
ul.tl-dates{list-style:none;margin:6px 0 8px;padding:0;display:flex;flex-direction:column}
ul.tl-dates li{display:flex;justify-content:space-between;align-items:baseline;gap:14px;padding:10px 0;border-top:1px solid var(--line-soft);font-size:14px;color:var(--text-2);font-weight:600}
ul.tl-dates li:first-child{border-top:0}
ul.tl-dates li b{flex:none;color:var(--text);font-weight:800;text-align:right}
.tl-src a{color:var(--blue-ink,var(--accent))}
/* the Friends tab: "Registration days" above Messages (website-reg-timeline) */
#frRegStrip:empty{display:none}
.rs-rnd{font-size:var(--t-label);color:var(--faint);font-weight:700}
.rs-card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:6px}
.rs-l{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
.rs-row{display:grid;grid-template-columns:84px auto minmax(0,1fr) auto;align-items:center;gap:10px;padding:7px 10px;border:1px solid transparent;border-radius:11px}
.rs-d{display:flex;flex-direction:column;line-height:1.25}
.rs-d b{font-size:var(--t-body);font-weight:800;color:var(--text);white-space:nowrap}
.rs-d span{font-size:var(--t-label);color:var(--faint);font-weight:600}
.rs-f{display:flex;align-items:center}
.rs-fb{position:relative;flex:none;display:block;width:28px;height:28px;margin-right:-6px;padding:0;border:2px solid var(--panel);border-radius:50%;background:none;cursor:pointer;font:inherit}
button.rs-fb::after{content:'';position:absolute;inset:-8px -3px}
span.rs-fb{cursor:default}
.rs-fb .rg-face{width:24px;height:24px;font-size:10px}
.rs-f .rs-fb:last-child{margin-right:0}
.rs-plus{margin-left:10px;font-size:var(--t-label);font-weight:700;color:var(--faint)}
.rs-n{min-width:0;font-size:var(--t-body);font-weight:600;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rs-rel{font-size:var(--t-label);font-weight:600;color:var(--faint);white-space:nowrap}
.rs-me{border-color:rgba(var(--accent-rgb),.5);background:rgba(var(--accent-rgb),.10)}
.rs-me .rs-d b{color:var(--accent)}
.rs-me .rs-rel{color:var(--accent);font-weight:700}
.rs-ft{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:4px 4px 0;padding:8px 6px 4px;border-top:1px solid var(--line-soft);font-size:var(--t-body);font-weight:600;color:var(--muted)}
.rs-more{font:inherit;font-size:var(--t-body);font-weight:700;color:var(--accent);background:none;border:0;cursor:pointer;padding:6px 0 6px 10px;min-height:32px}
.rs-card:not(.rs-open) .rs-x{display:none}
.rs-card button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:760px){
  .rs-l{flex-direction:row;gap:8px;overflow-x:auto;padding:2px 2px 6px;scrollbar-width:none}
  .rs-l::-webkit-scrollbar{display:none}
  .rs-row,.rs-card:not(.rs-open) .rs-x{display:flex!important;flex:none;flex-direction:column;align-items:flex-start;gap:7px;padding:8px 12px;border:1px solid var(--line);border-radius:14px;background:var(--panel-2)}
  .rs-row.rs-me{border-color:rgba(var(--accent-rgb),.55);background:rgba(var(--accent-rgb),.12)}
  .rs-d{flex-direction:row;align-items:baseline;gap:6px}
  .rs-n,.rs-rel,.rs-more{display:none}
  .rs-ft{border-top:0;margin-top:0;padding-top:2px}
}
/* a sheet is open (All dates, a day picker, any .mback): the Ask Me! bird stays out of its way */
body:has(.mback.open) .hawk-fab{visibility:hidden}'''

# ---------------------------------------------------------------------------------------------- the Friends tab: the strip's place
one('''        <div class="fr-sec" id="frMsgSec" style="display:none">''',
    '''        <!-- website-reg-timeline (2026-10-16): friends' registration days, above Messages; empty (and display:none) unless it has something to say -->
        <div id="frRegStrip"></div>
        <div class="fr-sec" id="frMsgSec" style="display:none">''')
one('''try{ frRenderGroups(); }catch(e){}''',
    '''try{ frRenderGroups(); }catch(e){}
  try{ if(typeof regStripPaint==='function')regStripPaint(); }catch(e){}   /* website-reg-timeline (2026-10-16) */''')

# ---------------------------------------------------------------------------------------------- Home: the one timeline card
span('''/* website-sync (2026-10-15): the registration banner as a compact card on Home's right rail''', '''function hmRegTopPaint(){''',
'''/* website-reg-timeline (2026-10-16): Home's one registration card is the term's timeline (regTimelineHtml, in the regday module: Your Round 1,
   Your Round 2, classes begin, last day to add / drop / withdraw). It shows from 14 days before Round 1 until the term's last day of instruction;
   x dismisses it (key regtl_<user id>_<term code>; a fresh key from Jan 18, a week before classes, so it comes back for the drop / withdraw dates). Below 1140px the rail is hidden, so the same card is drawn at the top of Home's main column
   (#hmRegTop) instead. It replaces the website-sync (2026-10-15) "Round 1 registration opens" card and the rail's own day card. */
function hmRegCardKey(){
  try{
    if(typeof sbUser==='undefined'||!sbUser)return null;
    if(typeof regTimelineOn!=='function'||!regTimelineOn())return null;
    var key=typeof regTimelineKey==='function'?regTimelineKey():'';
    if(!key||campusBannerDismissed(key))return null;
    return {key:key};
  }catch(e){ return null; }
}
function hmRegCardOn(){ return !!hmRegCardKey(); }
function hmRegCardHtml(where){
  var k=hmRegCardKey(); if(!k)return '';
  try{ return regTimelineHtml(where==='top'?'top':'rail',k.key); }catch(e){ return ''; }
}
''')
one('''  /* Your registration day — from 14 days before Round 1 until its last day (website-registration-day, 2026-10-14) */
  try{ if(typeof regSlotHtml==='function')out+=regSlotHtml('rail'); }catch(e){}
''', '')
span('''.hm-regcard{padding:14px 16px 16px;display:flex''', '''/* Stories: a pin button on every tile (hover / focus; always there for a pinned one), the phone's pin badge on the ring */''',
     CARD_CSS)

# ---------------------------------------------------------------------------------------------- the regday module
one('''    RG.day = null; RG.gap = false; RG.loaded = false;
    if (!active()) return;''',
    '''    RG.day = null; RG.gap = false; RG.loaded = false;
    if (!mineOn()) return;                           /* website-reg-timeline: your own days are read until the term's last day, so the card can show them */''')
one('''    if (!active()) { repaint(); return; }
    loadMine().then(function () { if (!RG.fr) loadFriends(true); });''',
    '''    if (!mineOn()) { repaint(); return; }
    loadMine().then(function () { loadMine2(); if (!RG.fr) loadFriends(true); });''')
one('''    RG.day = null; RG.fr = null; RG.frBusy = 0; RG.gen++;''',
    '''    RG.r2 = null; RG.r2gap = false; RG.r2loaded = false; RG.gen2++; RG.fr2 = null; RG.fr2Busy = 0; RG.fr2N = 0; RG.r2err = ''; RG.tl.edit = null; RG.stripAll = false;   /* website-reg-timeline */
    RG.day = null; RG.fr = null; RG.frBusy = 0; RG.gen++;''')
one('''  /* Home's rail: from 14 days before Round 1 through its last day */
  function railOn() { return active() && today() >= isoAdd(cfgv('REGISTRATION_OPENS'), -14); }
''', '')
# Schedule's card: no friends' list, no rail copy
span('''    if (!active() || (where === 'rail' && !railOn())) return '';''', '''    var L = lines(); if (!L) return '';''',
     '''    /* website-reg-timeline (2026-10-16): Home's rail has the timeline card; this card is Schedule's (plans, builder), and says nothing about friends — the Friends tab has them */
    if (!active() || where === 'rail') return '';
''')
one('''    if (!RG.frBusy) setTimeout(function () { loadFriends(); }, 0);
    var td = today(), up = frRows().filter(function (x) { return x.day >= td; });
''', '')
span('''    if (up.length) {
      var cap = where === 'rail' ''', '''    return h + '</section>';
  }
  function slotHtml''', '')
one('''    try { if (typeof hmRegCardPaint === 'function') hmRegCardPaint(); } catch (_) {}      /* website-sync (2026-10-15): the card on Home's rail */''',
    '''    try { tlPaint(); } catch (_) {}      /* website-reg-timeline (2026-10-16): the timeline card on Home (it was the banner card, website-sync 2026-10-15) */
    try { stripPaint(); } catch (_) {}   /* ... and the strip on the Friends tab */''')
one('''      var sel = from === 'banner' ?''',
    '''      var sel = from === 'timeline' ? '.hm-regcard [data-tl-key="pen1"], .hm-regcard [data-tl-key="add1"]' : from === 'banner' ?''')
one('''  window.TCReg = { parseTime: parseTime,''',
    '''  window.regTimelineHtml = regTimelineHtml; window.regTimelineOn = tlOn; window.regTimelineKey = tlKey; window.regStripPaint = stripPaint;   /* website-reg-timeline (2026-10-16) */
  window.TCReg = { tlRows: function () { var T = tlT(); return T ? tlRows(T, today()) : []; }, strip: stripHtml, loadMine2: loadMine2, loadFriends2: loadFriends2, saveR2: saveMine2, terms: TL_TERMS, parseTime: parseTime,''')
one('''  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { retry(); loadFriends(); } });

  /* ---------------------------------------------------------------- signing in and out */''',
    '''  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { retry(); loadFriends(); } });

''' + BLOCK_JS + '''
  /* ---------------------------------------------------------------- signing in and out */''')

# the dismiss comment was about the rail's old day card, which is gone
one('''regDayRepaint(); else hmRegCardPaint(); }catch(e){}   /* the rail's own day card comes back */''',
    '''regDayRepaint(); else hmRegCardPaint(); }catch(e){}   /* website-reg-timeline: the Schedule card and the timeline redraw */''')
# today(): without mcPacificDay the fallback is still the Pacific day, like mcPacificDay itself
one('''  function today() { try { return mcPacificDay(); } catch (_) { return new Date().toISOString().slice(0, 10); } }''',
    '''  function today() {
    try { return mcPacificDay(); } catch (_) {}
    try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Los_Angeles', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); } catch (_) {}
    return new Date().toISOString().slice(0, 10);
  }''')

f.write_text(s)
print('patched', f)
