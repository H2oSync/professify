#!/bin/sh
# Runs check-planner.sql on a local Postgres 16. pg_cron, pg_net and the Vault aren't installed locally:
# the migration's "create extension" lines are inside a guarded block already, and the test supplies
# stub cron, net and vault schemas. Usage: sh app-dev/tests/sql/run-check-planner.sh  (PSQL=... to override)
set -e
cd "$(dirname "$0")/../../.."
MIG=$(mktemp /tmp/planner-XXXX.sql); cp sql/professify-planner.sql "$MIG"; chmod o+r "$MIG"
DB=plannertest_$$
${CREATEDB:-createdb} "$DB"
trap '${DROPDB:-dropdb} "$DB"' EXIT
${PSQL:-psql} -q -v ON_ERROR_STOP=1 -v mig="$MIG" -d "$DB" -f app-dev/tests/sql/check-planner.sql
