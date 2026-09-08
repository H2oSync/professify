-- ================================================================================================
-- WORD FILTER — 7 September 2026
-- ================================================================================================
-- Tate's rule, and the whole design follows from it:
--
--     names, profile photos and reviews are held to a standard; chats between friends are not,
--     because those are your friends.
--
-- So this guards the surfaces where a word reaches somebody who did not choose to hear from you:
--
--     profiles.display_name, profiles.username   your identity on every screen in the app
--     reviews.note                               public, and the thing the app exists for
--     community_posts.body                       seen by people who are not your friends
--     groups.name                                sits in the message list of everyone in the group,
--                                                including people added later by somebody else
--
-- and deliberately does NOT touch:
--
--     messages.body, conversations.title         a direct message is between friends
--     free_now.note                              friends-only status, closest thing to a chat
--
-- WHY THIS IS IN THE DATABASE. The app checks as you type, which is the useful half — nobody
-- writes 200 words and then loses them. But that check is a courtesy, exactly like `maxlength`:
-- anyone POSTing straight to PostgREST ignores it. The trigger below is the control.
--
-- WHAT A WORD LIST HONESTLY DOES. It stops the careless and the opportunistic. It does not stop
-- somebody determined to get a slur past it — they will find a spelling, and every extra rule
-- that chases them costs a false positive against a real student. What actually stops the
-- determined person is that the name is attached to a verified @calpoly.edu account that can be
-- suspended. This is the cheap layer; moderation is the real one.
--
-- WHAT IS DELIBERATELY NOT IN THE LIST. Identity words — gay, lesbian, bi, trans, queer, and the
-- like. They are not slurs, students are named and write about them, and a filter that blocks
-- them does more harm than the words it catches. Slurs aimed AT those groups are in the list.
--
-- Safe to re-run. Adds no columns and deletes nothing; the final section is a read-only scan that
-- names existing rows that would fail, so you can decide what to do about them.
-- ================================================================================================


-- ------------------------------------------------------------------------------------------------
-- 1. The list. This is the only place to edit — everything below reads it.
-- ------------------------------------------------------------------------------------------------
create or replace function public.wf_words()
returns text[]
language sql
immutable
as $$
  select array[
    -- Slurs. No legitimate use in a display name or a review of a class.
    'nigger','nigga','chink','gook','spic','wetback','beaner','kike','wop',
    'towelhead','raghead','sandnigger','coon','jigaboo','abo','gyppo','pikey',
    'faggot','fag','fagot','tranny','shemale','ladyboy',
    -- 'dyke' is NOT here, and the self-check is why: it blocked "Van Dyke", which is a surname
    -- students actually have, and a dyke is also an embankment. A filter that refuses a real
    -- student their own name is worse than the word it catches. If it turns up as an insult
    -- that is a moderation call, which is what moderation is for.
    'retard','retarded','tard','spastic','mongoloid','cripple',

    -- Profanity. Fine in a chat with your friends; not on a public review or a name every
    -- student sees next to your face.
    'fuck','fucker','fucking','motherfucker','clusterfuck',
    'shit','bullshit','shithead','shitty',
    'cunt','twat','bitch','bastard','whore','slut','skank',
    'dick','cock','prick','wanker','wank','jackoff','jerkoff',
    'asshole','arsehole','dumbass','jackass','asshat',
    'pussy','tits','titty','boobs','blowjob','handjob','rimjob',
    'cum','jizz','dildo','buttplug','felch','queef',
    'pedo','pedophile','rapist','molester',

    -- Not profanity, but not a name either: impersonating the app or the university.
    'professify','calpoly','mustangs'
  ]
$$;

