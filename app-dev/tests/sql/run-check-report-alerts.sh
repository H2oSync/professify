#!/bin/sh
# Runs check-report-alerts.sql on a local Postgres 16. pg_net isn't installed locally: the migration
# is copied with its "create extension" line made a no-op; the test supplies stub cron, net and vault.
set -e
cd "$(dirname "$0")/../../.."
MIG=$(mktemp /tmp/report-alerts-XXXX.sql)
sed 's/^    create extension if not exists pg_net with schema extensions;$/    null;  -- (local test: stub net schema)/' sql/professify-report-alerts.sql > "$MIG"
grep -q 'stub net schema' "$MIG" || { echo 'pg_net line not found'; exit 1; }
chmod o+r "$MIG"
${PSQL:-psql} -q -v ON_ERROR_STOP=1 -v mig="$MIG" -f app-dev/tests/sql/check-report-alerts.sql
