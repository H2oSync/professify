#!/bin/bash
# Local Postgres 16: fresh cluster, the production stand-in, the contacts SQL twice (idempotent), the checks.
set -e
D=/tmp/claude-0/fix/contacts; PG=/usr/lib/postgresql/16/bin; PORT=${PORT:-5547}
OLD=$(stat -c %a /tmp/claude-0); chmod o+x /tmp/claude-0; trap 'su postgres -c "$PG/pg_ctl -D $D/pg stop -m fast" >/dev/null 2>&1 || true; chmod $OLD /tmp/claude-0' EXIT
rm -rf $D/pg; mkdir -p $D/pg; chown postgres $D/pg
su postgres -c "$PG/initdb -D $D/pg -A trust" >/dev/null
su postgres -c "$PG/pg_ctl -D $D/pg -o '-p $PORT -k /tmp' -l $D/pg/log start -w" >/dev/null
P="$PG/psql -h /tmp -p $PORT -U postgres -d postgres -v ON_ERROR_STOP=1 -q"
cp ${SQL:-$D/termchamp-contacts-2026-10-30.sql} /tmp/termchamp-contacts-2026-10-30.sql && cp $D/tests/standin.sql $D/tests/contacts-sql-test.sql /tmp/ && chmod 644 /tmp/termchamp-contacts-2026-10-30.sql /tmp/standin.sql /tmp/contacts-sql-test.sql
su postgres -c "$P -f /tmp/standin.sql"
su postgres -c "$P -f /tmp/termchamp-contacts-2026-10-30.sql"
su postgres -c "$P -f /tmp/termchamp-contacts-2026-10-30.sql"
su postgres -c "$P -f /tmp/contacts-sql-test.sql" 2>&1
rm -f /tmp/termchamp-contacts-2026-10-30.sql /tmp/standin.sql /tmp/contacts-sql-test.sql