-- USERNAMES ARE A DIFFERENT PROBLEM. A display name has spaces, so a word boundary tells you
-- where one word ends. A username does not: "fuckface" is one token, and \y finds no boundary
-- inside it, so the bounded matcher above lets it straight through.
--
-- The fix is to match usernames as a bare substring — but only against words that are SAFE as a
-- substring, and that is not a judgement call. Every word in wf_words() was run as a substring
-- against 76,274 English words plus a list of surnames people actually have, and any word that
-- lit up an innocent one was excluded. The excluded ones and why:
--
--     cum      accumulate, document, acumen           cock   Hancock, Cockburn, peacock
--     spic     auspicious, conspicuous, allspice      anal   analysis  (dropped from the list)
--     tard     custard, mustard, leotard, dotard      shit   shiitake, Shiite, mishit
--     dick     Dickinson, Dickens, Chappaquiddick     coon   raccoon, cocoon, tycoon
--     twat     saltwater, smartwatch, nightwatchman   pedo   pedometer, pedology
--     fag      leafage, wharfage, Antofagasta         wank   swanky, Wankel
--     nigga    niggardly  (unrelated etymology)       dyke   Van Dyke
--     cunt     Scunthorpe                             slut   Slutsky (the economist)
--     tits     Titsworth                              chink  chinkapin
--     rapist   therapist, physiotherapist             abo    abbot, abolish, aboard
--     prick    prickly, pinprick                      wop    swoop, twopence
--     gook     gobbledygook                           beaner beanery
--     retard   retardation  (retarded is safe)        spastic epispastic
--
-- Those still apply to a display name, where the boundary does the work. They just cannot be
-- used on a token with no boundaries in it.
create or replace function public.wf_words_tight()
returns text[]
language sql
immutable
as $$
  select array[
    'arsehole','asshat','asshole','bastard','bitch','blowjob','boobs','bullshit','buttplug',
    'clusterfuck','cripple','dildo','dumbass','faggot','fagot','felch','fuck','fucker','fucking',
    'gyppo','handjob','jackass','jackoff','jerkoff','jigaboo','jizz','kike','ladyboy','molester',
    'mongoloid','motherfucker','pedophile','pikey','pussy','queef','raghead','retarded','rimjob',
    'sandnigger','shemale','shithead','shitty','skank','titty','towelhead','tranny','wanker',
    'wetback','whore'
  ]
$$;

-- Usernames only. A display name may legitimately contain any of these; a HANDLE that reads as
-- an official account is impersonation whatever the words around it are.
create or replace function public.wf_reserved_usernames()
returns text[]
language sql
immutable
as $$
  select array[
    'admin','administrator','moderator','mod','staff','support','help','helpdesk',
    'professify','professifyapp','official','team','root','system','security',
    'calpoly','calpolyslo','cpslo','mustang','mustangs','registrar','advising',
    'polyratings','anonymous','anon','deleted','null','undefined','me','you','everyone'
  ]
$$;


-- ------------------------------------------------------------------------------------------------
-- 2. Normalisation — the cheap evasions, and only those
-- ------------------------------------------------------------------------------------------------
-- Lowercase; map the digits and symbols people substitute for letters; and pull out a separator
-- sitting BETWEEN two letters so f.u.c.k and f-u-c-k read as one word.
--
-- The lookahead in the second replace is load-bearing. Without it the match consumes the letter
-- after the separator too, the scan resumes past it, and every second separator survives:
-- 'f.u.c.k' comes out as 'fu.ck'. With (?=[a-z]) the match ends at the separator, so the next
-- letter is still available to start the next match.
--
-- Not handled: letters spaced apart with real spaces ('f u c k'). Catching that means joining
-- every word in the string together, and then 'a class ass' becomes a hit inside 'class'. The
-- false positives cost more than the evasion does.
create or replace function public.wf_norm(t text)
returns text
language sql
immutable
as $$
  select regexp_replace(
           translate(lower(coalesce(t, '')), '0134578@$!|', 'oieastbasil'),
           '([a-z])[._*-]+(?=[a-z])', '\1', 'g')
$$;

-- The same string with those separators turned into SPACES instead of removed, and both forms are
-- tested. One form alone is always wrong in one direction: joining makes 'f.u.c.k' readable but
-- turns 'fuck_face' into one long token with no boundary in it, and the boundary is what the
-- matcher needs; splitting catches 'fuck_face' but leaves 'f.u.c.k' as four one-letter words.
-- Testing both costs one more regex and closes both shapes.
create or replace function public.wf_split(t text)
returns text
language sql
immutable
as $$
  select translate(lower(coalesce(t, '')), '0134578@$!|._*-', 'oieastbasil    ')
