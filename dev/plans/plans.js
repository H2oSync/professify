/* =================================================================================================
   PLANS A–C, THE REGISTRATION GAME PLAN AND BACKUP SECTIONS — 2026-09-25
   Design: claude/spring-plans-game-plan-design-2026-09-25.md (locked by Tate the same day).

   Inlined into index.html by apply-plans.mjs, between the PLANS-JS markers. Everything it reads it
   reads through the app's own functions — clsSections, parseMeet, meetsOverlap, secSeat,
   seatParts, to5, wcWatchSec, mcEnrollSec — so a section a plan calls "Tuesday 11:10" is the
   section the calendar draws on Tuesday at 11:10.

   WHAT A PLAN IS. Up to three schedules per term, A, B and C, each a list of {code, class_nbr}.
   Every section in a plan is watched (the seat-alert path is unchanged), and the old section
   watchlist lives on underneath as "Watching, not in a plan".

   WHERE IT IS KEPT. On the device always; in the `plans` table (professify-plans.sql) when the
   student is signed in. If the table is not there yet the plans stay on this device and the pane
   says so — it never claims a save it did not make.

   WHAT IT WILL NOT SAY. Anything about other students' appointments, a seat count it does not
   hold, or a pairing of lecture and lab the feed does not carry. A plan built on this term's
   sections while registration is for another term is labelled a preview, not passed off.
   ================================================================================================= */
