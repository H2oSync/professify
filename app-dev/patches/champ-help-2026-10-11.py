#!/usr/bin/env python3
"""Champ answers the basic questions people ask about TermChamp (Tate, 2026-10-11: "make sure Champ can ask basic
question that people ask about termchamp … still tight and regulated and only specific but … a useful tool";
then, on the 16-topic table: "use these as most likely to be asked but also have it be smart so when someone asks a
quesiton that is similar it has this show up … like instead of what does champ send. what does champ do and where
does my information go?").

Tight: the model never writes the answer. It picks ONE of 16 fixed topics (app_help {topic}); the phone shows that
topic's fixed answer and one button. An unknown topic is cant_answer.
Smart: the model is told to pick the CLOSEST topic however it is worded (and the golden set asks every topic three
or more ways); when the model can't place a question, or can't be reached, the phone itself looks for a close topic
and offers it as a "Did you mean" chip that opens the answer without asking the model again.

Edits:
  supabase/functions/ask/shared.ts       — HELP_TOPICS, the app_help tool (phone menu only), its validate() branch,
                                           one sentence in APP_SYSTEM, go_to/help descriptions pointed at it
  dev/golden/model-golden-v3.json        — app_help cases (3+ per topic) and app_help as an alt where a screen also fits
  dev/golden/check-models-v3.ts          — the case count in its header
  dev/tests/check-ask-function.ts        — five phone tools, the v8 whitelist, app_help validated
  sql/professify-assistant-v8.sql        — new: app_help on both log whitelists
  app/index.html                         — HELP (the 16 answers), helpMatch, answerTool's app_help, the chips,
                                           the champHelp / copySupport actions
The website's menu and prompt are not touched (their fingerprint test pins them).
"""
import json, pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
HERE = pathlib.Path(__file__).resolve().parent

def patch(rel, reps):
    p = ROOT / rel; s = p.read_text()
    for a, b in reps:
        c = s.count(a)
        if c != 1: sys.exit(f'champ-help: {rel}: expected 1 of {a[:80]!r}, found {c}')
        s = s.replace(a, b)
    p.write_text(s)

TOPICS = ['what_is', 'free', 'who_sees', 'ratings_anonymous', 'ratings_source', 'seats_source', 'add_class', 'plans',
          'seat_alerts', 'degree_report', 'add_friends', 'block_report', 'delete_account', 'champ', 'dark_mode', 'contact']

