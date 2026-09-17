/**
 * Professify — the rule that says a results page and a row list belong together.
 * =============================================================================
 *
 * THE DEFECT THIS EXISTS TO MAKE IMPOSSIBLE (found 14 Sep 2026, live since the 300-cap split
 * landed). PeopleSoft refuses any search returning more than 300 sections, so a big subject is
 * sliced into two course-number bands and the two row lists are concatenated:
 *
 *     collected.push(...lowHalf.list, ...highHalf.list);
 *
 * The browser is then sitting on the HIGH band's results page — it was the last search run — and
 * the enrichment loop walks the combined list clicking `MTG_CLASS_NBR$i` for i = 0, 1, 2 …
 * Those ids are assigned by PeopleSoft in document order on WHATEVER PAGE IS CURRENTLY LOADED.
 * So for CSC, with ~200 low-band rows followed by ~286 high-band rows:
 *
 *   i = 0..285    a real link is clicked, and CSC 3000's seat counts are written onto
 *                 CSC 1010's row. Real numbers, wrong section, upserted clean.
 *   i = 286..485  getElementById returns null, the click is a no-op, and the wait for a
 *                 capacity block times out after 12 seconds — swallowed by .catch(() => {}).
 *                 200 rows x 12.1s is 40 minutes of a lane doing nothing at all.
 *
 * (The follow-up wait, for the results page to come back, returns immediately rather than adding
 * a second 12s: its condition — MTG_CLASS_NBR$0 present and the Back button absent — is already
 * true, because the page never left the result list. So the cost is ~12s per orphan row, not 24.)
 *
 * The performance half is what got noticed; the correctness half is the one that matters. An app
 * that shows no seat count says "we don't know". An app that shows another section's seat count
 * says something false, confidently, and the constraint this project runs on is that it must
 * never do that.
 *
 * The structural fix is in scrape-seats.mjs: enrich each band while ITS OWN result page is
 * loaded, then merge. This file holds the invariant that makes a regression loud instead of
 * silent, plus the band decision, both as pure functions a test can drive without a browser.
 */

/**
 * May this list be enriched against the page currently loaded?
 *
 * The list index IS the DOM id suffix — there is no other key tying a row to its link — so the
 * only safe state is a page whose link count matches the list exactly. Anything else means the
 * list came from a different search, and clicking by index would attribute one section's numbers
 * to another.
 *
 * @param {number} listLength  rows about to be enriched
 * @param {number} linkCount   MTG_CLASS_NBR$ anchors on the page right now
 * @returns {{ok:boolean, reason:string}}
 */
export function indexableAgainstPage(listLength, linkCount) {
  if (!Number.isInteger(listLength) || !Number.isInteger(linkCount)) {
    return { ok: false, reason: `non-integer counts (list=${listLength}, links=${linkCount})` };
  }
  if (listLength === 0) return { ok: true, reason: 'nothing to enrich' };
  if (linkCount === listLength) return { ok: true, reason: `${listLength} rows against ${linkCount} links` };
  if (linkCount < listLength) {
    return { ok: false, reason:
      `${listLength} rows but only ${linkCount} links on this page — ${listLength - linkCount} rows have no link, ` +
      `and every row that DOES get one is being matched to a section from a different search. ` +
      `This is the split-band defect: enrich each band while its own result page is loaded.` };
  }
  return { ok: false, reason:
    `${listLength} rows but ${linkCount} links on this page — the page holds sections this list does not, ` +
    `so index ${listLength - 1} is not the row it looks like. Refusing to attribute counts by position.` };
}

/**
 * Which course-number bands cover this subject?
 *
 * Pure: it is handed what each probe search reported and returns the plan, so the decision can be
 * tested without running a single search. `null` bands means no boundary worked and the subject
 * cannot be covered — which must be reported, never quietly under-reported.
 *
 * @param {boolean} wholeOverLimit   did the unbanded search blow the 300 cap?
 * @param {Array<{boundary:number, lowOverLimit:boolean, highOverLimit:boolean}>} attempts
 * @returns {{bands:Array<{op:string,num:number,label:string}>|null, boundary:number|null, label:string}}
 */
export function bandPlan(wholeOverLimit, attempts = []) {
  if (!wholeOverLimit) {
    return { bands: [{ op: 'G', num: 0, label: 'all' }], boundary: null, label: 'all' };
  }
  for (const a of attempts) {
    if (!a.lowOverLimit && !a.highOverLimit) {
      return {
        bands: [
          { op: 'L', num: a.boundary - 1, label: `<=${a.boundary - 1}` },
          { op: 'G', num: a.boundary, label: `>=${a.boundary}` },
        ],
        boundary: a.boundary,
        label: `<=${a.boundary - 1} + >=${a.boundary}`,
      };
    }
  }
  return { bands: null, boundary: null, label: 'UNCOVERABLE' };
}

/**
 * Merge bands and drop any section seen twice.
 *
 * Bands are disjoint by construction (<= b-1 and >= b), so this is belt and braces — but a future
 * finer split could overlap, and Postgres rejects an upsert that touches one row twice, which
 * would take a whole lane's write down rather than just duplicating a row.
 */
export function mergeBands(lists) {
  const seen = new Set();
  const out = [];
  for (const list of lists) {
    for (const x of list || []) {
      const k = String(x.class_nbr || '') + '|' + String(x.section || '') + '|' + String(x.course_code || '');
      if (seen.has(k)) continue;
      seen.add(k);
      out.push(x);
    }
  }
  return out;
}
