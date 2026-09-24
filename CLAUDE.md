# TermChamp (formerly Professify)

Professor ratings, seat counts, schedules and friends for Cal Poly students. Live at
**termchamp.com**; professify.app is a permanent alias that 301s there (see `netlify.toml`).

## Layout

- `index.html` — the entire app: HTML + inline CSS + inline JS, ~3 MB, no build step. Search it
  with grep/Grep and edit in place; never read it whole.
- `invite.html`, `sw.js`, `manifest.webmanifest`, icons, share cards — the other public files.
- `netlify.toml` — deploy config. Publishes an **allowlist** into `public/`: a new public file is
  not served until it is added to `OPTIONAL` in the build command.
- `netlify/edge-functions/share.ts` — `/s` shared-schedule link previews.
- `supabase/functions/push-send/` — push notification sender.
- `sql/` — hand-run Supabase migrations. Nothing here runs automatically. Read `sql/README.md`
  (the "Do not run" and "Not run yet" tables) before touching any of it.
- `seats/` — the Cal Poly seat scraper, run by `.github/workflows/update-seats.yml` on the
  registrar's calendar (`seats/registrar-calendar.json`, gated by `seats/cadence.mjs`).
- `check-*.mjs` — Playwright checks against `index.html`.

## House rules (from CONTRIBUTING.md)

1. **Never push to `main`.** Branch → PR → check the Netlify deploy preview → merge. Small PRs.
2. **Real data only.** Never invent a course code, professor, section or teaching assignment.
   Missing data beats fake data.
3. **Keep it one file.** No framework, no bundler, no external scripts beyond what the CSP in
   `netlify.toml` already allows. A new external host needs a CSP change too.
4. **Mobile first.** Most students are on phones.

## Things that look renameable and are not

The rename to TermChamp changed only what a student reads. These stay exactly as they are:

- Every `professify-*` / `professify_*` localStorage key. Renaming one silently logs students
  out and wipes their cached classes: no error, it just looks like a new user.
- `window.PROFESSIFY_BUILD`, `professifyDiag()`, and the `professify.app` domain.
- Comments that say "Professify". They are a dated record of decisions, not copy.

Never find-and-replace "professify" across `index.html`. `check-brand.mjs` exists to catch this.

## Style

Comments in this repo are long, dated (`2026-09-16`) and explain *why*, including what went
wrong before. Match that when changing non-obvious behaviour; keep old dated notes intact.

## Checks

The SessionStart hook (`.claude/hooks/session-start.sh`) links Playwright so these run as-is:

```bash
node check-brand.mjs      # the rename: name gone from UI, every identifier still in place
node check-gebrowse.mjs   # GE browser in Explore
cd seats && node plan.mjs # which terms the seat scraper would pull right now
```

Both checks default to this checkout's `index.html`; set `PAGE=file:///abs/path.html` to point
them at a deliberately broken copy (mutation testing). Run `check-brand.mjs` after any change
that touches the app's name, storage keys or head metadata.

Known as of 2026-09-24: `check-brand.mjs` reports 2 failures ("the wordmark in the header" and
"they all agree") because the 2026-09-17 build replaced the `.brand-name` text wordmark with the
capital TC image mark. The check needs updating, not the app.
