-- ============================================================================================
-- FREE NOW + PINNED FRIENDS — 2026-09-05
-- ============================================================================================
-- Tate: "Add a 'Free Now' indicator that lets users quickly show that they are available to hang
-- out, study, eat, or do something on campus. add a pin friend on the top and only allow 2
-- friends to be pinned."
--
-- Two small pieces of state, with the same rule the rest of Professify runs on: a person's day
-- is theirs, and only their accepted friends see any of it.
--
-- WHY THE ROW EXPIRES IN THE DATABASE AND NOT ONLY IN THE APP
--   A "free now" that outlives the afternoon is a false statement about a person, which is the
--   one kind of bug this project does not ship. The client refuses to render an expired row, but
--   the client is not the only reader — a push worker, a future widget, anything. So `until` is
--   NOT NULL, the read policy itself filters on it, and an expired row is invisible to everyone
--   including the friend it belongs to. Nothing has to remember to clean up for the data to stop
--   being wrong; the worst a stale row can do is take up a few bytes.
--
-- Run in the Supabase SQL editor. Safe to re-run.
-- ============================================================================================


-- --------------------------------------------------------------------------------------------
-- 1. free_now — one row per person, replaced, never appended
-- --------------------------------------------------------------------------------------------
-- One row per user is deliberate. An append-only log of every afternoon a student was free is a
-- movement history nobody asked us to keep, and it would sit there being subpoena-able for the
-- life of the app. There is no version of this feature that needs yesterday.
create table if not exists public.free_now (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  until      timestamptz not null,
  kind       text not null default 'open',
  note       text,
  updated_at timestamptz not null default now()
);

do $$ begin
  if not exists (select 1 from pg_constraint where conname='free_now_kind_ck') then
    alter table public.free_now
      add constraint free_now_kind_ck check (kind in ('study','eat','hang','open'));
  end if;
end $$;

-- An "I'm free" that runs for two days is a stale status wearing a live badge. The app sets this
-- to your next class; the ceiling is what stops anything else from setting it to next week.
do $$ begin
  if not exists (select 1 from pg_constraint where conname='free_now_window_ck') then
    alter table public.free_now
      add constraint free_now_window_ck check (until <= updated_at + interval '12 hours');
  end if;
end $$;

alter table public.free_now enable row level security;

-- READ: your own row, and your accepted friends' rows, and only while they are still current.
-- The `until > now()` lives in the POLICY, so an expired status is not merely hidden by the app —
-- it does not exist as far as any client is concerned.
drop policy if exists "friends read live statuses" on public.free_now;
create policy "friends read live statuses"
  on public.free_now for select
  using (
    until > now()
    and (
      user_id = auth.uid()
      or exists (
        select 1 from public.friend_requests r
        where r.status = 'accepted'
          and ( (r.from_user = auth.uid() and r.to_user = free_now.user_id)
             or (r.to_user   = auth.uid() and r.from_user = free_now.user_id) )
      )
    )
  );

-- WRITE: yourself only, in every direction.
drop policy if exists "set your own status" on public.free_now;
create policy "set your own status"
  on public.free_now for insert with check (user_id = auth.uid());

drop policy if exists "update your own status" on public.free_now;
create policy "update your own status"
  on public.free_now for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "clear your own status" on public.free_now;
create policy "clear your own status"
  on public.free_now for delete using (user_id = auth.uid());

-- updated_at has to be the server's clock, or the 12-hour ceiling is enforced against whatever
-- time the client felt like sending.
create or replace function public.free_now_touch()
returns trigger language plpgsql as $$
begin new.updated_at := now(); return new; end $$;

drop trigger if exists free_now_touch_t on public.free_now;
create trigger free_now_touch_t before insert or update on public.free_now
  for each row execute function public.free_now_touch();

create index if not exists free_now_until_idx on public.free_now(until);


-- --------------------------------------------------------------------------------------------
-- 2. profiles.pinned_friends — two, and the database says two
-- --------------------------------------------------------------------------------------------
-- The cap is the feature. A pin list that grows is the friends list again in a different order,
-- and the top of the feed stops meaning anything. The app enforces it and explains it; the
-- constraint is here so a stale tab or a direct API call cannot quietly make it five.
alter table public.profiles add column if not exists pinned_friends uuid[];

do $$ begin
  if not exists (select 1 from pg_constraint where conname='profiles_pins_max_ck') then
    alter table public.profiles
      add constraint profiles_pins_max_ck
      check (pinned_friends is null or cardinality(pinned_friends) <= 2);
  end if;
end $$;


-- --------------------------------------------------------------------------------------------
-- 3. Live updates (optional but this is the whole point of "now")
-- --------------------------------------------------------------------------------------------
-- A friend declaring they're free is worth exactly as much as it is timely. Adding the table to
-- the realtime publication lets an open Home reorder the moment it happens instead of at the
-- next visit. RLS still applies to realtime, so a non-friend receives nothing.
do $$ begin
  if exists (select 1 from pg_publication where pubname='supabase_realtime')
     and not exists (
       select 1 from pg_publication_tables
       where pubname='supabase_realtime' and schemaname='public' and tablename='free_now')
  then
    alter publication supabase_realtime add table public.free_now;
  end if;
end $$;


-- --------------------------------------------------------------------------------------------
-- VERIFY — as a signed-in student, not the service role
-- --------------------------------------------------------------------------------------------
--   insert into public.free_now (user_id, until, kind)
--     values (auth.uid(), now() + interval '90 minutes', 'study')
--     on conflict (user_id) do update set until = excluded.until, kind = excluded.kind;
--   select * from public.free_now;               -- your row, plus any live friend rows
--
--   update public.free_now set until = now() - interval '1 minute' where user_id = auth.uid();
--   select * from public.free_now;               -- your own expired row is GONE from the read
--
--   update public.profiles set pinned_friends = array[...three uuids...] where id = auth.uid();
--     -- expect: violates check constraint "profiles_pins_max_ck"
