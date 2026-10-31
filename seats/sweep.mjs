/**
 * TermChamp — is this sweep's data what it claims to be, and is it COMPLETE? (2026-10-30)
 * =====================================================================================
 *
 * WHAT THE AUDIT FOUND (read-only SQL against course_seats, 2026-10-31 00:55 UTC).
 * Spring 2027 (2274) held 7,851 rows; 990 had not been seen for a day. Of those:
 *
 *   678  were FALL 2026 SECTIONS STAMPED AS SPRING. Every one has dates in 2026
 *        ("08/24/2026 - 12/11/2026" for 669 of them), and every one has an exact twin in term
 *        2268 with the same class_nbr, course_code and section. Each was written by ONE subject
 *        search, inside one minute — and whole lanes at a time: STAT,BRAE,GRC,PLSC,BMED at
 *        Oct 29 03:49-03:58, COMS,AGC,JPNS,WLC at Oct 30 00:15-00:17, HIST,AEPS,ENGR at Oct 30
 *        19:13-19:15. The page's default term is Fall, and the search ran against it while the
 *        term FIELD read back 2274 — confirmTerm() passed, because the read-back is of our own
 *        write to the DOM, not of what PeopleSoft searched. Fall lanes are never hit because
 *        "fell back to the default" lands on the right term for them. The app showed those 678
 *        Fall sections as Spring classes, and the next correct sweep never touched them again,
 *        so they sat there forever looking a little older every day.
 *
 *   354  are real Spring sections that stopped appearing — departments cancelling sections
 *        before registration (PSY alone: 47, nearly all enrolled 0, last seen Oct 5-20). Nothing
 *        ever removed a row, so these lingered too.
 *
 * And a third defect the same queries exposed: a subject search that returns ANOTHER subject's
 * sections (the one searched just before it in the lane). GEOG's search at 00:09 Oct 31 returned
 * 278 MATH sections and stamped them subject=GEOG; AEPS returned HIST's 70; ANT/FPE/MSCI returned
 * EE's. The rows are real and their counts are right — only the label and the completeness of the
 * subject that was ASKED for are wrong.
 *
 * So nothing here trusts what we set on the form. It checks the RESULTS: their dates say which
 * term they are, and their course codes say which subject. Both are pure functions of the parsed
 * list, so they are tested in check-sweep.mjs without a browser.
 */

/* ------------------------------------------------------------------- dates ---- */

/** "01/25/2027 - 05/14/2027 01/25/2027 - 03/24/2027" -> { start:'2027-01-25', end:'2027-05-14' } */
export function parseDates(s) {
  const all = [...String(s || '').matchAll(/(\d{1,2})\/(\d{1,2})\/(\d{4})/g)]
    .map(m => `${m[3]}-${m[1].padStart(2, '0')}-${m[2].padStart(2, '0')}`).sort();
  return all.length ? { start: all[0], end: all[all.length - 1] } : null;
}

const addDays = (iso, n) => new Date(Date.parse(iso + 'T00:00:00Z') + n * 86400000).toISOString().slice(0, 10);

/**
 * When a term's classes begin, from the calendar: the earliest add_drop window's `from`, which
 * registrar-calendar.json quotes verbatim as "<Term> Classes Begin". Null when the term has no
 * add/drop window yet (Summer 2027 today) — the term check then says "unverifiable", never guesses.
 */
export function classesBegin(termEntry) {
  const w = ((termEntry && termEntry.windows) || []).filter(x => x.kind === 'add_drop' && x.from).map(x => x.from).sort();
  return w.length ? w[0] : null;
}

/* A section belongs to some OTHER term when it ended well before this term's classes began, or
   starts long after. Measured against the live table on 2026-10-31: of 7,851 Spring rows, exactly
   the 678 Fall impostors fail this and not one genuine Spring row does (the latest real Spring
   start is 05/05/2027, a Maritime cruise, 100 days in); of 6,988 Fall rows, 7 June-session rows
   fail it — a minority in mixed subjects, which is why the verdict is a MAJORITY, not any-row. */
export const ENDS_BEFORE_SLACK_DAYS = 14;
export const STARTS_AFTER_DAYS = 120;

/**
 * @returns {{verdict:'ok'|'wrong-term'|'unverifiable', foreign:number, dated:number, note:string}}
 */