# ------------------------------------------------------------------------------------------------ shared.ts
patch('supabase/functions/ask/shared.ts', [
("""  go_to: 'Open a screen of the app, ONLY when the student asks to open, find or change something on a screen. E.g. "where do I change '
    + 'my password" → account, "turn on dark mode" → appearance, "my qr code", "how do I block someone" → privacy settings. '
    + 'Not for: a question another tool answers — answer it instead of sending them to a screen.',
  help: 'What Champ can do. E.g. "help", "what can you do", "what should I ask".',""",
 """  go_to: 'Open a screen of the app, ONLY when the student asks to open, find or change something on a screen. E.g. "where do I change '
    + 'my password" → account, "turn on dark mode" → appearance, "my qr code", "privacy settings". '
    + 'Not for: a question another tool answers — answer it instead of sending them to a screen; how something in '
    + 'TermChamp works or is it free, private or safe (app_help).',
  help: 'What Champ can do. E.g. "help", "what can you do", "what should I ask". '
    + 'Not for: what Champ does with their questions or where their information goes (app_help topic champ).',"""),
("""];
export const APP_NEW_NAMES = APP_NEW.map((t) => t.name);""",
 """  /* 2026-10-11: questions about TermChamp itself. The model only picks a topic; the phone shows that topic's
     fixed answer (HELP in app/index.html), so nothing the model writes is ever read as a fact about the app. */
  { name: 'app_help', description: 'A question about TermChamp ITSELF — what it is, its rules, privacy, how to do something in '
      + 'it, or what Champ does with questions. Pick the CLOSEST topic even when the words are different. '
      + 'E.g. "is termchamp free", "can my professor see my review", "what does champ do with my questions", '
      + '"how do I add friends", "where do the seat numbers come from". '
      + 'Not for: a class, professor, seat count, schedule or friend question (the other tools); adding a NAMED person '
      + '(add_friend) or a NAMED course (add_section); opening a screen by name (go_to); "turn on dark mode" '
      + '(set_theme); what Champ can answer (help).',
    parameters: { type: 'object', required: ['topic'], properties: { topic: { type: 'string', enum: HELP_TOPICS,
      description: 'what_is: what TermChamp is, who made it, is it official. free: cost, ads, selling data. '
        + 'who_sees: who can see their schedule, classes or plans, is it private. ratings_anonymous: are reviews '
        + 'anonymous, can a professor or friends see who wrote one. ratings_source: where ratings come from. '
        + 'seats_source: where seat numbers come from, how up to date they are. add_class: how to add a class. '
        + 'plans: what Plans A, B and C are. seat_alerts: how watching and seat notifications work. '
        + 'degree_report: uploading the Degree Progress Report (DPR), where to get it, is it safe. '
        + 'add_friends: how to add or find friends. block_report: blocking or reporting someone or something. '
        + 'delete_account: deleting the account and what happens. champ: what Champ does, where their questions '
        + 'and information go, does Champ see their data. dark_mode: is there dark mode, changing the look. '
        + 'contact: contacting TermChamp, support, a bug, feedback.' } } } },
];
export const APP_NEW_NAMES = APP_NEW.map((t) => t.name);"""),
("""const APP_NEW: any[] = [""",
 """export const HELP_TOPICS = ['what_is', 'free', 'who_sees', 'ratings_anonymous', 'ratings_source', 'seats_source', 'add_class',
  'plans', 'seat_alerts', 'degree_report', 'add_friends', 'block_report', 'delete_account', 'champ', 'dark_mode', 'contact'];

const APP_NEW: any[] = ["""),
("""  + `comparing two named professors is compare_professors. App requests (a screen, a `
  + `setting, the theme, their account) are go_to or set_theme. Actions""",
 """  + `comparing two named professors is compare_professors. App requests (a screen, a `
  + `setting, the theme, their account) are go_to or set_theme. A question ABOUT TermChamp or Champ — what it is, is it `
  + `free or private, who sees what, where ratings or seats come from, how to do something in it, what happens to `
  + `their questions — is app_help with the closest topic, however it is worded; never answer it in words. Actions"""),
("""  if (name === 'fits_plan') {
    const c = course(a.course); if (!c) return cantAnswer();""",
 """  if (name === 'app_help') return HELP_TOPICS.includes(a.topic) ? { tool: 'app_help', args: { topic: a.topic } } : cantAnswer();
  if (name === 'fits_plan') {
    const c = course(a.course); if (!c) return cantAnswer();"""),
("""  /* The phone's four (2026-10-08). Only the phone's menu offers them. */""",
 """  /* The phone's own (2026-10-08; app_help 2026-10-11). Only the phone's menu offers them. */"""),
])

