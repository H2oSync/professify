#!/usr/bin/env python3
"""Seats: pull whatever is stale, and let Supabase's clock start the workflow (2026-10-13).

WHY. GitHub was asked to fire update-seats.yml every 10 minutes and fired it 34 times between
Oct 5 and Oct 13 — about once every 5-6 hours. The gate only pulls a term when the firing lands
within SLOT_TOLERANCE of one of its wall-clock slots, so Spring 2027 (daily slot, 7:00 PT) was
not pulled once after Oct 5, and from Oct 19 (every 20m, 10m on opening day) it would get a
couple of pulls a day during registration.

TWO CHANGES:
  1. cadence.mjs / plan.mjs — CATCH-UP. A term is also due when its newest row in course_seats
     is older than its interval, and a clock slot is skipped when the term was pulled within the
     last half interval (two clocks must not start two sweeps). The plan job reads that from Supabase (one tiny query per
     term). Any firing, however late, pulls what is stale. If the read fails the gate falls back
     to slots only and says so.
  2. update-seats.yml — a dispatch input `auto` that joins the same one-sweep-at-a-time
     concurrency group as the cron, so Supabase pg_cron (sql/professify-seats-dispatch.sql) can
     start the workflow every 10 minutes on time. The GitHub cron stays as a backup.

Each anchor must match exactly once; the script stops before writing anything if one doesn't.
"""
import sys, pathlib

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
edits = {}

def rep(path, old, new):
    p = ROOT / path
    s = edits.get(path, p.read_text())
    n = s.count(old)
    if n != 1:
        sys.exit(f'{path}: anchor matched {n}x: {old[:70]!r}')
    edits[path] = s.replace(old, new)

# ---------------------------------------------------------------- cadence.mjs ----
rep('seats/cadence.mjs',
"""export function planFor(now = new Date(), calendar = loadCalendar()) {
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
  });""",
"""/* CATCH-UP (2026-10-13). Slots alone assume the cron fires on time. It does not: GitHub fired a
   10-minute cron about every 5-6 hours from Oct 5 to Oct 13, so Spring 2027's 7:00 slot was never
   hit and its rows sat at Oct 5. `lastPulls` maps a term code to the ISO time of its newest row
   in course_seats (null = the term has no rows). A term whose newest row is at least one
   interval old is due no matter what the clock says — so every firing, however late, pulls what
   is stale, and a missed slot costs one firing instead of a day.
   `lastPulls` undefined = not read (tests, or Supabase unreachable): slots only, as before. */
/* Age in minutes of a term's newest row, or null when unknown / no rows. */
export function ageMinutes(ageNow, last) {
  if (last === null || last === undefined) return null;
  const t = new Date(last).getTime();
  return Number.isNaN(t) ? null : (ageNow.getTime() - t) / 60000;
}

/* Stale = newest row at least one interval old. A term with NO rows is not "stale" — it is pulled
   on its clock slots only, because a term the scraper keeps finding empty (it exits on "Zero
   sections" without writing) would otherwise be re-swept, 24 lanes, every ten minutes forever. */
export function isStale(age, every) {
  return every !== null && every !== undefined && age !== null && age >= every;
}

/* Fresh = pulled within the last half interval. Two clocks start this workflow (Supabase's and
   GitHub's backup cron); without this, a GitHub firing that lands in the same slot right after a
   finished sweep would start a second full sweep of numbers that are minutes old. */
export function isFresh(age, every) {
  return every !== null && every !== undefined && age !== null && age < every / 2;
}

/* `ageNow` is the real current time. `now` (the run's creation time) still picks the clock slot,
   but a run released late from the concurrency queue must measure age against the present, or
   rows written while it waited look newer than "now" and it never counts as stale. */
export function planFor(now = new Date(), calendar = loadCalendar(), lastPulls = undefined, ageNow = now) {
  const pt = pacific(now);
  const terms = (calendar.terms || []).map(t => {
    const p = phaseForTerm(t, pt.date);
    const last = lastPulls && t.term_code ? (lastPulls[t.term_code] ?? null) : undefined;
    const age = last === undefined ? null : ageMinutes(ageNow, last);
    const stale = !!t.term_code && isStale(age, p.every);
    const fresh = !!t.term_code && isFresh(age, p.every);
    return {
      label: t.label,
      term_code: t.term_code || null,
      phase: p.phase,
      every: p.every,
      mode: p.mode,
      why: p.why,
      due: (dueNow(pt, p.every) && !fresh) || stale,
      stale,
      last_pull: last === undefined ? undefined : last,
      source: t.source,
    };
  });""")

rep('seats/cadence.mjs',
"""    lines.push(`  ${t.due ? '>>' : '  '} ${t.label.padEnd(12)} ${t.phase.padEnd(16)} ${cadence.padEnd(18)} ${t.mode || '-'}  — ${t.why}`);""",
"""    const age = t.last_pull === undefined ? '' : t.last_pull === null ? ' [no rows yet]'
      : ` [newest row ${Math.round((plan.ageNow - new Date(t.last_pull).getTime()) / 60000)}m old${t.stale ? ', STALE' : ''}]`;
    lines.push(`  ${t.due ? '>>' : '  '} ${t.label.padEnd(12)} ${t.phase.padEnd(16)} ${cadence.padEnd(18)} ${t.mode || '-'}  — ${t.why}${age}`);""")

