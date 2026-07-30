# Professify

A better RateMyProfessors for Cal Poly — every major's classes, who teaches them, and their **live ratings synced from [PolyRatings](https://polyratings.org)**. Plus first-year plans for all 65 Cal Poly majors and a best-professor schedule builder.

Live at **[professify.app](https://professify.app)**.

Built by students, for students. Ad-free. Verified `.edu` reviews only.

---

## What's in this repo

```
index.html              ← the entire app (one self-contained file: HTML + CSS + JS)
netlify.toml            ← deploy config
BACKEND-SETUP.md        ← how to turn on persistent, .edu-verified reviews (Supabase)
supabase-setup.sql      ← the database schema to run in Supabase
CONTRIBUTING.md         ← how to make changes without breaking the live site
```

There is **no build step**. The app is a single `index.html` you can open straight in a browser.

---

## Run it locally

Just open `index.html` in your browser — that's it. For a proper local server (so `fetch` and auth behave exactly like production):

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

The live PolyRatings sync only works in a real browser with internet — it fetches `https://api-prod.polyratings.org/professors.all` on load and attaches live ratings to each department's professors.

---

## How it's structured (all inside `index.html`)

- **`SCHOOLS`** — per-school config (term system, accent colors, ratings source, live/building status). Cal Poly is live; SDSU + UCSB are scaffolded.
- **`FLOWCHARTS`** — all 65 Cal Poly majors, first-year courses from the official 2026–28 catalog.
- **`MAJOR_CATALOG`** — core + concentration courses used by the "Explore classes" mode.
- **`CONFIRMED_SECTIONS`** — real confirmed Fall 2026 instructors (shown when we actually know who's teaching).
- **PolyRatings live sync** — `loadPolyRatings()` pulls every professor + rating and matches them to departments/courses.
- **Supabase reviews** — dormant until keys are added (see `docs/BACKEND-SETUP.md`); gates rating behind a verified `.edu` email.

### Core principle: **real data only**
We never invent a course, a professor, or a future teaching assignment. If we don't know who teaches a section, we show the top-rated professor *in that department* and say so — we don't guess. We plan **one year at a time** and only name an instructor when we actually know who it is.

---

## Deploy

The site auto-deploys from this repo via Netlify: **push to `main` → Netlify rebuilds professify.app** (see `netlify.toml`). No manual drag-and-drop needed once it's connected.

To turn on real persistent reviews, follow **`BACKEND-SETUP.md`** (about 15 minutes).

---

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)**. Short version: never commit straight to `main` — branch, open a pull request, let the Netlify preview build, then merge. That way the live site can't break.
