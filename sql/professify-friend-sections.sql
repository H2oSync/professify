-- ============================================================================
-- Let friends read each other's imported sections
-- ============================================================================
-- The app already writes every imported class to my_sections: exact section
-- token, class number, instructor and meeting days. That is precisely what the
-- Quad needs to draw a friend's real week and name their professor.
--
-- Until now the app only ever read my_sections for the signed-in student, and
-- friends' schedules were reconstructed from saved_classes (course codes only).
-- With 958 of 1,870 Fall 2026 courses running more than one timed section, a
-- course code cannot say when someone is on campus or who teaches them.
--
-- This grants SELECT on a row only to people you are ALREADY FRIENDS WITH —
-- the same relationship that already lets them see your class list. It does not
-- open my_sections to anyone else, and it grants read only.
--
-- Run once in Supabase -> SQL Editor.
-- ============================================================================

alter table public.my_sections enable row level security;

-- Your own rows: unchanged, full access.
drop policy if exists "own sections" on public.my_sections;
create policy "own sections"
  on public.my_sections for all
  using ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

-- Accepted friends may READ your sections. This matches the app's own table:
-- friend_requests(from_user, to_user, status), where 'accepted' IS the friendship.
drop policy if exists "friends can read sections" on public.my_sections;
create policy "friends can read sections"
  on public.my_sections for select
  using (
    exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and ( (fr.from_user = auth.uid() and fr.to_user  = my_sections.user_id)
           or (fr.to_user   = auth.uid() and fr.from_user = my_sections.user_id) )
    )
  );

-- Sanity check: should return the sections of everyone you're friends with.
-- select user_id, code, section, instructor, days from public.my_sections;
