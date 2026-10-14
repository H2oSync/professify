"""The website's assistant becomes Champ, looking like the phone's Champ sheet (2026-10-14).

Tate: the website still showed the old "Hawk". Two things:
 1. NAME. Every user-visible "Hawk" in hawk-ask.js and index.html is now "Champ": the header, the greeting ("Hi, I'm Champ."),
    the placeholder, the aria-labels, "What Champ can do", "Noted — this helps Champ get better.", the help copy (APP_HELP.champ,
    APP_HELP_Q.champ) and the privacy page ("Champ (called Hawk on the website)" -> "Champ"). Code identifiers, CSS classes,
    event names (hawk_miss ...), storage keys and file names are NOT renamed: nothing that stores or measures changes.
 2. LOOK. The box is the phone's Champ sheet in the website's own light/dark tokens: a white (--panel) surface instead of navy,
    the big bird and "Hi, I'm Champ.", the phone's four starter chips (same words; each asks that question through the same
    path a typed question takes), an "Ask Champ..." pill with a round navy send button, and the footer line under it. It is
    still a floating non-modal box above the launcher and still dragged by its header. The old colours that assumed navy
    (white text, translucent-white rows, light-blue links, mint/amber chips) are now tokens with a light and a dark value, each
    >= 4.5:1 on its surface.
 The footer is true for the website: signed in, a question that needs the model goes to the `ask` function (and on to
 Anthropic); signed out, nothing leaves the browser. So the line follows that, and says "Some questions", because many are
 answered in the browser (the privacy page says the same).
Run after website-hawk-champ-icon-2026-10-14.py:  python3 <this> <repo>
"""
import sys, re, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
css_f = root / 'hawk-ask.css'; css = css_f.read_text()
js_f = root / 'hawk-ask.js'; js = js_f.read_text()
idx_f = root / 'index.html'; idx = idx_f.read_text()
def one(s, old, new):
    n = s.count(old); assert n == 1, (n, old[:90]); return s.replace(old, new)

# ---------------------------------------------------------------- 1. the name (user-visible strings only)
js = one(js, "help: 'What Hawk can do'", "help: 'What Champ can do'")
js = one(js, "'Noted — this helps Hawk get better.'", "'Noted — this helps Champ get better.'")
js = one(js, "champ: ['Hawk answers questions about classes", "champ: ['Champ answers questions about classes")
js = one(js, "champ: 'What does Hawk do and where does my information go?'", "champ: 'What does Champ do and where does my information go?'")
js = one(js, "face.setAttribute('aria-label', 'Hawk');", "face.setAttribute('aria-label', 'Champ');")
js = one(js, "fab.setAttribute('aria-label', 'Ask Hawk');", "fab.setAttribute('aria-label', 'Ask Champ');")
js = one(js, "box.setAttribute('aria-label', 'Hawk');", "box.setAttribute('aria-label', 'Champ');")
js = one(js, "make('span', 'hawk-head__name', 'Hawk')", "make('span', 'hawk-head__name', 'Champ')")
js = one(js, "x.setAttribute('aria-label', 'Close Hawk');", "x.setAttribute('aria-label', 'Close Champ');")
js = one(js, "make('label', 'hawk-sr', 'Ask Hawk')", "make('label', 'hawk-sr', 'Ask Champ')")
js = one(js, "input.placeholder = 'Ask Hawk…';", "input.placeholder = 'Ask Champ…';")
idx = one(idx, "sends the questions you ask Champ (Hawk on the website) to <b>Anthropic", "sends the questions you ask Champ to <b>Anthropic")
idx = one(idx, "<p>Champ (called Hawk on the website) answers the questions", "<p>Champ answers the questions")

