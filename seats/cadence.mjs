/**
 * Professify — the registrar's clock.
 * ===================================
 *
 * THE PROBLEM THIS SOLVES. The scraper ran every morning at 7:00 Pacific and pulled every
 * section of every subject, whether or not a single seat could move. For most of the year that
 * is thousands of requests to a public university to re-learn a number nobody can change. And
 * the flip side is worse: on the morning Round 1 registration opens, one pull a day means the
 * app shows students a seat count that is up to twenty-three hours stale, on the one day of the
 * year the number matters most.
 *
 * So the cadence is not a setting. It is a function of Cal Poly's own published calendar:
 * registrar-calendar.json holds the dates, this file turns "what time is it" into "should we
 * pull, which term, and how hard".
 *
 * FOUR THINGS THIS GETS RIGHT THAT ARE EASY TO GET WRONG:
 *
 *   1. PACIFIC, NOT UTC. Every date the Registrar publishes is a Pacific local date, and GitHub
 *      cron fires in UTC. During Pacific Daylight Time those differ by 7 hours, so a naive UTC
 *      comparison puts the whole gate a day off for 17 hours out of every 24 in the worst case —
 *      and gets it wrong in the direction of going dark early. Everything here converts first.
 *
 *   2. A TERM IS NOT OVER WHEN ITS FIRST ADD DEADLINE PASSES. Fall 2026's 15-week add deadline
 *      is September 14, but the second 7.5-week session is enrollable until October 21. Gating
 *      on the first deadline would take the app dark on a term that is still moving.
 *
 *   3. TWO TERMS RUN AT ONCE. From October 5 to October 21 Fall 2026 is in add/drop for its
 *      second session while Spring 2027 registration is opening. The plan is a LIST of terms,
 *      never one term, because collapsing it to one would silently drop whichever lost.
 *
 *   4. AN UNCOVERED DATE IS NOT A QUIET ONE. If the calendar has nothing to say about today —
 *      the Registrar has not published next year yet, or someone let this file go stale — the
 *      answer is UNKNOWN: keep polling daily and say so loudly. Treating "I don't know" as
 *      "nothing is happening" is how a scraper sleeps through registration week.
 *
 * NOTHING HERE INVENTS A DATE. Every window comes from a published Registrar page named in the
 * calendar's `source`. A term whose calendar is not out yet gets an empty window list and reads
 * as UNKNOWN, which is the honest answer.
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
export const CALENDAR_PATH = join(HERE, 'registrar-calendar.json');

export function loadCalendar(path = CALENDAR_PATH) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

/* ---------------------------------------------------------------- Pacific time ---- */
/* Intl is the only thing in Node that knows when California changes its clocks. Hand-rolling
   "UTC minus 7, or 8 in winter" is the classic way to be an hour wrong for two weeks in March. */
const PT = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/Los_Angeles',
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hour12: false,
});

/** A Date -> what the wall clock in San Luis Obispo says. */
export function pacific(now = new Date()) {
  const p = {};
  for (const { type, value } of PT.formatToParts(now)) p[type] = value;
  /* hour12:false still emits "24" for midnight in some ICU builds. */
  const hour = p.hour === '24' ? 0 : +p.hour;
  return {
    date: `${p.year}-${p.month}-${p.day}`,
    hour,
    minute: +p.minute,
    minutesSinceMidnight: hour * 60 + +p.minute,
  };
}

/* Dates are compared as YYYY-MM-DD strings. That is not laziness: it sidesteps every DST and
   off-by-one-day bug that Date arithmetic invites, and ISO date strings sort correctly. */
const within = (d, from, to) => !!from && !!to && d >= from && d <= to;

/** Whole days from `a` to `b`, both YYYY-MM-DD. Used only for "how close is the deadline". */
export function daysBetween(a, b) {
  return Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 86400000);
}

/* ------------------------------------------------------------------- the phases ---- */
/**
 * How hard to pull in each phase, and why.
 *
 * `every` is minutes between pulls. `mode` is what a pull is for: 'discovery' learns which
 * sections exist (cheap, list-only); 'counts' opens each section for capacity/enrolled/waitlist
 * (expensive, and the entire point during registration).
 */
