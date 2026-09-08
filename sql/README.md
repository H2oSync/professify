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
| `professify-phone-drop.sql` | Drops the phone-number lookup. **Tate decided on 2026-09-07 to keep it** for contact sync in the mobile app. It is here as the written-down version of a decision that was made and reversed, not as something to execute. |

## Not run yet

| File | State |
|---|---|
| `professify-share-cards.sql` | Written 2026-09-08. Lets the `schedule-cards` bucket accept `application/json` and tightens its INSERT policy. Until this runs, every shared-schedule link opens on "That schedule link has expired". See `claude/share-preview-2026-09-08.md`. |
| `professify-free-now.sql` | Checked on production 2026-09-08: `free_now` does not exist. Never run. |

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

## Everything else

Written before 2026-09-07 and **not re-verified in this session**. Most were run when written.
Check the object they create actually exists before assuming either way.
