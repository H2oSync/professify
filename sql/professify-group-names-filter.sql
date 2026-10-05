-- TermChamp: group chat names go through the word filter (2026-10-04)
--
-- professify-word-filter.sql left conversations.title out on purpose ("a direct message is between
-- friends"). A group's name is different: it sits in the chat list of everyone in the group, and
-- the person who adds you to one chooses it, not you. The phone app already refuses a filtered word
-- as you type (wfHit); this is the control behind it, for anything that skips the app.
--
-- Same trigger function as profiles, reviews and posts (wf_guard), on the title only. A rename that
-- leaves the title alone, and every direct chat (no title), pass untouched. The student reads:
--   A group name can't contain "…" — change it and try again.
-- Needs professify-word-filter.sql (live since 2026-09-07). Adds a trigger; deletes nothing; existing
-- names are left as they are (the scan at the end lists any that would fail). Safe to run twice.

begin;

do $$ begin
  if to_regproc('public.wf_guard') is null then
    raise exception 'the word filter is not on this database — run professify-word-filter.sql first';
  end if;
end $$;

drop trigger if exists wf_guard_conversations on public.conversations;
create trigger wf_guard_conversations before insert or update on public.conversations
  for each row execute function public.wf_guard('A group name', 'title');

do $$
begin
  if not exists (select 1 from pg_trigger where tgname = 'wf_guard_conversations' and tgrelid = 'public.conversations'::regclass) then
    raise exception 'the group name filter did not attach';
  end if;
  if public.wf_hit('Study crew') is not null then raise exception 'an ordinary group name would be refused'; end if;
end $$;

commit;

-- Read-only: existing group names that would now be refused (rename them by hand if any show up).
select id, title, created_by from public.conversations where title is not null and public.wf_hit(title) is not null;