(function () {
  'use strict';
  var SLOTS = ['A', 'B', 'C'];
  var ROUND1_UNITS = 16, ROUND1_WAIT = 12;   // registrar, Spring 2027 calendar (see REGISTRATION_OPENS)
  var UNRATED = 2.64;                         // 3.3 out of 5 on PolyRatings' 0–4 scale: neutral, never zero
  var SHOW_AT = 3;                            // "N in plans" threshold (Tate, 2026-09-25); the server enforces it too

  function has(n) { try { return typeof window[n] === 'function'; } catch (_) { return false; } }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function term() { try { return has('mcTerm') ? mcTerm() : '2268'; } catch (_) { return '2268'; } }
  function termLabel() { try { return has('mcTermLabel') ? mcTermLabel() : term(); } catch (_) { return term(); } }
  function cfgv(k) { try { return ((window.PROFESSIFY_CONFIG || {})[k]) || ''; } catch (_) { return ''; } }
  function me() { try { return (typeof sbUser !== 'undefined' && sbUser) ? sbUser : null; } catch (_) { return null; } }
  function client() { try { return (typeof sb !== 'undefined' && sb) ? sb : null; } catch (_) { return null; } }
  function toast(m) { try { if (has('frToast')) frToast(m); } catch (_) {} }

  /* ---------------------------------------------------------------------------------------------
     State
     --------------------------------------------------------------------------------------------- */
  var S = { term: null, owner: null, plans: null, cur: 'A', server: 'local', dirty: {}, autoW: {}, adopt: false };
  var watchesFor = null;      // the account whose own watches have finished loading on this device
  var interest = {}, interestAsked = {}, interestTerm = null;
  var friendPlans = null, friendPlansFor = {};
  var undoBox = null;

  function blank() { var o = {}; SLOTS.forEach(function (s) { o[s] = { sections: [], shared: true }; }); return o; }
  /* KEYED BY TERM AND BY WHO. Keyed by term alone, one student's plans on a shared computer were
     pushed into the next account that signed in there (review, 2026-09-25) — and shared with that
     account's friends by default. Each account has its own copy; plans made signed out live under
     'anon' and join an account only when the student says so. Signing out clears the account's
     copy from this device. */
  function ownerId() { var u = me(); return u ? String(u.id) : 'anon'; }
  function lsKey(owner) { return 'professify_plans_' + term() + '_' + (owner || ownerId()); }
  function readLocal(key) {
    var out = { plans: blank(), cur: null, autoW: {}, dirty: {} };
    try {
      var raw = JSON.parse(localStorage.getItem(key) || 'null');
      if (raw && raw.plans) SLOTS.forEach(function (s) {
        var p = raw.plans[s]; if (!p) return;
        out.plans[s] = { sections: clean(p.sections), shared: p.shared !== false };
      });
      if (raw && raw.cur && SLOTS.indexOf(raw.cur) >= 0) out.cur = raw.cur;
      if (raw && raw.autoW) out.autoW = raw.autoW;
      if (raw && raw.dirty) out.dirty = raw.dirty;
    } catch (_) {}
    return out;
  }
  function ensure() {
    if (S.plans && S.term === term() && S.owner === ownerId()) return;
    S.term = term(); S.owner = ownerId();
    var l = readLocal(lsKey());
    S.plans = l.plans; S.autoW = l.autoW; S.dirty = l.dirty; if (l.cur) S.cur = l.cur;
    S.adopt = false;
    if (S.owner !== 'anon') {
      var anon = readLocal(lsKey('anon'));
      S.adopt = SLOTS.some(function (x) { return anon.plans[x].sections.length; });
    }
  }
  function saveLocal() {
    try { localStorage.setItem(lsKey(), JSON.stringify({ plans: S.plans, cur: S.cur, autoW: S.autoW, dirty: S.dirty })); } catch (_) {}
  }
  function hasAny(pl) { return SLOTS.some(function (x) { return pl[x].sections.length; }); }
  /* The signed-out plans, offered to the account — never taken without asking. */
  function adoptAnon(keep) {
    var anon = readLocal(lsKey('anon')), lost = 0;
    if (keep) {
      SLOTS.forEach(function (x) {
        if (!anon.plans[x].sections.length) return;
        var slot = x;
        if (S.plans[slot].sections.length) slot = SLOTS.filter(function (y) { return !S.plans[y].sections.length; })[0];
        if (!slot) { lost += 1; return; }
        setSections(slot, anon.plans[x].sections);
      });
      if (lost) toast(lost + (lost === 1 ? ' plan wasn’t kept' : ' plans weren’t kept') + ' — Plans A, B and C were already full');
    }
    try { localStorage.removeItem(lsKey('anon')); } catch (_) {}
    S.adopt = false; refresh();
  }
  function clean(list) {
    var seen = {}, out = [];
    (Array.isArray(list) ? list : []).forEach(function (x) {
      if (!x) return;
      var code = String(x.code || '').trim().toUpperCase().replace(/\s+/g, ' ');
      var nbr = String(x.class_nbr || x.crn || '').trim();
      if (!code || !/^\d{3,6}$/.test(nbr) || seen[nbr]) return;
      seen[nbr] = 1; out.push({ code: code, class_nbr: nbr });
    });
    return out.slice(0, 12);
  }

  /* ---------------------------------------------------------------------------------------------
     Reading a section — the app's functions, never a parse of our own
     --------------------------------------------------------------------------------------------- */
  function rowsOf(code) { try { return ((typeof SEAT_SECTIONS !== 'undefined' && SEAT_SECTIONS) ? SEAT_SECTIONS[code] : null) || []; } catch (_) { return []; } }
  function rowOf(code, crn) { var r = rowsOf(code); for (var i = 0; i < r.length; i++) if (String(r[i].class_nbr || '').trim() === String(crn)) return r[i]; return null; }
  function compOf(r) {
    try { if (has('secComponent')) { var c = secComponent(r.section); if (c && c.label) return String(c.label).toUpperCase().slice(0, 3); } } catch (_) {}
    var m = /-(LEC|LAB|ACT|SEM|DIS|SUP|IND|STU)\b/i.exec(String((r && r.section) || ''));
    return m ? m[1].toUpperCase() : '';
  }
  function meetOf(r) {
    try { var d = has('prettyTime') ? prettyTime(r.days) : (r.days || ''); return has('parseMeet') ? parseMeet(d) : null; } catch (_) { return null; }
  }
  function isAsync(r) { try { return has('secIsAsync') ? !!secIsAsync(r) : /async/i.test(String(r.instruction_mode || '')); } catch (_) { return false; } }
  function overlap(a, b) { try { return has('meetsOverlap') ? meetsOverlap(a, b) : false; } catch (_) { return false; } }
  function unitsOf(code) {
    try { if (has('classInfo')) { var u = Number((classInfo(code) || {}).units); if (u > 0) return u; } } catch (_) {}
    return null;
  }
  function secNo(r) { var m = /(\d+)/.exec(String((r && r.section) || '')); return m ? m[1] : String((r && r.section) || '').split('-')[0]; }
  function nameOf(code) {
    try { if (has('fp_name')) { var n = fp_name(code); if (n) return n; } } catch (_) {}
    try { if (has('classInfo')) { var ci = classInfo(code); if (ci && ci.name) return ci.name; } } catch (_) {}
    return '';
  }
  function info(code, crn) {
    var r = rowOf(code, crn);
    var out = { code: code, crn: String(crn), row: r, missing: !r, units: unitsOf(code) };
    if (!r) return out;
    var cs = null;
    try { if (has('clsSections')) cs = clsSections(code).filter(function (s) { return s.class_nbr === String(crn); })[0] || null; } catch (_) {}
    out.sec = cs;
    out.meet = meetOf(r);
    out.async = isAsync(r);
    out.comp = compOf(r);
    out.no = secNo(r);
    out.label = code + '-' + (out.no || crn);
    out.rating = cs && cs.rating != null ? cs.rating : null;             // 0–4, shown through to5()
    out.seat = cs ? cs.seat : null;
    out.cap = r.capacity != null ? Math.max(0, +r.capacity) : null;
    out.when = cs && cs.days ? cs.days : (out.async ? 'No set meeting time' : 'Time TBA');
    out.prof = cs ? (has('cpDispName') ? cpDispName(cs.name, cs.pid) : cs.name) : '';
    out.pid = cs ? cs.pid : null;
    return out;
  }
  function five(v) { try { return has('to5') ? to5(v) : Math.round(v / 4 * 5 * 100) / 100; } catch (_) { return null; } }
  function rateHtml(v) {
    if (v == null) return '';
    var col = has('scoreColor') ? scoreColor(v) : 'var(--good)';
    return '<span class="pl2-rt" style="color:' + col + '">' + five(v).toFixed(1) + ' ★</span>';
  }
  function seatText(i) {
    if (!i || !i.seat) return '';
    try { var sp = has('seatParts') ? seatParts(i.seat) : null; if (sp && !sp.unknown) return sp.open; } catch (_) {}
    return '';
  }
  function opened() {
    var d = cfgv('REGISTRATION_OPENS'); if (!d) return false;
    try { return new Date() >= new Date(d + 'T00:00:00'); } catch (_) { return false; }
  }

  /* ---------------------------------------------------------------------------------------------
     Membership, and the watch that comes with it
     --------------------------------------------------------------------------------------------- */
  function plan(slot) { ensure(); return S.plans[slot] || { sections: [], shared: true }; }
  function slotsHaving(crn) { ensure(); return SLOTS.filter(function (s) { return S.plans[s].sections.some(function (x) { return x.class_nbr === String(crn); }); }); }
  function inAnyPlan(crn) { return slotsHaving(crn).length > 0; }
  function watched(code, crn) { try { return has('isWatchedSec') && isWatchedSec(code, crn); } catch (_) { return false; } }

  /* Adding a section to a plan watches it. Taking it out of every plan un-watches it ONLY if the
     plan was what watched it — a section the student had watched on its own before stays watched. */
  function syncOK() { var u = me(); return !u || watchesFor === String(u.id); }
  function resyncAll() {
    ensure();
    SLOTS.forEach(function (x) { S.plans[x].sections.forEach(function (y) { syncWatch(y.code, y.class_nbr); }); });
    saveLocal();
  }
  function syncWatch(code, crn) {
    try {
      /* Not before the account's own watches have arrived: a section the student watched on
         another device would look unwatched here, be marked as the plan's, and later be dropped. */
      if (!has('wcWatchSec') || !syncOK()) return;
      var inPlan = inAnyPlan(crn), w = watched(code, crn);
      if (inPlan && !w && rowOf(code, crn)) { wcWatchSec(code, crn, null, true); S.autoW[crn] = 1; }
      else if (!inPlan && w && S.autoW[crn]) { wcWatchSec(code, crn, null, true); delete S.autoW[crn]; }
      else if (!inPlan) delete S.autoW[crn];
    } catch (_) {}
  }

  function setSections(slot, list, why) {
    ensure();
    var prev = S.plans[slot].sections.slice();
    S.plans[slot].sections = clean(list);
    S.dirty[slot] = (S.dirty[slot] || 0) + 1;
    saveLocal();
    var touched = {};
    prev.concat(S.plans[slot].sections).forEach(function (x) { touched[x.class_nbr] = x.code; });
    Object.keys(touched).forEach(function (n) { syncWatch(touched[n], n); });
    saveLocal();
    push(slot);
    askInterest();
    refresh();
    return prev;
  }
  function add(slot, code, crn) {
    var l = plan(slot).sections.slice();
    if (l.some(function (x) { return x.class_nbr === String(crn); })) return false;
    if (l.length >= 12) { toast('Plan ' + slot + ' is full — 12 sections is the most a plan holds'); return false; }
    l.push({ code: code, class_nbr: String(crn) });
    setSections(slot, l, 'add');
    try { if (has('track')) track('plan_edit', null, null, { op: 'add', slot: slot }); } catch (_) {}
    return true;
  }
  function remove(slot, crn) {
    var l = plan(slot).sections.filter(function (x) { return x.class_nbr !== String(crn); });
    return setSections(slot, l, 'remove');
  }
  function replace(slot, fromCrn, code, toCrn) {
    var l = plan(slot).sections.map(function (x) { return x.class_nbr === String(fromCrn) ? { code: code, class_nbr: String(toCrn) } : x; });
    return setSections(slot, l, 'replace');
  }
  function setShared(slot, on) {
    ensure(); S.plans[slot].shared = !!on; S.dirty[slot] = (S.dirty[slot] || 0) + 1; saveLocal(); push(slot); refresh();
    try { if (has('track')) track('plan_share', null, null, { on: !!on }); } catch (_) {}
  }

  /* ---------------------------------------------------------------------------------------------
     The server — best effort, and honest about it
     --------------------------------------------------------------------------------------------- */
  function missingTable(err) {
    var c = String((err && err.code) || ''), m = String((err && err.message) || '');
    return c === '42P01' || c === 'PGRST205' || /does not exist|schema cache/i.test(m);
  }
  var pushT = {};
  function push(slot) {
    clearTimeout(pushT[slot]);
    pushT[slot] = setTimeout(function () { pushNow(slot); }, 350);
  }
  function pushNow(slot) {
    var u = me(), c = client();
    if (!u || !c) { S.server = 'local'; return Promise.resolve(false); }
    var p = plan(slot), t = term(), gen = S.dirty[slot];
    var q = p.sections.length
      ? c.from('plans').upsert({ user_id: u.id, term: t, slot: slot, sections: p.sections, shared: p.shared !== false }, { onConflict: 'user_id,term,slot' })
      : c.from('plans').delete().eq('user_id', u.id).eq('term', t).eq('slot', slot);
    return Promise.resolve(q).then(function (r) {
      if (r && r.error) {
        S.server = missingTable(r.error) ? 'missing' : 'error';
        if (S.server === 'error') toast('Couldn’t save Plan ' + slot + ' to your account — it’s kept on this device');
        refresh(); return false;
      }
      /* Only if nothing changed while this save was in flight — a newer edit keeps its flag. */
      if (ownerId() === String(u.id) && term() === t && S.dirty[slot] === gen) { delete S.dirty[slot]; saveLocal(); }
      S.server = 'ok'; return true;
    }, function () { S.server = 'error'; refresh(); return false; });
  }
  function load() {
    ensure();
    var u = me(), c = client();
    if (!u || !c) { S.server = 'local'; refresh(); return Promise.resolve(false); }
    var t = term();
    return Promise.resolve(c.from('plans').select('slot,sections,shared,updated_at').eq('user_id', u.id).eq('term', t)).then(function (r) {
      if (!r || r.error) { S.server = (r && missingTable(r.error)) ? 'missing' : 'error'; refresh(); return false; }
      if (term() !== t || ownerId() !== String(u.id)) return false;
      var got = {}, before = {};
      SLOTS.forEach(function (x) { S.plans[x].sections.forEach(function (y) { before[y.class_nbr] = y.code; }); });
      (r.data || []).forEach(function (row) { if (SLOTS.indexOf(row.slot) >= 0) got[row.slot] = row; });
      /* An edit that could not be saved is still this device's newest word on that slot, so it goes
         up rather than being overwritten. Every other slot follows the account — including a slot
         the account no longer has, which was emptied on another device and must not come back. */
      SLOTS.forEach(function (x) {
        if (S.dirty[x]) { pushNow(x); return; }
        var row = got[x];
        S.plans[x] = row ? { sections: clean(row.sections), shared: row.shared !== false } : { sections: [], shared: true };
      });
      S.server = 'ok';
      saveLocal();
      var after = {};
      SLOTS.forEach(function (x) { S.plans[x].sections.forEach(function (y) { after[y.class_nbr] = y.code; }); });
      Object.keys(before).forEach(function (n) { if (!after[n]) after[n] = before[n]; });
      Object.keys(after).forEach(function (n) { syncWatch(after[n], n); });
      saveLocal();
      askInterest(); loadFriendPlans();
      refresh();
      return true;
    }, function () { S.server = 'error'; refresh(); return false; });
  }

  /* "N in plans" — counts only, never who, and only at 3 or more. The server enforces the 3; this
     side just never shows an absent number as a zero. */
  var interestT = null, interestQueue = {};
  function askInterest(extra) {
    ensure();
    if (interestTerm !== term()) { interest = {}; interestAsked = {}; interestTerm = term(); }
    SLOTS.forEach(function (s) { S.plans[s].sections.forEach(function (x) { if (!interestAsked[x.class_nbr]) interestQueue[x.class_nbr] = 1; }); });
    (extra || []).forEach(function (n) { n = String(n); if (/^\d{3,6}$/.test(n) && !interestAsked[n]) interestQueue[n] = 1; });
    clearTimeout(interestT);
    interestT = setTimeout(function () {
      var list = Object.keys(interestQueue).slice(0, 300); interestQueue = {};
      var u = me(), c = client();
      if (!list.length || !u || !c) return;
      list.forEach(function (n) { interestAsked[n] = 1; });
      var t = term();
      Promise.resolve(c.rpc('plan_interest', { p_term: t, p_class_nbrs: list })).then(function (r) {
        if (!r || r.error || !Array.isArray(r.data) || t !== term()) return;
        var changed = false;
        r.data.forEach(function (x) { if (x && x.n >= SHOW_AT) { interest[String(x.class_nbr)] = x.n; changed = true; } });
        if (changed) { refresh(); try { if (has('cpRefresh')) cpRefresh(); } catch (_) {} }
      }, function () {});
    }, 250);
  }
  function interestOf(crn) { var n = interest[String(crn)]; return (n && n >= SHOW_AT) ? n : null; }
  function interestChip(crn) { var n = interestOf(crn); return n ? '<span class="pl2-chip" title="' + n + ' other TermChamp students have this section in a plan or on their watchlist">' + n + ' in plans</span>' : ''; }

  /* Friends' shared plans for this term — RLS returns only accepted friends' rows with the toggle on. */
  function loadFriendPlans() {
    var u = me(), c = client(); if (!u || !c) return Promise.resolve(null);
    var t = term();
    return Promise.resolve(c.from('plans').select('user_id,slot,sections').eq('term', t).neq('user_id', u.id)).then(function (r) {
      if (!r || r.error || !Array.isArray(r.data) || t !== term()) return null;
      friendPlans = r.data; friendPlansFor = {};
      r.data.forEach(function (row) { (friendPlansFor[row.user_id] = friendPlansFor[row.user_id] || []).push(row); });
      refresh();
      return friendPlans;
    }, function () { return null; });
  }
  function friendById(id) { try { return (FRIENDS || []).filter(function (f) { return f && f.id === id; })[0] || null; } catch (_) { return null; } }
  /* Friends with this exact section in a shared plan, or enrolled in it. */
  function friendsOn(code, crn) {
    var out = [], seen = {};
    (friendPlans || []).forEach(function (row) {
      if (seen[row.user_id]) return;
      if ((row.sections || []).some(function (x) { return String(x.class_nbr) === String(crn); })) {
        var f = friendById(row.user_id); if (f) { seen[row.user_id] = 1; out.push(f); }
      }
    });
    try {
      (FRIENDS || []).forEach(function (f) {
        if (!f || seen[f.id] || (f.classes || []).indexOf(code) < 0) return;
        if (has('friendSectionRel') && friendSectionRel(f, code, [String(crn)]) === 'same') { seen[f.id] = 1; out.push(f); }
      });
    } catch (_) {}
    return out;
  }
  function first(n) { return String(n || '').split(/\s+/)[0]; }
  function faces(list) {
    if (!list.length) return '';
    return '<span class="pl2-faces" title="' + esc(list.map(function (f) { return f.name; }).join(', ')) + '">' + list.slice(0, 3).map(function (f) {
      var ini = f.ini || (has('hmIni') ? hmIni(f.name) : String(f.name || '?').slice(0, 2).toUpperCase());
      var col = has('hmFriendColor') ? hmFriendColor(f) : '#5E7A8A';
      return '<span class="pl2-face" style="background:' + esc(col) + '">' + esc(ini) + '</span>';
    }).join('') + '</span>';
  }

  /* ---------------------------------------------------------------------------------------------
     A plan's week, and what it says about itself
     --------------------------------------------------------------------------------------------- */
  var DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr'];
  var DAY_WORD = { Mo: 'Mondays', Tu: 'Tuesdays', We: 'Wednesdays', Th: 'Thursdays', Fr: 'Fridays' };
  function planInfo(slot) {
    var items = plan(slot).sections.map(function (x) { return info(x.code, x.class_nbr); });
    var units = 0, unitsKnown = true, rated = [], clashes = [], used = {}, unplaced = 0, codes = {};
    items.forEach(function (i) {
      if (!codes[i.code]) { codes[i.code] = 1; if (i.units) units += i.units; else unitsKnown = false; }
      if (i.rating != null) rated.push(i.rating);
      if (i.meet) i.meet.days.forEach(function (d) { used[d] = 1; });
      else if (!i.async) unplaced += 1;
    });
    for (var a = 0; a < items.length; a++) for (var b = a + 1; b < items.length; b++) {
      if (items[a].meet && items[b].meet && overlap(items[a].meet, items[b].meet)) clashes.push([items[a], items[b]]);
    }
    var off = unplaced ? [] : DAYS.filter(function (d) { return !used[d]; });
    var ge = {};
    Object.keys(codes).forEach(function (c) { try { if (has('geAreasFor')) geAreasFor(c).forEach(function (k) { ge[k] = 1; }); } catch (_) {} });
    return {
      items: items, units: units, unitsKnown: unitsKnown,
      avg: rated.length ? rated.reduce(function (s, v) { return s + v; }, 0) / rated.length : null,
      clashes: clashes, off: items.length ? off : [], ge: Object.keys(ge).sort(), unplaced: unplaced
    };
  }
  function unitsLabel(pi) { return pi.items.length ? (pi.units + (pi.unitsKnown ? '' : '+') + 'u') : '—'; }

  function weekStrip(items) {
    var placed = items.filter(function (i) { return i.meet; });
    if (!placed.length) return '';
    var lo = 24 * 60, hi = 0;
    placed.forEach(function (i) { lo = Math.min(lo, i.meet.start); hi = Math.max(hi, i.meet.end); });
    lo = Math.floor(lo / 60) * 60; hi = Math.ceil(hi / 60) * 60; if (hi - lo < 240) hi = Math.min(1440, lo + 240);
    return '<div class="pl2-week" aria-hidden="true">' + DAYS.map(function (d) {
      var blocks = placed.filter(function (i) { return i.meet.days.indexOf(d) >= 0; }).map(function (i) {
        return '<span class="pl2-blk" title="' + esc(i.label) + '" style="top:' + ((i.meet.start - lo) / (hi - lo) * 100).toFixed(1) + '%;height:'
          + Math.max(4, (i.meet.end - i.meet.start) / (hi - lo) * 100).toFixed(1) + '%"></span>';
      }).join('');
      return '<div class="pl2-wcol"><span class="pl2-wday">' + d.charAt(0) + '</span><div class="pl2-lane' + (blocks ? '' : ' pl2-lane--off') + '">' + blocks + '</div></div>';
    }).join('') + '</div>';
  }

  /* ---------------------------------------------------------------------------------------------
     Backups (item 2): the best-rated other section of the same course and component that fits the
     plan's week alongside everything else in it and isn't full. Ties go to more open seats.
     --------------------------------------------------------------------------------------------- */
  function fitsWith(meet, asyncRow, others) {
    if (!meet) return asyncRow;                        // no time and not async: cannot be checked, so not offered
    return !others.some(function (o) { return o.meet && overlap(meet, o.meet); });
  }
  function siblings(i) {
    return rowsOf(i.code).filter(function (r) { return compOf(r) === i.comp && String(r.class_nbr).trim() !== i.crn; });
  }
  function backupFor(slot, crn) {
    var pi = planInfo(slot);
    var i = pi.items.filter(function (x) { return x.crn === String(crn); })[0];
    if (!i || i.missing) return null;
    var others = pi.items.filter(function (x) { return x.crn !== i.crn; });   // the course's own lab or lecture counts too
    var cands = siblings(i).map(function (r) { return info(i.code, String(r.class_nbr).trim()); }).filter(function (c) {
      if (c.seat && c.seat.cls === 'full') return false;
      return fitsWith(c.meet, c.async, others);
    });
    cands.sort(function (a, b) {
      var ra = a.rating != null ? a.rating : UNRATED, rb = b.rating != null ? b.rating : UNRATED;
      if (rb !== ra) return rb - ra;
      return ((b.seat && b.seat.n) || 0) - ((a.seat && a.seat.n) || 0);
    });
    var lab = i.comp === 'LEC' && rowsOf(i.code).some(function (r) { var k = compOf(r); return k && k !== 'LEC'; });
    return { best: cands[0] || null, fitting: cands.length, needsLab: lab };
  }

  /* ---------------------------------------------------------------------------------------------
     The game plan (item 1): register first whatever you would lose most. Every reason is a fact.
     --------------------------------------------------------------------------------------------- */
  function gamePlan(slot) {
    ensure();
    slot = slot || S.cur;
    var pi = planInfo(slot), live = opened();
    var steps = pi.items.filter(function (i) { return !i.missing; }).map(function (i) {
      var others = pi.items.filter(function (x) { return x.crn !== i.crn; });   // the course's own lab or lecture counts too
      var sib = siblings(i);
      /* An alternative is a section that fits the week AND is not full — the same test the backup
         uses, so "1 other section fits" never sits above "No backup fits". */
      var fitAll = sib.filter(function (r) { var m = meetOf(r); return fitsWith(m, isAsync(r), others); });
      var fitN = fitAll.filter(function (r) { var st = has('secSeat') ? secSeat(r) : null; return !(st && st.cls === 'full'); }).length;
      var offered = sib.length + 1;
      var reasons = [], score = 0;
      var tbaN = sib.filter(function (r) { return !meetOf(r) && !isAsync(r); }).length;
      if (!fitN) {
        /* A sibling with no time on record might fit — "only" would overclaim, so it says so. */
        var t0 = fitAll.length ? 'Only open section that fits your week'
          : (tbaN ? 'No other section with a set time fits' : 'Only section that fits your week');
        reasons.push({ t: t0, hot: true }); score += tbaN ? 700 : 1000;
      }
      else if (fitN === 1) { reasons.push({ t: '1 other section fits' }); score += 200; }
      else reasons.push({ t: (fitN + 1) + ' of ' + offered + ' sections fit' });
      if (live && i.seat && !i.seat.unknown) {
        if (i.seat.cls === 'full' || i.seat.cls === 'wait') { reasons.unshift({ t: 'Full now — waitlist', hot: true }); score += 800; }
        else if (i.seat.n != null) score += Math.max(0, 60 - Math.min(i.seat.n, 60)) * 3;
      } else if (i.cap != null) {
        score += Math.max(0, 100 - Math.min(i.cap, 100)) * 1.5;   // smaller sections fill first
      }
      if (offered <= 2) { reasons.push({ t: offered === 1 ? 'Only section offered' : 'Only 2 sections offered' }); score += 20; }
      var n = interestOf(i.crn); if (n) { reasons.push({ t: n + ' in plans' }); score += Math.min(n, 30) * 2; }
      var fr = friendsOn(i.code, i.crn);
      if (fr.length) { reasons.push({ t: fr.slice(0, 2).map(function (f) { return first(f.name); }).join(' + ') + (fr.length > 2 ? ' +' + (fr.length - 2) : '') + ' planning it' }); score += fr.length; }
      var seatLine = live ? seatText(i) : (i.cap != null ? i.cap + ' seats' : '');
      var mine = null;
      try {
        if (has('isMineSec') && isMineSec(i.code, i.crn)) {
          var m = (myClassMeta[i.code] || {}).secs || [];
          var rec = m.filter(function (x) { return String(x.crn) === i.crn; })[0];
          mine = rec && rec.status === 'waitlisted' ? 'waitlisted' : 'enrolled';
        }
      } catch (_) {}
      return { i: i, reasons: reasons, score: score, seatLine: seatLine, backup: backupFor(slot, i.crn), friends: fr, mine: mine };
    });
    steps.sort(function (a, b) { return b.score - a.score || String(a.i.label).localeCompare(String(b.i.label)); });
    /* Round 1 caps what you can enroll in. Taken in order, a class that would push past 16 units
       waits for Round 2 — so the riskiest classes are the ones that make Round 1. */
    var r1 = 0, w1 = 0, seenCode = {};
    steps.forEach(function (s) {
      var u = seenCode[s.i.code] ? 0 : (s.i.units || 0);
      var toWait = live && s.i.seat && (s.i.seat.cls === 'full' || s.i.seat.cls === 'wait');
      if (toWait) {
        if (w1 + u <= ROUND1_WAIT) { s.round = 1; s.wait = true; w1 += u; seenCode[s.i.code] = 1; } else s.round = 2;
      } else if (r1 + u <= ROUND1_UNITS) { s.round = 1; r1 += u; seenCode[s.i.code] = 1; }
      else s.round = 2;
    });
    /* The greedy split can interleave (4,4,4,5,4 units → rounds 1,1,1,2,1). Group by round, keeping
       the risk order inside each, so nothing that goes in Round 1 is drawn under the Round 2 line. */
    steps = steps.map(function (s, ix) { return { s: s, ix: ix }; })
      .sort(function (a, b) { return (a.s.round - b.s.round) || (a.ix - b.ix); })
      .map(function (x) { return x.s; });
    var regTerm = cfgv('REGISTRATION_TERM');
    return {
      slot: slot, steps: steps, units: pi.units, unitsKnown: pi.unitsKnown, r1Units: r1, w1Units: w1, inRound1: inRound1(),
      split: steps.some(function (s) { return s.round === 2; }), live: live,
      preview: !!(regTerm && regTerm !== termLabel()), regTerm: regTerm, termLabel: termLabel(),
      missing: pi.items.filter(function (i) { return i.missing; }).length,
      asOf: seatsAsOf()
    };
  }
  function seatsAsOf() {
    try { if (typeof SEATS_UPDATED_AT !== 'undefined' && SEATS_UPDATED_AT) return new Date(SEATS_UPDATED_AT); } catch (_) {}
    return null;
  }
  function clockOf(d) {
    try { return d.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' }); } catch (_) { return ''; }
  }
  function niceDay(ymd) {
    try { return new Date(ymd + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }); } catch (_) { return ymd; }
  }
  function roundLine() {
    var r1 = cfgv('REGISTRATION_OPENS'), r2 = cfgv('REGISTRATION_ROUND2'), oe = cfgv('OPEN_ENROLLMENT');
    var now = new Date();
    function past(d) { return d && now >= new Date(d + 'T00:00:00'); }
    if (r1 && !past(r1)) return 'Round 1 opens ' + niceDay(r1) + ' · by appointment';
    if (r2 && !past(r2)) return 'Round 1 is open · Round 2 begins ' + niceDay(r2);
    if (oe && !past(oe)) return 'Round 2 is open · Open Enrollment begins ' + niceDay(oe);
    if (oe) return 'Open Enrollment is open';
    return '';
  }
  function inRound1() { var r2 = cfgv('REGISTRATION_ROUND2'); return !r2 || new Date() < new Date(r2 + 'T00:00:00'); }

  /* The appointment time: typed by the student from the Portal, kept on this device, used for a
     countdown and nothing else. TermChamp cannot read it and does not pretend to. */
  function apptKey() { return 'professify_appt_' + term(); }
  function appt() { try { var v = localStorage.getItem(apptKey()); return v ? new Date(v) : null; } catch (_) { return null; } }
  function countdown(d) {
    var ms = d - new Date(); if (isNaN(ms)) return '';
    if (ms <= 0) return 'now';
    var h = Math.floor(ms / 3600000), dd = Math.floor(h / 24);
    return dd ? ('in ' + dd + ' day' + (dd === 1 ? '' : 's') + (h % 24 ? ', ' + (h % 24) + ' h' : '')) : (h ? 'in ' + h + ' h' : 'in ' + Math.max(1, Math.round(ms / 60000)) + ' min');
  }

  /* =============================================================================================
     REDESIGN (Tate, 2026-09-25): "we've made it a bit too complicated."
       · Plans = the plan as a WEEK, and nothing else. Edit plan / Game plan.
       · Planner = where a plan is BUILT: "Classes you need" on one side, the week on the other;
         hover (or tap) a class and every section of it that fits your open time appears on the
         week as a green block — click one to add it.
     Contrast and simplicity come first (Tate): every colour here is a theme token whose ratio was
     measured in dark, light and cream (plans.css says which), nothing is smaller than --t-label,
     one primary action per screen, and green means only "fits / add it" and the primary button.
     design: claude/plans-and-planner-simplified-2026-09-25.md
     ============================================================================================= */
  var DAY_NAME = { Mo: 'Mon', Tu: 'Tue', We: 'Wed', Th: 'Thu', Fr: 'Fri' };
  var COMP_WORD = { LEC: 'lecture', LAB: 'lab', ACT: 'activity', SEM: 'seminar', DIS: 'discussion', SUP: 'supervision', IND: 'independent study', STU: 'studio' };
  function compWord(k) { return COMP_WORD[k] || 'section'; }
  function hourLabel(h) { return ((h + 11) % 12 + 1) + (h < 12 ? 'a' : 'p'); }
  function clockMin(m) { var h = Math.floor(m / 60), mi = m % 60; return ((h + 11) % 12 + 1) + (mi ? ':' + (mi < 10 ? '0' : '') + mi : '') + (h < 12 ? 'am' : 'pm'); }
  function dayLetters(meet) { return meet.days.map(function (d) { return d; }).join(''); }
  function whenShort(i) { return i.meet ? dayLetters(i.meet) + ' ' + clockMin(i.meet.start) : (i.async ? 'Online, no set time' : 'Time TBA'); }

  /* Side-by-side lanes when two things share an hour (a clash, or two green options). */
  function laneOut(list) {
    list.sort(function (a, b) { return a.s - b.s || a.e - b.e; });
    var ends = [];
    list.forEach(function (x) {
      var k = 0; while (k < ends.length && ends[k] > x.s) k += 1;
      x.lane = k; ends[k] = x.e;
    });
    list.forEach(function (x) {
      var n = 0; list.forEach(function (y) { if (y.s < x.e && x.s < y.e) n = Math.max(n, y.lane + 1); });
      x.lanes = Math.max(n, x.lane + 1);
    });
  }

  /* The week. items = plan sections (info), ghosts = sections that would fit (info), edit = Planner. */
  function mergeSameTime(ghosts) {
    var byKey = {}, out = [];
    ghosts.forEach(function (i) {                        // already best-rated first (fitFor sorts)
      var k = i.meet ? i.meet.days.join('') + '|' + i.meet.start + '|' + i.meet.end : 'x' + i.crn;
      if (byKey[k]) { byKey[k].more = (byKey[k].more || 0) + 1; return; }
      var c = {}; Object.keys(i).forEach(function (x) { c[x] = i[x]; }); c.more = 0; byKey[k] = c; out.push(c);
    });
    return out;
  }
  function weekHtml(slot, items, ghosts, edit) {
    ghosts = mergeSameTime(ghosts);
    var focusable = {};
    var lo = 8 * 60, hi = 18 * 60;
    items.concat(ghosts).forEach(function (i) { if (i.meet) { lo = Math.min(lo, Math.floor(i.meet.start / 60) * 60); hi = Math.max(hi, Math.ceil(i.meet.end / 60) * 60); } });
    var span = hi - lo, pct = function (m) { return ((m - lo) / span * 100).toFixed(2) + '%'; };
    var clashes = {};
    for (var a = 0; a < items.length; a++) for (var b = a + 1; b < items.length; b++) {
      if (items[a].meet && items[b].meet && overlap(items[a].meet, items[b].meet)) { clashes[items[a].crn] = 1; clashes[items[b].crn] = 1; }
    }
    var h = '<div class="pl3-week' + (edit ? ' pl3-week--edit' : '') + '" role="group" aria-label="Plan ' + slot + ', week">'
      + '<div class="pl3-head"><span></span>' + DAYS.map(function (d) { return '<span>' + DAY_NAME[d] + '</span>'; }).join('') + '</div>'
      + '<div class="pl3-grid"><div class="pl3-gut">';
    for (var hr = lo / 60; hr <= hi / 60; hr += 2) h += '<span style="top:' + pct(hr * 60) + '">' + hourLabel(hr) + '</span>';
    h += '</div>';
    DAYS.forEach(function (d) {
      var cells = [];
      items.forEach(function (i) { if (i.meet && i.meet.days.indexOf(d) >= 0) cells.push({ i: i, s: i.meet.start, e: i.meet.end, ghost: false }); });
      ghosts.forEach(function (i) { if (i.meet && i.meet.days.indexOf(d) >= 0) cells.push({ i: i, s: i.meet.start, e: i.meet.end, ghost: true }); });
      laneOut(cells);
      h += '<div class="pl3-col">';
      for (var r = lo / 60 + 1; r < hi / 60; r += 1) h += '<i class="pl3-line" style="top:' + pct(r * 60) + '"></i>';
      cells.forEach(function (c) {
        var i = c.i, pos = 'top:' + pct(c.s) + ';height:' + ((c.e - c.s) / span * 100).toFixed(2) + '%;left:calc(' + (c.lane / c.lanes * 100).toFixed(2) + '% + 2px);width:calc(' + (100 / c.lanes).toFixed(2) + '% - 4px)';
        var time = clockMin(c.s) + '–' + clockMin(c.e);
        if (c.ghost) {
          var r5 = i.rating != null ? five(i.rating).toFixed(1) + '★' : '';
          var tab = focusable[i.crn] ? ' tabindex="-1"' : ''; focusable[i.crn] = 1;
          h += '<button type="button" class="pl3-ghost" style="' + pos + '"' + tab + ' data-pl-act="ghost" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '"'
            + ' aria-label="Add ' + esc(i.label) + ', ' + esc(dayLetters(i.meet) + ' ' + time) + (i.prof ? ', ' + esc(i.prof) : '') + (r5 ? ', rated ' + r5 : '')
            + (i.more ? ', the best-rated of ' + (i.more + 1) + ' sections at this time' : '') + ', to Plan ' + slot + '">'
            + '<b><span class="pl3-gcode">' + esc(i.code) + '</span>' + esc(i.no ? '-' + i.no : '') + (i.more ? ' +' + i.more : '') + '</b><span>' + esc([r5, seatText(i)].filter(Boolean).join(' · ')) + '</span></button>';
        } else if (edit) {
          h += '<div class="pl3-blk' + (clashes[i.crn] ? ' pl3-blk--clash' : '') + '" style="' + pos + '"><b>' + esc(i.code) + '</b><span>' + esc(time) + '</span>'
            + '<button type="button" class="pl3-rm" data-pl-act="rm" data-slot="' + slot + '" data-crn="' + esc(i.crn) + '" aria-label="Remove ' + esc(i.label) + ' from Plan ' + slot + '">×</button></div>';
        } else {
          h += '<button type="button" class="pl3-blk' + (clashes[i.crn] ? ' pl3-blk--clash' : '') + '" style="' + pos + '" data-pl-act="open" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '"'
            + ' aria-label="' + esc(i.label + ', ' + dayLetters(i.meet) + ' ' + time + (clashes[i.crn] ? ', clashes with another class' : '')) + '"><b>' + esc(i.code) + '</b><span>' + esc(time) + '</span></button>';
        }
      });
      h += '</div>';
    });
    h += '</div>';
    /* Online / no-set-time sections have no place on a grid; they get one quiet line each. */
    var loose = items.filter(function (i) { return !i.meet; }), gl = ghosts.filter(function (i) { return !i.meet; });
    if (loose.length || gl.length) {
      h += '<div class="pl3-loose">' + loose.map(function (i) {
        return '<span class="pl3-lchip">' + esc(i.missing ? i.code + ' · no longer offered' : i.label + ' · ' + whenShort(i))
          + (edit ? '<button type="button" class="pl3-rm pl3-rm--in" data-pl-act="rm" data-slot="' + slot + '" data-crn="' + esc(i.crn) + '" aria-label="Remove ' + esc(i.label || i.code) + ' from Plan ' + slot + '">×</button>' : '') + '</span>';
      }).join('') + gl.map(function (i) {
        return '<button type="button" class="pl3-ghost pl3-ghost--loose" data-pl-act="ghost" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '">＋ ' + esc(i.label) + ' · online' + (i.rating != null ? ' · ' + five(i.rating).toFixed(1) + '★' : '') + '</button>';
      }).join('') + '</div>';
    }
    return h + '</div>';
  }

  function summary(pi) {
    var bits = [], n = {};
    pi.items.forEach(function (i) { n[i.code] = 1; });
    var k = Object.keys(n).length;
    bits.push(k + (k === 1 ? ' class' : ' classes'));
    bits.push(pi.units + (pi.unitsKnown ? '' : '+') + ' units');
    bits.push(pi.clashes.length ? pi.clashes.length + (pi.clashes.length === 1 ? ' clash' : ' clashes') : 'no clashes');
    if (pi.off.length && pi.off.length < 5) bits.push(pi.off.map(function (d) { return DAY_NAME[d]; }).join(' & ') + ' free');
    return bits.join(' · ');
  }
  function pillsHtml(act) {
    return '<div class="pl3-pills" role="group" aria-label="Plans">' + SLOTS.map(function (s) {
      var q = planInfo(s), on = s === S.cur;
      return '<button type="button" aria-pressed="' + on + '" class="pl3-pill' + (on ? ' on' : '') + '" data-pl-act="' + act + '" data-slot="' + s + '">'
        + '<b>Plan ' + s + '</b><span>' + (q.items.length ? q.units + (q.unitsKnown ? '' : '+') + ' units' : 'empty') + '</span></button>';
    }).join('') + '</div>';
  }
  function notesHtml() {
    var h = '';
    if (S.adopt) h += '<div class="pl3-note pl3-note--act">You made plans on this device before signing in. Keep them in your account? Friends can see them, like your other plans. '
      + '<span class="pl3-row"><button type="button" class="btn primary" data-pl-act="adopt-yes">Keep them</button><button type="button" class="btn" data-pl-act="adopt-no">Discard</button></span></div>';
    if (undoBox) h += '<div class="pl3-note pl3-note--undo" role="status">' + esc(undoBox.text) + ' <button type="button" class="pl3-link" data-pl-act="undo">Undo</button></div>';
    return h;
  }

  /* ---- the Plans tab: your week -------------------------------------------------------------- */
  function paneHtml() {
    ensure();
    var slot = S.cur, p = plan(slot), pi = planInfo(slot);
    var h = '<div class="pl3">' + notesHtml() + pillsHtml('cur');
    if (!pi.items.length) {
      h += '<div class="pl3-emptywrap">' + weekHtml(slot, [], [], false)
        + '<div class="pl3-empty"><b>Nothing in Plan ' + slot + ' yet</b><span>Planner shows the classes you need and where each one fits.</span>'
        + '<button type="button" class="btn primary pl3-cta" data-pl-act="edit" data-slot="' + slot + '">Build Plan ' + slot + '</button></div></div>';
    } else {
      h += '<p class="pl3-sum">' + esc(summary(pi)) + '</p>' + weekHtml(slot, pi.items, [], false)
        + '<div class="pl3-acts"><button type="button" class="btn pl3-btn2" data-pl-act="edit" data-slot="' + slot + '">Edit plan</button>'
        + '<button type="button" class="btn primary" data-pl-act="gameplan" data-slot="' + slot + '">Game plan</button></div>';
    }
    if (me()) {
      h += '<label class="pl3-share"><input type="checkbox" data-pl-act="share" data-slot="' + slot + '"' + (p.shared !== false ? ' checked' : '') + '>'
        + '<span class="pl3-sw" aria-hidden="true"></span><span>Friends can see Plan ' + slot + '</span></label>';
      if (S.server === 'missing' || S.server === 'error') h += '<p class="pl3-quiet">Saved on this device — it couldn’t be saved to your account just now.</p>';
    } else {
      h += '<p class="pl3-quiet">Plans are kept on this device. Sign in to keep them everywhere and share them with friends.</p>';
    }
    return h + '</div>';
  }

  /* ---- Planner: build the plan --------------------------------------------------------------- */
  var B = { hov: null, sel: null, q: '', deg: false, more: {} };
  var dwellT = null, lastScroll = 0;

  /* The sections of the course's NEXT missing component (lecture first, then lab) that fit
     everything already in the plan and are not full. A course the plan already covers → null. */
  function fitFor(code, slot) {
    var pi = planInfo(slot), rows = rowsOf(code);
    if (!rows.length) return { offered: false, list: [], fullN: 0 };
    var have = {}, comps = [];
    pi.items.forEach(function (i) { if (i.code === code) have[i.comp || '?'] = 1; });
    rows.forEach(function (r) { var k = compOf(r) || '?'; if (comps.indexOf(k) < 0) comps.push(k); });
    comps.sort(function (x, y) { return (x === 'LEC' ? 0 : 1) - (y === 'LEC' ? 0 : 1); });
    var need = comps.filter(function (k) { return !have[k]; })[0];
    if (!need) return null;
    var others = pi.items, fullN = 0, tbaN = 0, list = [];
    rows.forEach(function (r) {
      if ((compOf(r) || '?') !== need) return;
      var i = info(code, String(r.class_nbr).trim());
      if (!i.meet && !i.async) { tbaN += 1; return; }      // no time on record: can't be placed, and isn't "doesn't fit"
      if (!fitsWith(i.meet, i.async, others)) return;
      if (i.seat && i.seat.cls === 'full') { fullN += 1; return; }
      list.push(i);
    });
    list.sort(function (a, b) { return (b.rating != null ? b.rating : UNRATED) - (a.rating != null ? a.rating : UNRATED); });
    return { offered: true, comp: need, partial: !!Object.keys(have).length, list: list, fullN: fullN, tbaN: tbaN };
  }

  function geKeyOfTitle(title) {
    var t = String(title || '');
    if (!/\bGE\b/i.test(t)) return null;
    if (/Upper-?Division/i.test(t)) { var u = t.match(/Area\s*(\d)/i); if (!u) return null; return (u[1] === '2' || u[1] === '5') ? 'U25' : 'UD' + u[1]; }
    var m = t.match(/\(([0-9]+[A-C]?)\)/); if (m) return m[1].toUpperCase();
    m = t.match(/Area\s*([0-9]+[A-C]?)/i); return m ? m[1].toUpperCase() : null;
  }
  function takenCodes() {
    var s = {};
    try { if (has('completedCodes')) completedCodes().forEach(function (c) { s[c] = 1; }); } catch (_) {}
    return s;
  }

  /* "Classes you need", in the order a student would reach for them. */
  function needGroups(slot) {
    var pi = planInfo(slot), inPlan = {}, taken = takenCodes(), seen = {}, groups = [];
    pi.items.forEach(function (i) { inPlan[i.code] = 1; });
    function row(code, why) {
      if (seen[code] || taken[code]) return null;
      var f = fitFor(code, slot);
      if (f === null || !f.offered) return null;
      seen[code] = 1;
      return { code: code, name: nameOf(code) || code, why: f.partial ? 'Pick a ' + compWord(f.comp) : why, fit: f };
    }
    var finish = [];
    Object.keys(inPlan).forEach(function (c) { var f = fitFor(c, slot); if (f && f.offered) { seen[c] = 1; finish.push({ code: c, name: nameOf(c) || c, why: 'Pick a ' + compWord(f.comp), fit: f }); } else seen[c] = 1; });
    if (finish.length) groups.push({ title: 'Finish these', rows: finish });
    var L = null;
    try { if (has('plLedgerCompute')) L = plLedgerCompute(); } catch (_) {}
    if (L && L.led) {
      var major = [];
      (L.led.need || []).forEach(function (sl) { (sl.codes || []).forEach(function (c) { var r = row(c, 'Your major'); if (r) major.push(r); }); });
      if (major.length) groups.push({ title: 'Your major', rows: major });
      var keys = [];
      (L.led.needU || []).forEach(function (sl) { var k = geKeyOfTitle(sl && sl.title); if (k && keys.indexOf(k) < 0) keys.push(k); });
      keys.forEach(function (k) {
        var all = [];
        try { (GE_COURSES || []).forEach(function (c) { if (c && String(c.areaKey || '').toUpperCase() === k) { var r = row(c.code, 'GE ' + k); if (r && r.fit.list.length) all.push(r); } }); } catch (_) {}
        all.sort(function (a, b) { return (b.fit.list[0].rating != null ? b.fit.list[0].rating : UNRATED) - (a.fit.list[0].rating != null ? a.fit.list[0].rating : UNRATED); });
        if (all.length) groups.push({ title: 'GE ' + k, rows: all, cap: 3, key: 'ge' + k });
      });
    }
    var saved = [];
    try { (watchClasses || []).forEach(function (c) { var r = row(c, 'Saved'); if (r) saved.push(r); }); } catch (_) {}
    if (saved.length) groups.push({ title: 'Saved', rows: saved });
    return { groups: groups, noMajor: !(L && L.led) };
  }
  function searchRows(q, slot) {
    q = q.trim().toLowerCase(); if (!q) return [];
    var out = [], codes = [];
    try { codes = Object.keys(SEAT_SECTIONS || {}); } catch (_) {}
    var qn = q.replace(/\s+/g, '');
    codes.forEach(function (c) {
      if (out.length >= 12) return;
      var nm = (nameOf(c) || '').toLowerCase();
      if (c.toLowerCase().replace(/\s+/g, '').indexOf(qn) === 0 || nm.indexOf(q) >= 0) {
        var f = fitFor(c, slot);
        if (f === null) out.push({ code: c, name: nameOf(c) || c, why: 'In Plan ' + slot, fit: { list: [], inPlan: true } });
        else if (f.offered) out.push({ code: c, name: nameOf(c) || c, why: '', fit: f });
      }
    });
    return out;
  }
  function needRowHtml(r) {
    var n = r.fit.list.length, on = (B.sel === r.code), hov = (B.hov === r.code);
    return '<button type="button" class="pl3-need' + (on || hov ? ' on' : '') + (n ? '' : ' pl3-need--none') + '" data-pl-act="need" data-code="' + esc(r.code) + '" aria-pressed="' + (on || hov) + '">'
      + '<span class="pl3-nmain"><span class="pl3-code">' + esc(r.code) + '</span><span class="pl3-nname">' + esc(r.name) + '</span></span>'
      + '<span class="pl3-nside">' + (r.why ? '<span class="pl3-tag">' + esc(r.why) + '</span>' : '')
      + (r.fit.inPlan ? '' : '<span class="pl3-fitn">' + (n ? n + (n === 1 ? ' fits' : ' fit') : (r.fit.tbaN && !r.fit.fullN ? 'no time yet' : 'none fit')) + '</span>') + '</span></button>';
  }
  /* Which class is being previewed, and the line that says what to do with it. */
  function focusCode() { return B.hov || B.sel; }
  function builderWeek(slot) {
    var pi = planInfo(slot), code = focusCode(), ghosts = [], hint;
    if (code) {
      var f = fitFor(code, slot);
      ghosts = f && f.list ? f.list : [];
      var extra = [];
      if (f && f.fullN) extra.push(f.fullN + ' more ' + (f.fullN === 1 ? 'is' : 'are') + ' full');
      if (f && f.tbaN) extra.push(f.tbaN + (f.tbaN === 1 ? ' has' : ' have') + ' no time yet');
      var tail = extra.length ? ' (' + extra.join(', ') + ')' : '';
      if (!f) hint = code + ' is already in Plan ' + slot + '.';
      else if (!ghosts.length) hint = (f.tbaN && !f.fullN && !rowsOf(code).some(function (r) { return meetOf(r) || isAsync(r); }))
        ? code + ' has no meeting times posted yet, so it can’t be placed.'
        : 'Nothing of ' + code + ' fits around Plan ' + slot + tail + '.';
      else { var spots = mergeSameTime(ghosts).length; hint = code + (f.partial ? ' ' + compWord(f.comp) : '') + ' fits in ' + spots + (spots === 1 ? ' spot' : ' spots')
        + (spots !== ghosts.length ? ' (' + ghosts.length + ' sections)' : '') + tail + '. '
        + (hoverDevice() ? 'Click' : 'Tap') + ' a green block to add it.'
        + (f.partial && f.comp !== 'LEC' ? ' Check Cal Poly’s schedule for which ' + compWord(f.comp) + ' goes with your lecture.' : ''); }
    } else {
      hint = pi.items.length ? (hoverDevice() ? 'Point at a class to see where it fits.' : 'Tap a class to see where it fits.') : 'Pick a class you need to see where it fits.';
    }
    return '<p class="pl3-hint' + (code ? ' pl3-hint--on' : '') + '" role="status">' + esc(hint) + '</p>' + weekHtml(slot, pi.items, ghosts, true);
  }
  function builderHtml() {
    ensure();
    var slot = S.cur;
    return '<div class="pl3 pl3-builder" data-slot="' + slot + '"><div id="pl3BNotes">' + notesHtml() + '</div>'
      + '<div class="pl3-bhead"><div><h2 class="pl3-title">Building Plan ' + slot + '</h2><p class="pl3-sum" id="pl3BSum"></p></div>'
      + '<button type="button" class="btn primary pl3-done" data-pl-act="done">Done</button></div>'
      + '<div id="pl3BPills">' + pillsHtml('bslot') + '</div>'
      + '<div class="pl3-bgrid"><div class="pl3-bweek" id="pl3BWeek"></div>'
      + '<div class="pl3-side" id="pl3BSide"><h3 class="pl3-h">Classes you need</h3>'
      + '<label class="pl3-search"><span class="sr-only">Find any class</span><input type="search" data-pl-act="q" placeholder="Find any class…" value="' + esc(B.q) + '" autocomplete="off"></label>'
      + '<div id="pl3BList"></div></div></div>'
      + '<button type="button" class="pl3-degree" data-pl-act="degree" aria-expanded="' + B.deg + '">' + (B.deg ? 'Hide' : 'Show') + ' your degree progress and 4-year plan</button>'
      + '</div>';
  }
  function listHtml(slot) {
    if (B.q.trim()) {
      var rs = searchRows(B.q, slot);
      return rs.length ? '<div class="pl3-list">' + rs.map(needRowHtml).join('') + '</div>' : '<p class="pl3-quiet">No class this term matches “' + esc(B.q) + '”.</p>';
    }
    var G = needGroups(slot), h = '';
    if (!G.groups.length) h += '<p class="pl3-quiet">' + (G.noMajor ? 'Add your major in Settings and this fills with what you still need. Until then, find any class above.' : 'Nothing left that’s offered this term — find any class above.') + '</p>';
    G.groups.forEach(function (g) {
      var rows = g.rows, cut = g.cap && !B.more[g.key] && rows.length > g.cap;
      h += '<div class="pl3-group"><h4>' + esc(g.title) + '</h4><div class="pl3-list">' + (cut ? rows.slice(0, g.cap) : rows).map(needRowHtml).join('') + '</div>'
        + (cut ? '<button type="button" class="pl3-link" data-pl-act="more" data-key="' + esc(g.key) + '">' + (rows.length - g.cap) + ' more ' + esc(g.title) + ' classes</button>' : '') + '</div>';
    });
    return h;
  }
  /* Focus survives a repaint: the element that had it is found again by what it is. */
  function fkey(el) {
    if (!el || !el.getAttribute || !el.getAttribute('data-pl-act')) return null;
    return { a: el.getAttribute('data-pl-act'), code: el.getAttribute('data-code'), crn: el.getAttribute('data-crn'), slot: el.getAttribute('data-slot'), key: el.getAttribute('data-key') };
  }
  function findKey(root, k) {
    if (!root || !k) return null;
    return Array.prototype.filter.call(root.querySelectorAll('[data-pl-act="' + k.a + '"]'), function (el) {
      return (!k.code || el.getAttribute('data-code') === k.code) && (!k.crn || el.getAttribute('data-crn') === k.crn)
        && (!k.slot || el.getAttribute('data-slot') === k.slot) && (!k.key || el.getAttribute('data-key') === k.key) && el.getAttribute('tabindex') !== '-1';
    })[0] || null;
  }
  function paintWeek() {
    var w = document.getElementById('pl3BWeek'); if (!w) return;
    w.innerHTML = builderWeek(S.cur);
    var code = focusCode();
    Array.prototype.forEach.call(document.querySelectorAll('#plBuilderOut .pl3-need'), function (b) {
      var on = b.getAttribute('data-code') === code; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on));
    });
  }
  var paintBuilderWeek = paintWeek;
  function paintList() {
    var l = document.getElementById('pl3BList'), side = document.getElementById('pl3BSide'); if (!l) return;
    var top = side ? side.scrollTop : 0;
    l.innerHTML = listHtml(S.cur);
    if (side) side.scrollTop = top;
  }
  /* Everything but the shell and the search box — so a plan edit, a sign-in load or the Undo
     timer never throws away the student's place in the list, their scroll, or the keyboard. */
  function paintBuilder() {
    var out = document.getElementById('plBuilderOut'), shell = out && out.querySelector('.pl3-builder');
    if (!shell || shell.getAttribute('data-slot') !== S.cur) { renderBuilder(); return; }
    var k = fkey(document.activeElement), inside = out.contains(document.activeElement);
    var pi = planInfo(S.cur);
    var sum = document.getElementById('pl3BSum'); if (sum) sum.textContent = pi.items.length ? summary(pi) : 'Empty so far';
    var n = document.getElementById('pl3BNotes'); if (n) n.innerHTML = notesHtml();
    var pl = document.getElementById('pl3BPills'); if (pl) pl.innerHTML = pillsHtml('bslot');
    paintList(); paintWeek();
    if (inside && k && k.a !== 'q' && !out.contains(document.activeElement)) { var el = findKey(out, k); if (el) el.focus({ preventScroll: true }); }
  }
  function renderBuilder() {
    var out = document.getElementById('plBuilderOut'); if (!out) return;
    var wrapEl = document.getElementById('schedPlanWrap');
    if (wrapEl) wrapEl.classList.toggle('pl3-deg-closed', !B.deg);
    var k = fkey(document.activeElement), inside = out.contains(document.activeElement);
    try { out.innerHTML = builderHtml(); paintBuilder(); } catch (e) {
      out.innerHTML = '<p class="pl3-quiet">Planner couldn’t be drawn just now.</p>';
      try { if (has('trackError')) trackError('planner render: ' + (e && e.message)); } catch (_) {}
    }
    if (inside && k) { var el = findKey(out, k); if (el) el.focus({ preventScroll: true }); }
  }
  function openDegree() { B.deg = true; renderBuilder(); }
  function hoverDevice() { try { return !!(window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches); } catch (_) { return false; } }

  function render() {
    var out = document.getElementById('plansOut');
    if (out) {
      try { out.innerHTML = paneHtml(); } catch (e) {
        out.innerHTML = '<p class="pl3-quiet">Plans couldn’t be drawn just now.</p>';
        try { if (has('trackError')) trackError('plans render: ' + (e && e.message)); } catch (_) {}
      }
    }
    var bw = document.getElementById('schedPlanWrap');
    if (bw && bw.style.display !== 'none') paintBuilder();
    var n = document.getElementById('stabWatchN');
    if (n) { var k = SLOTS.filter(function (s) { return plan(s).sections.length; }).length; n.textContent = k ? ' (' + k + ')' : ''; }
  }
  var refreshT = null;
  function refresh() {
    clearTimeout(refreshT);
    refreshT = setTimeout(function () {
      render();
      var gp = document.getElementById('plGpBack'); if (gp && gp.classList.contains('open')) renderGamePlan();
      try { if (typeof profileFriendId !== 'undefined' && profileFriendId && profileTab === 'plans' && has('renderFriendProfile')) renderFriendProfile(); } catch (_) {}
    }, 0);
  }

  /* ---------------------------------------------------------------------------------------------
     Rendering: the game plan sheet
     --------------------------------------------------------------------------------------------- */
  var gpSlot = 'A';
  function openGamePlan(slot) {
    ensure();
    gpSlot = slot || S.cur;
    if (!plan(gpSlot).sections.length) {
      var firstFull = SLOTS.filter(function (s) { return plan(s).sections.length; })[0];
      if (firstFull) gpSlot = firstFull;
    }
    var back = document.getElementById('plGpBack');
    if (!back) {
      back = document.createElement('div'); back.id = 'plGpBack'; back.className = 'mback';
      back.innerHTML = '<div class="modal pl2-gpm" id="plGpModal" role="dialog" aria-modal="true" aria-labelledby="plGpTitle"></div>';
      back.addEventListener('click', function (e) { if (e.target === back) closeGamePlan(); });
      back.addEventListener('click', onClick);
      back.addEventListener('change', onChange);
      document.body.appendChild(back);
    }
    askInterest();
    renderGamePlan();
    back.classList.add('open'); document.body.style.overflow = 'hidden';
    try { if (has('track')) track('game_plan_open', null, null, {}); } catch (_) {}
  }
  function closeGamePlan() {
    var b = document.getElementById('plGpBack'); if (b) b.classList.remove('open');
    document.body.style.overflow = document.querySelector('.mback.open') ? 'hidden' : '';
  }
  function renderGamePlan() {
    var el = document.getElementById('plGpModal'); if (!el) return;
    var g = gamePlan(gpSlot);
    var a = appt();
    var pills = '<div class="pl2-pills pl2-pills--sm">' + SLOTS.map(function (s) {
      var q = planInfo(s);
      return '<button type="button" class="pl2-pill' + (s === gpSlot ? ' on' : '') + '" data-pl-act="gpslot" data-slot="' + s + '"' + (q.items.length ? '' : ' disabled') + '><b>' + s + '</b><span>' + (q.items.length ? unitsLabel(q) : 'empty') + '</span></button>';
    }).join('') + '</div>';
    var h = '<div class="rate-wrap pl2-gpw"><button class="mclose" data-pl-act="gpclose" aria-label="Close">&times;</button>'
      + '<div class="pl2-gphd"><div class="rate-kicker">Plan ' + g.slot + '</div><h2 class="rate-h" id="plGpTitle">Registration game plan' + (g.preview ? ' <span class="pl2-prev">preview</span>' : '') + '</h2>'
      + '<p class="pl2-stats">' + esc(g.regTerm ? g.regTerm + ' · ' : '') + esc(roundLine()) + '</p></div>' + pills;
    if (g.preview) {
      h += '<div class="pl2-callout">This plan uses ' + esc(g.termLabel) + ' sections, so treat it as a preview. Plans made once ' + esc(g.regTerm)
        + ' classes are in TermChamp are the ones to register with.</div>';
    }
    h += '<label class="pl2-appt"><span>Your appointment time <em>(from the Portal)</em></span>'
      + '<input type="datetime-local" data-pl-act="appt" value="' + (a && !isNaN(a) ? esc(new Date(a.getTime() - a.getTimezoneOffset() * 60000).toISOString().slice(0, 16)) : '') + '">'
      + (a && !isNaN(a) ? '<b>' + esc(countdown(a)) + '</b>' : '') + '</label>';
    if (!g.steps.length) {
      h += '<p class="pl2-note">Plan ' + g.slot + ' has no sections yet.</p></div>';
      el.innerHTML = h; return;
    }
    if (inRound1()) {
      h += '<div class="pl2-callout pl2-callout--ok">Round 1 lets you enroll in ' + ROUND1_UNITS + ' units and waitlist ' + ROUND1_WAIT + '. '
        + (!g.unitsKnown
          ? 'A class in Plan ' + g.slot + ' has no unit count on record, so check units in the Portal before counting on this split.'
          : 'Plan ' + g.slot + ' is ' + g.units + ' units — ' + (g.split ? 'register the first ' + g.r1Units + ' units in Round 1; the rest waits for Round 2.' : 'all of it goes in Round 1.')
            + (g.w1Units ? ' Plus ' + g.w1Units + ' waitlist units for classes that are full now.' : ''))
        + '</div>';
    }
    h += '<div class="pl2-gplab">Register in this order</div><ol class="pl2-steps">';
    var lastRound = 1;
    g.steps.forEach(function (s, ix) {
      var i = s.i;
      if (s.round === 2 && lastRound === 1 && inRound1()) { h += '<li class="pl2-roundsep">Round 2 — ' + esc(niceDay(cfgv('REGISTRATION_ROUND2')) || 'later') + '</li>'; lastRound = 2; }
      var bk = s.backup, bkHtml;
      if (bk && bk.best) {
        var b = bk.best;
        bkHtml = '<span class="pl2-bkl">Backup</span><span class="pl2-code">-' + esc(b.no) + '</span><span class="pl2-bkw">' + esc([b.when, b.prof].filter(Boolean).join(' · ')) + '</span>' + rateHtml(b.rating)
          + (bk.needsLab ? '<span class="pl2-chip">pick a lab too</span>' : '')
          + '<button type="button" class="pl2-mini" data-pl-act="usebackup" data-slot="' + g.slot + '" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '" data-to="' + esc(b.crn) + '">Use backup</button>';
      } else {
        bkHtml = '<span class="pl2-bkl">Backup</span><span class="pl2-bkw">None fits — if it fills, join the waitlist' + (inRound1() ? ' (up to ' + ROUND1_WAIT + ' units in Round 1)' : '') + '</span>';
      }
      var status = s.mine === 'enrolled' ? '<span class="pl2-chip pl2-chip--ok">✓ Got it</span>'
        : (s.mine === 'waitlisted' ? '<span class="pl2-chip pl2-chip--wait">⏳ Waitlisted</span>' : '');
      h += '<li class="pl2-step' + (s.reasons[0] && s.reasons[0].hot ? ' pl2-step--hot' : '') + '">'
        + '<span class="pl2-num">' + (ix + 1) + '</span><div class="pl2-stepb">'
        + '<div class="pl2-steph"><span class="pl2-code">' + esc(i.label) + '</span><span class="pl2-name">' + esc(nameOf(i.code)) + '</span>' + (s.seatLine ? '<span class="pl2-seat">' + esc(s.seatLine) + '</span>' : '') + '</div>'
        + '<div class="pl2-chips">' + s.reasons.map(function (r) { return '<span class="pl2-chip' + (r.hot ? ' pl2-chip--hot' : '') + '">' + esc(r.t) + '</span>'; }).join('') + status + '</div>'
        + '<div class="pl2-bk">' + bkHtml + '</div>'
        + (s.mine ? '' : '<div class="pl2-stepa"><button type="button" class="pl2-mini pl2-mini--ok" data-pl-act="gotit" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '">Got it</button>'
          + '<button type="button" class="pl2-mini" data-pl-act="waitlisted" data-code="' + esc(i.code) + '" data-crn="' + esc(i.crn) + '">Waitlisted</button></div>')
        + '</div></li>';
    });
    h += '</ol>';
    if (g.missing) h += '<p class="pl2-note">' + g.missing + ' section' + (g.missing === 1 ? ' in this plan is' : 's in this plan are') + ' no longer in this term’s list and ' + (g.missing === 1 ? 'is' : 'are') + ' left out.</p>';
    h += '<p class="pl2-note">Order uses which sections fit your week, '
      + (g.live ? 'live seats from Cal Poly' : 'section size from Cal Poly (live seats once Round 1 opens)')
      + ', how many sections are offered, how many TermChamp students have it in a plan (shown at 3 or more) and friends planning it. It can’t see anyone’s appointment time.'
      + (g.asOf ? ' Seats as of ' + esc(clockOf(g.asOf)) + '.' : '') + '</p></div>';
    el.innerHTML = h;
  }

  /* ---------------------------------------------------------------------------------------------
     The ＋ Plan button on class pages, and its chooser
     --------------------------------------------------------------------------------------------- */
  function planBtnHtml(code, crn, cls) {
    ensure();
    var on = slotsHaving(crn);
    var label = on.length ? ('In Plan ' + on.join(', ')) : (watched(code, crn) ? 'Watching · ＋ Plan' : '＋ Plan');
    return '<button type="button" class="' + (cls || 'cp-watch') + ' pl2-cpbtn' + (on.length ? ' on' : '') + '" data-pl-act="choose" data-code="' + esc(code) + '" data-crn="' + esc(crn) + '"'
      + ' title="Add this section to Plan A, B or C — every class in a plan is watched" aria-haspopup="true">' + esc(label) + '</button>';
  }
  function openChooser(btn, code, crn) {
    closeChooser();
    ensure();
    var box = document.createElement('div');
    box.className = 'pl2-choose'; box.id = 'plChoose'; box.setAttribute('role', 'menu');
    box.innerHTML = '<div class="pl2-chhd">' + esc(code) + ' · add to</div>' + SLOTS.map(function (s) {
      var on = slotsHaving(crn).indexOf(s) >= 0, q = planInfo(s);
      return '<button type="button" role="menuitemcheckbox" aria-checked="' + on + '" class="pl2-chi' + (on ? ' on' : '') + '" data-pl-act="chtoggle" data-slot="' + s + '" data-code="' + esc(code) + '" data-crn="' + esc(crn) + '">'
        + '<span class="pl2-chk">' + (on ? '✓' : '') + '</span>Plan ' + s + '<em>' + (q.items.length ? unitsLabel(q) : 'empty') + '</em></button>';
    }).join('') + '<div class="pl2-chft">Every class in a plan is watched.</div>';
    document.body.appendChild(box);
    var r = btn.getBoundingClientRect();
    var w = 210, left = Math.min(window.innerWidth - w - 8, Math.max(8, r.right - w));
    var top = r.bottom + 6; if (top + 200 > window.innerHeight) top = Math.max(8, r.top - 190);
    box.style.left = left + 'px'; box.style.top = top + 'px';
    askInterest([crn]);
    setTimeout(function () { document.addEventListener('click', outside, true); }, 0);
  }
  function outside(e) { var b = document.getElementById('plChoose'); if (b && !b.contains(e.target)) closeChooser(); }
  function closeChooser() { var b = document.getElementById('plChoose'); if (b) b.remove(); document.removeEventListener('click', outside, true); }

  /* ---------------------------------------------------------------------------------------------
     Friend profile: a Plans tab
     --------------------------------------------------------------------------------------------- */
  var fpSlot = {};
  function friendTabHtml(f) {
    var rows = friendPlansFor[f.id] || [];
    if (!rows.length) return '';
    var on = (typeof profileTab !== 'undefined' && profileTab === 'plans');
    return '<button class="wl-tab ' + (on ? 'on' : '') + '" onclick="setProfileTab(\'plans\')">Plans (' + rows.length + ')</button>';
  }
  function friendBodyHtml(f) {
    var rows = (friendPlansFor[f.id] || []).slice().sort(function (a, b) { return a.slot < b.slot ? -1 : 1; });
    if (!rows.length) return '<p class="fr-mut frp-none">Nothing to show here yet.</p>';
    var cur = fpSlot[f.id] && rows.some(function (r) { return r.slot === fpSlot[f.id]; }) ? fpSlot[f.id] : rows[0].slot;
    var row = rows.filter(function (r) { return r.slot === cur; })[0];
    var items = clean(row.sections).map(function (x) { return info(x.code, x.class_nbr); });
    var nm = first(f.name);
    var h = '<p class="fr-mut">' + esc(nm) + ' shares ' + rows.length + ' plan' + (rows.length === 1 ? '' : 's') + ' for ' + esc(termLabel()) + '.</p>'
      + '<div class="pl2-pills pl2-pills--sm">' + rows.map(function (r) {
        var u = 0, seen = {}; clean(r.sections).forEach(function (x) { if (!seen[x.code]) { seen[x.code] = 1; u += unitsOf(x.code) || 0; } });
        return '<button type="button" class="pl2-pill' + (r.slot === cur ? ' on' : '') + '" data-pl-act="fpslot" data-fid="' + esc(f.id) + '" data-slot="' + r.slot + '"><b>Plan ' + r.slot + '</b><span>' + u + 'u</span></button>';
      }).join('') + '</div>' + weekStrip(items) + '<div class="pl2-list">';
    items.forEach(function (i) {
      var mineIn = slotsHaving(i.crn);
      var right = mineIn.length ? '<span class="pl2-chip pl2-chip--ok">Same section · your Plan ' + mineIn.join(', ') + '</span>'
        : (i.missing ? '' : planBtnHtml(i.code, i.crn, 'pl2-mini'));
      h += '<div class="pl2-row"><div class="pl2-main"><span class="pl2-code">' + esc(i.missing ? i.code : i.label) + '</span>'
        + '<span class="pl2-name">' + esc(nameOf(i.code)) + '</span><span class="pl2-sub">' + esc(i.missing ? 'Not in this term’s sections any more' : i.when) + '</span></div>'
        + '<div class="pl2-side">' + right + '</div></div>';
    });
    h += '</div>';
    if (has('msgOn') && msgOn()) {
      h += '<button type="button" class="btn pl2-msg" data-pl-act="fpmsg" data-fid="' + esc(f.id) + '" data-slot="' + cur + '">Message ' + esc(nm) + ' about Plan ' + cur + '</button>';
    }
    h += '<p class="fr-mut pl2-note">Only accepted friends see plans, and only the ones ' + esc(nm) + ' shares.</p>';
    return h;
  }
  /* A draft, never sent (Tate's standing rule for Hawk and every "ask about it"). */
  function messageFriend(fid, slot) {
    var f = friendById(fid); if (!f) return;
    var text = 'Hey ' + first(f.name) + ' — saw your Plan ' + slot + ' for ' + termLabel() + '. Want to line up any classes?';
    try { if (has('closeFriendProfile')) closeFriendProfile(); } catch (_) {}
    try {
      if (has('msgWith')) {
        msgWith(fid);
        setTimeout(function () {
          var box = document.querySelector('#msgInput, .msg-input textarea, .msg-compose textarea, textarea[placeholder*="essage"]');
          if (box && !box.value) { box.value = text; box.dispatchEvent(new Event('input', { bubbles: true })); box.focus(); }
        }, 450);
      }
    } catch (_) {}
  }

  /* ---------------------------------------------------------------------------------------------
     Undo, events
     --------------------------------------------------------------------------------------------- */
  function offerUndo(text, fn) {
    undoBox = { text: text, fn: fn };
    clearTimeout(offerUndo._t);
    offerUndo._t = setTimeout(function () {
      var a = document.activeElement, onUndo = a && a.getAttribute && a.getAttribute('data-pl-act') === 'undo';
      undoBox = null; render();
      if (onUndo) {                                     // don't drop the keyboard onto the page
        var nx = document.querySelector('#plBuilderOut .pl3-need, #plBuilderOut [data-pl-act="q"], #plansOut .pl3-pill.on');
        if (nx) nx.focus({ preventScroll: true });
      }
    }, 8000);
  }
  function onClick(e) {
    var t = e.target.closest ? e.target.closest('[data-pl-act]') : null;
    if (!t) return;
    var act = t.getAttribute('data-pl-act'), slot = t.getAttribute('data-slot'), code = t.getAttribute('data-code'), crn = t.getAttribute('data-crn');
    if (act === 'open') { var inner = e.target.closest('button,input,label'); if (inner && inner !== t) return; }
    if (act === 'q') return;
    if (act !== 'share' && act !== 'appt') { e.preventDefault(); e.stopPropagation(); }
    if (act === 'cur') { S.cur = slot; saveLocal(); undoBox = null; render(); return; }
    if (act === 'open') { try { if (has('openClassPage')) { openClassPage(code); if (has('cpRefresh')) cpRefresh(crn); } } catch (_) {} return; }
    if (act === 'remove') {
      var hit = plan(slot).sections.filter(function (x) { return x.class_nbr === crn; })[0];
      var i = hit ? info(hit.code, crn) : { label: '' };
      var prev = remove(slot, crn);
      offerUndo('Removed ' + (i.label || ('#' + crn)) + ' from Plan ' + slot + '.', function () { setSections(slot, prev); });
      render(); return;
    }
    if (act === 'adopt-yes' || act === 'adopt-no') { adoptAnon(act === 'adopt-yes'); return; }
    /* ---- the redesign's Plans ↔ Planner hand-off ---- */
    if (act === 'edit') {
      S.cur = slot || S.cur; saveLocal(); B.sel = null; B.hov = null; B.q = '';
      try { if (has('show')) show('sched'); if (has('setSchedTab')) setSchedTab('plan'); } catch (_) {}
      try { window.scrollTo(0, 0); } catch (_) {}
      return;
    }
    if (act === 'done') { B.sel = null; try { if (has('setSchedTab')) setSchedTab('watch'); } catch (_) {} return; }
    if (act === 'bslot') { S.cur = slot; saveLocal(); B.sel = null; B.hov = null; undoBox = null; renderBuilder(); render(); return; }
    var byKeys = e.detail === 0;                      // a click made by Enter/Space, not a pointer
    if (act === 'need') {
      /* A tap or click PINS the class: it never toggles off (a first tap on a phone used to focus,
         select and then un-select the row). Hover only previews; the click is the commitment. */
      clearTimeout(dwellT); B.sel = code; B.hov = null; paintWeek();
      var w0 = document.getElementById('pl3BWeek');
      if (w0 && w0.scrollIntoView) {                   // the green blocks must be on screen, on any device
        var wr = w0.getBoundingClientRect();
        if (wr.top < 60 || wr.top > window.innerHeight - 120) { try { w0.scrollIntoView({ block: 'start', behavior: 'smooth' }); } catch (_) {} }
      }
      if (byKeys) { var g0 = document.querySelector('#pl3BWeek .pl3-ghost:not([tabindex="-1"])'); if (g0) g0.focus(); }
      return;
    }
    if (act === 'ghost') {
      var gi = info(code, crn);
      if (add(S.cur, code, crn)) toast('Added ' + (gi.label || code) + ' to Plan ' + S.cur);
      var nextF = fitFor(code, S.cur);
      B.sel = nextF && nextF.offered ? code : null; B.hov = null;
      paintBuilder();
      if (byKeys) {                                     // keep the keyboard where the work is
        var back = document.querySelector('#plBuilderOut .pl3-need[data-code="' + code.replace(/"/g, '') + '"]')
          || document.querySelector('#plBuilderOut .pl3-need') || document.querySelector('#plBuilderOut [data-pl-act="q"]');
        if (back) back.focus();
      }
      return;
    }
    if (act === 'rm') {
      var hit2 = plan(slot).sections.filter(function (x) { return x.class_nbr === crn; })[0];
      var ri = hit2 ? info(hit2.code, crn) : { label: '' };
      var prev2 = remove(slot, crn);
      offerUndo('Removed ' + (ri.label || ('#' + crn)) + ' from Plan ' + slot + '.', function () { setSections(slot, prev2); });
      render();
      if (byKeys) { var nx = document.querySelector('#plBuilderOut [data-pl-act="undo"]'); if (nx) nx.focus(); }
      return;
    }
    if (act === 'more') { B.more[t.getAttribute('data-key')] = 1; paintList(); return; }
    if (act === 'degree') { B.deg = !B.deg; renderBuilder(); return; }
    if (act === 'undo') { var u = undoBox; undoBox = null; if (u) u.fn(); render(); return; }
    if (act === 'gameplan') { openGamePlan(slot); return; }
    if (act === 'addto') { if (add(slot, code, crn)) toast(code + ' → Plan ' + slot); return; }
    if (act === 'unwatch') { try { if (has('wcWatchSec')) wcWatchSec(code, crn, null, true); } catch (_) {} render(); return; }
    if (act === 'choose') { openChooser(t, code, crn); return; }
    if (act === 'chtoggle') {
      if (slotsHaving(crn).indexOf(slot) >= 0) { remove(slot, crn); toast('Removed from Plan ' + slot); }
      else if (add(slot, code, crn)) toast(code + ' → Plan ' + slot + ' · watching it');
      closeChooser();
      try { if (has('cpRefresh')) cpRefresh(crn); } catch (_) {}
      try { if (has('renderExplore')) renderExplore(); } catch (_) {}
      return;
    }
    if (act === 'gpclose') { closeGamePlan(); return; }
    if (act === 'gpslot') { gpSlot = slot; renderGamePlan(); return; }
    if (act === 'gotit' || act === 'waitlisted') {
      closeGamePlan();
      try { if (has('mcEnrollSec')) { mcEnrollSec(code, crn); if (act === 'waitlisted' && has('enSetStatus')) enSetStatus('waitlisted'); } } catch (_) {}
      return;
    }
    if (act === 'usebackup') {
      var to = t.getAttribute('data-to'), before = plan(slot).sections.slice();
      replace(slot, crn, code, to);
      offerUndo('Swapped to the backup in Plan ' + slot + '.', function () { setSections(slot, before); });
      renderGamePlan(); return;
    }
    if (act === 'fpslot') { fpSlot[t.getAttribute('data-fid')] = slot; try { if (has('renderFriendProfile')) renderFriendProfile(); } catch (_) {} return; }
    if (act === 'fpmsg') { messageFriend(t.getAttribute('data-fid'), slot); return; }
  }
  function onChange(e) {
    var t = e.target; if (!t || !t.getAttribute) return;
    var act = t.getAttribute('data-pl-act');
    if (act === 'share') { setShared(t.getAttribute('data-slot'), t.checked); return; }
    if (act === 'appt') {
      try { if (t.value) localStorage.setItem(apptKey(), new Date(t.value).toISOString()); else localStorage.removeItem(apptKey()); } catch (_) {}
      renderGamePlan();
    }
  }

  /* ---------------------------------------------------------------------------------------------
     Saving a Hawk-built term as a plan (item 3 folds in here)
     --------------------------------------------------------------------------------------------- */
  function saveFromBuild(slot, picks) {
    var list = (picks || []).map(function (p) { return { code: p.code, class_nbr: String(p.class_nbr || p.crn || '') }; });
    var prev = setSections(slot, list, 'build');
    var kept = S.plans[slot].sections.length;
    S.cur = slot; saveLocal();
    try { if (has('track')) track('plan_edit', null, null, { op: 'build', slot: slot }); } catch (_) {}
    return { undo: function () { setSections(slot, prev); }, saved: kept, dropped: Math.max(0, list.length - kept) };
  }

  /* ---------------------------------------------------------------------------------------------
     Wiring into the app, without editing its functions in place
     --------------------------------------------------------------------------------------------- */
  function wrap(name, after) {
    try {
      var orig = window[name];
      if (typeof orig !== 'function' || orig._plWrapped) return;
      var w = function () {
        var r = orig.apply(this, arguments);
        try { if (r && typeof r.then === 'function') r.then(function () { after(); }, function () {}); else after(); } catch (_) {}
        return r;
      };
      w._plWrapped = true;
      window[name] = w;
    } catch (_) {}
  }
  function mount() {
    document.addEventListener('click', function (e) {
      var t = e.target.closest ? e.target.closest('#plansOut [data-pl-act], #plBuilderOut [data-pl-act], #plChoose [data-pl-act], .pl2-cpbtn, #view-class [data-pl-act], .frp-wrap [data-pl-act], #view-explore [data-pl-act]') : null;
      if (t && !t.closest('#plGpBack')) onClick(e);
    });
    document.addEventListener('change', function (e) { if (e.target && e.target.closest && e.target.closest('#plansOut')) onChange(e); });
    /* Planner: pointing at a class previews where it fits, and the preview STAYS when the pointer
       moves on to the week — otherwise the green blocks would vanish on the way to clicking one. */
    /* Pointing at a class previews it — but only once the pointer RESTS there (a quarter second).
       Sweeping across the list on the way to a green block, or scrolling it, changes nothing; and
       entering the week freezes the preview so the block you're heading for stays put. */
    document.addEventListener('mouseover', function (e) {
      if (!hoverDevice() || !e.target.closest) return;
      if (e.target.closest('#pl3BWeek')) { clearTimeout(dwellT); return; }
      var r = e.target.closest('#plBuilderOut .pl3-need');
      if (!r) return;
      var code = r.getAttribute('data-code');
      clearTimeout(dwellT);
      if (code === focusCode()) return;
      dwellT = setTimeout(function () {
        if (Date.now() - lastScroll < 400) return;       // rows sliding under a still pointer are not a choice
        B.hov = code; paintWeek();
      }, 250);
    });
    /* Leaving a class cancels its pending preview, so only a class the pointer RESTS on can win. */
    document.addEventListener('mouseout', function (e) {
      var r = e.target.closest ? e.target.closest('#plBuilderOut .pl3-need') : null;
      if (r && !(e.relatedTarget && r.contains(e.relatedTarget))) clearTimeout(dwellT);
    });
    window.addEventListener('scroll', function () { lastScroll = Date.now(); clearTimeout(dwellT); }, true);
    document.addEventListener('input', function (e) {
      if (e.target && e.target.getAttribute && e.target.getAttribute('data-pl-act') === 'q' && e.target.closest('#plBuilderOut')) {
        B.q = e.target.value; B.sel = null; B.hov = null; paintList(); paintWeek();     // the box itself is never rebuilt
      }
    });
    var st = window.setSchedTab;
    if (typeof st === 'function' && !st._plWrapped) {
      var w3 = function (tab) {
        if (tab === 'past') B.deg = true;              // Past classes and the ledger live under the degree section
        var r = st.apply(this, arguments);
        try { if (tab === 'plan' || tab === 'past') renderBuilder(); if (tab === 'watch') render(); } catch (_) {}
        return r;
      };
      w3._plWrapped = true; window.setSchedTab = w3;
    }
    wrap('exGoPlanner', openDegree);
    /* Onboarding's "help me build one" clicks the planner's own build button and shows its result —
       both live in the degree section, so open it first. */
    var gm = window.goMyPlan;
    if (typeof gm === 'function' && !gm._plWrapped) {
      var w4 = function () { B.deg = true; try { var wr = document.getElementById('schedPlanWrap'); if (wr) wr.classList.remove('pl3-deg-closed'); } catch (_) {} var r = gm.apply(this, arguments); try { renderBuilder(); } catch (_) {} return r; };
      w4._plWrapped = true; window.goMyPlan = w4;
    }
    /* The tab's count is the number of plans with something in them — not the old watchlist's. */
    wrap('updateWatchTabCounts', function () {
      var n = document.getElementById('stabWatchN'); if (!n) return;
      var k = SLOTS.filter(function (s) { return plan(s).sections.length; }).length; n.textContent = k ? ' (' + k + ')' : '';
    });                     // Explore's "See your full ledger →"
    window.plansOpenDegree = openDegree;
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closeChooser(); var gp = document.getElementById('plGpBack'); if (gp && gp.classList.contains('open')) closeGamePlan(); }
      if ((e.key === 'Enter' || e.key === ' ') && e.target && e.target.getAttribute && e.target.getAttribute('data-pl-act') === 'open') onClick(e);
    });
    wrap('renderWatchClasses', render);
    wrap('loadWatchSectionsFromDb', function () {
      var u = me(); if (u) watchesFor = String(u.id);
      resyncAll(); load();
    });
    /* Signing out takes this account's plans off the device, so the next person here never sees them. */
    var so = window.authSignOut;
    if (typeof so === 'function' && !so._plWrapped) {
      var w2 = function () {
        var u = me(), id = u ? String(u.id) : null;
        if (id) {
          try {
            for (var k = localStorage.length - 1; k >= 0; k -= 1) {
              var key = localStorage.key(k);
              if (key && key.indexOf('professify_plans_') === 0 && key.slice(-(id.length + 1)) === '_' + id) localStorage.removeItem(key);
            }
          } catch (_) {}
        }
        friendPlans = null; friendPlansFor = {}; interest = {}; interestAsked = {};
        var r = so.apply(this, arguments);
        try { Promise.resolve(r).then(function () { S.plans = null; refresh(); }); } catch (_) {}
        return r;
      };
      w2._plWrapped = true; window.authSignOut = w2;
    }
    wrap('renderFriends', refresh);          // friends' names and faces arrive after plans do
    /* The profile's tab row scrolls sideways on a phone; opening straight onto Plans must show it. */
    wrap('renderFriendProfile', function () {
      try { if (profileTab === 'plans') { var t = document.querySelector('#frpModal .frp-tabs .wl-tab.on'); if (t && t.scrollIntoView) t.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } } catch (_) {}
    });
    ensure(); render();
    setTimeout(function () { if (me()) load(); }, 1500);
  }

  window.TCPlans = {
    slots: SLOTS, get: plan, cur: function () { ensure(); return S.cur; }, setCur: function (s) { S.cur = s; saveLocal(); render(); },
    slotsHaving: slotsHaving, add: add, remove: remove, replace: replace, setSections: setSections, setShared: setShared,
    info: info, planInfo: planInfo, backupFor: backupFor, gamePlan: gamePlan, openGamePlan: openGamePlan, closeGamePlan: closeGamePlan,
    render: render, renderBuilder: renderBuilder, openDegree: openDegree, fitFor: fitFor, needGroups: needGroups, load: load, loadFriendPlans: loadFriendPlans, askInterest: askInterest, interestOf: interestOf,
    planBtnHtml: planBtnHtml, interestChip: interestChip, friendTabHtml: friendTabHtml, friendBodyHtml: friendBodyHtml,
    saveFromBuild: saveFromBuild, server: function () { return S.server; },
    fromBanner: function () {
      ensure();
      if (SLOTS.some(function (s) { return plan(s).sections.length; })) { openGamePlan(); return; }
      try { if (has('show')) show('sched'); if (has('setSchedTab')) setSchedTab('watch'); } catch (_) {}
    },
    _setInterest: function (m) { interest = m || {}; interestTerm = term(); refresh(); },
    _setFriendPlans: function (rows) { friendPlans = rows || []; friendPlansFor = {}; friendPlans.forEach(function (r) { (friendPlansFor[r.user_id] = friendPlansFor[r.user_id] || []).push(r); }); refresh(); }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
}());
