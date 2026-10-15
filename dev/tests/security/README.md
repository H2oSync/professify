# Security SQL tests (2026-10-14)

Local-only tests for the three `sql/professify-security-*.sql` files. They run on a local Postgres 16
that emulates Supabase's roles and `auth.uid()` (`scaffold.sql`), with replicas of the tables the repo
doesn't define (`shapes-replica.sql`, `push-subs-only.sql`). The `run-*.sh` scripts were written in the
review sandbox and still point at its paths (`/tmp/claude-0/sec/...`); set `R` and the working
directory to your checkout before running. Never run these against production.
