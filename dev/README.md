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
| `ask` Edge Function | `cd dev && deno run --allow-env --allow-read tests/check-ask-function.ts` | 59/59 (2026-10-08) |
| Champ golden set, offline — every build (shape, reachable answers, scorer can fail, coverage, scored-menu gate) | `deno run --allow-read --allow-env dev/golden/check-golden.ts` | 13/13 — not scored yet |
| Router golden set | `node dev/golden/check-router-golden.mjs` | 82/82 |
| Plans SQL (Postgres 16) | `psql -f dev/tests/fixture-plans.sql -f sql/professify-plans.sql -f dev/tests/check-plans.sql` | all ok |
| Hawk SQL through v8 | `fixture.sql`, `professify-assistant.sql`…`-v8.sql`, `check-hawk-misses.sql`, `check-assistant-v6.sql`, `check-assistant-v7.sql`, `check-assistant-v8.sql` | all ok |
| **Champ model gate (needs the key, run by Tate before deploying `ask`)** — 376 questions, phone menu vs website menu, fails on errors, under 80%, a loss on old-tool questions, or a drop below the accepted rate | `npx deno run --allow-net --allow-env --allow-read --allow-write dev/golden/check-models-v3.ts --accept` | — |
| Website model comparison (older; the 2026-09-26 set) | `dev/golden/model-golden-v2.json`, results in `model-results-v2-2026-09-26.json` | Haiku 89.7% |
