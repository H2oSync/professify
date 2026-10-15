#!/bin/sh
# Local only. Builds the assistant tables from the repo's real SQL (v1..v8), shows the exploit, runs the file twice, shows the fix.
cd "$(dirname "$0")/.."; R=/tmp/claude-0/sec/repo
dropdb --if-exists sec_assist 2>/dev/null; createdb sec_assist
psql -q -v ON_ERROR_STOP=1 -d sec_assist -f scratch/scaffold.sql
for f in professify-assistant professify-assistant-v2 professify-assistant-v3 professify-assistant-v4 professify-assistant-v5 professify-assistant-v6 professify-assistant-v7 professify-assistant-v8; do psql -q -v ON_ERROR_STOP=1 -d sec_assist -f $R/sql/$f.sql >/dev/null 2>&1; done
F='^$\|^---\|row)\|^(1'
echo "#################### BEFORE (v8 live)"; psql -q -d sec_assist -f tests/check-assistant-spend.sql 2>&1 | grep -v "$F\|set_config\|^ *{"
for i in 1 2; do echo "#################### RUN $i"; psql -q -v ON_ERROR_STOP=1 -d sec_assist -f professify-security-assistant-spend.sql 2>&1; done
echo "#################### AFTER"; psql -q -d sec_assist -f tests/check-assistant-spend.sql 2>&1 | grep -v "$F\|set_config\|^ *{"
echo "#################### ceiling test"; psql -q -v ON_ERROR_STOP=1 -d sec_assist -f tests/check-assistant-spend-ceiling.sql 2>&1 | grep -v "set_config\|^ *{\|^---\|^$\|row)\|b_ok\|^ t$\|^ *b_big\|c51"
echo "#################### existing v6/v7/v8 checks against the new function"
for v in v6 v7 v8; do psql -q -v ON_ERROR_STOP=1 -d sec_assist -f $R/dev/tests/check-assistant-$v.sql 2>&1 | tail -1; done
