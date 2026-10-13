-- TermChamp: flowchart rows you checked off yourself (2026-10-09). RUN 15.
--
-- Past classes › Your flowchart: a row with no class to log (a GE area, an elective) or one TermChamp
-- can't check now takes a tap — "Marked done by you" — and counts as done everywhere the flowchart is
-- counted. This table keeps those marks with the account: one row per mark, owner-only, the row's words
-- kept so a mark only ever applies to the row it was made on. Nothing a friend or anyone else can read.
-- Until this runs, the phone keeps marks on the device and sends them up once it can.
--
-- Additive, one transaction, safe to run again. Self-checks at the end raise on anything wrong.
-- Check after:
--   select count(*) from pg_policies where tablename = 'flowchart_marks';   -- 3
begin;

create table if not exists public.flowchart_marks (
  user_id   uuid        not null references auth.users(id) on delete cascade,
  major     text        not null,
  slot_id   text        not null,
  label     text        not null default '',
  marked_at timestamptz not null default now(),
  primary key (user_id, major, slot_id),
  constraint flowchart_marks_major_len check (length(major) between 1 and 120),
  constraint flowchart_marks_slot_ok   check (slot_id ~ '^[A-Za-z0-9_.:-]{1,80}$'),
  constraint flowchart_marks_label_len check (length(label) <= 160)
);
alter table public.flowchart_marks enable row level security;

drop policy if exists flowchart_marks_own_select on public.flowchart_marks;
drop policy if exists flowchart_marks_own_insert on public.flowchart_marks;
drop policy if exists flowchart_marks_own_delete on public.flowchart_marks;
create policy flowchart_marks_own_select on public.flowchart_marks for select to authenticated using (user_id = auth.uid());
-- 300 marks per account is far more than any flowchart has rows
create policy flowchart_marks_own_insert on public.flowchart_marks for insert to authenticated
  with check (user_id = auth.uid() and (select count(*) from public.flowchart_marks m where m.user_id = auth.uid()) < 300);
create policy flowchart_marks_own_delete on public.flowchart_marks for delete to authenticated using (user_id = auth.uid());

-- Supabase's default privileges give anon and authenticated everything on a new table: take it all back,
-- then grant only what the phone uses
revoke all on public.flowchart_marks from public, anon, authenticated;
grant select, insert, delete on public.flowchart_marks to authenticated;

do $$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'flowchart_marks') <> 3 then
    raise exception 'flowchart_marks: expected 3 policies';
  end if;
  if has_table_privilege('anon', 'public.flowchart_marks', 'select') or has_table_privilege('anon', 'public.flowchart_marks', 'insert') then
    raise exception 'flowchart_marks: anon can reach it';
  end if;
  if has_table_privilege('authenticated', 'public.flowchart_marks', 'update') then
    raise exception 'flowchart_marks: rows are added or removed, never edited';
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.flowchart_marks'::regclass) then
    raise exception 'flowchart_marks: row level security is off';
  end if;
end $$;

commit;
