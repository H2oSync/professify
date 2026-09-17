#!/usr/bin/env node
/**
 * The gate the workflow asks before it spends anything.
 *
 * Prints the plan for human eyes, writes machine outputs for the lanes, and exits 0 either way —
 * "nothing to do right now" is a SUCCESS, not a failure. A skipped run that reports failure
 * trains everyone to ignore a red workflow, which is how a genuinely broken scraper goes
 * unnoticed for a week.
 *
 *   node plan.mjs            # print and emit outputs
 *   node plan.mjs --at ISO   # ask what it would do at another moment (for testing the gate)
 */
import { appendFileSync } from 'node:fs';
import { planFor, describe, daysBetween, loadCalendar } from './cadence.mjs';

const atArg = process.argv.indexOf('--at');
const now = atArg > -1 && process.argv[atArg + 1] ? new Date(process.argv[atArg + 1]) : new Date();
if (Number.isNaN(now.getTime())) { console.error('--at needs an ISO timestamp'); process.exit(2); }

/* CP_CALENDAR points the gate at a different calendar file. Its reason for existing is that the
   dispatch logic — which terms go to the lanes — could otherwise only ever be exercised against
   whatever the committed calendar happens to say today, and the case that matters most (two
   confirmed terms due at once, neither allowed to starve the other) is not reachable that way
   until Spring's code is committed in October. A bug that only becomes testable on the morning
   it fires is not tested. */
const plan = planFor(now, process.env.CP_CALENDAR ? loadCalendar(process.env.CP_CALENDAR) : undefined);
console.log(describe(plan));

/* WHICH TERMS THE LANES PULL — plural, and what happens when one of them cannot be known.
 *
 * Two rewrites got here, and the second one exists because the first was still wrong:
 *
 *   v1 picked `ordered.find(t => t.term_code)` — the highest-priority due term that HAPPENED to
 *   have a code. On 19 October, Round 1 opening morning, that skipped Spring 2027 and swept Fall
 *   2026 instead: green run, real code, real label, entirely the wrong semester. And from 22
 *   October it returned null for 252 days and printed `scrape=false` while the log above it said
 *   `=> SCRAPE: Spring 2027`.
 *
 *   v2 made an unconfirmed term fail the run. That fixed the wrong-term dispatch and replaced it
 *   with two new ones. A term in the calmest phase there is — `quiet`, which means "nobody can
 *   enrol, departments are still editing" — would abort a run that had already correctly decided
 *   to scrape a healthy term. And because only one term was ever dispatched, Fall 2026's second
 *   7.5-week add/drop (15-28 October: classes in session, students adding and dropping) was
 *   starved for ten days by Spring's higher-priority registration.
 *
 * So: EVERY due term with a confirmed code is dispatched, as a list, which is what cadence.mjs
 * said all along — "the plan is a LIST of terms, never one term, because collapsing it to one
 * would silently drop whichever lost." Collapsing it by accident and collapsing it on purpose
 * drop the same term.
 *
 * And the failure is separated from the dispatch. This CLI writes its outputs and exits 0 for
 * every ordinary outcome, including a blocked term; a separate `guard` job in the workflow turns
 * a missing term code red. A blocked term therefore makes the run impossible to miss WITHOUT
 * taking down the terms that are fine. The only non-zero exits are for inputs that make the gate
 * itself unusable: a calendar whose every term ended over a month ago (3), a half-specified
 * manual override (4), and a value that would corrupt GITHUB_OUTPUT (5).
 */
const rank = { appointments: 0, open_enrollment: 1, add_drop: 2, published: 3, quiet: 4, unknown: 5 };
const ordered = [...plan.due].sort((a, b) => (rank[a.phase] ?? 9) - (rank[b.phase] ?? 9));

/* Dispatchable: due, and we know which PeopleSoft term it is. */
const dispatch = ordered.filter(t => t.term_code).map(t => ({
  code: t.term_code,
  label: t.label,
  phase: t.phase,
  /* `details` decides CP_FETCH_DETAILS, and a lane run with details off leaves the seat-count
     columns untouched rather than refreshing them. It is spelled out per term rather than
     derived from a truthiness test, because the cost of getting it wrong is a table full of
     blanks stamped with a fresh timestamp. */
  details: t.mode === 'counts' ? '1' : '0',
  force: '0',
}));

/* Blocked: due, no confirmed code. Only an ENROLLING phase is worth failing over — `quiet` means
   nobody can enrol and `unknown` means we do not know, and failing every run forever on either
   is how a red build becomes wallpaper that hides a real one. */
const ENROLLING = new Set(['appointments', 'open_enrollment', 'add_drop', 'published']);
const blocked = ordered.filter(t => !t.term_code);
const hardBlocked = blocked.filter(t => ENROLLING.has(t.phase));

/* THE MANUAL OVERRIDE GOES THROUGH THE SAME OUTPUT, not around it.
   `ignore_calendar` used to skip this CLI entirely and let the workflow fall back to a hardcoded
   CP_TERM with no label — which is how an operator working around a blocked run ends up sweeping
   a dead term under a code that outlives it. Forcing a term here means the override still has to
   name the term it wants, still flows through `terms`, and still reaches a scraper that refuses
   a code it cannot confirm. */