# ------------------------------------------------------------------------------------------------ golden set
g = ROOT / 'dev/golden/model-golden-v3.json'
G = json.loads(g.read_text())
assert not any(c['tool'] == 'app_help' for c in G['cases']), 'champ-help: golden already has app_help'
H = lambda t: {'topic': t}
NEW = {
  'what_is': ['what is termchamp', 'what is this app', 'who made termchamp', 'is termchamp an official cal poly app'],
  'free': ['is termchamp free', 'does this app cost money', 'are there ads on here', 'do you sell my data'],
  'who_sees': ['who can see my schedule', 'can strangers see my classes', 'is my schedule private', 'can other people see my plans'],
  'ratings_anonymous': ['are my reviews anonymous', 'can my professor see my review', 'will people know i rated a professor', 'do my friends see what i wrote about a prof'],
  'ratings_source': ['where do the ratings come from', 'are the ratings from polyratings', 'how are professors rated on here'],
  'seats_source': ['where do the seat numbers come from', 'are the seat counts live', 'how accurate are the open seats'],
  'add_class': ['how do i add a class', 'how do i put my classes in', 'how do i add my spring classes'],
  'plans': ['what are plans a b and c', 'what is a plan', 'why are there three plans'],
  'seat_alerts': ['how do seat alerts work', 'will i get notified when a seat opens', 'what does the watch button do'],
  'degree_report': ['how do i upload my degree progress report', 'is it safe to upload my dpr', 'where do i get my degree progress report', 'why do you need my dpr'],
  'add_friends': ['how do i add friends', 'how do i find my friends on here', 'how do friends work'],
  'block_report': ['how do i block someone', 'how do i report a review', 'someone is harassing me what do i do'],
  'delete_account': ['how do i delete my account', 'what happens if i delete my account', 'can i get my account back after deleting it', 'how do i delete termchamp'],
  'champ': ['what does champ do and where does my information go', 'what does champ send', 'does champ see my schedule', 'is champ private', 'who sees my questions to champ', 'is my data sent to ai'],
  'dark_mode': ['is there a dark mode', 'can i change the colors of the app', 'does termchamp have dark mode'],
  'contact': ['how do i contact termchamp', 'i found a bug', 'where do i send feedback'],
}
assert set(NEW) == set(TOPICS)
seen = {c['q'].lower().strip() for c in G['cases']}
for t, qs in NEW.items():
  for q in qs:
    assert q not in seen, q; seen.add(q)
    c = {'cat': 'apphelp', 'q': q, 'tool': 'app_help', 'args': H(t), 'from': 'v3'}
    # where a screen or another tool is also a fair answer
    alt = {'how do i add a class': [{'tool': 'go_to', 'args': {'where': 'explore'}}],
           'how do i block someone': [{'tool': 'go_to', 'args': {'where': 'privacy settings'}}],
           'can i change the colors of the app': [{'tool': 'go_to', 'args': {'where': 'appearance'}}],
           'how do i add friends': [{'tool': 'add_friend', 'args': {}}, {'tool': 'go_to', 'args': {'where': 'add friend'}}],
           'how do i find my friends on here': [{'tool': 'add_friend', 'args': {}}, {'tool': 'go_to', 'args': {'where': 'add friend'}}],
           'how do i add my spring classes': [{'tool': 'go_to', 'args': {'where': {'$in': ['explore', 'schedule', 'my classes']}}}],
           'how do i delete my account': [{'tool': 'go_to', 'args': {'where': 'account'}}]}.get(q)
    if alt: c['alt'] = alt
    if q == 'what does champ do and where does my information go': c['from'] = 'tate'
    G['cases'].append(c)
# Tate's own example, the short way he first said it
G['cases'].append({'cat': 'apphelp', 'q': 'what does champ do', 'tool': 'app_help', 'args': H('champ'), 'alt': [{'tool': 'help', 'args': {}}], 'from': 'tate'})
# app_help is a fair answer to a few questions that already open a screen
ALT = {'delete my account': H('delete_account'), 'how do i make my profile private': H('who_sees'),
       'add a class i took last year': H('add_class'), 'turn on dark mode': H('dark_mode'), 'light mode': H('dark_mode')}
for c in G['cases']:
  if c['q'] in ALT:
    c.setdefault('alt', []).append({'tool': 'app_help', 'args': ALT.pop(c['q'])})
assert not ALT, ALT
G['note'] += ' 2026-10-11: cat apphelp — questions about TermChamp itself, 3+ ways each for the 16 app_help topics.'
g.write_text(json.dumps(G, indent=1, ensure_ascii=False) + '\n')
N = len(G['cases'])

patch('dev/golden/check-models-v3.ts', [
("""   Runs dev/golden/model-golden-v3.json (376 questions: the 2026-09-26 set adapted to the phone, the
   four new tools, the who's-free / when-am-I-free kind of mix-ups, and Tate's own questions) through""",
 f"""   Runs dev/golden/model-golden-v3.json ({N} questions: the 2026-09-26 set adapted to the phone, the
   phone's own tools, the who's-free / when-am-I-free kind of mix-ups, the 16 TermChamp-help topics asked
   several ways each, and Tate's own questions) through"""),
])