export const PHASES = {
  /* Nothing about this term can change. Not "pull less" — do not pull. */
  dark: { every: null, mode: null, why: 'no enrollment activity is possible for this term' },

  /* Between windows. Students cannot move, but DEPARTMENTS still add and cancel sections for a
     session that has not opened yet, so section existence is live even when seats are not. */
  quiet: { every: 1440, mode: 'discovery', why: 'no enrollment, but departments still edit the schedule' },

  /* Schedule is published, enrollment has not opened. Capacities are set now and barely move —
     one pull a day with counts on establishes the baseline every later delta is measured from. */
  published: { every: 1440, mode: 'counts', why: 'schedule published; capacities set, enrollment not yet open' },

  /* Appointment rounds. The busiest hours of the year: a popular section can fill inside one
     appointment slot, so a stale count is worse than no count. */
  appointments: { every: 20, mode: 'counts', why: 'registration appointments — seats move by the minute' },

  /* Everyone at once, but spread over weeks. Hourly, tightening as the window closes. */
  open_enrollment: { every: 60, mode: 'counts', why: 'open enrollment' },

  /* Classes have begun; churn until the add deadline. */
  add_drop: { every: 180, mode: 'counts', why: 'add/drop churn' },

  /* The calendar does not cover today. Keep pulling and complain. */
  unknown: { every: 1440, mode: 'counts', why: 'NO CALENDAR DATA for this date — polling daily as a fallback' },
};

/* A window's opening hours are worth more than the rest of it put together, and so is its last
   stretch. These two rules are the difference between "we have seat data" and "we had it when
   it mattered". */
const SURGE_OPEN_DAYS = 1;   // the day a window opens
const SURGE_OPEN_EVERY = 10; // minutes
const CLOSING_DAYS = 3;      // last days of an open-enrollment window
const CLOSING_EVERY = 20;
/* A published drop or add deadline is one of the highest-churn days a term has: everyone who
   was going to move finally moves, and the seats they free are taken within the hour. 60 was the
   right number when it only ever tightened an add/drop window's 180m base — but a deadline can
   now fall inside an overlapping open-enrolment window whose base is ALREADY 60, and then
   "tightening" did nothing at all. It has to beat every base it can coincide with. */
const DEADLINE_DAYS = 2;
const DEADLINE_EVERY = 20;

/**
 * Where one term stands on a given Pacific date.
 * @returns {{phase:string, every:number|null, mode:string|null, why:string, window:object|null}}
 */
