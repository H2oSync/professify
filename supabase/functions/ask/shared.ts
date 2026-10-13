/* The ask function's prompt, tools, vendor calls, validation and pricing — shared by the function
   (index.ts) and by the model comparison (golden/check-models.ts), so the models are scored on the
   EXACT prompt and tools students get. A second copy would drift, and then the score would be for
   a Hawk nobody uses. Moved out of index.ts unchanged on 2026-09-24. */
export const MAX_Q = 300;
export const TIMEOUT_MS = 8000;
export const MAX_OUT = 200;

export const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': 'authorization, content-type',
  'access-control-allow-methods': 'POST, OPTIONS',
};

/* ------------------------------------------------------------------------------------------------
   The tools. Descriptions are tokens on every single call, so every line here is paid for on every
   question a student asks. They are terse on purpose.
   ------------------------------------------------------------------------------------------------ */
export const TOOLS = [
  {
    name: 'search_sections',
    description: 'Find sections in the current term.',
    parameters: {
      type: 'object',
      properties: {
        subject: { type: 'string', description: 'Subject code, e.g. CSC' },
        course: { type: 'string', description: 'Course code, e.g. CSC1001 or BUS4442' },
        days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'] } },
        at_time: { type: 'string', description: 'HH:MM 24h, sections starting near this time' },
        start_after: { type: 'string', description: 'HH:MM 24h' },
        end_before: { type: 'string', description: 'HH:MM 24h' },
        open_only: { type: 'boolean', description: 'Only sections with seats' },
        min_rating: { type: 'number', description: 'Professor rating floor, 1-5' },
        instruction_mode: { type: 'string', enum: ['in_person', 'hybrid', 'async', 'sync_online'] },
        ge_area: { type: 'string', description: 'Cal Poly 2026 GE area KEY. What each key means (these are the app\'s own labels): 1A Written Communication; 1B Critical Thinking; 1C Oral Communication; 2 Math & Quantitative; 3A Arts; 3B Humanities; 4A American Institutions; 4B Social & Behavioral Sciences; 5A Physical Science; 5B Life Science; 5C Lab Science; 6 Ethnic Studies; U25 Upper-Div Math or Science; UD3 Upper-Div Arts & Humanities; UD4 Upper-Div Social Sciences. Old lettered areas: A1=1C A2=1A A3=1B B1=5A B2=5B B3=5C B4=2 C1=3A C2=3B D1=4A D2=4B F=6. "arts" is 3A, "humanities" is 3B, "social science" is 4B; "upper division" picks the U* key.' },
        component: { type: 'string', enum: ['LEC', 'LAB', 'ACT', 'SEM'] },
        fits_my_schedule: { type: 'boolean', description: 'Only sections that do not clash with the student’s saved classes' },
        sort: { type: 'string', enum: ['rating', 'seats', 'easiest'], description: 'rating = best-rated professor first' },
        scope: { type: 'string', enum: ['ge_unmet', 'required'], description: 'ge_unmet = GE areas the student still needs; required = everything their major still requires' },
      },
    },
  },
  {
    name: 'open_class',
    description: 'Open one course’s page.',
    parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } },
  },
  {
    name: 'open_professor',
    description: 'Open one professor’s page.',
    parameters: { type: 'object', required: ['name'], properties: { name: { type: 'string' } } },
  },
  /* Phase 2, and they cost nothing to add here because the CLIENT resolves "my" — the model only
     names the intent, and the student's own device reads their own week. */
  { name: 'my_free', description: 'Show when the student is free.', parameters: { type: 'object', properties: { days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } } } } },
  { name: 'my_conflicts', description: 'Show time clashes in the student’s own schedule.', parameters: { type: 'object', properties: {} } },
  { name: 'my_day', description: 'The student’s own classes on a day.', parameters: { type: 'object', properties: { days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } }, rel: { type: 'string', enum: ['today', 'tomorrow'] } } } },
  { name: 'my_units', description: 'How many units the student is taking.', parameters: { type: 'object', properties: {} } },
  { name: 'my_professors', description: 'The professors teaching the student’s own classes, ranked by rating. For "which of my professors is best/worst rated", "who are my professors".', parameters: { type: 'object', properties: { order: { type: 'string', enum: ['desc', 'asc'], description: 'asc for lowest/worst first' } } } },
  { name: 'my_requirements', description: 'What the student still needs for their degree.', parameters: { type: 'object', properties: {} } },
  { name: 'prereqs', description: 'Whether the student has met a course’s prerequisites.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } } },
  { name: 'fit_pair', description: 'Whether two courses can be taken together this term.', parameters: { type: 'object', required: ['a', 'b'], properties: { a: { type: 'string' }, b: { type: 'string' } } } },
  { name: 'swap_section', description: 'Other sections of a class the student is already in.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' }, prefer: { type: 'string', enum: ['later', 'earlier'] } } } },
  { name: 'friends_took', description: 'Classes the student’s friends have already taken (their past classes), optionally only ones the student still needs, one course, or one subject. For "a class my friends took", "have my friends taken X".', parameters: { type: 'object', properties: { scope: { type: 'string', enum: ['ge_unmet', 'required'] }, course: { type: 'string' }, subject: { type: 'string' } } } },
  { name: 'friends_in', description: 'Which of the student’s friends are in a course.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } } },
  { name: 'when_registration', description: 'When registration opens.', parameters: { type: 'object', properties: {} } },
  /* 2026-09-25: the registration game plan. The CLIENT reads the student's own Plans A–C; the model
     only names which plan, if the student said one. */
  { name: 'game_plan', description: 'The order to register for the classes in one of the student’s plans, with a backup section for each. For "what do I register for first", "my game plan", "backups for plan B".', parameters: { type: 'object', properties: { plan: { type: 'string', enum: ['A', 'B', 'C'] } } } },
  { name: 'go_to', description: 'Open a screen of the app. ONLY when the student asks to open, find or change something on a screen ("where do I change my password" → account, "how do I import my schedule" → import schedule), never as a stand-in for an answer.', parameters: { type: 'object', required: ['where'], properties: { where: { type: 'string', enum: ['home', 'explore', 'explore professors', 'ge browser', 'find professor', 'schedule', 'my classes', 'week view', 'watchlist', 'watched professors', 'compare professors', 'planner', 'ledger', 'past classes', 'add past class', 'add past term', 'import schedule', 'share my schedule', 'friends', 'groups', 'messages', 'new message', 'add friend', 'my qr code', 'invite link', 'settings', 'appearance', 'account', 'privacy settings', 'about', 'edit profile', 'notifications', 'rate', 'my reviews', 'privacy policy', 'terms', 'community guidelines', 'security'] } } } },
  { name: 'help', description: 'What Hawk can do ("help", "what can you do").', parameters: { type: 'object', properties: {} } },
  { name: 'set_theme', description: 'Switch the app theme.', parameters: { type: 'object', required: ['theme'], properties: { theme: { type: 'string', enum: ['dark', 'light', 'cream'] } } } },
  { name: 'watch', description: 'Watch or stop watching a class, one section, or a professor (seat alerts, watchlist). "alert me when BUS4442 opens", "add X to my watchlist", "stop watching X".', parameters: { type: 'object', required: ['kind'], properties: { kind: { type: 'string', enum: ['class', 'section', 'professor'] }, course: { type: 'string' }, section: { type: 'string', description: 'section number, e.g. 2' }, name: { type: 'string', description: 'professor name' }, off: { type: 'boolean', description: 'true to stop watching' } } } },
  { name: 'open_section', description: 'One section of a course, e.g. "BUS4442-02", "BUS 4442 section 2".', parameters: { type: 'object', required: ['course', 'section'], properties: { course: { type: 'string' }, section: { type: 'string' } } } },
  { name: 'add_section', description: 'Add a class (optionally one section) to the student’s own classes. The student confirms in the app.', parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' }, section: { type: 'string' } } } },
  { name: 'rate_professor', description: 'Open the review form for a professor, or for the professor of one of the student’s courses. The student submits it.', parameters: { type: 'object', properties: { name: { type: 'string' }, course: { type: 'string' } } } },
  { name: 'draft_message', description: 'Open a chat with one of the student’s friends with a question typed in, about a course or professor. Never sends.', parameters: { type: 'object', required: ['friend'], properties: { friend: { type: 'string', description: 'the friend’s name as the student wrote it' }, course: { type: 'string' }, name: { type: 'string', description: 'a professor to ask about' } } } },
  { name: 'share', description: 'Send a class or a professor to a friend through the share sheet. The student picks who and sends.', parameters: { type: 'object', properties: { course: { type: 'string' }, name: { type: 'string', description: 'professor' }, friend: { type: 'string' } } } },
  { name: 'add_friend', description: 'Find a person to add as a friend.', parameters: { type: 'object', properties: { person: { type: 'string' } } } },
  { name: 'friend_profile', description: 'One friend’s current classes, past classes, or friends ("what is Maya taking", "Maya’s schedule").', parameters: { type: 'object', required: ['friend'], properties: { friend: { type: 'string' }, tab: { type: 'string', enum: ['classes', 'took', 'friends'] } } } },
  { name: 'professor_stats', description: 'A professor’s rating, number of ratings, would-take-again, hours, difficulty ("how hard is X", "would people take X again").', parameters: { type: 'object', required: ['name'], properties: { name: { type: 'string' } } } },
  { name: 'compare_professors', description: 'Compare two professors.', parameters: { type: 'object', required: ['a', 'b'], properties: { a: { type: 'string' }, b: { type: 'string' } } } },
  {
    name: 'build_term',
    description: 'Build complete class schedules for a term from the student’s constraints.',
    parameters: {
      type: 'object',
      properties: {
        units: { type: 'number', description: 'Target units, e.g. 15' },
        scope: { type: 'string', enum: ['ge_unmet', 'required'], description: 'Fill it from GE the student still needs, or everything their major still requires' },
        include: { type: 'array', items: { type: 'string' }, description: 'Course codes that must be in it' },
        days_off: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } },
        start_after: { type: 'string', description: 'HH:MM 24h, nothing earlier' },
        end_before: { type: 'string', description: 'HH:MM 24h, nothing later' },
        open_only: { type: 'boolean' },
        sort: { type: 'string', enum: ['rating', 'seats'] },
      },
    },
  },
  {
    name: 'cant_answer',
    description: 'Use when no other tool fits.',
    parameters: {
      type: 'object', required: ['reason'],
      properties: { reason: { type: 'string', enum: ['not_about_classes', 'needs_judgment', 'needs_private_data', 'ambiguous'] } },
    },
  },
];