$$;


-- ------------------------------------------------------------------------------------------------
-- 3. The match
-- ------------------------------------------------------------------------------------------------
-- Each listed word becomes a pattern where every letter may repeat — 'ass' becomes 'a+s+s+' — so
-- 'assss' and 'fuuuuck' are caught. Anchored on a NON-LETTER at both ends, which is
-- what keeps 'class', 'assignment', 'Scunthorpe', 'analysis', 'passage' and 'Hancock' out of it.
--
-- (^|[^a-z]) and not \y, and the difference is not cosmetic: \y counts digits and underscores as
-- word characters, so \yfuck\y does not match 'fuck_face' or 'fuck2' — the first two shapes
-- anybody reaches for. [^a-z] treats both as boundaries and catches them.
--
-- And never \b: in POSIX regular expressions \b is a backspace character, so \b here would
-- silently match nothing and this whole file would be decoration.
create or replace function public.wf_hit(t text)
returns text
language sql
immutable
as $$
  select w
    from unnest(public.wf_words()) as w
   where public.wf_norm(t)  ~ ('(^|[^a-z])' || regexp_replace(w, '(.)', '\1+', 'g') || '([^a-z]|$)')
      or public.wf_split(t) ~ ('(^|[^a-z])' || regexp_replace(w, '(.)', '\1+', 'g') || '([^a-z]|$)')
   order by length(w) desc
   limit 1
$$;

-- Same repeat-tolerant pattern, no boundaries: for a username, the whole handle is one word.
create or replace function public.wf_hit_tight(t text)
returns text
language sql
immutable
as $$
  select w
    from unnest(public.wf_words_tight()) as w
   where public.wf_norm(t) ~ regexp_replace(w, '(.)', '\1+', 'g')
   order by length(w) desc
   limit 1
$$;

create or replace function public.wf_reserved(t text)
returns boolean
language sql
immutable
as $$
  select lower(trim(coalesce(t, ''))) = any(public.wf_reserved_usernames())
$$;


-- ------------------------------------------------------------------------------------------------
-- 4. The guard
-- ------------------------------------------------------------------------------------------------
-- Generic over columns so one function covers every table: TG_ARGV[0] is what to call the field
-- in the error, the rest are column names.
--
-- On UPDATE a column is only checked if it CHANGED. Without that, a student whose display name
-- predates this file could never edit their major again — the trigger would refuse a write that
-- has nothing to do with the name. Grandfathered rows stay until somebody touches them or a
-- moderator does, which is the read-only scan at the bottom of this file.
--
-- errcode P0001 is deliberate: the client's dbFriendlyErr() passes a P0001 message through to the
-- student verbatim, so the sentence written here is the sentence they read.
create or replace function public.wf_guard()
returns trigger
language plpgsql
as $$
declare
  i     int;
  col   text;
  val   text;
  prev  text;
  w     text;
  label text;
begin
  label := coalesce(TG_ARGV[0], 'That');

  for i in 1 .. (TG_NARGS - 1) loop
    col := TG_ARGV[i];
    execute format('select ($1).%I::text', col) into val using NEW;

    if TG_OP = 'UPDATE' then
      execute format('select ($1).%I::text', col) into prev using OLD;
      if val is not distinct from prev then
        continue;                       -- untouched, so not this write's problem
      end if;
    end if;

    if val is null or val = '' then
      continue;
    end if;

    w := public.wf_hit(val);
    if w is not null then
      raise exception '% can''t contain "%" — change it and try again.', label, w
        using errcode = 'P0001';
    end if;
  end loop;

  return NEW;
end;
$$;