# ---------------------------------------------------------------- 2. the footer line
js = one(js, """    return aiUrl() ? 'Questions are read by AI · your classes stay on this device'
                   : 'Nothing you type here leaves your browser';""",
"""    /* Signed in, a question that needs the model goes to the `ask` function and on to Anthropic; many are answered
       in the browser, hence "Some". Signed out nothing leaves (sessionToken() is null and callAsk stops). The phone's
       line is "Questions go to Anthropic’s AI · your classes stay on this phone". */
    var signedIn = false;
    try { signedIn = typeof sbUser !== 'undefined' && !!(sbUser && sbUser.id); } catch (_) {}
    return aiUrl() && signedIn ? 'Some questions go to Anthropic’s AI · your classes stay on this device'
                               : 'Nothing you type here leaves your browser';""")

# ---------------------------------------------------------------- 3. the sheet: greeting + chips (JS)
js = one(js, """  function hintEl() {
    var d = make('div', 'hawk-hint');
    var face = make('div', 'hawk-hint__face');
    face.setAttribute('role', 'img');
    face.setAttribute('aria-label', 'Champ');
    d.appendChild(face);
    var words = make('div');
    words.appendChild(make('div', 'hawk-hint__lead', 'Hawk is here!'));
    words.appendChild(make('div', 'hawk-hint__sub', 'What can I assist you with?'));
    d.appendChild(words);
    return d;
  }""", """  /* The phone's four starter questions, word for word (app/index.html champView `sugg`). Each is asked through
     answer(), the path a typed question takes. */
  var STARTERS = [['cc1', 'When am I free this week?'], ['cc2', 'Who\\'s free right now?'], ['cc3', 'What’s my day look like?'], ['cc4', 'My best professor']];
  function startersEl(cls) {
    var d = make('div', cls);
    STARTERS.forEach(function (s) {
      var b = make('button', 'hawk-cchip hawk-' + s[0], s[1]);
      b.type = 'button';
      b.addEventListener('click', function () { answer(s[1]); });
      d.appendChild(b);
    });
    return d;
  }
  /* The sheet is "empty" while the greeting is up: then the big bird and the 2 x 2 chips show, and the slim chip row and
     the header bird do not (and the other way round once there is an answer). */
  function syncEmpty() {
    var empty = !!els.log.querySelector('.hawk-hint');
    els.box.classList.toggle('hawk-box--empty', empty);
  }
  function hintEl() {
    var d = make('div', 'hawk-hint');
    var face = make('div', 'hawk-hint__face');
    face.setAttribute('role', 'img');
    face.setAttribute('aria-label', 'Champ');
    d.appendChild(face);
    d.appendChild(make('div', 'hawk-hint__lead', 'Hi, I\\'m Champ.'));
    d.appendChild(make('div', 'hawk-hint__sub', 'Ask about classes, professors, your week or your friends.'));
    d.appendChild(startersEl('hawk-cgrid'));
    return d;
  }""")
js = one(js, """    var headSpark = make('span', 'hawk-head__spark');
    headSpark.appendChild(spark());
    head.appendChild(headSpark);
    head.appendChild(make('span', 'hawk-head__name', 'Champ'));
    head.appendChild(make('span', 'hawk-head__sub', 'AI assistant'));""",
"""    var headBird = make('span', 'hawk-head__bird'); headBird.setAttribute('aria-hidden', 'true');
    head.appendChild(headBird);
    head.appendChild(make('span', 'hawk-head__name', 'Champ'));
    head.appendChild(make('span', 'hawk-head__sub', 'From TermChamp’s real data'));""")
js = one(js, """    var send = make('button', 'hawk-send', 'Ask');
    send.type = 'submit';""", """    var send = make('button', 'hawk-send');
    send.type = 'submit';
    send.setAttribute('aria-label', 'Send');
    var arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    arrow.setAttribute('viewBox', '0 0 24 24'); arrow.setAttribute('width', '20'); arrow.setAttribute('height', '20');
    arrow.setAttribute('aria-hidden', 'true'); arrow.setAttribute('fill', 'none'); arrow.setAttribute('stroke', 'currentColor');
    arrow.setAttribute('stroke-width', '2.6'); arrow.setAttribute('stroke-linecap', 'round'); arrow.setAttribute('stroke-linejoin', 'round');
    var ap = document.createElementNS('http://www.w3.org/2000/svg', 'path'); ap.setAttribute('d', 'M5 12h14M13 6l6 6-6 6');
    arrow.appendChild(ap); send.appendChild(arrow);""")