export const SYSTEM = (term: string) =>
  `You route a Cal Poly student's question to one tool. Pick exactly one. The current term is ${term}. `
  + `Course codes are SUBJECT+NUMBER (BUS4442), sometimes with one letter after the number (CSC1001L is a lab, BUS3393A); keep that letter. `
  + `Write a code exactly as the student gave it: never turn an old 3-digit number (CSC101) into a different course. `
  + `Times are 24-hour. "Open" means seats available. `
  + `Time words: morning = end_before 12:00; afternoon = start_after 12:00; evening or night = start_after 17:00; early = end_before 10:00; `
  + `"no 8ams" = start_after 09:00; "sleep in" or "no early classes" = start_after 10:00; "done by 3" = end_before 15:00; "around 10" or "at 10" = at_time 10:00. `
  + `Days: MWF = Mo We Fr; TTh, TR or "tues thurs" = Tu Th. For search_sections, "not on Fridays" means days = the other weekdays (Mo Tu We Th); for build_term use days_off. `
  + `A day you cannot name from the words ("tomorrow", "this week") is left out of search_sections rather than guessed. `
  + `If the question is not about Cal Poly classes, sections, professors, the student's own schedule or plans, their friends, or using this app, `
  + `or it needs an opinion about which choice is better for them, call cant_answer. App requests (a screen, a setting, the theme, their account) are go_to or set_theme, not cant_answer. Questions about the student's own classes, day, units, `
  + `requirements, professors, friends or prerequisites have their own tools; answer them with those, not go_to. Never guess a course that was not named. `
  + `For a recommendation, use search_sections and fill EVERY constraint the student gave at once: `
  + `scope for "GE I still need" or "for my major", fits_my_schedule, days, times, open_only, sort. `
  + `To plan a whole term ("build me a schedule", "15 units no Fridays"), use build_term. What to register for first, or backups, is game_plan. `
  + `Actions (watch, add_section, rate_professor, draft_message, share, add_friend, set_theme) only OPEN things for the student to finish; use them when asked. `
  + `If EARLIER is given, the question may be a follow-up: keep those filters unless the student changes them. `
  + `Reply only with a tool call, never with text.`;

/* ------------------------------------------------------------------------------------------------
   THE PHONE APP'S MENU (2026-10-08). The phone sends `client: 'app'`; everyone else — the website's
   Hawk, the live phone build before this one — gets TOOLS and SYSTEM above, byte for byte, so
   nothing changes for a client that never asked.

   Why a second menu and not edits to the first: the misses Tate found ("who's free right now?"
   answered with HIS free time, "best professor for BUS 3431" answered with his own professors)
   were the model picking the closest tool on a menu that had no right one. The phone can answer
   four more things than the website can, so its menu names them; and every description below
   says what the tool is FOR, how students actually phrase it, and what it is NOT for — the
   confusable neighbour, named. The parameters are TOOLS' own (one schema, no drift); only the
   descriptions differ, plus go_to's places (the phone's screens) and set_theme (no cream).

   Descriptions are paid tokens on every call, but they sit in the cached prefix with the system
   prompt, so after the first call of a few minutes they cost a tenth.
   ------------------------------------------------------------------------------------------------ */