create or replace function public.wf_guard_username()
returns trigger
language plpgsql
as $$
declare w text;
begin
  if TG_OP = 'UPDATE' and NEW.username is not distinct from OLD.username then
    return NEW;
  end if;
  if NEW.username is null or NEW.username = '' then
    return NEW;
  end if;
  if public.wf_reserved(NEW.username) then
    raise exception 'That username is reserved. Pick another one.'
      using errcode = 'P0001';
  end if;
  w := public.wf_hit_tight(NEW.username);
  if w is not null then
    raise exception 'That username contains "%" — pick another one.', w
      using errcode = 'P0001';
  end if;
  return NEW;
end;
$$;


-- ------------------------------------------------------------------------------------------------
-- 5. Attach, only where the rule says to
-- ------------------------------------------------------------------------------------------------
do $$
declare
  t record;
  present text[];
  c text;
begin
  for t in
    select * from (values
      ('profiles',        'Your name',   array['display_name']),   -- username: wf_guard_username
      ('reviews',         'A review',    array['note']),
      ('community_posts', 'A post',      array['body']),
      ('groups',          'A group name',array['name'])
    ) as v(tbl, label, cols)
  loop
    if to_regclass('public.' || t.tbl) is null then
      raise notice 'skip %: not on this deploy', t.tbl;
      continue;
    end if;

    -- only name columns this deploy actually has, so a missing optional column is not fatal
    present := array[]::text[];
    foreach c in array t.cols loop
      if exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name=t.tbl and column_name=c) then
        present := present || c;
      end if;
    end loop;

    if array_length(present, 1) is null then
      raise notice 'skip %: none of its guarded columns exist', t.tbl;
      continue;
    end if;

    execute format('drop trigger if exists wf_guard_%s on public.%I', t.tbl, t.tbl);
    execute format(
      'create trigger wf_guard_%s before insert or update on public.%I
         for each row execute function public.wf_guard(%L, %s)',
      t.tbl, t.tbl, t.label,
      (select string_agg(quote_literal(x), ', ') from unnest(present) as x));
    raise notice 'guarding %.{%}', t.tbl, array_to_string(present, ', ');
  end loop;

  if to_regclass('public.profiles') is not null
     and exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='profiles' and column_name='username')
  then
    drop trigger if exists wf_reserved_profiles on public.profiles;
    create trigger wf_reserved_profiles before insert or update on public.profiles
      for each row execute function public.wf_guard_username();
    raise notice 'guarding reserved usernames';
  end if;
end $$;

-- The list is data, not a document. Nobody outside these functions needs to read it, and a
-- readable list of what is blocked is a readable list of what to try next.
revoke all on function public.wf_words()              from public;
revoke all on function public.wf_reserved_usernames() from public;
revoke all on function public.wf_norm(text)           from public;
revoke all on function public.wf_split(text)          from public;
revoke all on function public.wf_hit(text)            from public;
revoke all on function public.wf_words_tight()        from public;
revoke all on function public.wf_hit_tight(text)      from public;
revoke all on function public.wf_reserved(text)       from public;


