#!/bin/bash
# Tests 2026-10-30-last-messages.sql on a scratch Postgres 16 with the repo's real messaging tables + RLS.
# Usage: bash sql-last-messages.sh   (starts a scratch server in /tmp/claude-0/fix/scale/pg on port 5571, stops it after)
set -e
chmod o+x /tmp/claude-0
PG=/usr/lib/postgresql/16/bin; D=/tmp/claude-0/fix/scale/pg
mkdir -p $D; chown postgres $D
[ -d $D/d ] || su postgres -c "$PG/initdb -D $D/d -A trust >/dev/null"
su postgres -c "$PG/pg_ctl -D $D/d -o '-p 5571 -k $D' -l $D/log -w start" >/dev/null
trap 'su postgres -c "$PG/pg_ctl -D $D/d -m fast -w stop" >/dev/null; chmod o-x /tmp/claude-0' EXIT
R=/home/claude/tc/app-icon/sql; F=/tmp/claude-0/fix/scale; W=$F/pg/work; mkdir -p $W; chmod 777 $W
PSQL="psql -X -q -v ON_ERROR_STOP=1 -h $F/pg -p 5571"
su postgres -c "$PSQL -d postgres -c 'set client_min_messages=warning' -c 'drop database if exists lm' -c 'create database lm'"
cat > $W/stub.sql <<'S'
do $$ begin create role anon nologin; exception when duplicate_object then null; end $$;
do $$ begin create role authenticated nologin; exception when duplicate_object then null; end $$;
create schema auth; grant usage on schema auth to anon, authenticated;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $f$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $f$;
grant execute on function auth.uid() to anon, authenticated;
grant usage on schema public to anon, authenticated;
create table public.friend_requests (id bigserial primary key, from_user uuid, to_user uuid, status text);
create function public.is_suspended(u uuid) returns boolean language sql stable as $f$ select false $f$;
create function public.blocked_between(a uuid, b uuid) returns boolean language sql stable as $f$ select false $f$;
S
sed -n '/^create table if not exists public.conversations (/,/^revoke all on public.professor_suggestions from anon;/p' $R/professify-messaging.sql | grep -v professor_suggestions > $W/msg.sql
cp $R/professify-chat-likes-hides.sql $W/lh.sql; cp $F/2026-10-30-last-messages.sql $W/lm.sql
cat > $W/test.sql <<'S'
\set ON_ERROR_STOP 1
-- A in c1 (busy, 500 msgs) c2 (quiet, 2) c3 (all newest hidden by A) c4 (cleared by A, nothing after) ; B alone in c5
insert into auth.users values ('a0000000-0000-4000-8000-000000000001'),('b0000000-0000-4000-8000-000000000002');
insert into public.conversations (id, created_by) values
 ('c0000000-0000-4000-8000-000000000001','a0000000-0000-4000-8000-000000000001'),('c0000000-0000-4000-8000-000000000002','a0000000-0000-4000-8000-000000000001'),
 ('c0000000-0000-4000-8000-000000000003','a0000000-0000-4000-8000-000000000001'),('c0000000-0000-4000-8000-000000000004','a0000000-0000-4000-8000-000000000001'),
 ('c0000000-0000-4000-8000-000000000005','b0000000-0000-4000-8000-000000000002');
insert into public.conversation_members (conversation_id, user_id) select c, 'a0000000-0000-4000-8000-000000000001' from unnest(array['c0000000-0000-4000-8000-000000000001','c0000000-0000-4000-8000-000000000002','c0000000-0000-4000-8000-000000000003','c0000000-0000-4000-8000-000000000004']::uuid[]) c;
insert into public.conversation_members values ('c0000000-0000-4000-8000-000000000005','b0000000-0000-4000-8000-000000000002');
insert into public.messages (conversation_id, sender, body, created_at)
  select 'c0000000-0000-4000-8000-000000000001', 'a0000000-0000-4000-8000-000000000001', 'c1 #' || g, timestamptz '2026-10-01' + g * interval '1 minute' from generate_series(1, 500) g;
insert into public.messages (conversation_id, sender, body, created_at) values
  ('c0000000-0000-4000-8000-000000000002','a0000000-0000-4000-8000-000000000001','c2 old','2026-09-01'),('c0000000-0000-4000-8000-000000000002','a0000000-0000-4000-8000-000000000001','c2 new','2026-09-02'),
  ('c0000000-0000-4000-8000-000000000003','a0000000-0000-4000-8000-000000000001','c3 keep','2026-09-01'),('c0000000-0000-4000-8000-000000000004','a0000000-0000-4000-8000-000000000001','c4 before clear','2026-09-01'),
  ('c0000000-0000-4000-8000-000000000005','b0000000-0000-4000-8000-000000000002','c5 secret','2026-09-01');
insert into public.messages (conversation_id, sender, body, created_at)
  select 'c0000000-0000-4000-8000-000000000003', 'a0000000-0000-4000-8000-000000000001', 'c3 hidden ' || g, timestamptz '2026-09-05' + g * interval '1 minute' from generate_series(1, 5) g;
