#!/bin/sh
# Runs check-registration-days.sql against a local Postgres 16 (PGHOST/PGPORT/PGUSER as usual).
set -e
cd "$(dirname "$0")/../../.."
W=$(mktemp)
trap 'rm -f "$W"; dropdb --if-exists regdaytest' EXIT
# RUN 7's wrap of the people functions (its section 5), as it would run after RUN 17
sed -n '/^-- 5\. Hidden while pending/,/^end \$\$;/p' ${RUN7:-sql/professify-delete-account-30-days.sql} > "$W"
for v in "0 0" "1 0" "0 1"; do
  set -- $v
  createdb regdaytest
  psql -q -v ON_ERROR_STOP=1 -v sqlfile=${SQLFILE:-sql/professify-registration-days.sql} -v pend=$1 -v late=$2 -v run7wrap="$W" -d regdaytest -f app-dev/tests/sql/check-registration-days.sql
  dropdb regdaytest
done
