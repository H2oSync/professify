"""Champ on the website gets the phone's chat and answer cards (2026-10-15).

Tate: the website's Champ still looked like the old "Hawk" answer screen (plain lines, an "AI" pill, "Not it?"). The phone shows a
chat: the question is a blue bubble on the right, Champ's reply is a white bubble beside Champ's face, a full-width tappable
PREVIEW CARD hangs under it, follow-up questions sit under the newest answer, and the header has a trash can (clear chat) and x.
This ports that to the website's panel, drawn from the website's own data.

 1. THE CHAT. Turns stay on screen, newest at the bottom, until the trash can clears them (24 at most). A turn routes what the
    older renderers append: notes go into Champ's bubble, rows and sections into one card of rows, the rest under them as before.
 2. THE CARDS (all drawn when the answer is shown, from what the page holds then; every part opens the real screen; nothing on a
    card is model text and every string goes in through textContent):
      Your week / Your day  - the week you are IN (a row per day with a bar; a day on a clock with free stretches)
      Free together / Free now - friends who are free when you are; who is free right now, with Message and the friend's page
      Fit                   - a section against Plan A/B/C (or your classes): the week grid, what it clashes with, + Add
      Professors            - the big card for the best one (ratings, sections) and "Also teaching X" rows; one professor
      Class / Sections      - a class with its sections (seats, fits/clashes, +) and the understood filters as chips
      Prerequisites         - the checklist (done, taking now, still needed) with links and Show in Planner
      Game plan             - the order to register, seats, backups
      Your clashes          - the week grid with the overlaps outlined
    Taps ask the question again through answer() (days, follow-ups) or open the class, professor, friend, Plans or add flow.
 3. THE TERM. The site has two terms: the one you are IN (Fall 2026, read-only: NOW_MINE) and the one you are choosing classes
    for (Spring 2027). Free time, a day, who is free now, who is free with you and clashes read the term you are IN, the same
    meetings Home draws (avMyMeets: classes plus your work and activities). Fit, the game plan, plans A-C and add read the
    planning term. "When am I free this week?" used to say "I don't have any classes saved for you yet" for a student with Fall
    classes and no Spring ones, because it read the planning list.
 4. LOCAL QUESTIONS. The phone's chIntent: questions with an unmistakable shape and a lookup for an answer (free time, my day,
    who is free, does X fit, best professor for X) are answered here before the model is asked, so they work offline and signed
    out and the chips under a card never need a round trip.
Run after website-champ-2026-10-14.py (and the security PRs):  python3 <this> <repo>
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
css_f = root / 'hawk-ask.css'; css = css_f.read_text()
js_f = root / 'hawk-ask.js'; js = js_f.read_text()
idx_f = root / 'index.html'; idx = idx_f.read_text()
sw_f = root / 'sw.js'; sw = sw_f.read_text()
def one(s, old, new):
    n = s.count(old); assert n == 1, (n, old[:90]); return s.replace(old, new)
def swap(s, start, end, new):
    """Replace from `start` (unique) through the first `end` after it with `new`."""
    assert s.count(start) == 1, (s.count(start), start[:90])
    a = s.index(start); b = s.index(end, a); assert b >= a, end[:90]
    return s[:a] + new + s[b + len(end):]
def cut(s, start, end):
    """Delete from `start` (unique) up to, not including, `end` (unique)."""
    assert s.count(start) == 1 and s.count(end) == 1, (s.count(start), s.count(end), start[:70], end[:70])
    a = s.index(start); b = s.index(end); assert a < b, (start[:60], end[:60])
    return s[:a] + s[b:]

CARDS = r'''  /* ===============================================================================================
     THE CHAT AND ITS CARDS — website-champ-cards (2026-10-15). The phone's Champ (app/index.html, "Champ answer cards",
     Tate 2026-10-08), drawn here from the website's own data.

     An answer is { t, card, acts, follow }: ONE short line in Champ's bubble, then a full-width card, then follow-up
     questions under the newest answer. The card is drawn when the answer is shown, from what the page holds at that moment
     (seats, ratings and weeks are always current), and every part of it opens the real screen. The model only ever NAMES
     a tool; nothing on a card is model text, and every string a card prints goes in through textContent, never markup.

     TWO TERMS. Free time, a day, "who's free now" and clashes are about the week the student is IN: the now-term
     (Fall 2026 = mcNowTerm; avMyMeets() reads NOW_MINE, the same week Home draws). A plan, a fit, a game plan and an add are
     about the term they are choosing in (Spring 2027 = mcTerm; SEAT_SECTIONS, My Classes, Plans A-C). They are never mixed.
     When the site has one term (or Spring has begun) both are the same list and nothing changes.
     =============================================================================================== */
  var D5 = ['Mo', 'Tu', 'We', 'Th', 'Fr'];
  var DAY3 = { Mo: 'Mon', Tu: 'Tue', We: 'Wed', Th: 'Thu', Fr: 'Fri', Sa: 'Sat', Su: 'Sun' };
  var DAY_S0 = 480;                  // a day card starts at 8a
  var TOGETHER_END = 1080;           // "free together" looks at the class day, 8a-6p
  var ICON_PATH = { chev: 'M9 6l6 6-6 6', trash: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5M14 11v5', plus: 'M12 5v14M5 12h14' };

  function twoTerms() { try { return has('mcTwoTerms') && !!global.mcTwoTerms(); } catch (_) { return false; } }
  function nowLabel() { try { return has('mcNowLabel') ? String(global.mcNowLabel() || '') : ''; } catch (_) { return ''; } }
  function planLabel() { try { return has('mcTermLabel') ? String(global.mcTermLabel() || '') : ''; } catch (_) { return ''; } }
  function termWord(label) { return label || 'this term'; }

  function hs(m) { var h = Math.floor(m / 60) % 24, mi = m % 60; return ((h % 12) || 12) + (mi ? ':' + (mi < 10 ? '0' : '') + mi : '') + (h >= 12 ? 'p' : 'a'); }
  function lenW(m) { var h = Math.floor(m / 60), r = m % 60; return (h ? h + 'h' : '') + (h && r ? ' ' : '') + (r ? r + 'm' : ''); }
  function firstName(n) { return String(n || '').trim().split(/\s+/)[0] || 'Friend'; }
  function plural(n, one, many) { return n + ' ' + (n === 1 ? one : (many || one + 's')); }
  function lower1(s) { s = String(s || ''); return s.charAt(0).toLowerCase() + s.slice(1); }

  function icon(kind, px, sw) {
    var s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('width', String(px || 16)); s.setAttribute('height', String(px || 16));
    s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor'); s.setAttribute('stroke-width', String(sw || 2.4));
    s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round'); s.setAttribute('aria-hidden', 'true');
    var p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('d', ICON_PATH[kind] || ''); s.appendChild(p);
    return s;
  }
  function button(cls, label, aria) {
    var b = make('button', cls, label); b.type = 'button';
    if (aria) b.setAttribute('aria-label', aria);
    return b;
  }
  /* A tap that goes somewhere says where it went, once, at the foot of that answer — the page behind has just changed. */
  function showWent(from, text) {
    if (!text) return;
    var turn = from && from.closest ? from.closest('.hawk-turn') : null;
    if (!turn || !turn.isConnected) { var all = turnsIn(); turn = all[all.length - 1] || null; }   // the tap re-drew its own turn
    Array.prototype.forEach.call(els.log.querySelectorAll('.hawk-went'), function (n) { n.remove(); });
    var w = make('div', 'hawk-went', text);
    if (!turn) { els.log.appendChild(w); return; }
    var follow = turn.querySelector('.hawk-follow');
    if (follow) turn.insertBefore(w, follow); else turn.appendChild(w);
  }
  function tap(b, fn) {
    b.addEventListener('click', function () { var w = null; try { w = fn(); } catch (_) {} if (w) showWent(b, w); });
    return b;
  }
  function pill(text, tone) { return make('span', 'hawk-pill' + (tone ? ' hawk-pill--' + tone : ''), text); }
  function starPill(r, who) {
    if (r == null) return pill('No ratings yet' + (who ? ' · ' + who : ''));
    return pill('★ ' + r.toFixed(1) + (who ? ' ' + who : ''), r >= 4 ? 'ok' : (r >= 3 ? 'mid' : 'bad'));
  }
  function inkFor(hex) {
    var m = /^#?([0-9a-f]{6})$/i.exec(String(hex || '').trim()); if (!m) return '#fff';
    var n = parseInt(m[1], 16), f = function (v) { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
    var L = .2126 * f(n >> 16) + .7152 * f((n >> 8) & 255) + .0722 * f(n & 255);
    return L > .4 ? '#111' : '#fff';
  }
  function initialsOf(name) {
    var p = String(name || '').trim().split(/\s+/).filter(Boolean);
    return ((p[0] || '?').charAt(0) + (p.length > 1 ? p[p.length - 1].charAt(0) : '')).toUpperCase();
  }
  function avatar(f, px) {
    var a = make('span', 'hawk-av'); a.style.width = a.style.height = px + 'px'; a.style.fontSize = Math.round(px * .36) + 'px';
    a.setAttribute('aria-hidden', 'true');
    var url = ''; try { url = has('frAvatarFor') ? String(global.frAvatarFor(f) || '') : String(f.avatar_url || ''); } catch (_) {}
    if (url && /^(https?:|data:image\/)/i.test(url)) { var im = document.createElement('img'); im.alt = ''; im.src = url; a.appendChild(im); return a; }
    var col = ''; try { col = f.color || (has('hmFriendColor') ? global.hmFriendColor(f) : ''); } catch (_) {}
    if (/^#[0-9a-f]{6}$/i.test(col)) { a.style.background = col; a.style.color = inkFor(col); }
    a.textContent = initialsOf(f.name);
    return a;
  }
  function profAvatar(name, px) {
    var a = make('span', 'hawk-av hawk-av--prof', initialsOf(name)); a.style.width = a.style.height = px + 'px'; a.style.fontSize = Math.round(px * .36) + 'px';
    a.setAttribute('aria-hidden', 'true');
    return a;
  }

  /* ---- THE WEEK YOU ARE IN (the now-term). One list of meetings — classes and your own work & activities — as Home reads it. */
  function nowMeetsAll() {
    try { if (has('avMyMeets')) return global.avMyMeets() || []; } catch (_) {}
    var out = [];
    try {
      var nm = has('nowMine') ? global.nowMine() : { classes: myClasses, meta: myClassMeta };
      (has('myClassMeets') ? global.myClassMeets(nm.classes, nm.meta) : []).forEach(function (m) { if (m && m.meet) out.push(m); });
    } catch (_) {}
    return out;
  }
  function nowCodes() { try { return (has('nowMine') ? global.nowMine().classes : (myClasses || [])).slice(); } catch (_) { return []; } }
  function nowUnplaced(meets) {
    var placed = {}; (meets || []).forEach(function (m) { if (m && !m.cm) placed[m.code] = 1; });
    return nowCodes().filter(function (c) { return !placed[c]; });
  }
  function nowRating(code) {
    try {
      var nm = has('nowMine') ? global.nowMine() : null, m = nm && nm.meta && nm.meta[code];
      var raw = m && ((Array.isArray(m.secs) && m.secs[0] && m.secs[0].prof) || m.prof);
      var p = raw ? profOf({ instructor: raw }) : null;
      return p && p.rating != null ? p.rating : null;
    } catch (_) { return null; }
  }
  function dayItems(meets, d) {
    var out = [];
    (meets || []).forEach(function (m) {
      var mt = m && m.meet;
      if (!mt || !mt.days || mt.days.indexOf(d) < 0 || typeof mt.start !== 'number' || typeof mt.end !== 'number') return;
      out.push({ code: String(m.code || ''), s: mt.start, e: mt.end, busy: !!m.cm, cmId: m.cm === 'mine' ? String(m.id || '') : '' });
    });
    return out.sort(function (a, b) { return a.s - b.s || a.e - b.e; });
  }
  function gapsIn(list, a, b) {
    var out = [], t = a;
    list.forEach(function (s) { if (s.s > t && Math.min(s.s, b) - t >= MIN_GAP) out.push([t, Math.min(s.s, b)]); t = Math.max(t, s.e); });
    if (b - t >= MIN_GAP) out.push([t, b]);
    return out;
  }
  function dayStart(list) { return Math.min(DAY_S0, list.length ? Math.floor(list[0].s / 60) * 60 : DAY_S0); }
  function dayEnd(list) { return Math.min(1440, Math.max(1080, list.length ? Math.ceil((list[list.length - 1].e + 60) / 60) * 60 : 0)); }
  function freeWords(gaps, a, b) {
    var w = function (g) { return g[0] <= a && g[1] >= b ? 'all day' : (g[0] <= a ? 'before ' + hs(g[1]) : (g[1] >= b ? 'after ' + hs(g[0]) : hs(g[0]) + '–' + hs(g[1]))); };
    var ws = gaps.map(w);
    return ws.length <= 2 ? ws.join(' and ') : ws.slice(0, -1).join(', ') + ' and ' + ws[ws.length - 1];
  }
  /* Work, practice and the rest, in words: "Barista 3p–6p". */
  function busyWords(list) {
    var seen = [], out = [];
    list.forEach(function (x) { if (x.busy && seen.indexOf(x.code) < 0) { seen.push(x.code); out.push(x.code + ' ' + hs(x.s) + '–' + hs(x.e)); } });
    return out.slice(0, 2).join(' · ');
  }
  function realDay() { return DAY_ORDER[(new Date().getDay() + 6) % 7]; }
  function todayKey() { var k = realDay(); return D5.indexOf(k) >= 0 ? k : 'Mo'; }
  function nextDay(d) { return D5[(D5.indexOf(d) + 1) % 5]; }
  function tomorrowKey() { return D5[(D5.indexOf(realDay()) + 1) % 5]; }
  function nowMin() { var n = new Date(); return n.getHours() * 60 + n.getMinutes(); }
  function nowWords() { return DAY3[realDay()] + ' ' + hs(nowMin()); }

  function openMyWeek() {
    /* "Week ›" — the week you are in: the same place Home's My schedule opens. */
    try { if (has('hmOpenCal')) { global.hmOpenCal(); return 'Opened your week'; } } catch (_) {}
    return goPlace('week view');
  }
  function openPlan(P) {
    try { if (global.TCPlans && global.TCPlans.setCur && P) global.TCPlans.setCur(P); } catch (_) {}
    return goPlace('watchlist');
  }
  /* A class you are in NOW opens on its Fall page (read-only), whatever screen Champ happens to be over. */
  function goNowClass(code) {
    var went = goClass(code);
    try {
      if (twoTerms() && global.cpNow === false && nowCodes().indexOf(code) >= 0) {
        global.cpNow = true;
        if (has('fallEnsure')) global.fallEnsure();
        if (has('renderClassPage')) global.renderClassPage();
      }
    } catch (_) {}
    return went;
  }
  function openFriend(f) {
    try { if (has('openFriendProfile')) { global.openFriendProfile(f.id, 'classes'); return 'Opened ' + f.name; } } catch (_) {}
    return goPlace('friends');
  }
  function messageFriend(f) {
    try { if (has('msgWith')) { global.msgWith(f.id); return 'Opened your chat with ' + firstName(f.name); } } catch (_) {}
    return goPlace('messages');
  }
  function goProfId(id, name) {
    if (id && has('openProf')) { try { global.openProf(id); return 'Opened ' + name; } catch (_) {} }
    return goProfessor(name);
  }
  /* The site's own "add to a plan" flow: a button that wears the same attributes as planBtnHtml, so the page's own click
     handler opens its chooser (Plan A / B / C, and Replace / Keep both on a clash). Nothing is added by Champ itself. */
  function planAddBtn(code, crn, cls, aria) {
    var b = button(cls + ' pl2-cpbtn', '', aria);
    b.setAttribute('data-pl-act', 'choose'); b.setAttribute('data-code', code); b.setAttribute('data-crn', String(crn));
    b.setAttribute('aria-haspopup', 'true');
    return b;
  }

  /* ---- the card frame ---------------------------------------------------------------------- */
  function cardFrame(label, extra) {
    var s = make('section', 'hawk-card' + (extra ? ' ' + extra : '')); s.setAttribute('aria-label', label); return s;
  }
  function cardHead(title, openText, openFn, extras) {
    var h = make('div', 'hawk-ch');
    if (title) h.appendChild(make('span', 'hawk-ch__t', title));
    (extras || []).forEach(function (x) { if (x) h.appendChild(x); });
    h.appendChild(make('span', 'hawk-ch__gap'));
    if (openText) h.appendChild(tap(button('hawk-ch__open', openText), openFn));
    return h;
  }
  function termPill() { return twoTerms() && nowLabel() ? pill(nowLabel()) : null; }
  function kicker(text) { return make('span', 'hawk-k', text); }

  /* ---- Your day: the day laid out on a clock, free stretches dashed, classes as buttons ------------- */
  function cardDay(c) {
    var d = c.d, meets = nowMeetsAll(), l = dayItems(meets, d), a = dayStart(l), b = dayEnd(l), span = b - a;
    var PH = 40, H = Math.round(span / 60 * PH), y = function (m) { return (m - a) / span * H; };
    var sec = cardFrame('Your ' + DAY_FULL[d]);
    var nc = l.filter(function (x) { return !x.busy; }).length, bw = busyWords(l);
    sec.appendChild(cardHead(DAY_FULL[d], 'Week ›', openMyWeek, [pill(plural(nc, 'class', 'classes'), 'blue'), bw ? pill(bw) : null, termPill()]));
    var wrap = make('div', 'hawk-day');
    var labs = make('div', 'hawk-day__lab'); labs.style.height = H + 'px'; labs.setAttribute('aria-hidden', 'true');
    for (var m = a; m < b; m += 120) { var sp = make('span', '', hs(m)); sp.style.top = y(m).toFixed(1) + 'px'; labs.appendChild(sp); }
    var col = make('div', 'hawk-day__col'); col.style.height = H + 'px';
    var bot = {};
    var bh = function (s) { return Math.max(40, (s.e - s.s) / span * H - 2); };
    l.forEach(function (s) { bot[s.e] = Math.max(bot[s.e] || 0, y(s.s) + 1 + bh(s)); });
    gapsIn(l, a, b).forEach(function (g) {
      var open = g[1] >= b && l.length, top = Math.max(y(g[0]) + 2, (bot[g[0]] || 0) + 2), h = Math.max(24, y(g[1]) - 2 - top);
      var f = make('div', 'hawk-day__free' + (h < 40 ? ' hawk-day__free--one' : ''));
      f.style.top = top.toFixed(1) + 'px'; f.style.height = h.toFixed(1) + 'px';
      f.appendChild(make('b', '', open ? 'Free after ' + hs(g[0]) : (g[0] <= a && g[1] >= b ? 'Free all day' : 'Free ' + hs(g[0]) + '–' + hs(g[1]))));
      if (!open) f.appendChild(make('span', '', lenW(g[1] - g[0])));
      col.appendChild(f);
    });
    l.forEach(function (s) {
      var blk = button('hawk-day__blk' + (s.busy ? ' hawk-day__blk--cm' : ''), '', s.code + ', ' + hs(s.s) + ' to ' + hs(s.e));
      blk.style.top = (y(s.s) + 1).toFixed(1) + 'px'; blk.style.height = bh(s).toFixed(1) + 'px';
      blk.appendChild(make('b', '', s.code)); blk.appendChild(make('span', '', hs(s.s) + '–' + hs(s.e)));
      if (s.busy) {
        /* the commitments module opens its editor from this attribute on any button, anywhere on the page */
        if (s.cmId) { blk.setAttribute('data-cm-act', 'edit'); blk.setAttribute('data-id', s.cmId); } else blk.disabled = true;
      } else {
        var r = nowRating(s.code); if (r != null) blk.appendChild(starPill(r));
        tap(blk, function () { return goNowClass(s.code); });
      }
      col.appendChild(blk);
    });
    var nm = nowMin();
    if (d === realDay() && nm > a && nm < b) { var now = make('span', 'hawk-day__now'); now.style.top = y(nm).toFixed(1) + 'px'; now.setAttribute('aria-label', 'Now'); col.appendChild(now); }
    wrap.appendChild(labs); wrap.appendChild(col); sec.appendChild(wrap);
    return sec;
  }

  /* ---- Your week: a row per day with a bar of its classes; tap a day to ask about that day ---------- */
  function cardWeek(c) {
    var ds = (c.days || D5).filter(function (d) { return D5.indexOf(d) >= 0; }), meets = nowMeetsAll();
    if (!ds.length) ds = D5.slice();
    var lists = ds.map(function (d) { return dayItems(meets, d); });
    var a = Math.min.apply(null, lists.map(dayStart)), b = Math.max.apply(null, lists.map(dayEnd)), span = b - a;
    var pc = function (m) { return ((m - a) / span * 100).toFixed(1); };
    var sec = cardFrame('Your free time');
    sec.appendChild(cardHead('Your week', 'Week ›', openMyWeek, [termPill()]));
    ds.forEach(function (d, i) {
      var l = lists[i], g = gapsIn(l, a, b);
      var row = button('hawk-wrow', '', 'When am I free ' + DAY_FULL[d] + '?');
      row.setAttribute('data-day', d);
      row.appendChild(make('span', 'hawk-wrow__d', DAY3[d]));
      var mid = make('span', 'hawk-wrow__m'), bar = make('span', 'hawk-wrow__bar'); bar.setAttribute('aria-hidden', 'true');
      l.forEach(function (s) { var x = document.createElement('i'); x.style.left = pc(s.s) + '%'; x.style.width = ((s.e - s.s) / span * 100).toFixed(1) + '%'; bar.appendChild(x); });
      mid.appendChild(bar);
      mid.appendChild(make('span', 'hawk-wrow__t', l.length ? (g.length ? 'Free ' + freeWords(g, a, b) : 'Booked ' + hs(a) + '–' + hs(l[l.length - 1].e)) : 'No classes'));
      row.appendChild(mid); row.appendChild(icon('chev', 16));
      row.addEventListener('click', function () { answer('When am I free ' + DAY_FULL[d] + '?'); });
      sec.appendChild(row);
    });
    var ax = make('div', 'hawk-wax'); ax.setAttribute('aria-hidden', 'true');
    ax.appendChild(make('span', '', hs(a))); ax.appendChild(make('span', '', hs(b)));
    sec.appendChild(ax);
    return sec;
  }

  /* ---- A week as a grid: your classes, a section that would go in (dashed) and what it runs into (red) ---- */
  function weekGridEl(blocks, o) {
    o = o || {};
    var lo = DAY_S0, hi = 1020;
    blocks.forEach(function (x) { lo = Math.min(lo, Math.floor(x.s / 60) * 60); hi = Math.max(hi, Math.ceil(x.e / 60) * 60); });
    var H = o.h || 230, span = hi - lo, y = function (m) { return (m - lo) / span * H; };
    var w = make('div', 'hawk-wk');
    var head = make('div', 'hawk-wk__row hawk-wk__head'); head.setAttribute('aria-hidden', 'true');
    head.appendChild(make('span'));
    D5.forEach(function (d) { head.appendChild(make('span', '', DAY3[d].charAt(0))); });
    w.appendChild(head);
    var body = make('div', 'hawk-wk__row');
    var labs = make('div', 'hawk-wk__lab'); labs.style.height = H + 'px'; labs.setAttribute('aria-hidden', 'true');
    for (var m = lo; m < hi; m += 120) { var sp = make('span', '', hs(m)); sp.style.top = y(m).toFixed(1) + 'px'; labs.appendChild(sp); }
    body.appendChild(labs);
    D5.forEach(function (d) {
      var lane = make('div', 'hawk-wk__lane'); lane.style.height = H + 'px';
      blocks.filter(function (x) { return x.days.indexOf(d) >= 0; }).forEach(function (x) {
        var bk = button('hawk-wk__blk' + (x.cls ? ' ' + x.cls : ''), x.code, x.code + ', ' + DAY3[d] + ' ' + hs(x.s) + ' to ' + hs(x.e));
        bk.style.top = y(x.s).toFixed(1) + 'px'; bk.style.height = Math.max(14, (x.e - x.s) / span * H - 1).toFixed(1) + 'px';
        if (x.cmId) { bk.setAttribute('data-cm-act', 'edit'); bk.setAttribute('data-id', x.cmId); }
        else if (x.go) tap(bk, x.go);
        else bk.disabled = true;
        lane.appendChild(bk);
      });
      body.appendChild(lane);
    });
    w.appendChild(body);
    return w;
  }

  /* ---- Does it clash? the classes you choose in (this term), a plan, and your work & activities ---------- */
  function cmMeets() { try { return has('cmBlocks') ? (global.cmBlocks('me') || []) : []; } catch (_) { return []; } }
  function planBase(P) {
    var out = [];
    if (P === 'mine') {
      try { (has('myClassMeets') ? global.myClassMeets(myClasses || [], myClassMeta || {}) : []).forEach(function (m) { if (m && m.meet) out.push({ code: m.code, meet: m.meet, crn: '', label: m.code }); }); } catch (_) {}
      return out;
    }
    try {
      var T = global.TCPlans; if (!T || !T.planInfo) return out;
      T.planInfo(P).items.forEach(function (i) { if (i && !i.missing) out.push({ code: i.code, meet: i.meet, crn: i.crn, label: i.label || i.code }); });
    } catch (_) {}
    return out;
  }
  function whenLong(row) {
    var m = meetOf(row);
    if (!m) return modeOf(row) === 'async' ? 'Online — no set time' : 'Time not posted';
    return m.days.map(function (d) { return DAY_SHORT[d] || d; }).join('') + ' ' + hs(m.start) + '–' + hs(m.end);
  }
  function secEntry(code, row) {
    var meet = meetOf(row);
    return { row: row, code: code, crn: String(row.class_nbr || row.crn || ''), no: secNumber(row), meet: meet,
      label: code + (secNumber(row) ? '-' + secNumber(row) : ''), when: whenLong(row), prof: profOf(row), seat: seatOf(row) };
  }
  function seatRank(s) { var c = s && s.seat && s.seat.cls; return c === 'open' ? 0 : c === 'wait' ? 1 : c === 'full' ? 3 : 2; }
  function clashOf(base, code, e) {
    var out = [];
    if (!e.meet) return out;
    base.forEach(function (x) { if (x.code !== code && x.meet && overlaps(e.meet, x.meet)) out.push({ code: x.code }); });
    cmMeets().forEach(function (x) { if (x.meet && overlaps(e.meet, x.meet)) out.push({ code: x.label || x.code, cm: true }); });
    return out;
  }
  function fitCalc(code, P) {
    var base = planBase(P), inIt = base.filter(function (x) { return x.code === code; })[0] || null;
    var sc = sectionsOf(code).map(function (r) { var e = secEntry(code, r); return { e: e, cl: clashOf(base, code, e) }; })
      .sort(function (x, y) {
        return (x.cl.length - y.cl.length) || (seatRank(x.e) - seatRank(y.e))
          || ((y.e.prof && y.e.prof.rating != null ? y.e.prof.rating : -1) - (x.e.prof && x.e.prof.rating != null ? x.e.prof.rating : -1));
      });
    return { base: base, inIt: inIt, best: sc[0] || null, fits: sc.filter(function (x) { return !x.cl.length; }).length, n: sc.length };
  }
  function planName(P) { return P === 'mine' ? 'your classes' : 'Plan ' + P; }
  function curSlot() { try { return global.TCPlans && global.TCPlans.cur ? global.TCPlans.cur() : 'A'; } catch (_) { return 'A'; } }
  function seatsLoaded() { return seatCount() > 0; }
  function seatWords(e) {
    var s = e.seat;
    if (!s || s.unknown || s.cls === 'unknown') return 'Seats unknown';
    try { if (has('seatBadge')) return global.seatBadge(s); } catch (_) {}
    var c = seatChip(e.row); return c ? c.text : 'Seats unknown';
  }
  function profPill(e) { return e.prof ? starPill(e.prof.rating, e.prof.name.split(/\s+/).slice(-1)[0]) : pill('Instructor not assigned'); }

  function cardFit(c) {
    var f = fitCalc(c.code, c.P), s = f.best && f.best.e; if (!s) return null;
    var inIt = !!f.inIt, cl = inIt ? [] : f.best.cl, P = c.P;
    var sec = cardFrame(c.code + ' in ' + planName(P));
    var tag = make('span', 'hawk-plan' + (P === 'mine' ? ' hawk-plan--mine' : ' hawk-plan--' + P), P === 'mine' ? 'My classes' : 'Plan ' + P);
    sec.appendChild(cardHead('', 'Open ›', function () { return P === 'mine' ? goPlace('my classes') : openPlan(P); }, [tag, make('span', 'hawk-ch__s', s.label)]));
    var blocks = [], clashCodes = {};
    cl.forEach(function (x) { clashCodes[x.code] = 1; });
    f.base.forEach(function (x) {
      if (!x.meet || (x.code === c.code && !inIt)) return;
      blocks.push({ code: x.code, days: x.meet.days, s: x.meet.start, e: x.meet.end, cls: clashCodes[x.code] ? 'hawk-wk__blk--clash' : '', go: (function (cd) { return function () { return goClass(cd); }; })(x.code) });
    });
    cmMeets().forEach(function (x) { if (x.meet) blocks.push({ code: x.label || x.code, days: x.meet.days, s: x.meet.start, e: x.meet.end, cmId: x.mine ? String(x.id) : '', cls: 'hawk-wk__blk--cm' + (clashCodes[x.label || x.code] ? ' hawk-wk__blk--clash' : '') }); });
    if (!inIt && s.meet) blocks.push({ code: c.code, days: s.meet.days, s: s.meet.start, e: s.meet.end, cls: 'hawk-wk__blk--ghost' + (cl.length ? ' hawk-wk__blk--clash' : ''), go: function () { return goClass(c.code); } });
    if (blocks.length) sec.appendChild(weekGridEl(blocks, { h: 200 }));
    var facts = make('div', 'hawk-facts');
    facts.appendChild(inIt ? pill('In ' + planName(P), 'blue') : (cl.length ? pill('Clashes with ' + cl.map(function (x) { return x.code; }).join(', '), 'bad') : pill('✓ No clashes', 'ok')));
    facts.appendChild(pill(s.when)); facts.appendChild(profPill(s)); facts.appendChild(pill(seatWords(s)));
    sec.appendChild(facts);
    var btns = make('div', 'hawk-btns');
    if (!inIt) {
      if (P === 'mine') {
        if (has('mcEnrollSec')) btns.appendChild(tap(button('hawk-btn hawk-btn--go', 'Add it', 'Add ' + s.label + ' to your classes'), function () { global.mcEnrollSec(c.code, s.crn); return 'Confirm it in the box that opened'; }));
      } else {
        var add = planAddBtn(c.code, s.crn, 'hawk-btn hawk-btn--go', 'Add ' + s.label + ' to Plan ' + P);
        add.textContent = 'Add to Plan ' + P; btns.appendChild(add);
      }
    }
    btns.appendChild(tap(button('hawk-btn hawk-btn--soft', 'Open ' + c.code), function () { return goClass(c.code); }));
    sec.appendChild(btns);
    return sec;
  }
  function planArg(p) { return (p === 'mine' || /^[ABC]$/.test(String(p || ''))) ? p : curSlot(); }
  function ansFit(code, P) {
    P = planArg(P);
    if (!seatsLoaded()) return { t: 'Classes are still loading — ask again in a moment.' };
    if (!sectionsOf(code).length) return { t: code + ' isn’t offered in ' + termWord(planLabel()) + '.' };
    if (P === 'mine' && !planBase('mine').some(function (x) { return x.meet; }) && !cmMeets().length) {
      return { t: 'You haven’t added ' + termWord(planLabel()) + ' classes with times yet, so anything fits.', card: { k: 'cls', code: code }, acts: [['Open Schedule', function () { return goPlace('schedule'); }]] };
    }
    var f = fitCalc(code, P), L = planName(P);
    var follow = [P === 'mine' ? 'Does ' + code + ' fit my Plan ' + curSlot() + '?' : 'Does ' + code + ' fit my schedule?', 'Best professor for ' + code + '?'];
    if (f.inIt) return { t: code + ' is already in ' + L + '.', card: { k: 'fit', code: code, P: P }, follow: follow };
    var s = f.best.e, lab = s.no ? 'Section ' + s.no : 'a section';
    if (!s.meet) return { t: 'Yes — ' + lab + ' has no set time, so it fits ' + L + '.', card: { k: 'fit', code: code, P: P }, follow: follow };
    if (!f.best.cl.length) return { t: 'Yes — ' + lab + ' fits ' + L + (f.fits > 1 ? ' (' + f.fits + ' of ' + f.n + ' sections do)' : '') + '.', card: { k: 'fit', code: code, P: P }, follow: follow };
    var other = ['Other ' + code + ' sections?'].concat(follow.slice(1));
    if (f.best.cl.every(function (x) { return x.cm; })) return { t: 'No — every ' + code + ' section overlaps your ' + f.best.cl.map(function (x) { return x.code; }).join(', ') + '.', card: { k: 'fit', code: code, P: P }, follow: other };
    return { t: 'No — every ' + code + ' section clashes with ' + L + '.', card: { k: 'fit', code: code, P: P }, follow: other };
  }

  /* ---- your day, and your week's free time (the now-term) ---- */
  function emptyWeek() {
    return { t: 'You haven’t added ' + termWord(nowLabel()) + ' classes with times yet.', acts: [['Open Schedule', function () { return goPlace('schedule'); }]] };
  }
  function unplacedNotes(meets) {
    var u = nowUnplaced(meets);
    return u.length ? ['Not counted — no meeting time on ' + u.join(', ') + '.'] : [];
  }
  function ansDay(d, mode) {
    var meets = nowMeetsAll(); if (!meets.length) return emptyWeek();
    var l = dayItems(meets, d), a = dayStart(l), b = dayEnd(l), gaps = gapsIn(l, a, b), D = DAY_FULL[d];
    var follow = ['When am I free ' + DAY_FULL[nextDay(d)] + '?', 'Who’s free with me ' + D + '?'];
    var ans;
    if (!l.length) ans = { t: 'No classes ' + D + ' — the whole day is yours.', card: { k: 'day', d: d }, follow: follow };
    else if (mode === 'free') ans = { t: gaps.length ? 'Free ' + freeWords(gaps, a, b) + '.' : 'No free stretch of 30 minutes or more between ' + hs(a) + ' and ' + hs(l[l.length - 1].e) + '.', card: { k: 'day', d: d }, follow: follow };
    else {
      var today = d === realDay(), nm = nowMin();
      var cur = today && l.filter(function (s) { return s.s <= nm && nm < s.e; })[0], next = today && l.filter(function (s) { return s.s > nm; })[0];
      var nc = l.filter(function (s) { return !s.busy; }).length, bw = busyWords(l);
      ans = { t: today ? [cur ? (cur.busy ? cur.code + ' until ' + hs(cur.e) + '.' : 'You’re in ' + cur.code + ' until ' + hs(cur.e) + '.') : '', next ? 'Next: ' + next.code + ' at ' + hs(next.s) + '.' : 'Nothing else today.'].filter(Boolean).join(' ')
        : [nc ? plural(nc, 'class', 'classes') : '', bw].filter(Boolean).join(' and ') + ' ' + D + ', ' + hs(l[0].s) + '–' + hs(l[l.length - 1].e) + '.',
        card: { k: 'day', d: d }, follow: follow };
    }
    ans.notes = unplacedNotes(meets);
    return ans;
  }
  function ansFreeWeek(days) {
    var meets = nowMeetsAll(); if (!meets.length) return emptyWeek();
    var ds = (days && days.length ? days : D5).filter(function (d) { return D5.indexOf(d) >= 0; });
    if (!ds.length) ds = D5.slice();
    return { t: 'Your free time, day by day. Tap a day to see it.', card: { k: 'week', days: ds }, notes: unplacedNotes(meets),
      follow: ds.length > 1 ? ['Who’s free with me ' + DAY_FULL[todayKey()] + '?'] : [] };
  }

  /* ---- friends free at the same time as you ---- */
  function friendMeets(f) { try { return has('avMeetsOf') ? (global.avMeetsOf(f) || []) : []; } catch (_) { return []; } }
  function friendTimed(f) { return friendMeets(f).some(function (m) { return m && !m.cm; }); }
  function togetherCalc(d) {
    var myGaps = gapsIn(dayItems(nowMeetsAll(), d), DAY_S0, TOGETHER_END), out = [];
    appFriends().forEach(function (f) {
      if (!friendTimed(f)) return;
      var theirs = gapsIn(dayItems(friendMeets(f), d), DAY_S0, TOGETHER_END), both = [];
      myGaps.forEach(function (x) { theirs.forEach(function (y) { var s = Math.max(x[0], y[0]), e = Math.min(x[1], y[1]); if (e - s >= MIN_GAP) both.push([s, e]); }); });
      both.sort(function (p, q) { return (q[1] - q[0]) - (p[1] - p[0]); });
      if (both.length) out.push({ f: f, both: both, best: both[0] });
    });
    return out.sort(function (p, q) { return (q.best[1] - q.best[0]) - (p.best[1] - p.best[0]) || p.best[0] - q.best[0]; });
  }
  function togetherWords(x) { return 'Free together ' + hs(x.best[0]) + '–' + hs(x.best[1]) + ' · ' + lenW(x.best[1] - x.best[0]) + (x.both.length > 1 ? ' · +' + (x.both.length - 1) + ' more' : ''); }
  function addFriendsAct() { return ['Add friends', function () { return goPlace('add friend'); }]; }
  function ansTogether(d) {
    if (!appFriends().length) return { t: 'Add friends and I can find when you’re both free.', acts: [addFriendsAct()] };
    if (!nowMeetsAll().length) return { t: 'Add your ' + termWord(nowLabel()) + ' classes and I can match your free time with friends’.', acts: [['Open Schedule', function () { return goPlace('schedule'); }]] };
    var l = togetherCalc(d), D = DAY_FULL[d];
    if (!l.length) return { t: appFriends().some(friendTimed) ? 'None of your friends is free at the same time as you on ' + D + ' between ' + hs(DAY_S0) + ' and ' + hs(TOGETHER_END) + '.' : 'None of your friends has added classes with times yet.', follow: ['Who’s free with me ' + DAY_FULL[nextDay(d)] + '?'] };
    var names = l.slice(0, 2).map(function (x) { return firstName(x.f.name); });
    return { t: (l.length > 2 ? names.join(', ') + ' and ' + (l.length - 2) + ' more' : names.join(' and ')) + ' ' + (l.length === 1 ? 'is' : 'are') + ' free when you are on ' + D + '.',
      card: { k: 'together', d: d }, follow: ['When am I free ' + D + '?', 'Who’s free with me ' + DAY_FULL[nextDay(d)] + '?'] };
  }
  function ansTogetherWith(f, d) {
    var nm = firstName(f.name);
    if (!nowMeetsAll().length) return { t: 'None of your ' + termWord(nowLabel()) + ' classes have set times yet, so I can’t match your free time with ' + nm + '’s.', acts: [['Open Schedule', function () { return goPlace('schedule'); }]] };
    if (!friendTimed(f)) return { t: 'None of ' + nm + '’s ' + termWord(nowLabel()) + ' classes have set times, so I can’t match your free time.', acts: [['Open ' + nm, function () { return openFriend(f); }]] };
    if (d) {
      var x = togetherCalc(d).filter(function (y) { return y.f === f; })[0];
      return x ? { t: 'You and ' + nm + ' are both free ' + hs(x.best[0]) + '–' + hs(x.best[1]) + ' on ' + DAY_FULL[d] + (x.both.length > 1 ? ', and ' + (x.both.length - 1) + ' more time' + (x.both.length > 2 ? 's' : '') : '') + '.', card: { k: 'together', d: d, f: f } }
        : { t: 'You and ' + nm + ' aren’t free at the same time on ' + DAY_FULL[d] + ' between ' + hs(DAY_S0) + ' and ' + hs(TOGETHER_END) + '. Here’s the week:', card: { k: 'togetherWk', f: f } };
    }
    var n = D5.filter(function (dd) { return togetherCalc(dd).some(function (y) { return y.f === f; }); }).length;
    return { t: n ? 'You and ' + nm + ' are both free on ' + n + ' of 5 days.' : 'You and ' + nm + ' aren’t free at the same time on any weekday between ' + hs(DAY_S0) + ' and ' + hs(TOGETHER_END) + '.', card: { k: 'togetherWk', f: f } };
  }
  function ansFriendNow(f) {
    var nm = firstName(f.name), line = freeLine(freeState(f));
    return { t: line ? nm + ': ' + line + '.' : 'I don’t have times for ' + nm + '’s classes, so I can’t say.',
      acts: [['Message ' + nm, function () { return messageFriend(f); }], ['Open ' + nm, function () { return openFriend(f); }]] };
  }
  function ansNow() {
    var list = appFriends();
    if (!list.length) return { t: 'Add friends and I can tell you who’s free.', acts: [addFriendsAct()] };
    var free = 0, busy = 0;
    list.forEach(function (f) { var st = freeState(f); if (st.state === 'open') free++; else if (st.state === 'class') busy++; });
    var follow = ['Who’s free with me ' + DAY_FULL[todayKey()] + '?'], unk = list.length - free - busy;
    if (!free && !busy) return { t: 'None of your friends’ classes have times I can read yet, so I can’t say who’s free.', follow: follow };
    return { t: free ? plural(free, 'friend is', 'friends are') + ' free · ' + nowWords() : 'None of your friends with class times are free right now · ' + nowWords(), card: { k: 'now' }, follow: follow,
      notes: unk > 0 ? [plural(unk, 'friend has', 'friends have') + ' no times I can read, so ' + 'they’re' + ' not counted.'] : [] };
  }

  function friendRowEl(f, sub, free, strip) {
    var row = make('div', 'hawk-fr' + (free ? ' hawk-fr--free' : ''));
    var top = make('div', 'hawk-fr__top');
    var main = button('hawk-fr__main', '', 'Open ' + (f.name || 'friend') + '’s classes');
    main.appendChild(avatar(f, free ? 40 : 32));
    var tx = make('span', 'hawk-fr__tx'); tx.appendChild(make('b', '', firstName(f.name))); tx.appendChild(make('span', '', sub)); main.appendChild(tx);
    tap(main, function () { return openFriend(f); });
    top.appendChild(main);
    if (free) top.appendChild(tap(button('hawk-act', 'Message', 'Message ' + firstName(f.name)), function () { return messageFriend(f); }));
    row.appendChild(top);
    if (strip) row.appendChild(strip);
    return row;
  }
  function cardNow() {
    var free = [], busy = [];
    appFriends().forEach(function (f) { var st = freeState(f); if (st.state === 'open') free.push({ f: f, st: st }); else if (st.state === 'class') busy.push({ f: f, st: st }); });
    if (!free.length && !busy.length) return null;
    var S1 = 1200, span = S1 - DAY_S0, pc = function (m) { return (Math.max(0, Math.min(span, m - DAY_S0)) / span * 100).toFixed(1); };
    var strip = function (f) {
      var bar = make('span', 'hawk-fbar'); bar.setAttribute('aria-hidden', 'true');
      dayItems(friendMeets(f), realDay()).forEach(function (s) { var i = document.createElement('i'); i.style.left = pc(s.s) + '%'; i.style.width = (pc(s.e) - pc(s.s)).toFixed(1) + '%'; bar.appendChild(i); });
      var em = document.createElement('em'); em.style.left = pc(nowMin()) + '%'; bar.appendChild(em);
      return bar;
    };
    var sec = cardFrame('Who is free');
    free.slice(0, 6).forEach(function (x) { sec.appendChild(friendRowEl(x.f, freeLine(x.st), true, strip(x.f))); });
    if (busy.length) { sec.appendChild(kicker('Busy')); busy.slice(0, 4).forEach(function (x) { sec.appendChild(friendRowEl(x.f, freeLine(x.st), false, null)); }); }
    return sec;
  }
  function cardTogether(c) {
    var l = togetherCalc(c.d).filter(function (x) { return !c.f || x.f === c.f; }).slice(0, 6); if (!l.length) return null;
    var sec = cardFrame('Free with you ' + DAY_FULL[c.d]);
    l.forEach(function (x) { sec.appendChild(friendRowEl(x.f, togetherWords(x), true, null)); });
    return sec;
  }
  function cardTogetherWk(c) {
    var f = c.f; if (!f) return null;
    var sec = cardFrame('Free with ' + firstName(f.name));
    sec.appendChild(friendRowEl(f, 'Free when you are, ' + hs(DAY_S0) + '–' + hs(TOGETHER_END), true, null));
    D5.forEach(function (d) {
      var x = togetherCalc(d).filter(function (y) { return y.f === f; })[0];
      var r = make('div', 'hawk-wrow hawk-wrow--static');
      r.appendChild(make('span', 'hawk-wrow__d', DAY3[d]));
      r.appendChild(make('span', 'hawk-wrow__t' + (x ? ' hawk-wrow__t--ok' : ''), x ? togetherWords(x) : 'Not free at the same time'));
      sec.appendChild(r);
    });
    return sec;
  }

  /* ---- professors ---- */
  function evalsOf(p) { try { return (PROFESSORS[p.id] || {}).evals || 0; } catch (_) { return 0; } }
  function profsForCode(code) {
    var by = {}, order = [];
    sectionsOf(code).forEach(function (r) { var p = profOf(r); if (!p) return; var k = p.id || p.raw; if (!by[k]) { by[k] = { p: p, rows: [] }; order.push(k); } by[k].rows.push(r); });
    return order.map(function (k) { return by[k]; }).sort(function (x, y) {
      return ((y.p.rating == null ? -1 : y.p.rating) - (x.p.rating == null ? -1 : x.p.rating)) || (evalsOf(y.p) - evalsOf(x.p));
    });
  }
  var profCourseCache = { n: -1, map: {} };
  function profCourses(id) {
    var n = seatCount();
    if (profCourseCache.n !== n) {
      profCourseCache = { n: n, map: {} };
      try {
        Object.keys(SEAT_SECTIONS || {}).forEach(function (code) {
          var seen = {};
          (SEAT_SECTIONS[code] || []).forEach(function (r) { var p = profOf(r); if (p && p.id && !seen[p.id]) { seen[p.id] = 1; (profCourseCache.map[p.id] = profCourseCache.map[p.id] || []).push(code); } });
        });
      } catch (_) {}
    }
    return (profCourseCache.map[id] || []).slice().sort();
  }
  /* One section as a row, the way a search result is drawn: tap opens the class at that section; the + is the plan chooser. */
  function secDesc(code, row, base) {
    var e = secEntry(code, row), yours = isMine(code, row), cl = [], fit = null;
    if (e.meet && !yours) {
      cl = clashOf(base || planBase('mine'), code, e).map(function (x) { return x.code; });
      if (!cl.length && ((base || planBase('mine')).some(function (x) { return x.meet; }) || cmMeets().length)) fit = '✓ Fits your week';
    }
    return { rich: true, code: e.label, name: e.when, sub: e.prof ? e.prof.name : 'Instructor not assigned',
      chip: yours ? { text: 'yours', tone: 'open' } : seatChip(row), chip2: e.prof ? ratingChip(e.prof.rating) : null,
      clash: cl.length ? cl : null, fit: fit, sec: { code: code, crn: e.crn },
      go: function () { return goSection(code, e.crn, e.label); } };
  }
  function cardProfBig(item, code) {
    var p = item.p, P0 = {}; try { P0 = PROFESSORS[p.id] || {}; } catch (_) {}
    var sec = cardFrame(p.name, 'hawk-card--prof');
    var top = button('hawk-ptop', '', 'Open ' + p.name);
    top.appendChild(profAvatar(p.name, 44));
    var tx = make('span', 'hawk-ptop__tx'); tx.appendChild(make('b', '', p.name));
    var evals = P0.evals || 0, dept = P0.dept || P0.field || '';
    tx.appendChild(make('span', '', [dept, evals ? plural(evals, 'rating') : 'No ratings yet'].filter(Boolean).join(' · ')));
    top.appendChild(tx);
    if (p.rating != null) { var av = make('span', 'hawk-ptop__avg'); av.appendChild(make('b', '', p.rating.toFixed(1))); av.appendChild(make('span', '', 'AVERAGE')); top.appendChild(av); }
    tap(top, function () { return goProfId(p.id, p.name); });
    sec.appendChild(top);
    var tiles = [], courses = p.id ? profCourses(p.id) : [];
    if (evals) tiles.push([String(evals), 'ratings']);
    if (code && item.rows.length) tiles.push([String(item.rows.length), item.rows.length === 1 ? 'section' : 'sections']);
    if (!code && courses.length) tiles.push([String(courses.length), courses.length === 1 ? 'class' : 'classes']);
    if (tiles.length) {
      var tl = make('div', 'hawk-tiles');
      tiles.forEach(function (t) { var d = make('div'); d.appendChild(make('b', '', t[0])); d.appendChild(make('span', '', t[1])); tl.appendChild(d); });
      sec.appendChild(tl);
    }
    if (code && item.rows.length) {
      var base = planBase('mine'), box = make('div', 'hawk-psecs');
      item.rows.slice().sort(function (x, y) { return seatRank({ seat: seatOf(x) }) - seatRank({ seat: seatOf(y) }); }).slice(0, 2).forEach(function (r) { box.appendChild(rowEl(secDesc(code, r, base))); });
      sec.appendChild(box);
    }
    if (!code) {
      var tc = make('div', 'hawk-teach');
      tc.appendChild(kicker(courses.length ? 'Teaching ' + termWord(planLabel()) : 'Not teaching in ' + termWord(planLabel())));
      courses.slice(0, 4).forEach(function (cd) { tc.appendChild(tap(button('hawk-teach__c', cd, 'Open ' + cd), function () { return goClass(cd); })); });
      sec.appendChild(tc);
    }
    return sec;
  }
  function profRowEl(item, code, subText) {
    var p = item.p;
    var b = button('hawk-prow', '', 'Open ' + p.name);
    b.appendChild(profAvatar(p.name, 34));
    var tx = make('span', 'hawk-prow__tx'); tx.appendChild(make('b', '', p.name));
    var sub = subText;
    if (!sub && code && item.rows && item.rows[0]) {
      var best = item.rows.slice().sort(function (x, y) { return seatRank({ seat: seatOf(x) }) - seatRank({ seat: seatOf(y) }); })[0], e = secEntry(code, best);
      sub = (e.no ? 'Section ' + e.no + ' · ' : '') + e.when + ' · ' + seatWords(e);
    }
    if (!sub) { var ev = evalsOf(p); sub = ev ? plural(ev, 'rating') : 'No ratings yet'; }
    tx.appendChild(make('span', '', sub)); b.appendChild(tx);
    b.appendChild(starPill(p.rating));
    return tap(b, function () { return goProfId(p.id, p.name); });
  }
  function cardProfs(c) {
    var wrap = make('div', 'hawk-cards');
    var items = c.items || (c.code ? profsForCode(c.code) : []);
    if (!items.length) return null;
    var big = (c.items && !c.solo) ? null : items[0], rest = big ? items.slice(1) : items;
    if (big) wrap.appendChild(cardProfBig(big, c.code));
    if (rest.length) {
      if (big) wrap.appendChild(kicker('Also teaching ' + c.code));
      var sec = cardFrame(c.label || 'Professors', 'hawk-card--rows');
      rest.forEach(function (it) { sec.appendChild(profRowEl(it, c.code, c.subs && c.subs[it.p.id || it.p.raw])); });
      wrap.appendChild(sec);
    }
    return wrap;
  }
  function ansBest(code, cat) {
    var rows = sectionsOf(code);
    if (!rows.length) return ansClass(code, cat);
    var ps = profsForCode(code), rated = ps.filter(function (x) { return x.p.rating != null; });
    var follow = ['Does ' + code + ' fit my schedule?', 'Who’s in ' + code + '?'];
    if (!ps.length) return { t: 'No professor is assigned to ' + code + ' yet.', card: { k: 'cls', code: code }, follow: follow };
    if (!rated.length) return { t: 'None of the ' + code + ' professors have ratings yet.', card: { k: 'profs', code: code }, follow: follow };
    return { t: ps.length === 1 ? 'Only ' + ps[0].p.name + ' teaches ' + code + '.' : ps[0].p.name + ' — top rated of ' + ps.length + '.', card: { k: 'profs', code: code }, follow: follow };
  }
  function profItem(id) { var p = profCard(id); return { p: { id: id, name: p.name, rating: p.rating, raw: id }, rows: [] }; }
  function ansProf(id) {
    if (!id) return { t: 'I couldn’t find that professor.' };
    var c = profCard(id), cs = profCourses(id);
    return { t: c.rating != null ? c.name + ' · ★ ' + c.rating.toFixed(1) + ' from ' + plural(c.evals, 'rating') + '.' : c.name + ' has no ratings yet.',
      card: { k: 'profs', items: [profItem(id)], solo: true }, follow: cs.length ? ['Best professor for ' + cs[0] + '?'] : [] };
  }
  function ansCompare(a, b) {
    var x = profCard(a), y = profCard(b), rt = function (c) { return c.rating != null ? '★ ' + c.rating.toFixed(1) : 'no ratings yet'; };
    return { t: x.name + ' ' + rt(x) + ' · ' + y.name + ' ' + rt(y), card: { k: 'profs', items: [profItem(a), profItem(b)], label: 'Compare' } };
  }
  /* Your professors: the classes you are in now and the ones you are choosing, ranked by rating. */
  function ansMyProfs(a) {
    var lists = [{ codes: myCodes(), meta: (function () { try { return myClassMeta || {}; } catch (_) { return {}; } })() }];
    if (twoTerms()) { try { var nm = global.nowMine(); lists.push({ codes: nm.classes || [], meta: nm.meta || {} }); } catch (_) {} }
    var got = myProfessors(lists);
    if (!lists.some(function (L) { return L.codes.length; })) return { t: 'You haven’t added classes yet, so there are no professors to rank.', acts: [['Open Schedule', function () { return goPlace('schedule'); }]] };
    if (!got.list.length) return { t: 'I can’t see who teaches your classes yet. Pick your sections in Schedule and I’ll rank them.', acts: [['Open Schedule', function () { return goPlace('schedule'); }]] };
    var asc = a && a.order === 'asc';
    var rated = got.list.filter(function (x) { return x.prof.rating != null; }).sort(function (p, q) { return asc ? p.prof.rating - q.prof.rating : q.prof.rating - p.prof.rating; });
    var all = rated.concat(got.list.filter(function (x) { return x.prof.rating == null; }));
    var subs = {};
    all.forEach(function (x) { subs[x.prof.id || x.prof.raw] = x.codes.join(', '); });
    return { t: 'Your ' + plural(all.length, 'professor') + ', ' + (asc ? 'lowest' : 'best') + ' rated first.', notes: got.unknown.length ? ['No professor on record for ' + got.unknown.join(', ') + '.'] : [],
      card: { k: 'profs', items: all.map(function (x) { return { p: x.prof, rows: [] }; }), subs: subs, label: 'Your professors' } };
  }

  /* ---- classes and sections ---- */
  function ansClass(code, cat) {
    if (!sectionsOf(code).length) {
      return { t: seatsLoaded() ? code + ' isn’t offered in ' + termWord(planLabel()) + '.' : 'Classes are still loading — ask again in a moment.',
        acts: [['Open ' + code, function () { return goClass(code); }]] };
    }
    var fr = friendsIn(code);
    return { t: code + (cat.courses[code] && cat.courses[code] !== code ? ' · ' + cat.courses[code] : '') + (fr.length ? ' · ' + namesWords(fr) + ' ' + (fr.length === 1 ? 'is' : 'are') + ' in it' : ''),
      card: { k: 'cls', code: code, title: cat.courses[code] || code }, follow: ['Best professor for ' + code + '?', 'Does ' + code + ' fit my schedule?'] };
  }
  function friendsIn(code) { return appFriends().filter(function (f) { return f && (f.classes || []).indexOf(code) >= 0; }); }
  function namesWords(list) { return list.slice(0, 2).map(function (f) { return firstName(f.name); }).join(' and ') + (list.length > 2 ? ' +' + (list.length - 2) : ''); }
  function cardClass(c) {
    var code = c.code, rows = sectionsOf(code).slice().sort(function (x, y) {
      return (seatRank({ seat: seatOf(x) }) - seatRank({ seat: seatOf(y) })) || ((profOf(y) && profOf(y).rating != null ? profOf(y).rating : -1) - (profOf(x) && profOf(x).rating != null ? profOf(x).rating : -1));
    });
    if (!rows.length) return null;
    var sec = cardFrame(code, 'hawk-card--class'), fr = friendsIn(code);
    var top = button('hawk-ctop', '', 'Open ' + code);
    top.appendChild(make('span', 'hawk-ctop__code', code)); top.appendChild(make('b', '', c.title || code)); top.appendChild(icon('chev', 16));
    tap(top, function () { return goClass(code); });
    sec.appendChild(top);
    var facts = make('div', 'hawk-facts'), open = 0, anyOpen = false, allFull = true;
    rows.forEach(function (r) { var s = seatOf(r); if (s && s.cls === 'open') { anyOpen = true; if (s.n != null) open += s.n; } if (!(s && s.cls === 'full')) allFull = false; });
    facts.appendChild(pill(plural(rows.length, 'section')));
    if (anyOpen) facts.appendChild(pill(open ? open + ' open seats' : 'Open sections', 'ok')); else if (allFull) facts.appendChild(pill('Every section is full', 'bad'));
    if (fr.length) facts.appendChild(pill(plural(fr.length, 'friend')));
    sec.appendChild(facts);
    var base = planBase('mine'), box = make('div', 'hawk-psecs');
    rows.slice(0, 3).forEach(function (r) { box.appendChild(rowEl(secDesc(code, r, base))); });
    sec.appendChild(box);
    if (rows.length > 3) sec.appendChild(tap(button('hawk-more', 'All ' + rows.length + ' sections ›'), function () { return goClass(code); }));
    return sec;
  }
  /* Search results: the sections that answer the question, with what was understood shown as chips. */
  function searchChips(a) {
    var out = [];
    if (a.course) out.push(a.course); else if (a.subject) out.push(a.subject);
    if (a.open_only === true) out.push('Open seats');
    if (a.days && a.days.length) out.push(a.days.map(function (d) { return DAY3[d] || d; }).join('/') + ' only');
    if (a.start_after) out.push('After ' + clock12(toMin(a.start_after)));
    if (a.end_before) out.push('Done by ' + clock12(toMin(a.end_before)));
    if (a.at_time) out.push('Around ' + clock12(toMin(a.at_time)));
    if (a.component) out.push({ LAB: 'Labs', LEC: 'Lectures', ACT: 'Activities', SEM: 'Seminars' }[String(a.component).toUpperCase().slice(0, 3)] || a.component);
    if (a.instruction_mode) out.push({ async: 'Online', sync_online: 'Online, live', in_person: 'In person', hybrid: 'Hybrid' }[a.instruction_mode] || a.instruction_mode);
    if (a.fits_my_schedule) out.push('Fits my week');
    if (a.sort === 'rating') out.push('Best-rated first'); else if (a.sort === 'seats') out.push('Most seats first');
    return out;
  }
  function ansSearch(result, cat) {
    var a = result.args || {};
    if (a.ge_area || a.scope || (!a.course && !a.subject)) return null;      // GE and requirement searches keep the planner's rows
    if (a.course && !wantsSections(a)) return ansClass(a.course, cat);
    if (!a.course && !wantsSections(a)) return null;                          // a whole subject: the course list
    var out = rowsFor(result, cat);
    if (out.needsAnchor || !out.rows.length) return null;
    lastSearch = a;
    var near = out.rows.some(function (r) { return r.near; });
    return { t: near ? 'Nothing matches all of that — these are the closest.' : plural(out.rows.length, 'section') + ' ' + (out.rows.length === 1 ? 'matches' : 'match') + '.',
      notes: out.unread.length ? ['I cannot filter by ' + (out.unread.length === 1 ? out.unread[0] : out.unread.slice(0, -1).join(', ') + ' or ' + out.unread[out.unread.length - 1]) + ' yet.'] : [],
      card: { k: 'rows', rows: out.rows, chips: searchChips(a) } };
  }
  function cardRows(c) {
    var wrap = make('div', 'hawk-cards');
    if (c.chips && c.chips.length) { var f = make('div', 'hawk-facts'); c.chips.forEach(function (t) { f.appendChild(pill(t, 'blue')); }); wrap.appendChild(f); }
    var sec = cardFrame(c.label || 'Results', 'hawk-card--rows');
    c.rows.forEach(function (r) { sec.appendChild(rowEl(r)); });
    wrap.appendChild(sec);
    return wrap;
  }

  /* ---- prerequisites ---- */
  function canonOf(x) { try { return (has('canonCode') ? global.canonCode(x) : x) || x; } catch (_) { return x; } }
  function prereqCheck(code) {
    var rec = null; try { rec = has('coursePrereqs') ? global.coursePrereqs(code) : null; } catch (_) {}
    var req = rec && rec.req;
    if (!req || !req.length) return { k: 'none' };
    var done = [], now = [];
    try { done = has('completedCodes') ? global.completedCodes() : []; now = has('enrolledNowCodes') ? global.enrolledNowCodes() : myCodes(); } catch (_) {}
    var st = null; try { st = has('prereqStatus') ? global.prereqStatus(code, done, [], now) : null; } catch (_) {}
    if (!st) return { k: 'unknown' };
    /* the phone's rule: no past classes and no waivers on record, and the answer would be "unmet" - which is not information.
       (A class you are taking now is mirrored into the record, so it does not count as a past class.) */
    var cur = {}; now.forEach(function (x) { cur[canonOf(x)] = 1; });
    var past = done.filter(function (x) { return !cur[canonOf(x)]; }).length, wav = 0;
    try { wav = has('waivedCodes') ? (global.waivedCodes() || []).length : 0; } catch (_) {}
    if (!past && !wav && (st.state === 'unmet' || st.state === 'concurrent')) return { k: 'norecord', st: st, req: req };
    return { k: st.state === 'met' ? 'met' : st.state, st: st, req: req };
  }
  function ansPrereq(code, cat) {
    var r = prereqCheck(code), follow = ['Does ' + code + ' fit my schedule?'];
    var gl = function (g) { return groupLabel(g); };
    if (r.k === 'none') return { t: 'The catalog lists no prerequisite for ' + code + '.', follow: follow };
    if (r.k === 'unknown') return { t: 'I can’t read prerequisites in this build.' };
    var card = { k: 'prereq', code: code, title: cat.courses[code] || code };
    if (r.k === 'met') return { t: 'Yes — you’ve got the prerequisites for ' + code + '.', card: card, follow: follow };
    if (r.k === 'norecord') return { t: 'I can’t tell yet — nothing’s logged in your past classes.', card: card, acts: [['Open Past classes', function () { return goPlace('past classes'); }]] };
    if (r.k === 'unmet') { var n = r.st.missing.length; return { t: 'Not yet — ' + (n === 1 ? 'one class' : n + ' classes') + ' to go: ' + r.st.missing.map(gl).join(', ') + '.', card: card }; }
    if (r.k === 'inprogress') return { t: 'You’re taking the prerequisite for ' + code + ' now.', card: card };
    if (r.k === 'concurrent') return { t: code + ' needs ' + r.st.concurrent.map(gl).join(', ') + ' in the same term.', card: card };
    return { t: 'I can’t check that one against your record right now.' };
  }
  function cardPrereq(c) {
    var code = c.code, r = prereqCheck(code); if (!r.req) return null;
    var unknown = r.k === 'norecord';
    var done = {}, now = {}, canon = canonOf;
    try { global.completedCodes().forEach(function (x) { done[canon(x)] = 1; }); } catch (_) {}
    try { global.enrolledNowCodes().forEach(function (x) { now[canon(x)] = 1; }); } catch (_) {}
    var ok = 0, n = r.req.length;
    var sec = cardFrame('Prerequisites for ' + code, 'hawk-card--prereq');
    var top = button('hawk-ctop', '', 'Open ' + code);
    top.appendChild(make('span', 'hawk-ctop__code', code)); top.appendChild(make('b', '', c.title || code));
    var chipSlot = make('span', 'hawk-ctop__chip'); top.appendChild(chipSlot);
    tap(top, function () { return goClass(code); });
    sec.appendChild(top);
    var bar = make('div', 'hawk-pbar'); bar.setAttribute('aria-hidden', 'true'); var fill = document.createElement('i'); bar.appendChild(fill); sec.appendChild(bar);
    r.req.forEach(function (grp) {
      var g = dedupeGroup(grp), dn = g.filter(function (x) { return done[canon(x)]; })[0], nw = !dn && g.filter(function (x) { return now[canon(x)]; })[0];
      var row = make('div', 'hawk-q'), dot, name = make('span', 'hawk-q__tx'), sub;
      if (dn && !unknown) { ok++; dot = make('span', 'hawk-q__dot hawk-q__dot--ok', '✓'); name.appendChild(make('b', '', dn)); sub = 'On your record'; }
      else if (nw && !unknown) { ok++; dot = make('span', 'hawk-q__dot hawk-q__dot--now', '◐'); name.appendChild(make('b', '', nw)); sub = 'Taking it now'; }
      else {
        var conc = r.st.concurrent.some(function (x) { return dedupeGroup(x).join() === g.join(); });
        var offered = g.filter(function (x) { return sectionsOf(x).length; });
        dot = make('span', 'hawk-q__dot ' + (unknown ? 'hawk-q__dot--unk' : 'hawk-q__dot--need'), unknown ? '?' : '');
        name.appendChild(make('b', '', g.join(' or ')));
        sub = conc ? 'Take it the same term' : offered.length ? (offered.length === g.length ? 'Offered ' + termWord(planLabel()) : offered.join(', ') + ' offered ' + termWord(planLabel())) : (g.length > 1 ? 'Neither is' : 'Not') + ' offered ' + termWord(planLabel());
      }
      dot.setAttribute('aria-hidden', 'true'); name.appendChild(make('span', '', sub));
      var links = make('span', 'hawk-q__links');
      g.forEach(function (x) { links.appendChild(tap(button('hawk-q__go', x + ' ›', 'Open ' + x), function () { return goClass(x); })); });
      name.appendChild(links);
      row.appendChild(dot); row.appendChild(name); sec.appendChild(row);
    });
    chipSlot.appendChild(unknown ? pill('Can’t check') : pill(ok + ' of ' + n, ok === n ? 'ok' : 'bad'));
    fill.style.width = unknown ? '0%' : Math.round(100 * ok / n) + '%';
    sec.appendChild(tap(button('hawk-btn hawk-btn--go hawk-btn--wide', 'Show in Planner'), function () { return goPlace('planner'); }));
    return sec;
  }
  function dedupeGroup(grp) {
    try { if (has('pqDedupeGroup')) return global.pqDedupeGroup(grp); } catch (_) {}
    var seen = {}, out = []; (grp || []).forEach(function (x) { if (x && !seen[x]) { seen[x] = 1; out.push(x); } }); return out;
  }

  /* ---- the registration game plan (Plans A-C, the term you are choosing in) ---- */
  function askBuild() {
    render('build me a 15 unit schedule', { prerouted: true, confident: true, in_scope: true, tool: 'build_term', args: { units: 15 }, corrections: [], leftovers: [], signals: [] }, buildCatalog());
    return 'Building a term';
  }
  function ansGamePlan(want) {
    var P = global.TCPlans;
    if (!P || !P.gamePlan) return { t: 'Plans aren’t in this build yet.' };
    var full = P.slots.filter(function (s) { return P.get(s).sections.length; });
    var openPlans = ['Open Plans', function () { return goPlace('watchlist'); }];
    if (!full.length) return { t: 'You don’t have a plan yet. Build a term, save it as Plan A, and I’ll put it in the order to register.', acts: [['Build a term', askBuild], openPlans] };
    var asked = /^[ABC]$/.test(String(want || '')) ? String(want) : null;
    if (asked && full.indexOf(asked) < 0) return { t: 'Plan ' + asked + ' is empty. Add sections from Explore and I’ll order them.', acts: [['Open Plans', function () { return goPlace('watchlist'); }]] };
    var slot = asked || (full.indexOf(P.cur()) >= 0 ? P.cur() : full[0]);
    var g = P.gamePlan(slot);
    if (!g.steps.length) return { t: 'Plan ' + slot + ' has no sections I can read yet.', acts: [openPlans] };
    var st = g.steps[0], why = st.reasons.length ? lower1(st.reasons[0].t) : '';
    return { t: 'Start with ' + st.i.label + (why ? ' — ' + why : '') + '.', card: { k: 'game', P: slot },
      follow: full.filter(function (x) { return x !== slot; }).slice(0, 1).map(function (x) { return 'My game plan for Plan ' + x; }) };
  }
  function cardGame(c) {
    var P = global.TCPlans, g = P.gamePlan(c.P); if (!g.steps.length) return null;
    var conf = {}; try { conf = global.PROFESSIFY_CONFIG || {}; } catch (_) {}
    var open = regDate(conf.REGISTRATION_OPENS);
    var sec = cardFrame('Plan ' + c.P + ' game plan', 'hawk-card--game');
    sec.appendChild(cardHead('', 'Open ›', function () { P.openGamePlan(c.P); return 'Opened the game plan'; },
      [make('span', 'hawk-plan hawk-plan--' + c.P, 'Plan ' + c.P),
       make('span', 'hawk-ch__s', plural(g.steps.length, 'class', 'classes') + (g.preview ? ' · preview on ' + g.termLabel + ' sections' : (open ? ' · registration opens ' + open.toLocaleDateString([], { month: 'short', day: 'numeric' }) : '')))]));
    g.steps.slice(0, 8).forEach(function (st, ix) {
      var i = st.i, bk = st.backup, seat = i.seat || {};
      var hot = (st.reasons[0] && st.reasons[0].hot) || seat.cls === 'full' || seat.cls === 'wait';
      var tone = hot ? 'hot' : (seat.cls === 'unknown' || seat.unknown || !st.seatLine ? 'unk' : (seat.n != null && seat.n <= 5 ? 'hot' : 'ok'));
      var pct = (seat.cls === 'open' && seat.n != null && i.cap) ? Math.max(4, Math.round(100 * (i.cap - seat.n) / i.cap)) : (hot ? 100 : null);
      var row = button('hawk-grow', '', 'Open ' + i.label + ', number ' + (ix + 1));
      row.appendChild(make('span', 'hawk-grow__n hawk-grow__n--' + tone, String(ix + 1)));
      var tx = make('span', 'hawk-grow__tx');
      var h = make('span', 'hawk-grow__h'); h.appendChild(make('b', '', i.label)); if (i.when) h.appendChild(make('span', '', i.when)); tx.appendChild(h);
      if (st.reasons.length) tx.appendChild(make('span', 'hawk-grow__why', st.reasons[0].t + (g.inRound1 && st.round === 2 ? ' · Round 2' : '')));
      if (st.seatLine || pct != null) {
        var sb = make('span', 'hawk-grow__bar'), trk = make('span'); trk.setAttribute('aria-hidden', 'true');
        if (pct != null) { var fi = document.createElement('i'); fi.className = 'hawk-grow__fill--' + tone; fi.style.width = pct + '%'; trk.appendChild(fi); }
        sb.appendChild(trk); sb.appendChild(make('span', 'hawk-grow__seat hawk-grow__seat--' + tone, st.seatLine || '')); tx.appendChild(sb);
      }
      tx.appendChild(make('span', 'hawk-grow__bk', bk && bk.best ? 'Backup -' + bk.best.no + ' · ' + [bk.best.when, bk.best.prof].filter(Boolean).join(' · ') + (bk.needsLab ? ' · pick a lab too' : '') : 'No backup fits — waitlist if it fills'));
      row.appendChild(tx);
      sec.appendChild(tap(row, function () { return goSection(i.code, i.crn, i.label); }));
    });
    if (g.steps.length > 8) sec.appendChild(make('div', 'hawk-count', (g.steps.length - 8) + ' more, lower risk'));
    if (g.inRound1 && g.split && g.unitsKnown) sec.appendChild(make('div', 'hawk-count', 'Round 1 caps you at 16 units — the rest waits for Round 2.'));
    return sec;
  }

  /* ---- your clashes (the week you are in) ---- */
  function clashIdx(meets) {
    var bad = {};
    for (var i = 0; i < meets.length; i += 1) {
      for (var j = i + 1; j < meets.length; j += 1) {
        var a = meets[i], b = meets[j];
        if (!a.meet || !b.meet || (a.cm && b.cm) || (!a.cm && !b.cm && a.code === b.code)) continue;
        if (overlaps(a.meet, b.meet)) { bad[i] = 1; bad[j] = 1; }
      }
    }
    return bad;
  }
  function ansConflicts() {
    var meets = nowMeetsAll(); if (!meets.length) return emptyWeek();
    var bad = clashIdx(meets), codes = {};
    Object.keys(bad).forEach(function (i) { if (!meets[i].cm) codes[meets[i].code] = 1; });
    var n = Object.keys(codes).length;
    if (!Object.keys(bad).length) return { t: 'No time clashes in your ' + termWord(nowLabel()) + ' classes.', notes: unplacedNotes(meets) };
    return { t: (n ? plural(n, 'of your classes overlaps', 'of your classes overlap') : 'Something in your week overlaps') + ' — they’re outlined in red.', card: { k: 'mine' }, notes: unplacedNotes(meets) };
  }
  function cardMine() {
    var meets = nowMeetsAll().filter(function (m) { return m && m.meet; }); if (!meets.length) return null;
    var bad = clashIdx(meets), blocks = [];
    meets.forEach(function (m, i) {
      blocks.push({ code: String(m.code || ''), days: m.meet.days, s: m.meet.start, e: m.meet.end, cmId: m.cm === 'mine' ? String(m.id || '') : '',
        cls: (m.cm ? 'hawk-wk__blk--cm' : '') + (bad[i] ? ' hawk-wk__blk--clash' : ''), go: m.cm ? null : (function (cd) { return function () { return goNowClass(cd); }; })(String(m.code || '')) });
    });
    var sec = cardFrame('Your classes');
    sec.appendChild(cardHead('', 'Week ›', openMyWeek, [make('span', 'hawk-plan hawk-plan--mine', twoTerms() && nowLabel() ? nowLabel() : 'My classes')]));
    sec.appendChild(weekGridEl(blocks, { h: 220 }));
    return sec;
  }

  /* ---- the answer, drawn ---- */
  function cardEl(c) {
    try {
      switch (c.k) {
        case 'fit': return cardFit(c);
        case 'day': return cardDay(c);
        case 'week': return cardWeek(c);
        case 'together': return cardTogether(c);
        case 'togetherWk': return cardTogetherWk(c);
        case 'now': return cardNow();
        case 'profs': return cardProfs(c);
        case 'cls': return cardClass(c);
        case 'rows': return cardRows(c);
        case 'prereq': return cardPrereq(c);
        case 'game': return cardGame(c);
        case 'mine': return cardMine();
      }
    } catch (_) {}
    return null;
  }
  function actsEl(acts) {
    var d = make('div', 'hawk-acts');
    acts.forEach(function (a, i) { d.appendChild(tap(button('hawk-act' + (i === 0 ? ' hawk-act--primary' : ''), a[0]), a[1])); });
    return d;
  }
  function followEl(list) {
    var d = make('div', 'hawk-follow');
    list.forEach(function (q) {
      var b = button('hawk-fq', q); b.addEventListener('click', function () { answer(q); });
      d.appendChild(b);
    });
    return d;
  }
  function renderAnswer(turn, ans) {
    turn.appendChild(make('div', 'hawk-note', ans.t));
    (ans.notes || []).forEach(function (n) { bubbleOf(turn).appendChild(make('div', 'hawk-note', n)); });
    if (ans.acts && ans.acts.length) bubbleOf(turn).appendChild(actsEl(ans.acts));
    if (ans.card) { var el = cardEl(ans.card); if (el) turn.appendChild(el); }
    if (ans.follow && ans.follow.length) turn.appendChild(followEl(ans.follow));
  }

  /* ---- what the router or the model named, answered as a card. null = this tool keeps its rows. ---- */
  function weekday(d) { return D5.indexOf(d) >= 0; }
  function answerFromTool(result, cat) {
    var a = result.args || {};
    switch (result.tool) {
      case 'my_free': { var ds = (a.days || []).filter(weekday); if (!ds.length && (a.rel === 'today' || a.rel === 'tomorrow')) ds = [a.rel === 'today' ? todayKey() : tomorrowKey()]; return ds.length === 1 ? ansDay(ds[0], 'free') : ansFreeWeek(ds); }
      case 'my_day': {
        var d = a.rel === 'tomorrow' ? tomorrowKey() : (a.days && a.days.filter(weekday)[0]) || todayKey();
        return ansDay(d, 'day');
      }
      case 'my_conflicts': return ansConflicts();
      case 'friends_free_now': return ansNow();
      case 'free_with_friends': {
        var dd = a.rel === 'today' ? todayKey() : a.rel === 'tomorrow' ? tomorrowKey() : (a.days || []).filter(weekday)[0] || null;
        if (a.friend) {
          var f = friendByName(a.friend);
          if (!f) return { t: 'I couldn’t find one friend named ' + a.friend + '.', acts: [['Open Friends', function () { return goPlace('friends'); }]] };
          return a.week ? ansTogetherWith(f, null) : (!dd ? ansFriendNow(f) : ansTogetherWith(f, dd));
        }
        return dd ? ansTogether(dd) : ansNow();
      }
      case 'best_professor': return a.course ? ansBest(a.course, cat) : { t: 'I couldn’t tell which class.' };
      case 'professor_stats': { var id = profIdByName(a.name); return id ? ansProf(id) : { t: 'I couldn’t find “' + (a.name || '') + '”.' }; }
      case 'compare_professors': {
        var ia = profIdByName(a.a), ib = profIdByName(a.b);
        return ia && ib ? ansCompare(ia, ib) : { t: 'I couldn’t find both of those professors.' };
      }
      case 'my_professors': return ansMyProfs(a);
      case 'fits_plan': return a.course ? ansFit(a.course, a.plan) : { t: 'I couldn’t tell which class.' };
      case 'prereqs': return a.course ? ansPrereq(a.course, cat) : null;
      case 'game_plan': return ansGamePlan(a.plan);
      case 'open_class': return a.course ? ansClass(a.course, cat) : null;
      case 'search_sections': return ansSearch(result, cat);
    }
    return null;
  }

  /* ---- questions answered here before the model is asked: the shape is unmistakable and the answer is a lookup
     (the phone's chIntent, 2026-10-08). They also work signed out and offline, and the chips under a card are asked
     through them, so a follow-up never needs a round trip. ---- */
  var CH_CODE = /\b([a-z&]{2,5})\s*-?\s*(\d{3,4}[a-z]?)\b/i;
  var CH_NOTNAME = /^(me|my|i|im|you|u|anyone|anybody|someone|somebody|friends?|everyone|everybody|them|him|her|us|a|an|the|class|classes|lunch|food|today|tomorrow|now|people|good|open|seats)$/;
  var CH_NOWQ = /\b(now|rn|right now|currently|at the moment)\b|^(is|are) [a-z][a-z'-]* free\??$/;
  var CH_LATERQ = /\d|\b(when i'?m free|when i am|at|after|before|around|between|until|till|tonight|later|noon|morning|afternoon|evening|night|weekend|next|sat(urday)?|sun(day)?)\b/;
  var DAYWORD = { mon: 'Mo', tue: 'Tu', wed: 'We', thu: 'Th', fri: 'Fr' };
  var DAYCOMBO = { mtwrf: ['Mo', 'Tu', 'We', 'Th', 'Fr'], mwf: ['Mo', 'We', 'Fr'], mw: ['Mo', 'We'], tth: ['Tu', 'Th'], tuth: ['Tu', 'Th'], tr: ['Tu', 'Th'] };
  function daysIn(t) {
    var s = String(t), hits = [], m, re1 = /\b(mon(?:day)?|tues?(?:day)?|wed(?:nesday|s)?|thu(?:rs?)?(?:day)?|fri(?:day)?)\b/g, re2 = /\b(mtwrf|mwf|mw|tth|tuth|tr)\b/g;
    while ((m = re1.exec(s))) hits.push([m.index, [DAYWORD[m[1].slice(0, 3)]]]);
    while ((m = re2.exec(s))) hits.push([m.index, DAYCOMBO[m[1]]]);
    hits.sort(function (x, y) { return x[0] - y[0]; });
    var out = []; hits.forEach(function (h) { h[1].forEach(function (d) { out.push(d); }); });
    return out;
  }
  function laterQ(t) { return CH_LATERQ.test(t.replace(/\bat the moment\b/g, '')); }
  function namedFriend(t) {
    var pats = [/\b([a-z][a-z'-]+) and (?:i|me)\b/, /\b(?:me|i) and ([a-z][a-z'-]+)/, /\bwith ([a-z][a-z'-]+)/, /\b(?:is|when is|when's) ([a-z][a-z'-]+) free\b/];
    for (var i = 0; i < pats.length; i += 1) {
      var m = t.match(pats[i]), w = m && m[1].replace(/'s$/, '');
      if (w && !CH_NOTNAME.test(w) && !daysIn(w).length) return w;
    }
    return null;
  }
  function dayOfQ(t) {
    var ds = daysIn(t); if (ds.length) return ds[ds.length - 1];
    if (/\btomorrow\b/.test(t)) return tomorrowKey();
    return todayKey();
  }
  var NAME_STOP = /^(best|professors?|teachers?|instructors?|which|should|easiest|highest|better|good|class|section|rated|rating|for|the|who|and|can|get|fit|any|are|how|why|one|two|day|you|her|his|our|top|was|has|had|not|but|all|out|its|did|see|new|way|use|now|plan|schedule|week|classes|prof|profs|teacher|with|this|that|does|work|works|clash|clashes|conflict|room|mine|from|about|take|taking)$/;
  function namesAProfessor(t, cat) {
    var words = t.replace(CH_CODE, ' ').replace(/[^a-z\s'-]/g, ' ').split(/\s+/).filter(function (w) { return w.length > 2 && !NAME_STOP.test(w); });
    if (!words.length) return false;
    var names = (cat.professors || []).map(function (n) { return String(n).toLowerCase().split(/[\s,]+/); });
    return words.some(function (w) { return names.some(function (parts) { return parts.indexOf(w) >= 0; }); });
  }
  function mk(tool, args) {
    return { prerouted: true, confident: true, in_scope: true, local: true, tool: tool, args: args || {}, corrections: [], leftovers: [], signals: ['local'] };
  }
  function localIntent(q, cat) {
    var t = String(q || '').toLowerCase().replace(/[’‘]/g, "'"), m = t.match(CH_CODE), code = null;
    if (m) { var c0 = (m[1] + ' ' + m[2]).toUpperCase(); if (cat.courses[c0] || sectionsOf(c0).length) code = c0; }
    if (code && !namesAProfessor(t, cat) && (/\b(best|top|highest|good|better|which|who should)\b[\s\S]*\b(prof|profs|professor|professors|teacher|teachers|instructor)\b|\b(prof|professor|teacher)s?\b[\s\S]*\b(best|top|good)\b/.test(t))) return mk('best_professor', { course: code });
    if (code && /\b(fit|fits|work with|works with|clash|clashes|conflict|go with|room for)\b/.test(t) && /\bplan\s*[abc]\b|\bmy (plan|schedule|week|classes)\b|\bplan\b/.test(t)) {
      var p = t.match(/\bplan\s*([abc])\b/);
      return mk('fits_plan', { course: code, plan: p ? p[1].toUpperCase() : /\bmy (schedule|week|classes)\b/.test(t) ? 'mine' : curSlot() });
    }
    var nm = !code && namedFriend(t);
    if (nm && /\b(free|overlap|gap|break|lunch|meet up|hang out)\b/.test(t)) {
      var f = friendByName(nm), ds = []; daysIn(t).forEach(function (d) { if (ds.indexOf(d) < 0) ds.push(d); });
      if (!f || ds.length > 1 || laterQ(t)) return null;
      if (!ds.length && CH_NOWQ.test(t)) return mk('free_with_friends', { friend: f.name });
      return ds.length || /\b(today|tomorrow)\b/.test(t) ? mk('free_with_friends', { friend: f.name, days: [dayOfQ(t)] }) : mk('free_with_friends', { friend: f.name, week: true });
    }
    if (/\bfree\b[\s\S]*\b(with me|same time|as me|together)\b|\bboth free\b|\bfree together\b/.test(t)) return mk('free_with_friends', { days: [dayOfQ(t)] });
    /* "who's free?" is about friends. A day -> free when you are that day; otherwise right now. A time or a person goes on. */
    if (/^(so |ok |okay |hey |yo )?(who'?s|who is|who are|is anyone|anyone|is anybody|anybody|are any of my friends|any friends|which friends are|which of my friends are)( (even|actually|currently))? free\b/.test(t) && !/\d|\bwith\b|\band (i|me)\b/.test(t) && !laterQ(t)) {
      return daysIn(t).length || /\b(today|tomorrow)\b/.test(t) ? mk('free_with_friends', { days: [dayOfQ(t)] }) : mk('friends_free_now', {});
    }
    if (/\b(when am i free|when i'?m free|my free time|am i free|free time)\b/.test(t) && !/\bright now\b/.test(t) && !/\b(friends?|anyone|anybody|who'?s?|someone)( are| is)? free\b/.test(t)) {
      var days = []; daysIn(t).forEach(function (d) { if (days.indexOf(d) < 0) days.push(d); });
      if (days.length === 1 || /\b(today|tomorrow)\b/.test(t)) return mk('my_free', { days: [days[0] || dayOfQ(t)] });
      return mk('my_free', { days: days });
    }
    /* a bare day ("Monday", "on tuesday?") is "what do I have that day" */
    /* ("what about tuesday" right after a section search narrows THAT search — followUp() — so it is left to the router) */
    if (/^(on |for |what about |how about |and )?(mon|tue|wed|thu|fri)[a-z]*\??$/.test(t) && daysIn(t).length === 1 && !(lastSearch && /^(what about|how about|and) /.test(t))) return mk('my_day', { days: daysIn(t) });
    /* the starter "What's my day look like?" and its neighbours */
    if (!code && /\b(my day|next class|what do i have (today|tomorrow|on (mon|tue|wed|thu|fri)\w*)|what'?s on (today|tomorrow)|(my )?(classes|schedule) (today|tomorrow))\b/.test(t) && !laterQ(t.replace(/\b(today|tomorrow|next class)\b/g, ''))) return mk('my_day', { days: [dayOfQ(t)] });
    return null;
  }
'''
FRAME = r'''  /* ===============================================================================================
     THE CHAT (website-champ-cards, 2026-10-15). Champ is a conversation now, the phone's way: the question is a blue
     bubble on the right; Champ's reply is a bubble beside Champ's face; a card hangs under it; the follow-up questions sit
     under the newest answer. Every turn stays above the next one until the student clears the chat (the trash can).

     The older renderers all write into "the turn" (notes, rows, reading lines, alternatives). Rather than rewrite each,
     the turn routes what they append: a note goes into Champ's bubble, a row or a section goes into one card of rows,
     and everything else is laid under them as it always was. So a tool that has no card of its own still reads as chat.
     =============================================================================================== */
  var MAX_TURNS = 24;               // the oldest turns drop off the top; a chat is not a log
  var clickTurn = null;             // the turn whose row is being tapped: a re-render of the same question replaces it

  function newTurn(q) {
    var turn = make('div', 'hawk-turn');
    var said = make('div', 'hawk-said');
    said.appendChild(make('span', 'hawk-said__q', q));
    turn.appendChild(said);
    var bot = null, rows = null, put = Node.prototype.appendChild;
    function bubble() {
      if (!bot) {
        bot = make('div', 'hawk-bot');
        var av = make('span', 'hawk-bot__av'); av.setAttribute('aria-hidden', 'true');
        bot.appendChild(av); bot.appendChild(make('div', 'hawk-bubble'));
        turn.insertBefore(bot, said.nextSibling);
      }
      return bot.lastChild;
    }
    turn._bubble = bubble;
    turn.appendChild = function (n) {
      var c = n && typeof n.className === 'string' ? n.className : '';
      if (/(^|\s)hawk-note(\s|$)/.test(c) && !rows) return put.call(bubble(), n);
      if (/(^|\s)hawk-(row|sec)(\s|$)/.test(c)) {
        if (!rows) { rows = cardFrame('Results', 'hawk-card--rows'); put.call(turn, rows); }
        return put.call(rows, n);
      }
      return put.call(turn, n);
    };
    return turn;
  }
  function bubbleOf(turn) { return turn && turn._bubble ? turn._bubble() : turn; }

  function turnsIn() { return Array.prototype.slice.call(els.log.querySelectorAll(':scope > .hawk-turn')); }
  function place(turn, replace) {
    var hint = els.log.querySelector('.hawk-hint'); if (hint) hint.remove();
    if (replace && replace.parentNode === els.log) els.log.replaceChild(turn, replace); else els.log.appendChild(turn);
    var all = turnsIn();
    /* only the newest answer offers follow-ups and "Not it?" — an older one is history */
    all.forEach(function (t, i) {
      if (i === all.length - 1) return;
      Array.prototype.forEach.call(t.querySelectorAll(':scope > .hawk-follow, :scope > .hawk-notit'), function (n) { n.remove(); });
    });
    while (all.length > MAX_TURNS) all.shift().remove();
    var log = els.log;
    /* a short answer sits at the bottom; one taller than the sheet starts at its question, so the student reads it from the top */
    try {
      if (turn.offsetHeight + 24 > log.clientHeight) log.scrollTop += turn.getBoundingClientRect().top - log.getBoundingClientRect().top - 8;
      else log.scrollTop = log.scrollHeight;
    } catch (_) {}
  }
  function clearChat() {
    els.log.textContent = '';
    lastSearch = null; lastBuild = null; readings = { local: null, model: null };
    els.log.appendChild(hintEl());
    stamp(); syncEmpty();
    try { els.input.focus(); } catch (_) {}
  }

'''

# ---------------------------------------------------------------- 1. the chat frame
js = one(js, "  function render(q, result, cat) {\n    if (result.tool !== 'build_term') lastBuild = null;\n\n    els.log.textContent = '';\n    var turn = make('div', 'hawk-turn');\n\n    var said = make('div', 'hawk-said');\n    said.appendChild(make('span', 'hawk-said__q', q));\n",
FRAME + """  function render(q, result, cat, replaceTurn) {
    if (result.tool !== 'build_term') lastBuild = null;
    /* A row that re-asks the same question (Loosened it, Here's that instead) replaces its own turn rather than stacking. */
    if (!replaceTurn && clickTurn && clickTurn.isConnected) {
      var cq = clickTurn.querySelector('.hawk-said__q');
      if (cq && cq.textContent === q) replaceTurn = clickTurn;
    }
    var turn = newTurn(q);
    var said = turn.querySelector('.hawk-said');
""")
js = one(js, "    if (result.viaModel) said.appendChild(make('span', 'hawk-fix hawk-fix--ai', 'AI'));\n    turn.appendChild(said);\n\n    if (result.refused) {",
            "    if (result.viaModel) said.appendChild(make('span', 'hawk-fix hawk-fix--ai', 'AI'));\n\n    if (result.refused) {")
js = one(js, "    els.log.appendChild(turn);\n    stamp();\n    explainTurn(q, turn);\n  }",
            "    place(turn, replaceTurn);\n    stamp();\n    explainTurn(q, turn);\n  }")
js = swap(js, "  function renderThinking(q) {\n    els.log.textContent = '';", "    return turn;\n  }\n",
"""  function renderThinking(q) {
    var turn = newTurn(q);
    turn.appendChild(make('div', 'hawk-note hawk-thinking', 'Working that out…'));
    place(turn);
    stamp();
    return turn;
  }
""")
js = swap(js, "  function answer(q) {\n    var cat = buildCatalog();", "      render(q, pickAnswer(viaModel, result), cat);\n    });\n  }\n",
"""  function answer(q) {
    var cat = buildCatalog();
    /* The shapes that are a lookup (free time, my day, who is free, does X fit, best professor for X) are answered here, in the
       browser, before the router or the model is asked: they work offline and signed out, and the chips under a card use them. */
    var near = localIntent(q, cat);
    if (near) { readings = { local: near, model: null }; render(q, near, cat); return; }
    var result = R.route(q, cat);
    var fu = buildFollowUp(q, result) || followUp(result);
    if (fu) result = fu;

    if (skipsModel(result) || !result.in_scope || !aiUrl()) {
      readings = { local: result, model: null };
      render(q, result, cat);
      return;
    }
    var thinking = renderThinking(q);
    askModel(q).then(function (viaModel) {
      if (!thinking.isConnected) return;            // they cleared the chat meanwhile
      readings = { local: result, model: viaModel };
      render(q, pickAnswer(viaModel, result), cat, thinking);
    });
  }
""")
js = one(js, "    if (result.refused || result.followUp) return true;", "    if (result.refused || result.followUp || result.local) return true;")

# ---------------------------------------------------------------- 2. rows: a fit line, and the + that opens the plan chooser
js = one(js, "        'clashes with ' + r.clash.join(', ')));\n    }\n    row.appendChild(main);",
             "        'clashes with ' + r.clash.join(', ')));\n    }\n    if (r.fit && !r.clash) main.appendChild(make('span', 'hawk-row__fit', r.fit));\n    row.appendChild(main);")
js = swap(js, "    row.addEventListener('click', function () {\n      var went = r.go();", "    return row;\n  }\n",
"""    row.addEventListener('click', function () {
      /* The box stays open and says where it sent you, because the page behind has just changed underneath something the
         student is still looking at. Without this line the app silently becomes a different screen and only the lucky notice. */
      clickTurn = row.closest('.hawk-turn');
      var went;
      try { went = r.go(); } finally { clickTurn = null; }
      showWent(row, went);
    });
    if (!r.sec) return row;
    /* A section row: tapping the row opens the class at that section; the + beside it is the site's own add-to-plan flow
       (Plan A / B / C, and Replace / Keep both on a clash). Champ adds nothing itself. */
    var wrap = make('div', 'hawk-sec');
    wrap.appendChild(row);
    var add = planAddBtn(r.sec.code, r.sec.crn, 'hawk-sec__add', 'Add ' + r.code + ' to a plan');
    add.appendChild(icon('plus', 16, 2.6));
    wrap.appendChild(add);
    return wrap;
  }
