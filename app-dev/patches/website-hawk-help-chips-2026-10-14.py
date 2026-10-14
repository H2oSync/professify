"""Website Hawk: the phone's "Did you mean" help chips, and two help answers made true for the website (2026-10-14).

Tate, before shipping the website catch-up: "make sure hawk is up to date then run".

What was behind the phone (champ-help-and-haiku-5-5-2026-10-11):
  1. The phone offers up to two "Did you mean …" chips for its 16 TermChamp questions when the model says
     cant_answer or can't be reached (helpMatch: word rules per topic, all words required, some "not" words; never
     when the question names a course). The website had the 16 answers (website-hawk-app-menu) but no chips, and
     Hawk's on-device pre-router refuses some help phrasings ("how do I contact …") before the model is asked, so
     those got "I only find classes …". Now the refusal, the not_about_classes / ambiguous answers and the
     "Not it?" alternatives offer the matching topics first. A chip answers from APP_HELP on the page: nothing sent.
     HW / HELP_RULES / HELP_BARE / helpMatch are lifted verbatim from app/index.html (const -> var), with "hawk" added
     wherever the rules say "champ".
  2. Two of the 16 answers described the phone, not the website:
     - dark_mode said "System, Light or Dark"; the website's Appearance offers Light and Dark.
     - plans said Plans live in "Schedule › Planner"; on the website they are Schedule › Plans (Planner is the Builder),
       and the button now opens Plans.
Also checked (check-desktop-hawk-places.mjs): every APP_PLACES value the app menu's go_to may return lands on a
website screen, and set_theme dark/light work.
Run after website-hawk-app-menu-2026-10-14.py:  python3 app-dev/patches/website-hawk-help-chips-2026-10-14.py <repo>
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
f = root / 'hawk-ask.js'; s = f.read_text()
app = (root / 'app' / 'index.html').read_text()

def one(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:100]); s = s.replace(old, new)

# the matcher, verbatim from the phone
a = app.index('const HW = { app:'); b = app.index('const helpOffer')
lift = app[a:b].replace('const HW', 'var HW').replace('const HELP_RULES', 'var HELP_RULES').replace('const HELP_BARE', 'var HELP_BARE')
# the website's assistant is Hawk, not Champ: let the champ topic hear its name too
lift = lift.replace('ai: /\\b(champ|', 'ai: /\\b(hawk|champ|').replace('/\\bchamp\\b/', '/\\b(?:champ|hawk)\\b/').replace('who is champ', 'who is (?:champ|hawk)')
lift = '\n'.join('  ' + l if l.strip() else l for l in lift.rstrip('\n').split('\n'))

one("""    dark_mode: ['Yes — Settings › Appearance: System, Light or Dark.', 'Open Settings', 'appearance'],""",
    """    dark_mode: ['Yes — Settings › Appearance: Light or Dark.', 'Open Settings', 'appearance'],""")
one("""    plans: ['Plans A, B and C are three versions of your next term, kept in Schedule › Planner. Add a section to one from any class page with ＋ Plan, and change any of them. Ask me for your game plan to see what to register for first.', 'Open Planner', 'planner'],""",
    """    plans: ['Plans A, B and C are three versions of your next term, kept in Schedule › Plans. Add a section to one from any class page with ＋ Plan, or let the Planner draft all three, and change any of them. Ask me for your game plan to see what to register for first.', 'Open Plans', 'watchlist'],""")

one("""  function renderAppHelp(turn, result) {""",
    """  /* The questions as the chips show them (the phone's HELP[k].q). */
  var APP_HELP_Q = { what_is: 'What is TermChamp?', free: 'Is TermChamp free?', who_sees: 'Who can see my schedule?',
    ratings_anonymous: 'Are my reviews anonymous?', ratings_source: 'Where do the ratings come from?',
    seats_source: 'Where do the seat numbers come from?', add_class: 'How do I add a class?', plans: 'What are Plans A, B and C?',
    seat_alerts: 'How do seat alerts work?', degree_report: 'How do I upload my degree report?', add_friends: 'How do I add friends?',
    block_report: 'How do I block or report someone?', delete_account: 'How do I delete my account?',
    champ: 'What does Hawk do and where does my information go?', dark_mode: 'Is there a dark mode?', contact: 'How do I contact TermChamp?' };
  /* helpMatch — lifted verbatim from the phone (app/index.html, champ-help-2026-10-11). OFFERED, never answered on a guess. */
""" + lift + """
  /* Up to two "Did you mean" rows for TermChamp questions; a tap answers from APP_HELP on this page (nothing sent). */
  function helpRows(q) {
    var ks = []; try { ks = helpMatch(q).filter(function (k) { return APP_HELP_Q[k] && APP_HELP[k]; }); } catch (_) {}
    return ks.map(function (k) {
      return { code: '', name: APP_HELP_Q[k], chip: null, go: function () {
        try { if (has('track')) global.track('hawk_help_chip', null, 'hawk', { topic: k }); } catch (_) {}
        readings = { local: null, model: null };
        render(APP_HELP_Q[k], { prerouted: true, confident: true, in_scope: true, tool: 'app_help', args: { topic: k },
                                corrections: [], leftovers: [], signals: [] }, buildCatalog());
        return 'Here’s that'; } };
    });
  }
  function helpChips(turn, q) {
    var rows = helpRows(q); if (!rows.length) return false;
    var box = make('div', 'hawk-alts');
    box.appendChild(make('div', 'hawk-alts__head', rows.length > 1 ? 'Did you mean one of these?' : 'Did you mean this?'));
    rows.forEach(function (r) { box.appendChild(rowEl(r)); });
    turn.appendChild(box);
    return true;
  }
  function renderAppHelp(turn, result) {""")

# the router's refusal: a TermChamp question gets its chips instead of "I only find classes"
one("""    if (result.refused) {
      turn.appendChild(make('div', 'hawk-note',
        'I only find classes, sections and professors at Cal Poly.'));""",
    """    if (result.refused) {
      if (!helpChips(turn, q)) turn.appendChild(make('div', 'hawk-note',
        'I only find classes, sections and professors at Cal Poly.'));""")
one("""      } else if (why === 'not_about_classes') {
        turn.appendChild(make('div', 'hawk-note',
          'I only find classes, sections and professors at Cal Poly.'));""",
    """      } else if (why === 'not_about_classes') {
        if (helpChips(turn, q)) why = 'shown';
        else turn.appendChild(make('div', 'hawk-note',
          'I only find classes, sections and professors at Cal Poly.'));""")
# "Not it?" and the not-sure answers: help topics first, then the other readings (three rows in all)
one("""    var box = make('div', 'hawk-alts');
    box.appendChild(make('div', 'hawk-alts__head', alts.length ? 'Did you mean' : (quiet ? 'Try a course code, a professor, or “open CSC labs after 6”.' : 'Sorry about that. Try it another way:')));
    alts.slice(0, 3).forEach(function (r) {""",
    """    var hrows = (shown && shown.tool === 'app_help') ? [] : helpRows(q);
    var box = make('div', 'hawk-alts');
    box.appendChild(make('div', 'hawk-alts__head', (alts.length || hrows.length) ? 'Did you mean' : (quiet ? 'Try a course code, a professor, or “open CSC labs after 6”.' : 'Sorry about that. Try it another way:')));
    hrows.forEach(function (r) { box.appendChild(rowEl(r)); });
    alts.slice(0, Math.max(0, 3 - hrows.length)).forEach(function (r) {""")
f.write_text(s)
print('website-hawk-help-chips: applied')
