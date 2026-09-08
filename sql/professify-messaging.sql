-- =============================================================================================
-- Professify — messaging, suggestions, and the review-privacy fix that has to come with them
-- Written 2026-08-28 for Tate. Run this in the Supabase SQL editor. Safe to re-run.
--
-- WHAT THIS TURNS ON
--   1. Direct and group messages between accepted friends.
--   2. Class and professor suggestions sent INTO a thread as structured cards.
--   3. "Tate and Sean suggested this teacher" on a professor's page — a recommendation that
--      costs nobody a rating form.
--   4. A per-review "show this to my friends" flag, OFF by default.
--
-- AND THE THING THAT HAD TO BE FIXED FIRST
--   Section 1 closes the reviews.user_id exposure. This is not optional housekeeping bundled
--   in for tidiness: today ANY signed-in student can read the author id on every review, and
--   that same id sits on my_sections and saved_classes rows, so a review can be tied to a
--   person and their schedule. The Privacy page currently promises the opposite — "never shown
--   to anyone, including your friends". Adding an opt-in "share my review with friends" toggle
--   on top of that would be selling a choice that has already been made for people. So the
--   leak closes in the same file that adds the toggle, and it closes FIRST.
--
-- ORDER: run after professify-rls-hardening.sql. It replaces two policies from that file.
--
-- Nothing here drops a table or deletes a row. Two functions are dropped by name so their
-- signatures can change; both compute their answers from tables this file does not touch.
-- =============================================================================================


-- =============================================================================================
-- 1. REVIEWS: content stays public, the author stops being readable
-- =============================================================================================
-- The previous fix revoked user_id from `anon` only, and said so in its own RESIDUAL RISK note:
-- "any SIGNED-IN student can still read reviews.user_id and de-anonymise other students."
-- The proper fix, named in that note, is what this does — public reviews come from a view with
-- no author column, and the base table becomes readable only by the person who wrote the row.

alter table public.reviews
  add column if not exists share_with_friends boolean not null default false;

comment on column public.reviews.share_with_friends is
  'OFF by default. When true, accepted friends may see that THIS person wrote THIS review. '
  'Never changes who can read the review text — that has always been public and anonymous.';

-- ---------------------------------------------------------------------------------------------
-- 1a. The public view: every review, no author.
-- ---------------------------------------------------------------------------------------------
-- A view runs with its OWNER's rights unless it is declared security_invoker, so this reads the
-- base table past RLS and hands back exactly the columns listed. There is no user_id to select,
-- no user_id to filter on, and no user_id to join against — the column does not exist here at
-- all. That is a stronger guarantee than a policy, because a policy can be worked around by
-- asking a different question and a missing column cannot.
-- The column list is BUILT from the table rather than typed out. Typing it out means this file
-- has to know every column public.reviews happens to have today (teach_ability, format, term,
-- grade, verified — the set has grown), and one wrong guess makes the view fail to create and
-- takes every review on the site down with it. Reading information_schema cannot be wrong.
do $$
declare cols text;
begin
  select string_agg(quote_ident(column_name), ', ' order by ordinal_position)
    into cols
    from information_schema.columns
   where table_schema = 'public'
     and table_name   = 'reviews'
     -- user_id is the one that must never come through. share_with_friends is somebody's
     -- privacy SETTING rather than review content, and a public list of who has opted in is
     -- not something the public view is for.
     and column_name not in ('user_id', 'share_with_friends');
  if cols is null then
    raise exception 'public.reviews not found — run professify-rls-hardening.sql first';
  end if;
  execute 'drop view if exists public.reviews_public';
  execute 'create view public.reviews_public with (security_invoker = false) as select '
          || cols || ' from public.reviews';
end $$;

grant select on public.reviews_public to anon, authenticated;

-- ---------------------------------------------------------------------------------------------
-- 1b. The base table: yours, and your friends' only if they said so.
-- ---------------------------------------------------------------------------------------------
alter table public.reviews enable row level security;

-- This is the policy that was doing the leaking: `using (true)` for everyone, every column.
drop policy if exists "reviews are publicly readable" on public.reviews;

