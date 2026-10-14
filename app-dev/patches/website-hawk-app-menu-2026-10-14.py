#!/usr/bin/env python3
"""Website Hawk gets the app's menu (Tate, 2026-10-13: "Hawk sends client:'app'"; phone: TC.ask sends client:'app',
answerTool / CH_CARDS / HELP, 2026-10-08..11). Edits hawk-ask.js only (website-only; the edge function is untouched).

  - The model tier now sends client:'app', so the function routes with the app's menu (APP_TOOLS) - the same five tools the phone's
    Champ added answer here: friends_free_now, free_with_friends, best_professor, fits_plan, app_help (16 topics).
  - Each renders as Hawk rows in Hawk's own style:
      friends_free_now / free_with_friends -> one row per friend (opens their profile), with the line the app already shows
        ("No class till 2:10pm"); a friend whose times we do not have is counted, never guessed.
      best_professor -> the professors teaching that course, best-rated first (opens the professor).
      fits_plan -> the sections of that course that fit Plan A/B/C (or your classes), each opening its class page.
      app_help -> the answer in a sentence or two and a "Go there" row.
Replay on f72f221:  python3 website-hawk-app-menu-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'hawk-ask.js'
s = f.read_text()
if 'website-hawk-app-menu (2026-10-14)' in s:
    sys.exit('already patched')

def one(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:120])
    s = s.replace(old, new)

one("    return callAsk({ q: q }).then(function (j) {",
    "    return callAsk({ q: q, client: 'app' }).then(function (j) {   /* website-hawk-app-menu (2026-10-14): the app's menu of tools */")

BLOCK = r"""
  /* ===============================================================================================
     THE APP'S MENU — website-hawk-app-menu (2026-10-14). The five tools the phone's Champ adds to the menu, answered
     here from what the page already holds, in Hawk's rows. Nothing is guessed: a friend with no timetable is counted
     as such, a professor with no rating shows none, and a class that fits nowhere says so.
     =============================================================================================== */
  function appFriends() { var l = []; try { l = FRIENDS || []; } catch (_) {} return l; }
  function freeState(f) {
    try { if (has('avState') && has('avMeetsOf')) return global.avState(global.avMeetsOf(f), new Date()); } catch (_) {}
    return { state: 'unknown' };
  }
  function freeLine(st) { try { return has('avLine') ? global.avLine(st) : ''; } catch (_) { return ''; } }
  function friendRow(f, sub) {
    return rowEl({ code: '', name: f.name || 'Friend', sub: sub || '', chip: null,
      go: function () {
        try { if (has('openFriendProfile')) { global.openFriendProfile(f.id, 'classes'); return 'Opened ' + f.name; } } catch (_) {}
        return goPlace('friends');
      } });
  }
  function noFriends(turn) {
    turn.appendChild(make('div', 'hawk-note', 'You haven’t added any friends yet, so there’s nobody to look for.'));
    turn.appendChild(rowEl({ code: '', name: 'Open Friends', chip: null, go: function () { return goPlace('friends'); } }));
  }
  /* friends_free_now: who has no class right now */
  function renderFriendsFreeNow(turn) {
    var list = appFriends();
    if (!list.length) { noFriends(turn); return; }
    var free = [], unknown = 0;
    list.forEach(function (f) {
      var st = freeState(f);
      if (st.state === 'open') free.push({ f: f, st: st });
      else if (st.state === 'unknown') unknown += 1;
    });
    if (!free.length) {
      turn.appendChild(make('div', 'hawk-note', unknown === list.length
        ? 'None of your friends’ classes have times I can read yet, so I can’t say who’s free.'
        : 'Nobody’s free right now.' + (unknown ? ' ' + unknown + (unknown === 1 ? ' friend has' : ' friends have') + ' no times I can read, so I can’t say for them.' : '')));
    } else {
      turn.appendChild(make('div', 'hawk-note', free.length + (free.length === 1 ? ' friend is' : ' friends are') + ' free right now:'));
      free.forEach(function (x) { turn.appendChild(friendRow(x.f, freeLine(x.st))); });
    }
    if (unknown && free.length) turn.appendChild(make('div', 'hawk-note', unknown + (unknown === 1 ? ' friend has' : ' friends have') + ' no times I can read, so they’re not counted.'));
  }
  /* free_with_friends: one friend, now (or a day, which their page shows), or everyone now */
  function renderFreeWith(turn, result) {
    var a = result.args || {};
    var named = !!(a.rel || (a.days && a.days.length));
    if (a.friend) {
      var f = friendByName(a.friend);
      if (!f) { notFound(turn, 'I couldn’t find one friend named “' + a.friend + '”.'); return; }
      var first = String(f.name || '').split(' ')[0], st = freeState(f);
      if (named) {
        turn.appendChild(make('div', 'hawk-note', first + '’s week is on their page.'));
        turn.appendChild(friendRow(f, ''));
        return;
      }
      var line = freeLine(st);
      turn.appendChild(make('div', 'hawk-note', line ? (first + ': ' + line + '.') : ('I don’t have times for ' + first + '’s classes, so I can’t say.')));
      turn.appendChild(friendRow(f, ''));
      return;
    }
    if (!named) { renderFriendsFreeNow(turn); return; }
    turn.appendChild(make('div', 'hawk-note', 'Free time together is in Groups.'));
    turn.appendChild(rowEl({ code: '', name: 'Open Groups', chip: null, go: function () { return goPlace('groups'); } }));
  }
  /* best_professor: who teaches the course, best-rated first */
  function renderBestProf(turn, result) {
    var code = (result.args || {}).course;
    var rows = sectionsOf(code);
    if (!code || !rows.length) { notFound(turn, (code || 'That class') + ' isn’t on this term’s schedule.'); return; }
    var by = {}, order = [];
    rows.forEach(function (r) {
      var p = profOf(r); if (!p) return;
      var k = p.id || p.raw;
      if (!by[k]) { by[k] = { p: p, n: 0 }; order.push(k); }
      by[k].n += 1;
    });
    if (!order.length) { notFound(turn, 'No professor is listed for ' + code + ' yet.'); return; }
    order.sort(function (x, y) { var rx = by[x].p.rating, ry = by[y].p.rating; return (ry == null ? -1 : ry) - (rx == null ? -1 : rx); });
    var any = order.some(function (k) { return by[k].p.rating != null; });
    turn.appendChild(make('div', 'hawk-note', any ? ('Who teaches ' + code + ', best-rated first:') : ('Who teaches ' + code + ' — none of them has a rating yet:')));
    order.forEach(function (k) {
      var p = by[k].p;
      turn.appendChild(rowEl({ code: '', name: p.name, sub: by[k].n + (by[k].n === 1 ? ' section' : ' sections'),
        chip: p.rating != null ? ratingChip(p.rating) : null,
        go: function () { return p.id ? goProfessor(p.name) : goClass(code); } }));
    });
  }
  /* fits_plan: the sections of a course that fit Plan A/B/C, or your classes */
  function renderFitsPlan(turn, result) {
    var a = result.args || {}, code = a.course;
    if (!code) { notFound(turn, 'I couldn’t tell which class.'); return; }
    var slot = /^[ABC]$/.test(String(a.plan || '')) ? String(a.plan) : null, T = global.TCPlans, items = [], where = '';
    if (!slot && a.plan !== 'mine' && T && T.cur) { try { slot = T.cur(); } catch (_) {} }
    if (slot && T && T.fitFor) {
      var fit = null; try { fit = T.fitFor(code, slot); } catch (_) {}
      where = 'Plan ' + slot;
      if (fit === null) { turn.appendChild(make('div', 'hawk-note', code + ' is already in Plan ' + slot + '.')); return; }
      if (!fit || !fit.offered) { notFound(turn, code + ' isn’t on this term’s schedule.'); return; }
      items = (fit.list || []).map(function (i) { return { crn: i.crn, label: i.label, when: i.when, prof: i.prof, rating: i.rating != null ? five(i.rating) : null }; });
    } else {
      where = 'your classes';
      var rows = sectionsOf(code);
      if (!rows.length) { notFound(turn, code + ' isn’t on this term’s schedule.'); return; }
      var mine = []; try { mine = has('myClassMeets') ? global.myClassMeets(myCodes()) : []; } catch (_) {}
      rows.forEach(function (r) {
        var m = meetOf(r); if (!m) return;
        var clash = mine.some(function (x) { return x.code !== code && x.meet && has('meetsOverlap') && global.meetsOverlap(m, x.meet); });
        if (clash) return;
        var p = profOf(r) || {}, crn = String(r.class_nbr || '');
        items.push({ crn: crn, label: code + '-' + (secNumber(r) || crn), when: r.days, prof: p.name || '', rating: p.rating == null ? null : p.rating });
      });
    }
    if (!items.length) { turn.appendChild(make('div', 'hawk-note', 'Nothing in ' + code + ' fits around ' + where + '.')); return; }
    turn.appendChild(make('div', 'hawk-note', items.length + (items.length === 1 ? ' section of ' : ' sections of ') + code + ' fit' + (items.length === 1 ? 's' : '') + ' around ' + where + ':'));
    items.slice(0, 8).forEach(function (i) {
      turn.appendChild(rowEl({ code: i.label, name: i.prof || 'Staff', sub: i.when || '', chip: i.rating != null ? ratingChip(i.rating) : null,
        go: function () { return goSection(code, i.crn, i.label); } }));
    });
  }
  /* app_help: the sixteen questions about TermChamp, in a sentence or two, and where to go */
  var APP_HELP = {
    what_is: ['TermChamp helps Cal Poly students plan classes with friends: professor ratings, open seats, and which friends are in each class. It’s made by students — not a Cal Poly service.', 'Browse classes', 'explore'],
    free: ['Yes — TermChamp is free. There are no ads, and your data is never sold.', 'Privacy policy', 'privacy policy'],
    who_sees: ['Only friends you’ve accepted see your classes. Each plan has its own “Friends can see” switch — turn it off to keep that plan to yourself. Remove a friend and they stop seeing it.', 'Open Settings', 'privacy settings'],
    ratings_anonymous: ['Yes. Your name is never shown on a review — professors and other students can’t tell it was you. You can choose to show your friends, one review at a time.', 'Your reviews', 'my reviews'],
    ratings_source: ['From PolyRatings, plus the reviews TermChamp students write here. Open a professor to see their rating.', 'Find a professor', 'explore professors'],
    seats_source: ['From Cal Poly’s public class search, refreshed about once a day — so they can be a day old, or wrong. Always check the Cal Poly Portal before you register.', 'Browse classes', 'explore'],
    add_class: ['Find it in Explore, open the class and tap “I’m in this” on your section — or ＋ Plan to put it in Plan A, B or C. Classes you’ve already taken go in Schedule › Past classes.', 'Open Explore', 'explore'],
    plans: ['Plans A, B and C are three versions of your next term, kept in Schedule › Planner. Add a section to one from any class page with ＋ Plan, and change any of them. Ask me for your game plan to see what to register for first.', 'Open Planner', 'planner'],
    seat_alerts: ['Tap Watch on a full section; sections you add to a plan are watched for you. With notifications on, the TermChamp iPhone app tells you when a seat opens.', 'Browse classes', 'explore'],
    degree_report: ['In the Cal Poly Portal: Student Center › Academic Progress › Degree Progress Report › View PDF › Download. Then upload it in Schedule › Past classes. Your grades and student ID are never saved.', 'Open Past classes', 'past classes'],
    add_friends: ['Open Friends and search by name or @username, or share your QR code or invite link. Once they accept, you see each other’s classes.', 'Add a friend', 'add friend'],
    block_report: ['Open their profile or your chat with them and use Block or Report at the bottom — they aren’t told. To report a review, use the flag on it. A person looks at every report within 24 hours.', 'Open Friends', 'friends'],
    delete_account: ['Settings › Delete account. It’s hidden right away and deleted after 30 days — sign back in before then to recover it. You choose whether your reviews stay up with no name.', 'Open Settings', 'account'],
    champ: ['Hawk answers questions about classes, professors, your week, your friends and TermChamp. Each question you ask goes to Anthropic’s AI to work out what you mean — never your name or account, though a class or friend you name goes with it. TermChamp keeps questions about 30 days, not linked to you, and Anthropic doesn’t train on them.', 'Privacy policy', 'privacy policy'],
    dark_mode: ['Yes — Settings › Appearance: System, Light or Dark.', 'Open Settings', 'appearance'],
    contact: ['Email support@termchamp.com — for a bug, feedback, or anything else.', 'Email support', 'mailto']
  };
  function renderAppHelp(turn, result) {
    var k = String((result.args || {}).topic || ''), h = Object.prototype.hasOwnProperty.call(APP_HELP, k) ? APP_HELP[k] : null;
    if (!h) { turn.appendChild(make('div', 'hawk-note', 'I’m not sure which question you mean — try asking it another way.')); return; }
    turn.appendChild(make('div', 'hawk-note', h[0]));
    turn.appendChild(rowEl({ code: '', name: h[1], chip: null,
      go: function () { if (h[2] === 'mailto') { try { global.location.href = 'mailto:support@termchamp.com'; } catch (_) {} return 'Opened your email'; } return goPlace(h[2]); } }));
  }

"""
one("  function renderTool(turn, result, cat, q) {\n", BLOCK + "  function renderTool(turn, result, cat, q) {\n")
one("      case 'my_conflicts':\n      case 'my_free':          renderPersonal(turn, result); return true;",
    "      case 'friends_free_now': renderFriendsFreeNow(turn); return true;\n      case 'free_with_friends': renderFreeWith(turn, result); return true;\n      case 'best_professor':   renderBestProf(turn, result); return true;\n      case 'fits_plan':        renderFitsPlan(turn, result); return true;\n      case 'app_help':         renderAppHelp(turn, result); return true;\n      case 'my_conflicts':\n      case 'my_free':          renderPersonal(turn, result); return true;")
s = s.replace("  var AI_TIMEOUT = 9000;", "  /* website-hawk-app-menu (2026-10-14) */\n  var AI_TIMEOUT = 9000;", 1)
f.write_text(s)
print('ok')
