#!/usr/bin/env python3
r"""The phone app gets its own menu in the `ask` function (Tate, 2026-10-08).

Run on the ask function as fixed 2026-09-26 (shared.ts md5 44c2ecdf5605, index.ts 3e9b8af43208).
Edits supabase/functions/ask/shared.ts and supabase/functions/ask/index.ts.

Tate's screenshots: "Who's free right now?" answered with HIS free week; "best professor for BUS 3431"
answered with his own professors. The model had picked the closest tool on a menu with no right one.

  * The phone sends `client: 'app'` (patch champ-tools-2026-10-08.py) and gets APP_TOOLS + APP_SYSTEM.
    Everyone else — the website's Hawk, the live phone build — gets TOOLS + SYSTEM byte for byte.
  * Four new tools only the phone can answer: friends_free_now, free_with_friends, best_professor,
    fits_plan.
  * Every phone tool's description says what it is for, how students phrase it ("E.g. …") and what
    it is NOT for, naming the confusable neighbour. Parameters are TOOLS' own, so one schema.
  * routeSpec() picks the prompt and menu for the function AND the model scorer, so the golden set is
    scored on exactly what students get.
  * validate() knows the four new tools.
"""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
SH = ROOT / 'supabase' / 'functions' / 'ask' / 'shared.ts'
IX = ROOT / 'supabase' / 'functions' / 'ask' / 'index.ts'
s = SH.read_text()
ix = IX.read_text()


def rep(src, a, b, n=1, what='shared.ts'):
    c = src.count(a)
    if c != n:
        sys.exit(f'ask-app-menu: expected {n} of {a[:80]!r} in {what}, found {c}')
    return src.replace(a, b)


APP_BLOCK = r"""/* ------------------------------------------------------------------------------------------------
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
    + 'my password" → account, "turn on dark mode" → appearance, "my qr code", "how do I block someone" → privacy settings. '
    + 'Not for: a question another tool answers — answer it instead of sending them to a screen.',
  help: 'What Champ can do. E.g. "help", "what can you do", "what should I ask".',
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
  + `setting, the theme, their account) are go_to or set_theme. Actions (watch, add_section, rate_professor, draft_message, share, `
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

"""

VALID_BLOCK = r"""  /* The phone's four (2026-10-08). Only the phone's menu offers them. */
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
  if (name === 'fits_plan') {
    const c = course(a.course); if (!c) return cantAnswer();
    const p = String(a.plan ?? '').trim().replace(/^plan\s*/i, ''), P = p.toLowerCase() === 'mine' ? 'mine' : p.toUpperCase();
    return { tool: 'fits_plan', args: ['A', 'B', 'C', 'mine'].includes(P) ? { course: c, plan: P } : { course: c } };
  }

"""

EXPLAIN_HEAD = """/* ------------------------------------------------------------------------------------------------
   EXPLAIN — the second job"""
s = rep(s, EXPLAIN_HEAD, APP_BLOCK + EXPLAIN_HEAD)
s = rep(s, "export const NAMES = TOOLS.map((t) => t.name);", "export const NAMES = TOOLS.map((t) => t.name).concat(APP_NEW_NAMES);")
s = rep(s, "  // search_sections — copy only", VALID_BLOCK + "  // search_sections — copy only")

ix = rep(ix, "  splitModel, callVendor, estimateUsd, validate, type Spec,", "  splitModel, callVendor, estimateUsd, validate, routeSpec, type Spec,", what='index.ts')
ix = rep(ix, "  MAX_Q, TIMEOUT_MS, CORS, TOOLS, SYSTEM, EXPLAIN_SYSTEM,", "  MAX_Q, TIMEOUT_MS, CORS, EXPLAIN_SYSTEM,", what='index.ts')
ix = rep(ix, "  const who = String(body?.who ?? '').slice(0, 32);",
         "  const who = String(body?.who ?? '').slice(0, 32);\n"
         "  /* The phone app says so (2026-10-08) and gets its own menu; anything else gets the website's. */\n"
         "  const client = body?.client === 'app' ? 'app' : 'web';", what='index.ts')
ix = rep(ix, "    spec = { system: SYSTEM(term), tools: TOOLS, user: prev ? `EARLIER: ${prev}\\nQUESTION: ${q}` : q };",
         "    spec = routeSpec(client, term, q, prev);", what='index.ts')

SH.write_text(s)
IX.write_text(ix)
print('ask-app-menu-2026-10-08: ok')
