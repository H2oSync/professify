#!/bin/sh
# Runs check-commitments.sql against a local Postgres 16 (PGHOST/PGPORT/PGUSER as usual).
set -e
cd "$(dirname "$0")/../../.."
W=$(mktemp)
trap 'rm -f "$W"; dropdb --if-exists cmtest' EXIT
# RUN 7's wrap of the people functions (its section 5), as it would run after RUN 18
sed -n '/^-- 5\. Hidden while pending/,/^end \$\$;/p' ${RUN7:-sql/professify-delete-account-30-days.sql} > "$W"
for v in "0 0" "1 0" "0 1"; do
  set -- $v
  createdb cmtest
  psql -q -v ON_ERROR_STOP=1 -v sqlfile=${SQLFILE:-sql/professify-commitments.sql} -v pend=$1 -v late=$2 -v run7wrap="$W" -d cmtest -f app-dev/tests/sql/check-commitments.sql
  dropdb cmtest
done
