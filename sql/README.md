# sql/

The migrations, kept here so they stop living only in one person's `~/Downloads`.

**Nothing in this folder runs automatically.** Netlify never sees it; `netlify.toml` publishes an
allowlist and `sql/` is not on it. Every file here was pasted into the Supabase SQL editor by hand,
which is also the only way any of them should ever run again.

Read this before running anything:

- These are **not** an ordered, replayable migration set. They were written one at a time against a
  live database. Several have been superseded by later ones.
- Every file is written to be safe to run twice — guarded `do $$ ... if not exists ... $$`,
  `drop ... if exists`, policies dropped by *shape* rather than by name. That is a property of how
  they were written, not a guarantee about a database they have never seen.
- Verify against production before running any of them. `professify-audit-queries.sql` and
  `professify-check-functions.sql` exist for exactly that.

## Do not run

| File | Why |
|---|---|
| `professify-free-now.sql` | **Do not run.** It creates the `free_now` table for the "I'm free now" declaration, and Tate removed that control on 2026-09-05 — a timetable can show nothing is scheduled, only a person can say they are free, and with no control there is nobody to say it. Push kept the half a timetable can prove ("done for the day"), which needs none of this. Its other half, `profiles.pinned_friends`, is live and now lives in `professify-pinned-friends.sql`. Kept as the written-down version of a decision, not as something to execute. |
| `professify-phone-drop.sql` | Drops the phone-number lookup. **Tate decided on 2026-09-07 to keep it** for contact sync in the mobile app. It is here as the written-down version of a decision that was made and reversed, not as something to execute. |

## Not run yet

| File | State |
|---|---|
| `professify-share-cards.sql` | Written 2026-09-08. Lets the `schedule-cards` bucket accept `application/json` and tightens its INSERT policy. Until this runs, every shared-schedule link opens on "That schedule link has expired". See `claude/share-preview-2026-09-08.md`. |
| `professify-review-refusals.sql` | Written 2026-09-11. **Run this one first.** Raises the review cap 5 → 30 and adds the trigger that names WHICH of the four insert conditions refused a review — until it runs, every refusal still reaches the student as an unexplained "the server wouldn't accept that review", and the server cap is still 5 while the client says 30. Also installs `why_cant_i_review()`. Proven against a replica by `check-revsql.mjs`. See `claude/review-refusals-and-friend-emails-2026-09-11.md`. |
| `professify-friend-emails.sql` | Written 2026-09-11. Adds `friend_emails()` so accepted friends can see each other's school address for group projects, without re-granting the revoked column. Until it runs the contact row simply never appears — the client degrades silently and warns the console. |
| `professify-pinned-friends.sql` | Written 2026-09-12. Section 2 of `professify-free-now.sql`, lifted verbatim: `profiles.pinned_friends` plus the 2-pin check constraint. The Home feed still ranks pinned friends first and `epPins()` reads the column on every render, so without it pins silently do not save. Verified on a replica: installs, re-runs clean, two pins allowed, three refused. |
| `professify-term-scope.sql` | Written 2026-09-12. Adds `term` to `my_sections`, `saved_classes` and `watch_sections`, stamps everything that exists as `2268`, and widens each table's unique key to include it. Nothing changes on screen — with one term in the data, `(user_id, code, term)` is equivalent to `(user_id, code)`, which is why this is safe today and expensive on 5 October. Keys are discovered from the catalog, not assumed: these three tables were created outside this repo. Verified against two plausible shapes (natural PKs, and surrogate `id` plus a natural unique index), idempotent on both, and it refuses a partial index rather than rebuilding a copy without its predicate. |
| `professify-view-security.sql` | Written 2026-09-12, from the three CRITICAL "Security Definer View" warnings in the Supabase Advisor. Drops `professor_review_stats` (never read by anything since `supabase-setup.sql`); keeps `reviews_public` and `prof_activity_7d` as definer views on purpose and says why in a `comment on view`; revokes the unused direct grant on `prof_activity_7d` so `trending_profs()` is the only path. **Also fixes a real defect the Advisor could not see: `reviews_public` had no removed-review filter, so a review a moderator took down was still served to the public.** Proven against a replica as an anonymous reader by `check-viewsec.mjs`. |

## Confirmed live on production (checked 2026-09-07 / 2026-09-08)

| File | What was verified |
|---|---|
| `professify-length-limits.sql` | 33 `len_*` check constraints present |
| `professify-length-limits-2.sql` | 21 more; 55 total |
| `professify-phone-oracle.sql` | execute revoked from `public`; 3 hashes nulled |
| `professify-word-filter.sql` | 4 triggers live |
| `professify-analytics.sql` | `log_events` accepts `'error'`; `analytics_summary` returns the errors block |
| `professify-push.sql` | 3 tables, the seat-change trigger, 3 policies on `push_subscriptions`, 0 on `push_outbox` (deliberate — only the service role writes it) |
| `professify-missing-bits.sql` | `profiles.pinned_friends` and `get_inviter()` both present |
| `professify-schools.sql` | Run 2026-09-10; self-check clean — 24 profiles all stamped `calpoly`, the `profiles_read` policy is school-scoped, six RPCs scoped, no unscoped original callable by `authenticated`. It landed at the repo ROOT that day because GitHub's web uploader cannot place a file in a subfolder; moved here 2026-09-10. See `claude/deploy-2026-09-10.md`. |

## Everything else

Written before 2026-09-07 and **not re-verified in this session**. Most were run when written.
Check the object they create actually exists before assuming either way.
