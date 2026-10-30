-- 2026-10-30 — the newest few messages of each chat, in one call (scale fix).
-- The chat list read its previews with ONE query: the newest 300 messages across all of a student's
-- chats. A few busy chats filled those 300, so every quieter chat came back with no last message —
-- no preview, no unread dot, and a direct chat with no preview could drop out of the list.
-- last_messages() returns the newest `per_conv` messages of EACH conversation asked for (default 3,
-- at most 20), newest first, using messages_conv_idx (conversation_id, created_at desc) once per chat.
--
-- SECURITY INVOKER (the default, stated): it runs as the caller, so the RLS policy "members read
-- the thread" on public.messages decides what comes back — a conversation id you are not in returns
-- nothing. Messages you hid (message_hides) and messages from before you deleted the chat
-- (conversation_clears) are skipped here, so a chat whose newest messages you hid still gets a
-- preview; message_hides / conversation_clears are read under their own RLS (your rows only).
-- Requires sql/professify-messaging.sql and sql/professify-chat-likes-hides.sql (already live).
--
-- The phone app works without this function (it falls back to its old read plus a small per-chat
-- read for any chat left without a preview), and uses it as soon as it exists. Idempotent.
begin;

create or replace function public.last_messages(conv_ids uuid[], per_conv int default 3)
returns setof public.messages
language sql
stable
security invoker
set search_path = public
as $$
  select m.*
    from (select distinct c from unnest(conv_ids[1:1000]) as u(c)) ids
    cross join lateral (
      select x.*
        from public.messages x
       where x.conversation_id = ids.c
         and not exists (select 1 from public.message_hides h
                          where h.message_id = x.id and h.user_id = auth.uid())
         and x.created_at > coalesce((select cc.cleared_at from public.conversation_clears cc
                                       where cc.conversation_id = ids.c and cc.user_id = auth.uid()),
                                     '-infinity'::timestamptz)
       order by x.created_at desc, x.id desc
       limit least(greatest(coalesce(per_conv, 3), 1), 20)
    ) m
   order by m.conversation_id, m.created_at desc, m.id desc
$$;

revoke execute on function public.last_messages(uuid[], int) from public, anon;
grant  execute on function public.last_messages(uuid[], int) to authenticated;

commit;
notify pgrst, 'reload schema';

-- check: select proname, prosecdef from pg_proc where proname = 'last_messages';   -- prosecdef = false
-- undo:  drop function if exists public.last_messages(uuid[], int);
