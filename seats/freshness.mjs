#!/usr/bin/env node
/**
 * TermChamp — is the seat data as fresh as the registrar's clock says it should be? (2026-10-30)
 *
 * The scraper can be "green" while students look at old numbers: lanes that write a fraction of a
 * subject, a subject that silently searched its neighbour, sections nobody removed. Nothing used
 * to notice. This reads course_seats for every term the calendar says is LIVE right now (any phase
 * but `dark` — a finished term going stale is expected and is never reported) and fails when:
 *
 *   · the term's newest row is older than its limit (sweeps are not landing at all),
 *   · any subject's newest row is older than the limit (a subject is failing every sweep),
 *   · rows have gone unseen far past the dropped-section grace (pruning is not keeping up).
 *
 * Limits come from sweep.mjs freshLimitMinutes: appointments 2h, open enrolment 3h, add/drop 7h,
 * daily phases 49h.
 *
 *   node freshness.mjs                    # reads SUPABASE_URL + SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY)
 *   CP_FRESHNESS_ROWS=file.json node freshness.mjs --at ISO    # offline: {code:[{course_code,updated_at}]}
 *
 * Exit 0 = fine (or nothing live), 1 = a problem, 2 = could not check at all.
 */
import { appendFileSync, readFileSync } from 'node:fs';
import { planFor, loadCalendar } from './cadence.mjs';
import { freshnessReport, classesBegin } from './sweep.mjs';

const atArg = process.argv.indexOf('--at');
const now = atArg > -1 && process.argv[atArg + 1] ? new Date(process.argv[atArg + 1]) : new Date();
if (Number.isNaN(now.getTime())) { console.error('--at needs an ISO timestamp'); process.exit(2); }

const calendar = process.env.CP_CALENDAR ? loadCalendar(process.env.CP_CALENDAR) : loadCalendar();
const plan = planFor(now, calendar);
const live = plan.terms.filter(t => t.term_code && t.phase !== 'dark' && t.every != null);
const beginByCode = Object.fromEntries((calendar.terms || []).filter(t => t.term_code).map(t => [t.term_code, classesBegin(t)]));

async function readRows(code) {
  const url = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
  const key = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_ANON_KEY || '';
  if (!url || !key) throw new Error('SUPABASE_URL and a key are required');
  const out = [];
  for (let off = 0; off < 50000; off += 1000) {
    const r = await fetch(`${url}/rest/v1/course_seats?term=eq.${encodeURIComponent(code)}&select=course_code,updated_at&order=class_nbr.asc&limit=1000&offset=${off}`,
      { headers: { apikey: key, Authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(20000) });
    if (!r.ok) throw new Error(`course_seats read for ${code}: HTTP ${r.status}`);
    const part = await r.json();
    out.push(...part);
    if (part.length < 1000) return out;
  }
  return out;
}

let rowsByTerm = {};
try {
  if (process.env.CP_FRESHNESS_ROWS) rowsByTerm = JSON.parse(readFileSync(process.env.CP_FRESHNESS_ROWS, 'utf8'));
  else for (const t of live) rowsByTerm[t.term_code] = await readRows(t.term_code);
} catch (e) {
  console.log(`::error title=Seat freshness check could not run::${String(e.message || e).slice(0, 300)}`);
  process.exit(2);
}

const rep = freshnessReport(plan.terms, rowsByTerm, now, beginByCode);
for (const l of rep.lines) console.log('  ' + l);
for (const w of rep.warnings) console.log(`::warning title=Seat freshness::${w}`);
for (const p of rep.problems) console.log(`::error title=Seat data is stale::${p}`);
if (process.env.GITHUB_STEP_SUMMARY) {
  appendFileSync(process.env.GITHUB_STEP_SUMMARY, `### Seat freshness\n\n${rep.lines.map(l => '- ' + l).join('\n')}\n\n` +
    (rep.problems.length ? `**${rep.problems.length} problem(s):**\n\n${rep.problems.map(p => '- ' + p).join('\n')}\n` : 'No problems.\n') +
    (rep.warnings.length ? `\nWarnings:\n\n${rep.warnings.map(p => '- ' + p).join('\n')}\n` : ''));
}
if (rep.problems.length) {
  console.log(`\n${rep.problems.length} freshness problem(s). See the sweep lanes' step summaries (sweep-report.json in the diag artifacts) for which subjects failed and why.`);
  process.exit(1);
}
console.log(live.length ? '\nSeat data is as fresh as the calendar requires.' : '\nNo term is live right now — nothing to check.');
