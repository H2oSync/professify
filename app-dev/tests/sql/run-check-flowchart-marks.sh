#!/bin/sh
# Runs check-flowchart-marks.sql against a local Postgres 16 (PGHOST/PGPORT/PGUSER as usual).
set -e
cd "$(dirname "$0")/../../.."
createdb marktest
trap 'dropdb marktest' EXIT
psql -q -v ON_ERROR_STOP=1 -v sqlfile=sql/professify-flowchart-marks.sql -d marktest -f app-dev/tests/sql/check-flowchart-marks.sql