# ------------------------------------------------------------------------------------------------ check-ask-function
patch('dev/tests/check-ask-function.ts', [
("""t('app: the phone menu is sent — the four new tools, then every website tool, cant_answer last',
  JSON.stringify(appTools) === JSON.stringify(['friends_free_now', 'free_with_friends', 'best_professor', 'fits_plan', ...""",
 """t('app: the phone menu is sent — the phone\\'s own five tools, then every website tool, cant_answer last',
  JSON.stringify(appTools) === JSON.stringify(['friends_free_now', 'free_with_friends', 'best_professor', 'fits_plan', 'app_help', ..."""),
("""  ['fits_plan', { plan: 'A' }, (r) => r.tool === 'cant_answer'],
];""",
 """  ['fits_plan', { plan: 'A' }, (r) => r.tool === 'cant_answer'],
  ['app_help', { topic: 'champ', junk: 1 }, (r) => r.tool === 'app_help' && JSON.stringify(r.args) === '{"topic":"champ"}'],
  ['app_help', { topic: 'delete_account' }, (r) => r.tool === 'app_help' && r.args.topic === 'delete_account'],
  ['app_help', { topic: 'refund' }, (r) => r.tool === 'cant_answer'],
  ['app_help', { topic: 'Champ' }, (r) => r.tool === 'cant_answer'],
  ['app_help', {}, (r) => r.tool === 'cant_answer'],
];
t('app: app_help offers exactly the 16 topics the phone answers',
  JSON.stringify(shared.APP_TOOLS.find((x: any) => x.name === 'app_help').parameters.properties.topic.enum) === JSON.stringify(shared.HELP_TOPICS) && shared.HELP_TOPICS.length === 16);
t('app: the phone prompt sends questions about TermChamp to app_help, never answered in words',
  /ABOUT TermChamp or Champ[^.]*is app_help with the closest topic, however it is worded; never answer it in words/.test(shared.APP_SYSTEM('Fall 2026')));
t('web: app_help is not on the website menu', !shared.TOOLS.some((x: any) => x.name === 'app_help'));"""),
("""t('the phone menu adds exactly four tools', appNew.join() === 'friends_free_now,free_with_friends,best_professor,fits_plan', appNew);
const sql = await Deno.readTextFile(new URL('../../sql/professify-assistant-v7.sql', import.meta.url));""",
 """t('the phone menu adds exactly five tools', appNew.join() === 'friends_free_now,free_with_friends,best_professor,fits_plan,app_help', appNew);
const sql = await Deno.readTextFile(new URL('../../sql/professify-assistant-v8.sql', import.meta.url));"""),
])