if (process.env.CP_FORCE_TERM && process.env.CP_FORCE_LABEL) {
  /* `force: '1'` rides ON THE TERM, and the lane turns it into CP_IGNORE_CALENDAR for that leg
     only. The first version wired the workflow's CP_IGNORE_CALENDAR to a literal '0', so the
     override got past this gate and was then refused by the scraper's own dark check: twenty-four
     green lanes, zero rows, and a skip message telling the operator to set a variable the
     workflow hardcoded against them. An override that silently does nothing is worse than not
     having one. Per-term, not per-run, so forcing one term does not switch the calendar off for
     any other term in the same sweep. */
  const forced = {
    code: process.env.CP_FORCE_TERM,
    label: process.env.CP_FORCE_LABEL,
    phase: 'forced',
    details: process.env.CP_FORCE_DETAILS === '0' ? '0' : '1',
    force: '1',
  };
  /* Prepended, not substituted. Evicting the terms that were legitimately due would re-create the
     starvation this whole restructure removed — forcing Spring should not stop Fall being swept. */
  const rest = dispatch.filter(t => t.code !== forced.code);
  dispatch.length = 0;
  dispatch.push(forced, ...rest);
  console.log(`  => FORCED: ${forced.label} / ${forced.code} (calendar gate bypassed for this term)` +
    (rest.length ? ` — the terms that were due anyway still run: ${rest.map(t => t.label).join(', ')}` : ''));
} else if (process.env.CP_FORCE_TERM || process.env.CP_FORCE_LABEL) {
  console.log('::error title=Incomplete override::ignore_calendar needs BOTH a term code and a term_label — a code with no label cannot be confirmed against anything.');
  process.exit(4);
}

const out = {
  scrape: dispatch.length ? 'true' : 'false',
  terms: JSON.stringify(dispatch),
  /* Scalars for the first dispatched term, kept so a human reading the run, and any step that
     wants one value, does not have to parse JSON. The lanes use `terms`. */
  term: dispatch.length ? dispatch[0].code : '',
  term_label: dispatch.length ? dispatch[0].label : '',
  phase: dispatch.length ? dispatch[0].phase : (ordered[0] ? ordered[0].phase : 'dark'),
  details: dispatch.length ? dispatch[0].details : '0',
  blocked: hardBlocked.map(t => `${t.label} (${t.phase})`).join('; '),
  needs_term_discovery: blocked.length ? 'true' : 'false',
  /* WHICH terms, not just whether. needs_term_discovery on its own is a boolean a job can branch
     on but cannot ACT on — the discover path needs a label to resolve. Without this, the only
     automatic response available to the Oct 5 run is a warning, and a warning inside a job that
     exits 0 is the thing the comment below calls indistinguishable from silence. */
  discover_labels: blocked.map(t => t.label).join('; '),
  unknown_terms: plan.unknown.join(','),
  horizon: plan.horizon || '',
};

if (dispatch.length > 1) console.log(`  => ${dispatch.length} terms dispatched: ${dispatch.map(t => `${t.label}/${t.code}`).join(', ')}`);

/* WARNINGS HAVE TO LEAVE stdout. Every one of these was already being printed, inside a job that
   exits 0, 144 times a day — which is indistinguishable from silence. `::warning::` puts them in
   the Actions UI, on the run summary, and in the notification. */
for (const w of (plan.warnings || [])) console.log(`::warning title=Registrar clock::${w}`);

if (process.env.GITHUB_OUTPUT) {
  appendFileSync(process.env.GITHUB_OUTPUT, Object.entries(out).map(([k, v]) => `${k}=${v}`).join('\n') + '\n');
}
if (process.env.GITHUB_STEP_SUMMARY) {
  appendFileSync(process.env.GITHUB_STEP_SUMMARY, `### Registrar clock\n\n\`\`\`\n${describe(plan)}\n\`\`\`\n`);
}
/* GITHUB_OUTPUT is newline-delimited, and `term_label` can reach here from a free-text dispatch
   input — a newline in it would inject arbitrary step outputs. Nothing in this repo is reachable
   without write access, so this is hygiene rather than a hole, but it costs one line. */
for (const [k, v] of Object.entries(out)) {
  if (/[\r\n]/.test(String(v))) { console.error(`refusing to write a multi-line value for ${k}`); process.exit(5); }
}
console.log('\noutputs: ' + JSON.stringify(out));

if (hardBlocked.length) {
  const names = hardBlocked.map(t => `${t.label} (${t.phase})`).join(', ');
  console.log(`::error title=No term code::${names} due to be scraped with no confirmed PeopleSoft term code. Run this workflow with mode=discover_term, then commit the code into seats/registrar-calendar.json.`);
  console.log(
    `\n${names} ${hardBlocked.length === 1 ? 'is' : 'are'} due to be scraped and ` +
    `${hardBlocked.length === 1 ? 'has' : 'have'} no confirmed PeopleSoft term code. The guard job will fail this run.\n` +
    `\nNothing is guessed and nothing is substituted: a guessed code returns an EMPTY search that ` +
    `looks exactly like a term with no classes, and sweeping a different term returns real data ` +
    `about the wrong semester.\n` +
    `\nFIX: run this workflow by hand with mode=discover_term and term_label="${hardBlocked[0].label}". ` +
    `It resolves the code against the live class search and prints it. Put it in ` +
    `seats/registrar-calendar.json as that term's term_code, with a note saying how it was confirmed.\n` +
    (dispatch.length ? `\nThe terms that ARE confirmed still run: ${dispatch.map(t => t.label).join(', ')}.\n` : '')
  );
}

/* A HORIZON IN THE PAST IS A STALE FILE, NOT AN UNPUBLISHED TERM — and that one does fail. */
const STALE_DAYS = 30;
if (plan.horizon && daysBetween(plan.pacific.date, plan.horizon) < -STALE_DAYS) {
  console.log(`::error title=Stale calendar::registrar-calendar.json ended ${plan.horizon}, more than ${STALE_DAYS} days ago. Nothing in it describes today.`);
  console.error(`\nregistrar-calendar.json ran out on ${plan.horizon}. Every term in it is over, so the gate has nothing to say about today and is guessing by omission. Add the current terms from the Registrar's planning calendars.\n`);
  process.exit(3);
}