export function phaseForTerm(term, date) {
  const sa = term.schedule_available;
  const last = term.last_day_anything_can_change;

  /* Before the schedule exists there is nothing to search for — and this is certain without any
     window data, which is why it is checked before the unknown fallback. */
  if (sa && date < sa) return { phase: 'dark', ...PHASES.dark, why: `schedule for ${term.label} is not published until ${sa}`, window: null };
  if (last && date > last) return { phase: 'dark', ...PHASES.dark, why: `${term.label} closed to enrollment after ${last}`, window: null };

  const windows = Array.isArray(term.windows) ? term.windows : [];

  /* Past schedule_available with no windows means the Registrar has not published this term's
     calendar (or this file is stale). Say UNKNOWN out loud rather than guessing dark. */
  if (!windows.length) {
    return { phase: 'unknown', ...PHASES.unknown, why: `${term.label}: ${PHASES.unknown.why} (calendar has no windows)`, window: null };
  }

  /* OVERLAPPING WINDOWS ARE NORMAL, NOT A DATA ERROR. A term's 15-week and second 7.5-week
     sessions share one Open Enrolment period, so Aug 15 sits inside two windows at once and the
     second 7.5-week session is open all through the 15-week's add/drop. Taking the FIRST match
     would make the answer depend on the order someone typed the windows in — and the order that
     reads most naturally (chronological) is the one that hides the busier phase behind the
     calmer one. Take the most INTENSE match instead: shortest interval wins, and a window with
     no interval never wins anything. */
  const matches = windows.filter(w => within(date, w.from, w.to));
  if (matches.length) {
    /* WHICH WINDOW NAMES THE PHASE: the most intense one. A term's 15-week and second 7.5-week
       sessions share one open-enrolment period, so a single day sits inside two or three windows
       at once. Taking the first match makes the answer depend on the order someone typed them
       in — and chronological order, the order that reads most naturally, is exactly the one that
       hides the busier phase behind the calmer one. Ties are broken by kind so that two windows
       of equal intensity cannot swap the answer when reordered. */
    const rank = k => (PHASES[k] && PHASES[k].every != null) ? PHASES[k].every : Infinity;
    const open = matches.slice().sort((x, y) => rank(x.kind) - rank(y.kind) || (x.kind < y.kind ? -1 : x.kind > y.kind ? 1 : 0))[0];

    /* A MISSPELLED KIND MUST NOT LOOK LIKE A REAL PHASE. `PHASES[kind] || PHASES.unknown` gives
       the unknown CADENCE, but reporting `phase: open.kind` would put "appointment" (singular)
       in the plan — which is not 'unknown', so the loud warning never fires and the only sign of
       a 72x cadence collapse during registration is a string in a log line nobody reads. */
    const known = !!PHASES[open.kind];
    const base = known ? PHASES[open.kind] : PHASES.unknown;
    let every = base.every;
    let why = `${term.label}: ${base.why}`;
    if (!known) why = `${term.label}: window kind ${JSON.stringify(open.kind)} is not a phase this code knows — CHECK registrar-calendar.json. ${PHASES.unknown.why}`;

    /* BOUNDARY RULES RUN ACROSS EVERY MATCHING WINDOW, NOT JUST THE WINNER.
       Reading only the winner's edges lost both surges the moment windows started overlapping.
       On 24 August — the first day of Fall classes — the add/drop window opens, but the second
       session's open enrolment (60m) outranks it (180m) and carries a `from` nine weeks earlier,
       so "is this an opening day?" answered no and the first day of classes polled exactly like
       the Sunday before it. The right question is whether ANY live window has a boundary here. */
    const reasons = [];
    const tighten = (v, note) => { if (v != null && (every == null || v < every)) { every = v; reasons.push(note); } };
    for (const w of matches) {
      const ph = PHASES[w.kind];
      if (!ph || ph.every == null) continue;                    // a never-poll kind tightens nothing

      if (daysBetween(w.from, date) < SURGE_OPEN_DAYS) tighten(SURGE_OPEN_EVERY, `${w.kind} opens today`);

      /* An open-enrolment window's `to` IS its deadline, so the far edge is the right thing to
         watch. An add/drop window's `to` is the LATE APPEAL deadline — a trickle of individually
         approved appeals — while the days seats really move are the published drop and add
         deadlines, which is what `deadlines` holds. Watching `to` there tightened a week late
         and left the two busiest days of each session on the slow base interval. */
      if (w.kind === 'open_enrollment' && daysBetween(date, w.to) < CLOSING_DAYS) tighten(CLOSING_EVERY, `open enrolment closes ${w.to}`);
      for (const d of (w.deadlines || [])) {
        const away = daysBetween(date, d);
        if (away >= 0 && away < DEADLINE_DAYS) tighten(DEADLINE_EVERY, `deadline ${d}`);
      }
    }
    if (reasons.length) why += ` — ${reasons.join('; ')}, pulling every ${every}m`;

    return { phase: known ? open.kind : 'unknown', every, mode: base.mode, why, window: open };
  }

  /* Inside the term's life but between windows. */
  const next = windows.filter(w => w.from > date).sort((a, b) => a.from < b.from ? -1 : 1)[0];
  if (next) return { phase: 'quiet', ...PHASES.quiet, why: `${term.label}: ${PHASES.quiet.why}; next window ${next.kind} opens ${next.from}`, window: null };

  /* Past every window but not past last_day — or last_day is missing. Neither is a reason to
     go dark on a term whose schedule is out. */
  return { phase: 'quiet', ...PHASES.quiet, why: `${term.label}: past every published window`, window: null };
}

/**
 * The whole plan for a moment: every term, its phase, and whether THIS minute is a scheduled
 * pull for it.
 *
 * Slots are aligned to the Pacific day rather than measured from the last run, so the decision
 * needs no memory of previous runs, is identical on every runner, and is completely testable.
 * A daily phase pulls at 07:00 Pacific — the hour the old cron used, kept so the daily numbers
 * stay comparable across the change.
 */
export const DAILY_HOUR_PT = 7;

/* HOW LATE A FIRING MAY BE AND STILL COUNT.
 *
 * This was five minutes, against a ten-minute cron, on the reasoning that a tolerance narrower
 * than the interval stops one slot being served twice. The arithmetic says otherwise, and says it
 * in the worst direction: GitHub does not promise scheduled runs are punctual, the delay lands in
 * the run's own creation time so no context value escapes it, and at a sustained five-minute
 * delay EVERY cadence drops to zero firings a day — silently, with every run green.
 *
 *   tolerance  5, a 10-minute cron, delay 0..9m  ->  every=20: 72,72,72,72,72, 0,0,0,0,0  (ideal 72)
 *   tolerance 10, a 10-minute cron, delay 0..9m  ->  every=20: 72,72,72,72,72,72,72,72,72,72
 *
 * Equality is not the risky edge, it is the correct one: every interval in use is a multiple of
 * the cron interval, so if minute m is due then m + CRON is exactly one interval further along
 * and lands in the NEXT slot, never the same one. A tolerance equal to the cron interval means
 * every slot is served exactly once no matter how late the firing is, which is the property
 * actually wanted.
 *
 * It must stay equal to the workflow's cron. check-cadence.mjs reads both and asserts it. */