export function termCheck(list, begin) {
  const rows = list || [];
  if (!begin) return { verdict: 'unverifiable', foreign: 0, dated: 0, note: 'no classes-begin date in the calendar for this term — dates not checked' };
  const lo = addDays(begin, -ENDS_BEFORE_SLACK_DAYS), hi = addDays(begin, STARTS_AFTER_DAYS);
  let dated = 0, foreign = 0; const sample = [];
  for (const r of rows) {
    const d = parseDates(r.dates); if (!d) continue;
    dated++;
    if (d.end < lo || d.start > hi) { foreign++; if (sample.length < 3) sample.push(`${r.course_code || '?'} ${r.dates}`); }
  }
  if (!dated) return { verdict: rows.length ? 'unverifiable' : 'ok', foreign, dated, note: rows.length ? 'no row carries a date' : 'empty list' };
  if (foreign * 2 >= dated) {
    return { verdict: 'wrong-term', foreign, dated,
      note: `${foreign} of ${dated} sections are dated outside a term whose classes begin ${begin} (e.g. ${sample.join('; ')}) — the search ran against a different term` };
  }
  return { verdict: 'ok', foreign, dated, note: foreign ? `${foreign} of ${dated} sections dated oddly (kept — a minority is real, e.g. early-start sessions)` : `${dated} sections dated inside the term` };
}

/* ----------------------------------------------------------------- subjects ---- */

/** "MATH 1241" -> "MATH". Blank when the code is blank. */
export const subjectOf = code => String(code || '').trim().split(/\s+/)[0].toUpperCase();

/**
 * @returns {{verdict:'ok'|'mixed'|'wrong-subject', mismatched:number, coded:number, others:object, note:string}}
 */
export function subjectCheck(list, subj) {
  const want = String(subj || '').toUpperCase();
  let coded = 0, mismatched = 0; const others = {};
  for (const r of list || []) {
    const p = subjectOf(r.course_code); if (!p) continue;
    coded++;
    if (p !== want) { mismatched++; others[p] = (others[p] || 0) + 1; }
  }
  if (!coded || !mismatched) return { verdict: 'ok', mismatched, coded, others, note: coded ? `${coded} sections, all ${want}` : 'no coded rows' };
  const o = Object.entries(others).map(([k, v]) => `${k}×${v}`).join(', ');
  if (mismatched * 2 >= coded) return { verdict: 'wrong-subject', mismatched, coded, others, note: `searched ${want} but ${mismatched} of ${coded} sections are ${o} — the subject did not take` };
  return { verdict: 'mixed', mismatched, coded, others, note: `${mismatched} of ${coded} sections belong to ${o} (relabelled)` };
}

/** Label every row by its own course code, never by the lane's loop variable. Rows with no code keep the searched subject. */
export function relabelBySubject(list, searched) {
  for (const r of list || []) r.subject = subjectOf(r.course_code) || searched;
  return list;
}

/* ------------------------------------------------------------ completeness ---- */

/**
 * Two different questions, kept apart on purpose:
 *   failed    — something went wrong that a human should hear about (the lane exits non-zero)
 *   pruneSafe — this sweep is trustworthy enough to conclude "a row we did not see is gone"
 * A subject can be not-failed and still not prune-safe (an unverifiable term, a suspected
 * open-only leak, a subject Cal Poly does not offer this term). It can never be prune-safe and
 * failed.
 */
export function sweepVerdict(o) {
  const failed = [], unsafe = [];
  if (o.notOffered) return { failed: false, pruneSafe: false, reasons: ['not offered this term (not in the subject list)'] };
  if (o.error) failed.push('error: ' + String(o.error).slice(0, 160));
  if (o.subjectNotSet) failed.push('subject field did not take');
  if (o.term && o.term.verdict === 'wrong-term') failed.push(o.term.note);
  if (o.subject && o.subject.verdict === 'wrong-subject') failed.push(o.subject.note);
  if (o.uncoverable) failed.push("over Cal Poly's 300-section cap after every split");
  if (o.openOnly === 'STUCK-ON') failed.push('"Show Open Classes Only" stuck on');
  if (!o.term || o.term.verdict !== 'ok') unsafe.push('term not verified by dates');
  if (o.openOnlyLeak) unsafe.push('suspected open-only leak');
  if (o.capNote) unsafe.push('result-cap note on the page');
  const msgs = o.msgs || [];
  if (msgs.some(m => m && m !== 'no-results')) unsafe.push('search message ' + msgs.filter(m => m && m !== 'no-results').join(','));
  if (!o.count && !msgs.includes('no-results')) unsafe.push('zero sections without an explicit "no results"');
  return { failed: failed.length > 0, pruneSafe: failed.length === 0 && unsafe.length === 0, reasons: [...failed, ...unsafe] };
}

/* ---------------------------------------------------------- dropped sections ---- */