export const APP_PLACES = ['home', 'explore', 'explore professors', 'find professor', 'schedule', 'my classes', 'week view',
  'planner', 'past classes', 'ledger', 'friends', 'groups', 'messages', 'new message', 'add friend', 'my qr code', 'invite link',
  'settings', 'appearance', 'account', 'privacy settings', 'about', 'edit profile', 'notifications', 'rate', 'my reviews',
  'privacy policy', 'terms', 'community guidelines', 'security'];

const APP_DESC: Record<string, string> = {
  search_sections: 'Find sections this term by subject, course, days, times, open seats, GE area, mode, rating, or what the student '
    + 'still needs. E.g. "open BUS sections Tuesday after 2", "is bus 4442 open" (course + open_only), "csc classes mwf mornings", '
    + '"an arts GE", "a GE I still need that fits my week", "online stat classes", "a chill ge" (sort easiest). '
    + 'Not for: the best professor for one course (best_professor); whether one course fits a plan or my week (fits_plan).',
  open_class: 'Show one course\'s page when nothing else is asked about it. E.g. "bus 4442", "what is phil 3331", "tell me about stat 2170". '
    + 'Not for: is it open / seats (search_sections with open_only), its best professor (best_professor), prerequisites (prereqs), '
    + 'whether it fits (fits_plan).',
  open_professor: 'Show one professor by name when nothing else is asked. E.g. "professor Lee", "who is kurt voelker", "dr chance". '
    + 'Not for: is X good / how hard is X (professor_stats).',
  my_free: 'When the STUDENT THEMSELF is out of class, on a day or across the week. E.g. "when am I free monday", "my free time this week", '
    + '"do I have a break tuesday", "when am I free mwf". '
    + 'Not for: which FRIENDS are free ("who\'s free" — friends_free_now, free_with_friends).',
  my_conflicts: 'Time clashes among the student\'s own classes. E.g. "do any of my classes overlap", "am I double booked". '
    + 'Not for: whether a new course fits (fits_plan).',
  my_day: 'The student\'s own classes on one day, today or tomorrow. E.g. "what do I have today", "my classes tuesday", '
    + '"when is my first class tomorrow", "what\'s my next class", "when am I done monday". Not for: free time (my_free).',
  my_units: 'How many units the student is taking. E.g. "how many units am I taking", "am I full time".',
  my_professors: 'The professors of the student\'s OWN classes, ranked by rating. E.g. "who are my professors", '
    + '"which of my profs is rated highest", "my worst professor" (order asc). '
    + 'Not for: the best professor for a course (best_professor); one named professor (professor_stats).',
  my_requirements: 'What the student still needs for their degree. E.g. "what do I still need to graduate", "what GEs do I have left", '
    + '"degree progress". Not for: classes to take next term (build_term), a section search (search_sections).',
  prereqs: 'Whether the student can take a course yet (its prerequisites against their record). E.g. "can I take stat 2170", '
    + '"what are the prereqs for bus 4442", "am I allowed to take csc 1010". Not for: whether it fits their week (fits_plan).',
  fit_pair: 'Whether TWO named courses can both be taken this term without a clash. E.g. "can I take bus 3431 and bus 4401 together", '
    + '"do econ 2303 and stat 2170 overlap". Not for: one course against a plan or the student\'s week (fits_plan).',
  swap_section: 'Other sections of a course the student is ALREADY in that fit their week. E.g. "a later section of bus 3438", '
    + '"can I switch to an earlier stat 2170". Not for: a course they are not in (search_sections).',
  friends_took: 'Courses the student\'s friends have ALREADY TAKEN in past terms. E.g. "have any of my friends taken bus 4442", '
    + '"a GE my friends took". Not for: friends in a course NOW (friends_in).',
  friends_in: 'Which friends are in a course THIS term. E.g. "which friends are in bus 4442", "is anyone I know taking csc 1001", '
    + '"who\'s in stat 2170". Not for: friends who took it before (friends_took); who is free (friends_free_now).',
  when_registration: 'When registration opens. E.g. "when do I register", "when is round 1", "when can I sign up for spring classes".',
  game_plan: 'The order to register for the classes in one of the student\'s Plans A–C, with a backup section for each. '
    + 'E.g. "what do I register for first", "my game plan", "backups for plan B", "what should I grab first".',
  go_to: 'Open a screen of the app, ONLY when the student asks to open, find or change something on a screen. E.g. "where do I change '
    + 'my password" → account, "turn on dark mode" → appearance, "my qr code", "privacy settings". '
    + 'Not for: a question another tool answers — answer it instead of sending them to a screen; how something in '
    + 'TermChamp works or is it free, private or safe (app_help).',
  help: 'What Champ can do. E.g. "help", "what can you do", "what should I ask". '
    + 'Not for: what Champ does with their questions or where their information goes (app_help topic champ).',
  set_theme: 'Switch the app between light and dark. E.g. "dark mode", "switch to light mode".',
  watch: 'Watch or stop watching a course, one section, or a professor for seat alerts. E.g. "alert me when bus 4442 opens", '
    + '"watch section 2 of stat 2170", "stop watching phil 3331". Not for: adding it to a plan (add_section).',
  open_section: 'One section of a course. E.g. "bus 4442-02", "bus 4442 section 2".',
  add_section: 'Add a course (optionally one section) to a plan or the student\'s classes; the student confirms in the app. '
    + 'E.g. "add bus 4401 to my plan", "put stat 2170 section 1 in plan B". Not for: asking whether it fits (fits_plan).',
  rate_professor: 'Open the review form for a professor, or for the professor of one of the student\'s courses. '
    + 'E.g. "rate professor Lee", "review my bus 3431 professor".',
  draft_message: 'Open a chat with one friend with a question typed in, about a course or professor. Never sends. '
    + 'E.g. "ask Maya about bus 4442", "text Sky about professor Lee".',
  share: 'Send a course or a professor to a friend through the share sheet; the student picks who and sends. '
    + 'E.g. "share bus 4442 with Maya", "send professor Lee to Sky".',
  add_friend: 'Find a person to add as a friend. E.g. "add Jordan", "find my roommate on here".',
  friend_profile: 'One friend\'s classes this term, past classes, or friends. E.g. "what is Maya taking", "Maya\'s schedule", '
    + '"what has Sky taken before" (tab took), "who are Garrett\'s friends" (tab friends). '
    + 'Not for: when the student and that friend are both free (free_with_friends).',
  professor_stats: 'One NAMED professor\'s rating, number of ratings, would-take-again and difficulty. E.g. "is professor Lee good", '
    + '"how hard is kurt voelker", "would people take Beth Chance again", "is Lee good for bus 3431". '
    + 'Not for: the best professor for a course when no professor is named (best_professor).',
  compare_professors: 'Compare two named professors. E.g. "Lee or Chance", "who is better, X or Y".',
  build_term: 'Pick classes for a whole term from the student\'s constraints. E.g. "build me a schedule", "15 units no fridays", '
    + '"what should I take next semester". Not for: one course\'s fit (fits_plan).',
  cant_answer: 'Use when no other tool fits: not about Cal Poly classes, professors, schedules, plans, friends or this app; an opinion '
    + 'only the student can give; or too unclear to route.',
};