js = one(js, """    box.appendChild(head);
    box.appendChild(log);
    box.appendChild(foot);
    box.appendChild(ask);
    document.body.appendChild(fab);

    els = { fab: fab, box: box, log: log, input: input, send: send, foot: foot };
""", """    box.appendChild(head);
    box.appendChild(log);
    box.appendChild(startersEl('hawk-chips'));
    box.appendChild(ask);
    box.appendChild(foot);
    document.body.appendChild(fab);

    els = { fab: fab, box: box, log: log, input: input, send: send, foot: foot };
    try { new MutationObserver(syncEmpty).observe(log, { childList: true }); } catch (_) {}
""")
js = one(js, "    els.foot.textContent = when || privacyLine();", "    els.foot.textContent = when ? when + ' · ' + privacyLine() : privacyLine();   /* the as-of joins the privacy line; it never replaces it */")
# the footer follows the signed-in state each time the box opens (it is built once, at page load, signed out)
js = one(js, """    if (!els.log.childNodes.length) { els.log.appendChild(hintEl()); stamp(); }
    els.input.focus();""", """    if (!els.log.childNodes.length) { els.log.appendChild(hintEl()); stamp(); }
    else stamp();
    syncEmpty();
    els.input.focus();""")

# ---------------------------------------------------------------- 4. the sheet: colours as tokens (CSS)
head_end = css.index('.hawk-box {')
a, b = css[:head_end], css[head_end:]
subs = [
  (r'rgba\(255,\s*255,\s*255,\s*([.\d]+)\)', r'rgba(var(--hawk-fg), \1)'),
  (r'rgba\(159,\s*180,\s*255,\s*([.\d]+)\)', r'rgba(var(--hawk-link-rgb), \1)'),
  (r'rgba\(127,\s*227,\s*181,\s*([.\d]+)\)', r'rgba(var(--hawk-good-rgb), \1)'),
  (r'rgba\(255,\s*207,\s*122,\s*([.\d]+)\)', r'rgba(var(--hawk-warn-rgb), \1)'),
  (r'#9fb4ff\b', 'var(--hawk-link)'), (r'#cdd7ff\b', 'var(--hawk-link-2)'), (r'#7fe3b5\b', 'var(--hawk-good)'),
  (r'#ffcf7a\b', 'var(--hawk-warn)'), (r'#8fa6ff\b', 'var(--hawk-focus)'),
]
for pat, rep in subs: b = re.sub(pat, rep, b)
b = one(b, ".hawk-opt.is-on { background: #fff; border-color: #fff; color: var(--hawk-navy); }", ".hawk-opt.is-on { background: var(--hawk-sel-bg); border-color: var(--hawk-sel-bg); color: var(--hawk-sel-ink); }")
b = b.replace('color: #fff', 'color: var(--hawk-ink)')
css = a + b

