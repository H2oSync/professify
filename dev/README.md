# dev/ — how this build was made, and how to check it

`index.html` at the repo root is the production line (2026-09-24 19:34) with three replayable
patch scripts applied, in order. Every anchor must match exactly once or a script refuses:

    node dev/apply-hawk.mjs <dir> && node dev/apply-sep24.mjs <dir> && node dev/apply-plans.mjs <dir>

`apply-plans.mjs` inlines `dev/plans/plans.js` and `dev/plans/plans.css` between the PLANS markers,
so edit those two files and re-run — never hand-edit the inlined copy.

## Checks
| Check | How | Result on this build |
|---|---|---|
| Plans, Planner, game plan (desktop + phone, touch, keyboard, contrast in dark/light/cream) | `node dev/check-plans.mjs` (cwd = folder with index.html + hawk files; needs Playwright) | 165/165 |
| Hawk | `node dev/mock-ask.mjs &` then `node dev/check-hawk.mjs` | 264/264 |
| `ask` Edge Function | `deno run --allow-env --allow-read dev/tests/check-ask-function.ts` | 38/38 |
| Router golden set | `node dev/golden/check-router-golden.mjs` | 82/82 |
| Plans SQL (Postgres 16) | `psql -f dev/tests/fixture-plans.sql -f sql/professify-plans.sql -f dev/tests/check-plans.sql` | all ok |
| Hawk SQL through v6 | `fixture.sql`, `professify-assistant.sql`…`-v6.sql`, `check-hawk-misses.sql`, `check-assistant-v6.sql` | all ok |
| Model comparison (needs the key, run by Tate) | `deno run --allow-net --allow-env --allow-read --allow-write dev/golden/check-models.ts` | — |
