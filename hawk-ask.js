/* ================================================================================================
   HAWK — the ask box
   ================================================================================================
   A small box in the bottom-right corner. Tap the Hawk icon, type a question, get back a few rows
   you can tap. Tapping one takes you to that class, that section, that professor — and the box is
   still there afterwards, with the answer still in it, because you have not gone anywhere Hawk
   cannot follow.

   IT IS NOT A MODAL. No scrim, nothing dimmed, nothing blurred, and the rest of the app stays
   fully clickable the whole time. Navigating does not close it. A modal would make every question
   a round trip — open, ask, close, look, open again — which is the many-tab ritual this product
   exists to end, rebuilt inside the product.

   ONE ANSWER AT A TIME. The previous build kept a scrolling log of twelve turns, which grew into a
   panel. Tate, 2026-09-20: a small text box, simple answers, not long explanations. So each
   question replaces the last one. The box never grows past what you can read at a glance.

   IT ANSWERS WITH SECTIONS, NOT JUST COURSES. "bus 100 mondays at 3pm" does not return BUS 100 and
   an apology about not being able to filter by day or time. It returns the sections that meet on
   Monday at 3, and if none do, the nearest one, MARKED as the nearest one. The seat feed already
   carries days, times, instructor, CRN and status for every section; the only reason Hawk used to
   shrug at those words was that it had never been taught to look.

   WHAT IT WILL NOT DO. It never answers in prose, never summarises, and never states a fact of its
   own. Every row is a course, a section, a professor or a GE area that already exists, rendered
   from the same data the app renders from and THROUGH THE APP'S OWN FUNCTIONS — `parseMeet` reads
   the meeting time, `secSeat` reads the seat state, `openClassPage` does the navigating. If the
   class page and Hawk ever disagree about a section, it is one bug in one function, not two
   readings of the same feed.

   Requires hawk-router.js. Uses, and degrades without: openClassPage, openProf, cpRefresh,
   parseMeet, secSeat, show, setExMode, setExDept, exSetGeArea, renderExplore, COURSE_NAME,
   CLASS_INDEX, FLOW_INDEX, GE_COURSES, GE_AREAS, SEAT_SECTIONS, SEATS_UPDATED_AT, PROFESSORS,
   matchProfId.
   ============================================================================================== */