/* updated_at is stamped on every sighting, changed or not, so `now - updated_at` is "how long since
   any sweep saw this section". A section is pruned only when ALL of these hold:
     1. this sweep of its subject is pruneSafe (complete, verified term, verified subject),
     2. it was not in this sweep's results,
     3. no sweep has seen it for the grace period — 24h, or three cadence intervals if longer.
        During registration (every 20m) that is ~72 consecutive sweeps that did not see it;
        in a daily phase it is three days,
     4. pruning it would not remove more than half the subject (and at least the floor below) —
        a sweep that "completes" with most of a subject missing is a broken sweep, not a mass
        cancellation, and it is refused and reported instead. */
export const DROP_GRACE_MIN = 24 * 60;
export const DROP_CAP_FRACTION = 0.5;
export const DROP_CAP_FLOOR = 10;

export const dropGraceMinutes = every => Math.max(DROP_GRACE_MIN, every ? 3 * every : 0);

/**
 * @param {Array<{class_nbr:string, course_code:string, updated_at:string}>} existing  the term's rows for this subject, read AFTER this sweep's upsert
 * @param {Set<string>} seen     class numbers this sweep returned
 * @returns {{remove:string[], refused:boolean, reason:string, considered:number}}
 */
export function dropPlan({ existing, seen, subject, sweepStartedAt, graceMin }) {
  const want = String(subject || '').toUpperCase();
  const mine = (existing || []).filter(r => subjectOf(r.course_code) === want);
  const cutoff = new Date(new Date(sweepStartedAt).getTime() - graceMin * 60000).getTime();
  const remove = mine.filter(r => !seen.has(String(r.class_nbr)) && r.updated_at && new Date(r.updated_at).getTime() < cutoff)
    .map(r => String(r.class_nbr));
  const cap = Math.max(DROP_CAP_FLOOR, Math.floor(mine.length * DROP_CAP_FRACTION));
  if (!seen.size && remove.length) return { remove: [], refused: true, considered: mine.length, reason: `${want}: the sweep saw no sections, refusing to prune ${remove.length}` };
  if (remove.length > cap) return { remove: [], refused: true, considered: mine.length, reason: `${want}: ${remove.length} of ${mine.length} sections unseen for ${Math.round(graceMin / 60)}h — more than the cap of ${cap}. Refusing; check the subject by hand.` };
  return { remove, refused: false, considered: mine.length, reason: remove.length ? `${want}: pruning ${remove.length} section(s) unseen for over ${Math.round(graceMin / 60)}h` : '' };
}

/**
 * Apply dropPlan to every prune-safe subject of a lane: read the subject's rows, delete the ones
 * the plan names. Runs only AFTER the lane's upsert succeeded, so everything this sweep saw already
 * carries a fresh updated_at — and the DELETE re-checks `updated_at < cutoff` itself, so a row
 * that anything refreshed in the meantime survives. `fetchImpl` is injectable for check-sweep.mjs.
 * @returns {Promise<{removed:Array, refused:string[], skipped:string[]}>}
 */
