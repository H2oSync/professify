# TermChamp: descriptions checked against the real catalog (build 2026-09-24 00:43)

This replaces the 2026-09-23 23:36 production-line build. **The only change is the code that cuts the description down to one line.** Everything else is pass 1 plus pass 2, unchanged.

## Why

On 09-24 all 2,062 real `course_catalog` rows were exported and run through the one-line cutter. The fixtures had been made up; this was the first run against Cal Poly's real text. It turned up:

| What | Rows | Before the fix, the card would have shown |
|---|---|---|
| The seat scraper saved the class-search page around the text for crosslisted courses | 114 | `Status Enrl Tot Wait Tot ME 4404-X01 LEC (6251) … Open 32 6 CE…` |
| Selected-topics courses open with a cut-off registrar link | 20 | `of the topic selected for this course can be found on the…` |
| Maritime courses open with a campus note | 41 | `Offered at Solano Campus` |
| Topic-list catalogs open with a two-word fragment | ~15 | `Partial derivatives` |
| A bracket was left open by the 96-character cut | 7 | `…food processing (unit conversion, mass and…` |
| "1 laboratory" wasn't recognised as a format line (old regex bug) | 1 | `1 laboratory` |

After the fix, all 2,045 semester-code courses get a line. None of those lines contains seat numbers, section codes, notes, requirements, "Formerly", "Also offered", a link or a format count. The 17 quarter-era rows are still ignored.

How each case is handled:

- **Page text around the description:** the text before the page's own "Description" label is cut away. Where a row has page text but no label, the card shows nothing rather than seat numbers.
- **Campus note, "Formerly …", "Also offered as …", "Repeatable …", "The Class Schedule will list …":** these sentences are skipped.
- **Short opening fragment:** it takes the next sentence with it, in Cal Poly's own words with its own full stops.
- **Open bracket:** the cut goes before the bracket.

It's still Cal Poly's own text, cut and never reworded. The one exception: one row (ME 4492L) starts with a lower-case fragment, and its first letter is capitalised.

## The source problem (not fixed here)

`seats/scrape-seats.mjs` stores the page chrome in `description` for crosslisted and selected-topics courses. The app now copes with that. The scraper should still save only the text after "Description", and `ps-client.mjs parseDetail` should capture the description the same way when it replaces the Playwright scraper. The table was left unchanged: no UPDATE, no DROP.

## Checks

- `check-mobile.mjs`: **98/98**, with 12 new catalog assertions built from the real shapes. The wording is fixture text and the numbers are invented.
- `mutate.mjs`: **54/54** mutations caught (was 43), including one for each new rule.
- check-ga 53/53, check-avatar 4/4, check-gebrowse 29/29.
- check-brand 23/25: the same two stale failures as before.
- Second-model review:
  - First pass: **SHIP WITH FIXES**. Picking the *last* "Description" label could silently drop the opening words of a description that itself says "Description" (e.g. "Hardware Description Language"). Fixed: the cut now uses the first label after the last piece of page text. Both cases have tests and mutations.
  - Re-review: **SHIP**. 0 differences across all 2,062 rows.

## Rebuild

    node patch/apply-mobile.mjs <live index.html> out/index.html <live sw.js> out/sw.js --build "YYYY-MM-DD HH:MM"

The Hawk line isn't rebuilt here. When Hawk is ready, run the same command on the Hawk session's build.

## Running the checks from this repo

    sh mobile/vendor/fetch.sh            # test-only deps, ~18 MB, not committed
    node mobile/check-mobile.mjs index.html
    SRC=index.html node mobile/mutate-par.mjs

`harness/harness.mjs` imports Playwright from `/opt/node-tools/node_modules/playwright`. Point that import at your own Playwright install to run it elsewhere.