export const SLOT_TOLERANCE = 10;

/* HOW MUCH CALENDAR IS LEFT.
   `unknown` only fires for terms that are IN the file. A term nobody has added yet — Fall 2027,
   say — produces no phase, no warning, and no trace: the plan simply does not mention it, which
   is indistinguishable from a quiet week. So the file's own edge has to be an alarm of its own.
   The lead time is deliberately long because Cal Poly publishes a term's schedule roughly five
   months before its classes begin, and registration opens two weeks after that; a warning that
   arrives inside that window arrives too late to act on calmly. */
export const HORIZON_WARN_DAYS = 90;

export function calendarHorizon(calendar) {
  const ends = (calendar.terms || []).map(t => t.last_day_anything_can_change).filter(Boolean).sort();
  return ends.length ? ends[ends.length - 1] : null;
}

export function planFor(now = new Date(), calendar = loadCalendar()) {
  const pt = pacific(now);
  const terms = (calendar.terms || []).map(t => {
    const p = phaseForTerm(t, pt.date);
    return {
      label: t.label,
      term_code: t.term_code || null,
      phase: p.phase,
      every: p.every,
      mode: p.mode,
      why: p.why,
      due: dueNow(pt, p.every),
      source: t.source,
    };
  });
  const dueTerms = terms.filter(t => t.due && t.every !== null);
  const horizon = calendarHorizon(calendar);
  const warnings = [];
  if (!horizon) warnings.push('registrar-calendar.json names no end date for any term — the gate has no horizon at all.');
  else if (daysBetween(pt.date, horizon) < HORIZON_WARN_DAYS) {
    warnings.push(`registrar-calendar.json runs out on ${horizon} (${daysBetween(pt.date, horizon)} days). Add the next term from the Registrar's planning calendar — a term that is not in this file produces no phase and no warning of its own.`);
  }
  for (const t of terms) if (t.phase === 'unknown') warnings.push(`NO CALENDAR DATA for ${t.label} — ${t.why}`);
  for (const t of dueTerms) if (!t.term_code) warnings.push(`${t.label} is due to be scraped (${t.phase}) but has no confirmed PeopleSoft term code.`);

  return {
    pacific: pt,
    verified_on: calendar.verified_on || null,
    horizon,
    warnings,
    terms,
    due: dueTerms,
    scrape: dueTerms.length > 0,
    unknown: terms.filter(t => t.phase === 'unknown').map(t => t.label),
  };
}

/** Is this Pacific minute one of the aligned slots for a given interval? */
export function dueNow(pt, every) {
  if (every === null || every === undefined) return false;
  if (every >= 1440) return pt.hour === DAILY_HOUR_PT && pt.minute < SLOT_TOLERANCE;
  /* Every interval in use divides the Pacific day evenly, so slots are fixed points on the wall
     clock and no drift accumulates across 23- and 25-hour days. */
  return pt.minutesSinceMidnight % every < SLOT_TOLERANCE;
}

/** One-line human summary, for the workflow log and the run summary. */
export function describe(plan) {
  const lines = [`Pacific ${plan.pacific.date} ${String(plan.pacific.hour).padStart(2, '0')}:${String(plan.pacific.minute).padStart(2, '0')}`];
  for (const t of plan.terms) {
    const cadence = t.every === null ? 'never' : t.every >= 1440 ? `daily @${DAILY_HOUR_PT}:00 PT` : `every ${t.every}m`;
    lines.push(`  ${t.due ? '>>' : '  '} ${t.label.padEnd(12)} ${t.phase.padEnd(16)} ${cadence.padEnd(18)} ${t.mode || '-'}  — ${t.why}`);
  }
  for (const w of (plan.warnings || [])) lines.push('  !! ' + w);
  lines.push(plan.scrape ? `  => SCRAPE: ${plan.due.map(t => `${t.label} (${t.mode})`).join(', ')}` : '  => skip this run');
  return lines.join('\n');
}