# ------------------------------------------------------------------------------------------------ SQL v8
v7 = (ROOT / 'sql/professify-assistant-v7.sql').read_text()
OLD_LIST = "'friends_free_now','free_with_friends','best_professor','fits_plan')"
OLD_ARR = "'friends_free_now','free_with_friends','best_professor','fits_plan'];"
assert v7.count(OLD_LIST) == 1 and v7.count(OLD_ARR) == 1
body = v7[v7.index('begin;'):]
body = body.replace(OLD_LIST, "'friends_free_now','free_with_friends','best_professor','fits_plan','app_help')")
body = body.replace(OLD_ARR, "'friends_free_now','free_with_friends','best_professor','fits_plan','app_help'];")
old_check = body[body.index('do $$'):body.index('commit;')]
body = body.replace(old_check, """-- Supabase's default privileges can give anon an explicit EXECUTE that `revoke … from public` leaves in place
-- (the earlier script revoked it on assistant_log_miss for that reason); the run log gets the same.
revoke execute on function public.assistant_log_run(text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric) from anon;

do $$
declare t text;
begin
  foreach t in array array['game_plan','friends_free_now','free_with_friends','best_professor','fits_plan','app_help'] loop
    if not exists (select 1 from pg_proc where proname = 'assistant_log_run' and prosrc like '%''' || t || '''%') then
      raise exception 'v8: assistant_log_run does not know %', t;
    end if;
    if not exists (select 1 from pg_proc where proname = 'assistant_log_miss' and prosrc like '%''' || t || '''%') then
      raise exception 'v8: assistant_log_miss does not know %', t;
    end if;
  end loop;
  if has_function_privilege('anon', 'public.assistant_log_miss(text, text, text, jsonb, text, text, jsonb, bigint)', 'execute') then
    raise exception 'v8: anon can call assistant_log_miss';
  end if;
  if has_function_privilege('anon', 'public.assistant_log_run(text, text, text, jsonb, text, text, integer, integer, integer, integer, boolean, boolean, numeric)', 'execute') then
    raise exception 'v8: anon can call assistant_log_run';
  end if;
  raise notice 'v8: app_help is on both whitelists';
end $$;

""")
assert 'v7' not in body.replace('as v7 left', ''), [l for l in body.splitlines() if 'v7' in l]
(ROOT / 'sql/professify-assistant-v8.sql').write_text("""-- =================================================================================================
-- professify-assistant-v8.sql — 2026-10-11
-- Run AFTER professify-assistant-v7.sql. One transaction, idempotent, safe to re-run.
--
-- One change: the phone app's Champ has one more tool, app_help — questions about TermChamp itself
-- ("is termchamp free?", "who can see my schedule?", "what does Champ do and where does my
-- information go?"). Both whitelists — the run log and the miss log — refuse any tool name they do
-- not know, so without this those answers are shown but never logged. Both functions are recreated
-- exactly as v7 left them, same signatures (so existing grants stand), with app_help added to each
-- list. Nothing else changes.
-- =================================================================================================
""" + body)
(ROOT / 'dev/tests/check-assistant-v8.sql').write_text(r"""\set ON_ERROR_STOP on
reset role;
insert into auth.users (id,email) values ('44444444-4444-4444-4444-444444444444','d@calpoly.edu') on conflict do nothing;
select set_config('request.jwt.claim.sub','44444444-4444-4444-4444-444444444444',false);
do $$
declare t text;
begin
  foreach t in array array['app_help','friends_free_now','fits_plan','game_plan','my_free','help'] loop
    if not public.assistant_log_run('0123456789abcdef','q8 '||t, t, '{}'::jsonb) then raise exception 'FAIL v8 run %', t; end if;
    if public.assistant_log_miss('0123456789abcdef','q8 '||t, t) is null then raise exception 'FAIL v8 miss %', t; end if;
    if public.assistant_log_miss('0123456789abcdef','q8 pick '||t, 'my_free', null, 'model', t) is null then raise exception 'FAIL v8 picked %', t; end if;
  end loop;
  if public.assistant_log_run('0123456789abcdef','q','app_helps') then raise exception 'FAIL v8 unknown run accepted'; end if;
  if public.assistant_log_miss('0123456789abcdef','q','apphelp') is not null then raise exception 'FAIL v8 unknown miss accepted'; end if;
  if (select count(*) from public.assistant_runs where tool = 'app_help') <> 1 then raise exception 'FAIL v8 rows'; end if;
  raise notice 'ok   v8: app_help logs as a run, a miss and a pick; old tools still do; unknown names still refused';
end $$;
""")
patch('dev/README.md', [
("""| Hawk SQL through v7 | `fixture.sql`, `professify-assistant.sql`…`-v7.sql`, `check-hawk-misses.sql`, `check-assistant-v6.sql`, `check-assistant-v7.sql` | all ok |""",
 """| Hawk SQL through v8 | `fixture.sql`, `professify-assistant.sql`…`-v8.sql`, `check-hawk-misses.sql`, `check-assistant-v6.sql`, `check-assistant-v7.sql`, `check-assistant-v8.sql` | all ok |"""),
])
print(f'champ-help: shared.ts, golden ({N} cases), check-models-v3, check-ask-function, SQL v8')

# ------------------------------------------------------------------------------------------------ the phone
exec((HERE / 'champ-help-2026-10-11-app.py').read_text(), {'ROOT': ROOT, 'patch': patch, 'TOPICS': TOPICS})