""")
js = one(js, "        clash: hits.length ? hits : null,\n        go: function () { return goSection(code, crn, label); }",
             "        clash: hits.length ? hits : null,\n        sec: crn ? { code: code, crn: String(crn) } : null,\n        go: function () { return goSection(code, crn, label); }")
js = one(js, "                    clash: hits.length ? hits : null,\n                    go: function () { return goSection(pk.code, crn, label); } });",
             "                    clash: hits.length ? hits : null,\n                    sec: crn ? { code: pk.code, crn: String(crn) } : null,\n                    go: function () { return goSection(pk.code, crn, label); } });")
js = one(js, "        clash: x.clash && x.clash.length ? x.clash : null,\n        go: function () { return goSection(x.course.code, crn, label); }",
             "        clash: x.clash && x.clash.length ? x.clash : null,\n        sec: crn ? { code: x.course.code, crn: String(crn) } : null,\n        go: function () { return goSection(x.course.code, crn, label); }")

# ---------------------------------------------------------------- 3. the cards, the term fix, and what they replace
js = one(js, "  /* One dispatcher for everything that is not a catalog search. Returns true when it rendered. */\n", CARDS + "\n  /* One dispatcher for everything that is not a catalog search. Returns true when it rendered. */\n")
js = one(js, "      if (renderPlan(turn, result, cat, q)) return true;\n    }\n    switch (result.tool) {",
             "      if (renderPlan(turn, result, cat, q)) return true;\n    }\n    var ans = answerFromTool(result, cat);\n    if (ans) { renderAnswer(turn, ans); return true; }\n    switch (result.tool) {")
for line in [
    "      case 'professor_stats':  renderProfStats(turn, result); return true;\n",
    "      case 'compare_professors': renderCompare(turn, result); return true;\n",
    "      case 'prereqs':          renderPrereqs(turn, result, cat); return true;\n",
    "      case 'my_day':           renderMyDay(turn, result); return true;\n",
    "      case 'my_professors':    renderMyProfessors(turn, result); return true;\n",
    "      case 'game_plan':        renderGamePlan(turn, result); return true;\n",
    "      case 'friends_free_now': renderFriendsFreeNow(turn); return true;\n",
    "      case 'free_with_friends': renderFreeWith(turn, result); return true;\n",
    "      case 'best_professor':   renderBestProf(turn, result); return true;\n",
    "      case 'fits_plan':        renderFitsPlan(turn, result); return true;\n",
    "      case 'my_conflicts':\n      case 'my_free':          renderPersonal(turn, result); return true;\n",
]:
    js = one(js, line, "")
# the renderers those cases called (their cards are above), and the helpers only they used
js = cut(js, "  function renderProfStats(turn, result) {", "  /* A prerequisite group is \"one of these\".")
js = cut(js, "  /* -- my_day: what do I have on <day>", "  /* -- my_units ---")
js = cut(js, "  /* -- game_plan (2026-09-25)", "  function nameOf(code) {")
js = cut(js, "  function nameOf(code) {", "  function regDate(v) {")
js = cut(js, "  function friendRow(f, sub) {", "  /* app_help: the sixteen questions about TermChamp")
js = cut(js, "  function renderMyProfessors(turn, result) {", "  function rowEl(r) {")
js = cut(js, "  function freeOn(day, mine) {", "  /* ---------------------------------------------------------------------------------------------\n     Scoring a section against what was asked.")
js = one(js, "  function myProfessors() {\n    var byKey = {}, list = [], unknown = [];\n    myCodes().forEach(function (code) {\n      var meta = null;\n      try { meta = (myClassMeta || {})[code] || null; } catch (_) { meta = null; }",
"""  function myProfessors(lists) {
    var byKey = {}, list = [], unknown = [];
    (lists || [{ codes: myCodes(), meta: null }]).forEach(function (L) { L.codes.forEach(function (code) {
      var meta = null;
      try { meta = (L.meta || myClassMeta || {})[code] || null; } catch (_) { meta = null; }""")
js = one(js, "      if (!got) unknown.push(code);\n    });\n    return { list: list, unknown: unknown };",
             "      if (!got) unknown.push(code);\n    }); });\n    return { list: list, unknown: unknown };")

# ---------------------------------------------------------------- 4. the header: the phone's line, and the trash can
js = one(js, "make('span', 'hawk-head__sub', 'From TermChamp’s real data')", "make('span', 'hawk-head__sub', 'Answers from TermChamp’s real data')")
js = one(js, "    x.setAttribute('aria-label', 'Close Champ');\n    head.appendChild(x);",
"""    x.setAttribute('aria-label', 'Close Champ');
    var clr = make('button', 'hawk-clear');
    clr.type = 'button';
    clr.setAttribute('aria-label', 'Clear chat');
    clr.appendChild(icon('trash', 17, 2));
    head.appendChild(clr);
    head.appendChild(x);""")
js = one(js, "    x.addEventListener('click', close);", "    x.addEventListener('click', close);\n    clr.addEventListener('click', clearChat);")
js = one(js, "if (e.target.closest && e.target.closest('.hawk-x')) return;   // the close button is a button",
             "if (e.target.closest && e.target.closest('.hawk-x, .hawk-clear')) return;   // the close and clear buttons are buttons")

CSS_NEW = r'''
/* ------------------------------------------------------------------------------------------------
   The chat and its cards — 2026-10-15 (website-champ-cards). The phone's Champ: a blue question bubble on the right, Champ's
   reply in a bubble beside Champ's face, a full-width card under it, follow-up questions under the newest answer.
   Every colour pair is a token with a dark and a light value, each >= 4.5:1 on the card it sits on (tested in both).
   ------------------------------------------------------------------------------------------------ */
:root {
  --hawk-chat-bg: var(--bg, #121212);
  --hawk-card: var(--panel, #1E1E1E);
  --hawk-fill: rgba(var(--hawk-fg), .07);
  --hawk-rule-strong: rgba(var(--hawk-fg), .24);
  --hawk-user-bg: #2A4A8F;
  --hawk-bar: #7C9BF2;
  --hawk-pill-bg: rgba(var(--hawk-fg), .09); --hawk-pill-ink: var(--hawk-dim);
  --hawk-ok-bg: rgba(127, 227, 181, .16);  --hawk-ok-ink: #7fe3b5;
  --hawk-bad-bg: rgba(255, 140, 140, .16); --hawk-bad-ink: #ffa3a3;
  --hawk-blue-bg: rgba(159, 180, 255, .16); --hawk-blue-ink: #c9d6ff;
  --hawk-mid-bg: rgba(255, 207, 122, .16); --hawk-mid-ink: #ffcf7a;
  --hawk-blk: var(--blk, #25396A); --hawk-blk-ink: var(--blk-ink, #DCE7FF);
  --hawk-clash: #F87171;
  --hawk-planA: #0F766E; --hawk-planB: #C2410C; --hawk-planC: #BE185D; --hawk-planM: #2A4A8F;
}
:root[data-theme="light"], :root[data-theme="cream"] {
  --hawk-user-bg: #16336B;
  --hawk-bar: #4B6FD6;
  --hawk-ok-bg: #DDF5F1;  --hawk-ok-ink: #0B5F58;
  --hawk-bad-bg: #FEE2E2; --hawk-bad-ink: #991B1B;
  --hawk-blue-bg: #E3ECFF; --hawk-blue-ink: #1E40AF;
  --hawk-mid-bg: #FEF3C7; --hawk-mid-ink: #744600;
  --hawk-blk: var(--blk, #D6E4FF); --hawk-blk-ink: var(--blk-ink, #1E40AF);
  --hawk-clash: #DC2626;
  --hawk-planA: #0F766E; --hawk-planB: #C2410C; --hawk-planC: #BE185D; --hawk-planM: #16336B;
}

/* the phone's header: Champ / Answers from TermChamp's real data, a trash can and the x */
.hawk-head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto auto; grid-template-areas: "bird name clear x" "bird sub clear x"; column-gap: 8px; row-gap: 0; align-items: center; }
.hawk-head__bird { grid-area: bird; }
.hawk-head__name { grid-area: name; align-self: end; line-height: 1.15; }
.hawk-head__sub { grid-area: sub; align-self: start; white-space: normal; font-size: 11.5px; line-height: 1.2; }
.hawk-box--empty .hawk-head { grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "name x"; }
.hawk-box--empty .hawk-head__name { align-self: center; }
.hawk-clear { grid-area: clear; display: grid; place-items: center; width: 32px; height: 32px; padding: 0; border: 0; border-radius: 999px; background: transparent; color: var(--hawk-dim); cursor: pointer; }
.hawk-clear:hover { color: var(--hawk-ink); background: var(--hawk-fill); }
.hawk-clear:focus-visible, .hawk-x:focus-visible { outline: 2px solid var(--hawk-focus); outline-offset: 1px; }
.hawk-box--empty .hawk-clear { display: none; }
.hawk-x { grid-area: x; margin-left: 0; min-width: 32px; min-height: 32px; }

/* the conversation */
.hawk-log { position: relative; max-height: min(62vh, 540px); padding: 12px 10px 8px; scroll-behavior: auto; overscroll-behavior: contain; }
.hawk-box:not(.hawk-box--empty) .hawk-log { background: var(--hawk-chat-bg); }
.hawk-turn { display: flex; flex-direction: column; gap: 8px; margin: 0 0 18px; min-width: 0; }
.hawk-turn:last-child { margin-bottom: 4px; }
.hawk-turn > * { min-width: 0; }
.hawk-turn > .hawk-read, .hawk-turn > .hawk-say, .hawk-turn > .hawk-opts, .hawk-turn > .hawk-alts, .hawk-turn > .hawk-week,
.hawk-turn > .hawk-count, .hawk-turn > .hawk-plansave { margin: 0; }
.hawk-turn > .hawk-count, .hawk-turn > .hawk-went { padding: 0 4px; }
.hawk-turn > .hawk-read { background: var(--hawk-blue-bg); color: var(--hawk-blue-ink); }
.hawk-turn > .hawk-read::before { color: var(--hawk-blue-ink); opacity: .8; }

.hawk-said { align-self: flex-end; max-width: 88%; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; padding: 0; }
.hawk-said__q { font-size: 13.5px; font-weight: 700; line-height: 1.35; color: #fff; background: var(--hawk-user-bg); padding: 8px 13px; border-radius: 18px 18px 4px 18px; overflow-wrap: anywhere; }
.hawk-said .hawk-fix { font-size: 10.5px; }

.hawk-bot { display: flex; gap: 7px; align-items: flex-start; }
.hawk-bot__av { flex: none; width: 26px; height: 31px; margin-top: 2px; background: var(--hawk-champ) center / contain no-repeat; }
.hawk-bubble { flex: 1 1 auto; min-width: 0; background: var(--hawk-card); border: 1px solid var(--hawk-rule); border-radius: 4px 18px 18px 18px; padding: 8px 12px; }
.hawk-bubble .hawk-note { padding: 0; margin: 0; font-size: 13.5px; line-height: 1.4; font-weight: 600; color: var(--hawk-ink); overflow-wrap: anywhere; }
.hawk-bubble .hawk-note + .hawk-note { margin-top: 5px; font-size: 12px; font-weight: 500; color: var(--hawk-dim); }
.hawk-bubble .hawk-note.hawk-note--good { color: var(--hawk-good); }
.hawk-bubble .hawk-acts, .hawk-bubble .hawk-alts { margin-top: 8px; }
.hawk-acts { display: flex; flex-wrap: wrap; gap: 6px; }
.hawk-follow { display: flex; flex-wrap: wrap; gap: 6px; padding-left: 2px; }
.hawk-fq { border: 1px solid var(--hawk-rule-strong); background: var(--hawk-card); color: var(--hawk-link); font-weight: 800; font-size: 12.5px; line-height: 1.25; padding: 7px 12px; min-height: 34px; border-radius: 17px; text-align: left; cursor: pointer; }
.hawk-fq:hover { border-color: var(--hawk-link); }
.hawk-fq:focus-visible, .hawk-act:focus-visible, .hawk-btn:focus-visible, .hawk-wrow:focus-visible, .hawk-day__blk:focus-visible,
.hawk-wk__blk:focus-visible, .hawk-ptop:focus-visible, .hawk-prow:focus-visible, .hawk-ctop:focus-visible, .hawk-fr__main:focus-visible,
.hawk-q__go:focus-visible, .hawk-grow:focus-visible, .hawk-sec__add:focus-visible, .hawk-ch__open:focus-visible, .hawk-teach__c:focus-visible,
.hawk-more:focus-visible { outline: 2px solid var(--hawk-focus); outline-offset: 2px; }
.hawk-act { border: 1px solid var(--hawk-rule-strong); border-radius: 999px; background: transparent; color: var(--hawk-link); font-weight: 800; font-size: 12px; line-height: 1; min-height: 34px; padding: 0 13px; cursor: pointer; }
.hawk-act--primary { background: var(--hawk-user-bg); border-color: var(--hawk-user-bg); color: #fff; }
.hawk-turn > .hawk-notit { align-self: flex-end; margin: -4px 0 0; }

/* a card */
.hawk-card { display: flex; flex-direction: column; gap: 8px; min-width: 0; background: var(--hawk-card); border: 1px solid var(--hawk-rule); border-radius: 16px; padding: 10px; }
.hawk-cards { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.hawk-ch { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.hawk-ch__t { font-size: 15px; font-weight: 900; color: var(--hawk-ink); }
.hawk-ch__s { font-size: 11.5px; color: var(--hawk-dim); }
.hawk-ch__gap { flex: 1 1 auto; }
.hawk-ch__open { border: 0; background: none; color: var(--hawk-link); font-weight: 800; font-size: 12.5px; line-height: 1; min-height: 32px; padding: 0 2px 0 8px; cursor: pointer; }
.hawk-k { display: block; padding: 6px 4px 0; font-size: 11px; font-weight: 900; letter-spacing: .05em; text-transform: uppercase; color: var(--hawk-dim); }
.hawk-pill { display: inline-flex; align-items: center; max-width: 100%; font-size: 11px; font-weight: 800; line-height: 1.15; padding: 4px 8px; border-radius: 999px; background: var(--hawk-pill-bg); color: var(--hawk-pill-ink); overflow-wrap: anywhere; }
.hawk-pill--ok { background: var(--hawk-ok-bg); color: var(--hawk-ok-ink); }
.hawk-pill--bad { background: var(--hawk-bad-bg); color: var(--hawk-bad-ink); }
.hawk-pill--blue { background: var(--hawk-blue-bg); color: var(--hawk-blue-ink); }
.hawk-pill--mid { background: var(--hawk-mid-bg); color: var(--hawk-mid-ink); }
.hawk-plan { font-size: 11px; font-weight: 900; padding: 4px 9px; border-radius: 999px; color: #fff; background: var(--hawk-planM); }
.hawk-plan--A { background: var(--hawk-planA); } .hawk-plan--B { background: var(--hawk-planB); } .hawk-plan--C { background: var(--hawk-planC); }
.hawk-facts { display: flex; flex-wrap: wrap; gap: 5px; }
.hawk-btns { display: flex; gap: 8px; }
.hawk-btn { flex: 1 1 0; min-height: 38px; border: 0; border-radius: 12px; font-weight: 800; font-size: 13px; line-height: 1.1; padding: 0 10px; cursor: pointer; background: var(--hawk-blue-bg); color: var(--hawk-blue-ink); }
.hawk-btn--go { background: var(--hawk-user-bg); color: #fff; }
.hawk-btn--wide { flex: none; width: 100%; }

/* Your week */
.hawk-wrow { display: grid; grid-template-columns: 34px minmax(0, 1fr) 16px; gap: 8px; align-items: center; width: 100%; padding: 8px 2px; border: 0; border-top: 1px solid var(--hawk-rule); background: none; color: var(--hawk-dim); font: inherit; text-align: left; cursor: pointer; }
.hawk-wrow:hover { background: var(--hawk-fill); }
.hawk-wrow--static { cursor: default; padding: 6px 2px; }
.hawk-wrow--static:hover { background: none; }
.hawk-wrow--static { grid-template-columns: 34px minmax(0, 1fr); }
.hawk-wrow__d { font-size: 13px; font-weight: 900; color: var(--hawk-ink); }
.hawk-wrow__m { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.hawk-wrow__bar { position: relative; display: block; height: 10px; border-radius: 5px; background: rgba(var(--hawk-fg), .09); overflow: hidden; }
.hawk-wrow__bar i { position: absolute; top: 0; bottom: 0; border-radius: 3px; background: var(--hawk-bar); }
.hawk-wrow__t { font-size: 12px; font-weight: 700; color: var(--hawk-dim); overflow-wrap: anywhere; }
.hawk-wrow__t--ok { color: var(--hawk-ok-ink); }
.hawk-wax { display: flex; justify-content: space-between; padding: 0 22px 0 42px; font-size: 10px; color: var(--hawk-dim); }

/* Your day, on a clock */
.hawk-day { display: flex; gap: 6px; }
.hawk-day__lab { position: relative; flex: none; width: 34px; }
.hawk-day__lab span { position: absolute; right: 0; transform: translateY(-50%); font-size: 10px; color: var(--hawk-dim); }
.hawk-day__lab span:first-child { transform: none; }
.hawk-day__col { position: relative; flex: 1 1 auto; min-width: 0; border-left: 1px solid var(--hawk-rule); }
.hawk-day__free { position: absolute; left: 6px; right: 0; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; border: 1.5px dashed var(--hawk-rule-strong); border-radius: 10px; color: var(--hawk-dim); font-size: 11.5px; text-align: center; overflow: hidden; }
.hawk-day__free b { font-weight: 800; }
.hawk-day__free--one { flex-direction: row; gap: 6px; }
.hawk-day__blk { position: absolute; left: 6px; right: 0; box-sizing: border-box; display: block; text-align: left; border: 0; border-radius: 10px; padding: 5px 9px; background: var(--hawk-blk); color: var(--hawk-blk-ink); font: inherit; overflow: hidden; cursor: pointer; }
.hawk-day__blk b { display: block; font-size: 13px; font-weight: 900; }
.hawk-day__blk > span:not(.hawk-pill) { font-size: 11px; font-weight: 700; }
.hawk-day__blk .hawk-pill { margin-top: 3px; }
.hawk-day__blk--cm { background: var(--hawk-mid-bg); color: var(--hawk-mid-ink); }
.hawk-day__blk:disabled { cursor: default; }
.hawk-day__now { position: absolute; left: 0; right: 0; height: 0; border-top: 2px solid var(--hawk-clash); pointer-events: none; }
.hawk-day__now::before { content: ""; position: absolute; left: -4px; top: -5px; width: 8px; height: 8px; border-radius: 50%; background: var(--hawk-clash); }

/* A week as a grid (does it fit? / my clashes) */
.hawk-wk__row { display: grid; grid-template-columns: 30px repeat(5, minmax(0, 1fr)); gap: 3px; }
.hawk-wk__head span { text-align: center; font-size: 10.5px; font-weight: 900; color: var(--hawk-dim); padding-bottom: 3px; }
.hawk-wk__lab { position: relative; }
.hawk-wk__lab span { position: absolute; right: 2px; transform: translateY(-1px); font-size: 9px; color: var(--hawk-dim); }
.hawk-wk__lane { position: relative; border-radius: 6px; background: rgba(var(--hawk-fg), .05); }
.hawk-wk__blk { position: absolute; left: 1px; right: 1px; box-sizing: border-box; display: block; border: 0; border-radius: 4px; padding: 2px 3px; background: var(--hawk-blk); color: var(--hawk-blk-ink); font-weight: 800; font-size: 9px; line-height: 1.15; text-align: left; overflow: hidden; cursor: pointer; }
.hawk-wk__blk:disabled { cursor: default; }
.hawk-wk__blk--cm { background: var(--hawk-mid-bg); color: var(--hawk-mid-ink); }
.hawk-wk__blk--ghost { background: var(--hawk-card); color: var(--hawk-link); border: 1.5px dashed var(--hawk-link); }
.hawk-wk__blk--clash { outline: 2px solid var(--hawk-clash); outline-offset: -1px; z-index: 1; }

/* friends */
.hawk-fr { display: flex; flex-direction: column; gap: 6px; padding: 8px 2px; border-top: 1px solid var(--hawk-rule); }
.hawk-fr:first-of-type { border-top: 0; }
.hawk-fr__top { display: flex; align-items: center; gap: 8px; }
.hawk-fr__main { flex: 1 1 auto; min-width: 0; display: flex; align-items: center; gap: 9px; border: 0; background: none; color: inherit; font: inherit; text-align: left; padding: 0; cursor: pointer; }
.hawk-fr__tx { display: flex; flex-direction: column; min-width: 0; }
.hawk-fr__tx b { font-size: 14px; font-weight: 900; color: var(--hawk-ink); }
.hawk-fr__tx span { font-size: 11.5px; font-weight: 600; color: var(--hawk-dim); overflow-wrap: anywhere; }
.hawk-fr--free .hawk-fr__tx span { color: var(--hawk-ok-ink); }
.hawk-av { flex: none; display: inline-grid; place-items: center; border-radius: 50%; overflow: hidden; background: var(--hawk-blk); color: var(--hawk-blk-ink); font-weight: 900; }
.hawk-av img { width: 100%; height: 100%; object-fit: cover; display: block; }
.hawk-fbar { position: relative; display: block; height: 8px; border-radius: 4px; background: rgba(var(--hawk-fg), .09); overflow: hidden; }
.hawk-fbar i { position: absolute; top: 0; bottom: 0; background: var(--hawk-bar); border-radius: 2px; }
.hawk-fbar em { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--hawk-clash); }

/* professors, classes, sections */
.hawk-ptop { display: flex; align-items: center; gap: 10px; width: 100%; border: 0; background: none; color: inherit; font: inherit; text-align: left; padding: 0; cursor: pointer; }
.hawk-ptop__tx { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; }
.hawk-ptop__tx b { font-size: 15px; font-weight: 900; color: var(--hawk-ink); overflow-wrap: anywhere; }
.hawk-ptop__tx span { font-size: 11.5px; color: var(--hawk-dim); }
.hawk-ptop__avg { flex: none; display: flex; flex-direction: column; align-items: center; }
.hawk-ptop__avg b { font-size: 24px; font-weight: 900; line-height: 1; color: var(--hawk-ok-ink); }
.hawk-ptop__avg span { font-size: 9px; letter-spacing: .06em; color: var(--hawk-dim); }
.hawk-av--prof { background: var(--hawk-blue-bg); color: var(--hawk-blue-ink); }
.hawk-tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(72px, 1fr)); gap: 6px; }
.hawk-tiles div { background: var(--hawk-fill); border-radius: 10px; padding: 7px 4px; text-align: center; }
.hawk-tiles b { display: block; font-size: 17px; font-weight: 900; color: var(--hawk-ink); }
.hawk-tiles span { font-size: 10.5px; color: var(--hawk-dim); }
.hawk-teach { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.hawk-teach .hawk-k { padding: 0 4px 0 0; }
.hawk-teach__c { border: 0; border-radius: 999px; background: var(--hawk-blue-bg); color: var(--hawk-blue-ink); font: 900 12px/1 ui-monospace, Menlo, monospace; padding: 8px 11px; min-height: 32px; cursor: pointer; }
.hawk-prow { display: flex; align-items: center; gap: 9px; width: 100%; padding: 9px 2px; border: 0; border-top: 1px solid var(--hawk-rule); background: none; color: inherit; font: inherit; text-align: left; cursor: pointer; }
.hawk-prow:first-child { border-top: 0; }
.hawk-prow .hawk-pill, .hawk-day__blk .hawk-pill { flex: none; white-space: nowrap; }
.hawk-prow:hover { background: var(--hawk-fill); }
.hawk-prow__tx { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; }
.hawk-prow__tx b { font-size: 13.5px; font-weight: 800; color: var(--hawk-ink); overflow-wrap: anywhere; }
.hawk-prow__tx span { font-size: 11.5px; color: var(--hawk-dim); overflow-wrap: anywhere; }
.hawk-ctop { display: flex; align-items: center; gap: 8px; width: 100%; border: 0; background: none; color: inherit; font: inherit; text-align: left; padding: 0; cursor: pointer; }
.hawk-ctop__code { flex: none; font: 900 12.5px/1 ui-monospace, Menlo, monospace; color: var(--hawk-link); }
.hawk-ctop b { flex: 1 1 auto; min-width: 0; font-size: 14px; font-weight: 800; color: var(--hawk-ink); overflow-wrap: anywhere; }
.hawk-ctop svg { flex: none; color: var(--hawk-dim); }
.hawk-ctop__chip { flex: none; margin-left: auto; }
.hawk-more { align-self: flex-start; border: 0; background: none; color: var(--hawk-link); font-weight: 800; font-size: 12.5px; line-height: 1; min-height: 32px; padding: 0 4px; cursor: pointer; }
.hawk-card--rows { padding: 2px 10px; gap: 0; }
.hawk-card--rows > .hawk-row, .hawk-card--rows > .hawk-sec, .hawk-psecs > .hawk-row, .hawk-psecs > .hawk-sec { border-top: 1px solid var(--hawk-rule); }
.hawk-card--rows > :first-child, .hawk-psecs > :first-child { border-top: 0; }
.hawk-card--rows .hawk-row, .hawk-psecs .hawk-row { background: none; border-radius: 0; margin: 0; padding: 9px 2px; }
.hawk-card--rows .hawk-row:hover, .hawk-psecs .hawk-row:hover { background: var(--hawk-fill); }
.hawk-psecs { display: flex; flex-direction: column; border-radius: 12px; background: var(--hawk-fill); padding: 0 8px; }
.hawk-sec { display: flex; align-items: center; gap: 4px; }
.hawk-sec > .hawk-row { flex: 1 1 auto; min-width: 0; width: auto; }
.hawk-sec__add { flex: none; display: grid; place-items: center; width: 34px; height: 34px; padding: 0; border: 1px solid var(--hawk-rule-strong); border-radius: 50%; background: var(--hawk-card); color: var(--hawk-link); cursor: pointer; }
.hawk-sec__add:hover { border-color: var(--hawk-link); }
.hawk-row__fit { display: block; margin-top: 1px; font-size: 10.5px; font-weight: 700; color: var(--hawk-ok-ink); }
.hawk-row--rich .hawk-row__name { -webkit-line-clamp: 3; }

/* prerequisites */
.hawk-pbar { height: 6px; border-radius: 3px; background: rgba(var(--hawk-fg), .1); overflow: hidden; }
.hawk-pbar i { display: block; height: 100%; background: var(--hawk-bar); border-radius: 3px; }
.hawk-q { display: flex; align-items: flex-start; gap: 9px; padding: 7px 2px; border-top: 1px solid var(--hawk-rule); }
.hawk-q__dot { flex: none; display: grid; place-items: center; width: 22px; height: 22px; margin-top: 1px; border-radius: 50%; font-size: 12px; font-weight: 900; border: 2px dashed var(--hawk-rule-strong); color: var(--hawk-dim); box-sizing: border-box; }
.hawk-q__dot--ok { border: 0; background: var(--hawk-ok-bg); color: var(--hawk-ok-ink); }
.hawk-q__dot--now { border: 0; background: var(--hawk-mid-bg); color: var(--hawk-mid-ink); }
.hawk-q__tx { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; }
.hawk-q__tx b { font-size: 13px; font-weight: 800; color: var(--hawk-ink); }
.hawk-q__tx > span:not(.hawk-q__links) { font-size: 11.5px; color: var(--hawk-dim); }
.hawk-q__links { display: flex; flex-wrap: wrap; gap: 2px 10px; }
.hawk-q__go { border: 0; background: none; color: var(--hawk-link); font: 800 12px/1 ui-monospace, Menlo, monospace; min-height: 30px; padding: 0; cursor: pointer; }

/* the game plan */
.hawk-grow { display: flex; align-items: flex-start; gap: 9px; width: 100%; padding: 9px 2px; border: 0; border-top: 1px solid var(--hawk-rule); background: none; color: inherit; font: inherit; text-align: left; cursor: pointer; }
.hawk-grow:hover { background: var(--hawk-fill); }
.hawk-grow__n { flex: none; display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; font-weight: 900; background: var(--hawk-pill-bg); color: var(--hawk-pill-ink); }
.hawk-grow__n--hot { background: var(--hawk-bad-bg); color: var(--hawk-bad-ink); }
.hawk-grow__n--ok { background: var(--hawk-ok-bg); color: var(--hawk-ok-ink); }
.hawk-grow__tx { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.hawk-grow__h { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 8px; }
.hawk-grow__h b { font: 900 12.5px/1.2 ui-monospace, Menlo, monospace; color: var(--hawk-ink); }
.hawk-grow__h span, .hawk-grow__bk { font-size: 11.5px; color: var(--hawk-dim); }
.hawk-grow__why { font-size: 12px; font-weight: 700; color: var(--hawk-ink); }
.hawk-grow__bar { display: flex; align-items: center; gap: 7px; }
.hawk-grow__bar > span:first-child { flex: 1 1 auto; height: 5px; border-radius: 3px; background: rgba(var(--hawk-fg), .1); overflow: hidden; }
.hawk-grow__bar i { display: block; height: 100%; border-radius: 3px; background: var(--hawk-bar); }
.hawk-grow__fill--hot { background: var(--hawk-bad-ink) !important; }
.hawk-grow__seat { flex: none; font-size: 11.5px; font-weight: 800; color: var(--hawk-dim); }
.hawk-grow__seat--hot { color: var(--hawk-bad-ink); } .hawk-grow__seat--ok { color: var(--hawk-ok-ink); }

/* where a tap went: said once, at the foot of that answer */
.hawk-went { font-size: 11.5px; }
/* The site's own plan chooser (Plan A / B / C) opens over Champ, not under it. */
#plChoose.pl2-choose { z-index: 9100; }

@media (max-width: 720px) {
  .hawk-log { max-height: min(54vh, 460px); }
  .hawk-fq { font-size: 13px; }
}
@media (prefers-reduced-motion: reduce) { .hawk-card, .hawk-bubble { animation: none !important; } }
'''
css = css.rstrip("\n") + "\n" + CSS_NEW

# ---------------------------------------------------------------- 5. the build stamp (index.html, sw.js and the three asset ?v= digits move together)
STAMP = '2026-10-15 12:14'; DIGITS = re.sub(r'\D', '', STAMP)
idx = one(idx, "window.PROFESSIFY_BUILD='2026-10-15 00:36';", "window.PROFESSIFY_BUILD='" + STAMP + "';")
sw = one(sw, "const BUILD = '2026-10-15 00:36';", "const BUILD = '" + STAMP + "';")
for a in ('hawk-ask.css', 'hawk-router.js', 'hawk-ask.js'):
    idx = one(idx, a + '?v=202610150036"', a + '?v=' + DIGITS + '"')

js_f.write_text(js)
css_f.write_text(css)
idx_f.write_text(idx)
sw_f.write_text(sw)