css = one(css, """:root {
  --hawk-navy: #1a224e;      /* header and the ask bar */
  --hawk-navy-lift: #20295d; /* the body, one step lighter */
  --hawk-dim: #aaaec2;       /* secondary text on navy */
  --hawk-rule: rgba(255, 255, 255, .10);""", """:root {
  /* The Champ sheet (2026-10-14): the phone's white sheet, drawn in the website's own tokens (--panel, --text ...), so it
     follows Light / Dark / Cream with the page. The names --hawk-navy* stay (other rules use them); they are surfaces now. */
  --hawk-navy: var(--panel-2, #242424);      /* the plan-save card, the field */
  --hawk-navy-lift: var(--panel, #1E1E1E);   /* the sheet */
  --hawk-dim: var(--text-2, rgba(255,255,255,.72));   /* secondary text */
  --hawk-ink: var(--text, rgba(255,255,255,.87));     /* primary text */
  --hawk-rule: var(--line, rgba(255, 255, 255, .10));
  --hawk-fg: var(--fg-rgb, 255,255,255);              /* tint for rows: ink at low alpha */
  --hawk-brand: #AFC3EE;                              /* "Champ", the greeting (the phone's navy, lifted for dark) */
  --hawk-send-bg: #2A4A8F;
  --hawk-sel-bg: #AFC3EE; --hawk-sel-ink: #101a33;
  --hawk-link: #9fb4ff; --hawk-link-2: #cdd7ff; --hawk-link-rgb: 159,180,255; --hawk-focus: #8fa6ff;
  --hawk-good: #7fe3b5; --hawk-good-rgb: 127,227,181;
  --hawk-warn: #ffcf7a; --hawk-warn-rgb: 255,207,122;
  --hawk-cc1-bg: #271C45; --hawk-cc1-ink: #CDBEFF; --hawk-cc2-bg: #3A1529; --hawk-cc2-ink: #F9B4D6;
  --hawk-cc3-bg: #0E2D2B; --hawk-cc3-ink: #5FD9C9; --hawk-cc4-bg: #172748; --hawk-cc4-ink: #A9C6FF;""")
# light + cream values, just before .hawk-sr
css = one(css, "\n.hawk-sr {", """
:root[data-theme="light"], :root[data-theme="cream"] {
  --hawk-brand: #16336B;
  --hawk-send-bg: #16336B;
  --hawk-sel-bg: #16336B; --hawk-sel-ink: #fff;
  --hawk-link: #16336B; --hawk-link-2: #16336B; --hawk-link-rgb: 22,51,107; --hawk-focus: #2563EB;
  --hawk-good: #11633C; --hawk-good-rgb: 17,99,60;
  --hawk-warn: #744600; --hawk-warn-rgb: 116,70,0;
  --hawk-cc1-bg: #EFE7FF; --hawk-cc1-ink: #5B21B6; --hawk-cc2-bg: #FCE4F0; --hawk-cc2-ink: #9D174D;
  --hawk-cc3-bg: #DDF5F1; --hawk-cc3-ink: #0B5F58; --hawk-cc4-bg: #E3ECFF; --hawk-cc4-ink: #1E40AF;
}

.hawk-sr {""")

