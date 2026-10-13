-- TermChamp: slurs are refused in chat messages (2026-10-07) — RUN ONLY IF APP REVIEW ASKS, or Tate decides
--
-- Apple 1.2 wants "a method for filtering objectionable material" wherever users post. Names, reviews
-- and group names already go through the word filter; chat messages deliberately do not (Tate,
-- 2026-09-07: "chats between friends are not [held to a standard], because those are your friends").
-- If App Review cites 1.2 for messages, this is the narrowest answer that keeps that rule's spirit:
--
--   · ONLY unambiguous slurs — a subset of the "Slurs" lines of wf_words(). Words that are also ordinary
--     words or names in a student's chat are left out on purpose (checked 2026-10-07): abo ("ABO blood
--     type"), wop ("woop"), coon ("Maine Coon", surnames), chink ("a chink in his armor"), tranny (a
--     car's transmission), tard ("plus tard"), retard ("retard the timing"), kike ("Kike" = Enrique),
--     spic ("spic and span"), gyppo, pikey, cripple, spastic, ladyboy. Plurals and a slur followed
--     by "!" / "?" / "." are caught. Profanity between friends stays allowed — "fuck this midterm" sends.
--   · Only text messages (kind 'text'), on insert and on edit of the body. Class/professor cards and
--     Champ answers carry no free text from the sender.
--   · Same matcher as everything else (wf_norm / wf_split, word boundaries), so "Van Dyke",
--     "raccoon", "Scunthorpe" etc. pass, and the same cheap evasions (f.a.g, sp1c) are caught.
--   · The sender reads: "Messages can't contain slurs. Change it and try again." (P0001, which the
--     app shows verbatim since build 2026-10-07's native-review-polish patch; the draft stays.)
--
-- Needs professify-word-filter.sql (live). Adds two functions and one trigger; deletes nothing;
-- existing messages are untouched. Safe to run twice. To undo:
--   drop trigger if exists wf_slur_guard_messages on public.messages;

begin;

do $$ begin
  if to_regproc('public.wf_norm') is null or to_regproc('public.wf_split') is null then
    raise exception 'the word filter is not on this database — run professify-word-filter.sql first';
  end if;
end $$;

-- Unambiguous slurs only, every one also in wf_words(). Kept separate so the profanity lines can never
-- reach a chat by accident.
create or replace function public.wf_slurs()
returns text[]
language sql
immutable
as $$
  select array[
    'nigger','nigga','sandnigger','jigaboo','wetback','beaner','towelhead','raghead','gook',
    'faggot','fagot','fag','shemale',
    'retarded','mongoloid'
  ]
$$;

-- Checked twice: as typed (so "f@g" and "n1gger" are caught by wf_norm's substitutions) and with
-- ! ? . , turned into spaces first (wf_norm reads "!" as "i", which hid "fag!" and "nigger!").
-- A trailing s/z is allowed on every word (plurals).
create or replace function public.wf_slur_hit(t text)
returns text
language sql
immutable
as $$
  select w
    from unnest(public.wf_slurs()) as w,
         unnest(array[t, regexp_replace(coalesce(t, ''), '[!?.,]', ' ', 'g')]) as v
   where public.wf_norm(v)  ~ ('(^|[^a-z])' || regexp_replace(w, '(.)', '\1+', 'g') || '[sz]?([^a-z]|$)')
      or public.wf_split(v) ~ ('(^|[^a-z])' || regexp_replace(w, '(.)', '\1+', 'g') || '[sz]?([^a-z]|$)')
   limit 1
$$;

create or replace function public.wf_slur_guard_message()
returns trigger
language plpgsql
as $$
begin
  if coalesce(NEW.kind, 'text') <> 'text' or NEW.body is null or NEW.body = '' then return NEW; end if;
  if TG_OP = 'UPDATE' and NEW.body is not distinct from OLD.body then return NEW; end if;
  if public.wf_slur_hit(NEW.body) is not null then
    raise exception 'Messages can''t contain slurs. Change it and try again.' using errcode = 'P0001';
  end if;
  return NEW;
end $$;

revoke all on function public.wf_slurs() from public;
revoke all on function public.wf_slur_hit(text) from public;
revoke all on function public.wf_slur_guard_message() from public;

drop trigger if exists wf_slur_guard_messages on public.messages;
create trigger wf_slur_guard_messages before insert or update of body on public.messages
  for each row execute function public.wf_slur_guard_message();

do $$
begin
  if not exists (select 1 from pg_trigger where tgname = 'wf_slur_guard_messages' and tgrelid = 'public.messages'::regclass) then
    raise exception 'the message slur filter did not attach';
  end if;
  if public.wf_slur_hit('want to grab food after BUS 3431? this midterm is fucking hard') is not null then
    raise exception 'an ordinary message (with profanity) would be refused';
  end if;
  if public.wf_slur_hit('my roommate Van Dyke saw a raccoon in Scunthorpe') is not null
     or public.wf_slur_hit('ABO blood type for BIO 3312, woop woop!') is not null
     or public.wf_slur_hit('a Maine Coon, plus tard, spic and span, Kike Hernandez, a chink in his armor') is not null
     or public.wf_slur_hit('my tranny is slipping, retard the timing, custard, tardy, Niger, Wopat, Cooney') is not null then
    raise exception 'an innocent message would be refused';
  end if;
  if public.wf_slur_hit('you f.a.g') is null or public.wf_slur_hit('Fag!') is null or public.wf_slur_hit('faggots?') is null
     or public.wf_slur_hit('such retarded people.') is null then
    raise exception 'an evaded, punctuated or plural slur gets through';
  end if;
  -- every slur here must also be in the main list, so the two never disagree about what a slur is
  if exists (select 1 from unnest(public.wf_slurs()) w where not (w = any(public.wf_words()))) then
    raise exception 'wf_slurs() has a word that is not in wf_words()';
  end if;
end $$;

commit;
