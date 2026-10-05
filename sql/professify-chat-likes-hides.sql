-- TermChamp chats: like a message, delete a message for yourself, delete a chat for yourself
-- (Tate, 2026-10-03: "make it so i can like messages, i can delete messages on my side. i can delete
-- conversations.")
--
-- ADDITIVE. Three new tables; nothing in messages, conversations or conversation_members changes, and
-- nobody's messages are removed for anyone else. Safe to run twice. Needs professify-messaging.sql and
-- professify-safety.sql (is_conv_member, is_suspended, blocked_between), which are live.
--
--   message_likes        who liked which message. Everyone in that conversation can see them.
--   message_hides        "Delete for me": the messages YOU hid. Only you can see your rows.
--   conversation_clears  "Delete chat": when YOU cleared a conversation. Only you can see your row,
--                        so the other person can't tell you deleted it. Messages from before that time
--                        are hidden for you; a new message brings the chat back, starting fresh.

begin;

-- ------------------------------------------------------------------------------------------------
-- 1. Likes
-- ------------------------------------------------------------------------------------------------
create table if not exists public.message_likes (
  message_id uuid not null references public.messages(id) on delete cascade,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (message_id, user_id)
);
alter table public.message_likes enable row level security;

drop policy if exists "members see likes" on public.message_likes;
create policy "members see likes" on public.message_likes for select to authenticated
  using ( exists (select 1 from public.messages m
                  where m.id = message_likes.message_id
                    and public.is_conv_member(m.conversation_id, auth.uid())) );

-- You like as yourself, only a message in a conversation you are in, and not while suspended (a like is
-- something others see). The block rule is the one messages already use: no like in a thread you share
-- with anyone you've blocked or who blocked you, whoever wrote the message, and never on a message from
-- them even if they've since left.
drop policy if exists "you like as yourself" on public.message_likes;
create policy "you like as yourself" on public.message_likes for insert to authenticated
  with check ( user_id = auth.uid()
               and not public.is_suspended(auth.uid())
               and exists (select 1 from public.messages m
                           where m.id = message_likes.message_id
                             and public.is_conv_member(m.conversation_id, auth.uid())
                             and not public.blocked_between(auth.uid(), m.sender)
                             and not exists (select 1 from public.conversation_members cm
                                             where cm.conversation_id = m.conversation_id
                                               and cm.user_id <> auth.uid()
                                               and public.blocked_between(auth.uid(), cm.user_id))) );

drop policy if exists "you unlike your own" on public.message_likes;
create policy "you unlike your own" on public.message_likes for delete to authenticated
  using ( user_id = auth.uid() );

-- ------------------------------------------------------------------------------------------------
-- 2. Delete a message for yourself
-- ------------------------------------------------------------------------------------------------
create table if not exists public.message_hides (
  message_id uuid not null references public.messages(id) on delete cascade,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (message_id, user_id)
);
alter table public.message_hides enable row level security;

drop policy if exists "you see your own hides" on public.message_hides;
create policy "you see your own hides" on public.message_hides for select to authenticated
  using ( user_id = auth.uid() );

drop policy if exists "you hide what you can see" on public.message_hides;
create policy "you hide what you can see" on public.message_hides for insert to authenticated
  with check ( user_id = auth.uid()
               and exists (select 1 from public.messages m
                           where m.id = message_hides.message_id
                             and public.is_conv_member(m.conversation_id, auth.uid())) );

drop policy if exists "you unhide your own" on public.message_hides;
create policy "you unhide your own" on public.message_hides for delete to authenticated
  using ( user_id = auth.uid() );

-- ------------------------------------------------------------------------------------------------
-- 3. Delete a chat for yourself
-- ------------------------------------------------------------------------------------------------
create table if not exists public.conversation_clears (
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id         uuid not null default auth.uid() references auth.users(id) on delete cascade,
  cleared_at      timestamptz not null default now(),
  primary key (conversation_id, user_id)
);
alter table public.conversation_clears enable row level security;

drop policy if exists "you see your own clears" on public.conversation_clears;
create policy "you see your own clears" on public.conversation_clears for select to authenticated
  using ( user_id = auth.uid() );

drop policy if exists "you clear a chat you are in" on public.conversation_clears;
create policy "you clear a chat you are in" on public.conversation_clears for insert to authenticated
  with check ( user_id = auth.uid() and public.is_conv_member(conversation_id, auth.uid()) );

drop policy if exists "you move your own clear" on public.conversation_clears;
create policy "you move your own clear" on public.conversation_clears for update to authenticated
  using ( user_id = auth.uid() )
  with check ( user_id = auth.uid() and public.is_conv_member(conversation_id, auth.uid()) );

drop policy if exists "you drop your own clear" on public.conversation_clears;
create policy "you drop your own clear" on public.conversation_clears for delete to authenticated
  using ( user_id = auth.uid() );

-- Your own hides and clears are read by user_id on every chat-list load.
create index if not exists message_hides_user_idx on public.message_hides (user_id);
create index if not exists conversation_clears_user_idx on public.conversation_clears (user_id);

-- ------------------------------------------------------------------------------------------------
-- 4. Grants: signed-in students only; nothing for anon.
-- ------------------------------------------------------------------------------------------------
revoke all on public.message_likes       from public, anon, authenticated;
revoke all on public.message_hides       from public, anon, authenticated;
revoke all on public.conversation_clears from public, anon, authenticated;
grant select, insert, delete on public.message_likes to authenticated;
grant select, insert, delete on public.message_hides to authenticated;
grant select, insert, delete on public.conversation_clears to authenticated;
grant update (cleared_at)   on public.conversation_clears to authenticated;

-- ------------------------------------------------------------------------------------------------
-- 5. Self-checks: stop here, with nothing applied, if any of this didn't take.
-- ------------------------------------------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from pg_tables
   where schemaname = 'public' and tablename in ('message_likes','message_hides','conversation_clears') and rowsecurity;
  if n <> 3 then raise exception 'chat tables: row-level security is not on for all three (got %)', n; end if;
  select count(*) into n from pg_policies
   where schemaname = 'public' and tablename in ('message_likes','message_hides','conversation_clears');
  if n <> 10 then raise exception 'chat tables: expected 10 policies, found %', n; end if;
  if has_table_privilege('anon', 'public.message_likes', 'select')
     or has_table_privilege('anon', 'public.message_hides', 'select')
     or has_table_privilege('anon', 'public.conversation_clears', 'select') then
    raise exception 'chat tables: anon can read them';
  end if;
end $$;

commit;
