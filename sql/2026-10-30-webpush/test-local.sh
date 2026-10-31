#!/bin/bash
# Runs sql/test-local.sql on a throwaway Postgres 16 under /tmp/claude-0/fix/webpush/pg (port 5641).
set -e
D=/tmp/claude-0/fix/webpush; B=/usr/lib/postgresql/16/bin; PORT=5641
OLD=$(stat -c %a /tmp/claude-0)
chmod o+x /tmp/claude-0; trap 'su postgres -c "$B/pg_ctl -D $D/pg -m fast stop" >/dev/null 2>&1 || true; chmod $OLD /tmp/claude-0' EXIT
rm -rf $D/pg $D/pgrun; mkdir -p $D/pgrun $D/pg; chown postgres $D/pgrun $D/pg; chmod 700 $D/pg; chmod o+rx $D $D/sql
sed '/cron\./d' $D/sql/99-rollback.sql > $D/sql/99-rollback-noncron.sql
su postgres -c "$B/initdb -D $D/pg -A trust -U postgres >/dev/null"
su postgres -c "$B/pg_ctl -D $D/pg -o '-p $PORT -k $D/pgrun -c listen_addresses=' -l $D/pgrun/log -w start >/dev/null"
cd $D/sql && su postgres -c "psql -h $D/pgrun -p $PORT -U postgres -X -q -v ON_ERROR_STOP=1 -f test-local.sql postgres"
