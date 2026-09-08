/* =================================================================================================
   professify-share-cards.sql
   Makes a shared schedule link actually OPEN when the friend taps it.

   WHAT WAS BROKEN
   ---------------
   `shareMySchedule()` puts two objects in the `schedule-cards` bucket under one random id:

       <32 hex>.png    the picture iMessage draws in the card   (og:image, served by /s)
       <32 hex>.json   the WEEK itself, which the recipient's app fetches and renders

   The bucket was created with `allowed_mime_types = {image/png}`. The picture uploads fine. The
   payload is uploaded with contentType 'application/json' and is therefore rejected by the storage
   API every single time — 415, before RLS is even consulted.

   Both uploads are deliberately fire-and-forget (navigator.share() has to be called inside the
   click, so nothing in that path may be awaited), so the failure only ever reached a console.warn
   nobody was watching. The link still got built and sent. The card still previewed correctly.
   The friend who tapped it got:

       "That schedule link has expired — ask <name> to send it again."

   100% of the time, for every short link the app has ever produced.

   WHY THE BUCKET LOOKED FINE
   --------------------------
   It is empty (0 objects), and an empty bucket looks the same whether the writes are failing or
   nobody has tried. Ruled out on production before writing this: `authenticated` holds INSERT on
   storage.objects, RLS is on but the schedule-cards INSERT policy's WITH CHECK is the
   unconditional `(bucket_id = 'schedule-cards')`, there is no pg_cron and so no cleanup job, and
   all 7 objects in the project are avatars. The PNG half was never blocked — nobody had clicked
   Share on a signed-in session since the feature shipped on 2026-08-28.

   WHAT THIS CHANGES
   -----------------
   1. The bucket accepts application/json, so the payload can land beside its picture.
   2. The INSERT policy stops being "any authenticated user may write anything here" and starts
      naming the two shapes the app actually writes. The random id stays random — it must not
      contain the account id, because the image URL travels inside a link that gets forwarded.

   Safe to run more than once. Nothing is dropped except a policy this file immediately replaces.
   ================================================================================================= */

/* ---- 1. the bucket has to accept the payload it is asked to hold -------------------------------
   A null allowed_mime_types means "no restriction" in Supabase, which is already permissive enough
   and is left alone rather than tightened by surprise. */
do $$
declare
  v_exists boolean;
  v_mimes  text[];
begin
  select true, allowed_mime_types into v_exists, v_mimes
    from storage.buckets where id = 'schedule-cards';

  if v_exists is not true then
    raise notice 'schedule-cards: bucket does not exist — create it before running this';
  elsif v_mimes is null then
    raise notice 'schedule-cards: bucket accepts any mime type — nothing to change';
  elsif 'application/json' = any(v_mimes) then
    raise notice 'schedule-cards: application/json already allowed (%)', array_to_string(v_mimes, ', ');
  else
    update storage.buckets
       set allowed_mime_types = v_mimes || array['application/json']
     where id = 'schedule-cards';
    raise notice 'schedule-cards: application/json added (now %)',
      array_to_string(v_mimes || array['application/json'], ', ');
  end if;
end $$;

/* ---- 2. replace the INSERT policy, dropped BY SHAPE not by name --------------------------------
   The live policy is named "students upload schedule cards 1iwvaul_0" — a name the Storage
   Policies UI generated, which no migration should ever have to know. Permissive policies OR
   together, so leaving the old one in place would leave its unconditional WITH CHECK live and make
   the new one decorative. Anything that is an INSERT policy on storage.objects and mentions this
   bucket is the thing being replaced, whatever it is called. */
do $$
declare r record;
begin
  for r in
    select policyname
      from pg_policies
     where schemaname = 'storage'
       and tablename  = 'objects'
       and cmd        = 'INSERT'
       and coalesce(with_check, '') like '%schedule-cards%'
  loop
    execute format('drop policy %I on storage.objects', r.policyname);
    raise notice 'dropped INSERT policy %', r.policyname;
  end loop;
end $$;

/* The two names scToken() can produce, and nothing else: 16 random bytes rendered as 32 lowercase
   hex characters, then .png for the picture or .json for the week. No folders, no traversal, and
   no using a public student-facing bucket as free general-purpose file storage.
   Kept in step with the client by check-sharecards.mjs, which reads this regex out of this file
   and runs the real scToken() against it. */
create policy "schedule card insert"
  on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'schedule-cards'
    and name ~ '^[0-9a-f]{32}\.(png|json)$'
  );

/* ---- 3. say what the database now believes ---------------------------------------------------- */
do $$
declare
  v_mimes text;
  v_pol   text;
begin
  select array_to_string(allowed_mime_types, ', ') into v_mimes
    from storage.buckets where id = 'schedule-cards';
  select string_agg(policyname, ', ') into v_pol
    from pg_policies
   where schemaname = 'storage' and tablename = 'objects'
     and cmd = 'INSERT' and coalesce(with_check, '') like '%schedule-cards%';
  raise notice 'schedule-cards now accepts: %', coalesce(v_mimes, '(any)');
  raise notice 'schedule-cards INSERT policies: %', coalesce(v_pol, '(none)');
end $$;
