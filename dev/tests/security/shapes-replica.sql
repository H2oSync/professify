-- GUESSED local replicas (the real definitions are not in the repo): shapes inferred from the apps' writes + term-scope + length-limits
create table public.saved_classes (user_id uuid not null references auth.users(id) on delete cascade, term text not null default '2268', code text not null, class_nbr text, waitlist_pos int, primary key (user_id, term, code));
create table public.my_sections (user_id uuid not null references auth.users(id) on delete cascade, term text not null default '2268', code text not null, class_nbr text not null, section text, instructor text, days text, status text, wl_pos int, primary key (user_id, term, class_nbr));
create table public.class_history (user_id uuid not null references auth.users(id) on delete cascade, code text not null, term text, year integer, professor text, unique (user_id, code, term, year));
do $$ declare t text; begin foreach t in array array['saved_classes','my_sections','class_history'] loop
  execute format('alter table public.%I enable row level security', t);
  execute format('create policy own on public.%I for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid())', t);
end loop; end $$;