-- ------------------------------------------------------------------------------------------------
-- 6. SELF-CHECK — must-block and must-NOT-block, both. Raises if either side is wrong.
-- ------------------------------------------------------------------------------------------------
do $$
declare
  s text;
  bad int := 0;
  block_these text[] := array[
    'fuck','FUCK','Fuck this class','fuuuuck','f.u.c.k','f-u-c-k','fu*ck','sh1t','a55hole',
    'what the fuck','asshole','ASSHOLE','retard','n1gger','b!tch','c0ck','Dumbass',
    'fuck_face','fuck2','2fuck','_shit_'
  ];
  -- Not a hand-picked list. wf_words() was run as a bare substring against 76,274 English
  -- words plus real surnames; these are the ones that lit up, so they are exactly the words a
  -- boundary-blind filter gets wrong. If any of them is ever blocked, the filter is worse than
  -- not having one.
  allow_these text[] := array[
    'accumulate','document','acumen','circumstance','Hancock','Cockburn','peacock','cockpit',
    'auspicious','conspicuous','allspice','analysis','analytics','annals','custard','mustard',
    'leotard','dotard','shiitake','Shiite','mishit','Dickinson','Dickens','Dickerson',
    'raccoon','cocoon','tycoon','saltwater','smartwatch','nightwatchman','pedometer','pedology',
    'leafage','wharfage','swanky','Wankel','niggardly','Van Dyke','Scunthorpe','Slutsky',
    'Titsworth','chinkapin','therapist','physiotherapist','abbot','abolish','aboard','prickly',
    'pinprick','swoop','twopence','gobbledygook','beanery','retardation','epispastic',
    'Niger','Nigeria','Nigerian',
    -- identity words are not slurs and are never in the list
    'gay','lesbian','trans','queer','bisexual','Gay Nelson',
    -- and the ordinary things a student types all day
    'class','classes','Class of 2027','assignment','assessment','passage','bass','grass',
    'assassin','Massachusetts','associate','password','Cummings','Matthew','professor',
    'possess','embarrassed','harassment','glass','brass','Uranus','Essex','Sussex','titles',
    'Assignments were fair','I passed the class','BUS 2200','MATH 141','CSC 357',
    'He is anal about deadlines'
  ];
  -- usernames are matched without boundaries, so they get their own must-block and must-allow
  block_user text[] := array['fuckface','xXfuckXx','asshole99','th3.r3tard3d.one','wh0re'];
  allow_user text[] := array['cassandra','bassist','classic','vandyke','dickinson','hancock',
                             'documents','analysis','custard','therapist','nigeria','scunthorpe',
                             'shiitake','swanky','abbot','prickly','saltwater','pedometer'];
begin
  -- the list itself must be plain letters: a metacharacter would break the pattern builder
  foreach s in array public.wf_words() loop
    if s !~ '^[a-z]+$' then
      raise exception 'word list entry % is not plain lowercase letters', s;
    end if;
  end loop;

  foreach s in array block_these loop
    if public.wf_hit(s) is null then
      raise notice 'MISS  should have been blocked: %', s;
      bad := bad + 1;
    end if;
  end loop;

  foreach s in array allow_these loop
    if public.wf_hit(s) is not null then
      raise notice 'FALSE POSITIVE  "%" blocked by "%"', s, public.wf_hit(s);
      bad := bad + 1;
    end if;
  end loop;

  foreach s in array block_user loop
    if public.wf_hit_tight(s) is null then
      raise notice 'MISS  username should have been blocked: %', s;
      bad := bad + 1;
    end if;
  end loop;

  foreach s in array allow_user loop
    if public.wf_hit_tight(s) is not null then
      raise notice 'FALSE POSITIVE  username "%" blocked by "%"', s, public.wf_hit_tight(s);
      bad := bad + 1;
    end if;
  end loop;

  -- every tight word must also be in the main list, or a username could be stricter than a name
  foreach s in array public.wf_words_tight() loop
    if not (s = any(public.wf_words())) then
      raise exception 'wf_words_tight() has "%" which is not in wf_words()', s;
    end if;
  end loop;

  if bad > 0 then
    raise exception '% self-check failure(s) above — the filter is not safe to leave on', bad;
  end if;
  raise notice 'OK — % + % blocked, % + % allowed, no false positives',
               array_length(block_these,1), array_length(block_user,1),
               array_length(allow_these,1), array_length(allow_user,1);
end $$;


-- ------------------------------------------------------------------------------------------------
-- 7. What is already in the tables. READ-ONLY — nothing here changes a row.
--    Rows listed below predate the trigger and are still visible. Deciding what happens to them
--    is a moderation call, not a migration.
-- ------------------------------------------------------------------------------------------------
select 'profiles.display_name' as where_, id::text as row_id, public.wf_hit(display_name) as word
  from public.profiles where public.wf_hit(display_name) is not null
union all
select 'profiles.username', id::text, public.wf_hit_tight(username)
  from public.profiles where public.wf_hit_tight(username) is not null
union all
select 'reviews.note', id::text, public.wf_hit(note)
  from public.reviews where public.wf_hit(note) is not null
order by 1, 2;
