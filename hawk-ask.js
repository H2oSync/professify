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
        sec: crn ? { code: code, crn: String(crn) } : null,
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
        sec: crn ? { code: x.course.code, crn: String(crn) } : null,
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
                    sec: crn ? { code: pk.code, crn: String(crn) } : null,
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
  /* website-hawk-app-menu (2026-10-14) */
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
    return callAsk({ q: q, client: 'app' }).then(function (j) {   /* website-hawk-app-menu (2026-10-14): the app's menu of tools */
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
    if (result.refused || result.followUp || result.local) return true;
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

  /* WHAT THE FOOTER PROMISES HAS TO BE TRUE. With the model tier on, the question does leave the
     browser — to TermChamp's server and on to the AI vendor — so "nothing leaves" became a lie the
     day AI-first shipped. What stays true either way: the student's classes, friends and ledger
     never leave; the model sees the question and, for an explanation, only public catalog rows. */
  function privacyLine() {
    /* Signed in, a question that needs the model goes to the `ask` function and on to Anthropic; many are answered
       in the browser, hence "Some". Signed out nothing leaves (sessionToken() is null and callAsk stops). The phone's
       line is "Questions go to Anthropic’s AI · your classes stay on this phone". */
    var signedIn = false;
    try { signedIn = typeof sbUser !== 'undefined' && !!(sbUser && sbUser.id); } catch (_) {}
    return aiUrl() && signedIn ? 'Some questions go to Anthropic’s AI · your classes stay on this device'
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
    var turn = newTurn(q);
    turn.appendChild(make('div', 'hawk-note hawk-thinking', 'Working that out…'));
    place(turn);
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
    help: 'What Champ can do'
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

    var hrows = (shown && shown.tool === 'app_help') ? [] : helpRows(q);
    var box = make('div', 'hawk-alts');
    box.appendChild(make('div', 'hawk-alts__head', (alts.length || hrows.length) ? 'Did you mean' : (quiet ? 'Try a course code, a professor, or “open CSC labs after 6”.' : 'Sorry about that. Try it another way:')));
    hrows.forEach(function (r) { box.appendChild(rowEl(r)); });
    alts.slice(0, Math.max(0, 3 - hrows.length)).forEach(function (r) {
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
    if (!quiet) box.appendChild(make('div', 'hawk-alts__noted', 'Noted — this helps Champ get better.'));
    turn.appendChild(box);
    try { box.scrollIntoView({ block: 'nearest' }); } catch (_) {}
  }

  /* ===============================================================================================
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

  function render(q, result, cat, replaceTurn) {
    if (result.tool !== 'build_term') lastBuild = null;
    /* A row that re-asks the same question (Loosened it, Here's that instead) replaces its own turn rather than stacking. */
    if (!replaceTurn && clickTurn && clickTurn.isConnected) {
      var cq = clickTurn.querySelector('.hawk-said__q');
      if (cq && cq.textContent === q) replaceTurn = clickTurn;
    }
    var turn = newTurn(q);
    var said = turn.querySelector('.hawk-said');
    (result.corrections || []).forEach(function (c) {
      said.appendChild(make('span', 'hawk-fix', c.typed + ' → ' + c.read));
    });
    /* Say when a question left the browser. The free tier answers on the device and this one does
       not, and which of the two happened is the student's business — it is the difference between
       a question nobody else ever saw and one that was sent somewhere. */
    if (result.viaModel) said.appendChild(make('span', 'hawk-fix hawk-fix--ai', 'AI'));

    if (result.refused) {
      if (!helpChips(turn, q)) turn.appendChild(make('div', 'hawk-note',
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
        if (helpChips(turn, q)) why = 'shown';
        else turn.appendChild(make('div', 'hawk-note',
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

    place(turn, replaceTurn);
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
    els.foot.textContent = when ? when + ' · ' + privacyLine() : privacyLine();   /* the as-of joins the privacy line; it never replaces it */
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
    if (['dark', 'light'].indexOf(t) < 0 || !has('setTheme')) { notFound(turn, 'I can switch between light and dark.'); return; }   /* cream retired 2026-10-04 */
    var prev = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
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
  /* A prerequisite group is "one of these". Rendered as such rather than flattened. */
  function groupLabel(g) {
    if (Array.isArray(g)) return g.length > 1 ? 'one of ' + g.join(' / ') : String(g[0] || '');
    return String(g || '');
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

  /* ===============================================================================================
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

  /* One dispatcher for everything that is not a catalog search. Returns true when it rendered. */

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
  /* app_help: the sixteen questions about TermChamp, in a sentence or two, and where to go */
  var APP_HELP = {
    what_is: ['TermChamp helps Cal Poly students plan classes with friends: professor ratings, open seats, and which friends are in each class. It’s made by students — not a Cal Poly service.', 'Browse classes', 'explore'],
    free: ['Yes — TermChamp is free. There are no ads, and your data is never sold.', 'Privacy policy', 'privacy policy'],
    who_sees: ['Only friends you’ve accepted see your classes. Each plan has its own “Friends can see” switch — turn it off to keep that plan to yourself. Remove a friend and they stop seeing it.', 'Open Settings', 'privacy settings'],
    ratings_anonymous: ['Yes. Your name is never shown on a review — professors and other students can’t tell it was you. You can choose to show your friends, one review at a time.', 'Your reviews', 'my reviews'],
    ratings_source: ['From PolyRatings, plus the reviews TermChamp students write here. Open a professor to see their rating.', 'Find a professor', 'explore professors'],
    seats_source: ['From Cal Poly’s public class search, refreshed about once a day — so they can be a day old, or wrong. Always check the Cal Poly Portal before you register.', 'Browse classes', 'explore'],
    add_class: ['Find it in Explore, open the class and tap “I’m in this” on your section — or ＋ Plan to put it in Plan A, B or C. Classes you’ve already taken go in Schedule › Past classes.', 'Open Explore', 'explore'],
    plans: ['Plans A, B and C are three versions of your next term, kept in Schedule › Plans. Add a section to one from any class page with ＋ Plan, or let the Planner draft all three, and change any of them. Ask me for your game plan to see what to register for first.', 'Open Plans', 'watchlist'],
    seat_alerts: ['Tap Watch on a full section; sections you add to a plan are watched for you. With notifications on, the TermChamp iPhone app tells you when a seat opens.', 'Browse classes', 'explore'],
    degree_report: ['In the Cal Poly Portal: Student Center › Academic Progress › Degree Progress Report › View PDF › Download. Then upload it in Schedule › Past classes. Your grades and student ID are never saved.', 'Open Past classes', 'past classes'],
    add_friends: ['Open Friends and search by name or @username, or share your QR code or invite link. Once they accept, you see each other’s classes.', 'Add a friend', 'add friend'],
    block_report: ['Open their profile or your chat with them and use Block or Report at the bottom — they aren’t told. To report a review, use the flag on it. A person looks at every report within 24 hours.', 'Open Friends', 'friends'],
    delete_account: ['Settings › Delete account. It’s hidden right away and deleted after 30 days — sign back in before then to recover it. You choose whether your reviews stay up with no name.', 'Open Settings', 'account'],
    champ: ['Champ answers questions about classes, professors, your week, your friends and TermChamp. Each question you ask goes to Anthropic’s AI to work out what you mean — never your name or account, though a class or friend you name goes with it. TermChamp keeps questions about 30 days, not linked to you, and Anthropic doesn’t train on them.', 'Privacy policy', 'privacy policy'],
    dark_mode: ['Yes — Settings › Appearance: Light or Dark.', 'Open Settings', 'appearance'],
    contact: ['Email support@termchamp.com — for a bug, feedback, or anything else.', 'Email support', 'mailto']
  };
  /* The questions as the chips show them (the phone's HELP[k].q). */
  var APP_HELP_Q = { what_is: 'What is TermChamp?', free: 'Is TermChamp free?', who_sees: 'Who can see my schedule?',
    ratings_anonymous: 'Are my reviews anonymous?', ratings_source: 'Where do the ratings come from?',
    seats_source: 'Where do the seat numbers come from?', add_class: 'How do I add a class?', plans: 'What are Plans A, B and C?',
    seat_alerts: 'How do seat alerts work?', degree_report: 'How do I upload my degree report?', add_friends: 'How do I add friends?',
    block_report: 'How do I block or report someone?', delete_account: 'How do I delete my account?',
    champ: 'What does Champ do and where does my information go?', dark_mode: 'Is there a dark mode?', contact: 'How do I contact TermChamp?' };
  /* helpMatch — lifted verbatim from the phone (app/index.html, champ-help-2026-10-11). OFFERED, never answered on a guess. */
  var HW = { app: /\b(termchamp|term champ|this app|the app|app|this site)\b/,
    mine: /\b(my|im|i'm|i am) (schedule|classes|class list|plans?|week|timetable|courses)\b|\bclasses (im|i'm|i am) (taking|in)\b/,
    ai: /\b(hawk|champ|ai|bot|chatbot|assistant|anthropic|claude)\b/, notClass: { not: /\b(class|classes|course|courses|lab|book|books|textbook|permit|parking|tuition|units?|housing|dorm|food|gym)\b/ } };
  var HELP_RULES = {
    what_is: [[3, /\b(what'?s|whats|what is|what does|what even is)\b/, /\b(termchamp|term champ|this app)\b/], [3, /\bwho\b/, /\b(made|built|makes|runs|created|owns|behind)\b/, /\b(termchamp|term champ|this app|the app|this site)\b|\b(it|this) ?$/],
      [3, /\b(affiliated|endorsed)\b/], [3, /\bofficial\b/, /\b(app|termchamp|this|cal poly)\b/, { not: /\b(transcript|records?|grades?)\b/ }],
      [2, /\b(explain|tell me about|how does|what can i do (on|with))\b/, /\b(this app|the app|termchamp)\b/]],
    free: [[3, /\b(termchamp|term champ|this app|the app) (free|cost|costs)\b/], [3, /\b(is|was) (it|this) free( to use)? ?$|\bfree to use ?$/],
      [3, /\bhow much (does|is) (it|this|termchamp|the app)\b/, HW.notClass], [3, /\b(have to|need to|do i) pay\b|\bpaywall\b|\bpremium\b|\bsubscription\b|\bcosts? money\b/, HW.notClass],
      [3, /\b(cost|costs|price|pricing|pay for)\b/, HW.app], [3, /\b(ads|adverts?|advertising|advertisements?)\b/, HW.app], [3, /\bthere ads\b|\bany ads\b/],
      [3, /\bsell\w*\b/, /\b(data|info|information)\b/]],
    who_sees: [[3, /\b(see|sees|seeing|view|views|visible|look at|access)\b/, HW.mine, /\b(who|whom|ppl|people|someone|somebody|anyone|anybody|everyone|strangers|random|others|public|friends|students|professors?)\b/],
      [3, /\b(private|public|hidden|hide|privacy)\b/, /\bmy (schedule|classes|class list|plans?|week|timetable|courses|profile|account)\b/]],
    ratings_anonymous: [[3, /\b(anonymous|anonymously|anon)\b/],
      [3, /\b(know|see|find out|figure out|tell)\b/, /\b(i|me|my)\b/, /\b(wrote|review|reviews|rated|rating|ratings)\b/, /\b(professors?|profs?|teachers?|people|ppl|friends|anyone|others|they|everyone)\b/],
      [3, /\b(figure out|find out|know|tell|see) who (posted|wrote|left|made)\b/, /\b(review|reviews|rating|ratings)\b/], [3, /\bname\b/, /\b(review|reviews|rating|ratings)\b/]],
    ratings_source: [[3, /\b(where|how)\b/, /\b(ratings?|reviews?|stars?|scores?)\b/, /\b(come from|from|calculated|work|made|get)\b/], [3, /\bpoly ?ratings\b/],
      [3, /\bhow\b/, /\b(professors?|profs?|teachers?)\b/, /\b(rated|scored|ranked)\b/], [3, /\b(ratings?|reviews?)\b/, /\b(real|accurate|legit|fake|trust|reliable|scraped|sourced)\b/],
      [3, /\bwho (writes|makes|leaves|does)\b/, /\b(the )?(ratings|reviews)\b/]],
    seats_source: [[3, /\b(seats?|seat counts?|seat numbers?|enrollment numbers?)\b/, /\b(come from|from|live|accurate|up to date|updated|update|real|real time|realtime|wrong|correct|old|stale|refresh\w*|how often|reliable)\b/],
      [3, /\bwhere (do|does) (you|u|they|termchamp|the app)\b/, /\bseats?|seat (counts?|numbers?)\b/]],
    add_class: [[3, /\b(how|where)\b/, /\b(add|adding|put|enter|import)\b/, /\b(class|classes|course|courses|schedule)\b/],
      [3, /^ (add|put in|enter) (a|my) (class|classes|course|courses)\b/], [3, /\badding (my )?classes\b/]],
    plans: [[3, /\b(what|why|how)\b/, /\b(plans a|plans? a,? b|three plans|3 plans|a plan)\b/], [3, /\bwhat (is|are) plans?\b/],
      [3, /\b(multiple|different|three|3|several|other|two) plans\b|\bplan tabs\b|\bbackup (plans?|schedules?)\b/], [3, /\b(make|switch|use|set up|create|between)\b/, /\bplans? ?[abc]\b/]],
    seat_alerts: [[3, /\b(seat alerts?|alerts?|notifications?|notified|notify|push|watch|watching|watched|watchlist)\b/, /\b(how|what|does|do|will|work|works|mean|get|set up|setup|turn on|full)\b/]],
    degree_report: [[3, /\b(dpr|degree progress report|degree progress|degree report|degree audit|academic progress)\b/, /\b(how|where|why|what|whats|what's|safe|upload|get|need|private|download|find|import|read|use|add)\b/]],
    add_friends: [[3, /\b(how|where|can)\b/, /\b(add|find|invite|friend request|connect\w*|search)\b/, /\bfriends?\b/], [3, /\bhow do(es)? (friends?|friend requests?) work\b/],
      [3, /\b(how|can i|where)\b/, /\binvite\b/, { not: /\blink\b/ }]],
    block_report: [[3, /\b(block|blocking|harass\w*|bull(y|ying|ied)|stalk\w*|abusive|inappropriate|offensive|creepy|mean to me|threaten\w*)\b/, { not: /\bblock(ing)? (off|out)\b|\b(time|class) blocks?\b|\bblock schedul/ }],
      [3, /\b(report|reporting|flag)\b/, /\b(someone|somebody|a user|user|person|people|review|reviews|message|messages|profile|group|account|him|her|them|abuse|post)\b/, { not: /\b(progress|degree|dpr|transfer)\b/ }]],
    delete_account: [[3, /\b(delete|deleting|deleted|deactivate|close|cancel|erase|wipe|remove)\b/, /\b(account|termchamp|my data|everything|my profile|the app)\b/, { not: /\b(photo|picture|pic|class|classes|friend|friends|plan)\b/ }],
      [3, /\b(recover|restore|get back|undelete)\b/, /\baccount\b/]],
    champ: [[3, HW.ai, /\b(send|sends|sent|data|info|information|privacy|private|store|stores|stored|keep|keeps|save|saves|saved|track|tracks|tracking|train|training|safe|share|shares|shared|questions?|messages?|chats?)\b/],
      [3, /\bwhat (does|is|can)\b/, /\b(?:champ|hawk)\b/], [3, /\bwho is (?:champ|hawk)\b|\bchamp\b.*\b(real person|a person|human|a bot|ai)\b/], [3, HW.ai, /\b(see|sees|read|reads|access|know|knows)\b/, /\bmy\b/],
      [3, /\bwhere\b/, /\b(info|information|data|questions?)\b/, /\b(go|goes|going|sent|stored|kept)\b/]],
    dark_mode: [[3, /\b(dark|night|light) ?(mode|theme)\b/], [3, /\b(change|switch|customi[sz]e)\b/, /\b(colou?rs?|theme|look|looks|appearance)\b/], [3, /\bdark\b/, /\b(app|setting|settings|screen|version)\b/]],
    contact: [[3, /\b(contact|customer service|help desk|helpdesk)\b/, { not: /\b(professors?|profs?|teachers?|advisors?|instructors?|ta|department|registrar|counselor)\b/ }], [3, /\bsupport\b/, { not: /\b(class|classes|course|courses|requirements?|units|ge|major)\b/ }],
      [3, /\b(bug|bugs|glitch|glitches|crash\w*|not working|doesn'?t work|isn'?t working)\b/], [3, /\b(broken|not loading|won'?t load|keeps freezing)\b/, /\b(app|termchamp|it)\b/],
      [3, /\b(feedback|suggestion|feature request)\b/], [3, /\b(problem|issue)\b/, HW.app], [3, /\b(email|e-mail)\b/, /\b(team|termchamp|you guys|the devs?|developers?|creators?)\b/],
      [3, /\b(talk to|reach|message|email) (a )?(human|person|someone|the team|the devs?|the developers?|the creators?|you guys)\b/]],
  };
  /* A question that is just a topic's name ("cost?", "seat alerts", "add friend"). */
  var HELP_BARE = { free: /^ (cost|price|ads|is it free|free) $/, seat_alerts: /^ (seat alerts?|alerts|watching|notifications) $/, add_friends: /^ (add|adding|find) (a )?friends? $/,
    plans: /^ (plans?|plans? [abc]|plan a b c) $/, degree_report: /^ (dpr|degree progress report|degree report) $/, dark_mode: /^ dark $/, contact: /^ (support|contact|feedback) $/ };
  Object.keys(HELP_BARE).forEach(k => HELP_RULES[k].push([3, HELP_BARE[k]]));
  function helpMatch(q) {
    const t = ' ' + String(q || '').toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim() + ' ';
    if (t.trim().length < 4 || /\b[a-z]{2,5} ?\d{3,4}[a-z]?\b/.test(t.replace(/\b(fall|winter|spring|summer|in|of|since|by|until|for|class of) (19|20)\d\d\b/g, ' '))) return [];
    return Object.keys(HELP_RULES).map(k => ({ k, s: HELP_RULES[k].reduce((n, r) => {
        const w = r[0], rs = r.slice(1), not = rs.find(x => x && x.not);
        return rs.every(x => (x && x.not) ? true : x.test(t)) && !(not && not.not.test(t)) ? n + w : n; }, 0) }))
      .filter(x => x.s >= 2).sort((x, y) => y.s - x.s).slice(0, 2).map(x => x.k);
  }
  /* Up to two "Did you mean" rows for TermChamp questions; a tap answers from APP_HELP on this page (nothing sent). */
  function helpRows(q) {
    var ks = []; try { ks = helpMatch(q).filter(function (k) { return APP_HELP_Q[k] && APP_HELP[k]; }); } catch (_) {}
    return ks.map(function (k) {
      return { code: '', name: APP_HELP_Q[k], chip: null, go: function () {
        try { if (has('track')) global.track('hawk_help_chip', null, 'hawk', { topic: k }); } catch (_) {}
        readings = { local: null, model: null };
        render(APP_HELP_Q[k], { prerouted: true, confident: true, in_scope: true, tool: 'app_help', args: { topic: k },
                                corrections: [], leftovers: [], signals: [] }, buildCatalog());
        return 'Here’s that'; } };
    });
  }
  function helpChips(turn, q) {
    var rows = helpRows(q); if (!rows.length) return false;
    var box = make('div', 'hawk-alts');
    box.appendChild(make('div', 'hawk-alts__head', rows.length > 1 ? 'Did you mean one of these?' : 'Did you mean this?'));
    rows.forEach(function (r) { box.appendChild(rowEl(r)); });
    turn.appendChild(box);
    return true;
  }
  function renderAppHelp(turn, result) {
    var k = String((result.args || {}).topic || ''), h = Object.prototype.hasOwnProperty.call(APP_HELP, k) ? APP_HELP[k] : null;
    if (!h) { turn.appendChild(make('div', 'hawk-note', 'I’m not sure which question you mean — try asking it another way.')); return; }
    turn.appendChild(make('div', 'hawk-note', h[0]));
    turn.appendChild(rowEl({ code: '', name: h[1], chip: null,
      go: function () { if (h[2] === 'mailto') { try { global.location.href = 'mailto:support@termchamp.com'; } catch (_) {} return 'Opened your email'; } return goPlace(h[2]); } }));
  }

  function renderTool(turn, result, cat, q) {
    if (result.tool === 'search_sections' && result.args
        && (result.args.scope || result.args.ge_area || (result.args.subject && (result.args.fits_my_schedule || result.args.sort)))) {
      if (renderPlan(turn, result, cat, q)) return true;
    }
    var ans = answerFromTool(result, cat);
    if (ans) { renderAnswer(turn, ans); return true; }
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
      case 'my_units':         renderMyUnits(turn); return true;
      case 'my_requirements':  renderMyRequirements(turn); return true;
      case 'when_registration': renderRegistration(turn); return true;
      case 'friends_in':       renderFriendsIn(turn, result, cat); return true;
      case 'friends_took':     renderFriendsTook(turn, result, cat); return true;
      case 'fit_pair':         renderFitPair(turn, result, cat); return true;
      case 'swap_section':     renderSwap(turn, result, cat); return true;
      case 'app_help':         renderAppHelp(turn, result); return true;
      default: return false;
    }
  }

  /* -- my_professors: who teaches my classes, ranked by rating ------------------------------------
     Read from what the app already holds: each saved class's sections (myClassMeta[code].secs[].prof,
     or .prof), else the seat feed's row for the saved CRN. Rated through the same matchProfId →
     PROFESSORS path as every other rating on screen. No rating is never shown as a low one. */
  function myProfessors(lists) {
    var byKey = {}, list = [], unknown = [];
    (lists || [{ codes: myCodes(), meta: null }]).forEach(function (L) { L.codes.forEach(function (code) {
      var meta = null;
      try { meta = (L.meta || myClassMeta || {})[code] || null; } catch (_) { meta = null; }
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
    }); });
    return { list: list, unknown: unknown };
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
    if (r.fit && !r.clash) main.appendChild(make('span', 'hawk-row__fit', r.fit));
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

  /* The empty state. Hawk's own face, a greeting, and nothing else — Tate's mockup, 2026-09-21.
     The face is a background-image in the stylesheet rather than an <img>, so it is a data URI in
     one file the service worker already caches. No fourth file, no publish-list entry, no 404. */
  /* The phone's four starter questions, word for word (app/index.html champView `sugg`). Each is asked through
     answer(), the path a typed question takes. */
  var STARTERS = [['cc1', 'When am I free this week?'], ['cc2', 'Who\'s free right now?'], ['cc3', 'What’s my day look like?'], ['cc4', 'My best professor']];
  function startersEl(cls) {
    var d = make('div', cls);
    STARTERS.forEach(function (s) {
      var b = make('button', 'hawk-cchip hawk-' + s[0], s[1]);
      b.type = 'button';
      b.addEventListener('click', function () { answer(s[1]); });
      d.appendChild(b);
    });
    return d;
  }
  /* The sheet is "empty" while the greeting is up: then the big bird and the 2 x 2 chips show, and the slim chip row and
     the header bird do not (and the other way round once there is an answer). */
  function syncEmpty() {
    var empty = !!els.log.querySelector('.hawk-hint');
    els.box.classList.toggle('hawk-box--empty', empty);
  }
  function hintEl() {
    var d = make('div', 'hawk-hint');
    var face = make('div', 'hawk-hint__face');
    face.setAttribute('role', 'img');
    face.setAttribute('aria-label', 'Champ');
    d.appendChild(face);
    d.appendChild(make('div', 'hawk-hint__lead', 'Hi, I\'m Champ.'));
    d.appendChild(make('div', 'hawk-hint__sub', 'Ask about classes, professors, your week or your friends.'));
    d.appendChild(startersEl('hawk-cgrid'));
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
    else stamp();
    syncEmpty();
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
      if (e.target.closest && e.target.closest('.hawk-x, .hawk-clear')) return;   // the close and clear buttons are buttons
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
    fab.setAttribute('aria-label', 'Ask Champ');
    fab.setAttribute('aria-expanded', 'false');
    /* The phone's Champ (2026-10-14): "Ask Me!" over the bird. Decorative; the button's name is its label. */
    var bub = make('span', 'hawk-fab__bub', 'Ask Me!'); bub.setAttribute('aria-hidden', 'true');
    var bird = make('span', 'hawk-fab__bird'); bird.setAttribute('aria-hidden', 'true');
    fab.appendChild(bub); fab.appendChild(bird);

    var box = make('aside', 'hawk-box');
    box.setAttribute('aria-label', 'Champ');

    /* A titled header band, so the box says what it is before it says anything else. */
    var head = make('div', 'hawk-head');
    var headBird = make('span', 'hawk-head__bird'); headBird.setAttribute('aria-hidden', 'true');
    head.appendChild(headBird);
    head.appendChild(make('span', 'hawk-head__name', 'Champ'));
    head.appendChild(make('span', 'hawk-head__sub', 'Answers from TermChamp’s real data'));

    var log = make('div', 'hawk-log');
    log.setAttribute('role', 'status');
    log.setAttribute('aria-live', 'polite');

    var x = make('button', 'hawk-x', '×');
    x.type = 'button';
    x.setAttribute('aria-label', 'Close Champ');
    var clr = make('button', 'hawk-clear');
    clr.type = 'button';
    clr.setAttribute('aria-label', 'Clear chat');
    clr.appendChild(icon('trash', 17, 2));
    head.appendChild(clr);
    head.appendChild(x);

    var ask = make('form', 'hawk-ask');
    var label = make('label', 'hawk-sr', 'Ask Champ');
    label.setAttribute('for', 'hawk-input');
    var input = make('input', 'hawk-input');
    input.type = 'text';
    input.id = 'hawk-input';
    input.autocomplete = 'off';
    input.maxLength = 300;
    input.placeholder = 'Ask Champ…';
    var send = make('button', 'hawk-send');
    send.type = 'submit';
    send.setAttribute('aria-label', 'Send');
    var arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    arrow.setAttribute('viewBox', '0 0 24 24'); arrow.setAttribute('width', '20'); arrow.setAttribute('height', '20');
    arrow.setAttribute('aria-hidden', 'true'); arrow.setAttribute('fill', 'none'); arrow.setAttribute('stroke', 'currentColor');
    arrow.setAttribute('stroke-width', '2.6'); arrow.setAttribute('stroke-linecap', 'round'); arrow.setAttribute('stroke-linejoin', 'round');
    var ap = document.createElementNS('http://www.w3.org/2000/svg', 'path'); ap.setAttribute('d', 'M5 12h14M13 6l6 6-6 6');
    arrow.appendChild(ap); send.appendChild(arrow);
    send.disabled = true;
    ask.appendChild(label);
    ask.appendChild(input);
    ask.appendChild(send);

    var foot = make('div', 'hawk-foot', privacyLine());

    box.appendChild(head);
    box.appendChild(log);
    box.appendChild(startersEl('hawk-chips'));
    box.appendChild(ask);
    box.appendChild(foot);
    document.body.appendChild(fab);

    els = { fab: fab, box: box, log: log, input: input, send: send, foot: foot };
    try { new MutationObserver(syncEmpty).observe(log, { childList: true }); } catch (_) {}

    fab.addEventListener('click', toggle);
    makeDraggable(head);
    x.addEventListener('click', close);
    clr.addEventListener('click', clearChat);
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
