#!/bin/sh
# Local only. Usage: sh tests/run-push-endpoint.sh   (from /tmp/claude-0/sec/sql)
cd "$(dirname "$0")/.."
q(){ psql -q -d sec_push -At -c "$1"; }
show(){ psql -q -d sec_push -f tests/check-push-endpoint.sql 2>&1 | grep -v '^$\|^---\|row)\|  try'; }
mig(){ psql -q -v ON_ERROR_STOP=1 -d sec_push -f professify-security-push-endpoint.sql 2>&1 | cut -c1-170; }
state(){ q "select 'constraint ' || conname || ' validated=' || convalidated from pg_constraint where conname='push_subs_endpoint_is_push_service'"; }
dropdb --if-exists sec_push 2>/dev/null; createdb sec_push
psql -q -d sec_push -f scratch/scaffold.sql; psql -q -d sec_push -f scratch/push-subs-only.sql 2>/dev/null
echo "#### BEFORE: student saves endpoints through RLS"; show
echo "#### RUN 1 (4 bad old rows present)"; mig; state
echo "#### student writes while constraint is NOT VALID (4 bad old rows still there, untouched)"; show
echo "#### RUN 2 same state -> still warns, still not validated, no error"; mig; state
echo "#### remove the bad old rows, RUN 3 -> validates; RUN 4 -> no-op"; q "delete from public.push_subscriptions where endpoint ~ 'attacker|169[.]254|^http:'" >/dev/null; mig; state; mig; state
echo "#### AFTER (validated): student writes"; q "delete from public.push_subscriptions" >/dev/null; show
