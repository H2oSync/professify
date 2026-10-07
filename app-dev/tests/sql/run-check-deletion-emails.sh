#!/bin/sh
# Runs check-deletion-emails.sql on a local Postgres 16, after check-delete-30-days.sql (its stand-in
# and migration). pg_cron and pg_net aren't installed locally: the migrations are copied with their
# "create extension" lines made no-ops; the tests supply stub cron, net and vault schemas.
set -e
cd "$(dirname "$0")/../../.."
MIG=$(mktemp /tmp/delete-30-days-XXXX.sql); MIG2=$(mktemp /tmp/deletion-emails-XXXX.sql); MIG3=$(mktemp /tmp/group-names-XXXX.sql)
sed 's/^    create extension if not exists pg_cron;$/    null;  -- (local test: stub cron schema)/' sql/professify-delete-account-30-days.sql > "$MIG"
sed 's/^    create extension if not exists pg_net with schema extensions;$/    null;  -- (local test: stub net schema)/' sql/professify-deletion-emails.sql > "$MIG2"
cp sql/professify-group-names-filter.sql "$MIG3"
grep -q 'stub cron schema' "$MIG" || { echo 'cron line not found'; exit 1; }
grep -q 'stub net schema' "$MIG2" || { echo 'pg_net line not found'; exit 1; }
chmod o+r "$MIG" "$MIG2" "$MIG3"
${PSQL:-psql} -q -v ON_ERROR_STOP=1 -v mig="$MIG" -f app-dev/tests/sql/check-delete-30-days.sql
${PSQL:-psql} -q -v ON_ERROR_STOP=1 -v mig2="$MIG2" -v mig3="$MIG3" -f app-dev/tests/sql/check-deletion-emails.sql