(function (global) {
  'use strict';

  var R = global.HawkRouter;
  if (!R) return;

  var MAX_ROWS = 4;          // four is what fits without the box becoming a panel
  var MAX_SECTIONS = 3;
  var NEAR_ENOUGH = 45;      // minutes: how far off "at 3pm" may be and still count as answering it
  var catalogCache = null;
  var els = null;
  var returnFocusTo = null;

  function make(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function has(name) {
    try { return typeof global[name] === 'function'; } catch (_) { return false; }
  }

  /* ---------------------------------------------------------------------------------------------
     The catalog, assembled from every place this app keeps courses.
     Five separate stores, and reading only two of them is a bug this app has already shipped once:
     the autocomplete offered HIST 2202 while the search could not find it, so the app suggested a
     course and then told the student it did not exist. One pool.
     --------------------------------------------------------------------------------------------- */
  /* THE CACHE HAS TO NOTICE THE FEED ARRIVING.

     The seat feed is fetched from Supabase after the page loads, so whether `SEAT_SECTIONS` exists
     when Hawk first builds its catalog is a race with the network. Cached once and never rebuilt,
     a student who asked early got a Hawk permanently missing every course that only exists in the
     seat feed — and one who asked thirty seconds later got a complete one. Same build, same
     student, different answers, no error either way.

     Keyed on the feed's size: cheap to check on every question, and it rebuilds exactly once, when
     the feed lands. */
  var catalogSeatCount = -1;

  function seatCount() {
    try { return Object.keys(SEAT_SECTIONS || {}).length; } catch (_) { return 0; }
  }

  function buildCatalog() {
    var nf = 0;
    try { nf = (FRIENDS || []).length; } catch (_) { nf = 0; }
    var n = seatCount() * 1000 + nf;   // friends load after seats; either changing rebuilds
    if (catalogCache && n === catalogSeatCount) return catalogCache;
    catalogSeatCount = n;
    var courses = Object.create(null);
    function add(code, name) {
      var c = String(code || '').trim();
      if (!c) return;
      if (!courses[c] || (courses[c] === c && name)) courses[c] = String(name || '').trim() || c;
    }
    try { Object.keys(COURSE_NAME || {}).forEach(function (c) { add(c, COURSE_NAME[c]); }); } catch (_) {}
    try { Object.keys(CLASS_INDEX || {}).forEach(function (c) { var x = CLASS_INDEX[c] || {}; add(c, x.name || x.title); }); } catch (_) {}
    try { Object.keys(FLOW_INDEX || {}).forEach(function (c) { var x = FLOW_INDEX[c] || {}; add(c, x.name); }); } catch (_) {}
    try { (GE_COURSES || []).forEach(function (x) { if (x) add(x.code, x.name); }); } catch (_) {}
    try {
      Object.keys(SEAT_SECTIONS || {}).forEach(function (c) {
        var rows = SEAT_SECTIONS[c] || [];
        add(c, rows[0] && rows[0].title);
      });
    } catch (_) {}

    var subjects = [];
    Object.keys(courses).forEach(function (c) {
      var sub = c.split(/\s+/)[0];
      if (sub && subjects.indexOf(sub) === -1) subjects.push(sub);
    });
    subjects.sort();

    var professors = [];
    try {
      Object.keys(PROFESSORS || {}).forEach(function (id) {
        var p = PROFESSORS[id] || {};
        var n = p.name || p.n || p.full;
        if (n && professors.indexOf(n) === -1) professors.push(n);
      });
    } catch (_) {}

    var geAreas = [];
    try { (GE_AREAS || []).forEach(function (a) { if (a && a.key) geAreas.push(String(a.key).toUpperCase()); }); } catch (_) {}

    /* Friends' names, so "message maya" and "maya's schedule" can be read on the device. Only ids
       and names; this object never leaves the browser. */
    var friends = [];
    try { (FRIENDS || []).forEach(function (f) { if (f && f.id && f.name) friends.push({ id: f.id, name: f.name }); }); } catch (_) {}

    catalogCache = { courses: courses, subjects: subjects, professors: professors, geAreas: geAreas, friends: friends };
    return catalogCache;
  }

  /* ---------------------------------------------------------------------------------------------
     Reading a section — through the app's own functions, never our own parse.
     --------------------------------------------------------------------------------------------- */
  function sectionsOf(code) {
    try {
      var rows = (SEAT_SECTIONS || {})[code];
      return (rows && rows.length) ? rows : [];
    } catch (_) { return []; }
  }

  /* `parseMeet` turns "MoWe 3:10PM–4:00PM" into {days, start, end} in minutes. It is the same
     function the planner uses for conflict detection, which is the point: a section Hawk says
     meets on Monday is a section the calendar will also draw on Monday. */
  function meetOf(row) {
    try {
      if (has('parseMeet')) return global.parseMeet(row && row.days);
    } catch (_) {}
    return null;
  }

  /* `secSeat` is the app's single reading of a section's seat state, and it is deliberate about
     absence: an open section with a null count says "open" and refuses to print a made-up zero.
     Hawk repeats whatever it returns and adds nothing.

     (The previous build read `row.open`, a field that does not exist on these rows — so the seat
     line was null every time and simply never appeared. Nothing errored. Nobody saw a zero. The
     feature was just quietly absent, which is how this class of bug always looks.) */
  function seatOf(row) {
    try {
      if (has('secSeat')) return global.secSeat(row);
    } catch (_) {}
    return null;
  }

  /* Who teaches a section, and how they are rated — read the way the class page reads it:
     `matchProfId` resolves the feed's "Last, First" to a rated professor, `PROFESSORS[id].rating`
     is the blended score the rest of the app shows. No score is invented: a section whose
     instructor is not in the roster, or is "Staff", gets no number rather than a zero. */
  function profOf(row) {
    var raw = String((row && (row.name || row.instructor || row.prof)) || '').trim();
    if (!raw || /^staff$|^tba$/i.test(raw)) return null;
    var id = null;
    try { if (has('matchProfId')) id = global.matchProfId(raw); } catch (_) {}
    var p = null;
    try { p = id ? (PROFESSORS || {})[id] : null; } catch (_) { p = null; }
    /* PROFESSORS[id].rating is PolyRatings' 0–4 score. Every screen in the app shows it through
       to5() — out of 5 — so Hawk does too. Showing the raw number made a professor the class page
       calls 4.5 ★ read as 3.6 ★ in Hawk (found 2026-09-23). */
    var rating = (p && typeof p.rating === 'number' && p.rating > 0) ? five(p.rating) : null;
    var name = (p && p.name) || flipName(raw);
    return { id: id, name: name, rating: rating, raw: raw };
  }

  function five(raw) {
    try { if (has('to5')) return global.to5(raw); } catch (_) {}
    return Math.round(raw / 4 * 5 * 100) / 100;
  }

  /* "Kathuria, Ajay" → "Ajay Kathuria". Only a lone comma is flipped; a suffix stays as written. */
  function flipName(t) {
    var bits = String(t || '').split(',');
    if (bits.length === 2 && bits[0].trim() && bits[1].trim()) return bits[1].trim() + ' ' + bits[0].trim();
    return String(t || '').trim();
  }

  function ratingChip(rating) {
    if (rating == null) return null;
    var tone = rating >= 4 ? 'open' : (rating >= 3 ? 'wait' : 'full');
    return { text: rating.toFixed(1) + ' ★', tone: tone };
  }

  function seatChip(row) {
    var s = seatOf(row);
    if (!s || s.unknown) return null;
    if (s.cls === 'open') return { text: (s.n != null ? s.n + ' open' : 'open'), tone: 'open' };
    if (s.cls === 'wait') return { text: 'waitlist', tone: 'wait' };
    if (s.cls === 'full') return { text: 'full', tone: 'full' };
    return null;
  }

  /* The live feed writes sections as "S01-LEC Regular"; older builds and fixtures wrote "01".
     The first run of digits is the section in both. Anchoring on ^ turned every live section into
     "S01" — readable, but not the number on a student's registration screen. */
  function secNumber(row) {
    var t = String((row && row.section) || '').trim();
    var m = /(\d+)/.exec(t);
    if (m) return m[1];
    return t ? t.split('-')[0] : '';
  }

  /* Lecture / Lab / Activity. The live feed carries it INSIDE the section string ("S01-LEC"), not in
     a `comp` object — which only some app code adds after normalising. Reading `comp.label` alone
     meant every "labs" question on real data missed every section, silently. */
  function compOf(row) {
    try { if (row && row.comp && row.comp.label) return String(row.comp.label).toUpperCase().slice(0, 3); } catch (_) {}
    var m = /-(LEC|LAB|ACT|SEM|DIS|SUP|IND|STU)\b/i.exec(String((row && row.section) || ''));
    return m ? m[1].toUpperCase() : '';
  }

  /* Online / in person, from the live feed's `instruction_mode` ("In Person", "Asynchronous", …). */
  function modeOf(row) {
    var t = String((row && (row.instruction_mode || row.mode)) || '').toLowerCase();
    if (!t) return '';
    if (/async/.test(t)) return 'async';
    if (/hybrid/.test(t)) return 'hybrid';
    if (/sync|online|remote|virtual/.test(t)) return 'sync_online';
    if (/person|campus/.test(t)) return 'in_person';
    return '';
  }

  function toMin(hhmm) {
    var m = /^(\d{2}):(\d{2})$/.exec(String(hhmm || ''));
    return m ? (+m[1]) * 60 + (+m[2]) : null;
  }

  var DAY_SHORT = { Mo: 'Mo', Tu: 'Tu', We: 'We', Th: 'Th', Fr: 'Fr', Sa: 'Sa', Su: 'Su' };

  function clock12(mins) {
    var h = Math.floor(mins / 60), mi = mins % 60;
    var ap = h >= 12 ? 'pm' : 'am';
    var h12 = h % 12 === 0 ? 12 : h % 12;
    return h12 + (mi ? ':' + String(mi).padStart(2, '0') : '') + ' ' + ap;
  }

  /* The one line of text on a section row. Built from the parsed meeting rather than echoed from
     the feed's own string, so every row in the box reads the same way regardless of how that
     section happened to be written upstream. No meeting time is said plainly, never blank. */
  function meetLabel(row) {
    var m = meetOf(row);
    if (!m) return modeOf(row) === 'async' ? 'Async \u2014 no set time' : 'no set meeting time';
    return m.days.map(function (d) { return DAY_SHORT[d] || d; }).join('') + ' ' + clock12(m.start);
  }

  /* ===============================================================================================
     THE STUDENT'S OWN SCHEDULE — read here, on the device, and nowhere else.

     This is Phase 2 of `cheap-assistant-build-plan-2026-09-20.md`, and the plan's own line is the
     reason it needs no vendor at all: "Still zero data to the model: the CLIENT resolves 'my'."
     Nothing below asks anything of a network. It reads `myClasses` and `myClassMeta` — already in
     memory because the app drew the student's week with them — through the app's own `parseMeet`
     and `meetsOverlap`, which is what makes a clash Hawk reports and a clash the calendar draws
     the same clash.

     WHAT IT REFUSES TO DO: invent a schedule. A student with nothing saved is told they have
     nothing saved. An empty answer here is a true answer, and the alternative — a confident
     "no conflicts!" to somebody whose classes we simply cannot see — is the exact shape of the
     failure this whole product is built against.
     =============================================================================================== */

  var DAY_ORDER = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
  var DAY_FULL = { Mo: 'Monday', Tu: 'Tuesday', We: 'Wednesday', Th: 'Thursday', Fr: 'Friday',
                   Sa: 'Saturday', Su: 'Sunday' };

  /* Every enrolled class we can actually place on a clock. `unplaced` is carried rather than
     dropped: a student with an async class and no meeting time deserves to be told that their
     answer is missing a class, not handed a tidy lie. */
  /* READ AS BARE NAMES, NOT OFF `window`, AND THAT IS NOT A STYLE CHOICE.

     `myClasses` and `myClassMeta` are `let` bindings at the top level of a classic script, so they
     live in the global LEXICAL environment and never appear on `window` — `window.myClasses` is
     `undefined` while `myClasses` resolves perfectly. Functions differ: `function myClassTime()`
     does land on `window`, which is why `has()` works for those.

     Written first as `global.myClasses`, this returned "no classes saved" for every student
     forever, with no error and nothing in the console. It was caught only by seeding a schedule
     and reading the answer. `buildCatalog` above survives the same trap by accident, because it
     reads `COURSE_NAME` bare — and `COURSE_NAME` is not on `window` either. */
  function mySchedule() {
    var placed = [], unplaced = [], codes = [];
    try { codes = (myClasses || []).slice(); } catch (_) { return null; }
    if (!codes.length) return { placed: placed, unplaced: unplaced, empty: true };
    codes.forEach(function (code) {
      var when = null;
      try { if (has('myClassTime')) when = global.myClassTime(code); } catch (_) {}
      var meet = null;
      try { if (when && has('parseMeet')) meet = global.parseMeet(when); } catch (_) {}
      if (meet) placed.push({ code: code, meet: meet });
      else unplaced.push(code);
    });
    return { placed: placed, unplaced: unplaced, empty: false };
  }

  function overlaps(a, b) {
    try { if (has('meetsOverlap')) return global.meetsOverlap(a, b); } catch (_) {}
    if (!a || !b) return false;
    var shared = a.days.some(function (d) { return b.days.indexOf(d) >= 0; });
    return shared && a.start < b.end && b.start < a.end;
  }

  /* What in the student's week this section runs into. Returns the codes, not a sentence. */
  function clashesWith(meet, mine, selfCode) {
    if (!meet || !mine || mine.empty) return [];
    var hits = [];
    mine.placed.forEach(function (c) {
      /* A section of a class you are already in does not clash with that class — it IS that
         class, or a sibling of it. "BUS 4442-01 clashes with BUS 4442" was true and absurd. */
      if (selfCode && c.code === selfCode) return;
      if (overlaps(meet, c.meet) && hits.indexOf(c.code) === -1) hits.push(c.code);
    });
    return hits;
  }

  /* The section the student is enrolled in, by CRN, so a row can say "yours" instead of "clash". */
  function isMine(code, row) {
    try {
      var m = (myClassMeta || {})[code];
      var want = String(row.class_nbr || row.crn || '');
      if (!m || !want) return false;
      /* The app keeps the enrolled section in meta.secs[].crn (mcCommitSection and the sync).
         meta.crn is only in older fixtures; reading it alone meant "yours" never showed live. */
      var crns = (Array.isArray(m.secs) ? m.secs : []).map(function (x) { return String(x && x.crn || ''); });
      if (m.crn || m.class_nbr) crns.push(String(m.crn || m.class_nbr));
      return crns.indexOf(want) >= 0;
    } catch (_) { return false; }
  }

  /* Free stretches on one day, between the first and last class on it. Deliberately NOT "you are
     free from midnight to 8am": a gap before the day starts or after it ends is not a gap in a
     schedule, it is the absence of one, and printing it would pad the answer with noise. */
  var MIN_GAP = 30;   // minutes. A gap shorter than this is a walk between buildings, not free time.

  function freeOn(day, mine) {
    var todays = mine.placed
      .filter(function (c) { return c.meet.days.indexOf(day) >= 0; })
      .map(function (c) { return { code: c.code, start: c.meet.start, end: c.meet.end }; })
      .sort(function (a, b) { return a.start - b.start; });
    if (!todays.length) return { day: day, wholeDay: true, gaps: [], classes: [] };
    var gaps = [];
    for (var i = 1; i < todays.length; i += 1) {
      var prevEnd = Math.max(todays[i - 1].end, todays[i - 1].start);
      var gap = todays[i].start - prevEnd;
      if (gap >= MIN_GAP) gaps.push({ from: prevEnd, to: todays[i].start });
    }
    return { day: day, wholeDay: false, gaps: gaps, classes: todays };
  }

  /* ---------------------------------------------------------------------------------------------
     Scoring a section against what was asked.

     `miss` is what this section FAILS. `penalty` is how far off it is. A section that misses
     nothing answers the question; a section that misses something is only ever shown as the
     nearest thing, and labelled as such. The distinction is the whole honesty of this feature: a
     near-miss presented as an answer is worse than no answer, because the student registers for it.
     --------------------------------------------------------------------------------------------- */
  function scoreSection(row, a) {
    var meet = meetOf(row);
    var miss = [];
    var penalty = 0;

    if (a.days && a.days.length) {
      if (!meet) { miss.push('days'); penalty += 900; }
      else {
        var hit = a.days.filter(function (d) { return meet.days.indexOf(d) >= 0; });
        if (!hit.length) { miss.push('days'); penalty += 800; }
        else if (hit.length < a.days.length) penalty += 30;   // meets on some of them, not all
      }
    }

    /* "at 3pm" is about when a class STARTS. Ranking by distance to the nearest edge of the
       meeting put a 2:10–3:00 section above a 3:10 one, because it happens to END at exactly
       three — which is not what anybody asking means, and read as obviously wrong the moment the
       rows were on screen rather than in a test.

       So distance is measured from the START, always. A class that spans the hour still counts as
       an answer rather than a near-miss — a two-hour lab running 2:00–4:00 does put you in a room
       at 3 — but it sorts behind anything that actually begins near the time asked for. */
    var target = toMin(a.at_time);
    if (target != null) {
      if (!meet) { miss.push('time'); penalty += 900; }
      else {
        var off = Math.abs(meet.start - target);
        var spans = (target >= meet.start && target <= meet.end);
        penalty += off;
        if (off > NEAR_ENOUGH && !spans) miss.push('time');
      }
    }

    var after = toMin(a.start_after);
    if (after != null) {
      if (!meet) { miss.push('time'); penalty += 900; }
      else if (meet.start < after) { miss.push('time'); penalty += (after - meet.start); }
    }

    var before = toMin(a.end_before);
    if (before != null) {
      if (!meet) { miss.push('time'); penalty += 900; }
      else if (meet.end > before) { miss.push('time'); penalty += (meet.end - before); }
    }

    if (a.open_only === true) {
      var s = seatOf(row);
      if (!(s && s.cls === 'open')) { miss.push('open seats'); penalty += 600; }
    } else if (a.open_only === false) {
      var s2 = seatOf(row);
      if (!(s2 && s2.cls === 'wait')) { miss.push('a waitlist'); penalty += 600; }
    }

    if (a.component) {
      var label = compOf(row);
      var want = String(a.component).toUpperCase().slice(0, 3);
      if (!label || label !== want) { miss.push('labs or lectures'); penalty += 500; }
    }

    if (a.instruction_mode) {
      var mode = modeOf(row);
      /* "online" from a student means either kind of online; the feed distinguishes them. */
      var okMode = mode === a.instruction_mode
        || (a.instruction_mode === 'async' && mode === 'sync_online')
        || (a.instruction_mode === 'sync_online' && mode === 'async');
      if (!okMode) { miss.push('online or in person'); penalty += 500; }
    }

    return { row: row, meet: meet, miss: miss, penalty: penalty };
  }

  /* Which of the router's words this build genuinely cannot act on, given the sections in hand.
     Deliberately computed rather than listed: `instruction_mode` is answerable only if these rows
     carry a mode at all, and claiming otherwise in either direction is a lie about the data. */
  function unsupported(a, rows) {
    var out = [];
    if (a.min_rating != null) out.push('a rating');
    if (a.instruction_mode) {
      var anyMode = rows.some(function (r) { return r && (r.mode || r.instruction_mode); });
      if (!anyMode) out.push('online or in person');
    }
    return out;
  }

  /* ---------------------------------------------------------------------------------------------
     Going somewhere — WITHOUT closing.
     Each of these calls the function the app already uses for that tap, so a Hawk row and a card
     in Explore land in the same place by the same route. None of them close the box: staying open
     through a navigation is the entire feature.
     --------------------------------------------------------------------------------------------- */
  function goClass(code) {
    if (has('openClassPage')) { try { global.openClassPage(code); return 'Opened ' + code; } catch (_) {} }
    searchInExplore(code);
    return 'Searched Explore for ' + code;
  }

  /* A section lives on its course's page. `cpRefresh(crn)` is how the rest of the app says "and
     this is the row you came for" — the class page marks it. If that function is ever removed the
     student still lands on the right page, one row short of perfect, rather than nowhere. */
  function goSection(code, crn, label) {
    var went = goClass(code);
    try { if (crn && has('cpRefresh')) global.cpRefresh(String(crn)); } catch (_) {}
    return (went.indexOf('Opened') === 0 && label) ? ('Opened ' + label) : went;
  }

  function goProfessor(name) {
    var id = null;
    try { if (has('matchProfId')) id = global.matchProfId(name); } catch (_) {}
    if (id && has('openProf')) { try { global.openProf(id); return 'Opened ' + name; } catch (_) {} }
    searchInExplore(name);
    return 'Searched Explore for ' + name;
  }

  function goGeArea(key) {
    try {
      if (has('show')) global.show('explore');
      if (has('exSetGeArea')) { global.exSetGeArea(key); return 'Opened GE ' + key; }
    } catch (_) {}
    searchInExplore(key);
    return 'Searched Explore for ' + key;
  }

  /* The fallback for a question the router could not place: the app's own search with the
     student's own words in it. That is the bar a fallback has to clear — no worse than what they
     would have got by typing in the search box themselves. */
  function searchInExplore(text, subject) {
    try {
      if (has('show')) global.show('explore');
      if (has('setExMode')) global.setExMode('classes');
      if (subject && has('setExDept')) global.setExDept(subject);
      var box = document.getElementById('exQuery');
      if (box) {
        box.value = text || '';
        box.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (has('renderExplore')) global.renderExplore();
    } catch (_) {}
    return 'Searched Explore';
  }

  /* ---------------------------------------------------------------------------------------------
     Turning a route into rows.
     --------------------------------------------------------------------------------------------- */
  /* Which questions are answered with SECTIONS rather than a course. "fits my schedule" belongs
     here and was missing: it is a question about meeting times, so answering it with the course —
     one row, no times, nothing filtered — silently ignored the only part that was asked. */
  function wantsSections(a) {
    return !!(a.days || a.at_time || a.start_after || a.end_before
      || a.open_only !== undefined || a.component || a.fits_my_schedule || a.sort || a.instruction_mode);
  }

  function sectionRows(code, a) {
    var rows = sectionsOf(code);
    if (!rows.length) return null;

    var scored = rows.map(function (r) {
      var sc = scoreSection(r, a);
      sc.prof = profOf(r);
      return sc;
    });
    /* "best section of X" sorts by the professor's rating, with fit as the tiebreak. Unrated
       instructors sort last rather than being invented a score. */
    if (a.sort === 'rating') {
      scored.sort(function (x, y) {
        var rx = x.prof && x.prof.rating != null ? x.prof.rating : -1;
        var ry = y.prof && y.prof.rating != null ? y.prof.rating : -1;
        return (ry - rx) || (x.penalty - y.penalty);
      });
    } else {
      scored.sort(function (x, y) { return x.penalty - y.penalty; });
    }

    var exact = scored.filter(function (x) { return !x.miss.length; });
    var show = a.sort === 'rating' ? scored.slice(0, 4)
      : (exact.length ? exact.slice(0, MAX_SECTIONS) : scored.slice(0, 2));

    var mine = mySchedule();
    return show.map(function (x) {
      var num = secNumber(x.row);
      var label = code + (num ? '-' + num : '');
      var crn = x.row.class_nbr || x.row.crn;
      var chip = seatChip(x.row);
      /* EVERY section row now says whether it fits the week the student already has. This is the
         single highest-value thing on the row and it costs nothing: a section with seats that
         collides with the class you are already in is not an answer, and until now Hawk showed it
         exactly like one. */
      var hits = clashesWith(x.meet, mine, code);
      var who = x.prof;
      var yours = isMine(code, x.row);
      return {
        code: label,
        name: meetLabel(x.row),
        sub: who ? who.name : null,
        chip: yours ? { text: 'yours', tone: 'open' } : chip,
        chip2: who ? ratingChip(who.rating) : null,
        near: (exact.length || a.sort === 'rating') ? null : nearWhy(x, a),
        clash: hits.length ? hits : null,
        go: function () { return goSection(code, crn, label); }
      };
    }).filter(function (r) {
      /* "…that fits my schedule" is a filter, not a decoration. Asked for explicitly, a clashing
         section is not a result. Not asked for, it is shown and labelled. */
      return a.fits_my_schedule ? !r.clash : true;
    });
  }

  /* Why this row is only the closest thing. One short phrase, because a student reading "closest"
     with no reason has to open it to find out what is wrong with it. */
  function nearWhy(x, a) {
    if (x.miss.indexOf('days') >= 0) return 'closest — different day';
    if (x.miss.indexOf('time') >= 0) {
      var t = toMin(a.at_time || a.start_after || a.end_before);
      if (t != null && x.meet) return 'closest — ' + clock12(x.meet.start);
      return 'closest — different time';
    }
    if (x.miss.indexOf('open seats') >= 0) return 'closest — not open';
    if (x.miss.indexOf('a waitlist') >= 0) return 'closest — not waitlisted';
    if (x.miss.indexOf('labs or lectures') >= 0) return 'closest — other component';
    return 'closest';
  }

  function coursesFor(args, cat) {
    var out = [];
    Object.keys(cat.courses).forEach(function (code) {
      if (args.subject && code.split(/\s+/)[0] !== args.subject) return;
      out.push(code);
    });
    /* Courses with live sections first: somebody asking about a subject wants what is being taught
       this term, not the back of the catalog. */
    out.sort(function (a, b) {
      var sa = sectionsOf(a).length ? 1 : 0;
      var sb = sectionsOf(b).length ? 1 : 0;
      return sb - sa || a.localeCompare(b);
    });
    return out.slice(0, MAX_ROWS);
  }

  function courseChip(code) {
    var rows = sectionsOf(code);
    if (!rows.length) return null;
    var open = 0, any = false;
    rows.forEach(function (r) {
      var s = seatOf(r);
      if (s && s.cls === 'open') { any = true; if (s.n != null) open += s.n; }
    });
    if (!any) return { text: 'full', tone: 'full' };
    return { text: (open ? open + ' open' : 'open'), tone: 'open' };
  }

  /* ===============================================================================================
     THE PLANNER — ONE SEARCH THAT HOLDS EVERY CONSTRAINT.

     "Recommend a GE I still need that fits my schedule with the highest-rated professors" is four
     constraints. Hawk used to pick ONE tool per question, so it grabbed "requirements", dropped the
     other three and said "open your ledger" — Tate tapped Not it?, which is how this exists.

     A hard schedule question is almost always a combination of things the device can already
     check: which classes are in scope, which of their sections meet when, whether a section
     collides with your week, and who teaches it. So instead of more single-purpose tools there is
     one composable search, and the model's whole job on a hard question is filling its slots —
     which is the thing models are reliably good at. Every fact in the answer still comes from the
     app's own data through the app's own functions.

     Scopes: ge_unmet (GE areas your ledger says are open) · required (every unmet requirement)
             · ge_area (one area) · subject (a department).
     Then:   days · times · open seats · lab/lecture · online/in person · fits my week.
     Ranked: rating (professor) · seats · easiest — and there is no difficulty data at all in the
             live roster (0 of 2,603, measured 2026-09-24), so "easiest" says so and ranks by rating
             rather than inventing an order.
     =============================================================================================== */

  /* The app's geAreaKeyOf, replicated because it lives inside a closure. One deliberate difference:
     an upper-division slot titled "Area 2" or "Area 5" maps to U25, the key GE_COURSES actually
     uses. The app's own version returns "UD2", which matches no course. */
  function geKeyOfTitle(title) {
    var t = String(title || '');
    if (!/\bGE\b/i.test(t)) return null;
    if (/Upper-?Division/i.test(t)) {
      var u = t.match(/Area\s*(\d)/i);
      if (!u) return null;
      return (u[1] === '2' || u[1] === '5') ? 'U25' : 'UD' + u[1];
    }
    var m = t.match(/\(([0-9]+[A-C]?)\)/); if (m) return m[1].toUpperCase();
    m = t.match(/Area\s*([0-9]+[A-C]?)/i); return m ? m[1].toUpperCase() : null;
  }

  function geAreaKeys() {
    try { return (GE_AREAS || []).map(function (a) { return String(a.key).toUpperCase(); }); } catch (_) { return []; }
  }

  /* "3" means 3A and 3B; "UD3" means itself. A key nothing matches is reported, never widened. */
  function geKeysMatching(key) {
    var k = String(key || '').toUpperCase().replace(/\s+/g, '');
    var all = geAreaKeys();
    if (all.indexOf(k) >= 0) return [k];
    if (/^\d$/.test(k)) return all.filter(function (x) { return x.charAt(0) === k && /^\d[A-C]?$/.test(x); });
    return [];
  }

  function geLabel(key) {
    try {
      var a = (GE_AREAS || []).filter(function (x) { return String(x.key).toUpperCase() === key; })[0];
      return a ? a.label : 'GE ' + key;
    } catch (_) { return 'GE ' + key; }
  }

  function geCoursesIn(keys) {
    var out = [];
    try {
      (GE_COURSES || []).forEach(function (c) {
        var k = String((c && c.areaKey) || '').toUpperCase();
        if (keys.indexOf(k) >= 0) out.push({ code: c.code, name: c.name, tag: 'GE ' + k });
      });
    } catch (_) {}
    return out;
  }

  function ledger() {
    try {
      if (!has('plLedgerCompute')) return null;
      var lc = global.plLedgerCompute();
      if (!lc || !lc.led) return { noMajor: true };
      return lc;
    } catch (_) { return null; }
  }

  function unmetGeKeys(L) {
    var keys = [];
    (L.led.needU || []).forEach(function (sl) {
      var k = geKeyOfTitle(sl && sl.title);
      if (k && keys.indexOf(k) < 0) keys.push(k);
    });
    return keys;
  }

  function takenSet() {
    var s = {};
    try { if (has('completedCodes')) global.completedCodes().forEach(function (c) { s[c] = 1; }); } catch (_) {}
    myCodes().forEach(function (c) { s[c] = 1; });
    return s;
  }

  /* Which classes are in play, and a phrase for how the question was read. */
  function planCandidates(a, cat) {
    if (a.scope === 'ge_unmet' || a.scope === 'required') {
      var L = ledger();
      if (!L) return { problem: 'I can’t read your requirements in this build.' };
      if (L.noMajor) return { problem: 'Set your major first, and I’ll know what you still need.', fix: 'settings' };
      var keys = unmetGeKeys(L);
      var list = geCoursesIn(keys);
      var parts = [];
      if (a.scope === 'required') {
        (L.led.need || []).forEach(function (sl) {
          (sl.codes || []).forEach(function (c) { list.push({ code: c, name: cat.courses[c] || c, tag: 'Required' }); });
        });
        if ((L.led.need || []).length) parts.push('classes your major still requires');
      }
      if (keys.length) parts.push('GE you still need (' + keys.join(', ') + ')');
      if (!list.length) {
        return { problem: a.scope === 'ge_unmet'
          ? 'Your ledger shows no GE areas left to fill.'
          : 'Your ledger shows nothing left to take.', done: true };
      }
      return { list: list, label: parts.join(' and ') };
    }
    if (a.ge_area) {
      var gk = geKeysMatching(a.ge_area);
      if (!gk.length) return { problem: 'There’s no GE area called “' + a.ge_area + '” in the 2026 catalog.' };
      return { list: geCoursesIn(gk), label: gk.map(geLabel).join(' / ') };
    }
    if (a.subject) {
      var sl2 = [];
      Object.keys(cat.courses).forEach(function (c) { if (c.split(/\s+/)[0] === a.subject) sl2.push({ code: c, name: cat.courses[c] }); });
      return { list: sl2, label: a.subject + ' classes' };
    }
    return null;
  }

  function rankKey(x, sort) {
    var r = x.prof && x.prof.rating != null ? x.prof.rating : -1;
    var seats = 0;
    try { var st = seatOf(x.row); seats = st && st.n != null ? st.n : (st && st.cls === 'open' ? 1 : 0); } catch (_) {}
    if (sort === 'seats') return seats * 10 + r;
    return r * 1000 + Math.min(seats, 999);   // rating, then seats as the tiebreak
  }

  function planSearch(a, cat) {
    var cand = planCandidates(a, cat);
    if (!cand) return null;
    if (cand.problem) return cand;

    var taken = takenSet(), mine = mySchedule();
    var fits = !!a.fits_my_schedule;
    var n = { inScope: 0, offered: 0, matched: 0 };
    var seen = {}, results = [];

    cand.list.forEach(function (c) {
      if (seen[c.code]) return; seen[c.code] = 1;
      if (taken[c.code]) return;
      n.inScope += 1;
      var rows = sectionsOf(c.code);
      if (!rows.length) return;
      n.offered += 1;
      var best = null;
      rows.forEach(function (r) {
        var sc = scoreSection(r, a);
        if (sc.miss.length) return;
        var clash = sc.meet ? clashesWith(sc.meet, mine, c.code) : [];
        /* An async section fits every week. A section with no time that is NOT async cannot be
           checked, so "fits my schedule" leaves it out rather than promising it fits. */
        if (fits && (clash.length || (!sc.meet && modeOf(r) !== 'async'))) return;
        var x = { course: c, row: r, meet: sc.meet, prof: profOf(r), clash: clash };
        if (!best || rankKey(x, a.sort) > rankKey(best, a.sort)) best = x;
      });
      if (best) { n.matched += 1; results.push(best); }
    });

    results.sort(function (x, y) { return rankKey(y, a.sort) - rankKey(x, a.sort); });
    return { results: results, n: n, label: cand.label };
  }

  /* How the question was read, in one line, before any answer. On a four-constraint question this
     is the line that makes a wrong reading visible and a right one trustworthy. */
  function readingLine(a, label) {
    var bits = [label];
    if (a.fits_my_schedule) bits.push('fits your week');
    if (a.days) bits.push(a.days.map(function (d) { return DAY_FULL[d] || d; }).join('/'));
    if (a.at_time) bits.push('around ' + clock12(toMin(a.at_time)));
    if (a.start_after) bits.push('after ' + clock12(toMin(a.start_after)));
    if (a.end_before) bits.push('before ' + clock12(toMin(a.end_before)));
    if (a.open_only === true) bits.push('open seats');
    if (a.component) bits.push({ LAB: 'labs', LEC: 'lectures', ACT: 'activities', SEM: 'seminars' }[a.component] || a.component);
    if (a.instruction_mode) bits.push({ async: 'online', sync_online: 'online, live', in_person: 'in person', hybrid: 'hybrid' }[a.instruction_mode]);
    if (a.sort === 'rating' || a.sort === 'easiest') bits.push('best-rated professor first');
    if (a.sort === 'seats') bits.push('most open seats first');
    return bits.filter(Boolean).join(' · ');
  }

  function renderPlan(turn, result, cat, q) {
    var a = result.args || {};
    var out = planSearch(a, cat);
    if (!out) return false;
    lastSearch = a;

    if (out.problem) {
      turn.appendChild(make('div', 'hawk-note', out.problem));
      if (out.fix === 'settings') {
        turn.appendChild(rowEl({ code: '', name: 'Open Settings', chip: null, go: function () { return goPlace('settings'); } }));
      } else if (!out.done) {
        turn.appendChild(rowEl({ code: '', name: 'Open my ledger', chip: null, go: function () { return goPlace('ledger'); } }));
      }
      return true;
    }

    turn.appendChild(make('div', 'hawk-read', readingLine(a, out.label)));
    if (a.sort === 'easiest') {
      turn.appendChild(make('div', 'hawk-note',
        'There’s no difficulty data yet, so I can’t rank by easiest. Ranked by professor rating instead.'));
    }

    var top = out.results.slice(0, 5);
    if (!top.length) {
      turn.appendChild(make('div', 'hawk-note', out.n.offered
        ? 'None of the ' + out.n.offered + ' offered this term match all of that.'
        : 'None of these are offered this term.'));
      /* ONE TAP TO RELAX. An empty answer to a four-constraint question should say which
         constraint to drop, and drop it for you. */
      if (a.fits_my_schedule) relaxRow(turn, q, a, 'fits_my_schedule', 'Show ones that clash with my week too');
      else if (a.days || a.at_time || a.start_after || a.end_before) relaxRow(turn, q, a, 'time', 'Any day and time');
      else if (a.open_only) relaxRow(turn, q, a, 'open_only', 'Include full and waitlisted');
      return true;
    }

    top.forEach(function (x) {
      var label = x.course.code + '-' + secNumber(x.row);
      var crn = x.row.class_nbr || x.row.crn;
      turn.appendChild(rowEl({
        rich: true,
        code: label,
        name: x.course.name || cat.courses[x.course.code] || x.course.code,
        sub: [meetLabel(x.row), x.prof ? x.prof.name : null, x.course.tag || null].filter(Boolean).join(' · '),
        chip2: x.prof ? ratingChip(x.prof.rating) : null,
        chip: isMine(x.course.code, x.row) ? { text: 'yours', tone: 'open' } : seatChip(x.row),
        clash: x.clash && x.clash.length ? x.clash : null,
        go: function () { return goSection(x.course.code, crn, label); }
      }));
    });
    turn._explain = {
      reading: readingLine(a, out.label),
      rows: top.map(function (x) {
        return { code: x.course.code + '-' + secNumber(x.row), title: x.course.name || cat.courses[x.course.code] || '',
                 when: meetLabel(x.row), prof: x.prof ? x.prof.name : '', rating: x.prof ? x.prof.rating : null,
                 seats: seatsOf(x.row), tag: x.course.tag || '', fits: !(x.clash && x.clash.length) };
      })
    };
    turn.appendChild(make('div', 'hawk-count',
      out.n.matched + ' of ' + out.n.offered + ' offered this term match'
      + (out.n.inScope > out.n.offered ? ' · ' + (out.n.inScope - out.n.offered) + ' not offered' : '')
      + (out.results.length > top.length ? ' · showing the top ' + top.length : '')));
    return true;
  }

  function relaxRow(turn, q, a, what, text) {
    turn.appendChild(rowEl({
      code: '', name: text, chip: null,
      go: function () {
        var b = {}; Object.keys(a).forEach(function (k) { b[k] = a[k]; });
        if (what === 'time') { delete b.days; delete b.at_time; delete b.start_after; delete b.end_before; }
        else delete b[what];
        render(q, { prerouted: true, confident: true, in_scope: true, tool: 'search_sections', args: b,
                    corrections: [], leftovers: [], signals: [] }, buildCatalog());
        return 'Loosened it';
      }
    }));
  }

  /* ===============================================================================================
     BUILD MY TERM — "15 units, no Fridays, GEs I need, best professors" → two or three whole weeks.

     Everything here runs on the device, from the same sections, the same ledger and the same clash
     check as every other answer. The model's only part is reading the sentence into build_term's
     arguments; it never picks a class. What it hands back is a SEARCH over real sections with the
     student's real week as a hard constraint, so a schedule Hawk shows is one the calendar will
     draw without a single overlap.

     WHAT IT WILL NOT DO. Pair a lecture with its lab: the feed does not say which lab goes with
     which lecture, so a class that has both is built on its lecture and says "pick a lab too".
     Invent a unit count: a class with no units on record is left out and counted, not guessed as
     four.
     =============================================================================================== */
  var BUILD_NODE_LIMIT = 40000;
  var BUILD_SECTIONS_PER_CLASS = 3;
  var BUILD_MAX_CLASSES = 16;
  var UNRATED = 3.3;   // a section with no rating sorts behind a 3.5 and ahead of a 3.0 — neutral, not zero

  function courseUnits(code) {
    var u = null;
    try { if (has('classInfo')) u = Number((global.classInfo(code) || {}).units); } catch (_) {}
    if (u == null || isNaN(u) || u <= 0) {
      try {
        (GE_COURSES || []).some(function (c) { if (c && c.code === code) { u = Number(c.units); return true; } return false; });
      } catch (_) {}
    }
    return (u != null && !isNaN(u) && u > 0) ? u : null;
  }

  function seatsOf(row) {
    try { var st = seatOf(row); return st && st.n != null ? st.n : (st && st.cls === 'open' ? 1 : 0); } catch (_) { return 0; }
  }

  function buildTerm(a, cat) {
    var target = a.units || 15;
    var includes = (a.include || []).slice();
    var cand;
    if (a.scope || !includes.length) {
      cand = planCandidates({ scope: a.scope || 'required' }, cat);
      if (cand && cand.problem && !includes.length) return cand;
      if (!cand || cand.problem) cand = { list: [], label: '' };
    } else {
      cand = { list: [], label: '' };
    }
    var list = includes.map(function (c) { return { code: c, name: cat.courses[c] || c, tag: null, must: true }; })
      .concat(cand.list);

    var mine = mySchedule() || { placed: [], unplaced: [], empty: true };
    var fixedUnits = 0, fixedUnknown = [];
    myCodes().forEach(function (c) { var u = courseUnits(c); if (u) fixedUnits += u; else fixedUnknown.push(c); });
    var taken = takenSet();
    var off = a.days_off || [];
    var filt = { start_after: a.start_after, end_before: a.end_before, open_only: a.open_only === true ? true : undefined };
    var noUnits = [], notOffered = 0, blocked = 0;
    var seen = {}, pool = [];

    list.forEach(function (c) {
      if (seen[c.code]) return; seen[c.code] = 1;
      if (taken[c.code] && !c.must) return;
      var u = courseUnits(c.code);
      if (!u) { noUnits.push(c.code); return; }
      var rows = sectionsOf(c.code);
      if (!rows.length) { notOffered += 1; return; }
      /* Lecture first: a class offered as LEC + LAB is built on its lecture. */
      var comps = {};
      rows.forEach(function (r) { comps[compOf(r) || '?'] = 1; });
      var primary = comps.LEC ? 'LEC' : null;
      var needsMore = primary && Object.keys(comps).some(function (k) { return k !== 'LEC' && k !== '?'; });
      var secs = [];
      rows.forEach(function (r) {
        if (primary && compOf(r) !== primary) return;
        var sc = scoreSection(r, filt);
        if (sc.miss.length) return;
        if (!sc.meet && modeOf(r) !== 'async') return;          // no time and not async: cannot be checked
        if (sc.meet && off.some(function (d) { return sc.meet.days.indexOf(d) >= 0; })) return;
        if (sc.meet && clashesWith(sc.meet, mine, c.code).length) return;
        var p = profOf(r);
        secs.push({ row: r, meet: sc.meet, prof: p, rating: p && p.rating != null ? p.rating : null, seats: seatsOf(r) });
      });
      if (!secs.length) { blocked += 1; return; }
      secs.sort(function (x, y) {
        var rx = x.rating != null ? x.rating : UNRATED, ry = y.rating != null ? y.rating : UNRATED;
        return a.sort === 'seats' ? (y.seats - x.seats) || (ry - rx) : (ry - rx) || (y.seats - x.seats);
      });
      var group = c.must ? 'must:' + c.code : (c.tag && /^GE /.test(c.tag) ? c.tag : 'code:' + c.code);
      pool.push({ course: c, units: u, secs: secs.slice(0, BUILD_SECTIONS_PER_CLASS), group: group,
                  needsMore: needsMore, must: !!c.must,
                  best: secs[0].rating != null ? secs[0].rating : UNRATED });
    });

    var missingMust = includes.filter(function (c) { return !pool.some(function (x) { return x.course.code === c; }); });
    pool.sort(function (x, y) { return (y.must - x.must) || (y.best - x.best); });
    pool = pool.slice(0, BUILD_MAX_CLASSES);

    var need = Math.max(0, target - fixedUnits);
    var lo = need - 1, hi = need + 1;
    var sols = [], nodes = 0, closest = null;
    var fixedMeets = mine.placed.map(function (p) { return p.meet; });

    function score(pick, units) {
      var r = 0, s = 0;
      pick.forEach(function (x) { r += x.sec.rating != null ? x.sec.rating : UNRATED; s += Math.min(x.sec.seats, 30); });
      var n = pick.length || 1;
      var base = a.sort === 'seats' ? (s / n) / 6 + (r / n) * 0.2 : (r / n) + (s / n) / 300;
      return base - Math.abs(units - need) * 0.15;
    }
    function keep(pick, units) {
      var sc = score(pick, units);
      sols.push({ pick: pick.slice(), units: units, score: sc });
      if (sols.length > 80) { sols.sort(function (p, q) { return q.score - p.score; }); sols.length = 40; }
    }
    function dfs(i, pick, units, meets, groups) {
      nodes += 1;
      if (nodes > BUILD_NODE_LIMIT) return;
      if (units > hi) return;
      var mustLeft = pool.slice(i).some(function (x) { return x.must; });
      if (!mustLeft && units >= lo && pick.length) keep(pick, units);
      if (!mustLeft && pick.length && (!closest || units > closest.units || (units === closest.units && score(pick, units) > closest.score))) {
        closest = { pick: pick.slice(), units: units, score: score(pick, units) };
      }
      if (i >= pool.length) return;
      var c = pool[i];
      if (!groups[c.group]) {
        for (var k = 0; k < c.secs.length; k += 1) {
          var s = c.secs[k];
          if (s.meet && meets.some(function (m) { return overlaps(m, s.meet); })) continue;
          groups[c.group] = 1;
          pick.push({ c: c, sec: s });
          dfs(i + 1, pick, units + c.units, s.meet ? meets.concat([s.meet]) : meets, groups);
          pick.pop();
          delete groups[c.group];
        }
      }
      if (!c.must) dfs(i + 1, pick, units, meets, groups);
    }
    if (!missingMust.length) dfs(0, [], 0, fixedMeets, {});

    sols.sort(function (p, q) { return q.score - p.score; });
    /* Two or three options that are actually different: a new option must change at least one
       class, not just one section of the same classes. */
    var opts = [];
    sols.forEach(function (s) {
      if (opts.length >= 3) return;
      var codes = s.pick.map(function (x) { return x.c.course.code; }).sort().join('|');
      if (opts.some(function (o) { return o.key === codes; })) return;
      opts.push({ key: codes, pick: s.pick, units: s.units, score: s.score });
    });
    var short = false;
    if (!opts.length && closest) { opts.push({ key: '', pick: closest.pick, units: closest.units, score: closest.score }); short = true; }

    return {
      options: opts, short: short, target: target, need: need, label: cand.label,
      fixedUnits: fixedUnits, fixedCount: myCodes().length, fixedUnknown: fixedUnknown,
      poolSize: pool.length, noUnits: noUnits, notOffered: notOffered, blocked: blocked,
      missingMust: missingMust, capped: nodes > BUILD_NODE_LIMIT
    };
  }

  function buildReading(a, label) {
    var bits = [(a.units || 15) + ' units'];
    if (label) bits.push(label);
    if (a.include && a.include.length) bits.push('with ' + a.include.join(', '));
    if (a.days_off && a.days_off.length) bits.push('no ' + a.days_off.map(function (d) { return DAY_FULL[d] + 's'; }).join(' or '));
    if (a.start_after) bits.push('nothing before ' + clock12(toMin(a.start_after)));
    if (a.end_before) bits.push('done by ' + clock12(toMin(a.end_before)));
    if (a.open_only) bits.push('open seats');
    bits.push(a.sort === 'seats' ? 'most open seats first' : 'best-rated professors first');
    return bits.join(' · ');
  }

  /* The week at a glance: five columns, one block per class. The student's saved classes are drawn
     dimmed, so what the option ADDS is what stands out. */
  function weekStrip(pick, mine) {
    var blocks = [];
    (mine && mine.placed || []).forEach(function (p) { blocks.push({ meet: p.meet, code: p.code, fixed: true }); });
    pick.forEach(function (x) { if (x.sec.meet) blocks.push({ meet: x.sec.meet, code: x.c.course.code, fixed: false }); });
    if (!blocks.length) return null;
    /* The scale is the day this option actually has, so a late-start week LOOKS late. */
    var lo = 24 * 60, hi = 0;
    blocks.forEach(function (b) { lo = Math.min(lo, b.meet.start); hi = Math.max(hi, b.meet.end); });
    lo = Math.floor(lo / 60) * 60; hi = Math.ceil(hi / 60) * 60;
    if (hi - lo < 240) hi = Math.min(24 * 60, lo + 240);
    var wrap = make('div', 'hawk-week');
    wrap.setAttribute('aria-hidden', 'true');
    ['Mo', 'Tu', 'We', 'Th', 'Fr'].forEach(function (d) {
      var col = make('div', 'hawk-week__col');
      col.appendChild(make('span', 'hawk-week__day', d.charAt(0)));
      var lane = make('div', 'hawk-week__lane');
      blocks.forEach(function (b) {
        if (b.meet.days.indexOf(d) < 0) return;
        var el = make('span', 'hawk-week__blk' + (b.fixed ? ' hawk-week__blk--fixed' : ''));
        el.style.top = ((b.meet.start - lo) / (hi - lo) * 100).toFixed(1) + '%';
        el.style.height = Math.max(4, (b.meet.end - b.meet.start) / (hi - lo) * 100).toFixed(1) + '%';
        el.title = b.code;
        lane.appendChild(el);
      });
      col.appendChild(lane);
      wrap.appendChild(col);
    });
    var scale = make('div', 'hawk-week__scale');
    scale.appendChild(make('span', null, clock12(lo)));
    scale.appendChild(make('span', null, clock12(hi)));
    wrap.appendChild(scale);
    return wrap;
  }

  var lastBuild = null;

  /* SAVE A BUILT TERM AS A PLAN (2026-09-25). A built option becomes Plan A, B or C — the plan
     keeps exactly the sections on screen, every one of them is watched from then on, and Undo puts
     the slot back as it was. An empty slot says "Save as", a full one says "Replace", so the
     student can see before tapping that something will be overwritten. */
  function planSaveBox(getOpt, getIx) {
    var P = global.TCPlans;
    if (!P) return null;
    var el = make('div', 'hawk-plansave');
    function paint() {
      el.textContent = '';
      el.appendChild(make('div', 'hawk-plansave__hd', 'Save Option ' + (getIx() + 1) + ' as a plan'));
      var row = make('div', 'hawk-plansave__row');
      P.slots.forEach(function (s) {
        var fullNow = P.get(s).sections.length > 0;
        var b = make('button', 'hawk-plansave__btn', (fullNow ? 'Replace ' : 'Save as ') + s);
        b.type = 'button';
        b.addEventListener('click', function () {
          var o = getOpt(); if (!o) return;
          var picks = o.pick.map(function (x) { return { code: x.c.course.code, class_nbr: String(x.sec.row.class_nbr || x.sec.row.crn || '') }; });
          var r = P.saveFromBuild(s, picks);
          paint();
          var done = make('div', 'hawk-plansave__done', 'Saved as Plan ' + s + ' — every class in it is now watched. '
            + (r.dropped ? r.dropped + (r.dropped === 1 ? ' class had' : ' classes had') + ' no class number and ' + (r.dropped === 1 ? 'wasn’t' : 'weren’t') + ' saved. ' : ''));
          var u = make('button', 'hawk-plansave__undo', 'Undo');
          u.type = 'button';
          u.addEventListener('click', function () { r.undo(); paint(); el.appendChild(make('div', 'hawk-plansave__done', 'Plan ' + s + ' is back as it was.')); });
          done.appendChild(u);
          var open = make('button', 'hawk-plansave__undo', 'Open Plans');
          open.type = 'button';
          open.addEventListener('click', function () { goPlace('watchlist'); });
          done.appendChild(document.createTextNode(' · '));
          done.appendChild(open);
          el.appendChild(done);
        });
        row.appendChild(b);
      });
      el.appendChild(row);
    }
    paint();
    return { el: el, paint: paint };
  }

  function renderBuild(turn, result, cat, q) {
    var a = result.args || {};
    lastBuild = a; lastSearch = null;
    var out = buildTerm(a, cat);

    if (out.problem) {
      turn.appendChild(make('div', 'hawk-note', out.problem));
      if (out.fix === 'settings') turn.appendChild(rowEl({ code: '', name: 'Open Settings', chip: null, go: function () { return goPlace('settings'); } }));
      return true;
    }
    turn.appendChild(make('div', 'hawk-read', buildReading(a, out.label)));

    if (out.fixedCount) {
      turn.appendChild(make('div', 'hawk-note', 'Built around the ' + out.fixedCount
        + (out.fixedCount === 1 ? ' class' : ' classes') + ' you’ve saved (' + out.fixedUnits + ' units).'));
    }
    if (out.need <= 0) {
      turn.appendChild(make('div', 'hawk-note hawk-note--good', 'You already have ' + out.fixedUnits + ' units saved.'));
      return true;
    }
    if (out.missingMust.length) {
      turn.appendChild(make('div', 'hawk-note', 'No section of ' + out.missingMust.join(', ')
        + ' fits all of that, so I couldn’t build around it.'));
      relaxBuild(turn, q, a);
      return true;
    }
    if (!out.options.length) {
      turn.appendChild(make('div', 'hawk-note', out.poolSize
        ? 'I couldn’t fit a schedule together with all of that.'
        : 'None of the classes in play have a section that fits all of that.'));
      relaxBuild(turn, q, a);
      return true;
    }
    if (out.short) {
      turn.appendChild(make('div', 'hawk-note', 'The closest I could get is ' + (out.options[0].units + out.fixedUnits)
        + ' units — not enough classes fit all of that.'));
    }

    var mine = mySchedule();
    var holder = make('div', 'hawk-build');
    var pills = make('div', 'hawk-opts');
    var body = make('div', 'hawk-build__body');

    var curIx = 0;
    function show(ix) {
      var o = out.options[ix];
      curIx = ix;
      try { if (saveBox) saveBox.paint(); } catch (_) {}
      Array.prototype.forEach.call(pills.children, function (b, j) { b.classList.toggle('is-on', j === ix); b.setAttribute('aria-pressed', j === ix ? 'true' : 'false'); });
      body.textContent = '';
      var w = weekStrip(o.pick, mine);
      if (w) body.appendChild(w);
      o.pick.forEach(function (x) {
        var code = x.c.course.code, label = code + '-' + secNumber(x.sec.row), crn = x.sec.row.class_nbr || x.sec.row.crn;
        body.appendChild(rowEl({
          rich: true, code: label,
          name: x.c.course.name || cat.courses[code] || code,
          sub: [meetLabel(x.sec.row), x.sec.prof ? x.sec.prof.name : null, x.c.course.tag || null,
                x.c.units + 'u', x.c.needsMore ? 'pick a lab too' : null].filter(Boolean).join(' · '),
          chip2: x.sec.prof ? ratingChip(x.sec.prof.rating) : null,
          chip: seatChip(x.sec.row),
          go: function () { return goSection(code, crn, label); }
        }));
      });
      var say = turn.querySelector('.hawk-say');
      if (say) say.hidden = ix !== 0;
    }

    out.options.forEach(function (o, ix) {
      var rated = o.pick.filter(function (x) { return x.sec.rating != null; });
      var avg = rated.length ? rated.reduce(function (s, x) { return s + x.sec.rating; }, 0) / rated.length : null;
      var b = make('button', 'hawk-opt');
      b.type = 'button';
      b.appendChild(make('span', 'hawk-opt__name', 'Option ' + (ix + 1)));
      b.appendChild(make('span', 'hawk-opt__meta', (o.units + out.fixedUnits) + 'u' + (avg != null ? ' · ' + avg.toFixed(1) + '★' : '')));
      b.addEventListener('click', function () { show(ix); });
      pills.appendChild(b);
    });
    if (out.options.length > 1) holder.appendChild(pills);
    holder.appendChild(body);
    turn.appendChild(holder);
    var saveBox = planSaveBox(function () { return out.options[curIx]; }, function () { return curIx; });
    if (saveBox) turn.appendChild(saveBox.el);
    show(0);

    var foot = [];
    foot.push(out.options.length + (out.options.length === 1 ? ' schedule' : ' schedules') + ' from ' + out.poolSize + ' classes that fit');
    if (out.notOffered) foot.push(out.notOffered + ' not offered');
    if (out.noUnits.length) foot.push(out.noUnits.length + ' with no unit count left out');
    turn.appendChild(make('div', 'hawk-count', foot.join(' · ')));

    var first = out.options[0];
    turn._explain = {
      reading: buildReading(a, out.label),
      rows: first.pick.map(function (x) {
        return { code: x.c.course.code + '-' + secNumber(x.sec.row), title: x.c.course.name || cat.courses[x.c.course.code] || '',
                 when: meetLabel(x.sec.row), prof: x.sec.prof ? x.sec.prof.name : '', rating: x.sec.rating,
                 seats: x.sec.seats, tag: x.c.course.tag || '' };
      })
    };
    return true;
  }

  function relaxBuild(turn, q, a) {
    var b = {}; Object.keys(a).forEach(function (k) { b[k] = a[k]; });
    var text;
    if (b.start_after || b.end_before) { delete b.start_after; delete b.end_before; text = 'Any time of day'; }
    else if (b.days_off) { delete b.days_off; text = 'Any day of the week'; }
    else if (b.open_only) { delete b.open_only; text = 'Include full and waitlisted'; }
    else return;
    turn.appendChild(rowEl({ code: '', name: text, chip: null, go: function () {
      render(q, { prerouted: true, confident: true, in_scope: true, tool: 'build_term', args: b,
                  corrections: [], leftovers: [], signals: [] }, buildCatalog());
      return 'Loosened it';
    } }));
  }

  /* "make it 12 units" / "no fridays" right after a build changes THAT build, on the device. */
  function buildFollowUp(q, result) {
    if (!lastBuild || !R.buildMods) return null;
    if (result && result.tool === 'build_term' && result.prerouted) return null;   // a new build says so itself
    var got = R.buildMods(q);
    var keys = Object.keys(got.mods);
    var extra = /\b(?:open(?:\s+seats)?|best|highest|rated)\b/.test(String(q).toLowerCase());
    if (!keys.length && !extra) return null;
    var left = got.rest.split(/\s+/).filter(function (w) {
      return w && w.length > 3 && !/^(make|instead|then|also|only|just|what|about|with|want|have|classes|class|it|please|open|seats?|best|highest|rated|professors?|profs?|teachers?)$/.test(w);
    });
    if (left.length) return null;
    var merged = {}; Object.keys(lastBuild).forEach(function (k) { merged[k] = lastBuild[k]; });
    keys.forEach(function (k) { merged[k] = got.mods[k]; });
    if (/\bopen\b/i.test(q)) merged.open_only = true;
    if (/\b(?:best|highest|rated)\b/i.test(q)) merged.sort = 'rating';
    return { prerouted: true, confident: true, in_scope: true, followUp: true, tool: 'build_term', args: merged,
             corrections: [], leftovers: [], signals: ['build'] };
  }

  function rowsFor(result, cat) {
    var rows = [];
    if (!result || !result.tool) return { rows: rows, unread: [] };
    var a = result.args || {};

    if (result.tool !== 'search_sections' && result.tool !== 'open_class' && result.tool !== 'open_professor') {
      return { rows: rows, unread: [] };
    }

    if (result.tool === 'open_professor') {
      var name = a.name;
      rows.push({ code: '', name: name, chip: null,
                  go: function () { return goProfessor(name); } });
      return { rows: rows, unread: [] };
    }

    if (a.ge_area) {
      rows.push({ code: a.ge_area, name: 'GE area ' + a.ge_area, chip: null,
                  go: function () { return goGeArea(a.ge_area); } });
      return { rows: rows, unread: [] };
    }

    if (a.course) {
      var secs = wantsSections(a) ? sectionRows(a.course, a) : null;
      if (secs && secs.length) {
        return { rows: secs, unread: unsupported(a, sectionsOf(a.course)) };
      }
      rows.push({ code: a.course, name: cat.courses[a.course] || a.course,
                  chip: courseChip(a.course),
                  go: function () { return goClass(a.course); } });
      return { rows: rows, unread: unsupported(a, sectionsOf(a.course)) };
    }

    if (a.subject) {
      var wantsFilter = wantsSections(a);
      var mine = wantsFilter ? mySchedule() : null;
      /* A WHOLE SUBJECT, FILTERED THROUGH ITS SECTIONS. "open STAT sections on tuesday" used to show
         every STAT course and apologise for the day. Now each course in the subject is kept only if
         at least one of its sections answers the filters — and the row says which section that is,
         so the student lands on a real section rather than a course they then have to search. */
      var picked = [];
      Object.keys(cat.courses).forEach(function (code) {
        if (code.split(/\s+/)[0] !== a.subject) return;
        if (!wantsFilter) { picked.push({ code: code }); return; }
        var rows = sectionsOf(code);
        if (!rows.length) return;
        var best = null;
        rows.forEach(function (r) {
          var sc = scoreSection(r, a);
          if (sc.miss.length) return;
          if (a.fits_my_schedule && clashesWith(sc.meet, mine, code).length) return;
          if (!best || sc.penalty < best.penalty) best = sc;
        });
        if (best) picked.push({ code: code, sec: best, prof: profOf(best.row) });
      });
      if (wantsFilter && a.sort === 'rating') {
        picked.sort(function (x, y) {
          var rx = x.prof && x.prof.rating != null ? x.prof.rating : -1;
          var ry = y.prof && y.prof.rating != null ? y.prof.rating : -1;
          return ry - rx;
        });
      } else if (!wantsFilter) {
        picked.sort(function (x, y) {
          var sa = sectionsOf(x.code).length ? 1 : 0, sb = sectionsOf(y.code).length ? 1 : 0;
          return sb - sa || x.code.localeCompare(y.code);
        });
      }
      picked.slice(0, MAX_ROWS).forEach(function (pk) {
        if (!pk.sec) {
          rows.push({ code: pk.code, name: cat.courses[pk.code] || pk.code, chip: courseChip(pk.code),
                      go: function () { return goClass(pk.code); } });
          return;
        }
        var label = pk.code + '-' + secNumber(pk.sec.row);
        var crn = pk.sec.row.class_nbr || pk.sec.row.crn;
        var hits = clashesWith(pk.sec.meet, mine, pk.code);
        rows.push({ code: label, name: meetLabel(pk.sec.row), sub: pk.prof ? pk.prof.name : null,
                    chip: isMine(pk.code, pk.sec.row) ? { text: 'yours', tone: 'open' } : seatChip(pk.sec.row), chip2: pk.prof ? ratingChip(pk.prof.rating) : null,
                    clash: hits.length ? hits : null,
                    go: function () { return goSection(pk.code, crn, label); } });
      });
      if (!wantsFilter) {
        rows.push({ code: '', name: 'Every ' + a.subject + ' class in Explore', chip: null,
                    go: function () { return searchInExplore('', a.subject); } });
      } else if (!picked.length) {
        return { rows: [], unread: unsupported(a, []), none: 'No ' + a.subject + ' section matches that this term.' };
      }
      return { rows: rows, unread: unsupported(a, []) };
    }

    /* Filters, but nothing to anchor them to — "something open in the morning" across the whole
       catalog. Hawk renders its own rows, so this would mean enumerating every course at Cal Poly
       and slicing four off the top, which is not an answer to that question.

       IT MUST NOT SAY "nothing matches". That is a false statement — there are plenty of morning
       classes — and a false statement is the one thing this product does not do. Say what is
       missing and hand the filters to the screen built to hold them. */
    return { rows: rows, unread: [], needsAnchor: true };
  }

  /* ===============================================================================================
     THE MODEL TIER.

     Reached only when the pre-router could not place the question. Everything about it is designed
     so that its absence is invisible: if the function is not deployed, the key is not set, the
     database says `enabled=false`, the cap is spent, the vendor is down or the request times out,
     the student gets the ordinary Explore search with their own words in it — which is exactly
     what they got before this tier existed. There is no state in which Hawk shows a spinner that
     dies.

     WHAT LEAVES THE BROWSER, when this path runs at all: the question, the term, and the rotating
     device pseudonym. Not the JWT's contents, not the schedule, not a friend, not a row. And what
     comes back is a tool call, never prose — so the answer is rendered by the same code that
     renders a pre-routed one, and there is no second way for Hawk to be wrong.
     =============================================================================================== */
  var AI_TIMEOUT = 9000;

  function aiUrl() {
    try {
      var base = (global.PROFESSIFY_CONFIG || {}).SUPABASE_URL;
      if (!base) return null;
      return String(base).replace(/\/+$/, '') + '/functions/v1/ask';
    } catch (_) { return null; }
  }

  /* The pseudonym `events` already uses. Identity never travels with a question; this is the same
     rotating device id the analytics table is keyed on, and the schema keeps it in a table that
     shares no joinable column with the one holding questions. */
  /* `evWho()` is ASYNC — it hashes the device salt with SubtleCrypto. Called without awaiting,
     it returns a Promise, and String(Promise) is "[object Promise]": every run would have logged
     the same sixteen characters of garbage as the pseudonym, and nothing would have complained.
     Resolves to '' when the function is missing, which the schema accepts. */
  function pseudonym() {
    try {
      if (has('evWho')) {
        return Promise.resolve(global.evWho()).then(function (w) {
          return String(w || '').slice(0, 32);
        }).catch(function () { return ''; });
      }
    } catch (_) {}
    return Promise.resolve('');
  }

  function currentTerm() {
    try { if (has('mcTerm')) return String(global.mcTerm() || ''); } catch (_) {}
    return '';
  }

  /* Resolves to a route-shaped object, or null when this tier cannot answer for ANY reason.
     Null is not an error path — it is the ordinary case on a build with the tier switched off. */
  function askModel(q) {
    return callAsk({ q: q }).then(function (j) {
      if (!j || j.fallback || !j.tool) return null;
      /* `prerouted: true` because this question IS routed — by the model rather than in the
         browser, which is what `viaModel` records. Returning false here made `render` treat
         every successful model answer as a failure to understand and print "I am not sure what
         you mean" over a perfectly good filter. */
      return { prerouted: true, viaModel: true, confident: true, in_scope: true,
               tool: j.tool, args: spaceCodes(j.args || {}), corrections: [], leftovers: [], signals: [] };
    });
  }

  /* The function validates course codes as "BUS4442"; every catalog key on the device is
     "BUS 4442". Without this, a model-routed "can I take bus 4442" looked up a course that does
     not exist and answered about nothing. */
  function spaceCodes(args) {
    var fix = function (v) {
      var m = /^([A-Z]{2,4})\s?(\d{3,4})$/.exec(String(v || '').toUpperCase().trim());
      return m ? m[1] + ' ' + m[2] : v;
    };
    var out = {};
    Object.keys(args).forEach(function (k) {
      var v = args[k];
      if (k === 'course' || k === 'a' || k === 'b') out[k] = fix(v);
      else if (k === 'include' && Array.isArray(v)) out[k] = v.map(fix);
      else out[k] = v;
    });
    return out;
  }

  /* One POST to the function, for either job. Resolves to its JSON, or null for ANY failure —
     signed out, no URL, timeout, network. Null is the ordinary case on a build with the tier off. */
  /* The signed-in session's token, or null. Signed out, NOTHING Hawk has is sent anywhere — the
     privacy policy says so, and both callAsk and logMiss stop here. */
  function sessionToken() {
    var token = null;
    try {
      var s = sb && sb.auth && sb.auth.session ? sb.auth.session() : null;
      token = s && s.access_token;
    } catch (_) {}
    if (token) return Promise.resolve(token);
    try {
      if (sb && sb.auth && typeof sb.auth.getSession === 'function') {
        return sb.auth.getSession().then(function (r) {
          return r && r.data && r.data.session ? r.data.session.access_token : null;
        }).catch(function () { return null; });
      }
    } catch (_) {}
    return Promise.resolve(null);
  }

  /* Global Privacy Control: the question still has to go to the model for Hawk to answer it, but
     TermChamp does not KEEP it — the function logs the run without its words, and misses are not
     logged at all. Mirrors how the Counting section honours the same signal. */
  function gpcOn() {
    try { return navigator.globalPrivacyControl === true; } catch (_) { return false; }
  }

  function callAsk(payload) {
    var url = aiUrl();
    if (!url) return Promise.resolve(null);
    if (gpcOn()) payload = Object.assign({ nolog: true }, payload);
    var go = sessionToken();

    return go.then(function (tok) {
      /* Signed out is not a failure: the model tier requires a session so that anonymous traffic
         cannot spend the budget, and a signed-out student simply keeps the free tier. */
      if (!tok) return null;
      return pseudonym().then(function (who) { return { tok: tok, who: who }; });
    }).then(function (ctx) {
      if (!ctx) return null;
      var ctl = (typeof AbortController === 'function') ? new AbortController() : null;
      var timer = setTimeout(function () { try { ctl && ctl.abort(); } catch (_) {} }, AI_TIMEOUT);
      return fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: 'Bearer ' + ctx.tok },
        body: JSON.stringify(Object.assign({ term: currentTerm(), who: ctx.who }, payload)),
        signal: ctl ? ctl.signal : undefined
      }).then(function (r) { return r.json(); }).then(function (j) {
        clearTimeout(timer);
        return j || null;
      }).catch(function () { clearTimeout(timer); return null; });
    }).catch(function () { return null; });
  }

  /* ---------------------------------------------------------------------------------------------
     The answer. One at a time: this replaces whatever was there.
     --------------------------------------------------------------------------------------------- */
  /* The last catalog question, kept ON THE DEVICE so a follow-up can lean on it. "open BUS sections"
     then "what about tuesday" merges the day into the previous search. Nothing about this ever goes
     to the model — it is one object in memory, and it stops feeling like a search box that forgets
     you the moment you refine. Only search results are remembered: a follow-up to "who is beth
     chance" has nothing sensible to merge into. */
  var lastSearch = null;

  function followUp(result) {
    if (!lastSearch || result.prerouted || result.refused) return null;
    /* "find me…" / "recommend…" opens a NEW question even when it names no subject. Merging it into
       the last search answered "find me something in the morning" with sections of whatever class
       was asked about before. */
    if ((result.signals || []).some(function (x) { return x === 'recommend' || x.indexOf('scope:') === 0; })) return null;
    var c = result.candidate && result.candidate.args ? result.candidate.args : null;
    if (!c) return null;
    var FILTERS = ['days', 'at_time', 'start_after', 'end_before', 'open_only', 'component',
                   'instruction_mode', 'min_rating', 'fits_my_schedule', 'sort'];
    var hasFilter = FILTERS.some(function (k) { return c[k] !== undefined; });
    var hasAnchor = c.course || c.subject || c.ge_area;
    /* A refinement is: no new anchor, at least one filter, and nothing the router could not read
       beyond the connective words a follow-up naturally starts with. */
    var strays = (result.leftovers || []).filter(function (w) { return !/^(about|what|instead|then|also|only|just|make|those|them|that|ones)$/.test(w); });
    if (hasAnchor || !hasFilter || strays.length) return null;
    var merged = {};
    Object.keys(lastSearch).forEach(function (k) { merged[k] = lastSearch[k]; });
    FILTERS.forEach(function (k) { if (c[k] !== undefined) merged[k] = c[k]; });
    return { prerouted: true, confident: true, in_scope: true, followUp: true,
             tool: 'search_sections', args: merged, corrections: result.corrections || [], leftovers: [], signals: [] };
  }

  /* AI-FIRST, 2026-09-23 (Tate: "AI reads everything non-trivial").

     Every question that is more than a bare lookup goes to the model, and the router's reading is
     kept as the answer it falls back to — on a timeout, when signed out, over the daily cap, or
     when the model says it can't answer something the router read cleanly. What stays on the
     device: a refusal, a screen name, a bare course code or professor, and a follow-up that merges
     into the last answer (Tate's call: follow-ups are client-side only). */
  /* Both readings of the last question — the router's and the model's — so "Not it?" can offer
     the one that wasn't shown. Memory only; never sent anywhere. */
  var readings = { local: null, model: null };

  function skipsModel(result) {
    if (!result) return false;
    if (result.refused || result.followUp) return true;
    if (!result.prerouted) return false;
    return result.tool === 'go_to' || result.tool === 'open_class' || result.tool === 'open_professor'
      || result.tool === 'help' || result.tool === 'open_section' || result.tool === 'set_theme';
  }

  function pickAnswer(viaModel, local) {
    if (!viaModel) return local;
    var localSure = local.prerouted && local.confident && local.tool && local.tool !== 'cant_answer';
    if (viaModel.tool === 'cant_answer' && localSure) return local;
    /* The router reads navigation phrases reliably ("take me to…", "open my…"). If it read this
       question cleanly as something ELSE, a model go_to is a guess — the live miss on 2026-09-23 was
       "which professor of mine has the highest rating" answered with a My classes button. */
    if (viaModel.tool === 'go_to' && localSure && local.tool !== 'go_to') return local;
    return viaModel;
  }

  function answer(q) {
    var cat = buildCatalog();
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
      if (thinking !== els.log.firstChild) return;   // they asked something else meanwhile
      readings = { local: result, model: viaModel };
      render(q, pickAnswer(viaModel, result), cat);
    });
  }

  /* WHAT THE FOOTER PROMISES HAS TO BE TRUE. With the model tier on, the question does leave the
     browser — to TermChamp's server and on to the AI vendor — so "nothing leaves" became a lie the
     day AI-first shipped. What stays true either way: the student's classes, friends and ledger
     never leave; the model sees the question and, for an explanation, only public catalog rows. */
  function privacyLine() {
    return aiUrl() ? 'Questions are read by AI · your classes stay on this device'
                   : 'Nothing you type here leaves your browser';
  }

  /* ---------------------------------------------------------------------------------------------
     THE VERIFIED EXPLANATION. One or two sentences under a recommendation, written by the model
     from the rows already on screen and nothing else. It is checked here, against those rows,
     before anyone reads it: every course code, every number and every capitalised name must be in
     them. One miss and the whole sentence is dropped — silently, because a missing sentence costs
     nothing and the rows already answer the question.
     --------------------------------------------------------------------------------------------- */
  var PLAIN_WORDS = ('a about all also an and any are as at because best both but by can consider either '
    + 'every fits for from go good grab great has have here highest if in is it its just most neither no '
    + 'none not note of on one only open or otherwise out pick plus rated seats since so solid strong '
    + 'take than that the their then there these this those to top try two three while with you your '
    + 'yours online async lecture lab monday tuesday wednesday thursday friday mondays tuesdays wednesdays '
    + 'thursdays fridays mon tue wed thu fri prof professor option week schedule class classes section '
    + 'sections ge area still need needs taught teaches rating ratings rated star stars each other '
    + 'morning afternoon evening early late later earlier fit fitting works work well am pm '
    + 'mo tu we th fr mowe tuth mowefr mwf').split(' ');

  function verifyExplanation(text, rows) {
    var t = String(text || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 320 || /https?:|www\./i.test(t)) return null;
    /* How a professor teaches is not in the rows and never will be; the model is told not to say
       it, and this is the check that it didn't. */
    if (/\b(?:easy|easier|easiest|hard|harder|hardest|tough|strict|lenient|curves?|exams?|tests?|quizz?es|homework|workload|boring|fun|engaging|chill|funny|grader|grading|teaching\s+style|lectures?\s+(?:are|is))\b/i.test(t)) return null;
    var hay = JSON.stringify(rows);
    var HAY = hay.toUpperCase();
    var codes = t.toUpperCase().match(/\b[A-Z]{2,4}\s?\d{3,4}\b/g) || [];
    for (var i = 0; i < codes.length; i += 1) {
      var c = codes[i].replace(/^([A-Z]+)\s?(\d+)$/, '$1 $2');
      if (HAY.indexOf(c) < 0) return null;
    }
    var nums = {};
    (hay.match(/\d+(?:\.\d+)?/g) || []).forEach(function (n) { nums[n] = 1; nums[String(parseFloat(n))] = 1; });
    var saidNums = t.replace(/\b[A-Z]{2,4}\s?\d{3,4}(?:-\d+)?\b/g, ' ').match(/\d+(?:\.\d+)?/g) || [];
    for (var j = 0; j < saidNums.length; j += 1) if (!nums[saidNums[j]] && !nums[String(parseFloat(saidNums[j]))]) return null;
    var words = {};
    (hay.toLowerCase().match(/[a-z][a-z'’-]*/g) || []).forEach(function (w) { words[w] = 1; });
    var caps = t.match(/\b[A-Z][a-z'’-]+\b/g) || [];
    for (var k = 0; k < caps.length; k += 1) {
      var w = caps[k].toLowerCase().replace(/['’]s$/, '');
      if (!words[w] && PLAIN_WORDS.indexOf(w) < 0) return null;
    }
    return t;
  }

  function explainTurn(q, turn) {
    var ex = turn && turn._explain;
    if (!ex || !ex.rows || ex.rows.length < 2 || !aiUrl()) return;
    callAsk({ mode: 'explain', q: q, reading: ex.reading, rows: ex.rows }).then(function (j) {
      if (!j || j.fallback || !j.args || !j.args.text) return;
      if (!turn.isConnected) return;                        // a newer answer replaced this one
      var ok = verifyExplanation(j.args.text, ex.rows);
      if (!ok) return;
      var say = make('div', 'hawk-say', ok);
      var anchorEl = turn.querySelector('.hawk-read');
      if (anchorEl && anchorEl.nextSibling) turn.insertBefore(say, anchorEl.nextSibling);
      else turn.appendChild(say);
      var opts = turn.querySelector('.hawk-opt.is-on');
      if (opts && opts !== turn.querySelector('.hawk-opt')) say.hidden = true;
      var said = turn.querySelector('.hawk-said');
      if (said && !said.querySelector('.hawk-fix--ai')) said.appendChild(make('span', 'hawk-fix hawk-fix--ai', 'AI'));
    });
  }

  /* A question that has left the browser takes a moment, and a box that sits still for a second is
     a box the student thinks is broken. This says what is happening in the same small voice as
     everything else, and is replaced by the answer whichever way it resolves. */
  function renderThinking(q) {
    els.log.textContent = '';
    var turn = make('div', 'hawk-turn');
    var said = make('div', 'hawk-said');
    said.appendChild(make('span', 'hawk-said__q', q));
    turn.appendChild(said);
    turn.appendChild(make('div', 'hawk-note hawk-thinking', 'Working that out…'));
    els.log.appendChild(turn);
    stamp();
    return turn;
  }

  /* ---------------------------------------------------------------------------------------------
     "NOT IT?" STAYS IN HAWK (Tate, 2026-09-23: "the not it shouldnt just go pasted into explore").
     It used to drop the question into Explore's search box, which searches class TITLES — so a
     sentence like "which professor of mine has the highest rating" found nothing and the student
     was worse off than before. Now it logs the miss and offers, inside the box, the other ways
     the question could have been read: the router's reading if the model's was shown (and the
     reverse), what the router would have guessed, and the obvious neighbours of the words used.
     Explore is still there, last, as a plain search — and "Say it another way" puts the question
     back in the box to rephrase.
     --------------------------------------------------------------------------------------------- */
  var TOOL_LABEL = {
    my_professors: 'Your professors, ranked by rating',
    my_free: 'When you’re free',
    my_conflicts: 'Clashes in your week',
    my_day: 'Your classes on a day',
    my_units: 'How many units you’re taking',
    my_requirements: 'What you still need',
    when_registration: 'When registration opens',
    game_plan: 'Your registration game plan',
    build_term: 'Build a whole term',
    friends_took: 'Classes your friends have taken',
    help: 'What Hawk can do'
  };

  function labelFor(r, cat) {
    var a = r.args || {};
    if (TOOL_LABEL[r.tool]) return TOOL_LABEL[r.tool];
    if (r.tool === 'go_to') return 'Open ' + ((PLACES[String(a.where || '').toLowerCase()] || {}).label || a.where);
    if (r.tool === 'open_class') return 'Open ' + a.course;
    if (r.tool === 'open_section') return 'Open ' + a.course + ' section ' + a.section;
    if (r.tool === 'watch') return (a.off ? 'Stop watching ' : 'Watch ') + (a.course ? a.course + (a.section ? '-' + a.section : '') : a.name);
    if (r.tool === 'add_section') return 'Add ' + a.course + ' to my classes';
    if (r.tool === 'rate_professor') return 'Rate ' + (a.name || 'my ' + a.course + ' professor');
    if (r.tool === 'draft_message') return 'Message ' + a.friend;
    if (r.tool === 'share') return 'Send ' + (a.course || a.name) + (a.friend ? ' to ' + a.friend : '');
    if (r.tool === 'add_friend') return a.person ? 'Add ' + a.person + ' as a friend' : 'Add a friend';
    if (r.tool === 'friend_profile') return a.friend + '’s ' + (a.tab === 'took' ? 'past classes' : 'classes');
    if (r.tool === 'professor_stats') return a.name + '’s ratings';
    if (r.tool === 'compare_professors') return 'Compare ' + a.a + ' and ' + a.b;
    if (r.tool === 'set_theme') return 'Switch to ' + a.theme;
    if (r.tool === 'open_professor') return a.name;
    if (r.tool === 'prereqs') return 'Can I take ' + a.course + '?';
    if (r.tool === 'friends_in') return 'Friends in ' + a.course;
    if (r.tool === 'fit_pair') return 'Do ' + a.a + ' and ' + a.b + ' fit together?';
    if (r.tool === 'swap_section') return 'Other sections of ' + a.course;
    if (r.tool === 'search_sections') {
      if (a.scope === 'ge_unmet') return 'GE you still need' + (a.sort ? ', best-rated first' : '');
      if (a.scope === 'required') return 'Classes you still need' + (a.sort ? ', best-rated first' : '');
      try { return R.describe('search_sections', a, cat).replace(/^Showing: /, 'Sections: '); } catch (_) {}
    }
    return null;
  }

  function sameReading(x, y) {
    return !!x && !!y && x.tool === y.tool && JSON.stringify(x.args || {}) === JSON.stringify(y.args || {});
  }

  /* THE MISS LOG (2026-09-24). "Not it?" is the one moment a student says, in so many words, that
     Hawk was wrong — so that question, and what Hawk did with it, goes to assistant_log_miss
     (sql/professify-hawk-misses.sql). When they then pick a "Did you mean" reading, the pick goes
     too: the right answer, labelled by the person who asked. Pseudonym, never the account; signed
     out, nothing is sent. The events table still gets hawk_miss for counting — it just cannot say
     WHAT was missed, because events never store what anyone typed. */
  function smallArgs(a) {
    try { var j = JSON.stringify(a || {}); return j.length <= 600 ? JSON.parse(j) : null; } catch (_) { return null; }
  }
  /* One tap on "Not it?" and then a pick is ONE miss: the pick updates the row the tap wrote
     (review, 2026-09-24 — two rows double-counted the weekly review). */
  var lastMiss = { q: null, id: null };
  function logMiss(q, shown, picked) {
    try {
      if (!sb || typeof sb.rpc !== 'function' || !shown || !shown.tool || gpcOn()) return;
    } catch (_) { return; }
    var update = picked && lastMiss.q === q ? lastMiss.id : null;
    sessionToken().then(function (tok) {
      if (!tok) return null;                    // signed out: nothing leaves the browser
      return pseudonym();
    }).then(function (who) {
      if (!who) return;
      try {
        var p = sb.rpc('assistant_log_miss', {
          p_who: who, p_q: String(q).slice(0, 300),
          p_shown_tool: String(shown.tool), p_shown_args: smallArgs(shown.args),
          p_via: shown.viaModel ? 'model' : 'router',
          p_picked_tool: picked ? String(picked.tool) : null, p_picked_args: picked ? smallArgs(picked.args) : null,
          p_update_id: update
        });
        if (p && typeof p.then === 'function') {
          p.then(function (r) {
            var id = r && typeof r.data === 'number' ? r.data : (r && r.data && +r.data) || null;
            if (!picked) lastMiss = { q: q, id: id };
            else lastMiss = { q: null, id: null };
          }, function () {});
        }
      } catch (_) {}
    });
  }

  function showAlternatives(turn, q, shown, cat, quiet) {
    var alts = [];
    function add(r) {
      if (!r || !r.tool || r.tool === 'cant_answer') return;
      if (sameReading(r, shown) || alts.some(function (x) { return sameReading(x, r); })) return;
      if (!labelFor(r, cat)) return;
      alts.push(r);
    }
    var L = readings.local, M = readings.model;
    add(L && L.prerouted ? L : null);
    add(M);
    if (L && L.candidate && L.candidate.tool) add({ tool: L.candidate.tool, args: L.candidate.args });
    var t = String(q).toLowerCase();
    if (/\b(?:prof|profs|professors?|teachers?|instructors?)\b/.test(t) && /\b(?:my|mine|i have|i m|im)\b/.test(t)) add({ tool: 'my_professors', args: /\b(?:lowest|worst)\b/.test(t) ? { order: 'asc' } : {} });
    if (/\bfriends?\b/.test(t)) add({ tool: 'friends_took', args: /\bge\b/.test(t) ? { scope: 'ge_unmet' } : {} });
    if (/\b(?:free|busy|gap|break)\b/.test(t)) add({ tool: 'my_free', args: {} });
    if (/\b(?:need|left|require|requirement|graduate)\b/.test(t)) add({ tool: 'my_requirements', args: {} });
    if (/\b(?:ge|g\.e\.)\b/.test(t)) add({ tool: 'search_sections', args: { scope: 'ge_unmet', sort: 'rating' } });
    if (/\b(?:schedule|term|semester|units?)\b/.test(t) && /\b(?:build|make|plan)\b/.test(t)) add({ tool: 'build_term', args: {} });

    var box = make('div', 'hawk-alts');
    box.appendChild(make('div', 'hawk-alts__head', alts.length ? 'Did you mean' : (quiet ? 'Try a course code, a professor, or “open CSC labs after 6”.' : 'Sorry about that. Try it another way:')));
    alts.slice(0, 3).forEach(function (r) {
      box.appendChild(rowEl({
        code: '', name: labelFor(r, cat), chip: null,
        go: function () {
          try { if (has('track')) global.track('hawk_miss_fixed', null, 'hawk', { tool: String(r.tool) }); } catch (_) {}
          if (shown && shown.tool) logMiss(q, shown, r);
          readings = { local: null, model: null };
          render(q, { prerouted: true, confident: true, in_scope: true, tool: r.tool, args: r.args || {},
                      corrections: [], leftovers: [], signals: [] }, buildCatalog());
          return 'Here’s that instead';
        }
      }));
    });
    var again = make('button', 'hawk-alts__link', 'Say it another way');
    again.type = 'button';
    again.addEventListener('click', function () {
      try { els.input.value = q; els.input.focus(); els.input.select(); } catch (_) {}
    });
    var explore = make('button', 'hawk-alts__link', 'Search Explore');
    explore.type = 'button';
    explore.addEventListener('click', function () { searchInExplore(q); });
    var links = make('div', 'hawk-alts__links');
    links.appendChild(again); links.appendChild(explore);
    box.appendChild(links);
    if (!quiet) box.appendChild(make('div', 'hawk-alts__noted', 'Noted — this helps Hawk get better.'));
    turn.appendChild(box);
    try { box.scrollIntoView({ block: 'nearest' }); } catch (_) {}
  }

  function render(q, result, cat) {
    if (result.tool !== 'build_term') lastBuild = null;

    els.log.textContent = '';
    var turn = make('div', 'hawk-turn');

    var said = make('div', 'hawk-said');
    said.appendChild(make('span', 'hawk-said__q', q));
    (result.corrections || []).forEach(function (c) {
      said.appendChild(make('span', 'hawk-fix', c.typed + ' → ' + c.read));
    });
    /* Say when a question left the browser. The free tier answers on the device and this one does
       not, and which of the two happened is the student's business — it is the difference between
       a question nobody else ever saw and one that was sent somewhere. */
    if (result.viaModel) said.appendChild(make('span', 'hawk-fix hawk-fix--ai', 'AI'));
    turn.appendChild(said);

    if (result.refused) {
      turn.appendChild(make('div', 'hawk-note',
        'I only find classes, sections and professors at Cal Poly.'));
    } else if (!result.prerouted) {
      turn.appendChild(make('div', 'hawk-note', result.leftovers && result.leftovers.length
        ? 'I could not read “' + result.leftovers.join(', ') + '”.'
        : 'I am not sure what you mean.'));
      /* Same as "Not it?": the readings Hawk CAN act on, instead of a search box. */
      showAlternatives(turn, q, result, cat, true);
    } else if (result.tool === 'cant_answer') {
      /* The model said it cannot answer, and WHY it cannot is the useful part. One honest line per
         reason, each naming something Hawk genuinely can do instead — a bare "I don't know" sends
         the student away with nothing when three of the four reasons have an obvious next step. */
      var why = (result.args && result.args.reason) || 'ambiguous';
      if (why === 'needs_judgment') {
        turn.appendChild(make('div', 'hawk-note',
          'That one’s a judgement call, and it isn’t mine to make. I can show you the '
          + 'ratings and reviews.'));
      } else if (why === 'needs_private_data') {
        turn.appendChild(make('div', 'hawk-note',
          'I can’t see who’s in a class. Friends shows that, for people you’ve added.'));
      } else if (why === 'not_about_classes') {
        turn.appendChild(make('div', 'hawk-note',
          'I only find classes, sections and professors at Cal Poly.'));
      } else {
        /* MORE OPEN (Tate, 2026-09-23). A dead end with a search box helped nobody; offer the
           readings Hawk CAN act on, the same way "Not it?" does. */
        turn.appendChild(make('div', 'hawk-note', 'I’m not sure which you meant.'));
        showAlternatives(turn, q, result, cat, true);
        why = 'shown';
      }
      if (why !== 'not_about_classes' && why !== 'shown') {
        turn.appendChild(rowEl({
          code: '', name: 'Search Explore for “' + q + '”', chip: null,
          go: function () { return searchInExplore(q); }
        }));
      }
    } else if (renderTool(turn, result, cat, q)) {
      /* rendered above */
    } else {
      var out = rowsFor(result, cat);
      if (result.tool === 'search_sections' && (result.args.course || result.args.subject || result.args.ge_area)) {
        lastSearch = result.args;
      }
      if (out.needsAnchor) {
        turn.appendChild(make('div', 'hawk-note',
          'I read that, but I need a subject or a course to narrow it to — otherwise it’s '
          + 'the whole catalog. Explore can hold those filters.'));
        turn.appendChild(rowEl({
          code: '', name: 'Search Explore for “' + q + '”', chip: null,
          go: function () { return searchInExplore(q); }
        }));
      } else if (!out.rows.length) {
        turn.appendChild(make('div', 'hawk-note', out.none || 'Nothing in the catalog matches that.'));
      } else {
        out.rows.forEach(function (r) { turn.appendChild(rowEl(r)); });
      }
      /* Reading a filter and quietly dropping it is the failure this whole design exists to
         avoid, so whatever is left unacted-on is said out loud, under the rows, in one line. */
      if (out.unread.length) {
        var phrase = out.unread.length === 1 ? out.unread[0]
          : out.unread.slice(0, -1).join(', ') + ' or ' + out.unread[out.unread.length - 1];
        turn.appendChild(make('div', 'hawk-note', 'I cannot filter by ' + phrase + ' yet.'));
      }
    }

    /* "NOT IT?" on every answer that was an answer. Tapping it hands the student to the ordinary
       search with their words in it AND logs the miss with the question — which is the only signal
       that tells us Hawk was wrong rather than merely what it thought. Every router rule, golden
       set entry and new tool comes from reading these. Without it there is no loop. */
    if (!result.refused && result.tool && result.tool !== 'cant_answer') {
      var notIt = make('button', 'hawk-notit', 'Not it?');
      notIt.type = 'button';
      notIt.addEventListener('click', function () {
        try { if (has('track')) global.track('hawk_miss', null, 'hawk', { tool: String(result.tool), via: result.viaModel ? 'model' : 'router' }); } catch (_) {}
        logMiss(q, result, null);
        notIt.remove();
        showAlternatives(turn, q, result, cat);
      });
      turn.appendChild(notIt);
    }

    els.log.appendChild(turn);
    stamp();
    explainTurn(q, turn);
  }

  /* Seats carry the time they were read, once, at the bottom — not on every row. Hawk never states
     a seat count of its own; where it repeats the feed's, the feed's as-of goes with it. */
  function stamp() {
    var when = '';
    try {
      if (typeof SEATS_UPDATED_AT !== 'undefined' && SEATS_UPDATED_AT) {
        var d = new Date(SEATS_UPDATED_AT);
        if (!isNaN(d.getTime())) {
          when = 'Seats as of ' + d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        }
      }
    } catch (_) {}
    els.foot.textContent = when || privacyLine();
  }

  /* ---------------------------------------------------------------------------------------------
     The two answers that are about the student rather than the catalog.
     Both render a fact the device already knows, or say plainly that it does not know it.
     --------------------------------------------------------------------------------------------- */
  /* ===============================================================================================
     THE REST OF THE APP, AS ANSWERS.
     Each of these reads something the page already holds, or opens a screen the app already has.
     None of them can be wrong in a way the app itself is not already wrong, because they use the
     same functions: prereqStatus, completedCodes, classInfo, FRIENDS, secPitch, show.
     =============================================================================================== */

  function myCodes() {
    try { return (myClasses || []).slice(); } catch (_) { return []; }
  }

  /* -- go_to: one hop to any screen ------------------------------------------------------------- */
  /* EVERY SCREEN IN THE APP (2026-09-23). Each place is the app's own calls, in order — the same
     functions its own buttons use — so a place Hawk opens is exactly the screen a tap would. A
     function that is missing in some build is skipped, and the step before it still lands the
     student somewhere sensible. */
  function call(fn) {
    var rest = Array.prototype.slice.call(arguments, 1);
    return function () { try { if (has(fn)) global[fn].apply(global, rest); } catch (_) {} };
  }
  var PLACES = {
    'home':               { label: 'Home',                  run: [call('show', 'home')] },
    'explore':            { label: 'Explore',               run: [call('show', 'explore'), call('setExMode', 'classes')] },
    'explore professors': { label: 'Explore · Professors',  run: [call('show', 'explore'), call('setExMode', 'professors')] },
    'ge browser':         { label: 'Explore · GE areas',    run: [call('show', 'explore'), call('setExMode', 'classes')] },
    'find professor':     { label: 'Find a professor',      run: [call('openFindProf')] },
    'schedule':           { label: 'Schedule',              run: [call('show', 'sched')] },
    'my classes':         { label: 'My classes',            run: [call('show', 'sched'), call('setSchedTab', 'mine')] },
    'week view':          { label: 'My classes · Week',     run: [call('show', 'sched'), call('setSchedTab', 'mine'), call('setMyClassesView', 'calendar')] },
    /* The watchlist became Plans on 2026-09-25; watched professors live in Explore › Professors › Saved. */
    'watchlist':          { label: 'Plans',                 run: [call('show', 'sched'), call('setSchedTab', 'watch')] },
    'watch list':         { label: 'Plans',                 run: [call('show', 'sched'), call('setSchedTab', 'watch')] },
    'watched professors': { label: 'Saved professors',      run: [call('show', 'explore'), call('setExMode', 'professors'), call('exSetSaved', true)] },
    'compare professors': { label: 'Compare professors',    run: [call('goCompare')] },
    'planner':            { label: 'Planner',               run: [call('show', 'sched'), call('setSchedTab', 'plan')] },
    'ledger':             { label: 'Requirements ledger',   run: [call('show', 'sched'), call('setSchedTab', 'plan'), call('plansOpenDegree')] },
    'past classes':       { label: 'Past classes',          run: [call('show', 'sched'), call('setSchedTab', 'past')] },
    'add past class':     { label: 'Add a past class',      run: [call('show', 'sched'), call('setSchedTab', 'past'), call('addPastClass')] },
    'add past term':      { label: 'Add a past term',       run: [call('show', 'sched'), call('setSchedTab', 'past'), call('openTermImport')] },
    'import schedule':    { label: 'Import your schedule',  run: [call('show', 'sched'), call('openSchedImport')] },
    'share my schedule':  { label: 'Share my schedule',     run: [call('shareMySchedule')] },
    'friends':            { label: 'Friends',               run: [call('show', 'friends'), call('gpSetTab', 'friends')] },
    'groups':             { label: 'Groups',                run: [call('show', 'friends'), call('frOpenGroups')] },
    'messages':           { label: 'Messages',              run: [call('show', 'friends')] },
    'new message':        { label: 'New message',           run: [call('show', 'friends'), call('msgNewConv')] },
    'add friend':         { label: 'Add a friend',          run: [call('show', 'friends'), call('gpSetTab', 'friends'), call('openAddFriend')] },
    'my qr code':         { label: 'My QR code',            run: [call('show', 'friends'), call('showMyQR')] },
    'invite link':        { label: 'Invite a friend',       run: [call('show', 'friends'), call('gpSetTab', 'friends'), call('openAddFriend')] },
    'settings':           { label: 'Settings',              run: [call('openSettings')] },
    'appearance':         { label: 'Settings · Appearance', run: [call('openSettings', 'appearance')] },
    'account':            { label: 'Settings · Account',    run: [call('openSettings', 'account')] },
    'privacy settings':   { label: 'Settings · Privacy',    run: [call('openSettings', 'privacy')] },
    'about':              { label: 'Settings · About',      run: [call('openSettings', 'about')] },
    'edit profile':       { label: 'Edit profile',          run: [call('openEditProfile')] },
    'notifications':      { label: 'Notifications',         run: [call('openNotifs')] },
    'rate':               { label: 'Rate a professor',      run: [call('openRate')] },
    'my reviews':         { label: 'Your reviews',          run: [call('openMyReviews')] },
    'reviews':            { label: 'Your reviews',          run: [call('openMyReviews')] },
    'privacy policy':     { label: 'Privacy policy',        run: [call('openLegal', 'privacy')] },
    'terms':              { label: 'Terms',                 run: [call('openLegal', 'terms')] },
    'community guidelines': { label: 'Community guidelines', run: [call('openLegal', 'guidelines')] },
    'security':           { label: 'Security',              run: [call('openLegal', 'security')] }
  };
  var PLACE_KEYS = Object.keys(PLACES);

  function goPlace(key) {
    var p = PLACES[String(key || '').toLowerCase()];
    if (!p) return 'Could not find that screen';
    p.run.forEach(function (step) { step(); });
    return 'Opened ' + p.label;
  }

  function renderGoTo(turn, result) {
    var key = String((result.args && result.args.where) || '').toLowerCase();
    var p = PLACES[key];
    if (!p) {
      turn.appendChild(make('div', 'hawk-note', 'I don’t know a screen called “' + key + '”.'));
      return;
    }
    turn.appendChild(rowEl({ code: '', name: p.label, chip: null, go: function () { return goPlace(key); } }));
  }

  /* ===============================================================================================
     ACTIONS (2026-09-23). Tate's two rules, and every function below keeps them:
       1. Hawk opens it READY TO GO and the student makes the final tap — the rate form for that
          professor, the enroll dialog for that section, the chat with the question typed in.
          Only small, undoable things happen by themselves (watching, the theme), with an Undo.
       2. Nothing is ever SENT to another person. Messages are drafts; shares open the sheet.
     Every step is the app's own function, the one its own button calls.
     =============================================================================================== */
  function profIdByName(name) {
    var n = String(name || '').trim();
    if (!n) return null;
    try { if (has('matchProfId')) { var id = global.matchProfId(n); if (id) return id; } } catch (_) {}
    try {
      var low = n.toLowerCase(), ids = Object.keys(PROFESSORS || {});
      for (var i = 0; i < ids.length; i += 1) {
        if (String((PROFESSORS[ids[i]] || {}).name || '').toLowerCase() === low) return ids[i];
      }
    } catch (_) {}
    return null;
  }

  function friendByName(name) {
    var low = String(name || '').toLowerCase().trim();
    if (!low) return null;
    var list = [];
    try { list = FRIENDS || []; } catch (_) { list = []; }
    var exact = list.filter(function (f) { return String(f.name || '').toLowerCase() === low; });
    if (exact.length) return exact[0];
    var first = list.filter(function (f) { return String(f.name || '').toLowerCase().split(/\s+/)[0] === low.split(/\s+/)[0]; });
    return first.length === 1 ? first[0] : null;
  }

  function sectionRow(code, num) {
    var want = parseInt(num, 10);
    return sectionsOf(code).filter(function (r) { return parseInt(secNumber(r), 10) === want; })[0] || null;
  }

  function notFound(turn, what) {
    turn.appendChild(make('div', 'hawk-note', what));
  }

  /* A done-for-you change, said plainly, with a way back. */
  function undoNote(turn, text, undo) {
    var d = make('div', 'hawk-note hawk-note--good hawk-done');
    d.appendChild(make('span', null, text + ' '));
    var b = make('button', 'hawk-alts__link', 'Undo');
    b.type = 'button';
    b.addEventListener('click', function () {
      try { undo(); } catch (_) {}
      d.textContent = 'Undone.';
      d.className = 'hawk-note hawk-done';
    });
    d.appendChild(b);
    turn.appendChild(d);
  }

  /* -- help ------------------------------------------------------------------------------------ */
  var HELP = [
    ['Build me a 15 unit schedule, no Fridays', 'Plan a whole term'],
    ['A GE I still need with the best professors', 'Recommendations that fit you'],
    ['When am I free on Tuesday?', 'Your week, clashes and units'],
    ['Which of my professors is highest rated?', 'Your professors, ranked'],
    ['Classes my friends have taken', 'What your friends took and are in'],
    ['Watch BUS 4442', 'Seat alerts, watchlist, rating, sharing'],
    ['How do I change my profile picture?', 'Any screen in TermChamp']
  ];
  function renderHelp(turn) {
    turn.appendChild(make('div', 'hawk-note',
      'I find classes and professors, plan your term, answer about your week and your friends, '
      + 'and open anything in TermChamp. Try:'));
    HELP.forEach(function (h) {
      turn.appendChild(rowEl({ code: '', name: h[0], sub: h[1], chip: null,
        go: function () { try { els.input.value = h[0]; } catch (_) {} answer(h[0]); return 'Asked'; } }));
    });
  }

  /* -- set_theme ------------------------------------------------------------------------------- */
  function renderTheme(turn, result) {
    var t = String((result.args || {}).theme || '');
    if (['dark', 'light', 'cream'].indexOf(t) < 0 || !has('setTheme')) { notFound(turn, 'I can switch between dark, light and cream.'); return; }
    var prev = document.documentElement.getAttribute('data-theme') || 'dark';
    if (prev === t) { turn.appendChild(make('div', 'hawk-note', 'You’re already on ' + t + '.')); return; }
    global.setTheme(t);
    undoNote(turn, 'Switched to ' + t + '.', function () { global.setTheme(prev); });
  }

  /* -- watch / unwatch ------------------------------------------------------------------------- */
  function renderWatch(turn, result, cat) {
    var a = result.args || {}, off = !!a.off;
    var kind = a.kind || (a.name ? 'professor' : (a.section ? 'section' : 'class'));
    var is, flip, label;
    if (kind === 'professor') {
      var id = profIdByName(a.name);
      if (!id || !has('toggleWatch')) { notFound(turn, 'I couldn’t find a professor called “' + (a.name || '') + '”.'); return; }
      label = (PROFESSORS[id] || {}).name || a.name;
      is = function () { try { return has('isWatched') ? !!global.isWatched(id) : false; } catch (_) { return false; } };
      flip = function () { global.toggleWatch(id); };
    } else if (kind === 'section') {
      var row = sectionRow(a.course, a.section);
      if (!row || !has('wcWatchSec')) { notFound(turn, 'I couldn’t find section ' + a.section + ' of ' + a.course + ' this term.'); return; }
      var crn = String(row.class_nbr || row.crn);
      label = a.course + '-' + secNumber(row);
      is = function () { try { return has('isWatchedSec') ? !!global.isWatchedSec(a.course, crn) : false; } catch (_) { return false; } };
      flip = function () { global.wcWatchSec(a.course, crn, null, true); };
    } else {
      if (!a.course || !has('toggleWatchClass')) { notFound(turn, 'Which class? Try “watch BUS 4442”.'); return; }
      label = a.course;
      is = function () { try { return has('isWatchedClass') ? !!global.isWatchedClass(a.course) : false; } catch (_) { return false; } };
      flip = function () { global.toggleWatchClass(a.course); };
    }
    if (is() === !off) {
      turn.appendChild(make('div', 'hawk-note', off ? 'You weren’t watching ' + label + '.' : 'You’re already watching ' + label + '.'));
    } else {
      flip();
      undoNote(turn, (off ? 'Stopped watching ' : 'Watching ') + label + '.', flip);
    }
    turn.appendChild(rowEl({ code: '', name: kind === 'professor' ? 'Open saved professors' : 'Open Plans', chip: null,
      go: function () { return goPlace(kind === 'professor' ? 'watched professors' : 'watchlist'); } }));
  }

  /* -- open_section ---------------------------------------------------------------------------- */
  function renderOpenSection(turn, result, cat) {
    var a = result.args || {};
    var row = sectionRow(a.course, a.section);
    if (!row) {
      notFound(turn, 'There’s no section ' + a.section + ' of ' + a.course + ' this term.');
      turn.appendChild(rowEl({ code: a.course, name: cat.courses[a.course] || a.course, chip: courseChip(a.course), go: function () { return goClass(a.course); } }));
      return;
    }
    var label = a.course + '-' + secNumber(row), crn = row.class_nbr || row.crn, p = profOf(row);
    turn.appendChild(rowEl({ rich: true, code: label, name: cat.courses[a.course] || a.course,
      sub: [meetLabel(row), p ? p.name : null].filter(Boolean).join(' · '),
      chip2: p ? ratingChip(p.rating) : null,
      chip: isMine(a.course, row) ? { text: 'yours', tone: 'open' } : seatChip(row),
      go: function () { return goSection(a.course, crn, label); } }));
  }

  /* -- add_section: the app's own enroll dialog, for the student to confirm ------------------------ */
  function renderAddSection(turn, result, cat) {
    var a = result.args || {};
    if (!has('mcEnrollSec')) { notFound(turn, 'Adding classes isn’t available in this build.'); return; }
    var mine = mySchedule();
    function addRow(row) {
      var label = a.course + '-' + secNumber(row), crn = String(row.class_nbr || row.crn), p = profOf(row);
      var clash = row && meetOf(row) ? clashesWith(meetOf(row), mine, a.course) : [];
      return rowEl({ rich: true, code: label, name: 'Add ' + label,
        sub: [meetLabel(row), p ? p.name : null].filter(Boolean).join(' · '),
        chip2: p ? ratingChip(p.rating) : null, chip: seatChip(row),
        clash: clash.length ? clash : null,
        go: function () { global.mcEnrollSec(a.course, crn); return 'Confirm it in the box that opened'; } });
    }
    if (a.section) {
      var row = sectionRow(a.course, a.section);
      if (!row) { notFound(turn, 'There’s no section ' + a.section + ' of ' + a.course + ' this term.'); return; }
      turn.appendChild(make('div', 'hawk-note', 'Tap to add it — you’ll confirm enrolled or waitlisted before anything saves.'));
      turn.appendChild(addRow(row));
      return;
    }
    var rows = sectionsOf(a.course);
    if (!rows.length) { notFound(turn, a.course + ' isn’t offered this term.'); return; }
    turn.appendChild(make('div', 'hawk-note', 'Which section? You’ll confirm before anything saves.'));
    rows.slice().sort(function (x, y) {
      var cx = meetOf(x) ? clashesWith(meetOf(x), mine, a.course).length : 0, cy = meetOf(y) ? clashesWith(meetOf(y), mine, a.course).length : 0;
      return (cx - cy) || (seatsOf(y) - seatsOf(x));
    }).slice(0, 5).forEach(function (r) { turn.appendChild(addRow(r)); });
  }

  /* -- rate_professor: the rate form, prefilled --------------------------------------------------- */
  function renderRate(turn, result, cat) {
    var a = result.args || {};
    var id = a.name ? profIdByName(a.name) : null;
    if (!id && a.course) {
      /* "rate my STAT 2170 professor" — the one on the student's own section. */
      var meta = null;
      try { meta = (myClassMeta || {})[a.course]; } catch (_) {}
      var raw = meta && ((Array.isArray(meta.secs) && meta.secs[0] && meta.secs[0].prof) || meta.prof);
      if (raw) { var p = profOf({ instructor: raw }); id = p && p.id; }
      if (!id) {
        var seen = {};
        var teachers = sectionsOf(a.course).map(profOf).filter(function (x) { if (!x || !x.id || seen[x.id]) return false; seen[x.id] = 1; return true; });
        if (!teachers.length) { notFound(turn, 'I don’t know who teaches ' + a.course + '.'); turn.appendChild(rowEl({ code: '', name: 'Open Rate', chip: null, go: function () { return goPlace('rate'); } })); return; }
        turn.appendChild(make('div', 'hawk-note', 'Who did you have for ' + a.course + '?'));
        teachers.slice(0, 5).forEach(function (t) {
          turn.appendChild(rowEl({ code: '', name: 'Rate ' + t.name, chip: t.rating != null ? ratingChip(t.rating) : null,
            go: function () { global.startRate(t.id, a.course); return 'The form is open — you submit it'; } }));
        });
        return;
      }
    }
    if (!id || !has('startRate')) { notFound(turn, 'I couldn’t find “' + (a.name || a.course || '') + '”.'); turn.appendChild(rowEl({ code: '', name: 'Open Rate', chip: null, go: function () { return goPlace('rate'); } })); return; }
    var name = (PROFESSORS[id] || {}).name || a.name;
    turn.appendChild(rowEl({ code: '', name: 'Rate ' + name + (a.course ? ' for ' + a.course : ''), chip: null,
      go: function () { global.startRate(id, a.course || ''); return 'The form is open — you submit it'; } }));
  }

  /* -- draft_message: a chat with the words typed in, never sent ----------------------------------- */
  function renderDraft(turn, result, cat) {
    var a = result.args || {};
    var f = friendByName(a.friend);
    if (!f) { notFound(turn, 'I couldn’t find a friend called “' + (a.friend || '') + '”.'); turn.appendChild(rowEl({ code: '', name: 'Open Friends', chip: null, go: function () { return goPlace('friends'); } })); return; }
    var first = String(f.name).split(' ')[0];
    var took = a.course && (f.history || []).some(function (h) { return h && h.code === a.course; });
    var inIt = a.course && (f.classes || []).indexOf(a.course) >= 0;
    var text = '';
    if (a.course && inIt) text = 'hey! you’re in ' + a.course + ' right? how is it so far?';
    else if (a.course && !took) text = 'hey! thinking about taking ' + a.course + ' — have you heard anything about it?';
    else if (a.name) text = 'hey! have you had ' + a.name + '? thinking about taking them.';
    turn.appendChild(rowEl({ code: '', name: 'Message ' + first, sub: took ? 'asks how ' + a.course + ' was' : (text || 'opens your chat'), chip: null,
      go: function () {
        if (took && has('askFriendAbout')) { global.askFriendAbout(f.id, a.course); return 'Draft is in your chat with ' + first + ' — you press Send'; }
        if (!has('msgWith')) return goPlace('messages');
        Promise.resolve(global.msgWith(f.id)).then(function () {
          if (!text) return;
          var box = document.getElementById('msgInput');
          if (box) { box.value = text; try { box.dispatchEvent(new Event('input', { bubbles: true })); box.focus(); } catch (_) {} }
        });
        return text ? 'Draft is in your chat with ' + first + ' — you press Send' : 'Opened your chat with ' + first;
      } }));
  }

  /* -- share: the app's share sheet; the student picks who ----------------------------------------- */
  function renderShare(turn, result, cat) {
    var a = result.args || {};
    if (!has('shOpen')) { notFound(turn, 'Sharing isn’t available in this build.'); return; }
    var kind = a.course ? 'class' : 'prof', key = a.course || profIdByName(a.name);
    if (!key) { notFound(turn, 'I couldn’t find “' + (a.name || '') + '”.'); return; }
    var what = a.course || (PROFESSORS[key] || {}).name || a.name;
    var who = a.friend ? friendByName(a.friend) : null;
    turn.appendChild(rowEl({ code: '', name: 'Send ' + what + (who ? ' to ' + String(who.name).split(' ')[0] : ''), chip: null,
      sub: 'opens the share sheet — you pick who and send',
      go: function () { global.shOpen(kind, key); return who ? 'Pick ' + String(who.name).split(' ')[0] + ' in the list to send it' : 'Pick who to send it to'; } }));
  }

  /* -- add_friend: the people search, with the name typed in -------------------------------------- */
  function renderAddFriend(turn, result) {
    var person = String((result.args || {}).person || '').trim();
    turn.appendChild(rowEl({ code: '', name: person ? 'Find ' + person : 'Add a friend', sub: 'you send the request', chip: null,
      go: function () {
        goPlace('add friend');
        if (person) {
          setTimeout(function () {
            var el = document.getElementById('frSearchPeople');
            if (el) { el.value = person; try { el.dispatchEvent(new Event('input', { bubbles: true })); } catch (_) {} }
          }, 60);
        }
        return person ? 'Searching for ' + person : 'Opened Add a friend';
      } }));
  }

  /* -- friend_profile ------------------------------------------------------------------------------ */
  function renderFriendProfile(turn, result) {
    var a = result.args || {};
    var f = friendByName(a.friend);
    if (!f || !has('openFriendProfile')) { notFound(turn, 'I couldn’t find a friend called “' + (a.friend || '') + '”.'); return; }
    var tab = ['classes', 'took', 'friends'].indexOf(a.tab) >= 0 ? a.tab : 'classes';
    var first = String(f.name).split(' ')[0];
    if (tab === 'classes' && (f.classes || []).length) {
      turn.appendChild(make('div', 'hawk-note', first + ' is taking ' + f.classes.slice(0, 6).join(', ') + (f.classes.length > 6 ? '…' : '') + '.'));
    }
    if (tab === 'took' && (f.history || []).length) {
      turn.appendChild(make('div', 'hawk-note', first + ' has taken ' + f.history.slice(0, 6).map(function (h) { return h.code; }).join(', ') + (f.history.length > 6 ? '…' : '') + '.'));
    }
    turn.appendChild(rowEl({ code: '', name: 'Open ' + first + '’s ' + ({ classes: 'classes', took: 'past classes', friends: 'friends' }[tab]), chip: null,
      go: function () { global.openFriendProfile(f.id, tab); return 'Opened ' + first; } }));
  }

  /* -- professor_stats / compare_professors ------------------------------------------------------
     Only what TermChamp holds in memory: the blended rating (out of 5, as every screen shows it),
     how many ratings, the department. Would-take-again, hours and difficulty come from reviews the
     professor page loads — so Hawk says so and opens it, rather than guessing a number. */
  function profCard(id) {
    var p = PROFESSORS[id] || {};
    var r = typeof p.rating === 'number' && p.rating > 0 ? five(p.rating) : null;
    return { id: id, name: p.name || 'Professor', rating: r, evals: p.evals || 0, dept: p.dept || p.field || '' };
  }
  function renderProfStats(turn, result) {
    var id = profIdByName((result.args || {}).name);
    if (!id) { notFound(turn, 'I couldn’t find “' + ((result.args || {}).name || '') + '”.'); return; }
    var c = profCard(id);
    turn.appendChild(make('div', 'hawk-note', c.rating != null
      ? c.name + ': ' + c.rating.toFixed(1) + ' ★ from ' + c.evals + (c.evals === 1 ? ' rating' : ' ratings') + (c.dept ? ' · ' + c.dept : '') + '.'
      : c.name + ' has no ratings yet.'));
    turn.appendChild(make('div', 'hawk-note', 'Would take again, hours a week and difficulty are on their page, from the reviews.'));
    turn.appendChild(rowEl({ code: '', name: 'Open ' + c.name, chip: c.rating != null ? ratingChip(c.rating) : null,
      go: function () { return goProfessor(c.name); } }));
  }
  function renderCompare(turn, result) {
    var a = result.args || {};
    var ids = [profIdByName(a.a), profIdByName(a.b)];
    if (!ids[0] || !ids[1]) { notFound(turn, 'I couldn’t find both of those professors.'); return; }
    var cs = ids.map(profCard);
    var both = cs[0].rating != null && cs[1].rating != null;
    if (both && cs[0].rating !== cs[1].rating) {
      var hi = cs[0].rating > cs[1].rating ? cs[0] : cs[1];
      turn.appendChild(make('div', 'hawk-note hawk-note--good', hi.name + ' is rated higher.'));
    }
    cs.forEach(function (c) {
      turn.appendChild(rowEl({ code: '', name: c.name, sub: (c.evals ? c.evals + ' ratings' : 'no ratings yet') + (c.dept ? ' · ' + c.dept : ''),
        chip: c.rating != null ? ratingChip(c.rating) : { text: 'no ratings', tone: 'wait' },
        go: function () { return goProfessor(c.name); } }));
    });
    if (has('goCompare') && has('isWatched')) {
      var watched = ids.every(function (id) { try { return !!global.isWatched(id); } catch (_) { return false; } });
      if (watched) turn.appendChild(rowEl({ code: '', name: 'Compare side by side', chip: null, go: function () { global.goCompare(ids); return 'Opened Compare'; } }));
    }
  }

  /* -- prereqs: can I take X ------------------------------------------------------------------- */
  function renderPrereqs(turn, result, cat) {
    var code = result.args.course;
    var st = null;
    try {
      if (has('prereqStatus')) {
        var done = has('completedCodes') ? global.completedCodes() : [];
        var now = has('enrolledNowCodes') ? global.enrolledNowCodes() : myCodes();
        st = global.prereqStatus(code, done, [], now);
      }
    } catch (_) { st = null; }

    if (!st) {
      turn.appendChild(make('div', 'hawk-note', 'I can’t read prerequisites in this build.'));
    } else if (st.state === 'none') {
      turn.appendChild(make('div', 'hawk-note', code + ' has no prerequisites listed.'));
    } else {
      var missing = st.missing || [], inProg = st.inProgress || [], conc = st.concurrent || [];
      if (!missing.length && !inProg.length) {
        turn.appendChild(make('div', 'hawk-note hawk-note--good', 'You’ve met the prerequisites for ' + code + '.'));
      } else {
        if (missing.length) {
          turn.appendChild(make('div', 'hawk-note', 'Still need: ' + missing.map(groupLabel).join('; ')));
        }
        if (inProg.length) {
          turn.appendChild(make('div', 'hawk-note', 'In progress now: ' + inProg.map(groupLabel).join('; ')
            + ' — counts once it’s done.'));
        }
      }
      if (conc.length) {
        turn.appendChild(make('div', 'hawk-note', 'Can be taken at the same time: ' + conc.map(groupLabel).join(', ')));
      }
      turn.appendChild(make('div', 'hawk-note', 'Based on the classes you’ve logged. Cal Poly’s degree audit is the final word.'));
    }
    turn.appendChild(rowEl({ code: code, name: cat.courses[code] || code, chip: courseChip(code),
                             go: function () { return goClass(code); } }));
  }

  /* A prerequisite group is "one of these". Rendered as such rather than flattened. */
  function groupLabel(g) {
    if (Array.isArray(g)) return g.length > 1 ? 'one of ' + g.join(' / ') : String(g[0] || '');
    return String(g || '');
  }

  /* -- my_day: what do I have on <day> ---------------------------------------------------------- */
  function dayFor(rel) {
    var d = new Date();
    if (rel === 'tomorrow') d.setDate(d.getDate() + 1);
    return DAY_ORDER[(d.getDay() + 6) % 7];   // JS Sunday=0 → our Mo=0
  }

  function renderMyDay(turn, result) {
    var mine = mySchedule();
    if (!mine || mine.empty) { renderNoClasses(turn); return; }
    var a = result.args || {};
    var days = a.rel ? [dayFor(a.rel)] : (a.days && a.days.length ? a.days : [dayFor('today')]);
    var label = a.rel === 'tomorrow' ? 'Tomorrow' : (a.rel === 'today' ? 'Today' : null);

    days.forEach(function (day) {
      var f = freeOn(day, mine);
      var head = (label || DAY_FULL[day]) + (label ? ' (' + DAY_FULL[day] + ')' : '');
      if (f.wholeDay) {
        turn.appendChild(make('div', 'hawk-note', head + ' — nothing scheduled.'));
        return;
      }
      turn.appendChild(make('div', 'hawk-note', head + ' — ' + f.classes.length
        + (f.classes.length === 1 ? ' class' : ' classes') + ', ' + clock12(f.classes[0].start)
        + ' to ' + clock12(f.classes[f.classes.length - 1].end)));
      f.classes.forEach(function (c) {
        turn.appendChild(rowEl({
          code: c.code, name: clock12(c.start) + '–' + clock12(c.end), chip: null,
          go: function () { return goClass(c.code); }
        }));
      });
    });
    noteUnplaced(turn, mine);
  }

  /* -- my_units ------------------------------------------------------------------------------- */
  function renderMyUnits(turn) {
    var codes = myCodes();
    if (!codes.length) { renderNoClasses(turn); return; }
    var total = 0, unknown = [];
    codes.forEach(function (c) {
      var u = null;
      try { u = has('classInfo') ? Number(global.classInfo(c).units) : null; } catch (_) {}
      if (u != null && !isNaN(u) && u > 0) total += u; else unknown.push(c);
    });
    turn.appendChild(make('div', 'hawk-note',
      total + ' units across ' + codes.length + (codes.length === 1 ? ' class' : ' classes') + '.'));
    if (unknown.length) {
      turn.appendChild(make('div', 'hawk-note', 'Not counted — no unit count on ' + unknown.join(', ') + '.'));
    }
  }

  /* -- my_requirements ------------------------------------------------------------------------ */
  /* exStillNeed() returns { state, items, open, left, coded } — an OBJECT. The first version read
     it as an array, found none, and for every student ever said "the full picture is in your
     ledger" and nothing else. Read the shape it actually has. */
  function renderMyRequirements(turn) {
    var r = null;
    try { if (has('exStillNeed')) r = global.exStillNeed(); } catch (_) { r = null; }
    var st = r && r.state;
    if (st === 'nomajor') {
      turn.appendChild(make('div', 'hawk-note', 'Set your major first, and I\u2019ll know what you still need.'));
      turn.appendChild(rowEl({ code: '', name: 'Open Settings', chip: null, go: function () { return goPlace('settings'); } }));
      return;
    }
    if (st === 'norecord') {
      turn.appendChild(make('div', 'hawk-note', 'Log your past classes and I can tell what\u2019s left.'));
      turn.appendChild(rowEl({ code: '', name: 'Open Past classes', chip: null, go: function () { return goPlace('past classes'); } }));
      return;
    }
    if (st === 'ok') {
      turn.appendChild(make('div', 'hawk-note', r.left + (r.left === 1 ? ' requirement' : ' requirements') + ' left.'));
      (r.items || []).slice(0, 4).forEach(function (it) {
        var c = it.code;
        turn.appendChild(rowEl({ code: c, name: (buildCatalog().courses[c] || c), sub: it.group === 'major' ? 'Major' : String(it.group || ''),
                                 chip: courseChip(c), go: function () { return goClass(c); } }));
      });
      (r.open || []).slice(0, 3).forEach(function (o) {
        var k = geKeyOfTitle(o.title);
        turn.appendChild(rowEl({ code: k ? 'GE ' + k : '', name: String(o.title || '').replace(/^GE\s*\u00b7\s*/, ''),
                                 sub: o.n ? o.n + ' classes count toward it' : null, chip: null,
                                 go: function () { return k ? goGeArea(k) : goPlace('ledger'); } }));
      });
      turn.appendChild(make('div', 'hawk-note', 'Try \u201ca GE I still need that fits my schedule\u201d.'));
      return;
    }
    turn.appendChild(make('div', 'hawk-note', 'The full picture is in your requirements ledger.'));
    turn.appendChild(rowEl({ code: '', name: 'Open my ledger', chip: null, go: function () { return goPlace('ledger'); } }));
  }

  /* -- game_plan (2026-09-25) --------------------------------------------------------------------
     "What do I register for first?" — read from the student's own Plans A–C on the device, through
     plans.js, which orders them by what they would lose most and finds a backup for each. Hawk
     repeats that order and adds nothing: no reason here that the full game plan does not show. */
  function renderGamePlan(turn, result) {
    var P = global.TCPlans;
    if (!P) { turn.appendChild(make('div', 'hawk-note', 'Plans aren’t in this build yet.')); return; }
    var a = result.args || {};
    var full = P.slots.filter(function (s) { return P.get(s).sections.length; });
    if (!full.length) {
      turn.appendChild(make('div', 'hawk-note', 'You don’t have a plan yet. Build a term, save it as Plan A, and I’ll put it in the order to register.'));
      turn.appendChild(rowEl({ code: '', name: 'Build a term', chip: null, go: function () {
        render('build me a 15 unit schedule', { prerouted: true, confident: true, in_scope: true, tool: 'build_term', args: { units: 15 }, corrections: [], leftovers: [], signals: [] }, buildCatalog()); return 'Building a term';
      } }));
      turn.appendChild(rowEl({ code: '', name: 'Open Plans', chip: null, go: function () { return goPlace('watchlist'); } }));
      return;
    }
    var want = a.plan && full.indexOf(a.plan) >= 0 ? a.plan : null;
    var slot = want || (full.indexOf(P.cur()) >= 0 ? P.cur() : full[0]);
    if (a.plan && !want) turn.appendChild(make('div', 'hawk-note', 'Plan ' + a.plan + ' is empty, so here’s Plan ' + slot + '.'));
    var read = make('div', 'hawk-read', '');
    turn.appendChild(read);
    var pills = make('div', 'hawk-opts');
    var body = make('div', 'hawk-build__body');
    function show(sl) {
      var g = P.gamePlan(sl);
      read.textContent = 'game plan · Plan ' + sl + (g.preview ? ' · preview on ' + g.termLabel + ' sections' : '');
      Array.prototype.forEach.call(pills.children, function (b) { var on = b.getAttribute('data-slot') === sl; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
      body.textContent = '';
      g.steps.slice(0, 4).forEach(function (st, ix) {
        var i = st.i, bk = st.backup;
        var bkText = bk && bk.best ? ('Backup -' + bk.best.no + ' · ' + [bk.best.when, bk.best.prof].filter(Boolean).join(' · ') + (bk.needsLab ? ' · pick a lab too' : ''))
          : 'No backup fits — waitlist if it fills';
        body.appendChild(rowEl({
          rich: true, code: (ix + 1) + '. ' + i.label,
          name: st.reasons.length ? st.reasons[0].t : (nameOf(i.code) || i.code),
          sub: bkText + (g.inRound1 && st.round === 2 ? ' · Round 2' : ''),
          chip: st.seatLine ? { text: st.seatLine, tone: st.reasons[0] && st.reasons[0].hot ? 'wait' : 'open' } : null,
          go: function () { return goSection(i.code, i.crn, i.label); }
        }));
      });
      if (g.steps.length > 4) body.appendChild(make('div', 'hawk-count', (g.steps.length - 4) + ' more, lower risk'));
      body.appendChild(rowEl({ code: '', name: 'Open the full game plan', chip: null, go: function () { P.openGamePlan(sl); return 'Opened the game plan'; } }));
      if (g.inRound1 && g.split && g.unitsKnown) body.appendChild(make('div', 'hawk-count', 'Round 1 caps you at 16 units — the rest waits for Round 2.'));
    }
    full.forEach(function (s) {
      var q = P.planInfo(s);
      var b = make('button', 'hawk-opt');
      b.type = 'button'; b.setAttribute('data-slot', s);
      b.appendChild(make('span', 'hawk-opt__name', 'Plan ' + s));
      b.appendChild(make('span', 'hawk-opt__meta', q.units + (q.unitsKnown ? '' : '+') + 'u'));
      b.addEventListener('click', function () { show(s); });
      pills.appendChild(b);
    });
    if (full.length > 1) turn.appendChild(pills);
    turn.appendChild(body);
    show(slot);
  }
  function nameOf(code) {
    try { var cat = buildCatalog(); return cat.courses[code] && cat.courses[code] !== code ? cat.courses[code] : ''; } catch (_) { return ''; }
  }

  /* -- when_registration ---------------------------------------------------------------------- */
  /* Dates from PROFESSIFY_CONFIG, which quotes the registrar (registrar.calpoly.edu/spring-semester-
     planning-calendar, read 2026-09-24). Cal Poly calls it "Round 1 Registration … for registration
     appointment rotations" — it opens by appointment, so Hawk never says "you can register on the
     19th", only when the round opens and where the student's own time is. */
  function regDate(v) {
    var d = new Date(String(v || '') + 'T12:00:00');
    return isNaN(d.getTime()) ? null : d;
  }
  function niceDate(d) { return d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }); }
  function renderRegistration(turn) {
    var c = {};
    try { c = global.PROFESSIFY_CONFIG || {}; } catch (_) {}
    var r1 = regDate(c.REGISTRATION_OPENS), r2 = regDate(c.REGISTRATION_ROUND2), oe = regDate(c.OPEN_ENROLLMENT);
    var term = c.REGISTRATION_TERM || '';
    if (!r1) {
      turn.appendChild(make('div', 'hawk-note',
        'I don’t have the registration date in this build yet. Cal Poly’s Portal shows your appointment time.'));
      return;
    }
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var steps = [['Round 1', r1], ['Round 2', r2], ['Open Enrollment', oe]].filter(function (x) { return x[1]; });
    var next = steps.filter(function (x) { return x[1] >= today; })[0];
    var isToday = next && next[1].getFullYear() === today.getFullYear() && next[1].getMonth() === today.getMonth() && next[1].getDate() === today.getDate();
    if (next) {
      turn.appendChild(make('div', 'hawk-note hawk-note--good',
        next[0] + ' registration' + (term ? ' for ' + term : '') + ' opens ' + (isToday ? 'today' : niceDate(next[1])) + '.'));
    } else {
      turn.appendChild(make('div', 'hawk-note', 'Registration rounds' + (term ? ' for ' + term : '') + ' have all opened.'));
    }
    steps.forEach(function (x) {
      if (next && x[0] === next[0]) return;
      turn.appendChild(make('div', 'hawk-note', x[0] + ': ' + x[1].toLocaleDateString([], { month: 'long', day: 'numeric' }) + (x[1] < today ? ' (opened)' : '') + '.'));
    });
    /* Rounds 1 and 2 go by appointment; Open Enrollment does not. */
    if (next && next[0] !== 'Open Enrollment') {
      turn.appendChild(make('div', 'hawk-note', 'It opens by appointment — your own time is on the Cal Poly Portal.'));
    }
  }

  /* -- friends_in: which of my friends are in X ------------------------------------------------ */
  function renderFriendsIn(turn, result, cat) {
    var code = result.args.course;
    var list = [];
    try { list = FRIENDS || []; } catch (_) { list = []; }
    if (!list.length) {
      turn.appendChild(make('div', 'hawk-note', 'You haven’t added any friends yet, so there’s nobody to look for.'));
      turn.appendChild(rowEl({ code: '', name: 'Open Friends', chip: null, go: function () { return goPlace('friends'); } }));
      return;
    }
    var mineSec = null;
    try { mineSec = (myClassMeta || {})[code]; } catch (_) {}
    var myCrn = null;
    if (mineSec && Array.isArray(mineSec.secs) && mineSec.secs[0] && mineSec.secs[0].crn) myCrn = String(mineSec.secs[0].crn);
    else if (mineSec && (mineSec.crn || mineSec.class_nbr)) myCrn = String(mineSec.crn || mineSec.class_nbr);

    var hits = list.filter(function (f) { return f && (f.classes || []).indexOf(code) >= 0; });
    if (!hits.length) {
      turn.appendChild(make('div', 'hawk-note', 'None of your friends are in ' + code + '.'));
    } else {
      turn.appendChild(make('div', 'hawk-note', hits.length + (hits.length === 1 ? ' friend is' : ' friends are') + ' in ' + code + ':'));
      hits.forEach(function (f) {
        var crn = null;
        (f.secs || []).forEach(function (x) { if (x && x.code === code && x.crn) crn = String(x.crn); });
        var same = myCrn && crn && myCrn === crn;
        turn.appendChild(rowEl({
          code: '', name: f.name || 'Friend',
          chip: same ? { text: 'same section', tone: 'open' } : (crn ? { text: 'other section', tone: 'full' } : null),
          go: function () {
            try { if (has('openFriendProfile')) { global.openFriendProfile(f.id, 'classes'); return 'Opened ' + f.name; } } catch (_) {}
            return goPlace('friends');
          }
        }));
      });
    }
  }

  /* -- friends_took: classes my friends have already taken ---------------------------------------
     From FRIENDS[].history — the same records the "Already took" tab on a friend's profile shows,
     already on the device. Classes the student still needs lead, then the ones most friends took.
     Nothing is said about how a friend did in it: the history holds no grade, and never will. */
  function renderFriendsTook(turn, result, cat) {
    var a = result.args || {};
    var list = [];
    try { list = FRIENDS || []; } catch (_) { list = []; }
    if (!list.length) {
      turn.appendChild(make('div', 'hawk-note', 'You haven’t added any friends yet, so there’s nobody to ask.'));
      turn.appendChild(rowEl({ code: '', name: 'Open Friends', chip: null, go: function () { return goPlace('friends'); } }));
      return;
    }
    var need = {}, needLabel = '';
    var cand = planCandidates({ scope: a.scope || 'required' }, cat);
    if (cand && cand.list) { cand.list.forEach(function (c) { need[c.code] = c.tag || 'you need'; }); needLabel = cand.label; }
    if (a.scope && (!cand || cand.problem)) {
      turn.appendChild(make('div', 'hawk-note', (cand && cand.problem) || 'I can’t read your requirements in this build.'));
      return;
    }
    var taken = takenSet();
    var by = {}, rows = [];
    list.forEach(function (f) {
      (f && f.history || []).forEach(function (h) {
        var code = h && h.code; if (!code) return;
        if (a.course && code !== a.course) return;
        if (a.subject && code.split(/\s+/)[0] !== a.subject) return;
        if (a.scope && !need[code]) return;
        if (!by[code]) { by[code] = { code: code, friends: [], profs: [] }; rows.push(by[code]); }
        var first = String(f.name || 'Friend').split(' ')[0];
        if (by[code].friends.indexOf(first) < 0) by[code].friends.push(first);
        if (h.professor && by[code].profs.indexOf(h.professor) < 0) by[code].profs.push(h.professor);
      });
    });
    if (!a.course) rows = rows.filter(function (r) { return !taken[r.code]; });
    rows.sort(function (x, y) {
      return ((need[y.code] ? 1 : 0) - (need[x.code] ? 1 : 0))
        || (y.friends.length - x.friends.length)
        || ((sectionsOf(y.code).length ? 1 : 0) - (sectionsOf(x.code).length ? 1 : 0));
    });
    var read = ['classes your friends have taken'];
    if (a.scope) read.push(needLabel || 'that you still need');
    if (a.course) read = [a.course + ' — which friends have taken it'];
    if (a.subject) read.push(a.subject);
    turn.appendChild(make('div', 'hawk-read', read.join(' · ')));
    if (!rows.length) {
      turn.appendChild(make('div', 'hawk-note', a.course
        ? 'None of your friends has ' + a.course + ' in their past classes.'
        : 'None of your friends’ past classes match that yet. Friends add them under Past classes.'));
      return;
    }
    rows.slice(0, 6).forEach(function (r) {
      var profs = r.profs.slice(0, 2).map(flipName);
      turn.appendChild(rowEl({
        rich: true, code: r.code,
        name: cat.courses[r.code] || r.code,
        sub: [r.friends.slice(0, 3).join(', ') + (r.friends.length > 3 ? ' +' + (r.friends.length - 3) : '') + ' took it',
              profs.length ? 'with ' + profs.join(' / ') : null,
              need[r.code] ? (need[r.code] === 'Required' ? 'you still need it' : need[r.code] + ' · you still need it') : null]
              .filter(Boolean).join(' · '),
        chip: courseChip(r.code) || { text: 'not offered', tone: 'wait' },
        go: function () { return goClass(r.code); }
      }));
    });
    turn.appendChild(make('div', 'hawk-count', rows.length + (rows.length === 1 ? ' class' : ' classes')
      + ' from ' + list.length + (list.length === 1 ? ' friend' : ' friends')
      + (rows.length > 6 ? ' · showing 6' : '')));
  }

  /* -- fit_pair: can I take X and Y ------------------------------------------------------------- */
  function renderFitPair(turn, result, cat) {
    var A = result.args.a, B = result.args.b;
    var sa = sectionsOf(A), sb2 = sectionsOf(B);
    if (!sa.length || !sb2.length) {
      var missing = !sa.length ? A : B;
      turn.appendChild(make('div', 'hawk-note', 'No sections in the feed for ' + missing + ' this term, so I can’t check the pair.'));
      turn.appendChild(rowEl({ code: missing, name: cat.courses[missing] || missing, chip: null, go: function () { return goClass(missing); } }));
      return;
    }
    var mine = mySchedule();
    var combos = [];
    sa.forEach(function (ra) {
      var ma = meetOf(ra); if (!ma) return;
      sb2.forEach(function (rb) {
        var mb = meetOf(rb); if (!mb) return;
        if (overlaps(ma, mb)) return;
        var clash = clashesWith(ma, mine).concat(clashesWith(mb, mine));
        combos.push({ ra: ra, rb: rb, ma: ma, mb: mb, clash: clash });
      });
    });
    if (!combos.length) {
      turn.appendChild(make('div', 'hawk-note', 'Every section of ' + A + ' collides with every section of ' + B + '. They can’t be taken together this term.'));
      return;
    }
    var clean = combos.filter(function (c) { return !c.clash.length; });
    var show = (clean.length ? clean : combos).slice(0, 3);
    turn.appendChild(make('div', 'hawk-note', (clean.length || combos.length) + (clean.length ? ' combinations fit' : ' combinations work together, but clash with your week') + ':'));
    show.forEach(function (c) {
      var la = A + '-' + secNumber(c.ra), lb = B + '-' + secNumber(c.rb);
      turn.appendChild(rowEl({
        code: la, name: meetLabel(c.ra) + '  +  ' + lb + ' ' + meetLabel(c.rb),
        chip: null, clash: c.clash.length ? c.clash : null,
        go: function () { return goSection(A, c.ra.class_nbr || c.ra.crn, la); }
      }));
    });
  }

  /* -- swap_section: a different section of a class I'm in ------------------------------------ */
  function renderSwap(turn, result, cat) {
    var code = result.args.course, prefer = result.args.prefer;
    var meta = null;
    try { meta = (myClassMeta || {})[code]; } catch (_) {}
    if (myCodes().indexOf(code) < 0) {
      turn.appendChild(make('div', 'hawk-note', 'You’re not in ' + code + ', so there’s nothing to swap. Here are its sections:'));
      var out = sectionRows(code, {}) || [];
      out.slice(0, 3).forEach(function (r) { turn.appendChild(rowEl(r)); });
      return;
    }
    var myCrn = meta && (meta.crn || meta.class_nbr) ? String(meta.crn || meta.class_nbr) : null;
    var current = null;
    try { current = meta && meta.time && has('parseMeet') ? global.parseMeet(meta.time) : null; } catch (_) {}

    /* The week minus this class, so the class does not clash with itself. */
    var mine = mySchedule();
    if (mine && !mine.empty) mine.placed = mine.placed.filter(function (c) { return c.code !== code; });

    var alts = sectionsOf(code).filter(function (r) { return String(r.class_nbr || r.crn) !== myCrn; })
      .map(function (r) { var m = meetOf(r); return { row: r, meet: m, clash: m ? clashesWith(m, mine) : [], prof: profOf(r) }; })
      .filter(function (x) { return x.meet; });
    if (prefer === 'later' && current) alts = alts.filter(function (x) { return x.meet.start > current.start; });
    if (prefer === 'earlier' && current) alts = alts.filter(function (x) { return x.meet.start < current.start; });
    alts.sort(function (x, y) { return (x.clash.length - y.clash.length) || (x.meet.start - y.meet.start); });

    if (!alts.length) {
      turn.appendChild(make('div', 'hawk-note', 'No ' + (prefer ? prefer + ' ' : 'other ') + 'section of ' + code + ' with a meeting time this term.'));
      return;
    }
    turn.appendChild(make('div', 'hawk-note', (prefer ? prefer[0].toUpperCase() + prefer.slice(1) + ' sections' : 'Other sections') + ' of ' + code
      + (current ? ' (you’re in ' + clock12(current.start) + ')' : '') + ':'));
    alts.slice(0, 4).forEach(function (x) {
      var label = code + '-' + secNumber(x.row);
      turn.appendChild(rowEl({
        code: label, name: meetLabel(x.row) + (x.prof ? ' · ' + x.prof.name : ''),
        chip: seatChip(x.row), chip2: x.prof ? ratingChip(x.prof.rating) : null,
        clash: x.clash.length ? x.clash : null,
        go: function () { return goSection(code, x.row.class_nbr || x.row.crn, label); }
      }));
    });
  }

  function renderNoClasses(turn) {
    turn.appendChild(make('div', 'hawk-note',
      'I don’t have any classes saved for you yet. Add them in Schedule and ask me again.'));
    turn.appendChild(rowEl({ code: '', name: 'Open Schedule', chip: null, go: function () { return goPlace('schedule'); } }));
  }

  /* One dispatcher for everything that is not a catalog search. Returns true when it rendered. */
  function renderTool(turn, result, cat, q) {
    if (result.tool === 'search_sections' && result.args
        && (result.args.scope || result.args.ge_area || (result.args.subject && (result.args.fits_my_schedule || result.args.sort)))) {
      if (renderPlan(turn, result, cat, q)) return true;
    }
    switch (result.tool) {
      case 'build_term':       return renderBuild(turn, result, cat, q);
      case 'go_to':            renderGoTo(turn, result); return true;
      case 'help':             renderHelp(turn); return true;
      case 'set_theme':        renderTheme(turn, result); return true;
      case 'watch':            renderWatch(turn, result, cat); return true;
      case 'open_section':     renderOpenSection(turn, result, cat); return true;
      case 'add_section':      renderAddSection(turn, result, cat); return true;
      case 'rate_professor':   renderRate(turn, result, cat); return true;
      case 'draft_message':    renderDraft(turn, result, cat); return true;
      case 'share':            renderShare(turn, result, cat); return true;
      case 'add_friend':       renderAddFriend(turn, result); return true;
      case 'friend_profile':   renderFriendProfile(turn, result); return true;
      case 'professor_stats':  renderProfStats(turn, result); return true;
      case 'compare_professors': renderCompare(turn, result); return true;
      case 'prereqs':          renderPrereqs(turn, result, cat); return true;
      case 'my_day':           renderMyDay(turn, result); return true;
      case 'my_units':         renderMyUnits(turn); return true;
      case 'my_professors':    renderMyProfessors(turn, result); return true;
      case 'my_requirements':  renderMyRequirements(turn); return true;
      case 'when_registration': renderRegistration(turn); return true;
      case 'game_plan':        renderGamePlan(turn, result); return true;
      case 'friends_in':       renderFriendsIn(turn, result, cat); return true;
      case 'friends_took':     renderFriendsTook(turn, result, cat); return true;
      case 'fit_pair':         renderFitPair(turn, result, cat); return true;
      case 'swap_section':     renderSwap(turn, result, cat); return true;
      case 'my_conflicts':
      case 'my_free':          renderPersonal(turn, result); return true;
      default: return false;
    }
  }

  /* -- my_professors: who teaches my classes, ranked by rating ------------------------------------
     Read from what the app already holds: each saved class's sections (myClassMeta[code].secs[].prof,
     or .prof), else the seat feed's row for the saved CRN. Rated through the same matchProfId →
     PROFESSORS path as every other rating on screen. No rating is never shown as a low one. */
  function myProfessors() {
    var byKey = {}, list = [], unknown = [];
    myCodes().forEach(function (code) {
      var meta = null;
      try { meta = (myClassMeta || {})[code] || null; } catch (_) { meta = null; }
      var names = [];
      (meta && Array.isArray(meta.secs) ? meta.secs : []).forEach(function (sec) {
        var n = sec && sec.prof;
        if (!n && sec && sec.crn) {
          var row = sectionsOf(code).filter(function (r) { return String(r.class_nbr || r.crn) === String(sec.crn); })[0];
          if (row) n = row.instructor || row.name || '';
        }
        if (n) names.push(n);
      });
      if (!names.length && meta && meta.prof) names.push(meta.prof);
      var got = false;
      names.forEach(function (raw) {
        var p = profOf({ instructor: raw });
        if (!p) return;
        got = true;
        var key = p.id || p.name.toLowerCase();
        if (!byKey[key]) { byKey[key] = { prof: p, codes: [] }; list.push(byKey[key]); }
        if (byKey[key].codes.indexOf(code) < 0) byKey[key].codes.push(code);
      });
      if (!got) unknown.push(code);
    });
    return { list: list, unknown: unknown };
  }

  function renderMyProfessors(turn, result) {
    if (!myCodes().length) { renderNoClasses(turn); return; }
    var got = myProfessors();
    var asc = result.args && result.args.order === 'asc';
    var rated = got.list.filter(function (x) { return x.prof.rating != null; });
    var unrated = got.list.filter(function (x) { return x.prof.rating == null; });
    rated.sort(function (a, b) { return asc ? a.prof.rating - b.prof.rating : b.prof.rating - a.prof.rating; });

    if (!got.list.length) {
      turn.appendChild(make('div', 'hawk-note',
        'I can’t see who teaches your classes yet. Pick your sections in Schedule and I’ll rank them.'));
      turn.appendChild(rowEl({ code: '', name: 'Open Schedule', chip: null, go: function () { return goPlace('schedule'); } }));
      return;
    }
    if (rated.length) {
      var top = rated[0];
      turn.appendChild(make('div', 'hawk-note hawk-note--good',
        (asc ? 'Lowest rated: ' : 'Highest rated: ') + top.prof.name + ' (' + top.prof.rating.toFixed(1) + ' ★) — '
        + top.codes.join(', ') + '.'));
    } else {
      turn.appendChild(make('div', 'hawk-note', 'None of your professors has a rating yet.'));
    }
    rated.concat(unrated).forEach(function (x) {
      turn.appendChild(rowEl({
        code: '', name: x.prof.name,
        sub: x.codes.join(', '),
        rich: false,
        chip: x.prof.rating != null ? ratingChip(x.prof.rating) : { text: 'no ratings', tone: 'wait' },
        go: function () { return goProfessor(x.prof.name); }
      }));
    });
    if (got.unknown.length) {
      turn.appendChild(make('div', 'hawk-note', 'No professor on record for ' + got.unknown.join(', ') + '.'));
    }
  }

  function renderPersonal(turn, result) {
    var mine = mySchedule();

    if (!mine || mine.empty) {
      turn.appendChild(make('div', 'hawk-note',
        'I don’t have any classes saved for you yet, so I can’t read your week. '
        + 'Add them in Schedule and ask me again.'));
      turn.appendChild(rowEl({
        code: '', name: 'Open Schedule', chip: null,
        go: function () { try { if (has('show')) global.show('sched'); } catch (_) {} return 'Opened Schedule'; }
      }));
      return;
    }

    if (result.tool === 'my_conflicts') {
      var found = [];
      for (var i = 0; i < mine.placed.length; i += 1) {
        for (var j = i + 1; j < mine.placed.length; j += 1) {
          if (overlaps(mine.placed[i].meet, mine.placed[j].meet)) {
            found.push([mine.placed[i], mine.placed[j]]);
          }
        }
      }
      if (!found.length) {
        turn.appendChild(make('div', 'hawk-note',
          'Nothing in your week overlaps' + countedOver(mine) + '.'));
      } else {
        turn.appendChild(make('div', 'hawk-note',
          found.length === 1 ? 'One clash:' : found.length + ' clashes:'));
        found.forEach(function (pair) {
          var a = pair[0], b = pair[1];
          var sharedDays = a.meet.days.filter(function (d) { return b.meet.days.indexOf(d) >= 0; });
          turn.appendChild(rowEl({
            code: a.code,
            name: 'vs ' + b.code + ' · ' + sharedDays.join('') + ' ' + clock12(Math.max(a.meet.start, b.meet.start)),
            chip: { text: 'clash', tone: 'wait' },
            go: function () { return goClass(a.code); }
          }));
        });
      }
      noteUnplaced(turn, mine);
      return;
    }

    /* my_free */
    var want = (result.args && result.args.days && result.args.days.length)
      ? result.args.days
      : DAY_ORDER.slice(0, 5);
    var any = false;
    want.forEach(function (day) {
      var f = freeOn(day, mine);
      if (f.wholeDay) {
        any = true;
        turn.appendChild(make('div', 'hawk-note',
          DAY_FULL[day] + ' — nothing scheduled all day.'));
        return;
      }
      var first = f.classes[0], last = f.classes[f.classes.length - 1];
      var bits = f.gaps.map(function (g) { return clock12(g.from) + '–' + clock12(g.to); });
      any = true;
      var line = DAY_FULL[day] + ' — '
        + (bits.length ? 'free ' + bits.join(', ') : 'no gaps between classes')
        + ' · in class ' + clock12(first.start) + '–' + clock12(last.end);
      turn.appendChild(make('div', 'hawk-note', line));
    });
    if (!any) turn.appendChild(make('div', 'hawk-note', 'Nothing scheduled on those days.'));
    noteUnplaced(turn, mine);
  }

  function countedOver(mine) {
    var n = mine.placed.length;
    return ' (' + n + (n === 1 ? ' class' : ' classes') + ' I can place on a clock)';
  }

  /* A class with no known meeting time is a hole in the answer, and the student is told about it
     rather than quietly given a conclusion drawn from everything except it. */
  function noteUnplaced(turn, mine) {
    if (!mine.unplaced.length) return;
    turn.appendChild(make('div', 'hawk-note',
      'Not counted — no meeting time on ' + mine.unplaced.join(', ') + '.'));
  }

  function rowEl(r) {
    var row = make('button', 'hawk-row' + (r.near ? ' hawk-row--near' : '') + (r.rich ? ' hawk-row--rich' : ''));
    row.type = 'button';
    /* A RICH row — a recommendation with a real course title and a who/when/why line — puts the
       code ABOVE the title instead of beside it. Beside it, the code took a third of the width and
       every title came out as "Intermediate Chi…", which is not an answer anyone can act on. */
    if (r.code && !r.rich) row.appendChild(make('span', 'hawk-row__code', r.code));
    var main = make('div', 'hawk-row__main');
    if (r.code && r.rich) main.appendChild(make('span', 'hawk-row__code', r.code));
    main.appendChild(make('span', 'hawk-row__name', r.name));
    if (r.sub) main.appendChild(make('span', 'hawk-row__sub', r.sub));
    if (r.near) main.appendChild(make('span', 'hawk-row__near', r.near));
    if (r.clash) {
      main.appendChild(make('span', 'hawk-row__clash',
        'clashes with ' + r.clash.join(', ')));
    }
    row.appendChild(main);
    if (r.chip || r.chip2) {
      /* Two chips stack in a narrow column on the right. Side by side they were eating the time
         column, and "MoWe 3:10…" is not a meeting time anyone can act on. */
      var chips = make('span', 'hawk-row__chips');
      if (r.chip2) chips.appendChild(make('span', 'hawk-chip hawk-chip--' + r.chip2.tone, r.chip2.text));
      if (r.chip) chips.appendChild(make('span', 'hawk-chip hawk-chip--' + r.chip.tone, r.chip.text));
      row.appendChild(chips);
    }
    row.addEventListener('click', function () {
      var went = r.go();
      /* The box stays open and says where it sent you, because the page behind has just changed
         underneath something the student is still looking at. Without this line the app silently
         becomes a different screen and only the lucky notice. */
      var old = els.log.querySelector('.hawk-went');
      if (old) old.remove();
      els.log.appendChild(make('div', 'hawk-went', went));
    });
    return row;
  }

  /* The empty state. Hawk's own face, a greeting, and nothing else — Tate's mockup, 2026-09-21.
     The face is a background-image in the stylesheet rather than an <img>, so it is a data URI in
     one file the service worker already caches. No fourth file, no publish-list entry, no 404. */
  function hintEl() {
    var d = make('div', 'hawk-hint');
    var face = make('div', 'hawk-hint__face');
    face.setAttribute('role', 'img');
    face.setAttribute('aria-label', 'Hawk');
    d.appendChild(face);
    var words = make('div');
    words.appendChild(make('div', 'hawk-hint__lead', 'Hawk is here!'));
    words.appendChild(make('div', 'hawk-hint__sub', 'What can I assist you with?'));
    d.appendChild(words);
    return d;
  }

  /* ---------------------------------------------------------------------------------------------
     Open and close. No scrim, no focus trap: the app behind is genuinely usable, and stealing Tab
     from it would be a lie about what this box is.
     --------------------------------------------------------------------------------------------- */
  function onKey(e) {
    if (e.key === 'Escape' && els.box.parentNode) close();
  }

  /* THE CIRCLE NEVER LEAVES. It used to hide itself whenever the box was open, which meant the one
     thing you could always press in that corner was, at the moment you were using it, not there.
     The box now opens above it instead, so the hawk is permanently on screen and permanently
     clickable — through every page change, because it is a fixed child of <body> and this app
     swaps views underneath rather than reloading. Pressing it while open closes it. */
  function open() {
    if (els.box.parentNode) { els.input.focus(); return; }
    returnFocusTo = document.activeElement;
    document.body.appendChild(els.box);
    els.fab.setAttribute('aria-expanded', 'true');
    if (!moved) restorePos();
    document.addEventListener('keydown', onKey, true);
    if (!els.log.childNodes.length) { els.log.appendChild(hintEl()); stamp(); }
    els.input.focus();
  }

  function close() {
    if (!els.box.parentNode) return;
    document.removeEventListener('keydown', onKey, true);
    els.box.parentNode.removeChild(els.box);
    els.fab.setAttribute('aria-expanded', 'false');
    var target = (returnFocusTo && document.contains(returnFocusTo)) ? returnFocusTo : els.fab;
    try { if (target && typeof target.focus === 'function') target.focus(); } catch (_) {}
    returnFocusTo = null;
  }

  function toggle() {
    if (els.box.parentNode) close(); else open();
  }

  /* ---------------------------------------------------------------------------------------------
     Moving it.
     Dragged by the header, because the body holds tappable rows and the footer holds a text field,
     and a box that starts moving when you meant to select your own typing is worse than one that
     does not move at all.

     Pointer events rather than mouse+touch pairs: one code path, and pointer capture means a fast
     drag that outruns the cursor does not drop the box halfway across the screen.

     Position is remembered per browser. It is a convenience, not state — if localStorage is
     unavailable or the saved spot no longer fits the window, it silently goes back to the corner.
     --------------------------------------------------------------------------------------------- */
  var POS_KEY = 'hawk-pos';
  var moved = false;

  function clampTo(x, y) {
    var r = els.box.getBoundingClientRect();
    var maxX = Math.max(8, window.innerWidth - r.width - 8);
    var maxY = Math.max(8, window.innerHeight - r.height - 8);
    return { x: Math.min(Math.max(8, x), maxX), y: Math.min(Math.max(8, y), maxY) };
  }

  function placeAt(x, y) {
    var p = clampTo(x, y);
    els.box.style.left = p.x + 'px';
    els.box.style.top = p.y + 'px';
    els.box.style.right = 'auto';
    els.box.style.bottom = 'auto';
    moved = true;
    return p;
  }

  function savePos(p) {
    try { localStorage.setItem(POS_KEY, JSON.stringify(p)); } catch (_) {}
  }

  function restorePos() {
    var raw = null;
    try { raw = localStorage.getItem(POS_KEY); } catch (_) { return; }
    if (!raw) return;
    var p;
    try { p = JSON.parse(raw); } catch (_) { return; }
    if (!p || typeof p.x !== 'number' || typeof p.y !== 'number') return;
    /* A window narrower than the saved spot would strand the box off-screen. Corner instead. */
    var r = els.box.getBoundingClientRect();
    if (p.x + r.width > window.innerWidth || p.y + r.height > window.innerHeight) return;
    placeAt(p.x, p.y);
  }

  function makeDraggable(handle) {
    var sx = 0, sy = 0, ox = 0, oy = 0, dragging = false;

    handle.addEventListener('pointerdown', function (e) {
      if (e.target.closest && e.target.closest('.hawk-x')) return;   // the close button is a button
      if (e.button != null && e.button !== 0) return;                // left / primary only
      var r = els.box.getBoundingClientRect();
      dragging = true;
      sx = e.clientX; sy = e.clientY; ox = r.left; oy = r.top;
      placeAt(r.left, r.top);
      els.box.classList.add('hawk-box--moving');
      try { handle.setPointerCapture(e.pointerId); } catch (_) {}
      e.preventDefault();
    });

    handle.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      placeAt(ox + (e.clientX - sx), oy + (e.clientY - sy));
    });

    function end(e) {
      if (!dragging) return;
      dragging = false;
      els.box.classList.remove('hawk-box--moving');
      try { handle.releasePointerCapture(e.pointerId); } catch (_) {}
      var r = els.box.getBoundingClientRect();
      savePos({ x: Math.round(r.left), y: Math.round(r.top) });
    }
    handle.addEventListener('pointerup', end);
    handle.addEventListener('pointercancel', end);

    /* A window that shrinks under a moved box would hide it. Pull it back into view. */
    window.addEventListener('resize', function () {
      if (!moved || !els.box.parentNode) return;
      var r = els.box.getBoundingClientRect();
      placeAt(r.left, r.top);
    });
  }

  function submit() {
    var q = String(els.input.value || '').trim();
    if (!q) return;
    answer(q);
    els.input.value = '';
    els.send.disabled = true;
    els.input.focus();
  }

  function spark() {
    var s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('width', '13');
    s.setAttribute('height', '13');
    s.setAttribute('fill', 'currentColor');
    s.setAttribute('aria-hidden', 'true');
    var p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', 'M12 2l2.2 6.6L21 11l-6.8 2.4L12 20l-2.2-6.6L3 11l6.8-2.4z');
    s.appendChild(p);
    return s;
  }

  function mount() {
    if (document.querySelector('.hawk-fab')) return;

    /* The way in is Hawk's own face, in a circle, bottom-right, on every screen and at every size.
       It is never hidden and never covered — the box opens above it — so there is always exactly
       one thing in that corner to press. */
    var fab = make('button', 'hawk-fab');
    fab.type = 'button';
    fab.setAttribute('aria-label', 'Ask Hawk');
    fab.setAttribute('aria-expanded', 'false');

    var box = make('aside', 'hawk-box');
    box.setAttribute('aria-label', 'Hawk');

    /* A titled header band, so the box says what it is before it says anything else. */
    var head = make('div', 'hawk-head');
    var headSpark = make('span', 'hawk-head__spark');
    headSpark.appendChild(spark());
    head.appendChild(headSpark);
    head.appendChild(make('span', 'hawk-head__name', 'Hawk'));
    head.appendChild(make('span', 'hawk-head__sub', 'AI assistant'));

    var log = make('div', 'hawk-log');
    log.setAttribute('role', 'status');
    log.setAttribute('aria-live', 'polite');

    var x = make('button', 'hawk-x', '×');
    x.type = 'button';
    x.setAttribute('aria-label', 'Close Hawk');
    head.appendChild(x);

    var ask = make('form', 'hawk-ask');
    var label = make('label', 'hawk-sr', 'Ask Hawk');
    label.setAttribute('for', 'hawk-input');
    var input = make('input', 'hawk-input');
    input.type = 'text';
    input.id = 'hawk-input';
    input.autocomplete = 'off';
    input.maxLength = 300;
    input.placeholder = 'Ask Hawk…';
    var send = make('button', 'hawk-send', 'Ask');
    send.type = 'submit';
    send.disabled = true;
    ask.appendChild(label);
    ask.appendChild(input);
    ask.appendChild(send);

    var foot = make('div', 'hawk-foot', privacyLine());

    box.appendChild(head);
    box.appendChild(log);
    box.appendChild(foot);
    box.appendChild(ask);
    document.body.appendChild(fab);

    els = { fab: fab, box: box, log: log, input: input, send: send, foot: foot };

    fab.addEventListener('click', toggle);
    makeDraggable(head);
    x.addEventListener('click', close);
    input.addEventListener('input', function () { send.disabled = !input.value.trim(); });
    ask.addEventListener('submit', function (e) { e.preventDefault(); submit(); });

    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && String(e.key).toLowerCase() === 'k') {
        e.preventDefault();
        if (els.box.parentNode) close(); else open();
      }
    });

    global.HawkAsk = {
      open: open,
      close: close,
      ask: function (q) { open(); answer(String(q || '')); },
      route: function (q) { return R.route(q, buildCatalog()); },
      /* For the harness: the explanation check, on its own, so a lie can be fed to it directly. */
      verifyExplanation: verifyExplanation
    };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
}(typeof self !== 'undefined' ? self : this));