drop policy if exists "authors read their own reviews" on public.reviews;
create policy "authors read their own reviews"
  on public.reviews for select
  using ( auth.uid() = user_id );

-- The opt-in. A friend sees the author only when the author flipped the switch on that review.
-- Both halves are required: an accepted friendship AND share_with_friends on the row.
drop policy if exists "friends read reviews shared with them" on public.reviews;
create policy "friends read reviews shared with them"
  on public.reviews for select
  using (
    share_with_friends
    and exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and (
          (fr.from_user = auth.uid() and fr.to_user = public.reviews.user_id) or
          (fr.to_user   = auth.uid() and fr.from_user = public.reviews.user_id)
        )
    )
  );

-- Writes are unchanged and stay owner-only. Restated rather than assumed, because the select
-- policy above is being replaced and it is worth reading the whole set in one place.
drop policy if exists "authors edit their own reviews" on public.reviews;
create policy "authors edit their own reviews"
  on public.reviews for update
  using ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

drop policy if exists "authors delete their own reviews" on public.reviews;
create policy "authors delete their own reviews"
  on public.reviews for delete
  using ( auth.uid() = user_id );

-- Anonymous callers have no business at the base table now that the view exists.
revoke select on public.reviews from anon;


-- =============================================================================================
-- 2. "3 friends reviewed this professor"
-- =============================================================================================
-- Counting is not the hard part; being able to say the sentence honestly is. The number has to
-- mean "three people CHOSE to show you this", so a friend who never opted in is not counted —
-- which is exactly what the share_with_friends filter below does. SECURITY DEFINER because the
-- caller cannot read other people's review rows any more, by design.
drop function if exists public.friends_reviewed(text);

create or replace function public.friends_reviewed(p_professor_key text)
returns table (
  id           uuid,
  display_name text,
  username     text,
  avatar_url   text,
  score        numeric,
  course       text,
  created_at   timestamptz
)
language sql
security definer
stable
set search_path = public
as $$
  select p.id, p.display_name, p.username, p.avatar_url,
         r.score, r.course, r.created_at
  from public.reviews r
  join public.profiles p on p.id = r.user_id
  where r.professor_key = p_professor_key
    and r.share_with_friends
    and r.user_id <> auth.uid()          -- your own review is already on your screen
    and auth.uid() is not null
    and exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and (
          (fr.from_user = auth.uid() and fr.to_user = r.user_id) or
          (fr.to_user   = auth.uid() and fr.from_user = r.user_id)
        )
    )
  order by r.created_at desc
$$;