insert into public.message_hides (message_id, user_id) select id, 'a0000000-0000-4000-8000-000000000001' from public.messages where body like 'c3 hidden%';
insert into public.conversation_clears values ('c0000000-0000-4000-8000-000000000004','a0000000-0000-4000-8000-000000000001','2026-09-10');
-- as A, through RLS
set role authenticated; select set_config('request.jwt.claim.sub', 'a0000000-0000-4000-8000-000000000001', false);
create temp table r as select conversation_id, body from public.last_messages(array['c0000000-0000-4000-8000-000000000001','c0000000-0000-4000-8000-000000000002','c0000000-0000-4000-8000-000000000003','c0000000-0000-4000-8000-000000000004','c0000000-0000-4000-8000-000000000005']::uuid[], 3);
select conversation_id, string_agg(body, ' | ') from r group by 1 order by 1;
do $$ declare n int; b text; begin
  select count(*) into n from r where conversation_id = 'c0000000-0000-4000-8000-000000000001'; if n <> 3 then raise exception 'FAIL busy chat rows %', n; end if;
  select string_agg(body, ',' order by body) into b from r where conversation_id = 'c0000000-0000-4000-8000-000000000001'; if b <> 'c1 #498,c1 #499,c1 #500' then raise exception 'FAIL busy chat newest: %', b; end if;
  select string_agg(body, ',') into b from r where conversation_id = 'c0000000-0000-4000-8000-000000000002'; if b <> 'c2 new,c2 old' then raise exception 'FAIL quiet chat (newest first): %', b; end if;
  select string_agg(body, ',') into b from r where conversation_id = 'c0000000-0000-4000-8000-000000000003'; if b <> 'c3 keep' then raise exception 'FAIL hides skipped: %', b; end if;
  select count(*) into n from r where conversation_id = 'c0000000-0000-4000-8000-000000000004'; if n <> 0 then raise exception 'FAIL clear respected: %', n; end if;
  select count(*) into n from r where conversation_id = 'c0000000-0000-4000-8000-000000000005'; if n <> 0 then raise exception 'FAIL RLS: read a chat A is not in'; end if;
  raise notice 'ok   newest per chat, hides + clears skipped, RLS keeps out other chats';
end $$;
-- default per_conv, clamp 0 -> 1 and 999 -> 20
do $$ declare n int; begin
  select count(*) into n from public.last_messages(array['c0000000-0000-4000-8000-000000000001']::uuid[]); if n <> 3 then raise exception 'FAIL default 3: %', n; end if;
  select count(*) into n from public.last_messages(array['c0000000-0000-4000-8000-000000000001']::uuid[], 0); if n <> 1 then raise exception 'FAIL clamp low: %', n; end if;
  select count(*) into n from public.last_messages(array['c0000000-0000-4000-8000-000000000001']::uuid[], 999); if n <> 20 then raise exception 'FAIL clamp high: %', n; end if;
  select count(*) into n from public.last_messages(array[]::uuid[]); if n <> 0 then raise exception 'FAIL empty'; end if;
  select count(*) into n from public.last_messages(null); if n <> 0 then raise exception 'FAIL null'; end if;
  raise notice 'ok   per_conv default/clamps, empty and null arrays';
end $$;
-- as B: sees only c5
select set_config('request.jwt.claim.sub', 'b0000000-0000-4000-8000-000000000002', false);
do $$ declare n int; begin
  select count(*) into n from public.last_messages(array['c0000000-0000-4000-8000-000000000001','c0000000-0000-4000-8000-000000000005']::uuid[]);
  if n <> 1 then raise exception 'FAIL B sees %', n; end if; raise notice 'ok   B sees only their own chat';
end $$;
reset role;
-- anon cannot call it; it is SECURITY INVOKER; the plan uses the index
do $$ begin
  if has_function_privilege('anon', 'public.last_messages(uuid[], int)', 'execute') then raise exception 'FAIL anon can execute'; end if;
  if not has_function_privilege('authenticated', 'public.last_messages(uuid[], int)', 'execute') then raise exception 'FAIL authenticated cannot'; end if;
  if (select prosecdef from pg_proc where proname = 'last_messages') then raise exception 'FAIL security definer'; end if;
  raise notice 'ok   grants: authenticated only; SECURITY INVOKER';
end $$;
S
chmod 644 $W/*.sql
su postgres -c "PGOPTIONS='-c client_min_messages=warning' $PSQL -d lm -f $W/stub.sql -f $W/msg.sql -f $W/lh.sql -f $W/lm.sql -f $W/lm.sql" 2>&1 | grep -v "^NOTICE\|^$" || true
su postgres -c "$PSQL -d lm -f $W/test.sql" 2>&1
# the plan: one index scan per chat, not a scan of every message
su postgres -c "$PSQL -d lm" <<'S' 2>&1 | grep -E "Index Scan|Seq Scan on messages|Execution Time|ms  plan" 
alter table public.messages disable trigger messages_touch_conv;
insert into public.messages (conversation_id, sender, body, created_at) select 'c0000000-0000-4000-8000-000000000002', 'a0000000-0000-4000-8000-000000000001', 'bulk', timestamptz '2026-08-01' - g * interval '1 second' from generate_series(1, 50000) g;
analyze public.messages;
load 'auto_explain'; set auto_explain.log_min_duration = 0; set auto_explain.log_nested_statements = on; set auto_explain.log_analyze = on;
set role authenticated; select set_config('request.jwt.claim.sub', 'a0000000-0000-4000-8000-000000000001', false); set client_min_messages = log;
select count(*) from public.last_messages(array['c0000000-0000-4000-8000-000000000001','c0000000-0000-4000-8000-000000000002']::uuid[]);
S