export const HELP_TOPICS = ['what_is', 'free', 'who_sees', 'ratings_anonymous', 'ratings_source', 'seats_source', 'add_class',
  'plans', 'seat_alerts', 'degree_report', 'add_friends', 'block_report', 'delete_account', 'champ', 'dark_mode', 'contact'];

const APP_NEW: any[] = [
  { name: 'friends_free_now', description: 'Which of the student\'s FRIENDS are out of class RIGHT NOW. E.g. "who\'s free", '
      + '"who\'s free right now", "anyone free rn", "who can hang out", "which friends aren\'t in class". '
      + 'Not for: when the student themself is free (my_free); friends free on a day or with one friend (free_with_friends).',
    parameters: { type: 'object', properties: {} } },
  { name: 'free_with_friends', description: 'When the student AND their friends are out of class at the same time, on a day or with '
      + 'one named friend. E.g. "who\'s free with me tuesday", "who\'s free tomorrow", "when are Maya and I both free", '
      + '"when can I get lunch with Sky". Not for: right now (friends_free_now); the student alone (my_free).',
    parameters: { type: 'object', properties: {
      friend: { type: 'string', description: 'one friend\'s name as the student wrote it, if they named one' },
      days: { type: 'array', items: { type: 'string', enum: ['Mo', 'Tu', 'We', 'Th', 'Fr'] } },
      rel: { type: 'string', enum: ['today', 'tomorrow'] } } } },
  { name: 'best_professor', description: 'The best-rated professors teaching ONE course this term, best first. E.g. '
      + '"best professor for bus 3431", "who should I take for stat 2170", "which prof is good for econ 2303", '
      + '"best teacher for biz 3431", "who\'s the goat for phil 3331". '
      + 'Not for: the student\'s own professors (my_professors); a professor the student named (professor_stats).',
    parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' } } } },
  { name: 'fits_plan', description: 'Whether ONE course fits one of the student\'s Plans A–C, or their current classes (plan "mine"), '
      + 'without a time clash. E.g. "does bus 4401 fit my plan A", "can I fit stat 2170 into my schedule", '
      + '"would econ 2303 work with my week", "is there room for phil 3331 in plan b". '
      + 'Not for: two courses together (fit_pair); adding it (add_section).',
    parameters: { type: 'object', required: ['course'], properties: { course: { type: 'string' },
      plan: { type: 'string', enum: ['A', 'B', 'C', 'mine'], description: 'mine = the student\'s current classes ("my schedule", "my week"); leave out if no plan was named' } } } },
  /* 2026-10-11: questions about TermChamp itself. The model only picks a topic; the phone shows that topic's
     fixed answer (HELP in app/index.html), so nothing the model writes is ever read as a fact about the app. */
  { name: 'app_help', description: 'A question about TermChamp ITSELF — what it is, its rules, privacy, how to do something in '
      + 'it, or what Champ does with questions. Pick the CLOSEST topic even when the words are different. '
      + 'E.g. "is termchamp free", "can my professor see my review", "what does champ do with my questions", '
      + '"how do I add friends", "where do the seat numbers come from". '
      + 'Not for: a class, professor, seat count, schedule or friend question (the other tools); adding a NAMED person '
      + '(add_friend) or a NAMED course (add_section); opening a screen by name (go_to); "turn on dark mode" '
      + '(set_theme); what Champ can answer (help).',
    parameters: { type: 'object', required: ['topic'], properties: { topic: { type: 'string', enum: HELP_TOPICS,
      description: 'what_is: what TermChamp is, who made it, is it official. free: cost, ads, selling data. '
        + 'who_sees: who can see their schedule, classes or plans, is it private. ratings_anonymous: are reviews '
        + 'anonymous, can a professor or friends see who wrote one. ratings_source: where ratings come from. '
        + 'seats_source: where seat numbers come from, how up to date they are. add_class: how to add a class. '
        + 'plans: what Plans A, B and C are. seat_alerts: how watching and seat notifications work. '
        + 'degree_report: uploading the Degree Progress Report (DPR), where to get it, is it safe. '
        + 'add_friends: how to add or find friends. block_report: blocking or reporting someone or something. '
        + 'delete_account: deleting the account and what happens. champ: what Champ does, where their questions '
        + 'and information go, does Champ see their data. dark_mode: is there dark mode, changing the look. '
        + 'contact: contacting TermChamp, support, a bug, feedback.' } } } },
];
export const APP_NEW_NAMES = APP_NEW.map((t) => t.name);

export const APP_TOOLS = (() => {
  const base = TOOLS.filter((t) => t.name !== 'cant_answer').map((t) => {
    let parameters: any = t.parameters;
    if (t.name === 'go_to') parameters = { ...t.parameters, properties: { where: { type: 'string', enum: APP_PLACES } } };
    if (t.name === 'set_theme') parameters = { ...t.parameters, properties: { theme: { type: 'string', enum: ['dark', 'light'] } } };
    return { name: t.name, description: APP_DESC[t.name] ?? t.description, parameters };
  });
  const cant = TOOLS.find((t) => t.name === 'cant_answer')!;
  return [...APP_NEW, ...base, { ...cant, description: APP_DESC.cant_answer }];
})();

export const APP_SYSTEM = (term: string) =>
  `You route a Cal Poly student's question in the TermChamp phone app to exactly one tool. The current term is ${term}. `
  + `FIRST decide who the question is about. "I", "me", "my" is the student. "Who", "anyone", "friends" or a person's name is other `
  + `people. "Who's free" is friends_free_now (free_with_friends when a day or a friend is named); "when am I free" is my_free. `
  + `"Best professor for X" or "who should I take for X" is best_professor; "my professors" is my_professors; a professor the `
  + `student names is professor_stats. "Does X fit my plan A / my schedule" is fits_plan; two courses together is fit_pair. `
  + `"Is X open" or seats in X is search_sections with course and open_only. `
  + `Course codes are SUBJECT+NUMBER with no space (BUS4442), sometimes with one letter after the number (CSC1001L, BUS3393A); keep `
  + `that letter, and never turn an old 3-digit number (CSC101) into a different course. Students say "biz" or "business" for BUS, `
  + `"stats" STAT, "econ" ECON, "comp sci" or "cs" CSC, "psych" PSY, "kin" KINE, "poli sci" POLS, "comm" COMS, "phil" PHIL, `
  + `"bio" BIO, "chem" CHEM, "english" ENGL, "history" HIST, "physics" PHYS, "math" MATH: write the real code. Never make up a `
  + `subject code you are not sure of (MTH, MKT, WINE are not Cal Poly subjects): leave subject out instead. `
  + `Times are 24-hour. "Open" means seats available. `
  + `Time words: morning = end_before 12:00; afternoon = start_after 12:00; evening or night = start_after 17:00; early = end_before 10:00; `
  + `"no 8ams" = start_after 09:00; "sleep in" or "no early classes" = start_after 10:00; "done by 3" = end_before 15:00; "around 10" or "at 10" = at_time 10:00. `
  + `Days: MWF = Mo We Fr; TTh, TR or "tues thurs" = Tu Th. For search_sections, "not on Fridays" means days = the other weekdays `
  + `(Mo Tu We Th); for build_term use days_off. "Today" and "tomorrow" are rel where a tool has it; otherwise leave the day out `
  + `rather than guess. Never invent a course, a plan, a day or a person the student did not say. `
  + `If the question is not about Cal Poly classes, sections, professors, the student's schedule or plans, their friends, or using `
  + `this app, or it asks for an opinion only the student can give ("is this class worth it for me"), call cant_answer — but `
  + `comparing two named professors is compare_professors. App requests (a screen, a `
  + `setting, the theme, their account) are go_to or set_theme. A question ABOUT TermChamp or Champ — what it is, is it `
  + `free or private, who sees what, where ratings or seats come from, how to do something in it, what happens to `
  + `their questions — is app_help with the closest topic, however it is worded; never answer it in words. Actions (watch, add_section, rate_professor, draft_message, share, `
  + `add_friend) only OPEN things for the student to finish. `
  + `If EARLIER is given, the question may be a follow-up: keep those filters unless the student changes them. `
  + `Reply only with a tool call, never with text.`;

/* The one place a route's prompt and menu are chosen, for the function AND for the model scorer —
   so the golden set is scored on exactly what students get. */
export function routeSpec(client: string, term: string, q: string, prev = ''): Spec {
  const app = client === 'app';
  return { system: app ? APP_SYSTEM(term) : SYSTEM(term), tools: app ? APP_TOOLS : TOOLS,
           user: prev ? `EARLIER: ${prev}\nQUESTION: ${q}` : q };
}

/* ------------------------------------------------------------------------------------------------
   EXPLAIN — the second job, and the only place the model writes words a student reads.

   It is handed the rows the student is ALREADY looking at and asked for one or two sentences
   pointing at the best one and why. It is never asked a question it could answer from its own
   knowledge. Its sentences are checked twice before anyone reads them — here, and again in the
   browser against the rows on screen — and any course code, number or name that is not in those
   rows drops the whole sentence. A missing explanation costs nothing; a wrong one is the product
   stating a fact it cannot back.
   ------------------------------------------------------------------------------------------------ */
export const EXPLAIN_SYSTEM =
  `You help a Cal Poly student act on the search results TermChamp is showing them. `
  + `Write one or two short sentences, at most 45 words, in plain friendly English. `
  + `Use ONLY facts in ROWS. Every course code, time, name and number you write must appear in ROWS. `
  + `Do not describe how a professor teaches; you may mention their rating. `
  + `Point to the row that best answers the question and say why using its fields: fits their week, `
  + `rating, open seats, time, GE area. If the best-rated row does not fit their week, say so. `
  + `Reply only with the explain tool.`;

export const EXPLAIN_TOOLS = [{
  name: 'explain',
  description: 'The sentence or two to show the student.',
  parameters: { type: 'object', required: ['text'], properties: { text: { type: 'string' } } },
}];

export const ROW_KEYS = ['code', 'title', 'when', 'prof', 'rating', 'seats', 'tag', 'fits', 'yours'];
export function cleanRows(raw: any): Record<string, unknown>[] {
  if (!Array.isArray(raw)) return [];
  return raw.slice(0, 8).map((r: any) => {
    const o: Record<string, unknown> = {};
    for (const k of ROW_KEYS) {
      const v = r?.[k];
      if (typeof v === 'string') o[k] = v.slice(0, 90);
      else if (typeof v === 'number' || typeof v === 'boolean') o[k] = v;
    }
    return o;
  }).filter((o) => Object.keys(o).length);
}

/* The server's half of the grounding check. Every course code in the sentence must be in the rows. */
export function groundedText(text: string, rows: Record<string, unknown>[]): string | null {
  const t = String(text || '').replace(/\s+/g, ' ').trim();
  if (!t || t.length > 320 || /https?:|www\./i.test(t)) return null;
  const hay = JSON.stringify(rows).toUpperCase();
  const codes = t.toUpperCase().match(/\b[A-Z]{2,4}\s?\d{3,4}[A-Z]?(?:-\d+)?\b/g) || [];
  for (const c of codes) {
    const bare = c.replace(/\s+/, ' ').replace(/-\d+$/, '');
    if (!hay.includes(bare)) return null;
  }
  return t;
}

/* ------------------------------------------------------------------------------------------------
   Vendor adapters.

   THE MODEL STRING PICKS THE VENDOR: "openai:gpt-5.6-luna", "anthropic:claude-haiku-4.5",
   "gemini:gemini-2.5-flash". One config row therefore chooses both, and swapping vendors is an
   UPDATE rather than a deploy — which matters, because the build plan's own conclusion is that the
   golden set picks the model, and that answer is not known until it has been run.
   ------------------------------------------------------------------------------------------------ */
/* The status alone — "vendor_400" — says a request was refused and nothing about why, which is
   what turned a one-line fix into a round trip through a redeploy. The vendor's own message is
   short, has no secret in it, and names the offending field. It is trimmed to a size the log
   column holds. */
export function vendorErr(status: number, j: any): string {
  const msg = j?.error?.message ?? j?.error?.status ?? j?.message ?? '';
  return ('vendor_' + status + (msg ? ': ' + String(msg).replace(/\s+/g, ' ').slice(0, 160) : ''));
}

export function splitModel(raw: string): { vendor: string; model: string } {
  const i = raw.indexOf(':');
  if (i < 0) return { vendor: 'openai', model: raw };
  return { vendor: raw.slice(0, i).toLowerCase(), model: raw.slice(i + 1) };
}

/* TWO KINDS OF CLAUDE, AND THE REQUEST HAS TO KNOW WHICH.

   The Claude 5 generation (Fable, Mythos, Opus 5, Sonnet 5) thinks by default and cannot be told
   not to: `thinking.type.disabled` is refused outright — the API's own words, read off a 400 on
   2026-09-24. What it accepts is `adaptive` thinking steered by `output_config.effort`, and with
   thinking on it also refuses `temperature: 0` and a FORCED tool choice. So those models get
   `effort: low` (the doc: "at lower levels, Claude can skip thinking entirely for simpler
   problems"), `tool_choice: auto`, and the system prompt does the forcing — a reply with no tool
   call is caught by validate() and becomes cant_answer.

   Haiku 4.5 is the other way round: no adaptive mode, no effort parameter, and it takes
   `temperature: 0` with `tool_choice: any` exactly as the plan assumed. The classic shape.

   Haiku 5.5 (2026-10-11) is a third shape: adaptive by default like the Claude 5 models, but it
   ACCEPTS `thinking: {type: 'disabled'}` at its default effort. Off, it is a plain fast router again,
   so the tool is forced as on Haiku 4.5. Temperature is left out: a Claude 5 model has refused it
   before, and the forced tool plus validate() are what keep the answer in shape.

   The two are told apart by name. `tokens_out` in assistant_runs is what proves the effort
   setting is actually keeping thinking small — the doc calls effort "a behavioral signal, not a
   strict token budget", which is a sentence to measure rather than trust. */
export type Spec = { system: string; tools: any[]; user: string; force?: string };

export function anthropicBody(model: string, spec: Spec) {
  const adaptive = /fable|mythos|opus-5|sonnet-5/.test(model);
  const noThink = /haiku-5/.test(model);
  const shared = {
    model, max_tokens: MAX_OUT,
    system: [{ type: 'text', text: spec.system, cache_control: { type: 'ephemeral' } }],
    tools: spec.tools.map((t) => ({ name: t.name, description: t.description, input_schema: t.parameters })),
    messages: [{ role: 'user', content: spec.user }],
  };
  if (adaptive) {
    return {
      ...shared,
      /* Thinking tokens count against max_tokens. 200 would cut a thought off before the tool
         call and every answer would arrive as cant_answer. 800 is headroom, not a budget — the
         cap and tokens_out are what bound it. */
      max_tokens: 800,
      thinking: { type: 'adaptive' },
      output_config: { effort: 'low' },
      tool_choice: { type: 'auto' },
    };
  }
  const forced = spec.force ? { type: 'tool', name: spec.force } : { type: 'any' };
  if (noThink) return { ...shared, thinking: { type: 'disabled' }, tool_choice: forced };
  return { ...shared, temperature: 0, tool_choice: forced };
}

export async function callVendor(vendor: string, model: string, key: string, spec: Spec, signal: AbortSignal) {
  if (vendor === 'anthropic') {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST', signal,
      headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify(anthropicBody(model, spec)),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(vendorErr(r.status, j));
    const block = (j.content || []).find((c: any) => c.type === 'tool_use');
    const text = (j.content || []).filter((c: any) => c.type === 'text').map((c: any) => c.text).join(' ').trim();
    return {
      name: block?.name, args: block?.input ?? {}, text,
      /* input_tokens EXCLUDES the tokens written to the cache; those arrive in
         cache_creation_input_tokens and are billed at 1.25x input. Left out, the estimate the daily
         cap runs on was missing the whole prefix on every first call. */
      usage: {
        in: (j.usage?.input_tokens ?? 0) + Math.round((j.usage?.cache_creation_input_tokens ?? 0) * 1.25),
        cached: j.usage?.cache_read_input_tokens ?? 0,
        out: j.usage?.output_tokens ?? 0,
      },
    };
  }

  if (vendor === 'gemini') {
    const r = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`,
      {
        method: 'POST', signal, headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: spec.system }] },
          contents: [{ role: 'user', parts: [{ text: spec.user }] }],
          tools: [{ functionDeclarations: spec.tools }],
          toolConfig: { functionCallingConfig: { mode: 'ANY' } },
          generationConfig: { temperature: 0, maxOutputTokens: MAX_OUT },
        }),
      },
    );
    const j = await r.json();
    if (!r.ok) throw new Error(vendorErr(r.status, j));
    const part = (j.candidates?.[0]?.content?.parts || []).find((p: any) => p.functionCall);
    return {
      name: part?.functionCall?.name, args: part?.functionCall?.args ?? {},
      usage: { in: j.usageMetadata?.promptTokenCount ?? 0, cached: j.usageMetadata?.cachedContentTokenCount ?? 0, out: j.usageMetadata?.candidatesTokenCount ?? 0 },
    };
  }

  // default: OpenAI chat completions with forced tool choice
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST', signal,
    headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` },
    body: JSON.stringify({
      model, temperature: 0, max_tokens: MAX_OUT,
      tools: spec.tools.map((t) => ({ type: 'function', function: t })),
      tool_choice: 'required',
      messages: [{ role: 'system', content: spec.system }, { role: 'user', content: spec.user }],
    }),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(vendorErr(r.status, j));
  const call = j.choices?.[0]?.message?.tool_calls?.[0];
  let args = {};
  try { args = call ? JSON.parse(call.function.arguments || '{}') : {}; } catch (_) { args = {}; }
  return {
    name: call?.function?.name, args,
    usage: { in: j.usage?.prompt_tokens ?? 0, cached: j.usage?.prompt_tokens_details?.cached_tokens ?? 0, out: j.usage?.completion_tokens ?? 0 },
  };
}

/* Keyed on the EXACT API model id, because that is what the config row holds. The first draft
   keyed on marketing names — 'claude-haiku-4.5' — which matched nothing, so every real model fell
   through to UNKNOWN_RATE, and UNKNOWN_RATE was set below Fable's actual price. The cap would have
   counted Fable at half its cost and tripped late. Prices per million tokens, read from
   platform.claude.com/docs/en/about-claude/pricing on 2026-09-23; re-check when a model changes. */
export const RATES: Record<string, [number, number, number]> = {   // [in, cache read, out]
  'claude-fable-5-1':          [10.00, 0.25, 50.00],
  'claude-opus-5':             [5.00, 0.50, 25.00],
  'claude-sonnet-5':           [2.00, 0.20, 10.00],
  'claude-opus-5-5':           [4.00, 0.20, 20.00],
  'claude-sonnet-5-5':         [2.00, 0.10, 10.00],
  'claude-haiku-5-5':          [0.10, 0.01, 0.50],     // prompts up to 100K tokens (2026-10-11); ours are far under
  'claude-haiku-4-5-20251001': [1.00, 0.10, 5.00],
  'claude-haiku-4-5':          [1.00, 0.10, 5.00],
  'gpt-5.6-luna':              [0.20, 0.02, 1.20],
  'gemini-2.5-flash':          [0.075, 0.075, 0.30],
  'gemini-3.1-flash-lite':     [0.25, 0.025, 1.50],
};
/* At or above the priciest model this table knows. A model this table has not heard of must never
   be counted cheaper than one it has. */
export const UNKNOWN_RATE: [number, number, number] = [10.00, 1.00, 50.00];

export function estimateUsd(model: string, u: { in: number; cached: number; out: number }) {
  const [ri, rc, ro] = RATES[model] ?? UNKNOWN_RATE;
  const fresh = Math.max(0, (u.in ?? 0) - (u.cached ?? 0));
  return (fresh * ri + (u.cached ?? 0) * rc + (u.out ?? 0) * ro) / 1_000_000;
}

/* ------------------------------------------------------------------------------------------------
   Validation. The model's output is never trusted to be well-formed — anything that does not match
   the schema exactly becomes cant_answer rather than reaching the client as a half-filled filter.
   ------------------------------------------------------------------------------------------------ */
export const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;
export const DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
export const MODES = ['in_person', 'hybrid', 'async', 'sync_online'];
export const COMPONENTS = ['LEC', 'LAB', 'ACT', 'SEM'];
export const REASONS = ['not_about_classes', 'needs_judgment', 'needs_private_data', 'ambiguous'];
export const NAMES = TOOLS.map((t) => t.name).concat(APP_NEW_NAMES);

export function cantAnswer(reason = 'ambiguous') {
  return { tool: 'cant_answer', args: { reason } };
}

export function validate(name: string | undefined, raw: any) {
  if (!name || !NAMES.includes(name)) return cantAnswer();
  const a = (raw && typeof raw === 'object') ? raw : {};

  if (name === 'cant_answer') {
    return cantAnswer(REASONS.includes(a.reason) ? a.reason : 'ambiguous');
  }
  if (name === 'open_class') {
    const c = String(a.course ?? '').toUpperCase().replace(/\s+/g, '');
    if (!/^[A-Z]{2,4}\d{3,4}[A-Z]?$/.test(c)) return cantAnswer();
    return { tool: 'open_class', args: { course: c } };
  }
  if (name === 'open_professor') {
    const n = String(a.name ?? '').trim().slice(0, 80);
    if (!n) return cantAnswer();
    return { tool: 'open_professor', args: { name: n } };
  }
  if (name === 'my_professors') {
    return { tool: 'my_professors', args: a.order === 'asc' ? { order: 'asc' } : {} };
  }
  if (name === 'my_conflicts' || name === 'my_units' || name === 'my_requirements' || name === 'when_registration') {
    return { tool: name, args: {} };
  }
  if (name === 'game_plan') {
    const p = String(a.plan ?? '').toUpperCase();
    return { tool: 'game_plan', args: ['A', 'B', 'C'].includes(p) ? { plan: p } : {} };
  }
  const course = (v: any) => {
    const c = String(v ?? '').toUpperCase().replace(/\s+/g, '');
    return /^[A-Z]{2,4}\d{3,4}[A-Z]?$/.test(c) ? c : null;
  };
  if (name === 'friends_took') {
    const out: Record<string, unknown> = {};
    if (a.scope === 'ge_unmet' || a.scope === 'required') out.scope = a.scope;
    const c = course(a.course); if (c) out.course = c;
    if (typeof a.subject === 'string' && /^[A-Za-z]{2,4}$/.test(a.subject.trim())) out.subject = a.subject.trim().toUpperCase();
    return { tool: 'friends_took', args: out };
  }
  const person = (v: any) => { const t = String(v ?? '').replace(/[^\p{L}\p{M}' .-]/gu, '').trim().slice(0, 60); return t || null; };
  const secNo = (v: any) => { const n = parseInt(String(v ?? ''), 10); return n >= 1 && n <= 99 ? String(n) : null; };
  if (name === 'help') return { tool: 'help', args: {} };
  if (name === 'set_theme') {
    return ['dark', 'light', 'cream'].includes(a.theme) ? { tool: 'set_theme', args: { theme: a.theme } } : cantAnswer();
  }
  if (name === 'watch') {
    const out: Record<string, unknown> = {};
    const c = course(a.course), n = person(a.name), sec = secNo(a.section);
    if (a.kind === 'professor' && n) { out.kind = 'professor'; out.name = n; }
    else if (c && sec && a.kind !== 'class') { out.kind = 'section'; out.course = c; out.section = sec; }
    else if (c) { out.kind = 'class'; out.course = c; }
    else return cantAnswer();
    if (a.off === true) out.off = true;
    return { tool: 'watch', args: out };
  }
  if (name === 'open_section') {
    const c = course(a.course), sec = secNo(a.section);
    return c && sec ? { tool: 'open_section', args: { course: c, section: sec } } : cantAnswer();
  }
  if (name === 'add_section') {
    const c = course(a.course), sec = secNo(a.section);
    if (!c) return cantAnswer();
    return { tool: 'add_section', args: sec ? { course: c, section: sec } : { course: c } };
  }
  if (name === 'rate_professor') {
    const out: Record<string, unknown> = {};
    const n = person(a.name), c = course(a.course);
    if (n) out.name = n; if (c) out.course = c;
    return Object.keys(out).length ? { tool: 'rate_professor', args: out } : { tool: 'go_to', args: { where: 'rate' } };
  }
  if (name === 'draft_message') {
    const f = person(a.friend); if (!f) return cantAnswer();
    const out: Record<string, unknown> = { friend: f };
    const c = course(a.course), n = person(a.name);
    if (c) out.course = c; else if (n) out.name = n;
    return { tool: 'draft_message', args: out };
  }
  if (name === 'share') {
    const c = course(a.course), n = person(a.name), f = person(a.friend);
    if (!c && !n) return cantAnswer();
    const out: Record<string, unknown> = c ? { course: c } : { name: n };
    if (f) out.friend = f;
    return { tool: 'share', args: out };
  }
  if (name === 'add_friend') { const p = person(a.person); return { tool: 'add_friend', args: p ? { person: p } : {} }; }
  if (name === 'friend_profile') {
    const f = person(a.friend); if (!f) return cantAnswer();
    return { tool: 'friend_profile', args: { friend: f, tab: ['classes', 'took', 'friends'].includes(a.tab) ? a.tab : 'classes' } };
  }
  if (name === 'professor_stats') { const n = person(a.name); return n ? { tool: 'professor_stats', args: { name: n } } : cantAnswer(); }
  if (name === 'compare_professors') {
    const x = person(a.a), y = person(a.b);
    return x && y ? { tool: 'compare_professors', args: { a: x, b: y } } : cantAnswer();
  }
  if (name === 'prereqs' || name === 'friends_in') {
    const c = course(a.course); if (!c) return cantAnswer();
    return { tool: name, args: { course: c } };
  }
  if (name === 'swap_section') {
    const c = course(a.course); if (!c) return cantAnswer();
    const out: Record<string, unknown> = { course: c };
    if (a.prefer === 'later' || a.prefer === 'earlier') out.prefer = a.prefer;
    return { tool: 'swap_section', args: out };
  }
  if (name === 'fit_pair') {
    const x = course(a.a), y = course(a.b);
    if (!x || !y || x === y) return cantAnswer();
    return { tool: 'fit_pair', args: { a: x, b: y } };
  }
  if (name === 'my_day') {
    const out: Record<string, unknown> = {};
    if (a.rel === 'today' || a.rel === 'tomorrow') out.rel = a.rel;
    else if (Array.isArray(a.days)) { const d = a.days.filter((x: any) => DAYS.includes(x)); if (d.length) out.days = d; }
    return { tool: 'my_day', args: out };
  }
  if (name === 'build_term') {
    const out: Record<string, unknown> = {};
    if (typeof a.units === 'number' && a.units >= 3 && a.units <= 24) out.units = Math.round(a.units);
    if (a.scope === 'ge_unmet' || a.scope === 'required') out.scope = a.scope;
    if (Array.isArray(a.include)) { const inc = a.include.map(course).filter(Boolean).slice(0, 6); if (inc.length) out.include = inc; }
    if (Array.isArray(a.days_off)) { const d = a.days_off.filter((x: any) => ['Mo', 'Tu', 'We', 'Th', 'Fr'].includes(x)); if (d.length) out.days_off = d; }
    for (const k of ['start_after', 'end_before']) if (typeof a[k] === 'string' && HHMM.test(a[k])) out[k] = a[k];
    if (typeof a.open_only === 'boolean') out.open_only = a.open_only;
    if (a.sort === 'rating' || a.sort === 'seats') out.sort = a.sort;
    return { tool: 'build_term', args: out };
  }
  if (name === 'go_to') {
    const PLACES = ['home', 'explore', 'explore professors', 'ge browser', 'find professor', 'schedule', 'my classes', 'week view', 'watchlist', 'watched professors', 'compare professors', 'planner', 'ledger', 'past classes', 'add past class', 'add past term', 'import schedule', 'share my schedule', 'friends', 'groups', 'messages', 'new message', 'add friend', 'my qr code', 'invite link', 'settings', 'appearance', 'account', 'privacy settings', 'about', 'edit profile', 'notifications', 'rate', 'my reviews', 'privacy policy', 'terms', 'community guidelines', 'security'];
    const w = String(a.where ?? '').toLowerCase().trim();
    if (!PLACES.includes(w)) return cantAnswer();
    return { tool: 'go_to', args: { where: w } };
  }
  if (name === 'my_free') {
    const d = Array.isArray(a.days) ? a.days.filter((x: any) => DAYS.includes(x)) : [];
    return { tool: 'my_free', args: d.length ? { days: d } : {} };
  }

  /* The phone's own (2026-10-08; app_help 2026-10-11). Only the phone's menu offers them. */
  if (name === 'friends_free_now') return { tool: 'friends_free_now', args: {} };
  if (name === 'free_with_friends') {
    const out: Record<string, unknown> = {};
    const f = person(a.friend); if (f) out.friend = f;
    if (a.rel === 'today' || a.rel === 'tomorrow') out.rel = a.rel;
    else if (Array.isArray(a.days)) { const d = a.days.filter((x: any) => ['Mo', 'Tu', 'We', 'Th', 'Fr'].includes(x)); if (d.length) out.days = d; }
    return { tool: 'free_with_friends', args: out };
  }
  if (name === 'best_professor') {
    const c = course(a.course); if (!c) return cantAnswer();
    return { tool: 'best_professor', args: { course: c } };
  }
  if (name === 'app_help') return HELP_TOPICS.includes(a.topic) ? { tool: 'app_help', args: { topic: a.topic } } : cantAnswer();
  if (name === 'fits_plan') {
    const c = course(a.course); if (!c) return cantAnswer();
    const p = String(a.plan ?? '').trim().replace(/^plan\s*/i, ''), P = p.toLowerCase() === 'mine' ? 'mine' : p.toUpperCase();
    return { tool: 'fits_plan', args: ['A', 'B', 'C', 'mine'].includes(P) ? { course: c, plan: P } : { course: c } };
  }

  // search_sections — copy only what is well-formed, drop the rest silently rather than guess
  const out: Record<string, unknown> = {};
  if (typeof a.subject === 'string' && /^[A-Za-z]{2,4}$/.test(a.subject)) out.subject = a.subject.toUpperCase();
  if (typeof a.course === 'string') {
    const c = a.course.toUpperCase().replace(/\s+/g, '');
    if (/^[A-Z]{2,4}\d{3,4}[A-Z]?$/.test(c)) out.course = c;
  }
  if (Array.isArray(a.days)) {
    const d = a.days.filter((x: any) => DAYS.includes(x));
    if (d.length) out.days = d;
  }
  for (const k of ['at_time', 'start_after', 'end_before']) {
    if (typeof a[k] === 'string' && HHMM.test(a[k])) out[k] = a[k];
  }
  if (typeof a.open_only === 'boolean') out.open_only = a.open_only;
  if (typeof a.fits_my_schedule === 'boolean') out.fits_my_schedule = a.fits_my_schedule;
  if (typeof a.min_rating === 'number' && a.min_rating >= 1 && a.min_rating <= 5) out.min_rating = a.min_rating;
  if (MODES.includes(a.instruction_mode)) out.instruction_mode = a.instruction_mode;
  if (COMPONENTS.includes(a.component)) out.component = a.component;
  if (a.sort === 'rating' || a.sort === 'seats' || a.sort === 'easiest') out.sort = a.sort;
  if (typeof a.ge_area === 'string' && /^(1[ABC]|[2-6][ABC]?|UD[34]|U25|USCP|GWR)$/i.test(a.ge_area.replace(/\s+/g, ''))) out.ge_area = a.ge_area.replace(/\s+/g, '').toUpperCase();
  if (a.scope === 'ge_unmet' || a.scope === 'required') out.scope = a.scope;

  /* A search with nothing in it is not a search. It is the model having produced the right tool
     name and no usable arguments, which is a failure to understand, not an instruction to show
     every class at Cal Poly. */
  if (!Object.keys(out).length) return cantAnswer();
  return { tool: 'search_sections', args: out };
}

/* ------------------------------------------------------------------------------------------------ */
