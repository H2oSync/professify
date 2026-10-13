#!/bin/sh
# Runs check-friends-of.sql against a local Postgres 16 (PGHOST/PGPORT/PGUSER as usual).
set -e
cd "$(dirname "$0")/../../.."
createdb foftest
trap 'dropdb foftest' EXIT
psql -q -v ON_ERROR_STOP=1 -v sqlfile=${SQLFILE:-sql/professify-friends-of-blocks.sql} -d foftest -f app-dev/tests/sql/check-friends-of.sql
dropdb foftest; createdb foftest
psql -q -v ON_ERROR_STOP=1 -v sqlfile=${SQLFILE:-sql/professify-friends-of-blocks.sql} -d foftest -f app-dev/tests/sql/check-friends-of-wrapped.sql