-- NOTE ON THESE REVOKES — the reason they say "from public" and not "from anon".
-- Postgres grants EXECUTE on a new function to the PUBLIC pseudo-role automatically, so
-- "revoke execute ... from anon" removes a grant anon never needed and changes nothing: the
-- function stays callable by everyone through PUBLIC. Verified on Postgres 16 on 2026-08-28 —
-- an anonymous caller ran every function in this file after those revokes "succeeded".
-- The revoke has to name PUBLIC, and the grant then hands it back to exactly one role.
-- (The same mistake is in professify-review-integrity.sql, line "revoke execute on function
--  public.suggest_classmates() from anon" — that one is still open. See the end of this file.)

revoke execute on function public.friends_reviewed(text) from public, anon;
grant  execute on function public.friends_reviewed(text) to authenticated;


-- =============================================================================================
-- 3. SUGGESTING A PROFESSOR WITHOUT WRITING A REVIEW
-- =============================================================================================
-- A suggestion is a much smaller claim than a review: "I'd take this person." It carries no
-- score, so it cannot move an average, and there is nothing to fill in. Your friends see it on
-- that professor's page as a pill naming who suggested them.
create table if not exists public.professor_suggestions (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  professor_key  text not null,
  professor_name text,
  note           text,
  created_at     timestamptz not null default now(),
  unique (user_id, professor_key)      -- suggesting twice is the same suggestion
);

create index if not exists prof_sug_key_idx on public.professor_suggestions (professor_key);

alter table public.professor_suggestions enable row level security;

drop policy if exists "you manage your own suggestions" on public.professor_suggestions;
create policy "you manage your own suggestions"
  on public.professor_suggestions for all
  using ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

-- Reading OTHER people's suggestions goes through the function below, not through the table,
-- so a suggestion never leaks past the friendship boundary even by a broad select.
drop function if exists public.professor_suggested_by(text);

create or replace function public.professor_suggested_by(p_professor_key text)
returns table (
  id           uuid,
  display_name text,
  username     text,
  avatar_url   text,
  note         text,
  created_at   timestamptz
)
language sql
security definer
stable
set search_path = public
as $$
  select p.id, p.display_name, p.username, p.avatar_url, s.note, s.created_at
  from public.professor_suggestions s
  join public.profiles p on p.id = s.user_id
  where s.professor_key = p_professor_key
    and auth.uid() is not null
    and s.user_id <> auth.uid()
    and exists (
      select 1 from public.friend_requests fr
      where fr.status = 'accepted'
        and (
          (fr.from_user = auth.uid() and fr.to_user = s.user_id) or
          (fr.to_user   = auth.uid() and fr.from_user = s.user_id)
        )
    )
  order by s.created_at desc
$$;

revoke execute on function public.professor_suggested_by(text) from public, anon;
grant  execute on function public.professor_suggested_by(text) to authenticated;


-- =============================================================================================
-- 4. MESSAGES
-- =============================================================================================
-- This is the first data Professify stores about what students say TO EACH OTHER rather than
-- about classes. Two consequences worth being deliberate about, both handled below:
--   * membership is the ONLY key to a thread, enforced in the database, not in the app;
--   * there is a retention lever at the bottom of this file, because deciding later is much
--     harder than deciding now.

create table if not exists public.conversations (
  id         uuid primary key default gen_random_uuid(),
  kind       text not null default 'direct' check (kind in ('direct','group')),
  title      text,                       -- groups only; direct threads are named by who is in them
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  last_at    timestamptz not null default now()   -- kept fresh by a trigger, for ordering
);

create table if not exists public.conversation_members (
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id         uuid not null references auth.users(id) on delete cascade,
  joined_at       timestamptz not null default now(),
  last_read_at    timestamptz not null default 'epoch',
  primary key (conversation_id, user_id)
);

create index if not exists conv_members_user_idx on public.conversation_members (user_id);

create table if not exists public.messages (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  sender          uuid not null references auth.users(id) on delete cascade,
  kind            text not null default 'text'
                  check (kind in ('text','class','professor','ask')),
  body            text,
  -- A suggestion is a course code and a section, not a screenshot of one. Storing the
  -- REFERENCE and rendering it on read is what lets the seat count and the "who is free then"
  -- line be true when the message is READ rather than when it was sent.
  payload         jsonb,
  created_at      timestamptz not null default now()
);

create index if not exists messages_conv_idx on public.messages (conversation_id, created_at desc);

-- ---------------------------------------------------------------------------------------------
-- 4a. Membership, without the recursion trap
-- ---------------------------------------------------------------------------------------------
-- A policy on conversation_members that asks "is the caller in conversation_members?" recurses
-- forever and Postgres will tell you so at query time, not at create time. This function reads
-- the table as its owner, so the policies below can call it without re-entering RLS.
create or replace function public.is_conv_member(p_conv uuid, p_user uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (
    select 1 from public.conversation_members m
    where m.conversation_id = p_conv and m.user_id = p_user
  )
$$;

revoke execute on function public.is_conv_member(uuid, uuid) from public, anon;
grant  execute on function public.is_conv_member(uuid, uuid) to authenticated;

-- Are these two accepted friends? Used to stop a thread being opened with a stranger.
create or replace function public.is_friend_of(p_a uuid, p_b uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (
    select 1 from public.friend_requests fr
    where fr.status = 'accepted'
      and ((fr.from_user = p_a and fr.to_user = p_b) or (fr.to_user = p_a and fr.from_user = p_b))
  )
$$;

revoke execute on function public.is_friend_of(uuid, uuid) from public, anon;
grant  execute on function public.is_friend_of(uuid, uuid) to authenticated;

-- ---------------------------------------------------------------------------------------------
-- 4b. Policies
-- ---------------------------------------------------------------------------------------------
alter table public.conversations        enable row level security;
alter table public.conversation_members enable row level security;
alter table public.messages             enable row level security;

drop policy if exists "members read their conversations" on public.conversations;
create policy "members read their conversations"
  on public.conversations for select
  using ( public.is_conv_member(id, auth.uid()) );

-- The creator, separately from membership. This is not belt-and-braces: without it the very
-- first membership insert is impossible. The member policy below asks "did the caller create
-- this conversation?", which reads public.conversations — and with only the membership policy
-- above, a conversation with no members yet is invisible even to the person who just made it.
-- So the creator's own row is never writable and the thread can never be started.
-- (Found on a real Postgres, 2026-08-28, not reasoned about: every insert failed with
--  "new row violates row-level security policy for table conversation_members".)
drop policy if exists "creators read their conversations" on public.conversations;
create policy "creators read their conversations"
  on public.conversations for select
  using ( auth.uid() = created_by );

drop policy if exists "you start your own conversations" on public.conversations;
create policy "you start your own conversations"
  on public.conversations for insert
  with check ( auth.uid() = created_by );

drop policy if exists "the creator renames a group" on public.conversations;
create policy "the creator renames a group"
  on public.conversations for update
  using ( auth.uid() = created_by )
  with check ( auth.uid() = created_by );

drop policy if exists "members read the member list" on public.conversation_members;
create policy "members read the member list"
  on public.conversation_members for select
  using ( public.is_conv_member(conversation_id, auth.uid()) );

-- You may add someone to a thread you created, and only if they are already your accepted
-- friend. Adding YOURSELF is allowed too, which is how the creator's own row gets written.
drop policy if exists "the creator adds friends" on public.conversation_members;
create policy "the creator adds friends"
  on public.conversation_members for insert
  with check (
    exists (
      select 1 from public.conversations c
      where c.id = conversation_id and c.created_by = auth.uid()
    )
    and ( user_id = auth.uid() or public.is_friend_of(auth.uid(), user_id) )
  );

-- Your own row: mark it read, or leave.
drop policy if exists "you update your own membership" on public.conversation_members;
create policy "you update your own membership"
  on public.conversation_members for update
  using ( auth.uid() = user_id )
  with check ( auth.uid() = user_id );

drop policy if exists "you can leave" on public.conversation_members;
create policy "you can leave"
  on public.conversation_members for delete
  using ( auth.uid() = user_id );

drop policy if exists "members read the thread" on public.messages;
create policy "members read the thread"
  on public.messages for select
  using ( public.is_conv_member(conversation_id, auth.uid()) );

drop policy if exists "members write to the thread" on public.messages;
create policy "members write to the thread"
  on public.messages for insert
  with check (
    auth.uid() = sender
    and public.is_conv_member(conversation_id, auth.uid())
  );

-- You can take back what you said. You cannot touch what anyone else said, and there is
-- deliberately no UPDATE policy: an edited message with no edit marker is a way to make
-- someone look like they said something they did not.
drop policy if exists "you delete your own messages" on public.messages;
create policy "you delete your own messages"
  on public.messages for delete
  using ( auth.uid() = sender );

-- ---------------------------------------------------------------------------------------------
-- 4c. Thread ordering
-- ---------------------------------------------------------------------------------------------
-- Sorting the list by "the newest message in each thread" is a per-row subquery on every load.
-- One column, kept fresh by the write that would have invalidated it.
create or replace function public.touch_conversation()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.conversations set last_at = new.created_at where id = new.conversation_id;
  return new;
end $$;

-- A trigger function errors if called directly ("can only be called as a trigger"), so this is
-- tidiness rather than a hole — but it makes the audit query at the end of this file come back
-- with an empty anon column, and a clean audit is worth more than a footnote about why one row
-- in it is fine.
revoke execute on function public.touch_conversation() from public, anon, authenticated;

drop trigger if exists messages_touch_conv on public.messages;
create trigger messages_touch_conv
  after insert on public.messages
  for each row execute function public.touch_conversation();


-- ---------------------------------------------------------------------------------------------
-- 4d. Grants
-- ---------------------------------------------------------------------------------------------
-- Supabase's default privileges usually hand new public tables to anon and authenticated, which
-- is the wrong default for these three. Stated explicitly so the answer does not depend on how
-- the project was set up: a signed-in student reaches these tables (and RLS decides which rows),
-- a signed-out visitor does not reach them at all.
grant select, insert, update, delete on public.conversations        to authenticated;
grant select, insert, update, delete on public.conversation_members to authenticated;
grant select, insert,         delete on public.messages             to authenticated;
grant select, insert, update, delete on public.professor_suggestions to authenticated;

revoke all on public.conversations        from anon;
revoke all on public.conversation_members from anon;
revoke all on public.messages             from anon;
revoke all on public.professor_suggestions from anon;


-- =============================================================================================
-- 5. RETENTION — the decision, made rather than deferred
-- =============================================================================================
-- Default: messages are kept until the thread is deleted or an account is closed, at which
-- point the cascades above remove them. That is the ordinary expectation for a chat app and it
-- is what the Privacy page now says.
--
-- If you would rather they roll off — and for a class-planning app there is a real argument
-- that a thread about Spring registration has no business still existing in your senior year —
-- this function does it, and the pg_cron line below schedules it. Uncomment BOTH to turn it on,
-- and change the Privacy page to match, because the page and the database have to agree.
create or replace function public.prune_messages(p_older_than interval default interval '18 months')
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare n integer;
begin
  delete from public.messages where created_at < now() - p_older_than;
  get diagnostics n = row_count;
  return n;
end $$;

-- Nobody but the database owner. This one DELETES, and called as prune_messages(interval '0')
-- it would empty every thread in the app — so an over-broad grant here is not a leak, it is a
-- delete button on the open internet. PUBLIC has to be named for the same reason as above.
revoke execute on function public.prune_messages(interval) from public, anon, authenticated;

-- select cron.schedule('professify-prune-messages', '0 4 * * 0',
--   $cron$ select public.prune_messages(interval '18 months') $cron$);


-- =============================================================================================
-- VERIFY
-- =============================================================================================
-- Signed OUT, in a devtools console on professify.app:
--   const c=window.PROFESSIFY_CONFIG;
--   const a=window.supabase.createClient(c.SUPABASE_URL,c.SUPABASE_ANON_KEY,
--           {auth:{persistSession:false,storageKey:'v'}});
--   await a.from('reviews_public').select('*').limit(1);   // reviews still load, no user_id
--   await a.from('reviews').select('id').limit(1);         // expect an error / zero rows
--   await a.from('messages').select('*').limit(1);         // expect zero rows
--
-- Signed IN as yourself:
--   * A professor page still lists every review.
--   * Settings → Your reviews still lists yours.
--   * A thread you are not in returns nothing — not an error, nothing.
--   * "N friends reviewed" only counts friends who turned the toggle on.


-- =============================================================================================
-- STILL OPEN AFTER THIS FILE — for the security page, not for this run
-- =============================================================================================
-- professify-review-integrity.sql ends with "revoke execute on function
-- public.suggest_classmates() from anon". As shown above, that does not revoke anything,
-- because the grant those functions actually carry is to PUBLIC. If suggest_classmates still
-- exists in the database, close it properly:
--
--   revoke execute on function public.suggest_classmates() from public, anon;
--   grant  execute on function public.suggest_classmates() to authenticated;
--
-- and check the rest the same way — this lists every function anonymous callers can run:
--
--   select p.proname,
--          has_function_privilege('anon', p.oid, 'execute') as anon_can_run
--     from pg_proc p join pg_namespace n on n.oid = p.pronamespace
--    where n.nspname = 'public'
--    order by 2 desc, 1;