rep('seats/cadence.mjs',
"""  return {
    pacific: pt,
    verified_on: calendar.verified_on || null,""",
"""  return {
    now: now.getTime(),
    ageNow: ageNow.getTime(),
    pacific: pt,
    verified_on: calendar.verified_on || null,""")

# ------------------------------------------------------------------- plan.mjs ----
rep('seats/plan.mjs',
"""const plan = planFor(now, process.env.CP_CALENDAR ? loadCalendar(process.env.CP_CALENDAR) : undefined);
console.log(describe(plan));""",
"""const calendar = process.env.CP_CALENDAR ? loadCalendar(process.env.CP_CALENDAR) : loadCalendar();

/* HOW OLD EACH TERM'S DATA IS (2026-10-13) — see isStale in cadence.mjs. One query per term with
   a confirmed code: the newest updated_at in course_seats. CP_LAST_PULLS (JSON: {code: iso|null})
   replaces the query in tests. Anything going wrong means `undefined` = slots only, and a
   warning, never a failed gate. */
async function readLastPulls() {
  if (process.env.CP_LAST_PULLS) return JSON.parse(process.env.CP_LAST_PULLS);
  const url = (process.env.SUPABASE_URL || '').replace(/\\/$/, '');
  const key = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_ANON_KEY || '';
  if (!url || !key) return undefined;
  const out = {};
  for (const t of calendar.terms || []) {
    if (!t.term_code) continue;
    const r = await fetch(`${url}/rest/v1/course_seats?term=eq.${encodeURIComponent(t.term_code)}&select=updated_at&order=updated_at.desc.nullslast&limit=1`,
      { headers: { apikey: key, Authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(10000) });
    if (!r.ok) throw new Error(`course_seats read for ${t.term_code}: HTTP ${r.status}`);
    const rows = await r.json();
    out[t.term_code] = rows.length && rows[0].updated_at ? rows[0].updated_at : null;
  }
  return out;
}
let lastPulls, pullWarning = '';
try { lastPulls = await readLastPulls(); }
catch (e) { lastPulls = undefined; pullWarning = `Could not read how old each term's seats are (${String(e.message || e).slice(0, 160)}) — pulling on clock slots only this run.`; }
if (lastPulls === undefined && !pullWarning && !process.env.CP_CALENDAR) pullWarning = 'SUPABASE_URL / key not set for the plan job — pulling on clock slots only.';

/* Age is measured against the real present unless a test pins the moment with CP_LAST_PULLS. */
const ageNow = process.env.CP_LAST_PULLS ? now : new Date(Math.max(now.getTime(), Date.now()));
const plan = planFor(now, calendar, lastPulls, ageNow);
if (pullWarning) plan.warnings.push(pullWarning);
console.log(describe(plan));""")

# ------------------------------------------------------ the workflow ----
rep('.github/workflows/update-seats.yml',
"""concurrency:
  group: ${{ github.event_name == 'schedule' && 'seats-sweep' || github.run_id }}
  cancel-in-progress: false""",
"""#
# `auto` (2026-10-13): Supabase pg_cron starts this workflow every 10 minutes through the API
# (sql/professify-seats-dispatch.sql), because GitHub fired the */10 cron only every 5-6 hours.
# Those runs are the same thing as a cron firing, so they join the same one-sweep group.
concurrency:
  group: ${{ (github.event_name == 'schedule' || github.event.inputs.auto == 'true') && 'seats-sweep' || github.run_id }}
  cancel-in-progress: false""")

rep('.github/workflows/update-seats.yml',
"""      ignore_calendar:
        description: 'Bypass the calendar gate. REQUIRES both term_code and term_label — a code with no label cannot be confirmed against anything.'
        default: 'false'
        type: choice
        options: ['false', 'true']""",
"""      ignore_calendar:
        description: 'Bypass the calendar gate. REQUIRES both term_code and term_label — a code with no label cannot be confirmed against anything.'
        default: 'false'
        type: choice
        options: ['false', 'true']
      auto:
        description: 'true = started by the Supabase clock (behaves like the cron). Leave false by hand.'
        default: 'false'
        type: choice
        options: ['false', 'true']""")

rep('.github/workflows/update-seats.yml',
"""          CP_FORCE_DETAILS: ${{ github.event.inputs.details || '1' }}""",
"""          CP_FORCE_DETAILS: ${{ github.event.inputs.details || '1' }}
          # catch-up (2026-10-13): the gate reads how old each term's newest row is
          SUPABASE_URL:         ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}""")

for path, s in edits.items():
    (ROOT / path).write_text(s)
    print('patched', path)