css = css.rstrip('\n') + """

/* ------------------------------------------------------------------------------------------------
   The Champ sheet — 2026-10-14. Later rules win over the navy-era ones above.
   ------------------------------------------------------------------------------------------------ */
.hawk-box {
  background: var(--hawk-navy-lift);
  color: var(--hawk-ink);
  border: 1px solid var(--hawk-rule);
  border-radius: 20px;
  box-shadow: 0 18px 48px rgba(22, 51, 107, .22);
}
.hawk-box--moving { box-shadow: 0 24px 60px rgba(22, 51, 107, .32); }
.hawk-head { background: var(--hawk-navy-lift); border-bottom: 1px solid var(--hawk-rule); }
.hawk-head__bird { flex: none; width: 24px; height: 28px; background: var(--hawk-champ) center / contain no-repeat; }
.hawk-head__name { font-size: 16px; font-weight: 900; color: var(--hawk-brand); }
.hawk-head__sub { font-size: 12px; color: var(--hawk-dim); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hawk-box--empty .hawk-head__bird, .hawk-box--empty .hawk-head__sub { display: none; }
.hawk-x { color: var(--hawk-dim); }
.hawk-x:hover { color: var(--hawk-ink); }

/* Empty state: the big bird, the greeting, the phone's 2 x 2 starter chips. */
.hawk-hint { display: flex; flex-direction: column; align-items: center; gap: 0; padding: 4px 4px 6px; text-align: center; }
.hawk-hint__face { flex: none; width: 92px; height: 112px; background: var(--hawk-champ) center / contain no-repeat; filter: drop-shadow(0 10px 12px rgba(22, 51, 107, .26)); }
.hawk-hint__lead { margin-top: 6px; font-size: 24px; font-weight: 900; letter-spacing: -.01em; color: var(--hawk-brand); }
.hawk-hint__sub { margin: 4px 0 14px; font-size: 13.5px; line-height: 1.4; color: var(--hawk-dim); text-wrap: balance; }
.hawk-cgrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; width: 100%; }
.hawk-cchip { border: 0; font: inherit; font-weight: 900; font-size: 13px; line-height: 1.2; cursor: pointer; border-radius: 18px; padding: 7px 8px; min-height: 36px; text-align: center; text-wrap: balance; }
.hawk-cchip:focus-visible { outline: 2px solid var(--hawk-focus); outline-offset: 2px; }
.hawk-cc1 { background: var(--hawk-cc1-bg); color: var(--hawk-cc1-ink); }
.hawk-cc2 { background: var(--hawk-cc2-bg); color: var(--hawk-cc2-ink); }
.hawk-cc3 { background: var(--hawk-cc3-bg); color: var(--hawk-cc3-ink); }
.hawk-cc4 { background: var(--hawk-cc4-bg); color: var(--hawk-cc4-ink); }
/* After an answer the chips sit in one slim scrolling row above the field, as on the phone. */
.hawk-chips { flex: none; display: flex; gap: 8px; overflow-x: auto; padding: 8px 12px; scrollbar-width: none; border-top: 1px solid var(--hawk-rule); }
.hawk-chips::-webkit-scrollbar { display: none; }
.hawk-chips .hawk-cchip { flex: none; white-space: nowrap; min-height: 32px; padding: 0 13px; border-radius: 16px; }
.hawk-box--empty .hawk-chips { display: none; }
/* On a phone the greeting is a row (bird left, words right) so the sheet stays small: a sheet that eats the screen is a modal. */
@media (max-width: 720px) {
  .hawk-hint { display: grid; grid-template-columns: 56px minmax(0, 1fr); column-gap: 12px; align-items: center; text-align: left; padding: 0 2px 4px; }
  .hawk-hint__face { grid-row: 1 / span 2; width: 56px; height: 68px; }
  .hawk-hint__lead { margin-top: 0; font-size: 21px; align-self: end; }
  .hawk-hint__sub { margin: 2px 0 0; font-size: 12.5px; align-self: start; }
  .hawk-box { width: calc(100vw - 20px); }   /* a dragged box (left set, right auto) keeps the phone's width; the chip row scrolls inside it */
  .hawk-cgrid { grid-column: 1 / -1; margin-top: 8px; }
  .hawk-box--empty .hawk-log { padding: 6px 12px 4px; }
  .hawk-box--empty .hawk-head { padding-top: 8px; padding-bottom: 8px; }
  .hawk-box--empty .hawk-foot { padding-top: 5px; padding-bottom: 9px; }
}

/* The field: a pill with a round navy send button, like the phone's .cinput / .sendbtn. */
.hawk-ask { margin: 0 12px; padding: 5px 5px 5px 16px; gap: 8px; border: 1px solid var(--hawk-rule); border-radius: 28px; background: var(--hawk-navy); }
.hawk-box--empty .hawk-ask { margin-top: 4px; }
.hawk-ask:focus-within { border-color: var(--hawk-send-bg); box-shadow: 0 0 0 2px var(--hawk-send-bg); }
.hawk-input { color: var(--hawk-ink); font-weight: 600; height: 40px; }
.hawk-input::placeholder { color: var(--hawk-dim); font-size: 15px; font-weight: 600; opacity: 1; }
.hawk-send { width: 40px; height: 40px; min-height: 0; padding: 0; border-radius: 50%; display: grid; place-items: center; background: var(--hawk-send-bg); color: #fff; }
.hawk-send:disabled { opacity: .5; }
.hawk-foot { padding: 7px 14px 11px; font-size: 11.5px; text-align: center; color: var(--hawk-dim); background: var(--hawk-navy-lift); }
"""
css_f.write_text(css); js_f.write_text(js); idx_f.write_text(idx)
print('ok champ')
