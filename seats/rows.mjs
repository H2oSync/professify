/**
 * Professify — the two decisions in the scraper that can quietly corrupt the term.
 * ==============================================================================
 *
 * These lived inside scrape-seats.mjs, which imports Playwright and drives a browser, so nothing
 * could test them without a runner and a live site. Both had already been the subject of a
 * defect, and a mutation could revert either one with the whole suite still green. They are pure
 * functions of their inputs, so they live here instead and check-cadence.mjs runs them directly.
 */

/* The five columns that only exist when a section's detail page was opened. */
export const COUNT_COLS = ['capacity', 'enrolled', 'available', 'waitlist_total', 'waitlist_capacity'];

/**
 * Shape the rows for the Supabase upsert.
 *
 * WHY `withCounts` OMITS RATHER THAN NULLS. With CP_FETCH_DETAILS=0 the detail pages are never
 * opened, so capacity / enrolled / available / waitlist_* are never assigned — and `undefined ??
 * null` is `null`. Upserting that under `resolution=merge-duplicates` writes NULL over every real
 * number in the table and stamps updated_at as fresh, so the app shows blank seats on data it
 * believes is minutes old. That is the app inventing an answer.
 *
 * PostgREST leaves a column it was not sent alone, so the columns are omitted instead. It also
 * rejects an array whose objects have different keys, which is why `withCounts` is decided once
 * for the whole batch and never per row.
 */
export function buildUpsertRows(rows, { withCounts }) {
  return (rows || []).filter(r => r.class_nbr).map(r => {
    const row = {
      term: r.term, class_nbr: r.class_nbr, subject: r.subject, course_code: r.course_code, title: r.title,
      section: r.section, instructor: r.instructor, days: r.days, dates: r.dates, status: r.status,
      updated_at: r.updated_at,
      instruction_mode: r.instruction_mode || null, location: r.location || null, room: r.room || null,
    };
    if (withCounts) for (const k of COUNT_COLS) row[k] = r[k] ?? null;
    return row;
  });
}

/** Collapse cross-listed duplicates: Postgres refuses an upsert that hits one row twice. */
export function dedupeByClassNbr(rows) {
  const byKey = new Map();
  for (const r of rows) byKey.set(r.term + '|' + r.class_nbr, r);
  return [...byKey.values()];
}

/**
 * Is the page really showing the term we are about to stamp on every row?
 *
 * THREE SIGNALS, AND THEY ARE NOT INTERCHANGEABLE.
 *
 *   `back` — what the term field itself now holds. The only one that neighbouring text cannot
 *   contaminate, and the only one that is hard evidence. Required.
 *
 *   `label` — what the calendar says this code is. Without it there is nothing to compare
 *   anything against, and CFG.TERM defaults to a hardcoded value that outlives the term it names,
 *   so a label-less run sweeps a dead term and refreshes updated_at on months-old rows.
 *
 *   `echo` — the description PeopleSoft renders beside the field. Read from the field's
 *   container, which on some layouts also holds the Registrar's notice about when the NEXT term's
 *   schedule becomes available.
 *
 * The subtlety is that a failed echo match means two different things, and treating them alike
 * was a tripwire: "this text names a term and it is not ours" is real evidence and must refuse,
 * while "I could not read a term description at all" is evidence of nothing — and turning that
 * into a throw takes all 24 lanes red on every run for a layout that simply does not print a
 * description. So an unreadable echo DEGRADES to the field read-back and says so out loud; only a
 * contradicting echo refuses.
 *
 * @returns {{ok:true, degraded:boolean, note:string}}
 * @throws  when the term cannot be trusted
 */
export function confirmTerm({ code, label, echo, back }, termsNamedIn, matchesTerm) {
  if (!code) throw new Error('no term code to confirm');
  if (!label) {
    throw new Error(
      `CP_TERM=${code} was given with no CP_TERM_LABEL, so there is nothing to confirm it against. ` +
      `A wrong term code returns an EMPTY search that looks exactly like a term with no classes. ` +
      `Set CP_TERM_LABEL (e.g. "Fall 2026"), or clear CP_TERM and let the term be resolved.`);
  }
  if (String(back || '').trim() !== String(code).trim()) {
    throw new Error(`the term field reads "${back}" but we are about to label every row ${code}. Refusing.`);
  }
  const named = termsNamedIn(echo);
  if (named.length === 0) {
    return { ok: true, degraded: true, note: `no term description next to the term field (echo=${JSON.stringify(String(echo || '').slice(0, 80))}); proceeding on the field read-back alone` };
  }
  if (!matchesTerm(echo, label)) {
    throw new Error(`term ${code} does not name "${label}" — the page names ${JSON.stringify(named)}. Refusing to scrape a term we cannot identify.`);
  }
  return { ok: true, degraded: false, note: `term ${code} confirmed as ${label} (field reads "${back}")` };
}