export async function pruneDropped(report, { enabled, base, key, term, begin, graceMin, sweepStartedAt, fetchImpl = fetch, log = console }) {
  const out = { removed: [], refused: [], skipped: [] };
  if (!enabled) { log.log('• Pruning off (CP_PRUNE=0 or no Supabase credentials).'); return out; }
  if (!begin) { log.log(`• Pruning off for term ${term}: the calendar has no classes-begin date, so no sweep of it can be verified.`); return out; }
  const root = String(base).replace(/\/$/, '');
  const hdr = { apikey: key, Authorization: `Bearer ${key}` };
  const cutoff = new Date(new Date(sweepStartedAt).getTime() - graceMin * 60000).toISOString();
  for (const r of report) {
    if (!r.pruneSafe) { out.skipped.push(`${r.subject}: ${(r.reasons || []).join('; ') || 'not prune-safe'}`); continue; }
    if (!/^[A-Z]{1,8}$/.test(r.subject)) { out.skipped.push(`${r.subject}: not a plain subject code`); continue; }
    try {
      const got = await fetchImpl(`${root}/rest/v1/course_seats?term=eq.${encodeURIComponent(term)}&course_code=like.${encodeURIComponent(r.subject + ' *')}&select=class_nbr,course_code,updated_at&limit=5000`, { headers: hdr });
      if (!got.ok) { out.refused.push(`${r.subject}: could not read its rows (HTTP ${got.status})`); continue; }
      const existing = await got.json();
      const plan = dropPlan({ existing, seen: new Set(r.seen || []), subject: r.subject, sweepStartedAt, graceMin });
      if (plan.refused) { out.refused.push(plan.reason); log.error(`::warning title=Dropped-section prune refused (${r.subject}, term ${term})::${plan.reason}`); continue; }
      if (!plan.remove.length) continue;
      const del = await fetchImpl(`${root}/rest/v1/course_seats?term=eq.${encodeURIComponent(term)}&class_nbr=in.(${plan.remove.map(encodeURIComponent).join(',')})&updated_at=lt.${encodeURIComponent(cutoff)}`,
        { method: 'DELETE', headers: { ...hdr, Prefer: 'return=representation' } });
      if (!del.ok) { out.refused.push(`${r.subject}: delete failed (HTTP ${del.status}) ${String(await del.text()).slice(0, 160)}`); continue; }
      const gone = await del.json();
      out.removed.push(...gone.map(x => ({ subject: r.subject, class_nbr: x.class_nbr, course_code: x.course_code, section: x.section, last_seen: x.updated_at })));
      log.log(`• ${plan.reason}: ${gone.map(x => `${x.course_code} ${String(x.section || '').split(' ')[0]} #${x.class_nbr} (last seen ${String(x.updated_at).slice(0, 16)})`).join(', ')}`);
    } catch (e) {
      out.refused.push(`${r.subject}: ${String(e.message || e).slice(0, 160)}`);
    }
  }
  if (out.removed.length) log.log(`• Pruned ${out.removed.length} dropped section(s) from term ${term}.`);
  return out;
}

/* --------------------------------------------------------------- freshness ---- */

/* How old a term's data may get before someone is told. Two missed sweeps plus an hour, never
   under two hours: appointments (20m) 2h · open enrolment (60m) 3h · add/drop (180m) 7h ·
   a daily phase 49h. */
export const freshLimitMinutes = every => Math.max(2 * every + 60, 120);

/**
 * @param {Array} terms   plan.terms from cadence.planFor
 * @param {Object<string, Array<{course_code:string, updated_at:string}>>} rowsByTerm
 * @param {Date} now
 * @param {Object<string, string|null>} beginByCode  term code -> classes-begin (null = cannot prune)
 * @returns {{problems:string[], warnings:string[], lines:string[]}}
 */
export function freshnessReport(terms, rowsByTerm, now, beginByCode = {}) {
  const problems = [], warnings = [], lines = [];
  for (const t of terms || []) {
    if (!t.term_code || t.phase === 'dark' || t.every == null) {
      lines.push(`${t.label}: ${t.phase}${t.phase === 'dark' ? ' — not scraped, staleness expected' : ''}`);
      continue;
    }
    const rows = rowsByTerm[t.term_code];
    if (!rows) { warnings.push(`${t.label}: rows could not be read`); continue; }
    const limit = freshLimitMinutes(t.every);
    const age = iso => (now.getTime() - new Date(iso).getTime()) / 60000;
    if (!rows.length) { problems.push(`${t.label} (${t.term_code}) is ${t.phase} but has NO rows`); continue; }
    const newestBySubj = {};
    let newest = Infinity, lingering = 0;
    const linger = limit + dropGraceMinutes(t.every) + 24 * 60;
    for (const r of rows) {
      const a = age(r.updated_at);
      if (a < newest) newest = a;
      const s = subjectOf(r.course_code) || '(blank)';
      if (!(s in newestBySubj) || a < newestBySubj[s]) newestBySubj[s] = a;
      if (a > linger) lingering++;
    }
    const h = m => m >= 120 ? `${Math.round(m / 60)}h` : `${Math.round(m)}m`;
    lines.push(`${t.label} (${t.term_code}) ${t.phase}, every ${t.every}m: ${rows.length} rows, newest ${h(newest)} old (limit ${h(limit)})`);
    if (newest > limit) { problems.push(`${t.label}: newest row is ${h(newest)} old — limit ${h(limit)} for ${t.phase}. Sweeps are not landing.`); continue; }
    const behind = Object.entries(newestBySubj).filter(([, a]) => a > limit).sort((a, b) => b[1] - a[1]);
    if (behind.length) problems.push(`${t.label}: ${behind.length} subject(s) not refreshed within ${h(limit)}: ${behind.slice(0, 15).map(([s, a]) => `${s} ${h(a)}`).join(', ')}${behind.length > 15 ? ', …' : ''}`);
    if (lingering) {
      const msg = `${t.label}: ${lingering} row(s) unseen for over ${h(linger)} — dropped sections are not being pruned`;
      if (beginByCode[t.term_code]) problems.push(msg); else warnings.push(msg + ' (term has no classes-begin date, so pruning is off for it)');
    }
  }
  return { problems, warnings, lines };
}
