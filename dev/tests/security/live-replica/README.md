# Live-replica test for the security SQL (2026-10-14)

`gen.py` turns a read-only catalog snapshot of production (tables, columns, RLS policies, grants,
function bodies, views, triggers — no rows) into `replica.sql`, which rebuilds the same rules on a
local Postgres 16 (after `../scaffold.sql`). Push/seat/email triggers are skipped. The snapshot and
the generated `replica.sql` are NOT committed (they spell out every rule); regenerate them with the
catalog query in the review doc.

Order used on 2026-10-14: scaffold → replica → seed → probe (probe-before.txt) →
professify-security-hotfix-2026-10-14.sql (twice) → probe (probe-after.txt) →
assistant-spend (twice) → nan.sql → push-endpoint → friend-text-shapes. All passed.
Local only. Never run against production.
