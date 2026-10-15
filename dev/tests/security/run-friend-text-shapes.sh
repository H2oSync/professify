#!/bin/sh
# Local only. Usage: sh tests/run-friend-text-shapes.sh   (from /tmp/claude-0/sec/sql)
cd "$(dirname "$0")/.."
show(){ psql -q -d sec_shapes -f tests/check-friend-text-shapes.sql 2>&1 | grep -v '^$\|^---\|row)\|   w  *$\|^ *w *$'; }
dropdb --if-exists sec_shapes 2>/dev/null; createdb sec_shapes
psql -q -v ON_ERROR_STOP=1 -d sec_shapes -f scratch/scaffold.sql -f scratch/shapes-replica.sql
echo "#################### BEFORE"; show
echo "#################### OLD BAD ROWS then RUN 1"
psql -q -d sec_shapes -c "insert into saved_classes(user_id,term,code) values ('88888888-8888-8888-8888-888888888888','2268','old junk row'); insert into class_history(user_id,code,term,year) values ('88888888-8888-8888-8888-888888888888','OLD 101','Wtr',1975)"
psql -q -v ON_ERROR_STOP=1 -d sec_shapes -f professify-security-friend-text-shapes.sql 2>&1 | cut -c1-260
echo "#################### AFTER RUN 1"; show
echo "#################### RUN 2 (idempotent)"; psql -q -v ON_ERROR_STOP=1 -d sec_shapes -f professify-security-friend-text-shapes.sql 2>&1 | cut -c1-200
psql -d sec_shapes -Atc "select 'old rows untouched: ' || (select count(*) from saved_classes where code='old junk row') || ' / ' || (select count(*) from class_history where code='OLD 101')"
echo "#################### MISSING / WRONG-TYPE TABLES (table class_history absent; my_sections.class_nbr is integer; year is text)"
dropdb --if-exists sec_shapes2 2>/dev/null; createdb sec_shapes2
psql -q -v ON_ERROR_STOP=1 -d sec_shapes2 -f scratch/scaffold.sql
psql -q -d sec_shapes2 -c "create table saved_classes (user_id uuid, term text, code text); create table my_sections (user_id uuid, term text, code text, class_nbr integer);"
psql -q -v ON_ERROR_STOP=1 -d sec_shapes2 -f professify-security-friend-text-shapes.sql 2>&1 | cut -c1-200
psql -d sec_shapes2 -Atc "select conname from pg_constraint where conname ~ '_(shape|digits|quarter|range)$' order by 1"
