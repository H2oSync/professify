create table if not exists public.push_subscriptions (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  endpoint    text not null unique,          -- the push service's URL for this browser
  p256dh      text not null,                 -- public key half of the browser's keypair
  auth        text not null,                 -- the shared secret half
  ua          text,
  created_at  timestamptz not null default now(),
  last_ok_at  timestamptz,
  fail_count  int not null default 0
);
create index if not exists push_subs_user_idx on public.push_subscriptions(user_id);

alter table public.push_subscriptions enable row level security;

do $$
begin
  -- drop by SHAPE, not by name. Five separate times on this project a permissive policy under a
  -- name no migration mentioned survived every migration and quietly decided the outcome.
  perform 1;
  execute (
    select coalesce(string_agg(format('drop policy %I on public.push_subscriptions;', polname), ' '), '')
      from pg_policy where polrelid = 'public.push_subscriptions'::regclass);
end $$;

create policy push_subs_own_select on public.push_subscriptions
  for select to authenticated using (user_id = auth.uid());
create policy push_subs_own_insert on public.push_subscriptions
  for insert to authenticated with check (user_id = auth.uid());
create policy push_subs_own_delete on public.push_subscriptions
  for delete to authenticated using (user_id = auth.uid());
-- deliberately no UPDATE policy: a browser re-subscribing inserts a new endpoint and deletes the
-- old one. Nothing legitimate needs to rewrite somebody's keys in place.

revoke all on public.push_subscriptions from anon;
