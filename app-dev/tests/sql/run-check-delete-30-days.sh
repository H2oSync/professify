#!/bin/sh
# Runs check-delete-30-days.sql against a local Postgres 16 (PGHOST/PGPORT/PGUSER as usual).
# pg_cron isn't installed locally: the migration is copied with its "create extension" line made a
# no-op, and the test supplies a stub cron schema. Everything else runs exactly as written.
set -e
cd "$(dirname "$0")/../../.."
MIG=$(mktemp /tmp/delete-30-days-XXXX.sql)
sed 's/^    create extension if not exists pg_cron;$/    null;  -- (local test: stub cron schema)/' sql/professify-delete-account-30-days.sql > "$MIG"
grep -q 'stub cron schema' "$MIG" || { echo 'cron line not found'; exit 1; }
psql -q -v ON_ERROR_STOP=1 -v mig="$MIG" -f app-dev/tests/sql/check-delete-30-days.sql
